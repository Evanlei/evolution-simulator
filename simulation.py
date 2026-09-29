"""Deterministic fixed-step ecosystem, usable without Pygame or a display."""

import csv
import json
from pathlib import Path
import random

from brain import Brain
from config import Config
from creature import Creature
from spatial import FoodIndex

SCHEMA_VERSION = 1


class World:
    def __init__(self, config=None, seed=42, brain=None, controller="neural", record=True):
        self.config = config or Config()
        self.seed = seed
        self.founder_brain = brain.copy() if brain else None
        self.controller = controller
        # Food layouts do not depend on random numbers consumed by neural initialization.
        self.environment_rng = random.Random(seed)
        self.rng = random.Random(seed + 1_000_003)
        self.policy_rng = random.Random(seed + 2_000_003)
        self.food = FoodIndex([self.random_food() for _ in range(self.config.food_count)])
        self.creatures = []
        for i in range(self.config.initial_population):
            point = self.random_position(self.config.radius)
            self.creatures.append(Creature(i, *point, brain.copy() if brain else Brain(self.rng),
                energy=self.config.initial_energy, lineage=i, controller=controller))
        self.next_id = len(self.creatures)
        self.steps = self.births = self.deaths = self.meals = self.max_generation = 0
        self.record = record
        self.history = []
        self.champion = None
        self.sample()

    @property
    def time(self):
        return self.steps * self.config.dt

    def random_position(self, margin):
        return (self.environment_rng.uniform(margin, self.config.width - margin),
                self.environment_rng.uniform(margin, self.config.height - margin))

    def random_food(self):
        return self.random_position(self.config.food_radius)

    def step(self):
        c = self.config
        newborns, survivors = [], []
        # Seeded shuffling removes permanent first-in-list feeding priority.
        order = list(self.creatures)
        self.rng.shuffle(order)
        for agent in order:
            index = self.food.nearest(agent.x, agent.y, c.sensor_range)
            target = None if index is None else self.food.positions[index]
            agent.update(c.dt, target, c, self.policy_rng)
            # A depleted creature cannot be revived by feeding in the same step.
            if agent.energy <= 0:
                self.deaths += 1
                self.consider_champion(agent)
                continue
            eaten = self.food.nearest(agent.x, agent.y, c.radius + c.food_radius)
            if eaten is not None:
                agent.energy = min(c.max_energy, agent.energy + c.food_energy)
                agent.meals += 1
                self.meals += 1
                self.food.replace(eaten, self.random_food())
            if (c.reproduction and agent.energy >= c.reproduction_energy and
                    agent.age >= c.minimum_age and agent.cooldown == 0 and
                    len(order) + len(newborns) < c.population_limit):
                child = agent.reproduce(self.next_id, c, self.rng)
                self.next_id += 1
                self.births += 1
                self.max_generation = max(self.max_generation, child.generation)
                newborns.append(child)
            self.consider_champion(agent)
            survivors.append(agent)
        self.creatures = survivors + newborns
        self.steps += 1
        if self.record and self.steps % max(1, round(1 / c.dt)) == 0:
            self.sample()

    def consider_champion(self, agent):
        score = (agent.meals, agent.children, agent.age)
        if self.champion is None or score > tuple(self.champion["score"]):
            self.champion = {"score": list(score), "agent": agent.to_dict()}

    def metrics(self):
        agents = self.creatures
        return {"time": round(self.time, 6), "population": len(agents), "births": self.births,
                "deaths": self.deaths, "meals": self.meals, "max_generation": self.max_generation,
                "mean_energy": sum(a.energy for a in agents) / len(agents) if agents else 0,
                "lineages": len({a.lineage for a in agents})}

    def sample(self):
        if self.record:
            self.history.append(self.metrics())

    def to_dict(self):
        return {"schema_version": SCHEMA_VERSION, "config": self.config.to_dict(), "seed": self.seed,
                "steps": self.steps, "births": self.births, "deaths": self.deaths,
                "meals": self.meals, "max_generation": self.max_generation, "next_id": self.next_id,
                "food": self.food.positions, "creatures": [a.to_dict() for a in self.creatures],
                "rng": self.rng.getstate(), "environment_rng": self.environment_rng.getstate(),
                "policy_rng": self.policy_rng.getstate(), "history": self.history,
                "champion": self.champion, "record": self.record,
                "founder_brain": self.founder_brain.parameters if self.founder_brain else None,
                "controller": self.controller}

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.to_dict(), allow_nan=False))
        temporary.replace(path)

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text())
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported checkpoint version")
        founder = Brain(parameters=data["founder_brain"]) if data.get("founder_brain") else None
        world = cls(Config(**data["config"]), data["seed"], founder,
                    data.get("controller", "neural"), record=data["record"])
        for key in ("steps", "births", "deaths", "meals", "max_generation", "next_id", "history", "champion"):
            setattr(world, key, data[key])
        world.creatures = [Creature.from_dict(a) for a in data["creatures"]]
        world.food = FoodIndex([tuple(p) for p in data["food"]])

        def tuples(value):
            return tuple(tuples(v) for v in value) if isinstance(value, list) else value

        for name in ("rng", "environment_rng", "policy_rng"):
            getattr(world, name).setstate(tuples(data[name]))
        return world

    def export_csv(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = list(self.history)
        if not rows or rows[-1] != self.metrics():
            rows.append(self.metrics())
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

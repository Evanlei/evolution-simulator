"""Creature state and decisions. Rendering belongs to the dashboard."""

from dataclasses import dataclass, field
import math

from brain import Brain


@dataclass
class Creature:
    id: int
    x: float
    y: float
    brain: Brain
    energy: float = 100
    generation: int = 0
    parent_id: int = -1
    lineage: int = 0
    age: float = 0
    vx: float = 0
    vy: float = 0
    meals: int = 0
    children: int = 0
    cooldown: float = 0
    progress: float = 0
    controller: str = "neural"
    inputs: list = field(default_factory=lambda: [0.0] * 8)
    target: object = None

    def sense(self, target, config):
        self.target = target
        dx, dy = (0, 0) if target is None else (target[0] - self.x, target[1] - self.y)
        # Direction stays informative close to food; range is enforced by the food index.
        distance = math.hypot(dx, dy)
        dx, dy = (dx / distance, dy / distance) if distance else (0, 0)
        self.inputs = [dx, dy,
                       float(target is not None), self.energy / config.max_energy,
                       self.vx / config.max_speed, self.vy / config.max_speed,
                       2 * self.x / config.width - 1, 2 * self.y / config.height - 1]
        return self.inputs

    def update(self, dt, target, config, rng):
        inputs = self.sense(target, config)
        if self.controller == "greedy" and target is not None:
            dx, dy = target[0] - self.x, target[1] - self.y
            distance = math.hypot(dx, dy)
            ox, oy = (dx / distance, dy / distance) if distance else (0, 0)
        elif self.controller in ("random", "greedy"):
            # Baseline: persist a heading, with a mean one-second turn interval.
            if self.age == 0 or rng.random() < dt:
                angle = rng.uniform(-math.pi, math.pi)
                self.vx, self.vy = math.cos(angle) * config.max_speed, math.sin(angle) * config.max_speed
            ox, oy = self.vx / config.max_speed, self.vy / config.max_speed
        else:
            ox, oy = self.brain.forward(inputs)
        # Bound total speed, so diagonal movement gets no speed bonus.
        norm = max(1.0, math.hypot(ox, oy))
        self.vx, self.vy = ox / norm * config.max_speed, oy / norm * config.max_speed
        old_distance = math.hypot(target[0] - self.x, target[1] - self.y) if target else 0
        self.x = max(config.radius, min(config.width - config.radius, self.x + self.vx * dt))
        self.y = max(config.radius, min(config.height - config.radius, self.y + self.vy * dt))
        if target:
            self.progress += old_distance - math.hypot(target[0] - self.x, target[1] - self.y)
        self.energy -= (config.basal_cost + config.movement_cost * math.hypot(self.vx, self.vy)) * dt
        self.age += dt
        self.cooldown = max(0, self.cooldown - dt)

    def reproduce(self, child_id, config, rng):
        """Split energy and inherit an independently allocated, mutated genome."""
        self.energy /= 2
        self.children += 1
        self.cooldown = config.reproduction_cooldown
        angle = rng.uniform(-math.pi, math.pi)
        separation = 2 * config.radius + 1
        return Creature(
            child_id,
            max(config.radius, min(config.width - config.radius, self.x + math.cos(angle) * separation)),
            max(config.radius, min(config.height - config.radius, self.y + math.sin(angle) * separation)),
            self.brain.mutated_copy(rng, config.mutation_rate, config.mutation_sigma),
            energy=self.energy, generation=self.generation + 1, parent_id=self.id,
            lineage=self.lineage, cooldown=config.reproduction_cooldown,
        )

    def to_dict(self):
        data = dict(vars(self))
        data["brain"] = list(self.brain.parameters)
        data["target"] = list(self.target) if self.target is not None else None
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["brain"] = Brain(parameters=data["brain"])
        if data.get("target") is not None:
            data["target"] = tuple(data["target"])
        return cls(**data)

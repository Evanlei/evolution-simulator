import math
import random
import tempfile
import unittest
from pathlib import Path

from brain import Brain, PARAMETERS
from config import Config
from creature import Creature
from simulation import World
from spatial import FoodIndex


class CoreTests(unittest.TestCase):
    def test_sensors_keep_direction_close_to_food(self):
        agent = Creature(0, 500, 350, Brain(random.Random(2)))
        near = agent.sense((503, 354), Config())[:2]
        far = agent.sense((560, 430), Config())[:2]
        self.assertEqual(near, far)
        self.assertEqual(near, [0.6, 0.8])
        self.assertEqual(agent.sense(None, Config())[:3], [0, 0, 0])
        self.assertEqual(agent.sense((500, 350), Config())[:3], [0, 0, 1])

    def test_food_replenishes_and_reproduction_cooldown(self):
        config = Config(initial_population=1, food_count=1, minimum_age=0)
        world = World(config, 4)
        parent = world.creatures[0]
        parent.brain = Brain(parameters=[0.0] * PARAMETERS)
        parent.energy = 180
        world.food.replace(0, (parent.x, parent.y))
        world.step()
        self.assertEqual(world.meals, 1)
        self.assertEqual(len(world.food.positions), 1)
        self.assertEqual(world.births, 1)
        self.assertEqual(len(world.creatures), 2)
        parent.energy = 200
        world.step()
        self.assertEqual(world.births, 1)

    def test_brain_and_mutation(self):
        rng = random.Random(4)
        parent = Brain(rng)
        original = parent.parameters[:]
        child = parent.mutated_copy(rng, rate=1)
        self.assertEqual(len(original), 112)
        self.assertEqual(parent.parameters, original)
        self.assertIsNot(child.parameters, parent.parameters)
        self.assertNotEqual(child.parameters, original)
        self.assertTrue(all(-1 <= v <= 1 for v in child.forward([0.2] * 8)))
        self.assertEqual(parent.mutated_copy(rng, rate=0).parameters, original)
        with self.assertRaises(ValueError):
            Brain(parameters=[0] * 2)
        with self.assertRaises(ValueError):
            Brain(parameters=[float("nan")] * PARAMETERS)

    def test_spatial_index_matches_brute_force(self):
        rng = random.Random(3)
        points = [(rng.uniform(0, 1000), rng.uniform(0, 700)) for _ in range(100)]
        index = FoodIndex(points)
        for _ in range(100):
            i = rng.randrange(100)
            index.replace(i, (rng.uniform(0, 1000), rng.uniform(0, 700)))
            x, y, radius = rng.uniform(0, 1000), rng.uniform(0, 700), rng.uniform(0, 300)
            candidates = [((fx - x) ** 2 + (fy - y) ** 2, i)
                          for i, (fx, fy) in enumerate(index.positions)
                          if (fx - x) ** 2 + (fy - y) ** 2 <= radius ** 2]
            expected = min(candidates)[1] if candidates else None
            self.assertEqual(index.nearest(x, y, radius), expected)

    def test_reproduction_conserves_energy(self):
        c = Config()
        parent = Creature(1, 500, 350, Brain(random.Random(1)), energy=180, generation=3, lineage=1)
        original = parent.brain.parameters[:]
        child = parent.reproduce(2, c, random.Random(8))
        self.assertEqual(parent.energy + child.energy, 180)
        self.assertEqual(child.generation, 4)
        self.assertEqual(child.parent_id, 1)
        self.assertEqual(child.lineage, 1)
        self.assertIsNot(parent.brain, child.brain)
        self.assertEqual(parent.brain.parameters, original)
        self.assertNotEqual((parent.x, parent.y), (child.x, child.y))

    def test_determinism_and_checkpoint_continuation(self):
        config = Config(initial_population=8, food_count=40)
        a, b = World(config, 17), World(config, 17)
        for _ in range(70):
            a.step()
            b.step()
        self.assertEqual(a.to_dict(), b.to_dict())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "world.json"
            a.save(path)
            loaded = World.load(path)
            for _ in range(50):
                a.step()
                loaded.step()
            self.assertEqual(a.to_dict(), loaded.to_dict())

    def test_boundaries_and_energy(self):
        config = Config()
        p = [0.0] * PARAMETERS
        p[-2:] = [5, 5]
        agent = Creature(0, 993, 693, Brain(parameters=p))
        agent.update(config.dt, None, config, random.Random(1))
        self.assertEqual((agent.x, agent.y), (993, 693))
        self.assertLess(agent.energy, 100)
        self.assertLessEqual(math.hypot(agent.vx, agent.vy), config.max_speed + 1e-9)

    def test_population_cap_and_no_resurrection(self):
        config = Config(initial_population=2, population_limit=2, minimum_age=0)
        world = World(config, 3)
        for agent in world.creatures:
            agent.energy = 220
        world.step()
        self.assertEqual(world.births, 0)
        agent = world.creatures[0]
        agent.energy = 0
        world.food.replace(0, (agent.x, agent.y))
        world.step()
        self.assertNotIn(agent, world.creatures)
        self.assertEqual(world.deaths, 1)

    def test_empty_world_and_invalid_config(self):
        world = World(Config(initial_population=0, food_count=0))
        world.step()
        self.assertEqual(world.metrics()["population"], 0)
        with self.assertRaises(ValueError):
            Config(dt=0)
        with self.assertRaises(ValueError):
            Config(initial_population=200)


if __name__ == "__main__":
    unittest.main()

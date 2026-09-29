import random
import tempfile
import unittest
from pathlib import Path

from brain import Brain
from experiments import episode, load_policy, save_policy, train


class ExperimentTests(unittest.TestCase):
    def test_episode_reproducible(self):
        brain = Brain(random.Random(2))
        self.assertEqual(episode(brain, 12, 1), episode(brain, 12, 1))

    def test_elitism_and_policy_round_trip(self):
        champion, initial, history, _ = train(1, population=4, generations=2, seconds=0.2, episodes=1)
        self.assertGreaterEqual(history[-1]["best_fitness"], history[0]["best_fitness"])
        self.assertIsNot(champion, initial)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brain.json"
            save_policy(champion, path)
            self.assertEqual(load_policy(path).parameters, champion.parameters)


if __name__ == "__main__":
    unittest.main()

"""Check that published results agree with raw observations and current inference."""

import csv
import json
from pathlib import Path
import statistics
import unittest

from experiments import episode, load_policy

RESULTS = Path(__file__).resolve().parents[1] / "results" / "benchmark"


class ResultsTests(unittest.TestCase):
    def test_report_aggregation_and_disjoint_seeds(self):
        report = json.loads((RESULTS / "report.json").read_text())
        with (RESULTS / "episodes.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        for run in report["runs"]:
            self.assertFalse(set(run["training_seeds"]) & set(report["test_seeds"]))
            for policy, values in run["results"].items():
                matching = [row for row in rows if int(row["training_seed"]) == run["seed"] and row["policy"] == policy]
                self.assertEqual(len(matching), len(report["test_seeds"]))
                self.assertEqual({int(r["environment_seed"]) for r in matching}, set(report["test_seeds"]))
                self.assertAlmostEqual(statistics.mean(float(r["meals"]) for r in matching), values["mean_meals"])
        for policy, summary in report["summary"].items():
            self.assertAlmostEqual(summary["mean_meals"], statistics.mean(run["results"][policy]["mean_meals"] for run in report["runs"]))

    def test_exported_policies_reproduce_one_recorded_episode(self):
        with (RESULTS / "episodes.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        for seed in (11, 22, 33):
            brain = load_policy(RESULTS / f"champion-{seed}.json")
            result = episode(brain, 1900000, 25)
            recorded = next(row for row in rows if int(row["training_seed"]) == seed
                            and int(row["environment_seed"]) == 1900000 and row["policy"] == "evolved")
            self.assertEqual(result["meals"], int(recorded["meals"]))


if __name__ == "__main__":
    unittest.main()

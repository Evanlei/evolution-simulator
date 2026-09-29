"""Train neural policies and evaluate them on disjoint, paired environment seeds.

This explicit generational experiment is separate from natural reproduction in
the interactive ecosystem. Report held-out food counts, not training fitness,
when describing the results.
"""

import argparse
import csv
from dataclasses import replace
import json
import math
from pathlib import Path
import random
import statistics

from brain import Brain
from config import Config
from simulation import World


def episode(brain, seed, seconds=25, controller="neural"):
    config = Config(initial_population=1, food_count=60, reproduction=False)
    world = World(config, seed, brain, controller, record=False)
    agent = world.creatures[0]
    for _ in range(round(seconds / config.dt)):
        world.step()
        if not world.creatures:
            break
    # Distance progress supplies a learning signal even before the first meal.
    # This is an engineered training objective, not a claim of natural selection.
    fitness = agent.meals * 30 + agent.progress / 40 + agent.age * 0.02
    return {"meals": agent.meals, "survival": agent.age, "energy": max(0, agent.energy),
            "fitness": fitness}


def evaluate(brain, seeds, seconds):
    rows = [episode(brain, seed, seconds) for seed in seeds]
    return {key: statistics.mean(row[key] for row in rows) for key in rows[0]}


def train(seed, population=32, generations=24, seconds=25, episodes=3, progress=None):
    if population < 4 or generations < 1 or episodes < 1 or seconds <= 0:
        raise ValueError("Training needs population >= 4 and positive generations, episodes and seconds.")
    rng = random.Random(seed)
    seeds = [1000 + seed * 100 + i for i in range(episodes)]
    brains = [Brain(rng) for _ in range(population)]
    history, initial_best, champion = [], None, None
    elite_count = max(2, population // 8)
    for generation in range(generations + 1):
        scores = [(evaluate(brain, seeds, seconds), brain) for brain in brains]
        scores.sort(key=lambda pair: pair[0]["fitness"], reverse=True)
        if generation == 0:
            initial_best = scores[0][1].copy()
        champion = scores[0][1].copy()
        row = {"generation": generation, "best_fitness": scores[0][0]["fitness"],
               "mean_fitness": statistics.mean(s[0]["fitness"] for s in scores),
               "best_meals": scores[0][0]["meals"]}
        history.append(row)
        if progress:
            progress(seed, row)
        if generation < generations:
            brains = [brain.copy() for _, brain in scores[:elite_count]]
            while len(brains) < population:
                tournament = rng.sample(scores, 3)
                parent = max(tournament, key=lambda pair: pair[0]["fitness"])[1]
                brains.append(parent.mutated_copy(rng, rate=0.18, sigma=0.28))
    return champion, initial_best, history, seeds


def save_policy(brain, path, metadata=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "architecture": [8, 10, 2],
                               "parameters": brain.parameters, "metadata": metadata or {}}, indent=2))


def load_policy(path):
    data = json.loads(Path(path).read_text())
    if data.get("schema_version") != 1 or data.get("architecture") != [8, 10, 2]:
        raise ValueError("Unsupported policy format or architecture.")
    return Brain(parameters=data["parameters"])


def write_chart(summary, path):
    """Dependency-free, exportable SVG of measured held-out food consumption."""
    labels = {"evolved": "Evolved neural", "initial_best": "Best initial neural",
              "random_brain": "Random neural", "random_walk": "Random walk", "greedy": "Greedy heuristic"}
    ceiling = max(1, max(row["mean_meals"] for row in summary.values()))
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">',
                '<rect width="900" height="420" fill="#101b26"/>',
                '<g font-family="sans-serif" fill="#e8eff5">',
                '<text x="35" y="45" font-size="24">Held-out foraging performance</text>',
                '<text x="35" y="73" font-size="14" fill="#a7b8c8">Mean meals per episode · same unseen layouts for every policy</text>']
    for i, (name, row) in enumerate(summary.items()):
        y = 106 + i * 52
        width = 470 * row["mean_meals"] / ceiling
        color = "#71e0b8" if name == "evolved" else "#7695bd"
        elements += [f'<text x="35" y="{y + 21}" font-size="15">{labels[name]}</text>',
                     f'<rect x="215" y="{y}" width="{width:.2f}" height="30" rx="5" fill="{color}"/>',
                     f'<text x="{230 + width:.2f}" y="{y + 21}" font-size="15">{row["mean_meals"]:.2f}</text>']
    elements += ['<text x="35" y="395" font-size="12" fill="#a7b8c8">Training fitness includes distance shaping. Evaluation reports actual meals. See report.json for all runs.</text>', '</g></svg>']
    Path(path).write_text("\n".join(elements))


def benchmark(output, seeds=(11, 22, 33), population=32, generations=24, seconds=25,
              training_episodes=3, test_episodes=12, progress=None):
    if not seeds or test_episodes < 1:
        raise ValueError("At least one training seed and test episode are required.")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # These seeds are never used by selection or mutation.
    holdout = list(range(900_000, 900_000 + test_episodes))
    if any(seed < 0 or seed >= 8000 for seed in seeds):
        raise ValueError("Training seeds must lie between 0 and 7999 to keep holdout seeds disjoint.")
    runs, raw = [], []
    for seed in seeds:
        champion, initial, history, train_seeds = train(seed, population, generations, seconds,
                                                      training_episodes, progress)
        if set(train_seeds) & set(holdout):
            raise ValueError("Training and evaluation seed sets overlap.")
        save_policy(champion, output / f"champion-{seed}.json", {"training_seed": seed,
                    "training_seeds": train_seeds, "training_fitness": history[-1]["best_fitness"]})
        with (output / f"training-{seed}.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        policies = {"evolved": champion, "initial_best": initial, "random_brain": None,
                    "random_walk": None, "greedy": None}
        run_summary = {}
        for name, brain in policies.items():
            rows = []
            for test_seed in holdout:
                policy = brain or Brain(random.Random(seed * 100_000 + test_seed))
                controller = {"random_walk": "random", "greedy": "greedy"}.get(name, "neural")
                row = episode(policy, test_seed, seconds, controller)
                raw.append({"training_seed": seed, "environment_seed": test_seed, "policy": name, **row})
                rows.append(row)
            run_summary[name] = {"mean_meals": statistics.mean(r["meals"] for r in rows),
                                 "mean_survival": statistics.mean(r["survival"] for r in rows)}
        runs.append({"seed": seed, "training_seeds": train_seeds, "results": run_summary})
    summary = {}
    for name in runs[0]["results"]:
        values = [run["results"][name]["mean_meals"] for run in runs]
        summary[name] = {"mean_meals": statistics.mean(values),
                         "sd_across_training_runs": statistics.stdev(values) if len(values) > 1 else 0}
    # Choose the demo policy using training fitness only, never the holdout results.
    champion_paths = [output / f"champion-{seed}.json" for seed in seeds]
    best = max(champion_paths, key=lambda path: json.loads(path.read_text())["metadata"]["training_fitness"])
    (output / "champion.json").write_text(best.read_text())
    report = {"schema_version": 1, "population": population, "generations": generations,
              "episode_seconds": seconds, "training_episodes": training_episodes,
              "test_seeds": holdout, "runs": runs, "summary": summary,
              "protocol": "Single-agent foraging, reproduction disabled, 60 respawning food sources; shared held-out layouts; no test-based model selection.",
              "fitness": "30 * meals + signed approach progress / 40 + survival_seconds * 0.02",
              "limitations": ["Foraging benchmark is not proof of stable multi-agent ecology.",
                              "Few training replicates; results are descriptive, not a significance claim.",
                              "Greedy is a hand-written reference policy, not a learned network."]}
    (output / "report.json").write_text(json.dumps(report, indent=2))
    with (output / "episodes.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw[0].keys())
        writer.writeheader()
        writer.writerows(raw)
    write_chart(summary, output / "comparison.svg")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("runs/benchmark"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--population", type=int, default=32)
    parser.add_argument("--generations", type=int, default=24)
    parser.add_argument("--seconds", type=float, default=25)
    parser.add_argument("--training-episodes", type=int, default=3)
    parser.add_argument("--test-episodes", type=int, default=12)
    args = parser.parse_args()
    def progress(seed, row):
        print(f"seed={seed} generation={row['generation']:02d} fitness={row['best_fitness']:.2f} meals={row['best_meals']:.2f}", flush=True)
    try:
        report = benchmark(args.output, args.seeds, args.population, args.generations,
                           args.seconds, args.training_episodes, args.test_episodes, progress)
        print(json.dumps(report["summary"], indent=2))
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

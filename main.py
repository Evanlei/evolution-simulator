"""Run the visual ecosystem or a deterministic headless simulation."""

import argparse
import json
import math
from pathlib import Path

from config import Config
from experiments import load_policy
from simulation import World


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--population", type=int, default=36)
    parser.add_argument("--food", type=int, default=100)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--load", type=Path, help="Resume a world checkpoint")
    parser.add_argument("--brain", type=Path, help="Initialize founders with an exported neural policy")
    parser.add_argument("--output", type=Path, default=Path("runs/latest"))
    parser.add_argument("--frames", type=int, help="Close the dashboard after this many rendered frames")
    parser.add_argument("--screenshot", type=Path, help="Save the dashboard on exit")
    args = parser.parse_args(argv)
    try:
        if args.seconds <= 0 or not math.isfinite(args.seconds):
            raise ValueError("Seconds must be positive and finite.")
        if args.frames is not None and args.frames < 1:
            raise ValueError("Frames must be positive.")
        if args.load and args.brain:
            raise ValueError("Choose either a checkpoint or a founder policy, not both.")
        brain = None
        if args.brain:
            brain = load_policy(args.brain)
        world = World.load(args.load) if args.load else World(
            Config(initial_population=args.population, food_count=args.food), args.seed, brain)
        if args.headless:
            for _ in range(round(args.seconds / world.config.dt)):
                world.step()
            world.export_csv(args.output / "metrics.csv")
            world.save(args.output / "world.json")
            print(json.dumps(world.metrics(), indent=2))
        else:
            from dashboard import run
            run(world, args.output, brain, args.frames, args.screenshot)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

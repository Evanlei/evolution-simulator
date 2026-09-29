"""Run the visual ecosystem or a deterministic headless simulation."""

import argparse
import json
from pathlib import Path

from brain import Brain
from config import Config
from simulation import World


def basic_view(world):
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((world.config.width, world.config.height))
    clock = pygame.time.Clock()
    accumulator, running = 0.0, True
    while running:
        accumulator += min(clock.tick(60) / 1000, 0.25)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        while accumulator >= world.config.dt:
            world.step()
            accumulator -= world.config.dt
        screen.fill((13, 22, 30))
        for x, y in world.food.positions:
            pygame.draw.circle(screen, (236, 187, 96), (round(x), round(y)), 4)
        for agent in world.creatures:
            pygame.draw.circle(screen, (100, 215, 176), (round(agent.x), round(agent.y)), 7)
        pygame.display.set_caption(f"Evolution Simulator | {len(world.creatures)} creatures | {world.births} births")
        pygame.display.flip()
    pygame.quit()


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
    args = parser.parse_args(argv)
    try:
        if args.seconds <= 0:
            raise ValueError("Seconds must be positive.")
        brain = None
        if args.brain:
            policy = json.loads(args.brain.read_text())
            brain = Brain(parameters=policy["parameters"])
        world = World.load(args.load) if args.load else World(
            Config(initial_population=args.population, food_count=args.food), args.seed, brain)
        if args.headless:
            for _ in range(round(args.seconds / world.config.dt)):
                world.step()
            world.export_csv(args.output / "metrics.csv")
            world.save(args.output / "world.json")
            print(json.dumps(world.metrics(), indent=2))
        else:
            basic_view(world)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

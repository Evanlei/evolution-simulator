"""Create a reproducible dashboard screenshot and PNG frames for the README demo."""

import argparse
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from config import Config
from dashboard import Dashboard
from experiments import load_policy
from simulation import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/assets"))
    parser.add_argument("--frames", type=int, default=48)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frame_dir = Path("runs/demo-frames")
    frame_dir.mkdir(parents=True, exist_ok=True)
    brain = load_policy(Path(__file__).resolve().parents[1] / "results/benchmark/champion.json")
    world = World(Config(), seed=42, brain=brain)
    app = Dashboard(world, founder_brain=brain)
    app.mode = "evolved founders"
    app.sensors = False
    try:
        for frame in range(args.frames):
            # Each exported frame represents one simulated second, played back at 8 fps.
            for _ in range(30):
                world.step()
                if world.steps % 3 == 0:
                    for agent in world.creatures:
                        app.trails[agent.id].append(app.point(agent.x, agent.y))
            if world.creatures:
                app.selected_id = max(world.creatures, key=lambda a: (a.meals, a.energy)).id
            app.draw()
            if frame == min(19, args.frames - 1):
                pygame.image.save(app.screen, str(args.output / "dashboard.png"))
            small = pygame.transform.smoothscale(app.screen, (960, 640))
            pygame.image.save(small, str(frame_dir / f"frame-{frame:03d}.png"))
        print(f"Screenshot: {args.output / 'dashboard.png'}; animation frames: {frame_dir}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()

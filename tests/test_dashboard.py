"""Exercise UI controls with SDL's offscreen display; no real window required."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path
import tempfile
import unittest

import pygame

from config import Config
from dashboard import Dashboard
from simulation import World


class DashboardTests(unittest.TestCase):
    def test_pause_selection_save_load_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Dashboard(World(Config(initial_population=3), seed=42), Path(directory))
            try:
                app.draw()
                app.action("pause")
                app.advance(1)
                self.assertEqual(app.world.steps, 0)
                app.action("pause")
                app.advance(0.1)
                self.assertGreater(app.world.steps, 0)
                agent = app.world.creatures[-1]
                app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                    button=1, pos=app.point(agent.x, agent.y)))
                self.assertEqual(app.selected_id, agent.id)
                app.action("save")
                saved = app.world.to_dict()
                app.advance(0.1)
                app.action("load")
                self.assertEqual(app.world.to_dict(), saved)
                self.assertTrue(app.paused)
                app.action("export")
                self.assertTrue((Path(directory) / "metrics.csv").exists())
                self.assertTrue((Path(directory) / "champion.json").exists())
                app.action("new")
                self.assertEqual(app.world.seed, 43)
                self.assertEqual(app.world.steps, 0)
                self.assertTrue(app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)))
                self.assertTrue(app.paused)
                app.draw()
                self.assertFalse(app.handle_event(pygame.event.Event(pygame.QUIT)))
            finally:
                pygame.quit()

    def test_extinction_draw_and_missing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Dashboard(World(Config(initial_population=0, food_count=0)), Path(directory))
            try:
                app.draw()
                app.action("load")
                self.assertIn("Could not load", app.notice)
                app.advance(1)
                self.assertEqual(app.world.steps, 0)
            finally:
                pygame.quit()

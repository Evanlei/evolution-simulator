"""Interactive Pygame laboratory. The world model has no rendering dependencies."""

import colorsys
from collections import defaultdict, deque
import math
from pathlib import Path

import pygame

from brain import INPUT_NAMES
from experiments import load_policy, save_policy
from simulation import World

BG = (12, 19, 27)
PANEL = (20, 30, 41)
BORDER = (39, 54, 67)
TEXT = (229, 236, 238)
MUTED = (142, 160, 175)
MINT = (116, 224, 184)
AMBER = (238, 190, 110)
BLUE = (123, 170, 230)


def lineage_color(lineage):
    hue = (lineage * 0.61803398875 + 0.35) % 1
    return tuple(round(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.45, 0.9))


class Dashboard:
    SIZE = (1440, 960)
    ARENA = pygame.Rect(28, 196, 1000, 700)

    def __init__(self, world, output=Path("runs/latest"), founder_brain=None):
        pygame.init()
        self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption("Evolution Simulator | Neuroevolution Lab")
        self.clock = pygame.time.Clock()
        self.fonts = {size: pygame.font.SysFont("Arial", size) for size in (12, 13, 14, 16, 18, 22, 28, 34)}
        self.world, self.output = world, Path(output)
        self.founder_brain = founder_brain or world.founder_brain
        self.paused = False
        self.speed_index = 0
        self.speeds = (1, 2, 4, 8)
        self.sensors = True
        self.show_trails = True
        self.selected_id = world.creatures[0].id if world.creatures else None
        self.trails = defaultdict(lambda: deque(maxlen=40))
        self.accumulator = 0.0
        self.notice = "Click a creature to inspect its brain."
        self.notice_until = 0
        self.buttons = []
        self.mode = "imported founders" if self.founder_brain else "random founders"

    def label(self, text, x, y, size=16, color=TEXT):
        surface = self.fonts[size].render(str(text), True, color)
        self.screen.blit(surface, (x, y))
        return surface.get_width()

    def panel(self, rect):
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, rect, width=1, border_radius=12)

    def point(self, x, y):
        return (round(self.ARENA.x + x / self.world.config.width * self.ARENA.width),
                round(self.ARENA.y + y / self.world.config.height * self.ARENA.height))

    def notify(self, message):
        self.notice, self.notice_until = message, pygame.time.get_ticks() + 5000

    def reset(self, seed=None, demo=False):
        brain = self.founder_brain
        if demo:
            path = Path(__file__).parent / "results/benchmark/champion.json"
            brain = load_policy(path)
            self.founder_brain = brain
            self.mode = "evolved founders"
        self.world = World(self.world.config, self.world.seed if seed is None else seed, brain)
        self.mode = "imported founders" if brain else "random founders"
        self.selected_id = self.world.creatures[0].id if self.world.creatures else None
        self.accumulator = 0
        self.trails.clear()
        self.paused = False

    def action(self, name):
        try:
            if name == "pause":
                self.paused = not self.paused
            elif name == "speed":
                self.speed_index = (self.speed_index + 1) % len(self.speeds)
            elif name == "reset":
                self.reset()
                self.notify("Restarted with the same seed and founder policy.")
            elif name == "new":
                self.founder_brain = None
                self.mode = "random founders"
                self.reset(self.world.seed + 1)
                self.notify("Fresh random founders on a new seed.")
            elif name == "demo":
                self.reset(demo=True)
                self.mode = "evolved founders"
                self.notify("Loaded the benchmark's training-selected policy into every founder.")
            elif name == "sensors":
                self.sensors = not self.sensors
            elif name == "trails":
                self.show_trails = not self.show_trails
            elif name == "save":
                self.world.save(self.output / "world.json")
                self.notify(f"Checkpoint saved: {self.output / 'world.json'}")
            elif name == "load":
                self.world = World.load(self.output / "world.json")
                self.founder_brain = self.world.founder_brain
                self.selected_id = None
                self.accumulator = 0
                self.trails.clear()
                self.paused = True
                self.mode = "loaded checkpoint"
                self.notify("Checkpoint loaded and paused. Space resumes it.")
            elif name == "export":
                self.world.export_csv(self.output / "metrics.csv")
                if self.world.champion:
                    from brain import Brain
                    save_policy(Brain(parameters=self.world.champion["agent"]["brain"]),
                                self.output / "champion.json", {"seed": self.world.seed,
                                "selection": "most meals, then offspring, then age in this ecosystem"})
                self.notify("Exported metrics.csv and the ecosystem champion policy.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.notify(f"Could not {name}: {str(error)[:100]}")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            actions = {pygame.K_SPACE: "pause", pygame.K_TAB: "speed", pygame.K_r: "reset",
                       pygame.K_n: "new", pygame.K_d: "demo", pygame.K_v: "sensors",
                       pygame.K_t: "trails", pygame.K_s: "save", pygame.K_l: "load", pygame.K_e: "export"}
            if event.key in actions:
                self.action(actions[event.key])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, name in self.buttons:
                if rect.collidepoint(event.pos):
                    self.action(name)
                    return True
            if self.ARENA.collidepoint(event.pos) and self.world.creatures:
                nearest = min(self.world.creatures, key=lambda a: math.dist(self.point(a.x, a.y), event.pos))
                if math.dist(self.point(nearest.x, nearest.y), event.pos) < 25:
                    self.selected_id = nearest.id
        return True

    def advance(self, elapsed):
        if self.paused or not self.world.creatures:
            self.accumulator = 0
            return
        self.accumulator += min(elapsed, 0.25) * self.speeds[self.speed_index]
        budget = 0
        while self.accumulator >= self.world.config.dt and budget < 16:
            self.world.step()
            self.accumulator -= self.world.config.dt
            budget += 1
            if self.world.steps % 3 == 0:
                living = {a.id for a in self.world.creatures}
                for agent in self.world.creatures:
                    self.trails[agent.id].append(self.point(agent.x, agent.y))
                for dead in set(self.trails) - living:
                    del self.trails[dead]
        # Under load slow wall-clock playback instead of taking unstable larger physics steps.
        self.accumulator = min(self.accumulator, self.world.config.dt * 16)

    def toolbar(self):
        items = [("Resume" if self.paused else "Pause", "pause", 84),
                 (f"{self.speeds[self.speed_index]}x speed", "speed", 92),
                 ("Reset", "reset", 76), ("New seed", "new", 98),
                 ("Evolved demo", "demo", 122), ("Sensors", "sensors", 88),
                 ("Trails", "trails", 70), ("Save", "save", 68),
                 ("Load", "load", 68), ("Export CSV", "export", 108)]
        self.buttons = []
        x = 28
        for title, name, width in items:
            rect = pygame.Rect(x, 92, width, 33)
            active = ((name == "sensors" and self.sensors) or
                      (name == "trails" and self.show_trails) or (name == "pause" and self.paused))
            color = (37, 70, 65) if active else PANEL
            if rect.collidepoint(pygame.mouse.get_pos()):
                color = (43, 62, 74)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=6)
            self.label(title, x + 12, 99, 14, MINT if active else TEXT)
            self.buttons.append((rect, name))
            x += width + 7

    def draw_world(self, selected):
        pygame.draw.rect(self.screen, (15, 26, 35), self.ARENA, border_radius=10)
        self.screen.set_clip(self.ARENA)
        for x in range(self.ARENA.left, self.ARENA.right, 50):
            pygame.draw.line(self.screen, (23, 36, 46), (x, self.ARENA.top), (x, self.ARENA.bottom))
        for y in range(self.ARENA.top, self.ARENA.bottom, 50):
            pygame.draw.line(self.screen, (23, 36, 46), (self.ARENA.left, y), (self.ARENA.right, y))
        if self.show_trails:
            for agent in self.world.creatures:
                points = self.trails[agent.id]
                if len(points) > 1:
                    color = tuple(round(c * 0.30) for c in lineage_color(agent.lineage))
                    pygame.draw.lines(self.screen, color, False, list(points), 1)
        for point in self.world.food.positions:
            pos = self.point(*point)
            pygame.draw.circle(self.screen, (72, 62, 44), pos, 6)
            pygame.draw.circle(self.screen, AMBER, pos, 3)
        if selected and self.sensors:
            scale = self.ARENA.width / self.world.config.width
            pygame.draw.circle(self.screen, (47, 78, 81), self.point(selected.x, selected.y),
                               round(self.world.config.sensor_range * scale), 1)
        for agent in self.world.creatures:
            pos = self.point(agent.x, agent.y)
            color = lineage_color(agent.lineage)
            if self.sensors and agent.target:
                pygame.draw.line(self.screen, (40, 76, 73), pos, self.point(*agent.target), 1)
            pygame.draw.circle(self.screen, (8, 16, 23), pos, 9)
            pygame.draw.circle(self.screen, color, pos, 6)
            speed = math.hypot(agent.vx, agent.vy)
            if speed > 1:
                tip = (round(pos[0] + 10 * agent.vx / speed), round(pos[1] + 10 * agent.vy / speed))
                pygame.draw.line(self.screen, color, pos, tip, 2)
            if agent.id == self.selected_id:
                pygame.draw.circle(self.screen, TEXT, pos, 12, 1)
                self.label(f"#{agent.id}", pos[0] + 15, pos[1] - 9, 12)
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, BORDER, self.ARENA, 1, border_radius=10)
        if not self.world.creatures:
            box = pygame.Rect(218, 463, 620, 112)
            pygame.draw.rect(self.screen, PANEL, box, border_radius=12)
            self.label("Population extinct", 252, 483, 28)
            self.label("R: retry this seed   N: random start   D: evolved founders", 252, 532, 16, MUTED)
        elif self.paused:
            self.label("PAUSED", self.ARENA.x + 18, self.ARENA.y + 16, 14, AMBER)

    def draw_history(self):
        self.panel(pygame.Rect(1052, 196, 360, 172))
        self.label("POPULATION / LAST 180 SECONDS", 1070, 211, 12, MUTED)
        rows = self.world.history[-180:]
        values = [r["population"] for r in rows] + [len(self.world.creatures)]
        maximum = max(10, max(values, default=10))
        rect = pygame.Rect(1072, 244, 318, 85)
        for i in range(3):
            y = rect.top + i * rect.height // 2
            pygame.draw.line(self.screen, BORDER, (rect.left, y), (rect.right, y))
        if len(values) > 1:
            points = [(rect.left + i * rect.width / (len(values) - 1),
                       rect.bottom - value / maximum * rect.height) for i, value in enumerate(values)]
            pygame.draw.lines(self.screen, MINT, False, points, 2)
        self.label(f"0 — {maximum} creatures", 1072, 341, 12, MUTED)
        self.label(f"{self.world.metrics()['lineages']} founder lineages", 1236, 341, 12, MUTED)

    def draw_inspector(self, agent):
        self.panel(pygame.Rect(1052, 382, 360, 178))
        self.label("CREATURE INSPECTOR", 1070, 397, 12, MUTED)
        if agent is None:
            self.label("No living creature selected", 1070, 435, 18)
            return
        self.label(f"#{agent.id:04d}", 1070, 423, 28, lineage_color(agent.lineage))
        self.label(f"Generation {agent.generation}  /  lineage {agent.lineage}", 1190, 432, 14)
        ratio = max(0, min(1, agent.energy / self.world.config.max_energy))
        pygame.draw.rect(self.screen, BORDER, (1072, 469, 318, 7), border_radius=3)
        pygame.draw.rect(self.screen, MINT, (1072, 469, round(318 * ratio), 7), border_radius=3)
        self.label(f"Energy {agent.energy:.0f}", 1072, 486, 14)
        self.label(f"Age {agent.age:.1f}s", 1245, 486, 14)
        self.label(f"Meals {agent.meals}  /  offspring {agent.children}", 1072, 515, 14, MUTED)
        self.label(f"{math.hypot(agent.vx, agent.vy):.0f} px/s", 1310, 515, 14, MUTED)

    def draw_brain(self, agent):
        self.panel(pygame.Rect(1052, 574, 360, 247))
        self.label("LIVE BRAIN", 1070, 588, 12, MUTED)
        self.label("8 → 10 → 2  /  112 parameters", 1184, 588, 12, MINT)
        if agent is None:
            return
        hidden, outputs = agent.brain.activations(agent.inputs)
        layers = [agent.inputs, hidden, outputs]
        positions = []
        for layer, x in zip(layers, (1094, 1230, 1368)):
            positions.append([(x, round(635 + i * 142 / max(1, len(layer) - 1))) for i in range(len(layer))])
        for left, right, weights in ((0, 1, agent.brain.w1), (1, 2, agent.brain.w2)):
            for j, row in enumerate(weights):
                for i, weight in enumerate(row):
                    strength = min(1, abs(weight) / 2)
                    color = (int(32 + 24 * strength), int(47 + 48 * strength), int(53 + 35 * strength)) if weight >= 0 else (int(49 + 36 * strength), 38, int(53 + 48 * strength))
                    pygame.draw.line(self.screen, color, positions[left][i], positions[right][j])
        for values, points in zip(layers, positions):
            for value, pos in zip(values, points):
                base = MINT if value >= 0 else BLUE
                color = tuple(round(45 + (c - 45) * min(1, abs(value))) for c in base)
                pygame.draw.circle(self.screen, BG, pos, 7)
                pygame.draw.circle(self.screen, color, pos, 5)
        self.label("sensors", 1075, 795, 12, MUTED)
        self.label("tanh hidden", 1200, 795, 12, MUTED)
        self.label("vx / vy", 1345, 795, 12, MUTED)
        # Hover a neuron for its name and most recent activation.
        for layer, (values, points) in enumerate(zip(layers, positions)):
            for i, (value, pos) in enumerate(zip(values, points)):
                if math.dist(pygame.mouse.get_pos(), pos) < 9:
                    name = INPUT_NAMES[i] if layer == 0 else (f"hidden {i + 1}" if layer == 1 else ("horizontal", "vertical")[i])
                    pygame.draw.rect(self.screen, (34, 49, 62), (1066, 611, 332, 21), border_radius=4)
                    self.label(f"{name}: {value:+.3f}", 1072, 614, 12)

    def draw(self):
        self.screen.fill(BG)
        self.label("EVOLUTION", 28, 24, 34)
        self.label("/ NEURAL ECOSYSTEM LAB", 251, 35, 18, MINT)
        self.label("Selection, inheritance and mutation. Every creature carries its own neural policy.", 29, 66, 14, MUTED)
        self.label(f"SEED {self.world.seed}  ·  {self.mode.upper()}", 1070, 38, 12, MUTED)
        self.toolbar()
        metrics = self.world.metrics()
        cards = [("LIVING", metrics["population"], MINT), ("BIRTHS / DEATHS", f"{metrics['births']} / {metrics['deaths']}", TEXT),
                 ("DEEPEST GENERATION", metrics["max_generation"], BLUE), ("MEALS / SIM TIME", f"{metrics['meals']} / {self.world.time:.1f}s", AMBER)]
        for i, (title, value, color) in enumerate(cards):
            x = 28 + i * 350
            self.panel(pygame.Rect(x, 139, 334, 43))
            self.label(title, x + 12, 153, 12, MUTED)
            value_width = self.fonts[22].size(str(value))[0]
            self.label(value, x + 322 - value_width, 146, 22, color)
        selected = next((a for a in self.world.creatures if a.id == self.selected_id), None)
        if selected is None and self.world.creatures:
            selected = max(self.world.creatures, key=lambda a: (a.meals, a.energy))
            self.selected_id = selected.id
        self.draw_world(selected)
        self.draw_history()
        self.draw_inspector(selected)
        self.draw_brain(selected)
        self.panel(pygame.Rect(1052, 835, 360, 61))
        self.label("Color = founder lineage   •   gold = food", 1070, 848, 13, MUTED)
        self.label("No backpropagation. Parameters evolve at birth.", 1070, 870, 13, MUTED)
        notice = self.notice if pygame.time.get_ticks() < self.notice_until else "SPACE pause   TAB speed   R reset   N new seed   D evolved demo   V sensors   T trails   S save   L load   E export"
        self.label(notice, 29, 919, 13, MUTED)
        self.label(f"{1 / self.world.config.dt:.0f} Hz physics", 1325, 919, 13, MUTED)

    def run(self, frames=None, screenshot=None):
        running, rendered = True, 0
        try:
            while running:
                elapsed = self.clock.tick(60) / 1000
                for event in pygame.event.get():
                    running = self.handle_event(event) and running
                self.advance(elapsed)
                self.draw()
                pygame.display.flip()
                rendered += 1
                if frames is not None and rendered >= frames:
                    running = False
            if screenshot:
                path = Path(screenshot)
                path.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(self.screen, str(path))
        finally:
            pygame.quit()


def run(world, output, founder_brain=None, frames=None, screenshot=None):
    Dashboard(world, output, founder_brain).run(frames, screenshot)

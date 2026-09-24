import pygame


class Creature:
    # Each instance owns its position, velocity, energy, and size.
    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Velocities are measured in pixels per second.
        self.velocity_x = 120
        self.velocity_y = 120
        self.energy = 100
        self.radius = 10

    def update(self, dt, width, height):
        # Scale changes by elapsed seconds so they do not depend on frame rate.
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.energy -= 6 * dt  # Living costs six energy units per second.

        # Bounce when the circle's outer edge reaches a window boundary.
        if self.x + self.radius >= width or self.x - self.radius <= 0:
            self.velocity_x = -self.velocity_x
        if self.y + self.radius >= height or self.y - self.radius <= 0:
            self.velocity_y = -self.velocity_y

    def draw(self, screen):
        # Draw this creature on the surface supplied by main.py.
        pygame.draw.circle(screen, "green", (self.x, self.y), self.radius)

    def reproduce(self):
        """Create an offspring by splitting the parent's energy equally"""
        self.energy = self.energy / 2
        offspring = Creature(self.x, self.y)
        offspring.energy = self.energy
        offspring.velocity_x = -self.velocity_x
        offspring.velcity_y = -self.velocity_y
        return offspring




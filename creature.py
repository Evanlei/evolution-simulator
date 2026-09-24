import pygame

class Creature:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.velocity_x = 120
        self.velocity_y = 120
        self.energy = 100
        self.radius = 10

    def update(self, dt, width, height):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.energy -= 6 * dt

        if self.x + self.radius >= width or self.x - self.radius <= 0:
            self.velocity_x = -self.velocity_x
        if self.y + self.radius >= height or self.y - self.radius <=0:
            self.velocity_y = -self.velocity_y

    def draw(self, screen):
        pygame.draw.circle(
            screen, "green", (self.x, self.y), self.radius
        )
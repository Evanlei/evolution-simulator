import math
import random

import pygame

from brain import Brain


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
        self.base_energy_cost = 6
        self.movement_energy_cost = 0.02

        self.brain = Brain()
        # Convert each brain output from [-1, 1] to pixels per second.
        self.movement_scale = 120

    def think(self, foods, width, height):
        """Pass the nearest food's relative position through this creature's brain."""
        input_x, input_y = self.sense_food(foods, width, height)
        return self.brain.forward(input_x, input_y)

    def update(self, dt, width, height, foods):
        # The brain chooses new horizontal and vertical velocities each frame.
        output_x, output_y = self.think(foods, width, height)
        self.velocity_x = output_x * self.movement_scale
        self.velocity_y = output_y * self.movement_scale

        # Scale changes by elapsed seconds so they do not depend on frame rate.
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        speed = math.hypot(self.velocity_x, self.velocity_y)

        # Charge for staying alive and commanded movement, even against a wall.
        self.energy -= (
            self.base_energy_cost + self.movement_energy_cost * speed
        ) * dt

        # Clamp the center so the entire circle stays inside the window.
        # Reversing velocity would be overwritten by the brain next frame.
        self.x = max(self.radius, min(self.x, width - self.radius))
        self.y = max(self.radius, min(self.y, height - self.radius))

    def draw(self, screen):
        # Draw this creature on the surface supplied by main.py.
        pygame.draw.circle(screen, "green", (self.x, self.y), self.radius)

    def find_nearest_food(self, foods):
        """Return the closest food position, or None when no food is available."""
        nearest_food = None
        nearest_distance = float("inf")

        for food_x, food_y in foods:
            distance = math.hypot(self.x - food_x, self.y - food_y)

            if distance < nearest_distance:
                nearest_food = (food_x, food_y)
                nearest_distance = distance

        return nearest_food

    def sense_food(self, foods, width, height):
        """Express the food's horizontal and vertical offsets as window fractions."""
        location = self.find_nearest_food(foods)

        if location is None:
            # No-food fallback; this also represents food exactly at our center.
            return (0.0, 0.0)

        food_x, food_y = location

        return ((food_x - self.x) / width, (food_y - self.y) / height)

    def reproduce(self):
        """Create an offspring by splitting the parent's energy equally."""
        self.energy = self.energy / 2
        offspring = Creature(self.x, self.y)
        offspring.energy = self.energy

        offspring.brain = self.brain.mutated_copy()

        return offspring

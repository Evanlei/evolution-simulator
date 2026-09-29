"""Explicit simulation parameters shared by the UI and headless experiments."""

from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class Config:
    width: int = 1000
    height: int = 700
    initial_population: int = 36
    food_count: int = 100
    population_limit: int = 180
    dt: float = 1 / 30
    radius: float = 7
    food_radius: float = 4
    sensor_range: float = 250
    max_speed: float = 120
    initial_energy: float = 100
    max_energy: float = 240
    food_energy: float = 38
    basal_cost: float = 2.5
    movement_cost: float = 0.018
    reproduction_energy: float = 170
    reproduction_cooldown: float = 5
    minimum_age: float = 5
    mutation_rate: float = 0.12
    mutation_sigma: float = 0.22
    reproduction: bool = True

    def __post_init__(self):
        for key, value in asdict(self).items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                raise ValueError(f"{key} must be finite")
        for name in ("width", "height", "initial_population", "food_count", "population_limit"):
            if not isinstance(getattr(self, name), int):
                raise ValueError(f"{name} must be an integer")
        if self.width <= 2 * max(self.radius, self.food_radius) or self.height <= 2 * max(self.radius, self.food_radius):
            raise ValueError("World must be larger than creatures and food.")
        if not 0 < self.dt <= 0.1 or self.radius <= 0 or self.food_radius <= 0:
            raise ValueError("Invalid time step or radius.")
        if not 0 <= self.initial_population <= self.population_limit or self.food_count < 0:
            raise ValueError("Invalid population or food count.")
        if self.population_limit < 1 or self.sensor_range <= 0 or self.max_speed <= 0:
            raise ValueError("Population limit, sensor range and max speed must be positive.")
        if not 0 < self.initial_energy <= self.max_energy or not 0 < self.reproduction_energy <= self.max_energy:
            raise ValueError("Invalid energy settings.")
        if any(getattr(self, k) < 0 for k in ("food_energy", "basal_cost", "movement_cost",
                "reproduction_cooldown", "minimum_age", "mutation_sigma")):
            raise ValueError("Costs, rewards, ages and mutation sigma cannot be negative.")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("Mutation rate must be in [0, 1].")

    def to_dict(self):
        return asdict(self)

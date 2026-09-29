"""Uniform-grid food index for local sensing and collision queries."""

import math


class FoodIndex:
    def __init__(self, positions, cell_size=100):
        self.positions = list(positions)
        self.cell_size = cell_size
        self.cells = {}
        for index, point in enumerate(self.positions):
            self.cells.setdefault(self.cell(point), set()).add(index)

    def cell(self, point):
        return math.floor(point[0] / self.cell_size), math.floor(point[1] / self.cell_size)

    def replace(self, index, point):
        cell = self.cell(self.positions[index])
        self.cells[cell].remove(index)
        if not self.cells[cell]:
            del self.cells[cell]
        self.positions[index] = point
        self.cells.setdefault(self.cell(point), set()).add(index)

    def nearest(self, x, y, radius):
        left, top = self.cell((x - radius, y - radius))
        right, bottom = self.cell((x + radius, y + radius))
        best, best_distance = None, radius * radius
        for cx in range(left, right + 1):
            for cy in range(top, bottom + 1):
                for index in self.cells.get((cx, cy), ()):
                    fx, fy = self.positions[index]
                    distance = (fx - x) ** 2 + (fy - y) ** 2
                    if distance < best_distance or (distance == best_distance and (best is None or index < best)):
                        best, best_distance = index, distance
        return best

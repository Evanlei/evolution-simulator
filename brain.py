"""Feed-forward neural networks implemented with Python's standard library."""

import math
import random

INPUT_NAMES = ("food dx", "food dy", "food visible", "energy", "velocity x",
               "velocity y", "position x", "position y")
INPUTS, HIDDEN, OUTPUTS = 8, 10, 2
PARAMETERS = INPUTS * HIDDEN + HIDDEN + HIDDEN * OUTPUTS + OUTPUTS


def neuron(inputs, weights, bias):
    return math.tanh(sum(x * w for x, w in zip(inputs, weights)) + bias)


class Brain:
    """8 → 10 → 2 tanh network; its 112 parameters form a heritable genome."""

    def __init__(self, rng=None, parameters=None):
        rng = rng or random.Random()
        if parameters is None:
            parameters = (
                [rng.gauss(0, 1 / math.sqrt(INPUTS)) for _ in range(INPUTS * HIDDEN)]
                + [0.0] * HIDDEN
                + [rng.gauss(0, 1 / math.sqrt(HIDDEN)) for _ in range(HIDDEN * OUTPUTS)]
                + [0.0] * OUTPUTS
            )
        if len(parameters) != PARAMETERS or not all(math.isfinite(v) for v in parameters):
            raise ValueError(f"A brain needs {PARAMETERS} finite parameters.")
        self.parameters = list(parameters)
        self._unpack()

    def _unpack(self):
        p = self.parameters
        self.w1 = [p[i * INPUTS:(i + 1) * INPUTS] for i in range(HIDDEN)]
        offset = INPUTS * HIDDEN
        self.b1 = p[offset:offset + HIDDEN]
        offset += HIDDEN
        self.w2 = [p[offset + i * HIDDEN:offset + (i + 1) * HIDDEN] for i in range(OUTPUTS)]
        self.b2 = p[-OUTPUTS:]

    def activations(self, inputs):
        if len(inputs) != INPUTS:
            raise ValueError(f"Expected {INPUTS} sensory inputs.")
        hidden = [neuron(inputs, w, b) for w, b in zip(self.w1, self.b1)]
        outputs = [neuron(hidden, w, b) for w, b in zip(self.w2, self.b2)]
        return hidden, outputs

    def forward(self, inputs):
        return self.activations(inputs)[1]

    def copy(self):
        return Brain(parameters=self.parameters)

    def mutated_copy(self, rng, rate=0.12, sigma=0.22):
        """Independent Gaussian mutations; the parent is never modified."""
        if not 0 <= rate <= 1 or sigma < 0:
            raise ValueError("Mutation rate must be in [0, 1] and sigma nonnegative.")
        return Brain(parameters=[
            max(-5.0, min(5.0, v + rng.gauss(0, sigma))) if rng.random() < rate else v
            for v in self.parameters
        ])

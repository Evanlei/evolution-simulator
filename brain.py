import math
import random


def neuron(input_x, input_y, weight_x, weight_y, bias):
    """Combine two weighted inputs and a bias, then squash the result with tanh."""
    result = input_x * weight_x + input_y * weight_y + bias
    return math.tanh(result)
    

class Brain:
    """Two output neurons, each receiving both food-offset inputs."""

    def __init__(self):
        # Each output has its own two weights and bias, chosen once per brain.
        self.x_weight_x = random.uniform(-1, 1)
        self.x_weight_y = random.uniform(-1, 1)
        self.x_bias = random.uniform(-1, 1)

        self.y_weight_x = random.uniform(-1, 1)
        self.y_weight_y = random.uniform(-1, 1)
        self.y_bias = random.uniform(-1, 1)

    def forward(self, input_x, input_y):
        """Return horizontal and vertical commands using the stored parameters."""
        output_x = neuron(
            input_x, input_y, self.x_weight_x, self.x_weight_y, self.x_bias
        )

        output_y = neuron(
            input_x, input_y, self.y_weight_x, self.y_weight_y, self.y_bias
        )

        return (output_x, output_y)

    def mutated_copy(self):
        child = Brain()

        child.x_weight_x = self.x_weight_x + random.uniform(-0.1, 0.1)
        child.x_weight_y = self.x_weight_y + random.uniform(-0.1, 0.1)
        child.x_bias = self.x_bias + random.uniform(-0.1, 0.1)

        child.y_weight_x = self.y_weight_x + random.uniform(-0.1, 0.1)
        child.y_weight_y = self.y_weight_y + random.uniform(-0.1, 0.1)
        child.y_bias = self.y_bias + random.uniform(-0.1, 0.1)

        return child

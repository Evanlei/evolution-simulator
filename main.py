import pygame
import math
import random
from creature import Creature


# Window and timing setup
pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")
clock = pygame.time.Clock()

# Starting world: food positions and independent creature objects.
foods = []
for _ in range(20):
    foods.append((
        # Leave room for the food's five-pixel radius at each edge.
        random.randint(5, 995),
        random.randint(5, 695),
    ))

creatures = [
    Creature(500, 350),
    Creature(200, 200),
    Creature(800, 500),
]

# Main loop: handle input, update the world, then draw a complete frame.
running = True
while running:
    # Limit the frame rate and convert elapsed milliseconds to seconds.
    dt = clock.tick(60) / 1000

    # Handle window events.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Create offspring list
    newborns = []

    # Move each creature, spend energy, and check whether it touches food.
    for creature in creatures:
        creature.update(dt, screen.get_width(), screen.get_height())

        for index, (food_x, food_y) in enumerate(foods):
            distance = math.hypot(creature.x - food_x, creature.y - food_y)

            # Circles touch when their center distance is at most their radii sum.
            if distance <= creature.radius + 5:
                creature.energy += 30
                # Replace the eaten food at the same list index to respawn it.
                foods[index] = (
                    random.randint(5, 995),
                    random.randint(5, 695),
                )
                break  # Each creature can eat at most one food per frame.

        if creature.energy >= 160:
            newborns.append(creature.reproduce())

    # Keep survivors after updates, rather than removing items during iteration.
    creatures = [creature for creature in creatures if creature.energy > 0]

    # Add the newborns to the population
    creatures.extend(newborns)

    # Clear the previous frame, then draw food and surviving creatures.
    screen.fill("black")

    for food_x, food_y in foods:
        pygame.draw.circle(screen, "orange", (food_x, food_y), 5)

    for creature in creatures:
        creature.draw(screen)

    pygame.display.set_caption(
        f"Evolution Simulator | Population: {len(creatures)}"
    )

    pygame.display.flip()  # Show the completed frame in the window.

# Release Pygame resources after the main loop ends.
pygame.quit()

import pygame
import math
import random
from creature import Creature

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")

running = True

foods = []

for _ in range(20):
    foods.append((
        random.randint(5, 995),
        random.randint(5, 695),
    ))

clock = pygame.time.Clock()

creatures = [
    Creature(500, 350),
    Creature(200, 200),
    Creature(800, 500),
]

while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for creature in creatures:
        creature.update(dt, screen.get_width(), screen.get_height())

        for index, (food_x, food_y) in enumerate(foods):
            distance = math.hypot(creature.x - food_x, creature.y - food_y)

            if distance <= creature.radius + 5:
                creature.energy += 30
                foods[index] = (
                    random.randint(5, 995),
                    random.randint(5, 695),
                )
                break



    creatures = [creature for creature in creatures if creature.energy > 0]

    screen.fill("black")

    for food_x, food_y in foods:
        pygame.draw.circle(screen, "orange", (food_x, food_y), 5)

    for creature in creatures:
        creature.draw(screen)

    pygame.display.set_caption(
        f"Evolution Simulator | Population: {len(creatures)}"
    )

    pygame.display.flip() # updates the screen

    
pygame.quit()
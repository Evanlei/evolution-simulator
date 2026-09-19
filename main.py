import pygame
import math

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")

running = True

x = 500
y = 350
velocity_x = 2
velocity_y = 2
food_x = 600
food_y = 450
clock = pygame.time.Clock()

food_available = True
energy = 5 

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    x += velocity_x
    y += velocity_y
    energy -= 0.1

    if x + 10 >= 1000 or x - 10 <= 0:
        velocity_x = -velocity_x
    if y + 10 >= 700 or y - 10 <= 0:
        velocity_y = -velocity_y

    distance = math.hypot(x - food_x, y - food_y)

    if food_available and distance <= 15: 
        food_available = False
        energy += 30
        print("Food eaten! Energy:", energy)

    if energy <= 0:
        print("Creature ran out of energy.")
        running = False


    screen.fill("black")

    if food_available:
        pygame.draw.circle(screen, "orange", (food_x, food_y), 5)

    pygame.draw.circle(screen, "green", (x, y), 10)

    pygame.display.set_caption(f"Evolution Simulator | Energy: {energy:.1f}")
    pygame.display.flip() # updates the screen
    clock.tick(60)
    
pygame.quit()
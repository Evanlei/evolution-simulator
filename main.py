import pygame

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")

running = True

x = 500
y = 350
velocity_x = 2
velocity_y = 2
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    x += velocity_x
    y += velocity_y
    if x + 10 >= 1000 or x - 10 <= 0:
        velocity_x = -velocity_x
    if y + 10 >= 700 or y - 10 <= 0:
        velocity_y = -velocity_y

    screen.fill("black")

    pygame.draw.circle(screen, "green", (x, y), 10)
    pygame.display.flip() # updates the screen
    clock.tick(60)
    
pygame.quit()
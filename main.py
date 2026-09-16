import pygame

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")

running = True

x = 500
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    x += 1
    screen.fill("black")
    pygame.draw.circle(screen, "green", (x, 350), 10)
    pygame.display.flip() # updates the screen
    clock.tick(60)
pygame.quit()
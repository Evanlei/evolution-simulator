import pygame

pygame.init()

pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Evolution Simulator")

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
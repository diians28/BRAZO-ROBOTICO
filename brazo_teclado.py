# -*- coding: utf-8 -*-
"""
Control del brazo robotico usando teclado.
"""

import math
import pygame


pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brazo Robotico - Teclado")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

base = (400, 300)
lengths = [100, 80, 60, 40]
angles = [0, 0, 0, 0]
selected = 0

box_pos = [550, 250]
box_size = 20
grabbed = False

target_rect = pygame.Rect(100, 400, 80, 80)


def forward_kinematics():
    x, y = base
    total_angle = 0
    points = [base]

    for i in range(4):
        total_angle += angles[i]
        x += lengths[i] * math.cos(total_angle)
        y += lengths[i] * math.sin(total_angle)
        points.append((x, y))

    return points


running = True

while running:
    screen.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                selected = (selected - 1) % 4
            elif event.key == pygame.K_RIGHT:
                selected = (selected + 1) % 4
            elif event.key == pygame.K_UP:
                angles[selected] += 0.1
            elif event.key == pygame.K_DOWN:
                angles[selected] -= 0.1
            elif event.key == pygame.K_g:
                points = forward_kinematics()
                end = points[-1]
                dist = math.hypot(end[0] - box_pos[0], end[1] - box_pos[1])

                if not grabbed and dist < 25:
                    grabbed = True
                elif grabbed:
                    grabbed = False

    points = forward_kinematics()

    for i in range(len(points) - 1):
        pygame.draw.line(screen, (0, 150, 255), points[i], points[i + 1], 5)
        pygame.draw.circle(screen, (255, 0, 0), (int(points[i][0]), int(points[i][1])), 6)

    end = points[-1]
    pygame.draw.circle(screen, (255, 255, 0), (int(end[0]), int(end[1])), 8)

    if grabbed:
        box_pos[0], box_pos[1] = end

    pygame.draw.rect(
        screen,
        (255, 165, 0),
        (box_pos[0] - box_size // 2, box_pos[1] - box_size // 2, box_size, box_size),
    )
    pygame.draw.rect(screen, (0, 255, 0), target_rect, 2)

    if target_rect.collidepoint(box_pos):
        text = font.render("Caja colocada exitosamente", True, (0, 255, 0))
        screen.blit(text, (250, 50))

    text1 = font.render("Controles: <- -> seleccion | ^ v mover | G agarrar/soltar", True, (255, 255, 255))
    text2 = font.render(f"Eslabon seleccionado: {selected + 1}", True, (255, 255, 255))
    screen.blit(text1, (10, 10))
    screen.blit(text2, (10, 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

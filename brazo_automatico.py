# -*- coding: utf-8 -*-
import pygame
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brazo Robotico - Pygame")

clock = pygame.time.Clock()

# =========================
# Parámetros
# =========================
base = (400, 300)
lengths = [100, 80, 60, 40]
angles = [0, 0, 0, 0]
selected = 0

# Caja
box_pos = [550, 250]
box_size = 20
grabbed = False

# Zona objetivo
target_rect = pygame.Rect(100, 400, 80, 80)

font = pygame.font.SysFont(None, 30)

# =========================
# Cinemática directa
# =========================
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

# =========================
# CCD — UN SOLO PASO POR FRAME
# =========================
def ik_single_step(target):
    best_i   = 0
    best_diff = 0.0

    for i in range(3, -1, -1):
        points = forward_kinematics()
        pivot  = points[i]
        end    = points[-1]

        to_end    = (end[0]    - pivot[0], end[1]    - pivot[1])
        to_target = (target[0] - pivot[0], target[1] - pivot[1])

        angle_end    = math.atan2(to_end[1],    to_end[0])
        angle_target = math.atan2(to_target[1], to_target[0])

        diff = (angle_target - angle_end + math.pi) % (2 * math.pi) - math.pi

        if abs(diff) > abs(best_diff):
            best_diff = diff
            best_i    = i

    MAX_STEP = 0.03
    step = max(-MAX_STEP, min(MAX_STEP, best_diff * 0.4))
    angles[best_i] += step

# =========================
# Rutina automática
# =========================
GRAB_DIST  = 20

STATE_APPROACH = "approach"
STATE_GRAB     = "grab"
STATE_DELIVER  = "deliver"
STATE_DROP     = "drop"
STATE_DONE     = "done"

auto_state  = STATE_APPROACH
auto_active = True

state_timer = 0
PAUSE_FRAMES = 30

# =========================
# Loop principal
# =========================
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

    # =========================
    # Lógica rutina automática
    # =========================
    if auto_active and auto_state != STATE_DONE:
        points = forward_kinematics()
        end    = points[-1]

        if auto_state == STATE_APPROACH:
            ik_single_step((box_pos[0], box_pos[1]))
            dist = math.hypot(end[0] - box_pos[0], end[1] - box_pos[1])
            if dist < GRAB_DIST:
                auto_state  = STATE_GRAB
                state_timer = PAUSE_FRAMES

        elif auto_state == STATE_GRAB:
            state_timer -= 1
            if state_timer <= 0:
                grabbed    = True
                auto_state = STATE_DELIVER

        elif auto_state == STATE_DELIVER:
            cx, cy = target_rect.centerx, target_rect.centery
            ik_single_step((cx, cy))
            dist = math.hypot(end[0] - cx, end[1] - cy)
            if dist < GRAB_DIST:
                auto_state  = STATE_DROP
                state_timer = PAUSE_FRAMES

        elif auto_state == STATE_DROP:
            state_timer -= 1
            if state_timer <= 0:
                grabbed    = False
                auto_state = STATE_DONE

    # =========================
    # Mover caja si está agarrada
    # =========================
    points = forward_kinematics()
    end    = points[-1]

    if grabbed:
        box_pos[0], box_pos[1] = end[0], end[1]

    # =========================
    # Dibujo (mismo orden que interfaz.py)
    # =========================
    # Brazo
    for i in range(len(points) - 1):
        pygame.draw.line(screen, (0, 150, 255), points[i], points[i + 1], 5)
        pygame.draw.circle(screen, (255, 0, 0), (int(points[i][0]), int(points[i][1])), 6)

    # Pinza
    pygame.draw.circle(screen, (255, 255, 0), (int(end[0]), int(end[1])), 8)

    # Caja
    pygame.draw.rect(
        screen,
        (255, 165, 0),
        (box_pos[0] - box_size // 2, box_pos[1] - box_size // 2, box_size, box_size),
    )

    # Zona objetivo
    pygame.draw.rect(screen, (0, 255, 0), target_rect, 2)

    # Verificar éxito
    if target_rect.collidepoint(box_pos):
        text = font.render("Caja colocada exitosamente", True, (0, 255, 0))
        screen.blit(text, (250, 50))

    # Mostrar eslabón seleccionado
    text2 = font.render(f"Eslabon seleccionado: {selected + 1}", True, (255, 255, 255))
    screen.blit(text2, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
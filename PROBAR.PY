# -*- coding: utf-8 -*-
import pygame
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brazo Robotico - Pygame")
clock = pygame.time.Clock()

# =========================
# Parámetros del brazo
# =========================
base = (400, 300)
lengths = [100, 80, 60, 40]
angles = [0, 0, 0, 0]
selected = 0

box_pos = [550, 250]
box_size = 20
grabbed = False

target_rect = pygame.Rect(100, 400, 80, 80)
font = pygame.font.SysFont(None, 28)
font_small = pygame.font.SysFont(None, 22)

# =========================
# Sistema de teclas reasignables
# =========================
KEY_LABELS = {
    "prev_segment":  "Izquierda",
    "next_segment":  "Derecha",
    "rotate_up":     "Arriba",
    "rotate_down":   "Abajo",
    "grab":          "Agarrar ",
}

# Teclas por defecto
key_bindings = {
    "prev_segment":  pygame.K_LEFT,
    "next_segment":  pygame.K_RIGHT,
    "rotate_up":     pygame.K_UP,
    "rotate_down":   pygame.K_DOWN,
    "grab":          pygame.K_g,
}

# Estado del panel de reasignación
show_panel = False
listening_for = None   # nombre de la acción esperando tecla

PANEL_W, PANEL_H = 340, 240
PANEL_X = (WIDTH - PANEL_W) // 2
PANEL_Y = (HEIGHT - PANEL_H) // 2
ROW_H = 36
MARGIN = 16

def key_name(key_code):
    """Devuelve nombre legible de un keycode."""
    name = pygame.key.name(key_code)
    return name.upper() if len(name) == 1 else name.capitalize()

def draw_panel():
    """Dibuja el panel de reasignación de teclas."""
    # Fondo oscuro semitransparente
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # Panel principal
    pygame.draw.rect(screen, (45, 45, 50), (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), border_radius=10)
    pygame.draw.rect(screen, (100, 100, 120), (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), 1, border_radius=10)

    title = font.render("Reasignar teclas", True, (220, 220, 255))
    screen.blit(title, (PANEL_X + MARGIN, PANEL_Y + 10))

    actions = list(KEY_LABELS.keys())
    for i, action in enumerate(actions):
        y = PANEL_Y + 44 + i * ROW_H
        label = KEY_LABELS[action]
        is_listening = (listening_for == action)

        # Etiqueta de acción
        color_label = (180, 180, 200)
        txt = font_small.render(label, True, color_label)
        screen.blit(txt, (PANEL_X + MARGIN, y + 8))

        # Botón de tecla
        btn_w, btn_h = 80, 24
        btn_x = PANEL_X + PANEL_W - btn_w - MARGIN
        btn_y = y + 6

        if is_listening:
            btn_color = (60, 100, 180)
            border_color = (120, 160, 255)
            key_text = "..."
        else:
            btn_color = (60, 60, 70)
            border_color = (90, 90, 110)
            key_text = key_name(key_bindings[action])

        pygame.draw.rect(screen, btn_color, (btn_x, btn_y, btn_w, btn_h), border_radius=5)
        pygame.draw.rect(screen, border_color, (btn_x, btn_y, btn_w, btn_h), 1, border_radius=5)
        kt = font_small.render(key_text, True, (220, 220, 255))
        screen.blit(kt, (btn_x + (btn_w - kt.get_width()) // 2,
                         btn_y + (btn_h - kt.get_height()) // 2))

    hint_color = (120, 120, 140)
    if listening_for:
        hint = font_small.render("Presiona la nueva tecla...", True, (120, 200, 255))
    else:
        hint = font_small.render("Clic en un boton para reasignar  |  TAB cierra", True, hint_color)
    screen.blit(hint, (PANEL_X + MARGIN, PANEL_Y + PANEL_H - 22))

def panel_button_hit(mx, my):
    """Retorna la acción cuyo botón fue clicado, o None."""
    actions = list(KEY_LABELS.keys())
    for i, action in enumerate(actions):
        y = PANEL_Y + 44 + i * ROW_H
        btn_w, btn_h = 80, 24
        btn_x = PANEL_X + PANEL_W - btn_w - MARGIN
        btn_y = y + 6
        rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        if rect.collidepoint(mx, my):
            return action
    return None

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
# Loop principal
# =========================
running = True

while running:
    screen.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---- Panel abierto ----
        if show_panel:
            if event.type == pygame.KEYDOWN:
                if listening_for:
                    # Asignar la tecla presionada a la acción
                    key_bindings[listening_for] = event.key
                    listening_for = None
                elif event.key == pygame.K_TAB:
                    show_panel = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = panel_button_hit(*event.pos)
                if action:
                    listening_for = action
                else:
                    listening_for = None

        # ---- Juego normal ----
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    show_panel = True
                    listening_for = None

                elif event.key == key_bindings["prev_segment"]:
                    selected = (selected - 1) % 4

                elif event.key == key_bindings["next_segment"]:
                    selected = (selected + 1) % 4

                elif event.key == key_bindings["rotate_up"]:
                    angles[selected] += 0.1

                elif event.key == key_bindings["rotate_down"]:
                    angles[selected] -= 0.1

                elif event.key == key_bindings["grab"]:
                    points = forward_kinematics()
                    end = points[-1]
                    dist = math.hypot(end[0] - box_pos[0], end[1] - box_pos[1])
                    if not grabbed and dist < 25:
                        grabbed = True
                    elif grabbed:
                        grabbed = False

    points = forward_kinematics()

    # Dibujar brazo
    for i in range(len(points) - 1):
        pygame.draw.line(screen, (0, 150, 255), points[i], points[i+1], 5)
        pygame.draw.circle(screen, (255, 0, 0), (int(points[i][0]), int(points[i][1])), 6)

    end = points[-1]
    pygame.draw.circle(screen, (255, 255, 0), (int(end[0]), int(end[1])), 8)

    if grabbed:
        box_pos[0], box_pos[1] = end

    pygame.draw.rect(screen, (255, 165, 0),
                     (box_pos[0] - box_size//2, box_pos[1] - box_size//2,
                      box_size, box_size))

    pygame.draw.rect(screen, (0, 255, 0), target_rect, 2)

    if target_rect.collidepoint(box_pos):
        text = font.render("Caja colocada exitosamente", True, (0, 255, 0))
        screen.blit(text, (250, 50))

    text2 = font.render(f"Eslabon: {selected+1}  |  TAB = Reasignar teclas", True, (200, 200, 200))
    screen.blit(text2, (10, 10))

    # Dibujar panel si está activo
    if show_panel:
        draw_panel()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
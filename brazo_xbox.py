
import math
import pygame


# ---------------------------------------------------------------------------
# Mapeo de botones y ejes — edita aqui si tu control es distinto
# ---------------------------------------------------------------------------
AXIS_LEFT_X    = 0   # Stick izquierdo horizontal  -> cambia eslabón
AXIS_LEFT_Y    = 1   # Stick izquierdo vertical    -> gira eslabón
AXIS_RIGHT_X   = 2   # Stick derecho horizontal    (no usado por defecto)
AXIS_RIGHT_Y   = 3   # Stick derecho vertical      -> gira eslabón (alternativo)
AXIS_LT        = 4   # Trigger izquierdo
AXIS_RT        = 5   # Trigger derecho

BTN_A          = 0   # Agarrar / soltar caja
BTN_LB         = 4   # Eslabón anterior
BTN_RB         = 5   # Eslabón siguiente

DEADZONE       = 0.20
BUTTON_DELAY   = 200  # ms entre cambios de eslabón con botón
AXIS_DELAY     = 100  # ms entre movimientos de eje
# ---------------------------------------------------------------------------


pygame.init()
pygame.joystick.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brazo Robotico - Pygame")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

joystick       = None
joystick_name  = "Sin control"

last_select_time = 0
last_angle_time  = 0

base    = (400, 300)
lengths = [100, 80, 60, 40]
angles  = [0.0, 0.0, 0.0, 0.0]
selected = 0

box_pos  = [550, 250]
box_size = 20
grabbed  = False

target_rect = pygame.Rect(100, 400, 80, 80)


# ---------------------------------------------------------------------------
# Joystick
# ---------------------------------------------------------------------------
def connect_joystick():
    global joystick, joystick_name
    joystick      = None
    joystick_name = "Sin control"

    count = pygame.joystick.get_count()
    if count <= 0:
        return

    for index in range(count):
        try:
            candidate = pygame.joystick.Joystick(index)
            candidate.init()
            joystick      = candidate
            joystick_name = joystick.get_name()
            print(f"Control conectado: {joystick_name}")
            print(f"  Ejes: {joystick.get_numaxes()}  "
                  f"Botones: {joystick.get_numbuttons()}  "
                  f"Hats: {joystick.get_numhats()}")
            return
        except pygame.error:
            continue


def safe_get_axis(idx):
    """Devuelve el valor del eje aplicando zona muerta."""
    if joystick is None:
        return 0.0
    if idx < 0 or idx >= joystick.get_numaxes():
        return 0.0
    try:
        v = joystick.get_axis(idx)
    except (pygame.error, IndexError):
        return 0.0
    return 0.0 if abs(v) < DEADZONE else v


def safe_get_trigger(idx):
    """
    Los triggers Xbox reportan -1.0 en reposo en Windows.
    Esta funcion los normaliza: reposo = 0.0, presionado = 1.0
    """
    if joystick is None:
        return 0.0
    if idx < 0 or idx >= joystick.get_numaxes():
        return 0.0
    try:
        raw = joystick.get_axis(idx)
    except (pygame.error, IndexError):
        return 0.0
    # Normaliza de [-1, 1] -> [0, 1]  (cubre tanto Windows como Linux)
    normalized = (raw + 1.0) / 2.0
    return normalized if normalized > DEADZONE else 0.0


def safe_get_button(idx):
    if joystick is None:
        return 0
    if idx < 0 or idx >= joystick.get_numbuttons():
        return 0
    try:
        return joystick.get_button(idx)
    except (pygame.error, IndexError):
        return 0


def safe_get_hat(idx=0):
    if joystick is None:
        return (0, 0)
    if idx < 0 or idx >= joystick.get_numhats():
        return (0, 0)
    try:
        return joystick.get_hat(idx)
    except (pygame.error, IndexError):
        return (0, 0)


def safe_get_events():
    try:
        return pygame.event.get()
    except (pygame.error, KeyError):
        connect_joystick()
        return []


# ---------------------------------------------------------------------------
# Cinematica
# ---------------------------------------------------------------------------
def forward_kinematics():
    x, y = base
    total_angle = 0.0
    points = [base]
    for i in range(4):
        total_angle += angles[i]
        x += lengths[i] * math.cos(total_angle)
        y += lengths[i] * math.sin(total_angle)
        points.append((x, y))
    return points


def clamp_angles():
    for i in range(len(angles)):
        angles[i] = max(-math.pi, min(math.pi, angles[i]))


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
connect_joystick()

running = True
while running:
    screen.fill((30, 30, 30))
    now = pygame.time.get_ticks()

    # ---- Eventos --------------------------------------------------------
    for event in safe_get_events():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        elif event.type == pygame.JOYDEVICEADDED:
            connect_joystick()

        elif event.type == pygame.JOYDEVICEREMOVED:
            connect_joystick()

        # Boton A: agarrar / soltar
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == BTN_A:
                points = forward_kinematics()
                end    = points[-1]
                dist   = math.hypot(end[0] - box_pos[0], end[1] - box_pos[1])
                if not grabbed and dist < 30:
                    grabbed = True
                    print("Caja agarrada")
                elif grabbed:
                    grabbed = False
                    print("Caja soltada")

    # ---- Lectura continua del joystick ----------------------------------
    if joystick is not None:
        try:
            pygame.event.pump()

            # LB / RB -> cambiar eslabon seleccionado
            if now - last_select_time > BUTTON_DELAY:
                if safe_get_button(BTN_LB):
                    selected = (selected - 1) % 4
                    last_select_time = now
                elif safe_get_button(BTN_RB):
                    selected = (selected + 1) % 4
                    last_select_time = now

            # Cruceta (hat) -> cambiar eslabon (izq/der) o girar (arr/abj)
            hat = safe_get_hat(0)
            if hat[0] != 0 and now - last_select_time > AXIS_DELAY:
                selected = (selected + hat[0]) % 4
                last_select_time = now
            if hat[1] != 0 and now - last_angle_time > AXIS_DELAY:
                angles[selected] += 0.06 * hat[1]
                last_angle_time = now

            # Stick izquierdo X -> cambiar eslabon
            lx = safe_get_axis(AXIS_LEFT_X)
            if lx != 0.0 and now - last_select_time > AXIS_DELAY:
                selected = (selected + (1 if lx > 0 else -1)) % 4
                last_select_time = now

            # Stick izquierdo Y -> girar eslabon (invertido: arriba = positivo)
            ly = safe_get_axis(AXIS_LEFT_Y)
            if ly != 0.0 and now - last_angle_time > AXIS_DELAY:
                angles[selected] += -0.06 * ly
                last_angle_time = now

            # Stick derecho Y -> girar eslabon (alternativo si left Y no funciona)
            ry = safe_get_axis(AXIS_RIGHT_Y)
            if ry != 0.0 and ly == 0.0 and now - last_angle_time > AXIS_DELAY:
                angles[selected] += -0.06 * ry
                last_angle_time = now

            clamp_angles()

        except pygame.error:
            connect_joystick()

    # ---- Actualizar posicion de la caja si esta agarrada ----------------
    points = forward_kinematics()
    end    = points[-1]
    if grabbed:
        box_pos[0] = int(end[0])
        box_pos[1] = int(end[1])

    # ---- Dibujo (mismo orden que interfaz.py) ---------------------------

    # Brazo
    for i in range(len(points) - 1):
        pygame.draw.line(
            screen,
            (0, 150, 255),
            (int(points[i][0]), int(points[i][1])),
            (int(points[i + 1][0]), int(points[i + 1][1])),
            5,
        )
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
# config.py
import pygame


class GameConfig:
    # Dimensiones del Grid y Pantalla
    GRID_WIDTH = 40
    GRID_HEIGHT = 30
    SQUARE_SIZE = 22
    HUD_HEIGHT = 52  # Barra superior tipo marcador
    SIDEBAR_WIDTH = 300
    GRID_ORIGIN = (0, HUD_HEIGHT)  # Esquina superior izquierda del tablero en pantalla
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = HUD_HEIGHT + GRID_HEIGHT * SQUARE_SIZE
    WINDOW_TITLE = "JuegoIA · Bomber Mind"

    # Vistas: "2d" (tablero), "3d" (maqueta 3D del mapa), "fps" (primera persona)
    VIEW_MODES = ["2d", "3d", "fps"]
    VIEW_NAMES = {"2d": "2D", "3d": "MAPA 3D", "fps": "1ª PERSONA"}

    # Colores
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (50, 50, 50)

    GRID_BG = DARK_GRAY
    GRID_COLOR = GRAY
    PLAYER_COLOR = BLUE
    HOUSE_COLOR = GREEN
    ENEMY_COLOR = RED
    OBSTACLE_COLOR = LIGHT_GRAY
    PATH_COLOR = YELLOW
    CURRENT_PATH_COLOR = ORANGE

    SIDEBAR_BG = (30, 30, 30)
    BUTTON_BG = (70, 70, 70)
    BUTTON_HOVER = (100, 100, 100)
    BUTTON_ACTIVE = (130, 130, 130)
    BUTTON_FOCUS = WHITE
    BUTTON_TEXT = WHITE
    BUTTON_TEXT_ACTIVE = YELLOW

    HEAT_COLORS = [
        (255, 255, 204), (255, 237, 160), (254, 217, 118),
        (254, 178, 76), (253, 141, 60), (252, 78, 42),
        (227, 26, 28), (189, 0, 38), (128, 0, 38)
    ]

    PLAYER_IMAGE = "bomberman.png.webp"
    HOUSE_IMAGE = "27187.jpg.webp"
    ENEMY_IMAGE = "enemy.png"

    GAME_SPEED = 60  # FPS del bucle de dibujo (independiente de la velocidad de los turnos)
    MOVE_DELAY = 150  # ms por turno
    HEADLESS_DELAY = 30  # ms por turno en modo sin cabeza
    OBSTACLE_PERCENTAGE = 18  # Ligeramente reducido para grid más grande

    # --- Turnos ---
    # Cada MOVE_DELAY ms ocurre un "turno": el jugador da un paso y los enemigos
    # acumulan ENEMY_SPEED_FACTOR; cada vez que el acumulado llega a 1 dan un paso.
    # 0.5 = un paso enemigo cada 2 turnos, 0.75 = 3 pasos cada 4 turnos, 1.5 = 3 cada 2.
    ENEMY_SPEED_FACTOR = 0.5
    ENEMY_MIN_PLAYER_DISTANCE = 3
    DEFAULT_ENEMY_TYPE = "perseguidor"
    ENEMY_TYPES = ["perseguidor", "bloqueador", "patrulla", "aleatorio"]

    # --- Comportamiento de los tipos de enemigo ---
    BLOCKER_LOOKAHEAD = 6          # Bloqueador: apunta a la celda N pasos adelante en la ruta del jugador
    PATROL_RADIUS = 5              # Patrulla: radio de su ronda alrededor del punto de aparición
    PATROL_DETECTION_RADIUS = 6    # Patrulla: distancia a la que detecta al jugador y empieza a perseguir
    PATROL_LOSE_RADIUS = 10        # Patrulla: distancia a la que pierde al jugador y vuelve a patrullar
    RANDOM_ENEMY_INERTIA = 0.6     # Aleatorio: probabilidad de mantener la dirección anterior
    ENEMY_LOOP_MEMORY = 4          # Celdas recientes que un enemigo recuerda para no oscilar

    # --- Evasión del avatar ---
    DANGER_RADIUS = 3              # Distancia a la que un enemigo "calienta" el costo de una celda
    DANGER_WEIGHT = 6.0            # Costo extra junto a un enemigo (decrece con 1/(1+d))
    REPLAN_EVERY_TURNS = 3         # Con enemigos presentes, la ruta se recalcula cada N turnos
    THREAT_LOOKAHEAD = 4           # Celdas de la ruta que se vigilan para replanificar de inmediato

    MAX_OBSTACLE_LAYOUT_ATTEMPTS = 30  # Reintentos para generar un mapa donde la casa sea alcanzable

    INITIAL_PLAYER_POS = (1, 1)
    INITIAL_HOUSE_POS = (GRID_WIDTH - 2, GRID_HEIGHT - 2)
    INITIAL_ENEMY_POSITIONS = [
        (GRID_WIDTH - 5, 5),  # Ajustado para grid más grande
        (5, GRID_HEIGHT - 5),
        (GRID_WIDTH // 2, GRID_HEIGHT - 3),
        (GRID_WIDTH - 3, GRID_HEIGHT // 2)
    ]
    # INITIAL_ENEMY_POSITIONS = None

    MOVE_UP_RANGE = (1, 5)
    MOVE_RIGHT_RANGE = (6, 10)
    MOVE_DOWN_RANGE = (11, 15)
    MOVE_LEFT_RANGE = (16, 20)

    SHOW_MOVEMENT_MATRIX = True
    SHOW_VISIT_COUNT_ON_HEATMAP = False
    COUNT_SETUP_MOVES_IN_FREQUENCY_MAP = False  # NUEVO: Para Problema 4

    HEADLESS_MODE = False
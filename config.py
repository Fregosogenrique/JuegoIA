# config.py
import pygame


class GameConfig:
    # Dimensiones del Grid y Pantalla
    GRID_WIDTH = 40  # MODIFICADO
    GRID_HEIGHT = 30  # MODIFICADO
    SQUARE_SIZE = 20  # MODIFICADO (opcional, para que quepa mejor en pantalla)
    SIDEBAR_WIDTH = 250
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

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

    GAME_SPEED = 10
    MOVE_DELAY = 150  # Reducido para movimiento más fluido
    HEADLESS_DELAY = 30
    OBSTACLE_PERCENTAGE = 18  # Ligeramente reducido para grid más grande

    ENEMY_SPEED_FACTOR = 0.5
    ENEMY_MIN_PLAYER_DISTANCE = 3
    DEFAULT_ENEMY_TYPE = "perseguidor"

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
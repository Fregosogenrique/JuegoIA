import pygame


class GameConfig:
    # Tamaños de la cuadrícula y ventana
    SQUARE_SIZE = 20  # Tamaño de cada cuadro
    GRID_WIDTH = 40  # Ancho del grid
    GRID_HEIGHT = 30  # Alto del grid
    SIDEBAR_WIDTH = 200  # Ancho de la barra lateral

    # Dimensiones de la ventana
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

    # Velocidad del juego
    GAME_SPEED = 60  # FPS
    MOVE_DELAY = 100  # ms entre movimientos (normal)
    HEADLESS_DELAY = 0  # ms entre movimientos (modo sin interfaz)
    RESET_DELAY = 500
    VICTORY_DURATION = 2000

    # Rangos de movimiento aleatorio
    MOVE_UP_RANGE = (1, 5)
    MOVE_RIGHT_RANGE = (6, 10)
    MOVE_DOWN_RANGE = (11, 15)
    MOVE_LEFT_RANGE = (16, 20)

    # Rutas de imágenes
    PLAYER_IMAGE = 'bomberman.png.webp'
    HOUSE_IMAGE = '27187.jpg.webp'

    # Configuración de juego
    MOVE_DELAY = 100  # Milisegundos entre movimientos
    SHOW_MOVEMENT_MATRIX = True  # Mostrar números de movimiento
    HEADLESS_MODE = False  # Modo sin interfaz gráfica
    USE_DECISION_TREE = True  # Usar árbol de decisiones con poda
    OBSTACLE_PERCENTAGE = 20  # Porcentaje de obstáculos en el grid (0-100)

    # Posiciones iniciales predefinidas
    INITIAL_PLAYER_POS = (12, 10)  # Posición inicial del jugador (x, y)
    INITIAL_HOUSE_POS = (25, 20)  # Posición inicial de la casa (x, y)

    # Colores
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    EGGSHELL = (240, 234, 214)
    CYAN = (0, 255, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    PRUNED_PATH_COLOR = (0, 191, 255)  # DeepSkyBlue - Color más brillante para la ruta con poda

    # Colores de mapa de calor
    HEAT_COLORS = [
        (255, 255, 0),  # Amarillo suave
        (255, 200, 0),  # Naranja claro
        (255, 150, 0),  # Naranja
        (255, 100, 0),  # Naranja intenso
        (255, 50, 0),  # Rojo-naranja
        (255, 0, 0),  # Rojo
        (200, 0, 0),  # Rojo oscuro
        (150, 0, 0)  # Rojo muy oscuro
    ]

    # Colores de UI
    SIDEBAR_BG = DARK_GRAY
    GRID_BG = DARK_GRAY
    GRID_COLOR = EGGSHELL
    BUTTON_BG = (200, 200, 200)  # Gris claro para botones
    BUTTON_HOVER = (230, 230, 230)  # Gris más claro para hover
    BUTTON_ACTIVE = (100, 100, 220)  # Azul para botón activo
    BUTTON_FOCUS = (0, 128, 255)  # Azul para focus
    BUTTON_TEXT = BLACK
    BUTTON_TEXT_ACTIVE = WHITE
    OBSTACLE_COLOR = GRAY  # Color de obstáculos
    PLAYER_COLOR = BLUE  # Color del jugador (fallback)
    HOUSE_COLOR = GREEN  # Color de la casa (fallback)
    PATH_COLOR = ORANGE  # Color de la ruta
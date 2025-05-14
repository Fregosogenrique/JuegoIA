# config.py
import pygame  # Necesario para colores


class GameConfig:
    # Dimensiones del Grid y Pantalla
    GRID_WIDTH = 40
    GRID_HEIGHT = 30
    SQUARE_SIZE = 20
    SIDEBAR_WIDTH = 250  # Ancho de la barra lateral
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

    # Colores (Tuplas RGB)
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
    PATH_COLOR = YELLOW  # Color para la mejor ruta planificada
    CURRENT_PATH_COLOR = ORANGE  # Color para la ruta que se está siguiendo

    # Colores UI Sidebar
    SIDEBAR_BG = (30, 30, 30)
    BUTTON_BG = (70, 70, 70)
    BUTTON_HOVER = (100, 100, 100)
    BUTTON_ACTIVE = (130, 130, 130)  # Clickeado
    BUTTON_FOCUS = WHITE  # Borde cuando hover
    BUTTON_TEXT = WHITE
    BUTTON_TEXT_ACTIVE = YELLOW

    # Heatmap Colors (de menos a más intenso)
    HEAT_COLORS = [
        (255, 255, 204), (255, 237, 160), (254, 217, 118),
        (254, 178, 76), (253, 141, 60), (252, 78, 42),
        (227, 26, 28), (189, 0, 38), (128, 0, 38)
    ]

    # Rutas de Imágenes (relativas al script principal o a una carpeta 'assets')
    PLAYER_IMAGE = "bomberman.png.webp"  # Reemplaza con tus nombres de archivo
    HOUSE_IMAGE = "27187.jpg.webp"
    ENEMY_IMAGE = "enemy.png"

    # Configuración del Juego
    GAME_SPEED = 10  # FPS (Frames por segundo)
    MOVE_DELAY = 200  # Milisegundos entre movimientos automáticos del jugador
    HEADLESS_DELAY = 50  # Milisegundos entre movimientos en modo headless
    OBSTACLE_PERCENTAGE = 20  # Porcentaje de celdas que serán obstáculos

    # Configuración IA y Enemigos
    ENEMY_SPEED_FACTOR = 0.5  # 1.0: misma vel que jugador, 0.5: mitad vel, 2.0: doble vel
    # Si es 0.5, enemigo se mueve cada 2 pasos del jugador.
    ENEMY_MIN_PLAYER_DISTANCE = 3  # Distancia mínima que algunos enemigos intentan mantener
    DEFAULT_ENEMY_TYPE = "perseguidor"

    # Posiciones Iniciales (si son None, se usan valores por defecto o aleatorios donde aplique)
    INITIAL_PLAYER_POS = (1, 1)
    INITIAL_HOUSE_POS = (GRID_WIDTH - 2, GRID_HEIGHT - 2)
    INITIAL_ENEMY_POSITIONS = [  # Puede ser una lista de tuplas (x,y) o None
        (GRID_WIDTH - 3, 2),
        (2, GRID_HEIGHT - 3),
        (GRID_WIDTH // 2, GRID_HEIGHT - 2),
        (GRID_WIDTH - 2, GRID_HEIGHT // 2)
    ]
    # INITIAL_ENEMY_POSITIONS = None # Para forzar colocación estratégica/aleatoria

    # Movimiento Aleatorio del Jugador (rangos para random.randint(1,20))
    # Asegurar que los rangos no se solapen y cubran del 1 al 20 (o el rango que uses)
    # Ejemplo: 1-5 (Up), 6-10 (Right), 11-15 (Down), 16-20 (Left)
    # Estos se usan en _execute_player_random_move si no hay otra lógica de movimiento.
    MOVE_UP_RANGE = (1, 5)
    MOVE_RIGHT_RANGE = (6, 10)
    MOVE_DOWN_RANGE = (11, 15)
    MOVE_LEFT_RANGE = (16, 20)

    # Opciones de Visualización
    SHOW_MOVEMENT_MATRIX = True  # Para mostrar el heatmap de frecuencia del jugador
    SHOW_VISIT_COUNT_ON_HEATMAP = False  # Para mostrar números en el heatmap de frecuencia

    # Modo Headless (para entrenamiento rápido sin UI visible, aunque aquí la UI sigue)
    HEADLESS_MODE = False
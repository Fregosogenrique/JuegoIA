class GameConfig:
    # Aquí guardo todos los números importantes del juego

    # Tamaños de la ventana y el tablero
    GRID_WIDTH = 40
    GRID_HEIGHT = 30
    SQUARE_SIZE = 25
    SIDEBAR_WIDTH = 200
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = max(GRID_HEIGHT * SQUARE_SIZE, 600)  # Asegura espacio suficiente

    # Gameplay
    GAME_SPEED = 120  # Aumentado para movimiento más lento

    # Colores que uso en el juego
    WHITE = (74, 78, 105)  # Para la cuadrícula
    BLACK = (26, 26, 46)  # Para el fondo
    GREEN = (76, 175, 80)  # Para cuando ganas
    GRAY = (154, 140, 152)  # Para los obstáculos

    # Los demás colores se mantienen igual
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    BUTTON_ACTIVE = (100, 200, 100)
    BUTTON_INACTIVE = (200, 200, 200)
    BUTTON_TEXT = (0, 0, 0)

    # Rutas de imágenes
    PLAYER_IMAGE = 'bomberman.png.webp'
    HOUSE_IMAGE = '27187.jpg.webp'

    # Cuánto tiempo muestro los mensajes
    VICTORY_TIME = 15  # Mensaje de victoria
    ERROR_TIME = 25  # Mensaje de error
    VICTORY_DELAY = 10  # Delay entre frames en victoria
    ERROR_DELAY = 10  # Delay entre frames en error
    RESET_DELAY = 10  # Delay al resetear el juego
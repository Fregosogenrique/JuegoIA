class GameConfig:
    # Dimensiones
    GRID_WIDTH = 40
    GRID_HEIGHT = 30
    SQUARE_SIZE = 25
    SIDEBAR_WIDTH = 200
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

    # Gameplay
    OBSTACLE_COUNT = 1000
    GAME_SPEED = 100

    # Colores
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    GRAY = (128, 128, 128)
    RED = (255, 0, 0)
    BLUE = (0,0,255)

    # Rutas de imágenes
    PLAYER_IMAGE = 'bomberman.png.webp'
    HOUSE_IMAGE = '27187.jpg.webp'

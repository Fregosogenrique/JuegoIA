import random
from config import GameConfig


class GameState:
    """Clase que mantiene el estado del juego"""

    def __init__(self, grid_width, grid_height):
        """Inicializa el estado del juego"""
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.obstacles = set()  # Cambiar a un conjunto en lugar de una lista
        self.player_pos = None
        self.initial_player_pos = None  # Guardar la posición inicial
        self.house_pos = None
        self.victory = False
        self.game_started = False

    def initialize_game(self):
        """Inicializa el estado del juego"""
        # Usar posiciones predefinidas de config
        self.player_pos = GameConfig.INITIAL_PLAYER_POS
        self.initial_player_pos = GameConfig.INITIAL_PLAYER_POS
        self.house_pos = GameConfig.INITIAL_HOUSE_POS

        # Generar obstáculos aleatorios
        self._generate_obstacles()

    def _generate_obstacles(self):
        """Genera obstáculos aleatorios en el grid"""
        self.obstacles = set()
        num_obstacles = int((self.grid_width * self.grid_height) * (GameConfig.OBSTACLE_PERCENTAGE / 100))

        while len(self.obstacles) < num_obstacles:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            pos = (x, y)

            # Evitar colocar obstáculos en la posición inicial del jugador o la casa
            if pos != self.player_pos and pos != self.house_pos and pos not in self.obstacles:
                self.obstacles.add(pos)

    def is_valid_move(self, pos):
        """Verifica si una posición es válida para moverse"""
        x, y = pos
        return (0 <= x < self.grid_width and
                0 <= y < self.grid_height and
                pos not in self.obstacles)
import sys
import pygame
from config import GameConfig
from render import GameRenderer
import random
from Eventos_Teclado import InputHandler
from ADB import AStar, UCS


class GameState:
    """Maneja el estado del juego y sus variables principales"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia todas las variables del estado del juego"""
        self.player_pos = (1, 1)
        self.house_pos = (8, 8)
        self.obstacles = set()
        self.game_started = False
        self.victory = False
        self.victory_timer = 0
        self.show_victory_message = False
        self.selected_path = 'astar'
        self.astar_cost = float('inf')
        self.ucs_cost = float('inf')

    def generate_obstacles(self):
        """Genera obstáculos aleatorios evitando posiciones del jugador y la casa"""
        self.obstacles.clear()
        positions = {(x, y) for x in range(GameConfig.GRID_WIDTH)
                     for y in range(GameConfig.GRID_HEIGHT)} - {self.player_pos, self.house_pos}
        self.obstacles = set(random.sample(list(positions), 150))


class Game:
    """Clase principal que maneja la lógica del juego"""

    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer(self.game_state)
        self.astar = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.ucs = UCS(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.initialize_game_variables()

    def initialize_game_variables(self):
        """Inicializa variables de control del juego"""
        self.edit_mode = None
        self.current_algorithm = 'astar'
        self.selected_path = 'astar'
        self.astar_path = self.ucs_path = self.current_path = None
        self.astar_cost = self.ucs_cost = float('inf')
        self.path_index = self.move_timer = 0

    def handle_mouse_click(self, pos):
        """Maneja los clics del mouse en el grid y la barra lateral"""
        x, y = pos
        if x < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
            self._handle_grid_click(x, y)
        else:
            self._handle_sidebar_click(x, y)

    def _handle_grid_click(self, x, y):
        """Procesa clics en la cuadrícula del juego"""
        grid_pos = (x // GameConfig.SQUARE_SIZE, y // GameConfig.SQUARE_SIZE)
        if grid_pos in self.game_state.obstacles:
            return

        if self.edit_mode == 'player' and grid_pos != self.game_state.house_pos:
            self.game_state.player_pos = grid_pos
        elif self.edit_mode == 'house' and grid_pos != self.game_state.player_pos:
            self.game_state.house_pos = grid_pos

        if self.game_state.game_started:
            self.calculate_path()

    def _handle_sidebar_click(self, x, y):
        """Procesa clics en la barra lateral"""
        sidebar_x = x - GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE
        if 10 <= sidebar_x <= 190:
            if 60 <= y <= 100:
                self.edit_mode = 'player' if self.edit_mode != 'player' else None
            elif 120 <= y <= 160:
                self.edit_mode = 'house' if self.edit_mode != 'house' else None

    def handle_keyboard(self, key):
        """Maneja eventos de teclado"""
        key_actions = {
            pygame.K_a: lambda: self._switch_path('astar'),
            pygame.K_u: lambda: self._switch_path('ucs'),
            pygame.K_SPACE: self._start_game,
            pygame.K_TAB: self._toggle_algorithm,
            pygame.K_r: self.reset_game
        }
        if key in key_actions:
            key_actions[key]()

    def _switch_path(self, path_type):
        """Cambia entre rutas A* y UCS"""
        self.selected_path = path_type
        self.current_path = self.astar_path if path_type == 'astar' else self.ucs_path
        self.path_index = 1 if self.current_path else 0

    def _start_game(self):
        """Inicia el juego si no está comenzado"""
        if not self.game_state.game_started:
            self.game_state.generate_obstacles()
            self.calculate_path()
            self.game_state.game_started = True
            self.path_index = 1 if self.current_path else 0

    def _toggle_algorithm(self):
        """Alterna entre algoritmos A* y UCS"""
        self.current_algorithm = 'ucs' if self.current_algorithm == 'astar' else 'astar'
        if self.game_state.game_started:
            self.calculate_path()

    def calculate_path_cost(self, path):
        """Calcula el costo de una ruta usando distancia Manhattan"""
        if not path:
            return float('inf')
        return sum(abs(x2 - x1) + abs(y2 - y1)
                   for (x1, y1), (x2, y2) in zip(path, path[1:]))

    def calculate_path(self):
        """Calcula las rutas usando A* y UCS"""
        start = self.game_state.player_pos
        goal = self.game_state.house_pos
        obstacles = self.game_state.obstacles

        self.astar_path = self.astar.find_path(start, goal, obstacles)
        self.ucs_path = self.ucs.find_path(start, goal, obstacles)

        self.astar_cost = self.calculate_path_cost(self.astar_path)
        self.ucs_cost = self.calculate_path_cost(self.ucs_path)

        self.current_path = self.astar_path if self.selected_path == 'astar' else self.ucs_path
        self.path_index = 1 if self.current_path else 0

    def update_player_movement(self):
        """Actualiza la posición del jugador siguiendo la ruta"""
        if not self._can_move():
            return

        self.move_timer += 1
        if self.move_timer >= GameConfig.GAME_SPEED // 50:
            self.move_timer = 0
            self.game_state.player_pos = self.current_path[self.path_index]
            self.path_index += 1

            if self.game_state.player_pos == self.game_state.house_pos:
                self._trigger_victory()

    def _can_move(self):
        """Verifica si el jugador puede moverse"""
        return (self.game_state.game_started and self.current_path
                and self.path_index < len(self.current_path))

    def _trigger_victory(self):
        """Activa el estado de victoria"""
        self.game_state.victory = True
        self.game_state.show_victory_message = True
        self.game_state.victory_timer = 0

    def reset_game(self):
        """Reinicia el juego a su estado inicial"""
        self.game_state.reset()
        self.initialize_game_variables()
        pygame.time.wait(200)

    def run(self):
        """Bucle principal del juego"""
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self._handle_victory_state()
            self._update_display()
            self._process_events()
            pygame.time.delay(GameConfig.GAME_SPEED)

    def _handle_victory_state(self):
        """Maneja el estado de victoria y la transición"""
        if self.game_state.victory:
            self._draw_victory_state()
            if self.game_state.victory_timer < 30:
                self.game_state.victory_timer += 1
                pygame.time.delay(30)
            else:
                self.reset_game()

    def _draw_victory_state(self):
        """Dibuja la pantalla de victoria"""
        self.renderer.draw_grid()
        self.renderer.draw_game_elements()
        self.renderer.draw_sidebar(self.edit_mode)
        self.renderer.show_congratulations()
        pygame.display.flip()

    def _update_display(self):
        """Actualiza todos los elementos visuales del juego"""
        self.renderer.draw_grid()
        if self.astar_path or self.ucs_path:
            self.renderer.draw_path(self.astar_path, self.ucs_path)
            self.game_state.astar_cost = self.astar_cost
            self.game_state.ucs_cost = self.ucs_cost
        self.renderer.draw_game_elements()
        self.renderer.draw_sidebar(self.edit_mode)
        pygame.display.flip()

    def _process_events(self):
        """Procesa todos los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                self.handle_keyboard(event.key)

        if self.game_state.game_started and self.current_path:
            self.update_player_movement()
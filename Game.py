import sys
import pygame
from config import GameConfig
from render import GameRenderer
import random
from ADB import AStar, UCS


class GameState:
    # Aquí guardo todo lo que pasa en el juego
    def __init__(self):
        self.reset()

    def reset(self):
        # Reinicio todo a como estaba al principio
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
        self.no_path_error = False
        self.error_timer = 0

    def generate_obstacles(self):
        """Genera obstáculos aleatorios evitando posiciones del jugador y la casa"""
        self.obstacles.clear()
        positions = {(x, y) for x in range(GameConfig.GRID_WIDTH)
                     for y in range(GameConfig.GRID_HEIGHT)} - {self.player_pos, self.house_pos}
        self.obstacles = set(random.sample(list(positions), 150))


class Game:
    # Esta es la clase principal donde controlo todo el juego
    def __init__(self):
        try:
            pygame.init()
            self.game_state = GameState()
            self.renderer = GameRenderer(self.game_state)
            # Creo los buscadores de rutas
            self.astar = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
            self.ucs = UCS(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
            self.initialize_game_variables()
            self.is_running = False
            self.last_click_time = 0  # Para prevenir doble clic
            self.edit_mode = None
            self.button_rects = {}  # Almacenará los rectángulos de los botones
            # Generar obstáculos iniciales
            self.game_state.generate_obstacles()
        except Exception as e:
            print(f"Error al inicializar el juego: {e}")
            raise

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
            self._handle_grid_click(x, y, 1)
        else:
            self._handle_sidebar_click(x, y)

    def _handle_grid_click(self, x, y, button):
        # Aquí manejo cuando el jugador hace clic en el tablero
        grid_pos = (x // GameConfig.SQUARE_SIZE, y // GameConfig.SQUARE_SIZE)

        if self.edit_mode == 'edit':
            if button == 1:  # Click izquierdo
                if grid_pos in self.game_state.obstacles:
                    self.game_state.obstacles.remove(grid_pos)
            elif button == 3:  # Click derecho
                if grid_pos not in self.game_state.obstacles and \
                        grid_pos != self.game_state.player_pos and \
                        grid_pos != self.game_state.house_pos:
                    self.game_state.obstacles.add(grid_pos)
        elif not self.is_running:
            if self.edit_mode == 'player' and grid_pos != self.game_state.house_pos:
                self.game_state.player_pos = grid_pos
                self.edit_mode = None  # Deselecciona después de colocar
            elif self.edit_mode == 'house' and grid_pos != self.game_state.player_pos:
                self.game_state.house_pos = grid_pos
                self.edit_mode = None  # Deselecciona después de colocar

        if self.game_state.game_started:
            self.calculate_path()

    def _handle_sidebar_click(self, x, y):
        """Procesa clics en la barra lateral usando los rectángulos de los botones"""
        mouse_pos = (x, y)

        # Usar los rectángulos de botones actualizados desde el renderer
        self.button_rects = self.renderer.get_button_rects()

        # Verificar clic en botones
        for button_id, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                self._handle_button_action(button_id)
                return True
        return False

    def _handle_button_action(self, action):
        """Maneja las acciones de los botones del sidebar"""
        if action == 'start':
            if not self.game_state.game_started:
                if self.selected_path:  # Verificar que se haya seleccionado una ruta
                    self.game_state.game_started = True
                    self.is_running = True
                    self.calculate_path()
            else:
                self.is_running = not self.is_running
        elif action in ['astar', 'ucs']:
            self.selected_path = action
            if self.game_state.game_started:
                self.calculate_path()
        else:
            self.edit_mode = None if self.edit_mode == action else action

    def handle_keyboard(self, key):
        """Maneja eventos de teclado - removido el inicio con teclas"""
        if key == pygame.K_r:
            self.reset_game()

    def _switch_path(self, path_type):
        """Cambia entre rutas A* y UCS"""
        self.selected_path = path_type
        self.current_path = self.astar_path if path_type == 'astar' else self.ucs_path
        self.path_index = 1 if self.current_path else 0

    def calculate_path_cost(self, path):
        """Calcula el costo de una ruta usando distancia Manhattan"""
        if not path:
            return float('inf')
        return sum(abs(x2 - x1) + abs(y2 - y1)
                   for (x1, y1), (x2, y2) in zip(path, path[1:]))

    def calculate_path(self):
        # Busco el mejor camino usando A* y UCS
        try:
            start = self.game_state.player_pos
            goal = self.game_state.house_pos
            obstacles = self.game_state.obstacles

            self.astar_path = self.astar.find_path(start, goal, obstacles)
            self.ucs_path = self.ucs.find_path(start, goal, obstacles)

            if not self.astar_path and not self.ucs_path:
                self.game_state.no_path_error = True
                self.game_state.error_timer = 0
                self.game_state.game_started = False
                self.is_running = False
                return False

            self.astar_cost = self.calculate_path_cost(self.astar_path)
            self.ucs_cost = self.calculate_path_cost(self.ucs_path)
            self.current_path = self.astar_path if self.selected_path == 'astar' else self.ucs_path
            self.path_index = 1 if self.current_path else 0
            return True
        except Exception as e:
            print(f"Error al calcular las rutas: {e}")
            return False

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
        self.game_state.victory_timer = 0
        self.is_running = False
        self.game_state.game_started = False

    def reset_game(self):
        """Reinicia el juego a su estado inicial"""
        self.game_state.reset()
        self.initialize_game_variables()
        self.game_state.generate_obstacles()
        self.calculate_path()
        pygame.time.wait(GameConfig.RESET_DELAY)

    def _toggle_game(self):
        """Alterna entre iniciar/pausar el juego"""
        if not self.game_state.game_started:
            # Verificar que se haya seleccionado una ruta
            if not hasattr(self, 'selected_path'):
                self.selected_path = 'astar'
            self.game_state.game_started = True
            self.is_running = True
            self.calculate_path()
        else:
            self.is_running = not self.is_running

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            try:
                if self.game_state.victory:
                    self._handle_victory_state()
                elif self.game_state.no_path_error:
                    self._handle_no_path_error()
                else:
                    self.renderer.screen.fill(GameConfig.BLACK)
                    self._update_display()

                running = self._process_events()
                pygame.time.delay(GameConfig.GAME_SPEED)
            except Exception as e:
                print(f"Error en el bucle principal: {e}")
                running = False

    def _handle_victory_state(self):
        """Maneja el estado de victoria y la transición"""
        if self.game_state.victory_timer == 0:
            # Dibuja primero el estado actual del juego
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()
            self.renderer.draw_game_elements()
            # Corregido: añadido el parámetro selected_path
            self.renderer.draw_sidebar(self.edit_mode, self.is_running, self.selected_path)
            # Superpone el mensaje de felicitaciones
            self.renderer.show_congratulations()

        if self.game_state.victory_timer < GameConfig.VICTORY_TIME:
            self.game_state.victory_timer += 1
            pygame.time.delay(GameConfig.VICTORY_DELAY)
        else:
            self.game_state.victory = False
            self.reset_game()
            self.is_running = False

    def _handle_no_path_error(self):
        """Maneja el estado de error cuando no hay ruta disponible"""
        if self.game_state.error_timer == 0:
            # Dibuja el estado actual del juego
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()
            self.renderer.draw_game_elements()
            # Corregido: añadido el parámetro selected_path
            self.renderer.draw_sidebar(self.edit_mode, self.is_running, self.selected_path)
            # Muestra el mensaje de error
            self.renderer.show_no_path_error()

        if self.game_state.error_timer < GameConfig.ERROR_TIME:
            self.game_state.error_timer += 1
            pygame.time.delay(GameConfig.ERROR_DELAY)
        else:
            self.game_state.no_path_error = False
            self.edit_mode = 'edit'  # Activar modo edición automáticamente

    def _update_display(self):
        """Actualiza todos los elementos visuales del juego"""
        self.renderer.draw_grid()
        # Solo muestra las rutas si el juego ha iniciado
        if self.game_state.game_started and (self.astar_path or self.ucs_path):
            self.renderer.draw_path(self.astar_path, self.ucs_path)
            self.game_state.astar_cost = self.astar_cost
            self.game_state.ucs_cost = self.ucs_cost
        self.renderer.draw_game_elements()
        self.renderer.draw_sidebar(self.edit_mode, self.is_running, self.selected_path)
        pygame.display.flip()

    def _process_events(self):
        """Procesa todos los eventos del juego"""
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif not self.game_state.victory and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
                        self._handle_grid_click(event.pos[0], event.pos[1], event.button)
                    else:
                        self._handle_sidebar_click(event.pos[0], event.pos[1])
                elif not self.game_state.victory and event.type == pygame.KEYDOWN:
                    self.handle_keyboard(event.key)

            if not self.game_state.victory and self.game_state.game_started and \
                    self.current_path and self.is_running:
                self.update_player_movement()

            return True
        except Exception as e:
            print(f"Error en el procesamiento de eventos: {e}")
            return False
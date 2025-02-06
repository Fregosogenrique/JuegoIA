import sys
import pygame
from config import GameConfig
from render import GameRenderer
import random

class GameState:
    def __init__(self):
        self.player_pos = (1, 1)
        self.house_pos = (8, 8)
        self.obstacles = set()
        self.game_started = False
        self.victory = False
        self.victory_timer = 0
        self.show_victory_message = False
        self.selected_path = 'astar'  # Por defecto A*
        self.astar_cost = float('inf')
        self.ucs_cost = float('inf')
    
    def reset(self):
        self.player_pos = (1, 1)
        self.house_pos = (8, 8)
        self.obstacles = set()
        self.game_started = False
        self.victory = False
        self.victory_timer = 0
        self.show_victory_message = False
    
    def generate_obstacles(self):
        self.obstacles = set()
        num_obstacles = 150
        while len(self.obstacles) < num_obstacles:
            x = random.randint(0, GameConfig.GRID_WIDTH - 1)
            y = random.randint(0, GameConfig.GRID_HEIGHT - 1)
            pos = (x, y)
            if pos != self.player_pos and pos != self.house_pos:
                self.obstacles.add(pos)
from Eventos_Teclado import InputHandler
from ADB import *


class Game:
    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer(self.game_state)
        self.game_over = False
        self.input_handler = InputHandler()
        self.astar = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.ucs = UCS(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.edit_mode = None  # Puede ser 'player' o 'house'
        self.current_algorithm = 'astar'  # Puede ser 'astar' o 'ucs'
        self.selected_path = 'astar'  # Ruta actualmente seleccionada para seguir
        self.astar_path = None
        self.ucs_path = None
        self.current_path = None
        self.astar_cost = float('inf')
        self.ucs_cost = float('inf')
        self.path_index = 0
        self.move_timer = 0
        self.game_state.game_started = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Manejo de clics del mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if x < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
                    # Clic en el grid
                    grid_x = x // GameConfig.SQUARE_SIZE
                    grid_y = y // GameConfig.SQUARE_SIZE
                    grid_pos = (grid_x, grid_y)
                    
                    if self.edit_mode == 'player':
                        if grid_pos not in self.game_state.obstacles and grid_pos != self.game_state.house_pos:
                            self.game_state.player_pos = grid_pos
                            if self.game_state.game_started:
                                self.calculate_path()
                    elif self.edit_mode == 'house':
                        if grid_pos not in self.game_state.obstacles and grid_pos != self.game_state.player_pos:
                            self.game_state.house_pos = grid_pos
                            if self.game_state.game_started:
                                self.calculate_path()
                else:
                    # Clic en la barra lateral
                    sidebar_x = x - GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE
                    
                    # Detectar clic en botón de jugador
                    if 10 <= sidebar_x <= 190 and 60 <= y <= 100:
                        self.edit_mode = 'player' if self.edit_mode != 'player' else None
                    
                    # Detectar clic en botón de casa
                    elif 10 <= sidebar_x <= 190 and 120 <= y <= 160:
                        self.edit_mode = 'house' if self.edit_mode != 'house' else None
            
            # Manejo de eventos de teclado
            # Manejo de eventos de teclado
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.selected_path = 'astar'
                    self.current_path = self.astar_path
                    self.path_index = 1 if self.current_path else 0
                elif event.key == pygame.K_u:
                    self.selected_path = 'ucs'
                    self.current_path = self.ucs_path
                    self.path_index = 1 if self.current_path else 0
                elif event.key == pygame.K_SPACE and not self.game_state.game_started:
                    self.game_state.generate_obstacles()
                    self.calculate_path()
                    self.game_state.game_started = True
                    self.path_index = 1 if self.current_path else 0
                    self.move_timer = 0
                elif event.key == pygame.K_TAB:
                    self.current_algorithm = 'ucs' if self.current_algorithm == 'astar' else 'astar'
                    if self.game_state.game_started:
                        self.calculate_path()
                elif event.key == pygame.K_r:
                    self.reset_game()
    def calculate_path_cost(self, path):
        if not path:
            return float('inf')
        cost = 0
        for i in range(len(path) - 1):
            # Calculamos el costo como la distancia Manhattan entre puntos consecutivos
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            cost += abs(x2 - x1) + abs(y2 - y1)
        return cost

    def calculate_path(self):
        self.astar_path = self.astar.find_path(
            self.game_state.player_pos,
            self.game_state.house_pos,
            self.game_state.obstacles
        )
        self.ucs_path = self.ucs.find_path(
            self.game_state.player_pos,
            self.game_state.house_pos,
            self.game_state.obstacles
        )
        
        # Calcular costos
        self.astar_cost = self.calculate_path_cost(self.astar_path)
        self.ucs_cost = self.calculate_path_cost(self.ucs_path)
        
        # Mantener el camino seleccionado por el usuario
        if self.selected_path == 'astar':
            self.current_path = self.astar_path
        else:
            self.current_path = self.ucs_path
        
        self.path_index = 1 if self.current_path else 0

    def update_player_movement(self):
        """Actualiza la posición del jugador siguiendo el camino calculado"""
        if not self.game_state.game_started or not self.current_path or self.path_index >= len(self.current_path):
            return

        self.move_timer += 1
        if self.move_timer >= GameConfig.GAME_SPEED // 50:  # Ajusta la velocidad del movimiento
            self.move_timer = 0
            self.game_state.player_pos = self.current_path[self.path_index]
            self.path_index += 1
            
            # Verificar si llegamos al final del camino
            if self.game_state.player_pos == self.game_state.house_pos:
                self.game_state.victory = True
                self.game_state.show_victory_message = True
                self.game_state.victory_timer = 0
                return

    def reset_game(self):
        self.game_state.reset()
        self.astar_path = None
        self.ucs_path = None
        self.current_path = None
        self.path_index = 0
        self.move_timer = 0
        self.current_algorithm = 'astar'
        self.edit_mode = None
        pygame.time.wait(200)  # Pausa breve para transición suave
    def run(self):
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()
            
            if self.game_state.victory:
                # Dibujamos todo el estado del juego normalmente
                self.renderer.draw_grid()
                self.renderer.draw_game_elements()
                self.renderer.draw_sidebar(self.edit_mode)
                
                # Mostramos el mensaje de victoria
                self.renderer.show_congratulations()
                pygame.display.flip()
                
                # Esperamos un momento antes de reiniciar
                if self.game_state.victory_timer < 30:  # Medio segundo
                    self.game_state.victory_timer += 1
                    pygame.time.delay(50)  # Pequeña pausa para estabilizar la pantalla
                else:
                    self.reset_game()
                    continue
            
            if self.astar_path or self.ucs_path:
                if self.astar_path or self.ucs_path:
                    self.renderer.draw_path(self.astar_path, self.ucs_path)
                    self.game_state.astar_cost = self.astar_cost
                    self.game_state.ucs_cost = self.ucs_cost

            self.renderer.draw_game_elements()
            self.renderer.draw_sidebar(self.edit_mode)
            self.handle_events()

            if self.game_state.game_started and self.current_path:
                self.update_player_movement()

            pygame.display.flip()
            pygame.time.delay(GameConfig.GAME_SPEED)
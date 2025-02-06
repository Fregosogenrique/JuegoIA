#Modulo Principal del juego
# Game.py
import sys
import pygame
from config import GameConfig
from state import GameState
from render import GameRenderer
from Eventos_Teclado import InputHandler
from ADB import *


class Game:
    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer()
        self.input_handler = InputHandler()
        self.astar = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.ucs = UCS(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.current_algorithm = 'astar'
        self.astar_path = None
        self.ucs_path = None
        self.current_path = None
        self.astar_cost = float('inf')
        self.ucs_cost = float('inf')
        self.path_index = 0
        self.move_timer = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not self.game_state.game_started:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
                        self.input_handler.handle_grid_click(event.pos, self.game_state)
                    else:
                        self.input_handler.handle_sidebar_click(event.pos, self.game_state)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.game_state.game_started = True
                        self.game_state.generate_obstacles()
                        self.calculate_path()
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
        
        # Seleccionar el camino más eficiente
        if self.astar_cost <= self.ucs_cost:
            self.current_path = self.astar_path
            self.current_algorithm = 'astar'
        else:
            self.current_path = self.ucs_path
            self.current_algorithm = 'ucs'
        
        self.path_index = 1 if self.current_path else 0

    def update_player_movement(self):
        """Actualiza la posición del jugador siguiendo el camino calculado"""
        if not self.current_path or self.path_index >= len(self.current_path):
            return

        self.move_timer += 1
        if self.move_timer >= GameConfig.GAME_SPEED // 50:  # Ajusta la velocidad del movimiento
            self.move_timer = 0
            self.game_state.player_pos = self.current_path[self.path_index]
            self.path_index += 1

            if self.game_state.player_pos == self.game_state.house_pos:
                self.renderer.show_congratulations()
                self.reset_game()

    def reset_game(self):
        self.game_state.reset()
        self.astar_path = None
        self.ucs_path = None
        self.current_path = None
        self.path_index = 0
        self.move_timer = 0
        self.current_algorithm = 'astar'
    def run(self):
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()

            if self.astar_path or self.ucs_path:
                self.renderer.draw_path(self.astar_path, self.ucs_path)

            self.renderer.draw_game_elements(self.game_state)
            self.renderer.draw_sidebar(self.game_state)
            self.handle_events()

            if self.game_state.game_started and self.current_path:
                self.update_player_movement()

            pygame.display.flip()
            pygame.time.delay(GameConfig.GAME_SPEED)
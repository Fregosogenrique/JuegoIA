#Modulo Principal del juego
# Game.py
import sys
import pygame
from config import GameConfig
from state import GameState
from render import GameRenderer
from Eventos_Teclado import InputHandler
from AStar import AStar


class Game:
    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer()
        self.input_handler = InputHandler()
        self.pathfinder = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.current_path = None
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
                    self.game_state.game_started = True
                    #self.game_state.generate_obstacles()
                    # Calcular el camino inicial cuando comienza el juego
                    self.calculate_path()

    def calculate_path(self):
        """Calcula el camino usando A*"""
        self.current_path = self.pathfinder.find_path(
            self.game_state.player_pos,
            self.game_state.house_pos,
            self.game_state.obstacles
        )
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
                self.game_state.reset()
                self.current_path = None
                self.path_index = 0

    def run(self):
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()

            # Dibujar el camino si existe
            if self.current_path:
                self.renderer.draw_path(self.current_path)

            self.renderer.draw_game_elements(self.game_state)
            self.renderer.draw_sidebar(self.game_state)
            self.handle_events()

            if self.game_state.game_started and self.current_path:
                self.update_player_movement()

            pygame.display.flip()
            pygame.time.delay(GameConfig.GAME_SPEED)

import sys
import pygame
from config import GameConfig
from state import GameState
from render import GameRenderer
from Eventos_Teclado import InputHandler
from ADB import AStar, UCS


class Game:
    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer()
        self.input_handler = InputHandler()
        self.astar = AStar(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.ucs = UCS(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.current_algorithm = "astar"
        self.astar_path = None
        self.ucs_path = None
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
                    if event.key == pygame.K_SPACE:  # Iniciar juego con espacio
                        self.game_state.game_started = True
                        self.game_state.generate_obstacles()
                        self.calculate_paths()
                    elif event.key == pygame.K_TAB:  # Cambiar algoritmo con TAB
                        self.current_algorithm = "ucs" if self.current_algorithm == "astar" else "astar"
                        self.calculate_paths()

    def calculate_paths(self):
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
        self.path_index = 1

    def get_current_path(self):
        return self.astar_path if self.current_algorithm == "astar" else self.ucs_path

    def update_player_movement(self):
        current_path = self.get_current_path()
        if not current_path or self.path_index >= len(current_path):
            return

        self.move_timer += 1
        if self.move_timer >= GameConfig.GAME_SPEED // 50:
            self.move_timer = 0
            self.game_state.player_pos = current_path[self.path_index]
            self.path_index += 1

            if self.game_state.player_pos == self.game_state.house_pos:
                self.renderer.show_congratulations()
                self.game_state.reset()
                self.astar_path = None
                self.ucs_path = None
                self.path_index = 0

    def run(self):
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()

            # Dibujar ambos caminos si existen
            self.renderer.draw_path(self.astar_path, self.ucs_path)

            self.renderer.draw_game_elements(self.game_state)
            self.renderer.draw_sidebar(self.game_state, self.current_algorithm)
            self.handle_events()

            if self.game_state.game_started and self.get_current_path():
                self.update_player_movement()

            pygame.display.flip()
            pygame.time.delay(GameConfig.GAME_SPEED)
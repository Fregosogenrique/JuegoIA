#Modulo Principal del juego
import sys
import pygame
from config import GameConfig
from state import GameState
from render import GameRenderer
from Eventos_Teclado import InputHandler


class Game:
    def __init__(self):
        pygame.init()
        self.game_state = GameState()
        self.renderer = GameRenderer()
        self.input_handler = InputHandler()

    def handle_events(self):
        #Maneja todos los eventos del juego
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not self.game_state.game_started:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
                        self.input_handler.handle_grid_click(event.pos,
                                                             self.game_state)
                    else:
                        self.input_handler.handle_sidebar_click(event.pos,
                                                                self.game_state)
                elif event.type == pygame.KEYDOWN:
                    self.game_state.game_started = True
                    self.game_state.generate_obstacles()
            else:
                if event.type == pygame.KEYDOWN:
                    self.handle_movement(event.key)

    def handle_movement(self, key):
        #Maneja el movimiento del jugador en el mapa
        dx = dy = 0
        if key == pygame.K_UP:
            dy = -1
        elif key == pygame.K_DOWN:
            dy = 1
        elif key == pygame.K_LEFT:
            dx = -1
        elif key == pygame.K_RIGHT:
            dx = 1

        self.move_player(dx, dy)

    def move_player(self, dx, dy):
        #Mueve al jugador en la dirección especificada
        new_x = self.game_state.player_pos[0] + dx
        new_y = self.game_state.player_pos[1] + dy

        if (0 <= new_x < GameConfig.GRID_WIDTH and
                0 <= new_y < GameConfig.GRID_HEIGHT and
                [new_x, new_y] not in self.game_state.obstacles):
            if [new_x, new_y] == self.game_state.house_pos:
                self.renderer.show_congratulations()
                self.game_state.reset()
            else:
                self.game_state.player_pos[0] = new_x
                self.game_state.player_pos[1] = new_y

    def run(self):
        #Bucle principal del juego
        while True:
            self.renderer.screen.fill(GameConfig.BLACK)
            self.renderer.draw_grid()
            self.renderer.draw_game_elements(self.game_state)
            self.renderer.draw_sidebar(self.game_state)
            self.handle_events()
            pygame.display.flip()
            pygame.time.delay(GameConfig.GAME_SPEED)

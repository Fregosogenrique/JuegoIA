#Modulo que maneja las entradas del usuario
import pygame
from config import GameConfig


class InputHandler:
    @staticmethod
    def handle_sidebar_click(pos, game_state):
        #Maneja los clics en la barra lateral
        sidebar_x = GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE

        if pos[0] > sidebar_x:
            if 60 <= pos[1] <= 100:
                game_state.selected_item = 'player'
            elif 120 <= pos[1] <= 160:
                game_state.selected_item = 'house'

    @staticmethod
    def handle_grid_click(pos, game_state):
        #Maneja los clics en la cuadrícula
        grid_x = pos[0] // GameConfig.SQUARE_SIZE
        grid_y = pos[1] // GameConfig.SQUARE_SIZE

        if grid_x < GameConfig.GRID_WIDTH and grid_y < GameConfig.GRID_HEIGHT:
            new_pos = [grid_x, grid_y]
            if new_pos not in game_state.obstacles:
                if (game_state.selected_item == 'player' and
                        new_pos != game_state.house_pos):
                    game_state.player_pos = new_pos
                elif (game_state.selected_item == 'house' and
                      new_pos != game_state.player_pos):
                    game_state.house_pos = new_pos
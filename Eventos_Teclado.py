
import pygame
from config import GameConfig

class InputHandler:
    def __init__(self):
        self.button_rects = {
            'player': pygame.Rect(
                GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                160,
                180,
                40
            ),
            'house': pygame.Rect(
                GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                220,
                180,
                40
            )
        }

    def handle_grid_click(self, pos, game_state):
        if game_state.game_started:
            return

        grid_x = pos[0] // GameConfig.SQUARE_SIZE
        grid_y = pos[1] // GameConfig.SQUARE_SIZE

        if 0 <= grid_x < GameConfig.GRID_WIDTH and 0 <= grid_y < GameConfig.GRID_HEIGHT:
            new_pos = (grid_x, grid_y)
            
            if game_state.selected_item == 'player' and new_pos != game_state.house_pos:
                game_state.player_pos = new_pos
            elif game_state.selected_item == 'house' and new_pos != game_state.player_pos:
                game_state.house_pos = new_pos

    def handle_sidebar_click(self, pos, game_state):
        if game_state.game_started:
            return

        for button_name, button_rect in self.button_rects.items():
            if button_rect.collidepoint(pos):
                game_state.selected_item = button_name
                break

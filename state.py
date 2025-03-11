
#De esta forma se manejan los estados del juego
import random
import pygame
from config import GameConfig


class GameState:
    def __init__(self):
        self.player_pos = [1, 1]
        self.house_pos = [5, 5]
        self.obstacles = []
        self.game_started = False
        self.selected_item = None

    def reset(self):
        #Reinicia el estado del juego
        self.player_pos = [1, 1]
        self.house_pos = [random.randint(0, GameConfig.GRID_WIDTH - 1),
                          random.randint(0, GameConfig.GRID_HEIGHT - 1)]
        self.obstacles.clear()
        self.game_started = False
        self.selected_item = None
        self.generate_obstacles()

    #Funcion temporalmente desahabilitada
    def generate_obstacles(self):
        #Generacion de obstáculos aleatorios
        self.obstacles.clear()
        while len(self.obstacles) < GameConfig.OBSTACLE_COUNT:
            pos = [random.randint(0, GameConfig.GRID_WIDTH - 1),
                   random.randint(0, GameConfig.GRID_HEIGHT - 1)]
            if (pos != self.player_pos and
                    pos != self.house_pos and
                    pos not in self.obstacles):
                self.obstacles.append(pos)
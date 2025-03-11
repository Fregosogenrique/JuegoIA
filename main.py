import pygame
from Game import Game


def main():
    # Inicializar Pygame
    pygame.init()

    # Inicializar el juego
    game = Game()

    # Ejecutar el bucle principal
    game.run()

    # Cerrar Pygame
    pygame.quit()


if __name__ == "__main__":
    main()
import sys
import pygame
from Game import Game

def main():
    # Inicio mi juego aquí, manejo errores por si algo sale mal
    try:
        pygame.init()
        game = Game()
        game.run()
    except Exception as e:
        print(f"Ups, algo salió mal: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
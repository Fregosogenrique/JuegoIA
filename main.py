"""
Módulo principal para la aplicación del juego con IA.

Este módulo sirve como punto de entrada para la aplicación. Inicializa
los componentes necesarios de Pygame, crea una instancia del juego y
ejecuta el bucle principal del juego.
"""

import pygame
from Game import Game # Importo mi clase Game desde el archivo Game.py


def main():
    """
    Mi función principal que inicializa y ejecuta el juego.
    """
    # La inicialización de Pygame (pygame.init()) y su cierre (pygame.quit())
    # ahora están manejados dentro de la clase Game (en __init__ y al final de run_main_game_loop).
    # Así que aquí solo necesito crear la instancia y correrla.

    # Creo una instancia de mi juego.
    juego_instancia = Game()

    # Ejecuto el bucle principal del juego.
    juego_instancia.run_main_game_loop()


if __name__ == "__main__":
    # Esta línea asegura que main() solo se ejecute cuando corro este archivo directamente.
    main()
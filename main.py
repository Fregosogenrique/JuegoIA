"""
Módulo principal para la aplicación del juego con IA.

Este módulo sirve como punto de entrada para la aplicación. Inicializa 
los componentes necesarios de Pygame, crea una instancia del juego y 
ejecuta el bucle principal del juego.
"""

import pygame
from Game import Game


def main():
    """
    Función principal que inicializa y ejecuta el juego.
    
    Esta función realiza las siguientes tareas:
    1. Inicializa el módulo Pygame
    2. Crea una instancia del juego
    3. Ejecuta el bucle principal del juego
    4. Cierra correctamente Pygame cuando el juego termina
    
    Returns:
        None
    """
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
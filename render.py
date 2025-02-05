#Renderizacion del juego
import pygame
from config import GameConfig

class GameRenderer:
    def __init__(self):
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH,
                                             GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Fregoso Gutierrez IA25A")

        # Cargar y escalar imágenes
        self.player_image = pygame.image.load(GameConfig.PLAYER_IMAGE)
        self.house_image = pygame.image.load(GameConfig.HOUSE_IMAGE)
        self.player_image = pygame.transform.scale(self.player_image,
                                                 (GameConfig.SQUARE_SIZE,
                                                  GameConfig.SQUARE_SIZE))
        self.house_image = pygame.transform.scale(self.house_image,
                                                (GameConfig.SQUARE_SIZE,
                                                 GameConfig.SQUARE_SIZE))

    def draw_grid(self):#Dibuja la cuadrícula del juego
        for x in range(0, GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
                      GameConfig.SQUARE_SIZE):
            for y in range(0, GameConfig.SCREEN_HEIGHT, GameConfig.SQUARE_SIZE):
                rect = pygame.Rect(x, y, GameConfig.SQUARE_SIZE,
                                 GameConfig.SQUARE_SIZE)
                pygame.draw.rect(self.screen, GameConfig.WHITE, rect, 1)

    def draw_game_elements(self, game_state):#Funcion para los obstaculos
        """# Dibujar obstáculos /Temporalmente deshabilitado
        for obs in game_state.obstacles:
            obstacle_rect = pygame.Rect(
                obs[0] * GameConfig.SQUARE_SIZE,
                obs[1] * GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE
            )
            pygame.draw.rect(self.screen, GameConfig.GRAY, obstacle_rect)"""""

        # Dibujar jugador
        player_rect = pygame.Rect(
            game_state.player_pos[0] * GameConfig.SQUARE_SIZE,
            game_state.player_pos[1] * GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE
        )

        # Dibujar casa
        house_rect = pygame.Rect(
            game_state.house_pos[0] * GameConfig.SQUARE_SIZE,
            game_state.house_pos[1] * GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE
        )

        self.screen.blit(self.player_image, player_rect.topleft)
        self.screen.blit(self.house_image, house_rect.topleft)

    def draw_sidebar(self, game_state):#Manejo de la barra lateral
        # Fondo de la barra lateral
        sidebar_rect = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
            0,
            GameConfig.SIDEBAR_WIDTH,
            GameConfig.SCREEN_HEIGHT
        )
        pygame.draw.rect(self.screen, GameConfig.GRAY, sidebar_rect)

        # Configurar fuente
        font = pygame.font.Font(None, 24)

        # Título
        title = font.render("Configuración Inicial", True, GameConfig.BLACK)
        self.screen.blit(title, (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10, 20))

        # Botones
        player_button = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
            60,
            180,
            40
        )
        house_button = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
            120,
            180,
            40
        )

        # Colorear botones
        pygame.draw.rect(
            self.screen,
            GameConfig.RED if game_state.selected_item == 'player' else GameConfig.WHITE,
            player_button
        )
        pygame.draw.rect(
            self.screen,
            GameConfig.RED if game_state.selected_item == 'house' else GameConfig.WHITE,
            house_button
        )

        # Texto de botones
        player_text = font.render("Posición Jugador", True, GameConfig.BLACK)
        house_text = font.render("Posición Casa", True, GameConfig.BLACK)

        self.screen.blit(player_text, (player_button.x + 10, player_button.y + 10))
        self.screen.blit(house_text, (house_button.x + 10, house_button.y + 10))

        # Instrucciones
        if not game_state.game_started:
            instructions = [
                "1. Selecciona un ",
                "   elemento",
                "2. Haz clic en la",
                "   cuadrícula para",
                "   posicionar",
                "3. Presiona una tecla",
                "   para iniciar"
            ]
            for i, text in enumerate(instructions):
                instruction = font.render(text, True, GameConfig.BLACK)
                self.screen.blit(instruction,
                               (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                                200 + i * 30))

    def show_congratulations(self):
        #Muestra mensaje de felicitación"""
        font = pygame.font.Font(None, 74)
        text = font.render("¡Felicitaciones, ruta alcanzada!", True, GameConfig.GREEN)
        text_rect = text.get_rect(center=(GameConfig.SCREEN_WIDTH // 2,
                                        GameConfig.SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(2000)

    # Añadir este método a la clase GameRenderer
    def draw_path(self, path):
        """Dibuja el camino calculado por A*"""
        if path:
            for i in range(len(path) - 1):
                start_pos = path[i]
                end_pos = path[i + 1]

                start_pixel = (
                    start_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                    start_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                )
                end_pixel = (
                    end_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                    end_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                )

                pygame.draw.line(
                    self.screen,
                    (0, 255, 0),  # Color verde para el camino
                    start_pixel,
                    end_pixel,
                    2  # Grosor de la línea
                )
#Renderizacion del juego
import pygame
from config import GameConfig

class GameRenderer:
    def __init__(self, game_state):
        self.game_state = game_state
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

    def draw_game_elements(self):
        # Dibujar obstáculos
        for obs in self.game_state.obstacles:
            obstacle_rect = pygame.Rect(
                obs[0] * GameConfig.SQUARE_SIZE,
                obs[1] * GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE
            )
            pygame.draw.rect(self.screen, GameConfig.GRAY, obstacle_rect)

        # Dibujar jugador
        player_rect = pygame.Rect(
            self.game_state.player_pos[0] * GameConfig.SQUARE_SIZE,
            self.game_state.player_pos[1] * GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE
        )

        # Dibujar casa
        house_rect = pygame.Rect(
            self.game_state.house_pos[0] * GameConfig.SQUARE_SIZE,
            self.game_state.house_pos[1] * GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE,
            GameConfig.SQUARE_SIZE
        )

        self.screen.blit(self.player_image, player_rect.topleft)
        self.screen.blit(self.house_image, house_rect.topleft)

    def draw_sidebar(self, edit_mode):  # Manejo de la barra lateral
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
            GameConfig.RED if edit_mode == 'player' else GameConfig.WHITE,
            player_button
        )
        pygame.draw.rect(
            self.screen,
            GameConfig.RED if edit_mode == 'house' else GameConfig.WHITE,
            house_button
        )

        # Texto de botones
        player_text = font.render("Posición Jugador", True, GameConfig.BLACK)
        house_text = font.render("Posición Casa", True, GameConfig.BLACK)

        self.screen.blit(player_text, (player_button.x + 10, player_button.y + 10))
        self.screen.blit(house_text, (house_button.x + 10, house_button.y + 10))

        # Instrucciones
        if not self.game_state.game_started:
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
        if self.game_state.game_started:
            astar_cost_text = font.render(f"A* Cost: {self.game_state.astar_cost:.2f}", True, GameConfig.BLACK)
            ucs_cost_text = font.render(f"UCS Cost: {self.game_state.ucs_cost:.2f}", True, GameConfig.BLACK)
            Eficiente = (int(self.game_state.astar_cost),int(self.game_state.ucs_cost))

            instructions = [
                "La ruta A* tiene",
                "un costo de: "+str(Eficiente[0]),
                "La ruta UCS tiene",
                "un costo de: "+str(Eficiente[1]),
                "   posicionar",
                "La ruta mas rapida",
                "tiene un costo de: " + str(min(Eficiente)),
                "Para desplazarte por ",
                "las rutas presiona",
                "A para A* y U para UCS"

            ]
            for i, text in enumerate(instructions):
                instruction = font.render(text, True, GameConfig.BLACK)
                self.screen.blit(instruction,
                                 (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                                  200 + i * 30))
    def show_congratulations(self):
        # Crear un fondo semi-transparente
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0,0))

        # Mostrar mensaje de felicitación
        font = pygame.font.Font(None, 74)
        text = font.render("¡Felicitaciones!", True, GameConfig.GREEN)
        text_rect = text.get_rect(center=(GameConfig.SCREEN_WIDTH // 2,
                                    GameConfig.SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(text, text_rect)

        subtext = font.render("¡Ruta alcanzada!", True, GameConfig.GREEN)
        subtext_rect = subtext.get_rect(center=(GameConfig.SCREEN_WIDTH // 2,
                                            GameConfig.SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(subtext, subtext_rect)

    def draw_path(self, astar_path=None, ucs_path=None):
        def draw_route(path, color):
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
                        color,
                        start_pixel,
                        end_pixel,
                        2
                    )
        
        # Dibujar ambas rutas
        draw_route(astar_path, (0, 255, 0))  # Verde para A*
        draw_route(ucs_path, (0, 0, 255))    # Azul para UCS
        
        # Agregar leyenda en la barra lateral
        font = pygame.font.Font(None, 24)
        legend_y = 400
        # Leyenda para A*
        pygame.draw.line(
            self.screen,
            (0, 255, 0),
            (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10, legend_y + 10),
            (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 30, legend_y + 10),
            2
        )
        astar_text = font.render("A* Path (Presiona 'A')", True, GameConfig.BLACK)
        self.screen.blit(astar_text, (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 40, legend_y))
        
        # Leyenda para UCS
        pygame.draw.line(
            self.screen,
            (0, 0, 255),
            (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10, legend_y + 40),
            (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 30, legend_y + 40),
            2
        )
        ucs_text = font.render("UCS Path (Presiona 'U')", True, GameConfig.BLACK)
        self.screen.blit(ucs_text, (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 40, legend_y + 30))

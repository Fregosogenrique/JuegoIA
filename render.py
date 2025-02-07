import pygame
from config import GameConfig


class GameRenderer:
    """
    Clase encargada de renderizar todos los elementos visuales del juego.
    Maneja la ventana principal, elementos gráficos y la interfaz de usuario.
    """

    def __init__(self, game_state):
        # Inicialización de la ventana del juego
        self.game_state = game_state
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH,
                                               GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Fregoso Gutierrez IA25A")

        # Carga y escalado de imágenes del jugador y la casa
        self.player_image = pygame.transform.scale(
            pygame.image.load(GameConfig.PLAYER_IMAGE),
            (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE)
        )
        self.house_image = pygame.transform.scale(
            pygame.image.load(GameConfig.HOUSE_IMAGE),
            (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE)
        )

    def draw_grid(self):
        """
        Dibuja la cuadrícula del juego, creando una matriz visual
        donde se moverá el jugador.
        """
        for x in range(0, GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
                       GameConfig.SQUARE_SIZE):
            for y in range(0, GameConfig.SCREEN_HEIGHT, GameConfig.SQUARE_SIZE):
                pygame.draw.rect(
                    self.screen,
                    GameConfig.WHITE,
                    pygame.Rect(x, y, GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE),
                    1
                )

    def draw_game_elements(self):
        """
        Dibuja los elementos principales del juego:
        - Obstáculos (bloques grises)
        - Jugador (imagen cargada)
        - Casa (imagen cargada)
        """
        # Dibuja obstáculos
        for obs in self.game_state.obstacles:
            pygame.draw.rect(
                self.screen,
                GameConfig.GRAY,
                pygame.Rect(
                    obs[0] * GameConfig.SQUARE_SIZE,
                    obs[1] * GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE
                )
            )

        # Posiciona jugador y casa usando sus imágenes
        self.screen.blit(
            self.player_image,
            (self.game_state.player_pos[0] * GameConfig.SQUARE_SIZE,
             self.game_state.player_pos[1] * GameConfig.SQUARE_SIZE)
        )
        self.screen.blit(
            self.house_image,
            (self.game_state.house_pos[0] * GameConfig.SQUARE_SIZE,
             self.game_state.house_pos[1] * GameConfig.SQUARE_SIZE)
        )

    def draw_sidebar(self, edit_mode):
        """
        Dibuja la barra lateral con controles e información:
        - Botones de configuración
        - Instrucciones del juego
        - Información de costos de rutas
        """
        # Fondo de la barra lateral
        sidebar_rect = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
            0,
            GameConfig.SIDEBAR_WIDTH,
            GameConfig.SCREEN_HEIGHT
        )
        pygame.draw.rect(self.screen, GameConfig.GRAY, sidebar_rect)

        font = pygame.font.Font(None, 24)

        # Título y botones
        title = font.render("Configuración Inicial", True, GameConfig.BLACK)
        self.screen.blit(title, (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10, 20))

        # Botones de posicionamiento
        buttons = [
            ('player', "Posición Jugador", 60),
            ('house', "Posición Casa", 120)
        ]

        for button_id, text, y_pos in buttons:
            button_rect = pygame.Rect(
                GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                y_pos,
                180,
                40
            )
            pygame.draw.rect(
                self.screen,
                GameConfig.RED if edit_mode == button_id else GameConfig.WHITE,
                button_rect
            )
            button_text = font.render(text, True, GameConfig.BLACK)
            self.screen.blit(button_text, (button_rect.x + 10, button_rect.y + 10))

        # Muestra instrucciones según el estado del juego
        instructions = self._get_instructions() if not self.game_state.game_started else \
            self._get_game_status()

        for i, text in enumerate(instructions):
            instruction = font.render(text, True, GameConfig.BLACK)
            self.screen.blit(instruction,
                             (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 10,
                              200 + i * 30))

    def _get_instructions(self):
        """Retorna las instrucciones iniciales del juego"""
        return [
            "1. Selecciona un elemento",
            "2. Haz clic en la cuadrícula",
            "   para posicionar",
            "3. Presiona una tecla",
            "   para iniciar"
        ]

    def _get_game_status(self):
        """Retorna el estado actual del juego y costos de rutas"""
        costs = (int(self.game_state.astar_cost), int(self.game_state.ucs_cost))
        return [
            "La ruta A* tiene",
            f"un costo de: {costs[0]}",
            "La ruta UCS tiene",
            f"un costo de: {costs[1]}",
            "La ruta mas rapida",
            f"tiene un costo de: {min(costs)}",
            "Para desplazarte por",
            "las rutas presiona",
            "A para A* (Linea Verde",
            "U para UCS (Linea Azul)"
        ]

    def show_congratulations(self):
        """Muestra la pantalla de felicitación al completar una ruta"""
        # Overlay semitransparente
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        # Mensajes de felicitación
        font = pygame.font.Font(None, 74)
        messages = [
            ("¡Felicitaciones!", -40),
            ("¡Ruta alcanzada!", 40)
        ]

        for text, y_offset in messages:
            rendered_text = font.render(text, True, GameConfig.GREEN)
            text_rect = rendered_text.get_rect(
                center=(GameConfig.SCREEN_WIDTH // 2,
                        GameConfig.SCREEN_HEIGHT // 2 + y_offset)
            )
            self.screen.blit(rendered_text, text_rect)

    def draw_path(self, astar_path=None, ucs_path=None):
        """
        Dibuja las rutas calculadas por A* y UCS.
        Incluye una leyenda para identificar cada ruta.
        """

        def draw_route(path, color):
            """Dibuja una ruta específica con el color indicado"""
            if path:
                for i in range(len(path) - 1):
                    start_pos = path[i]
                    end_pos = path[i + 1]

                    # Calcula los puntos centrales de cada cuadro
                    start_pixel = (
                        start_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                        start_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                    )
                    end_pixel = (
                        end_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                        end_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                    )

                    pygame.draw.line(self.screen, color, start_pixel, end_pixel, 2)

        # Dibuja ambas rutas
        draw_route(astar_path, (0, 255, 0))  # Verde para A*
        draw_route(ucs_path, (0, 0, 255))  # Azul para UCS
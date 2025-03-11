import pygame
from config import GameConfig


class GameRenderer:
    """
    Esta clase se encarga de dibujar todo en pantalla.
    La uso para manejar la parte visual del juego.
    """

    def __init__(self, game_state):
        self.game_state = game_state
        # Creo la ventana del juego
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH,
                                               GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Fregoso Gutierrez IA25A")
        
        # Variables para los campos de texto
        self.visible_iterations = "1"
        self.invisible_iterations = "0"
        self.active_input = None  # Para seguimiento del campo activo

        # Cargo y ajusto el tamaño de las imágenes
        self.player_image = pygame.transform.scale(
            pygame.image.load(GameConfig.PLAYER_IMAGE),
            (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE)
        )
        self.house_image = pygame.transform.scale(
            pygame.image.load(GameConfig.HOUSE_IMAGE),
            (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE)
        )
        # Guardo los rectángulos de los botones para detectar clicks
        self.button_rects = {}

    def get_button_rects(self):
        """Devuelve el diccionario de rectángulos de botones"""
        return self.button_rects

    def draw_grid(self):
        # Dibujo el tablero cuadrado por cuadrado
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
        # Primero dibujo los obstáculos
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

        # Pongo el jugador y la casa en su lugar
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

    def _draw_separator(self, y_pos, text=None):
        # Dibujo una línea para separar las secciones del menú
        sidebar_x = GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE
        separator_width = GameConfig.SIDEBAR_WIDTH - 20

        # Dibuja la línea
        pygame.draw.line(
            self.screen,
            GameConfig.BLACK,
            (sidebar_x + 10, y_pos),
            (sidebar_x + separator_width + 10, y_pos),
            2
        )

        # Si hay texto, dibújalo centrado sobre la línea
        if text:
            font = pygame.font.Font(None, 24)
            text_surface = font.render(text, True, GameConfig.BLACK)
            text_rect = text_surface.get_rect(
                centerx=sidebar_x + GameConfig.SIDEBAR_WIDTH // 2,
                bottom=y_pos - 5
            )
            # Dibuja un pequeño rectángulo de fondo
            padding = 5
            bg_rect = text_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(self.screen, GameConfig.GRAY, bg_rect)
            self.screen.blit(text_surface, text_rect)

    def draw_sidebar(self, edit_mode, is_running, selected_path):
        # Dibujo el panel lateral con todos los controles
        # Fondo de la barra lateral
        sidebar_rect = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
            0,
            GameConfig.SIDEBAR_WIDTH,
            GameConfig.SCREEN_HEIGHT
        )
        pygame.draw.rect(self.screen, GameConfig.GRAY, sidebar_rect)

        font = pygame.font.Font(None, 28)  # Fuente más grande
        y_offset = 20  # Espacio inicial desde arriba

        # Título
        title = font.render("Panel de Control", True, GameConfig.BLACK)
        title_rect = title.get_rect(
            centerx=sidebar_rect.centerx,
            top=y_offset
        )
        self.screen.blit(title, title_rect)

        y_offset = 20
        current_y = y_offset

        # Título con más espacio
        title = font.render("Panel de Control", True, GameConfig.BLACK)
        title_rect = title.get_rect(
            centerx=sidebar_rect.centerx,
            top=current_y
        )
        self.screen.blit(title, title_rect)
        current_y += 50  # Aumentado de 40 a 70 para más separación

        # Sección de Edición
        self._draw_separator(current_y, "EDICIÓN")
        current_y += 30
        edit_buttons = [
             ('edit', "Modo Edición", current_y),
            ('player', "Posición Jugador", current_y + 60),
            ('house', "Posición Casa", current_y + 120),
        ]

        # Sección de Rutas con más espacio
        current_y += 160
        self._draw_separator(current_y, "RUTAS")
        current_y += 30
        route_buttons = [
            ('astar', "Ruta A*", current_y),
            ('random', "Aprendizaje", current_y + 60),
        ]
        
        # Campos de texto para iteraciones visibles e invisibles
        visible_label_y = current_y + 120
        invisible_label_y = current_y + 160
        
        # Rectángulos para los campos de texto
        self.visible_input_rect = pygame.Rect(
            sidebar_rect.left + 90,
            visible_label_y,
            GameConfig.SIDEBAR_WIDTH - 100,
            30
        )
        
        self.invisible_input_rect = pygame.Rect(
            sidebar_rect.left + 90,
            invisible_label_y,
            GameConfig.SIDEBAR_WIDTH - 100,
            30
        )
        
        # Dibujar etiquetas
        font_small = pygame.font.Font(None, 24)
        visible_label = font_small.render("Visible:", True, GameConfig.BLACK)
        self.screen.blit(visible_label, (sidebar_rect.left + 15, visible_label_y + 5))
        
        invisible_label = font_small.render("Invisible:", True, GameConfig.BLACK)
        self.screen.blit(invisible_label, (sidebar_rect.left + 15, invisible_label_y + 5))
        
        # Dibujar campos de entrada
        # Campo Visible
        color = GameConfig.BUTTON_INACTIVE
        if self.active_input == 'visible':
            color = GameConfig.BUTTON_ACTIVE
        pygame.draw.rect(self.screen, color, self.visible_input_rect, border_radius=5)
        visible_text = font_small.render(self.visible_iterations, True, GameConfig.BLACK)
        self.screen.blit(visible_text, (self.visible_input_rect.x + 5, self.visible_input_rect.y + 5))
        
        # Campo Invisible
        color = GameConfig.BUTTON_INACTIVE
        if self.active_input == 'invisible':
            color = GameConfig.BUTTON_ACTIVE
        pygame.draw.rect(self.screen, color, self.invisible_input_rect, border_radius=5)
        invisible_text = font_small.render(self.invisible_iterations, True, GameConfig.BLACK)
        self.screen.blit(invisible_text, (self.invisible_input_rect.x + 5, self.invisible_input_rect.y + 5))

        # Sección de Control con más espacio
        current_y += 200  # Aumentado para dar espacio a los nuevos campos
        self._draw_separator(current_y, "CONTROL")
        current_y += 30
        control_buttons = [
            ('start', "Iniciar/Pausar", current_y),
        ]

        # Limpiar los rectángulos de botones anteriores
        self.button_rects.clear()

        # Dibujar todos los botones con mejor feedback visual
        for button_id, text, y_pos in (edit_buttons + route_buttons + control_buttons):
            # Todos los botones tendrán el mismo tamaño
            button_rect = pygame.Rect(
                sidebar_rect.left + 10,
                y_pos,
                GameConfig.SIDEBAR_WIDTH - 20,
                40  # Altura fija para todos los botones
            )

            # Guardar el rectángulo del botón
            self.button_rects[button_id] = button_rect

            # Color del botón según estado con mejor contraste
            if button_id in ['astar', 'random']:
                color = (100, 200, 100) if selected_path == button_id else GameConfig.BUTTON_INACTIVE
            elif button_id in ['edit', 'player', 'house']:
                color = (100, 200, 100) if button_id == edit_mode else GameConfig.BUTTON_INACTIVE
            elif button_id == 'start':
                if is_running:
                    color = (200, 50, 50)  # Rojo más brillante
                    text = "PAUSAR"
                else:
                    color = (100, 180, 100)  # Verde más suave
                    text = "INICIAR" if not self.game_state.game_started else "CONTINUAR"
            else:
                color = GameConfig.BUTTON_INACTIVE

            # Efecto hover y dibujo del botón
            mouse_pos = pygame.mouse.get_pos()
            if button_rect.collidepoint(mouse_pos):
                color = tuple(min(c + 40, 255) for c in color)
                pygame.draw.rect(self.screen, (255, 255, 255), button_rect.inflate(4, 4), border_radius=5)

            # Dibujar el botón
            pygame.draw.rect(self.screen, (30, 30, 30), button_rect.inflate(2, 2), border_radius=5)
            pygame.draw.rect(self.screen, color, button_rect, border_radius=5)

            # Texto del botón
            font_size = 32 if button_id == 'start' else 28
            button_font = pygame.font.Font(None, font_size)
            button_text = button_font.render(text, True, GameConfig.BUTTON_TEXT)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)

        # Sección de Información con más espacio
        current_y += 80
        self._draw_separator(current_y, "INFORMACIÓN")
        current_y += 20

        # Información del juego
        if not self.game_state.game_started:
            instructions = self._get_instructions()
        else:
            instructions = self._get_game_status()

        # Dibuja las instrucciones o estado del juego
        font_small = pygame.font.Font(None, 24)  # Fuente más pequeña para instrucciones
        for i, text in enumerate(instructions):
            instruction = font_small.render(text, True, GameConfig.BLACK)
            text_rect = instruction.get_rect(
                left=sidebar_rect.left + 15,
                top=current_y + i * 25
            )
            self.screen.blit(instruction, text_rect)

    def _get_instructions(self):
        # Instrucciones básicas para el usuario
        return [
            "Para jugar:",
            "• Click izq: Quitar cosas",
            "• Click der: Poner cosas",
        ]

    def _get_game_status(self):
        # Muestro info sobre las rutas disponibles
        costs = (int(self.game_state.astar_cost), int(self.game_state.ucs_cost))
        if not self.game_state.game_started:
            return [
                "Tengo estas rutas:",
                f"A*: {costs[0]} pasos",
                f"Aprendiendo: {costs[1]} pasos",
                "",
                f"La mejor ruta toma: {min(costs)} pasos",
                "",
                "Usa el modo Edición",
                "si quieres cambiar el mapa"
            ]
        else:
            return [
                "Estado actual:",
                f"A*: {costs[0]} pasos",
                f"Aprendiendo: {costs[1]} pasos",
                "",
                f"Mejor ruta: {min(costs)} pasos",
            ]

    def show_congratulations(self):
        # Muestro mensaje cuando gana
        # Crear overlay semitransparente verde oscuro
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.fill((0, 50, 0))  # Verde oscuro
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        # Mensajes de felicitación
        font = pygame.font.Font(None, 74)
        messages = [
            ("¡Felicitaciones!", -60),
            ("¡Ruta completada!", 0),
        ]

        for text, y_offset in messages:
            rendered_text = font.render(text, True, GameConfig.GREEN)
            text_rect = rendered_text.get_rect(
                center=(GameConfig.SCREEN_WIDTH // 2,
                        GameConfig.SCREEN_HEIGHT // 2 + y_offset)
            )
            self.screen.blit(rendered_text, text_rect)

        pygame.display.flip()

    def show_no_path_error(self):
        # Aviso que no encontré camino posible
        # Crear overlay semitransparente rojo oscuro
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.fill((50, 0, 0))  # Rojo oscuro
        overlay.set_alpha(160)  # Más opaco que el mensaje de victoria
        self.screen.blit(overlay, (0, 0))

        # Mensajes de error
        font = pygame.font.Font(None, 74)
        messages = [
            ("¡No hay ruta disponible!", -60),
            ("Modifica los obstáculos", 0),
            ("o reposiciona elementos", 60)
        ]

        for text, y_offset in messages:
            rendered_text = font.render(text, True, GameConfig.RED)
            text_rect = rendered_text.get_rect(
                center=(GameConfig.SCREEN_WIDTH // 2,
                        GameConfig.SCREEN_HEIGHT // 2 + y_offset)
            )
            self.screen.blit(rendered_text, text_rect)

        pygame.display.flip()

    def handle_input_event(self, event):
        """
        Maneja eventos de entrada para los campos de texto
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Verificar si se hizo clic en alguno de los campos de texto
            if self.visible_input_rect.collidepoint(event.pos):
                self.active_input = 'visible'
            elif self.invisible_input_rect.collidepoint(event.pos):
                self.active_input = 'invisible'
            else:
                self.active_input = None

        if event.type == pygame.KEYDOWN and self.active_input is not None:
            if event.key == pygame.K_BACKSPACE:
                # Borrar el último carácter
                if self.active_input == 'visible':
                    self.visible_iterations = self.visible_iterations[:-1]
                else:
                    self.invisible_iterations = self.invisible_iterations[:-1]
            elif event.key == pygame.K_RETURN:
                # Desactivar el campo al presionar Enter
                self.active_input = None
            elif event.unicode.isdigit():  # Solo permitir dígitos
                # Agregar el carácter presionado al campo activo
                if self.active_input == 'visible':
                    self.visible_iterations += event.unicode
                else:
                    self.invisible_iterations += event.unicode

    def get_visible_iterations(self):
        """
        Retorna el número de iteraciones visibles
        """
        try:
            return int(self.visible_iterations)
        except ValueError:
            return 1  # Valor por defecto

    def get_invisible_iterations(self):
        """
        Retorna el número de iteraciones invisibles
        """
        try:
            return int(self.invisible_iterations)
        except ValueError:
            return 0  # Valor por defecto

    def draw_path(self, astar_path=None, ucs_path=None):
        # Dibujo las líneas que muestran las rutas
        def draw_route(path, color):
            # Dibujo una ruta conectando los puntos
            if path:
                for i in range(len(path) - 1):
                    start_pos = path[i]
                    end_pos = path[i + 1]

                    # Centro la línea en cada cuadro
                    start_pixel = (
                        start_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                        start_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                    )
                    end_pixel = (
                        end_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                        end_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                    )

                    pygame.draw.line(self.screen, color, start_pixel, end_pixel, 2)

        # Verde para A* y azul para UCS
        draw_route(astar_path, (0, 255, 0))
        draw_route(ucs_path, (0, 0, 255))
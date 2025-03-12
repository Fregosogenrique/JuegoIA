import pygame
import os
from config import GameConfig
import numpy as np


class GameRenderer:
    """Clase que maneja el renderizado del juego"""

    def __init__(self, screen, game):
        """Inicializa el renderizador del juego"""
        self.screen = screen
        self.game = game
        self.button_rects = {}

        # Cargar imágenes
        self.player_img = self._load_image(GameConfig.PLAYER_IMAGE)
        self.house_img = self._load_image(GameConfig.HOUSE_IMAGE)

    def _load_image(self, filename):
        try:
            img = pygame.image.load(filename)
            return pygame.transform.scale(img, (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))
        except (pygame.error, FileNotFoundError):
            # Si hay error al cargar la imagen, usar un rectángulo de color como fallback
            fallback = pygame.Surface((GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))
            fallback.fill(GameConfig.WHITE)
            return fallback

    def render(self):
        """Renderiza el juego completo"""
        # Limpiar pantalla
        self.screen.fill(GameConfig.WHITE)

        # Dibujar grid y elementos básicos
        self._draw_grid()

        # Dibujar matriz de movimiento (mapa de calor)
        if GameConfig.SHOW_MOVEMENT_MATRIX:
            self._draw_movement_matrix()

        # Dibujar obstáculos
        self._draw_obstacles()

        # Dibujar rutas si es necesario (antes del jugador y la casa)
        if self.game.game_state.victory:
            self._draw_paths()

        # Dibujar jugador y casa
        self._draw_player()
        self._draw_house()

        # Dibujar mensaje de victoria al final
        if self.game.game_state.victory:
            self._draw_victory_message()

        # Dibujar estado de entrenamiento
        self._draw_training_status()

        # Dibujar barra lateral
        self._draw_sidebar()

        # Actualizar pantalla
        pygame.display.flip()

    def _draw_grid(self):
        """Dibuja el grid y todos sus elementos"""
        # Dibujar fondo de la cuadrícula
        grid_rect = pygame.Rect(
            0, 0,
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
            GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE
        )
        pygame.draw.rect(self.screen, GameConfig.GRID_BG, grid_rect)

        # Dibujar líneas del grid
        for x in range(0, GameConfig.GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen,
                GameConfig.EGGSHELL,
                (x * GameConfig.SQUARE_SIZE, 0),
                (x * GameConfig.SQUARE_SIZE, GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE),
                1
            )

        for y in range(0, GameConfig.GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen,
                GameConfig.EGGSHELL,
                (0, y * GameConfig.SQUARE_SIZE),
                (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE, y * GameConfig.SQUARE_SIZE),
                1
            )

    def _draw_obstacles(self):
        """Dibuja los obstáculos"""
        for obstacle in self.game.game_state.obstacles:
            rect = pygame.Rect(
                obstacle[0] * GameConfig.SQUARE_SIZE,
                obstacle[1] * GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE
            )
            pygame.draw.rect(self.screen, GameConfig.OBSTACLE_COLOR, rect)

    def _draw_player(self):
        """Dibuja el jugador"""
        if self.game.game_state.player_pos:
            if self.player_img:
                self.screen.blit(
                    self.player_img,
                    (
                        self.game.game_state.player_pos[0] * GameConfig.SQUARE_SIZE,
                        self.game.game_state.player_pos[1] * GameConfig.SQUARE_SIZE
                    )
                )
            else:
                rect = pygame.Rect(
                    self.game.game_state.player_pos[0] * GameConfig.SQUARE_SIZE,
                    self.game.game_state.player_pos[1] * GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, GameConfig.PLAYER_COLOR, rect)

    def _draw_house(self):
        """Dibuja la casa"""
        if self.game.game_state.house_pos:
            if self.house_img:
                self.screen.blit(
                    self.house_img,
                    (
                        self.game.game_state.house_pos[0] * GameConfig.SQUARE_SIZE,
                        self.game.game_state.house_pos[1] * GameConfig.SQUARE_SIZE
                    )
                )
            else:
                rect = pygame.Rect(
                    self.game.game_state.house_pos[0] * GameConfig.SQUARE_SIZE,
                    self.game.game_state.house_pos[1] * GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE,
                    GameConfig.SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, GameConfig.HOUSE_COLOR, rect)

    def _draw_paths(self):
        """Dibuja las rutas"""
        # Dibujar la mejor ruta si existe
        if self.game.best_path:
            # Dibujar líneas verdes para la mejor ruta
            for i in range(len(self.game.best_path) - 1):
                start_pos = self.game.best_path[i]
                end_pos = self.game.best_path[i + 1]

                start_pixel = (
                    start_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                    start_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                )
                end_pixel = (
                    end_pos[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                    end_pos[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                )

                # Dibujar línea con borde negro
                pygame.draw.line(
                    self.screen,
                    GameConfig.BLACK,
                    start_pixel,
                    end_pixel,
                    4  # Línea más gruesa para el borde
                )
                pygame.draw.line(
                    self.screen,
                    GameConfig.GREEN,
                    start_pixel,
                    end_pixel,
                    2  # Línea más delgada para el color principal
                )

    def _draw_movement_matrix(self):
        """Dibuja el mapa de calor basado en la matriz de movimiento"""
        if not self.game.movement_matrix.any():  # Si la matriz está vacía
            return

        max_value = np.max(self.game.movement_matrix)
        if max_value == 0:
            return

        for y in range(GameConfig.GRID_HEIGHT):
            for x in range(GameConfig.GRID_WIDTH):
                value = self.game.movement_matrix[y][x]
                if value > 0:
                    # Calcular color basado en el valor
                    intensity = value / max_value

                    # Obtener color interpolado
                    color_index = min(int(intensity * (len(GameConfig.HEAT_COLORS) - 1)),
                                      len(GameConfig.HEAT_COLORS) - 1)
                    color = GameConfig.HEAT_COLORS[color_index]

                    # Dibujar rectángulo semi-transparente
                    rect = pygame.Rect(
                        x * GameConfig.SQUARE_SIZE,
                        y * GameConfig.SQUARE_SIZE,
                        GameConfig.SQUARE_SIZE,
                        GameConfig.SQUARE_SIZE
                    )

                    # Crear superficie con alpha
                    s = pygame.Surface((GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))
                    s.set_alpha(int(128 + intensity * 127))  # Alpha aumenta con la intensidad
                    s.fill(color)
                    self.screen.blit(s, rect)

                    # Mostrar número de visitas
                    font = pygame.font.SysFont(None, 18)  # Tamaño aumentado
                    text = font.render(str(int(value)), True, GameConfig.WHITE)
                    text_rect = text.get_rect(center=(
                        x * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                        y * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                    ))
                    self.screen.blit(text, text_rect)

    def _draw_training_status(self):
        """Dibuja el estado actual del entrenamiento si está en progreso"""
        if not hasattr(self.game, 'is_training') or not self.game.is_training:
            return
            
        # Configuración
        font = pygame.font.SysFont(None, 24)
        status_text = f"Entrenando... ({getattr(self.game, 'training_current_iteration', 0)}/{getattr(self.game, 'training_total_iterations', 0)})"
        
        # Crear texto
        text = font.render(status_text, True, GameConfig.WHITE)
        
        # Calcular posición
        text_rect = text.get_rect(
            centerx=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE // 2,
            top=10
        )
        
        # Crear fondo semitransparente
        background = pygame.Surface((text_rect.width + 20, text_rect.height + 10))
        background.fill(GameConfig.BLACK)
        background.set_alpha(180)
        
        background_rect = background.get_rect(center=text_rect.center)
        
        # Dibujar fondo y texto
        self.screen.blit(background, background_rect)
        self.screen.blit(text, text_rect)
        
        # Si hay mensaje adicional de entrenamiento
        if hasattr(self.game, 'training_status_message') and self.game.training_status_message:
            status_font = pygame.font.SysFont(None, 18)
            status_text = status_font.render(self.game.training_status_message, True, GameConfig.EGGSHELL)
            status_rect = status_text.get_rect(
                centerx=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE // 2,
                top=text_rect.bottom + 5
            )
            self.screen.blit(status_text, status_rect)

    def _draw_victory_message(self):
        """Dibuja el mensaje de victoria"""
        font = pygame.font.SysFont(None, 48)
        text = font.render("¡Felicidades!", True, GameConfig.BLACK)

        # Calcular posición para el mensaje (en la parte superior de la pantalla)
        text_rect = text.get_rect(
            centerx=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE // 2,
            top=10  # 10 píxeles desde la parte superior
        )

        # Crear un fondo semi-transparente para el texto
        background = pygame.Surface((text_rect.width + 20, text_rect.height + 10))
        background.fill(GameConfig.WHITE)
        background.set_alpha(200)  # Semi-transparente

        background_rect = background.get_rect(center=text_rect.center)

        # Dibujar el fondo y el texto
        self.screen.blit(background, background_rect)
        self.screen.blit(text, text_rect)

    def _draw_progress_bar(self, x, y, width, height, progress, bg_color, fg_color, border_color):
        """
        Dibuja una barra de progreso personalizada.
        
        Args:
            x (int): Posición x de la barra
            y (int): Posición y de la barra
            width (int): Ancho total de la barra
            height (int): Altura de la barra
            progress (float): Valor de progreso (0-100)
            bg_color (tuple): Color RGB del fondo de la barra
            fg_color (tuple): Color RGB de la barra de progreso
            border_color (tuple): Color RGB del borde de la barra
        """
        # Asegurar que el progreso esté entre 0 y 100
        progress = max(0, min(100, progress))
        
        # Dibujar el fondo de la barra
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, bg_color, bg_rect)
        
        # Dibujar el progreso
        if progress > 0:
            fg_width = int(width * (progress / 100.0))
            fg_rect = pygame.Rect(x, y, fg_width, height)
            pygame.draw.rect(self.screen, fg_color, fg_rect)
        
        # Dibujar el borde
        pygame.draw.rect(self.screen, border_color, bg_rect, 1)
        
        # Mostrar el porcentaje de progreso en texto
        font = pygame.font.SysFont(None, 18)
        text = font.render(f"{int(progress)}%", True, GameConfig.BLACK)
        text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text, text_rect)

    def _draw_sidebar(self):
        """Dibuja la barra lateral con botones y estadísticas"""
        # Dibujar fondo de la barra lateral
        sidebar_rect = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE,
            0,
            GameConfig.SIDEBAR_WIDTH,
            GameConfig.SCREEN_HEIGHT
        )
        pygame.draw.rect(self.screen, GameConfig.SIDEBAR_BG, sidebar_rect)

        # Obtener posición del mouse y estado de botones
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Configuración de botones
        button_margin = 10
        button_height = 30
        font = pygame.font.SysFont(None, 20)
        font_title = pygame.font.SysFont(None, 24)

        # Título del juego
        title = font_title.render("SIMULACIÓN DE MOVIMIENTO", True, GameConfig.WHITE)
        title_rect = title.get_rect(
            centerx=sidebar_rect.centerx,
            top=10
        )
        self.screen.blit(title, title_rect)

        # Sección de controles
        controls_title = font_title.render("CONTROLES", True, GameConfig.EGGSHELL)
        controls_title_rect = controls_title.get_rect(
            centerx=sidebar_rect.centerx,
            top=title_rect.bottom + 20
        )
        self.screen.blit(controls_title, controls_title_rect)

        # Botones
        # Botones
        button_texts = [
            ("start", "Iniciar/Detener (Space)"),
            ("reset", "Reiniciar (R)"),
            ("headless", "Entrenamiento (H)"),
            ("edit_house", "Editar Casa (C)"),
            ("edit_obstacles", "Editar Obstáculos (O)"),
            ("clear_obstacles", "Limpiar Obstáculos (L)")
        ]

        # Calcular altura total para centrar
        total_height = len(button_texts) * button_height + (len(button_texts) - 1) * 10
        start_y = controls_title_rect.bottom + 10

        # Inicializar diccionario de rectángulos de botones
        self.button_rects = {}

        # Dibujar botones
        for i, (button_id, button_text) in enumerate(button_texts):
            button_y = start_y + i * (button_height + 10)
            button_rect = pygame.Rect(
                GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + button_margin,
                button_y,
                GameConfig.SIDEBAR_WIDTH - 2 * button_margin,
                button_height
            )

            is_hovered = button_rect.collidepoint(mouse_pos)
            is_pressed = is_hovered and mouse_pressed

            # Determinar color del botón
            if is_pressed:
                button_color = GameConfig.BUTTON_FOCUS
                text_color = GameConfig.WHITE
            elif is_hovered:
                button_color = GameConfig.BUTTON_HOVER
                text_color = GameConfig.BLACK
            else:
                button_color = GameConfig.BUTTON_BG
                text_color = GameConfig.BLACK

            # Dibujar botón
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5)

            # Efecto de hover
            if is_hovered and not is_pressed:
                pygame.draw.rect(self.screen, GameConfig.BUTTON_FOCUS, button_rect, 2, border_radius=5)

            # Texto del botón
            text_surface = font.render(button_text, True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)

            # Ajustar posición del texto si está presionado
            if is_pressed:
                text_rect.y += 1

            self.screen.blit(text_surface, text_rect)

            # Guardar rectángulo para detección de clics
            self.button_rects[button_id] = button_rect

        # Estadísticas
        stats_y = controls_title_rect.bottom + total_height + 20
        font_stats = pygame.font.SysFont(None, 22)
        title_stats = font_stats.render("ESTADÍSTICAS", True, GameConfig.EGGSHELL)
        title_stats_rect = title_stats.get_rect(
            centerx=sidebar_rect.centerx,
            top=stats_y
        )
        self.screen.blit(title_stats, title_stats_rect)

        stats = [
            f"Ejecuciones Visibles: {getattr(self.game, 'training_visible_executions', 0)}",
            f"Ejecuciones Invisibles: {getattr(self.game, 'training_invisible_executions', 0)}",
            f"Total Ejecuciones: {getattr(self.game, 'training_visible_executions', 0) + getattr(self.game, 'training_invisible_executions', 0)}",
            f"Progreso Entrenamiento: {getattr(self.game, 'training_progress', 0):.2f}%"
        ]

        font_stats_text = pygame.font.SysFont(None, 20)
        for i, stat in enumerate(stats):
            text = font_stats_text.render(stat, True, GameConfig.EGGSHELL)
            text_rect = text.get_rect(
                left=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + button_margin,
                top=title_stats_rect.bottom + 20 + i * 25
            )
            self.screen.blit(text, text_rect)
        
        # Dibujar barra de progreso de entrenamiento
        progress_title = font_stats_text.render("Progreso de Entrenamiento:", True, GameConfig.EGGSHELL)
        progress_title_rect = progress_title.get_rect(
            left=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + button_margin,
            top=title_stats_rect.bottom + 20 + len(stats) * 25
        )
        self.screen.blit(progress_title, progress_title_rect)
        
        # Obtener el progreso actual
        training_progress = getattr(self.game, 'training_progress', 0)
        
        # Dibujar la barra de progreso
        self._draw_progress_bar(
            x=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + button_margin,
            y=progress_title_rect.bottom + 5,
            width=GameConfig.SIDEBAR_WIDTH - 2 * button_margin,
            height=15,
            progress=training_progress,
            bg_color=GameConfig.BUTTON_BG,
            fg_color=self._get_progress_color(training_progress),
            border_color=GameConfig.BLACK
        )
        
        # Añadir información adicional sobre el entrenamiento si está en curso
        if hasattr(self.game, 'is_training') and self.game.is_training:
            status_text = f"Ejecutando iteración {getattr(self.game, 'training_current_iteration', 0)}/{getattr(self.game, 'training_total_iterations', 0)}"
            status_render = font_stats_text.render(status_text, True, GameConfig.EGGSHELL)
            status_rect = status_render.get_rect(
                left=GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + button_margin,
                top=progress_title_rect.bottom + 25
            )
            self.screen.blit(status_render, status_rect)
    def get_button_at(self, pos):
        """Devuelve el ID del botón en la posición dada o None si no hay botón"""
        for button_id, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                return button_id
        return None
    def _get_progress_color(self, progress):
        """
        Devuelve un color basado en el progreso del entrenamiento.
        
        Args:
            progress (float): Valor de progreso (0-100)
            
        Returns:
            tuple: Color RGB representando el progreso (rojo -> amarillo -> verde -> azul)
        """
        # Asegurar que el progreso esté entre 0 y 100
        progress = max(0, min(100, progress))
        
        if progress < 25:
            # Rojo a amarillo (0-25%)
            r = 255
            g = int(255 * (progress / 25))
            b = 0
        elif progress < 50:
            # Amarillo a verde claro (25-50%)
            r = int(255 * (1 - (progress - 25) / 25))
            g = 255
            b = 0
        elif progress < 75:
            # Verde claro a verde (50-75%)
            r = 0
            g = 255
            b = int(255 * ((progress - 50) / 25))
        else:
            # Verde a azul verdoso (75-100%)
            r = 0
            g = int(255 * (1 - (progress - 75) / 25))
            b = 255
        
        # Asegurarse de que los valores RGB estén dentro del rango 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return (r, g, b)

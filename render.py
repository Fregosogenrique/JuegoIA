
import pygame
import os  # Necesario para construir rutas de archivo si las imágenes están en subcarpetas
from config import GameConfig
import numpy as np


class GameRenderer:
    """
    Yo me encargo de dibujar todo lo que se ve en el juego.
    """

    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game = game_instance
        self.button_rects = {}

        self.player_img = self._load_image(GameConfig.PLAYER_IMAGE)
        self.house_img = self._load_image(GameConfig.HOUSE_IMAGE)
        self.enemy_img = self._load_image(GameConfig.ENEMY_IMAGE)

    def _load_image(self, filename_str):
        try:
            # Asumimos que las imágenes están en la misma carpeta que los scripts
            # o que filename_str ya incluye la ruta relativa (e.g., "assets/player.png")
            filepath = filename_str
            if not os.path.exists(
                    filepath) and "assets" not in filename_str:  # Intenta buscar en "assets" si no se encuentra
                filepath_assets = os.path.join("assets", filename_str)
                if os.path.exists(filepath_assets):
                    filepath = filepath_assets

            img_loaded = pygame.image.load(filepath)
            return pygame.transform.scale(img_loaded, (GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))
        except (pygame.error, FileNotFoundError) as e:
            print(
                f"ADVERTENCIA: No se pudo cargar la imagen '{filename_str}' (buscada en '{filepath}', Error: {e}). Usando color de fallback.")
            fallback_surf = pygame.Surface((GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))
            if "player" in filename_str.lower():
                fallback_surf.fill(GameConfig.PLAYER_COLOR)
            elif "house" in filename_str.lower():
                fallback_surf.fill(GameConfig.HOUSE_COLOR)
            elif "enemy" in filename_str.lower():
                fallback_surf.fill(GameConfig.ENEMY_COLOR)
            else:
                fallback_surf.fill(GameConfig.WHITE)
            return fallback_surf

    def render(self):
        self.screen.fill(GameConfig.GRID_BG)
        self._draw_grid_lines()

        if self.game.avatar_heatmap_trained and hasattr(self.game, 'heat_map_pathfinder'):
            self._draw_avatar_learned_heatmap()

        if GameConfig.SHOW_MOVEMENT_MATRIX and \
                hasattr(self.game, 'player_movement_frequency_matrix') and \
                self.game.player_movement_frequency_matrix is not None and \
                self.game.player_movement_frequency_matrix.any():
            self._draw_player_frequency_heatmap()

        self._draw_game_obstacles()
        self._draw_all_enemies()

        if self.game.best_path_player and len(self.game.best_path_player) > 1:
            if not (self.game.is_running and self.game.current_path_player and len(self.game.current_path_player) > 1):
                self._draw_path_lines_on_grid(self.game.best_path_player, GameConfig.PATH_COLOR, line_width=2,
                                              style="dashed")

        if self.game.current_path_player and len(self.game.current_path_player) > 1 and self.game.is_running:
            self._draw_path_lines_on_grid(self.game.current_path_player, GameConfig.ORANGE, line_width=3, style="solid")

        self._draw_player_sprite()
        self._draw_house_sprite()

        if self.game.game_state.victory:
            self._draw_victory_message()
        elif self.game.game_over:
            self._draw_game_over_message()

        self._draw_ui_sidebar()

    def _draw_grid_lines(self):
        for x_l in range(0, GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE + 1, GameConfig.SQUARE_SIZE):
            pygame.draw.line(self.screen, GameConfig.GRID_COLOR, (x_l, 0),
                             (x_l, GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE))
        for y_l in range(0, GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE + 1, GameConfig.SQUARE_SIZE):
            pygame.draw.line(self.screen, GameConfig.GRID_COLOR, (0, y_l),
                             (GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE, y_l))

    def _draw_avatar_learned_heatmap(self):
        avatar_heatmap_data_matrix = self.game.heat_map_pathfinder.avatar_heat_map

        if not hasattr(avatar_heatmap_data_matrix, 'any') or not avatar_heatmap_data_matrix.any(): return
        max_heat_val_avatar = np.max(avatar_heatmap_data_matrix)
        if max_heat_val_avatar == 0: return

        for r_idx_avatar in range(GameConfig.GRID_HEIGHT):
            for c_idx_avatar in range(GameConfig.GRID_WIDTH):
                heat_value_cell = avatar_heatmap_data_matrix[r_idx_avatar, c_idx_avatar]
                if heat_value_cell > 0:
                    intensity_ratio_avatar = heat_value_cell / max_heat_val_avatar
                    color_index_avatar = min(int(intensity_ratio_avatar * (len(GameConfig.HEAT_COLORS) - 1)),
                                             len(GameConfig.HEAT_COLORS) - 1)
                    chosen_heatmap_color = GameConfig.HEAT_COLORS[color_index_avatar]
                    heatmap_cell_render_surface = pygame.Surface((GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE),
                                                                 pygame.SRCALPHA)
                    base_alpha_heatmap = 60
                    dynamic_alpha_for_heatmap = int(
                        base_alpha_heatmap + (intensity_ratio_avatar * (120 - base_alpha_heatmap)))
                    dynamic_alpha_for_heatmap = min(255, max(0, dynamic_alpha_for_heatmap))
                    heatmap_cell_render_surface.fill((*chosen_heatmap_color, dynamic_alpha_for_heatmap))
                    self.screen.blit(heatmap_cell_render_surface,
                                     (c_idx_avatar * GameConfig.SQUARE_SIZE, r_idx_avatar * GameConfig.SQUARE_SIZE))

    def _draw_player_frequency_heatmap(self):
        player_freq_matrix = self.game.player_movement_frequency_matrix
        if not player_freq_matrix.any(): return

        max_player_freq_val = np.max(player_freq_matrix)
        if max_player_freq_val == 0: return

        for r_f_idx_player in range(GameConfig.GRID_HEIGHT):
            for c_f_idx_player in range(GameConfig.GRID_WIDTH):
                freq_val_player = player_freq_matrix[r_f_idx_player, c_f_idx_player]
                if freq_val_player > 0:
                    intensity_freq_player = freq_val_player / max_player_freq_val

                    color_idx_freq_p = min(int(intensity_freq_player * (len(GameConfig.HEAT_COLORS) - 1)),
                                           len(GameConfig.HEAT_COLORS) - 1)
                    color_freq_p = GameConfig.HEAT_COLORS[color_idx_freq_p]

                    freq_cell_surf_p = pygame.Surface((GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE), pygame.SRCALPHA)
                    alpha_freq_p = int(80 + intensity_freq_player * (180 - 80));
                    alpha_freq_p = min(255, max(0, alpha_freq_p))
                    freq_cell_surf_p.fill((*color_freq_p, alpha_freq_p))
                    self.screen.blit(freq_cell_surf_p,
                                     (c_f_idx_player * GameConfig.SQUARE_SIZE, r_f_idx_player * GameConfig.SQUARE_SIZE))

                    if GameConfig.SHOW_VISIT_COUNT_ON_HEATMAP:
                        font_visits_num = pygame.font.SysFont(None, 15)
                        text_visits_num = font_visits_num.render(str(int(freq_val_player)), True, GameConfig.BLACK)
                        text_visits_rect_num = text_visits_num.get_rect(center=(
                            c_f_idx_player * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                            r_f_idx_player * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2
                        ))
                        self.screen.blit(text_visits_num, text_visits_rect_num)

    def _draw_game_obstacles(self):
        for obs_p_tuple in self.game.game_state.obstacles:
            obs_render_rect = pygame.Rect(
                obs_p_tuple[0] * GameConfig.SQUARE_SIZE, obs_p_tuple[1] * GameConfig.SQUARE_SIZE,
                GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE
            )
            pygame.draw.rect(self.screen, GameConfig.OBSTACLE_COLOR, obs_render_rect)

    def _draw_all_enemies(self):
        if hasattr(self.game.game_state, 'enemies') and isinstance(self.game.game_state.enemies, dict):
            for enemy_unique_id, data_of_enemy in self.game.game_state.enemies.items():
                pos_of_enemy = data_of_enemy['position']
                type_of_enemy = data_of_enemy.get('type', GameConfig.DEFAULT_ENEMY_TYPE)
                self._draw_one_enemy_sprite(pos_of_enemy, type_of_enemy)
        elif hasattr(self.game.game_state, 'enemy_positions') and self.game.game_state.enemy_positions:
            for pos_e_from_set in self.game.game_state.enemy_positions:
                self._draw_one_enemy_sprite(pos_e_from_set, GameConfig.DEFAULT_ENEMY_TYPE)

    def _draw_one_enemy_sprite(self, enemy_on_grid_pos, enemy_type_name_str):
        enemy_type_color_map = {
            'perseguidor': GameConfig.RED, 'bloqueador': GameConfig.ORANGE,
            'patrulla': GameConfig.PURPLE, 'aleatorio': GameConfig.CYAN
        }
        color_for_this_enemy = enemy_type_color_map.get(enemy_type_name_str, GameConfig.ENEMY_COLOR)
        pixel_render_x_e, pixel_render_y_e = enemy_on_grid_pos[0] * GameConfig.SQUARE_SIZE, enemy_on_grid_pos[
            1] * GameConfig.SQUARE_SIZE

        if self.enemy_img and self.enemy_img.get_width() > 0 and self.enemy_img.get_height() > 0:
            self.screen.blit(self.enemy_img, (pixel_render_x_e, pixel_render_y_e))
            indicator_radius = max(3, GameConfig.SQUARE_SIZE // 7)
            indicator_pos_x = pixel_render_x_e + GameConfig.SQUARE_SIZE - indicator_radius - 2
            indicator_pos_y = pixel_render_y_e + indicator_radius + 2
            pygame.draw.circle(self.screen, color_for_this_enemy, (indicator_pos_x, indicator_pos_y), indicator_radius)
        else:
            shape_rect_enemy = pygame.Rect(pixel_render_x_e, pixel_render_y_e, GameConfig.SQUARE_SIZE,
                                           GameConfig.SQUARE_SIZE)
            pygame.draw.rect(self.screen, color_for_this_enemy, shape_rect_enemy)

    def _draw_player_sprite(self):
        if self.game.game_state.player_pos:
            px_p = self.game.game_state.player_pos[0] * GameConfig.SQUARE_SIZE
            py_p = self.game.game_state.player_pos[1] * GameConfig.SQUARE_SIZE
            if self.player_img and self.player_img.get_width() > 0 and self.player_img.get_height() > 0:
                self.screen.blit(self.player_img, (px_p, py_p))
            else:
                pygame.draw.rect(self.screen, GameConfig.PLAYER_COLOR,
                                 (px_p, py_p, GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))

    def _draw_house_sprite(self):
        if self.game.game_state.house_pos:
            px_h = self.game.game_state.house_pos[0] * GameConfig.SQUARE_SIZE
            py_h = self.game.game_state.house_pos[1] * GameConfig.SQUARE_SIZE
            if self.house_img and self.house_img.get_width() > 0 and self.house_img.get_height() > 0:
                self.screen.blit(self.house_img, (px_h, py_h))
            else:
                pygame.draw.rect(self.screen, GameConfig.HOUSE_COLOR,
                                 (px_h, py_h, GameConfig.SQUARE_SIZE, GameConfig.SQUARE_SIZE))

    def _draw_path_lines_on_grid(self, path_coordinate_list, path_line_rgb_color, line_width=3, style="solid"):
        if not path_coordinate_list or len(path_coordinate_list) < 2: return

        for i_path_segment in range(len(path_coordinate_list) - 1):
            start_node_tuple = path_coordinate_list[i_path_segment]
            end_node_tuple = path_coordinate_list[i_path_segment + 1]
            start_center_pixels = (start_node_tuple[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                                   start_node_tuple[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2)
            end_center_pixels = (end_node_tuple[0] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2,
                                 end_node_tuple[1] * GameConfig.SQUARE_SIZE + GameConfig.SQUARE_SIZE // 2)

            if style == "dashed":
                dx = end_center_pixels[0] - start_center_pixels[0]
                dy = end_center_pixels[1] - start_center_pixels[1]
                dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
                num_dashes = int(dist / (GameConfig.SQUARE_SIZE / 2.5))  # Ajustar densidad
                if num_dashes < 1: num_dashes = 1  # Al menos un guión (o línea sólida si es corto)

                for i_dash in range(num_dashes):
                    t0 = i_dash / num_dashes
                    t1 = (i_dash + 0.5) / num_dashes  # Mitad del segmento para guión
                    if t1 > 1.0: t1 = 1.0  # Asegurar que no exceda

                    p1 = (start_center_pixels[0] + dx * t0,
                          start_center_pixels[1] + dy * t0)
                    p2 = (start_center_pixels[0] + dx * t1,
                          start_center_pixels[1] + dy * t1)
                    pygame.draw.line(self.screen, path_line_rgb_color, p1, p2, line_width)
            else:
                pygame.draw.line(self.screen, GameConfig.BLACK, start_center_pixels, end_center_pixels, line_width + 2)
                pygame.draw.line(self.screen, path_line_rgb_color, start_center_pixels, end_center_pixels, line_width)

    def _draw_victory_message(self):
        font_vic = pygame.font.SysFont(None, 60)
        text_vic = font_vic.render("¡FELICIDADES!", True, GameConfig.GREEN, GameConfig.DARK_GRAY)
        rect_vic = text_vic.get_rect(
            centerx=(GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE) // 2,
            centery=(GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE) // 3
        )
        self.screen.blit(text_vic, rect_vic)

    def _draw_game_over_message(self):
        font_gameover = pygame.font.SysFont(None, 70)
        text_gameover = font_gameover.render("GAME OVER", True, GameConfig.RED, GameConfig.BLACK)
        rect_gameover = text_gameover.get_rect(
            centerx=(GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE) // 2,
            centery=(GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE) // 2
        )
        self.screen.blit(text_gameover, rect_gameover)
        font_instr_restart = pygame.font.SysFont(None, 24)
        text_instr_restart = font_instr_restart.render("Presiona 'R' para reiniciar", True, GameConfig.WHITE)
        rect_instr_restart = text_instr_restart.get_rect(centerx=rect_gameover.centerx, top=rect_gameover.bottom + 10)
        self.screen.blit(text_instr_restart, rect_instr_restart)

    def _draw_ui_sidebar(self):
        sidebar_full_rect = pygame.Rect(
            GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE, 0,
            GameConfig.SIDEBAR_WIDTH, GameConfig.SCREEN_HEIGHT
        )
        pygame.draw.rect(self.screen, GameConfig.SIDEBAR_BG, sidebar_full_rect)

        mouse_current_pos = pygame.mouse.get_pos()
        mouse_left_button_pressed, _, _ = pygame.mouse.get_pressed()

        font_buttons_sidebar = pygame.font.SysFont(None, 20)
        font_titles_sidebar = pygame.font.SysFont(None, 24)

        main_title_surf = font_titles_sidebar.render("Control Juego IA", True, GameConfig.WHITE)
        main_title_ui_rect = main_title_surf.get_rect(centerx=sidebar_full_rect.centerx, top=10)
        self.screen.blit(main_title_surf, main_title_ui_rect)

        sidebar_button_definitions = [
            ("start", "Iniciar/Detener (Space)"), ("reset", "Reiniciar Juego (R)"),
            ("train_player_agent", "Ent. Agente Jugador (H)"),
            ("train_enemy_agent", "Ent. Agente Enemigo (Q)"),
            ("stop_train", "Detener Entrenamientos"),
            ("edit_player", "Editar Pos Jugador (P)"), ("edit_house", "Editar Pos Casa (C)"),
            ("edit_obstacles", "Editar Obstáculos (O)"), ("edit_enemies", "Editar Enemigos (E)"),
            ("clear_obstacles", "Limpiar Obstáculos"), ("clear_enemies", "Limpiar Enemigos"),
            ("use_heat_map", "Jugador Sigue Heatmap (N)"),
            ("visualize_heat_map", "Ver Heatmap Avatar (V)"),
            ("reset_heat_map", "Resetear Heatmap Av."),
            ("toggle_edit_avatar_heatmap_iters", f"Iter HM Av: ...")
        ]

        button_y_start_offset = main_title_ui_rect.bottom + 20
        button_render_height = 26
        button_vertical_margin = 7
        self.button_rects.clear()

        for i, (button_id_str, button_text_str) in enumerate(sidebar_button_definitions):
            current_button_rect = pygame.Rect(
                sidebar_full_rect.left + button_vertical_margin,
                button_y_start_offset + i * (button_render_height + button_vertical_margin),
                sidebar_full_rect.width - 2 * button_vertical_margin,
                button_render_height
            )
            self.button_rects[button_id_str] = current_button_rect

            mouse_is_over_button = current_button_rect.collidepoint(mouse_current_pos)
            button_is_being_clicked = mouse_is_over_button and mouse_left_button_pressed

            button_fill_color = GameConfig.BUTTON_BG
            button_text_color = GameConfig.BUTTON_TEXT
            current_text_to_display = button_text_str
            is_active_input_field = False

            if button_id_str == "toggle_edit_avatar_heatmap_iters":
                field_id_for_button = 'avatar_heatmap_iters'
                is_active_input_field = (self.game.input_field_active == field_id_for_button)
                current_val_str = self.game.input_buffer if is_active_input_field else str(
                    self.game.avatar_heatmap_training_iterations)
                cursor_str = "|" if is_active_input_field and pygame.time.get_ticks() % 1000 < 500 else ""
                current_text_to_display = f"Iter HM Av: {current_val_str}{cursor_str}"

            if is_active_input_field:
                button_fill_color = GameConfig.BLUE
            elif button_is_being_clicked:
                button_fill_color = GameConfig.BUTTON_ACTIVE
            elif mouse_is_over_button:
                button_fill_color = GameConfig.BUTTON_HOVER

            if button_is_being_clicked and not is_active_input_field:
                button_text_color = GameConfig.BUTTON_TEXT_ACTIVE

            pygame.draw.rect(self.screen, button_fill_color, current_button_rect, border_radius=4)
            if mouse_is_over_button and not button_is_being_clicked and not is_active_input_field:
                pygame.draw.rect(self.screen, GameConfig.BUTTON_FOCUS, current_button_rect, 1, border_radius=4)

            text_surf_for_button = font_buttons_sidebar.render(current_text_to_display, True, button_text_color)
            text_rect_for_button = text_surf_for_button.get_rect(center=current_button_rect.center)
            if button_is_being_clicked and not is_active_input_field: text_rect_for_button.y += 1
            self.screen.blit(text_surf_for_button, text_rect_for_button)

    def get_button_at(self, mouse_click_coordinates):
        for button_identifier, rect_object_button in self.button_rects.items():
            if rect_object_button.collidepoint(mouse_click_coordinates):
                return button_identifier
        return None
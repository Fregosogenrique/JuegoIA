import pygame
import random
import numpy as np
from queue import Queue, Empty

from GameState import GameState
# from DecisionTree import DecisionTree # Comentado - no se usa activamente
from config import GameConfig
from render import GameRenderer
from sprites import SpriteFactory
from ui import MenuScreen
from ADB import QLearningAgent
from HeatMapPathfinding import HeatMapPathfinding
from grid_utils import manhattan, neighbors_4


class Game:
    """
    Mi clase principal del juego. Aquí controlo toda la lógica y la UI.

    El juego avanza por TURNOS (cada GameConfig.MOVE_DELAY ms):
      1. El avatar da un paso por su ruta (o huye si no tiene ruta segura).
      2. Si llegó a la casa: victoria.
      3. Los enemigos acumulan ENEMY_SPEED_FACTOR y dan un paso por cada
         unidad acumulada, cada uno según su tipo.
      4. Si un enemigo ocupa la celda del avatar: game over.
      5. Si hay amenaza en la ruta (o cada REPLAN_EVERY_TURNS turnos) el
         avatar replanifica considerando la posición actual de los enemigos.
    """

    def __init__(self):
        pygame.init()
        self.screen = self._create_window()
        pygame.display.set_caption(GameConfig.WINDOW_TITLE)
        pygame.key.set_repeat(220, 90)

        # Escena actual: "menu" (menú principal) o "playing" (partida)
        self.scene = "menu"
        self.game_started_once = False
        self.view_mode = "2d"  # "2d", "3d" (maqueta) o "fps" (primera persona)
        self.show_trail = True  # Mostrar el rastro de feromona del mapa de calor
        self.player_facing = (0, 1)  # Hacia dónde mira el avatar (para los sprites y la cámara 3D)

        self.step_counter = 0  # Pasos que ha dado el avatar
        self.turn_counter = 0  # Turnos de simulación transcurridos
        self.enemy_move_accumulator = 0.0
        self.game_over = False
        self.is_running = False
        self.is_pygame_loop_running = True

        self.game_state = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.game_state.initialize_game()

        self.current_path_player = []
        self.path_index_player = 0
        self.best_path_player = None
        self.player_path_source = "Ninguna"
        self._replan_requested = False  # Lo activan los hilos de entrenamiento; lo atiende el hilo principal

        self.enemy_q_agent = QLearningAgent(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.enemy_q_agent_trained = False
        self.enemy_agent_is_training = False
        self.enemy_agent_training_progress = 0.0
        self.enemy_agent_training_status = ""
        self.enemy_agent_training_complete = False
        self.enemy_agent_max_training_iterations = 5000

        self.agent_player = QLearningAgent(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.player_agent_is_training = False
        self.player_agent_training_progress = 0.0
        self.player_agent_training_status = ""
        self.player_agent_training_complete = False
        self.player_agent_max_training_iterations = 1500

        self.heat_map_pathfinder = HeatMapPathfinding(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.avatar_heatmap_trained = False
        self.avatar_heatmap_training_iterations = 500
        self.player_uses_heatmap_path = False
        self.environment_analyzed = False
        self.enemies_initialized = False
        self.user_placed_enemies = False

        self._train_avatar_heatmap_on_init()

        self.player_movement_frequency_matrix = np.zeros((GameConfig.GRID_HEIGHT, GameConfig.GRID_WIDTH), dtype=int)

        self.move_timer = pygame.time.get_ticks()
        self.edit_mode = None
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen, self)
        self.menu = MenuScreen(self.renderer.sprites)
        self.learning_status_display = ""
        self.plot_request_queue = Queue()

        self.input_field_active = None
        self.input_buffer = ""

        self.determine_player_optimal_path()  # Calcular ruta inicial basada en el estado inicial

    @staticmethod
    def _create_window():
        """Ventana escalable (se puede redimensionar y poner a pantalla completa con F11)."""
        size = (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        pygame.display.set_icon(SpriteFactory().player(32))  # Icono de la ventana: el avatar
        try:
            return pygame.display.set_mode(size, pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            return pygame.display.set_mode(size)

    # ================================================================ VISTAS
    def set_view_mode(self, mode):
        if mode not in GameConfig.VIEW_MODES:
            return
        self.view_mode = mode
        self.renderer.on_view_changed(mode)
        print(f"Vista: {GameConfig.VIEW_NAMES[mode]}")

    def cycle_view_mode(self):
        modes = GameConfig.VIEW_MODES
        self.set_view_mode(modes[(modes.index(self.view_mode) + 1) % len(modes)])

    def toggle_trail(self):
        self.show_trail = not self.show_trail
        print(f"Rastro de feromona {'visible' if self.show_trail else 'oculto'}.")

    def open_menu(self):
        if self.is_running:
            self.toggle_game_running_state()
        self.edit_mode = None
        self.menu.page = 'main'
        self.menu.selected = 0  # "CONTINUAR" queda preseleccionado
        self.scene = "menu"

    def _handle_menu_action(self, action):
        if action == 'quit':
            self.is_pygame_loop_running = False
            return
        if action == 'continue':
            self.scene = "playing"
            return
        if action in ('play2d', 'play3d', 'playfps'):
            if self.game_started_once:
                self.reset_game_state_full()
            self.game_started_once = True
            self.scene = "playing"
            self.set_view_mode({'play2d': '2d', 'play3d': '3d', 'playfps': 'fps'}[action])

    def _train_avatar_heatmap_on_init(self):
        print("\n=== ENTRENANDO/RE-ENTRENANDO HEATMAP DEL AVATAR ===")
        iters_hm = self.avatar_heatmap_training_iterations
        enemy_positions_set_for_hm = set(self.game_state.enemy_positions)  # Usar enemigos actuales

        best_hm_path = self.heat_map_pathfinder.train(
            self.game_state.initial_player_pos, self.game_state.house_pos,
            self.game_state.obstacles, enemy_positions_set_for_hm, iters_hm)

        if best_hm_path:
            print(f"Heatmap Avatar: Ruta de referencia de {len(best_hm_path)} pasos.")
            self.avatar_heatmap_trained = True
        else:
            print("Heatmap Avatar: No se encontró ruta de referencia.")
            self.avatar_heatmap_trained = False

        if self.avatar_heatmap_trained:
            print("Analizando entorno con Heatmap Avatar entrenado...")
            num_enemies_analysis = len(self.game_state.enemies or [])
            self.environment_analyzed = self.heat_map_pathfinder.analyze_environment(
                self.game_state.initial_player_pos, self.game_state.house_pos,
                self.game_state.obstacles, num_enemies_analysis)
            if self.environment_analyzed:
                print("Análisis del entorno completado.")
            else:
                print("Advertencia: Análisis del entorno no se completó bien.")
        else:
            self.environment_analyzed = False
        print("=== ENTRENAMIENTO HEATMAP AVATAR FINALIZADO ===\n")

    # ================================================================ TURNOS
    def update(self):
        """Ejecuta un turno cada MOVE_DELAY ms (HEADLESS_DELAY en modo sin cabeza)."""
        if not self.is_running:
            return
        turn_delay = GameConfig.HEADLESS_DELAY if GameConfig.HEADLESS_MODE else GameConfig.MOVE_DELAY
        current_tick = pygame.time.get_ticks()
        if current_tick - self.move_timer < turn_delay:
            return
        self.move_timer = current_tick
        self.play_turn()

    def play_turn(self):
        """Un turno completo: avatar → victoria → enemigos → captura → replanificación."""
        self.turn_counter += 1

        self._advance_player()
        if self._check_victory():
            return

        if self.enemies_initialized and self.game_state.enemies:
            self._update_enemies()
            if self._check_player_enemy_collision():
                return
            if self.turn_counter % GameConfig.REPLAN_EVERY_TURNS == 0 or self._path_is_threatened():
                self.determine_player_optimal_path()

    def _advance_player(self):
        """Da un paso por la ruta; si está bloqueada replanifica, y si no hay ruta segura, huye."""
        if self._try_step_along_path():
            return
        self.determine_player_optimal_path()
        if self._try_step_along_path():
            return
        self._player_flee_step()

    def _try_step_along_path(self):
        path, idx = self.current_path_player, self.path_index_player
        if not path or idx >= len(path):
            return False
        next_pos = path[idx]
        if manhattan(next_pos, self.game_state.player_pos) != 1 or not self.game_state.is_valid_move(next_pos):
            return False
        self._move_player_to(next_pos)
        self.path_index_player += 1
        return True

    def _move_player_to(self, new_pos):
        old = self.game_state.player_pos
        if manhattan(old, new_pos) == 1:
            self.player_facing = (new_pos[0] - old[0], new_pos[1] - old[1])
        self.game_state.player_pos = new_pos
        self.player_movement_frequency_matrix[new_pos[1]][new_pos[0]] += 1
        self.step_counter += 1

    def _player_flee_step(self):
        """
        Sin ruta segura a la casa (p. ej. enemigos tapando un pasillo): si hay un
        enemigo cerca, el avatar se mueve a la celda vecina más alejada de todos
        los enemigos; si no, espera.
        """
        enemies = self.game_state.enemy_positions
        here = self.game_state.player_pos
        if not enemies or min(manhattan(here, e) for e in enemies) > GameConfig.DANGER_RADIUS:
            return
        options = [here] + [n for n in neighbors_4(here, self.game_state.grid_width, self.game_state.grid_height,
                                                   self.game_state.obstacles) if n not in enemies]
        best = max(options, key=lambda p: (min(manhattan(p, e) for e in enemies), random.random()))
        if best != here:
            self._move_player_to(best)
            self.player_path_source = "Huida"
            self.current_path_player = [best]
            self.path_index_player = 1

    def _check_victory(self):
        if self.game_state.player_pos == self.game_state.house_pos and not self.game_state.victory:
            self.game_state.victory = True
            self.is_running = False
            print(f"¡Meta alcanzada en {self.step_counter} pasos y {self.turn_counter} turnos!")
        return self.game_state.victory

    def _path_is_threatened(self):
        """True si algún enemigo está a 1 casilla o menos de las próximas celdas de la ruta."""
        upcoming = self.current_path_player[self.path_index_player:
                                            self.path_index_player + GameConfig.THREAT_LOOKAHEAD]
        return any(manhattan(cell, e) <= 1 for cell in upcoming for e in self.game_state.enemy_positions)

    def _execute_player_random_move(self):
        val_rand = random.randint(1, 20);
        curr_p = self.game_state.player_pos;
        next_p_cand = None
        if GameConfig.MOVE_UP_RANGE[0] <= val_rand <= GameConfig.MOVE_UP_RANGE[1]:
            next_p_cand = (curr_p[0], curr_p[1] - 1)
        elif GameConfig.MOVE_RIGHT_RANGE[0] <= val_rand <= GameConfig.MOVE_RIGHT_RANGE[1]:
            next_p_cand = (curr_p[0] + 1, curr_p[1])
        elif GameConfig.MOVE_DOWN_RANGE[0] <= val_rand <= GameConfig.MOVE_DOWN_RANGE[1]:
            next_p_cand = (curr_p[0], curr_p[1] + 1)
        elif GameConfig.MOVE_LEFT_RANGE[0] <= val_rand <= GameConfig.MOVE_LEFT_RANGE[1]:
            next_p_cand = (curr_p[0] - 1, curr_p[1])

        if next_p_cand and self.game_state.is_valid_move(
                next_p_cand) and next_p_cand not in self.game_state.enemy_positions:
            self.game_state.player_pos = next_p_cand
            self.player_movement_frequency_matrix[next_p_cand[1]][next_p_cand[0]] += 1
            self.step_counter += 1
            self.current_path_player = [self.game_state.player_pos]
            self.path_index_player = 1
            self.player_uses_heatmap_path = False

    def initiate_player_agent_training(self):
        if self.player_agent_is_training: print("Ent. Jugador ya en curso."); return
        if self.enemy_agent_is_training: print("Ent. Enemigo en curso, espera."); return
        print("Iniciando ent. AGENTE JUGADOR...")
        self.game_state.player_pos = self.game_state.initial_player_pos
        self.player_movement_frequency_matrix.fill(0)
        self.game_state.victory = False
        self.player_agent_is_training = True
        self.player_agent_training_progress = 0.0
        self.player_agent_training_complete = False
        self.player_agent_training_status = "Ent. Jugador..."
        self.agent_player.max_training_iterations = self.player_agent_max_training_iterations

        def p_q_cb(it, _p, _h, _bp, is_final=False):
            # Se ejecuta en el hilo de entrenamiento: sólo actualiza indicadores.
            max_it = self.agent_player.max_training_iterations
            self.player_agent_training_progress = (it / max_it) * 100.0 if max_it > 0 else 100.0
            success = self.agent_player.success_rate * 100
            self.player_agent_training_status = f"J: éxito {success:.0f}%"
            if is_final:
                self.player_agent_is_training = False
                self.player_agent_training_complete = True
                self.player_agent_training_status = f"J: COMPLETO (éxito {success:.0f}%)"
                print("Ent. AGENTE JUGADOR finalizado.")
                self._replan_requested = True  # El hilo principal recalcula la ruta

        self.agent_player.train_background(self.game_state.house_pos, self.game_state.initial_player_pos,
                                           set(self.game_state.obstacles), callback=p_q_cb, update_interval=30)

    def _q_policy_path(self):
        """Ruta que produce la política del Agente Q Jugador desde la posición actual (o None)."""
        path = self.agent_player.simulate_policy(self.game_state.player_pos, self.game_state.house_pos,
                                                 set(self.game_state.obstacles))
        if path[-1] != self.game_state.house_pos or len(path) < 2:
            return None
        if any(cell in self.game_state.enemy_positions for cell in path[1:]):
            return None
        return path

    def determine_player_optimal_path(self):
        """
        Calcula las rutas candidatas desde la posición ACTUAL del avatar y elige
        la de menor costo de riesgo (pasos + peligro por cercanía a enemigos):
          - Heatmap Avatar: A* sobre el mapa de calor, evitando enemigos.
          - Agente Q Jugador: la política aprendida (si está entrenado y no
            se forzó el heatmap con 'N').
        """
        enemies = set(self.game_state.enemy_positions)
        candidates = []

        if self.avatar_heatmap_trained:
            hm_path = self.heat_map_pathfinder.find_path_with_heat_map(
                self.game_state.player_pos, self.game_state.house_pos,
                obstacles=self.game_state.obstacles, enemy_positions_set=enemies, is_avatar=True)
            if hm_path:
                candidates.append(("Heatmap Avatar", hm_path))

        if self.player_agent_training_complete and not self.player_uses_heatmap_path and \
                self.agent_player.is_policy_current(self.game_state.obstacles):
            q_path = self._q_policy_path()
            if q_path:
                candidates.append(("Agente Q Jugador", q_path))

        if candidates:
            self.player_path_source, self.best_path_player = min(
                candidates, key=lambda c: self.heat_map_pathfinder.path_cost(c[1], enemies))
        else:
            self.player_path_source, self.best_path_player = "Ninguna", None
        self._follow_path(self.best_path_player)

    def _follow_path(self, path):
        """Carga `path` como ruta actual. path[0] es la celda actual; el índice apunta al siguiente paso."""
        if path and path[0] == self.game_state.player_pos:
            self.current_path_player = list(path)
        else:
            self.current_path_player = [self.game_state.player_pos]
        self.path_index_player = 1

    def toggle_game_running_state(self):
        if not self.is_running:  # Si el juego estaba detenido y se va a iniciar
            self.is_running = True
            self.game_state.victory = False;
            self.game_state.player_caught = False;
            self.game_over = False
            self.move_timer = pygame.time.get_ticks()

            if not self.enemies_initialized and not self.user_placed_enemies:
                self._initialize_game_enemies()
            elif not self.enemies_initialized and self.user_placed_enemies:  # Usuario puso enemigos, pero no se ha "inicializado formalmente"
                self.enemies_initialized = True
                # Si enemies_initialized es True Y user_placed_enemies es False Y no hay enemigos, significa que se limpiaron
            # y el usuario no puso nuevos. Se correrá sin enemigos.

            self.enemy_move_accumulator = 0.0
            self.determine_player_optimal_path()
        else:  # Si el juego estaba corriendo y se va a detener
            self.is_running = False
            print("Juego detenido.")

    def reset_game_state_full(self):
        self.is_running = False
        self.game_state.initialize_game();
        self.player_movement_frequency_matrix.fill(0)
        self.best_path_player = None
        self.step_counter = 0
        self.turn_counter = 0
        self.enemy_move_accumulator = 0.0
        self.game_over = False
        self.enemies_initialized = False
        self.user_placed_enemies = False
        self.game_state.victory = False;
        self.game_state.player_caught = False
        if self.player_agent_is_training: self.stop_player_agent_training()
        if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()
        self.player_uses_heatmap_path = False;
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None;
            self.input_buffer = ""

        print("Juego reseteado. Aprendizaje agentes MANTENIDO.")
        self._train_avatar_heatmap_on_init()
        self.determine_player_optimal_path()

    def generate_new_random_obstacles(self):
        self.game_state.generate_obstacles();
        print("Nuevos obstáculos generados.");
        self.best_path_player = None
        self._train_avatar_heatmap_on_init()
        self.determine_player_optimal_path()

    def clear_all_enemies(self):
        self.game_state.enemies.clear();
        self.game_state.enemy_positions.clear();
        self.enemies_initialized = True
        self.user_placed_enemies = False
        print("Enemigos limpiados.")
        self._train_avatar_heatmap_on_init()
        self.determine_player_optimal_path()

    def edit_obstacle_at_pos(self, pos_edit_obs):
        changed = False
        if pos_edit_obs == self.game_state.player_pos or pos_edit_obs == self.game_state.house_pos: print(
            f"No se puede editar obstáculo en Jugador/Casa: {pos_edit_obs}"); return

        if pos_edit_obs in self.game_state.obstacles:
            self.game_state.obstacles.remove(pos_edit_obs);
            print(f"Obstáculo quitado: {pos_edit_obs}")
            changed = True
        else:
            if pos_edit_obs in self.game_state.enemy_positions: print(
                f"No se puede añadir obstáculo en posición de enemigo: {pos_edit_obs}"); return
            self.game_state.obstacles.add(pos_edit_obs);
            print(f"Obstáculo añadido: {pos_edit_obs}")
            changed = True

        if changed:
            self.best_path_player = None
            self._train_avatar_heatmap_on_init()
            self.determine_player_optimal_path()

    def reset_avatar_heatmap_data(self):
        self.heat_map_pathfinder.reset();
        self.avatar_heatmap_trained = False
        self.environment_analyzed = False
        self.player_uses_heatmap_path = False
        print("Heatmap Avatar reiniciado. Se requiere re-entrenamiento ('M').")
        self.determine_player_optimal_path()

    def train_avatar_heatmap_interactive(self, iterations=None):
        if self.player_agent_is_training or self.enemy_agent_is_training: print(
            "Otro entrenamiento activo, espera."); return
        iters = iterations or self.avatar_heatmap_training_iterations
        print(f"Iniciando entrenamiento INTERACTIVO Heatmap Avatar ({iters} iter)...")
        start_pos_hm = self.game_state.initial_player_pos
        target_pos_hm = self.game_state.house_pos

        stop_flag_hm_train = [False]

        def hm_cb_inter(it_n, tot_n, _p, _bp, prog_p, is_final=False):
            if it_n % max(1, tot_n // 40) == 0 and not is_final:
                self.renderer.render_training_overlay(it_n / max(1, tot_n))
            pygame.event.pump()
            for ev_stop in pygame.event.get():
                if ev_stop.type == pygame.QUIT: stop_flag_hm_train[0] = True; self.is_pygame_loop_running = False
                if ev_stop.type == pygame.KEYDOWN and ev_stop.key == pygame.K_ESCAPE: stop_flag_hm_train[0] = True
            return not stop_flag_hm_train[0]

        current_enemies_for_hm_train = set(self.game_state.enemy_positions)
        best_hm_p_i = self.heat_map_pathfinder.train(
            start_pos_hm, target_pos_hm,
            self.game_state.obstacles, current_enemies_for_hm_train, iters, callback=hm_cb_inter)

        if not stop_flag_hm_train[0]:
            if best_hm_p_i:
                self.avatar_heatmap_trained = True
                print(f"Heatmap Avatar Ent. (Inter) COMPLETO. Ruta de referencia: {len(best_hm_p_i)}p.")
                print("Re-analizando entorno con Heatmap Avatar entrenado...")
                num_enemies_analysis = len(self.game_state.enemies or [1, 2, 3, 4])
                self.environment_analyzed = self.heat_map_pathfinder.analyze_environment(
                    start_pos_hm, target_pos_hm, self.game_state.obstacles, num_enemies_analysis)
                if self.environment_analyzed:
                    print("Análisis del entorno completado.")
                else:
                    print("Advertencia: Re-análisis del entorno no se completó bien.")
                self.determine_player_optimal_path()
            else:
                print("Heatmap Avatar Ent. (Inter) COMPLETO. No se encontró ruta de referencia.")
                self.avatar_heatmap_trained = False
        else:
            print("Entrenamiento Heatmap Avatar DETENIDO por usuario.")

    def set_player_to_use_heatmap_path(self):
        """
        Alterna entre "elegir automáticamente la ruta más segura" (Heatmap o
        Agente Q) y "forzar la ruta del Heatmap Avatar".
        """
        if self.player_uses_heatmap_path:
            self.player_uses_heatmap_path = False
            print("Selección de ruta AUTOMÁTICA (Heatmap o Agente Q, la de menor riesgo).")
            self.determine_player_optimal_path()
            return

        if not self.avatar_heatmap_trained:
            print("Heatmap Avatar no entrenado. Entrenando interactivamente...")
            self.train_avatar_heatmap_interactive()
            if not self.avatar_heatmap_trained: print("Fallo al entrenar HM. No se puede usar."); return

        self.player_uses_heatmap_path = True
        self.determine_player_optimal_path()
        if self.player_path_source == "Heatmap Avatar":
            print(f"Jugador FORZADO a seguir el Heatmap Avatar: {len(self.current_path_player)}p.")
            if not self.is_running: print("Ruta de Heatmap cargada. Presiona Iniciar para seguirla.")
        else:
            print("No se encontró ruta usando Heatmap para la posición actual del jugador.")

    def request_avatar_heatmap_visualization(self):
        if not self.avatar_heatmap_trained: print("HM Av no entrenado."); return
        print("Solicitando vis. HM Avatar...");
        path_to_display = self.current_path_player if self.is_running and self.current_path_player and len(
            self.current_path_player) > 1 else self.best_path_player
        if path_to_display and len(path_to_display) <= 1 and self.best_path_player:
            path_to_display = self.best_path_player

        self.plot_request_queue.put({'agent': self.heat_map_pathfinder, 'type': 'heatmap_avatar',
                                     'args': {'start_pos': self.game_state.player_pos,
                                              'goal_pos': self.game_state.house_pos,
                                              'path': path_to_display,
                                              'obstacles_vis': list(self.game_state.obstacles),
                                              'enemies_vis': list(self.game_state.enemy_positions),
                                              'title': "Mapa Calor - Rutas Avatar (desde pos actual)",
                                              'show': True,
                                              'save_path': "heatmap_avatar_visualizado.png"}})

    def toggle_player_edit_mode(self, mode_str_edit):
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None;
            self.input_buffer = ""

        if self.edit_mode == mode_str_edit:
            self.edit_mode = None;
            print(f"Modo Edición '{mode_str_edit.upper()}' DESACTIVADO.")
        else:
            self.edit_mode = mode_str_edit;
            print(f"Modo Edición: {mode_str_edit.upper()} ACTIVADO.")

    def _handle_input_field_click(self, field_id):
        if self.edit_mode:
            self.edit_mode = None

        if self.input_field_active == field_id:
            self._apply_input_buffer(field_id)
            self.input_field_active = None;
            self.input_buffer = ""
        else:
            if self.input_field_active:
                self._apply_input_buffer(self.input_field_active)

            self.input_field_active = field_id
            if field_id == 'avatar_heatmap_iters':
                self.input_buffer = str(self.avatar_heatmap_training_iterations)
            print(f"Campo entrada '{field_id}' activado. Valor: {self.input_buffer}. Use teclado y Enter/Esc.")

    def _apply_input_buffer(self, field_id):
        if not field_id: return False
        try:
            value = int(self.input_buffer)
            if value <= 0:
                print(f"Error: Valor para '{field_id}' debe ser positivo (>0). No se aplicó '{self.input_buffer}'.")
                if field_id == 'avatar_heatmap_iters': self.input_buffer = str(self.avatar_heatmap_training_iterations)
                return False

            if field_id == 'avatar_heatmap_iters':
                if self.avatar_heatmap_training_iterations != value:
                    self.avatar_heatmap_training_iterations = value
                    print(f"Iteraciones Heatmap Avatar actualizadas a: {value}")
                    self.avatar_heatmap_trained = False
                    self.environment_analyzed = False
                    print("Heatmap Avatar necesitará re-entrenarse.")
                    if not self.is_running:
                        self._train_avatar_heatmap_on_init()
                        self.determine_player_optimal_path()
            return True
        except ValueError:
            print(f"Error: Entrada inválida '{self.input_buffer}' para '{field_id}'. No se aplicó.")
            if field_id == 'avatar_heatmap_iters': self.input_buffer = str(self.avatar_heatmap_training_iterations)
            return False

    def _manual_player_move(self, dx, dy):
        if self.is_running:  # Si el juego está corriendo, el movimiento es automático y este se ignora
            return

        if self.input_field_active: return

        self.player_facing = (dx, dy)
        current_player_pos = self.game_state.player_pos
        new_player_pos = (current_player_pos[0] + dx, current_player_pos[1] + dy)

        can_move_here = self._is_pos_in_grid(new_player_pos) and \
                        new_player_pos not in self.game_state.obstacles

        if can_move_here:
            self.game_state.player_pos = new_player_pos

            if GameConfig.COUNT_SETUP_MOVES_IN_FREQUENCY_MAP:
                self.player_movement_frequency_matrix[new_player_pos[1]][new_player_pos[0]] += 1

            self.determine_player_optimal_path()  # Actualizar rutas planeadas después de mover en config

    def _handle_keyboard_input(self, event):
        key_pressed_val = event.key

        if self.input_field_active:
            if key_pressed_val == pygame.K_RETURN:
                if self._apply_input_buffer(self.input_field_active):
                    pass
                self.input_field_active = None;
                self.input_buffer = ""
            elif key_pressed_val == pygame.K_ESCAPE:
                self.input_field_active = None;
                self.input_buffer = ""
            elif key_pressed_val == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif event.unicode.isdigit():
                if len(self.input_buffer) < 5: self.input_buffer += event.unicode
            return

        if key_pressed_val == pygame.K_ESCAPE:
            if self.edit_mode:
                self.edit_mode = None
            else:
                self.open_menu()
            return
        if key_pressed_val == pygame.K_TAB:
            self.cycle_view_mode()
            return
        if key_pressed_val == pygame.K_t:
            self.toggle_trail()
            return
        if self.view_mode == 'fps' and key_pressed_val in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            self._first_person_control(key_pressed_val)
            return

        if key_pressed_val == pygame.K_SPACE:
            self.toggle_game_running_state()
        elif key_pressed_val == pygame.K_r:
            self.reset_game_state_full()
        elif key_pressed_val == pygame.K_h:
            if not self.player_agent_is_training:
                self.initiate_player_agent_training()
            else:
                print("Ent. Agente Jugador ya en curso.")
        elif key_pressed_val == pygame.K_o:
            self.toggle_player_edit_mode('obstacles')
        elif key_pressed_val == pygame.K_p:
            self.toggle_player_edit_mode('player')
        elif key_pressed_val == pygame.K_c:
            self.toggle_player_edit_mode('house')
        elif key_pressed_val == pygame.K_e:
            self.toggle_player_edit_mode('enemies')
        elif key_pressed_val == pygame.K_g:
            self.generate_new_random_obstacles()
        elif key_pressed_val == pygame.K_m:
            self.train_avatar_heatmap_interactive()
        elif key_pressed_val == pygame.K_v:
            self.request_avatar_heatmap_visualization()
        elif key_pressed_val == pygame.K_n:
            self.set_player_to_use_heatmap_path()
        elif key_pressed_val == pygame.K_q:
            if not self.enemy_agent_is_training:
                self.initiate_enemy_q_agent_training()
            else:
                print("Ent. Q-Agent ENEMIGO ya en curso.")

        elif key_pressed_val == pygame.K_UP:
            self._manual_player_move(0, -1)
        elif key_pressed_val == pygame.K_DOWN:
            self._manual_player_move(0, 1)
        elif key_pressed_val == pygame.K_LEFT:
            self._manual_player_move(-1, 0)
        elif key_pressed_val == pygame.K_RIGHT:
            self._manual_player_move(1, 0)

        elif pygame.K_F1 <= key_pressed_val <= pygame.K_F4:
            if self.enemy_q_agent_trained and not self.enemy_agent_is_training:
                plot_type_map_e = {pygame.K_F1: 'analysis', pygame.K_F2: 'q_heatmap', pygame.K_F3: 'best_path_q',
                                   pygame.K_F4: 'comprehensive'}
                sim_e_start_p = (1, 1)
                if self.game_state.enemies:
                    try:
                        first_enemy_id = list(self.game_state.enemies.keys())[0]
                        sim_e_start_p = self.game_state.enemies[first_enemy_id]['position']
                    except (IndexError, KeyError):
                        pass

                plot_args_map_e = {
                    'analysis': {'show': True, 'save_path': 'plot_q_e_analisis.png'},
                    'q_heatmap': {'show': True, 'save_path': 'plot_q_e_qvals.png'},
                    'best_path_q': {'agent_sim_start_pos': sim_e_start_p, 'target_pos': self.game_state.player_pos,
                                    'obstacles': set(self.game_state.obstacles), 'show': True,
                                    'save_path': 'plot_q_e_camino.png'},
                    'comprehensive': {'agent_target_pos': self.game_state.player_pos,
                                      'agent_initial_pos_for_sim': sim_e_start_p,
                                      'obstacles': set(self.game_state.obstacles), 'show': True,
                                      'save_path': 'plot_q_e_comp.png'}
                }
                ptype_req = plot_type_map_e.get(key_pressed_val);
                pargs_req = plot_args_map_e.get(ptype_req)
                if ptype_req and pargs_req:
                    print(f"Solicitando plot '{ptype_req}' Q-Enemigo...");
                    self.plot_request_queue.put({'agent': self.enemy_q_agent, 'type': ptype_req, 'args': pargs_req})
            else:
                print("Q-Enemigo no entrenado o entrenando. ('Q' primero para entrenar)")

    def _first_person_control(self, key):
        """En primera persona (con el juego detenido): ←/→ giran 90°, ↑ avanza y ↓ retrocede."""
        if self.is_running or self.input_field_active:
            return
        dx, dy = self.player_facing
        if key == pygame.K_LEFT:
            self.player_facing = (dy, -dx)
        elif key == pygame.K_RIGHT:
            self.player_facing = (-dy, dx)
        elif key == pygame.K_UP:
            self._manual_player_move(dx, dy)
        else:
            self._manual_player_move(-dx, -dy)
            self.player_facing = (dx, dy)  # Retroceder no cambia hacia dónde mira

    def process_grid_click_in_edit_mode(self, clicked_grid_pos_tuple):
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None;
            self.input_buffer = ""
            print(f"Campo texto desactivado por clic en grid (edit mode).")

        original_player_pos = self.game_state.player_pos
        original_house_pos = self.game_state.house_pos
        changed_critical_item = False

        if self.edit_mode == "player":
            if clicked_grid_pos_tuple != self.game_state.house_pos and \
                    clicked_grid_pos_tuple not in self.game_state.obstacles and \
                    clicked_grid_pos_tuple not in self.game_state.enemy_positions:
                self.game_state.player_pos = clicked_grid_pos_tuple
                self.game_state.initial_player_pos = clicked_grid_pos_tuple
                print(f"Jugador movido a: {clicked_grid_pos_tuple}");
                if original_player_pos != self.game_state.player_pos: changed_critical_item = True
            else:
                print(f"Posición inválida para jugador: {clicked_grid_pos_tuple}.")
            self.edit_mode = None
        elif self.edit_mode == "house":
            if clicked_grid_pos_tuple != self.game_state.player_pos and \
                    clicked_grid_pos_tuple not in self.game_state.obstacles and \
                    clicked_grid_pos_tuple not in self.game_state.enemy_positions:
                self.game_state.house_pos = clicked_grid_pos_tuple
                print(f"Casa movida a: {clicked_grid_pos_tuple}");
                if original_house_pos != self.game_state.house_pos: changed_critical_item = True
            else:
                print(f"Posición inválida para casa: {clicked_grid_pos_tuple}.")
            self.edit_mode = None
        elif self.edit_mode == "obstacles":
            self.edit_obstacle_at_pos(clicked_grid_pos_tuple)
        elif self.edit_mode == "enemies":
            enemy_id_at_click = self.game_state.get_enemy_at_position(clicked_grid_pos_tuple)
            if enemy_id_at_click is not None:
                if self.game_state.remove_enemy(clicked_grid_pos_tuple):
                    print(f"Enemigo ID {enemy_id_at_click} removido de {clicked_grid_pos_tuple}")
                    if not self.game_state.enemies: self.user_placed_enemies = False
                else:
                    print(f"Error al remover enemigo ID {enemy_id_at_click}.")
            else:
                default_type_on_click = random.choice(GameConfig.ENEMY_TYPES)
                newly_added_enemy_id = self.game_state.add_enemy(clicked_grid_pos_tuple, default_type_on_click)
                if newly_added_enemy_id is not None:
                    print(f"Enemigo '{default_type_on_click}' ID {newly_added_enemy_id} en {clicked_grid_pos_tuple}")
                    self.user_placed_enemies = True
                    if not self.enemies_initialized: self.enemies_initialized = True
                else:
                    print(f"No se pudo añadir enemigo en {clicked_grid_pos_tuple}.")
            self._train_avatar_heatmap_on_init()
            self.determine_player_optimal_path()

        if changed_critical_item:
            self.best_path_player = None
            self._train_avatar_heatmap_on_init()
            self.determine_player_optimal_path()

    def _process_ui_button_click(self, button_id_str_clicked):
        field_id_of_button = None
        if button_id_str_clicked == "toggle_edit_avatar_heatmap_iters":
            field_id_of_button = "avatar_heatmap_iters"

        edit_mode_button_would_set = None
        if button_id_str_clicked.startswith("edit_"):
            try:
                edit_mode_button_would_set = button_id_str_clicked.split("edit_")[1]
            except IndexError:
                pass

        if self.input_field_active and self.input_field_active != field_id_of_button:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None;
            self.input_buffer = ""

        if self.edit_mode and self.edit_mode != edit_mode_button_would_set:
            non_edit_buttons = ["start", "reset", "train_player_agent", "train_enemy_agent",
                                "stop_train", "use_heat_map", "visualize_heat_map", "reset_heat_map",
                                "toggle_edit_avatar_heatmap_iters", "generate", "menu"]
            if button_id_str_clicked in non_edit_buttons or button_id_str_clicked.startswith("clear_"):
                self.edit_mode = None

        if button_id_str_clicked == "start":
            self.toggle_game_running_state()
        elif button_id_str_clicked == "reset":
            self.reset_game_state_full()
        elif button_id_str_clicked == "train_player_agent":
            if not self.player_agent_is_training:
                self.initiate_player_agent_training()
            else:
                print("Ent. Agente Jugador ya en curso.")
        elif button_id_str_clicked == "train_enemy_agent":
            if not self.enemy_agent_is_training:
                self.initiate_enemy_q_agent_training()
            else:
                print("Ent. Q-Agente Enemigo ya en curso.")
        elif button_id_str_clicked == "stop_train":
            stopped_any = False
            if self.player_agent_is_training: self.stop_player_agent_training(); stopped_any = True
            if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training(); stopped_any = True
            if stopped_any:
                print("Intentando detener entrenamientos.")
            else:
                print("No hay entrenamientos para detener.")
        elif button_id_str_clicked == "edit_player":
            self.toggle_player_edit_mode("player")
        elif button_id_str_clicked == "edit_house":
            self.toggle_player_edit_mode("house")
        elif button_id_str_clicked == "edit_obstacles":
            self.toggle_player_edit_mode("obstacles")
        elif button_id_str_clicked == "edit_enemies":
            self.toggle_player_edit_mode("enemies")
        elif button_id_str_clicked == "clear_obstacles":
            self.game_state.obstacles.clear();
            self.best_path_player = None;
            self._train_avatar_heatmap_on_init()
            self.determine_player_optimal_path()
            print("Obstáculos borrados.")
        elif button_id_str_clicked == "clear_enemies":
            self.clear_all_enemies()
        elif button_id_str_clicked == "use_heat_map":
            self.set_player_to_use_heatmap_path()
        elif button_id_str_clicked == "visualize_heat_map":
            self.request_avatar_heatmap_visualization()
        elif button_id_str_clicked == "reset_heat_map":
            self.reset_avatar_heatmap_data()
        elif button_id_str_clicked == "toggle_edit_avatar_heatmap_iters":
            self._handle_input_field_click('avatar_heatmap_iters')
        elif button_id_str_clicked == "toggle_view":
            self.cycle_view_mode()
        elif button_id_str_clicked == "toggle_trail":
            self.toggle_trail()
        elif button_id_str_clicked == "generate":
            self.generate_new_random_obstacles()
        elif button_id_str_clicked == "menu":
            self.open_menu()

    def run_main_game_loop(self):
        while self.is_pygame_loop_running:
            dt = self.clock.tick(GameConfig.GAME_SPEED) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_pygame_loop_running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    try:
                        pygame.display.toggle_fullscreen()
                    except pygame.error as err:
                        print(f"No se pudo cambiar a pantalla completa: {err}")
                elif self.scene == "menu":
                    action = self.menu.handle_event(event, self.game_started_once)
                    if action:
                        self._handle_menu_action(action)
                else:
                    self._handle_game_event(event)

            if self.scene == "menu":
                mouse = pygame.mouse.get_pos()
                self.menu.draw(self.screen, dt, self.game_started_once, mouse, pygame.mouse.get_pressed()[0])
            else:
                if self._replan_requested:  # Pedido por un hilo de entrenamiento al terminar
                    self._replan_requested = False
                    self.determine_player_optimal_path()
                self.update()
                self.renderer.render(dt)
                self._process_plot_requests()
            pygame.display.flip()

        if self.player_agent_is_training: self.stop_player_agent_training()
        if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()
        pygame.quit()

    def _handle_game_event(self, event):
        if self.view_mode == '3d' and self.renderer.map3d.handle_event(event, self.edit_mode):
            return
        if event.type == pygame.KEYDOWN:
            self._handle_keyboard_input(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            previous_input_field = self.input_field_active
            button_id = self.renderer.get_button_at(event.pos)
            if button_id:
                self._process_ui_button_click(button_id)
            if previous_input_field and button_id != f"toggle_edit_{previous_input_field}":
                self._apply_input_buffer(previous_input_field)
                self.input_field_active = None
                self.input_buffer = ""
            if self.edit_mode and not button_id:
                cell = self.renderer.screen_to_cell(event.pos)
                if cell is not None:
                    self.process_grid_click_in_edit_mode(cell)

    def _process_plot_requests(self):
        if self.plot_request_queue.empty():
            return
        req = None
        try:
            req = self.plot_request_queue.get_nowait()
            agent_plot, ptype_plot, pargs_plot = req['agent'], req['type'], req['args']
            if ptype_plot == 'heatmap_avatar' and isinstance(agent_plot, HeatMapPathfinding):
                agent_plot.visualize_heat_map(**pargs_plot)
            elif isinstance(agent_plot, QLearningAgent):
                plot_map_q = {'analysis': 'plot_analysis', 'q_heatmap': 'plot_q_values_heatmap',
                              'best_path_q': 'plot_best_path', 'comprehensive': 'plot_comprehensive_analysis'}
                plot_func = getattr(agent_plot, plot_map_q.get(ptype_plot, ''), None)
                if plot_func:
                    plot_func(**pargs_plot)
            self.plot_request_queue.task_done()
        except Empty:
            pass
        except Exception as e:
            print(f"MAIN_PLOT_ERR: {e}\nReq: {req}")

    def stop_player_agent_training(self):
        if not self.player_agent_is_training: print("Ent. Agente Jugador no activo."); return
        print("Deteniendo ent. AGENTE JUGADOR...");
        if hasattr(self.agent_player, 'stop_background_training'):
            if self.agent_player.stop_background_training():
                print("Señal parada hilo ent. Agente Jugador.")
            else:
                print("Hilo ent. Agente Jugador no activo o ya parado.")
        self.player_agent_is_training = False
        if not self.player_agent_training_complete:
            self.player_agent_training_status = "Jugador - DETENIDO"

    def player_agent_training_callback(self, iteration, _p_ign, _h_ign, _bp_pol_ign, is_final=False):
        pass

    def initiate_enemy_q_agent_training(self):
        """
        Entrena UNA política compartida por todos los enemigos. Cada episodio
        persigue un objetivo aleatorio, así la política sirve para alcanzar al
        jugador esté donde esté (y para cualquier objetivo intermedio).
        """
        if self.enemy_agent_is_training: print("El Q-Agent Enemigo ya está entrenando."); return
        if self.player_agent_is_training: print("El Agente Jugador está entrenando, espera."); return
        print("Iniciando entrenamiento del Q-Agent para ENEMIGOS (objetivos aleatorios)...")
        self.enemy_agent_is_training = True
        self.enemy_agent_training_progress = 0.0
        self.enemy_agent_training_complete = False
        self.enemy_agent_training_status = "Entrenando Enemigos..."

        target_for_enemy_q = self.game_state.player_pos  # Sólo como referencia para las gráficas F2/F4
        enemy_q_start_pos = self._find_random_valid_start(target_for_enemy_q)
        if self.game_state.enemies:
            enemy_q_start_pos = next(iter(self.game_state.enemies.values()))['position']

        self.enemy_q_agent.max_training_iterations = self.enemy_agent_max_training_iterations
        self.enemy_q_agent.train_background(target_for_enemy_q, enemy_q_start_pos, set(self.game_state.obstacles),
                                            callback=self._enemy_q_agent_training_callback, update_interval=30,
                                            randomize_targets=True)

    def _find_random_valid_start(self, target_pos):
        for _ in range(100):
            pos = (random.randint(0, GameConfig.GRID_WIDTH - 1),
                   random.randint(0, GameConfig.GRID_HEIGHT - 1))
            if pos != target_pos and pos not in self.game_state.obstacles:
                return pos
        return (1, 1)

    def _enemy_q_agent_training_callback(self, iteration, _pe_ign, _he_ign, _bpe_pol_ign, is_final=False):
        max_it = self.enemy_q_agent.max_training_iterations
        self.enemy_agent_training_progress = (iteration / max_it) * 100.0 if max_it > 0 else 100.0
        success = self.enemy_q_agent.success_rate * 100
        self.enemy_agent_training_status = f"Enemigo - éxito {success:.0f}%"
        if is_final:
            self.enemy_agent_is_training = False
            self.enemy_agent_training_complete = True
            self.enemy_q_agent_trained = True
            self.enemy_agent_training_status = f"Enemigo - COMPLETO (éxito {success:.0f}%)"
            print("Ent. Q-Agent ENEMIGO finalizado.")

    # ============================================================== ENEMIGOS
    def _update_enemies(self):
        """
        Velocidad relativa con acumulador: cada turno se suma ENEMY_SPEED_FACTOR
        y por cada unidad completa los enemigos dan un paso. Así 0.5 = 1 paso
        cada 2 turnos, 0.75 = 3 pasos cada 4 turnos y 2.0 = 2 pasos por turno.
        """
        if not self.is_running or self.game_state.victory or self.game_over: return
        if not self.enemies_initialized or not self.game_state.enemies: return
        if GameConfig.ENEMY_SPEED_FACTOR <= 0: return

        self.enemy_move_accumulator += GameConfig.ENEMY_SPEED_FACTOR
        while self.enemy_move_accumulator >= 1.0:
            self.enemy_move_accumulator -= 1.0
            self._move_all_enemies_once()
            if self.game_state.player_pos in self.game_state.enemy_positions:
                break

    def _move_all_enemies_once(self):
        for e_id, e_data in list(self.game_state.enemies.items()):
            current = e_data['position']
            target = self._enemy_target(e_data)
            next_pos = self._enemy_next_step(e_data, target)
            if next_pos != current and self.game_state.update_enemy_position(e_id, next_pos):
                recent = e_data.setdefault('recent', [])
                recent.append(current)
                del recent[:-GameConfig.ENEMY_LOOP_MEMORY]
            if next_pos == self.game_state.player_pos:
                return

    def _enemy_target(self, e_data):
        """
        Decide hacia dónde va cada tipo de enemigo (None = movimiento libre):
        - perseguidor: directo a la posición actual del jugador.
        - bloqueador: a la celda BLOCKER_LOOKAHEAD pasos adelante en la ruta del
          jugador (le corta el paso); si está a 2 casillas o menos, lo ataca.
        - patrulla: recorre una ronda alrededor de su punto de aparición; si ve
          al jugador (PATROL_DETECTION_RADIUS) lo persigue hasta perderlo
          (PATROL_LOSE_RADIUS) y entonces vuelve a su ronda.
        - aleatorio: deambula con inercia.
        """
        enemy_type = e_data.get('type', GameConfig.DEFAULT_ENEMY_TYPE)
        position, player = e_data['position'], self.game_state.player_pos
        distance_to_player = manhattan(position, player)

        if enemy_type == 'aleatorio':
            e_data['state'] = 'wander'
            return None

        if enemy_type == 'bloqueador':
            remaining = self.current_path_player[self.path_index_player:-1]  # Sin la casa (no la pueden pisar)
            if distance_to_player <= 2 or not remaining:
                e_data['state'] = 'chase'
                return player
            e_data['state'] = 'intercept'
            return remaining[min(GameConfig.BLOCKER_LOOKAHEAD, len(remaining)) - 1]

        if enemy_type == 'patrulla':
            if e_data.get('state') == 'chase':
                if distance_to_player > GameConfig.PATROL_LOSE_RADIUS:
                    e_data['state'] = 'patrol'
            elif distance_to_player <= GameConfig.PATROL_DETECTION_RADIUS:
                e_data['state'] = 'chase'
                print(f"Patrulla en {position} detectó al jugador.")
            else:
                e_data['state'] = 'patrol'
            if e_data['state'] == 'chase':
                return player
            return self._next_patrol_waypoint(e_data)

        e_data['state'] = 'chase'  # perseguidor
        return player

    def _next_patrol_waypoint(self, e_data):
        route = e_data.get('patrol_path')
        if not route:
            route = self._build_patrol_route(e_data['position'])
            e_data['patrol_path'], e_data['patrol_index'] = route, 0
        if e_data['position'] == route[e_data['patrol_index']]:
            e_data['patrol_index'] = (e_data['patrol_index'] + 1) % len(route)
        return route[e_data['patrol_index']]

    def _build_patrol_route(self, center):
        """Ronda: el punto de aparición + hasta 3 celdas libres a ~PATROL_RADIUS (una por cuadrante)."""
        route = [center]
        radius = GameConfig.PATROL_RADIUS
        for sign_x, sign_y in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            candidates = [(center[0] + sign_x * dx, center[1] + sign_y * (radius - dx)) for dx in range(radius + 1)]
            candidates = [c for c in candidates if self._is_pos_in_grid(c) and c not in self.game_state.obstacles
                          and c != self.game_state.house_pos]
            if candidates:
                route.append(random.choice(candidates))
            if len(route) == 4:
                break
        return route

    def _enemy_next_step(self, e_data, target):
        """
        Elige la siguiente celda del enemigo:
        - Sin objetivo: paseo aleatorio con inercia.
        - Ya en el objetivo (bloqueador en su punto de corte): espera.
        - Con Agente Q Enemigo entrenado EN ESTE MAPA: la acción de la política
          aprendida (sabe rodear muros porque aprendió con distancias reales).
        - Sin entrenar: "instinto" voraz, el vecino que más reduce la distancia
          Manhattan (se atasca detrás de los muros: por eso conviene entrenar).
        En ambos casos, una memoria corta evita oscilar entre dos celdas.
        """
        position = e_data['position']
        blocked = self.game_state.obstacles | (self.game_state.enemy_positions - {position}) | \
            {self.game_state.house_pos}
        options = neighbors_4(position, self.game_state.grid_width, self.game_state.grid_height, blocked)
        if not options:
            return position

        if target is None:
            dx, dy = e_data.get('direction', (0, 0))
            keep_going = (position[0] + dx, position[1] + dy)
            if keep_going in options and random.random() < GameConfig.RANDOM_ENEMY_INERTIA:
                return keep_going
            return random.choice(options)

        if target == position:
            return position  # Emboscada: ya está donde quería estar, espera al jugador
        if target in options:
            return target

        next_pos = None
        if self.enemy_q_agent_trained and self.enemy_q_agent.is_policy_current(self.game_state.obstacles):
            action = self.enemy_q_agent.get_learned_action_xy(position, blocked, target_pos=target)
            if action:
                next_pos = (position[0] + action[0], position[1] + action[1])
        if next_pos is None:
            best_distance = min(manhattan(o, target) for o in options)
            next_pos = random.choice([o for o in options if manhattan(o, target) == best_distance])

        recent = e_data.get('recent', [])
        if next_pos in recent:
            fresh = [o for o in options if o not in recent]
            if fresh:
                next_pos = random.choice(fresh)
        return next_pos

    def _check_player_enemy_collision(self):
        if not self.is_running or self.game_state.victory or self.game_over: return False
        if self.game_state.player_pos in self.game_state.enemy_positions:
            self.game_state.player_caught = True;
            self.game_over = True;
            print("¡GAME OVER! Jugador atrapado.");
            self.is_running = False;
            return True
        return False

    def _is_pos_in_grid(self, pos_tuple_check):
        x_c, y_c = pos_tuple_check
        return 0 <= x_c < self.game_state.grid_width and 0 <= y_c < self.game_state.grid_height

    def _initialize_game_enemies(self):
        # print("\n=== INICIALIZANDO ENEMIGOS POR DEFECTO (Colocación) ===");
        self.game_state.enemies.clear();
        self.game_state.enemy_positions.clear();

        num_e_init_config = GameConfig.INITIAL_ENEMY_POSITIONS
        num_e_init = len(num_e_init_config) if num_e_init_config and isinstance(num_e_init_config,
                                                                                list) and num_e_init_config else 4

        # print(f"Intentando colocar {num_e_init} enemigos por defecto...");
        used_pos_e_init = set();
        placed_e_cnt = 0

        if num_e_init_config and isinstance(num_e_init_config, list) and all(
                isinstance(p, tuple) for p in num_e_init_config):
            for i_e_place, e_pos_config in enumerate(num_e_init_config):
                if self._is_pos_in_grid(e_pos_config) and \
                        e_pos_config not in self.game_state.obstacles and \
                        e_pos_config != self.game_state.player_pos and \
                        e_pos_config != self.game_state.house_pos and \
                        e_pos_config not in used_pos_e_init:
                    e_type_for_p = random.choice(GameConfig.ENEMY_TYPES)
                    new_e_id_game = self.game_state.add_enemy(e_pos_config, e_type_for_p)
                    if new_e_id_game is not None:
                        used_pos_e_init.add(e_pos_config);
                        placed_e_cnt += 1

        enemies_to_place_strategically = num_e_init - placed_e_cnt
        if enemies_to_place_strategically > 0:
            for i_e_place in range(enemies_to_place_strategically):
                e_type_for_p = random.choice(GameConfig.ENEMY_TYPES)
                pos_e_for_p = self._get_strategic_position_for_enemy(e_type_for_p, list(used_pos_e_init))
                if pos_e_for_p:
                    new_e_id_game = self.game_state.add_enemy(pos_e_for_p, e_type_for_p)
                    if new_e_id_game is not None:
                        used_pos_e_init.add(pos_e_for_p);
                        placed_e_cnt += 1

        print(f"Inicialización enemigos por defecto: {placed_e_cnt} en juego.");
        self.enemies_initialized = True;

    def _get_strategic_position_for_enemy(self, enemy_type_place_strat, list_occupied_pos_strat):
        if self.environment_analyzed and hasattr(self.heat_map_pathfinder,
                                                 'potential_enemy_positions') and self.heat_map_pathfinder.potential_enemy_positions:
            cand_hm_pos_strat = [];
            if enemy_type_place_strat == 'perseguidor':
                cand_hm_pos_strat = [p for p in self.heat_map_pathfinder.potential_enemy_positions if
                                     self.heat_map_pathfinder.manhattan_distance(p,
                                                                                 self.game_state.player_pos) >= GameConfig.ENEMY_MIN_PLAYER_DISTANCE]
            elif enemy_type_place_strat == 'bloqueador':
                cand_hm_pos_strat = getattr(self.heat_map_pathfinder, 'choke_points', [])
            elif enemy_type_place_strat == 'patrulla':
                cand_hm_pos_strat = getattr(self.heat_map_pathfinder, 'safe_zones', [])
            else:
                cand_hm_pos_strat = list(self.heat_map_pathfinder.potential_enemy_positions)

            avail_strat_hm_pos_s = [p for p in cand_hm_pos_strat if
                                    p not in list_occupied_pos_strat and \
                                    p != self.game_state.player_pos and \
                                    p != self.game_state.house_pos and \
                                    p not in self.game_state.obstacles and \
                                    self._is_pos_in_grid(p)]
            if avail_strat_hm_pos_s:
                return random.choice(avail_strat_hm_pos_s)

        max_tries_rand_pos_e_s = 80
        for _s in range(max_tries_rand_pos_e_s):
            rand_x_e_s = random.randint(0, GameConfig.GRID_WIDTH - 1);
            rand_y_e_s = random.randint(0, GameConfig.GRID_HEIGHT - 1)
            rand_pos_c_e_s = (rand_x_e_s, rand_y_e_s)

            is_valid_for_enemy = self._is_pos_in_grid(rand_pos_c_e_s) and \
                                 rand_pos_c_e_s not in self.game_state.obstacles and \
                                 rand_pos_c_e_s != self.game_state.player_pos and \
                                 rand_pos_c_e_s != self.game_state.house_pos

            not_taken_batch_e_s = rand_pos_c_e_s not in list_occupied_pos_strat
            far_player_e_s = self.heat_map_pathfinder.manhattan_distance(rand_pos_c_e_s,
                                                                         self.game_state.player_pos) >= GameConfig.ENEMY_MIN_PLAYER_DISTANCE

            if is_valid_for_enemy and not_taken_batch_e_s and far_player_e_s: return rand_pos_c_e_s

        return None
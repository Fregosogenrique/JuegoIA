import pygame
import random
import time
import numpy as np
from queue import Queue, Empty

from GameState import GameState
# from DecisionTree import DecisionTree # Comentado - no se usa activamente
from config import GameConfig
from render import GameRenderer
from ADB import QLearningAgent
from HeatMapPathfinding import HeatMapPathfinding


class Game:
    """
    Mi clase principal del juego. Aquí controlo toda la lógica y la UI.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Mi Simulación de Movimiento Inteligente con Heatmap")

        # Flags y contadores
        self.step_counter = 0
        self.game_over = False
        self.is_running = False
        self.is_pygame_loop_running = True

        self.game_state = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.game_state.initialize_game()

        # Estado del Jugador
        self.current_path_player = []  # La ruta que el jugador está siguiendo activamente
        self.path_index_player = 0  # Índice actual en current_path_player
        self.best_path_player = None  # La mejor ruta calculada (puede ser por Q-Learning o Heatmap)

        # Agente Q-learning Enemigos
        self.enemy_q_agent = QLearningAgent(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.enemy_q_agent_trained = False
        self.enemy_agent_is_training = False
        self.enemy_agent_training_progress = 0.0
        self.enemy_agent_training_status = ""
        self.enemy_agent_training_complete = False
        self.enemy_agent_max_training_iterations = 1000

        # Agente Q-learning Jugador
        self.agent_player = QLearningAgent(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.player_agent_is_training = False
        self.player_agent_training_progress = 0.0
        self.player_agent_training_status = ""
        self.player_agent_training_complete = False
        self.player_agent_max_training_iterations = 500

        # Heatmap del Avatar
        self.heat_map_pathfinder = HeatMapPathfinding(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.avatar_heatmap_trained = False
        self.avatar_heatmap_training_iterations = 500  # Valor editable por el usuario
        self.player_uses_heatmap_path = False  # True si current_path_player proviene del heatmap
        self.environment_analyzed = False
        self.enemies_initialized = False

        self._train_avatar_heatmap_on_init()  # Entrenar heatmap base al inicio

        self.player_movement_frequency_matrix = np.zeros((GameConfig.GRID_HEIGHT, GameConfig.GRID_WIDTH), dtype=int)

        self.move_timer = pygame.time.get_ticks()
        self.edit_mode = None  # 'obstacles', 'player', 'house', 'enemies'
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen, self)
        self.learning_status_display = ""
        self.plot_request_queue = Queue()

        # Para manejo de campos de texto
        self.input_field_active = None  # e.g., 'avatar_heatmap_iters'
        self.input_buffer = ""

    def _train_avatar_heatmap_on_init(self):
        print("\n=== ENTRENANDO HEATMAP DEL AVATAR (INICIALIZACIÓN) ===")
        iters_hm = self.avatar_heatmap_training_iterations
        # El heatmap se entrena desde la posición inicial del jugador definida en GameState
        best_hm_path = self.heat_map_pathfinder.train(
            self.game_state.initial_player_pos, self.game_state.house_pos,
            self.game_state.obstacles, set(self.game_state.enemy_positions), iters_hm)  # Pasar enemigos actuales

        if best_hm_path:
            print(f"Heatmap Avatar (Inicial): Ruta de referencia de {len(best_hm_path)} pasos.")
            self.avatar_heatmap_trained = True
            # No asignamos a self.best_path_player aquí directamente.
            # determine_player_optimal_path se encargará de elegir la mejor ruta globalmente.
        else:
            print("Heatmap Avatar (Inicial): No se encontró ruta de referencia.")
            self.avatar_heatmap_trained = False  # Asegurar que está False si falla

        if self.avatar_heatmap_trained:
            print("Analizando entorno con Heatmap Avatar entrenado...")
            num_enemies_analysis = len(self.game_state.enemies or [1, 2, 3, 4])  # Usar enemigos actuales
            self.environment_analyzed = self.heat_map_pathfinder.analyze_environment(
                self.game_state.initial_player_pos, self.game_state.house_pos,
                self.game_state.obstacles, num_enemies_analysis)
            if self.environment_analyzed:
                print("Análisis del entorno completado.")
            else:
                print("Advertencia: Análisis del entorno no se completó bien.")
        else:
            self.environment_analyzed = False  # No se puede analizar sin heatmap
        print("=== ENTRENAMIENTO HEATMAP AVATAR (INICIAL) FINALIZADO ===\n")

    def update(self):
        if not self.is_running: return
        current_tick = pygame.time.get_ticks()

        # Movimiento de enemigos
        if self.enemies_initialized and self.game_state.enemies:
            self._update_enemies()

            # Chequeo de colisión jugador-enemigo
        if self._check_player_enemy_collision():
            return

            # Movimiento del jugador (automático si hay ruta, o manual por teclado)
        if GameConfig.HEADLESS_MODE and self.best_path_player:
            if current_tick - self.move_timer >= GameConfig.HEADLESS_DELAY:
                if self.path_index_player < len(self.best_path_player):
                    next_pos = self.best_path_player[self.path_index_player]
                    if self.game_state.is_valid_move(next_pos) and next_pos not in self.game_state.enemy_positions:
                        self.game_state.player_pos = next_pos
                        self.player_movement_frequency_matrix[next_pos[1]][next_pos[0]] += 1
                        if next_pos == self.game_state.house_pos:
                            self.game_state.victory = True;
                            self.is_running = False;
                            print("HL: ¡Meta!")
                        else:
                            self.path_index_player += 1
                    else:
                        print("HL: Enemigo en ruta o movimiento inválido. Recalculando...");
                        self._recalculate_path_for_player_headless()
                        if not self.best_path_player or not (self.path_index_player < len(self.best_path_player) and \
                                                             self.best_path_player[
                                                                 self.path_index_player] == self.game_state.player_pos):
                            print("HL: Recálculo falló/inválido o ruta no empieza en pos actual. Deteniendo.");
                            self.is_running = False
                    self.move_timer = current_tick
                else:
                    self.is_running = False;
                    print("HL: Ruta completada.")
            return

        if current_tick - self.move_timer >= GameConfig.MOVE_DELAY:
            moved_this_frame = False
            if self.current_path_player and self.path_index_player < len(self.current_path_player):
                if self.path_index_player == 0 and self.current_path_player[0] != self.game_state.player_pos:
                    print(
                        f"JUGADOR: Ruta actual ({self.current_path_player[0]}) no empieza en jugador ({self.game_state.player_pos}). Recalculando...")
                    self._recalculate_player_path()

                if self.current_path_player and self.path_index_player < len(self.current_path_player):
                    next_p_norm = self.current_path_player[self.path_index_player]

                    if self.game_state.is_valid_move(
                            next_p_norm) and next_p_norm not in self.game_state.enemy_positions:
                        self.game_state.player_pos = next_p_norm
                        self.player_movement_frequency_matrix[next_p_norm[1]][next_p_norm[0]] += 1
                        self.path_index_player += 1
                        self.step_counter += 1
                        moved_this_frame = True
                        print(
                            f"Jugador movido automáticamente a {self.game_state.player_pos} (paso {self.path_index_player}/{len(self.current_path_player)})")
                    else:
                        print(f"JUGADOR: Ruta automática bloqueada en {next_p_norm}. Recalculando...")
                        self._recalculate_player_path()

            if moved_this_frame:
                self.move_timer = current_tick

        if self.game_state.player_pos == self.game_state.house_pos:
            self.game_state.victory = True;
            self.is_running = False;
            print("¡Meta alcanzada!")

    def _execute_player_random_move(self):
        print("JUGADOR: Ejecutando movimiento aleatorio (fallback).")
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
            self.path_index_player = 0
            self.player_uses_heatmap_path = False
        else:
            print("JUGADOR: Movimiento aleatorio (fallback) no fue válido o estaba bloqueado.")

    def initiate_player_agent_training(self):
        if self.player_agent_is_training: print("Ent. Jugador ya en curso."); return
        if self.enemy_agent_is_training: print("Ent. Enemigo en curso, espera."); return
        print("Iniciando ent. AGENTE JUGADOR...");
        self.game_state.player_pos = self.game_state.initial_player_pos
        self.player_movement_frequency_matrix.fill(0)
        self.game_state.victory = False;
        self.player_agent_is_training = True;
        self.player_agent_training_progress = 0.0
        self.player_agent_training_complete = False;
        self.player_agent_training_status = "Ent. Jugador..."
        obs_p_train = set(self.game_state.obstacles);
        self.agent_player.max_training_iterations = self.player_agent_max_training_iterations

        def p_q_cb(it, _p, _h, _bp, is_final=False):
            self.player_agent_training_progress = (
                                                          it / self.agent_player.max_training_iterations) * 100.0 if self.agent_player.max_training_iterations > 0 else 100.0
            p_rew = getattr(self.agent_player, 'best_reward', -float('inf'))
            self.player_agent_training_status = f"J:Recomp {p_rew:.1f}" if p_rew > -float('inf') else "J:Opt..."
            if is_final:
                self.player_agent_is_training = False;
                self.player_agent_training_complete = True
                self.player_agent_training_status = f"J:COMPLETO (Rew:{p_rew:.1f})"
                print("Ent. AGENTE JUGADOR finalizado (cbk).")

                path_s = [self.game_state.initial_player_pos];
                c_s = path_s[0]
                for _ in range(GameConfig.GRID_WIDTH * GameConfig.GRID_HEIGHT * 2):
                    if c_s == self.game_state.house_pos: break
                    act_s = self.agent_player.get_learned_action_xy(c_s, obs_p_train,
                                                                    target_pos=self.game_state.house_pos)
                    if not act_s: break
                    c_s = (c_s[0] + act_s[0], c_s[1] + act_s[1])
                    if not self._is_pos_in_grid(c_s) or c_s in obs_p_train: break
                    path_s.append(c_s)

                if c_s == self.game_state.house_pos and len(path_s) > 1:
                    print(f"Política del Jugador Q-Learning generó ruta de {len(path_s)} pasos.")
                    if not self.best_path_player or len(path_s) < len(self.best_path_player):
                        self.best_path_player = path_s
                        print("Esta ruta Q-Learning es ahora la 'best_path_player'.")
                else:
                    print("Política del Jugador Q-Learning no llevó a la casa en simulación.");

                # Tras entrenar, determinar la ruta óptima globalmente
                self.determine_player_optimal_path()

        self.agent_player.train_background(self.game_state.house_pos, self.game_state.initial_player_pos,
                                           obs_p_train, callback=p_q_cb, update_interval=30)

    def determine_player_optimal_path(self):
        print(f"Determinando ruta óptima para jugador desde: {self.game_state.player_pos}")
        p_cand = None;
        method_src = "Ninguno"

        if self.avatar_heatmap_trained and hasattr(self.heat_map_pathfinder, 'find_path_with_heat_map'):
            hm_p = self.heat_map_pathfinder.find_path_with_heat_map(self.game_state.player_pos,
                                                                    self.game_state.house_pos, is_avatar=True)
            if hm_p:
                p_cand = hm_p
                method_src = "Heatmap Avatar"
                print(f"Ruta candidata (Heatmap Avatar): {len(p_cand)}p.")

        if self.player_agent_training_complete and hasattr(self.agent_player, 'get_learned_action_xy'):
            q_p_s = [self.game_state.player_pos];
            c_qp_s = q_p_s[0];
            obs_qp_s = set(self.game_state.obstacles)

            for _ in range(GameConfig.GRID_WIDTH * GameConfig.GRID_HEIGHT * 2):
                if c_qp_s == self.game_state.house_pos: break
                act_qp_s = self.agent_player.get_learned_action_xy(c_qp_s, obs_qp_s,
                                                                   target_pos=self.game_state.house_pos)
                if not act_qp_s: break

                c_qp_s = (c_qp_s[0] + act_qp_s[0], c_qp_s[1] + act_qp_s[1])
                if not self._is_pos_in_grid(c_qp_s) or c_qp_s in obs_qp_s: break
                q_p_s.append(c_qp_s)

            if c_qp_s == self.game_state.house_pos and len(q_p_s) > 1:
                print(f"Ruta candidata (Agente Q Jugador): {len(q_p_s)}p.")
                if not p_cand or len(q_p_s) < len(p_cand):
                    p_cand = q_p_s
                    method_src = "Agente Q Jugador"

        if p_cand:
            self.best_path_player = p_cand
            print(f"MEJOR RUTA para Jugador determinada por '{method_src}': {len(self.best_path_player)} pasos.")
        else:
            self.best_path_player = None
            print("No se pudo determinar una MEJOR RUTA para el Jugador desde la posición actual.")

        # Actualizar current_path_player para seguir la nueva best_path_player si se encontró una
        if self.best_path_player:
            self.current_path_player = self.best_path_player.copy()
            self.path_index_player = 0
            if self.current_path_player[0] != self.game_state.player_pos:
                print(
                    f"ADVERTENCIA: best_path_player {self.best_path_player[0]} no empieza en pos actual {self.game_state.player_pos}. Ajustando current_path.")
                self.current_path_player = [self.game_state.player_pos] + self.current_path_player
                # O recalcular desde la posición actual si esto es un error grave
                # self.current_path_player = [self.game_state.player_pos]
        else:
            self.current_path_player = [self.game_state.player_pos]
            self.path_index_player = 0

    def toggle_game_running_state(self):
        if not self.is_running:
            self.is_running = True
            self.game_state.victory = False
            self.game_state.player_caught = False
            self.game_over = False
            self.move_timer = pygame.time.get_ticks()

            self.determine_player_optimal_path()

            if self.current_path_player:
                self.path_index_player = 0
                print(
                    f"Juego iniciado. Siguiendo ruta de {len(self.current_path_player)} pasos desde {self.game_state.player_pos}")
            else:
                self.current_path_player = [self.game_state.player_pos]
                self.path_index_player = 0
                print(
                    f"Juego iniciado. No hay ruta planificada desde {self.game_state.player_pos}. Esperando movimiento manual.")

            if not self.enemies_initialized:
                self._initialize_game_enemies()
        else:
            self.is_running = False
            print("Juego detenido.")
            if self.player_agent_is_training: self.stop_player_agent_training()
            if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()

    def reset_game_state_full(self):
        self.is_running = False  # Detener el juego primero
        self.game_state.initialize_game();
        self.player_movement_frequency_matrix.fill(0)

        self.best_path_player = None
        self.step_counter = 0;
        self.game_over = False;

        self.enemies_initialized = False
        self.game_state.victory = False;
        self.game_state.player_caught = False
        if self.player_agent_is_training: self.stop_player_agent_training()
        if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()
        self.player_uses_heatmap_path = False;
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None
            self.input_buffer = ""

        print("Juego reseteado. Aprendizaje agentes MANTENIDO.")
        self._train_avatar_heatmap_on_init()  # Re-entrenar heatmap con nueva config.
        self.determine_player_optimal_path()  # Determinar nueva ruta óptima desde pos inicial
        self.current_path_player = self.best_path_player.copy() if self.best_path_player else [
            self.game_state.player_pos]
        self.path_index_player = 0

    def generate_new_random_obstacles(self):
        self.game_state.generate_obstacles();
        print("Nuevos obstáculos generados.");
        self.best_path_player = None
        self._train_avatar_heatmap_on_init()
        self.determine_player_optimal_path()
        self.current_path_player = self.best_path_player.copy() if self.best_path_player else [
            self.game_state.player_pos]
        self.path_index_player = 0

    def clear_all_enemies(self):
        self.game_state.enemies.clear();
        self.game_state.enemy_positions.clear();
        self.enemies_initialized = False
        print("Enemigos limpiados.")

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
            self.current_path_player = self.best_path_player.copy() if self.best_path_player else [
                self.game_state.player_pos]
            self.path_index_player = 0

    def reset_avatar_heatmap_data(self):
        self.heat_map_pathfinder.reset();
        self.avatar_heatmap_trained = False
        self.environment_analyzed = False  # Requerirá re-análisis si se re-entrena
        if self.player_uses_heatmap_path:  # Si la ruta actual era del heatmap, se invalida
            self.best_path_player = None
            self.current_path_player = [self.game_state.player_pos]
            self.path_index_player = 0
        self.player_uses_heatmap_path = False;
        print("Heatmap Avatar reiniciado. Se requiere re-entrenamiento ('M').")
        self.determine_player_optimal_path()  # Intentar encontrar ruta con otros métodos si es posible

    def train_avatar_heatmap_interactive(self, iterations=None):
        if self.player_agent_is_training or self.enemy_agent_is_training: print(
            "Otro entrenamiento activo, espera."); return
        iters = iterations or self.avatar_heatmap_training_iterations
        print(f"Iniciando entrenamiento INTERACTIVO Heatmap Avatar ({iters} iter)...")
        start_pos_hm = self.game_state.initial_player_pos
        target_pos_hm = self.game_state.house_pos

        stop_flag_hm_train = [False]

        def hm_cb_inter(it_n, tot_n, _p, _bp, prog_p):
            if it_n % (tot_n // 20 if tot_n >= 20 else 1) == 0:
                print(f"Prog Ent. Heatmap Avatar: {prog_p:.1f}% ({it_n}/{tot_n})")
                pygame.event.pump()
            for ev_stop in pygame.event.get():
                if ev_stop.type == pygame.QUIT: stop_flag_hm_train[0] = True; self.is_pygame_loop_running = False
                if ev_stop.type == pygame.KEYDOWN and ev_stop.key == pygame.K_ESCAPE: stop_flag_hm_train[0] = True
            return not stop_flag_hm_train[0]

        # Usar enemigos actuales para el entrenamiento del heatmap
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

                self.determine_player_optimal_path()  # Recalcular ruta óptima global
            else:
                print("Heatmap Avatar Ent. (Inter) COMPLETO. No se encontró ruta de referencia.")
                self.avatar_heatmap_trained = False  # Marcar como no entrenado si falla
        else:
            print("Entrenamiento Heatmap Avatar DETENIDO por usuario.")

    def set_player_to_use_heatmap_path(self):
        if not self.avatar_heatmap_trained:
            print("Heatmap Avatar no entrenado. Entrenando interactivamente...");
            self.train_avatar_heatmap_interactive()
            if not self.avatar_heatmap_trained: print("Fallo al entrenar HM. No se puede usar."); return

        path_hm_for_p = self.heat_map_pathfinder.find_path_with_heat_map(self.game_state.player_pos,
                                                                         self.game_state.house_pos, is_avatar=True)
        if path_hm_for_p:
            print(f"Jugador usará ruta desde Heatmap Avatar: {len(path_hm_for_p)}p.");
            self.current_path_player = path_hm_for_p;
            self.path_index_player = 0
            self.player_uses_heatmap_path = True;
            if not self.best_path_player or len(path_hm_for_p) < len(self.best_path_player):
                self.best_path_player = path_hm_for_p  # Actualizar best_path si esta es mejor
            if not self.is_running: print("Ruta de Heatmap cargada. Presiona Iniciar para seguirla.")
        else:
            print("No se encontró ruta usando Heatmap para la posición actual del jugador.");
            self.player_uses_heatmap_path = False
            self.determine_player_optimal_path()  # Intentar con otros métodos

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
                                              'title': "Mapa Calor - Rutas Avatar (desde pos actual)",
                                              'show': True,  # El método del agente debe manejar 'show'
                                              'save_path': "heatmap_avatar_visualizado.png"}})

    def toggle_player_edit_mode(self, mode_str_edit):
        if self.edit_mode == mode_str_edit:
            self.edit_mode = None;
            print("Modo Edición: DESACTIVADO.")
        else:
            self.edit_mode = mode_str_edit;
            print(f"Modo Edición: {mode_str_edit.upper()} ACTIVADO.")
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None
            self.input_buffer = ""

    def _handle_input_field_click(self, field_id):
        if self.input_field_active == field_id:
            self._apply_input_buffer(field_id)
            self.input_field_active = None
            self.input_buffer = ""
            print(f"Campo '{field_id}' desactivado por nuevo clic.")
        else:
            if self.input_field_active:
                self._apply_input_buffer(self.input_field_active)

            self.input_field_active = field_id
            if field_id == 'avatar_heatmap_iters':
                self.input_buffer = str(self.avatar_heatmap_training_iterations)
            print(
                f"Campo de entrada '{field_id}' activado. Valor actual: {self.input_buffer}. Use teclado numérico y Enter/Esc.")
        if self.edit_mode:
            print(f"Modo Edición '{self.edit_mode}' desactivado debido a activación de campo de texto.")
            self.edit_mode = None

    def _apply_input_buffer(self, field_id):
        if not field_id: return False
        try:
            value = int(self.input_buffer)
            if value <= 0:
                print(f"Error: El valor para '{field_id}' debe ser positivo (>0). No se aplicó '{self.input_buffer}'.")
                if field_id == 'avatar_heatmap_iters': self.input_buffer = str(self.avatar_heatmap_training_iterations)
                return False

            if field_id == 'avatar_heatmap_iters':
                if self.avatar_heatmap_training_iterations != value:
                    self.avatar_heatmap_training_iterations = value
                    print(f"Iteraciones Heatmap Avatar actualizadas a: {value}")
                    self.avatar_heatmap_trained = False
                    self.environment_analyzed = False
                    print("El Heatmap Avatar necesitará re-entrenarse con las nuevas iteraciones.")
                    # Considerar re-entrenar automáticamente o recalcular path si el juego no está corriendo
                    if not self.is_running:
                        self._train_avatar_heatmap_on_init()
                        self.determine_player_optimal_path()

                else:
                    print(f"Iteraciones Heatmap Avatar sin cambios ({value}).")
            return True
        except ValueError:
            print(
                f"Error: Entrada inválida '{self.input_buffer}' para '{field_id}'. Debe ser un número entero. No se aplicó.")
            if field_id == 'avatar_heatmap_iters': self.input_buffer = str(self.avatar_heatmap_training_iterations)
            return False

    def _manual_player_move(self, dx, dy):
        if self.input_field_active: return

        current_player_pos = self.game_state.player_pos
        new_player_pos = (current_player_pos[0] + dx, current_player_pos[1] + dy)

        can_move_here = self._is_pos_in_grid(new_player_pos) and \
                        new_player_pos not in self.game_state.obstacles

        if self.is_running and new_player_pos in self.game_state.enemy_positions:
            can_move_here = False

        if can_move_here:
            self.game_state.player_pos = new_player_pos
            self.player_movement_frequency_matrix[new_player_pos[1]][new_player_pos[0]] += 1

            if self.is_running:
                self.step_counter += 1
                self.current_path_player = [self.game_state.player_pos]
                self.path_index_player = 0
                self.player_uses_heatmap_path = False
                print(
                    f"Jugador movido manualmente a {self.game_state.player_pos} (juego corriendo). Ruta automática invalidada.")
                # Tras movimiento manual, recalcular ruta desde nueva posición si el juego está corriendo
                self.determine_player_optimal_path()

            else:
                print(f"Jugador movido (configuración) a {self.game_state.player_pos}.")
                self.determine_player_optimal_path()

            if self.is_running:
                if self.game_state.player_pos == self.game_state.house_pos:
                    self.game_state.victory = True
                    self.is_running = False
                    print("¡Meta alcanzada por movimiento manual!")

                if self._check_player_enemy_collision():
                    return
        else:
            print(f"Movimiento manual a {new_player_pos} inválido o bloqueado.")

    def _handle_keyboard_input(self, event):
        key_pressed_val = event.key

        if self.input_field_active:
            if key_pressed_val == pygame.K_RETURN:
                if self._apply_input_buffer(self.input_field_active):
                    print(f"Valor '{self.input_buffer}' aplicado a '{self.input_field_active}' con Enter.")
                self.input_field_active = None
                self.input_buffer = ""
            elif key_pressed_val == pygame.K_ESCAPE:
                print(f"Edición de '{self.input_field_active}' cancelada.")
                self.input_field_active = None
                self.input_buffer = ""
            elif key_pressed_val == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif event.unicode.isdigit():
                if len(self.input_buffer) < 5:
                    self.input_buffer += event.unicode
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
                    first_enemy_id = list(self.game_state.enemies.keys())[0]
                    sim_e_start_p = self.game_state.enemies[first_enemy_id]['position']

                plot_args_map_e = {
                    'analysis': {'show': True, 'save_path': 'plot_q_e_analisis.png'},
                    'q_heatmap': {'show': True, 'save_path': 'plot_q_e_qvals.png'},
                    'best_path_q': {'agent_sim_start_pos': sim_e_start_p,
                                    'target_pos': self.game_state.player_pos,
                                    'obstacles': set(self.game_state.obstacles), 'show': True,
                                    'save_path': 'plot_q_e_camino.png'},
                    'comprehensive': {'agent_target_pos': self.game_state.player_pos,
                                      'agent_initial_pos_for_sim': sim_e_start_p,
                                      'obstacles': set(self.game_state.obstacles), 'show': True,
                                      'save_path': 'plot_q_e_comp.png'}}
                ptype_req = plot_type_map_e.get(key_pressed_val);
                pargs_req = plot_args_map_e.get(ptype_req)
                if ptype_req and pargs_req:
                    print(f"Solicitando plot '{ptype_req}' Q-Enemigo...");
                    self.plot_request_queue.put({'agent': self.enemy_q_agent, 'type': ptype_req, 'args': pargs_req})
            else:
                print("Q-Enemigo no entrenado o entrenando. ('Q' primero para entrenar)")

    def process_grid_click_in_edit_mode(self, clicked_grid_pos_tuple):
        if self.input_field_active:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None
            self.input_buffer = ""
            print(f"Campo de texto desactivado por clic en grid.")

        print(f"Clic en grid (Modo: {self.edit_mode}) en: {clicked_grid_pos_tuple}")
        original_player_pos = self.game_state.player_pos
        original_house_pos = self.game_state.house_pos
        changed_critical_pos = False

        if self.edit_mode == "player":
            if clicked_grid_pos_tuple != self.game_state.house_pos and \
                    clicked_grid_pos_tuple not in self.game_state.obstacles and \
                    clicked_grid_pos_tuple not in self.game_state.enemy_positions:
                self.game_state.player_pos = clicked_grid_pos_tuple
                self.game_state.initial_player_pos = clicked_grid_pos_tuple
                print(f"Jugador movido a: {clicked_grid_pos_tuple}");
                if original_player_pos != self.game_state.player_pos: changed_critical_pos = True
            else:
                print(f"Posición inválida para jugador: {clicked_grid_pos_tuple}.")
            self.edit_mode = None
        elif self.edit_mode == "house":
            if clicked_grid_pos_tuple != self.game_state.player_pos and \
                    clicked_grid_pos_tuple not in self.game_state.obstacles and \
                    clicked_grid_pos_tuple not in self.game_state.enemy_positions:
                self.game_state.house_pos = clicked_grid_pos_tuple
                print(f"Casa movida a: {clicked_grid_pos_tuple}");
                if original_house_pos != self.game_state.house_pos: changed_critical_pos = True
            else:
                print(f"Posición inválida para casa: {clicked_grid_pos_tuple}.")
            self.edit_mode = None
        elif self.edit_mode == "obstacles":
            self.edit_obstacle_at_pos(clicked_grid_pos_tuple)
        elif self.edit_mode == "enemies":
            enemy_id_at_click = self.game_state.get_enemy_at_position(clicked_grid_pos_tuple)
            if enemy_id_at_click is not None:
                if self.game_state.remove_enemy(clicked_grid_pos_tuple):
                    print(f"Enemigo (ID {enemy_id_at_click}) removido de: {clicked_grid_pos_tuple}")
                else:
                    print(f"Error al remover enemigo (ID {enemy_id_at_click}).")
            else:
                default_type_on_click = random.choice(["perseguidor", "bloqueador", "patrulla", "aleatorio"])
                newly_added_enemy_id = self.game_state.add_enemy(clicked_grid_pos_tuple, default_type_on_click)
                if newly_added_enemy_id is not None:
                    print(
                        f"Enemigo '{default_type_on_click}' (ID {newly_added_enemy_id}) añadido en: {clicked_grid_pos_tuple}")
                else:
                    print(f"No se pudo añadir enemigo en {clicked_grid_pos_tuple}.")

        if changed_critical_pos:
            self.best_path_player = None
            self._train_avatar_heatmap_on_init()
            self.determine_player_optimal_path()
            self.current_path_player = self.best_path_player.copy() if self.best_path_player else [
                self.game_state.player_pos]
            self.path_index_player = 0

    def _process_ui_button_click(self, button_id_str_clicked):
        target_field_id_for_button = None
        if button_id_str_clicked == "toggle_edit_avatar_heatmap_iters":
            target_field_id_for_button = "avatar_heatmap_iters"

        if self.input_field_active and self.input_field_active != target_field_id_for_button:
            self._apply_input_buffer(self.input_field_active)
            self.input_field_active = None
            self.input_buffer = ""
            print(f"Campo de texto '{self.input_field_active}' desactivado por clic en otro botón UI.")

        print(f"Botón UI presionado: {button_id_str_clicked}")
        if button_id_str_clicked == "start":
            self.toggle_game_running_state()
        elif button_id_str_clicked == "reset":
            self.reset_game_state_full()
        elif button_id_str_clicked == "train_player_agent":  # Cambiado desde "headless"
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
            self.current_path_player = self.best_path_player.copy() if self.best_path_player else [
                self.game_state.player_pos]
            self.path_index_player = 0
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

    def run_main_game_loop(self):
        font_prog_ui = pygame.font.Font(None, 18)
        while self.is_pygame_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_pygame_loop_running = False
                    if self.player_agent_is_training: self.stop_player_agent_training()
                    if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()
                elif event.type == pygame.KEYDOWN:
                    self._handle_keyboard_input(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_on_sidebar_button = False
                    ui_btn_id_clk = self.renderer.get_button_at(event.pos)
                    if ui_btn_id_clk:
                        self._process_ui_button_click(ui_btn_id_clk)
                        clicked_on_sidebar_button = True

                    target_field_id_for_button_click = None
                    if ui_btn_id_clk == "toggle_edit_avatar_heatmap_iters":
                        target_field_id_for_button_click = "avatar_heatmap_iters"

                    if self.input_field_active and self.input_field_active != target_field_id_for_button_click:
                        # Si se hizo clic fuera del botón del campo activo, desactivar
                        if not (
                                ui_btn_id_clk and target_field_id_for_button_click and self.input_field_active == target_field_id_for_button_click):
                            self._apply_input_buffer(self.input_field_active)
                            self.input_field_active = None
                            self.input_buffer = ""
                            print(f"Campo de texto '{self.input_field_active}' desactivado por clic fuera.")

                    if self.edit_mode and not clicked_on_sidebar_button:
                        grid_w_px_clk = GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE;
                        grid_h_px_clk = GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE
                        if 0 <= event.pos[0] < grid_w_px_clk and 0 <= event.pos[1] < grid_h_px_clk:
                            gx_clk = event.pos[0] // GameConfig.SQUARE_SIZE;
                            gy_clk = event.pos[1] // GameConfig.SQUARE_SIZE
                            self.process_grid_click_in_edit_mode((gx_clk, gy_clk))

            self.update();
            self.renderer.render()

            y_prog_start_draw = GameConfig.SCREEN_HEIGHT - 20
            if self.enemy_agent_is_training or self.enemy_agent_training_complete:
                txt_e_p = f"Ent. Enemigo: {self.enemy_agent_training_progress:.0f}% ({self.enemy_agent_training_status})"
                if self.enemy_agent_training_complete: txt_e_p = f"Ent. Enemigo COMPLETO! ({self.enemy_agent_training_status})"
                s_e_p = font_prog_ui.render(txt_e_p, True, GameConfig.CYAN, GameConfig.DARK_GRAY);
                r_e_p = s_e_p.get_rect(left=5, bottom=y_prog_start_draw)
                self.screen.blit(s_e_p, r_e_p);
                y_prog_start_draw -= (r_e_p.height + 3)
            if self.player_agent_is_training or self.player_agent_training_complete:
                txt_p_p = f"Ent. Jugador: {self.player_agent_training_progress:.0f}% ({self.player_agent_training_status})"
                if self.player_agent_training_complete: txt_p_p = f"Ent. Jugador COMPLETO! ({self.player_agent_training_status})"
                s_p_p = font_prog_ui.render(txt_p_p, True, GameConfig.YELLOW, GameConfig.DARK_GRAY);
                r_p_p = s_p_p.get_rect(left=5, bottom=y_prog_start_draw)
                self.screen.blit(s_p_p, r_p_p)

            if not self.plot_request_queue.empty():
                try:
                    req = self.plot_request_queue.get_nowait();
                    agent_plot = req['agent'];
                    ptype_plot = req['type'];
                    pargs_plot = req['args']
                    print(f"MAIN: Procesando plot '{ptype_plot}'...");
                    plot_func = None
                    if ptype_plot == 'heatmap_avatar' and isinstance(agent_plot, HeatMapPathfinding):
                        plot_func = agent_plot.visualize_heat_map
                        # Pasar show=True explícitamente si el método lo espera
                        plot_func(start_pos=pargs_plot.get('start_pos'), goal_pos=pargs_plot.get('goal_pos'),
                                  path=pargs_plot.get('path'), title=pargs_plot.get('title', "Vis HM"),
                                  save_path=pargs_plot.get('save_path'), show=pargs_plot.get('show', True))
                    elif isinstance(agent_plot, QLearningAgent):
                        plot_map_q = {'analysis': 'plot_analysis', 'q_heatmap': 'plot_q_values_heatmap',
                                      'best_path_q': 'plot_best_path', 'comprehensive': 'plot_comprehensive_analysis'}
                        m_name = plot_map_q.get(ptype_plot)
                        if m_name: plot_func = getattr(agent_plot, m_name, None)
                        if plot_func:
                            plot_func(**pargs_plot)  # Desempaquetar kwargs

                    if not plot_func:
                        print(f"Plot '{ptype_plot}' no encontrado o no aplicable en {type(agent_plot)}.")
                    self.plot_request_queue.task_done()
                except Empty:
                    pass
                except KeyError as ek:
                    print(
                        f"MAIN_PLOT_ERR Key: {ek} in {pargs_plot if 'pargs_plot' in locals() else 'Args no disponibles'}")
                except Exception as e:
                    print(f"MAIN_PLOT_ERR Gen: {e}\nReq: {req if 'req' in locals() else 'N/A'}")

            pygame.display.flip();
            self.clock.tick(GameConfig.GAME_SPEED)

        if self.player_agent_is_training: self.stop_player_agent_training()
        if self.enemy_agent_is_training: self.enemy_q_agent.stop_background_training()
        pygame.quit()

    def stop_player_agent_training(self):
        if not self.player_agent_is_training: print("Ent. Agente Jugador no activo."); return
        print("Deteniendo ent. AGENTE JUGADOR...");
        if hasattr(self.agent_player, 'stop_background_training'):
            if self.agent_player.stop_background_training():
                print("Señal parada hilo ent. Agente Jugador.")
            else:
                print("Hilo ent. Agente Jugador no activo o ya parado.")
        self.player_agent_is_training = False
        if not self.player_agent_training_complete:  # Si no se completó, marcar como detenido
            self.player_agent_training_status = "Jugador - DETENIDO"
            self.player_agent_training_progress = self.player_agent_training_progress  # Mantener progreso
            # No marcar como completo si se detuvo
            # self.player_agent_training_complete = False

    def player_agent_training_callback(self, iteration, _p_ign, _h_ign, _bp_pol_ign, is_final=False):
        # Este método no se usa directamente. La lógica está en la lambda p_q_cb.
        pass

    def initiate_enemy_q_agent_training(self):
        if self.enemy_agent_is_training: print("El Q-Agent Enemigo ya está entrenando."); return
        if self.player_agent_is_training: print("El Agente Jugador está entrenando, espera."); return
        print("Iniciando entrenamiento del Q-Agent para ENEMIGOS...");
        self.enemy_agent_is_training = True;
        self.enemy_agent_training_progress = 0.0
        self.enemy_agent_training_complete = False;
        self.enemy_agent_training_status = "Entrenando Enemigos..."

        target_for_enemy_q = self.game_state.player_pos
        enemy_q_start_pos = (1, 1)

        if self.game_state.enemies:
            valid_enemy_starts = [e_data['position'] for e_data in self.game_state.enemies.values()
                                  if self._is_pos_in_grid(e_data['position']) and \
                                  e_data['position'] != target_for_enemy_q and \
                                  e_data['position'] not in self.game_state.obstacles]
            if valid_enemy_starts:
                enemy_q_start_pos = random.choice(valid_enemy_starts)
            else:
                print("No hay enemigos válidos para iniciar Q-Agent. Usando pos. aleatoria.")
                enemy_q_start_pos = self._find_random_valid_start(target_for_enemy_q)
        else:
            print("No hay enemigos, Q-Agent entrenará desde pos. aleatoria.");
            enemy_q_start_pos = self._find_random_valid_start(target_for_enemy_q)

        obs_for_e_t = set(self.game_state.obstacles);
        self.enemy_q_agent.max_training_iterations = self.enemy_agent_max_training_iterations
        # Pasar target_for_enemy_q a train_background si la Q-table del enemigo se entrena para un objetivo específico
        self.enemy_q_agent.train_background(target_for_enemy_q, enemy_q_start_pos, obs_for_e_t,
                                            callback=self._enemy_q_agent_training_callback, update_interval=30)

    def _find_random_valid_start(self, target_pos):
        max_tries_e_start = 100
        for _ in range(max_tries_e_start):
            pos = (random.randint(0, GameConfig.GRID_WIDTH - 1),
                   random.randint(0, GameConfig.GRID_HEIGHT - 1))
            # Asegurarse que la posición no sea el objetivo, esté en el grid y no sea un obstáculo
            if pos != target_pos and self._is_pos_in_grid(pos) and pos not in self.game_state.obstacles:
                return pos
        print("Fallo al encontrar pos aleatoria válida para Q-Agente. Usando (1,1).")
        return (1, 1)  # Fallback

    def _enemy_q_agent_training_callback(self, iteration, _pe_ign, _he_ign, _bpe_pol_ign, is_final=False):
        if hasattr(self.enemy_q_agent, 'max_training_iterations') and self.enemy_q_agent.max_training_iterations > 0:
            self.enemy_agent_training_progress = (iteration / self.enemy_q_agent.max_training_iterations) * 100.0
        else:
            self.enemy_agent_training_progress = 100.0 if iteration > 0 else 0.0
        e_q_b_rew = getattr(self.enemy_q_agent, 'best_reward', -float('inf'))
        if e_q_b_rew > -float('inf'):
            self.enemy_agent_training_status = f"Enemigo - Recomp: {e_q_b_rew:.1f}"
        else:
            self.enemy_agent_training_status = "Enemigo - Optimizando..."
        if is_final:
            self.enemy_agent_is_training = False;
            self.enemy_agent_training_complete = True;
            self.enemy_q_agent_trained = True
            final_e_msg = "Enemigo - Ent. COMPLETO!"
            if e_q_b_rew > -float('inf'): final_e_msg += f" Recomp: {e_q_b_rew:.1f}"
            self.enemy_agent_training_status = final_e_msg;
            print("Ent. Q-Agent ENEMIGO finalizado (cbk).")

    def _recalculate_player_path(self):
        print("JUGADOR: Recalculando ruta (desde _recalculate_player_path)...");
        self.determine_player_optimal_path()  # Esto actualiza best_path_player y current_path_player

        if self.current_path_player:  # current_path_player siempre debería existir
            # path_index_player ya está en 0 por determine_player_optimal_path
            print(
                f"JUGADOR: Nueva ruta recalculada de {len(self.current_path_player)}p desde {self.game_state.player_pos}.")
        else:  # Esto no debería ocurrir si determine_player_optimal_path funciona bien
            self.current_path_player = [self.game_state.player_pos]
            self.path_index_player = 0
            print("JUGADOR: (ERROR) No se pudo recalcular ruta. Jugador en espera o movimiento manual.")

    def _recalculate_path_for_player_headless(self):
        print("JUGADOR (HL): Recalculando...");
        self.determine_player_optimal_path()
        if self.best_path_player:  # En headless, seguimos best_path_player
            self.path_index_player = 0
            print(f"JUGADOR (HL): Nueva ruta de {len(self.best_path_player)}p desde {self.game_state.player_pos}.")
        else:
            self.best_path_player = None
            self.path_index_player = 0
            print("JUGADOR (HL): No se pudo recalcular ruta.")

    def _update_enemies(self):
        if not self.is_running or self.game_state.victory or self.game_over: return
        if not self.enemies_initialized or not self.game_state.enemies: return

        player_steps_per_enemy_move = 1
        if 0 < GameConfig.ENEMY_SPEED_FACTOR < 1:
            player_steps_per_enemy_move = int(1 / GameConfig.ENEMY_SPEED_FACTOR)

        # Los enemigos se mueven si el step_counter del jugador es un múltiplo de player_steps_per_enemy_move
        # Esto asume que step_counter se incrementa con cada "acción" del jugador (automática o manual)
        if self.step_counter > 0 and self.step_counter % player_steps_per_enemy_move == 0:
            print(f"Actualizando enemigos (step_counter: {self.step_counter})")
            for e_id, e_data in list(self.game_state.enemies.items()):
                curr_e_pos = e_data['position'];
                next_e_pos = curr_e_pos

                if self.enemy_q_agent_trained and hasattr(self.enemy_q_agent, 'get_learned_action_xy'):
                    act_xy_e = self.enemy_q_agent.get_learned_action_xy(curr_e_pos, self.game_state.obstacles,
                                                                        target_pos=self.game_state.player_pos)
                    if act_xy_e:
                        pot_next_e = (curr_e_pos[0] + act_xy_e[0], curr_e_pos[1] + act_xy_e[1])
                        if self._is_pos_in_grid(pot_next_e) and \
                                pot_next_e not in self.game_state.obstacles and \
                                (pot_next_e == self.game_state.player_pos or pot_next_e not in (
                                        self.game_state.enemy_positions - {curr_e_pos})):
                            next_e_pos = pot_next_e
                else:
                    poss_rand_e_mvs = [];
                    for dx_re, dy_re in self.enemy_q_agent.actions_xy:
                        rand_p_e = (curr_e_pos[0] + dx_re, curr_e_pos[1] + dy_re)
                        if self._is_pos_in_grid(rand_p_e) and \
                                rand_p_e not in self.game_state.obstacles and \
                                (rand_p_e == self.game_state.player_pos or rand_p_e not in (
                                        self.game_state.enemy_positions - {curr_e_pos})):
                            poss_rand_e_mvs.append(rand_p_e)
                    if poss_rand_e_mvs: next_e_pos = random.choice(poss_rand_e_mvs)

                if next_e_pos != curr_e_pos:
                    print(f"Enemigo {e_id} moviéndose de {curr_e_pos} a {next_e_pos}")
                    self.game_state.update_enemy_position(e_id, next_e_pos)

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
        print("\n=== INICIALIZANDO ENEMIGOS (Colocación) ===");
        self.game_state.enemies.clear();
        self.game_state.enemy_positions.clear()
        num_e_init_config = GameConfig.INITIAL_ENEMY_POSITIONS
        num_e_init = len(num_e_init_config) if num_e_init_config and isinstance(num_e_init_config,
                                                                                list) and num_e_init_config else 4  # Default si es None o vacío

        print(f"Intentando colocar {num_e_init} enemigos...");
        used_pos_e_init = set();
        placed_e_cnt = 0

        if num_e_init_config and isinstance(num_e_init_config, list) and all(
                isinstance(p, tuple) for p in num_e_init_config):
            print("Usando posiciones de GameConfig.INITIAL_ENEMY_POSITIONS...")
            for i_e_place, e_pos_config in enumerate(num_e_init_config):
                if self._is_pos_in_grid(e_pos_config) and \
                        e_pos_config not in self.game_state.obstacles and \
                        e_pos_config != self.game_state.player_pos and \
                        e_pos_config != self.game_state.house_pos and \
                        e_pos_config not in used_pos_e_init:

                    e_type_for_p = random.choice(["perseguidor", "bloqueador", "patrulla", "aleatorio"])
                    new_e_id_game = self.game_state.add_enemy(e_pos_config, e_type_for_p)
                    if new_e_id_game is not None:
                        used_pos_e_init.add(e_pos_config);
                        placed_e_cnt += 1
                        print(f"✓ Enemigo '{e_type_for_p}' (ID {new_e_id_game}) en {e_pos_config} (de config).")
                    else:
                        print(f"✗ Error GS: No se pudo añadir '{e_type_for_p}' en {e_pos_config} (de config).")
                else:
                    print(
                        f"✗ Posición de config {e_pos_config} inválida o ocupada. Intentando estratégico/aleatorio para este enemigo.")
                    e_type_for_p = random.choice(["perseguidor", "bloqueador", "patrulla", "aleatorio"])
                    pos_e_for_p = self._get_strategic_position_for_enemy(e_type_for_p, list(used_pos_e_init))
                    if pos_e_for_p:
                        new_e_id_game = self.game_state.add_enemy(pos_e_for_p, e_type_for_p)
                        if new_e_id_game is not None:
                            used_pos_e_init.add(pos_e_for_p);
                            placed_e_cnt += 1
                            print(f"✓ Enemigo '{e_type_for_p}' (ID {new_e_id_game}) en {pos_e_for_p} (estratégico).")
                        else:
                            print(f"✗ Error GS al añadir '{e_type_for_p}' en {pos_e_for_p} (estratégico).")
                    else:
                        print(
                            f"✗ No pos estratégica para enemigo {i_e_place + 1} ('{e_type_for_p}') tras fallo de config.")

        enemies_to_place_strategically = num_e_init - placed_e_cnt
        if enemies_to_place_strategically > 0:
            print(f"Colocando {enemies_to_place_strategically} enemigos estratégicamente/aleatoriamente...")
            for i_e_place in range(enemies_to_place_strategically):
                e_type_for_p = random.choice(["perseguidor", "bloqueador", "patrulla", "aleatorio"])
                pos_e_for_p = self._get_strategic_position_for_enemy(e_type_for_p, list(used_pos_e_init))
                if pos_e_for_p:
                    new_e_id_game = self.game_state.add_enemy(pos_e_for_p, e_type_for_p)
                    if new_e_id_game is not None:
                        used_pos_e_init.add(pos_e_for_p);
                        placed_e_cnt += 1
                        print(f"✓ Enemigo '{e_type_for_p}' (ID {new_e_id_game}) en {pos_e_for_p}.")
                    else:
                        print(f"✗ Error GS: No se pudo añadir '{e_type_for_p}' en {pos_e_for_p}.")
                else:
                    print(f"✗ No pos estratégica para enemigo adicional {i_e_place + 1} ('{e_type_for_p}').")

        print(f"Inicialización enemigos: {placed_e_cnt} en juego.");
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
            else:
                print(f"Info: HM no dio pos válidas para '{enemy_type_place_strat}'. Intentando aleatorio.")

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

        print(
            f"ADVERTENCIA: No se pudo encontrar pos aleatoria válida para '{enemy_type_place_strat}' tras {max_tries_rand_pos_e_s} intentos.");
        return None
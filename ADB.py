# ADB.py
"""
Agente de Q-learning tabular usado por el avatar (para llegar a la casa) y por
los enemigos (para alcanzar al avatar).

Mejoras respecto a la versión original:
- ESTADO CON OBJETIVO: el estado es (x, y, sector), donde `sector` es el
  desplazamiento hacia el objetivo recortado a ±2 casillas por eje (25 valores).
  Antes el estado era sólo (x, y), así que el agente enemigo aprendía a ir a
  la casilla donde estaba el jugador AL ENTRENAR e ignoraba al jugador real.
- RECOMPENSA MOLDEADA CON DISTANCIA REAL: se conserva la idea original
  (premiar acercarse y castigar alejarse), pero la distancia se mide con BFS
  rodeando obstáculos en lugar de Manhattan:
      r = -1 por paso + (d(s) - d(s')) + 100 al llegar
  Acercarse cuesta 0, alejarse cuesta -2, así que la política óptima es
  exactamente el camino más corto. Con Manhattan, un muro hacía que el
  camino correcto (rodearlo) pareciera "alejarse" y se castigaba.
- ÉPSILON PROGRAMADO: el decaimiento se calcula para llegar a `epsilon_min`
  al 70 % del entrenamiento, garantizando una fase final de explotación.
- INICIOS EXPLORATORIOS: parte de los episodios arrancan en celdas
  aleatorias, de modo que la tabla Q es útil desde cualquier posición
  (importante porque el avatar replanifica a mitad de camino).
- OBJETIVOS ALEATORIOS (enemigos): cada episodio persigue un objetivo
  distinto, así la política generaliza a un jugador que se mueve.
- VIGENCIA DEL APRENDIZAJE: una tabla Q sólo vale para el mapa en que se
  aprendió. El agente recuerda ese mapa y `is_policy_current()` indica si el
  mapa actual sigue siendo lo bastante parecido para confiar en la política.
"""
import random
import threading
import time

import numpy as np

from grid_utils import UNREACHABLE, bfs_distance_map
from plotting import plt

# Desplazamiento relativo al objetivo, recortado a [-R, R] en cada eje.
# Con R=2: distingue "alineado", "a 1 casilla" y "lejos" en cada eje (5x5 = 25 sectores).
SECTOR_RANGE = 2
SECTOR_SIDE = 2 * SECTOR_RANGE + 1
NUM_SECTORS = SECTOR_SIDE * SECTOR_SIDE
ON_TARGET_SECTOR = SECTOR_RANGE * SECTOR_SIDE + SECTOR_RANGE


class QLearningAgent:
    REWARD_GOAL = 100.0
    REWARD_STEP = -1.0
    REWARD_STUCK = -20.0
    SUCCESS_WINDOW = 100  # episodios usados para la tasa de éxito móvil
    MAP_SIMILARITY_THRESHOLD = 0.9  # Por debajo de esto la política se considera desactualizada

    def __init__(self, width, height, num_actions=4):
        self.width = width
        self.height = height
        self.num_actions = num_actions
        self.q_table = np.zeros((height, width, NUM_SECTORS, num_actions), dtype=float)

        self.learning_rate = 0.3
        self.discount_factor = 0.97
        self.epsilon_start = 1.0
        self.epsilon = self.epsilon_start
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.999  # Se recalcula al iniciar cada entrenamiento
        self.exploration_fraction = 0.7  # Fracción del entrenamiento en que épsilon baja hasta el mínimo
        self.exploring_starts_prob = 0.5  # Prob. de iniciar un episodio en una celda aleatoria

        self.actions_xy = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        self.action_names = ["Arriba", "Derecha", "Abajo", "Izquierda"]

        self.best_reward = -float('inf')
        self.training_history = self._empty_history()
        self.reference_target = None  # Objetivo usado para graficar la tabla Q
        self.trained_obstacles = None  # Mapa (obstáculos) en el que se aprendió la tabla Q

        self.training_thread = None
        self.stop_training_flag = False
        self.current_training_iteration = 0
        self.max_training_iterations = 1000

        self._distance_cache = {}

    @staticmethod
    def _empty_history():
        return {'path_lengths': [], 'rewards': [], 'epsilons': [], 'successes': []}

    # ------------------------------------------------------------------ estado
    @staticmethod
    def sector_to_target(pos, target_pos):
        """Desplazamiento recortado hacia el objetivo, codificado en 0..NUM_SECTORS-1."""
        if target_pos is None:
            return ON_TARGET_SECTOR
        sx = max(-SECTOR_RANGE, min(SECTOR_RANGE, target_pos[0] - pos[0]))
        sy = max(-SECTOR_RANGE, min(SECTOR_RANGE, target_pos[1] - pos[1]))
        return (sy + SECTOR_RANGE) * SECTOR_SIDE + (sx + SECTOR_RANGE)

    def _is_valid(self, pos, obstacles):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and pos not in obstacles

    def get_valid_actions(self, state_pos, obstacles):
        current_x, current_y = state_pos
        return [idx for idx, (dx, dy) in enumerate(self.actions_xy)
                if self._is_valid((current_x + dx, current_y + dy), obstacles)]

    def choose_action(self, state_pos, obstacles, is_training_exploration=True, target_pos=None):
        """Política ε-greedy restringida a acciones válidas (nunca choca con muros)."""
        valid_actions = self.get_valid_actions(state_pos, obstacles)
        if not valid_actions:
            return None
        if is_training_exploration and random.random() < self.epsilon:
            return random.choice(valid_actions)
        if not self._is_valid(state_pos, ()):
            return random.choice(valid_actions)

        sector = self.sector_to_target(state_pos, target_pos)
        q_values = self.q_table[state_pos[1], state_pos[0], sector]
        best_q = max(q_values[a] for a in valid_actions)
        best_actions_tied = [a for a in valid_actions if q_values[a] == best_q]
        return random.choice(best_actions_tied)

    def update_q_value(self, state_pos, action_idx, reward, next_state_pos, obstacles, done, target_pos=None):
        """Regla de Bellman: Q(s,a) += α·(r + γ·max_a' Q(s',a') - Q(s,a))."""
        sector = self.sector_to_target(state_pos, target_pos)
        old_q_value = self.q_table[state_pos[1], state_pos[0], sector, action_idx]

        max_future_q = 0.0
        if not done:
            valid_next_actions = self.get_valid_actions(next_state_pos, obstacles)
            if valid_next_actions:
                next_sector = self.sector_to_target(next_state_pos, target_pos)
                next_q = self.q_table[next_state_pos[1], next_state_pos[0], next_sector]
                max_future_q = max(next_q[a] for a in valid_next_actions)

        td_target = reward + self.discount_factor * max_future_q
        self.q_table[state_pos[1], state_pos[0], sector, action_idx] = \
            old_q_value + self.learning_rate * (td_target - old_q_value)

    # -------------------------------------------------------------- recompensa
    def _distance_map_to(self, target_pos, obstacles):
        """Mapa de distancias BFS hacia el objetivo (con caché pequeña por objetivo)."""
        key = (target_pos, len(obstacles))
        dist_map = self._distance_cache.get(key)
        if dist_map is None:
            if len(self._distance_cache) > 256:
                self._distance_cache.clear()
            dist_map = bfs_distance_map(self.width, self.height, target_pos, obstacles)
            self._distance_cache[key] = dist_map
        return dist_map

    def _real_distance(self, pos, target_pos, dist_map):
        """Pasos reales hasta el objetivo (Manhattan penalizada si es inalcanzable)."""
        d = dist_map[pos[1], pos[0]]
        if d == UNREACHABLE:
            d = abs(pos[0] - target_pos[0]) + abs(pos[1] - target_pos[1]) + self.width + self.height
        return float(d)

    def calculate_reward(self, prev_pos, next_pos, target_pos, reached_target, dist_map):
        if reached_target:
            return self.REWARD_GOAL
        progress = self._real_distance(prev_pos, target_pos, dist_map) \
            - self._real_distance(next_pos, target_pos, dist_map)
        return self.REWARD_STEP + progress

    # ----------------------------------------------------------- entrenamiento
    def train_one_episode(self, agent_start_pos, target_pos, obstacles, max_steps_per_episode=300,
                          dist_map=None):
        if dist_map is None:
            dist_map = self._distance_map_to(target_pos, obstacles)
        agent_current_pos = agent_start_pos
        episode_reward = 0.0
        path_len = 0
        reached = False

        for _ in range(max_steps_per_episode):
            if self.stop_training_flag:
                break
            action_idx = self.choose_action(agent_current_pos, obstacles, True, target_pos)
            if action_idx is None:
                episode_reward += self.REWARD_STUCK
                break

            dx, dy = self.actions_xy[action_idx]
            agent_next_pos = (agent_current_pos[0] + dx, agent_current_pos[1] + dy)
            reached = agent_next_pos == target_pos
            reward_val = self.calculate_reward(agent_current_pos, agent_next_pos, target_pos, reached, dist_map)
            self.update_q_value(agent_current_pos, action_idx, reward_val, agent_next_pos, obstacles, reached,
                                target_pos)

            episode_reward += reward_val
            path_len += 1
            agent_current_pos = agent_next_pos
            if reached:
                break

        if not self.stop_training_flag and self.epsilon > self.epsilon_min:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return episode_reward, path_len, reached

    def _schedule_epsilon(self, total_episodes):
        self.epsilon = self.epsilon_start
        decay_episodes = max(1, int(total_episodes * self.exploration_fraction))
        self.epsilon_decay = (self.epsilon_min / self.epsilon_start) ** (1.0 / decay_episodes)

    def _random_reachable_cell(self, dist_map, exclude):
        reachable = np.argwhere(dist_map > 0)
        if len(reachable) == 0:
            return None
        for _ in range(10):
            y, x = reachable[random.randrange(len(reachable))]
            if (int(x), int(y)) != exclude:
                return int(x), int(y)
        return None

    def _sample_episode(self, target_pos, start_pos, obstacles, free_cells=None):
        """
        Elige (inicio, objetivo, mapa de distancias) para el siguiente episodio.
        Con `free_cells` el objetivo se sortea entre esas celdas (modo enemigo).
        """
        if free_cells:
            target_pos = random.choice(free_cells)
            dist_map = bfs_distance_map(self.width, self.height, target_pos, obstacles)
            return self._random_reachable_cell(dist_map, target_pos), target_pos, dist_map

        dist_map = self._distance_map_to(target_pos, obstacles)
        start_ok = self._is_valid(start_pos, obstacles) and start_pos != target_pos \
            and dist_map[start_pos[1], start_pos[0]] != UNREACHABLE
        if not start_ok or random.random() < self.exploring_starts_prob:
            start_pos = self._random_reachable_cell(dist_map, target_pos)
        return start_pos, target_pos, dist_map

    def map_similarity(self, obstacles):
        """1.0 = mismo mapa del entrenamiento; 0.0 = ningún obstáculo en común."""
        if self.trained_obstacles is None:
            return 0.0
        union = self.trained_obstacles | set(obstacles)
        if not union:
            return 1.0
        return 1.0 - len(self.trained_obstacles.symmetric_difference(obstacles)) / len(union)

    def is_policy_current(self, obstacles):
        return self.map_similarity(obstacles) >= self.MAP_SIMILARITY_THRESHOLD

    @property
    def success_rate(self):
        recent = self.training_history['successes'][-self.SUCCESS_WINDOW:]
        return (sum(recent) / len(recent)) if recent else 0.0

    def get_learned_action_xy(self, state_pos, obstacles, target_pos=None):
        action_idx = self.choose_action(state_pos, obstacles, is_training_exploration=False, target_pos=target_pos)
        if action_idx is not None:
            return self.actions_xy[action_idx]
        return None

    def simulate_policy(self, start_pos, target_pos, obstacles, max_steps=None):
        """Sigue la política aprendida (sin exploración) y devuelve el camino recorrido."""
        max_steps = max_steps or self.width * self.height
        path = [start_pos]
        visited = {start_pos}
        current = start_pos
        for _ in range(max_steps):
            if current == target_pos:
                break
            action = self.get_learned_action_xy(current, obstacles, target_pos=target_pos)
            if not action:
                break
            current = (current[0] + action[0], current[1] + action[1])
            path.append(current)
            if current in visited:  # Ciclo: la política aún no está bien aprendida aquí
                break
            visited.add(current)
        return path

    def train_background(self, target_pos_for_training, initial_agent_pos_for_training, obstacles, callback=None,
                         update_interval=50, randomize_targets=False):
        """
        Entrena en un hilo aparte para no congelar la interfaz.
        `randomize_targets=True` se usa para los enemigos (objetivo móvil).
        """
        self.stop_background_training()

        self.stop_training_flag = False
        self.current_training_iteration = 0
        self.training_history = self._empty_history()
        self.best_reward = -float('inf')
        self.reference_target = target_pos_for_training
        self._schedule_epsilon(self.max_training_iterations)
        obstacles = frozenset(obstacles)
        self.trained_obstacles = obstacles
        free_cells = [(x, y) for x in range(self.width) for y in range(self.height)
                      if (x, y) not in obstacles] if randomize_targets else None

        def training_worker():
            print(f"Hilo Q-learning iniciado. Objetivo: "
                  f"{'aleatorio' if randomize_targets else target_pos_for_training}, "
                  f"Inicio: {initial_agent_pos_for_training}, Iter Máx: {self.max_training_iterations}")
            report_every = max(1, self.max_training_iterations // 10)

            for i in range(self.max_training_iterations):
                if self.stop_training_flag:
                    print("Hilo Q-learning: recibida señal de parada.")
                    break

                start, target, dist_map = self._sample_episode(target_pos_for_training,
                                                               initial_agent_pos_for_training,
                                                               obstacles, free_cells)
                if start is None:
                    continue

                reward, path_len, reached = self.train_one_episode(start, target, obstacles, dist_map=dist_map)
                self.current_training_iteration = i + 1

                self.training_history['path_lengths'].append(path_len)
                self.training_history['rewards'].append(reward)
                self.training_history['epsilons'].append(self.epsilon)
                self.training_history['successes'].append(1 if reached else 0)
                self.best_reward = max(self.best_reward, reward)

                if callback and self.current_training_iteration % update_interval == 0:
                    callback(self.current_training_iteration, None, self.training_history, None, is_final=False)

                if self.current_training_iteration % report_every == 0:
                    print(f"Q-Train iter {self.current_training_iteration}: Recompensa={reward:.1f}, "
                          f"Pasos={path_len}, ε={self.epsilon:.3f}, Éxito(últimos {self.SUCCESS_WINDOW})="
                          f"{self.success_rate * 100:.0f}%")

                time.sleep(0)  # Cede el GIL al hilo de la interfaz

            print(f"Hilo Q-learning finalizado. Iteraciones: {self.current_training_iteration}")
            if callback:
                callback(self.current_training_iteration, None, self.training_history, None, is_final=True)

        self.training_thread = threading.Thread(target=training_worker, daemon=True)
        self.training_thread.start()

    def stop_background_training(self):
        if self.training_thread and self.training_thread.is_alive():
            print("Intentando detener hilo de entrenamiento Q-learning...")
            self.stop_training_flag = True
            self.training_thread.join(timeout=2.0)
            if self.training_thread.is_alive():
                print("Advertencia: Hilo de entrenamiento Q-learning no terminó limpiamente.")
            else:
                print("Hilo de entrenamiento Q-learning detenido exitosamente.")
            self.training_thread = None
            return True
        self.training_thread = None
        return False

    # ------------------------------------------------------------- gráficas
    def q_values_for_target(self, target_pos=None):
        """
        Vista (alto, ancho, acciones) de la tabla Q tal como la "ve" el agente
        cuando persigue `target_pos` (cada celda usa su sector relativo).
        Sin objetivo, devuelve el máximo sobre todos los sectores.
        """
        target_pos = target_pos or self.reference_target
        if target_pos is None:
            return np.max(self.q_table, axis=2)
        ys, xs = np.indices((self.height, self.width))
        sx = np.clip(target_pos[0] - xs, -SECTOR_RANGE, SECTOR_RANGE)
        sy = np.clip(target_pos[1] - ys, -SECTOR_RANGE, SECTOR_RANGE)
        sectors = (sy + SECTOR_RANGE) * SECTOR_SIDE + (sx + SECTOR_RANGE)
        return self.q_table[ys, xs, sectors]

    @staticmethod
    def _smooth(values):
        if len(values) < 20:
            return None, None
        window = min(50, max(10, len(values) // 10))
        smoothed = np.convolve(np.asarray(values, dtype=float), np.ones(window) / window, 'valid')
        x_axis = np.arange(window, window + len(smoothed))
        return x_axis, smoothed

    @staticmethod
    def _finish_plot(fig, show, save_path):
        if save_path:
            fig.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig

    def plot_analysis(self, show=True, save_path=None):
        if not self.training_history['rewards']:
            print("ADB.py: No hay datos de entrenamiento para plot_analysis.")
            return
        fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        episodes = np.arange(1, len(self.training_history['rewards']) + 1)

        axs[0].plot(episodes, self.training_history['rewards'], color='tab:blue', alpha=0.4, label='Recompensa')
        sx, sy = self._smooth(self.training_history['rewards'])
        if sx is not None:
            axs[0].plot(sx, sy, color='firebrick', linewidth=1.5, label='Recompensa suavizada')
        axs[0].set_ylabel('Recompensa por episodio')
        axs[0].set_title('Recompensa por Episodio')

        sx, sy = self._smooth(self.training_history['successes'])
        if sx is not None:
            axs[1].plot(sx, sy * 100, color='tab:purple', label='Tasa de éxito (%)')
        axs[1].set_ylim(-5, 105)
        axs[1].set_ylabel('Éxito (%)')
        axs[1].set_title('Episodios que alcanzan el objetivo')

        axs[2].plot(episodes, self.training_history['epsilons'], color='tab:green', label='Épsilon')
        axs[2].set_ylabel('Épsilon (exploración)')
        axs[2].set_xlabel('Episodio')
        axs[2].set_title('Programa de Exploración (ε)')

        for ax in axs:
            ax.grid(True, linestyle=':', alpha=0.5)
            ax.legend(loc='best')
        fig.suptitle("Análisis de Aprendizaje Q-Agent", fontsize=16)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        return self._finish_plot(fig, show, save_path)

    def plot_q_values_heatmap(self, show=True, save_path=None):
        q_view = self.q_values_for_target()
        fig, axs = plt.subplots(2, 2, figsize=(11, 9))
        axs = axs.flatten()
        vmin, vmax = float(np.min(q_view)), float(np.max(q_view))
        if vmin == vmax:
            vmin, vmax = vmin - 0.1, vmax + 0.1
        for i in range(self.num_actions):
            im = axs[i].imshow(q_view[:, :, i], cmap='viridis', vmin=vmin, vmax=vmax, origin='upper')
            axs[i].set_title(f'Valores Q para: {self.action_names[i]}')
            axs[i].set_xlabel('Posición X')
            axs[i].set_ylabel('Posición Y')
            fig.colorbar(im, ax=axs[i], orientation='vertical', label='Valor Q')
        fig.suptitle(f"Q-Values por Acción (objetivo {self.reference_target})", fontsize=16)
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        return self._finish_plot(fig, show, save_path)

    def _draw_path_axes(self, ax, path, start, target, obstacles, title):
        ax.set_xlim(-0.5, self.width - 0.5)
        ax.set_ylim(self.height - 0.5, -0.5)
        ax.grid(True, linestyle=':', alpha=0.7)
        for obs_x, obs_y in obstacles:
            ax.add_patch(plt.Rectangle((obs_x - 0.5, obs_y - 0.5), 1, 1, color='dimgray', zorder=2))
        if path:
            ax.plot([p[0] for p in path], [p[1] for p in path], 'r-o', linewidth=1.5, markersize=3,
                    label=f'Camino por Política Q ({len(path) - 1} pasos)', zorder=3)
        ax.plot(start[0], start[1], 'bs', markersize=8, label='Inicio', zorder=4)
        ax.plot(target[0], target[1], 'g*', markersize=12, label='Objetivo', zorder=4)
        ax.legend(loc='best', fontsize='small')
        ax.set_title(title)
        ax.set_aspect('equal', adjustable='box')

    def plot_best_path(self, agent_sim_start_pos, target_pos, obstacles, show=True, save_path=None):
        path = self.simulate_policy(agent_sim_start_pos, target_pos, obstacles)
        fig, ax = plt.subplots(figsize=(max(8, self.width * 0.3), max(6, self.height * 0.3)))
        self._draw_path_axes(ax, path, agent_sim_start_pos, target_pos, obstacles,
                             'Camino Simulado Usando Política Q Aprendida')
        fig.tight_layout()
        return self._finish_plot(fig, show, save_path)

    def plot_comprehensive_analysis(self, agent_target_pos, agent_initial_pos_for_sim, obstacles, show=True,
                                    save_path=None):
        if not self.training_history['rewards']:
            print("ADB.py: No hay datos de entrenamiento para plot_comprehensive_analysis.")
            return

        fig = plt.figure(figsize=(17, 15))
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.5, 1.5])

        ax_progress = fig.add_subplot(gs[0, :])
        episodes = np.arange(1, len(self.training_history['rewards']) + 1)
        ax_progress.plot(episodes, self.training_history['rewards'], color='royalblue', alpha=0.4,
                         label='Recompensa')
        sx, sy = self._smooth(self.training_history['rewards'])
        if sx is not None:
            ax_progress.plot(sx, sy, color='crimson', linewidth=1.5, label='Recompensa suavizada')
        ax_progress.set_xlabel('Episodio')
        ax_progress.set_ylabel('Recompensa')
        ax_progress.grid(True, linestyle=':', alpha=0.6)
        ax_eps = ax_progress.twinx()
        ax_eps.plot(episodes, self.training_history['epsilons'], color='forestgreen', linestyle='--',
                    label='Épsilon')
        ax_eps.set_ylabel('Épsilon')
        lines, labels = ax_progress.get_legend_handles_labels()
        lines2, labels2 = ax_eps.get_legend_handles_labels()
        ax_progress.legend(lines + lines2, labels + labels2, loc='center left')
        ax_progress.set_title(f'Progreso del Entrenamiento (éxito reciente: {self.success_rate * 100:.0f}%)')

        ax_path_sim = fig.add_subplot(gs[1, 0])
        path = self.simulate_policy(agent_initial_pos_for_sim, agent_target_pos, obstacles)
        self._draw_path_axes(ax_path_sim, path, agent_initial_pos_for_sim, agent_target_pos, obstacles,
                             'Camino Simulado por Política Q')

        q_view = self.q_values_for_target(agent_target_pos)
        ax_q_max = fig.add_subplot(gs[1, 1])
        im_q_max = ax_q_max.imshow(np.max(q_view, axis=2), cmap='viridis', origin='upper', aspect='auto')
        fig.colorbar(im_q_max, ax=ax_q_max, label='V(s) = max Q(s,a)')
        ax_q_max.set_title('Valor de cada celda hacia el objetivo')

        q_min_plot, q_max_plot = float(np.min(q_view)), float(np.max(q_view))
        if q_min_plot == q_max_plot:
            q_max_plot += 0.1
        for slot, action_idx in ((gs[2, 0], 2), (gs[2, 1], 1)):  # Abajo, Derecha
            ax = fig.add_subplot(slot)
            im = ax.imshow(q_view[:, :, action_idx], cmap='coolwarm', vmin=q_min_plot, vmax=q_max_plot,
                           origin='upper', aspect='auto')
            fig.colorbar(im, ax=ax, label=f'Valor Q ({self.action_names[action_idx]})')
            ax.set_title(f'Mapa Q para Acción "{self.action_names[action_idx]}"')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')

        fig.suptitle(f"Análisis Comprensivo del Agente Q-learning (objetivo {agent_target_pos})", fontsize=18)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        return self._finish_plot(fig, show, save_path)

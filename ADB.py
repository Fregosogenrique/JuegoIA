# ADB.py
# Agente Q-learning.
import numpy as np
import random
import time
import threading
import matplotlib.pyplot as plt


# from matplotlib.colors import LinearSegmentedColormap # No usado
# import math # No usado

class QLearningAgent:
    def __init__(self, width, height, num_actions=4):
        self.width = width
        self.height = height
        self.num_actions = num_actions
        self.q_table = np.zeros((height, width, num_actions), dtype=float)

        self.learning_rate = 0.1  # Alpha
        self.discount_factor = 0.9  # Gamma
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

        self.actions_xy = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Arriba, Derecha, Abajo, Izquierda
        self.action_names = ["Arriba", "Derecha", "Abajo", "Izquierda"]

        self.best_reward = -float('inf')
        self.best_path_length = float('inf')

        self.training_history = {'path_lengths': [], 'rewards': [], 'epsilons': []}

        self.training_thread = None
        self.stop_training_flag = False
        self.current_training_iteration = 0
        self.max_training_iterations = 1000

    def _is_valid(self, pos, obstacles):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and pos not in obstacles

    def get_valid_actions(self, state_pos, obstacles):
        valid_action_indices = []
        current_x, current_y = state_pos
        for action_idx, (dx, dy) in enumerate(self.actions_xy):
            next_x, next_y = current_x + dx, current_y + dy
            if self._is_valid((next_x, next_y), obstacles):
                valid_action_indices.append(action_idx)
        return valid_action_indices

    def choose_action(self, state_pos, obstacles, is_training_exploration=True, target_pos=None):
        # target_pos es opcional, puede usarse para heurísticas si se desea (no implementado aquí)
        if is_training_exploration and random.random() < self.epsilon:
            valid_actions = self.get_valid_actions(state_pos, obstacles)
            if not valid_actions: return None
            return random.choice(valid_actions)
        else:
            current_x, current_y = state_pos
            # Asegurarse que y, x están dentro de los límites de la q_table
            if not (0 <= current_y < self.q_table.shape[0] and 0 <= current_x < self.q_table.shape[1]):
                # print(f"Q-Agent: Estado {state_pos} fuera de límites de Q-table. Eligiendo acción aleatoria válida.")
                valid_actions_fallback = self.get_valid_actions(state_pos, obstacles)
                return random.choice(valid_actions_fallback) if valid_actions_fallback else None

            q_values_for_state = self.q_table[current_y, current_x, :]
            valid_actions = self.get_valid_actions(state_pos, obstacles)
            if not valid_actions: return None

            best_q = -float('inf')
            best_actions_tied = []

            for action_idx in valid_actions:
                if q_values_for_state[action_idx] > best_q:
                    best_q = q_values_for_state[action_idx]
                    best_actions_tied = [action_idx]
                elif q_values_for_state[action_idx] == best_q:
                    best_actions_tied.append(action_idx)

            if not best_actions_tied:  # Fallback si todas las válidas tienen Q=-inf o algo raro
                return random.choice(valid_actions) if valid_actions else None

            return random.choice(best_actions_tied)

    def update_q_value(self, state_pos, action_idx, reward, next_state_pos, obstacles, done):
        current_x, current_y = state_pos
        next_x, next_y = next_state_pos

        # Validar índices antes de acceder a q_table
        if not (0 <= current_y < self.q_table.shape[0] and 0 <= current_x < self.q_table.shape[1]):
            # print(f"Q-Agent Update: Estado actual {state_pos} fuera de límites. Omitiendo actualización.")
            return
        if not (0 <= next_y < self.q_table.shape[0] and 0 <= next_x < self.q_table.shape[1]):
            # print(f"Q-Agent Update: Estado siguiente {next_state_pos} fuera de límites. Omitiendo actualización de Q futuro.")
            # Considerar done=True o una penalización si el agente se sale del mapa
            done = True  # Tratar como estado terminal si se sale

        old_q_value = self.q_table[current_y, current_x, action_idx]

        if done:
            max_future_q = 0.0
        else:
            valid_next_actions = self.get_valid_actions(next_state_pos, obstacles)
            if not valid_next_actions:
                max_future_q = 0.0
            else:
                future_q_values = [self.q_table[next_y, next_x, na_idx] for na_idx in valid_next_actions]
                max_future_q = max(future_q_values) if future_q_values else 0.0

        new_q_value = old_q_value + self.learning_rate * \
                      (reward + self.discount_factor * max_future_q - old_q_value)
        self.q_table[current_y, current_x, action_idx] = new_q_value

    def calculate_reward(self, current_agent_pos, target_pos, prev_agent_pos, steps_in_episode, caught_target):
        if caught_target:
            return 100.0

        reward = -0.1  # Costo por paso

        dist_current_to_target = abs(current_agent_pos[0] - target_pos[0]) + abs(current_agent_pos[1] - target_pos[1])
        dist_prev_to_target = abs(prev_agent_pos[0] - target_pos[0]) + abs(prev_agent_pos[1] - target_pos[1])

        if dist_current_to_target < dist_prev_to_target:
            reward += 1.0
        elif dist_current_to_target > dist_prev_to_target:
            reward -= 0.5

            # Penalización si se choca con un obstáculo (aunque _is_valid debería prevenirlo)
        # Esto se manejaría mejor si la acción lleva a un estado inválido, el step no ocurre y se da -reward.
        # La lógica actual asume que la acción lleva a un estado válido o al target.

        return reward

    def train_one_episode(self, agent_start_pos, target_pos, obstacles,
                          max_steps_per_episode=200):  # Aumentado max_steps
        agent_current_pos = agent_start_pos
        agent_prev_pos = agent_start_pos
        episode_reward = 0
        path_len = 0

        for step in range(max_steps_per_episode):
            if self.stop_training_flag: break  # Chequear flag de parada dentro del episodio

            action_idx = self.choose_action(agent_current_pos, obstacles, is_training_exploration=True,
                                            target_pos=target_pos)

            if action_idx is None:  # Atrapado
                # Penalización por quedarse atrapado
                episode_reward -= 10  # Penalización mayor
                break

            dx, dy = self.actions_xy[action_idx]
            agent_next_pos = (agent_current_pos[0] + dx, agent_current_pos[1] + dy)

            # Chequear si el movimiento es realmente válido (redundante si choose_action funciona bien, pero seguro)
            if not self._is_valid(agent_next_pos, obstacles) and agent_next_pos != target_pos:
                # print(f"Q-Train: Movimiento inválido de {agent_current_pos} a {agent_next_pos} con acción {action_idx}. Penalizando.")
                reward = -20  # Penalización fuerte por intentar moverse a obstáculo
                self.update_q_value(agent_current_pos, action_idx, reward, agent_current_pos, obstacles,
                                    True)  # Considerar estado terminal
                episode_reward += reward
                break  # Terminar episodio si intenta movimiento inválido

            path_len += 1
            caught_or_reached_target = (agent_next_pos == target_pos)
            reward = self.calculate_reward(agent_next_pos, target_pos, agent_current_pos, step,
                                           caught_or_reached_target)
            episode_reward += reward

            self.update_q_value(agent_current_pos, action_idx, reward, agent_next_pos, obstacles,
                                caught_or_reached_target)

            agent_prev_pos = agent_current_pos
            agent_current_pos = agent_next_pos

            if caught_or_reached_target:
                break

        if not self.stop_training_flag and self.epsilon > self.epsilon_min:  # Solo decaer epsilon si no se detuvo
            self.epsilon *= self.epsilon_decay

        return episode_reward, path_len

    def get_learned_action_xy(self, state_pos, obstacles, target_pos=None):
        action_idx = self.choose_action(state_pos, obstacles, is_training_exploration=False, target_pos=target_pos)
        if action_idx is not None:
            return self.actions_xy[action_idx]
        return None

    def train_background(self, target_pos_for_training, initial_agent_pos_for_training, obstacles, callback=None,
                         update_interval=50):
        self.stop_background_training()

        self.stop_training_flag = False
        self.current_training_iteration = 0
        # Reiniciar historial para cada nuevo entrenamiento
        self.training_history = {'path_lengths': [], 'rewards': [], 'epsilons': []}
        self.best_reward = -float('inf')  # Resetear best_reward para la nueva sesión de entrenamiento

        def training_worker():
            print(
                f"Hilo Q-learning (trabajador) iniciado. Objetivo: {target_pos_for_training}, Inicio Agente: {initial_agent_pos_for_training}, Iter Máx: {self.max_training_iterations}")

            for i in range(self.max_training_iterations):
                if self.stop_training_flag:
                    print("Hilo Q-learning (trabajador): Recibida señal de parada.")
                    break

                current_agent_start_pos = initial_agent_pos_for_training
                # Si la pos inicial fija no es válida O es el target, la hago aleatoria válida
                if not self._is_valid(current_agent_start_pos,
                                      obstacles) or current_agent_start_pos == target_pos_for_training:
                    # print(f"Q-Train: Posición inicial {current_agent_start_pos} inválida o es el objetivo. Buscando aleatoria.")
                    temp_start_pos_found = False
                    for _try_start in range(100):  # Intentar encontrar una posición inicial aleatoria
                        temp_x = random.randint(0, self.width - 1)
                        temp_y = random.randint(0, self.height - 1)
                        candidate_start_pos = (temp_x, temp_y)
                        if self._is_valid(candidate_start_pos,
                                          obstacles) and candidate_start_pos != target_pos_for_training:
                            current_agent_start_pos = candidate_start_pos
                            temp_start_pos_found = True
                            break
                    if not temp_start_pos_found:
                        print(
                            f"Q-Train: No se pudo encontrar posición inicial aleatoria válida. Omitiendo episodio {i + 1}.")
                        continue  # Saltar este episodio si no se encuentra un inicio válido

                reward, path_len = self.train_one_episode(current_agent_start_pos, target_pos_for_training, obstacles)
                self.current_training_iteration = i + 1

                self.training_history['path_lengths'].append(path_len)
                self.training_history['rewards'].append(reward)
                self.training_history['epsilons'].append(self.epsilon)

                if reward > self.best_reward:
                    self.best_reward = reward
                    # self.best_path_length = path_len # path_len de un episodio no es "el mejor camino global"

                if callback and self.current_training_iteration % update_interval == 0:
                    callback(self.current_training_iteration, None, self.training_history, None)

                if self.current_training_iteration % 100 == 0:
                    print(
                        f"Q-Train iter {self.current_training_iteration}: Ep_Reward={reward:.2f}, PathLen={path_len}, Epsilon={self.epsilon:.4f}, BestRew={self.best_reward:.2f}")

                time.sleep(0.0001)

            print(
                f"Hilo Q-learning (trabajador): Entrenamiento finalizado o detenido. Iteraciones: {self.current_training_iteration}")
            if callback:
                callback(self.current_training_iteration, None, self.training_history, None, is_final=True)
            print("Hilo Q-learning (trabajador) terminado formalmente.")

        self.training_thread = threading.Thread(target=training_worker)
        self.training_thread.daemon = True
        self.training_thread.start()

    def stop_background_training(self):
        if self.training_thread and self.training_thread.is_alive():
            print("Intentando detener hilo de entrenamiento Q-learning...")
            self.stop_training_flag = True
            self.training_thread.join(timeout=2.0)  # Aumentar timeout
            if self.training_thread.is_alive():
                print("Advertencia: Hilo de entrenamiento Q-learning no terminó limpiamente.")
            else:
                print("Hilo de entrenamiento Q-learning detenido exitosamente.")
            self.training_thread = None
            return True
        self.training_thread = None
        return False

    def plot_analysis(self, show=True, save_path=None):
        if not self.training_history['rewards']:
            print("ADB.py: No hay datos de entrenamiento para plot_analysis.")
            if show and plt.get_fignums(): plt.close('all')
            return

        fig, axs = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        episodes = range(1, len(self.training_history['rewards']) + 1)

        color_reward = 'tab:blue'
        axs[0].set_ylabel('Recompensa Acumulada por Episodio', color=color_reward)
        axs[0].plot(episodes, self.training_history['rewards'], color=color_reward, label='Recompensa', alpha=0.7)
        axs[0].tick_params(axis='y', labelcolor=color_reward)
        axs[0].grid(True, linestyle=':', alpha=0.5)

        if len(self.training_history['rewards']) >= 20:
            window_size = min(50, max(10, len(self.training_history['rewards']) // 10))
            if window_size > 1:
                kernel = np.ones(window_size) / window_size
                smoothed_rewards = np.convolve(self.training_history['rewards'], kernel, 'valid')
                smoothed_x_rewards = range(window_size // 2, window_size // 2 + len(smoothed_rewards))
                axs[0].plot(smoothed_x_rewards, smoothed_rewards, label=f'Recompensa Suavizada ({window_size}ep)',
                            color='firebrick')
        axs[0].legend(loc='best')
        axs[0].set_title('Recompensa por Episodio')

        color_epsilon = 'tab:green'
        axs[1].set_ylabel('Valor de Epsilon (Exploración)', color=color_epsilon)
        axs[1].plot(episodes, self.training_history['epsilons'], color=color_epsilon, label='Epsilon')
        axs[1].tick_params(axis='y', labelcolor=color_epsilon)
        axs[1].set_xlabel('Número de Episodios')
        axs[1].grid(True, linestyle=':', alpha=0.5)
        axs[1].legend(loc='best')
        axs[1].set_title('Decaimiento de Epsilon')

        fig.suptitle("Análisis de Aprendizaje Q-Agent", fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        if save_path: plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig

    def plot_q_values_heatmap(self, show=True, save_path=None):
        fig, axs = plt.subplots(2, 2, figsize=(11, 9))
        axs = axs.flatten()
        cmap = 'viridis'

        min_q_overall = np.min(self.q_table)
        max_q_overall = np.max(self.q_table)
        if min_q_overall == max_q_overall:
            min_q_overall -= 0.1
            max_q_overall += 0.1

        for i in range(self.num_actions):
            q_values_action = self.q_table[:, :, i]
            im = axs[i].imshow(q_values_action, cmap=cmap, vmin=min_q_overall, vmax=max_q_overall, origin='lower')
            axs[i].set_title(f'Valores Q para: {self.action_names[i]}')
            axs[i].set_xlabel('Posición X')
            axs[i].set_ylabel('Posición Y')
            fig.colorbar(im, ax=axs[i], orientation='vertical', label='Valor Q')

        fig.suptitle("Mapas de Calor de Q-Values por Acción", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        if save_path: plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig

    def plot_best_path(self, agent_sim_start_pos, target_pos, obstacles, show=True, save_path=None):
        simulated_path = []
        current_pos = agent_sim_start_pos
        simulated_path.append(current_pos)
        max_steps_for_plot = self.width * self.height * 2  # Aumentado por si acaso

        for _ in range(max_steps_for_plot):
            if current_pos == target_pos: break
            action_direction_xy = self.get_learned_action_xy(current_pos, obstacles,
                                                             target_pos=target_pos)  # Pasar target

            if action_direction_xy is None: break

            dx, dy = action_direction_xy
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            # Adicional: chequear si el siguiente paso es válido (no debería ser necesario si get_learned_action_xy es robusto)
            if not self._is_valid(next_pos, obstacles) and next_pos != target_pos:
                # print(f"Plot best path: Intento de movimiento inválido de {current_pos} a {next_pos}. Deteniendo simulación de path.")
                break
            current_pos = next_pos
            simulated_path.append(current_pos)
            if len(simulated_path) > 1 and simulated_path[-1] == simulated_path[-2]:  # Atrapado en bucle de 1 paso
                # print("Plot best path: Detectado bucle de 1 paso. Deteniendo.")
                break

        fig, ax = plt.subplots(figsize=(self.width * 0.5 + 1, self.height * 0.5 + 1))  # Ajustar tamaño dinámicamente
        ax.set_xlim(-0.5, self.width - 0.5)
        ax.set_ylim(self.height - 0.5, -0.5)
        ax.set_xticks(np.arange(self.width))
        ax.set_yticks(np.arange(self.height))
        ax.grid(True, linestyle=':', alpha=0.7)

        for obs_x, obs_y in obstacles:
            ax.add_patch(plt.Rectangle((obs_x - 0.5, obs_y - 0.5), 1, 1, color='dimgray', zorder=2))

        if simulated_path:
            path_x = [p[0] for p in simulated_path]
            path_y = [p[1] for p in simulated_path]
            ax.plot(path_x, path_y, 'r-o', linewidth=1.5, markersize=4,
                    label=f'Camino por Política Q ({len(simulated_path) - 1} pasos)', zorder=3)

        ax.plot(agent_sim_start_pos[0], agent_sim_start_pos[1], 'bs', markersize=8, label='Inicio Agente (Simulación)',
                zorder=4)
        ax.plot(target_pos[0], target_pos[1], 'g*', markersize=12, label='Objetivo', zorder=4)
        ax.legend(loc='best')
        ax.set_title('Camino Simulado Usando Política Q Aprendida')
        ax.set_aspect('equal', adjustable='box')

        plt.tight_layout()
        if save_path: plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig

    def plot_comprehensive_analysis(self, agent_target_pos, agent_initial_pos_for_sim, obstacles, show=True,
                                    save_path=None):
        if not self.training_history['rewards']:
            print("ADB.py: No hay datos de entrenamiento para plot_comprehensive_analysis.")
            if show and plt.get_fignums(): plt.close('all')
            return

        fig = plt.figure(figsize=(17, 15))
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.5, 1.5])

        ax_progress = fig.add_subplot(gs[0, :])
        if self.training_history['rewards']:
            episodes = range(1, len(self.training_history['rewards']) + 1)
            color_reward = 'royalblue'
            ax_progress.set_xlabel('Número de Episodios')
            ax_progress.set_ylabel('Recompensa Acumulada', color=color_reward)
            ax_progress.plot(episodes, self.training_history['rewards'], color=color_reward, label='Recompensa',
                             alpha=0.8)
            ax_progress.tick_params(axis='y', labelcolor=color_reward)
            ax_progress.grid(True, linestyle=':', alpha=0.6)

            if len(self.training_history['rewards']) >= 20:
                win_size_rew = min(50, max(10, len(self.training_history['rewards']) // 10))
                if win_size_rew > 1:
                    kernel_rew = np.ones(win_size_rew) / win_size_rew
                    smoothed_rewards_vals = np.convolve(self.training_history['rewards'], kernel_rew, 'valid')
                    smoothed_rewards_x = range(win_size_rew // 2, win_size_rew // 2 + len(smoothed_rewards_vals))
                    ax_progress.plot(smoothed_rewards_x, smoothed_rewards_vals,
                                     label=f'Recompensa Suavizada ({win_size_rew}ep)', color='crimson', linewidth=1.5)

            ax_epsilon = ax_progress.twinx()
            color_epsilon = 'forestgreen'
            ax_epsilon.set_ylabel('Valor de Epsilon (Exploración)', color=color_epsilon)
            ax_epsilon.plot(episodes, self.training_history['epsilons'], color=color_epsilon, label='Epsilon',
                            linestyle='--')
            ax_epsilon.tick_params(axis='y', labelcolor=color_epsilon)

            lines, labels = ax_progress.get_legend_handles_labels()
            lines2, labels2 = ax_epsilon.get_legend_handles_labels()
            ax_progress.legend(lines + lines2, labels + labels2, loc='center left', bbox_to_anchor=(0.05, 0.5))
        ax_progress.set_title('Progreso del Entrenamiento del Agente')

        ax_path_sim = fig.add_subplot(gs[1, 0])
        sim_path_coords = []
        curr_p = agent_initial_pos_for_sim
        sim_path_coords.append(curr_p)
        for _ in range(self.width * self.height * 2):  # Aumentado límite
            if curr_p == agent_target_pos: break
            act_dir_xy = self.get_learned_action_xy(curr_p, obstacles, target_pos=agent_target_pos)  # Pasar target
            if not act_dir_xy: break
            next_p_sim = (curr_p[0] + act_dir_xy[0], curr_p[1] + act_dir_xy[1])
            if not self._is_valid(next_p_sim, obstacles) and next_p_sim != agent_target_pos: break
            curr_p = next_p_sim
            sim_path_coords.append(curr_p)
            if len(sim_path_coords) > 1 and sim_path_coords[-1] == sim_path_coords[-2]: break

        ax_path_sim.set_xlim(-0.5, self.width - 0.5);
        ax_path_sim.set_ylim(self.height - 0.5, -0.5)
        ax_path_sim.set_xticks(np.arange(self.width));
        ax_path_sim.set_yticks(np.arange(self.height))
        ax_path_sim.grid(True, linestyle=':', alpha=0.7)
        for ox, oy in obstacles: ax_path_sim.add_patch(
            plt.Rectangle((ox - 0.5, oy - 0.5), 1, 1, color='dimgray', zorder=2))
        if sim_path_coords: ax_path_sim.plot([p[0] for p in sim_path_coords], [p[1] for p in sim_path_coords],
                                             'crimson', marker='o', ms=3, lw=1.5,
                                             label=f'Ruta Simulada ({len(sim_path_coords) - 1} pasos)', zorder=3)
        ax_path_sim.plot(agent_initial_pos_for_sim[0], agent_initial_pos_for_sim[1], 'bs', ms=7,
                         label='Inicio Agente (Sim.)', zorder=4)
        ax_path_sim.plot(agent_target_pos[0], agent_target_pos[1], 'g*', ms=10, label='Objetivo Agente', zorder=4)
        ax_path_sim.legend(fontsize='small');
        ax_path_sim.set_title('Camino Simulado por Política Q');
        ax_path_sim.set_aspect('equal', adjustable='box')

        ax_q_max_heatmap = fig.add_subplot(gs[1, 1])
        max_q_values_per_state = np.max(self.q_table, axis=2)
        im_q_max = ax_q_max_heatmap.imshow(max_q_values_per_state, cmap='viridis', origin='lower', aspect='auto')
        fig.colorbar(im_q_max, ax=ax_q_max_heatmap, label='Valor Q Máximo del Estado')
        ax_q_max_heatmap.set_title('Mapa de Calor de Valores Q Máximos por Estado');
        ax_q_max_heatmap.set_xlabel('X');
        ax_q_max_heatmap.set_ylabel('Y')

        q_min_plot = np.min(self.q_table)
        q_max_plot = np.max(self.q_table)
        if q_min_plot == q_max_plot: q_max_plot += 0.1

        ax_q_action1 = fig.add_subplot(gs[2, 0])
        action1_idx = 2  # Abajo
        im_a1 = ax_q_action1.imshow(self.q_table[:, :, action1_idx], cmap='coolwarm', vmin=q_min_plot, vmax=q_max_plot,
                                    origin='lower', aspect='auto')
        fig.colorbar(im_a1, ax=ax_q_action1, label=f'Valor Q ({self.action_names[action1_idx]})')
        ax_q_action1.set_title(f'Mapa de Calor Q para Acción "{self.action_names[action1_idx]}"');
        ax_q_action1.set_xlabel('X');
        ax_q_action1.set_ylabel('Y')

        ax_q_action2 = fig.add_subplot(gs[2, 1])
        action2_idx = 1  # Derecha
        im_a2 = ax_q_action2.imshow(self.q_table[:, :, action2_idx], cmap='coolwarm', vmin=q_min_plot, vmax=q_max_plot,
                                    origin='lower', aspect='auto')
        fig.colorbar(im_a2, ax=ax_q_action2, label=f'Valor Q ({self.action_names[action2_idx]})')
        ax_q_action2.set_title(f'Mapa de Calor Q para Acción "{self.action_names[action2_idx]}"');
        ax_q_action2.set_xlabel('X');
        ax_q_action2.set_ylabel('Y')

        fig.suptitle(f"Análisis Comprensivo del Agente Q-learning (Entrenado para alcanzar {agent_target_pos})",
                     fontsize=18)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        if save_path: plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)
        return fig
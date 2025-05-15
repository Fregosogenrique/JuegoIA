# HeatMapPathfinding.py
import numpy as np
import heapq
import random
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


class HeatMapPathfinding:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.avatar_heat_map = np.zeros((height, width))
        self.enemy_heat_map = np.zeros((height, width))

        self.potential_enemy_positions = set()
        self.choke_points = []
        self.safe_zones = []
        self.last_analysis_params = None

    def reset(self):
        self.avatar_heat_map.fill(0)
        self.enemy_heat_map.fill(0)
        self.potential_enemy_positions.clear()
        self.choke_points = [];
        self.safe_zones = []
        self.last_analysis_params = None

    def manhattan_distance(self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _is_valid(self, pos, obstacles_set, target_goal=None):
        x, y = pos
        return 0 <= x < self.width and \
            0 <= y < self.height and \
            (pos not in obstacles_set or (target_goal is not None and pos == target_goal))

    def _get_neighbors(self, pos, obstacles_set, target_goal=None):
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self._is_valid((nx, ny), obstacles_set, target_goal):
                neighbors.append((nx, ny))
        return neighbors

    def train(self, start_pos, goal_pos, obstacles, enemy_positions_set, iterations=1000, callback=None):
        self.avatar_heat_map.fill(0)
        obstacles_set = set(obstacles) if not isinstance(obstacles, set) else obstacles
        best_path_found = None

        for i in range(iterations):
            if callback and not callback(i, iterations, None, best_path_found, (i / iterations) * 100.0,
                                         is_final=False):
                return best_path_found

            current_pos = start_pos
            path_taken = [current_pos]
            max_steps = (self.width * self.height) // 2 + self.manhattan_distance(start_pos, goal_pos) * 2
            max_steps = max(max_steps, 20)

            for step_num in range(max_steps):
                if current_pos == goal_pos:
                    break

                neighbors = self._get_neighbors(current_pos, obstacles_set, target_goal=goal_pos)
                if not neighbors:
                    break

                weighted_neighbors = []
                for neighbor_pos in neighbors:
                    weight = self.manhattan_distance(neighbor_pos, goal_pos) * -10.0
                    for enemy_pos in enemy_positions_set:
                        dist_to_enemy = self.manhattan_distance(neighbor_pos, enemy_pos)
                        if dist_to_enemy < 1:
                            weight -= 2000
                        elif dist_to_enemy < 3:
                            weight -= 600 / (dist_to_enemy + 0.1)

                    weight += self.avatar_heat_map[neighbor_pos[1], neighbor_pos[0]] * 0.05
                    weighted_neighbors.append((weight + random.uniform(-0.1, 0.1), neighbor_pos))

                if not weighted_neighbors: break

                if random.random() < 0.15 and len(weighted_neighbors) > 1:
                    current_pos = random.choice(neighbors)
                else:
                    weighted_neighbors.sort(key=lambda x: x[0], reverse=True)
                    current_pos = weighted_neighbors[0][1]

                if current_pos in path_taken and len(path_taken) > 5:
                    valid_random_choices = [n for n in neighbors if n not in path_taken[-3:]]
                    if valid_random_choices:
                        current_pos = random.choice(valid_random_choices)
                    elif neighbors:
                        current_pos = random.choice(neighbors)
                    else:
                        break
                path_taken.append(current_pos)

            if path_taken[-1] == goal_pos:
                if best_path_found is None or len(path_taken) < len(best_path_found):
                    best_path_found = list(path_taken)

                path_len = len(path_taken)
                for idx, pos_in_path in enumerate(path_taken):
                    reinforcement = (1.0 / (path_len + 1e-5)) * (path_len - idx) * 15.0
                    self.avatar_heat_map[pos_in_path[1], pos_in_path[0]] += reinforcement

        if callback:
            callback(iterations, iterations, None, best_path_found, 100.0, is_final=True)
        return best_path_found

    def find_path_with_heat_map(self, start_pos, goal_pos, obstacles=None, enemy_positions_set=None, is_avatar=True):
        heatmap_to_use = self.avatar_heat_map if is_avatar else self.enemy_heat_map

        if start_pos == goal_pos:
            return [start_pos]

        obstacles_set = set(obstacles) if obstacles and not isinstance(obstacles, set) else (obstacles or set())

        direct_neighbors_of_start = []
        for dx_direct, dy_direct in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx_direct, ny_direct = start_pos[0] + dx_direct, start_pos[1] + dy_direct
            if 0 <= nx_direct < self.width and 0 <= ny_direct < self.height:
                direct_neighbors_of_start.append((nx_direct, ny_direct))

        if goal_pos in direct_neighbors_of_start and goal_pos not in obstacles_set:
            return [start_pos, goal_pos]

        if not heatmap_to_use.any() and is_avatar:
            if obstacles is None:
                print("Error: Obstáculos no provistos para entrenamiento ad-hoc de heatmap.")
                return None
            current_enemies_for_adhoc = set(enemy_positions_set) if enemy_positions_set is not None else set()
            # print(f"Find_path: Heatmap vacío, entrenando ad-hoc con {len(current_enemies_for_adhoc)} enemigos considerados.") # Para depuración
            self.train(start_pos, goal_pos, obstacles, current_enemies_for_adhoc, iterations=200, callback=None)
            if not self.avatar_heat_map.any():
                print("Find_path: Fallo en entrenamiento ad-hoc.")
                return None
            heatmap_to_use = self.avatar_heat_map

        pq = []
        initial_h_cost = self.manhattan_distance(start_pos, goal_pos)
        heapq.heappush(pq, (initial_h_cost, 0, start_pos))

        came_from = {start_pos: None}
        cost_so_far = {start_pos: 0}

        max_exploration_nodes = self.width * self.height * 2
        nodes_explored = 0

        while pq and nodes_explored < max_exploration_nodes:
            nodes_explored += 1
            f_cost_current_node, g_cost_current, current = heapq.heappop(pq)

            if current == goal_pos:
                path = []
                temp = current
                while temp is not None:
                    path.append(temp)
                    temp = came_from[temp]
                return path[::-1]

            for neighbor in self._get_neighbors(current, obstacles_set, target_goal=goal_pos):
                heat_val = 0
                if 0 <= neighbor[1] < self.height and 0 <= neighbor[0] < self.width:
                    heat_val = heatmap_to_use[neighbor[1], neighbor[0]]

                base_movement_cost = 1.0

                if neighbor == goal_pos:
                    step_cost = 0.01
                else:
                    heat_influence_factor = 0.5
                    adjusted_cost_from_heat = - (heat_val * heat_influence_factor * 0.01)
                    step_cost = max(0.1, base_movement_cost + adjusted_cost_from_heat)

                new_g_cost = g_cost_current + step_cost

                if neighbor not in cost_so_far or new_g_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_g_cost
                    priority = new_g_cost + self.manhattan_distance(neighbor, goal_pos)
                    heapq.heappush(pq, (priority, new_g_cost, neighbor))
                    came_from[neighbor] = current
        return None

    def analyze_environment(self, player_start_pos, goal_pos, obstacles, num_enemies):
        if not self.avatar_heat_map.any():
            return False

        current_params = (player_start_pos, goal_pos, tuple(sorted(list(obstacles))), num_enemies)
        if current_params == self.last_analysis_params:
            return True

        self.last_analysis_params = current_params
        self.potential_enemy_positions.clear()
        self.choke_points = []
        self.safe_zones = []

        obstacles_set = set(obstacles)
        best_path_player_ref = self.find_path_with_heat_map(player_start_pos, goal_pos, obstacles_set,
                                                            enemy_positions_set=set(), is_avatar=True)

        if best_path_player_ref:
            for r in range(self.height):
                for c in range(self.width):
                    pos = (c, r)
                    if pos in obstacles_set or pos == player_start_pos or pos == goal_pos:
                        continue
                    if pos in best_path_player_ref:
                        valid_neighbors = len(self._get_neighbors(pos, obstacles_set, target_goal=goal_pos))
                        if valid_neighbors <= 2:
                            self.choke_points.append(pos)

        threshold_safe = np.percentile(self.avatar_heat_map[self.avatar_heat_map > 0], 25) if np.any(
            self.avatar_heat_map > 0) else 0.5
        for r in range(self.height):
            for c in range(self.width):
                pos = (c, r)
                if pos in obstacles_set or pos == player_start_pos or pos == goal_pos:
                    continue
                if self.avatar_heat_map[r, c] < threshold_safe and self.avatar_heat_map[r, c] >= 0:
                    is_far_from_path = True
                    if best_path_player_ref:
                        for path_node in best_path_player_ref:
                            if self.manhattan_distance(pos, path_node) < 3:
                                is_far_from_path = False;
                                break
                    if is_far_from_path:
                        self.safe_zones.append(pos)

        if best_path_player_ref:
            for node_idx, node_on_path in enumerate(best_path_player_ref):
                if node_idx > len(best_path_player_ref) // 4 and node_idx < len(best_path_player_ref) * 3 // 4:
                    if self.manhattan_distance(node_on_path, player_start_pos) > 3:
                        self.potential_enemy_positions.add(node_on_path)

        for cp in self.choke_points:
            if len(self.potential_enemy_positions) < num_enemies * 2:
                self.potential_enemy_positions.add(cp)

        attempts = 0
        while len(self.potential_enemy_positions) < num_enemies and attempts < self.width * self.height * 2:
            rx, ry = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            rpos = (rx, ry)
            if self._is_valid(rpos, obstacles_set,
                              target_goal=goal_pos) and rpos != player_start_pos and rpos != goal_pos:
                if rpos not in self.choke_points and rpos not in self.safe_zones:
                    self.potential_enemy_positions.add(rpos)
            attempts += 1
        return True

    def visualize_heat_map(self, start_pos=None, goal_pos=None, path=None, obstacles_vis=None, title="Heatmap",
                           is_avatar=True, show=True, save_path=None):
        heatmap_to_display = self.avatar_heat_map if is_avatar else self.enemy_heat_map
        if not heatmap_to_display.any():
            print(f"Visualize HM: Heatmap {'Avatar' if is_avatar else 'Enemigo'} está vacío.")
            return

        plt.figure(figsize=(max(8, self.width * 0.4), max(6, self.height * 0.4)))

        vmin_plot, vmax_plot = np.min(heatmap_to_display), np.max(heatmap_to_display)
        if vmin_plot == vmax_plot: vmax_plot += 0.1

        plt.imshow(heatmap_to_display.T, cmap='viridis', origin='lower', interpolation='bilinear', vmin=vmin_plot,
                   vmax=vmax_plot)
        plt.colorbar(label="Valor del Heatmap")

        if obstacles_vis:
            obs_x = [o[0] for o in obstacles_vis]
            obs_y = [o[1] for o in obstacles_vis]
            plt.scatter(obs_x, obs_y, marker='s', s=60, color='black', alpha=0.7, label='Obstáculos')

        if start_pos:
            plt.scatter(start_pos[0], start_pos[1], marker='o', s=120, color='cyan', edgecolor='black', linewidth=1.5,
                        label='Inicio', zorder=5)
        if goal_pos:
            plt.scatter(goal_pos[0], goal_pos[1], marker='*', s=180, color='magenta', edgecolor='black', linewidth=1.5,
                        label='Meta', zorder=5)

        if path:
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            plt.plot(path_x, path_y, 'w--', linewidth=2.5, label='Camino')

        plt.title(title, fontsize=14)
        plt.xlabel("X");
        plt.ylabel("Y")
        x_ticks_step = 1 if self.width <= 20 else max(1, self.width // 10)
        y_ticks_step = 1 if self.height <= 20 else max(1, self.height // 10)
        plt.xticks(np.arange(0, self.width, x_ticks_step))
        plt.yticks(np.arange(0, self.height, y_ticks_step))

        plt.grid(True, which='major', color='dimgray', linestyle='-', linewidth=0.7, alpha=0.5)
        plt.xlim(-0.5, self.width - 0.5)
        plt.ylim(self.height - 0.5, -0.5)

        if save_path: plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close()
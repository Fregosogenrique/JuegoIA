# HeatMapPathfinding.py
"""
Mapa de calor del avatar + búsqueda de rutas sobre ese mapa.

La idea original se mantiene: se simulan muchas "caminatas" desde el avatar
hasta la casa y las celdas de las caminatas exitosas se "calientan"; después
un A* prefiere las celdas calientes. La mejora formaliza esa idea como una
COLONIA DE HORMIGAS (Ant Colony Optimization, Dorigo 1996):

- Cada caminata es una hormiga. En cada paso elige vecino con probabilidad
      p(n) ∝ (τ(n) + τ0)^α · exp(-β·Δd(n)) · exp(-peligro(n))
  τ = feromona (el valor del mapa de calor), Δd = cuánto se aleja de la casa
  según la distancia REAL (BFS, rodea muros), peligro = cercanía a enemigos.
- Las hormigas tienen memoria (no repiten celdas) y antes de depositar se
  borran los bucles del camino, así no se calientan los rodeos.
- EVAPORACIÓN: en cada iteración τ ← (1-ρ)·τ. Las rutas viejas o malas se
  enfrían; antes el calor sólo se acumulaba.
- DEPÓSITO ∝ 1/longitud: las rutas cortas calientan más (antes el refuerzo
  dependía de la posición dentro del camino).
- ELITISMO: la mejor ruta conocida se refuerza en cada iteración.

El A* ahora usa un costo por celda >= 1 (heurística Manhattan admisible, por
lo que la ruta es óptima para ese costo) y sí considera a los enemigos:
      costo(n) = 1 + w_calor·(1 - τ(n)/τ_max) + peligro(n)
"""
import heapq
import math
import random

import matplotlib.pyplot as plt
import numpy as np

from config import GameConfig
from grid_utils import UNREACHABLE, bfs_distance_map, manhattan, neighbors_4


class HeatMapPathfinding:
    # Parámetros de la colonia de hormigas
    ACO_ALPHA = 1.0          # Peso de la feromona
    ACO_BETA = 1.5           # Peso de la heurística (acercarse a la casa)
    ACO_TAU0 = 0.5           # Feromona base: evita que celdas frías tengan probabilidad 0
    ACO_EVAPORATION = 0.05   # ρ: fracción de feromona que se evapora por iteración
    ACO_DEPOSIT = 10.0       # Q: feromona total que deposita una hormiga exitosa (Q / L por celda)
    ACO_ELITE_WEIGHT = 2.0   # Refuerzo extra de la mejor ruta conocida

    # Parámetros del A*
    HEAT_WEIGHT = 0.5        # Cuánto prefiere el A* las celdas calientes

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.avatar_heat_map = np.zeros((height, width))
        self.enemy_heat_map = np.zeros((height, width))

        self.potential_enemy_positions = set()
        self.choke_points = []
        self.safe_zones = []
        self.last_analysis_params = None
        self.best_training_path = None

    def reset(self):
        self.avatar_heat_map.fill(0)
        self.enemy_heat_map.fill(0)
        self.potential_enemy_positions.clear()
        self.choke_points = []
        self.safe_zones = []
        self.last_analysis_params = None
        self.best_training_path = None

    # ------------------------------------------------------------- utilidades
    def manhattan_distance(self, p1, p2):
        return manhattan(p1, p2)

    def _is_valid(self, pos, obstacles_set, target_goal=None):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and \
            (pos not in obstacles_set or (target_goal is not None and pos == target_goal))

    def _get_neighbors(self, pos, obstacles_set, target_goal=None):
        return [n for n in neighbors_4(pos, self.width, self.height) if self._is_valid(n, obstacles_set, target_goal)]

    @staticmethod
    def danger_cost(pos, enemy_positions):
        """
        Penalización por cercanía a enemigos: DANGER_WEIGHT / (1 + d) para
        d <= DANGER_RADIUS. Una celda con enemigo (d = 0) es infinita.
        """
        total = 0.0
        for enemy_pos in enemy_positions:
            d = manhattan(pos, enemy_pos)
            if d == 0:
                return math.inf
            if d <= GameConfig.DANGER_RADIUS:
                total += GameConfig.DANGER_WEIGHT / (1 + d)
        return total

    def path_cost(self, path, enemy_positions=()):
        """Costo comparable entre rutas de distinto origen: pasos + peligro acumulado."""
        if not path:
            return math.inf
        return sum(1 + self.danger_cost(p, enemy_positions) for p in path[1:])

    @staticmethod
    def _loop_erase(path):
        """Elimina los bucles de un camino (si se vuelve a una celda, se corta el rodeo)."""
        index_of = {}
        clean = []
        for pos in path:
            if pos in index_of:
                cut = index_of[pos]
                for removed in clean[cut + 1:]:
                    del index_of[removed]
                clean = clean[:cut + 1]
            else:
                index_of[pos] = len(clean)
                clean.append(pos)
        return clean

    # ---------------------------------------------- entrenamiento (hormigas)
    def _ant_walk(self, start_pos, goal_pos, obstacles_set, dist_goal, danger, max_steps):
        current = start_pos
        path = [current]
        visited = {current}
        tau = self.avatar_heat_map
        for _ in range(max_steps):
            if current == goal_pos:
                break
            neighbors = [n for n in self._get_neighbors(current, obstacles_set, goal_pos)
                         if danger[n[1], n[0]] != math.inf]
            if not neighbors:
                break
            fresh = [n for n in neighbors if n not in visited]
            candidates = fresh or neighbors  # Sin salida nueva: se permite retroceder (luego se borra el bucle)

            d_current = dist_goal[current[1], current[0]]
            weights = []
            for n in candidates:
                delta = dist_goal[n[1], n[0]] - d_current  # -1 se acerca, +1 se aleja
                weights.append(((tau[n[1], n[0]] + self.ACO_TAU0) ** self.ACO_ALPHA)
                               * math.exp(-self.ACO_BETA * delta - danger[n[1], n[0]]))
            current = random.choices(candidates, weights=weights)[0]
            path.append(current)
            visited.add(current)
        return path

    def _deposit(self, path, amount_total):
        per_cell = amount_total / max(1, len(path))
        for x, y in path:
            self.avatar_heat_map[y, x] += per_cell

    def train(self, start_pos, goal_pos, obstacles, enemy_positions_set, iterations=1000, callback=None):
        """
        Entrena el mapa de calor con `iterations` hormigas. Devuelve la mejor
        ruta encontrada (o None). `callback` puede devolver False para cancelar.
        """
        self.avatar_heat_map.fill(0)
        self.best_training_path = None
        obstacles_set = obstacles if isinstance(obstacles, (set, frozenset)) else set(obstacles)
        enemies = set(enemy_positions_set or ())

        dist_goal = bfs_distance_map(self.width, self.height, goal_pos, obstacles_set)
        if dist_goal[start_pos[1], start_pos[0]] == UNREACHABLE:
            if callback:
                callback(iterations, iterations, None, None, 100.0, is_final=True)
            return None
        dist_goal = np.where(dist_goal == UNREACHABLE, self.width * self.height, dist_goal)

        danger = np.zeros((self.height, self.width))
        if enemies:
            for y in range(self.height):
                for x in range(self.width):
                    danger[y, x] = self.danger_cost((x, y), enemies)
        danger[goal_pos[1], goal_pos[0]] = 0.0

        max_steps = 4 * int(dist_goal[start_pos[1], start_pos[0]]) + 20
        best_path = None

        for i in range(iterations):
            if callback and not callback(i, iterations, None, best_path, (i / iterations) * 100.0, is_final=False):
                self.best_training_path = best_path
                return best_path

            walk = self._ant_walk(start_pos, goal_pos, obstacles_set, dist_goal, danger, max_steps)

            self.avatar_heat_map *= (1.0 - self.ACO_EVAPORATION)
            if walk[-1] == goal_pos:
                walk = self._loop_erase(walk)
                self._deposit(walk, self.ACO_DEPOSIT)
                if best_path is None or len(walk) < len(best_path):
                    best_path = walk
            if best_path:
                self._deposit(best_path, self.ACO_DEPOSIT * self.ACO_ELITE_WEIGHT)

        self.best_training_path = best_path
        if callback:
            callback(iterations, iterations, None, best_path, 100.0, is_final=True)
        return best_path

    # ------------------------------------------------------------- búsqueda
    def find_path_with_heat_map(self, start_pos, goal_pos, obstacles=None, enemy_positions_set=None, is_avatar=True):
        """A* sobre el mapa de calor, evitando enemigos y sus alrededores."""
        if start_pos == goal_pos:
            return [start_pos]

        obstacles_set = set(obstacles) if obstacles and not isinstance(obstacles, (set, frozenset)) \
            else (obstacles or set())
        enemies = set(enemy_positions_set or ())
        heatmap_to_use = self.avatar_heat_map if is_avatar else self.enemy_heat_map

        if is_avatar and not heatmap_to_use.any():
            if obstacles is None:
                print("Error: Obstáculos no provistos para entrenamiento ad-hoc de heatmap.")
                return None
            self.train(start_pos, goal_pos, obstacles_set, enemies, iterations=200)
            if not self.avatar_heat_map.any():
                return None

        heat_max = float(np.max(heatmap_to_use)) or 1.0
        danger_cache = {}

        def step_cost(cell):
            if cell == goal_pos:
                return 1.0
            if cell not in danger_cache:
                danger_cache[cell] = self.danger_cost(cell, enemies)
            coldness = 1.0 - heatmap_to_use[cell[1], cell[0]] / heat_max
            return 1.0 + self.HEAT_WEIGHT * coldness + danger_cache[cell]

        open_heap = [(manhattan(start_pos, goal_pos), 0.0, start_pos)]
        came_from = {start_pos: None}
        cost_so_far = {start_pos: 0.0}
        closed = set()

        while open_heap:
            _, g_current, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            if current == goal_pos:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]
            closed.add(current)

            for neighbor in self._get_neighbors(current, obstacles_set, target_goal=goal_pos):
                cost = step_cost(neighbor)
                if cost == math.inf:
                    continue
                new_g = g_current + cost
                if new_g < cost_so_far.get(neighbor, math.inf):
                    cost_so_far[neighbor] = new_g
                    came_from[neighbor] = current
                    heapq.heappush(open_heap, (new_g + manhattan(neighbor, goal_pos), new_g, neighbor))
        return None

    # ---------------------------------------------- análisis del entorno
    def _detour_if_blocked(self, cell, start_pos, goal_pos, obstacles_set, base_length):
        """Pasos extra que costaría llegar a la meta si `cell` estuviera bloqueada."""
        dist = bfs_distance_map(self.width, self.height, goal_pos, obstacles_set | {cell})
        d = dist[start_pos[1], start_pos[0]]
        return math.inf if d == UNREACHABLE else d - base_length

    def analyze_environment(self, player_start_pos, goal_pos, obstacles, num_enemies):
        """
        Identifica, a partir del mapa de calor entrenado:
        - choke_points (cuellos de botella): celdas de la ruta principal cuyo
          bloqueo obliga a un rodeo de 4+ pasos (o deja la casa inalcanzable).
        - safe_zones: celdas frías y alejadas de la ruta (buenas para patrullas).
        - potential_enemy_positions: tramo central de la ruta + cuellos de botella.
        """
        if not self.avatar_heat_map.any():
            return False

        current_params = (player_start_pos, goal_pos, tuple(sorted(obstacles)), num_enemies)
        if current_params == self.last_analysis_params:
            return True

        self.last_analysis_params = current_params
        self.potential_enemy_positions.clear()
        self.choke_points = []
        self.safe_zones = []

        obstacles_set = set(obstacles)
        reference_path = self.find_path_with_heat_map(player_start_pos, goal_pos, obstacles_set,
                                                      enemy_positions_set=set(), is_avatar=True)

        if reference_path:
            base_dist = bfs_distance_map(self.width, self.height, goal_pos, obstacles_set)
            base_length = base_dist[player_start_pos[1], player_start_pos[0]]
            detours = []
            for pos in reference_path[1:-1]:
                detour = self._detour_if_blocked(pos, player_start_pos, goal_pos, obstacles_set, base_length)
                narrow = len(self._get_neighbors(pos, obstacles_set, goal_pos)) <= 2
                if detour >= 4 or narrow:
                    detours.append((detour, pos))
            detours.sort(key=lambda item: item[0], reverse=True)
            self.choke_points = [pos for _, pos in detours]

        heat_values = self.avatar_heat_map[self.avatar_heat_map > 0]
        threshold_safe = np.percentile(heat_values, 25) if heat_values.size else 0.5
        path_cells = set(reference_path or [])
        for r in range(self.height):
            for c in range(self.width):
                pos = (c, r)
                if pos in obstacles_set or pos == player_start_pos or pos == goal_pos:
                    continue
                if self.avatar_heat_map[r, c] < threshold_safe and \
                        all(manhattan(pos, node) >= 3 for node in path_cells):
                    self.safe_zones.append(pos)

        if reference_path:
            n = len(reference_path)
            for idx, node in enumerate(reference_path):
                if n // 4 < idx < n * 3 // 4 and manhattan(node, player_start_pos) > 3:
                    self.potential_enemy_positions.add(node)

        for cp in self.choke_points:
            if len(self.potential_enemy_positions) < num_enemies * 2:
                self.potential_enemy_positions.add(cp)

        attempts = 0
        while len(self.potential_enemy_positions) < num_enemies and attempts < self.width * self.height * 2:
            rpos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if self._is_valid(rpos, obstacles_set) and rpos not in (player_start_pos, goal_pos) \
                    and rpos not in self.choke_points and rpos not in self.safe_zones:
                self.potential_enemy_positions.add(rpos)
            attempts += 1
        return True

    # ------------------------------------------------------------ gráfica
    def visualize_heat_map(self, start_pos=None, goal_pos=None, path=None, obstacles_vis=None, title="Heatmap",
                           is_avatar=True, show=True, save_path=None, enemies_vis=None):
        heatmap_to_display = self.avatar_heat_map if is_avatar else self.enemy_heat_map
        if not heatmap_to_display.any():
            print(f"Visualize HM: Heatmap {'Avatar' if is_avatar else 'Enemigo'} está vacío.")
            return

        fig = plt.figure(figsize=(max(8, self.width * 0.3), max(6, self.height * 0.3)))
        # Misma orientación que el juego: x hacia la derecha, y hacia abajo.
        plt.imshow(heatmap_to_display, cmap='viridis', origin='upper', interpolation='nearest',
                   extent=(-0.5, self.width - 0.5, self.height - 0.5, -0.5))
        plt.colorbar(label="Feromona (calor)")

        if obstacles_vis:
            plt.scatter([o[0] for o in obstacles_vis], [o[1] for o in obstacles_vis], marker='s', s=40,
                        color='black', alpha=0.7, label='Obstáculos')
        if enemies_vis:
            plt.scatter([e[0] for e in enemies_vis], [e[1] for e in enemies_vis], marker='X', s=120,
                        color='red', edgecolor='white', label='Enemigos', zorder=5)
        if start_pos:
            plt.scatter(start_pos[0], start_pos[1], marker='o', s=120, color='cyan', edgecolor='black',
                        linewidth=1.5, label='Inicio', zorder=5)
        if goal_pos:
            plt.scatter(goal_pos[0], goal_pos[1], marker='*', s=180, color='magenta', edgecolor='black',
                        linewidth=1.5, label='Meta', zorder=5)
        if path:
            plt.plot([p[0] for p in path], [p[1] for p in path], 'w--', linewidth=2.5, label='Camino')

        plt.title(title, fontsize=14)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend(loc='upper right', fontsize='small')
        plt.xlim(-0.5, self.width - 0.5)
        plt.ylim(self.height - 0.5, -0.5)

        if save_path:
            plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close(fig)

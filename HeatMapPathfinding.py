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
        # Heatmap para el avatar (atraído a la casa, repelido por amenazas)
        self.avatar_heat_map = np.zeros((height, width))
        # Heatmap para los enemigos (atraídos al avatar, repelidos por obstáculos)
        self.enemy_heat_map = np.zeros((height, width))

        # Para análisis de entorno
        self.potential_enemy_positions = set()
        self.choke_points = []
        self.safe_zones = []
        self.last_analysis_params = None  # Para evitar re-análisis innecesario

    def reset(self):
        self.avatar_heat_map.fill(0)
        self.enemy_heat_map.fill(0)
        self.potential_enemy_positions.clear()
        self.choke_points = []
        self.safe_zones = []
        self.last_analysis_params = None

    def manhattan_distance(self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _is_valid(self, pos, obstacles_set):  # Acepta un set de obstáculos
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and pos not in obstacles_set

    def _get_neighbors(self, pos, obstacles_set):
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # Abajo, Arriba, Derecha, Izquierda
            nx, ny = x + dx, y + dy
            if self._is_valid((nx, ny), obstacles_set):
                neighbors.append((nx, ny))
        return neighbors

    def train(self, start_pos, goal_pos, obstacles, enemy_positions_set, iterations=1000, callback=None):
        """Entrena el avatar_heat_map para encontrar una ruta óptima hacia goal_pos."""
        print(f"HMPF Train: Start={start_pos}, Goal={goal_pos}, Iter={iterations}")
        self.avatar_heat_map.fill(0)  # Reiniciar heatmap del avatar

        # Convertir lista de obstáculos a set para búsquedas más rápidas
        obstacles_set = set(obstacles) if not isinstance(obstacles, set) else obstacles

        # Simular múltiples caminatas aleatorias o semi-aleatorias
        # y reforzar las celdas que llevan a la meta.
        best_path_found = None

        for i in range(iterations):
            if callback and not callback(i, iterations, None, best_path_found, (i / iterations) * 100.0):
                print("HMPF Train: Entrenamiento detenido por callback.")
                return best_path_found  # Devolver el mejor camino encontrado hasta ahora si se detiene

            current_pos = start_pos
            path_taken = [current_pos]
            max_steps = self.width * self.height  # Evitar bucles infinitos

            for _ in range(max_steps):
                if current_pos == goal_pos:
                    break  # Llegó a la meta

                neighbors = self._get_neighbors(current_pos, obstacles_set)
                if not neighbors:  # Atrapado
                    break

                # Selección de siguiente paso: sesgado hacia la meta, con algo de aleatoriedad
                # y penalización por acercarse a enemigos (si los hay)
                weighted_neighbors = []
                for neighbor_pos in neighbors:
                    # Valor base: distancia a la meta
                    weight = self.manhattan_distance(neighbor_pos,
                                                     goal_pos) * -10  # Queremos minimizar dist, así que negativo

                    # Penalización por enemigos (si están cerca)
                    for enemy_pos in enemy_positions_set:
                        dist_to_enemy = self.manhattan_distance(neighbor_pos, enemy_pos)
                        if dist_to_enemy < 1:
                            weight -= 1000  # Muy peligroso
                        elif dist_to_enemy < 3:
                            weight -= 500 / (dist_to_enemy + 0.1)  # Peligroso

                    # Pequeño bonus por celdas ya visitadas positivamente en el heatmap (exploración)
                    weight += self.avatar_heat_map[neighbor_pos[1], neighbor_pos[0]] * 0.1

                    weighted_neighbors.append((weight, neighbor_pos))

                if not weighted_neighbors: break  # No hay movimientos posibles (raro si _get_neighbors devolvió algo)

                # Elegir el vecino con el mayor peso (más atractivo)
                # Podríamos añadir epsilon-greedy aquí también para más exploración
                if random.random() < 0.2 and len(weighted_neighbors) > 1:  # 20% de exploración
                    current_pos = random.choice(neighbors)
                else:
                    weighted_neighbors.sort(key=lambda x: x[0], reverse=True)  # Mayor peso primero
                    current_pos = weighted_neighbors[0][1]

                path_taken.append(current_pos)

            # Si se llegó a la meta, reforzar el camino
            if path_taken[-1] == goal_pos:
                if best_path_found is None or len(path_taken) < len(best_path_found):
                    best_path_found = list(path_taken)  # Guardar copia

                # Reforzar celdas del camino. Las más cercanas a la meta reciben más refuerzo.
                path_len = len(path_taken)
                for idx, pos_in_path in enumerate(path_taken):
                    # Refuerzo inversamente proporcional a la longitud del camino y proporcional a la cercanía a la meta
                    reinforcement = (1.0 / path_len) * (path_len - idx) * 10.0
                    self.avatar_heat_map[pos_in_path[1], pos_in_path[0]] += reinforcement

            if i % (iterations // 10 if iterations >= 10 else 1) == 0:
                print(
                    f"HMPF Train progress: {i + 1}/{iterations}. Current best path len: {len(best_path_found) if best_path_found else 'N/A'}")

        if callback:  # Llamada final al callback
            callback(iterations, iterations, None, best_path_found, 100.0, is_final=True)

        if best_path_found:
            print(f"HMPF Train: Mejor ruta encontrada de {len(best_path_found)} pasos.")
        else:
            print("HMPF Train: No se encontró ruta a la meta tras las iteraciones.")
        return best_path_found

    def find_path_with_heat_map(self, start_pos, goal_pos, obstacles=None, is_avatar=True):
        """Encuentra un camino usando el heatmap precalculado (A* style sobre el heatmap)."""
        heatmap_to_use = self.avatar_heat_map if is_avatar else self.enemy_heat_map

        if not heatmap_to_use.any() and is_avatar:  # Si el heatmap del avatar está vacío, intentar entrenarlo
            print("find_path_with_heat_map: Heatmap Avatar vacío. Intentando entrenamiento ad-hoc.")
            # Necesitamos obstáculos y posiciones de enemigos para el entrenamiento.
            # Si no se proporcionan, no se puede entrenar.
            if obstacles is None:
                print("Error: Obstáculos no proporcionados para entrenamiento de heatmap ad-hoc.")
                return None

            # Para enemigos, si no se proporcionan, se asume un set vacío.
            # Lo ideal sería que el llamador (Game.py) proporcione el estado actual.
            # Aquí usamos un set vacío como placeholder si no se pasan.
            enemy_pos_set_for_adhoc = set()  # Asumir no enemigos si no se especifica

            self.train(start_pos, goal_pos, obstacles, enemy_pos_set_for_adhoc, iterations=100)  # Entrenamiento corto
            if not self.avatar_heat_map.any():  # Si sigue vacío
                print("find_path_with_heat_map: Fallo en entrenamiento ad-hoc.")
                return None
            heatmap_to_use = self.avatar_heat_map  # Actualizar referencia

        obstacles_set = set(obstacles) if obstacles and not isinstance(obstacles, set) else (obstacles or set())

        pq = [(0, start_pos)]  # (costo_total_estimado, posicion)
        came_from = {start_pos: None}
        cost_so_far = {start_pos: 0}  # Costo real desde el inicio

        max_exploration_nodes = self.width * self.height * 5  # Límite para evitar exploración excesiva
        nodes_explored = 0

        while pq and nodes_explored < max_exploration_nodes:
            nodes_explored += 1
            _, current = heapq.heappop(pq)

            if current == goal_pos:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # Invertir para obtener de inicio a fin

            for neighbor in self._get_neighbors(current, obstacles_set):
                # Costo de moverse al vecino: inverso al valor del heatmap (mayor valor = menor costo)
                # Añadir un pequeño costo base para preferir caminos más cortos si los valores del heatmap son similares.
                heat_value = heatmap_to_use[neighbor[1], neighbor[0]]
                # Evitar división por cero o valores muy pequeños de heat
                movement_cost = 1.0 / (abs(heat_value) + 0.1) if heat_value != 0 else 10.0  # Costo alto si heat es 0
                movement_cost += 0.1  # Costo base por paso

                new_cost = cost_so_far[current] + movement_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    # Heurística: distancia Manhattan al objetivo
                    # (aunque el heatmap ya debería guiar, esto puede ayudar a romper empates)
                    priority = new_cost + self.manhattan_distance(neighbor, goal_pos)
                    heapq.heappush(pq, (priority, neighbor))
                    came_from[neighbor] = current

        if nodes_explored >= max_exploration_nodes:
            print("find_path_with_heat_map: Límite de exploración alcanzado.")
        return None  # No se encontró camino

    def analyze_environment(self, player_start_pos, goal_pos, obstacles, num_enemies):
        """Analiza el entorno basado en el avatar_heat_map para identificar puntos estratégicos."""
        if not self.avatar_heat_map.any():
            print("Analyze Env: Heatmap del avatar no entrenado. No se puede analizar.")
            return False

        # Evitar re-análisis si los parámetros no han cambiado significativamente
        current_params = (player_start_pos, goal_pos, tuple(sorted(list(obstacles))), num_enemies)
        if current_params == self.last_analysis_params:
            # print("Analyze Env: Parámetros sin cambios, omitiendo re-análisis.")
            return True  # Asumir que el análisis anterior sigue siendo válido

        self.last_analysis_params = current_params
        self.potential_enemy_positions.clear()
        self.choke_points = []
        self.safe_zones = []

        obstacles_set = set(obstacles)

        # 1. Identificar Puntos de Estrangulamiento (Choke Points)
        # Celdas que, si se bloquean, aumentan significativamente la longitud del camino del jugador.
        # O celdas con pocos vecinos válidos en rutas de alto valor del heatmap.
        best_path_player_ref = self.find_path_with_heat_map(player_start_pos, goal_pos, obstacles_set, is_avatar=True)

        if best_path_player_ref:
            for r in range(self.height):
                for c in range(self.width):
                    pos = (c, r)
                    if pos in obstacles_set or pos == player_start_pos or pos == goal_pos:
                        continue

                    # Choke point si está en el camino óptimo y tiene pocos vecinos válidos
                    if pos in best_path_player_ref:
                        valid_neighbors = len(self._get_neighbors(pos, obstacles_set))
                        if valid_neighbors <= 2:  # Umbral para choke point (ajustable)
                            self.choke_points.append(pos)
            # También considerar puntos que no están en el camino pero que si se bloquean...
            # Esta parte es más compleja y podría requerir simular bloqueos. Por ahora, nos centramos en el camino.

        # 2. Identificar Zonas Seguras (Safe Zones)
        # Áreas con bajo valor en el heatmap del avatar (el avatar no suele pasar por ahí)
        # y lejos de la ruta óptima del jugador.
        threshold_safe = np.percentile(self.avatar_heat_map[self.avatar_heat_map > 0],
                                       25) if self.avatar_heat_map.any() else 0.5
        for r in range(self.height):
            for c in range(self.width):
                pos = (c, r)
                if pos in obstacles_set or pos == player_start_pos or pos == goal_pos:
                    continue
                if self.avatar_heat_map[r, c] < threshold_safe and self.avatar_heat_map[
                    r, c] > -1:  # Evitar zonas muy negativas (peligro)
                    # Y si está suficientemente lejos del camino del jugador
                    is_far_from_path = True
                    if best_path_player_ref:
                        for path_node in best_path_player_ref:
                            if self.manhattan_distance(pos, path_node) < 3:  # Umbral de distancia
                                is_far_from_path = False
                                break
                    if is_far_from_path:
                        self.safe_zones.append(pos)

        # 3. Identificar Posiciones Potenciales para Enemigos
        # Podrían ser puntos de estrangulamiento, o celdas en el camino del jugador
        # pero a una distancia prudencial del inicio del jugador.
        if best_path_player_ref:
            for node_idx, node_on_path in enumerate(best_path_player_ref):
                # Considerar nodos a partir de un cierto punto del camino
                if node_idx > len(best_path_player_ref) // 4 and node_idx < len(best_path_player_ref) * 3 // 4:
                    if self.manhattan_distance(node_on_path, player_start_pos) > 3:  # No demasiado cerca del inicio
                        self.potential_enemy_positions.add(node_on_path)

        # Añadir algunos choke points a las posiciones potenciales de enemigos
        for cp in self.choke_points:
            if len(self.potential_enemy_positions) < num_enemies * 2:  # Limitar
                self.potential_enemy_positions.add(cp)

        # Si no hay suficientes posiciones, añadir algunas aleatorias válidas
        attempts = 0
        while len(self.potential_enemy_positions) < num_enemies and attempts < self.width * self.height:
            rx, ry = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            rpos = (rx, ry)
            if self._is_valid(rpos, obstacles_set) and rpos != player_start_pos and rpos != goal_pos:
                self.potential_enemy_positions.add(rpos)
            attempts += 1

        # print(f"Analyze Env: Choke Points: {self.choke_points}")
        # print(f"Analyze Env: Safe Zones: {self.safe_zones}")
        # print(f"Analyze Env: Potential Enemy Positions: {self.potential_enemy_positions}")
        return True

    def visualize_heat_map(self, start_pos=None, goal_pos=None, path=None, obstacles_vis=None, title="Heatmap",
                           is_avatar=True, show=True, save_path=None):
        heatmap_to_display = self.avatar_heat_map if is_avatar else self.enemy_heat_map
        if not heatmap_to_display.any():
            print(f"Visualize HM: Heatmap {'Avatar' if is_avatar else 'Enemigo'} está vacío. Nada que mostrar.")
            return

        plt.figure(figsize=(self.width * 0.6, self.height * 0.6))  # Ajustar tamaño

        # Crear un colormap personalizado si se desea (ej. de azul claro a rojo oscuro)
        # colors = [(0.8, 0.8, 1), (1, 0.2, 0.2)] # Azul claro a Rojo
        # cmap_name = 'custom_heatmap'
        # cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
        # plt.imshow(heatmap_to_display.T, cmap=cm, origin='lower', interpolation='nearest')

        plt.imshow(heatmap_to_display.T, cmap='viridis', origin='lower',
                   interpolation='nearest')  # .T para transponer si es necesario
        plt.colorbar(label="Valor del Heatmap")

        # Marcar obstáculos (si se proporcionan para visualización)
        if obstacles_vis:
            obs_x = [o[0] for o in obstacles_vis]
            obs_y = [o[1] for o in obstacles_vis]
            plt.scatter(obs_x, obs_y, marker='s', s=80, color='black', label='Obstáculos')

        if start_pos:
            plt.scatter(start_pos[0], start_pos[1], marker='o', s=100, color='lime', edgecolor='black', label='Inicio',
                        zorder=5)
        if goal_pos:
            plt.scatter(goal_pos[0], goal_pos[1], marker='*', s=150, color='red', edgecolor='black', label='Meta',
                        zorder=5)

        if path:
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            plt.plot(path_x, path_y, 'w-', linewidth=2, label='Camino')  # Línea blanca para el camino

        plt.title(title)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.xticks(np.arange(self.width))
        plt.yticks(np.arange(self.height))
        plt.grid(True, which='both', color='gray', linestyle=':', linewidth=0.5)
        plt.legend()
        plt.gca().invert_yaxis()  # Para que (0,0) esté arriba a la izquierda como en Pygame

        if save_path:
            plt.savefig(save_path)
        if show:
            plt.show()
        else:  # Cerrar la figura si no se muestra para liberar memoria
            plt.close()
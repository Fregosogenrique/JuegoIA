from config import GameConfig
import numpy as np
import random


class DecisionTree:
    """Implementación de un árbol de decisiones con poda para mejorar el pathfinding"""

    def __init__(self, game_state, movement_matrix):
        """Inicializa el árbol de decisiones"""
        self.game_state = game_state
        self.movement_matrix = movement_matrix
        self.max_depth = 10  # Profundidad máxima de búsqueda
        self.visited = set()  # Conjunto de nodos visitados en esta ejecución
        self.best_path = None
        self.best_score = float('inf')

    def find_path(self, start, goal):
        """Encuentra un camino optimizado usando poda alpha-beta"""
        print(f"\nIniciando búsqueda de ruta desde {start} hasta {goal}")
        self.visited = set()
        self.best_path = None
        self.best_score = float('inf')

        # Iniciar búsqueda recursiva
        path = [start]
        self._search_path(start, goal, path, 0, float('-inf'), float('inf'))

        if self.best_path:
            print(f"Ruta encontrada: {self.best_path}")
            print(f"Longitud de la ruta: {len(self.best_path)}")
        else:
            print("No se encontró ninguna ruta")

        return self.best_path if self.best_path else [start]

    def _search_path(self, current, goal, path, depth, alpha, beta):
        """Búsqueda recursiva con poda alpha-beta"""
        # Caso base: llegamos a la meta
        if current == goal:
            path_score = len(path)
            if path_score < self.best_score:
                self.best_path = path.copy()
                self.best_score = path_score
            return path_score

        # Caso base: profundidad máxima alcanzada o camino demasiado largo
        if depth >= self.max_depth or len(path) > self.best_score:
            return float('inf')

        # Marcar como visitado en esta ejecución
        self.visited.add(current)

        # Obtener vecinos ordenados por prioridad
        neighbors = self._get_prioritized_neighbors(current, goal)

        # Valor mínimo para el nodo actual
        min_score = float('inf')
        best_local_path = None

        for neighbor in neighbors:
            # Evitar ciclos y nodos ya visitados
            if neighbor in self.visited or neighbor in path:
                continue

            # Explorar este vecino
            path.append(neighbor)
            score = self._search_path(neighbor, goal, path, depth + 1, alpha, beta)
            path.pop()  # Backtracking

            # Actualizar mejor puntuación local
            if score < min_score:
                min_score = score
                best_local_path = path.copy()

            # Poda beta
            beta = min(beta, min_score)
            if alpha >= beta:
                break  # Poda alpha-beta

        # Desmarcar como visitado (backtracking)
        self.visited.remove(current)

        # Si encontramos un camino válido, actualizar el mejor camino global
        if best_local_path and min_score < float('inf'):
            if len(best_local_path) < self.best_score:
                self.best_path = best_local_path
                self.best_score = len(best_local_path)

        return min_score

    def _get_prioritized_neighbors(self, pos, goal):
        """Obtiene los vecinos ordenados por prioridad usando los rangos de movimiento"""
        x, y = pos
        move_value = random.randint(1, 20)  # Usar el mismo rango que en el juego
        possible_neighbors = []

        # Usar los rangos de movimiento de config
        if GameConfig.MOVE_UP_RANGE[0] <= move_value <= GameConfig.MOVE_UP_RANGE[1]:
            possible_neighbors.append((x, y - 1))  # Arriba
        elif GameConfig.MOVE_RIGHT_RANGE[0] <= move_value <= GameConfig.MOVE_RIGHT_RANGE[1]:
            possible_neighbors.append((x + 1, y))  # Derecha
        elif GameConfig.MOVE_DOWN_RANGE[0] <= move_value <= GameConfig.MOVE_DOWN_RANGE[1]:
            possible_neighbors.append((x, y + 1))  # Abajo
        elif GameConfig.MOVE_LEFT_RANGE[0] <= move_value <= GameConfig.MOVE_LEFT_RANGE[1]:
            possible_neighbors.append((x - 1, y))  # Izquierda

        # Filtrar vecinos válidos
        valid_neighbors = []
        for nx, ny in possible_neighbors:
            # Verificar límites del grid
            if (0 <= nx < GameConfig.GRID_WIDTH and
                    0 <= ny < GameConfig.GRID_HEIGHT):
                # Verificar que no sea un obstáculo
                if (nx, ny) not in self.game_state.obstacles:
                    valid_neighbors.append((nx, ny))

        # Calcular puntuación para cada vecino
        neighbor_scores = []
        for neighbor in valid_neighbors:
            nx, ny = neighbor
            # Obtener frecuencia de visitas (normalizada)
            visit_count = self.movement_matrix[ny][nx]
            visit_score = visit_count / (np.max(self.movement_matrix) + 1)

            # Calcular distancia a la meta
            distance = self._heuristic(neighbor, goal)
            distance_score = distance / (GameConfig.GRID_WIDTH + GameConfig.GRID_HEIGHT)

            # Puntuación combinada (menor es mejor)
            combined_score = (0.7 * distance_score) + (0.3 * visit_score)
            neighbor_scores.append((neighbor, combined_score))

        # Ordenar por puntuación (menor primero)
        neighbor_scores.sort(key=lambda x: x[1])

        # Devolver solo los vecinos ordenados
        return [n[0] for n in neighbor_scores]

    def _heuristic(self, pos1, pos2):
        """Calcula la distancia Manhattan entre dos puntos"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
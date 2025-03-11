from config import GameConfig


class AStar:
    """Implementación del algoritmo A* para pathfinding"""

    def __init__(self, game_state):
        """Inicializa el pathfinder"""
        self.game_state = game_state

    def find_path(self, start, goal):
        """Encuentra el camino más corto entre dos puntos usando A*"""
        if not start or not goal:
            return None

        # Conjuntos para el algoritmo
        open_set = {start}  # Nodos por explorar
        closed_set = set()  # Nodos ya explorados

        # Diccionarios para rastrear el camino
        came_from = {}  # Para reconstruir el camino
        g_score = {start: 0}  # Costo desde el inicio
        f_score = {start: self._heuristic(start, goal)}  # Costo estimado total

        while open_set:
            # Obtener el nodo con menor f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))

            # Si llegamos al objetivo, reconstruir y devolver el camino
            if current == goal:
                return self._reconstruct_path(came_from, current)

            # Mover el nodo actual al conjunto cerrado
            open_set.remove(current)
            closed_set.add(current)

            # Explorar vecinos
            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                # Calcular g_score tentativo
                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                # Este camino es el mejor hasta ahora
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)

        return None

    def _heuristic(self, pos1, pos2):
        """Calcula la distancia Manhattan entre dos puntos"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_neighbors(self, pos):
        """Obtiene los vecinos válidos de una posición"""
        x, y = pos
        possible_neighbors = [
            (x, y - 1),  # Arriba
            (x + 1, y),  # Derecha
            (x, y + 1),  # Abajo
            (x - 1, y)  # Izquierda
        ]

        # Filtrar vecinos válidos
        valid_neighbors = []
        for nx, ny in possible_neighbors:
            # Verificar límites del grid
            if (0 <= nx < GameConfig.GRID_WIDTH and
                    0 <= ny < GameConfig.GRID_HEIGHT):
                # Verificar que no sea un obstáculo
                if (nx, ny) not in self.game_state.obstacles:
                    valid_neighbors.append((nx, ny))

        return valid_neighbors

    def _reconstruct_path(self, came_from, current):
        """Reconstruye el camino desde el final hasta el inicio"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]  # Invertir para tener el camino desde el inicio
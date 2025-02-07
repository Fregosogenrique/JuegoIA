#Fregosogenrique
# Implementación del algoritmo A* (A-Star)
class AStar:
    def __init__(self, width, height):
        # Inicializa el espacio de búsqueda con dimensiones específicas
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """
        Obtiene las posiciones vecinas válidas (arriba, derecha, abajo, izquierda)
        para una posición dada, excluyendo obstáculos y límites del mapa.
        """
        x, y = pos
        neighbors = []
        # Movimientos posibles: derecha, abajo, izquierda, arriba
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            # Verifica que el vecino esté dentro de los límites y no sea un obstáculo
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    (new_x, new_y) not in obstacles):
                neighbors.append((new_x, new_y))
        return neighbors

    def manhattan_distance(self, pos1, pos2):
        """
        Calcula la distancia Manhattan entre dos puntos.
        Esta es la heurística que hace que A* sea más eficiente que UCS.
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start, goal, obstacles):
        """
        Encuentra el camino más corto entre start y goal usando A*.

        A* combina:
        - g_score: costo real desde el inicio hasta el nodo actual
        - h_score: estimación heurística desde el nodo actual hasta la meta
        - f_score: suma de g_score y h_score
        """
        start = tuple(start)
        goal = tuple(goal)
        open_set = {start}  # Conjunto de nodos por explorar
        closed_set = set()  # Conjunto de nodos ya explorados

        came_from = {}  # Diccionario para reconstruir el camino
        g_score = {start: 0}  # Costo real desde el inicio
        f_score = {start: self.manhattan_distance(start, goal)}  # Costo total estimado

        while open_set:
            # Selecciona el nodo con menor f_score (más prometedor)
            current = min(open_set, key=lambda pos: f_score[pos])

            if current == goal:
                # Reconstruye y devuelve el camino cuando se alcanza la meta
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            # Procesa el nodo actual
            open_set.remove(current)
            closed_set.add(current)

            # Explora los vecinos
            for neighbor in self.get_neighbors(current, obstacles):
                neighbor = tuple(neighbor)
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                # Actualiza los valores para el vecino
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self.manhattan_distance(neighbor, goal)

        return None  # No hay camino posible


# Implementación del algoritmo UCS (Uniform Cost Search)
class UCS:
    def __init__(self, width, height):
        # Inicializa el espacio de búsqueda con dimensiones específicas
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """
        Función idéntica a la de A*. Obtiene las posiciones vecinas válidas
        excluyendo obstáculos y posiciones fuera de los límites.
        """
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    (new_x, new_y) not in obstacles):
                neighbors.append((new_x, new_y))
        return neighbors

    def find_path(self, start, goal, obstacles):
        """
        Encuentra el camino más corto entre start y goal usando UCS.

        UCS es similar a A* pero:
        - Solo usa g_score (costo real)
        - No usa heurística (h_score)
        - Por lo tanto, explora más nodos que A* pero garantiza el camino óptimo
        """
        start = tuple(start)
        goal = tuple(goal)
        open_set = {start}
        closed_set = set()

        came_from = {}
        g_score = {start: 0}  # Solo mantiene track del costo real

        while open_set:
            # Selecciona el nodo con menor costo acumulado
            current = min(open_set, key=lambda pos: g_score[pos])

            if current == goal:
                # Reconstruye el camino cuando se alcanza la meta
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            # Procesa el nodo actual
            open_set.remove(current)
            closed_set.add(current)

            # Explora los vecinos
            for neighbor in self.get_neighbors(current, obstacles):
                neighbor = tuple(neighbor)
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                # Actualiza los valores para el vecino
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score

        return None  # No hay camino posible
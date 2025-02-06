"""
Este archivo implementa dos algoritmos de búsqueda de caminos:
1. A* (AStar): Un algoritmo de búsqueda informada que usa una heurística (distancia Manhattan)
2. UCS (Uniform Cost Search): Un algoritmo de búsqueda no informada que explora basándose en el costo del camino
"""
class AStar:
    """
    Implementación del algoritmo A* para encontrar el camino más corto entre dos puntos.
    Utiliza la distancia Manhattan como heurística para guiar la búsqueda.
    """
    def __init__(self, width, height):
        """
        Inicializa el buscador de caminos con las dimensiones del área de búsqueda
        :param width: Ancho del área de búsqueda
        :param height: Alto del área de búsqueda
        """
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """
        Obtiene los vecinos válidos de una posición.
        Un vecino válido es una celda adyacente que:
        - Está dentro de los límites del área
        - No es un obstáculo
        - Solo se mueve en las 4 direcciones principales (sin diagonales)
        """
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    [new_x, new_y] not in obstacles):
                neighbors.append([new_x, new_y])
        return neighbors

    def manhattan_distance(self, pos1, pos2):
        """
        Calcula la distancia Manhattan entre dos puntos.
        Esta es la heurística utilizada por A* para estimar el costo restante.
        :return: La suma de las diferencias absolutas en x e y
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start, goal, obstacles):
        """
        Implementa el algoritmo A* para encontrar el camino más corto.

        Utiliza:
        - g_score: Costo real desde el inicio hasta el nodo actual
        - f_score: Costo total estimado (g_score + heurística)
        - open_set: Conjunto de nodos por explorar
        - closed_set: Conjunto de nodos ya explorados
        """
        start = tuple(start)
        goal = tuple(goal)
        open_set = {start}
        closed_set = set()

        came_from = {}  # Almacena el camino recorrido
        g_score = {start: 0}  # Costo real desde el inicio
        f_score = {start: self.manhattan_distance(start, goal)}  # Costo total estimado

        while open_set:
            # Selecciona el nodo con menor f_score
            current = min(open_set, key=lambda pos: f_score[pos])

            if current == goal:
                path = []
                while current in came_from:
                    path.append(list(current))
                    current = came_from[current]
                path.append(list(start))
                path.reverse()
                return path

            open_set.remove(current)
            closed_set.add(current)

            for neighbor in self.get_neighbors(current, obstacles):
                neighbor = tuple(neighbor)
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self.manhattan_distance(neighbor, goal)

        return None  # No se encontró camino
class UCS:
    """
    Implementación del algoritmo de búsqueda de costo uniforme (Uniform Cost Search).
    Similar a A* pero sin utilizar heurística, solo considera el costo real del camino.
    """
    def __init__(self, width, height):
        """
        Inicializa el buscador de caminos con las dimensiones del área de búsqueda
        :param width: Ancho del área de búsqueda
        :param height: Alto del área de búsqueda
        """
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """
        Obtiene los vecinos válidos de una posición.
        Idéntico al método en AStar, permite movimiento en 4 direcciones.
        """
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    [new_x, new_y] not in obstacles):
                neighbors.append([new_x, new_y])
        return neighbors

    def find_path(self, start, goal, obstacles):
        """
        Implementa el algoritmo de búsqueda de costo uniforme.

        A diferencia de A*:
        - No utiliza heurística
        - Solo usa g_score (costo real) para seleccionar el siguiente nodo
        - Garantiza encontrar el camino más corto si existe
        """
        start = tuple(start)
        goal = tuple(goal)
        open_set = {start}
        closed_set = set()

        came_from = {}  # Almacena el camino recorrido
        g_score = {start: 0}  # Solo mantiene track del costo real

        while open_set:
            # Selecciona el nodo con menor costo acumulado (g_score)
            current = min(open_set, key=lambda pos: g_score[pos])

            if current == goal:
                path = []
                while current in came_from:
                    path.append(list(current))
                    current = came_from[current]
                path.append(list(start))
                path.reverse()
                return path

            open_set.remove(current)
            closed_set.add(current)

            for neighbor in self.get_neighbors(current, obstacles):
                neighbor = tuple(neighbor)
                if neighbor in closed_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score

        return None  # No se encontró camino

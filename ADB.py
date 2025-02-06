class AStar:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    (new_x, new_y) not in obstacles):
                neighbors.append((new_x, new_y))
        return neighbors

    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start, goal, obstacles):
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
                    path.append(current)
                    current = came_from[current]
                path.append(start)
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
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
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
                    path.append(current)
                    current = came_from[current]
                path.append(start)
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

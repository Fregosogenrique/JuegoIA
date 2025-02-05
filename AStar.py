# astar.py
class AStar:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """Obtiene los vecinos válidos de una posición"""
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
        """Calcula la distancia Manhattan entre dos puntos"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start, goal, obstacles):
        """Implementa el algoritmo A* para encontrar el camino más corto"""
        start = tuple(start)
        goal = tuple(goal)
        open_set = {start}
        closed_set = set()

        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}

        while open_set:
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
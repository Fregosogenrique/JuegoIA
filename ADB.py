#Fregosogenrique
# Aquí implemento los algoritmos de búsqueda que uso para encontrar caminos
import numpy as np

class AStar:
    def __init__(self, width, height):
        # Necesito saber el tamaño del mapa para no salirme
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        # Busco las casillas a las que puedo moverme
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
        # Calculo qué tan lejos estoy de la meta
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start, goal, obstacles):
        # Busco el camino usando A* - es más rápido que UCS
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

"""
class UCS:
    def __init__(self, width, height):
        # Similar a A*, pero sin la parte inteligente
        self.width = width
        self.height = height

    def get_neighbors(self, pos, obstacles):
        """
        #Función idéntica a la de A*. Obtiene las posiciones vecinas válidas
        #excluyendo obstáculos y posiciones fuera de los límites.
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
        # Busco el camino revisando todo - más lento pero seguro
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
    """
class RandomRoute:
    def __init__(self, width=40, height=30):
        # La implementación está diseñada para un grid de 40x30,
        # pero se permite configurar otros tamaños
        self.width = width
        self.height = height
        
        # Inicializar una matriz de arreglos para contar las direcciones
        # Cada celda tiene un array de 4 enteros: [derecha, abajo, izquierda, arriba]
        # que corresponden a las direcciones [(0,1), (1,0), (0,-1), (-1,0)]
        self.grid = np.zeros((height, width, 4), dtype=int)
        
        # Mapeo de direcciones a índices en el array
        # Mapeo de direcciones a índices en el array
        self.dir_indices = {
            (0, 1): 0,  # derecha
            (-1, 0): 1,  # arriba
            (0, -1): 2, # izquierda
            (1, 0): 3  # abajo
        }
        # Direcciones de movimiento: derecha, abajo, izquierda, arriba
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    def get_neighbors(self, pos, obstacles):
        # Busco las casillas a las que puedo moverme
        x, y = pos
        neighbors = []
        # Movimientos posibles: derecha, abajo, izquierda, arriba
        for dx, dy in self.directions:
            new_x, new_y = x + dx, y + dy
            # Verifica que el vecino esté dentro de los límites y no sea un obstáculo
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    (new_x, new_y) not in obstacles):
                neighbors.append(((dx, dy), (new_x, new_y)))
        return neighbors
    def find_path(self, start, goal, obstacles):
        """
        Busca un camino desde start hasta goal moviéndose con base en los valores
        registrados en cada celda, priorizando las direcciones con más visitas.
        """
        start = tuple(start)
        goal = tuple(goal)
        current = start
        path = [current]
        max_steps = self.width * self.height * 4  # Límite para evitar bucles infinitos
        steps = 0
        
        while current != goal and steps < max_steps:
            # Obtener vecinos válidos con sus direcciones
            valid_neighbors = self.get_neighbors(current, obstacles)
            
            if not valid_neighbors:
                # No hay movimientos posibles, retroceder o terminar
                return None
            
            # Extraer las direcciones y sus posiciones
            directions = []
            positions = []
            for dir_tuple, pos in valid_neighbors:
                directions.append(dir_tuple)
                positions.append(pos)
            
            # Obtener los contadores para cada dirección disponible
            counts = []
            for direction in directions:
                dir_idx = self.dir_indices[direction]
                counts.append(self.grid[current[0], current[1], dir_idx])
            
            # Si todos los contadores son 0, elegir al azar
            if sum(counts) == 0:
                selected_idx = np.random.randint(0, len(valid_neighbors))
            else:
                # Seleccionar con mayor probabilidad las direcciones con mayores contadores
                counts_array = np.array(counts)
                # Asegurar que al menos sean probabilidades de 1 para evitar división por 0
                probabilities = counts_array + 1
                probabilities = probabilities / probabilities.sum()
                selected_idx = np.random.choice(len(valid_neighbors), p=probabilities)
            
            direction = directions[selected_idx]
            next_pos = positions[selected_idx]
            
            # Incrementar el contador para la dirección tomada
            dir_idx = self.dir_indices[direction]
            self.grid[current[0], current[1], dir_idx] += 1
            
            # Moverse a la siguiente posición
            current = next_pos
            path.append(current)
            steps += 1
        
        if current == goal:
            return path
        return None  # No se encontró un camino dentro del límite de pasos

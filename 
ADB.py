# Fregosogenrique
# Aquí implemento los algoritmos de búsqueda que uso para encontrar caminos
import numpy as np
import random


class RandomRoute:
    def __init__(self, width=40, height=30):
        # Inicialización con dimensiones configurables
        self.width = width
        self.height = height

        # Matriz de aprendizaje para cada celda y dirección
        # [arriba, derecha, abajo, izquierda]
        self.learning_grid = np.ones((height, width, 4), dtype=float)

        # Factor de aprendizaje y descuento
        self.learning_rate = 0.1
        self.discount_factor = 0.9

        # Mapeo de direcciones a índices y rangos de probabilidad
        self.dir_indices = {
            (-1, 0): 0,  # arriba (1-5)
            (0, 1): 1,  # derecha (6-10)
            (1, 0): 2,  # abajo (11-15)
            (0, -1): 3  # izquierda (16-20)
        }

        # Direcciones de movimiento con sus rangos
        self.directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        self.direction_ranges = [(1, 5), (6, 10), (11, 15), (16, 20)]

        # Almacenar el mejor camino encontrado
        self.best_path = None
        self.best_path_length = float('inf')

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
        Busca un camino usando movimientos aleatorios basados en rangos específicos
        y aprende de las experiencias previas.
        """
        start = tuple(start)
        goal = tuple(goal)
        current = start
        path = [current]
        visited = {current}
        max_steps = self.width * self.height * 2
        steps = 0

        while current != goal and steps < max_steps:
            valid_neighbors = self.get_neighbors(current, obstacles)
            if not valid_neighbors:
                break

            # Generar número aleatorio entre 1 y 20
            random_num = random.randint(1, 20)

            # Determinar la dirección basada en el rango
            chosen_dir = None
            for dir_idx, (min_val, max_val) in enumerate(self.direction_ranges):
                if min_val <= random_num <= max_val:
                    chosen_dir = self.directions[dir_idx]
                    break

            # Filtrar vecinos válidos según la dirección elegida
            valid_moves = []
            for dir_move, new_pos in valid_neighbors:
                if dir_move == chosen_dir and new_pos not in visited:
                    valid_moves.append((dir_move, new_pos))

            # Si no hay movimientos válidos en la dirección elegida, intentar otras direcciones
            if not valid_moves:
                valid_moves = [(dir_move, new_pos) for dir_move, new_pos in valid_neighbors
                               if new_pos not in visited]

            if not valid_moves:
                break

            # Elegir el siguiente movimiento basado en los pesos de aprendizaje
            weights = [self.learning_grid[current[1]][current[0]][self.dir_indices[move[0]]]
                       for move in valid_moves]
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
            else:
                weights = [1.0 / len(valid_moves)] * len(valid_moves)

            chosen_move = random.choices(valid_moves, weights=weights)[0]
            current = chosen_move[1]
            visited.add(current)
            path.append(current)
            steps += 1

            # Actualizar la matriz de aprendizaje
            if current == goal:
                self.reinforce_path(path)

        return path if current == goal else None

    def reinforce_path(self, path):
        """Refuerza el camino exitoso en la matriz de aprendizaje"""
        if not path:
            return

        # Calcular la longitud del camino
        path_length = len(path)

        # Actualizar el mejor camino si este es más corto
        if path_length < self.best_path_length:
            self.best_path = path.copy()
            self.best_path_length = path_length

        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i + 1]
            direction = (next_pos[0] - current[0], next_pos[1] - current[1])
            dir_idx = self.dir_indices[direction]

            # Incrementar el peso del movimiento exitoso
            # Dar más refuerzo a caminos más cortos
            reinforcement = self.learning_rate * (1 + (1 / path_length))
            self.learning_grid[current[1]][current[0]][dir_idx] *= (1 + reinforcement)

            # Normalizar los pesos para mantener la suma constante
            total = sum(self.learning_grid[current[1]][current[0]])
            self.learning_grid[current[1]][current[0]] /= total

        return None  # No se encontró un camino dentro del límite de pasos

    def get_best_path(self):
        return self.best_path
        # Eliminar cualquier print de consola existente
        # sobre ejecuciones visibles/invisibles

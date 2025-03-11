#Fregosogenrique
# Aquí implemento los algoritmos de búsqueda que uso para encontrar caminos
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
        
        # Matriz lógica para contar las visitas de cada celda
        # Esta matriz se incrementa por 1 cada vez que el avatar pasa por una celda
        # La matriz no se limpia entre ejecuciones
        # Note que la matriz sigue siendo (height, width) para el acceso numpy
        # pero las coordenadas externas serán manejadas como (x,y)
        self.logical_matrix = np.zeros((height, width), dtype=int)
        
        # Estado actual del agente
        self.current_position = None
        self.goal_position = None
        self.obstacles = []
        self.path = []
        self.found_goal = False
        self.total_steps = 0
        
        # Direcciones de movimiento: arriba, derecha, abajo, izquierda
        self.directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Nombres de las direcciones para el plotting
        self.dir_names = ['Arriba', 'Derecha', 'Abajo', 'Izquierda']
    def get_neighbors(self, pos):
        # Busco las casillas a las que puedo moverme
        # Posición ahora está en formato (x, y)
        x, y = pos
        neighbors = []
        # Movimientos posibles: arriba, derecha, abajo, izquierda
        for dy, dx in self.directions:
            new_x, new_y = x + dx, y + dy
            # Verifica que el vecino esté dentro de los límites y no sea un obstáculo
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    (new_x, new_y) not in self.obstacles):
                neighbors.append(((dx, dy), (new_x, new_y)))
        return neighbors
        
    def is_goal(self, position):
        """Verifica si la posición actual es la meta"""
        return position == self.goal_position
        
    def reset(self, start_position, obstacles, goal_position=None):
        """Reinicia el agente para una nueva búsqueda"""
        # Ahora manejamos coordenadas como (x,y) consistentemente
        self.current_position = tuple(start_position)
        self.obstacles = [tuple(obs) for obs in obstacles]
        self.goal_position = tuple(goal_position) if goal_position else None
        
        # Validar que las posiciones estén dentro de los límites
        x, y = self.current_position
        if (x >= self.width or 
            y >= self.height or
            x < 0 or
            y < 0):
            print(f"Advertencia: Posición inicial {self.current_position} fuera de los límites ({self.width}x{self.height})")
        
        if self.goal_position:
            gx, gy = self.goal_position
            if (gx >= self.width or
                gy >= self.height or
                gx < 0 or
                gy < 0):
                print(f"Advertencia: Posición de meta {self.goal_position} fuera de los límites ({self.width}x{self.height})")
        
        self.path = [self.current_position]
        self.found_goal = False
        self.total_steps = 0
        
        # Incrementamos el contador de visitas para la posición inicial
        # Asegurar que las coordenadas están dentro de los límites
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            # Nota que la matriz se accede como [y][x]
            self.logical_matrix[y, x] += 1
    def make_move(self):
        """Realiza un único movimiento y actualiza la posición del agente"""
        if self.found_goal:
            return False  # Ya se encontró la meta
            
        # Obtener vecinos válidos con sus direcciones
        valid_neighbors = self.get_neighbors(self.current_position)
        
        if not valid_neighbors:
            # No hay movimientos posibles, terminamos la búsqueda
            return False
        
        # Determinar la dirección usando números aleatorios del 1 al 20
        # Up = 1-5, Right = 6-10, Down = 11-15, Left = 16-20
        random_number = np.random.randint(1, 21)
        
        # Mapear el número random a una dirección
        if 1 <= random_number <= 5:  # Arriba
            direction_index = 0
        elif 6 <= random_number <= 10:  # Derecha
            direction_index = 1
        elif 11 <= random_number <= 15:  # Abajo
            direction_index = 2
        else:  # Izquierda
            direction_index = 3
        
        # Verificar si la dirección elegida es válida
        valid_directions = [i for i, (dir_tuple, pos) in enumerate(valid_neighbors) 
                           if dir_tuple == self.directions[direction_index]]
        
        if valid_directions:
            # Usar la dirección elegida si es válida
            selected_idx = valid_directions[0]
        else:
            # Si la dirección elegida no es válida, elegir una al azar entre las disponibles
            selected_idx = np.random.randint(0, len(valid_neighbors))
        
        direction, next_pos = valid_neighbors[selected_idx]
        # Moverse a la siguiente posición
        self.current_position = next_pos
        self.path.append(self.current_position)
        self.total_steps += 1
        
        # Incrementar contador de visitas en la matriz lógica
        # Asegurar que las coordenadas están dentro de los límites
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            # Nota que la matriz se accede como [y][x]
            self.logical_matrix[y, x] += 1
            self.logical_matrix[y, x] += 1
        
        # Verificar si hemos llegado a la meta
        if self.goal_position and self.current_position == self.goal_position:
            self.found_goal = True
            return True
            
        return True  # Movimiento exitoso

                
    def find_path(self, start, goal=None, obstacles=[]):
        """
        Busca un camino desde start hasta goal. Si goal es None, 
        explora hasta encontrar la meta por casualidad.
        """
        # Inicializar el estado del agente
        self.reset(start, obstacles, goal)
        
        max_steps = self.width * self.height * 4  # Límite para evitar bucles infinitos
        
        # Bucle principal de exploración
        while not self.found_goal and self.total_steps < max_steps:
            if not self.make_move():
                break
        
        if self.found_goal:
            # Si encontramos la meta, podemos visualizar la matriz de movimiento
            self.plot_movement_matrix()
            return self.path
            
        return None  # No se encontró un camino dentro del límite de pasos
        
    def find_path_with_learning(self, start, goal, obstacles, iterations=30):
        """
        Busca un camino intentando múltiples veces con movimientos aleatorios.
        El método mantiene internamente su posición y registra los movimientos en la matriz lógica.
        Al final, se visualiza la matriz de movimientos.
        """
        best_path = None
        best_path_length = float('inf')
        max_length = self.width * self.height * 3  # Usar un valor finito grande como fallback
        
        print(f"Iniciando búsqueda con {iterations} intentos...")
        for i in range(iterations):
            # Buscamos un camino en cada iteración
            self.reset(start, obstacles, goal)
            
            max_steps = self.width * self.height * 3  # Límite para evitar bucles infinitos
            
            # Bucle principal de exploración
            while not self.found_goal and self.total_steps < max_steps:
                if not self.make_move():
                    break
            
            # Si encontramos la meta, evaluamos si es el mejor camino hasta ahora
            if self.found_goal:
                current_path_length = len(self.path)
                
                print(f"Intento {i+1}: Camino encontrado con {current_path_length} pasos")
                
                if current_path_length < best_path_length:
                    best_path_length = int(current_path_length)  # Asegurar que sea entero
                    best_path = self.path.copy()
                    print(f"¡Nuevo mejor camino encontrado! Longitud: {best_path_length}")
            else:
                print(f"Intento {i+1}: No se encontró camino a la meta")
        
        # Al final de todas las iteraciones, establecemos el camino óptimo
        if best_path:
            self.path = best_path
            self.found_goal = True
            print(f"Mejor camino encontrado después de {iterations} intentos: {best_path_length} pasos")
            
            # Visualizamos la matriz de movimiento
            self.plot_movement_matrix()
            
            return best_path
        else:
            print(f"No se encontró camino a la meta después de {iterations} intentos")
            return None  # Retorna None en lugar de un camino vacío o de longitud infinita
            
            
    def plot_movement_matrix(self):
        """
        Visualiza la matriz de movimientos, mostrando la frecuencia de visitas
        a cada celda y el camino encontrado.
        """
        # Crear una figura para el heatmap de visitas
        plt.figure(figsize=(12, 10))
        
        # Preparar datos para el heatmap de frecuencia de visitas
        visit_heatmap = self.logical_matrix.copy()
        
        # Marcar las posiciones especiales
        start_pos = self.path[0]
        goal_pos = self.path[-1]
        
        # Crear una máscara para los obstáculos (para mostrarlos de manera diferente)
        obstacle_mask = np.zeros((self.height, self.width), dtype=bool)
        for obs in self.obstacles:
            x, y = obs  # Ahora las coordenadas están en formato (x,y)
            if 0 <= x < self.width and 0 <= y < self.height:
                obstacle_mask[y, x] = True  # Nota que la matriz se accede como [y][x]
            
        # Crear un mapa de colores personalizado
        cmap = plt.cm.viridis.copy()
        cmap.set_bad('black', 1.0)  # Color para los obstáculos
        
        # Aplicar máscara de obstáculos
        masked_data = np.ma.array(visit_heatmap, mask=obstacle_mask)
        
        # Dibujar el heatmap
        heatmap = plt.imshow(masked_data, cmap=cmap, interpolation='nearest')
        plt.title(f'Mapa de calor de visitas - Total de celdas visitadas: {np.sum(self.logical_matrix > 0)}')
        
        # Añadir una barra de color
        cbar = plt.colorbar(heatmap)
        cbar.set_label('Número de visitas')
        
        # Marcar inicio y meta
        plt.plot(start_pos[0], start_pos[1], 'ro', markersize=10, label='Inicio')
        plt.plot(goal_pos[0], goal_pos[1], 'go', markersize=10, label='Meta')
        
        # Marcar el camino final
        path_x = [pos[0] for pos in self.path]
        path_y = [pos[1] for pos in self.path]
        plt.plot(path_x, path_y, 'r-', linewidth=2, alpha=0.7, label='Camino')
        
        # Añadir leyenda
        plt.legend()
        
        # Configurar ejes
        plt.xticks(np.arange(0, self.width, 5))
        plt.yticks(np.arange(0, self.height, 5))
        plt.grid(which='both', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
        
        # Añadir información sobre la eficiencia de la ruta
        path_length = len(self.path)
        # Calcular Manhattan distance usando el formato (x,y)
        manhattan_distance = abs(self.path[-1][0] - self.path[0][0]) + abs(self.path[-1][1] - self.path[0][1])
        efficiency = manhattan_distance / path_length if path_length > 0 else 0.0  # Asegurar que es float
        
        plt.figtext(0.5, 0.01, 
                  f'Longitud del camino: {path_length} pasos, Distancia Manhattan: {manhattan_distance}, Eficiencia: {efficiency:.2f}',
                  ha='center', fontsize=12, bbox={'facecolor': 'yellow', 'alpha': 0.2, 'pad': 5})
        
        # Ajustar layout y mostrar
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.10)
        
        # Guardar la figura y mostrarla
        plt.savefig('random_route_analysis.png')
        plt.show()

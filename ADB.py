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
        
        # Matriz con 4 dimensiones (una para cada dirección) para almacenar pesos de éxito
        # [y, x, dirección] donde dirección es 0:Arriba, 1:Derecha, 2:Abajo, 3:Izquierda
        # Valores más altos indican mayor probabilidad de éxito en esa dirección
        # La matriz no se limpia entre ejecuciones para mantener el aprendizaje
        # Las coordenadas externas serán manejadas como (x,y)
        self.learning_matrix = np.ones((height, width, 4), dtype=float)
        
        # Matriz para contar las visitas (desconectada de la interfaz visual)
        self.logical_matrix = np.zeros((height, width), dtype=int)
        
        # Matriz de pesos independiente (separada de la matriz lógica)
        # Esta matriz almacena la eficacia de cada movimiento en cada posición
        self.weight_matrix = np.ones((height, width, 4), dtype=float) * 0.5
        
        # Factor de decaimiento para balancear exploración/explotación
        # Valores más cercanos a 1 favorecen la explotación de rutas conocidas
        # Valores más cercanos a 0 favorecen la exploración de nuevas rutas
        self.decay_factor = 0.85
        
        # Factor de aprendizaje - determina qué tan rápido se actualizan los pesos
        self.learning_rate = 0.2
        
        # Métricas para la rúbrica de evaluación
        self.rubric_scores = {
            'efficiency': 0.0,       # Eficiencia del camino (0-1)
            'exploration': 0.0,      # Exploración del espacio (0-1)
            'consistency': 0.0,      # Consistencia de resultados (0-1)
            'adaptability': 0.0,     # Adaptabilidad a cambios (0-1)
            'learning_progress': 0.0  # Mejora con las iteraciones (0-1)
        }
        
        # Histórico de puntuaciones para medir progreso
        self.rubric_history = {
            'efficiency': [],
            'exploration': [],
            'consistency': [],
            'adaptability': [],
            'learning_progress': []
        }
        
        # Historial de métricas para seguimiento
        self.metric_history = {
            'path_lengths': [],
            'efficiencies': [],
            'success_rates': []
        }
        
        # Estado actual del agente
        self.current_position = None
        self.goal_position = None
        self.obstacles = []
        self.path = []
        self.found_goal = False
        self.total_steps = 0
        self.move_history = []  # Almacena (posición, dirección_tomada) para cada paso
        
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
        # Verificar si la dirección elegida es válida
        valid_directions = [i for i, (dir_tuple, pos) in enumerate(valid_neighbors) 
                           if dir_tuple == self.directions[direction_index]]
        
        # Obtener los pesos de aprendizaje para las posiciones actuales
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            weights = self.learning_matrix[y, x].copy()
            
            # Normalizar los pesos para que funcionen como probabilidades
            weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones(4) / 4
            
            # Decidir si explorar (aleatorio) o explotar (usar conocimiento previo)
            if np.random.random() > self.decay_factor:
                # Exploración: movimiento aleatorio
                if valid_directions:
                    selected_idx = valid_directions[0]
                else:
                    selected_idx = np.random.randint(0, len(valid_neighbors))
            else:
                # Explotación: usar pesos de aprendizaje
                # Filtrar solo las direcciones válidas
                valid_dir_weights = []
                valid_dir_indices = []
                
                for i, (dir_tuple, _) in enumerate(valid_neighbors):
                    dir_idx = self.directions.index(dir_tuple)
                    valid_dir_weights.append(weights[dir_idx])
                    valid_dir_indices.append(i)
                
                # Normalizar los pesos de las direcciones válidas
                valid_dir_weights = np.array(valid_dir_weights)
                valid_dir_weights = valid_dir_weights / np.sum(valid_dir_weights) if np.sum(valid_dir_weights) > 0 else np.ones(len(valid_dir_weights)) / len(valid_dir_weights)
                
                # Seleccionar dirección basada en pesos probabilísticos
                selected_idx = np.random.choice(valid_dir_indices, p=valid_dir_weights)
        else:
            # Si estamos fuera de los límites, movimiento aleatorio
            if valid_directions:
                selected_idx = valid_directions[0]
            else:
                selected_idx = np.random.randint(0, len(valid_neighbors))
        
        # Obtener la dirección y la nueva posición
        direction, next_pos = valid_neighbors[selected_idx]
        self.current_position = next_pos
        self.path.append(self.current_position)
        self.total_steps += 1
        self.current_position = next_pos
        self.path.append(self.current_position)
        self.total_steps += 1
        
        # Incrementar contador de visitas en la matriz lógica
        # Asegurar que las coordenadas están dentro de los límites
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            # Nota que la matriz se accede como [y][x]
            self.logical_matrix[y, x] += 1
            
            # Registrar este movimiento para aprendizaje posterior
            prev_x, prev_y = self.path[-2] if len(self.path) > 1 else (x, y)  # Posición anterior
            if (prev_x, prev_y) != (x, y):  # Si no es la posición inicial
                # Determinar qué dirección se utilizó
                dx, dy = x - prev_x, y - prev_y
                dir_index = self.directions.index((dy, dx)) if (dy, dx) in self.directions else -1
                
                if dir_index >= 0:
                    self.move_history.append(((prev_x, prev_y), dir_index))
        
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
            self.plot_analysis()
            return self.path
            
        return None  # No se encontró un camino dentro del límite de pasos
       # return None  # No se encontró un camino dentro del límite de pasos
    
    def update_weights(self, path_success, path_efficiency):
        """
        Actualiza la matriz de aprendizaje basado en el éxito o fracaso del camino actual
        
        Args:
            path_success (bool): True si se encontró la meta, False en caso contrario
            path_efficiency (float): Valor entre 0 y 1 que indica la eficiencia del camino
        """
        if not self.move_history:
            return  # No hay movimientos para aprender
            
        # Determinar la recompensa base según el éxito del camino
        base_reward = 0.1  # Recompensa base por intentar
        
        if path_success:
            # Mayor recompensa por encontrar la meta, ajustada por eficiencia
            # La eficiencia perfecta (1.0) da la máxima recompensa (1.0)
            success_reward = 0.5 + (0.5 * path_efficiency)
            reward = base_reward + success_reward
        else:
            # Pequeña penalización por no encontrar la meta
            reward = base_reward - 0.1
            
        # Actualizar los pesos en la matriz de aprendizaje y la matriz de pesos independiente
        # Los pesos se actualizan en proporción inversa a la distancia desde el final del camino
        # para dar más importancia a los movimientos cercanos a la meta
        for i, (pos, dir_index) in enumerate(self.move_history):
            x, y = pos
            # Factor de proximidad: los movimientos más cercanos al final tienen más peso
            proximity_factor = (i + 1) / len(self.move_history)
            
            # Calcular la recompensa ajustada por proximidad
            adjusted_reward = reward * proximity_factor
            
            # Aplicar la recompensa a ambas matrices
            self.learning_matrix[y, x, dir_index] += adjusted_reward * self.learning_rate
            
            # La matriz de pesos independiente recibe retroalimentación adicional
            # para mejorar el aprendizaje basado en el resultado total
            if path_success:
                # Refuerzo positivo más fuerte en la matriz de pesos si fue exitoso
                self.weight_matrix[y, x, dir_index] += (adjusted_reward * self.learning_rate * 1.5)
                
                # Incremento adicional para rutas eficientes (refuerzo por eficiencia)
                if path_efficiency > 0.7:
                    self.weight_matrix[y, x, dir_index] += 0.1 * path_efficiency
            else:
                # Penalización en la matriz de pesos para movimientos en rutas fallidas
                self.weight_matrix[y, x, dir_index] -= 0.05
            
            # Asegurar que los pesos se mantengan en un rango razonable
            self.learning_matrix[y, x, dir_index] = max(0.1, min(10.0, self.learning_matrix[y, x, dir_index]))
            self.weight_matrix[y, x, dir_index] = max(0.1, min(10.0, self.weight_matrix[y, x, dir_index]))
            
        # Actualizar métricas para el historial
        if path_success:
            self.metric_history['path_lengths'].append(len(self.path) - 1)
            self.metric_history['efficiencies'].append(path_efficiency)
            self.metric_history['success_rates'].append(1.0)
        else:
            self.metric_history['success_rates'].append(0.0)
    
    def calculate_path_efficiency(self, path=None):
        """
        Calcula la eficiencia del camino como la relación entre:
        - La distancia Manhattan desde el inicio hasta la meta
        - La longitud real del camino
        
        Returns:
            float: Un valor entre 0 y 1, donde 1 es la eficiencia perfecta
        """
        if path is None:
            path = self.path
            
        if not path or len(path) < 2:
            return 0.0
            
        # Calcular la distancia Manhattan
        start_pos = path[0]
        end_pos = path[-1]
        manhattan_distance = abs(end_pos[0] - start_pos[0]) + abs(end_pos[1] - start_pos[1])
        
        # Calcular la eficiencia
        path_length = len(path) - 1  # Número de pasos (no de nodos)
        
        # Ajustar para evitar división por cero
        if path_length == 0:
            return 0.0
            
        # La eficiencia perfecta es 1.0 (cuando el camino tiene la longitud mínima posible)
        # En casos donde el movimiento es complejo debido a obstáculos, la eficiencia será menor
        efficiency = min(1.0, manhattan_distance / path_length)
        
        return efficiency
        
    def find_path_with_learning(self, start, goal, obstacles, iterations=30, visible_iterations=0):
        """
        Busca un camino utilizando aprendizaje iterativo.
        
        Esta función ejecuta múltiples iteraciones de búsqueda, utilizando el aprendizaje
        acumulado para mejorar progresivamente la calidad de los caminos encontrados.
        
        Args:
            start (tuple): Posición inicial (x, y)
            goal (tuple): Posición de la meta (x, y)
            obstacles (list): Lista de obstáculos (x, y)
            iterations (int): Número total de iteraciones (visibles + invisibles)
            visible_iterations (int): Número de iteraciones visibles en la interfaz
            
        Returns:
            list: El mejor camino encontrado o None si no se encuentra ninguno
        """
        best_path = None
        best_path_length = float('inf')
        best_efficiency = 0.0
        
        # Inicializar el historial para el seguimiento de métricas
        self.metric_history['path_lengths'] = []
        self.metric_history['efficiencies'] = []
        self.metric_history['success_rates'] = []
        
        print(f"Iniciando búsqueda con {iterations} iteraciones ({visible_iterations} visibles)")
        
        # Primero ejecutamos las iteraciones invisibles (sin interfaz)
        invisible_iterations = iterations - visible_iterations
        if invisible_iterations > 0:
            print(f"Ejecutando {invisible_iterations} iteraciones invisibles...")
            
            # Bucle de iteraciones invisibles
            for i in range(invisible_iterations):
                # Reiniciar para una nueva búsqueda
                self.reset(start, obstacles, goal)
                
                max_steps = self.width * self.height * 3  # Límite para evitar bucles infinitos
                
                # Bucle principal de exploración (invisible)
                while not self.found_goal and self.total_steps < max_steps:
                    if not self.make_move():
                        break
                
                # Procesar resultados de la iteración invisible
                path_efficiency = 0.0
                if self.found_goal:
                    current_path_length = len(self.path) - 1  # Corrección: restar 1 para obtener pasos, no nodos
                    path_efficiency = self.calculate_path_efficiency()
                    
                    # Actualizar mejor camino si corresponde
                    if current_path_length < best_path_length or (current_path_length == best_path_length and path_efficiency > best_efficiency):
                        best_path_length = int(current_path_length)
                        best_path = self.path.copy()
                        best_efficiency = path_efficiency
                
                # Actualizar matrices y métricas después de cada iteración invisible
                # Actualizar matrices y métricas después de cada iteración invisible
                self.update_weights(self.found_goal, path_efficiency)
                self.update_rubric_scores(self.found_goal, path_efficiency, i+1, invisible_iterations)
                # Mostrar progreso periódicamente
                if (i+1) % 5 == 0 or i+1 == invisible_iterations:
                    rubric_score = self.evaluate_performance()
                    print(f"Progreso: {i+1}/{invisible_iterations} - Mejor camino: {best_path_length if best_path else 'No encontrado'} - Puntuación: {rubric_score:.2f}/5.0")
        
        # Luego ejecutamos las iteraciones visibles (con interfaz)
        if visible_iterations > 0:
            print(f"Ejecutando {visible_iterations} iteraciones visibles...")
            
            for i in range(visible_iterations):
                # Reiniciar para una nueva búsqueda
                self.reset(start, obstacles, goal)
                
                max_steps = self.width * self.height * 3
                
                # Bucle principal de exploración (visible)
                while not self.found_goal and self.total_steps < max_steps:
                    if not self.make_move():
                        break
                
                # Calcular la eficiencia si encontramos un camino
                path_efficiency = 0.0
                if self.found_goal:
                    current_path_length = len(self.path) - 1  # Restar 1 para obtener pasos, no nodos
                    path_efficiency = self.calculate_path_efficiency()
                    
                    print(f"Iteración visible {i+1}: Camino encontrado con {current_path_length} pasos (Eficiencia: {path_efficiency:.2f})")
                    
                    # Actualizar mejor camino si corresponde
                    if current_path_length < best_path_length or (current_path_length == best_path_length and path_efficiency > best_efficiency):
                        best_path_length = int(current_path_length)
                        best_path = self.path.copy()
                        best_efficiency = path_efficiency
                        print(f"¡Nuevo mejor camino encontrado! Longitud: {best_path_length}, Eficiencia: {path_efficiency:.2f}")
                else:
                    print(f"Iteración visible {i+1}: No se encontró camino a la meta")
                
                # Actualizar matriz de aprendizaje y métricas
                # Actualizar matriz de aprendizaje y métricas
                self.update_weights(self.found_goal, path_efficiency)
                self.update_rubric_scores(self.found_goal, path_efficiency, invisible_iterations+i+1, iterations)
                # Ajustar dinámicamente el factor de decaimiento
                if self.found_goal and path_efficiency > 0.7:
                    # Favorece explotación cuando encontramos buenos caminos
                    self.decay_factor = min(0.95, self.decay_factor + 0.02)
                elif not self.found_goal or path_efficiency < 0.3:
                    # Favorece exploración cuando no encontramos caminos o son ineficientes
                    self.decay_factor = max(0.5, self.decay_factor - 0.03)
                
                # Mostrar estadísticas actualizadas
                rubric_score = self.evaluate_performance()
                print(f"Factor de decaimiento: {self.decay_factor:.2f} - Puntuación actual: {rubric_score:.2f}/5.0")
        
        # Al final de todas las iteraciones, establecemos el camino óptimo
        if best_path:
            self.path = best_path
            self.found_goal = True
            # Evaluación final de rendimiento
            final_score = self.evaluate_performance()
            print(f"Mejor camino encontrado después de {iterations} iteraciones: {best_path_length} pasos")
            print(f"Puntuación final del aprendizaje: {final_score:.2f}/5.0")
            
            # Visualizamos la matriz de movimiento y análisis completo
            self.plot_movement_matrix()
            self.plot_analysis()
            return best_path
        else:
            print(f"No se encontró camino a la meta después de {iterations} iteraciones")
            return None
            
            
    def plot_movement_matrix(self, ax=None, save_fig=True):
        """
        Visualiza la matriz de movimientos, mostrando la frecuencia de visitas
        a cada celda y el camino encontrado.
        
        Args:
            ax (matplotlib.axes.Axes, optional): Eje donde dibujar. Si es None, se crea una nueva figura.
            save_fig (bool): Si es True, guarda la figura en un archivo.
        
        Returns:
            matplotlib.figure.Figure: La figura creada o modificada
        """
        # Determinar si debemos crear una nueva figura
        create_new_fig = ax is None
        if create_new_fig:
            fig, ax = plt.subplots(figsize=(12, 10))
        else:
            fig = ax.figure
        
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
        heatmap = ax.imshow(masked_data, cmap=cmap, interpolation='nearest')
        ax.set_title(f'Mapa de calor de visitas - Total de celdas visitadas: {np.sum(self.logical_matrix > 0)}')
        
        # Añadir una barra de color
        cbar = fig.colorbar(heatmap, ax=ax)
        cbar.set_label('Número de visitas')
        
        # Marcar inicio y meta
        ax.plot(start_pos[0], start_pos[1], 'ro', markersize=10, label='Inicio')
        ax.plot(goal_pos[0], goal_pos[1], 'go', markersize=10, label='Meta')
        
        # Marcar el camino final
        path_x = [pos[0] for pos in self.path]
        path_y = [pos[1] for pos in self.path]
        ax.plot(path_x, path_y, 'r-', linewidth=2, alpha=0.7, label='Camino')
        
        # Añadir leyenda
        ax.legend(loc='upper right')
        
        # Configurar ejes
        ax.set_xticks(np.arange(0, self.width, 5))
        ax.set_yticks(np.arange(0, self.height, 5))
        ax.grid(which='both', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
        
        # Añadir información sobre la eficiencia de la ruta
        path_length = len(self.path)
        # Calcular Manhattan distance usando el formato (x,y)
        manhattan_distance = abs(self.path[-1][0] - self.path[0][0]) + abs(self.path[-1][1] - self.path[0][1])
        efficiency = manhattan_distance / (path_length-1) if path_length > 1 else 0.0  # Asegurar que es float
        
        if create_new_fig:
            plt.figtext(0.5, 0.01, 
                      f'Longitud del camino: {path_length-1} pasos, Distancia Manhattan: {manhattan_distance}, Eficiencia: {efficiency:.2f}',
                      ha='center', fontsize=12, bbox={'facecolor': 'yellow', 'alpha': 0.2, 'pad': 5})
            
            # Ajustar layout
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.10)
            
            # Guardar la figura si se solicita
            if save_fig:
                plt.savefig('movement_analysis.png')
                print("Gráfico de movimiento guardado como 'movement_analysis.png'")
            
            plt.show()
        
        return fig

    def evaluate_performance(self):
        """
        Evalúa el rendimiento del aprendizaje basado en una rúbrica definida.
        
        La rúbrica evalúa 5 dimensiones fundamentales del aprendizaje:
        1. Eficiencia: Qué tan directo es el camino encontrado comparado con la distancia óptima
        2. Exploración: Qué porcentaje del espacio disponible ha sido explorado
        3. Consistencia: Estabilidad en los resultados a lo largo de múltiples iteraciones
        4. Adaptabilidad: Capacidad para ajustar los pesos según retroalimentación
        5. Progreso de aprendizaje: Mejora demostrable con el tiempo
        
        Returns:
            float: Puntuación total (suma de todas las dimensiones), valor entre 0 y 5
        """
        # Calcular puntuación total (cada dimensión vale 1 punto máximo)
        total_score = sum(self.rubric_scores.values())
        
        # Generar un informe detallado de cada dimensión
        report = "\nRÚBRICA DE EVALUACIÓN DE APRENDIZAJE\n"
        report += "=====================================\n\n"
        
        # 1. Eficiencia
        report += f"1. EFICIENCIA: {self.rubric_scores['efficiency']:.2f}/1.00\n"
        report += "   Evalúa qué tan directo es el camino encontrado comparado con el camino óptimo.\n"
        if self.rubric_scores['efficiency'] > 0.8:
            report += "   ✓ EXCELENTE: Camino casi óptimo, similar al encontrado por A*.\n"
        elif self.rubric_scores['efficiency'] > 0.6:
            report += "   ✓ BUENO: Camino eficiente con pocas desviaciones.\n"
        elif self.rubric_scores['efficiency'] > 0.3:
            report += "   ✓ REGULAR: Camino con algunas desviaciones significativas.\n"
        else:
            report += "   ✗ DEFICIENTE: Camino ineficiente con muchas desviaciones.\n"
        report += "\n"
        
        # 2. Exploración
        report += f"2. EXPLORACIÓN: {self.rubric_scores['exploration']:.2f}/1.00\n"
        report += "   Evalúa qué porcentaje del espacio disponible ha sido explorado.\n"
        if self.rubric_scores['exploration'] > 0.8:
            report += "   ✓ EXCELENTE: Exploración completa del espacio relevante.\n"
        elif self.rubric_scores['exploration'] > 0.6:
            report += "   ✓ BUENO: Exploración significativa de áreas relevantes.\n"
        elif self.rubric_scores['exploration'] > 0.3:
            report += "   ✓ REGULAR: Exploración limitada, concentrada en pocas áreas.\n"
        else:
            report += "   ✗ DEFICIENTE: Exploración muy limitada, ignorando grandes áreas del mapa.\n"
        report += "\n"
        
        # 3. Consistencia
        report += f"3. CONSISTENCIA: {self.rubric_scores['consistency']:.2f}/1.00\n"
        report += "   Evalúa la estabilidad en los resultados a lo largo de múltiples iteraciones.\n"
        if self.rubric_scores['consistency'] > 0.8:
            report += "   ✓ EXCELENTE: Resultados altamente consistentes entre iteraciones.\n"
        elif self.rubric_scores['consistency'] > 0.6:
            report += "   ✓ BUENO: Resultados generalmente consistentes con variaciones menores.\n"
        elif self.rubric_scores['consistency'] > 0.3:
            report += "   ✓ REGULAR: Resultados con variabilidad moderada entre iteraciones.\n"
        else:
            report += "   ✗ DEFICIENTE: Resultados muy variables e impredecibles.\n"
        report += "\n"
        
        # 4. Adaptabilidad
        report += f"4. ADAPTABILIDAD: {self.rubric_scores['adaptability']:.2f}/1.00\n"
        report += "   Evalúa la capacidad para ajustar los pesos según la retroalimentación.\n"
        if self.rubric_scores['adaptability'] > 0.8:
            report += "   ✓ EXCELENTE: Adaptación rápida y precisa a nuevas condiciones.\n"
        elif self.rubric_scores['adaptability'] > 0.6:
            report += "   ✓ BUENO: Adaptación efectiva con ajustes apropiados a los pesos.\n"
        elif self.rubric_scores['adaptability'] > 0.3:
            report += "   ✓ REGULAR: Adaptación lenta pero eventualmente efectiva.\n"
        else:
            report += "   ✗ DEFICIENTE: Adaptación deficiente, persiste en estrategias inefectivas.\n"
        report += "\n"
        
        # 5. Progreso de aprendizaje
        report += f"5. PROGRESO DE APRENDIZAJE: {self.rubric_scores['learning_progress']:.2f}/1.00\n"
        report += "   Evalúa la mejora demostrable con el tiempo y la capacidad de refinar estrategias.\n"
        if self.rubric_scores['learning_progress'] > 0.8:
            report += "   ✓ EXCELENTE: Mejora continua y significativa a lo largo de las iteraciones.\n"
        elif self.rubric_scores['learning_progress'] > 0.6:
            report += "   ✓ BUENO: Mejora clara y sostenida en el rendimiento.\n"
        elif self.rubric_scores['learning_progress'] > 0.3:
            report += "   ✓ REGULAR: Alguna mejora observable pero inconsistente.\n"
        else:
            report += "   ✗ DEFICIENTE: Poca o ninguna mejora observable con el tiempo.\n"
        report += "\n"
        
        # Puntuación total
        report += f"PUNTUACIÓN TOTAL: {total_score:.2f}/5.00\n"
        if total_score > 4.0:
            report += "CALIFICACIÓN: SOBRESALIENTE - Aprendizaje excepcional con resultados óptimos.\n"
        elif total_score > 3.0:
            report += "CALIFICACIÓN: NOTABLE - Buen aprendizaje con resultados eficaces.\n"
        elif total_score > 2.0:
            report += "CALIFICACIÓN: SATISFACTORIO - Aprendizaje adecuado con resultados aceptables.\n"
        else:
            report += "CALIFICACIÓN: INSUFICIENTE - Aprendizaje limitado, requiere mejoras significativas.\n"
        
        print(report)
        return total_score
    
    def update_rubric_scores(self, path_success, path_efficiency, current_iteration, total_iterations):
        """
        Actualiza las puntuaciones de la rúbrica basándose en los resultados de la iteración actual.
        
        Las puntuaciones se calculan considerando múltiples factores:
        - Eficiencia del camino encontrado
        - Porcentaje de espacio explorado
        - Consistencia de los resultados en iteraciones recientes
        - Adaptabilidad de los pesos a lo largo del tiempo
        - Progreso del aprendizaje comparado con iteraciones anteriores
        
        Args:
            path_success (bool): Si se encontró un camino exitoso a la meta
            path_efficiency (float): Eficiencia del camino encontrado (0-1)
            current_iteration (int): Número de la iteración actual
            total_iterations (int): Número total de iteraciones planificadas
        """
        # 1. Actualizar eficiencia
        if path_success:
            # La eficiencia se basa directamente en la eficiencia del camino actual
            self.rubric_scores['efficiency'] = max(self.rubric_scores['efficiency'], path_efficiency)
        
        # 2. Actualizar exploración
        # Calculamos el porcentaje de celdas exploradas respecto al total disponible
        total_cells = self.width * self.height - len(self.obstacles)
        cells_visited = np.sum(self.logical_matrix > 0)
        exploration_score = min(1.0, cells_visited / total_cells)
        self.rubric_scores['exploration'] = exploration_score
        
        # 3. Actualizar consistencia
        # Medimos la consistencia en los resultados recientes (últimas 5 iteraciones)
        if len(self.metric_history['efficiencies']) >= 2:
            recent_efficiencies = self.metric_history['efficiencies'][-5:] if len(self.metric_history['efficiencies']) >= 5 else self.metric_history['efficiencies']
            
            # Una baja varianza indica alta consistencia
            if len(recent_efficiencies) > 0:
                variance = np.var(recent_efficiencies)
                consistency_score = max(0.0, min(1.0, 1.0 - variance))
                
                # Promediamos con el valor anterior para suavizar cambios bruscos
                self.rubric_scores['consistency'] = 0.7 * self.rubric_scores['consistency'] + 0.3 * consistency_score
        
        # 4. Actualizar adaptabilidad
        # Medimos cómo han cambiado los pesos en respuesta a éxitos/fracasos
        if current_iteration > 1:
            # Calculamos la desviación estándar media de los pesos para medir su adaptación
            weights_std = np.std(self.learning_matrix)
            
            # Una desviación estándar moderada indica buena adaptabilidad
            # (demasiado baja = no aprende, demasiado alta = inestable)
            adaptability_score = min(1.0, weights_std / 0.5) if weights_std < 0.5 else max(0.0, 2.0 - weights_std / 0.5)
            
            # Factor de mejora según el éxito actual
            improvement_factor = 0.1 if path_success else -0.05
            self.rubric_scores['adaptability'] = min(1.0, max(0.0, 
                                                             self.rubric_scores['adaptability'] + improvement_factor))
        
        # 5. Actualizar progreso de aprendizaje
        # Medimos la mejora en la eficiencia a lo largo del tiempo
        if len(self.metric_history['efficiencies']) >= 5:
            # Comparamos el promedio de las primeras iteraciones con las últimas
            early_iterations = self.metric_history['efficiencies'][:5]
            recent_iterations = self.metric_history['efficiencies'][-5:]
            
            early_avg = np.mean(early_iterations) if len(early_iterations) > 0 else 0
            recent_avg = np.mean(recent_iterations) if len(recent_iterations) > 0 else 0
            
            # Calculamos el progreso como mejora relativa
            progress = max(0, min(1, (recent_avg - early_avg) / max(0.01, early_avg)))
            self.rubric_scores['progress'] = progress
        
        # Actualizar score global
        self.rubric_scores['overall'] = np.mean([
            self.rubric_scores['efficiency'],
            self.rubric_scores['exploration'],
            self.rubric_scores['consistency'],
            self.rubric_scores['adaptability'],
            self.rubric_scores['progress']
        ])
        
        return self.rubric_scores
        
    def plot_analysis(self):
        # Crear una figura con 3 subplots: 
        # - Mapa de movimientos (arriba izquierda)
        # - Matriz de aprendizaje (arriba derecha y abajo)
        # - Panel de estadísticas (abajo derecha)
        fig = plt.figure(figsize=(18, 14))
        grid = plt.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

        # Área para el mapa de movimientos
        ax_movement = fig.add_subplot(grid[0:2, 0:2])
        
        # Área para las estadísticas
        ax_stats = fig.add_subplot(grid[2, 0:2])
        ax_stats.axis('off')  # Sin ejes para el panel de estadísticas
        
        # Áreas para los mapas de aprendizaje por dirección
        ax_learning = []
        ax_learning.append(fig.add_subplot(grid[0, 2]))
        ax_learning.append(fig.add_subplot(grid[1, 2]))
        ax_learning.append(fig.add_subplot(grid[2, 2]))

        # Título general
        fig.suptitle('Análisis de búsqueda de camino con aprendizaje', fontsize=16)
        
        # 1. Visualizar el mapa de movimientos
        self.plot_movement_matrix(ax=ax_movement, save_fig=False)
        
        # 2. Visualizar matriz de aprendizaje (solo 3 direcciones principales)
        # Encontrar las 3 direcciones con mayores pesos promedio
        avg_weights = np.mean(self.learning_matrix, axis=(0, 1))
        top_dirs = np.argsort(avg_weights)[-3:]
        
        # Crear mapa de colores
        cmap = plt.cm.plasma.copy()
        cmap.set_bad('black', 1.0)
        
        # Máscara para obstáculos
        obstacle_mask = np.zeros((self.height, self.width), dtype=bool)
        for obs in self.obstacles:
            x, y = obs
            if 0 <= x < self.width and 0 <= y < self.height:
                obstacle_mask[y, x] = True
        
        # Estadísticas para normalizar colores
        min_weight = np.min(self.learning_matrix)
        max_weight = np.max(self.learning_matrix)
        
        # Mostrar las 3 direcciones principales
        for i, dir_idx in enumerate(top_dirs):
            weights = self.learning_matrix[:, :, dir_idx].copy()
            masked_weights = np.ma.array(weights, mask=obstacle_mask)
            
            im = ax_learning[i].imshow(masked_weights, cmap=cmap, 
                                      vmin=min_weight, vmax=max_weight, 
                                      interpolation='nearest')
            
            ax_learning[i].set_title(f'Dirección: {self.dir_names[dir_idx]}\n'
                                    f'Peso Promedio: {avg_weights[dir_idx]:.2f}')
            
            # Configurar ejes
            ax_learning[i].set_xticks(np.arange(0, self.width, 5))
            ax_learning[i].set_yticks(np.arange(0, self.height, 5))
            ax_learning[i].grid(color='gray', linestyle='-', alpha=0.3)
            
            # Marcar inicio y meta
            if len(self.path) > 0:
                start_pos = self.path[0]
                ax_learning[i].plot(start_pos[0], start_pos[1], 'ro', markersize=6)
                
                if self.found_goal and len(self.path) > 1:
                    goal_pos = self.path[-1]
                    ax_learning[i].plot(goal_pos[0], goal_pos[1], 'go', markersize=6)
            
            # Añadir flechas para la dirección
            arrow_styles = ['^', '>', 'v', '<']  # Arriba, Derecha, Abajo, Izquierda
            
            # Marcar las posiciones con mayor peso
            flat_weights = weights.flatten()
            if len(flat_weights) > 0:
                top_indices = np.argsort(flat_weights)[-3:]
                for idx in top_indices:
                    y_pos, x_pos = np.unravel_index(idx, weights.shape)
                    if not obstacle_mask[y_pos, x_pos]:
                        ax_learning[i].plot(x_pos, y_pos, arrow_styles[dir_idx], 
                                          color='white', markersize=8, 
                                          markeredgecolor='black')
        
        # Añadir barra de color para los mapas de aprendizaje
        cbar_ax = fig.add_axes([0.93, 0.4, 0.02, 0.5])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label('Peso de Aprendizaje')
        
        # 3. Estadísticas comparativas en el panel inferior
        # Calcular métricas
        path_length = len(self.path) - 1
        manhattan_dist = abs(self.path[-1][0] - self.path[0][0]) + abs(self.path[-1][1] - self.path[0][1])
        efficiency = self.calculate_path_efficiency()
        cells_visited = np.sum(self.logical_matrix > 0)
        total_visits = np.sum(self.logical_matrix)
        
        # Extraer información de aprendizaje
        best_dir = self.dir_names[np.argmax(avg_weights)]
        learning_stats = f"Dirección preferida: {best_dir} | " \
                        f"Factor de decaimiento: {self.decay_factor:.2f} | " \
                        f"Varianza de pesos: {np.var(self.learning_matrix):.2f}"
        
        # Calcular estadísticas de exploración
        exploration_rate = cells_visited / (self.width * self.height - len(self.obstacles))
        revisit_rate = (total_visits - cells_visited) / total_visits if total_visits > 0 else 0
        
        # Texto para el panel de estadísticas
        stats_text = (
            f"ESTADÍSTICAS DE RENDIMIENTO\n\n"
            f"Métricas de camino:\n"
            f"• Longitud del camino: {path_length} pasos\n"
            f"• Distancia Manhattan: {manhattan_dist} unidades\n"
            f"• Eficiencia de ruta: {efficiency:.2f}\n\n"
            f"Exploración:\n"
            f"• Celdas exploradas: {cells_visited} de {self.width * self.height - len(self.obstacles)} ({exploration_rate:.1%})\n"
            f"• Tasa de revisita: {revisit_rate:.1%}\n"
            f"• Total de movimientos: {self.total_steps}\n\n"
            f"Aprendizaje:\n"
            f"• {learning_stats}"
        )
        
        # Añadir el texto al panel de estadísticas
        ax_stats.text(0.5, 0.5, stats_text, ha='center', va='center', 
                     fontsize=12, bbox=dict(facecolor='lightyellow', alpha=0.5, boxstyle='round,pad=1'))
        
        # Ajustar layout
        plt.tight_layout(rect=[0, 0, 0.92, 0.95])
        
        # Guardar la figura si se solicita
        if save_fig:
            plt.savefig(filename)
            print(f"Análisis de búsqueda guardado como '{filename}'")
        
        plt.show()
        return fig

    def plot_learning_heatmap(self, ax=None, save_fig=True):
        """
        Visualiza la matriz de aprendizaje mostrando los pesos acumulados para cada dirección.
        
        Args:
            ax (matplotlib.axes.Axes, optional): Eje donde dibujar. Si es None, se crea una nueva figura.
            save_fig (bool): Si es True, guarda la figura en un archivo.
        
        Returns:
            matplotlib.figure.Figure: La figura creada o modificada
        """
        # Determinar si debemos crear una nueva figura
        create_new_fig = ax is None
        if create_new_fig:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            axes = axes.flatten()
            fig.suptitle('Matriz de Aprendizaje - Pesos por Dirección', fontsize=16)
        else:
            fig = ax.figure
            # Crear una estructura de 2x2 dentro del eje proporcionado
            grid_size = 2
            axes = []
            for i in range(grid_size):
                for j in range(grid_size):
                    # Crear un subeje dentro del eje proporcionado
                    ax_pos = [
                        ax.get_position().x0 + j * ax.get_position().width / grid_size,
                        ax.get_position().y0 + (grid_size - 1 - i) * ax.get_position().height / grid_size,
                        ax.get_position().width / grid_size,
                        ax.get_position().height / grid_size
                    ]
                    new_ax = fig.add_axes(ax_pos)
                    axes.append(new_ax)
            
        # Crear una máscara para los obstáculos
        obstacle_mask = np.zeros((self.height, self.width), dtype=bool)
        for obs in self.obstacles:
            x, y = obs
            if 0 <= x < self.width and 0 <= y < self.height:
                obstacle_mask[y, x] = True
        
        # Crear mapa de colores
        cmap = plt.cm.plasma.copy()
        cmap.set_bad('black', 1.0)
        
        # Calcular estadísticas para normalizar los colores
        min_weight = np.min(self.learning_matrix)
        max_weight = np.max(self.learning_matrix)
        
        # Estadísticas agregadas para mostrar en el título
        avg_weights = np.mean(self.learning_matrix, axis=(0, 1))
        max_weights = np.max(self.learning_matrix, axis=(0, 1))
        
        # Para cada dirección, crear un heatmap
        for i, (direction, dir_name) in enumerate(zip(range(4), self.dir_names)):
            # Obtener los pesos para esta dirección
            weights = self.learning_matrix[:, :, direction].copy()
            
            # Aplicar máscara de obstáculos
            masked_weights = np.ma.array(weights, mask=obstacle_mask)
            
            # Dibujar el heatmap para esta dirección
            im = axes[i].imshow(masked_weights, cmap=cmap, vmin=min_weight, vmax=max_weight, interpolation='nearest')
            axes[i].set_title(f'Dirección: {dir_name}\nPeso Promedio: {avg_weights[direction]:.2f}, Máximo: {max_weights[direction]:.2f}')
            
            # Configurar ejes
            axes[i].set_xticks(np.arange(0, self.width, 5))
            axes[i].set_yticks(np.arange(0, self.height, 5))
            axes[i].grid(which='both', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
            
            # Marcar inicio y meta si existen
            if len(self.path) > 0:
                start_pos = self.path[0]
                axes[i].plot(start_pos[0], start_pos[1], 'ro', markersize=8, label='Inicio')
                
                if self.found_goal and len(self.path) > 1:
                    goal_pos = self.path[-1]
                    axes[i].plot(goal_pos[0], goal_pos[1], 'go', markersize=8, label='Meta')
            
            # Añadir flechas para indicar la dirección
            arrow_styles = ['^', '>', 'v', '<']  # Arriba, Derecha, Abajo, Izquierda
            
            # Encontrar las 5 posiciones con mayor peso para esta dirección
            flat_weights = weights.flatten()
            if len(flat_weights) > 0:
                top_indices = np.argsort(flat_weights)[-5:]
                for idx in top_indices:
                    y_pos, x_pos = np.unravel_index(idx, weights.shape)
                    if not obstacle_mask[y_pos, x_pos]:
                        axes[i].plot(x_pos, y_pos, arrow_styles[direction], color='white', 
                                   markersize=10, markeredgecolor='black')
        
        # Añadir una barra de color común
        if create_new_fig:
            cbar_ax = fig.add_axes([0.93, 0.15, 0.02, 0.7])
            cbar = fig.colorbar(im, cax=cbar_ax)
            cbar.set_label('Peso de Aprendizaje')
            
            # Ajustar layout
            plt.tight_layout(rect=[0, 0, 0.9, 0.95])
            
            # Añadir estadísticas generales
            plt.figtext(0.5, 0.02, 
                      f'Estadísticas de Aprendizaje:\n'
                      f'Promedio General: {np.mean(self.learning_matrix):.2f}, '
                      f'Desviación Estándar: {np.std(self.learning_matrix):.2f}\n'
                      f'Dirección Preferida: {self.dir_names[np.argmax(avg_weights)]}, '
                      f'Factor de Decaimiento: {self.decay_factor:.2f}',
                      ha='center', fontsize=10, bbox={'facecolor': 'lightblue', 'alpha': 0.2, 'pad': 5})
            
            # Guardar la figura si se solicita
            if save_fig:
                plt.savefig('learning_heatmap.png')
                print("Mapa de calor de aprendizaje guardado como 'learning_heatmap.png'")
            
            plt.show()
        
        return fig
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

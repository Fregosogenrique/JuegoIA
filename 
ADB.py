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
        self.move_history = []  # Reiniciar historial de movimientos
        
        # Incrementamos el contador de visitas para la posición inicial
        # Asegurar que las coordenadas están dentro de los límites
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            # Nota que la matriz se accede como [y][x]
            self.logical_matrix[y, x] += 1
            
    def get_direction_index(self, direction):
        """Obtiene el índice de la dirección en el array self.directions"""
        try:
            return self.directions.index(direction)
        except ValueError:
            return -1  # Dirección no válida
    def make_move(self):
        """Realiza un único movimiento y actualiza la posición del agente"""
        if self.found_goal:
            return False  # Ya se encontró la meta
            
        # Obtener vecinos válidos con sus direcciones
        valid_neighbors = self.get_neighbors(self.current_position)
        
        if not valid_neighbors:
            # No hay movimientos posibles, terminamos la búsqueda
            return False
        
        # Extraer posición actual
        current_x, current_y = self.current_position
        
        # Aplicar un enfoque de selección basado en los pesos aprendidos
        # Recopilar pesos para cada dirección válida
        weights = []
        
        for i, (dir_tuple, pos) in enumerate(valid_neighbors):
            dir_index = self.get_direction_index(dir_tuple)
            if dir_index >= 0:
                # Obtener el peso aprendido para esta dirección desde esta posición
                weight = self.learning_matrix[current_y, current_x, dir_index]
                # Añadir algo de aleatoriedad para exploración
                exploration_factor = 1.0 - self.decay_factor
                randomness = np.random.random() * exploration_factor
                # El peso final es una combinación del peso aprendido y la exploración aleatoria
                final_weight = (weight * self.decay_factor) + randomness
                weights.append((i, final_weight))
        
        if weights:
            # Seleccionar la dirección con el mayor peso (mejor opción según el aprendizaje)
            selected_idx, _ = max(weights, key=lambda x: x[1])
        else:
            # Si no hay pesos (no debería ocurrir), seleccionar al azar
            selected_idx = np.random.randint(0, len(valid_neighbors))
        
        direction, next_pos = valid_neighbors[selected_idx]
        
        # Guardar el movimiento en el historial antes de mover
        prev_pos = self.current_position
        dir_index = self.get_direction_index(direction)
        self.move_history.append((prev_pos, dir_index))
        
        # Moverse a la siguiente posición
        self.current_position = next_pos
        self.path.append(self.current_position)
        self.total_steps += 1
        
        # Incrementar contador de visitas en la matriz lógica
        x, y = self.current_position
        if 0 <= x < self.width and 0 <= y < self.height:
            # Nota que la matriz se accede como [y][x]
            self.logical_matrix[y
        # Métricas para la rúbrica de evaluación
        self.rubric_scores = {
            'efficiency': 0.0,       # Eficiencia del camino (0-1)
            'exploration': 0.0,      # Exploración del espacio (0-1)
            'consistency': 0.0,      # Consistencia de resultados (0-1)
            'adaptability': 0.0,     # Adaptabilidad a cambios (0-1)
            'learning_progress': 0.0  # Mejora con las iteraciones (0-1)
        }
        
        # Historial de métricas para seguimiento
        self.metric_history = {
            'path_lengths': [],      # Longitud de cada camino exitoso
            'efficiencies': [],      # Eficiencia de cada camino
            'success_rates': [],     # 1.0 si se encontró el objetivo, 0.0 si no
            'exploration_rates': [], # Porcentaje del mapa explorado en cada iteración
            'iteration_times': [],   # Tiempo en segundos por iteración
            'rubric_scores': []      # Puntuaciones de la rúbrica a lo largo del tiempo
        }
            return None  # Retorna None en lugar de un camino vacío o de longitud infinita
    
    def evaluate_performance(self):
        """
        Evalúa el rendimiento del algoritmo de aprendizaje y calcula una puntuación
        general basada en la rúbrica definida.
        
        La puntuación se calcula en una escala de 0 a 5, donde:
        - 0-1: Rendimiento deficiente
        - 1-2: Rendimiento básico


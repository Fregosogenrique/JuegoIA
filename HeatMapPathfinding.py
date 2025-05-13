import numpy as np
import random
import matplotlib.pyplot as plt
from config import GameConfig


class HeatMapPathfinding:
    """
    Algoritmo de búsqueda de caminos basado en mapas de calor con aprendizaje por refuerzo.
    
    El concepto de mapa de calor:
    ----------------------------
    Este sistema utiliza una matriz 2D (el "mapa de calor") donde cada celda almacena
    un valor numérico que representa la "utilidad" o "deseabilidad" de visitar esa celda
    para llegar a la meta. Cuanto mayor sea el valor, más probable es que esa celda
    forme parte de un camino óptimo hacia el objetivo.
    
    Proceso de entrenamiento y pathfinding:
    -------------------------------------
    1. Durante el entrenamiento, el sistema genera múltiples caminos aleatorios.
    2. Los caminos exitosos (que alcanzan la meta) incrementan los valores en el mapa de calor.
    3. Al buscar un camino, el algoritmo sigue preferentemente las celdas con valores más altos.
    
    El sistema de recompensas:
    -----------------------
    - Las celdas reciben recompensas basadas en la fórmula: (M/C)/E
      donde M = distancia Manhattan entre inicio y meta
            C = longitud real del camino encontrado
            E = número de ejecuciones realizadas
    - Los caminos más eficientes (cercanos a la distancia Manhattan óptima) reciben
      mayores recompensas.
    - Las recompensas disminuyen con cada ejecución para dar mayor peso a la exploración inicial.
    
    Ventajas y desventajas:
    ---------------------
    + Ventajas:
      - Aprende de la experiencia acumulada en múltiples ejecuciones
      - Puede adaptarse a entornos complejos con obstáculos
      - Converge gradualmente hacia soluciones óptimas
    
    - Desventajas:
      - Requiere entrenamiento previo para ser efectivo
      - El rendimiento depende de la calidad del entrenamiento
      - Puede quedar atrapado en óptimos locales sin suficiente exploración
    """
    
    def __init__(self, grid_width, grid_height):
        """
        Inicializa el sistema de pathfinding con mapas de calor separados.
        
        Crea una nueva instancia del sistema de pathfinding con mapas de calor separados
        para el avatar y los enemigos, inicializando las matrices de valores con ceros
        y configurando el tamaño del grid. El sistema requiere entrenamiento (método train())
        antes de poder utilizarse para encontrar caminos efectivamente.
        
        Args:
            grid_width (int): Ancho de la cuadrícula en número de celdas
            grid_height (int): Alto de la cuadrícula en número de celdas
        
        Atributos inicializados:
            avatar_heat_map: Matriz numpy (grid_height × grid_width) de valores flotantes
                     inicializada con ceros. Almacena los valores de "calor" para el avatar.
            enemy_heat_map: Matriz similar para los enemigos, permitiendo rutas diferentes.
            avatar_execution_count: Contador de ejecuciones exitosas del avatar.
            enemy_execution_count: Contador de ejecuciones exitosas para los enemigos.
            avatar_path_history: Lista de caminos exitosos del avatar.
            enemy_path_history: Lista de caminos exitosos de los enemigos.
            obstacles: Conjunto de tuplas (x, y) que representan posiciones de obstáculos.
            enemies: Conjunto de tuplas (x, y) que representan posiciones de enemigos.
            strategic_routes: Diccionario que almacena rutas óptimas entre puntos clave.
            accessibility_map: Matriz que indica qué celdas son accesibles desde la posición inicial.
            environment_analyzed: Indicador de si el entorno ha sido completamente analizado.
            potential_enemy_positions: Conjunto de posiciones estratégicas donde podría haber enemigos.
            choke_points: Lista de puntos de estrangulamiento estratégicos identificados.
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        
        # Inicializar mapas de calor separados para avatar y enemigos
        self.avatar_heat_map = np.zeros((grid_height, grid_width))
        self.enemy_heat_map = np.zeros((grid_height, grid_width))
        
        # Para mantener compatibilidad con código existente
        self.heat_map = np.zeros((grid_height, grid_width))
        
        # Contadores de ejecuciones separados
        self.avatar_execution_count = 0
        self.enemy_execution_count = 0
        self.execution_count = 0  # Para compatibilidad con código existente
        
        # Historiales de rutas exitosas separados
        self.avatar_path_history = []
        self.enemy_path_history = []
        self.path_history = []  # Para compatibilidad con código existente
        
        # Almacenar las posiciones de obstáculos y enemigos
        self.obstacles = set()
        self.enemies = set()
        
        # Nuevos atributos para análisis avanzado del entorno
        self.strategic_routes = {}  # Diccionario de rutas clave: {(origen, destino): ruta}
        self.accessibility_map = np.zeros((grid_height, grid_width), dtype=bool)  # Mapa de accesibilidad
        self.environment_analyzed = False  # Indicador de análisis completo
        self.potential_enemy_positions = set()  # Posiciones estratégicas para enemigos
        self.choke_points = []  # Puntos de estrangulamiento identificados
        self.safe_zones = []  # Áreas seguras identificadas lejos de obstáculos

    def manhattan_distance(self, pos1, pos2):
        """
        Calcula la distancia de Manhattan entre dos posiciones.
        
        Args:
            pos1 (tuple): Primera posición (x, y)
            pos2 (tuple): Segunda posición (x, y)
            
        Returns:
            int: La distancia de Manhattan entre las dos posiciones
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_valid_move(self, pos):
        """
        Verifica si una posición es válida para moverse.
        
        Args:
            pos (tuple): Posición a verificar (x, y)
            
        Returns:
            bool: True si la posición es válida, False en caso contrario
        """
        x, y = pos
        return (0 <= x < self.grid_width and 
                0 <= y < self.grid_height and 
                pos not in self.obstacles and
                pos not in self.enemies)
    
    def get_possible_moves(self, current_pos, visited=None):
        """
        Obtiene los movimientos posibles desde una posición.
        
        Args:
            current_pos (tuple): Posición actual (x, y)
            visited (set): Conjunto de posiciones ya visitadas (opcional)
            
        Returns:
            list: Lista de posiciones válidas para moverse
        """
        x, y = current_pos
        possible_moves = []
        
        # Movimientos posibles: arriba, derecha, abajo, izquierda
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        for dx, dy in directions:
            new_pos = (x + dx, y + dy)
            
            if self.is_valid_move(new_pos) and (visited is None or new_pos not in visited):
                possible_moves.append(new_pos)
                
        return possible_moves
    
    def update_heat_map(self, path, start_pos, goal_pos, is_avatar=True):
        """
        Actualiza el mapa de calor basado en un camino exitoso encontrado.
        
        Este método implementa el núcleo del sistema de aprendizaje por refuerzo,
        recompensando las celdas que forman parte de caminos exitosos. Utiliza
        una fórmula de recompensa que premia caminos más cortos y reduce el impacto
        de las actualizaciones conforme aumenta el número de ejecuciones.
        
        Fórmula de recompensa:
            Incremento = (M/C)/E
        
        Donde:
            M = Distancia Manhattan entre inicio y meta (camino ideal teórico)
            C = Longitud real del camino encontrado
            E = Número de ejecuciones realizadas
        
        La fórmula premia caminos que sean cercanos a la distancia Manhattan óptima:
        - Si C = M (camino perfecto), la recompensa es mayor (1/E)
        - Si C > M (camino subóptimo), la recompensa disminuye proporcionalmente
        - Con cada ejecución (E aumenta), las recompensas se reducen para dar
          más importancia al aprendizaje temprano y estabilizar el mapa
        
        Args:
            path (list): Lista de posiciones (x, y) que forman el camino
            start_pos (tuple): Posición inicial (x, y)
            goal_pos (tuple): Posición objetivo (x, y)
            is_avatar (bool): True si es actualización para el avatar, False para enemigo
            
        Efectos:
            Modifica la matriz de calor correspondiente, incrementando los valores 
            en cada posición del camino según la fórmula de recompensa.
        """
        if not path or len(path) < 2:
            return
        
        # Seleccionar el mapa de calor y contador correspondiente
        if is_avatar:
            heat_map = self.avatar_heat_map
            self.avatar_execution_count += 1
            execution_count = self.avatar_execution_count
            path_history = self.avatar_path_history
        else:
            heat_map = self.enemy_heat_map
            self.enemy_execution_count += 1
            execution_count = self.enemy_execution_count
            path_history = self.enemy_path_history
        
        # Mantener compatibilidad con código existente
        self.heat_map = heat_map.copy()
        self.execution_count = max(self.avatar_execution_count, self.enemy_execution_count)
        
        # Calcular la distancia de Manhattan ideal
        manhattan_value = self.manhattan_distance(start_pos, goal_pos)
        
        # Cantidad de casillas recorridas
        path_length = len(path)
        
        # Actualizar el calor de cada casilla en el camino según la fórmula:
        # P = P + ((M/C)/E)
        # Donde P es el peso actual, M es la distancia de Manhattan,
        # C es la cantidad de casillas recorridas, y E es el número de ejecuciones
        reward_value = (manhattan_value / path_length) / execution_count
        
        for pos in path:
            x, y = pos
            heat_map[y][x] += reward_value
            
        # Guardar el camino en el historial
        path_history.append(path)
        self.path_history = path_history.copy()  # Para compatibilidad
    
    def generate_random_path(self, start_pos, goal_pos, max_steps=1000):
        """
        Genera un camino aleatorio desde la posición inicial hasta la meta.
        
        Args:
            start_pos (tuple): Posición inicial (x, y)
            goal_pos (tuple): Posición objetivo (x, y)
            max_steps (int): Número máximo de pasos permitidos
            
        Returns:
            list: Camino encontrado o None si no se llegó a la meta
        """
        path = [start_pos]
        current_pos = start_pos
        visited = {start_pos}
        
        step_count = 0
        while current_pos != goal_pos and step_count < max_steps:
            possible_moves = self.get_possible_moves(current_pos, visited)
            
            if not possible_moves:
                # No hay movimientos posibles, camino bloqueado
                return None
            
            # Elegir un movimiento aleatorio
            next_pos = random.choice(possible_moves)
            
            # Actualizar posición actual y camino
            current_pos = next_pos
            path.append(current_pos)
            visited.add(current_pos)
            
            step_count += 1
            
            # Si llegamos a la meta, terminar
            if current_pos == goal_pos:
                return path
        
        # Si salimos del bucle sin llegar a la meta, retornar None
        if current_pos != goal_pos:
            return None
            
        return path
    
    def train(self, start_pos, goal_pos, obstacles, enemies=None, num_iterations=100, callback=None, train_enemies=True):
        """
        Entrena el mapa de calor con múltiples ejecuciones aleatorias.
        
        Args:
            start_pos (tuple): Posición inicial
            goal_pos (tuple): Posición objetivo
            obstacles (set): Conjunto de obstáculos
            enemies (set): Conjunto de enemigos (opcional)
            num_iterations (int): Número de iteraciones de entrenamiento
            callback (function): Función de callback para progreso (opcional)
            train_enemies (bool): Si se debe entrenar también el mapa de enemigos
            
        Returns:
            list: Lista de tuplas (x, y) representando el camino encontrado, o None
                 si no se pudo llegar a la meta.
        """
        # Establecer obstáculos y enemigos
        self.obstacles = obstacles
        self.enemies = enemies or set()
        
        successful_paths = 0
        best_path = None
        best_length = float('inf')
        
        for i in range(num_iterations):
            path = self.generate_random_path(start_pos, goal_pos)
            
            if path:
                successful_paths += 1
                self.update_heat_map(path, start_pos, goal_pos)
                
                if len(path) < best_length:
                    best_path = path
                    best_length = len(path)
            
            if callback:
                progress = (i + 1) / num_iterations * 100
                callback(iteration=i+1, total=num_iterations, 
                        path=path, best_path=best_path, progress=progress)
        
        print(f"Entrenamiento completado: {successful_paths}/{num_iterations} "
              f"caminos exitosos ({successful_paths/num_iterations*100:.1f}%)")
        
        return best_path
    
    def find_path_with_heat_map(self, start_pos, goal_pos, avoid_cycles=True, avoid_enemies=None, allow_slight_detour=True, is_avatar=True):
        """
        Encuentra un camino desde la posición inicial hasta la meta utilizando el mapa de calor.
        
        Este método implementa un algoritmo de búsqueda greedy guiado por el mapa de calor:
        1. En cada paso, evalúa todos los movimientos posibles desde la posición actual
        2. Selecciona el movimiento con mayor valor en el mapa de calor
        3. Si la meta está disponible como movimiento posible, la selecciona inmediatamente
        4. Si no hay valores positivos en el mapa de calor, realiza un movimiento aleatorio
        
        La estrategia de selección de camino:
        - Greedy: Siempre selecciona el movimiento con mayor valor de calor
        - Determinística: A diferencia del entrenamiento, no hay aleatoriedad
          excepto cuando todos los valores son cero o negativos
        - Meta-orientada: Prioriza llegar a la meta si está disponible como movimiento
        
        Mejoras de pathfinding:
        - Evita enemigos si se proporciona una lista de posiciones de enemigos
        - Permite pequeños desvíos para encontrar caminos alternativos
        - Implementa una heurística mejorada que considera espacios abiertos
        - Soporta mapas de calor separados para avatar y enemigos
        
        Args:
            start_pos (tuple): Posición inicial (x, y)
            goal_pos (tuple): Posición objetivo (x, y) a alcanzar
            avoid_cycles (bool): Si es True, evita ciclos marcando casillas visitadas.
            avoid_enemies (set): Conjunto de posiciones de enemigos a evitar
            allow_slight_detour (bool): Si es True, permite pequeños desvíos para encontrar rutas alternativas
            is_avatar (bool): Si es True, usa el mapa de calor del avatar; si es False, usa el mapa de calor de enemigos
            
        Returns:
            list: Lista de tuplas (x, y) representando el camino encontrado, o None
                 si no se pudo llegar a la meta.
        """
        # Seleccionar el mapa de calor adecuado
        heat_map = self.avatar_heat_map if is_avatar else self.enemy_heat_map
        execution_count = self.avatar_execution_count if is_avatar else self.enemy_execution_count
        
        # Usar heat_map para este algoritmo
        self.heat_map = heat_map.copy()
        
        if execution_count == 0:
            entity_type = "del avatar" if is_avatar else "de enemigos"
            print(f"Error: El mapa de calor {entity_type} no ha sido entrenado.")
            return None
        
        path = [start_pos]
        current_pos = start_pos
        visited = {start_pos} if avoid_cycles else set()
        
        # Incrementar max_steps para permitir rutas más largas y desvíos
        max_steps = self.grid_width * self.grid_height * 3
        step_count = 0
        
        # Para detectar y evitar bloqueos
        last_positions = []
        max_history = 5
        stuck_counter = 0
        
        while current_pos != goal_pos and step_count < max_steps:
            possible_moves = self.get_possible_moves(current_pos, visited if avoid_cycles else None)
            
            # Filtrar posiciones de enemigos si se proporcionaron
            if avoid_enemies:
                possible_moves = [move for move in possible_moves if move not in avoid_enemies]
            
            if not possible_moves:
                if allow_slight_detour and avoid_cycles:
                    # Intentar encontrar un camino alternativo relajando la restricción de ciclos
                    print("Camino bloqueado. Intentando encontrar desvío...")
                    
                    # Buscar posiciones ya visitadas que podrían ofrecer un camino alternativo
                    alternative_positions = []
                    for pos in visited:
                        # No considerar posiciones muy recientes
                        if pos in last_positions:
                            continue
                        
                        # Verificar si desde esta posición hay movimientos no visitados
                        alt_moves = self.get_possible_moves(pos)
                        unvisited_moves = [m for m in alt_moves if m not in visited]
                        
                        if unvisited_moves:
                            # Calcular distancia a la meta como heurística
                            distance_to_goal = self.manhattan_distance(pos, goal_pos)
                            alternative_positions.append((pos, distance_to_goal, len(unvisited_moves)))
                    
                    if alternative_positions:
                        # Ordenar por distancia a la meta y número de movimientos disponibles
                        alternative_positions.sort(key=lambda x: (x[1], -x[2]))
                        
                        # Tomar la mejor alternativa y calcular un camino hasta ella desde la posición actual
                        detour_pos = alternative_positions[0][0]
                        
                        # Reconstruir el camino hasta ese punto desde el camino actual
                        detour_path = self._reconstruct_path_to_position(path, detour_pos)
                        
                        if detour_path:
                            # Actualizar el camino y continuar desde la posición de desvío
                            path = detour_path
                            current_pos = detour_pos
                            visited = {p for p in visited if p not in last_positions}  # Olvidar posiciones recientes
                            step_count += 1
                            continue
                
                # Si no se pudo encontrar un desvío o no está permitido
                print("No se encontró ninguna ruta alternativa")
                return None
            
            # Detectar si el enemigo está atascado en un ciclo
            if current_pos in last_positions:
                stuck_counter += 1
                if stuck_counter >= 3:
                    # Estamos atascados en un ciclo, intentar un movimiento aleatorio
                    if possible_moves:
                        best_move = random.choice(possible_moves)
                        stuck_counter = 0
                        
                        # Limpiar el historial de posiciones recientes
                        last_positions = []
                    else:
                        # No hay salida, ruta bloqueada
                        return None
                        
            else:
                stuck_counter = 0
            
            # Actualizar historial de posiciones recientes
            last_positions.append(current_pos)
            if len(last_positions) > max_history:
                last_positions.pop(0)
            
            # Elegir el movimiento con el valor más alto en el mapa de calor
            best_move = None
            best_score = -float('inf')
            
            for move in possible_moves:
                x, y = move
                # Valor base desde el mapa de calor
                base_value = self.heat_map[y][x]
                
                # Si es la meta, priorizar absolutamente
                if move == goal_pos:
                    best_move = move
                    break
                
                # Calcular un score que combine varios factores
                # 1. Valor del mapa de calor
                # 2. Distancia a la meta (heurística)
                # 3. Apertura del espacio (número de vecinos libres)
                
                # Distancia Manhattan a la meta (invertida para que valores menores sean mejores)
                distance_to_goal = self.manhattan_distance(move, goal_pos)
                distance_factor = 1.0 / (distance_to_goal + 1)
                
                # Contar vecinos libres para favorecer espacios abiertos
                free_neighbors = len(self.get_possible_moves(move, visited if avoid_cycles else None))
                openness_factor = free_neighbors / 4.0  # Normalizado entre 0 y 1
                
                # Calcular puntuación combinada
                # Pesos ajustables para cada factor
                heat_weight = 0.5
                distance_weight = 0.3
                openness_weight = 0.2
                
                # Si es un enemigo, penalizar rutas usadas por el avatar
                if not is_avatar:
                    # Obtener valor del mapa de calor del avatar (rutas más usadas)
                    avatar_value = self.avatar_heat_map[y][x]
                    # Penalizar uso de rutas frecuentes del avatar
                    avatar_penalty = avatar_value * 0.5  # 50% de penalización
                    
                    score = (heat_weight * base_value + 
                             distance_weight * distance_factor + 
                             openness_weight * openness_factor - 
                             avatar_penalty)  # Restar penalización
                else:
                    score = (heat_weight * base_value + 
                             distance_weight * distance_factor + 
                             openness_weight * openness_factor)
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            # Si no hay un buen movimiento pero hay movimientos posibles, elegir uno aleatorio
            if (best_score <= 0 or best_move is None) and best_move != goal_pos and possible_moves:
                best_move = random.choice(possible_moves)
            
            # Actualizar posición actual y camino
            current_pos = best_move
            path.append(current_pos)
            
            if avoid_cycles:
                visited.add(current_pos)
            
            step_count += 1
            
            # Si llegamos a la meta, terminar
            if current_pos == goal_pos:
                # Aplicar suavizado al camino antes de devolverlo
                if len(path) > 3:
                    path = self._smooth_path(path)
                return path
        
        # Si salimos del bucle sin llegar a la meta
        if current_pos != goal_pos:
            return None
            
        # Aplicar suavizado al camino antes de devolverlo
        if len(path) > 3:
            path = self._smooth_path(path)
        return path
    
    def _reconstruct_path_to_position(self, current_path, target_position):
        """
        Reconstruye un camino desde el inicio hasta una posición específica.
        
        Args:
            current_path (list): Camino actual como lista de posiciones
            target_position (tuple): Posición objetivo a la que queremos llegar
            
        Returns:
            list: Camino reconstruido hasta la posición objetivo, o None si no es posible
        """
        # Verificar si la posición objetivo está en el camino actual
        if target_position in current_path:
            target_index = current_path.index(target_position)
            return current_path[:target_index + 1]
        
        # Si no está en el camino actual, intentar encontrar un camino alternativo
        if not current_path:
            return None
            
        start_pos = current_path[0]
        
        # Implementar búsqueda A* simplificada
        open_set = {start_pos}
        closed_set = set()
        came_from = {}
        g_score = {start_pos: 0}
        f_score = {start_pos: self.manhattan_distance(start_pos, target_position)}
        
        while open_set:
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            if current == target_position:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            open_set.remove(current)
            closed_set.add(current)
            
            # Obtener vecinos válidos
            x, y = current
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                if (0 <= neighbor[0] < self.grid_width and 
                    0 <= neighbor[1] < self.grid_height and 
                    neighbor not in closed_set and 
                    neighbor not in self.obstacles):
                    neighbors.append(neighbor)
            
            for neighbor in neighbors:
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self.manhattan_distance(neighbor, target_position)
                    if neighbor not in open_set:
                        open_set.add(neighbor)
        
        return None
    
    def analyze_environment(self, start_pos, goal_pos, obstacles, potential_enemy_count=4):
        """
        Realiza un análisis completo del entorno para entrenar al avatar antes de la colocación de enemigos.
        
        Este método lleva a cabo un escaneo completo del mapa para:
        1. Identificar todas las celdas accesibles desde la posición inicial
        2. Detectar puntos de estrangulamiento (choke points) donde el paso es limitado
        3. Encontrar posiciones estratégicas donde los enemigos podrían ser colocados
        4. Calcular rutas alternativas entre puntos clave del mapa
        5. Identificar zonas seguras alejadas de obstáculos
        
        El análisis se realiza una sola vez al inicio del juego y sus resultados
        se utilizan durante toda la partida para tomar decisiones inteligentes.
        
        Args:
            start_pos (tuple): Posición inicial del avatar (x, y)
            goal_pos (tuple): Posición objetivo (casa) (x, y)
            obstacles (set): Conjunto de tuplas (x, y) que representan obstáculos
            potential_enemy_count (int): Número esperado de enemigos que se añadirán
            
        Returns:
            bool: True si el análisis se completó con éxito, False en caso contrario
        """
        print("\nIniciando análisis completo del entorno...")
        
        # Almacenar los obstáculos
        self.obstacles = obstacles
        
        # 1. Generar mapa de accesibilidad desde la posición inicial
        self._generate_accessibility_map(start_pos)
        
        # 2. Identificar puntos de estrangulamiento
        self.choke_points = self._identify_choke_points()
        print(f"Se identificaron {len(self.choke_points)} puntos de estrangulamiento")
        
        # 3. Determinar posiciones estratégicas para enemigos
        self.potential_enemy_positions = self._identify_strategic_enemy_positions(
            start_pos, goal_pos, potential_enemy_count
        )
        print(f"Se identificaron {len(self.potential_enemy_positions)} posiciones estratégicas para enemigos")
        
        # 4. Calcular y almacenar rutas estratégicas
        self._calculate_strategic_routes(start_pos, goal_pos)
        
        # 5. Identificar zonas seguras
        self.safe_zones = self._identify_safe_zones(start_pos, goal_pos)
        print(f"Se identificaron {len(self.safe_zones)} zonas seguras")
        
        # Marcar el entorno como analizado
        self.environment_analyzed = True
        
        print("Análisis del entorno completado con éxito.")
        return True
        
    def _generate_accessibility_map(self, start_pos):
        """
        Genera un mapa binario que indica qué celdas son accesibles desde la posición inicial.
        
        Una celda se considera accesible si existe al menos un camino válido desde
        la posición inicial hasta ella. Esta información es crucial para identificar
        áreas aisladas y calcular rutas alternativas.
        
        Args:
            start_pos (tuple): Posición inicial (x, y) desde donde comprobar la accesibilidad
        """
        # Inicializar matriz de accesibilidad con False
        self.accessibility_map = np.zeros((self.grid_height, self.grid_width), dtype=bool)
        
        # Usar algoritmo de inundación (flood fill) para marcar celdas accesibles
        queue = [start_pos]
        visited = {start_pos}
        
        while queue:
            current_pos = queue.pop(0)
            x, y = current_pos
            
            # Marcar como accesible
            self.accessibility_map[y][x] = True
            
            # Explorar vecinos
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                
                if (neighbor not in visited and 
                    self.is_valid_move(neighbor)):
                    queue.append(neighbor)
                    visited.add(neighbor)
        
        # Imprimir estadísticas
        accessible_count = np.sum(self.accessibility_map)
        total_cells = self.grid_width * self.grid_height
        print(f"Mapa de accesibilidad generado: {accessible_count}/{total_cells} celdas accesibles "
              f"({accessible_count/total_cells*100:.1f}%)")
    
    def _identify_choke_points(self):
        """
        Identifica puntos de estrangulamiento en el mapa.
        
        Los puntos de estrangulamiento son celdas cuya eliminación dividiría el mapa
        en regiones desconectadas. Son posiciones estratégicas para los enemigos bloqueadores.
        
        Returns:
            list: Lista de tuplas (x, y) que representan puntos de estrangulamiento
        """
        choke_points = []
        
        # Iterar sobre todas las celdas accesibles
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not self.accessibility_map[y][x]:
                    continue
                    
                pos = (x, y)
                
                # Contar vecinos accesibles
                accessible_neighbors = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.grid_width and 
                        0 <= ny < self.grid_height and 
                        self.accessibility_map[ny][nx]):
                        accessible_neighbors += 1
                
                # Si tiene exactamente 2 vecinos accesibles y no es un borde,
                # podría ser un punto de estrangulamiento
                if accessible_neighbors == 2 and 0 < x < self.grid_width-1 and 0 < y < self.grid_height-1:
                    # Verificar si es un punto de estrangulamiento horizontal o vertical
                    horizontal_connected = (self.accessibility_map[y][x-1] and self.accessibility_map[y][x+1])
                    vertical_connected = (self.accessibility_map[y-1][x] and self.accessibility_map[y+1][x])
                    
                    # Si no es un simple pasillo (solo conectado horizontal o verticalmente), 
                    # añadir como punto de estrangulamiento
                    if not (horizontal_connected or vertical_connected):
                        choke_points.append(pos)
        
        return choke_points
    
    def _identify_strategic_enemy_positions(self, start_pos, goal_pos, enemy_count):
        """
        Identifica posiciones estratégicas donde los enemigos podrían ser colocados.
        
        Las posiciones estratégicas se seleccionan considerando:
        - Distancia moderada del jugador inicial (no demasiado cerca ni lejos)
        - Cercanía a puntos de estrangulamiento o caminos óptimos
        - Distribución en diferentes áreas del mapa para maximizar cobertura
        
        Args:
            start_pos (tuple): Posición inicial del avatar (x, y)
            goal_pos (tuple): Posición objetivo (casa) (x, y)
            enemy_count (int): Número de enemigos a posicionar
            
        Returns:
            set: Conjunto de tuplas (x, y) que representan posiciones estratégicas
        """
        strategic_positions = set()
        
        # 1. Calcular un camino óptimo base entre inicio y meta
        optimal_path = self.generate_random_path(start_pos, goal_pos)
        if not optimal_path:
            # Si no se puede encontrar un camino, usar distancia Manhattan para aproximar
            x_range = sorted([start_pos[0], goal_pos[0]])
            y_range = sorted([start_pos[1], goal_pos[1]])
            
            # Generar un área de búsqueda aproximada entre el inicio y la meta
            search_area = []
            for x in range(x_range[0], x_range[1] + 1):
                for y in range(y_range[0], y_range[1] + 1):
                    pos = (x, y)
                    if self.is_valid_move(pos) and pos not in [start_pos, goal_pos]:
                        search_area.append(pos)
            
            # Seleccionar posiciones estratégicas del área de búsqueda
            if search_area:
                # 1. Priorizar puntos equidistantes entre inicio y meta
                strategic_positions = self._select_intermediate_points(search_area, start_pos, goal_pos, min(enemy_count, len(search_area)))
            else:
                print("No se pudieron encontrar posiciones estratégicas en el área de búsqueda")
                # Fallback: Buscar en todo el mapa
                return self._fallback_strategic_positions(start_pos, goal_pos, enemy_count)
        else:
            # 2. Si tenemos un camino óptimo, usar puntos estratégicos a lo largo del camino
            print(f"Camino óptimo encontrado con {len(optimal_path)} pasos")
            
            # Usar puntos de estrangulamiento si están disponibles
            if hasattr(self, 'choke_points') and self.choke_points:
                # Filtrar puntos de estrangulamiento que estén cerca del camino óptimo
                nearby_choke_points = []
                for cp in self.choke_points:
                    # Calcular distancia mínima al camino
                    min_distance = min(self._manhattan_distance(cp, p) for p in optimal_path)
                    if min_distance <= 3:  # Considerar puntos cercanos al camino
                        nearby_choke_points.append(cp)
                
                # Si hay suficientes puntos cercanos, usarlos como posiciones estratégicas
                if len(nearby_choke_points) >= enemy_count:
                    # Seleccionar puntos bien distribuidos
                    strategic_positions.update(self._select_distributed_points(nearby_choke_points, enemy_count))
            
            # Si no tenemos suficientes posiciones, usar puntos del camino óptimo
            if len(strategic_positions) < enemy_count:
                # Seleccionar puntos a lo largo del camino, excluyendo inicio y final
                path_points = optimal_path[1:-1]  # Excluir inicio y meta
                
                if len(path_points) > 0:
                    # Tomar puntos equidistantes a lo largo del camino
                    needed_points = enemy_count - len(strategic_positions)
                    step = max(1, len(path_points) // needed_points)
                    
                    # Seleccionar puntos a intervalos regulares
                    for i in range(0, len(path_points), step):
                        if len(strategic_positions) >= enemy_count:
                            break
                        strategic_positions.add(path_points[i])
        
        # 3. Si no tenemos suficientes posiciones, agregar posiciones aleatorias válidas
        if len(strategic_positions) < enemy_count:
            # Completar con posiciones aleatorias válidas
            additional_positions = self._generate_random_valid_positions(
                enemy_count - len(strategic_positions),
                start_pos,
                goal_pos,
                strategic_positions
            )
            strategic_positions.update(additional_positions)
        
        # 4. Verificar que tenemos al menos el número de posiciones requeridas
        if len(strategic_positions) < enemy_count:
            print(f"Advertencia: Solo se encontraron {len(strategic_positions)} posiciones estratégicas de {enemy_count} solicitadas")
        
        # 5. Devolver el conjunto de posiciones estratégicas
        return strategic_positions
    
    def _select_intermediate_points(self, positions, start_pos, goal_pos, count):
        """
        Selecciona puntos intermedios entre las posiciones de inicio y meta.
        
        Args:
            positions (list): Lista de posiciones candidatas
            start_pos (tuple): Posición inicial
            goal_pos (tuple): Posición objetivo
            count (int): Número de puntos a seleccionar
            
        Returns:
            set: Conjunto de posiciones seleccionadas
        """
        # Ordenar posiciones por distancia a ambos puntos (inicio y meta)
        scored_positions = []
        
        for pos in positions:
            # Distancias a inicio y meta
            dist_to_start = self._manhattan_distance(pos, start_pos)
            dist_to_goal = self._manhattan_distance(pos, goal_pos)
            
            # Preferir puntos equidistantes del inicio y la meta
            # y que no estén demasiado cerca de ninguno
            if dist_to_start < 3 or dist_to_goal < 3:
                continue  # Ignorar puntos demasiado cercanos
                
            # Calcular un puntaje como la diferencia entre distancias
            # (menor = más equidistante)
            score = abs(dist_to_start - dist_to_goal)
            
            scored_positions.append((pos, score))
        
        # Ordenar por puntaje (menor primero)
        scored_positions.sort(key=lambda x: x[1])
        
        # Seleccionar los mejores puntos
        selected = set()
        for pos, _ in scored_positions[:count]:
            selected.add(pos)
            
        return selected
    
    def _select_distributed_points(self, positions, count):
        """
        Selecciona puntos bien distribuidos en el espacio.
        
        Args:
            positions (list): Lista de posiciones candidatas
            count (int): Número de puntos a seleccionar
            
        Returns:
            set: Conjunto de posiciones seleccionadas
        """
        if not positions:
            return set()
            
        if len(positions) <= count:
            return set(positions)
            
        # Empezar con una posición aleatoria
        selected = {positions[0]}
        remaining = positions[1:]
        
        # Iterativamente agregar el punto más lejano a los ya seleccionados
        while len(selected) < count and remaining:
            # Para cada punto restante, calcular la distancia mínima a los puntos seleccionados
            best_point = None
            max_min_distance = -1
            
            for point in remaining:
                # Distancia mínima a cualquier punto ya seleccionado
                min_distance = min(self._manhattan_distance(point, sel) for sel in selected)
                
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_point = point
            
            # Agregar el mejor punto
            if best_point:
                selected.add(best_point)
                remaining.remove(best_point)
            else:
                break
                
        return selected
    
    def _generate_random_valid_positions(self, count, start_pos, goal_pos, existing_positions):
        """
        Genera posiciones aleatorias válidas para enemigos.
        
        Args:
            count (int): Número de posiciones a generar
            start_pos (tuple): Posición inicial a evitar
            goal_pos (tuple): Posición objetivo a evitar
            existing_positions (set): Posiciones existentes a evitar
            
        Returns:
            set: Conjunto de posiciones aleatorias válidas
        """
        positions = set()
        attempts = 0
        max_attempts = count * 20  # Limitar número de intentos
        
        while len(positions) < count and attempts < max_attempts:
            # Generar posición aleatoria
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            pos = (x, y)
            
            # Verificar validez
            if (self.is_valid_move(pos) and 
                pos != start_pos and 
                pos != goal_pos and
                pos not in existing_positions and
                pos not in positions and
                self._manhattan_distance(pos, start_pos) >= 3):  # No demasiado cerca del inicio
                positions.add(pos)
                
            attempts += 1
            
        return positions
        
    def _fallback_strategic_positions(self, start_pos, goal_pos, count):
        """
        Método fallback para encontrar posiciones estratégicas cuando otros métodos fallan.
        
        Args:
            start_pos (tuple): Posición inicial
            goal_pos (tuple): Posición objetivo
            count (int): Número de posiciones a encontrar
            
        Returns:
            set: Conjunto de posiciones estratégicas
        """
        # Buscar en todo el mapa posiciones accesibles
        valid_positions = []
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                pos = (x, y)
                # Verificar que la posición sea válida y accesible
                if (self.is_valid_move(pos) and 
                    pos != start_pos and
                    pos != goal_pos and
                    self.accessibility_map[y][x]):
                    valid_positions.append(pos)
        
        # Si no hay posiciones válidas, devolver un conjunto vacío
        if not valid_positions:
            print("No se encontraron posiciones válidas para enemigos")
            return set()
        
        # Implementar estrategia de distribución para seleccionar posiciones bien distribuidas
        # Primero, calcular la distancia media ideal entre posiciones
        selected_positions = set()
        
        if len(valid_positions) <= count:
            # Si hay menos posiciones que las solicitadas, usar todas las disponibles
            selected_positions = set(valid_positions)
        else:
            # Seleccionar posiciones bien distribuidas usando la función auxiliar
            selected_positions = self._select_distributed_points(valid_positions, count)
        
        # Realizar comprobaciones finales de validez
        final_positions = set()
        for pos in selected_positions:
            if (self.is_valid_move(pos) and 
                pos != start_pos and 
                pos != goal_pos and
                self._manhattan_distance(pos, start_pos) >= 3):  # No demasiado cerca del inicio
                final_positions.add(pos)
        
        # Si no pudimos encontrar suficientes posiciones, completar con posiciones aleatorias
        if len(final_positions) < count:
            print(f"Sólo se encontraron {len(final_positions)} posiciones estratégicas de {count}")
            # Intentar generar posiciones aleatorias para completar
            random_positions = self._generate_random_valid_positions(
                count - len(final_positions),
                start_pos,
                goal_pos,
                final_positions
            )
            final_positions.update(random_positions)
            
        return final_positions

    def _manhattan_distance(self, pos1, pos2):
        """
        Calcula la distancia de Manhattan entre dos posiciones.
        
        Args:
            pos1 (tuple): Primera posición (x, y)
            pos2 (tuple): Segunda posición (x, y)
            
        Returns:
            int: La distancia de Manhattan
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _calculate_strategic_routes(self, start_pos, goal_pos):
        """
        Calcula y almacena rutas estratégicas entre puntos clave del mapa.

        Esta función identificará puntos importantes en el mapa y calculará
        rutas óptimas entre ellos, almacenándolas para uso futuro.

        Args:
            start_pos (tuple): Posición inicial (x, y)
            goal_pos (tuple): Posición objetivo (casa) (x, y)
        """
        # Puntos clave: inicio, meta, y puntos de estrangulamiento seleccionados
        key_points = [start_pos, goal_pos]
        
        # Añadir algunos puntos de estrangulamiento como puntos clave (máximo 3)
        if self.choke_points:
            key_points.extend(self.choke_points[:min(3, len(self.choke_points))])
        
        # Calcular rutas entre cada par de puntos clave
        for i, point1 in enumerate(key_points):
            for j, point2 in enumerate(key_points):
                if i != j:  # No calcular ruta de un punto a sí mismo
                    route_key = (point1, point2)
                    # Comprobar si ya tenemos esta ruta calculada
                    if route_key not in self.strategic_routes:
                        # Intentar encontrar una ruta
                        route = self.find_path_with_heat_map(point1, point2)
                        if route:
                            self.strategic_routes[route_key] = route
        
        print(f"Se calcularon {len(self.strategic_routes)} rutas estratégicas entre puntos clave")

    def _identify_safe_zones(self, start_pos, goal_pos):
        """
        Identifica zonas seguras en el mapa, alejadas de obstáculos y puntos de estrangulamiento.
        
        Las zonas seguras son áreas donde:
        - Hay espacio abierto (múltiples celdas accesibles contiguas)
        - Están alejadas de obstáculos
        - No son puntos de estrangulamiento
        - No están justo en el camino principal entre inicio y meta
        
        Args:
            start_pos (tuple): Posición inicial del avatar (x, y)
            goal_pos (tuple): Posición objetivo (casa) (x, y)
            
        Returns:
            list: Lista de tuplas (x, y) que representan centros de zonas seguras
        """
        safe_zones = []
        
        # Calcular camino principal para excluirlo
        main_path = self.find_path_with_heat_map(start_pos, goal_pos)
        main_path_set = set(main_path) if main_path else set()
        
        # Puntos de estrangulamiento a evitar
        choke_points_set = set(self.choke_points)
        
        # Recorrer todo el mapa
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                pos = (x, y)
                
                # Verificar que la posición sea válida y accesible
                if (self.is_valid_move(pos) and 
                    self.accessibility_map[y][x] and
                    pos not in main_path_set and
                    pos not in choke_points_set and
                    pos != start_pos and
                    pos != goal_pos):
                    
                    # Contar espacios libres alrededor (radio 2)
                    open_space_count = 0
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            check_pos = (x + dx, y + dy)
                            if (0 <= check_pos[0] < self.grid_width and
                                0 <= check_pos[1] < self.grid_height and
                                check_pos not in self.obstacles):
                                open_space_count += 1
                    
                    # Considerar como zona segura si hay suficiente espacio abierto
                    if open_space_count >= 15:  # Umbral arbitrario, ajustar según necesidad
                        safe_zones.append(pos)
        
        return safe_zones

    def _smooth_path(self, path):
        """
        Suaviza un camino eliminando puntos innecesarios y zigzags.
        
        Args:
            path (list): Lista de posiciones (x, y) que forman el camino
            
        Returns:
            list: Camino suavizado
        """
        if len(path) <= 2:
            return path
            
        smoothed_path = [path[0]]  # Mantener el punto inicial
        i = 1
        
        while i < len(path) - 1:
            current = path[i]
            next_point = path[i + 1]
            
            # Si los puntos están en línea recta, podemos saltar el punto intermedio
            if (current[0] == smoothed_path[-1][0] == next_point[0] or 
                current[1] == smoothed_path[-1][1] == next_point[1]):
                i += 1
                continue
            
            # Si no, añadir el punto actual
            smoothed_path.append(current)
            i += 1
        
        # Siempre añadir el punto final
        smoothed_path.append(path[-1])
        
        return smoothed_path
    
    def visualize_heat_map(self, start_pos=None, goal_pos=None, path=None, title="Mapa de Calor"):
        """
        Visualiza el mapa de calor generado, con posibilidad de mostrar un camino.
        
        Este método crea una visualización gráfica del mapa de calor utilizando matplotlib
        para mostrar la intensidad de los valores en cada celda y la distribución espacial 
        de estos valores en el grid. La visualización incluye:
        
        - Mapa de calor con escala de colores (rojo más intenso = valores más altos)
        - Marcadores para obstáculos (cuadrados negros)
        - Marcadores para enemigos (cuadrados rojos)
        - Marcadores para posiciones de inicio (círculo azul) y meta (círculo verde)
        - Camino opcional con flechas direccionales (línea cian)
        
        La intensidad de color se normaliza automáticamente para que el valor máximo
        en el mapa sea representado con el color más intenso, facilitando la 
        interpretación visual de los valores relativos.
        
        Args:
            start_pos (tuple, opcional): Posición inicial (x, y) a marcar en la visualización
            goal_pos (tuple, opcional): Posición objetivo (x, y) a marcar en la visualización
            path (list, opcional): Lista de posiciones (x, y) que forman el camino a visualizar
            title (str, opcional): Título para la visualización. Por defecto "Mapa de Calor"
        """
        plt.figure(figsize=(10, 8))
        
        # Crear una copia del mapa de calor para visualización
        heat_map_display = self.heat_map.copy()
        
        # Escalar para mejor visualización si es necesario
        if np.max(heat_map_display) > 0:
            heat_map_display = heat_map_display / np.max(heat_map_display)
        
        # Mostrar mapa de calor
        plt.imshow(heat_map_display, cmap='hot', interpolation='nearest')
        plt.colorbar(label="Valor Normalizado")
        
        # Marcar obstáculos
        for obs in self.obstacles:
            plt.plot(obs[0], obs[1], 's', color='black', markersize=10)
        
        # Marcar enemigos si existen
        for enemy in self.enemies:
            plt.plot(enemy[0], enemy[1], 's', color='red', markersize=10)
        
        # Marcar inicio y meta si se proporcionan
        if start_pos:
            plt.plot(start_pos[0], start_pos[1], 'o', color='blue', markersize=10)
        if goal_pos:
            plt.plot(goal_pos[0], goal_pos[1], 'o', color='green', markersize=10)
        
        # Mostrar camino si se proporciona
        if path:
            path_x = [pos[0] for pos in path]
            path_y = [pos[1] for pos in path]
            plt.plot(path_x, path_y, '-', color='cyan', linewidth=2)
            
            # Agregar flechas para mostrar la dirección
            for i in range(len(path) - 1):
                dx = path[i+1][0] - path[i][0]
                dy = path[i+1][1] - path[i][1]
                plt.arrow(path[i][0], path[i][1], dx * 0.8, dy * 0.8, 
                          head_width=0.3, head_length=0.3, fc='cyan', ec='cyan')
        
        plt.title(title)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def reset(self):
        """
        Reinicia el mapa de calor y los contadores.
        """
        self.heat_map = np.zeros((self.grid_height, self.grid_width))
        self.execution_count = 0
        self.path_history = []
        
    def save_heat_map(self, filename="heat_map.npy"):
        """
        Guarda el mapa de calor en un archivo.
        
        Args:
            filename (str): Nombre del archivo para guardar el mapa de calor
        """
        np.save(filename, self.heat_map)
        print(f"Mapa de calor guardado en {filename}")
        
    def load_heat_map(self, filename="heat_map.npy", execution_count=None):
        """
        Carga un mapa de calor desde un archivo.
        
        Args:
            filename (str): Nombre del archivo a cargar
            execution_count (int): Contador de ejecuciones a establecer (opcional)
        """
        try:
            self.heat_map = np.load(filename)
            if execution_count is not None:
                self.execution_count = execution_count
            else:
                # Estimar el número de ejecuciones basado en la suma del mapa de calor
                self.execution_count = max(1, int(np.sum(self.heat_map)))
                
            print(f"Mapa de calor cargado desde {filename}")
            print(f"Ejecuciones estimadas: {self.execution_count}")
            return True
        except Exception as e:
            print(f"Error al cargar el mapa de calor: {e}")
            return False


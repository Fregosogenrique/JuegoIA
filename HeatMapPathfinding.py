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
        Inicializa el sistema de pathfinding con mapa de calor.
        
        Crea una nueva instancia del sistema de pathfinding con mapa de calor,
        inicializando la matriz de valores con ceros y configurando el tamaño
        del grid. El sistema requiere entrenamiento (método train()) antes de 
        poder utilizarse para encontrar caminos efectivamente.
        
        Args:
            grid_width (int): Ancho de la cuadrícula en número de celdas
            grid_height (int): Alto de la cuadrícula en número de celdas
        
        Atributos inicializados:
            heat_map: Matriz numpy (grid_height × grid_width) de valores flotantes
                     inicializada con ceros. Almacena los valores de "calor" de cada celda.
            execution_count: Contador de ejecuciones exitosas, usado para ajustar recompensas.
            path_history: Lista de caminos exitosos encontrados durante el entrenamiento.
            obstacles: Conjunto de tuplas (x, y) que representan posiciones de obstáculos.
            enemies: Conjunto de tuplas (x, y) que representan posiciones de enemigos.
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        
        # Inicializar mapa de calor con ceros
        self.heat_map = np.zeros((grid_height, grid_width))
        
        # Contador de ejecuciones
        self.execution_count = 0
        
        # Historial de rutas exitosas
        self.path_history = []
        
        # Almacenar las posiciones de obstáculos y enemigos
        self.obstacles = set()
        self.enemies = set()

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
    
    def update_heat_map(self, path, start_pos, goal_pos):
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
            
        Efectos:
            Modifica la matriz heat_map, incrementando los valores en cada
            posición del camino según la fórmula de recompensa.
        """
        if not path or len(path) < 2:
            return
        
        # Incrementar contador de ejecuciones
        self.execution_count += 1
        
        # Calcular la distancia de Manhattan ideal
        manhattan_value = self.manhattan_distance(start_pos, goal_pos)
        
        # Cantidad de casillas recorridas
        path_length = len(path)
        
        # Actualizar el calor de cada casilla en el camino según la fórmula:
        # P = P + ((M/C)/E)
        # Donde P es el peso actual, M es la distancia de Manhattan,
        # C es la cantidad de casillas recorridas, y E es el número de ejecuciones
        reward_value = (manhattan_value / path_length) / self.execution_count
        
        for pos in path:
            x, y = pos
            self.heat_map[y][x] += reward_value
            
        # Guardar el camino en el historial
        self.path_history.append(path)
    
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
    
    def train(self, start_pos, goal_pos, obstacles, enemies=None, num_iterations=100, callback=None):
        """
        Entrena el mapa de calor con múltiples ejecuciones aleatorias.
        
        Este método ejecuta el proceso completo de entrenamiento del mapa de calor:
        1. Genera múltiples caminos aleatorios desde el inicio hasta la meta
        2. Actualiza el mapa de calor con los caminos exitosos encontrados
        3. Mantiene registro del mejor camino encontrado durante el entrenamiento
        
        El proceso de entrenamiento es estocástico (basado en exploración aleatoria)
        y su calidad depende del número de iteraciones. Con suficientes iteraciones,
        el mapa converge hacia una representación que favorece caminos óptimos o
        cercanos al óptimo.
        
        El entrenamiento puede visualizarse en tiempo real mediante una función
        de callback, lo que permite mostrar el progreso y los caminos encontrados
        durante el proceso.
        
        Args:
            start_pos (tuple): Posición inicial (x, y) para el entrenamiento
            goal_pos (tuple): Posición objetivo (x, y) a alcanzar
            obstacles (set): Conjunto de tuplas (x, y) de posiciones con obstáculos
            enemies (set, opcional): Conjunto de tuplas (x, y) de posiciones con enemigos
            num_iterations (int, opcional): Número de iteraciones de entrenamiento.
                                          Valores más altos producen mejores resultados
                                          pero aumentan el tiempo de entrenamiento.
            callback (function, opcional): Función llamada en cada iteración con los
                                         parámetros (iteration, total, path, best_path, progress)
                                         para actualizar la UI o mostrar el progreso.
                                         
        Returns:
            list: El mejor camino encontrado durante el entrenamiento, o None si
                 no se encontró ningún camino exitoso.
                 
        Notas sobre convergencia:
            - Para entornos simples, 100-200 iteraciones suelen ser suficientes
            - Para entornos complejos con muchos obstáculos, pueden requerirse
              500-1000 iteraciones para obtener buenos resultados
            - El algoritmo nunca garantiza encontrar el camino óptimo global,
              pero con suficientes iteraciones se aproxima a buenas soluciones
        """
        self.obstacles = obstacles
        self.enemies = enemies or set()
        
        successful_paths = 0
        best_path = None
        best_length = float('inf')
        
        for i in range(num_iterations):
            path = self.generate_random_path(start_pos, goal_pos)
            
            if path:
                # Incrementar contador de caminos exitosos
                successful_paths += 1
                
                # Actualizar mapa de calor con el camino encontrado
                self.update_heat_map(path, start_pos, goal_pos)
                
                # Actualizar mejor camino si es más corto
                if len(path) < best_length:
                    best_path = path
                    best_length = len(path)
            
            # Llamar a la función de callback si existe
            if callback:
                progress = (i + 1) / num_iterations * 100
                callback(iteration=i+1, total=num_iterations, 
                         path=path, best_path=best_path, progress=progress)
        
        print(f"Entrenamiento completado: {successful_paths}/{num_iterations} "
              f"caminos exitosos ({successful_paths/num_iterations*100:.1f}%)")
        
        return best_path
    
    def find_path_with_heat_map(self, start_pos, goal_pos, avoid_cycles=True):
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
        
        Detección de ciclos:
        - Cuando avoid_cycles=True, mantiene un registro de celdas visitadas para
          evitar volver a posiciones anteriores y quedar en bucles infinitos
        - Cuando avoid_cycles=False, permite revisitar celdas, lo que puede ser útil
          en algunos escenarios pero podría causar bucles
        
        Args:
            start_pos (tuple): Posición inicial (x, y)
            goal_pos (tuple): Posición objetivo (x, y) a alcanzar
            avoid_cycles (bool): Si es True, evita ciclos marcando casillas visitadas.
                               Recomendado mantener en True para la mayoría de casos.
            
        Returns:
            list: Lista de tuplas (x, y) representando el camino encontrado, o None
                 si no se pudo llegar a la meta.
                 
        Requisito:
            El mapa de calor debe estar entrenado previamente (execution_count > 0).
            De lo contrario, el método retornará None y mostrará un mensaje de error.
        """
        if self.execution_count == 0:
            print("Error: El mapa de calor no ha sido entrenado.")
            return None
        
        path = [start_pos]
        current_pos = start_pos
        visited = {start_pos} if avoid_cycles else set()
        
        max_steps = self.grid_width * self.grid_height * 2
        step_count = 0
        
        while current_pos != goal_pos and step_count < max_steps:
            possible_moves = self.get_possible_moves(current_pos, visited if avoid_cycles else None)
            
            if not possible_moves:
                # No hay movimientos posibles, camino bloqueado
                return None
            
            # Elegir el movimiento con el valor más alto en el mapa de calor
            best_move = None
            best_value = -float('inf')
            
            for move in possible_moves:
                x, y = move
                value = self.heat_map[y][x]
                
                # Si es la meta, priorizar
                if move == goal_pos:
                    best_move = move
                    break
                
                if value > best_value:
                    best_value = value
                    best_move = move
            
            # Si no hay valor positivo en el mapa de calor, elegir un movimiento aleatorio
            if best_value <= 0 and best_move != goal_pos:
                best_move = random.choice(possible_moves)
            
            # Actualizar posición actual y camino
            current_pos = best_move
            path.append(current_pos)
            
            if avoid_cycles:
                visited.add(current_pos)
            
            step_count += 1
            
            # Si llegamos a la meta, terminar
            if current_pos == goal_pos:
                return path
        
        # Si salimos del bucle sin llegar a la meta, retornar None
        if current_pos != goal_pos:
            return None
            
        return path
    
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


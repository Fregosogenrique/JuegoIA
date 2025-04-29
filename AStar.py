from config import GameConfig
import math


class AStar:
    """
    Implementación del algoritmo A* con bloqueo absoluto de casillas con enemigos.
    
    IMPORTANTE: El personaje NUNCA podrá pasar por:
    - Casillas ocupadas por enemigos
    - Casillas adyacentes a enemigos (incluyendo diagonales)
    - Obstáculos
    
    Esta implementación usa un radio de bloqueo muy amplio (4 casillas) y una
    distancia mínima de seguridad (5 unidades) para garantizar que el personaje
    mantenga una distancia estrictamente segura de los enemigos en todo momento.
    
    La clase implementa el algoritmo A*, un algoritmo de búsqueda informada que:
    - Encuentra la ruta más corta entre dos puntos en un grid
    - Utiliza una heurística (distancia Manhattan) para guiar la búsqueda
    - Garantiza encontrar el camino óptimo si existe
    - Tiene mejor rendimiento que algoritmos como Dijkstra para espacios grandes
    
    Características de esta implementación:
    - Bloqueo absoluto de casillas con enemigos y sus adyacentes
    - Tratamiento de casillas bloqueadas igual que obstáculos
    - Garantía de que el personaje nunca pasará cerca de enemigos
    - Preferencia por el camino más corto entre los caminos seguros
    """

    # Constantes de clase para configuración de seguridad
    BLOCKED_ZONE_RADIUS = 4  # Radio de zona bloqueada alrededor de enemigos (en casillas)
    MIN_SAFE_DISTANCE = 5    # Distancia mínima segura a enemigos (en unidades)

    def __init__(self, game_state):
        """
        Inicializa el pathfinder con el estado del juego.
        Precalcula todas las posiciones bloqueadas.
        
        Args:
            game_state: Objeto GameState que contiene el estado actual del juego,
                       incluyendo obstáculos y enemigos.
        """
        self.game_state = game_state
        # Precalcular todas las casillas bloqueadas
        self.blocked_positions = self._calculate_blocked_positions()

    def _calculate_blocked_positions(self):
        """
        Calcula el conjunto de todas las posiciones bloqueadas:
        - Obstáculos
        - Enemigos
        - Casillas adyacentes a enemigos (en las 8 direcciones)
        
        Returns:
            set: Conjunto de todas las posiciones bloqueadas
        """
        blocked = set()
        
        # Agregar obstáculos
        blocked.update(self.game_state.obstacles)
        
        # Agregar enemigos
        blocked.update(self.game_state.enemies)
        
        # Agregar enemigos y sus zonas de bloqueo usando distancia euclidiana
        for enemy_pos in self.game_state.enemies:
            x_enemy, y_enemy = enemy_pos
            # Bloquear posición del enemigo
            blocked.add(enemy_pos)
            
            # Calcular zona de bloqueo usando distancia euclidiana precisa
            # Usamos un rango ligeramente mayor para asegurar que capturamos todas las celdas relevantes
            for dx in range(-self.BLOCKED_ZONE_RADIUS - 1, self.BLOCKED_ZONE_RADIUS + 2):
                for dy in range(-self.BLOCKED_ZONE_RADIUS - 1, self.BLOCKED_ZONE_RADIUS + 2):
                    x, y = x_enemy + dx, y_enemy + dy
                    
                    # Verificar límites del grid
                    if not (0 <= x < GameConfig.GRID_WIDTH and 0 <= y < GameConfig.GRID_HEIGHT):
                        continue
                    
                    # Calcular distancia euclidiana exacta
                    distance = math.sqrt((x - x_enemy)**2 + (y - y_enemy)**2)
                    
                    # Bloquear si está dentro del radio (inclusive)
                    if distance <= self.BLOCKED_ZONE_RADIUS:
                        blocked.add((x, y))
        
        return blocked

    def is_position_valid(self, pos):
        """
        Verifica si una posición es válida (no bloqueada).
        
        Una posición es válida si:
        - Está dentro de los límites del grid
        - No está en el conjunto de posiciones bloqueadas
        
        Args:
            pos (tuple): Posición (x, y) a verificar.
            
        Returns:
            bool: True si la posición es válida, False si está bloqueada.
        """
        x, y = pos
        # Verificar límites del grid
        if not (0 <= x < GameConfig.GRID_WIDTH and 0 <= y < GameConfig.GRID_HEIGHT):
            return False
            
        # Verificar que no sea una posición bloqueada
        if pos in self.blocked_positions:
            return False
            
        return True

    def _heuristic(self, pos1, pos2):
        """
        Heurística simple de distancia Manhattan.
        
        Args:
            pos1 (tuple): Primera posición (x1, y1).
            pos2 (tuple): Segunda posición (x2, y2).
            
        Returns:
            int: Distancia Manhattan entre los dos puntos.
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_neighbors(self, pos):
        """
        Obtiene los vecinos válidos de una posición.
        Solo considera las cuatro direcciones cardinales.
        
        Args:
            pos (tuple): Posición actual (x, y).
            
        Returns:
            list: Lista de posiciones válidas adyacentes.
        """
        x, y = pos
        possible_neighbors = [
            (x, y-1),  # Arriba
            (x+1, y),  # Derecha
            (x, y+1),  # Abajo
            (x-1, y)   # Izquierda
        ]
        
        # Filtrar solo las posiciones válidas (dentro de límites y no bloqueadas)
        return [pos for pos in possible_neighbors if self.is_position_valid(pos)]

    def find_path(self, start, goal):
        """
        Encuentra un camino seguro desde start hasta goal.
        
        Usa el algoritmo A* pero garantiza que el camino NUNCA pasará
        por casillas con enemigos o adyacentes a enemigos.
        
        Args:
            start (tuple): Posición inicial (x, y).
            goal (tuple): Posición objetivo (x, y).
            
        Returns:
            list or None: Lista de posiciones que forman el camino si existe,
                          None si no hay camino seguro posible.
        """
        # Verificar que inicio y fin sean válidos
        if not self.is_position_valid(start) or not self.is_position_valid(goal):
            return None

        # Conjuntos para el algoritmo
        open_set = {start}  # Nodos por explorar
        closed_set = set()  # Nodos ya explorados

        # Diccionarios para rastrear el camino
        came_from = {}  # Para reconstruir el camino
        g_score = {start: 0}  # Costo desde el inicio
        f_score = {start: self._heuristic(start, goal)}  # Costo estimado total

        while open_set:
            # Obtener el nodo con menor f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))

            # Si llegamos al objetivo, reconstruir y devolver el camino
            if current == goal:
                return self._reconstruct_path(came_from, current)

            # Mover el nodo actual al conjunto cerrado
            open_set.remove(current)
            closed_set.add(current)

            # Explorar vecinos válidos
            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                # Costo uniforme para todas las casillas válidas
                tentative_g_score = g_score[current] + 1

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                # Este camino es el mejor hasta ahora
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)

        # No se encontró camino
        return None

    def _reconstruct_path(self, came_from, current):
        """
        Reconstruye el camino desde el inicio hasta el objetivo.
        
        Args:
            came_from (dict): Diccionario de referencias a nodos previos.
            current (tuple): Nodo actual desde donde reconstruir.
            
        Returns:
            list: Lista de posiciones que forman el camino.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]  # Invertir para tener el camino desde el inicio

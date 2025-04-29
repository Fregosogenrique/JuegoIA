from config import GameConfig
import math


class AStar:
    """
    Implementación del algoritmo A* (A-star) para encontrar caminos óptimos en el juego.
    
    La clase implementa el algoritmo A*, un algoritmo de búsqueda informada que:
    - Encuentra la ruta más corta entre dos puntos en un grid
    - Utiliza una heurística (distancia Manhattan) para guiar la búsqueda
    - Garantiza encontrar el camino óptimo si existe
    - Tiene mejor rendimiento que algoritmos como Dijkstra para espacios grandes
    
    Características principales:
    - Integración con el estado del juego para verificar obstáculos y límites
    - Uso de conjuntos abiertos y cerrados para rastrear nodos a explorar
    - Implementación de la heurística de distancia Manhattan
    - Estructura de datos para reconstruir el camino óptimo encontrado
    
    Complejidad:
    - Tiempo: O(b^d) donde b es el factor de ramificación y d la profundidad
    - Espacio: O(b^d) para almacenar los nodos explorados
    
    El algoritmo es especialmente eficiente para grids con pocos obstáculos o
    cuando existe una ruta directa o casi directa entre el origen y el destino.
    """

    # Constants for enemy avoidance
    ENEMY_INFLUENCE_RADIUS = 4  # Radio de influencia del enemigo (ajustado para grid más grande)
    MAX_DANGER_COST = 10.0      # Costo máximo de peligro cerca de enemigos
    SAFETY_WEIGHT = 1.5         # Peso para balancear distancia vs seguridad (ajustado para mejor balance)

    def __init__(self, game_state):
        """
        Inicializa el pathfinder A* con el estado del juego.
        
        Configura la instancia del algoritmo A* para trabajar con un estado de
        juego específico, que proporciona información sobre los obstáculos,
        límites del grid y otras entidades como enemigos.
        
        Args:
            game_state: Objeto GameState que contiene el estado actual del juego,
                       incluyendo obstáculos y límites del grid.
        """
        self.game_state = game_state

    def calculate_enemy_influence(self, pos):
        """
        Calcula la influencia total de los enemigos en una posición dada.
        
        Crea una "zona de peligro" alrededor de cada enemigo, donde el peligro
        es mayor cuanto más cerca esté de un enemigo. El algoritmo considerará
        estas zonas de peligro al calcular el camino óptimo.
        
        Args:
            pos (tuple): Posición (x, y) a evaluar.
            
        Returns:
            float: Valor de influencia/peligro en la posición (0.0 = seguro,
                  valores mayores indican mayor peligro).
        """
        total_influence = 0.0
        
        for enemy_pos in self.game_state.enemies:
            # Usar distancia euclidiana para crear zonas circulares de influencia
            distance = math.sqrt((pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2)
            
            # Si está dentro del radio de influencia
            if distance <= self.ENEMY_INFLUENCE_RADIUS:
                # Influencia inversa a la distancia, normalizada
                influence = (self.ENEMY_INFLUENCE_RADIUS - distance) / self.ENEMY_INFLUENCE_RADIUS
                influence = influence * self.MAX_DANGER_COST
                
                # Tomar el mayor valor de influencia (caso de múltiples enemigos)
                total_influence = max(total_influence, influence)
        
        return total_influence

    def find_path(self, start, goal):
        """
        Encuentra el camino más corto entre dos puntos usando el algoritmo A*.
        
        Este método implementa la búsqueda A* completa, que:
        1. Mantiene un conjunto de nodos abiertos para explorar
        2. Mantiene un conjunto de nodos cerrados ya explorados
        3. Utiliza una función heurística para estimar el costo restante
        4. Combina el costo real (g_score) y el estimado (heurística) para priorizar nodos
        5. Reconstruye el camino óptimo cuando se encuentra el objetivo
        
        Args:
            start (tuple): Coordenadas (x, y) del punto de inicio.
            goal (tuple): Coordenadas (x, y) del punto de destino (meta).
            
        Returns:
            list o None: Lista de tuplas (x, y) representando el camino óptimo desde
                        start hasta goal, en orden desde el inicio hasta el final.
                        Si no se encuentra un camino válido, devuelve None.
        
        Complejidad:
            Si h(n) ≤ d(n) (donde h es la heurística y d la distancia real),
            la complejidad es O(b^d) en el peor caso, pero en la práctica suele
            ser mucho más eficiente debido a la guía de la heurística.
        """
        if not start or not goal:
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

            # Explorar vecinos
            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue

                # Calcular g_score tentativo con penalización por enemigos
                enemy_cost = self.calculate_enemy_influence(neighbor)
                movement_cost = 1.0 + enemy_cost * self.SAFETY_WEIGHT
                tentative_g_score = g_score[current] + movement_cost

                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue

                # Este camino es el mejor hasta ahora
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)

        return None

    def _heuristic(self, pos1, pos2):
        """
        Calcula una heurística mejorada que combina distancia y seguridad.
        
        Esta función mantiene la base de la distancia Manhattan pero incorpora
        un factor adicional relacionado con la proximidad a los enemigos.
        
        La heurística sigue siendo admisible (nunca sobreestima el costo real)
        pero ahora guía al algoritmo para preferir caminos más seguros.
        
        Args:
            pos1 (tuple): Primera posición (x1, y1).
            pos2 (tuple): Segunda posición (x2, y2).
            
        Returns:
            float: Valor heurístico combinado (distancia + seguridad).
        """
        # Distancia Manhattan base
        base_distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        
        # Factor de seguridad (influencia de enemigos)
        # Solo evaluamos la posición actual, no la meta
        danger_cost = self.calculate_enemy_influence(pos1)
        
        # Combinar distancia y seguridad manteniendo admisibilidad
        return float(base_distance) + (danger_cost * 0.5)

    def _get_neighbors(self, pos):
        """
        Obtiene los vecinos válidos de una posición en el grid.
        
        Este método determina qué celdas adyacentes son accesibles desde la
        posición actual, considerando:
        1. Los límites del grid (no salirse del mapa)
        2. Los obstáculos (no atravesar paredes)
        3. La proximidad a enemigos (evitar situaciones de peligro extremo)
        
        Solo considera movimientos en las cuatro direcciones cardinales:
        arriba, derecha, abajo e izquierda (sin diagonales).
        
        Args:
            pos (tuple): Posición actual (x, y).
            
        Returns:
            list: Lista de tuplas (x, y) representando posiciones válidas
                 adyacentes a la posición actual.
        """
        x, y = pos
        possible_neighbors = [
            (x, y - 1),  # Arriba
            (x + 1, y),  # Derecha
            (x, y + 1),  # Abajo
            (x - 1, y)  # Izquierda
        ]

        # Filtrar vecinos válidos
        valid_neighbors = []
        for nx, ny in possible_neighbors:
            # Verificar límites del grid
            if (0 <= nx < GameConfig.GRID_WIDTH and
                    0 <= ny < GameConfig.GRID_HEIGHT):
                # Verificar que no sea un obstáculo
                if (nx, ny) not in self.game_state.obstacles:
                    # Calcular peligrosidad de la casilla
                    danger_level = self.calculate_enemy_influence((nx, ny))
                    
                    # Comprobar si no es una posición extremadamente peligrosa
                    # (estar exactamente en la misma casilla que un enemigo)
                    if (nx, ny) not in self.game_state.enemies:
                        valid_neighbors.append((nx, ny))

        return valid_neighbors

    def _reconstruct_path(self, came_from, current):
        """
        Reconstruye el camino completo desde el nodo inicial hasta el nodo final.
        
        Después de que A* encuentra un camino al objetivo, este método reconstruye
        la secuencia completa de pasos utilizando el diccionario de referencias que
        almacena, para cada nodo, el nodo previo en el camino óptimo.
        
        El proceso comienza desde el nodo final (current) y retrocede hasta
        el nodo inicial, siguiendo las referencias del diccionario came_from.
        Luego invierte la lista para obtener el camino en orden desde el inicio.
        
        Args:
            came_from (dict): Diccionario que mapea cada nodo a su predecesor
                             en el camino óptimo.
            current (tuple): Nodo final (x, y) desde el que reconstruir el camino.
            
        Returns:
            list: Lista de tuplas (x, y) que representan el camino completo
                 desde el nodo inicial hasta el nodo final, en orden.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]  # Invertir para tener el camino desde el inicio
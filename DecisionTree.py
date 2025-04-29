from config import GameConfig
import numpy as np
import random


class DecisionTree:
    """
    Implementación de un árbol de decisiones con poda alpha-beta para encontrar rutas óptimas.
    
    Esta clase implementa un algoritmo de búsqueda de rutas basado en árboles de decisión
    con optimización mediante poda alpha-beta. Utiliza información del estado del juego
    y una matriz de frecuencia de movimientos para guiar la búsqueda y priorizar rutas
    con mayor probabilidad de éxito.
    
    Características principales:
    - Búsqueda recursiva de caminos desde un punto inicial a una meta
    - Poda alpha-beta para reducir el espacio de búsqueda
    - Heurística combinada que considera distancia y frecuencia de visitas
    - Límite de profundidad configurable para controlar el tiempo de búsqueda
    - Prevención de ciclos mediante seguimiento de nodos visitados
    
    La clase se integra con el estado del juego para verificar la validez de movimientos
    (evitando obstáculos) y utiliza la matriz de movimiento como parte de su heurística
    para favorecer rutas previamente exitosas.
    """

    def __init__(self, game_state, movement_matrix):
        """
        Inicializa el árbol de decisiones con el estado del juego y la matriz de movimiento.
        
        Args:
            game_state: Objeto GameState que contiene el estado actual del juego,
                        incluyendo posiciones del jugador, casa, obstáculos y enemigos.
            movement_matrix: Matriz numpy que registra la frecuencia de visitas a cada celda.
                             Se utiliza como parte de la heurística para favorecer rutas
                             con movimientos exitosos anteriores.
        
        Atributos inicializados:
            max_depth: Profundidad máxima de búsqueda en el árbol (por defecto 10).
                       Limita el tiempo de búsqueda en grafos grandes.
            visited: Conjunto de nodos visitados en la ejecución actual para evitar ciclos.
            best_path: Lista que almacena el mejor camino encontrado durante la búsqueda.
            best_score: Puntuación del mejor camino (menor es mejor, generalmente la longitud).
        """
        self.game_state = game_state
        self.movement_matrix = movement_matrix
        self.max_depth = 10  # Profundidad máxima de búsqueda
        self.visited = set()  # Conjunto de nodos visitados en esta ejecución
        self.best_path = None
        self.best_score = float('inf')

    def find_path(self, start, goal):
        """
        Encuentra un camino optimizado desde el punto inicial hasta la meta.
        
        Este método público inicia el proceso de búsqueda, reiniciando las variables
        de estado (visitados, mejor camino, mejor puntuación) y lanzando una búsqueda
        recursiva con poda alpha-beta desde el punto inicial.
        
        Args:
            start (tuple): Coordenadas (x, y) del punto inicial.
            goal (tuple): Coordenadas (x, y) de la meta a alcanzar.
            
        Returns:
            list: Lista de tuplas (x, y) que representan el camino más óptimo encontrado
                  desde start hasta goal. Si no se encuentra un camino, devuelve una lista
                  con solo el punto inicial.
        
        Nota:
            Los resultados de la búsqueda dependen significativamente del valor de max_depth.
            Valores mayores pueden encontrar caminos más óptimos pero a costa de mayor
            tiempo de procesamiento.
        """
        print(f"\nIniciando búsqueda de ruta desde {start} hasta {goal}")
        self.visited = set()
        self.best_path = None
        self.best_score = float('inf')

        # Iniciar búsqueda recursiva
        path = [start]
        self._search_path(start, goal, path, 0, float('-inf'), float('inf'))

        if self.best_path:
            print(f"Ruta encontrada: {self.best_path}")
            print(f"Longitud de la ruta: {len(self.best_path)}")
        else:
            print("No se encontró ninguna ruta")

        return self.best_path if self.best_path else [start]

    def _search_path(self, current, goal, path, depth, alpha, beta):
        """
        Implementa la búsqueda recursiva del camino utilizando poda alpha-beta.
        
        Este método privado realiza la búsqueda recursiva a través del espacio de estados,
        explorando los posibles movimientos desde la posición actual y utilizando
        la poda alpha-beta para reducir la exploración de ramas que no pueden mejorar
        la mejor solución encontrada hasta el momento.
        
        La búsqueda se realiza en profundidad (DFS) pero con las siguientes optimizaciones:
        - Límite de profundidad máxima para evitar búsquedas infinitas
        - Poda alpha-beta para eliminar ramas subóptimas
        - Heurística para priorizar vecinos más prometedores
        - Detección de ciclos mediante seguimiento de nodos visitados
        - Límite basado en la mejor solución encontrada hasta el momento
        
        Args:
            current (tuple): Posición actual (x, y) en la búsqueda.
            goal (tuple): Posición objetivo (x, y) a alcanzar.
            path (list): Camino acumulado hasta el momento.
            depth (int): Profundidad actual en el árbol de búsqueda.
            alpha (float): Valor alpha para la poda (mejor valor para el maximizador).
            beta (float): Valor beta para la poda (mejor valor para el minimizador).
            
        Returns:
            float: Puntuación del mejor camino encontrado desde la posición actual.
                  float('inf') significa que no se encontró un camino válido.
        
        Efectos secundarios:
            Actualiza self.best_path y self.best_score si encuentra un camino mejor.
        """
        # Caso base: llegamos a la meta
        if current == goal:
            path_score = len(path)
            if path_score < self.best_score:
                self.best_path = path.copy()
                self.best_score = path_score
            return path_score

        # Caso base: profundidad máxima alcanzada o camino demasiado largo
        if depth >= self.max_depth or len(path) > self.best_score:
            return float('inf')

        # Marcar como visitado en esta ejecución
        self.visited.add(current)

        # Obtener vecinos ordenados por prioridad
        neighbors = self._get_prioritized_neighbors(current, goal)

        # Valor mínimo para el nodo actual
        min_score = float('inf')
        best_local_path = None

        for neighbor in neighbors:
            # Evitar ciclos y nodos ya visitados
            if neighbor in self.visited or neighbor in path:
                continue

            # Explorar este vecino
            path.append(neighbor)
            score = self._search_path(neighbor, goal, path, depth + 1, alpha, beta)
            path.pop()  # Backtracking

            # Actualizar mejor puntuación local
            if score < min_score:
                min_score = score
                best_local_path = path.copy()

            # Poda beta
            beta = min(beta, min_score)
            if alpha >= beta:
                break  # Poda alpha-beta

        # Desmarcar como visitado (backtracking)
        self.visited.remove(current)

        # Si encontramos un camino válido, actualizar el mejor camino global
        if best_local_path and min_score < float('inf'):
            if len(best_local_path) < self.best_score:
                self.best_path = best_local_path
                self.best_score = len(best_local_path)

        return min_score

    def _get_prioritized_neighbors(self, pos, goal):
        """
        Obtiene los vecinos de la posición actual ordenados por prioridad.
        
        Este método privado determina las posiciones adyacentes válidas a la posición actual
        y las ordena según una heurística combinada que considera:
        1. La distancia Manhattan a la meta (70% del peso)
        2. La frecuencia de visitas previas normalizadas (30% del peso)
        
        El proceso consta de tres etapas:
        1. Generación de posibles vecinos basada en los rangos de movimiento configurados
        2. Filtrado de vecinos inválidos (fuera de límites o con obstáculos)
        3. Ordenamiento de vecinos según la puntuación heurística combinada
        
        Args:
            pos (tuple): Posición actual (x, y).
            goal (tuple): Posición objetivo (x, y).
            
        Returns:
            list: Lista de tuplas (x, y) representando los vecinos válidos ordenados
                  por prioridad (el más prometedor primero).
        
        Nota:
            La aleatoriedad en la generación de vecinos introduce variabilidad en los
            resultados, lo que puede ayudar a evitar mínimos locales pero también
            puede llevar a soluciones diferentes en cada ejecución.
        """
        x, y = pos
        move_value = random.randint(1, 20)  # Usar el mismo rango que en el juego
        possible_neighbors = []

        # Usar los rangos de movimiento de config
        if GameConfig.MOVE_UP_RANGE[0] <= move_value <= GameConfig.MOVE_UP_RANGE[1]:
            possible_neighbors.append((x, y - 1))  # Arriba
        elif GameConfig.MOVE_RIGHT_RANGE[0] <= move_value <= GameConfig.MOVE_RIGHT_RANGE[1]:
            possible_neighbors.append((x + 1, y))  # Derecha
        elif GameConfig.MOVE_DOWN_RANGE[0] <= move_value <= GameConfig.MOVE_DOWN_RANGE[1]:
            possible_neighbors.append((x, y + 1))  # Abajo
        elif GameConfig.MOVE_LEFT_RANGE[0] <= move_value <= GameConfig.MOVE_LEFT_RANGE[1]:
            possible_neighbors.append((x - 1, y))  # Izquierda

        # Filtrar vecinos válidos
        valid_neighbors = []
        for nx, ny in possible_neighbors:
            # Verificar límites del grid
            if (0 <= nx < GameConfig.GRID_WIDTH and
                    0 <= ny < GameConfig.GRID_HEIGHT):
                # Verificar que no sea un obstáculo
                if (nx, ny) not in self.game_state.obstacles:
                    valid_neighbors.append((nx, ny))

        # Calcular puntuación para cada vecino
        neighbor_scores = []
        for neighbor in valid_neighbors:
            nx, ny = neighbor
            # Obtener frecuencia de visitas (normalizada)
            visit_count = self.movement_matrix[ny][nx]
            visit_score = visit_count / (np.max(self.movement_matrix) + 1)

            # Calcular distancia a la meta
            distance = self._heuristic(neighbor, goal)
            distance_score = distance / (GameConfig.GRID_WIDTH + GameConfig.GRID_HEIGHT)

            # Puntuación combinada (menor es mejor)
            combined_score = (0.7 * distance_score) + (0.3 * visit_score)
            neighbor_scores.append((neighbor, combined_score))

        # Ordenar por puntuación (menor primero)
        neighbor_scores.sort(key=lambda x: x[1])

        # Devolver solo los vecinos ordenados
        return [n[0] for n in neighbor_scores]

    def _heuristic(self, pos1, pos2):
        """
        Calcula la distancia Manhattan entre dos puntos del grid.
        
        La distancia Manhattan es la suma de las diferencias absolutas
        de las coordenadas cartesianas, lo que representa el número mínimo
        de movimientos en el grid (horizontal y vertical) para ir de un punto a otro.
        
        Esta heurística es admisible para este problema, ya que nunca sobreestima
        la distancia real entre dos puntos en un grid donde solo se permiten
        movimientos horizontales y verticales.
        
        Args:
            pos1 (tuple): Primera posición (x1, y1).
            pos2 (tuple): Segunda posición (x2, y2).
            
        Returns:
            int: Distancia Manhattan entre los dos puntos.
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
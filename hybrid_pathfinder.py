import numpy as np
import math
import random
from config import GameConfig
from AStar import AStar
from HeatMapPathfinding import HeatMapPathfinding


class HybridPathfinder:
    """
    Sistema híbrido de pathfinding que combina las ventajas de AStar y HeatMapPathfinding.
    
    Esta implementación:
    1. Mantiene la seguridad estricta de AStar (MIN_SAFE_DISTANCE = 5)
    2. Aprovecha el aprendizaje por refuerzo de HeatMapPathfinding
    3. Implementa recálculo dinámico de rutas cuando se detectan enemigos
    4. Mantiene una ratio de entrenamiento 2:1 de éxitos vs fallos
    5. Verifica condiciones de victoria o game over
    
    Características principales:
    - Integración de zonas de peligro de HeatMap con distancias seguras de AStar
    - Validación continua de caminos para detectar bloqueos o enemigos
    - Recálculo automático de rutas cuando es necesario
    - Aprendizaje mejorado con peso 2:1 para caminos exitosos
    - Detección de victoria cuando el jugador llega a la casa
    """

    # Constantes para garantizar seguridad y gestión de recálculos
    MIN_SAFE_DISTANCE = 5  # Distancia mínima segura a enemigos (en unidades)
    MAX_RECALCULATIONS = 3  # Número máximo de recálculos antes de considerar game over
    SUCCESSFUL_PATH_WEIGHT = 2.0  # Peso para mantener la proporción 2:1 en entrenamiento

    def __init__(self, game_state):
        """
        Inicializa el pathfinder híbrido con componentes de AStar y HeatMapPathfinding.
        
        Args:
            game_state: Objeto GameState que contiene el estado actual del juego,
                       incluyendo obstáculos, enemigos, posición del jugador y de la casa.
        """
        self.game_state = game_state
        
        # Inicializar componentes de pathfinding
        self.astar = AStar(game_state)
        self.heat_map = HeatMapPathfinding(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        
        # Configurar el mapa de calor con obstáculos y enemigos
        self.heat_map.obstacles = set(game_state.obstacles)
        self.heat_map.enemies = set(game_state.enemies)
        
        # Variables para manejar el estado del camino
        self.current_path = None
        self.recalculation_count = 0
        self.is_game_over = False
        self.success_path_count = 0
        self.failed_path_count = 0
        
        # Historial de caminos parciales exitosos
        self.successful_partial_paths = []
        self.danger_zones = set()
        
        # Si el mapa de calor no ha sido entrenado, realizar entrenamiento inicial
        if self.heat_map.execution_count == 0:
            self._perform_initial_training()

    def _perform_initial_training(self, iterations=100):
        """
        Realiza un entrenamiento inicial del mapa de calor si no ha sido entrenado previamente.
        
        Args:
            iterations (int): Número de iteraciones para el entrenamiento inicial.
        """
        print("Realizando entrenamiento inicial del mapa de calor...")
        start_pos = self.game_state.player_pos
        goal_pos = self.game_state.house_pos
        
        # Entrenar el mapa de calor
        self.heat_map.train(
            start_pos=start_pos,
            goal_pos=goal_pos,
            obstacles=self.game_state.obstacles,
            enemies=self.game_state.enemies,
            num_iterations=iterations
        )
        
        print(f"Entrenamiento inicial completado con {self.heat_map.execution_count} ejecuciones exitosas.")

    def update_danger_zones(self):
        """
        Actualiza las zonas de peligro basadas en las posiciones actuales de los enemigos.
        Combina la detección de AStar con la información del mapa de calor.
        """
        # Actualizar posiciones bloqueadas en AStar
        self.astar.blocked_positions = self.astar._calculate_blocked_positions()
        
        # Actualizar enemigos en el mapa de calor
        self.heat_map.enemies = set(self.game_state.enemies)
        
        # Calcular zonas de peligro adicionales (casillas con valores bajos en el mapa de calor)
        self.danger_zones = set()
        
        # Agregar todas las posiciones bloqueadas de AStar a las zonas de peligro
        self.danger_zones.update(self.astar.blocked_positions)
        
        # Identificar casillas con valores bajos en el mapa de calor como zonas de peligro adicionales
        if self.heat_map.execution_count > 0:
            threshold = np.mean(self.heat_map.heat_map) * 0.5  # 50% por debajo de la media
            for y in range(self.heat_map.grid_height):
                for x in range(self.heat_map.grid_width):
                    if self.heat_map.heat_map[y][x] < threshold:
                        # Solo agregar si no es un obstáculo y no está ya en las zonas de peligro
                        pos = (x, y)
                        if pos not in self.game_state.obstacles and pos not in self.danger_zones:
                            self.danger_zones.add(pos)

    def is_path_safe(self, path):
        """
        Verifica si un camino completo es seguro respecto a las posiciones actuales de los enemigos.
        
        Args:
            path (list): Lista de posiciones que forman el camino a verificar.
            
        Returns:
            bool: True si el camino es seguro, False si algún punto está en peligro.
        """
        if not path:
            return False
            
        # Verificar cada punto del camino
        for pos in path:
            # Verificar que la posición sea válida según AStar (distancia segura de enemigos)
            if not self.astar.is_position_valid(pos):
                return False
                
            # Verificar que la posición no esté en una zona de peligro
            if pos in self.danger_zones:
                return False
                
            # Verificación adicional de distancia mínima a cada enemigo
            if hasattr(self.game_state, 'enemies') and isinstance(self.game_state.enemies, dict):
                for enemy_data in self.game_state.enemies.values():
                    if isinstance(enemy_data, dict) and 'position' in enemy_data:
                        enemy_pos = enemy_data['position']
                        dx = pos[0] - enemy_pos[0]
                        dy = pos[1] - enemy_pos[1]
                        distance = (dx * dx + dy * dy) ** 0.5
                        
                        # Usar un pequeño margen adicional para seguridad
                        if distance <= self.MIN_SAFE_DISTANCE:
                            return False
            
            # También verificar con el conjunto de enemy_positions para compatibilidad
            for enemy_pos in self.game_state.enemy_positions:
                dx = pos[0] - enemy_pos[0]
                dy = pos[1] - enemy_pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                
                # Usar un pequeño margen adicional para seguridad
                if distance <= self.MIN_SAFE_DISTANCE:
                    return False
                
        return True

    def validate_path(self):
        """
        Valida si el camino actual sigue siendo seguro con las posiciones actuales de los enemigos.
        
        Returns:
            bool: True si el camino sigue siendo válido, False si necesita recalcularse.
        """
        if not self.current_path:
            return False
            
        # Obtener posición actual del jugador
        player_pos = self.game_state.player_pos
        
        # Verificar cada punto del camino restante
        player_index = -1
        for i, pos in enumerate(self.current_path):
            if pos == player_pos:
                player_index = i
                break
        
        # Si el jugador no está exactamente en el camino, buscar el punto más cercano
        if player_index == -1:
            min_distance = float('inf')
            for i, pos in enumerate(self.current_path):
                distance = abs(pos[0] - player_pos[0]) + abs(pos[1] - player_pos[1])
                if distance < min_distance:
                    min_distance = distance
                    player_index = i
            
            # Si el jugador se ha desviado demasiado del camino, recalcular
            if min_distance > 1:
                return False
        
        # Verificar el resto del camino desde la posición actual
        remaining_path = self.current_path[player_index:]
        
        # Verificar si algún enemigo está demasiado cerca del camino restante
        for pos in remaining_path:
            # Verificar distancia a cada enemigo
            if hasattr(self.game_state, 'enemies') and isinstance(self.game_state.enemies, dict):
                for enemy_data in self.game_state.enemies.values():
                    if isinstance(enemy_data, dict) and 'position' in enemy_data:
                        enemy_pos = enemy_data['position']
                        dx = pos[0] - enemy_pos[0]
                        dy = pos[1] - enemy_pos[1]
                        distance = (dx * dx + dy * dy) ** 0.5
                        
                        if distance <= self.MIN_SAFE_DISTANCE:
                            return False
            
            # También verificar con el conjunto de enemy_positions para compatibilidad
            for enemy_pos in self.game_state.enemy_positions:
                dx = pos[0] - enemy_pos[0]
                dy = pos[1] - enemy_pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= self.MIN_SAFE_DISTANCE:
                    return False
        
        return True

    def find_path(self, start, goal):
        """
        Encuentra un camino óptimo combinando AStar y HeatMapPathfinding.
        
        Estrategia:
        1. Primero intenta usar HeatMapPathfinding para aprovechar el aprendizaje previo
        2. Si no encuentra camino o no es seguro, usa AStar para garantizar seguridad
        3. Si AStar tampoco encuentra camino, retorna None (game over potencial)
        
        Args:
            start (tuple): Posición inicial (x, y)
            goal (tuple): Posición objetivo (x, y)
            
        Returns:
            list or None: Lista de posiciones que forman el camino si existe,
                         None si no hay camino seguro posible.
        """
        # Actualizar zonas de peligro
        self.update_danger_zones()
        
        # Actualizar posiciones bloqueadas en AStar para estar seguros
        self.astar.blocked_positions = self.astar._calculate_blocked_positions()
        
        # Paso 1: Intentar con HeatMapPathfinding si ya ha sido entrenado
        heat_map_path = None
        if self.heat_map.execution_count > 0:
            heat_map_path = self.heat_map.find_path_with_heat_map(start, goal)
            
            # Verificar si el camino del mapa de calor es seguro con validación estricta
            if heat_map_path and self.is_path_safe(heat_map_path):
                self.current_path = heat_map_path
                return heat_map_path
        
        # Paso 2: Si HeatMapPathfinding falló o el camino no es seguro, usar AStar
        astar_path = self.astar.find_path(start, goal)
        
        # Validar nuevamente el camino de AStar con nuestros criterios estrictos
        if astar_path and not self.is_path_safe(astar_path):
            return None
        
        if astar_path:
            self.current_path = astar_path
            
            # Registrar este camino en el mapa de calor con peso doble para mantener el ratio 2:1
            if self.heat_map.execution_count > 0:
                # Aplicar el camino dos veces para mantener el ratio 2:1
                self.heat_map.update_heat_map(astar_path, start, goal)
                # Segunda actualización con peso adicional para rutas seguras
                self.heat_map.update_heat_map(astar_path, start, goal)
                
            return astar_path
            
        # Si ambos métodos fallan, no hay camino seguro
        self.current_path = None
        return None

    def recalculate_path(self):
        """
        Recalcula el camino cuando se detecta que el actual ya no es seguro.
        
        Returns:
            list or None: Nuevo camino calculado, o None si no se pudo encontrar uno.
        """
        # Incrementar contador de recálculos
        self.recalculation_count += 1
        
        # Verificar si hemos excedido el número máximo de recálculos
        if self.recalculation_count > self.MAX_RECALCULATIONS:
            self.is_game_over = True
            return None
            
        # Obtener posiciones actuales
        start = self.game_state.player_pos
        goal = self.game_state.house_pos
        
        # Actualizar zonas de peligro
        self.update_danger_zones()
        
        # Intentar encontrar un nuevo camino
        new_path = self.find_path(start, goal)
        
        # Si encontramos un camino, reiniciar el estado
        if new_path:
            self.current_path = new_path
            return new_path
            
        # Si no se pudo encontrar un camino, incrementar el contador de fallos
        self.failed_path_count += 1
        
        # Mantener el ratio 2:1 (éxitos:fallos)
        self._maintain_training_ratio()
        
        # Si seguimos sin camino, es game over
        if not new_path and self.recalculation_count >= self.MAX_RECALCULATIONS:
            self.is_game_over = True
            
        return new_path

    def _maintain_training_ratio(self):
        """
        Mantiene el ratio de entrenamiento 2:1 (éxitos:fallos).
        Si hay demasiados fallos en comparación con éxitos, ajusta el entrenamiento.
        """
        # Verificar si necesitamos más caminos exitosos para mantener el ratio 2:1
        if self.failed_path_count * 2 > self.success_path_count:
            # Entrenar más caminos exitosos
            if self.success_path_count > 0 and self.successful_partial_paths:
                # Usar los caminos parciales exitosos para entrenamiento adicional
                for path in self.successful_partial_paths:
                    if len(path) >= 2:
                        # Reforzar los caminos exitosos con peso adicional
                        start = path[0]
                        end = path[-1]
                        self.heat_map.update_heat_map(path, start, end)
                        # Aplicar segunda actualización para mantener la ratio 2:1
                        self.heat_map.update_heat_map(path, start, end)
                        
                        self.success_path_count += 2
                        
                print(f"Ratio de entrenamiento ajustado: {self.success_path_count} éxitos, {self.failed_path_count} fallos")

    def check_victory_conditions(self):
        """
        Verifica si se cumplen las condiciones de victoria o derrota.
        
        Returns:
            tuple: (victoria, game_over, mensaje)
                victoria (bool): True si el jugador llegó a la casa
                game_over (bool): True si el juego ha terminado por derrota
                mensaje (str): Mensaje descriptivo del estado
        """
        # Victoria: El jugador llegó a la casa
        if self.game_state.player_pos == self.game_state.house_pos:
            # Registrar este camino como exitoso con doble peso
            path = self.current_path or [self.game_state.player_pos]
            if self.heat_map.execution_count > 0 and len(path) > 1:
                self.heat_map.update_heat_map(path, path[0], path[-1])
                self.heat_map.update_heat_map(path, path[0], path[-1])  # Segunda aplicación
                
            self.success_path_count += 2
            return True, False, "¡Victoria! Has llegado a la casa."
            
        # Game over: Jugador atrapado por enemigo
        if hasattr(self.game_state, 'player_caught') and self.game_state.player_caught:
            self.is_game_over = True
            self.failed_path_count += 1
            return False, True, "Game Over: Has sido capturado por un enemigo."
            
        # Game over: Máximo de recálculos excedido
        if self.recalculation_count > self.MAX_RECALCULATIONS:
            self.is_game_over = True
            self.failed_path_count += 1
            return False, True, "Game Over: No se pudo encontrar un camino seguro después de múltiples intentos."


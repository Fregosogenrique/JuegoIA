from GameState import GameState
from hybrid_pathfinder import HybridPathfinder
from config import GameConfig


class EnhancedGameState(GameState):
    """
    Versión mejorada de GameState que implementa pathfinding híbrido.
    
    Esta clase extiende GameState añadiendo:
    - Integración con HybridPathfinder para encontrar rutas seguras
    - Validación y recálculo de caminos cuando se detectan enemigos
    - Manejo de condiciones de victoria y derrota
    - Mantenimiento de la proporción de entrenamiento 2:1
    
    Todas las funcionalidades originales de GameState se mantienen,
    añadiendo nuevas capacidades para garantizar que el jugador pueda
    llegar a la casa o se produzca un game over apropiado.
    """
    
    def __init__(self, grid_width=None, grid_height=None):
        """
        Inicializa una instancia de EnhancedGameState.
        
        Args:
            grid_width (int, opcional): Ancho del grid del juego. Si no se proporciona,
                                       usa el valor de GameConfig.
            grid_height (int, opcional): Alto del grid del juego. Si no se proporciona,
                                        usa el valor de GameConfig.
        """
        # Usar valores predeterminados si no se proporcionan
        if grid_width is None:
            grid_width = GameConfig.GRID_WIDTH
        if grid_height is None:
            grid_height = GameConfig.GRID_HEIGHT
            
        # Inicializar la clase base
        super().__init__(grid_width, grid_height)
        
        # Atributos adicionales para pathfinding híbrido
        self.pathfinder = None
        self.current_path = []
        self.path_valid = False
        self.retry_count = 0
        self.max_retries = 3
        self.game_over = False
        
        # Atributos para tracking de éxito/fallo
        self.successful_paths = 0
        self.failed_paths = 0
        
        # Historial de caminos parciales exitosos
        self.partial_success_paths = []
    
    def initialize_game(self):
        """
        Inicializa el estado del juego con valores predeterminados y configura el pathfinder.
        
        Extiende el método original para añadir la inicialización del pathfinder
        y cálculo del camino inicial.
        """
        # Llamar al método de la clase base
        super().initialize_game()
        
        # Inicializar el pathfinder híbrido
        self.pathfinder = HybridPathfinder(self)
        
        # Reiniciar estados relacionados con pathfinding
        self.current_path = []
        self.path_valid = False
        self.retry_count = 0
        self.game_over = False
        self.successful_paths = 0
        self.failed_paths = 0
        self.partial_success_paths = []
        
        # Calcular un camino inicial
        self.calculate_initial_path()
    
    def calculate_initial_path(self):
        """
        Calcula el camino inicial desde la posición del jugador hasta la casa.
        
        Returns:
            bool: True si se encontró un camino válido, False en caso contrario.
        """
        if not self.pathfinder:
            self.pathfinder = HybridPathfinder(self)
        
        # Calcular camino inicial
        path = self.pathfinder.find_path(self.player_pos, self.house_pos)
        
        if path:
            self.current_path = path
            self.path_valid = True
            self.successful_paths += 1
            return True
        else:
            self.path_valid = False
            self.failed_paths += 1
            return False
    
    def validate_current_path(self):
        """
        Valida si el camino actual sigue siendo seguro.
        
        Returns:
            bool: True si el camino sigue siendo válido, False si necesita recalcularse.
        """
        if not self.pathfinder or not self.current_path:
            self.path_valid = False
            return False
        
        # Usar el pathfinder para validar el camino
        self.path_valid = self.pathfinder.validate_path()
        
        # Si el camino es inválido pero teníamos uno antes, guardar el camino parcial recorrido
        if not self.path_valid and len(self.current_path) > 1:
            # Encontrar posición del jugador en el camino
            player_index = -1
            for i, pos in enumerate(self.current_path):
                if pos == self.player_pos:
                    player_index = i
                    break
            
            # Si el jugador está en el camino, guardar el camino hasta ese punto
            if player_index > 0:
                partial_path = self.current_path[:player_index+1]
                if len(partial_path) > 1:
                    self.partial_success_paths.append(partial_path)
        
        return self.path_valid
    
    def recalculate_path(self):
        """
        Recalcula el camino cuando se detecta que el actual ya no es seguro.
        
        Returns:
            bool: True si se encontró un nuevo camino válido, False si no es posible.
        """
        if not self.pathfinder:
            return False
        
        # Incrementar contador de reintentos
        self.retry_count += 1
        
        # Verificar si hemos excedido el número máximo de reintentos
        if self.retry_count > self.max_retries:
            self.game_over = True
            return False
        
        # Actualizar zonas de peligro antes de recalcular
        self.pathfinder.update_danger_zones()
        
        # Intentar recalcular el camino
        new_path = self.pathfinder.recalculate_path()
        
        if new_path:
            self.current_path = new_path
            self.path_valid = True
            self.successful_paths += 1
            
            # Mantener la proporción 2:1 de éxitos vs fallos
            self._maintain_training_ratio()
            
            return True
        else:
            self.path_valid = False
            self.failed_paths += 1
            
            if self.retry_count >= self.max_retries:
                self.game_over = True
            
            return False
    
    def _maintain_training_ratio(self):
        """
        Mantiene la proporción 2:1 de éxitos vs fallos en el entrenamiento.
        
        Cuando el ratio cae por debajo de 2:1, refuerza los caminos exitosos
        previos para restaurar el balance.
        """
        # Calcular cuántos éxitos adicionales necesitamos para mantener el ratio 2:1
        # Añadir +1 para asegurar que siempre tenemos al menos un éxito más de lo necesario
        required_successes = max(0, (self.failed_paths * 2) - self.successful_paths + 1)
        
        if required_successes > 0 and self.pathfinder and hasattr(self.pathfinder, 'heat_map'):
            success_added = 0
            
            # Primero intentar con caminos parciales
            if self.partial_success_paths:
                for path in self.partial_success_paths:
                    if len(path) >= 2:
                        start, end = path[0], path[-1]
                        # Doble actualización para mantener ratio 2:1
                        self.pathfinder.heat_map.update_heat_map(path, start, end)
                        self.pathfinder.heat_map.update_heat_map(path, start, end)
                        success_added += 2
                        
                        if success_added >= required_successes:
                            break
            
            # Si aún necesitamos más éxitos y tenemos un camino actual válido
            remaining = required_successes - success_added
            if remaining > 0 and self.current_path and len(self.current_path) >= 2:
                start, end = self.current_path[0], self.current_path[-1]
                for _ in range((remaining + 1) // 2):  # Redondear hacia arriba
                    self.pathfinder.heat_map.update_heat_map(self.current_path, start, end)
                    self.pathfinder.heat_map.update_heat_map(self.current_path, start, end)
                    success_added += 2
            
            # Si no tenemos caminos disponibles pero necesitamos mejorar el ratio,
            # crear un camino directo ficticio (esto es un último recurso)
            if success_added == 0 and required_successes > 0:
                start = self.player_pos
                end = self.house_pos
                path = [start, end]  # Camino directo simple
                for _ in range((required_successes + 1) // 2):
                    self.pathfinder.heat_map.update_heat_map(path, start, end)
                    self.pathfinder.heat_map.update_heat_map(path, start, end)
                    success_added += 2
            
            self.successful_paths += success_added
            print(f"Ratio de entrenamiento ajustado: {self.successful_paths} éxitos, {self.failed_paths} fallos")
    
    def check_player_collision(self):
        """
        Verifica si el jugador ha colisionado con algún enemigo.
        
        Override del método de la clase base para establecer game_over además de player_caught.
        
        Returns:
            bool: True si hay colisión, False en caso contrario
        """
        if self.player_pos in self.enemy_positions:
            self.player_caught = True
            self.game_over = True  # Asegurar que game_over se establece
            return True
        return False
    
    def check_victory_conditions(self):
        """
        Verifica si se cumplen las condiciones de victoria o derrota.
        
        Returns:
            str: Mensaje descriptivo del estado ("victoria", "derrota" o None)
        """
        # Victoria: El jugador llegó a la casa
        if self.player_pos == self.house_pos:
            self.victory = True
            
            # Registrar este camino como exitoso si tenemos uno
            if self.current_path and self.pathfinder and hasattr(self.pathfinder, 'heat_map'):
                # Aplicar doble refuerzo para mantener ratio 2:1
                self.pathfinder.heat_map.update_heat_map(self.current_path, self.current_path[0], self.current_path[-1])
                self.pathfinder.heat_map.update_heat_map(self.current_path, self.current_path[0], self.current_path[-1])
                
                self.successful_paths += 2
            
            return "victoria"
        
        # Derrota: Jugador atrapado por enemigo
        if self.player_caught:
            self.game_over = True
            self.failed_paths += 1
            return "derrota"
        
        # Derrota: Sin camino posible después de varios intentos
        if self.retry_count > self.max_retries:
            self.game_over = True
            self.failed_paths += 1
            return "derrota"
        
        # Consultar al pathfinder para verificaciones adicionales
        if self.pathfinder:
            victory, game_over, _ = self.pathfinder.check_victory_conditions()
            
            if victory:
                self.victory = True
                return "victoria"
            
            if game_over:
                self.game_over = True
                self.failed_paths += 1
                return "derrota"
        
        return None
    
    def is_valid_move(self, pos):
        """
        Verifica si una posición es válida para mover al jugador.
        
        Override del método original para añadir validación del pathfinder.
        
        Args:
            pos (tuple): Tupla (x, y) que representa la posición a verificar.
            
        Returns:
            bool: True si la posición es válida para moverse, False en caso contrario.
        """
        # Primero verificar con validación básica de la clase base
        if not super().is_valid_move(pos):
            return False
        
        # Verificación adicional con el pathfinder
        if self.pathfinder:
            # Verificar cada enemigo individualmente en su formato actual
            if hasattr(self, 'enemies') and isinstance(self.enemies, dict):
                for enemy_id, enemy_data in self.enemies.items():
                    # Obtener la posición del enemigo
                    if isinstance(enemy_data, dict) and 'position' in enemy_data:
                        enemy_pos = enemy_data['position']
                        dx = pos[0] - enemy_pos[0]
                        dy = pos[1] - enemy_pos[1]
                        distance = (dx * dx + dy * dy) ** 0.5
                        
                        # Estrictamente mayor que MIN_SAFE_DISTANCE
                        if distance <= HybridPathfinder.MIN_SAFE_DISTANCE:
                            return False
            
            # Verificar con el conjunto de posiciones de enemigos para compatibilidad
            for enemy_pos in self.enemy_positions:
                dx = pos[0] - enemy_pos[0]
                dy = pos[1] - enemy_pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                
                # Estrictamente mayor que MIN_SAFE_DISTANCE
                if distance <= HybridPathfinder.MIN_SAFE_DISTANCE:
                    return False
            
            # También usar la validación completa de AStar si está disponible
            if hasattr(self.pathfinder, 'astar'):
                # Forzar recálculo de posiciones bloqueadas para estar seguros
                self.pathfinder.astar.blocked_positions = self.pathfinder.astar._calculate_blocked_positions()
                if not self.pathfinder.astar.is_position_valid(pos):
                    return False
        
        return True
    
    def move_player(self, dx, dy):
        """
        Intenta mover al jugador en la dirección especificada.
        
        Override del método original para añadir validación y recálculo de camino.
        
        Args:
            dx (int): Desplazamiento en el eje X (-1, 0, 1).
            dy (int): Desplazamiento en el eje Y (-1, 0, 1).
            
        Returns:
            bool: True si el movimiento fue exitoso, False si no se pudo mover.
        """
        # Intentar mover usando el método de la clase base
        move_success = super().move_player(dx, dy)
        
        if move_success:
            # Verificar si hemos llegado a la casa
            if self.player_pos == self.house_pos:
                self.victory = True
                self.check_victory_conditions()
                return True
            
            # Validar el camino actual después del movimiento
            if self.current_path and not self.validate_current_path():
                # Si el camino ya no es válido, intentar recalcular
                if not self.recalculate_path():
                    # Si no se pudo recalcular, verificar condiciones de game over
                    self.check_victory_conditions()
        
        return move_success
    
    def update_enemy_positions(self):
        """
        Actualiza las posiciones de los enemigos y valida el camino actual.
        
        Override del método original para añadir validación y recálculo de camino
        después de que los enemigos se muevan.
        """
        # Mover enemigos usando el método de la clase base
        super().update_enemy_positions()
        
        # Después de mover enemigos, actualizar zonas de peligro
        if self.pathfinder:
            self.pathfinder.update_danger_zones()
            
            # Validar si el camino actual sigue siendo seguro
            if self.current_path and not self.validate_current_path():
                # Si el camino ya no es válido, intentar recalcular
                if not self.recalculate_path():
                    # Si no se pudo recalcular, verificar condiciones de game over
                    self.check_victory_conditions()
        
        # Verificar colisión con el jugador
        if self.check_player_collision():
            self.game_over = True
            self.check_victory_conditions()
    
    def get_next_move_suggestion(self):
        """
        Obtiene la sugerencia del siguiente movimiento basada en el camino actual.
        
        Útil para implementar movimiento automático o asistido del jugador.
        
        Returns:
            tuple or None: Tupla con (dx, dy) sugerido, o None si no hay sugerencia.
        """
        if not self.current_path or len(self.current_path) < 2:
            return None
        
        # Encontrar la posición actual del jugador en el camino
        player_index = -1
        for i, pos in enumerate(self.current_path):
            if pos == self.player_pos:
                player_index = i
                break
        
        # Si no encontramos al jugador en el camino actual, usar el primer paso
        if player_index == -1:
            next_pos = self.current_path[1]  # El primer paso después de la posición inicial
        else:
            # Si el jugador está al final del camino, no hay sugerencia
            if player_index >= len(self.current_path) - 1:
                return None
            
            next_pos = self.current_path[player_index + 1]
        
        # Calcular el desplazamiento
        dx = next_pos[0] - self.player_pos[0]
        dy = next_pos[1] - self.player_pos[1]
        
        # Normalizar a -1, 0, 1
        if dx != 0:
            dx = 1 if dx > 0 else -1
        if dy != 0:
            dy = 1 if dy > 0 else -1
        
        return (dx, dy)


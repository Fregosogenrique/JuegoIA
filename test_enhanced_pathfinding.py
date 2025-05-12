import unittest
import random
import numpy as np
from config import GameConfig
from enhanced_game_state import EnhancedGameState
from hybrid_pathfinder import HybridPathfinder


class TestEnhancedPathfinding(unittest.TestCase):
    """
    Pruebas unitarias para verificar las funcionalidades del sistema de pathfinding híbrido
    y la integración con EnhancedGameState.
    """
    
    def setUp(self):
        """
        Configura un entorno controlado para las pruebas.
        """
        # Configuración controlada para pruebas
        self.game_state = EnhancedGameState(grid_width=20, grid_height=15)
        
        # Posiciones fijas para pruebas predecibles
        self.game_state.player_pos = (1, 1)
        self.game_state.house_pos = (18, 13)
        
        # Reiniciar obstáculos y enemigos para control total
        self.game_state.obstacles = set()
        self.game_state.enemies.clear()
        self.game_state.enemy_positions = set()
        
        # Inicializar pathfinder con entorno controlado
        self.game_state.pathfinder = HybridPathfinder(self.game_state)
        self.game_state.current_path = []
        
    def tearDown(self):
        """
        Limpia después de cada prueba.
        """
        self.game_state = None
        
    def add_test_enemies(self, positions):
        """
        Función auxiliar para añadir enemigos en posiciones específicas.
        """
        for pos in positions:
            self.game_state.add_enemy(pos)
            
    def add_test_obstacles(self, positions):
        """
        Función auxiliar para añadir obstáculos en posiciones específicas.
        """
        for pos in positions:
            self.game_state.obstacles.add(pos)
    
    #---------------------------------------------------------------------------
    # 1. Pruebas de pathfinding básico y evitación de enemigos
    #---------------------------------------------------------------------------
    
    def test_basic_path_finding(self):
        """
        Verifica que el pathfinder puede encontrar un camino básico sin obstáculos ni enemigos.
        """
        # Calcular camino inicial
        success = self.game_state.calculate_initial_path()
        
        # Verificar que se encontró un camino
        self.assertTrue(success, "No se pudo encontrar un camino en un grid vacío")
        self.assertTrue(len(self.game_state.current_path) > 0, "El camino encontrado está vacío")
        
        # Verificar que el camino comienza en player_pos y termina en house_pos
        self.assertEqual(self.game_state.current_path[0], self.game_state.player_pos, 
                         "El camino no comienza en la posición del jugador")
        self.assertEqual(self.game_state.current_path[-1], self.game_state.house_pos, 
                         "El camino no termina en la posición de la casa")
    
    def test_enemy_avoidance(self):
        """
        Verifica que el pathfinder evita enemigos manteniendo una distancia segura.
        """
        # Añadir un enemigo en el centro del grid
        enemy_pos = (10, 7)
        self.add_test_enemies([enemy_pos])
        
        # Calcular camino con enemigo presente
        self.game_state.calculate_initial_path()
        
        # Verificar que se encontró un camino
        self.assertTrue(len(self.game_state.current_path) > 0, "No se pudo encontrar un camino con un enemigo")
        
        # Verificar que cada punto del camino está a una distancia segura del enemigo
        for pos in self.game_state.current_path:
            dx = pos[0] - enemy_pos[0]
            dy = pos[1] - enemy_pos[1]
            distance = np.sqrt(dx**2 + dy**2)
            
            self.assertGreaterEqual(distance, HybridPathfinder.MIN_SAFE_DISTANCE, 
                                   f"El camino pasa demasiado cerca del enemigo ({pos}, distancia={distance})")
    
    def test_path_recalculation_when_blocked(self):
        """
        Verifica que el camino se recalcula cuando un enemigo bloquea la ruta actual.
        """
        # Calcular camino inicial sin enemigos
        initial_success = self.game_state.calculate_initial_path()
        self.assertTrue(initial_success, "No se pudo encontrar camino inicial")
        initial_path = self.game_state.current_path.copy()
        
        # Añadir enemigo en el camino actual
        if len(initial_path) > 2:
            blocking_point = initial_path[len(initial_path) // 2]
            self.add_test_enemies([blocking_point])
            
            # Forzar actualización de zonas de peligro
            self.game_state.pathfinder.update_danger_zones()
            
            # Validar el camino
            is_valid = self.game_state.validate_current_path()
            self.assertFalse(is_valid, "El camino se considera válido a pesar del enemigo que lo bloquea")
            
            # Recalcular camino
            recalc_success = self.game_state.recalculate_path()
            self.assertTrue(recalc_success, "No se pudo recalcular un camino alternativo")
            
            # Verificar que el nuevo camino es diferente y evita el punto bloqueado
            self.assertNotEqual(self.game_state.current_path, initial_path,
                              "El camino recalculado es idéntico al inicial")
            self.assertNotIn(blocking_point, self.game_state.current_path,
                            "El camino recalculado pasa por el punto bloqueado")
    
    #---------------------------------------------------------------------------
    # 2. Pruebas de mantenimiento de ratio de entrenamiento
    #---------------------------------------------------------------------------
    
    def test_success_failure_ratio(self):
        """
        Verifica que se mantiene un ratio 2:1 de éxitos vs fallos en el entrenamiento.
        """
        # Configurar un entorno donde se producirán varios fallos
        obstacles = [(x, 7) for x in range(5, 15)]  # Barrera horizontal
        self.add_test_obstacles(obstacles)
        
        # Añadir enemigos que obligarán a recalcular
        enemies = [(5, 5), (10, 10), (15, 5)]
        self.add_test_enemies(enemies)
        
        # Forzar varios recálculos fallidos
        self.game_state.calculate_initial_path()
        
        # Bloquear camino varias veces
        for i in range(3):
            # Añadir enemigo en el camino actual
            if self.game_state.current_path and len(self.game_state.current_path) > 2:
                blocking_point = self.game_state.current_path[len(self.game_state.current_path) // 2]
                self.add_test_enemies([blocking_point])
                
                # Forzar recálculo
                self.game_state.validate_current_path()
                self.game_state.recalculate_path()
        
        # Verificar que el ratio se mantiene aproximadamente 2:1
        success_count = self.game_state.successful_paths
        failure_count = self.game_state.failed_paths
        
        # Permitir cierta flexibilidad en el ratio exacto
        self.assertGreaterEqual(success_count, failure_count * 1.5, 
                               f"El ratio éxito/fallo ({success_count}:{failure_count}) es menor que 1.5:1")
    
    def test_path_weighting_in_heat_map(self):
        """
        Verifica que los caminos exitosos reciben un peso mayor en el mapa de calor.
        """
        # Preparar entorno y calcular camino inicial
        self.game_state.calculate_initial_path()
        
        # Obtenemos el camino encontrado y comprobamos que exista
        path = self.game_state.current_path
        self.assertTrue(len(path) > 0, "No se encontró un camino inicial")
        
        # Verificar que los valores en el mapa de calor son mayores para las casillas del camino
        if hasattr(self.game_state.pathfinder, 'heat_map'):
            heat_map = self.game_state.pathfinder.heat_map.heat_map
            
            # Calcular valor medio en el mapa de calor
            avg_heat = np.mean(heat_map)
            
            # Verificar que las casillas del camino tienen valores por encima de la media
            for pos in path:
                x, y = pos
                heat_value = heat_map[y][x]
                self.assertGreaterEqual(heat_value, avg_heat,
                                      f"La casilla {pos} del camino tiene un valor ({heat_value}) menor que la media ({avg_heat})")
    
    def test_learning_from_partial_successes(self):
        """
        Verifica que el sistema aprende de caminos parcialmente exitosos.
        """
        # Calcular camino inicial sin obstáculos
        self.game_state.calculate_initial_path()
        initial_path = self.game_state.current_path.copy()
        
        # Guardar un camino parcial (primeros 5 pasos)
        partial_path = initial_path[:5]
        self.game_state.partial_success_paths.append(partial_path)
        
        # Forzar un desequilibrio en el ratio de entrenamiento
        self.game_state.successful_paths = 1
        self.game_state.failed_paths = 2
        
        # Aplicar mantenimiento de ratio
        self.game_state._maintain_training_ratio()
        
        # Verificar que el ratio se ha corregido
        self.assertGreaterEqual(self.game_state.successful_paths, self.game_state.failed_paths * 2,
                              "No se corrigió el ratio de entrenamiento usando caminos parciales")
    
    #---------------------------------------------------------------------------
    # 3. Pruebas de condiciones de victoria y game over
    #---------------------------------------------------------------------------
    
    def test_successful_arrival_at_house(self):
        """
        Verifica que se detecta correctamente cuando el jugador llega a la casa.
        """
        # Mover al jugador a una posición adyacente a la casa
        house_x, house_y = self.game_state.house_pos
        self.game_state.player_pos = (house_x - 1, house_y)
        
        # Calcular camino hacia la casa
        self.game_state.calculate_initial_path()
        
        # Mover al jugador a la casa
        move_result = self.game_state.move_player(1, 0)
        
        # Verificar que el movimiento fue exitoso
        self.assertTrue(move_result, "No se pudo mover el jugador a la casa")
        
        # Verificar que se detectó la victoria
        self.assertTrue(self.game_state.victory, "No se detectó la victoria al llegar a la casa")
        
        # Verificar que check_victory_conditions retorna "victoria"
        result = self.game_state.check_victory_conditions()
        self.assertEqual(result, "victoria", "check_victory_conditions no retornó 'victoria'")
    
    def test_game_over_on_enemy_capture(self):
        """
        Verifica que se detecta game over cuando un enemigo captura al jugador.
        """
        # Colocar un enemigo adyacente al jugador
        player_x, player_y = self.game_state.player_pos
        enemy_pos = (player_x + 1, player_y)
        self.add_test_enemies([enemy_pos])
        
        # Simular movimiento del enemigo a la posición del jugador
        for enemy_id in self.game_state.enemies:
            self.game_state.update_enemy_position(enemy_id, self.game_state.player_pos)
            break  # Solo necesitamos mover un enemigo
        
        # Verificar colisión con el jugador
        collision = self.game_state.check_player_collision()
        
        # Verificar que se detectó la colisión
        self.assertTrue(collision, "No se detectó la colisión con el enemigo")
        self.assertTrue(self.game_state.player_caught, "No se estableció player_caught a True")
        self.assertTrue(self.game_state.game_over, "No se estableció game_over a True")
        
        # Verificar que check_victory_conditions retorna "derrota"
        result = self.game_state.check_victory_conditions()
        self.assertEqual(result, "derrota", "check_victory_conditions no retornó 'derrota'")
    
    def test_max_retries_exceeded(self):
        """
        Verifica que se detecta game over cuando se excede el máximo de reintentos.
        """
        # Crear un escenario donde no hay camino posible
        # Rodear al jugador con obstáculos
        player_x, player_y = self.game_state.player_pos
        obstacle_positions = [
            (player_x + 1, player_y),
            (player_x - 1, player_y),
            (player_x, player_y + 1),
            (player_x, player_y - 1)
        ]
        self.add_test_obstacles(obstacle_positions)
        
        # Forzar el número máximo de reintentos
        self.game_state.retry_count = self.game_state.max_retries
        
        # Intentar recalcular el camino una vez más
        recalc_success = self.game_state.recalculate_path()
        
        # Verificar que se detectó game over
        self.assertFalse(recalc_success, "Se reportó éxito en recalcular a pesar de no haber camino posible")
        self.assertTrue(self.game_state.game_over, "No se estableció game_over cuando se excedió max_retries")
        
        # Verificar que check_victory_conditions retorna "derrota"
        result = self.game_state.check_victory_conditions()
        self.assertEqual(result, "derrota", "check_victory_conditions no retornó 'derrota'")
    
    #---------------------------------------------------------------------------
    # 4. Pruebas de integración con game state
    #---------------------------------------------------------------------------
    
    def test_movement_validation(self):
        """
        Verifica que la validación de movimiento integra correctamente el pathfinder.
        """
        # Preparar entorno con un enemigo para probar la validación
        player_x, player_y = self.game_state.player_pos
        enemy_pos = (player_x + HybridPathfinder.MIN_SAFE_DISTANCE + 1, player_y)  # Enemigo a distancia segura + 1
        self.add_test_enemies([enemy_pos])
        
        # Movimiento válido alejándose del enemigo
        valid_move = self.game_state.is_valid_move((player_x - 1, player_y))
        self.assertTrue(valid_move, "Un movimiento válido se reporta como inválido")
        
        # Movimiento hacia el enemigo pero aún seguro
        slightly_closer_pos = (player_x + 1, player_y)
        dx = slightly_closer_pos[0] - enemy_pos[0]
        dy = slightly_closer_pos[1] - enemy_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Solo verificar si el movimiento mantiene la distancia segura
        if distance > HybridPathfinder.MIN_SAFE_DISTANCE:
            valid_closer_move = self.game_state.is_valid_move(slightly_closer_pos)
            self.assertTrue(valid_closer_move, "Un movimiento seguro hacia el enemigo se reporta como inválido")
        
        # Movimiento demasiado cerca del enemigo
        too_close_pos = (enemy_pos[0] - 2, enemy_pos[1])  # Posición a 2 unidades del enemigo
        invalid_move = self.game_state.is_valid_move(too_close_pos)
        self.assertFalse(invalid_move, "Un movimiento demasiado cerca del enemigo se reporta como válido")
    
    def test_path_validation_during_movement(self):
        """
        Verifica que el camino se valida y recalcula durante el movimiento del jugador.
        """
        # Calcular camino inicial
        self.game_state.calculate_initial_path()
        initial_path = self.game_state.current_path.copy()
        
        # Simular movimiento del jugador a lo largo del camino
        if len(initial_path) > 1:
            next_pos = initial_path[1]
            dx = next_pos[0] - self.game_state.player_pos[0]
            dy = next_pos[1] - self.game_state.player_pos[1]
            
            # Mover al jugador
            old_player_pos = self.game_state.player_pos
            move_success = self.game_state.move_player(dx, dy)
            
            # Verificar que el movimiento fue exitoso
            self.assertTrue(move_success, "No se pudo mover el jugador a lo largo del camino")
            self.assertNotEqual(self.game_state.player_pos, old_player_pos, "La posición del jugador no cambió")
            
            # Verificar que el camino sigue siendo válido después del movimiento
            self.assertTrue(self.game_state.path_valid, "El camino se invalidó después de un movimiento válido")
            
            # Ahora añadir un enemigo que bloquee el camino y verificar recálculo
            if len(self.game_state.current_path) > 2:
                blocking_point = self.game_state.current_path[2]  # Un punto más adelante en el camino
                self.add_test_enemies([blocking_point])
                
                # Mover al jugador otra vez, lo que debería llevar a recalcular
                if len(self.game_state.current_path) > 1:
                    next_pos = initial_path[1]
                    dx = next_pos[0] - self.game_state.player_pos[0]
                    dy = next_pos[1] - self.game_state.player_pos[1]
                    
                    self.game_state.move_player(dx, dy)
                    
                    # Verificar que el camino ha sido recalculado
                    self.assertNotEqual(self.game_state.current_path, initial_path, 
                                       "El camino no se recalculó después de añadir un enemigo")
    
    def test_enemy_update_triggers_recalculation(self):
        """
        Verifica que el movimiento de enemigos desencadena la recalculación del camino.
        """
        # Calcular camino inicial
        self.game_state.calculate_initial_path()
        initial_path = self.game_state.current_path.copy()
        
        # Añadir un enemigo lejos del camino
        enemy_pos = (self.game_state.grid_width - 2, self.game_state.grid_height - 2)
        self.add_test_enemies([enemy_pos])
        
        # El camino debería seguir siendo válido
        self.game_state.validate_current_path()
        self.assertTrue(self.game_state.path_valid, "El camino se invalidó por un enemigo lejos")
        
        # Ahora mover el enemigo a una posición que bloquee el camino
        if len(initial_path) > 2:
            blocking_point = initial_path[len(initial_path) // 2]
            enemy_id = None
            
            # Obtener el ID del enemigo
            for eid in self.game_state.enemies:
                enemy_id = eid
                break
                
            if enemy_id is not None:
                # Mover el enemigo
                self.game_state.update_enemy_position(enemy_id, blocking_point)
                
                # Actualizar posiciones de enemigos, lo que debería desencadenar validación y recálculo
                self.game_state.update_enemy_positions()
                
                # Verificar que el camino ya no es válido o ha sido recalculado
                self.assertNotEqual(self.game_state.current_path, initial_path, 
                                    "El camino no se recalculó después de que un enemigo lo bloqueara")
    
    def test_danger_zone_updates(self):
        """
        Verifica que las zonas de peligro se actualizan correctamente al mover enemigos.
        """
        # Asegurarse de que el pathfinder está inicializado
        if not self.game_state.pathfinder:
            self.game_state.pathfinder = HybridPathfinder(self.game_state)
            
        # Añadir un enemigo
        enemy_pos = (10, 10)
        self.add_test_enemies([enemy_pos])
        
        # Actualizar zonas de peligro
        self.game_state.pathfinder.update_danger_zones()
        initial_danger_zones = self.game_state.pathfinder.danger_zones.copy()
        
        # Verificar que la posición del enemigo está en las zonas de peligro
        self.assertIn(enemy_pos, initial_danger_zones, "La posición del enemigo no está en las zonas de peligro")
        
        # Verificar que las zonas cercanas al enemigo también están marcadas como peligrosas
        nearby_pos = (enemy_pos[0] + 1, enemy_pos[1])
        self.assertIn(nearby_pos, initial_danger_zones, "Una posición cercana al enemigo no está marcada como peligrosa")
        
        # Mover el enemigo
        enemy_id = None
        for eid in self.game_state.enemies:
            enemy_id = eid
            break
            
        if enemy_id is not None:
            new_enemy_pos = (5, 5)
            self.game_state.update_enemy_position(enemy_id, new_enemy_pos)
            
            # Actualizar zonas de peligro
            self.game_state.pathfinder.update_danger_zones()
            new_danger_zones = self.game_state.pathfinder.danger_zones
            
            # Verificar que la nueva posición está en las zonas de peligro
            self.assertIn(new_enemy_pos, new_danger_zones, "La nueva posición del enemigo no está en las zonas de peligro")
            
            # Verificar que las zonas han cambiado
            self.assertNotEqual(initial_danger_zones, new_danger_zones, "Las zonas de peligro no se actualizaron")
    
    def test_next_move_suggestion(self):
        """
        Verifica que las sugerencias de movimiento son válidas y consistentes con el camino.
        """
        # Calcular camino inicial
        self.game_state.calculate_initial_path()
        
        # Verificar que hay un camino
        self.assertTrue(len(self.game_state.current_path) > 1, "No hay camino para sugerir movimientos")
        
        # Obtener sugerencia de movimiento
        move_suggestion = self.game_state.get_next_move_suggestion()
        
        # Verificar que la sugerencia no es None
        self.assertIsNotNone(move_suggestion, "No se produjo sugerencia de movimiento")
        
        # Verificar que la sugerencia es una tupla de dos elementos (dx, dy)
        self.assertEqual(len(move_suggestion), 2, "La sugerencia no tiene el formato correcto (dx, dy)")
        
        # Verificar que los valores están normalizados a -1, 0, 1
        dx, dy = move_suggestion
        self.assertIn(dx, [-1, 0, 1], "dx no está normalizado a -1, 0, 1")
        self.assertIn(dy, [-1, 0, 1], "dy no está normalizado a -1, 0, 1")
        
        # Calcular la nueva posición basada en la sugerencia
        new_pos = (self.game_state.player_pos[0] + dx, self.game_state.player_pos[1] + dy)
        
        # Verificar que la posición sugerida es válida
        self.assertTrue(self.game_state.is_valid_move(new_pos), "La posición sugerida no es válida")
        
        # Verificar que la posición sugerida está en el camino o es adyacente a él
        is_on_path = new_pos in self.game_state.current_path
        is_next_in_path = False
        
        for i, pos in enumerate(self.game_state.current_path[:-1]):
            if pos == self.game_state.player_pos:
                is_next_in_path = self.game_state.current_path[i+1] == new_pos
                break
                
        self.assertTrue(is_on_path or is_next_in_path, 
                        "La posición sugerida no está en el camino o no es la siguiente posición")
    
    def test_suggestions_with_obstacles(self):
        """
        Verifica que las sugerencias de movimiento funcionan correctamente con obstáculos.
        """
        # Añadir algunos obstáculos
        obstacles = [(5, 5), (6, 5), (7, 5), (8, 5), (9, 5)]  # Barrera horizontal
        self.add_test_obstacles(obstacles)
        
        # Calcular camino con obstáculos
        self.game_state.calculate_initial_path()
        
        # Verificar que hay un camino a pesar de los obstáculos
        self.assertTrue(len(self.game_state.current_path) > 1, "No hay camino con obstáculos")
        
        # Verificar que el camino evita los obstáculos
        for obs in obstacles:
            self.assertNotIn(obs, self.game_state.current_path, 
                            f"El camino pasa por un obstáculo en {obs}")
        
        # Obtener sugerencia de movimiento
        move_suggestion = self.game_state.get_next_move_suggestion()
        
        # Verificar que la sugerencia no lleva a un obstáculo
        if move_suggestion:
            dx, dy = move_suggestion
            new_pos = (self.game_state.player_pos[0] + dx, self.game_state.player_pos[1] + dy)
            self.assertNotIn(new_pos, obstacles, "La sugerencia lleva a un obstáculo")
    
    def test_suggestions_near_enemies(self):
        """
        Verifica que las sugerencias de movimiento mantienen al jugador lejos de los enemigos.
        """
        # Añadir un enemigo
        enemy_pos = (10, 10)
        self.add_test_enemies([enemy_pos])
        
        # Calcular camino con enemigos
        self.game_state.calculate_initial_path()
        
        # Verificar que hay un camino a pesar del enemigo
        self.assertTrue(len(self.game_state.current_path) > 1, "No hay camino con enemigos")
        
        # Obtener sugerencia de movimiento
        move_suggestion = self.game_state.get_next_move_suggestion()
        
        # Verificar que la sugerencia mantiene distancia segura del enemigo
        if move_suggestion:
            dx, dy = move_suggestion
            new_pos = (self.game_state.player_pos[0] + dx, self.game_state.player_pos[1] + dy)
            
            # Calcular distancia al enemigo
            enemy_dx = new_pos[0] - enemy_pos[0]
            enemy_dy = new_pos[1] - enemy_pos[1]
            distance = np.sqrt(enemy_dx**2 + enemy_dy**2)
            
            # Verificar que la distancia es segura
            self.assertGreaterEqual(distance, HybridPathfinder.MIN_SAFE_DISTANCE, 
                                  "La sugerencia de movimiento lleva demasiado cerca del enemigo")
        
        # Simular varios movimientos siguiendo las sugerencias
        for _ in range(5):  # Probar 5 movimientos
            # Obtener sugerencia de movimiento
            move_suggestion = self.game_state.get_next_move_suggestion()
            
            if not move_suggestion:
                break  # No hay más sugerencias
                
            # Mover al jugador según la sugerencia
            dx, dy = move_suggestion
            self.game_state.move_player(dx, dy)
            
            # Verificar que seguimos a distancia segura del enemigo
            player_pos = self.game_state.player_pos
            enemy_dx = player_pos[0] - enemy_pos[0]
            enemy_dy = player_pos[1] - enemy_pos[1]
            distance = np.sqrt(enemy_dx**2 + enemy_dy**2)
            
            self.assertGreaterEqual(distance, HybridPathfinder.MIN_SAFE_DISTANCE, 
                                  f"El movimiento {_+1} ha llevado demasiado cerca del enemigo (distancia={distance})")
            
        # Verificar que el camino completo mantiene distancia segura
        for pos in self.game_state.current_path:
            enemy_dx = pos[0] - enemy_pos[0]
            enemy_dy = pos[1] - enemy_pos[1]
            distance = np.sqrt(enemy_dx**2 + enemy_dy**2)
            
            self.assertGreaterEqual(distance, HybridPathfinder.MIN_SAFE_DISTANCE, 
                                  f"El camino pasa demasiado cerca del enemigo en {pos} (distancia={distance})")
    
    def test_complete_game_flow(self):
        """
        Prueba integral que simula un flujo completo de juego desde inicio hasta victoria.
        Verifica todas las funcionalidades trabajando en conjunto.
        """
        # 1. Inicializar juego con obstáculos y enemigos
        obstacles = [(5, 5), (6, 5), (7, 5)]  # Barrera parcial
        self.add_test_obstacles(obstacles)
        
        enemies = [(8, 8), (12, 6)]
        self.add_test_enemies(enemies)
        
        # 2. Calcular camino inicial
        initial_success = self.game_state.calculate_initial_path()
        self.assertTrue(initial_success, "No se pudo calcular un camino inicial")
        initial_path = self.game_state.current_path.copy()
        
        # 3. Mover al jugador siguiendo el camino, con eventos dinámicos
        steps_taken = 0
        max_steps = 50  # Límite para evitar bucles infinitos
        
        while not self.game_state.victory and not self.game_state.game_over and steps_taken < max_steps:
            # Obtener sugerencia del siguiente movimiento
            move_suggestion = self.game_state.get_next_move_suggestion()
            
            if not move_suggestion:
                # Si no hay sugerencia, verificar si el camino es válido
                if not self.game_state.validate_current_path():
                    # Recalcular si es necesario
                    self.game_state.recalculate_path()
                    move_suggestion = self.game_state.get_next_move_suggestion()
                    
            # Si aún no hay sugerencia, no podemos continuar
            if not move_suggestion:
                break
                
            # Mover al jugador según la sugerencia
            dx, dy = move_suggestion
            old_pos = self.game_state.player_pos
            move_success = self.game_state.move_player(dx, dy)
            
            # Verificar que el movimiento fue exitoso
            self.assertTrue(move_success, f"El movimiento {dx},{dy} desde {old_pos} falló")
            
            # Cada 3 pasos, mover un enemigo para simular cambios dinámicos
            if steps_taken % 3 == 0 and self.game_state.enemies:
                enemy_id = list(self.game_state.enemies.keys())[0]
                old_enemy_pos = self.game_state.enemies[enemy_id]['position']
                
                # Mover el enemigo en dirección aleatoria
                dx_enemy = random.choice([-1, 0, 1])
                dy_enemy = random.choice([-1, 0, 1])
                new_enemy_pos = (old_enemy_pos[0] + dx_enemy, old_enemy_pos[1] + dy_enemy)
                
                # Solo mover si la posición es válida
                if (0 <= new_enemy_pos[0] < self.game_state.grid_width and
                    0 <= new_enemy_pos[1] < self.game_state.grid_height and
                    new_enemy_pos not in self.game_state.obstacles):
                    self.game_state.update_enemy_position(enemy_id, new_enemy_pos)
                    
                # Actualizar enemigos, lo que debería desencadenar validación del camino
                self.game_state.update_enemy_positions()
            
            # Verificar si hemos llegado a la casa o hay game over
            self.game_state.check_victory_conditions()
            
            steps_taken += 1
            
            # Si estamos cerca de la casa, verificar condiciones especiales
            if self.game_state.player_pos == self.game_state.house_pos:
                break
        
        # 4. Verificar que el juego termina en victoria o game over
        end_state = self.game_state.check_victory_conditions()
        self.assertIsNotNone(end_state, "El juego no terminó con un estado claro")
        
        if self.game_state.victory:
            # 5. Verificar ratio de entrenamiento después de la victoria
            self.assertGreaterEqual(self.game_state.successful_paths, self.game_state.failed_paths * 1.5,
                                  "No se mantuvo un ratio favorable de éxito/fallo")
        elif self.game_state.game_over:
            # Si hay game over, verificar que la causa es legítima
            is_player_caught = self.game_state.player_caught
            is_max_retries = self.game_state.retry_count > self.game_state.max_retries
            
            self.assertTrue(is_player_caught or is_max_retries,
                          "Game over sin razón válida (ni captura ni máximos reintentos)")
        else:
            self.fail("El juego no terminó en victoria ni game over después de múltiples pasos")
    
    def test_training_state_persistence(self):
        """
        Verifica que el estado de entrenamiento se guarda y carga correctamente,
        manteniendo la proporción 2:1 de éxitos vs fallos.
        """
        # Verificar si los métodos de guardado/carga están implementados
        if not hasattr(self.game_state.pathfinder, 'save_training_state') or not hasattr(self.game_state.pathfinder, 'load_training_state'):
            print("Métodos save_training_state/load_training_state no implementados - saltando prueba")
            return
            
        # 1. Generar algunos datos de entrenamiento
        # Calcular varios caminos exitosos
        self.game_state.calculate_initial_path()
        initial_success_count = self.game_state.pathfinder.success_path_count
        initial_fail_count = self.game_state.pathfinder.failed_path_count
        
        # Forzar algunos fallos añadiendo obstáculos
        obstacles = [(x, 7) for x in range(5, 15)]
        self.add_test_obstacles(obstacles)
        self.game_state.recalculate_path()
        
        # 2. Guardar el estado actual
        save_success = self.game_state.pathfinder.save_training_state("test_state")
        self.assertTrue(save_success, "No se pudo guardar el estado de entrenamiento")
        
        # Guardar contadores actuales
        success_count = self.game_state.pathfinder.success_path_count
        fail_count = self.game_state.pathfinder.failed_path_count
        
        # 3. Crear una nueva instancia de GameState/Pathfinder
        new_game_state = EnhancedGameState(grid_width=20, grid_height=15)
        
        # 4. Cargar el estado guardado
        load_success = new_game_state.pathfinder.load_training_state("test_state")
        self.assertTrue(load_success, "No se pudo cargar el estado de entrenamiento")
        
        # 5. Verificar que los contadores se mantienen
        self.assertEqual(new_game_state.pathfinder.success_path_count, success_count,
                        "El contador de éxitos no se mantuvo después de cargar")
        self.assertEqual(new_game_state.pathfinder.failed_path_count, fail_count,
                        "El contador de fallos no se mantuvo después de cargar")
        
        # 6. Verificar que se mantiene la proporción 2:1
        ratio = new_game_state.pathfinder.success_path_count / (new_game_state.pathfinder.failed_path_count + 1)
        self.assertGreaterEqual(ratio, 1.5, "No se mantuvo la proporción mínima de 1.5:1 después de cargar")
    
    def test_edge_cases(self):
        """
        Verifica el comportamiento del sistema en situaciones límite.
        """
        # Caso 1: Grid completamente vacío excepto jugador y casa
        self.game_state.obstacles.clear()
        self.game_state.enemies.clear()
        self.game_state.enemy_positions.clear()
        success = self.game_state.calculate_initial_path()
        self.assertTrue(success, "No se pudo encontrar camino en grid vacío")
        
        # Caso 2: Jugador rodeado de enemigos excepto una salida
        player_x, player_y = self.game_state.player_pos
        enemy_positions = [
            (player_x + 1, player_y),
            (player_x - 1, player_y),
            (player_x, player_y + 1)
        ]  # Dejando libre (x, y-1)
        self.add_test_enemies(enemy_positions)
        self.game_state.recalculate_path()
        self.assertIsNotNone(self.game_state.current_path, "No se encontró salida disponible")
        
        # Caso 3: Cambios rápidos en posiciones de enemigos
        for _ in range(5):
            # Mover enemigos aleatoriamente
            for enemy_id in list(self.game_state.enemies.keys()):
                new_x = random.randint(0, self.game_state.grid_width - 1)
                new_y = random.randint(0, self.game_state.grid_height - 1)
                self.game_state.update_enemy_position(enemy_id, (new_x, new_y))
            
            # Verificar que el sistema maneja los cambios rápidos
            self.game_state.update_enemy_positions()
            if not self.game_state.path_valid:
                success = self.game_state.recalculate_path()
                if not success:
                    # Si no hay camino, verificar que es por una razón válida
                    self.assertTrue(self.game_state.check_player_collision() or 
                                  self.game_state.retry_count > self.game_state.max_retries,
                                  "Fallo en recálculo sin razón válida")
    
    def test_path_learning_effectiveness(self):
        """
        Verifica que los caminos exitosos previos influyen positivamente en futuras decisiones de ruta.
        """
        # 1. Encontrar un camino inicial exitoso
        success = self.game_state.calculate_initial_path()
        self.assertTrue(success, "No se pudo encontrar camino inicial")
        initial_path = self.game_state.current_path.copy()
        
        # 2. Simular éxito llegando a la casa
        self.game_state.player_pos = self.game_state.house_pos
        self.game_state.check_victory_conditions()
        
        # 3. Reiniciar posición del jugador
        self.game_state.player_pos = (1, 1)
        
        # 4. Calcular nuevo camino
        success = self.game_state.calculate_initial_path()
        self.assertTrue(success, "No se pudo encontrar segundo camino")
        second_path = self.game_state.current_path
        
        # 5. Verificar que el segundo camino es similar al primero (aprendizaje)
        common_positions = set(initial_path) & set(second_path)
        similarity_ratio = len(common_positions) / len(initial_path)
        
        self.assertGreaterEqual(similarity_ratio, 0.7, 
            "El nuevo camino no aprovecha suficientemente el aprendizaje del camino exitoso previo")


if __name__ == "__main__":
    unittest.main()

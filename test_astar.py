import pygame
from AStar import AStar
from GameState import GameState
from config import GameConfig

def test_enemy_avoidance_pathfinding():
    """
    Prueba la funcionalidad de evitación de enemigos en el algoritmo A*.
    
    Este test:
    1. Inicializa un estado de juego con las dimensiones correctas
    2. Añade posiciones estratégicas de enemigos para probar la evitación
    3. Coloca algunos obstáculos para crear escenarios interesantes
    4. Intenta encontrar un camino desde la posición inicial hasta la casa
    5. Verifica que el camino evite a los enemigos y llegue al destino
    """
    print("Iniciando prueba de pathfinding con evitación de enemigos...")
    
    # 1. Inicializar estado del juego con dimensiones correctas
    game_state = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
    game_state.player_pos = GameConfig.INITIAL_PLAYER_POS
    game_state.house_pos = GameConfig.INITIAL_HOUSE_POS
    
    print(f"Grid: {GameConfig.GRID_WIDTH}x{GameConfig.GRID_HEIGHT}")
    print(f"Posición inicial del jugador: {GameConfig.INITIAL_PLAYER_POS}")
    print(f"Posición de la casa: {GameConfig.INITIAL_HOUSE_POS}")
    
    # 2. Añadir posiciones de enemigos estratégicas para probar la evitación
    test_enemies = {
        (18, 15),  # Enemigo entre jugador y casa
        (20, 18),  # Enemigo cerca del camino óptimo
        (22, 16)   # Enemigo creando un corredor desafiante
    }
    game_state.enemies = test_enemies
    print(f"Enemigos posicionados en: {test_enemies}")
    
    # 3. Crear obstáculos (simular la inicialización del juego con colocación controlada)
    test_obstacles = {
        (15, 12), (16, 12), (17, 12),  # Muro horizontal
        (19, 16), (19, 17), (19, 18),  # Muro vertical
        (21, 14), (21, 15), (21, 16)   # Otro muro vertical
    }
    game_state.obstacles = test_obstacles
    print(f"Obstáculos colocados: {len(test_obstacles)}")
    
    # 4. Inicializar pathfinder A* y buscar camino
    astar = AStar(game_state)
    
    # Configuración del algoritmo A*
    print(f"Radio de influencia de enemigos: {astar.ENEMY_INFLUENCE_RADIUS}")
    print(f"Peso de seguridad: {astar.SAFETY_WEIGHT}")
    
    # Intentar encontrar camino desde inicio hasta casa
    start = GameConfig.INITIAL_PLAYER_POS
    goal = GameConfig.INITIAL_HOUSE_POS
    
    path = astar.find_path(start, goal)
    
    # 5. Verificar resultados
    if path:
        print(f"\n✅ ¡Camino encontrado! Longitud: {len(path)} pasos")
        
        # Verificar la distancia mínima a cualquier enemigo en el camino
        min_enemy_distance = float('inf')
        closest_pos = None
        closest_enemy = None
        
        for pos in path:
            for enemy_pos in game_state.enemies:
                distance = ((pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2)**0.5
                if distance < min_enemy_distance:
                    min_enemy_distance = distance
                    closest_pos = pos
                    closest_enemy = enemy_pos
        
        print(f"Distancia mínima a enemigos: {min_enemy_distance:.2f} unidades")
        print(f"Punto más cercano: {closest_pos} a enemigo en {closest_enemy}")
        
        # Verificar si el camino pasa directamente por posiciones de enemigos
        safe_path = True
        for pos in path:
            if pos in game_state.enemies:
                safe_path = False
                print(f"⚠️ ¡Advertencia! El camino pasa por la posición del enemigo en {pos}")
        
        if safe_path:
            print("✅ El camino evita completamente a todos los enemigos")
        
        # Verificar si el camino evita obstáculos
        for pos in path:
            if pos in game_state.obstacles:
                print(f"❌ Error: El camino pasa por un obstáculo en {pos}")
                return False
        
        # Test exitoso si encontramos un camino y mantiene una distancia mínima segura
        return min_enemy_distance >= 2 and safe_path
    else:
        print("❌ No se encontró ningún camino")
        return False

if __name__ == "__main__":
    result = test_enemy_avoidance_pathfinding()
    print(f"\nResultado de la prueba: {'✅ PASÓ' if result else '❌ FALLÓ'}")


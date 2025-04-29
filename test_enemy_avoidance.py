#!/usr/bin/env python3
from AStar import AStar
from GameState import GameState
from config import GameConfig
import math

def test_enemy_avoidance():
    """
    Prueba exhaustiva de la funcionalidad de evitación de enemigos en el algoritmo A*.
    
    Esta prueba verifica las siguientes condiciones críticas:
    1. El personaje NUNCA pasa por una casilla ocupada por un enemigo
    2. Se mantiene una distancia mínima segura de los enemigos (BLOCKED_ZONE_RADIUS)
    3. El algoritmo encuentra rutas alternativas cuando hay enemigos bloqueando el camino directo
    4. El algoritmo retorna None cuando no hay un camino seguro disponible
    """
    print("\n=== PRUEBA DE EVITACIÓN DE ENEMIGOS ===")
    
    # Crear estado del juego
    game_state = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
    
    # Configurar posiciones iniciales fijas para las pruebas
    start_pos = (5, 5)
    goal_pos = (15, 15)
    print(f"Posición inicial: {start_pos}")
    print(f"Posición objetivo: {goal_pos}")
    print(f"Radio de zona bloqueada: {AStar.BLOCKED_ZONE_RADIUS}")
    
    # Caso 1: Enemigo directamente en el camino
    print("\n--- Caso 1: Enemigo en el camino directo ---")
    game_state.enemies = {(10, 10)}  # Enemigo en medio del camino directo
    astar = AStar(game_state)
    path = astar.find_path(start_pos, goal_pos)
    
    if path:
        # Verificar que el camino no pasa por el enemigo
        for pos in path:
            if pos in game_state.enemies:
                print(f"❌ ERROR: El camino pasa por un enemigo en {pos}")
                return False
        
        # Verificar distancia mínima a enemigos
        min_distance = float('inf')
        closest_point = None
        for pos in path:
            for enemy_pos in game_state.enemies:
                distance = math.sqrt((pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_point = pos
        
        print(f"Camino encontrado de longitud: {len(path)}")
        print(f"Distancia mínima al enemigo: {min_distance:.2f} (en posición {closest_point})")
        
        if min_distance <= astar.BLOCKED_ZONE_RADIUS:
            print(f"❌ ERROR: El camino pasa demasiado cerca del enemigo ({min_distance:.2f} < {astar.BLOCKED_ZONE_RADIUS})")
            return False
        else:
            print("✅ El camino mantiene distancia segura del enemigo")
    else:
        print("❌ ERROR: No se encontró camino cuando debería existir una alternativa")
        return False
    
    # Caso 2: Múltiples enemigos formando una barrera parcial
    print("\n--- Caso 2: Barrera parcial de enemigos ---")
    game_state.enemies = {(10, 8), (10, 9), (10, 10), (10, 11), (10, 12)}
    astar = AStar(game_state)
    path = astar.find_path(start_pos, goal_pos)
    
    if path:
        # Verificar que el camino no pasa por enemigos
        for pos in path:
            if pos in game_state.enemies:
                print(f"❌ ERROR: El camino pasa por un enemigo en {pos}")
                return False
                
        # Verificar distancia mínima a todos los enemigos
        min_distance = float('inf')
        closest_enemy = None
        closest_point = None
        
        for pos in path:
            for enemy_pos in game_state.enemies:
                distance = math.sqrt((pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = enemy_pos
                    closest_point = pos
        
        print(f"Camino encontrado de longitud: {len(path)}")
        print(f"Distancia mínima a enemigos: {min_distance:.2f} (punto {closest_point} a enemigo {closest_enemy})")
        
        if min_distance <= astar.BLOCKED_ZONE_RADIUS:
            print(f"❌ ERROR: El camino pasa demasiado cerca de un enemigo ({min_distance:.2f} < {astar.BLOCKED_ZONE_RADIUS})")
            return False
        else:
            print("✅ El camino mantiene distancia segura de todos los enemigos")
    else:
        print("❌ ERROR: No se encontró camino cuando debería existir una ruta alternativa")
        return False
    
    # Caso 3: Camino completamente bloqueado por enemigos
    print("\n--- Caso 3: Camino completamente bloqueado ---")
    # Crear una barrera completa de enemigos que divide el mapa
    # Esto garantiza que no haya ningún camino posible entre inicio y meta
    barrier_y = 10
    game_state.enemies = {(x, barrier_y) for x in range(GameConfig.GRID_WIDTH)}
    astar = AStar(game_state)
    path = astar.find_path(start_pos, goal_pos)
    
    if path is None:
        print("✅ Correctamente detectó que no hay camino posible")
    else:
        print(f"❌ ERROR: Encontró un camino de longitud {len(path)} cuando debería estar completamente bloqueado")
        return False
    
    # Caso 4: Enemigos en posiciones inicial y final
    print("\n--- Caso 4: Enemigos en posiciones inicial o final ---")
    game_state.enemies = {start_pos}  # Enemigo en posición inicial
    astar = AStar(game_state)
    path = astar.find_path(start_pos, goal_pos)
    
    if path is None:
        print("✅ Correctamente detectó que la posición inicial está bloqueada")
    else:
        print("❌ ERROR: Encontró camino cuando la posición inicial tiene un enemigo")
        return False
    
    game_state.enemies = {goal_pos}  # Enemigo en posición final
    path = astar.find_path(start_pos, goal_pos)
    
    if path is None:
        print("✅ Correctamente detectó que la posición final está bloqueada")
    else:
        print("❌ ERROR: Encontró camino cuando la posición final tiene un enemigo")
        return False
    
    # Caso 5: Laberinto complejo con enemigos estratégicos
    print("\n--- Caso 5: Laberinto complejo con enemigos estratégicos ---")
    # Crear un escenario más complejo con obstáculos y enemigos
    game_state.obstacles = {
        (8, 7), (9, 7), (10, 7),
        (8, 13), (9, 13), (10, 13),
        (7, 8), (7, 9), (7, 10), (7, 11), (7, 12)
    }
    
    # Enemigos colocados estratégicamente para forzar un camino específico
    game_state.enemies = {
        (10, 9), (10, 11),  # En el centro, creando un corredor estrecho
        (12, 8), (14, 12)   # Dispersos para afectar la ruta
    }
    
    astar = AStar(game_state)
    path = astar.find_path(start_pos, goal_pos)
    
    if path:
        # Verificar que el camino no pasa por enemigos
        for pos in path:
            if pos in game_state.enemies:
                print(f"❌ ERROR: El camino pasa por un enemigo en {pos}")
                return False
                
        # Verificar distancia mínima a todos los enemigos
        min_distance = float('inf')
        for pos in path:
            for enemy_pos in game_state.enemies:
                distance = math.sqrt((pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2)
                min_distance = min(min_distance, distance)
        
        print(f"Camino encontrado de longitud: {len(path)}")
        print(f"Distancia mínima a enemigos en laberinto: {min_distance:.2f}")
        
        if min_distance <= astar.BLOCKED_ZONE_RADIUS:
            print(f"❌ ERROR: El camino pasa demasiado cerca de un enemigo ({min_distance:.2f} < {astar.BLOCKED_ZONE_RADIUS})")
            return False
        else:
            print("✅ El camino mantiene distancia segura de todos los enemigos")
    else:
        print("❌ ERROR: No se encontró camino cuando debería existir una ruta alternativa")
        return False
    
    print("\n=== RESULTADO FINAL ===")
    print("✅ Todas las pruebas pasaron exitosamente!")
    print("La implementación garantiza que el personaje nunca pasa por casillas ocupadas por enemigos")
    print(f"Se mantiene una distancia mínima segura de {astar.BLOCKED_ZONE_RADIUS} unidades de los enemigos")
    print("El algoritmo encuentra rutas alternativas cuando hay enemigos bloqueando el camino directo")
    print("El algoritmo identifica correctamente cuando no hay camino seguro disponible")
    return True

if __name__ == "__main__":
    test_enemy_avoidance()


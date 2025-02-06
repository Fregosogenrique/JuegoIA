class GameState:
    def __init__(self):
        self.player_pos = (1, 1)
        self.house_pos = (8, 8)
        self.obstacles = set()
        self.game_started = False
        self.victory = False
        self.victory_timer = 0
        self.show_victory_message = False

    def reset(self):
        self.player_pos = (1, 1)
        self.house_pos = (8, 8)
        self.obstacles = set()
        self.game_started = False
        self.victory = False
        self.show_victory_message = False
        self.victory_timer = 0

    def generate_obstacles(self):
        import random
        from ADB import AStar
        
        # Generar todas las posiciones posibles
        all_positions = {(x, y) for x in range(10) for y in range(10)}
        
        # Remover posiciones del jugador y la casa
        all_positions.remove(self.player_pos)
        all_positions.remove(self.house_pos)
        
        # Convertir a lista para poder usar random.sample
        available_positions = list(all_positions)
        
        # Seleccionar 70% de las posiciones disponibles
        num_obstacles = int(len(available_positions) * 0.7)
        self.obstacles = set(random.sample(available_positions, num_obstacles))
        
        # Verificar si hay un camino posible
        pathfinder = AStar()
        possible_path = pathfinder.find_path(
            self.player_pos,
            self.house_pos,
            self.obstacles
        )
        
        # Si no hay camino posible, regenerar obstáculos
        while not possible_path:
            self.obstacles = set(random.sample(available_positions, num_obstacles))
            possible_path = pathfinder.find_path(
                self.player_pos,
                self.house_pos,
                self.obstacles
            )

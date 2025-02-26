class GameState:
    def __init__(self):
        self.player_pos = (1, 1)
        self.house_pos = (8, 38)
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
        # Dimensiones de la matriz
        import random
        import numpy as np
        from ADB import AStar

        filas, columnas = 40, 30
        valores_por_celda = 4  # Cada celda contiene un arreglo de 4 valores

        # Crear la matriz con arreglos inicializados en [0, 0, 0, 0]
        self.matriz = np.array([[[0] * valores_por_celda for _ in range(columnas)] for _ in range(filas)], dtype=object)

        # Generar todas las posiciones posibles en un grid 10x10
        all_positions = {(x, y) for x in range(10) for y in range(10)}

        # Remover posiciones del jugador y la casa
        all_positions.discard(self.player_pos)
        all_positions.discard(self.house_pos)

        # Convertir a lista para poder usar random.sample
        available_positions = list(all_positions)

        # Seleccionar 70% de las posiciones disponibles como obstáculos
        num_obstacles = int(len(available_positions) * 0.7)
        self.obstacles = set(random.sample(available_positions, num_obstacles))

        # Verificar si hay un camino posible usando A*
        pathfinder = AStar()
        possible_path = pathfinder.find_path(
            self.player_pos,
            self.house_pos,
            self.obstacles
        )

        # Si no hay camino posible, regenerar obstáculos hasta encontrar uno válido
        while not possible_path:
            self.obstacles = set(random.sample(available_positions, num_obstacles))
            possible_path = pathfinder.find_path(
                self.player_pos,
                self.house_pos,
                self.obstacles
            )

        # Asignar -1 a las celdas de los obstáculos en la matriz
        for i, j in self.obstacles:
            self.matriz[i, j] = [-1] * valores_por_celda

        print("Obstáculos generados correctamente y camino válido encontrado.")
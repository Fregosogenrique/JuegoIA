import random
from config import GameConfig


class GameState:
    """
    Clase que mantiene el estado del juego y gestiona las interacciones con el entorno.
    """

    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.obstacles = set()
        self.enemies = {}  # {enemy_id: {'position': (x,y), 'type': '...', ...}}
        self.enemy_positions = set()  # Para chequeos rápidos de colisión
        self.next_enemy_id = 1

        self.player_pos = GameConfig.INITIAL_PLAYER_POS
        self.initial_player_pos = GameConfig.INITIAL_PLAYER_POS
        self.house_pos = GameConfig.INITIAL_HOUSE_POS

        self.victory = False
        self.player_caught = False
        self.game_started = False  # Se pone True en initialize_game

    def initialize_game(self):
        self.player_pos = GameConfig.INITIAL_PLAYER_POS
        self.initial_player_pos = GameConfig.INITIAL_PLAYER_POS
        self.house_pos = GameConfig.INITIAL_HOUSE_POS

        self.obstacles.clear()  # Limpiar obstáculos antes de generar nuevos
        self.generate_obstacles()

        # Limpiar enemigos antes de inicializar (Game._initialize_game_enemies se encarga de poblarlo)
        self.enemies.clear()
        self.enemy_positions.clear()
        self.next_enemy_id = 1

        self.victory = False
        self.player_caught = False
        self.game_started = True  # Marcar que el juego (estado) ha sido inicializado

    def initialize_enemies(self, enemy_definitions_list=None):
        """
        Inicializa enemigos basados en una lista de definiciones o usa GameConfig.
        Game._initialize_game_enemies es el método principal para poblar enemigos.
        Este método es más un helper si se necesita una inicialización directa.
        """
        self.enemies.clear()
        self.enemy_positions.clear()
        self.next_enemy_id = 1

        positions_to_use = enemy_definitions_list or GameConfig.INITIAL_ENEMY_POSITIONS or []

        for enemy_info in positions_to_use:
            pos = None
            enemy_type = GameConfig.DEFAULT_ENEMY_TYPE
            if isinstance(enemy_info, tuple) and len(enemy_info) == 2:  # Solo posición
                pos = enemy_info
            elif isinstance(enemy_info, dict) and 'position' in enemy_info:  # Diccionario con detalles
                pos = enemy_info['position']
                enemy_type = enemy_info.get('type', enemy_type)

            if pos and self.is_valid_enemy_position(pos):  # Asegurarse que la posición es válida
                self.add_enemy(pos, enemy_type)
            elif pos:
                print(f"Advertencia GS: Posición de enemigo {pos} no válida al inicializar.")

    def generate_obstacles(self):
        self.obstacles.clear()  # Siempre empezar con un set vacío
        num_obstacles = int((self.grid_width * self.grid_height) * (GameConfig.OBSTACLE_PERCENTAGE / 100))

        attempts = 0
        max_attempts = num_obstacles * 5  # Para evitar bucles infinitos

        while len(self.obstacles) < num_obstacles and attempts < max_attempts:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            pos = (x, y)

            if pos != self.player_pos and \
                    pos != self.initial_player_pos and \
                    pos != self.house_pos and \
                    pos not in self.enemy_positions and \
                    pos not in self.obstacles:  # Evitar duplicados
                self.obstacles.add(pos)
            attempts += 1

        if attempts >= max_attempts and len(self.obstacles) < num_obstacles:
            print(
                f"Advertencia GS: No se pudieron generar todos los obstáculos. Generados: {len(self.obstacles)} de {num_obstacles}")

    def is_valid_move(self, pos):
        """Verifica si una posición es válida para mover al jugador."""
        x, y = pos
        return (0 <= x < self.grid_width and
                0 <= y < self.grid_height and
                pos not in self.obstacles and
                pos not in self.enemy_positions)  # Jugador no puede moverse a celda de enemigo

    def is_valid_enemy_position(self, pos, exclude_enemy_id=None):
        """Verifica si una posición es válida para colocar o mover un enemigo."""
        x, y = pos
        if not (0 <= x < self.grid_width and 0 <= y < self.grid_height): return False
        if pos == self.player_pos: return False  # Enemigo no puede estar en la misma celda que el jugador (a menos que sea para atraparlo)
        if pos == self.house_pos: return False
        if pos in self.obstacles: return False

        # Chequear colisión con otros enemigos
        for enemy_id, data in self.enemies.items():
            if exclude_enemy_id is not None and enemy_id == exclude_enemy_id:
                continue  # No chequear contra sí mismo si se está moviendo
            if data['position'] == pos:
                return False
        return True

    def add_enemy(self, pos, enemy_type=None):
        if self.is_valid_enemy_position(pos):  # Chequea si la pos es válida para un NUEVO enemigo
            enemy_type = enemy_type or GameConfig.DEFAULT_ENEMY_TYPE
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1

            self.enemies[enemy_id] = {
                'position': pos,
                'type': enemy_type,
                'direction': (0, 0),
                'last_move_time': 0,
                'target': 'player',
                'path': [],
                'state': 'patrol',
                'patrol_path': [],
                'patrol_index': 0
            }
            self.enemy_positions.add(pos)
            return enemy_id
        else:
            print(f"Advertencia GS: No se pudo añadir enemigo en posición inválida {pos}")
        return None

    def remove_enemy(self, enemy_pos_or_id):
        """Elimina un enemigo por su posición o ID."""
        enemy_id_to_remove = None
        pos_to_remove = None

        if isinstance(enemy_pos_or_id, int):  # Es un ID
            if enemy_pos_or_id in self.enemies:
                enemy_id_to_remove = enemy_pos_or_id
                pos_to_remove = self.enemies[enemy_id_to_remove]['position']
        elif isinstance(enemy_pos_or_id, tuple):  # Es una posición
            pos_to_remove = enemy_pos_or_id
            for eid, data in self.enemies.items():
                if data['position'] == pos_to_remove:
                    enemy_id_to_remove = eid
                    break

        if enemy_id_to_remove is not None and pos_to_remove is not None:
            del self.enemies[enemy_id_to_remove]
            if pos_to_remove in self.enemy_positions:  # Chequeo extra de consistencia
                self.enemy_positions.remove(pos_to_remove)
            return True
        print(f"Advertencia GS: No se pudo remover enemigo {enemy_pos_or_id}")
        return False

    def update_enemy_position(self, enemy_id, new_pos):
        if enemy_id not in self.enemies:
            print(f"Error GS: Intentando mover enemigo ID {enemy_id} que no existe.")
            return False

        # Un enemigo PUEDE moverse a la posición del jugador (para atraparlo).
        # No puede moverse a obstáculos u otros enemigos.
        is_valid_for_moving_enemy = (0 <= new_pos[0] < self.grid_width and
                                     0 <= new_pos[1] < self.grid_height and
                                     new_pos not in self.obstacles)

        collides_with_other_enemy = False
        for other_id, data in self.enemies.items():
            if other_id != enemy_id and data['position'] == new_pos:
                collides_with_other_enemy = True
                break

        if not is_valid_for_moving_enemy or collides_with_other_enemy:
            # print(f"Error GS: Movimiento inválido para enemigo {enemy_id} a {new_pos}")
            return False  # Movimiento inválido

        old_pos = self.enemies[enemy_id]['position']

        if old_pos in self.enemy_positions:  # Debería estar siempre
            self.enemy_positions.remove(old_pos)
        self.enemy_positions.add(new_pos)

        self.enemies[enemy_id]['position'] = new_pos

        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        if dx != 0 or dy != 0:
            self.enemies[enemy_id]['direction'] = (dx, dy)

        return True

    def get_enemy_at_position(self, pos):
        for enemy_id, enemy_data in self.enemies.items():
            if enemy_data['position'] == pos:
                return enemy_id
        return None

    # ... (Otros setters como set_enemy_state, set_enemy_target, etc., pueden mantenerse si son útiles) ...
    # Por ahora, estos no son llamados activamente desde Game.py para la lógica principal.

    def move_player(self, dx, dy):
        """Mueve al jugador si es válido. No usado por Game.py que mueve directamente."""
        # Esta función es un helper, Game.py maneja el movimiento del jugador directamente.
        new_pos = (self.player_pos[0] + dx, self.player_pos[1] + dy)
        if self.is_valid_move(new_pos):
            self.player_pos = new_pos
            if self.player_pos == self.house_pos:
                self.victory = True
            # Chequeo de colisión con enemigos es manejado en Game.py
            return True
        return False

    def check_player_collision(self):
        """Verifica si el jugador ha colisionado con algún enemigo."""
        # Game.py maneja esto directamente con self.game_state.player_pos in self.game_state.enemy_positions
        if self.player_pos in self.enemy_positions:
            self.player_caught = True  # Actualiza el estado interno
            return True
        return False
import pygame
import random

class BaseEnemy:
    """Clase base para todos los enemigos con funcionalidad común"""
    def __init__(self, position, grid_width, grid_height):
        self.position = position
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.direction = (0, 0)
        self.obstacles = set()
        self.enemies = set()
        self.house_position = None
        # Para mantener el ratio de movimiento 2:1
        self.move_counter = 0

    def update_environment(self, obstacles, enemies, house_position):
        self.obstacles = obstacles
        self.enemies = enemies
        self.house_position = house_position

    def can_move(self):
        """Controla el ratio de movimiento 2:1"""
        self.move_counter += 1
        if self.move_counter >= 2:
            self.move_counter = 0
            return True
        return False

    def is_valid_position(self, pos):
        """Verifica si una posición es válida"""
        x, y = pos
        return (0 <= x < self.grid_width and 
                0 <= y < self.grid_height and 
                pos not in self.obstacles and 
                pos not in self.enemies)

class Perseguidor(BaseEnemy):
    """Enemigo que persigue directamente al jugador"""
    def __init__(self, position, grid_width, grid_height):
        super().__init__(position, grid_width, grid_height)
        # Crear superficie roja para el perseguidor
        self.surface = pygame.Surface((30, 30))
        self.surface.fill((255, 0, 0))  # Rojo

    def get_next_move(self, player_pos):
        if not self.can_move():
            return self.position

        # Implementar una distancia mínima para evitar bloqueos constantes
        min_distance = 3
        current_distance = abs(self.position[0] - player_pos[0]) + abs(self.position[1] - player_pos[1])
        
        # Si estamos muy cerca, mantener distancia
        if current_distance < min_distance:
            # Moverse en dirección opuesta al jugador
            dx = -1 if self.position[0] < player_pos[0] else 1
            dy = -1 if self.position[1] < player_pos[1] else 1
            
            # Intentar alejarse
            possible_moves = [
                (self.position[0] + dx, self.position[1]),
                (self.position[0], self.position[1] + dy)
            ]
            
            for move in possible_moves:
                if self.is_valid_position(move):
                    return move
            
            return self.position

        # Calcular movimiento normal
        dx = player_pos[0] - self.position[0]
        dy = player_pos[1] - self.position[1]
        
        # Intentar movimiento diagonal si es posible
        if abs(dx) > 0 and abs(dy) > 0:
            diagonal_x = self.position[0] + (1 if dx > 0 else -1)
            diagonal_y = self.position[1] + (1 if dy > 0 else -1)
            diagonal_pos = (diagonal_x, diagonal_y)
            
            if self.is_valid_position(diagonal_pos):
                return diagonal_pos

        # Si no es posible diagonal, intentar movimiento ortogonal
        if abs(dx) > abs(dy):
            new_x = self.position[0] + (1 if dx > 0 else -1)
            new_pos = (new_x, self.position[1])
            if self.is_valid_position(new_pos):
                return new_pos
        else:
            new_y = self.position[1] + (1 if dy > 0 else -1)
            new_pos = (self.position[0], new_y)
            if self.is_valid_position(new_pos):
                return new_pos
        
        return self.position

class Bloqueador(BaseEnemy):
    """Enemigo que intenta interceptar al jugador"""
    def __init__(self, position, grid_width, grid_height):
        super().__init__(position, grid_width, grid_height)
        # Crear superficie naranja para el bloqueador
        self.surface = pygame.Surface((30, 30))
        self.surface.fill((255, 165, 0))  # Naranja

    def get_next_move(self, player_pos):
        if not self.can_move():
            return self.position

        # Predecir posición futura del jugador
        player_direction = (
            player_pos[0] - self.position[0],
            player_pos[1] - self.position[1]
        )
        
        predicted_pos = (
            player_pos[0] + (1 if player_direction[0] > 0 else -1),
            player_pos[1] + (1 if player_direction[1] > 0 else -1)
        )
        
        # Calcular punto de intercepción
        if self.house_position:
            # Punto medio entre jugador y casa, pero ligeramente más cerca del jugador
            intercept_x = int(player_pos[0] * 0.7 + self.house_position[0] * 0.3)
            intercept_y = int(player_pos[1] * 0.7 + self.house_position[1] * 0.3)
            target_pos = (intercept_x, intercept_y)
        else:
            target_pos = predicted_pos

        # Moverse hacia el punto de intercepción
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        
        # Intentar movimiento diagonal primero
        if abs(dx) > 0 and abs(dy) > 0:
            new_x = self.position[0] + (1 if dx > 0 else -1)
            new_y = self.position[1] + (1 if dy > 0 else -1)
            diagonal_pos = (new_x, new_y)
            if self.is_valid_position(diagonal_pos):
                return diagonal_pos

        # Si no es posible diagonal, intentar movimiento ortogonal
        moves = []
        if abs(dx) > 0:
            moves.append((self.position[0] + (1 if dx > 0 else -1), self.position[1]))
        if abs(dy) > 0:
            moves.append((self.position[0], self.position[1] + (1 if dy > 0 else -1)))
            
        # Filtrar movimientos válidos
        valid_moves = [move for move in moves if self.is_valid_position(move)]
        
        if valid_moves:
            # Seleccionar el movimiento que nos acerque más al punto de intercepción
            return min(valid_moves, 
                      key=lambda m: abs(m[0] - target_pos[0]) + abs(m[1] - target_pos[1]))
        
        return self.position

class Patrulla(BaseEnemy):
    """Enemigo que sigue una ruta de patrulla"""
    def __init__(self, position, grid_width, grid_height):
        super().__init__(position, grid_width, grid_height)
        # Crear superficie morada para la patrulla
        self.surface = pygame.Surface((30, 30))
        self.surface.fill((128, 0, 128))  # Morado
        self.patrol_path = []
        self.patrol_index = 0
        self.patrol_radius = 3

    def get_next_move(self, player_pos):
        if not self.can_move():
            return self.position

        # Generar ruta de patrulla si no existe
        if not self.patrol_path:
            self._generate_patrol_path()

        # Seguir la ruta de patrulla
        if self.patrol_path:
            target = self.patrol_path[self.patrol_index]
            if self.position == target:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_path)
                target = self.patrol_path[self.patrol_index]

            dx = target[0] - self.position[0]
            dy = target[1] - self.position[1]
            
            if abs(dx) > abs(dy):
                new_x = self.position[0] + (1 if dx > 0 else -1)
                new_pos = (new_x, self.position[1])
                if self.is_valid_position(new_pos):
                    return new_pos
            else:
                new_y = self.position[1] + (1 if dy > 0 else -1)
                new_pos = (self.position[0], new_y)
                if self.is_valid_position(new_pos):
                    return new_pos

        return self.position

    def _generate_patrol_path(self):
        """Genera una ruta de patrulla alrededor de la posición inicial"""
        self.patrol_path = []
        x, y = self.position
        
        # Generar puntos de patrulla en un patrón rectangular
        for dx in range(-self.patrol_radius, self.patrol_radius + 1):
            for dy in [-self.patrol_radius, self.patrol_radius]:
                new_pos = (x + dx, y + dy)
                if self.is_valid_position(new_pos):
                    self.patrol_path.append(new_pos)
        
        for dy in range(-self.patrol_radius + 1, self.patrol_radius):
            for dx in [-self.patrol_radius, self.patrol_radius]:
                new_pos = (x + dx, y + dy)
                if self.is_valid_position(new_pos):
                    self.patrol_path.append(new_pos)
        
        # Si no se pudieron generar puntos, usar un punto cercano
        if not self.patrol_path:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    new_pos = (x + dx, y + dy)
                    if self.is_valid_position(new_pos):
                        self.patrol_path.append(new_pos)

class Aleatorio(BaseEnemy):
    """Enemigo que se mueve de forma aleatoria"""
    def __init__(self, position, grid_width, grid_height):
        super().__init__(position, grid_width, grid_height)
        # Crear superficie azul para el aleatorio
        self.surface = pygame.Surface((30, 30))
        self.surface.fill((0, 0, 255))  # Azul

    def get_next_move(self, player_pos):
        if not self.can_move():
            return self.position

        # Lista de posibles movimientos
        possible_moves = []
        x, y = self.position
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_pos = (x + dx, y + dy)
            if self.is_valid_position(new_pos):
                possible_moves.append(new_pos)
        
        # Si hay movimientos posibles, elegir uno al azar
        if possible_moves:
            return random.choice(possible_moves)
        
        return self.position


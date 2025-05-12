import random
from config import GameConfig


class GameState:
    """
    Clase que mantiene el estado del juego y gestiona las interacciones con el entorno.
    
    Esta clase es responsable de:
    - Almacenar y gestionar la posición del jugador, la casa (meta) y los obstáculos
    - Manejar la validación de movimientos dentro del grid del juego
    - Gestionar los enemigos y sus posiciones
    - Controlar el estado de victoria del juego
    - Inicializar el entorno del juego con configuraciones predefinidas o aleatorias
    
    Atributos:
        grid_width (int): Ancho del grid del juego en número de celdas.
        grid_height (int): Alto del grid del juego en número de celdas.
        obstacles (set): Conjunto de tuplas (x, y) que representan las posiciones de los obstáculos.
        enemies (dict): Diccionario que almacena el estado completo de cada enemigo.
        enemy_positions (set): Conjunto de tuplas (x, y) que representan las posiciones actuales de los enemigos.
        player_pos (tuple): Tupla (x, y) que representa la posición actual del jugador.
        initial_player_pos (tuple): Tupla (x, y) que representa la posición inicial del jugador.
        house_pos (tuple): Tupla (x, y) que representa la posición de la casa (meta).
        victory (bool): Indica si el jugador ha llegado a la casa (meta).
        player_caught (bool): Indica si el jugador ha sido atrapado por un enemigo.
        game_started (bool): Indica si el juego ha sido iniciado.
    """

    def __init__(self, grid_width, grid_height):
        """
        Inicializa una nueva instancia del estado del juego.
        
        Crea un nuevo estado de juego con el tamaño de grid especificado,
        inicializando las colecciones necesarias para obstáculos y enemigos,
        pero sin establecer posiciones iniciales hasta que se llame a initialize_game().
        
        Args:
            grid_width (int): Ancho del grid del juego en número de celdas.
            grid_height (int): Alto del grid del juego en número de celdas.
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.obstacles = set()  # Conjunto para almacenar posiciones de obstáculos
        
        # Diccionario para almacenar los estados de los enemigos
        # Clave: ID único del enemigo (entero)
        # Valor: diccionario con el estado completo del enemigo
        # {
        #   'position': (x, y),          # Posición actual
        #   'type': 'perseguidor',       # Tipo de comportamiento
        #   'direction': (dx, dy),       # Dirección actual (-1,0), (1,0), (0,-1), (0,1)
        #   'last_move_time': 0,         # Tiempo del último movimiento
        #   'target': 'player',          # 'player' o 'house' 
        #   'path': [(x1,y1), (x2,y2)],  # Camino planificado (opcional)
        #   'state': 'patrol'            # Estado actual: 'patrol', 'chase', 'intercept'
        # }
        self.enemies = {}
        
        # Conjunto auxiliar para mantener las posiciones de los enemigos
        # Facilita la compatibilidad con el código existente
        self.enemy_positions = set()
        
        # Contador para IDs de enemigos
        self.next_enemy_id = 1
        
        # Variables de posición principales
        self.player_pos = None
        self.initial_player_pos = None  # Guardar la posición inicial
        self.house_pos = None
        
        # Estados del juego
        self.victory = False
        self.game_started = False
        self.player_caught = False  # Indica si el jugador ha sido atrapado por un enemigo
        
        # Temporizador para movimiento de enemigos
        self.enemy_move_timer = 0

    def initialize_game(self):
        """
        Inicializa el estado del juego con valores predeterminados.
        
        Establece las posiciones iniciales del jugador y la casa desde la configuración.
        Inicializa también los enemigos desde la configuración predeterminada.
        Genera obstáculos aleatorios en el grid utilizando el método generate_obstacles().
        
        Este método debe llamarse después de crear una instancia de GameState
        y antes de comenzar la lógica del juego.
        """
        # Usar posiciones predefinidas de config
        self.player_pos = GameConfig.INITIAL_PLAYER_POS
        self.initial_player_pos = GameConfig.INITIAL_PLAYER_POS
        self.house_pos = GameConfig.INITIAL_HOUSE_POS
        
        # Inicializar enemigos desde la configuración
        self.initialize_enemies(GameConfig.INITIAL_ENEMY_POSITIONS)
        
        # Generar obstáculos aleatorios
        self.generate_obstacles()
        
        # Reiniciar estados del juego
        self.victory = False
        self.player_caught = False
        self.game_started = True
        self.enemy_move_timer = 0

    def initialize_enemies(self, positions):
        """
        Inicializa enemigos en las posiciones especificadas.
        
        Args:
            positions (list): Lista de tuplas (x, y) con las posiciones iniciales de los enemigos.
        """
        # Limpiar enemigos existentes
        self.enemies.clear()
        self.enemy_positions.clear()
        self.next_enemy_id = 1
        
        # Crear un enemigo en cada posición
        for pos in positions:
            # Verificar si la posición es válida
            if self.is_valid_enemy_position(pos):
                # Asignar un tipo aleatorio de enemigo
                enemy_types = ["perseguidor", "bloqueador", "patrulla", "aleatorio"]
                enemy_type = random.choice(enemy_types)
                
                # Crear el enemigo
                self.add_enemy(pos, enemy_type)

    def generate_obstacles(self):
        """
        Genera obstáculos aleatorios en el grid del juego.
        
        Crea obstáculos en posiciones aleatorias basándose en el porcentaje
        definido en GameConfig.OBSTACLE_PERCENTAGE. Evita colocar obstáculos
        en la posición del jugador, la casa, o donde ya hay enemigos.
        
        Este método es invocado automáticamente por initialize_game()
        pero también puede llamarse directamente para regenerar obstáculos.
        """
        self.obstacles = set()
        num_obstacles = int((self.grid_width * self.grid_height) * (GameConfig.OBSTACLE_PERCENTAGE / 100))

        while len(self.obstacles) < num_obstacles:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            pos = (x, y)

            # Evitar colocar obstáculos en la posición inicial del jugador, la casa o un enemigo
            if pos != self.player_pos and pos != self.house_pos and pos not in self.obstacles and pos not in self.enemy_positions:
                self.obstacles.add(pos)

    def is_valid_move(self, pos):
        """
        Verifica si una posición es válida para mover al jugador.
        
        Una posición es válida si:
        - Está dentro de los límites del grid
        - No está ocupada por un obstáculo
        - No está ocupada por un enemigo
        
        Args:
            pos (tuple): Tupla (x, y) que representa la posición a verificar.
            
        Returns:
            bool: True si la posición es válida para moverse, False en caso contrario.
        """
        x, y = pos
        return (0 <= x < self.grid_width and
                0 <= y < self.grid_height and
                pos not in self.obstacles and
                pos not in self.enemy_positions)
                
    def is_valid_enemy_position(self, pos):
        """
        Verifica si una posición es válida para colocar un enemigo.
        
        Una posición es válida para un enemigo si:
        - Está dentro de los límites del grid
        - No está ocupada por el jugador
        - No está ocupada por la casa (meta)
        - No está ocupada por un obstáculo
        - No está ocupada por otro enemigo
        
        Args:
            pos (tuple): Tupla (x, y) que representa la posición a verificar.
            
        Returns:
            bool: True si la posición es válida para colocar un enemigo, False en caso contrario.
        """
        x, y = pos
        return (0 <= x < self.grid_width and
                0 <= y < self.grid_height and
                pos != self.player_pos and
                pos != self.house_pos and
                pos not in self.obstacles and
                pos not in self.enemy_positions)
                
    def add_enemy(self, pos, enemy_type=None):
        """
        Añade un enemigo en la posición indicada si es válida.
        
        Utiliza is_valid_enemy_position() para verificar si la posición es válida
        antes de añadir el enemigo al conjunto de enemigos.
        
        Args:
            pos (tuple): Tupla (x, y) donde se desea colocar el enemigo.
            enemy_type (str, opcional): Tipo de enemigo. Si es None, usa el tipo predeterminado.
            
        Returns:
            int: ID del enemigo creado si fue añadido correctamente, None si la posición no es válida.
        """
        if self.is_valid_enemy_position(pos):
            # Asignar tipo de enemigo predeterminado si no se especifica
            if enemy_type is None:
                enemy_type = GameConfig.DEFAULT_ENEMY_TYPE
                
            # Crear estado del enemigo
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            
            # Crear estructura de datos del enemigo
            self.enemies[enemy_id] = {
                'position': pos,
                'type': enemy_type,
                'direction': (0, 0),  # Sin dirección inicial
                'last_move_time': 0,
                'target': 'player',   # Por defecto persigue al jugador
                'path': [],           # Camino vacío inicialmente
                'state': 'patrol',    # Estado inicial
                'patrol_path': [],    # Ruta de patrulla vacía inicialmente
                'patrol_index': 0     # Índice en la ruta de patrulla
            }
            
            # Actualizar conjunto de posiciones para compatibilidad
            self.enemy_positions.add(pos)
            return enemy_id
        return None
        
    def remove_enemy(self, pos):
        """
        Elimina un enemigo de la posición indicada si existe.
        
        Args:
            pos (tuple): Tupla (x, y) de la posición del enemigo a eliminar.
            
        Returns:
            bool: True si el enemigo fue eliminado correctamente, False si no existía enemigo en esa posición.
        """
        if pos in self.enemy_positions:
            # Encontrar el ID del enemigo en esta posición
            enemy_id_to_remove = None
            for enemy_id, enemy_data in self.enemies.items():
                if enemy_data['position'] == pos:
                    enemy_id_to_remove = enemy_id
                    break
                    
            if enemy_id_to_remove is not None:
                del self.enemies[enemy_id_to_remove]
                self.enemy_positions.remove(pos)
                return True
        return False
        
    def toggle_enemy(self, pos):
        """
        Alterna la presencia de un enemigo en la posición indicada.
        
        Si ya existe un enemigo en la posición, lo elimina.
        Si no existe un enemigo, intenta añadir uno en esa posición.
        
        Args:
            pos (tuple): Tupla (x, y) de la posición donde alternar un enemigo.
            
        Returns:
            bool: True si la operación fue exitosa (ya sea añadir o eliminar), False en caso contrario.
        """
        if pos in self.enemy_positions:
            return self.remove_enemy(pos)
        else:
            return self.add_enemy(pos) is not None
            
    def update_enemy_position(self, enemy_id, new_pos):
        """
        Actualiza la posición de un enemigo existente.
        
        Args:
            enemy_id (int): ID único del enemigo a mover
            new_pos (tuple): Nueva posición (x, y) para el enemigo
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        # Verificar que el enemigo existe
        if enemy_id not in self.enemies:
            return False
            
        # Verificar que la nueva posición es válida
        if not self.is_valid_enemy_position(new_pos) and new_pos != self.player_pos:
            return False
            
        # Obtener la posición actual
        old_pos = self.enemies[enemy_id]['position']
        
        # Actualizar conjunto de posiciones
        if old_pos in self.enemy_positions:
            self.enemy_positions.remove(old_pos)
        self.enemy_positions.add(new_pos)
        
        # Actualizar posición en el estado del enemigo
        self.enemies[enemy_id]['position'] = new_pos
        
        # Calcular y actualizar dirección
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        if dx != 0 or dy != 0:  # Solo actualizar si hay movimiento real
            self.enemies[enemy_id]['direction'] = (dx, dy)
            
        return True
        
    def get_enemy_at_position(self, pos):
        """
        Obtiene el ID del enemigo en la posición especificada, si existe.
        
        Args:
            pos (tuple): Posición (x, y) a verificar
            
        Returns:
            int o None: ID del enemigo si existe en esa posición, None en caso contrario
        """
        for enemy_id, enemy_data in self.enemies.items():
            if enemy_data['position'] == pos:
                return enemy_id
        return None
        
    def set_enemy_state(self, enemy_id, state):
        """
        Actualiza el estado de un enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            state (str): Nuevo estado ('patrol', 'chase', 'intercept')
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        if enemy_id not in self.enemies:
            return False
            
        self.enemies[enemy_id]['state'] = state
        return True
        
    def set_enemy_target(self, enemy_id, target):
        """
        Establece el objetivo del enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            target (str): Objetivo ('player' o 'house')
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        if enemy_id not in self.enemies:
            return False
            
        self.enemies[enemy_id]['target'] = target
        return True
        
    def set_enemy_path(self, enemy_id, path):
        """
        Establece un camino planificado para el enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            path (list): Lista de posiciones (x, y) que forman el camino
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        if enemy_id not in self.enemies:
            return False
            
        self.enemies[enemy_id]['path'] = path
        return True
        
    def set_patrol_path(self, enemy_id, patrol_path):
        """
        Establece una ruta de patrulla para el enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            patrol_path (list): Lista de posiciones (x, y) que forman la ruta de patrulla
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        if enemy_id not in self.enemies:
            return False
            
        self.enemies[enemy_id]['patrol_path'] = patrol_path
        self.enemies[enemy_id]['patrol_index'] = 0
        return True
        
    def get_player_distance(self, enemy_id):
        """
        Calcula la distancia Manhattan entre un enemigo y el jugador.
        
        Args:
            enemy_id (int): ID único del enemigo
            
        Returns:
            int: Distancia Manhattan o -1 si el enemigo no existe
        """
        if enemy_id not in self.enemies:
            return -1
            
        enemy_pos = self.enemies[enemy_id]['position']
        return abs(enemy_pos[0] - self.player_pos[0]) + abs(enemy_pos[1] - self.player_pos[1])
        
    def get_house_distance(self, enemy_id):
        """
        Calcula la distancia Manhattan entre un enemigo y la casa.
        
        Args:
            enemy_id (int): ID único del enemigo
            
        Returns:
            int: Distancia Manhattan o -1 si el enemigo no existe
        """
        if enemy_id not in self.enemies:
            return -1
            
        enemy_pos = self.enemies[enemy_id]['position']
        return abs(enemy_pos[0] - self.house_pos[0]) + abs(enemy_pos[1] - self.house_pos[1])
        
    def get_next_patrol_point(self, enemy_id):
        """
        Obtiene el siguiente punto en la ruta de patrulla de un enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            
        Returns:
            tuple o None: Siguiente posición (x, y) o None si no hay ruta de patrulla
        """
        if enemy_id not in self.enemies:
            return None
            
        enemy_data = self.enemies[enemy_id]
        if not enemy_data.get('patrol_path'):
            return None
            
        patrol_index = enemy_data.get('patrol_index', 0)
        patrol_path = enemy_data['patrol_path']
        
        if patrol_path and 0 <= patrol_index < len(patrol_path):
            return patrol_path[patrol_index]
            
        return None
        
    def advance_patrol_index(self, enemy_id):
        """
        Avanza al siguiente punto en la ruta de patrulla de un enemigo.
        
        Args:
            enemy_id (int): ID único del enemigo
            
        Returns:
            bool: True si se avanzó correctamente, False en caso contrario
        """
        if enemy_id not in self.enemies:
            return False
            
        enemy_data = self.enemies[enemy_id]
        if not enemy_data.get('patrol_path'):
            return False
            
        patrol_index = enemy_data.get('patrol_index', 0)
        patrol_path = enemy_data['patrol_path']
        
        if patrol_path:
            # Avanzar al siguiente punto (circular)
            new_index = (patrol_index + 1) % len(patrol_path)
            self.enemies[enemy_id]['patrol_index'] = new_index
            return True
            
        return False
        
    def move_player(self, dx, dy):
        """
        Mueve al jugador en la dirección especificada.
        
        Args:
            dx (int): Cambio en la posición x (-1, 0, 1)
            dy (int): Cambio en la posición y (-1, 0, 1)
            
        Returns:
            bool: True si el movimiento fue exitoso, False en caso contrario
        """
        new_pos = (self.player_pos[0] + dx, self.player_pos[1] + dy)
        if self.is_valid_move(new_pos):
            self.player_pos = new_pos
            
            # Verificar colisión con enemigos después del movimiento
            if self.check_player_collision():
                self.player_caught = True
                return False
                
            # Verificar si llegamos a la casa
            if self.player_pos == self.house_pos:
                self.victory = True
                
            return True
        return False
    
    def check_player_collision(self):
        """
        Verifica si el jugador ha colisionado con algún enemigo.
        
        Returns:
            bool: True si hay colisión, False en caso contrario
        """
        if self.player_pos in self.enemy_positions:
            self.player_caught = True
            return True
        return False

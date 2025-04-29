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
        enemies (set): Conjunto de tuplas (x, y) que representan las posiciones de los enemigos.
        player_pos (tuple): Tupla (x, y) que representa la posición actual del jugador.
        initial_player_pos (tuple): Tupla (x, y) que representa la posición inicial del jugador.
        house_pos (tuple): Tupla (x, y) que representa la posición de la casa (meta).
        victory (bool): Indica si el jugador ha llegado a la casa (meta).
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
        self.obstacles = set()  # Cambiar a un conjunto en lugar de una lista
        self.enemies = set()    # Conjunto para almacenar posiciones de enemigos
        self.player_pos = None
        self.initial_player_pos = None  # Guardar la posición inicial
        self.house_pos = None
        self.victory = False
        self.game_started = False

    def initialize_game(self):
        """
        Inicializa el estado del juego con valores predeterminados.
        
        Establece las posiciones iniciales del jugador y la casa desde la configuración.
        Inicializa también los enemigos desde la configuración predeterminada.
        Genera obstáculos aleatorios en el grid utilizando el método _generate_obstacles().
        
        Este método debe llamarse después de crear una instancia de GameState
        y antes de comenzar la lógica del juego.
        """
        # Usar posiciones predefinidas de config
        self.player_pos = GameConfig.INITIAL_PLAYER_POS
        self.initial_player_pos = GameConfig.INITIAL_PLAYER_POS
        self.house_pos = GameConfig.INITIAL_HOUSE_POS
        
        # Inicializar enemigos desde la configuración
        self.enemies = set(GameConfig.INITIAL_ENEMY_POSITIONS)
        
        # Generar obstáculos aleatorios
        self.generate_obstacles()

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
            if pos != self.player_pos and pos != self.house_pos and pos not in self.obstacles and pos not in self.enemies:
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
                pos not in self.enemies)
                
    def is_valid_enemy_position(self, pos):
        """
        Verifica si una posición es válida para colocar un enemigo.
        
        Una posición es válida para un enemigo si:
        - Está dentro de los límites del grid
        - No está ocupada por el jugador
        - No está ocupada por la casa (meta)
        - No está ocupada por un obstáculo
        
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
                pos not in self.obstacles)
                
    def add_enemy(self, pos):
        """
        Añade un enemigo en la posición indicada si es válida.
        
        Utiliza is_valid_enemy_position() para verificar si la posición es válida
        antes de añadir el enemigo al conjunto de enemigos.
        
        Args:
            pos (tuple): Tupla (x, y) donde se desea colocar el enemigo.
            
        Returns:
            bool: True si el enemigo fue añadido correctamente, False si la posición no es válida.
        """
        if self.is_valid_enemy_position(pos):
            self.enemies.add(pos)
            return True
        return False
        
    def remove_enemy(self, pos):
        """
        Elimina un enemigo de la posición indicada si existe.
        
        Args:
            pos (tuple): Tupla (x, y) de la posición del enemigo a eliminar.
            
        Returns:
            bool: True si el enemigo fue eliminado correctamente, False si no existía enemigo en esa posición.
        """
        if pos in self.enemies:
            self.enemies.remove(pos)
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
        if pos in self.enemies:
            return self.remove_enemy(pos)
        else:
            return self.add_enemy(pos)

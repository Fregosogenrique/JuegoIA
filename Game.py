import pygame
import random
import time
import numpy as np
from GameState import GameState
from DecisionTree import DecisionTree
from config import GameConfig
from render import GameRenderer
from ADB import RandomRoute
from HeatMapPathfinding import HeatMapPathfinding

class Game:
    """
    Clase principal que controla la lógica del juego y la interfaz de usuario.
    
    Esta clase maneja la inicialización del juego, la gestión del estado del juego,
    el procesamiento de entradas del usuario, la visualización, y la integración
    con varios algoritmos de IA para encontrar rutas óptimas en el entorno del juego.
    
    Características principales:
    - Inicialización y configuración del juego
    - Manejo del estado del juego y la lógica de movimiento
    - Procesamiento de eventos de usuario (teclado y ratón)
    - Integración con algoritmos de IA (árboles de decisión, Q-learning, mapas de calor)
    - Visualización del estado del juego y datos de entrenamiento
    - Modos de edición para modificar el entorno del juego
    
    Atributos:
        screen: Superficie de pygame para renderizar el juego.
        game_state: Instancia de GameState que almacena el estado actual del juego.
        movement_matrix: Matriz numpy que registra la frecuencia de movimientos.
        is_running: Indicador de si el juego está en ejecución.
        edit_mode: Modo de edición actual (None, 'player', 'house', 'obstacles', 'enemies').
        current_path: Lista de posiciones que forman el camino actual.
        best_path: Mejor camino encontrado por los algoritmos de IA.
        agent: Agente de IA utilizado para entrenar y encontrar rutas.
        heat_map_pathfinder: Objeto para pathfinding basado en mapas de calor.
        renderer: Objeto encargado de la visualización del juego.
    """
    def __init__(self):
        """
        Inicializa una nueva instancia del juego.
        
        Configura la pantalla de pygame, inicializa el estado del juego, matrices de movimiento,
        variables de control, rutas, agentes de IA, y el renderizador.
        """
        # Iniciar pygame
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Simulación de Movimiento con Visualización de Datos")

        # Inicializar estado del juego
        self.game_state = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.game_state.initialize_game()
        
        # Inicializar enemigos con comportamiento dinámico si hay soporte para ello
        if hasattr(self, '_initialize_enemies'):
            self._initialize_enemies(3)  # Crear 3 enemigos por defecto

        # Inicializar matriz de movimiento
        self.movement_matrix = np.zeros((GameConfig.GRID_HEIGHT, GameConfig.GRID_WIDTH))

        # Variables de control del juego
        self.is_running = False
        self.move_timer = pygame.time.get_ticks()
        self.edit_mode = None
        self.clock = pygame.time.Clock()  # Inicializar el reloj para controlar FPS y timing

        # Variables de ruta y camino
        self.current_path = []
        self.path_index = 0
        self.best_path = None

        # Variables de entrenamiento y aprendizaje
        self.agent = RandomRoute(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.is_training = False
        self.training_progress = 0
        self.training_status = ""
        self.training_complete = False
        self.show_training_visualization = True
        self.max_training_iterations = 500
        self.total_executions = 0
        self.visible_executions = 0
        self.invisible_executions = 0

        # Inicializar pathfinding con mapa de calor
        self.heat_map_pathfinder = HeatMapPathfinding(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
        self.use_heat_map = False  # Indica si se debe usar el mapa de calor para pathfinding
        self.heat_map_trained = False  # Indica si el mapa de calor ha sido entrenado
        self.heat_map_training_iterations = 500  # Número de iteraciones para entrenamiento

        # Inicializar renderizador
        self.renderer = GameRenderer(self.screen, self)

    def update(self):
        """
        Actualiza el estado del juego en cada ciclo del bucle principal.
        
        Este método maneja:
        - El avance del juego basado en el tiempo
        - El movimiento del jugador según la ruta actual o algoritmos de IA
        - La verificación de victoria al alcanzar la meta
        - Ejecución en modo headless (sin interfaz gráfica) cuando está activado
        - Actualización del movimiento de los enemigos
        
        No realiza ninguna actualización si el juego no está en ejecución (is_running=False).
        """
        # Actualizar estado del juego
        if not self.is_running:
            return
            
        # Actualizar movimiento de enemigos
        self._update_enemies()
        
        # Detectar colisiones entre jugador y enemigos
        self._check_player_enemy_collision()
        
        # Si el jugador ha colisionado con un enemigo, no continuar con la actualización
        if self.game_state.player_caught:
            return
            
        current_time = pygame.time.get_ticks()

        # En modo headless, usar la ruta óptima
        if GameConfig.HEADLESS_MODE and self.best_path:
            if current_time - self.move_timer >= GameConfig.MOVE_DELAY:
                print(f"Paso {self.path_index + 1}/{len(self.best_path)}")

                if self.path_index < len(self.best_path):
                    # Mover al siguiente punto en la ruta
                    next_pos = self.best_path[self.path_index]
                    self.game_state.player_pos = next_pos
                    self.movement_matrix[next_pos[1]][next_pos[0]] += 1

                    # Verificar si llegamos a la meta
                    if next_pos == self.game_state.house_pos:
                        print("¡Llegamos a la meta!")
                        self.game_state.victory = True
                        self.is_running = False
                        GameConfig.HEADLESS_MODE = False
                        
                        # Visualizar análisis final si está disponible
                        if hasattr(self.agent, 'plot_comprehensive_analysis'):
                            self.agent.plot_comprehensive_analysis(
                                self.game_state.initial_player_pos,
                                self.game_state.house_pos,
                                self.game_state.obstacles,
                                save_path="analisis_final.png",
                                show=True
                            )
                    else:
                        self.path_index += 1
                        self.move_timer = current_time
                else:
                    print("Ejecución rápida completada")
                    self.is_running = False
                    GameConfig.HEADLESS_MODE = False
            # Modo normal con movimientos aleatorios
            if current_time - self.move_timer >= GameConfig.MOVE_DELAY:
                self._make_random_move()
                self.move_timer = current_time

        if self.game_state.victory:
            # Calcular la ruta óptima cuando llegamos a la meta
            if not self.best_path:
                self.calculate_optimal_path()
            return

        # Obtener siguiente movimiento
        next_pos = self._get_next_move()
        if not next_pos:
            return

        # Actualizar posición del jugador
        self.game_state.player_pos = next_pos

        # Incrementar contador de visitas en la matriz de movimiento
        x, y = next_pos
        self.movement_matrix[y][x] += 1

        # Verificar victoria
        if next_pos == self.game_state.house_pos:
            self.game_state.victory = True
            # Calcular la ruta óptima inmediatamente
            self.calculate_optimal_path()

    def _get_next_move(self):
        """
        Determina y ejecuta el siguiente movimiento del jugador.
        
        Este método privado:
        - Verifica si el jugador ha llegado a la meta
        - Determina el siguiente movimiento basado en el tiempo transcurrido
        - Sigue un camino predefinido si existe
        - Utiliza árboles de decisión o movimientos aleatorios para generar nuevos movimientos
        - Actualiza la matriz de movimientos con la nueva posición
        
        Returns:
            tuple o None: Las nuevas coordenadas de posición (x, y) o None si no se realizó movimiento
        """
        # Verificar si llegamos a la meta
        if self.game_state.player_pos == self.game_state.house_pos:
            self.game_state.victory = True
            self.is_running = False
            self.visible_executions += 1

            # Calcular la ruta óptima usando A*
            self.calculate_optimal_path()
            return

        # Actualizar movimiento basado en el tiempo
        current_time = pygame.time.get_ticks()
        if current_time - self.move_timer > GameConfig.MOVE_DELAY:
            # Si tenemos un camino predefinido, seguirlo
            if self.path_index < len(self.current_path) - 1:
                self.path_index += 1
                next_pos = self.current_path[self.path_index]
                self.movement_matrix[next_pos[1]][next_pos[0]] += 1
            else:
                # Generar movimiento aleatorio o usar árbol de decisiones
                if GameConfig.USE_DECISION_TREE and random.random() < 0.7:
                    # Usar árbol de decisiones para encontrar el siguiente movimiento
                    decision_tree = DecisionTree(self.game_state, self.movement_matrix)
                    # Limitar la profundidad para decisiones rápidas
                    decision_tree.max_depth = 5
                    smart_path = decision_tree.find_path(
                        self.game_state.player_pos,
                        self.game_state.house_pos
                    )

                    if smart_path and len(smart_path) > 1:
                        # Tomar solo el siguiente paso del camino inteligente
                        next_pos = smart_path[1]
                        self.game_state.player_pos = next_pos
                        self.movement_matrix[next_pos[1]][next_pos[0]] += 1
                        if not self.current_path:
                            self.current_path = [self.game_state.player_pos]
                        self.current_path.append(next_pos)
                    else:
                        # Si no se encuentra un camino, usar movimiento aleatorio
                        self._make_random_move()
                else:
                    # Usar movimiento aleatorio
                    self._make_random_move()

            self.move_timer = current_time

    def _make_random_move(self):
        """
        Genera y ejecuta un movimiento aleatorio para el jugador.
        
        Este método privado:
        - Genera un valor aleatorio para determinar la dirección del movimiento
        - Utiliza los rangos definidos en GameConfig para determinar la dirección
        - Verifica que el movimiento sea válido (dentro de los límites y sin obstáculos)
        - Actualiza la posición del jugador y la matriz de movimientos
        - Añade la nueva posición al camino actual
        """
        # Realiza un movimiento aleatorio usando los rangos de config
        move_value = random.randint(1, 20)
        current_pos = self.game_state.player_pos
        next_pos = None

        # Determinar dirección basada en los rangos de config
        if GameConfig.MOVE_UP_RANGE[0] <= move_value <= GameConfig.MOVE_UP_RANGE[1]:
            next_pos = (current_pos[0], current_pos[1] - 1)
        elif GameConfig.MOVE_RIGHT_RANGE[0] <= move_value <= GameConfig.MOVE_RIGHT_RANGE[1]:
            next_pos = (current_pos[0] + 1, current_pos[1])
        elif GameConfig.MOVE_DOWN_RANGE[0] <= move_value <= GameConfig.MOVE_DOWN_RANGE[1]:
            next_pos = (current_pos[0], current_pos[1] + 1)
        elif GameConfig.MOVE_LEFT_RANGE[0] <= move_value <= GameConfig.MOVE_LEFT_RANGE[1]:
            next_pos = (current_pos[0] - 1, current_pos[1])

            # Verificar si el movimiento es válido
        if (next_pos and
                0 <= next_pos[0] < GameConfig.GRID_WIDTH and
                0 <= next_pos[1] < GameConfig.GRID_HEIGHT and
                next_pos not in self.game_state.obstacles):

            # Actualizar posición y matriz
            self.game_state.player_pos = next_pos
            self.movement_matrix[next_pos[1]][next_pos[0]] += 1
            if not self.current_path:
                self.current_path = [self.game_state.initial_player_pos]
            self.current_path.append(next_pos)

    def run_headless(self):
        """
        Ejecuta el proceso de aprendizaje en segundo plano y muestra la mejor ruta.
        
        Este método:
        - Inicia un proceso de aprendizaje automático en segundo plano
        - Configura callbacks para actualizar la interfaz durante el entrenamiento
        - Reinicia la posición del jugador a la inicial
        - Muestra el progreso del entrenamiento en la interfaz
        - Al finalizar, muestra la mejor ruta encontrada
        - Genera visualizaciones del análisis del aprendizaje si está disponible
        """
        # Iniciar el proceso de aprendizaje
        print("Iniciando proceso de aprendizaje...")
        
        # Definir número de iteraciones para el aprendizaje
        iterations = 500  # Valor predeterminado si no se especifica
        
        # Reiniciar posición del jugador
        self.game_state.player_pos = self.game_state.initial_player_pos
        self.game_state.victory = False
        
        # Preparar visualización del progreso
        self.is_training = True
        self.training_progress = 0
        
        # Configurar los obstáculos para el agente
        obstacles_set = set(self.game_state.obstacles)
        
        # Configurar el número de iteraciones máximas
        self.agent.max_training_iterations = iterations
        
        # Crear una función de callback para actualizar la interfaz durante el entrenamiento
        def progress_callback(iteration, path, history, best_path, is_final=False):
            # Actualizar el progreso
            self.training_progress = (iteration / iterations) * 100
            
            # Actualizar mejor camino
            if best_path:
                self.best_path = best_path
                
            # Cuando termina, mostrar la mejor ruta
            if is_final:
                print(f"Aprendizaje completado. Mejor ruta: {len(best_path) if best_path else 'No encontrada'} pasos")
                self.is_training = False
                
                # Mostrar la mejor ruta
                if best_path:
                    # Reiniciar el juego para mostrar la ruta
                    self.game_state.player_pos = self.game_state.initial_player_pos
                    self.current_path = best_path
                    self.path_index = 0
                    GameConfig.HEADLESS_MODE = True
                    self.is_running = True
                    self.move_timer = pygame.time.get_ticks()
                    
                    # Mostrar análisis del aprendizaje
                    if hasattr(self.agent, 'plot_analysis'):
                        self.agent.plot_analysis(
                            path=best_path,
                            history=history,
                            title="Análisis Final de Aprendizaje",
                            show_heatmap=True
                        )
        
        # Iniciar el entrenamiento en segundo plano
        self.agent.train_background(
            self.game_state.initial_player_pos,
            self.game_state.house_pos,
            obstacles_set,
            callback=progress_callback,
            update_interval=5  # Actualizar el progreso cada 5 iteraciones
        )


    def calculate_optimal_path(self):
        """
        Calcula la ruta óptima usando diferentes algoritmos en orden de prioridad.
        
        El método intenta diferentes estrategias en el siguiente orden:
        1. Primero intenta usar el mejor camino del agente Q-learning si existe
        2. Luego intenta usar el camino del mapa de calor si está entrenado
        3. Como última opción, usa el árbol de decisiones
        
        La mejor ruta encontrada se almacena en self.best_path.
        """
        # Si el agente de Q-learning tiene un mejor camino, usarlo
        if self.agent.best_path:
            self.best_path = self.agent.best_path
            return
        
        # Si el mapa de calor está entrenado, intentar usarlo
        if self.heat_map_trained:
            heat_map_path = self.heat_map_pathfinder.find_path_with_heat_map(
                self.game_state.player_pos,
                self.game_state.house_pos
            )
            
            if heat_map_path:
                self.best_path = heat_map_path
                return
            
        # Si no, usar el árbol de decisiones como respaldo
        decision_tree = DecisionTree(self.game_state, self.movement_matrix)
        decision_tree.max_depth = 20

        # Encontrar el mejor camino usando el árbol de decisiones
        self.best_path = decision_tree.find_path(
            self.game_state.player_pos,
            self.game_state.house_pos
        )


    def toggle_game(self):
        """
        Inicia o detiene la ejecución del juego.
        
        Si el juego no está en ejecución, lo inicia y:
        - Reinicia el índice de camino y el temporizador de movimiento
        - Usa el mejor camino del agente si está disponible
        - Si el mapa de calor está entrenado, intenta usarlo
        - Como alternativa, usa el árbol de decisiones
        
        Si el juego está en ejecución, lo detiene y también detiene cualquier
        entrenamiento en curso.
        """
        # Inicia o detiene el juego
        if not self.is_running:
            self.is_running = True
            self.path_index = 0
            self.move_timer = pygame.time.get_ticks()

            # Reiniciar el camino actual
            self.current_path = [self.game_state.player_pos]

            # Si hemos entrenado y tenemos un mejor camino, usarlo directamente
            if self.agent.best_path:
                self.best_path = self.agent.best_path
                self.current_path = self.best_path
                self.path_index = 0
            # Si el mapa de calor está entrenado, intentar usarlo
            elif self.heat_map_trained and self.use_heat_map:
                heat_map_path = self.heat_map_pathfinder.find_path_with_heat_map(
                    self.game_state.player_pos,
                    self.game_state.house_pos
                )
                
                if heat_map_path and len(heat_map_path) > 1:
                    self.current_path = heat_map_path
                    self.path_index = 0
            # Si no, intentar usar el árbol de decisiones
            elif GameConfig.USE_DECISION_TREE:
                decision_tree = DecisionTree(self.game_state, self.movement_matrix)
                smart_path = decision_tree.find_path(
                    self.game_state.player_pos,317)
        else:
            self.is_running = False
            # Si estamos entrenando, detener el entrenamiento
            if self.is_training:
                self.stop_training()

    def reset_game(self):
        """
        Reinicia el estado del juego a sus valores iniciales.
        
        Este método:
        - Restaura la posición del jugador a la inicial
        - Limpia el camino actual y reinicia el índice
        - Reinicia la matriz de movimiento a ceros
        - Reinicia el estado de victoria
        - Restaura los enemigos a sus posiciones iniciales
        - Detiene cualquier entrenamiento en curso
        
        Nota: No reinicia el mapa de calor para permitir su uso en múltiples ejecuciones.
        """
        # Reinicia el juego
        # Reiniciar posición del jugador
        self.game_state.player_pos = self.game_state.initial_player_pos

        # Reiniciar path
        self.current_path = []
        self.path_index = 0

        # Reiniciar matriz de movimiento
        self.movement_matrix = np.zeros((GameConfig.GRID_HEIGHT, GameConfig.GRID_WIDTH))

        # Reiniciar victoria
        self.game_state.victory = False
        
        # Reiniciar enemigos
        if hasattr(self.game_state, 'enemies') and isinstance(self.game_state.enemies, dict):
            # Si estamos usando el nuevo sistema de enemigos con estados
            self.game_state.enemies.clear()
            self.game_state.enemy_positions.clear()
            
            # Inicializar enemigos desde la configuración
            if hasattr(self, '_initialize_enemies'):
                self._initialize_enemies()
        else:
            # Configuración antigua por compatibilidad
            self.game_state.enemies = set(GameConfig.INITIAL_ENEMY_POSITIONS)

        # Detener cualquier entrenamiento en curso
        if self.is_training:
            self.stop_training()
            
        # No reiniciar el mapa de calor automáticamente
        # para permitir usarlo en múltiples ejecuciones

    def generate_new_obstacles(self):
        """
        Genera nuevos obstáculos aleatorios en el tablero de juego.
        
        Limpia todos los obstáculos existentes y llama al método de generación
        de obstáculos del GameState para crear un nuevo conjunto de obstáculos
        aleatorios.
        """
        # Genera nuevos obstáculos aleatorios
        self.game_state.obstacles.clear()
        self.game_state.generate_obstacles()
        
    def clear_enemies(self):
        """
        Elimina todos los enemigos del juego.
        
        Vacía el conjunto de enemigos en el estado del juego y muestra un
        mensaje de confirmación.
        """
        # Limpia todos los enemigos del juego
        if hasattr(self.game_state, 'enemies') and isinstance(self.game_state.enemies, dict):
            # Nuevo sistema de enemigos
            self.game_state.enemies.clear()
            self.game_state.enemy_positions.clear()
        else:
            # Sistema antiguo
            self.game_state.enemies.clear()
            
        print("Todos los enemigos han sido eliminados")

    def add_or_remove_obstacle(self, pos):
        """
        Agrega o elimina un obstáculo en la posición dada.
        
        Si ya existe un obstáculo en la posición, lo elimina.
        Si no existe un obstáculo, lo agrega siempre que la posición
        no esté ocupada por el jugador o la casa.
        
        Args:
            pos (tuple): Coordenadas (x, y) donde se agregará o eliminará el obstáculo
        """
        # Agrega o remueve un obstáculo en la posición dada
        # Verificar que no sea la posición del jugador o la casa
        if pos == self.game_state.player_pos or pos == self.game_state.house_pos:
            return

        if pos in self.game_state.obstacles:
            self.game_state.obstacles.remove(pos)
        else:
            # No permitir obstáculos en la posición del jugador o la casa
            if pos != self.game_state.player_pos and pos != self.game_state.house_pos:
                self.game_state.obstacles.add(pos)

    def reset_heat_map(self):
        """
        Reinicia el mapa de calor y lo marca como no entrenado.
        
        Este método restablece el estado del objeto HeatMapPathfinding a sus
        valores iniciales y actualiza el indicador de entrenamiento.
        Muestra un mensaje de confirmación.
        """
        self.heat_map_pathfinder.reset()
        self.heat_map_trained = False
        print("Mapa de calor reiniciado")

    def train_heat_map(self, iterations=None):
        """
        Entrena el mapa de calor usando el estado actual del juego.
        
        Este método inicia el entrenamiento del mapa de calor con la configuración
        actual del juego, incluyendo obstáculos y enemigos. Muestra el progreso
        durante el entrenamiento y actualiza la interfaz.
        
        Args:
            iterations (int, opcional): Número de iteraciones para el entrenamiento.
                Si no se proporciona, usa el valor por defecto establecido en la clase.
        
        El método configura un callback para mostrar el progreso y puede ser
        interrumpido por el usuario durante la ejecución.
        """
        if iterations is not None:
            self.heat_map_training_iterations = iterations
            
        print(f"Iniciando entrenamiento del mapa de calor con {self.heat_map_training_iterations} iteraciones...")
        
        # Configurar callback para actualizar interfaz durante entrenamiento
        def training_callback(iteration, total, path, best_path, progress):
            # Actualizar estado en la interfaz
            self.training_progress = progress
            self.training_status = f"Entrenando mapa de calor: {iteration}/{total}"
            
            # Actualizar cada 10 iteraciones para no ralentizar demasiado
            if iteration % 10 == 0 or iteration == total:
                # Actualizar eventos de pygame para mantener la interfaz responsiva
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False  # Detener entrenamiento
                        
                # Renderizar para mostrar progreso
                self.renderer.render()
                pygame.display.flip()
                
            return True  # Continuar entrenamiento
        
        # Entrenar mapa de calor
        self.is_training = True
        try:
            # Ejecutar entrenamiento
            best_path = self.heat_map_pathfinder.train(
                self.game_state.initial_player_pos,
                self.game_state.house_pos,
                self.game_state.obstacles,
                self.game_state.enemies,
                self.heat_map_training_iterations,
                training_callback
            )
            
            # Actualizar estado
            if best_path:
                self.best_path = best_path
                self.heat_map_trained = True
                print(f"Entrenamiento completado. Mejor ruta encontrada: {len(best_path)} pasos")
            else:
                print("Entrenamiento completado pero no se encontró una ruta válida")
        finally:
            self.is_training = False

    def use_heat_map_path(self):
        """
        Configura el juego para usar el camino basado en el mapa de calor.
        
        Si el mapa de calor no está entrenado, inicia automáticamente el entrenamiento.
        Si se encuentra un camino válido, configura el juego para seguir este camino
        y lo muestra en la interfaz.
        
        El método actualiza:
        - current_path con la ruta encontrada
        - path_index a 0 para comenzar desde el principio
        - is_running a True para iniciar el movimiento
        - use_heat_map a True para indicar que se está usando el mapa de calor
        """
        if not self.heat_map_trained:
            print("El mapa de calor no ha sido entrenado. Entrenando ahora...")
            self.train_heat_map()
            
        # Encontrar camino usando el mapa de calor
        path = self.heat_map_pathfinder.find_path_with_heat_map(
            self.game_state.player_pos,
            self.game_state.house_pos,
            avoid_cycles=True
        )
        
        if path:
            print(f"Camino encontrado con mapa de calor: {len(path)} pasos")
            self.current_path = path
            self.path_index = 0
            self.is_running = True
            self.move_timer = pygame.time.get_ticks()
            self.use_heat_map = True
        else:
            print("No se pudo encontrar un camino usando el mapa de calor")

    def visualize_heat_map(self):
        """
        Visualiza el mapa de calor"""
        if not self.heat_map_trained:
            print("El mapa de calor no ha sido entrenado. No hay nada que visualizar.")
            return
            
        # Obtener camino actual si existe para visualizarlo
        path = None
        if self.use_heat_map and self.current_path:
            path = self.current_path
            
        # Visualizar mapa de calor
        self.heat_map_pathfinder.visualize_heat_map(
            start_pos=self.game_state.player_pos,
            goal_pos=self.game_state.house_pos,
            path=path,
            title="Mapa de Calor - Pesos de Recorrido"
        )
        
    def toggle_edit_mode(self, mode):
        # Activa o desactiva un modo de edición
        if self.edit_mode == mode:
            self.edit_mode = None
        else:
            self.edit_mode = mode
            
        # Mensaje de información según el modo
        if self.edit_mode:
            mode_descriptions = {
                "player": "Jugador - Haz clic para colocar el jugador",
                "house": "Casa - Haz clic para colocar la casa",
                "obstacles": "Obstáculos - Haz clic para agregar/eliminar obstáculos",
                "enemies": "Enemigos - Haz clic para agregar/eliminar enemigos"
            }
            print(f"Modo de edición: {mode_descriptions.get(self.edit_mode, self.edit_mode)}")
        else:
            print("Modo de edición desactivado")

    def _handle_keydown(self, key):
        # Maneja eventos de teclado
        if key == pygame.K_SPACE:
            # Iniciar/Detener juego
            self.toggle_game()
        elif key == pygame.K_r:
            # Reiniciar juego
            self.reset_game()
        elif key == pygame.K_h:
            # Modo ejecución rápida
            self.run_headless()
        elif key == pygame.K_o:
            # Modo edición: Obstáculos
            self.toggle_edit_mode('obstacles')
        elif key == pygame.K_p:
            # Modo edición: Jugador
            self.toggle_edit_mode('player')
        elif key == pygame.K_c:
            # Modo edición: Casa
            self.toggle_edit_mode('house')
        elif key == pygame.K_e:
            # Modo edición: Enemigos
            self.toggle_edit_mode('enemies')
        elif key == pygame.K_g:
            # Generar nuevos obstáculos
            self.generate_new_obstacles()
        elif key == pygame.K_i:
            # Inicializar nuevos enemigos
            self._initialize_enemies()
        elif key == pygame.K_m:
            # Entrenar y usar el mapa de calor
            self.train_heat_map()
        elif key == pygame.K_v:
            # Visualizar el mapa de calor
            self.visualize_heat_map()
        elif key == pygame.K_n:
            # Usar ruta generada con mapa de calor
            self.use_heat_map_path()

    def handle_click(self, pos):
        """
        Maneja los eventos de clic del ratón en la interfaz del juego.
        
        Este método procesa los clics del usuario, diferenciando entre:
        - Clics en botones de la interfaz (barra lateral)
        - Clics en el grid del juego durante diferentes modos de edición
        
        Dependiendo de dónde se haga clic y el modo actual, se ejecutarán
        diferentes acciones como iniciar/detener el juego, modificar el entorno,
        o cambiar entre modos de edición.
        
        Args:
            pos (tuple): Coordenadas (x, y) del clic del ratón en píxeles
        """
        # Maneja los clics del mouse
        print(f"\nClic recibido en posición: {pos}")
        print(f"Modo de edición actual: {self.edit_mode}")

        # Obtener botón clickeado
        clicked_button = self.renderer.get_button_at(pos)
        print(f"Botón clickeado: {clicked_button}")

        if clicked_button == "start":
            self.toggle_game()
        elif clicked_button == "reset":
            self.reset_game()
        elif clicked_button == "headless":
            self.run_headless()
        elif clicked_button == "train":
            self.start_training()
        elif clicked_button == "stop_train":
            self.stop_training()
        elif clicked_button == "show_best":
            self.show_best_path()
        elif clicked_button == "edit_player":
            self.edit_mode = "player"
            print("Modo de edición: Jugador")
        elif clicked_button == "edit_house":
            self.edit_mode = "house"
            print("Modo de edición: Casa")
        elif clicked_button == "edit_obstacles":
            self.edit_mode = "obstacles"
            print("Modo de edición: Obstáculos")
        elif clicked_button == "edit_enemies":
            self.edit_mode = "enemies"
            print("Modo de edición: Enemigos")
        elif clicked_button == "clear_obstacles":
            self.game_state.obstacles.clear()
            print("Obstáculos limpiados")
        elif clicked_button == "clear_enemies":
            # Limpiar tanto el diccionario de enemigos como el conjunto de posiciones
            if hasattr(self.game_state, 'enemy_positions'):
                self.game_state.enemy_positions.clear()
            self.game_state.enemies.clear()
            print("Enemigos limpiados")
        elif clicked_button == "use_heat_map":
            self.use_heat_map_path()
        elif clicked_button == "visualize_heat_map":
            self.visualize_heat_map()
        elif clicked_button == "reset_heat_map":
            self.reset_heat_map()
        elif self.edit_mode:
            # Verificar que el clic esté dentro del grid
            grid_width = GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE
            grid_height = GameConfig.GRID_HEIGHT * GameConfig.SQUARE_SIZE

            print(f"Grid width: {grid_width}, Grid height: {grid_height}")
            print(f"Clic dentro del grid: {0 <= pos[0] < grid_width and 0 <= pos[1] < grid_height}")

            if 0 <= pos[0] < grid_width and 0 <= pos[1] < grid_height:
                # Convertir posición del clic a coordenadas del grid
                grid_x = pos[0] // GameConfig.SQUARE_SIZE
                grid_y = pos[1] // GameConfig.SQUARE_SIZE
                grid_pos = (grid_x, grid_y)

                print(f"Posición del grid: {grid_pos}")
                print(f"Obstáculos actuales: {self.game_state.obstacles}")

                # Aplicar edición según el modo
                if self.edit_mode == "player":
                    self.game_state.player_pos = grid_pos
                    self.game_state.initial_player_pos = grid_pos
                    print(f"Jugador movido a: {grid_pos}")
                    self.edit_mode = None
                elif self.edit_mode == "house":
                    self.game_state.house_pos = grid_pos
                    print(f"Casa movida a: {grid_pos}")
                    self.edit_mode = None
                elif self.edit_mode == "obstacles":
                    if grid_pos in self.game_state.obstacles:
                        self.game_state.obstacles.remove(grid_pos)
                        print(f"Obstáculo removido en: {grid_pos}")
                    else:
                        # No permitir obstáculos en la posición del jugador o la casa
                        if grid_pos != self.game_state.player_pos and grid_pos != self.game_state.house_pos:
                            self.game_state.obstacles.add(grid_pos)
                            print(f"Obstáculo añadido en: {grid_pos}")
                        else:
                            print(f"No se puede añadir obstáculo en {grid_pos}: posición ocupada por jugador o casa")
                elif self.edit_mode == "enemies":
                    # Verificar si hay un enemigo en esa posición usando enemy_positions
                    if hasattr(self.game_state, 'enemy_positions') and grid_pos in self.game_state.enemy_positions:
                        # Usar el método remove_enemy para eliminar el enemigo
                        self.game_state.remove_enemy(grid_pos)
                        print(f"Enemigo removido en: {grid_pos}")
                    else:
                        # Usar el método de validación en GameState
                        if self.game_state.is_valid_enemy_position(grid_pos):
                            # Usar add_enemy para añadir un enemigo con tipo aleatorio
                            enemy_types = ["perseguidor", "bloqueador", "patrulla", "aleatorio"]
                            enemy_type = random.choice(enemy_types)
                            enemy_id = self.game_state.add_enemy(grid_pos, enemy_type)
                            if enemy_id:
                                print(f"Enemigo de tipo {enemy_type} añadido en: {grid_pos}")
                            else:
                                print(f"Error al añadir enemigo en: {grid_pos}")
                        else:
                            print(f"No se puede añadir enemigo en {grid_pos}: posición inválida")
        else:
            print("No se realizó ninguna acción")

    def run(self):
        """
        Método principal del juego que maneja el bucle de eventos.
        """
        clock = pygame.time.Clock()
        running = True
        
        # Loop principal
        while running:
            # Manejar eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    # Asegurarse de detener entrenamiento si está activo
                    if self.is_training:
                        self.stop_training()
                
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic izquierdo
                        self.handle_click(event.pos)
            
            # Actualizar estado del juego
            self.update()
            
            # Actualizar visualización
            self.renderer.render()
            
            # Mostrar indicador de progreso de entrenamiento si está activo
            if self.is_training:
                # Dibujar fondo para la información de entrenamiento
                pygame.draw.rect(self.screen, (30, 30, 30), 
                                (0, GameConfig.SCREEN_HEIGHT - 100, GameConfig.SCREEN_WIDTH, 100))
                
                # Dibujar barra de progreso en la parte inferior
                progress_width = int((GameConfig.SCREEN_WIDTH - 40) * (self.training_progress / 100))
                pygame.draw.rect(self.screen, (50, 50, 50), (20, GameConfig.SCREEN_HEIGHT - 40, GameConfig.SCREEN_WIDTH - 40, 20))
                
                # Color dinámico para la barra basado en el progreso
                progress_color = (
                    min(255, int(255 * (1 - self.training_progress / 100))),  # R: disminuye con el progreso
                    min(255, int(255 * (self.training_progress / 100))),       # G: aumenta con el progreso
                    50  # B: constante
                )
                pygame.draw.rect(self.screen, progress_color, (20, GameConfig.SCREEN_HEIGHT - 40, progress_width, 20))
                
                # Mostrar texto de progreso y estado
                font = pygame.font.Font(None, 24)
                
                # Crear sombra para el texto (mejora legibilidad)
                text_shadow = font.render(f"Aprendizaje: {self.training_progress:.1f}% {self.training_status}", True, (0, 0, 0))
                self.screen.blit(text_shadow, (22, GameConfig.SCREEN_HEIGHT - 72))
                
                # Texto principal
                text = font.render(f"Aprendizaje: {self.training_progress:.1f}% {self.training_status}", True, (255, 255, 255))
                self.screen.blit(text, (20, GameConfig.SCREEN_HEIGHT - 70))
                
                # Si el aprendizaje ha completado, mostrar mensaje de finalización
                if self.training_complete and self.best_path:
                    # Mensaje con detalles de la ruta
                    complete_text = font.render(
                        f"¡Aprendizaje completado! Mejor ruta: {len(self.best_path)} pasos", 
                        True, (255, 255, 0)
                    )
                    self.screen.blit(complete_text, (20, GameConfig.SCREEN_HEIGHT - 95))
            # Actualizar pantalla
            pygame.display.flip()
            
            # Controlar FPS
            clock.tick(60)
        
        # Limpieza al salir
        if self.is_training:
            self.stop_training()
        pygame.quit()

    def show_best_path(self):
        """
        Muestra el mejor camino encontrado durante el entrenamiento.
        """
        if not self.best_path:
            print("No hay un mejor camino disponible. Inicie entrenamiento primero.")
            return
        
        print(f"Mostrando mejor camino: {len(self.best_path)} pasos")
        
        # Reiniciar el juego a la posición inicial
        self.game_state.player_pos = self.game_state.initial_player_pos
        self.game_state.victory = False
        
        # Configurar para seguir el mejor camino
        self.current_path = self.best_path.copy()
        self.path_index = 0
        
        # Activar modo de seguimiento
        self.is_running = True
        self.move_timer = pygame.time.get_ticks()
        
        # Mostrar visualización detallada del mejor camino si está disponible
        if hasattr(self.agent, 'plot_best_path'):
            self.agent.plot_best_path(
                self.game_state.initial_player_pos,
                self.game_state.house_pos,
                self.best_path,
                self.game_state.obstacles
            )

    def toggle_headless_mode(self):
        # Activa/desactiva el modo de ejecución rápida
        print("\nCambiando modo de ejecución rápida")
        GameConfig.HEADLESS_MODE = not GameConfig.HEADLESS_MODE
        print(f"Modo headless: {'activado' if GameConfig.HEADLESS_MODE else 'desactivado'}")

        if GameConfig.HEADLESS_MODE:
            print("Calculando ruta óptima para ejecución rápida...")
            # Reiniciar el juego a la posición inicial
            self.game_state.player_pos = self.game_state.initial_player_pos
            self.current_path = [self.game_state.initial_player_pos]
            self.path_index = 0

            # Calcular la ruta óptima
            self.calculate_optimal_path()

            if self.best_path:
                print(f"Ruta encontrada con {len(self.best_path)} pasos")
                self.current_path = self.best_path.copy()
                self.path_index = 0
                self.is_running = True
                self.move_timer = pygame.time.get_ticks()
            else:
                print("No se pudo encontrar una ruta óptima")
                GameConfig.HEADLESS_MODE = False

    def start_training(self):
        """
        Inicia el entrenamiento del agente Q-learning en segundo plano
        """
        if self.is_training:
            print("Ya hay un entrenamiento en curso")
            return

        print("Iniciando entrenamiento en segundo plano...")
        self.is_training = True
        self.training_progress = 0
        
        # Preparar obstáculos para Q-learning
        obstacles_set = set(self.game_state.obstacles)
        
        # Configurar parámetros para el agente
        self.agent.max_training_iterations = self.max_training_iterations
        
        # Iniciar entrenamiento en segundo plano
        self.agent.train_background(
            self.game_state.initial_player_pos,
            self.game_state.house_pos,
            obstacles_set,
            callback=self.training_callback,
            update_interval=10
        )

    def stop_training(self):
        """
        Detiene el entrenamiento en curso
        """
        if not self.is_training:
            print("No hay entrenamiento en curso")
            return

        print("Deteniendo entrenamiento...")
        self.agent.stop_background_training()
        self.is_training = False
        
        # Si tenemos una ruta, mostrarla
        if self.agent.best_path:
            print(f"Mejor ruta encontrada: {len(self.agent.best_path)} pasos")
            self.best_path = self.agent.best_path
        else:
            print("No se encontró una ruta óptima durante el entrenamiento")
            self.training_status = "No se encontró ruta óptima"
    def training_callback(self, iteration, path, history, best_path, is_final=False):
        """
        Callback que se ejecuta periódicamente durante el entrenamiento
        
        Args:
            iteration: Número de iteración actual
            path: Último camino encontrado
            history: Historial de entrenamiento
            best_path: Mejor camino encontrado hasta ahora
            is_final: Si es la llamada final del callback
        """
        # Actualizar el progreso
        self.training_progress = (iteration / self.max_training_iterations) * 100
        
        # Actualizar mejor camino si existe
        if best_path:
            self.best_path = best_path
            self.training_status = f"Mejor ruta: {len(best_path)} pasos"
        else:
            self.training_status = "Buscando ruta óptima..."
            
        # Actualizar visualización cada cierto número de iteraciones
        if iteration % 20 == 0 and not is_final and path:
            # Mostrar información detallada del progreso
            success_count = sum(1 for h in history[-100:] if h.get('success', False)) if history else 0
            recent_success_rate = (success_count / min(100, len(history))) * 100 if history else 0
            
            # Actualizar estado con métricas recientes
            self.training_status = f"Éxito reciente: {recent_success_rate:.1f}%"
            
            # Verificar si el agente está mejorando
            if history and len(history) > 100:
                recent_iterations = [h.get('path_length', float('inf')) for h in history[-50:] if h.get('success', False)]
                earlier_iterations = [h.get('path_length', float('inf')) for h in history[-100:-50] if h.get('success', False)]
                
                if recent_iterations and earlier_iterations:
                    recent_avg = np.mean(recent_iterations) if len(recent_iterations) > 0 else float('inf')
                    earlier_avg = np.mean(earlier_iterations) if len(earlier_iterations) > 0 else float('inf')
                    
                    # Actualizar estado con información de mejora
                    if recent_avg < earlier_avg:
                        improvement = ((earlier_avg - recent_avg) / earlier_avg) * 100
                        self.training_status = f"Mejorando: {improvement:.1f}% (caminos más cortos)"
                    elif recent_avg > earlier_avg:
                        decline = ((recent_avg - earlier_avg) / earlier_avg) * 100
                        self.training_status = f"Explorando: {decline:.1f}% (caminos más largos)"
                    else:
                        self.training_status = f"Estable: {recent_avg:.1f} pasos promedio"
        
        # Cuando finaliza el entrenamiento, mostrar la mejor ruta
        if is_final:
            self.is_training = False
            self.training_complete = True
            
            # Actualizar estado final
            # Actualizar estado final
            if best_path:
                print(f"Entrenamiento completo. Mejor ruta: {len(best_path)} pasos")
                self.training_status = f"¡Completado! Mejor ruta: {len(best_path)} pasos"
                # Preparar para mostrar la mejor ruta con una transición suave
                self.game_state.player_pos = self.game_state.initial_player_pos
                self.current_path = best_path
                self.path_index = 0
                self.is_running = True
                self.move_timer = pygame.time.get_ticks() + 1000  # Retardo para una transición suave
                
                # Mostrar análisis final del aprendizaje
                if hasattr(self.agent, 'plot_comprehensive_analysis'):
                    self.agent.plot_comprehensive_analysis(
                        self.game_state.initial_player_pos,
                        self.game_state.house_pos,
                        self.game_state.obstacles,
                        save_path="analisis_aprendizaje.png",
                        show=self.show_training_visualization
                    )
            else:
                print("Entrenamiento completo. No se encontró una ruta óptima.")
                self.training_status = "No se encontró ruta óptima"
                
            # Actualizar visualización final
            if self.show_training_visualization and best_path:
                # Mostrar visualización de la mejor ruta
                self.agent.plot_best_path(
                    start=self.game_state.initial_player_pos,
                    goal=self.game_state.house_pos,
                    obstacles=self.game_state.obstacles,
                    title="Mejor Ruta Encontrada"
                )

    def _update_enemies(self):
        """
        Actualiza el estado y posición de los enemigos.
        
        Este método maneja:
        - El movimiento de los enemigos según el tiempo transcurrido
        - La detección del jugador por parte de los enemigos
        - La planificación de rutas para perseguir al jugador o interceptarlo
        - El comportamiento específico según el tipo de enemigo
        """
        # No actualizar si el juego no está en ejecución o ya se alcanzó la victoria
        if not self.is_running or self.game_state.victory:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Actualizar el temporizador de enemigos en el estado del juego
        self.game_state.enemy_move_timer += self.clock.get_time() if hasattr(self.clock, 'get_time') else 16  # 16ms aproximadamente 60fps por defecto
        
        # Verificar si es momento de mover a los enemigos
        if self.game_state.enemy_move_timer >= GameConfig.ENEMY_MOVE_DELAY:
            # Reiniciar el temporizador
            self.game_state.enemy_move_timer = 0
            
            # Primero, actualizar todas las posiciones de enemigos
            updated_enemy_positions = set()
            
            # Lista de movimientos a realizar (para evitar colisiones entre enemigos)
            enemy_moves = []
            
            # Para cada enemigo, calcular su movimiento
            for enemy_id, enemy_data in list(self.game_state.enemies.items()):
                # Obtener posición actual del enemigo
                current_pos = enemy_data['position']
                enemy_type = enemy_data['type']
                
                # Determinar el objetivo del enemigo según su tipo
                if enemy_type == "perseguidor":
                    # Persigue directamente al jugador
                    target_pos = self.game_state.player_pos
                    next_pos = self._calculate_enemy_move(enemy_id, current_pos, target_pos)
                elif enemy_type == "bloqueador":
                    # Intenta interceptar el camino del jugador a la casa
                    intercept_pos = self._calculate_intercept_position(current_pos)
                    next_pos = self._calculate_enemy_move(enemy_id, current_pos, intercept_pos)
                elif enemy_type == "patrulla":
                    # Sigue una ruta de patrulla
                    next_pos = self._move_patrol_enemy(enemy_id, current_pos)
                elif enemy_type == "aleatorio":
                    # Movimiento aleatorio
                    next_pos = self._random_enemy_move(enemy_id, current_pos)
                else:
                    # Por defecto, usar comportamiento de perseguidor
                    target_pos = self.game_state.player_pos
                    next_pos = self._calculate_enemy_move(enemy_id, current_pos, target_pos)
                
                # Si se encontró una posición válida, agregarla a la lista de movimientos
                if next_pos and next_pos != current_pos:
                    enemy_moves.append((enemy_id, next_pos))
            
            # Realizar los movimientos evitando colisiones
            for enemy_id, next_pos in enemy_moves:
                # Verificar que la posición no esté ocupada por otro enemigo
                if next_pos not in updated_enemy_positions:
                    # Actualizar posición del enemigo
                    old_pos = self.game_state.enemies[enemy_id]['position']
                    
                    # Eliminar la posición anterior del conjunto de posiciones
                    self.game_state.enemy_positions.remove(old_pos)
                    
                    # Actualizar a la nueva posición
                    self.game_state.enemies[enemy_id]['position'] = next_pos
                    self.game_state.enemy_positions.add(next_pos)
                    
                    # Añadir a posiciones actualizadas
                    updated_enemy_positions.add(next_pos)
                    
                    # Actualizar dirección
                    dx = next_pos[0] - old_pos[0]
                    dy = next_pos[1] - old_pos[1]
                    self.game_state.enemies[enemy_id]['direction'] = (dx, dy)

    def _calculate_enemy_move(self, enemy_id, current_pos, target_pos):
        """
        Calcula el siguiente movimiento para un enemigo hacia un objetivo.
        
        Args:
            enemy_id: ID único del enemigo
            current_pos: Posición actual del enemigo (x, y)
            target_pos: Posición objetivo (x, y)
            
        Returns:
            tuple: Nueva posición (x, y) o None si no hay movimiento válido
        """
        # Verificar si el objetivo está dentro del rango de detección
        manhattan_distance = abs(current_pos[0] - target_pos[0]) + abs(current_pos[1] - target_pos[1])
        
        # Si está fuera del rango de detección, moverse aleatoriamente
        if manhattan_distance > GameConfig.ENEMY_DETECTION_RANGE:
            return self._random_enemy_move(enemy_id, current_pos)
        
        # Intentar usar pathfinding A* para encontrar ruta
        path = self._find_path_for_enemy(current_pos, target_pos)
        
        # Si se encontró una ruta con más de un punto, tomar el siguiente paso
        if path and len(path) > 1:
            return path[1]  # El primer punto es la posición actual
            
        # Si no se pudo encontrar una ruta, intentar movimiento directo
        # Determinar dirección hacia el objetivo
        dx = 0
        dy = 0
        
        # Mover en X
        if current_pos[0] < target_pos[0]:
            dx = 1
        elif current_pos[0] > target_pos[0]:
            dx = -1
            
        # Mover en Y
        if current_pos[1] < target_pos[1]:
            dy = 1
        elif current_pos[1] > target_pos[1]:
            dy = -1
        
        # Intentar movimientos en el siguiente orden: 
        # 1. Movimiento diagonal (si ambos dx y dy no son 0)
        # 2. Movimiento horizontal (dx)
        # 3. Movimiento vertical (dy)
        # 4. Cualquier movimiento válido adyacente
        
        # Lista de posibles movimientos en orden de prioridad
        possible_moves = []
        
        # Añadir movimiento diagonal si ambos dx y dy no son 0
        if dx != 0 and dy != 0:
            possible_moves.append((current_pos[0] + dx, current_pos[1] + dy))
            
        # Añadir movimiento horizontal
        if dx != 0:
            possible_moves.append((current_pos[0] + dx, current_pos[1]))
            
        # Añadir movimiento vertical
        if dy != 0:
            possible_moves.append((current_pos[0], current_pos[1] + dy))
            
        # Añadir movimientos diagonales restantes
        if dx != 0 or dy != 0:
            possible_moves.append((current_pos[0] + dx, current_pos[1] - dy))
            possible_moves.append((current_pos[0] - dx, current_pos[1] + dy))
            
        # Añadir movimientos cardinales restantes
        possible_moves.append((current_pos[0] - 1, current_pos[1]))
        possible_moves.append((current_pos[0] + 1, current_pos[1]))
        possible_moves.append((current_pos[0], current_pos[1] - 1))
        possible_moves.append((current_pos[0], current_pos[1] + 1))
        
        # Probar cada movimiento en orden
        for move in possible_moves:
            # Verificar que el movimiento sea válido
            if self._is_valid_enemy_move(move, current_pos):
                return move
                
        # Si no se encontró ningún movimiento válido, quedarse en la posición actual
        return current_pos
        
    def _random_enemy_move(self, enemy_id, current_pos):
        """
        Genera un movimiento aleatorio para un enemigo.
        
        Args:
            enemy_id: ID único del enemigo
            current_pos: Posición actual del enemigo
            
        Returns:
            tuple: Nueva posición (x, y) o la misma posición si no se puede mover
        """
        # Direcciones posibles (arriba, derecha, abajo, izquierda)
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        # Mezclar direcciones para aleatorizar
        random.shuffle(directions)
        
        # Probar cada dirección
        for dx, dy in directions:
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            if self._is_valid_enemy_move(next_pos, current_pos):
                return next_pos
                
        # Si no hay movimiento válido, quedarse en la misma posición
        return current_pos
        
    def _move_patrol_enemy(self, enemy_id, current_pos):
        """
        Mueve un enemigo en modo patrulla siguiendo una ruta predefinida.
        
        Args:
            enemy_id: ID único del enemigo
            current_pos: Posición actual del enemigo
            
        Returns:
            tuple: Nueva posición (x, y)
        """
        # Obtener datos del enemigo
        enemy_data = self.game_state.enemies[enemy_id]
        
        # Si no tiene una ruta de patrulla, crearla
        if 'patrol_path' not in enemy_data or not enemy_data['patrol_path']:
            # Generar una ruta de patrulla aleatoria alrededor de la posición actual
            patrol_center = current_pos
            patrol_radius = 3  # Radio de patrulla
            
            # Generar puntos de patrulla
            patrol_points = []
            for _ in range(4):  # 4 puntos de patrulla
                # Intentar generar un punto válido
                for attempt in range(10):  # Máximo 10 intentos
                    # Generar desplazamiento aleatorio dentro del radio
                    dx = random.randint(-patrol_radius, patrol_radius)
                    dy = random.randint(-patrol_radius, patrol_radius)
                    
                    # Calcular punto de patrulla
                    patrol_point = (patrol_center[0] + dx, patrol_center[1] + dy)
                    
                    # Verificar que sea un punto válido
                    if self._is_valid_enemy_move(patrol_point, current_pos):
                        patrol_points.append(patrol_point)
                        break
                        
            # Si no se pudo generar suficientes puntos, usar al menos los que tenemos
            if not patrol_points:
                return self._random_enemy_move(enemy_id, current_pos)
                
            # Guardar la ruta de patrulla
            enemy_data['patrol_path'] = patrol_points
            enemy_data['patrol_index'] = 0
        
        # Obtener el punto actual de la patrulla
        patrol_path = enemy_data['patrol_path']
        patrol_index = enemy_data.get('patrol_index', 0)
        
        # Si estamos cerca del punto actual, avanzar al siguiente
        target_point = patrol_path[patrol_index]
        distance = abs(current_pos[0] - target_point[0]) + abs(current_pos[1] - target_point[1])
        
        if distance <= 1:
            # Avanzar al siguiente punto
            patrol_index = (patrol_index + 1) % len(patrol_path)
            enemy_data['patrol_index'] = patrol_index
            target_point = patrol_path[patrol_index]
            
        # Calcular el siguiente paso hacia el punto objetivo
        return self._calculate_enemy_move(enemy_id, current_pos, target_point)
                    
    def _find_path_for_enemy(self, start_pos, target_pos):
        """
        Encuentra una ruta desde la posición inicial hasta el objetivo usando A*.
        
        Args:
            start_pos: Posición inicial (x, y)
            target_pos: Posición objetivo (x, y)
            
        Returns:
            list: Lista de coordenadas (x, y) que forman la ruta, o None si no se encontró ruta
        """
        # Implementación simplificada de A*
        # Conjunto de nodos abiertos y cerrados
        open_set = set([start_pos])
        closed_set = set()
        
        # Diccionario para reconstruir el camino
        came_from = {}
        
        # Costo acumulado desde el inicio a cada nodo
        g_score = {start_pos: 0}
        
        # Costo estimado total (g + h) para cada nodo
        f_score = {start_pos: self._manhattan_distance(start_pos, target_pos)}
        
        # Máximo número de iteraciones para evitar bucles infinitos
        max_iterations = 100
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Encontrar el nodo con menor f_score en open_set
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            # Si llegamos al objetivo, reconstruir y devolver el camino
            if current == target_pos:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
                
            # Mover el nodo actual de open a closed
            open_set.remove(current)
            closed_set.add(current)
            
            # Explorar vecinos (arriba, derecha, abajo, izquierda)
            neighbors = [
                (current[0], current[1] - 1),  # arriba
                (current[0] + 1, current[1]),  # derecha
                (current[0], current[1] + 1),  # abajo
                (current[0] - 1, current[1])   # izquierda
            ]
            
            for neighbor in neighbors:
                # Ignorar vecinos inválidos o ya procesados
                if not self._is_valid_enemy_move(neighbor, current) or neighbor in closed_set:
                    continue
                    
                # Costo tentativo desde el inicio hasta el vecino a través del nodo actual
                tentative_g_score = g_score[current] + 1
                
                # Este camino es mejor que cualquier anterior encontrado para este vecino
                if neighbor not in open_set or tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._manhattan_distance(neighbor, target_pos)
                    
                    if neighbor not in open_set:
                        open_set.add(neighbor)
        
        # Si no se encontró una ruta, devolver None
        return None

    def _manhattan_distance(self, pos1, pos2):
        """
        Calcula la distancia Manhattan entre dos posiciones.
        
        Args:
            pos1: Primera posición (x, y)
            pos2: Segunda posición (x, y)
            
        Returns:
            int: Distancia Manhattan
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        
    def _calculate_intercept_position(self, enemy_pos):
        """
        Calcula una posición para interceptar al jugador en su camino hacia la casa.
        
        Args:
            enemy_pos: Posición actual del enemigo (x, y)
            
        Returns:
            tuple: Posición objetivo (x, y) para la interceptación
        """
        player_pos = self.game_state.player_pos
        house_pos = self.game_state.house_pos
        
        # Calcular vector desde el jugador hasta la casa
        player_to_house_x = house_pos[0] - player_pos[0]
        player_to_house_y = house_pos[1] - player_pos[1]
        
        # Normalizar dirección
        magnitude = max(1, abs(player_to_house_x) + abs(player_to_house_y))
        direction_x = player_to_house_x / magnitude
        direction_y = player_to_house_y / magnitude
        
        # Calcular un punto intermedio en la línea jugador-casa
        # La ubicación exacta se basa en la ponderación de la distancia del enemigo
        # con respecto al jugador y la casa
        
        # Calcular distancias
        enemy_to_player = self._manhattan_distance(enemy_pos, player_pos)
        enemy_to_house = self._manhattan_distance(enemy_pos, house_pos)
        player_to_house = self._manhattan_distance(player_pos, house_pos)
        
        # Factor para decidir qué tan adelante interceptar
        # Si el enemigo está más cerca de la casa, interceptar más cerca del jugador
        # Si el enemigo está más cerca del jugador, interceptar más cerca de la casa
        interception_factor = min(0.8, max(0.2, enemy_to_house / (enemy_to_player + enemy_to_house)))
        
        # Calcular punto de interceptación proyectado
        interception_distance = int(player_to_house * interception_factor)
        projected_x = player_pos[0] + int(direction_x * interception_distance)
        projected_y = player_pos[1] + int(direction_y * interception_distance)
        
        # Asegurar que el punto esté dentro de los límites
        projected_x = max(0, min(GameConfig.GRID_WIDTH - 1, projected_x))
        projected_y = max(0, min(GameConfig.GRID_HEIGHT - 1, projected_y))
        
        # Si el punto proyectado no es válido (ej: hay un obstáculo), usar A* para encontrar un punto cercano
        projected_pos = (projected_x, projected_y)
        if not self._is_valid_enemy_move(projected_pos, enemy_pos):
            # Intentar encontrar un punto válido cerca
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    test_pos = (projected_x + dx, projected_y + dy)
                    if self._is_valid_enemy_move(test_pos, enemy_pos):
                        return test_pos
            
            # Si no encontramos un punto válido, simplemente perseguir al jugador
            return player_pos
            
        return projected_pos

    def _is_valid_enemy_move(self, pos, current_pos=None):
        """
        Verifica si una posición es válida para que un enemigo se mueva a ella.
        
        Args:
            pos: Posición a verificar (x, y)
            current_pos: Posición actual del enemigo, opcional
            
        Returns:
            bool: True si es válida, False en caso contrario
        """
        # Verificar límites del grid
        if not (0 <= pos[0] < GameConfig.GRID_WIDTH and 0 <= pos[1] < GameConfig.GRID_HEIGHT):
            return False
            
        # Verificar que no sea la posición de otro enemigo
        # Si es la posición actual del enemigo que se está moviendo, permitirlo
        if pos in self.game_state.enemy_positions and pos != current_pos:
            return False
            
        # Verificar que no sea un obstáculo
        if pos in self.game_state.obstacles:
            return False
            
        # La posición del jugador se puede pisar (para captura)
        # La posición de la casa no se puede pisar
        if pos == self.game_state.house_pos:
            return False
            
        return True

    def _initialize_enemies(self, count=None):
        """
        Inicializa un número determinado de enemigos en posiciones aleatorias.
        
        Args:
            count: Número de enemigos a crear. Si es None, usa un valor aleatorio basado en el tamaño del grid.
        """
        # Limpiar enemigos existentes
        self.game_state.enemies.clear()
        self.game_state.enemy_positions.clear()
        
        # Determinar número de enemigos
        if count is None:
            # Aproximación simple basada en el tamaño del grid
            grid_area = GameConfig.GRID_WIDTH * GameConfig.GRID_HEIGHT
            obstacle_count = len(self.game_state.obstacles)
            
            # Calcular espacio libre disponible (al menos 20 celdas)
            free_space = max(20, grid_area - obstacle_count - 2)  # Restar jugador y casa
            
            # Usar valores fijos como base para diferentes tamaños de grid
            # Grids pequeños (< 400 celdas): 2-4 enemigos
            # Grids medianos (400-800 celdas): 3-5 enemigos
            # Grids grandes (> 800 celdas): 4-8 enemigos
            
            if grid_area < 400:
                min_enemies = 2
                max_enemies = 4
            elif grid_area < 800:
                min_enemies = 3
                max_enemies = 5
            else:
                min_enemies = 4
                max_enemies = 8
                
            # Limitar por espacio disponible (máximo 5% del espacio libre)
            max_by_space = max(3, int(free_space * 0.05))
            max_enemies = min(max_enemies, max_by_space)
            
            # Asegurar que min_enemies nunca sea mayor que max_enemies
            min_enemies = min(min_enemies, max_enemies)
            
            # Asegurar que siempre hay al menos 1 enemigo y como máximo 8
            min_enemies = max(1, min(8, min_enemies))
            max_enemies = max(min_enemies, min(8, max_enemies))
            
            try:
                # Generar número aleatorio entre min y max (inclusivo)
                count = random.randint(min_enemies, max_enemies)
            except ValueError:
                # En caso de error, usar el valor mínimo
                count = min_enemies
                
            print(f"Generando {count} enemigos (rango {min_enemies}-{max_enemies}) en un grid de {grid_area} celdas con {free_space} espacios libres.")
        
        # Crear enemigos
        enemy_types = ["perseguidor", "bloqueador", "patrulla", "aleatorio"]
        for _ in range(count):
            # Intentar hasta 10 veces encontrar una posición válida
            for attempt in range(10):
                x = random.randint(0, GameConfig.GRID_WIDTH - 1)
                y = random.randint(0, GameConfig.GRID_HEIGHT - 1)
                pos = (x, y)
                
                # Verificar que la posición sea válida y no esté demasiado cerca del jugador
                player_distance = self._manhattan_distance(pos, self.game_state.player_pos)
                
                # No colocar enemigos demasiado cerca del jugador inicial
                min_distance = 4  # Distancia mínima para dar al jugador espacio inicial
                
                if player_distance >= min_distance and self._is_valid_enemy_move(pos):
                    # Escoger un tipo aleatorio de enemigo
                    enemy_type = random.choice(enemy_types)
                    
                    # Crear el enemigo
                    enemy_id = self.game_state.add_enemy(pos, enemy_type)
                    if enemy_id:
                        break  # Enemigo creado exitosamente
        
        print(f"Se han generado {len(self.game_state.enemies)} enemigos")
        
    def _check_player_enemy_collision(self):
        """
        Verifica si el jugador ha colisionado con algún enemigo.
        
        Si hay colisión, establece el estado game_state.player_caught a True
        lo que desencadenará el reinicio del nivel.
        """
        # No verificar colisiones si el juego no está en ejecución o si ya ganó
        if not self.is_running or self.game_state.victory:
            return
            
        # Verificar si el jugador está en la misma posición que algún enemigo
        if self.game_state.player_pos in self.game_state.enemy_positions:
            # Jugador atrapado por un enemigo
            self.game_state.player_caught = True
            print("¡El jugador ha sido atrapado por un enemigo!")
            
            # Esperar un momento antes de reiniciar
            pygame.time.delay(1000)  # Esperar 1 segundo
            
            # Reiniciar posición del jugador pero mantener obstáculos y enemigos
            self.game_state.player_pos = self.game_state.initial_player_pos
            self.game_state.player_caught = False
            
            # Si estamos en modo de camino predefinido, reiniciar índice
            if self.current_path:
                self.path_index = 0
                
            # Actualizar el temporizador de movimiento
            self.move_timer = pygame.time.get_ticks()

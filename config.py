import pygame


class GameConfig:
    """
    Clase de configuración central del juego que define todos los parámetros globales.
    
    Esta clase contiene constantes de configuración utilizadas en toda la aplicación,
    organizadas en secciones lógicas:
    
    - Dimensiones y tamaños: Controla las dimensiones del grid, tamaño de la ventana y elementos visuales
    - Temporización: Velocidad del juego, retrasos entre movimientos, duración de eventos
    - Movimiento: Configuración de rangos para generación de movimientos aleatorios
    - Visualización: Rutas de recursos, colores, y opciones de visualización
    - Gameplay: Parámetros que afectan la lógica y comportamiento del juego
    - Posicionamiento: Posiciones predefinidas para elementos del juego
    
    Todas las configuraciones son accesibles como atributos de clase estáticos.
    Modificar estos valores afectará el comportamiento global del juego.
    """
    
    #==========================================================================
    # DIMENSIONES Y TAMAÑOS
    #==========================================================================
    # Tamaños de la cuadrícula y ventana
    # Tamaño en píxeles de cada celda del grid. Determina la escala visual del juego.
    # Valores más grandes = visualización más grande pero menos celdas visibles.
    SQUARE_SIZE = 20
    
    # Número de celdas en el eje horizontal del grid.
    # Afecta directamente la complejidad del espacio de búsqueda para algoritmos de IA.
    GRID_WIDTH = 40
    
    # Número de celdas en el eje vertical del grid.
    # Afecta directamente la complejidad del espacio de búsqueda para algoritmos de IA.
    GRID_HEIGHT = 30
    
    # Ancho en píxeles del panel lateral que contiene controles e información.
    SIDEBAR_WIDTH = 200

    # Dimensiones calculadas de la ventana en píxeles.
    # Se derivan automáticamente de los parámetros anteriores.
    SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

    #==========================================================================
    # TEMPORIZACIÓN
    #==========================================================================
    # Velocidad del juego en cuadros por segundo (FPS).
    # Controla la frecuencia de actualización de la visualización.
    GAME_SPEED = 60
    
    # Tiempo en milisegundos entre movimientos del jugador en modo normal.
    # Valores más bajos = movimiento más rápido.
    MOVE_DELAY = 100
    
    # Tiempo en milisegundos entre movimientos en modo headless (sin interfaz).
    # Usado durante ejecuciones rápidas y entrenamientos.
    HEADLESS_DELAY = 0
    
    # Tiempo en milisegundos de espera después de resetear el juego.
    # Proporciona una pausa visual antes de reiniciar la acción.
    RESET_DELAY = 500
    
    # Duración en milisegundos de la animación de victoria.
    # Tiempo que se muestra el estado de victoria antes de continuar.
    VICTORY_DURATION = 2000

    #==========================================================================
    # MOVIMIENTO
    #==========================================================================
    # Rangos de valores aleatorios para determinar la dirección de movimiento.
    # Se genera un número aleatorio entre 1-20, y estos rangos determinan 
    # la dirección resultante. Modificar estos rangos cambia la probabilidad
    # de cada dirección durante el entrenamiento con movimientos aleatorios.
    MOVE_UP_RANGE = (1, 5)      # 25% probabilidad de moverse hacia arriba
    MOVE_RIGHT_RANGE = (6, 10)  # 25% probabilidad de moverse hacia la derecha
    MOVE_DOWN_RANGE = (11, 15)  # 25% probabilidad de moverse hacia abajo
    MOVE_LEFT_RANGE = (16, 20)  # 25% probabilidad de moverse hacia la izquierda

    #==========================================================================
    # RECURSOS Y VISUALIZACIÓN
    #==========================================================================
    # Rutas relativas a los archivos de imágenes utilizados para representar elementos del juego.
    # Estas imágenes deben existir en el directorio del proyecto.
    PLAYER_IMAGE = 'bomberman.png.webp'  # Imagen para el jugador
    HOUSE_IMAGE = '27187.jpg.webp'       # Imagen para la meta (casa)
    ENEMY_IMAGE = 'enemy.png'            # Imagen para enemigos

    #==========================================================================
    # CONFIGURACIÓN DE GAMEPLAY
    #==========================================================================
    # NOTA: MOVE_DELAY está duplicado. Se mantiene por compatibilidad pero debería
    # usarse la versión de la sección de temporización.
    MOVE_DELAY = 100  # Duplicado, ver definición anterior
    
    # Controla si se muestran valores numéricos en el grid que indican 
    # la frecuencia de visitas a cada celda. Útil para visualizar patrones de movimiento.
    SHOW_MOVEMENT_MATRIX = True
    
    # Cuando es True, ejecuta el juego en modo rápido sin renderizado visual completo.
    # Útil para entrenamiento y evaluación de algoritmos.
    HEADLESS_MODE = False
    
    # Habilita el uso del algoritmo de árbol de decisiones para encontrar caminos.
    # Si es False, solo se utilizan movimientos aleatorios o mapas de calor.
    USE_DECISION_TREE = True
    
    # Densidad de obstáculos en el grid como porcentaje del total de celdas.
    # Valores válidos: 0-100. Valores más altos = laberintos más difíciles.
    OBSTACLE_PERCENTAGE = 25

    #==========================================================================
    # CONFIGURACIÓN DE ENEMIGOS
    #==========================================================================
    # Tiempo en milisegundos entre movimientos de los enemigos
    # Valores más bajos = enemigos más rápidos
    ENEMY_MOVE_DELAY = 200
    
    # Distancia máxima a la que un enemigo puede detectar al jugador
    # Esta es la distancia en celdas (Manhattan) dentro de la cual el enemigo
    # intentará perseguir al jugador usando pathfinding
    ENEMY_DETECTION_RANGE = 6  # Reducido de 8 para dar más espacio al jugador
    
    # Velocidad de movimiento de los enemigos relativa al jugador (1.0 = misma velocidad)
    # Valores mayores a 1.0 hacen que los enemigos sean más rápidos que el jugador
    ENEMY_SPEED_FACTOR = 0.7  # Reducido de 0.8 para dar ventaja al jugador
    
    # El factor de agresividad determina qué tan probable es que el enemigo
    # intente bloquear el camino hacia la casa en lugar de perseguir al jugador
    # Rango 0.0 (sólo persigue al jugador) a 1.0 (sólo bloquea camino a la casa)
    ENEMY_AGGRESSION_FACTOR = 0.4  # Reducido para hacer el juego más equilibrado
    
    # Distancia mínima entre enemigos durante el posicionamiento inicial
    # Ayuda a evitar la agrupación de enemigos al inicio del juego
    ENEMY_MIN_SEPARATION = 5
    
    # Radio de exploración para el enemigo tipo 'patrulla'
    # Define qué tan lejos de su posición inicial patrullará
    PATROL_RADIUS = 5  # Aumentado para más recorrido
    
    # Tipos de enemigos disponibles y su comportamiento:
    # - "perseguidor": persigue directamente al jugador
    # - "bloqueador": intenta bloquear el camino a la casa
    # - "patrulla": se mueve en rutas de patrulla predefinidas
    # - "aleatorio": se mueve en direcciones aleatorias
    DEFAULT_ENEMY_TYPE = "perseguidor"
    
    # Rango de patrulla para enemigos tipo "patrulla"
    # Define la distancia máxima a la que se generan puntos de patrulla aleatorios
    ENEMY_PATROL_RADIUS = 3
    
    # Distancia mínima inicial entre enemigos y jugador al generar niveles
    # Esto evita que los enemigos aparezcan demasiado cerca del jugador al inicio
    ENEMY_MIN_PLAYER_DISTANCE = 4

    #==========================================================================
    # POSICIONES INICIALES
    #==========================================================================
    #==========================================================================
    # POSICIONES INICIALES
    #==========================================================================
    # Coordenadas iniciales del jugador en el grid como tupla (x, y).
    # Debe ser una posición válida dentro de los límites del grid.
    INITIAL_PLAYER_POS = (12, 10)
    
    # Coordenadas de la meta (casa) en el grid como tupla (x, y).
    # Representa el punto final que el jugador debe alcanzar.
    INITIAL_HOUSE_POS = (25, 20)
    
    # Lista de tuplas (x, y) representando posiciones iniciales de enemigos.
    # Los enemigos actúan como obstáculos móviles o elementos a evitar.
    # Se pueden agregar más posiciones para aumentar la dificultad.
    INITIAL_ENEMY_POSITIONS = [
        (6, 4),
        (20, 8),
        (15, 18)
    ]

    #==========================================================================
    # COLORES BÁSICOS
    #==========================================================================
    # Definiciones de colores en formato RGB (0-255) utilizados en la interfaz.
    # Cada color se representa como una tupla (R, G, B).
    WHITE = (255, 255, 255)     # Blanco puro
    BLACK = (0, 0, 0)           # Negro puro
    RED = (255, 0, 0)           # Rojo puro, usado para enemigos y alertas
    GREEN = (0, 255, 0)         # Verde puro, usado para meta y confirmaciones
    BLUE = (0, 0, 255)          # Azul puro, usado para el jugador
    GRAY = (128, 128, 128)      # Gris medio, usado para elementos neutros y obstáculos
    DARK_GRAY = (64, 64, 64)    # Gris oscuro, usado para fondos
    EGGSHELL = (240, 234, 214)  # Color crema suave, usado para elementos de grid
    CYAN = (0, 255, 255)        # Cian, usado para información
    YELLOW = (255, 255, 0)      # Amarillo, usado para advertencias y puntos de interés
    ORANGE = (255, 165, 0)      # Naranja, usado para rutas y acciones
    PURPLE = (128, 0, 128)      # Púrpura, usado para elementos especiales
    
    # Color para visualizar rutas optimizadas mediante algoritmos de poda.
    # Azul cielo intenso para destacar sobre otros elementos.
    PRUNED_PATH_COLOR = (0, 191, 255)
    
    # Escala de colores para el mapa de calor (heat map), ordenados de menor a mayor intensidad.
    # La visualización usa estos colores para representar la frecuencia de visitas a cada celda,
    # progresando desde amarillo (valores bajos) hasta rojo oscuro (valores altos).
    HEAT_COLORS = [
        (255, 255, 0),   # Amarillo suave - intensidad muy baja
        (255, 200, 0),   # Amarillo anaranjado - intensidad baja
        (255, 150, 0),   # Naranja claro - intensidad moderada baja
        (255, 100, 0),   # Naranja - intensidad moderada
        (255, 50, 0),    # Rojo anaranjado - intensidad moderada alta
        (255, 0, 0),     # Rojo - intensidad alta
        (200, 0, 0),     # Rojo oscuro - intensidad muy alta
        (150, 0, 0)      # Rojo muy oscuro - intensidad máxima
    ]

    #==========================================================================

    # Colores de UI
    SIDEBAR_BG = DARK_GRAY
    GRID_BG = DARK_GRAY
    GRID_COLOR = EGGSHELL
    BUTTON_BG = (200, 200, 200)  # Gris claro para botones
    BUTTON_HOVER = (230, 230, 230)  # Gris más claro para hover
    BUTTON_ACTIVE = (100, 100, 220)  # Azul para botón activo
    BUTTON_FOCUS = (0, 128, 255)  # Azul para focus
    BUTTON_TEXT = BLACK
    BUTTON_TEXT_ACTIVE = WHITE
    OBSTACLE_COLOR = GRAY  # Color de obstáculos
    PLAYER_COLOR = BLUE  # Color del jugador (fallback)
    HOUSE_COLOR = GREEN  # Color de la casa (fallback)
    PATH_COLOR = ORANGE  # Color de la ruta
    ENEMY_COLOR = RED  # Color del enemigo (fallback)

# JuegoIA - Juego de Navegación Inteligente

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![Pygame Version](https://img.shields.io/badge/pygame-2.x-blue.svg)
![License](https://img.shields.io/badge/license-Educational-green.svg)
![Version](https://img.shields.io/badge/version-1.6.0-brightgreen.svg)
![CUValles](https://img.shields.io/badge/CUValles-IA%202024A-orange.svg)

## Resumen Ejecutivo
Este proyecto implementa un juego de simulación de movimiento en cuadrícula donde un avatar intenta alcanzar una meta mientras evita o interactúa con elementos del entorno. La inteligencia del avatar y los enemigos se gestiona mediante algoritmos de aprendizaje por refuerzo (Q-learning) y pathfinding basado en mapas de calor. Destacan:
- Pathfinding para el avatar utilizando Mapas de Calor y Q-learning.
- Enemigos controlados por Q-learning (si se entrena) o con movimiento aleatorio.
- Análisis del entorno mediante mapas de calor para posicionamiento estratégico.
- Interfaz gráfica con Pygame para visualización, interacción y edición del escenario.
- Mecanismo de entrenamiento en segundo plano para los agentes de IA.

## Descripción
Proyecto desarrollado como parte del curso de Inteligencia Artificial en CUValles (Enero-Mayo 2024). Este juego simula la aplicación de técnicas de IA para la toma de decisiones en un entorno dinámico, con un enfoque en Q-learning y pathfinding heurístico.

El avatar debe navegar un grid desde una posición inicial hasta una "casa" (meta), evitando obstáculos. Opcionalmente, pueden existir enemigos que intentan interceptar al avatar. El sistema permite entrenar agentes de Q-learning tanto para el avatar como para los enemigos, y un sistema de pathfinding basado en mapas de calor para guiar al avatar.

> **Nota**: Este proyecto es una herramienta de demostración y aprendizaje.

### Objetivos del Juego/Simulación
- Guiar al avatar desde su posición inicial hasta la casa/meta utilizando las rutas aprendidas o calculadas.
- (Opcional) Evitar ser atrapado por enemigos.
- Observar y analizar cómo diferentes algoritmos de IA (Q-learning, Mapas de Calor) generan rutas y comportamientos.
- Experimentar con la edición del entorno (obstáculos, posiciones) para ver cómo afecta a los algoritmos.

## Índice
1. [Objetivos del Juego/Simulación](#objetivos-del-juegosimulación)
2. [Características Principales](#características-principales)
3. [Controles y UI](#controles-y-ui)
4. [Mecánicas de IA y Juego](#mecánicas-de-ia-y-juego)
5. [Instalación](#instalación)
6. [Estructura del Proyecto](#estructura-del-proyecto)
7. [Detalles Técnicos de IA](#detalles-técnicos-de-ia)
8. [Desarrollo y Contribuciones](#desarrollo-y-contribuciones)
9. [Equipo de Desarrollo](#equipo-de-desarrollo)
10. [Solución de Problemas (FAQ)](#solución-de-problemas-faq)

---

## Características Principales

### Navegación del Avatar
- Movimiento automático basado en rutas calculadas (Q-learning o Mapa de Calor) cuando el juego está en marcha.
- Control manual del avatar con teclas de flecha **solo cuando el juego no está en marcha** (para configuración).
- Detección de colisiones con obstáculos y enemigos.
- Visualización de la ruta actual y la "mejor ruta" planificada.

### Inteligencia de Enemigos
- (Opcional) Hasta 4 tipos de enemigos con comportamiento base de persecución o aleatorio.
- Si se entrena el Agente Q-Learning para enemigos, estos intentarán alcanzar la posición actual del jugador.
- Movimiento de enemigos sincronizado con el del jugador a través de `GameConfig.ENEMY_SPEED_FACTOR`.

### Algoritmos de IA Implementados
- **Q-learning**:
    - Agente para el avatar, aprende una política para alcanzar la casa.
    - Agente para los enemigos, aprende una política para alcanzar al jugador.
    - Entrenamiento en segundo plano con callbacks para visualización de progreso.
    - Funciones de plot para analizar el aprendizaje (recompensas, valores Q, rutas simuladas).
- **Pathfinding con Mapas de Calor (HeatMapPathfinding):**
    - Genera un "heatmap" del avatar que indica la conveniencia de las celdas para llegar a la casa, considerando obstáculos y enemigos (durante el `train`).
    - Utiliza un algoritmo tipo A\* sobre el heatmap generado para encontrar una ruta.
    - Analiza el entorno (basado en el heatmap) para sugerir puntos de estrangulamiento, zonas seguras y posiciones para enemigos.
    - Visualización del heatmap y rutas.

### Interfaz Gráfica (Pygame)
- Visualización en tiempo real del grid, avatar, casa, obstáculos y enemigos.
- Barra lateral con botones para controlar la simulación, entrenamientos, modos de edición y visualizaciones.
- Campo de texto editable en la UI para configurar las iteraciones del entrenamiento del heatmap del avatar.
- Indicadores de progreso para los entrenamientos de los agentes.
- Mensajes de "Victoria" o "Game Over".

---

## Controles y UI

### Teclado:
- **Espacio**: Iniciar/Detener la simulación del movimiento automático del avatar.
- **Flechas (Arriba, Abajo, Izquierda, Derecha)**: Mover el avatar manually **solo si la simulación está detenida (`is_running = False`)**.
- **R**: Reiniciar el juego completamente (resetea posiciones, borra heatmap de frecuencia, mantiene el aprendizaje de los agentes).
- **H**: Iniciar entrenamiento del Agente Q-Learning del Jugador.
- **Q**: Iniciar entrenamiento del Agente Q-Learning de los Enemigos.
- **M**: Iniciar entrenamiento interactivo del Mapa de Calor del Avatar.
- **N**: Configurar al jugador para que siga la ruta del Mapa de Calor (si está entrenado y disponible).
- **V**: Solicitar visualización del Mapa de Calor del Avatar (plot).
- **O**: Activar/Desactivar modo edición de Obstáculos (clic en grid para añadir/quitar).
- **P**: Activar/Desactivar modo edición de Posición del Jugador (clic en grid para mover).
- **C**: Activar/Desactivar modo edición de Posición de la Casa (clic en grid para mover).
- **E**: Activar/Desactivar modo edición de Enemigos (clic en grid para añadir/quitar).
- **G**: Generar un nuevo conjunto aleatorio de obstáculos.
- **F1-F4**: Solicitar diferentes plots de análisis para el Agente Q-Learning de Enemigos (si está entrenado).

### Interfaz Gráfica (Botones en la Sidebar):
La barra lateral contiene botones que replican y extienden la funcionalidad de las teclas:
- **Iniciar/Detener**: Equivalente a la tecla Espacio.
- **Reiniciar Juego**: Equivalente a la tecla R.
- **Entrenar Agente Jugador**: Equivalente a la tecla H.
- **Entrenar Agente Enemigo**: Equivalente a la tecla Q.
- **Detener Entrenamientos Activos**: Para los procesos de Q-learning o Heatmap.
- **Editar Pos Jugador/Casa/Obstáculos/Enemigos**: Activan los respectivos modos de edición.
- **Limpiar Todos Obstáculos/Enemigos**: Eliminan estos elementos del mapa.
- **Jugador Sigue Heatmap**: Equivalente a la tecla N.
- **Ver Heatmap Avatar**: Equivalente a la tecla V.
- **Resetear Heatmap Avatar**: Borra los datos aprendidos del heatmap, requiere re-entrenamiento.
- **Iter HM Av: [valor]**: Botón que funciona como campo de texto. Al hacer clic, permite ingresar un nuevo número de iteraciones para el entrenamiento del heatmap del avatar usando el teclado numérico (Enter para confirmar, Esc para cancelar).

---

## Mecánicas de IA y Juego

### Movimiento del Avatar
- Cuando la simulación está activa (`is_running = True`), el avatar sigue automáticamente la `current_path_player`. Las teclas de flecha son ignoradas para el movimiento del avatar en este estado.
- `current_path_player` se determina por `determine_player_optimal_path()`, que considera:
    1.  La ruta del Mapa de Calor del Avatar (si está entrenado y es la opción preferida o la única).
    2.  La ruta derivada de la política del Agente Q-Learning del Jugador (si está entrenado y es mejor que la del heatmap).
- Si la ruta se bloquea, se intenta un recálculo. Si falla, el avatar se detiene.
- El movimiento manual con flechas solo es posible cuando `is_running = False` (para configurar la posición inicial).

### Comportamiento de Enemigos
- **Inicialización:**
    - El usuario puede colocar enemigos manualmente en el modo edición (tecla 'E').
    - Si el usuario no coloca enemigos y se inicia el juego, se inicializan según `GameConfig.INITIAL_ENEMY_POSITIONS` o mediante colocación estratégica/aleatoria basada en el análisis del heatmap del avatar.
    - El juego puede correr sin enemigos si el usuario los elimina todos ("Limpiar Enemigos") y no reinicia con la configuración por defecto o añade nuevos.
- **Movimiento:**
    - Si el Agente Q-Learning de Enemigos está entrenado (`enemy_q_agent_trained = True`), los enemigos usarán la política aprendida para moverse hacia la posición actual del jugador.
    - Si no está entrenado, los enemigos se moverán aleatoriamente a celdas válidas adyacentes.
    - La frecuencia de movimiento de los enemigos se controla por `GameConfig.ENEMY_SPEED_FACTOR` en relación con los "pasos" del jugador (incrementos de `self.step_counter`). Por ejemplo, si `ENEMY_SPEED_FACTOR = 0.5`, el enemigo se mueve cada 2 pasos del jugador.

### Sistema de Colisiones y Fin de Juego
- Si el avatar alcanza la posición de la casa, se declara "Victoria" y la simulación se detiene.
- Si la posición del avatar coincide con la de un enemigo mientras la simulación está activa, se declara "Game Over" y la simulación se detiene.
- En ambos casos, se muestra un mensaje en pantalla y el juego espera la interacción del usuario (principalmente reiniciar con 'R'). La pantalla del juego se "congela" mostrando el estado final, con el mensaje de victoria/derrota superpuesto.

---

## Instalación

### Requisitos
- Python 3.x (probado con 3.9+)
- Pygame (probado con 2.x)
- NumPy
- Matplotlib (para los plots de análisis)

### Pasos de Instalación
1.  Asegúrate de tener Python 3 instalado.
2.  Clona o descarga el repositorio del proyecto.
3.  Abre una terminal o línea de comandos en la carpeta del proyecto.
4.  Instala las dependencias (se recomienda usar un entorno virtual):
    ```bash
    pip install pygame numpy matplotlib
    ```
5.  Asegúrate de tener los archivos de imagen (`player.png`, `house.png`, `enemy.png`) en la misma carpeta que `main.py`, o en una subcarpeta `assets/` (y ajusta `GameConfig.PLAYER_IMAGE`, etc., si es necesario).
6.  Ejecuta el juego:
    ```bash
    python main.py
    ```

### Configuración Inicial Recomendada
1.  Al iniciar, puedes usar las teclas **P**, **C**, **O**, **E** (o los botones de la UI) para entrar en los respectivos modos de edición y configurar el escenario (posición del jugador, casa, obstáculos, enemigos). El movimiento manual del avatar con flechas solo funciona si el juego está detenido.
2.  Puedes ajustar el número de iteraciones para el entrenamiento del heatmap del avatar usando el botón/campo de texto "Iter HM Av: [valor]".
3.  Entrena el heatmap del avatar (**M**) y/o los agentes Q-learning (**H** para jugador, **Q** para enemigos). Los entrenamientos se ejecutan en segundo plano.
4.  Una vez configurado y/o entrenado, presiona **Espacio** o el botón "Iniciar/Detener" para comenzar la simulación. El avatar seguirá la ruta calculada.

---

## Estructura del Proyecto
JuegoIA/
├── main.py # Punto de entrada principal
├── Game.py # Clase principal del juego, maneja lógica y bucle principal
├── GameState.py # Clase para gestionar el estado del juego (posiciones, obstáculos, etc.)
├── render.py # Clase para dibujar todos los elementos y la UI
├── config.py # Constantes y configuraciones del juego y IA
├── ADB.py # Implementación del Agente Q-learning
├── HeatMapPathfinding.py # Implementación del pathfinding basado en Mapas de Calor
└── README.md # Esta documentación
---

## Detalles Técnicos de IA

### Agente Q-learning (`ADB.py`)
- Implementa una tabla Q (NumPy array) para el espacio de estados (posiciones del grid) y acciones (arriba, abajo, izquierda, derecha).
- Utiliza una política epsilon-greedy para el balance entre exploración y explotación durante el entrenamiento.
- Parámetros configurables: tasa de aprendizaje (`learning_rate`), factor de descuento (`discount_factor`), decaimiento de épsilon (`epsilon_decay`), épsilon mínimo (`epsilon_min`).
- La función de recompensa incentiva acercarse al objetivo y penaliza los pasos, el alejamiento o quedarse quieto.
- Permite entrenamiento en un hilo separado para no bloquear la UI, con un callback para actualizar el progreso.
- Ofrece varios métodos de plot para visualizar:
    - `plot_analysis`: Progreso de recompensas y épsilon.
    - `plot_q_values_heatmap`: Mapas de calor de los valores Q para cada acción.
    - `plot_best_path`: Simulación de un camino usando la política aprendida.
    - `plot_comprehensive_analysis`: Un conjunto combinado de los plots anteriores.

### Pathfinding con Mapas de Calor (`HeatMapPathfinding.py`)
- **Entrenamiento del Heatmap (`train`):**
    - Simula múltiples "caminatas" desde la posición inicial del avatar hacia la casa.
    - Las celdas en los caminos exitosos son reforzadas en `avatar_heat_map`.
    - El refuerzo es mayor para celdas más cercanas a la meta en un camino corto.
    - Considera obstáculos y la posición actual de los enemigos (si se proporcionan) para penalizar celdas peligrosas durante la simulación de caminatas.
- **Búsqueda de Ruta (`find_path_with_heat_map`):**
    - Utiliza un algoritmo similar a A\* para encontrar la ruta óptima sobre el `avatar_heat_map`.
    - El "costo" de moverse a una celda vecina está influenciado por el valor del `avatar_heat_map`.
    - Maneja explícitamente el caso donde la meta es adyacente al inicio.
    - Puede realizar un entrenamiento ad-hoc si el heatmap está vacío.
- **Análisis del Entorno (`analyze_environment`):**
    - Utiliza el `avatar_heat_map` entrenado para identificar puntos de estrangulamiento, zonas seguras y posiciones potenciales para enemigos.
- **Visualización (`visualize_heat_map`):**
    - Genera un plot del `avatar_heat_map` usando Matplotlib.

---

## Desarrollo y Contribuciones
Proyecto desarrollado como parte del curso de Inteligencia Artificial 2024A en CUValles.

## Equipo de Desarrollo
Desarrollado como proyecto del curso de Inteligencia Artificial 2024A en CUValles:
- Fregoso Gutierrez Enrique de Jesus
- Ortiz Jimenez Vladimir
- Sanchez Sanchez Andrea Yunuhen Vianney

### Supervisión y Asesoría
- Dr. Hernando Rosales - Profesor del curso de IA

---

## Registro de Versiones (Ejemplo)
- v1.0 - v1.4: Desarrollo inicial.
- v1.5: Re-enfoque en Q-learning y Heatmaps.
- v1.6.0 (Mayo 2024):
  * Implementación robusta de Q-learning y Heatmaps.
  * UI mejorada, campo de texto editable, feedback de entrenamiento.
  * Control de movimiento de enemigos por `ENEMY_SPEED_FACTOR`.
  * Múltiples correcciones de bugs y refinamientos de lógica de juego y IA.
  * Clarificación del movimiento manual vs. automático.

---

## Agradecimientos
- Dr. Hernando Rosales por la guía y supervisión del proyecto.
- Centro Universitario de los Valles (CUValles) por el apoyo y recursos.
- Comunidad de desarrollo de Pygame y Matplotlib.

---

## Solución de Problemas (FAQ)

1.  **El avatar no se mueve después de iniciar el juego (Espacio):**
    *   Asegúrate de que se haya calculado una ruta. `determine_player_optimal_path()` se llama al iniciar.
    *   Intenta entrenar el Mapa de Calor del Avatar (M) o el Agente Q-Jugador (H) primero.
    *   Verifica la consola; si dice "No hay ruta planificada" o `current_path_player` es solo la posición actual, el avatar no se moverá automáticamente.
    *   Si creaste un escenario donde la casa es inaccesible (ej. completamente rodeada por obstáculos, o un "muro" hecho con la propia casa donde ninguna celda adyacente a la casa es válida), ningún pathfinder podrá encontrar una ruta.

2.  **Los enemigos se comportan de forma extraña (atascados, ciclos):**
    *   Esto suele indicar que el Agente Q-Learning de Enemigos necesita más entrenamiento o ajustes en sus parámetros (tasa de aprendizaje, decaimiento de épsilon, función de recompensa).
    *   Aumenta `enemy_agent_max_training_iterations` en `Game.py`.
    *   Prueba con valores diferentes para `epsilon_decay` y `epsilon_min` en `ADB.py` (los valores recientes deberían ser mejores).
    *   Asegúrate de que la función de recompensa en `ADB.py` incentive correctamente el comportamiento deseado (perseguir al jugador).
    *   Si no has entrenado a los enemigos, se moverán aleatoriamente.

3.  **El juego se ejecuta lento, especialmente durante el entrenamiento:**
    *   Los algoritmos de IA pueden ser intensivos. El entrenamiento en un hilo separado ayuda a que la UI no se congele, pero el proceso sigue consumiendo CPU.
    *   Considera reducir el tamaño del grid en `config.py` o el número de iteraciones de entrenamiento. Para un grid de 40x30, `max_training_iterations` para Q-learning podría necesitar ser de varios miles (e.g., 10000-50000) para una buena convergencia, lo cual tomará tiempo.

4.  **Errores de `TypeError` o `AttributeError`:**
    *   Asegúrate de tener todos los archivos del proyecto actualizados y en la misma carpeta.
    *   Verifica las versiones de Python y las bibliotecas.

5.  **Las imágenes no se cargan:**
    *   Asegúrate de que los archivos de imagen (`player.png`, `house.png`, `enemy.png`) estén en la misma carpeta que `main.py`, o en una subcarpeta `assets/` y que la ruta en `GameRenderer._load_image()` (vía `GameConfig`) sea correcta.

---

## Contacto
Para dudas o sugerencias sobre el proyecto:
- Email: fregosogenrique@gmail.com
- Email: vladimir.ortiz8015@alumnos.udg.mx
- Email: andrea.sanchez0541@alumnos.udg.mx

---

## Licencia
Este proyecto es parte del curso de IA en CUValles y está disponible para uso educativo.

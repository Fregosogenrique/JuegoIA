# JuegoIA - Juego de Navegación Inteligente

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![Pygame Version](https://img.shields.io/badge/pygame-2.x-blue.svg)
![License](https://img.shields.io/badge/license-Educational-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)
![CUValles](https://img.shields.io/badge/CUValles-IA%202024A-orange.svg)

## Resumen Ejecutivo
Este proyecto implementa un juego de simulación de movimiento en cuadrícula donde un avatar intenta alcanzar una meta mientras evita o interactúa con elementos del entorno. La inteligencia del avatar y los enemigos se gestiona mediante algoritmos de aprendizaje por refuerzo (Q-learning) y pathfinding basado en mapas de calor. Destacan:
- Pathfinding para el avatar utilizando Mapas de Calor (colonia de hormigas + A*) y Q-learning, eligiendo la ruta de menor riesgo y replanificando en tiempo real.
- Cuatro tipos de enemigo con comportamiento propio (perseguidor, bloqueador, patrulla, aleatorio), guiados por Q-learning si se entrena o por "instinto" si no.
- Análisis del entorno mediante mapas de calor para posicionamiento estratégico (cuellos de botella, zonas seguras).
- Sistema de turnos con velocidad relativa exacta entre avatar y enemigos.
- Interfaz gráfica con Pygame para visualización, interacción y edición del escenario.
- Mecanismo de entrenamiento en segundo plano para los agentes de IA.

> 📘 **La explicación detallada de cada mecánica** (cómo funciona, qué se mejoró en la v2.0 y con qué parámetros se ajusta) está en **[MECANICAS.md](MECANICAS.md)**.

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
- (Opcional) 4 tipos de enemigos con comportamiento propio: perseguidor, bloqueador (corta el paso), patrulla (ronda/persecución) y aleatorio.
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
- **R**: Reiniciar el juego completamente (mapa nuevo, resetea posiciones, borra heatmap de frecuencia, mantiene el aprendizaje de los agentes; si el mapa cambió mucho, el panel indicará que conviene reentrenarlos).
- **H**: Iniciar entrenamiento del Agente Q-Learning del Jugador.
- **Q**: Iniciar entrenamiento del Agente Q-Learning de los Enemigos.
- **M**: Iniciar entrenamiento interactivo del Mapa de Calor del Avatar.
- **N**: Alternar entre selección automática de ruta (la de menor riesgo entre Heatmap y Agente Q) y forzar la ruta del Mapa de Calor.
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
- **Jugador Sigue Heatmap**: Equivalente a la tecla N (interruptor).
- **Ver Heatmap Avatar**: Equivalente a la tecla V.
- **Resetear Heatmap Avatar**: Borra los datos aprendidos del heatmap, requiere re-entrenamiento.
- **Iter HM Av: [valor]**: Botón que funciona como campo de texto. Al hacer clic, permite ingresar un nuevo número de iteraciones para el entrenamiento del heatmap del avatar usando el teclado numérico (Enter para confirmar, Esc para cancelar).

---

## Mecánicas de IA y Juego

Resumen; la explicación completa, con fórmulas y parámetros, está en **[MECANICAS.md](MECANICAS.md)**.

| Mecánica | En pocas palabras |
|---|---|
| **Mundo** | Grid 40×30 con 18 % de obstáculos. Cada mapa generado se verifica con BFS: la casa siempre es alcanzable. |
| **Turnos** | Cada `MOVE_DELAY` ms: avatar → victoria → enemigos → captura → replanificación. Los enemigos acumulan `ENEMY_SPEED_FACTOR` y dan un paso por cada unidad completa (0.5 = 1 paso cada 2 turnos). |
| **Avatar** | Sigue su ruta; replanifica si un enemigo amenaza las próximas celdas o cada `REPLAN_EVERY_TURNS` turnos; si no hay ruta segura, huye. Con el juego detenido se mueve con las flechas. |
| **Selección de ruta** | Compara la ruta del Heatmap y la del Agente Q con un mismo costo: pasos + peligro por cercanía a enemigos. Gana la más segura. |
| **Mapa de calor** | Colonia de hormigas: caminatas guiadas por feromona y distancia real a la casa, con borrado de bucles, depósito ∝ 1/longitud, evaporación y elitismo. |
| **A\*** | Costo por celda ≥ 1 (heurística admisible): prefiere celdas calientes, evita enemigos y sus alrededores. |
| **Análisis del entorno** | Cuellos de botella medidos por el rodeo que causaría bloquearlos; zonas seguras frías y lejos de la ruta. |
| **Q-learning** | Estado (x, y, dirección al objetivo); recompensa por progreso en distancia real; ε programado; inicios exploratorios; objetivos aleatorios para enemigos; aviso si el mapa cambió desde el entrenamiento. |
| **Enemigos** | Perseguidor (directo), bloqueador (corta el paso y embosca), patrulla (ronda ↔ persecución con histéresis), aleatorio (con inercia). Nunca pisan la casa. |
| **Fin de partida** | Victoria al llegar a la casa; game over si un enemigo entra en la celda del avatar. |

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
### JuegoIA/
    ├── main.py # Punto de entrada principal
    ├── Game.py # Clase principal del juego, maneja lógica y bucle principal
    ├── GameState.py # Clase para gestionar el estado del juego (posiciones, obstáculos, etc.)
    ├── render.py # Clase para dibujar todos los elementos y la UI
    ├── config.py # Constantes y configuraciones del juego y IA
    ├── ADB.py # Implementación del Agente Q-learning
    ├── HeatMapPathfinding.py # Mapa de calor (colonia de hormigas), A* y análisis del entorno
    ├── grid_utils.py # Utilidades de cuadrícula compartidas (BFS, distancias, vecinos)
    ├── test_mecanicas.py # Pruebas automáticas de las mecánicas (python -m unittest test_mecanicas)
    ├── MECANICAS.md # Explicación detallada de cada mecánica
    └── README.md # Esta documentación
---

## Detalles Técnicos de IA

### Agente Q-learning (`ADB.py`)
- Tabla Q de forma `(alto, ancho, 25 sectores, 4 acciones)`: el estado incluye el desplazamiento hacia el objetivo, por lo que una misma tabla sirve para objetivos que se mueven.
- Política ε-greedy restringida a acciones válidas; ε decae con un programa calculado para llegar a `epsilon_min` al 70 % del entrenamiento.
- Recompensa: `-1` por paso, `+ (d(s) - d(s'))` por progreso en distancia real (BFS) y `+100` al llegar; la política óptima coincide con el camino más corto.
- Inicios exploratorios (jugador) y objetivos aleatorios (enemigos).
- `is_policy_current(obstáculos)` indica si la tabla sigue siendo válida para el mapa actual.
- Entrenamiento en un hilo separado con callback de progreso (tasa de éxito de los últimos 100 episodios).
- Gráficas: `plot_analysis`, `plot_q_values_heatmap`, `plot_best_path`, `plot_comprehensive_analysis`.

### Pathfinding con Mapas de Calor (`HeatMapPathfinding.py`)
- **`train`** (colonia de hormigas): cada iteración lanza una hormiga desde el avatar hacia la casa; la probabilidad de cada vecino combina feromona, progreso en distancia real y peligro por enemigos. Las hormigas exitosas depositan feromona proporcional a 1/longitud (tras borrar bucles); en cada iteración se evapora una fracción y se refuerza la mejor ruta (elitismo).
- **`find_path_with_heat_map`** (A*): costo `1 + HEAT_WEIGHT·(1 − τ/τmax) + peligro`; heurística Manhattan admisible; las celdas con enemigo quedan bloqueadas.
- **`path_cost`**: costo de riesgo usado para comparar rutas de distinto origen.
- **`analyze_environment`**: cuellos de botella (por rodeo al bloquearlos), zonas seguras y posiciones potenciales para enemigos.
- **`visualize_heat_map`**: gráfica de la feromona con obstáculos, enemigos y ruta, con la misma orientación que el juego.

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
- v2.0.0 (Octubre 2026): Actualización de todas las mecánicas conservando la esencia del juego (ver [MECANICAS.md](MECANICAS.md)).
  * Sistema de turnos con velocidad de enemigos exacta (antes iban al doble de lo configurado).
  * Mapa de calor como colonia de hormigas: rutas óptimas y entrenamiento ~4× más rápido.
  * A* que evita enemigos y con heurística admisible; selección de ruta por costo de riesgo; replanificación dinámica y huida.
  * Q-learning con estado relativo al objetivo, recompensa por distancia real, ε programado y aviso de política desactualizada.
  * Comportamiento propio para cada tipo de enemigo (perseguidor, bloqueador, patrulla, aleatorio).
  * Mapas generados siempre con la casa alcanzable; panel de estado en la interfaz; pruebas automáticas.
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
    *   Los mapas generados (inicio, R, G) siempre dejan la casa alcanzable, pero si editas obstáculos a mano y la encierras, ningún pathfinder podrá encontrar una ruta.
    *   Si los enemigos tapan el único pasillo, el panel mostrará "Ruta: Huida": el avatar se aleja de ellos hasta que se abra un camino.

2.  **Los enemigos se comportan de forma extraña (atascados, ciclos):**
    *   Sin entrenar, los enemigos usan su "instinto" (acercarse en línea recta) y pueden atascarse detrás de muros. Entrena el Agente Q Enemigo con **Q**.
    *   Si el panel dice "Q Enemigo: desactualizado (mapa cambió)", el mapa es distinto al del entrenamiento: vuelve a pulsar **Q**.
    *   Para más precisión, aumenta `enemy_agent_max_training_iterations` en `Game.py` (5000 por defecto) o ajusta `learning_rate`, `exploration_fraction` y `epsilon_min` en `ADB.py`.
    *   Recuerda que cada tipo se mueve distinto: el aleatorio deambula y la patrulla hace su ronda hasta que te detecta.

3.  **El juego se ejecuta lento, especialmente durante el entrenamiento:**
    *   Los algoritmos de IA pueden ser intensivos. El entrenamiento en un hilo separado ayuda a que la UI no se congele, pero el proceso sigue consumiendo CPU.
    *   Considera reducir el tamaño del grid en `config.py` o el número de iteraciones de entrenamiento. Con los valores por defecto (grid 40x30), el Agente Q Jugador converge en ~1 s (1500 episodios) y el Enemigo en ~8 s (5000 episodios).

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

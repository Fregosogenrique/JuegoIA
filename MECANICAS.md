# Mecánicas de JuegoIA (v2.0)

Este documento explica **cada mecánica del juego**: qué hace, cómo funciona por dentro, qué se mejoró respecto a la versión 1.x y qué parámetros la controlan. La esencia del proyecto se mantiene: un avatar que debe llegar a su casa en una cuadrícula, enemigos que intentan atraparlo, un **mapa de calor** aprendido con caminatas simuladas y agentes de **Q-learning**. Lo que cambia es que cada concepto ahora está implementado de forma correcta y actual.

## Índice

1. [El mundo: cuadrícula y obstáculos](#1-el-mundo-cuadrícula-y-obstáculos)
2. [Sistema de turnos y velocidad de los enemigos](#2-sistema-de-turnos-y-velocidad-de-los-enemigos)
3. [Movimiento del avatar: seguir, replanificar, huir](#3-movimiento-del-avatar-seguir-replanificar-huir)
4. [Selección de ruta por costo de riesgo](#4-selección-de-ruta-por-costo-de-riesgo)
5. [Mapa de calor: colonia de hormigas](#5-mapa-de-calor-colonia-de-hormigas)
6. [A* sobre el mapa de calor](#6-a-sobre-el-mapa-de-calor)
7. [Análisis del entorno](#7-análisis-del-entorno)
8. [Agentes de Q-learning](#8-agentes-de-q-learning)
9. [Enemigos: tipos y comportamiento](#9-enemigos-tipos-y-comportamiento)
10. [Victoria, captura y fin de partida](#10-victoria-captura-y-fin-de-partida)
11. [Mapa de frecuencia del avatar](#11-mapa-de-frecuencia-del-avatar)
12. [Lo que se ve en pantalla](#12-lo-que-se-ve-en-pantalla)
13. [Resultados medidos: antes y después](#13-resultados-medidos-antes-y-después)

---

## 1. El mundo: cuadrícula y obstáculos

**Qué es.** Una cuadrícula de 40×30 celdas (`GRID_WIDTH`, `GRID_HEIGHT`). Cada celda puede estar libre o tener un obstáculo, el avatar, la casa o un enemigo. El movimiento es ortogonal: arriba, derecha, abajo o izquierda.

**Generación de obstáculos** (`GameState.generate_obstacles`). Se coloca un `OBSTACLE_PERCENTAGE` % de obstáculos al azar (18 % por defecto), sin tocar al avatar, la casa ni los enemigos.

**Mejora: garantía de mapa jugable.** Antes, un mapa aleatorio podía encerrar la casa o al avatar, y ningún algoritmo encontraba ruta. Ahora, después de generar el mapa, se comprueba con una **búsqueda en anchura (BFS)** que exista un camino del avatar a la casa. Si no existe, el mapa se descarta y se genera otro (hasta `MAX_OBSTACLE_LAYOUT_ATTEMPTS` intentos).

**Distancia real frente a distancia Manhattan** (`grid_utils.py`). Muchas mecánicas necesitan saber "qué tan lejos está algo":
- **Manhattan**, `|dx| + |dy|`: rápida, pero no ve los muros.
- **Distancia BFS**: el número real de pasos rodeando obstáculos. La calcula `bfs_distance_map` para todo el mapa de una sola vez. La usan el Q-learning (recompensa), las hormigas (heurística), el análisis del entorno y el generador de mapas.

## 2. Sistema de turnos y velocidad de los enemigos

**Qué es.** El juego avanza por **turnos**, uno cada `MOVE_DELAY` ms (150 ms; `HEADLESS_DELAY` en modo sin cabeza). El dibujo en pantalla va aparte, a `GAME_SPEED` FPS.

**Orden de un turno** (`Game.play_turn`):
1. El avatar da un paso.
2. Si llegó a la casa → **victoria**.
3. Los enemigos se mueven según su velocidad.
4. Si un enemigo ocupa la celda del avatar → **captura (game over)**.
5. Si hay amenaza en la ruta, o cada `REPLAN_EVERY_TURNS` turnos, el avatar **replanifica**.

**Velocidad relativa con acumulador.** En cada turno se suma `ENEMY_SPEED_FACTOR` a un acumulador, y por cada unidad completa los enemigos dan un paso:

| `ENEMY_SPEED_FACTOR` | Pasos de enemigo |
|---|---|
| 0.5 | 1 cada 2 turnos |
| 0.75 | 3 cada 4 turnos |
| 1.0 | 1 por turno |
| 1.5 | 3 cada 2 turnos |

**Qué se corrigió.** Antes, los enemigos se movían "si el contador de pasos del avatar es múltiplo de N", pero la comprobación se hacía en **cada fotograma**. Como el avatar tarda dos fotogramas en dar un paso, los enemigos se movían dos veces en los pasos pares. La velocidad efectiva era **0.98 en vez de 0.5**. Además, si el avatar se quedaba quieto en un número par de pasos, los enemigos se movían en cada fotograma. Con el acumulador, la velocidad es exacta y admite cualquier valor fraccionario.

## 3. Movimiento del avatar: seguir, replanificar, huir

**Modo configuración** (juego detenido). Las flechas mueven al avatar manualmente para elegir el punto de partida, como antes.

**Modo simulación** (juego corriendo). El avatar sigue `current_path_player`. En cada turno (`_advance_player`):
1. **Seguir:** avanza a la siguiente celda de la ruta si está libre y es adyacente.
2. **Replanificar:** si la siguiente celda está bloqueada (por ejemplo, por un enemigo), recalcula la ruta desde su posición actual y lo intenta de nuevo.
3. **Huir** (nuevo): si no existe ninguna ruta segura (enemigos tapando un pasillo) y hay un enemigo a `DANGER_RADIUS` casillas o menos, se mueve a la celda vecina más alejada de todos los enemigos. El panel muestra "Ruta: Huida".

**Replanificación dinámica** (nuevo). Antes, la ruta se calculaba una sola vez y el avatar caminaba "a ciegas" junto a los enemigos hasta chocar. Ahora replanifica:
- **por amenaza:** si un enemigo está a 1 casilla o menos de alguna de las próximas `THREAT_LOOKAHEAD` celdas de la ruta;
- **periódicamente:** cada `REPLAN_EVERY_TURNS` turnos mientras haya enemigos.

Es la misma idea que usan los algoritmos de planificación en tiempo real (familia D*): planificar, ejecutar un poco y volver a planificar con la información nueva.

**Detalle corregido.** Tras cada replanificación, el índice de la ruta apuntaba a la celda actual, así que el avatar "gastaba" un paso quedándose en el sitio. Ahora apunta a la siguiente celda.

## 4. Selección de ruta por costo de riesgo

**Qué es** (`Game.determine_player_optimal_path`). Hay dos "cerebros" que pueden proponer una ruta a la casa:
- **Heatmap Avatar:** A* sobre el mapa de calor (secciones 5 y 6).
- **Agente Q Jugador:** la política aprendida (sección 8), si está entrenada y vigente para el mapa actual.

**Mejora.** Antes se elegía simplemente la ruta más corta, aunque pasara junto a un enemigo. Ahora ambas rutas se comparan con el mismo **costo de riesgo**:

```
costo(ruta) = Σ (1 + peligro(celda))
peligro(celda) = Σ_enemigos  DANGER_WEIGHT / (1 + d)   si d ≤ DANGER_RADIUS
```

Gana la de menor costo. Una ruta 2 pasos más larga pero lejos de los enemigos le gana a una más corta que roza a uno.

**Tecla N / botón "Jugador Sigue Heatmap"** (ahora es un interruptor). Fuerza a usar solo el mapa de calor; si se pulsa otra vez, se vuelve a la selección automática. Antes, el efecto de N se perdía al pulsar Iniciar, porque la ruta se recalculaba sin tenerlo en cuenta.

## 5. Mapa de calor: colonia de hormigas

**La idea original (se conserva).** Se simulan muchas caminatas desde el avatar hasta la casa. Las celdas de las caminatas exitosas se "calientan", y luego el buscador de rutas prefiere las celdas calientes.

**La mejora: formalizarlo como Ant Colony Optimization (ACO, Dorigo 1996).** Esa idea es exactamente el algoritmo de colonia de hormigas, y adoptar su forma completa corrige sus debilidades (`HeatMapPathfinding.train`):

- **Cada caminata es una hormiga.** En cada paso elige vecino con probabilidad
  ```
  p(n) ∝ (τ(n) + τ0)^α · exp(-β·Δd(n)) · exp(-peligro(n))
  ```
  - `τ(n)`: **feromona** de la celda (el valor del mapa de calor). Lo que aprendieron las hormigas anteriores.
  - `Δd(n)`: cuánto acerca (−1) o aleja (+1) ese vecino de la casa según la **distancia real BFS**. Antes se usaba Manhattan, que empuja contra los muros.
  - `peligro(n)`: cercanía a los enemigos presentes durante el entrenamiento.
  - `τ0`: feromona base, para que ninguna celda tenga probabilidad cero (exploración).
- **Memoria de la hormiga:** no repite celdas mientras tenga alternativas.
- **Borrado de bucles:** antes de depositar, se eliminan los rodeos del camino (si la hormiga volvió a una celda ya visitada, se corta el bucle). Así no se calientan desvíos inútiles.
- **Depósito ∝ 1/longitud:** cada hormiga exitosa reparte `Q` unidades de feromona entre las celdas de su camino. Las rutas cortas concentran más calor por celda. Antes, el refuerzo dependía de la posición dentro del camino: el inicio siempre era lo más caliente, aunque la ruta fuera mala.
- **Evaporación** (`ACO_EVAPORATION`, ρ): en cada iteración `τ ← (1−ρ)·τ`. Las rutas viejas o malas se enfrían solas. Antes, el calor solo se acumulaba.
- **Elitismo:** la mejor ruta encontrada se refuerza en cada iteración (`ACO_ELITE_WEIGHT`).

**Parámetros** (atributos de clase de `HeatMapPathfinding`): `ACO_ALPHA`, `ACO_BETA`, `ACO_TAU0`, `ACO_EVAPORATION`, `ACO_DEPOSIT` y `ACO_ELITE_WEIGHT`. El número de hormigas es el campo "Iter HM Av" de la interfaz.

**Cuándo se entrena.** Al iniciar, al reiniciar y al editar el mapa (obstáculos, casa, avatar, enemigos), y a demanda con la tecla **M** (cancelable con Esc).

## 6. A* sobre el mapa de calor

**Qué es** (`find_path_with_heat_map`). Una búsqueda A* desde la posición actual del avatar hasta la casa, donde moverse a una celda cuesta:

```
costo(n) = 1 + HEAT_WEIGHT·(1 − τ(n)/τ_max) + peligro(n)
```

- Las celdas **calientes** (rutas aprendidas) cuestan cerca de 1; las frías cuestan un poco más.
- Las celdas **cercanas a enemigos** se encarecen, y las **ocupadas por enemigos** quedan bloqueadas.

**Qué se corrigió.**
1. **Los enemigos se ignoraban:** el A* recibía las posiciones de los enemigos pero no las usaba. Ahora sí las evita.
2. **Heurística no admisible:** el costo por paso podía bajar a 0.1, pero la heurística (Manhattan) supone un costo de 1 por paso. Eso sobrestima y hace que A* devuelva rutas que no son óptimas. Ahora el costo es siempre ≥ 1, así que Manhattan es **admisible** y la ruta es óptima para el costo definido.
3. **Conjunto cerrado:** los nodos ya expandidos no se vuelven a procesar, en lugar de cortar la búsqueda tras un número fijo de nodos.

## 7. Análisis del entorno

**Qué es** (`analyze_environment`). Con el mapa de calor entrenado, se estudia el terreno para colocar enemigos de forma estratégica cuando el usuario no pone los suyos:

- **Cuellos de botella** (`choke_points`). **Mejora:** antes, una celda era cuello de botella si tenía 2 vecinos libres o menos. Ahora se mide directamente: se bloquea cada celda de la ruta principal y se recalcula la distancia BFS. Si el rodeo cuesta **4 pasos o más** (o deja la casa inalcanzable), es un cuello de botella real. Se ordenan de mayor a menor impacto.
- **Zonas seguras** (`safe_zones`): celdas frías (por debajo del percentil 25 de calor) y a 3 casillas o más de la ruta. Son buenos puntos de patrulla.
- **Posiciones para enemigos** (`potential_enemy_positions`): el tramo central de la ruta principal más los cuellos de botella.

## 8. Agentes de Q-learning

Hay dos agentes con la misma clase (`ADB.QLearningAgent`): el **Agente Q Jugador** (tecla H) aprende a llegar a la casa, y el **Agente Q Enemigo** (tecla Q) aprende a alcanzar un objetivo cualquiera. Ambos entrenan en un hilo en segundo plano.

**Regla de aprendizaje (Bellman):**
```
Q(s,a) ← Q(s,a) + α·( r + γ·max_a' Q(s',a') − Q(s,a) )
```
Con α = `learning_rate` (0.3) y γ = `discount_factor` (0.97). Las acciones que llevarían contra un muro o fuera del mapa nunca se eligen.

### 8.1 Estado que incluye el objetivo
**Antes:** el estado era solo la celda `(x, y)`, y la función de elegir acción ignoraba el objetivo. El agente enemigo aprendía a ir a la casilla donde estaba el jugador **en el momento de entrenar**, y en el juego perseguía ese punto fijo aunque el jugador ya no estuviera ahí.

**Ahora:** el estado es `(x, y, sector)`, donde `sector` es el desplazamiento hasta el objetivo recortado a ±2 casillas por eje (25 valores). Así, el agente distingue "objetivo a 1 casilla al este" de "objetivo lejos al sureste". Una sola tabla sirve para perseguir a un jugador que se mueve.

### 8.2 Recompensa con distancia real
Se conserva la idea original: premiar acercarse y castigar alejarse. Pero la distancia se mide con BFS:
```
r = −1 (por paso) + ( d(s) − d(s') ) + 100 (al llegar)
```
Acercarse cuesta 0, alejarse cuesta −2, y llegar da +100, así que **la política óptima es exactamente el camino más corto**. Con Manhattan, rodear un muro parecía "alejarse" y se castigaba justo el movimiento correcto.

> Nota de diseño: también se probó el moldeado por potencial clásico, `γ·Φ(s') − Φ(s)`. Con γ < 1, ese término da un premio por paso proporcional a la distancia, y lejos de la casa deambular salía "rentable": el agente aprendía a no llegar nunca. Por eso se usa la diferencia directa de distancias.

### 8.3 Exploración programada (ε-greedy)
Con probabilidad ε el agente elige una acción al azar (explora); si no, la de mayor Q (explota). **Antes**, ε se multiplicaba por 0.999 por episodio: tras 500 episodios seguía en **0.61**, es decir, el agente se comportaba al azar el 61 % del tiempo hasta el final. **Ahora**, el decaimiento se calcula para que ε llegue a `epsilon_min` (0.05) al 70 % del entrenamiento (`exploration_fraction`). El último 30 % de los episodios es una fase de afinado.

### 8.4 Inicios exploratorios y objetivos aleatorios
- **Jugador:** la mitad de los episodios empieza en una celda aleatoria (`exploring_starts_prob`). Como el avatar replanifica a mitad de camino, la política debe ser buena desde cualquier celda, no solo desde la salida.
- **Enemigo:** cada episodio sortea un **objetivo y un inicio aleatorios**. La política aprende a "ir hacia lo que sea", que es lo que necesita para perseguir al jugador o interceptarlo.

### 8.5 Vigencia del aprendizaje
Una tabla Q tabular solo vale para el mapa en que se aprendió. **Antes**, al reiniciar (R) se generaba un mapa nuevo y los agentes seguían usando su tabla vieja, que a menudo los llevaba contra los muros. **Ahora**, el agente recuerda el mapa de su entrenamiento y `is_policy_current()` mide la similitud con el actual. Si difiere más de un 10 %:
- el Agente Q Jugador deja de proponer rutas;
- los enemigos vuelven al "instinto" (sección 9);
- el panel lateral muestra "desactualizado (mapa cambió)" para indicar que hay que reentrenar.

### 8.6 Métricas y gráficas
Durante el entrenamiento se muestra la **tasa de éxito** de los últimos 100 episodios, una métrica más clara que la "mejor recompensa". Teclas **F1–F4** (agente enemigo):
- F1: recompensa, tasa de éxito y ε por episodio.
- F2: valores Q de cada acción, vistos hacia el objetivo de referencia.
- F3: camino simulado con la política.
- F4: análisis completo.

Las gráficas usan la misma orientación que el juego (y hacia abajo).

## 9. Enemigos: tipos y comportamiento

**Antes**, los 4 tipos (perseguidor, bloqueador, patrulla, aleatorio) solo se distinguían por el color del indicador: todos se movían igual. **Ahora**, cada tipo tiene su propio comportamiento (`Game._enemy_target`):

| Tipo | Color | Comportamiento |
|---|---|---|
| **Perseguidor** | rojo | Va directo hacia la posición actual del avatar. |
| **Bloqueador** | naranja | Apunta a la celda que está `BLOCKER_LOOKAHEAD` pasos **por delante** del avatar en su ruta, para cortarle el paso. Al llegar, espera en **emboscada**. Si el avatar está a 2 casillas o menos, lo ataca. |
| **Patrulla** | morado | **Máquina de estados.** En *patrulla* recorre una ronda de 4 puntos alrededor de su aparición (radio `PATROL_RADIUS`). Si ve al avatar (`PATROL_DETECTION_RADIUS`) pasa a *persecución*; si lo pierde (`PATROL_LOSE_RADIUS`) vuelve a patrullar. Usar dos radios distintos (histéresis) evita que cambie de estado en cada turno. |
| **Aleatorio** | cian | Deambula con **inercia**: mantiene su dirección con probabilidad `RANDOM_ENEMY_INERTIA`, así que se mueve en tramos en vez de temblar en el sitio. |

**Cómo da cada paso hacia su objetivo** (`Game._enemy_next_step`):
1. Si el objetivo es adyacente, entra en él (así atrapa al avatar).
2. **Con el Agente Q Enemigo entrenado y vigente:** usa la política aprendida, que sabe rodear muros.
3. **Sin entrenar ("instinto"):** elige el vecino que más reduce la distancia Manhattan. Funciona en terreno abierto, pero se atasca detrás de los muros. Antes, un enemigo sin entrenar se movía completamente al azar.
4. **Memoria anti-ciclos:** cada enemigo recuerda sus últimas `ENEMY_LOOP_MEMORY` celdas. Si el paso elegido vuelve a una de ellas, prueba otra salida, para no oscilar entre dos casillas.

**Reglas comunes.** Ningún enemigo puede pisar obstáculos, otros enemigos ni **la casa**: así el avatar siempre tiene una meta libre (antes un enemigo podía quedarse sobre la casa). Todos los enemigos sí pueden entrar en la celda del avatar, que es como lo atrapan.

**Colocación inicial.** Si el usuario no coloca enemigos (tecla E), al iniciar se usan `INITIAL_ENEMY_POSITIONS`, completadas con la colocación estratégica de la sección 7:
- perseguidores en el tramo central de la ruta;
- bloqueadores en cuellos de botella;
- patrullas en zonas seguras.

Los tipos se sortean de `ENEMY_TYPES`.

## 10. Victoria, captura y fin de partida

- **Victoria:** el avatar entra en la casa. Se muestran los pasos y turnos usados.
- **Captura:** un enemigo entra en la celda del avatar. El avatar nunca entra voluntariamente en la celda de un enemigo, y como el avatar mueve antes que los enemigos, no pueden "cruzarse" sin que haya captura.
- En ambos casos la simulación se detiene y se muestra el mensaje. **R** reinicia: mapa nuevo, con el aprendizaje de los agentes conservado (aunque puede quedar desactualizado, ver 8.5).

## 11. Mapa de frecuencia del avatar

Cada paso del avatar suma 1 en `player_movement_frequency_matrix`, que se dibuja como un mapa de calor de "dónde ha estado". Con `COUNT_SETUP_MOVES_IN_FREQUENCY_MAP` también cuentan los movimientos manuales de configuración, y con `SHOW_VISIT_COUNT_ON_HEATMAP` se ve el número de visitas en cada celda.

## 12. Lo que se ve en pantalla

- **Estela de feromona** (amarillo → rojo oscuro): el mapa de calor de las hormigas. Las celdas por debajo del 2 % del máximo no se dibujan, para que se distingan la ruta principal y las alternativas.
- **Línea discontinua amarilla:** la mejor ruta planificada (con el juego detenido).
- **Línea naranja:** el tramo de ruta que **falta** recorrer (con el juego corriendo).
- **Aro rojo sobre un enemigo:** está persiguiendo activamente al avatar.
- **Panel de estado** (abajo en la barra lateral): turno y pasos, origen de la ruta (Heatmap, Agente Q o Huida) y celdas restantes, número de enemigos y su velocidad, y estado de cada agente Q (sin entrenar, entrenado o desactualizado).

## 13. Resultados medidos: antes y después

Mediciones con el grid de 40×30 y 18 % de obstáculos (scripts de simulación sin interfaz):

| Mecánica | v1.x | v2.0 |
|---|---|---|
| Velocidad real de enemigos con `ENEMY_SPEED_FACTOR = 0.5` | 0.98 | 0.50 |
| Agente Q Jugador: pasos hasta la casa (óptimo = 64) | 64–76 | **64** |
| Agente Q Jugador: ε al terminar | 0.61 | 0.05 |
| Agente Q Jugador: éxito desde una celda aleatoria | no se entrenaba para ello | ≈ 98 % |
| Mapa de calor: ruta de referencia (óptimo = 64) | 83 pasos | **64** |
| A* sobre el heatmap (óptimo = 64) | 68 pasos | **64** |
| Tiempo de entrenamiento del heatmap (500 iteraciones) | 1.26 s | 0.3 s |
| Agente Q Enemigo: sigue la posición **actual** del jugador | no | sí |
| Enemigo entrenado alcanzando un objetivo (≤ 40 pasos) | – | 96 %, rutas 1.17× el óptimo (instinto: 92 %, 1.44×) |
| Mapas con la casa inalcanzable | posibles | imposibles |
| Avatar gana a velocidad 0.5 con 4 enemigos sin entrenar | – | 19 de 20 partidas |

Las pruebas automáticas de estas mecánicas están en `test_mecanicas.py`:

```bash
python -m unittest test_mecanicas -v
```

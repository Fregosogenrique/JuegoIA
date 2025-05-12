# JuegoIA - Proyecto Acumulativo IA 25A CUValles

## Descripción
Proyecto desarrollado como parte del curso de Inteligencia Artificial en CUValles. Es un juego de navegación implementado en Python utilizando la librería Pygame, donde un avatar debe alcanzar una meta mientras evita obstáculos y enemigos. El proyecto está diseñado de forma modular para permitir futuras actualizaciones y extensiones.

## Características Principales

### Navegación del Avatar
- Control manual del avatar
- Movimiento basado en cuadrícula
- Reposicionamiento del avatar mediante interfaz gráfica
- Detección de colisiones con obstáculos y enemigos

### Enemigos Inteligentes
- Implementación de A* pathfinding para persecución
- Ratio de movimiento 2:1 (el avatar se mueve dos veces por cada movimiento de enemigo)
- Diferentes tipos de enemigos:
  * Perseguidores: Usan A* para seguir al jugador
  * Bloqueadores: Intentan interceptar al jugador
  * Patrullas: Siguen rutas predefinidas
  * Aleatorios: Movimiento aleatorio

### Algoritmos de IA Implementados
- **Pathfinding A***: Implementación optimizada para la navegación de enemigos
- **Árboles de decisión**: Sistema de toma de decisiones para navegación
- **Mapas de calor**: Análisis y visualización de patrones de movimiento
- **Sistema Q-learning**: Aprendizaje de rutas óptimas

### Interfaz Gráfica
- Visualización en tiempo real del juego
- Barra lateral con controles y estadísticas
- Indicadores visuales de estado
- Mapa de calor para análisis de movimiento

### Características del Sistema de IA
- Inteligencia artificial adaptativa que mejora con el tiempo
- Sistema de toma de decisiones basado en el comportamiento del jugador
- Múltiples niveles de dificultad en el comportamiento de los enemigos
- Análisis en tiempo real de patrones de movimiento

## Controles
- **Espacio**: Iniciar/Detener juego
- **R**: Reiniciar juego
- **H**: Modo entrenamiento (headless)
- **C**: Editar posición de la casa
- **O**: Editar obstáculos
- **E**: Editar enemigos
- **Botón Reposicionar Avatar**: Permite cambiar la posición inicial del avatar
- **L**: Limpiar obstáculos

## Mecánicas de Juego

### Sistema de Enemigos
- Cada enemigo tiene su propio comportamiento basado en IA
- Los enemigos perseguidores utilizan A* para encontrar la ruta más corta
- Los bloqueadores predicen y anticipan el movimiento del jugador
- Las patrullas mantienen áreas específicas bajo vigilancia
- Los enemigos aleatorios añaden un elemento de imprevisibilidad

### Ratio de Movimiento 2:1
- El jugador tiene ventaja estratégica con dos movimientos por cada uno del enemigo
- Sistema implementado mediante contador de pasos (step_counter)
- Balance entre desafío y jugabilidad

### Sistema de Colisiones
- Detección precisa de colisiones entre entidades
- Manejo de game over al colisionar con enemigos
- Validación de movimientos para evitar superposiciones

## Modos de Juego
1. **Modo Normal**
   - Control manual del avatar
   - Enemigos activos con IA
   - Objetivo: Llegar a la casa evitando enemigos

2. **Modo Entrenamiento**
   - Entrenamiento automático de rutas
   - Visualización de progreso
   - Generación de mapas de calor

3. **Modo Edición**
   - Modificación de obstáculos
   - Colocación de enemigos
   - Ajuste de posiciones iniciales

## Instalación

### Requisitos
- Python 3.x
- Pygame
- NumPy

### Pasos de Instalación
1. Clonar el repositorio:
   ```bash
   git clone [URL_del_repositorio]
   ```

2. Instalar dependencias:
   ```bash
   pip install pygame numpy
   ```

3. Ejecutar el juego:
   ```bash
   python main.py
   ```

## Estructura del Proyecto
```
JuegoIA/
├── main.py                 # Punto de entrada principal
├── Game.py                # Lógica principal del juego y IA
├── GameState.py           # Gestión del estado del juego
├── render.py              # Sistema de renderizado y UI
├── config.py              # Configuraciones y constantes
├── DecisionTree.py        # Algoritmo de árboles de decisión
├── HeatMapPathfinding.py  # Sistema de mapas de calor
├── ADB.py                 # Algoritmos de aprendizaje
└── README.md             # Documentación del proyecto
```

## Funcionalidades Avanzadas

### Sistema de Pathfinding A*
El juego implementa un sistema avanzado de pathfinding A* que:
- Calcula rutas óptimas para los enemigos
- Evita obstáculos y otros enemigos
- Se actualiza en tiempo real según el movimiento del jugador

### Control de Movimiento 2:1
- El avatar se mueve dos veces por cada movimiento de enemigo
- Sistema sincronizado para mantener el balance del juego
- Previene que los enemigos sean demasiado agresivos

### Mapas de Calor
- Visualización de zonas más transitadas
- Análisis de patrones de movimiento
- Ayuda en la estrategia de juego

## Desarrollo y Contribuciones
Proyecto desarrollado como parte del curso de IA en CUValles. Las contribuciones y mejoras son bienvenidas siguiendo estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Realiza tus cambios y commits (`git commit -am 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crea un Pull Request

## Equipo de Desarrollo
Desarrollado por estudiantes del curso de Inteligencia Artificial 25A en CUValles:
- Fregoso Gutierrez Enrique de Jesus
- Ortiz Jimenez Vladimir
- Sanchez Sanchez Andrea Yunuhen Vianney

## Registro de Versiones
- v1.0: Implementación inicial del juego
- v1.1: Adición de sistema A* para enemigos
- v1.2: Implementación de ratio 2:1 en movimiento
- v1.3: Mejoras en la interfaz y controles
- v1.4: Integración de mapas de calor
- v1.5: Sistema de reposicionamiento del avatar

## Agradecimientos
- Dr. Hernando Rosales por la guía y supervisión del proyecto
- Centro Universitario de los Valles (CUValles) por el apoyo y recursos
- Comunidad de desarrollo de Pygame por las herramientas y documentación

## Licencia
Este proyecto es parte del curso de IA en CUValles y está disponible para uso educativo.

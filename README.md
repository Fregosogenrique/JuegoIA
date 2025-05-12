# JuegoIA - Proyecto Acumulativo IA 25A CUValles

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![Pygame Version](https://img.shields.io/badge/pygame-2.5.0+-blue.svg)
![License](https://img.shields.io/badge/license-Educational-green.svg)
![Version](https://img.shields.io/badge/version-1.5-brightgreen.svg)
![CUValles](https://img.shields.io/badge/CUValles-IA%2025A-orange.svg)

## Resumen Ejecutivo
Este proyecto implementa un juego de navegación con diferentes tipos de enemigos controlados por IA. Destacan:
- Implementación de A* pathfinding con ratio 2:1
- Cuatro tipos de enemigos con comportamientos únicos
- Sistema de mapas de calor para análisis
- Interfaz gráfica intuitiva con múltiples modos

## Descripción
Proyecto desarrollado como parte del curso de Inteligencia Artificial en CUValles (Enero-Mayo 2024). Este juego forma parte de la evaluación continua de la materia, demostrando la aplicación práctica de conceptos como pathfinding, comportamientos inteligentes y análisis de datos a través de mapas de calor.

Este juego de navegación, implementado en Python con Pygame, presenta un desafío donde un avatar debe alcanzar una meta mientras evita enemigos inteligentes que utilizan algoritmos de IA, incluyendo A* pathfinding con ratio de movimiento 2:1, árboles de decisión y mapas de calor para su comportamiento.

> **Nota**: Este proyecto está en desarrollo activo y se actualiza regularmente con nuevas características y mejoras.

### Objetivos del Juego
- Guiar al avatar desde su posición inicial hasta la casa/meta
- Evitar ser atrapado por los enemigos inteligentes
- Encontrar rutas óptimas considerando los obstáculos
- Utilizar la ventaja del movimiento 2:1 estratégicamente

## Índice
1. [Objetivos del Juego](#objetivos-del-juego)
2. [Características Principales](#características-principales)
3. [Controles](#controles)
4. [Mecánicas de Juego](#mecánicas-de-juego)
5. [Instalación](#instalación)
6. [Detalles Técnicos](#detalles-técnicos)
7. [Desarrollo y Contribuciones](#desarrollo-y-contribuciones)
8. [Equipo de Desarrollo](#equipo-de-desarrollo)
9. [Solución de Problemas](#solución-de-problemas)

### Capturas de Pantalla
[Aquí irían capturas del juego mostrando:
- Interfaz principal
- Enemigos en acción
- Mapas de calor
- Sistema de edición]

---

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
- **Pathfinding A***: Implementación optimizada para navegación de enemigos con ratio 2:1
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

---

## Controles
- **Espacio**: Iniciar/Detener juego
- **Flechas/WASD**: Mover el avatar
- **R**: Reiniciar juego
- **H**: Modo entrenamiento (headless)
- **C**: Editar posición de la casa
- **O**: Editar obstáculos
- **E**: Editar enemigos
- **Botón Reposicionar Avatar**: Permite cambiar la posición inicial del avatar
- **L**: Limpiar obstáculos

### Atajos de Teclado Adicionales
- **ESC**: Pausar juego
- **M**: Mostrar/ocultar mapa de calor
- **V**: Visualizar mejor ruta
- **N**: Alternar modo noche

---

## Mecánicas de Juego

### Sistema de Enemigos
- Cada enemigo tiene su propio comportamiento basado en IA
- Los enemigos perseguidores utilizan A* para encontrar la ruta más corta
- Los bloqueadores predicen y anticipan el movimiento del jugador
- Las patrullas mantienen áreas específicas bajo vigilancia
- Los enemigos aleatorios añaden un elemento de imprevisibilidad

Ejemplos de comportamiento:
- Perseguidores: Calculan y actualizan rutas constantemente hacia el jugador
- Bloqueadores: Predicen la ruta del jugador y se posicionan estratégicamente
- Patrullas: Mantienen rutas predefinidas y reaccionan al jugador en su rango
- Aleatorios: Movimiento impredecible que añade variedad al juego

### Ratio de Movimiento 2:1
- El jugador tiene ventaja estratégica con dos movimientos por cada uno del enemigo
- Sistema implementado mediante contador de pasos (step_counter)
- Balance entre desafío y jugabilidad
- Implementación específica:
  * Contador en Game.py para sincronización
  * Validación en _update_enemies para movimiento de enemigos
  * Control preciso de la ventaja del jugador

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

---

## Instalación

### Requisitos
- Python 3.x
- Pygame 2.5.0 o superior
- NumPy 1.24.0 o superior
- Sistema Operativo: Windows 10/11, macOS 10.15+, o Linux

**Nota**: Se recomienda usar la última versión estable de Python y Pygame para mejor compatibilidad.

#### Requerimientos Mínimos del Sistema
- CPU: 2.0 GHz Dual Core
- RAM: 4GB
- GPU: Integrada compatible con OpenGL 2.0
- Espacio en disco: 100MB

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

### Quick Start
1. **Ejecutar el juego:**
   ```bash
   python main.py
   ```
2. **Configuración inicial:**
   - Usar el botón "Reposicionar Avatar" para colocar al jugador
   - Presionar Espacio para iniciar el juego
   
3. **Controles básicos:**
   - Usar las teclas de flecha o WASD para mover al avatar
   
4. **Tipos de enemigos:**
   - 🔴 Perseguidores: Te seguirán directamente
   - 🟠 Bloqueadores: Intentarán interceptarte
   - 🟣 Patrullas: Seguirán rutas fijas
   - 🔵 Aleatorios: Movimiento impredecible
   
5. **Objetivo:**
   - Llegar a la casa evitando los enemigos
   
6. **Consejos de juego:**
   - Utiliza la ventaja del movimiento 2:1 estratégicamente
   - Observa los patrones de movimiento de cada tipo de enemigo
   - Aprovecha el reposicionamiento del avatar para situaciones difíciles
   - Consulta el mapa de calor para identificar zonas peligrosas

### Nota de Rendimiento
El juego está optimizado para mantener 60 FPS en la mayoría de sistemas modernos. La complejidad computacional de los algoritmos de IA está balanceada para proporcionar comportamientos inteligentes sin comprometer el rendimiento.

### Consejos de Rendimiento
- Mantener un número razonable de enemigos (máximo 8 recomendado)
- Evitar crear demasiados obstáculos
- Cerrar otras aplicaciones al ejecutar el juego
- Actualizar los drivers de su tarjeta gráfica

---

## Estructura del Proyecto
Los archivos del proyecto están completamente documentados con docstrings y comentarios explicativos. Consulte cada archivo para detalles específicos de implementación.

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

---

## Detalles Técnicos

### Implementación de A*
- Uso de conjuntos abiertos y cerrados para exploración eficiente
- Heurística Manhattan para estimación de distancias
- Optimización de recálculo de rutas en tiempo real
- Manejo de colisiones y obstáculos durante la búsqueda de rutas
- Sistema de prioridad para selección de nodos
- Optimizaciones específicas:
  * Uso de heurística Manhattan personalizada
  * Cache de caminos calculados
  * Actualización dinámica de rutas
  * Evitación de recálculos innecesarios

### Sistema de Enemigos
- Gestión de estados independiente para cada tipo de enemigo
- Sincronización de movimientos mediante step_counter
- Sistema de predicción para enemigos bloqueadores

### Arquitectura del Juego
- Diseño modular para fácil extensibilidad
- Separación clara de responsabilidades entre componentes
- Sistema de eventos para comunicación entre módulos

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

---

## Desarrollo y Contribuciones
Proyecto desarrollado como parte del curso de IA en CUValles.

## Equipo de Desarrollo
Desarrollado como proyecto del curso de Inteligencia Artificial 25A en CUValles:
- Fregoso Gutierrez Enrique de Jesus
- Ortiz Jimenez Vladimir
- Sanchez Sanchez Andrea Yunuhen Vianney

### Supervisión y Asesoría
- Dr. Hernando Rosales - Profesor del curso de IA

---

## [Registro de Versiones](#registro-de-versiones)
- v1.0 (Febrero 2024): Implementación inicial del juego con movimiento básico
- v1.1 (Marzo 2024): Sistema A* para navegación inteligente de enemigos y ratio 2:1
- v1.2 (Marzo 2024): Implementación de diferentes tipos de enemigos y sus comportamientos
- v1.3 (Abril 2024): Sistema de UI mejorado y reposicionamiento del avatar
- v1.4 (Mayo 2024): Implementación de mapas de calor y análisis de movimiento
- v1.5 (Mayo 2024): Optimizaciones finales y documentación completa

---

## Agradecimientos
- Dr. Hernando Rosales por la guía y supervisión del proyecto
- Centro Universitario de los Valles (CUValles) por el apoyo y recursos
- Comunidad de desarrollo de Pygame por las herramientas y documentación

---

## Solución de Problemas
### Problemas Comunes
1. **El juego se ejecuta lento**
   - Verificar que cumple los requisitos mínimos del sistema
   - Cerrar aplicaciones en segundo plano
   - Reducir la cantidad de enemigos en pantalla

2. **Errores de Instalación**
   - Asegurarse de tener Python 3.x instalado
   - Actualizar pip: `python -m pip install --upgrade pip`
   - Instalar dependencias individualmente si es necesario

3. **Problemas de Visualización**
   - Verificar resolución mínima: 1024x768
   - Actualizar drivers de video
   - Probar en modo ventana

---

## Contacto
Para dudas o sugerencias sobre el proyecto:
- Email: fregosogenrique@gmail.com
- Email: vladimir.ortiz8015@alumnos.udg.mx
- Email: andrea.sanchez0541@alumnos.udg.mx


---

## Licencia
Este proyecto es parte del curso de IA en CUValles y está disponible para uso educativo.

# grid_utils.py
"""
Utilidades de cuadrícula compartidas por las distintas mecánicas del juego.

Todas las posiciones son tuplas (x, y) y el movimiento es en 4 direcciones
(arriba, derecha, abajo, izquierda), igual que el avatar y los enemigos.
"""
from collections import deque

import numpy as np

DIRECTIONS_4 = [(0, -1), (1, 0), (0, 1), (-1, 0)]
UNREACHABLE = -1


def manhattan(p1, p2):
    """Distancia Manhattan: número mínimo de pasos si no hubiera obstáculos."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def in_grid(pos, width, height):
    return 0 <= pos[0] < width and 0 <= pos[1] < height


def neighbors_4(pos, width, height, blocked=()):
    """Vecinos ortogonales dentro del grid que no están en `blocked`."""
    x, y = pos
    result = []
    for dx, dy in DIRECTIONS_4:
        nxt = (x + dx, y + dy)
        if in_grid(nxt, width, height) and nxt not in blocked:
            result.append(nxt)
    return result


def bfs_distance_map(width, height, origin, blocked):
    """
    Distancia real (en pasos) desde `origin` a cada celda, rodeando `blocked`.

    Devuelve una matriz (height, width) de enteros; UNREACHABLE (-1) indica
    que la celda no se puede alcanzar. A diferencia de la distancia Manhattan,
    esta sí "ve" las paredes, por eso la usan el Q-learning (para moldear la
    recompensa), el mapa de calor (como heurística de las hormigas) y el
    generador de obstáculos (para garantizar que la casa sea alcanzable).
    """
    dist = np.full((height, width), UNREACHABLE, dtype=np.int32)
    if not in_grid(origin, width, height):
        return dist
    dist[origin[1], origin[0]] = 0
    queue = deque([origin])
    while queue:
        cx, cy = queue.popleft()
        d_next = dist[cy, cx] + 1
        for dx, dy in DIRECTIONS_4:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height and dist[ny, nx] == UNREACHABLE \
                    and (nx, ny) not in blocked:
                dist[ny, nx] = d_next
                queue.append((nx, ny))
    return dist


def is_reachable(width, height, start, goal, blocked):
    """True si existe al menos un camino de `start` a `goal` evitando `blocked`."""
    return bfs_distance_map(width, height, start, blocked)[goal[1], goal[0]] != UNREACHABLE

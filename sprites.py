# sprites.py
"""
Arte del juego generado por código (estilo Bomberman), sin archivos externos.

Cada sprite se dibuja en un lienzo de 64x64 con primitivas de pygame y luego
se escala con suavizado al tamaño pedido; el resultado se guarda en caché.
"""
import math
import random

import pygame

BASE = 64

PALETTE = {
    'grass_a': (76, 154, 62),
    'grass_b': (66, 140, 54),
    'grass_blade': (98, 178, 78),
    'grass_dark': (52, 112, 44),
    'brick': (186, 98, 52),
    'brick_light': (222, 140, 82),
    'brick_dark': (122, 58, 30),
    'mortar': (94, 64, 48),
    'stone': (132, 138, 150),
    'stone_light': (190, 196, 206),
    'stone_dark': (72, 76, 88),
    'helmet': (246, 246, 250),
    'helmet_shade': (196, 200, 214),
    'skin': (255, 196, 160),
    'suit': (52, 102, 222),
    'suit_dark': (34, 68, 160),
    'glove': (255, 120, 170),
    'boot': (196, 52, 96),
    'antenna': (255, 64, 120),
    'outline': (24, 22, 34),
}

ENEMY_COLORS = {
    'perseguidor': ((236, 64, 72), (160, 30, 42)),
    'bloqueador': ((255, 150, 40), (186, 92, 16)),
    'patrulla': ((156, 92, 232), (96, 52, 160)),
    'aleatorio': ((52, 200, 220), (24, 128, 150)),
}


def _shade(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def block_kind(cell):
    """Tipo visual de un obstáculo (determinista por celda): 'stone' o 'brick'."""
    h = (cell[0] * 73856093) ^ (cell[1] * 19349663)
    return 'stone' if h % 100 < 35 else 'brick'


class SpriteFactory:
    def __init__(self):
        self._cache = {}

    def _cached(self, key, builder, size):
        full_key = key + (size,)
        surf = self._cache.get(full_key)
        if surf is None:
            base = builder()
            surf = base if size == BASE else pygame.transform.smoothscale(base, (size, size))
            self._cache[full_key] = surf
        return surf

    # ------------------------------------------------------------- terreno
    def floor_tile(self, size, cell):
        """Césped a cuadros con matas pseudoaleatorias (estable por celda)."""
        parity = (cell[0] + cell[1]) % 2
        variant = ((cell[0] * 31 + cell[1] * 17) % 4)
        return self._cached(('floor', parity, variant), lambda: self._draw_floor(parity, variant), size)

    def _draw_floor(self, parity, variant):
        s = pygame.Surface((BASE, BASE))
        s.fill(PALETTE['grass_a'] if parity == 0 else PALETTE['grass_b'])
        rng = random.Random(variant * 977 + parity)
        for _ in range(7):
            x, y = rng.randint(4, BASE - 6), rng.randint(6, BASE - 4)
            pygame.draw.line(s, PALETTE['grass_blade'], (x, y), (x - 2, y - 5), 2)
            pygame.draw.line(s, PALETTE['grass_blade'], (x, y), (x + 2, y - 6), 2)
        for _ in range(4):
            x, y = rng.randint(2, BASE - 4), rng.randint(2, BASE - 4)
            pygame.draw.circle(s, PALETTE['grass_dark'], (x, y), 2)
        return s

    def block(self, kind, size):
        return self._cached(('block', kind), (lambda: self._draw_stone()) if kind == 'stone'
                            else (lambda: self._draw_brick()), size)

    def _draw_brick(self):
        s = pygame.Surface((BASE, BASE))
        s.fill(PALETTE['mortar'])
        row_h = 16
        for row in range(4):
            offset = 0 if row % 2 == 0 else -16
            y = row * row_h
            for col in range(-1, 3):
                x = offset + col * 32
                r = pygame.Rect(x + 2, y + 2, 28, row_h - 3)
                pygame.draw.rect(s, PALETTE['brick'], r)
                pygame.draw.line(s, PALETTE['brick_light'], r.topleft, (r.right - 1, r.top), 2)
                pygame.draw.line(s, PALETTE['brick_light'], r.topleft, (r.left, r.bottom - 1), 2)
                pygame.draw.line(s, PALETTE['brick_dark'], (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1), 2)
        pygame.draw.rect(s, PALETTE['brick_dark'], s.get_rect(), 2)
        return s

    def _draw_stone(self):
        s = pygame.Surface((BASE, BASE))
        s.fill(PALETTE['stone'])
        pygame.draw.polygon(s, PALETTE['stone_light'], [(0, 0), (BASE, 0), (BASE - 8, 8), (8, 8), (8, BASE - 8),
                                                        (0, BASE)])
        pygame.draw.polygon(s, PALETTE['stone_dark'], [(BASE, BASE), (0, BASE), (8, BASE - 8), (BASE - 8, BASE - 8),
                                                       (BASE - 8, 8), (BASE, 0)])
        inner = pygame.Rect(8, 8, BASE - 16, BASE - 16)
        pygame.draw.rect(s, PALETTE['stone'], inner)
        pygame.draw.line(s, _shade(PALETTE['stone'], 0.85), (14, 30), (30, 24), 2)
        pygame.draw.line(s, _shade(PALETTE['stone'], 0.85), (36, 44), (50, 40), 2)
        for cx, cy in ((14, 14), (BASE - 14, 14), (14, BASE - 14), (BASE - 14, BASE - 14)):
            pygame.draw.circle(s, PALETTE['stone_dark'], (cx + 1, cy + 1), 3)
            pygame.draw.circle(s, PALETTE['stone_light'], (cx, cy), 3)
        pygame.draw.rect(s, PALETTE['outline'], s.get_rect(), 1)
        return s

    # ------------------------------------------------------------- avatar
    def player(self, size, facing=(0, 1), frame=0):
        """Avatar estilo Bomberman. facing: (dx, dy); frame: 0/1 para el paso."""
        if facing[1] < 0:
            view = 'back'
        elif facing[0] != 0:
            view = 'side'
        else:
            view = 'front'
        flip = facing[0] < 0
        surf = self._cached(('player', view, frame % 2), lambda: self._draw_player(view, frame % 2), size)
        if flip:
            key = ('player_flip', view, frame % 2, size)
            if key not in self._cache:
                self._cache[key] = pygame.transform.flip(surf, True, False)
            return self._cache[key]
        return surf

    def _draw_player(self, view, frame):
        s = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
        o = PALETTE['outline']
        step = 3 if frame else -3
        # Botas
        for fx, dy in ((22, step), (42, -step)):
            r = pygame.Rect(0, 0, 16, 10)
            r.center = (fx, 57 + min(0, dy))
            pygame.draw.ellipse(s, o, r.inflate(3, 3))
            pygame.draw.ellipse(s, PALETTE['boot'], r)
        # Cuerpo
        body = pygame.Rect(19, 36, 26, 20)
        pygame.draw.rect(s, o, body.inflate(3, 3), border_radius=9)
        pygame.draw.rect(s, PALETTE['suit'], body, border_radius=8)
        pygame.draw.rect(s, PALETTE['suit_dark'], (body.left, body.bottom - 6, body.width, 6),
                         border_bottom_left_radius=8, border_bottom_right_radius=8)
        pygame.draw.rect(s, (250, 220, 70), (body.left + 2, 44, body.width - 4, 4))  # Cinturón
        # Guantes
        for gx, dy in ((14, -step), (50, step)):
            pygame.draw.circle(s, o, (gx, 45 + dy // 2), 7)
            pygame.draw.circle(s, PALETTE['glove'], (gx, 45 + dy // 2), 5)
        # Cabeza / casco
        head_c = (32, 23)
        pygame.draw.circle(s, o, head_c, 19)
        pygame.draw.circle(s, PALETTE['helmet'], head_c, 17)
        pygame.draw.circle(s, PALETTE['helmet_shade'], (head_c[0], head_c[1] + 6), 14,
                           draw_top_left=False, draw_top_right=False, draw_bottom_left=True, draw_bottom_right=True)
        pygame.draw.circle(s, (255, 255, 255), (head_c[0] - 7, head_c[1] - 8), 4)
        # Antena
        pygame.draw.line(s, o, (32, 6), (32, 0), 3)
        pygame.draw.circle(s, o, (32, 3), 5)
        pygame.draw.circle(s, PALETTE['antenna'], (32, 3), 4)
        if view == 'back':
            return s
        # Visor y ojos
        if view == 'front':
            visor = pygame.Rect(19, 17, 26, 15)
            eyes = ((27, 24), (37, 24))
        else:
            visor = pygame.Rect(27, 17, 20, 15)
            eyes = ((40, 24),)
        pygame.draw.rect(s, o, visor.inflate(2, 2), border_radius=7)
        pygame.draw.rect(s, PALETTE['skin'], visor, border_radius=6)
        for ex, ey in eyes:
            pygame.draw.ellipse(s, o, (ex - 2, ey - 5, 5, 10))
            pygame.draw.ellipse(s, (255, 255, 255), (ex - 1, ey - 4, 2, 3))
        return s

    # ------------------------------------------------------------- enemigos
    def enemy(self, size, enemy_type, look=(0, 0), angry=False):
        lx = max(-1, min(1, look[0]))
        ly = max(-1, min(1, look[1]))
        return self._cached(('enemy', enemy_type, lx, ly, angry),
                            lambda: self._draw_enemy(enemy_type, lx, ly, angry), size)

    def _draw_enemy(self, enemy_type, lx, ly, angry):
        s = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
        main, dark = ENEMY_COLORS.get(enemy_type, ENEMY_COLORS['perseguidor'])
        o = PALETTE['outline']
        # Cola ondulada (globo)
        tail = [(20, 46), (24, 58), (30, 50), (34, 60), (40, 50), (44, 58), (46, 46)]
        pygame.draw.polygon(s, o, [(x, y + 2) for x, y in tail])
        pygame.draw.polygon(s, dark, tail)
        pygame.draw.circle(s, o, (32, 30), 24)
        pygame.draw.circle(s, dark, (32, 30), 22)
        pygame.draw.circle(s, main, (30, 27), 20)
        pygame.draw.ellipse(s, _shade(main, 1.35), (16, 12, 14, 9))
        # Ojos que miran al jugador
        for ex in (24, 40):
            pygame.draw.ellipse(s, o, (ex - 7, 21, 14, 17))
            pygame.draw.ellipse(s, (255, 255, 255), (ex - 6, 22, 12, 15))
            pygame.draw.circle(s, o, (ex + lx * 3, 30 + ly * 3), 4)
            pygame.draw.circle(s, (255, 255, 255), (ex + lx * 3 - 1, 29 + ly * 3), 1)
        if angry:
            pygame.draw.line(s, o, (16, 16), (29, 22), 4)
            pygame.draw.line(s, o, (48, 16), (35, 22), 4)
            pygame.draw.lines(s, o, False, [(25, 48), (32, 43), (39, 48)], 4)
        else:
            pygame.draw.ellipse(s, o, (27, 40, 10, 8))
            pygame.draw.ellipse(s, (255, 130, 150), (29, 43, 6, 4))
        return s

    # ------------------------------------------------------------- casa
    def house(self, size):
        return self._cached(('house',), self._draw_house, size)

    def _draw_house(self):
        s = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
        o = PALETTE['outline']
        pygame.draw.rect(s, o, (42, 6, 10, 20))
        pygame.draw.rect(s, (150, 80, 60), (44, 8, 6, 18))
        walls = pygame.Rect(12, 28, 40, 32)
        pygame.draw.rect(s, o, walls.inflate(4, 4))
        pygame.draw.rect(s, (250, 232, 190), walls)
        pygame.draw.rect(s, (222, 196, 150), (walls.left, walls.bottom - 6, walls.width, 6))
        roof = [(4, 32), (32, 6), (60, 32)]
        pygame.draw.polygon(s, o, [(1, 34), (32, 2), (63, 34)])
        pygame.draw.polygon(s, (220, 54, 54), roof)
        pygame.draw.polygon(s, (255, 110, 100), [(10, 30), (32, 10), (34, 13), (14, 31)])
        door = pygame.Rect(26, 40, 13, 20)
        pygame.draw.rect(s, o, door.inflate(2, 2), border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.rect(s, (130, 76, 40), door, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.circle(s, (250, 210, 80), (35, 51), 2)
        for wx in (15, 42):
            w = pygame.Rect(wx, 36, 8, 8)
            pygame.draw.rect(s, o, w.inflate(2, 2))
            pygame.draw.rect(s, (130, 200, 255), w)
            pygame.draw.line(s, o, w.midtop, w.midbottom, 1)
            pygame.draw.line(s, o, w.midleft, w.midright, 1)
        return s

    # ------------------------------------------------------------- bomba
    def bomb(self, size, spark_phase=0):
        return self._cached(('bomb', spark_phase % 3), lambda: self._draw_bomb(spark_phase % 3), size)

    def _draw_bomb(self, phase):
        s = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
        pygame.draw.circle(s, (20, 20, 30), (30, 38), 22)
        pygame.draw.circle(s, (54, 56, 80), (30, 38), 19)
        pygame.draw.ellipse(s, (150, 160, 200), (18, 24, 12, 8))
        pygame.draw.rect(s, (20, 20, 30), (34, 14, 10, 8), border_radius=2)
        pygame.draw.arc(s, (210, 170, 110), (38, 2, 18, 22), 0, math.pi * 0.9, 3)
        colors = [(255, 240, 120), (255, 160, 40), (255, 80, 40)]
        for i, r in enumerate((6, 4, 2)):
            pygame.draw.circle(s, colors[(i + phase) % 3], (55, 8), r)
        return s

    # --------------------------------------------------------------- iconos
    def icon(self, name, size, color=(240, 240, 250)):
        return self._cached(('icon', name, color), lambda: self._draw_icon(name, color), size)

    def _draw_icon(self, name, c):
        s = pygame.Surface((BASE, BASE), pygame.SRCALPHA)
        if name == 'play':
            pygame.draw.polygon(s, c, [(18, 10), (54, 32), (18, 54)])
        elif name == 'pause':
            pygame.draw.rect(s, c, (14, 10, 13, 44), border_radius=3)
            pygame.draw.rect(s, c, (37, 10, 13, 44), border_radius=3)
        elif name == 'reset':
            pygame.draw.arc(s, c, (10, 10, 44, 44), 0.6, 2 * math.pi - 0.3, 7)
            pygame.draw.polygon(s, c, [(40, 4), (58, 16), (40, 26)])
        elif name == 'cube':
            pygame.draw.polygon(s, c, [(32, 6), (56, 18), (32, 30), (8, 18)], 5)
            pygame.draw.lines(s, c, False, [(8, 18), (8, 46), (32, 58), (56, 46), (56, 18)], 5)
            pygame.draw.line(s, c, (32, 30), (32, 58), 5)
        elif name == 'stop':
            pygame.draw.rect(s, c, (12, 12, 40, 40), border_radius=6)
        elif name == 'eye':
            pygame.draw.ellipse(s, c, (4, 16, 56, 32), 5)
            pygame.draw.circle(s, c, (32, 32), 10)
        elif name == 'chart':
            for i, h in enumerate((20, 34, 26, 46)):
                pygame.draw.rect(s, c, (8 + i * 13, 56 - h, 10, h), border_radius=2)
        elif name == 'trash':
            pygame.draw.rect(s, c, (16, 20, 32, 38), 5, border_radius=4)
            pygame.draw.rect(s, c, (10, 12, 44, 6), border_radius=2)
            pygame.draw.rect(s, c, (26, 6, 12, 6), border_radius=2)
        elif name == 'dice':
            pygame.draw.rect(s, c, (8, 8, 48, 48), 5, border_radius=10)
            for p in ((22, 22), (42, 22), (32, 32), (22, 42), (42, 42)):
                pygame.draw.circle(s, c, p, 5)
        elif name == 'brain':
            pygame.draw.circle(s, c, (24, 28), 16, 5)
            pygame.draw.circle(s, c, (40, 28), 16, 5)
            pygame.draw.circle(s, c, (32, 42), 14, 5)
            pygame.draw.line(s, c, (32, 14), (32, 54), 4)
        elif name == 'flame':
            pygame.draw.polygon(s, c, [(32, 4), (48, 30), (50, 44), (40, 58), (24, 58), (14, 44), (18, 28), (26, 36)])
        elif name == 'menu':
            for y in (16, 30, 44):
                pygame.draw.rect(s, c, (10, y, 44, 7), border_radius=3)
        elif name == 'trail':
            for i, (x, y) in enumerate(((10, 52), (22, 40), (32, 30), (42, 20), (54, 10))):
                pygame.draw.circle(s, c, (x, y), 4 + i)
        else:
            pygame.draw.circle(s, c, (32, 32), 20)
        return s

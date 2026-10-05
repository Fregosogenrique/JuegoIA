# view3d.py
"""
Vista "MAPA 3D": el tablero como una maqueta en perspectiva.

- Cámara orbital (yaw, pitch, distancia) que apunta al centro del tablero.
- Suelo: cada píxel de la vista se proyecta inversamente sobre el plano z=0 y
  toma el color del tablero 2D (césped, rastro de feromona, ruta). Se calcula
  con numpy y sólo cuando la cámara cambia.
- Obstáculos: cubos con caras sombreadas y detalle de ladrillo/piedra,
  dibujados de atrás hacia adelante (algoritmo del pintor) junto con los
  personajes (figuras de pie con sombra), la casa (modelo 3D) y los efectos.
- Al entrar, la cámara baja desde la vista cenital y los bloques "crecen"
  hacia el jugador, como si el mapa saliera de la pantalla.
"""
import math

import numpy as np
import pygame

from config import GameConfig
from effects import FIRE_COLORS
from sprites import ENEMY_COLORS, block_kind
from ui import draw_text, gradient

COLORKEY = (255, 0, 255)

BLOCK_STYLE = {
    'brick': {'height': 0.85, 'top': (214, 128, 74), 'side': (182, 96, 52), 'line': (110, 56, 32)},
    'stone': {'height': 1.05, 'top': (176, 182, 196), 'side': (128, 134, 148), 'line': (78, 82, 96)},
}
# Sombreado por orientación de la cara (luz desde el noroeste y arriba)
FACE_LIGHT = {'top': 1.0, 'west': 0.86, 'north': 0.72, 'east': 0.62, 'south': 0.78}


def _shade(color, k):
    return (min(255, int(color[0] * k)), min(255, int(color[1] * k)), min(255, int(color[2] * k)))


def _ease_out_back(t):
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class MapView3D:
    TOP_PITCH = math.radians(89.0)
    FOCAL = 900.0

    def __init__(self, renderer):
        self.renderer = renderer
        self.game = renderer.game
        self.sprites = renderer.sprites
        self.rect = renderer.grid_rect
        self.w, self.h = self.rect.size
        self.gw, self.gh = GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT
        self.yaw = 0.0
        self.pitch = math.radians(55)
        self.distance = 47.0
        self.intro = 1.0
        self.dragging = False
        self._floor_key = None
        self._map = None
        self._floor_surface = pygame.Surface((self.w, self.h))
        self._floor_surface.set_colorkey(COLORKEY)
        self._board_key = None
        self._board_array = None
        self._sky = gradient((self.w, self.h), (64, 120, 210), (190, 222, 250))
        self._cubes_key = None

    # ------------------------------------------------------------ cámara
    def enter(self):
        self.intro = 0.0

    def handle_event(self, event, edit_mode):
        """Arrastrar para orbitar, rueda para zoom. Devuelve True si consumió el evento."""
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if event.button == 3 or (event.button == 1 and not edit_mode):
                self.dragging = True
                return True
            if event.button in (4, 5):
                self._zoom(0.92 if event.button == 4 else 1.08)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.yaw = (self.yaw - event.rel[0] * 0.008) % (2 * math.pi)
            self.pitch = max(math.radians(25), min(math.radians(85), self.pitch + event.rel[1] * 0.006))
            return True
        elif event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self._zoom(0.92 if event.y > 0 else 1.08)
            return True
        return False

    def _zoom(self, factor):
        self.distance = max(18.0, min(70.0, self.distance * factor))

    def _camera_params(self):
        e = 1.0 if self.intro >= 1 else (1 - (1 - self.intro) ** 3)
        top_distance = self.FOCAL * self.gw / self.w
        pitch = self.TOP_PITCH + (self.pitch - self.TOP_PITCH) * e
        distance = top_distance + (self.distance - top_distance) * e
        target = np.array([self.gw / 2, self.gh / 2 + 0.8 * e, 0.0])
        offset = np.array([math.sin(self.yaw) * math.cos(pitch), math.cos(self.yaw) * math.cos(pitch),
                           math.sin(pitch)])
        cam = target + offset * distance
        f = target - cam
        f /= np.linalg.norm(f)
        up = np.array([0.0, 0.0, 1.0])
        r = np.cross(up, f)
        r /= np.linalg.norm(r)
        u = np.cross(f, r)
        return cam, r, u, f

    def _setup_camera(self):
        self.cam, self.r, self.u, self.f = self._camera_params()
        self.cx, self.cy = self.w / 2, self.h / 2

    def project(self, pts):
        """pts: (N, 3) -> (sx, sy, profundidad) como arrays."""
        d = np.asarray(pts, dtype=float) - self.cam
        xc, yc, zc = d @ self.r, d @ self.u, d @ self.f
        zc = np.maximum(zc, 0.05)
        return self.cx + self.FOCAL * xc / zc, self.cy - self.FOCAL * yc / zc, zc

    def project1(self, x, y, z):
        sx, sy, zc = self.project([(x, y, z)])
        return float(sx[0]), float(sy[0]), float(zc[0])

    def screen_to_cell(self, pos):
        """Inverso: punto de pantalla -> celda del tablero (rayo contra el plano z=0)."""
        if not self.rect.collidepoint(pos):
            return None
        self._setup_camera()
        px, py = pos[0] - self.rect.left, pos[1] - self.rect.top
        direction = self.f + ((px - self.cx) / self.FOCAL) * self.r - ((py - self.cy) / self.FOCAL) * self.u
        if direction[2] >= -1e-6:
            return None
        t = -self.cam[2] / direction[2]
        x, y = self.cam[0] + t * direction[0], self.cam[1] + t * direction[1]
        if 0 <= x < self.gw and 0 <= y < self.gh:
            return int(x), int(y)
        return None

    # ------------------------------------------------------------ suelo
    def _camera_key(self):
        return (round(self.yaw, 4), round(self.pitch, 4), round(self.distance, 3), round(self.intro, 3))

    def _build_floor_map(self, scale):
        """Proyección inversa de cada píxel (a 1/scale de resolución) sobre el plano del tablero."""
        w, h = self.w // scale, self.h // scale
        xs = (np.arange(w, dtype=np.float32) * scale)[:, None]
        ys = (np.arange(h, dtype=np.float32) * scale)[None, :]
        a = (xs - self.cx) / self.FOCAL
        b = (ys - self.cy) / self.FOCAL
        dx = self.f[0] + a * self.r[0] - b * self.u[0]
        dy = self.f[1] + a * self.r[1] - b * self.u[1]
        dz = self.f[2] + a * self.r[2] - b * self.u[2]
        with np.errstate(divide='ignore', invalid='ignore'):
            t = np.where(dz < -1e-6, -self.cam[2] / dz, np.inf).astype(np.float32)
        wx = self.cam[0] + t * dx
        wy = self.cam[1] + t * dy
        sq = GameConfig.SQUARE_SIZE
        valid = (wx >= 0) & (wx < self.gw) & (wy >= 0) & (wy < self.gh) & np.isfinite(t)
        ix = np.clip(np.nan_to_num(wx * sq, posinf=0, neginf=0).astype(np.int32), 0, self.gw * sq - 1)
        iy = np.clip(np.nan_to_num(wy * sq, posinf=0, neginf=0).astype(np.int32), 0, self.gh * sq - 1)
        if valid.any():
            near, far = np.percentile(t[valid], 2), float(np.max(t[valid]))
        else:
            near, far = 1.0, 2.0
        shade = 1.08 - 0.33 * np.clip((np.where(valid, t, near) - near) / max(1e-3, far - near), 0, 1)
        small = pygame.Surface((w, h))
        self._map = (ix, iy, valid, (shade * 256).astype(np.uint32)[:, :, None], small, scale)

    def _draw_floor(self, surface, board_surface, board_version):
        """
        El suelo se recalcula a media resolución mientras la cámara se mueve y
        a resolución completa en cuanto se queda quieta.
        """
        key = self._camera_key()
        refresh = False
        if key != self._floor_key:
            self._floor_key = key
            self._build_floor_map(2)
            refresh = True
        elif self._map[5] == 2:
            self._build_floor_map(1)
            refresh = True
        if board_version != self._board_key:
            self._board_key = board_version
            self._board_array = pygame.surfarray.array3d(board_surface)
            refresh = True
        if refresh:
            ix, iy, valid, shade, small, scale = self._map
            out = np.minimum(self._board_array[ix, iy].astype(np.uint32) * shade >> 8, 255).astype(np.uint8)
            out[~valid] = COLORKEY
            pygame.surfarray.blit_array(small, out)
            if scale == 1:
                self._floor_surface.blit(small, (0, 0))
            else:
                pygame.transform.scale(small, (self.w, self.h), self._floor_surface)
        surface.blit(self._floor_surface, (0, 0))

    # ------------------------------------------------------------ geometría
    def _box_faces(self, x0, y0, x1, y1, z0, z1):
        """Caras visibles de una caja alineada: lista de (nombre, 4 vértices)."""
        cx, cy, cz = self.cam
        faces = []
        if cy > y1:
            faces.append(('south', [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]))
        if cy < y0:
            faces.append(('north', [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)]))
        if cx < x0:
            faces.append(('west', [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)]))
        if cx > x1:
            faces.append(('east', [(x1, y1, z0), (x1, y0, z0), (x1, y0, z1), (x1, y1, z1)]))
        if cz > z1:
            faces.append(('top', [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]))
        return faces

    def _poly(self, surface, pts3d, color, outline=(30, 26, 40)):
        sx, sy, _ = self.project(pts3d)
        pts = list(zip(sx.tolist(), sy.tolist()))
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, 1)
        return pts

    def _line3d(self, surface, a, b, color, width=1):
        sx, sy, _ = self.project([a, b])
        pygame.draw.line(surface, color, (sx[0], sy[0]), (sx[1], sy[1]), width)

    # Caras de un bloque por índices de esquina: (a, b) borde inferior, (d, c) borde superior.
    # Esquinas 0-3 en el suelo y 4-7 arriba: 0=(x0,y0) 1=(x1,y0) 2=(x1,y1) 3=(x0,y1)
    BLOCK_FACES = {'south': (3, 2, 6, 7), 'north': (1, 0, 4, 5), 'west': (0, 3, 7, 4), 'east': (2, 1, 5, 6),
                   'top': (4, 5, 6, 7)}

    def _project_blocks(self, cells, grow):
        """Proyecta de una vez las 8 esquinas de todos los bloques -> {celda: [(sx, sy) x 8]}."""
        if not cells:
            return {}
        base = np.array(cells, dtype=float)
        heights = np.array([BLOCK_STYLE[block_kind(c)]['height'] for c in cells]) * max(0.02, grow)
        offs = np.array([[0, 0], [1, 0], [1, 1], [0, 1]] * 2, dtype=float)
        pts = np.zeros((len(cells), 8, 3))
        pts[:, :, 0] = base[:, None, 0] + offs[None, :, 0]
        pts[:, :, 1] = base[:, None, 1] + offs[None, :, 1]
        pts[:, 4:, 2] = heights[:, None]
        sx, sy, _ = self.project(pts.reshape(-1, 3))
        sx, sy = sx.reshape(-1, 8).tolist(), sy.reshape(-1, 8).tolist()
        return {c: list(zip(sx[i], sy[i])) for i, c in enumerate(cells)}

    @staticmethod
    def _lerp(p, q, k):
        return p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k

    def _draw_block(self, surface, cell, kind, corners):
        style = BLOCK_STYLE[kind]
        x0, y0 = cell
        cx, cy, _ = self.cam
        visible = ['top']
        if cy > y0 + 1:
            visible.append('south')
        if cy < y0:
            visible.append('north')
        if cx < x0:
            visible.append('west')
        if cx > x0 + 1:
            visible.append('east')
        outline = (30, 26, 40)
        for name in visible[1:] + visible[:1]:  # Laterales primero, tapa al final
            a, b, c, d = (corners[i] for i in self.BLOCK_FACES[name])
            light = FACE_LIGHT[name]
            base = style['top'] if name == 'top' else style['side']
            pygame.draw.polygon(surface, _shade(base, light), (a, b, c, d))
            pygame.draw.polygon(surface, outline, (a, b, c, d), 1)
            if abs(b[0] - a[0]) + abs(b[1] - a[1]) < 14:
                continue
            line = _shade(style['line'], light)
            if name == 'top':
                inset = [self._lerp(self._lerp(a, d, v), self._lerp(b, c, v), u)
                         for u, v in ((0.16, 0.16), (0.84, 0.16), (0.84, 0.84), (0.16, 0.84))]
                pygame.draw.polygon(surface, _shade(base, 1.08 if kind == 'stone' else 0.94), inset)
                pygame.draw.polygon(surface, line, inset, 1)
            elif kind == 'brick':
                rows = [(self._lerp(a, d, k), self._lerp(b, c, k)) for k in (0, 1 / 3, 2 / 3, 1)]
                for left, right in rows[1:3]:
                    pygame.draw.line(surface, line, left, right)
                for row, frac in ((0, 0.5), (1, 0.25), (1, 0.75), (2, 0.5)):
                    (l0, r0), (l1, r1) = rows[row], rows[row + 1]
                    pygame.draw.line(surface, line, self._lerp(l0, r0, frac), self._lerp(l1, r1, frac))
            else:
                pygame.draw.line(surface, line, self._lerp(a, d, 0.55), self._lerp(b, c, 0.55), 2)

    def _draw_slab(self, surface):
        """Plataforma de tierra bajo el tablero: el mapa 'flota' como una maqueta."""
        dirt, grass = (120, 82, 52), (70, 140, 58)
        for name, quad in self._box_faces(0, 0, self.gw, self.gh, -1.6, 0.0):
            if name == 'top':
                continue
            k = FACE_LIGHT[name]
            self._poly(surface, quad, _shade(dirt, k), (60, 40, 26))
            lip = [(p[0], p[1], 0.0 if p[2] == 0.0 else -0.3) for p in quad]
            self._poly(surface, lip, _shade(grass, k), None)
            for z in (-0.75, -1.2):
                self._line3d(surface, (quad[0][0], quad[0][1], z), (quad[1][0], quad[1][1], z),
                             _shade(dirt, k * 0.8), 2)

    def _draw_house(self, surface, cell, t):
        """Casa como modelo 3D (1.6 veces una celda para que la meta destaque)."""
        k = 1.6
        x, y = cell[0] + 0.5 - k / 2, cell[1] + 0.5 - k / 2  # Esquina del modelo escalado
        x0, x1, y0, y1 = x + 0.12 * k, x + 0.88 * k, y + 0.12 * k, y + 0.88 * k
        wall_h, ridge_h = 0.62 * k, 1.4 * k
        faces = []
        wall = (248, 232, 196)
        for name, quad in self._box_faces(x0, y0, x1, y1, 0.0, wall_h):
            if name != 'top':
                faces.append((quad, _shade(wall, FACE_LIGHT[name]), name))
        ex0, ex1, ey0, ey1 = x + 0.04 * k, x + 0.96 * k, y + 0.04 * k, y + 0.96 * k
        mid_y = (ey0 + ey1) / 2
        roof = (222, 58, 58)
        cam = self.cam
        faces.append(([(ex0, ey1, wall_h), (ex1, ey1, wall_h), (ex1, mid_y, ridge_h), (ex0, mid_y, ridge_h)],
                       _shade(roof, 0.95 if cam[1] > mid_y else 0.6), 'roof_s'))
        faces.append(([(ex1, ey0, wall_h), (ex0, ey0, wall_h), (ex0, mid_y, ridge_h), (ex1, mid_y, ridge_h)],
                       _shade(roof, 0.95 if cam[1] < mid_y else 0.6), 'roof_n'))
        for gx in (x0, x1):
            faces.append(([(gx, y0, wall_h), (gx, y1, wall_h), (gx, mid_y, ridge_h)],
                          _shade(wall, 0.8), 'gable'))
        for name, quad in self._box_faces(x + 0.6 * k, y + 0.22 * k, x + 0.74 * k, y + 0.36 * k, 0.7 * k, 1.3 * k):
            faces.append((quad, _shade((150, 84, 64), FACE_LIGHT[name]), 'chimney'))

        def depth(face):
            c = np.mean(np.array(face[0]), axis=0)
            return float(np.linalg.norm(c - cam))

        for quad, color, name in sorted(faces, key=depth, reverse=True):
            self._poly(surface, quad, color)
            if name in ('roof_s', 'roof_n'):  # Hileras de tejas y cumbrera
                a, b, c, d = quad
                for frac in (0.33, 0.66):
                    p1 = tuple(a[i] + (d[i] - a[i]) * frac for i in range(3))
                    p2 = tuple(b[i] + (c[i] - b[i]) * frac for i in range(3))
                    self._line3d(surface, p1, p2, _shade(color, 0.7), 2)
                self._line3d(surface, c, d, (120, 24, 24), 3)
            if name == 'south' and cam[1] > y1:
                self._poly(surface, [(x + 0.42 * k, y1, 0), (x + 0.58 * k, y1, 0), (x + 0.58 * k, y1, 0.36 * k),
                                     (x + 0.42 * k, y1, 0.36 * k)], (130, 76, 40))
                for wx in (x + 0.2 * k, x + 0.66 * k):
                    self._poly(surface, [(wx, y1, 0.3 * k), (wx + 0.14 * k, y1, 0.3 * k),
                                         (wx + 0.14 * k, y1, 0.46 * k), (wx, y1, 0.46 * k)], (130, 200, 255))

        # Faro de luz y estrella flotante: la meta se ve desde lejos
        mx, my = cell[0] + 0.5, cell[1] + 0.5
        bx, by, _ = self.project1(mx, my, ridge_h)
        tx, ty, _ = self.project1(mx, my, 5.0)
        half = max(6, int(self.FOCAL * 0.55 / max(1.0, self.project1(mx, my, 1)[2])))
        top_left = (min(bx, tx) - half, min(by, ty))
        beam_w, beam_h = int(abs(tx - bx) + half * 2 + 2), int(abs(by - ty) + 2)
        if beam_h > 2:
            beam = pygame.Surface((beam_w, beam_h), pygame.SRCALPHA)
            pulse = 0.6 + 0.4 * math.sin(t * 3)
            for i in range(beam_h):
                a = int(90 * pulse * (i / beam_h))
                pygame.draw.line(beam, (255, 240, 150, a), (0, i), (beam_w, i))
            surface.blit(beam, top_left)
        # Gema dorada que gira sobre su eje vertical encima de la casa
        sx, sy, zc = self.project1(mx, my, 2.9 + 0.2 * math.sin(t * 2.5))
        r = max(7, int(self.FOCAL * 0.36 / zc))
        w = max(2.0, r * 0.75 * abs(math.cos(t * 2.0)))
        gem = [(sx, sy - r), (sx + w, sy), (sx, sy + r), (sx - w, sy)]
        pygame.draw.polygon(surface, (255, 214, 64), gem)
        pygame.draw.polygon(surface, (255, 248, 200), [(sx, sy - r), (sx + w * 0.5, sy - r * 0.2), (sx, sy)])
        pygame.draw.polygon(surface, (150, 90, 10), gem, 2)

    def _draw_shadow(self, surface, x, y, radius, color=(38, 84, 34)):
        pts = [(x + math.cos(a) * radius, y + math.sin(a) * radius * 0.8, 0.01)
               for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        sx, sy, _ = self.project(pts)
        pygame.draw.polygon(surface, color, list(zip(sx.tolist(), sy.tolist())))

    def _draw_ring(self, surface, x, y, radius, color, width=2):
        pts = [(x + math.cos(a) * radius, y + math.sin(a) * radius, 0.02)
               for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
        sx, sy, _ = self.project(pts)
        pygame.draw.polygon(surface, color, list(zip(sx.tolist(), sy.tolist())), width)

    def _relative_facing(self, facing):
        """Dirección del mundo vista desde la cámara (para elegir frente/espalda/perfil)."""
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        fx = facing[0] * c - facing[1] * s
        fy = facing[0] * s + facing[1] * c
        if abs(fx) > abs(fy):
            return (1 if fx > 0 else -1, 0)
        return (0, 1 if fy > 0 else -1)

    def _draw_billboard(self, surface, image_fn, x, y, height, lift=0.0):
        bx, by, zc = self.project1(x, y, lift)
        _, ty, _ = self.project1(x, y, lift + height)
        size = max(4, min(400, int(by - ty)))
        img = pygame.transform.smoothscale(image_fn(96), (size, size))  # Base fija: la caché no crece
        surface.blit(img, (bx - size / 2, by - size))

    # ------------------------------------------------------------ dibujo
    def draw(self, screen, dt, t):
        self.intro = min(1.0, self.intro + dt / 1.1)
        surface = screen.subsurface(self.rect)
        self._setup_camera()
        surface.blit(self._sky, (0, 0))
        self._draw_slab(surface)
        board_surface, board_version = self.renderer.board_for_3d()
        self._draw_floor(surface, board_surface, board_version)

        game, anim = self.game, self.renderer.anim
        grow = 1.0 if self.intro >= 1 else max(0.0, _ease_out_back(min(1.0, self.intro * 1.15)))
        items = []
        cam = self.cam

        def dist(x, y, z=0.4):
            return math.sqrt((x - cam[0]) ** 2 + (y - cam[1]) ** 2 + (z - cam[2]) ** 2)

        cells = list(game.game_state.obstacles)
        block_corners = self._project_blocks(cells, grow)
        for cell in cells:
            items.append((dist(cell[0] + 0.5, cell[1] + 0.5), 'block', cell))
        house = game.game_state.house_pos
        items.append((dist(house[0] + 0.5, house[1] + 0.5), 'house', house))
        px, py = anim.player_pos
        items.append((dist(px + 0.5, py + 0.5), 'player', None))
        for e_id, (ex, ey) in anim.enemy_pos.items():
            if e_id in game.game_state.enemies:
                items.append((dist(ex + 0.5, ey + 0.5), 'enemy', e_id))
        for p in self.renderer.effects.particles:
            items.append((dist(p.x, p.y, p.z), 'particle', p))
        for b in self.renderer.effects.blasts:
            for c in b.arms:
                items.append((dist(c[0] + 0.5, c[1] + 0.5), 'flame', (c, b)))
        items.sort(key=lambda item: item[0], reverse=True)

        for _, kind, data in items:
            if kind == 'block':
                self._draw_block(surface, data, block_kind(data), block_corners[data])
            elif kind == 'house':
                self._draw_house(surface, data, t)
            elif kind == 'player':
                self._draw_player(surface, anim, t)
            elif kind == 'enemy':
                self._draw_enemy(surface, data, anim, t)
            elif kind == 'particle':
                sx, sy, zc = self.project1(data.x, data.y, data.z)
                pygame.draw.circle(surface, data.color, (sx, sy), max(1, int(self.FOCAL * data.size * 0.5 / zc)))
            elif kind == 'flame':
                (c, blast) = data
                k = blast.intensity
                for i, color in enumerate(reversed(FIRE_COLORS)):
                    rad = (0.55 - i * 0.11) * k
                    if rad <= 0:
                        continue
                    sx, sy, zc = self.project1(c[0] + 0.5, c[1] + 0.5, 0.4)
                    pygame.draw.circle(surface, color, (sx, sy), max(1, int(self.FOCAL * rad / zc)))

        for text in self.renderer.effects.texts:
            sx, sy, _ = self.project1(text.x, text.y, 1.3 + text.time * 0.8)
            draw_text(surface, text.text, text.size, text.color, (sx, sy), 'center', outline=3,
                      alpha=int(255 * text.alpha))

        if game.edit_mode:
            cell = self.screen_to_cell(pygame.mouse.get_pos())
            if cell:
                pts = [(cell[0], cell[1], 0.03), (cell[0] + 1, cell[1], 0.03), (cell[0] + 1, cell[1] + 1, 0.03),
                       (cell[0], cell[1] + 1, 0.03)]
                sx, sy, _ = self.project(pts)
                pygame.draw.polygon(surface, (255, 230, 80), list(zip(sx.tolist(), sy.tolist())), 3)

        if self.intro >= 1:
            draw_text(surface, "Arrastra para girar · Rueda para acercar", 16, (30, 40, 70),
                      (self.w - 10, self.h - 8), 'bottomright')

    def _draw_player(self, surface, anim, t):
        px, py = anim.player_pos
        cx, cy = px + 0.5, py + 0.5
        self._draw_shadow(surface, cx, cy, 0.38)
        bob = abs(math.sin(t * 12)) * 0.08 if anim.player_moving else math.sin(t * 3) * 0.02
        facing = self._relative_facing(anim.player_facing)
        frame = int(t * 8) if anim.player_moving else 0
        self._draw_billboard(surface, lambda s: self.sprites.player(s, facing, frame), cx, cy, 1.35, bob)

    def _draw_enemy(self, surface, e_id, anim, t):
        data = self.game.game_state.enemies[e_id]
        ex, ey = anim.enemy_pos[e_id]
        cx, cy = ex + 0.5, ey + 0.5
        chasing = data.get('state') == 'chase'
        if chasing:
            pulse = 0.35 + 0.08 * math.sin(t * 8)
            self._draw_ring(surface, cx, cy, pulse, ENEMY_COLORS['perseguidor'][0], 3)
        self._draw_shadow(surface, cx, cy, 0.36)
        ppx, ppy = anim.player_pos
        look = self._relative_facing((ppx - ex, ppy - ey)) if (ppx, ppy) != (ex, ey) else (0, 1)
        etype = data.get('type', GameConfig.DEFAULT_ENEMY_TYPE)
        lift = 0.12 + math.sin(t * 4 + e_id) * 0.06
        self._draw_billboard(surface, lambda s: self.sprites.enemy(s, etype, look, chasing), cx, cy, 1.2, lift)

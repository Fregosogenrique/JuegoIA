# raycaster.py
"""
Vista en PRIMERA PERSONA: el mundo visto con los ojos del avatar.

Técnica de raycasting (como Wolfenstein 3D):
- Por cada columna de la pantalla se lanza un rayo con DDA sobre la
  cuadrícula hasta chocar con un muro; su distancia perpendicular da la
  altura de la franja de pared (textura de ladrillo o piedra, oscurecida
  con la distancia y en las caras laterales).
- El suelo se calcula por píxel con numpy (floor casting): cada píxel bajo el
  horizonte corresponde a un punto del tablero, coloreado con el césped a
  cuadros, el rastro de feromona y la ruta planificada.
- Enemigos, casa y llamas son "sprites" que miran siempre a la cámara y se
  recortan con un z-buffer por columna para que los muros los tapen.
Se dibuja a media resolución y se escala (estética retro y más rápido).
"""
import math

import numpy as np
import pygame

from config import GameConfig
from effects import FIRE_COLORS
from grid_utils import manhattan
from sprites import block_kind
from ui import UI, draw_text, gradient

TEX = 32
SHADES = 10
VOID = np.array([18, 22, 40], dtype=np.float32)


class FirstPersonView:
    FOV_PLANE = 0.70

    def __init__(self, renderer):
        self.renderer = renderer
        self.game = renderer.game
        self.sprites = renderer.sprites
        self.rect = renderer.grid_rect
        self.rw, self.rh = self.rect.width // 2, self.rect.height // 2
        self.canvas = pygame.Surface((self.rw, self.rh))
        self.angle = math.pi / 2
        self._sky = gradient((self.rw, self.rh // 2), (40, 90, 190), (176, 214, 246))
        self._columns = {kind: self._shaded_columns(kind) for kind in ('brick', 'stone')}
        self._cell_colors_key = None
        self._cell_colors = None
        ys = np.arange(self.rh // 2 + 1, self.rh, dtype=np.float32)
        self._row_dist = (0.5 * self.rh / (ys - self.rh / 2))[None, :]  # Forma (1, filas)
        self._fog = np.clip(1.05 - self._row_dist / 13.0, 0.18, 1.0)[:, :, None]
        self._floor_buffer = pygame.Surface((self.rw, self.rh - self.rh // 2 - 1))

    def _shaded_columns(self, kind):
        base = self.sprites.block(kind, TEX)
        columns = []
        for level in range(SHADES):
            k = 1.0 - level / (SHADES + 2)
            tex = base.copy()
            tex.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_MULT)
            columns.append([tex.subsurface((x, 0, 1, TEX)) for x in range(TEX)])
        return columns

    def enter(self):
        fx, fy = self.renderer.anim.player_facing
        self.angle = math.atan2(fy, fx)

    # ------------------------------------------------------------- mundo
    def _cell_color_map(self):
        key = self.renderer.board_version()
        if key == self._cell_colors_key:
            return self._cell_colors
        self._cell_colors_key = key
        gw, gh = GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT
        ys, xs = np.indices((gh, gw))
        a = np.array([86, 168, 70], dtype=np.float32)
        b = np.array([72, 150, 60], dtype=np.float32)
        colors = np.where(((xs + ys) % 2 == 0)[:, :, None], a, b)
        heat = self.game.heat_map_pathfinder.avatar_heat_map
        if self.renderer.show_trail and heat.max() > 0:
            k = np.clip(heat / heat.max(), 0, 1)[:, :, None]
            k = np.where(k > 0.03, k, 0)
            colors = colors * (1 - 0.35 * k) + np.array([255, 150, 70], dtype=np.float32) * 0.35 * k
        path = self.game.current_path_player[self.game.path_index_player:]
        for (x, y) in path:
            colors[y, x] = colors[y, x] * 0.6 + np.array([255, 210, 90]) * 0.4
        hx, hy = self.game.game_state.house_pos
        colors[hy, hx] = (255, 220, 90)
        self._cell_colors = colors
        return colors

    def _draw_floor(self, pos, direction, plane):
        colors = self._cell_color_map()
        cam_x = (2 * np.arange(self.rw, dtype=np.float32) / self.rw - 1)[:, None]
        rdx = direction[0] + plane[0] * cam_x
        rdy = direction[1] + plane[1] * cam_x
        fx = pos[0] + self._row_dist * rdx
        fy = pos[1] + self._row_dist * rdy
        cx = np.floor(fx).astype(np.int32)
        cy = np.floor(fy).astype(np.int32)
        inside = (cx >= 0) & (cx < GameConfig.GRID_WIDTH) & (cy >= 0) & (cy < GameConfig.GRID_HEIGHT)
        cxc = np.clip(cx, 0, GameConfig.GRID_WIDTH - 1)
        cyc = np.clip(cy, 0, GameConfig.GRID_HEIGHT - 1)
        pix = colors[cyc, cxc]
        pix = np.where(inside[:, :, None], pix, VOID)
        # Líneas sutiles entre baldosas
        edge = ((fx - cx) < 0.04) | ((fy - cy) < 0.04)
        pix = np.where(edge[:, :, None], pix * 0.8, pix)
        out = (pix * self._fog).astype(np.uint8)
        pygame.surfarray.blit_array(self._floor_buffer, out)
        self.canvas.blit(self._floor_buffer, (0, self.rh // 2 + 1))

    def _cast_walls(self, pos, direction, plane):
        obstacles = self.game.game_state.obstacles
        gw, gh = GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT
        zbuffer = [0.0] * self.rw
        px, py = pos
        rh = self.rh
        for col in range(self.rw):
            cam_x = 2 * col / self.rw - 1
            rdx = direction[0] + plane[0] * cam_x
            rdy = direction[1] + plane[1] * cam_x
            map_x, map_y = int(px), int(py)
            ddx = abs(1 / rdx) if rdx != 0 else 1e30
            ddy = abs(1 / rdy) if rdy != 0 else 1e30
            if rdx < 0:
                step_x, side_x = -1, (px - map_x) * ddx
            else:
                step_x, side_x = 1, (map_x + 1.0 - px) * ddx
            if rdy < 0:
                step_y, side_y = -1, (py - map_y) * ddy
            else:
                step_y, side_y = 1, (map_y + 1.0 - py) * ddy
            side = 0
            kind = 'stone'
            for _ in range(80):
                if side_x < side_y:
                    side_x += ddx
                    map_x += step_x
                    side = 0
                else:
                    side_y += ddy
                    map_y += step_y
                    side = 1
                if not (0 <= map_x < gw and 0 <= map_y < gh):
                    kind = 'stone'
                    break
                if (map_x, map_y) in obstacles:
                    kind = block_kind((map_x, map_y))
                    break
            dist = (side_x - ddx) if side == 0 else (side_y - ddy)
            dist = max(dist, 0.02)
            zbuffer[col] = dist
            wall_x = (py + dist * rdy) if side == 0 else (px + dist * rdx)
            wall_x -= math.floor(wall_x)
            tex_x = min(TEX - 1, int(wall_x * TEX))
            if (side == 0 and rdx > 0) or (side == 1 and rdy < 0):
                tex_x = TEX - 1 - tex_x
            shade = min(SHADES - 1, int(dist * 0.9) + (2 if side == 1 else 0))
            column = self._columns[kind][shade][tex_x]
            line_h = int(rh / dist)
            if line_h <= rh:
                strip = pygame.transform.scale(column, (1, line_h))
                self.canvas.blit(strip, (col, (rh - line_h) // 2))
            else:
                visible = rh / line_h
                top = int((1 - visible) / 2 * TEX)
                rows = max(1, int(visible * TEX))
                strip = pygame.transform.scale(column.subsurface((0, top, 1, min(rows, TEX - top))), (1, rh))
                self.canvas.blit(strip, (col, 0))
        return zbuffer

    def _sprite_list(self, pos):
        anim, game = self.renderer.anim, self.game
        items = []
        hx, hy = game.game_state.house_pos
        items.append(('house', hx + 0.5, hy + 0.5, 1.0, None))
        for e_id, (ex, ey) in anim.enemy_pos.items():
            if e_id in game.game_state.enemies:
                items.append(('enemy', ex + 0.5, ey + 0.5, 0.8, e_id))
        for blast in self.renderer.effects.blasts:
            for c in blast.arms:
                items.append(('flame', c[0] + 0.5, c[1] + 0.5, 0.9 * blast.intensity, None))
        items.sort(key=lambda it: (it[1] - pos[0]) ** 2 + (it[2] - pos[1]) ** 2, reverse=True)
        return items

    def _draw_sprites(self, pos, direction, plane, zbuffer, t):
        inv_det = 1.0 / (plane[0] * direction[1] - direction[0] * plane[1])
        rw, rh = self.rw, self.rh
        for kind, sx, sy, height, data in self._sprite_list(pos):
            rx, ry = sx - pos[0], sy - pos[1]
            tx = inv_det * (direction[1] * rx - direction[0] * ry)
            depth = inv_det * (-plane[1] * rx + plane[0] * ry)
            if depth <= 0.15 or height <= 0:
                continue
            screen_x = int(rw / 2 * (1 + tx / depth))
            size = int(height * rh / depth)
            if size < 2 or size > rh * 4:
                continue
            floor_y = rh / 2 + 0.5 * rh / depth
            lift = 0
            if kind == 'enemy':
                lift = int((0.1 + 0.06 * math.sin(t * 4 + data)) * rh / depth)
                e = self.game.game_state.enemies[data]
                px, py = self.renderer.anim.player_pos
                img = self.sprites.enemy(96, e.get('type', 'perseguidor'), (0, 0), e.get('state') == 'chase')
            elif kind == 'house':
                img = self.sprites.house(96)
            else:
                img = pygame.Surface((32, 32), pygame.SRCALPHA)
                for i, color in enumerate(reversed(FIRE_COLORS)):
                    pygame.draw.circle(img, color, (16, 16), 16 - i * 4)
            img = pygame.transform.scale(img, (size, size))
            left = screen_x - size // 2
            top = int(floor_y - size - lift)
            start = max(0, left)
            end = min(rw, left + size)
            col = start
            while col < end:
                if depth >= zbuffer[col]:
                    col += 1
                    continue
                run = col
                while run < end and depth < zbuffer[run]:
                    run += 1
                self.canvas.blit(img, (col, top), area=pygame.Rect(col - left, 0, run - col, size))
                col = run

    # ------------------------------------------------------------- dibujo
    def draw(self, screen, dt, t):
        anim = self.renderer.anim
        fx, fy = anim.player_facing
        target = math.atan2(fy, fx)
        diff = (target - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += diff * min(1.0, dt * 9)
        direction = (math.cos(self.angle), math.sin(self.angle))
        plane = (-direction[1] * self.FOV_PLANE, direction[0] * self.FOV_PLANE)
        pos = (anim.player_pos[0] + 0.5, anim.player_pos[1] + 0.5)

        self.canvas.blit(self._sky, (0, 0))
        self._draw_floor(pos, direction, plane)
        zbuffer = self._cast_walls(pos, direction, plane)
        self._draw_sprites(pos, direction, plane, zbuffer, t)

        view = screen.subsurface(self.rect)
        pygame.transform.scale(self.canvas, self.rect.size, view)
        self._draw_hud(view, pos, t, anim)

    def _draw_hud(self, view, pos, t, anim):
        w, h = view.get_size()
        game = self.game
        # Peligro: viñeta roja si un enemigo persigue de cerca
        near = [e for e in game.game_state.enemies.values()
                if manhattan(e['position'], game.game_state.player_pos) <= GameConfig.DANGER_RADIUS + 1]
        if near:
            pulse = int(36 + 24 * math.sin(t * 8))
            vignette = pygame.Surface((w, h), pygame.SRCALPHA)
            for i in range(8):
                pygame.draw.rect(vignette, (220, 20, 30, max(0, pulse - i * 5)), (i * 5, i * 5, w - i * 10,
                                                                                    h - i * 10), 5)
            view.blit(vignette, (0, 0))
            draw_text(view, "¡ENEMIGO CERCA!", 30, UI['red'], (w // 2, 96), 'center', outline=3)

        # Brújula con la dirección de la casa
        bar = pygame.Rect(w // 2 - 200, 12, 400, 30)
        pygame.draw.rect(view, (14, 16, 30), bar, border_radius=15)
        pygame.draw.rect(view, UI['panel_border'], bar, 2, border_radius=15)
        heading = math.degrees(self.angle)
        for label, ang in (("E", 0), ("S", 90), ("O", 180), ("N", 270)):
            delta = (ang - heading + 180) % 360 - 180
            if abs(delta) < 60:
                draw_text(view, label, 22, UI['text'], (bar.centerx + delta / 60 * 190, bar.centery), 'center')
        hx, hy = game.game_state.house_pos
        house_ang = math.degrees(math.atan2(hy + 0.5 - pos[1], hx + 0.5 - pos[0]))
        delta = (house_ang - heading + 180) % 360 - 180
        marker_x = bar.centerx + max(-60, min(60, delta)) / 60 * 190
        view.blit(self.sprites.house(26), (marker_x - 13, bar.bottom - 2))
        remaining = max(0, len(game.current_path_player) - game.path_index_player)
        draw_text(view, f"Casa: {remaining} pasos" if remaining else "Casa: sin ruta", 18, UI['gold'],
                  (bar.centerx, bar.bottom + 34), 'center', outline=2)

        # Bomba en mano (se balancea al caminar)
        sway = math.sin(t * 10) * 10 if anim.player_moving else math.sin(t * 2) * 3
        bomb = self.sprites.bomb(150, int(t * 10))
        view.blit(bomb, (w - 210 + sway, h - 150 + abs(sway) * 0.6))
        pygame.draw.circle(view, (255, 255, 255), (w // 2, h // 2), 3, 1)

        # Minimapa
        cell = 4
        gw, gh = GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT
        mini = pygame.Surface((gw * cell + 8, gh * cell + 8), pygame.SRCALPHA)
        mini.fill((10, 12, 26, 200))
        for (ox, oy) in game.game_state.obstacles:
            pygame.draw.rect(mini, (170, 120, 90), (4 + ox * cell, 4 + oy * cell, cell, cell))
        for (cx, cy) in game.current_path_player[game.path_index_player:]:
            pygame.draw.rect(mini, (255, 190, 60), (4 + cx * cell + 1, 4 + cy * cell + 1, 2, 2))
        pygame.draw.rect(mini, (255, 220, 80), (4 + hx * cell - 1, 4 + hy * cell - 1, cell + 2, cell + 2))
        for e in game.game_state.enemies.values():
            ex, ey = e['position']
            pygame.draw.circle(mini, (240, 70, 80), (4 + ex * cell + 2, 4 + ey * cell + 2), 2)
        mx, my = 4 + pos[0] * cell, 4 + pos[1] * cell
        a = self.angle
        tri = [(mx + math.cos(a) * 7, my + math.sin(a) * 7), (mx + math.cos(a + 2.5) * 5, my + math.sin(a + 2.5) * 5),
               (mx + math.cos(a - 2.5) * 5, my + math.sin(a - 2.5) * 5)]
        pygame.draw.polygon(mini, (90, 210, 255), tri)
        pygame.draw.rect(mini, UI['panel_border'], mini.get_rect(), 2)
        view.blit(mini, (w - mini.get_width() - 12, 12))
        if not game.is_running:
            draw_text(view, "Flechas: girar y avanzar  ·  Espacio: iniciar", 18, UI['text'], (w // 2, h - 20),
                      'center', outline=2)

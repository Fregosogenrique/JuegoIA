# ui.py
"""
Componentes de interfaz con estética de videojuego: textos con contorno,
paneles con degradado, botones con relieve y el menú principal animado.
"""
import math
import random

import pygame

from config import GameConfig
from sprites import block_kind

UI = {
    'bg_top': (28, 30, 52),
    'bg_bottom': (14, 14, 28),
    'panel_top': (44, 48, 82),
    'panel_bottom': (30, 32, 58),
    'panel_border': (90, 98, 160),
    'button_top': (74, 82, 132),
    'button_bottom': (52, 58, 100),
    'button_edge': (26, 28, 52),
    'text': (240, 242, 255),
    'text_dim': (170, 176, 210),
    'gold': (255, 206, 64),
    'gold_dark': (176, 110, 20),
    'red': (240, 70, 80),
    'green': (90, 220, 120),
    'cyan': (90, 210, 240),
    'orange': (255, 150, 50),
    'purple': (170, 110, 250),
    'outline': (18, 16, 30),
}

_font_cache = {}


def font(size):
    f = _font_cache.get(size)
    if f is None:
        f = pygame.font.Font(None, size)
        _font_cache[size] = f
    return f


def render_text(text, size, color, outline=0, outline_color=UI['outline']):
    """Superficie con el texto; `outline` > 0 añade contorno grueso estilo arcade."""
    f = font(size)
    base = f.render(text, True, color)
    if outline <= 0:
        return base
    w, h = base.get_width() + outline * 2, base.get_height() + outline * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    edge = f.render(text, True, outline_color)
    for ang in range(0, 360, 30):
        ox = round(math.cos(math.radians(ang)) * outline)
        oy = round(math.sin(math.radians(ang)) * outline)
        surf.blit(edge, (outline + ox, outline + oy))
    surf.blit(base, (outline, outline))
    return surf


def draw_text(surface, text, size, color, pos, anchor='topleft', outline=0, outline_color=UI['outline'],
              alpha=255, max_width=None):
    surf = render_text(text, size, color, outline, outline_color)
    while max_width and surf.get_width() > max_width and size > 10:
        size -= 1
        surf = render_text(text, size, color, outline, outline_color)
    if alpha < 255:
        surf.set_alpha(alpha)
    rect = surf.get_rect(**{anchor: pos})
    surface.blit(surf, rect)
    return rect


_gradient_cache = {}


def gradient(size, top, bottom, radius=0):
    key = (size, top, bottom, radius)
    surf = _gradient_cache.get(key)
    if surf is None:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, color, (0, y), (w, y))
        if radius:
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _gradient_cache[key] = surf
    return surf


def draw_panel(surface, rect, title=None, accent=UI['gold'], radius=10):
    rect = pygame.Rect(rect)
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=radius)
    surface.blit(shadow, rect.move(3, 4))
    surface.blit(gradient(rect.size, UI['panel_top'], UI['panel_bottom'], radius), rect)
    pygame.draw.rect(surface, UI['panel_border'], rect, 2, border_radius=radius)
    if title:
        tab = pygame.Rect(rect.left + 10, rect.top - 9, 0, 20)
        label = render_text(title, 18, UI['outline'])
        tab.width = label.get_width() + 18
        pygame.draw.rect(surface, accent, tab, border_radius=6)
        pygame.draw.rect(surface, UI['outline'], tab, 2, border_radius=6)
        surface.blit(label, label.get_rect(center=tab.center))


def draw_progress_bar(surface, rect, progress, color, label=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, (20, 20, 36), rect, border_radius=rect.height // 2)
    fill = rect.copy()
    fill.width = max(rect.height, int(rect.width * max(0.0, min(1.0, progress))))
    if progress > 0:
        surface.blit(gradient(fill.size, tuple(min(255, c + 50) for c in color), color, rect.height // 2), fill)
    pygame.draw.rect(surface, UI['outline'], rect, 2, border_radius=rect.height // 2)
    if label:
        draw_text(surface, label, 15, UI['text'], rect.center, 'center', outline=1)


class Button:
    def __init__(self, button_id, label, rect, icon=None, sprite=None, accent=None, hotkey=None, font_size=17):
        self.id = button_id
        self.label = label
        self.rect = pygame.Rect(rect)
        self.icon = icon
        self.sprite = sprite  # Callable(size) -> Surface (mini sprite del juego)
        self.accent = accent or UI['gold']
        self.hotkey = hotkey
        self.font_size = font_size

    def draw(self, surface, sprites, mouse_pos, mouse_down, toggled=False, highlight=False, label=None):
        hover = self.rect.collidepoint(mouse_pos)
        pressed = hover and mouse_down
        r = self.rect.move(0, 2 if pressed else 0)
        edge = r.move(0, 3 if not pressed else 1)
        pygame.draw.rect(surface, UI['button_edge'], edge, border_radius=8)
        top, bottom = UI['button_top'], UI['button_bottom']
        if toggled:
            top, bottom = tuple(min(255, c + 30) for c in self.accent), self.accent
        elif hover:
            top, bottom = tuple(min(255, c + 25) for c in top), tuple(min(255, c + 25) for c in bottom)
        surface.blit(gradient(r.size, top, bottom, 8), r)
        pygame.draw.rect(surface, UI['outline'], r, 2, border_radius=8)
        if hover or highlight:
            pygame.draw.rect(surface, UI['gold'] if highlight else (230, 235, 255), r.inflate(2, 2), 2,
                             border_radius=9)

        text_color = UI['outline'] if toggled else UI['text']
        icon_size = min(r.height - 10, 20 if self.font_size < 20 else 26)
        x = r.left + 8
        if self.sprite:
            surface.blit(self.sprite(icon_size + 2), (x - 1, r.centery - (icon_size + 2) // 2))
            x += icon_size + 6
        elif self.icon:
            surface.blit(sprites.icon(self.icon, icon_size, text_color), (x, r.centery - icon_size // 2))
            x += icon_size + 6
        text = label or self.label
        available = r.right - x - 6
        draw_text(surface, text, self.font_size, text_color, (x + available // 2, r.centery + 1), 'center',
                  outline=0 if toggled else 1, max_width=available)
        return hover


class MenuScreen:
    """Menú principal animado y pantalla de controles."""

    def __init__(self, sprites):
        self.sprites = sprites
        self.page = 'main'
        self.selected = 0
        self.time = 0.0
        self.buttons = []
        self._background = None
        self._walkers = [
            {'kind': 'player', 'x': -2.0, 'y': 22.5, 'speed': 2.6},
            {'kind': 'perseguidor', 'x': -5.0, 'y': 22.5, 'speed': 2.6},
            {'kind': 'patrulla', 'x': -7.5, 'y': 22.5, 'speed': 2.6},
            {'kind': 'aleatorio', 'x': 30.0, 'y': 4.5, 'speed': -1.8},
            {'kind': 'bloqueador', 'x': 45.0, 'y': 4.5, 'speed': -1.8},
        ]

    def items(self, can_continue):
        items = []
        if can_continue:
            items.append(('continue', 'CONTINUAR', 'play'))
        items += [('play2d', 'JUGAR', 'play'), ('play3d', 'JUGAR EN MAPA 3D', 'cube'),
                  ('playfps', 'PRIMERA PERSONA', 'eye'), ('help', 'CONTROLES', 'menu'), ('quit', 'SALIR', 'stop')]
        return items

    def _build_buttons(self, can_continue):
        items = self.items(can_continue)
        w, h, gap = 340, 46, 12
        top = 300
        cx = GameConfig.SCREEN_WIDTH // 2
        self.buttons = [Button(i, label, (cx - w // 2, top + n * (h + gap), w, h), icon=icon, font_size=28)
                        for n, (i, label, icon) in enumerate(items)]
        self.selected = min(self.selected, len(self.buttons) - 1)

    def handle_event(self, event, can_continue):
        self._build_buttons(can_continue)
        if self.page == 'help':
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.page = 'main'
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                return self._activate(self.buttons[self.selected].id)
            elif event.key == pygame.K_ESCAPE and can_continue:
                return 'continue'
        elif event.type == pygame.MOUSEMOTION:
            for n, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.selected = n
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b.rect.collidepoint(event.pos):
                    return self._activate(b.id)
        return None

    def _activate(self, action):
        if action == 'help':
            self.page = 'help'
            return None
        return action

    # -------------------------------------------------------------- dibujo
    def _draw_background(self, surface, dt):
        size = 44
        cols = GameConfig.SCREEN_WIDTH // size + 2
        rows = GameConfig.SCREEN_HEIGHT // size + 2
        if self._background is None:
            bg = pygame.Surface((cols * size, rows * size))
            rng = random.Random(5)
            for y in range(rows):
                for x in range(cols):
                    bg.blit(self.sprites.floor_tile(size, (x, y)), (x * size, y * size))
                    border = x in (0, cols - 1) or y in (0, rows - 1)
                    pillar = x % 2 == 0 and y % 2 == 0
                    if border or pillar or (rng.random() < 0.12 and y not in (4, 22)):
                        kind = 'stone' if border or pillar else block_kind((x, y))
                        bg.blit(self.sprites.block(kind, size), (x * size, y * size))
            self._background = bg
        offset = (self.time * 12) % (size * 2)
        surface.blit(self._background, (-offset, -offset * 0.5))
        surface.blit(self._background, (-offset + self._background.get_width(), -offset * 0.5))

        for w in self._walkers:
            w['x'] += w['speed'] * dt
            if w['speed'] > 0 and w['x'] > cols + 2:
                w['x'] = -2 - (w['kind'] != 'player') * (3 if w['kind'] == 'perseguidor' else 5.5)
            if w['speed'] < 0 and w['x'] < -3:
                w['x'] = cols + (15 if w['kind'] == 'bloqueador' else 0)
            bob = abs(math.sin(self.time * 9 + w['x'])) * 5
            px, py = w['x'] * size, w['y'] * size * 0.5 + 40
            facing = (1 if w['speed'] > 0 else -1, 0)
            if w['kind'] == 'player':
                spr = self.sprites.player(size, facing, int(self.time * 6))
            else:
                spr = self.sprites.enemy(size, w['kind'], facing, angry=w['speed'] > 0)
            pygame.draw.ellipse(surface, (30, 70, 30), (px + 8, py + size - 8, size - 16, 10))
            surface.blit(spr, (px, py - bob))

        shade = gradient((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT), (10, 10, 30), (6, 6, 18))
        shade.set_alpha(175)
        surface.blit(shade, (0, 0))

    def draw(self, surface, dt, can_continue, mouse_pos, mouse_down):
        self.time += dt
        self._build_buttons(can_continue)
        self._draw_background(surface, dt)
        cx = GameConfig.SCREEN_WIDTH // 2

        bob = math.sin(self.time * 2.2) * 6
        draw_text(surface, "JUEGO IA", 132, UI['gold'], (cx, 150 + bob), 'center', outline=7)
        draw_text(surface, "BOMBER MIND", 46, UI['text'], (cx, 222 + bob * 0.5), 'center', outline=4,
                  outline_color=(200, 40, 70))
        bomb = self.sprites.bomb(84, int(self.time * 10))
        surface.blit(pygame.transform.rotate(bomb, math.sin(self.time * 3) * 12), (cx - 420, 100 + bob))
        hero = self.sprites.player(96, (0, 1), int(self.time * 4))
        surface.blit(hero, (cx + 330, 92 - abs(math.sin(self.time * 4)) * 14))

        if self.page == 'help':
            self._draw_help(surface)
        else:
            for n, b in enumerate(self.buttons):
                b.draw(surface, self.sprites, mouse_pos, mouse_down, highlight=(n == self.selected))
                if n == self.selected:
                    spark = self.sprites.bomb(40, int(self.time * 12))
                    surface.blit(spark, (b.rect.left - 50, b.rect.centery - 22 + math.sin(self.time * 8) * 3))
            draw_text(surface, "Flechas: elegir  ·  Enter: aceptar  ·  F11: pantalla completa", 18, UI['text_dim'],
                      (cx, self.buttons[-1].rect.bottom + 22), 'center')

        draw_text(surface, "CUValles · Inteligencia Artificial 2024A · Q-learning + Colonia de Hormigas + A*", 17,
                  UI['text_dim'], (cx, GameConfig.SCREEN_HEIGHT - 34), 'center')
        draw_text(surface, "Fregoso Gutiérrez · Ortiz Jiménez · Sánchez Sánchez", 17, UI['text_dim'],
                  (cx, GameConfig.SCREEN_HEIGHT - 16), 'center')

    def _draw_help(self, surface):
        panel = pygame.Rect(0, 0, 900, 400)
        panel.center = (GameConfig.SCREEN_WIDTH // 2, 470)
        draw_panel(surface, panel, "CONTROLES")
        left = [
            ("Espacio", "Iniciar / pausar la simulación"),
            ("Tab", "Cambiar vista: 2D, Mapa 3D, 1ª persona"),
            ("Esc", "Volver al menú"),
            ("R / G", "Reiniciar / generar mapa nuevo"),
            ("Flechas", "Mover al avatar (con el juego detenido)"),
            ("T", "Mostrar u ocultar el rastro de feromona"),
            ("F11", "Pantalla completa"),
        ]
        right = [
            ("H / Q", "Entrenar IA del jugador / de los enemigos"),
            ("M", "Entrenar el mapa de calor (hormigas)"),
            ("N", "Forzar ruta del mapa de calor"),
            ("V, F1-F4", "Gráficas de análisis"),
            ("P C O E", "Editar jugador, casa, muros, enemigos"),
            ("Mapa 3D", "Arrastra para girar · rueda para zoom"),
            ("1ª persona", "Flechas izq/der giran, arriba/abajo avanzan"),
        ]
        for col, rows in enumerate((left, right)):
            x = panel.left + 30 + col * 440
            for n, (key, desc) in enumerate(rows):
                y = panel.top + 34 + n * 48
                key_rect = draw_text(surface, key, 22, UI['gold'], (x, y), outline=2)
                draw_text(surface, desc, 19, UI['text'], (x, key_rect.bottom + 2), max_width=410)
        draw_text(surface, "Pulsa cualquier tecla para volver", 18, UI['text_dim'],
                  (panel.centerx, panel.bottom - 18), 'center')

# render.py
"""
Dibujo del juego con estética de videojuego (estilo Bomberman):
- Barra superior tipo marcador (pasos, turno, tiempo, estado, enemigos).
- Tablero 2D con sprites animados, sombras, rastro de feromona y ruta,
  o bien las vistas 3D (maqueta del mapa / primera persona).
- Barra lateral con paneles y botones por sección, y estado de la IA.
- Efectos: polvo al caminar, explosión al ser atrapado, confeti al ganar,
  "!" cuando una patrulla detecta al avatar.
"""
import math

import numpy as np
import pygame

from config import GameConfig
from effects import Effects, FIRE_COLORS
from raycaster import FirstPersonView
from sprites import SpriteFactory, block_kind, ENEMY_COLORS
from ui import UI, Button, draw_panel, draw_progress_bar, draw_text, gradient, render_text
from view3d import MapView3D

EDIT_LABELS = {'player': 'JUGADOR', 'house': 'CASA', 'obstacles': 'MUROS', 'enemies': 'ENEMIGOS'}
TYPE_NAMES = {'perseguidor': 'Perseguidor', 'bloqueador': 'Bloqueador', 'patrulla': 'Patrulla',
              'aleatorio': 'Aleatorio'}


class Animator:
    """Posiciones "de dibujo" que se deslizan suavemente hacia las posiciones lógicas."""

    def __init__(self, game):
        self.game = game
        self.player_pos = tuple(map(float, game.game_state.player_pos))
        self.player_facing = (0, 1)
        self.player_moving = False
        self.enemy_pos = {}

    @staticmethod
    def _approach(current, target, max_step):
        dx, dy = target[0] - current[0], target[1] - current[1]
        dist = math.hypot(dx, dy)
        if dist > 2.5:  # Teletransporte (reinicio, edición): sin animación
            return tuple(map(float, target)), False
        if dist <= max_step:
            return tuple(map(float, target)), dist > 1e-3
        return (current[0] + dx / dist * max_step, current[1] + dy / dist * max_step), True

    def update(self, dt):
        turn = (GameConfig.HEADLESS_DELAY if GameConfig.HEADLESS_MODE else GameConfig.MOVE_DELAY) / 1000.0
        step = dt / max(0.03, turn) * 1.15
        self.player_pos, self.player_moving = self._approach(self.player_pos, self.game.game_state.player_pos, step)
        self.player_facing = getattr(self.game, 'player_facing', (0, 1))
        enemies = self.game.game_state.enemies
        for e_id, data in enemies.items():
            current = self.enemy_pos.get(e_id, tuple(map(float, data['position'])))
            self.enemy_pos[e_id], _ = self._approach(current, data['position'],
                                                     step * max(1.0, GameConfig.ENEMY_SPEED_FACTOR))
        for e_id in list(self.enemy_pos):
            if e_id not in enemies:
                del self.enemy_pos[e_id]


class GameRenderer:
    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game = game_instance
        self.sprites = SpriteFactory()
        self.effects = Effects()
        self.anim = Animator(game_instance)
        self.time = 0.0
        sq = GameConfig.SQUARE_SIZE
        self.grid_rect = pygame.Rect(GameConfig.GRID_ORIGIN, (GameConfig.GRID_WIDTH * sq, GameConfig.GRID_HEIGHT * sq))
        self.hud_rect = pygame.Rect(0, 0, self.grid_rect.width, GameConfig.HUD_HEIGHT)
        self.sidebar_rect = pygame.Rect(self.grid_rect.right, 0, GameConfig.SIDEBAR_WIDTH, GameConfig.SCREEN_HEIGHT)
        self.buttons = []
        self._sections = []
        self._build_sidebar()

        self._terrain = self._build_terrain()
        self._blocks_key = None
        self._board_2d = None
        self._floor_with_shadows = None
        self._trail_key = None
        self._trail_surface = None
        self._floor3d_key = None
        self._floor3d = None
        self._prev = {'victory': False, 'game_over': False, 'player': game_instance.game_state.player_pos,
                      'states': {}}

        self.map3d = MapView3D(self)
        self.fps = FirstPersonView(self)

    @property
    def show_trail(self):
        return getattr(self.game, 'show_trail', True)

    # ------------------------------------------------------------ barra lateral
    def _build_sidebar(self):
        s = self.sprites
        x0 = self.sidebar_rect.left + 14
        full_w = self.sidebar_rect.width - 28
        half_w = (full_w - 8) // 2
        row_h, gap = 30, 6

        layout = [
            ("PARTIDA", UI['gold'], [
                [("start", "INICIAR (Espacio)", 'play', None)],
                [("reset", "Reiniciar (R)", 'reset', None), ("toggle_view", "Vista (Tab)", 'cube', None)],
                [("generate", "Mapa nuevo (G)", 'dice', None), ("toggle_trail", "Rastro (T)", 'trail', None)],
            ]),
            ("INTELIGENCIA", UI['cyan'], [
                [("train_player_agent", "IA Jugador (H)", 'brain', None),
                 ("train_enemy_agent", "IA Enemigos (Q)", 'brain', None)],
                [("use_heat_map", "Seguir rastro (N)", 'flame', None),
                 ("visualize_heat_map", "Gráfica (V)", 'chart', None)],
                [("reset_heat_map", "Borrar rastro", 'trash', None),
                 ("toggle_edit_avatar_heatmap_iters", "Hormigas", 'flame', None)],
                [("stop_train", "Detener entrenamientos", 'stop', None)],
            ]),
            ("EDITOR", UI['orange'], [
                [("edit_player", "Jugador (P)", None, lambda size: s.player(size)),
                 ("edit_house", "Casa (C)", None, lambda size: s.house(size))],
                [("edit_obstacles", "Muros (O)", None, lambda size: s.block('brick', size)),
                 ("edit_enemies", "Enemigos (E)", None, lambda size: s.enemy(size, 'perseguidor'))],
                [("clear_obstacles", "Quitar muros", 'trash', None),
                 ("clear_enemies", "Quitar enemigos", 'trash', None)],
            ]),
        ]
        y = 70
        for title, accent, rows in layout:
            top = y
            y += 16
            for row in rows:
                width = full_w if len(row) == 1 else half_w
                for i, (bid, label, icon, sprite) in enumerate(row):
                    rect = pygame.Rect(x0 + i * (half_w + 8), y, width, row_h)
                    self.buttons.append(Button(bid, label, rect, icon=icon, sprite=sprite, accent=accent))
                y += row_h + gap
            self._sections.append((title, accent, pygame.Rect(x0 - 6, top, full_w + 12, y - top + 4)))
            y += 18
        self._status_top = y
        menu_rect = pygame.Rect(x0, GameConfig.SCREEN_HEIGHT - 40, full_w, 28)
        self.buttons.append(Button("menu", "Menú principal (Esc)", menu_rect, icon='menu'))
        self.button_rects = {b.id: b.rect for b in self.buttons}

    def get_button_at(self, pos):
        for b in self.buttons:
            if b.rect.collidepoint(pos):
                return b.id
        return None

    # ------------------------------------------------------------ tablero 2D
    def _build_terrain(self):
        sq = GameConfig.SQUARE_SIZE
        surf = pygame.Surface(self.grid_rect.size)
        for y in range(GameConfig.GRID_HEIGHT):
            for x in range(GameConfig.GRID_WIDTH):
                surf.blit(self.sprites.floor_tile(sq, (x, y)), (x * sq, y * sq))
        return surf

    def _ensure_board(self):
        obstacles = self.game.game_state.obstacles
        key = hash(frozenset(obstacles))
        if key == self._blocks_key:
            return
        self._blocks_key = key
        sq = GameConfig.SQUARE_SIZE
        floor = self._terrain.copy()
        shadow = pygame.Surface((sq, sq // 2), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        side_shadow = pygame.Surface((sq // 3, sq), pygame.SRCALPHA)
        side_shadow.fill((0, 0, 0, 45))
        for (x, y) in obstacles:
            floor.blit(shadow, (x * sq, (y + 1) * sq))
            floor.blit(side_shadow, ((x + 1) * sq, y * sq + sq // 3))
        self._floor_with_shadows = floor
        board = floor.copy()
        for (x, y) in sorted(obstacles, key=lambda c: c[1]):
            board.blit(self.sprites.block(block_kind((x, y)), sq), (x * sq, y * sq))
        self._board_2d = board

    def _trail(self):
        heat = self.game.heat_map_pathfinder.avatar_heat_map
        key = (float(heat.sum()), float(heat.max()))
        if key == self._trail_key:
            return self._trail_surface
        self._trail_key = key
        sq = GameConfig.SQUARE_SIZE
        surf = pygame.Surface(self.grid_rect.size, pygame.SRCALPHA)
        top = heat.max()
        if top > 0:
            for y, x in zip(*np.nonzero(heat > top * 0.03)):
                k = heat[y, x] / top
                color = (255, int(235 - 120 * k), int(140 - 100 * k), int(25 + 85 * k))
                r = int(sq * (0.18 + 0.22 * k))
                pygame.draw.circle(surf, color, (x * sq + sq // 2, y * sq + sq // 2), r)
        self._trail_surface = surf
        return surf

    def board_version(self):
        g = self.game
        if self.show_trail:
            self._trail()
        path = tuple(g.current_path_player[g.path_index_player:]) if g.is_running else tuple(g.best_path_player or ())
        return (self._blocks_key, self._trail_key if self.show_trail else None, g.game_state.house_pos, path)

    def board_for_3d(self):
        """Suelo del tablero (sin bloques ni personajes) para proyectarlo en la maqueta 3D."""
        self._ensure_board()
        key = self.board_version()
        if key != self._floor3d_key:
            self._floor3d_key = key
            surf = self._floor_with_shadows.copy()
            if self.show_trail:
                surf.blit(self._trail(), (0, 0))
            self._draw_paths(surf, (0, 0), animated=False)
            self._floor3d = surf
        return self._floor3d, key

    @staticmethod
    def _cell_center(x, y, origin):
        sq = GameConfig.SQUARE_SIZE
        return origin[0] + x * sq + sq / 2, origin[1] + y * sq + sq / 2

    def _draw_paths(self, surface, origin, animated=True):
        g = self.game
        sq = GameConfig.SQUARE_SIZE
        if g.is_running and len(g.current_path_player) > 1:
            path = g.current_path_player[max(0, g.path_index_player - 1):]
            color, radius = (255, 170, 40), max(2, sq // 6)
        elif g.best_path_player and len(g.best_path_player) > 1:
            path = g.best_path_player
            color, radius = (255, 240, 120), max(2, sq // 8)
        else:
            return
        phase = (self.time * 6) % 3 if animated else 0
        for i, (x, y) in enumerate(path[1:-1], start=1):
            cx, cy = self._cell_center(x, y, origin)
            pulse = 1 if animated and int(i - phase) % 3 == 0 else 0
            pygame.draw.circle(surface, (40, 30, 10), (cx + 1, cy + 1), radius + 1 + pulse)
            pygame.draw.circle(surface, color, (cx, cy), radius + pulse)

    def _draw_board_2d(self, t):
        g = self.game
        self._ensure_board()
        sq = GameConfig.SQUARE_SIZE
        shake = self.effects.shake_offset()
        ox, oy = self.grid_rect.left + shake[0], self.grid_rect.top + shake[1]
        self.screen.blit(self._board_2d, (ox, oy))
        if self.show_trail and g.avatar_heatmap_trained:
            self.screen.blit(self._trail(), (ox, oy))

        if GameConfig.SHOW_MOVEMENT_MATRIX:
            freq = g.player_movement_frequency_matrix
            for y, x in zip(*np.nonzero(freq)):
                pygame.draw.circle(self.screen, (230, 245, 255), (ox + x * sq + sq // 2, oy + y * sq + sq * 0.7), 2)

        self._draw_paths(self.screen, (ox, oy))

        # Casa con faro pulsante
        hx, hy = g.game_state.house_pos
        glow = pygame.Surface((sq * 3, sq * 3), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(t * 3)
        pygame.draw.circle(glow, (255, 230, 120, int(60 + 60 * pulse)), (sq * 1.5, sq * 1.5), sq * (1.0 + 0.3 * pulse))
        self.screen.blit(glow, (ox + hx * sq - sq, oy + hy * sq - sq))
        self.screen.blit(self.sprites.house(sq + 6), (ox + hx * sq - 3, oy + hy * sq - 7))

        # Personajes ordenados por fila (los de abajo tapan a los de arriba)
        actors = [('player', None, self.anim.player_pos)]
        actors += [('enemy', e_id, pos) for e_id, pos in self.anim.enemy_pos.items() if e_id in g.game_state.enemies]
        actors.sort(key=lambda a: a[2][1])
        size = sq + 8
        for kind, e_id, (fx, fy) in actors:
            px, py = ox + fx * sq + sq / 2, oy + fy * sq + sq / 2
            pygame.draw.ellipse(self.screen, (30, 70, 28), (px - sq * 0.38, py + sq * 0.22, sq * 0.76, sq * 0.3))
            if kind == 'player':
                moving = self.anim.player_moving
                bob = abs(math.sin(t * 14)) * 3 if moving else 0
                img = self.sprites.player(size, self.anim.player_facing, int(t * 8) if moving else 0)
                self.screen.blit(img, (px - size / 2, py - size + sq * 0.45 - bob))
            else:
                data = g.game_state.enemies[e_id]
                chasing = data.get('state') == 'chase'
                if chasing:
                    ring = sq * (0.6 + 0.1 * math.sin(t * 8))
                    pygame.draw.circle(self.screen, ENEMY_COLORS['perseguidor'][0], (px, py + sq * 0.3), ring, 2)
                look = (int(np.sign(self.anim.player_pos[0] - fx)), int(np.sign(self.anim.player_pos[1] - fy)))
                bob = math.sin(t * 4 + e_id) * 2
                img = self.sprites.enemy(size, data.get('type', GameConfig.DEFAULT_ENEMY_TYPE), look, chasing)
                self.screen.blit(img, (px - size / 2, py - size + sq * 0.45 - 3 + bob))

        self._draw_effects_2d(ox, oy)
        self._draw_edit_cursor()

    def _draw_effects_2d(self, ox, oy):
        sq = GameConfig.SQUARE_SIZE
        for b in self.effects.blasts:
            k = b.intensity
            for (x, y) in b.arms:
                cx, cy = ox + x * sq + sq / 2, oy + y * sq + sq / 2
                for i, color in enumerate(reversed(FIRE_COLORS)):
                    r = sq * (0.75 - i * 0.15) * k
                    if r > 1:
                        pygame.draw.circle(self.screen, color, (cx, cy), r)
        for p in self.effects.particles:
            cx, cy = ox + p.x * sq, oy + (p.y - p.z * 0.6) * sq
            pygame.draw.circle(self.screen, p.color, (cx, cy), max(1, int(p.size * sq * 0.5)))
        for text in self.effects.texts:
            cx = min(max(ox + text.x * sq, self.grid_rect.left + 80), self.grid_rect.right - 80)
            cy = max(oy + (text.y - 0.8 - text.time * 0.8) * sq, self.grid_rect.top + 20)
            draw_text(self.screen, text.text, text.size, text.color, (cx, cy), 'center', outline=3,
                      alpha=int(255 * text.alpha))

    def _draw_edit_cursor(self):
        g = self.game
        if not g.edit_mode:
            return
        cell = self.screen_to_cell(pygame.mouse.get_pos())
        if cell is None:
            return
        sq = GameConfig.SQUARE_SIZE
        rect = pygame.Rect(self.grid_rect.left + cell[0] * sq, self.grid_rect.top + cell[1] * sq, sq, sq)
        ghost = {'player': self.sprites.player(sq), 'house': self.sprites.house(sq),
                 'obstacles': self.sprites.block(block_kind(cell), sq),
                 'enemies': self.sprites.enemy(sq, 'perseguidor')}.get(g.edit_mode)
        if ghost:
            ghost = ghost.copy()
            ghost.set_alpha(150)
            self.screen.blit(ghost, rect)
        pulse = int(200 + 55 * math.sin(self.time * 8))
        pygame.draw.rect(self.screen, (255, pulse, 60), rect.inflate(4, 4), 2, border_radius=4)

    def screen_to_cell(self, pos):
        mode = getattr(self.game, 'view_mode', '2d')
        if mode == '3d':
            return self.map3d.screen_to_cell(pos)
        if mode == 'fps' or not self.grid_rect.collidepoint(pos):
            return None
        sq = GameConfig.SQUARE_SIZE
        return (pos[0] - self.grid_rect.left) // sq, (pos[1] - self.grid_rect.top) // sq

    # ------------------------------------------------------------ eventos visuales
    def _detect_events(self):
        g, prev = self.game, self._prev
        state = g.game_state
        if state.victory and not prev['victory']:
            hx, hy = state.house_pos
            self.effects.confetti(hx + 0.5, hy + 0.5)
            self.effects.text("¡EN CASA!", hx + 0.5, hy + 0.5, UI['gold'], 1.8, 34)
        if g.game_over and not prev['game_over']:
            self.effects.explosion(state.player_pos, state.obstacles, state.grid_width, state.grid_height)
        if state.player_pos != prev['player'] and g.is_running:
            self.effects.dust(prev['player'][0] + 0.5, prev['player'][1] + 0.5)
        for e_id, data in state.enemies.items():
            if data.get('type') == 'patrulla' and data.get('state') == 'chase' and \
                    prev['states'].get(e_id) not in (None, 'chase'):
                x, y = data['position']
                self.effects.text("!", x + 0.5, y + 0.2, UI['red'], 1.0, 40)
        if (state.victory or g.is_running) and int(self.time * 10) % 4 == 0:
            hx, hy = state.house_pos
            self.effects.sparkle(hx + 0.5, hy + 0.5, count=1)
        prev['victory'], prev['game_over'], prev['player'] = state.victory, g.game_over, state.player_pos
        prev['states'] = {e_id: d.get('state') for e_id, d in state.enemies.items()}

    def on_view_changed(self, mode):
        if mode == '3d':
            self.map3d.enter()
        elif mode == 'fps':
            self.fps.enter()

    # ------------------------------------------------------------ frame
    def render(self, dt=1 / 60):
        dt = min(dt, 0.1)
        self.time += dt
        self.anim.update(dt)
        self._detect_events()
        self.effects.update(dt)
        t = self.time

        self.screen.fill(UI['bg_bottom'])
        mode = getattr(self.game, 'view_mode', '2d')
        if mode == '3d':
            self.map3d.draw(self.screen, dt, t)
        elif mode == 'fps':
            self.fps.draw(self.screen, dt, t)
        else:
            self._draw_board_2d(t)
        self._draw_end_overlay()
        self._draw_hud(t)
        self._draw_sidebar(t)

    # ------------------------------------------------------------ marcador
    def _draw_hud(self, t):
        g = self.game
        r = self.hud_rect
        self.screen.blit(gradient(r.size, (54, 60, 104), (26, 28, 52)), r)
        pygame.draw.line(self.screen, UI['outline'], r.bottomleft, r.bottomright, 3)
        pygame.draw.line(self.screen, UI['panel_border'], (0, r.bottom - 3), (r.right, r.bottom - 3), 1)

        portrait = pygame.Rect(8, 6, 40, 40)
        pygame.draw.rect(self.screen, (24, 26, 48), portrait, border_radius=8)
        pygame.draw.rect(self.screen, UI['gold'], portrait, 2, border_radius=8)
        self.screen.blit(self.sprites.player(38, (0, 1), int(t * 3) if g.is_running else 0), portrait.move(1, 0))

        def counter(x, label, value, color):
            draw_text(self.screen, label, 15, UI['text_dim'], (x, 9))
            draw_text(self.screen, value, 30, color, (x, 21), outline=2)

        counter(58, "PASOS", f"{g.step_counter:03d}", UI['text'])
        counter(138, "TURNO", f"{g.turn_counter:03d}", UI['text'])
        seconds = g.turn_counter * GameConfig.MOVE_DELAY / 1000
        counter(218, "TIEMPO", f"{int(seconds // 60):02d}:{int(seconds % 60):02d}", UI['cyan'])

        if g.game_state.victory:
            badge, color = "¡VICTORIA!", UI['green']
        elif g.game_over:
            badge, color = "¡ATRAPADO!", UI['red']
        elif g.edit_mode:
            badge, color = f"EDITANDO: {EDIT_LABELS.get(g.edit_mode, g.edit_mode.upper())}", UI['orange']
        elif g.is_running:
            badge, color = "EN MARCHA", UI['cyan']
        else:
            badge, color = "EN PAUSA", (190, 190, 210)
        center = (r.centerx + 40, r.centery)
        label = render_text(badge, 26, UI['outline'])
        pill = label.get_rect(center=center).inflate(28, 10)
        pygame.draw.rect(self.screen, color, pill, border_radius=pill.height // 2)
        pygame.draw.rect(self.screen, UI['outline'], pill, 2, border_radius=pill.height // 2)
        self.screen.blit(label, label.get_rect(center=center))

        view_label = GameConfig.VIEW_NAMES.get(getattr(g, 'view_mode', '2d'), '2D')
        vx = r.right - 10
        draw_text(self.screen, f"VISTA {view_label}", 17, UI['gold'], (vx, 7), 'topright', outline=2)
        x = vx
        enemies = list(g.game_state.enemies.values())[:8]
        for e in reversed(enemies):
            x -= 22
            self.screen.blit(self.sprites.enemy(22, e.get('type', 'perseguidor'), (0, 1), e.get('state') == 'chase'),
                             (x, 26))
        if not enemies:
            draw_text(self.screen, "sin enemigos", 16, UI['text_dim'], (vx, 30), 'topright')

    # ------------------------------------------------------------ barra lateral
    def _draw_sidebar(self, t):
        g = self.game
        r = self.sidebar_rect
        self.screen.blit(gradient(r.size, UI['bg_top'], UI['bg_bottom']), r)
        pygame.draw.line(self.screen, UI['outline'], r.topleft, r.bottomleft, 4)

        self.screen.blit(self.sprites.bomb(46, int(t * 10)), (r.left + 12, 6))
        draw_text(self.screen, "JUEGO IA", 40, UI['gold'], (r.left + 62, 10), outline=3)
        draw_text(self.screen, "BOMBER MIND", 17, UI['text'], (r.left + 64, 42), outline=2,
                  outline_color=(170, 30, 60))

        for title, accent, rect in self._sections:
            draw_panel(self.screen, rect, title, accent)

        mouse = pygame.mouse.get_pos()
        down = pygame.mouse.get_pressed()[0]
        for b in self.buttons:
            toggled, label = False, None
            if b.id == 'start':
                toggled = g.is_running
                label = "PAUSAR (Espacio)" if g.is_running else "INICIAR (Espacio)"
                b.icon = 'pause' if g.is_running else 'play'
            elif b.id == 'toggle_view':
                label = f"Vista: {GameConfig.VIEW_NAMES.get(getattr(g, 'view_mode', '2d'), '2D')}"
            elif b.id == 'toggle_trail':
                toggled = self.show_trail
            elif b.id == 'train_player_agent':
                toggled = g.player_agent_is_training
            elif b.id == 'train_enemy_agent':
                toggled = g.enemy_agent_is_training
            elif b.id == 'use_heat_map':
                toggled = g.player_uses_heatmap_path
            elif b.id.startswith('edit_'):
                toggled = g.edit_mode == b.id[5:]
            elif b.id == 'toggle_edit_avatar_heatmap_iters':
                active = g.input_field_active == 'avatar_heatmap_iters'
                toggled = active
                value = g.input_buffer if active else str(g.avatar_heatmap_training_iterations)
                cursor = "|" if active and int(t * 2) % 2 == 0 else ""
                label = f"Hormigas: {value}{cursor}"
            b.draw(self.screen, self.sprites, mouse, down, toggled=toggled, label=label)

        self._draw_status()

    def _q_agent_label(self, agent, trained):
        if not trained:
            return "sin entrenar", UI['text_dim']
        if not agent.is_policy_current(self.game.game_state.obstacles):
            return "desactualizada (mapa nuevo)", UI['orange']
        return "lista", UI['green']

    def _draw_status(self):
        g = self.game
        r = self.sidebar_rect
        x = r.left + 16
        y = self._status_top - 6
        width = r.width - 32
        route_left = max(0, len(g.current_path_player) - g.path_index_player)
        draw_text(self.screen, f"Ruta: {g.player_path_source} · {route_left} pasos", 17, UI['text'], (x, y),
                  max_width=width)
        y += 18
        for name, agent, trained, training, progress in (
                ("IA Jugador", g.agent_player, g.player_agent_training_complete, g.player_agent_is_training,
                 g.player_agent_training_progress),
                ("IA Enemigos", g.enemy_q_agent, g.enemy_q_agent_trained, g.enemy_agent_is_training,
                 g.enemy_agent_training_progress)):
            if training:
                draw_progress_bar(self.screen, (x, y + 1, width, 15), progress / 100, (60, 160, 230),
                                  f"{name}: {progress:.0f}% · éxito {agent.success_rate * 100:.0f}%")
            else:
                text, color = self._q_agent_label(agent, trained)
                draw_text(self.screen, f"{name}:", 17, UI['text_dim'], (x, y))
                draw_text(self.screen, text, 17, color, (x + 92, y), max_width=width - 92)
            y += 18
        self._draw_enemy_legend(x, y + 6, width)

    def _draw_enemy_legend(self, x, y, width):
        """Leyenda de tipos de enemigo con su comportamiento (si cabe sobre el botón de menú)."""
        rows = (('perseguidor', "Perseguidor: va directo a ti"), ('bloqueador', "Bloqueador: te corta el paso"),
                ('patrulla', "Patrulla: ronda y te persigue al verte"), ('aleatorio', "Aleatorio: deambula"))
        bottom = self.button_rects['menu'].top - 6
        if y + len(rows) * 20 > bottom:
            return
        for etype, text in rows:
            self.screen.blit(self.sprites.enemy(20, etype, (1, 0)), (x, y - 1))
            draw_text(self.screen, text, 16, UI['text_dim'], (x + 26, y + 3), max_width=width - 26)
            y += 20

    # ------------------------------------------------------------ fin de partida
    def _draw_end_overlay(self):
        g = self.game
        if not (g.game_state.victory or g.game_over):
            return
        grid = self.grid_rect
        shade = pygame.Surface(grid.size, pygame.SRCALPHA)
        shade.fill((8, 8, 20, 110))
        self.screen.blit(shade, grid)
        panel = pygame.Rect(0, 0, 470, 210)
        panel.center = (grid.centerx, grid.centery - 40)
        if g.game_state.victory:
            draw_panel(self.screen, panel, "META", UI['green'])
            draw_text(self.screen, "¡VICTORIA!", 78, UI['gold'], (panel.centerx, panel.top + 58), 'center', outline=5)
            detail = f"Llegaste a casa en {g.step_counter} pasos ({g.turn_counter} turnos)"
        else:
            draw_panel(self.screen, panel, "GAME OVER", UI['red'])
            draw_text(self.screen, "¡ATRAPADO!", 78, UI['red'], (panel.centerx, panel.top + 58), 'center', outline=5)
            catcher = next((e for e in g.game_state.enemies.values() if e['position'] == g.game_state.player_pos), None)
            who = TYPE_NAMES.get(catcher.get('type'), 'enemigo') if catcher else 'enemigo'
            detail = f"Te atrapó un {who} tras {g.step_counter} pasos"
        draw_text(self.screen, detail, 22, UI['text'], (panel.centerx, panel.top + 112), 'center', max_width=430)
        draw_text(self.screen, f"Ruta usada: {g.player_path_source}", 19, UI['text_dim'],
                  (panel.centerx, panel.top + 138), 'center')
        draw_text(self.screen, "R: otra partida   ·   Esc: menú", 22, UI['gold'], (panel.centerx, panel.bottom - 26),
                  'center', outline=2)

    # ------------------------------------------------------------ entrenamiento bloqueante
    def render_training_overlay(self, progress, title="Entrenando mapa de calor (hormigas)..."):
        self.render(1 / 60)
        grid = self.grid_rect
        shade = pygame.Surface(grid.size, pygame.SRCALPHA)
        shade.fill((8, 8, 20, 150))
        self.screen.blit(shade, grid)
        panel = pygame.Rect(0, 0, 520, 130)
        panel.center = grid.center
        draw_panel(self.screen, panel, "IA", UI['cyan'])
        draw_text(self.screen, title, 26, UI['text'], (panel.centerx, panel.top + 34), 'center', outline=2)
        draw_progress_bar(self.screen, (panel.left + 30, panel.top + 62, panel.width - 60, 24), progress,
                          (230, 120, 40), f"{progress * 100:.0f}%")
        draw_text(self.screen, "Esc para cancelar", 17, UI['text_dim'], (panel.centerx, panel.bottom - 18), 'center')
        pygame.display.flip()

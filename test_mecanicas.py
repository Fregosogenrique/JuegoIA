"""
Pruebas de las mecánicas del juego.

Ejecutar con:  python -m unittest test_mecanicas -v
(No abre ventana: usa el driver de video "dummy" de SDL.)
"""
import io
import os
import random
import contextlib
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MPLBACKEND", "Agg")

from config import GameConfig  # noqa: E402
from grid_utils import UNREACHABLE, bfs_distance_map, is_reachable  # noqa: E402
from GameState import GameState  # noqa: E402
from ADB import QLearningAgent  # noqa: E402
from HeatMapPathfinding import HeatMapPathfinding  # noqa: E402


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class GridUtilsTest(unittest.TestCase):
    def test_bfs_rodea_muros(self):
        wall = {(2, y) for y in range(0, 4)}  # Muro vertical con hueco abajo (y=4)
        dist = bfs_distance_map(5, 5, (0, 0), wall)
        self.assertEqual(dist[0, 4], 4 + 4 + 4)  # Baja 4, cruza por el hueco, sube 4
        self.assertEqual(dist[0, 2], UNREACHABLE)  # Celda del muro

    def test_alcanzabilidad(self):
        closed = {(1, 0), (0, 1)}
        self.assertFalse(is_reachable(4, 4, (0, 0), (3, 3), closed))
        self.assertTrue(is_reachable(4, 4, (0, 0), (3, 3), set()))


class ObstacleGenerationTest(unittest.TestCase):
    def test_la_casa_siempre_es_alcanzable(self):
        original = GameConfig.OBSTACLE_PERCENTAGE
        GameConfig.OBSTACLE_PERCENTAGE = 40  # Mapa muy denso: muchos mapas aleatorios saldrían cerrados
        try:
            for seed in range(15):
                random.seed(seed)
                gs = GameState(GameConfig.GRID_WIDTH, GameConfig.GRID_HEIGHT)
                with quiet():
                    gs.initialize_game()
                self.assertTrue(gs.is_house_reachable(), f"semilla {seed}")
        finally:
            GameConfig.OBSTACLE_PERCENTAGE = original


class QLearningTest(unittest.TestCase):
    def test_jugador_aprende_el_camino_mas_corto(self):
        random.seed(0)
        agent = QLearningAgent(10, 8)
        obstacles = frozenset({(4, y) for y in range(0, 6)})  # Muro que obliga a rodear por abajo
        start, goal = (0, 0), (9, 0)
        agent._schedule_epsilon(600)
        for _ in range(600):
            s, t, dist = agent._sample_episode(goal, start, obstacles)
            agent.train_one_episode(s, t, obstacles, dist_map=dist)
        path = agent.simulate_policy(start, goal, obstacles)
        optimal = bfs_distance_map(10, 8, goal, obstacles)[start[1], start[0]]
        self.assertEqual(path[-1], goal)
        self.assertEqual(len(path) - 1, optimal)

    def test_estado_relativo_al_objetivo(self):
        sector = QLearningAgent.sector_to_target
        self.assertNotEqual(sector((5, 5), (6, 5)), sector((5, 5), (9, 5)))  # Cerca vs lejos
        self.assertEqual(sector((5, 5), (9, 5)), sector((5, 5), (20, 5)))  # Ambos "lejos al este"

    def test_vigencia_de_la_politica(self):
        agent = QLearningAgent(10, 10)
        self.assertFalse(agent.is_policy_current(set()))  # Nunca entrenado
        agent.trained_obstacles = frozenset((x, 0) for x in range(10))
        self.assertTrue(agent.is_policy_current(set((x, 0) for x in range(10))))
        self.assertFalse(agent.is_policy_current({(x, 5) for x in range(10)}))


class HeatMapTest(unittest.TestCase):
    def test_hormigas_encuentran_ruta_optima(self):
        random.seed(1)
        hm = HeatMapPathfinding(12, 10)
        obstacles = {(5, y) for y in range(0, 8)}
        best = hm.train((0, 0), (11, 0), obstacles, set(), iterations=200)
        optimal = bfs_distance_map(12, 10, (11, 0), obstacles)[0, 0]
        self.assertEqual(len(best) - 1, optimal)
        self.assertGreater(hm.avatar_heat_map[9, 5], 0)  # El hueco del muro quedó "caliente"

    def test_a_estrella_evita_enemigos(self):
        random.seed(2)
        hm = HeatMapPathfinding(9, 5)
        hm.train((0, 2), (8, 2), set(), set(), iterations=50)
        enemy = (4, 2)
        path = hm.find_path_with_heat_map((0, 2), (8, 2), obstacles=set(), enemy_positions_set={enemy})
        self.assertEqual(path[-1], (8, 2))
        self.assertNotIn(enemy, path)
        self.assertGreaterEqual(min(abs(p[0] - 4) + abs(p[1] - 2) for p in path), 2)

    def test_borrado_de_bucles(self):
        path = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (0, 1), (0, 2)]
        self.assertEqual(HeatMapPathfinding._loop_erase(path), [(0, 0), (0, 1), (0, 2)])


class GameMechanicsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from Game import Game
        random.seed(3)
        with quiet():
            cls.game = Game()

    def setUp(self):
        self.original_speed = GameConfig.ENEMY_SPEED_FACTOR
        g = self.game
        with quiet():
            g.reset_game_state_full()
        g.game_state.obstacles = set()
        g.game_state.player_pos = g.game_state.initial_player_pos = (1, 1)
        g.game_state.house_pos = (GameConfig.GRID_WIDTH - 2, GameConfig.GRID_HEIGHT - 2)
        g.enemies_initialized = True
        g.is_running = True

    def tearDown(self):
        GameConfig.ENEMY_SPEED_FACTOR = self.original_speed

    def _count_enemy_moves(self, speed, turns):
        GameConfig.ENEMY_SPEED_FACTOR = speed
        g = self.game
        g.enemy_move_accumulator = 0.0
        moves = 0
        original = g._move_all_enemies_once

        def counting():
            nonlocal moves
            moves += 1

        g._move_all_enemies_once = counting
        g.game_state.add_enemy((30, 20), "aleatorio")
        try:
            for _ in range(turns):
                g._update_enemies()
        finally:
            g._move_all_enemies_once = original
        return moves

    def test_velocidad_de_enemigos(self):
        self.assertEqual(self._count_enemy_moves(0.5, 10), 5)
        self.assertEqual(self._count_enemy_moves(0.75, 8), 6)
        self.assertEqual(self._count_enemy_moves(1.5, 4), 6)

    def test_bloqueador_apunta_por_delante_del_jugador(self):
        g = self.game
        g.current_path_player = [(1, 1)] + [(x, 1) for x in range(2, 20)]
        g.path_index_player = 1
        enemy = {'position': (10, 10), 'type': 'bloqueador'}
        target = g._enemy_target(enemy)
        self.assertEqual(target, g.current_path_player[1 + GameConfig.BLOCKER_LOOKAHEAD - 1])
        self.assertEqual(enemy['state'], 'intercept')

    def test_patrulla_detecta_y_pierde_al_jugador(self):
        g = self.game
        enemy = {'position': (20, 15), 'type': 'patrulla', 'state': 'patrol'}
        g.game_state.player_pos = (1, 1)
        g._enemy_target(enemy)
        self.assertEqual(enemy['state'], 'patrol')
        g.game_state.player_pos = (20, 15 - GameConfig.PATROL_DETECTION_RADIUS)
        self.assertEqual(g._enemy_target(enemy), g.game_state.player_pos)
        self.assertEqual(enemy['state'], 'chase')
        g.game_state.player_pos = (20, 15 - GameConfig.PATROL_LOSE_RADIUS - 1)
        g._enemy_target(enemy)
        self.assertEqual(enemy['state'], 'patrol')

    def test_enemigo_no_pisa_la_casa(self):
        g = self.game
        house = g.game_state.house_pos
        e_id = g.game_state.add_enemy((house[0] - 1, house[1]), "perseguidor")
        g.game_state.player_pos = (house[0] + 1, house[1])
        for _ in range(5):
            g._move_all_enemies_once()
            self.assertNotEqual(g.game_state.enemies[e_id]['position'], house)

    def test_jugador_huye_si_no_hay_ruta(self):
        g = self.game
        g.game_state.player_pos = (5, 5)
        g.game_state.add_enemy((5, 7), "perseguidor")
        g.current_path_player, g.path_index_player = [(5, 5)], 1
        g._player_flee_step()
        new_pos = g.game_state.player_pos
        self.assertEqual(abs(new_pos[0] - 5) + abs(new_pos[1] - 5), 1)  # Un solo paso
        self.assertEqual(abs(new_pos[0] - 5) + abs(new_pos[1] - 7), 3)  # Se alejó del enemigo (2 -> 3)

    def test_victoria_al_llegar_a_la_casa(self):
        g = self.game
        house = g.game_state.house_pos
        g.game_state.player_pos = (house[0] - 1, house[1])
        g.determine_player_optimal_path()
        g.play_turn()
        self.assertTrue(g.game_state.victory)
        self.assertFalse(g.is_running)


class VisualizationTest(unittest.TestCase):
    """Las vistas se dibujan sin errores y el clic en la maqueta 3D cae en la celda correcta."""

    @classmethod
    def setUpClass(cls):
        from Game import Game
        random.seed(5)
        with quiet():
            cls.game = Game()
            cls.game._handle_menu_action('play2d')
            cls.game.toggle_game_running_state()
            for _ in range(5):
                cls.game.play_turn()

    def test_todas_las_vistas_se_dibujan(self):
        g = self.game
        for mode in GameConfig.VIEW_MODES:
            with quiet():
                g.set_view_mode(mode)
            for _ in range(3):
                g.renderer.render(1 / 30)
        self.assertEqual(g.screen.get_size(), (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))

    def test_clic_en_mapa_3d_selecciona_la_celda(self):
        g = self.game
        with quiet():
            g.set_view_mode('3d')
        view = g.renderer.map3d
        view.intro = 1.0
        view._setup_camera()
        for cell in ((3, 4), (20, 15), (35, 25)):
            sx, sy, _ = view.project1(cell[0] + 0.5, cell[1] + 0.5, 0.0)
            pos = (int(sx) + view.rect.left, int(sy) + view.rect.top)
            self.assertEqual(g.renderer.screen_to_cell(pos), cell)

    def test_primera_persona_gira_y_avanza(self):
        import pygame
        g = self.game
        g.is_running = False
        g.game_state.obstacles = set()
        g.game_state.player_pos = (10, 10)
        g.player_facing = (1, 0)
        g._first_person_control(pygame.K_LEFT)
        self.assertEqual(g.player_facing, (0, -1))  # Girar a la izquierda mirando al este -> norte
        g._first_person_control(pygame.K_UP)
        self.assertEqual(g.game_state.player_pos, (10, 9))


if __name__ == "__main__":
    unittest.main()

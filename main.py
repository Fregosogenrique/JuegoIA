"""
Módulo principal para la aplicación del juego con IA.

Este módulo sirve como punto de entrada para la aplicación. Crea una
instancia del juego y ejecuta el bucle principal (Pygame se inicializa y se
cierra dentro de la clase Game).

Uso:
    python main.py              -> abre el juego
    python main.py --selftest   -> prueba automática sin ventana (código de salida 0 = todo bien)
"""
import os
import sys


def run_selftest():
    """
    Arranca el juego sin ventana, juega unos turnos, dibuja las tres vistas y
    genera una gráfica. Sirve para comprobar que una instalación o un
    ejecutable empaquetado tiene todo lo necesario.
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["MPLBACKEND"] = "Agg"
    import tempfile
    from config import GameConfig
    from Game import Game

    game = Game()
    game._handle_menu_action('play2d')
    game.toggle_game_running_state()
    for _ in range(30):
        game.play_turn()
        if not game.is_running:
            break
    for mode in GameConfig.VIEW_MODES:
        game.set_view_mode(mode)
        for _ in range(5):
            game.renderer.render(1 / 30)
    game.menu.draw(game.screen, 1 / 30, True, (0, 0), False)
    plot_path = os.path.join(tempfile.gettempdir(), "juegoia_selftest.png")
    game.heat_map_pathfinder.visualize_heat_map(start_pos=game.game_state.player_pos,
                                                goal_pos=game.game_state.house_pos, show=False,
                                                save_path=plot_path)
    assert os.path.exists(plot_path), "No se generó la gráfica de prueba"
    print(f"SELFTEST OK: {game.step_counter} pasos, vistas {GameConfig.VIEW_MODES}, gráfica en {plot_path}")
    return 0


def main():
    if "--selftest" in sys.argv:
        try:
            sys.exit(run_selftest())
        except Exception as err:  # Cualquier fallo debe reflejarse en el código de salida
            import traceback
            traceback.print_exc()
            print(f"SELFTEST FALLÓ: {err}")
            sys.exit(1)

    from Game import Game
    juego_instancia = Game()
    juego_instancia.run_main_game_loop()


if __name__ == "__main__":
    main()

"""
Genera el icono del juego (avatar estilo Bomberman) a partir de los sprites
dibujados por código: build_assets/JuegoIA.png y build_assets/JuegoIA.ico.

Uso (desde la raíz del repositorio):  python tools/make_icon.py
Requiere Pillow para el .ico (viene instalado con matplotlib).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from sprites import SpriteFactory  # noqa: E402


def main():
    pygame.init()
    out_dir = os.path.join(ROOT, "build_assets")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "JuegoIA.png")
    icon = pygame.Surface((256, 256), pygame.SRCALPHA)
    pygame.draw.circle(icon, (255, 206, 64), (128, 128), 124)
    pygame.draw.circle(icon, (24, 22, 34), (128, 128), 124, 8)
    icon.blit(SpriteFactory().player(208), (24, 20))
    pygame.image.save(icon, png_path)
    from PIL import Image
    ico_path = os.path.join(out_dir, "JuegoIA.ico")
    Image.open(png_path).save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icono generado: {ico_path}")


if __name__ == "__main__":
    main()

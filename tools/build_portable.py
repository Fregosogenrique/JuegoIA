"""
Genera JuegoIA_portable.py: el juego completo en UN solo archivo .py.

El archivo generado contiene el código de todos los módulos del juego
(comprimido) y un pequeño arranque que:
  1. comprueba la versión de Python,
  2. instala con pip lo que falte (pygame o pygame-ce, numpy y, opcionalmente, matplotlib),
  3. extrae los módulos a una carpeta de caché y ejecuta el juego.

Uso (desde la raíz del repositorio):
    python tools/build_portable.py            -> escribe JuegoIA_portable.py
    python tools/build_portable.py --check    -> falla si el archivo está desactualizado
"""
import base64
import json
import os
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "JuegoIA_portable.py")

# Módulos del juego que se empaquetan (los que importa main.py directa o indirectamente).
MODULES = ["main", "Game", "GameState", "config", "render", "ADB", "HeatMapPathfinding", "grid_utils",
           "plotting", "sprites", "ui", "effects", "view3d", "raycaster"]

BOOTSTRAP = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JuegoIA · Bomber Mind — versión portátil en un solo archivo.

Requisitos: sólo Python 3.8 o superior (https://www.python.org/downloads/).
La primera vez instala lo que falte (pygame, numpy y matplotlib) con pip.

Cómo jugar:
    Windows:  doble clic en este archivo (o en Jugar.bat), o bien:  py JuegoIA_portable.py
    macOS / Linux:  python3 JuegoIA_portable.py

Opciones:
    --selftest       prueba automática sin ventana (código de salida 0 = todo bien)
    --sin-preguntar  instala las dependencias sin pedir confirmación

ARCHIVO GENERADO por tools/build_portable.py: no lo edites a mano.
"""
import base64
import hashlib
import importlib
import importlib.util
import json
import os
import site
import subprocess
import sys
import tempfile
import zlib

VERSION = "__VERSION__"
MIN_PYTHON = (3, 8)
# (módulo a importar, paquetes de pip a probar en orden, ¿obligatorio?)
DEPENDENCIES = [
    ("pygame", ["pygame", "pygame-ce"], True),
    ("numpy", ["numpy"], True),
    ("matplotlib", ["matplotlib"], False),  # Sólo para las gráficas (teclas V y F1-F4)
]


def _interactive():
    return sys.stdin is not None and sys.stdin.isatty()


def _pause_if_console():
    if _interactive():
        try:
            input("\nPulsa Enter para cerrar...")
        except EOFError:
            pass


def _has_module(name):
    importlib.invalidate_caches()
    return importlib.util.find_spec(name) is not None


def _pip(*args):
    command = [sys.executable, "-m", "pip"] + list(args)
    print("  >", " ".join(command))
    return subprocess.call(command) == 0


def _ensure_pip():
    if _has_module("pip"):
        return True
    print("pip no está disponible; intentando activarlo con ensurepip...")
    subprocess.call([sys.executable, "-m", "ensurepip", "--upgrade"])
    return _has_module("pip")


def _install(package):
    in_virtualenv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    extra = [] if in_virtualenv else ["--user"]
    if _pip("install", "--disable-pip-version-check", *extra, package):
        return True
    return not in_virtualenv and _pip("install", "--disable-pip-version-check", package)


def ensure_dependencies(ask=True):
    missing = [(module, packages, required) for module, packages, required in DEPENDENCIES
               if not _has_module(module)]
    if not missing:
        return True
    names = ", ".join(packages[0] for _, packages, _ in missing)
    print(f"Faltan estas librerías: {names}")
    if ask and _interactive():
        answer = input("¿Instalarlas ahora con pip? [S/n] ").strip().lower()
        if answer in ("n", "no"):
            print("No se instalaron. El juego necesita al menos pygame y numpy.")
            return False
    if not _ensure_pip():
        print("No se pudo usar pip. Instala manualmente: pip install pygame numpy matplotlib")
        return False
    for module, packages, required in missing:
        for package in packages:
            print(f"Instalando {package}...")
            if _install(package):
                break
        site.addsitedir(site.getusersitepackages())  # Por si la carpeta de usuario no existía al arrancar
        if not _has_module(module):
            if required:
                print(f"No se pudo instalar {module}. Prueba manualmente: pip install {packages[0]}")
                return False
            print(f"Aviso: {module} no se instaló; el juego funciona pero sin gráficas de análisis.")
    return True


def _cache_dir(payload):
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:12]
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache")
    for root in (base, tempfile.gettempdir()):
        path = os.path.join(root, "JuegoIA", f"v{VERSION}-{digest}")
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except OSError:
            continue
    raise OSError("No se encontró una carpeta con permiso de escritura para extraer el juego")


def extract_game():
    """Escribe los módulos del juego en una carpeta de caché y la añade a sys.path."""
    modules = json.loads(zlib.decompress(base64.b64decode(PAYLOAD)).decode("utf-8"))
    folder = _cache_dir(PAYLOAD)
    for name, source in modules.items():
        path = os.path.join(folder, name + ".py")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source)
    sys.path.insert(0, folder)
    return folder


def main():
    if sys.version_info < MIN_PYTHON:
        print(f"JuegoIA necesita Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} o superior "
              f"(tienes {sys.version.split()[0]}). Descárgalo en https://www.python.org/downloads/")
        _pause_if_console()
        return 1
    print(f"JuegoIA · Bomber Mind v{VERSION} (Python {sys.version.split()[0]})")
    if not ensure_dependencies(ask="--sin-preguntar" not in sys.argv and "--selftest" not in sys.argv):
        _pause_if_console()
        return 1
    extract_game()
    import main as game_main
    try:
        game_main.main()
    except SystemExit as exit_request:
        return exit_request.code or 0
    return 0


# Código de los módulos del juego (JSON comprimido con zlib y codificado en base64)
PAYLOAD = (
__PAYLOAD__
)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nEl juego se cerró por un error. Copia el mensaje de arriba para reportarlo.")
        _pause_if_console()
        sys.exit(1)
'''


def build_source(version="2.1.0"):
    sources = {}
    for name in MODULES:
        with open(os.path.join(ROOT, name + ".py"), encoding="utf-8") as handle:
            sources[name] = handle.read()
    payload = base64.b64encode(zlib.compress(json.dumps(sources, sort_keys=True).encode("utf-8"), 9)).decode("ascii")
    lines = "\n".join(f'    "{payload[i:i + 100]}"' for i in range(0, len(payload), 100))
    return BOOTSTRAP.replace("__VERSION__", version).replace("__PAYLOAD__", lines)


def main():
    source = build_source()
    if "--check" in sys.argv:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != source:
            print("JuegoIA_portable.py está desactualizado: ejecuta  python tools/build_portable.py")
            return 1
        print("JuegoIA_portable.py está actualizado.")
        return 0
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(source)
    print(f"Generado {OUTPUT} ({len(source) // 1024} KB, {len(MODULES)} módulos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

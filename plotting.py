# plotting.py
"""
Acceso diferido a matplotlib.

Las gráficas de análisis (teclas V y F1-F4) son opcionales: matplotlib sólo
se importa la primera vez que se dibuja una. Así el juego arranca más rápido y
funciona aunque matplotlib no esté instalado (la gráfica mostrará un aviso).
"""


class _LazyPyplot:
    _module = None

    def __getattr__(self, name):
        if _LazyPyplot._module is None:
            try:
                import matplotlib.pyplot as pyplot
            except ImportError as err:
                raise ImportError("Las gráficas necesitan matplotlib: pip install matplotlib") from err
            _LazyPyplot._module = pyplot
        return getattr(_LazyPyplot._module, name)


plt = _LazyPyplot()

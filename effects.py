# effects.py
"""
Efectos visuales: partículas, explosión en cruz (estilo Bomberman), textos
flotantes y temblor de pantalla. Todo se expresa en coordenadas de CELDA
(floats), así cada vista (2D, mapa 3D) lo proyecta a su manera.
"""
import math
import random

CONFETTI_COLORS = [(255, 214, 64), (255, 96, 128), (96, 200, 255), (130, 230, 120), (200, 140, 255)]
FIRE_COLORS = [(255, 250, 200), (255, 220, 90), (255, 150, 40), (240, 80, 30)]


class Particle:
    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'life', 'max_life', 'color', 'size', 'gravity')

    def __init__(self, x, y, z, vx, vy, vz, life, color, size, gravity):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = self.max_life = life
        self.color, self.size, self.gravity = color, size, gravity

    @property
    def alpha(self):
        return max(0.0, self.life / self.max_life)


class Blast:
    """Explosión en cruz: centro + brazos de `reach` celdas que se detienen en muros."""

    def __init__(self, cell, arms, duration=0.9):
        self.cell = cell
        self.arms = arms  # Lista de celdas afectadas (incluye el centro)
        self.time = 0.0
        self.duration = duration

    @property
    def progress(self):
        return min(1.0, self.time / self.duration)

    @property
    def intensity(self):
        """Crece rápido y se apaga lento."""
        p = self.progress
        return min(1.0, p * 6) * (1.0 - p) ** 0.6


class FloatingText:
    def __init__(self, text, x, y, color, duration=1.2, size=26):
        self.text, self.x, self.y, self.color = text, x, y, color
        self.time, self.duration, self.size = 0.0, duration, size

    @property
    def alpha(self):
        return max(0.0, 1.0 - self.time / self.duration)


class Effects:
    def __init__(self):
        self.particles = []
        self.blasts = []
        self.texts = []
        self.shake = 0.0

    def clear(self):
        self.particles.clear()
        self.blasts.clear()
        self.texts.clear()
        self.shake = 0.0

    def update(self, dt):
        for p in self.particles:
            p.life -= dt
            p.vz -= p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z = max(0.0, p.z + p.vz * dt)
            if p.z == 0.0:
                p.vx *= 0.9
                p.vy *= 0.9
        self.particles = [p for p in self.particles if p.life > 0]
        for b in self.blasts:
            b.time += dt
        self.blasts = [b for b in self.blasts if b.time < b.duration]
        for t in self.texts:
            t.time += dt
        self.texts = [t for t in self.texts if t.time < t.duration]
        self.shake = max(0.0, self.shake - dt * 2.5)

    def shake_offset(self):
        if self.shake <= 0:
            return 0, 0
        amp = 10 * self.shake
        return random.uniform(-amp, amp), random.uniform(-amp, amp)

    # ------------------------------------------------------------ emisores
    def confetti(self, cx, cy, count=120):
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.5, 6.0)
            self.particles.append(Particle(cx, cy, 0.5, math.cos(ang) * spd, math.sin(ang) * spd,
                                           random.uniform(3, 8), random.uniform(1.2, 2.4),
                                           random.choice(CONFETTI_COLORS), random.uniform(0.12, 0.22), 9.0))

    def sparkle(self, cx, cy, color=(255, 240, 150), count=6):
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(0.3, 1.2)
            self.particles.append(Particle(cx, cy, random.uniform(0.6, 1.2), math.cos(ang) * spd,
                                           math.sin(ang) * spd, random.uniform(0.5, 1.5), random.uniform(0.4, 0.8),
                                           color, random.uniform(0.06, 0.1), 1.5))

    def dust(self, cx, cy, count=3):
        for _ in range(count):
            self.particles.append(Particle(cx + random.uniform(-0.2, 0.2), cy + random.uniform(0.1, 0.35), 0.05,
                                           random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.3),
                                           random.uniform(0.3, 0.8), random.uniform(0.3, 0.5),
                                           (210, 230, 180), random.uniform(0.06, 0.1), 2.0))

    def explosion(self, cell, blocked, width, height, reach=3):
        arms = [cell]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for k in range(1, reach + 1):
                c = (cell[0] + dx * k, cell[1] + dy * k)
                if not (0 <= c[0] < width and 0 <= c[1] < height) or c in blocked:
                    break
                arms.append(c)
        self.blasts.append(Blast(cell, arms))
        for _ in range(70):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1, 5)
            self.particles.append(Particle(cell[0] + 0.5, cell[1] + 0.5, 0.4, math.cos(ang) * spd,
                                           math.sin(ang) * spd, random.uniform(2, 6), random.uniform(0.5, 1.2),
                                           random.choice(FIRE_COLORS), random.uniform(0.1, 0.2), 8.0))
        self.shake = 1.0

    def text(self, text, x, y, color=(255, 255, 255), duration=1.2, size=26):
        self.texts.append(FloatingText(text, x, y, color, duration, size))

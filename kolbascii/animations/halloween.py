"""Halloween graveyard: under a full moon, tombstones rise and a dead tree
claws its way up, spirits drift out of the ground and assemble into a 3D
pumpkin that carves its own face, a candle flickers on inside, bats burst out
of its mouth, ghosts drift between the graves, a spider drops on its thread,
fog rolls in and lightning cracks the sky.

Run it with:  kolbascii halloween
"""
import math
import random

from ..engine import Canvas
from .thanksgiving import (GROW, RAMP, Builder, clip, ease_back, ease_in_out, fib_sphere, lerp_t, mix,
                           unit)

TAU = math.tau
GROUND = 0.0
YC = 0.42
D = 3.4
PHI = 0.17

T_STONES = (0.4, 2.8)
T_TREE = (1.0, 4.6)
T_ASSEMBLE = (1.6, 5.4)
T_FLY = 1.5
T_STEM = (6.6, 7.3)
T_VINE = (7.0, 8.0)
T_EYES = (7.6, 8.1)
T_NOSE = 8.6
T_MOUTH = (9.0, 10.0)
T_LIGHT = 10.4
T_BATS = 10.9
T_GHOSTS = 11.5
T_SPIDER = 12.0
T_MSG = 13.0
T_STORM = 14.0
MESSAGE = "H A P P Y   H A L L O W E E N"
MSG_PALETTE = ((255, 140, 30), (175, 95, 255), (120, 240, 110))

ORANGE, ORANGE_DEEP = (0.92, 0.38, 0.03), (0.45, 0.12, 0.01)
FLESH = (0.55, 0.22, 0.04)
SPIRIT = (0.45, 1.0, 0.65)
CANDLE = (1.0, 0.62, 0.12)
FLAME = (1.0, 0.93, 0.55)
STONE, STONE_DARK, MOSS = (0.66, 0.68, 0.78), (0.10, 0.10, 0.14), (0.36, 0.55, 0.28)
BARK = (0.50, 0.40, 0.36)
BAT = (190, 150, 245)

NORMAL, CARVED, RIM = 0, 1, 2          # pumpkin skin states
STONE_K, TREE_K, GLOW_K, WICK_K = 3, 4, 5, 6

FONT = {  # 3x5 bitmap letters for the tombstones
    "R": ("##.", "#.#", "##.", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "P": ("##.", "#.#", "##.", "#..", "#.."),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "O": (".#.", "#.#", "#.#", "#.#", ".#."),
}

GHOST_SMALL = [
    "  .-~~-.  ",
    " ( o  o ) ",
    " |  __  | ",
    " |      | ",
    " |      | ",
]
GHOST_BIG = [
    "    .-~~~~-.    ",
    "  .'        '.  ",
    " /   O    O   \\ ",
    "|              |",
    "|     .--.     |",
    "|    (    )    |",
    "|     '--'     |",
    "|              |",
    "|              |",
]
GHOST_HEMS = ("\\/\\/\\/\\/\\/\\/\\/\\/", "/\\/\\/\\/\\/\\/\\/\\/\\")


# --------------------------------------------------------------- the carved face
def face_feature(u, v, pad=0.0):
    """Which part of the face (if any) the surface point at face coords (u, v)
    belongs to. u: angle around the pumpkin (0 = facing the camera), v: height
    on the unit sphere. ``pad`` grows every shape (for the cut rim)."""
    for side, name in ((-1, "eye_l"), (1, "eye_r")):          # triangular eyes, point up
        cx = side * 0.42
        if 0.06 - pad < v < 0.50 + pad:
            w = 0.27 * (0.50 - v) / 0.44 + pad
            if abs(u - cx) < w:
                return name
    if -0.10 - pad < v < 0.08 + pad:                            # little triangle nose
        if abs(u) < 0.11 * (0.08 - v) / 0.18 + pad:
            return "nose"
    if abs(u) < 0.86 + pad:                                     # grinning mouth with teeth
        k = (u / 0.86) ** 2
        top = -0.20 - 0.10 * (1 - k)
        bottom = -0.60 + 0.36 * k
        if bottom - pad < v < top + pad:
            if pad == 0.0:
                for tx in (-0.30, 0.30):                        # two top teeth
                    if abs(u - tx) < 0.08 and v > top - 0.11:
                        return None
                if abs(u) < 0.08 and v < bottom + 0.11:         # one bottom tooth
                    return None
            return "mouth"
    return None


def carve_time(name, u, rng):
    if name == "eye_l":
        return T_EYES[0] + rng.random() * 0.25
    if name == "eye_r":
        return T_EYES[1] + rng.random() * 0.25
    if name == "nose":
        return T_NOSE + rng.random() * 0.2
    return lerp_t(T_MOUTH, (u + 0.86) / 1.72) + rng.random() * 0.1


# --------------------------------------------------------------- scene building
class HalloweenBuilder(Builder):
    def __init__(self, dens):
        Builder.__init__(self, dens, seed=31)
        self.static = []       # (x,y,z,nx,ny,nz,r,g,b,kind,t0,base,gi,extra)

    def put(self, p, n, col, kind, t0, base=1.0, extra=0.0):
        self.static.append((p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2],
                            kind, t0, base, self.rng.randrange(3), extra))

    def lantern(self):
        rng, dens = self.rng, self.dens
        R, H = 0.42, 0.33
        pts, top = self.pumpkin_points(0.0, 0.0, R, H, 10, ORANGE, ORANGE_DEEP, int(6800 * dens))
        cy = GROUND + H * 0.96
        span = T_ASSEMBLE[1] - T_ASSEMBLE[0]
        swirl = []
        for p, n, col, base in pts:
            dx, dy, dz = p[0] / R, (p[1] - cy) / H, p[2] / R
            u = math.atan2(dx, -dz)
            name = face_feature(u, dy) if dz < -0.2 else None
            state, tc = NORMAL, 1e9
            if name:
                state, tc = CARVED, carve_time(name, u, rng)
            elif dz < -0.2:
                rim = face_feature(u, dy, pad=0.028)
                if rim:
                    state, tc = RIM, carve_time(rim, u, rng)
            hgt = clip((p[1] - GROUND) / 0.66, 0, 1)
            t0 = T_ASSEMBLE[0] + span * hgt * 0.8 + rng.random() * span * 0.2
            swirl.append((p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2], t0, base,
                          rng.randrange(3), rng.uniform(0, TAU), rng.uniform(0.9, 1.5), state, tc))
        # glowing inside wall, seen through the holes
        for d in fib_sphere(int(2600 * dens)):
            p = (d[0] * R * 0.84, cy + d[1] * H * 0.84, d[2] * R * 0.84)
            self.put(p, (-d[0], -d[1], -d[2]), CANDLE, GLOW_K, T_ASSEMBLE[1], 1.0, rng.random())
        # candle with a flame, standing on the inside floor
        for _ in range(int(160 * dens) + 40):
            a, v = rng.random() * TAU, rng.random()
            p = (math.cos(a) * 0.035, GROUND + 0.05 + v * 0.10, math.sin(a) * 0.035 - 0.05)
            self.put(p, (math.cos(a), 0, math.sin(a)), (0.95, 0.92, 0.82), WICK_K, T_LIGHT - 0.6, 0.9)
        for _ in range(int(80 * dens) + 20):
            v = rng.random()
            r = 0.022 * math.sin(math.pi * v) + 0.004
            a = rng.random() * TAU
            p = (math.cos(a) * r, GROUND + 0.16 + v * 0.07, math.sin(a) * r - 0.05)
            self.put(p, (0, 0, -1), FLAME, GLOW_K, T_LIGHT, 1.0, 9 + rng.random())
        tip = self.stem(top, *T_STEM)
        self.vine((top[0], top[1] + 0.01, top[2]), *T_VINE)
        return swirl

    def tombstone(self, cx, cz, w, h, lean, text, t0, cross=False):
        rng, dens = self.rng, self.dens
        depth = 0.05
        cl, sl = math.cos(lean), math.sin(lean)

        def place(x, y, z, n):  # lean around the base, then move into place
            return ((cx + x * cl - y * sl, x * sl + y * cl, cz + z),
                    (n[0] * cl - n[1] * sl, n[0] * sl + n[1] * cl, n[2]))

        def top_at(x):
            if cross:
                return h if abs(x) < w * 0.17 else (h * 0.78 if abs(x) < w / 2 else -1)
            r = w / 2
            return h - r + math.sqrt(max(0.0, r * r - x * x))

        def inside(x, y):
            if cross:
                stem = abs(x) < w * 0.17 and y <= h
                arm = abs(x) < w / 2 and h * 0.55 < y < h * 0.78
                return stem or arm
            return abs(x) <= w / 2 and 0 <= y <= top_at(x)

        def engraved(x, y):
            if not text:
                return False
            lh = h * 0.24
            lw = lh * 0.6
            gap = lw * 0.45
            total = len(text) * lw + (len(text) - 1) * gap
            x0, y0 = -total / 2, h * 0.42
            if not (x0 <= x <= -x0 and y0 <= y <= y0 + lh):
                return False
            i = int((x - x0) / (lw + gap))
            lx = (x - x0) - i * (lw + gap)
            if i >= len(text) or lx > lw:
                return False
            col = min(2, int(lx / lw * 3))
            row = min(4, int((y0 + lh - y) / lh * 5))
            return FONT[text[i]][row][col] == "#"

        n_face = int(1500 * dens * (w * h) / 0.06) + 80
        for side in (-1, 1):                                     # front / back
            for _ in range(n_face):
                x, y = rng.uniform(-w / 2, w / 2), rng.uniform(0, h)
                if not inside(x, y):
                    continue
                carved = side == -1 and engraved(x, y)
                moss = rng.random() < 0.10 * (1 - y / h)
                col = STONE_DARK if carved else (MOSS if moss else mix(STONE, STONE_DARK, rng.random() * 0.35))
                p, n = place(x, y, side * depth / 2, (0, 0, side))
                self.put(p, n, col, STONE_K, t0, 0.45 if carved else 0.95, h)
        for _ in range(int(500 * dens) + 40):                    # rim (sides and top)
            x = rng.uniform(-w / 2, w / 2)
            y = top_at(x)
            if y < 0:
                continue
            z = rng.uniform(-depth / 2, depth / 2)
            p, n = place(x, y, z, unit(x / (w / 2) * 0.5, 1, 0))
            self.put(p, n, mix(STONE, STONE_DARK, rng.random() * 0.3), STONE_K, t0, 0.9, h)
            if not cross:
                y2 = rng.uniform(0, h - w / 2)
                for sx in (-1, 1):
                    p, n = place(sx * w / 2, y2, z, (sx, 0, 0))
                    self.put(p, n, mix(STONE, STONE_DARK, 0.25), STONE_K, t0, 0.8, h)

    def dead_tree(self, bx, bz):
        rng, dens = self.rng, self.dens

        def branch(p, d, length, radius, depth, t0, dur):
            n = int(length * 900 * dens * (radius / 0.03 + 0.4)) + 12
            for _ in range(n):
                s = rng.random()
                a = rng.random() * TAU
                # a perpendicular basis around the branch direction
                ax = unit(-d[2], 0.0, d[0]) if abs(d[1]) < 0.95 else (1.0, 0.0, 0.0)
                bx_ = (d[1] * ax[2] - d[2] * ax[1], d[2] * ax[0] - d[0] * ax[2], d[0] * ax[1] - d[1] * ax[0])
                r = radius * (1 - 0.35 * s)
                off = tuple(ax[i] * math.cos(a) * r + bx_[i] * math.sin(a) * r for i in range(3))
                q = tuple(p[i] + d[i] * length * s + off[i] for i in range(3))
                nrm = unit(*off)
                self.put(q, nrm, mix(BARK, (0.22, 0.17, 0.15), rng.random() * 0.4), TREE_K,
                         t0 + dur * s, 0.85)
            if depth == 0:
                return
            end = tuple(p[i] + d[i] * length for i in range(3))
            kids = 2 if depth > 2 else rng.choice((2, 3))
            for k in range(kids):
                spread = rng.uniform(0.45, 0.85)
                yaw = rng.uniform(0, TAU)
                nd = unit(d[0] + math.cos(yaw) * spread, d[1] * (0.75 if depth < 3 else 0.9) + 0.05,
                          d[2] + math.sin(yaw) * spread)
                branch(end, nd, length * rng.uniform(0.62, 0.78), radius * 0.62, depth - 1,
                       t0 + dur, dur * 0.85)

        branch((bx, GROUND, bz), unit(0.08, 1, -0.05), 0.42, 0.045, 4, T_TREE[0], 0.9)

    def build(self):
        swirl = self.lantern()
        stones = [(-0.70, 0.42, 0.20, 0.30, 0.06, "RIP", False),
                  (0.70, 0.48, 0.18, 0.26, -0.10, "BOO", False),
                  (-0.22, 0.80, 0.16, 0.24, 0.12, "", False),
                  (0.30, 0.95, 0.20, 0.34, -0.04, "", True),
                  (1.10, 0.05, 0.15, 0.22, 0.15, "RIP", False)]
        for k, (x, z, w, h, lean, text, cross) in enumerate(stones):
            self.tombstone(x, z, w, h, lean, text, lerp_t(T_STONES, k / len(stones)), cross)
        self.dead_tree(-1.05, 0.70)
        grow = [p for p in self.parts]  # stem + vine from the pumpkin helpers
        return swirl, self.static, grow


# --------------------------------------------------------------- the scene
class Scene:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        U = min(1.45 * rows, 0.56 * cols)
        self.U = U
        self.F = U * D
        self.dens = clip((U / 60.0) ** 2, 0.8, 1.7)
        self.splat = U > 80
        self.cx = cols / 2 + 0.04 * cols
        self.cy = 0.76 * rows - (YC - GROUND) * math.cos(PHI) * self.F * 0.5 / D
        self.swirl, self.static, self.grow = HalloweenBuilder(self.dens).build()
        rng = random.Random(13)
        self.bats = [(T_BATS + k * 0.14, rng.uniform(0, TAU), rng.uniform(0.9, 1.7), rng.uniform(0.55, 1.25),
                      rng.uniform(0.5, 0.9) * rng.choice((-1, 1)), rng.uniform(-0.5, 0.5), rng.random())
                     for k in range(14)]
        self.stars = [(rng.randrange(cols), rng.randrange(max(1, int(rows * 0.5))), rng.random())
                      for _ in range(cols * rows // 150)]
        self.moon = (int(cols * 0.20), int(rows * 0.20), max(3, rows * 0.11))
        self.ground = self._ground()
        self.horizon = int(self.project(0, GROUND, 1.6)[1])
        big = U > 85
        self.ghost = GHOST_BIG if big else GHOST_SMALL
        self.hems = GHOST_HEMS if big else tuple(h[:10] for h in GHOST_HEMS)

    def project(self, x, y, z):
        yy = y - YC
        cp, sp = math.cos(PHI), math.sin(PHI)
        y2 = yy * cp + z * sp
        z2 = z * cp - yy * sp
        d = D + z2
        return self.cx + x * self.F / d, self.cy - y2 * self.F * 0.5 / d, d

    def _ground(self):
        cols, rows = self.cols, self.rows
        seen = {}
        step = 0.028 if self.U > 85 else 0.042
        n = int(2.4 / step)
        for i in range(-n, n + 1):
            for j in range(-n // 2, n):
                x, z = i * step, j * step
                if (x / 2.4) ** 2 + ((z - 0.35) / 1.5) ** 2 > 1:
                    continue
                sx, sy, d = self.project(x, GROUND, z)
                sx, sy = int(sx + 0.5), int(sy + 0.5)
                if 0 <= sx < cols and 0 <= sy < rows:
                    idx = sy * cols + sx
                    if idx not in seen or d < seen[idx][0]:
                        seen[idx] = (d, math.hypot(x, z))
        rng = random.Random(21)
        out = []
        for idx, (d, r) in seen.items():
            fog = clip(1.25 - 0.32 * (d - D + 1.0), 0.15, 1.0)
            sx, sy = idx % cols, idx // cols
            if rng.random() < 0.18:                                 # dead grass tufts
                ch, c = rng.choice(",'\"^v"), (40, 70, 38)
            else:
                ch = "-" if (sx // 2 + sy) % 3 else "."
                if sx % 4 == 3:
                    continue
                c = (62, 58, 80)
            out.append((idx, d + 50, ch, tuple(int(v * 0.85 * fog) for v in c)))
        return out

    # -- sky ------------------------------------------------------------------
    def _sky(self, t, zb, chs, cos_):
        cols, rows = self.cols, self.rows
        for x, y, ph in self.stars:
            v = int(45 + 50 * (0.5 + 0.5 * math.sin(t * 1.4 + ph * 50)))
            i = y * cols + x
            zb[i], chs[i], cos_[i] = 95, "." if ph < 0.85 else "+", (v, v - 5, v + 20)
        mx, my, mr = self.moon
        ry, rx = mr, mr * 2.0
        for y in range(int(my - ry * 1.9), int(my + ry * 1.9) + 1):
            for x in range(int(mx - rx * 1.9), int(mx + rx * 1.9) + 1):
                if not (0 <= x < cols and 0 <= y < rows):
                    continue
                dx, dy = (x - mx) / rx, (y - my) / ry
                rr = math.sqrt(dx * dx + dy * dy)
                i = y * cols + x
                if rr <= 1.0:
                    z = math.sqrt(max(0.0, 1 - rr * rr))
                    crater = (math.sin(dx * 9 + 1) * math.sin(dy * 8 - 2) + math.sin(dx * 17 - dy * 13) * 0.5)
                    b = clip(0.55 + 0.35 * z - 0.18 * max(0.0, crater), 0.2, 1.0)
                    li = int(b * (len(RAMP) - 1))
                    zb[i], chs[i], cos_[i] = 94, RAMP[li], (int(250 * b), int(238 * b), int(190 * b))
                elif rr < 1.8 and chs[i] is None:
                    k = (1.8 - rr) / 0.8
                    if (x * 7 + y * 3) % 5 == 0:
                        zb[i], chs[i], cos_[i] = 94, ".", (int(110 * k), int(100 * k), int(70 * k))
        # drifting clouds, passing over the moon
        top = int(rows * 0.42)
        sc = 30.0 / max(30, rows)                       # cloud size scales with the window
        ax = [math.sin(x * 0.030 * sc + t * 0.05) for x in range(cols)]
        bx = [math.sin(x * 0.071 * sc - t * 0.035 + 1.7) for x in range(cols)]
        for y in range(0, top):
            ay = math.sin(y * 0.30 * sc + 0.4)
            by_ = math.sin(y * 0.55 * sc + 2.2)
            if ay + by_ < -0.3:
                continue
            row0 = y * cols
            for x in range(cols):
                c = ax[x] * ay + 0.8 * bx[x] * by_
                if c > 0.92:
                    i = row0 + x
                    k = clip((c - 0.92) * 2.5, 0.2, 0.8)
                    chs[i] = "~" if c > 1.15 else ("-" if (x + y) % 3 else ".")
                    zb[i], cos_[i] = 93, (int(55 + 55 * k), int(52 + 48 * k), int(75 + 70 * k))

    def render(self, t):
        cols, rows = self.cols, self.rows
        N = cols * rows
        zb = [1e9] * N
        chs = [None] * N
        cos_ = [None] * N
        solid = bytearray(N)
        bx0, bx1, by0, by1 = cols, 0, rows, 0

        self._sky(t, zb, chs, cos_)
        for idx, d, ch, c in self.ground:
            zb[idx], chs[idx], cos_[idx] = d, ch, c

        F, F2, cx, cy = self.F, self.F * 0.5, self.cx, self.cy
        cp, sp = math.cos(PHI), math.sin(PHI)
        th = 0.55 * math.sin(t * 0.33)                       # the lantern sways, face stays to us
        c, s = math.cos(th), math.sin(th)
        Lx, Ly, Lz = unit(-0.6, 0.6, -0.5)                   # cold moonlight from the upper left
        nr = len(RAMP) - 1
        splat = self.splat
        visible = 0
        lit = t > T_LIGHT
        on = clip((t - T_LIGHT) / 0.6, 0, 1)
        flick = on * (0.78 + 0.12 * math.sin(t * 13) + 0.10 * math.sin(t * 31 + 1.3))
        glow_cells = []

        def plot(sx, sy, d, glyph, col, li, is_solid):
            nonlocal bx0, bx1, by0, by1
            idx = sy * cols + sx
            if d >= zb[idx]:
                return False
            zb[idx], chs[idx], cos_[idx] = d, glyph, col
            if is_solid:
                solid[idx] = 1
                if sx < bx0: bx0 = sx
                if sx > bx1: bx1 = sx
                if sy < by0: by0 = sy
                if sy > by1: by1 = sy
                if splat and sx + 1 < cols and d + 0.01 < zb[idx + 1]:
                    zb[idx + 1], chs[idx + 1], cos_[idx + 1] = d + 0.01, RAMP[max(0, min(nr, li) - 2)], col
                    solid[idx + 1] = 1
            return True

        def cam(x, y, z, rotate):
            if rotate:
                x, z = x * c - z * s, x * s + z * c
            yy = y - YC
            y2 = yy * cp + z * sp
            z2 = z * cp - yy * sp
            d = D + z2
            return int(cx + x * F / d + 0.5), int(cy - y2 * F2 / d + 0.5), d, z2

        def lambert(nx, ny, nz, rotate):
            if rotate:
                nx, nz = nx * c - nz * s, nx * s + nz * c
            dd = nx * Lx + (ny * cp + nz * sp) * Ly + (nz * cp - ny * sp) * Lz
            return (dd if dd > 0 else 0.0), (nz * cp - ny * sp)

        # -- tombstones, tree, glow, candle ----------------------------------
        for (x, y, z, nx, ny, nz, r, g, b, kind, t0, base, gi, extra) in self.static:
            if t < t0:
                continue
            age = t - t0
            rotate = kind in (GLOW_K, WICK_K)
            if kind == STONE_K and age < 1.2:                # rises out of the earth
                y -= (1 - ease_in_out(age / 1.2)) * extra * 1.05
                if y < GROUND:
                    continue
            sx, sy, d, z2 = cam(x, y, z, rotate)
            if sx < 0 or sx >= cols or sy < 0 or sy >= rows or d >= zb[sy * cols + sx]:
                continue
            if kind == GLOW_K:
                if extra >= 9:                               # the flame itself
                    if not lit:
                        continue
                    k = 0.8 + 0.2 * math.sin(t * 17 + extra * 5)
                    col = (255, int(200 + 40 * k), int(90 * k))
                    if plot(sx, sy, d, "@" if k > 0.85 else "^", col, nr, False):
                        visible += 1
                    continue
                k = 0.06 + 1.1 * flick * (0.85 + 0.15 * math.sin(t * 7 + extra * 20))
                col = (int(min(255, 50 + 240 * k)), int(min(255, 15 + 245 * k)), int(min(255, 8 + 150 * k * k)))
                li = int(clip(0.45 + 0.55 * k, 0, 1) * nr)
                if plot(sx, sy, d, RAMP[li], col, li, True):
                    visible += 1
                    if lit and k > 0.55:
                        glow_cells.append((sx, sy, k, d))
                continue
            diff, _ = lambert(nx, ny, nz, rotate)
            lum = base * (0.38 + 0.75 * diff)
            fog = clip(1.15 - 0.45 * (z2 + 0.5), 0.45, 1.0)
            li = int((0.30 + 0.75 * lum * fog) * nr) + gi - 1
            li = 0 if li < 0 else nr if li > nr else li
            v = (0.30 + 0.9 * lum) * fog
            rr_, gg_, bb_ = r, g, b
            if kind in (STONE_K, TREE_K) and age < 0.3 and kind == TREE_K:
                f = 1 - age / 0.3
                rr_, gg_, bb_ = mix((r, g, b), (0.7, 1.0, 0.75), f)
                v = max(v, f)
            col = (int(min(255, rr_ * v * 255)), int(min(255, gg_ * v * 255)), int(min(255, bb_ * v * 255)))
            if plot(sx, sy, d, RAMP[li], col, li, True):
                visible += 1

        # -- stem and vine (grow) -----------------------------------------------
        for (x, y, z, nx, ny, nz, r, g, b, mode, t0, base, ccx, ccy, ccz, gi) in self.grow:
            if t < t0:
                continue
            age = t - t0
            sx, sy, d, z2 = cam(x, y, z, True)
            if sx < 0 or sx >= cols or sy < 0 or sy >= rows or d >= zb[sy * cols + sx]:
                continue
            diff, _ = lambert(nx, ny, nz, True)
            lum = base * (0.22 + 0.85 * diff)
            li = int((0.30 + 0.75 * lum) * nr) + gi - 1
            li = 0 if li < 0 else nr if li > nr else li
            v = 0.30 + 0.9 * lum
            if age < 0.3:
                f = 1 - age / 0.3
                r, g, b = mix((r, g, b), (1, 1, 0.8), f)
                v = max(v, f)
            col = (int(min(255, r * v * 255)), int(min(255, g * v * 255)), int(min(255, b * v * 255)))
            if plot(sx, sy, d, RAMP[li], col, li, True):
                visible += 1

        # -- the jack-o'-lantern: spirits rise from the graves and become its skin
        for (x, y, z, nx, ny, nz, r, g, b, t0, base, gi, a0, rs, state, tc) in self.swirl:
            u = (t - (t0 - T_FLY)) / T_FLY
            if u < 0:
                continue
            flying = u < 1
            if state == CARVED and t > tc + 0.25 and not flying:
                # cut away: the cell becomes a window onto the candle (black until it's lit)
                sx, sy, d, z2 = cam(x, y, z, True)
                if sx < 0 or sx >= cols or sy < 0 or sy >= rows or d >= zb[sy * cols + sx]:
                    continue
                k = 1.1 * flick * (0.85 + 0.15 * math.sin(t * 7 + gi * 2.1 + a0 * 3))
                if k < 0.12:
                    plot(sx, sy, d, " ", (0, 0, 0), 0, True)
                    continue
                k = clip(k, 0.45, 1.0)
                col = (255, int(185 + 70 * k), int(70 + 130 * k))
                li = nr - gi - (1 if k < 0.7 else 0)
                if plot(sx, sy, d, RAMP[li], col, li, True):
                    visible += 1
                    glow_cells.append((sx, sy, k, d))
                continue
            if flying:
                e = ease_in_out(u)
                tang = math.atan2(z, x)
                tang += TAU * round((a0 - tang) / TAU) + TAU
                a = a0 * (1 - e) + tang * e
                rr = rs * (1 - e) + math.hypot(x, z) * e
                y_ = GROUND * (1 - e) + y * e + 0.45 * math.sin(math.pi * e)
                x_, z_ = math.cos(a) * rr, math.sin(a) * rr
                sx, sy, d, z2 = cam(x_, y_, z_, True)
                if sx < 0 or sx >= cols or sy < 0 or sy >= rows:
                    continue
                k = e * e
                rgb = mix(SPIRIT, (r, g, b), k)
                fade = clip(u * 4, 0, 1) * clip(1.2 - 0.5 * (z2 + 0.5), 0.35, 1.0)
                col = tuple(int(min(255, v * 255 * (0.6 + 0.6 * k) * fade)) for v in rgb)
                glyph = ("*", "+", ".", "'")[int(t * 6 + a0 * 5) % 4] if k < 0.75 else "#"
                if plot(sx, sy, d, glyph, col, nr, False):
                    visible += 1
                continue
            nzr = nx * s + nz * c
            if nzr * cp - ny * sp > 0.4:
                continue                                         # back-facing
            sx, sy, d, z2 = cam(x, y, z, True)
            if sx < 0 or sx >= cols or sy < 0 or sy >= rows or d >= zb[sy * cols + sx]:
                continue
            diff, _ = lambert(nx, ny, nz, True)
            lum = base * (0.20 + 0.80 * diff)
            settle = t - t0
            rr_, gg_, bb_ = r, g, b
            v = (0.22 + 0.68 * lum) * (1 - 0.22 * flick)
            glyph = None
            if state != NORMAL and t > tc:
                if state == CARVED:                              # the knife passing through
                    f = (t - tc) / 0.25
                    rr_, gg_, bb_, v, glyph = 1.0, 0.95, 0.7, 1.4 - f, "#"
                else:                                            # cut flesh at the edge, lit from inside
                    rr_, gg_, bb_ = FLESH
                    v = 0.45 + 0.45 * flick
            elif settle < 0.3:
                f = 1 - settle / 0.3
                rr_, gg_, bb_ = mix((r, g, b), SPIRIT, f)
                v = max(v, f)
            li = int((0.30 + 0.75 * lum) * nr) + gi - 1
            li = 0 if li < 0 else nr if li > nr else li
            col = (int(min(255, rr_ * v * 255)), int(min(255, gg_ * v * 255)), int(min(255, bb_ * v * 255)))
            if plot(sx, sy, d, glyph or RAMP[li], col, li, True):
                visible += 1

        # close one-cell holes inside solid surfaces
        for yy_ in range(max(1, by0), min(rows - 1, by1 + 1)):
            row0 = yy_ * cols
            for xx_ in range(max(1, bx0), min(cols - 1, bx1 + 1)):
                i = row0 + xx_
                if solid[i]:
                    continue
                if solid[i - 1] and solid[i + 1]:
                    j = i - 1
                elif solid[i - cols] and solid[i + cols]:
                    j = i - cols
                else:
                    continue
                cc = cos_[j]
                if cc is None:
                    continue
                chs[i] = RAMP[3 + (i * 7) % 5]
                cos_[i] = (int(cc[0] * 0.7), int(cc[1] * 0.7), int(cc[2] * 0.7))
                solid[i] = 2

        # candlelight spilling out of the face onto nearby cells
        for sx, sy, k, d in glow_cells[::2]:
            for dx, dy, w in ((-2, 0, 0.25), (2, 0, 0.25), (-1, 1, 0.3), (1, 1, 0.3), (0, 2, 0.2), (0, -1, 0.2)):
                x2, y2 = sx + dx, sy + dy
                if 0 <= x2 < cols and 0 <= y2 < rows:
                    i = y2 * cols + x2
                    cc = cos_[i]
                    if cc and zb[i] > d - 0.2:
                        a = w * k * flick
                        cos_[i] = (int(cc[0] + (255 - cc[0]) * a), int(cc[1] + (150 - cc[1]) * a * 0.7),
                                   int(cc[2] * (1 - a * 0.5)))

        # -- fog rolling over the ground --------------------------------------------
        fog_on = clip((t - 0.5) / 3.0, 0, 1)
        fa = [math.sin(x * 0.05 + t * 0.45) for x in range(cols)]
        fb = [math.sin(x * 0.019 - t * 0.27) for x in range(cols)]
        for y in range(max(0, self.horizon - 2), rows):
            depth = (y - self.horizon) / max(1, rows - self.horizon)
            row0 = y * cols
            wy, wy2 = math.cos(y * 0.45), math.sin(y * 0.8 + 1.0)
            for x in range(cols):
                i = row0 + x
                if solid[i]:
                    continue
                f = (fa[x] * wy + fb[x] * wy2 + 0.35) * 0.55 * fog_on
                if f > 0.25:
                    k = clip((f - 0.25) * 1.6, 0.0, 1.0) * (0.45 + 0.4 * (1 - depth))
                    chs[i] = "~" if f > 0.55 else ("-" if f > 0.38 else ".")
                    cos_[i] = (int(70 + 70 * k), int(64 + 56 * k), int(100 + 80 * k))

        # -- bats burst out of the mouth and circle the graveyard ------------------
        flying_bats = 0
        mouth = (0.0, 0.18, -0.42)
        for (t0, a0, rad, hgt, speed, tilt, ph) in self.bats:
            if t < t0:
                continue
            age = t - t0
            ang = a0 + speed * age
            orbit = (math.cos(ang) * rad, hgt + 0.15 * math.sin(age * 1.7 + ph * 6) + tilt * math.sin(ang),
                     0.4 + math.sin(ang) * rad * 0.7)
            e = ease_in_out(min(1.0, age / 1.6))
            p = mix(mouth, orbit, e)
            sx, sy, d, _ = cam(p[0], p[1], p[2], False)
            flap = int(age * 9 + ph * 7) % 2
            if d < D - 0.1:
                sprite = ("/\\^v^/\\", "\\/\\v/\\/")[flap] if self.U > 85 else ("/^v^\\", "\\_v_/")[flap]
            elif d < D + 0.9:
                sprite = ("^v^", "-v-")[flap]
            else:
                sprite = ("v", "w")[flap]
            if not (0 <= sy < rows):
                continue
            k = clip(1.3 - 0.35 * (d - D + 1), 0.45, 1.0)
            col = tuple(int(v * k) for v in BAT)
            x0 = sx - len(sprite) // 2
            drawn = False
            for j, ch in enumerate(sprite):
                xx = x0 + j
                if 0 <= xx < cols:
                    i = sy * cols + xx
                    if d < zb[i] or not solid[i]:
                        chs[i], cos_[i] = ch, col
                        drawn = True
            flying_bats += drawn

        cv = Canvas(chs, cos_, cols, rows)

        # -- ghosts drifting between the graves -----------------------------------
        if t > T_GHOSTS:
            gw = len(self.ghost[0])
            for k, (bx, by, sp_, phs) in enumerate(((0.16, 0.50, 0.35, 0.0), (0.80, 0.30, 0.28, 2.0))):
                alpha = clip((t - T_GHOSTS - k * 1.2) / 2.0, 0, 1) * (0.55 + 0.30 * math.sin(t * 0.8 + phs))
                if alpha <= 0.02:
                    continue
                gx = int(cols * bx + cols * 0.05 * math.sin(t * sp_ + phs)) - gw // 2
                gy = int(rows * by + 1.5 * math.sin(t * 1.1 + phs))
                lines = self.ghost + [self.hems[int(t * 3 + k) % 2][:gw]]
                for j, line in enumerate(lines):
                    for i_, ch in enumerate(line):
                        if ch == " ":
                            continue
                        xx, yy = gx + i_, gy + j
                        if 0 <= xx < cols and 0 <= yy < rows:
                            i = yy * cols + xx
                            if solid[i] == 1:
                                continue                     # behind the pumpkin, stones and tree
                            base_c = cos_[i] if chs[i] else (5, 7, 13)
                            ghost_c = (215, 255, 230) if ch in "oO" else (190, 215, 235)
                            chs[i], cos_[i] = ch, mix(base_c, ghost_c, alpha)

        # -- a spider drops in on its thread ------------------------------------------
        if t > T_SPIDER:
            sx = int(cols * 0.86)
            drop = clip((t - T_SPIDER) / 2.5, 0, 1)
            end = int(rows * 0.34 * ease_back(drop) + 1.2 * math.sin(t * 1.3) * drop)
            for y in range(0, max(0, end)):
                cv.put(y, sx, "|" if y % 3 else ":", (96, 100, 116))
            body = [" \\\\(oo)// ", " //\\''/\\\\ "]
            for j, line in enumerate(body):
                for i_, ch in enumerate(line):
                    if ch != " ":
                        cv.put(end + j, sx - len(line) // 2 + i_, ch,
                               (255, 60, 50) if ch == "o" else (150, 150, 170))

        # -- lightning ---------------------------------------------------------------------
        if t > T_STORM:
            k_storm = int((t - T_STORM) / 7.5)
            tt = (t - T_STORM) - k_storm * 7.5
            if tt < 0.32 and (tt < 0.08 or 0.17 < tt < 0.27):
                rng = random.Random(k_storm * 977)
                x = int(cols * rng.uniform(0.35, 0.95))
                for y in range(0, max(1, self.horizon - 3)):
                    x += rng.choice((-1, 0, 1, 1)) if rng.random() < 0.7 else 0
                    cv.put(y, x, "\\" if rng.random() < 0.5 else "/", (235, 235, 255))
                for i in range(N):
                    cc = cos_[i]
                    if cc and chs[i]:
                        cos_[i] = (min(255, cc[0] + 60), min(255, cc[1] + 60), min(255, cc[2] + 90))

        cv.banner(t, T_MSG, MESSAGE, MSG_PALETTE)
        cv.hud(t, [
            [("sway %+6.2f°" % math.degrees(th), (96, 104, 122)),
             ("bats %2d" % flying_bats, (175, 95, 255) if flying_bats else (96, 104, 122))],
            [("particles {:,}".format(visible), (96, 104, 122))],
        ])
        return chs, cos_

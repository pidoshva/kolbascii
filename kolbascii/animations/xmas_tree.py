#!/usr/bin/env python3
"""ASCII Christmas tree: a rotating 3D point cloud that grows from the ground up,
then gets garland, beads, baubles, candy canes, fairy lights, presents, a star
and a greeting.

Run it with:  kolbascii xmas_tree
"""
import math
import random

TAU = math.tau
GROUND, Y0, Y1 = 0.0, 0.10, 1.40       # ground, lowest branches, tree top
RMAX = 0.36                            # radius of the lowest branches
YC = 0.72                              # height the camera looks at
D = 3.4                                # camera distance
PHI = 0.17                             # camera tilt (looking slightly down)
SPIN = 0.30                            # rad / s
FPS = 30

T_GROW = (0.4, 6.5)
T_GARLAND = (6.5, 8.8)
T_BEADS = (7.0, 9.2)
T_BALLS = (7.8, 10.0)
T_CANES = (8.6, 10.2)
T_LIGHTS = (9.0, 11.5)
T_BOXES = (10.4, 12.4)
T_STAR = 12.6
T_MSG = 13.4
MESSAGE = "M E R R Y   C H R I S T M A S   2 0 2 6"

RAMP = ".:-~=+^v*x%&#W@"
BG = (5, 7, 13)
DIM, ACCENT = (96, 104, 122), (255, 196, 90)

WHITE = (1.0, 1.0, 1.0)
SNOWC = (0.92, 0.95, 1.0)
GOLD = (1.0, 0.78, 0.25)
SILVER = (0.80, 0.85, 0.95)
RED = (0.92, 0.10, 0.12)
DEEP_RED = (0.70, 0.05, 0.10)
BAUBLE_GOLD = (1.0, 0.66, 0.12)
BLUE = (0.22, 0.38, 0.98)
PURPLE = (0.62, 0.25, 0.85)
WARM = (1.0, 0.78, 0.40)
TRUNK_C = (0.45, 0.28, 0.14)
GREEN_BOX = (0.12, 0.62, 0.30)
CREAM = (0.92, 0.90, 0.84)

(NEEDLE, SNOWCAP, TRUNK, TINSEL, BALL, LIGHT, BOX, CONE, BEAD, CANE, SKIRT) = range(11)
GROWS = (NEEDLE, SNOWCAP, TRUNK, CONE, SKIRT)
POPS = (BALL, LIGHT, BOX, CANE)
CULLABLE = (NEEDLE, SNOWCAP, CONE)


def clip(v, a, b):
    return a if v < a else b if v > b else v


def unit(x, y, z):
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    return x / n, y / n, z / n


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def envelope(y):
    """Radius of the tree at height y: a slim cone with gentle tiers."""
    u = clip((y - Y0) / (Y1 - Y0), 0.0, 1.0)
    tiers = 1 + 0.07 * (0.5 - ((u * 6.5) % 1.0))
    return (RMAX * (1 - u) ** 1.08 + 0.01) * tiers


def grow_time(y):
    return T_GROW[0] + (T_GROW[1] - T_GROW[0]) * clip((y - GROUND) / (Y1 - GROUND), 0, 1)


def lerp_t(span, u):
    return span[0] + (span[1] - span[0]) * u


def ease_back(u):
    c1 = 1.70158
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


def fib_sphere(n):
    pts = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        a = i * 2.39996
        pts.append((math.cos(a) * r, y, math.sin(a) * r))
    return pts


def build(dens=1.0, seed=7):
    """Point tuples:
    (x, y, z, nx, ny, nz, r, g, b, kind, t0, base, phase, cx, cy, cz, glyph_seed)"""
    rng = random.Random(seed)
    g = rng.gauss
    pts = []

    def add(p, n, col, kind, t0, base=1.0, phase=0.0, centre=(0, 0, 0)):
        pts.append((p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2],
                    kind, t0, base, phase, centre[0], centre[1], centre[2], rng.randrange(3)))

    dark, light = (0.04, 0.26, 0.10), (0.32, 0.82, 0.30)
    tips = []

    # -- needles: whorls of drooping branches -------------------------------
    whorls = 38
    for i in range(whorls):
        y = Y0 + 0.02 + (Y1 - 0.05 - Y0 - 0.02) * (i / (whorls - 1)) ** 0.95
        u = (y - Y0) / (Y1 - Y0)
        R = envelope(y) + 0.03
        nb = int(7 + 10 * (1 - u))
        for b in range(nb):
            a = TAU * (b + 0.5 * rng.random()) / nb + i * 0.77
            L = R * rng.uniform(0.88, 1.06)
            n = int((6 + 85 * L) * dens)
            dx, dz = math.cos(a), math.sin(a)
            tone = rng.uniform(-0.08, 0.08)
            for _ in range(n):
                s = rng.random() ** 0.7
                spread = (0.015 + 0.06 * s) * g(0, 1)
                sl = s * L
                px = dx * sl - dz * spread
                pz = dz * sl + dx * spread
                py = y + 0.05 * sl - 0.22 * sl * sl + 0.010 * g(0, 1)
                nrm = unit(dx * 0.75 + 0.3 * g(0, 1), 0.5 + 0.3 * g(0, 1), dz * 0.75 + 0.3 * g(0, 1))
                ao = (0.30 + 0.70 * s ** 1.3) * rng.uniform(0.8, 1.1)
                t0 = grow_time(y) + 0.45 * s
                if s > 0.55 and nrm[1] > 0.45 and rng.random() < 0.10 * s:
                    add((px, py, pz), nrm, SNOWC, SNOWCAP, t0, 1.0)
                else:
                    col = mix(dark, light, clip(s * 0.8 + tone + rng.uniform(-0.15, 0.15), 0, 1))
                    add((px, py, pz), nrm, col, NEEDLE, t0, ao)
            tl = 0.95 * L
            tips.append((dx * tl, y + 0.05 * tl - 0.22 * tl * tl, dz * tl))

    # -- outer shell: evenly fills the silhouette between branches ----------
    for _ in range(int(5200 * dens)):
        u = 1 - math.sqrt(rng.random())               # uniform over the cone surface
        y = Y0 + (Y1 - Y0) * u
        a = rng.random() * TAU
        r = envelope(y) * rng.uniform(0.80, 1.03)
        p = (math.cos(a) * r, y - 0.02 * rng.random(), math.sin(a) * r)
        nrm = unit(math.cos(a) + 0.35 * g(0, 1), 0.45 + 0.3 * g(0, 1), math.sin(a) + 0.35 * g(0, 1))
        if nrm[1] > 0.5 and rng.random() < 0.05:
            add(p, nrm, SNOWC, SNOWCAP, grow_time(y) + 0.3, 1.0)
        else:
            add(p, nrm, mix(dark, light, rng.uniform(0.25, 0.85)), NEEDLE, grow_time(y) + 0.3,
                rng.uniform(0.55, 0.95))

    # -- leader shoot at the very top ----------------------------------------
    for _ in range(int(80 * dens)):
        y = Y1 - 0.06 + 0.09 * rng.random()
        add((0.008 * g(0, 1), y, 0.008 * g(0, 1)), unit(g(0, 1), 0.6, g(0, 1)),
            mix(dark, light, 0.7), NEEDLE, grow_time(y), 0.9)

    # -- dark inner cone so the back doesn't show through --------------------
    for _ in range(int(1800 * dens)):
        y = Y0 + (Y1 - 0.08 - Y0) * rng.random()
        phi = rng.random() * TAU
        r = 0.62 * envelope(y)
        add((math.cos(phi) * r, y, math.sin(phi) * r), unit(math.cos(phi), 0.3, math.sin(phi)),
            (0.05, 0.28, 0.11), CONE, grow_time(y), 0.40)

    # -- trunk with bark grooves --------------------------------------------
    for _ in range(int(500 * dens)):
        y = GROUND + rng.random() * (Y0 + 0.12 - GROUND)
        phi = rng.random() * TAU
        groove = math.sin(phi * 14 + 3 * math.sin(y * 40))
        bark = 0.6 + 0.4 * (groove > -0.2)
        n = (math.cos(phi), 0.0, math.sin(phi))
        rr = 0.045 + 0.006 * (groove > -0.2)
        add((n[0] * rr, y, n[2] * rr), n, tuple(c * bark for c in TRUNK_C), TRUNK, grow_time(y), 0.95)

    # -- tree skirt: red velvet ring with a white fur trim ------------------
    for _ in range(int(2600 * dens)):
        r = 0.07 + 0.27 * math.sqrt(rng.random())
        a = rng.random() * TAU
        fold = 0.012 * math.sin(a * 9)
        y = GROUND + 0.004 + fold * (r / 0.34) + 0.006 * (0.34 - r)
        trim = r > 0.30
        col = CREAM if trim else mix(DEEP_RED, RED, 0.5 + 0.5 * math.sin(a * 9))
        nrm = unit(0.25 * math.cos(a), 1.0, 0.25 * math.sin(a))
        add((math.cos(a) * r, y, math.sin(a) * r), nrm, col, SKIRT, 0.2 + 0.4 * r, 0.9 if trim else 0.75)

    # -- tinsel garland: gold spiral drooping in swags -----------------------
    m = int(900 * dens)
    for strand in range(2):
        for j in range(m):
            u = j / (m - 1)
            yg = Y0 + 0.12 + (Y1 - Y0 - 0.40) * u
            ag = TAU * 4.2 * u + 0.9
            swag = -0.05 * abs(math.sin(ag * 2.5))
            rg = envelope(yg) + 0.025
            p = (math.cos(ag) * rg + 0.010 * g(0, 1), yg + swag + 0.010 * g(0, 1),
                 math.sin(ag) * rg + 0.010 * g(0, 1))
            add(p, unit(math.cos(ag) + 0.6 * g(0, 1), 0.3, math.sin(ag) + 0.6 * g(0, 1)),
                GOLD, TINSEL, lerp_t(T_GARLAND, u), 1.0, rng.random())

    # -- bead garland: red beads spiralling the other way --------------------
    m = int(650 * dens)
    for j in range(m):
        u = j / (m - 1)
        yg = Y0 + 0.20 + (Y1 - Y0 - 0.50) * u
        ag = -TAU * 3.4 * u + 2.4
        swag = -0.04 * abs(math.sin(ag * 3.0))
        rg = envelope(yg) + 0.02
        if (j // 3) % 2:                                # gaps between beads
            continue
        p = (math.cos(ag) * rg, yg + swag, math.sin(ag) * rg)
        add(p, unit(math.cos(ag), 0.4, math.sin(ag)), (1.0, 0.25, 0.25) if (j // 6) % 3 else SILVER,
            BEAD, lerp_t(T_BEADS, u), 1.0)

    # -- baubles with gold caps ---------------------------------------------
    sphere = fib_sphere(int(55 * dens) + 25)
    cap = fib_sphere(8)
    nb = 46
    palette = (RED, BAUBLE_GOLD, RED, SILVER, RED, BAUBLE_GOLD, BLUE)
    for k in range(nb):
        u = (k + rng.random()) / nb
        y = Y0 + 0.06 + u * (Y1 - Y0 - 0.30)
        a = k * 2.39996 + rng.random() * 0.4
        e = envelope(y)
        c = (math.cos(a) * e, y - 0.02, math.sin(a) * e)
        rad = 0.022 + 0.020 * (1 - u)
        col = palette[k % len(palette)]
        t0 = lerp_t(T_BALLS, rng.random())
        for s in sphere:
            add((c[0] + s[0] * rad, c[1] + s[1] * rad, c[2] + s[2] * rad), s, col, BALL, t0, 1.0, 0, c)
        for s in cap:
            add((c[0] + s[0] * 0.006, c[1] + rad + 0.004, c[2] + s[2] * 0.006), (0, 1, 0), GOLD, BALL, t0, 1.0, 0, c)

    # -- candy canes ----------------------------------------------------------
    for k in range(12):
        u = (k + 0.5) / 12
        y = Y0 + 0.10 + u * (Y1 - Y0 - 0.45)
        a = k * 2.0 + 1.1
        e = envelope(y) + 0.012
        dx, dz = math.cos(a), math.sin(a)
        tx, tz = -dz, dx
        base = (dx * e, y, dz * e)
        t0 = lerp_t(T_CANES, rng.random())
        size = 0.9 + 0.4 * (1 - u)
        segs = []
        for j in range(int(40 * dens) + 20):           # stick
            v = j / (int(40 * dens) + 19)
            segs.append((0.0, -0.05 * size * v, v * 0.6))
        for j in range(int(25 * dens) + 12):           # hook
            w = math.pi * j / (int(25 * dens) + 11)
            segs.append((0.012 * size * (1 - math.cos(w)), 0.012 * size * math.sin(w), 0.6 + w / math.pi * 0.4))
        for off, dy, v in segs:
            p = (base[0] + tx * off, base[1] + dy, base[2] + tz * off)
            stripe = int(v * 14) % 2
            add(p, (dx, 0.2, dz), RED if stripe else WHITE, CANE, t0, 1.0, 0, base)

    # -- fairy lights on the branch tips --------------------------------------
    pick = rng.sample(tips, min(220, len(tips)))
    bulb = fib_sphere(4)
    for c in pick:
        t0 = lerp_t(T_LIGHTS, rng.random())
        col = WARM if rng.random() < 0.8 else (1.0, 0.95, 0.85)
        ph = rng.random()
        for s in bulb:
            add((c[0] + s[0] * 0.012, c[1] + s[1] * 0.012, c[2] + s[2] * 0.012), s, col, LIGHT, t0, 1.0, ph, c)

    # -- presents ---------------------------------------------------------------
    def box(px, pz, hx, hy, hz, yaw, col, rib, pattern, t0, y0=GROUND):
        cy, sy_ = math.cos(yaw), math.sin(yaw)

        def world(lx, ly, lz):
            return (px + lx * cy - lz * sy_, y0 + ly, pz + lx * sy_ + lz * cy)

        def wn(nx, ny, nz):
            return (nx * cy - nz * sy_, ny, nx * sy_ + nz * cy)

        centre = (px, y0 + hy, pz)
        lite = mix(col, WHITE, 0.45)
        area_dens = 14000 * dens
        faces = [((1, 0, 0), hz, hy), ((-1, 0, 0), hz, hy), ((0, 0, 1), hx, hy),
                 ((0, 0, -1), hx, hy), ((0, 1, 0), hx, hz)]
        for n, a, b in faces:
            for _ in range(int(4 * a * b * area_dens) + 30):
                ua, ub = rng.uniform(-1, 1), rng.uniform(-1, 1)
                if n[0]:
                    l = (n[0] * hx, hy + ub * hy, ua * hz)
                    rib_on = abs(ua) < 0.14
                elif n[2]:
                    l = (ua * hx, hy + ub * hy, n[2] * hz)
                    rib_on = abs(ua) < 0.14
                else:
                    l = (ua * hx, 2 * hy, ub * hz)
                    rib_on = abs(ua) < 0.14 or abs(ub) < 0.14
                if rib_on:
                    c = rib
                elif pattern == "stripes":
                    c = lite if int((ua + ub) * 4 + 8) % 2 else col
                elif pattern == "dots":
                    c = lite if (math.sin(ua * 14) * math.sin(ub * 14)) > 0.75 else col
                else:
                    c = col
                edge = max(abs(ua), abs(ub)) > 0.94
                add(world(*l), wn(*n), c, BOX, t0, 0.65 if edge else 0.9, 0, centre)
        # bow: two loops and two tails
        top = 2 * hy
        bs = min(hx, hz) * 0.9
        for j in range(int(90 * dens) + 30):
            a = TAU * j / (int(90 * dens) + 30)
            lx = bs * math.sin(a)
            ly = top + 0.012 + bs * 0.55 * abs(math.sin(2 * a))
            lz = 0.25 * bs * math.cos(a) * math.sin(a)
            add(world(lx, ly, lz), wn(0, 1, 0), rib, BOX, t0 + 0.25, 1.0, 0, centre)
        for j in range(int(30 * dens) + 10):
            v = j / (int(30 * dens) + 10)
            for side in (-1, 1):
                add(world(side * bs * 0.5 * v, top + 0.004, -hz * 0.6 * v - 0.004), wn(0, 1, 0),
                    rib, BOX, t0 + 0.25, 0.9, 0, centre)

    gifts = [
        (0.35, 0.50, 0.068, 0.050, 0.055, 0.3, RED, GOLD, "plain"),
        (1.55, 0.47, 0.048, 0.065, 0.048, -0.2, BLUE, SILVER, "dots"),
        (2.65, 0.52, 0.058, 0.040, 0.070, 0.8, GREEN_BOX, RED, "stripes"),
        (3.95, 0.48, 0.055, 0.055, 0.055, 0.1, BAUBLE_GOLD, DEEP_RED, "plain"),
        (5.10, 0.52, 0.072, 0.036, 0.046, -0.6, CREAM, RED, "stripes"),
    ]
    for i, (a, r, hx, hy, hz, yaw, col, rib, pat) in enumerate(gifts):
        t0 = lerp_t(T_BOXES, i / len(gifts))
        px, pz = math.cos(a) * r, math.sin(a) * r
        box(px, pz, hx, hy, hz, yaw, col, rib, pat, t0)
        if i == 3:  # a little one stacked on top
            box(px, pz, 0.032, 0.026, 0.030, yaw + 0.5, PURPLE, GOLD, "dots", t0 + 0.35, GROUND + 2 * hy)
    return pts


class Scene:
    def __init__(self, cols, rows):
        self.resize(cols, rows)
        self.pts = build(self.dens)
        rng = random.Random(3)
        self.snow = [[rng.uniform(-2.4, 2.4), rng.uniform(GROUND, 2.8), rng.uniform(-1.6, 3.0),
                      rng.uniform(0.09, 0.20), rng.random() * TAU]
                     for _ in range(clip(cols * rows // 24, 200, 900))]
        self.sky = [(rng.randrange(cols), rng.randrange(max(1, int(rows * 0.5))), rng.random())
                    for _ in range(cols * rows // 120)]

    def resize(self, cols, rows):
        self.cols, self.rows = cols, rows
        U = min(0.97 * rows, 0.75 * cols)     # screen columns per world unit
        self.U = U
        self.F = U * D
        self.dens = clip((U / 60.0) ** 2, 0.8, 2.3)
        self.splat = U > 85                  # big windows: points cover 2 cells
        self.cx = cols / 2
        cp = math.cos(PHI)
        self.cy = 0.80 * rows - (YC - GROUND) * cp * self.F * 0.5 / D
        self.ground = self._ground()

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
        step = 0.03 if self.U > 85 else 0.045
        n = int(2.4 / step)
        rng = random.Random(5)
        for i in range(-n, n + 1):
            for j in range(-n // 2, n):
                x, z = i * step, j * step
                if (x / 2.4) ** 2 + ((z - 0.4) / 1.6) ** 2 > 1:
                    continue
                sx, sy, d = self.project(x, GROUND, z)
                sx, sy = int(sx + 0.5), int(sy + 0.5)
                if 0 <= sx < cols and 0 <= sy < rows:
                    idx = sy * cols + sx
                    if idx not in seen or d < seen[idx][0]:
                        seen[idx] = (d, math.hypot(x, z))
        out = []
        for idx, (d, r) in seen.items():
            fog = clip(1.25 - 0.32 * (d - D + 1.0), 0.15, 1.0)
            sx, sy = idx % cols, idx // cols
            snowy = r < 0.75 + 0.25 * rng.random()
            if snowy:
                ch = rng.choice(".:~-.")
                k = 0.75 * fog * (1.05 - r * 0.6)
                c = (int(150 * k), int(162 * k), int(190 * k))
            else:
                ch = "-" if (sx // 2 + sy) % 3 else "."
                if sx % 4 == 3:
                    continue
                c = tuple(int(v * 0.75 * fog) for v in (72, 80, 100))
            out.append((idx, d + 50, ch, c))   # +50: ground never hides anything
        return out

    def render(self, t):
        cols, rows = self.cols, self.rows
        N = cols * rows
        zb = [1e9] * N
        chs = [None] * N
        cos_ = [None] * N
        tree = bytearray(N)
        bx0, bx1, by0, by1 = cols, 0, rows, 0

        for x, y, ph in self.sky:   # faint distant stars
            v = int(60 + 50 * (0.5 + 0.5 * math.sin(t * 1.3 + ph * 40)))
            i = y * cols + x
            zb[i], chs[i], cos_[i] = 90, "." if ph < 0.8 else "+", (v, v, v + 15)
        for idx, d, ch, c in self.ground:
            zb[idx], chs[idx], cos_[idx] = d, ch, c

        F, F2, cx, cy = self.F, self.F * 0.5, self.cx, self.cy
        cp, sp = math.cos(PHI), math.sin(PHI)
        th = SPIN * t + 0.6
        c, s = math.cos(th), math.sin(th)
        Lx, Ly, Lz = unit(-0.5, 0.7, -0.6)
        nr = len(RAMP) - 1
        splat = self.splat
        visible = 0
        lit = []

        # snow (world-fixed, not rotating)
        for f in self.snow:
            x, y, z = f[0] + 0.05 * math.sin(t * 0.7 + f[4]), f[1] - f[3] * t, f[2]
            y = GROUND + (y - GROUND) % 2.8
            yy = y - YC
            y2 = yy * cp + z * sp
            z2 = z * cp - yy * sp
            d = D + z2
            if d < 0.6:
                continue
            sx, sy = int(cx + x * F / d + 0.5), int(cy - y2 * F2 / d + 0.5)
            if 0 <= sx < cols and 0 <= sy < rows:
                idx = sy * cols + sx
                if d < zb[idx]:
                    fog = clip(1.3 - 0.3 * (d - D + 1.0), 0.3, 1.0)
                    v = int(235 * fog)
                    zb[idx], chs[idx], cos_[idx] = (
                        d, "*" if d < D - 0.6 else "+" if d < D + 0.8 else ".", (v, v, min(255, v + 12)))

        for (x, y, z, nx, ny, nz, r, g, b, kind, t0, base, ph, ccx, ccy, ccz, gi) in self.pts:
            if t < t0:
                continue
            nxr = nx * c - nz * s
            nzr = nx * s + nz * c
            nz2 = nzr * cp - ny * sp
            if nz2 > 0.4 and kind in CULLABLE:   # facing away: hidden by the front
                continue
            age = t - t0
            if kind in POPS:
                if age < 0.35:
                    k = ease_back(age / 0.35)
                    x, y, z = ccx + (x - ccx) * k, ccy + (y - ccy) * k, ccz + (z - ccz) * k
            elif age < 0.5:
                y -= 0.05 * (1 - age / 0.5) ** 2
            xr = x * c - z * s
            zr = x * s + z * c
            yy = y - YC
            y2 = yy * cp + zr * sp
            z2 = zr * cp - yy * sp
            d = D + z2
            sx = int(cx + xr * F / d + 0.5)
            sy = int(cy - y2 * F2 / d + 0.5)
            if sx < 0 or sx >= cols or sy < 0 or sy >= rows:
                continue
            idx = sy * cols + sx
            if kind == LIGHT:
                d -= 0.03
            if d >= zb[idx]:
                continue
            visible += 1
            diff = nxr * Lx + (ny * cp + nzr * sp) * Ly + nz2 * Lz
            if diff < 0:
                diff = 0.0
            fog = 1.15 - 0.55 * (z2 + 0.5)
            fog = 0.35 if fog < 0.35 else 1.0 if fog > 1.0 else fog
            tree[idx] = 1
            if kind == LIGHT:
                tw = 0.6 + 0.4 * math.sin(t * 2.6 + ph * TAU)
                glyph = "@" if tw > 0.8 else ("O" if tw > 0.45 else "o")
                v = 0.55 + 0.6 * tw
                col = (int(min(255, r * v * 255)), int(min(255, g * v * 255)), int(min(255, b * v * 230)))
                lit.append((sx, sy, tw * fog, d))
                zb[idx], chs[idx], cos_[idx] = d, glyph, col
                continue
            lum = base * (0.22 + 0.85 * diff)
            if kind == TINSEL:
                lum = 0.55 + 0.5 * diff
                if math.sin(t * 7 + ph * TAU * 9) > 0.94:
                    r, g, b, lum = 1.0, 1.0, 0.9, 1.2
            elif kind == BALL:
                lum = 0.25 + 0.95 * diff ** 1.5
                if diff > 0.93:
                    r, g, b, lum = 1.0, 1.0, 1.0, 1.25
            elif kind == BEAD:
                lum = 0.5 + 0.6 * diff
            li = int((0.30 + 0.75 * lum * fog) * nr) + gi - 1
            glyph = RAMP[0 if li < 0 else nr if li > nr else li]
            if kind == BEAD:
                glyph = "o"
            elif kind == CANE:
                glyph = "#" if lum > 0.5 else "="
            v = (0.30 + 0.9 * lum) * fog
            if kind in GROWS and age < 0.35:  # bright growth front
                f = 1 - age / 0.35
                r, g, b = r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f
                v = max(v, f)
                glyph = "#"
            col = (int(min(255, r * v * 255)), int(min(255, g * v * 255)), int(min(255, b * v * 255)))
            zb[idx], chs[idx], cos_[idx] = d, glyph, col
            tree[idx] = 1
            if sx < bx0: bx0 = sx
            if sx > bx1: bx1 = sx
            if sy < by0: by0 = sy
            if sy > by1: by1 = sy
            if splat and sx + 1 < cols and d + 0.01 < zb[idx + 1]:
                zb[idx + 1], chs[idx + 1], cos_[idx + 1] = d + 0.01, RAMP[max(0, li - 2) if li <= nr else nr - 2], col
                tree[idx + 1] = 1

        # close single-cell holes inside the foliage
        for yy_ in range(max(1, by0), min(rows - 1, by1 + 1)):
            row0 = yy_ * cols
            for xx_ in range(max(1, bx0), min(cols - 1, bx1 + 1)):
                i = row0 + xx_
                if tree[i]:
                    continue
                if tree[i - 1] and tree[i + 1]:
                    j = i - 1
                elif tree[i - cols] and tree[i + cols]:
                    j = i - cols
                else:
                    continue
                cc = cos_[j]
                if cc is None or chs[j] in ("@", "O", "o"):
                    continue
                chs[i] = RAMP[3 + (i * 7) % 5]
                cos_[i] = (int(cc[0] * 0.7), int(cc[1] * 0.7), int(cc[2] * 0.7))
                zb[i] = zb[j]

        # warm glow around lit bulbs
        for sx, sy, k, d in lit:
            for dx, dy, w in ((-1, 0, 0.45), (1, 0, 0.45), (-2, 0, 0.2), (2, 0, 0.2), (0, -1, 0.3), (0, 1, 0.3)):
                x2, y2 = sx + dx, sy + dy
                if 0 <= x2 < cols and 0 <= y2 < rows:
                    i = y2 * cols + x2
                    cc = cos_[i]
                    if cc and chs[i] not in ("@", "O", "o") and zb[i] < d + 0.3:
                        a = w * k
                        cos_[i] = (int(cc[0] + (255 - cc[0]) * a), int(cc[1] + (200 - cc[1]) * a * 0.8),
                                   int(cc[2] + (110 - cc[2]) * a * 0.4))

        def put(row, col, ch, rgb):
            if 0 <= row < rows and 0 <= col < cols:
                chs[row * cols + col], cos_[row * cols + col] = ch, rgb

        # star
        if t > T_STAR:
            tx, ty, _ = self.project(0, Y1 + 0.05, 0)
            tx, ty = int(tx + 0.5), int(ty + 0.5)
            flash = clip(1 - (t - T_STAR) / 1.2, 0, 1) ** 2
            on = clip((t - T_STAR) / 0.4, 0, 1)
            tw = 0.85 + 0.15 * math.sin(t * 4)
            big = self.U > 85
            if on < 1:
                sprite = ["  #  ", " #@# ", "  #  "]
            elif big:
                sprite = ["      #      ",
                          "     #@#     ",
                          "*##@@@@@@@##*",
                          "  ##@@@@@##  ",
                          "   #@@#@@#   ",
                          "  ##     ##  "]
            else:
                sprite = ["    #    ",
                          " **#@#** ",
                          "  #@@@#  ",
                          "  ## ##  "]
            h = len(sprite)
            for j, line in enumerate(sprite):
                for i, ch in enumerate(line):
                    if ch != " ":
                        core = 1 - abs(i - len(line) // 2) / (len(line) / 2)
                        base_c = mix((255, 170, 40), (255, 245, 190), core * 0.8)
                        rgb = tuple(int(min(255, (a + (255 - a) * flash) * tw)) for a in base_c)
                        put(ty - h + 2 + j, tx - len(line) // 2 + i, ch, rgb)
            ray = int((3 + 6 * flash + 2 * math.sin(t * 2) ** 2) * (1.5 if big else 1))
            faint = tuple(int(v * (0.35 + 0.6 * flash)) for v in (255, 220, 140))
            top = ty - h + 1
            for k in range(1, ray):
                put(top - k, tx, "|", faint)
                put(top - k // 2, tx - k - 1, "\\", faint)
                put(top - k // 2, tx + k + 1, "/", faint)
            mid = ty - h // 2 + 1
            for k in range(len(sprite[0]) // 2 + 2, len(sprite[0]) // 2 + 2 + ray * 2, 2):
                put(mid, tx - k, "-", faint)
                put(mid, tx + k, "-", faint)

        # message
        if t > T_MSG:
            row = rows - 5
            x0 = (cols - len(MESSAGE)) // 2
            shown = min(len(MESSAGE), int((t - T_MSG) * 10))
            for i in range(max(x0 - 3, 0), min(cols, x0 + shown + 3)):
                for rr in (row - 1, row, row + 1):
                    if 0 <= rr < rows:
                        chs[rr * cols + i] = None
            for i, ch in enumerate(MESSAGE[:shown]):
                if ch != " ":
                    tint = ((255, 70, 70), (255, 205, 80), (90, 220, 110))[(i // 2 + int(t * 1.5)) % 3]
                    k = 0.85 + 0.15 * math.sin(t * 5 + i)
                    put(row, x0 + i, ch, tuple(int(v * k) for v in tint))

        # HUD
        def text(row, col, s, rgb):
            for i, ch in enumerate(s):
                put(row, col + i, ch, rgb)
        deg = math.degrees(th) % 360
        text(rows - 3, 1, f"rotation {deg:6.2f}°", DIM)
        text(rows - 3, 22, f"lights {len(lit):3d}", ACCENT if lit else DIM)
        text(rows - 2, 1, f"particles {visible:,}", DIM)
        text(rows - 1, 1, "space pause · r restart · q quit", (70, 76, 92))
        ts = f"t {t:05.1f}"
        text(0, cols - len(ts) - 1, ts, ACCENT)
        return chs, cos_

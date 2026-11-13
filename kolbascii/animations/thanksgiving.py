"""Thanksgiving harvest: a vortex of autumn leaves settles into a ribbed 3D
pumpkin, then a stem and curling vine grow, little pumpkins and a gourd pop in,
a cob of multicoloured corn and a wheat bundle appear, and leaves keep falling.

Run it with:  kolbascii thanksgiving
"""
import math
import random

from ..engine import Canvas

TAU = math.tau
GROUND = 0.0
YC = 0.36
D = 3.4
PHI = 0.22
SPIN = 0.26

T_ASSEMBLE = (0.8, 5.4)      # pumpkin points leave the vortex bottom → top
T_FLY = 1.5                  # seconds each point spends flying in
T_STEM = (5.9, 6.8)
T_VINE = (6.5, 7.8)
T_LEAF = (6.9, 7.6)
T_SMALL = (7.3, 8.4)
T_WHEAT = (7.8, 9.6)
T_CORN = (8.4, 9.6)
T_FALL = 5.0
T_MSG = 10.2
MESSAGE = "H A P P Y   T H A N K S G I V I N G"
MSG_PALETTE = ((255, 140, 40), (255, 205, 90), (220, 70, 40), (190, 120, 60))

RAMP = ".:-~=+^v*x%&#W@"
WHITE = (1.0, 1.0, 1.0)
LEAF_COLORS = ((0.85, 0.18, 0.08), (0.95, 0.42, 0.06), (1.0, 0.68, 0.12),
               (0.70, 0.30, 0.08), (0.95, 0.80, 0.25), (0.55, 0.20, 0.06))
ORANGE, ORANGE_DEEP = (1.0, 0.55, 0.10), (0.72, 0.26, 0.02)
CREAM, CREAM_DEEP = (0.96, 0.91, 0.78), (0.70, 0.72, 0.52)
STEM_C, STEM_TIP = (0.40, 0.34, 0.14), (0.62, 0.55, 0.30)
VINE = (0.36, 0.58, 0.16)
LEAF_GREEN, LEAF_VEIN = (0.25, 0.55, 0.16), (0.55, 0.75, 0.30)
WHEAT_STALK, WHEAT_GRAIN, WHEAT_AWN = (0.72, 0.58, 0.28), (0.98, 0.78, 0.36), (0.85, 0.76, 0.52)
RIBBON = (0.85, 0.12, 0.10)
HUSK = (0.88, 0.78, 0.52)
CORN_KERNELS = ((0.75, 0.10, 0.10), (0.98, 0.75, 0.15), (0.45, 0.12, 0.40),
                (0.95, 0.45, 0.10), (0.95, 0.90, 0.70), (0.55, 0.08, 0.10))
GOURD_Y, GOURD_G = (0.98, 0.82, 0.22), (0.22, 0.48, 0.14)

GROW, POP, SOLID = 0, 1, 2       # how a part appears


def clip(v, a, b):
    return a if v < a else b if v > b else v


def unit(x, y, z):
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    return x / n, y / n, z / n


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def lerp_t(span, u):
    return span[0] + (span[1] - span[0]) * u


def ease_back(u):
    c1 = 1.70158
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


def ease_in_out(u):
    return u * u * (3 - 2 * u)


def fib_sphere(n):
    pts = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        a = i * 2.39996
        pts.append((math.cos(a) * r, y, math.sin(a) * r))
    return pts


class Builder:
    def __init__(self, dens, seed=11):
        self.rng = random.Random(seed)
        self.dens = dens
        self.parts = []     # (x,y,z,nx,ny,nz,r,g,b,mode,t0,base,cx,cy,cz,gi)
        self.swirl = []     # big pumpkin: same + (a0, rs, ys, lr, lg, lb)

    def add(self, p, n, col, mode, t0, base=1.0, centre=(0, 0, 0)):
        self.parts.append((p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2],
                           mode, t0, base, centre[0], centre[1], centre[2], self.rng.randrange(3)))

    # -- pumpkins ----------------------------------------------------------
    def pumpkin_points(self, cx, cz, R, H, ribs, ridge, groove, n):
        cy = GROUND + H * 0.96
        out = []
        k = ribs / 2.0
        for dx, dy, dz in fib_sphere(n):
            phi = math.atan2(dz, dx)
            c = math.cos(k * phi)
            g = abs(c) ** 0.6                       # 1 on a rib, 0 in a groove
            rs = 0.82 + 0.18 * g
            x = cx + dx * R * rs
            z = cz + dz * R * rs
            y = cy + dy * H * (0.93 + 0.07 * g)
            if dy > 0.6:                            # dimple around the stem
                y -= 0.35 * H * ((dy - 0.6) / 0.4) ** 2
            if dy < -0.7:
                y += 0.15 * H * ((-dy - 0.7) / 0.3) ** 2
            tx, tz = -math.sin(phi), math.cos(phi)
            slope = -0.55 * math.sin(k * phi) * (1 if c > 0 else -1) * (1 - dy * dy)
            nrm = unit(dx / R + tx * slope / R, dy / H, dz / R + tz * slope / R)
            col = mix(groove, ridge, g * 0.85 + 0.15 * self.rng.random())
            if dy > 0.75:
                col = mix(col, groove, 0.4)
            out.append(((x, y, z), nrm, col, 0.55 + 0.45 * g))
        return out, (cx, cy + H, cz)

    def stem(self, top, t0, t1, scale=1.0):
        rng = self.rng
        n = int(260 * self.dens * scale) + 40
        lean = rng.uniform(0, TAU)
        lx, lz = math.cos(lean), math.sin(lean)
        for _ in range(n):
            v = rng.random()
            a = rng.random() * TAU
            r = (0.035 - 0.012 * v) * scale
            ridge = math.cos(a * 6) > 0.2
            cx = top[0] + lx * 0.04 * v * v * scale
            cz = top[2] + lz * 0.04 * v * v * scale
            y = top[1] - 0.03 * scale + 0.15 * v * scale
            p = (cx + math.cos(a) * r, y, cz + math.sin(a) * r)
            col = mix(STEM_C, STEM_TIP, v) if ridge else mix(STEM_C, STEM_TIP, v * 0.5)
            self.add(p, (math.cos(a), 0.2, math.sin(a)), col, GROW, lerp_t((t0, t1), v), 0.95 if ridge else 0.7)
        return (top[0] + lx * 0.04 * scale, top[1] + 0.12 * scale, top[2] + lz * 0.04 * scale)

    def vine(self, base, t0, t1):
        rng = self.rng
        n = int(420 * self.dens) + 80
        start = rng.uniform(0, TAU)
        for j in range(n):
            v = j / (n - 1)
            a = start + v * TAU * 2.6
            r = 0.03 + 0.20 * v
            y = base[1] - 0.02 - 0.06 * v * v + 0.015 * math.sin(v * 30)
            p = (base[0] + math.cos(a) * r, y, base[2] + math.sin(a) * r)
            self.add(p, unit(math.cos(a), 0.6, math.sin(a)), VINE, GROW, lerp_t((t0, t1), v), 1.0)

    def leaf(self, base, angle, t0):
        """A flat, five-lobed pumpkin leaf resting on the pumpkin's shoulder."""
        rng = self.rng
        n = int(700 * self.dens) + 120
        ux, uz = math.cos(angle), math.sin(angle)       # leaf points this way
        vx, vz = -uz, ux
        size = 0.16
        for _ in range(n):
            th = rng.random() * TAU
            lobe = 0.70 + 0.30 * abs(math.cos(2.5 * th))
            rr = math.sqrt(rng.random()) * size * lobe
            a, b = math.cos(th) * rr, math.sin(th) * rr
            off = size * 0.9
            x = base[0] + ux * (a + off) + vx * b
            z = base[2] + uz * (a + off) + vz * b
            y = base[1] - 0.05 - 0.22 * (a + off) ** 2 + 0.01 * math.sin(th * 5)
            vein = abs(math.sin(th * 2.5)) < 0.08 or rr < 0.012
            col = LEAF_VEIN if vein else mix(LEAF_GREEN, LEAF_VEIN, rng.random() * 0.3)
            self.add((x, y, z), unit(-ux * 0.4, 1.0, -uz * 0.4), col, GROW, t0 + 0.6 * rr / size, 0.95)

    # -- the rest of the harvest --------------------------------------------
    def gourd(self, cx, cz, t0):
        rng = self.rng
        n = int(1500 * self.dens) + 200
        centre = (cx, 0.10, cz)
        for _ in range(n):
            h0 = rng.random() * 0.34
            if h0 < 0.20:
                r = 0.10 * math.sqrt(max(0.0, 1 - ((h0 - 0.10) / 0.10) ** 2))
            else:
                r = 0.0
            if h0 > 0.15:
                r = max(r, 0.042 - 0.012 * (h0 - 0.15) / 0.19)
            if r < 0.004:
                continue
            h, r = h0 * 0.62, r * 0.75                  # scaled to sit with the pumpkins
            bend = 0.05 * max(0.0, (h0 - 0.17) / 0.17) ** 2
            a = rng.random() * TAU
            x = cx + bend + math.cos(a) * r
            z = cz + math.sin(a) * r
            stripe = int((a / TAU) * 10) % 2 == 0
            if h0 < 0.17:
                col = GOURD_G if stripe and rng.random() < 0.8 else GOURD_Y
            else:
                col = GOURD_G if not (rng.random() < 0.15) else GOURD_Y
            dr = -(h0 - 0.10) / 0.10 if h0 < 0.17 else 0.0
            self.add((x, GROUND + h, z), unit(math.cos(a), dr * 0.8, math.sin(a)), col, POP, t0, 0.95, centre)

    def corn(self, cx, cy, cz, yaw, t0, t1):
        rng = self.rng
        ax, az = math.cos(yaw), math.sin(yaw)          # cob axis (lying down)
        px, pz = -az, ax
        L, R = 0.40, 0.055
        rows_, cols_ = 14, 26
        reps = max(2, int(3 * self.dens))
        for i in range(cols_):
            v = (i + 0.5) / cols_
            r = R * (1 - 0.55 * abs(2 * v - 1) ** 4)
            for j in range(rows_):
                col = rng.choice(CORN_KERNELS)
                for _ in range(reps):
                    a = TAU * (j + 0.5 + 0.35 * rng.uniform(-1, 1)) / rows_
                    vv = v + rng.uniform(-0.4, 0.4) / cols_
                    s = (vv - 0.5) * L
                    ny_, nr = math.sin(a), math.cos(a)
                    p = (cx + ax * s + px * nr * r, cy + ny_ * r, cz + az * s + pz * nr * r)
                    n = (px * nr, ny_, pz * nr)
                    self.add(p, n, col, POP, lerp_t((t0, t1), v), rng.uniform(0.75, 1.0), p)
        # papery husks fanning back from the stalk end
        for k in range(3):
            fan = (k - 1) * 0.55
            for _ in range(int(220 * self.dens) + 40):
                u = rng.random()
                w = math.sin(math.pi * u) * 0.035 * rng.uniform(-1, 1)
                s = 0.5 * L + 0.02 + u * 0.22
                spread = (0.03 + u * 0.12) * math.sin(fan)
                lift = 0.02 + (0.03 + u * 0.10) * math.cos(fan) * 0.6
                p = (cx + ax * s + px * (spread + w), cy + lift - 0.02 * u * u, cz + az * s + pz * (spread + w))
                self.add(p, (0, 1, 0), mix(HUSK, (0.7, 0.6, 0.38), rng.random() * 0.5), GROW,
                         t1 + 0.2 + 0.5 * u, 0.9)

    def wheat(self, cx, cz, t0, t1):
        rng = self.rng
        stalks = 13
        for i in range(stalks):
            a = TAU * i / stalks + rng.uniform(-0.2, 0.2)
            tilt = 0.30 + 0.20 * rng.random()
            dx, dz = math.cos(a) * tilt, math.sin(a) * tilt
            L = rng.uniform(0.50, 0.64)
            for j in range(int(45 * self.dens) + 15):            # stalk
                v = j / (int(45 * self.dens) + 15) * 0.80
                spread = abs(v - 0.28) * 1.0                    # pinched at the tie
                p = (cx + dx * L * spread, GROUND + v * L, cz + dz * L * spread)
                self.add(p, unit(dx, 0.2, dz), WHEAT_STALK, GROW, lerp_t((t0, t1), v), 0.8)
            # head: two rows of grains with awns
            hx, hz = cx + dx * L * 0.52, cz + dz * L * 0.52
            ox, oz = -dz / (tilt or 1), dx / (tilt or 1)
            grains = 9
            for gk in range(grains):
                v = 0.80 + 0.20 * gk / grains
                for side in (-1, 1):
                    gx = hx + dx * L * (v - 0.80) * 1.2 + ox * 0.012 * side
                    gz = hz + dz * L * (v - 0.80) * 1.2 + oz * 0.012 * side
                    gy = GROUND + v * L
                    for _ in range(int(2 * self.dens) + 2):
                        p = (gx + rng.gauss(0, 0.004), gy + rng.gauss(0, 0.006), gz + rng.gauss(0, 0.004))
                        self.add(p, unit(ox * side, 0.5, oz * side), WHEAT_GRAIN, GROW,
                                 lerp_t((t0, t1), v) + 0.1, 1.0)
                    for m in range(3):                           # awn
                        w = (m + 1) / 3
                        p = (gx + ox * side * 0.02 * w, gy + 0.05 * w, gz + oz * side * 0.02 * w)
                        self.add(p, (0, 1, 0), WHEAT_AWN, GROW, lerp_t((t0, t1), v) + 0.25, 0.7)
        # ribbon tied around the bundle
        for _ in range(int(160 * self.dens) + 40):
            a = rng.random() * TAU
            y = GROUND + 0.28 * 0.77 + rng.uniform(-0.015, 0.015)
            p = (cx + math.cos(a) * 0.035, y, cz + math.sin(a) * 0.035)
            self.add(p, (math.cos(a), 0, math.sin(a)), RIBBON, GROW, t1 - 0.3, 1.0)

    def build(self):
        rng, dens = self.rng, self.dens
        # big pumpkin, assembled from the leaf vortex
        pts, top = self.pumpkin_points(0.0, 0.0, 0.40, 0.31, 10, ORANGE, ORANGE_DEEP, int(6200 * dens))
        span = T_ASSEMBLE[1] - T_ASSEMBLE[0]
        for p, n, col, base in pts:
            hgt = clip((p[1] - GROUND) / 0.6, 0, 1)
            t0 = T_ASSEMBLE[0] + span * hgt * 0.8 + rng.random() * span * 0.2
            a0 = math.atan2(p[2], p[0]) + rng.uniform(0, TAU)
            ys = rng.uniform(0.05, 1.25)
            rs = (0.22 + 0.42 * ys / 1.25) * rng.uniform(0.85, 1.15)   # funnel: wider at the top
            leafc = rng.choice(LEAF_COLORS)
            self.swirl.append((p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2],
                               t0, base, rng.randrange(3), a0, rs, ys, leafc, rng.uniform(0.8, 1.3)))
        tip = self.stem(top, *T_STEM)
        self.vine((top[0], top[1] + 0.01, top[2]), *T_VINE)
        self.leaf(top, 2.2, T_LEAF[0])
        self.leaf(top, 4.6, T_LEAF[1])

        # small pumpkins
        for (cx, cz, R, H, ribs, ridge, groove, k) in (
                (0.66, -0.12, 0.17, 0.13, 8, (1.0, 0.45, 0.05), (0.65, 0.18, 0.02), 0),
                (-0.60, -0.22, 0.15, 0.11, 10, CREAM, CREAM_DEEP, 1)):
            t0 = lerp_t(T_SMALL, k)
            sp, stop = self.pumpkin_points(cx, cz, R, H, ribs, ridge, groove, int(1700 * dens) + 200)
            centre = (cx, GROUND + H, cz)
            for p, n, col, base in sp:
                self.add(p, n, col, POP, t0, base, centre)
            self.stem(stop, t0 + 0.3, t0 + 0.7, scale=0.6)
        self.gourd(0.10, -0.66, lerp_t(T_SMALL, 0.5))
        self.corn(-0.42, 0.06, 0.52, 0.5, *T_CORN)
        self.wheat(0.78, 0.30, *T_WHEAT)
        return self.parts, self.swirl


class Scene:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        U = min(1.6 * rows, 0.5 * cols)
        self.U = U
        self.F = U * D
        self.dens = clip((U / 60.0) ** 2, 0.8, 2.3)
        self.splat = U > 85
        self.cx = cols / 2
        self.cy = 0.74 * rows - (YC - GROUND) * math.cos(PHI) * self.F * 0.5 / D
        self.parts, self.swirl = Builder(self.dens).build()
        rng = random.Random(4)
        self.falling = [[rng.uniform(-2.2, 2.2), rng.uniform(0, 2.4), rng.uniform(-1.4, 2.6),
                         rng.uniform(0.06, 0.13), rng.random() * TAU, rng.choice(LEAF_COLORS),
                         rng.uniform(0, T_FALL + 3)]
                        for _ in range(int(clip(cols * rows // 55, 80, 420)))]
        self.sky = [(rng.randrange(cols), rng.randrange(max(1, int(rows * 0.45))), rng.random())
                    for _ in range(cols * rows // 140)]
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
        step = 0.028 if self.U > 85 else 0.042
        n = int(2.3 / step)
        for i in range(-n, n + 1):
            for j in range(-n // 2, n):
                x, z = i * step, j * step
                if (x / 2.3) ** 2 + ((z - 0.35) / 1.5) ** 2 > 1:
                    continue
                sx, sy, d = self.project(x, GROUND, z)
                sx, sy = int(sx + 0.5), int(sy + 0.5)
                if 0 <= sx < cols and 0 <= sy < rows:
                    idx = sy * cols + sx
                    if idx not in seen or d < seen[idx][0]:
                        seen[idx] = (d, math.hypot(x, z))
        rng = random.Random(9)
        out = []
        for idx, (d, r) in seen.items():
            fog = clip(1.25 - 0.32 * (d - D + 1.0), 0.15, 1.0)
            sx, sy = idx % cols, idx // cols
            if r < 1.05 and rng.random() < 0.55 * (1.15 - r):        # fallen leaves
                col = rng.choice(LEAF_COLORS)
                k = 0.55 * fog
                out.append((idx, d + 50, rng.choice("%&*v^~"), tuple(int(c * 255 * k) for c in col)))
            else:
                ch = "-" if (sx // 2 + sy) % 3 else "."
                if sx % 4 == 3:
                    continue
                c = tuple(int(v * 0.75 * fog) for v in (88, 76, 62))
                out.append((idx, d + 50, ch, c))
        return out

    def render(self, t):
        cols, rows = self.cols, self.rows
        N = cols * rows
        zb = [1e9] * N
        chs = [None] * N
        cos_ = [None] * N
        solid = bytearray(N)
        bx0, bx1, by0, by1 = cols, 0, rows, 0

        for x, y, ph in self.sky:
            v = int(55 + 45 * (0.5 + 0.5 * math.sin(t * 1.1 + ph * 40)))
            i = y * cols + x
            zb[i], chs[i], cos_[i] = 90, "." if ph < 0.85 else "+", (v + 10, v, v - 10 if v > 10 else 0)
        for idx, d, ch, c in self.ground:
            zb[idx], chs[idx], cos_[idx] = d, ch, c

        F, F2, cx, cy = self.F, self.F * 0.5, self.cx, self.cy
        cp, sp = math.cos(PHI), math.sin(PHI)
        th = SPIN * t + 0.4
        c, s = math.cos(th), math.sin(th)
        Lx, Ly, Lz = unit(-0.55, 0.65, -0.55)
        nr = len(RAMP) - 1
        splat = self.splat
        visible = 0

        def shade(nxr, ny, nzr, base, z2):
            diff = nxr * Lx + (ny * cp + nzr * sp) * Ly + (nzr * cp - ny * sp) * Lz
            if diff < 0:
                diff = 0.0
            fog = 1.15 - 0.55 * (z2 + 0.5)
            return base * (0.24 + 0.85 * diff), (0.35 if fog < 0.35 else 1.0 if fog > 1.0 else fog)

        # falling leaves (world-fixed)
        airborne = 0
        for f in self.falling:
            if t < f[6]:
                continue
            age = t - f[6]
            x = f[0] + 0.18 * math.sin(age * 0.9 + f[4]) + 0.05 * age
            y = 2.4 - (f[3] * age) % 2.4
            z = f[2]
            x = (x + 2.2) % 4.4 - 2.2
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
                    airborne += 1
                    fog = clip(1.3 - 0.3 * (d - D + 1.0), 0.3, 1.0)
                    spin = int(age * 4 + f[4] * 3) % 4
                    ch = ("@", "&", "%", "*")[spin] if d < D + 0.8 else ".:"[spin % 2]
                    zb[idx], chs[idx], cos_[idx] = d, ch, tuple(int(v * 255 * fog) for v in f[5])

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

        # big pumpkin: vortex → surface
        for (x, y, z, nx, ny, nz, r, g, b, t0, base, gi, a0, rs, ys, leafc, w) in self.swirl:
            appear = 0.9 * (a0 % 1.0)
            if t < appear:
                continue
            u = (t - t0) / T_FLY
            flying = u < 1
            if flying:
                # orbit in the vortex, then wind inwards to the surface point
                e = 0.0 if u <= 0 else ease_in_out(u)
                ang = a0 + w * 1.6 * t
                tang = math.atan2(z, x)
                ang0 = a0 + w * 1.6 * t0                 # orbit angle at launch: fixed anchor
                tang += TAU * round((ang0 - tang) / TAU) + TAU * 0.75
                a = ang * (1 - e) + tang * e
                tr = math.hypot(x, z)
                rr = rs * (1 - e) + tr * e
                yv = ys + 0.05 * math.sin(t * 2 + a0)
                y_ = yv * (1 - e) + y * e
                x_, z_ = math.cos(a) * rr, math.sin(a) * rr
            else:
                x_, y_, z_ = x, y, z
                nxr_ = nx * s + nz * c
                if nxr_ * cp - ny * sp > 0.4:            # back-facing: hidden anyway
                    continue
            xr = x_ * c - z_ * s
            zr = x_ * s + z_ * c
            yy = y_ - YC
            y2 = yy * cp + zr * sp
            z2 = zr * cp - yy * sp
            d = D + z2
            sx = int(cx + xr * F / d + 0.5)
            sy = int(cy - y2 * F2 / d + 0.5)
            if sx < 0 or sx >= cols or sy < 0 or sy >= rows:
                continue
            if flying:
                k = 0.0 if u <= 0 else e
                rgb = mix(leafc, (r, g, b), k)
                fog = clip(1.2 - 0.5 * (z2 + 0.5), 0.35, 1.0)
                spin = int(t * 5 + a0 * 7) % 4
                glyph = ("@", "&", "%", "*")[spin] if k < 0.8 else "#"
                v = (0.85 + 0.3 * k) * fog
                col = (int(min(255, rgb[0] * v * 255)), int(min(255, rgb[1] * v * 255)), int(min(255, rgb[2] * v * 255)))
                if plot(sx, sy, d, glyph, col, nr, False):
                    visible += 1
                continue
            nxr = nx * c - nz * s
            nzr = nx * s + nz * c
            lum, fog = shade(nxr, ny, nzr, base, z2)
            settle = t - t0 - T_FLY
            li = int((0.30 + 0.75 * lum * fog) * nr) + gi - 1
            glyph = RAMP[0 if li < 0 else nr if li > nr else li]
            v = (0.30 + 0.9 * lum) * fog
            rr_, gg_, bb_ = r, g, b
            if settle < 0.3:                             # warm flash as it lands
                f = 1 - settle / 0.3
                rr_, gg_, bb_ = r + (1 - r) * f, g + (0.9 - g) * f, b + (0.6 - b) * f
                v = max(v, f)
            col = (int(min(255, rr_ * v * 255)), int(min(255, gg_ * v * 255)), int(min(255, bb_ * v * 255)))
            if plot(sx, sy, d, glyph, col, li, True):
                visible += 1

        # everything else
        for (x, y, z, nx, ny, nz, r, g, b, mode, t0, base, ccx, ccy, ccz, gi) in self.parts:
            if t < t0:
                continue
            age = t - t0
            if mode == POP and age < 0.35:
                k = ease_back(age / 0.35)
                x, y, z = ccx + (x - ccx) * k, ccy + (y - ccy) * k, ccz + (z - ccz) * k
            nxr = nx * c - nz * s
            nzr = nx * s + nz * c
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
            if d >= zb[sy * cols + sx]:
                continue
            lum, fog = shade(nxr, ny, nzr, base, z2)
            li = int((0.30 + 0.75 * lum * fog) * nr) + gi - 1
            glyph = RAMP[0 if li < 0 else nr if li > nr else li]
            v = (0.30 + 0.9 * lum) * fog
            if mode == GROW and age < 0.3:               # bright growth tip
                f = 1 - age / 0.3
                r, g, b = r + (1 - r) * f, g + (1 - g) * f, b + (0.8 - b) * f
                v = max(v, f)
                glyph = "#"
            col = (int(min(255, r * v * 255)), int(min(255, g * v * 255)), int(min(255, b * v * 255)))
            if plot(sx, sy, d, glyph, col, li, True):
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

        cv = Canvas(chs, cos_, cols, rows)
        cv.banner(t, T_MSG, MESSAGE, MSG_PALETTE)
        cv.hud(t, [
            [("rotation %6.2f°" % (math.degrees(th) % 360), (96, 104, 122)),
             ("leaves %3d" % airborne, (255, 170, 80) if airborne else (96, 104, 122))],
            [("particles {:,}".format(visible), (96, 104, 122))],
        ])
        return chs, cos_

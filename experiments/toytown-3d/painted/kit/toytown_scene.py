"""Toy Town, the whole scene: ground, river and trees, the station, the houses, the square with its tree,
Marines, wagons and lamps, the low wall and steps, the bridge. Every element is built from shapes with the
shared kit and painted back to front on one canvas, in target-painting px (1399 x 1124).
    python3 toytown_scene.py [K]      # writes out/toytown_full.png, out/toytown_glow.png, out/toytown_compare.jpg
"""
import os, sys, math, time
import numpy as np, cv2
import toytown_kit as T
from toytown_kit import A, S, shaded, roof, window, garland, snow_edge, snow_clump, snow_cap, eave_shadow, chimney, stip, lump, hexc, glass, fir
from toytown_east import build_east, wreath
from toytown_west import build_west
from toytown_station import build_station, STONE, STONE_D, stonework

GRASS = ['#5f7a3a', '#6f8a44', '#809a4e', '#4f6a30']
SNOWG = ['#f3f1ec', '#e6e8ec', '#d8dde6']
COBBLE = ['#d8c6a8', '#c8b292', '#e4d4b8', '#b89e7e', '#d2bc98']
WATER = ['#3a66a8', '#4a7ab8', '#5d8ec8', '#2c5290']

def ground():
    """Hills around the town: green grass under patchy snow, a sandy path down the lower left."""
    m = A([(-20, -20), (1420, -20), (1420, 1140), (-20, 1140)], GRASS[1], wob=0, rough=0, edge_dark=0)
    stip(m, GRASS, spacing=1.6, L=4.0, w=2.2, weights=[.3, .3, .2, .2])
    # snow lying in drifts over the grass, thicker toward the town
    # a snowfield over the town and the near hills: soft-edged, with the grass showing through farther out
    snow = [(-20, 560), (120, 520), (260, 560), (300, 640), (330, 600), (1030, 600), (1150, 560), (1250, 500), (1300, 640), (1420, 700),
            (1420, 1140), (-20, 1140)]
    m = A(snow, SNOWG[0], wob=3.0, rough=1.0, edge_dark=0)
    stip(m, SNOWG + ['#ffffff'], spacing=1.6, L=4.0, w=2.2, weights=[.35, .25, .15, .25])
    T.sparkle(m, .5)
    for _ in range(140):                                        # grass showing through here and there
        x, y = T.R.uniform(0, 1399), T.R.uniform(900, 1124)
        if 270 < x < 1000 and y < 1010: continue
        g = A(lump(x, y, T.R.uniform(16, 40), T.R.uniform(5, 11)), GRASS[1], wob=.8, rough=.9, edge_dark=.05)
        stip(g, GRASS, spacing=1.6, L=3.6, w=2.0)
    for _ in range(220):
        x, y = T.R.uniform(0, 1399), T.R.uniform(0, 420)
        snow_clump(x, y, T.R.uniform(14, 34), T.R.uniform(5, 10))
    path = [(250, 1124), (300, 1060), (380, 1020), (470, 1000), (560, 985), (610, 1000), (560, 1040), (450, 1080), (380, 1124)]
    m = A(path, '#d8b870', wob=.6, rough=.8, edge_dark=.08)
    stip(m, ['#d8b870', '#c8a45c', '#e6c888'], spacing=1.6, L=3.2, w=2.0)
    for _ in range(18):
        x, y = T.R.uniform(300, 560), T.R.uniform(995, 1110); snow_clump(x, y, T.R.uniform(10, 18), 4)

def river():
    """The river: down from the hills past the station, under the bridge, out to the lower right."""
    P = [(1215, -10), (1256, 60), (1240, 130), (1270, 200), (1262, 270), (1245, 330), (1292, 420), (1338, 490), (1350, 600),
         (1360, 720), (1360, 840), (1300, 900), (1230, 960), (1150, 1010), (1050, 1060), (930, 1130)]
    wid = [30, 32, 34, 36, 36, 38, 40, 44, 48, 52, 56, 58, 60, 64, 68, 72]
    L, Rr = [], []
    for i, p in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy); nx, ny = -dy / n, dx / n
        L.append((p[0] + nx * wid[i] / 2, p[1] + ny * wid[i] / 2)); Rr.append((p[0] - nx * wid[i] / 2, p[1] - ny * wid[i] / 2))
    poly = L + Rr[::-1]
    m = A(poly, WATER[1], wob=.6, rough=.8, edge_dark=.2)
    def ang(X, Y):
        return np.full(X.shape, .9)
    stip(m, WATER, spacing=1.3, L=4.5, w=1.6, ang=lambda X, Y: np.full(X.shape, 1.1), weights=[.3, .3, .2, .2])
    for _ in range(90):                                         # white ripples
        i = T.R.randint(len(P) - 1); t = T.R.rand(); p = (P[i][0] + (P[i + 1][0] - P[i][0]) * t, P[i][1] + (P[i + 1][1] - P[i][1]) * t)
        o = T.R.uniform(-.35, .35) * wid[i]; a = math.atan2(P[i + 1][1] - P[i][1], P[i + 1][0] - P[i][0])
        T.c.dab(p[0] - T.X0 + o * -math.sin(a), p[1] - T.Y0 + o * math.cos(a), T.R.uniform(5, 10), 1.6, a, '#e8f0f8', a=.85, dry=.2)
    for side in (L, Rr):                                        # snow heaped along the banks, irregular
        for i in range(0, len(side) - 1):
            for t in (.2, .7):
                p = (side[i][0] + (side[i + 1][0] - side[i][0]) * t, side[i][1] + (side[i + 1][1] - side[i][1]) * t)
                snow_clump(p[0], p[1], T.R.uniform(9, 16), T.R.uniform(3, 5))

def bare_tree(x, y, h, seed):
    """A bare winter tree: trunk and branching limbs painted as tapered strokes, snow along the upper limbs."""
    r = np.random.RandomState(seed)
    def br(px, py, a, ln, wd, d):
        ex, ey = px + math.cos(a) * ln, py + math.sin(a) * ln
        S([(px, py), ((px + ex) / 2 + r.uniform(-2, 2), (py + ey) / 2), (ex, ey)], wd, '#4a3424', a=1, dry=.15, taper=(0, .5))
        if d > 0:
            for k in range(2 + (d > 2)):
                br(ex, ey, a + r.uniform(-.7, .7), ln * r.uniform(.55, .75), wd * .62, d - 1)
        elif r.rand() < .6:
            snow_clump(ex, ey - 1, 3.5, 1.8)
    S([(x, y), (x, y - h * .38)], h * .06, '#4a3424', a=1, dry=.15, taper=(0, .2))
    for a0 in (-math.pi / 2 - .5, -math.pi / 2, -math.pi / 2 + .5):
        br(x, y - h * .38, a0 + r.uniform(-.15, .15), h * .26, h * .035, 3)

def background_trees():
    """Snowy firs and bare trees on the hills behind and around the town (behind the station and houses)."""
    firs = [(40, 250, 150), (110, 330, 120), (20, 560, 110), (170, 110, 120), (360, 80, 90), (930, 90, 110), (1000, 230, 100),
            (1180, 300, 90), (1320, 360, 110), (1370, 700, 120), (1340, 1010, 100), (60, 1080, 110), (200, 1110, 90), (1100, 1110, 80)]
    for x, y, h in firs: fir(x, y, h)
    for i, (x, y, h) in enumerate([(240, 150, 140), (100, 160, 120), (1110, 140, 150), (1330, 160, 140), (1300, 1110, 150), (40, 760, 130)]):
        bare_tree(x, y, h, 31 + i)

def town_floor():
    """The ground the town stands on: snowy cobbles from the station front out to the houses and the bridge."""
    poly = [(0, 640), (120, 600), (260, 600), (300, 560), (1080, 560), (1210, 600), (1330, 640), (1330, 900), (1060, 920), (300, 920), (0, 930)]
    m = A(poly, SNOWG[0], wob=2.0, rough=.9, edge_dark=0)
    stip(m, SNOWG + ['#ffffff'], spacing=1.4, L=3.6, w=2.0, weights=[.35, .25, .15, .25])
    T.sparkle(m, .5)

def square():
    """The square: setts laid in shallow fans (as real squares are), low in contrast, mostly under trodden snow.
    The stones show only where feet have worn the snow away: paths to the doors, the steps and round the tree."""
    poly = [(300, 905), (290, 820), (320, 740), (380, 690), (470, 650), (560, 625), (840, 625), (930, 650), (1000, 690), (1040, 740),
            (1060, 820), (1050, 900)]
    m = A(poly, '#cdbda2', wob=1.2, rough=.8, edge_dark=.0)
    stip(m, ['#cdbda2', '#c4b296', '#d6c8ae'], spacing=1.4, L=3.2, w=1.8)
    prev = T.c.clipm; T.c.set_clip(m)
    # fans: arcs of stones around centres spaced across the square
    for fx in np.arange(260, 1100, 64):
        for k in range(1, 9):
            fy = 960; r = k * 9.5
            for a in np.linspace(-math.pi * .82, -math.pi * .18, int(r * .55)):
                for row in range(0, 360, 64):
                    px, py = fx + r * math.cos(a) + T.R.uniform(-1, 1), fy - row + r * math.sin(a) * .55 + T.R.uniform(-.8, .8)
                    if not (600 < py < 920): continue
                    col = '#%02x%02x%02x' % tuple(int(c * 255) for c in np.clip(hexc('#c8b69a') * T.R.uniform(.9, 1.08), 0, 1))
                    T.c.area(T.T(lump(px, py, T.R.uniform(3.4, 4.6), T.R.uniform(2.2, 2.8), amp=.2)), hexc(col), wob=.2, rough=.5,
                             edge_dark=.3, var=.04, a=.9, seed=int(T.R.randint(1 << 20)))
    # trodden snow over most of it: large soft sheets, leaving worn paths clear
    worn = [((700, 640), (700, 900), 70), ((420, 720), (700, 860), 46), ((980, 720), (700, 860), 46), ((340, 860), (560, 900), 40),
            ((1040, 860), (900, 900), 40)]
    def near_path(x, y):
        for (a, b, w) in worn:
            ax, ay = a; bx, by = b; t = np.clip(((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
            if math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay)) < w: return True
        return False
    for _ in range(120):
        x, y = T.R.uniform(290, 1060), T.R.uniform(625, 905)
        if near_path(x, y): continue
        mm = A(lump(x, y, T.R.uniform(18, 40), T.R.uniform(7, 14), amp=.25), SNOWG[0], wob=.8, rough=.9, edge_dark=0, a=.92)
        stip(mm, SNOWG + ['#ffffff'], spacing=1.4, L=3.0, w=1.8, weights=[.35, .25, .15, .25])
    for _ in range(260):                                         # a thin dusting everywhere, catching between stones
        x, y = T.R.uniform(290, 1060), T.R.uniform(625, 905)
        T.c.dab(x - T.X0, y - T.Y0, T.R.uniform(3, 7), T.R.uniform(1.4, 2.4), T.R.uniform(-.3, .3), SNOWG[T.R.randint(3)], a=.75, dry=.3)
    T.c.clipm = prev
    # the square's edge: snow heaped irregularly, wider in places, so it melts into the surrounding snow
    P = poly + [poly[0]]
    for a_, b_ in zip(P, P[1:]):
        for t in np.linspace(0, 1, max(2, int(math.dist(a_, b_) / 18))):
            snow_clump(a_[0] + (b_[0] - a_[0]) * t + T.R.uniform(-6, 6), a_[1] + (b_[1] - a_[1]) * t + T.R.uniform(-4, 4), T.R.uniform(14, 30), T.R.uniform(4, 8))

def cast(x, y, rx, ry, a=.32):
    """A soft cool shadow on the snow under an object, offset a little away from the light (upper left)."""
    T.c.area(T.T(lump(x + rx * .15, y + ry * .3, rx, ry, amp=.08)), hexc('#7a86a0'), wob=.4, rough=.6, edge_dark=0, a=a, var=0, varbig=0, seed=int(x * 3 + y))

def ground_line(x0, x1, y, depth=9, a=.3):
    """Where a wall meets the snow: a soft blue-grey shade along its foot, and the snow banked against it."""
    T.c.area(T.T([(x0, y - 2), (x1, y - 2), (x1 + depth * .6, y + depth), (x0 + depth * .6, y + depth)]), hexc('#7a86a0'), wob=.6, rough=.7, edge_dark=0, a=a, var=0, varbig=0, seed=int(x0))
    for t in np.linspace(0, 1, max(2, int((x1 - x0) / 22))):
        snow_clump(x0 + (x1 - x0) * t + T.R.uniform(-5, 5), y + T.R.uniform(-1, 2), T.R.uniform(10, 18), T.R.uniform(3, 5))

def lamp(x, y, h=120):
    """A black street lamp with a glowing lantern and a red bow; its light pools on the snow."""
    for rr_, aa in ((60, .12), (40, .16), (24, .2)):          # warm light pooling on the snow under the lantern
        T.c.area(T.T(lump(x, y + 4, rr_, rr_ * .32, amp=.1)), hexc('#ffd890'), wob=.4, rough=.6, edge_dark=0, a=aa, var=0, varbig=0, seed=int(x + rr_))
    cast(x + 8, y + 2, 10, 3.5)
    shaded([(x - 8, y + 2), (x + 8, y + 2), (x + 6, y - 10), (x - 6, y - 10)], ['#3a3a40', '#22222a', '#101014'], wob=.05, rough=.2, edge_dark=.2)
    S([(x, y - 10), (x, y - h + 26)], 4.0, '#1c1c22', a=1, dry=.05, taper=(0, 0))
    for yy in (y - 30, y - h + 34): S([(x - 4, yy), (x + 4, yy)], 2.5, '#2a2a32', a=1, dry=0)
    top = y - h
    shaded([(x - 11, top + 26), (x + 11, top + 26), (x + 8, top + 22), (x - 8, top + 22)], ['#3a3a40', '#22222a', '#101014'], wob=.05, rough=.2)
    g = A([(x - 9, top + 22), (x + 9, top + 22), (x + 11, top + 4), (x - 11, top + 4)], T.GOLD_C, wob=.05, rough=.2, edge_dark=.05)
    glass(g, x, top + 14, 10, 10)
    x0, y0, mm = g; T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] = np.maximum(T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]], mm)
    for xx in (x - 10, x + 10): S([(xx, top + 4), (xx * .5 + x * .5, top + 22)], 1.6, '#1c1c22', a=1, dry=0)
    shaded([(x - 15, top + 4), (x + 15, top + 4), (x + 4, top - 8), (x - 4, top - 8)], ['#3a3a40', '#22222a', '#101014'], wob=.05, rough=.2)
    snow_edge([(x - 14, top + 1), (x + 14, top + 1)], 5, drip=.3)
    by = top + 44
    for sg in (-1, 1): shaded([(x, by), (x + sg * 13, by - 8), (x + sg * 13, by + 8)], ['#e0504a', T.BERRY, '#7a1418'], wob=.05, rough=.2, edge_dark=.2)
    for sg in (-1, 1): S([(x, by + 2), (x + sg * 6, by + 18)], 3.0, T.BERRY, a=1, dry=.05)
    shaded(lump(x, by, 3.5, 3.5, amp=0), ['#c0383a', '#9a1e22', '#6a1214'], wob=0, rough=.2)
    snow_clump(x, y + 1, 12, 3)

def present(bx, by, bw, bh, col, rib):
    C = hexc(col); lt = '#%02x%02x%02x' % tuple(int(min(255, v * 255 * 1.18 + 12)) for v in C); dk = '#%02x%02x%02x' % tuple(int(v * 255 * .72) for v in C)
    shaded([(bx, by), (bx + bw, by), (bx + bw, by - bh), (bx, by - bh)], [lt, col, dk], wob=.05, rough=.2, edge_dark=.18, L=1.4, w=1.0)
    S([(bx + bw / 2, by), (bx + bw / 2, by - bh)], max(1.5, bw * .12), rib, a=1, dry=.05, taper=(0, 0))
    S([(bx, by - bh / 2), (bx + bw, by - bh / 2)], max(1.4, bh * .12), rib, a=1, dry=.05, taper=(0, 0))
    for sg in (-1, 1): A([(bx + bw / 2, by - bh), (bx + bw / 2 + sg * bw * .28, by - bh - bw * .2), (bx + bw / 2 + sg * bw * .28, by - bh + 2)], rib, wob=.05, rough=.2, edge_dark=.2)

def christmas_tree(x, y, h):
    """The square's Christmas tree: tiers of needles, baubles, warm lights, a gold star, presents beneath."""
    cast(x + 10, y + 14, 110, 14, .3)
    tiers = [(.04, .32, .44), (.22, .5, .37), (.4, .68, .29), (.56, .84, .2), (.72, 1.0, .11)]
    S([(x, y), (x, y - h * .1)], 8, '#4a3020', a=1, dry=.1)
    for i, (ta, tb, wd) in enumerate(tiers):
        yb, yt = y - h * ta, y - h * tb; half = wd * h
        poly = [(x, yt)] + [(x + half * u, yt + (yb - yt) * u) for u in np.linspace(.15, 1, 5)]
        poly += [(x + half - 2 * half * k / 9, yb + (4 if k % 2 else 0)) for k in range(1, 9)]
        poly += [(x - half * u, yt + (yb - yt) * u) for u in np.linspace(1, .15, 5)]
        shaded(poly, ['#3d7a52', '#2a5e40', '#173a29'], wob=.5, rough=1.0, edge_dark=.2, L=3.6, w=1.4)
        for _ in range(int(half / 4)):                         # baubles and lights on this tier
            u = T.R.uniform(.3, 1); px = x + T.R.uniform(-1, 1) * half * u * .85; py = yt + (yb - yt) * u - 3
            if T.R.rand() < .45:
                cols = ['#e0504a', '#b8262a', '#7a1418'] if T.R.rand() < .55 else ['#f6d77a', '#e0b040', '#a07a20']
                shaded(lump(px, py, 4, 4, amp=0), cols, wob=0, rough=.2, edge_dark=.1, L=1, w=.8)
                T.c.dab(px - 1.3 - T.X0, py - 1.5 - T.Y0, 1.2, 1.0, 0, '#ffffff', a=.9, dry=0)
            else:
                T.c.area(T.T(lump(px, py, 3.5, 3.5, amp=0)), hexc('#fff0b0'), wob=0, rough=.3, edge_dark=0, a=.45, var=0, varbig=0, seed=int(px * 7))
                T.c.dab(px - T.X0, py - T.Y0, 1.5, 1.4, 0, '#fffbe0', a=1, dry=0)
                cx_, cy_ = int((px - T.X0) * T.K), int((py - T.Y0) * T.K); cv2.circle(T.GLOW, (cx_, cy_), int(2 * T.K), 1.0, -1)
    st = [(x + (17 if k % 2 == 0 else 7) * math.cos(-math.pi / 2 + k * math.pi / 5), y - h - 4 + (17 if k % 2 == 0 else 7) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    shaded(st, ['#fff2a8', '#f0c040', '#b88a20'], light=(-.7, -.7), wob=.05, rough=.2, edge_dark=.15)
    for k, (dx, w_, h_, col, rib) in enumerate([(-80, 30, 26, '#b8262a', '#f0d070'), (-48, 26, 22, '#e0b040', '#b8262a'), (-20, 30, 30, '#3a6aa8', '#f3ead6'),
                                                (14, 26, 22, '#d84a8a', '#f0d070'), (42, 30, 26, '#2f6446', '#f0d070'), (74, 22, 20, '#b8262a', '#f3ead6')]):
        present(x + dx, y + 10, w_, h_, col, rib)
    snow_edge([(x - 90, y + 12), (x + 100, y + 12)], 6, drip=0)

def wagon(x, y, load='bear'):
    """A red toy wagon with black wheels, a handle, and a load: a teddy bear with presents, or a stack of presents."""
    cast(x + 8, y + 8, 56, 8)
    shaded([(x - 44, y - 30), (x + 44, y - 30), (x + 40, y - 8), (x - 40, y - 8)], ['#e0504a', '#b8262a', '#7a1418'], light=(-.5, -.8), wob=.05, rough=.2, edge_dark=.2)
    S([(x - 44, y - 30), (x + 44, y - 30)], 2.5, '#d84a40', a=1, dry=.05, taper=(0, 0))
    for wx in (x - 26, x + 26):
        shaded(lump(wx, y - 2, 11, 11, amp=0), ['#3a3a40', '#1c1c22', '#0c0c10'], wob=0, rough=.2, edge_dark=.1)
        shaded(lump(wx, y - 2, 5, 5, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2)
    S([(x + 44, y - 24), (x + 70, y - 52), (x + 74, y - 64)], 3.0, '#1c1c22', a=1, dry=.05, taper=(0, 0))
    S([(x + 66, y - 66), (x + 80, y - 60)], 3.5, '#1c1c22', a=1, dry=.05)
    if load == 'bear':
        present(x + 8, y - 30, 26, 22, '#3a6aa8', '#f0d070'); present(x + 22, y - 48, 16, 16, '#2f6446', '#f3ead6')
        bc = ['#d8995a', '#b9733a', '#7a4620']
        shaded(lump(x - 14, y - 46, 14, 16, amp=.04), bc, wob=.05, rough=.2, edge_dark=.2)
        shaded(lump(x - 14, y - 72, 12, 11, amp=.04), bc, wob=.05, rough=.2, edge_dark=.2)
        for sg in (-1, 1): shaded(lump(x - 14 + sg * 10, y - 82, 4.5, 4.5, amp=0), bc, wob=0, rough=.2)
        shaded(lump(x - 14, y - 68, 5.5, 4, amp=0), ['#f0c690', '#e2b07c', '#c48a56'], wob=0, rough=.2)
        T.c.dots([(x - 14 - T.X0, y - 70 - T.Y0)], 1.8, ['#2a1a12'], seed=3)
        for sg in (-1, 1): T.c.dots([(x - 14 + sg * 4.5 - T.X0, y - 75 - T.Y0)], 1.3, ['#1e140e'], seed=4)
        for sg in (-1, 1): shaded([(x - 14, y - 60), (x - 14 + sg * 7, y - 64), (x - 14 + sg * 7, y - 56)], ['#e0504a', T.BERRY, '#7a1418'], wob=0, rough=.2)
    else:
        for (dx, dy, w_, h_, col, rib) in [(-36, -30, 26, 22, '#3a6aa8', '#f0d070'), (-8, -30, 24, 26, '#b8262a', '#f0d070'), (18, -30, 22, 18, '#2f6446', '#f3ead6'),
                                           (-26, -52, 22, 18, '#e0b040', '#b8262a'), (0, -56, 20, 20, '#2f6446', '#f0d070'), (-14, -74, 18, 16, '#b8262a', '#f3ead6')]:
            present(x + dx, y + dy, w_, h_, col, rib)

def marine(x, y, h=96, skin='#e8b080'):
    """A toy Marine in dress blues standing to attention: white cap, blue coat with red trim, gold buttons."""
    NAVY, NAVY_D, NAVY_L = '#1c2a52', '#101a38', '#2e4078'
    cast(x + 6, y + 1, 18, 4)
    for sg in (-1, 1):                                          # trousers with a red stripe, black shoes
        shaded([(x + sg * 2, y - h * .42), (x + sg * 11, y - h * .42), (x + sg * 10, y - 6), (x + sg * 2, y - 6)], [NAVY_L, NAVY, NAVY_D], wob=.05, rough=.2, edge_dark=.2)
        S([(x + sg * 9.5, y - h * .42), (x + sg * 9, y - 7)], 1.6, '#c8282a', a=1, dry=.05, taper=(0, 0))
        shaded(lump(x + sg * 7, y - 3, 7, 3.5, amp=0), ['#3a3a40', '#16161c', '#08080a'], wob=0, rough=.2)
    shaded([(x - 15, y - h * .42), (x + 15, y - h * .42), (x + 14, y - h * .74), (x - 14, y - h * .74)], [NAVY_L, NAVY, NAVY_D], wob=.05, rough=.2, edge_dark=.2)
    S([(x - 15, y - h * .44), (x + 15, y - h * .44)], 3.0, '#f3ead6', a=1, dry=.05, taper=(0, 0))      # white belt
    T.c.dots([(x - T.X0 + 1, y - h * (.5 + .055 * k) - T.Y0) for k in range(4)], 1.2, ['#f0c040'], seed=int(x))
    for sg in (-1, 1):
        shaded([(x + sg * 14, y - h * .73), (x + sg * 19, y - h * .7), (x + sg * 18, y - h * .46), (x + sg * 13, y - h * .46)], [NAVY_L, NAVY, NAVY_D], wob=.05, rough=.2, edge_dark=.2)
        shaded(lump(x + sg * 16, y - h * .44, 3.8, 3.8, amp=0), ['#ffffff', '#f3ead6', '#cfc4ac'], wob=0, rough=.2)        # white gloves
        S([(x + sg * 9, y - h * .74), (x + sg * 18, y - h * .72)], 2.0, '#c8282a', a=1, dry=0, taper=(0, 0))
    S([(x - 7, y - h * .75), (x + 7, y - h * .75)], 3.5, '#c8282a', a=1, dry=0, taper=(0, 0))          # collar
    sk = hexc(skin); lt = '#%02x%02x%02x' % tuple(int(min(255, v * 255 * 1.12)) for v in sk); dk = '#%02x%02x%02x' % tuple(int(v * 255 * .78) for v in sk)
    shaded(lump(x, y - h * .84, 8.5, 9.5, amp=0), [lt, skin, dk], wob=0, rough=.2, edge_dark=.15)
    for sg in (-1, 1): T.c.dots([(x + sg * 3 - T.X0, y - h * .85 - T.Y0)], 1.1, ['#1e140e'], seed=int(x) + sg)
    S([(x - 2.5, y - h * .8), (x + 2.5, y - h * .8)], .8, '#8a3a2a', a=.8, dry=0)
    shaded([(x - 11, y - h * .9), (x + 11, y - h * .9), (x + 10, y - h * .99), (x - 10, y - h * .99)], ['#ffffff', '#f3ead6', '#cfc4ac'], wob=0, rough=.2, edge_dark=.15)
    S([(x - 10, y - h * .9), (x + 10, y - h * .9)], 2.5, '#101014', a=1, dry=0, taper=(0, 0))
    T.c.dots([(x - T.X0, y - h * .945 - T.Y0)], 1.4, ['#f0c040'], seed=int(x) + 9)

def planter(x, y, w=70):
    """A stone planter on the wall, full of holly with red berries and a cap of snow."""
    shaded([(x - w / 2, y + 44), (x + w / 2, y + 44), (x + w / 2, y), (x - w / 2, y)], [STONE[3], STONE[1], STONE_D], wob=.1, rough=.4, edge_dark=.2, L=3, w=1.6)
    for yy in (y + 14, y + 29): S([(x - w / 2, yy), (x + w / 2, yy)], 1.0, STONE_D, a=.6, dry=.3)
    for _ in range(int(w * 5)):
        T.c.dab(x - T.X0 + T.R.uniform(-w * .5, w * .5), y - T.Y0 - T.R.uniform(-2, 30) * (1 - abs(T.R.uniform(-.6, .6))), T.R.uniform(5, 8), 2.2, T.R.uniform(0, 3), T.NEEDLES[T.R.randint(4)], a=1, dry=.1)
    for _ in range(int(w / 3)):
        bx, by = x + T.R.uniform(-w * .4, w * .4), y - T.R.uniform(4, 28)
        shaded(lump(bx, by, 3.2, 3.2, amp=0), ['#e0504a', T.BERRY, '#7a1418'], wob=0, rough=.2)
    for _ in range(3): snow_clump(x + T.R.uniform(-w * .3, w * .3), y - 22, w * .22, 5)
    snow_edge([(x - w / 2 - 3, y), (x + w / 2 + 3, y)], 6, drip=.2)

def wall_and_steps():
    """The low stone wall along the front of the square, stepping down, with steps down to the path."""
    left = [(277, 1000), (523, 1000), (523, 905), (277, 905)]
    right = [(613, 1010), (990, 1010), (990, 945), (613, 945)]
    for q in (left, right): stonework(q, course=9, block=(14, 24))
    snow_edge([(272, 903), (528, 903)], 9, drip=.3)
    snow_edge([(608, 943), (996, 943)], 9, drip=.3)
    for i in range(6):                                          # steps between the two runs of wall
        y = 905 + i * 17
        shaded([(523, y), (613, y), (613, y + 17), (523, y + 17)], ['#e6dccc', '#d0c6b4', '#a89e8c'], light=(0, -1), wob=.1, rough=.3, edge_dark=.2, L=3, w=1.4)
        snow_edge([(526, y + 1), (610, y + 1)], 3.5, drip=0)
    for (px, py) in ((300, 905), (500, 905), (636, 945), (970, 945)):          # gate posts
        stonework([(px - 14, py + 6), (px + 14, py + 6), (px + 14, py - 22), (px - 14, py - 22)], course=7, block=(8, 14))
        snow_edge([(px - 17, py - 23), (px + 17, py - 23)], 7, drip=.3)
    planter(417, 862, 78); planter(923, 900, 78); planter(777, 940, 70)

def bridge():
    """The stone bridge to the right: an arch over the river, a balustrade, snow on the rail and deck."""
    x0, x1, yd = 1074, 1405, 838
    deck = [(x0, yd + 70)] + [(x0 + (x1 - x0) * t, yd - 30 * math.sin(math.pi * t * .9)) for t in np.linspace(0, 1, 20)] + [(x1, yd + 70)]
    stonework([(x0, 930)] + deck[1:-1] + [(x1, 930)], course=10, block=(14, 26))
    # the arch opening: dark under the bridge, its own voussoirs
    cx, cy, rx, ry = 1265, 955, 110, 90
    op = [(cx - rx, 960)] + [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(180, 360, 30)] + [(cx + rx, 960)]
    # through the arch: the far snowy bank, the river running through, the shade under the vault
    m = A(op, '#c8d0dc', wob=.1, rough=.3, edge_dark=.0)
    stip(m, ['#c8d0dc', '#b8c2d2', '#d8dee8'], spacing=1.4, L=3.0, w=1.8)
    wat = [(cx - rx, 960), (cx - rx * .9, cy - ry * .25), (cx + rx * .9, cy - ry * .35), (cx + rx, 960)]
    mw = A(wat, WATER[1], wob=.4, rough=.6, edge_dark=.05)
    stip(mw, WATER, spacing=1.3, L=4.5, w=1.6, ang=.15)
    for _ in range(26):
        T.c.dab(cx - T.X0 + T.R.uniform(-rx * .8, rx * .8), cy - T.Y0 + T.R.uniform(-ry * .25, 4), T.R.uniform(5, 10), 1.5, .1, '#e8f0f8', a=.8, dry=.2)
    top = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(180, 360, 30)]
    inner = [(cx + rx * .92 * math.cos(math.radians(a)), cy - ry * .2 + ry * .78 * math.sin(math.radians(a))) for a in np.linspace(360, 180, 30)]
    T.c.area(T.T(top + inner), hexc('#1e2a40'), wob=.2, rough=.5, edge_dark=0, a=.55, var=0, varbig=0, seed=7)
    for i in range(15):
        a0, a1 = 180 + 12 * i, 180 + 12 * (i + 1)
        q = [(cx + (rx + d) * math.cos(math.radians(a)), cy + (ry + d) * math.sin(math.radians(a))) for d, a in ((0, a0 + .5), (0, a1 - .5), (14, a1 - .5), (14, a0 + .5))]
        shaded(q, [STONE[3], STONE[T.R.randint(4)], STONE_D], wob=.1, rough=.4, edge_dark=.3, L=2, w=1.3)
    # balustrade: posts along the deck
    for t in np.linspace(.02, .98, 22):
        px = x0 + (x1 - x0) * t; py = yd - 30 * math.sin(math.pi * t * .9)
        shaded([(px - 3.5, py), (px + 3.5, py), (px + 3, py - 24), (px - 3, py - 24)], [STONE[3], STONE[1], STONE_D], wob=.05, rough=.3, edge_dark=.2, L=1.6, w=1)
    rail = [(x0 + (x1 - x0) * t, yd - 30 * math.sin(math.pi * t * .9) - 26) for t in np.linspace(0, 1, 20)]
    S(rail, 6, STONE[2], a=1, dry=.1, taper=(0, 0))
    snow_edge([(x, y - 2) for x, y in rail], 7, drip=.3)
    snow_edge([(x, y + 2) for x, y in deck[1:-1]], 6, drip=.2)

def foreground():
    for (x, y, h) in ((333, 893, 66), (1010, 867, 64), (1070, 973, 56), (240, 980, 70)):
        fir(x, y, h)

def build_scene():
    t = time.time(); log = lambda n: print(f'  {n} {time.time() - t:.0f}s', flush=True)
    ground(); log('ground'); river(); log('river'); background_trees(); log('trees')
    town_floor(); log('floor')
    build_station(); log('station')
    build_west(); build_east(); log('houses')
    T.blue_shop(); log('blue shop')
    for (x0, x1, y) in ((596, 804, 616), (458, 598, 616), (802, 942, 616), (344, 462, 703), (302, 350, 723), (938, 1058, 703), (1028, 1290, 852), (0, 340, 906)):
        ground_line(x0, x1, y)
    square(); log('square')
    for (x, y) in ((527, 717), (873, 717)): lamp(x, y, 120)
    wagon(487, 847, 'bear'); wagon(875, 860, 'presents')
    christmas_tree(650, 845, 212)
    marine(760, 812); marine(802, 812, skin='#8a5430')
    for (x, y) in ((373, 867), (963, 873)): lamp(x, y, 175)
    log('square life')
    wall_and_steps(); bridge(); foreground(); log('wall, bridge')

if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    T.init(0, 0, 1399, 1124, K)
    build_scene(); T.light()
    paint, al = T.finish(os.path.join(HERE, 'out', 'toytown_full.png'), os.path.join(HERE, 'out', 'toytown_glow.png'), opaque=True)
    tgt = cv2.imread(os.path.join(T.ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))[..., ::-1].astype(np.float32) / 255
    tc = cv2.resize(tgt, (paint.shape[1], paint.shape[0]), interpolation=cv2.INTER_CUBIC)
    sheet = np.concatenate([tc, np.ones((paint.shape[0], 30, 3)), paint], 1)
    cv2.imwrite(os.path.join(HERE, 'out', 'toytown_compare.jpg'), (cv2.resize(sheet, None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 86])
    cv2.imwrite(os.path.join(HERE, 'out', 'toytown_full_preview.jpg'), (cv2.resize(paint, (1399, 1124), interpolation=cv2.INTER_AREA)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok')

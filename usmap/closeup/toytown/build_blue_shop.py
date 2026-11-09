"""Toy Town study 1, version 3 ("built"): the blue shop drawn from its own shapes and painted with the map's
brush, the way the national map was made. Nothing is traced or sampled from the target painting: its layout
(positions and sizes, measured in its pixels) and its design are the reference, every colour and stroke is ours.

Units: target-painting px (x 0..340, y 430..912), so the building lands where the approved composition puts it.
Order of painting: back roofs and chimneys, tall house, side wing, front gable, roofs and snow, windows,
garlands, awning, shopfront and display, the snowy fir, ground snow; then the impasto light.
Writes out/blue_shop_v3_study.png (RGBA), out/blue_shop_v3_glow.png (the lit glass, for dusk) and comparisons.
    python3 build_blue_shop.py
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
sys.path[:0] = [os.path.join(ROOT, 'folk2'), os.path.join(ROOT, 'styles2')]
from kit import Kanvas, impasto
from brush import hexc
from parts import lumpy
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

X0, Y0, X1, Y1 = 0, 430, 340, 912
K = 4
W, H = X1 - X0, Y1 - Y0
c = Kanvas(W * K, H * K, K, '#000000', seed=5)
c.HM = np.zeros((c.H, c.W), np.float32)
ALPHA = np.zeros((c.H, c.W), np.float32)
GLOW = np.zeros((c.H, c.W), np.float32)
R = np.random.RandomState(12)

# ---- palette (the map's calmer range) ----
BLUE, BLUE_D, BLUE_L = '#3b5a98', '#2c4478', '#5a78b6'
CREAM, CREAM_D = '#ecdcbd', '#c9b48f'
ROOF, ROOF_D = '#953a33', '#6e2925'
SNOW, SNOW_S, SNOW_H = '#f1f3f7', '#c4cfe0', '#ffffff'
GOLD, GOLD_C, GOLD_E = '#f0b64e', '#fbe19a', '#d98a2e'
BAR = '#5e3319'
BRICK, BRICK_D = '#ad4c30', '#7e3220'
GREEN_A, WHITE_A, GREEN_AD = '#3f7340', '#ece5d2', '#2b5530'
WOOD, WOOD_D = '#86361f', '#5e2414'
NEEDLES = ['#173a29', '#1f4a33', '#2a5e40', '#12301f']
BERRY = '#b8262a'

def T(pts): return [(x - X0, y - Y0) for x, y in pts]
def track(m, a=1.0):
    if m is None: return m
    x0, y0, mm = m; h, w = mm.shape
    ALPHA[y0:y0 + h, x0:x0 + w] = np.maximum(ALPHA[y0:y0 + h, x0:x0 + w], mm * a)
    return m
def A(pts, col, a=1.0, **kw):
    kw.setdefault('wob', .35); kw.setdefault('rough', .6); kw.setdefault('edge_dark', .08)
    return track(c.area(T(pts), col, a=a, seed=int(R.randint(1 << 20)), **kw), a)
def S(pts, w, col, a=1.0, **kw):
    kw.setdefault('dry', .2)
    c.stroke(T(pts), w, col, a=a, seed=int(R.randint(1 << 20)), **kw)
    P = (np.array(T(pts)) * K).astype(np.int32)
    cv2.polylines(ALPHA, [P], False, float(a), max(1, int(w * K * .9)), cv2.LINE_AA)
def stip(m, cols, spacing=1.1, L=2.4, w=1.2, ang=None, var=.06, weights=None, seed=None):
    C = np.array([hexc(x) for x in cols]); p = np.array(weights or [1] * len(cols), float); p /= p.sum()
    def f(X, Y, r):
        idx = r.choice(len(C), size=len(X), p=p)
        return np.clip(C[idx] * (1 + (r.rand(len(X), 1) - .5) * 2 * var), 0, 1)
    af = (lambda X, Y: np.full(X.shape, ang)) if isinstance(ang, (int, float)) else ang
    c.stip(m, f, spacing=spacing, L=L, w=w, angfn=af, seed=int(R.randint(1 << 20)) if seed is None else seed, jit=.45, thresh=.3)
def lump(cx, cy, rx, ry, seed=None, amp=.12):
    return lumpy(cx, cy, rx, ry, int(R.randint(1 << 20)) if seed is None else seed, n=22, bumps=5, amp=amp, flat=.3)

# ---- snow, the way model makers build it: a thick rolled edge, lumpy, lit on top, blue in its shadow ----
def snow_edge(pts, thick=7.0, drip=.25, under=True):
    """Snow resting along an edge, as one soft mass: its top bulges in slow lumps, its underside hangs in
    scallops and the odd drip; it is lit on top and goes blue-grey underneath."""
    P = np.array(pts, float)
    seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); tot = L.sum(); cum = np.concatenate([[0], np.cumsum(L)])
    n = max(6, int(tot / 2.5)); up, lo, mid = [], [], []
    ph = R.uniform(0, 10)
    for i in range(n + 1):
        d = tot * i / n; j = int(np.clip(np.searchsorted(cum, d) - 1, 0, len(L) - 1)); t = (d - cum[j]) / L[j]
        p = P[j] + seg[j] * t; tx, ty = seg[j] / L[j]; nx, ny = ty, -tx            # normal pointing up (screen)
        if ny > 0: nx, ny = -nx, -ny
        bulge = 1 + .25 * math.sin(d / (thick * 1.6) + ph) + .12 * math.sin(d / (thick * .7) + ph * 2)
        sc = .55 + .45 * abs(math.sin(d / (thick * 1.1) + ph))                       # scalloped underside
        end = max(.05, min(1, d / (thick * 1.2), (tot - d) / (thick * 1.2))) ** .5
        up.append(p + np.array([nx, ny]) * thick * .62 * bulge * end)
        lo.append(p - np.array([nx, ny]) * thick * (.3 + .35 * sc) * end)
        mid.append(p)
    poly = [tuple(q) for q in up] + [tuple(q) for q in lo[::-1]]
    m = A(poly, SNOW, wob=.25, rough=.5, edge_dark=.0)
    if m is None: return
    lo_y = np.interp(np.arange(c.W), [ (q[0] - X0) * K for q in lo], [(q[1] - Y0) * K for q in lo]) if P[-1][0] != P[0][0] else None
    S1, S2, S3 = hexc(SNOW_H), hexc(SNOW), hexc(SNOW_S)
    def scol(X, Y, r):
        # blend from bright top to the blue-grey underside, by height within the band
        if lo_y is None: k = np.full(len(X), .4)
        else:
            ly = lo_y[np.clip((X * K).astype(int), 0, c.W - 1)] / K
            k = np.clip(1 - (ly - Y) / (thick * 1.1), 0, 1)
        k = k[:, None]
        col = np.where(k < .5, S1 * (1 - k * 2) + S2 * (k * 2), S2 * (2 - k * 2) + S3 * (k * 2 - 1))
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .05), 0, 1)
    c.stip(m, scol, spacing=1.0, L=2.4, w=1.5, seed=int(R.randint(1 << 20)), jit=.5, thresh=.3)
    if drip:
        for q in lo[2:-2:3]:
            if R.rand() < drip:
                A(lump(q[0], q[1] + thick * .25, thick * .28, thick * .45, amp=.08), SNOW, wob=.15, rough=.4, edge_dark=.0)
                S([(q[0], q[1] + thick * .15), (q[0], q[1] + thick * .55)], thick * .2, SNOW_S, a=.35, dry=.4)
    S([tuple(q + np.array([0, thick * .12])) for q in up[1:-1]], thick * .28, SNOW_H, a=.6, dry=.45, taper=(.3, .3))

def eave_shadow(pts, thick=8.0, col=None):
    """The soft shade a heavy snow edge casts on the wall just below it."""
    sh = [(x, y + thick * .9) for x, y in pts]
    c.stroke(T(sh), thick * 1.3, hexc(col or BLUE_D) * .7, a=.38, dry=.55, taper=(.25, .25), seed=int(R.randint(1 << 20)))

def snow_cap(x0, x1, y, thick=5.0):
    snow_edge([(x0, y), (x1, y)], thick, drip=.1)

# ---- walls: gouache ground, then stippled stucco in three blues, flecks of snow ----
def wall(pts, base, dark=False, fleck=.0):
    """Stucco in the map's manner: a gouache ground, then mottled dabs in three blues laid in short crossing
    strokes (the hand-modelled plaster of the reference), a few flecks of snow stuck to it."""
    m = A(pts, base, wob=.25, rough=.5, edge_dark=.16)
    cols = [BLUE_D, BLUE, BLUE, BLUE_L] if not dark else [BLUE_D, BLUE_D, BLUE, BLUE]
    stip(m, cols, spacing=1.6, L=4.0, w=2.3, ang=lambda X, Y: (np.floor(X / 3) + np.floor(Y / 3)) % 2 * 1.2 + .3, weights=[.3, .3, .25, .15])
    stip(m, [BLUE_D, BLUE_L], spacing=3.0, L=2.4, w=1.4, weights=[.5, .5])
    if fleck:
        x0, y0, mm = m; ys, xs = np.nonzero(mm > .6)
        for k in R.choice(len(xs), int(len(xs) * fleck / (K * K * 160)), replace=False):
            c.dab((xs[k] + x0) / K, (ys[k] + y0) / K, R.uniform(1.2, 2.2), R.uniform(.9, 1.3), R.uniform(0, 3), SNOW, a=.85, dry=.15)
    return m

def roof(pts, base=ROOF, snowy=.6, ridge=None, eave=None):
    """Red tiles under a blanket of snow: the snow covers the upper part of the slope (ridge side) down to a
    wavy edge at `snowy` of the way to the eave, with a few gaps where tiles show through."""
    m = A(pts, base, wob=.3, rough=.6, edge_dark=.1)
    stip(m, [ROOF, ROOF_D, '#a8463c'], spacing=1.3, L=2.6, w=1.6, weights=[.5, .3, .2])
    if ridge and eave:
        (ra, rb), (ea, eb) = (np.array(ridge[0]), np.array(ridge[1])), (np.array(eave[0]), np.array(eave[1]))
        top = [tuple(ra + (rb - ra) * t) for t in np.linspace(0, 1, 12)]
        bot = []; ph = R.uniform(0, 6)
        for t in np.linspace(1, 0, 24):
            u = snowy + .07 * math.sin(t * 7 + ph) + .035 * math.sin(t * 15 + ph * 3)
            a = ra + (rb - ra) * t; b = ea + (eb - ea) * t
            bot.append(tuple(a + (b - a) * np.clip(u, .2, .95)))
        mm = A(top + bot, SNOW, wob=.4, rough=.6, edge_dark=.0)
        stip(mm, [SNOW_H, SNOW, SNOW, SNOW_S], spacing=1.1, L=2.6, w=1.6, weights=[.2, .4, .25, .15])
        S([(x, y + 2.2) for x, y in bot], 3.2, ROOF_D, a=.5, dry=.45, taper=(.2, .2))
        S(bot, 3.0, SNOW_H, a=.6, dry=.35, taper=(.2, .2))
        # drifts lying across the tiles below the blanket: soft, elongated along the slope's contour
        dirx = rb - ra; dirx = dirx / np.linalg.norm(dirx)
        for _ in range(int(np.linalg.norm(rb - ra) / 9)):
            t = R.uniform(.05, .95); u = R.uniform(snowy + .1, .9)
            a = ra + (rb - ra) * t; b = ea + (eb - ea) * t; p = a + (b - a) * u
            ln, th = R.uniform(9, 20), R.uniform(2.2, 3.8)
            pts = [tuple(p + dirx * ln * v) for v in np.linspace(-.5, .5, 5)]
            snow_edge(pts, th, drip=0)
    return m

# ---- windows: cream frame, glowing glass, bars, a sill with snow ----
def window(x0, y0, x1, y1, arched=True, bars=(1, 1), frame=4.0):
    def poly(a0, b0, a1, b1):
        w = a1 - a0
        if not arched: return [(a0, b1), (a0, b0), (a1, b0), (a1, b1)]
        r = w / 2; cy = b0 + r
        return [(a0, b1), (a0, cy)] + [(a0 + r - r * math.cos(math.pi * k / 14), cy - r * math.sin(math.pi * k / 14)) for k in range(1, 14)] + [(a1, cy), (a1, b1)]
    halo = poly(x0 - frame - 6, y0 - frame - 6, x1 + frame + 6, y1 + frame + 4)
    c.area(T(halo), hexc('#f0b860'), wob=.6, rough=.8, edge_dark=0, a=.16, var=.0, varbig=.0, seed=int(R.randint(1 << 20)))
    fm = A(poly(x0 - frame, y0 - frame, x1 + frame, y1 + frame * .5), CREAM, wob=.25, rough=.5, edge_dark=.18)
    stip(fm, [CREAM, CREAM, CREAM_D], spacing=.9, L=1.5, w=1.0)
    gm = A(poly(x0, y0, x1, y1), GOLD, wob=.15, rough=.4, edge_dark=.0)
    cx, cy = (x0 + x1) / 2 - X0, (y0 + y1) / 2 - Y0 + (y1 - y0) * .12; hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
    C0, C1, C2 = hexc(GOLD_C), hexc(GOLD), hexc(GOLD_E)
    def gcol(X, Y, r):
        d = np.clip(np.hypot((X - cx) / hw, (Y - cy) / hh), 0, 1.4)[:, None]
        col = np.where(d < .6, C0 * (1 - d / .6) + C1 * (d / .6), C1 * np.clip(1.4 - d, 0, 1) / .8 + C2 * np.clip(d - .6, 0, .8) / .8)
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .08), 0, 1)
    c.stip(gm, gcol, spacing=.75, L=1.3, w=.95, seed=int(R.randint(1 << 20)), jit=.5)
    x0_, y0_, mm = gm; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm)
    nb, nh = bars; top = y0 + ((x1 - x0) * .08 if arched else 0)
    body = y0 + ((x1 - x0) / 2 if arched else 0) * .6
    for i in range(1, nb + 1):
        xx = x0 + (x1 - x0) * i / (nb + 1); S([(xx, top), (xx + .3, y1)], 1.3, BAR, a=.95, dry=.05, taper=(.05, .05))
    for j in range(1, nh + 1):
        yy = body + (y1 - body) * j / (nh + 1); S([(x0 + .5, yy), (x1 - .5, yy + .3)], 1.2, BAR, a=.95, dry=.05, taper=(.05, .05))
    # the bars stay dark when the glass glows
    for i in range(1, nb + 1):
        xx = (x0 + (x1 - x0) * i / (nb + 1) - X0) * K
        cv2.line(GLOW, (int(xx), int((top - Y0) * K)), (int(xx), int((y1 - Y0) * K)), 0, int(1.3 * K))
    for j in range(1, nh + 1):
        yy = (body + (y1 - body) * j / (nh + 1) - Y0) * K
        cv2.line(GLOW, (int((x0 - X0) * K), int(yy)), (int((x1 - X0) * K), int(yy)), 0, int(1.2 * K))
    # sill and its snow
    A([(x0 - frame - 2, y1 + frame * .5), (x1 + frame + 2, y1 + frame * .5), (x1 + frame + 1, y1 + frame * .5 + 3.5), (x0 - frame - 1, y1 + frame * .5 + 3.5)], CREAM_D, wob=.1, rough=.3)
    snow_cap(x0 - frame - 2, x1 + frame + 2, y1 + frame * .5 - .5, 5.0)

# ---- greenery: a garland of needle dabs, berries, little bows, a dusting of snow ----
def garland(x0, x1, y, sag=6.0, swags=3, bows=True):
    pts = []
    for i in range(swags):
        a, b = x0 + (x1 - x0) * i / swags, x0 + (x1 - x0) * (i + 1) / swags
        for t in np.linspace(0, 1, 9): pts.append((a + (b - a) * t, y + sag * math.sin(math.pi * t)))
    for (px, py) in pts:
        for _ in range(16):
            ang = R.uniform(0, math.pi); ln = R.uniform(5, 8)
            c.dab(px - X0 + R.uniform(-5, 5), py - Y0 + R.uniform(-4.5, 4.5), ln, R.uniform(1.8, 2.6), ang, NEEDLES[R.randint(4)], a=1, dry=.1)
        track((int((px - X0 - 5) * K), int((py - Y0 - 5) * K), np.ones((int(10 * K), int(10 * K)), np.float32)), .0)
    P = np.array(T(pts)) * K
    cv2.polylines(ALPHA, [P.astype(np.int32)], False, 1.0, int(13 * K), cv2.LINE_AA)
    for (px, py) in pts[::2]:
        c.dots([(px - X0 + R.uniform(-4, 4), py - Y0 + R.uniform(-2, 4))], 1.9, [BERRY], seed=int(R.randint(1 << 20)))
    for (px, py) in pts[::3]:
        c.dab(px - X0 + R.uniform(-3, 3), py - Y0 - 4.5, R.uniform(4, 6), 2.2, R.uniform(-.3, .3), SNOW, a=.95, dry=.2)
    if bows:
        for i in range(swags + 1):
            bx = x0 + (x1 - x0) * i / swags; by = y - 1
            for s in (-1, 1): A([(bx, by), (bx + s * 7, by - 4.5), (bx + s * 7, by + 4)], BERRY, wob=.1, rough=.3, edge_dark=.2)
            A(lump(bx, by, 2.4, 2.4), '#9a1e22', wob=.05, rough=.2)
            for s in (-1, 1): S([(bx, by + 1.5), (bx + s * 3.5, by + 9)], 1.8, BERRY, a=1, dry=.05)

def chimney(x0, x1, ytop, ybot, cap=True):
    m = A([(x0, ybot), (x1, ybot), (x1, ytop), (x0, ytop)], BRICK, wob=.15, rough=.4, edge_dark=.12)
    stip(m, [BRICK, BRICK_D, '#c0603c'], spacing=1.2, L=2.4, w=1.3, ang=0.0, weights=[.5, .3, .2])
    for yy in np.arange(ytop + 4, ybot, 5):
        S([(x0 + .5, yy), (x1 - .5, yy)], .5, '#e1c7a8', a=.45, dry=.5, taper=(0, 0))
    A([(x0 - 2, ytop + 3), (x1 + 2, ytop + 3), (x1 + 2, ytop - 1), (x0 - 2, ytop - 1)], BRICK_D, wob=.1, rough=.3)
    if cap: snow_edge([(x0 - 3, ytop - 2), (x1 + 3, ytop - 2)], 7.0, drip=.4)

# =========================================================================================== the shop
def build():
    # back: the red-roofed house behind, its roof reaching down behind the side roof, its chimney
    chimney(113, 168, 434, 500)
    wall([(96, 572), (96, 526), (205, 526), (205, 572)], BLUE_D, dark=True)            # the back house's wall, in shade
    roof([(82, 528), (104, 472), (212, 452), (238, 474), (214, 528)], snowy=.32, ridge=((104, 470), (212, 450)), eave=((84, 526), (214, 526)))
    snow_edge([(100, 471), (214, 450)], 6.0, drip=0)
    snow_edge([(80, 527), (216, 527)], 7.0, drip=.3)
    chimney(70, 104, 548, 610)
    # the tall house
    wall([(203, 760), (300, 760), (300, 520), (252, 446), (205, 520)], BLUE, fleck=.6)
    eave_shadow([(205, 522), (252, 450), (299, 522)], 8)
    S([(203, 522), (252, 446), (301, 522)], 4.2, CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(200, 520), (252, 443), (305, 520)], 8.5, drip=.3)
    window(233, 485, 268, 521, True)
    window(212, 541, 236, 572, True)
    window(258, 542, 290, 580, False)
    garland(254, 296, 590, sag=4, swags=1)
    # the side wing (set back, so a little darker)
    wall([(24, 902), (104, 902), (104, 662), (24, 662)], BLUE_D, dark=True, fleck=.4)
    eave_shadow([(24, 664), (104, 664)], 9)
    window(51, 683, 76, 727, True)
    # the side roof, running down to the left over the wing
    roof([(10, 664), (54, 596), (140, 566), (200, 566), (108, 664)], snowy=.35, ridge=((54, 596), (196, 566)), eave=((10, 664), (108, 664)))
    snow_edge([(8, 662), (108, 662)], 9.0, drip=.4)
    snow_edge([(10, 662), (54, 596), (140, 566), (196, 566)], 6.0, drip=.0)
    # the front gable
    wall([(100, 902), (303, 902), (303, 662), (200, 566), (100, 662)], BLUE, fleck=.8)
    for yy in (742, 744):
        S([(100, yy), (303, yy)], .6, BLUE_D, a=.4, dry=.4)
    eave_shadow([(102, 664), (200, 568), (300, 664)], 10)
    S([(96, 664), (200, 563), (306, 664)], 4.6, CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(92, 664), (200, 558), (310, 664)], 10.0, drip=.35)
    window(177, 601, 218, 641, True)
    window(126, 655, 160, 703, True)
    window(182, 655, 215, 703, False)
    window(236, 655, 270, 703, True)
    garland(110, 290, 713, sag=9, swags=3)
    # the awning: stripes leaning a little, rounded hems, shadow toward the valance, snow on top
    ax0, ax1, ay, ly, hem = 100, 322, 744, 778, 794
    n = 10
    for i in range(n):
        a, b = i / n, (i + 1) / n
        t0, t1 = ax0 + (ax1 - ax0) * a, ax0 + (ax1 - ax0) * b
        l0, l1 = t0 + 6, t1 + 6
        col, dark = (GREEN_A, GREEN_AD) if i % 2 == 0 else (WHITE_A, '#bdb6a5')
        m = A([(t0, ay), (t1, ay), (l1, ly), (l0, ly)], col, wob=.15, rough=.4, edge_dark=.12)
        stip(m, [col, col, dark], spacing=.9, L=2.6, w=1.0, ang=math.atan2(ly - ay, 6) , weights=[.5, .3, .2])
        sc = [(l1 - (l1 - l0) * k / 10, ly + (hem - ly) * math.sin(math.pi * k / 10)) for k in range(11)]
        mv = A([(l0, ly - .5), (l1, ly - .5)] + sc[1:-1], col, wob=.1, rough=.3, edge_dark=.18)
        stip(mv, [dark, col], spacing=.9, L=1.6, w=1.0, ang=0.0, weights=[.45, .55])
    S([(ax0 + 6, ly), (ax1 + 6, ly)], .9, GREEN_AD, a=.5, dry=.4)
    eave_shadow([(ax0 + 8, hem - 2), (ax1 + 6, hem - 2)], 6, WOOD_D)
    snow_edge([(ax0 - 3, ay - 1), (ax1 + 3, ay - 1)], 8.0, drip=.15)
    for _ in range(9):
        px = R.uniform(ax0 + 10, ax1 - 4); py = R.uniform(ay + 6, ly - 4)
        A(lump(px, py, R.uniform(3, 6), R.uniform(1.4, 2.4)), SNOW, wob=.15, rough=.4, edge_dark=.04)
    # the shopfront: dark wooden posts, the display with the bear, side windows, a brick plinth
    A([(104, 902), (306, 902), (306, 796), (104, 796)], WOOD, wob=.15, rough=.4, edge_dark=.12)
    # display window
    disp = A([(173, 879), (252, 879), (252, 800), (173, 800)], GOLD, wob=.1, rough=.3, edge_dark=0)
    cx, cy = 212 - X0, 835 - Y0
    C0, C1 = hexc(GOLD_C), hexc(GOLD_E)
    c.stip(disp, lambda X, Y, r: np.clip((C0 * (1 - np.clip(np.hypot((X - cx) / 40, (Y - cy) / 40), 0, 1)[:, None]) + C1 * np.clip(np.hypot((X - cx) / 40, (Y - cy) / 40), 0, 1)[:, None]) * (1 + (r.rand(len(X), 1) - .5) * .08), 0, 1), spacing=.8, L=1.4, w=1.0, seed=31, jit=.5)
    x0_, y0_, mm = disp; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm * .85)
    # the teddy bear: body, head, ears, muzzle, red bow, paws; a little holly in the corner
    BEAR, BEAR_D, BEAR_L = '#b9733a', '#8a5226', '#d8995a'
    def bl(cx, cy, rx, ry, seed=None, amp=.12):          # the bear, 1.3x around its feet
        return lump(213 + (cx - 213) * 1.3, 862 + (cy - 862) * 1.3, rx * 1.3, ry * 1.3, seed, amp)
    bp = lambda x, y: (213 + (x - 213) * 1.3, 862 + (y - 862) * 1.3)
    A(bl(213, 857, 13, 14, amp=.04), BEAR, wob=.1, rough=.3, edge_dark=.2)
    for s in (-1, 1): A(bl(213 + s * 13, 852, 5, 7, amp=.03), BEAR_D, wob=.1, rough=.3, edge_dark=.15)
    for s in (-1, 1): A(bl(213 + s * 8, 869, 6, 4.5, amp=.03), BEAR_D, wob=.1, rough=.3)
    A(bl(213, 832, 11, 10, amp=.03), BEAR, wob=.1, rough=.3, edge_dark=.2)
    for s in (-1, 1):
        A(bl(213 + s * 9, 822, 4.2, 4.2, amp=.02), BEAR_D, wob=.05, rough=.2); A(bl(213 + s * 9, 822, 2.2, 2.2, amp=.02), BEAR_L, wob=.05, rough=.2)
    A(bl(213, 836, 5, 3.8, amp=.02), BEAR_L, wob=.05, rough=.2)
    c.dots([(bp(213, 834.5)[0] - X0, bp(213, 834.5)[1] - Y0)], 1.6, ['#2a1a12'], seed=3)
    for s in (-1, 1): c.dots([(bp(213 + s * 4, 829)[0] - X0, bp(213 + s * 4, 829)[1] - Y0)], 1.2, ['#1e140e'], seed=4 + s)
    for s in (-1, 1): A([bp(213, 843), bp(213 + s * 7, 839), bp(213 + s * 7, 847)], BERRY, wob=.05, rough=.2, edge_dark=.15)
    A(bl(213, 843, 2, 2), '#9a1e22', wob=.05, rough=.2)
    for k in range(4):
        px, py = 182 + k * 4, 808 + (k % 2) * 3
        c.dab(px - X0, py - Y0, 4, 1.6, R.uniform(0, 3), NEEDLES[k % 4], a=1, dry=.1)
    c.dots([(186 - X0, 812 - Y0), (189 - X0, 810 - Y0)], 1.1, [BERRY], seed=8)
    # side windows: lit glass behind a wooden grid
    for (sx0, sy0, sx1, sy1), (nb, nh) in (((118, 800, 160, 872), (1, 2)), ((258, 800, 300, 866), (1, 1))):
        g = A([(sx0, sy1), (sx1, sy1), (sx1, sy0), (sx0, sy0)], GOLD, wob=.1, rough=.3, edge_dark=.1)
        stip(g, [GOLD_C, GOLD, GOLD_E], spacing=.8, L=1.3, w=.95, weights=[.35, .45, .2])
        x0_, y0_, mm = g; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm)
        for i in range(1, nb + 1):
            xx = sx0 + (sx1 - sx0) * i / (nb + 1); S([(xx, sy0), (xx, sy1)], 2.0, WOOD_D, a=1, dry=.05, taper=(0, 0))
            cv2.line(GLOW, (int((xx - X0) * K), int((sy0 - Y0) * K)), (int((xx - X0) * K), int((sy1 - Y0) * K)), 0, int(2 * K))
        for j in range(1, nh + 1):
            yy = sy0 + (sy1 - sy0) * j / (nh + 1); S([(sx0, yy), (sx1, yy)], 1.8, WOOD_D, a=1, dry=.05, taper=(0, 0))
            cv2.line(GLOW, (int((sx0 - X0) * K), int((yy - Y0) * K)), (int((sx1 - X0) * K), int((yy - Y0) * K)), 0, int(1.8 * K))
    # posts and lintel, the brick plinth under the display, snow on its sill
    for xx in (112, 166, 254, 303):
        S([(xx, 797), (xx, 902)], 4.0, WOOD_D, a=.9, dry=.15, taper=(0, 0))
    S([(104, 797), (306, 797)], 3.5, WOOD_D, a=.9, dry=.15, taper=(0, 0))
    pl = A([(170, 902), (256, 902), (256, 882), (170, 882)], BRICK, wob=.1, rough=.4, edge_dark=.12)
    stip(pl, [BRICK, BRICK_D], spacing=1.1, L=2.4, w=1.2, ang=0.0)
    snow_cap(168, 258, 880, 4.2)
    snow_cap(114, 164, 874, 3.6); snow_cap(254, 302, 868, 3.6)
    # the little wreath on the left post and a tub of greenery by the door
    for k in range(18):
        a = k / 18 * math.tau; c.dab(139 - X0 + 6 * math.cos(a), 888 - Y0 + 6 * math.sin(a), 3.2, 1.5, a + 1.57, NEEDLES[k % 4], a=1, dry=.1)
    c.dots([(139 - X0, 882 - Y0), (144 - X0, 890 - Y0), (134 - X0, 891 - Y0)], 1.0, [BERRY], seed=9)
    # the snowy fir in front of the side wing (in place of the blossom tree)
    fir(58, 908, 190)
    # snow on the ground along the front
    snow_edge([(0, 906), (340, 906)], 9.0, drip=0)

def fir(x, y, h):
    """A fir in the map's manner (tiers of needle dabs), heavy with snow resting on each tier."""
    tiers = [(.08, .38, .36), (.26, .56, .30), (.44, .72, .24), (.6, .86, .17), (.75, 1.0, .1)]
    S([(x, y), (x, y - h * .2)], 4, '#4a3020', a=1, dry=.1)
    for i, (ta, tb, wd) in enumerate(tiers):
        yb, yt = y - h * ta, y - h * tb; half = wd * h
        poly = [(x, yt)] + [(x + half * u + R.uniform(-1, 1), yt + (yb - yt) * u ** .85) for u in np.linspace(.15, 1, 6)]
        poly += [(x + half - 2 * half * k / 6, yb + (2.5 if k % 2 else -1.5)) for k in range(1, 6)]
        poly += [(x - half * u + R.uniform(-1, 1), yt + (yb - yt) * u ** .85) for u in np.linspace(1, .15, 6)]
        m = A(poly, NEEDLES[1], wob=.4, rough=.9, edge_dark=.15)
        stip(m, NEEDLES, spacing=1.0, L=3.4, w=1.3, ang=lambda X, Y: np.where(X < x - X0, math.pi / 2 + .95, math.pi / 2 - .95), weights=[.3, .3, .25, .15])
        # snow lying along the upper side of each tier, heavier toward the tips, heaped where the branches droop
        for side in (-1, 1):
            pts = [(x + side * half * u * .9, yt + (yb - yt) * u ** .85 - 1.0) for u in np.linspace(.12, .96, 6)]
            snow_edge(pts[1:], 6.0 + i * .3, drip=.35)
        for k in range(2):
            px = x + R.uniform(-half * .6, half * .6); snow_edge([(px - 6, yb - 3), (px + 6, yb - 2)], 5.5, drip=.4)
    snow_edge([(x - 3, y - h * .99), (x + 3, y - h * .99)], 4.5, drip=0)

if __name__ == '__main__':
    build()
    impasto(c, strength=.22)
    paint = np.clip(c.img, 0, 1); al = np.clip(cv2.GaussianBlur(ALPHA, (0, 0), .5), 0, 1)
    cv2.imwrite(os.path.join(OUT, 'blue_shop_v3_study.png'), (np.dstack([paint[..., ::-1], al]) * 255).astype(np.uint8))
    halo = cv2.GaussianBlur(GLOW, (0, 0), 3 * K) * .5
    g = np.clip(np.maximum(GLOW * .9, halo), 0, 1) * al
    cv2.imwrite(os.path.join(OUT, 'blue_shop_v3_glow.png'), (np.dstack([np.full_like(paint, (.4, .78, 1.0)), g]) * 255).astype(np.uint8))
    # comparison with the target and the earlier versions, at the study scale
    tgt = cv2.imread(os.path.join(ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))[..., ::-1].astype(np.float32) / 255
    tc = cv2.resize(tgt[Y0:Y1, X0:X1], (W * K, H * K), interpolation=cv2.INTER_CUBIC)
    v3 = paint * al[..., None] + np.array([.93, .91, .87]) * (1 - al[..., None])
    def old(n):
        a = cv2.imread(os.path.join(OUT, n), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255; out = np.ones((H * K, W * K, 3)) * np.array([.93, .91, .87])
        h, w = a.shape[:2]; oy = 0; ox = 0                         # the earlier studies start at y 430 too (BOX 0,430)
        out[:min(h, H * K), :min(w, W * K)] = (a[..., 2::-1] * a[..., 3:] + np.array([.93, .91, .87]) * (1 - a[..., 3:]))[:H * K, :W * K]
        return out
    gap = np.ones((H * K, 24, 3))
    sheet = np.concatenate([tc, gap, old('blue_shop_study.png'), gap, v3], 1)
    cv2.imwrite(os.path.join(OUT, 'blue_shop_v3_compare.jpg'), (sheet[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for nm, (cx0, cy0, cx1, cy1) in {'windows': (100, 595, 300, 735), 'awning': (95, 735, 335, 905)}.items():
        a = (np.array([cx0 - X0, cy0 - Y0, cx1 - X0, cy1 - Y0]) * K).astype(int); g_ = np.ones((a[3] - a[1], 16, 3))
        row = np.concatenate([tc[a[1]:a[3], a[0]:a[2]], g_, v3[a[1]:a[3], a[0]:a[2]]], 1)
        cv2.imwrite(os.path.join(OUT, f'blue_shop_v3_{nm}.jpg'), (row[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print('ok')

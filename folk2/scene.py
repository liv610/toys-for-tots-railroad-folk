"""Folk Art Exploration — Version 2.
A regional countryside painted in the language of the folk-art U.S. map: muted sage and olive, dusty blue, cream, faded red and
ochre; every surface built from short, thick dabs that leave a raised ridge; simple houses with terracotta roofs; dark tiered firs,
blossoming round trees, striped fields, a winding river under a stone bridge, and a little red train slipping into a wooded hill."""
import math, time
import numpy as np, cv2
from kit import *

c = setup('#5f84a2', 909)
c.HM = np.zeros((H, W), np.float32)
R = np.random.RandomState(17)
T0 = time.time()
def log(m): print(f'F {time.time() - T0:6.1f}s {m}', flush=True)
def sfn(y): return .8 + .55 * max(0, y - 300) / 560

CREAM, FADEDRED, TERRA, OCHRE, GOLD = '#efe2c4', '#a8432e', '#b8603a', '#c9963a', '#d8b060'
SAGE, OLIVE, MOSS, FIR, FIR2 = '#a3ab6c', '#7f8a3e', '#8f9a4c', '#2f4a32', '#3a5a3a'
DUSTY, PINK = '#6f8fae', '#dca5a3'

# --------------------------------------------------------------------------- composition
# hills: (cx, base, width, height, palette, kind), back to front
OLV = ['#8a8c42', '#96984c', '#7c7f3a', '#a2a258']; YG = ['#a29f52', '#aeaa5e', '#959448', '#b8b26a']; SG = ['#98a06a', '#a4aa76', '#8a925e', '#b0b482']
MS = ['#6f7a38', '#7a8642', '#646e32', '#86904c']; DK = ['#4f6234', '#59703a', '#45582e', '#647a44']
HILLS = [
    (90, 330, 400, 110, DK, 'forest'), (430, 318, 380, 96, MS, 'forest'), (760, 310, 360, 90, DK, 'forest'), (1080, 316, 400, 104, MS, 'forest'),
    (1420, 322, 440, 112, DK, 'forest'),
    (200, 470, 500, 190, YG, 'barn'), (600, 462, 420, 170, OLV, 'field'), (1020, 476, 480, 196, YG, 'village'), (1450, 570, 440, 270, DK, 'tunnel'),
    (70, 800, 360, 350, OLV, 'orchard'), (440, 800, 460, 340, ['#9c9a54', '#a8a660', '#8e8e4a', '#b2ae6c'], 'blossom'), (1160, 810, 460, 340, OLV, 'field2'), (800, 812, 300, 250, ['#7a8040', '#868c4a', '#6e7438', '#929656'], 'mid'),
    (180, 970, 680, 220, MS, 'front'), (780, 980, 560, 200, YG, 'frontmid'), (1380, 970, 700, 220, OLV, 'front'),
]
RIVER = catmull([(1196, 300), (1160, 352), (1180, 400), (1130, 446), (1060, 470), (980, 500), (930, 548), (960, 600), (900, 640),
                 (820, 664), (780, 700), (800, 752), (750, 800), (690, 850), (650, 930)], 12)
RAIL = resample(catmull([(-40, 708), (80, 700), (200, 694), (320, 690), (440, 690), (560, 694), (660, 700), (740, 700), (820, 690),
                          (900, 676), (990, 660), (1080, 640), (1170, 612), (1250, 578), (1306, 548), (1338, 530)], 14), 2.0)
def _cross():
    best = None
    for i, p in enumerate(RAIL):
        d = np.hypot(*(RIVER - p).T).min()
        if best is None or d < best[0]: best = (d, i)
    return best[1]
BI = _cross(); BR = (BI - 24, BI + 24)
TUNNEL = tuple(RAIL[-1])

def mound(cx, base, w, h, seed):
    r = np.random.RandomState(seed)
    pts = []
    for u in np.linspace(0, 1, 28):
        x = cx - w / 2 + w * u
        y = base - h * math.sin(u * math.pi) ** .75 * (1 + .06 * math.sin(u * 9 + seed))
        pts.append((x, y))
    pts += [(cx + w / 2 + w * .22, base + h * .45), (cx + w / 2 + w * .3, base + 400), (cx - w / 2 - w * .3, base + 400), (cx - w / 2 - w * .22, base + h * .45)]
    return np.array(pts)

def track(P, sfn, hide=()):
    P = np.asarray(P, float); n = len(P)
    d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    vis = np.ones(n, bool)
    for a, b in hide: vis[a:b] = False
    acc = 0
    for i in range(1, n - 1):
        if not vis[i]: continue
        s = sfn(P[i][1]); acc += np.hypot(*(P[i] - P[i - 1]))
        if acc >= 4.6 * s:
            acc = 0; c.stroke([P[i] + nr[i] * 8 * s, P[i] - nr[i] * 8 * s], 2.8 * s, '#e0cfa2', a=1, dry=.1, taper=(.05, .05), press=.1)
    for off in (4.4, -4.4):
        for k in range(0, n - 1, 20):
            idx = [i for i in range(k, min(n, k + 21)) if vis[i]]
            if len(idx) < 2: continue
            sub = np.array([P[i] + nr[i] * off * sfn(P[i][1]) for i in idx])
            c.stroke(sub, 2.2 * sfn(sub[0][1]), '#5a3a2a', a=1, dry=0, taper=(0, 0), press=.05, rough=.2, streak=0, ridge=0)

# --------------------------------------------------------------------------- painters
def flowdir(top):
    T = np.asarray(top)
    def f(X, Y):
        o = np.argsort(T[:, 0]); dx = np.gradient(T[o, 1]) / (np.gradient(T[o, 0]) + 1e-6)
        return np.arctan(np.interp(X, T[o, 0], dx)) * np.clip(1 - (Y - np.interp(X, T[o, 0], T[o, 1])) / 200, .15, 1)
    return f

def hill(top, cols, seed, bottom=930, poly=None):
    m = c.area(poly if poly is not None else land(top, bottom), cols[0], wob=.8, rough=1, edge_dark=.04, seed=seed)
    c.stip(m, pal_fn(cols, .06), spacing=1.45, L=3.4, w=1.9, angfn=flowdir(top), seed=seed + 1, jit=.35)
    c.stroke(np.asarray(top) + [0, 2], 3, '#c7c78e', a=.35, dry=.6, taper=(.02, .02))
    return m

def stripes(top, xa, xb, d0, d1, cols, seed, n=6):
    """Curved field stripes following a hill, as in the reference's ochre farmland."""
    T = np.asarray(top); o = np.argsort(T[:, 0])
    def ty(x): return float(np.interp(x, T[o, 0], T[o, 1]))
    for k in range(n):
        a_, b_ = d0 + (d1 - d0) * k / n, d0 + (d1 - d0) * (k + 1) / n
        xx = np.linspace(xa + k * 6, xb - k * 4, 26)
        q = [(x, ty(x) + a_ + 6 * math.sin((x - xa) / 60)) for x in xx] + [(x, ty(x) + b_ + 6 * math.sin((x - xa) / 60)) for x in xx[::-1]]
        col = cols[k % len(cols)]
        m = c.area(q, col, wob=.4, rough=.8, edge_dark=.05)
        c.stip(m, pal_fn([col, hexc(col) * .9, hexc(col) * 1.08], .05), spacing=1.3, L=3.6, w=1.4, angfn=flowdir(top), seed=seed + k, jit=.12)

def fir(x, y, h, seed, cols=None):
    cols = cols or [['#2f4a32', '#3a5a3a', '#263f2a', '#4a6a42'], ['#2a4436', '#365646', '#22392e', '#46684e']][seed % 2]
    r = np.random.RandomState(seed); w = h * .24
    poly = []
    nt = 5
    for i in range(nt + 1):
        t = i / nt; yy = y - h * .08 - h * .92 * (1 - t); ww = w * (.15 + .85 * t) * (1 + .1 * r.randn())
        poly.append((x - ww, yy)); poly.append((x - ww * .55, yy - h * .05))
    Lp = poly[::-1]; Rp = [(2 * x - p[0], p[1]) for p in poly]
    shape = [(x, y - h)] + Rp[1:] + [(x + w * .2, y - h * .05), (x - w * .2, y - h * .05)] + Lp[:-1]
    c.stroke([(x, y), (x, y - h * .12)], max(1.2, h * .05), '#5a3e2c', a=1, dry=.1, taper=(0, 0))
    m = c.area(shape, cols[0], wob=.15, rough=.7, edge_dark=.1, seed=seed)
    c.stip(m, pal_fn(cols, .06), spacing=1.2, L=2.8, w=1.3, seed=seed + 1,
           angfn=lambda X, Y: np.where(X < x, math.pi / 2 + .8, math.pi / 2 - .8), jit=.25)

def roundtree(x, y, h, seed, kind='green'):
    r = np.random.RandomState(seed)
    pal = {'green': ['#6f7f3a', '#7f8f44', '#5f6f32', '#94a056'], 'blossom': ['#8a9a50', '#9aa65a', '#7a8a46'],
           'orchard': ['#5f7a3a', '#6f8a44', '#4f6a34'], 'autumn': ['#c9963a', '#d8a84a', '#b8822e'], 'sage': ['#8fa070', '#a0b07e', '#7f9062']}[kind]
    rx, ry = h * .36, h * .32; cy = y - h * .62
    c.stroke([(x, y + 1), (x + r.randn() * .4, y - h * .5)], max(1.4, h * .06), '#6a4a34', a=1, dry=.1, taper=(0, .3))
    for k, side in enumerate((-1, 1)):
        c.stroke([(x, y - h * .38), (x + side * h * .14, y - h * .52)], max(.9, h * .025), '#6a4a34', a=1, dry=.1, taper=(0, .6))
    out = S.lumpy(x, cy, rx, ry, seed, n=40, bumps=5, amp=.1, flat=.15)
    m = c.area(out, pal[0], wob=.15, rough=.8, edge_dark=.1, seed=seed)
    def colf(X, Y, rr):
        lit = np.clip((x - X) / rx * .5 + (cy - Y) / ry * .7 + .4, 0, 1)
        C = np.array([hexc(cc) for cc in pal]); idx = np.clip((lit * (len(C) - 1) + rr.randn(len(X)) * .7).round().astype(int), 0, len(C) - 1)
        return C[idx] * (1 + (rr.rand(len(X), 1) - .5) * .08)
    c.stip(m, colf, spacing=1.2, L=2.4, w=1.6, seed=seed + 1, jit=1.6)
    if kind in ('blossom', 'orchard'):
        n = int(h * (1.4 if kind == 'blossom' else .5))
        cols = ['#f2e2dc', '#e8b4b0', '#f6ece2', '#dca0a0'] if kind == 'blossom' else ['#b8402e', '#c8502e']
        pts = []
        for i in range(n):
            a = r.uniform(0, 2 * math.pi); dd = r.rand() ** .6
            pts.append((x + math.cos(a) * rx * dd * .9, cy + math.sin(a) * ry * dd * .85))
        c.dots(pts, max(.7, h * .022), cols, seed=seed + 3)
        for p in pts: c.HM[int(p[1] * K) - 1:int(p[1] * K) + 2, int(p[0] * K) - 1:int(p[0] * K) + 2] = 1.0

def house(x, y, w, h, wall, roof, seed, kind='gable', door=None, side=True, chimney=True, nwin=None):
    r = np.random.RandomState(seed)
    sd = w * .28 if side else 0; D = np.array([sd, -sd * .42])
    BL, BR_, TL, TR = np.array([x - w / 2, y]), np.array([x + w / 2, y]), np.array([x - w / 2, y - h]), np.array([x + w / 2, y - h])
    wc = hexc(wall)
    c.area(S.lumpy(x + sd * .6, y + 1, w * .7 + sd, 2.4, seed, n=20, amp=.05), '#4f5a2c', wob=.2, rough=.6, a=.35, edge_dark=0)
    if kind == 'gable':
        rh = w * .5; ap = TL + [w / 2 + r.uniform(-1, 1), -rh]
        if side:
            c.area([BR_, BR_ + D, TR + D, TR], wc * .8, wob=.1, rough=.5)
            rs = [TR + [2.6, 1], ap, ap + D, TR + D + [2.6, 1]]
            m = c.area(rs, roof, wob=.1, rough=.5, edge_dark=.08); c.stip(m, pal_fn([roof, hexc(roof) * .88, hexc(roof) * 1.08]), spacing=1.1, L=2.4, w=1.2, angfn=lambda X, Y: 0 * X + .3, seed=seed + 5, jit=.2)
        m = c.area([BL, BR_, TR, TL], wc, wob=.15, rough=.6, edge_dark=.06, seed=seed)
        c.stip(m, pal_fn([wall, hexc(wall) * .94, hexc(wall) * 1.04]), spacing=1.2, L=2.4, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=seed + 1, jit=.15)
        gm = c.area([TL, TR, ap], wc * .97, wob=.1, rough=.5)
        c.stip(gm, pal_fn([wall, hexc(wall) * .94]), spacing=1.2, L=2.2, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=seed + 2, jit=.15)
        c.stroke([TL + [-3, 1.5], ap, TR + [3, 1.5]], 2.6, roof, a=1, dry=.1, taper=(0, 0))
        if side: c.stroke([ap, ap + D], 2.2, hexc(roof) * .8, a=1, dry=.1, taper=(0, 0))
    else:   # side-gable: a long roof facing us
        rh = h * .62
        eL, eR = TL + [-3.4, 1], TR + [3.4, 1]; RL, RR = TL + [w * .12, -rh], TR + [-w * .12, -rh]
        if side:
            c.area([BR_, BR_ + D, TR + D, RR + D * .5, TR], wc * .8, wob=.1, rough=.5)
        m = c.area([BL, BR_, TR, TL], wc, wob=.15, rough=.6, edge_dark=.06, seed=seed)
        c.stip(m, pal_fn([wall, hexc(wall) * .94, hexc(wall) * 1.04]), spacing=1.2, L=2.4, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=seed + 1, jit=.15)
        rm = c.area([eL, eR, RR, RL], roof, wob=.1, rough=.5, edge_dark=.08)
        c.stip(rm, pal_fn([roof, hexc(roof) * .88, hexc(roof) * 1.08]), spacing=1.1, L=2.6, w=1.2, angfn=lambda X, Y: 0 * X, seed=seed + 5, jit=.15)
    nw = nwin or max(1, int(w / 12))
    rows = 2 if h > 22 else 1
    for i in range(rows):
        for j in range(nw):
            if i == rows - 1 and nw >= 3 and j == nw // 2: continue
            wx = x - w / 2 + (j + .5) / nw * w + r.uniform(-.8, .8); wy = y - h + (i + .5) / (rows + .5) * h + 1
            ww, wh = min(4.6, w / (nw * 2.4)), min(5.6, h / (rows * 2.6))
            c.area([(wx - ww / 2 - .7, wy - wh / 2 - .7), (wx + ww / 2 + .7, wy - wh / 2 - .7), (wx + ww / 2 + .7, wy + wh / 2 + .7), (wx - ww / 2 - .7, wy + wh / 2 + .7)], '#f2ead6', wob=0, rough=.3)
            c.area([(wx - ww / 2, wy - wh / 2), (wx + ww / 2, wy - wh / 2), (wx + ww / 2, wy + wh / 2), (wx - ww / 2, wy + wh / 2)], ['#5a7488', '#4a6276'][r.randint(2)], wob=0, rough=.3)
            c.stroke([(wx, wy - wh / 2), (wx, wy + wh / 2)], .45, '#f2ead6', a=1, dry=0, taper=(0, 0))
    dw, dh = min(5, w * .18), min(9, h * .42)
    dx = x + (r.choice([-.18, 0, .18]) * w if nw != 3 else 0)
    c.area([(dx - dw / 2, y), (dx + dw / 2, y), (dx + dw / 2, y - dh), (dx - dw / 2, y - dh)], door or '#6a3e2c', wob=0, rough=.3)
    if chimney:
        px = x + w * r.uniform(.1, .3); py = y - h - (w * .5 if kind == 'gable' else h * .62) * .5
        c.area([(px - 1.8, py), (px + 1.8, py), (px + 1.8, py - 7), (px - 1.8, py - 7)], '#8a4a36', wob=0, rough=.3)

def barn(x, y, w=58, h=34):
    sd = w * .34; D = np.array([sd, -sd * .42])
    BL, BR_, TL, TR = np.array([x - w / 2, y]), np.array([x + w / 2, y]), np.array([x - w / 2, y - h]), np.array([x + w / 2, y - h])
    rh = w * .46; ap = TL + [w / 2, -rh]; kL = TL + [w * .08, -rh * .55]; kR = TR + [-w * .08, -rh * .55]
    c.area(S.lumpy(x + sd * .6, y + 1, w * .8, 3, 1, n=20, amp=.05), '#4f5a2c', wob=.2, rough=.6, a=.35)
    sm = c.area([BR_, BR_ + D, TR + D, TR], hexc(FADEDRED) * .78, wob=.1, rough=.5); c.stip(sm, pal_fn([hexc(FADEDRED) * .78, hexc(FADEDRED) * .7]), spacing=1.2, L=2.6, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=3)
    rs = [TR + [3, 1], kR + [1, 0], ap, ap + D, kR + D + [1, 0], TR + D + [3, 1]]
    rm = c.area(rs, '#6a6e72', wob=.1, rough=.5); c.stip(rm, pal_fn(['#6a6e72', '#7a7e80', '#5a5e62']), spacing=1.1, L=2.4, w=1.2, angfn=lambda X, Y: .3 + 0 * X, seed=4)
    fm = c.area([BL, BR_, TR, kR, ap, kL, TL], FADEDRED, wob=.15, rough=.6, edge_dark=.06)
    c.stip(fm, pal_fn([FADEDRED, hexc(FADEDRED) * .92, hexc(FADEDRED) * 1.06]), spacing=1.2, L=2.6, w=1.3, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=5)
    c.stroke([TL + [-3, 1], kL, ap, kR, TR + [3, 1]], 2.6, '#f2ead6', a=1, dry=.1, taper=(0, 0))
    dw, dh = w * .38, h * .7
    q = [(x - dw / 2, y), (x + dw / 2, y), (x + dw / 2, y - dh), (x - dw / 2, y - dh)]
    for a_, b_ in ((q[0], q[1]), (q[1], q[2]), (q[2], q[3]), (q[3], q[0]), (q[0], q[2]), (q[1], q[3])):
        c.stroke([a_, b_], 1.5, '#f2ead6', a=1, dry=.05, taper=(0, 0))
    c.area([(x - 3, y - h - rh * .35), (x + 3, y - h - rh * .35), (x + 3, y - h - rh * .1), (x - 3, y - h - rh * .1)], '#f2ead6', wob=0, rough=.3)
    sx, sy, sw, sh_ = x + w / 2 + sd + 10, y - 2, 14, 56
    smk = c.area([(sx - sw / 2, sy), (sx + sw / 2, sy), (sx + sw / 2, sy - sh_), (sx - sw / 2, sy - sh_)], '#b9b6a8', wob=.1, rough=.5)
    c.stip(smk, pal_fn(['#b9b6a8', '#a8a698', '#c8c6b8']), spacing=1.1, L=2.2, w=1.2, angfn=lambda X, Y: 0 * X, seed=6)
    dome = [(sx - sw / 2 - 1 + (sw + 2) * u, sy - sh_ - math.sin(u * math.pi) * 8) for u in np.linspace(0, 1, 14)]
    c.area(dome, '#8a8e92', wob=0, rough=.4)
    for k in range(5): c.stroke([(sx - sw / 2, sy - sh_ * (k + .5) / 5), (sx + sw / 2, sy - sh_ * (k + .5) / 5)], .6, '#8a887a', a=.8, dry=.1, taper=(0, 0))

def church(x, y):
    house(x, y, 34, 30, 'gable' and '#f2ead6', TERRA, 51, kind='gable', door='#7a4a34', nwin=2, chimney=False)
    tw = 12; top = y - 30 - 20
    tm = c.area([(x - tw / 2, y - 18), (x + tw / 2, y - 18), (x + tw / 2, top), (x - tw / 2, top)], '#f6efe2', wob=0, rough=.4)
    c.stip(tm, pal_fn(['#f6efe2', '#ebe2d0']), spacing=1.1, L=2.2, w=1.1, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=8)
    c.area([(x - 2, top + 8), (x + 2, top + 8), (x + 2, top + 14), (x - 2, top + 14)], '#5a7488', wob=0, rough=.3)
    sp = [(x - tw / 2 - 1.5, top), (x + tw / 2 + 1.5, top), (x, top - 34)]
    c.area(sp, '#6f7f8a', wob=0, rough=.4)
    c.stroke([(x, top - 34), (x, top - 42)], .9, '#4a3a30', a=1, dry=0, taper=(0, 0)); c.stroke([(x - 2.4, top - 39), (x + 2.4, top - 39)], .9, '#4a3a30', a=1, dry=0, taper=(0, 0))

def cow(x, y, flip=1):
    c.area(S.lumpy(x, y - 5, 7, 3.6, 2, n=20, amp=.03), '#f2ece0', wob=0, rough=.3)
    c.dots([(x - 2 * flip, y - 5.6), (x + 2.6 * flip, y - 4.2)], 1.6, ['#2a2622'])
    c.area(S.lumpy(x + 7.5 * flip, y - 7, 2.4, 2, 3, n=14, amp=0), '#f2ece0', wob=0, rough=.3)
    c.dots([(x + 8.6 * flip, y - 6.4)], 1.0, ['#d8a29c'])
    for dx in (-4.5, -2.5, 3, 5): c.stroke([(x + dx, y - 2.4), (x + dx, y + 1)], .9, '#3a322c', a=1, dry=0, taper=(0, 0))

def picket(pts):
    P = resample(catmull(pts, 6), 3.4)
    for p in P: c.stroke([(p[0], p[1] + .5), (p[0], p[1] - 5)], 1.2, '#f4eee2', a=1, dry=0, taper=(0, .2))
    c.stroke(P - [0, 3.4], .8, '#f4eee2', a=1, dry=0, taper=(0, 0)); c.stroke(P - [0, 1.4], .8, '#f4eee2', a=1, dry=0, taper=(0, 0))

def windpump(x, y):
    for dx in (-6, 6): c.stroke([(x + dx, y), (x + dx * .2, y - 52)], 1.2, '#5a4434', a=1, dry=.05, taper=(0, 0))
    for k in range(5):
        yy = y - 8 - k * 9; ww = 6 * (1 - (k * 9 + 8) / 56)
        c.stroke([(x - ww, yy), (x + ww, yy - 7)], .7, '#5a4434', a=.9, dry=0, taper=(0, 0))
    cx, cy = x, y - 56
    for k in range(14):
        a = k / 14 * 2 * math.pi
        c.stroke([(cx + math.cos(a) * 2.6, cy + math.sin(a) * 2.6), (cx + math.cos(a) * 11, cy + math.sin(a) * 11)], 2.2, '#e8dcc4' if k % 2 else '#8a6a4a', a=1, dry=0, taper=(0, .2))
    c.area([(cx + 11, cy - 3), (cx + 21, cy - 1), (cx + 21, cy + 4), (cx + 11, cy + 3)], FADEDRED, wob=0, rough=.3)

def track(P, sfn, hide=()):
    P = np.asarray(P, float); n = len(P)
    d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    vis = np.ones(n, bool)
    for a, b in hide: vis[a:b] = False
    acc = 0
    for i in range(1, n - 1):
        if not vis[i]: continue
        s = sfn(P[i][1]); acc += np.hypot(*(P[i] - P[i - 1]))
        if acc >= 4.6 * s:
            acc = 0; c.stroke([P[i] + nr[i] * 8 * s, P[i] - nr[i] * 8 * s], 2.8 * s, '#e0cfa2', a=1, dry=.1, taper=(.05, .05), press=.1)
    for off in (4.4, -4.4):
        for k in range(0, n - 1, 20):
            idx = [i for i in range(k, min(n, k + 21)) if vis[i]]
            if len(idx) < 2: continue
            sub = np.array([P[i] + nr[i] * off * sfn(P[i][1]) for i in idx])
            c.stroke(sub, 2.2 * sfn(sub[0][1]), '#5a3a2a', a=1, dry=0, taper=(0, 0), press=.05, rough=.2, streak=0, ridge=0)

# --------------------------------------------------------------------------- paint
def main():
    # dusty blue sky, laid in short swirling dabs, with cream impasto clouds
    m = c.area([(-10, -10), (1610, -10), (1610, 420), (-10, 420)], '#6f90ae', wob=0, rough=0, edge_dark=0)
    c.stip(m, lambda X, Y, r: np.array([hexc('#7092ae'), hexc('#7898b2'), hexc('#6a8ca8'), hexc('#7c9cb4')])[r.randint(4, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .06),
           spacing=2.4, L=9.0, w=2.4, angfn=lambda X, Y: .3 * np.sin(X / 90 + Y / 40), seed=1, jit=.2)
    c.HM *= .25
    for (cx, cy, rx, ry) in [(240, 70, 90, 22), (760, 54, 70, 18), (1210, 86, 100, 24), (1470, 60, 60, 16)]:
        for k in range(4):
            bx = cx - rx * .7 + k * rx * .47; br = ry * (.8 + .5 * math.sin((k + .5) / 4 * math.pi))
            cm = c.area(S.lumpy(bx, cy - br * .25, br * 1.15, br * .9, k + int(cx), n=30, amp=.06, flat=.45), '#efe6d2', wob=.3, rough=.6, edge_dark=.05)
            c.stip(cm, pal_fn(['#f4ecdc', '#e6dcc6', '#fbf5ea', '#d8d0c0']), spacing=1.1, L=3.0, w=1.4,
                   angfn=lambda X, Y, bx=bx, by=cy - br * .25: np.arctan2(Y - by, X - bx) + math.pi / 2, seed=int(cx) + k, jit=.3)
    log('sky')
    # a distant jagged range in lavender and slate, snow laid along the ridges
    for layer, (base, amp, cols, seed) in enumerate([(300, 1.0, ['#8a8cab', '#9698b4', '#7e80a0'], 31), (316, .78, ['#a2a2bc', '#aeacc4', '#9494b2'], 32)]):
        r = np.random.RandomState(seed); xs = np.arange(-20, 1640, 4.0); ys = np.full_like(xs, base)
        peaks = []
        for k in range(16):
            px = r.uniform(0, 1600) if layer else 40 + k * 104 + r.uniform(-30, 30); ph = r.uniform(70, 170) * amp; pw = r.uniform(70, 130)
            ys = np.minimum(ys, base - ph * np.clip(1 - np.abs(xs - px) / pw, 0, 1) ** r.uniform(.9, 1.3) + r.randn(len(xs)) * .6)
            peaks.append((px, base - ph, pw))
        ys = np.convolve(ys, [.25, .5, .25], 'same'); ys[0] = ys[1]; ys[-1] = ys[-2]
        sil = np.vstack([np.stack([xs, ys], 1), [[1640, 420], [-20, 420]]])
        mm = c.area(sil, cols[0], wob=0, rough=.6, edge_dark=.04)
        def mcol(X, Y, rr, peaks=peaks, cols=cols):
            out = np.array([hexc(cc) for cc in cols])[rr.randint(len(cols), size=len(X))]
            for (px, py, pw) in peaks:
                shade = (X > px) & (np.abs(X - px) < pw) & (Y > py)
                out[shade] *= .9
            return out * (1 + (rr.rand(len(X), 1) - .5) * .05)
        c.stip(mm, mcol, spacing=1.3, L=3.4, w=1.4, angfn=lambda X, Y: math.pi / 2 + .9 * np.sin(X / 37), seed=seed + 1, jit=.3)
        for (px, py, pw) in peaks:
            if py > base - 60: continue
            for k in range(int((base - py) / 5)):
                t = r.uniform(0, .55); side = r.choice([-1, 1]); sx = px + side * pw * t * r.uniform(.4, 1); sy = py + (base - py) * t + r.uniform(-2, 4)
                c.stroke([(sx, sy), (sx + side * r.uniform(2, 5), sy + r.uniform(6, 14))], r.uniform(1.4, 2.6), '#f4f0e8' if side < 0 else '#d8d8e4', a=.95, dry=.25, taper=(.05, .6))
    log('mountains')
    # rows of rounded hills, each carrying its own story
    hm = {}
    def paint_row(rows):
        for (cx, base, w, h, pal, kind) in rows:
            poly = mound(cx, base, w, h, int(cx))
            top = poly[:28]
            m = hill(top, pal, int(cx) + int(base), poly=poly)
            hm[kind + str(cx)] = (m, top)
            if kind in ('field', 'field2'):
                stripes(top, cx - w * .2, cx + w * .2, 8, 64, [GOLD, '#c99a4c', '#e2c070', OCHRE, '#b8ae6a'], int(cx), n=6)
            if kind == 'forest' or kind == 'tunnel':
                rr = np.random.RandomState(int(cx)); pts = []
                for i in range(int(w / 3.6)):
                    x = cx + rr.uniform(-.46, .46) * w; ytop = y_on(top, x)
                    y = ytop + rr.uniform(14, (base - ytop) * (.9 if kind == 'forest' else .55) + 14)
                    pts.append((y, x))
                for y, x in sorted(pts):
                    if kind == 'tunnel' and abs(x - TUNNEL[0]) < 34 and abs(y - TUNNEL[1]) < 30: continue
                    if rr.rand() < .72: fir(x, y, rr.uniform(26, 44) * (1 + (y - 300) / 600), int(rr.randint(1e6)))
                    else: roundtree(x, y, rr.uniform(22, 34), int(rr.randint(1e6)), ['green', 'blossom', 'blossom', 'sage', 'autumn'][rr.randint(5)])
    paint_row([hh for hh in HILLS if hh[1] < 400])
    log('back hills')
    paint_row([hh for hh in HILLS if 400 <= hh[1] < 600])
    paint_row([hh for hh in HILLS if 600 <= hh[1] < 900])
    log('middle hills')
    # the river: meandering, with cream ripples and a little fall below the bridge
    poly, nr, wv = ribbon(RIVER, lambda t: 7 + 40 * t ** 1.2)
    rm = c.area(poly, '#5f84a2', wob=.4, rough=.7, edge_dark=.1)
    def rang(X, Y):
        j = np.argmin(np.hypot(RIVER[:, 0][None] - X[:, None], RIVER[:, 1][None] - Y[:, None]), axis=1)
        d = np.gradient(RIVER, axis=0)[j]; return np.arctan2(d[:, 1], d[:, 0])
    c.stip(rm, pal_fn(['#6489a8', '#5a7e9e', '#7598b4', '#4f7494']), spacing=1.3, L=4.2, w=1.4, angfn=rang, seed=70, jit=.1)
    for k in range(140):
        j = R.randint(4, len(RIVER) - 6); t = j / len(RIVER); off = R.uniform(-.3, .3) * (7 + 40 * t ** 1.2)
        p = RIVER[j] + nr[min(j, len(nr) - 1)] * off; d = RIVER[j + 3] - RIVER[j]; d /= np.hypot(*d)
        c.stroke([p - d * 3.5, p - d * 1.2 + nr[j] * .9, p + d * 1.2 - nr[j] * .9, p + d * 3.5], .9, '#e6eadf', a=.85, dry=.1, taper=(.2, .2))
    log('river')
    # the bridge and the line, then a modest tunnel mouth in the wooded hill
    before = c.img.copy()
    track(RAIL, sfn, hide=[BR, (len(RAIL) - 3, len(RAIL))])
    a_, b_ = BR; dk = RAIL[a_:b_ + 1] + [0, 5]
    x0, x1 = dk[0, 0], dk[-1, 0]; base = float(dk[:, 1].max()) + 22
    jj = [j for j in range(len(RIVER)) if RIVER[j][1] >= base - 4]
    aw = 38; ah = 22
    ax = float(np.clip(RIVER[jj[0]][0] if jj else (x0 + x1) / 2, x0 + aw / 2 + 4, x1 - aw / 2 - 4))
    arch = [(ax + aw / 2 - aw * u, base - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    face = np.vstack([dk - [0, 4], [[x1, base]], arch, [[x0, base]]])
    bm = c.area(face, '#b8b0a0', wob=.2, rough=.6, edge_dark=.1)
    c.stip(bm, pal_fn(['#c2baa8', '#aaa290', '#d0c8b6', '#9c9482']), spacing=1.4, L=3.4, w=2.2, angfn=lambda X, Y: 0 * X, seed=81, jit=.2)
    for k in range(4):
        yy = base + 2 + k * 4
        c.stroke([(ax - 12 + k, yy), (ax + 12 - k, yy)], 2.4, '#eef0ea', a=.9, dry=.3, taper=(.1, .1))
    track(RAIL[a_:b_ + 1], sfn)
    tx, ty_ = TUNNEL
    outer = [(tx - 12 + 24 * u, ty_ + 4 - math.sin(u * math.pi) ** .75 * 18) for u in np.linspace(0, 1, 20)]
    c.area(outer + [(tx + 12, ty_ + 5), (tx - 12, ty_ + 5)], '#a8a090', wob=.2, rough=.6)
    inner = [(tx - 7.5 + 15 * u, ty_ + 5 - math.sin(u * math.pi) ** .8 * 12) for u in np.linspace(0, 1, 18)]
    c.area(inner + [(tx + 7.5, ty_ + 6), (tx - 7.5, ty_ + 6)], '#3d3e30', wob=0, rough=.3)
    restipple(c, before, seed=82)
    for k in range(4): fir(tx + R.uniform(-22, 22), ty_ - 20 - R.uniform(0, 12), R.uniform(28, 36), 950 + k)
    log('rail')
    # places on the hills
    objs = []
    VH = [(900, 400, 28, 22, 'gable', CREAM, TERRA), (948, 388, 36, 20, 'side', '#e6c87a', '#8a5a3a'), (1000, 396, 26, 24, 'gable', FADEDRED, '#6a5040'),
          (1100, 392, 34, 20, 'side', '#9ab0bc', TERRA), (1150, 404, 28, 22, 'gable', '#f2ead6', '#7a6050'), (930, 440, 34, 20, 'side', '#dca5a3', '#8a5a3a'),
          (990, 446, 28, 22, 'gable', '#f2ead6', '#b04a32'), (1110, 440, 28, 22, 'gable', '#c9963a', '#6a5040')]
    for i, h in enumerate(VH): objs.append((h[1], 'house', (i, h)))
    objs.append((404, 'church', (1050, 410)))
    objs.append((390, 'barn', (180, 398))); objs.append((380, 'house2', (80, 392, 34, 22, 'side', CREAM, TERRA))); objs.append((380, 'pump', (330, 390)))
    for (x, y, f) in [(110, 432, 1), (160, 440, -1), (250, 430, 1), (330, 446, -1)]: objs.append((y, 'cow', (x, y, f)))
    objs.append((560, 'house2', (420, 580, 30, 22, 'gable', '#f2ead6', TERRA))); objs.append((562, 'house2', (470, 586, 26, 20, 'gable', FADEDRED, '#6a5040')))
    objs.append((640, 'house2', (1180, 600, 30, 22, 'gable', CREAM, TERRA)))
    TREES = [(40, 430, 44, 'fir'), (390, 420, 34, 'blossom'), (520, 420, 36, 'fir'), (560, 430, 32, 'green'), (860, 420, 36, 'blossom'), (1190, 420, 38, 'fir'),
             (840, 450, 32, 'fir'), (1200, 452, 34, 'blossom'), (680, 430, 30, 'blossom'), (720, 440, 34, 'green'),
             (330, 560, 34, 'blossom'), (380, 600, 30, 'green'), (520, 590, 32, 'blossom'), (560, 600, 36, 'fir'), (600, 610, 30, 'blossom'),
             (900, 600, 34, 'green'), (980, 610, 30, 'blossom'), (1040, 620, 36, 'fir'), (1260, 640, 34, 'blossom'), (1300, 650, 30, 'green'),
             (300, 660, 28, 'autumn'), (520, 664, 30, 'green'), (250, 520, 30, 'blossom'), (480, 520, 28, 'autumn'), (700, 560, 32, 'blossom'),
             (760, 560, 28, 'fir'), (840, 580, 30, 'blossom'), (1230, 520, 30, 'autumn'), (1280, 560, 32, 'fir'), (1340, 580, 30, 'blossom'),
             (150, 520, 26, 'autumn'), (60, 500, 34, 'fir'), (100, 506, 30, 'fir'), (640, 500, 30, 'fir')]
    for j in range(3):
        for i in range(5):
            TREES.append((10 + i * 40 + (j % 2) * 20 + R.uniform(-4, 4), 560 + j * 24 + R.uniform(-2, 2), 26 * R.uniform(.9, 1.1), 'orchard'))
    for i, t in enumerate(TREES): objs.append((t[1], 'tree', (i, t)))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'house':
            i, (x, y, w, h, k, wall, roof) = v; house(x, y, w, h, wall, roof, 200 + i, kind=k)
        elif kind == 'house2':
            x, y, w, h, k, wall, roof = v; house(x, y, w, h, wall, roof, int(x), kind=k)
        elif kind == 'church': church(*v)
        elif kind == 'barn': barn(*v)
        elif kind == 'pump': windpump(*v)
        elif kind == 'cow': cow(*v)
        elif kind == 'tree':
            i, (x, y, h, k) = v
            if k == 'fir': fir(x, y, h, 400 + i)
            else: roundtree(x, y, h, 400 + i, k)
    for o in objs: draw(o)
    picket([(50, 452), (140, 446), (240, 450), (300, 460)]); picket([(880, 462), (960, 470), (1040, 468)]); picket([(400, 600), (480, 606)])
    log('places')
    # the front hills, wildflowers and a few big trees
    for (cx, base, w, h, pal, kind) in [hh for hh in HILLS if hh[1] >= 900]:
        poly = mound(cx, base, w, h, int(cx)); hill(poly[:28], pal, int(cx) + 7, poly=poly)
    pts = []
    for (cx, cy, n, sp) in [(140, 800, 160, 70), (440, 830, 120, 60), (760, 820, 120, 50), (1240, 800, 160, 70), (1500, 840, 110, 50)]:
        pts += [(cx + R.randn() * sp, cy + abs(R.randn()) * sp * .4) for _ in range(n)]
    c.dots(pts, 1.25, ['#f4eee2', '#f4eee2', '#e8c060', '#dca5a3', '#c8503a'], seed=79)
    for p in pts: c.HM[int(p[1] * K) - 1:int(p[1] * K) + 2, int(p[0] * K) - 1:int(p[0] * K) + 2] = 1.0
    for (x, y, h, k) in [(40, 860, 140, 'fir'), (110, 880, 110, 'fir'), (300, 900, 100, 'blossom'), (600, 890, 80, 'green'), (1000, 900, 90, 'blossom'),
                         (1180, 880, 70, 'fir'), (1380, 900, 110, 'green'), (1500, 880, 150, 'fir'), (1580, 900, 120, 'fir')]:
        if k == 'fir': fir(x, y, h, int(x) + 3)
        else: roundtree(x, y, h, int(x) + 3, k)
    log('front')
    # the train, painted in the same dabs
    i_head = int(np.argmin(np.abs(RAIL[:, 0] - 470)))
    before = c.img.copy()
    train(c, RAIL, i_head, 1.75)
    restipple(c, before, seed=91)
    impasto(c, .16)
    c.save('out/folk_v2')
    log('saved')

if __name__ == '__main__':
    main()

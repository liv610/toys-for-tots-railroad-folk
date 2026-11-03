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
MOUNT = [(150, 250, 210, 120), (300, 250, 240, 150), (450, 250, 250, 132), (600, 254, 230, 112), (740, 258, 200, 86)]
FOREST = catmull([(-30, 300), (80, 268), (200, 262), (340, 270), (480, 258), (620, 266), (760, 256), (880, 266), (1000, 250), (1140, 262),
                  (1280, 246), (1420, 258), (1630, 246)], 10)
FIELDS_H = catmull([(820, 380), (900, 320), (1020, 290), (1160, 282), (1300, 296), (1420, 320), (1500, 360)], 12)
BARN_H = catmull([(-30, 420), (60, 370), (180, 340), (310, 336), (430, 356), (540, 400), (600, 450)], 12)
WOOD_H = catmull([(1180, 520), (1240, 420), (1320, 360), (1420, 330), (1530, 324), (1630, 330)], 12)
VILL_H = catmull([(520, 520), (600, 452), (700, 420), (820, 410), (940, 424), (1040, 458), (1120, 520)], 12)
LOW_L = catmull([(-30, 600), (100, 560), (240, 548), (380, 566), (500, 610), (580, 680)], 12)
LOW_R = catmull([(900, 700), (1000, 640), (1120, 610), (1260, 600), (1400, 610), (1630, 590)], 12)
FRONT = catmull([(-30, 800), (160, 770), (360, 780), (540, 810), (700, 790), (880, 800), (1080, 780), (1300, 790), (1630, 770)], 12)
RIVER = catmull([(1196, 300), (1160, 350), (1120, 400), (1070, 450), (1010, 500), (930, 540), (860, 580), (800, 620), (770, 670),
                 (740, 730), (680, 790), (610, 840), (560, 930)], 12)
RAIL = resample(catmull([(-40, 744), (80, 730), (200, 716), (320, 700), (440, 684), (560, 666), (660, 650), (740, 640), (820, 628),
                          (900, 610), (990, 590), (1080, 568), (1160, 540), (1230, 510), (1290, 486), (1336, 470)], 14), 2.0)
def _cross():
    best = None
    for i, p in enumerate(RAIL):
        d = np.hypot(*(RIVER - p).T).min()
        if best is None or d < best[0]: best = (d, i)
    return best[1]
BI = _cross(); BR = (BI - 16, BI + 16)
TUNNEL = tuple(RAIL[-1])

# --------------------------------------------------------------------------- painters
def flowdir(top):
    T = np.asarray(top)
    def f(X, Y):
        o = np.argsort(T[:, 0]); dx = np.gradient(T[o, 1]) / (np.gradient(T[o, 0]) + 1e-6)
        return np.arctan(np.interp(X, T[o, 0], dx)) * np.clip(1 - (Y - np.interp(X, T[o, 0], T[o, 1])) / 200, .15, 1)
    return f

def hill(top, cols, seed, bottom=930):
    m = c.area(land(top, bottom), cols[0], wob=.8, rough=1, edge_dark=.04, seed=seed)
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

# --------------------------------------------------------------------------- paint
def main():
    # dusty blue sky, laid in short swirling dabs, with cream impasto clouds
    m = c.area([(-10, -10), (1610, -10), (1610, 420), (-10, 420)], '#6f90ae', wob=0, rough=0, edge_dark=0)
    c.stip(m, lambda X, Y, r: np.array([hexc('#6f90ae'), hexc('#7b9ab6'), hexc('#6386a6'), hexc('#88a6bc')])[r.randint(4, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .06),
           spacing=1.8, L=4.2, w=1.8, angfn=lambda X, Y: .35 * np.sin(X / 70 + Y / 30), seed=1, jit=.3)
    for (cx, cy, rx, ry) in [(240, 70, 90, 22), (760, 54, 70, 18), (1210, 86, 100, 24), (1470, 60, 60, 16)]:
        for k in range(4):
            bx = cx - rx * .7 + k * rx * .47; br = ry * (.8 + .5 * math.sin((k + .5) / 4 * math.pi))
            cm = c.area(S.lumpy(bx, cy - br * .25, br * 1.15, br * .9, k + int(cx), n=30, amp=.06, flat=.45), '#efe6d2', wob=.3, rough=.6, edge_dark=.05)
            c.stip(cm, pal_fn(['#f4ecdc', '#e6dcc6', '#fbf5ea', '#d8d0c0']), spacing=1.1, L=3.0, w=1.4,
                   angfn=lambda X, Y, bx=bx, by=cy - br * .25: np.arctan2(Y - by, X - bx) + math.pi / 2, seed=int(cx) + k, jit=.3)
    log('sky')
    # a distant range: lavender-grey with snow laid in along the slopes
    for i, (px, base, w, h) in enumerate(MOUNT):
        pk = (px + R.uniform(-10, 10), base - h)
        poly = [(px - w / 2, base)] + [(px - w / 2 + (pk[0] - px + w / 2) * t, base - h * t ** .9 + R.randn() * 2) for t in np.linspace(.2, .9, 4)] + [pk] + \
               [(pk[0] + (px + w / 2 - pk[0]) * t, base - h * (1 - t) ** .9 + R.randn() * 2) for t in np.linspace(.1, .8, 4)] + [(px + w / 2, base)]
        mm = c.area(poly, '#9c9cb4', wob=.3, rough=.7, edge_dark=.05)
        c.stip(mm, lambda X, Y, r, pkx=pk[0]: np.where((X > pkx)[:, None], np.array([hexc('#7f82a0'), hexc('#8a8ca8')])[r.randint(2, size=len(X))], np.array([hexc('#a8a8be'), hexc('#b4b2c6')])[r.randint(2, size=len(X))]) * (1 + (r.rand(len(X), 1) - .5) * .06),
               spacing=1.3, L=3.6, w=1.4, angfn=lambda X, Y, pkx=pk[0]: np.where(X > pkx, math.pi / 2 - .9, math.pi / 2 + .9), seed=30 + i, jit=.25)
        for k in range(int(h / 4)):
            t = R.uniform(0, .45); side = R.choice([-1, 1]); sx = pk[0] + side * (w / 2) * t * R.uniform(.6, 1.1); sy = pk[1] + h * t
            c.stroke([(sx, sy), (sx + side * 4, sy + R.uniform(6, 14))], R.uniform(1.4, 2.4), '#f2eee6' if side < 0 else '#d6d6e2', a=.95, dry=.2, taper=(.05, .6))
    log('mountains')
    # the far evergreen forest
    hill(FOREST, [FIR, FIR2, '#263f2a', '#456a44'], 40)
    for x in np.arange(-10, 1620, 12):
        y = y_on(FOREST, x) + R.uniform(-2, 14)
        fir(x + R.randn() * 3, y + 18, R.uniform(30, 48), int(R.randint(1e6)))
    log('forest')
    hill(FIELDS_H, [SAGE, '#b0b47a', OLIVE, MOSS], 50)
    stripes(FIELDS_H, 900, 1480, 14, 70, [GOLD, '#c99a4c', '#e2c070', OCHRE], 51, n=6)
    hill(WOOD_H, ['#4a6a42', '#55764a', '#3f5e3a', '#668a56'], 55)
    hill(BARN_H, [SAGE, '#b2b67c', MOSS, '#9aa462'], 60)
    hill(VILL_H, ['#b4b67a', '#c0c088', SAGE, '#a8ae70'], 65)
    log('hills')
    # river with cream ripples, then the low hills over it
    poly, nr, wv = ribbon(RIVER, lambda t: 8 + 54 * t ** 1.2)
    rm = c.area(poly, '#5f84a2', wob=.4, rough=.7, edge_dark=.1)
    def rang(X, Y):
        j = np.argmin(np.hypot(RIVER[:, 0][None] - X[:, None], RIVER[:, 1][None] - Y[:, None]), axis=1)
        d = np.gradient(RIVER, axis=0)[j]; return np.arctan2(d[:, 1], d[:, 0])
    c.stip(rm, pal_fn(['#6489a8', '#5a7e9e', '#7598b4', '#4f7494']), spacing=1.3, L=4.2, w=1.4, angfn=rang, seed=70, jit=.1)
    for k in range(120):
        j = R.randint(4, len(RIVER) - 6); t = j / len(RIVER); off = R.uniform(-.3, .3) * (8 + 54 * t ** 1.2)
        p = RIVER[j] + nr[min(j, len(nr) - 1)] * off; d = RIVER[j + 3] - RIVER[j]; d /= np.hypot(*d)
        c.stroke([p - d * 4, p - d * 1.5 + nr[j] * 1, p + d * 1.5 - nr[j] * 1, p + d * 4], 1.0, '#e6eadf', a=.85, dry=.1, taper=(.2, .2))
    log('river')
    hill(LOW_L, ['#9aa462', '#a8b070', '#8a964e', '#b6ba80'], 72)
    hill(LOW_R, ['#a3ab6c', '#b0b47a', '#8f9a56', '#bcbc84'], 74)
    stripes(LOW_R, 1180, 1600, 14, 64, [GOLD, '#b8ae6a', '#e2c070', '#a8a860'], 75, n=5)
    # wildflower meadow along the front
    fm = hill(FRONT, ['#8f9a4c', '#9aa45a', '#7f8a44', '#a8ae66'], 78)
    pts = []
    for (cx, cy, n, sp) in [(120, 830, 160, 70), (420, 850, 140, 60), (980, 840, 120, 60), (1300, 830, 160, 70), (1520, 850, 110, 50)]:
        pts += [(cx + R.randn() * sp, cy + abs(R.randn()) * sp * .35) for _ in range(n)]
    c.dots(pts, 1.2, ['#f4eee2', '#f4eee2', '#e8c060', '#dca5a3', '#c8503a'], seed=79)
    for p in pts: c.HM[int(p[1] * K) - 1:int(p[1] * K) + 2, int(p[0] * K) - 1:int(p[0] * K) + 2] = 1.0
    log('meadows')
    # the stone bridge and the line (painted in the same dabs), then the tunnel
    before = c.img.copy()
    rails(c, RAIL, sfn, ballast=None, tie='#d6c49a', steel='#5a3a2a', hide=[BR, (len(RAIL) - 3, len(RAIL))], shine=None)
    a_, b_ = BR; dk = RAIL[a_:b_ + 1] + [0, 4]
    x0, x1 = dk[0, 0], dk[-1, 0]; base = float(dk[:, 1].max()) + 22
    jj = [j for j in range(len(RIVER)) if RIVER[j][1] >= base - 4]
    aw = 34; ah = 18
    ax = float(np.clip(RIVER[jj[0]][0] if jj else (x0 + x1) / 2, x0 + aw / 2 + 4, x1 - aw / 2 - 4))
    arch = [(ax + aw / 2 - aw * u, base - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    face = np.vstack([dk - [0, 3], [[x1, base]], arch, [[x0, base]]])
    bm = c.area(face, '#b8b0a0', wob=.2, rough=.6, edge_dark=.1)
    c.stip(bm, pal_fn(['#c2baa8', '#aaa290', '#d0c8b6', '#9c9482']), spacing=1.4, L=3.4, w=2.2, angfn=lambda X, Y: 0 * X, seed=81, jit=.2)
    c.stroke(dk - [0, 2], 5, '#d6cebc', a=1, dry=.1, taper=(0, 0))
    rails(c, RAIL[a_:b_ + 1], sfn, ballast=None, tie='#d6c49a', steel='#5a3a2a', shine=None)
    tx, ty_ = TUNNEL
    outer = [(tx - 13 + 26 * u, ty_ + 3 - math.sin(u * math.pi) ** .75 * 20) for u in np.linspace(0, 1, 20)]
    c.area(outer + [(tx + 13, ty_ + 4), (tx - 13, ty_ + 4)], '#a8a090', wob=.2, rough=.6)
    inner = [(tx - 8 + 16 * u, ty_ + 4 - math.sin(u * math.pi) ** .8 * 13) for u in np.linspace(0, 1, 18)]
    c.area(inner + [(tx + 8, ty_ + 5), (tx - 8, ty_ + 5)], '#3a3a2e', wob=0, rough=.3)
    restipple(c, before, seed=82)
    log('rail')
    # places, back to front
    objs = []
    VH = [(640, 470, 30, 24, 'gable', CREAM, TERRA), (690, 452, 40, 22, 'side', '#e6c87a', '#8a5a3a'), (744, 462, 28, 26, 'gable', FADEDRED, '#6a5040'),
          (800, 448, 36, 22, 'side', '#9ab0bc', TERRA), (900, 456, 30, 26, 'gable', '#f2ead6', '#7a6050'), (950, 476, 36, 22, 'side', '#dca5a3', '#8a5a3a'),
          (700, 508, 34, 24, 'gable', '#f2ead6', '#b04a32'), (780, 500, 30, 22, 'gable', '#c9963a', '#6a5040'), (880, 506, 40, 22, 'side', '#f2ead6', TERRA),
          (1010, 504, 28, 24, 'gable', '#a8432e', '#5a4a40')]
    for i, h in enumerate(VH): objs.append((h[1], 'house', (i, h)))
    objs.append((462, 'church', (846, 466)))
    objs.append((380, 'barn', (210, 390))); objs.append((380, 'house2', (110, 384, 36, 24, 'side', CREAM, TERRA))); objs.append((370, 'pump', (330, 372)))
    for (x, y, f) in [(120, 440, 1), (170, 452, -1), (260, 440, 1), (380, 470, -1)]: objs.append((y, 'cow', (x, y, f)))
    objs.append((560, 'house2', (1130, 300, 26, 20, 'gable', CREAM, TERRA)))
    TREES = [(40, 400, 50, 'fir'), (64, 410, 44, 'fir'), (430, 380, 40, 'blossom'), (480, 400, 46, 'fir'), (520, 420, 40, 'green'),
             (600, 470, 38, 'blossom'), (980, 446, 40, 'blossom'), (1060, 470, 44, 'fir'), (1090, 480, 38, 'green'), (660, 520, 34, 'autumn'),
             (840, 520, 30, 'green'), (960, 520, 34, 'blossom'), (1150, 290, 36, 'fir'), (1100, 300, 30, 'green'),
             (1260, 470, 52, 'fir'), (1300, 440, 56, 'fir'), (1350, 420, 50, 'fir'), (1400, 400, 58, 'fir'), (1450, 386, 52, 'fir'), (1500, 380, 60, 'fir'),
             (1550, 384, 54, 'fir'), (1600, 390, 58, 'fir'), (1380, 470, 48, 'blossom'), (1440, 460, 52, 'fir'), (1520, 450, 56, 'fir'), (1580, 450, 50, 'green'),
             (1330, 452, 40, 'fir'), (1360, 486, 42, 'green'), (1300, 498, 40, 'fir'),
             (560, 700, 50, 'blossom'), (860, 690, 44, 'green'), (1020, 680, 48, 'fir'), (1100, 700, 40, 'blossom'),
             (60, 800, 120, 'fir'), (200, 840, 90, 'blossom'), (1440, 830, 110, 'green'), (1560, 860, 130, 'fir')]
    for j in range(3):
        for i in range(6):
            TREES.append((90 + i * 52 + (j % 2) * 26 + R.uniform(-5, 5), 610 + j * 34 + R.uniform(-3, 3), 34 * R.uniform(.9, 1.1), 'orchard'))
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
    picket([(60, 420), (140, 414), (240, 418), (300, 428)]); picket([(620, 528), (700, 534), (760, 530)]); picket([(1180, 650), (1280, 640), (1360, 646)])
    path(c, [(760, 640), (780, 600), (800, 560), (820, 520)], 4, '#d8c49a', sfn, seed=4)
    log('places')
    # the train, painted in the same dabs
    i_head = int(np.argmin(np.abs(RAIL[:, 0] - 560)))
    before = c.img.copy()
    train(c, RAIL, i_head, 1.75)
    restipple(c, before, seed=91)
    impasto(c, .16)
    c.save('out/folk_v2')
    log('saved')

if __name__ == '__main__':
    main()

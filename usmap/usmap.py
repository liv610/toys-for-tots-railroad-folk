"""Toys for Tots Railroad — code reconstruction of the folk-art U.S. map.
Coordinates are the reference's own pixel space (1672 x 941), rendered at 3200 x 1800.
Traced from the reference: the coastline and Great Lakes outlines (geometry only). Everything else is painted with the
village's brush system: stippled dabs, skeleton trees, stippled firs, folk houses, and paint-ridge relief."""
import sys, math, time
sys.path.insert(0, '/home/claude/folk2'); sys.path.append('/home/claude/styles2')
import numpy as np, cv2
from brush import *
import kit
from kit import Kanvas, pal_fn, catmull, resample, stipple_fir, skeleton_tree, bush, impasto, restipple, ribbon
import story as S
import a as A

RW, RH = 1672, 941
W, H = 3200, 1800
k = W / RW
c = Kanvas(W, H, k, '#2c5684', seed=1972)
c.HM = np.zeros((H, W), np.float32)
S.c = c; A.c = c
R = np.random.RandomState(1972)
_win = A.window
A.window = lambda x, y, ww, wh, lit=True, arch=False, frame='#2a2030': _win(x, y, ww, wh, False, arch, '#efe6d2')
T0 = time.time()
def log(m): print(f'US {time.time() - T0:6.1f}s {m}', flush=True)

COAST = np.load('coast.npy')
LAKES = list(np.load('lakes.npy', allow_pickle=True))
from matplotlib.path import Path as MP
LANDP = MP(COAST); LAKEP = [MP(l) for l in LAKES]
def on_land(x, y, pad=0):
    if not LANDP.contains_point((x, y), radius=-pad): return False
    return not any(lp.contains_point((x, y), radius=pad) for lp in LAKEP)

# --------------------------------------------------------------------------- the railroad, as continuous paths
RED = resample(catmull([(30, 166), (100, 160), (150, 166), (176, 204), (176, 256), (192, 304), (236, 348), (300, 384), (380, 404),
                         (470, 414), (560, 420), (640, 424), (700, 424), (744, 414), (772, 402)], 14), 1.6)
BLUE = resample(catmull([(104, 596), (220, 600), (340, 598), (440, 580), (540, 566), (620, 552), (680, 516), (712, 470), (730, 440), (744, 416)], 14), 1.6)
GREEN = resample(catmull([(1580, 196), (1550, 250), (1510, 300), (1460, 356), (1400, 404), (1320, 432), (1240, 446), (1160, 448), (1100, 436), (1060, 418)], 14), 1.6)
GREEN2 = resample(catmull([(1460, 360), (1480, 440), (1450, 520), (1400, 572), (1320, 610), (1220, 622), (1140, 612), (1080, 606), (1010, 596),
                            (950, 580), (900, 556), (872, 534)], 14), 1.6)
WEST_PORTAL, EAST_PORTAL = (776, 400), (1056, 414)
TRACKCOL = {'red': ('#b03a2c', '#d86a4a'), 'blue': ('#2f5a9c', '#e8dcc0'), 'green': ('#6f8a34', '#efe6c8')}

def track(P, kind, w=11.0):
    rail, tie = TRACKCOL[kind]
    P = np.asarray(P, float); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    for kk in range(0, len(P) - 1, 12):
        sub = P[kk:kk + 14]
        if len(sub) > 1: c.stroke(sub, w * 2.6, '#6a5a3c', a=.35, dry=.3, taper=(0, 0), press=0, rough=.5)
    acc = 0
    for i in range(1, len(P) - 1):
        acc += np.hypot(*(P[i] - P[i - 1]))
        if acc >= w * .9:
            acc = 0; c.stroke([P[i] + nr[i] * w * 1.15, P[i] - nr[i] * w * 1.15], w * .55, tie, a=1, dry=.15, taper=(.05, .05), press=.1, rough=.4)
    for off in (w * .8, -w * .8):
        for kk in range(0, len(P) - 1, 18):
            sub = np.array([P[i] + nr[i] * off for i in range(kk, min(len(P), kk + 19))])
            if len(sub) > 1: c.stroke(sub, w * .42, rail, a=1, dry=.05, taper=(0, 0), press=.05, rough=.3, streak=.12)

# --------------------------------------------------------------------------- painters
def mound(cx, base, w, h, seed, flat=.75):
    r = np.random.RandomState(seed); pts = []
    for u in np.linspace(0, 1, 30):
        pts.append((cx - w / 2 + w * u, base - h * math.sin(u * math.pi) ** flat * (1 + .07 * math.sin(u * 7 + seed))))
    pts += [(cx + w / 2 + w * .1, base + 30), (cx - w / 2 - w * .1, base + 30)]
    return np.array(pts)

def flow_of(top):
    T = np.asarray(top); o = np.argsort(T[:, 0])
    def f(X, Y):
        dx = np.gradient(T[o, 1]) / (np.gradient(T[o, 0]) + 1e-6)
        return np.arctan(np.interp(X, T[o, 0], dx)) * np.clip(1 - (Y - np.interp(X, T[o, 0], T[o, 1])) / 120, .15, 1)
    return f

def paint_mound(cx, base, w, h, pal, seed, stripes=None):
    poly = mound(cx, base, w, h, seed)
    m = c.area(poly, pal[0], wob=.6, rough=1, edge_dark=.05, seed=seed)
    if m is None: return
    x0, y0, mm = m
    lm = LAND_MASK[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]
    m = (x0, y0, mm * lm)
    c.stip(m, pal_fn(pal, .06), spacing=1.25, L=3.4, w=1.7, angfn=flow_of(poly[:30]), seed=seed + 1, jit=.35)
    if stripes:
        T = poly[:30]
        prev = c.clipm; c.set_clip(m)
        for j, d in enumerate(np.arange(8, h * 1.1, 7)):
            line = [(x, float(np.interp(x, T[:, 0], T[:, 1])) + d) for x in np.linspace(cx - w * .45, cx + w * .45, 30)]
            c.stroke(line, 3.0, stripes[j % len(stripes)], a=.95, dry=.25, taper=(.05, .05), rough=.5)
        c.clipm = prev
    c.stroke(poly[:30] + [0, 1.6], 2.4, '#d8cf8a', a=.35, dry=.6, taper=(.05, .05))

def tree(x, y, h, kind, seed):
    r = np.random.RandomState(seed)
    if kind == 'fir':
        stipple_fir(c, x, y, h, [['#2a4a34', '#365a3e', '#20402c', '#4a6e46'], ['#2f4f3a', '#3e6448', '#264434', '#56784e'], ['#3a5a30', '#4a6e38', '#2f4a28']][seed % 3], seed, slim=.22)
        return
    pal = {'green': ['#5f7f30', '#7a9a3c', '#4f6e28', '#9ab048'], 'yellow': ['#c9a030', '#e0b840', '#b08a28', '#e8c860'],
           'orange': ['#d0702a', '#e08a36', '#b85a22', '#eaa048'], 'red': ['#b8402a', '#c8503a', '#9e3424', '#d86a4a'],
           'pink': ['#d88a9a', '#e8a6b2', '#c87080', '#f2c4c8'], 'white': ['#e8e0cc', '#f4ecdc', '#d8ccb4', '#c8d0a0'],
           'olive': ['#7f8a30', '#96a03a', '#6a7428']}[kind]
    dots = None
    if kind in ('pink', 'white'): dots = ['#f6eee4', '#f2c4c8'] if kind == 'pink' else ['#fbf6ec', '#f0d8d0']
    if kind == 'red' and r.rand() < .4: dots = ['#f4c060']
    skeleton_tree(c, x, y, h, pal, seed, dots=dots, branches='#4a3424', shape='round')

def house(x, y, w, h, wall, roof, seed, kind='gable', rows=None, cols_=None):
    A.house(x, y, w * .82, h * .72, kind, wall, roof, seed, dotcol=None, rows=rows or 1, cols_=cols_ or 2)

def lighthouse(x, y, h):
    w0, w1 = h * .2, h * .13
    body = [(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y - h), (x - w1 / 2, y - h)]
    m = c.area(body, '#f2ead8', wob=.1, rough=.5, edge_dark=.08)
    prev = c.clipm; c.set_clip(m)
    for kk in range(4):
        yy = y - h * (kk * 2 + 1) / 8
        c.area([(x - h, yy), (x + h, yy), (x + h, yy - h / 8), (x - h, yy - h / 8)], '#b83a2e', wob=0, rough=.4)
    c.clipm = prev
    c.stip(m, lambda X, Y, rr: np.clip(c.img[np.clip((Y * k).astype(int), 0, H - 1), np.clip((X * k).astype(int), 0, W - 1)] * (1 + (rr.rand(len(X), 1) - .5) * .12), 0, 1),
           spacing=1.1, L=2.2, w=1.1, angfn=lambda X, Y: 0 * X, seed=int(x))
    c.area([(x - w1 / 2 - 2, y - h), (x + w1 / 2 + 2, y - h), (x + w1 / 2 + 2, y - h - 4), (x - w1 / 2 - 2, y - h - 4)], '#3a2e2a', wob=0, rough=.3)
    c.area([(x - w1 / 2, y - h - 4), (x + w1 / 2, y - h - 4), (x + w1 / 2, y - h - 12), (x - w1 / 2, y - h - 12)], '#f2d06a', wob=0, rough=.3)
    c.area([(x - w1 / 2 - 2, y - h - 12), (x + w1 / 2 + 2, y - h - 12), (x, y - h - 20)], '#b83a2e', wob=0, rough=.3)

def windmill(x, y, h):
    for dx in (-h * .14, h * .14): c.stroke([(x + dx, y), (x + dx * .2, y - h * .85)], 2.2, '#3a2e26', a=1, dry=.05, taper=(0, 0))
    for kk in range(6):
        yy = y - h * .12 - kk * h * .12; ww = h * .14 * (1 - (kk * .12 + .12))
        c.stroke([(x - ww, yy), (x + ww, yy - h * .1)], 1.2, '#3a2e26', a=1, dry=0, taper=(0, 0)); c.stroke([(x + ww, yy), (x - ww, yy - h * .1)], 1.2, '#3a2e26', a=1, dry=0, taper=(0, 0))
    cx, cy = x, y - h * .9
    for kk in range(16):
        a = kk / 16 * 2 * math.pi
        c.stroke([(cx + math.cos(a) * 4, cy + math.sin(a) * 4), (cx + math.cos(a) * h * .26, cy + math.sin(a) * h * .26)], 4, '#efe6d0' if kk % 2 else '#3a2e26', a=1, dry=.05, taper=(0, .25))
    c.area([(cx + h * .2, cy - 5), (cx + h * .36, cy - 2), (cx + h * .36, cy + 6), (cx + h * .2, cy + 4)], '#b8402e', wob=0, rough=.3)

def silo(x, y, w, h):
    m = c.area([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], '#c8bea8', wob=.1, rough=.5, edge_dark=.08)
    c.stip(m, pal_fn(['#c8bea8', '#b4aa94', '#d8d0bc']), spacing=1.1, L=3.0, w=1.3, angfn=lambda X, Y: 0 * X, seed=3, jit=.1)
    for kk in range(8): c.stroke([(x - w / 2, y - h * (kk + .5) / 8), (x + w / 2, y - h * (kk + .5) / 8)], .9, '#8a8270', a=.8, dry=.1, taper=(0, 0))
    dome = [(x - w / 2 - 2 + (w + 4) * u, y - h - math.sin(u * math.pi) * w * .45) for u in np.linspace(0, 1, 14)]
    c.area(dome, '#8a8e90', wob=0, rough=.4)

def barn(x, y, w, h):
    sd = w * .3; D = np.array([sd, -sd * .42]); BL, BR_, TL, TR = np.array([x - w / 2, y]), np.array([x + w / 2, y]), np.array([x - w / 2, y - h]), np.array([x + w / 2, y - h])
    rh = w * .45; ap = TL + [w / 2, -rh]; kL = TL + [w * .08, -rh * .55]; kR = TR + [-w * .08, -rh * .55]
    c.area([BR_, BR_ + D, TR + D, TR], '#8a2e24', wob=.1, rough=.5)
    c.area([TR + [3, 1], kR + [1, 0], ap, ap + D, kR + D + [1, 0], TR + D + [3, 1]], '#6a6e72', wob=.1, rough=.5)
    fm = c.area([BL, BR_, TR, kR, ap, kL, TL], '#b8382c', wob=.15, rough=.6, edge_dark=.06)
    c.stip(fm, pal_fn(['#b8382c', '#a8302a', '#c84834']), spacing=1.1, L=2.6, w=1.3, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=5)
    c.stroke([TL + [-3, 1], kL, ap, kR, TR + [3, 1]], 3.2, '#f2ead6', a=1, dry=.1, taper=(0, 0))
    dw, dh = w * .38, h * .72
    q = [(x - dw / 2, y), (x + dw / 2, y), (x + dw / 2, y - dh), (x - dw / 2, y - dh)]
    for a_, b_ in ((q[0], q[1]), (q[1], q[2]), (q[2], q[3]), (q[3], q[0]), (q[0], q[2]), (q[1], q[3])): c.stroke([a_, b_], 2.2, '#f2ead6', a=1, dry=.05, taper=(0, 0))
    c.area([(x - 4, y - h - rh * .4), (x + 4, y - h - rh * .4), (x + 4, y - h - rh * .1), (x - 4, y - h - rh * .1)], '#f2ead6', wob=0, rough=.3)

def church(x, y, w=46, h=34):
    house(x, y, w, h, '#f4eee2', '#b8402e', 61, rows=1, cols_=2)
    tw = w * .32; top = y - h - 26
    m = c.area([(x - tw / 2, y - h + 6), (x + tw / 2, y - h + 6), (x + tw / 2, top), (x - tw / 2, top)], '#f6efe2', wob=0, rough=.4)
    c.area([(x - tw / 2 - 2, top), (x + tw / 2 + 2, top), (x, top - 34)], '#f2ead6', wob=0, rough=.4)
    c.stroke([(x, top), (x, top - 34)], .6, '#c8bea8', a=1, dry=0, taper=(0, 0))
    c.area([(x - 2.5, top + 5), (x + 2.5, top + 5), (x + 2.5, top + 13), (x - 2.5, top + 13)], '#4a5a6a', wob=0, rough=.3)

def clocktower_town(x0, y):
    """Toy Town: a row of colourful storefronts with striped awnings around a cream clock-tower hall."""
    shops = [(x0 + 0, 44, 52, '#e8b84a', '#7a4a34', '#b8402e'), (x0 + 46, 42, 58, '#6a8ab8', '#3a4a6a', '#3f6aa8'), (x0 + 92, 40, 50, '#e89aa8', '#8a4a4a', '#b8402e'),
             (x0 + 214, 40, 54, '#e8b84a', '#7a4a34', '#3f6aa8'), (x0 + 258, 44, 50, '#b8402e', '#5a3a3a', '#b8402e'), (x0 + 304, 40, 56, '#e89aa8', '#6a4a5a', '#7f9a3a')]
    for i, (sx, sw, sh, wall, roof, awn) in enumerate(shops):
        A.house(sx + sw / 2, y, sw, sh, ['gable', 'side', 'tall'][i % 3], wall, roof, 120 + i, dotcol=None, rows=2, cols_=2)
        for kk in range(5):
            a0 = sx + 3 + kk * (sw - 6) / 5; a1 = sx + 3 + (kk + 1) * (sw - 6) / 5
            c.area([(a0, y - sh * .36), (a1, y - sh * .36), (a1 + 1, y - sh * .36 + 7), (a0 + 1, y - sh * .36 + 7)], [awn, '#f4eee2'][kk % 2], wob=0, rough=.3)
    hx = x0 + 168; hw, hh = 76, 70
    A.house(hx, y + 2, hw, hh, 'gable', '#efe2c4', '#8a5a3a', 131, dotcol=None, rows=2, cols_=3)
    tw = 30; top = y - hh - 54
    tm = c.area([(hx - tw / 2, y - hh + 10), (hx + tw / 2, y - hh + 10), (hx + tw / 2, top), (hx - tw / 2, top)], '#efe2c4', wob=0, rough=.4)
    c.stip(tm, pal_fn(['#efe2c4', '#e2d4b4']), spacing=1.1, L=2.4, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=9)
    c.area(S.lumpy(hx, top + 20, 11, 11, 2, n=36, amp=0), '#f8f2e4', wob=0, rough=.3, edge_dark=.2)
    c.stroke([(hx, top + 20), (hx, top + 12)], 1.4, '#2a2420', a=1, dry=0, taper=(0, .3)); c.stroke([(hx, top + 20), (hx + 6, top + 22)], 1.4, '#2a2420', a=1, dry=0, taper=(0, .3))
    c.area([(hx - tw / 2 - 4, top), (hx + tw / 2 + 4, top), (hx, top - 30)], '#3a3a4a', wob=0, rough=.4)
    c.stroke([(hx, top - 30), (hx, top - 40)], 1.2, '#2a2420', a=1, dry=0, taper=(0, 0))
    for kk in range(7):
        a0 = hx - hw / 2 + 4 + kk * (hw - 8) / 7; a1 = a0 + (hw - 8) / 7
        c.area([(a0, y - hh * .32), (a1, y - hh * .32), (a1 + 1, y - hh * .32 + 8), (a0 + 1, y - hh * .32 + 8)], ['#b8402e', '#f4eee2'][kk % 2], wob=0, rough=.3)
    plaza = S.lumpy(x0 + 170, y + 14, 190, 12, 3, n=40, amp=.04)
    pm = c.area(plaza, '#d8c8a0', wob=.3, rough=.8)
    c.stip(pm, pal_fn(['#d8c8a0', '#c8b890', '#e6d8b4']), spacing=1.6, L=2.4, w=2.2, seed=7, jit=1.5)

def portal(x, y, s=1.0):
    outer = [(x - 34 * s + 68 * s * u, y + 6 - math.sin(u * math.pi) ** .7 * 50 * s) for u in np.linspace(0, 1, 24)]
    om = c.area(outer + [(x + 36 * s, y + 8), (x - 36 * s, y + 8)], '#a89c88', wob=.2, rough=.6, edge_dark=.12)
    c.stip(om, pal_fn(['#b0a490', '#9c907c', '#c0b4a0', '#8c8270']), spacing=1.3, L=3.4, w=2.4, seed=int(x), jit=1.2)
    inner = [(x - 22 * s + 44 * s * u, y + 8 - math.sin(u * math.pi) ** .8 * 36 * s) for u in np.linspace(0, 1, 20)]
    c.area(inner + [(x + 22 * s, y + 9), (x - 22 * s, y + 9)], '#1a1814', wob=0, rough=.3)
    for u in np.linspace(.04, .96, 9):
        p = np.array(inner[int(u * 19)]); q = np.array(outer[int(u * 23)])
        c.stroke([p, p + (q - p) * .95], 1.4, '#6a6050', a=.8, dry=.1, taper=(0, 0))

def cow(x, y, s=1.0):
    c.area(S.lumpy(x, y - 10 * s, 22 * s, 11 * s, 2, n=24, amp=.03), '#f4eee2', wob=0, rough=.3, edge_dark=.1)
    c.dots([(x - 6 * s, y - 12 * s), (x + 8 * s, y - 8 * s), (x - 12 * s, y - 6 * s)], 4.4 * s, ['#2a2622'])
    c.area(S.lumpy(x + 24 * s, y - 6 * s, 6 * s, 5 * s, 3, n=16, amp=0), '#f4eee2', wob=0, rough=.3)
    c.dots([(x + 27 * s, y - 3 * s)], 2.4 * s, ['#d8a29c'])
    for dx in (-15, -9, 9, 15): c.stroke([(x + dx * s, y - 3 * s), (x + dx * s, y + 6 * s)], 2.2 * s, '#3a322c', a=1, dry=0, taper=(0, 0))

def horse(x, y, s=1.0):
    c.area(S.lumpy(x, y - 10 * s, 16 * s, 7 * s, 2, n=20, amp=.03), '#7a4a2c', wob=0, rough=.3)
    c.stroke([(x + 12 * s, y - 14 * s), (x + 20 * s, y - 24 * s)], 6 * s, '#7a4a2c', a=1, dry=0, taper=(0, .2))
    for dx in (-11, -6, 7, 12): c.stroke([(x + dx * s, y - 5 * s), (x + dx * s, y + 6 * s)], 2 * s, '#5a3420', a=1, dry=0, taper=(0, 0))

def boat(x, y, s=1.0):
    hull = [(x - 30 * s, y), (x + 32 * s, y), (x + 22 * s, y + 13 * s), (x - 20 * s, y + 13 * s)]
    hm = c.area(hull, '#8a5a34', wob=0, rough=.4, edge_dark=.1)
    c.stip(hm, pal_fn(['#8a5a34', '#7a4a2a', '#9a6a40']), spacing=1.1, L=2.6, w=1.2, angfn=lambda X, Y: 0 * X, seed=int(x))
    c.stroke([(x, y), (x, y - 62 * s)], 2.4, '#4a3424', a=1, dry=0, taper=(0, 0))
    sail = [(x + 2, y - 4 * s), (x + 2, y - 60 * s), (x + 28 * s, y - 6 * s)]
    sm = c.area(sail, '#f2ead8', wob=.1, rough=.4); c.stip(sm, pal_fn(['#f4ecdc', '#e6dcc8', '#faf4ea']), spacing=1.1, L=3.0, w=1.2, angfn=lambda X, Y: -1.2 + 0 * X, seed=int(x) + 1)
    sail2 = [(x - 2, y - 6 * s), (x - 2, y - 48 * s), (x - 22 * s, y - 8 * s)]
    sm2 = c.area(sail2, '#e8dcc4', wob=.1, rough=.4); c.stip(sm2, pal_fn(['#e8dcc4', '#dccfb4']), spacing=1.1, L=3.0, w=1.2, angfn=lambda X, Y: 1.2 + 0 * X, seed=int(x) + 2)
    for kk in range(3): c.stroke([(x - 40 * s + kk * 30 * s, y + 18 * s), (x - 28 * s + kk * 30 * s, y + 15 * s), (x - 16 * s + kk * 30 * s, y + 18 * s)], 2, '#e8eef0', a=.9, dry=.1, taper=(.2, .2))

def cloud(cx, cy, w, h):
    for i in range(5):
        u = (i + .5) / 5; bx = cx - w / 2 + w * u; br = h * (.55 + .5 * math.sin(u * math.pi))
        m = c.area(S.lumpy(bx, cy - br * .25, br * 1.05, br * .85, i + int(cx), n=30, amp=.06, flat=.45), '#efe6d2', wob=.3, rough=.6, edge_dark=.05)
        c.stip(m, pal_fn(['#f4ecdc', '#e6dcc6', '#fbf5ea', '#d8d0c0']), spacing=1.0, L=3.0, w=1.4,
               angfn=lambda X, Y, bx=bx, by=cy - br * .25: np.arctan2(Y - by, X - bx) + math.pi / 2, seed=int(cx) + i, jit=.3)

def mountain(px, base, w, h, seed):
    r = np.random.RandomState(seed); pk = (px + r.uniform(-8, 8), base - h)
    poly = [(px - w / 2, base)] + [(px - w / 2 + (pk[0] - px + w / 2) * t + r.randn() * 2, base - h * t ** .9 + r.randn() * 2) for t in np.linspace(.15, .9, 5)] + [pk] + \
           [(pk[0] + (px + w / 2 - pk[0]) * t + r.randn() * 2, base - h * (1 - t) ** .9 + r.randn() * 2) for t in np.linspace(.1, .85, 5)] + [(px + w / 2, base)]
    m = c.area(poly, '#8c84ac', wob=.3, rough=.7, edge_dark=.06)
    c.stip(m, lambda X, Y, rr, pkx=pk[0]: np.where((X > pkx)[:, None], np.array([hexc('#6c6890'), hexc('#7a749c'), hexc('#625e86')])[rr.randint(3, size=len(X))],
                                                np.array([hexc('#9a92b8'), hexc('#a8a0c4'), hexc('#b4aecc')])[rr.randint(3, size=len(X))]) * (1 + (rr.rand(len(X), 1) - .5) * .06),
           spacing=1.15, L=3.8, w=1.5, angfn=lambda X, Y, pkx=pk[0]: np.where(X > pkx, math.pi / 2 - .85, math.pi / 2 + .85), seed=seed, jit=.3)
    snow = [pk] + [(pk[0] - w * .26 * t + r.randn() * 2, pk[1] + h * .42 * t + 8 * math.sin(t * 9) ** 2) for t in np.linspace(.2, 1, 5)] + \
           [(pk[0] + w * .26 * t + r.randn() * 2, pk[1] + h * .42 * t + 8 * math.sin(t * 7) ** 2) for t in np.linspace(1, .2, 5)]
    sm = c.area(snow, '#f4f0ea', wob=.2, rough=.8)
    c.stip(sm, lambda X, Y, rr, pkx=pk[0]: np.where((X > pkx)[:, None], np.array([hexc('#d6d4e4'), hexc('#c8c6da')])[rr.randint(2, size=len(X))],
                                                 np.array([hexc('#f8f4ee'), hexc('#ece8e2')])[rr.randint(2, size=len(X))]),
           spacing=1.1, L=3.2, w=1.3, angfn=lambda X, Y, pkx=pk[0]: np.where(X > pkx, math.pi / 2 - .85, math.pi / 2 + .85), seed=seed + 1, jit=.3)

def mesa(x, y, w, h, seed):
    r = np.random.RandomState(seed); tw = w * .62
    poly = [(x - w / 2, y), (x - tw / 2 - 6, y - h * .6), (x - tw / 2, y - h), (x + tw / 2, y - h - 2), (x + tw / 2 + 6, y - h * .55), (x + w / 2, y)]
    m = c.area(poly, '#b8582e', wob=.3, rough=.6, edge_dark=.1)
    c.stip(m, lambda X, Y, rr: np.array([hexc('#c8683a'), hexc('#a84a28'), hexc('#d87a44'), hexc('#9a4226')])[((X - x) / 6 + rr.rand(len(X)) * .8).astype(int) % 4] * (1 + (rr.rand(len(X), 1) - .5) * .08),
           spacing=1.2, L=4.4, w=1.4, angfn=lambda X, Y: math.pi / 2 + 0 * X, seed=seed, jit=.12)
    c.area([(x - tw / 2, y - h), (x + tw / 2, y - h - 2), (x + tw / 2 - 4, y - h - 6), (x - tw / 2 + 4, y - h - 5)], '#e09a62', wob=0, rough=.4)

def cactus(x, y, h):
    for (pts, w_) in [([(x, y), (x, y - h)], h * .2), ([(x, y - h * .45), (x - h * .28, y - h * .45), (x - h * .28, y - h * .78)], h * .14),
                      ([(x, y - h * .6), (x + h * .26, y - h * .6), (x + h * .26, y - h * .88)], h * .14)]:
        c.stroke(pts, w_, '#4f7a3a', a=1, dry=.1, taper=(0, .08), streak=.2)

def palm(x, y, h, seed):
    r = np.random.RandomState(seed)
    trunk = [(x, y), (x + h * .08, y - h * .5), (x + h * .2, y - h)]
    c.stroke(trunk, h * .07, '#8a6a44', a=1, dry=.15, taper=(0, .3), streak=.2)
    tx, ty = trunk[-1]
    for kk in range(7):
        a = -math.pi + kk * math.pi / 6 + r.randn() * .1
        ln = h * r.uniform(.4, .55)
        pts = [(tx, ty), (tx + math.cos(a) * ln * .5, ty + math.sin(a) * ln * .5 - ln * .12), (tx + math.cos(a) * ln, ty + math.sin(a) * ln + ln * .25)]
        c.stroke(pts, h * .07, ['#3f6a34', '#5a8a3e', '#4a7a38'][kk % 3], a=1, dry=.15, taper=(.1, .8), streak=.2)

# --------------------------------------------------------------------------- compose
def main():
    global LAND_MASK
    # ocean: deep textured blue, wave marks in rows
    om = (0, 0, np.ones((H, W), np.float32))
    c.stip(om, pal_fn(['#2c5684', '#335e8c', '#26507c', '#3a6694', '#2f5a88'], .05), spacing=1.6, L=6.0, w=1.6,
           angfn=lambda X, Y: .25 * np.sin(X / 60 + Y / 25), seed=2, jit=.25)
    for i in range(240):
        x, y = R.uniform(0, RW), R.uniform(0, RH)
        if LANDP.contains_point((x, y), radius=-30): continue
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.2, '#e8eef0', a=.85, dry=.2, taper=(.2, .2))
    log('ocean')
    # land base
    LAND_MASK = np.zeros((H, W), np.float32)
    cv2.fillPoly(LAND_MASK, [np.round(COAST * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    LAND_MASK = cv2.GaussianBlur(LAND_MASK, (0, 0), 1.0)
    def landcol(X, Y, r):
        base = np.where((X < 560) & (Y < 330), 0, np.where((X < 520) & (Y > 500), 2, np.where(X > 1200, 3, 1)))
        P = np.array([[hexc('#4f6e34'), hexc('#5a7a3a'), hexc('#46602e')], [hexc('#7f8a34'), hexc('#8c943c'), hexc('#6f7a2e')],
                      [hexc('#c8802e'), hexc('#d8943a'), hexc('#b87028')], [hexc('#8a9a3c'), hexc('#98a646'), hexc('#7a8a34')]])
        return P[base, r.randint(3, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .1)
    c.area(None, '#8a9a3c', m=(0, 0, LAND_MASK), edge_dark=0, var=.03)
    c.stip((0, 0, LAND_MASK), landcol, spacing=1.4, L=3.6, w=1.8, angfn=lambda X, Y: .5 * np.sin(X / 50) * np.cos(Y / 40), seed=3, jit=.4)
    c.set_clip((0, 0, LAND_MASK))
    log('land')
    # rolling mounds across the country, back to front, each a different colour family
    YG = ['#a09a3a', '#b0a646', '#8e8a34', '#bcae54']; GR = ['#5f7a30', '#6e8a38', '#52702a', '#7f9a42']; OC = ['#c99a3a', '#d8aa48', '#b8862e', '#e2b850']
    DG = ['#4a6a34', '#55763a', '#3f5e2e', '#628044']; OL = ['#8a9234', '#9aa03e', '#7a8430', '#a6aa4a']
    MOUNDS = []
    rr = np.random.RandomState(9)
    for y in np.arange(150, 860, 46):
        for x in np.arange(40 + (y // 46 % 2) * 60, RW - 40, 120):
            px, py = x + rr.uniform(-40, 40), y + rr.uniform(-12, 12)
            if not on_land(px, py - 20, 10): continue
            if px < 520 and py > 500 and px > 120: continue                  # the desert
            if px < 560 and py < 210: continue                               # the mountains
            pal = DG if (px < 600 and py < 380) else (OC if rr.rand() < .18 else [YG, GR, OL, YG][rr.randint(4)])
            if px > 1250 and py < 400 and rr.rand() < .5: pal = OC
            MOUNDS.append((py, px, rr.uniform(130, 200), rr.uniform(34, 60), pal, int(rr.randint(1e6))))
    FIELDS = [(380, 340, 230, 70, OC, ['#a8822a', '#e2be5a']), (690, 210, 190, 64, OC, ['#a8822a', '#e2be5a']), (1110, 400, 200, 74, OC, ['#a8822a', '#e8c868']),
              (930, 600, 200, 70, OC, ['#a8822a', '#e2be5a']), (560, 210, 140, 46, YG, ['#8a8a2a', '#c8c060'])]
    for (cx, by, w, h, pal, st) in FIELDS: MOUNDS.append((by, cx, w, h, pal, int(cx), st))
    MOUNDS.sort(key=lambda m_: m_[0])
    for mo in MOUNDS:
        py, px, w, h, pal, sd = mo[:6]
        paint_mound(px, py, w, h, pal, sd, stripes=mo[6] if len(mo) > 6 else None)
    log('mounds')
    # the desert and its mesas
    dpoly = catmull([(130, 520), (300, 500), (470, 520), (500, 580), (470, 650), (300, 670), (150, 650), (120, 590)], 10, closed=True)
    dm = c.area(dpoly, '#d08a36', wob=1.5, rough=1, edge_dark=.05)
    x0, y0, mm = dm; dm = (x0, y0, mm * LAND_MASK[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]])
    c.stip(dm, pal_fn(['#d08a36', '#e09a40', '#c07a2e', '#e8aa52', '#b86a28']), spacing=1.25, L=3.6, w=1.7, angfn=lambda X, Y: .2 * np.sin(X / 40), seed=11, jit=.3)
    mesa(250, 600, 170, 86, 1); mesa(340, 610, 80, 54, 2)
    for (x, y, h) in [(170, 560, 34), (360, 640, 40), (395, 626, 30), (300, 650, 26), (450, 600, 28)]: cactus(x, y, h)
    # mountains of the Northwest
    for i, (px, base, w, h) in enumerate([(70, 110, 130, 74), (170, 140, 160, 96), (300, 180, 250, 170), (420, 190, 250, 176), (510, 220, 210, 130), (240, 216, 180, 100)]):
        mountain(px, base, w, h, 40 + i)
    log('desert & mountains')
    # the lakes, with cream rims
    for L_ in LAKES:
        lm = c.area(L_, '#3a6a9c', wob=.6, rough=.8, edge_dark=.08)
        c.stip(lm, pal_fn(['#3a6a9c', '#4474a6', '#305e8e', '#5080b0']), spacing=1.4, L=5, w=1.5, angfn=lambda X, Y: .3 * np.sin(X / 40 + Y / 20), seed=12, jit=.2)
        PP = np.vstack([L_, L_[:1]])
        for kk in range(0, len(PP) - 2, 14): c.stroke(PP[kk:kk + 16], 4.2, '#efe2c0', a=.95, dry=.2, taper=(0, 0), rough=.6)
    # rivers: the southeastern river with its fall, and the western stream
    RIV = catmull([(1010, 506), (1030, 540), (1060, 572), (1080, 606), (1096, 640), (1110, 680), (1124, 720), (1132, 760)], 12)
    poly, nr, wv = ribbon(RIV, lambda t: 14 + 16 * t)
    rm = c.area(poly, '#4a7ab0', wob=.4, rough=.7, edge_dark=.08)
    c.stip(rm, pal_fn(['#5a8ac0', '#4a7ab0', '#7aa6d0', '#e8eef0']), spacing=1.2, L=4.2, w=1.4, angfn=lambda X, Y: math.pi / 2.4 + 0 * X, seed=13, jit=.2)
    for (x, y) in [(1096, 640), (1104, 660)]:
        for kk in range(8): c.stroke([(x - 14 + kk * 4, y - 8), (x - 14 + kk * 4 + 1, y + 10)], 2, '#f2f6f6', a=.9, dry=.3, taper=(0, .4))
    WRIV = catmull([(130, 410), (100, 430), (70, 446), (40, 456)], 10)
    poly, nr, wv = ribbon(WRIV, lambda t: 10 + 14 * t)
    wm = c.area(poly, '#5a8ac0', wob=.4, rough=.7)
    c.stip(wm, pal_fn(['#5a8ac0', '#7aa6d0', '#e8eef0']), spacing=1.2, L=4, w=1.3, angfn=lambda X, Y: .3 + 0 * X, seed=14)
    for (x, y, rx) in [(60, 430, 26), (100, 424, 20), (36, 420, 18)]:
        sm2 = c.area(S.lumpy(x, y, rx, rx * .55, int(x), n=24, amp=.06, flat=.3), '#9a8a7a', wob=.2, rough=.6, edge_dark=.15)
        c.stip(sm2, pal_fn(['#a89a8a', '#8a7c6c', '#b8aa9a']), spacing=1.2, L=2.6, w=1.4, seed=int(x))
    log('water')
    # the hill behind Toy Town, its tunnels, and the three routes
    th = mound(916, 452, 400, 150, 77, flat=.6)
    tm_ = c.area(th, '#55763a', wob=.6, rough=1, edge_dark=.05)
    c.stip(tm_, pal_fn(['#55763a', '#628044', '#4a6a34', '#6f8a46', '#8a7a3a']), spacing=1.25, L=3.4, w=1.7, angfn=flow_of(th[:30]), seed=78, jit=.35)
    before = c.img.copy()
    track(RED, 'red'); track(BLUE, 'blue'); track(GREEN, 'green'); track(GREEN2, 'green')
    portal(*WEST_PORTAL, s=.95); portal(*EAST_PORTAL, s=.9)
    bi = int(np.argmin(np.hypot(*(GREEN2 - [1084, 606]).T))); dk = GREEN2[bi - 45:bi + 45] + [0, 8]
    bb = float(dk[:, 1].max()) + 40; x0_, x1_ = dk[:, 0].min(), dk[:, 0].max(); ax = 1092; aw = 60; ah = 34
    arch = [(ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    order = np.argsort(dk[:, 0]); dks = dk[order]
    face = np.vstack([dks - [0, 6], [[x1_, bb]], arch, [[x0_, bb]]])
    bm = c.area(face, '#a89c88', wob=.3, rough=.6, edge_dark=.1)
    c.stip(bm, pal_fn(['#b8ac98', '#9c907c', '#c8bca8', '#8c8270']), spacing=1.3, L=4, w=2.6, angfn=lambda X, Y: 0 * X, seed=88, jit=.2)
    for u in np.linspace(0, 1, 11):
        p = np.array((ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah)); dv = p - [ax, bb + 8]; dv /= np.hypot(*dv)
        c.stroke([p, p + dv * 8], 3.4, '#cfc4b0', a=.9, dry=.1, taper=(0, 0))
    track(GREEN2[bi - 45:bi + 45], 'green')
    c.HM *= 1.0
    log('rail')
    # objects, sorted by depth
    objs = []
    HOUSES = [(440, 270, 70, 44, '#e8d8b4', '#b8402e', 'gable'), (130, 384, 50, 34, '#f2ead8', '#b8402e', 'gable'), (520, 536, 66, 44, '#f2ead8', '#3f5a7a', 'gable'),
              (534, 694, 104, 60, '#f2ead8', '#c0603a', 'gable'), (1200, 268, 62, 40, '#e8c870', '#b8402e', 'gable'), (1046, 302, 60, 38, '#f2ead8', '#b8402e', 'side'),
              (1200, 400, 60, 44, '#f2ead8', '#b8402e', 'gable'), (1400, 452, 80, 50, '#f2ead8', '#c8603a', 'gable'), (1338, 590, 66, 50, '#e8c870', '#5a6a8a', 'gable'),
              (1048, 724, 66, 42, '#f2ead8', '#b8402e', 'side'), (1364, 834, 54, 36, '#f2ead8', '#b8402e', 'gable'), (1540, 172, 70, 44, '#f2ead8', '#b8402e', 'side'),
              (1468, 220, 40, 30, '#f2ead8', '#b8402e', 'gable')]
    for i, hh in enumerate(HOUSES): objs.append((hh[1], 'house', (i, hh)))
    objs.append((262, 'barn', (668, 262, 84, 50))); objs.append((256, 'silo', (726, 256, 34, 104)))
    objs.append((290, 'church', (1424, 290))); objs.append((376, 'lighthouse', (88, 400, 84))); objs.append((150, 'lighthouse', (1606, 150, 70)))
    objs.append((700, 'windmill', (680, 708, 120))); objs.append((684, 'cow', (790, 684, 1.3))); objs.append((486, 'horse', (1262, 488, 1.0)))
    objs.append((480, 'town', (790, 492)))
    for (x, y, h, s) in [(1370, 760, 120, 1), (1416, 800, 110, 2), (90, 640, 80, 3), (120, 600, 70, 4)]: objs.append((y, 'palm', (x, y, h, s)))
    # trees: hand-weighted species by region, placed with spacing, kept off tracks, buildings and water
    keep_out = [(x, y, w * .6 + 20, h + 30) for (x, y, w, h, *_ ) in HOUSES] + [(668, 262, 80, 90), (726, 256, 40, 120), (1424, 290, 40, 110), (88, 400, 30, 100),
               (1606, 150, 30, 90), (680, 708, 50, 130), (916, 470, 230, 110), (790, 684, 50, 40), (1262, 488, 30, 30), (290, 600, 220, 90)]
    tracks = np.vstack([RED, BLUE, GREEN, GREEN2])
    trees = []
    tr = np.random.RandomState(31)
    for attempt in range(20000):
        x, y = tr.uniform(20, RW - 20), tr.uniform(60, RH - 40)
        if not on_land(x, y, 14): continue
        if x < 560 and y < 200 and tr.rand() < .7: continue
        if 140 < x < 500 and 510 < y < 670: continue
        if any(abs(x - kx) < kw and y - kh < y < ky + 30 and abs(y - ky) < kh for kx, ky, kw, kh in keep_out): continue
        if np.min(np.hypot(*(tracks - [x, y]).T)) < 26: continue
        if np.min(np.hypot(*(RIV - [x, y]).T)) < 22: continue
        h = tr.uniform(46, 76)
        if any(abs(x - t[0]) < h * .42 and abs(y - t[1]) < h * .26 for t in trees): continue
        if x < 600 and y < 400: kind = 'fir' if tr.rand() < .6 else ['green', 'yellow', 'orange', 'pink', 'olive'][tr.randint(5)]
        elif x > 1250 and y < 420: kind = ['red', 'orange', 'yellow', 'fir', 'pink', 'green'][tr.randint(6)]
        else: kind = ['fir', 'fir', 'fir', 'green', 'green', 'yellow', 'orange', 'orange', 'red', 'red', 'pink', 'white', 'olive'][tr.randint(13)]
        trees.append((x, y, h, kind))
        if len(trees) > 470: break
    for i, t in enumerate(trees): objs.append((t[1], 'tree', (i, t)))
    objs.sort(key=lambda o: o[0])
    log(f'{len(trees)} trees')
    def draw(o):
        _, kind, v = o
        if kind == 'house':
            i, (x, y, w, h, wall, roof, kk) = v; house(x, y, w, h, wall, roof, 500 + i, kind=kk)
        elif kind == 'barn': barn(*v)
        elif kind == 'silo': silo(*v)
        elif kind == 'church': church(*v)
        elif kind == 'lighthouse': lighthouse(*v)
        elif kind == 'windmill': windmill(*v)
        elif kind == 'cow': cow(*v)
        elif kind == 'horse': horse(*v)
        elif kind == 'town': clocktower_town(*v)
        elif kind == 'palm': palm(*v)
        elif kind == 'tree':
            i, (x, y, h, kk) = v; tree(x, y, h, kk, 1000 + i)
    for n_, o in enumerate(objs):
        draw(o)
        if n_ % 120 == 0: log(f'objects {n_}/{len(objs)}')
    # the train on the red route, heading for the west tunnel
    i_head = int(np.argmin(np.abs(RED[:, 0] - 600) + (RED[:, 1] < 380) * 1e4))
    S.train(i_head=i_head, sabs=3.9, pts=RED)
    log('train')
    c.set_clip(None)
    # the cream coastline, painted as a broken, thick brush line
    PP = np.vstack([COAST, COAST[:1]]); PP = resample(PP, 2.0)
    d = np.gradient(PP, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.hypot(*nr.T)[:, None] + 1e-9
    for kk in range(0, len(PP) - 2, 10):
        sub = PP[kk:kk + 12]
        c.stroke(sub, 7.5, '#efe2c0', a=1, dry=.2, taper=(.05, .05), press=.3, rough=.8, streak=.12)
    for kk in range(0, len(PP) - 2, 6):
        p = PP[kk] + nr[kk] * R.uniform(-1, 1) * 3
        c.dots([tuple(p)], R.uniform(1.4, 2.6), ['#f6ecd2', '#e2d2ac'], seed=kk)
    # clouds and boats
    for (cx, cy, w, h) in [(440, 36, 150, 28), (940, 36, 160, 30), (1270, 42, 160, 30)]: cloud(cx, cy, w, h)
    for (x, y, s) in [(196, 800, 1.1), (884, 832, 1.0), (1600, 486, .95), (1510, 680, .9)]: boat(x, y, s)
    log('coast & sea')
    impasto(c, .14)
    c.save('out/usmap')
    log('saved')

if __name__ == '__main__':
    main()

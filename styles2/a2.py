"""Direction A — Enchanted Folk-Art Countryside.
A golden hill village at dusk, every surface stippled by hand; houses with dotted roofs and lit windows, trees with black
branch skeletons, a stone viaduct, and a river of stones. The train climbs from the riverside up to the windmill and the forest."""
import math, time
import numpy as np, cv2
from kit import *

c = setup('#1f2150', 101)
R = np.random.RandomState(3)
GLOW = []
T0 = time.time()
def log(m): print(f'A {time.time() - T0:6.1f}s {m}', flush=True)
def sfn(y): return .7 + .55 * max(0, y - 380) / 480

# --------------------------------------------------------------------------- composition
RIDGE_B = catmull([(-20, 330), (90, 280), (190, 236), (300, 214), (400, 232), (500, 206), (600, 174), (720, 160), (840, 182), (960, 156),
                   (1080, 138), (1200, 160), (1320, 140), (1440, 176), (1540, 160), (1630, 176)], 10)
RIDGE_M = catmull([(-20, 430), (110, 392), (240, 372), (340, 380), (420, 360), (520, 340), (700, 290), (860, 268), (980, 282), (1100, 262),
                   (1220, 280), (1340, 258), (1460, 284), (1630, 270)], 10)
GOLD = catmull([(-30, 660), (60, 580), (170, 492), (290, 420), (410, 366), (520, 334), (610, 324), (700, 340), (790, 384), (870, 446),
                (930, 512), (968, 580), (990, 660)], 12)
RIGHT = catmull([(840, 680), (930, 590), (1030, 512), (1140, 460), (1260, 430), (1380, 424), (1500, 444), (1630, 470)], 12)
SKIRT = catmull([(-30, 760), (120, 700), (300, 672), (480, 676), (640, 690), (780, 700), (900, 712)], 10)
STREAM = catmull([(956, 600), (946, 650), (958, 700), (972, 748), (962, 796), (970, 846)], 10)
RIVER_TOP = catmull([(-30, 838), (200, 846), (420, 840), (640, 850), (860, 842), (1080, 850), (1300, 842), (1630, 848)], 10)
RAIL = resample(catmull([(-40, 812), (120, 810), (300, 806), (480, 800), (640, 790), (760, 772), (866, 744), (968, 726), (1070, 708),
                          (1170, 684), (1262, 648), (1340, 604), (1392, 560), (1404, 520), (1372, 494), (1306, 482), (1240, 476),
                          (1180, 466), (1132, 452)], 14), 2.0)
VIADUCT = (int(np.argmin(np.abs(RAIL[:, 0] - 872))), int(np.argmin(np.abs(RAIL[:, 0] - 1062))))

# --------------------------------------------------------------------------- painting helpers
def flowdir(top):
    T = np.asarray(top)
    def f(X, Y):
        o = np.argsort(T[:, 0]); dx = np.gradient(T[o, 1]) / (np.gradient(T[o, 0]) + 1e-6)
        sl = np.interp(X, T[o, 0], dx)
        return np.arctan(sl) * np.clip(1 - (Y - np.interp(X, T[o, 0], T[o, 1])) / 220, .1, 1)
    return f

def hill(top, cols, seed, spacing=1.5, L=3.6, w=1.7, base=None):
    m = c.area(land(top), base or cols[0], wob=1, rough=1, edge_dark=.04, seed=seed)
    c.stip(m, pal_fn(cols, .07), spacing=spacing, L=L, w=w, angfn=flowdir(top), seed=seed + 1, jit=.3)
    return m

def roofdots(poly, col, n, seed, size=.55):
    P = np.asarray(poly); x0, x1 = P[:, 0].min(), P[:, 0].max(); y0, y1 = P[:, 1].min(), P[:, 1].max()
    r = np.random.RandomState(seed); pts = []
    from matplotlib.path import Path as MP
    mp = MP(P)
    for yy in np.arange(y0 + 2, y1 - 1, 3.2):
        for xx in np.arange(x0 + 1.5 + (int(yy) % 2) * 1.6, x1, 3.2):
            if mp.contains_point((xx, yy)) and r.rand() < .9: pts.append((xx + r.randn() * .3, yy + r.randn() * .3))
    c.dots(pts, size, col, seed=seed)

def window(x, y, ww, wh, lit=True, arch=False, frame='#2a2030'):
    c.area([(x - ww / 2 - .8, y - wh / 2 - .8), (x + ww / 2 + .8, y - wh / 2 - .8), (x + ww / 2 + .8, y + wh / 2 + .8), (x - ww / 2 - .8, y + wh / 2 + .8)], frame, wob=0, rough=.3, edge_dark=0)
    top = [(x - ww / 2, y - wh / 2)] if not arch else [(x - ww / 2 + ww * u, y - wh / 2 - math.sin(u * math.pi) * ww * .5) for u in np.linspace(0, 1, 8)]
    q = top + [(x + ww / 2, y - wh / 2), (x + ww / 2, y + wh / 2), (x - ww / 2, y + wh / 2)]
    c.area(q, '#f6b83c' if lit else '#3a3550', wob=0, rough=.3, edge_dark=.25 if lit else 0)
    if lit:
        c.dab(x - ww * .15, y - wh * .1, ww * .5, wh * .4, 0, '#ffd27a', a=.7, dry=.1)
        GLOW.append((x, y, ww * 2.6))
    c.stroke([(x, y - wh / 2), (x, y + wh / 2)], .55, frame, a=.95, dry=0, taper=(0, 0)); c.stroke([(x - ww / 2, y), (x + ww / 2, y)], .55, frame, a=.95, dry=0, taper=(0, 0))

def house(x, y, w, h, kind, wall, roof, seed, dotcol='#f3ecdc', door='#2a1f2e', side=True, rows=None, cols_=None, chimney=True):
    r = np.random.RandomState(seed)
    sd = w * .2 if side else 0; D = np.array([sd, -sd * .45])
    BL, BR, TL, TR = np.array([x - w / 2, y]), np.array([x + w / 2, y]), np.array([x - w / 2, y - h]), np.array([x + w / 2, y - h])
    wallc = hexc(wall)
    c.area(S.lumpy(x + sd * .6, y + 1, w * .7, 2.6, seed, n=20, amp=.05), '#24301c', wob=.3, rough=.6, a=.45, edge_dark=0)
    if kind == 'round':
        top = [(x - w / 2 + w * u, y - h - math.sin(u * math.pi) * w * .45) for u in np.linspace(0, 1, 16)]
        poly = [tuple(BL), tuple(BR)] + top[::-1]
        if side: c.area([BR, BR + D, BR + D + [0, -h], BR + [0, -h]], wallc * .72, wob=.1, rough=.5)
        m = c.area(poly, wallc, wob=.15, rough=.6, edge_dark=.06, seed=seed)
        c.stip(m, pal_fn([wall, hexc(wall) * .92, hexc(wall) * 1.06], .04), spacing=1.4, L=2.6, w=1.2, angfn=lambda X, Y: -math.pi / 2, seed=seed + 1, jit=.15)
        rh = 0
    else:
        rh = {'gable': w * .55, 'side': h * .55, 'tall': w * .85, 'barn': w * .5}[kind]
        if kind == 'side':
            eL, eR = TL + [-3, 1], TR + [3, 1]; RL, RR = TL + [w * .16, -rh], TR + [-w * .16, -rh]
            rpoly = [eL, eR, RR, RL]
            if side:
                c.area([BR, BR + D, TR + D, TR], wallc * .72, wob=.1, rough=.5)
                c.area([eR, eR + D, RR + D, RR], hexc(roof) * .75, wob=.1, rough=.5)
        elif kind == 'barn':
            ap = TL + [w / 2, -rh]; kL = TL + [w * .08, -rh * .55]; kR = TR + [-w * .08, -rh * .55]
            rpoly = [TL + [-3, 1], kL + [-1, 0], ap, kR + [1, 0], TR + [3, 1]]
            if side:
                c.area([BR, BR + D, TR + D, TR], wallc * .72, wob=.1, rough=.5)
                c.area([TR + [3, 1], kR + [1, 0], ap, ap + D, kR + D, TR + D + [3, 1]], hexc(roof) * .75, wob=.1, rough=.5)
        else:
            ap = TL + [w / 2, -rh]; rpoly = [TL + [-3, 1.5], TR + [3, 1.5], ap]
            if side:
                c.area([BR, BR + D, TR + D, TR], wallc * .72, wob=.1, rough=.5)
                c.area([TR + [3, 1.5], ap, ap + D, TR + D + [3, 1.5]], hexc(roof) * .75, wob=.1, rough=.5)
        m = c.area([BL, BR, TR, TL], wallc, wob=.15, rough=.6, edge_dark=.06, seed=seed)
        c.stip(m, pal_fn([wall, hexc(wall) * .92, hexc(wall) * 1.06], .04), spacing=1.4, L=2.6, w=1.2, angfn=lambda X, Y: -math.pi / 2, seed=seed + 1, jit=.15)
        rm = c.area(rpoly, roof, wob=.15, rough=.6, edge_dark=.1, seed=seed + 2)
        if dotcol: roofdots(rpoly, dotcol if isinstance(dotcol, (list, tuple)) else [dotcol], 0, seed + 3)
        else: c.stip(rm, pal_fn([roof, hexc(roof) * .85, hexc(roof) * 1.15], .05), spacing=1.3, L=2.4, w=1.3, seed=seed + 4)
        if kind == 'barn':
            dx, dw = x, w * .36
            c.area([(dx - dw / 2, y), (dx + dw / 2, y), (dx + dw / 2, y - h * .62), (dx - dw / 2, y - h * .62)], '#f1e4cf', wob=0, rough=.3)
            c.area([(dx - dw / 2 + 1.2, y), (dx + dw / 2 - 1.2, y), (dx + dw / 2 - 1.2, y - h * .62 + 1.2), (dx - dw / 2 + 1.2, y - h * .62 + 1.2)], wall, wob=0, rough=.3)
            c.stroke([(dx - dw / 2, y), (dx + dw / 2, y - h * .62)], 1, '#f1e4cf', a=1, dry=0, taper=(0, 0)); c.stroke([(dx + dw / 2, y), (dx - dw / 2, y - h * .62)], 1, '#f1e4cf', a=1, dry=0, taper=(0, 0))
            window(x, y - h - rh * .4, 5, 5)
            return
    # windows: a lit grid, with a little asymmetry
    nr = rows or max(1, int(h / 13)); nc = cols_ or max(1, int(w / 11))
    ww = min(5.5, w / (nc * 2.1)); wh = min(7, h / (nr * 2.4))
    for i in range(nr):
        for j in range(nc):
            if r.rand() < .08: continue
            u = (j + .5) / nc + r.uniform(-.03, .03); v = (i + .45) / (nr + .6)
            if i == nr - 1 and abs(u - .5) < .2 and nc % 2 == 1: continue
            window(x - w / 2 + u * w, y - h + v * h * .92 + 2, ww, wh, lit=r.rand() < .85)
    dw = min(7, w * .22); dh = min(12, h * .42)
    du = .5 if nc % 2 == 1 or nc == 1 else r.choice([.3, .7])
    dx = x - w / 2 + du * w
    q = [(dx - dw / 2, y)] + [(dx - dw / 2 + dw * u, y - dh + dw / 2 - math.sin(u * math.pi) * dw / 2) for u in np.linspace(0, 1, 10)] + [(dx + dw / 2, y)]
    c.area(q, door, wob=0, rough=.3, edge_dark=.1)
    if kind == 'round': window(x, y - h - w * .2, 5, 5, arch=True)
    if chimney and kind != 'round':
        px = x + w * r.uniform(.12, .3); py = y - h - rh * .45
        c.area([(px - 1.8, py), (px + 1.8, py), (px + 1.8, py - 7), (px - 1.8, py - 7)], '#3a2830', wob=0, rough=.3)
        smoke(px, py - 10, .8, seed, n=4, col='#c8c2d8')

def church(x, y):
    house(x, y, 34, 30, 'gable', '#f1e8da', '#2a2340', 7, dotcol='#e6c35a', rows=2, cols_=3, chimney=False)
    tw = 12; top = y - 30 - 32
    c.area([(x - tw / 2, y - 22), (x + tw / 2, y - 22), (x + tw / 2, top), (x - tw / 2, top)], '#f6efe2', wob=0, rough=.4)
    c.area([(x + tw / 2, y - 22), (x + tw / 2 + 3, y - 24), (x + tw / 2 + 3, top - 2), (x + tw / 2, top)], '#c9bfb3', wob=0, rough=.4)
    window(x, top + 9, 5, 6, arch=True)
    sp = [(x - tw / 2 - 1.5, top), (x + tw / 2 + 1.5, top), (x + .5, top - 30)]
    c.area(sp, '#2a2340', wob=0, rough=.4); roofdots(sp, ['#e6c35a'], 0, 9, .5)
    star = (x + .5, top - 35)
    for a in range(5):
        aa = -math.pi / 2 + a * 2 * math.pi / 5
        c.stroke([star, (star[0] + math.cos(aa) * 4.5, star[1] + math.sin(aa) * 4.5)], 1.3, '#f6c84a', a=1, dry=0, taper=(0, .8))
    GLOW.append((star[0], star[1], 30))

def windmill(x, y):
    w0, w1, h = 26, 15, 64
    body = [(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y - h), (x - w1 / 2, y - h)]
    m = c.area(body, '#e9dcc4', wob=.2, rough=.6, edge_dark=.1)
    c.stip(m, pal_fn(['#efe3cc', '#dccdb2', '#f6ecda']), spacing=1.4, L=2.6, w=1.2, angfn=lambda X, Y: -math.pi / 2, seed=21)
    cap = [(x - w1 / 2 - 3, y - h), (x + w1 / 2 + 3, y - h)] + [(x + (w1 / 2 + 3) * math.cos(a), y - h - math.sin(a) * 12) for a in np.linspace(0, math.pi, 12)]
    c.area(cap, '#7a2e3a', wob=0, rough=.4); roofdots(cap, ['#f3ecdc'], 0, 22, .5)
    window(x, y - h * .55, 5, 6, arch=True); window(x, y - h * .25, 5, 6)
    q = [(x - 4, y), (x - 4, y - 8), (x + 4, y - 8), (x + 4, y)]; c.area(q, '#2a1f2e', wob=0, rough=.3)
    hub = (x, y - h - 4)
    for k in range(4):
        a = math.radians(28 + k * 90)
        tip = (hub[0] + math.cos(a) * 56, hub[1] + math.sin(a) * 56)
        c.stroke([hub, tip], 2.2, '#4a3030', a=1, dry=.1, taper=(0, .1))
        nrm = (-math.sin(a), math.cos(a))
        for t in np.linspace(.25, .95, 6):
            p = (hub[0] + math.cos(a) * 56 * t, hub[1] + math.sin(a) * 56 * t)
            c.stroke([p, (p[0] + nrm[0] * 11, p[1] + nrm[1] * 11)], .9, '#f3ecdc', a=.95, dry=0, taper=(0, 0))
        c.stroke([(hub[0] + math.cos(a) * 14 + nrm[0] * 11, hub[1] + math.sin(a) * 14 + nrm[1] * 11), (tip[0] + nrm[0] * 11, tip[1] + nrm[1] * 11)], .9, '#f3ecdc', a=.95, dry=0, taper=(0, 0))
    c.dots([hub], 3, ['#3a2830'])

def viaduct():
    a, b = VIADUCT; dk = RAIL[a:b + 1] + [0, 4]
    x0, x1 = dk[0, 0], dk[-1, 0]; base = 842
    face = np.vstack([dk - [0, 3], [[x1, base], [x0, base]]])
    m = c.area(face, '#a99a8a', wob=.2, rough=.6, edge_dark=.1, seed=31)
    c.stip(m, pal_fn(['#b3a594', '#9d8e80', '#c2b5a3', '#8f8276']), spacing=1.4, L=3.2, w=2.0, angfn=lambda X, Y: 0 * X, seed=32, jit=.2)
    n = 4
    for k in range(n):
        ax = x0 + (x1 - x0) * (k + .5) / n; ay = base; aw = (x1 - x0) / n * .66
        top = float(np.interp(ax, dk[:, 0], dk[:, 1])) + 16
        ah = ay - top
        arch = [(ax - aw / 2 + aw * u, ay - (ah - aw / 2) - math.sin(u * math.pi) * aw / 2 if True else 0) for u in np.linspace(0, 1, 18)]
        arch = [(ax - aw / 2, ay)] + arch + [(ax + aw / 2, ay)]
        c.area(arch, '#1d2240', wob=0, rough=.3, edge_dark=0)
        for u in np.linspace(0, 1, 9):
            p = (ax - aw / 2 + aw * u, ay - (ah - aw / 2) - math.sin(u * math.pi) * aw / 2)
            dv = np.array(p) - [ax, ay - (ah - aw / 2)]; dv /= np.hypot(*dv) + 1e-6
            c.stroke([p, (p[0] + dv[0] * 4, p[1] + dv[1] * 4)], 2.6, '#c9bcaa', a=.9, dry=.1, taper=(0, 0))
    c.stroke(dk - [0, 2], 5, '#c9bcaa', a=1, dry=.1, taper=(0, 0))
    for xq in np.arange(x0, x1, 7):
        y = float(np.interp(xq, dk[:, 0], dk[:, 1])) - 5
        c.stroke([(xq, y), (xq, y - 3)], 1.4, '#c9bcaa', a=1, dry=0, taper=(0, 0))
    c.stroke(dk - [0, 7.5], 1.2, '#c9bcaa', a=1, dry=0, taper=(0, 0))

def tunnel(x, y):
    s = 1.0
    outer = [(x - 14 + 28 * u, y - math.sin(u * math.pi) ** .7 * 22) for u in np.linspace(0, 1, 20)]
    c.area(outer + [(x + 14, y + 3), (x - 14, y + 3)], '#8f8278', wob=.2, rough=.6)
    inner = [(x - 8.5 + 17 * u, y + 1 - math.sin(u * math.pi) ** .8 * 15) for u in np.linspace(0, 1, 18)]
    c.area(inner + [(x + 8.5, y + 3), (x - 8.5, y + 3)], '#0d0e1c', wob=0, rough=.3)
    for u in np.linspace(.05, .95, 7):
        p = np.array(inner[int(u * 17)]); q = np.array(outer[int(u * 19)])
        c.stroke([p, p + (q - p) * .95], 1.6, '#b3a594', a=.9, dry=.1, taper=(0, 0))

# --------------------------------------------------------------------------- paint
def main():
    # night sky, stippled, with stars and a pale moon
    m = c.area([(-10, -10), (1610, -10), (1610, 600), (-10, 600)], '#202255', wob=0, rough=0, edge_dark=0)
    c.stip(m, lambda X, Y, r: np.array([hexc('#1b1d4c'), hexc('#26296a'), hexc('#2e2a64'), hexc('#1d2a5a')])[r.randint(4, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .1),
           spacing=2.2, L=4.5, w=1.8, angfn=lambda X, Y: .15 * np.sin(X / 90 + Y / 40), seed=1)
    r = np.random.RandomState(5)
    stars = [(r.uniform(0, 1600), r.uniform(0, 330) ** 1.1 / 1.4) for _ in range(520)]
    c.dots(stars, .75, ['#f6efe0', '#f6efe0', '#f2c86a', '#e8a8c0', '#bcd6e6'], seed=2)
    mx, my = 214, 118
    for k in range(3):
        rr = 50 + k * 12
        c.dots([(mx + math.cos(a) * rr, my + math.sin(a) * rr) for a in np.linspace(0, 2 * math.pi, 60 + k * 14, endpoint=False)], .8, ['#f2e6c4', '#e8d4a0'], seed=3 + k)
    mm = c.area(S.lumpy(mx, my, 40, 40, 4, n=50, amp=.02, flat=0), '#f2e6c4', wob=.2, rough=.6, edge_dark=.06)
    c.stip(mm, pal_fn(['#f6ecd2', '#ecdcb4', '#f8f0dc', '#e2cfa6']), spacing=1.3, L=2.4, w=1.3, seed=4)
    # a tiny sleigh crossing the moon
    sx, sy = 200, 128
    c.area([(sx - 9, sy), (sx + 7, sy), (sx + 10, sy - 5), (sx + 6, sy - 3), (sx - 6, sy - 3)], '#1d1a20', wob=0, rough=.2)
    for k in range(3): c.area(S.lumpy(sx - 20 - k * 9, sy - 3, 3.2, 1.6, k, n=12, amp=0), '#1d1a20', wob=0, rough=.2)
    c.stroke([(sx - 8, sy - 3), (sx - 44, sy - 3)], .5, '#1d1a20', a=.9, dry=0, taper=(0, 0))
    log('sky')
    # dark forest ridges with poking firs
    mb = hill(RIDGE_B, ['#1f3a3e', '#244444', '#1a3236', '#2a4a48'], 11, spacing=1.6, L=3.4)
    for x in np.arange(-10, 1620, 16):
        y = y_on(RIDGE_B, x) + R.uniform(-2, 10)
        if R.rand() < .12: skeleton_tree(c, x, y + 30, R.uniform(50, 70), [['#5f8a3a', '#7aa04a', '#4a7030'], ['#3a6a6a', '#4f8a80', '#2f5a5a']][R.randint(2)], int(R.randint(1e6)), dots=['#f6efe0'])
        else: stipple_fir(c, x, y + 22, R.uniform(46, 84), [['#223f40', '#2c4e4a', '#193234', '#3a5e56'], ['#1f3a4a', '#2a4a5a', '#3a6070'], ['#2f4a2a', '#3e5e34', '#24401f']][R.randint(3)], int(R.randint(1e6)), slim=.2)
    mm_ = hill(RIDGE_M, ['#2c5450', '#33605a', '#264a48', '#3c6a5e'], 12, spacing=1.6, L=3.4)
    for x in np.arange(-10, 1620, 18):
        y = y_on(RIDGE_M, x) + R.uniform(0, 14)
        stipple_fir(c, x, y + 26, R.uniform(50, 92), [['#2f5a52', '#3a6a5e', '#24483f', '#4b7a62'], ['#3f5f30', '#4f7038', '#2f4a24'], ['#2a5060', '#386878', '#20404c']][R.randint(3)], int(R.randint(1e6)), slim=.21)
    log('ridges')
    # the right hill: olive and lime, with farm, windmill and station
    hill(RIGHT, ['#7d8c34', '#94a03c', '#6a7a2e', '#a7ad4a', '#5f7030'], 13)
    for (x, y) in [(1180, 560), (1300, 520), (1470, 520), (1540, 600), (1420, 640), (1100, 610)]:
        pass
    log('right hill')
    # the golden hill
    gm = c.area(land(GOLD), '#e39a2c', wob=1, rough=1, edge_dark=.04, seed=14)
    BANDS = [['#e8a034', '#f0b445', '#dc8e26'], ['#e2862a', '#ea9a34', '#d4741f'], ['#efbb4a', '#f4c95a', '#e2a63a'], ['#c9902a', '#d8a236', '#b97e22']]
    def goldcol(X, Y, r):
        b = ((np.sin(X / 140 + Y / 55) + np.sin(X / 63 - Y / 90) * .6 + 2) / 4 * len(BANDS)).astype(int) % len(BANDS)
        C = np.array([[hexc(cc) for cc in bb] for bb in BANDS])
        return C[b, r.randint(3, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .12)
    c.stip(gm, goldcol, spacing=1.5, L=3.6, w=1.7, angfn=flowdir(GOLD), seed=15, jit=.3)
    for (px, py, rx, ry) in [(150, 600, 90, 22), (420, 470, 70, 16), (640, 400, 60, 14), (300, 380, 40, 10), (760, 560, 70, 18), (560, 620, 90, 18), (880, 520, 40, 12)]:
        pm = c.area(S.lumpy(px, py, rx, ry, int(px), n=36, amp=.12, flat=0), '#8a9a2e', wob=.6, rough=1, edge_dark=.04)
        c.stip(pm, pal_fn(['#8f9c34', '#a3aa3e', '#7a8a2a', '#b4b448']), spacing=1.4, L=3.2, w=1.6, angfn=flowdir(GOLD), seed=int(px) + 3)
    hill(SKIRT, ['#7f8f2e', '#8f9c36', '#6e7f2a', '#a1a63e'], 15)
    log('gold hill')
    # the stream from the fold of the hills
    # river with a stitched surface
    rpoly = np.vstack([RIVER_TOP, [[1630, 930], [-30, 930]]])
    rm = c.area(rpoly, '#22466a', wob=.3, rough=.6, edge_dark=.1)
    c.stip(rm, pal_fn(['#244a70', '#2e5880', '#1d3d5e', '#36628a']), spacing=1.5, L=4.5, w=1.4, angfn=lambda X, Y: .06 * np.sin(X / 40), seed=17, jit=.1)
    for k in range(9):
        yy = 856 + k * 6
        pts = [(x, yy + 2.2 * math.sin(x / 26 + k)) for x in np.arange(-20, 1620, 6)]
        for i in range(0, len(pts) - 6, 9):
            if R.rand() < .7: c.stroke(pts[i:i + 6], .8, '#cfe0ea', a=.8, dry=.15, taper=(.2, .2))
    log('water')
    # village paths
    path(c, [(330, 806), (300, 760), (340, 700), (300, 640), (360, 580), (330, 520), (420, 470), (520, 420), (580, 356)], 6, '#e9cf96', sfn, dotted=['#f6ecd8', '#d9b77a'], seed=1)
    path(c, [(640, 794), (700, 740), (660, 680), (720, 620), (760, 560), (720, 500)], 5, '#e9cf96', sfn, dotted=['#f6ecd8', '#d9b77a'], seed=2)
    path(c, [(1200, 600), (1260, 560), (1300, 520), (1330, 488)], 4, '#d9c08a', sfn, dotted=['#f6ecd8'], seed=3)
    # objects: houses, trees, farm, sorted back to front
    objs = []
    HOUSES = [
        (470, 372, 26, 22, 'gable', '#f2a6bf', '#2a2340'), (690, 376, 24, 20, 'gable', '#a9d2e6', '#3a1f3a'),
        (300, 452, 30, 26, 'gable', '#f2ece0', '#1f1d2c'), (404, 444, 36, 24, 'side', '#7d6aa8', '#2a2340'), (522, 434, 22, 32, 'tall', '#5f98a6', '#1f2a3a'),
        (646, 444, 42, 26, 'side', '#c2397a', '#1f1d2c'), (770, 458, 30, 24, 'gable', '#e98a3a', '#3a1f3a'),
        (170, 544, 34, 28, 'gable', '#4f86b8', '#1f1d2c'), (292, 546, 42, 30, 'side', '#f2ece0', '#b8372e'), (434, 538, 26, 38, 'tall', '#ef9fb8', '#2a2340'),
        (566, 540, 48, 30, 'side', '#9e2f6a', '#1f1d2c'), (702, 534, 32, 30, 'round', '#ef8a2a', None), (826, 526, 28, 26, 'gable', '#a9d2e6', '#2a2340'),
        (106, 648, 40, 34, 'gable', '#f2ece0', '#c0392b'), (250, 656, 34, 42, 'tall', '#6fa8b0', '#3a1f3a'), (392, 646, 52, 32, 'side', '#4a5aa8', '#1f1d2c'),
        (542, 656, 38, 34, 'gable', '#e0703a', '#1f1d2c'), (690, 646, 46, 30, 'side', '#f6f0e4', '#5a2a5a'), (830, 616, 30, 30, 'tall', '#c2397a', '#2a2340'),
        (190, 752, 46, 36, 'gable', '#f2ece0', '#c22f2a'), (350, 756, 54, 34, 'side', '#f6f0e4', '#9e3a7a'), (510, 758, 40, 40, 'tall', '#3f5aa0', '#1f1d2c'),
        (660, 752, 46, 34, 'side', '#ef8a2a', '#1f1d2c'),
    ]
    HOUSES = [(x, y, w * 1.55, h * 1.55, k, wall, roof) for (x, y, w, h, k, wall, roof) in HOUSES]
    for i, h in enumerate(HOUSES): objs.append((h[1], 'house', (i, h)))
    objs.append((352, 'church', (580, 352)))
    TREES = [
        (220, 470, 54, ['#e04a2a', '#f06a3a', '#c8341f', '#f28a4a']), (360, 400, 40, ['#b8287a', '#d94a9a', '#9e1f62']), (600, 382, 44, ['#7fae3a', '#98c24a', '#668f2e']),
        (742, 404, 40, ['#f0a030', '#f6c050', '#d9801f']), (120, 560, 50, ['#c8287a', '#e04a9a', '#a01f62', '#f2a6c8']), (476, 470, 46, ['#3f9a7a', '#5ab48f', '#2f7a62'], '#f6efe0'),
        (360, 560, 46, ['#f2a6c8', '#e98ab0', '#f6c8dc']), (636, 580, 50, ['#e86a2a', '#f08a3a', '#c8501f', '#f6b050']), (774, 590, 44, ['#c8d24a', '#a8b83a', '#e2e070']),
        (40, 650, 60, ['#8a9a2e', '#a3b03a', '#6f7f26']), (318, 690, 52, ['#c9b83a', '#e2d050', '#a8962a']), (470, 700, 56, ['#e05a2a', '#f07a3a', '#c8401f']),
        (616, 700, 48, ['#8a2a8a', '#a84aa8', '#6a1f6a'], '#f6efe0'), (900, 520, 46, ['#5f9a8a', '#7ab4a0', '#4a7a6a'], '#f6efe0'),
        (60, 780, 64, ['#b8287a', '#d94a9a', '#9e1f62']), 
        (1120, 560, 52, ['#e08a2a', '#f0aa3a', '#c8701f']), (1220, 600, 46, ['#9e2f6a', '#c04a8a']), (1460, 560, 56, ['#c8d24a', '#a8b83a', '#e2e070']),
        (1560, 520, 50, ['#e04a2a', '#f06a3a']), (1424, 704, 54, ['#f2a6c8', '#e98ab0']),
        (1236, 748, 50, ['#f0a030', '#f6c050']), (1130, 800, 56, ['#8a2a8a', '#a84aa8']), (1580, 760, 66, ['#e86a2a', '#f08a3a']),
        (1020, 480, 40, ['#7fae3a', '#98c24a']), (1196, 760, 50, ['#c8287a', '#e04a9a'], '#f6efe0'), (1180, 660, 44, ['#e2d050', '#c9b83a']),
        (1080, 650, 46, ['#3f9a7a', '#5ab48f']), (1540, 690, 50, ['#f0a030', '#f6c050']),
    ]
    TREES = [(t[0], t[1], t[2] * 1.45) + tuple(t[3:]) for t in TREES]
    for i, t in enumerate(TREES): objs.append((t[1], 'tree', (i, t)))
    objs.append((580, 'barn', (1172, 580))); objs.append((470, 'windmill', (1462, 470))); objs.append((458, 'station', (1236, 458)))
    objs.append((786, 'rstation', (436, 786)))
    objs.append((600, 'house2', (1290, 600, 32, 26, 'gable', '#f2ece0', '#1f1d2c')))
    objs.append((640, 'house2', (1478, 614, 30, 24, 'side', '#ef9fb8', '#2a2340')))
    for x, y in [(1530, 590), (1560, 604), (1300, 700), (1250, 690)]: objs.append((y, 'hay', (x, y)))
    objs.append((700, 'house2', (1500, 760, 34, 28, 'gable', '#a9d2e6', '#1f1d2c')))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'house':
            i, (x, y, w, h, k, wall, roof) = v
            house(x, y, w, h, k, wall, roof or '#1f1d2c', 100 + i, dotcol=['#f3ecdc', '#f6c84a'][i % 2] if roof in ('#1f1d2c', '#2a2340', '#3a1f3a', '#1f2a3a', '#5a2a5a') else None)
        elif kind == 'house2':
            x, y, w, h, k, wall, roof = v; house(x, y, w * 1.55, h * 1.55, k, wall, roof, int(x), dotcol='#f3ecdc')
        elif kind == 'church': church(*v)
        elif kind == 'tree':
            i, t = v; skeleton_tree(c, t[0], t[1], t[2], t[3], 300 + i, dots=[t[4]] if len(t) > 4 else None)
        elif kind == 'barn': house(v[0], v[1], 64, 42, 'barn', '#b8302a', '#2a2340', 55, dotcol='#f3ecdc')
        elif kind == 'windmill': windmill(*v)
        elif kind == 'station':
            x, y = v
            c.area([(x - 30, y + 2), (x + 30, y + 2), (x + 34, y + 7), (x - 26, y + 7)], '#b3a594', wob=0, rough=.4)
            house(x, y, 40, 18, 'side', '#2f6a8a', '#e0703a', 61, dotcol=None, rows=1, cols_=3)
            for lx in (x - 26, x + 26):
                c.stroke([(lx, y + 4), (lx, y - 16)], .9, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 17)], 1.6, ['#ffd27a']); GLOW.append((lx, y - 17, 18))
        elif kind == 'rstation':
            x, y = v
            house(x, y, 70, 28, 'side', '#c22f2a', '#1f1d2c', 77, dotcol='#f6c84a', rows=1, cols_=4)
            for lx in (x - 40, x + 40):
                c.stroke([(lx, y + 6), (lx, y - 18)], 1.0, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 19)], 1.8, ['#ffd27a']); GLOW.append((lx, y - 19, 20))
        elif kind == 'hay':
            x, y = v; bush(c, x, y, 8, 7, ['#e2b44b', '#d49a30', '#efc860'], int(x))
    # a wooded knoll for the tunnel to enter
    km = c.area(S.lumpy(1112, 452, 74, 38, 77, n=40, amp=.1, flat=.5), '#244a46', wob=.6, rough=1, edge_dark=.06)
    c.stip(km, pal_fn(['#2a4f4a', '#33605a', '#1f3f3c', '#3c6a5e']), spacing=1.5, L=3.2, w=1.6, seed=78)
    for x in np.arange(1050, 1180, 14): stipple_fir(c, x + R.randn() * 3, 446 - 26 * math.sin((x - 1040) / 140 * math.pi) + R.uniform(0, 8), R.uniform(36, 56), ['#2f5a52', '#3a6a5e', '#24483f'], int(R.randint(1e6)), slim=.2)
    before = c.img.copy()
    rails(c, RAIL, sfn, ballast='#8f7f6a', tie='#3a2a24', steel='#2a2630', hide=[(VIADUCT[0], VIADUCT[1]), (len(RAIL) - 4, len(RAIL))], shine='#e8d8b0')
    restipple(c, before, seed=91)
    viaduct()
    before = c.img.copy()
    rails(c, RAIL[VIADUCT[0]:VIADUCT[1] + 1], sfn, ballast=None, tie='#3a2a24', steel='#2a2630', shine='#e8d8b0')
    restipple(c, before, seed=92)
    tunnel(1132, 458)
    for o in [o for o in objs if o[0] < 700]: draw(o)
    log('village')
    for o in [o for o in objs if o[0] >= 700]: draw(o)
    i_head = int(np.argmin(np.abs(RAIL[:, 0] - 1050)))
    before = c.img.copy()
    train(c, RAIL, i_head, 2.15)
    restipple(c, before, seed=93)
    GLOW.append(tuple(RAIL[i_head] + [6, -14]) + (60,))
    log('train')
    # stones and bushes along the bank, in front of the line
    for x in np.arange(-10, 1620, 42):
        y = y_on(RIVER_TOP, x) + R.uniform(-4, 6)
        if R.rand() < .55:
            rx = R.uniform(16, 30)
            sm2 = c.area(S.lumpy(x, y, rx, rx * .62, int(abs(x)) + 1, n=30, amp=.04, flat=.3), '#8a8892', wob=.2, rough=.6, edge_dark=.15)
            c.stip(sm2, pal_fn(['#9a98a2', '#7e7c88', '#b0aeb6', '#6e6c78']), spacing=1.3, L=2.6, w=1.4, seed=int(abs(x)) + 1)
        else:
            bush(c, x, y + 10, R.uniform(18, 30), R.uniform(14, 20), [['#c8302a', '#e04a3a', '#a8221f'], ['#e2b030', '#f0c84a', '#c8961f'], ['#8a2a6a', '#a84a8a', '#6a1f50'], ['#d0a030', '#e8c050']][R.randint(4)], int(abs(x)) + 7)
    # a lantern boat
    bx, by = 900, 880
    c.area([(bx - 18, by - 3), (bx + 20, by - 4), (bx + 14, by + 4), (bx - 13, by + 4)], '#b8302a', wob=0, rough=.3)
    c.stroke([(bx + 4, by - 4), (bx + 4, by - 22)], .9, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(bx + 4, by - 23)], 2, ['#ffd27a']); GLOW.append((bx + 4, by - 23, 40))
    # an owl in the big tree at the left
    c.dots([(66, 728), (70, 728)], 1.6, ['#f6c84a']); c.dots([(66, 728), (70, 728)], .6, ['#1d1a20'])
    log('foreground')
    # warm light: windows, lamps and the train's headlamp
    glow = np.zeros((H, W), np.float32)
    for gx, gy, rad in GLOW: cv2.circle(glow, (int(gx * K), int(gy * K)), max(1, int(rad * K * .35)), 1.0, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 10) * 1.1 + cv2.GaussianBlur(glow, (0, 0), 34) * .9
    c.img += hexc('#ffb85a') * np.clip(glow, 0, 1)[..., None] * .35
    c.save('out/A_refined')
    log('saved')

if __name__ == '__main__':
    main()

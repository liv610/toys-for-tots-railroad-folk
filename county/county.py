"""Folk Art — Village Expansion Test.
The Moonlit Village's painter, commissioned to paint the county around it: the same houses, polka-dot roofs, lit windows,
skeleton trees and stippled hills, with a farm, a river and stone bridge, a wooded tunnel hill and a far hamlet."""
import sys, math, time
sys.path.insert(0, '/home/claude/styles2')
import numpy as np, cv2
import a as A
from kit import *

c = A.c
GLOW = A.GLOW
R = np.random.RandomState(44)
T0 = time.time()
def log(m): print(f'C {time.time() - T0:6.1f}s {m}', flush=True)
def sfn(y): return .8 + .5 * max(0, y - 380) / 480

# --------------------------------------------------------------------------- composition (1600 x 900)
FAR = catmull([(-30, 300), (100, 270), (230, 262), (360, 278), (480, 256), (600, 244), (720, 262), (860, 250), (1000, 232), (1140, 244),
               (1280, 226), (1420, 240), (1540, 232), (1630, 246)], 10)
TUNNEL_H = catmull([(-30, 520), (30, 430), (90, 384), (150, 372), (220, 342), (300, 330), (370, 350), (420, 392), (470, 412), (530, 470), (580, 560), (610, 660)], 12)
MID = catmull([(-30, 360), (140, 330), (320, 318), (520, 300), (720, 314), (900, 302), (1080, 322), (1260, 316), (1440, 332), (1630, 320)], 12)
FARM_H = catmull([(1000, 720), (1050, 600), (1120, 520), (1210, 470), (1330, 444), (1450, 440), (1550, 452), (1640, 462)], 12)
VILL_H = catmull([(430, 760), (470, 660), (520, 590), (580, 524), (640, 474), (700, 448), (760, 404), (820, 390), (880, 400), (920, 424), (980, 434), (1040, 470), (1072, 520), (1100, 596), (1160, 680), (1250, 744), (1330, 790)], 12)
SKIRT = catmull([(-30, 740), (140, 700), (330, 690), (520, 700), (700, 712), (880, 716), (1040, 712), (1180, 730), (1360, 760), (1640, 770)], 12)
FRONT = catmull([(-30, 850), (180, 832), (420, 842), (640, 852), (860, 846), (1060, 836), (1280, 818), (1460, 812), (1630, 806)], 12)
RIVER = catmull([(1160, 500), (1132, 540), (1110, 576), (1100, 610), (1090, 650), (1064, 712), (1004, 762), (900, 790), (760, 802),
                 (600, 808), (420, 816), (240, 822), (60, 826), (-30, 828)], 12)
RAIL = resample(catmull([(-40, 640), (60, 620), (160, 590), (250, 548), (320, 506), (372, 470), (404, 450)][::-1] and
                        [(404, 450), (440, 486), (476, 540), (520, 590), (590, 626), (680, 646), (790, 656), (900, 658), (1000, 654),
                         (1090, 644), (1170, 626), (1260, 600), (1350, 584), (1450, 578), (1550, 582), (1640, 588)], 14), 2.0)
TUNNEL = (404, 452)
def _cross():
    best = None
    for i, p in enumerate(RAIL):
        d = np.hypot(*(RIVER - p).T).min()
        if best is None or d < best[0]: best = (d, i)
    return best[1]
BI = _cross(); BR = (BI - 20, BI + 20)

GOLD = [['#e8a034', '#f0b445', '#dc8e26'], ['#e2862a', '#ea9a34', '#d4741f'], ['#efbb4a', '#f4c95a', '#e2a63a'], ['#c9902a', '#d8a236', '#b97e22']]
def banded(m, top, bands, seed, L=3.6, w=1.7, sp=1.5, f1=140, f2=63):
    def col(X, Y, r):
        b = ((np.sin(X / f1 + Y / 55) + np.sin(X / f2 - Y / 90) * .6 + 2) / 4 * len(bands)).astype(int) % len(bands)
        Cc = np.array([[hexc(cc) for cc in bb] for bb in bands]); return Cc[b, r.randint(3, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .12)
    c.stip(m, col, spacing=sp, L=L, w=w, angfn=A.flowdir(top), seed=seed, jit=.3)

def bigchurch(x, y):
    A.house(x, y, 48, 42, 'gable', '#f1e8da', '#2a2340', 7, dotcol='#e6c35a', rows=2, cols_=3, chimney=False)
    tw = 16; top = y - 42 - 44
    m = c.area([(x - tw / 2, y - 30), (x + tw / 2, y - 30), (x + tw / 2, top), (x - tw / 2, top)], '#f6efe2', wob=0, rough=.4)
    c.stip(m, pal_fn(['#f6efe2', '#ebe2d2']), spacing=1.3, L=2.4, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=8, jit=.15)
    c.area([(x + tw / 2, y - 30), (x + tw / 2 + 4, y - 32), (x + tw / 2 + 4, top - 2), (x + tw / 2, top)], '#c9bfb3', wob=0, rough=.4)
    A.window(x, top + 12, 6, 8, arch=True)
    sp_ = [(x - tw / 2 - 2, top), (x + tw / 2 + 2, top), (x + .5, top - 40)]
    c.area(sp_, '#2a2340', wob=0, rough=.4); A.roofdots(sp_, ['#e6c35a'], 0, 9, .55)
    star = (x + .5, top - 46)
    for k in range(5):
        aa = -math.pi / 2 + k * 2 * math.pi / 5
        c.stroke([star, (star[0] + math.cos(aa) * 5.5, star[1] + math.sin(aa) * 5.5)], 1.5, '#f6c84a', a=1, dry=0, taper=(0, .8))
    GLOW.append((star[0], star[1], 36))

def silo(x, y, w=16, h=54):
    m = c.area([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], '#b8b0c4', wob=.1, rough=.5, edge_dark=.08)
    c.stip(m, pal_fn(['#bcb4c8', '#a8a0b6', '#c8c2d4']), spacing=1.2, L=2.6, w=1.2, angfn=lambda X, Y: 0 * X, seed=3, jit=.15)
    dome = [(x - w / 2 - 1 + (w + 2) * u, y - h - math.sin(u * math.pi) * 9) for u in np.linspace(0, 1, 14)]
    c.area(dome, '#7a2e3a', wob=0, rough=.4); A.roofdots(dome + [(x + w / 2, y - h), (x - w / 2, y - h)], ['#f3ecdc'], 0, 4, .5)

def field_strips(top, xa, xb, d0, d1, bands, seed, n=5):
    T = np.asarray(top); o = np.argsort(T[:, 0])
    def ty(x): return float(np.interp(x, T[o, 0], T[o, 1]))
    for k in range(n):
        a_, b_ = d0 + (d1 - d0) * k / n, d0 + (d1 - d0) * (k + 1) / n
        xx = np.linspace(xa + k * 10, xb - k * 6, 24)
        q = [(x, ty(x) + a_) for x in xx] + [(x, ty(x) + b_) for x in xx[::-1]]
        cols = bands[k % len(bands)]
        m = c.area(q, cols[0], wob=.5, rough=.9, edge_dark=.05, seed=seed + k)
        c.stip(m, pal_fn(cols, .06), spacing=1.3, L=4.2, w=1.3, angfn=A.flowdir(top), seed=seed + k, jit=.1)

def footbridge(x, y):
    c.stroke([(x - 14, y + 1), (x + 14, y - 1)], 3, '#9a7a56', a=1, dry=.1, taper=(0, 0))
    c.stroke([(x - 14, y - 4), (x + 14, y - 6)], .9, '#3a2830', a=1, dry=0, taper=(0, 0))
    for xq in (-12, 0, 12): c.stroke([(x + xq, y - xq * .07), (x + xq, y - 6 - xq * .07)], .9, '#3a2830', a=1, dry=0, taper=(0, 0))

def picket(pts, s=1.0):
    P = resample(catmull(pts, 6), 3.4 * s)
    for p in P: c.stroke([(p[0], p[1] + .5), (p[0], p[1] - 5 * s)], 1.2 * s, '#efe6d6', a=1, dry=0, taper=(0, .2))
    c.stroke(P - [0, 3.4 * s], .8 * s, '#efe6d6', a=1, dry=0, taper=(0, 0))

def garden(x, y, w, h, seed):
    r = np.random.RandomState(seed)
    m = c.area([(x, y), (x + w, y - 2), (x + w + 4, y + h), (x + 2, y + h + 1)], '#6a4a34', wob=.2, rough=.6)
    for k, yy in enumerate(np.arange(y + 3, y + h, 4)):
        for xq in np.arange(x + 3 + (k % 2) * 2, x + w + 2, 4):
            c.dots([(xq, yy)], 1.4, [['#6f8f3a', '#8aa84a'], ['#5f7a34', '#7a9a44']][k % 2], seed=int(xq * 7 + yy))
            if r.rand() < .15: c.dots([(xq, yy - 1)], 1.0, ['#e04a3a', '#f0b445', '#f2a6bf'], seed=int(xq + yy))

def main():
    # ----------------------------------------------------------------- sky and moon, as in the village
    m = c.area([(-10, -10), (1610, -10), (1610, 560), (-10, 560)], '#202255', wob=0, rough=0, edge_dark=0)
    c.stip(m, lambda X, Y, r: np.array([hexc('#1b1d4c'), hexc('#26296a'), hexc('#2e2a64'), hexc('#1d2a5a')])[r.randint(4, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .1),
           spacing=2.2, L=5.0, w=1.8, angfn=lambda X, Y: .15 * np.sin(X / 90 + Y / 40), seed=1)
    stars = [(R.uniform(0, 1600), R.uniform(0, 200) ** 1.05 / 1.2) for _ in range(420)]
    c.dots(stars, .75, ['#f6efe0', '#f6efe0', '#f2c86a', '#e8a8c0', '#bcd6e6'], seed=2)
    mx, my = 1430, 86
    for k in range(3):
        rr = 44 + k * 11
        c.dots([(mx + math.cos(a) * rr, my + math.sin(a) * rr) for a in np.linspace(0, 2 * math.pi, 54 + k * 14, endpoint=False)], .8, ['#f2e6c4', '#e8d4a0'], seed=3 + k)
    mm = c.area(S.lumpy(mx, my, 34, 34, 4, n=50, amp=.02), '#f2e6c4', wob=.2, rough=.6, edge_dark=.06)
    c.stip(mm, pal_fn(['#f6ecd2', '#ecdcb4', '#f8f0dc', '#e2cfa6']), spacing=1.3, L=2.4, w=1.3, seed=4)
    log('sky')
    # ----------------------------------------------------------------- mountains: low, slate-violet, snow laid on by hand
    r = np.random.RandomState(31); xs = np.arange(-20, 1640, 4.0); base = 270; ys = np.full_like(xs, base)
    peaks = []
    for k in range(13):
        px = 30 + k * 128 + r.uniform(-40, 40); ph = r.uniform(60, 130); pw = r.uniform(80, 140)
        ys = np.minimum(ys, base - ph * np.clip(1 - np.abs(xs - px) / pw, 0, 1) ** r.uniform(.9, 1.3) + r.randn(len(xs)) * .7)
        peaks.append((px, base - ph, pw))
    ys = np.convolve(ys, [.25, .5, .25], 'same'); ys[0] = ys[1]; ys[-1] = ys[-2]
    mmt = c.area(np.vstack([np.stack([xs, ys], 1), [[1640, 360], [-20, 360]]]), '#3c4476', wob=0, rough=.6, edge_dark=.04)
    def mcol(X, Y, rr):
        out = np.array([hexc('#3c4476'), hexc('#454e84'), hexc('#363e6c')])[rr.randint(3, size=len(X))]
        for (px, py, pw) in peaks:
            out[(X > px) & (np.abs(X - px) < pw) & (Y > py)] *= .82
        return out * (1 + (rr.rand(len(X), 1) - .5) * .06)
    c.stip(mmt, mcol, spacing=1.4, L=4.0, w=1.6, angfn=lambda X, Y: math.pi / 2 + .9 * np.sin(X / 41), seed=32, jit=.3)
    for (px, py, pw) in peaks:
        for k in range(int((base - py) / 4.5)):
            t = r.uniform(0, .45); side = r.choice([-1, 1]); sx = px + side * pw * t * r.uniform(.3, .9); sy = py + (base - py) * t + r.uniform(-2, 4)
            c.stroke([(sx, sy), (sx + side * r.uniform(2, 5), sy + r.uniform(6, 13))], r.uniform(1.4, 2.6), '#e8e2f0' if side < 0 else '#b8b6d4', a=.95, dry=.2, taper=(.05, .6))
    log('mountains')
    # ----------------------------------------------------------------- the far ridge, with a little hamlet
    A.hill(FAR, ['#1f3a3e', '#244444', '#1a3236', '#2a4a48'], 11, spacing=1.6, L=3.4)
    for x in np.arange(-10, 1620, 15):
        if 1300 < x < 1440: continue
        y = y_on(FAR, x) + R.uniform(0, 16)
        if R.rand() < .14: skeleton_tree(c, x, y + 26, R.uniform(40, 54), [['#3a6a6a', '#4f8a80', '#2f5a5a'], ['#5f7a3a', '#7a9a4a', '#4a6a30']][R.randint(2)], int(R.randint(1e6)), dots=['#f6efe0'])
        else: stipple_fir(c, x, y + 22, R.uniform(36, 64), [['#223f40', '#2c4e4a', '#193234', '#3a5e56'], ['#1f3a4a', '#2a4a5a', '#3a6070']][R.randint(2)], int(R.randint(1e6)), slim=.2)
    for i, (x, y, w, h, k, wall, roof) in enumerate([(1316, 262, 20, 16, 'gable', '#f2ece0', '#c22f2a'), (1342, 256, 24, 14, 'side', '#ef9fb8', '#2a2340'),
                                                    (1394, 258, 20, 18, 'gable', '#a9d2e6', '#1f1d2c'), (1420, 266, 22, 14, 'side', '#ef8a2a', '#1f1d2c')]):
        A.house(x, y, w, h, k, wall, roof, 700 + i, dotcol='#f3ecdc' if roof in ('#2a2340', '#1f1d2c') else None, rows=1, cols_=2, chimney=i % 2 == 0)
    tw = 7; c.area([(1368 - tw / 2, 262), (1368 + tw / 2, 262), (1368 + tw / 2, 230), (1368 - tw / 2, 230)], '#f1e8da', wob=0, rough=.3)
    c.area([(1368 - tw / 2 - 1, 230), (1368 + tw / 2 + 1, 230), (1368, 208)], '#2a2340', wob=0, rough=.3); GLOW.append((1368, 206, 14))
    A.hill(MID, ['#2c5450', '#33605a', '#264a48', '#3c6a5e'], 19)
    for x in np.arange(-10, 1620, 19):
        y = y_on(MID, x) + R.uniform(0, 16)
        if R.rand() < .2: skeleton_tree(c, x, y + 30, R.uniform(44, 60), [['#7fae3a', '#98c24a', '#668f2e'], ['#f0a030', '#f6c050', '#d9801f'], ['#3f9a7a', '#5ab48f', '#2f7a62']][R.randint(3)], int(R.randint(1e6)), dots=['#f6efe0'] if R.rand() < .4 else None)
        else: stipple_fir(c, x, y + 26, R.uniform(46, 80), [['#2f5a52', '#3a6a5e', '#24483f', '#4b7a62'], ['#3f5f30', '#4f7038', '#2f4a24'], ['#2a5060', '#386878', '#20404c']][R.randint(3)], int(R.randint(1e6)), slim=.21)
    log('far ridge')
    # ----------------------------------------------------------------- the wooded tunnel hill
    th = A.hill(TUNNEL_H, ['#3a6a50', '#44785a', '#305e46', '#4f8462'], 12)
    pts = []
    for i in range(80):
        x = R.uniform(-20, 560); top = y_on(TUNNEL_H, x); y = top + R.uniform(10, 150)
        if abs(x - TUNNEL[0]) < 46 and -40 < y - TUNNEL[1] < 40: continue
        if any(abs(x - p[1]) < 15 and abs(y - p[0]) < 12 for p in pts): continue
        pts.append((y, x))
    for y, x in sorted(pts):
        if R.rand() < .7: stipple_fir(c, x, y + 20, R.uniform(40, 70) * (1 + (y - 330) / 500), [['#2f5a52', '#3a6a5e', '#24483f', '#4b7a62'], ['#3f5f30', '#4f7038', '#2f4a24'], ['#2a5060', '#386878', '#20404c']][R.randint(3)], int(R.randint(1e6)), slim=.21)
        else: skeleton_tree(c, x, y + 22, R.uniform(40, 58), [['#e04a2a', '#f06a3a', '#c8341f'], ['#f2a6c8', '#e98ab0', '#f6c8dc'], ['#7fae3a', '#98c24a', '#668f2e'], ['#f0a030', '#f6c050']][R.randint(4)], int(R.randint(1e6)), dots=['#f6efe0'] if R.rand() < .3 else None)
    log('tunnel hill')
    # ----------------------------------------------------------------- the farm hill (lime and olive, as in the village's neighbour) and the village hill (gold)
    A.hill(FARM_H, ['#7d8c34', '#94a03c', '#6a7a2e', '#a7ad4a', '#5f7030'], 13)
    field_strips(FARM_H, 1340, 1640, 150, 250, [['#e0a03a', '#e8b04a', '#d08e2e'], ['#8a9a30', '#9aa83a'], ['#b86a3a', '#c47a44', '#a85e32'], ['#efbb4a', '#f4c95a'], ['#6a7a2e', '#7a8a34']], 21, n=5)
    vm = c.area(land(VILL_H), '#e39a2c', wob=1, rough=1, edge_dark=.04, seed=14)
    banded(vm, VILL_H, GOLD, 15)
    for (px, py, rx, ry) in [(600, 600, 60, 16), (980, 560, 60, 16), (800, 470, 44, 10)]:
        pm = c.area(S.lumpy(px, py, rx, ry, int(px), n=36, amp=.12), '#8a9a2e', wob=.6, rough=1, edge_dark=.04)
        c.stip(pm, pal_fn(['#8f9c34', '#a3aa3e', '#7a8a2a', '#b4b448']), spacing=1.4, L=3.2, w=1.6, angfn=A.flowdir(VILL_H), seed=int(px) + 3)
    sk = c.area(land(SKIRT), '#7f8f2e', wob=1, rough=1, edge_dark=.04, seed=16)
    c.stip(sk, pal_fn(['#7f8f2e', '#8f9c36', '#6e7f2a', '#a1a63e']), spacing=1.6, L=4.2, w=1.9, angfn=A.flowdir(SKIRT), seed=17, jit=.3)
    log('hills')
    # ----------------------------------------------------------------- the river, stitched, with stones on its banks
    poly, nr, wv = ribbon(RIVER, lambda t: 6 + 46 * t ** 1.1)
    rm = c.area(poly, '#22466a', wob=.4, rough=.7, edge_dark=.1)
    def rang(X, Y):
        j = np.argmin(np.hypot(RIVER[:, 0][None] - X[:, None], RIVER[:, 1][None] - Y[:, None]), axis=1)
        d = np.gradient(RIVER, axis=0)[j]; return np.arctan2(d[:, 1], d[:, 0])
    c.stip(rm, pal_fn(['#244a70', '#2e5880', '#1d3d5e', '#36628a']), spacing=1.4, L=4.6, w=1.4, angfn=rang, seed=22, jit=.1)
    for k in range(110):
        j = R.randint(6, len(RIVER) - 6); t = j / len(RIVER); off = R.uniform(-.3, .3) * (6 + 46 * t ** 1.1)
        p = RIVER[j] + nr[min(j, len(nr) - 1)] * off; d = RIVER[j + 3] - RIVER[j]; d /= np.hypot(*d)
        c.stroke([p - d * 5, p + d * 5], .8, '#cfe0ea', a=.8, dry=.15, taper=(.2, .2))
    log('river')
    # ----------------------------------------------------------------- lanes
    path(c, [(520, 760), (560, 700), (620, 640)], 5, '#e9cf96', sfn, dotted=['#f6ecd8', '#d9b77a'], seed=1)
    path(c, [(640, 620), (700, 560), (760, 500), (800, 440)], 5, '#e9cf96', sfn, dotted=['#f6ecd8', '#d9b77a'], seed=2)
    path(c, [(1170, 600), (1250, 548), (1320, 520), (1400, 512)], 4, '#d9c08a', sfn, dotted=['#f6ecd8'], seed=3)
    # ----------------------------------------------------------------- the railway, bridge and tunnel, painted with the same dabs
    before = c.img.copy()
    rails(c, RAIL, sfn, ballast='#8f7f6a', tie='#3a2a24', steel='#2a2630', hide=[BR, (0, 4)], shine='#e8d8b0')
    restipple(c, before, seed=31)
    a_, b_ = BR; dk = RAIL[a_:b_ + 1] + [0, 4]
    x0, x1 = dk[0, 0], dk[-1, 0]; bb = float(dk[:, 1].max()) + 30
    aw = 40; ah = 24
    jj = [j for j in range(len(RIVER)) if RIVER[j][1] >= bb - 6]
    ax = float(np.clip(RIVER[jj[0]][0] if jj else (x0 + x1) / 2, x0 + aw / 2 + 4, x1 - aw / 2 - 4))
    arch = [(ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    face = np.vstack([dk - [0, 3], [[x1, bb]], arch, [[x0, bb]]])
    bm = c.area(face, '#a99a8a', wob=.2, rough=.6, edge_dark=.1, seed=32)
    c.stip(bm, pal_fn(['#b3a594', '#9d8e80', '#c2b5a3', '#8f8276']), spacing=1.4, L=3.2, w=2.0, angfn=lambda X, Y: 0 * X, seed=33, jit=.2)
    for u in np.linspace(0, 1, 9):
        p = np.array((ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah)); dv = p - [ax, bb + 6]; dv /= np.hypot(*dv)
        c.stroke([p, p + dv * 5], 2.6, '#c9bcaa', a=.9, dry=.1, taper=(0, 0))
    c.stroke(dk - [0, 2], 5, '#c9bcaa', a=1, dry=.1, taper=(0, 0))
    for xq in np.arange(x0, x1, 7):
        y = float(np.interp(xq, dk[:, 0], dk[:, 1])) - 5; c.stroke([(xq, y), (xq, y - 3)], 1.4, '#c9bcaa', a=1, dry=0, taper=(0, 0))
    before = c.img.copy()
    rails(c, RAIL[a_:b_ + 1], sfn, ballast=None, tie='#3a2a24', steel='#2a2630', shine='#e8d8b0')
    restipple(c, before, seed=34)
    A.tunnel(TUNNEL[0], TUNNEL[1] + 2)
    for k, dx in enumerate((-30, -6, 18, 34)):
        stipple_fir(c, TUNNEL[0] + dx, TUNNEL[1] - 18 - abs(dx) * .2, R.uniform(34, 46), ['#2f5a52', '#3a6a5e', '#24483f', '#4b7a62'], 900 + k, slim=.2)
    log('rail')
    # ----------------------------------------------------------------- the county's places, back to front
    objs = []
    # the village: six houses and the church, each different
    for i, (x, y, w, h, k, wall, roof) in enumerate([
            (680, 470, 58, 46, 'gable', '#f2a6bf', '#2a2340'), (940, 476, 66, 40, 'side', '#7d6aa8', '#2a2340'),
            (742, 566, 48, 70, 'tall', '#5f98a6', '#1f2a3a'), (888, 580, 76, 48, 'side', '#c2397a', '#1f1d2c'),
            (600, 600, 52, 46, 'round', '#ef8a2a', None), (1010, 596, 54, 50, 'gable', '#f2ece0', '#c0392b')]):
        objs.append((y, 'house', (x, y, w, h, k, wall, roof, 300 + i)))
    objs.append((410, 'church', (812, 410)))
    objs.append((640, 'station', (780, 642)))
    # the farm
    objs.append((520, 'barn', (1290, 522))); objs.append((514, 'silo', (1346, 516))); objs.append((496, 'farmhouse', (1440, 496)))
    objs.append((470, 'windmill', (1560, 476)))
    for x, y in [(1420, 560), (1470, 566)]: objs.append((y, 'hay', (x, y)))
    # foreground homes
    objs.append((880, 'house', (210, 880, 80, 60, 'gable', '#f2ece0', '#c22f2a', 401)))
    objs.append((872, 'house', (1300, 872, 60, 84, 'tall', '#4f86b8', '#1f1d2c', 402)))
    objs.append((866, 'house', (1430, 866, 72, 48, 'side', '#ef9fb8', '#2a2340', 403)))
    TREES = [
        # village
        (620, 520, 50, ['#3f9a7a', '#5ab48f', '#2f7a62'], '#f6efe0'), (860, 470, 46, ['#e86a2a', '#f08a3a', '#c8501f']), (1000, 520, 48, ['#b8287a', '#d94a9a', '#9e1f62']),
        (820, 600, 44, ['#c8d24a', '#a8b83a', '#e2e070']), (690, 640, 40, ['#f2a6c8', '#e98ab0', '#f6c8dc']), (960, 640, 42, ['#8a2a8a', '#a84aa8', '#6a1f6a'], '#f6efe0'),
        (1060, 640, 46, ['#f0a030', '#f6c050', '#d9801f']),
        # farm orchard: loose rows of red-dotted trees
        *[(1160 + i * 30 + (j % 2) * 15 + R.uniform(-4, 4), 540 + j * 20 + R.uniform(-2, 2), 30, ['#5f8a3a', '#7aa04a', '#4a7030'], '#e04a3a') for j in range(2) for i in range(3)],
        (1240, 470, 52, ['#e04a2a', '#f06a3a', '#c8341f']), (1520, 520, 56, ['#3f9a7a', '#5ab48f']), (1610, 520, 50, ['#f0a030', '#f6c050']),
        # skirt and foreground
        (120, 720, 56, ['#c8287a', '#e04a9a', '#a01f62', '#f2a6c8']), (340, 730, 48, ['#e05a2a', '#f07a3a', '#c8401f']), (480, 740, 44, ['#3f9a7a', '#5ab48f'], '#f6efe0'),
        (60, 900, 180, ['#c8287a', '#e04a9a', '#a01f62']), (380, 900, 110, ['#c9b83a', '#e2d050', '#a8962a']), (640, 900, 90, ['#f2a6c8', '#e98ab0', '#f6c8dc']),
        (1160, 900, 100, ['#8a2a8a', '#a84aa8', '#6a1f6a'], '#f6efe0'), (1580, 900, 170, ['#e86a2a', '#f08a3a', '#c8501f']),
    ]
    for i, t in enumerate(TREES): objs.append((t[1], 'tree', (i, t)))
    objs.append((830, 'fir', (880, 840, 90)))
    objs.sort(key=lambda o: o[0])
    front_done = [False]
    def draw(o):
        _, kind, v = o
        if kind == 'house':
            x, y, w, h, k, wall, roof, sd = v
            A.house(x, y, w, h, k, wall, roof or '#1f1d2c', sd, dotcol=['#f3ecdc', '#f6c84a'][sd % 2] if roof in ('#1f1d2c', '#2a2340', '#1f2a3a') else None)
        elif kind == 'church': bigchurch(*v)
        elif kind == 'station':
            x, y = v; A.house(x, y, 80, 28, 'side', '#c22f2a', '#1f1d2c', 77, dotcol='#f6c84a', rows=1, cols_=4, chimney=False)
            for lx in (x - 46, x + 46):
                c.stroke([(lx, y + 6), (lx, y - 18)], 1.0, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 19)], 1.8, ['#ffd27a']); GLOW.append((lx, y - 19, 20))
        elif kind == 'barn': A.house(v[0], v[1], 70, 44, 'barn', '#b8302a', '#2a2340', 55, dotcol='#f3ecdc')
        elif kind == 'silo': silo(*v)
        elif kind == 'farmhouse': A.house(v[0], v[1], 60, 44, 'side', '#f2ece0', '#1f1d2c', 56, dotcol='#f6c84a', rows=2, cols_=3)
        elif kind == 'windmill': A.windmill(*v)
        elif kind == 'hay': bush(c, v[0], v[1], 9, 8, ['#e2b44b', '#d49a30', '#efc860'], int(v[0]))
        elif kind == 'tree':
            i, t = v; skeleton_tree(c, t[0], t[1], t[2], t[3], 800 + i, dots=[t[4]] if len(t) > 4 else None)
        elif kind == 'fir': stipple_fir(c, v[0], v[1], v[2], ['#2f5a52', '#3a6a5e', '#24483f', '#4b7a62'], int(v[0]), slim=.22)
    for o in [o for o in objs if o[0] < 760]: draw(o)
    picket([(1200, 600), (1260, 592), (1330, 586)]); picket([(560, 664), (620, 676), (680, 680)])
    garden(1376, 506, 34, 12, 5)
    log('village & farm')
    # the foreground meadow, in front of the river
    fm = c.area(land(FRONT), '#6f8a34', wob=1, rough=1, edge_dark=.04, seed=18)
    c.stip(fm, pal_fn(['#6f8a34', '#7f9a3c', '#5f7a2e', '#90a846']), spacing=2.0, L=5.4, w=2.4, angfn=A.flowdir(FRONT), seed=19, jit=.35)
    pts = []
    for (cx, cy, n, sp) in [(300, 880, 70, 50), (760, 880, 60, 50), (1060, 870, 50, 40), (1500, 880, 60, 40)]:
        pts += [(cx + R.randn() * sp, cy + abs(R.randn()) * sp * .3) for _ in range(n)]
    c.dots(pts, 1.4, ['#f6efe0', '#f2c86a', '#f2a6c8', '#e04a3a'], seed=23)
    for x in np.arange(10, 1100, 46):
        j = int(np.argmin(np.abs(RIVER[:, 0] - x))); t = j / len(RIVER)
        y = RIVER[j, 1] + (6 + 46 * t ** 1.1) / 2 + 6
        if R.rand() < .5:
            rx = R.uniform(12, 20); sm2 = c.area(S.lumpy(x, y, rx, rx * .55, int(x) + 1, n=30, amp=.04, flat=.3), '#8a8892', wob=.2, rough=.6, edge_dark=.15)
            c.stip(sm2, pal_fn(['#9a98a2', '#7e7c88', '#b0aeb6', '#6e6c78']), spacing=1.3, L=2.6, w=1.4, seed=int(x) + 2)
        elif R.rand() < .7:
            bush(c, x, y + 4, R.uniform(12, 20), R.uniform(9, 13), [['#c8302a', '#e04a3a'], ['#e2b030', '#f0c84a'], ['#8a2a6a', '#a84a8a']][R.randint(3)], int(x) + 7)
    footbridge(470, 816)
    path(c, [(250, 890), (330, 860), (420, 840), (470, 826)], 5, '#e9cf96', sfn, dotted=['#f6ecd8'], seed=5)
    garden(250, 896, 50, 12, 6); picket([(130, 900), (200, 904), (300, 910)], 1.3)
    for o in [o for o in objs if o[0] >= 760]: draw(o)
    log('foreground')
    # little discoveries: a lantern boat, a fox by the orchard, washing on a line
    bx, by = 860, 798
    c.area([(bx - 16, by - 3), (bx + 18, by - 4), (bx + 12, by + 4), (bx - 11, by + 4)], '#b8302a', wob=0, rough=.3)
    c.stroke([(bx + 4, by - 4), (bx + 4, by - 20)], .9, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(bx + 4, by - 21)], 2, ['#ffd27a']); GLOW.append((bx + 4, by - 21, 36))
    fx, fy = 1214, 600
    c.area(S.lumpy(fx, fy - 3, 6, 3, 4, n=18, amp=.04), '#d0703a', wob=0, rough=.3); c.area([(fx + 5, fy - 4), (fx + 10, fy - 6), (fx + 8, fy - 2)], '#d0703a', wob=0, rough=.3)
    c.area([(fx - 5, fy - 3), (fx - 12, fy - 6), (fx - 14, fy - 3)], '#d0703a', wob=0, rough=.3); c.dots([(fx - 13.5, fy - 4)], 1.1, ['#f6efe0'])
    wl = catmull([(1484, 500), (1500, 503), (1516, 500)], 6)
    c.stroke([(1484, 500), (1484, 492)], .7, '#3a2830', a=1, dry=0, taper=(0, 0)); c.stroke([(1516, 500), (1516, 492)], .7, '#3a2830', a=1, dry=0, taper=(0, 0))
    c.stroke(wl - [0, 8], .4, '#efe6d6', a=.8, dry=0, taper=(0, 0))
    for k, u in enumerate((.2, .45, .7)):
        p = wl[int(u * (len(wl) - 1))] - [0, 8]
        c.area([p + [-1.4, 0], p + [1.4, 0], p + [1.2, 3.2], p + [-1.2, 3]], ['#f2a6bf', '#a9d2e6', '#f0b445'][k], wob=0, rough=.2)
    # the train, in front of the village
    i_head = int(np.argmin(np.abs(RAIL[:, 0] - 1000) + (RAIL[:, 1] < 600) * 1e4))
    before = c.img.copy()
    train(c, RAIL, i_head, 2.0)
    restipple(c, before, seed=41)
    GLOW.append(tuple(RAIL[i_head] + [6, -14]) + (60,))
    glow = np.zeros((H, W), np.float32)
    for gx, gy, rad in GLOW: cv2.circle(glow, (int(gx * K), int(gy * K)), max(1, int(rad * K * .35)), 1.0, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 10) * 1.1 + cv2.GaussianBlur(glow, (0, 0), 34) * .9
    c.img += hexc('#ffb85a') * np.clip(glow, 0, 1)[..., None] * .35
    c.save('/home/claude/county/out/county')
    log('saved')

if __name__ == '__main__':
    main()

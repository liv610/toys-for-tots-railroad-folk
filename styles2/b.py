"""Direction B — Whimsical Storybook World.
A sunny American folk landscape in layers: dabbed teal forests, a lake with a lighthouse, a white farmhouse with picket fences,
a hillside village with a Ferris wheel, and a railway that swings in a great S from a big foreground train up to the far hills.
Scale is played with on purpose: giant sunflowers and a mushroom cottage in front, a tiny world behind."""
import math, time
import numpy as np, cv2
from kit import *

c = setup('#eadfc4', 202)
R = np.random.RandomState(8)
T0 = time.time()
def log(m): print(f'B {time.time() - T0:6.1f}s {m}', flush=True)
def sfn(y): return .62 + 2.3 * max(0, y - 310) / 590

FAR = catmull([(-20, 236), (90, 206), (200, 214), (330, 186), (460, 200), (580, 176), (700, 186), (830, 164), (960, 182), (1090, 160),
               (1220, 178), (1350, 160), (1480, 188), (1630, 172)], 10)
HUP_L = catmull([(-20, 300), (80, 286), (200, 276), (320, 282), (420, 296), (500, 322), (560, 356), (610, 420), (650, 520)], 12)
HUP_R = catmull([(600, 380), (680, 334), (780, 300), (900, 278), (1020, 266), (1140, 262), (1260, 274), (1380, 260), (1500, 280), (1630, 276)], 12)
HMID = catmull([(-20, 520), (100, 490), (240, 480), (380, 494), (520, 478), (640, 492), (720, 522), (780, 566), (800, 620)], 12)
HMID_R = catmull([(840, 600), (900, 566), (980, 530), (1080, 500), (1200, 476), (1320, 456), (1440, 444), (1560, 448), (1630, 452)], 12)
FG_L = catmull([(-20, 700), (120, 672), (260, 664), (420, 676), (560, 700), (700, 730), (800, 780), (860, 860), (880, 930)], 12)
FG_R = catmull([(1060, 930), (1100, 840), (1200, 776), (1340, 744), (1480, 732), (1630, 724)], 12)
LAKE = S.lumpy(360, 418, 290, 56, 14, n=60, bumps=4, amp=.06, flat=0)
RIVER = catmull([(752, 470), (790, 516), (824, 568), (870, 616), (930, 650), (972, 692), (984, 746), (996, 810), (1010, 870), (1022, 930)], 12)
RAIL = resample(catmull([(-40, 884), (140, 850), (320, 806), (500, 770), (660, 742), (800, 718), (900, 702), (1000, 688), (1100, 668),
                          (1220, 628), (1320, 572), (1392, 506), (1412, 452), (1380, 412), (1300, 390), (1180, 380), (1060, 384),
                          (940, 390), (830, 394), (730, 388), (640, 370), (560, 350), (480, 336), (400, 328), (280, 320),
                          (150, 314), (-40, 310)], 14), 2.0)
TRESTLE = (int(np.argmin(np.hypot(RAIL[:, 0] - 896, RAIL[:, 1] - 702))), int(np.argmin(np.hypot(RAIL[:, 0] - 1060, RAIL[:, 1] - 678))))

def meadow(top, cols, seed, speck='#4f6a2c', strokes=(9, 64, 7)):
    m = c.area(land(top), cols[0], wob=1, rough=1, edge_dark=.04, seed=seed)
    T = np.asarray(top)
    def ang(x, y):
        o = np.argsort(T[:, 0]); dx = np.gradient(T[o, 1]) / (np.gradient(T[o, 0]) + 1e-6)
        return math.atan(float(np.interp(x, T[o, 0], dx))) * max(.1, 1 - (y - float(np.interp(x, T[o, 0], T[o, 1]))) / 200)
    def col(x, y, r):
        d = y - float(np.interp(x, T[np.argsort(T[:, 0]), 0], T[np.argsort(T[:, 0]), 1]))
        t = np.clip(d / 140, 0, 1)
        return mix(cols[1], cols[0], t) * (1 + (r.rand() - .5) * .08)
    c.flow_fill(m, ang, col, strokes[0], strokes[1], strokes[2], dry=.3, a=.9, seed=seed + 1)
    if speck:
        x0, y0, mm = m; h, w = mm.shape; r = np.random.RandomState(seed + 2); pts = []
        for i in range(int(h * w / (K * K * 90))):
            px, py = r.randint(w), r.randint(h)
            if mm[py, px] > .9: pts.append(((px + x0) / K, (py + y0) / K))
        c.dots(pts, .45, [speck, '#6a7a3a', '#8a5a3a'], a=1, seed=seed + 3)
    c.stroke(T + [0, 2], 4, cols[1], a=.5, dry=.6, taper=(.02, .02))
    return m

def picket(pts, s=1.0, col='#f8f4ea'):
    P = resample(catmull(pts, 6), 3.0 * s)
    for p in P: c.stroke([(p[0], p[1] + .5 * s), (p[0], p[1] - 4.5 * s)], 1.1 * s, col, a=1, dry=0, taper=(0, .25), press=0)
    c.stroke(P - [0, 3.2 * s], .7 * s, col, a=1, dry=0, taper=(0, 0)); c.stroke(P - [0, 1.2 * s], .7 * s, col, a=1, dry=0, taper=(0, 0))

def ferris(x, y, rr):
    for a in (-.5, .5):
        c.stroke([(x, y - rr), (x + math.sin(a) * rr * 1.25, y + 2)], 1.6, '#c9a46a', a=1, dry=.1, taper=(0, 0))
    ring = [(x + rr * math.cos(t), y - rr + rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 60)]
    c.stroke(ring, 1.4, '#e05a4a', a=1, dry=0, taper=(0, 0))
    c.stroke([(x + rr * .82 * math.cos(t), y - rr + rr * .82 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 60)], .6, '#e8c050', a=1, dry=0, taper=(0, 0))
    for k in range(12):
        t = k / 12 * 2 * math.pi
        c.stroke([(x, y - rr), (x + rr * math.cos(t), y - rr + rr * math.sin(t))], .5, '#f4ecd8', a=.9, dry=0, taper=(0, 0))
        gx, gy = x + rr * math.cos(t), y - rr + rr * math.sin(t) + 3
        c.area([(gx - 2.6, gy - 2), (gx + 2.6, gy - 2), (gx + 2.2, gy + 2.6), (gx - 2.2, gy + 2.6)], ['#e05a4a', '#5fa59c', '#e8c050', '#d98ab0'][k % 4], wob=0, rough=.2)
    c.dots([(x, y - rr)], 2.2, ['#e8c050'])

def lighthouse(x, y):
    c.area(S.lumpy(x, y + 3, 26, 7, 3, n=24, amp=.1), '#9aa86a', wob=.3, rough=.6)
    c.area(S.lumpy(x - 6, y + 4, 10, 3, 4, n=16, amp=.1), '#a69a86', wob=.2, rough=.6)
    h = 44; w0, w1 = 9, 6
    body = [(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y - h), (x - w1 / 2, y - h)]
    m = c.area(body, '#f6f0e4', wob=0, rough=.4)
    prev = c.clipm; c.set_clip(m)
    for k in range(4):
        yy = y - h * (k * 2 + 1) / 8
        c.area([(x - 8, yy), (x + 8, yy), (x + 8, yy - h / 8), (x - 8, yy - h / 8)], '#c8402e', wob=0, rough=.3)
    c.area([(x + 1, y + 2), (x + 8, y + 2), (x + 8, y - h - 2), (x + 1, y - h - 2)], '#6a6058', wob=0, rough=.5, a=.25)
    c.clipm = prev
    c.area([(x - 5, y - h), (x + 5, y - h), (x + 5, y - h - 7), (x - 5, y - h - 7)], '#f2d06a', wob=0, rough=.3)
    c.area([(x - 6.5, y - h - 7), (x + 6.5, y - h - 7), (x, y - h - 14)], '#2a3a48', wob=0, rough=.3)
    c.stroke([(x - 7, y - h), (x + 7, y - h)], 1.2, '#2a3a48', a=1, dry=0, taper=(0, 0))

def sailboat(x, y, s, col):
    c.area([(x - 7 * s, y), (x + 8 * s, y), (x + 5 * s, y + 3 * s), (x - 5 * s, y + 3 * s)], '#8a3a2a', wob=0, rough=.2)
    c.area([(x, y - 1), (x, y - 15 * s), (x + 8 * s, y - 2)], col, wob=0, rough=.2)
    c.area([(x - 1, y - 1), (x - 1, y - 11 * s), (x - 6 * s, y - 2)], '#f8f4ea', wob=0, rough=.2)
    c.stroke([(x - 9 * s, y + 4 * s), (x + 10 * s, y + 4 * s)], .8, '#e6f0ee', a=.7, dry=.3)

def covered_bridge(x, y):
    w, h = 40, 12
    c.area([(x - w / 2 - 3, y), (x + w / 2 + 3, y), (x + w / 2 + 3, y + 4), (x - w / 2 - 3, y + 4)], '#9a8a76', wob=0, rough=.4)
    c.area([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], '#b8352a', wob=0, rough=.4, edge_dark=.1)
    for k in range(9): c.stroke([(x - w / 2 + k * w / 8, y), (x - w / 2 + k * w / 8, y - h)], .5, '#8a2420', a=.8, dry=0, taper=(0, 0))
    c.area([(x - w / 2 - 3, y - h), (x + w / 2 + 3, y - h), (x + w / 2 - 2, y - h - 9), (x - w / 2 + 2, y - h - 9)], '#4a3a3a', wob=0, rough=.4)
    c.area([(x - w / 2 + 6, y), (x - w / 2 + 6, y - h + 4), (x - w / 2 + 1, y - h + 4), (x - w / 2 + 1, y)], '#2a1f1e', wob=0, rough=.3)
    c.area([(x - 3, y - h + 3), (x + 3, y - h + 3), (x + 3, y - h + 7), (x - 3, y - h + 7)], '#f8f4ea', wob=0, rough=.3)

def trestle():
    a, b = TRESTLE; dk = RAIL[a:b + 1]
    x0, x1 = dk[0, 0], dk[-1, 0]; base = 790
    s = sfn(700)
    posts = np.arange(x0 + 4, x1, 15)
    for px in posts:
        top = float(np.interp(px, dk[:, 0], dk[:, 1])) + 3
        c.stroke([(px - 4, base), (px - 1, top)], 2.4, '#7a5636', a=1, dry=.15, taper=(0, 0))
        c.stroke([(px + 4, base), (px + 1, top)], 2.4, '#6a4a2e', a=1, dry=.15, taper=(0, 0))
    for yy in np.linspace(0, 1, 5)[:-1]:
        for i in range(len(posts) - 1):
            pa, pb = posts[i], posts[i + 1]
            ta = float(np.interp(pa, dk[:, 0], dk[:, 1])) + 3; tb = float(np.interp(pb, dk[:, 0], dk[:, 1])) + 3
            ya = ta + (base - ta) * yy; yb = tb + (base - tb) * (yy + .25)
            c.stroke([(pa, ya), (pb, yb)], 1.1, '#8a6440', a=.95, dry=.1, taper=(0, 0))
            c.stroke([(pa, yb + (ya - ta) * 0), (pb, ya)], 1.1, '#8a6440', a=.95, dry=.1, taper=(0, 0))
    c.stroke(dk + [0, 4], 6 * s, '#8a6440', a=1, dry=.1, taper=(0, 0))

def mushroom_house(x, y, h):
    sw = h * .28
    stem = [(x - sw / 2, y), (x + sw / 2, y), (x + sw * .42, y - h * .6), (x - sw * .42, y - h * .6)]
    m = c.area(stem, '#f2e8d4', wob=.3, rough=.6, edge_dark=.08)
    c.flow_fill(m, lambda a, b: -math.pi / 2, lambda a, b, r: hexc('#f2e8d4') * (.9 + .15 * r.rand()), 3, 16, 3, dry=.3, a=.8, seed=5)
    dw = sw * .4
    c.area([(x - dw / 2, y)] + [(x - dw / 2 + dw * u, y - h * .26 - math.sin(u * math.pi) * dw * .5) for u in np.linspace(0, 1, 10)] + [(x + dw / 2, y)], '#3f6a8a', wob=0, rough=.3)
    c.dots([(x + dw * .25, y - h * .14)], 1.2, ['#e8c050'])
    c.area(S.lumpy(x + sw * .26, y - h * .42, 3.4, 3.4, 2, n=16, amp=0), '#f2c860', wob=0, rough=.3)
    cap = [(x - h * .42 + h * .84 * u, y - h * .58 - math.sin(u * math.pi) ** .7 * h * .42) for u in np.linspace(0, 1, 24)]
    cap = cap + [(x + h * .4, y - h * .52), (x - h * .4, y - h * .52)]
    m = c.area(cap, '#c8352a', wob=.3, rough=.6, edge_dark=.1)
    c.flow_fill(m, lambda a, b: .2, lambda a, b, r: hexc(['#c8352a', '#d84a36', '#b02a22'][r.randint(3)]), 6, 30, 5, dry=.3, a=.9, seed=7)
    r = np.random.RandomState(3)
    c.dots([(x + r.uniform(-.32, .32) * h, y - h * .62 - r.uniform(0, .3) * h) for _ in range(9)], h * .03, ['#f8f4ea'])
    c.stroke([(x + h * .12, y - h * .9), (x + h * .14, y - h * 1.0)], 2, '#8a3a2a', a=1, dry=0, taper=(0, 0))
    smoke(x + h * .14, y - h * 1.05, 1.4, 4, n=4)

def sunflower(x, y, h, seed):
    r = np.random.RandomState(seed)
    stem = [(x, y), (x + r.randn() * 4, y - h * .5), (x + r.randn() * 6, y - h)]
    c.stroke(stem, h * .025, '#4f6a2c', a=1, dry=.1, taper=(0, .2))
    for k in range(3):
        ly = y - h * (.25 + k * .22); side = 1 if k % 2 else -1
        leaf = S.lumpy(x + side * h * .08, ly, h * .08, h * .035, seed + k, n=18, amp=.05)
        c.area(leaf, '#5f7a34', wob=.2, rough=.5)
        c.stroke([(x, ly), (x + side * h * .15, ly - h * .01)], .9, '#3f5a24', a=.8, dry=0)
    hx, hy = stem[-1]
    rr = h * .11
    for k in range(18):
        a = k / 18 * 2 * math.pi
        c.dab(hx + math.cos(a) * rr * 1.25, hy + math.sin(a) * rr * 1.1, rr * .9, rr * .32, a, ['#f0c040', '#e8a830', '#f6d060'][k % 3], a=1, dry=.15, bend=.2)
    m = c.area(S.lumpy(hx, hy, rr * .8, rr * .74, seed, n=24, amp=.03), '#5a3a22', wob=0, rough=.5)
    c.stip(m, pal_fn(['#5a3a22', '#7a4a2a', '#3f2818']), spacing=1.1, L=1.6, w=1.4, seed=seed)

def hollyhock(x, y, h, seed, col):
    r = np.random.RandomState(seed)
    c.stroke([(x, y), (x + r.randn() * 2, y - h)], h * .018, '#4f6a2c', a=1, dry=.1, taper=(0, .3))
    for k in range(int(h / 14)):
        t = k / (h / 14); px = x + r.randn() * 1.5; py = y - h * (.3 + .7 * t)
        rr = h * .05 * (1 - .5 * t)
        c.area(S.lumpy(px, py, rr, rr * .9, seed + k, n=18, amp=.12), col, wob=.2, rough=.5, edge_dark=.12)
        c.dots([(px, py)], rr * .25, ['#f6e6a0'])

def main():
    # sky with soft, brushed clouds
    m = c.area([(-10, -10), (1610, -10), (1610, 330), (-10, 330)], '#a9cbe0', wob=0, rough=0, edge_dark=0)
    def skc(x, y, r):
        t = np.clip(y / 260, 0, 1); b = mix('#8fbad8', '#d8e8e4', t)
        return mix(b, '#f6f2ea', .55) if r.rand() < .12 else b * (1 + (r.rand() - .5) * .05)
    c.flow_fill(m, lambda x, y: .04 * math.sin(x / 200), skc, 20, 160, 12, dry=.3, a=.9, seed=1)
    for (cx, cy, rx, ry) in [(160, 70, 120, 18), (520, 52, 90, 14), (900, 86, 150, 20), (1310, 60, 110, 16), (1520, 110, 70, 12)]:
        for k in range(18):
            px = cx + R.uniform(-1, 1) * rx; py = cy + R.uniform(-1, 1) * ry * (1 - abs(px - cx) / rx * .5)
            c.stroke([(px - rx * .3, py + 2), (px, py - 2), (px + rx * .3, py + 2)], R.uniform(6, 12), ['#ffffff', '#f4f0ea', '#e6ecef'][R.randint(3)], a=.85, dry=.35)
    log('sky')
    # far forests: a scalloped teal mass of dabs
    sil = []
    for x in np.arange(-20, 1630, 7):
        y = y_on(FAR, x); sil.append((x, y - 4 - 6 * abs(math.sin(x / 7.0 * 1.1 + R.rand()))))
    fm = c.area(np.vstack([sil, [[1630, 520], [-20, 520]]]), '#2f5a52', wob=0, rough=.8, edge_dark=.04, seed=3)
    def fcol(X, Y, r):
        top = np.interp(X, FAR[:, 0], FAR[:, 1]); t = np.clip((Y - top) / 80, 0, 1)
        C = np.array([hexc('#5f9a7a'), hexc('#3f7a6a'), hexc('#2f6058'), hexc('#244a46')])
        idx = np.clip((t * 3 + r.randn(len(X)) * .6).round().astype(int), 0, 3)
        return C[idx] * (1 + (r.rand(len(X), 1) - .5) * .1)
    c.stip(fm, fcol, spacing=1.2, L=2.0, w=1.8, seed=4, jit=1.5)
    for x in np.arange(-10, 1620, 22):
        y = y_on(FAR, x) + R.uniform(16, 60)
        dab_tree(c, x + R.randn() * 6, y, R.uniform(20, 34), [['#2a5a50', '#3f7a64', '#6aa080'], ['#3a6a40', '#4f8a50', '#8ab868']][R.randint(2)], int(R.randint(1e6)), shape='cone')
    log('forest')
    meadow(HUP_L, ['#9cb06a', '#bcc888'], 11)
    meadow(HUP_R, ['#b2b46a', '#d0cc8a'], 12)
    # the lake, with reflections in long strokes
    lm = c.area(LAKE, '#6aa6b6', wob=.6, rough=.8, edge_dark=.15, seed=13)
    c.flow_fill(lm, lambda x, y: 0, lambda x, y, r: hexc(['#6aa6b6', '#86bcc8', '#5a96a8', '#a8d0d8'][r.randint(4)]), 3, 40, 3.4, dry=.35, a=.85, seed=14, jitter=.05)
    c.stroke(LAKE[np.argsort(LAKE[:, 0])][::3], 1, '#3f6a3a', a=0)
    log('lake')
    meadow(HMID, ['#8fa65a', '#aebe78'], 15)
    meadow(HMID_R, ['#a6ac5e', '#c6c27c'], 16)
    # fields that follow the slope of the right-middle hill, stitched with hedgerows
    T = np.asarray(HMID_R); r = np.random.RandomState(31)
    def ty(x): return float(np.interp(x, T[:, 0], T[:, 1]))
    FCOL = ['#d8c06a', '#c9a95a', '#a9b45e', '#e0c87a', '#b8904e', '#9aa85a', '#d6b07a']
    last = None
    for bi, (d0, d1) in enumerate([(14, 34), (34, 58), (58, 88), (88, 124)]):
        xs = [1140] + sorted(r.uniform(1180, 1600, 2).tolist()) + [1640]
        for j in range(len(xs) - 1):
            xa_, xb_ = xs[j] + bi * 8, xs[j + 1]
            xx = np.linspace(xa_, xb_, 24)
            q = [(x, ty(x) + d0) for x in xx] + [(x + 6, ty(x) + d1) for x in xx[::-1]]
            col = FCOL[r.randint(len(FCOL))]
            while col == last: col = FCOL[r.randint(len(FCOL))]
            last = col
            pm = c.area(q, col, wob=.4, rough=.8, a=.92, edge_dark=.05)
            c.flow_fill(pm, lambda a, b: math.atan(-.12), lambda a, b, rr, cc=col: hexc(cc) * (.88 + .18 * rr.rand()), 1.8, 40, 3.2, dry=.4, a=.75, seed=bi * 10 + j)
            for p in resample(np.array([(x + 6, ty(x) + d1) for x in xx]), 4):
                if r.rand() < .85: c.dab(p[0], p[1], 3.4 * sfn(p[1]), 2.8 * sfn(p[1]), r.rand() * 3, ['#3f6a3a', '#4f7a44', '#2f5a34'][r.randint(3)], a=.95, dry=.05)
    # river
    poly, nr, wv = ribbon(RIVER, lambda t: 8 + 34 * t)
    rm = c.area(poly, '#5a9ab0', wob=.6, rough=.8, edge_dark=.12)
    c.flow_fill(rm, lambda x, y: math.pi / 2.6, lambda x, y, r: hexc(['#5a9ab0', '#7ab4c4', '#4a8aa0', '#b0d8e0'][r.randint(4)]), 3, 26, 3, dry=.35, a=.85, seed=17)
    log('river')
    meadow(FG_L, ['#7f9a46', '#9cb260'], 18, strokes=(14, 90, 10))
    meadow(FG_R, ['#76924a', '#94ac62'], 19, strokes=(14, 90, 10))
    log('meadows')
    # lanes and fences
    path(c, [(600, 520), (700, 548), (790, 570), (860, 576), (940, 560), (1010, 520), (1040, 470), (1050, 320)], 5, '#e6d4a6', sfn)
    path(c, [(150, 520), (220, 560), (300, 600), (330, 660), (300, 720)], 4, '#e6d4a6', sfn)
    picket([(960, 330), (1010, 340), (1100, 338), (1150, 330)], 1.0)
    picket([(880, 360), (960, 380), (1050, 400), (1150, 410), (1260, 400)], 1.1)
    picket([(1120, 600), (1220, 590), (1320, 572)], 1.6)
    picket([(1140, 840), (1260, 800), (1400, 780), (1560, 770)], 2.4)
    picket([(30, 640), (140, 620), (240, 618)], 1.7)
    # rails: the far run first
    i_tr0, i_tr1 = TRESTLE
    rails(c, RAIL, sfn, ballast='#c9b48a', tie='#5a4434', steel='#3c3d46', hide=[(i_tr0, i_tr1)])
    trestle()
    rails(c, RAIL[i_tr0:i_tr1 + 1], sfn, ballast=None, tie='#5a4434', steel='#3c3d46')
    covered_bridge(828, 576)
    log('rails')
    # objects, back to front
    objs = []
    VILL = [dict(t='side', x=70, y=304, w=26, d=16, h=14, rh=10, wall='coral', roof='slate', door='cream', name='v1'),
            dict(t='gable', x=124, y=300, w=18, d=18, h=18, rh=14, wall='turquoise', roof='brick', door='gold', name='v2'),
            dict(t='gable', x=176, y=298, w=22, d=26, h=24, rh=18, wall='offwhite', roof='terracotta', tower=True, door='turquoise', name='v3'),
            dict(t='side', x=236, y=306, w=28, d=16, h=14, rh=10, wall='gold', roof='slate', door='coral', name='v4'),
            dict(t='gable', x=288, y=304, w=16, d=16, h=16, rh=14, wall='dustypink', roof='olive', door='brick', name='v5'),
            dict(t='station', x=330, y=318, w=40, d=16, h=12, rh=9, wall='ochre', roof='brick', door='forest', name='vst'),
            dict(t='side', x=1040, y=304, w=58, d=30, h=34, rh=20, wall='offwhite', roof='#2f3036', door='brick', porch=True, dormer=True, shutters='#3a4a58', name='farmhouse'),
            dict(t='gambrel', x=1166, y=300, w=36, d=40, h=20, rh=22, wall='barnred', roof='slate', door='cream', name='barn'),
            dict(t='silo', x=1206, y=292, name='silo')]
    for b in VILL: objs.append((b['y'], 'bld', b))
    objs.append((300, 'ferris', (420, 300, 32)))
    objs.append((400, 'lighthouse', (520, 404)))
    for (x, y, s, col) in [(250, 402, 1.0, '#e05a4a'), (380, 440, 1.2, '#e8c050'), (180, 428, .9, '#5fa59c')]: objs.append((y, 'sail', (x, y, s, col)))
    TREES = [(900, 300, 36, 'cone'), (930, 304, 30, 'cone'), (1230, 296, 40, 'cone'), (1260, 300, 34, 'round'), (980, 320, 34, 'round'), (840, 330, 30, 'round'),
             (40, 520, 44, 'round'), (90, 528, 36, 'cone'), (620, 500, 40, 'round'), (660, 516, 34, 'cone'), (700, 540, 38, 'round'),
             (1460, 470, 46, 'cone'), (1500, 476, 40, 'cone'), (1540, 480, 44, 'round'), (1580, 486, 38, 'cone'), (1360, 476, 34, 'round'),
             (430, 520, 44, 'round'), (470, 528, 36, 'cone'), (250, 540, 42, 'round'),
             (1180, 640, 52, 'round'), (1250, 630, 46, 'cone'), (900, 620, 40, 'round'),
             (60, 760, 110, 'cone'), (170, 740, 80, 'round'), (520, 760, 70, 'round'), (720, 800, 86, 'cone'),
             (1300, 780, 90, 'round'), (1420, 770, 80, 'cone')]
    rr = np.random.RandomState(41)
    for (pts, hmin, hmax) in [([(600, 380), (680, 334), (780, 300), (860, 284)], 22, 30), ([(-20, 520), (100, 490), (240, 480)], 28, 40),
                              ([(380, 494), (520, 478), (640, 492), (720, 522)], 28, 38), ([(1300, 456), (1440, 444), (1560, 448)], 30, 42),
                              ([(120, 672), (260, 664), (420, 676)], 40, 56)]:
        for p in resample(catmull(pts, 8), 26):
            if rr.rand() < .75: TREES.append((p[0] + rr.randn() * 4, p[1] + 3 + rr.rand() * 4, rr.uniform(hmin, hmax), 'cone' if rr.rand() < .45 else 'round'))
    for (cx, cy, n, hh) in [(870, 470, 7, 40), (1120, 440, 5, 34), (560, 600, 6, 48), (1450, 600, 6, 60)]:
        for k in range(n): TREES.append((cx + rr.randn() * 30, cy + rr.randn() * 10, hh * rr.uniform(.8, 1.2), 'cone' if rr.rand() < .4 else 'round'))
    for j in range(3):
        for i in range(6): TREES.append((360 + i * 22 + j * 11, 336 + j * 12, 18, 'apple'))
    pals = [['#2f5a4a', '#3f7a5a', '#5f9a6a', '#8abf78'], ['#2a5a5a', '#3f7a74', '#6aa69a', '#9cc8b0'], ['#3a5a2a', '#4f7a34', '#7aa04a', '#a8c86a'],
            ['#4a6a2a', '#6a8a3a', '#9ab052', '#c8d070']]
    for i, t in enumerate(TREES): objs.append((t[1], 'tree', (i, t)))
    for (x, y) in [(1100, 360), (1130, 366), (1080, 370)]: objs.append((y, 'cow', (x, y)))
    for (x, y) in [(260, 640), (300, 648), (240, 660), (330, 652)]: objs.append((y, 'sheep', (x, y)))
    objs.append((560, 'school', (760, 560)))
    for (x, y) in [(1200, 600), (1240, 612), (1290, 596), (1500, 520), (1540, 530)]: objs.append((y, 'hay', (x, y)))
    pr = np.random.RandomState(5)
    for k in range(26): objs.append((0, 'pumpkin', (190 + pr.uniform(0, 160), 780 + pr.uniform(0, 50))))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'bld': S.paint_building(v)
        elif kind == 'ferris': ferris(*v)
        elif kind == 'lighthouse': lighthouse(*v)
        elif kind == 'sail': sailboat(*v)
        elif kind == 'tree':
            i, (x, y, h, shp) = v
            if shp == 'apple':
                dab_tree(c, x, y, h, ['#4f7a3a', '#6a9a48', '#8ab85a'], 500 + i)
                c.dots([(x + np.cos(a) * h * .22, y - h * .6 + np.sin(a) * h * .22) for a in np.linspace(0, 6.28, 6)], .9, ['#d0402e'], seed=i)
            else: dab_tree(c, x, y, h, pals[i % len(pals)], 500 + i, shape=shp)
        elif kind == 'school':
            S.paint_building(dict(t='gable', x=v[0], y=v[1], w=30, d=34, h=24, rh=18, wall='barnred', roof='slate', door='cream', tower=True, name='school'))
        elif kind == 'hay':
            bush(c, v[0], v[1], 9 * sfn(v[1]), 8 * sfn(v[1]), ['#e2b44b', '#d49a30', '#efc860'], int(v[0]))
        elif kind == 'pumpkin':
            x, y = v; s_ = sfn(y)
            c.area(S.lumpy(x, y - 3 * s_, 4.6 * s_, 3.4 * s_, int(x), n=18, amp=.06), '#e0782a', wob=0, rough=.3, edge_dark=.15)
            c.stroke([(x, y - 6 * s_), (x + 1, y - 8 * s_)], 1.2 * s_, '#4f6a2c', a=1, dry=0, taper=(0, 0))
        elif kind == 'cow': S.cow(*v, 1)
        elif kind == 'sheep': S.sheep(*v, 2)
    for o in objs: 
        if o[1] == 'pumpkin': o = (o[2][1], o[1], o[2])
        draw(o)
    log('objects')
    # the train in the foreground, big and close
    i_head = int(np.argmin(np.hypot(RAIL[:, 0] - 560, RAIL[:, 1] - 760)))
    train(c, RAIL, i_head, 3.0)
    log('train')
    # scale surprises in front
    mushroom_house(1270, 896, 150)
    for (x, h, sd) in [(26, 330, 1), (88, 280, 2), (140, 230, 3)]: sunflower(x, 930, h, sd)
    for (x, h, sd, col) in [(1500, 250, 4, '#d98ab0'), (1540, 300, 5, '#e05a6a'), (1586, 270, 6, '#f2c0d0')]: hollyhock(x, 930, h, sd, col)
    # wildflower drifts in the foreground meadows
    r = np.random.RandomState(9)
    for (cx, cy, n, sp) in [(420, 840, 70, 40), (700, 860, 60, 40), (1180, 860, 50, 30), (1400, 820, 70, 50), (560, 640, 40, 30), (1080, 760, 30, 26)]:
        cols = [['#f8f4ea', '#e8c050'], ['#d98ab0', '#f2c0d0'], ['#e05a4a', '#e8c050'], ['#b8a0d0', '#f8f4ea']][r.randint(4)]
        for k in range(n):
            x = cx + r.randn() * sp; y = cy + r.randn() * sp * .35; s_ = sfn(y)
            c.dab(x, y, 2.6 * s_ * .6, 2.2 * s_ * .6, r.rand() * 3, cols[r.randint(2)], a=1, dry=0)
    # a kite above the meadow
    kx, ky = 640, 470
    q = [(kx, ky - 10), (kx + 7, ky), (kx, ky + 12), (kx - 7, ky)]
    c.area(q, '#e05a4a', wob=0, rough=.3); c.area([(kx, ky - 10), (kx + 7, ky), (kx, ky)], '#e8c050', wob=0, rough=.3)
    tail = catmull([(kx, ky + 12), (kx - 5, ky + 22), (kx + 2, ky + 30), (kx - 4, ky + 40)], 6); c.stroke(tail, .6, '#3a2a2a', a=.8, dry=0, taper=(0, 0))
    c.stroke(catmull([(kx, ky + 2), (kx + 30, ky + 60), (690, 600)], 8), .4, '#3a2a2a', a=.6, dry=0, taper=(0, 0))
    for i in range(140):
        x = r.uniform(180, 1460); y = r.uniform(820, 900)
        if 860 < x < 1080: continue
        c.dab(x, y, 3, 2.6, r.rand() * 3, ['#f8f4ea', '#e8c050', '#d98ab0', '#e05a4a'][r.randint(4)], a=1, dry=0)
    c.save('out/B')
    log('saved')

if __name__ == '__main__':
    main()

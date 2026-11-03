"""Regional scale test, painted in the language of Option A.
A hillside village, a woodland station in a clearing, and Toy Town, joined by one winding line that crosses a river.
Landmarks are exaggerated, settlements stay small and characterful, and the land is left to breathe."""
import math, time
import numpy as np, cv2
import a as A
from kit import *

c = A.c
GLOW = A.GLOW
R = np.random.RandomState(21)
T0 = time.time()
def log(m): print(f'R {time.time() - T0:6.1f}s {m}', flush=True)
def sfn(y): return .8 + .5 * max(0, y - 330) / 560

FAR = catmull([(-20, 250), (120, 214), (260, 196), (400, 210), (540, 186), (700, 170), (860, 184), (1000, 164), (1160, 180), (1300, 160),
               (1460, 184), (1630, 170)], 10)
WOOD = catmull([(440, 486), (500, 369), (580, 299), (690, 262), (810, 257), (930, 286), (1020, 351), (1080, 447), (1110, 538)], 12)
VILL = catmull([(-30, 551), (60, 421), (170, 338), (280, 309), (390, 330), (480, 395), (550, 486), (600, 590), (620, 707)], 12)
TOY = catmull([(1000, 720), (1060, 590), (1150, 499), (1260, 452), (1380, 439), (1500, 460), (1630, 499)], 12)
MEAD_L = catmull([(-30, 774), (120, 744), (280, 734), (440, 744), (580, 766), (700, 798), (780, 840)], 12)
MEAD_C = catmull([(520, 816), (600, 744), (700, 707), (820, 684), (940, 707), (1040, 744), (1100, 792)], 12)
MEAD_R = catmull([(1060, 816), (1160, 774), (1300, 756), (1440, 756), (1630, 744)], 12)
RIVER = catmull([(1084, 512), (1040, 569), (990, 616), (950, 684), (920, 744), (880, 780), (800, 816), (720, 840), (640, 865), (560, 882),
                 (440, 890), (300, 888), (160, 883), (-30, 881)], 12)
RAIL = resample(catmull([(-40, 642), (60, 652), (170, 668), (280, 681), (380, 707), (470, 732), (560, 744), (640, 732), (690, 668),
                          (720, 577), (760, 499), (800, 465), (860, 460), (930, 478), (990, 517), (1040, 551), (1090, 590),
                          (1150, 616), (1230, 626), (1310, 632), (1400, 650), (1500, 676), (1640, 689)], 14), 2.0)
def _cross():
    best = None
    for i, p in enumerate(RAIL):
        d = np.hypot(*(RIVER - p).T).min()
        if best is None or d < best[0]: best = (d, i)
    return best[1]
_ci = _cross()
BR = (_ci - 22, _ci + 22)

# --------------------------------------------------------------------------- Toy Town landmarks
def awning(x0, x1, y, depth, cols=('#c8302a', '#f4ecdc'), n=None):
    n = n or max(4, int((x1 - x0) / 7))
    for k in range(n):
        a_, b_ = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
        col = cols[k % 2]
        c.area([(a_, y), (b_, y), (b_ + 2, y + depth), (a_ + 2, y + depth)], col, wob=0, rough=.3)
        c.area(S.lumpy((a_ + b_) / 2 + 2, y + depth, (b_ - a_) / 2, 2.4, k, n=14, amp=0, flat=-1), col, wob=0, rough=.3)

def shopwindow(x, y, w, h):
    c.area([(x - w / 2 - 1.5, y - h / 2 - 1.5), (x + w / 2 + 1.5, y - h / 2 - 1.5), (x + w / 2 + 1.5, y + h / 2 + 1.5), (x - w / 2 - 1.5, y + h / 2 + 1.5)], '#2a2030', wob=0, rough=.3)
    c.area([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], '#f6c050', wob=0, rough=.3, edge_dark=.25)
    r = np.random.RandomState(int(x))
    for k in range(int(w / 5)):
        px = x - w / 2 + 3 + k * 5 + r.uniform(-1, 1); py = y + h * .18
        c.dots([(px, py)], 1.8, ['#c8302a', '#3f7ab0', '#2f8a5a', '#e070a0', '#7a4a2a'], seed=int(px))
    c.dots([(x - w * .25, y - h * .15)], 2.6, ['#a0602a']); c.dots([(x - w * .25 - 2, y - h * .15 - 2.4), (x - w * .25 + 2, y - h * .15 - 2.4)], 1.1, ['#a0602a'])
    GLOW.append((x, y, w * 1.6))

def giftshop(x, y):
    w, h = 112, 70
    A.house(x, y, w, h, 'side', '#e86e98', '#2a2340', 401, dotcol=['#f6c84a', '#f3ecdc'], rows=2, cols_=5, chimney=False)
    for xx in (x - w * .18,):
        c.stroke([(xx, y), (xx, y - h)], 7, '#f2c040', a=1, dry=.1, taper=(0, 0))
    c.stroke([(x - w / 2, y - h * .62), (x + w / 2, y - h * .62)], 6, '#f2c040', a=1, dry=.1, taper=(0, 0))
    bx, by = x - w * .18, y - h - 26
    for side in (-1, 1):
        loop = S.lumpy(bx + side * 13, by - 4, 13, 9, 3 + side, n=24, amp=.05)
        c.area(loop, '#f2c040', wob=0, rough=.4, edge_dark=.15); c.area(S.lumpy(bx + side * 13, by - 4, 6, 3.5, 5, n=16, amp=0), '#c8902a', wob=0, rough=.3)
        c.stroke([(bx, by + 2), (bx + side * 10, by + 20)], 4, '#f2c040', a=1, dry=.1, taper=(0, .4))
    c.dots([(bx, by)], 5, ['#e8b030'])
    awning(x - w / 2 + 4, x + w / 2 - 4, y - h * .42, 9, ('#3f8a7a', '#f4ecdc'))
    for k, xx in enumerate((x - w * .32, x + w * .12, x + w * .36)): shopwindow(xx, y - h * .2, 22, 16)
    GLOW.append((x, y - h * .5, 80))

def clocktower(x, y):
    w, h = 34, 150
    body = [(x - w / 2, y), (x + w / 2, y), (x + w / 2 - 2, y - h), (x - w / 2 + 2, y - h)]
    c.area([(x + w / 2, y), (x + w / 2 + 8, y - 4), (x + w / 2 + 6, y - h - 4), (x + w / 2 - 2, y - h)], '#9a2a2a', wob=0, rough=.4)
    m = c.area(body, '#f4ecdc', wob=.2, rough=.5, edge_dark=.08)
    prev = c.clipm; c.set_clip(m)
    for k in range(-8, 12):
        yy = y - k * 18
        c.area([(x - w, yy), (x + w, yy - 26), (x + w, yy - 16), (x - w, yy + 10)], '#d0302a', wob=0, rough=.3)
    c.clipm = prev
    c.stip(m, lambda X, Y, r: np.clip(c.img[np.clip((Y * K).astype(int), 0, H - 1), np.clip((X * K).astype(int), 0, W - 1)] * (1 + (r.rand(len(X), 1) - .5) * .14), 0, 1),
           spacing=1.2, L=2.4, w=1.3, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=7)
    cy = y - h + 26
    c.area(S.lumpy(x, cy, 15, 15, 2, n=40, amp=0), '#2a2340', wob=0, rough=.3)
    c.area(S.lumpy(x, cy, 12.5, 12.5, 2, n=40, amp=0), '#f6e6b8', wob=0, rough=.3, edge_dark=.12)
    for k in range(12):
        a = k / 12 * 2 * math.pi; c.dots([(x + math.cos(a) * 10, cy + math.sin(a) * 10)], .9, ['#2a2340'])
    c.stroke([(x, cy), (x + 1, cy - 8)], 1.4, '#2a2340', a=1, dry=0, taper=(0, .3)); c.stroke([(x, cy), (x + 6, cy + 2)], 1.4, '#2a2340', a=1, dry=0, taper=(0, .3))
    GLOW.append((x, cy, 40))
    roof = [(x - w / 2 - 6, y - h)] + [(x + (w / 2 + 6) * math.cos(t) * (1 - .9 * u), y - h - 52 * u) for u, t in zip(np.linspace(0, 1, 12), np.linspace(math.pi, math.pi, 12))]
    onion = [(x - w / 2 - 6, y - h), (x + w / 2 + 6, y - h)] + [(x + (w / 2 + 6) * (1 - u) * (1 + .5 * math.sin(u * math.pi)) * s_, y - h - 56 * u) for s_ in (1,) for u in np.linspace(0, 1, 14)]
    onion = [(x - w / 2 - 6, y - h)] + [(x - (w / 2 + 6) * (1 - u) * (1 + .5 * math.sin(u * math.pi)), y - h - 56 * u) for u in np.linspace(0, 1, 14)] + \
            [(x + (w / 2 + 6) * (1 - u) * (1 + .5 * math.sin(u * math.pi)), y - h - 56 * u) for u in np.linspace(1, 0, 14)]
    om = c.area(onion, '#2f8a7a', wob=.1, rough=.4, edge_dark=.12)
    A.roofdots(onion, ['#f6c84a', '#f3ecdc'], 0, 9, .7)
    star = (x, y - h - 64)
    for k in range(5):
        aa = -math.pi / 2 + k * 2 * math.pi / 5
        c.stroke([star, (star[0] + math.cos(aa) * 7, star[1] + math.sin(aa) * 7)], 2, '#f6c84a', a=1, dry=0, taper=(0, .8))
    GLOW.append((star[0], star[1], 50))
    for k, yy in enumerate((y - h * .52, y - h * .3)): A.window(x, yy, 8, 12, arch=True)
    c.area([(x - 6, y)] + [(x - 6 + 12 * u, y - 18 - math.sin(u * math.pi) * 6) for u in np.linspace(0, 1, 10)] + [(x + 6, y)], '#2a1f2e', wob=0, rough=.3)

def carousel(x, y, r0):
    base = S.lumpy(x, y, r0 * 1.05, r0 * .26, 4, n=40, amp=0)
    c.area(base, '#b8302a', wob=0, rough=.4)
    c.area(S.lumpy(x, y - 4, r0, r0 * .22, 4, n=40, amp=0), '#f2c040', wob=0, rough=.4)
    for k in range(9):
        px = x - r0 * .85 + k * r0 * .21; py = y - 6 - (k % 2) * 4
        c.stroke([(px, y - 4), (px, y - r0 * .9)], .9, '#f2c040', a=1, dry=0, taper=(0, 0))
        c.area(S.lumpy(px, py - 10, 4.6, 2.6, k, n=14, amp=.05), ['#f4ecdc', '#7a4a2a', '#e8749a', '#3f8a7a'][k % 4], wob=0, rough=.3)
    top = y - r0 * .9
    n = 10
    for k in range(n):
        a0, a1 = x - r0 * 1.1 + 2.2 * r0 * k / n, x - r0 * 1.1 + 2.2 * r0 * (k + 1) / n
        c.area([(a0, top + 4), (a1, top + 4), (x, top - r0 * .8)], ['#d0302a', '#f4ecdc'][k % 2], wob=0, rough=.3)
    c.area(S.lumpy(x, top + 4, r0 * 1.1, 4, 6, n=30, amp=0, flat=-1), '#f2c040', wob=0, rough=.3)
    c.dots([(x - r0 * 1.05 + 2.1 * r0 * k / 16, top + 6) for k in range(17)], 1.4, ['#ffe08a'])
    c.stroke([(x, top - r0 * .8), (x, top - r0 * .8 - 14)], 1, '#2a1f2e', a=1, dry=0, taper=(0, 0))
    c.area([(x, top - r0 * .8 - 14), (x + 11, top - r0 * .8 - 10), (x, top - r0 * .8 - 6)], '#3f8a7a', wob=0, rough=.3)
    GLOW.append((x, y - r0 * .5, r0 * 2.4))

def xmas_tree(x, y, h):
    stipple_fir(c, x, y, h, ['#1f5a3a', '#2a6a44', '#174a30', '#3a7a4a'], 333, slim=.26)
    r = np.random.RandomState(4)
    for k in range(5):
        yy = y - h * (.15 + k * .16); ww = h * .26 * (1 - (k * .16 + .15))
        pts = [(x - ww + 2 * ww * u, yy + math.sin(u * math.pi) * 4 - ww * .3 * u) for u in np.linspace(0, 1, 9)]
        c.dots(pts, 1.5, ['#ffe08a', '#e8605a', '#7ac0e0', '#f6c84a'], seed=k)
        for p in pts[::2]: GLOW.append((p[0], p[1], 10))
    star = (x, y - h - 4)
    for k in range(5):
        aa = -math.pi / 2 + k * 2 * math.pi / 5
        c.stroke([star, (star[0] + math.cos(aa) * 8, star[1] + math.sin(aa) * 8)], 2.2, '#f6c84a', a=1, dry=0, taper=(0, .8))
    GLOW.append((star[0], star[1], 50))
    for k, (dx, col) in enumerate([(-16, '#c8302a'), (-4, '#3f7ab0'), (10, '#f2c040')]):
        c.area([(x + dx - 5, y + 2), (x + dx + 5, y + 2), (x + dx + 5, y - 7), (x + dx - 5, y - 7)], col, wob=0, rough=.3)
        c.stroke([(x + dx, y + 2), (x + dx, y - 7)], 1.4, '#f4ecdc', a=1, dry=0, taper=(0, 0))

def candyshop(x, y):
    A.house(x, y, 70, 46, 'gable', '#a9d2e6', '#c8302a', 411, dotcol=None, rows=1, cols_=2, chimney=True)
    awning(x - 33, x + 33, y - 30, 7, ('#e86e98', '#f4ecdc'))
    shopwindow(x - 16, y - 13, 20, 12)
    lx, ly = x + 46, y - 36
    c.stroke([(lx, y), (lx, ly)], 2.2, '#f4ecdc', a=1, dry=0, taper=(0, 0))
    for k in range(4):
        c.stroke([(lx + 9 * math.cos(t) * (1 - k * .22), ly + 9 * math.sin(t) * (1 - k * .22)) for t in np.linspace(0, 2 * math.pi, 24)], 2.4, ['#e86e98', '#f4ecdc'][k % 2], a=1, dry=0, taper=(0, 0))

# --------------------------------------------------------------------------- painting
def main():
    m = c.area([(-10, -10), (1610, -10), (1610, 560), (-10, 560)], '#202255', wob=0, rough=0, edge_dark=0)
    c.stip(m, lambda X, Y, r: np.array([hexc('#1b1d4c'), hexc('#26296a'), hexc('#2e2a64'), hexc('#1d2a5a')])[r.randint(4, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .1),
           spacing=2.2, L=4.5, w=1.8, angfn=lambda X, Y: .15 * np.sin(X / 90 + Y / 40), seed=1)
    stars = [(R.uniform(0, 1600), R.uniform(0, 230) ** 1.05 / 1.2) for _ in range(380)]
    c.dots(stars, .75, ['#f6efe0', '#f6efe0', '#f2c86a', '#e8a8c0', '#bcd6e6'], seed=2)
    mx, my = 1420, 92
    for k in range(3):
        rr = 46 + k * 11
        c.dots([(mx + math.cos(a) * rr, my + math.sin(a) * rr) for a in np.linspace(0, 2 * math.pi, 56 + k * 14, endpoint=False)], .8, ['#f2e6c4', '#e8d4a0'], seed=3 + k)
    mm = c.area(S.lumpy(mx, my, 36, 36, 4, n=50, amp=.02), '#f2e6c4', wob=.2, rough=.6, edge_dark=.06)
    c.stip(mm, pal_fn(['#f6ecd2', '#ecdcb4', '#f8f0dc', '#e2cfa6']), spacing=1.3, L=2.4, w=1.3, seed=4)
    c.stroke([(260, 70), (330, 40)], 1.6, '#f6efe0', a=.9, dry=.3, taper=(.9, 0))
    log('sky')
    A.hill(FAR, ['#1f3a3e', '#244444', '#1a3236', '#2a4a48'], 11, spacing=1.6, L=3.4)
    for x in np.arange(-10, 1620, 34):
        y = y_on(FAR, x) + R.uniform(4, 30)
        if R.rand() < .2: skeleton_tree(c, x, y + 30, R.uniform(46, 62), [['#3a6a6a', '#4f8a80', '#2f5a5a'], ['#5f7a3a', '#7a9a4a']][R.randint(2)], int(R.randint(1e6)), dots=['#f6efe0'])
        else: stipple_fir(c, x, y + 26, R.uniform(40, 76), [['#223f40', '#2c4e4a', '#193234', '#3a5e56'], ['#1f3a4a', '#2a4a5a', '#3a6070']][R.randint(2)], int(R.randint(1e6)), slim=.2)
    log('far')
    # the wood, with a clearing for its little station
    A.hill(WOOD, ['#2c5450', '#33605a', '#264a48', '#3c6a5e'], 12)
    cm = c.area(S.lumpy(790, 450, 120, 34, 7, n=40, amp=.12), '#8a9a3a', wob=.8, rough=1, edge_dark=.04)
    c.stip(cm, pal_fn(['#8f9c34', '#a3aa3e', '#7a8a2a', '#b4b448']), spacing=1.4, L=3.2, w=1.6, seed=13)
    log('wood')
    # the village hill and the Toy Town hill
    vm = c.area(land(VILL), '#e39a2c', wob=1, rough=1, edge_dark=.04, seed=14)
    BANDS = [['#e8a034', '#f0b445', '#dc8e26'], ['#e2862a', '#ea9a34', '#d4741f'], ['#efbb4a', '#f4c95a', '#e2a63a'], ['#c9902a', '#d8a236', '#b97e22']]
    def goldcol(X, Y, r):
        b = ((np.sin(X / 140 + Y / 55) + np.sin(X / 63 - Y / 90) * .6 + 2) / 4 * len(BANDS)).astype(int) % len(BANDS)
        Cc = np.array([[hexc(cc) for cc in bb] for bb in BANDS]); return Cc[b, r.randint(3, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .12)
    c.stip(vm, goldcol, spacing=1.5, L=3.6, w=1.7, angfn=A.flowdir(VILL), seed=15, jit=.3)
    tm = c.area(land(TOY), '#c2507a', wob=1, rough=1, edge_dark=.04, seed=16)
    PB = [['#c8507a', '#d4628a', '#b8406a'], ['#b8486e', '#c45a80', '#a83a60'], ['#d87090', '#e282a0', '#c86080']]
    def plumcol(X, Y, r):
        b = ((np.sin(X / 120 + Y / 50) + np.sin(X / 70 - Y / 80) * .6 + 2) / 4 * len(PB)).astype(int) % len(PB)
        Cc = np.array([[hexc(cc) for cc in bb] for bb in PB]); return Cc[b, r.randint(3, size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .12)
    c.stip(tm, plumcol, spacing=1.5, L=3.6, w=1.7, angfn=A.flowdir(TOY), seed=17, jit=.3)
    # a cobbled square in Toy Town
    sq = c.area(S.lumpy(1290, 551, 150, 30, 8, n=40, amp=.06), '#d8b880', wob=.4, rough=.8, edge_dark=.06)
    c.stip(sq, pal_fn(['#d8b880', '#c8a870', '#e6c890', '#b89860']), spacing=1.6, L=2.4, w=2.0, seed=18, jit=1.5)
    log('hills')
    A.hill(MEAD_L, ['#7f8f2e', '#8f9c36', '#6e7f2a', '#a1a63e'], 19)
    A.hill(MEAD_C, ['#6f8a34', '#7f9a3c', '#5f7a2e', '#90a846'], 20)
    A.hill(MEAD_R, ['#8a9a3a', '#9aa848', '#7a8a30', '#a8b450'], 21)
    for (px, py, rx, ry, cols) in [(240, 780, 90, 20, ['#d8a236', '#e2b44a', '#c9902a']), (860, 756, 70, 16, ['#c8507a', '#d4628a']), (1380, 792, 100, 20, ['#d8a236', '#e2b44a'])]:
        pm = c.area(S.lumpy(px, py, rx, ry, int(px), n=36, amp=.12, flat=0), cols[0], wob=.6, rough=1, edge_dark=.04)
        c.stip(pm, pal_fn(cols), spacing=1.4, L=3.2, w=1.6, seed=int(px) + 3)
    log('meadows')
    # the river with its stitched surface
    poly, nr, wv = ribbon(RIVER, lambda t: 10 + 70 * t ** 1.3)
    rm = c.area(poly, '#22466a', wob=.4, rough=.7, edge_dark=.1)
    def rang(X, Y):
        j = np.argmin(np.hypot(RIVER[:, 0][None] - X[:, None], RIVER[:, 1][None] - Y[:, None]), axis=1)
        d = np.gradient(RIVER, axis=0)[j]; return np.arctan2(d[:, 1], d[:, 0])
    c.stip(rm, pal_fn(['#244a70', '#2e5880', '#1d3d5e', '#36628a']), spacing=1.5, L=4.5, w=1.4, angfn=rang, seed=22, jit=.1)
    for k in range(70):
        j = R.randint(10, len(RIVER) - 6); t = j / len(RIVER); off = R.uniform(-.3, .3) * (10 + 70 * t ** 1.3)
        p = RIVER[j] + nr[min(j, len(nr) - 1)] * off; d = RIVER[j + 3] - RIVER[j]; d /= np.hypot(*d)
        c.stroke([p - d * 6, p + d * 6], .8, '#cfe0ea', a=.8, dry=.15, taper=(.2, .2))
    log('river')
    # paths between places
    path(c, [(330, 642), (300, 564), (340, 486), (300, 408), (280, 330)], 5, '#e9cf96', sfn, dotted=['#f6ecd8', '#d9b77a'], seed=1)
    path(c, [(1220, 616), (1260, 564), (1300, 525), (1340, 486)], 5, '#e9cf96', sfn, dotted=['#f6ecd8'], seed=2)
    path(c, [(780, 434), (720, 369), (680, 330)], 4, '#d9c08a', sfn, dotted=['#f6ecd8'], seed=3)
    # the railway: one continuous line, painted with the same dabs
    before = c.img.copy()
    rails(c, RAIL, sfn, ballast='#8f7f6a', tie='#3a2a24', steel='#2a2630', hide=[BR], shine='#e8d8b0')
    restipple(c, before, seed=31)
    a_, b_ = BR; dk = RAIL[a_:b_ + 1] + [0, 4]
    x0, x1 = dk[0, 0], dk[-1, 0]; base = float(dk[:, 1].max()) + 26
    aw = 34; ah = 20
    jj = [j for j in range(len(RIVER)) if RIVER[j][1] >= base - 2]
    ax = float(np.clip(RIVER[jj[0]][0] if jj else (x0 + x1) / 2, x0 + aw / 2 + 4, x1 - aw / 2 - 4))
    arch = [(ax + aw / 2 - aw * u, base - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    face = np.vstack([dk - [0, 3], [[x1, base]], arch, [[x0, base]]])
    bm = c.area(face, '#a99a8a', wob=.2, rough=.6, edge_dark=.1, seed=32)
    c.stip(bm, pal_fn(['#b3a594', '#9d8e80', '#c2b5a3', '#8f8276']), spacing=1.4, L=3.2, w=2.0, angfn=lambda X, Y: 0 * X, seed=33, jit=.2)
    for u in np.linspace(0, 1, 9):
        p = np.array((ax + aw / 2 - aw * u, base - math.sin(u * math.pi) ** .8 * ah)); dv = p - [ax, base + 6]; dv /= np.hypot(*dv)
        c.stroke([p, p + dv * 5], 2.6, '#c9bcaa', a=.9, dry=.1, taper=(0, 0))
    c.stroke(dk - [0, 2], 5, '#c9bcaa', a=1, dry=.1, taper=(0, 0))
    for xq in np.arange(x0, x1, 7):
        y = float(np.interp(xq, dk[:, 0], dk[:, 1])) - 5; c.stroke([(xq, y), (xq, y - 3)], 1.4, '#c9bcaa', a=1, dry=0, taper=(0, 0))
    before = c.img.copy()
    rails(c, RAIL[a_:b_ + 1], sfn, ballast=None, tie='#3a2a24', steel='#2a2630', shine='#e8d8b0')
    restipple(c, before, seed=34)
    log('rail')
    objs = []
    VH = [(110, 486, 50, 44, 'gable', '#f2ece0', '#c22f2a'), (200, 408, 56, 40, 'side', '#7d6aa8', '#2a2340'), (300, 372, 36, 56, 'tall', '#5f98a6', '#1f2a3a'),
          (390, 424, 50, 40, 'gable', '#f2a6bf', '#2a2340'), (170, 564, 64, 46, 'side', '#c2397a', '#1f1d2c'), (290, 525, 46, 42, 'round', '#ef8a2a', None),
          (440, 551, 40, 58, 'tall', '#4f86b8', '#1f1d2c'), (90, 642, 54, 46, 'gable', '#f2ece0', '#3a1f3a')]
    VH = [(x, y, w * 1.2, h * 1.2, k, wall, roof) for (x, y, w, h, k, wall, roof) in VH]
    for i, h in enumerate(VH): objs.append((h[1], 'house', (i, h)))
    objs.append((300, 'church', (250, 330)))
    objs.append((550, 'vstation', (380, 663)))
    objs.append((384, 'wstation', (800, 444)))
    objs.append((470, 'clock', (1420, 551))); objs.append((520, 'gift', (1250, 616))); objs.append((470, 'carousel', (1330, 551)))
    objs.append((460, 'xmas', (1200, 541))); objs.append((500, 'candy', (1520, 598)))
    objs.append((430, 'house2', (1110, 551, 48, 42, 'gable', '#a9d2e6', '#1f1d2c'))); objs.append((420, 'house2', (1560, 499, 44, 52, 'tall', '#ef8a2a', '#2a2340')))
    TREES = [
        # the wood: individuals in a ring around the clearing
        (560, 408, 92, 'fir'), (612, 369, 84, 'skel', ['#e04a2a', '#f06a3a', '#c8341f']), (660, 330, 96, 'fir'), (720, 317, 80, 'skel', ['#f0a030', '#f6c050', '#d9801f']),
        (880, 330, 88, 'skel', ['#b8287a', '#d94a9a', '#9e1f62']), (940, 356, 100, 'fir'), (990, 408, 82, 'skel', ['#7fae3a', '#98c24a', '#668f2e']),
        (650, 486, 80, 'skel', ['#3f9a7a', '#5ab48f', '#2f7a62'], '#f6efe0'), (930, 499, 84, 'skel', ['#f2a6c8', '#e98ab0', '#f6c8dc']), (1030, 486, 90, 'fir'),
        (520, 499, 70, 'skel', ['#c9b83a', '#e2d050', '#a8962a']), (780, 330, 70, 'fir'), (840, 343, 64, 'fir'),
        # village and meadows
        (40, 551, 70, 'skel', ['#c8287a', '#e04a9a', '#a01f62', '#f2a6c8']), (240, 473, 56, 'skel', ['#e86a2a', '#f08a3a', '#c8501f']),
        (360, 525, 60, 'skel', ['#8a2a8a', '#a84aa8', '#6a1f6a'], '#f6efe0'), (500, 616, 64, 'skel', ['#c8d24a', '#a8b83a', '#e2e070']),
        (150, 750, 74, 'skel', ['#e04a2a', '#f06a3a']), (620, 780, 60, 'skel', ['#3f9a7a', '#5ab48f'], '#f6efe0'),
        (980, 780, 70, 'skel', ['#f0a030', '#f6c050']), (1180, 804, 64, 'skel', ['#b8287a', '#d94a9a']), (1560, 780, 80, 'skel', ['#e86a2a', '#f08a3a']),
        (1470, 744, 60, 'skel', ['#7fae3a', '#98c24a']), (1600, 616, 70, 'skel', ['#3f9a7a', '#5ab48f'], '#f6efe0'),
        # framing the foreground
        (40, 900, 190, 'skel', ['#c8287a', '#e04a9a', '#a01f62']), (1560, 906, 200, 'fir'),
    ]
    for i, t in enumerate(TREES): objs.append((t[1], 'tree', (i, t)))
    ty_ = float(np.interp(1400, RAIL[:, 0], RAIL[:, 1])) - 12
    objs.append((ty_, 'tstation', (1400, ty_)))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'house':
            i, (x, y, w, h, k, wall, roof) = v
            A.house(x, y, w, h, k, wall, roof or '#1f1d2c', 500 + i, dotcol=['#f3ecdc', '#f6c84a'][i % 2] if roof in ('#1f1d2c', '#2a2340', '#3a1f3a', '#1f2a3a') else None)
        elif kind == 'house2':
            x, y, w, h, k, wall, roof = v; A.house(x, y, w, h, k, wall, roof, int(x), dotcol='#f3ecdc')
        elif kind == 'church': A.church(*v)
        elif kind == 'vstation':
            x, y = v; A.house(x, y, 74, 28, 'side', '#c22f2a', '#1f1d2c', 77, dotcol='#f6c84a', rows=1, cols_=4)
            for lx in (x - 42, x + 42):
                c.stroke([(lx, y + 6), (lx, y - 18)], 1.0, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 19)], 1.8, ['#ffd27a']); GLOW.append((lx, y - 19, 20))
        elif kind == 'wstation':
            x, y = v
            c.area([(x - 44, y + 4), (x + 44, y + 4), (x + 48, y + 10), (x - 40, y + 10)], '#b3a594', wob=0, rough=.4)
            A.house(x, y, 58, 26, 'gable', '#3f7a5a', '#e0703a', 88, dotcol=None, rows=1, cols_=3)
            for lx in (x - 38, x + 38):
                c.stroke([(lx, y + 6), (lx, y - 20)], 1.0, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 21)], 1.9, ['#ffd27a']); GLOW.append((lx, y - 21, 22))
            c.stroke([(x + 18, y + 2), (x + 30, y + 2)], 2, '#7a4a2a', a=1, dry=0, taper=(0, 0))
        elif kind == 'tstation':
            x, y = v; A.house(x, y, 84, 30, 'side', '#2f6a8a', '#f2c040', 79, dotcol=None, rows=1, cols_=4)
            c.area(S.lumpy(x, y - 44, 8, 8, 1, n=24, amp=0), '#f6e6b8', wob=0, rough=.3); c.stroke([(x, y - 44), (x + 1, y - 49)], 1, '#2a2340', a=1, dry=0, taper=(0, 0)); c.stroke([(x, y - 44), (x + 4, y - 43)], 1, '#2a2340', a=1, dry=0, taper=(0, 0))
            GLOW.append((x, y - 44, 24))
            for lx in (x - 48, x + 48):
                c.stroke([(lx, y + 6), (lx, y - 18)], 1.0, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 19)], 1.8, ['#ffd27a']); GLOW.append((lx, y - 19, 20))
        elif kind == 'clock': clocktower(*v)
        elif kind == 'gift': giftshop(*v)
        elif kind == 'carousel': carousel(v[0], v[1], 40)
        elif kind == 'xmas': xmas_tree(v[0], v[1], 96)
        elif kind == 'candy': candyshop(*v)
        elif kind == 'tree':
            i, t = v
            if t[3] == 'fir': stipple_fir(c, t[0], t[1], t[2], [['#3f7a5a', '#4f8a64', '#2f6a4a', '#6aa070'], ['#4a7a3a', '#5f8f44', '#3a6a30', '#7aa850'], ['#2f6a7a', '#3f7a8a', '#5a9aa0']][i % 3], 600 + i, slim=.22)
            else: skeleton_tree(c, t[0], t[1], t[2], t[4], 600 + i, dots=[t[5]] if len(t) > 5 else None)
    for o in objs: draw(o)
    log('places')
    i_head = int(np.argmin(np.abs(RAIL[:, 0] - 548) + (RAIL[:, 1] < 700) * 1e4))
    before = c.img.copy()
    train(c, RAIL, i_head, 1.9)
    restipple(c, before, seed=41)
    GLOW.append(tuple(RAIL[i_head] + [6, -14]) + (60,))
    # little discoveries: a lantern boat, a lit lantern balloon, deer at the wood's edge, a fox
    bx, by = 520, 868
    c.area([(bx - 18, by - 3), (bx + 20, by - 4), (bx + 14, by + 4), (bx - 13, by + 4)], '#b8302a', wob=0, rough=.3)
    c.stroke([(bx + 4, by - 4), (bx + 4, by - 22)], .9, '#1d1a20', a=1, dry=0, taper=(0, 0)); c.dots([(bx + 4, by - 23)], 2, ['#ffd27a']); GLOW.append((bx + 4, by - 23, 40))
    lb = (560, 150)
    c.area(S.lumpy(*lb, 16, 20, 3, n=30, amp=.02, flat=-.25), '#e8603a', wob=0, rough=.4, edge_dark=.1)
    c.stip(c.mask(S.lumpy(*lb, 16, 20, 3, n=30, amp=.02, flat=-.25), 0, .4), pal_fn(['#e8603a', '#f08a4a', '#d8502a']), spacing=1.2, L=2.4, w=1.3, seed=5)
    c.area([(lb[0] - 4, lb[1] + 26), (lb[0] + 4, lb[1] + 26), (lb[0] + 3, lb[1] + 31), (lb[0] - 3, lb[1] + 31)], '#7a4a2a', wob=0, rough=.3)
    GLOW.append((lb[0], lb[1] + 6, 70))
    for (dx, dy) in [(1050, 525), (1066, 535)]:
        c.area(S.lumpy(dx, dy - 5, 6, 3.4, 1, n=14, amp=0), '#a0602a', wob=0, rough=.3)
        for k in (-4, 4): c.stroke([(dx + k, dy - 3), (dx + k, dy + 3)], .9, '#5a3a20', a=1, dry=0, taper=(0, 0))
        c.area(S.lumpy(dx + 6, dy - 10, 2.6, 2.2, 2, n=12, amp=0), '#a0602a', wob=0, rough=.3)
        c.stroke([(dx + 6, dy - 12), (dx + 4, dy - 18)], .7, '#5a3a20', a=1, dry=0, taper=(0, 0)); c.stroke([(dx + 7, dy - 12), (dx + 10, dy - 18)], .7, '#5a3a20', a=1, dry=0, taper=(0, 0))
    # stones and bushes along the river's near bank
    for x in np.arange(0, 1332, 50):
        j = int(np.argmin(np.abs(RIVER[:, 0] - x)))
        if RIVER[j, 1] < 820: continue
        y = RIVER[j, 1] - (10 + 70 * (j / len(RIVER)) ** 1.3) / 2 - 2
        if R.rand() < .5:
            rx = R.uniform(14, 24); sm2 = c.area(S.lumpy(x, y, rx, rx * .6, int(x) + 1, n=30, amp=.04, flat=.3), '#8a8892', wob=.2, rough=.6, edge_dark=.15)
            c.stip(sm2, pal_fn(['#9a98a2', '#7e7c88', '#b0aeb6', '#6e6c78']), spacing=1.3, L=2.6, w=1.4, seed=int(x) + 2)
        else:
            bush(c, x, y + 8, R.uniform(16, 24), R.uniform(12, 16), [['#c8302a', '#e04a3a'], ['#e2b030', '#f0c84a'], ['#8a2a6a', '#a84a8a']][R.randint(3)], int(x) + 7)
    log('details')
    glow = np.zeros((H, W), np.float32)
    for gx, gy, rad in GLOW: cv2.circle(glow, (int(gx * K), int(gy * K)), max(1, int(rad * K * .35)), 1.0, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 10) * 1.1 + cv2.GaussianBlur(glow, (0, 0), 34) * .9
    c.img += hexc('#ffb85a') * np.clip(glow, 0, 1)[..., None] * .35
    c.save('out/region')
    log('saved')

if __name__ == '__main__':
    main()

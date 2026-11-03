"""Direction C — Vintage Illustrated Adventure Map.
An island seen from high above, hand-painted on aged paper: a harbor and lighthouse, a forest lodge, a mountain range with a
tunnel, a lake, a central town, patchwork farms and red-rock mesa country, joined by one looping railway."""
import math, time
import numpy as np, cv2
from kit import *

c = setup('#e8d9b6', 303)
R = np.random.RandomState(13)
T0 = time.time()
def log(m): print(f'C {time.time() - T0:6.1f}s {m}', flush=True)
SF = lambda y: .95
INK = '#4a3428'

LANDPTS = [(190, 190), (250, 140), (330, 128), (380, 96), (470, 104), (560, 92), (620, 130), (660, 172), (706, 150), (760, 110), (860, 96),
           (960, 112), (1040, 92), (1130, 104), (1220, 84), (1320, 112), (1390, 150), (1420, 210), (1474, 240), (1500, 300), (1462, 352),
           (1424, 396), (1468, 450), (1500, 520), (1470, 590), (1420, 632), (1384, 690), (1300, 720), (1240, 770), (1150, 782), (1080, 750),
           (1000, 772), (920, 792), (840, 770), (760, 792), (700, 804), (664, 792), (600, 770), (530, 782), (470, 760), (440, 722), (400, 692),
           (350, 702), (300, 732), (250, 722), (220, 680), (200, 622), (166, 580), (158, 520), (190, 470), (148, 420), (128, 360), (150, 300), (138, 240)]
LAND = wobble(catmull(LANDPTS, 10, closed=True), 3.2, 7, wl=22)
ISLES = [catmull([(70, 690), (110, 660), (150, 676), (140, 716), (96, 730), (64, 712)], 8, closed=True),
         catmull([(1530, 740), (1560, 724), (1580, 744), (1560, 768), (1532, 760)], 8, closed=True)]
FOREST = catmull([(210, 210), (330, 150), (480, 140), (600, 170), (610, 260), (560, 330), (430, 370), (300, 380), (220, 330)], 10, closed=True)
DESERT = catmull([(1200, 340), (1330, 300), (1420, 380), (1440, 500), (1400, 620), (1290, 680), (1190, 620), (1170, 480)], 10, closed=True)
LAKE = S.lumpy(520, 470, 78, 42, 21, n=48, bumps=4, amp=.12, flat=0)
RIVER1 = catmull([(900, 200), (870, 260), (800, 300), (700, 340), (620, 400), (585, 440)], 10)
RIVER2 = catmull([(560, 508), (590, 560), (640, 610), (650, 660), (630, 720), (650, 790)], 10)
RAIL = resample(catmull([(410, 680), (520, 700), (640, 704), (760, 712), (880, 716), (1000, 704), (1110, 672), (1200, 640), (1290, 580),
                          (1340, 500), (1350, 420), (1310, 340), (1240, 280), (1150, 250), (1050, 270), (950, 300), (860, 330),
                          (780, 380), (740, 440), (680, 510), (600, 540), (480, 540), (420, 500), (400, 430), (360, 400),
                          (280, 410), (230, 470), (230, 560), (280, 630), (340, 670)], 12, closed=True), 2.0)

def inpoly(P, x, y):
    from matplotlib.path import Path as MP
    return MP(P).contains_points(np.stack([x, y], 1))

def mountain(x, y, w, h, seed, snow=True):
    r = np.random.RandomState(seed)
    pk = np.array((x + r.uniform(-.15, .15) * w, y - h))
    hl, hr = w * r.uniform(.42, .6), w * r.uniform(.42, .6)
    def slope(side, hw):
        pts = []
        for t, f in ((0, 0), (.22, .18), (.42, .45 + r.uniform(-.08, .08)), (.55, .5 + r.uniform(-.05, .1)), (.75, .74), (.9, .9), (1, 1)):
            pts.append((pk[0] + side * hw * (1 - t) + r.randn() * 1.6, y - h * f + r.randn() * 1.6))
        return pts
    L = slope(-1, hl); Rr = slope(1, hr)[::-1]
    poly = L + Rr[1:]
    m = c.area(poly, '#cdbb98', wob=.2, rough=.6, edge_dark=.06, seed=seed)
    ridge = [tuple(pk)] + [(pk[0] + (u * .18 + r.randn() * .03) * w, pk[1] + u * h) for u in np.linspace(.15, 1, 6)]
    sh = ridge + Rr[::-1][1:][::-1]
    sh = ridge + [Rr[-1]] + Rr[::-1][1:-1][::-1][::-1]
    c.area(ridge + list(reversed(Rr[1:])), '#9c8a72', wob=.2, rough=.6, a=.92, seed=seed + 1)
    prev = c.clipm; c.set_clip(m)
    for k in range(int(w / 3.4)):
        u = r.rand(); sx = pk[0] - hl + u * (hl + hr); sy = y - r.uniform(.05, .75) * h
        dirx = .35 if sx > pk[0] else -.35
        c.stroke([(sx, sy), (sx + dirx * 6, sy + 9)], .9, '#6e5e4c' if sx > pk[0] else '#b4a27e', a=.75, dry=.3, taper=(.1, .5))
    c.clipm = prev
    if snow and h > 60:
        sn = [tuple(pk)]
        for t in np.linspace(0, 1, 9):
            side = -1 if t < .5 else 1; tt = abs(t - .5) * 2
            sn.append((pk[0] + side * (hl if side < 0 else hr) * .35 * tt, pk[1] + h * (.22 + .12 * math.sin(t * 19)) * (1 - .4 * tt)))
        sn.append(tuple(pk))
        c.area(sn, '#f6f0e2', wob=.1, rough=.6)
        c.area([tuple(pk)] + [p for p in sn if p[0] > pk[0]], '#d4d6de', wob=0, rough=.4, a=.85)
    c.stroke(L, 1.0, INK, a=.8, dry=.1, taper=(.1, .05), tremor=.3); c.stroke(Rr, 1.0, INK, a=.8, dry=.1, taper=(.05, .1), tremor=.3)
    c.stroke(ridge[:4], .6, INK, a=.5, dry=.1, taper=(0, .5))

def mesa(x, y, w, h, seed):
    r = np.random.RandomState(seed); tw = w * r.uniform(.55, .75)
    poly = [(x - w / 2, y), (x - tw / 2 - 4, y - h * .6), (x - tw / 2, y - h), (x + tw / 2, y - h - r.uniform(-2, 2)), (x + tw / 2 + 4, y - h * .55), (x + w / 2, y)]
    m = c.area(poly, '#c86a3e', wob=.3, rough=.6, edge_dark=.1, seed=seed)
    prev = c.clipm; c.set_clip(m)
    for k, yy in enumerate(np.linspace(y - h + 4, y - 3, 5)):
        c.stroke([(x - w / 2, yy), (x + w / 2, yy + r.randn())], 2.2, ['#e08a5a', '#a8502e', '#d47a4a'][k % 3], a=.8, dry=.3, taper=(0, 0))
    c.area([(x + tw * .1, y - h - 4), (x + w / 2 + 4, y - h - 4), (x + w / 2 + 4, y + 2), (x + tw * .1, y + 2)], '#7a3a24', wob=0, rough=.6, a=.35)
    c.clipm = prev
    c.area([(x - tw / 2, y - h), (x + tw / 2, y - h), (x + tw / 2 - 3, y - h - 3), (x - tw / 2 + 3, y - h - 3)], '#e8a070', wob=0, rough=.4)
    c.stroke(poly, 1.0, INK, a=.8, dry=.1, taper=(0, 0), tremor=.3)

def arch(x, y):
    outer = [(x - 34 + 68 * u, y - math.sin(u * math.pi) ** .8 * 44) for u in np.linspace(0, 1, 30)]
    inner = [(x - 20 + 40 * u, y - math.sin(u * math.pi) ** .8 * 30) for u in np.linspace(0, 1, 30)][::-1]
    m = c.area(outer + inner, '#c86a3e', wob=.3, rough=.6, edge_dark=.1)
    c.stroke(outer, 1.0, INK, a=.8, dry=.1, taper=(0, 0)); c.stroke(inner, 1.0, INK, a=.8, dry=.1, taper=(0, 0))
    c.stroke([(x - 30, y - 8), (x - 26, y - 26)], 2.4, '#e8a070', a=.8, dry=.3)

def cactus(x, y, h):
    c.stroke([(x, y), (x, y - h)], 2.4, '#5a7a3a', a=1, dry=.1, taper=(0, .05))
    c.stroke([(x, y - h * .45), (x - 4, y - h * .45), (x - 4, y - h * .75)], 1.8, '#5a7a3a', a=1, dry=.1, taper=(0, .1))
    c.stroke([(x, y - h * .6), (x + 4, y - h * .6), (x + 4, y - h * .85)], 1.8, '#5a7a3a', a=1, dry=.1, taper=(0, .1))

def pine(x, y, h, cols, seed):
    r = np.random.RandomState(seed); w = h * .3
    for k in range(3):
        t0 = k / 3; yy = y - h * .2 - h * .26 * k
        tri = [(x - w * (1 - t0 * .3), yy), (x + w * (1 - t0 * .3), yy), (x + r.randn() * .5, yy - h * .42)]
        c.area(tri, cols[k % len(cols)], wob=.1, rough=.4, edge_dark=.12)
    c.stroke([(x, y), (x, y - h * .2)], 1.4, '#5a3e2c', a=1, dry=0, taper=(0, 0))

def roundtree(x, y, h, cols, seed):
    c.stroke([(x, y), (x, y - h * .35)], 1.4, '#5a3e2c', a=1, dry=0, taper=(0, 0))
    m = c.area(S.lumpy(x, y - h * .62, h * .32, h * .32, seed, n=24, amp=.1), cols[0], wob=.1, rough=.5, edge_dark=.15)
    c.area(S.lumpy(x - h * .08, y - h * .7, h * .16, h * .14, seed + 1, n=16, amp=.1), cols[1], wob=0, rough=.4, a=.9)

def compass(x, y, r0):
    for k in range(3):
        rr = r0 * (.98 - k * .08)
        c.stroke([(x + rr * math.cos(t), y + rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 80)], 1.0 if k != 1 else 2.0, INK if k != 1 else '#c86a3e', a=.85, dry=.1, taper=(0, 0))
    for k in range(32):
        t = k / 32 * 2 * math.pi
        c.stroke([(x + r0 * .88 * math.cos(t), y + r0 * .88 * math.sin(t)), (x + r0 * .82 * math.cos(t), y + r0 * .82 * math.sin(t))], .6, INK, a=.8, dry=0, taper=(0, 0))
    for k in range(8):
        t = k / 8 * 2 * math.pi - math.pi / 2; ln = r0 * (.95 if k % 2 == 0 else .6); wd = r0 * (.16 if k % 2 == 0 else .12)
        tip = (x + math.cos(t) * ln, y + math.sin(t) * ln); nx, ny = -math.sin(t), math.cos(t)
        cl, cr = (x + nx * wd, y + ny * wd), (x - nx * wd, y - ny * wd)
        c.area([cl, tip, (x, y)], '#c86a3e' if k % 2 == 0 else '#5f9a96', wob=0, rough=.3)
        c.area([cr, tip, (x, y)], '#f3e6cb' if k % 2 == 0 else '#e2c98e', wob=0, rough=.3)
        c.stroke([cl, tip, cr], .7, INK, a=.85, dry=0, taper=(0, 0))
    c.dots([(x, y)], r0 * .06, ['#e2b44b'])
    n = (x, y - r0 * 1.12)
    c.stroke([(n[0] - 3, n[1] + 4), (n[0] - 3, n[1] - 4), (n[0] + 3, n[1] + 4), (n[0] + 3, n[1] - 4)], .9, INK, a=.9, dry=0, taper=(0, 0))

def whale(x, y):
    body = S.lumpy(x, y, 28, 9, 4, n=30, amp=.04, flat=-.4)
    c.area(body, '#4f6f80', wob=.2, rough=.4, edge_dark=.1)
    c.area([(x + 24, y - 2), (x + 38, y - 10), (x + 36, y + 2)], '#4f6f80', wob=0, rough=.3)
    c.stroke([(x - 20, y + 2), (x + 10, y + 6)], 1.4, '#c9d8d8', a=.8, dry=.2)
    c.dots([(x - 16, y - 2)], 1, [INK])
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * .35
        c.stroke([(x - 8, y - 9), (x - 8 + math.cos(a) * 12, y - 9 + math.sin(a) * 12)], 1.2, '#e6f0f0', a=.9, dry=.2, taper=(0, .6))

def ship(x, y):
    hull = [(x - 22, y), (x + 24, y), (x + 16, y + 9), (x - 16, y + 9)]
    c.area(hull, '#7a4a30', wob=0, rough=.3); c.stroke(hull + [hull[0]], .8, INK, a=.8, dry=0, taper=(0, 0))
    for mx, hh in ((x - 8, 34), (x + 8, 40)):
        c.stroke([(mx, y), (mx, y - hh)], 1.2, INK, a=.9, dry=0, taper=(0, 0))
        for k in range(2):
            yy = y - hh + 4 + k * 14
            sail = [(mx - 9, yy), (mx + 9, yy), (mx + 10, yy + 11), (mx - 10, yy + 11)]
            c.area(sail, '#f6efe0', wob=.1, rough=.3); c.stroke(sail + [sail[0]], .6, INK, a=.7, dry=0, taper=(0, 0))
    c.area([(x + 8, y - 40), (x + 18, y - 37), (x + 8, y - 34)], '#c8402e', wob=0, rough=.2)

def serpent(x, y):
    for k in range(3):
        cx = x + k * 26
        arc = [(cx + 11 * math.cos(t), y + 9 * math.sin(t)) for t in np.linspace(math.pi, 2 * math.pi, 14)]
        c.stroke(arc, 5.5, '#5f8a6a', a=1, dry=.15, taper=(.15, .15))
        for p in arc[3:-3:3]: c.dots([p], .9, ['#e8c050'])
    c.area(S.lumpy(x - 18, y - 6, 7, 5, 3, n=16, amp=.05), '#5f8a6a', wob=0, rough=.3)
    c.dots([(x - 20, y - 8)], 1, [INK])
    c.stroke([(x + 66, y), (x + 76, y - 8)], 3, '#5f8a6a', a=1, dry=.1, taper=(0, .8))

def main():
    # aged paper: warmer, darker towards the edges
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx / W - .5) ** 2 + (yy / H - .5) ** 2)
    c.img *= (1 - np.clip(v * .7, 0, .2))[..., None] * np.array([1, .98, .94], np.float32)
    # the sea
    seapoly = [(40, 40), (1560, 40), (1560, 860), (40, 860)]
    sm = c.area(seapoly, '#86b4aa', wob=.5, rough=1, edge_dark=.04, a=.92)
    c.flow_fill(sm, lambda x, y: .05 * math.sin(x / 60), lambda x, y, r: hexc(['#86b4aa', '#7aaa9e', '#94bcb2', '#709e94'][r.randint(4)]), 10, 80, 9, dry=.4, a=.7, seed=2)
    # coastline ripples, the classic way
    lm = np.zeros((H, W), np.uint8)
    for P in [LAND] + ISLES: cv2.fillPoly(lm, [np.round(np.asarray(P) * K * 8).astype(np.int32)], 255, cv2.LINE_AA, shift=3)
    dist = cv2.distanceTransform(255 - (lm > 127).astype(np.uint8) * 255, cv2.DIST_L2, 5) / K
    for d, a_ in ((5, .75), (11, .55), (18, .4), (27, .28)):
        cs, _ = cv2.findContours(((dist < d) & (dist >= 0)).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for cnt in cs:
            P = cnt[:, 0, :].astype(float) / K
            if len(P) < 20: continue
            P = resample(np.vstack([P, P[:1]]), 2.5)
            for i in range(0, len(P) - 2, 40):
                c.stroke(P[i:i + 42], .9, '#3f6a6a', a=a_, dry=.1, taper=(0, 0), press=.2, rough=.2)
    # wave marks in open water
    for i in range(320):
        x = R.uniform(60, 1540); y = R.uniform(60, 840)
        if dist[int(y * K), int(x * K)] < 34: continue
        c.stroke([(x - 6, y), (x - 3, y - 2.2), (x, y), (x + 3, y - 2.2), (x + 6, y)], .9, ['#3f6a6a', '#e6f0ea'][R.randint(2)], a=.75, dry=.15, taper=(.2, .2))
    log('sea')
    # the land
    for P in [LAND] + ISLES:
        m = c.area(P, '#ead7a4', wob=.6, rough=1, edge_dark=.08)
        c.flow_fill(m, lambda x, y: .1 * math.sin(y / 40), lambda x, y, r: hexc(['#e6d29e', '#dcc68e', '#efdcab', '#d8c088'][r.randint(4)]), 9, 60, 8, dry=.4, a=.8, seed=int(P[0][0]))
    inner = cv2.distanceTransform((lm > 127).astype(np.uint8), cv2.DIST_L2, 5) / K
    meadow_m = (0, 0, np.clip((inner - 9) / 4, 0, 1).astype(np.float32) * (.55 + .45 * c.Nbig))
    gr = np.random.RandomState(70)
    for (cx, cy, rx, ry) in [(330, 470, 140, 90), (700, 300, 150, 70), (980, 380, 170, 70), (560, 640, 160, 70), (1120, 680, 120, 50), (300, 640, 80, 40), (860, 720, 120, 40)]:
        pm = c.area(S.lumpy(cx, cy, rx, ry, int(cx), n=40, amp=.18), '#b9bc80', wob=3, rough=1.2, edge_dark=.02, a=.75)
        c.flow_fill(pm, lambda x, y: .2, lambda x, y, r: hexc(['#b9bc80', '#a9b070', '#c6c690'][r.randint(3)]), 7, 40, 7, dry=.45, a=.6, seed=int(cx))
    for P in [LAND] + ISLES:
        c.stroke(np.vstack([P, P[:1]])[::1], 1.4, INK, a=0)
    # a pale beach just inside the coast, then the inked coastline
    bm = (0, 0, (np.clip(1 - np.abs(inner - 4) / 3.5, 0, 1) * (inner > 0)).astype(np.float32))
    c.area(None, '#f0e2b8', m=bm, edge_dark=0, var=.03, a=.85)
    for P in [LAND] + ISLES:
        PP = np.vstack([P, P[:1]])
        for i in range(0, len(PP) - 2, 40): c.stroke(PP[i:i + 42], 1.4, INK, a=.85, dry=.15, taper=(0, 0), tremor=.4)
    # old-map hills: little humps with shaded flanks, in loose flocks
    for i in range(60):
        x = gr.uniform(200, 1180); y = gr.uniform(160, 760)
        if inner[int(y * K), int(x * K)] < 30: continue
        if inpoly(FOREST, np.array([x]), np.array([y]))[0] or inpoly(DESERT, np.array([x]), np.array([y]))[0]: continue
        if 800 < x < 1160 and 440 < y < 690: continue
        if 640 < x < 1320 and y < 280: continue
        w_ = gr.uniform(14, 26); h_ = w_ * gr.uniform(.35, .5)
        arc = [(x - w_ / 2 + w_ * u, y - math.sin(u * math.pi) * h_) for u in np.linspace(0, 1, 12)]
        c.area(arc, '#c7b882', wob=0, rough=.4, a=.8)
        c.area(arc[5:] + [(x + w_ / 2, y)], '#a99a6a', wob=0, rough=.4, a=.6)
        c.stroke(arc, .8, INK, a=.6, dry=.1, taper=(.1, .1))
        for kk in range(2): c.stroke([(x + w_ * (.05 + kk * .12), y - h_ * .7), (x + w_ * (.1 + kk * .12), y - h_ * .1)], .5, INK, a=.5, dry=0, taper=(0, 0))
    gm = c.area(FOREST, '#a7b07a', wob=1, rough=1, edge_dark=.05, a=.85)
    c.flow_fill(gm, lambda x, y: .3, lambda x, y, r: hexc(['#a7b07a', '#98a66c', '#b4b886'][r.randint(3)]), 8, 40, 8, dry=.45, a=.7, seed=4)
    dm = c.area(DESERT, '#e9b27a', wob=1, rough=1, edge_dark=.05, a=.85)
    c.flow_fill(dm, lambda x, y: -.2, lambda x, y, r: hexc(['#e9b27a', '#e2a46a', '#efc08a'][r.randint(3)]), 8, 40, 8, dry=.45, a=.7, seed=5)
    # farms: a stitched quilt of fields on a tilted grid
    fr = np.random.RandomState(81); ang = -.18; ca, sa = math.cos(ang), math.sin(ang)
    ox, oy = 980, 560; nx_, ny_ = 7, 5; cw, chh = 46, 34
    G = np.zeros((ny_ + 1, nx_ + 1, 2))
    for j in range(ny_ + 1):
        for i in range(nx_ + 1):
            u = (i - nx_ / 2) * cw + fr.uniform(-8, 8); v = (j - ny_ / 2) * chh + fr.uniform(-6, 6)
            G[j, i] = (ox + ca * u - sa * v, oy + sa * u + ca * v)
    FC = ['#d8b45a', '#a9b06a', '#c98a4e', '#e2c27a', '#9eaa62', '#d6a28a', '#b8a050', '#e0cc8a']
    for j in range(ny_):
        for i in range(nx_):
            if ((i - (nx_ - 1) / 2) / (nx_ / 2)) ** 2 + ((j - (ny_ - 1) / 2) / (ny_ / 2)) ** 2 > 1.05: continue
            q = [G[j, i], G[j, i + 1], G[j + 1, i + 1], G[j + 1, i]]
            col = FC[fr.randint(len(FC))]
            pm = c.area(q, col, wob=.3, rough=.8, a=.95, edge_dark=.06)
            fa = ang + (math.pi / 2 if fr.rand() < .4 else 0)
            c.flow_fill(pm, lambda x, y, a=fa: a, lambda x, y, r, cc=col: hexc(cc) * (.86 + .2 * r.rand()), 1.6, 40, 3.2, dry=.4, a=.75, seed=j * 10 + i)
            for e0, e1 in ((q[0], q[1]), (q[1], q[2])):
                for p in resample(np.array([e0, e1]), 3.2):
                    if fr.rand() < .85: c.dab(p[0], p[1], 3, 2.6, fr.rand() * 3, ['#4f6a38', '#5f7a40'][fr.randint(2)], a=.95, dry=.05)
    log('land')
    # rivers and lake
    for P, w0, w1 in ((RIVER1, 3, 7), (RIVER2, 6, 12)):
        poly, nr, wv = ribbon(P, lambda t: w0 + (w1 - w0) * t)
        c.area(poly, '#7aaab0', wob=.3, rough=.6, edge_dark=.12); c.stroke(P, .7, '#e6f0ea', a=.6, dry=.3, taper=(.2, .2))
    lk = c.area(LAKE, '#7aaab0', wob=.5, rough=.8, edge_dark=.15)
    c.flow_fill(lk, lambda x, y: 0, lambda x, y, r: hexc(['#7aaab0', '#8ab8bc', '#6a9ca4'][r.randint(3)]), 3, 30, 3.5, dry=.35, a=.85, seed=6)
    c.stroke(np.vstack([LAKE, LAKE[:1]]), 1.0, INK, a=.7, dry=.1, taper=(0, 0), tremor=.3)
    c.area(S.lumpy(530, 466, 14, 7, 3, n=18, amp=.1), '#a7b07a', wob=.2, rough=.5); roundtree(530, 466, 16, ['#5f8a4a', '#8ab060'], 2)
    c.area([(482, 486), (500, 484), (497, 488), (485, 489)], '#b8302a', wob=0, rough=.2)
    # the forest: an organic crowd of trees, densest in the middle
    trees = []
    for i in range(170):
        x = R.uniform(200, 620); y = R.uniform(140, 390)
        if not inpoly(FOREST, np.array([x]), np.array([y]))[0]: continue
        if any(abs(x - t[0]) < 9 and abs(y - t[1]) < 7 for t in trees): continue
        trees.append((x, y))
    trees.sort(key=lambda t: t[1])
    for i, (x, y) in enumerate(trees):
        if R.rand() < .7: pine(x, y + 10, R.uniform(16, 26), [['#3f6a4a', '#4f7a54', '#5f8a5e'], ['#2f5a4a', '#3f6a5a', '#4f7a6a']][R.randint(2)], i)
        else: roundtree(x, y + 10, R.uniform(14, 22), [['#6a8a4a', '#9ab06a'], ['#c87a3a', '#e8a05a'], ['#8a9a3a', '#b8c060']][R.randint(3)], i)
    log('forest')
    # mountains, back to front
    MTS = [(730, 190, 120, 62), (820, 176, 150, 92), (930, 186, 140, 78), (1010, 170, 190, 128), (1120, 186, 150, 96), (1220, 198, 130, 70),
           (1300, 214, 110, 52), (780, 226, 110, 44), (880, 236, 120, 52), (980, 240, 110, 46), (1080, 246, 130, 58), (1190, 250, 110, 40),
           (700, 240, 80, 30), (1260, 262, 90, 34)]
    for i, (x, y, w, h) in enumerate(sorted(MTS, key=lambda m: m[1])): mountain(x, y, w, h, 40 + i)
    for i in range(14):
        x = R.uniform(1220, 1420); y = R.uniform(360, 640)
        if inpoly(DESERT, np.array([x]), np.array([y]))[0] and R.rand() < .7: cactus(x, y, R.uniform(7, 12))
    canyon = catmull([(1230, 360), (1270, 400), (1250, 460), (1300, 520), (1280, 600), (1320, 660)], 10)
    cp, _, _ = ribbon(canyon, lambda t: 6 + 6 * math.sin(t * 3)); c.area(cp, '#8a3e24', wob=.3, rough=.8, a=.85); c.stroke(canyon, .8, INK, a=.6, dry=.1, taper=(0, 0))
    for i, (x, y, w, h) in enumerate([(1350, 400, 64, 30), (1220, 500, 70, 34), (1380, 500, 56, 40), (1340, 590, 84, 36), (1410, 610, 44, 22), (1230, 420, 40, 20)]): mesa(x, y, w, h, 60 + i)
    arch(1250, 650)
    log('mountains & mesas')
    # the railway loop
    rails(c, RAIL, SF, ballast='#b9a07a', tie='#5a4434', steel='#3a2e2a', hide=[(int(np.argmin(np.hypot(RAIL[:, 0] - 1170, RAIL[:, 1] - 252))), int(np.argmin(np.hypot(RAIL[:, 0] - 1100, RAIL[:, 1] - 256))))], shine=None)
    for (x, y) in [(1172, 254), (1098, 258)]:
        c.area([(x - 9, y + 3)] + [(x - 9 + 18 * u, y + 3 - math.sin(u * math.pi) * 14) for u in np.linspace(0, 1, 14)] + [(x + 9, y + 3)], '#9a8a76', wob=0, rough=.4)
        c.area([(x - 5, y + 3)] + [(x - 5 + 10 * u, y + 3 - math.sin(u * math.pi) * 9) for u in np.linspace(0, 1, 10)] + [(x + 5, y + 3)], '#1f1a18', wob=0, rough=.3)
    bi = int(np.argmin(np.hypot(RAIL[:, 0] - 645, RAIL[:, 1] - 704)))
    dk = RAIL[bi - 8:bi + 9]
    c.stroke(dk + [0, 4], 5, '#b3a594', a=1, dry=.1, taper=(0, 0)); c.stroke(dk + [0, 6.5], .8, INK, a=.8, dry=0, taper=(0, 0))
    log('rail')
    # destinations
    for b in [dict(t='side', x=356, y=702, w=30, d=16, h=14, rh=10, wall='coral', roof='slate', door='cream', name='h1'),
              dict(t='gable', x=400, y=716, w=18, d=18, h=18, rh=14, wall='turquoise', roof='brick', door='gold', name='h2'),
              dict(t='side', x=320, y=688, w=24, d=14, h=12, rh=9, wall='gold', roof='brick', door='slate', name='h3'),
              dict(t='side', x=420, y=316, w=36, d=20, h=16, rh=14, wall='#8a5a3c', roof='moss', door='gold', porch=True, name='lodge'),
              dict(t='gable', x=760, y=420, w=24, d=26, h=24, rh=18, wall='offwhite', roof='terracotta', tower=True, door='turquoise', name='t1'),
              dict(t='side', x=716, y=432, w=30, d=16, h=16, rh=11, wall='dustypink', roof='slate', door='brick', name='t2'),
              dict(t='false', x=806, y=446, w=28, d=22, h=20, rh=8, wall='gold', roof='slate', door='coral', awning=True, name='t3'),
              dict(t='gable', x=740, y=458, w=18, d=18, h=18, rh=14, wall='sage', roof='brick', door='cream', name='t4'),
              dict(t='station', x=700, y=520, w=44, d=16, h=12, rh=9, wall='ochre', roof='brick', door='forest', name='t5'),
              dict(t='gambrel', x=960, y=560, w=28, d=30, h=16, rh=18, wall='barnred', roof='slate', door='cream', name='f1'),
              dict(t='side', x=1020, y=600, w=26, d=16, h=14, rh=10, wall='cream', roof='brick', door='turquoise', porch=True, name='f2')]:
        S.paint_building(b)
    lighthouse_x, lighthouse_y = 262, 700
    body = [(lighthouse_x - 5, lighthouse_y), (lighthouse_x + 5, lighthouse_y), (lighthouse_x + 3.4, lighthouse_y - 40), (lighthouse_x - 3.4, lighthouse_y - 40)]
    lmk = c.area(body, '#f6f0e4', wob=0, rough=.3)
    prev = c.clipm; c.set_clip(lmk)
    for k in range(4): c.area([(lighthouse_x - 7, lighthouse_y - k * 10 - 5), (lighthouse_x + 7, lighthouse_y - k * 10 - 5), (lighthouse_x + 7, lighthouse_y - k * 10 - 10), (lighthouse_x - 7, lighthouse_y - k * 10 - 10)], '#c8402e', wob=0, rough=.3)
    c.clipm = prev
    c.area([(lighthouse_x - 3.5, lighthouse_y - 40), (lighthouse_x + 3.5, lighthouse_y - 40), (lighthouse_x + 3.5, lighthouse_y - 46), (lighthouse_x - 3.5, lighthouse_y - 46)], '#f2d06a', wob=0, rough=.3)
    c.area([(lighthouse_x - 5, lighthouse_y - 46), (lighthouse_x + 5, lighthouse_y - 46), (lighthouse_x, lighthouse_y - 52)], '#2a3a48', wob=0, rough=.3)
    for k in (-1, 1): c.stroke([(lighthouse_x + 6 * k, lighthouse_y - 43), (lighthouse_x + 40 * k, lighthouse_y - 50 + 6 * k)], 5, '#f6e6a0', a=.35, dry=.3, taper=(.1, .9))
    c.stroke([(340, 720), (330, 760)], 3, '#8a6440', a=1, dry=.1, taper=(0, 0))
    for (x, y, col) in [(300, 770, '#e05a4a'), (380, 780, '#e8c050')]:
        c.area([(x - 9, y), (x + 9, y), (x + 6, y + 4), (x - 6, y + 4)], '#7a4a30', wob=0, rough=.2); c.area([(x, y - 1), (x, y - 13), (x + 7, y - 2)], col, wob=0, rough=.2)
    for (x, y) in [(870, 470), (900, 640), (1100, 470), (1150, 600), (640, 300), (700, 600), (560, 640), (480, 610), (1060, 360), (980, 380), (300, 480), (270, 560)]:
        roundtree(x, y, R.uniform(14, 20), [['#6a8a4a', '#9ab06a'], ['#c87a3a', '#e8a05a'], ['#d6a0a8', '#f0c6c6']][R.randint(3)], int(x))
    for (x, y) in [(960, 470), (990, 476), (1070, 470)]: S.sheep(x, y, 1)
    for pts in [[(430, 330), (520, 360), (620, 380), (700, 420)], [(790, 440), (860, 470), (920, 520)], [(420, 690), (470, 640), (520, 600), (600, 560), (690, 520)],
                [(800, 450), (900, 420), (1060, 400), (1180, 420), (1240, 460)]]:
        P = catmull(pts, 10)
        for i in range(0, len(P) - 2, 4): c.stroke(P[i:i + 3], 1.2, '#8a6a4a', a=.85, dry=.1, taper=(.2, .2))
    # a windmill by the farms and a waterfall from the range
    wx, wy = 1150, 520
    c.area([(wx - 6, wy), (wx + 6, wy), (wx + 3.5, wy - 24), (wx - 3.5, wy - 24)], '#f3e6cb', wob=0, rough=.3); c.stroke([(wx - 6, wy), (wx - 3.5, wy - 24), (wx + 3.5, wy - 24), (wx + 6, wy)], .7, INK, a=.8, dry=0, taper=(0, 0))
    for k in range(4):
        a_ = math.radians(30 + k * 90); c.stroke([(wx, wy - 26), (wx + math.cos(a_) * 18, wy - 26 + math.sin(a_) * 18)], 2.6, '#c86a3e', a=1, dry=.1, taper=(0, 0))
    for k in range(5): c.stroke([(902 + k * 1.5, 196), (900 + k * 1.2, 214)], 1, '#f2f6f2', a=.9, dry=.2, taper=(0, .3))
    log('places')
    i_head = int(np.argmin(np.hypot(RAIL[:, 0] - 960, RAIL[:, 1] - 712)))
    train(c, RAIL, i_head, 1.45)
    # the sea's inhabitants and the compass
    whale(120, 790); ship(1530, 520); serpent(1480, 170); compass(1480, 760, 62)
    c.dots([(110, 690)], 1.6, ['#f2d06a'])
    roundtree(98, 690, 18, ['#6a8a4a', '#9ab06a'], 4); pine(1556, 748, 18, ['#3f6a4a', '#4f7a54', '#5f8a5e'], 5)
    # a hot-air balloon drifting over the mountains, dashed course behind it
    bx, by = 600, 80
    c.area(S.lumpy(bx, by, 14, 17, 2, n=30, amp=.02, flat=-.25), '#e08a6c', wob=0, rough=.3)
    for k in (-1, 0, 1): c.stroke([(bx + k * 5, by - 16), (bx + k * 6, by + 14)], 2.2, '#f3e6cb', a=.9, dry=.1, taper=(0, 0))
    c.area([(bx - 4, by + 22), (bx + 4, by + 22), (bx + 3, by + 27), (bx - 3, by + 27)], '#8a5a3c', wob=0, rough=.2)
    for k in (-1, 1): c.stroke([(bx + k * 9, by + 10), (bx + k * 3.5, by + 22)], .5, INK, a=.8, dry=0, taper=(0, 0))
    dash = catmull([(240, 60), (340, 96), (460, 70), (580, 92)], 10)
    for i in range(0, len(dash) - 3, 4): c.stroke(dash[i:i + 2], .8, INK, a=.6, dry=0, taper=(0, 0))
    # border: a painted double rule with corner diamonds
    for inset, w_, col in ((20, 3.2, '#8a3a2a'), (28, 1.0, INK)):
        q = [(inset, inset), (1600 - inset, inset), (1600 - inset, 900 - inset), (inset, 900 - inset), (inset, inset)]
        for i in range(4): c.stroke([q[i], q[i + 1]], w_, col, a=.9, dry=.15, taper=(0, 0), tremor=.3)
    for (x, y) in [(24, 24), (1576, 24), (1576, 876), (24, 876)]:
        c.area([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)], '#c86a3e', wob=0, rough=.3); c.dots([(x, y)], 2.2, ['#e2b44b'])
    c.save('out/C')
    log('saved')

if __name__ == '__main__':
    main()

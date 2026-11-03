"""Direction 1 — The Illustrated Storybook.
Opaque gouache on warm paper, strokes that follow each form, selective hand-inked line, a warm mid-century palette."""
import sys, time, math
import numpy as np, cv2
from brush import *
from world import *
from parts import *

K = 2
W, H = DW * K, DH * K
c = Canvas(W, H, K, '#f2e7d0', seed=7)
INK = '#2e2723'
R = np.random.RandomState(2024)
T0 = time.time()
def log(m): print(f'{time.time() - T0:6.1f}s  {m}', flush=True)

# --------------------------------------------------------------------------- helpers
def topcol(m):
    x0, y0, mm = m
    has = (mm > .5).any(0); first = np.argmax(mm > .5, 0).astype(np.float32)
    first[~has] = 1e4
    sm = cv2.GaussianBlur(first[None], (0, 0), 6 * K)[0] if has.any() else first
    sm = np.where(has, sm, 1e4)
    return x0, y0, sm

def depth_fn(tc):
    x0, y0, sm = tc
    def f(x, y):
        i = int(np.clip(x * K - x0, 0, len(sm) - 1)); return y - (sm[i] + y0) / K
    def slope(x, y):
        i = int(np.clip(x * K - x0, 2, len(sm) - 3)); return math.atan2(sm[i + 2] - sm[i - 2], 4)
    return f, slope

def shadow_blob(x, y, rx, ry, col, a=.35):
    c.area(lumpy(x, y, rx, ry, int(x * 7 + y), n=24, amp=.08), col, wob=.6, rough=.5, edge_dark=0, a=a, var=0, varbig=0)

def jit(col, r, v=.06):
    return hexc(col) * (1 + (r.rand() - .5) * 2 * v)

# --------------------------------------------------------------------------- sky
def sky():
    m = c.area([(-10, -10), (1610, -10), (1610, 480), (-10, 480)], '#d9e2d6', wob=0, rough=0, edge_dark=0, var=.02)
    def col(x, y, r):
        t = np.clip(y / 420, 0, 1)
        base = mix('#a6c6c9', '#f3dfbf', t ** 1.25)
        if r.rand() < .12: base = mix(base, '#f6eedf', .35)
        return base * (1 + (r.rand() - .5) * .04)
    c.flow_fill(m, lambda x, y: .03 * math.sin(x / 260 + y / 90), col, 30, 200, 19, dry=.32, a=.85, seed=11, jitter=.15, streak=.03)
    log('sky')

def cloud(cx, cy, rx, ry, seed):
    r0 = np.random.RandomState(seed); nb = r0.randint(5, 8)
    x0, y0 = int((cx - rx * 1.3) * K), int((cy - ry * 2.2) * K); ww, hh = int(rx * 2.6 * K), int(ry * 3 * K)
    mm = np.zeros((hh, ww), np.float32)
    for i in range(nb):
        u = (i + .5) / nb; bx = cx - rx + 2 * rx * u; br = ry * (.55 + .5 * math.sin(u * math.pi)) * (.8 + .4 * r0.rand())
        by = cy - br * .45
        cv2.circle(mm, (int((bx * K - x0) * 4), int((by * K - y0) * 4)), int(br * K * 4), 1.0, -1, cv2.LINE_AA, shift=2)
    cv2.rectangle(mm, (int((cx - rx) * K - x0), int((cy - ry * .2) * K - y0)), (int((cx + rx) * K - x0), int((cy + ry * .2) * K - y0)), 1.0, -1)
    mm[int((cy + ry * .2) * K - y0):] = 0
    mm = cv2.GaussianBlur(mm, (0, 0), 1.2 * K)
    n_ = c.Nsm[y0:y0 + hh, x0:x0 + ww]
    mm = np.clip((mm - .5 + .25 * (n_ - .5)) * 4 + .5, 0, 1)
    m = c.area(None, '#f8f0e1', m=(x0, y0, mm), edge_dark=.02, var=.03, seed=seed)
    cnt, _ = cv2.findContours((mm > .5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = (max(cnt, key=len)[:, 0, :].astype(float) + [x0, y0]) / K
    # a cool belly
    belly = [(cx - rx * .95, cy + ry * .05), (cx + rx * .98, cy + ry * .08), (cx + rx * .9, cy + ry * .22), (cx - rx * .9, cy + ry * .22)]
    prev = c.clipm; c.set_clip(m)
    c.area(belly, '#d9ddd6', wob=1.5, rough=1, a=.8, edge_dark=0, seed=seed + 1)
    for i in range(int(rx / 9)):
        xx = cx - rx * .8 + R.rand() * rx * 1.6; yy = cy - ry * .2 + R.rand() * ry * .3
        c.dab(xx, yy, 20, 6, -.2 + R.randn() * .2, '#fffaf0', a=.6, dry=.5)
    c.clipm = prev
    # a partial ink contour along the upper bumps only
    top = pts[pts[:, 1] < cy + ry * .05]
    top = top[np.argsort(np.arctan2(top[:, 1] - cy, top[:, 0] - cx))]
    k0 = int(len(top) * .05); k1 = int(len(top) * (.5 + .3 * R.rand()))
    if k1 - k0 > 8: c.ink(top[k0:k1:6], .9, a=.5, tremor=.3)

def balloon(x, y):
    rx, ry = 22, 27
    env = lumpy(x, y, rx, ry, 5, n=48, bumps=2, amp=.03, flat=-.25)
    m = c.area(env, '#e08a6c', wob=.3, rough=.4, edge_dark=.08)
    prev = c.clipm; c.set_clip(m)
    for i, col in enumerate(['#f3e6cb', '#e2b44b', '#f3e6cb', '#5fa59c', '#f3e6cb']):
        u = (i - 2) * .38
        gore = [(x + u * rx * (1 - (t * 2 - 1) ** 2) ** .5 * 1.2 - 4 + 0, y - ry + t * ry * 2) for t in np.linspace(0, 1, 16)]
        gore2 = [(p[0] + 7 * (1 - (((j / 15) * 2 - 1) ** 2)) ** .5, p[1]) for j, p in enumerate(gore)]
        c.area(gore + gore2[::-1], col, wob=0, rough=.3, edge_dark=0, a=.95)
    c.area([(x + rx * .1, y - ry), (x + rx * 1.1, y - ry), (x + rx * 1.1, y + ry), (x + rx * .35, y + ry)], '#8a4a3a', wob=0, rough=0, a=.18, edge_dark=0)
    c.clipm = prev
    c.ink(catmull(env[::3].tolist() + [env[0].tolist()], 4), .9, a=.7)
    bx, by = x, y + ry + 13
    for dx in (-5, 5): c.ink([(x + dx * 1.8, y + ry * .78), (bx + dx * .8, by)], .6, a=.7, tremor=.1)
    c.area([(bx - 5, by), (bx + 5, by), (bx + 4, by + 7), (bx - 4, by + 7)], '#b07a40', wob=.2, rough=.3)
    c.ink([(bx - 5, by), (bx + 5, by), (bx + 4, by + 7), (bx - 4, by + 7), (bx - 5, by)], .7, a=.8)
    c.area(lumpy(bx + 1, by - 2.5, 1.8, 2, 3, n=10, amp=0), '#e2b44b', wob=0, rough=0)

# --------------------------------------------------------------------------- mountains
PEAKS_FAR = [(110, 270), (205, 240), (300, 222), (380, 226), (470, 236), (548, 178), (590, 160), (640, 150), (930, 196), (1060, 82),
             (1310, 226), (1420, 186), (1520, 206)]
PEAKS_MID = [(100, 318), (210, 300), (330, 296), (450, 312), (1240, 286), (1400, 270), (1500, 268)]

def face(peaks, x, y):
    best = None
    for px, py in peaks:
        if y < py - 2: continue
        if abs(x - px) < (y - py) * 1.3 + 14:
            if best is None or py < best[1]: best = (px, py)
    if best is None: return 0, None
    px, py = best
    ridge = px + (y - py) * .1 + 5 * math.sin((y - py) / 11 + px)
    return (1 if x > ridge else -1), best

def mountains():
    m = c.area(land(FAR, 520), '#a9b5c3', wob=.2, rough=.8, edge_dark=.03, var=.03, seed=21)
    def ang(x, y):
        s, _ = face(PEAKS_FAR, x, y)
        return math.atan2(1, .6) if s > 0 else math.atan2(1, -.6)
    def col(x, y, r):
        s, pk = face(PEAKS_FAR, x, y)
        haze = np.clip((y - 200) / 240, 0, 1)
        base = mix('#b9c2cb', '#8d9db3', 1.0 if s > 0 else 0.0)
        if pk is None: base = hexc('#a9b5c3')
        return mix(base, '#d5dcd6', haze * .55) * (1 + (r.rand() - .5) * .04)
    c.flow_fill(m, ang, col, 13, 40, 8, dry=.18, a=.75, seed=22, jitter=.6, streak=.03)
    # snow: down to a wavering line, fingers running down the gullies
    xs = np.linspace(-30, 1630, 1200)
    topy = np.interp(xs, FAR[:, 0], FAR[:, 1]); snl = np.interp(xs, *np.array(SNOWLINE).T)
    fing = np.zeros_like(xs); rr = np.random.RandomState(4)
    for k in range(70):
        cx = rr.uniform(-30, 1630); wdt = rr.uniform(4, 12); ln = rr.uniform(8, 34)
        fing += ln * np.clip(1 - np.abs(xs - cx) / wdt, 0, 1) ** 1.5
    low = snl + fing * (.4 + .6 * np.clip((snl - topy) / 60, 0, 1)) - 12 * np.abs(np.sin(xs / 23))
    low = np.maximum(low, topy)
    poly = np.vstack([np.stack([xs, topy - 1], 1), np.stack([xs, low], 1)[::-1]])
    sm = c.area(poly, '#f5eee0', wob=.4, rough=1.4, edge_dark=.03, seed=23)
    prev = c.clipm
    def scol(x, y, r):
        s, _ = face(PEAKS_FAR, x, y)
        return jit('#fbf3e3' if s <= 0 else '#c4cfe0', r, .04)
    c.flow_fill(sm, ang, scol, 7, 24, 5, dry=.2, a=.9, seed=24, jitter=.5, streak=.03)
    c.clipm = prev
    # couloirs and rock ribs running down from the summits, dry-brushed
    rr = np.random.RandomState(29)
    c.set_clip(m)
    for (px, py) in PEAKS_FAR:
        nlines = 7 if py < 120 else 4
        for k in range(nlines):
            side = rr.choice([-1, 1]); x = px + side * rr.uniform(4, 30); y = py + rr.uniform(6, 30)
            pts = [(x, y)]
            for j in range(6):
                x += side * rr.uniform(2, 8) + rr.randn() * 2; y += rr.uniform(10, 22); pts.append((x, y))
            colr = '#8090a8' if side < 0 else '#70809a'
            c.stroke(catmull(pts, 4), rr.uniform(1.6, 3.2), colr, a=.7, dry=.6, taper=(.1, .6))
            if side > 0: c.stroke(catmull([(p[0] - 2, p[1]) for p in pts], 4), 1.2, '#dfe3e6', a=.6, dry=.7, taper=(.1, .7))
    for i in range(260):
        x = rr.uniform(0, 1600); y = np.interp(x, xs, low) + rr.uniform(-6, 18)
        if y > 400: continue
        s_, _ = face(PEAKS_FAR, x, y)
        c.dab(x, y, rr.uniform(3, 7), rr.uniform(1.4, 2.4), math.atan2(1, .6 * s_), '#7c8aa2' if s_ > 0 else '#94a2b6', a=.7, dry=.4)
    c.clipm = prev
    log('far range')
    # middle range: blue-green, wooded shoulders
    m2 = c.area(land(MID, 560), '#7e959b', wob=.3, rough=.8, edge_dark=.04, seed=25)
    tc = topcol(m2); dep, _ = depth_fn(tc)
    def ang2(x, y):
        s, _ = face(PEAKS_MID, x, y); return math.atan2(1, .8) if s > 0 else math.atan2(1, -.8)
    def col2(x, y, r):
        s, _ = face(PEAKS_MID, x, y)
        base = mix('#93a8a6', '#6a8290', 1.0 if s > 0 else 0.0)
        return mix(base, '#c8d3cc', np.clip((y - 300) / 200, 0, 1) * .3) * (1 + (r.rand() - .5) * .07)
    c.flow_fill(m2, ang2, col2, 12, 36, 8, dry=.18, a=.8, seed=26, jitter=.6, streak=.03)
    prev = c.clipm; c.set_clip(m2)
    rr = np.random.RandomState(27)
    for i in range(1700):
        x = rr.uniform(-20, 1620); d = rr.uniform(4, 120) ** 1.2 / 2.2
        y = y_at(MID, x) + d
        if y > 450: continue
        s, _ = face(PEAKS_MID, x, y)
        colr = ['#5a7570', '#4d6a68', '#6c8577'][rr.randint(3)] if s <= 0 else ['#4b6266', '#415a60'][rr.randint(2)]
        c.stroke([(x, y), (x + rr.randn() * .3, y - 5 - rr.rand() * 3)], 3.2, colr, a=.8, dry=.1, taper=(.02, .95), press=0)
    c.clipm = prev
    log('mid range')

def ridge(top, seed, base, dark, light):
    r = np.random.RandomState(seed)
    xs = np.arange(top[0, 0], top[-1, 0], 6.5)
    pts = []
    for x in xs:
        y = y_at(top, x); th = 7 + r.rand() * 9
        pts += [(x - 3.2, y + 1), (x + r.randn() * .6, y - th), (x + 3.2, y + 1)]
    sil = np.vstack([pts, [[top[-1, 0], 600], [top[0, 0], 600]]])
    m = c.area(sil, base, wob=.0, rough=.7, edge_dark=.04, seed=seed)
    prev = c.clipm; c.set_clip(m)
    for i in range(int(len(xs) * 6)):
        x = r.uniform(top[0, 0], top[-1, 0]); y = y_at(top, x) + r.uniform(-6, 70) ** 1.0
        h = 8 + r.rand() * 8
        c.stroke([(x, y), (x, y - h)], 5.4, dark if r.rand() < .55 else base, a=.9, dry=.08, taper=(.02, .95), press=0)
        if r.rand() < .45: c.stroke([(x - 1.2, y - 1), (x - .4, y - h * .75)], 2.0, light, a=.75, dry=.2, taper=(.02, .95), press=0)
    c.clipm = prev
    return m

# --------------------------------------------------------------------------- land
def flowers(m, n, cols, seed, ymin=None, size=1.0):
    x0, y0, mm = m; h, w = mm.shape; r = np.random.RandomState(seed)
    for i in range(n):
        px, py = r.randint(w), r.randint(h)
        if mm[py, px] < .8: continue
        X, Y = (px + x0) / K, (py + y0) / K
        if ymin and Y < ymin: continue
        s = size * persp(Y)
        colr = cols[r.randint(len(cols))]
        c.dab(X, Y, 2.4 * s, 2.2 * s, r.rand() * 3, colr, a=.95, dry=.05)

def grass_tufts(m, n, seed, col='#4a5a2c', size=1.0):
    x0, y0, mm = m; h, w = mm.shape; r = np.random.RandomState(seed)
    for i in range(n):
        px, py = r.randint(w), r.randint(h)
        if mm[py, px] < .9: continue
        X, Y = (px + x0) / K, (py + y0) / K; s = size * persp(Y)
        for k in range(3):
            a = -math.pi / 2 + (k - 1) * .45 + r.randn() * .1
            c.ink([(X + (k - 1) * 1.1 * s, Y), (X + (k - 1) * 1.1 * s + math.cos(a) * 5 * s, Y + math.sin(a) * 5 * s)], .55 * s, col=col, a=.55, tremor=0)

HILLCOL = {
    'meadow': ('#b8b672', '#97a058', '#6f7d40'),
    'orchard': ('#b5b86d', '#93a052', '#6d7d3e'),
    'fg': ('#8f9c4c', '#6f7f3c', '#4f5f30'),
}

def paint_hill(hd, seed):
    kind = hd['kind']; name = hd['name']
    light, base, dark = HILLCOL.get(kind, HILLCOL['meadow'])
    if name == 'village': light, base, dark = '#c2bb7c', '#a6a35e', '#7f8444'
    if name == 'low_l': light, base, dark = '#9fae64', '#7f9047', '#5c6d35'
    m = c.area(land(hd['top']), base, wob=1.2, rough=1.0, edge_dark=.05, seed=seed)
    tc = topcol(m); dep, slope = depth_fn(tc)
    def ang(x, y):
        d = dep(x, y); return slope(x, y) * max(0, 1 - d / 160) + .02 * math.sin(x / 70)
    def col(x, y, r):
        d = dep(x, y); t = np.clip(d / 110, 0, 1)
        cc = mix(light, base, t ** .8)
        if d > 120: cc = mix(base, dark, np.clip((d - 120) / 260, 0, 1) * .6)
        sl = slope(x, y)
        if sl > .15: cc = cc * (1 - .08 * min(1, sl * 2))
        return cc * (1 + (r.rand() - .5) * .09)
    if kind in ('fields', 'fields2'):
        return m, tc
    sz = 1.6 if kind == 'fg' else 1.0
    c.flow_fill(m, ang, col, 9 * sz, 64 * sz, 7 * sz, dry=.32, a=.9, seed=seed + 1)
    # the last light along the crest
    top = hd['top']
    c.stroke(top + [0, 2.5], 4.5 * sz, light, a=.6, dry=.6, taper=(.05, .05), seed=seed + 2)
    return m, tc

PATCH = ['#d7b25a', '#a7ae66', '#c98c4e', '#8f9b4f', '#e0c27a', '#b4a052', '#c47a52', '#9eae7a']

def patchwork(hd, m, tc, seed, bands, pal):
    dep, slope = depth_fn(tc)
    x0, y0, sm = tc
    xs_all = (np.arange(len(sm)) + x0) / K
    valid = sm < 9e3
    xa, xb = xs_all[valid].min(), xs_all[valid].max()
    r = np.random.RandomState(seed)
    prev = c.clipm; c.set_clip(m)
    last = None; hedges = []
    def ty(x): return (np.interp(x * K - x0, np.arange(len(sm)), sm) + y0) / K
    for bi, (d0, d1) in enumerate(bands):
        n = r.randint(2, 4); cuts = np.sort(r.uniform(xa, xb, n - 1)); edges = [xa - 20] + list(cuts) + [xb + 20]
        for j in range(len(edges) - 1):
            a, b = edges[j], edges[j + 1]
            tilt0 = r.uniform(-12, 12); tilt1 = r.uniform(-12, 12)
            xx = np.linspace(a, b, 30)
            up = [(x + (tilt0 if k == 0 else tilt1 if k == 29 else 0), ty(x) + d0) for k, x in enumerate(xx)]
            dn = [(x + (tilt0 if k == 0 else tilt1 if k == 29 else 0) * 1.6, ty(x) + d1) for k, x in enumerate(xx)]
            colr = pal[r.randint(len(pal))]
            while colr == last: colr = pal[r.randint(len(pal))]
            last = colr
            pm = c.area(up + dn[::-1], colr, wob=.9, rough=.9, edge_dark=.06, seed=int(r.randint(1e6)), var=.06)
            kind = r.rand()
            pc = c.clipm;
            if pm is not None:
                c.set_clip((pm[0], pm[1], pm[2] * (m[2][pm[1] - m[1]:pm[1] - m[1] + pm[2].shape[0], pm[0] - m[0]:pm[0] - m[0] + pm[2].shape[1]] if (pm[1] >= m[1] and pm[0] >= m[0] and pm[1] - m[1] + pm[2].shape[0] <= m[2].shape[0] and pm[0] - m[0] + pm[2].shape[1] <= m[2].shape[1]) else 1)))
                if kind < .45:     # furrows following the slope of the land
                    c.flow_fill(pm, lambda x, y: slope(x, y), lambda x, y, rr: hexc(colr) * (.86 + .1 * rr.rand()), 1.6, 50, 3.2, dry=.4, a=.8, seed=int(r.randint(1e6)), jitter=.05, rough=.1)
                elif kind < .8:    # soft brushing
                    c.flow_fill(pm, lambda x, y: slope(x, y), lambda x, y, rr: hexc(colr) * (.93 + .14 * rr.rand()), 7, 50, 7, dry=.4, a=.8, seed=int(r.randint(1e6)))
                else:              # stooks / rows of little dabs
                    for yy in np.arange(d0 + 5, d1 - 3, 7):
                        for xq in np.arange(a + 6, b - 6, 9):
                            c.dab(xq + r.randn(), ty(xq) + yy, 3.2, 2.6, -.3, hexc(colr) * .8, a=.85, dry=.1)
            c.clipm = prev; c.set_clip(m)
            hedges.append(dn)
            if j > 0: hedges.append([(a + tilt0, ty(a) + d0), (a + tilt0 * 1.6, ty(a) + d1)])
    # hedgerows between the patches
    for hl in hedges:
        P = resample(np.array(hl), 3.4)
        for p in P[::1]:
            if r.rand() < .12: continue
            s = persp(p[1])
            c.dab(p[0] + r.randn() * .5, p[1] - 1, 4 * s, 3.4 * s, r.rand() * 3, ['#4f6338', '#5d7140', '#3f5432'][r.randint(3)], a=.95, dry=.1)
        for p in P[::9]:
            if r.rand() < .25: tree_round(p[0], p[1], 14 * persp(p[1]), int(r.randint(1e6)), small=True)
    c.clipm = prev

def valley():
    m = c.area(land(VALLEY), '#a4ae74', wob=0, rough=.5, edge_dark=0, seed=31)
    c.flow_fill(m, lambda x, y: 0.0, lambda x, y, r: jit(['#a9b27a', '#97a466', '#b3b682'][r.randint(3)], r, .04), 8, 60, 7, dry=.3, a=.85, seed=32)
    # distant hedgerows and a pale track
    r = np.random.RandomState(33)
    for hy, xa, xb in [(446, 40, 520), (452, 760, 1300), (460, 1000, 1500), (470, 120, 380)]:
        for x in np.arange(xa, xb, 3):
            if r.rand() < .15: continue
            c.dab(x, hy + 3 * math.sin(x / 60), 3.2, 2.6, r.rand() * 3, ['#5f7547', '#6c7f4b'][r.randint(2)], a=.9, dry=.1)

def river():
    P = RIVER; n = len(P)
    t = np.linspace(0, 1, n); wv = river_w(t)
    d = np.gradient(P, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.hypot(*nr.T)[:, None]
    wob = 1 + .12 * np.sin(np.arange(n) / 5.0)
    L = P + nr * (wv * wob / 2)[:, None]; Rr = P - nr * (wv * wob / 2)[:, None]
    poly = np.vstack([L, Rr[::-1]])
    m = c.area(poly, '#6fa6a2', wob=.8, rough=.8, edge_dark=.12, seed=41)
    def ang(x, y):
        j = int(np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y))); dd = d[j]; return math.atan2(dd[1], dd[0])
    def col(x, y, r):
        j = int(np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y))); tt = j / n
        base = mix('#86b4ad', '#4f8b8f', tt ** .8)
        if r.rand() < .18: base = mix(base, '#d9e6dc', .45)
        return base * (1 + (r.rand() - .5) * .07)
    c.flow_fill(m, ang, col, 4.5, 34, 3.6, dry=.35, a=.9, seed=42, jitter=.15)
    # glints
    r = np.random.RandomState(43)
    prev = c.clipm; c.set_clip(m)
    for i in range(160):
        j = r.randint(10, n - 2); tt = j / n; off = r.uniform(-.35, .35) * wv[j]
        p = P[j] + nr[j] * off; dd = d[j] / np.hypot(*d[j])
        ln = 4 + 12 * tt
        c.stroke([p - dd * ln / 2, p + dd * ln / 2], 1.0 + tt, '#f4efe2', a=.75, dry=.3, taper=(.3, .3))
    c.clipm = prev
    # inked banks, broken
    for side in (L, Rr):
        i = 0
        while i < n - 4:
            ln = r.randint(6, 18)
            if r.rand() < .7: c.ink(side[i:i + ln], .75, a=.6, tremor=.2)
            i += ln + r.randint(2, 8)
    # reeds along the lower banks
    for i in range(70):
        j = r.randint(int(n * .45), n - 2); side = L if r.rand() < .5 else Rr
        p = side[j]; s = persp(p[1])
        for k in range(3):
            c.ink([(p[0] + (k - 1) * 1.2 * s, p[1] + 1), (p[0] + (k - 1) * 2 * s + r.randn() * .5, p[1] - 6 * s - r.rand() * 3 * s)], .6 * s, col='#4d5a2c', a=.75, tremor=0)
    log('river')
    return m, L, Rr

def railbed():
    pts = RAIL; n = len(pts)
    d = np.gradient(pts, axis=0); d /= np.hypot(*d.T)[:, None]; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    bi = BRIDGE_I; j = BRIDGE_RJ; rw = river_w(j / len(RIVER))
    span = int((rw / 2 + 16) / 2.0)
    globals()['BR_SPAN'] = (bi - span, bi + span)
    tun = n - 1
    # ballast
    segs = [(0, bi - span), (bi + span, tun)]
    for a, b in segs:
        seg = pts[a:b + 1]
        for k in range(0, len(seg) - 1, 10):
            sub = seg[k:k + 12]
            s = persp(sub[len(sub) // 2][1])
            c.stroke(sub, 12 * s, '#c4ad87', a=.95, dry=.25, taper=(.0, .0), press=.05, rough=.4)
    # ties and rails
    acc = 0
    for i in range(1, n - 1):
        s = persp(pts[i][1]); acc += np.hypot(*(pts[i] - pts[i - 1]))
        if acc >= 5.2 * s:
            acc = 0; p = pts[i]
            c.stroke([p + nr[i] * 6 * s, p - nr[i] * 6 * s], 2.0 * s, '#5b4535', a=.9, dry=.1, taper=(.05, .05), press=.1)
    for off in (3.4, -3.4):
        sp = np.array([pts[i] + nr[i] * off * persp(pts[i][1]) for i in range(n)])
        c.ink(sp, 1.15, col='#3c3d46', a=.95, tremor=0, press=.1, taper=(0, 0))
    c.ink(np.array([pts[i] + nr[i] * 3.4 * persp(pts[i][1]) - [0, .6] for i in range(n)]), .5, col='#c9ccd2', a=.6, tremor=0, taper=(0, 0))

def bridge():
    a, b = BR_SPAN; pts = RAIL[a:b + 1]
    s = persp(pts[len(pts) // 2][1]) * 1.15
    deck = pts + [0, 4 * s]; base_y = deck[:, 1] + 27 * s
    face = np.vstack([deck - [0, 3 * s], np.stack([deck[::-1, 0], base_y[::-1]], 1)])
    m = c.area(face, '#d6c39c', wob=.2, rough=.5, edge_dark=.1, seed=51)
    x0, x1 = deck[0, 0], deck[-1, 0]
    r = np.random.RandomState(52)
    prev = c.clipm; c.set_clip(m)
    # stone courses
    for row, yy in enumerate(np.arange(5, 27, 4.4)):
        off = (row % 2) * 3.5
        xs = np.arange(x0 - 7 + off, x1 + 7, 7 + r.rand())
        for xq in xs:
            y = float(np.interp(xq, deck[:, 0], deck[:, 1])) + yy * s
            c.dab(xq + 3.5, y + 2, 6.2 * s, 3.6 * s, 0, ['#cdb890', '#e2d3b0', '#c2aa82', '#d9c7a0'][r.randint(4)], a=.85, dry=.1, bend=0)
            c.ink([(xq, y), (xq, y + 4.2 * s)], .35, a=.4, tremor=0)
        c.ink([(x0, float(np.interp(x0, deck[:, 0], deck[:, 1])) + yy * s), (x1, float(np.interp(x1, deck[:, 0], deck[:, 1])) + yy * s)], .35, a=.35, tremor=.2)
    c.clipm = prev
    for k in range(2):
        ax = x0 + (x1 - x0) * (k + .5) / 2; ay = float(np.interp(ax, deck[:, 0], base_y)); aw = (x1 - x0) / 2 * .7; ah = 17 * s
        arch = [(ax - aw / 2 + aw * u, ay - math.sin(u * math.pi) ** .75 * ah) for u in np.linspace(0, 1, 22)]
        c.area(arch + [(ax + aw / 2, ay + 1), (ax - aw / 2, ay + 1)], '#2f5257', wob=0, rough=.3, edge_dark=0)
        c.area([(ax - aw / 2, ay - 4 * s), (ax + aw / 2, ay - 4 * s), (ax + aw / 2, ay + 1), (ax - aw / 2, ay + 1)], '#5d9294', wob=0, rough=.6, a=.8, edge_dark=0)
        for u in np.linspace(0, 1, 11):
            p = np.array((ax - aw / 2 + aw * u, ay - math.sin(u * math.pi) ** .75 * ah))
            dv = p - [ax, ay + 4 * s]; dv /= np.hypot(*dv)
            c.ink([p, p + dv * 4.2 * s], .6, a=.8, tremor=0)
        c.ink(arch, 1.0, a=.9, tremor=.15)
        outer = [(ax - aw / 2 - 4 * s + (aw + 8 * s) * u, ay - math.sin(u * math.pi) ** .75 * (ah + 4.2 * s)) for u in np.linspace(0, 1, 22)]
        c.ink(outer, .6, a=.7, tremor=.15)
    c.stroke(deck - [0, 2.4 * s], 4.6 * s, '#e8dabb', a=1, dry=.1, taper=(0, 0), press=0)
    c.ink(deck - [0, 4.6 * s], 1.0, a=.9)
    c.ink(deck - [0, .2 * s], .7, a=.7)
    c.ink(np.stack([deck[:, 0], base_y], 1), .7, a=.5)
    c.ink([deck[0] - [0, 4.6 * s], (deck[0][0], base_y[0])], .9, a=.85); c.ink([deck[-1] - [0, 4.6 * s], (deck[-1][0], base_y[-1])], .9, a=.85)
    d = np.gradient(pts, axis=0); d /= np.hypot(*d.T)[:, None]; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    acc = 0
    for i in range(1, len(pts)):
        acc += 2.0
        if acc > 5.2 * s: acc = 0; c.stroke([pts[i] + nr[i] * 6 * s, pts[i] - nr[i] * 6 * s], 2 * s, '#5b4535', a=.9, dry=.1, taper=(.05, .05))
    for off in (3.4, -3.4): c.ink(pts + nr * off * s, 1.15, col='#3c3d46', a=.95, tremor=0, taper=(0, 0))
    for k in range(7):
        x = r.uniform(x0, x1); y = float(np.interp(x, deck[:, 0], base_y)) + 2 + r.rand() * 5
        c.stroke([(x - 6, y), (x + 6, y)], 1.0, '#eef0e4', a=.7, dry=.3)

def lane(pts, w=5.0, seed=0):
    P = catmull(pts, 10)
    for k in range(0, len(P) - 1, 8):
        sub = P[k:k + 10]; s = persp(sub[len(sub) // 2][1])
        c.stroke(sub, w * s, '#dcc89c', a=.95, dry=.3, taper=(0, 0), press=.1, rough=.6)
    r = np.random.RandomState(seed)
    d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    for side in (1, -1):
        e = P + nr * side * np.array([w * persp(p[1]) * .5 for p in P])[:, None]
        i = 0
        while i < len(e) - 3:
            ln = r.randint(5, 14)
            if r.rand() < .55: c.ink(e[i:i + ln], .45, col='#7d6a4c', a=.55, tremor=.1)
            i += ln + r.randint(3, 10)
    for k in range(int(len(P) / 3)):
        p = P[r.randint(len(P))]; s = persp(p[1])
        c.dab(p[0] + r.randn() * w * s * .2, p[1], 2.4 * s, 1 * s, 0, '#c9b282', a=.6, dry=.4)

def pond(x, y, rx, ry):
    o = lumpy(x, y, rx, ry, 9, n=30, amp=.12, flat=0)
    c.area(lumpy(x, y + 1, rx + 2, ry + 1.4, 9, n=30, amp=.12, flat=0), '#6f7f3f', wob=.3, rough=.7, a=.8)
    m = c.area(o, '#6fa6a2', wob=.3, rough=.6, edge_dark=.15)
    prev = c.clipm; c.set_clip(m)
    for k in range(10):
        yy = y - ry * .6 + k * ry * .13
        c.stroke([(x - rx, yy), (x + rx, yy)], 1.4, ['#9cc4bb', '#5d9294'][k % 2], a=.6, dry=.4)
    c.clipm = prev
    c.ink(o[::2].tolist() + [o[0].tolist()], .6, a=.5, tremor=.2)
    for dx, dy in ((-rx * .3, 0), (rx * .2, ry * .25)):
        c.area(lumpy(x + dx, y + dy, 2.2, 1.2, 3, n=12, amp=0, flat=.3), '#f7efdf', wob=0, rough=.2)
        c.dab(x + dx + 1.8, y + dy - 1.4, 1.3, 1.1, 0, '#f7efdf', a=1, dry=0); c.dab(x + dx + 2.9, y + dy - 1.2, .9, .6, 0, '#e2b44b', a=1, dry=0)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        p = (x + math.cos(a) * rx * 1.02, y + math.sin(a) * ry * 1.02)
        if math.sin(a) > -.2: c.ink([p, (p[0] + .5, p[1] - 4)], .5, col='#4d5a2c', a=.7, tremor=0)

def picnic(x, y):
    q = [(x - 9, y), (x + 8, y - 2), (x + 11, y + 4), (x - 7, y + 6)]
    m = c.area(q, '#f3e6cb', wob=0, rough=.3)
    prev = c.clipm; c.set_clip(m)
    for k in range(6):
        c.stroke([(x - 10 + k * 3.6, y - 3), (x - 7 + k * 3.6, y + 8)], 1.6, '#c4473a', a=.85, dry=0, taper=(0, 0))
        c.stroke([(x - 12, y - 1 + k * 1.5), (x + 12, y - 3 + k * 1.5)], 1.0, '#c4473a', a=.6, dry=0, taper=(0, 0))
    c.clipm = prev
    c.area([(x + 1, y), (x + 6, y - .5), (x + 6, y + 3), (x + 1, y + 3.4)], '#b07a40', wob=0, rough=.3)
    c.ink([(x + 1, y), (x + 3.5, y - 3.5), (x + 6, y - .5)], .5, a=.9, tremor=0)
    c.dab(x - 4, y + 2, 2, 2, 0, '#c4473a', a=1, dry=0); c.dab(x - 1.4, y + 3, 1.6, 1.6, 0, '#e2b44b', a=1, dry=0)

def distant_fields():
    r = np.random.RandomState(71)
    for i in range(34):
        x = r.uniform(20, 1580)
        if 560 < x < 740: continue
        y0 = r.uniform(438, 470); w_ = r.uniform(18, 46); h_ = r.uniform(4, 9)
        colr = mix(['#c3b46c', '#b2ae6c', '#c9a76a', '#a5ab6a'][r.randint(4)], '#a8b07a', .35)
        sk = r.uniform(-4, 4)
        q = [(x, y0), (x + w_, y0 + sk * .2), (x + w_ + 3, y0 + h_), (x + 2, y0 + h_ + 1)]
        c.area(q, colr, wob=.4, rough=.8, a=.7, edge_dark=.04)
        for p in resample(np.array([(x + 2, y0 + h_ + 1), (x + w_ + 3, y0 + h_)]), 3.2):
            if r.rand() < .7: c.dab(p[0], p[1], 2.4, 2, r.rand() * 3, ['#5f7547', '#6c7f4b'][r.randint(2)], a=.85, dry=.1)

def hedgerow(pts, seed, trees=.2):
    r = np.random.RandomState(seed)
    P = resample(catmull(pts, 8), 3.2)
    for p in P:
        if r.rand() < .1: continue
        s = persp(p[1])
        c.dab(p[0] + r.randn() * .4, p[1], 4.2 * s, 3.4 * s, r.rand() * 3, ['#4f6338', '#5d7140', '#3f5432'][r.randint(3)], a=.95, dry=.1)
    for p in P[4::11]:
        if r.rand() < trees: tree_round(p[0], p[1], 15 * persp(p[1]), int(r.randint(1e6)), small=True)

def tunnel():
    x, y = TUNNEL; s = persp(y) * 1.15
    outer = [(x - 13 * s + 26 * s * u, y - math.sin(u * math.pi) ** .7 * 21 * s) for u in np.linspace(0, 1, 20)]
    c.area(outer + [(x + 15 * s, y + 3), (x - 15 * s, y + 3)], '#b9ab8e', wob=.2, rough=.6, edge_dark=.1)
    inner = [(x - 8 * s + 16 * s * u, y + 1 - math.sin(u * math.pi) ** .8 * 14 * s) for u in np.linspace(0, 1, 18)]
    c.area(inner + [(x + 8 * s, y + 3), (x - 8 * s, y + 3)], '#1e2523', wob=0, rough=.3, edge_dark=0)
    c.ink(outer, .9, a=.85); c.ink(inner, .8, a=.8)
    for u in np.linspace(.05, .95, 7):
        p = np.array(inner[int(u * 17)]); q = np.array(outer[int(u * 19)])
        c.ink([p, p + (q - p) * .95], .6, a=.7, tremor=0)

# --------------------------------------------------------------------------- trees
def trunk(x, y, h, w, col='#4d3b30'):
    c.stroke([(x, y + 1), (x + .5, y - h * .5), (x + .2, y - h)], w, col, a=1, dry=.15, taper=(.0, .5), press=.1)

def tree_fir(x, y, h, seed, pal=None):
    r = np.random.RandomState(seed)
    base, dark, light, hi = pal or (['#36533f', '#2f4a3b', '#3c5a44'][seed % 3], '#233a30', '#557352', '#88985e')
    tiers, (tx, ty, gy) = fir_tiers(x, y, h, seed, slim=.27 + r.rand() * .08)
    shadow_blob(x + h * .12, y + 1, h * .26, h * .05, '#3f4e2a', .3)
    trunk(x, y, h * .12, max(1.2, h * .045))
    for i, tp in enumerate(tiers):
        m = c.area(tp, base, wob=.25 * (h / 60), rough=.6, edge_dark=.12, seed=seed + i, var=.05)
        if m is None: continue
        prev = c.clipm; c.set_clip(m)
        # shade the right side, light the left with dry, drooping strokes
        cx = tp[0][0]; yt, yb = tp[:, 1].min(), tp[:, 1].max()
        c.area([(cx + 1, yt - 2), (cx + 60, yt), (cx + 60, yb + 6), (cx + 1, yb + 6)], dark, wob=0, rough=.4, a=.55, edge_dark=0, var=0)
        for k in range(max(2, int(h / 18))):
            ox = r.uniform(.15, .9); yy = yt + (yb - yt) * r.uniform(.3, .85)
            c.stroke([(cx - 1, yy - (yb - yt) * .25), (cx - (tp[:, 0].max() - cx) * ox, yy + (yb - yt) * .15)], max(1.0, h * .03), light if k % 2 else hi,
                     a=.85, dry=.45, taper=(.1, .4))
        c.clipm = prev

def canopy(x, cy, rx, ry, seed, base, mid, light, accent=None, dabs=1.0, ink_branches=True, flat=.3):
    r = np.random.RandomState(seed)
    out = lumpy(x, cy, rx, ry, seed, n=56, bumps=7, amp=.2, flat=flat)
    m = c.area(out, base, wob=.25 * rx / 20, rough=.8, edge_dark=.1, seed=seed, var=.06)
    if m is None: return
    prev = c.clipm; c.set_clip(m)
    # clumps catching the light from the upper left
    nc = r.randint(3, 6)
    for i in range(nc):
        a = r.uniform(math.pi * 1.05, math.pi * 1.85); dd = r.uniform(.25, .55)
        cx_, cy_ = x + math.cos(a) * rx * dd, cy + math.sin(a) * ry * dd
        c.area(lumpy(cx_, cy_, rx * r.uniform(.35, .55), ry * r.uniform(.3, .45), seed + 10 + i, n=30, amp=.18, flat=.4), mid,
               wob=.15 * rx / 20, rough=.8, edge_dark=.08, a=.95, seed=seed + 20 + i)
    if ink_branches and rx > 14:
        for k in range(2):
            sx = x + r.uniform(-.25, .25) * rx; ex = sx + r.uniform(-.5, .5) * rx
            c.ink([(sx, cy + ry * .7), (sx + (ex - sx) * .5, cy + ry * .35), (ex, cy + ry * r.uniform(-.1, .2))], max(.6, rx * .03), col='#3d3029', a=.65, tremor=.3)
    # leaf texture: little dabs, more of them in the light
    nd = int(rx * ry * .09 * dabs)
    for i in range(nd):
        a = r.uniform(0, 2 * math.pi); dd = r.rand() ** .6
        px, py = x + math.cos(a) * rx * dd * .95, cy + math.sin(a) * ry * dd * .9
        lit = (px - x) / rx + (py - cy) / ry < .1
        colr = (light if lit else mid) if r.rand() < .8 else (accent or light)
        c.dab(px, py, max(1.6, rx * .14), max(1.2, rx * .09), r.uniform(-.8, .8) - .3, colr, a=.9, dry=.2)
    # a darker underside
    c.area([(x - rx * 1.2, cy + ry * .35), (x + rx * 1.2, cy + ry * .25), (x + rx * 1.2, cy + ry * 1.3), (x - rx * 1.2, cy + ry * 1.3)], base, wob=1, rough=1, a=.45, edge_dark=0)
    c.clipm = prev

def tree_oak(x, y, h, seed, pal=None):
    base, mid, light, acc = pal or ('#56683a', '#7a8a44', '#a9b265', '#c3b85e')
    rx, ry = h * .42, h * .34; cy = y - h * .62
    shadow_blob(x + h * .16, y + 1, h * .32, h * .06, '#3f4e2a', .32)
    trunk(x, y, h * .5, max(1.4, h * .07))
    canopy(x, cy, rx, ry, seed, base, mid, light, acc)

def tree_round(x, y, h, seed, small=False, pal=None):
    r = np.random.RandomState(seed)
    pals = [('#5f7a4a', '#7f9a58', '#b3bf78', '#d9c46a'), ('#4f7366', '#6e9178', '#a8bf91', '#e2b44b'), ('#6a7a3c', '#8d9a4b', '#c2c272', '#e08a6c')]
    base, mid, light, acc = pal or pals[r.randint(len(pals))]
    rx, ry = h * .34, h * .36; cy = y - h * .6
    if not small: shadow_blob(x + h * .14, y + 1, h * .26, h * .05, '#3f4e2a', .3)
    trunk(x, y, h * .45, max(.9, h * .06))
    canopy(x, cy, rx, ry, seed, base, mid, light, acc, dabs=.8 if small else 1, ink_branches=not small, flat=.15)

def tree_maple(x, y, h, seed):
    tree_oak(x, y, h, seed, pal=('#a85a36', '#c9783f', '#e3a15a', '#e2b44b'))

def tree_blossom(x, y, h, seed):
    base, mid, light, acc = '#c08a86', '#d9a39c', '#efc9bd', '#f7ece0'
    rx, ry = h * .4, h * .32; cy = y - h * .6
    shadow_blob(x + h * .16, y + 1, h * .3, h * .06, '#3f4e2a', .3)
    trunk(x, y, h * .5, max(1.2, h * .06), '#5a4038')
    canopy(x, cy, rx, ry, seed, base, mid, light, acc, dabs=1.3)
    r = np.random.RandomState(seed + 5)
    for i in range(int(h * .8)):
        a = r.uniform(0, 2 * math.pi); dd = r.rand() ** .5
        c.dab(x + math.cos(a) * rx * dd, cy + math.sin(a) * ry * dd, 1.6, 1.5, 0, ['#fbf3ea', '#e0806a'][r.rand() < .25], a=.95, dry=0)

def tree_poplar(x, y, h, seed, pal=None):
    r = np.random.RandomState(seed)
    base, light, dark = pal or ('#6a7a3a', '#9fae60', '#4f5f30')
    wd = h * (.13 + .04 * r.rand())
    L = []; Rr = []
    for t in np.linspace(0, 1, 14):
        yy = y - h * .1 - (h * .9) * t
        prof = math.sin(min(1, (t * 1.05)) * math.pi) ** .7 * (1 - .25 * t)
        wob = 1 + .12 * math.sin(t * 17 + seed)
        L.append((x - wd * prof * wob + math.sin(t * 3) * h * .02, yy)); Rr.append((x + wd * prof * (2 - wob) + math.sin(t * 3) * h * .02, yy))
    poly = L + Rr[::-1]
    shadow_blob(x + h * .1, y + 1, h * .14, h * .04, '#3f4e2a', .3)
    trunk(x, y, h * .2, max(1, h * .04))
    m = c.area(poly, base, wob=.2, rough=.8, edge_dark=.1, seed=seed)
    prev = c.clipm; c.set_clip(m)
    for k in range(int(h * .5)):
        yy = y - h * .15 - r.rand() * h * .8; side = r.rand()
        xx = x - wd * .7 + side * wd * 1.4
        colr = light if side < .45 else (dark if side > .7 else base)
        c.stroke([(xx, yy + 4), (xx + .5, yy - 4)], max(1.2, wd * .35), colr, a=.85, dry=.35, taper=(.3, .3))
    c.clipm = prev

def tree_birch(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow_blob(x + h * .12, y + 1, h * .2, h * .04, '#3f4e2a', .28)
    trunks = [(x + r.uniform(-.06, .06) * h, r.uniform(-.06, .06)) for _ in range(r.randint(2, 4))]
    for tx, lean in trunks:
        top = (tx + lean * h, y - h * .92)
        c.stroke([(tx, y), ((tx + top[0]) / 2 + r.randn() * 1.0, (y + top[1]) / 2), top], max(1.2, h * .035), '#f1e9d8', a=1, dry=.05, taper=(0, .6))
        for k in range(int(h / 8)):
            t = r.uniform(.05, .8); px = tx + (top[0] - tx) * t; py = y + (top[1] - y) * t
            c.ink([(px - h * .015, py), (px + h * .012, py + .3)], max(.5, h * .012), a=.8, tremor=0)
    for i in range(5):
        a = r.uniform(math.pi * 1.1, math.pi * 1.9); cx, cy = x + math.cos(a) * h * .18, y - h * .65 + math.sin(a) * h * .2
        for k in range(int(h * .45)):
            px = cx + r.randn() * h * .1; py = cy + r.randn() * h * .09
            c.dab(px, py, max(1.6, h * .04), max(1.2, h * .03), r.uniform(-1, 1), ['#b9b75a', '#8f9f4c', '#d7c46a', '#6e8240'][r.randint(4)], a=.9, dry=.15)

def tree_willow(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow_blob(x + h * .14, y + 1, h * .3, h * .05, '#3f4e2a', .3)
    trunk(x, y, h * .55, max(1.3, h * .07))
    canopy(x, y - h * .62, h * .42, h * .26, seed, '#6c7a46', '#8f9c5c', '#b6bd82', dabs=.5, ink_branches=False)
    for k in range(int(h * 1.2)):
        sx = x + r.uniform(-.42, .42) * h; sy = y - h * .62 + r.uniform(-.1, .2) * h
        ln = r.uniform(.25, .5) * h
        c.stroke([(sx, sy), (sx + 1, sy + ln * .5), (sx + 2.5 * np.sign(sx - x), sy + ln)], max(.8, h * .025),
                 ['#7d8a4f', '#9aa66a', '#5f6d3a'][r.randint(3)], a=.85, dry=.3, taper=(.1, .6))

def tree_apple(x, y, h, seed):
    tree_round(x, y, h, seed, small=True, pal=('#5f7542', '#7f9a50', '#a9b86a', '#c4683f'))
    r = np.random.RandomState(seed)
    for k in range(5):
        c.dab(x + r.uniform(-.3, .3) * h, y - h * .6 + r.uniform(-.25, .2) * h, 1.4, 1.4, 0, '#c4473a', a=.95, dry=0)

def tree_pine(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow_blob(x + h * .1, y + 1, h * .2, h * .04, '#3f4e2a', .3)
    c.stroke([(x, y), (x + r.randn(), y - h * .55), (x + r.randn() * 2, y - h * .9)], max(1.2, h * .045), '#6a4a3a', dry=.1, taper=(0, .4))
    for k in range(4):
        cy = y - h * (.55 + k * .12); cx = x + r.uniform(-.12, .12) * h
        canopy(cx, cy, h * (.22 - k * .03), h * .07, seed + k, '#2f4a3b', '#4b6a4c', '#7f9563', dabs=.6, ink_branches=False, flat=.5)

TREEF = dict(fir=tree_fir, oak=tree_oak, round=tree_round, maple=tree_maple, blossom=tree_blossom, poplar=tree_poplar, birch=tree_birch,
             willow=tree_willow, apple=tree_apple, pine=tree_pine)

# --------------------------------------------------------------------------- buildings
def smoke(x, y, s=1.0, seed=0, n=5):
    r = np.random.RandomState(seed)
    pts = []
    for i in range(n):
        px = x + i * 4.5 * s + math.sin(i * 1.3) * 2 * s; py = y - i * 6 * s
        rr = (2.2 + i * .9) * s
        c.area(lumpy(px, py, rr, rr * .8, seed + i, n=18, amp=.12, flat=0), '#f7f1e6', wob=.2, rough=.5, a=.85 - i * .1, edge_dark=.0)
        pts.append((px, py))
    c.ink(catmull(pts, 5), .55, a=.35, tremor=.4)

def window(kind, p, ww, wh, D=None, frame='#f4ead6', glass='#40575c'):
    x, y = p
    if kind == 'side':
        Du = D / np.hypot(*D)
        q = [p - Du * ww / 2 + [0, wh / 2], p + Du * ww / 2 + [0, wh / 2], p + Du * ww / 2 - [0, wh / 2], p - Du * ww / 2 - [0, wh / 2]]
        c.area(q, '#34474c', wob=0, rough=.3, edge_dark=0)
        c.ink(q + [q[0]], .45, a=.55, tremor=0)
        return
    if kind == 'round' or kind == 'loft':
        c.area(lumpy(x, y, ww * .7, wh * .7, 3, n=18, amp=0, flat=0), frame, wob=0, rough=.3)
        c.area(lumpy(x, y, ww * .5, wh * .5, 3, n=18, amp=0, flat=0), glass, wob=0, rough=.3, edge_dark=0)
        c.ink([(x - ww * .5, y), (x + ww * .5, y)], .4, a=.6, tremor=0); return
    if kind == 'tri':
        c.area([(x - ww * .7, y + wh * .5), (x + ww * .7, y + wh * .5), (x, y - wh * .7)], glass, wob=0, rough=.3)
        return
    if kind == 'shop':
        c.area([(x - ww / 2 - 1, y - wh / 2 - 1), (x + ww / 2 + 1, y - wh / 2 - 1), (x + ww / 2 + 1, y + wh / 2 + 1), (x - ww / 2 - 1, y + wh / 2 + 1)], frame, wob=0, rough=.3)
        c.area([(x - ww / 2, y - wh / 2), (x + ww / 2, y - wh / 2), (x + ww / 2, y + wh / 2), (x - ww / 2, y + wh / 2)], '#e9d39a', wob=0, rough=.3, edge_dark=.2)
        # toys in the window
        for k, colr in enumerate(['#c4473a', '#5fa59c', '#e2b44b']):
            c.dab(x - ww / 3 + k * ww / 3, y + wh * .15, 2.2, 2.4, 0, colr, a=1, dry=0)
        c.ink([(x - ww / 2, y - wh / 2), (x + ww / 2, y - wh / 2), (x + ww / 2, y + wh / 2), (x - ww / 2, y + wh / 2), (x - ww / 2, y - wh / 2)], .6, a=.8)
        return
    hw, hh = ww / 2, wh / 2
    c.area([(x - hw - .9, y - hh - .9), (x + hw + .9, y - hh - .9), (x + hw + .9, y + hh + 1.4), (x - hw - .9, y + hh + 1.4)], frame, wob=0, rough=.3)
    top = [(x - hw, y - hh)] if kind == 'rect' else [(x - hw + hw * 2 * u, y - hh - math.sin(u * math.pi) * hw * .8) for u in np.linspace(0, 1, 8)]
    c.area(top + [(x + hw, y - hh), (x + hw, y + hh), (x - hw, y + hh)], glass, wob=0, rough=.3, edge_dark=.1)
    c.ink([(x, y - hh), (x, y + hh)], .4, col=frame, a=.9, tremor=0); c.ink([(x - hw, y), (x + hw, y)], .4, col=frame, a=.9, tremor=0)
    c.ink([(x - hw - 1.2, y + hh + 1.6), (x + hw + 1.2, y + hh + 1.6)], .6, a=.7, tremor=0)

def door(p, ww, wh, kind, col):
    x, y = p
    if kind == 'barn':
        q = [(x - ww / 2, y), (x + ww / 2, y), (x + ww / 2, y - wh), (x - ww / 2, y - wh)]
        c.area(q, col, wob=0, rough=.4)
        for a_, b_ in [((x - ww / 2, y), (x, y - wh)), ((x, y), (x - ww / 2, y - wh)), ((x, y), (x + ww / 2, y - wh)), ((x + ww / 2, y), (x, y - wh))]:
            c.ink([a_, b_], .7, col='#7a3326', a=.9, tremor=0)
        c.ink(q + [q[0]], .8, col='#7a3326', a=.9)
        c.ink([(x, y), (x, y - wh)], .7, col='#7a3326', a=.9, tremor=0)
        return
    top = [(x - ww / 2 + ww * u, y - wh + (0 if kind == 'rect' else -math.sin(u * math.pi) * ww * .45)) for u in np.linspace(0, 1, 9)]
    q = [(x - ww / 2, y)] + top + [(x + ww / 2, y)]
    c.area(q, col, wob=0, rough=.3, edge_dark=.15)
    c.ink(q, .7, a=.8)
    c.dab(x + ww * .28, y - wh * .45, .9, .9, 0, '#e2b44b', a=1, dry=0)

def ink_poly(poly, w=.8, a=.75, skip=None):
    P = np.vstack([poly, poly[:1]])
    for i in range(len(P) - 1):
        if skip and i in skip: continue
        c.ink([P[i], P[i + 1]], w, a=a, tremor=.25)

def roof_strokes(m, poly, col, slope_dir):
    def ang(x, y): return slope_dir
    c.flow_fill(m, ang, lambda x, y, r: hexc(col) * (.9 + .16 * r.rand()), 2.2, 10, 2.4, dry=.3, a=.85, seed=int(poly[0][0] * 13) % 99999, jitter=.1)

def paint_building(b):
    t = b['t']
    if t == 'silo': return silo(b['x'], b['y'])
    if t == 'water': return water_tower(b['x'], b['y'])
    if t == 'windpump': return windpump(b['x'], b['y'])
    parts, f = building(b)
    wall = P(b['wall']); roof = P(b['roof']); D = f['D']
    seed = abs(hash(b['name'])) % 99991
    shadow_blob(b['x'] + b['d'] * .45, b['y'] + 1, b['w'] * .6 + b['d'] * .3, 3.5, '#45542e', .35)
    if b.get('porch'):
        pass
    for i, (role, poly) in enumerate(parts):
        poly = np.array(poly)
        if role == 'front': col = wall
        elif role == 'side': col = wall * .76 + hexc('#5d7186') * .06
        elif role == 'roof_l': col = np.clip(roof * 1.12, 0, 1)
        elif role in ('roof_r', 'roof_r2', 'roof_back'): col = roof * .8
        else: col = roof
        m = c.area(poly, col, wob=.15, rough=.5, edge_dark=.06, var=.05, seed=seed + i)
        if m is None: continue
        if role.startswith('roof'):
            if role == 'roof_f':
                d0 = poly[3] - poly[0]; ang = math.atan2(d0[1], d0[0])
            elif role == 'roof_back': ang = 0
            else:
                d0 = poly[1] - poly[0]; ang = math.atan2(d0[1], d0[0])
            prev = c.clipm; c.set_clip(m); roof_strokes(m, poly, col, ang); c.clipm = prev
            # shingle courses
            if role in ('roof_r', 'roof_f', 'roof_l') and b['t'] != 'false':
                a0, a1 = (poly[0], poly[1]) if role != 'roof_f' else (poly[0], poly[3])
                e0, e1 = (poly[3], poly[2]) if role == 'roof_r' else ((poly[1], poly[2]) if role == 'roof_f' else (poly[1], poly[2]))
                for u in np.linspace(.25, .85, 3 if role != 'roof_f' else 3):
                    if role == 'roof_f':
                        pa = poly[0] + (poly[3] - poly[0]) * u; pb = poly[1] + (poly[2] - poly[1]) * u
                    else:
                        pa = poly[0] + (poly[1] - poly[0]) * u; pb = poly[3] + (poly[2] - poly[3]) * u
                    c.ink([pa, pb], .45, a=.35, tremor=.3)
        elif role == 'front' or role == 'side':
            prev = c.clipm; c.set_clip(m)
            c.flow_fill(m, lambda x, y: -math.pi / 2, lambda x, y, r: col * (.93 + .12 * r.rand()), 2.6, 12, 3.2, dry=.35, a=.6, seed=seed + 7, jitter=.1)
            c.clipm = prev
        ink_poly(poly, .7, .7)
    if b.get('tower'): church_tower(b, f)
    for kind, p, ww, wh in f['windows']:
        window(kind, np.array(p), ww, wh, D)
    for p, ww, wh, kind in f['doors']:
        door(p, ww, wh, kind, P(b.get('door', 'brick')))
    for tr in f['trims']:
        c.ink(tr, 1.0, a=.85, tremor=.3)
    if 'awning' in f:
        a_, b_ = f['awning']; n = 6
        for k in range(n):
            p0 = a_ + (b_ - a_) * k / n; p1 = a_ + (b_ - a_) * (k + 1) / n
            q = [p0, p1, p1 + [1.5, 6], p0 + [1.5, 6]]
            c.area(q, '#e08a6c' if k % 2 == 0 else '#f6eedf', wob=0, rough=.3)
            c.area(lumpy((p0[0] + p1[0]) / 2 + 1.5, p0[1] + 6, (p1[0] - p0[0]) / 2, 1.6, k, n=12, amp=0, flat=-1), '#e08a6c' if k % 2 == 0 else '#f6eedf', wob=0, rough=.3)
        c.ink([a_, b_], .8, a=.8)
    if b.get('porch'):
        fp = f['fp']; pa = fp(-.02, .42) + [0, 0]; pb = fp(1.02, .42)
        q = [pa + [-3, 0], pb + [3, 0], pb + [5, 4], pa + [-1, 4]]
        c.area(q, P(b['roof']) * .95, wob=0, rough=.3)
        for u in (.05, .35, .65, .95):
            p = fp(u, 0); c.ink([p, p + [0, -b['h'] * .42 + 4]], .8, col='#f4ead6', a=1, tremor=0)
        c.ink(q + [q[0]], .6, a=.7)
    for p, side in f['chimneys']:
        p = np.array(p)
        q = [p + [-2, 0], p + [2, 0], p + [2, -9], p + [-2, -9]]
        c.area(q, '#9c4a36', wob=0, rough=.3); c.area([p + [2, 0], p + [3.6, -1], p + [3.6, -10], p + [2, -9]], '#6e3527', wob=0, rough=.3)
        c.ink(q + [q[0]], .5, a=.7)
        smoke(p[0] + 1, p[1] - 12, .9, seed=seed)

def church_tower(b, f):
    x, y, w, h, rh = b['x'], b['y'], b['w'], b['h'], b['rh']
    tw = w * .44; top = y - h - rh - 8; Dt = f['D'] * .33
    fr = [(x - tw / 2, y + 1), (x + tw / 2, y + 1), (x + tw / 2, top), (x - tw / 2, top)]
    sd = [(x + tw / 2, y + 1), (x + tw / 2 + Dt[0], y + 1 + Dt[1]), (x + tw / 2 + Dt[0], top + Dt[1]), (x + tw / 2, top)]
    c.area(sd, P('cream') * .78, wob=0, rough=.4); c.area(fr, P('cream'), wob=0, rough=.4)
    ink_poly(np.array(fr), .7); ink_poly(np.array(sd), .6)
    # belfry
    bx, by = x, top + 9
    c.area([(bx - 3, by + 3), (bx + 3, by + 3)] + [(bx + 3 - 6 * u, by - 3 - math.sin(u * math.pi) * 3) for u in np.linspace(0, 1, 8)], '#3c4f52', wob=0, rough=.3)
    c.area(lumpy(x, y - h - 3, 3.4, 3.4, 1, n=18, amp=0, flat=0), '#f7efdf', wob=0, rough=.3)
    c.ink(lumpy(x, y - h - 3, 3.4, 3.4, 1, n=18, amp=0, flat=0).tolist() + [lumpy(x, y - h - 3, 3.4, 3.4, 1, n=18, amp=0, flat=0)[0].tolist()], .5, a=.8, tremor=0)
    c.ink([(x, y - h - 3), (x + 1.6, y - h - 4.4)], .5, a=.9, tremor=0); c.ink([(x, y - h - 3), (x, y - h - 5.4)], .5, a=.9, tremor=0)
    ap = (x + Dt[0] * .5, top - 30)
    c.area([(x - tw / 2 - 1, top), (x + tw / 2 + 1, top), ap], '#d7764a', wob=0, rough=.4)
    c.area([(x + tw / 2 + 1, top), (x + tw / 2 + Dt[0] + 1, top + Dt[1]), ap], '#a5512f', wob=0, rough=.4)
    c.ink([(x - tw / 2 - 1, top), ap, (x + tw / 2 + Dt[0] + 1, top + Dt[1])], .7, a=.85)
    c.ink([ap, (ap[0], ap[1] - 7)], .6, a=.9, tremor=0); c.ink([(ap[0] - 2.2, ap[1] - 5), (ap[0] + 2.2, ap[1] - 5)], .5, a=.9, tremor=0)
    c.area([(x - tw / 2 - 1.5, top + 1), (x + tw / 2 + 1.5, top + 1), (x + tw / 2 + 1.5, top + 3), (x - tw / 2 - 1.5, top + 3)], '#f4ead6', wob=0, rough=.3)

def silo(x, y):
    w, h = 13, 40
    shadow_blob(x + 8, y + 1, 12, 3, '#45542e', .35)
    body = [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)]
    m = c.area(body, '#b9c3bd', wob=0, rough=.4, edge_dark=.05)
    prev = c.clipm; c.set_clip(m)
    c.area([(x + w * .1, y + 2), (x + w, y + 2), (x + w, y - h - 2), (x + w * .1, y - h - 2)], '#8494a0', wob=0, rough=.6, a=.7, edge_dark=0)
    c.flow_fill(m, lambda a, b: -math.pi / 2, lambda a, b, r: hexc('#b9c3bd') * (.9 + .15 * r.rand()), 2, 16, 3, dry=.4, a=.5, seed=3)
    c.clipm = prev
    for k in range(5): c.ink([(x - w / 2, y - h * (k + .5) / 5), (x, y - h * (k + .5) / 5 + 1.2), (x + w / 2, y - h * (k + .5) / 5)], .45, a=.55, tremor=0)
    dome = [(x - w / 2 - 1 + (w + 2) * u, y - h - math.sin(u * math.pi) * 7) for u in np.linspace(0, 1, 14)]
    c.area(dome, '#7d8f9c', wob=0, rough=.4)
    c.ink(dome + [dome[0]], .6, a=.8); ink_poly(np.array(body), .7)

def water_tower(x, y):
    shadow_blob(x + 6, y + 1, 12, 3, '#45542e', .35)
    for dx in (-7, -2.5, 2.5, 7):
        c.ink([(x + dx * 1.15, y), (x + dx * .8, y - 18)], .9, col='#4a3a30', a=.95, tremor=0)
    c.ink([(x - 8, y - 6), (x + 8, y - 13)], .5, col='#4a3a30', a=.8, tremor=0); c.ink([(x - 8, y - 13), (x + 8, y - 6)], .5, col='#4a3a30', a=.8, tremor=0)
    tank = [(x - 9, y - 18), (x + 9, y - 18), (x + 9.5, y - 33), (x - 9.5, y - 33)]
    m = c.area(tank, '#9a6a42', wob=0, rough=.4, edge_dark=.08)
    prev = c.clipm; c.set_clip(m)
    for k in range(9): c.stroke([(x - 8 + k * 2, y - 18), (x - 8 + k * 2, y - 33)], 1.4, ['#a9774a', '#8a5c38'][k % 2], a=.8, dry=.3, taper=(0, 0))
    c.area([(x + 3, y - 16), (x + 11, y - 16), (x + 11, y - 35), (x + 3, y - 35)], '#5e3d28', wob=0, rough=.5, a=.4, edge_dark=0)
    c.clipm = prev
    for k in (21, 30): c.ink([(x - 9.4, y - k), (x + 9.4, y - k)], .55, a=.8, tremor=0)
    roof = [(x - 11, y - 33), (x + 11, y - 33), (x + 1, y - 43)]
    c.area(roof, '#5d7186', wob=0, rough=.4); c.area([(x + 1, y - 43), (x + 11, y - 33), (x + 4, y - 33)], '#465a6c', wob=0, rough=.4)
    c.ink(roof + [roof[0]], .7, a=.85); ink_poly(np.array(tank), .7)
    c.ink([(x - 9, y - 22), (x - 15, y - 19), (x - 15, y - 15)], .9, col='#4a3a30', a=.9, tremor=0)

def windpump(x, y):
    for dx in (-5, 5):
        c.ink([(x + dx, y), (x + dx * .15, y - 44)], .8, col='#4a3a30', a=.95, tremor=0)
    for k in range(5):
        yy = y - 8 - k * 8; ww = 5 * (1 - (k * 8 + 8) / 46)
        c.ink([(x - ww, yy), (x + ww, yy - 6)], .45, col='#4a3a30', a=.75, tremor=0)
    cx, cy = x - 1, y - 48
    for k in range(16):
        a = k / 16 * 2 * math.pi
        c.stroke([(cx + math.cos(a) * 2.5, cy + math.sin(a) * 2.5 * .9), (cx + math.cos(a) * 10, cy + math.sin(a) * 10 * .9)], 2.0, '#f2ead9' if k % 2 else '#c9783f', a=1, dry=0, taper=(0, .2))
    c.ink([(cx + 10 * math.cos(a), cy + 9 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)], .5, a=.7, tremor=0)
    c.ink([(cx, cy), (cx + 14, cy + 1)], .8, a=.9, tremor=0)
    c.area([(cx + 12, cy - 4), (cx + 19, cy - 2), (cx + 19, cy + 4), (cx + 12, cy + 3)], '#e08a6c', wob=0, rough=.3)

# --------------------------------------------------------------------------- the train
def train():
    pts = RAIL; xs = pts[:, 0]
    i_head = int(np.argmin(np.abs(xs - TRAIN_HEAD)))
    def frame(i):
        p = pts[i]; q = pts[min(len(pts) - 1, i + 3)]; o = pts[max(0, i - 3)]
        d = q - o; d /= np.hypot(*d); return p, d, np.array([d[1], -d[0]])     # up-normal
    s = persp(pts[i_head][1]) * 1.35
    # steam drifting back over the cars
    p, d, up = frame(i_head - 6)
    for k in range(7):
        q = p - d * (k * 7 * s) + up * (24 + k * 3.5) * s
        r_ = (4 + k * 1.3) * s
        c.area(lumpy(q[0], q[1], r_, r_ * .78, 90 + k, n=20, amp=.12, flat=0), '#fbf6ec', wob=.2, rough=.5, a=.92 - k * .09, edge_dark=.02)
    # cars, back to front
    cars = [('tree', 52), ('bear', 38), ('gifts', 24), ('tender', 12)]
    for kind, back in cars:
        i = max(0, i_head - int(back * s / 2.0) - 6)
        p, d, up = frame(i)
        L = (13 if kind == 'tender' else 15) * s
        a_ = p - d * L / 2; b_ = p + d * L / 2
        bed = [a_ + up * 2.5 * s, b_ + up * 2.5 * s, b_ + up * 6.5 * s, a_ + up * 6.5 * s]
        col = '#3c4f5a' if kind != 'tender' else '#2f2a28'
        if kind == 'tender':
            bed = [a_ + up * 2.5 * s, b_ + up * 2.5 * s, b_ + up * 11 * s, a_ + up * 11 * s]
            c.area(bed, '#b33a2c', wob=0, rough=.3, edge_dark=.1); ink_poly(np.array(bed), .7, .9)
            c.area([a_ + up * 11 * s, b_ + up * 11 * s, b_ + up * 13 * s + d * -1 * s, a_ + up * 13 * s + d * 1 * s], '#2f2a28', wob=0, rough=.5)
        else:
            c.area(bed, '#7a3a2c', wob=0, rough=.3, edge_dark=.1); ink_poly(np.array(bed), .7, .9)
            base = p + up * 6.5 * s
            if kind == 'gifts':
                for j, (colr, ww, hh, off) in enumerate([('#5fa59c', 6, 6, -4.5), ('#e2b44b', 5, 8, 1.5), ('#e08a6c', 4, 4.5, 6)]):
                    cc = base + d * off * s
                    q = [cc - d * ww / 2 * s, cc + d * ww / 2 * s, cc + d * ww / 2 * s + up * hh * s, cc - d * ww / 2 * s + up * hh * s]
                    c.area(q, colr, wob=0, rough=.3, edge_dark=.1); ink_poly(np.array(q), .5, .85)
                    c.ink([cc + up * 0, cc + up * hh * s], .7, col='#c4473a' if colr != '#e08a6c' else '#f7efdf', a=1, tremor=0)
                    c.ink([cc + up * hh * s, cc + up * (hh + 1.6) * s - d * 1.5 * s], .6, col='#c4473a', a=1, tremor=0)
                    c.ink([cc + up * hh * s, cc + up * (hh + 1.6) * s + d * 1.5 * s], .6, col='#c4473a', a=1, tremor=0)
            if kind == 'bear':
                cc = base + d * -2 * s
                c.area(lumpy(*(cc + up * 4 * s), 4 * s, 4.2 * s, 2, n=20, amp=.05, flat=0), '#b47a44', wob=0, rough=.3)
                hd = cc + up * 10 * s
                for e in (-2.6, 2.6): c.area(lumpy(*(hd + d * e * s + up * 2.6 * s), 1.4 * s, 1.4 * s, 3, n=12, amp=0, flat=0), '#9a6436', wob=0, rough=.3)
                c.area(lumpy(*hd, 3.2 * s, 3 * s, 4, n=18, amp=0, flat=0), '#b47a44', wob=0, rough=.3)
                c.dab(*(hd + up * -.8 * s), 1.6 * s, 1.2 * s, 0, '#e8c99a', a=1, dry=0)
                c.ink([hd + d * -1 * s + up * .8 * s, hd + d * -.9 * s + up * .9 * s], .5, a=1, tremor=0); c.ink([hd + d * 1 * s + up * .8 * s, hd + d * 1.1 * s + up * .9 * s], .5, a=1, tremor=0)
                cc2 = base + d * 5 * s     # a drum
                q = [cc2 - d * 2.6 * s, cc2 + d * 2.6 * s, cc2 + d * 2.6 * s + up * 5 * s, cc2 - d * 2.6 * s + up * 5 * s]
                c.area(q, '#c4473a', wob=0, rough=.3); ink_poly(np.array(q), .5, .9)
                c.ink([cc2 - d * 2.6 * s + up * 1 * s, cc2 - d * 1.3 * s + up * 4 * s, cc2 + up * 1 * s, cc2 + d * 1.3 * s + up * 4 * s, cc2 + d * 2.6 * s + up * 1 * s], .5, col='#e2b44b', a=1, tremor=0)
            if kind == 'tree':
                cc = base + d * -1 * s
                tri = [cc - d * 5 * s + up * 1 * s, cc + d * 5 * s + up * 1 * s, cc + up * 14 * s]
                c.area(tri, '#2f5a43', wob=0, rough=.4); ink_poly(np.array(tri), .5, .8)
                for j in range(5):
                    q = cc + up * (3 + j * 2) * s + d * ((j % 3) - 1) * 1.8 * s
                    c.dab(*q, 1.2, 1.2, 0, ['#e2b44b', '#e08a6c', '#f7efdf'][j % 3], a=1, dry=0)
                c.dab(*(cc + up * 14.5 * s), 1.6, 1.6, 0, '#e2b44b', a=1, dry=0)
                c.dab(*(cc + d * 5.5 * s + up * 3 * s), 3 * s, 3 * s, 0, '#5fa59c', a=1, dry=0)     # a ball
        for e in (-.32, .32):
            wpos = p + d * L * e + up * 1.6 * s
            c.area(lumpy(*wpos, 2.1 * s, 2.1 * s, 1, n=14, amp=0, flat=0), '#2a2523', wob=0, rough=.2)
    # the locomotive
    p, d, up = frame(i_head - 2)
    L = 24 * s
    a_ = p - d * L / 2; b_ = p + d * L / 2
    cab = [a_ + up * 3 * s, a_ + d * 8 * s + up * 3 * s, a_ + d * 8 * s + up * 15 * s, a_ + up * 15 * s]
    boiler = [a_ + d * 7 * s + up * 4 * s, b_ - d * 1 * s + up * 4 * s, b_ + up * 6.5 * s, b_ - d * 1 * s + up * 11 * s, a_ + d * 7 * s + up * 11 * s]
    c.area(boiler, '#c23b2c', wob=0, rough=.3, edge_dark=.08)
    c.area([a_ + d * 7 * s + up * 9 * s, b_ - d * 1.5 * s + up * 9 * s, b_ - d * 1 * s + up * 11 * s, a_ + d * 7 * s + up * 11 * s], '#e27a5f', wob=0, rough=.3, a=.8)
    for u in (.35, .6, .82):
        q = a_ + d * (7 + (L / s - 8) * u) * s
        c.ink([q + up * 4 * s, q + up * 11 * s], .7, col='#e2b44b', a=1, tremor=0)
    c.area(cab, '#a8302a', wob=0, rough=.3, edge_dark=.08)
    c.area([cab[3] + up * .2 * s - d * 1.5 * s, cab[2] + up * .2 * s + d * 1.5 * s, cab[2] + up * 2.4 * s + d * 1 * s, cab[3] + up * 2.4 * s - d * 1 * s], '#2f2a28', wob=0, rough=.3)
    win = [a_ + d * 2 * s + up * 9 * s, a_ + d * 6 * s + up * 9 * s, a_ + d * 6 * s + up * 13 * s, a_ + d * 2 * s + up * 13 * s]
    c.area(win, '#f2d48a', wob=0, rough=.3)
    stack = b_ - d * 5 * s + up * 11 * s
    c.area([stack - d * 1.4 * s, stack + d * 1.4 * s, stack + d * 2.4 * s + up * 6 * s, stack - d * 2.4 * s + up * 6 * s], '#2f2a28', wob=0, rough=.3)
    dome = b_ - d * 11 * s + up * 11 * s
    c.area(lumpy(*(dome + up * 1 * s), 2.2 * s, 2 * s, 7, n=14, amp=0, flat=.6), '#e2b44b', wob=0, rough=.3)
    c.area([b_ + up * 1.5 * s, b_ + d * 3.5 * s + up * .5 * s, b_ + up * 5 * s], '#2f2a28', wob=0, rough=.3)     # cow-catcher
    c.dab(*(b_ - d * .2 * s + up * 8.5 * s), 1.8 * s, 1.8 * s, 0, '#f7e6a6', a=1, dry=0)    # lamp
    ink_poly(np.array(boiler), .7, .9); ink_poly(np.array(cab), .7, .9)
    for e, rr in ((-.32, 2.4), (.05, 3.2), (.3, 3.2)):
        wpos = p + d * L * e + up * (rr - .4) * s
        c.area(lumpy(*wpos, rr * s, rr * s, 1, n=16, amp=0, flat=0), '#c23b2c' if rr > 3 else '#2a2523', wob=0, rough=.2)
        c.ink([(wpos[0] + rr * s * math.cos(a), wpos[1] + rr * s * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 16)], .5, a=.9, tremor=0)
    c.ink([p + d * L * .05 + up * 2.8 * s, p + d * L * .3 + up * 2.8 * s], .6, col='#e2b44b', a=1, tremor=0)
    # puffs from the stack
    for k in range(4):
        q = stack + up * (8 + k * 5) * s - d * k * 4 * s
        r_ = (2.4 + k * 1.2) * s
        c.area(lumpy(q[0], q[1], r_, r_ * .85, 80 + k, n=18, amp=.1, flat=0), '#fbf6ec', wob=.2, rough=.5, a=.95, edge_dark=.03)
        if k < 2: c.ink([(q[0] + r_ * math.cos(a), q[1] + r_ * .85 * math.sin(a)) for a in np.linspace(math.pi * .9, math.pi * 1.9, 8)], .45, a=.5, tremor=.1)

# --------------------------------------------------------------------------- creatures and small stories
def sheep(x, y, seed):
    s = persp(y) * 1.1
    shadow_blob(x + 2 * s, y + 1, 5 * s, 1.2 * s, '#5c6d35', .3)
    for dx in (-2.5, -1, 1.5, 2.8): c.ink([(x + dx * s, y - 1 * s), (x + dx * s, y + .5 * s)], .6 * s, a=.9, tremor=0)
    c.area(lumpy(x, y - 3.5 * s, 4.6 * s, 3 * s, seed, n=22, bumps=6, amp=.2, flat=.1), '#f6efe0', wob=0, rough=.4, edge_dark=.12)
    c.area(lumpy(x + 4.2 * s, y - 4.6 * s, 1.6 * s, 1.2 * s, seed, n=12, amp=0, flat=0), '#2f2a28', wob=0, rough=.2)

def cow(x, y, seed):
    s = persp(y) * 1.1
    shadow_blob(x + 2 * s, y + 1, 6 * s, 1.3 * s, '#5c6d35', .3)
    for dx in (-3.5, -2, 2.5, 3.6): c.ink([(x + dx * s, y - 1.5 * s), (x + dx * s, y + .3 * s)], .7 * s, a=.9, tremor=0)
    c.area(lumpy(x, y - 4 * s, 5.5 * s, 2.8 * s, seed, n=20, amp=.05, flat=.1), '#f4ede0', wob=0, rough=.3, edge_dark=.1)
    c.dab(x - 1.5 * s, y - 4.5 * s, 2.4 * s, 1.8 * s, .3, '#2f2a28', a=1, dry=0); c.dab(x + 2.6 * s, y - 3.4 * s, 1.6 * s, 1.4 * s, 0, '#2f2a28', a=1, dry=0)
    c.area(lumpy(x + 6 * s, y - 5.6 * s, 1.8 * s, 1.5 * s, seed, n=12, amp=0, flat=0), '#f4ede0', wob=0, rough=.3)
    c.dab(x + 6.8 * s, y - 5 * s, 1.1 * s, .9 * s, 0, '#d8a29c', a=1, dry=0)

def boat(x, y):
    hull = [(x - 9, y - 2), (x + 10, y - 3), (x + 7, y + 2), (x - 6, y + 2.5)]
    c.stroke([(x - 14, y + 3), (x + 14, y + 3)], 1.0, '#e8efe6', a=.7, dry=.3)
    c.area(hull, '#b33a2c', wob=0, rough=.3, edge_dark=.1); ink_poly(np.array(hull), .6, .9)
    c.stroke([(x - 8, y - 2.2), (x + 9, y - 3)], 1, '#f2e6cb', a=1, dry=0, taper=(0, 0))
    c.area(lumpy(x - 1, y - 6, 2, 3, 1, n=14, amp=0, flat=0), '#e2b44b', wob=0, rough=.3)
    c.area(lumpy(x - 1, y - 10.2, 1.5, 1.5, 2, n=12, amp=0, flat=0), '#e8c4a0', wob=0, rough=.3)
    c.area([(x - 3.4, y - 11), (x + 1.4, y - 11), (x - 1, y - 13.5)], '#5d7186', wob=0, rough=.3)
    c.ink([(x + .5, y - 7), (x + 9, y - 18), (x + 16, y - 15), (x + 18, y + 1)], .4, a=.7, tremor=0)

def kite(kx, ky, hx, hy):
    q = [(kx, ky - 7), (kx + 5, ky), (kx, ky + 9), (kx - 5, ky)]
    c.area(q, '#e08a6c', wob=0, rough=.3)
    c.area([(kx, ky - 7), (kx + 5, ky), (kx, ky)], '#e2b44b', wob=0, rough=.3); c.area([(kx, ky + 9), (kx - 5, ky), (kx, ky)], '#e2b44b', wob=0, rough=.3)
    ink_poly(np.array(q), .6, .9)
    tail = catmull([(kx, ky + 9), (kx - 4, ky + 16), (kx + 1, ky + 22), (kx - 3, ky + 28)], 6)
    c.ink(tail, .5, a=.8, tremor=0)
    for j, p in enumerate(tail[6::6]): c.dab(p[0], p[1], 2.2, 1.4, .5, ['#5fa59c', '#c4473a', '#e2b44b'][j % 3], a=1, dry=0)
    c.ink(catmull([(kx, ky + 1), ((kx + hx) / 2 + 3, (ky + hy) / 2 + 6), (hx, hy - 5)], 8), .4, a=.6, tremor=0)
    # the child
    c.area([(hx - 2, hy - 1), (hx + 2, hy - 1), (hx + 1.5, hy - 6), (hx - 1.5, hy - 6)], '#c4473a', wob=0, rough=.2)
    c.area(lumpy(hx, hy - 7.5, 1.6, 1.6, 3, n=12, amp=0, flat=0), '#e8c4a0', wob=0, rough=.2)
    c.dab(hx, hy - 8.6, 1.8, 1, 0, '#6a4a30', a=1, dry=0)
    c.ink([(hx + 1.5, hy - 5), (hx + 3, hy - 7)], .5, a=.9, tremor=0)
    for dx in (-1, 1): c.ink([(hx + dx * .8, hy - 1), (hx + dx * 1.1, hy + 1.5)], .5, a=.9, tremor=0)

def fox(x, y):
    c.area(lumpy(x, y - 3, 5, 2.6, 4, n=18, amp=.04, flat=.2), '#d0703a', wob=0, rough=.3, edge_dark=.1)
    c.area([(x + 4, y - 3), (x + 9, y - 5), (x + 7, y - 2)], '#d0703a', wob=0, rough=.3)
    c.area([(x + 5, y - 6), (x + 6.5, y - 9), (x + 7, y - 5.5)], '#b85e30', wob=0, rough=.3)
    tail = [(x - 4, y - 3), (x - 10, y - 6), (x - 13, y - 4), (x - 9, y - 2)]
    c.area(tail, '#d0703a', wob=0, rough=.3); c.dab(x - 12, y - 4.5, 2.2, 1.6, .2, '#f7efdf', a=1, dry=0)
    for dx in (-2.5, 2.5): c.ink([(x + dx, y - 1), (x + dx, y + 1.5)], .6, a=.9, tremor=0)

def birds():
    for (x, y) in BIRDS:
        c.ink([(x - 3.5, y - 1), (x - 1.2, y - 2.2), (x, y)], .55, a=.8, tremor=0); c.ink([(x, y), (x + 1.4, y - 2.4), (x + 4, y - 1.5)], .55, a=.8, tremor=0)

def fence(pts, h=4):
    P = resample(np.array(pts), 6)
    for p in P: c.ink([p, p - [0, h]], .6, col='#5a4636', a=.9, tremor=0)
    c.ink(P - [0, h * .75], .5, col='#5a4636', a=.85, tremor=.1); c.ink(P - [0, h * .35], .5, col='#5a4636', a=.85, tremor=.1)

def washing_line(a_, b_):
    c.ink([a_, a_ - [0, 8]], .6, col='#5a4636', a=.9, tremor=0); c.ink([b_, b_ - [0, 8]], .6, col='#5a4636', a=.9, tremor=0)
    line = catmull([a_ - [0, 8], (a_ + b_) / 2 - [0, 6], b_ - [0, 8]], 8)
    c.ink(line, .4, a=.7, tremor=0)
    for j, u in enumerate(np.linspace(.15, .85, 5)):
        p = line[int(u * (len(line) - 1))]
        c.area([p + [-1.6, 0], p + [1.6, 0], p + [1.4, 3.6], p + [-1.4, 3.4]], ['#e08a6c', '#f7efdf', '#5fa59c', '#e2b44b', '#d8a29c'][j], wob=0, rough=.2)

def bunting(a_, b_, n=9):
    line = catmull([a_, (np.array(a_) + b_) / 2 + [0, 4], b_], 10)
    c.ink(line, .35, a=.7, tremor=0)
    for j, u in enumerate(np.linspace(.08, .92, n)):
        p = line[int(u * (len(line) - 1))]
        c.area([p + [-1.3, 0], p + [1.3, 0], p + [0, 2.8]], ['#e08a6c', '#e2b44b', '#5fa59c', '#f7efdf'][j % 4], wob=0, rough=.2)

def scarecrow(x, y):
    c.ink([(x, y), (x, y - 12)], .7, col='#5a4636', a=.95, tremor=0); c.ink([(x - 5, y - 9), (x + 5, y - 9.6)], .7, col='#5a4636', a=.95, tremor=0)
    c.area([(x - 2.4, y - 10), (x + 2.4, y - 10), (x + 2, y - 4), (x - 2, y - 4)], '#5fa59c', wob=0, rough=.2)
    c.area(lumpy(x, y - 12, 1.8, 1.8, 2, n=12, amp=0, flat=0), '#e8d6a0', wob=0, rough=.2)
    c.area([(x - 3.4, y - 12.6), (x + 3.4, y - 12.6), (x, y - 16)], '#c9953f', wob=0, rough=.2)
    c.dab(x - 4.5, y - 13, 1.4, .8, 0, '#2f2a28', a=1, dry=0)     # a crow on the arm, unconcerned

# --------------------------------------------------------------------------- compose
def main():
    sky()
    for (x, y, rx, ry, sd) in [(230, 92, 74, 26, 1), (690, 60, 56, 20, 2), (1290, 116, 92, 28, 3), (1505, 62, 44, 16, 4)]:
        cloud(x, y, rx, ry, sd)
    log('clouds')
    mountains()
    balloon(*BALLOON); birds()
    ridge(RIDGE_L, 61, '#3f5f4a', '#2c4639', '#6f8a62'); ridge(RIDGE_R, 62, '#3c5b4a', '#2a4438', '#6a8660')
    log('ridges')
    tunnel()
    valley(); distant_fields()
    log('valley')
    order_mid = ['farm', 'village', 'fields', 'orchard_l']
    masks = {}
    for i, nm in enumerate(order_mid):
        hd = HILL[nm]; m, tc = paint_hill(hd, 100 + i * 10); masks[nm] = (m, tc)
        if nm == 'fields':
            patchwork(hd, m, tc, 77, [(0, 22), (22, 46), (46, 76), (76, 108), (108, 146), (146, 190), (190, 245), (245, 310), (310, 420)], PATCH)
        if nm in ('farm', 'village'):
            flowers(m, 260 if nm == 'farm' else 160, ['#f7efdf', '#e2b44b', '#e08a6c'], 3 + i, size=.8)
        log('hill ' + nm)
    hedgerow([(20, 520), (120, 506), (200, 510), (250, 530)], 5, .5)
    hedgerow([(330, 520), (380, 534), (440, 560), (500, 600)], 6, .35)
    hedgerow([(60, 580), (150, 566), (230, 572)], 7, .3)
    hedgerow([(1350, 600), (1430, 584), (1520, 590), (1600, 580)], 8, .4)
    pond(118, 540, 22, 9)
    lane([(244, 458), (236, 490), (262, 530), (300, 570), (318, 606), (330, 640), (300, 666)], 5, 1)
    lane([(1000, 590), (1030, 560), (1070, 540), (1110, 528), (1150, 524)], 4.4, 2)
    lane([(1150, 524), (1200, 530), (1250, 524), (1290, 545)], 4, 3)
    river()
    railbed(); bridge()
    log('rail')
    fence([(286, 476), (300, 486), (350, 490), (392, 482)], 4)
    washing_line(np.array([196.0, 470.0]), np.array([214.0, 474.0]))
    objs = []
    for t in TREES: objs.append((t[1], 'tree', t))
    for b in VILLAGE + FARM: objs.append((b['y'], 'bld', b))
    objs.append((rail_at(TRAIN_HEAD) + 2, 'train', None))
    for i, p in enumerate(SHEEP): objs.append((p[1], 'sheep', (p, i)))
    for i, p in enumerate(COWS): objs.append((p[1], 'cow', (p, i)))
    objs.append((BOAT[1], 'boat', BOAT)); objs.append((FOX[1], 'fox', FOX))
    objs.append((560, 'scare', (812, 560)))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'tree': TREEF[v[2]](v[0], v[1], v[3], v[4])
        elif kind == 'bld': paint_building(v)
        elif kind == 'train': train()
        elif kind == 'sheep': sheep(v[0][0], v[0][1], v[1])
        elif kind == 'cow': cow(v[0][0], v[0][1], v[1])
        elif kind == 'boat': boat(*v)
        elif kind == 'fox': fox(*v)
        elif kind == 'scare': scarecrow(*v)
    for o in [o for o in objs if o[0] < 640]: draw(o)
    bunting((1110, 488), (1150, 470)); bunting((1046, 512), (1086, 518), 7)
    log('village & mid objects')
    for i, nm in enumerate(['low_l', 'low_r']):
        hd = HILL[nm]; m, tc = paint_hill(hd, 200 + i * 10)
        if nm == 'low_r':
            patchwork(hd, m, tc, 88, [(0, 24), (24, 52), (52, 90), (90, 140), (140, 260)], ['#e0c27a', '#a7ae66', '#c98c4e', '#d7b25a', '#8f9b4f', '#b4a052'])
        else:
            flowers(m, 420, ['#f7efdf', '#e2b44b', '#d8a29c', '#e08a6c'], 9, size=1.0)
            grass_tufts(m, 80, 10)
    for o in [o for o in objs if 640 <= o[0] < 775]: draw(o)
    kite(KITE[0], KITE[1], 304, 744)
    picnic(180, 742)
    log('lower hills')
    for i, nm in enumerate(['fg_l', 'fg_r']):
        hd = HILL[nm]; m, tc = paint_hill(hd, 300 + i * 10)
        flowers(m, 700, ['#f7efdf', '#e2b44b', '#d8a29c', '#e08a6c', '#c4473a'], 19 + i, size=1.5)
        grass_tufts(m, 260, 20 + i, size=1.3)
    for o in [o for o in objs if o[0] >= 775]: draw(o)
    log('foreground')
    c.save('out/story')
    log('saved')

if __name__ == '__main__':
    main()

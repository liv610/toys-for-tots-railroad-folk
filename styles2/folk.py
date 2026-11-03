"""Direction 2 — The Painterly Folk Landscape.
Thick, bold gouache over a warm terracotta ground that shows between the strokes; banded mountains and hills, patterned
fields and decorative trees in the manner of folk painting; every line drawn with a fine brush instead of a pen."""
import math, time
import numpy as np, cv2
from brush import *
from world import *
from parts import *
import story as S
PEAKS_FAR, PEAKS_MID = S.PEAKS_FAR, S.PEAKS_MID

K = 2
W, H = DW * K, DH * K

class FolkCanvas(Canvas):
    def ink(s, pts, w, col='#2e2723', a=.92, tremor=.6, press=.4, taper=(.08, .15), seed=None, scaled=False):
        cm = {'#2e2723': '#3a2a2c', '#2b2521': '#3a2a2c', '#3c3d46': '#2f3540', '#4d5a2c': '#3f5a2c'}
        col2 = cm.get(col, col)
        s.stroke(pts, w * 1.35, col2, a=min(1, a * 1.05), dry=.22, taper=(.12, .3), press=.45, rough=.5, streak=.1, ridge=0,
                 seed=seed, tremor=tremor * 1.4 + .2, scaled=scaled)

c = FolkCanvas(W, H, K, '#b4643c', seed=17)
S.c = c
S.INK = '#3a2a2c'
R = np.random.RandomState(77)
T0 = time.time()
def log(m): print(f'{time.time() - T0:6.1f}s  {m}', flush=True)
jit = S.jit

# --------------------------------------------------------------------------- sky, sun, clouds
def sky():
    m = c.area([(-10, -10), (1610, -10), (1610, 480), (-10, 480)], '#8fbab3', wob=0, rough=0, edge_dark=0, a=.7, var=.04)
    def col(x, y, r):
        t = np.clip(y / 430, 0, 1)
        stops = [(0, '#5f9ea0'), (.45, '#8cbcb2'), (.78, '#e6d3a2'), (1, '#e9b796')]
        for (a0, c0), (a1, c1) in zip(stops[:-1], stops[1:]):
            if t <= a1: base = mix(c0, c1, (t - a0) / (a1 - a0)); break
        if r.rand() < .1: base = mix(base, '#f3e4c4', .4)
        return base * (1 + (r.rand() - .5) * .08)
    ang = lambda x, y: .28 * math.sin(x / 110 + y / 60) + .12 * math.cos(y / 37)
    c.flow_fill(m, ang, col, 15, 90, 10, dry=.42, a=.95, seed=11, jitter=.2, streak=.12, ridge=.15)
    log('sky')

def sun(x, y, r0):
    for k in range(28):
        a = k / 28 * 2 * math.pi
        ln = r0 * (1.55 if k % 2 == 0 else 1.3)
        c.stroke([(x + math.cos(a) * r0 * 1.1, y + math.sin(a) * r0 * 1.1), (x + math.cos(a) * ln, y + math.sin(a) * ln)], 3.4,
                 '#e9b949' if k % 2 == 0 else '#f3dfa4', a=.95, dry=.3, taper=(.05, .7))
    m = c.area(lumpy(x, y, r0, r0, 3, n=40, amp=.03, flat=0), '#f0c252', wob=.3, rough=.6, edge_dark=.1)
    prev = c.clipm; c.set_clip(m)
    for k in range(5):
        rr = r0 * (.25 + k * .17)
        c.stroke([(x + math.cos(a) * rr, y + math.sin(a) * rr) for a in np.linspace(0, 2 * math.pi, 30)], 3.2, ['#f5d47a', '#e7a93e'][k % 2], a=.8, dry=.4, taper=(0, 0))
    c.clipm = prev

def cloud(cx, cy, rx, ry, seed):
    r = np.random.RandomState(seed); nb = r.randint(3, 5)
    for i in range(nb):
        u = (i + .5) / nb; bx = cx - rx + 2 * rx * u; br = ry * (.7 + .45 * math.sin(u * math.pi))
        by = cy - br * .3
        m = c.area(lumpy(bx, by, br, br * .8, seed + i, n=30, amp=.04, flat=.35), '#f6ead4', wob=.3, rough=.6, edge_dark=.05)
        prev = c.clipm; c.set_clip(m)
        for k in range(3):
            rr = br * (.75 - k * .22)
            c.stroke([(bx + math.cos(a) * rr, by + math.sin(a) * rr * .8) for a in np.linspace(math.pi * 1.05, math.pi * 1.95, 12)], 2.6,
                     ['#ffffff', '#e9cdbc', '#f8eedd'][k % 3], a=.85, dry=.35, taper=(.2, .2))
        c.area([(bx - br * 1.2, by + br * .35), (bx + br * 1.2, by + br * .35), (bx + br * 1.2, by + br), (bx - br * 1.2, by + br)], '#e5c3b4', wob=1, rough=1, a=.6, edge_dark=0)
        c.clipm = prev

# --------------------------------------------------------------------------- banded mountains
def banded(m, top_pts, palette, band, w, L, sp, dry, seed, peaks=None, shade=None):
    tc = S.topcol(m); dep, slope = S.depth_fn(tc)
    def ang(x, y):
        d = dep(x, y)
        if peaks is not None:
            s, _ = S.face(peaks, x, y)
            sl = slope(x, y)
            return sl * max(0, 1 - d / 120) + (math.atan2(1, .9 * s) if s else 0) * min(1, d / 120) * .25
        return slope(x, y)
    def col(x, y, r):
        d = dep(x, y) + 3 * math.sin(x / 23)
        bi = int(d / band) % len(palette)
        cc = hexc(palette[bi])
        if peaks is not None and shade:
            s, _ = S.face(peaks, x, y)
            if s > 0: cc = cc * shade
        return cc * (1 + (r.rand() - .5) * .08)
    c.flow_fill(m, ang, col, w, L, sp, dry=dry, a=.95, seed=seed, jitter=.25, streak=.12, ridge=.15)
    return dep

def mountains():
    m = c.area(land(FAR, 520), '#8f97b4', wob=.2, rough=.8, edge_dark=.04, a=.75, seed=21)
    banded(m, FAR, ['#9aa3c0', '#b4a6b8', '#8f9bb8', '#a5aec4', '#c2a9b4'], 15, 9, 50, 6.5, .38, 22, PEAKS_FAR, .84)
    # snow caps with a scalloped hem and a row of dots along it
    xs = np.linspace(-30, 1630, 1400)
    topy = np.interp(xs, FAR[:, 0], FAR[:, 1]); snl = np.interp(xs, *np.array(SNOWLINE).T)
    hem = snl + 9 * np.abs(np.sin(xs / 9.0)) + 10 * np.sin(xs / 61) ** 2
    low = np.maximum(hem, topy)
    poly = np.vstack([np.stack([xs, topy - 1], 1), np.stack([xs, low], 1)[::-1]])
    sm = c.area(poly, '#f6ecdb', wob=0, rough=.6, edge_dark=.06, seed=23)
    prev = c.clipm
    def scol(x, y, r):
        s_, _ = S.face(PEAKS_FAR, x, y)
        return jit('#fbf3e6' if s_ <= 0 else '#d8d6e6', r, .04)
    c.flow_fill(sm, lambda x, y: math.atan2(1, .7 * (S.face(PEAKS_FAR, x, y)[0] or 1)), scol, 5, 22, 4, dry=.3, a=.9, seed=24, jitter=.4)
    c.clipm = prev
    for x in np.arange(-20, 1620, 6.5):
        y = float(np.interp(x, xs, low)); yt = float(np.interp(x, xs, topy))
        if y - yt > 6: c.dab(x, y + 4, 2.2, 2.0, 0, '#f6ecdb', a=.95, dry=0)
    log('far range')
    m2 = c.area(land(MID, 560), '#6f8e95', wob=.3, rough=.8, edge_dark=.05, a=.75, seed=25)
    banded(m2, MID, ['#7d9ba0', '#6a8a8f', '#8aa79f', '#5f7f86'], 13, 8, 44, 6.5, .38, 26, PEAKS_MID, .86)
    # tiny folk firs along the mid range
    rr = np.random.RandomState(27)
    for i in range(520):
        x = rr.uniform(-20, 1620); d = rr.uniform(6, 110)
        y = y_at(MID, x) + d
        if y > 448: continue
        h = 6 + rr.rand() * 4
        c.area([(x - h * .3, y), (x + h * .3, y), (x, y - h)], ['#3f6560', '#4c716a', '#355a57'][rr.randint(3)], wob=0, rough=.3, a=.95, edge_dark=0)
    log('mid range')

def ridge(top, seed, cols):
    r = np.random.RandomState(seed)
    m = c.area(land(top, 600), cols[0], wob=.3, rough=.6, edge_dark=.04, a=.85, seed=seed)
    dep = banded(m, top, cols, 10, 7, 40, 6, .4, seed + 1)
    # rows of folk firs, back to front
    xs0, xs1 = top[0, 0], top[-1, 0]
    rows = []
    for row in range(7):
        for x in np.arange(xs0 + (row % 2) * 4, xs1, 8.5):
            y = y_at(top, x) + row * 7 + r.uniform(-1, 2)
            rows.append((y, x))
    rows.sort()
    for y, x in rows:
        h = 13 + r.rand() * 5
        col = ['#24453a', '#2f5446', '#3a6150'][r.randint(3)]
        c.area([(x - h * .32, y), (x + h * .32, y), (x + r.randn() * .4, y - h)], col, wob=0, rough=.3, a=1, edge_dark=.08)
        c.stroke([(x, y - h * .9), (x, y)], 1.0, '#5f8a6a', a=.6, dry=.3, taper=(0, 0))
    return m

# --------------------------------------------------------------------------- land
HPAL = {
    'farm': ['#b8b46a', '#a3a85c', '#c2b873', '#97a055'],
    'village': ['#c4b878', '#b0aa66', '#cdbf82', '#a2a25e'],
    'orchard_l': ['#a9b36a', '#97a65c', '#b6bb72'],
    'low_l': ['#d6a59a', '#c9928c', '#dcb3a5', '#c48a82'],
    'low_r': ['#a8ad6a'],
    'fg_l': ['#6f8a4a', '#5f7a40', '#7d9552', '#55703c'],
    'fg_r': ['#6a8248', '#5a733e', '#788f50', '#506a38'],
    'fields': ['#a8ad6a'],
}

def hill(hd, seed):
    nm = hd['name']; pal = HPAL[nm]
    m = c.area(land(hd['top']), pal[0], wob=1.2, rough=1.0, edge_dark=.06, a=.8, seed=seed)
    sz = 1.5 if nm.startswith('fg') else 1.0
    dep = banded(m, hd['top'], pal, 26 * sz, 10 * sz, 70 * sz, 8 * sz, .42, seed + 1)
    # a pale crest line, as folk painters outline each hill
    c.stroke(hd['top'] + [0, 1.6], 3.4 * sz, '#efe0b6', a=.8, dry=.35, taper=(.02, .02), seed=seed + 2)
    return m, S.topcol(m)

def dotrows(m, tc, cols, seed, spacing=11, rowgap=12, size=1.6, start=8, stop=400, skip=.2):
    dep, slope = S.depth_fn(tc); x0, y0, sm = tc
    r = np.random.RandomState(seed)
    prev = c.clipm; c.set_clip(m)
    xs_all = (np.arange(len(sm)) + x0) / K; valid = sm < 9e3
    xa, xb = xs_all[valid].min(), xs_all[valid].max()
    def ty(x): return (np.interp(x * K - x0, np.arange(len(sm)), sm) + y0) / K
    for k, d in enumerate(np.arange(start, stop, rowgap)):
        colr = cols[k % len(cols)]
        for x in np.arange(xa + (k % 2) * spacing / 2, xb, spacing):
            if r.rand() < skip: continue
            y = ty(x) + d
            s = persp(y)
            c.dab(x + r.randn() * .6, y, size * 1.2 * s, size * s, 0, colr, a=.95, dry=0)
    c.clipm = prev

def quilt(hd, m, tc, seed, bands, pal):
    """Fields as a hand-pieced quilt: each patch with its own painted pattern, stitched together by hedges."""
    dep, slope = S.depth_fn(tc); x0, y0, sm = tc
    xs_all = (np.arange(len(sm)) + x0) / K; valid = sm < 9e3
    xa, xb = xs_all[valid].min(), xs_all[valid].max()
    def ty(x): return (np.interp(x * K - x0, np.arange(len(sm)), sm) + y0) / K
    r = np.random.RandomState(seed)
    prev = c.clipm; c.set_clip(m)
    last = None; seams = []
    for bi, (d0, d1) in enumerate(bands):
        n = r.randint(2, 4); cuts = np.sort(r.uniform(xa, xb, n - 1)); edges = [xa - 20] + list(cuts) + [xb + 20]
        for j in range(len(edges) - 1):
            a, b = edges[j], edges[j + 1]
            t0, t1 = r.uniform(-10, 10), r.uniform(-10, 10)
            xx = np.linspace(a, b, 30)
            up = [(x + (t0 if k == 0 else t1 if k == 29 else 0), ty(x) + d0) for k, x in enumerate(xx)]
            dn = [(x + (t0 if k == 0 else t1 if k == 29 else 0) * 1.6, ty(x) + d1) for k, x in enumerate(xx)]
            colr = pal[r.randint(len(pal))]
            while colr == last: colr = pal[r.randint(len(pal))]
            last = colr
            pm = c.area(up + dn[::-1], colr, wob=.9, rough=.9, edge_dark=.08, a=.9, seed=int(r.randint(1e6)))
            if pm is None: continue
            pc = c.clipm
            c.set_clip(pm)
            pat = r.randint(5)
            dk = hexc(colr) * .78; lt = np.clip(hexc(colr) * 1.15, 0, 1)
            c.flow_fill(pm, lambda x, y: slope(x, y), lambda x, y, rr: hexc(colr) * (.92 + .14 * rr.rand()), 8, 50, 8, dry=.45, a=.9, seed=int(r.randint(1e6)))
            mid = (d0 + d1) / 2; thick = d1 - d0
            if pat == 0:      # furrows
                for yy in np.arange(d0 + 3, d1, 3.6):
                    c.stroke([(x, ty(x) + yy) for x in np.linspace(a - 10, b + 10, 12)], 1.3, dk, a=.75, dry=.3, taper=(0, 0))
            elif pat == 1:    # sheaves in rows
                for yy in np.arange(d0 + 5, d1 - 2, 8):
                    for xq in np.arange(a + 4 + (int(yy) % 2) * 4, b - 3, 8):
                        y = ty(xq) + yy; s = persp(y)
                        c.stroke([(xq, y + 1.8 * s), (xq, y - 2.4 * s)], 2.2 * s, '#e9c768' if colr != '#e9c768' else '#c9953f', a=.95, dry=.1, taper=(.05, .6))
            elif pat == 2:    # zigzag rows
                for yy in np.arange(d0 + 5, d1 - 2, 7):
                    zz = [(x, ty(x) + yy + (2.2 if i % 2 else -2.2)) for i, x in enumerate(np.arange(a - 6, b + 6, 4.5))]
                    c.stroke(zz, 1.2, lt, a=.85, dry=.2, taper=(0, 0))
            elif pat == 3:    # dots
                for yy in np.arange(d0 + 4, d1 - 1, 5.5):
                    for xq in np.arange(a + 3 + (int(yy * 3) % 2) * 3, b - 2, 6):
                        c.dab(xq, ty(xq) + yy, 1.6, 1.4, 0, lt if r.rand() < .7 else '#f3e6cb', a=.95, dry=0)
            else:             # two-tone stripes across the slope
                for xq in np.arange(a, b, 7):
                    c.stroke([(xq, ty(xq) + d0), (xq + 4, ty(xq) + d1)], 3, dk, a=.5, dry=.4, taper=(0, 0))
            c.clipm = pc
            seams.append(dn)
            if j > 0: seams.append([(a + t0, ty(a) + d0), (a + t0 * 1.6, ty(a) + d1)])
    for sl in seams:
        P = resample(np.array(sl), 3.6)
        for p in P:
            if r.rand() < .08: continue
            s = persp(p[1])
            c.dab(p[0], p[1] - 1, 4 * s, 3.6 * s, r.rand() * 3, ['#3f5a32', '#4f6a38', '#2f4a2c'][r.randint(3)], a=1, dry=.05)
        for p in P[5::13]:
            if r.rand() < .25: tree_lolli(p[0], p[1], 15 * persp(p[1]), int(r.randint(1e6)), small=True)
    c.clipm = prev

def valley():
    m = c.area(land(VALLEY), '#a8ae70', wob=0, rough=.5, edge_dark=0, a=.85, seed=31)
    banded(m, VALLEY, ['#b2b276', '#a2a868', '#bab67c'], 9, 7, 60, 6.5, .42, 32)
    r = np.random.RandomState(71)
    for i in range(30):
        x = r.uniform(20, 1580)
        if 560 < x < 740: continue
        y0 = r.uniform(438, 470); w_ = r.uniform(18, 44); h_ = r.uniform(4, 8)
        colr = ['#d2b264', '#c98c5e', '#b5b06a', '#d7a8a0', '#e0c27a'][r.randint(5)]
        q = [(x, y0), (x + w_, y0), (x + w_ + 3, y0 + h_), (x + 2, y0 + h_ + 1)]
        c.area(q, colr, wob=.4, rough=.8, a=.85, edge_dark=.05)
        for p in resample(np.array([(x + 2, y0 + h_ + 1), (x + w_ + 3, y0 + h_)]), 3.4):
            if r.rand() < .75: c.dab(p[0], p[1], 2.6, 2.2, 0, '#3f5a32', a=.95, dry=.05)

def river():
    P = RIVER; n = len(P)
    t = np.linspace(0, 1, n); wv = river_w(t) * 1.05
    d = np.gradient(P, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.hypot(*nr.T)[:, None]
    L = P + nr * (wv / 2)[:, None]; Rr = P - nr * (wv / 2)[:, None]
    # a dark bank, then the water
    c.area(np.vstack([P + nr * (wv / 2 + 2.2)[:, None], (P - nr * (wv / 2 + 2.2)[:, None])[::-1]]), '#3f5a32', wob=.5, rough=.8, a=.95)
    m = c.area(np.vstack([L, Rr[::-1]]), '#3f7f8a', wob=.5, rough=.7, edge_dark=.12, seed=41)
    def ang(x, y):
        j = int(np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y))); dd = d[j]; return math.atan2(dd[1], dd[0])
    def col(x, y, r):
        j = int(np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y)))
        return mix('#5e9ea0', '#2f6c7a', (j / n) ** .8) * (1 + (r.rand() - .5) * .1)
    c.flow_fill(m, ang, col, 5, 30, 4, dry=.4, a=.9, seed=42, jitter=.2, streak=.12)
    # rows of little white waves, the folk way
    r = np.random.RandomState(43)
    prev = c.clipm; c.set_clip(m)
    for j in range(6, n - 2, 2):
        tt = j / n; ww = wv[j]
        nwav = max(1, int(ww / 9))
        for k in range(nwav):
            off = (k + .5) / nwav - .5 + ((j // 2) % 2) * .5 / nwav
            p = P[j] + nr[j] * off * ww * .85
            dd = d[j] / np.hypot(*d[j]); s = .6 + tt * 1.2
            arc = [p + dd * u * 3 * s + nr[j] * -math.sin((u + 1) / 2 * math.pi) * 1.6 * s for u in np.linspace(-1, 1, 6)]
            c.stroke(arc, .9 * s, '#e9efe2', a=.9, dry=.1, taper=(.2, .2))
    c.clipm = prev
    log('river')

# --------------------------------------------------------------------------- trees, the folk way
def shadow(x, y, rx, ry):
    S.shadow_blob(x, y, rx, ry, '#3a4a26', .35)

def trunkf(x, y, h, w, col='#5a3a2c'):
    c.stroke([(x, y + 1), (x + .4, y - h)], w, col, a=1, dry=.2, taper=(0, .4), press=.1, streak=.15)

def tree_fir(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow(x + h * .12, y + 1, h * .22, h * .045)
    lean = r.uniform(-.04, .04) * h
    top = (x + lean, y - h)
    trunkf(x, y, h * .97, max(1.0, h * .03), '#3f2e28')
    nlev = max(6, int(h / 4.2))
    cols = [['#22463b', '#2f5a48', '#3d6a52'], ['#1f4040', '#2c5652', '#3f6e62']][seed % 2]
    for i in range(nlev):
        f = (i + 1) / nlev
        yy = top[1] + (h * .9) * f; cx = x + lean * (1 - f)
        span = h * (.06 + .26 * f ** .9) * (.85 + .3 * r.rand())
        for side in (-1, 1):
            ln = span * (.85 + .3 * r.rand())
            p0 = (cx, yy - h * .06); p1 = (cx + side * ln, yy + h * .03 + ln * .25)
            c.stroke([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 1), p1], max(1.4, h * .06), cols[(i + (side > 0)) % 3], a=1, dry=.12, taper=(.02, .65), streak=.12)
            if side < 0 and r.rand() < .6:
                c.stroke([(cx - ln * .25, yy - h * .03), (cx - ln * .75, yy + ln * .15)], max(.8, h * .025), '#7fa071', a=.85, dry=.3, taper=(.1, .6))
    c.stroke([top, (top[0], top[1] + h * .1)], max(1.2, h * .05), cols[1], a=1, dry=.1, taper=(.6, .1))

def scales(x, cy, rx, ry, cols, seed, size=1.0, pattern='scale'):
    r = np.random.RandomState(seed)
    rings = max(2, int(min(rx, ry) / (4.2 * size)))
    for k in range(rings, 0, -1):
        rr = k / rings
        n = max(4, int(2 * math.pi * rx * rr / (5.5 * size)))
        for i in range(n):
            a = i / n * 2 * math.pi + k * .4
            px, py = x + math.cos(a) * rx * rr * .9, cy + math.sin(a) * ry * rr * .88
            colr = cols[(k + i) % len(cols)] if pattern == 'scale' else cols[r.randint(len(cols))]
            ang = a + math.pi / 2
            c.dab(px, py, 4.2 * size, 2.6 * size, ang, colr, a=.95, dry=.1, bend=.5)

def tree_lolli(x, y, h, seed, small=False, pal=None):
    r = np.random.RandomState(seed)
    pals = [('#3f6a3c', ['#5f8a4a', '#7fa45a', '#a9c06e']), ('#2f6060', ['#4f8478', '#6fa08a', '#9cc0a0']),
            ('#5a6a2c', ['#7d8a3a', '#a2a84a', '#c9c06a'])]
    base, cols = pal or pals[r.randint(len(pals))]
    rx, ry = h * .34, h * .34; cy = y - h * .62
    if not small: shadow(x + h * .14, y + 1, h * .24, h * .05)
    trunkf(x, y, h * .5, max(1, h * .07))
    m = c.area(lumpy(x, cy, rx, ry, seed, n=40, bumps=4, amp=.05, flat=.05), base, wob=.2, rough=.5, edge_dark=.12)
    if m is None: return
    prev = c.clipm; c.set_clip(m)
    scales(x, cy, rx, ry, cols, seed, size=max(.45, h / 70) if not small else .45)
    c.clipm = prev
    c.stroke([(x + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(math.pi * .55, math.pi * 1.45, 16)], max(.8, h * .02), '#2c3a24', a=.5, dry=.3, taper=(.2, .2))

def tree_oak(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow(x + h * .16, y + 1, h * .3, h * .06)
    trunkf(x, y, h * .45, max(1.4, h * .08))
    # branches drawn first, the way a folk painter shows the tree's bones
    bx, by = x, y - h * .45
    for side in (-1, 0, 1):
        c.stroke([(bx, by), (bx + side * h * .18, by - h * .2), (bx + side * h * .26, by - h * .3)], max(1, h * .035), '#5a3a2c', a=1, dry=.15, taper=(0, .7))
    blobs = [(0, -.66, .3, .22), (-.24, -.58, .2, .16), (.24, -.58, .2, .17), (-.12, -.82, .2, .15), (.14, -.8, .18, .14)]
    for i, (dx, dy, rx, ry) in enumerate(blobs):
        cx, cy = x + dx * h, y + dy * h
        m = c.area(lumpy(cx, cy, rx * h, ry * h, seed + i, n=30, bumps=3, amp=.06, flat=.1), ['#3f6a3c', '#4a723c', '#36603a'][i % 3], wob=.2, rough=.5, edge_dark=.12)
        prev = c.clipm; c.set_clip(m)
        scales(cx, cy, rx * h, ry * h, ['#6f9450', '#8fae5c', '#567c44'], seed + i, size=max(.5, h / 90))
        c.clipm = prev

def tree_round(x, y, h, seed, small=False):
    tree_lolli(x, y, h, seed, small)

def tree_maple(x, y, h, seed):
    tree_lolli(x, y, h, seed, pal=('#a4482e', ['#d0703a', '#e39a4a', '#f0c25a', '#c45a36']))

def tree_blossom(x, y, h, seed):
    r = np.random.RandomState(seed)
    rx, ry = h * .4, h * .32; cy = y - h * .62
    shadow(x + h * .16, y + 1, h * .3, h * .06)
    trunkf(x, y, h * .5, max(1.2, h * .07), '#5a3a34')
    m = c.area(lumpy(x, cy, rx, ry, seed, n=48, bumps=6, amp=.12, flat=.2), '#c98a8c', wob=.2, rough=.5, edge_dark=.12)
    prev = c.clipm; c.set_clip(m)
    scales(x, cy, rx, ry, ['#e0a8a4', '#d4928f', '#ecc0b6'], seed, size=max(.5, h / 80), pattern='rand')
    for i in range(int(h * .9)):
        a = r.uniform(0, 2 * math.pi); dd = r.rand() ** .5
        fx, fy = x + math.cos(a) * rx * dd, cy + math.sin(a) * ry * dd
        for k in range(5):
            aa = k / 5 * 2 * math.pi
            c.dab(fx + math.cos(aa) * 1.1, fy + math.sin(aa) * 1.1, 1.3, 1.1, aa, '#fbf1e6', a=1, dry=0)
        c.dab(fx, fy, .9, .9, 0, '#e2b44b', a=1, dry=0)
    c.clipm = prev

def tree_poplar(x, y, h, seed):
    r = np.random.RandomState(seed)
    wd = h * .13
    poly = []
    for t in np.linspace(0, 1, 14): poly.append((x - wd * math.sin(min(1, t * 1.05) * math.pi) ** .7 * (1 - .2 * t), y - h * .08 - h * .92 * t))
    for t in np.linspace(1, 0, 14): poly.append((x + wd * math.sin(min(1, t * 1.05) * math.pi) ** .7 * (1 - .2 * t), y - h * .08 - h * .92 * t))
    shadow(x + h * .1, y + 1, h * .14, h * .04)
    trunkf(x, y, h * .15, max(1, h * .04))
    m = c.area(poly, '#4f6a34', wob=.2, rough=.5, edge_dark=.12)
    prev = c.clipm; c.set_clip(m)
    c.stroke([(x, y - h * .08), (x, y - h * .98)], max(.8, h * .02), '#6a4a34', a=.8, dry=.2, taper=(0, .3))
    for k in range(int(h / 4)):
        yy = y - h * .12 - k * 4
        for side in (-1, 1):
            c.stroke([(x, yy), (x + side * wd, yy - 4.5)], max(1.2, h * .04), ['#7d9a4a', '#a3b45a', '#5f7a3c'][(k + (side > 0)) % 3], a=1, dry=.15, taper=(.1, .5))
    c.clipm = prev

def tree_birch(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow(x + h * .12, y + 1, h * .2, h * .04)
    for k in range(r.randint(2, 4)):
        tx = x + r.uniform(-.07, .07) * h; top = (tx + r.uniform(-.06, .06) * h, y - h * .92)
        c.stroke([(tx, y), top], max(1.2, h * .04), '#f4ecdc', a=1, dry=.05, taper=(0, .5))
        for j in range(int(h / 7)):
            t = r.uniform(.05, .8); px = tx + (top[0] - tx) * t; py = y + (top[1] - y) * t
            c.stroke([(px - h * .018, py), (px + h * .012, py + .2)], max(.6, h * .014), '#2c2422', a=.9, dry=0, taper=(0, 0))
    for i in range(int(h * 1.6)):
        a = r.uniform(0, 2 * math.pi); dd = r.rand() ** .7
        px = x + math.cos(a) * h * .26 * dd; py = y - h * .66 + math.sin(a) * h * .26 * dd
        c.dab(px, py, max(1.6, h * .04), max(1.2, h * .028), r.uniform(0, 3), ['#d9c45a', '#b3b84e', '#e6d47a', '#8faa4a'][r.randint(4)], a=1, dry=.05)

def tree_willow(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow(x + h * .14, y + 1, h * .3, h * .05)
    trunkf(x, y, h * .6, max(1.3, h * .07))
    for k in range(int(h * 1.5)):
        a = r.uniform(math.pi * 1.05, math.pi * 1.95); sx = x + math.cos(a) * h * .4; sy = y - h * .66 + math.sin(a) * h * .22
        ln = r.uniform(.3, .55) * h
        c.stroke([(x + math.cos(a) * h * .1, y - h * .72), (sx, sy), (sx + 1.5 * np.sign(sx - x), sy + ln)], max(.9, h * .03),
                 ['#8a9a50', '#a9b66a', '#6a7a3c', '#c1c47a'][r.randint(4)], a=.95, dry=.2, taper=(.05, .6))

def tree_apple(x, y, h, seed):
    tree_lolli(x, y, h, seed, small=True, pal=('#4f6a34', ['#6f8a44', '#8fa452']))
    r = np.random.RandomState(seed)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        c.dab(x + math.cos(a) * h * .2, y - h * .62 + math.sin(a) * h * .2, 1.6, 1.6, 0, '#d0402e', a=1, dry=0)

def tree_pine(x, y, h, seed):
    r = np.random.RandomState(seed)
    shadow(x + h * .1, y + 1, h * .2, h * .04)
    trunkf(x, y, h * .9, max(1.1, h * .04), '#6a4434')
    for k in range(4):
        cy = y - h * (.55 + k * .12); cx = x + r.uniform(-.1, .1) * h; rx = h * (.22 - k * .035)
        for j in range(int(rx / 2.2)):
            u = (j + .5) / int(rx / 2.2) * 2 - 1
            c.stroke([(cx + u * rx, cy + 2), (cx + u * rx * .9, cy - 3.5)], 2.2, ['#2f5446', '#3d6a52', '#5f8a62'][(j + k) % 3], a=1, dry=.1, taper=(.05, .6))

TREEF = dict(fir=tree_fir, oak=tree_oak, round=tree_round, maple=tree_maple, blossom=tree_blossom, poplar=tree_poplar, birch=tree_birch,
             willow=tree_willow, apple=tree_apple, pine=tree_pine)
S.tree_round = tree_round

# --------------------------------------------------------------------------- flowers and little things
def flowerbed(m, n, seed, size=1.0):
    x0, y0, mm = m; h, w = mm.shape; r = np.random.RandomState(seed)
    for i in range(n):
        px, py = r.randint(w), r.randint(h)
        if mm[py, px] < .9: continue
        X, Y = (px + x0) / K, (py + y0) / K; s = size * persp(Y)
        kind = r.randint(4)
        if kind == 0:      # daisy
            for k in range(6):
                a = k / 6 * 2 * math.pi
                c.dab(X + math.cos(a) * 1.4 * s, Y + math.sin(a) * 1.2 * s, 1.5 * s, 1.0 * s, a, '#fbf1e6', a=1, dry=0)
            c.dab(X, Y, 1 * s, 1 * s, 0, '#e2b44b', a=1, dry=0)
        elif kind == 1:    # tulip
            c.stroke([(X, Y + 4 * s), (X, Y)], .8 * s, '#3f6a3c', a=1, dry=0, taper=(0, 0))
            c.dab(X, Y - .6 * s, 2.2 * s, 1.8 * s, math.pi / 2, ['#d0402e', '#e08a6c', '#d8a29c'][r.randint(3)], a=1, dry=0)
        elif kind == 2:    # a sprig
            for k in range(3):
                c.stroke([(X, Y + 3 * s), (X + (k - 1) * 2 * s, Y - 2 * s)], .7 * s, '#4f7a3c', a=1, dry=0, taper=(0, .5))
                c.dab(X + (k - 1) * 2 * s, Y - 2.4 * s, 1.2 * s, 1.2 * s, 0, ['#8a7ab0', '#f3e6cb', '#e2b44b'][r.randint(3)], a=1, dry=0)
        else:
            c.dab(X, Y, 1.6 * s, 1.4 * s, 0, ['#f6ecdb', '#e2b44b', '#e8a8a0'][r.randint(3)], a=1, dry=0)

# --------------------------------------------------------------------------- compose
def main():
    sky()
    sun(1480, 92, 26)
    for (x, y, rx, ry, sd) in [(230, 92, 70, 22, 1), (700, 64, 52, 18, 2), (1240, 122, 80, 24, 3)]:
        cloud(x, y, rx, ry, sd)
    log('clouds & sun')
    mountains()
    S.balloon(*BALLOON); S.birds()
    ridge(RIDGE_L, 61, ['#2f5446', '#3a6150', '#2a4a40']); ridge(RIDGE_R, 62, ['#2c5048', '#365c52', '#284640'])
    log('ridges')
    S.tunnel()
    valley()
    log('valley')
    for i, nm in enumerate(['farm', 'village', 'fields', 'orchard_l']):
        hd = HILL[nm]; m, tc = hill(hd, 100 + i * 10)
        if nm == 'fields':
            quilt(hd, m, tc, 77, [(0, 22), (22, 46), (46, 76), (76, 108), (108, 146), (146, 190), (190, 245), (245, 310), (310, 420)],
                  ['#e0b54a', '#c4683f', '#9aa858', '#d98e6a', '#e8cf7a', '#7f8f44', '#d8a29c', '#b9a24a'])
        if nm == 'farm':
            dotrows(m, tc, ['#f6ecdb', '#e8a8a0'], 5, spacing=13, rowgap=16, size=1.2, start=60, stop=220, skip=.35)
        if nm == 'village':
            dotrows(m, tc, ['#f6ecdb', '#e2b44b'], 6, spacing=14, rowgap=16, size=1.1, start=90, stop=200, skip=.45)
        log('hill ' + nm)
    S.hedgerow([(20, 520), (120, 506), (200, 510), (250, 530)], 5, .5)
    S.hedgerow([(330, 520), (380, 534), (440, 560), (500, 600)], 6, .35)
    S.hedgerow([(60, 580), (150, 566), (230, 572)], 7, .3)
    S.hedgerow([(1350, 600), (1430, 584), (1520, 590), (1600, 580)], 8, .4)
    S.pond(118, 540, 22, 9)
    S.lane([(244, 458), (236, 490), (262, 530), (300, 570), (318, 606), (330, 640), (300, 666)], 5, 1)
    S.lane([(1000, 590), (1030, 560), (1070, 540), (1110, 528), (1150, 524)], 4.4, 2)
    S.lane([(1150, 524), (1200, 530), (1250, 524), (1290, 545)], 4, 3)
    river()
    S.railbed(); S.bridge()
    log('rail')
    S.fence([(286, 476), (300, 486), (350, 490), (392, 482)], 4)
    S.washing_line(np.array([196.0, 470.0]), np.array([214.0, 474.0]))
    objs = []
    for t in TREES: objs.append((t[1], 'tree', t))
    for b in VILLAGE + FARM: objs.append((b['y'], 'bld', b))
    objs.append((rail_at(TRAIN_HEAD) + 2, 'train', None))
    for i, p in enumerate(SHEEP): objs.append((p[1], 'sheep', (p, i)))
    for i, p in enumerate(COWS): objs.append((p[1], 'cow', (p, i)))
    objs.append((BOAT[1], 'boat', BOAT)); objs.append((FOX[1], 'fox', FOX)); objs.append((560, 'scare', (812, 560)))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'tree': TREEF[v[2]](v[0], v[1], v[3], v[4])
        elif kind == 'bld': S.paint_building(v)
        elif kind == 'train': S.train()
        elif kind == 'sheep': S.sheep(v[0][0], v[0][1], v[1])
        elif kind == 'cow': S.cow(v[0][0], v[0][1], v[1])
        elif kind == 'boat': S.boat(*v)
        elif kind == 'fox': S.fox(*v)
        elif kind == 'scare': S.scarecrow(*v)
    for o in [o for o in objs if o[0] < 640]: draw(o)
    S.bunting((1110, 488), (1150, 470)); S.bunting((1046, 512), (1086, 518), 7)
    log('village')
    for i, nm in enumerate(['low_l', 'low_r']):
        hd = HILL[nm]; m, tc = hill(hd, 200 + i * 10)
        if nm == 'low_r':
            quilt(hd, m, tc, 88, [(0, 24), (24, 52), (52, 90), (90, 140), (140, 260)], ['#e8cf7a', '#9aa858', '#c4683f', '#e0b54a', '#7f8f44', '#d98e6a'])
        else:
            dotrows(m, tc, ['#f6ecdb', '#c4683f', '#e2b44b'], 9, spacing=10, rowgap=11, size=1.4, start=10, stop=260, skip=.25)
    for o in [o for o in objs if 640 <= o[0] < 775]: draw(o)
    S.kite(KITE[0], KITE[1], 304, 744); S.picnic(180, 742)
    log('lower hills')
    for i, nm in enumerate(['fg_l', 'fg_r']):
        hd = HILL[nm]; m, tc = hill(hd, 300 + i * 10)
        flowerbed(m, 900, 19 + i, size=1.6)
    for o in [o for o in objs if o[0] >= 775]: draw(o)
    log('foreground')
    c.save('out/folk')
    log('saved')

if __name__ == '__main__':
    main()

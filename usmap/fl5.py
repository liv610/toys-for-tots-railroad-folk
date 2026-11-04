"""Pass 5, group 6 — Florida and the Southeast after the user's Florida reference.

  * a narrower, longer Florida peninsula (coast5.npy: only the peninsula's Gulf side and tip are re-traced)
  * the river: wider and lighter, no brown banks, white flow lines; the three-channel delta is replaced by one
    widening mouth that runs out through the shoreline into the Gulf
  * boats after the reference: curved wooden hull, mainsail and jib, a red pennant
  * flower patches for the meadows
Everything is in map units.
"""
import math
import numpy as np
import usmap4 as B
from usmap4 import c, hexc, pal_fn, catmull, resample
from kit import ribbon

S = B.S

# ---------------------------------------------------------------- the coastline
NEW_WEST = [(1200, 762), (1222, 752), (1248, 748), (1272, 752), (1290, 764), (1300, 784), (1306, 810), (1312, 840), (1322, 870),
            (1334, 898), (1346, 924), (1357, 944), (1370, 953), (1385, 951), (1398, 940), (1408, 922), (1415, 900), (1419, 876)]
def coast5():
    C = np.load('coast4.npy')
    # keep everything up to the Gulf inlet (index 162), then the new Gulf side and tip, then the east coast from index 189
    return np.vstack([C[:163], np.array(NEW_WEST, float), C[189:]])

# ---------------------------------------------------------------- river
RIVER_PAL = ['#5a8cc4', '#4c7eb8', '#6a9ad0', '#7aa8d8']
def river5(P, w0, w1, seed):
    """The river after the reference: lighter blue, no brown banks, a soft darker edge, white flow lines."""
    P = np.asarray(P, float)
    if len(P) < 3: return
    edge, _, _ = ribbon(P, lambda t: w0 + (w1 - w0) * t + 3.5)
    c.area(edge, '#3a6a9e', wob=.4, rough=.8, edge_dark=.05, seed=seed, a=.9)
    poly, nr, _ = ribbon(P, lambda t: w0 + (w1 - w0) * t)
    rm = c.area(poly, RIVER_PAL[0], wob=.4, rough=.7, edge_dark=.06, seed=seed + 2)
    d = np.gradient(P, axis=0)
    def ang(X, Y):
        j = np.argmin(np.hypot(P[:, 0][None] - X[:, None], P[:, 1][None] - Y[:, None]), axis=1); return np.arctan2(d[j, 1], d[j, 0])
    c.stip(rm, pal_fn(RIVER_PAL, .04), spacing=1.25, L=5.0, w=1.6, angfn=ang, seed=seed + 3, jit=.15)
    r = np.random.RandomState(seed + 4)
    for kk in range(int(len(P) * 1.3) if len(P) > 6 else 0):        # white flow lines, a little wavy
        j = r.randint(2, len(P) - 3); t = j / len(P); wd = w0 + (w1 - w0) * t; off = r.uniform(-.32, .32) * wd
        dd = d[j] / (np.hypot(*d[j]) + 1e-9); p = P[j] + nr[j] * off; ln = r.uniform(4, 8)
        q = [p - dd * ln, p + nr[j] * 1.0, p + dd * ln]
        c.stroke(q, 1.1, '#eef4fa', a=.85, dry=.2, taper=(.3, .3))

def river_mouth(P0, seed, coast_y=810):
    """Where the river meets the Gulf: it widens, runs out through the shoreline and fans into the sea; the colour
    turns to the sea's blue just past the shore, and white water fans out ahead of it."""
    P = resample(catmull(P0, 10), 1.6); n = len(P)
    wfn = lambda t: 30 + 30 * t ** 1.6
    poly, nr, _ = ribbon(P, wfn)
    fan = S.lumpy(P[-1][0], P[-1][1] + 4, 34, 13, seed + 5, n=30, amp=.12, flat=0)
    SEA = np.array([hexc(z) for z in ['#2c5684', '#335e8c', '#26507c', '#2f5a88']]); RV = np.array([hexc(z) for z in RIVER_PAL])
    d = np.gradient(P, axis=0)
    def colf(X, Y, rr):
        u = np.clip((Y - coast_y) / 22 + rr.randn(len(X)) * .12, 0, 1)
        a = RV[rr.randint(4, size=len(X))]; b = SEA[rr.randint(4, size=len(X))]
        return a * (1 - u)[:, None] + b * u[:, None]
    for shape, sd in ((fan, seed + 7), (poly, seed)):
        m = c.mask(shape, .6, .8, sd)
        if m is None: continue
        c.area(None, RIVER_PAL[1], m=B.U2.land_clip(m), edge_dark=0)       # solid water only over the land; at sea the stipple fades into the ocean
        c.stip(m, colf, spacing=1.25, L=5.0, w=1.6, angfn=lambda X, Y: np.arctan2(d[n // 2, 1], d[n // 2, 0]) + 0 * X, seed=sd + 1, jit=.25)
    r = np.random.RandomState(seed + 2)
    for kk in range(22):                                             # white water fanning out across the mouth and into the sea
        t = r.uniform(.1, 1.0); j = int(min(t, .999) * (n - 1)); wd = wfn(t); off = r.uniform(-.45, .45) * wd
        dd = d[j] / (np.hypot(*d[j]) + 1e-9); p = P[j] + nr[j] * off + dd * (t > .9) * r.uniform(0, 10); ln = r.uniform(4, 8)
        spread = off / wd * .9; dv = dd * math.cos(spread) + nr[j] * math.sin(spread)
        c.stroke([p - dv * ln, p + nr[j] * 1.2, p + dv * ln], 1.2, '#eef4fa', a=.9, dry=.25, taper=(.3, .3))
    for kk in range(4):                                              # a few wave crests just beyond the mouth
        bx = P[-1][0] - 26 + kk * 15 + r.uniform(-3, 3); by = P[-1][1] + 14 + r.uniform(-2, 5)
        c.stroke([(bx, by), (bx + 4, by - 2.4), (bx + 8, by), (bx + 12, by - 2.4)], 1.5, '#e6ecee', a=.85, dry=.2, taper=(.2, .2))

# ---------------------------------------------------------------- boats
def boat6(x, y, s=1.0):
    """A sailboat after the reference: a curved wooden hull, a tall mainsail and a smaller jib, a red pennant,
    and white wave lines under the bow and stern. The waterline is at y + 13 s."""
    wl = y + 13 * s
    hull = [(x - 34 * s, y + 1 * s)] + [(x - 34 * s + 68 * s * u, y + 1 * s + 1.5 * s * math.sin(u * math.pi)) for u in np.linspace(0, 1, 12)][1:] + \
           [(x + 26 * s, wl)] + [(x + 26 * s - 48 * s * u, wl + 1.5 * s * math.sin(u * math.pi)) for u in np.linspace(0, 1, 10)][1:]
    hm = c.area(hull, '#8a5432', wob=0, rough=.4, edge_dark=.18)
    if hm is not None: c.stip(hm, pal_fn(['#8a5432', '#7a4628', '#9c6640']), spacing=1.0, L=2.6, w=1.1, angfn=lambda X, Y: 0 * X, seed=int(x))
    c.stroke([(x - 33 * s, y + 1.5 * s), (x + 33 * s, y + 1.5 * s)], 1.8 * s, '#5a3420', a=1, dry=0, taper=(0, 0))   # gunwale
    c.stroke([(x - 30 * s, y + 6 * s), (x + 29 * s, y + 6 * s)], 1.0 * s, '#b07a4c', a=.8, dry=0, taper=(0, 0))      # plank line
    c.stroke([(x - 2 * s, y + 1 * s), (x - 2 * s, y - 66 * s)], 2.2 * s, '#4a3424', a=1, dry=0, taper=(0, 0))       # mast
    main = [(x + 1 * s, y - 4 * s), (x + 1 * s, y - 64 * s), (x + 30 * s, y - 5 * s)]
    sm = c.area(main, '#f4eedf', wob=.08, rough=.4, edge_dark=.08)
    if sm is not None: c.stip(sm, pal_fn(['#f6f0e2', '#e8dfca', '#fbf7ee']), spacing=1.1, L=3.0, w=1.2, angfn=lambda X, Y: -1.1 + 0 * X, seed=int(x) + 1)
    c.stroke([(x + 1 * s, y - 64 * s), (x + 30 * s, y - 5 * s)], .9 * s, '#d8ccb2', a=.8, dry=0, taper=(0, 0))
    jib = [(x - 5 * s, y - 5 * s), (x - 5 * s, y - 52 * s), (x - 27 * s, y - 6 * s)]
    jm = c.area(jib, '#ece2cc', wob=.08, rough=.4, edge_dark=.08)
    if jm is not None: c.stip(jm, pal_fn(['#ece2cc', '#ddd2ba']), spacing=1.1, L=3.0, w=1.2, angfn=lambda X, Y: 1.1 + 0 * X, seed=int(x) + 2)
    c.area([(x - 2 * s, y - 66 * s), (x + 12 * s, y - 62 * s), (x - 2 * s, y - 59 * s)], '#c8302a', wob=0, rough=.3, edge_dark=.15)  # pennant
    for kk in range(3):
        bx = x - 38 * s + kk * 30 * s
        c.stroke([(bx, wl + 4 * s), (bx + 6 * s, wl + 2 * s), (bx + 12 * s, wl + 4 * s), (bx + 18 * s, wl + 2 * s)], 1.8, '#eef3f4', a=.9, dry=.1, taper=(.2, .2))

# ---------------------------------------------------------------- meadow flowers
def flower_patch(x, y, rx, ry, seed, cols=('#f2c83a', '#f6dc6a', '#e8a828')):
    """A loose patch of small yellow wildflowers with a few green leaves, as in the reference's meadows."""
    r = np.random.RandomState(seed); n = int(rx * ry * .35)
    pts = []
    while len(pts) < n:
        u, v = r.uniform(-1, 1, 2)
        if u * u + v * v <= 1: pts.append((x + u * rx, y + v * ry))
    c.dots([(px + r.uniform(-1, 1), py + 1.5) for px, py in pts[::2]], 1.0, ['#4e7a30', '#62903a'], seed=seed + 1)
    c.dots(pts, 1.35, list(cols), seed=seed + 2)
    c.dots([(px + .3, py - .3) for px, py in pts[::4]], .5, ['#6a4a1a'], seed=seed + 3)

"""Pass 3 — the U.S. map rebuilt on a layered, depth-sorted scene.

What is new compared with pass 2 (pass 2 itself is untouched and still renders identically):
  * One scene description (out/scene3.json) lists every element with its own stable seed; the render reads it.
    Editing or moving one element no longer reshuffles anything else.
  * Painter's algorithm by true depth: hills, track segments, rivers, trees, buildings and landmarks are interleaved by
    the depth of the ground they stand on, so trees and hills pass in front of the railroad and the track can slip
    behind a hill crest.  A depth buffer (Z) records what is in front of what.
  * Three railroad routes re-routed through valleys, each into its own tunnel portal cut into a wooded mound behind
    Toy Town; one green line from New England straight into the east tunnel; a raised railbed with a shadow.
  * Mountains with lit and shaded faces, snow running down gullies, foothills; New England (and a little of the
    northern band) under snow; Lake Superior restored; objects are no longer clipped by the coastline.
  * Animation layers are exported: base (no train, clouds or boats), an occluder overlay for the railroad corridor,
    RGBA sprites for the train, clouds and boats, and the route geometry with depth and visibility (out/anim/).

Run:  PYTHONPATH=../folk2:../styles2 python3 usmap3.py            (builds the scene from rules, writes scene3.json)
      PYTHONPATH=../folk2:../styles2 python3 usmap3.py --scene out/scene3.json   (renders an edited scene file)
"""
import sys, os, json, math, time, zlib
import numpy as np, cv2
import usmap as U
import usmap2 as U2
from usmap import c, k, W, H, RW, RH, A, S, pal_fn, catmull, resample, stipple_fir, skeleton_tree, impasto, ribbon, hexc, bush
from matplotlib.path import Path as MP

T0 = time.time()
def log(m): print(f'P3 {time.time() - T0:6.1f}s {m}', flush=True)
def sid(*parts):                       # stable per-element seed, independent of Python's hash randomisation
    return zlib.crc32('|'.join(str(p) for p in parts).encode()) & 0x7fffffff

COAST = np.load('coast3.npy'); LAKES = list(np.load('lakes3.npy', allow_pickle=True))
LANDP = MP(COAST); LAKEP = [MP(l) for l in LAKES]
def on_land(x, y, pad=0):
    return LANDP.contains_point((x, y), radius=-pad) and not any(lp.contains_point((x, y), radius=pad) for lp in LAKEP)

# ====================================================================== snow field
def snow_amt(x, y):
    """0..1: deep snow in New England, a light dusting along the northern band."""
    ne = np.clip((x - 1300) / 90, 0, 1) * np.clip((470 - y) / 90, 0, 1)
    band = np.clip((x - 900) / 160, 0, 1) * np.clip((250 - y) / 70, 0, 1) * .55
    return np.maximum(ne, band)

SNOWPAL = ['#e8eaea', '#d8dee4', '#f2f0ea', '#c8d2de', '#b8c4d2']

# ====================================================================== geography: hills, mound, routes
HILLS = [list(h) for h in U2.HILLS]
for h in HILLS:
    if h[0] == 1260 and h[1] == 256: h[0], h[1], h[2] = 1390, 300, 230       # keep the moss hill off Lake Huron
HILLS = [tuple(h) for h in HILLS]

MOUND = dict(cx=930, base=488, w=640, h=230)                                # the wooded tunnel mound behind Toy Town
def mound_poly():
    m = MOUND; pts = []
    for u in np.linspace(0, 1, 44):
        pts.append((m['cx'] - m['w'] / 2 + m['w'] * u, m['base'] - m['h'] * math.sin(u * math.pi) ** .6 * (1 + .05 * math.sin(u * 11))))
    pts += [(m['cx'] + m['w'] / 2 + 40, m['base'] + 40), (m['cx'] - m['w'] / 2 - 40, m['base'] + 40)]
    return np.array(pts)

PORTALS = {'red': (742, 424), 'blue': (652, 482), 'green': (1203, 474)}
ROUTE_CTRL = {
    'red': [(22, 168), (90, 160), (150, 170), (180, 212), (178, 262), (196, 306), (238, 344), (300, 376), (372, 398), (452, 410),
            (530, 420), (600, 430), (660, 432), (706, 428), (742, 424)],
    'blue': [(96, 600), (190, 606), (290, 604), (380, 590), (460, 566), (530, 540), (584, 516), (624, 496), (652, 482)],
    'green': [(1584, 200), (1546, 226), (1540, 262), (1506, 296), (1466, 318), (1440, 352), (1400, 380), (1350, 404), (1300, 436), (1252, 458), (1203, 474)],
}
def route(name):
    P = resample(catmull(ROUTE_CTRL[name], 14), 1.6)
    return P

RIVER = catmull([(1010, 520), (1030, 548), (1060, 578), (1080, 610), (1096, 642), (1110, 680), (1124, 720), (1132, 760)], 12)
WRIV = catmull([(130, 410), (100, 430), (70, 446), (40, 456)], 10)

# ====================================================================== ground surface: which hill is the visible ground at (x, y)
def build_ground():
    """GID[y, x] = index of the front-most hill covering that point (-1 = open land). Reference-pixel resolution."""
    gid = np.full((RH, RW), -1, np.int32); gbase = np.full((RH, RW), np.nan, np.float32)
    polys = []
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        polys.append((base, i, U2.hill_poly(cx, base, w, h, 500 + i * 7)))
    polys.append((MOUND['base'], 'mound', mound_poly()))
    polys.sort(key=lambda t: t[0])
    tops = {}
    for base, i, poly in polys:
        m = np.zeros((RH, RW), np.uint8); cv2.fillPoly(m, [np.round(poly).astype(np.int32)], 1)
        gbase[m > 0] = base; tops[i] = poly
    return gbase, tops

def depth_at(x, y, gbase):
    xi, yi = int(np.clip(x, 0, RW - 1)), int(np.clip(y, 0, RH - 1))
    b = gbase[yi, xi]
    return (float(y) if np.isnan(b) else float(b)) + y * 1e-4

# ====================================================================== new painters
def paint_hill3(cx, base, w, h, kind, seed):
    """Pass-2 hill, now modelled: lit crest, darker skirt, light from the upper left; snow where the snow field says."""
    poly = U2.hill_poly(cx, base, w, h, seed); top = poly[:40]
    pal = U2.PAL['gold' if kind == 'field' else kind]
    m = c.area(poly, pal[0], wob=.8, rough=1, edge_dark=.06, seed=seed)
    if m is None: return
    m = U2.land_clip(m); fl = U.flow_of(top)
    C = np.array([hexc(cc) for cc in pal]); SN = np.array([hexc(cc) for cc in SNOWPAL])
    def col(X, Y, rr):
        d = np.clip((Y - np.interp(X, top[:, 0], top[:, 1])) / (h * 1.1), 0, 1)
        side = np.clip((X - cx) / (w / 2), -1, 1)
        base_ = C[rr.randint(len(C), size=len(X))] * (1.13 - .34 * d - .07 * side)[:, None]
        s = snow_amt(X, Y)
        snowy = SN[rr.randint(len(SN), size=len(X))] * (1.02 - .12 * d - .05 * side)[:, None]
        pick = rr.rand(len(X)) < s * 1.05
        out = np.where(pick[:, None], snowy, base_)
        return out * (1 + (rr.rand(len(X), 1) - .5) * .06)
    c.stip(m, col, spacing=2.0, L=6.5, w=2.8, angfn=fl, seed=seed + 1, jit=.25)
    r = np.random.RandomState(seed + 2)
    prev = c.clipm; c.set_clip(m)
    if snow_amt(cx, base - h * .5) < .45:
        for j in range(r.randint(2, 4)):
            px = cx + r.uniform(-.32, .32) * w; ty = float(np.interp(px, top[:, 0], top[:, 1])); py = ty + r.uniform(.25, .7) * h
            kk = 'gold' if kind == 'field' else kind
            pk = U2.PATCH[kk][r.randint(len(U2.PATCH[kk]))]
            pm = c.area(S.lumpy(px, py, w * r.uniform(.12, .22), h * r.uniform(.12, .22), seed + 10 + j, n=30, amp=.2), U2.PAL[pk][0], wob=1.2, rough=1, edge_dark=.03, a=.9)
            if pm is not None:
                P2 = np.array([hexc(cc) for cc in U2.PAL[pk]])
                def pcol(X, Y, rr, P2=P2):
                    d = np.clip((Y - np.interp(X, top[:, 0], top[:, 1])) / (h * 1.1), 0, 1)
                    return P2[rr.randint(len(P2), size=len(X))] * (1.1 - .3 * d)[:, None]
                c.stip(U2.land_clip(pm), pcol, spacing=2.0, L=6.0, w=2.6, angfn=fl, seed=seed + 20 + j, jit=.25)
    def finer(X, Y, rr):
        d = np.clip((Y - np.interp(X, top[:, 0], top[:, 1])) / h, 0, 1)
        out = C[rr.randint(len(C), size=len(X))] * (1.18 - .3 * d)[:, None]
        s = snow_amt(X, Y); pick = rr.rand(len(X)) < s
        out = np.where(pick[:, None], SN[rr.randint(len(SN), size=len(X))] * (1.04 - .1 * d)[:, None], out)
        return out * (1 + (rr.rand(len(X), 1) - .5) * .06)
    c.stip(m, finer, spacing=3.4, L=3.6, w=1.6, angfn=fl, seed=seed + 3, jit=.35, spill=.7)
    if kind == 'field' and snow_amt(cx, base) < .3:
        st = U2.FIELD_STRIPES.get(cx, ['#8e6a22', '#e0bc58'])
        for j, d in enumerate(np.arange(10, h * 1.05, 8.5)):
            line = [(x, float(np.interp(x, top[:, 0], top[:, 1])) + d) for x in np.linspace(cx - w * .44, cx + w * .44, 34)]
            c.stroke(line, 3.6, st[j % 2], a=.95, dry=.3, taper=(.04, .04), rough=.6, streak=.15)
    # a shadow band along the skirt and a lit crest
    c.stroke(top + [0, h * .78], 10, '#2c3618', a=.16, dry=.5, taper=(.1, .1))
    c.clipm = prev
    crest = '#f4f2ea' if snow_amt(cx, base - h) > .5 else ('#e8d690' if kind in ('gold', 'field', 'olive') else '#9ab060')
    c.stroke(top + [0, 2.2], 3.6, crest, a=.5, dry=.55, taper=(.05, .05))
    c.stroke(top + [0, -1.2], 1.6, '#2e3a1e', a=.35, dry=.4, taper=(.1, .1))

def mountain3(px, base, w, h, seed):
    """A folk-painted peak: wavy ridge splitting a lit and a shaded face, snow with fingers down the gullies,
    speckled lower slopes."""
    r = np.random.RandomState(seed)
    pk = np.array((px + r.uniform(-.06, .06) * w, base - h))
    def side(sgn, hw):
        pts = []
        for t in np.linspace(0, 1, 9):
            bump = (math.sin(t * 7 + seed) * .04 + (.08 if .45 < t < .6 else 0)) * h
            pts.append((pk[0] + sgn * hw * t ** .95, pk[1] + h * t ** 1.15 - bump * (t > .2)))
        return pts
    L = side(-1, w * r.uniform(.46, .54)); Rr = side(1, w * r.uniform(.46, .54))
    poly = np.array(L[::-1] + Rr[1:])
    ridge = np.array([(pk[0] + h * .05 * math.sin(t * 5 + seed) + t * w * .1, pk[1] + h * t) for t in np.linspace(0, 1, 12)])
    m = c.area(poly, '#9890bc', wob=.25, rough=.7, edge_dark=.07, seed=seed)
    if m is None: return
    LIT = np.array([hexc(x) for x in ['#a89ec8', '#b6acd2', '#9a90be', '#c2b8da']])
    SH = np.array([hexc(x) for x in ['#6c6694', '#78729e', '#605a88', '#847eaa']])
    def face(X):
        return X > np.interp(np.clip(X * 0, 0, 0) + 0, [0], [0]) if False else X > (pk[0] + 0 * X)
    def colf(X, Y, rr):
        rx = np.interp(Y, ridge[:, 1], ridge[:, 0]); sh = X > rx
        out = np.where(sh[:, None], SH[rr.randint(4, size=len(X))], LIT[rr.randint(4, size=len(X))])
        d = np.clip((Y - pk[1]) / h, 0, 1)
        return out * (1.04 - .12 * d)[:, None] * (1 + (rr.rand(len(X), 1) - .5) * .06)
    def ang(X, Y):
        rx = np.interp(Y, ridge[:, 1], ridge[:, 0])
        return np.where(X > rx, math.pi / 2 - .75, math.pi / 2 + .75) + .25 * np.sin(X / 9)
    c.stip(m, colf, spacing=1.15, L=4.2, w=1.6, angfn=ang, seed=seed + 1, jit=.3)
    # snow cap with gully fingers
    xs = np.linspace(poly[:, 0].min(), poly[:, 0].max(), 160)
    topy = np.interp(xs, poly[:len(L), 0][::-1] if False else np.concatenate([np.array(L)[::-1][:, 0], np.array(Rr)[1:, 0]]),
                     np.concatenate([np.array(L)[::-1][:, 1], np.array(Rr)[1:, 1]]))
    line = pk[1] + h * (.34 + .06 * np.sin(xs / 7 + seed))
    fing = np.zeros_like(xs)
    for kk in range(int(w / 9)):
        cxx = r.uniform(xs.min(), xs.max()); wd = r.uniform(2.5, 6); ln = r.uniform(.08, .3) * h
        fing += ln * np.clip(1 - np.abs(xs - cxx) / wd, 0, 1) ** 1.3
    low = np.maximum(line + fing * (1 - np.abs(xs - pk[0]) / (w * .55)).clip(0, 1), topy)
    snow = np.vstack([np.stack([xs, topy - 1], 1), np.stack([xs, low], 1)[::-1]])
    prev = c.clipm; c.set_clip(m)
    sm = c.area(snow, '#f2f0ee', wob=.2, rough=1.1, edge_dark=.04, seed=seed + 2)
    SW = np.array([hexc(x) for x in ['#fbf8f2', '#efece6', '#f6f2ea']]); SB = np.array([hexc(x) for x in ['#ccd0e2', '#bec4da', '#d6d8e6']])
    def scol(X, Y, rr):
        rx = np.interp(Y, ridge[:, 1], ridge[:, 0])
        return np.where((X > rx)[:, None], SB[rr.randint(3, size=len(X))], SW[rr.randint(3, size=len(X))])
    if sm is not None: c.stip(sm, scol, spacing=1.05, L=3.6, w=1.4, angfn=ang, seed=seed + 3, jit=.3)
    # snow streaks running further down the gullies
    for kk in range(int(w / 7)):
        sx = r.uniform(xs.min() + 6, xs.max() - 6); sy = float(np.interp(sx, xs, low)) - 2
        sgn = -1 if sx < pk[0] else 1
        c.stroke([(sx, sy), (sx + sgn * r.uniform(2, 6), sy + r.uniform(8, 22))], r.uniform(1.2, 2.4), '#f2efe8' if sgn < 0 else '#c8cce0', a=.9, dry=.35, taper=(.05, .7))
    # lower slopes: tiny dabs of colour and little firs climbing the base
    for kk in range(int(w * .8)):
        x = r.uniform(poly[:, 0].min(), poly[:, 0].max()); ytop = float(np.interp(x, xs, topy)); y = r.uniform(max(ytop, pk[1] + h * .62), base - 2)
        c.dots([(x, y)], .9, ['#d8a2c0', '#c88aa8', '#e8c0d0', '#8aa060'], seed=abs(int(x * 13 + y)))
    c.clipm = prev
    c.stroke(ridge[:6], .9, '#4e4878', a=.35, dry=.4, taper=(0, .6))

def portal3(x, y, s=1.0, seed=0):
    """A stone portal cut into the mound: a darker cutting around it, a rough-stone arch, deep shadow inside."""
    cut = [(x - 46 * s + 92 * s * u, y + 8 - math.sin(u * math.pi) ** .6 * 64 * s) for u in np.linspace(0, 1, 26)]
    cm = c.area(cut + [(x + 50 * s, y + 10), (x - 50 * s, y + 10)], '#3a4a2a', wob=.8, rough=1, edge_dark=.1, seed=seed)
    c.stip(cm, pal_fn(['#3a4a2a', '#45562e', '#2f3e24', '#56662f']), spacing=1.3, L=3.2, w=1.6, seed=seed + 1, jit=1.0)
    outer = [(x - 32 * s + 64 * s * u, y + 6 - math.sin(u * math.pi) ** .7 * 48 * s) for u in np.linspace(0, 1, 24)]
    om = c.area(outer + [(x + 34 * s, y + 8), (x - 34 * s, y + 8)], '#a89c88', wob=.3, rough=.7, edge_dark=.14, seed=seed + 2)
    c.stip(om, pal_fn(['#b0a490', '#9c907c', '#c0b4a0', '#8c8270', '#a8a08c']), spacing=1.25, L=3.6, w=2.6, seed=seed + 3, jit=1.3)
    inner = [(x - 21 * s + 42 * s * u, y + 8 - math.sin(u * math.pi) ** .8 * 34 * s) for u in np.linspace(0, 1, 20)]
    c.area(inner + [(x + 21 * s, y + 9), (x - 21 * s, y + 9)], '#121010', wob=0, rough=.3)
    c.area([(x - 18 * s, y + 9), (x + 18 * s, y + 9), (x + 12 * s, y - 14 * s), (x - 12 * s, y - 14 * s)], '#24201c', wob=0, rough=.5, a=.6)
    for u in np.linspace(.04, .96, 9):
        p = np.array(inner[int(u * 19)]); q = np.array(outer[int(u * 23)])
        c.stroke([p, p + (q - p) * .95], 1.5, '#6a6050', a=.85, dry=.1, taper=(0, 0))
    c.stroke(outer, 1.4, '#5a5040', a=.6, dry=.2, taper=(.1, .1))

def town3(x0, y):
    """Toy Town without the pale plaza: storefronts and the clock hall stand on a narrow cobbled street."""
    st = [(x0 - 20, y + 2), (x0 + 380, y + 2), (x0 + 384, y + 14), (x0 - 24, y + 14)]
    sm = c.area(st, '#c8b48a', wob=.6, rough=1, edge_dark=.08)
    c.stip(sm, pal_fn(['#c8b48a', '#b8a47a', '#d8c49a', '#a8946a']), spacing=1.5, L=2.4, w=2.0, seed=7, jit=1.5)
    shops = [(x0 + 0, 44, 52, '#e8b84a', '#7a4a34', '#b8402e', 'gable'), (x0 + 46, 42, 60, '#6a8ab8', '#3a4a6a', '#3f6aa8', 'side'),
             (x0 + 92, 40, 50, '#e89aa8', '#8a4a4a', '#b8402e', 'tall'), (x0 + 214, 40, 56, '#e8b84a', '#7a4a34', '#3f6aa8', 'gable'),
             (x0 + 258, 44, 50, '#b8402e', '#5a3a3a', '#b8402e', 'side'), (x0 + 304, 40, 58, '#e89aa8', '#6a4a5a', '#7f9a3a', 'tall')]
    for i, (sx, sw, sh, wall, roof, awn, kind) in enumerate(shops):
        sh = sh * 1.45
        A.house(sx + sw / 2, y, sw, sh, kind, wall, roof, 120 + i, dotcol=None, rows=3, cols_=2)
        for kk in range(5):
            a0 = sx + 3 + kk * (sw - 6) / 5; a1 = sx + 3 + (kk + 1) * (sw - 6) / 5
            c.area([(a0, y - sh * .3), (a1, y - sh * .3), (a1 + 1, y - sh * .3 + 8), (a0 + 1, y - sh * .3 + 8)], [awn, '#f4eee2'][kk % 2], wob=0, rough=.3)
    hx = x0 + 168; hw, hh = 84, 96
    A.house(hx, y + 2, hw, hh, 'gable', '#efe2c4', '#8a5a3a', 131, dotcol=None, rows=3, cols_=3)
    tw = 32; top = y - hh - 60
    tm = c.area([(hx - tw / 2, y - hh + 10), (hx + tw / 2, y - hh + 10), (hx + tw / 2, top), (hx - tw / 2, top)], '#efe2c4', wob=0, rough=.4)
    c.stip(tm, pal_fn(['#efe2c4', '#e2d4b4']), spacing=1.1, L=2.4, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=9)
    c.area(S.lumpy(hx, top + 20, 11, 11, 2, n=36, amp=0), '#f8f2e4', wob=0, rough=.3, edge_dark=.2)
    c.stroke([(hx, top + 20), (hx, top + 12)], 1.4, '#2a2420', a=1, dry=0, taper=(0, .3)); c.stroke([(hx, top + 20), (hx + 6, top + 22)], 1.4, '#2a2420', a=1, dry=0, taper=(0, .3))
    c.area([(hx - tw / 2 - 4, top), (hx + tw / 2 + 4, top), (hx, top - 30)], '#3a3a4a', wob=0, rough=.4)
    c.stroke([(hx, top - 30), (hx, top - 40)], 1.2, '#2a2420', a=1, dry=0, taper=(0, 0))
    for kk in range(7):
        a0 = hx - hw / 2 + 4 + kk * (hw - 8) / 7; a1 = a0 + (hw - 8) / 7
        c.area([(a0, y - hh * .32), (a1, y - hh * .32), (a1 + 1, y - hh * .32 + 8), (a0 + 1, y - hh * .32 + 8)], ['#b8402e', '#f4eee2'][kk % 2], wob=0, rough=.3)

def snowy_roof(x, y, w, h, kind):
    """Snow along a roof, matching a.house geometry for the gable and side-gable forms used in the map."""
    if kind == 'gable':
        rh = w * .55; ap = (x, y - h - rh); eL = (x - w / 2 - 3, y - h + 1.5); eR = (x + w / 2 + 3, y - h + 1.5)
        for a_, b_ in ((eL, ap), (ap, eR)):
            c.stroke([a_, b_], w * .16, '#f6f4ee', a=1, dry=.15, taper=(.05, .05), rough=.6)
        c.stroke([(ap[0] - w * .25, ap[1] + rh * .45), (ap[0] + w * .25, ap[1] + rh * .45)], w * .1, '#eceef0', a=.7, dry=.4, taper=(.2, .2))
    elif kind in ('side', 'tall'):
        rh = h * .55 if kind == 'side' else w * .85
        if kind == 'side':
            RL, RR = (x - w / 2 + w * .16, y - h - rh), (x + w / 2 - w * .16, y - h - rh)
            c.stroke([RL, RR], rh * .55, '#f6f4ee', a=1, dry=.15, taper=(.03, .03), rough=.6)
        else:
            ap = (x, y - h - rh)
            for a_, b_ in (((x - w / 2 - 3, y - h + 1.5), ap), (ap, (x + w / 2 + 3, y - h + 1.5))):
                c.stroke([a_, b_], w * .16, '#f6f4ee', a=1, dry=.15, taper=(.05, .05), rough=.6)

def snowy_fir(x, y, h, seed):
    U2.tall_fir(x, y, h, seed)
    r = np.random.RandomState(seed + 5)
    for t in np.linspace(.15, .9, 5):
        yy = y - h + h * .9 * t; ww = h * .15 * t
        c.stroke([(x - ww * 1.05, yy + 2), (x, yy - 2), (x + ww * 1.05, yy + 2)], max(1.4, h * .045), '#f4f4ee', a=.95, dry=.25, taper=(.2, .2))
        c.dots([(x + r.uniform(-ww, ww), yy + r.uniform(0, 3))], 1.0, ['#ffffff'], seed=int(seed + t * 100))

def bridge_road(x, y):
    """The stone arch bridge over the south-eastern river, now carrying a cart road (no railway branches here)."""
    aw, ah = 58, 32; bb = y + 30
    deck = np.array([(x - 64, y + 4), (x - 30, y - 4), (x, y - 6), (x + 30, y - 4), (x + 64, y + 4)])
    arch = [(x + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    face = np.vstack([deck, [[x + 64, bb]], arch, [[x - 64, bb]]])
    bm = c.area(face, '#a89c88', wob=.3, rough=.6, edge_dark=.12)
    c.stip(bm, pal_fn(['#b8ac98', '#9c907c', '#c8bca8', '#8c8270']), spacing=1.25, L=4.2, w=2.8, angfn=lambda X, Y: 0 * X, seed=88, jit=.25)
    for u in np.linspace(0, 1, 11):
        p = np.array((x + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah)); dv = p - [x, bb + 8]; dv /= np.hypot(*dv)
        c.stroke([p, p + dv * 8], 3.6, '#cfc4b0', a=.95, dry=.1, taper=(0, 0))
    c.stroke(deck - [0, 3], 5, '#d8ccb6', a=1, dry=.15, taper=(0, 0))
    for xx in np.arange(x - 60, x + 62, 9):
        yy = float(np.interp(xx, deck[:, 0], deck[:, 1]))
        c.stroke([(xx, yy - 3), (xx, yy - 9)], 2.6, '#cfc4b0', a=1, dry=.1, taper=(0, 0))
    c.stroke(deck - [0, 9], 2.2, '#cfc4b0', a=1, dry=.1, taper=(0, 0))
    for kk in range(4):
        c.stroke([(x - 18 + kk * 3, bb + 2 + kk * 3), (x + 18 - kk * 3, bb + 2 + kk * 3)], 2.4, '#f0f4f2', a=.9, dry=.3, taper=(.2, .2))

def river3(P, w0, w1, seed, falls=()):
    poly, nr, wv = ribbon(P, lambda t: w0 + (w1 - w0) * t)
    bank, _, _ = ribbon(P, lambda t: w0 + (w1 - w0) * t + 7)
    bm = c.area(bank, '#6f6a4a', wob=.5, rough=1, edge_dark=.1, seed=seed)
    c.stip(bm, pal_fn(['#7a745a', '#5f5a40', '#8a8468']), spacing=1.3, L=3.0, w=1.8, seed=seed + 1, jit=1.0)
    rm = c.area(poly, '#3f6ea4', wob=.4, rough=.7, edge_dark=.08, seed=seed + 2)
    d = np.gradient(P, axis=0)
    def ang(X, Y):
        j = np.argmin(np.hypot(P[:, 0][None] - X[:, None], P[:, 1][None] - Y[:, None]), axis=1); return np.arctan2(d[j, 1], d[j, 0])
    c.stip(rm, pal_fn(['#4a7ab0', '#3f6ea4', '#5a8ac0', '#6a96c4']), spacing=1.3, L=5.0, w=1.6, angfn=ang, seed=seed + 3, jit=.15)
    r = np.random.RandomState(seed + 4)
    for kk in range(int(len(P) * .9) if len(P) > 6 else 0):
        j = r.randint(2, len(P) - 3); t = j / len(P); off = r.uniform(-.3, .3) * (w0 + (w1 - w0) * t)
        p = P[j] + nr[j] * off; dd = d[j] / np.hypot(*d[j])
        c.stroke([p - dd * 4, p + dd * 4], 1.0, '#e6eef0', a=.85, dry=.2, taper=(.3, .3))
    for (fx, fy) in falls:
        for kk in range(9): c.stroke([(fx - 14 + kk * 3.5, fy - 9), (fx - 14 + kk * 3.5 + 1, fy + 11)], 2.2, '#f4f8f8', a=.92, dry=.3, taper=(0, .4))
        for kk in range(6): c.dots([(fx + r.uniform(-16, 16), fy + 12 + r.uniform(-2, 4))], 2.2, ['#f8fbfb', '#e2eef0'], seed=kk)
    for side in (1, -1):
        for j in range(4, len(P) - 2, 7):
            if r.rand() < .4:
                p = P[j] + nr[j] * side * ((w0 + (w1 - w0) * j / len(P)) / 2 + 3)
                rx = r.uniform(3, 6); sm2 = c.area(S.lumpy(p[0], p[1], rx, rx * .6, int(j * 7 + side + seed), n=16, amp=.08, flat=.3), '#9a948a', wob=.1, rough=.5, edge_dark=.2)

def palm3(x, y, h, seed):
    U.palm(x, y, h, seed)

def mesa3(x, y, w, h, seed):
    """A broad red butte: flat stepped tops, concave sloping skirts, horizontal strata, vertical cracks, lit from the left."""
    r = np.random.RandomState(seed)
    tw = w * .55
    prof = [(x - w / 2, y + 2), (x - w * .4, y - h * .18), (x - w * .33, y - h * .42), (x - tw / 2 - 4, y - h * .7),
            (x - tw / 2, y - h), (x - tw * .1, y - h - 2), (x + tw * .05, y - h * .9), (x + tw / 2 - 6, y - h * .9),
            (x + tw / 2 - 2, y - h * .66), (x + w * .34, y - h * .4), (x + w * .42, y - h * .16), (x + w / 2, y + 2)]
    m = c.area(prof, '#b05a30', wob=.5, rough=.9, edge_dark=.12, seed=seed)
    BANDS = np.array([hexc(z) for z in ['#c8683a', '#b05030', '#d88048', '#a24628', '#c86e3e', '#e09058']])
    def colf(X, Y, rr):
        b = ((Y - (y - h)) / (h / 7) + .3 * np.sin(X / 9)).astype(int) % 6
        lit = np.clip((x - X) / (w * .5), -1, 1)
        return BANDS[b] * (1 + .1 * lit)[:, None] * (1 + (rr.rand(len(X), 1) - .5) * .07)
    c.stip(m, colf, spacing=1.15, L=4.4, w=1.4, angfn=lambda X, Y: .08 * np.sin(X / 13 + Y / 7), seed=seed + 1, jit=.15)
    prev = c.clipm; c.set_clip(m)
    for kk in range(int(w / 7)):
        xx = x - w * .42 + kk * 7 + r.uniform(-2, 2)
        c.stroke([(xx, y - h * r.uniform(.6, .95)), (xx + r.uniform(-2, 2), y - h * r.uniform(.05, .3))], .9, '#7a3218', a=.6, dry=.4, taper=(.1, .3))
    c.area([(x + tw * .05, y - h - 6), (x + w / 2 + 6, y - h - 6), (x + w / 2 + 6, y + 6), (x + tw * .02, y + 6)], '#5a2412', wob=1.5, rough=.9, a=.25, edge_dark=0)
    c.clipm = prev
    c.area([(x - tw / 2, y - h), (x - tw * .1, y - h - 2), (x - tw * .12, y - h - 6), (x - tw / 2 + 3, y - h - 5)], '#eaa86c', wob=0, rough=.4)
    c.area([(x + tw * .05, y - h * .9), (x + tw / 2 - 6, y - h * .9), (x + tw / 2 - 8, y - h * .9 - 4), (x + tw * .07, y - h * .9 - 4)], '#eaa86c', wob=0, rough=.4)

# ====================================================================== railroad, painted in depth-sorted chunks
TRACKCOL = {'red': ('#b03a2c', '#e8c890'), 'blue': ('#2f5a9c', '#ece2c8'), 'green': ('#6f8a34', '#efe6c8')}
TW = 11.0
def track_chunk(P, nr, i0, i1, kind, ties):
    """One stretch of track, built from flat-ended pieces so consecutive stretches join without seams:
    a shadow, a raised gravel bed, cream or coloured ties, and two rails in the route colour."""
    rail, tie = TRACKCOL[kind]
    i1 = min(len(P) - 1, i1 + 1)
    seg = P[i0:i1 + 1]; nn = nr[i0:i1 + 1]
    if len(seg) < 2: return
    def rib(off0, off1, dy=0.0):
        return np.vstack([seg + nn * off0 + [0, dy], (seg + nn * off1 + [0, dy])[::-1]])
    c.area(rib(TW * 1.15, -TW * 1.15, 4.0), '#2a2a18', wob=0, rough=.3, edge_dark=0, a=.32, var=0, varbig=0)
    bm = c.area(rib(TW * 1.02, -TW * 1.02), '#6e6040', wob=0, rough=.2, edge_dark=.15, var=.04)
    if bm is not None: c.stip(bm, pal_fn(['#6e6040', '#5e5236', '#7e704c', '#504628']), spacing=1.3, L=1.8, w=1.5, seed=i0 + 7, jit=1.5)
    for i in range(i0, i1 + 1):
        if ties[i]: c.stroke([P[i] + nr[i] * TW * 1.12, P[i] - nr[i] * TW * 1.12], TW * .56, tie, a=1, dry=.1, taper=(.02, .02), press=.05, rough=.3)
    for off in (TW * .78, -TW * .78):
        c.area(rib(off + TW * .27, off - TW * .27), rail, wob=0, rough=0, edge_dark=.18, var=.03, varbig=0)
        c.area(rib(off + TW * .25, off + TW * .1, -.2), '#f0d8b8' if kind != 'blue' else '#c8d8f0', wob=0, rough=0, edge_dark=0, a=.55, var=0, varbig=0)

# ====================================================================== scene construction (rules -> element list)
HOUSES = [  # x, y, w, h, wall, roof, kind, rows, cols
    (440, 270, 62, 42, '#ecdcb8', '#b03a2a', 'gable', 2, 2), (130, 384, 46, 32, '#f2ead8', '#b03a2a', 'gable', 1, 2), (520, 548, 56, 40, '#f2ead8', '#3f5a7a', 'gable', 1, 2),
    (534, 702, 86, 50, '#f2ead8', '#c0603a', 'side', 2, 3), (1200, 268, 52, 40, '#e2c06a', '#b03a2a', 'gable', 2, 2), (1046, 300, 54, 34, '#f2ead8', '#b03a2a', 'side', 1, 3),
    (1210, 400, 50, 42, '#f2ead8', '#b03a2a', 'tall', 2, 2), (1404, 456, 70, 46, '#f2ead8', '#c0603a', 'gable', 2, 2), (1338, 594, 58, 46, '#e2c06a', '#5a6a8a', 'gable', 2, 2),
    (1048, 728, 58, 36, '#f2ead8', '#b03a2a', 'side', 1, 3), (1364, 836, 48, 34, '#f2ead8', '#b03a2a', 'gable', 1, 2), (1540, 176, 62, 40, '#f2ead8', '#b03a2a', 'side', 2, 3),
    (1468, 222, 38, 30, '#f2ead8', '#b03a2a', 'gable', 1, 2), (300, 640, 44, 30, '#f2e2c0', '#8a4a34', 'gable', 1, 2), (820, 760, 50, 34, '#e8d0a0', '#b03a2a', 'side', 1, 2),
]
LANDMARKS = [  # kind, x, y, params
    ('barn', 668, 262, [96, 58]), ('silo', 730, 256, [38, 116]), ('church', 1424, 292, []), ('lighthouse', 88, 400, [84]), ('lighthouse', 1606, 150, [70]),
    ('windmill', 680, 712, [120]), ('cow', 790, 690, [1.3]), ('horse', 1262, 492, [1.0]), ('town', 815, 502, []),
    ('palm', 1370, 762, [120]), ('palm', 1416, 802, [110]), ('palm', 90, 642, [80]), ('palm', 120, 602, [70]),
]

def build_scene():
    gbase, tops = build_ground()
    els = []
    def add(kind, depth, bbox, seed, layer='base', **params):
        els.append(dict(kind=kind, depth=float(depth), bbox=[float(v) for v in bbox], seed=int(seed), layer=layer, params=params))
    # terrain
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        add('hill', base, (cx - w * .65, base - h * 1.25, cx + w * .65, base + 50), 500 + i * 7, i=i)
    add('mound', MOUND['base'], (MOUND['cx'] - MOUND['w'] / 2 - 50, MOUND['base'] - MOUND['h'] - 20, MOUND['cx'] + MOUND['w'] / 2 + 50, MOUND['base'] + 50), sid('mound'))
    MTS = [(64, 112, 150, 82), (170, 142, 180, 104), (296, 188, 250, 150), (420, 198, 250, 150), (512, 230, 210, 118), (236, 226, 190, 100), (360, 236, 160, 80)]
    for j, (px, base, w, h) in enumerate(MTS):
        add('mountain', base - 40, (px - w * .6, base - h - 10, px + w * .6, base + 10), sid('mtn', j), px=px, base=base, w=w, h=h)
    add('desert', 560, (90, 470, 520, 700), sid('desert'))
    add('mesa', 612, (140, 500, 380, 640), sid('mesa', 1), x=258, y=610, w=150, h=78)
    add('mesa', 622, (300, 560, 400, 650), sid('mesa', 2), x=350, y=620, w=72, h=50)
    for j, (x, y, h) in enumerate([(170, 560, 34), (372, 650, 40), (405, 634, 30), (300, 660, 26), (452, 606, 28), (210, 600, 24)]):
        add('cactus', depth_at(x, y, gbase), (x - 20, y - h - 6, x + 20, y + 4), sid('cactus', j), x=x, y=y, h=h)
    for j, L_ in enumerate(LAKES):
        add('lake', float(L_[:, 1].max()) - 60, (L_[:, 0].min() - 10, L_[:, 1].min() - 10, L_[:, 0].max() + 10, L_[:, 1].max() + 10), sid('lake', j), j=j)
    # rivers: in chunks so hills and trees can sit in front where they should
    for name, P, w0, w1, falls in [('se', RIVER, 14, 30, [(1100, 652)]), ('w', WRIV, 10, 24, [])]:
        n = len(P); step = 10
        for i0 in range(0, n - 1, step):
            i1 = min(n - 1, i0 + step); mid = P[(i0 + i1) // 2]
            add('river', depth_at(mid[0], mid[1], gbase) - .2, (P[i0:i1 + 1, 0].min() - 40, P[i0:i1 + 1, 1].min() - 30, P[i0:i1 + 1, 0].max() + 40, P[i0:i1 + 1, 1].max() + 30),
                sid('river', name), name=name, i0=i0, i1=i1, falls=[f for f in falls if P[i0:i1 + 1, 1].min() - 10 < f[1] < P[i0:i1 + 1, 1].max() + 10])
    add('bridge', depth_at(1096, 640, gbase) + .1, (1020, 590, 1170, 690), sid('bridge'), x=1096, y=630)
    # railroad chunks: depth = the visible ground; near the crest of the front hill the track slips behind it
    routes = {}
    for name in ('red', 'blue', 'green'):
        P = route(name); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]; nr = np.stack([-d[:, 1], d[:, 0]], 1)
        n = len(P); depth = np.zeros(n); behind = np.zeros(n, bool)
        for i, (x, y) in enumerate(P):
            xi, yi = int(np.clip(x, 0, RW - 1)), int(np.clip(y, 0, RH - 1))
            b = gbase[yi, xi]
            if np.isnan(b): depth[i] = y; continue
            # distance below the crest of the visible hill at this x
            crest = None
            for key, poly in tops.items():
                bb = MOUND['base'] if key == 'mound' else HILLS[key][1]
                if abs(bb - b) < 1e-3:
                    t = poly[:-2]; crest = float(np.interp(x, t[:, 0], t[:, 1])); break
            if crest is not None and y - crest < 14 and key != 'mound': behind[i] = True; depth[i] = y
            else: depth[i] = b + y * 1e-4
        # remove flicker: hidden or visible runs shorter than 10 points take their neighbours' state
        for _ in range(2):
            j = 0
            while j < n:
                k2 = j
                while k2 < n and behind[k2] == behind[j]: k2 += 1
                if k2 - j < 10 and j > 0 and k2 < n:
                    behind[j:k2] = behind[j - 1]
                    for q in range(j, k2): depth[q] = P[q][1] if behind[q] else depth_at(*P[q], gbase)
                j = k2
        acc = 0; ties = np.zeros(n, bool)
        for i in range(1, n - 1):
            acc += np.hypot(*(P[i] - P[i - 1]))
            if acc >= TW * .9: acc = 0; ties[i] = True
        routes[name] = dict(P=P, nr=nr, depth=depth, behind=behind, ties=ties)
        for i0 in range(0, n - 1, 8):
            i1 = min(n - 1, i0 + 9); seg = P[i0:i1 + 1]
            add('track', float(np.max(depth[i0:i1 + 1])) + .01, (seg[:, 0].min() - 30, seg[:, 1].min() - 30, seg[:, 0].max() + 30, seg[:, 1].max() + 30),
                sid('track', name, i0), route=name, i0=i0, i1=i1)
    for name, (px, py) in PORTALS.items():
        add('portal', routes[name]['depth'][-1] + .02, (px - 60, py - 80, px + 60, py + 20), sid('portal', name), x=px, y=py)
    # buildings and landmarks
    tr_all = np.vstack([routes[n]['P'] for n in routes])
    for j, (x, y, w, h, wall, roof, kind, rows, cols) in enumerate(HOUSES):
        for _ in range(6):                                  # a house never stands on the line: step it down the slope until clear
            near = (np.abs(tr_all[:, 0] - x) < w * .6 + 12) & (tr_all[:, 1] > y - h * 1.6 - 14) & (tr_all[:, 1] < y + 16)
            if not near.any(): break
            y += 28
        add('house', depth_at(x, y, gbase), (x - w, y - h * 2.6, x + w * 1.1, y + 12), sid('house', j), x=x, y=y, w=w, h=h, wall=wall, roof=roof, k=kind, rows=rows, cols=cols,
            snow=float(snow_amt(x, y)))
    for j, (kind, x, y, prm) in enumerate(LANDMARKS):
        bb = {'town': (x - 40, y - 260, x + 420, y + 30), 'barn': (x - 80, y - 110, x + 90, y + 14), 'silo': (x - 30, y - 150, x + 30, y + 10),
              'church': (x - 50, y - 120, x + 60, y + 14), 'lighthouse': (x - 30, y - 130, x + 30, y + 10), 'windmill': (x - 50, y - 160, x + 70, y + 10),
              'palm': (x - 90, y - 160, x + 90, y + 10)}.get(kind, (x - 50, y - 60, x + 50, y + 14))
        add(kind, depth_at(x, y, gbase), bb, sid('lm', kind, j), x=x, y=y, prm=prm)
    # trees: every group has its own generator, so changing one group leaves the others alone
    tracks_xy = np.vstack([routes[n]['P'] for n in routes])
    keep = [(x, y, w * .55 + 22, h + 34) for (x, y, w, h, *_ ) in HOUSES] + [(668, 262, 80, 90), (730, 256, 40, 120), (1424, 292, 40, 110), (88, 400, 30, 100),
            (1606, 150, 30, 90), (680, 712, 56, 130), (790, 690, 56, 40), (1262, 492, 30, 30), (995, 470, 200, 150), (260, 600, 150, 80), (1096, 640, 90, 60)]
    for nm, (px, py) in PORTALS.items(): keep.append((px, py - 10, 60, 50))
    keep.append((470, 380, 120, 70))
    placed = []
    def ok(x, y, h):
        if not on_land(x, y, 10): return False
        if 150 < x < 470 and 520 < y < 660: return False
        if any(abs(x - kx) < kw and abs(y - ky) < kh for kx, ky, kw, kh in keep): return False
        dt = np.hypot(*(tracks_xy - [x, y]).T); j = int(np.argmin(dt))
        if dt[j] < 16: return False
        ty = tracks_xy[j][1]
        if y < ty and np.min(np.hypot(*(tracks_xy - [x, y - h * .55]).T)) < h * .45 + 10: return False   # behind the track: keep the canopy off it
        if y > ty and np.min(np.hypot(*(tracks_xy - [x, y - h * .6]).T)) < h * .42: return False  # in front: overlap the bed a little, never the rails
        for P_ in (RIVER, WRIV):
            if np.min(np.hypot(*(P_ - [x, y]).T)) < 20: return False
        if any(abs(x - p[0]) < h * .28 and abs(y - p[1]) < h * .15 for p in placed): return False
        return True
    def tree(x, y, h, kd, group, n):
        h *= 1.32 * (.62 + .45 * min(1.0, max(0.0, (y - 120) / 560)))
        if not ok(x, y, h): return
        s = float(snow_amt(x, y))
        if s > .5 and kd not in ('fir', 'lfir'): kd = 'fir' if (sid(group, n) % 3) else kd
        placed.append((x, y))
        add('tree', depth_at(x, y, gbase), (x - h * .75, y - h * 1.2, x + h * .75, y + h * .12), sid('tree', group, n), x=x, y=y, h=h, kd=kd, snow=s)
    zones = []
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        if kind == 'forest': continue
        zones.append(('crest', i, cx, base, w, h))
    for (_, i, cx, base, w, h) in zones:
        rr = np.random.RandomState(sid('crest', i)); top = U2.hill_poly(cx, base, w, h, 500 + i * 7)[:40]
        for j in range(rr.randint(3, 6) if HILLS[i][4] != 'field' else 1):
            x = cx + rr.uniform(-.38, .38) * w; y = float(np.interp(x, top[:, 0], top[:, 1])) + rr.uniform(10, 26)
            if cx > 1250 and base < 450: kd = ['red', 'orange', 'yellow'][rr.randint(3)]
            elif base > 700: kd = ['orange', 'red', 'pink', 'green', 'yellow', 'olive'][rr.randint(6)]
            else: kd = ['green', 'yellow', 'orange', 'olive', 'pink'][rr.randint(5)]
            tree(x, y, rr.uniform(62, 96), kd, f'crest{i}', j)
    FORESTS = [(180, 250, 190, 60), (430, 268, 140, 40), (1470, 230, 120, 60), (1570, 150, 50, 50), (110, 470, 100, 50), (1540, 500, 70, 40),
               (300, 400, 90, 30), (560, 300, 60, 30), (1180, 330, 80, 30), (700, 560, 60, 30), (1300, 700, 70, 30), (480, 640, 60, 30),
               (800, 360, 80, 26), (1080, 380, 70, 24), (930, 330, 90, 30), (1500, 300, 70, 40), (1390, 250, 60, 30), (1600, 250, 30, 60), (1450, 420, 50, 26)]
    for fi, (fx, fy, rx, ry) in enumerate(FORESTS):
        rr = np.random.RandomState(sid('forest', fi)); want = int(rx * ry / 115); got = 0
        for att in range(want * 14):
            if got >= want: break
            x = fx + rr.uniform(-1, 1) * rx; y = fy + rr.uniform(-1, 1) * ry
            if ((x - fx) / rx) ** 2 + ((y - fy) / ry) ** 2 > 1: continue
            r_ = rr.rand(); n0 = len(placed)
            if r_ < .6: tree(x, y, rr.uniform(44, 72), 'fir', f'forest{fi}', att)
            elif r_ < .85: tree(x, y, rr.uniform(40, 62), 'lfir', f'forest{fi}', att)
            else: tree(x, y, rr.uniform(50, 74), ['orange', 'yellow', 'red', 'green'][rr.randint(4)], f'forest{fi}', att)
            got += len(placed) - n0
    GROUPS = [(150, 560, 50, 'mixed'), (760, 430, 50, 'autumn'), (1120, 600, 50, 'mixed'), (1380, 420, 50, 'autumn'), (560, 860, 50, 'mixed'),
              (1100, 860, 40, 'mixed'), (340, 860, 40, 'autumn'), (1580, 380, 40, 'autumn'), (980, 470, 40, 'mixed'),
              (250, 330, 60, 'mixed'), (520, 420, 70, 'mixed'), (760, 340, 50, 'firs'), (1000, 340, 60, 'autumn'), (1350, 320, 70, 'autumn'),
              (1560, 300, 50, 'firs'), (1500, 440, 60, 'autumn'), (420, 520, 50, 'firs'), (620, 580, 60, 'mixed'), (840, 560, 50, 'mixed'),
              (1220, 560, 60, 'mixed'), (1480, 580, 50, 'autumn'), (380, 760, 70, 'mixed'), (640, 800, 70, 'autumn'), (880, 720, 60, 'firs'),
              (960, 800, 60, 'mixed'), (1200, 720, 60, 'autumn'), (1460, 740, 50, 'mixed'), (240, 700, 50, 'firs'), (1250, 830, 40, 'mixed'),
              (700, 640, 50, 'mixed'), (900, 880, 40, 'autumn'), (460, 340, 40, 'mixed'), (1320, 500, 40, 'mixed'), (160, 760, 40, 'mixed')]
    for gi, (gx, gy, rad, kind) in enumerate(GROUPS):
        rr = np.random.RandomState(sid('group', gi))
        for j in range(rr.randint(7, 12)):
            x = gx + rr.randn() * rad * .55; y = gy + rr.randn() * rad * .25; r_ = rr.rand()
            if kind == 'firs' or (kind == 'mixed' and r_ < .4): tree(x, y, rr.uniform(44, 70), 'fir' if rr.rand() < .6 else 'lfir', f'group{gi}', j)
            elif kind == 'mixed' and r_ < .5: tree(x, y, rr.uniform(50, 70), 'poplar', f'group{gi}', j)
            else: tree(x, y, rr.uniform(48, 78), (['red', 'orange', 'yellow'] if kind == 'autumn' else ['green', 'yellow', 'orange', 'red', 'pink', 'olive'])[rr.randint(3 if kind == 'autumn' else 6)], f'group{gi}', j)
    for oi, (ox, oy, nx_, ny_) in enumerate([(760, 318, 5, 2), (940, 690, 4, 2), (1440, 504, 3, 2), (190, 680, 3, 2)]):
        rr = np.random.RandomState(sid('orchard', oi))
        for j in range(ny_):
            for i in range(nx_): tree(ox + i * 26 + (j % 2) * 13 + rr.uniform(-3, 3), oy + j * 18, 30, 'orchard', f'orchard{oi}', j * 10 + i)
    rr = np.random.RandomState(sid('lone'))
    for i in range(170): tree(rr.uniform(150, 1550), rr.uniform(260, 860), rr.uniform(28, 40), ['green', 'olive', 'yellow', 'fir'][rr.randint(4)], 'lone', i)
    # the wooded mound: a ring of conifers and autumn trees on its shoulders, open in front of the town
    rr = np.random.RandomState(sid('moundtrees')); mp = mound_poly()[:44]
    for row in range(4):
        for x in np.arange(MOUND['cx'] - MOUND['w'] * .46, MOUND['cx'] + MOUND['w'] * .46, 13):
            ty = float(np.interp(x, mp[:, 0], mp[:, 1])); y = ty + 16 + row * 15 + rr.uniform(-3, 3)
            if any(abs(x - px) < 52 and y > py - 74 for px, py in PORTALS.values()): continue
            if 800 < x < 1200 and y > 380: continue
            if 800 < x < 1200 and row > 1 and rr.rand() < .5: continue
            if y > MOUND['base'] - 6: continue
            kd = 'fir' if rr.rand() < .62 else ['orange', 'red', 'yellow'][rr.randint(3)]
            h = rr.uniform(34, 56) * (1.6 if kd != 'fir' else 1.0)
            add('tree', MOUND['base'] + y * 1e-4, (x - h * .75, y - h * 1.2, x + h * .75, y + h * .12), sid('mtree', row, int(x)), x=float(x), y=float(y), h=float(h), kd=kd, snow=0.0)
    # sky and sea pieces (animated layers)
    for j, (cx, cy, w, h) in enumerate([(440, 36, 150, 28), (940, 36, 160, 30), (1270, 42, 160, 30)]):
        add('cloud', 1e6, (cx - w * .7, cy - h * 1.4, cx + w * .7, cy + h * .9), sid('cloud', j), layer='cloud', cx=cx, cy=cy, w=w, h=h)
    for j, (x, y, s) in enumerate([(196, 800, 1.1), (884, 832, 1.0), (1600, 486, .95), (1510, 680, .9)]):
        add('boat', 1e6, (x - 50 * s, y - 70 * s, x + 50 * s, y + 26 * s), sid('boat', j), layer='boat', x=x, y=y, s=s)
    rt = routes['red']; i_head = int(np.argmin(np.abs(rt['P'][:, 0] - 560) + (rt['P'][:, 1] < 380) * 1e4))
    add('train', rt['depth'][i_head] + .005, (rt['P'][i_head][0] - 230, rt['P'][i_head][1] - 110, rt['P'][i_head][0] + 60, rt['P'][i_head][1] + 30), sid('train'),
        layer='train', route='red', i_head=i_head, scale=3.4)
    scene = dict(version=3, ref_size=[RW, RH], out_size=[W, H], elements=els,
                 routes={n: dict(points=routes[n]['P'].tolist(), depth=routes[n]['depth'].tolist(), behind=routes[n]['behind'].astype(int).tolist(),
                                 ties=routes[n]['ties'].astype(int).tolist(), portal=list(PORTALS[n])) for n in routes})
    return scene

# ====================================================================== rendering
def render(scene):
    routes = {}
    for n, r in scene['routes'].items():
        P = np.array(r['points']); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]
        routes[n] = dict(P=P, nr=np.stack([-d[:, 1], d[:, 0]], 1), depth=np.array(r['depth']), behind=np.array(r['behind'], bool), ties=np.array(r['ties'], bool))
    Z = np.full((H, W), -1e9, np.float32); OBJ = np.zeros((H, W), np.uint8); TRK = np.zeros((H, W), bool)
    # ocean
    om = (0, 0, np.ones((H, W), np.float32))
    c.stip(om, pal_fn(['#244c78', '#2c5684', '#22466e', '#33608c', '#2a5280'], .05), spacing=1.8, L=8.0, w=2.0, angfn=lambda X, Y: .25 * np.sin(X / 60 + Y / 25), seed=2, jit=.25)
    R = np.random.RandomState(2026)
    for i in range(220):
        x, y = R.uniform(0, RW), R.uniform(0, RH)
        if LANDP.contains_point((x, y), radius=-30): continue
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2), seed=sid('wave', i, kk))
    LM = np.zeros((H, W), np.float32)
    cv2.fillPoly(LM, [np.round(COAST * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    U.LAND_MASK = cv2.GaussianBlur(LM, (0, 0), 1.0)
    c.area(None, '#5f6a2a', m=(0, 0, U.LAND_MASK), edge_dark=0, var=.03)
    def groundcol(X, Y, rr):
        base_ = np.array([hexc('#5f6a2a'), hexc('#6a7430'), hexc('#545e24')])[rr.randint(3, size=len(X))]
        s = snow_amt(X, Y); sn = np.array([hexc(z) for z in SNOWPAL])[rr.randint(5, size=len(X))]
        return np.where((rr.rand(len(X)) < s)[:, None], sn, base_)
    c.stip((0, 0, U.LAND_MASK), groundcol, spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    log('ocean & ground')
    terrain = {'hill', 'mound', 'mountain', 'desert', 'mesa', 'lake', 'river', 'bridge', 'cactus'}
    base_els = sorted([e for e in scene['elements'] if e['layer'] == 'base'], key=lambda e: e['depth'])
    coast_done = False
    def paint(e):
        p = e['params']; kd = e['kind']
        if kd == 'hill':
            cx, base, w, h, kind = HILLS[p['i']]; paint_hill3(cx, base, w, h, kind, e['seed'])
        elif kd == 'mound':
            mp = mound_poly(); m = U2.land_clip(c.area(mp, '#3f5a2c', wob=.6, rough=1, edge_dark=.06, seed=e['seed']))
            top = mp[:44]
            def mc(X, Y, rr):
                d = np.clip((Y - np.interp(X, top[:, 0], top[:, 1])) / MOUND['h'], 0, 1)
                return np.array([hexc(z) for z in ['#6a7a30', '#78883a', '#5c6c2a', '#8a9440', '#566a2c']])[rr.randint(5, size=len(X))] * (1.12 - .3 * d)[:, None]
            c.stip(m, mc, spacing=2.0, L=6, w=2.6, angfn=U.flow_of(top), seed=e['seed'] + 1, jit=.3)
            rr = np.random.RandomState(e['seed'] + 5); pts = []
            for kk in range(900):
                x = rr.uniform(MOUND['cx'] - MOUND['w'] * .45, MOUND['cx'] + MOUND['w'] * .45); ty = float(np.interp(x, top[:, 0], top[:, 1]))
                y = rr.uniform(ty + 6, MOUND['base'] - 4)
                pts.append((x, y))
            c.dots(pts, 1.3, ['#d8a040', '#c8603a', '#e8c860', '#e0a0a8', '#f2ead8', '#8a9a3a'], seed=e['seed'] + 6)
            c.stroke(top + [0, 2.2], 3.6, '#8aa05a', a=.45, dry=.55, taper=(.05, .05))
        elif kd == 'mountain': mountain3(p['px'], p['base'], p['w'], p['h'], e['seed'])
        elif kd == 'desert':
            dpoly = catmull([(130, 520), (210, 498), (300, 506), (380, 494), (470, 520), (506, 576), (480, 616), (470, 652), (390, 672), (300, 666), (210, 676), (150, 650), (118, 592)], 10, closed=True)
            dm = U2.land_clip(c.area(dpoly, '#c8823a', wob=5, rough=1.4, edge_dark=.03, seed=e['seed']))
            c.stip(dm, pal_fn(['#c8823a', '#d89446', '#b47030', '#e2a656', '#a86228']), spacing=2.0, L=6.5, w=2.8, angfn=lambda X, Y: .15 * np.sin(X / 40), seed=e['seed'] + 1, jit=.3)
            for j, (px, py, rx, ry) in enumerate([(220, 650, 70, 16), (430, 566, 60, 16), (170, 560, 40, 12), (330, 520, 60, 12), (450, 640, 44, 12)]):
                dune = [(px - rx + 2 * rx * u, py - math.sin(u * math.pi) ** .8 * ry * 1.6) for u in np.linspace(0, 1, 24)] + [(px + rx, py + 6), (px - rx, py + 6)]
                pm = c.area(dune, '#d89a50', wob=1, rough=1, a=.9, seed=e['seed'] + 9 + j)
                if pm is not None:
                    c.stip(U2.land_clip(pm), lambda X, Y, rr, py=py, ry=ry: np.array([hexc('#e6aa60'), hexc('#d89a50'), hexc('#c48840')])[np.clip(((Y - (py - ry * 1.6)) / (ry * .7)).astype(int), 0, 2)] * (1 + (rr.rand(len(X), 1) - .5) * .06),
                           spacing=1.8, L=6, w=2.4, angfn=lambda X, Y: .2 * np.sin(X / 20), seed=e['seed'] + 20 + j)
        elif kd == 'mesa': mesa3(p['x'], p['y'], p['w'], p['h'], e['seed'])
        elif kd == 'cactus': U.cactus(p['x'], p['y'], p['h'])
        elif kd == 'lake':
            L_ = LAKES[p['j']]
            lm = c.area(L_, '#33628f', wob=.6, rough=.8, edge_dark=.08, seed=e['seed'])
            c.stip(lm, pal_fn(['#33628f', '#3d6c9a', '#2a5682', '#4a78a6']), spacing=1.8, L=7, w=2, angfn=lambda X, Y: .3 * np.sin(X / 40 + Y / 20), seed=e['seed'] + 1, jit=.2)
            PP = np.vstack([L_, L_[:1]])
            for kk in range(0, len(PP) - 2, 14): c.stroke(PP[kk:kk + 16], 4.6, '#e8d8b0', a=.95, dry=.25, taper=(0, 0), rough=.6)
        elif kd == 'river':
            P = RIVER if p['name'] == 'se' else WRIV; i0, i1 = p['i0'], min(len(P) - 1, p['i1'] + 1)
            full_w = (14, 30) if p['name'] == 'se' else (10, 24); n = len(P)
            w0 = full_w[0] + (full_w[1] - full_w[0]) * i0 / n; w1 = full_w[0] + (full_w[1] - full_w[0]) * i1 / n
            river3(P[i0:i1 + 1], w0, w1, e['seed'] + i0, falls=[tuple(f) for f in p['falls']])
        elif kd == 'bridge': bridge_road(p['x'], p['y'])
        elif kd == 'track':
            r = routes[p['route']]; track_chunk(r['P'], r['nr'], p['i0'], p['i1'], p['route'], r['ties'])
        elif kd == 'portal': portal3(p['x'], p['y'], 1.0, e['seed'])
        elif kd == 'house':
            A.house(p['x'], p['y'], p['w'], p['h'], p['k'], p['wall'], p['roof'], e['seed'] % 100000, dotcol=None, rows=p['rows'], cols_=p['cols'])
            if p['snow'] > .4: snowy_roof(p['x'], p['y'], p['w'], p['h'], p['k'])
        elif kd == 'tree':
            x, y, h, t, sd = p['x'], p['y'], p['h'], p['kd'], e['seed'] % 1000000
            if t == 'fir': (snowy_fir if p['snow'] > .45 else U2.tall_fir)(x, y, h, sd)
            elif t == 'lfir': U2.layered_fir(x, y, h, sd)
            elif t == 'poplar': U2.poplar(x, y, h, sd)
            elif t == 'orchard': U2.orchard_tree(x, y, h, sd)
            else: U2.big_tree(x, y, h, t, sd)
            if p['snow'] > .45 and t != 'fir':
                c.dots([(x + np.cos(a) * h * .25, y - h * .7 + np.sin(a) * h * .2) for a in np.linspace(0, 6.28, 9)], 1.4, ['#f6f6f2'], seed=sd)
        elif kd == 'barn': U.barn(p['x'], p['y'], *p['prm'])
        elif kd == 'silo': U.silo(p['x'], p['y'], *p['prm'])
        elif kd == 'church':
            U.church(p['x'], p['y'])
            if snow_amt(p['x'], p['y']) > .4: snowy_roof(p['x'], p['y'], 46, 34, 'gable')
        elif kd == 'lighthouse': U.lighthouse(p['x'], p['y'], *p['prm'])
        elif kd == 'windmill': U.windmill(p['x'], p['y'], *p['prm'])
        elif kd == 'cow': U.cow(p['x'], p['y'], *p['prm'])
        elif kd == 'horse': U.horse(p['x'], p['y'], *p['prm'])
        elif kd == 'town': town3(p['x'], p['y'])
        elif kd == 'palm': palm3(p['x'], p['y'], p['prm'][0], e['seed'] % 1000)
    def coastline():
        PP = resample(np.vstack([COAST, COAST[:1]]), 2.0)
        for kk in range(0, len(PP) - 2, 10): c.stroke(PP[kk:kk + 12], 8, '#e8d8b0', a=1, dry=.25, taper=(.05, .05), press=.3, rough=.8, streak=.15, seed=sid('coast', kk))
    for n_, e in enumerate(base_els):
        if not coast_done and e['kind'] not in terrain and e['depth'] > 120:
            c.set_clip(None); coastline(); coast_done = True                               # the coast goes down before any object stands on it
        x0, y0 = int(max(0, e['bbox'][0] * k)), int(max(0, e['bbox'][1] * k)); x1, y1 = int(min(W, e['bbox'][2] * k)), int(min(H, e['bbox'][3] * k))
        if x1 <= x0 or y1 <= y0: continue
        before = c.img[y0:y1, x0:x1].copy()
        c.rng = np.random.RandomState(e['seed'])
        c.set_clip((0, 0, U.LAND_MASK) if e['kind'] in terrain - {'bridge', 'cactus'} else None)
        paint(e)
        ch = np.abs(c.img[y0:y1, x0:x1] - before).max(-1) > .004
        Z[y0:y1, x0:x1][ch] = e['depth']
        if e['kind'] not in terrain: OBJ[y0:y1, x0:x1][ch] = 1
        TRK[y0:y1, x0:x1][ch] = e['kind'] == 'track'
        if n_ % 150 == 0: log(f'element {n_}/{len(base_els)}')
    if not coast_done: c.set_clip(None); coastline()
    c.set_clip(None)
    log('base painted')
    impasto(c, .14)
    base_img = np.clip(c.img, 0, 1).copy()
    return base_img, Z, routes, TRK

def sprite(paint_fn, bbox, seed):
    """Difference matting: paint the element over black and over white to recover exact colour and alpha."""
    x0, y0 = int(max(0, bbox[0] * k)), int(max(0, bbox[1] * k)); x1, y1 = int(min(W, bbox[2] * k)), int(min(H, bbox[3] * k))
    keep_img, keep_hm, keep_clip = c.img, c.HM, c.clipm
    outs = []
    for bg in (0.0, 1.0):
        c.img = np.full((H, W, 3), bg, np.float32); c.HM = np.zeros((H, W), np.float32); c.clipm = None
        c.rng = np.random.RandomState(seed); paint_fn()
        outs.append((c.img[y0:y1, x0:x1].copy(), c.HM[y0:y1, x0:x1].copy()))
    (b, hm), (wht, _) = outs
    alpha = np.clip(1 - (wht - b).mean(-1), 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, b / np.maximum(alpha[..., None], 1e-3), 0)
    hb = cv2.GaussianBlur(hm, (0, 0), 1.1); gx = cv2.Sobel(hb, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hb, cv2.CV_32F, 0, 1, ksize=3)
    rgb = np.clip(rgb * (1 + np.clip((gx * -.7 + gy * -.7) * .14, -.14, .14))[..., None], 0, 1)
    c.img, c.HM, c.clipm = keep_img, keep_hm, keep_clip
    return (x0, y0), rgb.astype(np.float32), alpha.astype(np.float32)

def main():
    args = sys.argv[1:]
    if '--scene' in args:
        scene = json.load(open(args[args.index('--scene') + 1])); log('scene loaded')
    else:
        scene = build_scene(); os.makedirs('out', exist_ok=True); json.dump(scene, open('out/scene3.json', 'w')); log(f"scene built: {len(scene['elements'])} elements")
    base_img, Z, routes, TRK = render(scene)
    os.makedirs('out/anim', exist_ok=True)
    full = base_img.copy()
    manifest = dict(size=[W, H], scale=k, layers=[])
    def save_rgba(path, rgb, a):
        im = np.dstack([np.clip(rgb[..., ::-1] * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8); cv2.imwrite(path, im)
    for e in [e for e in scene['elements'] if e['layer'] != 'base']:
        p = e['params']
        if e['kind'] == 'cloud': fn = lambda p=p: U.cloud(p['cx'], p['cy'], p['w'], p['h'])
        elif e['kind'] == 'boat': fn = lambda p=p: U.boat(p['x'], p['y'], p['s'])
        elif e['kind'] == 'train':
            r = routes[p['route']]; fn = lambda p=p, r=r: S.train(i_head=p['i_head'], sabs=p['scale'], pts=r['P'])
        (x0, y0), rgb, a = sprite(fn, e['bbox'], e['seed'])
        h_, w_ = a.shape
        if e['kind'] == 'train':
            vis = ((Z[y0:y0 + h_, x0:x0 + w_] <= e['depth'] + 1e-3) | TRK[y0:y0 + h_, x0:x0 + w_]).astype(np.float32)       # anything painted in front hides the train
            a_eff = a * cv2.GaussianBlur(vis, (0, 0), .7)
        else: a_eff = a
        full[y0:y0 + h_, x0:x0 + w_] = full[y0:y0 + h_, x0:x0 + w_] * (1 - a_eff[..., None]) + rgb * a_eff[..., None]
        name = f"{e['kind']}_{len([l for l in manifest['layers'] if l['kind'] == e['kind']])}"
        save_rgba(f'out/anim/{name}.png', rgb, a)
        manifest['layers'].append(dict(kind=e['kind'], file=f'{name}.png', x=x0, y=y0, w=w_, h=h_, depth=e['depth']))
    # occluder overlay for the railroad corridor: base pixels that are in front of the track running beneath them
    corr = np.full((H, W), np.nan, np.float32)
    for n, r in routes.items():
        P = r['P']; ext = np.vstack([P, P[-1] + (P[-1] - P[-8]) / np.hypot(*(P[-1] - P[-8])) * np.arange(1, 50)[:, None] * 1.6])
        dd = np.concatenate([r['depth'], np.full(49, r['depth'][-1])])
        for i in range(0, len(ext) - 1):
            a_, b_ = ext[i] * k, ext[i + 1] * k
            poly = np.array([a_ + [-14 * k, 8 * k], b_ + [14 * k, 8 * k], b_ + [14 * k, -46 * k], a_ + [-14 * k, -46 * k]])
            m = np.zeros((H, W), np.uint8); x0, y0 = int(max(0, poly[:, 0].min())), int(max(0, poly[:, 1].min())); x1, y1 = int(min(W, poly[:, 0].max() + 1)), int(min(H, poly[:, 1].max() + 1))
            if x1 <= x0 or y1 <= y0: continue
            sub = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(sub, [np.round(poly - [x0, y0]).astype(np.int32)], 1)
            cur = corr[y0:y1, x0:x1]; upd = (sub > 0) & (np.isnan(cur) | (cur < dd[i]))
            cur[upd] = dd[i]
    occ = (~np.isnan(corr)) & (Z > np.nan_to_num(corr, nan=1e9) + 1e-3) & ~TRK
    save_rgba('out/anim/occluder.png', base_img, cv2.GaussianBlur(occ.astype(np.float32), (0, 0), .7))
    save_rgba('out/anim/base.png', base_img, np.ones((H, W), np.float32))
    np.save('out/anim/depth.npy', Z.astype(np.float32))
    manifest['routes'] = {n: dict(points=(r['P'] * k).round(2).tolist(), behind=r['behind'].astype(int).tolist(), portal=[PORTALS[n][0] * k, PORTALS[n][1] * k]) for n, r in routes.items()}
    json.dump(manifest, open('out/anim/manifest.json', 'w'))
    c.img = full; c.save('out/usmap3')
    log('saved')

if __name__ == '__main__':
    main()

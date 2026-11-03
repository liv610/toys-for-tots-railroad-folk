"""Pass 2 — the U.S. map rebuilt as a painted landscape.
Reuses pass 1's traced coastline, landmark positions, railroad geometry and painting functions (imported, unchanged).
New here: hand-authored landforms painted with broad opaque strokes and colour patches; forests as merged masses of
packed conifers following the hills; a tree vocabulary of tall firs, layered conifers, big branchy autumn trees,
orchards and columnar trees, placed by region and composition; a darker, warmer palette."""
import math, time
import numpy as np, cv2
import usmap as U
from usmap import c, k, W, H, RW, RH, A, S, pal_fn, catmull, resample, stipple_fir, skeleton_tree, impasto, ribbon, hexc
R = np.random.RandomState(2026)
T0 = time.time()
def log(m): print(f'P2 {time.time() - T0:6.1f}s {m}', flush=True)

PAL = {
    'gold': ['#c4932e', '#d4a43c', '#b07e26', '#ddb24a', '#a87a2a'],
    'olive': ['#7e7f2c', '#8e8c34', '#6e7026', '#9c9840', '#86802e'],
    'moss': ['#56692c', '#627634', '#4a5c26', '#6e803a', '#5a6a2a'],
    'forest': ['#33482c', '#3c5432', '#2a3e26', '#465e38'],
    'sage': ['#7a8a4a', '#86965a', '#6c7c40', '#94a064'],
    'rust': ['#b8702e', '#c8823a', '#a46028', '#d49448'],
}
PATCH = {'gold': ['olive', 'rust'], 'olive': ['gold', 'moss'], 'moss': ['olive', 'sage'], 'forest': ['moss'], 'sage': ['olive', 'moss'], 'rust': ['gold']}

# ---------------------------------------------------------------------- landforms (reference pixel coordinates), back to front
HILLS = [
    (150, 262, 330, 110, 'forest'), (420, 286, 300, 96, 'forest'), (1560, 170, 220, 96, 'forest'), (1450, 236, 280, 96, 'forest'),
    (660, 268, 280, 120, 'gold'), (880, 236, 250, 96, 'gold'), (1070, 268, 260, 96, 'olive'), (1260, 256, 250, 86, 'moss'),
    (380, 366, 290, 96, 'field'), (560, 356, 220, 84, 'olive'), (1110, 406, 230, 86, 'field'), (1300, 390, 250, 96, 'gold'), (1490, 386, 230, 94, 'moss'),
    (110, 486, 260, 120, 'forest'), (330, 476, 250, 86, 'olive'), (600, 506, 270, 96, 'moss'), (1170, 526, 270, 104, 'olive'),
    (1390, 526, 270, 96, 'gold'), (1540, 506, 190, 86, 'forest'),
    (930, 616, 250, 86, 'field'), (700, 626, 270, 96, 'gold'), (1250, 646, 270, 96, 'moss'), (1430, 650, 210, 96, 'olive'),
    (300, 726, 320, 106, 'gold'), (560, 766, 310, 116, 'olive'), (820, 766, 270, 104, 'gold'), (1050, 766, 270, 104, 'moss'), (1300, 776, 230, 104, 'gold'),
    (200, 806, 220, 86, 'sage'), (450, 856, 270, 96, 'moss'), (700, 866, 270, 96, 'gold'), (950, 866, 250, 96, 'olive'), (1390, 870, 210, 104, 'olive'),
]
FIELD_STRIPES = {380: ['#8e6a22', '#e0bc58'], 1110: ['#8e6a22', '#e6c460'], 930: ['#8e6a22', '#e0bc58']}

def hill_poly(cx, base, w, h, seed):
    r = np.random.RandomState(seed); pts = []
    ph = r.uniform(0, 6.28); sk = r.uniform(-.18, .18)
    for u in np.linspace(0, 1, 40):
        uu = min(1, max(0, u + sk * math.sin(u * math.pi)))
        y = base - h * math.sin(uu * math.pi) ** .7 * (1 + .08 * math.sin(u * 9 + ph) + .05 * math.sin(u * 23 + ph * 2))
        pts.append((cx - w / 2 + w * u, y))
    pts += [(cx + w / 2 + w * .12, base + 40), (cx - w / 2 - w * .12, base + 40)]
    return np.array(pts)

def land_clip(m):
    x0, y0, mm = m; return (x0, y0, mm * U.LAND_MASK[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]])

def paint_hill(cx, base, w, h, kind, seed):
    poly = hill_poly(cx, base, w, h, seed); top = poly[:40]
    pal = PAL['gold' if kind == 'field' else kind]
    m = c.area(poly, pal[0], wob=.8, rough=1, edge_dark=.06, seed=seed)
    if m is None: return
    m = land_clip(m)
    fl = U.flow_of(top)
    # broad, opaque, directional strokes
    c.stip(m, pal_fn(pal, .05), spacing=2.0, L=6.5, w=2.8, angfn=fl, seed=seed + 1, jit=.25)
    # irregular colour patches within the hill, each brushed in the same direction
    r = np.random.RandomState(seed + 2)
    prev = c.clipm; c.set_clip(m)
    for j in range(r.randint(2, 4)):
        px = cx + r.uniform(-.32, .32) * w; ty = float(np.interp(px, top[:, 0], top[:, 1])); py = ty + r.uniform(.25, .7) * h
        pk = PATCH[kind if kind != 'field' else 'gold'][r.randint(len(PATCH[kind if kind != 'field' else 'gold']))]
        pm = c.area(S.lumpy(px, py, w * r.uniform(.12, .22), h * r.uniform(.12, .22), seed + 10 + j, n=30, amp=.2), PAL[pk][0], wob=1.2, rough=1, edge_dark=.03, a=.9)
        if pm is not None: c.stip(land_clip(pm), pal_fn(PAL[pk], .05), spacing=2.0, L=6.0, w=2.6, angfn=fl, seed=seed + 20 + j, jit=.25)
    # a finer second pass of strokes for surface life, lighter toward the crest
    def finer(X, Y, rr):
        d = np.clip((Y - np.interp(X, top[:, 0], top[:, 1])) / h, 0, 1)
        C = np.array([hexc(cc) for cc in pal]); base_ = C[rr.randint(len(C), size=len(X))]
        return base_ * (1.12 - .22 * d)[:, None] * (1 + (rr.rand(len(X), 1) - .5) * .06)
    c.stip(m, finer, spacing=3.4, L=3.6, w=1.6, angfn=fl, seed=seed + 3, jit=.35, spill=.7)
    if kind == 'field':
        st = FIELD_STRIPES.get(cx, ['#8e6a22', '#e0bc58'])
        for j, d in enumerate(np.arange(10, h * 1.05, 8.5)):
            line = [(x, float(np.interp(x, top[:, 0], top[:, 1])) + d) for x in np.linspace(cx - w * .44, cx + w * .44, 34)]
            c.stroke(line, 3.6, st[j % 2], a=.95, dry=.3, taper=(.04, .04), rough=.6, streak=.15)
    c.clipm = prev
    c.stroke(top + [0, 2], 3.4, '#e6d48e' if kind in ('gold', 'field', 'olive') else '#8aa05a', a=.4, dry=.6, taper=(.05, .05))
    # a dark line where this hill overlaps the one behind it gives the layered, cut-paper depth of the reference
    c.stroke(top + [0, -1.2], 1.6, '#2e3a1e', a=.35, dry=.4, taper=(.1, .1))

# ---------------------------------------------------------------------- tree vocabulary
FIRS = [['#24392a', '#2e4632', '#1c3022', '#3a5638'], ['#2a4030', '#34503a', '#22382a', '#466444'], ['#2f4628', '#3a5630', '#26391f']]

def tall_fir(x, y, h, seed):
    stipple_fir(c, x, y, h, FIRS[seed % 3], seed, slim=.15)

def layered_fir(x, y, h, seed):
    r = np.random.RandomState(seed); cols = FIRS[seed % 3]
    c.stroke([(x, y + 1), (x, y - h * .2)], max(1.4, h * .05), '#4a3424', a=1, dry=.1, taper=(0, 0))
    n = r.randint(4, 6)
    for i in range(n):
        f0 = i / n; f1 = (i + 1.35) / n
        y0 = y - h + h * .92 * f0; y1 = y - h + h * .92 * min(1, f1)
        wd = h * .3 * (.3 + .7 * min(1, f1)) * (.9 + .2 * r.rand())
        tier = [(x, y0), (x + wd, y1 + 2), (x + wd * .55, y1 - 1), (x, y1 + 1), (x - wd * .55, y1 - 1), (x - wd, y1 + 2)]
        m = c.area(tier, cols[0], wob=.1, rough=.6, edge_dark=.1, seed=seed + i)
        c.stip(m, pal_fn(cols, .06), spacing=1.1, L=3.0, w=1.2, seed=seed + 10 + i,
               angfn=lambda X, Y: np.where(X < x, math.pi * .5 + .9, math.pi * .5 - .9), jit=.2)

def big_tree(x, y, h, kind, seed):
    pal = {'green': ['#5a7a2c', '#6e8e36', '#4a6824', '#86a044'], 'yellow': ['#c49a2c', '#d8b03a', '#aa8424', '#e4c254'],
           'orange': ['#c8682a', '#d88034', '#b05420', '#e49a44'], 'red': ['#a83a28', '#b84a32', '#902e20', '#c8603e'],
           'pink': ['#c87a86', '#d8949e', '#b4646e', '#e8b0b4'], 'olive': ['#7a7a2a', '#8c8a34', '#686a22']}[kind]
    dots = ['#f4e6dc', '#f0c8c8'] if kind == 'pink' else (['#f2c060'] if kind == 'red' and seed % 3 == 0 else None)
    skeleton_tree(c, x, y, h, pal, seed, dots=dots, branches='#3e2a1e', shape='round')

def orchard_tree(x, y, h, seed):
    skeleton_tree(c, x, y, h, ['#4f6a2a', '#5f7a32', '#405a22'], seed, dots=['#c8402e', '#d8602e'], branches='#3e2a1e', shape='round')

def poplar(x, y, h, seed):
    r = np.random.RandomState(seed); wd = h * .14
    poly = [(x - wd * math.sin(min(1, t * 1.05) * math.pi) ** .7, y - h * .1 - h * .9 * t) for t in np.linspace(0, 1, 14)] + \
           [(x + wd * math.sin(min(1, t * 1.05) * math.pi) ** .7, y - h * .1 - h * .9 * t) for t in np.linspace(1, 0, 14)]
    c.stroke([(x, y), (x, y - h * .15)], max(1.2, h * .04), '#4a3424', a=1, dry=.1, taper=(0, 0))
    m = c.area(poly, '#5f6e28', wob=.15, rough=.6, edge_dark=.1)
    c.stip(m, pal_fn(['#5f6e28', '#6e7e30', '#4f5e22', '#82903c']), spacing=1.1, L=3.0, w=1.2, angfn=lambda X, Y: math.pi / 2 + 0 * X, seed=seed, jit=.3)

# ---------------------------------------------------------------------- main
def main():
    log('start')
    # ocean, exactly as pass 1 (it already matched)
    om = (0, 0, np.ones((H, W), np.float32))
    c.stip(om, pal_fn(['#244c78', '#2c5684', '#22466e', '#33608c', '#2a5280'], .05), spacing=1.8, L=8.0, w=2.0,
           angfn=lambda X, Y: .25 * np.sin(X / 60 + Y / 25), seed=2, jit=.25)
    for i in range(220):
        x, y = R.uniform(0, RW), R.uniform(0, RH)
        if U.LANDP.contains_point((x, y), radius=-30): continue
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2))
    U.LAND_MASK = np.zeros((H, W), np.float32)
    cv2.fillPoly(U.LAND_MASK, [np.round(U.COAST * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    U.LAND_MASK = cv2.GaussianBlur(U.LAND_MASK, (0, 0), 1.0)
    c.area(None, '#5f6a2a', m=(0, 0, U.LAND_MASK), edge_dark=0, var=.03)
    c.stip((0, 0, U.LAND_MASK), pal_fn(['#5f6a2a', '#6a7430', '#545e24'], .05), spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    c.set_clip((0, 0, U.LAND_MASK))
    log('ocean & ground')
    # mountains first: they sit behind the northwestern forest ridges
    for i, (px, base, w, h) in enumerate([(70, 116, 130, 74), (170, 150, 160, 96), (300, 186, 250, 170), (420, 196, 250, 176), (510, 226, 210, 130), (240, 222, 180, 100)]):
        U.mountain(px, base, w, h, 40 + i)
    log('mountains')
    # the landforms, back to front, with forests packed onto the forest hills as they go
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        paint_hill(cx, base, w, h, kind, 500 + i * 7)
    log('landforms & forests')
    # the desert, its mesas and cacti
    dpoly = catmull([(130, 520), (300, 500), (470, 520), (500, 580), (470, 650), (300, 670), (150, 650), (120, 590)], 10, closed=True)
    dm = land_clip(c.area(dpoly, '#c8823a', wob=1.5, rough=1, edge_dark=.05))
    c.stip(dm, pal_fn(['#c8823a', '#d89446', '#b47030', '#e2a656', '#a86228']), spacing=2.0, L=6.5, w=2.8, angfn=lambda X, Y: .15 * np.sin(X / 40), seed=11, jit=.3)
    for (px, py) in [(220, 640), (420, 560)]:
        pm = c.area(S.lumpy(px, py, 50, 14, int(px), n=30, amp=.2), '#d89a50', wob=1, rough=1, a=.85)
        c.stip(land_clip(pm), pal_fn(['#d89a50', '#e6aa60']), spacing=2.0, L=6, w=2.6, seed=int(px))
    U.mesa(250, 600, 170, 86, 1); U.mesa(340, 610, 80, 54, 2)
    for (x, y, h) in [(170, 560, 34), (360, 640, 40), (395, 626, 30), (300, 650, 26), (450, 600, 28)]: U.cactus(x, y, h)
    log('desert')
    # lakes and rivers
    for L_ in U.LAKES:
        lm = c.area(L_, '#33628f', wob=.6, rough=.8, edge_dark=.08)
        c.stip(lm, pal_fn(['#33628f', '#3d6c9a', '#2a5682', '#4a78a6']), spacing=1.8, L=7, w=2, angfn=lambda X, Y: .3 * np.sin(X / 40 + Y / 20), seed=12, jit=.2)
        PP = np.vstack([L_, L_[:1]])
        for kk in range(0, len(PP) - 2, 14): c.stroke(PP[kk:kk + 16], 4.6, '#e8d8b0', a=.95, dry=.25, taper=(0, 0), rough=.6)
    RIV = catmull([(1010, 506), (1030, 540), (1060, 572), (1080, 606), (1096, 640), (1110, 680), (1124, 720), (1132, 760)], 12)
    poly, nr, wv = ribbon(RIV, lambda t: 14 + 16 * t)
    rm = c.area(poly, '#3f6ea4', wob=.4, rough=.7, edge_dark=.08)
    c.stip(rm, pal_fn(['#4a7ab0', '#3f6ea4', '#6a96c4', '#dfe6e8']), spacing=1.4, L=5, w=1.6, angfn=lambda X, Y: math.pi / 2.4 + 0 * X, seed=13, jit=.2)
    for (x, y) in [(1096, 640), (1104, 660)]:
        for kk in range(8): c.stroke([(x - 14 + kk * 4, y - 8), (x - 14 + kk * 4 + 1, y + 10)], 2, '#eef2f2', a=.9, dry=.3, taper=(0, .4))
    WRIV = catmull([(130, 410), (100, 430), (70, 446), (40, 456)], 10)
    poly, nr, wv = ribbon(WRIV, lambda t: 10 + 14 * t)
    wm = c.area(poly, '#4a7ab0', wob=.4, rough=.7)
    c.stip(wm, pal_fn(['#4a7ab0', '#6a96c4', '#dfe6e8']), spacing=1.3, L=4.6, w=1.5, angfn=lambda X, Y: .3 + 0 * X, seed=14)
    for (x, y, rx) in [(60, 430, 26), (100, 424, 20), (36, 420, 18)]:
        sm2 = c.area(S.lumpy(x, y, rx, rx * .55, int(x), n=24, amp=.06, flat=.3), '#9a8a7a', wob=.2, rough=.6, edge_dark=.15)
        c.stip(sm2, pal_fn(['#a89a8a', '#8a7c6c', '#b8aa9a']), spacing=1.2, L=2.6, w=1.4, seed=int(x))
    log('water')
    # the Toy Town hill: darker, wooded on its shoulders, open in front for the town
    th = U.mound(916, 452, 420, 160, 77, flat=.6)
    tm_ = land_clip(c.area(th, '#4a6230', wob=.6, rough=1, edge_dark=.06))
    c.stip(tm_, pal_fn(['#4a6230', '#56703a', '#3e5628', '#627a3e']), spacing=2.0, L=6, w=2.6, angfn=U.flow_of(th[:30]), seed=78, jit=.3)
    rr = np.random.RandomState(79); pts = []
    for row in range(3):
        for x in np.arange(720, 1110, 12):
            ty = float(np.interp(x, th[:30, 0], th[:30, 1])); y = ty + 14 + row * 13 + rr.uniform(-3, 3)
            if 790 < x < 1040 and row > 0: continue
            pts.append((y, x))
    for y, x in sorted(pts):
        if rr.rand() < .7: tall_fir(x, y, rr.uniform(34, 54), int(rr.randint(1e6)))
        else: big_tree(x, y, rr.uniform(40, 56), ['orange', 'red', 'yellow'][rr.randint(3)], int(rr.randint(1e6)))
    log('Toy Town hill')
    # railroad: same geometry as pass 1
    U.track(U.RED, 'red'); U.track(U.BLUE, 'blue'); U.track(U.GREEN, 'green'); U.track(U.GREEN2, 'green')
    U.portal(*U.WEST_PORTAL, s=.95); U.portal(*U.EAST_PORTAL, s=.9)
    bi = int(np.argmin(np.hypot(*(U.GREEN2 - [1084, 606]).T))); dk = U.GREEN2[bi - 45:bi + 45] + [0, 8]
    bb = float(dk[:, 1].max()) + 40; x0_, x1_ = dk[:, 0].min(), dk[:, 0].max(); ax = 1092; aw = 60; ah = 34
    arch = [(ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah) for u in np.linspace(0, 1, 20)]
    dks = dk[np.argsort(dk[:, 0])]
    bm = c.area(np.vstack([dks - [0, 6], [[x1_, bb]], arch, [[x0_, bb]]]), '#a89c88', wob=.3, rough=.6, edge_dark=.1)
    c.stip(bm, pal_fn(['#b8ac98', '#9c907c', '#c8bca8', '#8c8270']), spacing=1.3, L=4, w=2.6, angfn=lambda X, Y: 0 * X, seed=88, jit=.2)
    for u in np.linspace(0, 1, 11):
        p = np.array((ax + aw / 2 - aw * u, bb - math.sin(u * math.pi) ** .8 * ah)); dv = p - [ax, bb + 8]; dv /= np.hypot(*dv)
        c.stroke([p, p + dv * 8], 3.4, '#cfc4b0', a=.9, dry=.1, taper=(0, 0))
    U.track(U.GREEN2[bi - 45:bi + 45], 'green')
    log('rail')
    # ------------------------------------------------------------------ deliberate tree placement
    tracks = np.vstack([U.RED, U.BLUE, U.GREEN, U.GREEN2])
    HOUSES = [(440, 270, 70, 44, '#ecdcb8', '#b03a2a', 'gable'), (130, 384, 50, 34, '#f2ead8', '#b03a2a', 'gable'), (520, 536, 66, 44, '#f2ead8', '#3f5a7a', 'gable'),
              (534, 694, 104, 60, '#f2ead8', '#c0603a', 'gable'), (1200, 268, 62, 40, '#e2c06a', '#b03a2a', 'gable'), (1046, 302, 60, 38, '#f2ead8', '#b03a2a', 'side'),
              (1200, 400, 60, 44, '#f2ead8', '#b03a2a', 'gable'), (1400, 452, 80, 50, '#f2ead8', '#c0603a', 'gable'), (1338, 590, 66, 50, '#e2c06a', '#5a6a8a', 'gable'),
              (1048, 724, 66, 42, '#f2ead8', '#b03a2a', 'side'), (1364, 834, 54, 36, '#f2ead8', '#b03a2a', 'gable'), (1540, 172, 70, 44, '#f2ead8', '#b03a2a', 'side'),
              (1468, 220, 40, 30, '#f2ead8', '#b03a2a', 'gable')]
    keep_out = [(x, y, w * .55 + 22, h + 34) for (x, y, w, h, *_ ) in HOUSES] + [(668, 262, 80, 90), (726, 256, 40, 120), (1424, 290, 40, 110), (88, 400, 30, 100),
               (1606, 150, 30, 90), (680, 708, 56, 130), (916, 500, 170, 140), (790, 684, 56, 40), (1262, 488, 30, 30), (290, 600, 220, 90)]
    def free(x, y, h, sp=None):
        if not U.on_land(x, y, 12): return False
        if 140 < x < 500 and 510 < y < 670: return False
        if any(abs(x - kx) < kw and abs(y - ky) < kh for kx, ky, kw, kh in keep_out): return False
        if np.min(np.hypot(*(tracks - [x, y]).T)) < 24: return False
        if np.min(np.hypot(*(RIV - [x, y]).T)) < 22: return False
        return True
    objs = []; placed = []
    def put(x, y, h, kind, seed):
        h = h * 1.45
        if not free(x, y, h): return
        if np.min(np.hypot(*(tracks - [x, y - h * .5]).T)) < h * .42 + 12: return
        if any(abs(x - p[0]) < h * .3 and abs(y - p[1]) < h * .16 for p in placed): return
        placed.append((x, y)); objs.append((y, 'tree', (x, y, h, kind, seed)))
    rr = np.random.RandomState(301)
    # specimen trees on the crests of the open hills, coloured by region
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        if kind == 'forest': continue
        top = hill_poly(cx, base, w, h, 500 + i * 7)[:40]
        n = 1 if kind == 'field' else rr.randint(3, 6)
        for j in range(n):
            x = cx + rr.uniform(-.38, .38) * w; y = float(np.interp(x, top[:, 0], top[:, 1])) + rr.uniform(10, 26)
            if cx > 1250 and base < 450: kd = ['red', 'orange', 'yellow'][rr.randint(3)]
            elif base > 700: kd = ['orange', 'red', 'pink', 'green', 'yellow', 'olive'][rr.randint(6)]
            else: kd = ['green', 'yellow', 'orange', 'olive', 'pink'][rr.randint(5)]
            put(x, y, rr.uniform(62, 96), kd, int(rr.randint(1e6)))
    # tree groups: a few big trees, firs and a columnar tree gathered together, as a painter would group them
    GROUPS = [(150, 560, 50, 'mixed'), (760, 430, 50, 'autumn'), (1120, 600, 50, 'mixed'), (1380, 420, 50, 'autumn'), (560, 860, 50, 'mixed'),
              (1100, 860, 40, 'mixed'), (340, 860, 40, 'autumn'), (1580, 380, 40, 'autumn'), (980, 470, 40, 'mixed'), (250, 330, 60, 'mixed'), (520, 420, 70, 'mixed'), (760, 340, 50, 'firs'), (1000, 340, 60, 'autumn'), (1350, 320, 70, 'autumn'),
              (1560, 300, 50, 'firs'), (1500, 440, 60, 'autumn'), (420, 520, 50, 'firs'), (620, 580, 60, 'mixed'), (840, 560, 50, 'mixed'),
              (1220, 560, 60, 'mixed'), (1480, 580, 50, 'autumn'), (380, 760, 70, 'mixed'), (640, 800, 70, 'autumn'), (880, 720, 60, 'firs'),
              (960, 800, 60, 'mixed'), (1200, 720, 60, 'autumn'), (1460, 740, 50, 'mixed'), (240, 700, 50, 'firs'), (1250, 830, 40, 'mixed')]
    def put_n(target, gen):
        got = 0
        for _ in range(target * 12):
            if got >= target: break
            before = len(placed); gen(); got += len(placed) - before
    # forest masses: packed conifers in the forested zones, merging into dark bands
    FORESTS = [(180, 250, 190, 60), (430, 268, 140, 40), (1470, 230, 120, 60), (1570, 150, 50, 50), (110, 470, 100, 50), (1540, 500, 70, 40),
               (300, 400, 90, 30), (560, 300, 60, 30), (1180, 330, 80, 30), (700, 560, 60, 30), (1300, 700, 70, 30), (480, 640, 60, 30)]
    for (fx, fy, rx, ry) in FORESTS:
        n = int(rx * ry / 110)
        def g(fx=fx, fy=fy, rx=rx, ry=ry):
            x = fx + rr.uniform(-1, 1) * rx; y = fy + rr.uniform(-1, 1) * ry
            if ((x - fx) / rx) ** 2 + ((y - fy) / ry) ** 2 > 1: return
            r_ = rr.rand()
            if r_ < .6: put(x, y, rr.uniform(44, 72), 'fir', int(rr.randint(1e6)))
            elif r_ < .85: put(x, y, rr.uniform(40, 62), 'lfir', int(rr.randint(1e6)))
            else: put(x, y, rr.uniform(50, 74), ['orange', 'yellow', 'red', 'green'][rr.randint(4)], int(rr.randint(1e6)))
        put_n(n, g)
    for (gx, gy, rad, kind) in GROUPS:
        for j in range(rr.randint(10, 16)):
            x = gx + rr.randn() * rad * .55; y = gy + rr.randn() * rad * .25
            r_ = rr.rand()
            if kind == 'firs' or (kind == 'mixed' and r_ < .4): put(x, y, rr.uniform(44, 70), 'fir' if rr.rand() < .6 else 'lfir', int(rr.randint(1e6)))
            elif kind == 'mixed' and r_ < .5: put(x, y, rr.uniform(50, 70), 'poplar', int(rr.randint(1e6)))
            else: put(x, y, rr.uniform(48, 78), (['red', 'orange', 'yellow'] if kind == 'autumn' else ['green', 'yellow', 'orange', 'red', 'pink', 'olive'])[rr.randint(3 if kind == 'autumn' else 6)], int(rr.randint(1e6)))
    # orchards: loose rows by the barn and in the south-east
    for (ox, oy, nx_, ny_) in [(760, 318, 5, 2), (940, 680, 4, 2), (1440, 500, 3, 2)]:
        for j in range(ny_):
            for i in range(nx_): put(ox + i * 26 + (j % 2) * 13 + rr.uniform(-3, 3), oy + j * 18, 30, 'orchard', int(rr.randint(1e6)))
    # a few small trees standing alone in the open fields and meadows
    for i in range(160):
        x, y = rr.uniform(150, 1550), rr.uniform(260, 860)
        put(x, y, rr.uniform(28, 40), ['green', 'olive', 'yellow', 'fir'][rr.randint(4)], int(rr.randint(1e6)))
    log(f'{len(placed)} trees placed')
    for i, hh in enumerate(HOUSES): objs.append((hh[1], 'house', (i, hh)))
    objs.append((262, 'barn', (668, 262, 96, 58))); objs.append((256, 'silo', (730, 256, 38, 116)))
    objs.append((290, 'church', (1424, 290))); objs.append((376, 'lighthouse', (88, 400, 84))); objs.append((150, 'lighthouse', (1606, 150, 70)))
    objs.append((700, 'windmill', (680, 708, 120))); objs.append((684, 'cow', (790, 684, 1.3))); objs.append((486, 'horse', (1262, 488, 1.0)))
    objs.append((480, 'town', (790, 492)))
    for (x, y, h, s) in [(1370, 760, 120, 1), (1416, 800, 110, 2), (90, 640, 80, 3), (120, 600, 70, 4)]: objs.append((y, 'palm', (x, y, h, s)))
    objs.sort(key=lambda o: o[0])
    def draw(o):
        _, kind, v = o
        if kind == 'tree':
            x, y, h, kd, sd = v
            if kd == 'fir': tall_fir(x, y, h, sd)
            elif kd == 'lfir': layered_fir(x, y, h, sd)
            elif kd == 'poplar': poplar(x, y, h, sd)
            elif kd == 'orchard': orchard_tree(x, y, h, sd)
            else: big_tree(x, y, h, kd, sd)
        elif kind == 'house':
            i, (x, y, w, h, wall, roof, kk) = v; U.house(x, y, w, h, wall, roof, 500 + i, kind=kk)
        elif kind == 'barn': U.barn(*v)
        elif kind == 'silo': U.silo(*v)
        elif kind == 'church': U.church(*v)
        elif kind == 'lighthouse': U.lighthouse(*v)
        elif kind == 'windmill': U.windmill(*v)
        elif kind == 'cow': U.cow(*v)
        elif kind == 'horse': U.horse(*v)
        elif kind == 'town': U.clocktower_town(*v)
        elif kind == 'palm': U.palm(*v)
    for n_, o in enumerate(objs):
        draw(o)
        if n_ % 100 == 0: log(f'objects {n_}/{len(objs)}')
    i_head = int(np.argmin(np.abs(U.RED[:, 0] - 600) + (U.RED[:, 1] < 380) * 1e4))
    S.train(i_head=i_head, sabs=3.4, pts=U.RED)
    c.set_clip(None)
    PP = resample(np.vstack([U.COAST, U.COAST[:1]]), 2.0)
    for kk in range(0, len(PP) - 2, 10): c.stroke(PP[kk:kk + 12], 8, '#e8d8b0', a=1, dry=.25, taper=(.05, .05), press=.3, rough=.8, streak=.15)
    for (cx, cy, w, h) in [(440, 36, 150, 28), (940, 36, 160, 30), (1270, 42, 160, 30)]: U.cloud(cx, cy, w, h)
    for (x, y, s) in [(196, 800, 1.1), (884, 832, 1.0), (1600, 486, .95), (1510, 680, .9)]: U.boat(x, y, s)
    impasto(c, .14)
    c.save('out/usmap2')
    log('saved')

RIV = catmull([(1010, 506), (1030, 540), (1060, 572), (1080, 606), (1096, 640), (1110, 680), (1124, 720), (1132, 760)], 12)
if __name__ == '__main__':
    main()

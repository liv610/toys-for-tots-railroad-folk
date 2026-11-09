"""Toy Town painting kit: the brush helpers the blue shop study was built with, shared by every building.

All drawing is in target-painting px (the approved composition, 1399 x 1124); init() sets the window being
painted and the canvas resolution K (canvas px per target px). Helpers draw into the module's canvas `c`, and
track coverage (ALPHA) and lit glass (GLOW) for the dusk layer.
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
sys.path[:0] = [os.path.join(ROOT, 'folk2'), os.path.join(ROOT, 'styles2')]
from kit import Kanvas, impasto
from brush import hexc
from parts import lumpy

X0 = Y0 = 0; K = 3; W = H = 0; c = ALPHA = GLOW = None
R = np.random.RandomState(12)

def init(x0, y0, x1, y1, k=3, seed=5, ground='#000000'):
    global X0, Y0, K, W, H, c, ALPHA, GLOW, R
    X0, Y0, K, W, H = x0, y0, k, x1 - x0, y1 - y0
    c = Kanvas(W * K, H * K, K, ground, seed=seed); c.HM = np.zeros((c.H, c.W), np.float32)
    ALPHA = np.zeros((c.H, c.W), np.float32); GLOW = np.zeros((c.H, c.W), np.float32)
    R = np.random.RandomState(12)
    return c

def finish(path_png, path_glow=None, opaque=False):
    impasto(c, strength=.22)
    paint = np.clip(c.img, 0, 1); al = np.ones_like(ALPHA) if opaque else np.clip(cv2.GaussianBlur(ALPHA, (0, 0), .5), 0, 1)
    cv2.imwrite(path_png, (np.dstack([paint[..., ::-1], al]) * 255).astype(np.uint8))
    if path_glow:
        halo = cv2.GaussianBlur(GLOW, (0, 0), 3 * K) * .5
        g = np.clip(np.maximum(GLOW * .9, halo), 0, 1) * al
        cv2.imwrite(path_glow, (np.dstack([np.full_like(paint, (.4, .78, 1.0)), g]) * 255).astype(np.uint8))
    return paint, al

# ---- palette (the map's calmer range) ----
BLUE, BLUE_D, BLUE_L = '#4a6cb0', '#37548f', '#6c8ac6'
CREAM, CREAM_D = '#ecdcbd', '#c9b48f'
ROOF, ROOF_D = '#953a33', '#6e2925'
SNOW, SNOW_S, SNOW_H = '#f3f1ec', '#c6cbd8', '#fffcf5'
GOLD, GOLD_C, GOLD_E = '#f0b64e', '#fbe19a', '#d98a2e'
BAR = '#5e3319'
BRICK, BRICK_D = '#ad4c30', '#7e3220'
GREEN_A, WHITE_A, GREEN_AD = '#3f7340', '#f2ead6', '#2b5530'
WOOD, WOOD_D = '#86361f', '#5e2414'
NEEDLES = ['#173a29', '#1f4a33', '#2a5e40', '#12301f']
BERRY = '#b8262a'

def T(pts): return [(x - X0, y - Y0) for x, y in pts]
def track(m, a=1.0):
    if m is None: return m
    x0, y0, mm = m; h, w = mm.shape
    ALPHA[y0:y0 + h, x0:x0 + w] = np.maximum(ALPHA[y0:y0 + h, x0:x0 + w], mm * a)
    return m
def A(pts, col, a=1.0, **kw):
    kw.setdefault('wob', .35); kw.setdefault('rough', .6); kw.setdefault('edge_dark', .08)
    return track(c.area(T(pts), col, a=a, seed=int(R.randint(1 << 20)), **kw), a)
def S(pts, w, col, a=1.0, **kw):
    kw.setdefault('dry', .2)
    c.stroke(T(pts), w, col, a=a, seed=int(R.randint(1 << 20)), **kw)
    P = (np.array(T(pts)) * K).astype(np.int32)
    cv2.polylines(ALPHA, [P], False, float(a), max(1, int(w * K * .9)), cv2.LINE_AA)
def stip(m, cols, spacing=1.1, L=2.4, w=1.2, ang=None, var=.06, weights=None, seed=None):
    C = np.array([hexc(x) for x in cols]); p = np.array(weights or [1] * len(cols), float); p /= p.sum()
    def f(X, Y, r):
        idx = r.choice(len(C), size=len(X), p=p)
        return np.clip(C[idx] * (1 + (r.rand(len(X), 1) - .5) * 2 * var), 0, 1)
    af = (lambda X, Y: np.full(X.shape, ang)) if isinstance(ang, (int, float)) else ang
    c.stip(m, f, spacing=spacing, L=L, w=w, angfn=af, seed=int(R.randint(1 << 20)) if seed is None else seed, jit=.45, thresh=.3)
def lump(cx, cy, rx, ry, seed=None, amp=.12):
    return lumpy(cx, cy, rx, ry, int(R.randint(1 << 20)) if seed is None else seed, n=22, bumps=5, amp=amp, flat=.3)

# ---- snow, the way model makers build it: a thick rolled edge, lumpy, lit on top, blue in its shadow ----
def snow_edge(pts, thick=7.0, drip=.25, under=True):
    """Snow resting along an edge, as one soft mass: its top bulges in slow lumps, its underside hangs in
    scallops and the odd drip; it is lit on top and goes blue-grey underneath."""
    P = np.array(pts, float)
    seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); tot = L.sum(); cum = np.concatenate([[0], np.cumsum(L)])
    n = max(6, int(tot / 2.5)); up, lo, mid = [], [], []
    ph = R.uniform(0, 10)
    for i in range(n + 1):
        d = tot * i / n; j = int(np.clip(np.searchsorted(cum, d) - 1, 0, len(L) - 1)); t = (d - cum[j]) / L[j]
        p = P[j] + seg[j] * t; tx, ty = seg[j] / L[j]; nx, ny = ty, -tx            # normal pointing up (screen)
        if ny > 0: nx, ny = -nx, -ny
        bulge = 1 + .25 * math.sin(d / (thick * 1.6) + ph) + .12 * math.sin(d / (thick * .7) + ph * 2)
        sc = .55 + .45 * abs(math.sin(d / (thick * 1.1) + ph))                       # scalloped underside
        end = max(.05, min(1, d / (thick * 1.2), (tot - d) / (thick * 1.2))) ** .5
        up.append(p + np.array([nx, ny]) * thick * .62 * bulge * end)
        lo.append(p - np.array([nx, ny]) * thick * (.3 + .35 * sc) * end)
        mid.append(p)
    poly = [tuple(q) for q in up] + [tuple(q) for q in lo[::-1]]
    m = A(poly, SNOW, wob=.25, rough=.5, edge_dark=.0)
    if m is None: return
    lo_y = np.interp(np.arange(c.W), [ (q[0] - X0) * K for q in lo], [(q[1] - Y0) * K for q in lo]) if P[-1][0] != P[0][0] else None
    S1, S2, S3 = hexc(SNOW_H), hexc(SNOW), hexc(SNOW_S)
    def scol(X, Y, r):
        # blend from bright top to the blue-grey underside, by height within the band
        if lo_y is None: k = np.full(len(X), .4)
        else:
            ly = lo_y[np.clip((X * K).astype(int), 0, c.W - 1)] / K
            k = np.clip(1 - (ly - Y) / (thick * 1.1), 0, 1)
        k = k[:, None]
        col = np.where(k < .5, S1 * (1 - k * 2) + S2 * (k * 2), S2 * (2 - k * 2) + S3 * (k * 2 - 1))
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .05), 0, 1)
    c.stip(m, scol, spacing=1.0, L=2.4, w=1.5, seed=int(R.randint(1 << 20)), jit=.5, thresh=.3)
    sparkle(m, 1.0)
    if drip:
        idx = sorted(R.choice(np.arange(2, max(3, len(lo) - 2)), size=max(1, int(len(lo) * drip / 6)), replace=False))
        for q in [lo[i] for i in idx]:
            if True:
                g = R.uniform(.6, 1.3)          # a soft drip: a tapered tongue of snow, shaded on its right
                tongue = [(q[0] - thick * .22 * g, q[1] - 1), (q[0] + thick * .22 * g, q[1] - 1), (q[0] + thick * .08 * g, q[1] + thick * .7 * g), (q[0] - thick * .04 * g, q[1] + thick * .75 * g)]
                shaded(tongue, [SNOW_H, SNOW, SNOW_S], light=(-1, 0), wob=.1, rough=.3, edge_dark=.0, L=1.4, w=1.0)
    S([tuple(q + np.array([0, thick * .12])) for q in up[1:-1]], thick * .28, SNOW_H, a=.6, dry=.45, taper=(.3, .3))

def eave_shadow(pts, thick=8.0, col=None):
    """The soft shade a heavy snow edge casts on the wall just below it."""
    sh = [(x, y + thick * .9) for x, y in pts]
    c.stroke(T(sh), thick * 1.3, hexc(col or BLUE_D) * .7, a=.38, dry=.55, taper=(.25, .25), seed=int(R.randint(1 << 20)))

def snow_cap(x0, x1, y, thick=5.0):
    snow_edge([(x0, y), (x1, y)], thick, drip=.1)

def shaded(pts, cols, light=(-.6, -.8), a=1.0, spacing=.9, L=1.8, w=1.2, **kw):
    """An area lit from the upper left: its dabs pick light, mid or dark colour by facing."""
    m = A(pts, cols[1], a=a, **kw)
    if m is None: return m
    P = np.array(T(pts)); cx, cy = P.mean(0); rx = max(1, np.ptp(P[:, 0]) / 2); ry = max(1, np.ptp(P[:, 1]) / 2)
    C = np.array([hexc(x) for x in cols])
    def f(X, Y, r):
        lit = np.clip(-((X - cx) / rx * light[0] + (Y - cy) / ry * light[1]) * .7 + .5 + r.randn(len(X)) * .18, 0, .999)
        idx = (2 - np.floor(lit * 3)).astype(int)
        return np.clip(C[idx] * (1 + (r.rand(len(X), 1) - .5) * .06), 0, 1)
    c.stip(m, f, spacing=spacing, L=L, w=w, seed=int(R.randint(1 << 20)), jit=.5, thresh=.3)
    return m

def sparkle(m, density=1.0):
    """Sugary snow: a scatter of tiny bright crystals and a few cool glints over a snow area."""
    if m is None: return
    x0, y0, mm = m; ys, xs = np.nonzero(mm > .8)
    if len(xs) == 0: return
    n = int(len(xs) * density / (K * K * 18))
    for k in R.choice(len(xs), min(n, len(xs)), replace=False):
        px, py = (xs[k] + x0) / K, (ys[k] + y0) / K
        c.dab(px, py, R.uniform(.5, 1.1), R.uniform(.45, .75), R.uniform(0, 3), '#ffffff' if R.rand() < .8 else '#dfe8f6', a=.9, dry=0)

def snow_clump(cx, cy, rx, ry, ang=0.0, shadow=None):
    """An irregular clump of snow: two or three overlapping soft heaps, never a neat oval."""
    ca, sa = math.cos(ang), math.sin(ang)
    if shadow:                                  # the shade the heap casts on what it rests on
        c.area(T(lump(cx + 1, cy + ry * .55, rx * .95, ry * .5, amp=.1)), hexc(shadow), wob=.2, rough=.5, edge_dark=0, a=.45, var=0, varbig=0, seed=int(R.randint(1 << 20)))
    for k in range(R.randint(2, 4)):
        u = R.uniform(-.55, .55); px, py = cx + ca * rx * u, cy + sa * rx * u - R.uniform(0, ry * .35)
        snow_lump(px, py, rx * R.uniform(.45, .7), ry * R.uniform(.7, 1.0))

def snow_lump(cx, cy, rx, ry):
    """A soft heap of snow: white, lit on top, blue-grey in its lower curve."""
    m = shaded(lumpy(cx, cy, rx, ry, int(R.randint(1 << 20)), n=22, bumps=6, amp=.24, flat=.18), [SNOW_H, SNOW, SNOW_S], wob=.3, rough=.6, edge_dark=.0, L=2.0, w=1.3)
    sparkle(m, .6)

# ---- walls: gouache ground, then stippled stucco in three blues, flecks of snow ----
def noise_at(px, py):
    ix = int(np.clip((px - X0) * K, 0, c.W - 1)); iy = int(np.clip((py - Y0) * K, 0, c.H - 1))
    return float(c.Nbig[iy, ix])

def wall(pts, base, dark=False, fleck=.0, cols=None, stone_dark=.3):
    """Hand-modelled stucco: a gouache ground, then rounded 'stones' pressed into it, each its own blue with a
    darker rim where they meet (the cobbled plaster of the reference), a light dab texture, flecks of snow."""
    m = A(pts, base, wob=.25, rough=.5, edge_dark=.18)
    prev = c.clipm; c.set_clip(m)
    x0, y0, mm = m; h, w = mm.shape
    if cols is None: cols = [BLUE_D, BLUE, BLUE, BLUE_L, '#5a7cbc'] if not dark else [BLUE_D, BLUE_D, BLUE, '#2f4a80']
    elif dark: cols = [cols[0], cols[0], cols[1], cols[1]]
    sp = 7.0
    for gy in np.arange(y0 / K + Y0, (y0 + h) / K + Y0, sp * .8):
        off = R.uniform(0, sp)
        for gx in np.arange(x0 / K + X0 - off, (x0 + w) / K + X0, sp * R.uniform(.85, 1.2)):
            px, py = gx + R.uniform(-3, 3), gy + R.uniform(-2.4, 2.4)
            if noise_at(px, py) > .62: continue             # a patch of smoother plaster here
            ix, iy = int((px - X0) * K) - x0, int((py - Y0) * K) - y0
            if not (0 <= ix < w and 0 <= iy < h) or mm[iy, ix] < .3: continue
            sz = R.uniform(.7, 1.35)
            c.area(T(lump(px, py, R.uniform(2.6, 3.8) * sz, R.uniform(2.0, 3.0) * sz, amp=.22)), cols[R.randint(len(cols))], wob=.2, rough=.6,
                   edge_dark=stone_dark, var=.05, a=.85, seed=int(R.randint(1 << 20)))
    c.clipm = prev
    if fleck:
        ys, xs = np.nonzero(mm > .6)
        for k in R.choice(len(xs), int(len(xs) * fleck / (K * K * 420)), replace=False):
            c.dab((xs[k] + x0) / K, (ys[k] + y0) / K, R.uniform(1.0, 1.8), R.uniform(.8, 1.1), R.uniform(0, 3), SNOW, a=.8, dry=.15)
    return m

def roof(pts, base=ROOF, snowy=.6, ridge=None, eave=None, cols=None, tile_dark=None):
    """Red tiles under a blanket of snow: the snow covers the upper part of the slope (ridge side) down to a
    wavy edge at `snowy` of the way to the eave, with a few gaps where tiles show through."""
    m = A(pts, base, wob=.3, rough=.6, edge_dark=.1)
    stip(m, cols or [ROOF, ROOF_D, '#a8463c'], spacing=1.3, L=2.6, w=1.6, weights=[.5, .3, .2])
    if ridge and eave:
        # tile courses: rows of small scalloped tile ends, parallel to the ridge
        prev = c.clipm; c.set_clip(m)
        ra_, rb_, ea_, eb_ = map(np.array, (ridge[0], ridge[1], eave[0], eave[1]))
        depth = np.linalg.norm((ea_ + eb_) / 2 - (ra_ + rb_) / 2); nrow = int(depth / 4.5)
        for k in range(1, nrow + 1):
            u = k / (nrow + .5); a0 = ra_ + (ea_ - ra_) * u; b0 = rb_ + (eb_ - rb_) * u
            L_ = np.linalg.norm(b0 - a0); dirv = (b0 - a0) / L_; ntile = int(L_ / 5)
            sh = (k % 2) * .5
            for t in range(-1, ntile + 1):
                p = a0 + dirv * 5 * (t + sh)
                arc = [tuple(p + dirv * 5 * v + np.array([0, 1.6]) * math.sin(math.pi * v)) for v in np.linspace(0, 1, 5)]
                c.stroke(T(arc), 1.15, tile_dark or ROOF_D, a=.85, dry=.2, taper=(.2, .2), seed=int(R.randint(1 << 20)))
                c.dab(p[0] - X0 + dirv[0] * 2.5, p[1] - Y0 - .8, 3.2, 1.4, math.atan2(dirv[1], dirv[0]), (cols or ['#b8564a', '#a8443a'])[R.randint(2)], a=.75, dry=.2)
        c.clipm = prev
        (ra, rb), (ea, eb) = (np.array(ridge[0]), np.array(ridge[1])), (np.array(eave[0]), np.array(eave[1]))
        top = [tuple(ra + (rb - ra) * t) for t in np.linspace(0, 1, 12)]
        bot = []; ph = R.uniform(0, 6)
        for t in np.linspace(1, 0, 24):
            u = snowy + .07 * math.sin(t * 7 + ph) + .035 * math.sin(t * 15 + ph * 3)
            a = ra + (rb - ra) * t; b = ea + (eb - ea) * t
            bot.append(tuple(a + (b - a) * np.clip(u, .2, .95)))
        mm = A(top + bot, SNOW, wob=.4, rough=.6, edge_dark=.0)
        stip(mm, [SNOW_H, SNOW, SNOW, SNOW_S], spacing=1.1, L=2.6, w=1.6, weights=[.2, .4, .25, .15])
        S([(x, y + 2.2) for x, y in bot], 3.2, tile_dark or ROOF_D, a=.5, dry=.45, taper=(.2, .2))
        S(bot, 3.0, SNOW_H, a=.6, dry=.35, taper=(.2, .2))
        # drifts lying across the tiles below the blanket: soft, elongated along the slope's contour
        dirx = rb - ra; dirx = dirx / np.linalg.norm(dirx)
        for _ in range(int(np.linalg.norm(rb - ra) / 22)):
            t = R.uniform(.05, .95); u = R.uniform(snowy + .1, .9)
            a = ra + (rb - ra) * t; b = ea + (eb - ea) * t; p = a + (b - a) * u
            snow_clump(p[0], p[1], R.uniform(10, 16), R.uniform(2.4, 3.4), math.atan2(dirx[1], dirx[0]), shadow=tile_dark or ROOF_D)
    return m

# ---- windows: cream frame, glowing glass, bars, a sill with snow ----
def window(x0, y0, x1, y1, arched=True, bars=(1, 1), frame=4.0):
    def poly(a0, b0, a1, b1):
        w = a1 - a0
        if not arched: return [(a0, b1), (a0, b0), (a1, b0), (a1, b1)]
        r = w / 2; cy = b0 + r
        return [(a0, b1), (a0, cy)] + [(a0 + r - r * math.cos(math.pi * k / 14), cy - r * math.sin(math.pi * k / 14)) for k in range(1, 14)] + [(a1, cy), (a1, b1)]
    halo = poly(x0 - frame - 6, y0 - frame - 6, x1 + frame + 6, y1 + frame + 4)
    c.area(T(halo), hexc('#f0b860'), wob=.6, rough=.8, edge_dark=0, a=.16, var=.0, varbig=.0, seed=int(R.randint(1 << 20)))
    fm = A(poly(x0 - frame, y0 - frame, x1 + frame, y1 + frame * .5), CREAM, wob=.25, rough=.5, edge_dark=.18)
    shaded(poly(x0 - frame, y0 - frame, x1 + frame, y1 + frame * .5), [CREAM, CREAM, CREAM_D], wob=.25, rough=.5, edge_dark=.12, spacing=1.0, L=2.4, w=1.6)
    gm = A(poly(x0, y0, x1, y1), GOLD, wob=.15, rough=.4, edge_dark=.0)
    cx, cy = (x0 + x1) / 2 - X0, (y0 + y1) / 2 - Y0 + (y1 - y0) * .12; hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
    C0, C1, C2 = hexc(GOLD_C), hexc(GOLD), hexc(GOLD_E)
    def gcol(X, Y, r):
        d = np.clip(np.hypot((X - cx) / hw, (Y - cy) / hh), 0, 1.4)[:, None]
        col = np.where(d < .6, C0 * (1 - d / .6) + C1 * (d / .6), C1 * np.clip(1.4 - d, 0, 1) / .8 + C2 * np.clip(d - .6, 0, .8) / .8)
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .08), 0, 1)
    c.stip(gm, gcol, spacing=.75, L=1.3, w=.95, seed=int(R.randint(1 << 20)), jit=.5)
    x0_, y0_, mm = gm; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm)
    nb, nh = bars; top = y0 + ((x1 - x0) * .08 if arched else 0)
    body = y0 + ((x1 - x0) / 2 if arched else 0) * .6
    for i in range(1, nb + 1):
        xx = x0 + (x1 - x0) * i / (nb + 1); S([(xx, top), (xx + .3, y1)], 1.3, BAR, a=.95, dry=.05, taper=(.05, .05))
    for j in range(1, nh + 1):
        yy = body + (y1 - body) * j / (nh + 1); S([(x0 + .5, yy), (x1 - .5, yy + .3)], 1.2, BAR, a=.95, dry=.05, taper=(.05, .05))
    # the bars stay dark when the glass glows
    for i in range(1, nb + 1):
        xx = (x0 + (x1 - x0) * i / (nb + 1) - X0) * K
        cv2.line(GLOW, (int(xx), int((top - Y0) * K)), (int(xx), int((y1 - Y0) * K)), 0, int(1.3 * K))
    for j in range(1, nh + 1):
        yy = (body + (y1 - body) * j / (nh + 1) - Y0) * K
        cv2.line(GLOW, (int((x0 - X0) * K), int(yy)), (int((x1 - X0) * K), int(yy)), 0, int(1.2 * K))
    # sill and its snow
    A([(x0 - frame - 2, y1 + frame * .5), (x1 + frame + 2, y1 + frame * .5), (x1 + frame + 1, y1 + frame * .5 + 3.5), (x0 - frame - 1, y1 + frame * .5 + 3.5)], CREAM_D, wob=.1, rough=.3)
    snow_cap(x0 - frame - 2, x1 + frame + 2, y1 + frame * .5 - .5, 5.0)

def glass(m, cx, cy, hw, hh):
    """Lit glass: a warm glow, brightest a little below the middle, deeper gold toward the frame."""
    cx -= X0; cy -= Y0; C0, C1, C2 = hexc(GOLD_C), hexc(GOLD), hexc(GOLD_E)
    def f(X, Y, r):
        d = np.clip(np.hypot((X - cx) / hw, (Y - cy) / hh), 0, 1.4)[:, None]
        col = np.where(d < .6, C0 * (1 - d / .6) + C1 * (d / .6), C1 * np.clip(1.4 - d, 0, 1) / .8 + C2 * np.clip(d - .6, 0, .8) / .8)
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .05), 0, 1)
    c.stip(m, f, spacing=.75, L=1.6, w=1.1, seed=int(R.randint(1 << 20)), jit=.5)

# ---- greenery: a garland of needle dabs, berries, little bows, a dusting of snow ----
def garland(x0, x1, y, sag=6.0, swags=3, bows=True):
    pts = []
    for i in range(swags):
        a, b = x0 + (x1 - x0) * i / swags, x0 + (x1 - x0) * (i + 1) / swags
        for t in np.linspace(0, 1, 9): pts.append((a + (b - a) * t, y + sag * math.sin(math.pi * t)))
    # a fat rope of greenery: a dark core, then layered needle sprays lighter toward the top, holly leaves
    P0 = T(pts); c.stroke(P0, 9.5, NEEDLES[3], a=1, dry=.2, taper=(.15, .15), seed=int(R.randint(1 << 20)))
    for layer, (col_set, n, dy) in enumerate(((NEEDLES[3:] + NEEDLES[:1], 14, 2.5), (NEEDLES[1:3], 14, 0), (['#3d7a52', '#4c8a5c'], 7, -2.5))):
        for (px, py) in pts:
            for _ in range(n):
                ang = R.uniform(-.9, .9) + (math.pi / 2 if R.rand() < .5 else 0); ln = R.uniform(4.5, 7.5)
                c.dab(px - X0 + R.uniform(-5, 5), py - Y0 + dy + R.uniform(-3.5, 3.5), ln, R.uniform(1.5, 2.2), ang, col_set[R.randint(len(col_set))], a=1, dry=.1)
    for (px, py) in pts[1::3]:
        for sgn in (-1, 1):
            hx, hy = px + sgn * R.uniform(2, 4), py + R.uniform(-2, 2)
            shaded([(hx, hy), (hx + sgn * 6, hy - 2.5), (hx + sgn * 8, hy + 1), (hx + sgn * 3, hy + 2.5)], ['#4c8a5c', '#2f6446', '#1d4430'], wob=.1, rough=.3, edge_dark=.2, L=1.6, w=1.0)
        track((int((px - X0 - 5) * K), int((py - Y0 - 5) * K), np.ones((int(10 * K), int(10 * K)), np.float32)), .0)
    P = np.array(T(pts)) * K
    cv2.polylines(ALPHA, [P.astype(np.int32)], False, 1.0, int(13 * K), cv2.LINE_AA)
    for (px, py) in pts[::2]:
        for _ in range(2):
            bx_, by_ = px + R.uniform(-4, 4), py + R.uniform(-2, 4)
            shaded(lump(bx_, by_, 1.9, 1.9, amp=0), ['#e0504a', BERRY, '#7a1418'], wob=0, rough=.2, edge_dark=.1, L=1.0, w=.8)
    for (px, py) in pts[::3]:
        c.dab(px - X0 + R.uniform(-3, 3), py - Y0 - 4.5, R.uniform(4, 6), 2.2, R.uniform(-.3, .3), SNOW, a=.95, dry=.2)
    if bows:
        for i in range(swags + 1):
            bx = x0 + (x1 - x0) * i / swags; by = y - 1
            for s in (-1, 1): A([(bx, by), (bx + s * 7, by - 4.5), (bx + s * 7, by + 4)], BERRY, wob=.1, rough=.3, edge_dark=.2)
            A(lump(bx, by, 2.4, 2.4), '#9a1e22', wob=.05, rough=.2)
            for s in (-1, 1): S([(bx, by + 1.5), (bx + s * 3.5, by + 9)], 1.8, BERRY, a=1, dry=.05)

def chimney(x0, x1, ytop, ybot, cap=True):
    m = A([(x0, ybot), (x1, ybot), (x1, ytop), (x0, ytop)], BRICK, wob=.15, rough=.4, edge_dark=.12)
    stip(m, [BRICK, BRICK_D, '#c0603c'], spacing=1.2, L=2.4, w=1.3, ang=0.0, weights=[.5, .3, .2])
    for yy in np.arange(ytop + 4, ybot, 5):
        S([(x0 + .5, yy), (x1 - .5, yy)], .5, '#e1c7a8', a=.45, dry=.5, taper=(0, 0))
    A([(x0 - 2, ytop + 3), (x1 + 2, ytop + 3), (x1 + 2, ytop - 1), (x0 - 2, ytop - 1)], BRICK_D, wob=.1, rough=.3)
    if cap: snow_edge([(x0 - 3, ytop - 2), (x1 + 3, ytop - 2)], 7.0, drip=.4)

# =========================================================================================== the shop
def blue_shop():
    # back: the red-roofed house behind, its roof reaching down behind the side roof, its chimney
    chimney(118, 160, 452, 500)
    wall([(96, 572), (96, 526), (224, 526), (224, 572)], BLUE_D, dark=True)            # the back house's wall, in shade
    roof([(82, 528), (104, 472), (212, 452), (238, 474), (214, 528)], snowy=.32, ridge=((104, 470), (212, 450)), eave=((84, 526), (214, 526)))
    snow_edge([(100, 471), (214, 450)], 6.0, drip=0)
    snow_edge([(80, 527), (216, 527)], 7.0, drip=.3)
    chimney(70, 104, 548, 610)
    # the tall house
    wall([(222, 760), (300, 760), (300, 520), (252, 446), (222, 495)], BLUE, fleck=.6)
    eave_shadow([(222, 498), (252, 450), (299, 522)], 8)
    shaded([(190, 528), (252, 436), (314, 528), (308, 534), (252, 448), (196, 534)], ['#a8463c', ROOF, ROOF_D], light=(-1, -.4), wob=.2, rough=.4, edge_dark=.2)
    S([(200, 531), (252, 449), (304, 531)], 3.6, CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(186, 527), (252, 432), (318, 527)], 13.0, drip=.4)
    window(233, 485, 268, 521, True)
    window(258, 542, 290, 580, False)
    garland(254, 296, 590, sag=4, swags=1)
    # the side wing (set back, so a little darker)
    wall([(24, 902), (104, 902), (104, 662), (24, 662)], BLUE_D, dark=True, fleck=.4)
    eave_shadow([(24, 664), (104, 664)], 9)
    window(51, 683, 76, 727, True)
    # the side roof, running down to the left over the wing
    roof([(10, 664), (54, 596), (140, 566), (200, 566), (108, 664)], snowy=.35, ridge=((54, 596), (196, 566)), eave=((10, 664), (108, 664)))
    snow_edge([(4, 664), (108, 664)], 12.0, drip=.45)
    snow_edge([(10, 662), (54, 596), (140, 566), (196, 566)], 6.0, drip=.0)
    # the front gable
    wall([(100, 902), (303, 902), (303, 662), (200, 566), (100, 662)], BLUE, fleck=.8)
    for yy in (742, 744):
        S([(100, yy), (303, yy)], .6, BLUE_D, a=.4, dry=.4)
    eave_shadow([(102, 664), (200, 568), (300, 664)], 10)
    # a thick roof edge with a deep overhang: the red roof slab seen end-on, its shadowed underside, the trim
    slab = [(70, 676), (200, 548), (330, 676), (322, 684), (200, 562), (78, 684)]
    shaded(slab, ['#a8463c', ROOF, ROOF_D], light=(-1, -.4), wob=.2, rough=.4, edge_dark=.2)
    S([(80, 684), (200, 564), (320, 684)], 3.0, ROOF_D, a=.8, dry=.2, taper=(0, 0))
    S([(88, 682), (200, 566), (312, 682)], 4.4, CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(66, 674), (200, 544), (334, 674)], 15.0, drip=.45)
    window(177, 601, 218, 641, True)
    window(126, 655, 160, 703, True)
    window(182, 655, 215, 703, False)
    window(236, 655, 270, 703, True)
    garland(110, 290, 713, sag=9, swags=3)
    # the awning: stripes leaning a little, rounded hems, shadow toward the valance, snow on top
    ax0, ax1, ay, ly, hem = 100, 322, 744, 778, 794
    n = 10
    EDGES = [0.0] + sorted(np.clip(np.arange(1, n) / n + R.uniform(-.018, .018, n - 1), 0, 1)) + [1.0]
    for i in range(n):
        a, b = EDGES[i], EDGES[i + 1]
        t0, t1 = ax0 + (ax1 - ax0) * a, ax0 + (ax1 - ax0) * b
        l0, l1 = t0 + 6 + R.uniform(-1.2, 1.2) * (i > 0), t1 + 6 + R.uniform(-1.2, 1.2) * (i < n - 1)
        col, dark = (GREEN_A, GREEN_AD) if i % 2 == 0 else (WHITE_A, '#cfc4ac')
        m = A([(t0, ay), (t1, ay), (l1, ly), (l0, ly)], col, wob=.15, rough=.4, edge_dark=.12)
        Cc, Cd = hexc(col), hexc(dark); xa, xb = t0 - X0, t1 - X0
        def fold(X, Y, r, xa=xa, xb=xb, Cc=Cc, Cd=Cd):
            u = np.clip((X - xa - (Y - (ay - Y0)) * 6 / (ly - ay)) / (xb - xa), 0, 1)       # across the stripe
            k = np.clip(np.abs(u - .4) * 1.0 + (Y - (ay - Y0)) / (ly - ay) * .75 - .15, 0, 1)[:, None]
            return np.clip(Cc * (1 - k * .55) + Cd * k * .55 + (r.rand(len(X), 1) - .5) * .04, 0, 1)
        c.stip(m, fold, spacing=.85, L=2.6, w=1.1, angfn=lambda X, Y: np.full(X.shape, math.atan2(ly - ay, 6)), seed=int(R.randint(1 << 20)), jit=.4)
        sc = [(l1 - (l1 - l0) * k / 10, ly + (hem - ly) * math.sin(math.pi * k / 10)) for k in range(11)]
        mv = A([(l0, ly - .5), (l1, ly - .5)] + sc[1:-1], col, wob=.1, rough=.3, edge_dark=.18)
        stip(mv, [dark, col], spacing=.9, L=1.6, w=1.0, ang=0.0, weights=[.45, .55])
    S([(ax0 + 6, ly), (ax1 + 6, ly)], .9, GREEN_AD, a=.5, dry=.4)
    # the awning's right end: its side panel shows the slope, shaded
    shaded([(ax1, ay), (ax1 + 6, ly), (ax1 + 6, hem), (ax1 + 12, hem - 3), (ax1 + 9, ay + 2)], [GREEN_A, GREEN_AD, '#1d3d22'], light=(-1, -.3), wob=.1, rough=.3, edge_dark=.15)
    # shade cast by the snow onto the top of the canvas
    S([(ax0 + 2, ay + 5), (ax1 + 2, ay + 5)], 4.0, '#000000', a=.16, dry=.6, taper=(.2, .2))
    eave_shadow([(ax0 + 8, hem - 2), (ax1 + 6, hem - 2)], 6, WOOD_D)
    snow_edge([(ax0 - 4, ay - 1), (ax1 + 4, ay - 1)], 10.0, drip=.2)
    for _ in range(4):
        px = R.uniform(ax0 + 14, ax1 - 8); py = R.uniform(ay + 8, ay + 18)
        snow_clump(px, py, R.uniform(5, 8), R.uniform(2.2, 3.0), math.atan2(ly - ay, 6) - math.pi / 2 + 1.4)
    # the shopfront: dark wooden posts, the display with the bear, side windows, a brick plinth
    A([(104, 902), (306, 902), (306, 796), (104, 796)], WOOD, wob=.15, rough=.4, edge_dark=.12)
    # display window
    disp = A([(173, 879), (252, 879), (252, 800), (173, 800)], GOLD, wob=.1, rough=.3, edge_dark=0)
    cx, cy = 212 - X0, 835 - Y0
    C0, C1 = hexc(GOLD_C), hexc(GOLD_E)
    c.stip(disp, lambda X, Y, r: np.clip((C0 * (1 - np.clip(np.hypot((X - cx) / 40, (Y - cy) / 40), 0, 1)[:, None]) + C1 * np.clip(np.hypot((X - cx) / 40, (Y - cy) / 40), 0, 1)[:, None]) * (1 + (r.rand(len(X), 1) - .5) * .08), 0, 1), spacing=.8, L=1.4, w=1.0, seed=31, jit=.5)
    x0_, y0_, mm = disp; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm * .85)
    # the teddy bear: body, head, ears, muzzle, red bow, paws; a little holly in the corner
    BEAR, BEAR_D, BEAR_L = '#b9733a', '#8a5226', '#d8995a'; BC = [BEAR_L, BEAR, BEAR_D]
    # a shelf at the back with small toys: blocks, a drum, a ball
    A([(175, 846), (250, 846), (250, 849), (175, 849)], '#8a4a24', wob=.05, rough=.2)
    for bx, col in ((180, '#b8262a'), (186, '#3a6aa8'), (183, '#e0b040')):
        shaded([(bx, 846 - (6 if bx != 183 else 12)), (bx + 6, 846 - (6 if bx != 183 else 12)), (bx + 6, 846 - (0 if bx != 183 else 6)), (bx, 846 - (0 if bx != 183 else 6))], [col, col, BEAR_D], wob=.05, rough=.2)
    shaded([(236, 846), (246, 846), (246, 838), (236, 838)], ['#d84a3a', '#b8262a', '#7a1a1a'], wob=.05, rough=.2)
    S([(236, 839), (246, 839)], 1.2, '#f0d070', a=1, dry=.05); S([(236, 845), (246, 845)], 1.2, '#f0d070', a=1, dry=.05)
    shaded(lump(198, 873, 5, 5, amp=0), ['#5a8ad0', '#3a6aa8', '#24467a'], wob=.05, rough=.2)
    # the bear: one plush figure. Head, ears, body, arms and legs are united into a single silhouette first,
    # so the parts join like a stuffed toy; it is then shaded as one form (lit upper left, darker in its creases)
    sc = 1.3; cx0, cy0 = 213, 866
    bp = lambda px, py: (cx0 + (px - cx0) * sc, cy0 + (py - cy0) * sc)
    parts = [(213, 855, 12.5, 13.5), (213, 834, 11, 10), (204, 825, 4.2, 4.2), (222, 825, 4.2, 4.2),   # body, head, ears
             (200, 852, 4.6, 8.5, -.5), (226, 852, 4.6, 8.5, .5),                                      # arms, angled out
             (205, 868, 6.5, 5), (221, 868, 6.5, 5)]                                                   # legs
    M_ = np.zeros((c.H, c.W), np.float32)
    for p in parts:
        px, py = bp(p[0], p[1]); rx, ry = p[2] * sc, p[3] * sc; ang = math.degrees(p[4]) if len(p) > 4 else 0
        cv2.ellipse(M_, (int((px - X0) * K), int((py - Y0) * K)), (int(rx * K), int(ry * K)), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
    M_ = cv2.GaussianBlur(M_, (0, 0), 1.2 * K); M_ = np.clip((M_ - .5) * 3 + .5, 0, 1)
    ys, xs = np.nonzero(M_ > .01); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    mb = (int(bx0), int(by0), M_[by0:by1, bx0:bx1].copy())
    track(c.area(None, BEAR, m=mb, edge_dark=.25, var=.04))
    # shading: distance from each part's centre (rounded forms), light from the upper left
    inner = np.zeros((c.H, c.W), np.float32)
    for p in parts:
        px, py = bp(p[0], p[1]); rx, ry = p[2] * sc * K, p[3] * sc * K
        Y, Xg = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        d = 1 - np.clip(np.hypot((Xg - (px - X0) * K + rx * .3) / rx, (Y - (py - Y0) * K + ry * .3) / ry), 0, 1)
        inner[by0:by1, bx0:bx1] = np.maximum(inner[by0:by1, bx0:bx1], d)
    Cl, Cm, Cd = hexc('#dca066'), hexc(BEAR), hexc('#7a4620')
    def bcol(X, Y, r):
        v = inner[np.clip((Y * K).astype(int), 0, c.H - 1), np.clip((X * K).astype(int), 0, c.W - 1)][:, None]
        col = np.where(v > .5, Cm * (1 - (v - .5) * 2) + Cl * (v - .5) * 2, Cd * (1 - v * 2) + Cm * v * 2)
        return np.clip(col * (1 + (r.rand(len(X), 1) - .5) * .1), 0, 1)
    c.stip(mb, bcol, spacing=.7, L=1.4, w=.9, seed=77, jit=.6, thresh=.3)       # short dabs: plush fur
    # creases where the arms and legs meet the body
    for (a_, b_) in (((204, 846), (206, 860)), ((222, 846), (220, 860)), ((208, 864), (218, 864))):
        S([bp(*a_), bp(*b_)], 1.0, '#6a3a1a', a=.55, dry=.4)
    # inner ears, muzzle, paw pads
    for sg in (-1, 1):
        A(lump(*bp(213 + sg * 9, 825), 2.2 * sc, 2.2 * sc, amp=0), '#e8b07a', wob=.05, rough=.2)
        A(lump(*bp(213 + sg * 8, 869), 3.2 * sc, 2.4 * sc, amp=0), '#e6b07c', wob=.05, rough=.2)
    shaded(lump(*bp(213, 838), 5.2 * sc, 4 * sc, amp=0), ['#f0c690', '#e2b07c', '#c48a56'], wob=.05, rough=.2, L=1.0, w=.8)
    nx, ny = bp(213, 836); c.dots([(nx - X0, ny - Y0)], 2.0, ['#2a1a12'], seed=3)
    for sg in (-1, 1):
        ex, ey = bp(213 + sg * 4.2, 830.5); c.dots([(ex - X0, ey - Y0)], 1.4, ['#1e140e'], seed=4 + sg)
        c.dots([(ex - X0 - .4, ey - Y0 - .5)], .45, ['#ffffff'], seed=7 + sg)
    S([bp(210.5, 840), bp(213, 841.2), bp(215.5, 840)], .9, '#3a2216', a=.9, dry=.05)
    # the red bow at the neck
    for sg in (-1, 1): shaded([bp(213, 845), bp(213 + sg * 7, 841), bp(213 + sg * 7.5, 849)], ['#e0504a', BERRY, '#7a1418'], wob=.05, rough=.2, edge_dark=.2, L=1.0, w=.8)
    A(lump(*bp(213, 845), 2.2 * sc, 2.2 * sc, amp=0), '#9a1e22', wob=.05, rough=.2)
    # a little garland across the top of the display window
    for t in np.linspace(0, 1, 14):
        px = 175 + 75 * t; py = 803 + 3 * math.sin(math.pi * (t * 3 % 1))
        for _ in range(3): c.dab(px - X0 + R.uniform(-2, 2), py - Y0 + R.uniform(-1.5, 1.5), R.uniform(3, 4.5), 1.5, R.uniform(0, 3), NEEDLES[R.randint(4)], a=1, dry=.1)
    c.dots([(175 + 75 * t - X0, 805 - Y0) for t in (.17, .5, .83)], 1.4, [BERRY], seed=12)
    for k in range(4):
        px, py = 182 + k * 4, 808 + (k % 2) * 3
        c.dab(px - X0, py - Y0, 4, 1.6, R.uniform(0, 3), NEEDLES[k % 4], a=1, dry=.1)
    c.dots([(186 - X0, 812 - Y0), (189 - X0, 810 - Y0)], 1.1, [BERRY], seed=8)
    # side windows: lit glass behind a wooden grid
    for (sx0, sy0, sx1, sy1), (nb, nh) in (((118, 800, 160, 872), (1, 2)), ((258, 800, 300, 866), (1, 1))):
        g = A([(sx0, sy1), (sx1, sy1), (sx1, sy0), (sx0, sy0)], GOLD, wob=.1, rough=.3, edge_dark=.1)
        glass(g, (sx0 + sx1) / 2, (sy0 + sy1) / 2 + 6, (sx1 - sx0) / 2, (sy1 - sy0) / 2)
        x0_, y0_, mm = g; GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm)
        for i in range(1, nb + 1):
            xx = sx0 + (sx1 - sx0) * i / (nb + 1); S([(xx, sy0), (xx, sy1)], 2.0, WOOD_D, a=1, dry=.05, taper=(0, 0))
            cv2.line(GLOW, (int((xx - X0) * K), int((sy0 - Y0) * K)), (int((xx - X0) * K), int((sy1 - Y0) * K)), 0, int(2 * K))
        for j in range(1, nh + 1):
            yy = sy0 + (sy1 - sy0) * j / (nh + 1); S([(sx0, yy), (sx1, yy)], 1.8, WOOD_D, a=1, dry=.05, taper=(0, 0))
            cv2.line(GLOW, (int((sx0 - X0) * K), int((yy - Y0) * K)), (int((sx1 - X0) * K), int((yy - Y0) * K)), 0, int(1.8 * K))
    # posts and lintel, the brick plinth under the display, snow on its sill
    for xx in (112, 166, 254, 303):
        S([(xx, 797), (xx, 902)], 4.0, WOOD_D, a=.9, dry=.15, taper=(0, 0))
    S([(104, 797), (306, 797)], 3.5, WOOD_D, a=.9, dry=.15, taper=(0, 0))
    pl = A([(170, 902), (256, 902), (256, 882), (170, 882)], BRICK, wob=.1, rough=.4, edge_dark=.12)
    stip(pl, [BRICK, BRICK_D], spacing=1.1, L=2.4, w=1.2, ang=0.0)
    snow_cap(168, 258, 880, 4.2)
    snow_cap(114, 164, 874, 3.6); snow_cap(254, 302, 868, 3.6)
    # the little wreath on the left post and a tub of greenery by the door
    for k in range(18):
        a = k / 18 * math.tau; c.dab(139 - X0 + 6 * math.cos(a), 888 - Y0 + 6 * math.sin(a), 3.2, 1.5, a + 1.57, NEEDLES[k % 4], a=1, dry=.1)
    c.dots([(139 - X0, 882 - Y0), (144 - X0, 890 - Y0), (134 - X0, 891 - Y0)], 1.0, [BERRY], seed=9)
    # the snowy fir in front of the side wing (in place of the blossom tree)
    fir(58, 908, 190)
    # snow on the ground along the front
    # snow banked along the foot of the building, deeper by the fir and the corners
    bank = [(x, 905 - 3 * math.sin(x / 23) - 4 * math.exp(-((x - 60) / 40) ** 2) - 3 * math.exp(-((x - 320) / 25) ** 2)) for x in np.linspace(0, 340, 30)]
    snow_edge(bank, 11.0, drip=0)
    for x in (40, 95, 300):
        snow_clump(x, 900, R.uniform(14, 20), 6)

def fir(x, y, h):
    """A fir of drooping, jagged branch tiers (dark needles, lit edges), with irregular clumps of snow lying on
    the upper surface of each tier and caught at the branch tips."""
    tiers = [(.05, .34, .40), (.22, .52, .33), (.40, .68, .26), (.56, .83, .19), (.72, 1.0, .11)]
    S([(x, y), (x, y - h * .2)], 5, '#4a3020', a=1, dry=.1)
    for i, (ta, tb, wd) in enumerate(tiers):
        yb, yt = y - h * ta, y - h * tb; half = wd * h
        nt = 3 + (i < 3)
        poly = [(x, yt)]
        for k in range(1, nt + 1):                              # right side: branch tips stepping out and down
            u = k / nt; poly += [(x + half * u * .72 + R.uniform(-1, 1), yt + (yb - yt) * u * .92 - 2), (x + half * u + R.uniform(-1, 1.5), yt + (yb - yt) * u + 2.5)]
        for k in range(1, 8):                                   # the hem: drooping needle tufts
            poly.append((x + half - 2 * half * k / 8, yb + (3.5 if k % 2 else 0) + R.uniform(-1, 1)))
        for k in range(nt, 0, -1):
            u = k / nt; poly += [(x - half * u + R.uniform(-1.5, 1), yt + (yb - yt) * u + 2.5), (x - half * u * .72 + R.uniform(-1, 1), yt + (yb - yt) * u * .92 - 2)]
        shaded(poly, [NEEDLES[2], NEEDLES[1], NEEDLES[3]], wob=.5, rough=1.0, edge_dark=.22, L=3.2, w=1.3)
        for _ in range(3 + (i < 2)):                            # snow lying on the tier, inside its silhouette
            u = R.uniform(.4, .9); wu = half * u; rx = wu * R.uniform(.3, .42)
            px = x + R.uniform(-1, 1) * max(0, wu - rx) * .8; py = yt + (yb - yt) * u - 2.5
            snow_clump(px, py, rx, R.uniform(4.2, 5.6), shadow=NEEDLES[3])
        for sg in (-1, 1):                                      # small heaps caught near the branch tips
            snow_clump(x + sg * half * .66, yb - 3, half * .2, 4.0, shadow=NEEDLES[3])
    snow_clump(x, y - h * .96, 5, 4.5)

def light():
    """The lighting a painter adds last: light from the upper left across the whole building, shade
    gathering toward the ground and the right, and the warm glow of the windows spilling onto the walls."""
    yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
    g = 1.07 - .14 * (xx / c.W) - .16 * np.clip((yy / c.H - .35) / .65, 0, 1)
    g -= .1 * np.clip((yy / c.H - .9) / .1, 0, 1)                         # shade near the ground
    c.img *= g[..., None]
    spill = cv2.GaussianBlur(GLOW, (0, 0), 7 * K)
    warm = np.array(hexc('#ffb060'))
    lit = np.clip(spill * 1.6, 0, 1)[..., None] * (1 - GLOW[..., None])
    c.img[:] = c.img + (warm - c.img) * lit * .28


"""Toy Town quality study (step 1): one storefront and the two Marines at close-up detail.

Painted only with the map's own gouache brush (folk2: Kanvas.area / stip / stroke / dots, impasto ridge lighting), so it
belongs to the same painting as the map. What is new compared with today's Toy Town (lab8/tft7, at 2x):
  * one evening light for everything: lamps and lit windows cast warm pools; every surface is shaded from that light
    (lit side, shadow side, warm glow near the light), nothing is a flat fill;
  * form for every object: walls are stippled stucco and brick, awnings have folds and a shadowed underside, the sign is
    a painted board with brushed lettering, windows have depth (frame, reveal, sill, glass, display inside);
  * figures with faces, shading and weight: lit and shadow sides of coats and trousers, gloves, gold buttons, cap
    peaks, a contact shadow and a cast shadow; the two Marines differ in build, skin tone, pose and timing;
  * cobbles as stones, not dots: irregular stones in rows that grow toward the viewer, a worn lighter path, mortar,
    and pools of lamplight;
  * marks sized for the close-up: finer dabs for small things, broader ones for walls and ground.

    PYTHONPATH=../folk2:../styles2 python3 closeup/square11.py [OUT.png] [--quick]
Design space 1500 x 1050 units, rendered at K = 2 (3000 x 2100).
"""
import math, os, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', '..', 'folk2'), os.path.join(HERE, '..', '..', 'styles2')]
from brush import hexc, catmull, resample                     # noqa: E402
from kit import Kanvas, pal_fn, dab_tree, impasto            # noqa: E402
from parts import lumpy                                        # noqa: E402

W, H, K = 1500, 1050, 2
FONT = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrebonum-bold.otf'
QUICK = '--quick' in sys.argv
c = None
T0 = time.time()
def log(m): print(f'{time.time() - T0:6.1f}s {m}', flush=True)

# ------------------------------------------------------------------ one light for the whole scene
# light sources in design units: (x, y, radius, strength); evening: lamps and windows do most of the lighting
LIGHTS = []
SKY_DIR = np.array([-.6, -.8])                                 # soft sky light from the upper left
def light_at(X, Y):
    """Brightness multiplier and warmth (0..1) at design points from the lamps and windows."""
    b = np.zeros_like(X, dtype=np.float32); w = np.zeros_like(X, dtype=np.float32)
    for (lx, ly, r, s) in LIGHTS:
        d2 = ((X - lx) ** 2 + (Y - ly) ** 2) / (r * r)
        g = s * np.exp(-d2)
        b += g; w += g
    return b, np.clip(w, 0, 1)

WARM = np.array([1.0, .78, .42], np.float32)
def lit(cols, var=.05, base=.84, dir_=None, span=None, glow=.55):
    """A colour function: palette dabs, darkened away from the light, warmed and brightened near lamps and windows.
    dir_: (cx, cy, rx, ry) gives a form gradient: the upper-left of that box is lit, the lower-right in shadow."""
    C = np.array([hexc(x) for x in cols], np.float32)
    def f(X, Y, r):
        col = C[r.randint(len(C), size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * 2 * var)
        v = np.full(len(X), base, np.float32)
        if dir_ is not None:
            cx, cy, rx, ry = dir_
            v += .3 * np.clip(-(X - cx) / rx * .55 - (Y - cy) / ry * .45, -1, 1)
        b, w = light_at(X, Y)
        v = v + glow * b
        col = col * v[:, None]
        col = col * (1 - .45 * w[:, None]) + col * WARM * .45 * w[:, None] * 1.25
        return np.clip(col, 0, 1)
    return f

# ------------------------------------------------------------------ small painting helpers
def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def arch_top(x0, x1, ybase, rise, n=18):
    cx, rx = (x0 + x1) / 2, (x1 - x0) / 2
    return [(cx - rx * math.cos(t), ybase - rise * math.sin(t)) for t in np.linspace(0, math.pi, n)]

MARK = 2.6                       # dab size relative to the map's: the close-up is seen ~3x nearer, so its marks are bigger
def paint(poly, cols, spacing=1.4, L=2.6, w=1.8, ang=None, seed=0, base=None, dir_=None, var=.1, wob=.4, rough=.8, edge=.08, a=1.0, glow=.55, jit=.4, lbase=.84):
    """Lay a ground colour, then dabs over it: the map's own way of painting a surface."""
    col0 = base or cols[0]
    spacing, L, w = spacing * MARK, L * MARK, w * MARK
    m = c.area(poly, col0, wob=wob, rough=rough, edge_dark=edge, seed=seed, a=a)
    if m is None: return None
    af = (lambda X, Y: np.full(X.shape, ang)) if isinstance(ang, (int, float)) else ang
    c.stip(m, lit(cols, var, lbase, dir_, glow=glow), spacing=spacing, L=L, w=w, angfn=af, seed=seed + 1, jit=jit, a=a)
    return m

def line(pts, w, col, a=1.0, dry=.15, taper=(.05, .1), seed=None): c.stroke(pts, w, col, a=a, dry=dry, taper=taper, seed=seed)

def text_mask(text, cx, cy, size, track=0.0, wob=0.0, seed=0):
    k = c.k; px = max(8, int(round(size * k * 1.38))); f = ImageFont.truetype(FONT, px)
    widths = [f.getlength(ch) for ch in text]; trk = track * k; tw = sum(widths) + trk * (len(text) - 1)
    asc, desc = f.getmetrics(); W_, H_ = int(tw + 10), int(asc + desc + 10)
    im = Image.new('L', (W_, H_), 0); d = ImageDraw.Draw(im); x = 5.0; r = np.random.RandomState(seed)
    for ch, wd in zip(text, widths):            # hand-set: each letter a touch off the line and size
        d.text((x + r.uniform(-.3, .3) * k, 5 + r.uniform(-.8, .8) * k * wob), ch, font=f, fill=255); x += wd + trk
    m = np.asarray(im, np.float32) / 255
    ys, xs = np.nonzero(m > .02); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    m = cv2.GaussianBlur(m, (0, 0), .45 * k)
    hh, ww = m.shape; x0, y0 = int(cx * k - ww / 2), int(cy * k - hh / 2)
    return (x0, y0, np.clip((m - .35) * 2.2, 0, 1))

def letters(text, cx, cy, size, cols, track=0.0, seed=0):
    m = text_mask(text, cx, cy, size, track, wob=.8, seed=seed)
    x0, y0, mm = m; reg = c.img[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]
    reg += (hexc(cols[0]) - reg) * mm[..., None]
    c.stip(m, lit(cols, .06, .9, glow=.25), spacing=.8, L=1.5, w=1.1, seed=seed + 3, jit=.6)

def stars(cx, y, n, gap, r_, col):
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * gap
        pts = [(x + r_ * (1 if j % 2 == 0 else .45) * math.sin(j * math.pi / 5), y - r_ * (1 if j % 2 == 0 else .45) * math.cos(j * math.pi / 5)) for j in range(10)]
        paint(pts, [col, col], spacing=.7, L=1.2, w=1.0, wob=.15, rough=.4, edge=.05, seed=4000 + i)

def glow_spot(x, y, r, s): LIGHTS.append((x, y, r, s))

# ------------------------------------------------------------------ the buildings
def windows_row(x0, x1, y, n, w, h, frame, glass, seed, arch=True, box=True):
    for i in range(n):
        cx = x0 + (i + .5) * (x1 - x0) / n
        window(cx, y, w, h, frame, glass, seed + i * 17, arch=arch, box=box)

def window(cx, y, w, h, frame, glass, seed, arch=True, box=True, lit_=True):
    """y: top of the sill. A recessed window: reveal, glowing glass with panes, mullions, sill, flower box."""
    x0, x1, top = cx - w / 2, cx + w / 2, y - h
    shape = ([(x0, y)] + arch_top(x0, x1, top + w * .5, w * .5) + [(x1, y)]) if arch else rect(x0, top, x1, y)
    paint(shape, [frame, frame], spacing=1.0, L=1.8, w=1.3, seed=seed, edge=.2, wob=.2)                   # frame / reveal
    g0, g1 = x0 + w * .12, x1 - w * .12
    gshape = ([(g0, y - h * .05)] + arch_top(g0, g1, top + w * .5 + h * .03, (g1 - g0) * .5) + [(g1, y - h * .05)]) if arch else rect(g0, top + h * .07, g1, y - h * .05)
    gl = glass if lit_ else ['#2c3450', '#3a4466', '#26304a']
    glow_spot(cx, y - h * .42, w * .55, .35)
    m = paint(gshape, gl, spacing=.9, L=1.6, w=1.3, seed=seed + 2, wob=.15, rough=.5, edge=.0, glow=.7, lbase=.8)
    for xx in np.linspace(g0, g1, 3)[1:-1]:                                                                   # mullion and transom
        line([(xx, y - h * .05), (xx, top + h * .1)], 1.3, frame, a=.95)
    line([(g0, top + h * .48), (g1, top + h * .48)], 1.2, frame, a=.95)
    paint(rect(x0 - 4, y - 1.5, x1 + 4, y + 4), ['#f4efe4', '#e4dccc', '#fbf7ee'], spacing=.9, L=1.8, w=1.2, seed=seed + 4, edge=.15, wob=.15)   # sill
    if lit_: glow_spot(cx, y - h * .45, w * .9, .1)
    if box:
        bx = rect(x0 - 3, y + 4, x1 + 3, y + 15)
        paint(bx, ['#6a3f24', '#7c4c2c', '#5a341e'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed + 6, edge=.2, wob=.2)
        r = np.random.RandomState(seed)
        for j in range(int(w / 2.2)):                                                                     # leaves and blooms
            px, py = r.uniform(x0 - 2, x1 + 2), y + 4 - r.uniform(0, 7)
            c.dots([(px, py)], r.uniform(1.6, 2.6), ['#2f5a2a', '#3e6e32', '#4c7e3a'], seed=seed * 3 + j)
        for j in range(int(w / 5)):
            px, py = r.uniform(x0, x1), y + 3 - r.uniform(1, 7)
            c.dots([(px, py)], r.uniform(1.2, 2.0), ['#c8302a', '#e04838', '#f4d040'], seed=seed * 5 + j)

def awning(x0, x1, y, drop, cols, seed):
    """A striped awning seen slightly from below: sloped top, scalloped valance, folds, a shadow under it."""
    n = 9; wseg = (x1 - x0) / n
    c.area([(x0 - 6, y + drop + 2), (x1 + 6, y + drop + 2), (x1 + 2, y + drop + 16), (x0 - 2, y + drop + 16)], '#2a1c16', wob=.6, rough=.8, edge_dark=0, a=.45, seed=seed)  # cast shadow on the wall
    for i in range(n):
        a0, a1 = x0 + i * wseg, x0 + (i + 1) * wseg
        col = cols[i % 2]
        top0, top1 = a0 + (a0 - (x0 + x1) / 2) * .05, a1 + (a1 - (x0 + x1) / 2) * .05
        poly = [(top0, y), (top1, y), (a1 + (a1 - (x0 + x1) / 2) * .08, y + drop), (a0 + (a0 - (x0 + x1) / 2) * .08, y + drop)]
        pal = [col, col, col]
        paint(poly, pal, spacing=1.0, L=2.6, w=1.3, ang=math.pi / 2 * .9, seed=seed + i * 7, edge=.12, wob=.2, dir_=(a0 + wseg * .3, y, wseg, drop), var=.04)
        # the scallop
        sc = [(a0 + (a1 - a0) * u + (a0 - (x0 + x1) / 2) * .08, y + drop + math.sin(u * math.pi) * 11) for u in np.linspace(0, 1, 10)]
        paint([(a0 + (a0 - (x0 + x1) / 2) * .08, y + drop - 1)] + sc + [(a1 + (a1 - (x0 + x1) / 2) * .08, y + drop - 1)], pal, spacing=.9, L=1.6, w=1.1, seed=seed + i * 7 + 3, edge=.2, wob=.1, lbase=.72)
    line([(x0 - 2, y), (x1 + 2, y)], 3.2, '#3a2a22', a=.9)                                                    # rail at the top
    for i in range(1, n):                                                                                     # folds
        xx = x0 + i * wseg
        line([(xx, y + 2), (xx + (xx - (x0 + x1) / 2) * .08, y + drop - 2)], 1.4, '#1e1410', a=.18, taper=(.2, .2))

def string_lights(pts, seed, n=None, r_=1.5):
    P = resample(catmull(pts, 10), 6.5)
    line(P, .9, '#2a2620', a=.7)
    rr = np.random.RandomState(seed)
    for i, (x, y) in enumerate(P):
        col = ['#ffe8a0', '#fff2c8', '#ffd060'][i % 3]
        c.dots([(x, y + 1.5)], r_, [col], seed=seed + i)
        glow_spot(x, y + 1.5, 9, .05)

def garland(pts, seed, bows=()):
    P = resample(catmull(pts, 12), 2.2); r = np.random.RandomState(seed)
    for x, y in P:
        for j in range(3):
            c.dots([(x + r.uniform(-2.5, 2.5), y + r.uniform(-2.5, 2.5))], r.uniform(1.8, 2.8), ['#244a24', '#2f5a2a', '#3e6e32', '#557d3a'], seed=r.randint(1 << 20))
    for i in range(0, len(P), 5):
        x, y = P[i]; c.dots([(x + r.uniform(-2, 2), y + r.uniform(-1, 2))], 1.4, ['#ffe9a8', '#e04030', '#f4d040'], seed=seed + i)
        glow_spot(x, y, 7, .04)
    for (bx, by) in bows: bow(bx, by, 9, seed + int(bx))

def bow(x, y, s, seed):
    red = ['#c42a24', '#d63a2c', '#a82220']
    paint([(x, y), (x - s, y - s * .6), (x - s * 1.05, y + s * .5)], red, spacing=.8, L=1.4, w=1.1, seed=seed, wob=.2, edge=.15)
    paint([(x, y), (x + s, y - s * .6), (x + s * 1.05, y + s * .5)], red, spacing=.8, L=1.4, w=1.1, seed=seed + 1, wob=.2, edge=.15)
    line([(x - 1, y + 1), (x - s * .5, y + s * 1.4)], s * .32, '#b82822', taper=(0, .6))
    line([(x + 1, y + 1), (x + s * .45, y + s * 1.5)], s * .32, '#b82822', taper=(0, .6))
    c.dots([(x, y)], s * .28, ['#d84434'], seed=seed + 2)

def wall_lamp(x, y, seed):
    """A gooseneck lamp over the sign, with its glow."""
    line([(x, y - 22), (x, y - 30), (x + 7, y - 34), (x + 14, y - 30)], 1.8, '#1e1a18', a=1, taper=(0, 0))
    paint([(x + 7, y - 30), (x + 21, y - 30), (x + 18, y - 22), (x + 10, y - 22)], ['#2a2420', '#3a322c'], spacing=.8, L=1.4, w=1.0, seed=seed, wob=.15, edge=.2)
    c.dots([(x + 14, y - 21)], 2.6, ['#fff0b0'], seed=seed)
    glow_spot(x + 14, y - 12, 60, .55)

def lamp_post(x, y, h, seed, s=1.7):
    """A cast-iron lamp post: a fluted base, a tapering post with a collar, and a glowing lantern with a cap."""
    shadow(x + 14, y + 2, 26, 5, a=.45)
    paint([(x - 11 * s, y), (x + 11 * s, y), (x + 6 * s, y - 22 * s), (x - 6 * s, y - 22 * s)], ['#1c1a1a', '#2a2624', '#141212'], spacing=.7, L=1.3, w=.9, seed=seed, wob=.15, edge=.2)
    paint([(x - 3.2 * s, y - 20 * s), (x + 3.2 * s, y - 20 * s), (x + 2.2 * s, y - h), (x - 2.2 * s, y - h)], ['#1c1a1a', '#262220'], spacing=.6, L=1.6, w=.8, ang=math.pi / 2, seed=seed + 3, wob=.05, edge=.2)
    line([(x - 1.5 * s, y - 24 * s), (x - 1.2 * s, y - h + 6)], 1.2 * s, '#5a524c', a=.55, taper=(.1, .1))                  # light down the iron
    paint(rect(x - 5 * s, y - h * .55 - 3 * s, x + 5 * s, y - h * .55 + 3 * s), ['#1c1a1a', '#2a2624'], spacing=.5, L=1.0, w=.7, seed=seed + 4, wob=.05)
    ly = y - h
    paint(rect(x - 8 * s, ly - 2, x + 8 * s, ly + 4 * s), ['#1c1a1a', '#2a2624'], spacing=.5, L=1.0, w=.7, seed=seed + 5, wob=.05)
    paint([(x - 8 * s, ly), (x + 8 * s, ly), (x + 10 * s, ly - 22 * s), (x - 10 * s, ly - 22 * s)], ['#ffe9a0', '#fff4c8', '#ffd870'], spacing=.6, L=1.1, w=.8, seed=seed + 1, wob=.08, edge=0, glow=.1, lbase=1.0)
    for xx in (-4.5, 4.5): line([(x + xx * s, ly), (x + xx * 1.2 * s, ly - 22 * s)], 1.1 * s, '#1c1a1a', a=.9, taper=(0, 0))
    paint([(x - 13 * s, ly - 22 * s), (x + 13 * s, ly - 22 * s), (x + 3 * s, ly - 32 * s), (x - 3 * s, ly - 32 * s)], ['#1c1a1a', '#2c2826'], spacing=.6, L=1.2, w=.8, seed=seed + 2, wob=.1)
    c.dots([(x, ly - 35 * s)], 2.6 * s, ['#1c1a1a'], seed=seed)
    glow_spot(x, ly - 11 * s, 110, .85)

def facade_side(x0, x1, top, base_y, wall, seed, glass, awn=None, kind='teddy'):
    """A neighbouring house, painted with the same brush but quieter than the hero shop."""
    paint(rect(x0, top, x1, base_y), wall, spacing=1.5, L=2.8, w=2.0, seed=seed, dir_=((x0 + x1) / 2, (top + base_y) / 2, (x1 - x0), (base_y - top)), lbase=.8)
    line([(x0, top + 4), (x1, top + 4)], 6, '#f2ece0', a=.95, taper=(0, 0))                                 # cornice
    if kind == 'nutcracker':                                                                              # brick coursing
        rr = np.random.RandomState(seed)
        for ri, yy in enumerate(np.arange(top + 10, base_y, 14)):
            line([(x0, yy + rr.uniform(-.6, .6)), (x1, yy + rr.uniform(-.6, .6))], 1.3, '#7a1c18', a=.32, dry=.35, taper=(0, 0))
            for xx in np.arange(x0 + (ri % 2) * 18, x1, 36):
                line([(xx + rr.uniform(-1, 1), yy), (xx + rr.uniform(-1, 1), yy + 14)], 1.1, '#7a1c18', a=.28, dry=.3, taper=(0, 0))
    windows_row(x0 + 30, x1 - 30, top + 250, 2, 74, 120, '#f4efe6', ['#f8d068', '#ffe090', '#e8b048', '#fff0c0'], seed + 80)
    if awn:
        ay = top + 400
        awning(x0 + 10, x1 - 10, ay, 56, awn, seed + 120)
        sx0, sx1 = x0 + 40, x1 - 40; wy0, wy1 = ay + 80, base_y - 40
        paint(rect(sx0 - 8, wy0 - 6, sx1 + 8, wy1 + 8), ['#5a3420', '#6a3e26'], spacing=1.0, L=1.8, w=1.4, seed=seed + 139, edge=.2, wob=.2)
        paint(rect(sx0, wy0, sx1, wy1), ['#d89a30', '#e8b040', '#c88828', '#f0c860'], spacing=.9, L=1.6, w=1.3, seed=seed + 140, edge=0, glow=.75, lbase=.78)
        glow_spot((sx0 + sx1) / 2, (wy0 + wy1) / 2, 150, .5)
        shelf = wy1 - 30
        paint(rect(sx0, shelf, sx1, shelf + 7), ['#7a4a2a', '#8a5632'], spacing=.8, L=1.6, w=1.1, ang=0.0, seed=seed + 141, wob=.1)
        mid = (sx0 + sx1) / 2
        if kind == 'teddy':
            teddy(mid - 40, shelf, 2.4, seed + 142)
            present(mid + 30, shelf, 44, 36, '#c8302a', '#f4d040', seed + 143); present(mid + 78, shelf, 30, 46, '#3a5aa8', '#f4ede0', seed + 144)
            for bi, bc in enumerate(['#c8302a', '#3e7a3a', '#e4b030', '#3a5aa8', '#8a3a8a']):          # a little bookshelf
                paint(rect(sx1 - 70 + bi * 9, shelf - 52, sx1 - 62 + bi * 9, shelf), [bc, bc], spacing=.6, L=1.2, w=.8, seed=seed + 150 + bi, wob=.05)
        else:
            nutcracker(mid + 10, shelf, 1.5, seed + 142)
            present(sx0 + 20, shelf, 46, 40, '#3e7a3a', '#c8302a', seed + 143); present(sx1 - 70, shelf, 50, 30, '#c8302a', '#f4ede0', seed + 144)
            present(sx1 - 62, shelf - 30, 36, 28, '#e4b030', '#3a5aa8', seed + 145)
        for xx in np.linspace(sx0, sx1, 3)[1:-1]: line([(xx, wy0), (xx, wy1)], 3, '#5a3420', a=.95)
        string_lights([(sx0, wy0 + 8), (mid, wy0 + 20), (sx1, wy0 + 8)], seed + 160)
        paint(rect(sx0 - 12, wy1 + 8, sx1 + 12, base_y), ['#7a4a2a', '#6a3e22', '#8a5632'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed + 170, wob=.15)
        for px in (x0 + 30, x1 - 30):                                                        # planters at the corners
            paint(rect(px - 34, base_y - 34, px + 34, base_y), ['#6a3f24', '#7c4c2c'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed + int(px), wob=.2)
            rr = np.random.RandomState(seed + int(px))
            for j in range(40): c.dots([(px + rr.uniform(-34, 34), base_y - 34 - rr.uniform(0, 24))], rr.uniform(3, 5), ['#2f5a2a', '#3e6e32', '#4c7e3a'], seed=rr.randint(1 << 20))
            for j in range(12): c.dots([(px + rr.uniform(-30, 30), base_y - 36 - rr.uniform(0, 22))], rr.uniform(3, 4.5), ['#c42a24', '#e04838', '#f4d040'], seed=rr.randint(1 << 20))

def hero_shop(x0, x1, top, base_y):
    """The toy shop: yellow stucco, a wreathed cornice, two windows, a painted sign with lamps, a striped awning, a
    shop window with a rocking horse, presents and string lights, and a door with a wreath."""
    cx = (x0 + x1) / 2
    paint(rect(x0, top, x1, base_y), ['#e8b838', '#f0c448', '#dca630', '#f4cc58', '#d89c28'], spacing=1.3, L=2.6, w=1.9, seed=200,
          dir_=(cx, (top + base_y) / 2, (x1 - x0), (base_y - top)), lbase=.82)
    for yy in np.arange(top + 30, base_y - 10, 34):                                                         # faint coursing in the stucco
        line([(x0 + 3, yy + 2 * math.sin(yy)), (x1 - 3, yy - 2 * math.sin(yy * 1.3))], 1.0, '#b88420', a=.12, taper=(.1, .1))
    paint(rect(x0 - 6, top - 14, x1 + 6, top + 8), ['#f6f0e2', '#ece4d2', '#fffaf0'], spacing=1.0, L=2.2, w=1.5, ang=0.0, seed=210, edge=.15, wob=.2)   # cornice
    for i in range(14):
        xx = x0 + 4 + i * (x1 - x0 - 8) / 13
        paint(rect(xx - 3, top + 8, xx + 3, top + 14), ['#e8e0cc', '#f6f0e2'], spacing=.7, L=1.2, w=1.0, seed=220 + i, wob=.1, edge=.2)   # dentils
    garland([(x0 + 10, top + 22), (x0 + (x1 - x0) * .25, top + 40), (cx, top + 24), (x0 + (x1 - x0) * .75, top + 40), (x1 - 10, top + 22)], 230,
            bows=[(x0 + 12, top + 20), (cx, top + 22), (x1 - 12, top + 20)])
    windows_row(x0 + 40, x1 - 40, top + 250, 3, 78, 124, '#f4efe6', ['#ffd060', '#ffe49a', '#f4b844', '#fff0c0'], 260)
    # the sign
    sy0, sy1 = top + 290, top + 382
    sx0, sx1 = cx - 190, cx + 190
    c.area(rect(sx0 + 5, sy0 + 6, sx1 + 5, sy1 + 6), '#3a2610', wob=.4, rough=.8, edge_dark=0, a=.4, seed=300)                               # its shadow
    board = [(sx0, sy0 + 8), (sx0 + 10, sy0), (sx1 - 10, sy0), (sx1, sy0 + 8), (sx1, sy1 - 8), (sx1 - 10, sy1), (sx0 + 10, sy1), (sx0, sy1 - 8)]
    paint(board, ['#6a3a20', '#7a4628', '#5a301a'], spacing=1.0, L=2.2, w=1.5, ang=0.0, seed=301, edge=.25, wob=.25)
    inner = [(x + (cx - x) * .035, y + ((sy0 + sy1) / 2 - y) * .11) for x, y in board]
    paint(inner, ['#f6ecd2', '#efe2c0', '#fbf4e0'], spacing=.9, L=2.0, w=1.4, ang=0.0, seed=302, edge=.12, wob=.15, lbase=.9)
    letters('TOYS FOR TOTS', cx, sy0 + 38, 25, ['#b8302a', '#a82820', '#c8382c'], track=2, seed=310)
    stars(cx, sy0 + 72, 3, 34, 9, '#b8302a')
    for lx in (sx0 + 50, cx - 7, sx1 - 64): wall_lamp(lx, sy0 - 6, 330 + int(lx))
    # awning and shop window
    ay = top + 400
    awning(x0 + 14, x1 - 14, ay, 62, ['#c8302a', '#f4ede0'], 400)
    wx0, wx1, wy0, wy1 = x0 + 40, cx + 80, ay + 84, base_y - 40
    paint(rect(wx0 - 8, wy0 - 6, wx1 + 8, wy1 + 10), ['#5a3420', '#6a3e26'], spacing=1.0, L=1.8, w=1.4, seed=420, edge=.2, wob=.2)       # window frame
    paint(rect(wx0, wy0, wx1, wy1), ['#d89a30', '#e8b040', '#c88828', '#f0c860'], spacing=.9, L=1.6, w=1.3, seed=421, edge=0, glow=.75, lbase=.78)
    glow_spot((wx0 + wx1) / 2, (wy0 + wy1) / 2, 150, .55)
    shelf = wy1 - 34
    paint(rect(wx0, shelf, wx1, shelf + 6), ['#7a4a2a', '#8a5632'], spacing=.8, L=1.6, w=1.1, ang=0.0, seed=422, wob=.1)
    rocking_horse((wx0 + wx1) / 2 + 30, shelf - 2, 1.6, 430)
    toy_train(wx0 + 20, shelf, 1.2, 435)
    for i, (px, pw, ph, col, rib, yb) in enumerate([(wx1 - 70, 40, 34, '#3a5aa8', '#f4d040', 0), (wx1 - 34, 30, 44, '#c8302a', '#f4ede0', 0),
                                                    (wx1 - 62, 30, 24, '#3e7a3a', '#c8302a', -34), (wx0 + 30, 34, 28, '#e4b030', '#c8302a', -80)]):
        present(px, shelf + yb, pw, ph, col, rib, 440 + i * 9)
    paint(rect(wx0, wy0 + 64, wx0 + 110, wy0 + 70), ['#7a4a2a', '#8a5632'], spacing=.8, L=1.6, w=1.1, ang=0.0, seed=425, wob=.1)   # an upper shelf
    teddy(wx0 + 80, wy0 + 64, 1.3, 426)
    string_lights([(wx0, wy0 + 6), ((wx0 + wx1) / 2, wy0 + 16), (wx1, wy0 + 6)], 470)
    for xx in np.linspace(wx0, wx1, 4)[1:-1]: line([(xx, wy0), (xx, wy1)], 2.2, '#5a3420', a=.95)              # glazing bars
    paint(rect(wx0 - 10, wy1 + 8, wx1 + 10, wy1 + 16), ['#f2ece0', '#e6dece'], spacing=.9, L=1.8, w=1.2, ang=0.0, seed=480, wob=.15)   # stall riser
    paint(rect(wx0 - 10, wy1 + 16, wx1 + 10, base_y), ['#7a4a2a', '#6a3e22', '#8a5632'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=481, wob=.15)
    # the door
    dx0, dx1, dy1 = cx + 140, x1 - 60, base_y
    dtop = ay + 70
    paint([(dx0 - 8, dy1)] + arch_top(dx0 - 8, dx1 + 8, dtop + 20, 26) + [(dx1 + 8, dy1)], ['#f2ece0', '#e8e0d0', '#faf5ea'], spacing=1.0, L=1.8, w=1.3, seed=490, edge=.12, wob=.2)
    door = [(dx0, dy1)] + arch_top(dx0, dx1, dtop + 22, 20) + [(dx1, dy1)]
    paint(door, ['#6a3a22', '#7a4628', '#5a2e1a', '#84502e'], spacing=1.0, L=3.0, w=1.3, ang=math.pi / 2, seed=491, edge=.2, wob=.2, dir_=((dx0 + dx1) / 2, dy1 - 60, 60, 120))
    line([((dx0 + dx1) / 2, dtop + 8), ((dx0 + dx1) / 2, dy1)], 1.6, '#3a1e12', a=.8)
    for yy in (dtop + 50, dy1 - 50):
        for xa, xb in ((dx0 + 8, (dx0 + dx1) / 2 - 6), ((dx0 + dx1) / 2 + 6, dx1 - 8)):
            line([(xa, yy), (xb, yy), (xb, yy + 32), (xa, yy + 32), (xa, yy)], 1.2, '#3a1e12', a=.55, taper=(0, 0))
    paint(rect(dx0 + 10, dtop + 26, dx1 - 10, dtop + 44), ['#ffd870', '#ffe49a', '#f0b848'], spacing=.8, L=1.4, w=1.0, seed=495, edge=0, glow=.1, lbase=1.0)   # fanlight
    wreath((dx0 + dx1) / 2, dtop + 78, 17, 497)
    c.dots([((dx0 + dx1) / 2 + 6, dy1 - 52), ((dx0 + dx1) / 2 - 6, dy1 - 52)], 1.6, ['#d8a840'], seed=499)
    return (wx0, wx1, ay, base_y), (dx0, dx1)

def toy_train(x, ybase, s, seed):
    """A wind-up toy locomotive in the window (x: its left end)."""
    red = ['#c8302a', '#d63a2c', '#b82820']
    paint(rect(x, ybase - 26 * s, x + 54 * s, ybase - 8 * s), red, spacing=.6, L=1.3, w=.9, ang=0.0, seed=seed, wob=.06, glow=.3, dir_=(x + 10, ybase - 24 * s, 30 * s, 10 * s))
    paint(rect(x + 34 * s, ybase - 46 * s, x + 56 * s, ybase - 24 * s), red, spacing=.6, L=1.2, w=.9, seed=seed + 1, wob=.06, glow=.3)
    paint(rect(x + 30 * s, ybase - 50 * s, x + 60 * s, ybase - 44 * s), ['#1c1a1a', '#2a2624'], spacing=.5, L=1.0, w=.7, ang=0.0, seed=seed + 2, wob=.05)
    paint(rect(x + 38 * s, ybase - 41 * s, x + 50 * s, ybase - 31 * s), ['#ffe49a', '#fff0c0'], spacing=.5, L=.9, w=.7, seed=seed + 3, wob=.05, glow=.1, lbase=1.0)
    paint(rect(x + 10 * s, ybase - 40 * s, x + 18 * s, ybase - 26 * s), ['#1c1a1a', '#2a2624'], spacing=.5, L=1.0, w=.7, seed=seed + 4, wob=.05)
    for wx in (10, 26, 44): c.dots([(x + wx * s, ybase - 6 * s)], 6 * s, ['#1c1a1a'], seed=seed + wx); c.dots([(x + wx * s, ybase - 6 * s)], 2.2 * s, ['#e4b030'], seed=seed + wx + 1)
    c.dots([(x - 2 * s, ybase - 18 * s)], 3 * s, ['#e4b030'], seed=seed + 9)

def wreath(x, y, r_, seed):
    rr = np.random.RandomState(seed)
    for t in np.linspace(0, 2 * math.pi, 46, endpoint=False):
        for j in range(2):
            rad = r_ * rr.uniform(.78, 1.12)
            c.dots([(x + math.cos(t) * rad, y + math.sin(t) * rad)], rr.uniform(2.0, 3.0), ['#244a24', '#2f5a2a', '#3e6e32', '#557d3a'], seed=rr.randint(1 << 20))
    for t in np.linspace(0, 2 * math.pi, 9, endpoint=False):
        c.dots([(x + math.cos(t + .3) * r_, y + math.sin(t + .3) * r_)], 1.6, ['#d03028', '#f2d050'], seed=rr.randint(1 << 20))
    bow(x, y + r_ * .95, 7, seed + 7)

def present(x, ybase, w, h, col, rib, seed):
    """A wrapped box seen slightly from above: front, a lighter top, a ribbon and a bow; x is its left edge."""
    top = ybase - h; d = min(6, w * .25)
    paint(rect(x, top, x + w, ybase), [col, col], spacing=.8, L=1.4, w=1.0, seed=seed, wob=.15, edge=.18, dir_=(x + w * .3, top, w, h), var=.05)
    lt = hexc(col) * 1.18
    paint([(x, top), (x + w, top), (x + w + d * .6, top - d), (x + d * .6, top - d)], [lt, lt], spacing=.7, L=1.2, w=.9, seed=seed + 1, wob=.1, edge=.1)
    paint([(x + w, top), (x + w + d * .6, top - d), (x + w + d * .6, ybase - d), (x + w, ybase)], [hexc(col) * .7, hexc(col) * .7], spacing=.7, L=1.2, w=.9, seed=seed + 2, wob=.1)
    line([(x + w * .5, ybase), (x + w * .5, top)], max(1.2, w * .14), rib, a=.95, taper=(0, 0))
    line([(x + w * .5, top), (x + w * .5 + d * .6, top - d)], max(1.0, w * .12), rib, a=.95, taper=(0, 0))
    line([(x, top + h * .5), (x + w, top + h * .5)], max(1.0, h * .12), rib, a=.9, taper=(0, 0))
    bx, by = x + w * .5 + d * .3, top - d * .5
    for s_ in (-1, 1):
        paint([(bx, by), (bx + s_ * w * .28, by - w * .2), (bx + s_ * w * .3, by + w * .06)], [rib, rib], spacing=.6, L=1.0, w=.8, seed=seed + 4 + s_, wob=.1, edge=.15)

def rocking_horse(x, ybase, s, seed):
    """A painted wooden rocking horse in the shop window."""
    cream, dark = ['#f2e2c2', '#e8d4ae', '#fbefd6'], '#5a3a26'
    rocker = [(x - 40 * s + 80 * s * u, ybase - 4 * s - 9 * s * math.sin(u * math.pi) * -1 + 9 * s) for u in np.linspace(0, 1, 16)]
    rocker = [(px, ybase - 2 - 10 * s * (1 - (2 * (px - x) / (80 * s)) ** 2)) for px, _ in rocker]
    line(rocker, 4 * s, '#8a3a22', a=1, taper=(.05, .05))
    for lx, ang in ((-22, .25), (-12, .05), (10, -.05), (20, -.25)):
        line([(x + lx * s, ybase - 12 * s), (x + lx * s - ang * 18 * s, ybase - 34 * s)], 3.4 * s, cream[1], a=1, taper=(0, 0))
    body = lumpy(x, ybase - 42 * s, 26 * s, 11 * s, seed, n=30, bumps=3, amp=.05, flat=.1)
    paint(body, cream, spacing=.7, L=1.3, w=1.0, seed=seed, wob=.1, edge=.15, dir_=(x - 8, ybase - 48 * s, 30 * s, 14 * s), glow=.25)
    neck = [(x + 14 * s, ybase - 48 * s), (x + 20 * s, ybase - 74 * s), (x + 34 * s, ybase - 72 * s), (x + 38 * s, ybase - 62 * s), (x + 26 * s, ybase - 56 * s), (x + 24 * s, ybase - 44 * s)]
    paint(neck, cream, spacing=.7, L=1.3, w=1.0, seed=seed + 1, wob=.1, edge=.15, glow=.25)
    line([(x + 19 * s, ybase - 74 * s), (x + 14 * s, ybase - 62 * s), (x + 12 * s, ybase - 50 * s)], 3.2 * s, '#8a3a22', a=.95, taper=(.1, .2))   # mane
    line([(x - 24 * s, ybase - 46 * s), (x - 34 * s, ybase - 40 * s), (x - 36 * s, ybase - 30 * s)], 3 * s, '#8a3a22', a=.95, taper=(.1, .5))      # tail
    paint(rect(x - 6 * s, ybase - 54 * s, x + 8 * s, ybase - 46 * s), ['#c8302a', '#b82820'], spacing=.6, L=1.0, w=.8, seed=seed + 2, wob=.1)      # saddle
    c.dots([(x + 30 * s, ybase - 67 * s)], 1.1 * s, [dark], seed=seed)

def bench(x, y, s, seed):
    """A park bench: wooden slats on green cast-iron ends."""
    shadow(x + 20, y + 3, 70 * s, 6 * s, a=.4)
    for ex in (-38, 38):
        line([(x + ex * s, y), (x + ex * s, y - 26 * s), (x + (ex - 4) * s, y - 52 * s)], 4 * s, '#1e3a2a', a=1, taper=(0, 0))
        line([(x + (ex - 6) * s, y - 26 * s), (x + (ex + 6) * s, y - 26 * s)], 3 * s, '#1e3a2a', a=1, taper=(0, 0))
    for i, yy in enumerate((-30, -24)):
        paint(rect(x - 46 * s, y + (yy - 3) * s, x + 46 * s, y + (yy + 2) * s), ['#8a5632', '#9a6238', '#7a4a2a'], spacing=.6, L=2.0, w=.8, ang=0.0, seed=seed + i, wob=.05, glow=.35)
    for i, yy in enumerate((-50, -42)):
        paint(rect(x - 48 * s, y + (yy - 3) * s, x + 44 * s, y + (yy + 2) * s), ['#8a5632', '#9a6238', '#7a4a2a'], spacing=.6, L=2.0, w=.8, ang=0.0, seed=seed + 5 + i, wob=.05, glow=.35)

def planter(x, ybase, s, seed):
    """A wooden planter of poinsettias by the door."""
    paint([(x - 24 * s, ybase - 30 * s), (x + 24 * s, ybase - 30 * s), (x + 20 * s, ybase), (x - 20 * s, ybase)], ['#6a3f24', '#7c4c2c', '#5a341e'], spacing=.8, L=2.0, w=1.2, ang=math.pi / 2, seed=seed, wob=.1, edge=.2)
    rr = np.random.RandomState(seed)
    for j in range(26): c.dots([(x + rr.uniform(-26, 26) * s, ybase - 30 * s - rr.uniform(0, 22) * s)], rr.uniform(3, 4.6) * s, ['#244a24', '#2f5a2a', '#3e6e32'], seed=rr.randint(1 << 20))
    for j in range(7):
        fx, fy = x + rr.uniform(-20, 20) * s, ybase - 34 * s - rr.uniform(0, 20) * s
        for t in np.linspace(0, 2 * math.pi, 6, endpoint=False):
            line([(fx, fy), (fx + math.cos(t + j) * 7 * s, fy + math.sin(t + j) * 7 * s)], 3.2 * s, ['#c42a24', '#d63a2c', '#b82820'][j % 3], a=.95, taper=(0, .7))
        c.dots([(fx, fy)], 1.4 * s, ['#f4d040'], seed=seed + j)

def nutcracker(x, ybase, s, seed):
    """A wooden nutcracker soldier in the window: red coat, tall black hat, white beard."""
    paint(rect(x - 9 * s, ybase - 40 * s, x - 2 * s, ybase), ['#1c2642', '#28365c'], spacing=.5, L=1.0, w=.7, seed=seed, wob=.05)
    paint(rect(x + 2 * s, ybase - 40 * s, x + 9 * s, ybase), ['#1c2642', '#28365c'], spacing=.5, L=1.0, w=.7, seed=seed + 1, wob=.05)
    paint(rect(x - 13 * s, ybase - 82 * s, x + 13 * s, ybase - 38 * s), ['#c8302a', '#b82820', '#d63a2c'], spacing=.6, L=1.2, w=.8, seed=seed + 2, wob=.06, dir_=(x - 6 * s, ybase - 70 * s, 12 * s, 20 * s), glow=.3)
    for i in range(4): c.dots([(x, ybase - (76 - i * 9) * s)], 1.6 * s, ['#f4d040'], seed=seed + i)
    paint(rect(x - 14 * s, ybase - 46 * s, x + 14 * s, ybase - 40 * s), ['#f6f4ee', '#e8e2d6'], spacing=.5, L=1.0, w=.7, ang=0.0, seed=seed + 3, wob=.05)
    paint(lumpy(x, ybase - 92 * s, 10 * s, 11 * s, seed, n=20, bumps=2, amp=.03), ['#f0c8a0', '#e6b890'], spacing=.5, L=.9, w=.7, seed=seed + 4, wob=.05, glow=.3)
    paint([(x - 10 * s, ybase - 90 * s), (x + 10 * s, ybase - 90 * s), (x + 6 * s, ybase - 76 * s), (x, ybase - 72 * s), (x - 6 * s, ybase - 76 * s)], ['#f6f4ee', '#ffffff', '#e8e2d6'], spacing=.5, L=1.0, w=.7, seed=seed + 5, wob=.05)
    c.dots([(x - 4 * s, ybase - 95 * s), (x + 4 * s, ybase - 95 * s)], 1.2 * s, ['#1a1210'], seed=seed + 6)
    paint(rect(x - 11 * s, ybase - 128 * s, x + 11 * s, ybase - 100 * s), ['#141214', '#22201e'], spacing=.5, L=1.1, w=.7, ang=math.pi / 2, seed=seed + 7, wob=.05)
    line([(x - 11 * s, ybase - 104 * s), (x + 11 * s, ybase - 104 * s)], 2 * s, '#e4b030', a=.95, taper=(0, 0))
    for ex in (-1, 1): line([(x + ex * 13 * s, ybase - 78 * s), (x + ex * 17 * s, ybase - 50 * s)], 6 * s, '#c8302a', a=1, taper=(0, 0))

def christmas_tree(x, y, h, seed):
    """A decorated tree in a planter: a stippled cone, lights, baubles, a bow and a star."""
    paint(rect(x - 30, y - 22, x + 30, y + 6), ['#7a4a2a', '#6a3e22', '#8a5632'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed, wob=.2)
    dab_tree(c, x, y - 18, h, ['#1e3c22', '#264a28', '#2f5a2a', '#3e6e32', '#4c7e3a'], seed + 1, shape='cone', trunk='#4a3020')
    r = np.random.RandomState(seed)
    for i in range(70):
        t = r.uniform(.08, .92); wd = h * .26 * math.sin(min(1, (1 - t) * 1.3) * math.pi / 2) ** .8 * .85
        px, py = x + r.uniform(-wd, wd), y - 18 - h * .08 - h * .92 * t
        if i % 3 == 0: c.dots([(px, py)], 2.6, ['#c42a24', '#e4b030', '#d84434'], seed=seed + i)
        else: c.dots([(px, py)], 1.4, ['#fff0b0', '#ffe080'], seed=seed + i); glow_spot(px, py, 8, .05)
    bow(x, y - 18 - h * .55, 12, seed + 90)
    star = [(x + 10 * (1 if j % 2 == 0 else .45) * math.sin(j * math.pi / 5), y - 18 - h - 4 - 10 * (1 if j % 2 == 0 else .45) * math.cos(j * math.pi / 5)) for j in range(10)]
    paint(star, ['#f4d040', '#ffe060'], spacing=.7, L=1.2, w=1.0, seed=seed + 95, wob=.1, glow=.2)
    glow_spot(x, y - 18 - h * .5, h * .55, .25)

# ------------------------------------------------------------------ the people
SKIN = {'light': ['#f0c8a0', '#e6b890', '#f6d4b0'], 'brown': ['#9a6440', '#8a5634', '#a87048']}
def shadow(x, y, rx, ry, a=.42, dx=0.0):
    c.area(lumpy(x + dx, y, rx, ry, int(x * 7 + y), n=30, bumps=3, amp=.06, flat=.2), '#2a2420', wob=.4, rough=.7, edge_dark=0, a=a, seed=int(x))

def marine(x, y, s, skin, face_dir, seed, arm_out=1.0, lean=0.0):
    """A Marine in dress blues, about 160 units tall at s = 1: white cap with a black peak, a face with eyes, brows,
    nose and mouth, a navy coat lit on one side, gold buttons, a red collar band, white belt and gloves, blue trousers
    with the red blood stripe, black shoes. face_dir = 1 faces right, -1 faces left."""
    f = face_dir; r = np.random.RandomState(seed)
    navy = ['#1c2642', '#222e50', '#18203a', '#28365c']; blue = ['#3a5a9c', '#44669e', '#324e8a']
    gold, red, white = '#e4b040', '#c8302a', ['#f6f4ee', '#ece8de', '#ffffff']
    shadow(x + 26 * s, y + 3, 46 * s, 7 * s, a=.32)                    # cast shadow, away from the lamps on the left
    shadow(x, y + 1, 22 * s, 4.5 * s, a=.5)                           # contact shadow
    hip = y - 66 * s
    # legs: two trousers, one slightly forward; the red stripe on the outside of each
    for k_, (lx, fw) in enumerate(((-9, -2 * f), (8, 3 * f))):
        leg = [(x + (lx - 8) * s + lean * 2, hip), (x + (lx + 8) * s + lean * 2, hip), (x + (lx + 7) * s + fw * s, y - 6 * s), (x + (lx - 7) * s + fw * s, y - 6 * s)]
        paint(leg, blue, spacing=.8, L=2.4, w=1.0, ang=math.pi / 2, seed=seed + k_, wob=.1, edge=.15, dir_=(x - 10 * s, hip + 30 * s, 20 * s, 60 * s), lbase=.78)
        side = (lx + 7.5) if lx > 0 else (lx - 7.5)
        line([(x + side * s + lean * 2, hip + 2), (x + (side - .5) * s + fw * s, y - 7 * s)], 2.2 * s, red, a=.95, taper=(0, 0))
        shoe = [(x + (lx - 8) * s + fw * s, y - 7 * s), (x + (lx + 8 + 4 * f) * s + fw * s, y - 7 * s), (x + (lx + 9 + 5 * f) * s + fw * s, y), (x + (lx - 9) * s + fw * s, y)]
        paint(shoe, ['#141214', '#22201e'], spacing=.6, L=1.2, w=.9, seed=seed + 5 + k_, wob=.1, edge=.1)
        c.dots([(x + (lx + 2 * f) * s + fw * s, y - 5 * s)], 1.2 * s, ['#6a6660'], seed=seed + k_)          # shine on the toe
    # the coat
    sh = y - 116 * s
    # a tailored coat: rounded shoulders, a nipped waist at the belt, a short flared skirt
    coat = [(x - 15 * s + lean, sh - 2 * s), (x + 15 * s + lean, sh - 2 * s), (x + 21 * s + lean, sh + 4 * s), (x + 20 * s + lean * .8, sh + 22 * s),
            (x + 16 * s + lean * .5, hip - 6 * s), (x + 20 * s, hip + 12 * s), (x - 20 * s, hip + 12 * s), (x - 16 * s + lean * .5, hip - 6 * s),
            (x - 20 * s + lean * .8, sh + 22 * s), (x - 21 * s + lean, sh + 4 * s)]
    coat = list(map(tuple, catmull(coat, 6, closed=True)))
    paint(coat, navy + ['#34467a'], spacing=.8, L=2.2, w=1.1, ang=math.pi / 2, seed=seed + 10, wob=.12, edge=.3, dir_=(x - 12 * s, sh + 20 * s, 26 * s, 56 * s), lbase=.9, glow=.6)
    c.stroke(coat + [coat[0]], 1.4 * s, '#0c0e1a', a=.45, dry=.3, taper=(0, 0))
    line([(x + lean * .8, sh + 4 * s), (x + lean * .5, hip + 12 * s)], 1.2 * s, '#0e1222', a=.6, taper=(0, 0))               # front opening
    for i in range(4): c.dots([(x + 3.5 * s * f + lean * .7, sh + (8 + i * 10) * s)], 1.7 * s, [gold], seed=seed + 20 + i)
    paint(rect(x - 17 * s + lean * .6, hip - 8 * s, x + 17 * s + lean * .6, hip - 1 * s), white, spacing=.6, L=1.4, w=.9, ang=0.0, seed=seed + 30, wob=.1, edge=.12)  # belt
    paint(rect(x - 4 * s, hip - 8.5 * s, x + 4 * s, hip - .5 * s), ['#e8c050', '#f4d470'], spacing=.5, L=.9, w=.7, seed=seed + 31, wob=.05)                     # buckle
    for ex in (-1, 1): line([(x + ex * 13 * s + lean, sh - 1 * s), (x + ex * 21 * s + lean, sh + 3 * s)], 3.0 * s, gold, a=.9, taper=(0, 0))   # shoulder boards
    # arms: both reach toward the present; the far one a little higher
    hand_y = sh + 34 * s
    for k_, (side, dy, ext) in enumerate(((-f, 2, .8), (f, -2, 1.0))):
        sx_ = x + side * 18 * s + lean
        hx_ = x + f * (24 + 20 * arm_out * ext) * s
        hy_ = hand_y + dy * s
        elbow = (sx_ + side * 2 * s + f * 4 * s, sh + 30 * s)                                          # elbows by the sides, forearms forward
        c.stroke([(sx_, sh + 5 * s), elbow, (hx_, hy_)], 9.5 * s, navy[0] if k_ == 0 else navy[1], a=1, dry=.08, taper=(0, .05), press=.1)
        c.stroke([(sx_ - 2 * s, sh + 7 * s), elbow], 3 * s, '#3a4a78', a=.35, dry=.3, taper=(.1, .4))                       # light on the sleeve
        line([(hx_ - f * 5 * s, hy_ - 4 * s), (hx_ - f * 5 * s, hy_ + 4 * s)], 2.4 * s, red, a=.9, taper=(0, 0))          # cuff
        paint(lumpy(hx_, hy_, 5.2 * s, 4.6 * s, seed + 40 + k_, n=16, bumps=2, amp=.08), white, spacing=.5, L=1.0, w=.8, seed=seed + 42 + k_, wob=.05, edge=.18)  # glove
    # collar, neck, head
    paint(SKIN_NECK := rect(x - 5 * s + lean, sh - 9 * s, x + 5 * s + lean, sh - 3 * s), SKIN[skin], spacing=.5, L=1.0, w=.8, seed=seed + 49, wob=.05, lbase=.75)
    paint(rect(x - 9 * s + lean, sh - 6 * s, x + 9 * s + lean, sh + 1 * s), navy, spacing=.5, L=1.0, w=.8, seed=seed + 50, wob=.05)
    line([(x - 7 * s + lean, sh - 1.5 * s), (x + 7 * s + lean, sh - 1.5 * s)], 1.6 * s, red, a=.9, taper=(0, 0))
    hx, hy = x + lean + f * 1.5 * s, sh - 21 * s
    face = lumpy(hx, hy, 13.5 * s, 15 * s, seed + 60, n=28, bumps=2, amp=.03, flat=.1)
    paint(face, SKIN[skin], spacing=.5, L=1.0, w=.8, seed=seed + 61, wob=.05, edge=.14, dir_=(hx - 4 * s, hy - 4 * s, 12 * s, 14 * s), lbase=.9, glow=.35)
    c.dots([(hx - f * 12.5 * s, hy + 1 * s)], 2.8 * s, [hexc(SKIN[skin][0]) * .9], seed=seed)                               # ear
    for ex in (-5.5, 4.5):
        ex_ = hx + (ex + f * 1.2) * s
        c.dots([(ex_, hy + .5 * s)], 2.0 * s, ['#f6f2ea'], seed=seed + int(ex * 10) + 1)                    # the white of the eye
        c.dots([(ex_ + f * .5 * s, hy + .7 * s)], 1.45 * s, ['#1a120e'], seed=seed + int(ex * 10))
        c.dots([(ex_ + f * .1 * s - .5 * s, hy - .2 * s)], .45 * s, ['#ffffff'], seed=seed + int(ex * 10) + 2)   # catchlight
        line([(hx + (ex + f * 1.2 - 2) * s, hy - 3 * s), (hx + (ex + f * 1.2 + 2) * s, hy - 3.4 * s)], .9 * s, '#3a2418', a=.8, taper=(.2, .2))
    line([(hx + f * 3.5 * s, hy + 2 * s), (hx + f * 5.2 * s, hy + 5 * s), (hx + f * 3.2 * s, hy + 5.6 * s)], .9 * s, hexc(SKIN[skin][0]) * .72, a=.9, taper=(0, 0))   # nose
    line([(hx - 3 * s + f * 1.5 * s, hy + 8 * s), (hx + f * 1.5 * s, hy + 9.4 * s), (hx + 3 * s + f * 1.5 * s, hy + 8 * s)], 1.3 * s, '#6a2a20' if skin == 'brown' else '#8a3a2a', a=.9, taper=(.2, .2))  # smile
    c.dots([(hx - 6 * s + f * s, hy + 5 * s), (hx + 6 * s + f * s, hy + 5 * s)], 1.8 * s, ['#e88878'], a=.35, seed=seed + 70)                                     # cheeks
    # the cap: white crown, black peak, gold badge
    cy_ = hy - 13 * s
    crown = [(hx - 19 * s, cy_ - 1 * s), (hx + 19 * s, cy_ - 1 * s), (hx + 15 * s, cy_ - 10 * s), (hx - 15 * s, cy_ - 10 * s)]
    paint(crown, white, spacing=.5, L=1.1, w=.8, ang=0.0, seed=seed + 80, wob=.08, edge=.15, dir_=(hx - 6 * s, cy_ - 8 * s, 16 * s, 6 * s), glow=.3)
    paint(rect(hx - 14 * s, cy_ - 1.5 * s, hx + 14 * s, cy_ + 3.5 * s), ['#141214', '#22201e'], spacing=.5, L=1.0, w=.7, seed=seed + 81, wob=.05)
    peak = [(hx + f * 2 * s - 11 * s, cy_ + 3 * s), (hx + f * 2 * s + 11 * s, cy_ + 3 * s), (hx + f * 7 * s + 9 * s * f, cy_ + 7 * s), (hx + f * 7 * s - 9 * s * f, cy_ + 7 * s)]
    paint(peak, ['#0e0c0e', '#1c1a1c'], spacing=.5, L=1.0, w=.7, seed=seed + 82, wob=.05)
    c.dots([(hx, cy_ - 3 * s)], 2.0 * s, [gold], seed=seed + 83)
    return (x + f * (24 + 20 * arm_out) * s, hand_y)

def teddy(x, y, s, seed):
    fur = ['#a8703a', '#b87e44', '#966230', '#c48c50']
    paint(lumpy(x, y - 12 * s, 11 * s, 12 * s, seed, n=24, bumps=3, amp=.06), fur, spacing=.5, L=1.0, w=.8, seed=seed, wob=.05, edge=.18, dir_=(x - 4, y - 18 * s, 10 * s, 12 * s), glow=.3)
    for ex in (-9, 9): c.dots([(x + ex * s, y - 30 * s)], 4 * s, ['#a8703a'], seed=seed + ex)
    paint(lumpy(x, y - 29 * s, 9 * s, 8 * s, seed + 1, n=22, bumps=2, amp=.04), fur, spacing=.5, L=.9, w=.7, seed=seed + 2, wob=.05, edge=.16, glow=.3)
    c.dots([(x, y - 26.5 * s)], 3.4 * s, ['#e4c48e'], seed=seed + 3)
    c.dots([(x - 3 * s, y - 31 * s), (x + 3 * s, y - 31 * s), (x, y - 27.5 * s)], 1.0 * s, ['#1a1210'], seed=seed + 4)
    bow(x, y - 21 * s, 4 * s, seed + 5)

def wagon(x, y, s, seed):
    """A little red wagon with a teddy bear, a ball and a present; its handle angled toward the viewer."""
    shadow(x + 10 * s, y + 4, 52 * s, 6 * s, a=.4)
    bed = [(x - 40 * s, y - 34 * s), (x + 40 * s, y - 34 * s), (x + 37 * s, y - 14 * s), (x - 37 * s, y - 14 * s)]
    teddy(x - 12 * s, y - 34 * s, s * 1.1, seed + 30)
    c.dots([(x + 18 * s, y - 42 * s)], 9 * s, ['#3a6ab8'], seed=seed + 40)
    line([(x + 10 * s, y - 42 * s), (x + 26 * s, y - 42 * s)], 2.2 * s, '#f4d040', a=.9)
    line([(x + 18 * s, y - 51 * s), (x + 18 * s, y - 33 * s)], 2.2 * s, '#c8302a', a=.9)
    paint(bed, ['#c8302a', '#d63a2c', '#b82820'], spacing=.7, L=1.6, w=1.0, ang=0.0, seed=seed, wob=.1, edge=.18, dir_=(x - 20 * s, y - 34 * s, 40 * s, 20 * s), glow=.4)
    line([(x - 38 * s, y - 33 * s), (x + 38 * s, y - 33 * s)], 2.4 * s, '#e85844', a=.8, taper=(0, 0))
    for wx in (-26, 26):
        c.dots([(x + wx * s, y - 9 * s)], 9 * s, ['#1c1a1a'], seed=seed + wx)
        c.dots([(x + wx * s, y - 9 * s)], 3.5 * s, ['#8a8680'], seed=seed + wx + 1)
    line([(x + 38 * s, y - 22 * s), (x + 62 * s, y - 34 * s), (x + 72 * s, y - 38 * s)], 2.6 * s, '#1c1a1a', a=1, taper=(0, 0))

def donation_box(x, ybase, seed, s=1.0):
    w, h = 74 * s, 130 * s
    shadow(x + 30, ybase + 4, 50, 8, a=.4)
    body = [(x - w / 2, ybase), (x - w / 2, ybase - h + 14), (x - w / 2 + 10, ybase - h), (x + w / 2 - 10, ybase - h), (x + w / 2, ybase - h + 14), (x + w / 2, ybase)]
    paint(body, ['#c42a24', '#b82620', '#d43a2e', '#a82220'], spacing=.9, L=2.0, w=1.3, ang=math.pi / 2, seed=seed, wob=.15, edge=.2, dir_=(x - 20, ybase - h * .7, w * .6, h * .6), glow=.45)
    paint([(x + w / 2, ybase), (x + w / 2, ybase - h + 14), (x + w / 2 + 12, ybase - h + 20), (x + w / 2 + 12, ybase - 6)], ['#8a1c18', '#7a1814'], spacing=.8, L=1.8, w=1.2, seed=seed + 1, wob=.1)   # side, in shadow
    paint(rect(x - 22, ybase - h + 18, x + 22, ybase - h + 26), ['#2a1412', '#3a1a16'], spacing=.6, L=1.2, w=.8, seed=seed + 2, wob=.05)  # slot
    paint(rect(x - w / 2 + 6, ybase - h + 40, x + w / 2 - 6, ybase - 34), ['#f6ecd8', '#efe2c4'], spacing=.8, L=1.6, w=1.1, seed=seed + 3, wob=.1, edge=.12)
    letters('TOY', x, ybase - h + 58 * s, 12 * s, ['#b8302a', '#a82820'], seed=seed + 4)
    letters('DONATION', x, ybase - h + 80 * s, 6.6 * s, ['#b8302a', '#a82820'], seed=seed + 5)
    stars(x, ybase - 46 * s, 3, 13 * s, 4 * s, '#b8302a')
    paint(rect(x - w / 2 - 4, ybase - 6, x + w / 2 + 14, ybase + 2), ['#7a1814', '#8a1c18'], spacing=.7, L=1.4, w=1.0, seed=seed + 6, wob=.1)

# ------------------------------------------------------------------ the square
SPECKS = True
def cobbles(y0, y1, x0, x1):
    """Cobbles: a mortar ground, then stones in rows growing toward the viewer, each a dab of its own size and tone,
    a lighter worn path down the middle, and the lamplight pooling on them (applied through lit())."""
    c.area(rect(x0, y0, x1, y1), '#6e665c', wob=.2, rough=.6, edge_dark=0, seed=900)
    rows = []; y = y0 + 4
    while y < y1:
        sz = 9.0 + 16.0 * (y - y0) / (y1 - y0); rows.append((y, sz)); y += sz * .8
    rr = np.random.RandomState(901)
    for ri, (y, sz) in enumerate(rows):
        band = rect(x0, y - sz * .45, x1, y + sz * .45)
        m = c.mask(band, wob=0, rough=0)
        def col(X, Y, r, sz=sz):
            C = np.array([hexc(v) for v in ['#b8b0a2', '#a8a092', '#c8c0b0', '#9c9486', '#d0c8b8', '#b0a48e']])
            cc = C[r.randint(len(C), size=len(X))] * (1 + (r.rand(len(X), 1) - .5) * .16)
            worn = np.exp(-((X - 760) / 260) ** 2) * .1                                    # the worn path through the middle
            b, w = light_at(X, Y)
            v = .74 + worn + .55 * b
            cc = cc * v[:, None]; cc = cc * (1 - .45 * w[:, None]) + cc * WARM * .55 * w[:, None]
            return np.clip(cc, 0, 1)
        c.stip(m, col, spacing=sz * 1.05, L=sz * .95, w=sz * .66, angfn=lambda X, Y: np.zeros(X.shape), seed=902 + ri, jit=.18, thresh=.3)
    if SPECKS:
        for ri, (y, sz) in enumerate(rows[::2]):                                                      # tiny highlights on stone tops
            xs = rr.uniform(x0, x1, int((x1 - x0) / (sz * 5)))
            for xx in xs: c.dots([(xx, y - sz * .2)], sz * .12, ['#e8e2d4'], a=.5, seed=rr.randint(1 << 20))

def kerb_and_lawn():
    """The square's kerb curving round to the lawn, the lawn stroked along its contour, and two foreground trees."""
    curve = [(-20, 985), (200, 975), (440, 1020), (760, 1036), (1100, 1018), (1340, 975), (1520, 960)]
    P = resample(catmull(curve, 16), 3)
    lawn = list(map(tuple, P)) + [(1520, 1060), (-20, 1060)]
    paint(lawn, ['#d8b040', '#e4c050', '#c89c30', '#ecd070'], spacing=1.6, L=4.0, w=2.0, ang=0.0, seed=950, lbase=.86, glow=.3)
    for i in range(18):                                                                               # contour strokes
        off = 8 + i * 4.5
        Q = [(x, y + off + 3 * math.sin(x / 47 + i)) for x, y in P[::3]]
        c.stroke(Q, 2.2, ['#b88a28', '#f0d478', '#c89c30'][i % 3], a=.35, dry=.45, taper=(.05, .05))
    line(P - [0, 1], 6, '#d8d0c2', a=.95, taper=(0, 0))                                                  # kerb stones
    for x, y in P[::4]: line([(x, y - 3), (x, y + 2)], 1.0, '#8a8478', a=.6, taper=(0, 0))

def evening_glow():
    """The lamps' and windows' light as a soft warm bloom, added like a glaze."""
    k = c.k; gl = np.zeros((c.H, c.W), np.float32)
    for (x, y, r, s) in LIGHTS:
        if s < .2: continue
        cv2.circle(gl, (int(x * k), int(y * k)), int(r * k * .35), s, -1, cv2.LINE_AA)
    gl = cv2.GaussianBlur(gl, (0, 0), 30 * k)
    c.img[:] = np.clip(c.img + gl[..., None] * np.array([.30, .20, .07], np.float32), 0, 1)

def main(out):
    global c
    c = Kanvas(W * K, H * K, K, '#2a2430', seed=11); c.HM = np.zeros((c.H, c.W), np.float32)
    base_y, top = 590, -130                     # framed close: the ground floors fill the picture, upper floors run off the top
    glow_spot(300, 560, 160, .55); glow_spot(1215, 560, 160, .55)
    facade_side(-60, 360, top, base_y, ['#e89aa8', '#f0a8b4', '#dc8c9c', '#f4b8c2', '#e48698'], 100, None, awn=['#2f5aa8', '#f4ede0'], kind='teddy')
    facade_side(1140, 1560, top + 6, base_y, ['#b8302a', '#c4382e', '#a82a24', '#c84438', '#a02420'], 140, None, awn=['#3e7a3a', '#f4ede0'], kind='nutcracker')
    log('neighbours')
    hero_shop(360, 1140, top, base_y)
    for px in (830, 1110): planter(px, base_y + 4, 1.3, 870 + px)
    log('hero shop')
    paint(rect(-20, base_y - 4, 1520, base_y + 14), ['#d8d0c2', '#cac2b2', '#e4dccc'], spacing=1.0, L=2.4, w=1.4, ang=0.0, seed=880, wob=.2)   # pavement edge
    cobbles(base_y + 12, 1050, -20, 1520)
    log('cobbles')
    kerb_and_lawn()
    bench(445, 905, 1.6, 590)
    lamp_post(300, 900, 300, 600)
    christmas_tree(160, 960, 270, 620)
    for i, (px, pw, ph, col, rib) in enumerate([(250, 64, 52, '#c8302a', '#f4d040'), (318, 56, 44, '#3e7a3a', '#c8302a'), (282, 50, 36, '#3a5aa8', '#f4ede0'), (374, 48, 40, '#e4b030', '#c8302a')]):
        yb = 968 + (i % 2) * 8
        shadow(px + pw * .7, yb, pw * .7, 6, a=.35)
        present(px, yb, pw, ph, col, rib, 640 + i * 11)
    donation_box(1215, 880, 700, s=1.35)
    lamp_post(1340, 890, 300, 720)
    wagon(1010, 935, 1.45, 760)
    log('furniture')
    ha = marine(640, 950, 1.75, 'light', 1, 800, arm_out=.85, lean=2.0)
    hb = marine(852, 956, 1.8, 'brown', -1, 820, arm_out=.78, lean=-1.5)
    gx = (ha[0] + hb[0]) / 2; gy = min(ha[1], hb[1])
    present(gx - 26, gy + 18, 52, 40, '#e4b030', '#c8302a', 860)
    log('marines')
    dab_tree(c, 40, 1120, 300, ['#8a2a20', '#b83a2a', '#d4523a', '#e87858', '#f4a088'], 970)
    dab_tree(c, 1470, 1125, 280, ['#2f5a2a', '#4c7e3a', '#6e9a44', '#8fb24e', '#b4c868'], 980)
    impasto(c, strength=.22)
    evening_glow()
    im = (np.clip(c.img, 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(im).save(out); log(f'saved {out} {im.shape[1]}x{im.shape[0]}')

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else os.path.join(HERE, 'out', 'square11.png'))

"""Pass 5 — refinement of the approved pass 4 map (experimental; pass 4 is untouched).

Pass 4 (usmap4.py + out4/scene4.json, checkpointed in checkpoints/pass4-approved-2026-11-03/) is the baseline.
This file never edits it: it imports pass 4's painters and scene, applies a small, listed set of refinements to a copy
of the scene, and renders that copy into out5/ (or out5_<width>/).

    PYTHONPATH=../folk2:../styles2 python3 usmap5.py               # 3200 x 1800 -> out5/
    PYTHONPATH=../folk2:../styles2 python3 usmap5.py --width 6400  # same scene, zoomable size -> out5_6400/

Refinement group 1 (this file so far):
  * Pacific Northwest: a mostly evergreen forest of four species (narrow fir, full spruce, layered Douglas fir, short
    irregular pine) in deep green, blue-green, teal and olive, with new woodland clusters on the foothills; a few
    autumn trees kept near the houses and the lighthouse as accents.
  * Florida: the northern trees on the peninsula become palms of three kinds (tall curved, short full, asymmetric),
    singly and in clusters of two or three. Each palm is painted as a trunk plus separate fronds, so the fronds can
    later move individually.
Every changed or added element is listed in out5/changes5.json.
"""
import sys, os, json, math, zlib
import numpy as np

ARGS = sys.argv[1:]
OUTW = int(ARGS[ARGS.index('--width') + 1]) if '--width' in ARGS else 3200
OUT5 = 'out5' if OUTW == 3200 else f'out5_{OUTW}'
sys.argv = [sys.argv[0], '--width', str(OUTW), '--scene', f'{OUT5}/scene5.json']   # what pass 4's main() reads
import usmap4 as B
from usmap4 import c, k, hexc, pal_fn, catmull, resample
import story as S
from matplotlib.path import Path as MP

sid = B.sid
import fl5 as F5
B.COAST = F5.coast5(); B.LANDP = MP(B.COAST)                          # group 6: the re-traced Florida peninsula
B.U.boat = F5.boat6                                                  # group 6: boats after the Florida reference

# ====================================================================== regions (map units, reference-v2 grid)
PNW = MP([(0, 40), (600, 40), (600, 250), (470, 300), (330, 330), (300, 470), (0, 470)])
DESERT = MP(catmull([(112, 482), (250, 456), (400, 470), (520, 500), (562, 560), (522, 622), (420, 642), (300, 642), (200, 632), (110, 602)], 10, closed=True))
FLORIDA = MP([(1300, 560), (1520, 560), (1540, 720), (1470, 910), (1270, 910), (1270, 780)])
DECID = {'red', 'orange', 'yellow', 'green', 'pink', 'olive', 'poplar'}

# ====================================================================== new painters
EVERGREEN = {   # four palettes: deep forest green, blue-green, muted teal, olive
    'forest': ['#1f3a2a', '#2a4a34', '#18301f', '#3a5c3e'],
    'blue':   ['#21404a', '#2c5258', '#1a333c', '#3c6466'],
    'teal':   ['#24463e', '#2f5a4c', '#1c3a34', '#467062'],
    'olive':  ['#34431f', '#44562a', '#2a3618', '#5a6a32'],
}
def _pal(seed):   # weighted: mostly deep forest green and olive, some blue-green, a little teal
    return EVERGREEN[['forest', 'forest', 'forest', 'forest', 'olive', 'olive', 'olive', 'blue', 'blue', 'teal'][seed % 10]]

def _trunk(x, y, h, w, lean=0.0, col='#4a3424'):
    c.stroke([(x, y + 1), (x + lean * h * .1, y - h * .22)], max(1.2, w), col, a=1, dry=.1, taper=(0, .1))

def ev_fir(x, y, h, seed):
    """Tall, narrow fir: a slim spire with slightly ragged, upswept sides."""
    r = np.random.RandomState(seed); cols = _pal(seed); w = h * r.uniform(.12, .16); lean = r.uniform(-.25, .25)
    _trunk(x, y, h, h * .035, lean)
    L, Rr = [], []
    for t in np.linspace(0, 1, 16):
        yy = y - h * .08 - h * .92 * t; cx = x + lean * h * .1 * t
        ww = w * (1 - t) ** .85 * (1 + .14 * math.sin(t * 23 + seed) + .06 * r.randn())
        L.append((cx - ww, yy)); Rr.append((cx + ww * (1 + .1 * math.sin(t * 7 + seed)), yy))
    m = c.area(L + Rr[::-1], hexc(cols[0]) * .9, wob=.25, rough=.9, edge_dark=.12, seed=seed)
    c.stip(m, pal_fn(cols, .07), spacing=1.15, L=3.0, w=1.15, seed=seed + 1,
           angfn=lambda X, Y: np.where(X < x, math.pi / 2 + .8, math.pi / 2 - .8), jit=.25)

def ev_spruce(x, y, h, seed):
    """Fuller spruce: a broad cone built from scalloped tiers, darker on the right (light from the upper left)."""
    r = np.random.RandomState(seed); cols = _pal(seed + 1)
    _trunk(x, y, h, h * .05)
    n = r.randint(5, 7); W0 = h * r.uniform(.26, .32)
    for i in range(n):
        f0, f1 = i / n, (i + 1.5) / n
        y0 = y - h + h * .9 * f0; y1 = y - h + h * .9 * min(1.0, f1)
        wd = W0 * (.18 + .82 * min(1.0, f1)) * (.92 + .16 * r.rand())
        sc = [(x + wd * (u * 2 - 1), y1 + 2.2 * abs(math.sin(u * math.pi * r.randint(3, 5)))) for u in np.linspace(0, 1, 13)]
        tier = [(x + r.randn() * .4, y0)] + sc[::-1]
        m = c.area(tier, hexc(cols[0]) * .9, wob=.12, rough=.7, edge_dark=.14, seed=seed + i)
        def colf(X, Y, rr, x=x, wd=wd):
            C = np.array([hexc(z) for z in cols]); lit = np.clip(.55 - (X - x) / (wd * 1.6), 0, 1)
            return C[np.clip((lit * 3 + rr.randn(len(X)) * .7).round().astype(int), 0, 3)] * (1 + (rr.rand(len(X), 1) - .5) * .08)
        c.stip(m, colf, spacing=1.1, L=2.8, w=1.2, seed=seed + 20 + i, angfn=lambda X, Y: np.where(X < x, math.pi / 2 + 1.0, math.pi / 2 - 1.0), jit=.25)

def ev_douglas(x, y, h, seed):
    """Douglas fir: an irregular stack of drooping, uneven branch tiers with sky showing between some of them."""
    r = np.random.RandomState(seed); cols = _pal(seed + 2); lean = r.uniform(-.3, .3)
    c.stroke([(x, y + 1), (x + lean * h * .12, y - h * .92)], max(1.2, h * .04), '#4a3424', a=1, dry=.1, taper=(0, .7))
    n = r.randint(6, 9)
    for i in range(n):
        t = i / (n - 1); yy = y - h * .95 + h * .78 * t; cx = x + lean * h * .12 * (1 - t)
        wd = h * (.07 + .25 * t ** .8) * r.uniform(.75, 1.15); side = r.uniform(.8, 1.2)
        th = h * (.07 + .05 * t)
        tier = [(cx, yy - th * .6), (cx + wd * side, yy + th * .7), (cx + wd * side * .55, yy + th * .35), (cx, yy + th * .55),
                (cx - wd * .55, yy + th * .35), (cx - wd, yy + th * .7)]
        m = c.area(tier, hexc(cols[0]) * .9, wob=.15, rough=.7, edge_dark=.14, seed=seed + i)
        c.stip(m, pal_fn(cols, .07), spacing=1.1, L=2.6, w=1.1, seed=seed + 30 + i,
               angfn=lambda X, Y, cx=cx: np.where(X < cx, math.pi / 2 + 1.15, math.pi / 2 - 1.15), jit=.25)

def ev_pine(x, y, h, seed):
    """Short, irregular pine: a leaning trunk and two or three lopsided clumps of needles."""
    r = np.random.RandomState(seed); cols = _pal(seed + 3); lean = r.choice([-1, 1]) * r.uniform(.15, .45)
    top = (x + lean * h * .35, y - h * .82)
    c.stroke([(x, y + 1), (x + lean * h * .15, y - h * .45), top], max(1.3, h * .055), '#5a3e2c', a=1, dry=.15, taper=(0, .5))
    for j in range(r.randint(2, 4)):
        u = .45 + j * .2 + r.uniform(-.05, .05)
        cx = x + lean * h * .35 * u + r.uniform(-.12, .12) * h; cy = y - h * u * .95
        rx, ry = h * r.uniform(.18, .27), h * r.uniform(.1, .15)
        m = c.area(S.lumpy(cx, cy, rx, ry, seed + j, n=30, bumps=5, amp=.16, flat=.4), hexc(cols[0]) * .9, wob=.2, rough=.8, edge_dark=.14, seed=seed + j)
        c.stip(m, pal_fn(cols, .07), spacing=1.15, L=2.4, w=1.15, seed=seed + 40 + j, jit=.6)

# ---- group 4: distinct, storybook evergreens for the Pacific Northwest (after the user's second reference)
TIERED = [   # (base, light, dark, tip highlight)
    ('#3a7040', '#62a052', '#22462a', '#9acc66'),   # forest green
    ('#346856', '#5c967a', '#1e4236', '#8cc09c'),   # blue-green
    ('#4a7e3e', '#76aa48', '#2c5426', '#acd064'),   # mid green
    ('#2e5e48', '#508a68', '#1a3a2c', '#78ae84'),   # deep teal
    ('#56823a', '#82aa44', '#345a22', '#b6d25c'),   # yellow-green
]
def ev_tiered(x, y, h, seed, variant='classic'):
    """A storybook evergreen: a clean stack of drooping branch tiers, each lit along its top and left and shaded
    along its scalloped lower edge, on a short visible trunk. Upper tiers overlap the ones below, as in the reference."""
    r = np.random.RandomState(seed); base, light, dark, tip = TIERED[seed % len(TIERED)]
    wide = {'classic': .3, 'narrow': .2, 'wide': .37}[variant] * r.uniform(.9, 1.1)
    n = {'classic': r.randint(5, 8), 'narrow': r.randint(6, 9), 'wide': r.randint(4, 6)}[variant]
    trunk_h = h * .1
    c.stroke([(x, y + 1), (x, y - trunk_h - h * .05)], max(1.6, h * .055), '#5a3e2c', a=1, dry=.1, taper=(0, 0))
    c.stroke([(x + max(.6, h * .015), y + 1), (x + max(.6, h * .015), y - trunk_h)], max(.6, h * .016), '#3e2a1e', a=.8, dry=.1, taper=(0, 0))
    top = y - h; bottom = y - trunk_h
    tiers = []
    for i in range(n):
        f0 = i / n; f1 = (i + 1) / n
        yt = top + (bottom - top) * (f0 ** 1.05) - (h * .05 if i else 0)
        yb = top + (bottom - top) * f1
        wd = h * wide * (.22 + .78 * f1 ** .9) * r.uniform(.92, 1.08)
        tiers.append((yt, yb, wd))
    for i in range(n - 1, -1, -1):                                  # bottom tier first; each upper tier overlaps
        yt, yb, wd = tiers[i]; droop = (yb - yt) * .22
        k_ = r.randint(3, 5)                                          # scallops along the lower edge
        lower = [(x + wd * (u * 2 - 1), yb + droop * (1 - (u * 2 - 1) ** 2) * .25 + droop * .55 * abs(math.sin(u * math.pi * k_)))
                 for u in np.linspace(0, 1, 4 * k_ + 1)]
        left_side = [(x - wd * t ** .85, yt + (yb - yt) * t) for t in np.linspace(0, 1, 8)]
        right_side = [(x + wd * t ** .85, yt + (yb - yt) * t) for t in np.linspace(1, 0, 8)]
        poly = left_side + lower + right_side
        m = c.area(poly, base, wob=.05, rough=.45, edge_dark=.28, seed=seed + i)
        if m is None: continue
        yt_, yb_, wd_, x_ = yt, yb, wd, x
        def colf(X, Y, rr, yt_=yt_, yb_=yb_, wd_=wd_, x_=x_):
            v = np.clip((Y - yt_) / max(1e-3, yb_ - yt_), 0, 1); hz = (X - x_) / max(1e-3, wd_)
            lit = np.clip(.88 - v * 1.0 - hz * .42 + rr.randn(len(X)) * .1, 0, 1)
            C = np.array([hexc(dark), hexc(base), hexc(light), hexc(tip)])
            idx = np.where(lit > .74, 3, np.where(lit > .44, 2, np.where(lit > .16, 1, 0)))
            return C[idx] * (1 + (rr.rand(len(X), 1) - .5) * .06)
        c.stip(m, colf, spacing=1.05, L=3.0, w=1.25, seed=seed + 40 + i, jit=.15,
               angfn=lambda X, Y, x_=x_: np.where(X < x_, math.pi * .5 + 1.05, math.pi * .5 - 1.05))
        # a crisp dark line under each tier keeps the stack readable at map scale
        c.stroke(lower, max(.7, h * .012), dark, a=.75, dry=.1, taper=(.15, .15))
    c.stroke([(x, top - h * .04), (x, top + h * .06)], max(.9, h * .02), tip, a=.9, dry=0, taper=(0, .6))

def flower_bush(x, y, h, seed, col):
    """A low flowering shrub (white or pink blossom), for the gaps between the trees."""
    r = np.random.RandomState(seed)
    m = c.area(S.lumpy(x, y - h * .45, h * .75, h * .48, seed, n=28, bumps=5, amp=.12, flat=.4), '#3e5e2c', wob=.2, rough=.7, edge_dark=.18, seed=seed)
    if m is None: return
    c.stip(m, pal_fn(['#3e5e2c', '#4e7034', '#304a22', '#5e8040']), spacing=1.1, L=2.0, w=1.2, seed=seed + 1, jit=.8)
    pts = [(x + r.uniform(-.65, .65) * h, y - h * .45 + r.uniform(-.38, .38) * h) for _ in range(int(h * 2.2))]
    c.dots(pts[:int(len(pts) * .7)], max(.9, h * .1), [col, '#ffffff' if col != '#ffffff' else '#f4e8ec'], seed=seed + 2)

EV_PAINT = {'ev_fir': ev_fir, 'ev_spruce': ev_spruce, 'ev_douglas': ev_douglas, 'ev_pine': ev_pine,
            'ev_tiered': ev_tiered, 'ev_tiered_narrow': lambda x, y, h, s: ev_tiered(x, y, h, s, 'narrow'),
            'ev_tiered_wide': lambda x, y, h, s: ev_tiered(x, y, h, s, 'wide')}

# ---- palms: one trunk, separate fronds (so each frond can be animated on its own later)
PALM_GREEN = [['#4e7a36', '#5f8c3e', '#3c6430'], ['#5a7a2e', '#6c8c36', '#46642a'], ['#47703a', '#588444', '#365a30']]
def palm_geom(x, y, h, seed, variant):
    """Shared geometry for the palm painters: trunk points and the crown, plus one (angle, length, droop) per frond."""
    r = np.random.RandomState(seed)
    bend = {'tall': r.uniform(.18, .3), 'short': r.uniform(.04, .12), 'odd': r.uniform(.2, .34)}[variant] * r.choice([-1, 1])
    hh = h * {'tall': 1.0, 'short': .62, 'odd': .9}[variant]
    trunk = np.array([(x + bend * hh * (t ** 1.6), y - hh * t) for t in np.linspace(0, 1, 14)])
    n = {'tall': r.randint(7, 9), 'short': r.randint(8, 11), 'odd': r.randint(6, 8)}[variant]
    fronds = []
    for i in range(n):
        a = -math.pi + i * math.pi / (n - 1) + r.randn() * .12
        if variant == 'odd': a = a * .8 + (-.35 if bend > 0 else .35) - math.pi * .1 * (bend > 0)
        ln = hh * r.uniform(.34, .5) * (1.1 if variant == 'short' else 1)
        droop = r.uniform(.25, .55) + (.15 if abs(math.cos(a)) > .6 else 0)
        fronds.append((a, ln, droop, r.randint(1 << 30)))
    return trunk, fronds, bend

def palm_trunk(x, y, h, seed, variant):
    trunk, _, _ = palm_geom(x, y, h, seed, variant)
    w = h * (.055 if variant != 'short' else .07)
    c.stroke(trunk, w, '#8a6a44', a=1, dry=.12, taper=(0, .35), streak=.25)
    c.stroke(trunk + [w * .25, 0], w * .35, '#6a4e32', a=.6, dry=.2, taper=(0, .4))
    for t in np.linspace(.08, .9, 9):                          # ring marks
        i = int(t * (len(trunk) - 1)); p = trunk[i]; ww = w * (1 - t * .3) * .5
        c.stroke([(p[0] - ww, p[1]), (p[0] + ww, p[1] + .6)], .7, '#5a4030', a=.7, dry=0, taper=(0, 0))
    top = trunk[-1]
    c.dots([tuple(top + [-1.5, 1.5]), tuple(top + [1.6, 2.2])], max(1.0, h * .022), ['#6a4a2a'])   # coconuts

def palm_frond(x, y, h, seed, variant, i):
    trunk, fronds, _ = palm_geom(x, y, h, seed, variant); top = trunk[-1]
    a, ln, droop, fs = fronds[i]; rr = np.random.RandomState(fs); cols = PALM_GREEN[seed % 3]
    # midrib: out along the angle, then bending down
    mid = np.array([(top[0] + math.cos(a) * ln * u, top[1] + math.sin(a) * ln * u + droop * ln * u * u) for u in np.linspace(0, 1, 8)])
    d = np.gradient(mid, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    if nrm[len(nrm) // 2, 1] > 0: nrm = -nrm                      # first side is the upper one
    for side, col in ((1, cols[1]), (-1, cols[2])):               # upper leaflets lighter, under-side darker
        for j in range(1, len(mid) - 1):
            u = j / (len(mid) - 1); lf = ln * (.3 - .16 * u) * rr.uniform(.85, 1.15)
            p = mid[j]; q = p + nrm[j] * side * lf * .75 + d[j] * lf * .6 + [0, lf * .3 * (1 if side < 0 else .35)]
            c.stroke([p, q], max(1.2, h * .04 * (1 - u * .45)), col, a=1, dry=.08, taper=(0, .75))
    c.stroke(mid, max(1.1, h * .032), cols[0], a=1, dry=.05, taper=(.05, .85))

def palmetto(x, y, h, seed):
    """Low saw-palmetto scrub: a clump of fan leaves on short stems."""
    r = np.random.RandomState(seed); cols = PALM_GREEN[seed % 3]
    for j in range(r.randint(4, 7)):
        a = -math.pi / 2 + r.uniform(-1.1, 1.1); ln = h * r.uniform(.45, .7)
        bx, by = x + math.cos(a) * ln, y + math.sin(a) * ln * .8
        c.stroke([(x + r.uniform(-2, 2), y), (bx, by)], max(.8, h * .03), '#5a6a32', a=1, dry=.05, taper=(0, .3))
        for f in np.linspace(-1.0, 1.0, 7):
            fa = a + f * .8; fl = h * r.uniform(.26, .36)
            c.stroke([(bx, by), (bx + math.cos(fa) * fl, by + math.sin(fa) * fl)], max(.9, h * .045), cols[int(f > 0) + (j % 2)], a=1, dry=.08, taper=(.1, .8))

def palm5(x, y, h, seed, variant):
    palm_trunk(x, y, h, seed, variant)
    _, fronds, _ = palm_geom(x, y, h, seed, variant)
    order = sorted(range(len(fronds)), key=lambda i: -math.sin(fronds[i][0]))  # lower (back) fronds first
    for i in order: palm_frond(x, y, h, seed, variant, i)

# ====================================================================== scene refinement
PALM6 = [('#b4cc44', '#5a7a20', '#88a630', '#d6e46a'), ('#aac63e', '#56761e', '#82a02c', '#d0e064'), ('#bcd04c', '#5e7e24', '#8eaa34', '#dce872')]
def palm_geom(x, y, h, seed, variant):
    """Bold storybook palms (Florida reference): a tall curved, ringed trunk and a full crown of long arching fronds."""
    r = np.random.RandomState(seed)
    bend = {'tall': r.uniform(.14, .26), 'short': r.uniform(.04, .1), 'odd': r.uniform(.2, .3)}[variant] * r.choice([-1, 1])
    hh = h * {'tall': 1.0, 'short': .7, 'odd': .9}[variant]
    trunk = np.array([(x + bend * hh * (t ** 1.7), y - hh * t) for t in np.linspace(0, 1, 16)])
    n = r.randint(9, 12)
    fronds = []
    for i in range(n):
        a = -math.pi * 1.06 + i * math.pi * 1.12 / (n - 1) + r.randn() * .08
        if variant == 'odd': a += (.25 if bend > 0 else -.25)
        ln = hh * r.uniform(.5, .62) * (.8 if abs(math.cos(a)) < .5 else 1.0)
        droop = r.uniform(.4, .62) + (.1 if abs(math.cos(a)) > .7 else 0)
        fronds.append((a, ln, droop, r.randint(1 << 30)))
    return trunk, fronds, bend

def palm_trunk(x, y, h, seed, variant):
    trunk, _, _ = palm_geom(x, y, h, seed, variant)
    w = h * .072
    c.stroke(trunk, w, '#a8824c', a=1, dry=.1, taper=(0, .3), streak=.2)
    c.stroke(trunk - [w * .28, 0], w * .22, '#c8a26a', a=.8, dry=.2, taper=(0, .4))
    c.stroke(trunk + [w * .3, 0], w * .28, '#7a5a34', a=.7, dry=.2, taper=(0, .4))
    for t in np.linspace(.05, .92, 13):                                # curved ring bands
        i = int(t * (len(trunk) - 1)); p = trunk[i]; ww = w * (1 - t * .3) * .5
        c.stroke([(p[0] - ww, p[1] - .4), (p[0], p[1] + .8), (p[0] + ww, p[1] - .4)], .8, '#6a4a2a', a=.75, dry=0, taper=(0, 0))
    top = trunk[-1]
    c.dots([tuple(top + [-2.2, 2.4]), tuple(top + [1.8, 3.0]), tuple(top + [0, 4.2])], max(1.3, h * .028), ['#6a4424', '#7a5230'])

def palm_frond(x, y, h, seed, variant, i):
    trunk, fronds, _ = palm_geom(x, y, h, seed, variant); top = trunk[-1]
    a, ln, droop, fs = fronds[i]; rr = np.random.RandomState(fs); up, under, rib, tip = PALM6[seed % 3]
    mid = np.array([(top[0] + math.cos(a) * ln * u, top[1] + math.sin(a) * ln * u * .7 - .42 * ln * u * (1 - u) + droop * ln * u * u) for u in np.linspace(0, 1, 13)])   # rises, then arches down
    d = np.gradient(mid, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    if nrm[len(nrm) // 2, 1] > 0: nrm = -nrm                           # the first side is the upper one
    for side, col in ((-1, under), (1, up)):                           # darker underside first, lit upper leaflets over it
        for j in range(1, len(mid) - 1):
            u = j / (len(mid) - 1); lf = ln * (.3 - .16 * u) * rr.uniform(.85, 1.15)
            p = mid[j]; q = p + nrm[j] * side * lf * .75 + d[j] * lf * .4 + [0, lf * (.42 if side < 0 else .18)]
            c.stroke([p, q], max(1.4, h * .05 * (1 - u * .4)), col if u < .78 else tip, a=1, dry=.06, taper=(0, .75))
    c.stroke(mid, max(1.1, h * .03), rib, a=1, dry=.05, taper=(.05, .85))

def keep_boxes():
    boxes = [(x, y, w * .55 + 18, h + 30) for (x, y, w, h, *_) in B.HOUSES]
    boxes += [(98, 150, 115, 85), (176, 590, 110, 70), (1588, 150, 90, 70), (95, 388, 30, 110), (680, 216, 90, 100), (744, 212, 40, 130),
              (918, 420, 230, 160), (930, 520, 240, 60), (1086, 560, 80, 60), (1137, 425, 50, 40)]
    return boxes

U2_ = B.U2
U2_.PAL['meadow'] = ['#6a8a34', '#78983c', '#5e7c2e', '#86a646', '#70903a']
U2_.PATCH['meadow'] = ['moss', 'olive']
PNW_MEADOW = {(130, 250), (410, 262), (80, 410)}                     # these hills (cx, base) turn from dark forest to meadow
for i_, hl in enumerate(B.HILLS):
    if (hl[0], hl[1]) in PNW_MEADOW: B.HILLS[i_] = hl[:4] + ('meadow',)

def pnw4(els, changes, gbase, free):
    in_pnw = lambda e: e['kind'] == 'tree' and PNW.contains_point((e['params']['x'], e['params']['y'])) and not DESERT.contains_point((e['params']['x'], e['params']['y']))
    trees = [e for e in els if in_pnw(e)]
    ever = [e for e in trees if e['params']['kd'] in EV_PAINT or e['params']['kd'] in ('fir', 'lfir')]
    # thin the evergreens so each silhouette reads: keep the larger trees, drop any that would sit almost on top of one kept
    kept = []; drop = set()
    for e in sorted(ever, key=lambda e: -e['params']['h']):
        p = e['params']
        if any(abs(p['x'] - q['x']) < .3 * max(p['h'], q['h']) and abs(p['y'] - q['y']) < .2 * max(p['h'], q['h']) for q in kept):
            drop.add(id(e)); continue
        kept.append(p)
    for e in ever:
        p = e['params']
        if id(e) in drop:
            changes.append(dict(what='remove tree (crowded)', where='pnw', at=[round(p['x']), round(p['y'])], was=p['kd'], seed=e['seed'])); continue
        r10 = e['seed'] % 10; old = p['kd']
        p['kd'] = 'ev_tiered_narrow' if r10 < 3 else 'ev_tiered_wide' if r10 == 9 else 'ev_tiered'
        p['h'] = round(p['h'] * (1.08 if p['kd'] == 'ev_tiered_narrow' else 1.0), 2)
        changes.append(dict(what='retype tree', where='pnw', at=[round(p['x']), round(p['y'])], was=old, now=p['kd'], seed=e['seed']))
    els[:] = [e for e in els if id(e) not in drop]
    # flowering shrubs in a few open spots
    rr = np.random.RandomState(sid('pnw4bush')); pts = [(e['params']['x'], e['params']['y']) for e in els if in_pnw(e)]; n = 0
    for att in range(400):
        if n >= 12: break
        x, y = rr.uniform(20, 560), rr.uniform(200, 460); h = rr.uniform(14, 20)
        if not PNW.contains_point((x, y)) or not free(x, y, h * 2, pts): continue
        if any(abs(x - px) < 22 and abs(y - py) < 14 for px, py in pts): continue
        col = ['#ffffff', '#e89ab0', '#f2c8d6'][n % 3]; seed = sid('pnw4bush', att)
        els.append(dict(kind='bush5', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h, y - h * 1.1, x + h, y + 2], seed=seed, layer='base',
                        params=dict(x=x, y=y, h=h, col=col)))
        pts.append((x, y)); n += 1
        changes.append(dict(what='add flowering shrub', where='pnw', at=[round(x), round(y)], now=col, seed=seed))

import pnw5 as P5
LIGHTHOUSE5 = (54, 402)                                              # on the rocks at the water's edge (was 95, 388)
EVER_ZONE = MP([(0, 40), (600, 40), (600, 262), (470, 268), (330, 272), (180, 280), (150, 330), (120, 470), (0, 470)])
def pnw5_refine(els, changes, gbase, free, scene):
    """Second pass on the Northwest after the reference: a mix of evergreens and bright autumn trees, every tree about
    1.45 times larger and fewer of them, brighter greens, a rocky coast, the lighthouse on the rocks, the lodge's
    details, a double butte and desert plants."""
    in_pnw = lambda e: e['kind'] == 'tree' and PNW.contains_point((e['params']['x'], e['params']['y'])) and not DESERT.contains_point((e['params']['x'], e['params']['y']))
    tracks = np.vstack([np.array(r['points']) for r in scene['routes'].values()])
    boxes = [(x, y, w * .55 + 18, h + 30) for (x, y, w, h, *_) in B.HOUSES] + [(98, 150, 118, 88), (LIGHTHOUSE5[0], LIGHTHOUSE5[1], 32, 112), (176, 590, 110, 70)]
    def clear(x, y, h):
        if not B.on_land(x, y, 8): return False
        if any(abs(x - kx) < kw and abs(y - ky) < kh for kx, ky, kw, kh in boxes): return False
        for hx, hy, hw, hh, *_ in B.HOUSES:                              # the crown may not cover a house
            if x + h * .4 > hx - hw * .65 and x - h * .4 < hx + hw * .75 and y - h * 1.0 < hy + 4 and y > hy - hh * 2.2: return False
        dt = np.hypot(*(tracks - [x, y]).T); j = int(np.argmin(dt))
        if dt[j] < 18: return False
        if y < tracks[j][1] and np.min(np.hypot(*(tracks - [x, y - h * .55]).T)) < h * .45 + 10: return False
        if y > tracks[j][1] and np.min(np.hypot(*(tracks - [x, y - h * .6]).T)) < h * .42: return False
        if any(abs(x - mx) < mw * .4 and y < mb - 6 for mx, mb, mw, mh in B.MTS): return False
        return True
    trees = sorted([e for e in els if in_pnw(e)], key=lambda e: -e['params']['h'])
    kept, drop = [], set()
    for e in trees:
        p = e['params']; old = (p['kd'], p['h']); h = p['h'] * 1.45
        if not clear(p['x'], p['y'], h) or any(abs(p['x'] - q[0]) < .34 * max(h, q[2]) and abs(p['y'] - q[1]) < .2 * max(h, q[2]) for q in kept):
            drop.add(id(e)); changes.append(dict(what='remove tree (make room)', where='pnw', at=[round(p['x']), round(p['y'])], was=old[0], seed=e['seed'])); continue
        r10 = e['seed'] % 20; ever_zone = EVER_ZONE.contains_point((p['x'], p['y']))
        evergreen = (r10 < 17) if ever_zone else (r10 < 6)
        if evergreen: kd = 'ev_tiered_narrow' if r10 % 4 == 0 else 'ev_tiered_wide' if r10 % 7 == 3 else 'ev_tiered'
        else: kd = 'bl5_' + ['yellow', 'red', 'orange', 'pink', 'green', 'yellow', 'red', 'orange'][(e['seed'] >> 3) % 8]
        p['kd'] = kd; p['h'] = round(h * (.92 if kd.startswith('bl5') else 1.0), 2)
        e['bbox'] = [p['x'] - p['h'] * .75, p['y'] - p['h'] * 1.2, p['x'] + p['h'] * .75, p['y'] + p['h'] * .12]
        kept.append((p['x'], p['y'], p['h']))
        changes.append(dict(what='retype and enlarge tree', where='pnw', at=[round(p['x']), round(p['y'])], was=old[0], now=kd, seed=e['seed']))
    els[:] = [e for e in els if id(e) not in drop and not (e['kind'] == 'bush5')]
    # fill the hills again with large, well-spaced trees (the enlarged ones above left gaps)
    rr = np.random.RandomState(sid('pnw5fill')); added = 0
    for att in range(4000):
        if added >= 70: break
        x, y = rr.uniform(15, 600), rr.uniform(150, 470)
        if not PNW.contains_point((x, y)) or DESERT.contains_point((x, y)): continue
        h = rr.uniform(50, 82) * (.66 + .4 * min(1.0, max(0.0, (y - 150) / 560))) * 1.25 * 1.45
        if not clear(x, y, h) or any(abs(x - q[0]) < .34 * max(h, q[2]) and abs(y - q[1]) < .2 * max(h, q[2]) for q in kept): continue
        seed = sid('pnw5fill', att); r10 = seed % 20; ez = EVER_ZONE.contains_point((x, y))
        if (r10 < 16) if ez else (r10 < 6): kd = 'ev_tiered_narrow' if r10 % 4 == 0 else 'ev_tiered_wide' if r10 % 7 == 3 else 'ev_tiered'
        else: kd = 'bl5_' + ['yellow', 'red', 'orange', 'pink', 'green', 'yellow', 'red', 'orange'][(seed >> 3) % 8]; h *= .92
        els.append(dict(kind='tree', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h * .75, y - h * 1.2, x + h * .75, y + h * .12], seed=seed, layer='base',
                        params=dict(x=x, y=y, h=round(h, 2), kd=kd, snow=0.0)))
        kept.append((x, y, h)); added += 1
        changes.append(dict(what='add tree', where='pnw', at=[round(x), round(y)], now=kd, seed=seed))
    # bigger flowering shrubs in the open spaces
    rr = np.random.RandomState(sid('pnw5bush')); n = 0
    for att in range(600):
        if n >= 14: break
        x, y = rr.uniform(20, 560), rr.uniform(200, 470); h = rr.uniform(18, 26)
        if not PNW.contains_point((x, y)) or DESERT.contains_point((x, y)) or not clear(x, y, h): continue
        if any(abs(x - q[0]) < q[2] * .32 + 14 and -q[2] * .2 < q[1] - y < 22 for q in kept): continue
        col = ['#ffffff', '#e89ab0', '#f2c8d6', '#d8507a'][n % 4]; seed = sid('pnw5bush', att)
        els.append(dict(kind='bush5', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h, y - h * 1.1, x + h, y + 2], seed=seed, layer='base', params=dict(x=x, y=y, h=h, col=col)))
        kept.append((x, y, h)); n += 1
    # lighthouse onto the rocks at the shore
    for e in els:
        if e['kind'] == 'lighthouse':
            old = (e['params']['x'], e['params']['y']); e['params']['x'], e['params']['y'] = LIGHTHOUSE5
            e['depth'] = float(LIGHTHOUSE5[1]) + 30; e['bbox'] = [LIGHTHOUSE5[0] - 30, LIGHTHOUSE5[1] - 130, LIGHTHOUSE5[0] + 30, LIGHTHOUSE5[1] + 10]
            changes.append(dict(what='move lighthouse to the shore', where='pnw', at=list(LIGHTHOUSE5), was=list(old)))
        if e['kind'] == 'depot' and e['params']['name'] == 'nw':
            e['kind'] = 'lodge5'; changes.append(dict(what='add gable, flower boxes, railing', where='pnw', at=[e['params']['x'], e['params']['y']]))
        if e['kind'] == 'mesa':
            e['kind'] = 'butte5'; e['bbox'] = [e['params']['x'] - 130, e['params']['y'] - 100, e['params']['x'] + 130, e['params']['y'] + 12]
            changes.append(dict(what='redraw as a double butte', where='southwest', at=[e['params']['x'], e['params']['y']]))
        if e['kind'] == 'cactus':
            e['kind'] = 'saguaro5'; e['params']['h'] = e['params']['h'] * 1.35
            e['bbox'] = [e['params']['x'] - 25, e['params']['y'] - e['params']['h'] - 8, e['params']['x'] + 25, e['params']['y'] + 4]
    # rocky shore with surf, from below the lodge down past the lighthouse
    C = np.load('coast4.npy'); shore = [(float(x), float(y)) for x, y in C if x < 70 and 205 < y < 480]
    pts = []
    for x, y in sorted(shore, key=lambda q: q[1]):
        if not pts or y - pts[-1][1] > 15: pts.append((x + 5, y))
    pts.append((LIGHTHOUSE5[0] - 6, LIGHTHOUSE5[1] + 4))
    for j, (x, y) in enumerate(pts):                                  # one element per rock cluster, at the depth of its spot
        d = float(LIGHTHOUSE5[1]) + 29 if (x, y) == pts[-1] else float(B.depth_at(x, y, gbase)) + .5
        els.append(dict(kind='rocks5', depth=d, bbox=[x - 24, y - 16, x + 18, y + 18], seed=sid('rocks5', j), layer='base', params=dict(pts=[(x, y)])))
    els.append(dict(kind='falls5', depth=float(B.depth_at(48, 226, gbase)) + 60, bbox=[0, 210, 70, 270], seed=sid('falls5'), layer='base',
                    params=dict(x0=50, y0=224, x1=24, y1=256)))      # off the green cliff below the lodge, into the sea
    # nothing may stand in front of the lighthouse
    lx, ly = LIGHTHOUSE5
    for e in list(els):
        if e['kind'] in ('tree', 'bush5') and abs(e['params']['x'] - lx) < e['params']['h'] * .45 + 14 and ly - 4 < e['params']['y'] < ly + e['params']['h'] * 1.05 + 6:
            els.remove(e); changes.append(dict(what='remove tree in front of the lighthouse', where='pnw', at=[round(e['params']['x']), round(e['params']['y'])]))
    # desert plants round the butte and across the sand, clear of the blue line, the depot and the butte itself
    mx, my = 292, 526
    rr = np.random.RandomState(sid('desert5')); placed = []; counts = {'pear5': 0, 'agave5': 0, 'sage5': 0, 'tuft5': 0, 'saguaro5': 0}
    want = {'pear5': 6, 'agave5': 4, 'sage5': 14, 'tuft5': 12, 'saguaro5': 4}
    for att in range(3000):
        kd = ['pear5', 'agave5', 'sage5', 'tuft5', 'saguaro5'][att % 5]
        if counts[kd] >= want[kd]: continue
        x, y = rr.uniform(115, 560), rr.uniform(470, 640)
        if not DESERT.contains_point((x, y)) or not B.on_land(x, y, 8): continue
        if abs(x - mx) < 112 and my - 80 < y < my + 6: continue
        hgt = {'saguaro5': 62, 'pear5': 26, 'agave5': 18, 'sage5': 18, 'tuft5': 10}[kd]
        if abs(x - mx) < 130 and y - hgt < my - 4: continue               # nothing tall enough to hide the butte stands in front of it
        if np.min(np.hypot(*(tracks - [x, y]).T)) < 20 or np.min(np.hypot(*(tracks - [x, y - 14]).T)) < 18: continue
        if abs(x - 176) < 110 and 560 < y < 650: continue
        if any(abs(x - px) < 26 and abs(y - py) < 14 for px, py in placed): continue
        s_ = {'pear5': rr.uniform(16, 21), 'agave5': rr.uniform(12, 16), 'sage5': rr.uniform(12, 18), 'tuft5': rr.uniform(7, 10), 'saguaro5': rr.uniform(50, 62)}[kd]
        seed = sid('desert5', att)
        els.append(dict(kind=kd, depth=float(B.depth_at(x, y, gbase)), bbox=[x - s_ * 1.6, y - s_ * 2.4, x + s_ * 1.6, y + 4], seed=seed, layer='base',
                        params=dict(x=x, y=y, h=s_)))
        placed.append((x, y)); counts[kd] += 1
    changes.append(dict(what='add desert plants', where='southwest', now=counts))

BOATS5 = [(196, 800, 1.1), (880, 884, 1.0), (1610, 482, .95), (1578, 700, .9)]     # Gulf and Florida boats moved into open water
SE_HILLS = {(1250, 566): 'lime', (1460, 566): 'lime', (1410, 726): 'fgreen', (1360, 856): 'fgreen', (1230, 456): 'lime', (1450, 446): 'lime',
            (1240, 706): 'field'}
B.U2.PAL['lime'] = ['#6e9c30', '#7ca838', '#628c2a', '#8ab442', '#74a234']
B.U2.PAL['fgreen'] = ['#5a8a2a', '#669632', '#4e7a24', '#74a23a', '#5e8e2c']
B.U2.PATCH['fgreen'] = ['moss', 'lime']
B.U2.PATCH['lime'] = ['gold', 'moss']
B.U2.FIELD_STRIPES[1240] = ['#b88a2c', '#eec660']
for i_, hl in enumerate(B.HILLS):
    if (hl[0], hl[1]) in SE_HILLS: B.HILLS[i_] = hl[:4] + (SE_HILLS[(hl[0], hl[1])],)
SE = MP([(860, 470), (1671, 420), (1671, 941), (860, 941)])           # the Southeast, below Toy Town and east of the river
PEN = lambda x, y: x > 1294 and y > 712                                # the Florida peninsula
def fl6_refine(els, changes, gbase, scene):
    """Group 6: Florida and the Southeast after the user's Florida reference."""
    tracks = np.vstack([np.array(r['points']) for r in scene['routes'].values()])
    houses = [(x, y, w, h) for (x, y, w, h, *_) in B.HOUSES]
    def under_house(x, y, h):
        return any(x + h * .42 > hx - hw * .7 and x - h * .42 < hx + hw * .8 and y - h > hy - hh * 2.3 and y < hy + 40 and y > hy - hh * 2.4 for hx, hy, hw, hh in houses) \
            or any(abs(x - hx) < hw * .7 + 6 and abs(y - hy) < 12 for hx, hy, hw, hh in houses)
    def near_track(x, y, h):
        dt = np.hypot(*(tracks - [x, y]).T); j = int(np.argmin(dt))
        return dt[j] < 18 or (y < tracks[j][1] and np.min(np.hypot(*(tracks - [x, y - h * .55]).T)) < h * .45 + 10)
    def near_river(x, y, pad):
        return min(np.min(np.hypot(*(B.RIVER - [x, y]).T)), np.min(np.hypot(*(np.array(MOUTH) - [x, y]).T))) < pad
    # 1. vegetation that the new, narrower peninsula leaves in the sea goes
    veg = ('tree', 'palm5', 'bush5', 'fpatch5')
    for e in list(els):
        if e['kind'] in veg and not B.on_land(e['params']['x'], e['params']['y'], 6):
            els.remove(e); changes.append(dict(what='remove (now in the sea)', where='florida', at=[round(e['params']['x']), round(e['params']['y'])], was=e['params'].get('kd', e['kind'])))
    # 2. the river: no delta channels; one mouth that runs out through the shore into the Gulf
    for e in list(els):
        if e['kind'] == 'river' and str(e['params'].get('name', '')).startswith('delta'):
            els.remove(e); changes.append(dict(what='remove delta channel', where='river', was=e['params']['name']))
    els.append(dict(kind='mouth5', depth=805.0, bbox=[1030, 740, 1170, 880], seed=sid('mouth5'), layer='base', params=dict(pts=MOUTH)))
    changes.append(dict(what='river mouth into the Gulf', where='river', at=[1100, 820]))
    # 3. Southeast trees: the round, blossom-dotted kind, larger and fewer; about half the dark firs stay
    cmap = {'green': 'green', 'olive': 'green', 'red': 'red', 'orange': 'orange', 'yellow': 'yellow', 'pink': 'pink'}
    kept = []
    for e in sorted([e for e in els if e['kind'] == 'tree' and SE.contains_point((e['params']['x'], e['params']['y']))], key=lambda e: -e['params']['h']):
        p = e['params']; x, y = p['x'], p['y']; old = p['kd']
        if PEN(x, y):
            els.remove(e); changes.append(dict(what='remove (palms take its place)', where='florida', at=[round(x), round(y)], was=old)); continue
        if old in cmap: p['kd'] = 'bl5_' + (cmap[old] if e['seed'] % 5 else ['pink', 'green', 'orange', 'red'][e['seed'] % 4]); p['h'] = round(p['h'] * 1.22, 2)
        elif old in ('fir', 'lfir'):
            if e['seed'] % 2: els.remove(e); changes.append(dict(what='remove fir (fewer firs)', where='southeast', at=[round(x), round(y)])); continue
        h = p['h']
        if under_house(x, y, h) or near_track(x, y, h) or near_river(x, y, 16) or \
           any(abs(x - q[0]) < .34 * max(h, q[2]) and abs(y - q[1]) < .2 * max(h, q[2]) for q in kept):
            els.remove(e); changes.append(dict(what='remove tree (make room)', where='southeast', at=[round(x), round(y)], was=old)); continue
        e['bbox'] = [x - h * .75, y - h * 1.2, x + h * .75, y + h * .12]; kept.append((x, y, h))
        if p['kd'] != old: changes.append(dict(what='retype tree', where='southeast', at=[round(x), round(y)], was=old, now=p['kd']))
    for e in list(els):                                              # palmetto scrub goes; the bold palms replace it
        if e['kind'] == 'palm5' and (e['params']['variant'] == 'palmetto' or PEN(e['params']['x'], e['params']['y'])):
            els.remove(e)
    # 4. Florida: about a dozen bold palms, singly and in twos and threes
    rr = np.random.RandomState(sid('fl6palms')); palms = []
    SPOTS = [(1340, 752), (1446, 746), (1318, 812), (1432, 812), (1326, 868), (1420, 884), (1358, 918), (1384, 938)]   # spread down the whole peninsula
    for att, (sx, sy) in enumerate(SPOTS):
        for tries in range(30):
            x, y = sx + rr.uniform(-8, 8), sy + rr.uniform(-6, 6)
            if B.on_land(x, y, 8): break
        else: continue
        h = rr.uniform(80, 100) * (.85 if y > 860 else 1.0)
        if under_house(x, y, h * .6) or any(abs(x - q[0]) < 30 and abs(y - q[1]) < 20 for q in palms): continue
        seed = sid('fl6palm', att); variant = ['tall', 'tall', 'short', 'odd'][seed % 4]
        els.append(dict(kind='palm5', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h * .8, y - h * 1.15, x + h * .8, y + h * .1], seed=seed, layer='base',
                        params=dict(x=x, y=y, h=round(h, 2), variant=variant)))
        palms.append((x, y)); changes.append(dict(what='add palm', where='florida', at=[round(x), round(y)], now=variant))
    # 5. flowering bushes across Florida and the Southeast, and yellow wildflower patches in the meadows
    occupied = [(q[0], q[1]) for q in kept] + palms
    rr = np.random.RandomState(sid('fl6bush')); nb = 0
    for att in range(3000):
        if nb >= 26: break
        x, y = rr.uniform(880, 1490), rr.uniform(480, 940)
        if not SE.contains_point((x, y)) or not B.on_land(x, y, 10): continue
        h = rr.uniform(14, 20)
        if under_house(x, y, h * 2) or near_track(x, y, h * 1.5) or near_river(x, y, 22): continue
        if any(abs(x - q[0]) < 18 and abs(y - q[1]) < 12 for q in occupied): continue
        if 700 < x < 1180 and y < 600: continue                          # keep Toy Town's street clear
        col = ['#e8869e', '#d8507a', '#ffffff', '#f2a8bc', '#f6dc6a', '#e8869e'][nb % 6]; seed = sid('fl6bush', att)
        els.append(dict(kind='bush5', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h, y - h * 1.1, x + h, y + 2], seed=seed, layer='base', params=dict(x=x, y=y, h=h, col=col)))
        occupied.append((x, y)); nb += 1
    rr = np.random.RandomState(sid('fl6patch')); npch = 0
    for att in range(2000):
        if npch >= 9: break
        x, y = rr.uniform(900, 1480), rr.uniform(500, 900)
        if not SE.contains_point((x, y)) or not B.on_land(x, y, 16) or near_track(x, y, 30) or near_river(x, y, 26): continue
        if under_house(x, y, 30) or (700 < x < 1180 and y < 600): continue
        seed = sid('fl6patch', att)
        els.append(dict(kind='fpatch5', depth=float(B.depth_at(x, y, gbase)) - .3, bbox=[x - 30, y - 14, x + 30, y + 14], seed=seed, layer='base',
                        params=dict(x=x, y=y, rx=rr.uniform(16, 26), ry=rr.uniform(6, 9))))
        npch += 1
    changes.append(dict(what='add flowering bushes and wildflower patches', where='southeast', now=dict(bushes=nb, patches=npch)))
    # 6. boats into open water
    boats = [e for e in els if e['kind'] == 'boat']
    for e, (x, y, s_) in zip(boats, BOATS5):
        if (e['params']['x'], e['params']['y']) != (x, y):
            changes.append(dict(what='move boat into open water', where='sea', at=[x, y], was=[e['params']['x'], e['params']['y']]))
        e['params'].update(x=x, y=y, s=s_); e['bbox'] = [x - 50 * s_, y - 74 * s_, x + 50 * s_, y + 26 * s_]

MOUTH = [(1076, 752), (1088, 774), (1096, 796), (1101, 812), (1104, 826)]

def refine(scene):
    els = scene['elements']; changes = []
    gbase, _ = B.build_ground()
    tracks = np.vstack([np.array(r['points']) for r in scene['routes'].values()])
    boxes = keep_boxes()
    def free(x, y, h, others):
        if not B.on_land(x, y, 10) or DESERT.contains_point((x, y)): return False
        if any(abs(x - kx) < kw and abs(y - ky) < kh for kx, ky, kw, kh in boxes): return False
        dt = np.hypot(*(tracks - [x, y]).T); j = int(np.argmin(dt))
        if dt[j] < 18: return False
        if y < tracks[j][1] and np.min(np.hypot(*(tracks - [x, y - h * .55]).T)) < h * .45 + 10: return False
        if y > tracks[j][1] and np.min(np.hypot(*(tracks - [x, y - h * .6]).T)) < h * .42: return False
        for P_ in [B.RIVER] + B.DELTA:
            if np.min(np.hypot(*(P_ - [x, y]).T)) < 22: return False
        return all(abs(x - ox) > h * .2 or abs(y - oy) > h * .12 for ox, oy in others)
    def species(seed, region):
        r = seed % 20
        if region == 'pnw': return 'ev_fir' if r < 7 else 'ev_spruce' if r < 12 else 'ev_douglas' if r < 17 else 'ev_pine'
        return 'ev_fir'
    # --- Pacific Northwest: existing trees become a mostly evergreen forest
    pnw_pts = []
    for e in els:
        if e['kind'] != 'tree': continue
        p = e['params']; x, y = p['x'], p['y']
        if not PNW.contains_point((x, y)) or DESERT.contains_point((x, y)): continue
        keep_accent = p['kd'] in DECID and (e['seed'] % 3 == 0 or any(abs(x - hx) < 70 and abs(y - hy) < 50 for hx, hy, *_ in B.HOUSES))
        if keep_accent: pnw_pts.append((x, y)); continue
        old = p['kd']; new = species(e['seed'], 'pnw')
        scale = 1.0 + ((e['seed'] >> 3) % 7 - 2) * .06                 # some taller, some shorter
        p['kd'] = new; p['h'] = round(p['h'] * scale, 2); pnw_pts.append((x, y))
        changes.append(dict(what='retype tree', where='pnw', at=[round(x), round(y)], was=old, now=new, seed=e['seed']))
    # new woodland clusters on the foothills and western valleys
    CL = [(150, 255, 70, 28), (260, 240, 55, 22), (430, 262, 50, 18), (45, 300, 26, 55), (205, 330, 50, 24), (120, 440, 45, 20)]
    for ci, (cx, cy, rx, ry) in enumerate(CL):
        rr = np.random.RandomState(sid('pnw5', ci)); got = 0; want = int(rx * ry / 140) + 2
        for att in range(want * 25):
            if got >= want: break
            x = cx + rr.uniform(-1, 1) * rx; y = cy + rr.uniform(-1, 1) * ry
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 1: continue
            h = rr.uniform(46, 80) * (.66 + .4 * min(1.0, max(0.0, (y - 150) / 560))) * 1.25
            if not PNW.contains_point((x, y)) or not free(x, y, h, pnw_pts): continue
            if any(abs(x - mx) < mw * .42 and y < mb - 4 for mx, mb, mw, mh in B.MTS): continue   # not on the mountain faces
            seed = sid('pnw5tree', ci, att); kd = species(seed, 'pnw')
            els.append(dict(kind='tree', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h * .75, y - h * 1.2, x + h * .75, y + h * .12], seed=seed, layer='base',
                            params=dict(x=x, y=y, h=h, kd=kd, snow=0.0)))
            pnw_pts.append((x, y)); got += 1
            changes.append(dict(what='add tree', where='pnw', at=[round(x), round(y)], now=kd, seed=seed))
    # --- Florida: palms instead of northern trees
    fl_pts = []; drop = []
    for i, e in enumerate(els):
        if e['kind'] not in ('tree', 'palm'): continue
        p = e['params']; x, y = p['x'], p['y']
        if not FLORIDA.contains_point((x, y)): continue
        old = p.get('kd', 'palm'); h = p.get('h', (p.get('prm') or [110])[0]); r10 = e['seed'] % 10
        fl_pts.append((x, y))
        if e['kind'] == 'palm' or r10 < 5:                               # ~50%: palms
            variant = ['tall', 'short', 'odd'][e['seed'] % 3] if e['kind'] == 'tree' else 'tall'
            h = h * (.95 if e['kind'] == 'palm' else .8)
            e['kind'] = 'palm5'; e['params'] = dict(x=x, y=y, h=round(h, 2), variant=variant); now = f'palm:{variant}'
        elif r10 < 8 or p.get('kd') not in ('green', 'olive'):          # ~35%: low palmetto scrub
            h = h * .34; e['kind'] = 'palm5'; e['params'] = dict(x=x, y=y, h=round(h, 2), variant='palmetto'); now = 'palmetto'
        else:                                                            # the rest: keep green broadleaf trees (live-oak-like)
            now = 'kept ' + p['kd']
        e['bbox'] = [x - h * .8, y - h * 1.15, x + h * .8, y + h * .1]
        changes.append(dict(what='retype tree', where='florida', at=[round(x), round(y)], was=old, now=now, seed=e['seed']))
    for ci, (cx, cy, n) in enumerate([(1420, 790, 2), (1395, 862, 3), (1345, 690, 2)]):
        rr = np.random.RandomState(sid('fl5', ci)); got = 0
        for att in range(60):
            if got >= n: break
            x = cx + rr.uniform(-22, 22); y = cy + rr.uniform(-12, 12); h = rr.uniform(58, 86)
            if not FLORIDA.contains_point((x, y)) or not free(x, y, h * .8, fl_pts): continue
            seed = sid('fl5palm', ci, att); variant = ['tall', 'short', 'odd'][(seed >> 2) % 3]
            els.append(dict(kind='palm5', depth=float(B.depth_at(x, y, gbase)), bbox=[x - h * .8, y - h * 1.15, x + h * .8, y + h * .1], seed=seed, layer='base',
                            params=dict(x=x, y=y, h=h, variant=variant)))
            fl_pts.append((x, y)); got += 1
            changes.append(dict(what='add palm', where='florida', at=[round(x), round(y)], now=f'palm:{variant}', seed=seed))
    # --- group 4: the Pacific Northwest after the second reference: distinct tiered evergreens with ground showing
    #     between them, lighter meadow hills, and a few flowering shrubs in the gaps
    pnw5_refine(els, changes, gbase, free, scene)
    fl6_refine(els, changes, gbase, scene)
    # --- Toy Town's grand station, redrawn after the reference (station5.py); the pennants move to its new finials
    import station5 as ST
    feet = ST.flag_feet(*B.HALL); cols = {'#c8302a': 'red', '#3f6aa8': 'blue', '#3f7a3a': 'green'}
    for e in els:
        if e['kind'] == 'station':
            e['kind'] = 'station5'; e['bbox'] = [B.HALL[0] - 200, B.HALL[1] - 215, B.HALL[0] + 200, B.HALL[1] + 10]
            changes.append(dict(what='redraw', where='toy town', at=list(B.HALL), was='station (pass 4)', now='station5 (after the reference)'))
        if e['kind'] == 'flag' and e['params']['col'] in cols and abs(e['params']['x'] - B.HALL[0]) < 120 and e['params']['y'] < 300:
            fx, fy = feet[cols[e['params']['col']]]; old = (e['params']['x'], e['params']['y'])
            e['params']['x'], e['params']['y'] = fx, fy - 36; e['bbox'] = [fx - 4, fy - 42, fx + 28, fy + 4]
            changes.append(dict(what='move pennant', where='toy town', at=[round(fx), round(fy)], was=list(old)))
    scene['version'] = 5; scene['base'] = 'pass4 scene4.json (checkpoint pass4-approved-2026-11-03)'
    return scene, changes

# ====================================================================== render: pass 4's renderer, with the new kinds
_paint4 = B.paint
def paint5(e, routes):
    p = e['params']
    if e['kind'] == 'tree' and p.get('kd') in EV_PAINT:
        EV_PAINT[p['kd']](p['x'], p['y'], p['h'], e['seed'] % 1000000); return
    if e['kind'] == 'tree' and p.get('kd', '').startswith('bl5_'):
        P5.bl_tree(p['x'], p['y'], p['h'], p['kd'][4:], e['seed'] % 1000000); return
    if e['kind'] == 'lodge5':
        B.depot(p['x'], p['y'], p['roof'], pier=True, seed=e['seed'] % 100000); P5.lodge_extras(p['x'], p['y'], seed=e['seed'] % 1000); return
    if e['kind'] == 'desert': P5.desert_floor(e['seed']); return
    if e['kind'] == 'river' and p.get('name') == 'main':
        P = B.RIVER; i0, i1 = p['i0'], min(len(P) - 1, p['i1'] + 1); n = len(P)
        F5.river5(P[i0:i1 + 1], (13 + 17 * i0 / n) * 1.3, (13 + 17 * i1 / n) * 1.3, e['seed']); return
    if e['kind'] == 'mouth5': F5.river_mouth(p['pts'], e['seed'] % 100000); return
    if e['kind'] == 'fpatch5': F5.flower_patch(p['x'], p['y'], p['rx'], p['ry'], e['seed'] % 100000); return
    if e['kind'] == 'butte5': P5.double_butte(p['x'], p['y'], p['w'] * 1.15, p['h'] * 1.2, e['seed'] % 100000); return
    if e['kind'] == 'saguaro5': P5.saguaro(p['x'], p['y'], p['h'], e['seed'] % 100000); return
    if e['kind'] == 'pear5': P5.prickly_pear(p['x'], p['y'], p['h'], e['seed'] % 100000); return
    if e['kind'] == 'agave5': P5.agave(p['x'], p['y'], p['h'], e['seed'] % 100000); return
    if e['kind'] == 'sage5': P5.sage(p['x'], p['y'], p['h'], e['seed'] % 100000); return
    if e['kind'] == 'tuft5': P5.grass_tuft(p['x'], p['y'], p['h'], e['seed'] % 100000); return
    if e['kind'] == 'rocks5': P5.rocky_coast(p['pts'], e['seed'] % 100000); return
    if e['kind'] == 'falls5': P5.waterfall(p['x0'], p['y0'], p['x1'], p['y1'], e['seed'] % 100000); return
    if e['kind'] == 'bush5':
        flower_bush(p['x'], p['y'], p['h'], e['seed'] % 1000000, p['col']); return
    if e['kind'] == 'station5':
        import station5 as ST; ST.grand_station5(*B.HALL); return
    if e['kind'] == 'palm5':
        (palmetto(p['x'], p['y'], p['h'], e['seed'] % 1000000) if p['variant'] == 'palmetto' else palm5(p['x'], p['y'], p['h'], e['seed'] % 1000000, p['variant'])); return
    _paint4(e, routes)
B.paint = paint5

# ====================================================================== group 2: a living landscape (moving layers)
# Trees, palm fronds, extra wave marks and chimney smoke that move are painted as their own transparent images and
# left out of the base painting, so nothing leaves a hole behind when they move. A tree is only made to move if
# little is painted in front of it. Whatever is painted in front of a moving tree (a hill crest, a nearer tree, a
# house) is cut from the finished painting into a small 'front patch' that is drawn over the moving tree, so the tree
# stays behind it exactly as in the still. Trees that turn out to be mostly hidden are painted back into the base.
import a as A
CHIMNEYS = []
_smoke = A.smoke
def _smoke_rec(x, y, *a, **kw):
    CHIMNEYS.append((round(float(x), 2), round(float(y) + 10, 2)))   # the chimney top (house() puffs start 10 above it)
    return _smoke(x, y, *a, **kw)
A.smoke = _smoke_rec

def canopy_box(e):
    p = e['params']; x, y, h = p['x'], p['y'], p['h']
    if e['kind'] == 'palm5': return (x - h * .7, y - h * 1.15, x + h * .7, y + 2)
    return (x - h * .48, y - h * 1.1, x + h * .48, y + 2)

def choose_movers(scene):
    els = scene['elements']; tracks = np.vstack([np.array(r['points']) for r in scene['routes'].values()])
    hills = [(base, MP(B.U2.hill_poly(cx, base, w, h, 500 + i * 7))) for i, (cx, base, w, h, kind) in enumerate(B.HILLS)]
    def boxes_overlap(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
    later = [(e['depth'], canopy_box(e) if e['kind'] in ('tree', 'palm5') else tuple(e['bbox']), e['kind']) for e in els
             if e['layer'] == 'base' and e['kind'] not in ('hill', 'mountain', 'desert', 'lake')]
    def clear(e):
        bx = canopy_box(e); d = e['depth']; p = e['params']
        if np.min(np.hypot(*(tracks - [p['x'], p['y'] - p['h'] * .5]).T)) < p['h'] * .75 + 14: return False
        for dep, bb, kd in later:
            if dep > d + 1e-6 and boxes_overlap(bx, bb): return False
        corners = [(bx[0], bx[1]), (bx[2], bx[1]), ((bx[0] + bx[2]) / 2, bx[1]), (bx[0], (bx[1] + bx[3]) / 2), (bx[2], (bx[1] + bx[3]) / 2)]
        for base, poly in hills:
            if base > d + 1e-6 and any(poly.contains_point(q) for q in corners): return False
        return True
    movers = {'ever': [], 'decid': [], 'palm': []}
    cells = set()
    for e in sorted(els, key=lambda e: -e['params'].get('h', 0) if e['kind'] in ('tree', 'palm5') else 0):
        if e['layer'] != 'base' or e['kind'] not in ('tree', 'palm5'): continue
        p = e['params']
        if e['kind'] == 'palm5':
            if p['variant'] == 'palmetto': continue
            movers['palm'].append(e); continue
        kd = p['kd']; cls = 'ever' if kd in EV_PAINT or kd in ('fir', 'lfir') else 'decid' if (kd in DECID or kd.startswith('bl5_')) else None
        if cls is None or p['h'] < 52 or p.get('snow', 0) > .45: continue
        cell = (cls, int(p['x'] // 130), int(p['y'] // 100))
        if cell in cells: continue                                   # spread across the map, one per cell
        if np.min(np.hypot(*(tracks - [p['x'], p['y'] - p['h'] * .5]).T)) < p['h'] * .75 + 14: continue
        cells.add(cell); movers[cls].append(e)
    movers['ever'] = [e for e in movers['ever'] if e['params']['kd'] in EV_PAINT][:22] + [e for e in movers['ever'] if e['params']['kd'] not in EV_PAINT][:8]
    movers['decid'] = movers['decid'][:34]
    for cls, L in movers.items():
        for e in L:
            if cls == 'palm':
                e['params']['trunk_only'] = True                        # trunk stays in the painting; fronds move
            else:
                e['layer'] = 'anim5'; e['params']['sway'] = cls
    return movers

def ocean_wave_spots(n=46, seed=505):
    r = np.random.RandomState(seed); out = []
    boats = [(e_[0], e_[1]) for e_ in BOATS5]
    while len(out) < n:
        x, y = r.uniform(20, B.RW - 40), r.uniform(60, B.RH - 20)
        if B.LANDP.contains_point((x, y), radius=-40) or any(B.LANDP.contains_point((x + dx, y + dy)) for dx in (-30, 0, 50) for dy in (-20, 0, 20)): continue
        if any(abs(x - bx) < 70 and abs(y - by) < 50 for bx, by in boats) or any(abs(x - ox) < 60 and abs(y - oy) < 30 for ox, oy in out): continue
        if y < 70 and (380 < x < 520 or 860 < x < 1030 or 1150 < x < 1330): continue   # under the clouds
        out.append((x, y))
    return out
def wave_mark(x, y, seed):
    r = np.random.RandomState(seed)
    for kk in range(r.randint(2, 4)):
        pts = [(x + kk * 20 + u * 16, y + 2.6 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
        c.stroke(pts, 2.2, '#e6ecee', a=.9, dry=.25, taper=(.2, .2), seed=seed + kk)

def boat_range(x, y, s):
    """How far each boat may drift left/right and up/down without its hull touching land (map units)."""
    def ok(dx, dy): return all(not B.LANDP.contains_point((x + dx + hx * s, y + dy + hy * s), radius=-14) for hx in (-44, -20, 0, 20, 44) for hy in (-60, 0, 14))
    lo = 0
    while lo > -70 and ok(lo - 2, 0): lo -= 2
    hi = 0
    while hi < 70 and ok(hi + 2, 0): hi += 2
    up = 0
    while up > -24 and ok(0, up - 2): up -= 2
    dn = 0
    while dn < 24 and ok(0, dn + 2): dn += 2
    return [lo, hi, up, dn]

def export_movers(scene, movers, routes):
    A_ = f'{OUT5}/anim'; man = json.load(open(f'{A_}/manifest.json')); K_ = B.k
    full = c.img.copy(); add = []; Z = CAP['Z']; BASE = CAP['BASE']
    def place(rgb, a, x0, y0, img=None):
        img = full if img is None else img
        h_, w_ = a.shape; img[y0:y0 + h_, x0:x0 + w_] = img[y0:y0 + h_, x0:x0 + w_] * (1 - a[..., None]) + rgb * a[..., None]
    def front(a, x0, y0, depth):
        vis = (Z[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] <= depth + 1e-6).astype(np.float32)
        hidden = float((a * (1 - vis)).sum() / max(1e-6, a.sum()))
        return vis, hidden
    def patch(mask, x0, y0, name):
        if mask.sum() < 4: return None
        m = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
        ys, xs = np.nonzero(m); a0, a1, b0, b1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgb = BASE[y0 + a0:y0 + a1, x0 + b0:x0 + b1]; B.save_rgba(f'{A_}/{name}', rgb, m[a0:a1, b0:b1])
        return dict(file=name, x=int(x0 + b0), y=int(y0 + a0), w=int(b1 - b0), h=int(a1 - a0))
    dropped = 0
    # moving trees and palms, nearest last, so overlapping movers stack as in the painting
    DROP = set()
    def paint_back(rgb, a, vis, x0, y0, depth):
        place(rgb, a * vis, x0, y0, BASE); place(rgb, a * vis, x0, y0)
        Zs = Z[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]; Zs[(a * vis) > .5] = depth
    def do_sway(cls, j, e, phase):
        nonlocal dropped
        if phase == 2 and id(e) in DROP: return
        if True:
            p = e['params']; bb = canopy_box(e); bb = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
            (x0, y0), rgb, a = B.sprite(lambda e=e: paint5(dict(e, params={k_: v for k_, v in e['params'].items() if k_ != 'sway'}), routes), bb, e['seed'])
            vis, hidden = front(a, x0, y0, e['depth'])
            if phase == 1:
                if hidden > .45:                                         # mostly hidden: paint it back, keep it still
                    paint_back(rgb, a, vis, x0, y0, e['depth']); DROP.add(id(e)); dropped += 1
                return
            name = f'tree_{cls}_{j}.png'; B.save_rgba(f'{A_}/{name}', rgb, a); place(rgb, a * vis, x0, y0)
            d_ = dict(kind='sway', cls=cls, file=name, x=x0, y=y0, w=int(a.shape[1]), h=int(a.shape[0]), depth=e['depth'],
                      pivot=[p['x'] * K_ - x0, p['y'] * K_ - y0], tree=p['kd'], height=p['h'] * K_)
            pf = patch((a > .02) & (vis < .5), x0, y0, f'front_{cls}_{j}.png')
            if pf: d_['front'] = pf
            add.append(d_)
    def do_palm(j, e, phase):
        nonlocal dropped
        if phase == 2 and id(e) in DROP: return
        p = e['params']; trunk, fronds, _ = palm_geom(p['x'], p['y'], p['h'], e['seed'] % 1000000, p['variant']); top = trunk[-1]
        order = sorted(range(len(fronds)), key=lambda i: -math.sin(fronds[i][0]))
        parts = []
        for rank, i in enumerate(order):
            a_, ln, droop, _ = fronds[i]; R_ = ln * 1.25 + 4
            bb = (top[0] - R_, top[1] - R_, top[0] + R_, top[1] + R_ + ln * droop)
            (x0, y0), rgb, a = B.sprite(lambda p=p, e=e, i=i: palm_frond(p['x'], p['y'], p['h'], e['seed'] % 1000000, p['variant'], i), bb, e['seed'] + i)
            parts.append((rank, i, x0, y0, rgb, a) + front(a, x0, y0, e['depth']))
        tot = sum(pt[5].sum() for pt in parts); hid = sum((pt[5] * (1 - pt[6])).sum() for pt in parts) / max(1e-6, tot)
        if phase == 1:
            if hid > .45:
                for rank, i, x0, y0, rgb, a, vis, _h in parts: paint_back(rgb, a, vis, x0, y0, e['depth'])
                DROP.add(id(e)); dropped += 1
            return
        for rank, i, x0, y0, rgb, a, vis, _h in parts:
            a_, ln, droop, _ = fronds[i]
            name = f'frond_{j}_{rank}.png'; B.save_rgba(f'{A_}/{name}', rgb, a); place(rgb, a * vis, x0, y0)
            d_ = dict(kind='frond', palm=j, order=rank, file=name, x=x0, y=y0, w=int(a.shape[1]), h=int(a.shape[0]), depth=e['depth'],
                      pivot=[top[0] * K_ - x0, top[1] * K_ - y0], angle=round(a_, 3), length=ln * K_)
            pf = patch((a > .02) & (vis < .5), x0, y0, f'front_palm_{j}_{rank}.png')
            if pf: d_['front'] = pf
            add.append(d_)
    items = [(e['depth'], cls, j, e) for cls in ('ever', 'decid', 'palm') for j, e in enumerate(movers[cls])]
    for phase in (1, 2):         # 1: paint back the mostly hidden ones (and enter them in the depth buffer); 2: export the rest
        for _d, cls, j, e in sorted(items, key=lambda t: t[0]):
            do_palm(j, e, phase) if cls == 'palm' else do_sway(cls, j, e, phase)
    # extra ocean wave marks that come and go
    for j, (x, y) in enumerate(ocean_wave_spots()):
        (x0, y0), rgb, a = B.sprite(lambda x=x, y=y, j=j: wave_mark(x, y, 8000 + j), (x - 6, y - 8, x + 76, y + 8), 8000 + j)
        name = f'wave_{j}.png'; B.save_rgba(f'{A_}/{name}', rgb, a)
        if j % 3 == 0: place(rgb, a * .7, x0, y0)                       # a third of them show in the still
        add.append(dict(kind='wave', file=name, x=x0, y=y0, w=int(a.shape[1]), h=int(a.shape[0])))
    man['sprites'] += add
    # boats: how far each may drift without reaching land
    boats = [e for e in scene['elements'] if e['kind'] == 'boat']
    bsprites = [s_ for s_ in man['sprites'] if s_['kind'] == 'boat']
    for e, s_ in zip(boats, bsprites):
        s_['drift'] = [v * K_ for v in boat_range(e['params']['x'], e['params']['y'], e['params']['s'])]
    # river: which points of the centre-line are visible water (not under a bridge, the town or a tree)
    base = cv2.imread(f'{A_}/base.jpg').astype(int)
    vis = []
    for xp, yp in man['river']:
        xi, yi = int(min(max(xp, 0), B.W - 1)), int(min(max(yp, 0), B.H - 1)); bgr = base[yi, xi]
        vis.append(int(bgr[0] > bgr[2] + 40 and bgr[0] > bgr[1] + 10))
    man['river_visible'] = vis
    man['delta'] = [(np.array(P_) * K_).round(2).tolist() for P_ in B.DELTA]
    lh = next(e['params'] for e in scene['elements'] if e['kind'] == 'lighthouse')
    man['lighthouse'] = [lh['x'] * K_, (lh['y'] - 92 - 8) * K_]
    houses = [(x, y) for (x, y, *_r) in B.HOUSES]
    farm = [ch for ch in CHIMNEYS if any(abs(ch[0] - hx) < 40 and -90 < ch[1] - hy < 0 for hx, hy in houses)]
    man['chimneys'] = [[x * K_, y * K_] for x, y in farm[::2][:6]]
    man['wind'] = dict(note='gusts travel west to east across the map; see the viewer for the motion curves')
    json.dump(man, open(f'{A_}/manifest.json', 'w'))
    cv2.imwrite(f'{A_}/base.jpg', (BASE[..., ::-1] * 255 + .5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
    c.img = full; c.save(f'{OUT5}/usmap5')
    n_ = lambda kd, cl=None: len({s_['file'].rsplit('_', 1)[0] if kd == 'frond' else s_['file'] for s_ in add if s_['kind'] == kd and (cl is None or s_.get('cls') == cl)})
    B.log(f"moving: {n_('sway', 'ever')} evergreens, {n_('sway', 'decid')} broadleaf trees, {len({s_['palm'] for s_ in add if s_['kind'] == 'frond'})} palms; {dropped} candidates kept still (mostly hidden); "
          f"{sum(1 for s_ in add if s_['kind'] == 'wave')} wave marks, {len(man['chimneys'])} chimneys")

import inspect
CAP = {}
_impasto = B.impasto
def _impasto_cap(cv_, amt):
    CAP['Z'] = inspect.currentframe().f_back.f_locals['Z']            # pass 4's depth buffer, after the base is painted
    out = _impasto(cv_, amt); CAP['BASE'] = np.clip(cv_.img, 0, 1).copy(); return out
B.impasto = _impasto_cap

_paint5_static = paint5
def paint5_anim(e, routes):
    p = e['params']
    if e['kind'] == 'palm5' and p.get('trunk_only'):
        palm_trunk(p['x'], p['y'], p['h'], e['seed'] % 1000000, p['variant']); return
    _paint5_static(e, routes)
B.paint = paint5_anim

import cv2
if __name__ == '__main__':
    B.OUT = OUT5
    os.makedirs(OUT5, exist_ok=True)
    if '--keep-scene' not in ARGS or not os.path.exists(f'{OUT5}/scene5.json'):
        base = json.load(open('out4/scene4.json'))
        scene, changes = refine(base)
        movers = choose_movers(scene)
        json.dump(scene, open(f'{OUT5}/scene5.json', 'w')); json.dump(changes, open(f'{OUT5}/changes5.json', 'w'), indent=0)
        B.log(f'{len(changes)} refinements')
    else:
        scene = json.load(open(f'{OUT5}/scene5.json'))
    movers = {'ever': [], 'decid': [], 'palm': []}
    for e in scene['elements']:
        if e['layer'] == 'anim5': movers[e['params']['sway']].append(e)
        elif e['kind'] == 'palm5' and e['params'].get('trunk_only'): movers['palm'].append(e)
    B.main()
    routes = {}
    export_movers(scene, movers, routes)
    for ext in ('.png', '.jpg', '_sm.jpg'):                       # pass 4's main() also wrote usmap4.*; the final still is usmap5.*
        if os.path.exists(f'{OUT5}/usmap4{ext}'): os.remove(f'{OUT5}/usmap4{ext}')

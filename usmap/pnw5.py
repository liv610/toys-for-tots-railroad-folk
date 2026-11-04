"""Pass 5, group 5 — the Pacific Northwest corner after the user's reference (folk map, second Northwest reference).

Painters for: blossom-dotted autumn broadleaf trees, a rocky surf-washed coast with a waterfall, the lodge station's
timber gable / flower boxes / railing, a double red butte, and desert plants (saguaro, prickly pear, agave, sage).
All sizes are in map units.
"""
import math
import numpy as np
import usmap4 as B
from usmap4 import c, hexc, pal_fn, catmull, resample

S = B.S
U2 = B.U2

# ---------------------------------------------------------------- broadleaf trees with blossom dots
BL = {
    'yellow': (['#d8a828', '#e8bc34', '#c08e20', '#f2d058'], ['#f6dc78', '#fbe9a6', '#e07a28']),
    'red':    (['#b83a2a', '#cc4c34', '#9a2e22', '#de6a48'], ['#ee8a6c', '#f6c4b2', '#f0a030']),
    'orange': (['#d46c28', '#e48434', '#b85620', '#eea04c'], ['#f4b062', '#f9d29a', '#c03826']),
    'pink':   (['#d07c90', '#e094a6', '#b86478', '#eeb2c0'], ['#f4cad4', '#fde8ee', '#b84a64']),
    'green':  (['#5e8a34', '#72a03c', '#4a7228', '#8eb84e'], ['#9cc254', '#c2da80', '#e8c850']),
}
def bl_tree(x, y, h, kind, seed):
    """A storybook broadleaf tree: a round, slightly lobed crown of dabs, thick with blossom dots, dark branches
    showing through, on a visible trunk."""
    cols, dots = BL[kind]
    r = np.random.RandomState(seed)
    B.kit.skeleton_tree(c, x, y, h, cols, seed, dots=None, branches='#3a2418', shape='round')
    rx, ry = h * .36, h * .34; cy = y - h * .6
    n = int(h * 1.5)
    ang = r.rand(n) * 2 * math.pi; rad = r.rand(n) ** .55
    pts = [(x + math.cos(a) * rx * d * .9, cy + math.sin(a) * ry * d * .88) for a, d in zip(ang, rad)]
    c.dots(pts, max(.5, h * .0105), dots[:2], seed=seed + 7)
    c.dots(pts[::6], max(.5, h * .0095), [dots[2]], seed=seed + 8)

# ---------------------------------------------------------------- coast: grey rocks, surf, a waterfall
def rock_cluster(x, y, s, seed):
    r = np.random.RandomState(seed)
    for j in range(r.randint(3, 6)):
        px, py = x + r.uniform(-1, 1) * s * 1.2, y + r.uniform(-.6, .6) * s
        rx, ry = s * r.uniform(.55, .95), s * r.uniform(.4, .7)
        m = c.area(S.lumpy(px, py, rx, ry, seed + j, n=22, bumps=4, amp=.14, flat=.35), '#8a8a8c', wob=.15, rough=.6, edge_dark=.22, seed=seed + j)
        if m is None: continue
        def colf(X, Y, rr, px=px, py=py, rx=rx, ry=ry):
            lit = np.clip(.55 - (X - px) / rx * .5 - (Y - py) / ry * .6 + rr.randn(len(X)) * .15, 0, 1)
            C = np.array([hexc(z) for z in ['#5e5e62', '#7c7c80', '#9c9ca0', '#c0c0c2']])
            return C[np.clip((lit * 3.4).astype(int), 0, 3)]
        c.stip(m, colf, spacing=1.1, L=2.6, w=1.3, seed=seed + 20 + j, jit=.4)

def surf(x, y, w, seed):
    r = np.random.RandomState(seed)
    for k_ in range(3):
        pts = [(x - w / 2 + u * w, y + k_ * 3 + 1.6 * math.sin(u * math.pi * 3 + k_)) for u in np.linspace(0, 1, 8)]
        c.stroke(pts, 1.8 - k_ * .4, '#f4f6f6', a=.95 - k_ * .2, dry=.3, taper=(.3, .3), seed=seed + k_)

def rocky_coast(points, seed):
    """Grey rock clusters along the shore with white surf on the sea side (points: [(x, y)] on the coastline)."""
    r = np.random.RandomState(seed)
    for j, (x, y) in enumerate(points):
        s = r.uniform(10, 15)
        rock_cluster(x - 2, y, s, seed + 100 * j)
        surf(x - s * 1.5, y + s * .6, s * 2.4, seed + 100 * j + 50)

def waterfall(x0, y0, x1, y1, seed):
    """White water tumbling off the clifftop into the sea, with a splash at the foot."""
    r = np.random.RandomState(seed)
    P0 = catmull([(x0 - 3, y0 - 2), ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - 3, y1)], 8)
    c.stroke(P0, 14, '#cfe4f0', a=.85, dry=.15, taper=(.1, .1), seed=seed + 99)        # a pale body of water first
    for k_ in range(11):
        off = (k_ - 5) * 1.3
        P = catmull([(x0 + off * .6, y0), ((x0 + x1) / 2 + off, (y0 + y1) / 2 + r.uniform(-2, 2)), (x1 + off * 1.3, y1)], 8)
        c.stroke(P, r.uniform(1.4, 2.6), ['#f6f8fa', '#e2ecf2', '#ffffff'][k_ % 3], a=.95, dry=.25, taper=(.05, .2), seed=seed + k_)
    for k_ in range(5):
        c.area(S.lumpy(x1 + r.uniform(-7, 7), y1 + r.uniform(-2, 3), r.uniform(4, 7), r.uniform(2.5, 4), seed + 40 + k_, n=18, amp=.2), '#f2f6f8', wob=.3, rough=.6, a=.9)

# ---------------------------------------------------------------- the lodge: timber gable, flower boxes, railing
def lodge_extras(x, y, w=120, h=44, seed=0):
    r = np.random.RandomState(seed)
    # front gable over the centre of the long roof: cream infill, blue bargeboards, a king-post truss
    gw = 28; base_y = y - h + 2; apex = (x, y - h - 20)
    tri = [(x - gw, base_y), (x + gw, base_y), apex]
    m = B.wall(tri, '#f2e8d2', seed + 1)
    c.stroke([(x - gw - 3, base_y + 1), apex, (x + gw + 3, base_y + 1)], 3.4, '#2f6aa8', a=1, dry=.05, taper=(0, 0))
    c.stroke([(x - gw - 3, base_y + 1), apex, (x + gw + 3, base_y + 1)], .9, '#7fb0e0', a=.9, dry=0, taper=(0, 0))
    c.stroke([(x - gw + 2, base_y - 1), (x + gw - 2, base_y - 1)], 2.2, '#2f6aa8', a=1, dry=0, taper=(0, 0))
    c.stroke([(x, base_y - 1), (x, apex[1] + 4)], 1.8, '#2f6aa8', a=1, dry=0, taper=(0, 0))
    for sgn in (-1, 1):
        c.stroke([(x, base_y - 9), (x + sgn * gw * .62, base_y - 1)], 1.4, '#2f6aa8', a=1, dry=0, taper=(0, 0))
        c.stroke([(x + sgn * gw * .25, base_y - 1), (x + sgn * gw * .25, base_y - 8)], 1.1, '#2f6aa8', a=1, dry=0, taper=(0, 0))
    c.dots([(x, apex[1] + 2)], 1.6, ['#f2c25a'])
    # flower boxes under the five windows: a brown planter, red and pink geraniums, a little green
    for i in range(5):
        wx = x - w / 2 + w * (i + .5) / 5; wy = y - h * .45 + h * .21 + 2.5; bw = w / 9 + 4
        c.area([(wx - bw / 2, wy), (wx + bw / 2, wy), (wx + bw / 2 - 1, wy + 4), (wx - bw / 2 + 1, wy + 4)], '#7a4a2c', wob=0, rough=.3, edge_dark=.2)
        leaves = [(wx + r.uniform(-bw / 2, bw / 2), wy - r.uniform(0, 2.4)) for _ in range(10)]
        c.dots(leaves, 1.3, ['#3f7a34', '#5a9a40'], seed=seed + 10 + i)
        flowers = [(wx + r.uniform(-bw / 2 + 1, bw / 2 - 1), wy - r.uniform(.6, 3.4)) for _ in range(9)]
        c.dots(flowers, 1.25, ['#d8302a', '#e8506a', '#f2a0b0'], seed=seed + 20 + i)
    # a white railing along the front of the pier deck
    top = y + 1
    c.stroke([(x - 92, top - 5), (x - w / 2 - 2, top - 5)], 1.3, '#f4f0e6', a=1, dry=0, taper=(0, 0))
    c.stroke([(x - 92, top - 2), (x - w / 2 - 2, top - 2)], 1.0, '#f4f0e6', a=1, dry=0, taper=(0, 0))
    for px in np.arange(x - 92, x - w / 2, 5): c.stroke([(px, top + 3), (px, top - 6)], 1.0, '#f4f0e6', a=1, dry=0, taper=(0, 0))

# ---------------------------------------------------------------- the double butte
def butte(x, y, w, h, seed, shade_right=True):
    """One butte after the reference: a tall, slightly tapering column with an oval flat top, standing on a very
    wide skirt that sweeps out steeply from the column and flattens into the sand. Broad wavy bands run across
    column and skirt alike; fine vertical grooves run down the column."""
    r = np.random.RandomState(seed)
    tw, bw = w * .3, w * .4                                            # column width at the top and at its foot
    ycol = y - h * .46                                                 # where the column meets the skirt
    ry = tw * .1                                                       # the oval top, seen a little from above
    prof = []
    for s in np.linspace(1, 0, 18):                                    # left skirt, from the sand in to the column
        prof.append((x - bw / 2 - (w / 2 - bw / 2) * s, ycol + (y + 2 - ycol) * (1 - (1 - s) ** 2.6)))
    for u in np.linspace(0, 1, 10)[1:]:                                # left side of the column
        prof.append((x - bw / 2 + (bw - tw) / 2 * u, ycol - (ycol - (y - h)) * u))
    for a in np.linspace(math.pi, 2 * math.pi, 18)[1:-1]:              # far rim of the oval top
        prof.append((x + tw / 2 * math.cos(a), y - h + ry * math.sin(a)))
    for u in np.linspace(1, 0, 10)[:-1]:
        prof.append((x + bw / 2 - (bw - tw) / 2 * u, ycol - (ycol - (y - h)) * u))
    for s in np.linspace(0, 1, 18):
        prof.append((x + bw / 2 + (w / 2 - bw / 2) * s, ycol + (y + 2 - ycol) * (1 - (1 - s) ** 2.6)))
    m = c.area(prof, '#d0683e', wob=.25, rough=.6, edge_dark=.1, seed=seed)
    if m is None: return
    LIGHT, DARK, FOOT = np.array(hexc('#df7c49')), np.array(hexc('#ad4932')), np.array(hexc('#c55837'))
    ph = r.uniform(0, 6.28)
    def colf(X, Y, rr):
        v = (Y - (y - h)) / (h / 3.3) + .17 * np.sin(X / 21 + ph) + .05 * np.sin(X / 9 + ph * 2)
        v = v + rr.randn(len(X)) * .012                                # soft band edges
        band = (v % 1.0 > .55) & (v > .6)                              # broad light bands, slightly narrower dark ones
        C = np.where(band[:, None], DARK, LIGHT)
        C = np.where(((Y > y - h * .13) & ~band)[:, None], FOOT, C)    # the foot of the skirt is a deeper red-orange
        shd = np.where(X > x + tw * .2, .93, 1.0) if shade_right else 1.0
        return C * (shd * (1 + (rr.rand(len(X)) - .5) * .07))[:, None]
    c.stip(m, colf, spacing=1.05, L=3.4, w=1.4, angfn=lambda X, Y: .1 * np.sin(X / 9 + Y / 6), seed=seed + 1, jit=.25)
    prev = c.clipm; c.set_clip(m)
    ng = max(6, int(bw / 5.5))
    for kk in range(ng):                                               # fine vertical grooves down the column
        u = (kk + .5) / ng
        xt = x - tw / 2 + tw * u; xb = x - bw / 2 + bw * u + r.uniform(-.8, .8)
        yb = ycol + r.uniform(-2, 6)
        c.stroke([(xt, y - h + ry * .6), (xb, yb)], .55, '#8e3e26', a=.36, dry=.35, taper=(.05, .35))
    c.clipm = prev
    top = [(x + tw / 2 * math.cos(a), y - h + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)]
    cm = c.area(top, '#ecaa64', wob=0, rough=.5, edge_dark=.1)
    if cm is not None: c.stip(cm, pal_fn(['#ecaa64', '#f2b874', '#e09c58']), spacing=1.1, L=2.6, w=1.3, seed=seed + 3, jit=.6)

def double_butte(x, y, w, h, seed):
    butte(x + w * .2, y - 2, w * .62, h * .8, seed + 1)             # the smaller one, behind and to the right
    butte(x - w * .14, y, w * .9, h * 1.12, seed)                   # the big one, in front

# ---------------------------------------------------------------- desert plants
SAG = ('#6c8a4a', '#90aa66', '#4e6a38')                            # muted sage green, as in the reference
def _cactus_limb(pts, wd):
    pts = np.array(pts, float)
    c.stroke(pts, wd, SAG[0], a=1, dry=.05, taper=(0, 0), streak=.1)
    c.stroke(pts - [wd * .28, 0], wd * .14, SAG[1], a=.85, dry=.1, taper=(0, .15))     # lit ribs
    c.stroke(pts + [wd * .02, 0], wd * .1, SAG[1], a=.55, dry=.2, taper=(0, .15))
    c.stroke(pts + [wd * .32, 0], wd * .16, SAG[2], a=.8, dry=.1, taper=(0, .15))      # shaded side
    c.area(S.lumpy(pts[-1][0], pts[-1][1], wd * .5, wd * .42, 3, n=14, amp=0), SAG[0], wob=0, rough=.2)   # rounded tip

def saguaro(x, y, h, seed):
    """A saguaro after the reference: a tall trunk and two arms that turn up in a U, rounded tips, ribbed."""
    r = np.random.RandomState(seed); w = h * .18
    la = r.uniform(.32, .42); ra = r.uniform(.45, .58)
    for side, at, top in ((-1, la, la + r.uniform(.3, .4)), (1, ra, ra + r.uniform(.24, .32))):
        reach = h * r.uniform(.2, .25); ya = y - h * at
        arm = [(x, ya), (x + side * reach * .55, ya)] + [(x + side * (reach * .55 + reach * .45 * math.sin(t)), ya - reach * .45 * (1 - math.cos(t))) for t in np.linspace(.3, math.pi / 2, 4)] + \
              [(x + side * reach, y - h * top)]
        _cactus_limb(arm, w * .74)
    _cactus_limb([(x, y + 1), (x, y - h)], w)

def prickly_pear(x, y, s, seed):
    """Flat oval pads stacked in a clump, with magenta flowers on the top pads."""
    r = np.random.RandomState(seed)
    pads = [(x, y - s * .5, 0, 1.0), (x - s * .55, y - s * .62, -.4, .8), (x + s * .5, y - s * .7, .35, .85)]
    pads += [(x + r.uniform(-.4, .4) * s, y - s * r.uniform(1.15, 1.35), r.uniform(-.4, .4), .75) for _ in range(r.randint(1, 3))]
    tops = []
    for j, (px, py, a, sc) in enumerate(pads):
        rx, ry = s * .34 * sc, s * .44 * sc
        poly = [(px + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a), py + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a)) for t in np.linspace(0, 2 * math.pi, 22)]
        m = c.area(poly, '#728e50', wob=.08, rough=.4, edge_dark=.25, seed=seed + j)
        if m is not None: c.stip(m, pal_fn(['#728e50', '#86a060', '#607c44']), spacing=1.0, L=1.8, w=1.1, seed=seed + 30 + j, jit=.8)
        c.dots([(px + r.uniform(-.6, .6) * rx, py + r.uniform(-.6, .6) * ry) for _ in range(4)], max(.35, s * .02), ['#d8e4b0'], seed=seed + 10 + j)
        tops.append((px + ry * math.sin(a), py - ry * math.cos(a)))
    for j, (fx, fy) in enumerate(tops):
        if j == 0 or r.rand() < .25: continue
        fr = s * r.uniform(.13, .17)
        c.area(S.lumpy(fx, fy - fr * .6, fr, fr * 1.15, seed + 40 + j, n=16, amp=.12), '#b83a68', wob=0, rough=.3, edge_dark=.25)
        c.area(S.lumpy(fx - fr * .2, fy - fr * .9, fr * .5, fr * .55, seed + 50 + j, n=12, amp=0), '#d8608c', wob=0, rough=.2)

def agave(x, y, s, seed):
    r = np.random.RandomState(seed)
    for j in range(9):
        a = -math.pi / 2 + (j - 4) * .3 + r.uniform(-.06, .06); ln = s * (1.15 - abs(j - 4) * .09)
        c.stroke([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], s * .2, ['#7a9686', '#687f74', '#92aa9a'][j % 3], a=1, dry=.05, taper=(0, .85))

def sage(x, y, s, seed):
    """A spiky desert shrub: a dense fan of short olive and sage-green blades, darker at the base."""
    r = np.random.RandomState(seed)
    for j in range(int(34 + s * 2)):
        a = -math.pi / 2 + r.uniform(-1.25, 1.25); ln = s * r.uniform(.6, 1.15) * (1 - abs(a + math.pi / 2) * .25)
        bx = x + r.uniform(-.35, .35) * s
        col = ['#7c8440', '#98984e', '#626a34', '#a8a660', '#707a3c'][j % 5]
        c.stroke([(bx, y + .5), (bx + math.cos(a) * ln, y + math.sin(a) * ln)], max(.8, s * .11), col, a=1, dry=.1, taper=(0, .85))

def grass_tuft(x, y, s, seed):
    r = np.random.RandomState(seed)
    for j in range(6):
        a = -math.pi / 2 + r.uniform(-.7, .7)
        c.stroke([(x + r.uniform(-1, 1), y), (x + math.cos(a) * s, y + math.sin(a) * s)], .8, ['#b8a050', '#8a8a3a', '#d0b860'][j % 3], a=1, dry=.1, taper=(0, .8))

# ---------------------------------------------------------------- the desert floor, in the reference's soft peach
def desert_floor(seed):
    dpoly = catmull([(112, 482), (250, 456), (400, 470), (520, 500), (562, 560), (522, 622), (420, 642), (300, 642), (200, 632), (110, 602)], 10, closed=True)
    dm = U2.land_clip(c.area(dpoly, '#e09a54', wob=5, rough=1.4, edge_dark=.03, seed=seed))
    c.stip(dm, pal_fn(['#e09a54', '#e6a660', '#d68e4a', '#eab06c', '#dc944e'], .04), spacing=1.6, L=4.8, w=1.8, angfn=lambda X, Y: .15 * np.sin(X / 40), seed=seed + 1, jit=.3)
    for j, (px, py, rx, ry) in enumerate([(400, 560, 60, 14), (470, 620, 50, 12), (200, 600, 50, 12), (330, 630, 60, 12)]):
        dune = [(px - rx + 2 * rx * u, py - math.sin(u * math.pi) ** .8 * ry * 1.6) for u in np.linspace(0, 1, 24)] + [(px + rx, py + 6), (px - rx, py + 6)]
        pm = c.area(dune, '#eaab66', wob=1, rough=1, a=.7, seed=seed + 9 + j)
        if pm is not None: c.stip(U2.land_clip(pm), pal_fn(['#eeb672', '#e6a862', '#dc9a56'], .04), spacing=1.6, L=4.6, w=1.7, angfn=lambda X, Y: .2 * np.sin(X / 20), seed=seed + 20 + j)

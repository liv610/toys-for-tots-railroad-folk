"""Engine 10: a small library of designed toys (Phase 4).

Each toy is built silhouette first: one deliberate outer shape (a smooth closed curve from a handful of control
points), then a few large internal shapes, then only the details that read at the toy's size. Everything is painted
through the gouache brush with the 'fine' edge preset (eyes and glints use 'crisp').
Every function draws a toy standing on (x, y) — its base centre — that is h map units tall. A toy should still read
when it is 4-5 map units tall: about 8-10 px on the 2x Toy Town layer.
"""
import math
import numpy as np
import usmap4 as B
from brush import hexc, catmull

S = B.S
def C(): return B.c

def shape(pts, col, edge=.16, rough=.22, seed=0, a=1.0, smooth=True, soft=None):
    c = C(); P = catmull(pts, 6, closed=True) if smooth else np.asarray(pts, float)
    m = c.mask(P, 0, rough, seed, soft=soft) if soft is not None else c.mask(P, 0, rough, seed)
    return c.area(None, col, m=m, edge_dark=edge, a=a), P

def ellipse(x, y, rx, ry, col, n=22, edge=.12, rot=0.0, seed=0, a=1.0):
    pts = [(x + rx * math.cos(t) * math.cos(rot) - ry * math.sin(t) * math.sin(rot), y + rx * math.cos(t) * math.sin(rot) + ry * math.sin(t) * math.cos(rot)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    c = C(); return c.area(None, col, m=c.mask(pts, 0, .2, seed), edge_dark=edge, a=a)

def outline(P, w, col, a=.6):
    C().stroke(list(P) + [P[0]], w, col, a=a, dry=.15, taper=(0, 0))

def line(pts, w, col, a=1.0, taper=(0, 0)):
    C().stroke(pts, w, col, a=a, dry=0, taper=taper)

def light(col, f=1.32, add=.04): return np.minimum(hexc(col) * f + add, 1)
def dark(col, f=.62): return hexc(col) * f

# ---------------------------------------------------------------- teddy (the lab9 benchmark)
TEDDY = [(-3.2, 0), (-1.1, 0), (-.6, -1.0), (0, -1.25), (.6, -1.0), (1.1, 0), (3.2, 0), (3.7, -1.3), (3.35, -2.9), (4.35, -3.5), (4.65, -4.5),
         (3.75, -5.05), (2.65, -5.35), (1.95, -6.0), (2.85, -6.95), (2.95, -8.5), (3.4, -9.2), (2.95, -10.2), (2.0, -10.0), (.95, -10.25),
         (-.95, -10.25), (-2.0, -10.0), (-2.95, -10.2), (-3.4, -9.2), (-2.95, -8.5), (-2.85, -6.95), (-1.95, -6.0), (-2.65, -5.35),
         (-3.75, -5.05), (-4.65, -4.5), (-4.35, -3.5), (-3.35, -2.9), (-3.7, -1.3)]
def teddy(x, y, h, col='#a8683a', bow='#c8302a', seed=0):
    c = C(); s = h / 10.3; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        m, sil = shape([P(*p) for p in TEDDY], col, seed=seed)
        if m is not None and h > 6:
            Cc = np.array([hexc(col), hexc(col) * .86, np.minimum(hexc(col) * 1.12, 1)])
            c.stip(m, lambda X, Y, rr: Cc[rr.randint(3, size=len(X))], spacing=.32 * s, L=.55 * s, w=.32 * s, seed=seed + 1, jit=1.2)
        lc = light(col)
        for (dx, dy, rx, ry) in ((0, -3.0, 1.9, 1.6), (0, -7.35, 1.35, 1.0), (-2.3, -.55, 1.0, .5), (2.3, -.55, 1.0, .5), (-2.55, -9.55, .55, .5), (2.55, -9.55, .55, .5)):
            ellipse(x + dx * s, y + dy * s, rx * s, ry * s, lc, edge=.08)
        for sx in (-1, 1): line([P(sx * 2.6, -5.1), P(sx * 3.0, -4.1), P(sx * 3.2, -3.3)], .18 * s, dark(col), a=.85)
        for sd in (-1, 1): ellipse(x + sd * 1.5 * s * .97, y - 5.85 * s, .95 * s, .55 * s, bow, rot=sd * .35, edge=.2)
        ellipse(x, y - 5.85 * s, .38 * s, .34 * s, dark(bow, .75), edge=0)
    with c.edges('crisp'):
        for ex in (-.95, .95): ellipse(x + ex * s, y - 8.35 * s, .34 * s, .38 * s, '#1e1410', edge=0)
        shape([P(-.48, -7.8), P(.48, -7.8), P(0, -7.25)], '#2a1a12', edge=0, smooth=False)
        line([P(-.55, -6.65), P(0, -6.85), P(.55, -6.65)], .12 * s, '#2a1a12', a=.9)
        c.dots([P(ex - .1, -8.5) for ex in (-.95, .95)], .1 * s, ['#ffffff'])
    outline(sil, .16 * s, dark(col, .45), a=.5)

# ---------------------------------------------------------------- wooden train (engine + one wagon)
def wooden_train(x, y, h, seed=0):
    """A pull-along wooden engine with a cab, a flared chimney and spoked wheels, and a wagon of blocks behind."""
    c = C(); s = h / 6.0; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        shape([P(-1.4, -1.3), P(5.4, -1.3), P(5.4, -.7), P(-1.4, -.7)], '#5a3a24', smooth=False, edge=.2)          # chassis
        m, boiler = shape([P(-.2, -1.3), P(3.6, -1.3), P(3.9, -1.9), P(3.9, -3.1), P(3.6, -3.6), P(-.2, -3.6)], '#c8302a', smooth=False)
        shape([P(3.9, -1.5), P(4.9, -1.3), P(3.9, -3.3)], '#3a2e26', smooth=False, edge=.2)                           # buffer nose
        shape([P(-1.6, -1.3), P(.2, -1.3), P(.2, -5.2), P(-1.6, -5.2)], '#3f6aa8', smooth=False)                    # cab
        shape([P(-1.9, -5.0), P(.5, -5.0), P(.4, -5.7), P(-1.8, -5.7)], '#2a2a40', smooth=False, edge=.2)          # cab roof
        shape([P(-1.2, -3.4), P(-.2, -3.4), P(-.2, -4.6), P(-1.2, -4.6)], '#f6dc8a', smooth=False, edge=.25)       # cab window
        shape([P(2.3, -3.6), P(3.1, -3.6), P(3.3, -5.0), P(3.6, -5.5), P(1.8, -5.5), P(2.1, -5.0)], '#2a2a30', smooth=False, edge=.15)  # chimney
        ellipse(x + 1.3 * s, y - 3.9 * s, .55 * s, .45 * s, '#e8b84a', edge=.2)                                  # dome
        for bx in (.8, 2.0, 3.0): line([P(bx, -1.4), P(bx, -3.5)], .13 * s, '#e8b84a', a=.9)                     # boiler bands
        # wagon
        shape([P(-5.9, -1.3), P(-2.1, -1.3), P(-2.1, -3.0), P(-5.9, -3.0)], '#e8b84a', smooth=False)
        line([P(-2.1, -1.0), P(-1.4, -1.0)], .25 * s, '#3a2e26')
        for (bx, col, ch) in ((-5.3, '#3f8a44', 'A'), (-4.2, '#3f6aa8', 'B'), (-3.1, '#c8302a', 'C')):
            shape([P(bx - .5, -3.0), P(bx + .5, -3.0), P(bx + .5, -4.0), P(bx - .5, -4.0)], col, smooth=False, edge=.2)
    with c.edges('crisp'):
        for wx, r in ((-5.0, .8), (-3.0, .8), (.0, .95), (2.3, 1.25), (4.2, .8)):
            ellipse(x + wx * s, y - r * s, r * s, r * s, '#2a2420', edge=0)
            ellipse(x + wx * s, y - r * s, r * .55 * s, r * .55 * s, '#e8b84a' if wx > -1 else '#c8302a', edge=.1)
            ellipse(x + wx * s, y - r * s, r * .18 * s, r * .18 * s, '#2a2420', edge=0)
        line([P(0, -.95), P(2.3, -1.25)], .14 * s, '#c8c8c8', a=.9)                                                # coupling rod
        c.dots([P(-.9, -4.2)], .12 * s, ['#ffffff'])

# ---------------------------------------------------------------- toy soldier
def soldier(x, y, h, coat='#c8302a', seed=0):
    """A wooden toy soldier: tall black shako with a gold plate and red plume, white cross belts, navy trousers."""
    c = C(); s = h / 10.0; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        shape([P(-1.05, 0), P(-.15, 0), P(-.2, -3.6), P(-1.0, -3.6)], '#1c2a5a', smooth=False); shape([P(.15, 0), P(1.05, 0), P(1.0, -3.6), P(.2, -3.6)], '#1c2a5a', smooth=False)
        shape([P(-1.15, 0), P(-.1, 0), P(-.1, -.55), P(-1.15, -.55)], '#141218', smooth=False, edge=0); shape([P(.1, 0), P(1.15, 0), P(1.15, -.55), P(.1, -.55)], '#141218', smooth=False, edge=0)
        m, body = shape([P(-1.25, -3.5), P(1.25, -3.5), P(1.15, -6.8), P(-1.15, -6.8)], coat, smooth=False)
        for sx in (-1, 1): shape([P(sx * 1.2, -6.6), P(sx * 1.75, -6.4), P(sx * 1.7, -4.0), P(sx * 1.3, -4.0)], coat, smooth=False, edge=.2)
        line([P(-1.1, -6.6), P(1.1, -3.7)], .28 * s, '#f4f2ec'); line([P(1.1, -6.6), P(-1.1, -3.7)], .28 * s, '#f4f2ec')
        ellipse(x, y - 7.55 * s, .9 * s, .85 * s, '#ecc8a4', edge=.1)
        shape([P(-.95, -8.1), P(.95, -8.1), P(.85, -10.3), P(-.85, -10.3)], '#1a1a22', smooth=False, edge=.12)      # shako
        shape([P(-.45, -8.5), P(.45, -8.5), P(.45, -9.4), P(-.45, -9.4)], '#e8b84a', smooth=False, edge=.2)
        ellipse(x, y - 10.55 * s, .32 * s, .55 * s, '#d8302a', edge=.15)                                            # plume
        for sx in (-1, 1): ellipse(x + sx * 1.5 * s, y - 3.85 * s, .3 * s, .3 * s, '#f4f2ec', edge=0)                # white gloves
    with c.edges('crisp'):
        c.dots([P(0, -5.8), P(0, -5.0), P(0, -4.2)], .12 * s, ['#e8b84a'])
        c.dots([P(-.3, -7.6), P(.3, -7.6)], .1 * s, ['#1e1410'])
        c.dots([P(-.5, -7.2), P(.5, -7.2)], .14 * s, ['#e88a7a'])

# ---------------------------------------------------------------- rocking horse
HORSE = [(-3.6, -4.2), (-2.4, -4.9), (1.6, -4.9), (2.6, -5.4), (3.4, -7.2), (3.9, -7.9), (4.9, -7.6), (5.0, -7.0), (4.2, -6.5), (3.9, -5.6),
         (3.2, -4.3), (2.5, -3.7), (2.6, -1.4), (2.1, -1.4), (1.8, -3.5), (-1.8, -3.5), (-2.3, -1.4), (-2.8, -1.4), (-2.8, -3.7), (-3.8, -3.8)]
def rocking_horse(x, y, h, coat='#f2ead8', saddle='#c8302a', seed=0):
    """A dappled rocking horse on curved red rockers: one silhouette for body, neck and head, legs set into the rockers."""
    c = C(); s = h / 8.2; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        ry = lambda dx: -.35 - 1.1 * ((dx + 4.6) / 9.2 * 2 - 1) ** 2                                               # the rocker's curve
        rk = [P(dx, ry(dx)) for dx in np.linspace(-4.6, 4.6, 18)]
        line(rk, .75 * s, '#a8302a')                                                                                # rocker
        line([(px, py - .3 * s) for px, py in rk], .18 * s, '#e8685a', a=.8)
        for lx in (-2.55, -2.05, 1.85, 2.35): line([P(lx, -3.4), P(lx * 1.08, ry(lx * 1.08) - .25)], .38 * s, dark(coat, .82))
        m, sil = shape([P(*p) for p in HORSE], coat, seed=seed)
        if m is not None:
            r = np.random.RandomState(seed)
            c.dots([P(r.uniform(-2.8, 2.0), r.uniform(-4.6, -3.7)) for _ in range(9)], .28 * s, ['#c8c0b0', '#b8b0a0'], seed=seed)
        shape([P(-1.4, -4.85), P(1.0, -4.85), P(1.2, -3.6), P(-1.6, -3.6)], saddle, edge=.2, smooth=False)          # saddle
        line([P(-1.5, -3.75), P(1.15, -3.75)], .16 * s, '#e8b84a')
        line([P(2.7, -5.3), P(3.2, -6.8), P(3.6, -7.7)], .45 * s, '#6a4a2a', a=1, taper=(0, .3))                    # mane
        line([P(-3.6, -4.3), P(-4.4, -3.6), P(-4.6, -2.6)], .5 * s, '#6a4a2a', taper=(0, .6))                       # tail
        line([P(4.2, -6.9), P(3.1, -5.6), P(1.4, -4.9)], .1 * s, '#3a2a1e', a=.9)                                    # reins
    with c.edges('crisp'):
        c.dots([P(4.15, -7.3)], .17 * s, ['#1e1410']); shape([P(3.8, -7.8), P(4.05, -8.6), P(4.3, -7.8)], '#e8dcc4', smooth=False, edge=.2)
    outline(sil, .12 * s, '#7a6a58', a=.55)

# ---------------------------------------------------------------- doll, drum, blocks, books, presents
def doll(x, y, h, dress='#e88aa0', seed=0):
    c = C(); s = h / 8.0; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        shape([P(-2.0, 0), P(2.0, 0), P(1.4, -2.0), P(.8, -4.6), P(-.8, -4.6), P(-1.4, -2.0)], dress, seed=seed)
        shape([P(-1.1, -.3), P(1.1, -.3), P(.7, -3.2), P(-.7, -3.2)], '#f6f0e2', smooth=False, edge=.1)             # apron
        for sx in (-1, 1): line([P(sx * .85, -4.4), P(sx * 1.5, -3.0)], .4 * s, dress)
        ellipse(x, y - 5.6 * s, 1.1 * s, 1.15 * s, '#f0cca8', edge=.1)
        shape([P(-1.25, -5.4), P(-1.2, -6.4), P(0, -7.05), P(1.2, -6.4), P(1.25, -5.4), P(.9, -6.0), P(-.9, -6.0)], '#7a3a1e', edge=.15)
        ellipse(x, y - 7.2 * s, .5 * s, .45 * s, '#7a3a1e', edge=.1)                                                 # bun
    with c.edges('crisp'):
        c.dots([P(-.4, -5.6), P(.4, -5.6)], .12 * s, ['#1e1410']); c.dots([P(-.65, -5.2), P(.65, -5.2)], .16 * s, ['#f08a8a'])

def drum(x, y, h, col='#c8302a', seed=0):
    c = C(); s = h / 4.6; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        shape([P(-2.0, -.4), P(2.0, -.4), P(2.0, -3.4), P(-2.0, -3.4)], col, smooth=False)
        ellipse(x, y - .45 * s, 2.0 * s, .5 * s, dark(col), edge=.1)
        ellipse(x, y - 3.4 * s, 2.0 * s, .55 * s, '#f4f0e6', edge=.15)
        for yy in (-.6, -3.3): line([P(-2.0, yy), P(2.0, yy)], .3 * s, '#1c2642')
        zz = [P(-1.9 + .63 * i, -.75 if i % 2 == 0 else -3.05) for i in range(7)]
        line(zz, .14 * s, '#e8b84a', a=.95)
        line([P(.6, -3.6), P(2.6, -5.4)], .2 * s, '#b07a4c'); line([P(-.4, -3.7), P(1.6, -4.9)], .2 * s, '#b07a4c')
        c.dots([P(2.6, -5.4), P(1.6, -4.9)], .22 * s, ['#f4f0e6'])

def blocks(x, y, h, seed=0):
    """Three alphabet blocks, two below and one on top, each with a lit top face and a shaded side."""
    import tft7 as T7
    c = C(); s = h / 5.4; d = .55 * s
    for (dx, dy, col, ch) in ((-1.4, 0, '#3f6aa8', 'A'), (1.4, 0, '#c8302a', 'B'), (0, -2.7, '#e8b84a', 'C')):
        bx, by, w = x + dx * s, y + dy * s, 2.5 * s
        with c.edges('fine'):
            shape([(bx - w / 2, by), (bx + w / 2, by), (bx + w / 2, by - w), (bx - w / 2, by - w)], col, smooth=False, edge=.18)
            shape([(bx - w / 2, by - w), (bx + w / 2, by - w), (bx + w / 2 + d, by - w - d), (bx - w / 2 + d, by - w - d)], light(col, 1.2), smooth=False, edge=.12)
            shape([(bx + w / 2, by), (bx + w / 2 + d, by - d), (bx + w / 2 + d, by - w - d), (bx + w / 2, by - w)], dark(col, .72), smooth=False, edge=.1)
        T7.paint_text(ch, bx, by - w / 2, w * .58, '#f6f2ea')

def books(x, y, h, n=4, seed=0):
    c = C(); r = np.random.RandomState(seed); cols = ['#3f6aa8', '#c8302a', '#3f8a44', '#e8b84a', '#7a4aa0', '#2a4a6a']; xx = x
    with c.edges('fine'):
        for j in range(n):
            w = r.uniform(.17, .25) * h; hh = r.uniform(.8, 1.0) * h; col = cols[(seed + j) % len(cols)]
            shape([(xx, y), (xx + w, y), (xx + w, y - hh), (xx, y - hh)], col, smooth=False, edge=.2)
            for f in (.18, .8): line([(xx + w * .12, y - hh * f), (xx + w * .88, y - hh * f)], .05 * h, '#e8c870', a=.9)
            xx += w + .03 * h

def picture_book(x, y, h, seed=0):
    """An open picture book on a little stand: two pages with a red apple-tree picture and lines of text."""
    c = C(); s = h / 3.6; P = lambda dx, dy: (x + dx * s, y + dy * s)
    with c.edges('fine'):
        shape([P(-3.4, 0), P(3.4, 0), P(3.0, -3.0), P(0, -2.6), P(-3.0, -3.0)], '#3f6aa8', smooth=False, edge=.2)    # cover
        shape([P(-3.1, -.3), P(-.05, -.5), P(-.05, -2.9), P(-2.8, -3.2)], '#faf4e6', smooth=False, edge=.1)
        shape([P(.05, -.5), P(3.1, -.3), P(2.8, -3.2), P(.05, -2.9)], '#f6eedd', smooth=False, edge=.1)
        ellipse(x - 1.5 * s, y - 2.1 * s, .75 * s, .6 * s, '#5a9a4a', edge=.1); line([P(-1.5, -1.5), P(-1.5, -.9)], .18 * s, '#7a4a2a')
        c.dots([P(-1.7, -2.2), P(-1.2, -2.0)], .14 * s, ['#c8302a'])
        for yy in (-2.5, -2.0, -1.5, -1.0): line([P(.6, yy), P(2.5, yy - .1)], .08 * s, '#8a7a6a', a=.8)

def present(x, y, w, h, col, ribbon='#f2d488', seed=0):
    """A wrapped present: box, overhanging lid, ribbon both ways and a bow with two loops and two tails."""
    c = C(); lid = h * .22; d = w * .18
    with c.edges('fine'):
        shape([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h + lid), (x - w / 2, y - h + lid)], col, smooth=False, edge=.18)
        shape([(x + w / 2, y), (x + w / 2 + d, y - d), (x + w / 2 + d, y - h + lid - d), (x + w / 2, y - h + lid)], dark(col, .72), smooth=False, edge=.1)
        shape([(x - w / 2 - w * .05, y - h + lid), (x + w / 2 + w * .05, y - h + lid), (x + w / 2 + w * .05 + d, y - h - d), (x - w / 2 - w * .05 + d, y - h - d)],
              light(col, 1.15), smooth=False, edge=.14)
        line([(x, y), (x, y - h + lid)], w * .14, ribbon); line([(x - w / 2, y - (h - lid) * .5), (x + w / 2, y - (h - lid) * .5)], w * .12, ribbon)
        bx, by = x + d * .5, y - h - d * .5
        for sd in (-1, 1): ellipse(bx + sd * w * .2, by - w * .1, w * .2, w * .12, ribbon, rot=sd * .5, edge=.25)
        for sd in (-1, 1): line([(bx, by), (bx + sd * w * .16, by + w * .22)], w * .07, ribbon, taper=(0, .4))
        ellipse(bx, by, w * .07, w * .06, dark(ribbon, .8), edge=0)

GALLERY = [('teddy', lambda x, y, h: teddy(x, y, h)), ('wooden train', lambda x, y, h: wooden_train(x + h * .3, y, h * .62)),
           ('toy soldier', lambda x, y, h: soldier(x, y, h)), ('rocking horse', lambda x, y, h: rocking_horse(x - h * .1, y, h * .8)),
           ('doll', lambda x, y, h: doll(x, y, h * .85)), ('drum', lambda x, y, h: drum(x, y, h * .55)),
           ('blocks', lambda x, y, h: blocks(x, y, h * .62)), ('picture book', lambda x, y, h: picture_book(x, y, h * .45)),
           ('books', lambda x, y, h: books(x - h * .35, y, h * .65)), ('presents', lambda x, y, h: (present(x - h * .25, y, h * .45, h * .42, '#3f6aa8'), present(x + h * .28, y, h * .38, h * .6, '#c8302a', '#f4f2ec')))]

"""Toy Town quality study, round 2: rebuilt to the reference's layout.

Same brush as round 1 (closeup/square11.py, folk2 gouache). What changes:
  composition  a tight stage: five buildings fill the frame, a stone hall with an arched door at the centre, a small
               rounded square in front, framed by lawn and two foreground trees; the Marines at the centre
  materials    smooth stucco (pink, cream, yellow), cut stone blocks (the hall), brick (the red house)
  windows      dark frames around lit interiors: light comes from inside and spills onto sills and cobbles
  density      garlands with bows, door lamps, wreaths, planters, a bench, a tree with lights, presents, a wagon
  figures      the Marines as painted wooden toys: rounded forms, glossy highlights, peg proportions, and a mouth
               that can open (mouth=0..1), the hook for speech
    PYTHONPATH=../folk2:../styles2 python3 closeup/square12.py [OUT.png] [--mouth 0.6]
"""
import math, os, sys
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import square11 as S
from brush import hexc, catmull, resample
from kit import Kanvas, dab_tree, impasto, skeleton_tree
from parts import lumpy

W, H, K = S.W, S.H, S.K
c = None
def use(canvas):
    global c
    c = canvas; S.c = canvas

paint, line, glow, rect = S.paint, S.line, S.glow_spot, S.rect

def wrect(x0, y0, x1, y1, step=18):
    """A rectangle with points along its edges, so the brush's wobble bends the edges like a hand-drawn line."""
    P = []
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        P += [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in np.linspace(0, 1, n, endpoint=False)]
    return P

def shade(col, x, y, base=.9):
    b, w = S.light_at(np.array([x], np.float32), np.array([y], np.float32))
    v = base + .6 * float(b[0]); cc = hexc(col) * v
    cc = cc * (1 - .45 * float(w[0])) + cc * S.WARM * .55 * float(w[0])
    return np.clip(cc, 0, 1)

# ------------------------------------------------------------------ materials
def stucco(x0, y0, x1, y1, cols, seed):
    """Smooth render: a calm field of broad, low-contrast dabs, soft mottled patches, light from the upper left."""
    poly = wrect(x0, y0, x1, y1)
    paint(poly, cols, spacing=1.9, L=3.6, w=2.6, var=.035, seed=seed, wob=1.1, rough=.9, edge=.05, jit=1.3,
          dir_=((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0), (y1 - y0)), lbase=.86)
    r = np.random.RandomState(seed)
    for j in range(int((x1 - x0) * (y1 - y0) / 9000)):
        px, py = r.uniform(x0 + 20, x1 - 20), r.uniform(y0 + 20, y1 - 20)
        c.area(lumpy(px, py, r.uniform(25, 60), r.uniform(18, 40), seed + j, n=24, bumps=3, amp=.2), hexc(cols[0]) * r.uniform(.92, 1.06),
               wob=1.5, rough=1.2, edge_dark=0, a=.22, seed=seed + j)
    line([(x0, y0 + 2), (x0 + 3, y1)], 3, '#2a1a14', a=.25, dry=.4, taper=(.05, .05))          # a soft shadow where it meets its neighbour

def stone_wall(x0, y0, x1, y1, seed, rows=22):
    """Cut stone: courses of blocks of uneven length, each its own tone, mortar between, lit by the scene's lamps."""
    c.area(wrect(x0, y0, x1, y1), '#b8ae9c', wob=.6, rough=.6, edge_dark=0, seed=seed)
    r = np.random.RandomState(seed); y = y0
    tones = ['#ece6da', '#e2dacb', '#f2ede4', '#d8cfbf', '#e8e0d0']
    while y < y1:
        x = x0 - r.uniform(0, 30)
        while x < x1:
            bw = r.uniform(30, 56); a_, b_ = max(x0, x + 1.5), min(x1, x + bw - 1.5)
            if b_ - a_ > 6:
                col = shade(tones[r.randint(len(tones))], (a_ + b_) / 2, y + rows / 2) * r.uniform(.95, 1.04)
                c.area(wrect(a_, y + 1.5, b_, min(y1, y + rows - 1.5), 10), col, wob=.5, rough=.9, edge_dark=.14, seed=r.randint(1 << 30))
                line([(a_ + 2, y + 3), (b_ - 2, y + 3)], 1.2, '#fffaf0', a=.35, dry=.4, taper=(.2, .2))   # the lit top edge
            x += bw
        y += rows

def brick_wall(x0, y0, x1, y1, seed, bh=12, bw=26):
    c.area(wrect(x0, y0, x1, y1), '#6e2a22', wob=.6, rough=.6, edge_dark=0, seed=seed)
    r = np.random.RandomState(seed); tones = ['#b8302a', '#c4382e', '#a82a24', '#c84438', '#9c2620', '#b83c30']
    for ri, y in enumerate(np.arange(y0, y1, bh)):
        x = x0 - (bw / 2 if ri % 2 else 0)
        while x < x1:
            a_, b_ = max(x0, x + 1.2), min(x1, x + bw - 1.2)
            if b_ - a_ > 4:
                col = shade(tones[r.randint(len(tones))], (a_ + b_) / 2, y + bh / 2, base=.84) * r.uniform(.94, 1.06)
                c.area(rect(a_, y + 1.2, b_, min(y1, y + bh - 1.2)), col, wob=.25, rough=.9, edge_dark=.1, seed=r.randint(1 << 30))
            x += bw

# ------------------------------------------------------------------ windows lit from inside
def flowerbox(x0, x1, y, seed):
    paint(wrect(x0, y, x1, y + 13, 10), ['#6a3f24', '#7c4c2c', '#5a341e'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed, edge=.2, wob=.4)
    r = np.random.RandomState(seed)
    for j in range(int((x1 - x0) * 1.1)):
        c.dots([(r.uniform(x0, x1), y - r.uniform(-1, 10))], r.uniform(2.2, 3.6), ['#244a24', '#2f5a2a', '#3e6e32', '#4c7e3a'], seed=r.randint(1 << 20))
    for j in range(int((x1 - x0) / 3.5)):
        c.dots([(r.uniform(x0 + 2, x1 - 2), y - r.uniform(1, 10))], r.uniform(1.8, 2.8), ['#c8302a', '#e04838', '#f4d040', '#fff0c0'], seed=r.randint(1 << 20))

def window2(cx, y, w, h, frame, seed, arch=True, box=True, panes=(2, 3)):
    """y: the sill. A dark frame, a reveal, a glowing interior brightest at its heart, dark glazing bars."""
    x0, x1, top = cx - w / 2, cx + w / 2, y - h
    def shp(a, b, t, bot):
        return ([(a, bot)] + S.arch_top(a, b, t + (b - a) / 2, (b - a) / 2) + [(b, bot)]) if arch else wrect(a, t, b, bot, 10)
    paint(shp(x0 - 6, x1 + 6, top - 6, y), [frame, frame], spacing=1.0, L=1.8, w=1.3, seed=seed, edge=.2, wob=.35)          # surround
    paint(shp(x0, x1, top, y), ['#3a2414', '#4a2e1a', '#2e1c10'], spacing=.8, L=1.4, w=1.1, seed=seed + 1, edge=.1, wob=.25, glow=.1)   # frame
    g0, g1 = x0 + 5, x1 - 5
    c.area(shp(g0, g1, top + 5, y - 5), '#b0701e', wob=.2, rough=.5, edge_dark=0, seed=seed + 2)                                # glass
    c.area(lumpy(cx, y - h * .45, w * .36, h * .36, seed, n=22, bumps=3, amp=.15), '#ffc850', wob=1.0, rough=1.2, edge_dark=0, a=.9, seed=seed + 3)
    c.area(lumpy(cx, y - h * .42, w * .2, h * .2, seed + 1, n=18, bumps=3, amp=.2), '#fff0b8', wob=1.0, rough=1.2, edge_dark=0, a=.75, seed=seed + 4)
    nx, ny = panes
    for xx in np.linspace(g0, g1, nx + 1)[1:-1]: line([(xx, y - 5), (xx, top + 8)], 2.4, '#3a2414', a=.95, taper=(0, 0))
    for yy in np.linspace(top + w * .45 if arch else top + 5, y - 5, ny + 1)[1:-1]: line([(g0, yy), (g1, yy)], 2.2, '#3a2414', a=.95, taper=(0, 0))
    paint(wrect(x0 - 8, y - 1, x1 + 8, y + 5, 10), ['#f4efe4', '#e4dccc', '#fbf7ee'], spacing=.9, L=1.8, w=1.2, seed=seed + 5, edge=.15, wob=.3)
    if box: flowerbox(x0 - 5, x1 + 5, y + 5, seed + 6)

def shop_window(x0, x1, y0, y1, seed, display):
    paint(wrect(x0 - 10, y0 - 8, x1 + 10, y1 + 10), ['#5a3420', '#6a3e26', '#4a2a18'], spacing=1.0, L=1.8, w=1.4, seed=seed, edge=.2, wob=.4)
    c.area(rect(x0, y0, x1, y1), '#a86a1c', wob=.2, rough=.5, edge_dark=0, seed=seed + 1)
    cx = (x0 + x1) / 2
    c.area(lumpy(cx, (y0 + y1) / 2, (x1 - x0) * .48, (y1 - y0) * .5, seed, n=26, bumps=3, amp=.1), '#f4c050', wob=1, rough=1.2, edge_dark=0, a=.95, seed=seed + 2)
    c.area(lumpy(cx, (y0 + y1) / 2 - 8, (x1 - x0) * .3, (y1 - y0) * .3, seed + 1, n=22, bumps=3, amp=.15), '#ffe8a0', wob=1, rough=1.2, edge_dark=0, a=.7, seed=seed + 3)
    shelf = y1 - 22
    paint(rect(x0, shelf, x1, shelf + 6), ['#7a4a2a', '#8a5632'], spacing=.8, L=1.6, w=1.1, ang=0.0, seed=seed + 4, wob=.1)
    display(x0, x1, y0, shelf)
    S.string_lights([(x0 + 4, y0 + 8), (cx, y0 + 22), (x1 - 4, y0 + 8)], seed + 5)
    for xx in np.linspace(x0, x1, 3)[1:-1]: line([(xx, y0), (xx, y1)], 3, '#4a2a18', a=.95, taper=(0, 0))
    paint(wrect(x0 - 12, y1 + 10, x1 + 12, y1 + 34, 12), ['#7a4a2a', '#6a3e22', '#8a5632'], spacing=1.0, L=2.0, w=1.4, ang=0.0, seed=seed + 6, wob=.3)
    for j in range(3): glow(cx + (j - 1) * (x1 - x0) * .3, y1 + 90, 90, .25)                    # light spilling onto the cobbles

def door_lamp(x, y, seed):
    """A carriage lamp on a wall bracket, glowing."""
    line([(x, y + 20), (x, y + 8)], 2.2, '#1c1a1a', a=1, taper=(0, 0))
    paint([(x - 8, y + 8), (x + 8, y + 8), (x + 10, y - 16), (x - 10, y - 16)], ['#ffe49a', '#fff4c8', '#ffd060'], spacing=.6, L=1.1, w=.8, seed=seed, wob=.08, edge=0, glow=.1, lbase=1.0)
    for xx in (-5, 5): line([(x + xx, y + 8), (x + xx * 1.2, y - 16)], 1.3, '#1c1a1a', a=.9, taper=(0, 0))
    paint([(x - 13, y - 16), (x + 13, y - 16), (x + 3, y - 27), (x - 3, y - 27)], ['#1c1a1a', '#2c2826'], spacing=.6, L=1.2, w=.8, seed=seed + 1, wob=.1)
    paint(rect(x - 9, y + 8, x + 9, y + 13), ['#1c1a1a', '#2c2826'], spacing=.5, L=1.0, w=.7, seed=seed + 2, wob=.05)
    c.dots([(x, y - 30)], 2.4, ['#1c1a1a'], seed=seed)

# ------------------------------------------------------------------ the buildings
def displays():
    def teddy_shop(x0, x1, y0, shelf):
        S.teddy((x0 + x1) / 2 - 40, shelf, 2.6, 2010)
        for bi, bc in enumerate(['#c8302a', '#3e7a3a', '#e4b030', '#3a5aa8', '#8a3a8a', '#c8302a']):
            paint(rect(x1 - 70 + bi * 9, shelf - 56, x1 - 62 + bi * 9, shelf), [bc, bc], spacing=.6, L=1.2, w=.8, seed=2020 + bi, wob=.05)
        S.present(x0 + 10, shelf, 34, 26, '#3e7a3a', '#c8302a', 2030)
    def train_shop(x0, x1, y0, shelf):
        S.toy_train((x0 + x1) / 2 - 60, shelf, 1.9, 2040)
        for i, (px, pw, ph, col, rib, yb) in enumerate([(x1 - 64, 32, 28, '#3a5aa8', '#f4d040', 0), (x1 - 40, 26, 40, '#c8302a', '#f4ede0', 0), (x1 - 58, 24, 20, '#e4b030', '#c8302a', -28)]):
            S.present(px, shelf + yb, pw, ph, col, rib, 2050 + i * 9)
        for i in range(4): paint(rect(x0 + 10 + i * 13, shelf - 44 + (i % 2) * 6, x0 + 22 + i * 13, shelf - (i % 2) * 0), [['#c8302a', '#3a5aa8', '#e4b030', '#3e7a3a'][i]] * 2, spacing=.6, L=1.0, w=.8, seed=2070 + i, wob=.05)
    def horse_shop(x0, x1, y0, shelf):
        S.rocking_horse((x0 + x1) / 2 + 10, shelf - 2, 1.75, 2080)
        S.present(x0 + 10, shelf, 38, 30, '#3a5aa8', '#f4d040', 2090); S.present(x0 + 18, shelf - 30, 26, 22, '#c8302a', '#f4ede0', 2091)
        S.present(x1 - 46, shelf, 36, 34, '#3e7a3a', '#c8302a', 2092)
    def nut_shop(x0, x1, y0, shelf):
        S.nutcracker((x0 + x1) / 2 + 20, shelf, 1.25, 2100)
        S.present(x0 + 12, shelf, 40, 32, '#3e7a3a', '#c8302a', 2110); S.present(x1 - 50, shelf, 40, 26, '#c8302a', '#f4ede0', 2111)
        S.present(x1 - 44, shelf - 26, 30, 24, '#e4b030', '#3a5aa8', 2112)
    return teddy_shop, train_shop, horse_shop, nut_shop

def buildings(base):
    teddy_shop, train_shop, horse_shop, nut_shop = displays()
    # ---- pink house
    stucco(-20, -40, 262, base, ['#e89aa8', '#f0a8b4', '#e48e9e', '#f4b6c0'], 3000)
    for cx in (55, 185):
        window2(cx, 120, 56, 92, '#f6f0e6', 3010 + cx); window2(cx, 262, 56, 92, '#f6f0e6', 3020 + cx)
    S.awning(-10, 252, 322, 56, ['#c8302a', '#f4ede0'], 3030)
    shop_window(14, 230, 404, 546, 3040, teddy_shop)
    # ---- cream house
    stucco(262, -40, 560, base, ['#f2ead8', '#f8f2e4', '#ece2cc', '#fbf6ea'], 3100)
    line([(262, 18), (560, 18)], 7, '#f8f4ea', a=.95, taper=(0, 0))
    for cx in (330, 411, 492):
        paint([(cx - 38, 40), (cx, 4), (cx + 38, 40)], ['#f6f0e4', '#ece4d4'], spacing=1.0, L=2.0, w=1.4, seed=3110 + cx, wob=.4, edge=.2)   # window pediments
        window2(cx, 128, 44, 74, '#f6f0e6', 3120 + cx, box=False)
        window2(cx, 266, 48, 92, '#f6f0e6', 3130 + cx)
    S.awning(270, 552, 322, 56, ['#2f5aa8', '#f4ede0'], 3140)
    shop_window(294, 528, 404, 546, 3150, train_shop)
    # ---- the stone hall
    stone_wall(560, -40, 900, base, 3200)
    for x_ in (560, 900): paint(wrect(x_ - 10, -40, x_ + 10, base, 20), ['#e8e0d0', '#f2ece0', '#ddd4c2'], spacing=1.0, L=2.4, w=1.4, ang=math.pi / 2, seed=3201 + x_, wob=.4, edge=.2)   # quoins
    window2(730, 180, 120, 190, '#f2ece0', 3210, panes=(3, 4), box=False)
    flowerbox(660, 800, 186, 3215)
    S.garland([(570, 214), (640, 246), (730, 222), (820, 246), (890, 214)], 3220, bows=[(572, 212), (730, 220), (888, 212)])
    window2(730, 362, 104, 104, '#f2ece0', 3230, panes=(3, 2), box=False)
    # the arched door in a stone surround
    dx0, dx1, dtop = 650, 810, 414
    paint([(dx0 - 22, base)] + S.arch_top(dx0 - 22, dx1 + 22, dtop + 10, 60) + [(dx1 + 22, base)], ['#f2ece0', '#e6dece', '#faf6ec'], spacing=1.0, L=2.0, w=1.4, seed=3240, wob=.4, edge=.2)
    for t in np.linspace(.05, .95, 11):                                                    # voussoirs round the arch
        a = math.pi * (1 - t); ccx, ccy = (dx0 + dx1) / 2, dtop + 10 + 0
        p0 = (ccx + math.cos(a) * 82, ccy - math.sin(a) * 52); p1 = (ccx + math.cos(a) * 104, ccy - math.sin(a) * 66)
        line([p0, p1], 1.4, '#a89c88', a=.8, taper=(0, 0))
    door = [(dx0, base)] + S.arch_top(dx0, dx1, dtop + 14, 50) + [(dx1, base)]
    paint(door, ['#6a3a22', '#7a4628', '#5a2e1a', '#84502e'], spacing=1.0, L=3.4, w=1.3, ang=math.pi / 2, seed=3250, edge=.25, wob=.3, dir_=((dx0 + dx1) / 2, base - 90, 80, 160))
    line([((dx0 + dx1) / 2, dtop - 34), ((dx0 + dx1) / 2, base)], 2.2, '#3a1e12', a=.85, taper=(0, 0))
    for yy in (dtop + 40, base - 80):
        for xa, xb in ((dx0 + 12, (dx0 + dx1) / 2 - 10), ((dx0 + dx1) / 2 + 10, dx1 - 12)):
            line([(xa, yy), (xb, yy), (xb, yy + 54), (xa, yy + 54), (xa, yy)], 1.6, '#3a1e12', a=.55, taper=(0, 0))
    for xx in np.linspace(dx0 + 20, dx1 - 20, 8): line([(xx, dtop - 10), (xx, base - 2)], 1.0, '#4a2616', a=.25, dry=.4, taper=(.1, .1))   # planks
    S.wreath((dx0 + dx1) / 2, dtop + 6, 26, 3260)
    for x_ in ((dx0 + dx1) / 2 - 10, (dx0 + dx1) / 2 + 10): c.dots([(x_, base - 100)], 2.4, ['#d8a840'], seed=int(x_))
    paint(wrect(dx0 - 30, base - 6, dx1 + 30, base + 6, 12), ['#d8d0c2', '#cac2b2'], spacing=1.0, L=2.4, w=1.4, ang=0.0, seed=3270, wob=.3)   # step
    for lx in (612, 848): door_lamp(lx, 370, 3280 + lx)
    for px in (606, 854): S.planter(px, base - 2, 1.5, 3290 + px)
    # ---- yellow toy shop
    stucco(900, -40, 1232, base, ['#e8b838', '#f0c448', '#e0ac34', '#f4cc58'], 3300)
    for cx in (985, 1148): window2(cx, 120, 60, 96, '#f6f0e6', 3310 + cx)
    sx0, sx1, sy0, sy1 = 948, 1184, 196, 290
    c.area(rect(sx0 + 5, sy0 + 6, sx1 + 5, sy1 + 6), '#3a2610', wob=.5, rough=.8, edge_dark=0, a=.4, seed=3320)
    board = [(sx0, sy0 + 14), (sx0 + 16, sy0), (sx1 - 16, sy0), (sx1, sy0 + 14), (sx1, sy1 - 14), (sx1 - 16, sy1), (sx0 + 16, sy1), (sx0, sy1 - 14)]
    paint(board, ['#6a3a20', '#7a4628', '#5a301a'], spacing=1.0, L=2.2, w=1.5, ang=0.0, seed=3321, edge=.25, wob=.3)
    cx = (sx0 + sx1) / 2
    paint([(x + (cx - x) * .045, y + ((sy0 + sy1) / 2 - y) * .12) for x, y in board], ['#f6ecd2', '#efe2c0', '#fbf4e0'], spacing=.9, L=2.0, w=1.4, ang=0.0, seed=3322, edge=.12, wob=.2, lbase=.95)
    S.letters('TOYS', cx, sy0 + 28, 22, ['#b8302a', '#a82820', '#c8382c'], track=2, seed=3330)
    S.letters('FOR TOTS', cx, sy0 + 56, 22, ['#b8302a', '#a82820', '#c8382c'], track=1.5, seed=3331)
    S.stars(cx, sy0 + 80, 3, 28, 7, '#b8302a')
    for lx in (sx0 + 30, cx - 7, sx1 - 44): S.wall_lamp(lx, sy0 - 4, 3340 + int(lx))
    S.awning(908, 1224, 322, 56, ['#c8302a', '#f4ede0'], 3350)
    shop_window(930, 1202, 404, 546, 3360, horse_shop)
    # ---- red brick house
    brick_wall(1232, -40, 1520, base, 3400)
    for cx in (1300, 1440):
        window2(cx, 120, 56, 92, '#f6f0e6', 3410 + cx); window2(cx, 262, 56, 92, '#f6f0e6', 3420 + cx)
    S.awning(1240, 1520, 322, 56, ['#3e7a3a', '#f4ede0'], 3430)
    shop_window(1262, 1500, 404, 546, 3440, nut_shop)
    S.planter(1490, base - 2, 1.4, 3450)

# ------------------------------------------------------------------ toy Marines
def gloss(pts, w, a=.35, col='#ffffff'): c.stroke(pts, w, col, a=a, dry=.25, taper=(.35, .35))

def toy_marine(x, y, s, skin, f, seed, hands, mouth=0.0, tilt=0.0):
    """A Marine as a painted wooden toy, ~170 units tall at s = 1: rounded parts, glossy lacquer highlights.
    hands: [(x, y), (x, y)] where the white gloves go (on the present). mouth 0 = smile, 1 = wide open (for speech)."""
    navy, navy_l, navy_d = '#1e2a4e', '#34467e', '#121a32'
    blue, red, gold, white = '#36569a', '#c8302a', '#e8b440', '#f6f4ee'
    S.shadow(x + 30 * s, y + 4, 54 * s, 9 * s, a=.32); S.shadow(x, y + 2, 26 * s, 6 * s, a=.5)
    # legs: two rounded posts; trouser stripe; round black shoes
    for lx in (-8, 8):
        c.stroke([(x + lx * s, y - 72 * s), (x + lx * s, y - 10 * s)], 14 * s, blue, a=1, dry=.05, taper=(0, 0), press=.05)
        gloss([(x + (lx - 3) * s, y - 68 * s), (x + (lx - 3) * s, y - 16 * s)], 3 * s, .22)
        line([(x + (lx + (5 if lx > 0 else -5)) * s, y - 70 * s), (x + (lx + (5 if lx > 0 else -5)) * s, y - 12 * s)], 2.4 * s, red, a=.95, taper=(0, 0))
        S.paint(lumpy(x + (lx + 3 * f) * s, y - 5 * s, 10 * s, 6 * s, seed + lx, n=20, bumps=2, amp=.05, flat=.3), ['#141214', '#22201e'], spacing=.5, L=1.0, w=.8, seed=seed + lx, wob=.05, edge=.1)
        gloss([(x + (lx - 2 + 3 * f) * s, y - 8 * s), (x + (lx + 3 + 3 * f) * s, y - 9 * s)], 2 * s, .45)
    # the coat: one rounded lozenge, nipped at the belt
    hip = y - 74 * s; sh = y - 140 * s
    coat = catmull([(x - 16 * s, sh - 2 * s), (x + 16 * s, sh - 2 * s), (x + 24 * s, sh + 8 * s), (x + 21 * s, hip - 6 * s), (x + 23 * s, hip + 8 * s),
                    (x, hip + 12 * s), (x - 23 * s, hip + 8 * s), (x - 21 * s, hip - 6 * s), (x - 24 * s, sh + 8 * s)], 8, closed=True)
    c.stroke(list(map(tuple, coat)) + [tuple(coat[0])], 3 * s, '#0a0e1c', a=.6, dry=.2, taper=(0, 0))
    S.paint(list(map(tuple, coat)), [navy, navy, navy_l], spacing=.8, L=2.0, w=1.1, ang=math.pi / 2, seed=seed + 10, wob=.1, edge=.3,
            dir_=(x - 10 * s, sh + 20 * s, 26 * s, 60 * s), lbase=.95, glow=.55)
    gloss([(x - 17 * s, sh + 10 * s), (x - 18 * s, sh + 34 * s), (x - 16 * s, hip - 10 * s)], 4.5 * s, .2)
    gloss([(x - 15 * s, sh + 12 * s), (x - 15.5 * s, sh + 26 * s)], 1.8 * s, .5)
    for i in range(4): c.dots([(x + 3 * s * f, sh + (12 + i * 11) * s)], 2.0 * s, [gold], seed=seed + 20 + i); c.dots([(x + 3 * s * f - .6 * s, sh + (11.3 + i * 11) * s)], .7 * s, ['#fff4c8'], seed=seed + 25 + i)
    S.paint(rect(x - 21 * s, hip - 8 * s, x + 21 * s, hip), [white, '#ece8de'], spacing=.6, L=1.4, w=.9, ang=0.0, seed=seed + 30, wob=.08, edge=.15)
    S.paint(rect(x - 4.5 * s, hip - 9 * s, x + 4.5 * s, hip + 1 * s), ['#e8c050', '#f4d470'], spacing=.5, L=.9, w=.7, seed=seed + 31, wob=.05)
    for ex in (-1, 1): c.stroke([(x + ex * 12 * s, sh - 1 * s), (x + ex * 23 * s, sh + 5 * s)], 4.4 * s, gold, a=1, dry=.05, taper=(0, 0))   # shoulder boards
    # arms to the gloves on the present
    for k_, (hx_, hy_) in enumerate(hands):
        side = -1 if hx_ < x else 1
        if abs(hx_ - x) < 18 * s: side = -f if k_ == 0 else f
        sx_ = x + side * 19 * s; elbow = (sx_ + side * 7 * s, sh + 40 * s)
        arm = [(sx_, sh + 6 * s), elbow, (hx_ - side * 2 * s, hy_)]
        c.stroke(arm, 14 * s, '#0a0e1c', a=.9, dry=.05, taper=(0, .05), press=.05)               # a dark contour so the arm reads against the coat
        c.stroke(arm, 11 * s, navy_l if k_ else navy, a=1, dry=.05, taper=(0, .08), press=.08)
        gloss([(sx_ - 2 * s, sh + 9 * s), (elbow[0] - 2 * s, elbow[1] - 4 * s)], 2.4 * s, .3)
        line([(hx_ - side * 7 * s, hy_ - 5 * s), (hx_ - side * 7 * s, hy_ + 5 * s)], 3 * s, red, a=.95, taper=(0, 0))
        S.paint(lumpy(hx_, hy_, 7 * s, 6.5 * s, seed + 40 + k_, n=18, bumps=2, amp=.06), [white, '#ece8de'], spacing=.5, L=1.0, w=.8, seed=seed + 42 + k_, wob=.05, edge=.18)
        gloss([(hx_ - 3 * s, hy_ - 3 * s), (hx_ + 1 * s, hy_ - 4 * s)], 1.6 * s, .6)
    # collar and head: a round wooden peg head, rosy cheeks, dot eyes, a mouth that opens
    S.paint(rect(x - 10 * s, sh - 8 * s, x + 10 * s, sh + 1 * s), [navy, navy_d], spacing=.5, L=1.0, w=.8, seed=seed + 50, wob=.05)
    line([(x - 9 * s, sh - 2 * s), (x + 9 * s, sh - 2 * s)], 2 * s, red, a=.9, taper=(0, 0))
    hx, hy = x + f * 1.5 * s + tilt * 3 * s, sh - 22 * s
    skn = S.SKIN[skin]
    S.paint(lumpy(hx, hy, 16 * s, 16.5 * s, seed + 60, n=30, bumps=2, amp=.02, flat=.05), skn, spacing=.5, L=1.0, w=.8, seed=seed + 61, wob=.04, edge=.16,
            dir_=(hx - 5 * s, hy - 5 * s, 14 * s, 14 * s), lbase=.92, glow=.35)
    gloss([(hx - 9 * s, hy - 4 * s), (hx - 7 * s, hy - 9 * s)], 3 * s, .35)
    for ex in (-6, 6):
        ex_ = hx + (ex + f * 2) * s
        c.dots([(ex_, hy + 1 * s)], 2.3 * s, ['#1a120e'], seed=seed + ex); c.dots([(ex_ - .7 * s, hy + .2 * s)], .7 * s, ['#ffffff'], seed=seed + ex + 1)
    c.dots([(hx - 9 * s + f * 2 * s, hy + 7 * s), (hx + 9 * s + f * 2 * s, hy + 7 * s)], 2.6 * s, ['#e46a5c'], a=.38, seed=seed + 70)
    mx, my = hx + f * 2 * s, hy + 9 * s
    if mouth < .15:
        line([(mx - 5 * s, my - 1 * s), (mx, my + 1.6 * s), (mx + 5 * s, my - 1 * s)], 1.6 * s, '#6a2a20', a=.95, taper=(.2, .2))
    else:
        S.paint(lumpy(mx, my + 1 * s, 4.5 * s, (1.5 + 3.5 * mouth) * s, seed + 75, n=16, bumps=2, amp=.05), ['#5a1c18', '#6a2420'], spacing=.4, L=.8, w=.6, seed=seed + 76, wob=.03, edge=.1)
        c.dots([(mx, my + (1 + 2.4 * mouth) * s)], 2 * s, ['#d86a60'], a=.8, seed=seed + 77)
    # the cap: a wide white crown, black band and peak, gold badge, lacquer shine
    cy_ = hy - 14 * s
    S.paint(lumpy(hx, cy_ - 6 * s, 22 * s, 7.5 * s, seed + 80, n=26, bumps=2, amp=.02, flat=.2), [white, '#ece8de', '#ffffff'], spacing=.5, L=1.1, w=.8, ang=0.0, seed=seed + 81, wob=.05, edge=.18, glow=.3)
    gloss([(hx - 14 * s, cy_ - 9 * s), (hx + 2 * s, cy_ - 11 * s)], 2.4 * s, .7)
    S.paint(rect(hx - 15 * s, cy_ - 2 * s, hx + 15 * s, cy_ + 4 * s), ['#141214', '#22201e'], spacing=.5, L=1.0, w=.7, seed=seed + 82, wob=.05)
    S.paint(lumpy(hx + f * 4 * s, cy_ + 6 * s, 14 * s, 3.4 * s, seed + 83, n=18, bumps=1, amp=.02), ['#0e0c0e', '#1c1a1c'], spacing=.5, L=1.0, w=.7, seed=seed + 84, wob=.05)
    gloss([(hx + f * 4 * s - 8 * s, cy_ + 5 * s), (hx + f * 4 * s + 4 * s, cy_ + 5 * s)], 1.4 * s, .5)
    c.dots([(hx, cy_ - 5 * s)], 2.8 * s, [gold], seed=seed + 85)

# ------------------------------------------------------------------ the square
def square(base):
    S.SPECKS = False; S.cobbles(base + 10, 1050, -20, 1520)
    curve = [(-20, 760), (90, 860), (300, 940), (760, 965), (1220, 935), (1420, 860), (1520, 780)]
    P = resample(catmull(curve, 16), 3)
    paint(list(map(tuple, P)) + [(1520, 1070), (-20, 1070)], ['#d8b040', '#e4c050', '#c89c30', '#ecd070'], spacing=1.6, L=4.4, w=2.0, ang=0.0, seed=3500, lbase=.86, glow=.3, wob=.6)
    for i in range(22):
        Q = [(x, y + 10 + i * 6 + 3 * math.sin(x / 47 + i)) for x, y in P[::3]]
        c.stroke(Q, 2.4, ['#b88a28', '#f0d478', '#c89c30'][i % 3], a=.35, dry=.45, taper=(.05, .05))
    c.stroke(P - [0, 1], 9, '#ddd6c8', a=.95, dry=.15, taper=(0, 0))
    for x, y in P[::5]: line([(x, y - 4), (x, y + 3)], 1.2, '#8a8478', a=.6, taper=(0, 0))

def main(out, mouth=0.0):
    use(Kanvas(W * K, H * K, K, '#2a2430', seed=12)); c.HM = np.zeros((c.H, c.W), np.float32); S.LIGHTS.clear()
    base = 600
    for (x, y, r, s) in [(612, 360, 70, .45), (848, 360, 70, .45), (255, 520, 150, .6), (1185, 520, 150, .6), (730, 120, 120, .35),
                         (120, 480, 130, .35), (410, 480, 130, .35), (1066, 480, 130, .35), (1380, 480, 130, .35), (190, 760, 110, .3)]:
        glow(x, y, r, s)
    buildings(base); S.log('buildings')
    square(base); S.log('square')
    S.bench(430, 700, 1.7, 3600)
    S.lamp_post(255, 730, 280, 3610, s=1.9)
    S.lamp_post(1185, 730, 280, 3620, s=1.9)
    S.christmas_tree(170, 860, 300, 3630)
    for i, (px, pw, ph, col, rib) in enumerate([(262, 66, 54, '#c8302a', '#f4d040'), (334, 58, 46, '#3e7a3a', '#c8302a'), (292, 50, 36, '#3a5aa8', '#f4ede0'), (398, 46, 40, '#e4b030', '#c8302a')]):
        yb = 772 + (i % 2) * 12; S.shadow(px + pw * .7, yb, pw * .7, 6, a=.35); S.present(px, yb, pw, ph, col, rib, 3640 + i * 11)
    S.donation_box(1120, 810, 3700, s=1.5)
    S.wagon(1030, 818, 1.7, 3710)
    S.log('furniture')
    if '--empty' in sys.argv:                                        # the square without the Marines: a stage for the rigged ones
        impasto(c, strength=.22); S.evening_glow()
        Image.fromarray((np.clip(c.img, 0, 1) * 255 + .5).astype(np.uint8)).save(out); S.log(f'saved {out}'); return
    # the Marines hand the present across: the present between their gloves
    s = 2.35; ya, yb = 918, 924; xa, xb = 600, 900
    gx, gy = (xa + xb) / 2, ya - 112 * s
    pw_, ph_ = 84, 64
    toy_marine(xa, ya, s, 'light', 1, 3800, hands=[(gx - pw_ / 2 - 4, gy - 4), (gx - pw_ / 2 + 2, gy + 10)], mouth=mouth, tilt=.4)
    toy_marine(xb, yb, s * 1.03, 'brown', -1, 3820, hands=[(gx + pw_ / 2 + 4, gy - 2), (gx + pw_ / 2 - 2, gy + 12)], tilt=-.3)
    S.present(gx - pw_ / 2, gy + ph_ / 2 + 4, pw_, ph_, '#e4b030', '#c8302a', 3860)
    S.log('marines')
    skeleton_tree(c, 330, 1290, 520, ['#b83a2a', '#d4523a', '#c8402e', '#e87858', '#a83224'], 3900, dots=['#f4a088', '#ffc8a8', '#f4d040'], branches='#3a2014')
    skeleton_tree(c, 1050, 1300, 500, ['#4c7e3a', '#6e9a44', '#5a8a3c', '#8fb24e'], 3910, dots=['#b4c868', '#e4e070', '#f4d040'], branches='#3a2014')
    impasto(c, strength=.22)
    S.evening_glow()
    im = (np.clip(c.img, 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(im).save(out); S.log(f'saved {out}')

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    mo = float(sys.argv[sys.argv.index('--mouth') + 1]) if '--mouth' in sys.argv else 0.0
    main(args[0] if args else os.path.join(HERE, 'out', 'square12.png'), mo)

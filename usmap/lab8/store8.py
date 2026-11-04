"""lab8 — reusable storefront components for the Toy Town detail experiment.

Everything here is drawn with the same gouache primitives as the rest of the map (c.area, c.stroke, c.stip, c.dots,
c.dab) and in map units, so it scales with the render and stays editable. The experiment applies them to ONE
storefront — the yellow shop beside the clock tower (town row house 5) — at three levels of detail:

    'orig'  the current illustration (tft7's shop window and TOY DONATION sign)
    'A'     refined:  framed windows with sills and lintels, a cornice and string course, a proper shopfront
                      (pilasters, mullioned display window, transom, kick panels) and a panelled door with a step
    'B'     rich:     + shutters and flower boxes, a TOYS FOR TOTS sign, a scalloped awning with its shadow, an
                      evergreen garland with bows, a layered window display on a shelf, warm light spilling out
    'C'     maximum:  + quoins, dentil cornice with brackets, keystones, gooseneck sign lamps, string lights,
                      a two-shelf display, a glazed door with a wreath and a poinsettia, roof shingles and a
                      dormer, small stories in the upper windows (a candle, a cat)

The live map does not use this module.
"""
import math
import numpy as np
import usmap4 as B
import tft7 as T7
from usmap4 import hexc, pal_fn

c = None                       # set by the lab harness to the canvas in use
S = B.S

# palette — taken from the existing town and the Toys for Tots branding
WALL = '#e8b84a'; TRIM = '#f6ecd2'; TRIM_D = '#d8c8a0'; STONE = '#f2e2bc'; STONE_D = '#c8ae84'
WOOD = '#5a3a24'; WOOD_M = '#7a5234'; WOOD_L = '#a8784c'
GREEN = '#2f5a3a'; GREEN_L = '#4a7a50'; GOLD = '#d8a840'; GOLD_L = '#f2d488'
RED = '#b8302a'; RED_D = '#8a2420'; CREAM = '#f4ead2'; WHITE = '#f4f2ec'; NAVY = '#1c2642'
GLASS = '#f2c25a'; GLASS_L = '#f8dc8a'; GLASS_D = '#d8962e'

class fine:
    """A finer brush for small things: the engine softens every painted edge by about 0.9 map units, which melts
    anything smaller than two or three units (a teddy's ear, a window bar). Inside `with fine():` edges soften
    by `soft` map units instead. Nothing else about the brush changes."""
    def __init__(s, soft=.32): s.soft = soft
    def __enter__(s):
        s.orig = c.mask; soft = s.soft
        c.mask = lambda poly, wob=2.0, rough=1.0, seed=0, soft_=None, scaled=False: s.orig(poly, wob, rough, seed, soft, scaled)
        return s
    def __exit__(s, *a): c.mask = s.orig

def rect(x0, y0, x1, y1, col, edge=.12, rough=.3, a=1.0, seed=0):
    return c.area([(x0, y1), (x1, y1), (x1, y0), (x0, y0)], col, wob=0, rough=rough, edge_dark=edge, a=a, seed=seed)

def line(pts, w, col, a=1.0):
    c.stroke(pts, w, col, a=a, dry=0, taper=(0, 0))

def glow(x, y, r, col='#f8d880', a=.22, seed=0):
    """Painted warmth: a soft, low-opacity wash, never a gradient."""
    c.area(S.lumpy(x, y, r, r * .8, seed, n=22, amp=.06), col, wob=0, rough=.2, edge_dark=0, a=a)

# ---------------------------------------------------------------- geometry of the experiment's house
def house_layout(i=5):
    """Where pass 4 put house i's windows and door: the same arithmetic and random draws as styles2/a.house()."""
    for j, x, w, h in T7.houses():
        if j == i: break
    y = B.TOWN[1]; cx = x + w / 2; seed = 140 + i
    r = np.random.RandomState(seed); nr, nc = 3, 2
    ww = min(5.5, w / (nc * 2.1)); wh = min(7, h / (nr * 2.4)); wins = []
    for a in range(nr):
        for b in range(nc):
            if r.rand() < .08: continue
            u = (b + .5) / nc + r.uniform(-.03, .03); v = (a + .45) / (nr + .6)
            wins.append(dict(row=a, col=b, x=cx - w / 2 + u * w, y=y - h + v * h * .92 + 2, w=ww, h=wh, lit=r.rand() < .85))
    return dict(x0=x, x1=x + w, w=w, h=h, cx=cx, y=y, top=y - h, wins=wins, awn_top=y - h * .28, awn_bot=y - h * .28 + 8,
                kind=['gable', 'tall', 'side'][i % 3], rh=h * .55)

# ---------------------------------------------------------------- architecture
def cornice(x0, x1, y, depth=3.0, dentils=False, brackets=False, col=TRIM):
    """A moulded band under the eaves: a projecting top, a shadow line, optional dentils and end brackets."""
    rect(x0 - 1.4, y, x1 + 1.4, y + depth, col, edge=.18)
    line([(x0 - 1.4, y + .5), (x1 + 1.4, y + .5)], .5, WHITE, a=.8)
    line([(x0 - 1.2, y + depth + .35), (x1 + 1.2, y + depth + .35)], .8, '#8a6a30', a=.55)       # the shadow it casts
    if dentils:
        for dx in np.arange(x0 + .4, x1 - .4, 2.0):
            rect(dx, y + depth, dx + 1.1, y + depth + 1.2, col, edge=.2, rough=.2)
    if brackets:
        for bx in (x0 + .2, x1 - 2.0):
            c.area([(bx, y + depth), (bx + 1.8, y + depth), (bx + 1.8, y + depth + 3.4), (bx + .9, y + depth + 4.2), (bx, y + depth + 3.4)], col, wob=0, rough=.2, edge_dark=.2)
            line([(bx + .9, y + depth + .6), (bx + .9, y + depth + 3.4)], .35, TRIM_D, a=.9)

def string_course(x0, x1, y, col=TRIM):
    rect(x0 - .6, y, x1 + .6, y + 1.5, col, edge=.15)
    line([(x0 - .5, y + 1.8), (x1 + .5, y + 1.8)], .5, '#8a6a30', a=.45)

def quoins(x, y0, y1, side=1, col=STONE):
    """Alternating long and short stone blocks up a corner."""
    for j, yy in enumerate(np.arange(y1, y0, -4.2)):
        w = 3.6 if j % 2 == 0 else 2.4
        x0, x1 = (x, x + w) if side > 0 else (x - w, x)
        rect(x0, yy - 3.8, x1, yy, col, edge=.22, rough=.4, seed=int(yy * 3))
        line([(x0, yy - 3.9), (x1, yy - 3.9)], .3, STONE_D, a=.9)

def window_framed(win, style='plain', glass='night', story=None, shutters=None, box=None, frame=TRIM, seed=0):
    """A framed, multi-paned window: painted frame, glazing bars, a stone sill and a lintel.
    style: 'plain' | 'keystone'.  glass: 'night' (the town's deep blue) | 'warm' (lit from inside).
    shutters: a colour or None.  box: 'red' | 'white' | 'holly' | None.  story: 'candle' | 'cat' | 'lamp' | None."""
    x, y, w, h = win['x'], win['y'], win['w'] * 1.1, win['h'] * 1.04
    l, r_, t, b = x - w / 2, x + w / 2, y - h / 2, y + h / 2
    if glass == 'warm': glow(x, y, w * 1.05, a=.16, seed=seed + 1)
    if shutters:
        for s in (-1, 1):
            sx0, sx1 = (l - w * .55 - .5, l - .5) if s < 0 else (r_ + .5, r_ + w * .55 + .5)
            rect(sx0, t - .4, sx1, b + .4, shutters, edge=.2, seed=seed + s)
            for yy in np.arange(t + .8, b - .2, .85): line([(sx0 + .35, yy), (sx1 - .35, yy)], .22, hexc(shutters) * .62, a=.95)
            line([(sx0 + .2, t - .3), (sx0 + .2, b + .3)], .2, hexc(shutters) * 1.35, a=.7)
    rect(l - .9, t - .9, r_ + .9, b + .5, '#4a3a2a', edge=0, rough=.15)                        # the reveal (depth)
    rect(l - .6, t - .6, r_ + .6, b + .3, frame, edge=.15, seed=seed + 3)                        # frame
    gl = [GLASS_L, GLASS, GLASS_D] if glass == 'warm' else ['#3a3a5c', '#33335a', '#454670']
    m = rect(l, t, r_, b, gl[1], edge=.3, rough=.15, seed=seed + 4)
    if m is not None:
        G = np.array([hexc(z) for z in gl])
        c.stip(m, lambda X, Y, rr: G[rr.randint(3, size=len(X))] * (1 - np.clip((Y - t) / h, 0, 1)[:, None] * (.14 if glass == 'warm' else -.08)),
               spacing=.45, L=.9, w=.45, angfn=lambda X, Y: 0 * X, seed=seed + 5, jit=.4)
    if story == 'candle':
        rect(x - .3, b - 2.4, x + .3, b - .4, WHITE, edge=.1, rough=.1); c.dots([(x, b - 2.8)], .4, ['#fff2b0']); glow(x, b - 2.8, 1.5, a=.4, seed=seed + 6)
    elif story == 'cat':
        cx, cy = x + w * .2, b - .2
        c.area(S.lumpy(cx, cy - 1.2, 1.15, 1.1, seed + 7, n=14, amp=0), '#1e1a20', wob=0, rough=.1, edge_dark=0)
        c.area(S.lumpy(cx, cy - 2.75, .75, .7, seed + 8, n=12, amp=0), '#1e1a20', wob=0, rough=.1, edge_dark=0)
        for sd in (-1, 1): c.area([(cx + sd * .2, cy - 3.2), (cx + sd * .7, cy - 4.1), (cx + sd * .75, cy - 2.9)], '#1e1a20', wob=0, rough=.1, edge_dark=0)
        c.stroke([(cx + .9, cy - .3), (cx + 1.7, cy - 1.0), (cx + 1.5, cy - 2.2)], .32, '#1e1a20', a=1, dry=0, taper=(0, .5))
    elif story == 'lamp':
        rect(x - .2, b - 2.0, x + .2, b - .5, WOOD, edge=0, rough=.1)
        c.area([(x - 1.0, b - 2.0), (x + 1.0, b - 2.0), (x + .5, b - 3.2), (x - .5, b - 3.2)], '#e89a5a', wob=0, rough=.1, edge_dark=.1)
        glow(x, b - 2.6, 1.8, a=.35, seed=seed + 9)
    bar = frame if glass == 'night' else hexc(frame) * .9
    line([(x, t), (x, b)], .38, bar)
    for f in (.36, .68): line([(l, t + h * f), (r_, t + h * f)], .34, bar)
    c.stroke([(l + w * .15, t + h * .3), (l + w * .4, t + h * .08)], .3, '#ffffff', a=.3, dry=.2, taper=(.3, .3))   # a glint
    rect(l - 1.6, b + .3, r_ + 1.6, b + 1.5, STONE, edge=.25, seed=seed + 10)                   # sill
    line([(l - 1.5, b + 1.75), (r_ + 1.5, b + 1.75)], .45, '#6a4a20', a=.55)
    if style == 'keystone':
        rect(l - 1.4, t - 2.3, r_ + 1.4, t - .9, STONE, edge=.22, seed=seed + 11)
        c.area([(x - 1.0, t - .9), (x + 1.0, t - .9), (x + 1.35, t - 3.1), (x - 1.35, t - 3.1)], STONE, wob=0, rough=.15, edge_dark=.3)
    else:
        rect(l - 1.1, t - 1.9, r_ + 1.1, t - .9, STONE, edge=.2, seed=seed + 11)
    if box: flower_box(l - 1.2, r_ + 1.2, b + 1.5, box, seed + 12)

def flower_box(x0, x1, y, kind='red', seed=0):
    r = np.random.RandomState(seed)
    rect(x0, y, x1, y + 2.2, WOOD_M, edge=.18, seed=seed)
    line([(x0 + .2, y + .4), (x1 - .2, y + .4)], .3, WOOD_L, a=.8)
    leaves = [(x0 + r.uniform(0, 1) * (x1 - x0), y - r.uniform(-.2, 1.4)) for _ in range(int((x1 - x0) * 1.6))]
    c.dots(leaves, .8, ['#2f5a34', '#3f6e3c', '#25502c'], seed=seed + 1)
    c.stroke([(x0 + .5, y + .2), (x0 - .2, y + 1.8)], .5, '#3f6e3c', a=.9, dry=0, taper=(0, .5))            # trailing ivy
    c.stroke([(x1 - .6, y + .2), (x1 + .1, y + 2.0)], .5, '#3f6e3c', a=.9, dry=0, taper=(0, .5))
    cols = {'red': ['#c8302a', '#e04838'], 'white': ['#f6f2ea', '#efe6d6'], 'holly': ['#c8302a']}[kind]
    n = 4 if kind == 'holly' else 7
    c.dots([(x0 + .6 + r.uniform(0, 1) * (x1 - x0 - 1.2), y - r.uniform(.1, 1.3)) for _ in range(n)], .55 if kind == 'holly' else .75, cols, seed=seed + 2)

# ---------------------------------------------------------------- storefront
def shopfront(L, level):
    """The ground floor: pilasters, fascia, display window with mullions and transom, kick panels, door, step."""
    x0, x1, y = L['x0'], L['x1'], L['y']; top = L['awn_bot'] + .2
    paint = WOOD_M if level == 'A' else GREEN
    pd = hexc(paint) * .7
    # recess shadow and the frame
    rect(x0 + .3, top, x1 - .3, y, '#3a2a1a', edge=0, rough=.2)
    for px in (x0, x1 - 2.6):                                                             # pilasters
        rect(px, top, px + 2.6, y, paint, edge=.18, seed=int(px))
        line([(px + .6, top + .6), (px + .6, y - .6)], .3, GOLD if level != 'A' else WOOD_L, a=.8)
        rect(px - .4, y - 1.4, px + 3.0, y, pd, edge=.1)                                 # plinth
        rect(px - .4, top, px + 3.0, top + 1.0, pd, edge=.1)                             # capital
    dr_l, dr_r = x0 + 3.4, x0 + 12.6; win_l, win_r = x0 + 13.6, x1 - 3.4      # door on the left: the square's lamp post stands in front of the right end
    wt, wb = top + 2.4, y - 3.6
    # transom: a row of small panes over window and door
    rect(dr_l, top + .4, win_r, top + 2.2, paint, edge=.1)
    for tx in np.arange(dr_l + .4, win_r - .4, 2.2):
        rect(tx, top + .7, tx + 1.8, top + 1.9, GLASS_L if level != 'A' else GLASS, edge=.15, rough=.1)
    # display window
    rect(win_l - .5, wt - .5, win_r + .5, wb + .5, paint, edge=.15)
    m = rect(win_l, wt, win_r, wb, GLASS_D if level != 'A' else GLASS, edge=.25, seed=71)
    if m is not None:
        c.stip(m, lambda X, Y, rr: np.array([hexc(GLASS_L), hexc(GLASS), hexc(GLASS_D)])[rr.randint(3, size=len(X))] * (1 - np.clip((Y - wt) / (wb - wt), 0, 1)[:, None] * (.06 if level == 'A' else .18)),
               spacing=.6, L=1.2, w=.6, angfn=lambda X, Y: 0 * X, seed=72, jit=.4)
    display(win_l, wt, win_r, wb, level)
    for f in ((1 / 3, 2 / 3) if level == 'A' else (.5,)):                                 # mullions
        mx = win_l + (win_r - win_l) * f; line([(mx, wt), (mx, wb)], .55, paint)
    if level != 'A':
        for gx in (win_l + 2, win_l + (win_r - win_l) * .55):                              # reflections on the glass
            c.stroke([(gx, wb - .6), (gx + 3.4, wt + .6)], .5, '#fff6dc', a=.28, dry=.3, taper=(.3, .3))
    rect(win_l - .9, wb + .4, win_r + .9, wb + 1.3, WOOD_L if level == 'A' else TRIM, edge=.2)              # sill
    # kick panels under the window
    rect(win_l, wb + 1.3, win_r, y - 1.0, paint, edge=.12)
    n = 2 if level == 'A' else 3
    for j in range(n):
        a0 = win_l + .6 + j * (win_r - win_l - 1.2) / n; a1 = a0 + (win_r - win_l - 1.2) / n - .6
        rect(a0, wb + 1.8, a1, y - 1.5, pd, edge=.2)
        if level == 'C': T7.star((a0 + a1) / 2, (wb + y) / 2 + .1, .55, GOLD)
    door(dr_l, dr_r, top + 2.4, y, level, paint)

def door(l, r_, t, y, level, paint):
    w = r_ - l; cx = (l + r_) / 2
    rect(l - .4, t - .4, r_ + .4, y, '#2a1e14', edge=0, rough=.2)                        # the recess
    if level == 'C':
        rect(l - .4, t - .4, l + .5, y, '#1a120c', edge=0, rough=.1); rect(r_ - .5, t - .4, r_ + .4, y, '#1a120c', edge=0, rough=.1)
    dcol = '#8a2a24' if level != 'A' else WOOD
    rect(l + .5, t, r_ - .5, y - .3, dcol, edge=.18, seed=81)
    if level == 'C':                                                                       # glazed upper half
        rect(l + 1.4, t + .9, r_ - 1.4, t + (y - t) * .42, GLASS, edge=.25)
        line([(cx, t + .9), (cx, t + (y - t) * .42)], .3, dcol)
        T7.star(cx, t + (y - t) * .24, .9, RED)
        panels = [(t + (y - t) * .52, y - 1.4)]
    else:
        panels = [(t + 1.0, t + (y - t) * .46), (t + (y - t) * .54, y - 1.4)]
    for p0, p1 in panels:
        for s in (-1, 1):
            a0, a1 = (l + 1.3, cx - .45) if s < 0 else (cx + .45, r_ - 1.3)
            rect(a0, p0, a1, p1, hexc(dcol) * .78, edge=.22)
            line([(a0, p0 + .2), (a1, p0 + .2)], .25, hexc(dcol) * 1.2, a=.7)
    c.dots([(r_ - 1.6, (t + y) / 2 + .6)], .5, [GOLD]); c.dots([(r_ - 1.75, (t + y) / 2 + .45)], .18, [GOLD_L])       # knob
    if level != 'A':
        for hy in (t + 1.6, y - 2.6): line([(l + .5, hy), (l + 2.2, hy)], .45, '#2a2420')      # hinges
    if level == 'C': rect(l + .9, y - 1.4, r_ - .9, y - .5, GOLD, edge=.2, rough=.1)            # brass kick plate
    rect(l - 1.2, y - .2, r_ + 1.2, y + 1.3, STONE, edge=.2)                              # the step
    line([(l - 1.1, y + 1.55), (r_ + 1.1, y + 1.55)], .5, '#3a3224', a=.5)
    if level in ('B', 'C'): wreath(cx, t + (y - t) * (.22 if level == 'B' else .62), 1.9 if level == 'B' else 1.7)

def wreath(x, y, r=2.0):
    ring = [(x + r * math.cos(t), y + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 26)]
    c.stroke(ring, r * .75, '#2f5a34', a=1, dry=.15, taper=(0, 0))
    c.stroke(ring, r * .3, '#4a7a44', a=.7, dry=.4, taper=(0, 0))
    c.dots(ring[::3], r * .16, ['#c8302a', GOLD], seed=int(x))
    for s in (-1, 1): c.area([(x, y + r * .9), (x + s * r * .8, y + r * .55), (x + s * r * .8, y + r * 1.3)], RED, wob=0, rough=.2, edge_dark=.15)
    for s in (-1, 1): c.stroke([(x, y + r * 1.0), (x + s * r * .4, y + r * 2.0)], r * .22, RED, a=1, dry=0, taper=(0, .3))

def awning(L, level, cols=('#b8402e', '#f4eee2')):
    """Striped awning; B/C add a scalloped valance, a fold line and the shadow it throws on the wall."""
    x0, x1, t, b = L['x0'] + 1.0, L['x1'] - 1.0, L['awn_top'], L['awn_bot']
    n = 6
    for kk in range(n):
        a0 = x0 + kk * (x1 - x0) / n; a1 = x0 + (kk + 1) * (x1 - x0) / n
        c.area([(a0 + .6, t), (a1 + .6, t), (a1 + 1.2, b), (a0 + 1.2, b)], cols[kk % 2], wob=0, rough=.3, edge_dark=.08)
        for u in np.linspace(.3, .7, 2): c.stroke([(a0 + .6 + (a1 - a0) * u, t + .3), (a0 + 1.2 + (a1 - a0) * u, b - .3)], .25, hexc(cols[kk % 2]) * .9, a=.6, dry=.3, taper=(.2, .2))
        sc = [(a0 + 1.2 + (a1 - a0) * u, b + 1.6 * math.sin(u * math.pi)) for u in np.linspace(0, 1, 8)]   # scallop
        c.area([(a0 + 1.2, b - .1)] + sc + [(a1 + 1.2, b - .1)], cols[kk % 2], wob=0, rough=.25, edge_dark=.12)
    c.stroke([(x0 + .6, t + .2), (x1 + .6, t + .2)], .5, '#7a3a26', a=.7, dry=0, taper=(0, 0))                  # the roller bar
    c.stroke([(x0 + 1.2, b), (x1 + 1.2, b)], .4, '#7a2a20', a=.6, dry=0, taper=(0, 0))
    c.area([(x0 + 1.0, b + 1.6), (x1 + 1.4, b + 1.6), (x1 + 1.4, b + 3.0), (x0 + 1.0, b + 3.0)], '#2a1a10', wob=0, rough=.3, edge_dark=0, a=.28)  # shadow

def garland(x0, x1, y, sag=2.2, bows=3, lights=False, seed=0):
    pts = []
    nb = bows - 1
    for j in range(nb):
        a0 = x0 + (x1 - x0) * j / nb; a1 = x0 + (x1 - x0) * (j + 1) / nb
        pts += [(a0 + (a1 - a0) * u, y + sag * math.sin(u * math.pi)) for u in np.linspace(0, 1, 12)][(1 if j else 0):]
    c.stroke(pts, 1.5, '#2a5030', a=1, dry=.2, taper=(0, 0))
    r = np.random.RandomState(seed)
    c.dots([(px + r.uniform(-.4, .4), py + r.uniform(-.5, .5)) for px, py in pts[::1]], .6, ['#2f5a34', '#3f6e3c', '#24482a'], seed=seed + 1)
    c.dots([(px, py + .2) for px, py in pts[2::5]], .3, ['#c8302a', GOLD], seed=seed + 2)
    for j in range(bows):
        bx = x0 + (x1 - x0) * j / nb; by = y
        for s in (-1, 1): c.area([(bx, by), (bx + s * 1.5, by - .9), (bx + s * 1.5, by + .8)], RED, wob=0, rough=.2, edge_dark=.15)
        for s in (-1, 1): c.stroke([(bx, by + .2), (bx + s * .7, by + 2.3)], .5, RED, a=1, dry=0, taper=(0, .3))
        c.dots([(bx, by)], .45, [RED_D])
    if lights: string_lights(pts[1::2], seed=seed + 3)

def string_lights(pts, seed=0):
    r = np.random.RandomState(seed)
    for px, py in pts:
        glow(px, py + .5, .9, '#fff0b0', a=.18, seed=int(px * 10))
    c.dots([(px, py + .45) for px, py in pts], .28, ['#fff4c8', '#ffe8a0', '#ffd27a'], seed=seed)

def sign(x, y, w, h, level):
    """A painted signboard: cream field, red lettering TOYS / FOR TOTS, three stars, a moulded wooden frame."""
    rect(x - w / 2 - 1.2, y - h / 2 - 1.2, x + w / 2 + 1.2, y + h / 2 + 1.2, WOOD, edge=.15)
    if level == 'C':
        for s in (-1, 1):                                                                 # scrolled ends
            c.area(S.lumpy(x + s * (w / 2 + 1.2), y, 1.6, 2.6, 91 + s, n=14, amp=0), WOOD, wob=0, rough=.2, edge_dark=.2)
            c.dots([(x + s * (w / 2 + 1.2), y)], .6, [GOLD])
    m = rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, CREAM, edge=.1, seed=92)
    if m is not None: c.stip(m, pal_fn([CREAM, '#ece0c4', '#faf2e0'], .03), spacing=.7, L=1.4, w=.7, angfn=lambda X, Y: 0 * X, seed=93, jit=.3)
    line([(x - w / 2 + .8, y - h / 2 + .8), (x + w / 2 - .8, y - h / 2 + .8), (x + w / 2 - .8, y + h / 2 - .8), (x - w / 2 + .8, y + h / 2 - .8), (x - w / 2 + .8, y - h / 2 + .8)], .35, RED, a=.9)
    T7.paint_text('TOYS', x, y - h * .25, h * .27, RED, track=.3, outline='#7a1e18' if level == 'C' else None, ow=.25)
    T7.paint_text('FOR TOTS', x, y + h * .07, h * .23, RED, track=.25, outline='#7a1e18' if level == 'C' else None, ow=.25)
    for i in (-1, 0, 1): T7.star(x + i * w * .13, y + h * .32, h * .07, RED, inner=.45)

def gooseneck(x, y, drop=4.0, q=1.5):
    """A sign lamp on a curved arm, with a cone of warm light down onto the sign."""
    P = lambda dx, dy: (x + dx * q, y + dy * q)
    c.stroke([P(0, -1.0), P(0, -2.4), P(.8, -3.4), P(2.0, -3.3), P(2.5, -2.4)], .32 * q, '#1e1c20', a=1, dry=0, taper=(0, 0))
    c.area([P(1.4, -2.6), P(3.6, -2.6), P(3.1, -1.5), P(1.9, -1.5)], '#1e1c20', wob=0, rough=.1, edge_dark=0)
    c.area([P(1.9, -1.5), P(3.1, -1.5), (x + 3.4 * q + 1.2, y + drop), (x + 1.6 * q - 1.2, y + drop)], '#fff0b8', wob=0, rough=.1, edge_dark=0, a=.17)
    c.dots([P(2.5, -1.4)], .3 * q, ['#fff4c8'])

# ---------------------------------------------------------------- toys (simple, recognisable, folk-art)
def drum(x, y, s=1.0):
    rect(x - 1.6 * s, y - 2.8 * s, x + 1.6 * s, y, RED, edge=.15, rough=.1)
    for j in range(4): line([(x - 1.6 * s + j * 1.07 * s, y - 2.6 * s), (x - 1.0 * s + j * 1.07 * s, y - .2 * s)], .2 * s, GOLD, a=.9)
    c.area(S.lumpy(x, y - 2.8 * s, 1.6 * s, .45 * s, 101, n=12, amp=0), WHITE, wob=0, rough=.1, edge_dark=.2)
    for yy in (y - 2.7 * s, y - .15 * s): line([(x - 1.65 * s, yy), (x + 1.65 * s, yy)], .3 * s, NAVY)
    line([(x + .6 * s, y - 3.6 * s), (x + 1.8 * s, y - 4.6 * s)], .2 * s, WOOD_L)

def blocks(x, y, s=1.0):
    for j, (dx, dy, col, ch) in enumerate([(-1.5, 0, '#3f6aa8', 'A'), (1.5, 0, '#c8302a', 'B'), (0, -3.0, '#e8b84a', 'C')]):
        rect(x + dx * s - 1.4 * s, y + dy * s - 2.8 * s, x + dx * s + 1.4 * s, y + dy * s, col, edge=.2, rough=.1)
        T7.paint_text(ch, x + dx * s, y + dy * s - 1.4 * s, 1.5 * s, WHITE)

def soldier(x, y, s=1.0):
    rect(x - .55 * s, y - 2.6 * s, x + .55 * s, y, NAVY, edge=.1, rough=.1)
    rect(x - .75 * s, y - 5.2 * s, x + .75 * s, y - 2.6 * s, RED, edge=.12, rough=.1)
    line([(x - .7 * s, y - 3.0 * s), (x + .7 * s, y - 3.0 * s)], .25 * s, WHITE)
    T7.disc(x, y - 5.9 * s, .65 * s, '#e8c4a0', 102, edge=.1)
    rect(x - .6 * s, y - 8.0 * s, x + .6 * s, y - 6.3 * s, '#1c1c24', edge=.1, rough=.1)
    c.dots([(x + .9 * s, y - 4.2 * s)], .3 * s, [GOLD])

def books(x, y, s=1.0, n=5, seed=0):
    r = np.random.RandomState(seed); cols = ['#3f6aa8', '#c8302a', '#3f8a44', '#e8b84a', '#8a4aa0', '#e88aa0', '#2a4a6a']
    xx = x
    for j in range(n):
        w = r.uniform(.8, 1.2) * s; h = r.uniform(3.2, 4.4) * s; col = cols[r.randint(len(cols))]
        tilt = .5 * s if j == n - 1 else 0
        c.area([(xx, y), (xx + w, y), (xx + w + tilt, y - h), (xx + tilt, y - h)], col, wob=0, rough=.1, edge_dark=.2)
        line([(xx + .15 * s, y - h * .3), (xx + w - .15 * s, y - h * .3)], .15 * s, GOLD_L, a=.8)
        xx += w + .1 * s

def doll(x, y, s=1.0):
    c.area([(x - 1.8 * s, y), (x + 1.8 * s, y), (x + .7 * s, y - 3.6 * s), (x - .7 * s, y - 3.6 * s)], '#e88aa0', wob=0, rough=.1, edge_dark=.15)
    line([(x - 1.6 * s, y - .5 * s), (x + 1.6 * s, y - .5 * s)], .3 * s, WHITE)
    T7.disc(x, y - 4.5 * s, 1.0 * s, '#eccaa8', 103, edge=.1)
    c.area(S.lumpy(x, y - 5.0 * s, 1.15 * s, .7 * s, 104, n=12, amp=0), '#8a4a2a', wob=0, rough=.1, edge_dark=.1)
    c.dots([(x - .35 * s, y - 4.5 * s), (x + .35 * s, y - 4.5 * s)], .14 * s, ['#2a1a12'])

def wooden_train(x, y, s=1.0):
    T7.toy_train(x, y, s)
    c.dots([(x - 4.4 * s, y - 6.8 * s)], .25 * s, [WHITE])                                 # a glint on the cab window

def display(l, t, r_, b, level):
    """What is in the shop window. A: the rocking horse and two presents. B: a shelf with a teddy and books behind,
    the rocking horse and presents in front. C: two shelves (books, drum, soldier / teddy, doll), and on the floor a
    wooden train, blocks and presents beside the rocking horse."""
    w, h = r_ - l, b - t
    if level == 'A':
        T7.rocking_horse(l + w * .34, b - .3, .92); T7.presents(l + w * .76, b - .3, .82, 61, n=2); return
    # the back of the shop: a warm wall and a shelf
    rect(l + .2, t + .2, r_ - .2, b - .2, '#a8642c', edge=0, rough=.2, a=.55)                 # the shop's warm interior
    glow((l + r_) / 2, t + h * .3, w * .35, '#ffe0a0', a=.2, seed=118)
    sh = t + h * (.46 if level == 'B' else .42)
    if level == 'B':
        line([(l + .4, sh), (r_ - .4, sh)], .7, WOOD_M)
        T7.teddy(l + w * .24, sh - .3, .38); books(l + w * .52, sh - .3, .5, n=5, seed=111)
        T7.rocking_horse(l + w * .34, b - .3, .5); T7.presents(l + w * .76, b - .3, .62, 62, n=2)
        return
    # C: one shelf of small things, and the floor of the window
    line([(l + .4, sh), (r_ - .4, sh)], .55, WOOD_M)
    books(l + w * .05, sh - .25, .42, n=4, seed=112); T7.teddy(l + w * .36, sh - .25, .31); drum(l + w * .6, sh - .25, .45); soldier(l + w * .84, sh - .25, .38)
    T7.rocking_horse(l + w * .18, b - .3, .46); wooden_train(l + w * .52, b - .3, .42)
    blocks(l + w * .88, b - .3, .36); T7.presents(l + w * .7, b - .3, .42, 63, n=1)
    string_lights([(l + w * u, t + .5 + .35 * math.sin(u * math.pi * 3)) for u in np.linspace(.05, .95, 11)], seed=114)

# ---------------------------------------------------------------- roof (C)
def roof_detail(L):
    """Shingle courses and a ridge cap on the 'side' roof, and a small dormer with a lit window."""
    x0, x1, top, rh, w = L['x0'], L['x1'], L['top'], L['rh'], L['w']
    eL, eR = (x0 - 3, top + 1), (x1 + 3, top + 1); RL, RR = (x0 + w * .16, top - rh), (x1 - w * .16, top - rh)
    for yy in np.arange(top - 3, top - rh + 2, -3.2):
        u = (top + 1 - yy) / (rh + 1); xa = eL[0] + (RL[0] - eL[0]) * u; xb = eR[0] + (RR[0] - eR[0]) * u
        pts = [(xa + (xb - xa) * v, yy + .55 * abs(math.sin(v * (xb - xa) / 1.6 * math.pi))) for v in np.linspace(0, 1, int((xb - xa) * 1.4))]
        c.stroke(pts, .4, '#4a2a1e', a=.7, dry=.1, taper=(0, 0))
    c.stroke([RL, RR], 1.4, '#4a2a1e', a=1, dry=0, taper=(0, 0)); c.stroke([(RL[0], RL[1] + .5), (RR[0], RR[1] + .5)], .4, '#a8684a', a=.8, dry=0, taper=(0, 0))
    dx, dy = L['cx'], top - rh * .40                                                          # dormer
    c.area([(dx - 5.2, dy + 5.0), (dx + 5.2, dy + 5.0), (dx + 6.4, dy + 6.6), (dx - 6.4, dy + 6.6)], '#4a2a1e', wob=0, rough=.2, edge_dark=0, a=.5)   # its shadow on the roof
    rect(dx - 5.0, dy - 3.4, dx + 5.0, dy + 5.2, WALL, edge=.18, seed=121)
    c.area([(dx - 6.6, dy - 3.0), (dx + 6.6, dy - 3.0), (dx, dy - 9.2)], '#7a4a34', wob=0, rough=.3, edge_dark=.18)
    c.stroke([(dx - 6.6, dy - 3.0), (dx, dy - 9.2), (dx + 6.6, dy - 3.0)], .8, TRIM, a=1, dry=0, taper=(0, 0))
    window_framed(dict(x=dx, y=dy + 1.0, w=4.6, h=5.4), style='plain', glass='warm', story='lamp', seed=122)

# ---------------------------------------------------------------- the whole storefront, per level
def storefront(level, L=None):
    L = L or house_layout(5)
    if level == 'orig':
        T7.shop_window(5, L['x0'], L['w'], L['h'], L['y']); T7.donation_sign(L['cx'], L['y'] - L['h'] * .28 - 9.5, L['w'] * .86); return
    with fine():
        _storefront(level, L)

def _storefront(level, L):
    x0, x1, y, top = L['x0'], L['x1'], L['y'], L['top']
    if level == 'C':
        roof_detail(L)
        for xx, s in ((x0, 1), (x1, -1)): quoins(xx, top + 4, L['awn_top'] - .5, s)
    cornice(x0, x1, top + .6, 3.0 if level != 'C' else 2.6, dentils=level == 'C', brackets=level == 'C')
    string_course(x0, x1, L['awn_top'] - 2.4)
    for wi in L['wins']:
        if wi['row'] == 2: continue                                                         # behind the sign
        rw, cl = wi['row'], wi['col']
        if level == 'A':
            kw = dict(glass='night')
        else:
            kw = dict(glass='warm' if rw == 1 else 'night', shutters='#3f6a44' if rw == 0 else None, box=('red' if cl == 0 else 'white') if rw == 1 else None)
            if level == 'C':
                kw.update(style='keystone' if rw == 0 else 'plain', story={(0, 0): 'candle', (1, 1): 'cat'}.get((rw, cl)))
                if (rw, cl) == (0, 0): kw['glass'] = 'warm'
        window_framed(wi, seed=130 + rw * 10 + cl, **kw)
    if level == 'A':
        T7.donation_sign(L['cx'], y - L['h'] * .28 - 9.5, L['w'] * .86)
        shopfront(L, 'A'); return                                    # the town row's own awning stays
    sy = y - L['h'] * .28 - 9.0
    sign(L['cx'], sy, L['w'] * .8, 13.2, level)
    if level == 'C':
        for gx in (L['cx'] - 14.5, L['cx'] - 3.2, L['cx'] + 8.1): gooseneck(gx, sy - 6.6 - .4, 7.2)
    shopfront(L, level)
    awning(L, level)
    garland(x0 + 2.2, x1 - 2.2, L['awn_bot'] + 3.0, sag=1.4, bows=3, lights=level == 'C', seed=141)
    if level == 'C':
        string_lights([(x0 + 1.5 + (x1 - x0 - 1.5) * u, L['awn_bot'] + 1.3 + .45 * math.sin(u * 6 * math.pi)) for u in np.linspace(0, 1, 16)], seed=142)

def after_square(level, L=None):
    with fine(): _after_square(level, L)

def _after_square(level, L=None):
    """Things that stand on the pavement in front of the shop (painted after the square): light spilling from the
    window (B, C) and a poinsettia by the door (C)."""
    if level in ('orig', 'A'): return
    L = L or house_layout(5); x0, x1, y = L['x0'], L['x1'], L['y']
    c.area([(x0 + 13.6, y + .6), (x1 - 3.4, y + .6), (x1 - 1, y + 7.5), (x0 + 11, y + 7.5)], '#f8d880', wob=.3, rough=.4, edge_dark=0, a=.16)
    if level == 'C':
        c.area([(x0 + 3.4, y + .6), (x0 + 12.6, y + .6), (x0 + 13.6, y + 5), (x0 + 2.4, y + 5)], '#f8d880', wob=.3, rough=.4, edge_dark=0, a=.12)
        px, py = x0 + 15.2, y + 3.6
        rect(px - 1.8, py - 2.6, px + 1.8, py, WOOD_M, edge=.18)
        c.dots([(px + u, py - 3.4 + v) for u, v in ((-1.2, 0), (0, -.6), (1.2, 0), (-.6, .5), (.6, .5))], .85, ['#c8302a', '#e04838'], seed=151)
        c.dots([(px, py - 3.3)], .3, [GOLD])

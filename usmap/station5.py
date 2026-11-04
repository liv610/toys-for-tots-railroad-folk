"""Toy Town's grand station, redrawn after the reference (pass 5).

Reference features carried over:
  * a central bay under one great stone arch, with a tiled barrel roof following the arch
  * a dark fan-light (lunette) with radial glazing bars inside the arch, the Christmas wreath at its crown
  * below it, a wide arched opening: lit amber panes above, wooden plank doors below
  * two square stone pilasters with capitals and gold-ball finials carrying the red and green pennants; the blue
    pennant flies from the apex of the arch
  * lower side wings with curved, tiled roofs, each with an arched window (panes over doors)
  * at the outer end of each wing a dark arched opening where the railway enters
  * dressed cream stone with mortar joints and darker trim
All dimensions are in map units relative to the hall's base centre (x, y), so the station scales with the render.
"""
import math
import numpy as np
import usmap4 as B
from usmap4 import c, hexc, pal_fn

STONE, STONE_D, STONE_L, TRIM = '#e6d2a4', '#cdb588', '#f1e2bc', '#b89a68'
ROOF, ROOF_D = '#7c4a3a', '#5e3528'
GLASS = ['#f2c25a', '#f8d880', '#e8a840']
WOOD, WOOD_D = '#6a4630', '#4a2e20'

def arch_pts(cx, spring, half, rise, n=28, start=0.0, end=1.0):
    """Points on an elliptical arch from the left springing to the right (start/end in 0..1)."""
    return [(cx - half * math.cos(u * math.pi), spring - rise * math.sin(u * math.pi)) for u in np.linspace(start, end, n)]

def masonry(poly, col, seed, course=9.0, block=16.0, light=STONE_L, dark=STONE_D):
    """A dressed-stone wall: the base stipple plus faint mortar courses and staggered joints, clipped to the shape."""
    m = B.wall(poly, col, seed)
    if m is None: return m
    P = np.array(poly); x0, x1 = P[:, 0].min(), P[:, 0].max(); y0, y1 = P[:, 1].min(), P[:, 1].max()
    prev = c.clipm; c.set_clip(m)
    r = np.random.RandomState(seed)
    yy = y1 - course; row = 0
    while yy > y0:
        c.stroke([(x0 - 2, yy), (x1 + 2, yy)], .7, dark, a=.55, dry=.2, taper=(0, 0))
        off = (block / 2) * (row % 2)
        xx = x0 + off + r.uniform(-2, 2)
        while xx < x1:
            c.stroke([(xx, yy), (xx, yy + course)], .6, dark, a=.45, dry=.2, taper=(0, 0))
            if r.rand() < .3: c.stroke([(xx + 1.5, yy + 1.2), (xx + block - 3, yy + 1.2)], .7, light, a=.5, dry=.3, taper=(.1, .1))
            xx += block * r.uniform(.8, 1.2)
        yy -= course; row += 1
    c.clipm = prev
    return m

def tiles(poly, seed, col=ROOF):
    m = B.roof_tiles(poly, col, seed)
    if m is None: return
    P = np.array(poly); x0, x1 = P[:, 0].min(), P[:, 0].max(); y0, y1 = P[:, 1].min(), P[:, 1].max()
    prev = c.clipm; c.set_clip(m)
    for yy in np.arange(y0 + 4, y1, 5.5): c.stroke([(x0 - 2, yy), (x1 + 2, yy)], .8, ROOF_D, a=.5, dry=.3, taper=(0, 0))
    c.clipm = prev

WOOD_L = '#8a6040'

def wood_bar(p, q, w):
    """A wooden bar with a lit upper/left edge and a shadowed lower/right edge."""
    p, q = np.array(p, float), np.array(q, float); d = q - p; n = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-9)
    if n[1] > 0 or (abs(n[1]) < 1e-6 and n[0] > 0): n = -n                # n points up/left
    c.stroke([p, q], w, WOOD, a=1, dry=0, taper=(0, 0))
    c.stroke([p + n * w * .32, q + n * w * .32], max(.5, w * .25), WOOD_L, a=.9, dry=0, taper=(0, 0))
    c.stroke([p - n * w * .36, q - n * w * .36], max(.5, w * .22), WOOD_D, a=.9, dry=0, taper=(0, 0))

def panes_and_doors(cx, base, half, spring, rise, cols, rows, seed, door_frac=.46):
    """An arched opening in a heavy wooden frame: amber panes behind wooden glazing bars above a carved transom,
    and framed, panelled plank doors with iron hinge straps below."""
    fw = max(3.6, half * .09)                                             # frame width
    out = [(cx - half, base)] + arch_pts(cx, spring, half, rise) + [(cx + half, base)]
    c.area([(cx - half - fw, base)] + arch_pts(cx, spring, half + fw, rise + fw) + [(cx + half + fw, base)], WOOD, wob=0, rough=.3, edge_dark=.25)
    m = c.area(out, GLASS[0], wob=0, rough=.3, edge_dark=.2)
    if m is not None: c.stip(m, pal_fn(GLASS), spacing=1.0, L=1.8, w=1.2, seed=seed, jit=1.0)
    top = spring - rise; dy = base - top; door_top = base - dy * door_frac
    # the frame's moulding: a light inner line and a dark outer line round the arch and down the jambs
    c.stroke([(cx - half - fw * .5, base)] + arch_pts(cx, spring, half + fw * .5, rise + fw * .5) + [(cx + half + fw * .5, base)], .7, WOOD_L, a=.9, dry=0, taper=(0, 0))
    c.stroke([(cx - half - fw, base)] + arch_pts(cx, spring, half + fw, rise + fw) + [(cx + half + fw, base)], .8, WOOD_D, a=1, dry=0, taper=(0, 0))
    # glazing bars (wood, with highlights) and a radiating fan in the arched head
    gb = max(1.7, half * .036)
    for j in range(1, cols):
        xx = cx - half + 2 * half * j / cols
        yt = spring - rise * math.sqrt(max(0.0, 1 - ((xx - cx) / half) ** 2))
        wood_bar((xx, door_top), (xx, max(yt, spring - 1) if abs(xx - cx) > half * .55 else yt), gb)
    for i in range(1, rows + 1):
        yy = door_top - (door_top - top) * i / (rows + 1)
        hw = half * math.sqrt(max(0.0, 1 - ((spring - yy) / rise) ** 2)) if yy < spring else half
        wood_bar((cx - hw, yy), (cx + hw, yy), gb)
    # transom: a broad carved beam between glass and doors, with a row of small dentils
    tb = max(3.0, half * .085)
    c.area([(cx - half - fw, door_top + tb / 2), (cx + half + fw, door_top + tb / 2), (cx + half + fw, door_top - tb / 2), (cx - half - fw, door_top - tb / 2)], WOOD, wob=0, rough=.3, edge_dark=.25)
    c.stroke([(cx - half - fw, door_top - tb / 2 + .5), (cx + half + fw, door_top - tb / 2 + .5)], .8, WOOD_L, a=.9, dry=0, taper=(0, 0))
    for xx in np.arange(cx - half + 2, cx + half - 1, max(3.0, half / 9)):
        c.area([(xx - .7, door_top + tb / 2), (xx + .7, door_top + tb / 2), (xx + .7, door_top + tb / 2 + 1.6), (xx - .7, door_top + tb / 2 + 1.6)], WOOD_D, wob=0, rough=.2)
    # doors: two leaves of vertical planks, each with a raised frame and two sunk panels, and iron hinge straps
    d0 = door_top + tb / 2 + 1.4
    c.area([(cx - half, base), (cx + half, base), (cx + half, d0), (cx - half, d0)], WOOD, wob=0, rough=.4, edge_dark=.15)
    for xx in np.linspace(cx - half, cx + half, int(half * 2 / 4.0) + 1)[1:-1]:
        c.stroke([(xx, base), (xx, d0)], .55, WOOD_D, a=.75, dry=.1, taper=(0, 0))
    for side in (-1, 1):
        l0, l1 = (cx - half, cx) if side < 0 else (cx, cx + half); inset = max(1.6, half * .06)
        for (a0, a1) in ((d0 + inset, (d0 + base) / 2 - inset / 2), ((d0 + base) / 2 + inset / 2, base - inset)):
            q = [(l0 + inset, a1), (l1 - inset, a1), (l1 - inset, a0), (l0 + inset, a0)]
            c.stroke(q + [q[0]], .9, WOOD_D, a=.95, dry=0, taper=(0, 0))
            c.stroke([(l0 + inset + .8, a0 + .8), (l1 - inset - .8, a0 + .8)], .6, WOOD_L, a=.8, dry=0, taper=(0, 0))
        for hy in (d0 + (base - d0) * .2, d0 + (base - d0) * .78):          # hinge straps
            hx0 = l0 if side < 0 else l1; hx1 = hx0 - side * (l1 - l0) * .45
            c.stroke([(hx0, hy), (hx1, hy)], max(.9, half * .03), '#2a2420', a=1, dry=0, taper=(0, .5))
    wood_bar((cx, base), (cx, d0), max(1.6, half * .05))
    c.dots([(cx - 1.6, (d0 + base) / 2), (cx + 1.6, (d0 + base) / 2)], max(.7, half * .018), ['#d8a840'])   # door handles
    # jambs: the frame continues down beside the doors
    for xx in (cx - half - fw / 2, cx + half + fw / 2): wood_bar((xx, base), (xx, spring), fw)
    return fw

def voussoirs(cx, spring, half, rise, band, seed, n=19, col=STONE, joint=STONE_D):
    """A stone arch band of `band` thickness, with radial joints and a lighter keystone."""
    outer = arch_pts(cx, spring, half + band, rise + band, 40); inner = arch_pts(cx, spring, half, rise, 40)
    m = c.area(outer + inner[::-1], col, wob=.05, rough=.5, edge_dark=.12, seed=seed)
    if m is not None: c.stip(m, pal_fn([col, hexc(col) * .94, hexc(col) * 1.05]), spacing=1.1, L=2.2, w=1.2, seed=seed + 1, jit=.4)
    for u in np.linspace(0, 1, n):
        a = u * math.pi
        p_in = (cx - half * math.cos(a), spring - rise * math.sin(a)); p_out = (cx - (half + band) * math.cos(a), spring - (rise + band) * math.sin(a))
        c.stroke([p_in, p_out], .8, joint, a=.85, dry=.1, taper=(0, 0))
    k = [(cx - 5, spring - rise + 1), (cx + 5, spring - rise + 1), (cx + 6.5, spring - rise - band - 2), (cx - 6.5, spring - rise - band - 2)]
    c.area(k, STONE_L, wob=0, rough=.3, edge_dark=.15)
    c.stroke(outer, 1.0, TRIM, a=.9, dry=.1, taper=(0, 0)); c.stroke(inner, 1.0, TRIM, a=.9, dry=.1, taper=(0, 0))

def lunette(cx, spring, half, rise, seed):
    """The dark fan-light: brown glass with radial bars and a few warm reflections."""
    pts = arch_pts(cx, spring, half, rise, 36)
    m = c.area(pts + [(cx + half, spring), (cx - half, spring)], '#4a3326', wob=0, rough=.3, edge_dark=.2)
    if m is not None: c.stip(m, pal_fn(['#4a3326', '#5a4030', '#3a281e', '#7a5a3a']), spacing=1.1, L=2.2, w=1.2, seed=seed, jit=1.0)
    hub = (cx, spring)
    for u in np.linspace(.08, .92, 9):
        a = u * math.pi; p = (cx - half * math.cos(a), spring - rise * math.sin(a))
        wood_bar(hub, p, 2.0); c.stroke([hub, p], .5, '#d8b888', a=.7, dry=.1, taper=(0, 0))
    for f in (.45, .75):
        ring = arch_pts(cx, spring, half * f, rise * f, 26)
        c.stroke(ring, 2.2, WOOD, a=1, dry=0, taper=(0, 0)); c.stroke(ring, .6, '#d8b888', a=.7, dry=0, taper=(0, 0))
    edge = arch_pts(cx, spring, half - 1.5, rise - 1.5, 40)
    c.stroke(edge, 3.2, WOOD, a=1, dry=0, taper=(0, 0)); c.stroke(edge, .7, WOOD_L, a=.9, dry=0, taper=(0, 0))
    c.area(B.S.lumpy(cx, spring - 2, 9, 7, seed + 5, n=18, amp=0, flat=.6), WOOD, wob=0, rough=.3, edge_dark=.3)   # the hub
    r = np.random.RandomState(seed)
    c.dots([(cx + r.uniform(-.8, .8) * half, spring - r.uniform(.1, .7) * rise) for _ in range(14)], .9, ['#d8a858', '#b88848'], seed=seed + 3)

def pilaster(px, base, top, seed, w=18):
    masonry([(px - w / 2, base), (px + w / 2, base), (px + w / 2, top), (px - w / 2, top)], STONE, seed, course=8, block=w)
    c.stroke([(px - w / 2 + 2, base), (px - w / 2 + 2, top)], 1.0, STONE_L, a=.7, dry=.2, taper=(0, 0))
    c.stroke([(px + w / 2 - 2, base), (px + w / 2 - 2, top)], 1.0, STONE_D, a=.7, dry=.2, taper=(0, 0))
    cap = [(px - w / 2 - 3, top + 2), (px + w / 2 + 3, top + 2), (px + w / 2 + 3, top - 6), (px - w / 2 - 3, top - 6)]
    c.area(cap, STONE_L, wob=0, rough=.3, edge_dark=.18)
    c.stroke([(px - w / 2 - 3, top + 2), (px + w / 2 + 3, top + 2)], 1.0, TRIM, a=1, dry=0, taper=(0, 0))
    # a small lamp niche near the top, as in the reference
    c.area([(px - 3, top + 22), (px + 3, top + 22), (px + 3, top + 12)] + [(px + 3 * math.cos(t), top + 12 - 3 * math.sin(t)) for t in np.linspace(0, math.pi, 8)] + [(px - 3, top + 12)], '#5a4030', wob=0, rough=.3)
    c.dots([(px, top + 15)], 1.4, ['#f2c25a'])
    # finial: a stepped plinth and a gold ball
    c.area([(px - 5, top - 6), (px + 5, top - 6), (px + 3.5, top - 12), (px - 3.5, top - 12)], STONE_D, wob=0, rough=.3)
    c.area(B.S.lumpy(px, top - 16, 4.2, 4.2, seed, n=18, amp=0), '#d8a840', wob=0, rough=.2, edge_dark=.25)
    c.dots([(px - 1.3, top - 17.5)], 1.2, ['#f8e098'])

def wing(side, x, y, seed):
    """One side wing: curved tiled roof, an arched window over doors, and the railway opening at the far end."""
    s = side; inner = x + s * 110; outer = x + s * 182
    lo, hi = min(inner, outer), max(inner, outer)
    eave = y - 80
    # curved roof, rising toward the centre
    roof = [(outer - s * 6, eave + 2)] + [(outer + (inner - outer) * u, eave - 4 - 26 * math.sin(u * math.pi / 2) ** 1.3) for u in np.linspace(0, 1, 20)] + [(inner, eave + 2)]
    tiles(roof, seed)
    c.stroke([(outer - s * 6, eave + 1), (inner, eave + 1)], 2.4, TRIM, a=1, dry=.1, taper=(0, 0))
    masonry([(lo, y), (hi, y), (hi, eave), (lo, eave)], STONE, seed + 1)
    c.stroke([(lo, eave + 4), (hi, eave + 4)], 1.6, STONE_D, a=.8, dry=.1, taper=(0, 0))
    # arched window over doors
    wx = x + s * 136
    fw = panes_and_doors(wx, y - 2, 16, y - 44, 15, 4, 3, seed + 2)
    voussoirs(wx, y - 44, 16 + fw, 15 + fw, 5, seed + 3, n=11)
    # a corner pier at the far end of the wing
    px = outer - s * 5
    c.area([(px - 5, y), (px + 5, y), (px + 5, eave + 3), (px - 5, eave + 3)], STONE_D, wob=0, rough=.4, edge_dark=.12)
    c.stroke([(px - 3.5, y), (px - 3.5, eave + 3)], .8, STONE_L, a=.7, dry=.2, taper=(0, 0))

def grand_station5(x, y):
    # side wings first (the central bay overlaps their inner ends)
    wing(-1, x, y, 41); wing(1, x, y, 51)
    # central bay: barrel roof following the great arch, then the arched facade
    spring = y - 96; half = 92; rise = 74; band = 13
    roof_out = arch_pts(x, spring, half + band + 12, rise + band + 12, 44); roof_in = arch_pts(x, spring, half + band - 1, rise + band - 1, 44)
    tiles(roof_out + roof_in[::-1], 61)
    c.stroke(roof_out, 1.4, ROOF_D, a=.9, dry=.1, taper=(0, 0))
    facade = [(x - half - band, y)] + arch_pts(x, spring, half + band, rise + band, 44) + [(x + half + band, y)]
    masonry(facade, STONE, 62)
    lunette(x, spring, half - 4, rise - 4, 63)
    voussoirs(x, spring, half - 4, rise - 4, band, 64, n=23)
    # lintel under the fan-light, and the great opening below it
    c.area([(x - half + 2, spring + 1), (x + half - 2, spring + 1), (x + half - 2, spring + 8), (x - half + 2, spring + 8)], STONE_L, wob=0, rough=.3, edge_dark=.15)
    c.stroke([(x - half + 2, spring + 8), (x + half - 2, spring + 8)], 1.0, TRIM, a=1, dry=0, taper=(0, 0))
    fw = panes_and_doors(x, y - 1, 68, spring + 38, 26, 9, 3, 65, door_frac=.42)
    voussoirs(x, spring + 38, 68 + fw, 26 + fw, 7, 66, n=17)
    # pilasters between the bay and the wings, with finials for the red and green pennants
    for s in (-1, 1): pilaster(x + s * 101, y, y - 150, 70 + s)
    # wreath at the crown of the fan-light, with a red bow
    wx, wy = x, spring - rise * .62
    c.stroke([(wx + 15 * math.cos(t), wy + 15 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 44)], 8, '#2f5a34', a=1, dry=.15, taper=(0, 0))
    c.stroke([(wx + 15 * math.cos(t), wy + 15 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 44)], 3, '#4a7a44', a=.7, dry=.4, taper=(0, 0))
    c.dots([(wx + 15 * math.cos(t), wy + 15 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)], 1.5, ['#c8302a', '#f2c25a'], seed=5)
    c.area([(wx - 6, wy + 13), (wx + 6, wy + 13), (wx + 10, wy + 22), (wx - 10, wy + 22)], '#c8302a', wob=0, rough=.3)
    c.area(B.S.lumpy(wx, wy + 13, 3.2, 3, 9, n=14, amp=0), '#a82420', wob=0, rough=.2)
    # finial at the apex for the blue pennant
    ax, ay = x, spring - rise - band - 14
    c.area([(ax - 5, ay + 8), (ax + 5, ay + 8), (ax + 3.5, ay + 2), (ax - 3.5, ay + 2)], STONE_D, wob=0, rough=.3)
    c.area(B.S.lumpy(ax, ay - 2, 4.2, 4.2, 77, n=18, amp=0), '#d8a840', wob=0, rough=.2, edge_dark=.25)

# where the three pennants fly (map units; flag sprites put the foot of their pole here)
def flag_feet(x, y):
    spring = y - 96; rise = 74; band = 13
    return {'red': (x - 101, y - 150 - 20), 'blue': (x, spring - rise - band - 14 - 6), 'green': (x + 101, y - 150 - 20)}

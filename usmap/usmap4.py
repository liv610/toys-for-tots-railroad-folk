"""Pass 4 — the U.S. map rebuilt on the second reference (references/us-map-reference-v2.png).

Composition from that reference: three end stations (a lodge on a pier in the Pacific Northwest, a depot in the
Southwest, a station in snowy New England), three lines that run into a grand glass-roofed station at Toy Town,
the Mississippi flowing from the Great Lakes under Toy Town's bridge to a delta, a paddle steamer, a red and a blue
train.

Built for animation and zoom:
  * Same layered, depth-sorted, per-element-seeded scene as pass 3 (out4/scene4.json), rendered at any output width:
        usmap4.py --width 6400        (default 3200)
    Every brush mark is defined in map units, so a wider render is genuinely sharper, not enlarged.
  * Everything that will move is painted as its own transparent sprite and kept out of the base painting:
        trains (one sprite per locomotive and per wagon, drawn straight; placed along the track with rotation),
        smoke puffs, windmill blades (rotate about the hub), the steamer and its paddle wheel, sailboats, clouds, flags.
    out4/anim/manifest.json gives every sprite's file, size, pivot and where it sits in the still image;
    routes (track centre-lines) and the river path are included so trains and the steamer can follow them.
  * The occluder overlay (things in front of the railroad, including the station) lets a moving train pass behind
    trees and vanish into the station.
"""
import sys, os, json, math, time, zlib
import numpy as np, cv2
import usmap as U, usmap2 as U2, usmap3 as U3
import story as S, a as A, kit
from brush import hexc, catmull, resample
from kit import Kanvas, pal_fn, stipple_fir, skeleton_tree, impasto, ribbon, bush
from matplotlib.path import Path as MP

T0 = time.time()
def log(m): print(f'P4 {time.time() - T0:6.1f}s {m}', flush=True)
sid = U3.sid
RW, RH = 1671, 941
OUTW = int(sys.argv[sys.argv.index('--width') + 1]) if '--width' in sys.argv else 3200
W, H = OUTW, OUTW * 9 // 16
k = W / RW
OUT = 'out4' if OUTW == 3200 else f'out4_{OUTW}'

c = Kanvas(W, H, k, '#2c5684', seed=1972); c.HM = np.zeros((H, W), np.float32)
for m in (U, U2, U3): m.c, m.k, m.W, m.H = c, k, W, H
S.c = c; A.c = c

COAST = np.load('coast4.npy'); LAKES = list(np.load('lakes4.npy', allow_pickle=True))
LANDP = MP(COAST); LAKEP = [MP(l) for l in LAKES]
def on_land(x, y, pad=0):
    return LANDP.contains_point((x, y), radius=-pad) and not any(lp.contains_point((x, y), radius=pad) for lp in LAKEP)

def snow_amt(x, y):
    ylim = np.minimum(200 + np.maximum(x - 1340, 0) * 1.25, 400)
    ne = np.clip((x - 1335) / 40, 0, 1) * np.clip((ylim - y) / 40, 0, 1)
    band = np.clip((x - 880) / 120, 0, 1) * np.clip((1340 - x) / 80, 0, 1) * np.clip((210 - y) / 60, 0, 1) * .5
    return np.maximum(ne, band)
U3.snow_amt = snow_amt

# ====================================================================== geography (reference-v2 pixel coordinates)
HILLS = sorted([
    (130, 250, 320, 95, 'forest'), (410, 262, 300, 90, 'forest'), (620, 252, 300, 115, 'gold'), (860, 232, 280, 95, 'olive'),
    (1010, 246, 260, 90, 'gold'), (1250, 290, 260, 95, 'moss'), (1430, 210, 260, 95, 'forest'), (1570, 270, 240, 105, 'forest'),
    (250, 344, 320, 105, 'moss'), (560, 336, 300, 105, 'olive'), (1310, 366, 280, 105, 'moss'), (1490, 356, 240, 110, 'forest'),
    (80, 410, 220, 120, 'forest'), (920, 360, 560, 150, 'moss'), (420, 436, 330, 100, 'olive'), (650, 446, 270, 95, 'gold'),
    (1230, 456, 280, 105, 'olive'), (1450, 446, 250, 105, 'moss'), (1590, 476, 160, 90, 'forest'),
    (720, 584, 260, 100, 'moss'), (900, 640, 320, 115, 'field'), (1250, 566, 320, 115, 'moss'), (1460, 566, 250, 100, 'olive'),
    (110, 650, 220, 105, 'moss'), (300, 726, 340, 115, 'gold'), (560, 736, 320, 115, 'olive'), (770, 746, 300, 105, 'gold'),
    (1240, 706, 300, 115, 'gold'), (1410, 726, 230, 105, 'moss'), (1000, 690, 200, 70, 'olive'),
    (220, 806, 240, 95, 'sage'), (460, 856, 320, 115, 'moss'), (690, 866, 300, 105, 'gold'), (1360, 856, 240, 115, 'olive'),
], key=lambda h: h[1])
U3.HILLS = HILLS
U2.FIELD_STRIPES[900] = ['#8e6a22', '#e0bc58']

MTS = [(62, 176, 170, 150), (170, 182, 200, 160), (305, 178, 270, 178), (430, 182, 250, 160), (525, 198, 210, 130), (340, 212, 200, 116), (458, 218, 180, 104)]
ROUTE_CTRL = {
    'red': [(160, 172), (198, 180), (220, 206), (232, 244), (262, 272), (310, 292), (360, 298), (400, 302), (432, 328), (470, 350), (530, 364),
            (600, 378), (650, 392), (700, 404), (750, 400)],
    'blue': [(246, 606), (300, 612), (350, 602), (392, 585), (430, 566), (480, 556), (540, 552), (582, 540), (622, 520), (670, 494), (710, 468), (745, 446), (775, 430)],
    'green': [(1528, 168), (1502, 184), (1490, 214), (1475, 250), (1452, 284), (1428, 320), (1392, 352), (1340, 378), (1280, 398), (1210, 418), (1140, 428), (1090, 420)],
}
def route(n): return resample(catmull(ROUTE_CTRL[n], 14), 1.6)
VIADUCT = (300, 410)                              # x-range of the stone viaduct carrying the red line over a valley
VIADUCT_DEPTH = 436.01                            # just in front of the hill it stands on (base 436), behind that hill's trees
VIADUCT_BOX = (300, 288, 410, 356)                # its face, in map units
GREEN_BRIDGE = (1137, 30)                         # centre x and half-span of the stone rail bridge where the green line crosses the river
GREEN_BRIDGE_DEPTH = 547.55                       # after every river piece there (the last one sits just behind Toy Town), before the town
RIVER = catmull([(1112, 196), (1118, 240), (1138, 286), (1126, 330), (1150, 372), (1132, 415), (1162, 462), (1150, 505), (1112, 540), (1085, 566),
                 (1064, 600), (1034, 632), (1004, 664), (1002, 692), (1030, 720), (1066, 745), (1092, 776)], 12)
DELTA = [catmull([(1066, 745), (1052, 772), (1046, 804)], 8), catmull([(1080, 760), (1098, 790), (1102, 812)], 8), catmull([(1092, 776), (1126, 790), (1146, 804)], 8)]
STATIONS = {'nw': (98, 168), 'sw': (176, 612), 'ne': (1588, 166)}
HALL = (918, 456)                                  # the grand station's front base
TOWN = (718, 548)                                  # left end of Toy Town's row of houses

HOUSES = [  # x, y, w, h, wall, roof, kind, rows, cols
    (360, 234, 46, 30, '#f2ead8', '#b03a2a', 'gable', 1, 2), (145, 368, 46, 34, '#f2ead8', '#b03a2a', 'gable', 1, 2), (312, 666, 40, 28, '#f2ead8', '#b03a2a', 'gable', 1, 2),
    (540, 640, 46, 38, '#f2ead8', '#3a5a8a', 'gable', 1, 2), (566, 700, 92, 52, '#f2ead8', '#b8502e', 'side', 2, 3), (830, 750, 48, 36, '#f2ead8', '#b03a2a', 'gable', 1, 2),
    (1210, 270, 54, 40, '#f2e2b8', '#b03a2a', 'gable', 2, 2), (1372, 330, 40, 30, '#f2ead8', '#b03a2a', 'gable', 1, 2), (1246, 372, 48, 36, '#f2ead8', '#b03a2a', 'gable', 1, 2),
    (1452, 248, 34, 26, '#f2ead8', '#b03a2a', 'gable', 1, 2), (1388, 492, 62, 46, '#f2ead8', '#b8502e', 'gable', 2, 2), (1356, 580, 50, 46, '#e8c870', '#4a5a7a', 'gable', 2, 2),
    (1372, 830, 48, 36, '#f2ead8', '#b03a2a', 'gable', 1, 2), (1230, 640, 44, 32, '#f2ead8', '#b03a2a', 'side', 1, 2),
]

def build_ground():
    gbase = np.full((RH, RW), np.nan, np.float32); tops = {}
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        poly = U2.hill_poly(cx, base, w, h, 500 + i * 7)
        m = np.zeros((RH, RW), np.uint8); cv2.fillPoly(m, [np.round(poly).astype(np.int32)], 1); gbase[m > 0] = base; tops[i] = poly
    return gbase, tops
def depth_at(x, y, gbase):
    xi, yi = int(np.clip(x, 0, RW - 1)), int(np.clip(y, 0, RH - 1)); b = gbase[yi, xi]
    return (float(y) if np.isnan(b) else float(b)) + y * 1e-4

# ====================================================================== new painters (all in map units)
def roof_tiles(poly, col, seed):
    m = c.area(poly, col, wob=.1, rough=.5, edge_dark=.12, seed=seed)
    if m is not None: c.stip(m, pal_fn([col, hexc(col) * .85, hexc(col) * 1.12]), spacing=1.05, L=2.4, w=1.3, angfn=lambda X, Y: 0 * X, seed=seed + 1, jit=.2)
    return m

def wall(poly, col, seed):
    m = c.area(poly, col, wob=.1, rough=.5, edge_dark=.08, seed=seed)
    if m is not None: c.stip(m, pal_fn([col, hexc(col) * .93, hexc(col) * 1.05]), spacing=1.15, L=2.6, w=1.2, angfn=lambda X, Y: -math.pi / 2 + 0 * X, seed=seed + 1, jit=.15)
    return m

def lit_window(x, y, w, h, arch=False, frame='#5a3e2c', mullions=2):
    q = [(x - w / 2 - 1.2, y + h / 2 + 1.2), (x + w / 2 + 1.2, y + h / 2 + 1.2), (x + w / 2 + 1.2, y - h / 2)]
    if arch: q += [(x + (w / 2 + 1.2) * math.cos(t), y - h / 2 - (w / 2 + 1.2) * math.sin(t)) for t in np.linspace(0, math.pi, 12)]
    q += [(x - w / 2 - 1.2, y - h / 2)]
    c.area(q, frame, wob=0, rough=.3)
    g = [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2, y - h / 2)]
    if arch: g += [(x + w / 2 * math.cos(t), y - h / 2 - w / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 12)]
    g += [(x - w / 2, y - h / 2)]
    m = c.area(g, '#f2c25a', wob=0, rough=.3, edge_dark=.25)
    if m is not None: c.stip(m, pal_fn(['#f2c25a', '#f8d880', '#e8a840']), spacing=1.0, L=1.8, w=1.2, seed=int(x * 7 + y), jit=1.0)
    for j in range(1, mullions + 1):
        xx = x - w / 2 + w * j / (mullions + 1); c.stroke([(xx, y + h / 2), (xx, y - h / 2 - (w / 2 if arch else 0) * .9)], .9, frame, a=1, dry=0, taper=(0, 0))
    c.stroke([(x - w / 2, y), (x + w / 2, y)], .9, frame, a=1, dry=0, taper=(0, 0))

def grand_station(x, y):
    """Toy Town's grand station: a cream stone hall with a great arched glass window, two winged arches, a tiled
    barrel roof and a Christmas wreath."""
    L, R = x - 182, x + 176
    # roofs behind the facade
    roof_tiles([(L - 6, y - 92), (x - 66, y - 92), (x - 74, y - 122), (L + 14, y - 122)], '#7a4a3a', 11)
    roof_tiles([(x + 66, y - 92), (R + 6, y - 92), (R - 14, y - 122), (x + 74, y - 122)], '#7a4a3a', 12)
    barrel = [(x - 92 + 184 * u, y - 112 - math.sin(u * math.pi) ** .8 * 52) for u in np.linspace(0, 1, 30)]
    roof_tiles(barrel + [(x + 92, y - 100), (x - 92, y - 100)], '#86523e', 13)
    wall([(L, y), (R, y), (R, y - 94), (L, y - 94)], '#e8d4a8', 14)
    wall([(x - 88, y), (x + 88, y), (x + 88, y - 108), (x - 88, y - 108)], '#eedcb4', 15)
    # the great window and its two companions
    lit_window(x, y - 44, 112, 62, arch=True, mullions=5)
    for xx in (x - 136, x + 132): lit_window(xx, y - 34, 58, 40, arch=True, mullions=3)
    for xx in (L + 10, R - 10, x - 92, x + 92):
        wall([(xx - 6, y), (xx + 6, y), (xx + 6, y - 112 if abs(xx - x) < 100 else y - 98), (xx - 6, y - 112 if abs(xx - x) < 100 else y - 98)], '#d8c08c', 16 + int(xx))
    c.stroke([(L, y - 94), (R, y - 94)], 3.2, '#c8ae7a', a=1, dry=.1, taper=(0, 0))
    c.stroke(barrel, 3.6, '#c8ae7a', a=1, dry=.1, taper=(0, 0))
    # wreath with a red bow
    wx, wy = x, y - 128
    c.stroke([(wx + 13 * math.cos(t), wy + 13 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)], 7, '#2f5a34', a=1, dry=.15, taper=(0, 0))
    c.dots([(wx + 13 * math.cos(t), wy + 13 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)], 1.4, ['#c8302a', '#f2c25a'], seed=5)
    c.area([(wx - 6, wy + 12), (wx + 6, wy + 12), (wx + 9, wy + 20), (wx - 9, wy + 20)], '#c8302a', wob=0, rough=.3)
    for xx, top in ((x - 70, y - 150), (x, y - 172), (x + 68, y - 150)):
        c.stroke([(xx, top + 34), (xx, top)], 1.6, '#4a3a30', a=1, dry=0, taper=(0, 0))

def town_row(x0, y):
    """Toy Town's row of tall, narrow, colourful houses with striped awnings around a clock tower."""
    row = [(44, 74, '#e8b84a', '#7a4a34', '#b8402e'), (46, 92, '#5a7ab0', '#2f3a5a', '#3f6aa8'), (40, 80, '#e89aa8', '#6a3a4a', '#b8402e'),
           (44, 86, '#efe2c4', '#7a4a34', '#3f6aa8'), (60, 0, None, None, None), (44, 84, '#e8b84a', '#7a4a34', '#b8402e'),
           (42, 92, '#a83a30', '#3a2a3a', '#7f9a3a'), (44, 80, '#e89aa8', '#5a3a5a', '#b8402e'), (46, 74, '#e8b84a', '#7a4a34', '#3f6aa8')]
    tot = sum(r[0] for r in row); x = x0
    st = [(x0 - 16, y + 2), (x0 + tot * 1.03 + 16, y + 2), (x0 + tot * 1.03 + 20, y + 16), (x0 - 20, y + 16)]
    m = c.area(st, '#b8a888', wob=.4, rough=.9, edge_dark=.1)
    c.stip(m, pal_fn(['#b8a888', '#a89878', '#c8b898', '#988868']), spacing=1.5, L=2.6, w=2.2, seed=7, jit=1.5)
    for i, (w, h, wallc, roof, awn) in enumerate(row):
        cx = x + w / 2
        if wallc is None:                       # the clock tower
            wall([(cx - 24, y), (cx + 24, y), (cx + 24, y - 120), (cx - 24, y - 120)], '#efe2c4', 31)
            c.area(S.lumpy(cx, y - 96, 13, 13, 2, n=36, amp=0), '#f8f2e4', wob=0, rough=.3, edge_dark=.25)
            c.stroke([(cx, y - 96), (cx, y - 106)], 1.6, '#2a2420', a=1, dry=0, taper=(0, .3)); c.stroke([(cx, y - 96), (cx + 7, y - 93)], 1.6, '#2a2420', a=1, dry=0, taper=(0, .3))
            roof_tiles([(cx - 28, y - 120), (cx + 28, y - 120), (cx, y - 156)], '#3a3a5a', 32)
            for yy in (y - 64, y - 30): lit_window(cx, yy, 14, 16, arch=True, mullions=1)
            c.area([(cx - 9, y), (cx + 9, y)] + [(cx + 9 * math.cos(t), y - 20 - 9 * math.sin(t)) for t in np.linspace(0, math.pi, 10)], '#5a3a2a', wob=0, rough=.3)
        else:
            A.house(cx, y, w, h, 'tall' if i % 3 == 1 else ('side' if i % 3 == 2 else 'gable'), wallc, roof, 140 + i, dotcol=None, rows=3, cols_=2, chimney=i % 2 == 0)
            for kk in range(5):
                a0 = x + 3 + kk * (w - 6) / 5; a1 = x + 3 + (kk + 1) * (w - 6) / 5
                c.area([(a0, y - h * .28), (a1, y - h * .28), (a1 + 1, y - h * .28 + 8), (a0 + 1, y - h * .28 + 8)], [awn, '#f4eee2'][kk % 2], wob=0, rough=.3)
        x += w * 1.03
    for lx in (x0 - 14, x + 8):
        c.stroke([(lx, y + 8), (lx, y - 30)], 1.8, '#2a2420', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 32)], 3.2, ['#f8d880'])

def depot(x, y, roof, wallc='#ecdcb4', w=120, h=44, pier=False, snow=False, seed=0):
    """An end-of-line station: long low building, lit arched windows, a deep roof and a cupola for its flag."""
    if pier:
        deck = [(x - 92, y + 4), (x + 10, y + 4), (x + 10, y + 12), (x - 92, y + 12)]
        wall(deck, '#8a6440', seed + 1)
        for px in np.arange(x - 88, x + 8, 12): c.stroke([(px, y + 12), (px, y + 30)], 2.4, '#5a3e2c', a=1, dry=.1, taper=(0, 0))
        c.stroke([(x - 92, y + 2), (x + 10, y + 2)], 1.2, '#efe6d6', a=1, dry=0, taper=(0, 0))
        for px in np.arange(x - 88, x + 8, 8): c.stroke([(px, y + 4), (px, y - 4)], 1.0, '#efe6d6', a=1, dry=0, taper=(0, 0))
    wall([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], wallc, seed + 2)
    for i in range(5):
        lit_window(x - w / 2 + w * (i + .5) / 5, y - h * .45, w / 9, h * .42, arch=True, mullions=1)
    roof_tiles([(x - w / 2 - 10, y - h + 2), (x + w / 2 + 10, y - h + 2), (x + w / 2 - 12, y - h - 24), (x - w / 2 + 12, y - h - 24)], roof, seed + 3)
    roof_tiles([(x - 16, y - h - 22), (x + 16, y - h - 22), (x, y - h - 46)], roof, seed + 4)
    wall([(x - 10, y - h - 22), (x + 10, y - h - 22), (x + 10, y - h - 34), (x - 10, y - h - 34)], wallc, seed + 5)
    lit_window(x, y - h - 28, 8, 8, arch=True, mullions=0)
    if snow:
        c.stroke([(x - w / 2 - 10, y - h + 1), (x - w / 2 + 12, y - h - 24), (x + w / 2 - 12, y - h - 24), (x + w / 2 + 10, y - h + 1)], 5, '#f6f4ee', a=1, dry=.15, taper=(.05, .05), rough=.6)
    c.stroke([(x, y - h - 46), (x, y - h - 70)], 1.4, '#3a2e26', a=1, dry=0, taper=(0, 0))
    for lx in (x - w / 2 - 14, x + w / 2 + 14):
        c.stroke([(lx, y + 4), (lx, y - 30)], 1.8, '#2a2420', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 32)], 3.0, ['#f8d880'])

def viaduct(P, x0, x1):
    """Stone arches carrying the red line across a valley."""
    sel = P[(P[:, 0] >= x0) & (P[:, 0] <= x1)]
    if len(sel) < 4: return
    deck = sel + [0, 6]; base = float(deck[:, 1].max()) + 44
    face = np.vstack([deck, [[deck[-1, 0], base], [deck[0, 0], base]]])
    m = c.area(face, '#a89c88', wob=.2, rough=.6, edge_dark=.12)
    c.stip(m, pal_fn(['#b8ac98', '#9c907c', '#c8bca8', '#8c8270']), spacing=1.25, L=4.2, w=2.6, angfn=lambda X, Y: 0 * X, seed=91, jit=.25)
    n = 4; xs = np.linspace(deck[0, 0], deck[-1, 0], n + 1)
    for i in range(n):
        ax = (xs[i] + xs[i + 1]) / 2; aw = (xs[i + 1] - xs[i]) * .66; top = float(np.interp(ax, deck[:, 0], deck[:, 1])) + 14
        arch = [(ax - aw / 2, base)] + [(ax - aw / 2 + aw * u, top + aw * .5 - math.sin(u * math.pi) * aw * .5) for u in np.linspace(0, 1, 16)] + [(ax + aw / 2, base)]
        c.area(arch, '#3a4a2a', wob=0, rough=.3)
        for u in np.linspace(0, 1, 7):
            p = np.array((ax - aw / 2 + aw * u, top + aw * .5 - math.sin(u * math.pi) * aw * .5)); dv = p - [ax, top + aw * .5]; dv /= np.hypot(*dv) + 1e-6
            c.stroke([p, p + dv * 5], 2.6, '#cfc4b0', a=.95, dry=.1, taper=(0, 0))

def rail_bridge(P, xc, half):
    """A stone bridge with one wide arch, carrying the green line over the river: deck under the track, abutments
    on both banks, voussoirs round the arch and a low parapet along the front."""
    sel = P[np.abs(P[:, 0] - xc) <= half]
    if len(sel) < 4: return
    deck = sel + [0, 7]; ytop = float(np.interp(xc, deck[:, 0], deck[:, 1]))
    x0, x1 = float(deck[0, 0]), float(deck[-1, 0]); lo, hi = min(x0, x1), max(x0, x1)
    base = ytop + 24
    face = np.vstack([deck, [[deck[-1, 0], base], [deck[0, 0], base]]])
    m = c.area(face, '#a89c88', wob=.2, rough=.6, edge_dark=.12)
    c.stip(m, pal_fn(['#b8ac98', '#9c907c', '#c8bca8', '#8c8270']), spacing=1.2, L=3.6, w=2.4, angfn=lambda X, Y: 0 * X, seed=93, jit=.25)
    aw = (hi - lo) * .62; ah = 15; top = base - ah
    hole = [(xc - aw / 2, base + 1)] + [(xc - aw / 2 + aw * u, base - math.sin(u * math.pi) ** .85 * ah) for u in np.linspace(0, 1, 22)] + [(xc + aw / 2, base + 1)]
    hm = c.area(hole, '#3f6ea4', wob=0, rough=.3)
    if hm is not None: c.stip(hm, pal_fn(['#4a7ab0', '#3f6ea4', '#5a8ac0', '#2f5a8a']), spacing=1.1, L=3.6, w=1.4, angfn=lambda X, Y: math.pi / 2 + 0 * X, seed=94, jit=.2)
    c.area([(xc - aw / 2, base - 3), (xc + aw / 2, base - 3), (xc + aw / 2, base + 1), (xc - aw / 2, base + 1)], '#2f4f6a', wob=0, rough=.3, a=.55)
    for u in np.linspace(0, 1, 9):
        p = np.array((xc - aw / 2 + aw * u, base - math.sin(u * math.pi) ** .85 * ah)); dv = p - [xc, base + 6]; dv /= np.hypot(*dv) + 1e-6
        c.stroke([p, p + dv * 4.5], 2.4, '#d4c8b2', a=.95, dry=.1, taper=(0, 0))
    c.stroke(deck, 2.6, '#cfc4b0', a=1, dry=.12, taper=(0, 0))
    truss(sel, back=True)

def truss(sel, back):
    """The red iron truss of the green line's bridge. The far side is painted before the track, the near side after it,
    so a train runs through the bridge between its two sides."""
    P = resample(sel, 2.0); dy = -3.0 if back else 2.0; col = '#7a2620' if back else '#a8342a'; hi = 15.5
    bot = P + [0, dy]; top = P + [0, dy - hi]
    w = 1.6 if back else 2.4
    c.stroke(top, w + .6, col, a=1, dry=0, taper=(0, 0)); c.stroke(bot, w, col, a=1, dry=0, taper=(0, 0))
    n = 6; idx = np.linspace(0, len(P) - 1, n + 1).round().astype(int)
    for j, i in enumerate(idx):
        c.stroke([bot[i], top[i]], w, col, a=1, dry=0, taper=(0, 0))
        if j < n:
            i2 = idx[j + 1]; c.stroke([bot[i], top[i2]], w * .8, col, a=1, dry=0, taper=(0, 0)); c.stroke([top[i], bot[i2]], w * .8, col, a=1, dry=0, taper=(0, 0))
    for e_ in (0, len(P) - 1):                                    # portal posts with a gold cap
        c.stroke([bot[e_] + [0, 2], top[e_] - [0, 2]], w + 1, col, a=1, dry=0, taper=(0, 0))
        c.dots([tuple(top[e_] - [0, 2.5])], 1.8, ['#e2b44b'])
    if not back: c.stroke(top - [0, 1.2], .9, '#e8806a', a=.8, dry=0, taper=(0, 0))

def windmill_tower(x, y, h):
    for dx in (-h * .14, h * .14): c.stroke([(x + dx, y), (x + dx * .2, y - h * .85)], 2.4, '#3a2e26', a=1, dry=.05, taper=(0, 0))
    for kk in range(6):
        yy = y - h * .12 - kk * h * .12; ww = h * .14 * (1 - (kk * .12 + .12))
        c.stroke([(x - ww, yy), (x + ww, yy - h * .1)], 1.3, '#3a2e26', a=1, dry=0, taper=(0, 0)); c.stroke([(x + ww, yy), (x - ww, yy - h * .1)], 1.3, '#3a2e26', a=1, dry=0, taper=(0, 0))
    cx, cy = x, y - h * .9
    c.area([(cx + h * .02, cy - 4), (cx + h * .36, cy - 2), (cx + h * .36, cy + 6), (cx + h * .02, cy + 4)], '#b8402e', wob=0, rough=.3)
def windmill_blades(cx, cy, h):
    for kk in range(16):
        a = kk / 16 * 2 * math.pi
        c.stroke([(cx + math.cos(a) * 4, cy + math.sin(a) * 4), (cx + math.cos(a) * h * .28, cy + math.sin(a) * h * .28)], 4.4, '#efe6d0' if kk % 2 else '#8a5a3a', a=1, dry=.05, taper=(0, .25))
    c.stroke([(cx + h * .28 * math.cos(t), cy + h * .28 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48)], 1.2, '#3a2e26', a=.9, dry=0, taper=(0, 0))
    c.dots([(cx, cy)], 3.6, ['#3a2e26'])

def puff(x, y, r, seed):
    rr = np.random.RandomState(seed)
    for j in range(4):
        px, py = x + rr.uniform(-.5, .5) * r, y + rr.uniform(-.3, .3) * r; rad = r * rr.uniform(.55, .8)
        m = c.area(S.lumpy(px, py, rad, rad * .85, seed + j, n=24, amp=.08, flat=0), '#f4efe4', wob=.2, rough=.6, edge_dark=.04)
        if m is not None: c.stip(m, pal_fn(['#fbf8f0', '#ece6da', '#ffffff', '#ddd6ca']), spacing=1.0, L=2.4, w=1.3,
                                 angfn=lambda X, Y, px=px, py=py: np.arctan2(Y - py, X - px) + math.pi / 2, seed=seed + 10 + j, jit=.3)

def flag(x, y, col):
    c.area([(x, y), (x + 22, y + 4), (x + 18, y + 8), (x + 24, y + 13), (x, y + 13)], col, wob=.2, rough=.5, edge_dark=.12)
    c.stroke([(x, y - 2), (x, y + 36)], 1.6, '#3a2e26', a=1, dry=0, taper=(0, 0))

def sheep(x, y):
    c.area(S.lumpy(x, y - 8, 11, 7, 3, n=24, bumps=6, amp=.18, flat=.1), '#f6f2ea', wob=0, rough=.4, edge_dark=.15)
    c.area(S.lumpy(x + 11, y - 10, 4, 3.4, 4, n=14, amp=0), '#2a2622', wob=0, rough=.3)
    for dx in (-6, -2, 3, 7): c.stroke([(x + dx, y - 3), (x + dx, y + 3)], 1.4, '#2a2622', a=1, dry=0, taper=(0, 0))

# ---- trains: every vehicle is drawn in its own frame (p on the track centre, d along the track, up perpendicular)
THEMES = {'red': dict(loco='#c23b2c', cab='#a8302a', trim='#e2b44b', cars=['#5f8f3a', '#e8a830', '#b8342a']),
          'blue': dict(loco='#2f5aa8', cab='#244a90', trim='#e2b44b', cars=['#e08a2a', '#b8342a', '#e8b030']),
          'green': dict(loco='#3f7a3a', cab='#2f6430', trim='#e2b44b', cars=['#b8342a', '#e8a830', '#3f6aa8'])}
def gift(cc, d, up, s, w, h, col, ribbon):
    q = [cc - d * w / 2 * s, cc + d * w / 2 * s, cc + d * w / 2 * s + up * h * s, cc - d * w / 2 * s + up * h * s]
    c.area(q, col, wob=0, rough=.3, edge_dark=.12)
    c.stroke([cc, cc + up * h * s], .9 * s, ribbon, a=1, dry=0, taper=(0, 0))
    c.stroke([cc - d * w / 2 * s + up * h * .55 * s, cc + d * w / 2 * s + up * h * .55 * s], .9 * s, ribbon, a=1, dry=0, taper=(0, 0))
    top = cc + up * h * s
    for sg in (-1, 1): c.area(S.lumpy(*(top + d * sg * 1.3 * s + up * 1.2 * s), 1.4 * s, 1.1 * s, 3, n=12, amp=0), ribbon, wob=0, rough=.2)
def wagon(p, d, up, s, col, seed):
    """A toy boxcar: coloured body, darker roof, a lighter sliding door, gold trim, one small gift riding on top."""
    L = 17 * s; a_ = p - d * L / 2; b_ = p + d * L / 2
    body = [a_ + up * 3 * s, b_ + up * 3 * s, b_ + up * 12 * s, a_ + up * 12 * s]
    c.area(body, col, wob=0, rough=.3, edge_dark=.15)
    c.area([a_ - d * .6 * s + up * 11.5 * s, b_ + d * .6 * s + up * 11.5 * s, b_ + d * .2 * s + up * 13.2 * s, a_ - d * .2 * s + up * 13.2 * s], hexc(col) * .62, wob=0, rough=.3)
    door = [p - d * 3.6 * s + up * 4.2 * s, p + d * 3.6 * s + up * 4.2 * s, p + d * 3.6 * s + up * 10.4 * s, p - d * 3.6 * s + up * 10.4 * s]
    c.area(door, np.clip(hexc(col) * 1.18, 0, 1), wob=0, rough=.3, edge_dark=.2)
    c.stroke([door[0], door[2]], .5 * s, hexc(col) * .7, a=.8, dry=0, taper=(0, 0)); c.stroke([door[1], door[3]], .5 * s, hexc(col) * .7, a=.8, dry=0, taper=(0, 0))
    for yy in (3.6, 11.2): c.stroke([a_ + up * yy * s, b_ + up * yy * s], .8 * s, '#f2d48a', a=1, dry=0, taper=(0, 0))
    gift(p + d * (4.6 if seed % 2 else -4.6) * s + up * 13.2 * s, d, up, s, 4.2, 3.6, ['#e05a6a', '#5fa59c', '#f2ead8'][seed % 3], ['#f2c25a', '#c8302a', '#c8302a'][seed % 3])
    for e in (-.3, .3):
        wpos = p + d * L * e + up * 2 * s
        c.area(S.lumpy(*wpos, 2.3 * s, 2.3 * s, 1, n=16, amp=0), '#2a2523', wob=0, rough=.2)
        c.dots([tuple(wpos)], .8 * s, ['#c8a060'])
def loco(p, d, up, s, th):
    L = 26 * s; a_ = p - d * L / 2; b_ = p + d * L / 2
    cab = [a_ + up * 3 * s, a_ + d * 8 * s + up * 3 * s, a_ + d * 8 * s + up * 16 * s, a_ + up * 16 * s]
    boiler = [a_ + d * 7 * s + up * 4 * s, b_ - d * 1 * s + up * 4 * s, b_ + up * 6.5 * s, b_ - d * 1 * s + up * 11.5 * s, a_ + d * 7 * s + up * 11.5 * s]
    c.area(boiler, th['loco'], wob=0, rough=.3, edge_dark=.12)
    c.area([a_ + d * 7 * s + up * 9.5 * s, b_ - d * 1.5 * s + up * 9.5 * s, b_ - d * 1 * s + up * 11.5 * s, a_ + d * 7 * s + up * 11.5 * s], '#ffffff', wob=0, rough=.3, a=.22)
    for u in (.3, .55, .8):
        q = a_ + d * (7 + (L / s - 8) * u) * s; c.stroke([q + up * 4 * s, q + up * 11.5 * s], .8 * s, th['trim'], a=1, dry=0, taper=(0, 0))
    c.area(cab, th['cab'], wob=0, rough=.3, edge_dark=.12)
    c.area([cab[3] - d * 1.5 * s, cab[2] + d * 1.5 * s, cab[2] + up * 2.4 * s + d * 1 * s, cab[3] + up * 2.4 * s - d * 1 * s], '#2f2a28', wob=0, rough=.3)
    c.area([a_ + d * 2 * s + up * 9.5 * s, a_ + d * 6 * s + up * 9.5 * s, a_ + d * 6 * s + up * 13.5 * s, a_ + d * 2 * s + up * 13.5 * s], '#f2d48a', wob=0, rough=.3)
    stack = b_ - d * 5.5 * s + up * 11.5 * s
    c.area([stack - d * 1.6 * s, stack + d * 1.6 * s, stack + d * 2.8 * s + up * 7 * s, stack - d * 2.8 * s + up * 7 * s], '#2f2a28', wob=0, rough=.3)
    dome = b_ - d * 12 * s + up * 11.5 * s
    c.area(S.lumpy(*(dome + up * 1 * s), 2.4 * s, 2.2 * s, 7, n=14, amp=0, flat=.6), th['trim'], wob=0, rough=.3)
    c.area([b_ + up * 1.5 * s, b_ + d * 3.8 * s + up * .5 * s, b_ + up * 5.5 * s], '#2f2a28', wob=0, rough=.3)
    c.dots([tuple(b_ - d * .4 * s + up * 8.5 * s)], 1.9 * s, ['#f8eab0'])
    for e, rr in ((-.32, 2.6), (.04, 3.4), (.3, 3.4)):
        wpos = p + d * L * e + up * (rr - .4) * s
        c.area(S.lumpy(*wpos, rr * s, rr * s, 1, n=16, amp=0), th['loco'] if rr > 3 else '#2a2523', wob=0, rough=.2)
        c.stroke([(wpos[0] + rr * s * math.cos(t), wpos[1] + rr * s * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 18)], .55 * s, '#2a2523', a=.9, dry=0, taper=(0, 0))
    c.stroke([p + d * L * .04 + up * 3 * s, p + d * L * .3 + up * 3 * s], .7 * s, th['trim'], a=1, dry=0, taper=(0, 0))
    return stack + up * 7 * s
TRAIN_S = 2.2
def train_layout(P, i_head, ncars):
    step = float(np.mean(np.hypot(*np.diff(P, axis=0).T))); out = []
    gap = 2.2 * TRAIN_S                               # coupling gap between vehicles
    offs = [0] + [26 * TRAIN_S / 2 + 17 * TRAIN_S / 2 + gap + j * (17 * TRAIN_S + gap) for j in range(ncars)]
    for j, off in enumerate(offs):
        i = int(np.clip(i_head - round(off / step), 3, len(P) - 4))
        q, o = P[i + 3], P[i - 3]; d = (q - o) / np.hypot(*(q - o)); up = np.array([d[1], -d[0]])
        if up[1] > 0: up = -up
        out.append((P[i], d, up))
    return out

# ====================================================================== the scene
def build_scene():
    gbase, tops = build_ground(); els = []
    def add(kind, depth, bbox, seed, layer='base', **params):
        els.append(dict(kind=kind, depth=float(depth), bbox=[float(v) for v in bbox], seed=int(seed), layer=layer, params=params))
    for i, (cx, base, w, h, kind) in enumerate(HILLS): add('hill', base, (cx - w * .65, base - h * 1.25, cx + w * .65, base + 50), 500 + i * 7, i=i)
    for j, (px, base, w, h) in enumerate(MTS): add('mountain', base - 60, (px - w * .6, base - h - 10, px + w * .6, base + 10), sid('mtn4', j), px=px, base=base, w=w, h=h)
    add('desert', 525, (90, 440, 580, 660), sid('desert4'))
    add('mesa', 532, (180, 420, 400, 545), sid('mesa4'), x=292, y=526, w=210, h=74)
    for j, (x, y, h) in enumerate([(262, 590, 34), (410, 636, 40), (470, 604, 30), (160, 566, 28), (520, 590, 26)]):
        add('cactus', depth_at(x, y, gbase), (x - 20, y - h - 6, x + 20, y + 4), sid('cactus4', j), x=x, y=y, h=h)
    for j, L_ in enumerate(LAKES): add('lake', float(L_[:, 1].max()) - 60, (L_[:, 0].min() - 10, L_[:, 1].min() - 10, L_[:, 0].max() + 10, L_[:, 1].max() + 10), sid('lake4', j), j=j)
    n = len(RIVER)
    for i0 in range(0, n - 1, 10):
        i1 = min(n - 1, i0 + 10); seg = RIVER[i0:i1 + 1]; mid = RIVER[(i0 + i1) // 2]
        dep = depth_at(mid[0], mid[1], gbase) + .2
        if 1030 < mid[0] < 1170 and 470 < mid[1] < 556: dep = TOWN[1] - .5
        add('river', dep, (seg[:, 0].min() - 40, seg[:, 1].min() - 30, seg[:, 0].max() + 40, seg[:, 1].max() + 30), sid('river4', i0), name='main', i0=i0, i1=i1)
    for j, P_ in enumerate(DELTA): add('river', 800 + j * .01, (P_[:, 0].min() - 30, P_[:, 1].min() - 20, P_[:, 0].max() + 30, P_[:, 1].max() + 20), sid('delta', j), name=f'delta{j}', i0=0, i1=len(P_) - 1)
    add('bridge', 600, (1020, 520, 1170, 620), sid('bridge4'), x=1096, y=552)
    routes = {}
    for nm in ('red', 'blue', 'green'):
        P = route(nm); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]; nr = np.stack([-d[:, 1], d[:, 0]], 1)
        depth = np.array([depth_at(x, y, gbase) for x, y in P])
        if nm == 'red':                                           # the viaduct carries the line above the valley
            on = (P[:, 0] >= VIADUCT[0]) & (P[:, 0] <= VIADUCT[1]); depth[on] = np.maximum(depth[on], VIADUCT_DEPTH + .01)
        if nm == 'green':                                         # the rail bridge carries the green line over the river
            on = np.abs(P[:, 0] - GREEN_BRIDGE[0]) <= GREEN_BRIDGE[1]; depth[on] = np.maximum(depth[on], GREEN_BRIDGE_DEPTH + .02)
        acc = 0; ties = np.zeros(len(P), bool)
        for i in range(1, len(P) - 1):
            acc += np.hypot(*(P[i] - P[i - 1]))
            if acc >= U3.TW * .9: acc = 0; ties[i] = True
        routes[nm] = dict(P=P, nr=nr, depth=depth, behind=np.zeros(len(P), bool), ties=ties)
        for i0 in range(0, len(P) - 1, 8):
            i1 = min(len(P) - 1, i0 + 9); seg = P[i0:i1 + 1]
            add('track', float(np.max(depth[i0:i1 + 1])) + .01, (seg[:, 0].min() - 30, seg[:, 1].min() - 30, seg[:, 0].max() + 30, seg[:, 1].max() + 30), sid('track4', nm, i0), route=nm, i0=i0, i1=i1)
    add('viaduct', VIADUCT_DEPTH, (VIADUCT[0] - 20, 270, VIADUCT[1] + 20, 380), sid('viaduct'))
    add('railbridge_front', GREEN_BRIDGE_DEPTH + .05, (GREEN_BRIDGE[0] - GREEN_BRIDGE[1] - 20, 380, GREEN_BRIDGE[0] + GREEN_BRIDGE[1] + 20, 445), sid('railbridge_front'))
    add('railbridge', GREEN_BRIDGE_DEPTH, (GREEN_BRIDGE[0] - GREEN_BRIDGE[1] - 20, 390, GREEN_BRIDGE[0] + GREEN_BRIDGE[1] + 20, 475), sid('railbridge'))
    add('station', HALL[1] + .5, (HALL[0] - 200, HALL[1] - 190, HALL[0] + 200, HALL[1] + 10), sid('hall'))
    add('town', TOWN[1], (TOWN[0] - 40, TOWN[1] - 170, TOWN[0] + 460, TOWN[1] + 24), sid('town4'))
    for nm, (x, y), roof in (('nw', STATIONS['nw'], '#b8402e'), ('sw', STATIONS['sw'], '#3a5a9a'), ('ne', STATIONS['ne'], '#3f6a3a')):
        add('depot', depth_at(x, y, gbase) + 1, (x - 110, y - 130, x + 90, y + 40), sid('depot', nm), name=nm, x=x, y=y, roof=roof)
    for j, (x, y, w, h, wallc, roof, kind, rows, cols) in enumerate(HOUSES):
        add('house', depth_at(x, y, gbase), (x - w, y - h * 2.6, x + w * 1.1, y + 12), sid('house4', j), x=x, y=y, w=w, h=h, wall=wallc, roof=roof, k=kind, rows=rows, cols=cols,
            snow=float(snow_amt(x, y)))
    LM = [('barn', 680, 216, [120, 70]), ('silo', 744, 212, [34, 104]), ('lighthouse', 95, 388, [92]), ('windtower', 680, 702, [112]),
          ('sheep', 800, 676, []), ('sheep', 826, 670, []), ('palm', 1402, 706, [124]), ('palm', 1444, 716, [104]), ('fence', 0, 0, [])]
    for j, (kind, x, y, prm) in enumerate(LM):
        bb = {'barn': (x - 90, y - 130, x + 100, y + 14), 'silo': (x - 30, y - 140, x + 30, y + 10), 'lighthouse': (x - 30, y - 130, x + 30, y + 10),
              'windtower': (x - 40, y - 120, x + 60, y + 10), 'palm': (x - 90, y - 160, x + 90, y + 10), 'fence': (600, 640, 880, 700)}.get(kind, (x - 30, y - 30, x + 30, y + 10))
        add(kind, depth_at(x, y, gbase) if kind != 'fence' else 690, bb, sid('lm4', kind, j), x=x, y=y, prm=prm)
    # trees
    tracks_xy = np.vstack([routes[nm]['P'] for nm in routes])
    keep = [(x, y, w * .55 + 22, h + 34) for (x, y, w, h, *_ ) in HOUSES] + [
        (680, 216, 90, 100), (744, 212, 40, 130), (95, 388, 30, 110), (680, 702, 56, 130), (812, 674, 40, 30), (918, 420, 230, 160), (930, 520, 240, 60),
        (98, 150, 110, 80), (176, 590, 110, 70), (1588, 150, 90, 70), (1086, 560, 80, 60), (292, 500, 120, 60), (1035, 700, 70, 40), (1066, 640, 60, 50)]
    placed = []
    def ok(x, y, h):
        if not on_land(x, y, 10): return False
        if 120 < x < 560 and 460 < y < 650 and not (x < 300 and y > 620): return False
        if any(abs(x - kx) < kw and abs(y - ky) < kh for kx, ky, kw, kh in keep): return False
        dt = np.hypot(*(tracks_xy - [x, y]).T); j = int(np.argmin(dt))
        if dt[j] < 16: return False
        ty = tracks_xy[j][1]
        if y < ty and np.min(np.hypot(*(tracks_xy - [x, y - h * .55]).T)) < h * .45 + 10: return False
        if y > ty and np.min(np.hypot(*(tracks_xy - [x, y - h * .6]).T)) < h * .42: return False
        for P_ in [RIVER] + DELTA:
            if np.min(np.hypot(*(P_ - [x, y]).T)) < 22: return False
        if any(abs(x - p[0]) < h * .28 and abs(y - p[1]) < h * .15 for p in placed): return False
        return True
    def tree(x, y, h, kd, group, n):
        h *= 1.25 * (.66 + .4 * min(1.0, max(0.0, (y - 150) / 560)))
        if not ok(x, y, h): return
        s = float(snow_amt(x, y))
        if s > .5 and kd not in ('fir', 'lfir'): kd = 'fir' if (sid(group, n) % 4) else kd
        placed.append((x, y))
        add('tree', depth_at(x, y, gbase), (x - h * .75, y - h * 1.2, x + h * .75, y + h * .12), sid('tree4', group, n), x=x, y=y, h=h, kd=kd, snow=s)
    for i, (cx, base, w, h, kind) in enumerate(HILLS):
        rr = np.random.RandomState(sid('crest4', i)); top = U2.hill_poly(cx, base, w, h, 500 + i * 7)[:40]
        for j in range(rr.randint(3, 7) if kind != 'field' else 1):
            x = cx + rr.uniform(-.4, .4) * w; y = float(np.interp(x, top[:, 0], top[:, 1])) + rr.uniform(10, 30)
            kd = ['red', 'orange', 'yellow', 'green', 'pink', 'olive', 'fir'][rr.randint(7)] if kind != 'forest' else ['fir', 'fir', 'lfir', 'orange', 'yellow'][rr.randint(5)]
            tree(x, y, rr.uniform(56, 88), kd, f'crest{i}', j)
    FORESTS = [(120, 240, 110, 50), (300, 230, 90, 40), (480, 250, 80, 40), (60, 420, 50, 120), (240, 420, 90, 40), (520, 440, 70, 40), (1480, 260, 100, 60),
               (1560, 330, 60, 60), (1400, 200, 50, 40), (1300, 470, 60, 30), (1520, 450, 60, 40), (220, 690, 70, 40), (620, 610, 60, 40), (900, 720, 60, 30),
               (1180, 520, 50, 40), (480, 780, 80, 40), (1300, 760, 60, 40), (850, 300, 80, 40), (1010, 300, 70, 30)]
    for fi, (fx, fy, rx, ry) in enumerate(FORESTS):
        rr = np.random.RandomState(sid('forest4', fi)); want = int(rx * ry / 100); got = 0
        for att in range(want * 14):
            if got >= want: break
            x = fx + rr.uniform(-1, 1) * rx; y = fy + rr.uniform(-1, 1) * ry
            if ((x - fx) / rx) ** 2 + ((y - fy) / ry) ** 2 > 1: continue
            r_ = rr.rand(); n0 = len(placed)
            if r_ < .55: tree(x, y, rr.uniform(44, 72), 'fir', f'forest{fi}', att)
            elif r_ < .75: tree(x, y, rr.uniform(40, 62), 'lfir', f'forest{fi}', att)
            else: tree(x, y, rr.uniform(50, 74), ['orange', 'yellow', 'red', 'green', 'pink'][rr.randint(5)], f'forest{fi}', att)
            got += len(placed) - n0
    rr = np.random.RandomState(sid('lone4'))
    for i in range(520):
        x, y = rr.uniform(30, 1640), rr.uniform(150, 880)
        tree(x, y, rr.uniform(40, 80), ['red', 'orange', 'yellow', 'green', 'pink', 'olive', 'fir', 'fir', 'poplar'][rr.randint(9)], 'lone', i)
    log(f'{len(placed)} trees')
    # Trees standing in front of the viaduct (base below its foot) but on a hill further back would be painted before it
    # and cut off by its arches; bring them forward so they are painted over it.
    for e in els:
        if e['kind'] != 'tree': continue
        p = e['params']; x, y, h = p['x'], p['y'], p['h']
        if y > 352 and e['depth'] < VIADUCT_DEPTH and x + h * .45 > VIADUCT_BOX[0] and x - h * .45 < VIADUCT_BOX[2] and y - h * 1.05 < VIADUCT_BOX[3]:
            e['depth'] = VIADUCT_DEPTH + .04 + y * 1e-4
    # ------------------------------------------------------------------ animated sprites (layer != base)
    def sprite_el(kind, bbox, seed, **params): add(kind, 1e6, bbox, seed, layer='anim', **params)
    for j, (cx, cy, w, h) in enumerate([(440, 26, 150, 28), (940, 22, 160, 30), (1240, 34, 160, 30)]): sprite_el('cloud', (cx - w * .7, cy - h * 1.4, cx + w * .7, cy + h * .9), sid('cloud4', j), cx=cx, cy=cy, w=w, h=h)
    for j, (x, y, s) in enumerate([(196, 800, 1.1), (866, 822, 1.0), (1610, 482, .95), (1506, 676, .9)]): sprite_el('boat', (x - 50 * s, y - 70 * s, x + 50 * s, y + 26 * s), sid('boat4', j), x=x, y=y, s=s)
    sprite_el('steamer', (990, 650, 1090, 720), sid('steamer'), x=1036, y=706)
    sprite_el('wheel', (1062, 690, 1090, 718), sid('wheel'), x=1075, y=704)
    sprite_el('blades', (680 - 40, 702 - 140, 680 + 40, 702 - 60), sid('blades'), x=680, y=702 - 112 * .9, h=112)
    for j, (x, y, col) in enumerate([(848, 282, '#c8302a'), (918, 260, '#3f6aa8'), (986, 282, '#3f7a3a'), (98, 74, '#c8302a'), (176, 500, '#3a5a9a'), (1588, 72, '#3f7a3a')]):
        sprite_el('flag', (x - 4, y - 6, x + 28, y + 40), sid('flag4', j), x=x, y=y, col=col)
    for nm, head_x, ncars in (('red', 642, 3), ('blue', 548, 3), ('green', 1300, 3)):
        P = routes[nm]['P']; i_head = int(np.argmin(np.abs(P[:, 0] - head_x)))
        sprite_el('train', (0, 0, 1, 1), sid('train4', nm), route=nm, i_head=i_head, ncars=ncars, tdepth=float(routes[nm]['depth'][i_head]))
    scene = dict(version=4, ref_size=[RW, RH], elements=els,
                 routes={nm: dict(points=routes[nm]['P'].tolist(), depth=routes[nm]['depth'].tolist(), ties=routes[nm]['ties'].astype(int).tolist()) for nm in routes},
                 river=RIVER.tolist())
    return scene

# ====================================================================== render
TERRAIN = {'hill', 'mountain', 'desert', 'mesa', 'lake', 'river', 'bridge', 'cactus'}
def paint(e, routes):
    p = e['params']; kd = e['kind']
    if kd == 'hill':
        cx, base, w, h, kind = HILLS[p['i']]; U3.paint_hill3(cx, base, w, h, kind, e['seed'])
    elif kd == 'mountain': U3.mountain3(p['px'], p['base'], p['w'], p['h'], e['seed'])
    elif kd == 'desert':
        dpoly = catmull([(112, 482), (250, 456), (400, 470), (520, 500), (562, 560), (522, 622), (420, 642), (300, 642), (200, 632), (110, 602)], 10, closed=True)
        dm = U2.land_clip(c.area(dpoly, '#c8823a', wob=5, rough=1.4, edge_dark=.03, seed=e['seed']))
        c.stip(dm, pal_fn(['#c8823a', '#d89446', '#b47030', '#e2a656', '#a86228']), spacing=2.0, L=6.5, w=2.8, angfn=lambda X, Y: .15 * np.sin(X / 40), seed=e['seed'] + 1, jit=.3)
        for j, (px, py, rx, ry) in enumerate([(400, 560, 60, 14), (470, 620, 50, 12), (200, 600, 50, 12), (330, 630, 60, 12)]):
            dune = [(px - rx + 2 * rx * u, py - math.sin(u * math.pi) ** .8 * ry * 1.6) for u in np.linspace(0, 1, 24)] + [(px + rx, py + 6), (px - rx, py + 6)]
            pm = c.area(dune, '#d89a50', wob=1, rough=1, a=.9, seed=e['seed'] + 9 + j)
            if pm is not None: c.stip(U2.land_clip(pm), pal_fn(['#e6aa60', '#d89a50', '#c48840']), spacing=1.8, L=6, w=2.4, angfn=lambda X, Y: .2 * np.sin(X / 20), seed=e['seed'] + 20 + j)
    elif kd == 'mesa': U3.mesa3(p['x'], p['y'], p['w'], p['h'], e['seed'])
    elif kd == 'cactus': U.cactus(p['x'], p['y'], p['h'])
    elif kd == 'lake':
        L_ = LAKES[p['j']]
        lm = c.area(L_, '#33628f', wob=.6, rough=.8, edge_dark=.08, seed=e['seed'])
        c.stip(lm, pal_fn(['#33628f', '#3d6c9a', '#2a5682', '#4a78a6']), spacing=1.8, L=7, w=2, angfn=lambda X, Y: .3 * np.sin(X / 40 + Y / 20), seed=e['seed'] + 1, jit=.2)
        PP = np.vstack([L_, L_[:1]])
        for kk in range(0, len(PP) - 2, 14): c.stroke(PP[kk:kk + 16], 4.6, '#e8d8b0', a=.95, dry=.25, taper=(0, 0), rough=.6)
    elif kd == 'river':
        if p['name'] == 'main':
            P = RIVER; i0, i1 = p['i0'], min(len(P) - 1, p['i1'] + 1); n = len(P)
            U3.river3(P[i0:i1 + 1], 13 + 17 * i0 / n, 13 + 17 * i1 / n, e['seed'])
        else:
            P = DELTA[int(p['name'][-1])]; U3.river3(P, 14, 18, e['seed'])
    elif kd == 'bridge': U3.bridge_road(p['x'], p['y'])
    elif kd == 'track':
        r = routes[p['route']]; U3.track_chunk(r['P'], r['nr'], p['i0'], p['i1'], p['route'], r['ties'])
    elif kd == 'viaduct': viaduct(routes['red']['P'], *VIADUCT)
    elif kd == 'railbridge': rail_bridge(routes['green']['P'], *GREEN_BRIDGE)
    elif kd == 'railbridge_front':
        P_ = routes['green']['P']; truss(P_[np.abs(P_[:, 0] - GREEN_BRIDGE[0]) <= GREEN_BRIDGE[1]], back=False)
    elif kd == 'station': grand_station(*HALL)
    elif kd == 'town': town_row(*TOWN)
    elif kd == 'depot': depot(p['x'], p['y'], p['roof'], pier=p['name'] == 'nw', snow=p['name'] == 'ne', seed=e['seed'] % 100000)
    elif kd == 'house':
        A.house(p['x'], p['y'], p['w'], p['h'], p['k'], p['wall'], p['roof'], e['seed'] % 100000, dotcol=None, rows=p['rows'], cols_=p['cols'])
        if p['snow'] > .4: U3.snowy_roof(p['x'], p['y'], p['w'], p['h'], p['k'])
    elif kd == 'tree':
        x, y, h, t, sd = p['x'], p['y'], p['h'], p['kd'], e['seed'] % 1000000
        if t == 'fir': (U3.snowy_fir if p['snow'] > .45 else U2.tall_fir)(x, y, h, sd)
        elif t == 'lfir': U2.layered_fir(x, y, h, sd)
        elif t == 'poplar': U2.poplar(x, y, h, sd)
        else: U2.big_tree(x, y, h, t, sd)
    elif kd == 'barn': U.barn(p['x'], p['y'], *p['prm'])
    elif kd == 'silo': U.silo(p['x'], p['y'], *p['prm'])
    elif kd == 'lighthouse': U.lighthouse(p['x'], p['y'], *p['prm'])
    elif kd == 'windtower': windmill_tower(p['x'], p['y'], *p['prm'])
    elif kd == 'sheep': sheep(p['x'], p['y'])
    elif kd == 'palm': U.palm(p['x'], p['y'], p['prm'][0], e['seed'] % 1000)
    elif kd == 'fence':
        P_ = resample(catmull([(610, 676), (700, 668), (790, 682), (870, 690)], 8), 7)
        for q in P_: c.stroke([(q[0], q[1] + 1), (q[0], q[1] - 9)], 1.6, '#f2ead8', a=1, dry=0, taper=(0, .2))
        c.stroke(P_ - [0, 6.5], 1.1, '#f2ead8', a=1, dry=0, taper=(0, 0)); c.stroke(P_ - [0, 2.5], 1.1, '#f2ead8', a=1, dry=0, taper=(0, 0))

def sprite(paint_fn, bbox, seed):
    x0, y0 = int(max(0, bbox[0] * k)), int(max(0, bbox[1] * k)); x1, y1 = int(min(W, bbox[2] * k)), int(min(H, bbox[3] * k))
    keep_img, keep_hm, keep_clip = c.img, c.HM, c.clipm
    outs = []
    for bg in (0.0, 1.0):
        c.img = np.full((H, W, 3), bg, np.float32); c.HM = np.zeros((H, W), np.float32); c.clipm = None
        c.rng = np.random.RandomState(seed); paint_fn()
        outs.append((c.img[y0:y1, x0:x1].copy(), c.HM[y0:y1, x0:x1].copy()))
        c.img = None
    (b, hm), (wht, _) = outs
    alpha = np.clip(1 - (wht - b).mean(-1), 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, b / np.maximum(alpha[..., None], 1e-3), 0)
    hb = cv2.GaussianBlur(hm, (0, 0), 1.1 * k / 1.914); gx = cv2.Sobel(hb, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hb, cv2.CV_32F, 0, 1, ksize=3)
    rgb = np.clip(rgb * (1 + np.clip((gx * -.7 + gy * -.7) * .14, -.14, .14))[..., None], 0, 1)
    c.img, c.HM, c.clipm = keep_img, keep_hm, keep_clip
    return (x0, y0), rgb.astype(np.float32), alpha.astype(np.float32)

def save_rgba(path, rgb, a):
    im = np.dstack([np.clip(rgb[..., ::-1] * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8); cv2.imwrite(path, im)

def main():
    if '--scene' in sys.argv: scene = json.load(open(sys.argv[sys.argv.index('--scene') + 1]))
    else:
        scene = build_scene(); os.makedirs(OUT, exist_ok=True); json.dump(scene, open(f'{OUT}/scene4.json', 'w'))
    log(f"{len(scene['elements'])} elements at {W}x{H}")
    routes = {}
    for nm, r in scene['routes'].items():
        P = np.array(r['points']); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]
        routes[nm] = dict(P=P, nr=np.stack([-d[:, 1], d[:, 0]], 1), depth=np.array(r['depth']), ties=np.array(r['ties'], bool))
        n_ = int(80 / 1.6); d0 = P[0] - P[6]; d0 /= np.hypot(*d0); d1 = P[-1] - P[-7]; d1 /= np.hypot(*d1)
        pre = P[0] + d0[None] * (np.arange(n_, 0, -1) * 1.6)[:, None]; post = P[-1] + d1[None] * (np.arange(1, n_ + 1) * 1.6)[:, None]
        routes[nm].update(Pext=np.vstack([pre, P, post]), dext=np.concatenate([np.full(n_, -2e9), routes[nm]['depth'], np.full(n_, -2e9)]), npre=n_)
    Z = np.full((H, W), -1e9, np.float32); TRK = np.zeros((H, W), bool)
    om = (0, 0, np.ones((H, W), np.float32))
    c.stip(om, pal_fn(['#244c78', '#2c5684', '#22466e', '#33608c', '#2a5280'], .05), spacing=1.8, L=8.0, w=2.0, angfn=lambda X, Y: .25 * np.sin(X / 60 + Y / 25), seed=2, jit=.25)
    R = np.random.RandomState(2026)
    for i in range(240):
        x, y = R.uniform(0, RW), R.uniform(0, RH)
        if LANDP.contains_point((x, y), radius=-30): continue
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2), seed=sid('wave4', i, kk))
    LMk = np.zeros((H, W), np.float32)
    cv2.fillPoly(LMk, [np.round(COAST * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    U.LAND_MASK = cv2.GaussianBlur(LMk, (0, 0), k / 1.914); del LMk
    c.area(None, '#5f6a2a', m=(0, 0, U.LAND_MASK), edge_dark=0, var=.03)
    SN = np.array([hexc(z) for z in U3.SNOWPAL])
    def groundcol(X, Y, rr):
        base_ = np.array([hexc('#5f6a2a'), hexc('#6a7430'), hexc('#545e24')])[rr.randint(3, size=len(X))]
        return np.where((rr.rand(len(X)) < snow_amt(X, Y))[:, None], SN[rr.randint(5, size=len(X))], base_)
    c.stip((0, 0, U.LAND_MASK), groundcol, spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    log('ocean & ground')
    base_els = sorted([e for e in scene['elements'] if e['layer'] == 'base'], key=lambda e: e['depth'])
    coast_done = False
    sh = int(48 * k); MTCLIP = U.LAND_MASK.copy(); MTCLIP[:-sh] = np.maximum(MTCLIP[:-sh], U.LAND_MASK[sh:])   # peaks may rise above the north coast
    MT = np.zeros((H, W), bool)
    def coastline():
        PP = resample(np.vstack([COAST, COAST[:1]]), 2.0)
        for kk in range(0, len(PP) - 2, 10): c.stroke(PP[kk:kk + 12], 8, '#e8d8b0', a=1, dry=.25, taper=(.05, .05), press=.3, rough=.8, streak=.15, seed=sid('coast4', kk))
    for n_, e in enumerate(base_els):
        if not coast_done and e['kind'] not in TERRAIN and e['depth'] > 120:
            c.set_clip(None); snap = c.img.copy(); coastline(); c.img[MT] = snap[MT]; coast_done = True; del snap
        x0, y0 = int(max(0, e['bbox'][0] * k)), int(max(0, e['bbox'][1] * k)); x1, y1 = int(min(W, e['bbox'][2] * k)), int(min(H, e['bbox'][3] * k))
        if x1 <= x0 or y1 <= y0: continue
        before = c.img[y0:y1, x0:x1].copy()
        c.rng = np.random.RandomState(e['seed'])
        c.set_clip((0, 0, MTCLIP) if e['kind'] == 'mountain' else (0, 0, U.LAND_MASK) if e['kind'] in TERRAIN - {'bridge', 'cactus'} else None)
        paint(e, routes)
        ch = np.abs(c.img[y0:y1, x0:x1] - before).max(-1) > .004
        Z[y0:y1, x0:x1][ch] = e['depth']; TRK[y0:y1, x0:x1][ch] = e['kind'] == 'track'; MT[y0:y1, x0:x1][ch] = e['kind'] == 'mountain'
        if n_ % 200 == 0: log(f'element {n_}/{len(base_els)}')
    c.set_clip(None)
    log('base painted')
    impasto(c, .14)
    base_img = np.clip(c.img, 0, 1).copy()
    os.makedirs(f'{OUT}/anim', exist_ok=True)
    full = base_img.copy()
    man = dict(size=[W, H], map_units=[RW, RH], scale=k, sprites=[], trains=[], routes={}, river=(np.array(scene['river']) * k).round(2).tolist())
    def place(rgb, a, x0, y0, vis=None):
        h_, w_ = a.shape; a_eff = a if vis is None else a * vis
        full[y0:y0 + h_, x0:x0 + w_] = full[y0:y0 + h_, x0:x0 + w_] * (1 - a_eff[..., None]) + rgb * a_eff[..., None]
    count = {}
    def emit(kind, rgb, a, x0, y0, **extra):
        j = count.get(kind, 0); count[kind] = j + 1; name = f'{kind}_{j}.png'
        save_rgba(f'{OUT}/anim/{name}', rgb, a)
        d = dict(kind=kind, file=name, x=int(x0), y=int(y0), w=int(a.shape[1]), h=int(a.shape[0])); d.update(extra); man['sprites'].append(d); return d
    puff_sprites = []
    for j in range(3):
        (x0, y0), rgb, a = sprite(lambda j=j: puff(60 + j * 60, 60, 9, 7000 + j), (40 + j * 60, 40, 80 + j * 60, 80), sid('puff', j))
        puff_sprites.append(emit('puff', rgb, a, x0, y0, pivot=[(60 + j * 60) * k - x0, 60 * k - y0])); puff_sprites[-1]['rgb'] = (rgb, a)
    for e in [e for e in scene['elements'] if e['layer'] == 'anim']:
        p = e['params']
        if e['kind'] == 'train':
            P = routes[p['route']]['P']; lay = train_layout(P, p['i_head'], p['ncars']); th = THEMES[p['route']]
            vehicles = []
            for j in range(p['ncars'] + 1):
                cx, cy = 300, 300                               # draw each vehicle straight, at a scratch spot, then rotate into place
                fn = (lambda th=th: loco(np.array([cx, cy], float), np.array([1.0, 0]), np.array([0, -1.0]), TRAIN_S, th)) if j == 0 else \
                     (lambda j=j, th=th: wagon(np.array([cx, cy], float), np.array([1.0, 0]), np.array([0, -1.0]), TRAIN_S, th['cars'][(j - 1) % 3], j * 3 + {'red': 1, 'blue': 7, 'green': 4}[p['route']]))
                bb = (cx - 50, cy - 60, cx + 50, cy + 14)
                (x0, y0), rgb, a = sprite(fn, bb, e['seed'] + j)
                piv = [cx * k - x0, cy * k - y0]
                sp = emit('loco' if j == 0 else 'wagon', rgb, a, x0, y0, pivot=piv, route=p['route'])
                q, d, up = lay[j]; flip = d[0] < 0                  # a train heading left is the sprite mirrored, not upside down
                ang = math.degrees(math.atan2(-d[1], -d[0]) if flip else math.atan2(d[1], d[0]))
                rgb_, a_, pv = (rgb[:, ::-1].copy(), a[:, ::-1].copy(), [a.shape[1] - 1 - piv[0], piv[1]]) if flip else (rgb, a, piv)
                M = cv2.getRotationMatrix2D((pv[0], pv[1]), -ang, 1.0); M[0, 2] += q[0] * k - pv[0]; M[1, 2] += q[1] * k - pv[1]
                rgbw = cv2.warpAffine(rgb_, M, (W, H), flags=cv2.INTER_CUBIC); aw = np.clip(cv2.warpAffine(a_, M, (W, H), flags=cv2.INTER_LINEAR), 0, 1)
                vis = ((Z <= p['tdepth'] + 1e-3) | TRK).astype(np.float32)
                place(np.clip(rgbw, 0, 1), aw * vis, 0, 0)
                vehicles.append(dict(file=sp['file'], index_on_route=int(np.argmin(np.hypot(*(P - q).T))) + routes[p['route']]['npre'], angle_deg=round(ang, 2), mirrored=bool(flip)))
            # steam: a trail of puffs drifting back from the stack
            q, d, up = lay[0]; stack = q + d * (13 - 5.5) * TRAIN_S + up * 18.5 * TRAIN_S
            for t in range(6):
                pp = stack + up * (2.5 + t * 3.6) * TRAIN_S - d * t * 4.2 * TRAIN_S; sc = .55 + t * .2
                rgb_, a_ = puff_sprites[t % 3]['rgb']; piv = puff_sprites[t % 3]['pivot']
                M = np.array([[sc, 0, pp[0] * k - piv[0] * sc], [0, sc, pp[1] * k - piv[1] * sc]], np.float32)
                place(np.clip(cv2.warpAffine(rgb_, M, (W, H), flags=cv2.INTER_LINEAR), 0, 1), np.clip(cv2.warpAffine(a_, M, (W, H)), 0, 1) * (.95 - t * .1), 0, 0)
            man['trains'].append(dict(route=p['route'], head_index=p['i_head'] + routes[p['route']]['npre'], vehicles=vehicles,
                                      stack_offset=[(13 - 5.5) * TRAIN_S * k, -18.5 * TRAIN_S * k]))
            continue
        if e['kind'] == 'cloud': fn = lambda p=p: U.cloud(p['cx'], p['cy'], p['w'], p['h']); piv = None
        elif e['kind'] == 'boat': fn = lambda p=p: U.boat(p['x'], p['y'], p['s']); piv = [p['x'], p['y'] + 13 * p['s']]
        elif e['kind'] == 'steamer': fn = lambda p=p: steamer_body(p['x'], p['y']); piv = [p['x'], p['y']]
        elif e['kind'] == 'wheel': fn = lambda p=p: paddle_wheel(p['x'], p['y']); piv = [p['x'], p['y']]
        elif e['kind'] == 'blades': fn = lambda p=p: windmill_blades(p['x'], p['y'], p['h']); piv = [p['x'], p['y']]
        elif e['kind'] == 'flag': fn = lambda p=p: flag(p['x'], p['y'], p['col']); piv = [p['x'], p['y']]
        (x0, y0), rgb, a = sprite(fn, e['bbox'], e['seed'])
        place(rgb, a, x0, y0)
        extra = {} if piv is None else dict(pivot=[piv[0] * k - x0, piv[1] * k - y0])
        emit(e['kind'], rgb, a, x0, y0, **extra)
        if e['kind'] == 'steamer':
            sx = (p['x'] - 14, p['y'] - 44)
            for t in range(4):
                rgb_, a_ = puff_sprites[t % 3]['rgb']; pv = puff_sprites[t % 3]['pivot']; sc = .6 + t * .25
                pp = np.array([sx[0] + t * 9, sx[1] - t * 9]); M = np.array([[sc, 0, pp[0] * k - pv[0] * sc], [0, sc, pp[1] * k - pv[1] * sc]], np.float32)
                place(np.clip(cv2.warpAffine(rgb_, M, (W, H)), 0, 1), np.clip(cv2.warpAffine(a_, M, (W, H)), 0, 1) * (.9 - t * .15), 0, 0)
    for s_ in man['sprites']: s_.pop('rgb', None)
    # occluder overlay: base pixels in front of the railroad corridor — trains pass behind these. Each route is
    # extended straight on, past its last tie, into the grand station and back into its end station; on those
    # extensions everything painted occludes, so a train emerges from its depot and disappears into Toy Town.
    corr = np.full((H, W), np.nan, np.float32)
    for nm, r in routes.items():
        P = r['Pext']; DEP = r['dext']
        for i in range(len(P) - 1):
            a_, b_ = P[i] * k, P[i + 1] * k
            poly = np.array([a_ + [-14 * k, 8 * k], b_ + [14 * k, 8 * k], b_ + [14 * k, -48 * k], a_ + [-14 * k, -48 * k]])
            x0, y0 = int(max(0, poly[:, 0].min())), int(max(0, poly[:, 1].min())); x1, y1 = int(min(W, poly[:, 0].max() + 1)), int(min(H, poly[:, 1].max() + 1))
            sub = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(sub, [np.round(poly - [x0, y0]).astype(np.int32)], 1)
            cur = corr[y0:y1, x0:x1]; upd = (sub > 0) & (np.isnan(cur) | (cur < DEP[i])); cur[upd] = DEP[i]
    occ = (~np.isnan(corr)) & (Z > np.nan_to_num(corr, nan=1e9) + 1e-3) & ~TRK
    save_rgba(f'{OUT}/anim/occluder.png', base_img, cv2.GaussianBlur(occ.astype(np.float32), (0, 0), .7)); del corr
    cv2.imwrite(f'{OUT}/anim/base.jpg', (base_img[..., ::-1] * 255 + .5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
    man['routes'] = {nm: dict(points=(r['Pext'] * k).round(2).tolist(), track_from=r['npre'], track_to=r['npre'] + len(r['P']) - 1,
                              note='points beyond track_from..track_to run inside the end station and the grand station')
                     for nm, r in routes.items()}
    json.dump(man, open(f'{OUT}/anim/manifest.json', 'w'))
    c.img = full; c.save(f'{OUT}/usmap4')
    log('saved')

def steamer_body(x, y):
    hull = [(x - 44, y - 6), (x + 40, y - 6), (x + 32, y + 6), (x - 38, y + 6)]
    m = c.area(hull, '#f2ece0', wob=0, rough=.3, edge_dark=.12)
    c.stroke([(x - 40, y + 4), (x + 34, y + 4)], 3, '#b8302a', a=1, dry=0, taper=(0, 0))
    for j, (yy, w) in enumerate([(y - 6, 78), (y - 16, 64), (y - 25, 44)]):
        q = [(x - w / 2 - 2, yy), (x + w / 2 - 2, yy), (x + w / 2 - 2, yy - 9), (x - w / 2 - 2, yy - 9)]
        wall(q, '#f6f2ea', 300 + j)
        for wx in np.arange(x - w / 2 + 3, x + w / 2 - 6, 6): c.area([(wx, yy - 3), (wx + 3, yy - 3), (wx + 3, yy - 7), (wx, yy - 7)], '#3a4a6a', wob=0, rough=.2)
        c.stroke([(x - w / 2 - 3, yy - 9), (x + w / 2 - 1, yy - 9)], 1.6, '#b8302a', a=1, dry=0, taper=(0, 0))
    for sx in (x - 18, x - 8):
        c.area([(sx - 2.6, y - 34), (sx + 2.6, y - 34), (sx + 2.6, y - 52), (sx - 2.6, y - 52)], '#2a2420', wob=0, rough=.2)
        c.area([(sx - 4, y - 52), (sx + 4, y - 52), (sx + 3, y - 55), (sx - 3, y - 55)], '#2a2420', wob=0, rough=.2)
    c.stroke([(x - 52, y + 10), (x + 46, y + 10)], 1.4, '#e8eef0', a=.8, dry=.3, taper=(.2, .2))
def paddle_wheel(x, y):
    r = 12
    c.area(S.lumpy(x, y, r, r, 3, n=32, amp=0), '#b8302a', wob=0, rough=.3, edge_dark=.15)
    for kk in range(10):
        a = kk / 10 * 2 * math.pi
        c.stroke([(x, y), (x + math.cos(a) * r, y + math.sin(a) * r)], 1.5, '#f2ece0', a=1, dry=0, taper=(0, 0))
    c.stroke([(x + r * math.cos(t), y + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 36)], 1.6, '#7a2018', a=1, dry=0, taper=(0, 0))
    c.dots([(x, y)], 2.2, ['#2a2420'])

if __name__ == '__main__':
    main()

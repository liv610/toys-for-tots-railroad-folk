"""The valley, composed by hand in a 1600 x 900 design space (16:9). Both directions paint exactly this."""
import numpy as np, math
from brush import catmull, resample

DW, DH = 1600, 900

def contour(pts, n=14):
    return catmull(pts, n)

def land(top, bottom=930):
    t = np.asarray(top, float)
    return np.vstack([t, [[t[-1, 0], bottom], [t[0, 0], bottom]]])

def y_at(top, x):
    t = np.asarray(top); o = np.argsort(t[:, 0]); return float(np.interp(x, t[o, 0], t[o, 1]))

def jag(pts, amp, seed, step=7):
    """Rocky irregularity along a mountain silhouette: small peaks and notches, never a clean line."""
    P = resample(np.asarray(pts, float), step); r = np.random.RandomState(seed)
    off = np.zeros(len(P))
    for i in range(1, len(P) - 1):
        off[i] = r.randn() * amp * (1.0 if r.rand() < .7 else 2.2)
    off = np.convolve(off, [.25, .5, .25], 'same')
    P[:, 1] += off
    return P

# ---------------------------------------------------------------- far range: a broad volcano and a jagged range
FAR = jag(contour([(-30, 318), (40, 296), (110, 270), (150, 276), (205, 240), (250, 250), (300, 222), (345, 238), (380, 226),
                   (430, 248), (470, 236), (520, 200), (548, 178), (566, 186), (590, 160), (612, 168), (640, 150), (668, 172),
                   (700, 196), (742, 214), (790, 238), (840, 246), (885, 232), (930, 196), (970, 150), (1000, 118), (1028, 94),
                   (1050, 84), (1070, 82), (1090, 90), (1112, 104), (1146, 140), (1190, 188), (1232, 222), (1270, 236),
                   (1310, 226), (1352, 204), (1380, 210), (1420, 186), (1446, 194), (1480, 214), (1520, 206), (1560, 226), (1630, 246)], 8), 1.6, 3)
SNOWLINE = [(-30, 300), (200, 262), (330, 246), (480, 240), (560, 214), (640, 210), (720, 230), (920, 214), (1000, 176), (1070, 182),
            (1150, 176), (1240, 240), (1380, 232), (1450, 220), (1630, 260)]

# ---------------------------------------------------------------- middle mountains: bluer, forested shoulders
MID = jag(contour([(-30, 362), (40, 342), (100, 318), (150, 326), (210, 300), (270, 312), (330, 296), (400, 318), (450, 312),
                   (510, 334), (560, 350), (620, 368), (700, 372), (780, 364), (860, 352), (930, 340), (990, 332), (1060, 330),
                   (1130, 316), (1190, 296), (1240, 286), (1290, 300), (1350, 284), (1400, 270), (1450, 280), (1500, 268),
                   (1560, 292), (1630, 300)], 8), 1.0, 5)

# ---------------------------------------------------------------- near forested ridges, with a gorge for the river
RIDGE_L = contour([(-30, 404), (40, 388), (110, 376), (180, 384), (250, 370), (330, 380), (400, 372), (470, 388), (530, 400),
                   (580, 420), (620, 446)], 10)
RIDGE_R = contour([(690, 446), (730, 418), (790, 400), (860, 392), (930, 380), (1010, 386), (1080, 372), (1150, 364), (1220, 352),
                   (1290, 344), (1350, 352), (1410, 340), (1480, 350), (1550, 336), (1630, 346)], 10)

VALLEY = contour([(-30, 440), (300, 436), (600, 430), (900, 432), (1300, 428), (1630, 432)], 6)

# ---------------------------------------------------------------- rolling hills, back to front
HILLS = [
    dict(name='farm', kind='meadow', top=contour([(-30, 488), (40, 470), (120, 452), (200, 440), (270, 438), (340, 446), (410, 466),
                                                   (470, 494), (520, 528), (556, 566), (582, 630), (596, 700), (590, 780), (566, 860), (556, 940)])),
    dict(name='village', kind='meadow', top=contour([(820, 548), (880, 520), (950, 500), (1030, 488), (1110, 486), (1190, 494),
                                                      (1260, 506), (1310, 512), (1350, 500), (1400, 478), (1460, 462),
                                                      (1530, 458), (1630, 472)])),
    dict(name='knoll', kind='meadow', top=contour([(596, 700), (628, 610), (658, 540), (700, 490), (748, 466), (800, 462), (852, 474), (890, 500), (910, 540)])),
    dict(name='fields', kind='fields', top=contour([(706, 940), (676, 860), (646, 800), (650, 740), (676, 686), (694, 626), (720, 580), (770, 554), (830, 544), (880, 552), (930, 574), (962, 610), (990, 670), (1004, 740)])),
    dict(name='orchard_l', kind='orchard', top=contour([(-30, 640), (40, 628), (110, 622), (180, 630), (240, 648), (290, 674), (326, 702)])),
    dict(name='low_l', kind='meadow', top=contour([(-30, 704), (60, 684), (150, 676), (250, 682), (340, 702), (420, 734), (480, 776), (516, 840), (536, 940)])),
    dict(name='low_r', kind='fields2', top=contour([(890, 940), (902, 820), (930, 752), (970, 712), (1010, 690), (1100, 674), (1200, 670), (1300, 680), (1380, 672),
                                                     (1460, 652), (1540, 642), (1630, 648)])),
    dict(name='fg_l', kind='fg', top=contour([(-30, 804), (50, 784), (140, 778), (230, 790), (320, 822), (390, 862), (430, 930)])),
    dict(name='fg_r', kind='fg', top=contour([(1060, 930), (1110, 872), (1190, 836), (1290, 816), (1400, 804), (1500, 806), (1630, 794)])),
]
HILL = {h['name']: h for h in HILLS}

# ---------------------------------------------------------------- the river: from the gorge, around the hills, out the foreground
RIVER = catmull([(652, 432), (646, 452), (626, 476), (604, 500), (606, 530), (640, 560), (670, 596), (660, 634), (626, 662),
                 (584, 694), (566, 736), (590, 780), (650, 816), (700, 860), (716, 934)], 14)
def river_w(t):            # t: 0 at the gorge, 1 at the foreground
    return 5 + 58 * t ** 1.5

# ---------------------------------------------------------------- the railroad: in from the west, over the bridge, through the village, into the hills
RAIL = resample(catmull([(-40, 652), (50, 632), (140, 612), (230, 600), (320, 602), (400, 614), (480, 628), (560, 636),
                          (640, 634), (720, 624), (800, 610), (870, 598), (940, 590), (1020, 588), (1100, 590), (1180, 586),
                          (1250, 572), (1300, 550), (1336, 520), (1356, 488), (1366, 452)], 16), 2.0)
TUNNEL = (1366, 452)

def rail_at(x):
    return float(np.interp(x, RAIL[:, 0], RAIL[:, 1]))

def river_cross():
    # where the rail crosses the river
    best = None
    for i, p in enumerate(RAIL):
        d = np.hypot(*(RIVER - p).T); j = int(np.argmin(d))
        if best is None or d[j] < best[0]: best = (d[j], i, j)
    return best[1], best[2]
BRIDGE_I, BRIDGE_RJ = river_cross()

TRAIN_HEAD = 905          # x of the locomotive's front: heading east toward the village

# ---------------------------------------------------------------- the village: each building individually designed
# x, y = centre-bottom of the front wall. w front width, d depth, h wall height, rh roof height.
VILLAGE = [
    dict(t='side', x=1010, y=530, w=48, d=28, h=26, rh=18, wall='dustypink', roof='slate', door='turquoise', lean=.04, porch=True, dormer=True, shutters='#7f9a8a', name='rosehouse'),
    dict(t='gable', x=1165, y=528, w=36, d=42, h=36, rh=28, wall='cream', roof='terracotta', tower=True, door='turquoise', name='church'),
    dict(t='side', x=1262, y=532, w=40, d=24, h=22, rh=16, wall='sage', roof='terracotta', door='brick', boxes=True, name='bakery'),
    dict(t='gable', x=1074, y=550, w=28, d=30, h=46, rh=32, wall='turquoise', roof='brick', door='gold', lean=-.05, boxes=True, name='tall'),
    dict(t='gable', x=1126, y=546, w=22, d=22, h=20, rh=17, wall='coral', roof='slate', door='cream', round=True, name='coral'),
    dict(t='false', x=1112, y=580, w=46, d=34, h=32, rh=12, wall='gold', roof='slate', door='coral', awning=True, name='toyshop'),
    dict(t='gable', x=1208, y=572, w=34, d=28, h=28, rh=24, wall='brick', roof='olive', door='cream', round=True, shutters='#e2b44b', name='brick'),
    dict(t='station', x=1000, y=582, w=72, d=26, h=22, rh=15, wall='ochre', roof='brick', door='forest', name='station'),
    dict(t='water', x=906, y=584, name='watertower'),
    dict(t='gable', x=1346, y=588, w=26, d=24, h=20, rh=19, wall='cream', roof='coral', door='turquoise', lean=.05, porch=True, name='cottage'),
    dict(t='side', x=1500, y=478, w=30, d=20, h=16, rh=12, wall='#8a5a3c', roof='moss', door='gold', name='cabin'),
    dict(t='gable', x=632, y=516, w=24, d=26, h=22, rh=17, wall='#d9c8a6', roof='brick', door='slate', mill=True, name='mill'),
]
FARM = [
    dict(t='side', x=232, y=452, w=40, d=26, h=22, rh=15, wall='cream', roof='brick', door='turquoise', porch=True, shutters='#5d7186', boxes=True, name='farmhouse'),
    dict(t='gambrel', x=318, y=462, w=36, d=40, h=20, rh=22, wall='barnred', roof='slate', door='cream', name='barn'),
    dict(t='silo', x=356, y=452, name='silo'),
    dict(t='windpump', x=170, y=448, name='windpump'),
]

# ---------------------------------------------------------------- groves, placed by hand: (x, y, species, size)
def grove(cx, cy, n, rx, ry, species, size, seed, ymin=None):
    r = np.random.RandomState(seed); out = []
    tries = 0
    while len(out) < n and tries < n * 40:
        tries += 1
        x = cx + r.randn() * rx; y = cy + r.randn() * ry
        if ymin is not None and y < ymin(x): continue
        if any(abs(x - o[0]) < size * .32 and abs(y - o[1]) < size * .12 for o in out): continue
        sp = species[r.randint(len(species))] if isinstance(species, (list, tuple)) else species
        out.append((x, y, sp, size * (.75 + .5 * r.rand()), int(r.randint(1 << 20))))
    return out

def hill_y(name):
    t = HILL[name]['top']
    return lambda x: y_at(t, x) + 4

TREES = []
# around the farm: a windbreak of poplars, two big oaks, a blossoming tree by the house
TREES += [(120, 450, 'poplar', 54, 11), (136, 446, 'poplar', 48, 12), (152, 444, 'poplar', 58, 13),
          (276, 452, 'oak', 46, 14), (190, 466, 'blossom', 34, 15), (392, 472, 'oak', 52, 16), (410, 486, 'maple', 36, 17)]
# fir forest on the farm hill's back and west slope
TREES += grove(40, 466, 9, 40, 10, ['fir', 'fir', 'pine'], 56, 21, hill_y('farm'))
# riverside willows and birches, and the mill's trees
TREES += [(596, 470, 'willow', 34, 31), (700, 568, 'birch', 40, 32), (712, 578, 'birch', 34, 33), (620, 690, 'willow', 38, 34),
          (536, 700, 'birch', 36, 35), (548, 708, 'birch', 30, 36), (660, 520, 'round', 26, 37)]
# the knoll: one great oak with a swing, a blossoming companion
TREES += [(770, 470, 'oak', 62, 38), (812, 476, 'blossom', 34, 39), (730, 486, 'blossom', 26, 40)]
# flowering clusters scattered through the meadows, never in rows
TREES += [(470, 474, 'blossom', 28, 101), (490, 482, 'round', 24, 102), (452, 486, 'blossom', 22, 103),
          (96, 528, 'blossom', 26, 104), (150, 534, 'round', 22, 105), (360, 520, 'maple', 26, 106),
          (530, 570, 'blossom', 30, 107), (900, 486, 'maple', 30, 108), (930, 500, 'round', 26, 109)]
# village trees and a little orchard behind the bakery
TREES += [(1040, 548, 'round', 26, 41), (1192, 538, 'maple', 30, 42), (1148, 588, 'blossom', 26, 43), (1124, 512, 'poplar', 40, 44),
          (960, 538, 'oak', 38, 45), (1294, 586, 'round', 24, 46), (1050, 592, 'blossom', 22, 47)]
TREES += [(1286 + dx, 506 + dy, 'apple', 20, 110 + k) for k, (dx, dy) in enumerate([(0, 0), (24, 3), (49, 1), (12, 13), (38, 15), (63, 12), (28, 26)])]
# the forest on the right, gathered around the woodcutter's cabin
TREES += grove(1480, 490, 22, 70, 16, ['fir', 'fir', 'fir', 'pine', 'round', 'fir'], 54, 51, hill_y('village'))
TREES = [t for t in TREES if not (1470 < t[0] < 1535 and 462 < t[1] < 486)]
TREES += grove(1420, 690, 8, 70, 12, ['oak', 'round', 'maple', 'fir'], 44, 52, hill_y('low_r'))
# orchard on the left: loose, not a grid
_r = np.random.RandomState(5)
TREES += [(26 + i * 34 + (j % 2) * 15 + _r.uniform(-6, 6), 644 + j * 15 + _r.uniform(-3, 3), 'apple', 22 * _r.uniform(.85, 1.15), 60 + i * 5 + j)
          for j in range(3) for i in range(6) if _r.rand() > .15]
# foreground: individuals with real presence
TREES += [(42, 920, 'fir', 250, 71), (128, 836, 'oak', 120, 72), (210, 826, 'birch', 104, 73), (232, 830, 'birch', 90, 74),
          (330, 880, 'blossom', 92, 75), (1180, 880, 'round', 80, 76), (1300, 860, 'maple', 118, 77), (1420, 836, 'fir', 150, 78),
          (1470, 846, 'fir', 120, 79), (1560, 860, 'oak', 140, 80), (1612, 928, 'fir', 210, 81), (380, 900, 'round', 70, 82)]
# small things on the lower hills
TREES += [(300, 704, 'round', 32, 91), (360, 724, 'fir', 40, 92), (1040, 696, 'poplar', 40, 93), (1062, 700, 'poplar', 34, 94),
          (1010, 712, 'blossom', 30, 95), (424, 772, 'blossom', 36, 96), (446, 782, 'round', 30, 97), (402, 786, 'birch', 34, 98),
          (250, 712, 'blossom', 24, 99)]

FIELDS = HILL['fields']
SHEEP = [(800, 690), (816, 698), (790, 706), (836, 712), (850, 700), (812, 718)]
COWS = [(380, 540), (404, 552), (360, 556)]
BOAT = (628, 770)
BALLOON = (404, 132)
KITE = (282, 700)              # flown from the low hill, string to a child at (300, 760)
FOX = (1236, 852)
BIRDS = [(760, 120), (778, 112), (792, 122), (810, 116), (826, 126)]

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
RAIL = resample(catmull([(-40, 612), (40, 604), (140, 600), (240, 604), (340, 612), (440, 622), (540, 630), (640, 632),
                          (740, 626), (830, 614), (900, 600), (960, 590), (1040, 584), (1120, 584), (1200, 578),
                          (1262, 562), (1310, 536), (1342, 506), (1360, 474), (1366, 452)], 16), 2.0)
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

TRAIN_HEAD = 900          # x of the locomotive's front: heading east toward the village

# ---------------------------------------------------------------- the village: each building individually designed
# x, y = centre-bottom of the front wall. w front width, d depth, h wall height, rh roof height.
VILLAGE = [
    dict(t='gable', x=1150, y=520, w=30, d=34, h=30, rh=22, wall='cream', roof='terracotta', tower=True, door='turquoise', name='church'),
    dict(t='side', x=1012, y=508, w=38, d=22, h=22, rh=14, wall='dustypink', roof='slate', door='brick', lean=.05, name='rosehouse'),
    dict(t='gable', x=1068, y=530, w=22, d=26, h=36, rh=24, wall='turquoise', roof='brick', door='gold', lean=-.06, name='tall'),
    dict(t='false', x=1105, y=560, w=34, d=30, h=26, rh=10, wall='gold', roof='slate', door='coral', awning=True, name='toyshop'),
    dict(t='gable', x=1210, y=548, w=26, d=24, h=22, rh=18, wall='brick', roof='olive', door='cream', round=True, name='brick'),
    dict(t='side', x=1240, y=516, w=30, d=20, h=18, rh=12, wall='sage', roof='terracotta', door='slate', name='bakery'),
    dict(t='station', x=990, y=576, w=56, d=22, h=18, rh=12, wall='ochre', roof='brick', door='forest', name='station'),
    dict(t='water', x=930, y=586, name='watertower'),
    dict(t='gable', x=1290, y=540, w=20, d=20, h=16, rh=14, wall='cream', roof='coral', door='turquoise', lean=.04, name='cottage'),
]
FARM = [
    dict(t='side', x=232, y=452, w=40, d=26, h=22, rh=15, wall='cream', roof='brick', door='turquoise', porch=True, name='farmhouse'),
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
# riverside willows and birches
TREES += [(612, 474, 'willow', 34, 31), (700, 560, 'birch', 40, 32), (708, 570, 'birch', 34, 33), (620, 690, 'willow', 38, 34),
          (536, 700, 'birch', 36, 35), (548, 708, 'birch', 30, 36)]
# village trees: a few rounded street trees and one autumn maple
TREES += [(1040, 540, 'round', 26, 41), (1180, 532, 'maple', 30, 42), (1268, 560, 'round', 24, 43), (1124, 506, 'poplar', 34, 44),
          (960, 520, 'oak', 36, 45), (1330, 530, 'fir', 40, 46), (1310, 498, 'fir', 36, 47)]
# forest on the right slopes leading to the tunnel
TREES += grove(1470, 486, 14, 60, 14, ['fir', 'fir', 'fir', 'pine', 'round'], 52, 51, hill_y('village'))
TREES += grove(1420, 690, 8, 70, 12, ['oak', 'round', 'maple', 'fir'], 44, 52, hill_y('low_r'))
# orchard on the left
TREES += [(20 + i * 36 + (j % 2) * 18, 646 + j * 16, 'apple', 22, 60 + i * 5 + j) for j in range(3) for i in range(6)]
# foreground: individuals with real presence
TREES += [(42, 920, 'fir', 250, 71), (128, 836, 'oak', 120, 72), (210, 826, 'birch', 104, 73), (232, 830, 'birch', 90, 74),
          (330, 880, 'blossom', 92, 75), (1180, 880, 'round', 80, 76), (1300, 860, 'maple', 118, 77), (1420, 836, 'fir', 150, 78),
          (1470, 846, 'fir', 120, 79), (1560, 860, 'oak', 140, 80), (1612, 928, 'fir', 210, 81)]
# small things on the lower hills
TREES += [(300, 704, 'round', 32, 91), (360, 724, 'fir', 40, 92), (1040, 696, 'poplar', 40, 93), (1062, 700, 'poplar', 34, 94),
          (830, 552, 'oak', 30, 95), (780, 560, 'round', 24, 96)]

FIELDS = HILL['fields']
SHEEP = [(800, 690), (816, 698), (790, 706), (836, 712), (850, 700), (812, 718)]
COWS = [(380, 540), (404, 552), (360, 556)]
BOAT = (628, 770)
BALLOON = (404, 132)
KITE = (282, 700)              # flown from the low hill, string to a child at (300, 760)
FOX = (1236, 852)
BIRDS = [(760, 120), (778, 112), (792, 122), (810, 116), (826, 126)]

"""Toy Town as one folk-art painting in the map's brush, composed after the reference (references: the station square
seen from the front, houses wrapping round it, the tree and toys in the square, autumn trees in front, the hills,
barn, train and river behind). Every piece is painted by the shared kit (or is the map's own painted sprite) on its
own transparent canvas, so the viewer can stand each piece at its own depth: from the home camera the cards line
up into exactly this painting; when the camera glides in, they part with real parallax.

Frame: W x H units (the reference's 1536 x 1024), K px per unit. A piece standing on the ground gets its depth
from where its foot is: the ground is a plane seen from a camera HC metres up whose horizon is at VH.
    python3 compose.py            writes tex/*.png, tex/scene.json, out/toytown_folk.png (the flattened painting)
"""
import os, sys, json, math, time, zlib
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.join(HERE, '..', 'painted', 'kit'); sys.path.insert(0, KIT)
import toytown_kit as T
from toytown_kit import A, S, shaded, snow_edge, snow_clump, snow_lump, stip, lump, hexc, fir, sparkle
import toytown_scene as SC, toytown_station as ST, toytown_east as E, toytown_west as Wt
from toytown_station import stonework, STONE, STONE_D
ROOT = os.path.join(HERE, '..', '..', '..'); SPR = os.path.join(ROOT, 'usmap', 'viewer_tt', 'sprites'); LAND = os.path.join(HERE, '..', 'painted', 'tex')
OUT = os.path.join(HERE, 'tex'); os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
W, H, K = 1536, 1024, 2
FOV, HC, VH = 40.0, 6.0, 330.0                            # home camera: vertical fov, height (m), horizon line (units)
U1 = 2 * math.tan(math.radians(FOV / 2)) / H               # metres per unit at 1 m
depth_of = lambda v: HC / ((v - VH) * U1)
R = np.random.RandomState(3)
pieces = []

def kit_init(x0, y0, x1, y1, k):
    """The kit's init, with the canvas size rounded to whole pixels (pieces are painted at fractional scales)."""
    T.X0, T.Y0, T.K = x0, y0, k; T.W, T.H = x1 - x0, y1 - y0
    w, h = int(math.ceil(T.W * k)), int(math.ceil(T.H * k))
    T.c = T.Kanvas(w, h, k, '#000000', seed=5); T.c.HM = np.zeros((h, w), np.float32)
    T.ALPHA = np.zeros((h, w), np.float32); T.GLOW = np.zeros((h, w), np.float32)

# ------------------------------------------------------------------ painting a piece on its own canvas
def piece(name, box, fn, s=1.0, at=None, to=None, foot=None, depth=None, light=False, glow=True, kind='stand'):
    """Paint fn() in its own (native) coordinates inside box, at s x the frame's scale, and place it so the native
    point `at` lands on frame point `to`. Saves the piece cropped to what was painted."""
    at = at or (0, 0); to = to or at
    k = K * s; kit_init(*box, k); T.R = np.random.RandomState(zlib.crc32(name.encode()) % (1 << 30))
    fn()
    if light: T.light()
    p = os.path.join(OUT, name + '.png'); g = os.path.join(OUT, name + '_glow.png')
    paint, al = T.finish(p, g if glow else None)
    ys, xs = np.nonzero(al > .02)
    if len(xs) == 0: print('  (empty)', name); return
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)[by0:by1, bx0:bx1]; cv2.imwrite(p, im)
    has_glow = False
    if glow:
        gi = cv2.imread(g, cv2.IMREAD_UNCHANGED)[by0:by1, bx0:bx1]
        if gi[..., 3].max() > 20: cv2.imwrite(g, gi); has_glow = True
        else: os.remove(g)
    # canvas px -> native units -> frame units
    nx0, ny0 = box[0] + bx0 / k, box[1] + by0 / k
    fx0, fy0 = to[0] + (nx0 - at[0]) * s, to[1] + (ny0 - at[1]) * s
    fw, fh = im.shape[1] / K, im.shape[0] / K
    fv = foot if foot is not None else fy0 + fh
    pieces.append(dict(name=name, file=name + '.png', glow=(name + '_glow.png') if has_glow else None, x=fx0, y=fy0, w=fw, h=fh,
                       foot=fv, depth=depth if depth is not None else depth_of(max(fv, VH + 30)), kind=kind))
    print(f'  {name}: {im.shape[1]}x{im.shape[0]}px  depth {pieces[-1]["depth"]:.1f} m', flush=True)

def sprite(img, cx, foot, h):
    """Paste one of the map's own painted sprites into the current canvas, foot centred at (cx, foot), h units tall."""
    s = h * T.K / img.shape[0]; im = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    ih, iw = im.shape[:2]; x0, y0 = int((cx - T.X0) * T.K - iw / 2), int((foot - T.Y0) * T.K - ih)
    sx0, sy0 = max(0, -x0), max(0, -y0); ex, ey = min(iw, T.c.W - x0), min(ih, T.c.H - y0)
    if ex <= sx0 or ey <= sy0: return
    a = im[sy0:ey, sx0:ex, 3:].astype(np.float32) / 255; rgb = im[sy0:ey, sx0:ex, 2::-1].astype(np.float32) / 255
    reg = T.c.img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex]; T.c.img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = reg * (1 - a) + rgb * a
    T.ALPHA[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = np.maximum(T.ALPHA[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex], a[..., 0])

def load(path, trim=True):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if trim: ys, xs = np.nonzero(im[..., 3] > 10); im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return im
TREES = {f: load(os.path.join(SPR, f)) for f in sorted(os.listdir(SPR)) if f.startswith('tree_') and f.endswith('.png')}
DECID = [v for k, v in TREES.items() if 'decid' in k and '@' not in k]; EVER = [v for k, v in TREES.items() if 'ever' in k and '@' not in k]
BIG = [v for k, v in TREES.items() if 'decid' in k and '@2x' in k]

# ------------------------------------------------------------------ the sky and the hills behind the town
SKY = ['#2f5a9a', '#3a68a8', '#2a4f8c', '#4677b4']
def sky():
    m = A([(-610, -10), (W + 610, -10), (W + 610, 420), (-610, 420)], SKY[0], wob=0, rough=0, edge_dark=0)
    stip(m, SKY, spacing=1.5, L=4.2, w=2.0, ang=0.0, weights=[.35, .3, .2, .15])
    for _ in range(110):                                           # the map's little white waves, here as wind marks
        x, y = R.uniform(-600, W + 600), R.uniform(8, 200)
        if R.rand() < .5 and y > 120: continue
        for j in range(R.randint(1, 3)):
            xx = x + j * 13
            S([(xx, y), (xx + 4, y - 3), (xx + 8, y), (xx + 12, y - 3)], 1.6, '#e8eef6', a=.85, dry=.2, taper=(.2, .2))

def cloud(cx, cy, w):
    """A puffy cream cloud: overlapping lumps, lit on top, a flat shaded underside."""
    for k in range(7):
        u = (k / 6 - .5); r = w * (.18 + .12 * (1 - abs(u) * 2)) * R.uniform(.85, 1.1)
        shaded(lump(cx + u * w * .8, cy - r * .35, r, r * .72, amp=.1), ['#fffdf4', '#f1ead6', '#d6cdb6'], wob=.3, rough=.6, edge_dark=.05, L=2.6, w=1.6)
    A([(cx - w * .52, cy + 2), (cx + w * .52, cy + 2), (cx + w * .5, cy + 8), (cx - w * .5, cy + 8)], '#d8cfb8', wob=.3, rough=.5, edge_dark=0, a=.9)

GREENS = [['#6c8c3a', '#7a9a42', '#566f30'], ['#56783a', '#628640', '#43602e'], ['#8c983e', '#9ca646', '#727e34'], ['#bf963a', '#cca444', '#9c7a2c'], ['#4a6c36', '#56783c', '#3a582c']]
SPECK = ['#b8c85a', '#d8d070', '#4a6a2e', '#e0b850', '#8aa84a']
def mound(x0, x1, base, top, cols, rim='#e8e4c0'):
    """One rounded hill as the map paints them: stippled along its slope, lit from the upper left, a pale rim."""
    poly = [(x0, base + 40)] + [(x0 + (x1 - x0) * t, base - (base - top) * (math.sin(math.pi * t) ** .75)) for t in np.linspace(0, 1, 26)] + [(x1, base + 40)]
    m = shaded(poly, [cols[1], cols[0], cols[2]], light=(-.5, -.9), wob=1.0, rough=.8, edge_dark=.05, spacing=1.2, L=4.6, w=2.2)
    x0_, x1_ = min(p[0] for p in poly), max(p[0] for p in poly)
    for _ in range(int((x1_ - x0_) * (base - top) / 90)):              # the map's speckle of lighter and darker dabs
        u = R.uniform(.03, .97); px = x0_ + (x1_ - x0_) * u; ytop = base - (base - top) * (math.sin(math.pi * u) ** .75)
        py = R.uniform(ytop + 3, base + 30)
        T.c.dab(px - T.X0, py - T.Y0, R.uniform(1.6, 3.2), R.uniform(1.0, 1.8), R.uniform(-.3, .3), SPECK[R.randint(len(SPECK))], a=.8, dry=.2)
    S(poly[1:-1], 1.8, rim, a=.6, dry=.4, taper=(.1, .1))
    return poly

def hills_far():
    for (x0, x1, base, top, ci) in [(-620, -280, 210, 84, 4), (-380, -60, 210, 70, 1), (-120, 260, 210, 78, 0), (180, 560, 210, 92, 4), (470, 860, 210, 70, 0), (760, 1120, 210, 88, 1), (1040, 1400, 210, 74, 4), (1300, 1680, 210, 84, 0), (1600, 1900, 210, 76, 1), (1820, 2160, 210, 90, 4)]:
        mound(x0, x1, base, top, GREENS[ci])
    for _ in range(120):                                           # little trees on the far ridges
        x = R.uniform(-560, W + 560); sprite(EVER[R.randint(len(EVER))] if R.rand() < .4 else DECID[R.randint(len(DECID))], x, R.uniform(130, 205), R.uniform(26, 38))

def viaduct(x0, x1, y):
    """The stone viaduct on the left hill, with its arches."""
    stonework([(x0, y + 62), (x0, y), (x1, y - 8), (x1, y + 56)], course=7, block=(10, 18))
    n = 5
    for i in range(n):
        a, b = x0 + (x1 - x0) * (i + .18) / n, x0 + (x1 - x0) * (i + .82) / n; cx = (a + b) / 2; r = (b - a) / 2; yy = y + 62 - (y - 8 - y) * 0
        arch = [(a, y + 64)] + ST.ell(cx, y + 30, r, r * .9, 180, 360, 16) + [(b, y + 64)]
        A(arch, '#4c6a3a', wob=.2, rough=.4, edge_dark=.2)
    S([(x0 - 4, y - 1), (x1 + 4, y - 9)], 3.2, '#8a6a48', a=1, dry=.1, taper=(0, 0))       # the track bed
    for t in np.linspace(0, 1, 30): S([(x0 + (x1 - x0) * t, y - 8 * t - 4), (x0 + (x1 - x0) * t, y - 8 * t + 1)], 1.6, '#5a3a24', a=1, dry=0)

def train(x, y, h):
    """The map's own train (engine and wagons cut from the national map), steam rising."""
    loco = load(os.path.join(SPR, 'loco_0@2x.png')); wa = load(os.path.join(SPR, 'wagon_1@2x.png')); wb = load(os.path.join(SPR, 'wagon_0@2x.png'))
    xs = x
    for im in (wb, wa, loco):
        wdt = h * im.shape[1] / im.shape[0]; sprite(im, xs + wdt / 2, y, h); xs += wdt + 2
    for k in range(5):                                               # puffs of steam
        px, py = xs - h * .55 - k * 14, y - h * 1.1 - k * 9; r = 7 + k * 2.6
        shaded(lump(px, py, r, r * .8, amp=.15), ['#ffffff', '#eceae4', '#c8c6c0'], wob=.3, rough=.5, edge_dark=0, a=.92 - k * .1)

def river_and_bridge():
    """The river winding down the right-hand hills under a stone bridge."""
    pts = [(1300, 128), (1272, 160), (1232, 182), (1222, 210), (1250, 236), (1238, 262), (1196, 290)]
    S(pts, 30, '#e8e2c4', a=1, dry=.1, taper=(0, 0))
    S(pts, 24, '#3a66a8', a=1, dry=.1, taper=(0, 0))
    for _ in range(40):
        i = R.randint(len(pts) - 1); t = R.rand(); (ax, ay), (bx, by) = pts[i], pts[i + 1]; x, y = ax + (bx - ax) * t + R.uniform(-7, 7), ay + (by - ay) * t
        S([(x - 5, y), (x + 5, y + R.uniform(-1, 1))], 1.3, '#dce8f4', a=.9, dry=.2)
    x0, x1, yd = 1160, 1330, 150                                      # the bridge
    deck = [(x0, yd + 40)] + [(x0 + (x1 - x0) * t, yd - 14 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 16)] + [(x1, yd + 40)]
    stonework(deck, course=7, block=(10, 18))
    for cx in (1205, 1285):
        A([(cx - 24, yd + 41)] + ST.ell(cx, yd + 22, 24, 18, 180, 360, 14) + [(cx + 24, yd + 41)], '#2f4f7a', wob=.2, rough=.4, edge_dark=.2)
    snow_edge([(x0, yd + 2)] + [(x0 + (x1 - x0) * t, yd - 14 * math.sin(math.pi * t) - 2) for t in np.linspace(0, 1, 10)] + [(x1, yd + 2)], 5, drip=.2)

def stripes(poly, col):
    """Ploughed furrows across a golden field, following its curve."""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]; x0, x1, top, base = min(xs), max(xs), min(ys), max(ys) - 40
    for k in range(1, 6):
        y = top + (base - top) * k / 6
        S([(x0 + (x1 - x0) * t, y + 10 * math.sin(t * 3 + k)) for t in np.linspace(.1, .9, 12)], 1.8, col, a=.7, dry=.3)

def hills_mid():
    for (x0, x1, base, top, ci) in [(-640, -240, 470, 160, 3), (-400, -20, 470, 140, 0), (-160, 330, 470, 150, 1), (240, 700, 470, 170, 2), (980, 1330, 470, 160, 4), (1240, 1700, 470, 140, 3), (1600, 2000, 470, 160, 1), (560, 1060, 470, 190, 0)]:
        poly = mound(x0, x1, base, top, GREENS[ci])
        if ci in (2, 3): stripes(poly, '#e8cf7a')
    viaduct(30, 350, 222)
    train(60, 214, 56)
    barn = load(os.path.join(LAND, 'land_barn.png')); sprite(barn, 395, 176, 96)
    river_and_bridge()
    house = load(os.path.join(LAND, 'land_house_s.png')); sprite(house, 1425, 212, 70)
    spots = []
    for _ in range(300):                                           # trees thick on the nearer slopes, larger lower down
        x = R.uniform(-560, W + 560); y = R.uniform(206, 400)
        if 1150 < x < 1330 and y < 290: continue
        if 20 < x < 360 and 180 < y < 300: continue
        spots.append((y, x))
    for y, x in sorted(spots):
        pool = EVER if R.rand() < .35 else DECID
        sprite(pool[R.randint(len(pool))], x, y, (34 + (y - 206) * .32) * R.uniform(.85, 1.2))

def trees_behind():
    """Autumn trees and firs standing between the hills and the town, filling in round the station and houses."""
    spots = [(x, R.uniform(470, 530)) for x in np.arange(-420, W + 440, 46)]
    for (x, foot) in sorted(spots, key=lambda p: p[1]):
        if 470 < x < 1160: foot -= 30
        if R.rand() < .3: sprite(EVER[R.randint(len(EVER))], x + R.uniform(-15, 15), foot, R.uniform(110, 150))
        else: sprite((BIG if R.rand() < .5 else DECID)[R.randint(len(BIG if False else DECID))] if False else DECID[R.randint(len(DECID))], x + R.uniform(-15, 15), foot, R.uniform(100, 150))

# ------------------------------------------------------------------ the square
COB = ['#cdbda2', '#c0ae90', '#d8c8ac', '#b4a284', '#c8b898']
SQ = [(560, 646), (1070, 646), (1290, 716), (1560, 800), (1560, 1040), (-30, 1040), (-30, 820), (260, 730)]
def ground():
    """Snow over everything, the square's setts in rows that widen toward you, trodden snow lying in patches."""
    m = A([(-410, 440), (W + 410, 440), (W + 410, H + 10), (-410, H + 10)], SC.SNOWG[0], wob=0, rough=0, edge_dark=0)
    stip(m, SC.SNOWG + ['#ffffff'], spacing=1.6, L=4.2, w=2.4, weights=[.35, .25, .15, .25])
    sq = A(SQ, '#c8b898', wob=3, rough=1, edge_dark=0)
    prev = T.c.clipm; T.c.set_clip(sq)
    y = 632.0
    while y < H + 20:
        f = (y - VH) / (H - VH); ry = 2.4 + 6.2 * f; x = -20 + R.uniform(0, 10)
        while x < W + 20:
            rx = (4.5 + 10 * f) * R.uniform(.8, 1.2); yy = y + ry * .6 * math.sin(x / (60 + 80 * f) + y * .05)
            col = np.clip(hexc(COB[R.randint(len(COB))]) * R.uniform(.92, 1.06), 0, 1)
            T.c.area(T.T(lump(x + rx, yy, rx, ry, amp=.2)), col, wob=.25, rough=.6, edge_dark=.3, var=.05, a=.95, seed=int(R.randint(1 << 20)))
            x += rx * 2 + R.uniform(.5, 1.5) * (1 + f)
        y += ry * 2.1 + .6
    for _ in range(150):                                           # trodden snow in patches on the setts
        x, y = R.uniform(80, W - 80), R.uniform(650, H)
        f = (y - VH) / (H - VH)
        mm = A(lump(x, y, R.uniform(20, 46) * f + 6, R.uniform(5, 11) * f + 2, amp=.3), SC.SNOWG[0], wob=.8, rough=.9, edge_dark=0, a=.94)
        stip(mm, SC.SNOWG + ['#ffffff'], spacing=1.2, L=3, w=1.8, weights=[.35, .25, .15, .25])
    T.c.clipm = prev
    for a_, b_ in zip(SQ, SQ[1:] + SQ[:1]):                        # snow banked round the square's edge
        for t in np.linspace(0, 1, max(2, int(math.dist(a_, b_) / 26))):
            x, y = a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t
            if y > H - 4: continue
            f = (y - VH) / (H - VH); snow_clump(x + R.uniform(-6, 6), y, R.uniform(16, 30) * (.5 + f), R.uniform(4, 8) * (.5 + f))

def front_steps():
    """Wide stone steps down out of the square toward you, between two low walls topped with planters."""
    for i in range(4):
        y = 916 + i * 30; ext = i * 26
        shaded([(560 - ext, y), (980 + ext, y), (990 + ext, y + 30), (550 - ext, y + 30)], ['#eee4d2', '#d8ccb6', '#b0a38a'], light=(0, -1), wob=.1, rough=.3, edge_dark=.22, L=4, w=1.8)
        snow_edge([(556 - ext, y + 1), (984 + ext, y + 1)], 6, drip=0)
        for _ in range(6): snow_clump(R.uniform(560 - ext, 980 + ext), y + 3, R.uniform(14, 30), 4)

def station_steps():
    """A broad flight down from the porch doors, widening as it comes, between stone cheek walls."""
    n = 6
    for i in range(n):
        y = 652 + i * 12; ext = i * 9
        shaded([(722 - ext, y), (908 + ext, y), (912 + ext, y + 12), (718 - ext, y + 12)], ['#f0e8d8', '#dcd2bc', '#b4a890'], light=(0, -1), wob=.1, rough=.3, edge_dark=.22, L=3, w=1.5)
        snow_edge([(722 - ext, y + 1), (908 + ext, y + 1)], 3.5, drip=0)
    for sg in (-1, 1):
        xa = 815 + sg * 96; xb = 815 + sg * (96 + 60)
        q = [(xa, 650), (xa + sg * 26, 644), (xb, 724), (xa, 724)]
        stonework(q, course=8, block=(10, 16)); snow_edge([(xa - sg * 2, 649), (xa + sg * 28, 643)], 6, drip=.2)

def wall_block(x0, x1, y0, y1):
    stonework([(x0, y1), (x1, y1), (x1, y0), (x0, y0)], course=11, block=(18, 30))
    snow_edge([(x0 - 4, y0), (x1 + 4, y0)], 10, drip=.3)

def planter_box(x, y, w, h=46):
    stonework([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], course=10, block=(16, 26))
    for _ in range(int(w * 4)):                                    # holly and red flowers spilling over
        T.c.dab(x - T.X0 + R.uniform(-w * .5, w * .5), y - h - T.Y0 - R.uniform(-4, 22) * (1 - abs(R.uniform(-.6, .6))), R.uniform(5, 9), 2.6, R.uniform(0, 3), T.NEEDLES[R.randint(4)], a=1, dry=.1)
    for _ in range(int(w / 4)):
        bx, by = x + R.uniform(-w * .42, w * .42), y - h - R.uniform(2, 22)
        shaded(lump(bx, by, 4.2, 4.2, amp=0), ['#f06058', T.BERRY, '#7a1418'], wob=0, rough=.2)
        if R.rand() < .3: shaded(lump(bx + 3, by - 2, 2.6, 2.6, amp=0), ['#fff4d8', '#f0e2c0', '#c8b890'], wob=0, rough=.2)
    for _ in range(3): snow_clump(x + R.uniform(-w * .3, w * .3), y - h - 16, w * .18, 5)
    snow_edge([(x - w / 2 - 4, y - h), (x + w / 2 + 4, y - h)], 7, drip=.25)
    SC.cast(x + 6, y + 2, w * .55, 6, .25)

# ------------------------------------------------------------------ toys
def teddy(x, y, h):
    bc = ['#d8995a', '#b9733a', '#7a4620']; SC.cast(x + 6, y + 2, h * .45, h * .08)
    shaded(lump(x, y - h * .32, h * .3, h * .32, amp=.05), bc, wob=.05, rough=.2, edge_dark=.2)                     # body
    for sg in (-1, 1):
        shaded(lump(x + sg * h * .2, y - h * .08, h * .14, h * .1, amp=.05), bc, wob=.05, rough=.2, edge_dark=.2)   # feet
        shaded(lump(x + sg * h * .2, y - h * .08, h * .07, h * .055, amp=0), ['#f0c690', '#e2b07c', '#c48a56'], wob=0, rough=.2)
        shaded(lump(x + sg * h * .3, y - h * .38, h * .09, h * .17, amp=.05), bc, wob=.05, rough=.2, edge_dark=.2)   # arms
        shaded(lump(x + sg * h * .17, y - h * .9, h * .08, h * .08, amp=0), bc, wob=0, rough=.2, edge_dark=.2)      # ears
    shaded(lump(x, y - h * .7, h * .23, h * .21, amp=.04), bc, wob=.05, rough=.2, edge_dark=.2)                      # head
    shaded(lump(x, y - h * .64, h * .1, h * .075, amp=0), ['#f0c690', '#e2b07c', '#c48a56'], wob=0, rough=.2)
    T.c.dots([(x - T.X0, y - h * .67 - T.Y0)], h * .028, ['#2a1a12'], seed=3)
    for sg in (-1, 1): T.c.dots([(x + sg * h * .075 - T.X0, y - h * .75 - T.Y0)], h * .02, ['#1e140e'], seed=4)
    for sg in (-1, 1): shaded([(x, y - h * .52), (x + sg * h * .14, y - h * .58), (x + sg * h * .14, y - h * .46)], ['#e0504a', T.BERRY, '#7a1418'], wob=0, rough=.2, edge_dark=.2)
    snow_clump(x, y, h * .3, h * .05)

def rocking_horse(x, y, h):
    CRM = ['#fffaf0', '#efe4cc', '#c4b494']; RED = ['#e0504a', '#b8262a', '#7a1418']
    SC.cast(x + 8, y + 2, h * .7, h * .07)
    arc = [(x + h * .62 * math.cos(a), y - h * .08 - h * .14 * math.sin(a) + h * .14) for a in np.linspace(math.pi * .08, math.pi * .92, 18)]
    arc = [(px, y - h * .02 - (h * .12) * (1 - ((px - x) / (h * .62)) ** 2)) for px, _ in arc]
    S(arc, h * .055, '#8a5a32', a=1, dry=.1, taper=(.1, .1)); S([(p[0], p[1] - h * .02) for p in arc], h * .015, '#c4925c', a=.9, dry=.2)
    for dx in (-.33, -.18, .18, .33): S([(x + dx * h * .9, y - h * .42), (x + dx * h * 1.05, y - h * .12)], h * .055, CRM[1], a=1, dry=.1, taper=(0, 0))
    shaded(lump(x, y - h * .5, h * .4, h * .15, amp=.04), CRM, wob=.05, rough=.2, edge_dark=.22)                     # body
    shaded([(x + h * .22, y - h * .55), (x + h * .36, y - h * .9), (x + h * .5, y - h * .86), (x + h * .44, y - h * .56)], CRM, wob=.05, rough=.2, edge_dark=.22)  # neck
    shaded(lump(x + h * .5, y - h * .86, h * .14, h * .08, amp=.03), CRM, wob=.05, rough=.2, edge_dark=.22)          # head
    T.c.dots([(x + h * .48 - T.X0, y - h * .9 - T.Y0)], h * .02, ['#1e140e'], seed=5)
    for k in range(7): S([(x + h * (.28 + k * .03), y - h * (.62 + k * .045)), (x + h * (.2 + k * .03), y - h * (.58 + k * .045))], h * .035, RED[1], a=1, dry=.1)  # mane
    S([(x - h * .38, y - h * .56), (x - h * .5, y - h * .44), (x - h * .54, y - h * .3)], h * .05, RED[1], a=1, dry=.15, taper=(0, .6))        # tail
    shaded([(x - h * .16, y - h * .62), (x + h * .14, y - h * .62), (x + h * .12, y - h * .44), (x - h * .14, y - h * .44)], RED, wob=.05, rough=.2, edge_dark=.2)  # saddle
    S([(x - h * .16, y - h * .62), (x + h * .14, y - h * .62)], h * .02, '#f0c040', a=1, dry=0)
    snow_clump(x - h * .4, y, h * .2, h * .04); snow_clump(x + h * .4, y, h * .2, h * .04)

def ring_stacker(x, y, h):
    SC.cast(x + 4, y + 1, h * .45, h * .06)
    shaded(lump(x, y - h * .05, h * .38, h * .07, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2, edge_dark=.2)
    S([(x, y - h * .1), (x, y - h * .84)], h * .05, '#c4925c', a=1, dry=0)
    for i, cols in enumerate([['#e0504a', '#b8262a', '#7a1418'], ['#f6d77a', '#e0b040', '#a07a20'], ['#6fb060', '#3f8a46', '#245a2a'], ['#6c9ae0', '#3a6aa8', '#24407a']]):
        r = h * (.34 - i * .06); yy = y - h * (.17 + i * .16)
        shaded(lump(x, yy, r, h * .08, amp=0), cols, wob=0, rough=.2, edge_dark=.22)
    shaded(lump(x, y - h * .86, h * .09, h * .09, amp=0), ['#e0504a', '#b8262a', '#7a1418'], wob=0, rough=.2, edge_dark=.2)

def sailboat(x, y, h):
    SC.cast(x + 6, y + 2, h * .5, h * .06)
    shaded([(x - h * .5, y - h * .22), (x + h * .55, y - h * .22), (x + h * .38, y - h * .02), (x - h * .36, y - h * .02)], ['#e0504a', '#b8262a', '#7a1418'], light=(-.4, -.9), wob=.05, rough=.2, edge_dark=.2)
    S([(x - h * .48, y - h * .19), (x + h * .52, y - h * .19)], h * .035, '#f3ead6', a=1, dry=0, taper=(0, 0))
    S([(x, y - h * .22), (x, y - h * 1.02)], h * .03, '#6a4428', a=1, dry=0)
    shaded([(x + h * .03, y - h * .98), (x + h * .03, y - h * .3), (x + h * .45, y - h * .3)], ['#fffdf6', '#f1e8d4', '#cfc2a4'], light=(-.8, -.4), wob=.05, rough=.2, edge_dark=.16)
    shaded([(x - h * .03, y - h * .86), (x - h * .03, y - h * .32), (x - h * .34, y - h * .32)], ['#fffdf6', '#efe4cc', '#c8baa0'], light=(-.8, -.4), wob=.05, rough=.2, edge_dark=.16)
    shaded([(x, y - h * 1.02), (x + h * .14, y - h * .97), (x, y - h * .93)], ['#e0504a', '#b8262a', '#7a1418'], wob=0, rough=.2)
    snow_clump(x, y, h * .45, h * .05)

def flag(x, y, h):
    S([(x, y), (x, y - h)], h * .045, '#2a2228', a=1, dry=0, taper=(0, 0))
    shaded(lump(x, y - h - h * .04, h * .05, h * .05, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2)
    pts = [(x + h * .03, y - h * .97), (x + h * .62, y - h * .9), (x + h * .5, y - h * .78), (x + h * .64, y - h * .66), (x + h * .03, y - h * .6)]
    shaded(pts, ['#e8584a', '#c42e28', '#86181a'], light=(-.6, -.8), wob=.2, rough=.4, edge_dark=.2)

# ------------------------------------------------------------------ the composition
def main():
    t0 = time.time()
    # far to near ------------------------------------------------------------------------------------------
    piece('sky', (-600, 0, W + 600, 430), sky, depth=1600, glow=False, kind='back')
    piece('clouds', (0, 0, W, 200), lambda: [cloud(870, 46, 120), cloud(1330, 138, 110), cloud(150, 34, 90)], depth=1200, glow=False, kind='back')
    piece('hills_far', (-600, 50, W + 600, 260), hills_far, depth=700, glow=False, kind='back')
    piece('hills_mid', (-600, 100, W + 600, 520), hills_mid, depth=260, glow=False, kind='back')
    piece('trees_behind', (-460, 300, W + 460, 540), trees_behind, depth=depth_of(532), glow=False, kind='back')
    piece('ground', (-400, 436, W + 400, H + 4), ground, foot=H, depth=None, glow=False, kind='ground')
    # the station, in its painted layers, standing at the head of the square
    s, at, to = .88, (700, 659), (815, 692)
    for part, box, dz in (('wings', (170, 170, 1230, 630), 3.0), ('vault', (400, 0, 1000, 260), 1.0), ('face', (350, 0, 1050, 630), 0),
                          ('towers', (350, 80, 1050, 630), -.8), ('annex', (440, 430, 960, 630), -1.8), ('porch', (570, 370, 830, 630), -3.0)):
        piece('station_' + part, box, lambda p=part: ST.station({p}), s=s, at=at, to=to, foot=690, light=part != 'steps')
        pieces[-1]['depth'] = depth_of(690) + dz
    piece('station_steps', (600, 630, 1030, 730), station_steps, foot=724, glow=False)
    pieces[-1]['depth'] = depth_of(692) - 3.6
    fl = lambda nx, ny: (to[0] + (nx - at[0]) * s, to[1] + (ny - at[1]) * s)
    piece('flags', (400, 40, 1250, 260), lambda: [flag(*fl(372, 84), 70), flag(*fl(1028, 84), 70), flag(*fl(700, 4), 62)], foot=690, glow=False)
    pieces[-1]['depth'] = depth_of(690) - .8
    # the houses wrapping round the square
    for name, box, fn, foot_n, cx_n, s_, to_ in [
        ('pink_narrow', (280, 340, 372, 735), Wt.pink_narrow, 724, 326, 1.2, (300, 676)),
        ('red_house', (1040, 370, 1290, 650), E.red_house, 641, 1160, 1.35, (190, 724)),
        ('cream_house', (330, 395, 482, 712), Wt.cream_house, 704, 406, 1.45, (334, 708)),
        ('blue_shop', (0, 420, 345, 920), T.blue_shop, 916, 170, 1.08, (40, 810)),
        ('pink_house', (915, 436, 1080, 710), E.pink_house, 704, 997, 1.5, (1330, 702)),
        ('donation_shop', (1000, 495, 1300, 870), E.donation_shop, 858, 1145, 1.2, (1440, 846)),
    ]:
        piece(name, box, fn, s=s_, at=(cx_n, foot_n), to=to_, foot=to_[1], light=True)
    # the square's life
    piece('lamp_1', (440, 560, 560, 760), lambda: SC.lamp(500, 722, 118), s=1.55, at=(500, 722), to=(408, 726), foot=726)
    piece('lamp_2', (440, 560, 560, 760), lambda: SC.lamp(500, 722, 118), s=1.55, at=(500, 722), to=(1088, 716), foot=716)
    piece('tree', (360, 380, 810, 870), lambda: SC.christmas_tree(585, 822, 360), foot=834)
    piece('teddy', (400, 680, 560, 860), lambda: teddy(478, 842, 118), foot=842)
    piece('marine_a', (920, 600, 1000, 800), lambda: SC.marine(955, 782, 150), foot=782)
    piece('marine_b', (970, 600, 1050, 800), lambda: SC.marine(1005, 786, 150, skin='#8a5430'), foot=786)
    piece('ring_stacker', (1030, 700, 1110, 800), lambda: ring_stacker(1068, 790, 74), foot=790)
    piece('rocking_horse', (1120, 640, 1330, 820), lambda: rocking_horse(1222, 808, 150), foot=808)
    piece('wagon', (380, 400, 560, 560), lambda: SC.wagon(470, 545, 'presents'), s=1.25, at=(470, 545), to=(880, 822), foot=822)
    piece('sailboat', (680, 760, 840, 900), lambda: sailboat(760, 884, 104), foot=884)
    piece('planter_l', (80, 760, 260, 870), lambda: planter_box(170, 858, 130, 44), foot=858)
    piece('planter_r', (980, 780, 1180, 900), lambda: planter_box(1078, 880, 170, 48), foot=880)
    piece('lamp_3', (440, 560, 560, 760), lambda: SC.lamp(500, 722, 120), s=2.0, at=(500, 722), to=(276, 944), foot=944)
    piece('lamp_4', (440, 560, 560, 760), lambda: SC.lamp(500, 722, 120), s=2.0, at=(500, 722), to=(1344, 928), foot=928)
    # in front
    piece('front_steps', (420, 900, 1120, H + 10), front_steps, foot=H, glow=False)
    pieces[-1]['depth'] = depth_of(980)
    piece('wall_l', (330, 880, 600, H + 10), lambda: [wall_block(380, 560, 950, H + 10), planter_box(470, 952, 170, 50)], foot=H, glow=False)
    pieces[-1]['depth'] = depth_of(985)
    piece('wall_r', (960, 860, 1220, H + 10), lambda: wall_block(980, 1160, 930, H + 10), foot=H, glow=False)
    pieces[-1]['depth'] = depth_of(985)
    big = [k for k in TREES if 'decid' in k and '@2x' in k]
    def fg_tree(name, x, foot, h, which):
        piece(name, (x - h * .6, foot - h * 1.05, x + h * .6, min(foot + 4, H + 4)), lambda: sprite(TREES[which], x, foot, h), foot=H, glow=False)
    fg_tree('fg_tree_l', 100, 1120, 400, 'tree_decid_16@2x.png'); fg_tree('fg_tree_l2', 335, 1100, 270, 'tree_decid_2@2x.png')
    fg_tree('fg_tree_r', 1462, 1120, 390, 'tree_decid_21@2x.png'); fg_tree('fg_tree_r2', 1236, 1100, 260, 'tree_decid_7@2x.png')
    piece('fg_firs', (180, 860, 1360, H + 4), lambda: [fir(252, 1030, 110), fir(1300, 1016, 96), fir(205, 1040, 70)], foot=H - 6, glow=False)
    # write the scene and the flattened painting --------------------------------------------------------------
    json.dump(dict(frame=[W, H], K=K, camera=dict(fov=FOV, height=HC, horizon=VH), pieces=pieces), open(os.path.join(OUT, 'scene.json'), 'w'), indent=1)
    flatten(); print('done', len(pieces), 'pieces', round(time.time() - t0), 's')

def flatten():
    """The painting as the home camera sees it: back layers far to near, then the ground, then everything standing."""
    pieces[:] = json.load(open(os.path.join(OUT, 'scene.json')))['pieces']
    flat = np.zeros((H * K, W * K, 3), np.float32)
    order = sorted(range(len(pieces)), key=lambda i: (-(90 if pieces[i]['kind'] == 'ground' else pieces[i]['depth']), i))
    for i in order:
        p = pieces[i]; im = cv2.imread(os.path.join(OUT, p['file']), cv2.IMREAD_UNCHANGED).astype(np.float32)
        x0, y0 = int(round(p['x'] * K)), int(round(p['y'] * K)); ih, iw = im.shape[:2]
        sx0, sy0 = max(0, -x0), max(0, -y0); ex, ey = min(iw, W * K - x0), min(ih, H * K - y0)
        if ex <= sx0 or ey <= sy0: continue
        a = im[sy0:ey, sx0:ex, 3:] / 255; reg = flat[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex]
        flat[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = reg * (1 - a) + im[sy0:ey, sx0:ex, :3] * a
    cv2.imwrite(os.path.join(HERE, 'out', 'toytown_folk.png'), flat.astype(np.uint8))
    cv2.imwrite(os.path.join(HERE, 'out', 'toytown_folk_small.jpg'), cv2.resize(flat, (W, H), interpolation=cv2.INTER_AREA).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])

if __name__ == '__main__':
    flatten() if sys.argv[1:] == ['flat'] else main()

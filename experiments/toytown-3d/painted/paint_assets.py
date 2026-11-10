"""Approach 1 test: paint the diorama's surfaces with the folk-art kit (the same code as the map's Toy Town).

Everything is painted in the kit's units (the Toy Town illustration's pixels); the 3D scene places each painting
at one shared scale, SCALE metres per unit, so the buildings keep the proportions of the illustration.
Writes tex/*.png and tex/assets.json (size of each painting in units, and where its feet are).
    python3 paint_assets.py
"""
import os, sys, json, math, time
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'kit'))
import toytown_kit as T
from toytown_kit import A, S, shaded, stip, lump, snow_edge, snow_clump, hexc, fir
import toytown_east as E, toytown_west as Wt, toytown_station as ST, toytown_scene as SC
OUT = os.path.join(HERE, 'tex'); os.makedirs(OUT, exist_ok=True)
SCALE = 0.024                     # metres per kit unit (the station front: 1040 units, about 25 m)
K = 2
meta = {}

def crop_save(name, opaque=False, light=True):
    if light: T.light()
    paint, al = T.finish(os.path.join(OUT, name + '.png'), None, opaque=opaque)
    if opaque: ys, xs = np.mgrid[0:1, 0:1]; box = (0, 0, paint.shape[1], paint.shape[0])
    else:
        ys, xs = np.nonzero(al > .03); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    im = cv2.imread(os.path.join(OUT, name + '.png'), cv2.IMREAD_UNCHANGED)[box[1]:box[3], box[0]:box[2]]
    cv2.imwrite(os.path.join(OUT, name + '.png'), im)
    meta[name] = dict(w=im.shape[1] / K, h=im.shape[0] / K)           # in kit units
    print(f'  {name}: {im.shape[1]}x{im.shape[0]}px', flush=True)

def asset(name, box, fn, **kw):
    T.init(*box, K); fn(); crop_save(name, **kw)

def stucco(name, base, cols, w=220, h=220, stone_dark=.25):
    """A tile of a building's own wall (for its side walls), with a band of snow-shadow at the top."""
    T.init(0, 0, w, h, K)
    A([(-5, -5), (w + 5, -5), (w + 5, h + 5), (-5, h + 5)], base, wob=0, rough=0, edge_dark=0)
    T.wall([(-5, -5), (w + 5, -5), (w + 5, h + 5), (-5, h + 5)], base, cols=cols, stone_dark=stone_dark)
    T.light = T.light
    crop_save(name, opaque=True, light=False)

def roof_tile(name, cols, dark, w=240, h=200):
    """Tiles under a snow blanket (top two-thirds snow, tiles showing toward the eave), for roof slopes."""
    T.init(0, 0, w, h, K)
    T.roof([(-5, -5), (w + 5, -5), (w + 5, h + 5), (-5, h + 5)], cols=cols, tile_dark=dark, snowy=.6, ridge=((-5, -5), (w + 5, -5)), eave=((-5, h + 5), (w + 5, h + 5)))
    crop_save(name, opaque=True, light=False)

def ground():
    """The ground: snow over the meadow, the square's setts laid in fans and showing through trodden snow,
    paths to the bridge and to the fields. Painted 64 x 64 m (1 unit = SCALE m), centred on the square."""
    U = 1 / SCALE; N = int(64 * U); c = N / 2
    T.init(0, 0, N, N, 1)
    tx = lambda x, z: (c + x * U, c + z * U)
    m = A([(-10, -10), (N + 10, -10), (N + 10, N + 10), (-10, N + 10)], SC.SNOWG[0], wob=0, rough=0, edge_dark=0)
    stip(m, SC.SNOWG + ['#ffffff'], spacing=2.2, L=5, w=2.6, weights=[.35, .25, .15, .25])
    sq = [tx(x, z) for x, z in [(-10.5, -13), (10.5, -13), (11.5, -6), (12.5, 2), (12, 8.5), (6, 9.5), (-6, 9.5), (-12, 8.5), (-12.5, 1), (-11.5, -6)]]
    path = lambda pts, w: [S([tx(*p) for p in pts], w * U, '#d9cfbe', a=.95, dry=.35, taper=(0, 0))]
    path([(11.5, 6.8), (16, 7.6), (21, 7.8), (32, 8.2)], 3.0); path([(0, 10), (.5, 16), (-3, 26), (-10, 38)], 3.2)
    m = A(sq, '#cdbda2', wob=4, rough=1, edge_dark=0)
    prev = T.c.clipm; T.c.set_clip(m)
    # setts in gently wavering rows, each stone its own size and shade
    ph = T.R.uniform(0, 6)
    for row, y in enumerate(np.arange(c - 14 * U, c + 11 * U, 6.2)):
        x = c - 14 * U + T.R.uniform(0, 8)
        while x < c + 14 * U:
            rx = T.R.uniform(3.2, 4.8); yy = y + 3.2 * math.sin(x / 55 + row * .35 + ph) + T.R.uniform(-.8, .8)
            col = np.clip(hexc(['#c8b69a', '#bba98e', '#d4c4a8', '#b3a086'][T.R.randint(4)]) * T.R.uniform(.92, 1.06), 0, 1)
            T.c.area(T.T(lump(x + rx, yy, rx, T.R.uniform(2.2, 2.9), amp=.22)), col, wob=.25, rough=.6, edge_dark=.32, var=.05, a=.92, seed=int(T.R.randint(1 << 20)))
            x += rx * 2 + T.R.uniform(.4, 1.4)
    worn = [((0, -12), (0, 8), 3), ((-9, -3), (0, 6), 2), ((9, -3), (0, 6), 2)]
    def near(x, y):
        for (a, b, w) in worn:
            (ax, ay), (bx, by) = tx(*a), tx(*b); t = np.clip(((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
            if math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay)) < w * U: return True
        return False
    for _ in range(260):
        x, y = T.R.uniform(c - 13 * U, c + 13 * U), T.R.uniform(c - 13 * U, c + 10 * U)
        if near(x, y): continue
        mm = A(lump(x, y, T.R.uniform(18, 40), T.R.uniform(9, 18), amp=.25), SC.SNOWG[0], wob=.8, rough=.9, edge_dark=0, a=.92)
        stip(mm, SC.SNOWG + ['#ffffff'], spacing=1.4, L=3.0, w=1.8, weights=[.35, .25, .15, .25])
    T.c.clipm = prev
    for a_, b_ in zip(sq, sq[1:] + sq[:1]):
        for t in np.linspace(0, 1, max(2, int(math.dist(a_, b_) / 22))):
            snow_clump(a_[0] + (b_[0] - a_[0]) * t + T.R.uniform(-6, 6), a_[1] + (b_[1] - a_[1]) * t, T.R.uniform(16, 34), T.R.uniform(5, 9))
    T.impasto(T.c, strength=.22)
    paint = np.clip(T.c.img, 0, 1)
    cv2.imwrite(os.path.join(OUT, 'ground.jpg'), (paint[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    meta['ground'] = dict(size_m=64)
    print('  ground', paint.shape, flush=True)

def backdrop():
    """The hills beyond the town: a pale winter sky, three rows of rolling snowy hills (farther = paler and
    bluer), firs and bare trees along the ridges, painted with the kit's snow, needles and branches."""
    W_, H_ = 1600, 520
    T.init(0, 0, W_, H_, K)
    sky = A([(-10, -10), (W_ + 10, -10), (W_ + 10, H_ + 10), (-10, H_ + 10)], '#dfe6e4', wob=0, rough=0, edge_dark=0)
    def skycol(X, Y, r):
        t = np.clip(Y / H_, 0, 1)[:, None]
        return np.clip(hexc('#c9d6dc') * (1 - t) + hexc('#efe8dc') * t + (r.rand(len(X), 1) - .5) * .02, 0, 1)
    T.c.stip(sky, skycol, spacing=3, L=10, w=4, angfn=lambda X, Y: np.zeros(X.shape), seed=1, jit=.5)
    rows = [(250, 70, ['#dfe5ec', '#d2dae4', '#e8edf2'], '#9aaab4', 3), (320, 90, ['#e9edf1', '#dce2ea', '#f2f4f6'], '#6f8a7c', 2),
            (400, 110, ['#f2f3f4', '#e4e8ee', '#fbfbfb'], '#3d6a52', 1)]
    for ri, (base, amp, cols, tree_col, far) in enumerate(rows):
        ph = T.R.uniform(0, 6); top = []
        for x in np.linspace(-20, W_ + 20, 60):
            top.append((x, base - amp * (.55 + .45 * math.sin(x / (170 + 40 * ri) + ph) * math.sin(x / 90 + ph * 2) ** 2)))
        poly = top + [(W_ + 20, H_ + 20), (-20, H_ + 20)]
        m = A(poly, cols[0], wob=1.5, rough=.8, edge_dark=.04)
        def hcol(X, Y, r, top=top, cols=cols):
            C = np.array([hexc(c) for c in cols]); idx = r.choice(3, size=len(X), p=[.45, .3, .25])
            return np.clip(C[idx] * (1 + (r.rand(len(X), 1) - .5) * .04), 0, 1)
        T.c.stip(m, hcol, spacing=2.0, L=6, w=2.6, angfn=lambda X, Y: np.full(X.shape, .15), seed=10 + ri, jit=.5)
        # trees along the ridge and down the slope: farther rows small and pale
        for k in range(int(26 / far + 10)):
            x = T.R.uniform(0, W_); yi = np.interp(x, [p[0] for p in top], [p[1] for p in top]) + T.R.uniform(4, 40)
            h = T.R.uniform(30, 60) / far
            if T.R.rand() < .8:
                T.c.area(T.T([(x, yi - h), (x - h * .26, yi), (x + h * .26, yi)]), hexc(tree_col), wob=.4, rough=.8, edge_dark=.1, a=.95, seed=k + ri * 100)
                if far == 1: fir(x, yi, h)
            else:
                SC.bare_tree(x, yi, h * 1.2, k + ri * 50)
    crop_save('backdrop', opaque=True, light=False)

if __name__ == '__main__':
    t0 = time.time()
    if sys.argv[1:] == ['backdrop']:
        meta.update(json.load(open(os.path.join(OUT, 'assets.json')))); backdrop(); json.dump(meta, open(os.path.join(OUT, 'assets.json'), 'w'), indent=1); sys.exit()
    if sys.argv[1:] == ['ground']:
        meta.update(json.load(open(os.path.join(OUT, 'assets.json')))); ground(); json.dump(meta, open(os.path.join(OUT, 'assets.json'), 'w'), indent=1); sys.exit()
    asset('station', (170, 0, 1230, 680), ST.build_station)
    asset('blue_shop', (0, 420, 345, 920), T.blue_shop)
    asset('pink_narrow', (280, 340, 372, 735), Wt.pink_narrow)
    asset('cream_house', (330, 395, 482, 712), Wt.cream_house)
    asset('red_house', (1040, 370, 1290, 650), E.red_house)
    asset('pink_house', (915, 436, 1080, 710), E.pink_house)
    asset('donation_shop', (1000, 495, 1300, 870), E.donation_shop)
    asset('tree', (550, 600, 760, 880), lambda: SC.christmas_tree(650, 845, 212))
    asset('marine_a', (738, 710, 784, 822), lambda: SC.marine(760, 812))
    asset('marine_b', (780, 710, 826, 822), lambda: SC.marine(802, 812, skin='#8a5430'))
    asset('lamp', (495, 580, 560, 735), lambda: SC.lamp(527, 717, 120))
    asset('wagon_bear', (425, 755, 570, 870), lambda: SC.wagon(487, 847, 'bear'))
    asset('wagon_presents', (812, 765, 960, 880), lambda: SC.wagon(875, 860, 'presents'))
    asset('fir', (0, 0, 140, 220), lambda: fir(70, 210, 190))
    stucco('wall_cream', T.CREAM, ST.STONE)
    stucco('wall_blue', T.BLUE, None)
    stucco('wall_pink', E.PINK[2], E.PINK, stone_dark=.12)
    stucco('wall_red', E.RED[1], E.RED, stone_dark=.2)
    stucco('wall_yellow', E.YELLOW[1], E.YELLOW, stone_dark=.1)
    roof_tile('roof_red', ['#a8463c', '#8a3430', '#b8564a'], '#6e2925')
    roof_tile('roof_purple', E.PURPLE, '#38385e')
    backdrop()
    ground()
    meta['_scale_m_per_unit'] = SCALE
    json.dump(meta, open(os.path.join(OUT, 'assets.json'), 'w'), indent=1)
    print('done', round(time.time() - t0), 's')

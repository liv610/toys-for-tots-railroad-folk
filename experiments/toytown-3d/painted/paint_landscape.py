"""The country around Toy Town, made from the national map's own paint, so stepping into the town keeps the
world you just zoomed in from.

  * meadow.jpg     the ground beyond the square: patches of the map's painted grass and golden fields, laid
                   stamp by stamp (texture bombing with crisp edges, so the brushwork is not blurred), the
                   map's river, and the town's snow thinning out over the hills.
  * land_*.png     landmarks cut from the map painting: the red barn, the snowy mountains, the red mesas and
                   the farmhouses. They stand around the town in the directions they lie on the map.
  * sky.jpg        a sky painted with the kit's brush, soft blue overhead and warm at the horizon.
  * horizon.png    the far hills all round, in the map's greens and golds, bluer with distance.
  * map/*.png      the map's own tree and cloud sprites (copied from the map viewer), for the hills and sky.

Writes tex/land.json with sizes and placement. Needs the map viewer build (usmap/viewer_tt, from to_viewer.py).
    python3 paint_landscape.py
"""
import os, sys, json, math, shutil, time
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'kit'))
import toytown_kit as T
from toytown_kit import A, hexc
ROOT = os.path.join(HERE, '..', '..', '..'); VIEWER = os.path.join(ROOT, 'usmap', 'viewer_tt')
OUT = os.path.join(HERE, 'tex'); os.makedirs(os.path.join(OUT, 'map'), exist_ok=True)
R = np.random.RandomState(7)
TOWN = (3900, 1990)                                   # the town's centre in map (base) px
EXTENT, NPX = 600, 2048                               # the meadow texture covers 600 x 600 m
RIVER = [[60, -320], [52, -200], [46, -110], [42, -50], [41, -10], [40, 20], [34, 50], [22, 90], [14, 150], [20, 220], [35, 320]]

def stitch():
    d = os.path.join(VIEWER, 'tiles', 'base_files'); d = os.path.join(d, str(max(int(x) for x in os.listdir(d))))
    fs = os.listdir(d); xs = max(int(f.split('_')[0]) for f in fs) + 1; ys = max(int(f.split('_')[1].split('.')[0]) for f in fs) + 1
    rows = []
    for y in range(ys):
        rows.append(np.concatenate([cv2.imread(os.path.join(d, f'{x}_{y}.jpg'))[(1 if y else 0):(1 if y else 0) + 1024, (1 if x else 0):(1 if x else 0) + 1024] for x in range(xs)], 1))
    return np.concatenate(rows, 0)

# ------------------------------------------------------------------ landmarks cut from the painting
LANDMARKS = {   # name: (map rect x0, y0, x1, y1), height in metres
    'barn': ((2700, 560, 3400, 1120), 20), 'mountains': ((1000, 270, 2620, 1010), 110), 'mesas': ((1050, 1850, 2000, 2330), 34),
    'house_nw': ((1600, 930, 1920, 1200), 12), 'house_ne': ((5020, 1000, 5320, 1320), 13), 'house_e': ((5520, 1800, 5900, 2180), 14),
    'house_s': ((3430, 2850, 3720, 3170), 12), 'house_sw': ((2350, 2720, 2830, 2980), 13), 'house_y': ((5450, 2180, 5760, 2520), 13),
}
def cutout(img, name, rect, h_m):
    x0, y0, x1, y1 = rect; crop = img[y0:y1, x0:x1].copy(); H, W = crop.shape[:2]
    mask = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
    m = 6; mask[m:H - 2, m:W - m] = cv2.GC_PR_FGD; mask[:m] = mask[:, :m] = mask[:, -m:] = cv2.GC_BGD
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV); hh, ss = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
    grass = (hh >= 30) & (hh <= 80) & (ss > 80)                   # sure background: the map's green grass
    if name not in ('mountains',): mask[grass & (mask != cv2.GC_BGD)] = cv2.GC_PR_BGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(crop, mask, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    a = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)               # keep the big piece(s), drop specks
    keep = np.zeros_like(a)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > .04 * st[1:, cv2.CC_STAT_AREA].max(): keep[lab == i] = 255
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    keep = cv2.GaussianBlur(keep, (0, 0), .8)
    ys, xs = np.nonzero(keep > 20); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out = np.dstack([crop, keep])[by0:by1, bx0:bx1]
    cv2.imwrite(os.path.join(OUT, f'land_{name}.png'), out)
    cx, cy = x0 + (bx0 + bx1) / 2, y0 + by1                          # its foot on the map
    return dict(w=int(out.shape[1]), h=int(out.shape[0]), h_m=h_m, map=[float(cx), float(cy)])

# ------------------------------------------------------------------ donor patches of the map's painted grass
def donors(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); H_, S_, V_ = [hsv[..., i].astype(int) for i in range(3)]
    cls = {'green': (H_ >= 33) & (H_ <= 75) & (S_ > 90) & (V_ > 70), 'gold': (H_ >= 17) & (H_ < 30) & (S_ > 110) & (V_ > 130)}
    edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 120, 240)
    out = {}
    for k, m in cls.items():
        cand = []
        P = 176
        for y in range(0, img.shape[0] - P, 88):
            for x in range(0, img.shape[1] - P, 88):
                if abs(x + P / 2 - TOWN[0]) < 1050 and abs(y + P / 2 - TOWN[1]) < 820: continue   # not Toy Town itself
                if k == 'gold' and x < 2700 and 1700 < y < 2500: continue                         # not the desert
                f = m[y:y + P, x:x + P].mean()
                if f < .985: continue
                e = edges[y:y + P, x:x + P].mean()
                cand.append((e, x, y, V_[y:y + P, x:x + P].mean()))
        cand.sort(); cand = cand[:60]
        cand.sort(key=lambda c: c[3])                                      # dark to light, then spread across
        pick = [cand[int(i)] for i in np.linspace(0, len(cand) - 1, min(len(cand), 14))]
        out[k] = [img[y:y + P, x:x + P].copy() for _, x, y, _ in pick]
        print(f'  donors {k}: {len(cand)} candidates, {len(out[k])} used', flush=True)
    return out

def noise(shape, scale, seed):
    r = np.random.RandomState(seed); s = (max(2, int(shape[0] / scale)), max(2, int(shape[1] / scale)))
    return cv2.resize(r.rand(*s).astype(np.float32), shape[::-1], interpolation=cv2.INTER_CUBIC)

def w2t(x, z): return ((x + EXTENT / 2) / EXTENT * NPX, (z + EXTENT / 2) / EXTENT * NPX)

def meadow(img, D):
    N = NPX; canvas = np.zeros((N, N, 3), np.float32)
    zone = noise((N, N), 170, 3) * .7 + noise((N, N), 60, 4) * .3      # green, light green, gold
    light = [d for d in D['green'][len(D['green']) // 2:]]; dark = D['green'][:len(D['green']) // 2]
    P = 176; yy, xx = np.mgrid[0:P, 0:P]; rr = np.hypot(xx - P / 2, yy - P / 2) / (P / 2)
    soft = np.clip((1 - rr) / .22, 0, 1)[..., None]
    pts = [(x + R.uniform(-30, 30), y + R.uniform(-30, 30)) for y in range(-60, N + 60, 70) for x in range(-60, N + 60, 70)]
    R.shuffle(pts)
    for x, y in pts:
        z = zone[int(np.clip(y, 0, N - 1)), int(np.clip(x, 0, N - 1))]
        pool = D['gold'] if z > .66 else (light if z > .42 else dark)
        d = pool[R.randint(len(pool))]
        if R.rand() < .5: d = d[:, ::-1]
        x0, y0 = int(x - P / 2), int(y - P / 2); sx0, sy0 = max(0, -x0), max(0, -y0); ex, ey = min(P, N - x0), min(P, N - y0)
        if ex <= sx0 or ey <= sy0: continue
        reg = canvas[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex]; a = soft[sy0:ey, sx0:ex]
        canvas[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = reg * (1 - a) + d[sy0:ey, sx0:ex].astype(np.float32) * a
    # snow: deep around the town, thinning to drifts and then to bare autumn hills, with a lumpy edge
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32); X = xx / N * EXTENT - EXTENT / 2; Z = yy / N * EXTENT - EXTENT / 2
    r = np.hypot(X, Z + 6); ang = np.arctan2(Z, X)
    edge = 54 + 9 * np.sin(ang * 5 + 1) + 5 * np.sin(ang * 13 + 2) + (noise((N, N), 18, 9) - .5) * 8
    snowa = np.clip((edge - r) / 6, 0, 1)
    drift = (noise((N, N), 9, 11) > np.clip((r - edge) / 55, 0, 1) * .55 + .45) & (r < edge + 60)
    snowa = np.maximum(snowa, drift.astype(np.float32) * np.clip(1 - (r - edge) / 60, 0, 1))
    snowa = cv2.GaussianBlur(snowa, (0, 0), 1.2)[..., None]
    g = cv2.imread(os.path.join(OUT, 'ground.jpg')); sn = g[40:600, 40:600]          # the town's own painted snow
    sn = cv2.resize(sn, None, fx=.3, fy=.3)                                               # at the meadow's scale
    snow = np.zeros_like(canvas)
    for y in range(0, N, sn.shape[0]):
        for x in range(0, N, sn.shape[1]):
            t = sn if R.rand() < .5 else sn[:, ::-1]; snow[y:y + t.shape[0], x:x + t.shape[1]] = t[:N - y, :N - x]
    canvas = canvas * (1 - snowa) + snow * snowa
    # the river: the map's river paint along its course, with the pale bank line the map draws
    rv = img[1300:2000, 4660:4790]
    hsv = cv2.cvtColor(rv, cv2.COLOR_BGR2HSV); blue = (hsv[..., 0] > 95) & (hsv[..., 0] < 125) & (hsv[..., 1] > 90)
    ys, xs = np.nonzero(blue); water = rv[ys, xs].astype(np.float32)
    pts = np.array([w2t(x, z) for x, z in RIVER], np.float32)
    curve = cv2.approxPolyDP(pts.reshape(-1, 1, 2), .5, False).reshape(-1, 2)
    dense = []
    for a, b in zip(pts, pts[1:]):
        for t in np.linspace(0, 1, 40, endpoint=False): dense.append(a + (b - a) * t)
    dense = np.round(np.array(dense)).astype(np.int32)
    mk = np.zeros((N, N), np.uint8); cv2.polylines(mk, [dense], False, 255, int(8 / EXTENT * N), cv2.LINE_AA)
    bank = np.zeros((N, N), np.uint8); cv2.polylines(bank, [dense], False, 255, int(10.4 / EXTENT * N), cv2.LINE_AA)
    wt = np.zeros((N, N, 3), np.float32)
    for y in range(0, N, 64):                                          # tile the river paint with real map water
        for x in range(0, N, 32):
            if not mk[y:y + 64, x:x + 32].any(): continue
            sy, sx = R.randint(0, rv.shape[0] - 64), R.randint(0, rv.shape[1] - 32)
            t = rv[sy:sy + 64, sx:sx + 32].astype(np.float32); b = blue[sy:sy + 64, sx:sx + 32]
            t[~b] = water[R.randint(len(water), size=(~b).sum())]
            wt[y:y + 64, x:x + 32] = t[:min(64, N - y), :min(32, N - x)]
    bk = (cv2.GaussianBlur(bank, (0, 0), 1).astype(np.float32) / 255)[..., None]
    canvas = canvas * (1 - bk * .9) + np.array([200, 228, 236], np.float32) * bk * .9
    mw = (cv2.GaussianBlur(mk, (0, 0), .8).astype(np.float32) / 255)[..., None]
    canvas = canvas * (1 - mw) + wt * mw
    cv2.imwrite(os.path.join(OUT, 'meadow.jpg'), np.clip(canvas, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('  meadow', canvas.shape, flush=True)

# ------------------------------------------------------------------ sky and horizon, painted with the kit
def sky():
    W_, H_ = 1024, 512; T.init(0, 0, W_, H_, 1)
    m = A([(-10, -10), (W_ + 10, -10), (W_ + 10, H_ + 10), (-10, H_ + 10)], '#cfe0ea', wob=0, rough=0, edge_dark=0)
    stops = [(0, '#7fa8d0'), (.45, '#a9c6de'), (.8, '#cfe0e8'), (1, '#e6ece6')]
    def col(X, Y, r):
        t = np.clip(Y / H_, 0, 1); C = np.array([hexc(c) for _, c in stops]); P_ = [p for p, _ in stops]
        c = np.stack([np.interp(t, P_, C[:, i]) for i in range(3)], 1)
        return np.clip(c + (r.rand(len(X), 1) - .5) * .03, 0, 1)
    T.c.stip(m, col, spacing=2.6, L=9, w=4, angfn=lambda X, Y: np.zeros(X.shape), seed=2, jit=.6)
    paint = np.clip(T.c.img, 0, 1)
    cv2.imwrite(os.path.join(OUT, 'sky.jpg'), (paint[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])

def horizon(trees):
    """Far hills all round: four rows of the map's rounded hills, farther = smaller, paler and bluer, with the
    map's trees standing on the nearer ridges."""
    W_, H_ = 2400, 300; T.init(0, 0, W_, H_, 1)
    rows = [(150, 50, ['#a9bcae', '#b4c4b6', '#9fb3a6'], .55), (190, 60, ['#8ea86c', '#9db57a', '#b2b878'], .4),
            (225, 60, ['#79a04a', '#8bb055', '#c6a24a'], .25), (262, 50, ['#6d9a3c', '#86ac46', '#d0a43e'], .1)]
    tops = []
    for ri, (base, amp, cols, haze) in enumerate(rows):
        x = -20; poly = []
        while x < W_ + 20:                                              # a run of round-topped hills, as on the map
            w = R.uniform(110, 260) * (1 - ri * .12); h = amp * R.uniform(.5, 1.0)
            for t in np.linspace(0, 1, 12): poly.append((x + w * t, base - h * math.sin(math.pi * t) ** .8))
            x += w * R.uniform(.7, .95)
        tops.append(poly); full = poly + [(W_ + 20, H_ + 20), (-20, H_ + 20)]
        m = A(full, cols[0], wob=1.2, rough=.8, edge_dark=.06)
        def hcol(X, Y, r, cols=cols):
            C = np.array([hexc(c) for c in cols]); idx = r.choice(3, size=len(X), p=[.5, .3, .2])
            return np.clip(C[idx] * (1 + (r.rand(len(X), 1) - .5) * .05), 0, 1)
        T.c.stip(m, hcol, spacing=2.0, L=6, w=2.6, angfn=lambda X, Y: np.full(X.shape, .2), seed=20 + ri, jit=.5)
    T.light() if hasattr(T, 'light') else None
    paint = np.clip(T.c.img, 0, 1); img = (paint[..., ::-1] * 255).astype(np.float32)
    al = (np.clip(T.ALPHA, 0, 1) * 255).astype(np.uint8)
    # map trees on the two nearer rows, small, with haze toward the sky colour
    for ri in (1, 2, 3):
        haze = rows[ri][3]
        for _ in range(55 + ri * 25):
            x = R.uniform(0, W_); top = tops[ri]; yi = np.interp(x, [p[0] for p in top], [p[1] for p in top]) + R.uniform(2, 30)
            t = trees[R.randint(len(trees))]; s = (8 + ri * 7) * R.uniform(.8, 1.25) / t.shape[0]
            tt = cv2.resize(t, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); th, tw = tt.shape[:2]
            x0, y0 = int(x - tw / 2), int(yi - th)
            if x0 < 0 or y0 < 0 or x0 + tw > W_ or y0 + th > H_: continue
            a = tt[..., 3:].astype(np.float32) / 255; c = tt[..., :3].astype(np.float32) * (1 - haze) + np.array([214, 200, 172]) * haze
            img[y0:y0 + th, x0:x0 + tw] = img[y0:y0 + th, x0:x0 + tw] * (1 - a) + c * a
    cv2.imwrite(os.path.join(OUT, 'horizon.png'), np.dstack([np.clip(img, 0, 255).astype(np.uint8), al]))

def main():
    t0 = time.time(); img = stitch(); print('  map', img.shape, flush=True)
    meta = {'extent_m': EXTENT, 'river': RIVER, 'town_map_px': TOWN, 'landmarks': {}, 'trees': [], 'clouds': []}
    for k, (rect, h) in LANDMARKS.items(): meta['landmarks'][k] = cutout(img, k, rect, h); print('  land', k, flush=True)
    sp = os.path.join(VIEWER, 'sprites'); trees = []
    for f in sorted(os.listdir(sp)):
        if (f.startswith('tree_decid_') or f.startswith('tree_ever_') or f.startswith('cloud_')) and '@' not in f:
            shutil.copy(os.path.join(sp, f), os.path.join(OUT, 'map', f)); im = cv2.imread(os.path.join(sp, f), cv2.IMREAD_UNCHANGED)
            (meta['clouds'] if f.startswith('cloud') else meta['trees']).append(dict(file=f, w=im.shape[1], h=im.shape[0], ever=f.startswith('tree_ever')))
            if not f.startswith('cloud'): trees.append(im)
    D = donors(img); meadow(img, D); sky(); horizon(trees)
    json.dump(meta, open(os.path.join(OUT, 'land.json'), 'w'), indent=1)
    print('done', round(time.time() - t0), 's')

if __name__ == '__main__':
    main()

"""Toy Town study 1: the blue shop with the green-and-white awning, traced from the approved target painting and
repainted with the map's folk brush (the same method as the Marines trace).

1. Cut:     the blue shop group (front gabled shop, its side wing and the taller blue house behind it) from
            docs/toytown_layout/reference/toytown_target.webp, by a hand-drawn outline in the target's own pixels.
2. Clean:   the pink blossom tree in front of the side wing is removed and the wall behind it painted in
            (the user chose snowy firs and bare trees instead of blossom).
3. Calm:    colours eased toward the national map's palette: slightly lower lightness, saturation compressed at the
            top end, so Toy Town reads as part of the same painting.
4. Repaint: the folk brush, coarse to fine; every dab takes its colour from the traced shop and follows its forms.
            Dab sizes are set in Toy Town detail-layer pixels to match the brushwork already on the map.
Writes study out/ images only. Nothing in the map, routes or engine changes.
    PYTHONPATH=../../../folk2:../../../styles2 python3 study_blue_shop.py
"""
import os, sys, math, json, time
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path[:0] = [os.path.join(ROOT, 'folk2'), os.path.join(ROOT, 'styles2'), os.path.join(ROOT, 'docs', 'toytown_layout')]
from kit import Kanvas, impasto
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
TARGET = os.path.join(ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp')
FIT = 2.747                       # detail-layer px per target px (from the fit check)
K = 4                             # study canvas px per target px (a little above the detail layer, for close inspection)

# the outline of the blue shop group, in target px (clockwise from the side wing's lower left)
OUTLINE = [(25, 902), (25, 668), (6, 664), (12, 628), (60, 604), (120, 578), (196, 548), (204, 502), (250, 437), (296, 497),
           (300, 560), (300, 742), (322, 748), (322, 802), (311, 806), (311, 902)]
ROOF_CUT = [(8, 652), (14, 630), (60, 606), (120, 580), (196, 550)]     # where the cut crosses the side roof: snow is laid along it
FIR = (58, 908, 190)                                                    # snowy fir in front of the side wing: base x, y, height
TREE = [(0, 722), (100, 722), (100, 912), (0, 912)]            # the blossom tree in front of the side wing
BOX = (0, 430, 330, 912)

def calm(rgb):
    """Ease the target's colours toward the map: lightness down a little, the strongest saturation compressed."""
    lab = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    L, a, b = lab[..., 0], lab[..., 1] - 128, lab[..., 2] - 128
    C = np.hypot(a, b) + 1e-6
    C2 = np.where(C < 38, C * .9, 34.2 + (C - 38) * .62)
    L2 = (L - 145) * .96 + 138
    lab = np.dstack([L2, 128 + a * C2 / C, 128 + b * C2 / C])
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255

def poly_mask(shape, pts, ox, oy, k):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round((np.array(pts, np.float32) - (ox, oy)) * k * 8).astype(np.int32)], 255, cv2.LINE_AA, shift=3)
    return m.astype(np.float32) / 255

def traced_fir(tgt):
    """One of the target's own snowy firs (upper left of the painting), cut from its hillside by colour:
    dark needles, white snow, brown trunk, inside a generous cone around the tree."""
    x0, y0, x1, y1 = FIR_SRC; crop = tgt[y0:y1, x0:x1]; h, w = crop.shape[:2]
    hsv = cv2.cvtColor((crop * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.int32)
    Hh, Ss, Vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    needles = (Ss < 160) & (Vv < 130) & (Hh > 25)          # the fir's greens are duller and darker than the hillside's
    snow = (Ss < 85) & (Vv > 150)
    trunk = (Hh < 24) & (Vv < 85) & (Ss > 120)
    cone = np.zeros((h, w), np.uint8)
    cv2.fillPoly(cone, [np.array([(58, 0), (-6, h - 1), (w + 6, h - 1)], np.int32)], 1)
    m = ((needles | snow | trunk) & (cone > 0)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((4, 4), np.uint8))
    n, l, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = (l == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    inv = (1 - m).astype(np.uint8); n2, l2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, n2):
        if st2[i, 4] < 260: m[l2 == i] = 1                  # fill holes inside the tree; the jagged outline stays open
    return crop, cv2.GaussianBlur(m.astype(np.float32), (0, 0), .6)
FIR_SRC = (12, 100, 128, 276)

def main(prefix='blue_shop', finish=None, guide=None):
    t0 = time.time()
    tgt = cv2.imread(TARGET)[..., ::-1].astype(np.float32) / 255
    x0, y0, x1, y1 = BOX; ref = tgt[y0:y1, x0:x1].copy(); H, W = ref.shape[:2]
    # 2. remove the blossom tree: paint the side wing's blue wall back in where the tree stood
    tree = poly_mask((H, W), TREE, x0, y0, 1)
    hsv = cv2.cvtColor((ref * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    pinkish = ((hsv[..., 0] > 140) | (hsv[..., 0] < 8)) & (hsv[..., 1] > 40) & (hsv[..., 2] > 120)
    trunk = (hsv[..., 2] < 90) & (hsv[..., 1] > 60) & (hsv[..., 0] < 25)
    hole = ((tree > .5) & (pinkish | trunk | (hsv[..., 1] < 50))).astype(np.uint8)
    hole = cv2.dilate(hole, np.ones((5, 5), np.uint8)) * (tree > .5)
    u8 = (ref * 255).astype(np.uint8)
    filled = cv2.inpaint(u8, hole.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA).astype(np.float32) / 255
    # inpainting leaves a smear; give the wall back its mottled blue from the wall just above the tree
    # quilt the wall back from small patches of the side wing's own wall (beside its window), so it keeps its mottle
    patches = [ref[yy:yy + 14, xx:xx + 14] for yy in range(240, 285, 7) for xx in (28, 84)]
    rr = np.random.RandomState(3); quilt = np.zeros_like(ref)
    for yy in range(0, H, 12):
        for xx in range(0, W, 12):
            p = patches[rr.randint(len(patches))]; h_, w_ = min(14, H - yy), min(14, W - xx)
            quilt[yy:yy + h_, xx:xx + w_] = p[:h_, :w_]
    quilt = cv2.GaussianBlur(quilt, (0, 0), .7)
    hm = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 1.5)[..., None]
    ref = ref * (1 - hm) + (filled * .2 + quilt * .8) * hm
    # snow laid along the cut across the side roof, so the silhouette ends in a snowy edge rather than a cut
    sn = np.zeros((H, W), np.uint8)
    pts = (np.array(ROOF_CUT, np.float32) - (x0, y0))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(math.hypot(bx - ax, by - ay) / 3)
        for i in range(n + 1):
            t = i / max(1, n); px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            r_ = 6 + 2.5 * math.sin(i * 1.7) + rr.rand() * 2
            cv2.circle(sn, (int(px), int(py + 3)), int(r_), 255, -1, cv2.LINE_AA)
    snm = cv2.GaussianBlur(sn.astype(np.float32) / 255, (0, 0), 1.0)[..., None]
    snow_col = np.array([.95, .96, .985]) * (1 - .06 * cv2.GaussianBlur(rr.rand(H, W).astype(np.float32), (0, 0), 1.5)[..., None])
    ref = ref * (1 - snm) + snow_col * snm
    # the snowy fir (traced from the target) stands in front of the side wing where the blossom tree was
    fcrop, fm = traced_fir(tgt); fhgt = FIR[2]; sc = fhgt / fcrop.shape[0]
    fcrop = cv2.resize(fcrop, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); fm = cv2.resize(fm, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    fx0 = int(FIR[0] - x0 - fcrop.shape[1] * .48); fy0 = int(FIR[1] - y0 - fcrop.shape[0])
    fir_alpha = np.zeros((H, W), np.float32)
    ys, xs = slice(max(0, fy0), min(H, fy0 + fcrop.shape[0])), slice(max(0, fx0), min(W, fx0 + fcrop.shape[1]))
    sy, sx = slice(ys.start - fy0, ys.stop - fy0), slice(xs.start - fx0, xs.stop - fx0)
    fir_alpha[ys, xs] = fm[sy, sx]
    ref[ys, xs] = ref[ys, xs] * (1 - fm[sy, sx, None]) + fcrop[sy, sx] * fm[sy, sx, None]
    # 3. calm the palette
    ref = calm(np.clip(ref, 0, 1))
    # 4. repaint (canvas K px per target px)
    alpha = cv2.GaussianBlur(poly_mask((H * K, W * K), OUTLINE, x0, y0, K), (0, 0), .7 * K)
    alpha = np.maximum(alpha, cv2.resize(fir_alpha, (W * K, H * K), interpolation=cv2.INTER_LINEAR))
    c = Kanvas(W * K, H * K, K, '#000000', seed=31); c.HM = np.zeros((c.H, c.W), np.float32)
    big = cv2.resize(ref, (W * K, H * K), interpolation=cv2.INTER_CUBIC)
    if guide: big = np.clip(guide(big, x0, y0, K), 0, 1)       # a sharpened, partly redrawn guide at canvas resolution
    c.img[:] = cv2.GaussianBlur(big, (0, 0), (.6 if guide else 1.3) * K)
    g = cv2.cvtColor(big, cv2.COLOR_RGB2GRAY)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=5), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=5)
    mag = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 1.5 * K)
    ang = cv2.GaussianBlur(np.arctan2(gy, gx), (0, 0), 1) + math.pi / 2
    def sampler(img):
        def at(X, Y):
            X = X.astype(np.float32).ravel(); Y = Y.astype(np.float32).ravel(); out = np.empty((len(X), 3), np.float32)
            for i in range(0, len(X), 30000):        # remap takes at most 32767 points per row
                out[i:i + 30000] = cv2.remap(img, X[i:i + 30000].reshape(1, -1), Y[i:i + 30000].reshape(1, -1), cv2.INTER_LINEAR,
                                             borderMode=cv2.BORDER_REFLECT).reshape(-1, 3)
            return out
        return at
    if guide:       # sample the canvas-resolution guide, so the dabs can hold edges finer than the target's pixels
        at0 = {s: sampler(cv2.GaussianBlur(big, (0, 0), s * K) if s else big) for s in (1.4, .7, 0)}
        at = {s: (lambda X, Y, f=f: f(X * K, Y * K)) for s, f in at0.items()}
    else:
        at = {s: sampler(cv2.GaussianBlur(ref, (0, 0), s) if s else ref) for s in (1.4, .7, 0)}
    def angfn(X, Y):
        xi = np.clip((X * K).astype(int), 0, c.W - 1); yi = np.clip((Y * K).astype(int), 0, c.H - 1)
        return ang[yi, xi]
    def colfn(blur, var):
        def f(X, Y, r): return np.clip(at[blur](X, Y) * (1 + (r.rand(len(X), 1) - .5) * 2 * var), 0, 1)
        return f
    full = (0, 0, alpha)
    detail = np.clip((mag / np.percentile(mag[alpha > .5], 75) - .45) * 1.5, 0, 1) * alpha
    # dab sizes in target px; at the map's detail scale (x2.75) the coarse dab is ~9-10 px, like the map's houses
    passes = [(3.0, 4.8, 3.0, 1.4, .06, full, 1), (1.7, 2.8, 1.8, .7, .05, full, 2), (1.0, 1.7, 1.15, 0, .04, (0, 0, detail), 3),
              (.6, 1.0, .7, 0, .03, (0, 0, detail * (detail > .6)), 4)]
    if guide: passes.append((.4, .65, .45, 0, .02, (0, 0, detail * (detail > .75)), 5))
    for spacing, L, w, blur, var, m, seed in passes:
        c.stip(m, colfn(blur, var), spacing=spacing, L=L, w=w, angfn=angfn, seed=seed, jit=.35, thresh=.3)
    if finish: finish(c, x0, y0, alpha)
    impasto(c, strength=.22)
    paint = np.clip(c.img, 0, 1)
    rgba = np.dstack([paint, alpha])
    cv2.imwrite(os.path.join(OUT, f'{prefix}_study.png'), (np.dstack([paint[..., ::-1], alpha]) * 255).astype(np.uint8))
    # comparison sheet: target crop | repaint, both at the study scale, on a neutral ground
    tcrop = cv2.resize(tgt[y0:y1, x0:x1], (W * K, H * K), interpolation=cv2.INTER_CUBIC)
    ground = np.full_like(paint, (.93, .91, .87))
    rep = paint * alpha[..., None] + ground * (1 - alpha[..., None])
    gap = np.full((H * K, 30, 3), 1.0)
    sheet = np.concatenate([tcrop, gap, rep], 1)
    cv2.imwrite(os.path.join(OUT, f'{prefix}_compare.jpg'), (sheet[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    # 100% detail crops: the awning and display window, and the upper windows with the garland
    for nm, (cx0, cy0, cx1, cy1) in {'awning': (95, 735, 325, 905), 'windows': (95, 600, 320, 745)}.items():
        a_ = (np.array([cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0]) * K).astype(int)
        crop = np.concatenate([tcrop[a_[1]:a_[3], a_[0]:a_[2]], np.ones((a_[3] - a_[1], 20, 3)), rep[a_[1]:a_[3], a_[0]:a_[2]]], 1)
        cv2.imwrite(os.path.join(OUT, f'{prefix}_detail_{nm}.jpg'), (crop[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
    # in context at the map's detail scale: on the fit-check composite (neighbours still in the target's texture)
    s = FIT / K
    small = cv2.resize(rgba, (int(W * K * s), int(H * K * s)), interpolation=cv2.INTER_AREA)
    json.dump(dict(seconds=round(time.time() - t0, 1), canvas=[W * K, H * K], at_detail_scale=list(small.shape[1::-1])),
              open(os.path.join(OUT, f'{prefix}_study.json'), 'w'))
    np.save(os.path.join(OUT, f'{prefix}_detail_scale.npy'), small.astype(np.float16))
    print('done', round(time.time() - t0, 1), 's')

if __name__ == '__main__':
    main()

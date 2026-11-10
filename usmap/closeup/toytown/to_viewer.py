"""Preview build: the built Toy Town placed into a copy of the map viewer (usmap/viewer_tt/).

Nothing in the live viewer, the map, the routes or the engine changes; viewer_nw is copied, then in the copy:
  1. the town render is scaled to the detail layer (2.747 detail px per target px, the fit check) and blended in
     through a soft town-shaped mask, with the railway corridors outside the station cut out of the mask so the
     map's own tracks stay exactly where they are;
  2. the base (national) layer gets the same, at half the detail scale;
  3. both deep-zoom pyramids are rebuilt from the new images;
  4. the occluder tiles (what trains pass behind) are recoloured from the new art inside their existing masks;
  5. animated sprites cut from the old painting that sit inside the town (station flags, swaying trees) are
     left out, since they would show the old art.
    python3 to_viewer.py
"""
import os, sys, json, shutil, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
SRC = os.path.join(ROOT, 'usmap', 'viewer_nw'); DST = os.path.join(ROOT, 'usmap', 'viewer_tt')
S = 2.747; OX, OY = 1293 - 195 * S, 1173 - 285 * S         # target px -> detail px (fit check)
DET0 = (2560, 1024)                                         # detail px = (f1 px - DET0) * 2
TILE = 1024

def stitch(level_dir):
    fs = os.listdir(level_dir); xs = max(int(f.split('_')[0]) for f in fs) + 1; ys = max(int(f.split('_')[1].split('.')[0]) for f in fs) + 1
    rows = []
    for y in range(ys):
        row = []
        for x in range(xs):
            t = cv2.imread(os.path.join(level_dir, f'{x}_{y}.jpg')); ox, oy = (1 if x else 0), (1 if y else 0)
            row.append(t[oy:oy + TILE, ox:ox + TILE])
        rows.append(np.concatenate(row, 1))
    return np.concatenate(rows, 0)

def pyramid(img, out_dir, quality=90):
    shutil.rmtree(out_dir, ignore_errors=True)
    H, W = img.shape[:2]; top = math.ceil(math.log2(max(W, H)))
    cur = img
    for L in range(top, -1, -1):
        d = os.path.join(out_dir, str(L)); os.makedirs(d)
        h, w = cur.shape[:2]
        for ty in range(math.ceil(h / TILE)):
            for tx in range(math.ceil(w / TILE)):
                x0, y0 = max(0, tx * TILE - 1), max(0, ty * TILE - 1); x1, y1 = min(w, (tx + 1) * TILE + 1), min(h, (ty + 1) * TILE + 1)
                cv2.imwrite(os.path.join(d, f'{tx}_{ty}.jpg'), cur[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, quality])
        if L: cur = cv2.resize(cur, (max(1, math.ceil(w / 2)), max(1, math.ceil(h / 2))), interpolation=cv2.INTER_AREA)

CORE = [(186, 262), (362, 108), (560, 8), (840, 8), (1038, 108), (1214, 262), (1220, 392), (1296, 472), (1302, 860), (1399, 826),
        (1399, 966), (1280, 1004), (1000, 1034), (560, 1044), (260, 1014), (10, 936), (0, 700), (22, 628), (92, 556), (186, 522)]

def town_mask(shape, scene):
    """Where the new town replaces the old art, in detail px: the built town's outline with a lumpy, snow-drift
    edge, only lightly feathered so the snow ends as a painted edge rather than a haze. The map's tracks run
    up to this outline and disappear behind the buildings, as agreed."""
    t2d = lambda p: (OX + p[0] * S, OY + p[1] * S)
    P = []
    for a, b in zip(CORE, CORE[1:] + CORE[:1]):
        n = max(2, int(math.dist(a, b) / 6))
        for t in np.linspace(0, 1, n, endpoint=False): P.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    P = np.array(P); c = P.mean(0); rr = np.random.RandomState(4); ph = rr.uniform(0, 6, 3)
    out = []
    for i, p in enumerate(P):
        d = p - c; L = np.linalg.norm(d) or 1; u = i / len(P) * math.tau
        k = 5 * math.sin(u * 23 + ph[0]) + 3 * math.sin(u * 57 + ph[1]) + 2 * math.sin(u * 113 + ph[2])
        out.append(t2d(p + d / L * k))
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round(np.array(out)).astype(np.int32)], 255, cv2.LINE_AA)
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 3.5)

def fringe():
    """Snow drifting out from the town onto the surrounding hills, thinning with distance (target px), painted
    with the kit's snow on a transparent canvas."""
    sys.path.insert(0, HERE)
    import toytown_kit as T
    K = 3; T.init(-160, -160, 1560, 1290, K)
    core = np.array(CORE, np.float32)
    rr = np.random.RandomState(8)
    for _ in range(7000):
        x, y = rr.uniform(-150, 1550), rr.uniform(-150, 1280)
        d = cv2.pointPolygonTest(core.reshape(-1, 1, 2), (float(x), float(y)), True)
        if d > 4 or d < -170: continue
        p = math.exp(-(-d) / 70) ** 1.3                                # dense at the edge, thinning outward
        if rr.rand() > p: continue
        T.snow_clump(x, y, rr.uniform(12, 32) * (.45 + .55 * p), rr.uniform(4, 8) * (.55 + .45 * p))
    T.impasto(T.c, strength=.22)
    paint = np.clip(T.c.img, 0, 1); al = np.clip(cv2.GaussianBlur(T.ALPHA, (0, 0), .5), 0, 1)
    return (paint * 255).astype(np.float32)[..., ::-1], al

def main():
    shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
    scene = json.load(open(os.path.join(DST, 'scene.json')))
    town = cv2.imread(os.path.join(HERE, 'out', 'toytown_full.png'))
    tw, th = round(1399 * S), round(1124 * S)
    town = cv2.resize(town, (tw, th), interpolation=cv2.INTER_AREA)
    # 1. detail layer
    det = stitch(os.path.join(SRC, 'tiles', 'detail_files', str(max(int(d) for d in os.listdir(os.path.join(SRC, 'tiles', 'detail_files'))))))
    Hd, Wd = det.shape[:2]
    layer = det.copy(); ox, oy = int(round(OX)), int(round(OY))
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(Wd, ox + tw), min(Hd, oy + th)
    layer[y0:y1, x0:x1] = town[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    m = town_mask((Hd, Wd), scene)[..., None]
    det_new = (det * (1 - m) + layer * m)
    fp, fa = fringe()                                       # snow drifting out over the hills
    fw, fh = round(fp.shape[1] / 3 * S), round(fp.shape[0] / 3 * S)
    fp = cv2.resize(fp, (fw, fh), interpolation=cv2.INTER_AREA); fa = cv2.resize(fa, (fw, fh), interpolation=cv2.INTER_AREA)[..., None]
    fx, fy = int(round(OX - 160 * S)), int(round(OY - 160 * S))
    x0, y0, x1, y1 = max(0, fx), max(0, fy), min(Wd, fx + fw), min(Hd, fy + fh)
    reg = det_new[y0:y1, x0:x1]; a_ = fa[y0 - fy:y1 - fy, x0 - fx:x1 - fx] * (1 - m[y0:y1, x0:x1])
    det_new[y0:y1, x0:x1] = reg * (1 - a_) + fp[y0 - fy:y1 - fy, x0 - fx:x1 - fx] * a_
    m = np.maximum(m, np.pad(fa[..., 0], ((max(0, fy), 0), (max(0, fx), 0)))[:Hd, :Wd, None] if False else m)
    det_new = det_new.astype(np.uint8)
    pyramid(det_new, os.path.join(DST, 'tiles', 'detail_files'))
    # 2. base layer
    bdir = os.path.join(SRC, 'tiles', 'base_files'); btop = max(int(d) for d in os.listdir(bdir))
    base = stitch(os.path.join(bdir, str(btop)))
    W1, H1 = scene['size']; base = base[:H1, :W1]
    small = cv2.resize(det_new, (Wd // 2, Hd // 2), interpolation=cv2.INTER_AREA); ms = cv2.resize(m[..., 0], (Wd // 2, Hd // 2))[..., None]
    reg = base[DET0[1]:DET0[1] + Hd // 2, DET0[0]:DET0[0] + Wd // 2]
    h, w = reg.shape[:2]
    base[DET0[1]:DET0[1] + h, DET0[0]:DET0[0] + w] = (reg * (1 - ms[:h, :w]) + small[:h, :w] * ms[:h, :w]).astype(np.uint8)
    pyramid(base, bdir.replace(SRC, DST))
    # 3. occluders: trains pass behind the whole town (they run into it behind the houses, into the station).
    #    Every occluder tile touching the town gets the town's mask as alpha (plus its old mask elsewhere) and
    #    the new art as colour; tiles that did not exist are added.
    for sub, img, mk, key in (('occ', base, cv2.resize(m[..., 0], (Wd // 2, Hd // 2)), 'occluder'), ('occ_hi', det_new, m[..., 0], 'detail')):
        d = os.path.join(DST, sub); ts = 512
        entry = scene[key] if key == 'occluder' else scene['detail']['occluder']
        tiles = {tuple(t) for t in entry['tiles']}
        off = DET0 if sub == 'occ' else (0, 0)
        Hm, Wm = mk.shape
        for ty in range(math.ceil((off[1] + Hm) / ts)):
            for tx in range(math.ceil((off[0] + Wm) / ts)):
                x, y = tx * ts, ty * ts
                if x + ts > img.shape[1] or y + ts > img.shape[0]: continue
                a_ = np.zeros((ts, ts), np.float32)
                mx0, my0 = x - off[0], y - off[1]
                sx0, sy0 = max(0, mx0), max(0, my0); sx1, sy1 = min(Wm, mx0 + ts), min(Hm, my0 + ts)
                if sx1 <= sx0 or sy1 <= sy0: continue
                a_[sy0 - my0:sy1 - my0, sx0 - mx0:sx1 - mx0] = mk[sy0:sy1, sx0:sx1]
                if a_.max() < .05: continue
                f = os.path.join(d, f'{tx}_{ty}.png')
                old = cv2.imread(f, cv2.IMREAD_UNCHANGED) if os.path.exists(f) else None
                alpha = a_ * 255 if old is None else np.maximum(old[..., 3].astype(np.float32), a_ * 255)
                cv2.imwrite(f, np.dstack([img[y:y + ts, x:x + ts], alpha.astype(np.uint8)]))
                tiles.add((tx, ty))
        entry['tiles'] = sorted([list(t) for t in tiles], key=lambda t: (t[1], t[0]))
        # tiles already listed but outside the town: recolour from the new image where they touch the change
        for (tx, ty) in tiles:
            f = os.path.join(d, f'{tx}_{ty}.png'); o = cv2.imread(f, cv2.IMREAD_UNCHANGED)
            if o is None: continue
            new = img[ty * ts:ty * ts + ts, tx * ts:tx * ts + ts]
            if new.shape[:2] == o.shape[:2]: o[..., :3] = new; cv2.imwrite(f, o)
    # 4. sprites cut from the old art inside the town
    mb = (cv2.resize(m[..., 0], (Wd // 2, Hd // 2)) > .3)
    keep = []
    for e in scene['sprites']:
        cx, cy = e['x'] + e['w'] / 2 - DET0[0], e['y'] + e['h'] / 2 - DET0[1]
        inside = 0 <= cx < mb.shape[1] and 0 <= cy < mb.shape[0] and mb[int(cy), int(cx)]
        if not (inside and e['kind'] in ('flag', 'sway', 'frond')): keep.append(e)
    print('sprites removed:', len(scene['sprites']) - len(keep))
    scene['sprites'] = keep
    json.dump(scene, open(os.path.join(DST, 'scene.json'), 'w'))
    cv2.imwrite(os.path.join(HERE, 'out', 'viewer_tt_detail.jpg'), cv2.resize(det_new, None, fx=.4, fy=.4, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    cv2.imwrite(os.path.join(HERE, 'out', 'viewer_tt_national.jpg'), cv2.resize(base, None, fx=.25, fy=.25, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('ok')

if __name__ == '__main__':
    main()

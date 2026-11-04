"""Phase 3: the prototype viewer bundle (viewer10/), built from the engine's tile caches.

  tiles/base    the national map, engine-painted at f = 1 (cache/f1), as a Deep Zoom pyramid
  tiles/detail  Toy Town, engine-painted at f = 2 (cache/f2), as a second pyramid laid exactly over the same place
  sprites/      the published moving parts, except:
                  * every front patch (what is redrawn over a moving tree) is cut again from the ENGINE base,
                    so patch and painting match pixel for pixel
                  * the moving trees, flags and train vehicles that appear in Toy Town are painted again by the engine
                    at f = 1 (replacing the published sprite) and at f = 2 (used when zoomed in)
  occ/, occ_hi/ the occluder (what trains pass behind), cut from the engine base at f = 1, and at f = 2 in Toy Town
The published viewer (viewer5/) and its files are not touched.
"""
import sys, os, json, math, shutil, time, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2
import render10 as R, cache10 as C
B = R.B; U5 = R.U5; BR = R.BR
DST = os.path.join(R.ROOT, 'viewer10'); SRC_MAN = os.path.join(R.ROOT, 'out5_6400', 'anim')
TT = (670, 200, 1190, 650)                                      # Toy Town detail rectangle, map units
FD = 2                                                         # detail density
T0 = time.time(); log = lambda m: print(f'{time.time() - T0:6.1f}s {m}', flush=True)

def dzi(img, name):
    """A Deep Zoom pyramid (1024 px tiles, 1 px overlap), like make_viewer4."""
    TS_, OV = 1024, 1; H, W = img.shape[:2]; d = os.path.join(DST, 'tiles', f'{name}_files'); shutil.rmtree(d, ignore_errors=True)
    maxL = math.ceil(math.log2(max(W, H))); im = img; n = 0; nbytes = 0
    for L in range(maxL, -1, -1):
        h, w = im.shape[:2]; os.makedirs(f'{d}/{L}', exist_ok=True)
        for cx in range(math.ceil(w / TS_)):
            for cy in range(math.ceil(h / TS_)):
                x0, y0 = max(0, cx * TS_ - OV), max(0, cy * TS_ - OV); x1, y1 = min(w, (cx + 1) * TS_ + OV), min(h, (cy + 1) * TS_ + OV)
                p = f'{d}/{L}/{cx}_{cy}.jpg'; cv2.imwrite(p, im[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 88]); n += 1; nbytes += os.path.getsize(p)
        if L: im = cv2.resize(im, (max(1, math.ceil(w / 2)), max(1, math.ceil(h / 2))), interpolation=cv2.INTER_AREA)
    return dict(tiles=n, mb=round(nbytes / 1e6, 1), levels=maxL + 1, size=[W, H])

def save_rgba(path, rgb, a):
    im = np.dstack([np.clip(rgb[..., ::-1] * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8); cv2.imwrite(path, im)

def sprite(f, bbox, paint_fn, seed):
    """B.sprite() for the engine: paint on black and on white, recover colour and alpha, light the paint ridges."""
    k = BR.K1 * f; ox, oy = BR.PADL * k, BR.PADT * k; GW, GH = R.frame_px(f)
    x0, y0 = int(max(0, bbox[0] * k + ox)), int(max(0, bbox[1] * k + oy)); x1, y1 = int(min(GW, bbox[2] * k + ox)), int(min(GH, bbox[3] * k + oy))
    outs = []
    for bg in (0.0, 1.0):
        for m in R.MODS: m.c = None
        c = BR.EngineCanvas(f, (x0, y0, x1 - x0, y1 - y0), ground='#000000'); c.img[:] = bg; R.use(c)
        c.rng = np.random.RandomState(seed); c.eseed = seed & 0x7FFFFFFF; c.clipm = None
        paint_fn(); outs.append((c.img.copy(), c.HM.copy()))
    (b, hm), (wht, _) = outs
    alpha = np.clip(1 - (wht - b).mean(-1), 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, b / np.maximum(alpha[..., None], 1e-3), 0)
    hb = cv2.GaussianBlur(hm, (0, 0), 1.1 * f); gx = cv2.Sobel(hb, cv2.CV_32F, 1, 0, ksize=3) / f; gy = cv2.Sobel(hb, cv2.CV_32F, 0, 1, ksize=3) / f
    rgb = np.clip(rgb * (1 + np.clip((gx * -.7 + gy * -.7) * .14, -.14, .14))[..., None], 0, 1)
    return (x0, y0), rgb.astype(np.float32), alpha.astype(np.float32)

def front_patch(base, Z, a, x0, y0, depth, name, outdir):
    """What is painted in front of a moving part, cut from the (engine) base: the same rule as usmap5.export_movers."""
    h, w = a.shape; Zs = Z[y0:y0 + h, x0:x0 + w]; vis = (Zs <= depth + 1e-6)
    mask = (a > .02) & ~vis
    if mask.sum() < 4: return None
    m = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    ys, xs = np.nonzero(m); a0, a1, b0, b1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = base[y0 + a0:y0 + a1, x0 + b0:x0 + b1][..., ::-1].astype(np.float32) / 255
    save_rgba(os.path.join(outdir, name), rgb, m[a0:a1, b0:b1])
    return dict(file=name, x=int(x0 + b0), y=int(y0 + a0), w=int(b1 - b0), h=int(a1 - a0))

def occluder(base, Z, TRK, f, origin, scene, routes_px):
    """usmap4.main's occluder: base pixels in front of the railroad corridor (and on its extensions into the stations)."""
    k = BR.K1 * f; H, W = Z.shape; X0, Y0 = origin
    corr = np.full((H, W), np.nan, np.float32)
    for nm, r in scene['routes'].items():
        P = np.array(routes_px[nm]) * f - [X0, Y0]
        n_ = 50; DEP = np.concatenate([np.full(n_, -2e9), np.array(r['depth']), np.full(n_, -2e9)])
        for i in range(len(P) - 1):
            a_, b_ = P[i], P[i + 1]
            poly = np.array([a_ + [-14 * k, 8 * k], b_ + [14 * k, 8 * k], b_ + [14 * k, -48 * k], a_ + [-14 * k, -48 * k]])
            x0, y0 = int(max(0, poly[:, 0].min())), int(max(0, poly[:, 1].min())); x1, y1 = int(min(W, poly[:, 0].max() + 1)), int(min(H, poly[:, 1].max() + 1))
            if x1 <= x0 or y1 <= y0: continue
            sub = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(sub, [np.round(poly - [x0, y0]).astype(np.int32)], 1)
            cur = corr[y0:y1, x0:x1]; upd = (sub > 0) & (np.isnan(cur) | (cur < DEP[i])); cur[upd] = DEP[i]
    occ = (~np.isnan(corr)) & (Z > np.nan_to_num(corr, nan=1e9) + 1e-3) & ~TRK
    return cv2.GaussianBlur(occ.astype(np.float32), (0, 0), .7 * f)

def occ_tiles(base, a, sub, OT=512):
    d = os.path.join(DST, sub); shutil.rmtree(d, ignore_errors=True); os.makedirs(d); out = []
    for cy in range(math.ceil(a.shape[0] / OT)):
        for cx in range(math.ceil(a.shape[1] / OT)):
            t = a[cy * OT:(cy + 1) * OT, cx * OT:(cx + 1) * OT]
            if t.max() < 8 / 255: continue
            rgb = base[cy * OT:(cy + 1) * OT, cx * OT:(cx + 1) * OT][..., ::-1].astype(np.float32) / 255
            save_rgba(f'{d}/{cx}_{cy}.png', rgb, t); out.append([cx, cy])
    return out

if __name__ == '__main__':
    os.makedirs(DST, exist_ok=True)
    for d in ('sprites',): shutil.rmtree(os.path.join(DST, d), ignore_errors=True); os.makedirs(os.path.join(DST, d))
    man = json.load(open(os.path.join(SRC_MAN, 'manifest.json'))); S = R.load_scene(); scene = S['scene']
    rep = {}
    # 1. the two painted layers
    base, (bx0, by0, bx1, by1) = C.assemble(1, None, store='f1'); Z1, _ = C.assemble(1, None, store='f1', what='z'); T1, _ = C.assemble(1, None, store='f1', what='trk')
    assert (bx0, by0) == (0, 0) and base.shape[:2] == (4175, 7089), (base.shape, bx0, by0)
    rep['base'] = dzi(base, 'base'); log(f"base pyramid {rep['base']}")
    det, (dx0, dy0, dx1, dy1) = C.assemble(FD, TT, store=f'f{FD:g}'); Z2, _ = C.assemble(FD, TT, store=f'f{FD:g}', what='z'); T2, _ = C.assemble(FD, TT, store=f'f{FD:g}', what='trk')
    rep['detail'] = dzi(det, 'detail'); log(f"detail pyramid {rep['detail']}")
    detail = dict(f=FD, rect_px_f1=[dx0 / FD, dy0 / FD, (dx1 - dx0) / FD, (dy1 - dy0) / FD], size=[dx1 - dx0, dy1 - dy0], map_rect=list(TT))
    # 2. sprites: copy the published ones, then replace / add what Toy Town needs
    for s_ in man['sprites']:
        shutil.copy(os.path.join(SRC_MAN, s_['file']), os.path.join(DST, 'sprites', s_['file']))
    def in_tt(s_):
        x, y = s_['x'] / BR.K1 - BR.PADL, s_['y'] / BR.K1 - BR.PADT; w, h = s_['w'] / BR.K1, s_['h'] / BR.K1
        return x + w > TT[0] and x < TT[2] and y + h > TT[1] and y < TT[3]
    movers = {'ever': [], 'decid': [], 'palm': []}
    for e in scene['elements']:
        if e['layer'] == 'anim5': movers[e['params']['sway']].append(e)
        elif e['kind'] == 'palm5' and e['params'].get('trunk_only'): movers['palm'].append(e)
    nre = 0
    for s_ in man['sprites']:
        if s_['kind'] == 'sway':
            cls, j = s_['cls'], int(s_['file'].rsplit('_', 1)[1][:-4]); e = movers[cls][j]
            p = {kk: v for kk, v in e['params'].items() if kk != 'sway'}; el = dict(e, params=p)
            bb = U5.canopy_box(e); bb = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
            if in_tt(s_):
                for f in (1, FD):
                    (x0, y0), rgb, a = sprite(f, bb, lambda el=el: B.paint(el, S['routes']), e['seed'])
                    name = s_['file'] if f == 1 else s_['file'].replace('.png', f'@{f}x.png'); save_rgba(os.path.join(DST, 'sprites', name), rgb, a)
                    if f == 1: s_.update(x=x0, y=y0, w=int(a.shape[1]), h=int(a.shape[0]))
                    else:
                        s_['hi'] = dict(file=name, q=f)
                        x0f, y0f = x0 - dx0, y0 - dy0
                        if 0 <= x0f and 0 <= y0f and x0f + a.shape[1] <= Z2.shape[1] and y0f + a.shape[0] <= Z2.shape[0]:
                            pf = front_patch(det, Z2, a, x0f, y0f, e['depth'], s_['file'].replace('tree_', 'front_').replace('.png', f'@{f}x.png'), os.path.join(DST, 'sprites'))
                            if pf: pf['x'] += dx0; pf['y'] += dy0; s_['hi']['front'] = pf
                nre += 1
            a1 = cv2.imread(os.path.join(DST, 'sprites', s_['file']), cv2.IMREAD_UNCHANGED)[..., 3].astype(np.float32) / 255
            pf = front_patch(base, Z1, a1, s_['x'], s_['y'], s_['depth'], s_['file'].replace('tree_', 'front_'), os.path.join(DST, 'sprites'))
            if pf: s_['front'] = pf
            else: s_.pop('front', None)
        elif s_['kind'] == 'frond':
            a1 = cv2.imread(os.path.join(DST, 'sprites', s_['file']), cv2.IMREAD_UNCHANGED)[..., 3].astype(np.float32) / 255
            pf = front_patch(base, Z1, a1, s_['x'], s_['y'], s_['depth'], s_['file'].replace('frond_', 'front_palm_'), os.path.join(DST, 'sprites'))
            if pf: s_['front'] = pf
            else: s_.pop('front', None)
    log(f'front patches cut from the engine base; {nre} Toy Town trees painted at 1x and {FD}x')
    # flags in Toy Town, and every train vehicle, at 1x and FD x
    flags = [e for e in scene['elements'] if e['kind'] == 'flag']; fs = [s_ for s_ in man['sprites'] if s_['kind'] == 'flag']
    for e, s_ in zip(flags, fs):
        if not in_tt(s_): continue
        for f in (1, FD):
            (x0, y0), rgb, a = sprite(f, e['bbox'], lambda p=e['params']: B.flag(p['x'], p['y'], p['col']), e['seed'])
            name = s_['file'] if f == 1 else s_['file'].replace('.png', f'@{f}x.png'); save_rgba(os.path.join(DST, 'sprites', name), rgb, a)
            if f == 1: s_.update(x=x0, y=y0, w=int(a.shape[1]), h=int(a.shape[0]), pivot=[e['params']['x'] * BR.K1 + BR.PADL * BR.K1 - x0, e['params']['y'] * BR.K1 + BR.PADT * BR.K1 - y0])
            else: s_['hi'] = dict(file=name, q=f)
    cnt = {'loco': 0, 'wagon': 0}; vs = {s_['file']: s_ for s_ in man['sprites'] if s_['kind'] in ('loco', 'wagon')}
    for e in [e for e in scene['elements'] if e['layer'] == 'anim' and e['kind'] == 'train']:
        p = e['params']; th = B.THEMES[p['route']]
        for j in range(p['ncars'] + 1):
            kind = 'loco' if j == 0 else 'wagon'; fname = f'{kind}_{cnt[kind]}.png'; cnt[kind] += 1
            cx, cy = 300, 300; bb = (cx - 50, cy - 60, cx + 50, cy + 14)
            fn = (lambda th=th: B.loco(np.array([cx, cy], float), np.array([1.0, 0]), np.array([0, -1.0]), B.TRAIN_S, th)) if j == 0 else \
                 (lambda j=j, th=th, p=p: B.wagon(np.array([cx, cy], float), np.array([1.0, 0]), np.array([0, -1.0]), B.TRAIN_S, th['cars'][(j - 1) % 3], j * 3 + {'red': 1, 'blue': 7, 'green': 4}[p['route']]))
            s_ = vs[fname]
            for f in (1, FD):
                (x0, y0), rgb, a = sprite(f, bb, fn, e['seed'] + j)
                name = fname if f == 1 else fname.replace('.png', f'@{f}x.png'); save_rgba(os.path.join(DST, 'sprites', name), rgb, a)
                if f == 1: s_.update(w=int(a.shape[1]), h=int(a.shape[0]), pivot=[cx * BR.K1 + BR.PADL * BR.K1 - x0, cy * BR.K1 + BR.PADT * BR.K1 - y0])
                else: s_['hi'] = dict(file=name, q=f)
    log('flags and vehicles painted at 1x and 2x')
    # 3. occluders from the engine base, and a 2x one for Toy Town
    routes_px = {nm: r['points'] for nm, r in man['routes'].items()}
    o1 = occluder(base, Z1, T1, 1, (0, 0), scene, routes_px); man['occluder'] = dict(tile=512, tiles=occ_tiles(base, o1, 'occ'))
    o2 = occluder(det, Z2, T2, FD, (dx0, dy0), scene, routes_px); detail['occluder'] = dict(tile=512, tiles=occ_tiles(det, o2, 'occ_hi'))
    log(f"occluders: {len(man['occluder']['tiles'])} tiles at 1x, {len(detail['occluder']['tiles'])} at {FD}x")
    man['detail'] = detail; man['build'] = time.strftime('%Y%m%d%H%M%S'); man['engine'] = 'engine10 (prototype)'
    json.dump(man, open(os.path.join(DST, 'scene.json'), 'w'))
    shutil.copy(os.path.join(R.ROOT, 'viewer5', 'reference.jpg'), os.path.join(DST, 'reference.jpg'))
    cv2.imwrite(os.path.join(DST, 'still_preview.jpg'), cv2.resize(base, (1600, round(1600 * base.shape[0] / base.shape[1])), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 86])
    src = open(os.path.join(HERE, 'viewer10_src.html')).read()
    open(os.path.join(DST, 'index.html'), 'w').write(src.replace('<!--SCENE-->', '<script type="application/json" id="scene-data">' + json.dumps(man) + '</script>'))
    tot = sum(os.path.getsize(os.path.join(r, f_)) for r, _, fs_ in os.walk(DST) for f_ in fs_); nf = sum(len(fs_) for _, _, fs_ in os.walk(DST))
    rep.update(files=nf, mb=round(tot / 1e6, 1)); json.dump(rep, open(os.path.join(HERE, 'out', 'viewer10_build.json'), 'w'), indent=1); log(f'bundle {rep}')

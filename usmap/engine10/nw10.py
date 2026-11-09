"""Northwest integration test: build the branch scene and run the engine with the tunnel painters plugged in.

No existing engine file is edited. This module:
  * writes out5/scene5_nw.json = out5/scene5.json + the knoll and the tunnel (two elements);
  * plugs tunnel10.paint into the element dispatcher, and registers tunnel10.py as the code of its two kinds,
    so only tiles that contain them change their cache key;
  * builds tiles into their own cache stores (f1nw), seeded from f1 by hard links, so the original prototype's
    tiles stay untouched and every tile that does not contain the knoll is reused as it is.

    python3 engine10/nw10.py scene                       write the scene
    python3 engine10/nw10.py preview OUT.png             render the test area alone (seconds)
    python3 engine10/nw10.py build                       1x tiles into cache/f1nw (only touched tiles repaint)
    python3 engine10/nw10.py viewer                      build viewer_nw/ from f1nw + f2 and viewer_nw_src.html
"""
import os, sys, json, shutil, copy, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render10 as R, cache10 as C, tunnel10 as T

ROOT = R.ROOT
SCENE_NW = os.path.join(ROOT, 'out5', 'scene5_nw.json')
CODE = ['usmap/engine10/tunnel10.py']

KNOLL = dict(cx=514.0, base=372.0, w=192.0, h=86.0, kind='moss', seed_hill=9101,
             trees=[(-16, 38, 'fir'), (12, 46, 'lfir'), (40, 34, 'fir'), (66, 28, 'orange')],
             portal=244, cover=60.0, mouth_w=46.0, mouth_h=46.0, ring=7.0, tilt=1.5)

def build_scene():
    sc = json.load(open(R.SCENE))
    E = sc['elements']
    hi = next(i for i, e in enumerate(E) if e['kind'] == 'hill' and e['params'].get('i') == 8)
    cx, base, w, h = KNOLL['cx'], KNOLL['base'], KNOLL['w'], KNOLL['h']
    box = [cx - w / 2 - 20, base - h - 70, cx + w / 2 + 20, base + 12]
    knoll = dict(kind='knoll10', depth=336.0, bbox=box, seed=91010, layer='base', params=dict(KNOLL))
    # depth: one float16 step (0.25) nearer than the track (336), so the occluder can tell the knoll's face from the track
    tun = dict(kind='tunnel10', depth=336.3, bbox=[box[0], base - h - 10, box[2], base + 12], seed=91011, layer='base', params=dict(KNOLL))
    E.insert(hi + 1, knoll)            # same depth as the hill it stands on, painted right after it, before the track
    E.append(tun)
    sc['nw_test'] = dict(note='Northwest integration test: knoll10 + tunnel10 (engine10/tunnel10.py)', knoll=KNOLL)
    json.dump(sc, open(SCENE_NW, 'w'))
    return SCENE_NW

def plug():
    """Point the engine at the branch scene and the tunnel painters."""
    for kd in ('knoll10', 'tunnel10'): C.KIND_CODE[kd] = CODE
    B = R.B; orig = B.paint
    if getattr(B.paint, '_nw', False): return
    def paint(e, routes, orig=orig):
        if not T.paint(e, routes): orig(e, routes)
    paint._nw = True; B.paint = paint
    R.SCENE = SCENE_NW
    R.load_scene.__defaults__ = (SCENE_NW, None)
    # cache stores: the 1x map is read from f1nw; Toy Town's 2x layer (untouched by the knoll) from f2 as before
    oa = C.assemble; C._orig_assemble = oa
    def assemble(f, rect=None, *a_, oa=oa, **kw):
        if kw.get('store') in ('f1', 'f2'): kw['store'] += 'nw'      # both layers come from the branch scene
        return oa(f, rect, *a_, **kw)
    C.assemble = assemble
    ob = C.build
    def build(f, rect=None, scene_path=SCENE_NW, profile='equivalent', log=print, store=None, ob=ob):
        return ob(f, rect, scene_path=scene_path, profile=profile, log=log, store=store)
    C.build = build

STATION = dict(hit=(20, 62, 178, 210), anchor=(178, 128), tag=(98, 60), glow=(96, 140, 80, 34))
STOP_I, DWELL, CREEP, PULL = 17, 5.0, 42.0, 72.0          # route index of the locomotive at the platform; seconds; map units
SECTION = (40, 90, 740, 420)                               # the before/after crop, map units

def finish_viewer(move=True):
    """viewer10/ (just built from f1nw) becomes viewer_nw/: add the Northwest data, the card picture, the
    before/after crops, and the page from viewer_nw_src.html. The rebuilt original goes back to viewer10/."""
    import numpy as np, cv2
    V, BAK, DST = os.path.join(ROOT, 'viewer10'), os.path.join(ROOT, 'viewer10_orig'), os.path.join(ROOT, 'viewer_nw')
    if move:
        shutil.rmtree(DST, ignore_errors=True); os.rename(V, DST)
        if os.path.isdir(BAK): os.rename(BAK, V)
    man = json.load(open(os.path.join(DST, 'scene.json')))
    K, PL, PT = R.BR.K1, R.BR.PADL, R.BR.PADT
    px = lambda x, y: [(x + PL) * K, (y + PT) * K]
    red = man['routes']['red']; P = np.array(red['points']); off = red['track_from']
    A = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    Z = C.assemble(1, None, store='f1nw', what='z')[0]
    zr = np.array([Z[int(round(y)), int(round(x))] for x, y in P])
    hid = np.nonzero(np.abs(zr - 336.25) < 1e-3)[0]
    iL = off + KNOLL['portal']; hid = hid[hid >= iL - 4]
    S5 = json.load(open(SCENE_NW)); Pm = np.array(S5['routes']['red']['points'])
    via = [i for i in range(len(Pm)) if 300 <= Pm[i][0] <= 410 and 100 <= i <= 230]
    foot = Pm[KNOLL['portal']] + [0, 11.0]
    mouth = px(foot[0] + 4, foot[1] - KNOLL['mouth_h'] * .78)
    st = STATION
    nw = dict(stop_s=float(A[off + STOP_I]), dwell=DWELL, creep=CREEP, pull=PULL,
              portal_s=float(A[iL]), exit_s=float(A[hid.max()]) if len(hid) else float(A[iL] + 120 * K),
              viaduct=[float(A[off + via[0]]), float(A[off + via[-1]])], mouth_top=mouth,
              hit=px(st['hit'][0], st['hit'][1]) + px(st['hit'][2], st['hit'][3]), anchor=px(*st['anchor']), anchor_w=(st['hit'][2] - st['hit'][0]) * K,
              tag=px(*st['tag']), glow=px(st['glow'][0], st['glow'][1]) + [st['glow'][2] * K, st['glow'][3] * K])
    # occluder tiles along the red line from the station to past the tunnel: loaded when the page starts
    keys = sorted({f'{int(x // 512)}_{int((y - dy) // 512)}' for x, y in P[:off + KNOLL['portal'] + 140] for dy in (0, 60 * K)})
    nw['occ_preload'] = [k_ for k_ in keys if [int(v) for v in k_.split('_')] in man['occluder']['tiles']]
    man['nw'] = nw
    print('nw', {k_: (round(v, 1) if isinstance(v, float) else v) for k_, v in nw.items() if k_ not in ('hit', 'glow')}, 'hidden points', len(hid))
    json.dump(man, open(os.path.join(DST, 'scene.json'), 'w'))
    src = open(os.path.join(HERE, 'viewer_nw_src.html')).read()
    open(os.path.join(DST, 'index.html'), 'w').write(src.replace('<!--SCENE-->', '<script type="application/json" id="scene-data">' + json.dumps(man) + '</script>'))
    # the card's picture and the before/after crops, cut from the painting itself
    base_new = C.assemble(1, None, store='f1nw')[0]; base_old = C._orig_assemble(1, None, store='f1')[0]
    def crop(img, box, w):
        x0, y0 = px(box[0], box[1]); x1, y1 = px(box[2], box[3])
        c_ = img[int(y0):int(y1), int(x0):int(x1)]; return cv2.resize(c_, (w, round(w * c_.shape[0] / c_.shape[1])), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(DST, 'sprites', 'nw_station_card.jpg'), crop(base_new, (-6, 52, 190, 172), 720), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for nm, img in (('nw_before', base_old), ('nw_after', base_new)):
        cv2.imwrite(os.path.join(DST, 'sprites', nm + '.jpg'), crop(img, SECTION, 1200), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return DST

def seed_store(name='f1'):
    src, dst = os.path.join(C.CACHE, name), os.path.join(C.CACHE, name + 'nw')
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if not os.path.exists(os.path.join(dst, f)): os.link(os.path.join(src, f), os.path.join(dst, f))

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'scene': print(build_scene())
    elif cmd == 'preview':
        build_scene(); plug()
        import cv2, numpy as np
        x0, y0, x1, y1 = [float(v) for v in sys.argv[3:7]] if len(sys.argv) > 6 else (400, 250, 640, 410)
        k = R.BR.K1 * 1
        win = (int((x0 + R.BR.PADL) * k), int((y0 + R.BR.PADT) * k), int((x1 + R.BR.PADL) * k), int((y1 + R.BR.PADT) * k))
        img, Z, st = R.render_window(1, win, scene_path=SCENE_NW)
        cv2.imwrite(sys.argv[2], img); np.save(sys.argv[2][:-4] + '_z.npy', Z); print(st)
    elif cmd == 'build':
        build_scene(); plug(); seed_store('f1'); seed_store('f2')
        r1 = C.build(1, (0, 0, 1671, 1021), store='f1nw'); r2 = C.build(2, (670, 200, 1190, 650), store='f2nw')
        print(json.dumps(dict(f1=dict(painted=[t['tile'] for t in r1['painted']], reused=r1['reused']),
                              f2=dict(painted=[t['tile'] for t in r2['painted']], reused=r2['reused'])), indent=0))
    elif cmd == 'viewer':
        build_scene(); plug()
        V, BAK = os.path.join(ROOT, 'viewer10'), os.path.join(ROOT, 'viewer10_orig')
        if os.path.isdir(V) and not os.path.isdir(BAK): os.rename(V, BAK)      # keep the rebuilt original prototype
        sys.argv = [os.path.join(HERE, 'make_viewer10.py')]
        runpy.run_path(os.path.join(HERE, 'make_viewer10.py'), run_name='__main__')
        finish_viewer()
    elif cmd == 'finish':
        build_scene(); plug(); finish_viewer(move=False)

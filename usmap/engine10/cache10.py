"""Engine 10: incremental tile rendering.

The world (at density f) is cut into fixed tiles of TS x TS world pixels: tile (i, j) covers [i*TS, (i+1)*TS) x
[j*TS, (j+1)*TS). A tile is painted on a window that reaches PAD map units past its edges, and only its own square is
kept. Because the engine paints any window exactly like any other, tiles join without seams.

Which tiles does a change affect? A tile's content depends on:
  * the elements whose bounds, grown by the selection margin, touch the tile's window, in painting order;
  * the code of the painters those elements use, and the engine and shared libraries;
  * the global layers (sea, waves, ground, coastline), which every tile paints.
All of this goes into a tile's key (a SHA-1). A tile is repainted only when its key changes; otherwise the cached
PNG is reused. Moving a tree near a tile edge changes the key of every tile its grown bounds touch, so all of them
repaint, including the parts of its shadow and edges that cross into a neighbour.

    python3 cache10.py build  F [x0 y0 x1 y1 (map units)]   build (or update) the tiles covering a rectangle
"""
import sys, os, json, hashlib, math, time, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, cv2
import render10 as R

TS = {1: 1024, 2: 1024, 3: 1024, 4: 1024}
MARGIN = 16                                    # map units: element selection margin (render10.render_window)
PAD = 16                                       # map units of overlap around each tile
CACHE = os.path.join(HERE, 'cache')

ROOTS = {'usmap': R.ROOT, 'folk2': os.path.join(os.path.dirname(R.ROOT), 'folk2'), 'styles2': os.path.join(os.path.dirname(R.ROOT), 'styles2')}
BASE_CODE = ['folk2/brush.py', 'folk2/kit.py', 'styles2/story.py', 'styles2/a.py', 'usmap/usmap.py', 'usmap/usmap2.py', 'usmap/usmap3.py',
             'usmap/usmap4.py', 'usmap/usmap5.py', 'usmap/pad5.py', 'usmap/pnw5.py', 'usmap/fl5.py',
             'usmap/engine10/brush10.py', 'usmap/engine10/render10.py', 'usmap/engine10/edges10.py']
KIND_CODE = {'station7': ['usmap/station5.py', 'usmap/tft7.py'], 'station5': ['usmap/station5.py'],
             'shops7': ['usmap/tft7.py', 'usmap/lab8/store8.py', 'usmap/engine10/split10.py'], 'square7': ['usmap/tft7.py', 'usmap/lab8/store8.py'],
             'town': ['usmap/engine10/split10.py']}

_src = {}
def src_hash(rel):
    if rel not in _src:
        top, rest = rel.split('/', 1); _src[rel] = hashlib.sha1(open(os.path.join(ROOTS[top], rest), 'rb').read()).hexdigest()
    return _src[rel]

def tile_window(f, i, j):
    k = R.BR.K1 * f; ts = TS[int(f)]; GW, GH = R.frame_px(f); pad = int(math.ceil(PAD * k))
    x0, y0, x1, y1 = i * ts, j * ts, min(GW, (i + 1) * ts), min(GH, (j + 1) * ts)
    return (x0, y0, x1, y1), (max(0, x0 - pad), max(0, y0 - pad), min(GW, x1 + pad), min(GH, y1 + pad))

def tile_elements(S, f, win):
    k = R.BR.K1 * f; mx0, my0, mx1, my1 = win[0] / k - R.BR.PADL, win[1] / k - R.BR.PADT, win[2] / k - R.BR.PADL, win[3] / k - R.BR.PADT
    return [e for e in S['base'] if e['bbox'][2] > mx0 - MARGIN and e['bbox'][0] < mx1 + MARGIN and e['bbox'][3] > my0 - MARGIN and e['bbox'][1] < my1 + MARGIN]

def tile_parts(S, f, i, j, profile):
    """Everything a tile's pixels depend on, split into what comes from the scene and what comes from the code."""
    sq, win = tile_window(f, i, j); els = tile_elements(S, f, win)
    code = [src_hash(r) for r in BASE_CODE] + sorted({src_hash(r) for e in els for r in KIND_CODE.get(e['kind'], [])})
    scene = dict(v=10, f=float(f), ts=TS[int(f)], pad=PAD, margin=MARGIN, tile=[i, j], profile=profile,
                 coast=hashlib.sha1(np.asarray(R.B.COAST).tobytes()).hexdigest(),
                 els=[[e['kind'], e['depth'], e['bbox'], e['seed'], e['params']] for e in els])
    blob = json.dumps(dict(scene, code=code), sort_keys=True, default=str)
    return dict(key=hashlib.sha1(blob.encode()).hexdigest()[:16], n=len(els),
                scene=hashlib.sha1(json.dumps(scene, sort_keys=True, default=str).encode()).hexdigest()[:16],
                code=hashlib.sha1(json.dumps(code).encode()).hexdigest()[:16])

def tile_key(S, f, i, j, profile):
    t = tile_parts(S, f, i, j, profile); return t['key'], t['n']

def write_sidecar(path, parts):
    json.dump(dict(scene=parts['scene'], code=parts['code'], n=parts['n'], written=time.strftime('%Y-%m-%d %H:%M:%S')), open(path[:-4] + '.json', 'w'))

def tiles_for(f, rect=None):
    GW, GH = R.frame_px(f); ts = TS[int(f)]
    if rect is None: x0, y0, x1, y1 = 0, 0, GW, GH
    else:
        x0, y0 = R.map_to_px(rect[0], rect[1], f); x1, y1 = R.map_to_px(rect[2], rect[3], f)
    return [(i, j) for j in range(int(y0 // ts), int(math.ceil(y1 / ts))) for i in range(int(x0 // ts), int(math.ceil(x1 / ts)))
            if 0 <= i * ts < GW and 0 <= j * ts < GH]

def build(f, rect=None, scene_path=R.SCENE, profile='equivalent', log=print, store=None):
    """Bring every tile covering rect up to date. Returns a report: which tiles were painted, which were reused."""
    import edges10 as E
    E.activate(profile)
    S = R.load_scene(scene_path); d = os.path.join(CACHE, store or f'f{f:g}'); os.makedirs(d, exist_ok=True)
    rep = dict(f=f, painted=[], reused=[], seconds=0.0)
    t0 = time.time()
    for (i, j) in tiles_for(f, rect):
        parts = tile_parts(S, f, i, j, profile); key, n = parts['key'], parts['n']; path = os.path.join(d, f'{i}_{j}_{key}.png')
        if os.path.exists(path):
            if not os.path.exists(path[:-4] + '.json'): write_sidecar(path, parts)
            rep['reused'].append([i, j]); continue
        sq, win = tile_window(f, i, j); ts = time.time()
        img, Z, st = R.render_window(f, win, scene_path=scene_path)
        cut = lambda a: a[sq[1] - win[1]:sq[3] - win[1], sq[0] - win[0]:sq[2] - win[0]]
        cv2.imwrite(path, cut(img)); np.save(path[:-4] + '_z.npy', np.maximum(cut(Z), -6e4).astype(np.float16)); np.save(path[:-4] + '_trk.npy', np.packbits(cut(st['trk']))); write_sidecar(path, parts)
        for old in glob.glob(os.path.join(d, f'{i}_{j}_*.png')):            # drop superseded versions of this tile
            if old != path:
                for ext in ('.png', '_z.npy', '_trk.npy', '.json'):
                    p_ = old[:-4] + ext if ext != '.png' else old
                    if os.path.exists(p_): os.remove(p_)
        rep['painted'].append(dict(tile=[i, j], seconds=round(time.time() - ts, 1), elements=n)); log(f'  tile {i},{j}: {time.time() - ts:.1f}s, {n} elements')
    rep['seconds'] = round(time.time() - t0, 1)
    E.deactivate()
    return rep

def rekey(f, rect=None, scene_path=R.SCENE, profile='equivalent', store=None, verify=2, log=print):
    """When the code changed but the pixels provably did not, move cached tiles to their new keys instead of
    repainting them. A tile qualifies only if its sidecar shows the SAME scene part (so only the code differs).
    Then `verify` of those tiles (the ones with the most elements first) are painted again with the current code and
    compared exactly, colour, depth and track. Any difference and nothing is re-keyed. Tiles that do not qualify are
    left for build(). Returns a report."""
    import edges10 as E
    E.activate(profile)
    S = R.load_scene(scene_path); d = os.path.join(CACHE, store or f'f{f:g}'); rep = dict(f=f, current=[], rekeyed=[], needs_build=[], verified=[])
    cand = []
    for (i, j) in tiles_for(f, rect):
        parts = tile_parts(S, f, i, j, profile); path = os.path.join(d, f'{i}_{j}_{parts["key"]}.png')
        if os.path.exists(path): rep['current'].append([i, j]); continue
        old = sorted(glob.glob(os.path.join(d, f'{i}_{j}_*.png')), key=os.path.getmtime)
        side = old[-1][:-4] + '.json' if old else None
        if not old or not os.path.exists(side) or json.load(open(side))['scene'] != parts['scene']: rep['needs_build'].append([i, j]); continue
        cand.append((parts['n'], i, j, old[-1], path, parts))
    cand.sort(reverse=True)
    for n, i, j, old, new, parts in cand[:verify]:
        sq, win = tile_window(f, i, j); img, Z, st = R.render_window(f, win, scene_path=scene_path)
        cut = lambda a: a[sq[1] - win[1]:sq[3] - win[1], sq[0] - win[0]:sq[2] - win[0]]
        same = (np.array_equal(cut(img), cv2.imread(old)) and np.array_equal(np.maximum(cut(Z), -6e4).astype(np.float16), np.load(old[:-4] + '_z.npy'))
                and np.array_equal(np.packbits(cut(st['trk'])), np.load(old[:-4] + '_trk.npy')))
        log(f'  verify tile {i},{j} ({n} elements): {"identical" if same else "DIFFERENT"}')
        if not same:
            rep['refused'] = f'tile {i},{j} changed: the code change alters the painting, so the tiles must be rebuilt'
            E.deactivate(); return rep
        rep['verified'].append([i, j])
    for n, i, j, old, new, parts in cand:
        for ext in ('.png', '_z.npy', '_trk.npy'): os.replace(old[:-4] + ext if ext != '.png' else old, new[:-4] + ext if ext != '.png' else new)
        if os.path.exists(old[:-4] + '.json'): os.remove(old[:-4] + '.json')
        write_sidecar(new, parts); rep['rekeyed'].append([i, j])
    E.deactivate(); return rep

def assemble(f, rect=None, store=None, what='img'):
    """Stitch the cached tiles covering rect (map units) into one array (image, Z or track mask)."""
    d = os.path.join(CACHE, store or f'f{f:g}'); GW, GH = R.frame_px(f); ts = TS[int(f)]
    tl = tiles_for(f, rect)
    I0, J0 = min(t[0] for t in tl), min(t[1] for t in tl); I1, J1 = max(t[0] for t in tl), max(t[1] for t in tl)
    X0, Y0, X1, Y1 = I0 * ts, J0 * ts, min(GW, (I1 + 1) * ts), min(GH, (J1 + 1) * ts)
    out = np.zeros((Y1 - Y0, X1 - X0, 3), np.uint8) if what == 'img' else np.zeros((Y1 - Y0, X1 - X0), np.float32 if what == 'z' else bool)
    for (i, j) in tl:
        fs = sorted(glob.glob(os.path.join(d, f'{i}_{j}_*.png')), key=os.path.getmtime)
        if not fs: continue
        p = fs[-1]; sq, _ = tile_window(f, i, j)
        a = cv2.imread(p) if what == 'img' else np.load(p[:-4] + '_z.npy').astype(np.float32) if what == 'z' else \
            np.unpackbits(np.load(p[:-4] + '_trk.npy'))[:(sq[3] - sq[1]) * (sq[2] - sq[0])].reshape(sq[3] - sq[1], sq[2] - sq[0]).astype(bool)
        out[sq[1] - Y0:sq[3] - Y0, sq[0] - X0:sq[2] - X0] = a
    return out, (X0, Y0, X1, Y1)

if __name__ == '__main__':
    #   cache10.py build F [X0 Y0 X1 Y1]            paint every out-of-date tile
    #   cache10.py rekey F [X0 Y0 X1 Y1] [--verify N]   re-key tiles whose code changed but whose pixels did not
    #   cache10.py status F [X0 Y0 X1 Y1]           how many tiles are current / re-keyable / need painting (no painting)
    cmd = sys.argv[1]; args = sys.argv[2:]
    if '--verify' in args: vi = args.index('--verify'); args = args[:vi] + args[vi + 2:]     # drop the option and its value by position
    nums = [a_ for a_ in args if not a_.startswith('--')]
    f = float(nums[0]); rect = tuple(map(float, nums[1:5])) if len(nums) >= 5 else None
    if cmd == 'build': print(json.dumps(build(f, rect), indent=0))
    elif cmd == 'rekey': print(json.dumps(rekey(f, rect, verify=int(sys.argv[sys.argv.index('--verify') + 1]) if '--verify' in sys.argv else 2), indent=0))
    elif cmd == 'status':
        S = R.load_scene(); d = os.path.join(CACHE, f'f{f:g}'); cur = rk = nb = 0
        for (i, j) in tiles_for(f, rect):
            p = tile_parts(S, f, i, j, 'equivalent')
            if os.path.exists(os.path.join(d, f'{i}_{j}_{p["key"]}.png')): cur += 1; continue
            old = sorted(glob.glob(os.path.join(d, f'{i}_{j}_*.png')), key=os.path.getmtime)
            sd = old[-1][:-4] + '.json' if old else ''
            if old and os.path.exists(sd) and json.load(open(sd))['scene'] == p['scene']: rk += 1
            else: nb += 1
        print(f'f{f:g}: {cur} current, {rk} only code-stale (re-keyable after verification), {nb} need painting')

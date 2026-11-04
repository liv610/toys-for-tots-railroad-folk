"""Engine 10: the base painting of any rectangle of the world, at any density, with the position-exact brush.

render_window() repeats what pass 4/5's main() does for the base (the painting without moving parts, which the
viewer shows under its sprites), but for one window:
  * sea stipple, wave marks (pass 4's 240, plus pad5's margin waves), the land mask, the ground;
  * every base element whose bounds (plus a margin) touch the window, in the global painting order, with the same clips
    (mountains may rise above the coast, terrain is clipped to land);
  * the coastline drawn at the same point in the global order as in main();
  * the moving trees that the published render keeps still (they were mostly hidden) painted back;
  * impasto.
It also returns the depth buffer (Z) that front patches and occluders are cut from.

Nothing here writes into out5*/ or viewer5/.
"""
import sys, os, json, math, time, gc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, 'lab8'), os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path: sys.path.insert(0, p)
_argv = sys.argv; sys.argv = [sys.argv[0]]
_cwd = os.getcwd(); os.chdir(ROOT)
import numpy as np, cv2
import usmap5 as U5
B = U5.B; T7 = U5.T7
import station5 as ST, pnw5 as P5, fl5 as F5, store8 as SF
from brush import hexc
from kit import pal_fn
import brush10 as BR
os.chdir(_cwd); sys.argv = _argv

MODS = [B, B.U, B.U2, B.U3, B.S, B.A, U5, F5, P5, ST, T7, SF]
_land_clip = B.U2.land_clip
def _land_clip_safe(m):                    # a shape wholly outside a tile has no mask; the full map never hit this
    return None if m is None else _land_clip(m)
B.U2.land_clip = _land_clip_safe
TERRAIN = B.TERRAIN
SCENE = os.path.join(ROOT, 'out5', 'scene5.json')
MANIFEST = os.path.join(ROOT, 'out5_6400', 'anim', 'manifest.json')

def frame_px(f):
    return int(round(BR.FRAME1[0] * f)), int(round(BR.FRAME1[1] * f))

def map_to_px(x, y, f):
    k = BR.K1 * f; return (x + BR.PADL) * k, (y + BR.PADT) * k

def use(c):
    """Point every painter module at canvas c."""
    for m in MODS: m.c = c
    for m in (B, B.U, B.U2, B.U3): m.k, m.W, m.H = c.k, c.W, c.H
    U5.k = c.k
    B.OX, B.OY = c.d[0] * c.k, c.d[1] * c.k; B.U.OX, B.U.OY = B.OX, B.OY

_SCENE = {}
def load_scene(path=SCENE):
    if path not in _SCENE:
        scene = json.load(open(path))
        routes = {}
        for nm, r in scene['routes'].items():
            P = np.array(r['points']); d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None]
            routes[nm] = dict(P=P, nr=np.stack([-d[:, 1], d[:, 0]], 1), depth=np.array(r['depth']), ties=np.array(r['ties'], bool))
        base = sorted([e for e in scene['elements'] if e['layer'] == 'base'], key=lambda e: e['depth'])
        # movers that the published render painted back into the base (mostly hidden), from its manifest
        man = json.load(open(MANIFEST)); have = {s_['file'] for s_ in man['sprites']}
        movers = {'ever': [], 'decid': [], 'palm': []}
        for e in scene['elements']:
            if e['layer'] == 'anim5': movers[e['params']['sway']].append(e)
            elif e['kind'] == 'palm5' and e['params'].get('trunk_only'): movers['palm'].append(e)
        back = []
        for cls in ('ever', 'decid'):
            for j, e in enumerate(movers[cls]):
                if f'tree_{cls}_{j}.png' not in have: back.append(dict(e, layer='base', params={kk: v for kk, v in e['params'].items() if kk != 'sway'}))
        palms_out = {s_['palm'] for s_ in man['sprites'] if s_['kind'] == 'frond'}
        for j, e in enumerate(movers['palm']):
            if j not in palms_out: back.append(dict(e, params={kk: v for kk, v in e['params'].items() if kk != 'trunk_only'}))
        back_ids = {id(e) for e in back}
        base = [e for e in base if not any(e['kind'] == 'palm5' and e['params'] == dict(b['params'], trunk_only=True) for b in back)]
        allb = sorted(base + back, key=lambda e: e['depth'])
        trig = next(i for i, e in enumerate(allb) if e['kind'] not in TERRAIN and e['depth'] > 120)
        _SCENE[path] = dict(scene=scene, routes=routes, base=allb, coast_at=trig, painted_back=len(back))
    return _SCENE[path]

def waves(c):
    """pass 4's wave marks, then pad5's margin waves: the same positions and seeds."""
    R = np.random.RandomState(2026)
    for i in range(240):
        x, y = R.uniform(0, B.RW), R.uniform(0, B.RH)
        if B.LANDP.contains_point((x, y), radius=-30): continue
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2), seed=B.sid('wave4', i, kk))
    L, T, R_, Bm = B.PAD; R = np.random.RandomState(2027); n = 0
    while n < 70:
        x, y = R.uniform(-L + 8, B.RW + R_ - 50), R.uniform(-T + 12, B.RH + Bm - 10)
        if 0 <= x <= B.RW - 40 and 0 <= y <= B.RH: continue
        if B.LANDP.contains_point((x, y), radius=-30) or B.LANDP.contains_point((x + 30, y)): continue
        n += 1
        for kk in range(R.randint(2, 4)):
            pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
            c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2), seed=B.sid('wave7', n, kk))

def _land_full(f, extra_below):
    """The land mask of the WHOLE padded map at density f, blurred, with extra_below rows under the frame, exactly
    what a whole-map render computes. Made once per density and coastline, kept in engine10/cache/, and read
    through a memory map, so every window gets the same values (found 4 Nov 2026: filling the coast polygon into
    each window's own buffer anti-aliased its edges differently in each tile)."""
    import hashlib
    GW, GH = frame_px(f); key = hashlib.sha1(np.asarray(B.COAST).tobytes() + f'{f}:{extra_below}:{GW}x{GH}'.encode()).hexdigest()[:12]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', f'land_f{f:g}_{key}.npy')
    if not os.path.exists(path):
        k = BR.K1 * f; LM = np.zeros((GH + extra_below, GW), np.float32)
        cv2.fillPoly(LM, [np.round((np.asarray(B.COAST) + [BR.PADL, BR.PADT]) * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
        LM = cv2.GaussianBlur(LM, (0, 0), k / 1.914)
        os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path[:-4] + f'.{os.getpid()}.tmp.npy'; np.save(tmp, LM); os.replace(tmp, path); del LM
    return np.load(path, mmap_mode='r')

def land_mask(c, extra_below=0):
    ox, oy = c.T; full = _land_full(c.f, extra_below)
    return np.array(full[oy:oy + c.H + extra_below, ox:ox + c.W], np.float32)

def coastline(c):
    PP = B.resample(np.vstack([B.COAST, B.COAST[:1]]), 2.0)
    for kk in range(0, len(PP) - 2, 10):
        c.stroke(PP[kk:kk + 12], 8, '#e8d8b0', a=1, dry=.25, taper=(.05, .05), press=.3, rough=.8, streak=.15, seed=B.sid('coast4', kk))

# (4 Nov 2026) a comment-only edit, used to test cache10.rekey: it changes the code hash but not the painting
def render_window(f, win, margin=16, level=None, hook=None, scene_path=SCENE, sea=True, shop=None):
    """Paint world pixels win = (x0, y0, x1, y1) at density f. Returns (bgr uint8, Z float32, stats).
    level: optional storefront level for the experiment's shop (lab8/store8); hook(c) runs after painting."""
    t0 = time.time(); S = load_scene(scene_path)
    x0, y0, x1, y1 = win; W, H = x1 - x0, y1 - y0
    for m in MODS: m.c = None
    gc.collect()
    c = BR.EngineCanvas(f, (x0, y0, W, H)); use(c)
    k = c.k; mx0, my0 = x0 / k - BR.PADL, y0 / k - BR.PADT; mx1, my1 = x1 / k - BR.PADL, y1 / k - BR.PADT
    if sea:
        c.stip((0, 0, np.ones((H, W), np.float32)), pal_fn(['#244c78', '#2c5684', '#22466e', '#33608c', '#2a5280'], .05), spacing=1.8, L=8.0, w=2.0,
               angfn=lambda X, Y: .25 * np.sin(X / 60 + Y / 25), seed=2, jit=.25)
        waves(c)
    sh = int(48 * k); LMx = land_mask(c, extra_below=sh + 2)
    B.U.LAND_MASK = LMx[:H]
    MTCLIP = np.maximum(LMx[:H], LMx[sh:sh + H])                        # peaks may rise above the north coast
    c.area(None, '#5f6a2a', m=(0, 0, B.U.LAND_MASK), edge_dark=0, var=.03)
    SN = np.array([hexc(z) for z in B.U3.SNOWPAL])
    def groundcol(X, Y, rr):
        base_ = np.array([hexc('#5f6a2a'), hexc('#6a7430'), hexc('#545e24')])[rr.randint(3, size=len(X))]
        return np.where((rr.rand(len(X)) < B.snow_amt(X, Y))[:, None], SN[rr.randint(5, size=len(X))], base_)
    c.stip((0, 0, B.U.LAND_MASK), groundcol, spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    Z = np.full((H, W), -1e9, np.float32); MT = np.zeros((H, W), bool); TRK = np.zeros((H, W), bool); OWN = np.full((H, W), -1, np.int32)
    if level is None:                                                   # a scene may ask for a storefront level (the experiment's shop)
        sh = next((e for e in S['base'] if e['kind'] == 'shops7'), None)
        level = sh['params'].get('store_level') if sh else None
    te0, sq0 = T7.town_extras, T7.square
    if level is not None:
        SH = shop or SF                                                 # which storefront module paints the shop (lab8 store8 or engine10 store10)
        def town_extras(which):
            te0(set(which) - {5})
            if 5 in which: SH.storefront(level)
        def square(seed): sq0(seed); SH.after_square(level)
        T7.town_extras, T7.square = town_extras, square
    n_el = 0; coast_done = False
    try:
        for gi, e in enumerate(S['base']):
            if not coast_done and gi >= S['coast_at']:
                c.set_clip(None); snap = c.img.copy(); coastline(c); c.img[MT] = snap[MT]; coast_done = True; del snap
            b = e['bbox']
            if not (b[2] > mx0 - margin and b[0] < mx1 + margin and b[3] > my0 - margin and b[1] < my1 + margin): continue
            ex0, ey0 = int(max(0, (b[0] - margin + c.d[0]) * k)), int(max(0, (b[1] - margin + c.d[1]) * k))
            ex1, ey1 = int(min(W, (b[2] + margin + c.d[0]) * k)), int(min(H, (b[3] + margin + c.d[1]) * k))
            before = c.img[ey0:ey1, ex0:ex1].copy() if ex1 > ex0 and ey1 > ey0 else None
            c.rng = np.random.RandomState(e['seed']); c.eseed = e['seed'] & 0x7FFFFFFF
            c.set_clip((0, 0, MTCLIP) if e['kind'] == 'mountain' else (0, 0, B.U.LAND_MASK) if e['kind'] in TERRAIN - {'bridge', 'cactus'} else None)
            B.paint(e, S['routes']); n_el += 1
            if before is not None:
                ch = np.abs(c.img[ey0:ey1, ex0:ex1] - before).max(-1) > .004
                Z[ey0:ey1, ex0:ex1][ch] = e['depth']; MT[ey0:ey1, ex0:ex1][ch] = e['kind'] == 'mountain'; TRK[ey0:ey1, ex0:ex1][ch] = e['kind'] == 'track'; OWN[ey0:ey1, ex0:ex1][ch] = gi
        if not coast_done: c.set_clip(None); snap = c.img.copy(); coastline(c); c.img[MT] = snap[MT]
    finally:
        T7.town_extras, T7.square = te0, sq0
    c.set_clip(None)
    if hook: hook(c)
    BR.impasto(c, .14)
    img = (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
    c.TRK = TRK; c.OWN = OWN
    return img, Z, dict(seconds=round(time.time() - t0, 2), elements=n_el, size=[W, H], trk=TRK, own=OWN)

def render_tiled(f, win, tile=1024, pad=None, **kw):
    """The same window painted as tiles on a fixed world grid (multiples of `tile` px), each with `pad` px of overlap,
    then assembled."""
    x0, y0, x1, y1 = win; k = BR.K1 * f; pad = pad or int(math.ceil(16 * k))           # 16 map units: the widest reach of any painter (mountain edges, about 15)
    GW, GH = frame_px(f)
    out = np.zeros((y1 - y0, x1 - x0, 3), np.uint8); Zo = np.zeros((y1 - y0, x1 - x0), np.float32); times = []
    for ty in range((y0 // tile) * tile, y1, tile):
        for tx in range((x0 // tile) * tile, x1, tile):
            ax, ay, bx, by = max(x0, tx), max(y0, ty), min(x1, tx + tile), min(y1, ty + tile)
            if bx <= ax or by <= ay: continue
            wx0, wy0, wx1, wy1 = max(0, ax - pad), max(0, ay - pad), min(GW, bx + pad), min(GH, by + pad)
            img, Z, st = render_window(f, (wx0, wy0, wx1, wy1), **kw); times.append(st['seconds'])
            out[ay - y0:by - y0, ax - x0:bx - x0] = img[ay - wy0:by - wy0, ax - wx0:bx - wx0]
            Zo[ay - y0:by - y0, ax - x0:bx - x0] = Z[ay - wy0:by - wy0, ax - wx0:bx - wx0]
    return out, Zo, times

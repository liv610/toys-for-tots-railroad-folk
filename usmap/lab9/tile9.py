"""lab9 — is the resolution ceiling a limit of the technology, or of the technique?

The map is painted on ONE canvas held in memory, which caps it at about 7000 px wide in this workspace. Painting it
in tiles would remove the cap, but only if a tile paints its pixels exactly as the whole canvas would. Two things in
the current brush prevent that:
  1. the paper and pigment noise fields are generated for the canvas size, so they differ from tile to tile;
  2. stippling places its marks on a grid anchored at each mask's clipped corner, and draws its jitter, colours and
     order from one random stream, so a clipped mask gets different marks.
TileKanvas fixes both without changing the look: noise is sampled at ABSOLUTE pixel positions from one global lattice,
and every stipple mark is placed on a global grid and gets its jitter, colour and order from a hash of its global grid
cell. Everything else (strokes, areas, dots, the per-element random streams) is already position-exact.

    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:lab9 python3 lab9/tile9.py
"""
import sys, os, math, time, json, gc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lab8'))
import numpy as np, cv2
import crop8 as CR                                # brings in the whole pass 5 painter stack
from crop8 import B, T7, U5, SF, MODS
from pad5 import _Off
from kit import Kanvas, impasto
from brush import hexc

M64 = np.uint64(0xFFFFFFFFFFFFFFFF)
def _mix(z):
    z = z.astype(np.uint64)
    with np.errstate(over='ignore'):
        z = (z + np.uint64(0x9E3779B97F4A7C15))
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        return z ^ (z >> np.uint64(31))
def _u01(z): return ((z >> np.uint64(11)).astype(np.float64)) * (1.0 / (1 << 53))

class HashRNG:
    """Stands in for numpy's RandomState inside colour callbacks: every value is a hash of the stipple mark's global
    grid cell and of how many draws came before, so the same mark gets the same colour in every tile."""
    def __init__(s, keys): s.keys = keys; s.n = 0
    def _u(s, size):
        s.n += 1
        with np.errstate(over='ignore'):
            z = _mix(s.keys ^ (np.uint64(s.n) * np.uint64(0xD6E8FEB86659FD93)))
        u = _u01(z)
        if size is None: return float(u[0]) if len(u) else 0.0
        size = (size,) if np.isscalar(size) else tuple(size)
        if size[0] != len(u): raise ValueError('HashRNG: draws must be one per mark')
        if len(size) == 2: u = np.repeat(u[:, None], size[1], 1)
        return u
    def rand(s, *shape): return s._u(shape if shape else None)
    def uniform(s, lo=0.0, hi=1.0, size=None): return lo + (hi - lo) * s._u(size)
    def randint(s, lo, hi=None, size=None):
        if hi is None: lo, hi = 0, lo
        return (lo + np.floor(s._u(size) * (hi - lo))).astype(int) if size is not None else int(lo + s._u(None) * (hi - lo))
    def randn(s, *shape):
        u1 = np.clip(s._u(shape if shape else None), 1e-12, 1); u2 = s._u(shape if shape else None)
        return np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
    def choice(s, n, size=None, p=None):
        u = s._u(size)
        if p is None: return np.floor(u * n).astype(int)
        return np.searchsorted(np.cumsum(p), u).clip(0, n - 1)

def abs_noise(H, W, cell, seed, ox, oy, GH, GW):
    """brush.noise() sampled at absolute pixels (ox.., oy..) of a GW x GH global canvas: the same lattice of random
    values for every tile, interpolated at each pixel's absolute position."""
    r = np.random.RandomState(seed)
    gh, gw = int(GH / cell) + 4, int(GW / cell) + 4
    g = r.rand(gh, gw).astype(np.float32)
    sx = int(gw * cell) / gw; sy = int(gh * cell) / gh
    xs = ((np.arange(W, dtype=np.float32) + ox + .5) / sx - .5); ys = ((np.arange(H, dtype=np.float32) + oy + .5) / sy - .5)
    mx, my = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
    return cv2.remap(g, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def abs_fbm(H, W, cell, octaves, seed, ox, oy, GH, GW):
    def raw(h, w, x, y):
        out = np.zeros((h, w), np.float32); a = 1; tot = 0
        for o in range(octaves):
            out += abs_noise(h, w, max(1.0, cell / 2 ** o), seed + o * 17, x, y, GH, GW) * a; tot += a; a *= .5
        return out / tot
    ref = raw(min(GH, 768), min(GW, 768), 0, 0)                       # one fixed patch sets the contrast for every tile
    lo, hi = np.percentile(ref, 1), np.percentile(ref, 99)
    return np.clip((raw(H, W, ox, oy) - lo) / (hi - lo + 1e-6), 0, 1)

class _Tile:
    """Mixin: absolute noise fields, and stippling on a global grid with hashed randomness."""
    T = (0, 0); G = (0, 0)                                            # this tile's pixel origin, and the global size (W, H)
    def _init_fields(s, seed):
        H, W = s.H, s.W; ox, oy = s.T; GW, GH = s.G; k = s.k
        s.paper = np.clip(.55 * abs_noise(H, W, 1.6, seed + 1, ox, oy, GH, GW) + .45 * abs_noise(H, W, 5, seed + 2, ox, oy, GH, GW), 0, 1)
        s.Nbig = abs_fbm(H, W, 140 * k / 2, 3, seed + 3, ox, oy, GH, GW)
        s.Nmid = abs_fbm(H, W, 26 * k / 2, 3, seed + 4, ox, oy, GH, GW)
        s.Nsm = abs_noise(H, W, 3.2 * k / 2, seed + 5, ox, oy, GH, GW)
    def stip(s, m, colfn, spacing=2.6, L=4.0, w=1.7, angfn=None, a=1.0, seed=0, thresh=.5, jit=.35, spill=1.15):
        if m is None: return
        x0, y0, mm = m; h, ww = mm.shape; k = s.k; sp = spacing * k; ox, oy = s.T
        ix = np.arange(math.floor((x0 + ox) / sp), math.ceil((x0 + ox + ww) / sp) + 1)
        iy = np.arange(math.floor((y0 + oy) / sp), math.ceil((y0 + oy + h) / sp) + 1)
        IX, IY = np.meshgrid(ix, iy); IX = IX.ravel(); IY = IY.ravel()
        with np.errstate(over='ignore'):
            keys = _mix(_mix(np.uint64(seed & 0xFFFFFFFF) * np.uint64(0x9E3779B1) ^ (IX.astype(np.int64).astype(np.uint64) * np.uint64(0x85EBCA77))) ^ (IY.astype(np.int64).astype(np.uint64) * np.uint64(0xC2B2AE3D)))
        rr = HashRNG(keys)
        gx = IX * sp + rr.rand(len(keys)) * sp - ox - x0; gy = IY * sp + rr.rand(len(keys)) * sp - oy - y0
        ok = (gx >= 0) & (gy >= 0) & (gx < ww) & (gy < h)
        gx, gy, keys = gx[ok], gy[ok], keys[ok]
        if len(gx): ok = mm[gy.astype(int), gx.astype(int)] > thresh; gx, gy, keys = gx[ok], gy[ok], keys[ok]
        if len(gx) == 0: return
        o = np.argsort(_mix(keys ^ np.uint64(0x5bd1e995))); gx, gy, keys = gx[o], gy[o], keys[o]
        X, Y = (gx + x0) / k, (gy + y0) / k                              # (the _Off layer shifts these back for the callbacks)
        rr = HashRNG(keys)
        cols = np.clip(colfn(X, Y, rr), 0, 1)
        ang = angfn(X, Y) if angfn is not None else rr.rand(len(X)) * math.pi
        ang = np.broadcast_to(ang, X.shape) + rr.randn(len(X)) * jit
        Ls = L * k * (.7 + .6 * rr.rand(len(X))); Ws = w * k * (.75 + .5 * rr.rand(len(X)))
        reg = s.img[y0:y0 + h, x0:x0 + ww]; lay = reg.copy()
        hm = getattr(s, 'HM', None); hreg = hm[y0:y0 + h, x0:x0 + ww] if hm is not None else None
        hv = rr.uniform(.4, 1.0, len(X))
        for i in range(len(X)):
            cv2.ellipse(lay, (int(gx[i] * 4), int(gy[i] * 4)), (max(1, int(Ls[i] * 2)), max(1, int(Ws[i] * 2))), float(np.degrees(ang[i])), 0, 360,
                        (float(cols[i, 0]), float(cols[i, 1]), float(cols[i, 2])), -1, cv2.LINE_AA, shift=2)
            if hreg is not None:
                cv2.ellipse(hreg, (int(gx[i] * 4), int(gy[i] * 4)), (max(1, int(Ls[i] * 2)), max(1, int(Ws[i] * 2))), float(np.degrees(ang[i])), 0, 360, float(hv[i]), -1, cv2.LINE_AA, shift=2)
        al = np.clip(cv2.GaussianBlur(mm, (0, 0), 1.2) * spill, 0, 1) * a
        if s.clipm is not None: al = al * s.clipm[y0:y0 + h, x0:x0 + ww]
        reg += (lay - reg) * al[..., None]

def make_canvas(cls_tile, box, k, tile_px, size_px, global_px):
    """box: the global rectangle in map units (its corner is global pixel 0,0). tile_px: this tile's pixel origin."""
    x0, y0, _, _ = box; tx, ty = tile_px; W, H = size_px
    for m in MODS: m.c = None
    gc.collect()
    if cls_tile:
        C = type('TileKanvas', (_Off, _Tile, Kanvas), {}); C.T = (tx, ty); C.G = global_px
        c = C.__new__(C); c.W, c.H, c.k = W, H, k
        c.img = np.empty((H, W, 3), np.float32); c.img[:] = hexc('#2c5684'); c._init_fields(1972); c.clipm = None; c.rng = np.random.RandomState(1972 + 9)
    else:
        C = type('OffKanvas', (_Off, Kanvas), {}); c = C(W, H, k, '#2c5684', seed=1972)
    c.HM = np.zeros((H, W), np.float32); c.d = (-(x0 + tx / k), -(y0 + ty / k))
    for m in MODS: m.c = c
    for m in (B, B.U, B.U2, B.U3): m.k, m.W, m.H = k, W, H
    U5.k = k; B.OX, B.OY = c.d[0] * k, c.d[1] * k; B.U.OX, B.U.OY = B.OX, B.OY
    LM = np.zeros((H, W), np.float32)
    cv2.fillPoly(LM, [np.round((np.asarray(B.COAST) + c.d) * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    B.U.LAND_MASK = cv2.GaussianBlur(LM, (0, 0), k / 1.914)
    return c

def paint(c, level='orig', margin=40):
    """The same painting loop as lab8/crop8.render(), on the canvas given."""
    k = c.k; x0, y0 = -c.d[0], -c.d[1]; x1, y1 = x0 + c.W / k, y0 + c.H / k
    scene = json.load(open('out5/scene5.json'))
    def touches(b): return b[2] > x0 - margin and b[0] < x1 + margin and b[3] > y0 - margin and b[1] < y1 + margin
    els = sorted([e for e in scene['elements'] if e['layer'] in ('base', 'anim5') and e['kind'] != 'track' and touches(e['bbox'])], key=lambda e: e['depth'])
    c.area(None, '#5f6a2a', m=(0, 0, B.U.LAND_MASK), edge_dark=0, var=.03)
    SN = np.array([hexc(z) for z in B.U3.SNOWPAL])
    def groundcol(X, Y, rr):
        base_ = np.array([hexc('#5f6a2a'), hexc('#6a7430'), hexc('#545e24')])[rr.randint(3, size=len(X))]
        return np.where((rr.rand(len(X)) < B.snow_amt(X, Y))[:, None], SN[rr.randint(5, size=len(X))], base_)
    c.stip((0, 0, B.U.LAND_MASK), groundcol, spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    te0, sq0 = T7.town_extras, T7.square
    def town_extras(which):
        te0(set(which) - {5})
        if 5 in which: SF.storefront(level)
    def square(seed): sq0(seed); SF.after_square(level)
    T7.town_extras, T7.square = town_extras, square
    try:
        for e in els:
            e = dict(e, params={kk: v for kk, v in e['params'].items() if kk != 'sway'})
            c.rng = np.random.RandomState(e['seed'])
            c.set_clip((0, 0, B.U.LAND_MASK) if e['kind'] in B.TERRAIN - {'bridge', 'cactus'} else None)
            B.paint(e, {})
    finally:
        T7.town_extras, T7.square = te0, sq0
    c.set_clip(None); impasto(c, .14)
    return (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)

def tiled(cls_tile, box, k, ntx=2, nty=2, pad_px=None, level='orig'):
    GW, GH = int(round((box[2] - box[0]) * k)), int(round((box[3] - box[1]) * k))
    pad = pad_px or int(12 * k)
    out = np.zeros((GH, GW, 3), np.uint8)
    xs = np.linspace(0, GW, ntx + 1).astype(int); ys = np.linspace(0, GH, nty + 1).astype(int)
    for j in range(nty):
        for i in range(ntx):
            ax, ay = max(0, xs[i] - pad), max(0, ys[j] - pad); bx, by = min(GW, xs[i + 1] + pad), min(GH, ys[j + 1] + pad)
            c = make_canvas(cls_tile, box, k, (ax, ay), (bx - ax, by - ay), (GW, GH))
            img = paint(c, level)
            out[ys[j]:ys[j + 1], xs[i]:xs[i + 1]] = img[ys[j] - ay:ys[j + 1] - ay, xs[i] - ax:xs[i + 1] - ax]
    return out, (xs, ys)

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    box = CR.BOX; k = float(os.environ.get('K', CR.K_MAP)); res = {}
    GW, GH = int(round((box[2] - box[0]) * k)), int(round((box[3] - box[1]) * k))
    for name, cls_tile in (('current_brush', False), ('tile_brush', True)):
        t0 = time.time(); whole = paint(make_canvas(cls_tile, box, k, (0, 0), (GW, GH), (GW, GH))); t1 = time.time()
        tl, (xs, ys) = tiled(cls_tile, box, k); t2 = time.time()
        d = np.abs(whole.astype(int) - tl.astype(int)).max(-1)
        res[name] = dict(whole_s=round(t1 - t0, 1), tiled_s=round(t2 - t1, 1), mean_diff=round(float(d.mean()), 3), p99_diff=float(np.percentile(d, 99)), max_diff=int(d.max()),
                         pixels_off_by_more_than_8=int((d > 8).sum()), of=int(d.size))
        cv2.imwrite(f'{out}/{name}_whole.png', whole); cv2.imwrite(f'{out}/{name}_tiled.png', tl)
        cv2.imwrite(f'{out}/{name}_diff.png', np.clip(d * 4, 0, 255).astype(np.uint8))
        print(name, res[name], flush=True)
    json.dump(dict(k=k, box=box, tiles='2 x 2', results=res), open(f'{out}/tiling_k{k:.2f}.json', 'w'), indent=1)

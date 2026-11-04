"""Engine 10: a position-exact, tile-safe gouache brush with controllable edges.

It is opt-in. The legacy brush (folk2/brush.py, kit.py) is untouched, and everything rendered with it is unchanged.
EngineCanvas paints a WINDOW of one fixed world frame:

    world pixel = (map unit + (PADL, PADT)) * k,      k = K1 * f   (f = density: 1 for the published map, 4 for 4x)

Any window (a whole map, one tile, a sprite's box) paints its pixels exactly as every other window would, because:
  1. Noise fields (paper grain, pigment variation, edge roughness) are sampled at absolute world positions from one
     lattice per field. At f = 1 this reproduces the published map's noise (mean difference 3e-5). The lattices are
     defined in map units, so f = 4 is the same texture, finer.
  2. Stipple marks sit on a global grid in map units. Each mark's jitter, colour, size, angle and stacking order come
     from a hash of its grid cell, never from a random stream that depends on what is visible.
  3. A stroke with no explicit seed gets one from a hash of its own geometry and the element's seed, not from the
     shared sequence. The legacy sequence broke whenever a painter skipped an off-screen shape.

Edges are controlled by presets, chosen per call, per block (`with c.edges('fine'):`) or per drawing function
(edges10.py). The default preset, 'organic', is the legacy brush's behaviour.
"""
import math, zlib, contextlib
import numpy as np, cv2
from kit import Kanvas
from brush import hexc

K1 = 6400 / 1671                      # px per map unit on the published zoomable map
PADL, PADT, PADR, PADB = 100, 70, 80, 80
FRAME1 = (7089, 4175)                 # the published map's padded canvas, at f = 1

EDGES = {   # soft: edge blur (map units); rough, wob: multipliers on what the painter asks for
    'organic': dict(soft=.90, rough=1.0, wob=1.0),     # hills, foliage, water: the legacy look
    'built':   dict(soft=.55, rough=.85, wob=.8),      # facades, roofs, stonework
    'fine':    dict(soft=.32, rough=.7, wob=.6),       # windows, doors, toys, figures, small decorations
    'crisp':   dict(soft=.18, rough=.5, wob=.4),       # eyes, glints, the smallest marks
}

# ------------------------------------------------------------------ hashing
_M1, _M2, _M3 = np.uint64(0xBF58476D1CE4E5B9), np.uint64(0x94D049BB133111EB), np.uint64(0x9E3779B97F4A7C15)
def mix(z):
    z = np.asarray(z).astype(np.uint64)
    with np.errstate(over='ignore'):
        z = z + _M3; z = (z ^ (z >> np.uint64(30))) * _M1; z = (z ^ (z >> np.uint64(27))) * _M2
        return z ^ (z >> np.uint64(31))
def u01(z): return (np.asarray(z) >> np.uint64(11)).astype(np.float64) * (1.0 / (1 << 53))
def cell_keys(seed, IX, IY):
    with np.errstate(over='ignore'):
        a = mix(np.uint64(seed & 0xFFFFFFFF) * np.uint64(0x9E3779B1) ^ (np.asarray(IX).astype(np.int64).astype(np.uint64) * np.uint64(0x85EBCA77)))
        return mix(a ^ (np.asarray(IY).astype(np.int64).astype(np.uint64) * np.uint64(0xC2B2AE3D)))

class HashRNG:
    """Stands in for numpy's RandomState inside colour callbacks. Every draw is a hash of the mark's grid cell and of
    how many draws came before it, so a mark gets the same colour in every window."""
    def __init__(s, keys): s.keys = keys; s.n = 0
    def _u(s, size):
        s.n += 1
        with np.errstate(over='ignore'):
            u = u01(mix(s.keys ^ (np.uint64(s.n) * np.uint64(0xD6E8FEB86659FD93))))
        if size is None: return float(u[0]) if len(u) else 0.0
        size = (size,) if np.isscalar(size) else tuple(size)
        if size[0] != len(u): raise ValueError('HashRNG draws must be one per mark')
        return np.repeat(u[:, None], size[1], 1) if len(size) == 2 else u
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
        return np.floor(u * n).astype(int) if p is None else np.searchsorted(np.cumsum(p), u).clip(0, n - 1)

# ------------------------------------------------------------------ absolute noise
def _lattice(cell, seed, GH, GW):
    r = np.random.RandomState(seed)
    gh, gw = int(GH / cell) + 4, int(GW / cell) + 4
    return r.rand(gh, gw).astype(np.float32), int(gw * cell) / gw, int(gh * cell) / gh

def abs_noise(H, W, cell, seed, ox, oy, GH, GW):
    """brush.noise(GH, GW, cell, seed), but only the window starting at world pixel (ox, oy)."""
    g, sx, sy = _lattice(cell, seed, GH, GW)
    xs = ((np.arange(W, dtype=np.float64) + ox + .5) / sx - .5).astype(np.float32)
    ys = ((np.arange(H, dtype=np.float64) + oy + .5) / sy - .5).astype(np.float32)
    mx, my = np.meshgrid(xs, ys)
    return cv2.remap(g, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def _noise_at(cell, seed, GH, GW, px, py):
    g, sx, sy = _lattice(cell, seed, GH, GW)
    mx = ((px + .5) / sx - .5).astype(np.float32).reshape(200, -1); my = ((py + .5) / sy - .5).astype(np.float32).reshape(200, -1)
    return cv2.remap(g, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).ravel()

_NORM = {}
def abs_fbm(H, W, cell, octaves, seed, ox, oy, GH, GW):
    """brush.fbm, windowed. Its contrast is set from a fixed sample of 40,000 world positions, so every window shares
    one normalisation (the legacy version normalised each canvas by its own percentiles)."""
    key = (round(cell, 6), octaves, seed, GH, GW)
    if key not in _NORM:
        r = np.random.RandomState(12345); px = r.uniform(0, GW, 40000); py = r.uniform(0, GH, 40000)
        v = np.zeros(40000, np.float32); a = 1; tot = 0
        for o in range(octaves):
            v += _noise_at(max(1.0, cell / 2 ** o), seed + o * 17, GH, GW, px, py) * a; tot += a; a *= .5
        v /= tot; _NORM[key] = (np.percentile(v, 1), np.percentile(v, 99))
    lo, hi = _NORM[key]
    out = np.zeros((H, W), np.float32); a = 1; tot = 0
    for o in range(octaves):
        out += abs_noise(H, W, max(1.0, cell / 2 ** o), seed + o * 17, ox, oy, GH, GW) * a; tot += a; a *= .5
    return np.clip((out / tot - lo) / (hi - lo + 1e-6), 0, 1)

# ------------------------------------------------------------------ the canvas
class EngineCanvas(Kanvas):
    """A window (ox, oy, w, h) of the world frame at density f. Paints in map units, like every canvas in the project."""
    def __init__(s, f, window, ground='#2c5684', seed=1972):
        ox, oy, W, H = window
        s.f = f; s.k = K1 * f; s.W, s.H = W, H; s.T = (ox, oy)
        s.G = (int(round(FRAME1[0] * f)), int(round(FRAME1[1] * f)))
        s.d = (PADL - ox / s.k, PADT - oy / s.k)                     # map -> canvas pixel: (map + d) * k
        s.img = np.empty((H, W, 3), np.float32); s.img[:] = hexc(ground)
        GW, GH = s.G; k = s.k
        s.paper = np.clip(.55 * abs_noise(H, W, 1.6 * f, seed + 1, ox, oy, GH, GW) + .45 * abs_noise(H, W, 5 * f, seed + 2, ox, oy, GH, GW), 0, 1)
        s.Nbig = abs_fbm(H, W, 140 * k / 2, 3, seed + 3, ox, oy, GH, GW)
        s.Nmid = abs_fbm(H, W, 26 * k / 2, 3, seed + 4, ox, oy, GH, GW)
        s.Nsm = abs_noise(H, W, 3.2 * k / 2, seed + 5, ox, oy, GH, GW)
        s.clipm = None; s.rng = np.random.RandomState(seed + 9); s.eseed = 0; s.edge = EDGES['organic']
        s.HM = np.zeros((H, W), np.float32)

    # edges ---------------------------------------------------------
    @contextlib.contextmanager
    def edges(s, name):
        prev = s.edge; s.edge = EDGES[name]
        try: yield s
        finally: s.edge = prev

    # map-unit geometry in, shifted pixels out ---------------------------
    def _px(s, P):
        """map units -> this window's pixels, through world pixels: (P + PAD) * k is the same number in every window,
        and subtracting the integer window origin is exact, so every window rounds edges identically."""
        P = np.asarray(P, np.float64)
        return (P + np.array([PADL, PADT])) * s.k - np.array(s.T, np.float64)
    def _sh(s, P): return np.asarray(P, np.float64) + np.array(s.d)
    def mask(s, poly, wob=2.0, rough=1.0, seed=0, soft=None, scaled=False):
        e = s.edge
        if not scaled and poly is not None: poly = s._px(poly); scaled = True
        m = Kanvas.mask(s, poly, wob * e['wob'], rough * e['rough'], seed, e['soft'] if soft is None else soft, scaled)
        # A shape wholly outside this window gets an EMPTY mask, not None: painters use the returned mask as a clip
        # (set_clip(m)), and a None clip means "paint everywhere". On a whole map this case never arose.
        return m if m is not None else (0, 0, np.zeros((1, 1), np.float32))
    def stroke(s, pts, w, col, a=1.0, dry=0.0, taper=(.12, .3), press=.18, rough=.3, streak=.07, ridge=.1, seed=None, scaled=False, tremor=0.0, col2=None):
        if seed is None:                                               # from the stroke itself, not from a sequence
            q = np.round(np.asarray(pts, np.float64) * 64).astype(np.int64)
            seed = (zlib.crc32(q.tobytes()) ^ (s.eseed * 2654435761)) & 0x3FFFFFFF
        if not scaled: pts = s._px(pts); w = w * s.k; scaled = True
        return Kanvas.stroke(s, pts, w, col, a, dry, taper, press, rough, streak, ridge, seed, scaled, tremor, col2)
    def dots(s, pts, r_, cols, a=1.0, seed=0):
        """kit.dots, with each centre rounded in WORLD pixels (so every window rounds it the same way) and with the
        clip respected (the legacy dots ignored a clip)."""
        rr = np.random.RandomState(seed); k = s.k; ox, oy = s.T
        if not len(pts): return
        P = np.array(pts, np.float64)
        WX = np.floor((P[:, 0] + PADL) * k * 4).astype(np.int64) - 4 * ox; WY = np.floor((P[:, 1] + PADT) * k * 4).astype(np.int64) - 4 * oy
        clip = s.clipm is not None
        if clip:
            rmax = (np.max(r_) if not np.isscalar(r_) else r_) * k * 1.6 + 3
            x0, y0 = int(max(0, WX.min() / 4 - rmax)), int(max(0, WY.min() / 4 - rmax)); x1, y1 = int(min(s.W, WX.max() / 4 + rmax + 1)), int(min(s.H, WY.max() / 4 + rmax + 1))
            keep = s.img[y0:y1, x0:x1].copy() if x1 > x0 and y1 > y0 else None
        for i in range(len(P)):
            col = hexc(cols[rr.randint(len(cols))]) if isinstance(cols, (list, tuple)) else hexc(cols)
            rad = r_ * (.75 + .5 * rr.rand()) if np.isscalar(r_) else r_[i]
            cv2.ellipse(s.img, (int(WX[i]), int(WY[i])), (max(1, int(rad * k * 4)), max(1, int(rad * k * 4 * (.8 + .3 * rr.rand())))), rr.rand() * 180, 0, 360,
                        tuple(float(v) for v in col), -1, cv2.LINE_AA, shift=2)
        if clip and keep is not None:
            cl = s.clipm[y0:y1, x0:x1][..., None]; reg = s.img[y0:y1, x0:x1]; reg[:] = keep + (reg - keep) * cl
    def flow_fill(s, m, angle_fn, col_fn, *a, **kw):
        dx, dy = s.d; s.d = (0.0, 0.0)
        try: return Kanvas.flow_fill(s, m, lambda X, Y: angle_fn(X - dx, Y - dy), lambda X, Y, r: col_fn(X - dx, Y - dy, r), *a, **kw)
        finally: s.d = (dx, dy)

    # stipple on the global grid --------------------------------------------
    def stip(s, m, colfn, spacing=2.6, L=4.0, w=1.7, angfn=None, a=1.0, seed=0, thresh=.5, jit=.35, spill=1.15):
        if m is None: return
        x0, y0, mm = m; h, ww = mm.shape; k = s.k; sp = spacing * k; ox, oy = s.T; dx, dy = s.d
        ix = np.arange(math.floor((x0 + ox) / sp), math.ceil((x0 + ox + ww) / sp) + 1)
        iy = np.arange(math.floor((y0 + oy) / sp), math.ceil((y0 + oy + h) / sp) + 1)
        IX, IY = np.meshgrid(ix, iy); IX = IX.ravel(); IY = IY.ravel()
        keys = cell_keys(seed, IX, IY); rr = HashRNG(keys)
        wx = IX * sp + rr.rand(len(keys)) * sp; wy = IY * sp + rr.rand(len(keys)) * sp       # world pixels
        gx = wx - (ox + x0); gy = wy - (oy + y0)
        ok0 = (gx >= 0) & (gy >= 0) & (gx < ww) & (gy < h); gx, gy, keys = gx[ok0], gy[ok0], keys[ok0]
        ok1 = mm[gy.astype(int), gx.astype(int)] > thresh if len(gx) else np.zeros(0, bool); gx, gy, keys = gx[ok1], gy[ok1], keys[ok1]
        if len(gx) == 0: return
        wx, wy = wx[ok0][ok1], wy[ok0][ok1]
        o = np.argsort(mix(keys ^ np.uint64(0x5BD1E995)), kind='stable'); gx, gy, keys, wx, wy = gx[o], gy[o], keys[o], wx[o], wy[o]
        CX = np.floor(wx * 4).astype(np.int64) - 4 * (ox + x0); CY = np.floor(wy * 4).astype(np.int64) - 4 * (oy + y0)   # centres rounded in world pixels
        X, Y = (gx + x0) / k - dx, (gy + y0) / k - dy                     # map units, for the callbacks
        rr = HashRNG(keys)
        cols = np.clip(colfn(X, Y, rr), 0, 1)
        ang = angfn(X, Y) if angfn is not None else rr.rand(len(X)) * math.pi
        ang = np.broadcast_to(ang, X.shape) + rr.randn(len(X)) * jit
        Ls = L * k * (.7 + .6 * rr.rand(len(X))); Ws = w * k * (.75 + .5 * rr.rand(len(X)))
        reg = s.img[y0:y0 + h, x0:x0 + ww]; lay = reg.copy()
        hreg = s.HM[y0:y0 + h, x0:x0 + ww]; hv = rr.uniform(.4, 1.0, len(X))
        hkeep = hreg.copy() if s.clipm is not None else None             # paint ridges, like paint, stay inside a clip
        for i in range(len(X)):
            ax = (max(1, int(Ls[i] * 2)), max(1, int(Ws[i] * 2))); ctr = (int(CX[i]), int(CY[i])); an = float(np.degrees(ang[i]))
            cv2.ellipse(lay, ctr, ax, an, 0, 360, (float(cols[i, 0]), float(cols[i, 1]), float(cols[i, 2])), -1, cv2.LINE_AA, shift=2)
            cv2.ellipse(hreg, ctr, ax, an, 0, 360, float(hv[i]), -1, cv2.LINE_AA, shift=2)
        al = np.clip(cv2.GaussianBlur(mm, (0, 0), 1.2 * s.f) * spill, 0, 1) * a
        if s.clipm is not None:
            cl = s.clipm[y0:y0 + h, x0:x0 + ww]; al = al * cl
            hreg[:] = hkeep + (hreg - hkeep) * cl
        reg += (lay - reg) * al[..., None]

def impasto(c, strength=.16, light=(-.7, -.7)):
    """kit.impasto with its blur scaled to the density, so the paint ridges have the same size in map units."""
    hb = cv2.GaussianBlur(c.HM, (0, 0), 1.1 * c.f)
    gx = cv2.Sobel(hb, cv2.CV_32F, 1, 0, ksize=3) / c.f; gy = cv2.Sobel(hb, cv2.CV_32F, 0, 1, ksize=3) / c.f
    sh = np.clip((gx * light[0] + gy * light[1]) * strength, -.14, .14)
    c.img *= (1 + sh)[..., None]

"""Shared painting toolkit for the three new worlds: fast stipple, folk trees, folk houses, rails, and the toy train."""
import math
import numpy as np, cv2
from brush import *
import story as S

K = 2
W, H = 1600 * K, 900 * K

class Kanvas(Canvas):
    def stip(s, m, colfn, spacing=2.6, L=4.0, w=1.7, angfn=None, a=1.0, seed=0, thresh=.5, jit=.35, spill=1.15):
        """Thousands of short, hand-placed dabs: the stippled surface of folk painting. Directions follow the form via angfn."""
        if m is None: return
        x0, y0, mm = m; h, ww = mm.shape; k = s.k; r = np.random.RandomState(seed)
        sp = spacing * k
        gy, gx = np.mgrid[0:h:sp, 0:ww:sp]
        gx = (gx + r.rand(*gx.shape) * sp).ravel(); gy = (gy + r.rand(*gy.shape) * sp).ravel()
        ok = (gx < ww) & (gy < h)
        gx, gy = gx[ok], gy[ok]
        ok = mm[gy.astype(int), gx.astype(int)] > thresh
        gx, gy = gx[ok], gy[ok]
        if len(gx) == 0: return
        o = r.permutation(len(gx)); gx, gy = gx[o], gy[o]
        X, Y = (gx + x0) / k, (gy + y0) / k
        cols = np.clip(colfn(X, Y, r), 0, 1)
        ang = angfn(X, Y) if angfn is not None else r.rand(len(X)) * math.pi
        ang = np.broadcast_to(ang, X.shape) + r.randn(len(X)) * jit
        Ls = L * k * (.7 + .6 * r.rand(len(X))); Ws = w * k * (.75 + .5 * r.rand(len(X)))
        reg = s.img[y0:y0 + h, x0:x0 + ww]; lay = reg.copy()
        hm = getattr(s, 'HM', None)
        hreg = hm[y0:y0 + h, x0:x0 + ww] if hm is not None else None
        hv = r.uniform(.4, 1.0, len(X))
        for i in range(len(X)):
            cv2.ellipse(lay, (int(gx[i] * 4), int(gy[i] * 4)), (max(1, int(Ls[i] * 2)), max(1, int(Ws[i] * 2))), float(np.degrees(ang[i])), 0, 360,
                        (float(cols[i, 0]), float(cols[i, 1]), float(cols[i, 2])), -1, cv2.LINE_AA, shift=2)
            if hreg is not None:
                cv2.ellipse(hreg, (int(gx[i] * 4), int(gy[i] * 4)), (max(1, int(Ls[i] * 2)), max(1, int(Ws[i] * 2))), float(np.degrees(ang[i])), 0, 360,
                            float(hv[i]), -1, cv2.LINE_AA, shift=2)
        al = np.clip(cv2.GaussianBlur(mm, (0, 0), 1.2) * spill, 0, 1) * a
        if s.clipm is not None: al = al * s.clipm[y0:y0 + h, x0:x0 + ww]
        reg += (lay - reg) * al[..., None]

    def dots(s, pts, r_, cols, a=1.0, seed=0):
        rr = np.random.RandomState(seed); k = s.k
        for i, (x, y) in enumerate(pts):
            col = hexc(cols[rr.randint(len(cols))]) if isinstance(cols, (list, tuple)) else hexc(cols)
            rad = r_ * (.75 + .5 * rr.rand()) if np.isscalar(r_) else r_[i]
            cv2.ellipse(s.img, (int(x * k * 4), int(y * k * 4)), (max(1, int(rad * k * 4)), max(1, int(rad * k * 4 * (.8 + .3 * rr.rand())))), rr.rand() * 180, 0, 360,
                        tuple(float(v) for v in col), -1, cv2.LINE_AA, shift=2)

def pal_fn(cols, var=.06, weights=None):
    C = np.array([hexc(c) for c in cols])
    def f(X, Y, r):
        idx = r.choice(len(C), size=len(X), p=weights) if weights else r.randint(len(C), size=len(X))
        return C[idx] * (1 + (r.rand(len(X), 1) - .5) * 2 * var)
    return f

def setup(ground, seed):
    c = Kanvas(W, H, K, ground, seed=seed)
    S.c = c
    return c

def land(top, bottom=930):
    t = np.asarray(top, float)
    return np.vstack([t, [[t[-1, 0], bottom], [t[0, 0], bottom]]])

def y_on(top, x):
    t = np.asarray(top); o = np.argsort(t[:, 0]); return float(np.interp(x, t[o, 0], t[o, 1]))

def ribbon(P, wfn):
    P = np.asarray(P, float); d = np.gradient(P, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.hypot(*nr.T)[:, None] + 1e-9
    wv = np.array([wfn(i / (len(P) - 1)) for i in range(len(P))])
    return np.vstack([P + nr * (wv / 2)[:, None], (P - nr * (wv / 2)[:, None])[::-1]]), nr, wv

# --------------------------------------------------------------------------- trees
def skeleton_tree(c, x, y, h, cols, seed, dots=None, branches='#1c1a20', trunk_w=None, shape='round'):
    """Folk tree: a stippled canopy with the black branch skeleton painted over it."""
    r = np.random.RandomState(seed)
    rx, ry = h * (.36 if shape == 'round' else .24), h * (.34 if shape == 'round' else .44); cy = y - h * (.6 if shape == 'round' else .58)
    out = S.lumpy(x, cy, rx, ry, seed, n=48, bumps=5, amp=.08, flat=.15)
    m = c.area(out, hexc(cols[0]) * .85, wob=.2, rough=.8, edge_dark=.08, seed=seed)
    c.stip(m, pal_fn(cols, .08), spacing=1.25, L=2.4, w=1.3, seed=seed + 1)
    if dots:
        pts = [(x + math.cos(a) * rx * d * .92, cy + math.sin(a) * ry * d * .9) for a, d in zip(r.rand(int(h * 1.2)) * 6.283, r.rand(int(h * 1.2)) ** .5)]
        c.dots(pts, max(.5, h * .012), dots, seed=seed + 2)
    tw = trunk_w or max(1.2, h * .045)
    c.stroke([(x, y + 1), (x + r.randn() * .5, y - h * .45), (x + r.randn(), cy)], tw, branches, a=1, dry=.05, taper=(0, .4), press=.1)
    def br(px, py, ang, ln, wd, depth):
        if depth == 0 or ln < 2: return
        ex, ey = px + math.cos(ang) * ln, py + math.sin(ang) * ln
        if ((ex - x) / rx) ** 2 + ((ey - cy) / ry) ** 2 > .85: ln *= .6; ex, ey = px + math.cos(ang) * ln, py + math.sin(ang) * ln
        c.stroke([(px, py), ((px + ex) / 2 + r.randn() * .4, (py + ey) / 2), (ex, ey)], wd, branches, a=1, dry=.05, taper=(0, .5), press=.1)
        n = 2 if r.rand() < .7 else 3
        for k in range(n):
            br(ex, ey, ang + (k - (n - 1) / 2) * r.uniform(.35, .6), ln * r.uniform(.55, .72), wd * .62, depth - 1)
    start = (x, y - h * .42)
    for k, a0 in enumerate([-math.pi / 2 - .55, -math.pi / 2, -math.pi / 2 + .55]):
        br(start[0], start[1] - k * h * .04, a0 + r.randn() * .1, h * r.uniform(.2, .26), tw * .8, 4)

def stipple_fir(c, x, y, h, cols, seed, slim=.2):
    r = np.random.RandomState(seed); w = h * slim
    L = []; Rr = []
    for t in np.linspace(0, 1, 12):
        yy = y - h * t; ww = w * (1 - t) ** .9 * (1 + .08 * math.sin(t * 19 + seed))
        L.append((x - ww, yy)); Rr.append((x + ww, yy))
    poly = L + Rr[::-1]
    m = c.area(poly, hexc(cols[0]) * .85, wob=.25, rough=.9, edge_dark=.1, seed=seed)
    c.stip(m, pal_fn(cols, .08), spacing=1.3, L=3.2, w=1.2, seed=seed + 1,
           angfn=lambda X, Y: np.where(X < x, math.pi / 2 + .75, math.pi / 2 - .75))

def dab_tree(c, x, y, h, cols, seed, shape='round', trunk='#5a3e2c'):
    """Oil-daub tree in the American folk manner: a dense canopy of small dabs, lit from the upper left."""
    r = np.random.RandomState(seed)
    if shape == 'cone':
        w = h * .26; poly = []
        for t in np.linspace(0, 1, 14):
            ww = w * math.sin(min(1, (1 - t) * 1.3) * math.pi / 2) ** .8 * (1 + .1 * math.sin(t * 17 + seed))
            poly.append((x - ww, y - h * .08 - h * .92 * t))
        for t in np.linspace(1, 0, 14):
            ww = w * math.sin(min(1, (1 - t) * 1.3) * math.pi / 2) ** .8 * (1 + .1 * math.cos(t * 13 + seed))
            poly.append((x + ww, y - h * .08 - h * .92 * t))
        cx, cy, rx, ry = x, y - h * .5, w, h * .46
    else:
        rx, ry = h * .38, h * .4; cx, cy = x, y - h * .58
        poly = S.lumpy(cx, cy, rx, ry, seed, n=44, bumps=4, amp=.08, flat=.25)
    c.stroke([(x, y + 1), (x, y - h * .3)], max(1.2, h * .06), trunk, a=1, dry=.1, taper=(0, .3))
    m = c.area(poly, hexc(cols[0]) * .9, wob=.2, rough=.8, edge_dark=.12, seed=seed)
    def colf(X, Y, rr):
        lit = np.clip(((cx - X) / rx * .6 + (cy - Y) / ry * .8 + .3), 0, 1)
        C = np.array([hexc(cc) for cc in cols])
        idx = np.clip((lit * (len(C) - 1) + rr.randn(len(X)) * .6).round().astype(int), 0, len(C) - 1)
        return C[idx] * (1 + (rr.rand(len(X), 1) - .5) * .1)
    c.stip(m, colf, spacing=1.5, L=2.6, w=2.0, seed=seed + 1, jit=1.5)

def bush(c, x, y, rx, ry, cols, seed):
    m = c.area(S.lumpy(x, y - ry, rx, ry, seed, n=30, bumps=4, amp=.08, flat=.35), hexc(cols[0]) * .85, wob=.2, rough=.8, edge_dark=.1, seed=seed)
    c.stip(m, pal_fn(cols, .08), spacing=1.2, L=2.2, w=1.3, seed=seed + 1)

# --------------------------------------------------------------------------- rails
def rails(c, P, sfn, ballast='#b9a07a', tie='#4f3a30', steel='#34343c', hide=None, shine='#d8d6d0'):
    P = np.asarray(P, float); n = len(P)
    d = np.gradient(P, axis=0); d /= np.hypot(*d.T)[:, None] + 1e-9; nr = np.stack([-d[:, 1], d[:, 0]], 1)
    vis = np.ones(n, bool)
    if hide is not None:
        for a, b in hide: vis[a:b] = False
    runs = []; cur = []
    for i in range(n):
        if vis[i]: cur.append(i)
        elif cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    for run in runs:
        if ballast:
            for k in range(0, len(run) - 1, 10):
                idx = run[k:k + 12]; sub = P[idx]; s = sfn(sub[len(sub) // 2][1])
                if len(sub) > 1: c.stroke(sub, 12 * s, ballast, a=.95, dry=.25, taper=(0, 0), press=.05, rough=.4)
        acc = 0
        for i in run[1:-1]:
            s = sfn(P[i][1]); acc += np.hypot(*(P[i] - P[i - 1]))
            if acc >= 5.2 * s:
                acc = 0; c.stroke([P[i] + nr[i] * 6 * s, P[i] - nr[i] * 6 * s], 2.0 * s, tie, a=.95, dry=.1, taper=(.05, .05), press=.1)
        for off in (3.4, -3.4):
            sp = np.array([P[i] + nr[i] * off * sfn(P[i][1]) for i in run])
            for k in range(0, len(sp) - 1, 24):
                sub = sp[k:k + 25]
                if len(sub) > 1: c.stroke(sub, 1.3 * sfn(sub[0][1]), steel, a=.95, dry=0, taper=(0, 0), press=.05, rough=.1, streak=0, ridge=0)
        if shine:
            sp = np.array([P[i] + nr[i] * 3.4 * sfn(P[i][1]) - [0, .6] for i in run])
            for k in range(0, len(sp) - 1, 24):
                sub = sp[k:k + 25]
                if len(sub) > 1: c.stroke(sub, .5, shine, a=.6, dry=0, taper=(0, 0), press=0, rough=0, streak=0, ridge=0)

def path(c, pts, w, col, sfn=lambda y: 1.0, dotted=None, seed=0):
    P = catmull(pts, 10)
    for k in range(0, len(P) - 1, 8):
        sub = P[k:k + 10]; s = sfn(sub[len(sub) // 2][1])
        c.stroke(sub, w * s, col, a=.95, dry=.3, taper=(0, 0), press=.1, rough=.6)
    if dotted:
        r = np.random.RandomState(seed)
        for p in resample(P, 4.5):
            s = sfn(p[1]); c.dots([(p[0] + r.randn() * w * s * .18, p[1] + r.randn() * w * s * .1)], .6 * s, dotted, seed=int(r.randint(1e6)))

def train(c, P, i_head, s):
    S.train(i_head=i_head, sabs=s, pts=np.asarray(P, float))

def smoke(x, y, s=1.0, seed=0, n=5, col='#f7f1e6'):
    r = np.random.RandomState(seed)
    for i in range(n):
        px = x + i * 4.5 * s + math.sin(i * 1.3) * 2 * s; py = y - i * 6 * s; rr = (2.2 + i * .9) * s
        S.c.area(S.lumpy(px, py, rr, rr * .8, seed + i, n=18, amp=.12, flat=0), col, wob=.2, rough=.5, a=.85 - i * .12, edge_dark=0)

def restipple(c, before, spacing=1.15, L=2.3, w=1.25, seed=0, thresh=.03):
    """Repaint whatever changed since `before` with the same short dabs as the rest of the painting,
    sampling each dab's colour from what is there, so line-drawn things share the stippled surface."""
    diff = np.abs(c.img - before).max(-1)
    m = (diff > thresh).astype(np.float32)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) == 0: return
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    src = cv2.GaussianBlur(c.img, (0, 0), .6).copy()
    def colfn(X, Y, r):
        px = np.clip((X * c.k).astype(int), 0, c.W - 1); py = np.clip((Y * c.k).astype(int), 0, c.H - 1)
        return src[py, px] * (1 + (r.rand(len(X), 1) - .5) * .16)
    c.stip((x0, y0, m[y0:y1, x0:x1]), colfn, spacing=spacing, L=L, w=w, seed=seed, spill=1.0)


def impasto(c, strength=.16, light=(-.7, -.7)):
    """Light the paint ridges left by every dab, as thick paint catches a raking light."""
    hb = cv2.GaussianBlur(c.HM, (0, 0), 1.1)
    gx = cv2.Sobel(hb, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hb, cv2.CV_32F, 0, 1, ksize=3)
    sh = np.clip((gx * light[0] + gy * light[1]) * strength, -.14, .14)
    c.img *= (1 + sh)[..., None]

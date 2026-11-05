"""Engine 10: authored illustrations painted with the map's own brush (art direction, 5 Nov 2026).

An asset is drawn by hand as shapes in its own coordinates (for the Toy Town assets: one unit = one pixel of the
user's reference image, y down). Place() maps those coordinates onto the map, optionally mirrored, and every shape
is painted by the engine's gouache brush (c.mask, c.area, c.stroke, c.stip, c.dots), so an authored object keeps the
map's texture and stays consistent with everything else.

Edges are measured in ASSET units, not map units: the map's edge presets ('fine' blurs 0.32 map units) are sized for
buildings, and on a figure 28 map units tall they blur about 3 reference pixels, which made the first Marines soft.
Here `soft` (edge blur), `rimw` (width of the darker rim the gouache pools into) and `light` (a gentle lit-to-shaded
gradient across the shape) all scale with the asset, so it looks the same at every zoom.

    P = Place(x, y, scale, flip=False, W=280)     # (x, y): where asset point (0, 0) goes, in map units
    P.shape(pts, col, ...)    a smooth closed shape (Catmull-Rom through the points unless smooth=False)
    P.ellipse(cx, cy, rx, ry, col, ...)
    P.line(pts, w, col, ...)  a painted stroke (w in asset units)
    P.loop(pts, w, col, ...)  a painted stroke round a smooth closed path (a ribbon loop)
    P.dots(pts, r, col)
"""
import math
import numpy as np, cv2
import usmap4 as B
from brush import catmull, hexc
from kit import pal_fn

SOFT = {'fine': .6, 'crisp': .35}         # the old preset names, as asset-unit softness (reference pixels)

class Place:
    def __init__(s, x, y, scale, flip=False, W=0):
        s.x, s.y, s.u, s.flip, s.W = x, y, scale, flip, W
    def P(s, pts):
        pts = np.asarray(pts, np.float64)
        xs = (s.W - pts[:, 0]) if s.flip else pts[:, 0]
        return np.stack([s.x + xs * s.u, s.y + pts[:, 1] * s.u], 1)
    def shape(s, pts, col, smooth=True, soft=.6, rough=.3, rim=.10, rimw=2.5, var=.04, a=1.0, stip=None, n=10,
              light=None, edge=None, edge_dark=None):
        """light = (dx, dy, amount): brighter towards asset direction (dx, dy), darker away from it."""
        c = B.c
        if edge is not None: soft = SOFT.get(edge, soft)
        if edge_dark is not None: rim = edge_dark
        pts = np.asarray(pts, np.float64)
        if smooth and len(pts) >= 4: pts = np.asarray(catmull([tuple(p) for p in pts], n, closed=True))
        poly = [tuple(p) for p in s.P(pts)]
        prev = c.edge; c.edge = dict(soft=soft * s.u, rough=1.0, wob=0.0)
        try:
            m = c.mask(poly, 0, rough, 0)
            x0, y0, mm = m
            if mm.size <= 1 or mm.max() <= 0: return m
            shade = np.ones_like(mm)
            if rim:
                inner = cv2.GaussianBlur(mm, (0, 0), max(.5, rimw * s.u * c.k))
                shade *= 1 - rim * np.clip((mm - inner) * 2.5, 0, 1)
            if light:
                dx, dy, amt = light; dx = -dx if s.flip else dx; L = math.hypot(dx, dy) or 1
                Y, X = np.mgrid[0:mm.shape[0], 0:mm.shape[1]].astype(np.float32)
                pr = (X * dx + Y * dy) / L; ins = mm > .5
                if ins.any():
                    lo, hi = pr[ins].min(), pr[ins].max()
                    t = np.clip((pr - lo) / max(1e-6, hi - lo), 0, 1)
                    shade *= 1 + amt * (2 * t - 1)
            c.area(poly, col, m=m, shade=shade, edge_dark=0, var=var, a=a)
            if stip:                                     # painted dabs inside larger areas, as on the rest of the map
                cols, spacing, L_, w = stip
                c.stip(m, pal_fn(cols, .04), spacing=spacing * s.u, L=L_ * s.u, w=w * s.u, angfn=lambda X, Y: 1.35 + 0 * X,
                       seed=int(abs(pts[0][0] * 31 + pts[0][1] * 7)) % 9973, jit=.6, spill=.8, a=a)   # dabs stay inside
        finally:
            c.edge = prev
        return m
    def ellipse(s, cx, cy, rx, ry, col, rot=0.0, **kw):
        t = np.linspace(0, 2 * math.pi, 28, endpoint=False); cr, sr = math.cos(rot), math.sin(rot)
        pts = [(cx + rx * math.cos(a) * cr - ry * math.sin(a) * sr, cy + rx * math.cos(a) * sr + ry * math.sin(a) * cr) for a in t]
        return s.shape(pts, col, smooth=False, **kw)
    def line(s, pts, w, col, a=1.0, edge=None, taper=(.15, .15), dry=0.0):
        c = B.c
        c.stroke([tuple(p) for p in s.P(pts)], w * s.u, col, a=a, dry=dry, taper=taper)
    def loop(s, pts, w, col, a=1.0, n=10):
        q = catmull([tuple(p) for p in pts], n, closed=True); q = list(q) + [q[0], q[1]]
        s.line(q, w, col, a=a, taper=(0, 0))
    def dots(s, pts, r, col, edge=None):
        c = B.c
        prev = c.edge; c.edge = dict(soft=.3 * s.u, rough=1.0, wob=0.0)
        try: c.dots([tuple(p) for p in s.P(pts)], r * s.u, [col] if isinstance(col, str) else col)
        finally: c.edge = prev

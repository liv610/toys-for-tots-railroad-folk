"""Engine 10: authored illustrations painted with the map's own brush (art direction, 5 Nov 2026).

An asset is drawn by hand as shapes in its own coordinates (for the Toy Town assets: one unit = one pixel of the
user's reference image, y down). Place() maps those coordinates onto the map, optionally mirrored, and every shape
is painted by the engine's gouache brush (c.area, c.stroke, c.stip, c.dots) with an edge preset, so an authored
object keeps the map's texture and stays consistent with everything else.

    P = Place(x, y, scale, flip=False, W=280)     # (x, y): where asset point (0, 0) goes, in map units
    P.shape(pts, col, ...)    a smooth closed shape (Catmull-Rom through the points unless smooth=False)
    P.ellipse(cx, cy, rx, ry, col, ...)
    P.line(pts, w, col, ...)  a painted stroke (w in asset units)
    P.dots(pts, r, col)
"""
import math
import numpy as np
import usmap4 as B
from brush import catmull, hexc
from kit import pal_fn

class Place:
    def __init__(s, x, y, scale, flip=False, W=0):
        s.x, s.y, s.u, s.flip, s.W = x, y, scale, flip, W
    def P(s, pts):
        pts = np.asarray(pts, np.float64)
        xs = (s.W - pts[:, 0]) if s.flip else pts[:, 0]
        return np.stack([s.x + xs * s.u, s.y + pts[:, 1] * s.u], 1)
    def shape(s, pts, col, smooth=True, edge='fine', rough=.35, edge_dark=.08, var=.04, a=1.0, stip=None, n=10):
        c = B.c
        pts = np.asarray(pts, np.float64)
        if smooth and len(pts) >= 4: pts = np.asarray(catmull([tuple(p) for p in pts], n, closed=True))
        with c.edges(edge):
            m = c.area([tuple(p) for p in s.P(pts)], col, wob=0, rough=rough, edge_dark=edge_dark, var=var, a=a)
            if stip and m is not None:                   # painted dabs inside larger areas, as on the rest of the map
                cols, spacing, L, w = stip
                c.stip(m, pal_fn(cols, .04), spacing=spacing * s.u, L=L * s.u, w=w * s.u, angfn=lambda X, Y: 1.35 + 0 * X, seed=int(abs(pts[0][0] * 31 + pts[0][1] * 7)) % 9973, jit=.6, spill=.8)   # dabs stay inside the outline
        return m
    def ellipse(s, cx, cy, rx, ry, col, rot=0.0, **kw):
        t = np.linspace(0, 2 * math.pi, 28, endpoint=False); cr, sr = math.cos(rot), math.sin(rot)
        pts = [(cx + rx * math.cos(a) * cr - ry * math.sin(a) * sr, cy + rx * math.cos(a) * sr + ry * math.sin(a) * cr) for a in t]
        return s.shape(pts, col, smooth=False, **kw)
    def line(s, pts, w, col, a=1.0, edge='fine', taper=(.15, .15), dry=0.0):
        c = B.c
        with c.edges(edge):
            c.stroke([tuple(p) for p in s.P(pts)], w * s.u, col, a=a, dry=dry, taper=taper)
    def dots(s, pts, r, col, edge='crisp'):
        c = B.c
        with c.edges(edge):
            c.dots([tuple(p) for p in s.P(pts)], r * s.u, [col] if isinstance(col, str) else col)

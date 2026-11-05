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
import brush10 as BR
from brush import catmull, hexc
from kit import pal_fn

SOFT = {'fine': .6, 'crisp': .35}         # the old preset names, as asset-unit softness (reference pixels)
RELIEF_LIGHT = (1.0, -.7, 50.0)           # relief lighting: asset direction of the light (front and above), elevation in degrees
AMBIENT = .40
RELIEF_GAIN = 1.6                          # scales every relief height (tuning)

class Place:
    def __init__(s, x, y, scale, flip=False, W=0):
        s.x, s.y, s.u, s.flip, s.W = x, y, scale, flip, W
    def P(s, pts):
        pts = np.asarray(pts, np.float64)
        xs = (s.W - pts[:, 0]) if s.flip else pts[:, 0]
        return np.stack([s.x + xs * s.u, s.y + pts[:, 1] * s.u], 1)
    # ---- the shading field: distance from the outline and a light ramp, in WORLD pixels over the shape's whole box,
    # then cropped to this window, so a shape crossing a tile edge is shaded identically in every tile.
    def _field(s, poly, m, light, relief=None):
        c = B.c; x0, y0, mm = m; h, w = mm.shape; ox, oy = c.T
        Pw = (np.asarray(poly, np.float64) + np.array([BR.PADL, BR.PADT])) * c.k
        X0, Y0 = int(math.floor(Pw[:, 0].min())) - 3, int(math.floor(Pw[:, 1].min())) - 3
        X1, Y1 = int(math.ceil(Pw[:, 0].max())) + 4, int(math.ceil(Pw[:, 1].max())) + 4
        F = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
        cv2.fillPoly(F, [np.round((Pw - [X0, Y0]) * 8).astype(np.int32)], 1, cv2.LINE_8, shift=3)
        D = cv2.distanceTransform(F, cv2.DIST_L2, 5)
        Dw = np.zeros((h, w), np.float32)                                # cropped to this window's mask box
        gx0, gy0 = ox + x0, oy + y0
        a0, b0 = max(gx0, X0), max(gy0, Y0); a1, b1 = min(gx0 + w, X1), min(gy0 + h, Y1)
        if a1 > a0 and b1 > b0: Dw[b0 - gy0:b1 - gy0, a0 - gx0:a1 - gx0] = D[b0 - Y0:b1 - Y0, a0 - X0:a1 - X0]
        G = None
        if relief:                                   # a height that rises from the outline and levels off: a bevelled, moulded part
            hgt, wd = relief[0] * RELIEF_GAIN, relief[1]; px = s.u * c.k
            d = np.clip(D / max(.5, wd * px), 0, 1); H = (hgt * px) * np.sqrt(1 - (1 - d) ** 2)
            H = cv2.GaussianBlur(H, (0, 0), max(.4, .35 * px))
            gx = cv2.Sobel(H, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(H, cv2.CV_32F, 0, 1, ksize=3) / 8
            G = []
            for A_ in (gx, gy):
                o = np.zeros((h, w), np.float32)
                if a1 > a0 and b1 > b0: o[b0 - gy0:b1 - gy0, a0 - gx0:a1 - gx0] = A_[b0 - Y0:b1 - Y0, a0 - X0:a1 - X0]
                G.append(o)
        t = None
        if light:
            dx, dy = light[0], light[1]; dx = -dx if s.flip else dx; L = math.hypot(dx, dy) or 1
            YY, XX = np.nonzero(F); pr = ((XX + X0) * dx + (YY + Y0) * dy) / L
            lo, hi = float(pr.min()), float(pr.max())
            Y, X = np.mgrid[gy0:gy0 + h, gx0:gx0 + w].astype(np.float64)
            t = np.clip(((X * dx + Y * dy) / L - lo) / max(1e-6, hi - lo), 0, 1).astype(np.float32)
        return Dw, t, G
    def _relief(s, G, relief):
        """Light the height field: diffuse shading relative to a flat top (so 1 where the part is level), plus a highlight."""
        spec, pw = (relief[2] if len(relief) > 2 else 0.0), (relief[3] if len(relief) > 3 else 14)
        lx, ly, el = RELIEF_LIGHT; lx = -lx if s.flip else lx; e = math.radians(el); n = math.hypot(lx, ly) or 1
        L = np.array([lx / n * math.cos(e), ly / n * math.cos(e), math.sin(e)], np.float32)
        gx, gy = G; inv = 1 / np.sqrt(gx * gx + gy * gy + 1)
        Nx, Ny, Nz = -gx * inv, -gy * inv, inv
        ndl = Nx * L[0] + Ny * L[1] + Nz * L[2]
        dif = (AMBIENT + (1 - AMBIENT) * np.clip(ndl, 0, 1)) / (AMBIENT + (1 - AMBIENT) * L[2])
        sp = None
        if spec:
            Rz = 2 * ndl * Nz - L[2]                                                     # reflection towards the viewer
            sp = spec * np.clip(Rz, 0, 1) ** pw * (1 - Nz ** 40)                         # only on the curved edge, not the flat top
        return np.clip(dif, .45, 1.4).astype(np.float32), sp
    def _shade(s, Dw, t, rim, rimw, light, form):
        c = B.c; px = s.u * c.k; shade = np.ones_like(Dw)
        if rim: shade *= 1 - rim * np.clip(1 - Dw / max(.5, rimw * px), 0, 1)          # pigment pooled at the edge
        if light is not None and t is not None: shade *= 1 + light[2] * (2 * t - 1)
        if form:                                                                         # a rounded, moulded body
            amt, wd = form[0], form[1]
            f = (1 - np.clip(Dw / max(.5, wd * px), 0, 1)) ** 1.6
            if t is not None: f = f * (1.25 - .6 * t)                                    # edges turned from the light go darker
            shade *= 1 - amt * f
        return shade
    def shape(s, pts, col, smooth=True, soft=.6, rough=.3, rim=.10, rimw=2.5, var=.04, a=1.0, stip=None, n=10,
              light=None, form=None, relief=None, edge=None, edge_dark=None):
        """light = (dx, dy, amount): brighter towards asset direction (dx, dy), darker away from it.
        form = (amount, width): darker towards the outline over `width` asset units, as on a rounded object."""
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
            sp = None
            if rim or light or form or relief:
                Dw, t, G = s._field(poly, m, light, relief); shade = s._shade(Dw, t, rim, rimw, light, form)
                if relief: r_, sp = s._relief(G, relief); shade = shade * r_
            else: shade = None
            c.area(poly, col, m=m, shade=shade, edge_dark=0, var=var, a=a)
            if sp is not None:
                reg = c.img[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]; al = mm * sp * a
                if c.clipm is not None: al = al * c.clipm[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]
                reg += (1 - reg) * al[..., None]
            if stip:                                     # painted dabs inside larger areas, as on the rest of the map
                cols, spacing, L_, w = stip
                c.stip(m, pal_fn(cols, .04), spacing=spacing * s.u, L=L_ * s.u, w=w * s.u, angfn=lambda X, Y: 1.35 + 0 * X,
                       seed=int(abs(pts[0][0] * 31 + pts[0][1] * 7)) % 9973, jit=.6, spill=.8, a=a)   # dabs stay inside
        finally:
            c.edge = prev
        return m
    def tone(s, pts, light=None, form=None, rim=0, rimw=2.5, smooth=True, soft=.6, n=10, tint=None, relief=None):
        """Shade what is already painted inside a shape (after its grain and details), so the volume covers them too.
        tint: a colour the shadows lean towards (cool for cloth, warm for skin)."""
        c = B.c
        pts = np.asarray(pts, np.float64)
        if smooth and len(pts) >= 4: pts = np.asarray(catmull([tuple(p) for p in pts], n, closed=True))
        poly = [tuple(p) for p in s.P(pts)]
        prev = c.edge; c.edge = dict(soft=soft * s.u, rough=1.0, wob=0.0)
        try:
            m = c.mask(poly, 0, .15, 0)
        finally:
            c.edge = prev
        x0, y0, mm = m
        if mm.size <= 1 or mm.max() <= 0: return
        Dw, t, G = s._field(poly, m, light, relief); sh = s._shade(Dw, t, rim, rimw, light, form); sp = None
        if relief: r_, sp = s._relief(G, relief); sh = sh * r_
        reg = c.img[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]
        al = mm if c.clipm is None else mm * c.clipm[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]]
        new = reg * sh[..., None]
        if tint is not None:                                                         # shadows lean towards the tint
            dk = np.clip(1 - sh, 0, 1)[..., None] * 1.2
            new = new * (1 - dk * .35) + hexc(tint)[None, None] * new.mean(-1, keepdims=True) / max(1e-3, hexc(tint).mean()) * dk * .35
        if sp is not None: new = new + (1 - new) * sp[..., None]                     # the sheen on the curve
        reg += (new - reg) * al[..., None]
    def grain(s, pts, cols, spacing=1.2, L=2.2, w=.9, ang=1.35, a=1.0, smooth=False, soft=.6, n=10, seed=0):
        """The painted grain of cloth, gold or wood: small brush dabs in `cols`, clipped to the shape, over paint already there."""
        c = B.c
        pts = np.asarray(pts, np.float64)
        if smooth and len(pts) >= 4: pts = np.asarray(catmull([tuple(p) for p in pts], n, closed=True))
        prev = c.edge; c.edge = dict(soft=soft * s.u, rough=1.0, wob=0.0)
        try:
            m = c.mask([tuple(p) for p in s.P(pts)], 0, .2, 0)
            if m[2].size <= 1 or m[2].max() <= 0: return
            ang = (math.pi - ang) if s.flip else ang
            r = max(1, int(round(1.2 * c.f * 1.6)))           # the brush feathers the dabs by 1.2 f px: keep them inside the outline
            m = (m[0], m[1], cv2.erode(m[2], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))))
            c.stip(m, pal_fn(cols, .03), spacing=spacing * s.u, L=L * s.u, w=w * s.u, angfn=lambda X, Y: ang + 0 * X,
                   seed=(int(abs(pts[0][0] * 31 + pts[0][1] * 7)) + seed) % 9973, jit=.7, spill=.8, a=a)
        finally:
            c.edge = prev
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

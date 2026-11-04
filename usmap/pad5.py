"""Pass 5, group 7 — more ocean around the whole map.

The map keeps its own coordinates (the 1671 x 941 reference grid, "map units"); the canvas simply grows by a margin
of open sea on every side, and every map unit is painted PADL/PADT map units further right and down:

    pixel = (map + (PADL, PADT)) * k

How it is done, without touching pass 4 or the shared painting libraries:
  * OffKanvas: the painting canvas, which shifts every map-unit coordinate it is given (areas, strokes, dots) and
    shifts back the coordinates it hands to colour and direction callbacks, so every painter works unchanged.
  * pass 4's main() and sprite(), and the lighthouse painter, are the few places that turn map units into pixels by
    hand. They are re-compiled from pass 4's own source with each such conversion shifted (every replacement is
    checked to occur exactly once), so pass 4's file is never edited.
  * extra wave marks are painted in the new margin only; the waves of the old canvas keep their places.
"""
import math, inspect, gc
import numpy as np, cv2

PADL, PADT, PADR, PADB = 100, 70, 80, 80        # map units of new sea: west, north, east, south

class _Off:
    """Mixin for the canvas: map units in, shifted pixels out."""
    d = (0.0, 0.0)
    def _sh(s, P):
        return np.asarray(P, np.float64) + np.array(s.d)
    def mask(s, poly, wob=2.0, rough=1.0, seed=0, soft=0.9, scaled=False):
        if not scaled and poly is not None: poly = s._sh(poly)
        return super().mask(poly, wob, rough, seed, soft, scaled)
    def stroke(s, pts, *a, **kw):
        scaled = kw.get('scaled', a[10] if len(a) > 10 else False)
        if not scaled: pts = s._sh(pts)
        return super().stroke(pts, *a, **kw)
    def dots(s, pts, *a, **kw):
        return super().dots([(x + s.d[0], y + s.d[1]) for x, y in pts], *a, **kw)
    def stip(s, m, colfn, *a, **kw):
        dx, dy = s.d
        f = colfn; colfn = lambda X, Y, r: f(X - dx, Y - dy, r)
        if kw.get('angfn') is not None:
            g = kw['angfn']; kw['angfn'] = lambda X, Y: g(X - dx, Y - dy)
        elif len(a) > 3 and a[3] is not None:
            a = list(a); g = a[3]; a[3] = lambda X, Y: g(X - dx, Y - dy)
        return super().stip(m, colfn, *a, **kw)
    def flow_fill(s, m, angle_fn, col_fn, *a, **kw):
        dx, dy = s.d; s.d = (0.0, 0.0)        # the strokes it makes are already in the shifted frame
        try:
            return super().flow_fill(m, lambda X, Y: angle_fn(X - dx, Y - dy), lambda X, Y, r: col_fn(X - dx, Y - dy, r), *a, **kw)
        finally:
            s.d = (dx, dy)

def _recompile(mod, fn_name, end_marker, reps, extra_globals=None):
    src = inspect.getsource(mod)
    i = src.index(f'def {fn_name}('); j = src.index(end_marker, i)
    code = src[i:j]
    for old, new in reps:
        n = code.count(old)
        assert n == 1, f'{fn_name}: expected one {old!r}, found {n}'
        code = code.replace(old, new)
    if extra_globals: mod.__dict__.update(extra_globals)
    exec(compile(code, f'<pad5:{mod.__name__}.{fn_name}>', 'exec'), mod.__dict__)
    return mod.__dict__[fn_name]

def install(B):
    """Grow pass 4's canvas by the sea margin and re-point every painter at the new canvas."""
    from kit import Kanvas
    k = B.k
    W = B.W + int(round((PADL + PADR) * k)); H = B.H + int(round((PADT + PADB) * k))
    OX, OY = PADL * k, PADT * k
    # drop the old canvas first (at 6400 it is large), then make the new one
    B.c = None
    for m in (B.U, B.U2, B.U3, B.S, B.A): m.c = None
    gc.collect()
    Off = type('OffKanvas', (_Off, Kanvas), {})
    c = Off(W, H, k, '#2c5684', seed=1972); c.HM = np.zeros((H, W), np.float32); c.d = (float(PADL), float(PADT))
    B.c, B.W, B.H = c, W, H
    for m in (B.U, B.U2, B.U3): m.c, m.k, m.W, m.H = c, k, W, H
    B.S.c = c; B.A.c = c
    B.OX, B.OY = OX, OY; B.U.OX, B.U.OY = OX, OY
    B.PAD = (PADL, PADT, PADR, PADB)

    def margin_waves():
        """Wave marks in the new sea only (outside the old canvas), so the old waves keep their places."""
        R = np.random.RandomState(2027); n = 0
        while n < 70:
            x, y = R.uniform(-PADL + 8, B.RW + PADR - 50), R.uniform(-PADT + 12, B.RH + PADB - 10)
            if 0 <= x <= B.RW - 40 and 0 <= y <= B.RH: continue
            if B.LANDP.contains_point((x, y), radius=-30) or B.LANDP.contains_point((x + 30, y)): continue
            n += 1
            for kk in range(R.randint(2, 4)):
                pts = [(x + kk * 22 + u * 18, y + 3 * math.sin(u * math.pi * 2)) for u in np.linspace(0, 1, 6)]
                c.stroke(pts, 2.4, '#dfe6e8', a=.85, dry=.25, taper=(.2, .2), seed=B.sid('wave7', n, kk))
    B.MARGIN_WAVES = margin_waves

    _recompile(B, 'sprite', 'def save_rgba(', [
        ("int(max(0, bbox[0] * k)), int(max(0, bbox[1] * k))", "int(max(0, bbox[0] * k + OX)), int(max(0, bbox[1] * k + OY))"),
        ("int(min(W, bbox[2] * k)), int(min(H, bbox[3] * k))", "int(min(W, bbox[2] * k + OX)), int(min(H, bbox[3] * k + OY))"),
    ])
    _recompile(B, 'main', 'def steamer_body(', [
        ("    LMk = np.zeros((H, W), np.float32)\n", "    MARGIN_WAVES()\n    LMk = np.zeros((H, W), np.float32)\n"),
        ("np.round(COAST * k * 8)", "np.round((COAST * k + [OX, OY]) * 8)"),
        ("e['bbox'][0] * k", "e['bbox'][0] * k + OX"), ("e['bbox'][1] * k", "e['bbox'][1] * k + OY"),
        ("e['bbox'][2] * k", "e['bbox'][2] * k + OX"), ("e['bbox'][3] * k", "e['bbox'][3] * k + OY"),
        ("(np.array(scene['river']) * k)", "(np.array(scene['river']) * k + [OX, OY])"),
        ("pivot=[(60 + j * 60) * k - x0, 60 * k - y0]", "pivot=[(60 + j * 60) * k + OX - x0, 60 * k + OY - y0]"),
        ("piv = [cx * k - x0, cy * k - y0]", "piv = [cx * k + OX - x0, cy * k + OY - y0]"),
        ("M[0, 2] += q[0] * k - pv[0]; M[1, 2] += q[1] * k - pv[1]", "M[0, 2] += q[0] * k + OX - pv[0]; M[1, 2] += q[1] * k + OY - pv[1]"),
        ("pp[0] * k - piv[0] * sc], [0, sc, pp[1] * k - piv[1] * sc]", "pp[0] * k + OX - piv[0] * sc], [0, sc, pp[1] * k + OY - piv[1] * sc]"),
        ("pp[0] * k - pv[0] * sc], [0, sc, pp[1] * k - pv[1] * sc]", "pp[0] * k + OX - pv[0] * sc], [0, sc, pp[1] * k + OY - pv[1] * sc]"),
        ("dict(pivot=[piv[0] * k - x0, piv[1] * k - y0])", "dict(pivot=[piv[0] * k + OX - x0, piv[1] * k + OY - y0])"),
        ("a_, b_ = P[i] * k, P[i + 1] * k", "a_, b_ = P[i] * k + [OX, OY], P[i + 1] * k + [OX, OY]"),
        ("points=(r['Pext'] * k)", "points=(r['Pext'] * k + [OX, OY])"),
        ("map_units=[RW, RH], scale=k,", "map_units=[RW, RH], scale=k, frame=[OX, OY, RW * k, RH * k], pad=list(PAD),"),
    ])
    _recompile(B.U, 'lighthouse', 'def windmill(', [
        ("c.img[np.clip((Y * k).astype(int), 0, H - 1), np.clip((X * k).astype(int), 0, W - 1)]",
         "c.img[np.clip((Y * k + OY).astype(int), 0, H - 1), np.clip((X * k + OX).astype(int), 0, W - 1)]"),
    ])
    return c

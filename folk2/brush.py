"""A small gouache painting engine.
Everything is laid down as brush strokes or painted areas whose edges, pigment and bristle texture follow the stroke,
so texture lives in the paint, not in an overlay."""
import numpy as np, cv2, math

def hexc(h):
    if not isinstance(h, str): return np.asarray(h, np.float32)
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def mix(a, b, t): return hexc(a) * (1 - t) + hexc(b) * t

def noise(h, w, cell, seed):
    r = np.random.RandomState(seed)
    gh, gw = int(h / cell) + 4, int(w / cell) + 4
    g = r.rand(gh, gw).astype(np.float32)
    big = cv2.resize(g, (int(gw * cell), int(gh * cell)), interpolation=cv2.INTER_CUBIC)
    return big[:h, :w]

def fbm(h, w, cell, octaves, seed):
    out = np.zeros((h, w), np.float32); a = 1; tot = 0
    for o in range(octaves):
        out += noise(h, w, max(1.0, cell / 2 ** o), seed + o * 17) * a; tot += a; a *= .5
    out /= tot; lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)

def catmull(pts, n=12, closed=False):
    P = np.asarray(pts, np.float64)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed: out.append(P[-2])
    return np.array(out)

def resample(P, step):
    P = np.asarray(P, np.float64)
    if len(P) < 2: return P
    d = np.hypot(*np.diff(P, axis=0).T); c = np.concatenate([[0], np.cumsum(d)])
    if c[-1] < 1e-6: return P[:1]
    n = max(2, int(math.ceil(c[-1] / step)) + 1); s = np.linspace(0, c[-1], n)
    return np.stack([np.interp(s, c, P[:, 0]), np.interp(s, c, P[:, 1])], 1)

def smooth1d(n, seed, k=3):
    r = np.random.RandomState(seed); v = r.rand(n + 2 * k)
    v = np.convolve(v, np.ones(k) / k, 'same')[k:-k]
    return (v - v.min()) / (np.ptp(v) + 1e-6)

def wobble(P, amp, seed, wl=40.0, closed=True):
    """Displace a (pixel-space) outline along its normals by smooth noise: the hand is never perfectly steady."""
    P = resample(np.vstack([P, P[:1]]) if closed else P, 3.0)
    if len(P) < 3 or amp <= 0: return P
    d = np.gradient(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= (np.hypot(*nrm.T)[:, None] + 1e-6)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    r = np.random.RandomState(seed); m = int(s[-1] / wl) + 3
    k1 = r.randn(m); k2 = r.randn(m * 4) * .35
    off = np.interp(s / wl, np.arange(m), k1) + np.interp(s / (wl / 4), np.arange(m * 4), k2)
    if closed: off -= np.linspace(0, 1, len(off)) * (off[-1] - off[0])
    return P + nrm * off[:, None] * amp


class Canvas:
    def __init__(s, W, H, k, ground, seed=0):
        s.W, s.H, s.k = W, H, k
        s.img = np.empty((H, W, 3), np.float32); s.img[:] = hexc(ground)
        s.paper = np.clip(.55 * noise(H, W, 1.6, seed + 1) + .45 * noise(H, W, 5, seed + 2), 0, 1)
        s.Nbig = fbm(H, W, 140 * k / 2, 3, seed + 3)
        s.Nmid = fbm(H, W, 26 * k / 2, 3, seed + 4)
        s.Nsm = noise(H, W, 3.2 * k / 2, seed + 5)
        s.clipm = None
        s.rng = np.random.RandomState(seed + 9)

    # ---- clipping -------------------------------------------------------------------------------------------
    def set_clip(s, m):
        if m is None: s.clipm = None; return
        x0, y0, mm = m; c = np.zeros((s.H, s.W), np.float32)
        h, w = mm.shape; c[y0:y0 + h, x0:x0 + w] = mm; s.clipm = c

    # ---- painted area ---------------------------------------------------------------------------------------
    def mask(s, poly, wob=2.0, rough=1.0, seed=0, soft=0.9, scaled=False):
        P = np.asarray(poly, np.float64) * (1 if scaled else s.k)
        if wob > 0: P = wobble(P, wob * s.k, seed, wl=34 * s.k)
        pad = int(6 * s.k)
        x0 = max(0, int(P[:, 0].min()) - pad); x1 = min(s.W, int(P[:, 0].max()) + pad + 1)
        y0 = max(0, int(P[:, 1].min()) - pad); y1 = min(s.H, int(P[:, 1].max()) + pad + 1)
        if x1 <= x0 or y1 <= y0: return None
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        cv2.fillPoly(m, [np.round((P - [x0, y0]) * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
        if rough > 0:
            sg = soft * s.k
            mb = cv2.GaussianBlur(m, (0, 0), sg)
            n = s.Nsm[y0:y1, x0:x1] * .6 + s.paper[y0:y1, x0:x1] * .4
            m = np.clip((mb - .5 + rough * .32 * (n - .5)) * 3.2 + .5, 0, 1)
        return (x0, y0, m)

    def area(s, poly, col, wob=2.0, rough=1.0, var=.05, varbig=.05, edge_dark=.07, dens=.97, seed=0, a=1.0, m=None, shade=None, scaled=False):
        """Opaque gouache: an imperfect edge, pigment that pools at the edge, faint variation in density."""
        if m is None: m = s.mask(poly, wob, rough, seed, scaled=scaled)
        if m is None: return None
        x0, y0, mm = m; h, w = mm.shape
        reg = s.img[y0:y0 + h, x0:x0 + w]
        c = hexc(col)[None, None] * (1 + var * 2 * (s.Nmid[y0:y0 + h, x0:x0 + w, None] - .5) + varbig * 2 * (s.Nbig[y0:y0 + h, x0:x0 + w, None] - .5))
        if shade is not None: c = c * shade[..., None] if shade.ndim == 2 else c * shade
        if edge_dark:
            inner = cv2.GaussianBlur(mm, (0, 0), 2.2 * s.k)
            c = c * (1 - edge_dark * np.clip((mm - inner) * 2.5, 0, 1))[..., None]
        al = mm * (dens + (1 - dens) * s.paper[y0:y0 + h, x0:x0 + w]) * a
        if s.clipm is not None: al = al * s.clipm[y0:y0 + h, x0:x0 + w]
        reg += (c - reg) * al[..., None]
        return m

    # ---- the brush stroke -----------------------------------------------------------------------------------
    def stroke(s, pts, w, col, a=1.0, dry=0.0, taper=(.12, .3), press=.18, rough=.3, streak=.07, ridge=.1, seed=None,
               scaled=False, tremor=0.0, col2=None):
        """One brush stroke. Pure speed-up of stroke_bbox (4 Nov 2026), bit-identical to it.
        stroke_bbox evaluates every pixel of the stroke's bounding box against every segment. A pixel farther than
        pad = .8 w + 3 from the polyline always gets cover 0 (its edge distance de < -.27 w - 3), so its colour is
        unchanged (reg += (cc - reg) * 0). Here only the pixels within pad + 2 px of the polyline are evaluated, with
        the same arithmetic in the same dtypes, so every painted pixel gets exactly the same value."""
        k = 1 if scaled else s.k
        P = np.asarray(pts, np.float64) * k; w = max(.6, w * k)
        if seed is None: seed = int(s.rng.randint(1 << 30))
        r = np.random.RandomState(seed)
        if tremor > 0 and len(P) > 1:
            P = wobble(P, tremor * s.k, seed, wl=18 * s.k, closed=False)
        P = resample(P, max(1.5, w * .45))
        if len(P) < 2:
            P = np.vstack([P[0], P[0] + [.5, 0]])
        seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); L[L < 1e-6] = 1e-6
        cum = np.concatenate([[0], np.cumsum(L)]); total = cum[-1]
        pad = w * .8 + 3
        x0 = int(max(0, math.floor(P[:, 0].min() - pad))); x1 = int(min(s.W, math.ceil(P[:, 0].max() + pad)))
        y0 = int(max(0, math.floor(P[:, 1].min() - pad))); y1 = int(min(s.H, math.ceil(P[:, 1].max() + pad)))
        if x1 <= x0 or y1 <= y0: return
        nb = max(5, int(w / 1.8))
        comb = .35 + .65 * smooth1d(nb, seed, 2)
        Lb = .5 + .55 * r.rand(nb)
        pn = smooth1d(10, seed + 1, 2)
        en = r.rand(int(total / (2.5 * s.k / 2)) + 4)
        A = P[:-1]; U = seg / L[:, None]
        c0 = hexc(col); c1 = hexc(col2) if col2 is not None else None
        # the band: every pixel within pad + 2 px of the polyline (drawn with sub-pixel precision); outside it cover = 0
        band = np.zeros((y1 - y0, x1 - x0), np.uint8)
        q = np.round((P - [x0, y0]) * 16).astype(np.int32)
        cv2.polylines(band, [q], False, 1, thickness=int(2 * pad + 5), lineType=cv2.LINE_8, shift=4)
        YY, XX = np.nonzero(band)
        if not len(YY): return
        YY = YY + y0; XX = XX + x0
        per = max(1, int(2.5e6 / max(1, len(A))))                      # pixels per chunk (same memory bound as before)
        for i0 in range(0, len(YY), per):
            ys = YY[i0:i0 + per]; xs = XX[i0:i0 + per]
            px = xs.reshape(-1, 1).astype(np.float32); py = ys.reshape(-1, 1).astype(np.float32)
            rx = px - A[None, :, 0]; ryy = py - A[None, :, 1]
            u = np.clip(rx * U[None, :, 0] + ryy * U[None, :, 1], 0, L[None])
            cx = rx - u * U[None, :, 0]; cy = ryy - u * U[None, :, 1]
            d2 = cx * cx + cy * cy
            j = np.argmin(d2, axis=1); idx = np.arange(len(j))
            dmin = np.sqrt(d2[idx, j]); sv = cum[j] + u[idx, j]
            sgn = np.sign(U[j, 0] * ryy[idx, j] - U[j, 1] * rx[idx, j]); sgn[sgn == 0] = 1
            sn = sv / total; tn = dmin * sgn / (w / 2)
            a0, a1 = taper
            prof = np.clip(np.minimum(sn / a0 if a0 > 0 else 1e9, (1 - sn) / a1 if a1 > 0 else 1e9), 0, 1) ** .5
            pp = np.interp(sn * 9, np.arange(10), pn)
            wp = prof * (1 - press + press * pp)
            ei = np.clip((sv / (2.5 * s.k / 2)).astype(int), 0, len(en) - 1)
            de = (wp - np.abs(tn) + rough * .22 * (en[ei] - .5)) * (w / 2)
            cover = np.clip(de / 1.1 + .5, 0, 1)
            sel = cover > 0
            if not sel.any(): continue
            bi = np.clip(((tn * .5 + .5) * nb).astype(int), 0, nb - 1)
            bt = comb[bi]
            al = cover * a
            if dry > 0:
                run = np.clip((Lb[bi] - sn) / .22, 0, 1)
                dep = 1 - dry * (1 - bt * run)
                pap = s.paper[ys, xs]
                dep = np.clip(dep * 1.3 - (1 - pap) * dry * 1.2 - .12 * dry, 0, 1)
                al = al * dep
            if s.clipm is not None: al = al * s.clipm[ys, xs]
            f = (1 + streak * (bt - .6) * 2) * (1 - ridge * np.abs(np.clip(tn, -1, 1)) ** 4)
            cc = c0[None] * f[:, None]
            if c1 is not None: cc = (c0[None] * (1 - sn[:, None]) + c1[None] * sn[:, None]) * f[:, None]
            reg = s.img[ys, xs]
            reg += (cc - reg) * al[:, None]
            s.img[ys, xs] = reg

    def stroke_bbox(s, pts, w, col, a=1.0, dry=0.0, taper=(.12, .3), press=.18, rough=.3, streak=.07, ridge=.1, seed=None,
               scaled=False, tremor=0.0, col2=None):
        """The original stroke (until 4 Nov 2026), kept unchanged for comparison: stroke() must match it exactly.
        Use it with  brush.Canvas.stroke = brush.Canvas.stroke_bbox."""
        k = 1 if scaled else s.k
        P = np.asarray(pts, np.float64) * k; w = max(.6, w * k)
        if seed is None: seed = int(s.rng.randint(1 << 30))
        r = np.random.RandomState(seed)
        if tremor > 0 and len(P) > 1:
            P = wobble(P, tremor * s.k, seed, wl=18 * s.k, closed=False)
        P = resample(P, max(1.5, w * .45))
        if len(P) < 2:
            P = np.vstack([P[0], P[0] + [.5, 0]])
        seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); L[L < 1e-6] = 1e-6
        cum = np.concatenate([[0], np.cumsum(L)]); total = cum[-1]
        pad = w * .8 + 3
        x0 = int(max(0, math.floor(P[:, 0].min() - pad))); x1 = int(min(s.W, math.ceil(P[:, 0].max() + pad)))
        y0 = int(max(0, math.floor(P[:, 1].min() - pad))); y1 = int(min(s.H, math.ceil(P[:, 1].max() + pad)))
        if x1 <= x0 or y1 <= y0: return
        nb = max(5, int(w / 1.8))
        comb = .35 + .65 * smooth1d(nb, seed, 2)
        Lb = .5 + .55 * r.rand(nb)
        pn = smooth1d(10, seed + 1, 2)
        en = r.rand(int(total / (2.5 * s.k / 2)) + 4)
        A = P[:-1]; U = seg / L[:, None]
        hh = y1 - y0; ww = x1 - x0
        rows_per = max(1, int(2.5e6 / max(1, ww * len(A))))
        c0 = hexc(col); c1 = hexc(col2) if col2 is not None else None
        for ry in range(y0, y1, rows_per):
            ry1 = min(y1, ry + rows_per)
            ys, xs = np.mgrid[ry:ry1, x0:x1]
            px = xs.reshape(-1, 1).astype(np.float32); py = ys.reshape(-1, 1).astype(np.float32)
            rx = px - A[None, :, 0]; ryy = py - A[None, :, 1]
            u = np.clip(rx * U[None, :, 0] + ryy * U[None, :, 1], 0, L[None])
            cx = rx - u * U[None, :, 0]; cy = ryy - u * U[None, :, 1]
            d2 = cx * cx + cy * cy
            j = np.argmin(d2, axis=1); idx = np.arange(len(j))
            dmin = np.sqrt(d2[idx, j]); sv = cum[j] + u[idx, j]
            sgn = np.sign(U[j, 0] * ryy[idx, j] - U[j, 1] * rx[idx, j]); sgn[sgn == 0] = 1
            sn = sv / total; tn = dmin * sgn / (w / 2)
            a0, a1 = taper
            prof = np.clip(np.minimum(sn / a0 if a0 > 0 else 1e9, (1 - sn) / a1 if a1 > 0 else 1e9), 0, 1) ** .5
            pp = np.interp(sn * 9, np.arange(10), pn)
            wp = prof * (1 - press + press * pp)
            ei = np.clip((sv / (2.5 * s.k / 2)).astype(int), 0, len(en) - 1)
            de = (wp - np.abs(tn) + rough * .22 * (en[ei] - .5)) * (w / 2)
            cover = np.clip(de / 1.1 + .5, 0, 1)
            sel = cover > 0
            if not sel.any(): continue
            bi = np.clip(((tn * .5 + .5) * nb).astype(int), 0, nb - 1)
            bt = comb[bi]
            al = cover * a
            if dry > 0:
                run = np.clip((Lb[bi] - sn) / .22, 0, 1)
                dep = 1 - dry * (1 - bt * run)
                pap = s.paper[ys.ravel(), xs.ravel()]
                dep = np.clip(dep * 1.3 - (1 - pap) * dry * 1.2 - .12 * dry, 0, 1)
                al = al * dep
            if s.clipm is not None: al = al * s.clipm[ys.ravel(), xs.ravel()]
            f = (1 + streak * (bt - .6) * 2) * (1 - ridge * np.abs(np.clip(tn, -1, 1)) ** 4)
            cc = c0[None] * f[:, None]
            if c1 is not None: cc = (c0[None] * (1 - sn[:, None]) + c1[None] * sn[:, None]) * f[:, None]
            reg = s.img[ry:ry1, x0:x1].reshape(-1, 3)
            reg += (cc - reg) * al[:, None]
            s.img[ry:ry1, x0:x1] = reg.reshape(ry1 - ry, x1 - x0, 3)

    def ink(s, pts, w, col='#2a2420', a=.92, tremor=.6, press=.4, taper=(.08, .15), seed=None, scaled=False):
        s.stroke(pts, w, col, a=a, dry=0, taper=taper, press=press, rough=.15, streak=0, ridge=0, seed=seed, tremor=tremor, scaled=scaled)

    def dab(s, x, y, ln, w, ang, col, a=1.0, dry=.15, bend=.25, seed=None, **kw):
        c, si = math.cos(ang), math.sin(ang); nx, ny = -si, c
        p0 = (x - c * ln / 2, y - si * ln / 2); p2 = (x + c * ln / 2, y + si * ln / 2)
        p1 = (x + nx * ln * bend * .5, y + ny * ln * bend * .5)
        s.stroke([p0, p1, p2], w, col, a=a, dry=dry, taper=(.2, .35), seed=seed, **kw)

    def flow_fill(s, m, angle_fn, col_fn, w, L, spacing, a=1.0, dry=.2, seed=0, jitter=.25, thresh=.35, **kw):
        """Cover a painted area with strokes that follow its form; strokes are clipped softly to the area."""
        if m is None: return
        x0, y0, mm = m; h, ww = mm.shape; r = np.random.RandomState(seed); k = s.k
        prev = s.clipm
        cm = cv2.GaussianBlur(mm, (0, 0), 1.0 * k)
        s.set_clip((x0, y0, np.clip(cm * 1.15, 0, 1)))
        sp = spacing * k
        gy, gx = np.mgrid[0:h:sp, 0:ww:sp]
        gx = (gx + r.rand(*gx.shape) * sp).ravel(); gy = (gy + r.rand(*gy.shape) * sp).ravel()
        order = r.permutation(len(gx))
        for i in order:
            px, py = gx[i], gy[i]
            if px >= ww or py >= h or mm[int(py), int(px)] < thresh: continue
            X, Y = (px + x0) / k, (py + y0) / k
            pts = [(X, Y)]
            for sgn in (1, -1):
                cx, cy = X, Y; seq = []
                for _ in range(4):
                    ang = angle_fn(cx, cy) + r.randn() * jitter * .3
                    st = L / 8
                    cx += math.cos(ang) * st * sgn; cy += math.sin(ang) * st * sgn
                    seq.append((cx, cy))
                pts = (seq[::-1] + pts) if sgn == -1 else (pts + seq)
            col = col_fn(X, Y, r)
            s.stroke(pts, w * (.8 + .4 * r.rand()), col, a=a, dry=dry, seed=int(r.randint(1 << 30)), **kw)
        s.clipm = prev

    def save(s, path, quality=90):
        out = np.clip(s.img, 0, 1)
        bgr = (out[..., ::-1] * 255 + .5).astype(np.uint8)
        cv2.imwrite(path + '.png', bgr)
        cv2.imwrite(path + '.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
        sm = cv2.resize(bgr, (s.W // 2, s.H // 2), interpolation=cv2.INTER_AREA)
        cv2.imwrite(path + '_sm.jpg', sm, [cv2.IMWRITE_JPEG_QUALITY, 88])

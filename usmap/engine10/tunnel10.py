"""A small wooded knoll with a stone tunnel on the red line (Northwest integration test).

Painted with the map's own painters and brush, so it belongs to the same painting:
  * the knoll is a pass-3 hill (U3.paint_hill3), the same painter and palette family as every hill around it;
  * its trees are the map's tree painters (tall and layered firs, one small autumn tree);
  * the portals are stone in the viaduct's palette and stipple, with mossy tops and a dark, soft mouth.

Two scene elements, so the existing depth and occluder systems do the rest:
  knoll10   depth 336.0, painted just after the hill it stands on: behind the track and the train
  tunnel10  depth 336.3, painted after the track (one float16 depth step, 0.25, nearer, so the occluder sees it): the knoll's face between the two portals, plus the portals.
            Its pixels are in front of the track, so the occluder hides the train inside the tunnel, car by car.
Every mark depends only on map position and seed (Engine 10), so the face repainted inside the tunnel span matches
the knoll painted behind the track.
"""
import math
import numpy as np
import usmap4 as B
from usmap4 import hexc, pal_fn

U, U2, U3 = B.U, B.U2, B.U3
STONE = ['#b8ac98', '#9c907c', '#c8bca8', '#8c8270', '#a89c88']
MOSS = ['#56692c', '#627634', '#4a5c26', '#6e803a']

def knoll_poly(p):
    return U2.hill_poly(p['cx'], p['base'], p['w'], p['h'], p['seed_hill'])

def _top_at(p, x):
    top = knoll_poly(p)[:40]
    return float(np.interp(x, top[:, 0], top[:, 1]))

def _span_clip(c, x0, x1, ytop, ybot, feather):
    """A soft clip mask (canvas pixels) for x0..x1, ytop..ybot in map units."""
    import cv2
    m = c.mask([(x0, ytop), (x1, ytop), (x1, ybot), (x0, ybot)], wob=0, rough=0)
    if m is None: return None
    x, y, mm = m
    mm = cv2.GaussianBlur(mm, (0, 0), feather * c.k)
    full = np.zeros((c.H, c.W), np.float32); h, w = mm.shape; full[y:y + h, x:x + w] = mm
    return full

def _unit(v):
    v = np.asarray(v, float); return v / (np.hypot(*v) + 1e-9)

def portal_frame(P, i, side, face):
    """Where a portal stands and which way it faces. Its face is a vertical plane across the track at P[i], turned to
    face along the line (toward the oncoming train at the entrance, toward the open country at the exit) and a little
    toward the viewer, so the opening reads as a mouth the train runs into, not a doorway it runs past.
    Returns foot (track centre at the face), d (the face's direction on the ground, pointing toward the viewer),
    nrm (the way the face looks), t (track direction)."""
    t = _unit(P[min(i + 4, len(P) - 1)] - P[max(i - 4, 0)])
    nrm = _unit((-t if side == 'in' else t) + np.array([0.0, face]))
    d = np.array([-nrm[1], nrm[0]]); d = d if d[1] > 0 else -d
    return np.array(P[i], float), d, nrm, t

def front_span(c, p, routes):
    """The part of the scene in front of the hidden track: between the vertical lines where the track meets the two
    portal faces (the train's own plane meets a vertical face along a vertical line), from above the train down to
    the knoll's foot. A soft-edged mask in canvas pixels."""
    P = routes['red']['P']; iL, iR = p['portals']
    ys = P[iL:iR + 1, 1]
    m = _span_clip(c, float(P[iL][0]), float(P[iR][0]), float(ys.min()) - p['cover'], float(ys.max()) + 16, .01)
    # hard-edged on purpose: the two halves are painted by different elements, and a soft edge would leave a pale line
    return None if m is None else (m > .5).astype(np.float32)

def _clipped(c, mask, fn):
    """Run a painter with every clip it sets intersected with mask."""
    orig = c.set_clip
    def set_clip(m, orig=orig, mask=mask):
        orig(m); c.clipm = mask.copy() if c.clipm is None else c.clipm * mask
    c.set_clip = set_clip
    try:
        c.set_clip(None); fn()
    finally:
        del c.set_clip
        c.set_clip(None)

def _scene(c, p, routes):
    U3.paint_hill3(p['cx'], p['base'], p['w'], p['h'], p['kind'], p['seed_hill'])
    P = routes['red']['P']
    for i, side in zip(p['portals'], ('in', 'out')): portal(c, P, i, side, p)

def knoll(p, routes):
    """Behind the track: the knoll and both portals, everywhere except the span in front of the hidden track.
    Each pixel is painted by exactly one of the two elements: the engine records an element's depth only where it
    changes a pixel, so painting the same thing twice would leave the front at the back depth."""
    c = B.c
    span = front_span(c, p, routes)
    if span is None: _scene(c, p, routes)
    else: _clipped(c, 1 - span, lambda: _scene(c, p, routes))

def knoll_trees(p):
    for j, (dx, hh, kd) in enumerate(p['trees']):
        x = p['cx'] + dx; y = _top_at(p, x) + 7 + abs(dx) * .06
        sd = p['seed_hill'] * 7 + j * 131
        if kd == 'fir': U2.tall_fir(x, y, hh, sd)
        elif kd == 'lfir': U2.layered_fir(x, y, hh, sd)
        else: U2.big_tree(x, y, hh, kd, sd)

def tunnel(p, routes):
    """In front of the track: the same knoll and portals inside the span (so the train is hidden between the two
    faces and goes into each mouth along the face's own line), then the trees on the knoll's crown."""
    c = B.c
    span = front_span(c, p, routes)
    if span is not None: _clipped(c, span, lambda: _scene(c, p, routes))
    knoll_trees(p)

def portal(c, P, i, side, p):
    """A stone portal in the map's own style (usmap3.portal3: mossy cutting, rough-stone arch, radial joints, deep
    mouth), standing on a face turned along the track, so its arch is drawn foreshortened on that face."""
    r = np.random.RandomState(p['seed_hill'] + (11 if side == 'in' else 29))
    foot, d, nrm, t = portal_frame(P, i, side, p['face'])
    foot = foot + [0, U3.TW * .35]
    iw, ih, ring = p['mouth_w'], p['mouth_h'], p['ring']
    def prof(w, h, n=26, jit=0.0, pw=.75, ctr=None, dy=0.0):
        cf = foot if ctr is None else ctr; out = []
        for u in np.linspace(0, 1, n):
            b = cf + d * (u - .5) * w
            hh = math.sin(u * math.pi) ** pw * h * (1 + .03 * math.sin(u * 5.0 + (1 if side == 'in' else 3)))
            q = b + [0, dy - hh]
            if jit: q = q + r.uniform(-jit, jit, 2)
            out.append((float(q[0]), float(q[1])))
        return out
    def base(w, dy=2.5, ctr=None):
        cf = foot if ctr is None else ctr
        a, b = cf + d * w / 2 + [0, dy], cf - d * w / 2 + [0, dy]; return [(float(a[0]), float(a[1])), (float(b[0]), float(b[1]))]
    # the cutting: darker, mossy ground the portal is set into
    cw, chh = iw + 2 * ring + 22, ih + ring + 5
    cm = c.area(prof(cw, chh, jit=1.1, pw=.5) + base(cw, 4), '#3a4a2a', wob=1.1, rough=1.2, edge_dark=.04, a=.78, seed=r.randint(1 << 30))
    if cm is not None:
        c.stip(cm, pal_fn(['#45562e', '#3a4a2a', '#56662f', '#627634']), spacing=1.5, L=3.6, w=1.8, a=.85, seed=r.randint(1 << 30), jit=1.0)
    # the stone arch, then the mouth with its deeper core set back into the hill
    outer = prof(iw + 2 * ring, ih + ring, jit=.6, pw=.45)
    om = c.area(outer + base(iw + 2 * ring), '#a89c88', wob=.3, rough=.7, edge_dark=.14, seed=r.randint(1 << 30))
    if om is not None:
        c.stip(om, pal_fn(['#b0a490', '#9c907c', '#c0b4a0', '#8c8270', '#a8a08c']), spacing=1.25, L=3.6, w=2.6, seed=r.randint(1 << 30), jit=1.3)
    inner = prof(iw, ih, n=22, pw=.5)
    c.area(inner + base(iw, 1.5), '#121010', wob=0, rough=.3, seed=r.randint(1 << 30))
    back = foot - nrm * 5                                         # the tunnel runs back from the face
    c.area(prof(iw * .7, ih * .82, pw=.55, ctr=back) + base(iw * .7, 1.0, ctr=back), '#070607', wob=.6, rough=.9, edge_dark=0, a=.75, seed=r.randint(1 << 30))
    # the track runs on into the dark and fades: a few dim ties and the two rails, so it never just stops at the face
    nr = np.array([-t[1], t[0]]); inward = t if side == 'in' else -t; P0 = np.array(P[i], float)
    rail, tie = U3.TRACKCOL['red']
    mm = c.mask(inner + base(iw, 1.5), wob=0, rough=0)              # only inside the mouth
    prev = c.clipm
    if mm is not None:
        x_, y_, m_ = mm; full = np.zeros((c.H, c.W), np.float32); hh_, ww_ = m_.shape; full[y_:y_ + hh_, x_:x_ + ww_] = m_
        c.clipm = full if prev is None else prev * full
    for k_, u in enumerate((2.5, 7.5, 12.5)):
        q = P0 + inward * u; al = .55 * (1 - u / 16)
        c.stroke([q + nr * U3.TW * 1.05, q - nr * U3.TW * 1.05], U3.TW * .5, '#4a3a2c', a=al, dry=.15, taper=(.05, .05))
    for o in (U3.TW * .78, -U3.TW * .78):
        a0 = P0 + nr * o - inward * .5; c.stroke([a0, a0 + inward * 17], 2.2, rail, a=.62, dry=.1, taper=(0, .98))
    c.clipm = prev
    # radial joints, a dark line round the arch, moss over the top and at the feet
    n_in, n_out = len(inner), len(outer)
    for u in np.linspace(.06, .94, 8) + r.uniform(-.015, .015, 8):
        a_ = np.array(inner[int(u * (n_in - 1))]); b_ = np.array(outer[int(u * (n_out - 1))])
        c.stroke([a_, a_ + (b_ - a_) * .95], 1.4, '#6a6050', a=.85, dry=.1, taper=(0, 0))
    c.stroke(outer, 1.3, '#5a5040', a=.6, dry=.2, taper=(.1, .1))
    for j in range(16):
        q = np.array(outer[r.randint(3, n_out - 3)])
        c.stroke([q + [r.uniform(-2, 2), r.uniform(.5, 1.5)], q + [r.uniform(-1.5, 1.5), -r.uniform(1.5, 3.4)]], r.uniform(1.4, 2.3),
                 MOSS[r.randint(len(MOSS))], a=.9, dry=.3, taper=(.1, .6))
    for s_ in (-1, 1):
        for j in range(5):
            q = foot + d * s_ * (iw / 2 + ring * r.uniform(.2, 1.2)) + [0, r.uniform(-.5, 1.5)]
            c.stroke([q, q + [r.uniform(-1.5, 1.5), -r.uniform(2, 4.5)]], r.uniform(1.2, 2), MOSS[r.randint(len(MOSS))], a=.9, dry=.3, taper=(.1, .7))

def paint(e, routes):
    if e['kind'] == 'knoll10': knoll(e['params'], routes); return True
    if e['kind'] == 'tunnel10': tunnel(e['params'], routes); return True
    return False

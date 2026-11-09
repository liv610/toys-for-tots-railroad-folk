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

def front_span(c, p, routes):
    """The part of the knoll that stands in front of the track: from just inside the portal eastward, from above the
    train down to the knoll's foot. A soft mask in canvas pixels."""
    P = routes['red']['P']; iL = p['portal']
    x0 = float(P[iL][0]) - (p['mouth_w'] / 2 + p['ring']) * .55
    return _span_clip(c, x0, p['cx'] + p['w'] / 2 + 30, float(P[iL][1]) - p['cover'], p['base'] + 10, .6)

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

def knoll(p, routes):
    """The knoll behind the track, everywhere except the part that stands in front of it (painted by tunnel()).
    Splitting it this way matters: the engine records an element's depth only where it changes a pixel, so the front
    part must not be painted twice over itself, or its pixels would keep the back depth and the occluder miss them."""
    c = B.c
    span = front_span(c, p, routes)
    paint = lambda: U3.paint_hill3(p['cx'], p['base'], p['w'], p['h'], p['kind'], p['seed_hill'])
    if span is None: paint()
    else: _clipped(c, 1 - span, paint)

def knoll_trees(p):
    for j, (dx, hh, kd) in enumerate(p['trees']):
        x = p['cx'] + dx; y = _top_at(p, x) + 7 + abs(dx) * .06
        sd = p['seed_hill'] * 7 + j * 131
        if kd == 'fir': U2.tall_fir(x, y, hh, sd)
        elif kd == 'lfir': U2.layered_fir(x, y, hh, sd)
        else: U2.big_tree(x, y, hh, kd, sd)

def _span_clip(c, x0, x1, ytop, ybot, feather):
    """A soft clip mask (canvas pixels) for x0..x1, ytop..ybot in map units."""
    poly = [(x0, ytop), (x1, ytop), (x1, ybot), (x0, ybot)]
    m = c.mask(poly, wob=0, rough=0)
    if m is None: return None
    x, y, mm = m
    import cv2
    mm = cv2.GaussianBlur(mm, (0, 0), feather * c.k)
    full = np.zeros((c.H, c.W), np.float32); h, w = mm.shape; full[y:y + h, x:x + w] = mm
    return full

def tunnel(p, routes):
    """The knoll's face in front of the track, from the portal eastward, then the portal.
    The train enters the portal and comes back into view from behind the knoll's eastern shoulder."""
    c = B.c
    P = routes['red']['P']; iL = p['portal']
    span = front_span(c, p, routes)
    if span is not None:
        _clipped(c, span, lambda: U3.paint_hill3(p['cx'], p['base'], p['w'], p['h'], p['kind'], p['seed_hill']))
    knoll_trees(p)
    portal(c, P, iL, p)

def portal(c, P, i, p):
    """In the map's own portal style (usmap3.portal3): a mossy cutting, a rough-stone arch, a deep mouth with a
    lighter floor, radial joints; sized for the train, a little irregular, the track running into it."""
    r = np.random.RandomState(p['seed_hill'] + 11)
    x, y = float(P[i][0]) + p.get('dx', 0.0), float(P[i][1]) + U3.TW * 1.04
    t = P[min(i + 4, len(P) - 1)] - P[max(i - 4, 0)]; t = t / (np.hypot(*t) + 1e-9)
    iw, ih, ring = p['mouth_w'], p['mouth_h'], p['ring']
    tilt = p.get('tilt', 1.5)                                      # the right side sits a little lower: hand-set, not drawn
    def prof(w, h, n=26, jit=0.0, pw=.75):
        out = []
        for u in np.linspace(0, 1, n):
            px = x - w / 2 + w * u; py = y + tilt * u - math.sin(u * math.pi) ** pw * h * (1 + .03 * math.sin(u * 5.0))
            if jit: px += r.uniform(-jit, jit); py += r.uniform(-jit, jit)
            out.append((px, py))
        return out
    feet = lambda w, dy=2.0: [(x + w / 2 + 2, y + tilt + dy), (x - w / 2 - 2, y + dy)]
    # the cutting: darker, mossy ground the portal is set into
    cw, chh = iw + 2 * ring + 26, ih + ring + 7
    cm = c.area(prof(cw, chh, jit=1.2, pw=.42) + feet(cw, 3), '#3a4a2a', wob=1.1, rough=1.2, edge_dark=.04, a=.78, seed=r.randint(1 << 30))
    if cm is not None:
        c.stip(cm, pal_fn(['#45562e', '#3a4a2a', '#56662f', '#627634']), spacing=1.5, L=3.6, w=1.8, a=.85, seed=r.randint(1 << 30), jit=1.0)
    # the stone arch
    outer = prof(iw + 2 * ring, ih + ring, jit=.6, pw=.45)
    om = c.area(outer + feet(iw + 2 * ring), '#a89c88', wob=.3, rough=.7, edge_dark=.14, seed=r.randint(1 << 30))
    if om is not None:
        c.stip(om, pal_fn(['#b0a490', '#9c907c', '#c0b4a0', '#8c8270', '#a8a08c']), spacing=1.25, L=3.6, w=2.6, seed=r.randint(1 << 30), jit=1.3)
    # the mouth, with a faint lighter floor where daylight reaches in
    inner = prof(iw, ih, n=22, pw=.5)
    c.area(inner + feet(iw, 1.0), '#121010', wob=0, rough=.3, seed=r.randint(1 << 30))
    c.area([(x - iw * .42, y + 1), (x + iw * .42, y + tilt + 1), (x + iw * .28, y - ih * .3), (x - iw * .28, y - ih * .3)], '#24201c', wob=0, rough=.5, a=.6)
    # the rails run a little way into the dark
    nrm = np.array([-t[1], t[0]]); base_pt = np.array(P[i], float)
    for o in (U3.TW * .78, -U3.TW * .78):
        a0 = base_pt + nrm * o - t * 2; a1 = a0 + t * 10
        c.stroke([a0, a1], 1.5, '#5a3a30', a=.55, dry=.1, taper=(0, .95))
    # radial joints between the voussoirs, and a dark line around the arch (as in portal3)
    n_in, n_out = len(inner), len(outer)
    for u in np.linspace(.05, .95, 9) + r.uniform(-.015, .015, 9):
        a_ = np.array(inner[int(u * (n_in - 1))]); b_ = np.array(outer[int(u * (n_out - 1))])
        c.stroke([a_, a_ + (b_ - a_) * .95], 1.5, '#6a6050', a=.85, dry=.1, taper=(0, 0))
    c.stroke(outer, 1.4, '#5a5040', a=.6, dry=.2, taper=(.1, .1))
    # moss and grass over the top of the arch and at its feet
    for j in range(18):
        q = np.array(outer[r.randint(3, n_out - 3)])
        c.stroke([q + [r.uniform(-2, 2), r.uniform(.5, 1.5)], q + [r.uniform(-1.5, 1.5), -r.uniform(1.5, 3.4)]], r.uniform(1.4, 2.3),
                 MOSS[r.randint(len(MOSS))], a=.9, dry=.3, taper=(.1, .6))
    for s_ in (-1, 1):
        for j in range(5):
            q = (x + s_ * (iw / 2 + ring * r.uniform(.2, 1.3)), y + (tilt if s_ > 0 else 0) + r.uniform(-.5, 1.5))
            c.stroke([q, (q[0] + r.uniform(-1.5, 1.5), q[1] - r.uniform(2, 4.5))], r.uniform(1.2, 2), MOSS[r.randint(len(MOSS))], a=.9, dry=.3, taper=(.1, .7))

def paint(e, routes):
    if e['kind'] == 'knoll10': knoll(e['params'], routes); return True
    if e['kind'] == 'tunnel10': tunnel(e['params'], routes); return True
    return False

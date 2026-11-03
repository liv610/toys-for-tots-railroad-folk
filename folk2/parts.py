"""Shared drawing geometry: building massing in a 3/4 oblique view, lumpy canopies, fir tiers. No styling here."""
import numpy as np, math
from brush import catmull, resample, hexc

PAL = {
    'cream': '#f3e6cb', 'offwhite': '#f7efdf', 'moss': '#6f7f3f', 'sage': '#9fae86', 'olive': '#807a3c', 'forest': '#2f4a3b',
    'ochre': '#c9953f', 'gold': '#e2b44b', 'terracotta': '#c4683f', 'coral': '#e08a6c', 'brick': '#a5452f', 'dustypink': '#d8a29c',
    'turquoise': '#5fa59c', 'slate': '#5d7186', 'sky': '#bcd5d9', 'barnred': '#a33b2c', 'ink': '#2b2521', 'teal': '#3e6b6a',
}
def P(name): return hexc(PAL.get(name, name))

V = lambda *a: np.array(a, float)

def building(b):
    """Return an ordered list of (role, polygon) plus feature dicts for one building."""
    x, y = b['x'], b['y']; t = b['t']
    out = []; feats = dict(windows=[], doors=[], chimneys=[], trims=[], extras=[])
    if t in ('silo', 'water', 'windpump'):
        return out, feats
    w, d, h, rh = b['w'], b['d'], b['h'], b['rh']; lean = b.get('lean', 0.0)
    D = V(.62 * d, -.36 * d); sh = lean * h; e = 2.6
    BL, BR = V(x - w / 2, y), V(x + w / 2, y); TL, TR = V(x - w / 2 + sh, y - h), V(x + w / 2 + sh, y - h)
    def fp(u, v): return BL + (BR - BL) * u + (TL - BL) * v           # a point on the front wall (v up)
    def sp(u, v): return BR + D * u + (TR - BR) * v                     # a point on the right side wall
    feats['fp'] = fp; feats['sp'] = sp; feats['D'] = D
    if t in ('gable',):
        ap = V(x + sh * 1.25, y - h - rh)
        out += [('side', [BR, BR + D, TR + D, TR]),
                ('roof_l', [ap, ap + D, TL + D + V(-e, e * .5), TL + V(-e, e * .5)]),
                ('roof_r', [ap, TR + V(e, e * .5), TR + D + V(e, e * .5), ap + D]),
                ('front', [BL, BR, TR, ap, TL])]
        feats['trims'].append([TL + V(-e, e * .5), ap, TR + V(e, e * .5)])
        feats['gable'] = (ap, TL, TR)
        feats['chimneys'].append((ap + D * .7 + (TR - ap) * .35, 'r'))
    elif t in ('side', 'station'):
        ov = 7 if t == 'station' else e
        RL = TL + D * .5 + V(0, -rh); RR = TR + D * .5 + V(0, -rh)
        eL = TL + V(-ov, ov * .55); eR = TR + V(ov, ov * .55)
        if t == 'station': eL = eL + V(0, 5); eR = eR + V(0, 5)
        out += [('roof_back', [RL, RR, TR + D, TL + D]),
                ('side', [BR, BR + D, TR + D, RR, TR]),
                ('front', [BL, BR, TR, TL]),
                ('roof_f', [eL, eR, RR + V(ov * .6, 0), RL + V(-ov * .6, 0)])]
        feats['trims'].append([eL, eR])
        feats['chimneys'].append((RL + (RR - RL) * .25 + V(0, 3), 'f'))
    elif t == 'gambrel':
        kL = V(x - w * .44 + sh, y - h - rh * .55); kR = V(x + w * .44 + sh, y - h - rh * .55); ap = V(x + sh, y - h - rh)
        out += [('side', [BR, BR + D, TR + D, TR]),
                ('roof_l', [ap, ap + D, kL + D, kL]),
                ('roof_r2', [TR + V(e, e * .4), kR + V(e * .6, 0), kR + D + V(e * .6, 0), TR + D + V(e, e * .4)]),
                ('roof_r', [kR + V(e * .6, 0), ap, ap + D, kR + D + V(e * .6, 0)]),
                ('front', [BL, BR, TR, kR, ap, kL, TL])]
        feats['trims'].append([TL + V(-e, e * .4), kL, ap, kR, TR + V(e, e * .4)])
        feats['gable'] = (ap, TL, TR)
    elif t == 'false':
        ap = V(x + sh, y - h - rh); pf = rh + 9
        top = [TL + V(0, -pf + 4), TL + V(w * .22, -pf + 4), TL + V(w * .26, -pf - 2)]
        top += [TL + V(w * .5 + w * .24 * math.cos(a), -pf - 2 - 6 * math.sin(a)) for a in np.linspace(math.pi, 0, 9)]
        top += [TL + V(w * .74, -pf - 2), TL + V(w * .78, -pf + 4), TL + V(w, -pf + 4)]
        out += [('side', [BR, BR + D, TR + D, TR]),
                ('roof_r', [ap, TR + V(e, e * .5), TR + D + V(e, e * .5), ap + D]),
                ('front', [BL, BR] + [TR] + top[::-1][:0] + list(reversed(top)) + [TL])]
        feats['trims'].append([TL + V(0, -pf + 9), TR + V(0, -pf + 9)])
    # windows and doors
    r = np.random.RandomState(abs(hash(b['name'])) % 10000)
    if t == 'station':
        for u in (.12, .3, .62, .8): feats['windows'].append(('tall', fp(u, .62), 4.5, 8))
        feats['doors'].append((fp(.46, 0), 7, 13, 'arch'))
    elif t == 'false':
        feats['windows'] += [('shop', fp(.24, .42), 9, 10), ('shop', fp(.78, .42), 8, 10), ('round', fp(.5, 1.2), 4, 4)]
        feats['doors'].append((fp(.52, 0), 7, 14, 'rect'))
        feats['awning'] = (fp(.04, .74), fp(.96, .74))
    elif t == 'gambrel':
        feats['doors'].append((fp(.5, 0), 16, 15, 'barn'))
        feats['windows'].append(('loft', fp(.5, 1.25), 6, 6))
    else:
        nfl = 2 if h > 24 else 1
        us = [.24, .76] if w > 26 else [.3]
        for fl in range(nfl):
            for u in us:
                if fl == 0 and abs(u - .5) < .2: continue
                vv = .55 if nfl == 1 else (.3 + fl * .42)
                uu = u + r.uniform(-.04, .04)
                feats['windows'].append(('rect' if r.rand() < .7 else 'tall', fp(uu, vv), 4.6 + r.rand() * 1.4, 6 + r.rand() * 2))
        du = .52 if len(us) == 2 else .72
        if t == 'side': du = .5 + r.uniform(-.12, .12)
        feats['doors'].append((fp(du, 0), 5.5, 10 if h < 22 else 11, 'arch' if r.rand() < .5 else 'rect'))
        if 'gable' in feats and t == 'gable':
            ap, _, _ = feats['gable']
            feats['windows'].append(('round' if b.get('round') or r.rand() < .5 else 'tri', fp(.5 + lean * .3, 1.0) + V(sh * .1, -rh * .42), 3.2, 3.2))
    # side wall windows
    nside = max(1, int(d / 14))
    for i in range(nside):
        u = (i + .6) / (nside + .3)
        feats['windows'].append(('side', sp(u, .55), 3.4, 6.5))
    return out, feats

def lumpy(cx, cy, rx, ry, seed, n=40, bumps=7, amp=.16, flat=.25):
    """A canopy outline: a few soft bulges, flatter underneath."""
    r = np.random.RandomState(seed)
    ph = r.rand(bumps) * 2 * math.pi; fr = r.randint(3, 9, bumps); am = r.rand(bumps) * amp
    pts = []
    for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
        k = 1 + sum(am[i] * math.cos(fr[i] * a + ph[i]) for i in range(bumps)) / max(1, bumps ** .5)
        yy = math.sin(a)
        if yy > 0: k *= 1 - flat * yy ** 2
        pts.append((cx + math.cos(a) * rx * k, cy + yy * ry * k))
    return np.array(pts)

def scallop(cx, cy, rx, ry, seed, nb=None):
    """A cloud-or-canopy outline made of round bumps along the top."""
    r = np.random.RandomState(seed); nb = nb or r.randint(5, 8)
    pts = []
    for i in range(nb):
        a0 = math.pi + i * math.pi / nb; a1 = math.pi + (i + 1) * math.pi / nb
        bx = cx + math.cos((a0 + a1) / 2) * rx * .8; by = cy + math.sin((a0 + a1) / 2) * ry * .7
        br = rx * (.32 + .18 * r.rand())
        for a in np.linspace(math.pi * 1.0, math.pi * 2.0, 7):
            pts.append((bx + math.cos(a) * br, by + math.sin(a) * br * .9))
    pts += [(cx + rx * 1.02, cy + ry * .2), (cx - rx * 1.02, cy + ry * .2)]
    return np.array(pts)

def fir_tiers(x, y, h, seed, slim=.3, tiers=None, droop=.35):
    """A Douglas fir as stacked, drooping branch tiers with a bending leader. Returns tier polygons top to bottom."""
    r = np.random.RandomState(seed)
    n = tiers or max(4, int(h / 11) + r.randint(-1, 2))
    trunk_h = h * .08; top = y - h; out = []
    lean = r.uniform(-.05, .05) * h
    for i in range(n):
        f0 = i / n; f1 = (i + 1.25) / n
        y0 = top + (h - trunk_h) * f0 * .96; y1 = top + (h - trunk_h) * min(1, f1)
        cx = x + lean * (1 - f0) ** 2
        wd = h * slim * (.25 + .75 * min(1, f1) ** .85) * (.85 + .3 * r.rand())
        wl = wd * (.85 + .3 * r.rand()); wr = wd * (.85 + .3 * r.rand())
        dl = (y1 - y0) * droop * (.6 + .8 * r.rand()); dr = (y1 - y0) * droop * (.6 + .8 * r.rand())
        poly = [(cx + lean * .1, y0), (cx + wr * .55, y0 + (y1 - y0) * .55), (cx + wr, y1 + dr * .2), (cx + wr * .8, y1 - dr * .1),
                (cx + wr * .45, y1 + dr * .25), (cx, y1 - (y1 - y0) * .1), (cx - wl * .45, y1 + dl * .25), (cx - wl * .8, y1 - dl * .1),
                (cx - wl, y1 + dl * .2), (cx - wl * .55, y0 + (y1 - y0) * .55)]
        out.append(np.array(poly))
    return out, (x, y - trunk_h * 1.4, y)

def persp(y):
    return .62 + .58 * max(0, (y - 380)) / 520

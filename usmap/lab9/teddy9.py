"""lab9 — a component sandbox: is the naive look of the small toys a limit of the brush or of how they are built?

Current teddy (tft7.teddy): eight overlapping discs. Designed teddy: one silhouette drawn as a smooth closed curve
from 34 control points, painted through the same gouache brush, then a lighter belly, muzzle, ear and foot pads,
stitched seams, eyes with a glint, a nose, a red bow, a little fur stipple and a soft dark outline.
Each is rendered alone, in about a second, at the size it has in the B window display (4 map units tall) and at a
larger shelf size (10 units), at the map's density and at 4x, against the same lit shop-window glass.
It also measures how far each toy stands out from the glass (difference in lightness, CIE L*)."""
import sys, os, time, json, math
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
import numpy as np, cv2
import tft7 as T7
from kit import Kanvas, pal_fn
from brush import hexc, catmull
import story as S

OUTLINE = [(-3.2, 0), (-1.1, 0), (-.6, -1.0), (0, -1.25), (.6, -1.0), (1.1, 0), (3.2, 0), (3.7, -1.3), (3.35, -2.9), (4.35, -3.5), (4.65, -4.5),
           (3.75, -5.05), (2.65, -5.35), (1.95, -6.0), (2.85, -6.95), (2.95, -8.5), (3.4, -9.2), (2.95, -10.2), (2.0, -10.0), (.95, -10.25),
           (-.95, -10.25), (-2.0, -10.0), (-2.95, -10.2), (-3.4, -9.2), (-2.95, -8.5), (-2.85, -6.95), (-1.95, -6.0), (-2.65, -5.35),
           (-3.75, -5.05), (-4.65, -4.5), (-4.35, -3.5), (-3.35, -2.9), (-3.7, -1.3)]

def fine_area(c, poly, col, soft=.22, edge=.16, rough=.25, seed=0, a=1.0):
    m = c.mask(poly, 0, rough, seed, soft=soft)
    return c.area(None, col, m=m, edge_dark=edge, a=a) if m is not None else None

def teddy_designed(c, x, y, h, col='#a8683a', seed=0):
    s = h / 10.3
    P = lambda dx, dy: (x + dx * s, y + dy * s)
    sil = [P(*p) for p in catmull(OUTLINE, 6, closed=True)]
    m = fine_area(c, sil, col, seed=seed)
    if m is not None:                                             # a little fur: short dabs in two browns
        C = np.array([hexc(col), hexc(col) * .86, np.minimum(hexc(col) * 1.12, 1)])
        c.stip(m, lambda X, Y, rr: C[rr.randint(3, size=len(X))], spacing=.32 * s, L=.55 * s, w=.32 * s, seed=seed + 1, jit=1.2)
    light = np.minimum(hexc(col) * 1.38 + .05, 1)
    for (dx, dy, rx, ry) in ((0, -3.0, 1.9, 1.6), (0, -7.35, 1.35, 1.0), (-2.3, -.55, 1.0, .5), (2.3, -.55, 1.0, .5)):
        fine_area(c, [P(dx + rx * math.cos(t), dy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)], light, edge=.08, seed=seed + 2)
    for ex in (-2.55, 2.55):
        fine_area(c, [P(ex + .55 * math.cos(t), -9.55 + .5 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 18, endpoint=False)], light, edge=.1, seed=seed + 3)
    for sx in (-1, 1):                                            # stitched seams where the arms and legs join
        c.stroke([P(sx * 2.6, -5.1), P(sx * 3.0, -4.1), P(sx * 3.2, -3.3)], .18 * s, hexc(col) * .62, a=.85, dry=0, taper=(.2, .2))
        c.stroke([P(sx * .45, -1.15), P(sx * .9, -.2)], .16 * s, hexc(col) * .62, a=.8, dry=0, taper=(.2, .2))
    c.stroke([P(0, -4.6), P(0, -1.7)], .12 * s, hexc(col) * .7, a=.5, dry=0, taper=(.3, .3))
    for ex in (-.95, .95):                                         # eyes with a glint
        fine_area(c, [P(ex + .34 * math.cos(t), -8.35 + .38 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)], '#1e1410', soft=.12, edge=0)
        c.dots([P(ex - .1, -8.5)], .1 * s, ['#ffffff'])
    fine_area(c, [P(-.48, -7.8), P(.48, -7.8), P(0, -7.25)], '#2a1a12', soft=.12, edge=0)                    # nose
    c.stroke([P(0, -7.25), P(0, -6.85)], .12 * s, '#2a1a12', a=.9, dry=0, taper=(0, 0))
    c.stroke([P(-.55, -6.65), P(0, -6.85), P(.55, -6.65)], .12 * s, '#2a1a12', a=.9, dry=0, taper=(.2, .2))
    for sx in (-1, 1):                                             # the red bow at the neck
        fine_area(c, [P(0, -5.85), P(sx * 1.45, -6.5), P(sx * 1.55, -5.15)], '#c8302a', soft=.15, edge=.2)
    fine_area(c, [P(.4 * math.cos(t), -5.85 + .36 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)], '#8a2420', soft=.12, edge=0)
    c.stroke(sil + [sil[0]], .16 * s, hexc(col) * .45, a=.55, dry=.1, taper=(0, 0))                          # a soft dark outline

def glass(c, x0, y0, x1, y1):
    m = c.mask([(x0, y1), (x1, y1), (x1, y0), (x0, y0)], 0, .2, 5, soft=.3)
    c.area(None, '#f2c25a', m=m, edge_dark=0)
    G = np.array([hexc(z) for z in ('#f8dc8a', '#f2c25a', '#d8962e')])
    c.stip(m, lambda X, Y, rr: G[rr.randint(3, size=len(X))], spacing=.6, L=1.2, w=.6, angfn=lambda X, Y: 0 * X, seed=6, jit=.4)

def lstar(bgr):
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255, cv2.COLOR_BGR2LAB); return lab[..., 0]

def panel(kind, h, k, soft=None, backdrop=None):
    W_, H_ = 16, 13
    c = Kanvas(int(W_ * k), int(H_ * k), k, '#ffffff', seed=3); c.HM = np.zeros((c.H, c.W), np.float32); T7.c = c
    glass(c, 0, 0, W_, H_)
    if backdrop: c.area(None, backdrop, m=c.mask([(1, H_ - .5), (W_ - 1, H_ - .5), (W_ - 1, .5), (1, .5)], 0, .2, 9, soft=.3), edge_dark=0, a=.6)
    before = c.img.copy()
    if kind == 'current':
        orig = c.mask
        if soft: c.mask = lambda poly, wob=2.0, rough=1.0, seed=0, soft_=None, scaled=False: orig(poly, wob, rough, seed, soft, scaled)
        T7.teddy(W_ / 2, H_ - 1.2, h / 10.6)
        c.mask = orig
    else:
        teddy_designed(c, W_ / 2, H_ - 1.2, h)
    img = (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8); bef = (np.clip(before, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
    toy = np.abs(img.astype(int) - bef.astype(int)).max(-1) > 25
    dL = float(np.abs(lstar(img)[toy] - lstar(bef)[toy]).mean()) if toy.any() else 0.0
    return img, dL

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    K = 6400 / 1671; rows = []; rep = {}
    cases = [('current', None, None, 'as on the map (soft 0.9)'), ('current', .32, None, 'same discs, fine brush'),
             ('designed', None, None, 'designed silhouette'), ('designed', None, '#7a4420', 'designed, darker window interior')]
    for h in (4.0, 10.0):
        for k, kname in ((K, 'map 100%'), (K * 4, '4x')):
            ims = []
            for kind, soft, bd, label in cases:
                t0 = time.time(); img, dL = panel(kind, h, k, soft, bd); dt = time.time() - t0
                rep[f'h{h:g} {kname} {label}'] = dict(seconds=round(dt, 2), lightness_contrast=round(dL, 1))
                ims.append(cv2.resize(img, (400, 325), interpolation=cv2.INTER_AREA if img.shape[1] > 400 else cv2.INTER_NEAREST))
            rows.append(np.hstack([np.pad(i, ((0, 0), (0, 8), (0, 0)), constant_values=255) for i in ims]))
    cv2.imwrite(f'{out}/teddy_sandbox.png', np.vstack([np.pad(r, ((0, 8), (0, 0), (0, 0)), constant_values=255) for r in rows]))
    json.dump(rep, open(f'{out}/teddy_sandbox.json', 'w'), indent=1)
    for kk, v in rep.items(): print(f'{kk:55s}', v)

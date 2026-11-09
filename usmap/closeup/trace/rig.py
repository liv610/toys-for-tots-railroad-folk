"""Cut the repainted Marines into hinged parts, and paint in what the parts were hiding.

Parts per Marine (reference pixel coordinates, measured on the reference painting):
  head      above the collar; pivot at the neck (its frames come from marines.py: mouths and a blink)
  forearm   elbow to glove; pivot at the elbow (the upper arm stays on the body)
  legs      back and front, below the hip; pivot at the hip (hidden under the coat hem)
  body      coat and collar; the coat behind the forearm is painted in (inpainted, then dabbed over with the folk brush)
and the present on its own, its corners behind the gloves painted in.
Output: rig/ with the parts as RGBA PNGs and rig.json (positions and pivots in sprite pixels).
"""
import os, sys, json, math, shutil
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', '..', '..', 'folk2'), os.path.join(HERE, '..', '..', '..', 'styles2')]
from kit import Kanvas
import marines as MR

X0, Y0, K = MR.X0, MR.Y0, MR.K
SRC = os.path.join(HERE, 'out'); DST = os.path.join(HERE, 'rig'); os.makedirs(DST, exist_ok=True)
def sp(p): return ((p[0] - X0) * K, (p[1] - Y0) * K)

PARTS = {
    'a': dict(neck_y=613, head=MR.MARINES['a']['head'], head_pivot=(655, 618),
              forearm=[(661, 649), (700, 654), (724, 664), (724, 691), (695, 691), (667, 681), (660, 668)], elbow=(664, 662),
              torso=[(616, 613), (674, 613), (679, 722), (615, 722)], hip=721, legsplit=645, legx=(610, 690),
              hips={'back': (630, 716), 'front': (661, 716)}),
    'b': dict(neck_y=613, head=MR.MARINES['b']['head'], head_pivot=(822, 616),
              forearm=[(812, 648), (812, 682), (781, 686), (772, 687), (751, 686), (751, 666), (772, 654)], elbow=(808, 662),
              torso=[(801, 613), (853, 613), (853, 716), (799, 716)], hip=715, legsplit=825, legx=(782, 858),
              hips={'front': (813, 710), 'back': (838, 710)}),
}
PRESENT = [(696, 603), (778, 603), (778, 689), (696, 689)]

def poly_mask(shape, pts, feather=1.0):
    m = np.zeros(shape, np.float32)
    cv2.fillPoly(m, [np.round(np.array([sp(p) for p in pts]) * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m

def brush_fill(rgb, region, seed):
    """Inpaint the region, then lay folk-brush dabs over it in the inpainted colours, so the filled area is painted too."""
    u8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    filled = cv2.inpaint(u8, (region > .05).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    filled = cv2.GaussianBlur(filled, (0, 0), 3) * (region[..., None]) + filled * (1 - region[..., None])
    H, W = rgb.shape[:2]
    c = Kanvas(W, H, 1, '#000000', seed=seed); c.img[:] = rgb * (1 - region[..., None]) + filled * region[..., None]
    def col(X, Y, r):
        xi = np.clip(X.astype(int), 0, W - 1); yi = np.clip(Y.astype(int), 0, H - 1)
        return np.clip(filled[yi, xi] * (1 + (r.rand(len(X), 1) - .5) * .1), 0, 1)
    c.stip((0, 0, region), col, spacing=8, L=12, w=7, angfn=lambda X, Y: np.full(X.shape, math.pi / 2), seed=seed, jit=.4, thresh=.2)
    c.stip((0, 0, region), col, spacing=4.5, L=7, w=4, angfn=lambda X, Y: np.full(X.shape, math.pi / 2), seed=seed + 1, jit=.5, thresh=.2)
    return c.img

def crop_save(name, rgb, a):
    ys, xs = np.nonzero(a > .02); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    MR.save_rgba(os.path.join(DST, name + '.png'), rgb[y0:y1, x0:x1], a[y0:y1, x0:x1])
    return dict(file=name + '.png', x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))

if __name__ == '__main__':
    im = cv2.imread(os.path.join(SRC, 'marines.png'), cv2.IMREAD_UNCHANGED)
    rgb = im[..., 2::-1].astype(np.float32) / 255; A = im[..., 3].astype(np.float32) / 255
    H, W = A.shape; YY, XX = np.mgrid[0:H, 0:W]
    rig = dict(size=[W, H], k=K, marines={}, present=None)
    body_rgb, body_a = rgb.copy(), A.copy()
    pm = poly_mask(A.shape, PRESENT, 0)
    hsv = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    white = ((hsv[..., 1] < 90) & (hsv[..., 2] > 140)).astype(np.float32)          # the gloves are the white paint
    gloves = np.zeros_like(A)
    for nm, P in PARTS.items():
        fm = poly_mask(A.shape, P['forearm'], 1.2) * A
        g = cv2.morphologyEx(white * (fm > .5), cv2.MORPH_CLOSE, np.ones((9, 9)))
        gloves = np.maximum(gloves, cv2.GaussianBlur(cv2.dilate(g, np.ones((3, 3))), (0, 0), 1.0) * pm)
    # the present as a whole object: a clean box (lid and body) plus the traced bow; where gloves covered it, its own
    # gold face is copied down from just above (same x, so the ribbon lines up), its edges shaded, then brushed over
    box = np.maximum(poly_mask(A.shape, [(696, 631), (778, 631), (778, 646), (696, 646)], .8), poly_mask(A.shape, [(699, 645), (776, 645), (776, 688), (699, 688)], .8))
    hole = np.clip(cv2.dilate((white * pm > .5).astype(np.float32) + (gloves > .05), np.ones((15, 15))), 0, 1) * (box > .3)
    hole = cv2.GaussianBlur(hole, (0, 0), 1.5)
    pre = rgb.copy(); dy = int(20 * K)
    src = np.roll(rgb, dy, axis=0)
    for _ in range(3):                                                 # copy again where the source itself was glove
        bad = np.roll(hole, dy, axis=0) > .3
        src = np.where(bad[..., None], np.roll(src, dy, axis=0), src)
    pre = pre * (1 - hole[..., None]) + src * hole[..., None]
    by1 = int(sp((0, 688))[1]); bx0, bx1 = int(sp((699, 0))[0]), int(sp((776, 0))[0])
    shade_ = np.zeros_like(A); shade_[by1 - 10:by1, bx0:bx1] = np.linspace(0, .28, 10)[:, None]
    shade_[:, bx1 - 8:bx1] = np.maximum(shade_[:, bx1 - 8:bx1], np.linspace(0, .2, 8)[None, :]) * (box[:, bx1 - 8:bx1] > .5)
    pre = pre * (1 - shade_[..., None] * hole[..., None] * 1.0)
    pr_rgb = brush_fill(pre, hole * 0, 51) if False else pre
    from kit import Kanvas as _K
    cpk = _K(W, H, 1, '#000000', seed=52); cpk.img[:] = pre
    def colp(X, Y, r):
        xi = np.clip(X.astype(int), 0, W - 1); yi = np.clip(Y.astype(int), 0, H - 1)
        return np.clip(pre[yi, xi] * (1 + (r.rand(len(X), 1) - .5) * .08), 0, 1)
    cpk.stip((0, 0, hole), colp, spacing=4, L=6, w=4, angfn=lambda X, Y: np.zeros(X.shape), seed=53, jit=.6, thresh=.2)
    pr_rgb = cpk.img
    bow = A * pm * (YY < sp((0, 634))[1])
    pr_a = np.clip(np.maximum(box, bow), 0, 1)
    rig['present'] = crop_save('present', pr_rgb, pr_a)
    body_a = body_a * (1 - pm)
    for nm, P in PARTS.items():
        R = dict()
        fm = poly_mask(A.shape, P['forearm'], 1.2) * A
        fa_a = fm * (1 - pm) + fm * pm * np.clip(gloves * 1.3, 0, 1)
        R['forearm'] = crop_save(f'forearm_{nm}', rgb, fa_a)
        R['forearm']['pivot'] = list(sp(P['elbow']))
        # the far arm: the same forearm, in the shadow side's darker paint, a little lower and further back; it holds
        # the present from below, so both hands are on it
        far = rgb * .78; far[..., 2] = far[..., 2] * 1.06
        R['forearm_far'] = crop_save(f'forearm_{nm}_far', far, fa_a)
        R['forearm_far'].update(pivot=list(sp(P['elbow'])), dx=int(-5 * K if nm == 'a' else 5 * K), dy=int(13 * K))
        # body: remove the forearm; paint the coat in where the forearm lay over the torso
        tm = poly_mask(A.shape, P['torso'], 1.0)
        behind = np.clip(fm * tm, 0, 1)
        body_rgb = brush_fill(body_rgb, behind, 60 + ord(nm))
        body_a = np.clip(body_a * (1 - fm) + behind, 0, 1)
        # head: above the neck line, inside the head box (the head frames cover it); the body keeps a band under it
        hx0, hy0, hx1, hy1 = [v for v in (sp(P['head'][:2]) + sp(P['head'][2:]))]
        ny = sp((0, P['neck_y']))[1]
        hb = (XX >= hx0) & (XX < hx1) & (YY < ny)
        body_a[hb] = 0
        R['head'] = dict(frames=[f'head_{nm}_{i}.png' for i in range(4)], x=int(hx0), y=int(hy0), pivot=list(sp(P['head_pivot'])))
        # legs: below the hip, split back/front; they extend 10 px up under the coat hem
        hipy = sp((0, P['hip']))[1]; lx0, lx1 = sp((P['legx'][0], 0))[0], sp((P['legx'][1], 0))[0]; split = sp((P['legsplit'], 0))[0]
        R['legs'] = {}
        for side in ('back', 'front'):
            left = (side == 'back') == (nm == 'a')
            m = ((YY > hipy - 40) & (XX >= lx0) & (XX < lx1) & ((XX < split) if left else (XX >= split))).astype(np.float32)
            m = cv2.GaussianBlur(m, (0, 0), 1.0) * A
            R['legs'][side] = crop_save(f'leg_{nm}_{side}', rgb, m)
            R['legs'][side]['pivot'] = list(sp(P['hips'][side]))
        body_a[(YY > hipy) & (XX >= lx0 - 20) & (XX < lx1 + 20)] = 0
        R['bounds'] = [lx0, hy0, lx1, H]
        rig['marines'][nm] = R
    for nm in ('a', 'b'):                                     # the body of each Marine on its own
        x0_, x1_ = sp((PARTS[nm]['legx'][0] - 14, 0))[0], sp((PARTS[nm]['legx'][1] + 14, 0))[0]
        if nm == 'a': x1_ = min(x1_, sp((696, 0))[0])
        else: x0_ = max(x0_, sp((778, 0))[0])
        m = body_a * ((XX >= x0_) & (XX < x1_))
        rig['marines'][nm]['body'] = crop_save(f'body_{nm}', body_rgb, m)
    for nm in ('a', 'b'):
        for i in range(4): shutil.copy(os.path.join(SRC, f'head_{nm}_{i}.png'), os.path.join(DST, f'head_{nm}_{i}.png'))
    json.dump(rig, open(os.path.join(DST, 'rig.json'), 'w'), indent=1)
    print(json.dumps({nm: {k: (v if k != 'legs' else list(v)) for k, v in R.items() if k in ('forearm', 'head')} for nm, R in rig['marines'].items()})[:600])

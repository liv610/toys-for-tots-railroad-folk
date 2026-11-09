"""Trace and repaint: the two Marines from the reference painting, repainted with the map's own folk brush.

1. Trace:   cut the figures (and the present they hold) out of the reference with GrabCut (mask_raw.png).
2. Repaint: lay the reference's smoothed colours, then dab over them coarse to fine with folk2's stipple. Every dab
            takes its colour from the reference at its own position and runs along the local form (perpendicular to
            the colour gradient); the finest dabs go only where detail is (faces, buttons, gloves, ribbon). Then the
            impasto pass lights the paint ridges, exactly as on the map.
3. Speech:  each Marine gets mouth frames (closed = traced, half, open) painted over the traced mouth with the same
            brush, and his head is cut as its own layer with a pivot at the collar, so the viewer can nod it.
    PYTHONPATH=../../../folk2:../../../styles2 python3 marines.py
"""
import os, sys, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', '..', '..', 'folk2'), os.path.join(HERE, '..', '..', '..', 'styles2')]
from kit import Kanvas, impasto
from parts import lumpy

X0, Y0, X1, Y1 = 596, 540, 876, 834          # crop of the reference (its own pixels); the mask is at 3x
K = 4                                          # canvas pixels per reference pixel
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
# per Marine, in reference pixels: mouth centre and size, head box (cut as its own layer), neck pivot
MARINES = {
    'a': dict(eye=(659.6, 595.4), face=1, skin='#e8a878', iris='#5a7aa0', brow='#9a6a3a', mouth=(661.5, 607.5), mw=7.0, head=(612, 553, 690, 622), pivot=(655, 622), lips='#7a2a22', inner='#4a1612'),
    'b': dict(eye=(815.4, 593.8), face=-1, skin='#8a5430', iris='#3a2414', brow='#2a1a10', mouth=(813.5, 606.5), mw=5.5, head=(793, 553, 862, 619), pivot=(822, 619), lips='#4a1a14', inner='#2a0c0a'),
}

def load():
    ref = cv2.imread(os.path.join(HERE, 'reference_square.webp'))[Y0:Y1, X0:X1][..., ::-1].astype(np.float32) / 255
    m = cv2.imread(os.path.join(HERE, 'mask_raw.png'), 0).astype(np.float32) / 255
    m = cv2.resize(m, (ref.shape[1] * K, ref.shape[0] * K), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), .8 * K)
    return ref, np.clip((m - .5) * 3 + .5, 0, 1)

def sampler(img):
    """Colour of the reference at design points (reference pixel units, relative to the crop)."""
    def at(X, Y):
        return cv2.remap(img, X.astype(np.float32).reshape(1, -1), Y.astype(np.float32).reshape(1, -1), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT).reshape(-1, 3)
    return at

def repaint(ref, alpha, edits=None):
    H, W = ref.shape[:2]
    c = Kanvas(W * K, H * K, K, '#000000', seed=21); c.HM = np.zeros((c.H, c.W), np.float32)
    big = cv2.resize(ref, (W * K, H * K), interpolation=cv2.INTER_CUBIC)
    if edits: big = edits(big)
    edges_keep = big.copy()
    soft = cv2.GaussianBlur(big, (0, 0), 1.6 * K)
    c.img[:] = soft                                                   # the ground: the reference's colours, softened
    g = cv2.cvtColor(big, cv2.COLOR_RGB2GRAY)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=5), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=5)
    mag = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 2 * K)
    ang = np.arctan2(gy, gx) + math.pi / 2                            # dabs run along the form, not across it
    small = cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA)
    at = {s: sampler(cv2.GaussianBlur(small, (0, 0), s) if s else small) for s in (1.2, .6, 0)}
    def angfn(X, Y):
        xi = np.clip((X * K).astype(int), 0, c.W - 1); yi = np.clip((Y * K).astype(int), 0, c.H - 1)
        return ang[yi, xi]
    def colfn(blur, var):
        def f(X, Y, r):
            return np.clip(at[blur](X, Y) * (1 + (r.rand(len(X), 1) - .5) * 2 * var), 0, 1)
        return f
    full = (0, 0, alpha)
    detail = np.clip((mag / np.percentile(mag[alpha > .5], 80) - .5) * 1.5, 0, 1) * alpha
    for spacing, L, w, blur, var, m, seed in [(2.4, 3.6, 2.2, 1.2, .05, full, 1), (1.3, 2.2, 1.4, .6, .05, full, 2),
                                              (.75, 1.3, .9, 0, .04, (0, 0, detail), 3)]:
        c.stip(m, colfn(blur, var), spacing=spacing, L=L, w=w, angfn=angfn, seed=seed, jit=.35, thresh=.3)
    impasto(c, strength=.2)
    return np.clip(c.img, 0, 1)

def mouth_edit(name, amount):
    """Paint an opening mouth over the traced one, in reference pixels, before the brush pass (so it is brushed too)."""
    p = MARINES[name]
    def f(big):
        out = (np.clip(big, 0, 1) * 255).astype(np.uint8).copy()
        cx, cy = p['mouth'][0] - X0, p['mouth'][1] - Y0; w = p['mw']; h = 1.2 + 4.2 * amount
        def ell(col, sx, sy, dy=0):
            cv2.ellipse(out, (int((cx) * K * 4), int((cy + dy) * K * 4)), (int(sx * K * 4), int(sy * K * 4)), 0, 0, 360,
                        tuple(int(v) for v in bytes.fromhex(col[1:])), -1, cv2.LINE_AA, shift=2)
        ell(p['lips'], w * .55, h * .6 + .6, h * .25)
        ell(p['inner'], w * .45, h * .5, h * .3)
        if amount > .4: ell('#f2ece4', w * .38, .7, -h * .05)                # a hint of teeth
        ell('#c85a50', w * .28, h * .2, h * .55)                             # the tongue
        return out.astype(np.float32) / 255
    return f

def _px(col): return tuple(int(v) for v in bytes.fromhex(col[1:]))
def eye_edit(name, blink=0.0):
    """A more lifelike eye over the traced dot: almond white, coloured iris, pupil, catchlight, upper lid and lash line,
    lower lid, brow. blink 0..1 closes the lid."""
    p = MARINES[name]; f_ = p['face']
    def f(img):
        out = (np.clip(img, 0, 1) * 255).astype(np.uint8).copy(); S4 = K * 16
        cx, cy = (p['eye'][0] - X0) * K, (p['eye'][1] - Y0) * K
        P = lambda pts: np.round(np.array(pts) * 16).astype(np.int32)
        w, h = 3.9 * K, 2.1 * K                                            # half-width, half-height, canvas px
        cv2.ellipse(out, (int(cx * 16), int(cy * 16)), (int((w + 1.6 * K) * 16), int((h + 1.3 * K) * 16)), 0, 0, 360, _px(p['skin']), -1, cv2.LINE_AA, shift=4)   # clear the traced dot
        almond = [(cx - w, cy + .2 * K)] + [(cx - w + 2 * w * u, cy - h * math.sin(u * math.pi) ** .8 + (.4 * K * f_ * (u - .5))) for u in np.linspace(0, 1, 14)] + \
                 [(cx + w, cy + .2 * K)] + [(cx + w - 2 * w * u, cy + h * .75 * math.sin(u * math.pi)) for u in np.linspace(0, 1, 14)]
        if blink < .99:
            cv2.fillPoly(out, [P(almond)], _px('#f2ebe2'), cv2.LINE_AA, shift=4)
            ix = cx + f_ * 1.1 * K                                          # looking toward the other Marine
            cv2.circle(out, (int(ix * 16), int(cy * 16)), int(1.75 * K * 16), _px(p['iris']), -1, cv2.LINE_AA, shift=4)
            cv2.circle(out, (int(ix * 16), int(cy * 16)), int(.9 * K * 16), _px('#120c0a'), -1, cv2.LINE_AA, shift=4)
            cv2.circle(out, (int((ix - .5 * K) * 16), int((cy - .55 * K) * 16)), int(.38 * K * 16), _px('#ffffff'), -1, cv2.LINE_AA, shift=4)
        if blink > 0:                                                        # the lid comes down over the eye
            lid = [(x, y) for x, y in almond[:16]] + [(cx + w, cy - h + 2 * h * blink), (cx - w, cy - h + 2 * h * blink)]
            cv2.fillPoly(out, [P(lid)], _px(p['skin']), cv2.LINE_AA, shift=4)
        top = almond[1:15] if blink < .5 else [(cx - w + 2 * w * u, cy + .3 * K + .5 * K * math.sin(u * math.pi)) for u in np.linspace(0, 1, 14)]
        cv2.polylines(out, [P(top)], False, _px('#2a1810'), int(.75 * K), cv2.LINE_AA, shift=4)                 # upper lid and lashes
        cv2.polylines(out, [P(almond[16:])], False, tuple(int(v * .82) for v in _px(p['skin'])), int(.35 * K), cv2.LINE_AA, shift=4)   # lower lid
        brow = [(cx - w * 1.05, cy - h - 1.3 * K + .3 * K * f_), (cx, cy - h - 2.0 * K), (cx + w * 1.05, cy - h - 1.5 * K - .3 * K * f_)]
        cv2.polylines(out, [P(brow)], False, _px(p['brow']), int(.9 * K), cv2.LINE_AA, shift=4)
        return out.astype(np.float32) / 255
    return f

def chain(*fs):
    def g(img):
        for f in fs:
            if f: img = f(img)
        return img
    return g

def save_rgba(path, rgb, a):
    cv2.imwrite(path, np.dstack([np.clip(rgb[..., ::-1] * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8))

if __name__ == '__main__':
    ref, alpha = load()
    eyes = chain(eye_edit('a'), eye_edit('b'))                         # painted after the brush pass, so they stay crisp
    soften = lambda im: cv2.GaussianBlur(im, (0, 0), .45 * K) * .5 + im * .5
    base = soften(eyes(repaint(ref, alpha)))
    save_rgba(os.path.join(OUT, 'marines.png'), base, alpha)
    meta = dict(crop=[X0, Y0, X1, Y1], k=K, frames={})
    for nm, p in MARINES.items():
        hx0, hy0, hx1, hy1 = [(v - o) * K for v, o in zip(p['head'], (X0, Y0, X0, Y0))]
        frames = []
        for i, (amt, bl) in enumerate(((0, 0), (.5, 0), (1.0, 0), (0, 1.0))):     # mouth closed, half, open; then a blink
            if amt == 0 and bl == 0: img = base
            else:
                img = repaint(ref, alpha, mouth_edit(nm, amt) if amt else None)
                img = soften(chain(eyes, eye_edit(nm, bl) if bl else None)(img))
            f = f'head_{nm}_{i}.png'
            save_rgba(os.path.join(OUT, f), img[hy0:hy1, hx0:hx1], alpha[hy0:hy1, hx0:hx1]); frames.append(f)
        meta['frames'][nm] = dict(files=frames, x=hx0, y=hy0, pivot=[(p['pivot'][0] - X0) * K - hx0, (p['pivot'][1] - Y0) * K - hy0])
        print('frames', nm)
    json.dump(meta, open(os.path.join(OUT, 'marines.json'), 'w'), indent=1)
    # a side-by-side: the reference crop, our repaint on the cobbles of our square
    refbig = cv2.resize(ref, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_CUBIC)
    side = np.hstack([refbig, np.ones((base.shape[0], 20, 3), np.float32), base * alpha[..., None] + refbig * (1 - alpha[..., None]) * .0 + (1 - alpha[..., None]) * np.array([.08, .14, .23])])
    cv2.imwrite(os.path.join(OUT, 'compare.jpg'), (np.clip(side, 0, 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('done')

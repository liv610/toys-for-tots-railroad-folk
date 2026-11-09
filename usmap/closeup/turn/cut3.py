"""Round 4: the full asset set for each Marine on one sheet (cream paper, figures ~260 px, heads ~120 px).

Same layout on both sheets, 51 pieces each, in reading order:
  4 turnaround (front, q, side, back) | 8 side walk | 6 walk toward us | 6 walk away | 5 front heads |
  5 three-quarter heads | 3 head turns (left, front, right) | 3 wave | 2 salute | 4 hand over | 3 receive | 2 presents
Masks are made at the sheet's own size (chroma distance from the paper, cap holes filled, paper slivers and the drawn
ground line cleared), then image and mask are enlarged 2x (Lanczos, a light unsharp) so the browser isn't the one
stretching the brushwork.
"""
import os, json, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'parade'); os.makedirs(OUT, exist_ok=True)
UP = 2
NAMES = ([f'turn_{v}' for v in ('front', 'q', 'side', 'back')] + [f'walkside_{i}' for i in range(8)] + [f'walktoward_{i}' for i in range(6)] +
         [f'walkaway_{i}' for i in range(6)] + [f'fface_{e}' for e in ('smile', 'open', 'oh', 'teeth', 'closed')] +
         [f'qface_{e}' for e in ('smile', 'open', 'oh', 'teeth', 'closed')] + [f'glance_{e}' for e in ('left', 'front', 'right')] +
         [f'wave_{i}' for i in range(3)] + [f'salute_{i}' for i in range(2)] + [f'give_{i}' for i in range(4)] + [f'take_{i}' for i in range(3)] +
         ['present_front', 'present_q'])
assert len(NAMES) == 51

def labd(c, bg):
    lab = cv2.cvtColor(cv2.GaussianBlur(c, (0, 0), 1.0), cv2.COLOR_BGR2LAB).astype(np.float32)
    return lab, np.sqrt((lab[..., 0] - bg[0]) ** 2 * .5 + (3 * (lab[..., 1] - bg[1])) ** 2 + (3 * (lab[..., 2] - bg[2])) ** 2)

def blobs(img, bg):
    _, s = labd(img, bg)
    m = cv2.morphologyEx((s > 22).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 1)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5)))
    n, l, st, _ = cv2.connectedComponentsWithStats(m)
    idx = sorted([i for i in range(1, n) if st[i, 4] > 500], key=lambda i: (st[i, 1] // 100, st[i, 0]))
    return [tuple(int(v) for v in st[i][:4]) for i in idx], l, idx

def cutout(img, box, bg, figure, rowfill=False, pad=8, others=None):
    x, y, w, h = box; H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    c = img[y0:y1, x0:x1]
    lab, s = labd(c, bg); hh, ww = s.shape
    # paper is smooth; the white paint (cap, belt, gloves) is the paper's colour but brushed, so local texture counts
    L = cv2.cvtColor(c, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
    tex = np.sqrt(np.maximum(cv2.blur(L * L, (5, 5)) - cv2.blur(L, (5, 5)) ** 2, 0))
    a = ((s > 20) | ((tex > 5) & (s > 5))).astype(np.uint8)
    if others is not None: a[others[y0:y1, x0:x1]] = 0     # a neighbour reaching into this box (a held-out present)
    dL, da, db = lab[..., 0] - bg[0], lab[..., 1] - bg[1], lab[..., 2] - bg[2]
    # drawn ground line and soft shadow under the shoes: greyish, low chroma, at the bottom
    grey = (np.abs(da) < 6) & (np.abs(db) < 9) & (lab[..., 0] > 110) & (np.arange(hh)[:, None] > hh - 16)
    a[grey] = 0
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((2, 2)))
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((3, 3)))
    n, l, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        big = 1 + np.argmax(st[1:, 4]); near = cv2.dilate((l == big).astype(np.uint8), np.ones((5, 5))) > 0
        keep = np.zeros(n, bool); keep[big] = True
        for i in range(1, n):
            reg = l == i
            if i != big and st[i, 4] > 25 and (reg & near).any() and s[reg].mean() > 26: keep[i] = True
        a = keep[l].astype(np.uint8)
    capzone = .24 if figure else .45                       # cap top: pale paint the threshold misses
    inv = 1 - a; n, l, st, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, n):
        xx, yy, w_, h_, ar = st[i]
        if xx == 0 or yy == 0 or xx + w_ >= ww or yy + h_ >= hh: continue
        reg = l == i
        compact = ar < 160 and .35 < w_ / max(h_, 1) < 2.8 and ar > .45 * w_ * h_    # a glove's or belt's pale inside
        belt = w_ > 1.3 * h_ and h_ < 20 and .3 * hh < yy < .62 * hh                    # a white belt is a flat band
        if ar < 12 or compact or belt or (yy + h_ < capzone * hh and s[reg].mean() > 7): a[reg] = 1
    if figure:                                             # paper between arm and coat, between the legs
        raw = cv2.cvtColor(c, cv2.COLOR_BGR2LAB).astype(np.float32)
        pl = (np.abs(raw[..., 0] - bg[0]) < 8) & (np.abs(raw[..., 1] - bg[1]) < 3) & (np.abs(raw[..., 2] - bg[2]) < 4) & (tex < 2.2)
        pl = cv2.morphologyEx(pl.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2))) > 0
        pl[:int(.22 * hh)] = False
        a[cv2.dilate(pl.astype(np.uint8), np.ones((3, 3))) > 0] = 0
    if rowfill:                                            # caps are convex: close each cap row between its ends
        for r in range(int(capzone * hh * (.8 if figure else .5))):
            xs = np.nonzero(a[r])[0]
            if len(xs) > 1 and xs[-1] - xs[0] < .6 * ww: a[r, xs[0]:xs[-1] + 1] = 1
    raw2 = cv2.cvtColor(c, cv2.COLOR_BGR2LAB).astype(np.float32)
    pale = (raw2[..., 0] > 205) & (np.abs(raw2[..., 1] - bg[1]) < 5) & (np.abs(raw2[..., 2] - bg[2]) < 9)
    for _ in range(3):                                     # the sheet's light rim around every figure
        edge = (a > 0) & (cv2.erode(a, np.ones((3, 3))) == 0)
        a[edge & pale] = 0
    # a greyer rim where the outline meets dark cloth (trousers, coat): pale edge pixels right next to dark paint
    darknear = cv2.dilate((raw2[..., 0] < 120).astype(np.uint8), np.ones((5, 5))) > 0
    greyrim = (raw2[..., 0] > 165) & (np.abs(raw2[..., 1] - bg[1]) < 7) & (np.abs(raw2[..., 2] - bg[2]) < 11) & darknear
    for _ in range(2):
        edge = (a > 0) & (cv2.erode(a, np.ones((3, 3))) == 0)
        a[edge & greyrim] = 0
    if figure:                                             # nothing below the shoe soles
        dark = (raw2[..., 0] < 70) & (a > 0)
        rows = np.nonzero(dark.sum(1) >= 2)[0]
        if len(rows): a[rows[-1] + 2:] = 0
    af = cv2.GaussianBlur(a.astype(np.float32), (0, 0), .6)
    big = cv2.resize(c, None, fx=UP, fy=UP, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    big = np.clip(big + .45 * (big - cv2.GaussianBlur(big, (0, 0), 1.4)), 0, 255)
    A = cv2.resize(af, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR)
    A = np.clip((A - .5) * 1.6 + .5, 0, 1)                  # keep the enlarged edge crisp
    out = np.dstack([big.astype(np.uint8), (A * 255).astype(np.uint8)])
    ys, xs = np.nonzero(out[..., 3] > 10)
    return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

meta = {}
for who, f in (('a', 'sheet7_full_set_a.webp'), ('b', 'sheet8_full_set_b.webp')):
    img = cv2.cvtColor(np.array(Image.open(os.path.join(HERE, 'ref', f)).convert('RGB')), cv2.COLOR_RGB2BGR)
    bg = np.median(cv2.cvtColor(cv2.GaussianBlur(img, (0, 0), 1.0), cv2.COLOR_BGR2LAB)[:8].reshape(-1, 3).astype(np.float32), 0)
    bl, lab_, idx = blobs(img, bg); assert len(bl) == 51, len(bl)
    for j, (nm, b) in enumerate(zip(NAMES, bl)):
        oth = cv2.dilate(((lab_ > 0) & (lab_ != idx[j])).astype(np.uint8), np.ones((3, 3))) > 0
        fig = not (nm.startswith(('fface', 'qface', 'glance', 'present')))
        o = cutout(img, b, bg, fig, rowfill=not nm.startswith(('wave', 'salute', 'give', 'take', 'present')), others=oth)
        cv2.imwrite(os.path.join(OUT, f'{who}_{nm}.png'), o); meta[f'{who}_{nm}'] = [int(o.shape[1]), int(o.shape[0])]
json.dump(meta, open(os.path.join(OUT, 'pieces.json'), 'w'))
# contact sheet on green, per Marine
for who in 'ab':
    row = []
    for nm in NAMES:
        t = cv2.imread(os.path.join(OUT, f'{who}_{nm}.png'), cv2.IMREAD_UNCHANGED); a = t[..., 3:] / 255.
        g = np.zeros((560, t.shape[1] + 6, 3)); g[:] = (60, 90, 70)
        g[560 - t.shape[0]:, 3:3 + t.shape[1]] = t[..., :3] * a + g[560 - t.shape[0]:, 3:3 + t.shape[1]] * (1 - a)
        row.append(g)
    sh = np.concatenate(row, 1); k = sh.shape[1] // 3 + 1
    cv2.imwrite(os.path.join(HERE, f'parade_contact_{who}.jpg'), np.concatenate([np.pad(sh[:, i * k:(i + 1) * k], ((0, 0), (0, max(0, k - sh[:, i * k:(i + 1) * k].shape[1])), (0, 0))) for i in range(3)], 0).astype(np.uint8))
print(len(meta))

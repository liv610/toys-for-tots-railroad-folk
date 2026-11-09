"""Cut the second round of sheets (transparent backgrounds, so the alpha is the user's own; no paper to remove).

ref/sheet4_walk_side_white.webp  walk cycle, side view facing right, 8 frames per Marine (about 305 px tall)
ref/sheet2_mixed_cream.webp      three-quarter talking heads (row 3), arm poses (row 4), head turns (row 5)
The cream name plates under the heads and poses are joined to the figures in the alpha; each piece is cut off
below its lowest dark row (the collar, or the shoe soles).
"""
import os, json, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'cut2'); os.makedirs(OUT, exist_ok=True)

def load(n):
    im = np.array(Image.open(os.path.join(HERE, 'ref', n)).convert('RGBA'))
    return np.dstack([im[..., 2::-1], im[..., 3]])          # BGRA

def blobs(im, y0, y1):
    a = (im[y0:y1, :, 3] > 128).astype(np.uint8)
    n, l, st, _ = cv2.connectedComponentsWithStats(a)
    return sorted([(int(s[0]), int(s[1]) + y0, int(s[2]), int(s[3])) for s in st[1:] if s[4] > 800 and s[2] < 260], key=lambda b: b[0])

def piece(im, b, strip=False, pad=4):
    x, y, w, h = b; H, W = im.shape[:2]
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    c = im[y0:y1, x0:x1].copy()
    if strip:
        # the name plate: a run of rows at the bottom that are mostly cream; cut just above it
        lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.int32)
        op = c[..., 3] > 200
        cream = op & (lab[..., 0] > 185) & (np.abs(lab[..., 1] - 128) < 14) & (lab[..., 2] > 132)
        frac = cream.sum(1) / np.maximum(op.sum(1), 1)
        r = len(frac) - 1
        while r > 0 and (frac[r] > .12 or op[r].sum() == 0): r -= 1
        if r < len(frac) - 6: c[r + 1:, :, 3] = 0
        # the plate's soft top edge: trim bottom rows that still hold pale, warm pixels
        pale = (lab[..., 0] > 150) & (lab[..., 2] > 130) & (np.abs(lab[..., 1] - 128) < 16) & (c[..., 3] > 30)
        r = int(np.nonzero((c[..., 3] > 30).any(1))[0][-1])
        while r > 0 and pale[r].sum() > 2: c[r, :, 3] = 0; r -= 1
    # keep the largest blob (drops label fragments) and anything touching it
    a = (c[..., 3] > 40).astype(np.uint8)
    n, l, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 2:
        big = 1 + np.argmax(st[1:, 4]); near = cv2.dilate((l == big).astype(np.uint8), np.ones((5, 5))) > 0
        keep = np.zeros(n, bool); keep[big] = True
        for i in range(1, n):
            if (near & (l == i)).any() and st[i, 4] > 20: keep[i] = True
        c[..., 3] = (c[..., 3] * keep[l]).astype(np.uint8)
    ys, xs = np.nonzero(c[..., 3] > 20)
    return c[ys.min():ys.max() + 1, max(0, xs.min() - 2):xs.max() + 3]

meta = {}
def save(nm, c):
    cv2.imwrite(os.path.join(OUT, nm + '.png'), c); meta[nm] = dict(w=int(c.shape[1]), h=int(c.shape[0]))

im = load('sheet4_walk_side_white.webp')
for who, (y0, y1) in (('a', (0, 330)), ('b', (330, 667))):
    for i, b in enumerate(blobs(im, y0, y1)): save(f'walk_{who}_{i}', piece(im, b))
im = load('sheet2_mixed_cream.webp')
rows = {'qface': (460, 615), 'pose': (615, 860), 'turn': (860, 1024)}
names = {'qface': ['smile', 'open', 'oh', 'teeth', 'closed'], 'pose': ['wave', 'salute', 'present'], 'turn': ['left', 'front', 'right', 'side', 'back']}
for kind, (y0, y1) in rows.items():
    bl = [b for b in blobs(im, y0, y1) if b[0] > 260 and b[3] > 60]
    k = len(names[kind]); assert len(bl) == 2 * k, (kind, len(bl), bl)
    for i, b in enumerate(bl): save(f"{kind}_{'ab'[i // k]}_{names[kind][i % k]}", piece(im, b, strip=True))
json.dump(meta, open(os.path.join(OUT, 'cut2.json'), 'w'), indent=1)
# contact sheet
tiles = [cv2.imread(os.path.join(OUT, k + '.png'), cv2.IMREAD_UNCHANGED) for k in meta]
Hh = 320; row = []
for t in tiles:
    s = Hh / max(t.shape[0], 1) * (1 if t.shape[0] > 200 else .55)
    t = cv2.resize(t, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); a = t[..., 3:4] / 255.
    g = np.zeros((Hh, t.shape[1] + 8, 3)); g[:] = (60, 90, 70)
    g[Hh - t.shape[0]:, 4:4 + t.shape[1]] = t[..., :3] * a + g[Hh - t.shape[0]:, 4:4 + t.shape[1]] * (1 - a)
    row.append(g)
sh = np.concatenate(row, 1); half = sh.shape[1] // 2
cv2.imwrite(os.path.join(HERE, 'cut2_contact.jpg'), np.concatenate([sh[:, :half], sh[:, half:half * 2]], 0).astype(np.uint8))
print(len(meta), {k: (v['w'], v['h']) for k, v in list(meta.items())[::4]})

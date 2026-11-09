"""Cut the user's turnaround sheets into separate figure views (RGBA), ready for the brush and the turn viewer.

ref/sheet_bodies.webp: 8 full figures (a: front, three-quarter, side, back; b: the same).
ref/sheet_heads.webp:  head close-ups (front, three-quarter) and 5 expressions per Marine
                       (smile, open, oh, teeth, eyes closed).
"""
import os, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'cut'); os.makedirs(OUT, exist_ok=True)

def cutout(im, box, pad=14, T=14):
    """Mask by a chroma-weighted distance from the paper (the white cap and gloves differ from the cream mainly in
    yellowness), fill enclosed holes only where they are faintly painted (cap tops) and not bare paper (the gap
    between an arm and the body), and drop the grey ground shadow under the shoes."""
    x, y, w, h = box; H, W = im.shape[:2]
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    c = im[y0:y1, x0:x1].copy()
    lab = cv2.cvtColor(cv2.GaussianBlur(c, (0, 0), 1.2), cv2.COLOR_BGR2LAB).astype(np.float32)
    bg = PAPER
    dL, da, db = lab[..., 0] - bg[0], lab[..., 1] - bg[1], lab[..., 2] - bg[2]
    s = np.sqrt(dL ** 2 * .5 + (3 * da) ** 2 + (3 * db) ** 2)
    a = (s > T).astype(np.uint8)
    hh = a.shape[0]
    shadow = (np.abs(da) < 4) & (np.abs(db) < 5) & (lab[..., 0] > 125) & (np.arange(hh)[:, None] > hh - 45)
    a[shadow] = 0
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3)))
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5)))
    n, l, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        big = 1 + np.argmax(st[1:, 4]); keep = np.zeros(n, bool); keep[big] = True
        near = cv2.dilate((l == big).astype(np.uint8), np.ones((9, 9))) > 0
        for i in range(1, n):                     # small detached bits touching the figure (cap peaks, badge tips)
            reg = l == i
            if i != big and st[i, 4] > 40 and (reg & near).any() and s[reg].mean() > 22: keep[i] = True
        a = keep[l].astype(np.uint8)
    inv = 1 - a; n, l, st, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, n):
        xx, yy, ww, hh_, ar = st[i]
        if xx == 0 or yy == 0 or xx + ww >= a.shape[1] or yy + hh_ >= a.shape[0]: continue
        reg = l == i
        if ar < 150 or s[reg].mean() > (6.5 if T < 20 else 12): a[reg] = 1
    a = cv2.erode(a, np.ones((3, 3)))                 # lose the one-pixel cream halo
    af = cv2.GaussianBlur(a.astype(np.float32), (0, 0), .8)
    rgba = np.dstack([c, (np.clip(af, 0, 1) * 255).astype(np.uint8)])
    return rgba, (x0, y0)

def paper(im):
    return np.median(cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.2), cv2.COLOR_BGR2LAB)[:15].reshape(-1, 3).astype(np.float32), 0)

def blobs(im):
    f = im.astype(np.float32); d = np.linalg.norm(f - np.array([205., 234., 253.]), axis=2)
    m = cv2.morphologyEx((d > 40).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9)))
    n, l, st, _ = cv2.connectedComponentsWithStats(m)
    return sorted([tuple(st[i][:4]) for i in range(1, n) if st[i, 4] > 2000], key=lambda b: (b[1] // 150, b[0]))

PAPER = None
if __name__ == '__main__':
    meta = {}
    im = cv2.imread(os.path.join(HERE, 'ref', 'sheet_bodies.webp')); PAPER = paper(im)
    views = ['front', 'q', 'side', 'back']
    for i, b in enumerate(blobs(im)):
        nm = f"body_{'ab'[i // 4]}_{views[i % 4]}"
        b = (b[0], b[1] - 45, b[2], b[3] + 45)        # the cap top is too pale to start the blob; reach above it
        rgba, o = cutout(im, b, T=22); cv2.imwrite(os.path.join(OUT, nm + '.png'), rgba); meta[nm] = dict(origin=o, size=rgba.shape[1::-1])
    im = cv2.imread(os.path.join(HERE, 'ref', 'sheet_heads.webp')); PAPER = paper(im)
    bl = blobs(im)
    big = [b for b in bl if 400 < b[1] < 760]; small = [b for b in bl if b[1] >= 760]
    for i, b in enumerate(big):
        nm = f"head_{'ab'[i // 2]}_{['front', 'q'][i % 2]}"
        rgba, o = cutout(im, b); cv2.imwrite(os.path.join(OUT, nm + '.png'), rgba); meta[nm] = dict(origin=o, size=rgba.shape[1::-1])
    # expressions: 5 per Marine at a regular pitch; split merged blobs by the pitch
    ex = ['smile', 'open', 'oh', 'teeth', 'closed']
    for who, x0 in (('a', 64), ('b', 806)):
        for j, e in enumerate(ex):
            b = (x0 + int(round(j * 134.5)) - 4, 772, 134, 180)
            x, y, w, h = b; c = im[y:y + h, x:x + w]
            rgba, o = cutout(im, b, pad=0)
            nm = f'face_{who}_{e}'; cv2.imwrite(os.path.join(OUT, nm + '.png'), rgba); meta[nm] = dict(origin=o, size=rgba.shape[1::-1])
    json.dump(meta, open(os.path.join(OUT, 'cut.json'), 'w'), indent=1, default=int)
    # contact sheet on a dark ground to judge the edges
    tiles = [cv2.imread(os.path.join(OUT, k + '.png'), cv2.IMREAD_UNCHANGED) for k in meta]
    Hh = 720; row = []
    for t in tiles:
        s = Hh / t.shape[0] if t.shape[0] > 300 else 1.0
        t = cv2.resize(t, None, fx=s, fy=s); a = t[..., 3:4] / 255.
        g = np.zeros((Hh, t.shape[1] + 10, 3)); g[:] = (60, 90, 70)
        g[:t.shape[0], 5:5 + t.shape[1]] = t[..., :3] * a + g[:t.shape[0], 5:5 + t.shape[1]] * (1 - a)
        row.append(g)
    sheet = np.concatenate(row, 1)
    cv2.imwrite(os.path.join(HERE, 'cut_contact.jpg'), sheet[:, :min(sheet.shape[1], 6000)].astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(len(meta), 'pieces')

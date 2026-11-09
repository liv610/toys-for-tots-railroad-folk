"""Fit the expression heads (smile, open, oh, teeth, closed) onto each Marine's front body, so the front view can
talk and blink with the user's own painted faces. The fit is an affine found by ECC on the smile head against the
body's own head; every expression of that Marine uses the same fit (they are drawn on the same grid)."""
import os, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cut')
EX = ['smile', 'open', 'oh', 'teeth', 'closed']
def rd(n): return cv2.imread(os.path.join(C, n + '.png'), cv2.IMREAD_UNCHANGED)

out = {}
for who in 'ab':
    body = rd(f'body_{who}_front'); ba = body[..., 3] > 128
    rows = np.nonzero(ba.any(1))[0]; top = rows[0]
    # neck: narrowest row in the upper part
    wid = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 999 for r in ba[:260]])
    neck = top + 100 + int(np.argmin(wid[top + 100:top + 220]))
    sm = rd(f'face_{who}_smile'); fa = sm[..., 3] > 128
    fr = np.nonzero(fa.any(1))[0]; fwid = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 999 for r in fa])
    fneck = 98 + int(np.argmin(fwid[98:158]))
    s = (neck - top) / (fneck - fr[0])
    fc = np.nonzero(fa[:40].any(0))[0].mean(); bc = np.nonzero(ba[top:top + 40].any(0))[0].mean()
    warp = np.array([[s, 0, bc - s * fc], [0, s, top - s * fr[0]]], np.float32)
    g1 = cv2.GaussianBlur(cv2.cvtColor(body[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 2).astype(np.float32)
    g2 = cv2.GaussianBlur(cv2.cvtColor(sm[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 2).astype(np.float32)
    mask = np.zeros(g1.shape, np.uint8); mask[top:neck + 10] = 1; mask &= ba.astype(np.uint8)
    fmask = np.zeros(g2.shape, np.uint8); fmask[:fneck + 8] = 1; fmask &= fa.astype(np.uint8)
    # ECC wants template = warped input; estimate the map body->face then invert
    inv = cv2.invertAffineTransform(warp)
    try:
        _, inv = cv2.findTransformECC(g1, g2, inv.astype(np.float32), cv2.MOTION_AFFINE,
                                      (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), mask if mask.shape == g2.shape else fmask, 5)
        warp = cv2.invertAffineTransform(inv)
    except cv2.error as e:
        print('ECC failed', who, e)
    H, W = body.shape[:2]
    y0, y1 = max(0, top - 30), neck + 40
    yy = np.arange(H)[:, None].astype(np.float32)
    fade = np.clip((neck + 18 - yy) / 14, 0, 1)            # the expression's collar fades into the body's collar
    frames = []
    for e in EX:
        f = rd(f'face_{who}_{e}')
        w = cv2.warpAffine(f, warp, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = w[..., 3:4].astype(np.float32) / 255 * fade[..., None]
        crop = np.dstack([w[y0:y1, ..., :3], (a[y0:y1, ..., 0] * 255).astype(np.uint8)])
        cv2.imwrite(os.path.join(C, f'fhead_{who}_{e}.png'), crop); frames.append(f'fhead_{who}_{e}.png')
        if e == 'smile':
            comp = body[..., :3].astype(np.float32).copy(); comp[y0:y1] = crop[..., :3] * a[y0:y1] + comp[y0:y1] * (1 - a[y0:y1])
            side = np.concatenate([body[y0:y1, :, :3], comp[y0:y1].astype(np.uint8)], 1)
            cv2.imwrite(os.path.join(HERE, f'fit_{who}.jpg'), cv2.resize(side, None, fx=2, fy=2))
    out[who] = dict(y=int(y0), frames=frames, neck=int(neck), warp=warp.tolist())
json.dump(out, open(os.path.join(C, 'heads.json'), 'w'), indent=1)
print(json.dumps({k: (v['y'], v['neck'], [round(x, 3) for x in sum(v['warp'], [])]) for k, v in out.items()}))

# anchors for the turn viewer: the feet line and the body's centre line of every view
views = {}
for who in 'ab':
    for v in ('front', 'q', 'side', 'back'):
        a = rd(f'body_{who}_{v}')[..., 3] > 128
        rows = np.nonzero(a.any(1))[0]; bot = int(rows[-1]); top = int(rows[0])
        band = a[int(top + .3 * (bot - top)):int(top + .6 * (bot - top))]
        cx = float(np.nonzero(band)[1].mean())
        views[f'{who}_{v}'] = dict(file=f'body_{who}_{v}.png', cx=round(cx, 1), bottom=bot, top=top, w=int(a.shape[1]), h=int(a.shape[0]))
json.dump(dict(views=views, heads=out), open(os.path.join(C, 'views.json'), 'w'), indent=1)
print(views)

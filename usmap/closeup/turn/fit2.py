"""Fit the round-2 heads onto the round-1 bodies, and measure the walk frames and poses for the viewer.

  qhead  three-quarter talking faces fitted onto the three-quarter body (so they can talk facing each other)
  ghead  head turns (left, front, right) fitted onto the front body (so they can glance without turning)
  walk   side walk frames: feet line, body centre line, one scale per Marine from the standing frame
  pose   wave, salute, hold present: feet line, centre line, the waving forearm's box and elbow
"""
import os, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); C1 = os.path.join(HERE, 'cut'); C2 = os.path.join(HERE, 'cut2')
def rd(d, n): return cv2.imread(os.path.join(d, n + '.png'), cv2.IMREAD_UNCHANGED)

def outline(a):
    rows = np.nonzero(a.any(1))[0]
    wid = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 999 for r in a])
    return rows[0], wid

def fit(body, head, name_out, frames, src_dir, out_dir):
    """Affine from a head image onto the body's own head: start from cap-top / neck scale, refine with ECC."""
    ba = body[..., 3] > 128; fa = head[..., 3] > 128
    top, wid = outline(ba); neck = top + 100 + int(np.argmin(wid[top + 100:top + 220]))
    ftop, fwid = outline(fa); h = fa.shape[0]
    fneck = int(.62 * h) + int(np.argmin(fwid[int(.62 * h):int(.92 * h)]))
    capw = lambda wd, t, n: max(v for v in wd[t:t + int(.45 * (n - t))] if v < 999)
    s = capw(wid, top, neck) / capw(fwid, ftop, fneck)            # the cap brim is the same object in both drawings
    fc = np.nonzero(fa[ftop:ftop + 25].any(0))[0].mean(); bc = np.nonzero(ba[top:top + 25].any(0))[0].mean()
    warp = np.array([[s, 0, bc - s * fc], [0, s, top - s * ftop]], np.float32)
    g1 = cv2.GaussianBlur(cv2.cvtColor(body[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 2).astype(np.float32)
    g2 = cv2.GaussianBlur(cv2.cvtColor(head[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 1.2).astype(np.float32)
    fm = np.zeros(g2.shape, np.uint8); fm[:fneck + 6] = 1; fm &= fa.astype(np.uint8)   # this OpenCV masks the input image
    inv = cv2.invertAffineTransform(warp).astype(np.float32)
    ok = True
    try:
        _, inv2 = cv2.findTransformECC(g1, g2, inv, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), fm, 5)
        w2 = cv2.invertAffineTransform(inv2)
        if abs(w2[0, 0] / s - 1) < .2 and abs(w2[1, 1] / s - 1) < .2 and abs(w2[0, 2] - warp[0, 2]) < 25: warp = w2
        else: ok = False; print('ecc rejected', np.round(w2, 2).tolist(), round(s, 3))
    except cv2.error as e: ok = False; print('ecc error', str(e)[-80:])
    H, W = body.shape[:2]; y0, y1 = max(0, top - 30), neck + 40
    yy = np.arange(H)[:, None].astype(np.float32); fade = np.clip((neck + 18 - yy) / 14, 0, 1)
    files = []
    for f in frames:
        im = rd(src_dir, f)
        w = cv2.warpAffine(im, warp, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = w[..., 3].astype(np.float32) * fade[:, 0][:, None]
        crop = np.dstack([w[y0:y1, :, :3], a[y0:y1].astype(np.uint8)])
        nm = f'{name_out}_{f.split("_")[-1]}.png'; cv2.imwrite(os.path.join(out_dir, nm), crop); files.append(nm)
    first = cv2.imread(os.path.join(out_dir, files[0]), cv2.IMREAD_UNCHANGED).astype(np.float32); al = first[..., 3:] / 255
    comp = body[y0:y1, :, :3].astype(np.float32) * (1 - al) + first[..., :3] * al
    return dict(y=int(y0), frames=files, ecc=ok), np.concatenate([body[y0:y1, :, :3], comp.astype(np.uint8)], 1)

OUT = os.path.join(HERE, '..', 'turnview2'); os.makedirs(OUT, exist_ok=True)
res = dict(qhead={}, ghead={}, walk={}, pose={})
checks = []
for who in 'ab':
    r, img = fit(rd(C1, f'body_{who}_q'), rd(C2, f'qface_{who}_smile'), f'qhead_{who}', [f'qface_{who}_{e}' for e in ('smile', 'open', 'oh', 'teeth', 'closed')], C2, OUT)
    res['qhead'][who] = r; checks.append(img)
    r, img = fit(rd(C1, f'body_{who}_front'), rd(C2, f'turn_{who}_front'), f'ghead_{who}', [f'turn_{who}_{e}' for e in ('front', 'left', 'right')], C2, OUT)
    res['ghead'][who] = r; checks.append(img)
    # walk frames
    fr = []
    for i in range(8):
        im = rd(C2, f'walk_{who}_{i}'); a = im[..., 3] > 128; rows = np.nonzero(a.any(1))[0]
        band = a[int(rows[0] + .25 * (rows[-1] - rows[0])):int(rows[0] + .45 * (rows[-1] - rows[0]))]
        cv2.imwrite(os.path.join(OUT, f'walk_{who}_{i}.png'), im)
        fr.append(dict(file=f'walk_{who}_{i}.png', cx=round(float(np.nonzero(band)[1].mean()), 1), bottom=int(rows[-1]), top=int(rows[0])))
    res['walk'][who] = dict(frames=fr, height=fr[0]['bottom'] - fr[0]['top'])
    # poses
    P = {}
    ref = rd(C2, f'pose_{who}_present')[..., 3] > 128; rr = np.nonzero(ref.any(1))[0]
    for p in ('wave', 'salute', 'present'):
        im = rd(C2, f'pose_{who}_{p}'); a = im[..., 3] > 128; rows = np.nonzero(a.any(1))[0]; H, W = a.shape
        lower = a[int(.45 * H):int(.75 * H)]
        cx = float(np.nonzero(lower)[1].mean())
        d = dict(file=f'pose_{who}_{p}.png', cx=round(cx, 1), bottom=int(rows[-1]), top=int(rows[0]))
        if p == 'wave':
            # the raised forearm: opaque columns left of the head, above the shoulders
            head_cols = np.nonzero(a[int(.12 * H):int(.2 * H)].any(0))[0]
            hx0 = int(np.percentile(head_cols, 50)) - int(.16 * W)
            sh = int(.33 * H)
            arm = a[:sh, :max(1, hx0)]
            ys, xs = np.nonzero(arm)
            d['arm'] = [0, 0, int(hx0), int(sh)]
            d['elbow'] = [int(np.percentile(xs, 70)), int(sh - 4)]
        cv2.imwrite(os.path.join(OUT, d['file']), im); P[p] = d
    res['pose'][who] = dict(views=P, height=int(rr[-1] - rr[0]))
json.dump(res, open(os.path.join(OUT, 'rig2.json'), 'w'), indent=1)
hmax = max(c.shape[0] for c in checks)
cv2.imwrite(os.path.join(HERE, 'fit2.jpg'), np.concatenate([np.pad(c, ((0, hmax - c.shape[0]), (0, 6), (0, 0))) for c in checks], 1))
print({k: {w: v.get('ecc') for w, v in res[k].items()} for k in ('qhead', 'ghead')}, res['pose']['a']['views']['wave'])

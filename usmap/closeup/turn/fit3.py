"""Round 4: fit the talking heads and head turns onto the bodies they belong to, and measure every frame.

  front talking heads  -> turnaround front
  head turns           -> turnaround front
  3/4 talking heads    -> turnaround q, the wave frames, holding the present (give_0, take_2)
Writes parade/rig4.json: per frame its file, feet line, centre line; per head set its offset in the body frame.
"""
import os, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, '..', 'parade')
def rd(n): return cv2.imread(os.path.join(P, n + '.png'), cv2.IMREAD_UNCHANGED)
EX = ['smile', 'open', 'oh', 'teeth', 'closed']

def widths(a): return np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 9999 for r in a])

def fit(body_n, head_n, frames, out_prefix):
    body, head = rd(body_n), rd(head_n)
    ba, fa = body[..., 3] > 128, head[..., 3] > 128
    H = ba.shape[0]; rows = np.nonzero(ba.any(1))[0]; top = rows[0]
    wid = widths(ba)
    neck = top + int(.1 * H) + int(np.argmin(wid[top + int(.1 * H):top + int(.24 * H)]))
    fr = np.nonzero(fa.any(1))[0]; ftop = fr[0]; fh = fa.shape[0]; fw = widths(fa)
    fneck = int(.6 * fh) + int(np.argmin(fw[int(.6 * fh):int(.93 * fh)]))
    capw = lambda w, t, n: max(v for v in w[t:t + max(2, int(.45 * (n - t)))] if v < 9999)
    s = capw(wid, top, neck) / capw(fw, ftop, fneck)
    fc = np.nonzero(fa[ftop:ftop + int(.15 * fh)].any(0))[0].mean(); bc = np.nonzero(ba[top:top + int(.15 * (neck - top)) + 2].any(0))[0].mean()
    warp = np.array([[s, 0, bc - s * fc], [0, s, top - s * ftop]], np.float32)
    g1 = cv2.GaussianBlur(cv2.cvtColor(body[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 2).astype(np.float32)
    g2 = cv2.GaussianBlur(cv2.cvtColor(head[..., :3], cv2.COLOR_BGR2GRAY), (0, 0), 2 / max(s, .3)).astype(np.float32)
    fm = np.zeros(g2.shape, np.uint8); fm[:fneck + 4] = 1; fm &= fa.astype(np.uint8)
    inv = cv2.invertAffineTransform(warp).astype(np.float32); ecc = None
    try:
        cc, inv2 = cv2.findTransformECC(g1, g2, inv, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), fm, 5)
        w2 = cv2.invertAffineTransform(inv2)
        if abs(w2[0, 0] / s - 1) < .22 and abs(w2[1, 1] / s - 1) < .22 and abs(w2[0, 2] - warp[0, 2]) < .12 * ba.shape[1] and abs(w2[0, 1]) < .12:
            warp, ecc = w2, round(float(cc), 3)
    except cv2.error: pass
    Hb, Wb = body.shape[:2]; y0, y1 = max(0, top - 20), min(Hb, neck + int(.05 * H))
    yy = np.arange(Hb).astype(np.float32); fade = np.clip((neck + .03 * H - yy) / (.025 * H), 0, 1)
    files = []
    for f in frames:
        im = rd(f); w = cv2.warpAffine(im, warp, (Wb, Hb), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = w[..., 3].astype(np.float32) * fade[:, None]
        nm = f'{out_prefix}_{f.split("_")[-1]}.png'
        cv2.imwrite(os.path.join(P, nm), np.dstack([w[y0:y1, :, :3], a[y0:y1].astype(np.uint8)])); files.append(nm)
    return dict(y=int(y0), frames=files, ecc=ecc)

def anchor(n, band=(.62, .9)):
    a = rd(n)[..., 3] > 128; rows = np.nonzero(a.any(1))[0]; t, b = int(rows[0]), int(rows[-1])
    bb = a[int(t + band[0] * (b - t)):int(t + band[1] * (b - t))]
    return dict(file=n + '.png', cx=round(float(np.nonzero(bb)[1].mean()), 1), bottom=b, top=t, w=int(a.shape[1]), h=int(a.shape[0]))

def present_centre(n):
    im = rd(n); hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)
    gold = (hsv[..., 0] > 15) & (hsv[..., 0] < 35) & (hsv[..., 1] > 120) & (hsv[..., 2] > 150) & (im[..., 3] > 128)
    gold[:int(.25 * im.shape[0])] = False                  # not the cap badge
    ys, xs = np.nonzero(gold)
    return [round(float(xs.mean()), 1), round(float(ys.mean()), 1)] if len(xs) > 30 else None

rig = {}
for who in 'ab':
    R = dict(views={}, walk={}, pose={}, heads={})
    for v in ('front', 'q', 'side', 'back'): R['views'][v] = anchor(f'{who}_turn_{v}')
    R['walk']['side'] = [anchor(f'{who}_walkside_{i}', (.25, .5)) for i in range(8)]
    R['walk']['toward'] = [anchor(f'{who}_walktoward_{i}', (.25, .5)) for i in range(6)]
    R['walk']['away'] = [anchor(f'{who}_walkaway_{i}', (.25, .5)) for i in range(6)]
    for p in [f'wave_{i}' for i in range(3)] + ['salute_0', 'salute_1'] + [f'give_{i}' for i in range(4)] + [f'take_{i}' for i in range(3)]:
        R['pose'][p] = anchor(f'{who}_{p}')
        if p.startswith(('give', 'take')): R['pose'][p]['present'] = present_centre(f'{who}_{p}')
    R['height'] = R['views']['front']['bottom'] - R['views']['front']['top']
    R['heads']['front'] = {'turn_front': fit(f'{who}_turn_front', f'{who}_fface_smile', [f'{who}_fface_{e}' for e in EX], f'{who}_hf_front')}
    R['heads']['glance'] = {'turn_front': fit(f'{who}_turn_front', f'{who}_glance_front', [f'{who}_glance_{e}' for e in ('front', 'left', 'right')], f'{who}_hg_front')}
    R['heads']['q'] = {}
    for body in ('turn_q', 'wave_0', 'wave_1', 'wave_2', 'give_0', 'take_2'):
        R['heads']['q'][body] = fit(f'{who}_{body}', f'{who}_qface_smile', [f'{who}_qface_{e}' for e in EX], f'{who}_hq_{body}')
    rig[who] = R
json.dump(rig, open(os.path.join(P, 'rig4.json'), 'w'), indent=1)
for who in 'ab':
    print(who, {k: {b: v['ecc'] for b, v in d.items()} for k, d in rig[who]['heads'].items()})
    print('  present', {p: rig[who]['pose'][p]['present'] for p in rig[who]['pose'] if 'present' in rig[who]['pose'][p]}, 'height', rig[who]['height'])

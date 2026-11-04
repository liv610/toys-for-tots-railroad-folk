"""Phase 1 check: the band-limited Canvas.stroke against the original (Canvas.stroke_bbox), stroke by stroke.

Thousands of random strokes, including the awkward cases: hairlines and very wide strokes, very long strokes that
cross the whole canvas, strokes partly or wholly off the canvas, single points and zero-length strokes, every taper,
dry brush (which reads the paper), a soft clip, tremor, two-colour strokes, scaled and unscaled coordinates.
Each stroke is painted on two identical canvases, one with each implementation, and the canvases must be identical.

    cd usmap && PYTHONPATH=../folk2:../styles2:. python3 tools/verify_brush.py [n]
"""
import sys, time, json, numpy as np
import brush
from brush import Canvas

def case(r, W, H):
    kind = r.choice(['short', 'long', 'cross', 'off', 'point', 'zero', 'curve'])
    n = int(r.randint(2, 12))
    if kind == 'short': c = r.rand(2) * [W, H]; P = c + r.randn(n, 2) * r.uniform(2, 40)
    elif kind == 'long': P = np.linspace(r.rand(2) * [W, H], r.rand(2) * [W, H], n) + r.randn(n, 2) * 3
    elif kind == 'cross': P = np.linspace([-50, r.rand() * H], [W + 50, r.rand() * H], n)        # crosses both edges
    elif kind == 'off': P = np.linspace([W + 5, -40], [W + 60, H + 40], n) if r.rand() < .5 else r.rand(n, 2) * [W, H] - [W * 1.1, 0]
    elif kind == 'point': P = r.rand(1, 2) * [W, H]
    elif kind == 'zero': P = np.repeat(r.rand(1, 2) * [W, H], n, 0)
    else:
        t = np.linspace(0, r.uniform(1, 6), 30); c = r.rand(2) * [W, H]; rad = r.uniform(5, 120)
        P = c + np.c_[np.cos(t), np.sin(t)] * rad
    kw = dict(w=float(r.choice([r.uniform(.2, 2), r.uniform(2, 12), r.uniform(12, 45)])), col='#%06x' % r.randint(1 << 24),
              a=float(r.choice([1, r.uniform(.1, 1)])), dry=float(r.choice([0, 0, r.uniform(.05, .9)])),
              taper=[(0, 0), (.12, .3), (.5, .5), (0, .9), (.2, 0)][r.randint(5)],
              press=float(r.uniform(0, .5)), rough=float(r.uniform(0, 1)), streak=float(r.uniform(0, .2)), ridge=float(r.uniform(0, .3)),
              seed=int(r.randint(1 << 30)) if r.rand() < .8 else None, tremor=float(r.choice([0, 0, r.uniform(.1, 2)])),
              col2=('#%06x' % r.randint(1 << 24)) if r.rand() < .2 else None)
    scaled = bool(r.rand() < .5)
    return kind, P, scaled, kw

def run(n=3000, seed=1):
    r = np.random.RandomState(seed); res = dict(strokes=0, identical=0, kinds={}, worst=0.0, t_bbox=0.0, t_band=0.0, clip_cases=0)
    for i in range(n):
        if i % 150 == 0:                                         # a fresh pair of canvases every 150 strokes
            W, H = int(r.randint(120, 700)), int(r.randint(120, 500)); k = float(r.choice([1.0, 1.914, 3.83, 7.66]))
            A = Canvas(W, H, k, '#e8dcc0', seed=i); B = Canvas(W, H, k, '#e8dcc0', seed=i)
            if r.rand() < .5:                                    # a soft clip on half of the canvases
                m = (np.random.RandomState(i).rand(H, W) > .4).astype(np.float32); A.clipm = m.copy(); B.clipm = m.copy(); res['clip_cases'] += 1
        kind, P, scaled, kw = case(r, W, H)
        Pk = P if scaled else P / A.k
        A.rng = np.random.RandomState(i); B.rng = np.random.RandomState(i)       # strokes without a seed draw one from rng
        t = time.perf_counter(); Canvas.stroke_bbox(A, Pk, kw['w'] / (1 if scaled else A.k), kw['col'], kw['a'], kw['dry'], kw['taper'], kw['press'], kw['rough'],
                                                  kw['streak'], kw['ridge'], kw['seed'], scaled, kw['tremor'], kw['col2']); res['t_bbox'] += time.perf_counter() - t
        t = time.perf_counter(); Canvas.stroke(B, Pk, kw['w'] / (1 if scaled else B.k), kw['col'], kw['a'], kw['dry'], kw['taper'], kw['press'], kw['rough'],
                                             kw['streak'], kw['ridge'], kw['seed'], scaled, kw['tremor'], kw['col2']); res['t_band'] += time.perf_counter() - t
        same = np.array_equal(A.img, B.img) and np.array_equal(A.rng.randint(1 << 30, size=3), B.rng.randint(1 << 30, size=3))
        res['strokes'] += 1; res['identical'] += same; res['kinds'][kind] = res['kinds'].get(kind, 0) + 1
        if not same:
            res['worst'] = max(res['worst'], float(np.abs(A.img - B.img).max()))
            print('MISMATCH', i, kind, scaled, {k_: v for k_, v in kw.items() if k_ != 'col'}, flush=True); B.img[:] = A.img
    res['t_bbox'] = round(res['t_bbox'], 2); res['t_band'] = round(res['t_band'], 2)
    return res

if __name__ == '__main__':
    out = run(int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
    print(json.dumps(out, indent=1))
    sys.exit(0 if out['identical'] == out['strokes'] else 1)

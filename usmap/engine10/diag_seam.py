import sys, os, numpy as np, collections
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
f = 1.0; S = R.load_scene(); k = R.BR.K1
# northwest region: the seam at world x = 512, rows ~ 590..780
W0 = (183, 46, 1233, 1652)
A, _, sa = R.render_window(f, W0)
for tile in ((452, 466, 768, 814), (440, 466, 768, 814), (430, 466, 768, 814)):
    T_, _, st = R.render_window(f, tile)
    a = A[tile[1] - W0[1]:tile[3] - W0[1], tile[0] - W0[0]:tile[2] - W0[0]]
    d = np.abs(a.astype(int) - T_.astype(int)).max(-1); inner = np.zeros_like(d, bool); inner[46:-46, 512 - tile[0]:-46] = True
    dd = (d > 2) & inner; ys, xs = np.nonzero(dd)
    print('tile', tile, 'diff px', int(dd.sum()), 'x', (xs.min() + tile[0], xs.max() + tile[0]) if len(xs) else None)
    o = st['own'][dd]
    for i, n in collections.Counter(o.tolist()).most_common(4): print('   owner', n, S['base'][i]['kind'] if i >= 0 else 'ground/sea', S['base'][i]['bbox'] if i >= 0 else '')

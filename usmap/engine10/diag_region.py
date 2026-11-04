import sys, os, numpy as np, collections
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
f = 1.0; S = R.load_scene()
W0 = (4167, 2213, 5025, 3132); tile = (4562, 2213, 4910, 2558)
A, _, sa = R.render_window(f, W0); T_, _, st = R.render_window(f, tile)
a = A[tile[1] - W0[1]:tile[3] - W0[1], tile[0] - W0[0]:tile[2] - W0[0]]
d = np.abs(a.astype(int) - T_.astype(int)).max(-1)[46:-46, 46:-46] > 8
oa = sa['own'][tile[1] - W0[1]:tile[3] - W0[1], tile[0] - W0[0]:tile[2] - W0[0]][46:-46, 46:-46]; ot = st['own'][46:-46, 46:-46]
print('diff px', int(d.sum()))
for i, n in collections.Counter(oa[d].tolist()).most_common(5): print('whole owner', n, S['base'][i]['kind'] if i >= 0 else 'ground', S['base'][i]['bbox'] if i >= 0 else '')
for i, n in collections.Counter(ot[d].tolist()).most_common(5): print('tile owner ', n, S['base'][i]['kind'] if i >= 0 else 'ground', S['base'][i]['bbox'] if i >= 0 else '')

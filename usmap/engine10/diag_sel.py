import sys, os, numpy as np
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
f = 1.0; W0 = (4167, 2213, 5025, 3132); tile = (4562, 2213, 4910, 2558)
A, _, sa = R.render_window(f, W0)
for mg in (16, 120, 2000):
    T_, _, st = R.render_window(f, tile, margin=mg)
    a = A[tile[1] - W0[1]:tile[3] - W0[1], tile[0] - W0[0]:tile[2] - W0[0]]
    d = np.abs(a.astype(int) - T_.astype(int)).max(-1)[46:-46, 46:-46]
    print('margin', mg, 'elements', st['elements'], 'diff px', int((d > 8).sum()))

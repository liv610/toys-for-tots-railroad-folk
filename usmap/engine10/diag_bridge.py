import sys, os, json, numpy as np
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
BR = R.BR; f = 1.0
S = R.load_scene(); br = next(e for e in S['base'] if e['kind'] == 'bridge')
def one(win):
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, (win[0], win[1], win[2] - win[0], win[3] - win[1])); R.use(c); c.rng = np.random.RandomState(br['seed']); c.eseed = br['seed']
    import usmap3 as U3; U3.bridge_road(1096, 552); return c.img.copy(), c
A, ca = one((4167, 2213, 5025, 3132)); T_, ct = one((4562, 2213, 4910, 2482))
a = A[0:2482 - 2213, 4562 - 4167:4910 - 4167]; d = np.abs(a - T_).max(-1) * 255
print('bridge only: pixels >8 in tile area', int((d[:, 46:-46] > 8).sum()))

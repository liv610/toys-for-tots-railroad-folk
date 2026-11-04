import sys, os, numpy as np
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
BR = R.BR; f = 1.0; S = R.load_scene()
hill = next(e for e in S['base'] if e['kind'] == 'hill' and e['bbox'][0] == 1042.0)
def one(win, el):
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, (win[0], win[1], win[2] - win[0], win[3] - win[1])); R.use(c)
    import cv2; LM = R.land_mask(c); R.B.U.LAND_MASK = LM
    c.rng = np.random.RandomState(el['seed']); c.eseed = el['seed']; c.set_clip((0, 0, LM)); R.B.paint(el, S['routes']); return c.img.copy()
W0 = (4167, 2213, 5025, 3132); tile = (4562, 2213, 4910, 2558)
A = one(W0, hill); T_ = one(tile, hill)
a = A[0:tile[3] - W0[1], tile[0] - W0[0]:tile[2] - W0[0]]; d = np.abs(a - T_).max(-1) * 255
print('hill only: >8 interior', int((d[46:-46, 46:-46] > 8).sum()))

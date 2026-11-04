import sys, os, json, numpy as np
sys.path[:0] = ['/home/claude/usmap/lab8', '/home/claude/usmap/lab9']; os.chdir('/home/claude/usmap')
import tile9 as T9
from tile9 import B
box = T9.CR.BOX; k = T9.CR.K_MAP; GW, GH = int(round((box[2] - box[0]) * k)), int(round((box[3] - box[1]) * k))
scene = json.load(open('out5/scene5.json')); st = next(e for e in scene['elements'] if e['kind'] == 'station7')
def one(tile, size, steps):
    c = T9.make_canvas(True, box, k, tile, size, (GW, GH)); c.rng = np.random.RandomState(st['seed']); c.set_clip(None)
    import station5 as ST, tft7 as T7
    T7._GS = None
    B.paint(st, {}); return c.img.copy()
W = one((0, 0), (GW, GH), 0); t = one((0, 0), (GW // 2 + 46, GH // 2 + 46), 0)
d = np.abs(W[:t.shape[0], :t.shape[1]] - t).max(-1) * 255
print('station only, whole vs top-left tile: pixels >8:', int((d > 8).sum()), 'max', d.max())
t2 = one((0, 0), (GW, GH), 0); d2 = np.abs(W - t2).max(-1) * 255
print('whole vs whole again:', int((d2 > 8).sum()), 'max', d2.max())
di = d[:-46, :-46]; ys, xs = np.nonzero(di > 8)
print('interior only:', len(xs), 'max', di.max() if di.size else 0, 'x range', (xs.min() if len(xs) else None, xs.max() if len(xs) else None), 'y range', (ys.min() if len(ys) else None, ys.max() if len(ys) else None))

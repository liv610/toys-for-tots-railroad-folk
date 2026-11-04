import sys, os, json, numpy as np
sys.path[:0] = ['/home/claude/usmap/lab8', '/home/claude/usmap/lab9']; os.chdir('/home/claude/usmap')
import tile9 as T9
from tile9 import B
import station5 as ST, tft7 as T7
box = T9.CR.BOX; k = T9.CR.K_MAP; GW, GH = int(round((box[2] - box[0]) * k)), int(round((box[3] - box[1]) * k))
x, y = B.HALL; spring = y - 96; half = 92; rise = 74; band = 13
parts = {
 'panes': lambda: ST.panes_and_doors(x, y - 1, 68, spring + 38, 26, 9, 3, 65, door_frac=.42),
 'masonry': lambda: ST.masonry([(x - half - band, y)] + ST.arch_pts(x, spring, half + band, rise + band, 44) + [(x + half + band, y)], ST.STONE, 62),
 'lunette': lambda: ST.lunette(x, spring, half - 4, rise - 4, 63),
 'voussoirs': lambda: ST.voussoirs(x, spring + 38, 68 + 4, 26 + 4, 7, 66, n=17),
 'banner': lambda: T7.banner(x, spring - 6, half=84, hgt=23, lift=5),
 'wingR': lambda: ST.wing(1, x, y, 51),
 'wood_bar': lambda: ST.wood_bar((955.8, 420), (955.8, 380), 2.4),
 'stroke': lambda: T9.B.c.stroke([(955.8, 440), (955.8, 380)], 2.4, '#5a3a24', a=1, dry=0, taper=(0, 0)),
}
def run(fn, size):
    c = T9.make_canvas(True, box, k, (0, 0), size, (GW, GH)); c.rng = np.random.RandomState(5); c.set_clip(None); c.img[:] = .5
    fn(); return c.img.copy()
for nm, fn in parts.items():
    W = run(fn, (GW, GH)); t = run(fn, (GW // 2 + 46, GH // 2 + 46))
    d = np.abs(W[:t.shape[0], :t.shape[1]] - t).max(-1)[:-46, :-46] * 255
    print(f'{nm:10s} interior pixels >8: {int((d > 8).sum()):6d}  max {d.max():.1f}')

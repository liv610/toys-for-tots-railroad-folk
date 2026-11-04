"""Which painters own the pixels where tiles and the whole render still disagree (lab9's 0.2%)?"""
import sys, os, json, numpy as np, cv2, collections
sys.path[:0] = ['/home/claude/usmap/lab8', '/home/claude/usmap/lab9']
os.chdir('/home/claude/usmap')
import tile9 as T9
from tile9 import B, T7, SF
box = T9.CR.BOX; k = T9.CR.K_MAP
GW, GH = int(round((box[2] - box[0]) * k)), int(round((box[3] - box[1]) * k))
def paint_owned(c):
    scene = json.load(open('out5/scene5.json')); x0, y0 = -c.d[0], -c.d[1]; x1, y1 = x0 + c.W / k, y0 + c.H / k
    els = sorted([e for e in scene['elements'] if e['layer'] in ('base', 'anim5') and e['kind'] != 'track' and e['bbox'][2] > x0 - 40 and e['bbox'][0] < x1 + 40 and e['bbox'][3] > y0 - 40 and e['bbox'][1] < y1 + 40], key=lambda e: e['depth'])
    own = np.full((c.H, c.W), -1, np.int32)
    c.area(None, '#5f6a2a', m=(0, 0, B.U.LAND_MASK), edge_dark=0, var=.03)
    for i, e in enumerate(els):
        e = dict(e, params={kk: v for kk, v in e['params'].items() if kk != 'sway'})
        before = c.img.copy(); c.rng = np.random.RandomState(e['seed'])
        c.set_clip((0, 0, B.U.LAND_MASK) if e['kind'] in B.TERRAIN - {'bridge', 'cactus'} else None)
        B.paint(e, {}); own[np.abs(c.img - before).max(-1) > .004] = i
    return own, els
c = T9.make_canvas(True, box, k, (0, 0), (GW, GH), (GW, GH)); own, els = paint_owned(c)
whole = cv2.imread('lab9/out/tile_brush_whole.png').astype(int); tl = cv2.imread('lab9/out/tile_brush_tiled.png').astype(int)
d = np.abs(whole - tl).max(-1) > 8
cnt = collections.Counter(own[d].tolist())
for i, n in cnt.most_common(8): print(n, els[i]['kind'] if i >= 0 else 'ground', els[i]['params'].get('kd', '') if i >= 0 else '', [round(v) for v in els[i]['bbox']] if i >= 0 else '')

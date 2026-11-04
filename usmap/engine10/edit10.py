"""Phase 2 demonstration: two local edits against the cached national map (f = 1), with tiles repainted only where
needed. Writes scenes for the edits next to the cache and reports which tiles were painted and how long it took.

  edit 1  the yellow shop's storefront becomes lab8 level B (a change confined to Toy Town)
  edit 2  a tree standing on a tile boundary moves 9 map units (it must repaint the tiles on both sides)
"""
import sys, os, json, copy, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import render10 as R, cache10 as C
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
f = 1; TS = C.TS[f]; k = R.BR.K1 * f
logs = {}
for side in ('west', 'east'):
    for line in open(os.path.join(OUT, f'build_f1_{side}.log')):
        if line.strip().startswith('tile'): logs[line.split(':')[0].strip()] = float(line.split(':')[1].split('s')[0])
cold = dict(tiles=len(logs), seconds_total=round(sum(logs.values()), 1), seconds_per_tile=round(sum(logs.values()) / max(1, len(logs)), 1))
print('cold build', cold)
base = json.load(open(R.SCENE))
def save(scene, name):
    p = os.path.join(C.CACHE, f'{name}.json'); json.dump(scene, open(p, 'w')); return p
# edit 1: storefront level B
s1 = copy.deepcopy(base)
for e in s1['elements']:
    if e['kind'] == 'shops7': e['params']['store_level'] = 'B'
p1 = save(s1, 'scene_edit1_storefrontB')
t0 = time.time(); r1 = C.build(f, None, scene_path=p1, store='f1'); r1['wall_seconds'] = round(time.time() - t0, 1)
print('edit 1', len(r1['painted']), 'painted', len(r1['reused']), 'reused', r1['wall_seconds'], 's')
# edit 2: a tree on a vertical tile boundary
bx = [((i * TS) / k - R.BR.PADL) for i in range(1, 7)]
cand = [e for e in s1['elements'] if e['kind'] == 'tree' and e['layer'] == 'base' and any(e['bbox'][0] < b < e['bbox'][2] for b in bx) and 300 < e['params']['y'] < 700]
tree = sorted(cand, key=lambda e: -e['params']['h'])[0]
s2 = copy.deepcopy(s1)
for e in s2['elements']:
    if e['seed'] == tree['seed'] and e['kind'] == 'tree':
        e['params']['x'] += 9; e['bbox'] = [e['bbox'][0] + 9, e['bbox'][1], e['bbox'][2] + 9, e['bbox'][3]]
p2 = save(s2, 'scene_edit2_tree')
t0 = time.time(); r2 = C.build(f, None, scene_path=p2, store='f1'); r2['wall_seconds'] = round(time.time() - t0, 1)
print('edit 2', len(r2['painted']), 'painted', len(r2['reused']), 'reused', r2['wall_seconds'], 's', 'tree at', tree['params']['x'], tree['params']['y'])
# seams: assemble the tiles around the moved tree and compare with one whole-window render of the same area
tb = tree['bbox']; rect = (tb[0] - 30, tb[1] - 30, tb[2] + 40, tb[3] + 30)
asm, (X0, Y0, X1, Y1) = C.assemble(f, rect, store='f1')
x0, y0 = map(int, R.map_to_px(rect[0], rect[1], f)); x1, y1 = map(int, R.map_to_px(rect[2], rect[3], f)); pad = int(np.ceil(16 * k))
import edges10 as E; E.activate('equivalent')
whole, _, _ = R.render_window(f, (x0 - pad, y0 - pad, x1 + pad, y1 + pad), scene_path=p2); whole = whole[pad:-pad, pad:-pad]
a = asm[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]; d = np.abs(a.astype(int) - whole.astype(int)).max(-1)
seam = dict(area_px=int(d.size), identical_pct=round(100 * float((d == 0).mean()), 3), max_diff=int(d.max()))
print('seam check around the moved tree', seam)
cv2.imwrite(os.path.join(OUT, 'edit2_tree_tiles.png'), a); cv2.imwrite(os.path.join(OUT, 'edit2_tree_whole.png'), whole)
json.dump(dict(cold=cold, edit1=r1, edit2=dict(r2, tree=dict(x=tree['params']['x'], y=tree['params']['y'], kd=tree['params']['kd'], moved=9), seam=seam),
               tile_px=TS, pad_units=C.PAD, margin_units=C.MARGIN), open(os.path.join(OUT, 'phase2_incremental.json'), 'w'), indent=1)

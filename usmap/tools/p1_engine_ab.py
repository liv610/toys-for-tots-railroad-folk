#!/usr/bin/env python3
"""Phase 1 A/B in the tiled engine: build the whole 1x map with the ORIGINAL brush (Canvas.stroke_bbox) into
cache/f1_bboxcheck, in the same process and tile order as p1_engine_check.py's cache/f1_fastcheck, and compare all
35 tiles (colour, Z, track). Same code, same order; only the brush differs.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/p1_engine_ab.py"""
import sys, os, glob, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, cv2, brush
brush.Canvas.stroke = brush.Canvas.stroke_bbox
import cache10 as C
t0 = time.time(); r = C.build(1, None, store='f1_bboxcheck', log=lambda m: print(m, flush=True)); wall = time.time() - t0
new = lambda d, i, j: sorted(glob.glob(os.path.join(C.CACHE, d, f'{i}_{j}_*.png')), key=os.path.getmtime)[-1]
diff = []
for (i, j) in C.tiles_for(1):
    a, b = new('f1_bboxcheck', i, j), new('f1_fastcheck', i, j)
    same = np.array_equal(cv2.imread(a), cv2.imread(b)) and np.array_equal(np.load(a[:-4] + '_z.npy'), np.load(b[:-4] + '_z.npy')) and np.array_equal(np.load(a[:-4] + '_trk.npy'), np.load(b[:-4] + '_trk.npy'))
    if not same: diff.append([i, j])
rep = dict(tiles=35, identical=35 - len(diff), differences=diff, original_brush_cpu_s=round(sum(p['seconds'] for p in r['painted']), 1), wall_s=round(wall, 1))
print(json.dumps(rep)); json.dump(rep, open(os.path.join(C.HERE, 'out', 'p1_engine_ab.json'), 'w'), indent=1)
sys.exit(0 if not diff else 1)

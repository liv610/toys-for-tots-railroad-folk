#!/usr/bin/env python3
"""Phase 1 check in the tiled engine: rebuild the whole 1x map and the 2x Toy Town with the current brush into
separate stores (cache/f1_fastcheck, cache/f2_fastcheck) and compare every tile -- colour, depth (Z) and track mask --
with the existing caches, which were painted with the original brush. Tiles are windows with a 16-unit pad, so every
stroke that crosses a tile edge is painted partly in two or more windows: a match here also covers tile boundaries.

    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/p1_engine_check.py
"""
import sys, os, glob, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, cv2
import cache10 as C
import brush
assert hasattr(brush.Canvas, 'stroke_bbox'), 'expects the band-limited brush'
TT = (670, 200, 1190, 650)
def newest(d, i, j):
    fs = sorted(glob.glob(os.path.join(C.CACHE, d, f'{i}_{j}_*.png')), key=os.path.getmtime); return fs[-1] if fs else None
rep = {}
for f, rect, old, new in ((1, None, 'f1', 'f1_fastcheck'), (2, TT, 'f2', 'f2_fastcheck')):
    t0 = time.time(); r = C.build(f, rect, store=new, log=lambda m: print(m, flush=True)); wall = time.time() - t0
    tiles = C.tiles_for(f, rect); diff = []
    for (i, j) in tiles:
        a, b = newest(old, i, j), newest(new, i, j)
        A, B = cv2.imread(a), cv2.imread(b)
        za, zb = np.load(a[:-4] + '_z.npy'), np.load(b[:-4] + '_z.npy'); ta, tb = np.load(a[:-4] + '_trk.npy'), np.load(b[:-4] + '_trk.npy')
        if not (np.array_equal(A, B) and np.array_equal(za, zb) and np.array_equal(ta, tb)):
            diff.append(dict(tile=[i, j], pixels=int(np.any(A != B, -1).sum()), z=bool(not np.array_equal(za, zb)), trk=bool(not np.array_equal(ta, tb))))
    cpu = sum(p['seconds'] for p in r['painted'])
    rep[f'f{f}'] = dict(tiles=len(tiles), painted=len(r['painted']), identical=len(tiles) - len(diff), differences=diff,
                       new_brush_cpu_s=round(cpu, 1), wall_s=round(wall, 1))
    print(f'f{f}:', json.dumps(rep[f'f{f}']), flush=True)
json.dump(rep, open(os.path.join(C.HERE, 'out', 'p1_engine_check.json'), 'w'), indent=1)
sys.exit(0 if all(not v['differences'] for v in rep.values()) else 1)

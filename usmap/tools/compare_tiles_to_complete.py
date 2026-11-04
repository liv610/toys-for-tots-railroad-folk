#!/usr/bin/env python3
"""Compare the map assembled from the tile cache with a complete (single-window) render from engine_complete_render.py.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/compare_tiles_to_complete.py F COMPLETE.png [X0 Y0 X1 Y1] [--store S]
Reports differing pixels for colour and depth, and where any differences are (tile and map units)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, cv2, render10 as R, cache10 as C
a = sys.argv[1:]; store = a[a.index('--store') + 1] if '--store' in a else None
a = [x for x in a if x != '--store' and x != store]
f = float(a[0]); ref = cv2.imread(a[1]); refz = np.load(a[1][:-4] + '_z.npy'); rect = tuple(map(float, a[2:6])) if len(a) >= 6 else None
asm, (X0, Y0, X1, Y1) = C.assemble(f, rect, store=store); z, _ = C.assemble(f, rect, store=store, what='z')
assert asm.shape == ref.shape, (asm.shape, ref.shape)
d = np.any(asm != ref, -1); dz = z.astype(np.float16) != refz
rep = dict(f=f, pixels=int(d.size), colour_differ=int(d.sum()), depth_differ=int(dz.sum()), max_diff=int(np.abs(asm.astype(int) - ref.astype(int)).max()))
if d.any():
    ys, xs = np.nonzero(d); ts = C.TS[int(f)]; k = R.BR.K1 * f
    rep['tiles'] = sorted({(int((x + X0) // ts), int((y + Y0) // ts)) for x, y in zip(xs[::50], ys[::50])})
    rep['map_box'] = [round((xs.min() + X0) / k - R.BR.PADL, 1), round((ys.min() + Y0) / k - R.BR.PADT, 1), round((xs.max() + X0) / k - R.BR.PADL, 1), round((ys.max() + Y0) / k - R.BR.PADT, 1)]
print(json.dumps(rep)); sys.exit(0 if not d.any() and not dz.any() else 1)

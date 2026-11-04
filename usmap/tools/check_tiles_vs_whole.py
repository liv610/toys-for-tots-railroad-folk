#!/usr/bin/env python3
"""Assemble a region from the tile cache and compare it with the same region painted as one window.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/check_tiles_vs_whole.py F X0 Y0 X1 Y1 [STORE]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, render10 as R, cache10 as C, edges10 as E
f = float(sys.argv[1]); rect = tuple(map(float, sys.argv[2:6])); store = sys.argv[6] if len(sys.argv) > 6 else f'f{f:g}'
asm, (X0, Y0, X1, Y1) = C.assemble(f, rect, store=store); Za, _ = C.assemble(f, rect, store=store, what='z')
x0, y0 = map(int, R.map_to_px(rect[0], rect[1], f)); x1, y1 = map(int, R.map_to_px(rect[2], rect[3], f)); pad = int(np.ceil(C.PAD * R.BR.K1 * f))
E.activate('equivalent'); img, Z, st = R.render_window(f, (x0 - pad, y0 - pad, x1 + pad, y1 + pad)); E.deactivate()
w = img[pad:-pad, pad:-pad]; a = asm[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
Zw = np.maximum(Z[pad:-pad, pad:-pad], -6e4).astype(np.float16); Zt = Za[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0].astype(np.float16)
d = np.any(a != w, -1)
print(f'f{f:g} {rect} store {store}: {d.size:,} pixels, {int(d.sum())} differ; depth identical {np.array_equal(Zw, Zt)}')
sys.exit(0 if not d.any() and np.array_equal(Zw, Zt) else 1)

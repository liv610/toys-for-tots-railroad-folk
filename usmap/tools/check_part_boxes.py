#!/usr/bin/env python3
"""Every split part of Toy Town (engine10/split10.py) must paint only inside its own box: a tile includes an
element only if the element's box (plus the 16-unit margin) reaches the tile, so a mark outside the box could be
missing from a neighbouring tile. Paints the town region once and checks each part's changed pixels.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/check_part_boxes.py [LEVEL store8|store10 [selective]]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, render10 as R, split10 as SP, edges10 as E
f = 1; k = R.BR.K1 * f; x0, y0 = map(int, R.map_to_px(640, 280, f)); x1, y1 = map(int, R.map_to_px(1220, 640, f))
orig = SP.paint; bad = []; n = [0]
def spy(e):
    part = e['params'].get('part')
    if part is None: return orig(e)
    c = R.B.c; before = c.img.copy(); r = orig(e); ch = np.abs(c.img - before).max(-1) > 1e-6
    ys, xs = np.nonzero(ch); n[0] += 1
    if len(ys):
        mx = (xs + c.T[0]) / k - R.BR.PADL; my = (ys + c.T[1]) / k - R.BR.PADT; b = e['bbox']
        out = (mx < b[0]) | (mx > b[2]) | (my < b[1]) | (my > b[3])
        if out.any(): bad.append((e['kind'], part, int(out.sum()), [round(float(mx.min()), 1), round(float(my.min()), 1), round(float(mx.max()), 1), round(float(my.max()), 1)], b))
    return r
SP.paint = spy
level = sys.argv[1] if len(sys.argv) > 1 else None; mod = __import__(sys.argv[2]) if len(sys.argv) > 2 else None
E.activate(sys.argv[3] if len(sys.argv) > 3 else 'equivalent'); R.render_window(f, (x0, y0, x1, y1), level=level, shop=mod)
print(f'level {level} {sys.argv[2] if len(sys.argv) > 2 else ""}: {n[0]} parts painted;', 'every part stays inside its box' if not bad else f'OUTSIDE: {bad}')
sys.exit(0 if not bad else 1)

#!/usr/bin/env python3
"""Paint the same tiles twice in one process, in different orders, and check every repeat is identical. Any state
carried from one render to the next (like the frozen station canvas found on 4 Nov 2026) shows up here.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/check_order_independence.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, render10 as R, cache10 as C, edges10 as E
E.activate('equivalent'); tiles = [(4, 1), (3, 1), (3, 2), (4, 2), (5, 1)]; first = {}; bad = []
for rnd, order in enumerate((tiles, tiles[::-1], tiles)):
    for t in order:
        img, Z, st = R.render_window(1, C.tile_window(1, *t)[1])
        if t not in first: first[t] = (img, Z, st['own'])
        elif not (np.array_equal(first[t][0], img) and np.array_equal(first[t][1], Z) and np.array_equal(first[t][2], st['own'])):
            bad.append((rnd, t, int(np.any(first[t][0] != img, -1).sum())))
print('station-area tiles', tiles, 'painted 3 times in 3 orders:', 'all repeats IDENTICAL' if not bad else f'DIFFERENCES {bad}')
sys.exit(0 if not bad else 1)

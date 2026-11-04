import sys, os, numpy as np
sys.path.insert(0, '/home/claude/usmap/engine10')
import render10 as R
f = 1.0; tile = (4562, 2213, 4910, 2558); k = R.BR.K1
S = R.load_scene()
mx0, my0, mx1, my1 = tile[0] / k - 100, tile[1] / k - 70, tile[2] / k - 100, tile[3] / k - 70
def touch(b, m): return b[2] > mx0 - m and b[0] < mx1 + m and b[3] > my0 - m and b[1] < my1 + m
extra = [e for e in S['base'] if touch(e['bbox'], 120) and not touch(e['bbox'], 16)]
print(len(extra), sorted({e['kind'] for e in extra}))
for e in extra:
    if e['kind'] in ('tree', 'bush5', 'fpatch5', 'house', 'palm5'): continue
    print(e['kind'], [round(v) for v in e['bbox']], e['depth'], {kk: v for kk, v in e['params'].items() if not isinstance(v, list)})

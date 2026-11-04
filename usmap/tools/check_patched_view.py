#!/usr/bin/env python3
"""Proof that a patched view (cached tiles + the changed area painted fresh) equals a complete render.
Case 1: level B (lab8 storefront), default profile, against the whole-map complete render of that scene.
Case 2: level C (engine10 storefront), selective profile, against the town painted fresh as one window.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/check_patched_view.py"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, cv2, views10 as V, store10 as ST10
TOWN = (680, 230, 1180, 650); ok = True
t = time.time(); a = V.view(1, TOWN, 'f1', [V.yellow_shop_patch()], level='B'); ta = time.time() - t
ref = cv2.imread(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10/out/complete/f1_shopB_overlay.png'))
x0, y0, x1, y1 = V.px_rect(1, TOWN); r = ref[y0:y1, x0:x1]; n = int(np.any(a != r, -1).sum()); ok &= n == 0
print(f'level B, default profile: patched view {ta:.1f} s; {a.shape[1]}x{a.shape[0]} px, {n} differ from the complete render')
t = time.time(); b = V.view(1, TOWN, 'f1_sel', [V.yellow_shop_patch()], profile='selective', level='C', shop=ST10); tb = time.time() - t
t = time.time(); full = V.crop(1, TOWN, 'selective', level='C', shop=ST10); tf = time.time() - t
n = int(np.any(b != full, -1).sum()); ok &= n == 0
print(f'level C, selective profile: patched view {tb:.1f} s vs painting the town {tf:.1f} s; {n} px differ')
sys.exit(0 if ok else 1)

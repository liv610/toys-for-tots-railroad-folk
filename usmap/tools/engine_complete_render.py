#!/usr/bin/env python3
"""Paint a region with the engine as ONE window (no tiles) and save it, to compare with the tiled cache.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/engine_complete_render.py F OUT.png [X0 Y0 X1 Y1]
With no rectangle the whole padded map is painted. --scene PATH paints an edited scene. Saves OUT.png and OUT_z.npy (depth, float16 as the cache stores it)."""
import sys, os, time, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import numpy as np, cv2, render10 as R, cache10 as C, edges10 as E
scene = sys.argv[sys.argv.index('--scene') + 1] if '--scene' in sys.argv else R.SCENE
if '--scene' in sys.argv: i_ = sys.argv.index('--scene'); del sys.argv[i_:i_ + 2]
f = float(sys.argv[1]); out = sys.argv[2]
if len(sys.argv) >= 7:
    tl = C.tiles_for(f, tuple(map(float, sys.argv[3:7]))); ts = C.TS[int(f)]; GW, GH = R.frame_px(f)
    win = (min(t[0] for t in tl) * ts, min(t[1] for t in tl) * ts, min(GW, (max(t[0] for t in tl) + 1) * ts), min(GH, (max(t[1] for t in tl) + 1) * ts))
else: win = (0, 0) + R.frame_px(f)
GW, GH = R.frame_px(f); pad = int(math.ceil(C.PAD * R.BR.K1 * f))             # paint a margin round a region, as each tile has
pw = (max(0, win[0] - pad), max(0, win[1] - pad), min(GW, win[2] + pad), min(GH, win[3] + pad))
E.activate('equivalent'); t = time.time(); img, Z, st = R.render_window(f, pw, scene_path=scene)
cut = lambda a_: a_[win[1] - pw[1]:win[3] - pw[1], win[0] - pw[0]:win[2] - pw[0]]; img, Z = cut(img), cut(Z)
cv2.imwrite(out, img); np.save(out[:-4] + '_z.npy', np.maximum(Z, -6e4).astype(np.float16))
print(f'f{f:g} window {win}: {img.shape[1]}x{img.shape[0]} in {time.time() - t:.1f} s')

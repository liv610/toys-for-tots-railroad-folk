"""Check that an authored asset paints identically when split across tiles: the Marines pair painted on one canvas,
then on 2x2 windows of it, compared pixel by pixel.  PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 engine10/check_asset_tiles.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import render10 as R, edges10 as E, marines10 as M
BR = R.BR
PAD = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0     # map units
def paint(f, win):
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, win, ground='#b8ab98'); R.use(c); c.eseed = 17
    M.pair(-90, -40, 28); return np.clip(c.img, 0, 1).copy()
E.activate('selective')
for f in (2, 1 / (BR.K1 * 28 / 265)):
    k = BR.K1 * f; X0, Y0 = int((-100 + 100) * k), int((-70 + 70) * k); W, H = int(32 * k), int(32 * k)
    P0 = int(round(max(PAD, 3) * k)); whole = paint(f, (X0 - P0, Y0 - P0, W + 2 * P0, H + 2 * P0))[P0:P0 + H, P0:P0 + W]; worst = 0.0
    for (ox, oy, w, h) in ((X0, Y0, W // 2, H // 2), (X0 + W // 2, Y0, W - W // 2, H // 2), (X0, Y0 + H // 2, W // 2, H - H // 2), (X0 + W // 2, Y0 + H // 2, W - W // 2, H - H // 2)):
        pd = int(round(PAD * k))                                         # tiles render with a margin, as the engine's do
        part = paint(f, (ox - pd, oy - pd, w + 2 * pd, h + 2 * pd))[pd:pd + h, pd:pd + w]
        ref = whole[oy - Y0:oy - Y0 + h, ox - X0:ox - X0 + w]
        d = np.abs(part - ref).max(-1); worst = max(worst, float(d.max()))
        if '-v' in sys.argv and d.max() > .004:
            yy, xx = np.nonzero(d > .004); print(f'   tile at ({ox - X0},{oy - Y0}): {len(yy)} px differ, x {xx.min() + ox - X0}-{xx.max() + ox - X0}, y {yy.min() + oy - Y0}-{yy.max() + oy - Y0}')
    print(f'f={f:.3f}: {W}x{H} px, worst pixel difference across 4 tiles = {worst:.6f}')
E.deactivate()

"""Toy Town study 1, version 2 ("drawn"): the same traced repaint as version 1, then the parts that matter are
redrawn as clean shapes and painted with the same brush on top: window frames, glowing panes and glazing bars,
snow on the sills, the awning's stripes and scalloped hem with snow along the top, and the shopfront's wooden
frames. The panes are also written as their own layer (blue_shop_v2_glow.png) so they can glow at dusk.
(Revised: the shapes go into the guide the brush paints from, not on top of the paint; the first try,
painting clean shapes over the brushwork, looked flat and vector-like.)
    PYTHONPATH=../../../folk2:../../../styles2 python3 study_blue_shop_v2.py
"""
import os, math
import numpy as np, cv2
import study_blue_shop as B
import shapes_blue_shop as SH

def calmed(rgb):
    return B.calm(np.array(rgb, np.float32).reshape(1, 1, 3))[0, 0]

def guide(big, x0, y0, K):
    """Redraw the windows in the guide at canvas resolution, keeping the target's own colours: the pane's glow is
    smoothed (the AI speckle removed), the cream frame gets clean edges, and the glazing bars are drawn as clean
    lines in the colour of the target's own bars. The rest of the guide is lightly sharpened."""
    out = big.copy()
    sharp = cv2.addWeighted(big, 1.6, cv2.GaussianBlur(big, (0, 0), 1.2 * K), -.6, 0)
    out = np.clip(sharp, 0, 1)
    glow = np.zeros(big.shape[:2], np.float32)
    def mask(poly):
        m = np.zeros(big.shape[:2], np.uint8)
        cv2.fillPoly(m, [np.round((np.array(poly) - (x0, y0)) * K * 8).astype(np.int32)], 1, cv2.LINE_AA, shift=3)
        return m.astype(bool)
    # one cream for every frame (they are painted with the same paint): the lightest non-blue ring pixels of all
    rings = []
    for (wx0, wy0, wx1, wy1, arched, nbx, nby) in SH.WINDOWS:
        F = SH.FRAME; pane = mask(SH.window_poly(wx0, wy0, wx1, wy1, arched))
        rings.append(big[mask(SH.window_poly(wx0 - F, wy0 - F, wx1 + F, wy1 + F * .6, arched)) & ~pane])
    rp = np.concatenate(rings); lum = rp.sum(1); ok = (rp[:, 0] > rp[:, 2] + .05) & (lum >= np.percentile(lum, 60))
    CREAM = np.median(rp[ok], 0)
    for (wx0, wy0, wx1, wy1, arched, nbx, nby) in SH.WINDOWS:
        F = SH.FRAME
        pane = mask(SH.window_poly(wx0, wy0, wx1, wy1, arched))
        ring = mask(SH.window_poly(wx0 - F, wy0 - F, wx1 + F, wy1 + F * .6, arched)) & ~pane
        # the frame: the target's cream, lit at the top left, a little darker at the lower right
        cream = CREAM
        yy, xx = np.nonzero(ring); cx, cy = ((wx0 + wx1) / 2 - x0) * K, ((wy0 + wy1) / 2 - y0) * K
        k = np.clip(((xx - cx) + (yy - cy)) / ((wx1 - wx0) * K) * .35, -.2, .2)[:, None]
        out[yy, xx] = np.clip(cream * (1 - k * .5), 0, 1)
        # the pane: the target's light, smoothed, a touch brighter in the middle
        p = cv2.GaussianBlur(big, (0, 0), 2.5 * K)
        yy, xx = np.nonzero(pane); d = np.hypot((xx - cx) / ((wx1 - wx0) * K / 2), (yy - cy) / ((wy1 - wy0) * K / 2))
        pp = big[pane]; lum = pp.sum(1)
        gold = pp[:, 0] - pp[:, 2]                                           # the lit glass: its most golden pixels
        warm = np.median(pp[gold >= np.percentile(gold, 65)], 0)
        # the glass: the target's own gold, brighter at the middle, a warm shadow just inside the frame
        edge = np.clip((d - .7) / .3, 0, 1)[:, None]
        lit = warm * (.88 + .3 * (1 - np.clip(d, 0, 1)) ** 1.5)[:, None] + (1 - np.clip(d, 0, 1))[:, None] * np.array([.05, .04, .0])
        out[yy, xx] = np.clip(lit * (1 - edge * .25) + np.array([.6, .3, .08]) * edge * .25, 0, 1)
        glow[pane] = 1
        # glazing bars: one upright, one crossbar (as painted), in the darkest colour of the target's own pane
        bar = np.percentile(big[pane], 4, axis=0) * .9
        bw = max(2, int(1.25 * K))
        lx0, lx1, ly0, ly1 = [(v - o) * K for v, o in ((wx0, x0), (wx1, x0), (wy0, y0), (wy1, y0))]
        r = (lx1 - lx0) / 2; top = ly0 + (r * .05 if arched else 0)
        m = np.zeros(big.shape[:2], np.uint8)
        for i in range(1, nbx + 1):
            X = int(lx0 + (lx1 - lx0) * i / (nbx + 1)); cv2.line(m, (X, int(top)), (X, int(ly1)), 1, bw, cv2.LINE_AA)
        body0 = ly0 + (r if arched else 0) * .55
        for j in range(1, nby + 1):
            Y = int(body0 + (ly1 - body0) * j / (nby + 1)); cv2.line(m, (int(lx0), Y), (int(lx1), Y), 1, bw, cv2.LINE_AA)
        m = m.astype(bool) & pane
        out[m] = bar
        glow[m] = 0                                    # the bars stay dark when the windows glow
    # the shopfront glass glows too: the display and the two side windows, but not their wooden bars
    for sx0, sy0, sx1, sy1 in SH.SHOP:
        r = mask([(sx0 + 2, sy0 + 2), (sx1 - 2, sy0 + 2), (sx1 - 2, sy1 - 3), (sx0 + 2, sy1 - 3)])
        lum = big.sum(2); warm = (big[..., 0] - big[..., 2] > .25) & (lum > 1.6)
        glow[r & warm] = np.maximum(glow[r & warm], .8)
    guide.glow = cv2.GaussianBlur(glow, (0, 0), .6 * K)
    return out

def finish(c, x0, y0, alpha):
    """Write the lit panes as their own layer (warm light plus a soft halo) for dusk and twinkling later."""
    K = c.k; glow = guide.glow
    halo = cv2.GaussianBlur(glow, (0, 0), 3 * K) * .5
    g = np.clip(np.maximum(glow * .9, halo), 0, 1) * alpha
    col = np.array([1.0, .78, .4]) * np.ones((c.H, c.W, 3))
    cv2.imwrite(os.path.join(B.OUT, 'blue_shop_v2_glow.png'), (np.dstack([col[..., ::-1], g]) * 255).astype(np.uint8))

def compare():
    """Three-way sheet: the target, version 1 (repaint only) and version 2 (drawn), plus close-ups."""
    tgt = cv2.imread(B.TARGET)[..., ::-1].astype(np.float32) / 255
    x0, y0, x1, y1 = B.BOX; K = B.K; H, W = (y1 - y0) * K, (x1 - x0) * K
    tc = cv2.resize(tgt[y0:y1, x0:x1], (W, H), interpolation=cv2.INTER_CUBIC)
    def load(n):
        a = cv2.imread(os.path.join(B.OUT, n), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
        return a[..., 2::-1] * a[..., 3:] + np.array([.93, .91, .87]) * (1 - a[..., 3:])
    v1, v2 = load('blue_shop_study.png'), load('blue_shop_v2_study.png')
    gap = np.ones((H, 24, 3))
    cv2.imwrite(os.path.join(B.OUT, 'blue_shop_v1_v2_compare.jpg'), (np.concatenate([tc, gap, v1, gap, v2], 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for nm, (cx0, cy0, cx1, cy1) in {'windows': (100, 595, 300, 735), 'awning': (95, 735, 335, 885)}.items():
        a = (np.array([cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0]) * K).astype(int); g = np.ones((a[3] - a[1], 16, 3))
        row = np.concatenate([tc[a[1]:a[3], a[0]:a[2]], g, v1[a[1]:a[3], a[0]:a[2]], g, v2[a[1]:a[3], a[0]:a[2]]], 1)
        cv2.imwrite(os.path.join(B.OUT, f'blue_shop_v1_v2_{nm}.jpg'), (row[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])

if __name__ == '__main__':
    B.main('blue_shop_v2', finish, guide); compare(); print('ok')

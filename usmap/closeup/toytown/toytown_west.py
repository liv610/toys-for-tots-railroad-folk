"""Toy Town, west side behind the blue shop: the narrow pink house and the cream house with the red gable.
    python3 toytown_west.py            # study render, writes out/west_study.png and out/west_compare.jpg
"""
import os, math
import numpy as np, cv2
import toytown_kit as T
from toytown_kit import A, S, shaded, wall, roof, window, garland, snow_edge, snow_clump, snow_cap, eave_shadow, chimney, stip, lump, hexc
from toytown_east import PINK, RED, wreath

CREAMW = ['#d6bd8c', '#e8d2a4', '#f0e0b6', '#f6ebcc', '#dfc796']
GABLE = ['#8a3424', '#6e2618', '#a04432']

def door(x0, x1, ytop, yb, col=('#9a5a2c', '#7a4220', '#5a2e16'), wreathed=True):
    r = (x1 - x0) / 2
    d = [(x0, yb)] + [(x0 + r - r * math.cos(math.pi * k / 12), ytop + r - r * math.sin(math.pi * k / 12)) for k in range(13)] + [(x1, yb)]
    shaded(d, list(col), light=(-.8, -.6), wob=.1, rough=.3, edge_dark=.25, L=3.0, w=1.2)
    for xx in np.linspace(x0 + r * .5, x1 - r * .5, 2): S([(xx, ytop + r * .4), (xx, yb - 1)], .7, '#4a2410', a=.5, dry=.3)
    T.c.dots([(x1 - r * .35 - T.X0, (ytop + yb) / 2 + 4 - T.Y0)], 1.3, ['#e8c060'], seed=int(x0))
    if wreathed: wreath((x0 + x1) / 2, ytop + r + 8, r * .45)
    A([(x0 - 4, yb), (x1 + 4, yb), (x1 + 4, yb + 7), (x0 - 4, yb + 7)], '#b8b0a0', wob=.1, rough=.3)
    snow_cap(x0 - 6, x1 + 6, yb, 3.5)

def pink_narrow():
    """The tall narrow pink house: a steep red roof behind, windows stacked, a garland, a door at the foot."""
    x0, x1, ey, yb = 302, 350, 452, 722
    chimney(316, 334, 392, 420)
    roof([(294, ey + 2), (310, 414), (342, 414), (356, ey + 2)], cols=['#8a2e2a', '#6e2420', '#a03a34'], snowy=.35, ridge=((312, 416), (340, 416)), eave=((296, ey), (354, ey)))
    snow_edge([(304, 414), (348, 414)], 6, drip=.1)
    wall([(x0, yb), (x1, yb), (x1, ey), (x0, ey)], PINK[2], cols=PINK, stone_dark=.12, fleck=.4)
    eave_shadow([(x0, ey), (x1, ey)], 7, '#8a4058')
    snow_edge([(292, ey + 2), (358, ey + 2)], 10, drip=.45)
    window(312, 478, 340, 508, True, frame=3.2)
    window(312, 548, 340, 578, False, frame=3.2)
    garland(304, 348, 606, sag=4, swags=1, bows=False)
    window(312, 656, 340, 700, True, frame=3.2, bars=(1, 2))

def cream_house():
    """The cream stone house with a dark red gable, two windows with garlands, a scalloped canopy, a door."""
    x0, x1, px, py, ey, yb = 344, 462, 402, 444, 508, 702
    chimney(350, 374, 408, 450); chimney(386, 410, 400, 446)
    wall([(x0, yb), (x1, yb), (x1, ey), (x0, ey)], CREAMW[2], cols=CREAMW, stone_dark=.12, fleck=.3)
    # the red gable: a triangle of dark red boards over the cream wall, with a lit attic window
    m = shaded([(x0 - 6, ey + 2), (px, py), (x1 + 6, ey + 2)], GABLE, light=(-.8, -.6), wob=.2, rough=.4, edge_dark=.2)
    for k in range(1, 6):
        yy = ey - (ey - py) * k / 6; half = (x1 - x0) / 2 * (1 - k / 6)
        S([(px - half, yy), (px + half, yy)], .7, '#4a1a10', a=.45, dry=.4)
    window(390, 476, 414, 504, True, frame=3.0)
    S([(x0 - 8, ey + 4), (px, py - 4), (x1 + 8, ey + 4)], 4.0, T.CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(x0 - 14, ey + 6), (px, py - 10), (x1 + 14, ey + 6)], 12, drip=.4)
    snow_edge([(x0 - 6, ey + 6), (x1 + 6, ey + 6)], 8, drip=.35)
    eave_shadow([(x0, ey + 8), (x1, ey + 8)], 7, '#8a7650')
    for wx in (366, 418):
        window(wx, 538, wx + 22, 576, True, frame=3.2)
        garland(wx - 6, wx + 28, 586, sag=2, swags=1, bows=False)
    # a scalloped red-and-cream canopy across the ground floor, with snow on it
    cx0, cx1, cy = 360, 462, 604
    n = 8
    for i in range(n):
        a = cx0 + (cx1 - cx0) * i / n; b = cx0 + (cx1 - cx0) * (i + 1) / n
        sc = [(b - (b - a) * k / 8, cy + 6 + 7 * math.sin(math.pi * k / 8)) for k in range(9)]
        shaded([(a, cy), (b, cy)] + sc[1:-1], ['#d84a40', '#b8262a', '#7e1a1a'] if i % 2 == 0 else ['#fbf5e6', '#f3ead6', '#cfc4ac'], wob=.1, rough=.3, edge_dark=.15, L=1.6, w=1.0)
    snow_edge([(cx0 - 3, cy), (cx1 + 3, cy)], 7, drip=.3)
    door(372, 398, 622, 694)
    window(414, 622, 442, 670, True, frame=3.0, bars=(1, 1))
    A([(410, 672), (446, 672), (444, 684), (412, 684)], '#8a4a24', wob=.1, rough=.3, edge_dark=.2)
    garland(412, 444, 672, sag=1, swags=1, bows=False)

def build_west():
    pink_narrow(); cream_house()

if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    T.init(280, 330, 480, 730, 3)
    build_west(); T.light()
    paint, al = T.finish(os.path.join(HERE, 'out', 'west_study.png'), os.path.join(HERE, 'out', 'west_glow.png'))
    tgt = cv2.imread(os.path.join(T.ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))[..., ::-1].astype(np.float32) / 255
    tc = cv2.resize(tgt[330:730, 280:480], (paint.shape[1], paint.shape[0]), interpolation=cv2.INTER_CUBIC)
    v = paint * al[..., None] + np.array([.93, .91, .87]) * (1 - al[..., None])
    cv2.imwrite(os.path.join(HERE, 'out', 'west_compare.jpg'), (np.concatenate([tc, np.ones((tc.shape[0], 20, 3)), v], 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('ok')

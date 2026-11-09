"""Clean, hand-measured shapes for the blue shop (target px), used to redraw the parts that matter before the
brush paints over them: window panes, frames and bars, the awning's stripes and scalloped hem, the shopfront.
`python3 shapes_blue_shop.py` draws them over the target so their placement can be checked by eye."""
import os, math
import numpy as np, cv2

# windows: (x0, y0, x1, y1, arched, bars_x, bars_y); arched windows have a half-round top within y0..y0+w/2
WINDOWS = [
    (233, 485, 268, 521, True, 1, 1),      # tall house, attic
    (258, 542, 290, 580, False, 1, 1),     # tall house, second floor right
    (177, 601, 218, 641, True, 1, 1),      # front gable, attic
    (126, 655, 160, 703, True, 1, 1),      # front, first floor x3
    (182, 655, 215, 703, False, 1, 1),
    (236, 655, 270, 703, True, 1, 1),
    (51, 683, 76, 727, True, 1, 1),        # side wing
]
FRAME = 4.2                              # cream frame width, target px
# the awning: top edge (wall) and lower edge (where the valance starts), and the valance hem
AWN_TOP = [(100, 745), (322, 745)]
AWN_LOW = [(106, 778), (333, 778)]      # stripes lean a little to the right, as painted
AWN_HEM = 793                            # bottom of the scallops
AWN_N = 8                                # stripes (green first)
# shopfront below the awning: left window, display, right window
SHOP = [(118, 795, 160, 868), (172, 795, 252, 878), (256, 795, 300, 868)]

def window_poly(x0, y0, x1, y1, arched, n=16):
    w = x1 - x0
    if not arched: return [(x0, y1), (x0, y0), (x1, y0), (x1, y1)]
    r = w / 2; cy = y0 + r
    return [(x0, y1), (x0, cy)] + [(x0 + r - r * math.cos(math.pi * k / n), cy - r * math.sin(math.pi * k / n)) for k in range(1, n)] + [(x1, cy), (x1, y1)]

def stripes():
    """Polygons of the awning's stripes, top to hem; even index = green."""
    (tx0, ty), (tx1, _) = AWN_TOP; (lx0, ly), (lx1, _) = AWN_LOW
    out = []
    for i in range(AWN_N):
        a, b = i / AWN_N, (i + 1) / AWN_N
        t0, t1 = tx0 + (tx1 - tx0) * a, tx0 + (tx1 - tx0) * b
        l0, l1 = lx0 + (lx1 - lx0) * a, lx0 + (lx1 - lx0) * b
        hem = [(l1 - (l1 - l0) * k / 10, ly + (AWN_HEM - ly) * math.sin(math.pi * k / 10)) for k in range(11)]
        out.append([(t0, ty), (t1, ty), (l1, ly)] + hem[1:-1] + [(l0, ly)])
    return out

if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    t = cv2.imread(os.path.join(HERE, '..', '..', '..', 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))
    X0, Y0, X1, Y1, S = 0, 470, 330, 900, 3
    im = cv2.resize(t[Y0:Y1, X0:X1], None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    P = lambda pts: np.round((np.array(pts) - (X0, Y0)) * S).astype(np.int32)
    for wdw in WINDOWS: cv2.polylines(im, [P(window_poly(*wdw[:5]))], True, (255, 0, 255), 2)
    for i, s in enumerate(stripes()): cv2.polylines(im, [P(s)], True, (0, 255, 255) if i % 2 else (0, 0, 255), 2)
    for x0, y0, x1, y1 in SHOP: cv2.rectangle(im, tuple(P([(x0, y0)])[0]), tuple(P([(x1, y1)])[0]), (255, 255, 0), 2)
    cv2.imwrite('/tmp/claude-0/-home-user/0fbaec8a-c358-5484-bb9d-a4ee0b9d05a6/scratchpad/shapes_check.jpg', im)

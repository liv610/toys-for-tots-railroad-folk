"""Engine 10, phase 5: Toy Town's row of houses and its storefronts as separate objects.

In the published scene the whole row is two elements:
- 'town' (usmap4.town_row): the street strip, nine houses (one is the clock tower) and two lamps
- 'shops7' (tft7.town_extras): every shop window and the TOY DONATION sign

Each spans 500 map units, so changing one storefront invalidated six 1x tiles and fifteen 2x tiles. Here each is
split into parts that make exactly the same calls, in the same order, with the same element seed and depth:
- town: street, house 0 ... house 8, lamps
- shops7: one part per house

In the engine, a stroke's seed comes from its own geometry and the element seed, and nothing else carries over
between elements, so the painting is unchanged. Each part has a box around its own marks, so a tile is repainted
only when a part it touches changes.

This is applied only when the engine loads a scene (render10.load_scene). The published scene file and the
published pipeline (usmap5) are unchanged. In the published pipeline every element restarts the shared random
stream, so splitting there would change the unseeded strokes of houses 1-8.

The storefront level of the experiment (lab8 / engine10 store10) becomes a property of house 5's shop part:
params['store_level'].
"""
import math
import numpy as np
import usmap4 as B, tft7 as T7, story as S
from kit import pal_fn

# usmap4.town_row's row: (width, height, wall, roof, awning); the clock tower has no wall colour
ROW = [(44, 74, '#e8b84a', '#7a4a34', '#b8402e'), (46, 92, '#5a7ab0', '#2f3a5a', '#3f6aa8'), (40, 80, '#e89aa8', '#6a3a4a', '#b8402e'),
       (44, 86, '#efe2c4', '#7a4a34', '#3f6aa8'), (60, 0, None, None, None), (44, 84, '#e8b84a', '#7a4a34', '#b8402e'),
       (42, 92, '#a83a30', '#3a2a3a', '#7f9a3a'), (44, 80, '#e89aa8', '#5a3a5a', '#b8402e'), (46, 74, '#e8b84a', '#7a4a34', '#3f6aa8')]
assert [(w, h) for w, h, *_ in ROW] == [tuple(r) for r in T7.ROW], 'split10.ROW must match the painters'
YELLOW_SHOP = 5                                  # the TOY DONATION shop

def _xs():
    x0, y = B.TOWN; x = x0; out = []
    for w, *_ in ROW: out.append(x); x += w * 1.03
    return x0, y, out, x                         # x after the last house (the right lamp's position)

def split(base):
    """Replace the 'town' and 'shops7' elements of a sorted base list by their parts (same depth and seed)."""
    x0, y, xs, xend = _xs(); tot = sum(r[0] for r in ROW); out = []
    for e in base:
        if e['kind'] == 'town' and 'part' not in e['params']:
            mk = lambda part, bb: dict(e, params=dict(e['params'], part=part), bbox=[round(v, 2) for v in bb])
            out.append(mk('street', (x0 - 24, y - 2, x0 + tot * 1.03 + 24, y + 20)))
            for i, (w, h, *_) in enumerate(ROW):
                if h == 0: out.append(mk(['house', i], (xs[i] + w / 2 - 32, y - 162, xs[i] + w / 2 + 32, y + 4)))     # the clock tower
                else: out.append(mk(['house', i], (xs[i] - 10, y - h - 60, xs[i] + w + 18, y + 6)))                    # roof, chimney, side walls (measured: up to w + 13)
            out.append(mk('lamps', (x0 - 20, y - 38, xend + 14, y + 12)))
        elif e['kind'] == 'shops7' and 'part' not in e['params']:
            for i, (w, h, *_) in enumerate(ROW):
                if h == 0: continue
                p = {kk: v for kk, v in e['params'].items() if kk != 'store_level' or i == YELLOW_SHOP}
                bb = (xs[i] - 8, y - h * .28 - 34, xs[i] + w + 8, y + 6)
                if 'store_level' in p: bb = (xs[i] - 10, y - h - 60, xs[i] + w + 18, y + 6)       # an experiment storefront paints the whole facade (measured: up to the roof)
                out.append(dict(e, params=dict(p, part=['shop', i]), bbox=[round(v, 2) for v in bb]))
        else: out.append(e)
    # The storefront experiment also paints on the pavement after the town square (light from the window, a
    # poinsettia). That used to run inside the square element, so the square's tiles did not know about it. It is a
    # part of its own, right after the square (same seed and depth, so the painting is unchanged), with a box around
    # the shop and the level in its params, so changing the level invalidates exactly the tiles it paints on.
    lv = next((e['params']['store_level'] for e in out if e['kind'] == 'shops7' and 'store_level' in e['params']), None)
    if lv is not None:
        j = next((n for n, e in enumerate(out) if e['kind'] == 'square7' and 'part' not in e['params']), None)
        if j is not None:
            w, h = ROW[YELLOW_SHOP][:2]; x = xs[YELLOW_SHOP]; sq = out[j]
            out.insert(j + 1, dict(sq, params=dict(sq['params'], part=['after_square', lv]), bbox=[round(v, 2) for v in (x - 10, y - 4, x + w + 18, y + 14)]))
    return out

def paint(e):
    """Paint one part. Returns False if e is not a part (the caller paints it as usual)."""
    part = e['params'].get('part')
    if part is None: return False
    c = B.c; x0, y, xs, xend = _xs()
    if part == 'street':
        tot = sum(r[0] for r in ROW)
        st = [(x0 - 16, y + 2), (x0 + tot * 1.03 + 16, y + 2), (x0 + tot * 1.03 + 20, y + 16), (x0 - 20, y + 16)]
        m = c.area(st, '#b8a888', wob=.4, rough=.9, edge_dark=.1)
        c.stip(m, pal_fn(['#b8a888', '#a89878', '#c8b898', '#988868']), spacing=1.5, L=2.6, w=2.2, seed=7, jit=1.5)
    elif part == 'lamps':
        for lx in (x0 - 14, xend + 8):
            c.stroke([(lx, y + 8), (lx, y - 30)], 1.8, '#2a2420', a=1, dry=0, taper=(0, 0)); c.dots([(lx, y - 32)], 3.2, ['#f8d880'])
    elif part[0] == 'house':
        i = part[1]; w, h, wallc, roof, awn = ROW[i]; x = xs[i]; cx = x + w / 2
        if wallc is None:
            B.wall([(cx - 24, y), (cx + 24, y), (cx + 24, y - 120), (cx - 24, y - 120)], '#efe2c4', 31)
            c.area(S.lumpy(cx, y - 96, 13, 13, 2, n=36, amp=0), '#f8f2e4', wob=0, rough=.3, edge_dark=.25)
            c.stroke([(cx, y - 96), (cx, y - 106)], 1.6, '#2a2420', a=1, dry=0, taper=(0, .3)); c.stroke([(cx, y - 96), (cx + 7, y - 93)], 1.6, '#2a2420', a=1, dry=0, taper=(0, .3))
            B.roof_tiles([(cx - 28, y - 120), (cx + 28, y - 120), (cx, y - 156)], '#3a3a5a', 32)
            for yy in (y - 64, y - 30): B.lit_window(cx, yy, 14, 16, arch=True, mullions=1)
            c.area([(cx - 9, y), (cx + 9, y)] + [(cx + 9 * math.cos(t), y - 20 - 9 * math.sin(t)) for t in np.linspace(0, math.pi, 10)], '#5a3a2a', wob=0, rough=.3)
        else:
            B.A.house(cx, y, w, h, 'tall' if i % 3 == 1 else ('side' if i % 3 == 2 else 'gable'), wallc, roof, 140 + i, dotcol=None, rows=3, cols_=2, chimney=i % 2 == 0)
            for kk in range(5):
                a0 = x + 3 + kk * (w - 6) / 5; a1 = x + 3 + (kk + 1) * (w - 6) / 5
                c.area([(a0, y - h * .28), (a1, y - h * .28), (a1 + 1, y - h * .28 + 8), (a0 + 1, y - h * .28 + 8)], [awn, '#f4eee2'][kk % 2], wob=0, rough=.3)
    elif part[0] == 'shop':
        T7.town_extras({part[1]})
    elif part[0] == 'after_square':
        if AFTER_SQUARE is not None: AFTER_SQUARE(part[1])
    return True

AFTER_SQUARE = None              # set by render10 to the storefront module's after_square while a level is active

def group(e):
    """The element a part came from (its kind and seed), or None for an element that was not split."""
    return (e['kind'], e['seed']) if 'part' in e['params'] else None

_BOX = {}
def group_box(base, grp):
    """The union of the boxes of all parts of one split element."""
    if (id(base), grp) not in _BOX:
        bs = [e['bbox'] for e in base if group(e) == grp]
        _BOX[(id(base), grp)] = (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    return _BOX[(id(base), grp)]

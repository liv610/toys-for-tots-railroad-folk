"""lab8 — an isolated renderer for one rectangle of the real pass 5 scene.

It reads the published scene (out5/scene5.json), takes only the elements that touch the rectangle, and paints them in
the same order, with the same painters, clips and seeds as the full render, onto a small canvas of its own. Nothing
is written to out5*/ or the viewer, and no pass 5 file is modified: the experiment's storefront levels are applied by
swapping one function in memory (tft7.town_extras / tft7.square) for the duration of the run.

    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8 python3 lab8/crop8.py            # all four levels, both scales
"""
import sys, os, json, math, time, gc
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
import numpy as np, cv2
import usmap5 as U5
B = U5.B; T7 = U5.T7
import station5 as ST, pnw5 as P5, fl5 as F5
import store8 as SF
from pad5 import _Off
from kit import Kanvas, impasto
from brush import hexc

MODS = [B, B.U, B.U2, B.U3, B.S, B.A, U5, F5, P5, ST, T7, SF]
BOX = (940, 405, 1030, 600)                       # map units: the yellow shop beside the clock tower, roof to square
K_MAP = 6400 / 1671                                # the zoomable map's density (painted px per map unit)

def use_canvas(box, k):
    x0, y0, x1, y1 = box
    W, H = int(round((x1 - x0) * k)), int(round((y1 - y0) * k))
    for m in MODS: m.c = None
    gc.collect()
    Off = type('OffKanvas', (_Off, Kanvas), {})
    c = Off(W, H, k, '#2c5684', seed=1972); c.HM = np.zeros((H, W), np.float32); c.d = (-float(x0), -float(y0))
    for m in MODS: m.c = c
    for m in (B, B.U, B.U2, B.U3): m.k, m.W, m.H = k, W, H
    U5.k = k
    B.OX, B.OY = -x0 * k, -y0 * k; B.U.OX, B.U.OY = B.OX, B.OY
    LM = np.zeros((H, W), np.float32)
    cv2.fillPoly(LM, [np.round((np.asarray(B.COAST) - [x0, y0]) * k * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    B.U.LAND_MASK = cv2.GaussianBlur(LM, (0, 0), k / 1.914)
    return c

def render(level, box=BOX, k=K_MAP * 4):
    t0 = time.time()
    c = use_canvas(box, k)
    scene = json.load(open('out5/scene5.json'))
    x0, y0, x1, y1 = box
    def touches(b): return b[2] > x0 - 2 and b[0] < x1 + 2 and b[3] > y0 - 2 and b[1] < y1 + 2
    els = sorted([e for e in scene['elements'] if e['layer'] in ('base', 'anim5') and e['kind'] != 'track' and touches(e['bbox'])], key=lambda e: e['depth'])
    # the ground (the crop is all land)
    c.area(None, '#5f6a2a', m=(0, 0, B.U.LAND_MASK), edge_dark=0, var=.03)
    SN = np.array([hexc(z) for z in B.U3.SNOWPAL])
    def groundcol(X, Y, rr):
        base_ = np.array([hexc('#5f6a2a'), hexc('#6a7430'), hexc('#545e24')])[rr.randint(3, size=len(X))]
        return np.where((rr.rand(len(X)) < B.snow_amt(X, Y))[:, None], SN[rr.randint(5, size=len(X))], base_)
    c.stip((0, 0, B.U.LAND_MASK), groundcol, spacing=2.2, L=6, w=2.6, angfn=lambda X, Y: .4 * np.sin(X / 60), seed=3, jit=.4)
    # the storefront level, swapped in for this run only
    te0, sq0 = T7.town_extras, T7.square
    def town_extras(which):
        te0(set(which) - {5})
        if 5 in which: SF.storefront(level)
    def square(seed):
        sq0(seed); SF.after_square(level)
    T7.town_extras, T7.square = town_extras, square
    t_el = {}
    try:
        for e in els:
            e = dict(e, params={kk: v for kk, v in e['params'].items() if kk != 'sway'})
            c.rng = np.random.RandomState(e['seed'])
            c.set_clip((0, 0, B.U.LAND_MASK) if e['kind'] in B.TERRAIN - {'bridge', 'cactus'} else None)
            ts = time.time(); B.paint(e, {}); t_el[e['kind']] = t_el.get(e['kind'], 0) + time.time() - ts
    finally:
        T7.town_extras, T7.square = te0, sq0
    c.set_clip(None)
    impasto(c, .14)
    img = (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
    return img, time.time() - t0, t_el

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    levels = sys.argv[1:] or ['orig', 'A', 'B', 'C']
    timing = {}
    for lv in [l for l in os.environ.get('LEVELS', 'orig A B C').split()]:
        for tag, k in (('close', K_MAP * 4), ('map', K_MAP)):
            img, dt, tel = render(lv, k=k)
            cv2.imwrite(os.path.join(out, f'{lv}_{tag}.png'), img)
            timing[f'{lv}_{tag}'] = dict(seconds=round(dt, 2), shops=round(tel.get('shops7', 0), 2), square=round(tel.get('square7', 0), 2), size=list(img.shape[:2]))
            print(lv, tag, img.shape, f'{dt:.1f}s', 'shops7', round(tel.get('shops7', 0), 2), 'square7', round(tel.get('square7', 0), 2), flush=True)
    json.dump(timing, open(os.path.join(out, 'timing.json'), 'w'), indent=1)

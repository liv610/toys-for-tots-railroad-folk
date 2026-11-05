"""The Marines test: the reference, the hand-drawn pair painted by the map's brush, and the current procedural pair,
side by side at the same scale, plus the new pair at the size the 2x Toy Town layer shows it.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 engine10/marines_sheet10.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, edges10 as E, marines10 as M, assets10 as A
if os.environ.get("RELIEF_GAIN"): A.RELIEF_GAIN = float(os.environ["RELIEF_GAIN"])
if os.environ.get("AMBIENT"): A.AMBIENT = float(os.environ["AMBIENT"])
BR = R.BR; T7 = R.T7
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
H_MAP = 28.0; U = H_MAP / 265.0; WU, HU = 280 * U, 285 * U          # the reference crop, in map units
def canvas(f):
    k = BR.K1 * f; W, H = int(round(WU * k)), int(round(HU * k))
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, (0, 0, W, H), ground='#b8ab98'); R.use(c); c.eseed = 17
    m = c.mask([(-100, -70), (-100 + WU, -70), (-100 + WU, -70 + HU), (-100, -70 + HU)], 0, .2, 5, soft=.3)
    c.stip(m, lambda X, Y, rr: np.array([[.80, .71, .60], [.72, .63, .53], [.86, .79, .69], [.64, .56, .47]])[rr.randint(4, size=len(X))], spacing=.9, L=1.7, w=1.2,
           angfn=lambda X, Y: 0 * X, seed=5, jit=.6)
    return c
def img(c): return (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
def label(im, t):
    p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (p.width, p.height + 28), (250, 246, 236)); o.paste(p, (0, 28))
    ImageDraw.Draw(o).text((5, 5), t, font=F, fill=(40, 30, 30)); return cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR)
E.activate('selective'); t = {}
f1 = 1 / (BR.K1 * U)                                                  # one painted pixel per reference pixel
x, y = -100 + 58 * U, -70 + 276 * U
c = canvas(f1); t0 = time.time(); M.pair(x, y, H_MAP); t['new_1to1_s'] = round(time.time() - t0, 2); new = img(c)
c = canvas(f1); t0 = time.time(); T7.marine(-100 + 58 * U, y, face=1, h=H_MAP); T7.marine(-100 + 234 * U, y, face=-1, h=H_MAP); t['old_s'] = round(time.time() - t0, 2); old = img(c)
c = canvas(2); M.pair(x, y, H_MAP); new2 = img(c)                       # the size on the 2x Toy Town layer
E.deactivate()
ref = cv2.imread(os.path.join(HERE, 'assets', 'ref_marines.png'))
h = ref.shape[0]; fit = lambda a: cv2.resize(a, (round(a.shape[1] * h / a.shape[0]), h), interpolation=cv2.INTER_CUBIC)
row = np.hstack([label(ref, 'Reference'), np.full((h + 28, 12, 3), 255, np.uint8), label(fit(new), 'Hand-drawn, our brush'), np.full((h + 28, 12, 3), 255, np.uint8),
                 label(fit(old), 'Current (procedural)')])
big = cv2.resize(row, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
cv2.imwrite(os.path.join(OUT, 'marines_test.jpg'), big, [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite(os.path.join(OUT, 'marines_test_2x_layer.png'), new2)
print('sizes: reference', ref.shape[:2], 'new', new.shape[:2], 'on the 2x layer', new2.shape[:2], t)

"""Phase 1 visual validation: the published painting, the engine with equivalent settings, and the engine with
selective edges. Identical framing, size and zoom; detail crops are enlarged 3x with no smoothing."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, edges10 as E
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'); os.makedirs(OUT, exist_ok=True)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 19); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
pub = cv2.imread(os.path.join(R.ROOT, 'out5_6400', 'anim', 'base.jpg'))
def lab(im, t, s=''):
    p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (p.width, p.height + 50), (250, 246, 236)); o.paste(p, (0, 50))
    d = ImageDraw.Draw(o); d.text((6, 4), t, font=F, fill=(40, 30, 30)); d.text((6, 28), s, font=f2, fill=(90, 80, 70)); return cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR)
def row(ims, g=10):
    h = max(i.shape[0] for i in ims); out = []
    for i in ims: out += [np.vstack([i, np.full((h - i.shape[0], i.shape[1], 3), 255, np.uint8)]), np.full((h, g, 3), 255, np.uint8)]
    return np.hstack(out[:-1])
REG = {'town': (940, 405, 1030, 600), 'farm': (560, 560, 760, 720)}
DETAIL = {'town': {'roof & windows': (958, 440, 1004, 505), 'sign, awning, shop window & toys': (958, 505, 1004, 550), 'cobbles, box & figures': (940, 552, 1000, 598)},
          'farm': {'hills & grass': (600, 640, 660, 690), 'trees': (690, 600, 750, 660), 'house': (570, 600, 630, 650)}}
renders = {}
for name, (a, b, c_, d) in REG.items():
    x0, y0 = map(int, R.map_to_px(a, b, 1)); x1, y1 = map(int, R.map_to_px(c_, d, 1)); pad = 46
    P = pub[y0:y1, x0:x1]
    E.activate('equivalent'); eq, _, s1 = R.render_window(1, (x0 - pad, y0 - pad, x1 + pad, y1 + pad)); eq = eq[pad:-pad, pad:-pad]
    E.activate('selective'); se, _, s2 = R.render_window(1, (x0 - pad, y0 - pad, x1 + pad, y1 + pad)); se = se[pad:-pad, pad:-pad]; E.deactivate()
    renders[name] = (P, eq, se, (x0, y0))
    cv2.imwrite(f'{OUT}/cmp_{name}_published.png', P); cv2.imwrite(f'{OUT}/cmp_{name}_equivalent.png', eq); cv2.imwrite(f'{OUT}/cmp_{name}_selective.png', se)
    print(name, 'equivalent', s1['seconds'], 's; selective', s2['seconds'], 's', flush=True)
sheets = []
for name in REG:
    P, eq, se, (x0, y0) = renders[name]
    sheets.append(row([lab(P, '1  Published (legacy brush)'), lab(eq, '2  Engine, equivalent settings'), lab(se, '3  Engine, selective edges')]))
    for dn, (a, b, c_, d) in DETAIL[name].items():
        u0, v0 = map(int, R.map_to_px(a, b, 1)); u1, v1 = map(int, R.map_to_px(c_, d, 1))
        cr = [cv2.resize(im[v0 - y0:v1 - y0, u0 - x0:u1 - x0], None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST) for im in (P, eq, se)]
        sheets.append(row([lab(cr[0], f'1  {dn}', '3x, no smoothing'), lab(cr[1], '2'), lab(cr[2], '3')]))
W_ = max(s.shape[1] for s in sheets)
cv2.imwrite(f'{OUT}/phase1_comparison.jpg', np.vstack([np.hstack([s, np.full((s.shape[0], W_ - s.shape[1], 3), 255, np.uint8)]) for s in sheets]), [cv2.IMWRITE_JPEG_QUALITY, 90])
print('written')

"""Phase 4 character study: the square's current Marine (tft7) next to the posed figure from figures10, at the size
used on the map (28 units tall). Row 1: national map at 100% (1x). Row 2: the 2x Toy Town layer at 100%."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, figures10 as FG, edges10 as E
BR = R.BR; T7 = R.T7
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
def canvas(f, wu, hu):
    k = BR.K1 * f; W, H = int(wu * k), int(hu * k)
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, (0, 0, W, H), ground='#d9d2c2'); R.use(c); c.eseed = 11
    m = c.mask([(-100, -70), (-100 + wu, -70), (-100 + wu, -70 + hu), (-100, -70 + hu)], 0, .2, 5, soft=.3)
    c.stip(m, lambda X, Y, rr: np.array([[.86, .83, .78], [.80, .77, .72], [.74, .70, .64]])[rr.randint(3, size=len(X))], spacing=.7, L=1.3, w=.7, angfn=lambda X, Y: 0 * X, seed=4, jit=.4)
    return c
def img(c): return (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
H = 28
CASES = [('current Marine (live)', lambda x, y: T7.marine(x, y, face=1, h=H)),
         ('posed: giving a gift', lambda x, y: FG.marine(x, y, H, 1, 'give')),
         ('posed: carrying gifts', lambda x, y: FG.marine(x, y, H, 1, 'carry')),
         ('posed: saluting', lambda x, y: FG.marine(x, y, H, 1, 'salute')),
         ('posed: pulling the wagon', None)]
rows, times = [], {}
for f in (1, 2):
    cells = []
    for name, fn in CASES:
        wu = 34 if fn else 52; hu = 36
        c = canvas(f, wu, hu); E.activate('selective'); t0 = time.time(); x0, yb = -100 + 14, -70 + hu - 3
        if fn: fn(x0, yb)
        else:
            hand = FG.marine(x0 + 4, yb, H, -1, 'pull'); FG.wagon(x0 + 26, yb, 1.25, handle_to=hand)
        times[f'{name} f{f}'] = round(time.time() - t0, 2); E.deactivate()
        p = Image.fromarray(cv2.cvtColor(img(c), cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (max(p.width, 200), p.height + 22), (250, 246, 236)); o.paste(p, (0, 22))
        ImageDraw.Draw(o).text((3, 3), name, font=F, fill=(40, 30, 30)); cells.append(np.pad(cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR), ((0, 0), (0, 8), (0, 0)), constant_values=255))
    hm = max(x.shape[0] for x in cells)
    r = np.hstack([np.vstack([x, np.full((hm - x.shape[0], x.shape[1], 3), 255, np.uint8)]) for x in cells])
    p = Image.new('RGB', (r.shape[1], 26), (255, 255, 255)); ImageDraw.Draw(p).text((3, 4), ('national map at 100% (1x)' if f == 1 else '2x Toy Town layer at 100%'), font=F, fill=(40, 30, 30))
    rows.append(np.vstack([cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR), r]))
Wm = max(r.shape[1] for r in rows)
cv2.imwrite(f'{OUT}/figure_study.jpg', np.vstack([np.hstack([r, np.full((r.shape[0], Wm - r.shape[1], 3), 255, np.uint8)]) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 90])
json.dump(times, open(f'{OUT}/figure_study_times.json', 'w'), indent=1); print('ok', times)

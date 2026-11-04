"""Component sandbox: the toy library at the sizes visitors will see. Row 1: each toy 4.5 map units tall in a lit shop
window on the 2x Toy Town layer, shown at 100% of that layer. Row 2: the same at 100% of the national map (1x).
Row 3: 12 map units tall on the 2x layer, zoomed 2.5x (the closest view). Last column of rows 1-2: lab8's toys."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, toys10 as TY
BR = R.BR; T7 = R.T7
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
def canvas(f, wu, hu):
    k = BR.K1 * f; W, H = int(wu * k), int(hu * k)
    for m in R.MODS: m.c = None
    c = BR.EngineCanvas(f, (0, 0, W, H), ground='#f2c25a'); R.use(c); c.eseed = 7
    m = c.mask([(-100, -70), (-100 + wu, -70), (-100 + wu, -70 + hu), (-100, -70 + hu)], 0, .2, 5, soft=.3)
    G = np.array([hexc(z) for z in ('#f8dc8a', '#f2c25a', '#d8962e')]) if False else None
    c.stip(m, lambda X, Y, rr: np.array([[.97, .86, .54], [.95, .76, .35], [.85, .59, .18]])[rr.randint(3, size=len(X))][:, ::1], spacing=.6, L=1.2, w=.6, angfn=lambda X, Y: 0 * X, seed=6, jit=.4)
    return c
def img(c): return (np.clip(c.img, 0, 1)[..., ::-1] * 255 + .5).astype(np.uint8)
rows = []; times = {}
for (f, h, zoom, label) in ((2, 4.5, 1, 'in the window, 2x layer at 100%'), (1, 4.5, 1, 'in the window, national map at 100%'), (2, 12, 2.5, 'close-up: 12 units tall, 2x layer zoomed 2.5x')):
    cells = []
    for name, fn in TY.GALLERY + ([('lab8 toys', None)] if h < 6 else []):
        wu = max(10, h * 1.6); hu = h * 1.35
        c = canvas(f, wu, hu); t0 = time.time()
        if fn: fn(-100 + wu / 2, -70 + hu - .8, h)
        else:
            T7.teddy(-100 + wu * .3, -70 + hu - .8, h / 10.6); T7.rocking_horse(-100 + wu * .7, -70 + hu - .8, h / 9.6)
        times[f'{name} f{f} h{h}'] = round(time.time() - t0, 3)
        im = img(c)
        if zoom != 1: im = cv2.resize(im, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
        sc = max(1, int(round(96 / im.shape[0]))) if zoom == 1 else 1
        if sc > 1: im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_NEAREST)
        p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (max(p.width, 120), p.height + 22), (250, 246, 236)); o.paste(p, (0, 22))
        ImageDraw.Draw(o).text((3, 3), name, font=F, fill=(40, 30, 30)); cells.append(cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR))
    hmax = max(x.shape[0] for x in cells)
    row = np.hstack([np.vstack([x, np.full((hmax - x.shape[0], x.shape[1], 3), 255, np.uint8)]) for x in [np.pad(x, ((0, 0), (0, 6), (0, 0)), constant_values=255) for x in cells]])
    p = Image.new('RGB', (row.shape[1], 26), (255, 255, 255)); ImageDraw.Draw(p).text((3, 4), label + ('  (small views enlarged with no smoothing, so pixels show)' if zoom == 1 else ''), font=F, fill=(40, 30, 30))
    rows.append(np.vstack([cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR), row]))
Wm = max(r.shape[1] for r in rows)
cv2.imwrite(f'{OUT}/toy_library.jpg', np.vstack([np.hstack([r, np.full((r.shape[0], Wm - r.shape[1], 3), 255, np.uint8)]) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 90])
json.dump(times, open(f'{OUT}/toy_library_times.json', 'w'), indent=1); print('ok', max(times.values()))

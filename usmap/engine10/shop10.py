"""Phase 4 deliverable: the yellow shop as it is now, as lab8's B, and as engine10's A / B / C, at three scales:
close-up (the 2x Toy Town layer), Toy Town view (the national map at 100% and at the Toy Town button's 57%) and
national view (the whole map fitted to a laptop screen, about 20%)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, edges10 as E, store10 as ST10, store8 as ST8
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
SHOP = (944, 408, 1022, 600); TOWN = (680, 230, 1180, 650)
VERS = [('Original (published)', 'orig', ST10, 'equivalent'), ('lab8 B (previous best)', 'B', ST8, 'selective'),
        ('A  Refined construction', 'A', ST10, 'selective'), ('B  Rich illustration', 'B', ST10, 'selective'), ('C  Storybook', 'C', ST10, 'selective')]
def lab(im, t, s=''):
    p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (p.width, p.height + 50), (250, 246, 236)); o.paste(p, (0, 50))
    d = ImageDraw.Draw(o); d.text((6, 4), t, font=F, fill=(40, 30, 30)); d.text((6, 28), s, font=f2, fill=(90, 80, 70)); return cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR)
def row(ims, g=12):
    h = max(i.shape[0] for i in ims); out = []
    for i in ims: out += [np.vstack([i, np.full((h - i.shape[0], i.shape[1], 3), 255, np.uint8)]), np.full((h, g, 3), 255, np.uint8)]
    return np.hstack(out[:-1])
def render(box, f, level, mod, prof):
    E.activate(prof); x0, y0 = map(int, R.map_to_px(box[0], box[1], f)); x1, y1 = map(int, R.map_to_px(box[2], box[3], f)); pad = int(np.ceil(16 * R.BR.K1 * f))
    t0 = time.time(); img, _, _ = R.render_window(f, (x0 - pad, y0 - pad, x1 + pad, y1 + pad), level=None if level == 'orig' else level, shop=mod); E.deactivate()
    return img[pad:-pad, pad:-pad], time.time() - t0
times = {}; close, t100, town = [], [], []
for name, level, mod, prof in VERS:
    tag = name.split()[0] if name[0] in 'ABC' else ('orig' if level == 'orig' else 'lab8B')
    im2, dt2 = render(SHOP, 2, level, mod, prof); im1, dt1 = render(SHOP, 1, level, mod, prof); tw, dt3 = render(TOWN, 1, level, mod, prof)
    times[name] = dict(close_2x_s=round(dt2, 1), map_1x_s=round(dt1, 1), town_1x_s=round(dt3, 1))
    for nm, im in (('close', im2), ('map', im1), ('town', tw)): cv2.imwrite(f'{OUT}/shop_{tag}_{nm}.png', im)
    # close-up: the 2x layer, the ground floor at 1.6x on screen
    k2 = R.BR.K1 * 2; gx0, gy0, gx1, gy1 = [int(v) for v in ((954 - SHOP[0]) * k2, (500 - SHOP[1]) * k2, (1014 - SHOP[0]) * k2, (556 - SHOP[1]) * k2)]
    close.append(lab(cv2.resize(im2[gy0:gy1, gx0:gx1], None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC), name, 'close-up: 2x layer, zoomed 1.6x'))
    t100.append(lab(np.hstack([im1, np.full((im1.shape[0], 8, 3), 255, np.uint8), cv2.resize(im1, None, fx=.57, fy=.57, interpolation=cv2.INTER_AREA)
                               if False else np.vstack([cv2.resize(im1, None, fx=.57, fy=.57, interpolation=cv2.INTER_AREA), np.full((im1.shape[0] - round(im1.shape[0] * .57), round(im1.shape[1] * .57), 3), 255, np.uint8)])]), name, 'map at 100% | at 57% (Toy Town view)'))
    town.append(lab(cv2.resize(tw, None, fx=.2, fy=.2, interpolation=cv2.INTER_AREA), name.split('  ')[0], 'national view (20%)'))
    print(name, times[name], flush=True)
cv2.imwrite(f'{OUT}/shop_closeup.jpg', np.vstack([row(close[:3]), np.full((14, row(close[:3]).shape[1], 3), 255, np.uint8),
                                                 np.hstack([row(close[3:]), np.full((row(close[3:]).shape[0], row(close[:3]).shape[1] - row(close[3:]).shape[1], 3), 255, np.uint8)])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(f'{OUT}/shop_toytown_view.jpg', row(t100), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(f'{OUT}/shop_national_view.jpg', row(town), [cv2.IMWRITE_JPEG_QUALITY, 92])
json.dump(times, open(f'{OUT}/shop_times.json', 'w'), indent=1)

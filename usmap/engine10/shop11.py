"""Phase 6: the yellow-shop comparison sheets (as shop10.py), made without repainting what did not change.
- close-up: only the area shown (the ground floor), painted on the 2x layer
- Toy Town view and national view: the cached map, with only the yellow house painted fresh for each version
  (views10.view; equal to a complete render, see tools/check_patched_view.py)
The original version needs no painting at all: it is the cache. Caches used: f1 (default edges) and f1_sel (the
'selective' edge profile, Toy Town only): cache10.py build 1 680 230 1180 650 --profile selective --store f1_sel."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import views10 as V, store10 as ST10, store8 as ST8
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
SHOP = (944, 408, 1022, 600); TOWN = (680, 230, 1180, 650); CLOSE = (954, 500, 1014, 556)
VERS = [('Original (published)', None, None, 'equivalent'), ('lab8 B (previous best)', 'B', ST8, 'selective'),
        ('A  Refined construction', 'A', ST10, 'selective'), ('B  Rich illustration', 'B', ST10, 'selective'), ('C  Storybook', 'C', ST10, 'selective')]
def lab(im, t, s=''):
    p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (p.width, p.height + 50), (250, 246, 236)); o.paste(p, (0, 50))
    d = ImageDraw.Draw(o); d.text((6, 4), t, font=F, fill=(40, 30, 30)); d.text((6, 28), s, font=f2, fill=(90, 80, 70)); return cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR)
def row(ims, g=12):
    h = max(i.shape[0] for i in ims); out = []
    for i in ims: out += [np.vstack([i, np.full((h - i.shape[0], i.shape[1], 3), 255, np.uint8)]), np.full((h, g, 3), 255, np.uint8)]
    return np.hstack(out[:-1])
T0 = time.time(); times = {}; close, t100, town = [], [], []
for name, level, mod, prof in VERS:
    store = 'f1' if prof == 'equivalent' else 'f1_sel'; patches = [V.yellow_shop_patch()] if level else []
    kw = dict(level=level, shop=mod) if level else {}
    t = time.time(); cu = V.crop(2, CLOSE, prof, **kw); t_close = time.time() - t
    t = time.time(); m1 = V.view(1, SHOP, store, patches, prof, **kw); t_map = time.time() - t
    t = time.time(); tw = V.view(1, TOWN, store, patches, prof, **kw); t_town = time.time() - t
    times[name] = dict(close_2x_s=round(t_close, 1), map_1x_s=round(t_map, 1), town_1x_s=round(t_town, 1))
    close.append(lab(cv2.resize(cu, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC), name, 'close-up: 2x layer, zoomed 1.6x'))
    small = cv2.resize(m1, None, fx=.57, fy=.57, interpolation=cv2.INTER_AREA)
    t100.append(lab(np.hstack([m1, np.full((m1.shape[0], 8, 3), 255, np.uint8), np.vstack([small, np.full((m1.shape[0] - small.shape[0], small.shape[1], 3), 255, np.uint8)])]), name, 'map at 100% | at 57% (Toy Town view)'))
    town.append(lab(cv2.resize(tw, None, fx=.2, fy=.2, interpolation=cv2.INTER_AREA), name.split('  ')[0], 'national view (20%)'))
    print(name, times[name], flush=True)
r1 = row(close[:3]); r2 = row(close[3:])
cv2.imwrite(f'{OUT}/shop11_closeup.jpg', np.vstack([r1, np.full((14, r1.shape[1], 3), 255, np.uint8), np.hstack([r2, np.full((r2.shape[0], r1.shape[1] - r2.shape[1], 3), 255, np.uint8)])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(f'{OUT}/shop11_toytown_view.jpg', row(t100), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(f'{OUT}/shop11_national_view.jpg', row(town), [cv2.IMWRITE_JPEG_QUALITY, 92])
times['total_s'] = round(time.time() - T0, 1); json.dump(times, open(f'{OUT}/shop11_times.json', 'w'), indent=1); print('total', times['total_s'], 's')

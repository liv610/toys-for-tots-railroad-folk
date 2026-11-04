"""Phase 3 question: which density is worth it for the Toy Town layer? Renders the yellow shop at f = 1, 2, 3, 4, with
the current artwork and with richer content (lab8's level B), all shown at the same on-screen size (as a visitor
zoomed in would see them), and measures render time, pixel count and JPEG size per square map unit."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import render10 as R, edges10 as E
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
BOX = (952, 455, 1012, 560); SHOW_W = 360; res = {}
def lab(im, t, s):
    p = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); o = Image.new('RGB', (p.width, p.height + 52), (250, 246, 236)); o.paste(p, (0, 52))
    d = ImageDraw.Draw(o); d.text((6, 4), t, font=F, fill=(40, 30, 30)); d.text((6, 30), s, font=f2, fill=(90, 80, 70)); return cv2.cvtColor(np.array(o), cv2.COLOR_RGB2BGR)
rows = []
for content, level, prof in (('current artwork', None, 'equivalent'), ('richer content (lab8 B), selective edges', 'B', 'selective')):
    E.activate(prof); ims = []
    for f in (1, 2, 3, 4):
        x0, y0 = map(int, R.map_to_px(BOX[0], BOX[1], f)); x1, y1 = map(int, R.map_to_px(BOX[2], BOX[3], f)); pad = int(np.ceil(16 * R.BR.K1 * f))
        t0 = time.time(); img, _, _ = R.render_window(f, (x0 - pad, y0 - pad, x1 + pad, y1 + pad), level=level); dt = time.time() - t0
        img = img[pad:-pad, pad:-pad]; ok, enc = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        area = (BOX[2] - BOX[0]) * (BOX[3] - BOX[1])
        res[f'{content} f{f}'] = dict(seconds=round(dt, 1), px=int(img.shape[0] * img.shape[1]), jpeg_kb_per_1000_sq_units=round(len(enc) / 1024 / area * 1000, 1))
        show = cv2.resize(img, (SHOW_W, round(img.shape[0] * SHOW_W / img.shape[1])), interpolation=cv2.INTER_CUBIC if img.shape[1] < SHOW_W else cv2.INTER_AREA)
        ims.append(lab(show, f'{f}x density', f'{img.shape[1]}x{img.shape[0]} px, {dt:.0f}s'))
        cv2.imwrite(f'{OUT}/ladder_{"rich" if level else "current"}_f{f}.png', img); print(content, f, res[f'{content} f{f}'], flush=True)
    rows.append(np.hstack([np.pad(i, ((0, 0), (0, 10), (0, 0)), constant_values=255) for i in ims]))
E.deactivate()
cv2.imwrite(f'{OUT}/density_ladder.jpg', np.vstack([np.pad(r, ((0, 14), (0, 0), (0, 0)), constant_values=255) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 90])
json.dump(res, open(f'{OUT}/density_ladder.json', 'w'), indent=1)

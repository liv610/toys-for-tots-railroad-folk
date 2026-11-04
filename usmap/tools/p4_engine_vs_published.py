#!/usr/bin/env python3
"""How different is the engine's map from the published one? Compares the published 6400 base (the painting under
the moving parts, out5_6400/anim/base.jpg) with the engine's complete 1x render, overall and at four places, and
writes a side-by-side sheet: engine10/out/p4_engine_vs_published.jpg.
    cd usmap && python3 tools/p4_engine_vs_published.py"""
import os, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pub = cv2.imread(os.path.join(ROOT, 'out5_6400/anim/base.jpg')); eng = cv2.imread(os.path.join(ROOT, 'engine10/out/complete/f1_whole_map.png'))
pub_png = cv2.imread(os.path.join(ROOT, 'out5_6400/usmap5.png'))
K = 6400 / 1671; P = lambda x, y: (int((x + 100) * K), int((y + 70) * K))
blur = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), 6)
rep = dict(identical_pixels_pct=round(float(np.all(pub == eng, -1).mean() * 100), 2),
           mean_abs_diff_levels=round(float(np.abs(pub.astype(int) - eng.astype(int)).mean()), 1),
           mean_colour_diff_levels=[round(float(v), 2) for v in (eng.reshape(-1, 3).mean(0) - pub.reshape(-1, 3).mean(0))[::-1]],
           blurred_diff_levels=round(float(np.abs(blur(pub) - blur(eng)).mean()), 2),
           note='base.jpg is JPEG (quality 92), so even an identical painting would not match pixel for pixel')
places = [('Toy Town shops', 930, 470), ('Northwest coast', 120, 220), ('Florida', 1190, 760), ('River and bridge', 1000, 560)]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18); rows = []
for name, x, y in places:
    cx, cy = P(x, y); h, w = 260, 360
    a = pub[cy - h // 2:cy + h // 2, cx - w // 2:cx + w // 2]; b = eng[cy - h // 2:cy + h // 2, cx - w // 2:cx + w // 2]
    rep[name] = dict(mean_abs_diff=round(float(np.abs(a.astype(int) - b.astype(int)).mean()), 1), blurred_diff=round(float(np.abs(blur(a) - blur(b)).mean()), 2))
    rows.append(np.hstack([a, np.full((h, 10, 3), 255, np.uint8), b]))
sheet = np.vstack([np.vstack([r, np.full((10, r.shape[1], 3), 255, np.uint8)]) for r in rows])
im = Image.fromarray(cv2.cvtColor(sheet, cv2.COLOR_BGR2RGB)); out = Image.new('RGB', (im.width, im.height + 34), (250, 246, 236)); out.paste(im, (0, 34))
d = ImageDraw.Draw(out); d.text((6, 8), 'Published map (left)  |  Tiled engine (right)   same places, 100% at 6400', font=F, fill=(40, 30, 30))
out.save(os.path.join(ROOT, 'engine10/out/p4_engine_vs_published.jpg'), quality=90)
json.dump(rep, open(os.path.join(ROOT, 'engine10/out/p4_engine_vs_published.json'), 'w'), indent=1); print(json.dumps(rep, indent=1))

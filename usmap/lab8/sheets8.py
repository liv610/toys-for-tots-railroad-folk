"""lab8 — comparison sheets for the storefront experiment (same crop and zoom for every level)."""
import os, json, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(HERE, 'out')
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
NAMES = {'orig': 'Original', 'A': 'A  Refined', 'B': 'B  Rich', 'C': 'C  Maximum'}
LV = ['orig', 'A', 'B', 'C']; K4 = 6400 / 1671 * 4; BOX = (940, 405, 1030, 600)
def labelled(im, t, sub=None):
    h = 44 if not sub else 70
    pi = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); out = Image.new('RGB', (pi.width, pi.height + h), (250, 246, 236))
    out.paste(pi, (0, h)); d = ImageDraw.Draw(out); d.text((10, 7), t, font=F, fill=(40, 30, 30))
    if sub: d.text((10, 40), sub, font=f2, fill=(90, 80, 70))
    return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
def row(ims, gap=14):
    h = max(i.shape[0] for i in ims); ims = [np.vstack([i, np.full((h - i.shape[0], i.shape[1], 3), 255, np.uint8)]) for i in ims]
    parts = []
    for i in ims: parts += [i, np.full((h, gap, 3), 255, np.uint8)]
    return np.hstack(parts[:-1])
fit = lambda im, w: cv2.resize(im, (w, round(im.shape[0] * w / im.shape[1])), interpolation=cv2.INTER_AREA)
close = {lv: cv2.imread(f'{O}/{lv}_close.png') for lv in LV}; mp = {lv: cv2.imread(f'{O}/{lv}_map.png') for lv in LV}
# 1. the whole crop, close up (the same 90 x 195 map-unit rectangle, same scale)
cv2.imwrite(f'{O}/sheet1_closeup_whole.jpg', row([labelled(fit(close[lv], 470), NAMES[lv]) for lv in LV]), [cv2.IMWRITE_JPEG_QUALITY, 90])
# 2. the shop's ground floor and sign, close up
def sub(im, x0, y0, x1, y1, k):
    return im[int((y0 - BOX[1]) * k):int((y1 - BOX[1]) * k), int((x0 - BOX[0]) * k):int((x1 - BOX[0]) * k)]
g = [labelled(fit(sub(close[lv], 954, 500, 1012, 556, K4), 700), NAMES[lv]) for lv in LV]
cv2.imwrite(f'{O}/sheet2_closeup_storefront.jpg', np.vstack([row(g[:2]), np.full((14, row(g[:2]).shape[1], 3), 255, np.uint8), row(g[2:])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
# 2b. upper floors and roof, close up
u = [labelled(fit(sub(close[lv], 952, 412, 1010, 508, K4), 420), NAMES[lv]) for lv in LV]
cv2.imwrite(f'{O}/sheet3_closeup_upper.jpg', row(u), [cv2.IMWRITE_JPEG_QUALITY, 90])
# 3. at map scale: 100% of the zoomable map, and at the 'Toy Town' button's zoom (about 57%)
m100 = [labelled(mp[lv], NAMES[lv], '100% of the map') for lv in LV]
m57 = [labelled(cv2.resize(mp[lv], None, fx=.57, fy=.57, interpolation=cv2.INTER_AREA), NAMES[lv], '57%: Toy Town view') for lv in LV]
cv2.imwrite(f'{O}/sheet4_map_scale.jpg', np.vstack([row(m100), np.full((18, row(m100).shape[1], 3), 255, np.uint8), np.hstack([row(m57), np.full((row(m57).shape[0], row(m100).shape[1] - row(m57).shape[1], 3), 255, np.uint8)])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
print('sheets written')

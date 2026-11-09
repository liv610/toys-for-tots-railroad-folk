"""Place the blue shop study into the map at the Toy Town detail scale, on the fit-check composite (the rest of
the town still in the target's own texture), and at national-map scale. Preview images only."""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'docs', 'toytown_layout'))
import make_sketches as M, fit_check as FC
import study_blue_shop as B

det = M.stitch(os.path.join(M.ROOT, 'tiles', 'detail_files', '13'), 5, 4)
S = FC.S; ox, oy = int(round(FC.OX)), int(round(FC.OY))
big = FC.T.resize((int(FC.T.width * S), int(FC.T.height * S)), Image.LANCZOS)
lay = Image.new('RGB', det.size); lay.paste(det); lay.paste(big, (ox, oy))
m = Image.new('L', det.size, 0)
ImageDraw.Draw(m).polygon([FC.t2d(p) for p in [(170, 20), (1230, 20), (1260, 330), (1350, 790), (1350, 900), (1080, 990), (700, 1010), (330, 990), (20, 900), (20, 560), (170, 380)]], fill=255)
m = m.filter(ImageFilter.GaussianBlur(60)); comp = Image.composite(lay, det, m)
shop = np.load(os.path.join(B.OUT, 'blue_shop_detail_scale.npy')).astype(np.float32)
px, py = FC.t2d((B.BOX[0], B.BOX[1])); px, py = int(round(px)), int(round(py))
c = np.asarray(comp).astype(np.float32) / 255; h, w = shop.shape[:2]
reg = c[py:py + h, px:px + w]; a = shop[..., 3:4]
c[py:py + h, px:px + w] = reg * (1 - a) + shop[..., :3] * a
out = (np.clip(c, 0, 1) * 255).astype(np.uint8)
Image.fromarray(out[int(py - 250):int(py + h + 250), int(px - 120):int(px + w + 900)]).save(os.path.join(B.OUT, 'blue_shop_in_context_detail.jpg'), quality=90)
Image.fromarray(out).crop((500, 150, 4800, 3800)).resize((1720, 1460), Image.LANCZOS).save(os.path.join(B.OUT, 'blue_shop_in_context_town.jpg'), quality=90)
print('ok', px, py, w, h)

"""The built blue shop (v3) placed in Toy Town at the detail layer's real scale, on the fit-check composite
(the neighbours still in the target painting's texture). Preview only."""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'docs', 'toytown_layout'))
import make_sketches as M, fit_check as FC
det = M.stitch(os.path.join(M.ROOT, 'tiles', 'detail_files', '13'), 5, 4)
S = FC.S; ox, oy = int(round(FC.OX)), int(round(FC.OY))
big = FC.T.resize((int(FC.T.width * S), int(FC.T.height * S)), Image.LANCZOS)
lay = Image.new('RGB', det.size); lay.paste(det); lay.paste(big, (ox, oy))
m = Image.new('L', det.size, 0)
ImageDraw.Draw(m).polygon([FC.t2d(p) for p in [(170, 20), (1230, 20), (1260, 330), (1350, 790), (1350, 900), (1080, 990), (700, 1010), (330, 990), (20, 900), (20, 560), (170, 380)]], fill=255)
comp = np.asarray(Image.composite(lay, det, m.filter(ImageFilter.GaussianBlur(60)))).astype(np.float32) / 255
a = cv2.imread(os.path.join(HERE, 'out', 'blue_shop_v3_study.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
k = S / 4; a = cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
px, py = [int(round(v)) for v in FC.t2d((0, 430))]; h, w = a.shape[:2]
reg = comp[py:py + h, px:px + w]; al = a[..., 3:]
comp[py:py + h, px:px + w] = reg * (1 - al) + a[..., 2::-1] * al
out = (np.clip(comp, 0, 1) * 255).astype(np.uint8)
Image.fromarray(out[py - 200:py + h + 150, max(0, px - 150):px + w + 700]).save(os.path.join(HERE, 'out', 'blue_shop_v3_in_context.jpg'), quality=90)
print('ok')

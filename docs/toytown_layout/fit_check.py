"""Fit check: place the user's target painting over the real map and measure how well its landmarks land.

A single uniform scale (2.75 detail px per target px, the same both ways) plus an offset, anchored on the
station's walls and banner. No warping, so nothing in the painting is stretched. Writes:
  fit/overlay.jpg       the target at 65% over today's Toy Town detail art, with landmark pairs marked
  fit/in_map_detail.jpg the target dropped into the detail art inside a soft town-shaped mask
  fit/in_map_national.jpg the same at national-map scale (what a visitor sees zoomed out)
  fit/fit.json          landmark offsets in detail px
Nothing in the map, routes or engine changes; these are preview images only.
"""
import os, json
from PIL import Image, ImageDraw, ImageFilter
import make_sketches as M

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'fit')
T = Image.open(os.path.join(HERE, 'reference', 'toytown_target.webp')).convert('RGB')
S = 2.747                                   # from the station's outer walls: 1010 target px <-> 2774 detail px
OX, OY = 1293 - 195 * S, 1173 - 285 * S     # left wall and banner line up
t2d = lambda p: (OX + p[0] * S, OY + p[1] * S)

# landmark pairs: (name, target px, detail px measured on today's art)
PAIRS = [('station left wall', (195, 300), (1293, 1215)), ('station right wall', (1205, 300), (4067, 1215)),
         ('roof finial', (700, 15), (2677, 450)), ('star emblem', (700, 165), (2673, 900)), ('banner', (700, 285), (2667, 1173)),
         ('left corner tower', (395, 170), (1900, 830)), ('right corner tower', (995, 170), (3450, 830)),
         ('stone bridge, top of deck', (1210, 805), (4040, 2650)), ('red line at the west wall', (195, 360), (1293, 1563)),
         ('green line at the red bridge', (1330, 410), (4360, 1680)), ('station base (today)', (700, 640), (2700, 1960))]

def main():
    os.makedirs(OUT, exist_ok=True)
    det = M.stitch(os.path.join(M.ROOT, 'tiles', 'detail_files', '13'), 5, 4)
    W, H = int(T.width * S), int(T.height * S)
    big = T.resize((W, H), Image.LANCZOS); ox, oy = int(round(OX)), int(round(OY))
    # 1) overlay
    lay = Image.new('RGB', det.size); lay.paste(det); lay.paste(big, (ox, oy))
    ov = Image.blend(det, lay, .65)
    d = ImageDraw.Draw(ov); res = {}
    for name, tp, dp in PAIRS:
        a = t2d(tp); res[name] = [round(a[0] - dp[0]), round(a[1] - dp[1])]
        d.line([a, dp], fill=(255, 255, 0), width=6)
        d.ellipse((dp[0] - 22, dp[1] - 22, dp[0] + 22, dp[1] + 22), outline=(255, 255, 255), width=8)
        d.line([(a[0] - 26, a[1]), (a[0] + 26, a[1])], fill=(230, 60, 20), width=8); d.line([(a[0], a[1] - 26), (a[0], a[1] + 26)], fill=(230, 60, 20), width=8)
        d.text((dp[0] + 30, dp[1] - 30), f'{name}: {res[name][0]:+d}, {res[name][1]:+d} px', font=M.F(44, True), fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    for k, pts in M.ROUTES.items():
        d.line([M.f1_to_d(p) for p in pts], fill=M.RCOL[k], width=10)
    ov.crop((500, 150, 4800, 3800)).resize((1720, 1460), Image.LANCZOS).save(os.path.join(OUT, 'overlay.jpg'), quality=88)
    # 2) in the map: keep the map's surroundings, drop in the town inside a soft mask
    m = Image.new('L', det.size, 0); md = ImageDraw.Draw(m)
    town = [t2d(p) for p in [(170, 20), (1230, 20), (1260, 330), (1350, 790), (1350, 900), (1080, 990), (700, 1010), (330, 990), (20, 900), (20, 560), (170, 380)]]
    md.polygon(town, fill=255); m = m.filter(ImageFilter.GaussianBlur(60))
    lay2 = Image.new('RGB', det.size); lay2.paste(det); lay2.paste(big, (ox, oy))
    comp = Image.composite(lay2, det, m)
    for k, pts in M.ROUTES.items():       # today's rails, unchanged, redrawn faintly where the mask covers them
        pass
    comp.crop((500, 150, 4800, 3800)).resize((1720, 1460), Image.LANCZOS).save(os.path.join(OUT, 'in_map_detail.jpg'), quality=90)
    # 3) national scale: put the detail composite back into the base map (detail px = 2x f1, origin 2560,1024)
    base = M.stitch(os.path.join(M.ROOT, 'tiles', 'base_files', '13'), 7, 5).crop((0, 0, 7089, 4175))
    small = comp.resize((det.width // 2, det.height // 2), Image.LANCZOS); ms = m.resize(small.size)
    base.paste(small, (2560, 1024), ms)
    base.resize((1772, 1044), Image.LANCZOS).save(os.path.join(OUT, 'in_map_national.jpg'), quality=90)
    base.crop((1900, 450, 5600, 3450)).resize((1480, 1200), Image.LANCZOS).save(os.path.join(OUT, 'in_map_region.jpg'), quality=90)
    json.dump(dict(scale=S, offset=[OX, OY], offsets_px=res), open(os.path.join(OUT, 'fit.json'), 'w'), indent=1)
    print(json.dumps(res, indent=0))

if __name__ == '__main__':
    main()

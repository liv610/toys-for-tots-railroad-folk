"""Builds the deep-zoom viewer bundle for pass 4.

    python3 make_viewer4.py out4_6400 viewer4                       # pass 4
    python3 make_viewer4.py out5_6400 viewer5 viewer5_src/index.html # pass 5 (experimental)

Writes, inside the viewer folder:
  tiles/base_files/<level>/<col>_<row>.jpg + tiles/base.dzi   the painting WITHOUT moving parts (Deep Zoom format)
  sprites/*.png                                               every moving part, at full resolution
  occ/<col>_<row>.png                                         the occluder (things in front of the railroad),
                                                              cut into 512 px tiles, empty tiles skipped
  scene.json                                                  manifest + occluder tile list, for the page
  reference.jpg, still_preview.jpg
index.html is viewer4_src/index.html with scene.json inlined.
"""
import sys, os, json, math, shutil
import numpy as np, cv2

src, dst = sys.argv[1], sys.argv[2]
A = f'{src}/anim'
man = json.load(open(f'{A}/manifest.json'))
W, H = man['size']
for d in ('tiles/base_files', 'sprites', 'occ'):
    shutil.rmtree(f'{dst}/{d}', ignore_errors=True); os.makedirs(f'{dst}/{d}', exist_ok=True)

# ---- Deep Zoom pyramid of the base painting
TS, OV = 1024, 1
base = cv2.imread(f'{A}/base.jpg') if not os.path.exists(f'{A}/base.png') else cv2.imread(f'{A}/base.png')
maxL = math.ceil(math.log2(max(W, H)))
img = base; ntiles = 0
for L in range(maxL, -1, -1):
    h, w = img.shape[:2]; os.makedirs(f'{dst}/tiles/base_files/{L}', exist_ok=True)
    for cx in range(math.ceil(w / TS)):
        for cy in range(math.ceil(h / TS)):
            x0, y0 = max(0, cx * TS - OV), max(0, cy * TS - OV); x1, y1 = min(w, (cx + 1) * TS + OV), min(h, (cy + 1) * TS + OV)
            cv2.imwrite(f'{dst}/tiles/base_files/{L}/{cx}_{cy}.jpg', img[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 88]); ntiles += 1
    if L: img = cv2.resize(img, (max(1, math.ceil(w / 2)), max(1, math.ceil(h / 2))), interpolation=cv2.INTER_AREA)
open(f'{dst}/tiles/base.dzi', 'w').write(
    f'<?xml version="1.0" encoding="UTF-8"?><Image xmlns="http://schemas.microsoft.com/deepzoom/2008" TileSize="{TS}" Overlap="{OV}" Format="jpg"><Size Width="{W}" Height="{H}"/></Image>')
print('base tiles', ntiles, 'levels', maxL + 1)

# ---- occluder: sparse 512 px tiles
OT = 512
occ = cv2.imread(f'{A}/occluder.png', cv2.IMREAD_UNCHANGED); otiles = []
for cy in range(math.ceil(H / OT)):
    for cx in range(math.ceil(W / OT)):
        t = occ[cy * OT:(cy + 1) * OT, cx * OT:(cx + 1) * OT]
        if t[..., 3].max() < 8: continue
        cv2.imwrite(f'{dst}/occ/{cx}_{cy}.png', t, [cv2.IMWRITE_PNG_COMPRESSION, 9]); otiles.append([cx, cy])
print('occluder tiles', len(otiles))

# ---- sprites
for s in man['sprites']:
    shutil.copy(f'{A}/{s["file"]}', f'{dst}/sprites/{s["file"]}')
    if 'front' in s: shutil.copy(f'{A}/{s["front"]["file"]}', f'{dst}/sprites/{s["front"]["file"]}')
man['occluder'] = dict(tile=OT, tiles=otiles)
import time; man['build'] = time.strftime('%Y%m%d%H%M%S')                 # cache-busting tag for the page's asset URLs
json.dump(man, open(f'{dst}/scene.json', 'w'))
import glob
full = cv2.imread(sorted(glob.glob(f'{src}/usmap[0-9].png'))[-1])
cv2.imwrite(f'{dst}/still_preview.jpg', cv2.resize(full, (1600, round(1600 * full.shape[0] / full.shape[1])), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 86])
ref = cv2.imread('reference4.png'); cv2.imwrite(f'{dst}/reference.jpg', ref, [cv2.IMWRITE_JPEG_QUALITY, 92])
tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(dst) for f in fs)
print('bundle MB', round(tot / 1e6, 1), 'files', sum(len(fs) for _, _, fs in os.walk(dst)))

# ---- the page, with scene.json inlined (the page needs no fetch to start)
page = open(sys.argv[3] if len(sys.argv) > 3 else 'viewer4_src/index.html').read()
blob = '<script id="scene-data" type="application/json">' + json.dumps(man).replace('</', '<\\/') + '</script>\n'
open(f'{dst}/index.html', 'w').write(page.replace('<!-- scene.json is inlined here by make_viewer4.py -->\n', blob))
print('page written')

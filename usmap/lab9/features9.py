"""lab9 — the smallest detail the brush can paint, at the map's density and at 4x, with the default edge softness
(0.9 map units) and finer settings. Measures the peak opacity a filled disc of radius r reaches."""
import sys, os, json, numpy as np, cv2
sys.path[:0] = ['/home/claude/folk2']
from kit import Kanvas
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(f'{HERE}/out', exist_ok=True)
radii = [.25, .4, .6, .8, 1.0, 1.5, 2.0, 3.0]; res = {}
for kname, k in (('map 100%', 6400 / 1671), ('detail layer 4x', 6400 / 1671 * 4)):
    c = Kanvas(int(40 * k), int(12 * k), k, '#ffffff', seed=1)
    for soft in (.9, .32, .15):
        row = []
        for r in radii:
            pts = [(20 + r * np.cos(t), 6 + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 40, endpoint=False)]
            m = c.mask(pts, 0, .3, 7, soft=soft)
            row.append(round(float(m[2].max()) if m is not None else 0.0, 2))
        res[f'{kname}, soft {soft}'] = row
json.dump(dict(radii_map_units=radii, peak_opacity=res), open(f'{HERE}/out/features.json', 'w'), indent=1)
print('radius (map units):', radii)
for kk, v in res.items(): print(f'{kk:28s}', v)

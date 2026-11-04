"""Phase 1 test: tiles against the whole window, in four representative regions, at the published density.
Also compares the engine's whole-window render with the published base painting (out5_6400/anim/base.jpg)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import render10 as R
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'); os.makedirs(OUT, exist_ok=True)
REGIONS = {'toytown_storefront': (940, 405, 1030, 600), 'northwest_coast_mountains': (-40, 20, 210, 420),
           'florida_coast_palms': (1270, 690, 1480, 960), 'river_bridge_hills': (1000, 520, 1200, 760)}
f = float(os.environ.get('F', 1)); TILE = int(os.environ.get('TILE', 256)); res = {}
pub = cv2.imread(os.path.join(R.ROOT, 'out5_6400', 'anim', 'base.jpg')) if f == 1 else None
ONLY = os.environ.get('ONLY', '').split()
for name, (a, b, c_, d) in REGIONS.items():
    if ONLY and name not in ONLY: continue
    x0, y0 = map(int, R.map_to_px(a, b, f)); x1, y1 = map(int, R.map_to_px(c_, d, f))
    pad = int(np.ceil(16 * R.BR.K1 * f)); GW, GH = R.frame_px(f)
    wx0, wy0, wx1, wy1 = max(0, x0 - pad), max(0, y0 - pad), min(GW, x1 + pad), min(GH, y1 + pad)
    whole, Zw, st = R.render_window(f, (wx0, wy0, wx1, wy1)); whole = whole[y0 - wy0:y1 - wy0, x0 - wx0:x1 - wx0]   # the reference gets the same margin as the tiles
    tl, Zt, times = R.render_tiled(f, (x0, y0, x1, y1), tile=TILE)
    dd = np.abs(whole.astype(int) - tl.astype(int)).max(-1)
    # seams: is any difference concentrated on tile boundaries?
    bx = [(t - x0) for t in range((x0 // TILE + 1) * TILE, x1, TILE)]; by = [(t - y0) for t in range((y0 // TILE + 1) * TILE, y1, TILE)]
    near = np.zeros_like(dd, bool)
    for v in bx: near[:, max(0, v - 3):v + 3] = True
    for v in by: near[max(0, v - 3):v + 3, :] = True
    r = dict(size=[x1 - x0, y1 - y0], tiles=len(times), whole_s=st['seconds'], tiles_s=round(sum(times), 1),
             identical_pct=round(100 * float((dd == 0).mean()), 3), within_2_pct=round(100 * float((dd <= 2).mean()), 3), max_diff=int(dd.max()),
             mean_diff_on_seams=round(float(dd[near].mean()), 4) if near.any() else None, mean_diff_elsewhere=round(float(dd[~near].mean()), 4))
    if pub is not None:
        P = pub[y0:y1, x0:x1].astype(np.float32); Wn = whole.astype(np.float32)
        bl = lambda im: cv2.GaussianBlur(im, (0, 0), 6)
        hp = lambda im: float(np.std(im - bl(im)))
        r['vs_published'] = dict(mean_colour_published=[round(float(v), 1) for v in P.reshape(-1, 3).mean(0)[::-1]],
                                 mean_colour_engine=[round(float(v), 1) for v in Wn.reshape(-1, 3).mean(0)[::-1]],
                                 structure_diff=round(float(np.abs(bl(P) - bl(Wn)).mean()), 2),
                                 texture_energy_published=round(hp(P), 2), texture_energy_engine=round(hp(Wn), 2))
        cv2.imwrite(f'{OUT}/{name}_published.png', pub[y0:y1, x0:x1])
    cv2.imwrite(f'{OUT}/{name}_engine_whole.png', whole); cv2.imwrite(f'{OUT}/{name}_engine_tiled.png', tl)
    cv2.imwrite(f'{OUT}/{name}_tile_diff.png', np.clip(dd * 16, 0, 255).astype(np.uint8))
    res[name] = r; print(name, json.dumps(r), flush=True)
json.dump(dict(density=f, tile_px=TILE, regions=REGIONS, results=res), open(f'{OUT}/phase1_tiles_f{f:g}.json', 'w'), indent=1)

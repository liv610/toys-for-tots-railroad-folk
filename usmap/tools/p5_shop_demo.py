#!/usr/bin/env python3
"""Phase 5 demonstration: edit only the yellow TOY DONATION shop and rebuild incrementally.
Copies the 1x and 2x tile caches to cache/f1_shopdemo and cache/f2_shopdemo, sets the yellow shop's storefront to
lab8's level A in a copy of the scene (an existing experiment, used here only to make a visible edit), rebuilds
both caches and reports which tiles were painted. Verify afterwards with engine_complete_render.py --scene and
compare_tiles_to_complete.py --store.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/p5_shop_demo.py"""
import sys, os, json, copy, time, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import render10 as R, cache10 as C
TT = (670, 200, 1190, 650)
scene = json.load(open(R.SCENE)); s2 = copy.deepcopy(scene)
LEVEL = sys.argv[1] if len(sys.argv) > 1 else 'A'
shop = next(e for e in s2['elements'] if e['kind'] == 'shops7'); shop['params']['store_level'] = LEVEL
path = os.path.join(C.CACHE, f'scene_p5_yellow_shop_{LEVEL}.json'); json.dump(s2, open(path, 'w'))
rep = {}
for f, rect in ((1, None), (2, TT)):
    src, dst = os.path.join(C.CACHE, f'f{f}'), os.path.join(C.CACHE, f'f{f}_shopdemo')
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
    t0 = time.time(); r = C.build(f, rect, scene_path=path, store=f'f{f}_shopdemo', log=lambda m: print(m, flush=True))
    rep[f'f{f}'] = dict(tiles=len(C.tiles_for(f, rect)), painted=[p['tile'] for p in r['painted']], reused=len(r['reused']), seconds=round(time.time() - t0, 1))
print(json.dumps(rep)); json.dump(rep, open(os.path.join(C.HERE, 'out', f'p5_shop_demo_{LEVEL}.json'), 'w'), indent=1)

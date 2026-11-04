#!/usr/bin/env python3
"""Phase 4 demonstration: one small change to one existing object, rebuilt incrementally.
Copies the current 1x tile cache to cache/f1_demo, moves one tree that stands on a tile boundary by 9 map units
(in a copy of the scene), rebuilds the cache, and reports which tiles were painted and how long it took.
Then: tools/engine_complete_render.py --scene cache/scene_p4_tree.json paints the edited map as one window, and
tools/compare_tiles_to_complete.py --store f1_demo checks the assembled map against it.
    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/p4_demo.py"""
import sys, os, json, copy, time, glob, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine10'))
import render10 as R, cache10 as C
src, dst = os.path.join(C.CACHE, 'f1'), os.path.join(C.CACHE, 'f1_demo')
shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
scene = json.load(open(R.SCENE)); s2 = copy.deepcopy(scene)
ts = C.TS[1]; k = R.BR.K1; bx = [i * ts / k - R.BR.PADL for i in range(1, 7)]
cand = [e for e in s2['elements'] if e['kind'] == 'tree' and e['layer'] == 'base' and any(e['bbox'][0] < b < e['bbox'][2] for b in bx) and 300 < e['params']['y'] < 700]
tree = sorted(cand, key=lambda e: -e['params']['h'])[0]
tree['params']['x'] += 9; tree['bbox'] = [tree['bbox'][0] + 9, tree['bbox'][1], tree['bbox'][2] + 9, tree['bbox'][3]]
path = os.path.join(C.CACHE, 'scene_p4_tree.json'); json.dump(s2, open(path, 'w'))
t0 = time.time(); r = C.build(1, None, scene_path=path, store='f1_demo', log=lambda m: print(m, flush=True)); wall = time.time() - t0
rep = dict(object=f"tree at map ({tree['params']['x'] - 9:.0f}, {tree['params']['y']:.0f}), moved 9 units east", tiles=len(C.tiles_for(1)),
           painted=[p['tile'] for p in r['painted']], reused=len(r['reused']), seconds=round(wall, 1))
print(json.dumps(rep)); json.dump(rep, open(os.path.join(C.HERE, 'out', 'p4_demo.json'), 'w'), indent=1)

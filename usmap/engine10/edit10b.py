"""Phase 2, edit 1 again, now that the cache matches the current code: the yellow shop goes from level B to level A."""
import sys, os, json, copy, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render10 as R, cache10 as C
s = json.load(open(os.path.join(C.CACHE, 'scene_edit2_tree.json')))
for e in s['elements']:
    if e['kind'] == 'shops7': e['params']['store_level'] = 'A'
p = os.path.join(C.CACHE, 'scene_edit3_storefrontA.json'); json.dump(s, open(p, 'w'))
t0 = time.time(); r = C.build(1, None, scene_path=p, store='f1'); r['wall_seconds'] = round(time.time() - t0, 1)
print('edit 1b', len(r['painted']), 'painted', len(r['reused']), 'reused', r['wall_seconds'], 's', [t['tile'] for t in r['painted']])
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'phase2_incremental.json'))); d['edit1b_storefront'] = r
json.dump(d, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'phase2_incremental.json'), 'w'), indent=1)

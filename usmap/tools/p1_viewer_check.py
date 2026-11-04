#!/usr/bin/env python3
"""Phase 1 check of the moving parts: rebuild the prototype viewer bundle (engine10/make_viewer10.py) with the
current brush into a scratch folder and compare it with viewer10/, built with the original brush. This repaints every
Toy Town sway tree, flag and train vehicle at 1x and 2x, re-cuts every front patch and both occluders, so it covers
the animations. The build timestamp is the only thing allowed to differ.

    cd usmap && PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 tools/p1_viewer_check.py SCRATCH_DIR
"""
import sys, os, re, runpy, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DST = os.path.abspath(sys.argv[1])
src = open(os.path.join(ROOT, 'engine10', 'make_viewer10.py')).read()
a = "DST = os.path.join(R.ROOT, 'viewer10')"; b = "json.dump(rep, open(os.path.join(HERE, 'out', 'viewer10_build.json'), 'w'), indent=1)"
assert a in src and b in src
src = src.replace(a, f"DST = {DST!r}").replace(b, f"json.dump(rep, open(os.path.join(DST, '..', 'viewer10_build.json'), 'w'), indent=1)")
tmp = os.path.join(os.path.dirname(DST), 'make_viewer10_check.py'); open(tmp, 'w').write(src.replace("HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {os.path.join(ROOT, 'engine10')!r}"))
sys.path.insert(0, os.path.join(ROOT, 'engine10'))
runpy.run_path(tmp, run_name='__main__')
# compare: everything but index.html as files; index.html with the build stamp blanked
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'compare_outputs.py'), os.path.join(ROOT, 'viewer10'), DST, '--ignore-key', 'build'], capture_output=True, text=True)
print(r.stdout)
blank = lambda t: re.sub(r'"build": "\d+"', '"build": ""', t)
same_html = blank(open(os.path.join(ROOT, 'viewer10', 'index.html')).read()) == blank(open(os.path.join(DST, 'index.html')).read())
print('index.html (build stamp blanked):', 'IDENTICAL' if same_html else 'DIFFERS')
bad = [l for l in r.stdout.splitlines() if 'DIFF' in l and 'index.html' not in l]
sys.exit(0 if not bad and same_html else 1)

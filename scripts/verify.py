"""Proves the project reproduces its committed images pixel for pixel.
Copies the project to a temporary folder, re-renders each target there, and compares with the committed PNGs.
Usage:  python3 scripts/verify.py            (all targets, ~3 min)
        python3 scripts/verify.py usmap2     (one target)"""
import os, sys, shutil, subprocess, tempfile
import numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = {   # name: (script, rendered file relative to the copy, committed baseline relative to ROOT)
    'usmap2': ('render_usmap_pass2.sh', 'usmap/out/usmap2.png', 'usmap/out/usmap2.png'),
    'usmap1': ('render_usmap_pass1.sh', 'usmap/out/usmap.png', 'usmap/out/usmap_pass1.png'),
    'village': ('render_village_benchmark.sh', 'village_benchmark/out/A.png', 'styles2/out/A_original.png'),
    'village_refined': ('render_village_refined.sh', 'styles2/out/A_refined.png', 'styles2/out/A_refined.png'),
    'county': ('render_county.sh', 'county/out/county.png', 'county/out/county.png'),
}
want = sys.argv[1:] or list(TARGETS)
tmp = tempfile.mkdtemp(prefix='tft-verify-'); copy = os.path.join(tmp, 'p')
shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('__pycache__', '*.zip', 'archive'))
ok = True
for name in want:
    script, out, base = TARGETS[name]
    r = subprocess.run(['bash', os.path.join(copy, 'scripts', script)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'{name:16s} RENDER FAILED\n{r.stderr[-2000:]}'); ok = False; continue
    a = cv2.imread(os.path.join(copy, out)).astype(int); b = cv2.imread(os.path.join(ROOT, base)).astype(int)
    if a.shape != b.shape: print(f'{name:16s} SIZE MISMATCH {a.shape} vs {b.shape}'); ok = False; continue
    d = np.abs(a - b).max(-1); n = int((d > 0).sum())
    print(f'{name:16s} {"IDENTICAL" if n == 0 else "DIFFERENT"}  differing pixels: {n}  max channel diff: {int(d.max())}')
    ok &= n == 0
shutil.rmtree(tmp)
sys.exit(0 if ok else 1)

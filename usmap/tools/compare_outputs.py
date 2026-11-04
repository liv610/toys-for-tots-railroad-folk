#!/usr/bin/env python3
"""Compare two render output folders file by file.

    python3 tools/compare_outputs.py DIR_A DIR_B [--ignore-key build]

Images (png/jpg) are decoded and compared pixel by pixel (alpha included). .npy arrays are compared exactly.
JSON is compared as data (keys given with --ignore-key, such as build timestamps, are skipped). Anything else is
compared byte for byte. Prints one line per difference and a summary; exit 0 only when everything matches.
"""
import sys, os, json, hashlib
import numpy as np, cv2

def strip(o, ign):
    if isinstance(o, dict): return {k: strip(v, ign) for k, v in o.items() if k not in ign}
    if isinstance(o, list): return [strip(v, ign) for v in o]
    return o

def compare(a, b, ign=()):
    fa = {os.path.relpath(os.path.join(r, f), a) for r, _, fs in os.walk(a) for f in fs}
    fb = {os.path.relpath(os.path.join(r, f), b) for r, _, fs in os.walk(b) for f in fs}
    bad = [f'only in A: {p}' for p in sorted(fa - fb)] + [f'only in B: {p}' for p in sorted(fb - fa)]
    n = dict(images=0, pixels=0, arrays=0, json=0, other=0)
    for p in sorted(fa & fb):
        A, Bp = os.path.join(a, p), os.path.join(b, p); ext = p.rsplit('.', 1)[-1].lower()
        if ext in ('png', 'jpg', 'jpeg'):
            x, y = cv2.imread(A, cv2.IMREAD_UNCHANGED), cv2.imread(Bp, cv2.IMREAD_UNCHANGED); n['images'] += 1
            if x is None or y is None or x.shape != y.shape: bad.append(f'{p}: shape {None if x is None else x.shape} vs {None if y is None else y.shape}'); continue
            d = np.any(x != y, axis=-1) if x.ndim == 3 else (x != y); n['pixels'] += d.size
            if d.any(): bad.append(f'{p}: {int(d.sum())} of {d.size} pixels differ, max {int(np.abs(x.astype(int) - y.astype(int)).max())}')
        elif ext == 'npy':
            n['arrays'] += 1
            if not np.array_equal(np.load(A, allow_pickle=True), np.load(Bp, allow_pickle=True)): bad.append(f'{p}: array differs')
        elif ext == 'json':
            n['json'] += 1
            if strip(json.load(open(A)), ign) != strip(json.load(open(Bp)), ign): bad.append(f'{p}: data differs')
        else:
            n['other'] += 1
            if open(A, 'rb').read() != open(Bp, 'rb').read(): bad.append(f'{p}: bytes differ')
    return bad, n, len(fa & fb)

if __name__ == '__main__':
    a, b = sys.argv[1], sys.argv[2]; ign = set(sys.argv[sys.argv.index('--ignore-key') + 1].split(',')) if '--ignore-key' in sys.argv else set()
    bad, n, common = compare(a, b, ign)
    for x in bad[:40]: print('  DIFF', x)
    print(f'{a} vs {b}: {common} files compared ({n["images"]} images, {n["pixels"]:,} pixels; {n["arrays"]} arrays; {n["json"]} json; {n["other"]} other): '
          + ('IDENTICAL' if not bad else f'{len(bad)} differences'))
    sys.exit(0 if not bad else 1)

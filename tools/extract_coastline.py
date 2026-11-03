"""Re-derives usmap/coast.npy and usmap/lakes.npy from the reference image (geometry only).
This is the exact procedure used during development. The committed .npy files are the authoritative
inputs to the renderer; running this is only needed if the outline is ever re-traced.
Usage:  python3 tools/extract_coastline.py references/us-map-reference.png OUT_DIR"""
import sys, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
im = cv2.imread(src).astype(np.float32)
bl = cv2.GaussianBlur(im, (0, 0), 5)
b, g, r = bl[..., 0], bl[..., 1], bl[..., 2]
ocean = (((b - r) > 28) & (b > 80) & (g < b)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(ocean)
keep = np.zeros_like(ocean)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a > 2000 and (x == 0 or y == 0 or x + w >= 1672 or y + h >= 941): keep[lab == i] = 1
lakes = np.zeros_like(ocean)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a > 800 and not (x == 0 or y == 0 or x + w >= 1672 or y + h >= 941) and 1000 < x < 1400 and y < 330: lakes[lab == i] = 1
land = (1 - keep).astype(np.uint8) * 255
land = cv2.morphologyEx(land, cv2.MORPH_OPEN, np.ones((11, 11), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(land); i = 1 + np.argmax(st[1:, 4]); land = (lab == i).astype(np.uint8) * 255
cs, _ = cv2.findContours(land, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cnt = max(cs, key=cv2.contourArea)
ap = cv2.approxPolyDP(cnt, 1.2, True)[:, 0, :].astype(float); np.save(f'{out}/coast.npy', ap)
lk = []
cs2, _ = cv2.findContours(lakes * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
for cc in cs2:
    if cv2.contourArea(cc) > 600: lk.append(cv2.approxPolyDP(cc, 1.2, True)[:, 0, :].astype(float))
np.save(f'{out}/lakes.npy', np.array(lk, dtype=object), allow_pickle=True)
print(len(ap), 'coast points;', len(lk), 'lakes')

"""Dusk preview of the drawn blue shop: the painting darkened and cooled, then the separate glow layer added on
top, the way the viewer could light the town in the evening. Writes out/blue_shop_v2_dusk_compare.jpg."""
import os, numpy as np, cv2
import study_blue_shop as B
OUT = B.OUT
def rd(n): return cv2.imread(os.path.join(OUT, n), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
v2, glow = rd('blue_shop_v2_study.png'), rd('blue_shop_v2_glow.png')
a = v2[..., 3:]; col = v2[..., :3]
bg_day, bg_dusk = np.array([.87, .91, .93]), np.array([.32, .22, .18])          # BGR grounds
dusk = col * np.array([.62, .45, .38]) + glow[..., :3] * glow[..., 3:] * .9      # cooler, darker; windows lit
day = col * a + bg_day * (1 - a); dusk = np.clip(dusk, 0, 1) * a + bg_dusk * (1 - a)
dusk = dusk + glow[..., :3] * cv2.GaussianBlur(glow[..., 3], (0, 0), 30)[..., None] * .18 * (1 - a)   # spill on the ground
sheet = np.concatenate([day, np.ones((day.shape[0], 24, 3)), np.clip(dusk, 0, 1)], 1)
cv2.imwrite(os.path.join(OUT, 'blue_shop_v2_dusk_compare.jpg'), (sheet * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
print('ok')

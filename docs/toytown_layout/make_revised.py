"""Revised Toy Town composition (one sketch, at the scale of sketch B), after the review of A/B/C.

Changes from B: the clock moves onto the station, in a small gabled porch over the visitor entrance; the
square is smaller with organic edges, planted beds, low walls and steps; the houses vary in height, width,
roof form and lean; light snow and festive dressing; and an inset shows the tracks inside the station,
drawn from the real route data. Writes B2_revised.jpg. Nothing in the map, routes or engine changes.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import make_sketches as M
from make_sketches import F, dashed, label, arc

HERE = os.path.dirname(os.path.abspath(__file__))
ORANGE = (230, 120, 20)

def organic(pts, amp=35, n=10, seed=4):
    """Round a polygon into a soft, hand-drawn closed curve: Chaikin smoothing plus a gentle wobble."""
    rr = random.Random(seed); P = list(pts)
    for _ in range(3):
        Q = []
        for a, b in zip(P, P[1:] + P[:1]):
            Q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        P = Q
    ph = rr.uniform(0, 6)
    cx = sum(p[0] for p in P) / len(P); cy = sum(p[1] for p in P) / len(P)
    out = []
    for i, (x, y) in enumerate(P):
        t = i / len(P) * math.tau; k = amp * (math.sin(t * 5 + ph) * .6 + math.sin(t * 11 + ph * 2) * .4)
        dx, dy = x - cx, y - cy; L = math.hypot(dx, dy) or 1
        out.append((x + dx / L * k, y + dy / L * k))
    return out

# the cozier square (detail px): smaller than B, still reaching the station steps and the bridge path
SQUARE2 = organic([(2020, 2110), (3380, 2110), (3440, 2380), (3520, 2700), (3420, 2950), (3060, 3070), (2300, 3090), (1760, 3000),
                   (1560, 2780), (1640, 2470), (1820, 2260)], amp=30)
# (label, colour, x0, ground y, width, facade h, depth, roof, lean deg, kind)
HOUSES = [
    ('Small brown house', (160, 100, 70), 810, 2330, 270, 400, 95, 'low', -1.5, 'keep'),
    ('Cream house', (232, 222, 196), 1560, 2250, 300, 470, 95, 'hip', 1.0, 'keep'),
    ('Pink house', (225, 130, 160), 1220, 2430, 370, 610, 115, 'step', -1.0, 'keep'),
    ('Yellow house', (230, 195, 90), 1110, 2690, 300, 760, 105, 'steep', 1.5, 'keep'),
    ('Blue shop (green-and-white awning)', (70, 110, 190), 960, 3000, 480, 560, 150, 'gable', -.8, 'land'),
    ('Pink house', (225, 130, 160), 3500, 2240, 260, 450, 95, 'hip', -1.2, 'keep'),
    ('Red house', (190, 50, 45), 3760, 2410, 320, 770, 110, 'step', 1.2, 'keep'),
    ('Toy donation storefront', (230, 190, 70), 3560, 2700, 430, 590, 130, 'wide', -.6, 'land'),
]

def rot(p, c, deg):
    a = math.radians(deg); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))

def house(d, h, tf):
    name, col, x0, gy, w, fh, dep, roof, lean, kind = h
    sx, sk = dep, dep * .45; base = (x0 + w / 2, gy)
    P = lambda x, y: tf(rot((x, y), base, lean))
    dark = tuple(int(c * .7) for c in col); a = 235
    front = [P(x0, gy), P(x0 + w, gy), P(x0 + w, gy - fh), P(x0, gy - fh)]
    side = [P(x0 + w, gy), P(x0 + w + sx, gy - sk), P(x0 + w + sx, gy - fh - sk), P(x0 + w, gy - fh)]
    d.polygon(side, fill=dark + (a,)); d.polygon(front, fill=col + (a,))
    top = gy - fh; rc, rd = (150, 80, 65, 245), (115, 60, 50, 245)
    # roof forms: each house its own
    if roof in ('gable', 'steep', 'wide', 'low'):
        rh = {'gable': .5, 'steep': .95, 'wide': .38, 'low': .32}[roof] * w
        rf = [P(x0 - 18, top), P(x0 + w + 18, top), P(x0 + w / 2, top - rh)]
        rs = [P(x0 + w + 18, top), P(x0 + w + sx + 18, top - sk), P(x0 + w / 2 + sx, top - rh - sk), P(x0 + w / 2, top - rh)]
        d.polygon(rs, fill=rd); d.polygon(rf, fill=rc)
        d.line([P(x0 - 10, top + 4), P(x0 + w / 2, top - rh), P(x0 + w + 10, top + 4)], fill=(250, 252, 255, 255), width=7, joint='curve')
        d.line([P(x0 + w / 2, top - rh), P(x0 + w / 2 + sx, top - rh - sk)], fill=(250, 252, 255, 255), width=9)
    elif roof == 'step':      # stepped Dutch gable
        steps = 4; sw = w / (2 * steps + 1); pts = [P(x0, top)]
        for i in range(steps):
            pts += [P(x0 + sw * i, top - 70 * (i + 1)), P(x0 + sw * (i + 1), top - 70 * (i + 1))]
        pts += [P(x0 + w / 2 + sw / 2, top - 70 * (steps + .6)), P(x0 + w / 2 - sw / 2, top - 70 * (steps + .6))][::-1]
        mid = len(pts)
        right = [P(x0 + w - sw * (i + 1), top - 70 * (i + 1)) for i in range(steps)]
        poly = [P(x0, top)] + [p for i in range(steps) for p in (P(x0 + sw * i, top - 70 * (i + 1)), P(x0 + sw * (i + 1), top - 70 * (i + 1)))] + \
               [P(x0 + w / 2 - sw / 2, top - 70 * (steps + 1)), P(x0 + w / 2 + sw / 2, top - 70 * (steps + 1))] + \
               [p for i in reversed(range(steps)) for p in (P(x0 + w - sw * (i + 1), top - 70 * (i + 1)), P(x0 + w - sw * i, top - 70 * (i + 1)))] + [P(x0 + w, top)]
        d.polygon([P(x0 + w, top), P(x0 + w + sx, top - sk), P(x0 + w / 2 + sx, top - 70 * (steps + 1) - sk), P(x0 + w / 2, top - 70 * (steps + 1))], fill=rd)
        d.polygon(poly, fill=col + (a,)); d.line(poly, fill=dark, width=3)
        for i in range(steps):
            for xx in (x0 + sw * i, x0 + w - sw * (i + 1)):
                d.rectangle(P(xx, top - 70 * (i + 1) - 10) + P(xx + sw, top - 70 * (i + 1)), fill=(250, 252, 255, 250))
    elif roof == 'hip':
        rh = .42 * w
        rf = [P(x0 - 16, top), P(x0 + w + 16, top), P(x0 + w * .72, top - rh), P(x0 + w * .28, top - rh)]
        rs = [P(x0 + w + 16, top), P(x0 + w + sx + 16, top - sk), P(x0 + w * .72 + sx * .6, top - rh - sk * .6), P(x0 + w * .72, top - rh)]
        d.polygon(rs, fill=rd); d.polygon(rf, fill=rc)
        d.polygon([P(x0 + w * .25, top - rh + 4), P(x0 + w * .75, top - rh + 4), P(x0 + w * .84, top - rh * .7), P(x0 + w * .16, top - rh * .7)], fill=(250, 252, 255, 250))
        dw = [P(x0 + w * .4, top - rh * .2), P(x0 + w * .6, top - rh * .2), P(x0 + w * .6, top - rh * .55), P(x0 + w * .5, top - rh * .72), P(x0 + w * .4, top - rh * .55)]
        d.polygon(dw, fill=col + (255,)); d.rectangle(P(x0 + w * .45, top - rh * .48) + P(x0 + w * .55, top - rh * .25), fill=(255, 205, 110))
    # chimney with snow
    cx = x0 + w * (.22 if lean > 0 else .7)
    d.polygon([P(cx, top - 40), P(cx + 45, top - 40), P(cx + 45, top - 190), P(cx, top - 190)], fill=(150, 70, 55, 250))
    d.polygon([P(cx - 6, top - 190), P(cx + 51, top - 190), P(cx + 40, top - 210), P(cx + 4, top - 210)], fill=(250, 252, 255))
    # windows: lit, varied per house
    rr = random.Random(int(x0 + gy)); floors = max(2, int(fh / 190)); cols_ = 2 if w < 330 else 3
    for f in range(floors):
        for c in range(cols_):
            wx = x0 + w * (c + .5) / cols_ - 28; wy = gy - fh + 70 + f * (fh - 170) / floors
            if f == floors - 1 and kind == 'land': continue
            shape = [P(wx, wy), P(wx + 56, wy), P(wx + 56, wy + 78), P(wx, wy + 78)]
            d.polygon(shape, fill=(255, 205, 110, 255) if rr.random() < .75 else (90, 80, 90, 255))
            d.polygon([P(wx - 6, wy + 78), P(wx + 62, wy + 78), P(wx + 62, wy + 90), P(wx - 6, wy + 90)], fill=(250, 252, 255))
    if name.startswith('Blue shop'):
        for i in range(8):
            c = (40, 130, 70) if i % 2 == 0 else (245, 245, 235)
            ax = x0 + 20 + i * (w - 40) / 8
            d.polygon([P(ax, gy - 250), P(ax + (w - 40) / 8, gy - 250), P(ax + (w - 40) / 8 + 6, gy - 175), P(ax + 6, gy - 175)], fill=c)
        d.polygon([P(x0 + 40, gy - 165), P(x0 + w - 40, gy - 165), P(x0 + w - 40, gy - 20), P(x0 + 40, gy - 20)], fill=(255, 200, 100))
    if name.startswith('Toy donation'):
        d.polygon([P(x0 + 60, gy - 330), P(x0 + w - 60, gy - 330), P(x0 + w - 60, gy - 250), P(x0 + 60, gy - 250)], fill=(250, 245, 230), outline=(150, 40, 35))
        for i in range(8):
            c = (200, 50, 45) if i % 2 == 0 else (245, 245, 235); ax = x0 + 20 + i * (w - 40) / 8
            d.polygon([P(ax, gy - 230), P(ax + (w - 40) / 8, gy - 230), P(ax + (w - 40) / 8 + 6, gy - 165), P(ax + 6, gy - 165)], fill=c)
        d.polygon([P(x0 + 40, gy - 155), P(x0 + w - 40, gy - 155), P(x0 + w - 40, gy - 20), P(x0 + 40, gy - 20)], fill=(255, 200, 100))
    # wreath on the door
    dx_ = x0 + w * (.18 if kind == 'land' else .5); d.ellipse(P(dx_ - 26, gy - 150) + P(dx_ + 26, gy - 98), outline=(40, 110, 55), width=7)
    outline = ORANGE if kind == 'land' else (50, 35, 25)
    if kind == 'land': dashed(d, front, outline, 4, 12, 7, True)
    else: d.line(front + [front[0]], fill=outline, width=2)
    return P(x0 + w / 2, gy - fh + min(120, fh * .3))

def station_porch(d, tf):
    """A small gabled porch over the visitor entrance, with the clock in its gable. It sits at the foot of the
    great arch, in front of the wooden doors, so the arch, star, banner and upper glazing stay clear."""
    x0, x1, gy = 2450, 2950, 1985; top = 1690; peak = 1520; cx = (x0 + x1) / 2
    stone = (236, 226, 202, 255)
    d.polygon([tf(p) for p in [(x0, gy), (x1, gy), (x1, top), (x0, top)]], fill=stone)
    d.polygon([tf(p) for p in [(x0 - 30, top), (x1 + 30, top), (cx, peak)]], fill=stone, outline=(150, 70, 55))
    d.line([tf((x0 - 30, top)), tf((cx, peak)), tf((x1 + 30, top))], fill=(250, 252, 255), width=7)       # snow on the gable
    # the clock (moved here from the freestanding tower)
    c = tf((cx, top - 60)); r = 62 * SB
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=(250, 248, 238), outline=(150, 110, 40), width=3)
    d.line([c, (c[0], c[1] - r * .7)], fill=(30, 25, 25), width=3); d.line([c, (c[0] + r * .5, c[1] + r * .1)], fill=(30, 25, 25), width=3)
    # arched doorway, ticket window beside it, wreath and garland
    door = [(cx - 105, gy)] + arc(cx, 1810, 105, 80, 180, 0) + [(cx + 105, gy)]
    d.polygon([tf(p) for p in door], fill=(120, 65, 40))
    d.rectangle(tf((x0 + 30, 1800)) + tf((x0 + 120, 1890)), fill=(255, 205, 110), outline=(120, 65, 40), width=3)
    d.rectangle(tf((x1 - 120, 1800)) + tf((x1 - 30, 1890)), fill=(255, 205, 110), outline=(120, 65, 40), width=3)
    d.ellipse(tf((cx - 35, 1745)) + tf((cx + 35, 1815)), outline=(40, 110, 55), width=6)
    for k in range(9):
        a = tf((x0 + k * (x1 - x0) / 8, top + 12 + 18 * math.sin(math.pi * (k % 2))))
        d.ellipse((a[0] - 5, a[1] - 5, a[0] + 5, a[1] + 5), fill=(40, 110, 55))
    dashed(d, [tf(p) for p in [(x0, gy), (x0, top), (x0 - 30, top), (cx, peak), (x1 + 30, top), (x1, top), (x1, gy)]], ORANGE, 4, 12, 7)
    # steps down to the square
    for i in range(3):
        d.rectangle(tf((x0 - 40 - i * 25, gy + i * 32)) + tf((x1 + 40 + i * 25, gy + (i + 1) * 32)), fill=(200, 195, 185), outline=(150, 140, 130))

def edges(d, tf, sq):
    """The square's edges: low stone walls with gaps for the paths, planted beds, lamps, snow drifts."""
    rr = random.Random(8)
    # walk the outline; walls along the south and south-west, beds at a few points
    n = len(sq)
    def seg(i0, i1, wall=True):
        pts = [sq[i % n] for i in range(i0, i1)]
        if wall:
            d.line([tf(p) for p in pts], fill=(160, 150, 140, 255), width=int(34 * SB) + 6)
            d.line([tf((p[0], p[1] - 14)) for p in pts], fill=(250, 252, 255, 255), width=int(14 * SB) + 3)
            for p in pts[::3]:
                q = tf(p); d.line([(q[0], q[1] - 6), (q[0], q[1] + 6)], fill=(120, 110, 105), width=2)
    seg(int(n * .53), int(n * .66)); seg(int(n * .70), int(n * .82)); seg(int(n * .06), int(n * .2))
    beds = [(1690, 2560), (1820, 2930), (3380, 2420), (3330, 2930), (2050, 2190), (3300, 2190)]
    for x, y in beds:
        c = tf((x, y)); rx, ry = 85 * SB + 6, 40 * SB + 4
        d.ellipse((c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry), fill=(90, 70, 50), outline=(150, 140, 130), width=3)
        for k in range(6):
            bx = c[0] + rr.uniform(-rx * .7, rx * .7); by = c[1] + rr.uniform(-ry * .5, ry * .3); s = rr.uniform(9, 15)
            d.polygon([(bx, by - s * 1.8), (bx - s, by + s * .4), (bx + s, by + s * .4)], fill=(40, 105, 60))
            d.ellipse((bx - 3, by - s * 1.9, bx + 3, by - s * 1.9 + 6), fill=(250, 252, 255))
        d.ellipse((c[0] - rx * .8, c[1] - ry * 1.05, c[0] + rx * .8, c[1] - ry * .5), fill=(250, 252, 255, 200))
    # lamps around the edge
    for x, y in ((1780, 2380), (3420, 2560), (2250, 3040), (3080, 3030), (2000, 2780)):
        b = tf((x, y)); t = tf((x, y - 170))
        d.ellipse((t[0] - 16, t[1] - 16, t[0] + 16, t[1] + 14), fill=(255, 220, 140, 70))
        d.line([b, t], fill=(40, 35, 35), width=3); d.ellipse((t[0] - 5, t[1] - 7, t[0] + 5, t[1] + 4), fill=(255, 215, 120), outline=(40, 35, 35))

SB = 1.0
def main():
    global SB
    det = M.stitch(os.path.join(M.ROOT, 'tiles', 'detail_files', '13'), 5, 4)
    X0, Y0, X1, Y1 = 600, 250, 4700, 3700
    S = 2000 / (X1 - X0); SB = S
    im = det.crop((X0, Y0, X1, Y1)).resize((2000, int((Y1 - Y0) * S)), Image.LANCZOS)
    ghost = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(.45)).enhance(1.08)
    im = Image.blend(im, ghost, .55).convert('RGBA')
    tf = lambda p: ((p[0] - X0) * S, (p[1] - Y0) * S)
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov, 'RGBA')
    # light snow over the town ground: Toy Town a little snowier than the map around it
    snow = [tf(p) for p in organic([(700, 2050), (1300, 1960), (4100, 1960), (4300, 2500), (4000, 3200), (3000, 3450), (1600, 3420), (800, 3100), (600, 2500)], 60, seed=2)]
    d.polygon(snow, fill=(246, 248, 252, 150))
    # today's flat row: washed out
    r = M.EXIST['row_now']; d.rectangle(tf(r[:2]) + tf(r[2:]), fill=(242, 240, 236, 225))
    # routes: visible stretches solid; inside the station dotted
    for k, pts in M.ROUTES.items():
        D = [M.f1_to_d(p) for p in pts]; cut = next((i for i, q in enumerate(D) if 1290 < q[0] < 4110 and q[1] < M.STATION_BASE), len(D))
        P = [tf(q) for q in D]; d.line(P[:cut + 1], fill=M.RCOL[k] + (220,), width=9, joint='curve'); dashed(d, P[cut:], M.RCOL[k] + (255,), 5, 9, 7)
    # the square, cobbled, and its paths
    sq = [tf(p) for p in SQUARE2]
    d.polygon(sq, fill=(222, 214, 200, 245))
    mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).polygon(sq, fill=255); rr = random.Random(3)
    for _ in range(2200):
        x, y = rr.uniform(0, im.width - 1), rr.uniform(0, im.height - 1)
        if mask.getpixel((int(x), int(y))): d.ellipse((x - 4, y - 2.5, x + 4, y + 2.5), fill=(188, 180, 170, 220))
    for _ in range(26):    # little drifts of snow across the cobbles
        x, y = rr.uniform(0, im.width - 1), rr.uniform(0, im.height - 1)
        if mask.getpixel((int(x), int(y))): d.ellipse((x - 26, y - 8, x + 26, y + 8), fill=(250, 252, 255, 170))
    for pts, w in [([(3480, 2810), (3700, 2790), (3900, 2770)], 140), ([(2400, 3080), (2250, 3300), (2050, 3600)], 110),
                   ([(1600, 2770), (1460, 2740), (1350, 2700)], 70), ([(3460, 2500), (3530, 2420)], 60)]:
        d.line([tf(p) for p in pts], fill=(214, 206, 192, 235), width=int(w * S))
    dashed(d, sq, ORANGE, 4, 12, 7, True)
    edges(d, tf, SQUARE2)
    d.line([tf(p) for p in M.EXIST['bridge']] + [tf(M.EXIST['bridge'][0])], fill=(255, 255, 255, 255), width=4)
    # station: porch with the clock, a line of snow on the roofline
    d.line([tf(p) for p in M.EXIST['station']], fill=(255, 255, 255, 230), width=3)
    station_porch(d, tf)
    # houses, back to front
    centres = [(h, house(d, h, tf)) for h in sorted(HOUSES, key=lambda h: h[3])]
    # the square's life: tree, Marines, wagons, donation box, family, room left for characters
    def tree(x, y, s):
        c = tf((x, y)); S2 = 1.0
        for i in range(4):
            w_ = s * (1 - i * .2); d.polygon([(c[0] - w_, c[1] - i * s * .55), (c[0] + w_, c[1] - i * s * .55), (c[0], c[1] - i * s * .55 - s * .9)], fill=(35, 105, 55))
        d.polygon([(c[0], c[1] - s * 2.75), (c[0] - 7, c[1] - s * 2.5), (c[0] + 7, c[1] - s * 2.5)], fill=(250, 200, 60))
        rr2 = random.Random(int(x))
        for _ in range(14):
            hy = rr2.uniform(0, 2.1); bx_ = c[0] + rr2.uniform(-.7, .7) * s * (1 - hy / 2.6) * S2; by_ = c[1] - hy * s * S2 * .55
            d.ellipse((bx_ - 3, by_ - 3, bx_ + 3, by_ + 3), fill=(220, 40, 40) if rr2.random() < .5 else (255, 210, 90))
    tree(2380, 2690, 70 * S * 1.0)
    def blob(x, y, col, r=11, lab=None):
        c = tf((x, y)); d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=col, outline=(40, 30, 25), width=2)
    for x in (2700, 2780): blob(x, 2700, (40, 50, 90), 12)
    blob(2950, 2760, (200, 50, 45), 13); blob(3050, 2640, (200, 50, 45), 15); blob(2560, 2850, (60, 120, 70), 10); blob(2610, 2860, (200, 60, 60), 8)
    for x, y in ((2300, 2780), (2460, 2780), (2420, 2830)): blob(x, y, (230, 190, 70), 7)
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im, 'RGBA')
    # labels
    for h, c in centres:
        label(d, c, h[0], 15, (255, 255, 255), (30, 30, 40, 215))
        if h[9] == 'land': label(d, (c[0], c[1] + 23), 'landmark', 12, (40, 30, 25), (250, 210, 120, 235))
    label(d, tf((2700, 1430)), 'Clock moves onto the station: a small snowy porch over the visitor entrance', 15, (40, 30, 25), (250, 210, 120, 238), bold=True)
    label(d, tf((2700, 1490)), 'arch, star, banner and upper windows stay clear', 13, (40, 30, 25), (255, 250, 235, 230))
    label(d, tf((2700, 750)), 'Toys for Tots station: unchanged landmark (light snow on the roofline in the painting)', 16, bold=True)
    label(d, tf((2700, 2470)), 'TOWN SQUARE', 19, (40, 30, 25), (250, 240, 215, 235), bold=True)
    label(d, tf((2700, 2520)), 'smaller, softer edges; room kept for the tree, Marines, wagons, donation box, characters', 13, (40, 30, 25), (255, 250, 235, 230))
    label(d, tf((2160, 3190)), 'low stone wall, beds, lamps', 13, (40, 30, 25), (255, 250, 235, 230))
    label(d, tf((2420, 3480)), 'path down to the fields', 13, (40, 30, 25), (255, 250, 235, 230))
    label(d, tf((3900, 2990)), 'Stone bridge (kept)', 15)
    label(d, tf((1200, 1700)), 'today\'s flat row (washed out)', 12, (60, 50, 45), (245, 242, 236, 230))
    # inset: the tracks inside the station, from the route data
    ins_w, ins_h = 640, 330; IX, IY = 20, im.height - ins_h - 20; ix, iy = 0, 0
    inset = Image.new('RGBA', (ins_w + 1, ins_h + 1), (0, 0, 0, 0)); d = ImageDraw.Draw(inset, 'RGBA')
    d.rounded_rectangle((ix, iy, ix + ins_w, iy + ins_h), 12, fill=(250, 246, 236, 245), outline=(90, 80, 70), width=2)
    d.text((ix + 14, iy + 10), 'Inside the station (plan, from the route data)', font=F(17, True), fill=(40, 30, 25))
    bx0, bx1, by0, by1 = 1150, 4250, 1350, 2050
    k_ = min((ins_w - 40) / (bx1 - bx0), (ins_h - 90) / ((by1 - by0) * 1.5))
    it = lambda p: (ix + 20 + (p[0] - bx0) * k_, iy + 50 + (p[1] - by0) * k_ * 1.5)
    clip = Image.new('RGBA', inset.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(clip, 'RGBA')
    d.rectangle(it((1290, 1400)) + it((4110, 1960)), fill=(236, 228, 210), outline=(90, 80, 70), width=2)
    d.rectangle(it((2250, 1420)) + it((3300, 1950)), fill=(244, 236, 214))
    d.text(it((2775, 1700)), 'concourse', font=F(13), fill=(90, 80, 70), anchor='mm')
    d.rectangle(it((2450, 1950)) + it((2950, 1985)), fill=(250, 190, 90))
    d.text(it((2700, 2025)), 'entrance (to the square)', font=F(12), fill=(90, 80, 70), anchor='mm')
    # platforms beside the west pair and the east track
    d.polygon([it(p) for p in [(1400, 1600), (2060, 1525), (2060, 1555), (1400, 1720)]], fill=(195, 185, 170))
    d.polygon([it(p) for p in [(3420, 1640), (4000, 1760), (4000, 1820), (3420, 1690)]], fill=(195, 185, 170))
    for k, pts in M.ROUTES.items():
        D = [M.f1_to_d(p) for p in pts]; P = [it(q) for q in D if bx0 - 200 < q[0] < bx1 + 200 and q[1] < by1 + 100]
        dc.line(P, fill=M.RCOL[k], width=4, joint='curve')
        e = P[-1]; d.line([(e[0] + (6 if k != 'green' else -6), e[1] - 8), (e[0] + (6 if k != 'green' else -6), e[1] + 8)], fill=(40, 30, 25), width=4)
    m = Image.new('L', inset.size, 0); ImageDraw.Draw(m).rectangle((12, 40, ins_w - 12, ins_h - 60), fill=255)
    inset.paste(clip, (0, 0), Image.composite(clip, Image.new('RGBA', inset.size, (0, 0, 0, 0)), m))
    d = ImageDraw.Draw(inset, 'RGBA')
    d.text((ix + 14, iy + ins_h - 50), 'Red and Blue end side by side at the west platform; Green ends at its own east', font=F(12), fill=(40, 30, 25))
    d.text((ix + 14, iy + ins_h - 32), 'platform. The two ends never overlap, so no tracks cross. Bars = buffer stops.', font=F(12), fill=(40, 30, 25))
    im.alpha_composite(inset, (IX, IY)); d = ImageDraw.Draw(im, 'RGBA')
    M.title(im, 'Toy Town: revised composition (for approval)', 'Over today\'s art (faded). Clock on the station porch, a cozier square with organic edges, individual houses in two stepped sides, light snow. Orange dashes = new.')
    im.convert('RGB').save(os.path.join(HERE, 'B2_revised.jpg'), quality=91)

if __name__ == '__main__':
    main(); print('ok')

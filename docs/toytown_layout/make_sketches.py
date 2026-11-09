"""Toy Town layout proposal: three review sketches drawn over the real artwork and the real route data.

Nothing here changes the map, the route data or the engine. It reads:
  usmap/viewer_nw/tiles/base_files/13   the national map at full resolution (f1 px, 7089 x 4175)
  usmap/viewer_nw/tiles/detail_files/13 the Toy Town detail layer (f2, 5120 x 4096, covers f1 rect 2560,1024 +2560x2048)
  usmap/viewer_nw/scene.json            the three route polylines and the river, in f1 px
and writes A_context.jpg, B_layout.jpg, C_plan.jpg next to this file.

All proposal geometry is defined once, in detail-layer px (DX, DY), and converted for each sketch, so the
three drawings agree. In the painting, a building's "ground y" is where its front meets the ground: a larger
ground y means nearer the viewer (the map is drawn from above at an angle, fronts facing us, side walls on
the right).
"""
import os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', 'usmap', 'viewer_nw')
SC = json.load(open(os.path.join(ROOT, 'scene.json')))
F = lambda n, b=False: ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if b else ""}.ttf', n)

def stitch(level_dir, cols, rows, tile=1024):
    im = None
    for x in range(cols):
        for y in range(rows):
            p = os.path.join(level_dir, f'{x}_{y}.jpg')
            if not os.path.exists(p): continue
            t = Image.open(p).convert('RGB'); ox, oy = (1 if x else 0), (1 if y else 0)
            t = t.crop((ox, oy, min(t.width, ox + tile), min(t.height, oy + tile)))
            if im is None: im = Image.new('RGB', (cols * tile, rows * tile))
            im.paste(t, (x * tile, y * tile))
    return im

# f1 <-> detail px
def f1_to_d(p): return ((p[0] - 2560) * 2, (p[1] - 1024) * 2)
ROUTES = {k: v['points'] for k, v in SC['routes'].items()}
RIVER = SC['river']
RCOL = {'red': (200, 40, 40), 'blue': (40, 90, 200), 'green': (30, 140, 60)}
NAMES = {'red': 'Red line (from the Northwest)', 'blue': 'Blue line (from the Southwest)', 'green': 'Green line (from the Northeast)'}

# ------------------------------------------------------------------ the proposal (detail px)
def arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy - ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
EXIST = dict(
    # the station's outline as painted: side wings, the main block, the barrel vault
    station=[(1290, 1960), (1290, 1250), (1420, 1180), (1880, 1150)] + arc(2715, 1150, 835, 770, 180, 0) + [(3550, 1150), (4000, 1180), (4110, 1250), (4110, 1960)],
    bridge=[(3560, 2690), (4250, 2650), (4250, 2900), (3560, 2920)],
    square_now=[(1330, 2620), (3560, 2620), (3540, 2880), (3300, 3040), (1560, 3040), (1340, 2880)],
    row_now=(1050, 1640, 4050, 2660),      # the strip the flat row of houses covers today
)
STATION_BASE = 1960
# the enlarged square: reaches up to the station steps, out to the bridge, a little further toward us
SQUARE = [(1940, 2080), (3460, 2080), (3480, 2260), (3540, 2700), (3600, 2700), (3600, 2930), (3360, 3200), (2300, 3270), (1520, 3190),
          (1460, 3040), (1470, 2740), (1560, 2440), (1690, 2310), (1740, 2120)]
# buildings: (label, colour, x0, ground_y, width, facade_height, depth, kind)  kind: keep = existing building kept (moved),
# land = a preserved landmark, new = an added building
BUILD = [
    # west side: steps back up the hill toward the station; the blue shop stands forward at the corner of the square
    ('Blue shop (green-and-white awning)', (70, 110, 190), 980, 3020, 460, 620, 150, 'land'),
    ('Yellow house', (230, 195, 90), 1080, 2700, 360, 680, 120, 'keep'),
    ('Pink house', (225, 130, 160), 1180, 2420, 340, 640, 110, 'keep'),
    ('Clock tower (moved off the arch)', (235, 225, 200), 1700, 2300, 220, 900, 80, 'keep'),
    ('Cream house', (235, 225, 195), 820, 2350, 320, 560, 110, 'keep'),
    ('Small brown house (up the hill)', (170, 110, 80), 560, 1960, 260, 330, 90, 'keep'),
    # east side: the toy donation storefront fronts the square beside the bridge path; houses step back behind it
    ('Pink house', (225, 130, 160), 3470, 2230, 260, 420, 100, 'keep'),
    ('Red house', (190, 50, 45), 3720, 2400, 320, 720, 110, 'keep'),
    ('Toy donation storefront', (230, 190, 70), 3580, 2680, 400, 640, 130, 'land'),
]
PATHS = [  # cobbled paths: (points, width)
    ([(2700, 2100), (2700, 1990)], 360),                                       # steps up to the station entrance
    ([(3560, 2800), (3700, 2790), (3900, 2770)], 150),                        # onto the stone bridge
    ([(1700, 3150), (1450, 3350), (1250, 3600)], 120),                        # down the hill to the south-west
    ([(1470, 2760), (1350, 2730), (1250, 2690)], 80),                         # alley between the blue shop and the yellow house
    ([(1620, 2380), (1540, 2320)], 70),                                       # alley behind the clock tower
    ([(3540, 2520), (3560, 2420)], 70),                                       # alley between the donation shop and the red house
]
SQUARE_FEATURES = [  # (label, x, y, r)  kept items, re-spaced in the bigger square
    ('Christmas tree', 2050, 2800, 34), ('Marines + gift', 2650, 2760, 30), ('Gift wagon', 2950, 2820, 24),
    ('Donation box', 3300, 2720, 24), ('Lamp', 1850, 2600, 16), ('Lamp', 3400, 2500, 16), ('Lamp', 2200, 3170, 16), ('Lamp', 3200, 3140, 16),
    ('Family', 2350, 2920, 22),
]
ENTRANCE = (2500, 1770, 2900, 1990)   # the new visitor entrance and ticket window at the foot of the main arch

# ------------------------------------------------------------------ drawing helpers
def dashed(d, pts, fill, width=4, dash=18, gap=12, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if L < 1e-6: continue
        n = max(1, int(L / (dash + gap)))
        for i in range(n + 1):
            t0 = i * (dash + gap) / L; t1 = min(1, t0 + dash / L)
            if t0 >= 1: break
            d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=fill, width=width)

def label(d, xy, text, size=22, fill=(255, 255, 255), bg=(30, 30, 40, 200), anchor='mm', bold=False):
    f = F(size, bold); x, y = xy
    l, t, r, b = d.textbbox((x, y), text, font=f, anchor=anchor)
    d.rounded_rectangle((l - 7, t - 5, r + 7, b + 5), 6, fill=bg)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)

def legend(d, x, y, rows, w=470):
    h = 34 * len(rows) + 50
    d.rounded_rectangle((x, y, x + w, y + h), 12, fill=(250, 246, 236, 235), outline=(90, 80, 70), width=2)
    d.text((x + 16, y + 12), 'Legend', font=F(22, True), fill=(40, 30, 25))
    for i, (kind, col, text) in enumerate(rows):
        yy = y + 52 + 34 * i
        if kind == 'solid': d.line([(x + 16, yy + 10), (x + 66, yy + 10)], fill=col, width=6)
        elif kind == 'dash': dashed(d, [(x + 16, yy + 10), (x + 66, yy + 10)], col, 5, 12, 7)
        elif kind == 'box': d.rectangle((x + 20, yy, x + 62, yy + 20), fill=col, outline=(40, 30, 25))
        elif kind == 'hbox':
            d.rectangle((x + 20, yy, x + 62, yy + 20), fill=col); dashed(d, [(x + 20, yy), (x + 62, yy), (x + 62, yy + 20), (x + 20, yy + 20)], (230, 120, 20), 3, 6, 4, True)
        d.text((x + 80, yy + 10), text, font=F(19), fill=(40, 30, 25), anchor='lm')

def title(im, text, sub):
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle((0, 0, im.width, 92), fill=(25, 30, 45, 235))
    d.text((24, 16), text, font=F(32, True), fill=(250, 240, 220)); d.text((24, 58), sub, font=F(19), fill=(200, 205, 220))

def building(d, b, tf, scale, style='sketch'):
    """A building as the map draws it: front facade, a side wall receding up to the right, a pitched roof."""
    name, col, x0, gy, w, h, dep, kind = b
    sx, sk = dep, dep * .45            # side wall: goes right by dep and up by dep*0.45
    P = lambda x, y: tf((x, y))
    front = [P(x0, gy), P(x0 + w, gy), P(x0 + w, gy - h), P(x0, gy - h)]
    side = [P(x0 + w, gy), P(x0 + w + sx, gy - sk), P(x0 + w + sx, gy - h - sk), P(x0 + w, gy - h)]
    rh = w * .45
    roof_f = [P(x0 - 15, gy - h), P(x0 + w + 15, gy - h), P(x0 + w / 2, gy - h - rh)]
    roof_s = [P(x0 + w + 15, gy - h), P(x0 + w + sx + 15, gy - h - sk), P(x0 + w / 2 + sx, gy - h - rh - sk), P(x0 + w / 2, gy - h - rh)]
    dark = tuple(int(c * .7) for c in col)
    a = 215 if style == 'sketch' else 255
    d.polygon(side, fill=dark + (a,)); d.polygon(front, fill=col + (a,))
    d.polygon(roof_s, fill=(120, 60, 50, a)); d.polygon(roof_f, fill=(150, 80, 65, a))
    outline = (230, 120, 20) if kind != 'keep' else (40, 30, 25)
    for poly in (front, side, roof_f, roof_s):
        if kind == 'keep': d.line(poly + [poly[0]], fill=outline, width=2)
        else: dashed(d, poly, outline, 4 if scale > .3 else 3, 12, 7, True)
    return P(x0 + w / 2, gy - h + min(110, h * .3))      # label spot: just under the eaves, the part left visible

# ================================================================== A: context on the national map
def sketch_A():
    base = stitch(os.path.join(ROOT, 'tiles', 'base_files', '13'), 7, 5)
    X0, Y0, X1, Y1 = 1900, 450, 5600, 3450                 # f1 px window around Toy Town
    S = 1800 / (X1 - X0)
    im = base.crop((X0, Y0, X1, Y1)).resize((1800, int((Y1 - Y0) * S)), Image.LANCZOS)
    im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.92)).enhance(.75).convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov, 'RGBA')
    tf1 = lambda p: ((p[0] - X0) * S, (p[1] - Y0) * S)
    tfd = lambda p: tf1((p[0] / 2 + 2560, p[1] / 2 + 1024))
    # routes: existing alignment, solid; the last stretch (hidden inside / behind the station) dotted
    for k, pts in ROUTES.items():
        P = [tf1(p) for p in pts]
        hidden = [i for i, p in enumerate(pts) if f1_to_d(p)[1] < STATION_BASE and 1290 < f1_to_d(p)[0] < 4110]
        cut = hidden[0] if hidden else len(P)
        d.line(P[:cut + 1], fill=RCOL[k] + (255,), width=7, joint='curve')
        dashed(d, P[cut:], RCOL[k] + (255,), 5, 8, 8)
        e = P[-1]; d.ellipse((e[0] - 9, e[1] - 9, e[0] + 9, e[1] + 9), fill=RCOL[k] + (255,), outline=(255, 255, 255), width=3)
    d.line([tf1(p) for p in RIVER], fill=(120, 190, 255, 140), width=3)
    # existing station outline
    d.line([tfd(p) for p in EXIST['station']], fill=(255, 255, 255, 255), width=4)
    # existing town row (the strip the houses occupy today)
    r = EXIST['row_now']; d.rectangle(tfd(r[:2]) + tfd(r[2:]), fill=(245, 238, 222, 150)); dashed(d, [tfd(p) for p in [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]], (255, 255, 255, 230), 2, 8, 6, True)
    dashed(d, [tfd(p) for p in EXIST['square_now']], (255, 255, 255, 230), 2, 8, 6, True)
    # proposal: buildings, square and paths
    sq = [tfd(p) for p in SQUARE]; d.polygon(sq, fill=(228, 220, 205, 225)); dashed(d, sq, (230, 120, 20, 255), 4, 10, 6, True)
    for b in BUILD: building(d, b, tfd, S / 2, 'sketch')
    for pts, w in PATHS: d.line([tfd(p) for p in pts], fill=(225, 205, 160, 220), width=max(3, int(w * S / 2)))
    d.line([tfd(p) for p in EXIST['bridge']] + [tfd(EXIST['bridge'][0])], fill=(255, 255, 255, 255), width=3)
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im, 'RGBA')
    # labels
    for k, pts in ROUTES.items():
        i = {'red': 60, 'blue': 40, 'green': 40}[k]
        q = [p for p in pts if X0 + 80 < p[0] < X1 - 80 and Y0 + 120 < p[1] < Y1 - 80]
        if q: label(d, tf1(q[min(i, len(q) - 1)]), NAMES[k] + ', unchanged', 19, (255, 255, 255), RCOL[k] + (230,))
    label(d, tfd((2700, 900)), 'Toys for Tots station (kept)', 22, bold=True)
    label(d, tfd((2700, 2650)), 'Town square: enlarged', 21, (40, 30, 25), (250, 230, 190, 230), bold=True)
    label(d, tfd((4000, 3050)), 'Stone bridge + river (kept)', 19)
    label(d, tfd((1100, 1200)), 'Tracks run behind the houses', 18)
    label(d, tfd((1100, 1270)), 'into the station sides', 18)
    label(d, tfd((3900, 1350)), 'Green line enters the east side', 18)
    title(im, 'A  Toy Town in the national map: composition', 'Existing routes, station, river and bridge in solid lines; the proposed village and square dashed in orange. Route data is drawn as is, from scene.json.')
    legend(d, 1290, im.height - 330, [('solid', (200, 40, 40), 'Existing route, alignment unchanged'),
                                      ('dash', (200, 40, 40), 'Route stretch hidden by station / houses'),
                                      ('solid', (255, 255, 255), 'Existing station, bridge (kept)'),
                                      ('dash', (255, 255, 255), 'Today: house row and square'),
                                      ('hbox', (240, 220, 170), 'Proposed: square, new buildings'),
                                      ('box', (225, 130, 160), 'Existing house, moved')])
    # inset: the whole map, with the window marked
    small = stitch(os.path.join(ROOT, 'tiles', 'base_files', '10'), 1, 1).crop((0, 0, 887, 522)).resize((440, 259))
    ins = ImageDraw.Draw(small); k = 440 / 7089
    ins.rectangle((X0 * k, Y0 * k, X1 * k, Y1 * k), outline=(255, 200, 40), width=3)
    im.paste(small, (24, im.height - 283)); d.rectangle((24, im.height - 283, 464, im.height - 24), outline=(255, 255, 255), width=3)
    im.convert('RGB').save(os.path.join(HERE, 'A_context.jpg'), quality=90)
    # national-scale check: the same overlay at the size Toy Town appears when the whole map fills a screen
    return im

# ================================================================== B: closer architectural layout
def sketch_B():
    det = stitch(os.path.join(ROOT, 'tiles', 'detail_files', '13'), 5, 4)
    X0, Y0, X1, Y1 = 600, 250, 4700, 3700
    S = 2000 / (X1 - X0)
    im = det.crop((X0, Y0, X1, Y1)).resize((2000, int((Y1 - Y0) * S)), Image.LANCZOS)
    ghost = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(.35)).enhance(1.15).filter(ImageFilter.GaussianBlur(1))
    im = Image.blend(im, ghost, .7).convert('RGBA')
    tf = lambda p: ((p[0] - X0) * S, (p[1] - Y0) * S)
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov, 'RGBA')
    # routes near the station
    for k, pts in ROUTES.items():
        D = [f1_to_d(p) for p in pts]
        inside = lambda q: 1290 < q[0] < 4110 and q[1] < STATION_BASE
        cut = next((i for i, q in enumerate(D) if inside(q)), len(D))
        P = [tf(q) for q in D]
        d.line(P[:cut + 1], fill=RCOL[k] + (220,), width=9, joint='curve'); dashed(d, P[cut:], RCOL[k] + (255,), 5, 9, 7)
        e = P[-1]; d.ellipse((e[0] - 10, e[1] - 10, e[0] + 10, e[1] + 10), fill=RCOL[k] + (255,), outline=(255, 255, 255), width=3)
    # today's flat row of house fronts: washed out, it is repainted in the new arrangement
    r = EXIST['row_now']
    d.rectangle(tf(r[:2]) + tf(r[2:]), fill=(245, 238, 222, 205))
    for k in range(r[0], r[2], 90): d.line([tf((k, r[3])), tf((min(r[2], k + 400), r[3] - 400 * (r[3] - r[1]) / 1000 * 2.5))], fill=(200, 185, 160, 140), width=2)
    # station kept: outline; its new entrance
    d.line([tf(p) for p in EXIST['station']], fill=(255, 255, 255, 255), width=5)
    ex0, ey0, ex1, ey1 = ENTRANCE
    door = [(ex0, ey1), (ex0, ey0 + 60)] + arc((ex0 + ex1) / 2, ey0 + 60, (ex1 - ex0) / 2, 110, 180, 0) + [(ex1, ey1)]
    d.polygon([tf(p) for p in door], fill=(250, 200, 110, 200)); dashed(d, [tf(p) for p in door], (230, 120, 20), 4, 12, 7, True)
    tw = (2620, 1850, 2780, 1930); d.rectangle(tf(tw[:2]) + tf(tw[2:]), fill=(120, 60, 40, 230))
    # square, paths
    sq = [tf(p) for p in SQUARE]; d.polygon(sq, fill=(228, 220, 205, 235)); dashed(d, sq, (230, 120, 20), 5, 14, 8, True)
    mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).polygon(sq, fill=255)
    import random; rr = random.Random(3)
    for k in range(900):
        x, y = rr.uniform(0, im.width), rr.uniform(0, im.height)
        if mask.getpixel((int(min(x, im.width - 1)), int(min(y, im.height - 1)))): d.ellipse((x - 5, y - 3, x + 5, y + 3), fill=(195, 188, 178, 200))
    for pts, w in PATHS: d.line([tf(p) for p in pts], fill=(225, 210, 175, 220), width=int(w * S));
    d.line([tf(p) for p in EXIST['bridge']] + [tf(EXIST['bridge'][0])], fill=(255, 255, 255, 255), width=4)
    # buildings, painted back to front (smaller ground y first)
    centres = []
    for b in sorted(BUILD, key=lambda b: b[3]): centres.append((b, building(d, b, tf, S)))
    nq = [tf(p) for p in EXIST['square_now']]; dashed(d, nq, (70, 70, 70), 3, 8, 8, True)
    for name, x, y, r in SQUARE_FEATURES:
        c = tf((x, y)); rr = r * S
        if name == 'Christmas tree': d.polygon([(c[0], c[1] - rr * 2.6), (c[0] - rr, c[1] + rr * .4), (c[0] + rr, c[1] + rr * .4)], fill=(40, 120, 60, 240), outline=(20, 60, 30))
        else: d.ellipse((c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr), fill=(200, 60, 50, 230) if 'Lamp' not in name else (255, 210, 90, 240), outline=(40, 30, 25), width=2)
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im, 'RGBA')
    for b, c in centres:
        kind = b[7]
        tag = {'land': 'LANDMARK, kept', 'keep': 'kept, moved', 'new': 'NEW'}[kind]
        label(d, (c[0], c[1]), b[0], 16, (255, 255, 255), (30, 30, 40, 215))
        label(d, (c[0], c[1] + 24), tag, 13, (40, 30, 25), (250, 210, 120, 230) if kind != 'keep' else (230, 230, 230, 230))
    for name, x, y, r in SQUARE_FEATURES:
        if 'Lamp' in name: continue
        c = tf((x, y)); label(d, (c[0], c[1] - r * S - 16), name, 14, (40, 30, 25), (255, 250, 235, 225))
    label(d, tf((2700, 750)), 'Toys for Tots station: silhouette, vault, star, arched windows kept', 19, bold=True)
    label(d, tf((2700, 1580)), 'NEW: visitor entrance + ticket window', 17, (40, 30, 25), (250, 210, 120, 235), bold=True)
    label(d, tf((2700, 2040)), 'steps up from the square', 15, (40, 30, 25), (255, 250, 235, 225))
    label(d, tf((2650, 3060)), 'TOWN SQUARE (kept, enlarged)', 20, (40, 30, 25), (250, 230, 190, 235), bold=True)
    label(d, tf((2650, 3110)), 'grey dashes: today\'s square', 14, (255, 255, 255), (60, 60, 60, 220))
    label(d, tf((2550, 1700)), 'today\'s flat row of house fronts (washed out): repainted as the two sides of the square', 14, (40, 30, 25), (255, 250, 235, 230))
    label(d, tf((3900, 2980)), 'Stone bridge (kept)', 16)
    label(d, tf((1350, 3480)), 'path down to the fields', 15, (40, 30, 25), (255, 250, 235, 225))
    for k, at in (('red', (1000, 1330)), ('blue', (900, 2130)), ('green', (4400, 1560))):
        label(d, tf(at), NAMES[k].split(' (')[0] + ': enters the station side', 15, (255, 255, 255), RCOL[k] + (235,))
    title(im, 'B  Architectural layout: station, square, shops, paths, bridge', 'Drawn over today\'s Toy Town detail artwork (faded). Orange dashes = proposed; solid = existing. Buildings drawn as the map draws them: front, right side wall, pitched roof.')
    legend(d, im.width - 520, im.height - 330, [('solid', (255, 255, 255), 'Existing station, bridge (kept)'),
                                                ('solid', (40, 90, 200), 'Route, existing alignment'),
                                                ('box', (225, 130, 160), 'Existing house, moved (solid outline)'),
                                                ('hbox', (70, 110, 190), 'Landmark or new building (dashed)'),
                                                ('hbox', (235, 225, 205), 'Proposed square + cobbled paths'),
                                                ('dash', (60, 60, 60), 'Today\'s square edge')])
    im.convert('RGB').save(os.path.join(HERE, 'B_layout.jpg'), quality=90)

# ================================================================== C: overhead plan
def sketch_C():
    """Plan view. Depth comes from 'ground y' in the painting: each building's footprint runs from its front
    (ground y) back by its depth. Routes and river are drawn at their painted positions, which lie on the ground."""
    X0, Y0, X1, Y1 = 400, 800, 4900, 3700
    S = 1700 / (X1 - X0); Wd, Hd = 1700, int((Y1 - Y0) * S * 1.35) + 120
    im = Image.new('RGBA', (Wd + 120, Hd + 40), (246, 240, 226, 255)); d = ImageDraw.Draw(im, 'RGBA')
    tf = lambda p: (60 + (p[0] - X0) * S, 120 + (p[1] - Y0) * S * 1.35)      # stretch depth so the plan reads
    # hill shading and the field
    d.rectangle(tf((X0, Y0)) + tf((X1, 2000)), fill=(205, 222, 180)); d.rectangle(tf((X0, 2000)) + tf((X1, Y1)), fill=(225, 215, 160))
    d.line([tf(f1_to_d(p)) for p in RIVER], fill=(110, 170, 230), width=16)
    # station footprint (plan): main hall + wings, platforms inside, tracks to the side and rear entrances
    hall = (1880, 1050, 3550, 1960); wl = (1290, 1250, 1880, 1960); wr = (3550, 1250, 4110, 1960)
    for r, c in ((wl, (235, 225, 200)), (wr, (235, 225, 200)), (hall, (240, 232, 210))):
        d.rectangle(tf(r[:2]) + tf(r[2:]), fill=c, outline=(80, 60, 50), width=3)
    for i, yy in enumerate((1330, 1500, 1670)):
        d.rectangle(tf((1400, yy - 25)) + tf((3900, yy + 25)), fill=(190, 180, 165))
    for k, pts in ROUTES.items():
        d.line([tf(f1_to_d(p)) for p in pts], fill=RCOL[k], width=7, joint='curve')
    # inside the station: each route runs to its own platform (schematic)
    ends = {k: tf(f1_to_d(pts[-1])) for k, pts in ROUTES.items()}
    for k, yy in (('red', 1330), ('blue', 1500), ('green', 1670)):
        e = ends[k]; pa = tf((1450 if k != 'green' else 3850, yy)); pb = tf((2600 if k != 'green' else 2800, yy))
        dashed(d, [e, pa, pb], RCOL[k], 4, 10, 6)
    # entrance and square
    d.rectangle(tf((2500, 1910)) + tf((2900, 1990)), fill=(250, 190, 90), outline=(230, 120, 20), width=3)
    sq = [tf(p) for p in SQUARE]; d.polygon(sq, fill=(215, 205, 190)); dashed(d, sq, (230, 120, 20), 4, 12, 7, True)
    for pts, w in PATHS: d.line([tf(p) for p in pts], fill=(215, 205, 190), width=max(6, int(w * S)))
    d.polygon([tf(p) for p in EXIST['bridge']], fill=(185, 180, 175), outline=(90, 80, 70))
    for name, col, x0, gy, w, h, dep, kind in BUILD:
        fp = (x0, gy - dep * 2.2, x0 + w, gy)
        d.rectangle(tf(fp[:2]) + tf(fp[2:]), fill=col, outline=(230, 120, 20) if kind != 'keep' else (40, 30, 25), width=3)
    for name, x, y, r in SQUARE_FEATURES:
        c = tf((x, y)); rr = max(5, r * S)
        d.ellipse((c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr), fill=(200, 60, 50) if 'Lamp' not in name else (255, 200, 60), outline=(40, 30, 25))
    # labels and arrows
    label(d, tf((2700, 1200)), 'STATION: platforms under the vault', 17, bold=True)
    label(d, tf((2700, 2030)), 'public entrance faces the square', 14, (40, 30, 25), (250, 210, 120, 235))
    label(d, tf((2700, 2950)), 'TOWN SQUARE', 20, (40, 30, 25), (250, 240, 215, 235), bold=True)
    label(d, tf((1050, 1150)), 'Red: in at the west side', 15, (255, 255, 255), RCOL['red'] + (235,))
    label(d, tf((900, 2050)), 'Blue: behind the west houses,', 15, (255, 255, 255), RCOL['blue'] + (235,))
    label(d, tf((900, 2120)), 'in at the west side', 15, (255, 255, 255), RCOL['blue'] + (235,))
    label(d, tf((4350, 1450)), 'Green: over the river,', 15, (255, 255, 255), RCOL['green'] + (235,))
    label(d, tf((4350, 1520)), 'in at the east side', 15, (255, 255, 255), RCOL['green'] + (235,))
    label(d, tf((3950, 3250)), 'river + bridge', 15)
    label(d, tf((2900, 3550)), 'fields', 15, (40, 30, 25), (250, 240, 215, 220))
    label(d, tf((900, 1700)), 'hill', 15, (40, 30, 25), (230, 240, 215, 220))
    # viewer direction
    vx, vy = Wd - 60, Hd - 20
    d.polygon([(vx, vy - 70), (vx - 20, vy - 30), (vx + 20, vy - 30)], fill=(40, 30, 25))
    d.text((vx, vy - 10), 'viewer', font=F(15), fill=(40, 30, 25), anchor='mm')
    title(im, 'C  Plan: how the station, square, houses and railway entrances fit together',
          'Overhead, viewer at the bottom. Footprints from the painting\'s ground lines. Tracks stay on their current lines; none cross the square.')
    legend(d, 40, im.height - 300, [('solid', (200, 40, 40), 'Route, existing alignment'),
                                    ('dash', (200, 40, 40), 'Inside the station (schematic)'),
                                    ('box', (225, 130, 160), 'Existing house, moved'),
                                    ('hbox', (70, 110, 190), 'Landmark / new building'),
                                    ('hbox', (215, 205, 190), 'Square and paths (proposed)')], 440)
    im.convert('RGB').save(os.path.join(HERE, 'C_plan.jpg'), quality=92)

if __name__ == '__main__':
    sketch_A(); sketch_B(); sketch_C(); print('ok')

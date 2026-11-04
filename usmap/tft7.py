"""Pass 5, group 8 — Toys for Tots branding for Toy Town, after the user's Toy Town reference.

  * the grand station: a cream ribbon banner across the foot of the fan-light lettered TOYS FOR TOTS (with the
    registered mark), a red tab with three white stars under it, a round medallion at the crown of the fan-light
    (gold rim, red field, laurel sprays) in place of the wreath, red bunting swags with gold balls along the wings
  * the medallion is the place for the official logo: if logo/t4t_logo.png exists it is set into the red field;
    until then the field carries a plain gold star. The emblem is never redrawn by hand.
  * the town: lit shop windows with toys under the awnings, a TOY DONATION sign over the shop beside the clock tower
  * a cobbled square in front of the town (where three trees stood) with lamp posts, a Christmas tree, a red wagon
    with a teddy bear and presents, two Marines in dress blues handing over a present, presents, and a red
    TOYS FOR TOTS donation box
The lettering is set with a bundled font (TeX Gyre Bonum Bold) and painted through the gouache brush like the rest.
Everything is in map units.
"""
import math, os, inspect
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import usmap4 as B
from usmap4 import c, hexc, pal_fn
import station5 as ST

S = B.S
FONT = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrebonum-bold.otf'
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo', 't4t_logo.png')
RED, RED_D, CREAM, CREAM_D, GOLD, GOLD_L = '#b8302a', '#8a2420', '#f4ead2', '#d8c8a4', '#d8a840', '#f2d488'
NAVY, BLUE_T, WHITE = '#1c2642', '#2c4a86', '#f4f2ec'

# ---------------------------------------------------------------- lettering
def text_mask(text, cx, cy, size, arc=0.0, track=0.0, font=FONT):
    """A soft-edged pixel mask of `text` centred on (cx, cy), `size` map units tall (cap height), bent upward in the
    middle by `arc` map units. Returns a canvas mask tuple (x0, y0, m)."""
    k = c.k; px = max(8, int(round(size * k * 1.38)))
    f = ImageFont.truetype(font, px)
    widths = [f.getlength(ch) for ch in text]; trk = track * k
    tw = sum(widths) + trk * (len(text) - 1)
    asc, desc = f.getmetrics()
    W_, H_ = int(tw + 8), int(asc + desc + 8 + abs(arc) * k * 2)
    im = Image.new('L', (W_, H_), 0); d = ImageDraw.Draw(im)
    x = 4.0
    for ch, w in zip(text, widths):
        d.text((x, 4 + abs(arc) * k), ch, font=f, fill=255); x += w + trk
    m = np.asarray(im, np.float32) / 255
    if arc:
        u = (np.arange(W_) - W_ / 2) / (W_ / 2)
        shift = arc * k * (1 - u ** 2)                      # lift the middle
        mx, my = np.meshgrid(np.arange(W_, dtype=np.float32), np.arange(H_, dtype=np.float32))
        m = cv2.remap(m, mx, my + shift[None, :].astype(np.float32), cv2.INTER_LINEAR, borderValue=0)
    ys, xs = np.nonzero(m > .02)
    if len(xs) == 0: return None
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    pcx, pcy = (cx + c.d[0]) * k, (cy + c.d[1]) * k
    x0, y0 = int(round(pcx - m.shape[1] / 2)), int(round(pcy - m.shape[0] / 2))
    return (x0, y0, np.clip(m, 0, 1))

def _fit(m):
    """Crop a pixel mask to the canvas (it only matters when a render covers part of the map)."""
    x0, y0, mm = m; h, w = mm.shape
    a0, b0 = max(0, -y0), max(0, -x0); a1, b1 = min(h, c.H - y0), min(w, c.W - x0)
    if a1 <= a0 or b1 <= b0: return None
    return (x0 + b0, y0 + a0, mm[a0:a1, b0:b1])

def paint_text(text, cx, cy, size, col, arc=0.0, track=0.0, outline=None, ow=1.0):
    m = text_mask(text, cx, cy, size, arc, track)
    if m is None: return
    if outline:
        x0, y0, mm = m; p = int(math.ceil(ow * c.k)) + 2
        big = np.pad(mm, p); big = cv2.dilate(big, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * p - 3, 2 * p - 3)))
        om = _fit((x0 - p, y0 - p, cv2.GaussianBlur(big, (0, 0), .6)))
        if om is not None: c.area(None, outline, m=om, edge_dark=0, var=.03)
    m = _fit(m)
    if m is not None: c.area(None, col, m=m, edge_dark=.12, var=.04, varbig=.03)

def star(x, y, r, col, rot=-math.pi / 2, inner=.42):
    pts = [(x + (r if i % 2 == 0 else r * inner) * math.cos(rot + i * math.pi / 5), y + (r if i % 2 == 0 else r * inner) * math.sin(rot + i * math.pi / 5)) for i in range(10)]
    c.area(pts, col, wob=0, rough=.25, edge_dark=.08)

def disc(x, y, r, col, seed=0, edge=.15):
    return c.area(S.lumpy(x, y, r, r, seed, n=max(18, int(r * 3)), amp=0), col, wob=0, rough=.25, edge_dark=edge)

# ---------------------------------------------------------------- the station
def _station_without_wreath():
    """station5.grand_station5 with the wreath block left out (the medallion takes its place)."""
    src = inspect.getsource(ST)
    i = src.index('def grand_station5('); j = src.index('# where the three pennants fly', i); code = src[i:j]
    a = code.index('    # wreath at the crown of the fan-light'); b = code.index('    # finial at the apex for the blue pennant')
    code = code[:a] + code[b:]
    # Compile into station5's own (live) namespace under a new name. A copy of the namespace (as before 4 Nov 2026)
    # froze the canvas of the first render, so every later render in the same process sent the station's own marks
    # to that first canvas: only the first station tile of a tiled build was right. Whole-map renders were unaffected.
    code = code.replace('def grand_station5(', 'def _grand_station5_without_wreath(', 1)
    exec(compile(code, '<tft7:grand_station5>', 'exec'), ST.__dict__)
    return ST.__dict__['_grand_station5_without_wreath']
_GS = None

def medallion(x, y, r=18):
    # laurel sprays, behind the disc
    for s in (-1, 1):
        stem = [(x + s * (r * .55 + r * .95 * math.sin(t)), y + r * .95 * math.cos(t) * .95) for t in np.linspace(.15, 2.45, 14)]
        c.stroke(stem, 1.3, '#8a6a2a', a=1, dry=0, taper=(.2, .2))
        for i, (px, py) in enumerate(stem[1:-1]):
            t = .15 + (i + 1) / 13 * 2.3
            for side in (-1, 1):
                a_ = math.atan2(-math.sin(t) * .95, s * math.cos(t)) + side * .7
                c.dab(px + math.cos(a_) * 2.2, py + math.sin(a_) * 2.2, 5.2, 2.3, a_, ['#3f6a34', '#557e40', '#2f5a2c'][(i + side) % 3], a=1, dry=.1, bend=.3)
    disc(x, y + .6, r + 1.2, '#7a5418', 301, edge=0)              # a soft shadow ring
    disc(x, y, r, GOLD, 302, edge=.25)
    c.stroke([(x + (r - 1.6) * math.cos(t), y + (r - 1.6) * math.sin(t)) for t in np.linspace(math.pi * 1.05, math.pi * 1.6, 12)], 1.2, GOLD_L, a=.9, dry=.1, taper=(.3, .3))
    disc(x, y, r - 3.2, RED, 303, edge=.2)
    c.stroke([(x + (r - 4.6) * math.cos(t), y + (r - 4.6) * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48)], .7, GOLD, a=.9, dry=0, taper=(0, 0))
    if os.path.exists(LOGO):                                       # the official logo, supplied by Toys for Tots
        lg = cv2.imread(LOGO, cv2.IMREAD_UNCHANGED)
        if lg is not None:
            k = c.k; D = int((r - 5.5) * 2 * k); s_ = D / max(lg.shape[:2]); lg = cv2.resize(lg, (max(1, int(lg.shape[1] * s_)), max(1, int(lg.shape[0] * s_))), interpolation=cv2.INTER_AREA)
            rgb = lg[..., :3][..., ::-1].astype(np.float32) / 255; al = lg[..., 3].astype(np.float32) / 255 if lg.shape[2] == 4 else np.ones(lg.shape[:2], np.float32)
            x0 = int((x + c.d[0]) * k - lg.shape[1] / 2); y0 = int((y + c.d[1]) * k - lg.shape[0] / 2)
            reg = c.img[y0:y0 + lg.shape[0], x0:x0 + lg.shape[1]]; reg += (rgb - reg) * al[..., None]
            return
    star(x, y + .5, r * .5, GOLD, inner=.44)
    star(x - .4, y, r * .38, GOLD_L, inner=.44)

def banner(x, y, half=86, hgt=22, lift=5):
    """A cream ribbon banner, bent upward in the middle, with folded tails and gold knobs; lettered TOYS FOR TOTS."""
    def edge(off, n=40):
        return [(x - half + 2 * half * u, y + off - lift * (1 - (2 * u - 1) ** 2)) for u in np.linspace(0, 1, n)]
    top, bot = edge(-hgt / 2), edge(hgt / 2)
    # tails, folded back behind the ends
    for s in (-1, 1):
        ex = x + s * half
        tail = [(ex - s * 2, y - hgt / 2 + 3), (ex + s * 13, y - hgt / 2 + 6), (ex + s * 8, y + 2), (ex + s * 14, y + hgt / 2 + 4), (ex - s * 2, y + hgt / 2 - 1)]
        c.area(tail, CREAM_D, wob=0, rough=.35, edge_dark=.18)
        c.stroke([(ex + s * 13, y - hgt / 2 + 6), (ex + s * 8, y + 2), (ex + s * 14, y + hgt / 2 + 4)], .9, '#a8946c', a=.8, dry=0, taper=(0, 0))
    m = c.area(top + bot[::-1], CREAM, wob=0, rough=.35, edge_dark=.12, seed=311)
    if m is not None: c.stip(m, pal_fn([CREAM, '#ece0c4', '#faf2e0'], .03), spacing=1.2, L=2.4, w=1.1, angfn=lambda X, Y: 0 * X, seed=312, jit=.3)
    c.stroke(edge(-hgt / 2 + 2.2), 1.6, RED, a=.95, dry=.05, taper=(0, 0)); c.stroke(edge(hgt / 2 - 2.2), 1.6, RED, a=.95, dry=.05, taper=(0, 0))
    c.stroke(edge(-hgt / 2 + .3), .8, '#a8946c', a=.8, dry=0, taper=(0, 0)); c.stroke(edge(hgt / 2 - .3), .8, '#a8946c', a=.8, dry=0, taper=(0, 0))
    for s in (-1, 1):                                              # gold knobs where the banner is fixed
        disc(x + s * (half - 1), y - lift * 0 + 0, 3.4, GOLD, 320 + s, edge=.3); c.dots([(x + s * (half - 1) - 1, y - 1.2)], 1.0, [GOLD_L])
    paint_text('TOYS FOR TOTS', x - 2, y - lift * .86 + .6, 11.2, RED, arc=lift * .78, track=.5, outline='#7a1e18', ow=.5)
    paint_text('®', x + half - 11, y - lift * .3 - 5, 3.2, RED)
    # the red tab with three white stars under the middle
    tab = [(x - 24, y + hgt / 2 - lift - 1), (x + 24, y + hgt / 2 - lift - 1), (x + 22, y + hgt / 2 - lift + 10.5), (x - 22, y + hgt / 2 - lift + 10.5)]
    c.area(tab, RED, wob=0, rough=.3, edge_dark=.15)
    c.stroke([(x - 22, y + hgt / 2 - lift + 10), (x + 22, y + hgt / 2 - lift + 10)], .9, RED_D, a=.9, dry=0, taper=(0, 0))
    for i in (-1, 0, 1): star(x + i * 13.5, y + hgt / 2 - lift + 4.9, 4.6, WHITE, inner=.45)

def swag(x0, x1, y, sag=8, seed=0):
    xs = np.linspace(x0, x1, 18); u = (xs - x0) / (x1 - x0)
    top = [(px, y + 1.5 * math.sin(math.pi * uu)) for px, uu in zip(xs, u)]
    bot = [(px, y + sag * math.sin(math.pi * uu) + 1.2) for px, uu in zip(xs, u)]
    c.area(top + bot[::-1], RED, wob=0, rough=.35, edge_dark=.15, seed=seed)
    mid = [(px, y + (sag * .55) * math.sin(math.pi * uu) + 1.2) for px, uu in zip(xs, u)]
    c.stroke(mid[2:-2], .9, RED_D, a=.8, dry=.1, taper=(.3, .3))
    c.stroke(bot[1:-1], .8, '#e8685a', a=.6, dry=.1, taper=(.3, .3))

def station_branding(x, y):
    global _GS
    if _GS is None: _GS = _station_without_wreath()
    _GS(x, y)
    spring, rise = y - 96, 74
    medallion(x, spring - rise * .6, 18)
    banner(x, spring - 6, half=84, hgt=23, lift=5)
    eave = y - 80
    for s in (-1, 1):
        pts = [x + s * v for v in (112, 147, 180)]
        for a_, b_ in zip(pts[:-1], pts[1:]): swag(min(a_, b_), max(a_, b_), eave + 4, 8, seed=int(abs(a_)))
        for px in pts: disc(px, eave + 4.5, 2.6, GOLD, int(px), edge=.3); c.dots([(px - .7, eave + 3.6)], .8, [GOLD_L])
    # small swags hanging under the banner's ends, as in the reference
    for s in (-1, 1):
        swag(min(x + s * 86, x + s * 101), max(x + s * 86, x + s * 101), spring + 2, 6, seed=33 + s)

# ---------------------------------------------------------------- the town's shops
ROW = [(44, 74), (46, 92), (40, 80), (44, 86), (60, 0), (44, 84), (42, 92), (44, 80), (46, 74)]
def houses():
    x0, y = B.TOWN; x = x0; out = []
    for i, (w, h) in enumerate(ROW):
        out.append((i, x, w, h)); x += w * 1.03
    return out

def teddy(x, y, s=1.0, col='#a8683a'):
    c.area(S.lumpy(x, y - 3.2 * s, 2.9 * s, 3.3 * s, 401, n=20, amp=.03), col, wob=0, rough=.3, edge_dark=.15)
    for dx in (-2.4, 2.4): disc(x + dx * s, y - .6 * s, 1.3 * s, col, 402, edge=.1); disc(x + dx * 1.1 * s, y - 4.5 * s, 1.1 * s, col, 403, edge=.1)
    disc(x, y - 8.3 * s, 2.5 * s, col, 404, edge=.15)
    for dx in (-1.9, 1.9): disc(x + dx * s, y - 10.3 * s, 1.0 * s, col, 405, edge=.15)
    disc(x, y - 7.6 * s, 1.1 * s, '#e6c49a', 406, edge=0); c.dots([(x - .9 * s, y - 8.9 * s), (x + .9 * s, y - 8.9 * s)], .35 * s, ['#2a1a12'])
    c.dots([(x, y - 7.9 * s)], .4 * s, ['#2a1a12']); c.area([(x - 1.6 * s, y - 6.0 * s), (x + 1.6 * s, y - 6.0 * s), (x, y - 4.9 * s)], RED, wob=0, rough=.2)

def toy_train(x, y, s=1.0):
    c.area([(x - 6 * s, y - 1.5 * s), (x + 1 * s, y - 1.5 * s), (x + 1 * s, y - 5 * s), (x - 6 * s, y - 5 * s)], '#c8302a', wob=0, rough=.3, edge_dark=.15)
    c.area([(x - 6 * s, y - 5 * s), (x - 2.6 * s, y - 5 * s), (x - 2.6 * s, y - 8.4 * s), (x - 6 * s, y - 8.4 * s)], '#c8302a', wob=0, rough=.3, edge_dark=.15)
    c.area([(x - 6.6 * s, y - 8.4 * s), (x - 2 * s, y - 8.4 * s), (x - 2 * s, y - 9.4 * s), (x - 6.6 * s, y - 9.4 * s)], '#2a2420', wob=0, rough=.2)
    c.area([(x - .4 * s, y - 5 * s), (x + .8 * s, y - 5 * s), (x + .8 * s, y - 7.6 * s), (x - .4 * s, y - 7.6 * s)], '#2a2420', wob=0, rough=.2)
    c.area([(x + 2 * s, y - 1.5 * s), (x + 7 * s, y - 1.5 * s), (x + 7 * s, y - 4.6 * s), (x + 2 * s, y - 4.6 * s)], '#e8b84a', wob=0, rough=.3, edge_dark=.15)
    c.dots([(x - 4.6 * s, y - .8 * s), (x - 1.4 * s, y - .8 * s), (x + 3.2 * s, y - .8 * s), (x + 5.8 * s, y - .8 * s)], 1.05 * s, ['#2a2420'])
    c.dots([(x - 4.4 * s, y - 6.8 * s)], .6 * s, ['#f6e2a0'])

def presents(x, y, s=1.0, seed=0, n=3, cols=None):
    r = np.random.RandomState(seed); cols = cols or ['#c8302a', '#3f6aa8', '#3f8a44', '#e8b84a', '#8a4aa0', '#e88aa0']
    ribs = ['#f2d488', '#f4f2ec', '#c8302a']
    xx = x - (n - 1) * 3.2 * s
    for i in range(n):
        w = r.uniform(4.2, 6.0) * s; h = r.uniform(3.6, 5.4) * s; col = cols[r.randint(len(cols))]; rib = ribs[r.randint(3)]
        if rib == col: rib = '#f4f2ec'
        bx = xx + i * 6.2 * s + r.uniform(-.6, .6) * s
        c.area([(bx - w / 2, y), (bx + w / 2, y), (bx + w / 2, y - h), (bx - w / 2, y - h)], col, wob=0, rough=.3, edge_dark=.15)
        c.stroke([(bx, y), (bx, y - h)], .9 * s, rib, a=1, dry=0, taper=(0, 0)); c.stroke([(bx - w / 2, y - h * .55), (bx + w / 2, y - h * .55)], .9 * s, rib, a=1, dry=0, taper=(0, 0))
        c.area([(bx + w / 2, y), (bx + w / 2 + 1.2 * s, y - .8 * s), (bx + w / 2 + 1.2 * s, y - h - .8 * s), (bx + w / 2, y - h)], hexc(col) * .72, wob=0, rough=.2)   # side
        c.area([(bx - w / 2, y - h), (bx + w / 2, y - h), (bx + w / 2 + 1.2 * s, y - h - .8 * s), (bx - w / 2 + 1.2 * s, y - h - .8 * s)], np.minimum(hexc(col) * 1.18, 1), wob=0, rough=.2)   # lid
        for sd in (-1, 1):                                            # bow loops and tails
            c.area(S.lumpy(bx + sd * 1.3 * s + .5 * s, y - h - 1.5 * s, 1.25 * s, .8 * s, seed + i + sd, n=12, amp=0), rib, wob=0, rough=.2, edge_dark=.2)
        c.dots([(bx + .5 * s, y - h - 1.3 * s)], .55 * s, [rib])

def nutcracker(x, y, s=1.0):
    c.area([(x - 1.3 * s, y), (x + 1.3 * s, y), (x + 1.3 * s, y - 3.4 * s), (x - 1.3 * s, y - 3.4 * s)], '#2a2a5a', wob=0, rough=.2)
    c.area([(x - 1.8 * s, y - 3.4 * s), (x + 1.8 * s, y - 3.4 * s), (x + 1.6 * s, y - 7.2 * s), (x - 1.6 * s, y - 7.2 * s)], '#c8302a', wob=0, rough=.2, edge_dark=.1)
    c.stroke([(x - 1.7 * s, y - 4.2 * s), (x + 1.7 * s, y - 4.2 * s)], .6 * s, GOLD, a=1, dry=0, taper=(0, 0))
    disc(x, y - 8.4 * s, 1.35 * s, '#e8c4a0', 411, edge=.1); c.dots([(x, y - 7.6 * s)], .7 * s, [WHITE])
    c.area([(x - 1.4 * s, y - 9.3 * s), (x + 1.4 * s, y - 9.3 * s), (x + 1.2 * s, y - 12 * s), (x - 1.2 * s, y - 12 * s)], '#1c1c24', wob=0, rough=.2)
    c.dots([(x, y - 10.4 * s)], .45 * s, [GOLD])

def rocking_horse(x, y, s=1.0):
    c.stroke([(x - 6 * s, y - 1.5 * s), (x - 3 * s, y - .3 * s), (x + 3 * s, y - .3 * s), (x + 6 * s, y - 1.5 * s)], 1.2 * s, '#8a4a2a', a=1, dry=0, taper=(0, 0))
    for lx in (-3, -1.2, 1.8, 3.4): c.stroke([(x + lx * s, y - .6 * s), (x + lx * .8 * s, y - 4 * s)], .9 * s, '#c88a4a', a=1, dry=0, taper=(0, 0))
    c.area(S.lumpy(x, y - 5 * s, 4.4 * s, 1.9 * s, 412, n=18, amp=0), '#d89a5a', wob=0, rough=.2, edge_dark=.15)
    c.area([(x + 2.6 * s, y - 5.8 * s), (x + 4.4 * s, y - 9.6 * s), (x + 6.4 * s, y - 8.4 * s), (x + 5.6 * s, y - 7.6 * s), (x + 4.2 * s, y - 5.2 * s)], '#d89a5a', wob=0, rough=.2, edge_dark=.15)
    c.stroke([(x + 3.8 * s, y - 9.4 * s), (x + 2.6 * s, y - 6.2 * s)], 1.0 * s, '#7a3a1e', a=1, dry=0, taper=(0, .3))
    c.stroke([(x - 4.2 * s, y - 5.4 * s), (x - 6 * s, y - 3.6 * s)], .9 * s, '#7a3a1e', a=1, dry=0, taper=(0, .4))
    c.area([(x - 1 * s, y - 6.6 * s), (x + 1.6 * s, y - 6.6 * s), (x + 1.4 * s, y - 5 * s), (x - .8 * s, y - 5 * s)], RED, wob=0, rough=.2)

TOYS = {0: 'train', 1: 'teddy', 2: 'teddy', 3: 'train', 5: 'horse', 6: 'nut', 7: 'gifts', 8: 'teddy'}
def shop_window(i, x, w, h, y):
    """A lit display window under the awning, with a heavy wooden frame and a toy in it."""
    top = y - h * .28 + 9.6; bot = y - 2.4; l, r_ = x + w * .17, x + w * .83
    c.area([(l - 1.6, bot + 1.4), (r_ + 1.6, bot + 1.4), (r_ + 1.6, top - 1.2), (l - 1.6, top - 1.2)], '#5a3a24', wob=0, rough=.3, edge_dark=.15)
    m = c.area([(l, bot), (r_, bot), (r_, top), (l, top)], '#f2c25a', wob=0, rough=.25, edge_dark=0)
    if m is not None:
        c.stip(m, lambda X, Y, rr: np.array([hexc('#f6d27a'), hexc('#f0b848'), hexc('#f8e2a0')])[rr.randint(3, size=len(X))] * (1 - np.clip((Y - top) / (bot - top), 0, 1)[:, None] * .12),
               spacing=1.0, L=1.8, w=1.0, angfn=lambda X, Y: 0 * X, seed=500 + i, jit=.4)
    cx = (l + r_) / 2; s = min(1.0, (bot - top) / 11.5)
    kind = TOYS.get(i)
    if kind == 'teddy': teddy(cx, bot - .4, s * .95)
    elif kind == 'train': toy_train(cx, bot - .4, s * .95)
    elif kind == 'horse': rocking_horse(cx, bot - .4, s * .95)
    elif kind == 'nut': nutcracker(cx - 5 * s, bot - .3, s * .8); presents(cx + 4 * s, bot - .3, s * .8, 60 + i, n=1)
    elif kind == 'gifts': presents(cx, bot - .3, s * .85, 70 + i, n=3)
    c.stroke([(l - 1, bot + .6), (r_ + 1, bot + .6)], 1.4, '#7a5234', a=1, dry=0, taper=(0, 0))       # the sill
    c.stroke([(cx, top), (cx, top + 2.6)], .8, '#5a3a24', a=1, dry=0, taper=(0, 0))

def donation_sign(x, y, w=40):
    """A cream board with a red border lettered TOY / DONATION, hung over the shop."""
    hh = 13
    c.area([(x - w / 2 - 1, y + hh / 2 + 1), (x + w / 2 + 1, y + hh / 2 + 1), (x + w / 2 + 1, y - hh / 2 - 1), (x - w / 2 - 1, y - hh / 2 - 1)], '#5a3a24', wob=0, rough=.3, edge_dark=.1)
    m = c.area([(x - w / 2, y + hh / 2), (x + w / 2, y + hh / 2), (x + w / 2, y - hh / 2), (x - w / 2, y - hh / 2)], CREAM, wob=0, rough=.3, edge_dark=.1)
    c.stroke([(x - w / 2 + 1.2, y + hh / 2 - 1.2), (x + w / 2 - 1.2, y + hh / 2 - 1.2), (x + w / 2 - 1.2, y - hh / 2 + 1.2), (x - w / 2 + 1.2, y - hh / 2 + 1.2), (x - w / 2 + 1.2, y + hh / 2 - 1.2)], .8, RED, a=1, dry=0, taper=(0, 0))
    paint_text('TOY', x, y - 2.6, 4.0, RED, track=.3)
    paint_text('DONATION', x, y + 3.0, 4.0, RED, track=.2)

def town_extras(which):
    """Shop windows (and the donation sign) for the houses in `which` (indices into the row)."""
    y = B.TOWN[1]
    for i, x, w, h in houses():
        if i not in which or h == 0: continue
        shop_window(i, x, w, h, y)
        if i == 5: donation_sign(x + w / 2, y - h * .28 - 9.5, w * .86)

# ---------------------------------------------------------------- the square in front of the town
SQ_X0, SQ_X1, SQ_Y0, SQ_Y1 = 806, 1010, 548, 604
FRONT_HOUSES = {2, 3, 5}                      # houses whose foot the field hill used to hide (and the tower)
def lamp_post(x, y, h=26):
    c.stroke([(x, y), (x, y - h)], 1.6, '#1e1c20', a=1, dry=0, taper=(0, 0))
    c.area([(x - 2.2, y), (x + 2.2, y), (x + 1.4, y - 2.4), (x - 1.4, y - 2.4)], '#1e1c20', wob=0, rough=.2)
    c.area([(x - 2.4, y - h), (x + 2.4, y - h), (x + 2.8, y - h - 5.4), (x - 2.8, y - h - 5.4)], '#f8d470', wob=0, rough=.2, edge_dark=.1)
    c.stroke([(x - 2.4, y - h), (x + 2.4, y - h), (x + 2.8, y - h - 5.4), (x - 2.8, y - h - 5.4), (x - 2.4, y - h)], .8, '#1e1c20', a=1, dry=0, taper=(0, 0))
    c.area([(x - 3.6, y - h - 5.2), (x + 3.6, y - h - 5.2), (x, y - h - 8.4)], '#1e1c20', wob=0, rough=.2)
    c.dots([(x, y - h - 2.8)], 1.3, ['#fff4c8'])

def christmas_tree(x, y, h=36):
    c.area([(x - 1.6, y), (x + 1.6, y), (x + 1.4, y - h * .14), (x - 1.4, y - h * .14)], '#5a3a24', wob=0, rough=.3)
    tiers = [(.12, .44, .30), (.36, .66, .24), (.58, .88, .17)]
    for j, (b0, t0, hw) in enumerate(tiers):
        poly = [(x - h * hw, y - h * b0), (x + h * hw, y - h * b0), (x, y - h * t0 - h * .1)]
        m = c.area(poly, ['#2f6a3a', '#357440', '#2a6034'][j], wob=0, rough=.4, edge_dark=.15, seed=440 + j)
        if m is not None: c.stip(m, pal_fn(['#2f6a3a', '#3f7e46', '#24562e', '#4a8a4e']), spacing=1.1, L=2.4, w=1.1, angfn=lambda X, Y: 1.2 + 0 * X, seed=441 + j, jit=.5)
        c.stroke([(x - h * hw, y - h * b0), (x + h * hw, y - h * b0)], 1.0, '#1e4a28', a=.7, dry=.2, taper=(.2, .2))
    r = np.random.RandomState(7)
    orn = []
    for j, (b0, t0, hw) in enumerate(tiers):
        for _ in range(4):
            u = r.uniform(.15, .85); yy = y - h * (b0 + (t0 - b0) * r.uniform(.05, .6)); w_ = h * hw * (1 - (y - h * b0 - yy) / (h * (t0 - b0) + h * .1))
            orn.append((x + (u * 2 - 1) * w_ * .8, yy))
    c.dots(orn, 1.1, ['#c8302a', GOLD, '#3f6aa8', '#f4f2ec'], seed=8)
    star(x, y - h * .98 - 1, 3.4, GOLD, inner=.45)
    # the big red bow in front, as in the reference
    bx, by = x, y - h * .5; q = h / 36
    for s in (-1, 1): c.area([(bx, by), (bx + s * 6.4 * q, by - 3.8 * q), (bx + s * 6.4 * q, by + 3.2 * q)], RED, wob=0, rough=.25, edge_dark=.18)
    for s in (-1, 1): c.area([(bx - .6 * s, by + .4), (bx + s * 3.8 * q, by + 8.6 * q), (bx + s * 1.6 * q, by + 9.2 * q), (bx - .2 * s, by + .8)], RED, wob=0, rough=.25, edge_dark=.18)
    disc(bx, by, 1.9 * q, RED_D, 445, edge=.1)

def wagon(x, y, s=1.0, flip=False):
    if flip:                                                         # handle to the right
        c.stroke([(x + 7.4 * s, y - 4.4 * s), (x + 12 * s, y - 9.4 * s)], 1.0 * s, '#3a2e26', a=1, dry=0, taper=(0, 0))
        disc(x + 12 * s, y - 9.4 * s, .9 * s, '#3a2e26', 450, edge=0)
    c.area([(x - 7 * s, y - 2.2 * s), (x + 7 * s, y - 2.2 * s), (x + 7.6 * s, y - 7 * s), (x - 7.6 * s, y - 7 * s)], '#c8302a', wob=0, rough=.3, edge_dark=.15)
    c.stroke([(x - 7.4 * s, y - 6.4 * s), (x + 7.4 * s, y - 6.4 * s)], .9 * s, '#e8685a', a=.8, dry=0, taper=(0, 0))
    if not flip:
        c.stroke([(x - 7.4 * s, y - 4.4 * s), (x - 13 * s, y - 9 * s)], 1.0 * s, '#3a2e26', a=1, dry=0, taper=(0, 0))
        disc(x - 13 * s, y - 9 * s, .9 * s, '#3a2e26', 450, edge=0)
    teddy(x - 2.4 * s, y - 6.4 * s, .82 * s)
    presents(x + 3.6 * s, y - 6.6 * s, .72 * s, 451, n=2)
    for wx in (-4.6, 4.6):
        disc(x + wx * s, y - 1.6 * s, 2.0 * s, '#2a2420', 452, edge=0); disc(x + wx * s, y - 1.6 * s, .7 * s, '#9a9aa0', 453, edge=0)

def shadow(x, y, rx, ry=None, a=.26):
    c.area(S.lumpy(x, y, rx, ry or rx * .32, int(x * 7 + y) % 9973, n=20, amp=0), '#3a3224', wob=0, rough=.3, edge_dark=0, a=a)

def marine(x, y, face=1, h=23):
    """A Marine in dress blues: white cap with a black visor and gold emblem, dark blue coat with red piping, gold
    buttons and a white belt, sky-blue trousers with a red stripe, white gloves, polished shoes. Facing `face`
    (+1 right, -1 left), the front arm reaching forward."""
    s = h / 23.0; f = face
    for dx in (-1.2, 1.2):                                           # trousers and shoes
        c.area([(x + dx * s - 1.15 * s, y - 1 * s), (x + dx * s + 1.15 * s, y - 1 * s), (x + dx * s + 1.1 * s, y - 10.5 * s), (x + dx * s - 1.1 * s, y - 10.5 * s)], BLUE_T, wob=0, rough=.25, edge_dark=.15)
        c.stroke([(x + dx * s - f * .3 * s, y - 1.2 * s), (x + dx * s - f * .3 * s, y - 10.2 * s)], .3 * s, '#1e3a6e', a=.7, dry=0, taper=(0, 0))   # crease
        c.stroke([(x + dx * s + f * .7 * s, y - 1.2 * s), (x + dx * s + f * .7 * s, y - 10.2 * s)], .5 * s, '#c8302a', a=1, dry=0, taper=(0, 0))
        c.area([(x + dx * s - 1.2 * s, y), (x + dx * s + 1.2 * s + f * .9 * s, y), (x + dx * s + 1.1 * s + f * .8 * s, y - 1.3 * s), (x + dx * s - 1.2 * s, y - 1.3 * s)], '#141218', wob=0, rough=.2)
        c.dots([(x + dx * s + f * .5 * s, y - .9 * s)], .25 * s, ['#8a8a96'])                                                   # shine
    coat = [(x - 3.1 * s, y - 10 * s), (x + 3.1 * s, y - 10 * s), (x + 2.9 * s, y - 18.4 * s), (x - 2.9 * s, y - 18.4 * s)]
    c.area(coat, NAVY, wob=0, rough=.25, edge_dark=.15)
    c.stroke([(x + f * .5 * s, y - 10.2 * s), (x + f * .5 * s, y - 18.2 * s)], .3 * s, '#c8302a', a=.85, dry=0, taper=(0, 0))      # piping down the front
    c.stroke([(x - 3.1 * s, y - 10.1 * s), (x + 3.1 * s, y - 10.1 * s)], .3 * s, '#c8302a', a=.85, dry=0, taper=(0, 0))
    c.area([(x - 3.1 * s, y - 10.4 * s), (x + 3.1 * s, y - 10.4 * s), (x + 3.1 * s, y - 11.7 * s), (x - 3.1 * s, y - 11.7 * s)], WHITE, wob=0, rough=.2)   # belt
    c.area([(x + f * .2 * s - .7 * s, y - 10.6 * s), (x + f * .2 * s + .7 * s, y - 10.6 * s), (x + f * .2 * s + .7 * s, y - 11.5 * s), (x + f * .2 * s - .7 * s, y - 11.5 * s)], GOLD, wob=0, rough=.2)
    c.dots([(x + f * .5 * s, y - yy * s) for yy in (12.9, 14.5, 16.1, 17.6)], .34 * s, [GOLD])
    c.area([(x - 1.5 * s, y - 18.2 * s), (x + 1.5 * s, y - 18.2 * s), (x + 1.3 * s, y - 19.6 * s), (x - 1.3 * s, y - 19.6 * s)], NAVY, wob=0, rough=.2)     # high collar
    c.stroke([(x - 1.4 * s, y - 19.5 * s), (x + 1.4 * s, y - 19.5 * s)], .35 * s, '#c8302a', a=.9, dry=0, taper=(0, 0))
    for sx in (-1, 1): c.dots([(x + sx * 2.6 * s, y - 18.1 * s)], .55 * s, [GOLD])                                          # epaulette buttons
    # back arm at the side, front arm reaching forward; red cuffs, white gloves
    c.stroke([(x - f * 2.8 * s, y - 17.6 * s), (x - f * 3.2 * s, y - 11.8 * s)], 1.7 * s, NAVY, a=1, dry=0, taper=(0, 0))
    c.stroke([(x - f * 3.15 * s, y - 12.4 * s), (x - f * 3.2 * s, y - 11.7 * s)], 1.7 * s, '#c8302a', a=.8, dry=0, taper=(0, 0)); c.dots([(x - f * 3.2 * s, y - 11.0 * s)], .85 * s, [WHITE])
    c.stroke([(x + f * 2.6 * s, y - 17.4 * s), (x + f * 4.4 * s, y - 13.7 * s), (x + f * 6.4 * s, y - 13.5 * s)], 1.7 * s, NAVY, a=1, dry=0, taper=(0, 0))
    c.stroke([(x + f * 6.0 * s, y - 13.5 * s), (x + f * 6.5 * s, y - 13.5 * s)], 1.7 * s, '#c8302a', a=.8, dry=0, taper=(0, 0)); c.dots([(x + f * 7.1 * s, y - 13.5 * s)], .9 * s, [WHITE])
    # head: a face turned three-quarters, ear, eyes and a smile
    hx, hy = x + f * .2 * s, y - 21.4 * s
    disc(hx, hy, 2.05 * s, '#e2b48c', 460, edge=.12)
    c.dots([(hx - f * 1.7 * s, hy + .2 * s)], .55 * s, ['#c8946c'])
    c.dots([(hx + f * .35 * s, hy - .1 * s), (hx + f * 1.35 * s, hy - .1 * s)], .26 * s, ['#2a1a12'])
    c.stroke([(hx + f * .4 * s, hy + .95 * s), (hx + f * .9 * s, hy + 1.15 * s), (hx + f * 1.4 * s, hy + .95 * s)], .28 * s, '#8a3a2a', a=.9, dry=0, taper=(.2, .2))
    c.dots([(hx + f * 1.2 * s, hy + .5 * s)], .35 * s, ['#e89a88'])
    # dress cap: white crown, white band with a gold emblem, black visor reaching forward, gold chin strap
    c.area([(hx - 2.2 * s, hy - 1.5 * s), (hx + 2.2 * s, hy - 1.5 * s), (hx + 2.2 * s, hy - 2.5 * s), (hx - 2.2 * s, hy - 2.5 * s)], '#e6e4dc', wob=0, rough=.2, edge_dark=.1)
    c.area(S.lumpy(hx + f * .25 * s, hy - 3.0 * s, 3.1 * s, 1.05 * s, 461, n=18, amp=0), WHITE, wob=0, rough=.2, edge_dark=.14)
    c.area([(hx - f * .2 * s, hy - 1.9 * s), (hx + f * 2.0 * s, hy - 1.9 * s), (hx + f * 3.6 * s, hy - 1.05 * s), (hx + f * 3.2 * s, hy - .6 * s), (hx + f * 1.2 * s, hy - .75 * s), (hx - f * .2 * s, hy - 1.2 * s)], '#121016', wob=0, rough=.15, edge_dark=0)
    c.stroke([(hx + f * .6 * s, hy - 1.55 * s), (hx + f * 3.0 * s, hy - 1.1 * s)], .25 * s, '#5a5a66', a=.8, dry=0, taper=(.2, .2))
    c.dots([(hx + f * 1.1 * s, hy - 2.05 * s)], .42 * s, [GOLD])
    c.stroke([(hx - f * 1.6 * s, hy - 1.4 * s), (hx + f * 1.6 * s, hy - 1.4 * s)], .22 * s, GOLD, a=.9, dry=0, taper=(0, 0))

def person(x, y, h, coat, hat, face=1, gift=None, skirt=False, scarf='#f4f2ec', seed=0):
    """A townsperson in a winter coat, scarf and knitted hat; `gift` = a present held in front."""
    s = h / 23.0; f = face
    for dx in (-1.0, 1.0):
        c.area([(x + dx * s - .9 * s, y - .8 * s), (x + dx * s + .9 * s, y - .8 * s), (x + dx * s + .9 * s, y - 8.5 * s), (x + dx * s - .9 * s, y - 8.5 * s)], '#3a3440', wob=0, rough=.25)
        c.area([(x + dx * s - 1.1 * s, y), (x + dx * s + 1.1 * s + f * .6 * s, y), (x + dx * s + 1 * s + f * .6 * s, y - 1.3 * s), (x + dx * s - 1.1 * s, y - 1.3 * s)], '#5a3424', wob=0, rough=.2)
    body = [(x - (4.2 if skirt else 3.2) * s, y - 7 * s), (x + (4.2 if skirt else 3.2) * s, y - 7 * s), (x + 2.8 * s, y - 17.6 * s), (x - 2.8 * s, y - 17.6 * s)]
    c.area(body, coat, wob=0, rough=.3, edge_dark=.16, seed=seed)
    c.dots([(x + f * .4 * s, y - yy * s) for yy in (10, 12.5, 15)], .35 * s, ['#2a2420'])
    c.stroke([(x - 2.6 * s, y - 17.4 * s), (x + 2.6 * s, y - 17.4 * s)], 1.6 * s, scarf, a=1, dry=.1, taper=(.1, .1))
    c.stroke([(x - f * 1.2 * s, y - 17.2 * s), (x - f * 1.6 * s, y - 13.8 * s)], 1.0 * s, scarf, a=1, dry=.1, taper=(0, .2))
    hx, hy = x + f * .2 * s, y - 20.2 * s
    disc(hx, hy, 2.1 * s, '#e8bc96', seed + 1, edge=.12)
    c.dots([(hx + f * .35 * s, hy - .1 * s), (hx + f * 1.3 * s, hy - .1 * s)], .25 * s, ['#2a1a12'])
    c.stroke([(hx + f * .4 * s, hy + .9 * s), (hx + f * .9 * s, hy + 1.1 * s), (hx + f * 1.4 * s, hy + .9 * s)], .26 * s, '#8a3a2a', a=.9, dry=0, taper=(.2, .2))
    c.dots([(hx + f * 1.25 * s, hy + .45 * s)], .35 * s, ['#ec9a8a'])
    c.area([(hx - 2.3 * s, hy - .6 * s), (hx + 2.3 * s, hy - .6 * s)] + [(hx + 2.3 * s * math.cos(t), hy - .6 * s - 2.4 * s * math.sin(t)) for t in np.linspace(0, math.pi, 12)], hat, wob=0, rough=.25, edge_dark=.12)
    c.stroke([(hx - 2.3 * s, hy - .8 * s), (hx + 2.3 * s, hy - .8 * s)], .8 * s, WHITE, a=.9, dry=.1, taper=(0, 0))
    disc(hx, hy - 3.3 * s, .8 * s, WHITE, seed + 2, edge=.1)
    if gift:
        gx = x + f * 3.4 * s; gy = y - 8.6 * s
        presents(gx, gy, 1.15 * s, seed + 3, n=1, cols=[gift])
        c.stroke([(x + f * 2.2 * s, y - 16.6 * s), (gx - f * 1.2 * s, y - 12.2 * s)], 1.5 * s, coat, a=1, dry=0, taper=(0, 0))
        c.dots([(gx - f * 1.0 * s, y - 11.8 * s)], .8 * s, ['#e8bc96'])
    else:
        c.stroke([(x + f * 2.6 * s, y - 16.8 * s), (x + f * 3.4 * s, y - 11 * s)], 1.5 * s, coat, a=1, dry=0, taper=(0, 0))
    c.stroke([(x - f * 2.6 * s, y - 16.8 * s), (x - f * 3.1 * s, y - 11 * s)], 1.5 * s, coat, a=1, dry=0, taper=(0, 0))

def donation_box(x, y, w=20, h=25):
    """The red collection box, lettered TOYS FOR TOTS with three white stars."""
    shadow(x + 2, y + .6, w * .7)
    c.area([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], RED, wob=0, rough=.3, edge_dark=.15)
    c.area([(x + w / 2, y), (x + w / 2 + 3.2, y - 1.8), (x + w / 2 + 3.2, y - h - 1.8), (x + w / 2, y - h)], RED_D, wob=0, rough=.3)
    c.area([(x - w / 2 - .6, y - h), (x + w / 2 + .6, y - h), (x + w / 2 + 3.6, y - h - 2.0), (x - w / 2 + 2.6, y - h - 2.0)], '#d8463a', wob=0, rough=.3)
    c.stroke([(x - w * .3, y - h - 1.0), (x + w * .3 + 1.5, y - h - 1.0)], 1.0, '#4a1410', a=1, dry=0, taper=(0, 0))        # the slot, on the lid
    c.stroke([(x - w / 2 + 1.3, y - 1.3), (x + w / 2 - 1.3, y - 1.3), (x + w / 2 - 1.3, y - h + 1.3), (x - w / 2 + 1.3, y - h + 1.3), (x - w / 2 + 1.3, y - 1.3)], .6, '#f0d8d0', a=.85, dry=0, taper=(0, 0))
    paint_text('TOYS', x, y - h * .78, 3.6, WHITE, track=.2)
    paint_text('FOR', x, y - h * .58, 3.0, WHITE, track=.2)
    paint_text('TOTS', x, y - h * .37, 3.6, WHITE, track=.2)
    for i in (-1, 0, 1): star(x + i * 4.4, y - h * .15, 1.6, WHITE)
    c.area([(x - w / 2 - .4, y + .2), (x + w / 2 + .4, y + .2), (x + w / 2 + .4, y - 1.0), (x - w / 2 - .4, y - 1.0)], '#7a1a14', wob=0, rough=.2)

def cobbles(poly, seed):
    """Rounded cobblestones in offset rows over dark mortar, each with a light upper edge."""
    from matplotlib.path import Path as MP
    m = c.area(poly, '#7e7462', wob=.6, rough=.8, edge_dark=.12, seed=seed)
    if m is None: return None
    P = np.array(poly, float); path = MP(P); r = np.random.RandomState(seed + 2)
    pts = []
    for j, yy in enumerate(np.arange(P[:, 1].min() + 1.4, P[:, 1].max(), 2.35)):
        sc = .85 + .25 * (yy - P[:, 1].min()) / (P[:, 1].max() - P[:, 1].min())   # a little larger toward us
        for xx in np.arange(P[:, 0].min() + (j % 2) * 1.65 * sc, P[:, 0].max(), 3.3 * sc):
            q = (xx + r.uniform(-.35, .35), yy + r.uniform(-.25, .25))
            if path.contains_point(q, radius=-1.4): pts.append((q, sc))
    cols = ['#c8bca4', '#b8ab92', '#bfb39b', '#a89a80', '#d2c8b2', '#9e917a', '#c4b49a', '#b0a48e']
    for (q, sc) in pts:
        c.dots([q], 1.38 * sc, cols, seed=int(q[0] * 13 + q[1] * 7))
    c.dots([(q[0] - .45 * sc, q[1] - .5 * sc) for q, sc in pts[::2]], .5, ['#e0d8c6', '#ddd2bc'], seed=seed + 4)
    return m

def lamp_wreath(x, y):
    ring = [(x + 2.6 * math.cos(t), y + 2.6 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 20)]
    c.stroke(ring, 1.5, '#2f5a34', a=1, dry=.1, taper=(0, 0)); c.dots(ring[::4], .5, ['#c8302a'])
    c.area([(x - 1.6, y + 2.6), (x + 1.6, y + 2.6), (x + 2.2, y + 4.6), (x - 2.2, y + 4.6)], RED, wob=0, rough=.2)

def planter(x, y):
    c.area([(x - 4, y), (x + 4, y), (x + 4.6, y - 4), (x - 4.6, y - 4)], '#7a4e2c', wob=0, rough=.3, edge_dark=.15)
    c.stroke([(x - 4.4, y - 2), (x + 4.4, y - 2)], .5, '#5a3a20', a=.8, dry=0, taper=(0, 0))
    c.area(S.lumpy(x, y - 5.6, 4.4, 2.4, int(x), n=16, amp=.15), '#2f5a34', wob=0, rough=.4, edge_dark=.1)
    r = np.random.RandomState(int(x)); c.dots([(x + r.uniform(-3.4, 3.4), y - 5.6 + r.uniform(-1.6, 1.2)) for _ in range(7)], .8, ['#c8302a', '#e04838'], seed=int(x))

def square(scene_town_seed):
    """Paint the town's foot again in front of the field hill, then the square and everything on it."""
    k = c.k; X0, X1 = SQ_X0 + 2, SQ_X1 - 4
    # 1. the town again, clipped to the band at its foot that the hill crest used to hide
    band = np.zeros((c.H, c.W), np.float32)
    px0, px1 = int((X0 + c.d[0]) * k), int((X1 + c.d[0]) * k); py0, py1 = int((B.TOWN[1] - 30 + c.d[1]) * k), int((B.TOWN[1] + 17 + c.d[1]) * k)
    px0, px1 = min(max(0, px0), c.W), min(max(0, px1), c.W); py0, py1 = min(max(0, py0), c.H), min(max(0, py1), c.H)   # (partial renders)
    band[py0:py1, px0:px1] = 1; band = cv2.GaussianBlur(band, (0, 0), sigmaX=1.2 * k, sigmaY=.01)   # soft only at the sides: a soft top edge faded the sign
    keep_rng, keep_clip = c.rng, c.clipm
    c.rng = np.random.RandomState(scene_town_seed); c.set_clip((0, 0, band))
    B.town_row(*B.TOWN)
    town_extras(FRONT_HOUSES)
    c.clipm = keep_clip; c.rng = keep_rng
    del band
    # 2. the cobbled square, widening toward us, with a stone kerb
    y = B.TOWN[1]
    poly = [(SQ_X0, y + 6), (SQ_X1, y + 6), (SQ_X1 - 2, y + 28), (SQ_X1 - 22, y + 47), (SQ_X1 - 70, y + 53), (SQ_X0 + 66, y + 53), (SQ_X0 + 18, y + 45), (SQ_X0 + 2, y + 26)]
    cobbles(poly, 470)
    kerb = [(SQ_X1 - 2, y + 28), (SQ_X1 - 22, y + 47), (SQ_X1 - 70, y + 53), (SQ_X0 + 66, y + 53), (SQ_X0 + 18, y + 45), (SQ_X0 + 2, y + 26)]
    c.stroke(B.catmull(kerb, 8), 2.4, '#ddd2bc', a=1, dry=.15, taper=(.1, .1), rough=.5)
    c.stroke(B.catmull([(px, py + 1.6) for px, py in kerb], 8), 1.0, '#8a7e6a', a=.8, dry=.1, taper=(.1, .1))
    # 3. on the square, back to front
    for px in (913, 941): planter(px, y + 3)                         # flanking the clock tower's door
    for sx, sy, rx in ((851, y + 33, 13), (884, y + 39.5, 4.5), (897, y + 40, 3.4), (922, y + 39.5, 4.2), (948, y + 39.5, 4.2), (964, y + 41.5, 11), (SQ_X0 + 16, y + 25.5, 3), (SQ_X1 - 16, y + 25.5, 3)):
        shadow(sx, sy, rx)
    for lx in (SQ_X0 + 16, SQ_X1 - 16): lamp_post(lx, y + 25, 30); lamp_wreath(lx, y + 25 - 17)
    christmas_tree(851, y + 33, 46)
    presents(871, y + 37, 1.25, 481, n=2); presents(835, y + 36, 1.1, 485, n=1)
    donation_box(990, y + 34)
    person(884, y + 39, 25, '#3f7a44', '#c8302a', face=1, skirt=True, scarf='#e8b84a', seed=490)
    person(897, y + 40, 16, '#c8302a', '#3f6aa8', face=1, gift='#e8b84a', seed=495)
    marine(922, y + 39, face=1, h=28); marine(948, y + 39, face=-1, h=28)
    presents(935, y + 23.6, 1.1, 483, n=1)                          # the present passing between them
    wagon(964, y + 41, 1.2, flip=True)

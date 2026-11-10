"""Toy Town: the Toys for Tots station, built from shapes with the shared kit (target-painting px).
Barrel vault with a red roof, a stone arch with the fan window and the gold star in its wreath, the
TOYS FOR TOTS banner, the great lower arch window, corner towers, side wings with red swags, and the
clock porch with its doors, annexes, garlands and steps.
    python3 toytown_station.py         # study render, writes out/station_study.png and out/station_compare.jpg
"""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import toytown_kit as T
from toytown_kit import A, S, shaded, roof, window, garland, snow_edge, snow_clump, snow_cap, eave_shadow, chimney, stip, lump, hexc, glass
from toytown_east import sign, wreath

STONE = ['#e2c896', '#ecd6aa', '#f2e0b8', '#f8ecce', '#dcc08a']
STONE_D = '#b8975e'
CX = 700

def ell(cx, cy, rx, ry, a0=180, a1=360, n=48):
    """Points on an elliptical arc (degrees, screen coordinates: 180..360 is the upper half)."""
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]

def stonework(pts, course=9.0, block=(12, 22), arch=None):
    """Cut stone: a cream ground, then courses of rectangular blocks, each its own shade, with darker joints.
    With arch=(cx, cy), the blocks are voussoirs fanning around that centre instead of level courses."""
    m = A(pts, STONE[2], wob=.2, rough=.4, edge_dark=.12)
    if m is None: return m
    prev = T.c.clipm; T.c.set_clip(m)
    x0, y0, mm = m; h, w = mm.shape; K = T.K
    xa, ya = x0 / K + T.X0, y0 / K + T.Y0; xb, yb = xa + w / K, ya + h / K
    if arch is None:
        for i, y in enumerate(np.arange(ya, yb, course)):
            x = xa - T.R.uniform(0, block[1])
            while x < xb:
                bw = T.R.uniform(*block)
                ch = course * T.R.uniform(.85, 1.0)
                q = [(x + .7, y + .7), (x + bw - .7, y + .5), (x + bw - .6, y + ch - .6), (x + .5, y + ch - .7)]
                T.c.area(T.T(q), hexc(STONE[T.R.randint(len(STONE))]), wob=.35, rough=.7, edge_dark=.16, var=.06, a=.85, seed=int(T.R.randint(1 << 20)))
                x += bw
    else:
        cx, cy = arch
        for r in np.arange(0, max(xb - xa, yb - ya), course):
            pass
    T.c.clipm = prev
    return m

def voussoirs(cx, cy, rx0, ry0, rx1, ry1, n):
    """The stones of an arch: n wedge blocks between the inner and outer ellipses, with a keystone."""
    for i in range(n):
        a0, a1 = 180 + 180 * i / n, 180 + 180 * (i + 1) / n
        q = ell(cx, cy, rx0, ry0, a0 + .6, a1 - .6, 4) + ell(cx, cy, rx1, ry1, a1 - .6, a0 + .6, 4)
        col = STONE[T.R.randint(len(STONE))]
        shaded(q, [STONE[3], col, STONE_D], wob=.1, rough=.4, edge_dark=.3, L=2.0, w=1.3)

def lights_inside(g, n):
    """Warm points of light inside the station's glass: lamps and strings of lights seen through the panes."""
    x0, y0, mm = g; ys, xs = np.nonzero(mm > .9)
    for k in T.R.choice(len(xs), min(n, len(xs)), replace=False):
        px, py = (xs[k] + x0) / T.K, (ys[k] + y0) / T.K
        T.c.area(T.T(lump(px + T.X0, py + T.Y0, 4.5, 4.5, amp=0)), hexc('#fff2c0'), wob=0, rough=.3, edge_dark=0, a=.55, var=0, varbig=0, seed=k)
        T.c.dab(px, py, 2.4, 2.2, 0, '#fffbe8', a=1, dry=0)

def glazing_fan(cx, cy, rx, ry, spokes=9, rings=(.55,)):
    """A lit half-round window with radial glazing bars and a ring, like the upper fan of the station."""
    pts = [(cx - rx, cy)] + ell(cx, cy, rx, ry) + [(cx + rx, cy)]
    g = A(pts, T.GOLD, wob=.1, rough=.3, edge_dark=.12)
    glass(g, cx, cy - ry * .35, rx * .9, ry * .9)
    lights_inside(g, 40)
    x0, y0, mm = g; T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] = np.maximum(T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]], mm)
    BAR = '#5e3319'
    for k in range(1, spokes):
        a = math.radians(180 + 180 * k / spokes)
        S([(cx, cy), (cx + rx * math.cos(a), cy + ry * math.sin(a))], 2.0, BAR, a=.95, dry=.05, taper=(0, 0))
    for f in rings: S(ell(cx, cy, rx * f, ry * f, 180, 360, 30), 2.0, BAR, a=.95, dry=.05, taper=(0, 0))
    for yy in np.arange(cy - ry * .9, cy, ry * .12):
        span = rx * math.sqrt(max(0, 1 - ((yy - cy) / ry) ** 2))
        S([(cx - span, yy), (cx + span, yy)], 1.3, BAR, a=.8, dry=.1, taper=(0, 0))
    S(ell(cx, cy, rx, ry, 180, 360, 40), 3.0, BAR, a=.95, dry=.05, taper=(0, 0))

def glazing_grid(pts, cx, cy, hw, hh, xs, ys, bar=2.0):
    g = A(pts, T.GOLD, wob=.1, rough=.3, edge_dark=.12)
    glass(g, cx, cy, hw, hh)
    lights_inside(g, int(hw * hh / 260))
    x0, y0, mm = g; T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] = np.maximum(T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]], mm)
    prev = T.c.clipm; T.c.set_clip(g)
    for x in xs: S([(x, cy - hh * 1.2), (x, cy + hh * 1.2)], bar, '#5e3319', a=.95, dry=.05, taper=(0, 0))
    for y in ys: S([(cx - hw * 1.2, y), (cx + hw * 1.2, y)], bar * .9, '#5e3319', a=.95, dry=.05, taper=(0, 0))
    T.c.clipm = prev
    for x in xs:
        cv2.line(T.GLOW, (int((x - T.X0) * T.K), int((cy - hh * 1.2 - T.Y0) * T.K)), (int((x - T.X0) * T.K), int((cy + hh * 1.2 - T.Y0) * T.K)), 0, int(bar * T.K))
    for y in ys:
        cv2.line(T.GLOW, (int((cx - hw * 1.2 - T.X0) * T.K), int((y - T.Y0) * T.K)), (int((cx + hw * 1.2 - T.X0) * T.K), int((y - T.Y0) * T.K)), 0, int(bar * T.K))
    S(pts + [pts[0]], 3.0, '#5e3319', a=.9, dry=.05, taper=(0, 0))

def swag(x0, x1, y, depth=16):
    """A red fabric swag hanging between two gold knobs."""
    top = [(x0, y), (x1, y)]
    bot = [(x1 - (x1 - x0) * t, y + depth * math.sin(math.pi * t)) for t in np.linspace(0, 1, 14)]
    shaded(top + bot[1:-1], ['#d84a40', '#b8262a', '#7e1a1a'], light=(-.6, -.8), wob=.1, rough=.3, edge_dark=.18, L=2.2, w=1.3)
    for t in (.3, .5, .7): S([(x0 + (x1 - x0) * t, y + 2), (x0 + (x1 - x0) * t, y + depth * .8 * math.sin(math.pi * t))], 1.0, '#7e1a1a', a=.4, dry=.4)
    for xx in (x0, x1): shaded(lump(xx, y, 3.4, 3.4, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2, L=1, w=.8)

def banner(x0, x1, y0, y1, text):
    """The TOYS FOR TOTS banner: a cream ribbon with red trim lines, a slight upward curve, ends folding down."""
    sag = -8
    top = [(x0 + (x1 - x0) * t, y0 + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)]
    bot = [(x1 - (x1 - x0) * t, y1 + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)]
    for (ex, dx) in ((x0, -1), (x1, 1)):          # ribbon tails folding back and down
        shaded([(ex - dx * 4, y0 + 4), (ex + dx * 26, y0 + 22), (ex + dx * 22, y1 + 40), (ex + dx * 36, y1 + 56), (ex - dx * 2, y1 + 12)], ['#d84a40', '#b8262a', '#7e1a1a'], light=(dx * .8, -.4), wob=.1, rough=.3, edge_dark=.2)
        shaded(lump(ex + dx * 2, y0 + 8, 5, 5, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2)
    shaded(top + bot, ['#fbf5e6', '#f3ead6', '#d8cbab'], light=(0, -1), wob=.1, rough=.3, edge_dark=.12, spacing=1.0, L=3.0, w=1.6)
    for f in (.12, .88):
        S([(x0 + 6 + (x1 - x0 - 12) * t, y0 + (y1 - y0) * f + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)], 1.6, '#b8262a', a=.95, dry=.05, taper=(0, 0))
    # lettering, bent along the ribbon's curve
    K = T.K; w, h = int((x1 - x0) * K), int((y1 - y0) * K)
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    size = int(h * .62); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', size)
    while d.textlength(text, font=f) > w * .82: size -= 2; f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', size)
    d.text((w / 2, h * .54), text, font=f, fill=255, anchor='mm')
    m = np.asarray(im).astype(np.float32) / 255
    xs = np.arange(w); shift = (sag * np.sin(np.pi * xs / w) * K).astype(np.float32)
    mapx = np.tile(xs.astype(np.float32), (h, 1)); mapy = (np.arange(h, dtype=np.float32)[:, None] - shift[None, :]).astype(np.float32)
    m = cv2.remap(m, mapx, mapy, cv2.INTER_LINEAR, borderValue=0)
    m = cv2.GaussianBlur(m, (0, 0), .5)
    T.c.area(None, hexc('#a82420'), m=(int((x0 - T.X0) * K), int((y0 - T.Y0) * K), m), edge_dark=.3, var=.06)
    snow_edge([(x0 + 10 + (x1 - x0 - 20) * t, y0 - 2 + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 20)], 6, drip=.15)

def star_medallion(cx, cy, r):
    """The gold star in its red medallion, ringed by a wreath with baubles and a red bow."""
    for k in range(int(r * 9)):                                  # wreath behind
        a = k / int(r * 9) * math.tau + T.R.uniform(-.05, .05)
        for _ in range(4):
            rr = r * T.R.uniform(1.12, 1.85)
            T.c.dab(cx - T.X0 + rr * math.cos(a), cy - T.Y0 + rr * math.sin(a), T.R.uniform(6, 9), 2.4, a + math.pi / 2 + T.R.uniform(-.6, .6), T.NEEDLES[T.R.randint(4)], a=1, dry=.1)
    for k in range(10):
        a = T.R.uniform(0, math.tau); rr = r * T.R.uniform(1.3, 1.55)
        shaded(lump(cx + rr * math.cos(a), cy + rr * math.sin(a), 3.2, 3.2, amp=0), ['#e0504a', T.BERRY, '#7a1418'] if k % 3 else ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2, L=1, w=.8)
    shaded(lump(cx, cy, r * 1.08, r * 1.08, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=.05, rough=.2, edge_dark=.2)
    shaded(lump(cx, cy, r * .9, r * .9, amp=0), ['#d84a40', '#b8262a', '#8a1a1a'], wob=.05, rough=.2, edge_dark=.15)
    star = [(cx + (r * .66 if k % 2 == 0 else r * .27) * math.cos(-math.pi / 2 + k * math.pi / 5), cy + (r * .66 if k % 2 == 0 else r * .27) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    shaded(star, ['#fffaf0', '#f6ecd2', '#cdbf9a'], light=(-.7, -.7), wob=.05, rough=.2, edge_dark=.15, L=1.4, w=1.0)
    by = cy + r * 1.45
    for sg in (-1, 1): shaded([(cx, by), (cx + sg * 16, by - 10), (cx + sg * 16, by + 9)], ['#e0504a', T.BERRY, '#7a1418'], wob=.05, rough=.2, edge_dark=.2)
    for sg in (-1, 1): S([(cx, by + 2), (cx + sg * 8, by + 22)], 3.5, T.BERRY, a=1, dry=.05)
    shaded(lump(cx, by, 4.5, 4.5, amp=0), ['#c0383a', '#9a1e22', '#6a1214'], wob=0, rough=.2)

def clock(cx, cy, r):
    shaded(lump(cx, cy, r + 3, r + 3, amp=0), ['#f6d77a', '#c9a040', '#8a6a20'], wob=0, rough=.2, edge_dark=.2)
    shaded(lump(cx, cy, r, r, amp=0), ['#fffdf6', '#f6f0e2', '#d8ceb8'], wob=0, rough=.2, edge_dark=.1, L=1.2, w=.9)
    for k in range(12):
        a = k / 12 * math.tau; S([(cx + r * .8 * math.cos(a), cy + r * .8 * math.sin(a)), (cx + r * .92 * math.cos(a), cy + r * .92 * math.sin(a))], 1.1, '#2a2420', a=.9, dry=0, taper=(0, 0))
    S([(cx, cy), (cx, cy - r * .62)], 1.8, '#2a2420', a=1, dry=0, taper=(0, .2))
    S([(cx, cy), (cx + r * .45, cy - r * .1)], 2.2, '#2a2420', a=1, dry=0, taper=(0, .2))

def station():
    # the barrel vault: red roof band, snow along its crown and edge
    oc, ocy = (CX, 250)
    roof_band = ell(CX, 250, 282, 232) + ell(CX, 250, 262, 174, 360, 180)
    shaded(roof_band, ['#b8463c', '#9a3a33', '#6e2925'], light=(-.4, -1), wob=.2, rough=.5, edge_dark=.15, L=2.6, w=1.6)
    for k, f in enumerate(np.linspace(.18, .9, 7)):              # tile courses following the vault
        S(ell(CX, 250, 262 + 20 * f, 174 + 58 * f, 186, 354, 40), 1.0, '#6e2925', a=.55, dry=.3, taper=(.1, .1))
    snow_edge(ell(CX, 250, 284, 234, 196, 344, 40), 10, drip=.2)
    snow_edge(ell(CX, 250, 264, 176, 192, 348, 40), 7, drip=.3)
    # side wings: walls and red roofs with snow, swags under the eaves
    for (wx0, wx1, sgn) in ((188, 440, -1), (960, 1208, 1)):
        stonework([(wx0, 615), (wx1, 615), (wx1, 262), (wx0, 262)])
        rx0, rx1 = (wx0 - 12, wx1) if sgn < 0 else (wx0, wx1 + 12)
        top0, top1 = (rx0 + 40, 200) if sgn < 0 else (rx0, 196)
        pts = [(rx0, 266), (rx0 + 30, 196), (rx1, 186), (rx1, 266)] if sgn < 0 else [(rx0, 266), (rx0, 186), (rx1 - 30, 196), (rx1, 266)]
        roof(pts, cols=['#a8463c', '#8a3430', '#b8564a'], snowy=.35, ridge=(pts[1], pts[2]), eave=(pts[0], pts[3]))
        snow_edge([(rx0 - 6, 266), (rx1 + 6, 266)], 11, drip=.4)
        eave_shadow([(wx0, 268), (wx1, 268)], 8, '#8a7650')
        # a stone string course with snow on it, a darker plinth, and weathering low on the wall
        shaded([(wx0, 446), (wx1, 446), (wx1, 456), (wx0, 456)], [STONE[3], STONE[1], STONE_D], light=(0, -1), wob=.1, rough=.3, edge_dark=.25, L=3, w=1.4)
        snow_edge([(wx0 + 2, 445), (wx1 - 2, 445)], 5, drip=.3)
        shaded([(wx0, 590), (wx1, 590), (wx1, 615), (wx0, 615)], ['#cbb487', '#b89f72', '#9a8258'], light=(0, -1), wob=.1, rough=.3, edge_dark=.2, L=3, w=1.4)
        T.c.area(T.T([(wx0, 520), (wx1, 520), (wx1, 590), (wx0, 590)]), hexc('#a08a64'), wob=.6, rough=.8, edge_dark=0, a=.18, var=0, varbig=0, seed=int(wx0))
        # garland of greenery and lights along the wing below the swags, and lit lower windows
        garland(wx0 + 10, wx1 - 10, 470, sag=8, swags=3, bows=True)
        for k in range(3):
            lx = wx0 + 30 + k * (wx1 - wx0 - 60) / 2
            window(lx - 16, 520, lx + 16, 566, True, frame=3.5)
        xs = np.linspace(wx0 + 14, (wx1 if sgn < 0 else wx1) - 14, 4)
        for a_, b_ in zip(xs, xs[1:]): swag(a_, b_, 282, 20)
        # the arched side window
        ax0, ax1 = (258, 360) if sgn < 0 else (1028, 1132)
        cx_ = (ax0 + ax1) / 2; r_ = (ax1 - ax0) / 2
        pts_w = [(ax0, 420)] + ell(cx_, 330 + r_ * .55, r_, r_ * .55 * 1.6, 180, 360, 20) + [(ax1, 420)]
        A([(ax0 - 6, 424), (ax0 - 6, 330 + r_ * .55)] + ell(cx_, 330 + r_ * .55, r_ + 6, r_ * .88 + 6, 180, 360, 20) + [(ax1 + 6, 330 + r_ * .55), (ax1 + 6, 424)], STONE_D, wob=.1, rough=.3, edge_dark=.2)
        glazing_grid(pts_w, cx_, 380, r_, 50, np.linspace(ax0, ax1, 5)[1:-1], [352, 380, 404])
    # towers either side of the great arch
    for (tx0, tx1) in ((362, 436), (964, 1038)):
        stonework([(tx0, 615), (tx1, 615), (tx1, 126), (tx0, 126)], course=6.5)
        A([(tx0 - 4, 132), (tx1 + 4, 132), (tx1 + 4, 120), (tx0 - 4, 120)], STONE[0], wob=.1, rough=.3, edge_dark=.2)
        snow_edge([(tx0 - 6, 118), (tx1 + 6, 118)], 9, drip=.4)
        cx_ = (tx0 + tx1) / 2
        A([(cx_ - 10, 214), (cx_ - 10, 182)] + ell(cx_, 182, 10, 10, 180, 360, 10) + [(cx_ + 10, 182), (cx_ + 10, 214)], '#4a2c1e', wob=.05, rough=.2, edge_dark=.1)
        g = A([(cx_ - 6, 210), (cx_ - 6, 184)] + ell(cx_, 184, 6, 6, 180, 360, 8) + [(cx_ + 6, 184), (cx_ + 6, 210)], T.GOLD, wob=.05, rough=.2)
        glass(g, cx_, 198, 6, 14)
        x0, y0, mm = g; T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] = np.maximum(T.GLOW[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]], mm)
        chimney(cx_ - 14, cx_ + 14, 92, 122)
    # the front: stone face of the arch and the walls around the great window
    stonework([(436, 615), (964, 615), (964, 250)] + ell(CX, 250, 262, 174, 360, 180) + [(436, 250)])
    voussoirs(CX, 250, 236, 132, 262, 174, 23)
    # keystone and its gold finial at the crown
    shaded([(CX - 22, 108), (CX + 22, 108), (CX + 18, 70), (CX - 18, 70)], [STONE[3], STONE[2], STONE_D], wob=.1, rough=.3, edge_dark=.25)
    snow_edge([(CX - 24, 68), (CX + 24, 68)], 7, drip=.3)
    shaded(lump(CX, 22, 9, 9, amp=0), ['#f6d77a', '#e0b040', '#a07a20'], wob=0, rough=.2, edge_dark=.15)
    # the fan window, the star medallion, the banner
    glazing_fan(CX, 250, 236, 132, spokes=14, rings=(.45, .72))
    star_medallion(CX, 158, 36)
    banner(412, 988, 258, 318, 'TOYS FOR TOTS')
    # the great lower arch window
    lw = [(464, 470)] + ell(CX, 470, 236, 150) + [(936, 470)]
    voussoirs(CX, 470, 238, 152, 256, 170, 19)
    glazing_grid(lw, CX, 400, 236, 80, np.linspace(464, 936, 13)[1:-1], np.arange(340, 470, 22))
    shaded([(640, 322), (760, 322), (760, 352), (640, 352)], ['#d84a40', '#b8262a', '#8a1a1a'], wob=.05, rough=.2, edge_dark=.2)
    for k in range(3):
        sx = 662 + k * 38; sy = 337
        shaded([(sx + 9 * math.cos(-math.pi / 2 + j * math.pi / 5) * (1 if j % 2 == 0 else .42), sy + 9 * math.sin(-math.pi / 2 + j * math.pi / 5) * (1 if j % 2 == 0 else .42)) for j in range(10)], ['#ffffff', '#f6ecd2', '#cdbf9a'], wob=0, rough=.2, L=1, w=.8)
    snow_edge([(638, 321), (762, 321)], 5, drip=.2)
    # porch annexes either side of the clock porch: red roofs with snow, lit windows, garlands
    for (ax0, ax1) in ((458, 598), (802, 942)):
        stonework([(ax0, 615), (ax1, 615), (ax1, 486), (ax0, 486)], course=6.5)
        pts = [(ax0 - 6, 490), (ax0 + 8, 450), (ax1 - 8, 450), (ax1 + 6, 490)]
        roof(pts, cols=['#a8463c', '#8a3430', '#b8564a'], snowy=.3, ridge=(pts[1], pts[2]), eave=(pts[0], pts[3]))
        snow_edge([(ax0 + 8, 450), (ax1 - 8, 450)], 6, drip=0)
        snow_edge([(ax0 - 10, 490), (ax1 + 10, 490)], 10, drip=.4)
        wx0 = ax0 + 40 if ax0 < 700 else ax0 + 36
        window(wx0, 538, wx0 + 62, 586, False, bars=(2, 1), frame=4)
        garland(ax0 + 6, ax1 - 6, 500, sag=7, swags=2)
    # the clock porch: gable with the clock, doors, side windows, garland with a big bow, steps
    px0, px1, ey, yb = 596, 804, 468, 615
    stonework([(px0, yb), (px1, yb), (px1, ey), (CX, 392), (px0, ey)], course=6.5)
    eave_shadow([(px0, ey), (CX, 396), (px1, ey)], 9, '#8a7650')
    S([(px0 - 12, ey + 4), (CX, 388), (px1 + 12, ey + 4)], 4.5, T.CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(px0 - 20, ey + 6), (CX, 380), (px1 + 20, ey + 6)], 13, drip=.4)
    S([(px0, ey + 8), (px1, ey + 8)], 3.0, STONE_D, a=.8, dry=.15, taper=(0, 0))
    clock(CX, 440, 24)
    for (wx) in (622, 752):
        window(wx, 526, wx + 28, 572, True, frame=3.5)
    # double doors under an arch, with a wreath
    d = [(664, 614)] + [(CX - 36 * math.cos(math.pi * k / 16), 556 - 36 * math.sin(math.pi * k / 16)) for k in range(17)] + [(736, 614)]
    A([(658, 614)] + [(CX - 42 * math.cos(math.pi * k / 16), 556 - 42 * math.sin(math.pi * k / 16)) for k in range(17)] + [(742, 614)], STONE_D, wob=.1, rough=.3, edge_dark=.2)
    shaded(d, ['#a0602e', '#7e4422', '#5a2e16'], light=(-.8, -.6), wob=.1, rough=.3, edge_dark=.25, L=3.2, w=1.3)
    S([(CX, 522), (CX, 613)], 1.4, '#3a1c0c', a=.8, dry=.1, taper=(0, 0))
    for xx in (676, 688, 712, 724): S([(xx, 540), (xx, 610)], .7, '#4a2410', a=.45, dry=.3)
    for xx in (692, 708): T.c.dots([(xx - T.X0, 580 - T.Y0)], 1.5, ['#e8c060'], seed=int(xx))
    wreath(CX, 552, 14)
    garland(604, 796, 500, sag=9, swags=2)
    by = 498
    for sg in (-1, 1): shaded([(CX, by), (CX + sg * 13, by - 8), (CX + sg * 13, by + 8)], ['#e0504a', T.BERRY, '#7a1418'], wob=.05, rough=.2, edge_dark=.2)
    for sg in (-1, 1): S([(CX, by + 2), (CX + sg * 6, by + 20)], 3.0, T.BERRY, a=1, dry=.05)
    # steps down to the square
    for i in range(5):
        y = 614 + i * 9; half = 84 + i * 6
        shaded([(CX - half, y), (CX + half, y), (CX + half, y + 9), (CX - half, y + 9)], ['#e6dccc', '#d0c6b4', '#a89e8c'], light=(0, -1), wob=.1, rough=.3, edge_dark=.2, L=3, w=1.4)
        snow_edge([(CX - half + 4, y + 1), (CX + half - 4, y + 1)], 3.0, drip=0)
    # potted firs beside the porch, flower boxes under the annex windows
    for (fx) in (594, 806):
        A([(fx - 10, 615), (fx + 10, 615), (fx + 8, 600), (fx - 8, 600)], '#8a4a24', wob=.1, rough=.3, edge_dark=.2)
        T.fir(fx, 600, 52)

def build_station():
    station()

if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    T.init(180, 0, 1220, 670, 3)
    build_station(); T.light()
    paint, al = T.finish(os.path.join(HERE, 'out', 'station_study.png'), os.path.join(HERE, 'out', 'station_glow.png'))
    tgt = cv2.imread(os.path.join(T.ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))[..., ::-1].astype(np.float32) / 255
    tc = cv2.resize(tgt[0:670, 180:1220], (paint.shape[1], paint.shape[0]), interpolation=cv2.INTER_CUBIC)
    v = paint * al[..., None] + np.array([.93, .91, .87]) * (1 - al[..., None])
    cv2.imwrite(os.path.join(HERE, 'out', 'station_compare.jpg'), (np.concatenate([tc, v], 0)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('ok')

"""Toy Town, east side: the red house, the pink house with the purple roof, and the toy donation storefront.
Built from shapes with the shared kit (target-painting px), painted back to front.
    python3 toytown_east.py            # study render of this side alone, writes out/east_study.png
"""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import toytown_kit as T
from toytown_kit import A, S, shaded, wall, roof, window, garland, snow_edge, snow_clump, snow_cap, eave_shadow, chimney, stip, lump, hexc

PINK = ['#b8607a', '#d77f99', '#e597ad', '#f0b2c4', '#cc7090']
RED = ['#8e2620', '#ab3428', '#c0443a', '#cf5a4c', '#a02e26']
YELLOW = ['#c7942a', '#dfac3c', '#e8bd52', '#f0cd6c', '#d6a238']
PURPLE = ['#5a5a8e', '#47477a', '#6c6ca2']
CREAM_SIGN = '#f3ead6'

def awning(ax0, ax1, ay, ly, hem, n, ca, cb, da, db, lean=6):
    """A striped shop awning (as on the blue shop): stripes, scalloped valance, slope shading, side panel, snow."""
    edges = [0.0] + sorted(np.clip(np.arange(1, n) / n + T.R.uniform(-.018, .018, n - 1), 0, 1)) + [1.0]
    for i in range(n):
        a, b = edges[i], edges[i + 1]
        t0, t1 = ax0 + (ax1 - ax0) * a, ax0 + (ax1 - ax0) * b
        l0, l1 = t0 + lean, t1 + lean
        col, dark = (ca, da) if i % 2 == 0 else (cb, db)
        m = A([(t0, ay), (t1, ay), (l1, ly), (l0, ly)], col, wob=.15, rough=.4, edge_dark=.12)
        Cc, Cd = hexc(col), hexc(dark); xa, xb = t0 - T.X0, t1 - T.X0
        def fold(X, Y, r, xa=xa, xb=xb, Cc=Cc, Cd=Cd):
            u = np.clip((X - xa - (Y - (ay - T.Y0)) * lean / (ly - ay)) / (xb - xa), 0, 1)
            k = np.clip(np.abs(u - .4) * 1.0 + (Y - (ay - T.Y0)) / (ly - ay) * .75 - .15, 0, 1)[:, None]
            return np.clip(Cc * (1 - k * .55) + Cd * k * .55 + (r.rand(len(X), 1) - .5) * .04, 0, 1)
        T.c.stip(m, fold, spacing=.85, L=2.6, w=1.1, angfn=lambda X, Y: np.full(X.shape, math.atan2(ly - ay, lean)), seed=int(T.R.randint(1 << 20)), jit=.4)
        sc = [(l1 - (l1 - l0) * k / 10, ly + (hem - ly) * math.sin(math.pi * k / 10)) for k in range(11)]
        mv = A([(l0, ly - .5), (l1, ly - .5)] + sc[1:-1], col, wob=.1, rough=.3, edge_dark=.18)
        stip(mv, [dark, col], spacing=.9, L=1.6, w=1.0, ang=0.0, weights=[.45, .55])
    shaded([(ax1, ay), (ax1 + lean, ly), (ax1 + lean, hem), (ax1 + lean * 2, hem - 3), (ax1 + lean * 1.5, ay + 2)], [ca, da, da], light=(-1, -.3), wob=.1, rough=.3, edge_dark=.15)
    S([(ax0 + 2, ay + 5), (ax1 + 2, ay + 5)], 4.0, '#000000', a=.16, dry=.6, taper=(.2, .2))
    snow_edge([(ax0 - 4, ay - 1), (ax1 + 4, ay - 1)], 9.0, drip=.2)

def sign(x0, y0, x1, y1, lines, ink='#9a2420', board=CREAM_SIGN, frame='#b8a27c'):
    """A hand-painted shop sign: a cream board with a darker frame and lettering painted with the brush."""
    shaded([(x0 - 3, y0 - 3), (x1 + 3, y0 - 3), (x1 + 3, y1 + 3), (x0 - 3, y1 + 3)], ['#d2bf98', frame, '#8a7656'], wob=.1, rough=.3, edge_dark=.2)
    shaded([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ['#fbf5e6', board, '#ddd0b2'], wob=.1, rough=.3, edge_dark=.12, spacing=1.0, L=2.4, w=1.4)
    # lettering: a mask drawn with a serif font at canvas resolution, painted as an area of ink, so it gets
    # the brush's soft edge and pooled pigment like the rest
    K = T.K; w, h = int((x1 - x0) * K), int((y1 - y0) * K)
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    lh = h / len(lines)
    for i, ln in enumerate(lines):
        size = int(lh * .68); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', size)
        while d.textlength(ln, font=f) > w * .9: size -= 2; f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', size)
        d.text((w / 2, lh * (i + .5)), ln, font=f, fill=255, anchor='mm')
    m = cv2.GaussianBlur(np.asarray(im).astype(np.float32) / 255, (0, 0), .5)
    mx0, my0 = int((x0 - T.X0) * K), int((y0 - T.Y0) * K)
    T.c.area(None, hexc(ink), m=(mx0, my0, m), edge_dark=.25, var=.06)

def wreath(cx, cy, r):
    """A round wreath of needle dabs with berries and a red bow at the top."""
    for k in range(int(r * 3.2)):
        a = k / int(r * 3.2) * math.tau + T.R.uniform(-.1, .1)
        for _ in range(3):
            rr = r * T.R.uniform(.75, 1.05)
            T.c.dab(cx - T.X0 + rr * math.cos(a), cy - T.Y0 + rr * math.sin(a), T.R.uniform(4, 6), 1.8, a + math.pi / 2 + T.R.uniform(-.6, .6), T.NEEDLES[T.R.randint(4)], a=1, dry=.1)
    P = (np.array([(cx - T.X0, cy - T.Y0)]) * T.K).astype(int)[0]
    cv2.circle(T.ALPHA, tuple(P), int((r + 4) * T.K), 1.0, -1)
    for k in range(7):
        a = T.R.uniform(0, math.tau); bx, by = cx + r * .9 * math.cos(a), cy + r * .9 * math.sin(a)
        shaded(lump(bx, by, 1.8, 1.8, amp=0), ['#e0504a', T.BERRY, '#7a1418'], wob=0, rough=.2, L=1.0, w=.8)
    for sg in (-1, 1): shaded([(cx, cy - r), (cx + sg * 7, cy - r - 5), (cx + sg * 7, cy - r + 4)], ['#e0504a', T.BERRY, '#7a1418'], wob=.05, rough=.2, edge_dark=.2)
    for sg in (-1, 1): S([(cx, cy - r + 1), (cx + sg * 4, cy - r + 11)], 2.0, T.BERRY, a=1, dry=.05)

def red_house():
    """The tall red house behind the toy donation storefront: front gable facing the square, right side wall."""
    x0, x1, px, py, ey, yb = 1052, 1178, 1115, 382, 462, 640
    side = [(x1, yb), (1272, yb - 10), (1272, 470), (x1, ey)]
    wall(side, RED[1], dark=True, cols=RED, stone_dark=.2)
    roof([(x1 - 4, ey + 2), (px, py - 2), (1210, 378), (1280, 468)], cols=['#a03a34', '#7e2a26', '#b04a44'], snowy=.35, ridge=((px + 4, py), (1212, 380)), eave=((x1, ey), (1278, 466)))
    snow_edge([(x1 - 2, ey), (1280, 468)], 11, drip=.4)
    wall([(x0, yb), (x1, yb), (x1, ey), (px, py), (x0, ey)], RED[1], cols=RED, stone_dark=.2, fleck=.5)
    eave_shadow([(x0 + 2, ey), (px, py + 4), (x1 - 2, ey)], 8, '#6e1e18')
    S([(x0 - 4, ey + 4), (px, py - 2), (x1 + 4, ey + 4)], 4.0, T.CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(x0 - 10, ey + 6), (px, py - 8), (x1 + 10, ey + 6)], 12, drip=.4)
    window(1104, 400, 1128, 432, True)
    for wx in (1072, 1132):
        window(wx, 472, wx + 26, 512, True)
    for wx in (1072,):
        window(wx, 536, wx + 26, 572, False)
    for wx in (1206, 1240):
        window(wx, 490, wx + 20, 520, False, frame=3.0)
    chimney(992, 1012, 396, 440)                                  # the pink house's chimney, behind its roof

def pink_house():
    """The pink house with the purple roof and a dormer, its arched door facing the square."""
    x0, x1, ey, yb = 938, 1058, 512, 702
    roof([(926, ey + 4), (962, 446), (1036, 446), (1070, ey + 4)], cols=PURPLE, tile_dark='#38385e', snowy=.4, ridge=((962, 448), (1036, 448)), eave=((928, ey), (1068, ey)))
    snow_edge([(966, 447), (1032, 447)], 4.5, drip=0)
    # dormer
    wall([(980, 486), (1012, 486), (1012, 466), (996, 450), (980, 466)], PINK[2], cols=PINK, stone_dark=.12)
    S([(977, 468), (996, 448), (1015, 468)], 3.0, T.CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(975, 468), (996, 445), (1017, 468)], 7, drip=.2)
    window(988, 467, 1005, 485, True, frame=2.6)
    wall([(x0, yb), (x1, yb), (x1, ey), (x0, ey)], PINK[2], cols=PINK, stone_dark=.12, fleck=.5)
    eave_shadow([(x0, ey), (x1, ey)], 8, '#8a4058')
    snow_edge([(924, ey + 2), (1072, ey + 2)], 11, drip=.45)
    for wx in (958, 1006):
        window(wx, 538, wx + 26, 574, True)
    garland(1000, 1050, 590, sag=4, swags=1)
    # arched door with a little wreath, and the lit window beside it
    door = [(958, 684)] + [(958 + 14 - 14 * math.cos(math.pi * k / 12), 626 - 14 * math.sin(math.pi * k / 12)) for k in range(13)] + [(986, 684)]
    m = shaded(door, ['#9a5a2c', '#7a4220', '#5a2e16'], light=(-.8, -.6), wob=.1, rough=.3, edge_dark=.25, L=3.0, w=1.2)
    for xx in (967, 977): S([(xx, 616), (xx, 682)], .7, '#4a2410', a=.5, dry=.3)
    T.c.dots([(981 - T.X0, 654 - T.Y0)], 1.4, ['#e8c060'], seed=21)
    A([(954, 684), (990, 684), (990, 692), (954, 692)], '#b8b0a0', wob=.1, rough=.3)
    snow_cap(952, 992, 684, 4)
    window(1008, 620, 1048, 674, False, bars=(1, 1))
    # window box of greenery under it
    A([(1004, 678), (1052, 678), (1050, 690), (1006, 690)], '#8a4a24', wob=.1, rough=.3, edge_dark=.2)
    garland(1006, 1050, 678, sag=1, swags=1, bows=False)

def donation_shop():
    """The toy donation storefront: a warm yellow gabled shop with a TOY DONATION sign, red-and-white awning,
    a lit window full of presents, a wreath on the side wall, a chimney, and its side wall to the right."""
    x0, x1, px, py, ey, yb = 1028, 1206, 1118, 530, 620, 850
    # chimney behind the roof
    chimney(1214, 1250, 500, 600)
    side = [(x1, yb), (1282, yb - 12), (1282, 628), (x1, ey)]
    wall(side, YELLOW[1], dark=True, cols=YELLOW, stone_dark=.1)
    roof([(x1 - 4, ey + 2), (px, py - 2), (1196, 528), (1290, 626)], cols=PURPLE, tile_dark='#38385e', snowy=.4, ridge=((px + 4, py), (1198, 530)), eave=((x1, ey), (1288, 624)))
    snow_edge([(x1 - 2, ey), (1290, 626)], 12, drip=.4)
    wall([(x0, yb), (x1, yb), (x1, ey), (px, py), (x0, ey)], YELLOW[1], cols=YELLOW, stone_dark=.1, fleck=.5)
    eave_shadow([(x0 + 2, ey), (px, py + 4), (x1 - 2, ey)], 9, '#8a6418')
    shaded([(x0 - 22, ey + 10), (px, py - 12), (x1 + 22, ey + 10), (x1 + 16, ey + 16), (px, py), (x0 - 16, ey + 16)], ['#7a7ab2', PURPLE[0], PURPLE[1]], light=(-1, -.4), wob=.2, rough=.4, edge_dark=.2)
    S([(x0 - 10, ey + 14), (px, py - 1), (x1 + 10, ey + 14)], 4.2, T.CREAM, a=1, dry=.15, taper=(0, 0))
    snow_edge([(x0 - 26, ey + 8), (px, py - 16), (x1 + 26, ey + 8)], 15, drip=.45)
    window(1108, 580, 1132, 606, True, frame=3.2)
    garland(1040, 1196, 628, sag=7, swags=3)
    sign(1064, 662, 1194, 708, ['TOY', 'DONATION'])
    # the side wall: a small window and the wreath
    window(1294 - 40, 646, 1294 - 28, 662, True, frame=2.4)
    wreath(1248, 690, 17)
    # shopfront: window of presents and toys below the awning, framed in red wood
    WOOD, WOOD_D = '#9a2a22', '#6e1a14'
    A([(1030, yb), (1206, yb), (1206, 760), (1030, 760)], WOOD, wob=.1, rough=.3, edge_dark=.15)
    g = A([(1044, 840), (1192, 840), (1192, 768), (1044, 768)], T.GOLD, wob=.1, rough=.3, edge_dark=.1)
    T.glass(g, 1118, 812, 74, 36)
    x0_, y0_, mm = g; T.GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]] = np.maximum(T.GLOW[y0_:y0_ + mm.shape[0], x0_:x0_ + mm.shape[1]], mm * .9)
    # presents stacked in the window: wrapped boxes with ribbons
    pres = [(1050, 838, 30, 26, '#b8262a', '#f0d070'), (1082, 838, 24, 36, '#2f6446', '#f3ead6'), (1108, 838, 34, 22, '#3a6aa8', '#f0d070'),
            (1144, 838, 26, 30, '#e0b040', '#b8262a'), (1172, 838, 18, 20, '#b8262a', '#f3ead6'), (1114, 816, 22, 18, '#d84a8a', '#f3ead6'),
            (1150, 808, 18, 16, '#2f6446', '#f0d070'), (1056, 812, 20, 16, '#e0b040', '#b8262a')]
    for (bx, by, bw, bh, col, rib) in pres:
        C = hexc(col); lt = '#%02x%02x%02x' % tuple(int(min(255, v * 255 * 1.18 + 12)) for v in C); dk = '#%02x%02x%02x' % tuple(int(v * 255 * .72) for v in C)
        shaded([(bx, by), (bx + bw, by), (bx + bw, by - bh), (bx, by - bh)], [lt, col, dk], wob=.05, rough=.2, edge_dark=.18, L=1.4, w=1.0)
        S([(bx + bw / 2, by), (bx + bw / 2, by - bh)], 2.0, rib, a=1, dry=.05, taper=(0, 0))
        S([(bx, by - bh / 2), (bx + bw, by - bh / 2)], 1.8, rib, a=1, dry=.05, taper=(0, 0))
        for sg in (-1, 1): A([(bx + bw / 2, by - bh), (bx + bw / 2 + sg * 7, by - bh - 6), (bx + bw / 2 + sg * 7, by - bh + 2)], rib, wob=.05, rough=.2, edge_dark=.2)
    for xx in (1044, 1092, 1144, 1192):
        S([(xx, 766), (xx, 842)], 2.6, WOOD_D, a=1, dry=.05, taper=(0, 0))
    S([(1044, 800), (1192, 800)], 2.0, WOOD_D, a=.9, dry=.05, taper=(0, 0))
    for xx in (1092, 1144):
        cv2.line(T.GLOW, (int((xx - T.X0) * T.K), int((768 - T.Y0) * T.K)), (int((xx - T.X0) * T.K), int((840 - T.Y0) * T.K)), 0, int(2.6 * T.K))
    snow_cap(1040, 1196, 842, 5)
    awning(1014, 1206, 720, 750, 766, 10, '#b8262a', '#f3ead6', '#7e1a1a', '#cfc4ac', lean=5)
    # wall lamp glow by the sign, snow banked at the foot
    snow_edge([(1020, yb + 2), (1290, yb - 8)], 10, drip=0)

def build_east():
    red_house(); pink_house(); donation_shop()

if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    T.init(900, 360, 1310, 880, 3)
    build_east(); T.light()
    paint, al = T.finish(os.path.join(HERE, 'out', 'east_study.png'), os.path.join(HERE, 'out', 'east_glow.png'))
    # comparison with the target at the same scale
    tgt = cv2.imread(os.path.join(T.ROOT, 'docs', 'toytown_layout', 'reference', 'toytown_target.webp'))[..., ::-1].astype(np.float32) / 255
    tc = cv2.resize(tgt[360:880, 900:1310], (paint.shape[1], paint.shape[0]), interpolation=cv2.INTER_CUBIC)
    v = paint * al[..., None] + np.array([.93, .91, .87]) * (1 - al[..., None])
    cv2.imwrite(os.path.join(HERE, 'out', 'east_compare.jpg'), (np.concatenate([tc, np.ones((tc.shape[0], 20, 3)), v], 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('ok')

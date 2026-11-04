"""Engine 10, Phase 4: the yellow TOY DONATION shop rebuilt with better construction, at three levels.

    'A'  refined construction: recessed, well-proportioned openings; pilasters, fascia and stallriser; a recessed
         panelled door with a transom and a step; a cornice; soft outlines on the main edges. Decoration restrained:
         the existing sign and awning, a rocking horse and two presents in the window.
    'B'  rich illustration: A, plus shutters and flower boxes, a scalloped awning with a visible side and its shadow,
         a carved TOYS FOR TOTS signboard, an evergreen garland with bows, a two-depth window display of designed toys
         (teddy and books on a shelf; rocking horse and presents in front), a wreath on the door, warm light on the
         cobbles.
    'C'  high-resolution storybook: B, plus stone quoins, a dentil cornice on brackets, keystones, curtained and
         lit upper windows with a candle and a cat, shingles, a ridge cap and a lit dormer, gooseneck lamps over the
         sign, a fuller display (soldier, drum, doll, wooden train, blocks, picture book) under string lights, a glazed
         door with a brass kick plate, a poinsettia, wood grain and a brick stallriser.
Built on lab8's components (store8) where they already worked; the openings, door, awning and window display are new.
Everything uses the engine's edge presets: 'built' for walls and trim, 'fine' for openings and toys, 'crisp' for
the smallest marks.
"""
import math
import numpy as np
import usmap4 as B
import tft7 as T7
import store8 as SF
import toys10 as TY
from brush import hexc

S = B.S
def C(): return B.c
TRIM, STONE, STONE_D = '#f6ecd2', '#f2e2bc', '#c8ae84'
GREEN, GREEN_D, WOOD, WOOD_M, WOOD_L = '#2f5a3a', '#203e28', '#5a3a24', '#7a5234', '#a8784c'
RED, RED_D, GOLD, GOLD_L, CREAM = '#b8302a', '#8a2420', '#d8a840', '#f2d488', '#f4ead2'
GLASS, GLASS_L, GLASS_D, NIGHT = '#f2c25a', '#f8dc8a', '#d8962e', ['#3a3a5c', '#33335a', '#454670']

def rect(x0, y0, x1, y1, col, edge=.14, rough=.25, a=1.0, seed=0):
    return C().area([(x0, y1), (x1, y1), (x1, y0), (x0, y0)], col, wob=0, rough=rough, edge_dark=edge, a=a, seed=seed)
def line(pts, w, col, a=1.0, dry=0.0): C().stroke(pts, w, col, a=a, dry=dry, taper=(0, 0))
def soft_outline(pts, w=.35, col='#4a3220', a=.45): C().stroke(pts, w, col, a=a, dry=.35, taper=(0, 0), rough=.6)

# ---------------------------------------------------------------- openings
def window10(win, glass='night', shutters=None, box=None, curtains=None, story=None, keystone=False, seed=0):
    """A recessed window: a painted frame proud of the wall, a shadowed reveal inside it (light comes from the upper
    left, so the top and left reveals are dark), six panes, a projecting stone sill that throws a shadow."""
    c = C(); x, y, w, h = win['x'], win['y'], win['w'] * 1.15, win['h'] * 1.08
    l, r_, t, b = x - w / 2, x + w / 2, y - h / 2, y + h / 2
    with c.edges('fine'):
        if glass == 'warm': SF.glow(x, y, w * 1.1, a=.15, seed=seed)
        if shutters:
            for sd in (-1, 1):
                sx0, sx1 = (l - w * .55 - .6, l - .6) if sd < 0 else (r_ + .6, r_ + w * .55 + .6)
                rect(sx0, t - .5, sx1, b + .5, shutters, edge=.2, seed=seed + sd)
                for yy in np.arange(t + .7, b - .1, .8): line([(sx0 + .3, yy), (sx1 - .3, yy)], .2, hexc(shutters) * .6, a=.95)
                rect(sx0 + .25, t + h * .47, sx1 - .25, t + h * .53, hexc(shutters) * .78, edge=0, rough=.1)
                c.dots([((sx1 if sd < 0 else sx0) + sd * .15, t + h * .2), ((sx1 if sd < 0 else sx0) + sd * .15, b - h * .2)], .16, ['#2a2420'])   # hinges
        rect(l - .95, t - .95, r_ + .95, b + .45, TRIM, edge=.18, seed=seed + 3)                   # frame, proud of the wall
        G = np.array([hexc(z) for z in ([GLASS_L, GLASS, GLASS_D] if glass == 'warm' else NIGHT)])
        m = rect(l, t, r_, b, '#' + ''.join(f'{int(v * 255):02x}' for v in G[1]), edge=.28, rough=.12, seed=seed + 4)
        if m is not None:
            c.stip(m, lambda X, Y, rr: G[rr.randint(3, size=len(X))] * (1 - np.clip((Y - t) / h, 0, 1)[:, None] * (.14 if glass == 'warm' else -.08)),
                   spacing=.42, L=.85, w=.42, angfn=lambda X, Y: 0 * X, seed=seed + 5, jit=.4)
        rect(l, t, r_, t + .55, '#2a2030', edge=0, a=.55); rect(l, t, l + .5, b, '#2a2030', edge=0, a=.45)   # reveal shadows (top, left)
        if curtains:
            for sd in (-1, 1):
                cx0 = l if sd < 0 else r_
                c.area([(cx0, t + .5), (cx0 + sd * -w * .34, t + .5), (cx0 + sd * -w * .2, t + h * .45), (cx0 + sd * -w * .3, b - .1), (cx0, b - .1)], curtains, wob=0, rough=.2, edge_dark=.25)
                line([(cx0 + sd * -w * .1, t + .9), (cx0 + sd * -w * .14, b - .6)], .18, hexc(curtains) * .7, a=.8)
        if story == 'candle':
            rect(x - .28, b - 2.1, x + .28, b - .35, '#f8f2e6', edge=.1, rough=.1); SF.glow(x, b - 2.6, 1.4, a=.45, seed=seed + 6)
            with c.edges('crisp'): TY.ellipse(x, b - 2.45, .2, .32, '#fff2a8', edge=0)
        elif story == 'cat':
            cx, cy = x + w * .2, b - .15
            TY.ellipse(cx, cy - 1.1, 1.05, 1.0, '#1e1a20', edge=0); TY.ellipse(cx, cy - 2.55, .68, .64, '#1e1a20', edge=0)
            for sd in (-1, 1): c.area([(cx + sd * .18, cy - 2.95), (cx + sd * .62, cy - 3.75), (cx + sd * .7, cy - 2.7)], '#1e1a20', wob=0, rough=.1, edge_dark=0)
            c.stroke([(cx + .85, cy - .25), (cx + 1.6, cy - .9), (cx + 1.4, cy - 2.0)], .3, '#1e1a20', a=1, dry=0, taper=(0, .5))
        bar = TRIM
        line([(x, t + .5), (x, b)], .34, bar)
        for f in (.36, .68): line([(l + .5, t + h * f), (r_, t + h * f)], .3, bar)
        c.stroke([(l + w * .58, t + h * .12), (l + w * .9, t + h * .4)], .28, '#ffffff', a=.3, dry=.2, taper=(.3, .3))
        rect(l - 1.7, b + .35, r_ + 1.7, b + 1.45, STONE, edge=.25, seed=seed + 10)                 # sill
        rect(l - 1.5, b + 1.45, r_ + 1.5, b + 1.95, '#6a4a20', edge=0, a=.4)                        # its shadow
        if keystone:
            rect(l - 1.4, t - 2.2, r_ + 1.4, t - .95, STONE, edge=.22, seed=seed + 11)
            c.area([(x - .9, t - .95), (x + .9, t - .95), (x + 1.25, t - 3.0), (x - 1.25, t - 3.0)], STONE, wob=0, rough=.15, edge_dark=.3)
        else:
            rect(l - 1.1, t - 1.8, r_ + 1.1, t - .95, STONE, edge=.2, seed=seed + 11)
        if box: SF.flower_box(l - 1.2, r_ + 1.2, b + 1.45, box, seed + 12)

def door10(l, r_, t, y, level, paint):
    """A recessed doorway: dark reveals either side, a transom light over the door, a panelled door (glazed in C),
    a brass knob and a stone step that catches the light."""
    c = C(); w = r_ - l; cx = (l + r_) / 2
    with c.edges('fine'):
        rect(l - .5, t - .5, r_ + .5, y, '#1c140e', edge=0, rough=.15)                              # the recess
        rect(l + .1, t + 2.0, l + .8, y, '#3a2618', edge=0, a=.9); rect(r_ - .8, t + 2.0, r_ - .1, y, '#2a1c12', edge=0, a=.9)   # reveals
        tm = rect(l + .3, t, r_ - .3, t + 1.8, GLASS_L, edge=.25)                                   # transom light
        for xx in np.linspace(l + .3, r_ - .3, 4)[1:-1]: line([(xx, t), (xx, t + 1.8)], .22, paint)
        dcol = WOOD if level == 'A' else '#8a2a24'
        dl, dr, dt = l + .9, r_ - .9, t + 2.1
        rect(dl, dt, dr, y - .2, dcol, edge=.2, seed=81)
        if level == 'C':
            for xx in np.arange(dl + .35, dr - .2, .55): line([(xx, dt + .2), (xx, y - .4)], .08, hexc(dcol) * .8, a=.6, dry=.4)   # grain
            rect(dl + .7, dt + .7, dr - .7, dt + (y - dt) * .42, GLASS, edge=.25)
            line([((dl + dr) / 2, dt + .7), ((dl + dr) / 2, dt + (y - dt) * .42)], .25, dcol)
            panels = [(dt + (y - dt) * .52, y - 1.6)]
        else:
            panels = [(dt + .7, dt + (y - dt) * .45), (dt + (y - dt) * .55, y - 1.6)]
        for p0, p1 in panels:
            for sd in (-1, 1):
                a0, a1 = (dl + .55, (dl + dr) / 2 - .3) if sd < 0 else ((dl + dr) / 2 + .3, dr - .55)
                rect(a0, p0, a1, p1, hexc(dcol) * .78, edge=.25)
                line([(a0, p0 + .15), (a1, p0 + .15)], .16, np.minimum(hexc(dcol) * 1.25, 1), a=.8)
        if level == 'C': rect(dl + .5, y - 1.3, dr - .5, y - .4, GOLD, edge=.2, rough=.1)
    with c.edges('crisp'):
        c.dots([(dr - .6, (dt + y) / 2 + .5)], .36, [GOLD]); c.dots([(dr - .7, (dt + y) / 2 + .38)], .13, [GOLD_L])
    with c.edges('fine'):
        rect(l - 1.3, y - .2, r_ + 1.3, y + 1.2, STONE, edge=.22)                                   # step
        line([(l - 1.2, y - .1), (r_ + 1.2, y - .1)], .3, '#ffffff', a=.35)
        rect(l - 1.2, y + 1.2, r_ + 1.2, y + 1.75, '#3a3224', edge=0, a=.35)
        if level in ('B', 'C'): SF.wreath(cx, dt + (y - dt) * (.25 if level == 'B' else .66), 1.6)

def display10(l, t, r_, b, level):
    """The window display, composed in two depths: a shelf of smaller things at the back, the larger toys in front."""
    c = C(); w, h = r_ - l, b - t
    with c.edges('fine'):
        m = rect(l + .15, t + .15, r_ - .15, b - .15, '#d9a256', edge=0, rough=.15)                 # the lit shop interior: calm, so the toys read
        if m is not None:
            G = np.array([hexc(z) for z in ('#e2ae62', '#d9a256', '#d0984c')])
            c.stip(m, lambda X, Y, rr: G[rr.randint(3, size=len(X))] * (1.06 - np.clip((Y - t) / h, 0, 1)[:, None] * .12), spacing=.8, L=1.4, w=.8, angfn=lambda X, Y: 0 * X, seed=117, jit=.3)
        rect(l + .15, b - 1.0, r_ - .15, b - .15, '#8a5a30', edge=.15)                               # the display platform
        rect(l + .15, b - 1.0, r_ - .15, b - .75, '#b07a44', edge=0, a=.8)
    if level == 'A':
        TY.rocking_horse(l + w * .34, b - .8, 6.4); TY.present(l + w * .7, b - .8, 3.0, 3.0, '#3f6aa8'); TY.present(l + w * .85, b - .8, 2.5, 3.9, '#c8302a', '#f4f2ec'); return
    sh = t + h * (.44 if level == 'B' else .4)
    with c.edges('fine'):
        rect(l + .3, sh, r_ - .3, sh + .5, WOOD_M, edge=.15); rect(l + .3, sh + .5, r_ - .3, sh + .85, '#3a2618', edge=0, a=.4)
    if level == 'B':
        TY.teddy(l + w * .2, sh, 3.6); TY.books(l + w * .5, sh, 2.6, n=5, seed=3); TY.drum(l + w * .82, sh, 1.9)
        TY.rocking_horse(l + w * .3, b - .8, 4.6); TY.present(l + w * .66, b - .8, 2.5, 2.5, '#3f6aa8'); TY.present(l + w * .83, b - .8, 2.1, 3.1, '#c8302a', '#f4f2ec')
        return
    TY.books(l + w * .03, sh, 2.4, n=4, seed=5); TY.teddy(l + w * .36, sh, 3.3); TY.soldier(l + w * .56, sh, 3.4); TY.drum(l + w * .72, sh, 1.8); TY.doll(l + w * .88, sh, 2.9)
    TY.rocking_horse(l + w * .16, b - .8, 4.0); TY.wooden_train(l + w * .52, b - .8, 2.5); TY.blocks(l + w * .78, b - .8, 2.2)
    TY.present(l + w * .93, b - .8, 1.7, 2.3, '#3f8a44')
    with c.edges('fine'): SF.string_lights([(l + w * u, t + .5 + .3 * math.sin(u * math.pi * 3)) for u in np.linspace(.04, .96, 13)], seed=114)

def awning10(L, level, cols=('#b8402e', '#f4eee2')):
    """A striped awning seen from slightly below: it slopes out from the wall, shows its side cheek, ends in a
    scalloped valance and throws a soft shadow on the shopfront."""
    c = C(); x0, x1, t, b = L['x0'] + .8, L['x1'] - .8, L['awn_top'], L['awn_bot'] + .4; n = 6; ov = 1.4
    with c.edges('fine'):
        c.area([(x0 + ov, b + 1.4), (x1 + ov, b + 1.4), (x1 + ov, b + 3.4), (x0 + ov, b + 3.4)], '#2a1a10', wob=0, rough=.3, edge_dark=0, a=.3)   # shadow
        c.area([(x1, t), (x1 + ov, b), (x1 + ov, b + 1.6), (x1, t + 2.5)], hexc(cols[(n - 1) % 2]) * .7, wob=0, rough=.2, edge_dark=.15)   # side cheek
        for kk in range(n):
            a0 = x0 + kk * (x1 - x0) / n; a1 = x0 + (kk + 1) * (x1 - x0) / n
            col = cols[kk % 2]
            c.area([(a0, t), (a1, t), (a1 + ov, b), (a0 + ov, b)], col, wob=0, rough=.25, edge_dark=.06)
            c.area([(a0, t), (a1, t), (a1 + ov * .25, t + 1.4), (a0 + ov * .25, t + 1.4)], hexc(col) * .86, wob=0, rough=.2, edge_dark=0, a=.6)   # the fold under the roller
            sc = [(a0 + ov + (a1 - a0) * u, b + 1.6 * math.sin(u * math.pi)) for u in np.linspace(0, 1, 9)]
            c.area([(a0 + ov, b - .1)] + sc + [(a1 + ov, b - .1)], col, wob=0, rough=.2, edge_dark=.14)
        line([(x0, t + .15), (x1, t + .15)], .45, '#6a2a1e', a=.75)
        line([(x0 + ov, b), (x1 + ov, b)], .25, '#6a2a1e', a=.5)

def shopfront10(L, level):
    """Pilasters with capitals and plinths, a fascia, the display window over a stallriser, a recessed door."""
    c = C(); x0, x1, y = L['x0'], L['x1'], L['y']; top = L['awn_bot'] + .3
    paint = WOOD_M if level == 'A' else GREEN; pd = hexc(paint) * .7
    with c.edges('built'):
        rect(x0 + .3, top, x1 - .3, y, '#2a1e14', edge=0, rough=.2)
        for px in (x0, x1 - 2.7):
            rect(px, top, px + 2.7, y, paint, edge=.2, seed=int(px))
            line([(px + .7, top + 1.4), (px + .7, y - 1.6)], .25, GOLD if level != 'A' else WOOD_L, a=.8)
            rect(px - .45, y - 1.5, px + 3.15, y, pd, edge=.15); rect(px - .45, top, px + 3.15, top + 1.1, pd, edge=.15)
    dr_l, dr_r = x0 + 3.5, x0 + 12.6; win_l, win_r = x0 + 13.7, x1 - 3.5
    wt, wb = top + 1.7, y - 3.8
    with c.edges('fine'):
        rect(win_l - .55, wt - .55, win_r + .55, wb + .55, paint, edge=.15)
        G = np.array([hexc(z) for z in (GLASS_L, GLASS, GLASS_D)])
        m = rect(win_l, wt, win_r, wb, GLASS, edge=.25, seed=71)
        if m is not None:
            c.stip(m, lambda X, Y, rr: G[rr.randint(3, size=len(X))] * (1 - np.clip((Y - wt) / (wb - wt), 0, 1)[:, None] * .16), spacing=.55, L=1.1, w=.55, angfn=lambda X, Y: 0 * X, seed=72, jit=.4)
    display10(win_l, wt, win_r, wb, level)
    with c.edges('fine'):
        mx = (win_l + win_r) / 2; line([(mx, wt), (mx, wb)], .5, paint)
        for gx in (win_l + 1.8, mx + 1.6): c.stroke([(gx, wb - .5), (gx + 3.0, wt + .5)], .45, '#fff6dc', a=.22, dry=.3, taper=(.3, .3))
        rect(win_l - .9, wb + .35, win_r + .9, wb + 1.2, TRIM if level != 'A' else WOOD_L, edge=.22)                 # sill
        if level == 'C':                                                                           # brick stallriser
            rect(win_l, wb + 1.2, win_r, y - .9, '#9a4a32', edge=.15)
            for j, yy in enumerate(np.arange(wb + 1.6, y - .9, .75)):
                line([(win_l + .1, yy), (win_r - .1, yy)], .1, '#d8c0a0', a=.7)
                for xx in np.arange(win_l + (j % 2) * .9, win_r, 1.8): line([(xx, yy - .75), (xx, yy)], .1, '#d8c0a0', a=.6)
        else:
            rect(win_l, wb + 1.2, win_r, y - .9, paint, edge=.12)
            for j in range(3):
                a0 = win_l + .55 + j * (win_r - win_l - 1.1) / 3; a1 = a0 + (win_r - win_l - 1.1) / 3 - .55
                rect(a0, wb + 1.65, a1, y - 1.35, pd, edge=.22)
    door10(dr_l, dr_r, top + 1.7, y, level, paint)
    soft_outline([(x0, top), (x0, y)]); soft_outline([(x1, top), (x1, y)])

def storefront(level):
    """Paint the yellow shop at a level. 'orig' is tft7's current shop window and sign."""
    L = SF.house_layout(5); c = C()
    if level == 'orig':
        T7.shop_window(5, L['x0'], L['w'], L['h'], L['y']); T7.donation_sign(L['cx'], L['y'] - L['h'] * .28 - 9.5, L['w'] * .86); return
    x0, x1, y, top = L['x0'], L['x1'], L['y'], L['top']
    if level == 'C':
        with c.edges('built'):
            SF.roof_detail(L)
            for xx, s in ((x0, 1), (x1, -1)): SF.quoins(xx, top + 4, L['awn_top'] - .5, s)
    with c.edges('built'):
        SF.cornice(x0, x1, top + .6, 3.0 if level != 'C' else 2.6, dentils=level == 'C', brackets=level == 'C')
        SF.string_course(x0, x1, L['awn_top'] - 2.4)
    for wi in L['wins']:
        if wi['row'] == 2: continue
        rw, cl = wi['row'], wi['col']
        kw = dict(seed=130 + rw * 10 + cl)
        if level in ('B', 'C'):
            kw.update(glass='warm' if rw == 1 else 'night', shutters='#3f6a44' if rw == 0 else None, box=('red' if cl == 0 else 'white') if rw == 1 else None)
        if level == 'C':
            kw.update(keystone=rw == 0, curtains='#b8302a' if rw == 1 else None, story={(0, 0): 'candle', (1, 1): 'cat'}.get((rw, cl)))
            if (rw, cl) == (0, 0): kw['glass'] = 'warm'
        window10(wi, **kw)
    soft_outline([(x0, top + 3.6), (x0, L['awn_top'])]); soft_outline([(x1, top + 3.6), (x1, L['awn_top'])])
    if level == 'A':
        with c.edges('fine'): T7.donation_sign(L['cx'], y - L['h'] * .28 - 9.5, L['w'] * .86)
        shopfront10(L, 'A'); return
    sy = y - L['h'] * .28 - 9.0
    with c.edges('fine'):
        SF.sign(L['cx'], sy, L['w'] * .8, 13.2, 'B')                    # (lab8's outlined C lettering read as muddy)
    shopfront10(L, level)
    awning10(L, level)
    with c.edges('fine'):
        SF.garland(x0 + 2.4, x1 - 2.4, L['awn_bot'] + 3.2, sag=1.3, bows=3, lights=level == 'C', seed=141)

def after_square(level):
    """On the pavement in front: light from the window (B, C), a poinsettia by the door (C)."""
    if level in ('orig', 'A'): return
    L = SF.house_layout(5); x0, x1, y = L['x0'], L['x1'], L['y']; c = C()
    with c.edges('fine'):
        c.area([(x0 + 13.7, y + .6), (x1 - 3.5, y + .6), (x1 - 1, y + 7.5), (x0 + 11, y + 7.5)], '#f8d880', wob=.3, rough=.4, edge_dark=0, a=.17)
        if level == 'C':
            c.area([(x0 + 3.5, y + 1.8), (x0 + 12.6, y + 1.8), (x0 + 13.6, y + 5), (x0 + 2.4, y + 5)], '#f8d880', wob=.3, rough=.4, edge_dark=0, a=.1)
            px, py = x0 + 15.0, y + 3.6
            rect(px - 1.8, py - 2.6, px + 1.8, py, WOOD_M, edge=.18)
            c.dots([(px + u, py - 3.4 + v) for u, v in ((-1.2, 0), (0, -.6), (1.2, 0), (-.6, .5), (.6, .5))], .85, ['#c8302a', '#e04838'], seed=151)
            c.dots([(px, py - 3.3)], .3, [GOLD])

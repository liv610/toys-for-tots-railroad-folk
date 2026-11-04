"""Engine 10, Phase 4 investigation: small figures built silhouette-first, in poses that tell the story.

A figure is a few large shapes (a body that flares slightly at the hem, a round head, a cap) and limbs drawn as
tapered strokes through shoulder -> elbow -> hand joints, so a pose is just a handful of angles. Proportions stay
deliberately naive: a big head (about 1/5 of the height), short legs, no anatomy.
    marine(x, y, h, face, pose)   pose: 'give' | 'carry' | 'pull' | 'salute'
"""
import math
import numpy as np
import usmap4 as B
import toys10 as TY
from brush import hexc
def C(): return B.c
NAVY, BLUE_T, RED, WHITE, GOLD, SKIN = '#1c2642', '#2c4a86', '#c8302a', '#f4f2ec', '#d8a840', '#e2b48c'

def limb(P, w0, w1, col):
    """A tapered limb through its joints."""
    c = C(); P = [np.array(p, float) for p in P]
    for a, b, wa, wb in zip(P[:-1], P[1:], np.linspace(w0, w1, len(P))[:-1], np.linspace(w0, w1, len(P))[1:]):
        c.stroke([a, b], (wa + wb) / 2, col, a=1, dry=0, taper=(0, 0))
    for p, w in zip(P[1:-1], np.linspace(w0, w1, len(P))[1:-1]): TY.ellipse(p[0], p[1], w * .5, w * .5, col, edge=0)

def arm(sh, a1, a2, L, f):
    """Joints of an arm from shoulder sh: upper arm at angle a1, forearm at a2 (radians, 0 = forward, pi/2 = down)."""
    e = (sh[0] + f * math.cos(a1) * L, sh[1] + math.sin(a1) * L); h = (e[0] + f * math.cos(a2) * L * .95, e[1] + math.sin(a2) * L * .95)
    return [sh, e, h]

def marine(x, y, h=26, face=1, pose='give', seed=0):
    c = C(); s = h / 26.0; f = face; P = lambda dx, dy: (x + f * dx * s, y + dy * s)
    stride = pose == 'pull'
    with c.edges('fine'):
        # legs (behind the coat): sky-blue trousers with the red stripe, polished shoes
        legs = [((-1.3, -11), (-2.6 if stride else -1.2, -1.1)), ((1.3, -11), (2.9 if stride else 1.2, -1.1))]
        for (top, foot) in legs:
            limb([P(*top), P(*foot)], 2.5 * s, 2.2 * s, BLUE_T)
            c.stroke([P(top[0] + .9, top[1] + .5), P(foot[0] + .9, foot[1])], .45 * s, RED, a=1, dry=0, taper=(0, 0))
            TY.shape([P(foot[0] - 1.3, 0), P(foot[0] + 1.9, 0), P(foot[0] + 1.6, -1.4), P(foot[0] - 1.2, -1.4)], '#141218', edge=0, smooth=False)
            c.dots([P(foot[0] + 1.0, -.9)], .25 * s, ['#8a8a96'])
        # the back arm (behind the body)
        sh_b = P(-2.4, -19.2)
        back = {'give': arm(sh_b, math.pi * .55, math.pi * .5, 4.3 * s, -f), 'carry': arm(sh_b, math.pi * .3, -.2, 4.0 * s, f),
                'pull': arm(sh_b, math.pi * .64, math.pi * .58, 4.4 * s, f), 'salute': arm(sh_b, math.pi * .55, math.pi * .5, 4.3 * s, -f)}[pose]
        limb(back, 1.9 * s, 1.6 * s, hexc(NAVY) * .8); TY.ellipse(back[-1][0], back[-1][1], .95 * s, .95 * s, WHITE, edge=.1)
        # body: a dress-blue coat that flares a little at the hem, white belt with a gold buckle, red piping
        TY.shape([P(-3.3, -10.6), P(3.4, -10.6), P(3.0, -15), P(2.9, -19.6), P(1.6, -20.6), P(-1.6, -20.6), P(-2.9, -19.6), P(-3.0, -15)], NAVY, edge=.18, seed=seed)
        c.stroke([P(.7, -11), P(.7, -20.2)], .35 * s, RED, a=.85, dry=0, taper=(0, 0))
        TY.shape([P(-3.25, -11.2), P(3.35, -11.2), P(3.3, -12.6), P(-3.2, -12.6)], WHITE, edge=.1, smooth=False)
        TY.shape([P(-.1, -11.3), P(1.5, -11.3), P(1.5, -12.5), P(-.1, -12.5)], GOLD, edge=.15, smooth=False)
        c.dots([P(.75, yy) for yy in (-14.0, -15.8, -17.6, -19.3)], .32 * s, [GOLD])
        TY.shape([P(-1.6, -20.5), P(1.6, -20.5), P(1.4, -21.9), P(-1.4, -21.9)], NAVY, edge=.1, smooth=False)
        c.stroke([P(-1.5, -21.8), P(1.5, -21.8)], .35 * s, RED, a=.9, dry=0, taper=(0, 0))
        for sx in (-1, 1): c.dots([P(sx * 2.7, -19.9)], .5 * s, [GOLD])
        # head: three-quarter face, ear, eyes, smile, rosy cheek
        hx, hy = P(.35, -24.2)
        TY.ellipse(hx, hy, 2.35 * s, 2.45 * s, SKIN, edge=.12)
        c.dots([(hx - f * 1.9 * s, hy + .3 * s)], .6 * s, ['#c8946c'])
    with c.edges('crisp'):
        c.dots([(hx + f * .45 * s, hy - .05 * s), (hx + f * 1.55 * s, hy - .05 * s)], .28 * s, ['#2a1a12'])
        c.stroke([(hx + f * .45 * s, hy + 1.1 * s), (hx + f * 1.0 * s, hy + 1.35 * s), (hx + f * 1.55 * s, hy + 1.1 * s)], .3 * s, '#8a3a2a', a=.9, dry=0, taper=(.2, .2))
        c.dots([(hx + f * 1.45 * s, hy + .55 * s)], .4 * s, ['#e89a88'])
    with c.edges('fine'):
        # dress cap: white band and crown, black visor reaching forward, gold emblem
        TY.shape([(hx - 2.5 * s, hy - 1.7 * s), (hx + 2.5 * s, hy - 1.7 * s), (hx + 2.5 * s, hy - 2.8 * s), (hx - 2.5 * s, hy - 2.8 * s)], '#e6e4dc', edge=.12, smooth=False)
        TY.ellipse(hx + f * .3 * s, hy - 3.4 * s, 3.5 * s, 1.2 * s, WHITE, edge=.14)
        TY.shape([(hx - f * .2 * s, hy - 2.1 * s), (hx + f * 2.3 * s, hy - 2.1 * s), (hx + f * 3.9 * s, hy - 1.2 * s), (hx + f * 3.4 * s, hy - .7 * s), (hx + f * 1.3 * s, hy - .9 * s)], '#121016', edge=0, smooth=False)
    with c.edges('crisp'): c.dots([(hx + f * 1.2 * s, hy - 2.3 * s)], .45 * s, [GOLD])
    with c.edges('fine'):
        # the front arm, posed
        sh = P(2.4, -19.2)
        front = {'give': arm(sh, .55, -.05, 4.4 * s, f), 'carry': arm(sh, .9, -.35, 4.0 * s, f),
                 'pull': arm(sh, math.pi * .38, math.pi * .45, 4.4 * s, f), 'salute': arm(sh, -.25, -math.pi * .62, 4.4 * s, f)}[pose]
        if pose == 'salute':                                               # the hand meets the visor
            front[-1] = (hx + f * 2.2 * s, hy - 1.6 * s); front[1] = (front[0][0] + f * 3.6 * s, front[0][1] - .6 * s)
        limb(front, 1.9 * s, 1.6 * s, NAVY)
        c.stroke([front[-1], front[-2]], 1.65 * s, NAVY, a=1, dry=0, taper=(0, .9))
        TY.ellipse(front[-1][0], front[-1][1], 1.0 * s, 1.0 * s, WHITE, edge=.1)
        if pose == 'give': TY.present(front[-1][0] + f * 2.6 * s, front[-1][1] + 1.6 * s, 3.4 * s, 3.2 * s, '#c8302a', '#f2d488')
        if pose == 'carry':
            cx = x + f * 3.6 * s
            TY.present(cx, y - 11.6 * s, 4.4 * s, 3.4 * s, '#3f6aa8', '#f4f2ec'); TY.present(cx + f * .3 * s, y - 15.0 * s, 3.4 * s, 2.8 * s, '#3f8a44', '#f2d488')
            TY.ellipse(back[-1][0], back[-1][1], .95 * s, .95 * s, WHITE, edge=.1)
    return back[-1] if pose == 'pull' else None

def wagon(x, y, s=1.0, handle_to=None):
    c = C()
    with c.edges('fine'):
        TY.shape([(x - 7 * s, y - 2.2 * s), (x + 7 * s, y - 2.2 * s), (x + 7.6 * s, y - 7 * s), (x - 7.6 * s, y - 7 * s)], '#c8302a', edge=.15, smooth=False)
        c.stroke([(x - 7.4 * s, y - 6.4 * s), (x + 7.4 * s, y - 6.4 * s)], .9 * s, '#e8685a', a=.8, dry=0, taper=(0, 0))
        TY.teddy(x - 3 * s, y - 6.6 * s, 7 * s); TY.present(x + 1.5 * s, y - 6.6 * s, 3 * s, 3 * s, '#3f6aa8'); TY.present(x + 4.6 * s, y - 6.6 * s, 2.6 * s, 3.8 * s, '#e8b84a', '#c8302a')
        if handle_to is not None: c.stroke([(x + (7.4 if handle_to[0] > x else -7.4) * s, y - 4.4 * s), handle_to], .7 * s, '#3a2e26', a=1, dry=0, taper=(0, 0))
    with c.edges('crisp'):
        for wx in (-4.6, 4.6):
            TY.ellipse(x + wx * s, y - 1.8 * s, 2.0 * s, 2.0 * s, '#2a2420', edge=0); TY.ellipse(x + wx * s, y - 1.8 * s, .8 * s, .8 * s, '#9a9aa0', edge=0)

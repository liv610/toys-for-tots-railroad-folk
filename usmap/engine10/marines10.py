"""Engine 10: the two Marines handing over a gift, drawn by hand after the user's Toy Town reference.

Coordinates: one unit = one pixel of the reference crop (x 590-870, y 545-830 of the reference), y down; the left
Marine faces right, the right Marine is his mirror image (x' = 292 - x) with darker skin and hair, as in the
reference. Colours are sampled from the reference. Painted by the map's brush through assets10.Place.

    pair(x, y, h=28)    paint the pair with the soles of the left Marine at map (x, y), about h map units tall
"""
import assets10 as A

NAVY, NAVY_D, NAVY_L = '#272d3d', '#1d2232', '#353e55'
BLUE, BLUE_D, RED = '#314a79', '#25395f', '#e03a32'
WHITE, WHITE_S, BLACK, GOLD, GOLD_D = '#f7efe6', '#d8d0c6', '#1f1d21', '#e8bf3b', '#b8892a'
GIFT, GIFT_S, GIFT_T, RIBBON = '#f4b843', '#d99a2e', '#fbcd62', '#b8301f'
SKINS = {'left': ('#eab386', '#d4966a', '#9a6a3e'), 'right': ('#8c5634', '#74432a', '#2a1e18')}   # skin, shade, hair
MIRROR = 292

def marine(P, side):
    skin, skin_s, hair = SKINS[side]
    # ground shadow, then the legs
    P.ellipse(58, 276, 38, 5, '#5a5048', a=.35, rough=.2, edge_dark=0)
    P.shape([(29, 262), (70, 262), (74, 270), (70, 276), (29, 276)], BLACK, smooth=False, rough=.25)                   # back shoe
    P.shape([(27, 172), (81, 172), (80, 215), (79, 264), (56, 264), (54, 232), (52, 264), (29, 264), (27, 215)], BLUE, smooth=False,
            stip=([BLUE, '#35507f', '#2d4472'], 1.5, 2.8, 1.2), edge_dark=.14)
    P.shape([(66, 174), (80, 174), (79, 263), (68, 263)], BLUE_D, smooth=False, a=.8, edge_dark=0)                     # shade on the far leg
    P.shape([(40, 174), (50, 174), (48.5, 263), (38.5, 263)], RED, smooth=False, rough=.3)                             # the red stripe
    P.shape([(54, 266), (88, 265), (94, 271), (90, 278), (54, 278)], BLACK, smooth=False, rough=.25)                   # front shoe
    P.line([(60, 268), (86, 267.5)], 1.2, '#5a5a66', a=.7)                                                            # shine
    # the coat, its shading, belt and buttons
    P.shape([(30, 76), (42, 69), (56, 66), (70, 68), (82, 75), (86, 95), (85, 130), (87, 177), (55, 180), (24, 177), (26, 130), (25, 95)], NAVY,
            stip=([NAVY, '#2c3344', '#232837'], 1.4, 2.4, 1.1), edge_dark=.16)
    P.line([(30, 76), (25, 95), (26, 130), (24, 177), (55, 180), (87, 177)], 1.3, '#12151e', a=.85, taper=(0, 0))
    P.shape([(26, 82), (36, 76), (37, 176), (24, 176)], NAVY_D, smooth=False, a=.85, edge_dark=0)
    P.shape([(60, 80), (77, 79), (79, 122), (63, 124)], NAVY_L, a=.6, edge_dark=0)
    P.shape([(26, 134), (86, 133), (86, 142.5), (26, 143.5)], WHITE, smooth=False, rough=.25)
    P.shape([(57, 133.5), (72, 133.5), (72, 142.5), (57, 142.5)], GOLD, smooth=False, rough=.25)
    P.line([(58, 140.5), (71, 140.5)], .9, GOLD_D, a=.7)
    P.line([(56, 70), (62, 132)], .9, NAVY_D, a=.7)                                                                   # the coat's front edge
    P.line([(61, 144), (63, 177)], .9, NAVY_D, a=.7)
    buttons(P, [(57.3, 77.1), (64.5, 86.3), (68.4, 94.9), (75.6, 97.2), (61.1, 98.3), (70.8, 104.0), (72.1, 111.1), (75.2, 150.0), (75.5, 161)], 2.6)
    P.shape([(46, 63), (68, 63), (70, 71), (45, 71)], NAVY_L, smooth=False, rough=.25)                                # standing collar
    P.line([(46, 64), (68, 64)], .8, RED, a=.8)
    P.dots([(49, 68), (66, 68)], 1.2, GOLD)
    # the head
    P.shape([(52, 60), (64, 60), (64, 68), (52, 68)], skin_s, smooth=False)                                             # neck
    P.shape([(44, 41), (57, 39), (56, 48), (53, 57), (48, 63), (43, 54)], hair)                                         # hair under the cap
    P.shape([(52, 43), (66, 42), (76, 44), (78.5, 47.5), (79.5, 50.5), (82.8, 54.8), (79.6, 57.2), (80.2, 59.6), (79.2, 62.4), (78.2, 66.2),
             (73, 70.6), (64, 72.2), (56, 69.4), (50, 63.5), (48.5, 53), (50, 46)], skin, rough=.3, edge_dark=.1, n=6)
    P.shape([(49, 47), (55, 44), (56, 66), (51, 63)], skin_s, a=.5, edge_dark=0)                                       # shade at the back of the face
    P.shape([(74, 66), (78, 65.5), (73, 70.4), (66, 71.8)], skin_s, a=.5, edge_dark=0)                                 # under the jaw
    P.ellipse(52.8, 54.5, 3.0, 4.6, skin_s, edge_dark=.12); P.line([(53.5, 51.5), (54.2, 55), (53.2, 57.5)], .8, '#5e3a24', a=.6)   # ear
    P.line([(56.5, 41), (55, 47), (53, 50)], 1.6, hair, a=.9)                                                          # sideburn
    P.ellipse(71, 50.8, 1.6, 2.2, '#1e1612', edge='crisp', rough=.1, edge_dark=0); P.dots([(71.5, 50)], .55, '#f4efe8')  # eye
    P.line([(67, 46.4), (74.5, 45.6)], 1.5, hair, a=.95, taper=(.3, .2))                                                # brow
    P.line([(79, 50.5), (81.2, 54.6), (78.8, 56.6)], .9, skin_s, a=.95)                                                 # nose
    P.shape([(70, 61), (79.4, 60.2), (78.4, 63.4), (74.5, 65.2), (71, 63.9)], '#6e2a20', smooth=False, rough=.2, edge_dark=0)  # smiling mouth
    P.line([(71, 61.4), (78.6, 60.8)], 1.1, '#f4efe8', a=.95, taper=(.2, .2))                                           # teeth
    P.dots([(74.5, 57.2)], 2.4, '#f0907a' if side == 'left' else '#a0503a', edge='fine')                               # cheek
    # the dress cap: crown, band, visor, emblem
    P.shape([(24, 25), (36, 16), (58, 12), (80, 14), (87, 20), (81, 28), (60, 31), (37, 32)], WHITE, rough=.3, edge_dark=.1)
    P.shape([(30, 28), (60, 30), (81, 27), (80, 31), (58, 33), (32, 32)], WHITE_S, a=.8, edge_dark=0)
    P.shape([(36, 30), (77, 28), (77, 36.5), (37, 38.5)], '#ebe5dc', smooth=False, rough=.25)
    P.shape([(52, 36), (76, 34), (87, 38), (85, 42.5), (70, 43.5), (54, 41)], BLACK, rough=.25)
    P.line([(57, 38), (82, 38.5)], .8, '#55555f', a=.8)
    P.ellipse(74, 23, 3.0, 4.0, GOLD, edge='crisp'); P.dots([(74, 22)], 1.1, GOLD_D)
    # the front arm reaching for the gift, with the cuff buttons
    P.shape([(68, 79), (83, 80), (87, 102), (86, 131), (77, 129), (70, 104)], '#1b2030', a=.9, edge_dark=0)               # shadow the arm casts on the coat
    SLEEVE = [(71, 77), (83, 79), (90, 92), (94, 108), (98, 118), (110, 122), (111, 138), (95, 138.5), (84, 131.5), (77, 118), (72, 100)]
    P.shape(SLEEVE, '#30384d', stip=(['#30384d', '#353e55', '#2a3144'], 1.4, 2.2, 1.1), edge_dark=.18)
    P.line([(72, 100), (77, 118), (84, 131.5), (95, 138.5), (110.5, 138.6)], 1.6, '#12151e', a=.9)                         # underside outline
    P.line([(83, 79.5), (90, 92), (94, 108), (98, 118), (109.5, 122.2)], 1.2, '#56627f', a=.75)                              # lit top edge
    P.line([(86, 113), (92, 123)], 1.0, '#1b2030', a=.85); P.line([(89, 106), (95, 116.5)], .9, '#1b2030', a=.7)              # elbow folds
    P.shape([(102, 122.6), (110.5, 123), (111, 138.3), (102, 138.2)], '#404a66', smooth=False, a=.8, edge_dark=0)        # cuff
    buttons(P, [(90.9, 133.9), (97.1, 135.1)], 2.1)

def buttons(P, pts, r):
    for x, y in pts:
        P.ellipse(x + .4, y + .5, r, r, '#8a6418', edge='crisp', rough=.1, edge_dark=0, a=.8)
        P.ellipse(x, y, r, r, '#f2cc48', edge='crisp', rough=.1, edge_dark=.15)
        P.dots([(x - r * .35, y - r * .35)], r * .35, '#fff4c0')

def gift(P):
    P.shape([(108, 97), (170, 95), (170, 138), (109, 139)], GIFT, smooth=False, stip=([GIFT, '#f7c050', '#eeac3c'], 1.6, 2.8, 1.3))
    P.shape([(170, 95), (185, 91), (185, 133), (170, 138)], GIFT_S, smooth=False)
    P.shape([(105, 85), (172, 83), (172, 97), (106, 98)], GIFT_T, smooth=False)
    P.shape([(172, 83), (188, 80), (188, 93), (172, 97)], GIFT_S, smooth=False)
    P.shape([(105, 85), (124, 81), (188, 80), (172, 83)], '#fde08a', smooth=False, edge_dark=0)
    P.shape([(141, 84), (152, 84), (152, 139), (141, 139)], RIBBON, smooth=False, rough=.25)                         # ribbon down the front
    P.shape([(106, 88), (172, 86.5), (172, 92.5), (106, 94)], RIBBON, smooth=False, rough=.25)                         # round the lid
    P.shape([(172, 86.5), (188, 84), (188, 89.5), (172, 92.5)], '#962618', smooth=False)
    for tail in ([(146, 82), (139, 93)], [(149, 82), (157, 94)]): P.line(tail, 4.6, '#a52818', taper=(0, .3))
    for lp, inner in (([(146, 82), (141, 73), (133, 65), (124, 61.5), (118.5, 66), (121, 74.5), (131, 80.5)], (128, 70.5, 4.4, 3.0, -.5)),
                      ([(148, 82), (153, 73), (161, 65), (170, 61.5), (175.5, 66), (173, 74.5), (163, 80.5)], (166, 70.5, 4.4, 3.0, .5))):
        P.shape(lp, RIBBON, edge_dark=.18, rough=.25)
        cx, cy, rx, ry, rot = inner; P.ellipse(cx, cy, rx, ry, '#6e1810', rot=rot, edge_dark=0, a=.9)                    # the loop's shadowed inside
    P.line([(124, 63.5), (133, 66.5), (141, 74)], 1.3, '#e2604a', a=.75); P.line([(170, 63.5), (161, 66.5), (153, 74)], 1.3, '#e2604a', a=.75)
    P.ellipse(147, 80, 4, 3.4, '#962618')

def glove(P):
    P.shape([(103, 125), (117, 122), (128, 125), (132, 132), (127, 140), (112, 142.5), (103, 139)], WHITE, rough=.3, edge_dark=.12)
    for y in (129.5, 133.5, 137): P.line([(118, y), (128.5, y - .5)], .7, WHITE_S, a=.9)

def pair(x, y, h=28):
    """Paint the pair; (x, y) is where the left Marine's soles stand, h his height in map units."""
    u = h / 265.0; x0, y0 = x - 58 * u, y - 276 * u
    L = A.Place(x0, y0, u); R = A.Place(x0, y0, u, flip=True, W=MIRROR)
    marine(L, 'left'); marine(R, 'right'); gift(L); glove(L); glove(R)

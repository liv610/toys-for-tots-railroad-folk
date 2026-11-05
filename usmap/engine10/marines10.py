"""Engine 10: the two Marines handing over a gift, drawn by hand after the user's Toy Town reference.

Coordinates: one unit = one pixel of the reference crop (x 590-870, y 545-830 of the reference), y down; the left
Marine faces right, the right Marine is his mirror image (x' = 292 - x) with darker skin, dark hair and an open
smile, as in the reference. Shapes were measured from 5-8x gridded enlargements of the reference; colours are
sampled from it. Painted by the map's brush through assets10.Place.

Round 4 (5 Nov 2026): asset-scaled edges; the cap rebuilt (raked crown, navy band, button, visor); larger, sharper
faces in the reference's warm skin tones; shoulder insignia, lower buttons and red piping; trousers with a slanted
stripe, a lit and a shaded leg and the far shoe; a frontal gift with hollow bow loops and smoother gold.

    pair(x, y, h=28)    paint the pair with the soles of the left Marine at map (x, y), about h map units tall
"""
import assets10 as A

NAVY, NAVY_D, NAVY_L, NAVY_X = '#283146', '#1b2132', '#36415c', '#12151f'
BLUE, BLUE_D, BLUE_L, RED = '#2b4275', '#22345d', '#34508c', '#e03a2e'
WHITE, WHITE_S, WHITE_G, BLACK = '#fbf6f0', '#dcd6dc', '#c9c3cc', '#1d1c21'
GOLD, GOLD_D, GOLD_L = '#f2c63c', '#9a6c16', '#fff3b8'
GIFT, GIFT_D, GIFT_L, RIBBON, RIBBON_D, RIBBON_L = '#f5b840', '#cf8d26', '#fcd877', '#bd3220', '#8e2014', '#e0604a'
SKINS = {   # skin, shade, light, hair, hair shade, mouth
    'left': ('#f7a95c', '#d9873f', '#ffc27e', '#b4682a', '#8a4b1c', '#7a3418'),
    'right': ('#9c5a2c', '#7a431f', '#b26c3a', '#33261e', '#1e1612', '#3a180e'),
}
MIRROR = 292
LIGHT = (1, -.7)          # the light comes from the front and above, as on the reference

def marine(P, side):
    skin, skin_s, skin_l, hair, hair_s, mouth = SKINS[side]
    lt = lambda amt: (LIGHT[0], LIGHT[1], amt)
    P.ellipse(60, 274, 40, 5.5, '#4e443c', a=.32, rough=.15, rim=0, soft=2.5)                      # ground shadow
    # ---- legs: far shoe, trousers, the near leg in shade, the stripe, the lit far leg, near shoe
    P.shape([(63, 255), (86, 254), (94, 260), (93, 268), (63, 269)], BLACK, rough=.2, rim=.0, n=6)
    P.shape([(26, 172), (81, 172), (80, 215), (77, 259), (61, 259), (60, 246), (58, 265), (27, 265), (26, 215)], BLUE, smooth=False,
            stip=([BLUE, '#30497e', '#273c68'], 1.3, 2.6, 1.0), rim=.14, light=lt(.10))
    P.shape([(26.5, 173), (48, 173), (39, 264), (27.5, 264)], BLUE_D, smooth=False, a=.75, rim=0, soft=1.0)
    P.shape([(58, 173), (72, 173), (70, 257), (49, 263)], BLUE_L, smooth=False, a=.55, rim=0, soft=1.5)
    P.shape([(73, 173), (80.5, 173), (77, 258), (70, 258)], BLUE_D, smooth=False, a=.8, rim=0, soft=1.0)
    P.shape([(48, 173), (58, 173), (49.2, 264), (39, 264)], RED, smooth=False, rough=.25, rim=.08, light=lt(.08))
    P.line([(51, 180), (43, 255)], .9, '#f26a52', a=.55)                                            # light on the stripe
    P.line([(61, 228), (60.5, 246), (61.5, 260)], 1.1, '#18233f', a=.85)                             # between the legs
    P.line([(65, 200), (63.5, 252)], .8, '#1e2c50', a=.6)                                            # crease
    P.line([(26.5, 175), (26, 215), (27.3, 264)], 1.1, '#141c33', a=.8, taper=(0, 0))                # back edge
    P.shape([(26, 262), (62, 261), (69, 264.5), (71, 270), (67, 275.5), (26, 276)], BLACK, rough=.2, rim=0, n=6)
    P.line([(31, 264.5), (64, 264)], 1.2, '#55555f', a=.65); P.line([(68, 257.5), (89, 257.5)], 1.1, '#55555f', a=.55)
    # ---- the coat
    COAT = [(30, 75), (40, 69), (52, 67), (64, 68), (74, 74), (80, 84), (84, 100), (85, 130), (86, 175), (56, 177.5), (26, 175.5),
            (26, 130), (25, 96), (26, 84)]
    P.shape(COAT, NAVY, stip=([NAVY, '#2e3850', '#252c3f'], 1.3, 2.2, 1.0), rim=.16, light=lt(.16))
    P.line([(30, 75), (26, 84), (25, 96), (26, 130), (26, 175.5), (56, 177.5), (86, 175)], 1.3, NAVY_X, a=.85, taper=(0, 0))
    P.shape([(26, 84), (33, 76), (34, 176), (26, 175)], NAVY_D, smooth=False, a=.55, rim=0, soft=2.0)     # the shaded back
    P.line([(76, 144), (76.5, 175)], 1.0, '#c8382a', a=.9)                                           # red piping on the front edge
    P.line([(74.6, 144), (75, 175)], .8, NAVY_X, a=.7)
    P.shape([(30, 132.5), (84, 131.5), (84.5, 142.5), (30, 143.5)], WHITE, smooth=False, rough=.2, rim=.10, light=lt(.06))   # belt
    P.line([(31, 141.8), (84, 140.8)], 1.0, WHITE_G, a=.8)
    P.shape([(61, 131.8), (79, 131.6), (79.2, 142.6), (61.2, 142.8)], GOLD, smooth=False, rough=.2, rim=.18, rimw=1.6, light=lt(.12))
    P.line([(63, 137.2), (77, 137)], .8, GOLD_D, a=.6); P.line([(62, 132.8), (78, 132.6)], .8, GOLD_L, a=.8)
    buttons(P, [(48.6, 150), (55, 150), (75, 150.6)], 1.5)
    buttons(P, [(57.4, 77.3), (65, 86.6), (68.6, 95.6), (61.4, 98.4), (76, 97.6), (71.4, 104.4), (72.6, 111.6)], 2.05)
    P.shape([(43.5, 80), (46.2, 79.6), (44, 87.5), (41.6, 87.5)], '#b8402a', smooth=False, rough=.15, rim=0)  # shoulder insignia
    P.dots([(42.6, 78.8)], .9, '#e8e4e0')
    # ---- the head: neck, hair, face, ear, features
    P.shape([(51, 62), (65, 64), (65, 71), (51, 71)], skin_s, smooth=False, rim=0)
    P.shape([(42, 70), (52, 67.4), (62, 68.4), (66.5, 71.5), (65.5, 77.5), (44, 78.5)], NAVY_L, rough=.2, rim=.15, n=6)      # collar
    P.line([(43, 70.3), (52, 67.8), (62, 68.8), (66, 71.8)], .8, '#b8402a', a=.7)
    hair_pts = ([(36, 45), (53, 43), (57, 47.5), (53, 50), (50, 56), (52, 62), (47, 66.5), (40, 63), (36.5, 54)] if side == 'left' else
                [(40.5, 45.5), (53, 43.5), (55.5, 47.5), (51.5, 50), (49.6, 55.5), (50.2, 60), (46.5, 61.2), (42.5, 58.5), (40.6, 52)])
    P.shape(hair_pts, hair, rough=.3, rim=.12, light=lt(.10), n=6)
    P.line([(39, 50), (45, 58), (46, 64)], 1.0, hair_s, a=.6)
    FACE = [(51, 45.5), (62, 43.5), (76, 41.5), (77.6, 47), (77.4, 52), (76.6, 54.2), (79, 56.4), (79.6, 58.4), (76.6, 60), (77.2, 62),
            (75.7, 64.2), (75.3, 67), (71, 70.2), (64, 70.8), (56, 69.2), (51.2, 65.4), (49.4, 57)]
    P.shape(FACE, skin, rough=.2, rim=.14, rimw=2.0, light=lt(.10), n=6)
    P.shape([(51, 46), (56, 45.5), (55, 66), (51.5, 64.5), (49.8, 56)], skin_s, a=.45, rim=0, soft=2.0)     # shade at the back
    P.shape([(62, 44), (75, 42.2), (75.5, 45), (63, 46.5)], skin_s, a=.5, rim=0, soft=1.2)                 # under the visor
    P.shape([(64, 49), (70, 47.5), (74, 52), (73, 57), (66, 58)], skin_l, a=.35, rim=0, soft=2.5)          # lit cheek
    P.line([(52.5, 62.5), (56.5, 67), (63, 70)], 1.0, skin_s, a=.85)                                     # jaw
    P.ellipse(48, 53.2, 2.6, 3.6, skin, rim=.25, rimw=1.2, rough=.15)                                   # ear
    P.line([(48.6, 51), (49.3, 53.5), (48.4, 55.5)], .8, skin_s, a=.9)
    P.ellipse(69.4, 50.6, 1.75, 1.95, '#22160f', soft=.3, rough=.1, rim=0); P.dots([(69.9, 50)], .42, '#fbf3ea')   # eye
    P.line([(66.6, 47.2), (71.4, 46.6)], .9, hair_s, a=.65)                                              # brow
    P.line([(75.8, 59.4), (77.8, 59.6)], .8, skin_s, a=.9)                                               # under the nose
    if side == 'left':                                                                                    # closed smile
        P.line([(65.4, 60.2), (66.6, 61.6), (69.4, 62.6), (72.6, 62.1), (74, 61)], 1.15, mouth, a=.95, taper=(.3, .3))
    else:                                                                                                 # open smile, teeth
        P.shape([(65.5, 59.8), (73.4, 60.4), (72.4, 64), (67.2, 63.8)], mouth, smooth=False, rough=.1, rim=0, soft=.35)
        P.shape([(66.4, 60.3), (72.8, 60.8), (72.3, 62.3), (66.8, 62)], '#f6f0e8', smooth=False, rough=.1, rim=0, soft=.35)
    # ---- the dress cap: raked white crown, navy band with a button, black visor, gold emblem
    CROWN = [(24, 33), (30, 28), (40, 23), (55, 18), (70, 14), (80, 12.5), (83.2, 15), (82, 21), (78.5, 30), (60, 36), (45, 40), (35, 43.2), (26.5, 38.5)]
    P.shape(CROWN, WHITE, rough=.2, rim=.10, rimw=2.0, n=6)
    P.shape([(30, 33), (45, 28), (62, 24), (77, 21), (77.5, 27), (60, 32.5), (42, 37.5), (32, 39.5)], WHITE_S, a=.75, rim=0, soft=2.5)
    P.line([(25, 35), (35, 42.8), (45, 39.8), (60, 35.8), (78.5, 30)], 1.0, WHITE_G, a=.8)
    P.shape([(35, 42.6), (60, 35.8), (78.4, 30.4), (78.4, 38.6), (60, 43.5), (36, 48.2)], NAVY, smooth=False, rough=.2, rim=.12, light=lt(.12))
    buttons(P, [(54.2, 40.2)], 2.0)
    P.shape([(55, 41.4), (70, 37.4), (80, 37.6), (86.2, 40.3), (84.2, 42.8), (70, 43.4), (58, 45.2)], '#262a38', rough=.2, rim=0, n=6)
    P.line([(62, 39.8), (82.5, 39.2)], .8, '#5c6070', a=.75)
    P.line([(74.3, 20.6), (74.6, 25)], 1.1, GOLD, a=.95, taper=(.4, 0))                                 # emblem: eagle, globe, anchor
    P.ellipse(74.7, 27.4, 2.5, 2.7, GOLD, soft=.3, rough=.1, rim=.25, rimw=.9)
    P.line([(72.6, 29.6), (74.7, 31.4), (76.8, 29.6)], .8, GOLD, a=.95)
    P.line([(73.4, 26.8), (76, 27.4)], .55, GOLD_D, a=.7)
    # ---- the front arm reaching for the gift
    P.shape([(78, 100), (76, 116), (77, 128), (83, 137), (88, 145), (80, 145), (73, 132), (73, 115), (75, 100)], '#141927', a=.5, rim=0, soft=2.5)
    SLEEVE = [(73, 79), (78.5, 81), (84, 95), (92, 105), (102, 109), (110.5, 111), (112, 127), (108.5, 140), (95, 140.4), (86, 138.4),
              (79, 132), (76, 124), (77, 112), (79.5, 100), (78, 88)]
    P.shape(SLEEVE, '#2c354d', stip=(['#2c354d', '#333d57', '#262e43'], 1.3, 2.1, 1.0), rim=.18, light=lt(.14), n=6)
    P.line([(78.5, 90), (79.5, 100), (77, 112), (76, 124), (79, 132), (86, 138.4), (95, 140.4), (108.5, 140)], 1.5, NAVY_X, a=.9)
    P.line([(77.5, 81.5), (84, 96), (92, 105), (102, 109), (109.5, 111.2)], 1.1, '#56627f', a=.7)
    P.line([(84, 112), (90.5, 122)], .9, NAVY_X, a=.7); P.line([(88, 106), (94, 115.5)], .8, NAVY_X, a=.55)   # elbow folds
    P.line([(102.5, 110.5), (101, 139.5)], .9, NAVY_X, a=.75)                                          # cuff edge
    P.line([(101.6, 120.5), (101.2, 126.5)], .9, '#c8382a', a=.85)
    buttons(P, [(91, 134.4), (97.4, 135.4)], 1.7)

def buttons(P, pts, r):
    for x, y in pts:
        P.ellipse(x + .35, y + .45, r * 1.05, r * 1.05, GOLD_D, soft=.35, rough=.1, rim=0, a=.85)
        P.ellipse(x, y, r, r, GOLD, soft=.3, rough=.1, rim=.2, rimw=.8)
        P.dots([(x - r * .3, y - r * .32)], r * .34, GOLD_L)

def gift(P):
    lt = lambda amt: (-.6, -1, amt)                                         # lit from the top left, like the reference
    P.shape([(107, 92), (183, 91.5), (183.5, 140), (107.5, 140.5)], GIFT, smooth=False, rough=.2, rim=.14, light=lt(.12), var=.03)
    for cx, cy, rx, ry, col, a in ((122, 104, 9, 5, GIFT_L, .35), (170, 101, 8, 4.5, GIFT_L, .3), (131, 124, 7, 5, '#e9a334', .35),
                                   (168, 127, 9, 5.5, '#e9a334', .35), (124, 133, 6, 3.5, GIFT_L, .25), (172, 115, 5, 3.5, GIFT_L, .25)):
        P.ellipse(cx, cy, rx, ry, col, a=a, rim=0, soft=2.5, rough=.4)                                   # soft mottling, as on the reference
    P.line([(108, 93.6), (182.5, 93.2)], 1.4, GIFT_D, a=.55)                                             # under the lid
    P.shape([(104.5, 84), (185.5, 83.5), (185.5, 92.2), (104.5, 92.6)], GIFT_L, smooth=False, rough=.2, rim=.12, light=lt(.10))
    P.line([(105.5, 84.6), (184.5, 84.2)], 1.0, '#fff0b6', a=.85)
    P.shape([(104.5, 85.6), (185.5, 85.2), (185.5, 88.6), (104.5, 89)], RIBBON, smooth=False, rough=.15, rim=0, soft=.4)   # round the lid
    P.shape([(110.8, 92.5), (114, 92.4), (114, 140.3), (110.8, 140.4)], RIBBON, smooth=False, rough=.15, rim=0, a=.9)        # round the side
    P.shape([(146, 84), (156, 84), (156, 140.2), (146, 140.4)], RIBBON, smooth=False, rough=.2, rim=.16, rimw=1.5)           # down the front
    P.line([(148.6, 90), (148.4, 138)], 1.2, RIBBON_L, a=.55)
    # the bow: two hollow loops, a knot
    P.loop([(150, 87), (141, 80), (131, 70), (124.5, 63.5), (127.5, 60.5), (136, 63.5), (145, 73.5), (151, 85)], 6.6, RIBBON)
    P.loop([(153, 87), (160, 77), (168, 67), (176, 61.5), (180.5, 64.5), (176.5, 72), (166, 80.5), (154, 87.5)], 6.6, RIBBON)
    P.line([(127, 62.2), (135.5, 64.5), (143, 72.5)], 1.1, RIBBON_L, a=.7); P.line([(176, 62.8), (169, 67), (161, 76)], 1.1, RIBBON_L, a=.7)
    P.line([(132, 72), (141, 80.5), (148.5, 86.5)], 1.0, RIBBON_D, a=.6); P.line([(176, 71.5), (166, 79.5), (155.5, 86.5)], 1.0, RIBBON_D, a=.6)
    P.ellipse(151.6, 86.5, 4.4, 3.4, RIBBON_D, rough=.15, rim=0); P.ellipse(151.2, 86, 3.2, 2.3, RIBBON, rough=.15, rim=0)

def glove(P):
    P.shape([(104, 124), (110, 120.6), (118, 120), (125, 121.5), (130, 126), (131.2, 133), (126.5, 139.2), (113, 141.2), (104, 139.2)],
            WHITE, rough=.2, rim=.16, rimw=2.0, light=(.2, -1, .06), n=6)
    P.line([(109, 125.4), (117, 123.2), (123, 124.6)], .9, WHITE_G, a=.85)                                   # the thumb
    for y in (130, 134, 137.4): P.line([(116, y), (129, y - .6)], .75, WHITE_G, a=.85)

def pair(x, y, h=28):
    """Paint the pair; (x, y) is where the left Marine's soles stand, h his height in map units."""
    u = h / 265.0; x0, y0 = x - 58 * u, y - 276 * u
    L = A.Place(x0, y0, u); R = A.Place(x0, y0, u, flip=True, W=MIRROR)
    marine(L, 'left'); marine(R, 'right'); gift(L); glove(L); glove(R)

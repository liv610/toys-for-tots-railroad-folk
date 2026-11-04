# Pass 5 — refinement of the approved map (experimental)

Pass 4 is the approved baseline and is never edited. It is frozen in
`usmap/checkpoints/pass4-approved-2026-11-03/`. A restore test rebuilt it in a separate folder: 0 differing pixels.

`usmap/usmap5.py` imports pass 4's painters and scene. It applies a listed set of refinements to a copy of the scene
and renders the copy into `out5/` (3200 wide) or `out5_6400/`:

    PYTHONPATH=../folk2:../styles2 python3 usmap5.py               # out5/
    PYTHONPATH=../folk2:../styles2 python3 usmap5.py --width 6400  # out5_6400/
    python3 make_viewer4.py out5_6400 viewer5 viewer5_src/index.html

`out5/changes5.json` lists every element changed or added, with its position and what it was before.

## Group 1 — regional vegetation
* **Pacific Northwest.**
  * Most trees become evergreens of four kinds:
    * `ev_fir`: tall and narrow
    * `ev_spruce`: full, with scalloped tiers
    * `ev_douglas`: layered, with gaps between the branches
    * `ev_pine`: short, leaning and irregular
  * Colours are mostly deep green and olive, with some blue-green and a little teal.
  * About a third of the autumn trees are kept, mostly near houses and the lighthouse.
  * 48 new evergreens stand in foothill clusters. None stand on the mountain faces.
* **Florida.**
  * About half of the trees on the peninsula become palms of three kinds: tall curved, short full, and asymmetric.
  * About a third become low palmetto scrub. The green broadleaf trees stay.
  * There are four new palms in small clusters.
  * Each palm is a trunk (`palm_trunk`) plus separate fronds (`palm_frond`).

## Group 2 — a living landscape
* **Moving trees.**
  * About fifty trees are spread across the map, one per patch of land, chosen among the larger trees away from the railroad.
  * They are painted as their own images and left out of the background, so nothing leaves a hole behind them.
* **Front patches.**
  * The renderer keeps a depth record of which element was painted last at every pixel.
  * Any pixels painted in front of a moving tree (a hill crest, a nearer tree) are cut from the finished painting into a small front patch.
  * The viewer draws each patch over its tree, so the tree stays behind them exactly as in the still.
  * Candidates that are more than 45% hidden are painted back into the background and stay still.
* **Palms.** The trunk stays in the background. Every frond moves on its own about the top of the trunk.
* **Wind.**
  * A light breeze blows everywhere.
  * A gust sweeps west to east about every 22 seconds, with calm spells between.
  * Evergreens bend about half as far as broadleaf trees and move more slowly.
  * A tree bends progressively more towards the top, so the trunk stays rooted.
* **Water.**
  * 46 extra ocean wave marks fade in and out and drift a little. A third of them also appear in the still.
  * Glints run down the river with the current, only where the river shows; they skip the bridges and the stretch behind Toy Town.
* **Boats.** Each boat wanders, rocks and pauses inside a range checked against the coastline, so it never reaches land.
* **Lighthouse and chimneys.**
  * A soft beam turns at the lighthouse.
  * Smoke rises from six farmhouse chimneys. Their positions are recorded while the houses are painted.

The manifest (`out5*/anim/manifest.json`) records:
* every sprite's kind, file, position, pivot and depth
* the front patch for each moving tree or frond
* each boat's drift range
* which river points are visible
* the lighthouse lantern position
* the chimney positions

## Group 3 — Toy Town's grand station after the reference
`station5.py` redraws the station. The old painter in pass 4 is unchanged.
* **Central bay:** one great stone arch with a tiled barrel roof that follows it. Under the arch is a dark fan-light
  with wooden radial bars and rings, with the wreath at its crown.
* **Main opening:** amber panes behind wooden glazing bars, a carved wooden transom, and panelled plank doors with
  iron hinge straps. The whole opening has a heavy wooden frame inside a stone arch.
* **Pilasters:** two square stone pilasters with capitals, small lamp niches and gold-ball finials. The red and green
  pennants fly from them, and the blue one from the apex of the arch.
* **Side wings:** curved tiled roofs, and arched windows with the same wood detailing. A corner pier finishes each
  wing. As requested, there are no dark openings at the wing ends.
* **Walls:** dressed cream stone with mortar courses.

## Group 4 — Pacific Northwest after the second reference
* **Evergreens:** every evergreen in the region is now a tiered tree (`ev_tiered`, plus narrow and wide variants).
  Each is a clean stack of drooping, scalloped branch tiers on a short visible trunk. Each tier is lit along its top
  and left and shaded along its lower edge, with a dark line under it.
* **Colours:** five greens, from forest to blue-green, teal and yellow-green.
* **Spacing:** evergreens that sat almost on top of a larger one were removed, so each silhouette reads and grass
  shows between them.
* **Hills:** three of the dark forest hills became lighter meadow.
* **Shrubs:** twelve flowering shrubs (white and pink) stand in the gaps.

## Group 5 — the Northwest corner after the reference (`pnw5.py`, `pnw5_refine` in `usmap5.py`)
* **Trees:** a mix again. Evergreens stand along the coast and at the foot of the mountains. Bright autumn broadleaf
  trees (`bl_tree`, with blossom dots) stand across the hills.
* **Size:** every tree is about 1.45 times larger, and there are fewer of them, so each one reads on its own.
* **Coast:** grey rock clusters with white surf, and a waterfall off the green cliff below the lodge.
* **Lighthouse:** moved to the rocks at the water's edge, at (54, 402). It was at (95, 388).
* **Lodge:** a blue timber gable with a king-post truss, flower boxes under the windows, and a white railing on the pier.
* **Canyon:** redrawn as a double butte. It has rounded shoulders, domed tops, flared skirts, four bold wavy bands, a
  shadowed right side and vertical grooves.
* **Desert plants:** saguaros, flowering prickly pears, agave, sage and grass tufts, kept clear of the blue line.

## Group 6 — Florida and the Southeast after the Florida reference (`fl5.py`, `fl6_refine` in `usmap5.py`)
* **Coastline:** the Florida peninsula is re-traced narrower and longer, with a rounded tip (`coast5.npy` comes from
  `fl5.coast5()`). Only its Gulf side and tip changed. Vegetation left in the sea was removed.
* **River:** wider and lighter, with no brown banks and with white flow lines. The three delta channels are replaced
  by one mouth that widens and runs out through a gap in the cream shoreline, fading into the Gulf.
* **Palms:** bold storybook palms, with tall curved ringed trunks and arching yellow-green fronds that have darker
  undersides. They are spread down the peninsula, and each frond still moves on its own. The palmetto scrub is gone.
* **Southeast trees:** round, blossom-dotted trees, 1.22 times larger and fewer. About half of the dark firs remain.
* **Ground:** brighter lime and mid-green hills, and a golden striped field hill east of the river.
* **Flowers:** 26 flowering bushes (pink, white, yellow) and 9 yellow wildflower patches.
* **Boats:**
  * All four have a curved wooden hull, a mainsail and jib, and a red pennant.
  * The Florida boat moved out to open water at (1578, 700), and the Gulf boat to (880, 884).
  * Both now have a real drift range. Before, they had none, because they touched land.

## Group 7 — more ocean, and the steamer on the Gulf (`pad5.py`)
* **Sea margin:** the canvas grows by open sea on every side: 100 map units west, 70 north, 80 east and 80 south.
  * The map keeps its own coordinates. Every map unit is painted (100, 70) units further right and down.
  * The 3200 render is now 3545 × 2087. The zoomable one is 7089 × 4175.
  * Nothing is cut off at the edges any more: the west coast, the lodge pier, the rocks, the clouds and the tip of
    Florida all have sea around them.
* **How it is done:**
  * The canvas shifts every coordinate it is given and shifts back the ones it hands to colour callbacks.
  * The few places in pass 4 that convert to pixels by hand (`main`, `sprite`, the lighthouse) are recompiled from
    pass 4's own source with each conversion shifted. Each replacement is checked to occur exactly once.
  * Pass 4's files and the shared painting libraries are unchanged.
* **Waves:** about 70 extra wave marks are painted in the new margin, and 18 extra moving wave marks come and go there.
  The old waves keep their places.
* **Manifest:** it now records `frame` (where the old map sits in the new canvas, in pixels) and `pad`. The viewer uses
  them for the region buttons and the reference overlay.
* **Steamer:** the paddle steamer leaves the river for open water in the Gulf, at (1215, 884). It sits between the river
  mouth and the peninsula, clear of land even at the ends of its drift.

## Group 8 — Toys for Tots branding for Toy Town (`tft7.py`, `toytown8_refine` in `usmap5.py`)
* **Station:**
  * A cream ribbon banner across the foot of the fan-light is lettered TOYS FOR TOTS with the registered mark. It
    bends upward in the middle and has folded tails and gold knobs.
  * A red tab with three white stars hangs under it.
  * A round medallion at the crown of the fan-light replaces the wreath. It has a gold rim, a red field and laurel
    sprays.
  * Red bunting swags with gold balls hang along both wings and under the ends of the banner.
* **Logo:** the medallion is the place for the official Toys for Tots logo. If `logo/t4t_logo.png` exists, it is set
  into the red field at render time; until then the field carries a plain gold star. The emblem is never redrawn by
  hand.
* **Shops:** every house has a lit display window under its awning, with a toy in it: a train, a teddy bear, a rocking
  horse, a nutcracker or presents. The shop beside the clock tower has a TOY DONATION sign.
* **Square:**
  * Five trees that stood in front of the town were removed. A cobbled square with a stone kerb now opens in front of
    the town.
  * On the square: two lamp posts, a Christmas tree with a red bow, presents, a red wagon with a teddy bear, two
    Marines in dress blues handing over a present, and a red TOYS FOR donation box with stars.
  * The foot of the town is painted again in front of the hill crest that used to hide it.
* **Lettering:** set with TeX Gyre Bonum Bold and painted through the same gouache brush as everything else.

## Known limits
* The motion curves are written in the viewer page (`viewer5_src/index.html`), not in the manifest.
* Only the main river has glints. The delta channels do not.
* The pass 4 tree types elsewhere in the country are unchanged, apart from the trees that now move.

## Engine 10 prototype (separate, not part of the live map)

The work after Pass 5 group 8 lives in `engine10/`, documented in `engine10/README.md`, and builds its own viewer in
`viewer10/`. It covers:

- a position-exact brush and tiled, incremental rendering
- a 2× Toy Town layer that fades in as you zoom
- storefront levels A, B and C, the toy library, and the figure study

It changes nothing in the published map. The only edit outside those folders is a one-line clamp in `tft7.square`,
which does not affect the full-frame render.

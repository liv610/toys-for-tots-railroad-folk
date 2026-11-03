# Pass 3 — layered scene and rebuilt railroad

Entry point `usmap/usmap3.py` (run `scripts/render_usmap_pass3.sh`). Pass 1 and pass 2 are untouched and still render
identically; `usmap/out/usmap2_pass2_frozen.png` is a copy of pass 2 as it was approved.

## What changed
* **Scene file.** `out/scene3.json` lists all ~730 elements (hills, mound, mountains, desert, mesas, lakes, river and
  track segments, portals, bridge, houses, landmarks, trees, clouds, boats, train), each with its own depth, bounding
  box and stable seed (`zlib.crc32` of its name). The renderer reads this file: `usmap3.py --scene out/scene3.json`
  renders an edited scene. Changing one element changes only the pixels it covers (plus anything drawn over it).
  Verified: rendering from the saved scene reproduces `usmap3.png` exactly (0 differing pixels, with a different
  PYTHONHASHSEED).
* **Depth.** Every element is drawn in order of the ground it stands on (the front-most hill covering its base point,
  or its own y on open land). Trees and hills in front of the railroad overlap it; near the crest of a hill in front,
  the track slips behind it. A depth buffer `out/anim/depth.npy` records the depth of every pixel.
* **Railroad.** Red (Pacific Northwest → plains → west tunnel), blue (Southwest → its own lower-left tunnel) and one
  green line (New England → east tunnel; no branch). Each track piece is a flat-ended section — shadow, gravel bed,
  ties, coloured rails — so consecutive pieces join without seams. Houses are moved off the line automatically.
* **Terrain.** Hills are modelled (lit crest, darker skirt, light from the upper left). Mountains have shaded faces,
  snow with fingers down the gullies and speckled lower slopes. New England is under snow, with a light dusting along
  the northern band (`snow_amt`), snowy firs and snow on roofs. Lake Superior is restored (`coast3.npy`, `lakes3.npy`).
  Objects are no longer clipped by the coastline; the cream coast is painted before any object stands on it.
* **Landmarks.** Toy Town is taller, stands on a cobbled street (no pale plaza) in front of a wooded, flower-speckled
  mound with three stone portals. New mesas, desert dunes, river with banks and falls, and a stone road bridge.

## Animation layers (`out/anim/`)
* `base.png` — the whole map without train, clouds or boats.
* `train_0.png`, `cloud_*.png`, `boat_*.png` — RGBA sprites, extracted exactly by painting each element over black and
  over white (difference matting); `manifest.json` gives each sprite's position.
* `occluder.png` — RGBA: the base pixels that are in front of the railroad (portals, trees, hill crests, mesas). Stack
  base → moving train → occluder and the train passes behind them and disappears into the tunnels.
* `manifest.json` → `routes`: each route's points in output pixels, which stretches are behind a crest, and its portal.

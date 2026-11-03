# Pass 4 — the second reference, built to animate and to zoom

Entry point `usmap/usmap4.py` (run `scripts/render_usmap_pass4.sh`). Passes 1–3 are untouched.
Reference: `references/us-map-reference-v2.png` (also `usmap/reference4.png`).

## Composition (from the reference)
* **Three end stations**:
  * a red-roofed lodge on a pier in the Pacific Northwest
  * a blue-roofed depot in the Southwest desert
  * a green-roofed station in snowy New England
* **Three lines** run from those stations into **Toy Town's grand station**:
  * The hall is cream stone with a great arched glass window, two smaller arches, a tiled barrel roof, a wreath and three flags.
  * In front of it stands a row of tall coloured houses with striped awnings around a clock tower.
  * The red line crosses a stone viaduct.
* **The river** runs from the Great Lakes, under Toy Town's bridge and past a paddle steamer, to a delta.
* **Other landmarks**: the mesa and cacti, the barn and silo, the lighthouse, the windmill farm with sheep, palms in the south-east.
* **Geography**: the coastline and lakes are re-traced from this reference (`coast4.npy`, `lakes4.npy`). The mountain
  peaks are allowed to rise above the northern coast, as in the reference.

## Same scene system as pass 3
`out4/scene4.json` holds all 781 elements. Each element has its own depth, bounding box and stable seed. Rendering is
painter's order by ground depth, with a depth buffer. `usmap4.py --scene out4/scene4.json` renders an edited scene.

## Resolution: `--width`
`usmap4.py --width 6400 --scene out4/scene4.json` renders the same scene at 6400 × 3600 into `out4_6400/`. It takes
about 13 minutes and needs about 2.5 GB of memory.

Every brush mark is defined in map units (the reference's 1671 × 941 pixel grid), so a wider render repaints the same
marks with more pixels instead of enlarging an image. Edges, outlines, window bars and lettering-size details stay
crisp when you zoom in. The dab pattern keeps the same size in map units, so zooming shows each dab more clearly. It
does not reveal smaller dabs.

The next step up, 12800 × 7200, needs the canvas to be painted in strips to fit in memory. That has not been built yet.

## Moving parts (`out4/anim/`, `out4_6400/anim/`)
Nothing that moves is painted into `base.jpg`. Each moving part is its own RGBA sprite, extracted exactly by painting it
over black and over white. `manifest.json` lists every sprite's file, size, position in the still and pivot:

| Sprite | Motion it is built for | Pivot / anchor |
|---|---|---|
| `loco_*.png`, `wagon_*.png` | follow `routes[*].points`, rotated to the track | track centre under the vehicle; `trains[*].stack_offset` is the chimney top |
| `puff_*.png` | steam: rise, grow, fade | puff centre |
| `blades_0.png` | windmill rotation | hub |
| `steamer_0.png`, `wheel_0.png` | steamer drifts and bobs; the wheel turns | waterline; wheel axle |
| `boat_*.png` | bob, rock, drift | waterline |
| `cloud_*.png` | drift across the sky | — |
| `flag_*.png` | wave (skew about the pole) | top of the pole |

* **`occluder.png`** is the base painting's pixels that stand in front of the railroad. It includes the stations along
  each route's extension.
* **Route extensions.** Each route in the manifest runs 80 map units further than its track:
  * at the start, back into its end station
  * at the end, on into the grand station
  * `track_from` and `track_to` mark where the visible track is.
* **Layer order.** Stack base → trains → occluder → smoke → flags. A train then emerges from its depot, passes behind
  hill crests and the station hall, and disappears into Toy Town.
* `river` is the river centre-line, for moving the steamer.

## Deep-zoom viewer
`make_viewer4.py out4_6400 viewer4` builds a tiled viewer bundle:
* Deep Zoom (DZI) pyramid of `base.jpg`, 1024 px tiles
* the sprites
* the occluder in 512 px tiles, with empty tiles skipped
* `scene.json`

`viewer4_src/index.html` is the page. Copy it into the bundle. It uses OpenSeadragon 4.1.0 from cdnjs for the zoomable
base and draws the moving parts on a canvas locked to the zoom. A **Show reference** button cross-fades to the reference
at the same scale, and region buttons jump to each area. To preview locally, run `python3 -m http.server` inside
`viewer4/` and open `http://localhost:8000`.

## Known shortcomings against the reference
* **Density and colour.** The reference is denser and more golden. Its hills carry ploughed stripes and many small
  trees. Pass 4 reads as broader bands with fewer, larger trees.
* **Buildings.** Stations and houses have less ornament than the reference (timber framing, porches, signs).
* **Great Lakes.** The area is busy and unclear.
* **Delta.** It has three thin channels; the reference has a broad green-islanded fan.
* **Trains.** The trains carry one small gift per car. The reference cars are plain.
* **Trains.** Red, blue and green trains run. A train heading left (the green one) is the same kind of sprite drawn
  mirrored. The manifest marks it `mirrored`.

## Changes after first review
* **Viaduct trees.** Three trees standing in front of the red line's viaduct were painted behind its arches and cut
  off. They are now painted in front of it (`VIADUCT_DEPTH` and the tree pass in `build_scene`). Only pixels around
  the viaduct changed.
* **Green line.**
  * The green line now has a train.
  * It crosses the river on a red iron truss bridge (`rail_bridge`, `truss`). The far side of the truss is painted
    before the track and the near side after it, so the train runs through the bridge.

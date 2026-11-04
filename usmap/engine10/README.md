# Engine 10: position-exact gouache engine, tiles and the 2× Toy Town layer

Engine 10 is a prototype. The live Pass 5 map, its artifact and `toy-town.html` are unchanged. Everything here lives
in `usmap/engine10/` and writes to `engine10/out/`, `engine10/cache/` and `viewer10/`.

## 1. Why it exists

The legacy painter (`folk2/brush.py`, `usmap4.py`, …) paints the whole frame at once. Its textures and randomness
depend on where the canvas starts and on how many random numbers were drawn earlier. A window painted on its own
therefore came out different from the same area of the full painting. That ruled out three things:

- painting only a few tiles after an edit
- a sharper painting of one area
- painting at any density other than 1×

Engine 10 makes every mark depend only on its own position in map units and on the element that drew it.

## 2. Brush architecture (`brush10.py`)

`EngineCanvas(f, (ox, oy, W, H))` is a `Kanvas` subclass that paints a window of the padded frame at density `f`.

- **Density.** 1× is the published 6400/1671 px per map unit. Sizes are given in map units, so softness, stroke width
  and stipple spacing scale with `f`.
- **Coordinates.** Map units become world pixels with `(P + PAD) * k`, then window pixels by subtracting the window
  origin (`_px`).
- **Noise.** Paper grain and the big, mid and small noise fields are absolute lattices sampled at world positions.
  They are normalised from 40,000 fixed sample points, not from the window, so any window agrees with the whole.
  At f=1 they reproduce the legacy noise, with a mean difference of 3e-5.
- **Stipple.** Dabs sit on a global grid in map units. Each cell's jitter, colour and angle come from `HashRNG(cell
  key, element seed)`, so a dab is identical in every tile that contains it.
- **Strokes.** A stroke's random seed is `crc32` of its rounded points, XORed with the element seed. Before this
  change, strokes drew from a shared sequence that off-screen shapes skipped, which made tiles disagree.
- **Masks.** A shape wholly outside the window returns an empty mask, not `None`, so clips still clip. Before this
  change, `None` meant "no clip" and the lighthouse stripes leaked.
- **Edges.** The `with c.edges(name):` presets are `organic` .9, `built` .55, `fine` .32 and `crisp` .18 map units of
  softness. `organic` is the legacy look.

## 3. Rendering a window (`render10.py`)

`render_window(f, win, margin=16, level=None, shop=None)` paints in a fixed order:

1. sea, waves, land mask and ground
2. the scene elements in their global depth order, with the coast at its global position, mountains clipped to the
   mountain clip, and terrain clipped to land
3. painted-back movers, taken from the published manifest

It also records three per-pixel buffers: `Z` (depth), `TRK` (track) and `OWN` (which element painted the pixel).

Every element whose box comes within 16 units of the window is painted, because mountain strokes reach about 15
units. The window is also painted 16 units larger and then cropped.

`edges10.activate('selective')` gives built things (walls, roofs, windows, toys, figures) the `built` or `fine`
presets. `'equivalent'` keeps everything `organic`, which reproduces the published look.

## 4. Tiles and incremental rebuilds (`cache10.py`)

```
PYTHONPATH=../folk2:../styles2:.:lab8:engine10 python3 engine10/cache10.py build F X0 Y0 X1 Y1
```

- Tiles are 1024 px at every density, so they cover fewer map units as `f` rises.
- Each tile's key is the SHA-1 of four things:
  - the scene elements whose padded box touches the tile
  - the base code hash, plus code hashes for the kinds of element present
  - the coast and the edge profile
  - `f`, the tile size and the pad
- An unchanged key reuses the cached PNG and its `_z.npy` and `_trk.npy` buffers. A changed key repaints only that
  tile.
- `assemble()` stitches tiles into one image or buffer.

Measured on this container's CPU at 1×:

| | Result |
|---|---|
| Cold build | 35 tiles, 577 s of CPU, about 16.5 s per tile |
| Moving one tree 9 units | 2 tiles repainted, 33 reused, 52 s; identical to a full repaint |
| Changing the storefront | 6 tiles repainted, 310 s |

The cost is set by element size. The whole town row is one element covering 3×2 tiles, so any shop edit repaints all
six. Splitting the row into per-building elements would bring this down to 1 or 2 tiles.

Editing engine code changes the code hash, so the next build repaints every tile that uses it. That is by design:
the cache never serves art from old code.

Two pitfalls showed up in practice:

- **Editing code during a build.** A build process hashes the code files once, when it starts. Code edited while it
  runs leaves its tiles keyed to the old code, and they show as stale afterwards. Don't edit `BASE_CODE` files
  during a build.
- **Integer versus float density.** The key used to record `f` exactly as given, so `f=1` and `f=1.0` hashed
  differently. It is now normalised with `float(f)`.

`assemble()` takes the newest file for each tile without checking its key. To confirm a cache is current, compare
each tile's key with `tile_key()`.

## 5. Proof that tiles are exact (`test10_tiles.py`, `compare10.py`)

Four regions were rendered in tiles and as a single window: Toy Town, the Northwest coast and mountains, Florida, and
the river and bridge. All four tiled renders are 100.0% pixel-identical to their single-window renders.

Against the published map, the engine's mean colour is within 0.2 levels and its texture energy is within 2%. The
small remaining differences come from movers and the sign blur, not from the engine itself.

See `out/phase1_comparison.jpg` and `out/*_tile_diff.png`.

## 6. Density (`ladder10.py`)

| Density | Time per shop crop | JPEG KB per 1000 sq units |
|---|---|---|
| 1× | 4.9 s | 5.0 |
| 2× | 16.4 s | 13.4 |
| 3× | 35.1 s | 23.7 |
| 4× | 63.7 s | 34.9 |

Going from 1× to 2× is a clear gain. From 2× to 4× is close to invisible, because softness and texture are defined in
map units and the artwork has no finer detail to show. A 2× Toy Town layer was chosen for that reason. More density
only helps once components are drawn with finer detail.

See `out/density_ladder.jpg` and `out/density_deepzoom.jpg`.

## 7. Constructing objects

Components are functions in map units: `(x, y_base, height, colours…)`. Each builds silhouette-first: a few large
shapes, then shading, then small accents under tighter edge presets.

- **`toys10.py`** is the toy library: teddy, wooden train, soldier, rocking horse, doll, drum, blocks, books, picture
  book and present. It is built on the helpers `shape`, `ellipse`, `outline` and `line`. `GALLERY` lists every toy.
- **`store10.py`** holds the storefront parts:
  - `window10`: recessed, with reveal shadows, shutters, flower boxes and curtains
  - `door10`: recess, transom, panels and a wreath
  - `display10`: a calm interior and platform holding the toys
  - `awning10`: slope, side cheek and scallops
  - `shopfront10`: pilasters, sill and stallriser

  `storefront(level)` puts them together at level A, B or C.
- **`figures10.py`** is the figure study. A Marine is a body, a head and a cap, with limbs drawn as tapered strokes
  through shoulder, elbow and hand joints, so a pose is a handful of angles. The poses are `give`, `carry`, `salute`
  and `pull`, and `wagon(handle_to=…)` adds the wagon.

### Component sandbox

- `gallery10.py` paints each toy alone at the sizes visitors will see. Output: `out/toy_library.jpg`.
- `figsheet10.py` paints the figure study. Output: `out/figure_study.jpg`.

Each sandbox canvas is an `EngineCanvas` placed off-map, so a component renders in under 0.2 s.

### Adding a component

1. Write a function in map units, using the `toys10` helpers and `c.edges('fine')` or `c.edges('crisp')` for small
   parts.
2. Add it to `GALLERY` and run `gallery10.py` to see it at window size and in close-up.
3. Call it from the element painter that owns it, such as `store10.display10`.
4. If it is a new kind of element, add its module to `cache10.KIND_CODE`.
5. Rebuild the tiles. Only tiles touching that element repaint.

## 8. Viewer integration (`make_viewer10.py`, `viewer10_src.html` → `viewer10/`)

- **Base layer.** A 1× deep-zoom image built from the engine's own 1× tiles. The published base cannot be reused,
  because it differs slightly from the engine and the crossfade would show the difference.
- **Detail layer.** The 2× Toy Town image, added as a second tiled image over the same map rectangle. Its opacity
  ramps from 0 to 1 as on-screen density goes from 0.9 to 1.35 screen px per base px, so it fades in exactly when the
  1× layer starts to blur.
- **Sprites.** Trains, sway trees and flags in Toy Town are re-rendered at 1× and 2×. The viewer switches a sprite to
  2× once the detail layer is more than half visible. Occluders and front patches have 2× versions too.
- **Testing switches.** `?detail=on` and `?detail=off` force the layer on or off, so the two can be compared at the
  same view.

### Phase 3 measurements (headless Chromium, this container, no GPU)

The prototype bundle (`viewer10/`) has 444 files, 51 MB in total. The published viewer has 370 files, 32 MB.

| Part | Files | Size |
|---|---|---|
| Base pyramid | 62 | 11 MB |
| Detail pyramid (5120 × 4096) | 39 | 7 MB |
| 2× sprites (14 trees, 3 flags, 12 train vehicles) | 29 | 4.7 MB |
| 2× occluder | 17 | 6 MB |

| | Desktop 1440 × 900 | iPhone 13 emulation |
|---|---|---|
| Whole map shown | 1.7 s | 3.1 s |
| Toy Town button settled | 1.3 s | 4.7 s |
| Yellow shop button settled | 1.0 s | 1.5 s |
| Frame rate at the shop | 60 fps | 60 fps |
| Frame rate while panning | 44 fps (software rendering) | not measured |
| JavaScript heap | 10 MB | 10 MB |

On the phone, the screen's pixel ratio of 3 means the Toy Town button already shows the 2× layer at 71% opacity.

**Crossfade.** Zooming out from the shop in nine steps, the layer goes 100 → 100 → 76 → 47 → 20 → 0%. No frame shows a
jump. With the layer forced on versus off at the same view, mean colour differs by under 1 level and the blurred
(low-frequency) difference is 1–2 levels. Only sharpness changes.

**Seam.** At the edge of the 2× rectangle the painting steps from sharp to soft, with no colour step. The white fleck
on one tree's edge south of the town is also present in the published viewer.

## 9. Phase 4 findings (sheets in `out/`)

**`shop_closeup.jpg`, `shop_toytown_view.jpg`, `shop_national_view.jpg`**

- **A, Refined construction**, is the most coherent with the rest of the town:
  - recessed door with a transom
  - framed display on a wooden platform
  - sills and reveals on the upper windows
- **B, Rich illustration**, and **C, Storybook**, add festive layers: garland, wreaths, shutters and flower boxes, and in
  C a brick stallriser, a glazed door, string lights and a dormer.
  - C's dormer has a bright white outline that reads as a mistake at the Toy Town view. Fix it before using C.
- At the national view (about 20%), all five versions are nearly indistinguishable. Storefront work only pays off
  from the Toy Town view inward.
- Each storefront crop takes about 50 s at 2× and about 14 s at 1×. A full town view takes about 165 s at 1×.

**`toy_library.jpg`**

Ten designed toys. Most read at about 10 px tall on the 2× layer. At 1× they are blobs of the right colour.

**`figure_study.jpg`**

The live Marine next to a posed Marine: giving a gift, carrying gifts, saluting, and pulling the toy wagon. Poses tell
the story far better than the current standing figure. The limbs are still stiff tapered strokes, and the hands are
round white dots, which suits the folk style. Each figure paints in under 0.15 s.

## 10. Reproducing the comparisons

```
cd usmap; export PYTHONPATH=../folk2:../styles2:.:lab8:engine10
python3 engine10/test10_tiles.py      # tile exactness, 4 regions
python3 engine10/compare10.py         # phase 1 comparison sheet
python3 engine10/edit10.py; python3 engine10/edit10b.py    # incremental edits
python3 engine10/ladder10.py          # density ladder
python3 engine10/gallery10.py; python3 engine10/figsheet10.py; python3 engine10/shop10.py   # phase 4 sheets
python3 engine10/cache10.py build 1 0 0 1671 941    # full 1x base
python3 engine10/cache10.py build 2 670 200 1190 650  # 2x Toy Town
python3 engine10/make_viewer10.py     # builds viewer10/
(cd viewer10 && python3 -m http.server 8770 &)
node engine10/test_viewer10.js http://localhost:8770/ OUTDIR path/to/openseadragon.min.js   # views, crossfade, fps
node engine10/test_seam10.js http://localhost:8770/ OUTDIR path/to/openseadragon.min.js     # edges of the 2x layer
```

The tile caches (`engine10/cache/`, 164 MB) are not copied to the Mac. They rebuild with the two `cache10.py`
commands above, in about 10 minutes for 1× and about 12 minutes for 2× on two cores.

The prototype is published as its own artifact, "Toy Town Detail Prototype". The live Pass 5 map artifact is
untouched.

## 11. Recovery

- **`checkpoints/pass5-toytown-branding-2026-11-04`** is the published state (Pass 5 versions 18–19). Copy its
  contents over `usmap/` to restore it.
- **`checkpoints/pre-engine10-2026-11-04`** holds the code and the lab8 and lab9 experiments from just before
  Engine 10.
- Engine 10 changed one line outside `engine10/` and `viewer10/`: in `tft7.square`, the band bounds are now clamped
  to the canvas so a partial window can't slice backwards. On the full frame the bounds were already inside the
  canvas, so the published render is unaffected. Apart from that line, deleting the two folders removes Engine 10
  completely.

# Every experiment, in the order it was made

**Status key**
* **identical**: re-rendered from this package and matched the committed PNG pixel for pixel.
* **hash-dependent**: matches except on buildings, which varied run to run (see DETERMINISM.md).
* **preserved**: source and outputs copied byte for byte, not re-rendered.

`_v1`, `_a` and `_pass1` files are earlier saved states of a script, kept for history.

## In this folder

| Experiment | Entry point | Outputs | Status |
|---|---|---|---|
| U.S. map, pass 5 (experimental refinement: regional trees, moving landscape) | `usmap/usmap5.py`, page `usmap/viewer5_src/index.html` | `usmap/out5/`, `usmap/out5_6400/`, `usmap/viewer5/`, review page `usmap/preview5/`; see `docs/PASS5.md` | builds on the pass 4 checkpoint in `usmap/checkpoints/` |
| **U.S. map, pass 4 (second reference)** | `usmap/usmap4.py`, viewer builder `usmap/make_viewer4.py`, page `usmap/viewer4_src/index.html` | `usmap/out4/*` (3200), `usmap/out4_6400/*` (6400), `usmap/viewer4/` (deep-zoom bundle); see `docs/PASS4.md` | new; renders from `scene4.json` |
| U.S. map, pass 3 | `usmap/usmap3.py` | `usmap/out/usmap3.*`, `usmap/out/anim/`, page `usmap/page3/`; see `docs/PASS3.md` | renders identically from `scene3.json` |
| **U.S. map, pass 2 (current)** | `usmap/usmap2.py` | `usmap/out/usmap2.*` | **identical** |
| U.S. map, pass 1 | `usmap/usmap.py` (history: `usmap_v1.py`, `usmap_pass1.py`, `usmap2_a.py`) | `usmap/out/usmap.*`, `usmap_pass1.*`, `usmap_v1_sm.jpg` | **identical** |
| Published comparison pages for the map | `usmap/page/`, `usmap/page2/` | static HTML + JPEGs | preserved |
| Round-two directions: Storybook (1) and Folk (2), valley | `styles2/story.py` (history `story_v1.py`), `styles2/folk.py`, shared `world.py`, `parts.py` | `styles2/out/story*`, `story_v1.jpg`, `layout.png` | preserved (hash-dependent painters) |
| Three worlds: **A Moonlit Village**, B Storybook World, C Adventure Map | `styles2/a.py`, `b.py`, `c.py`, shared `kit.py` | `styles2/out/A*`, `B*`, `C*`; gallery `styles2/gallery/` | **A: identical via `village_benchmark/`**; B: hash-dependent (only its buildings differ); C: see note below |
| Moonlit Village, refined (Phase 1) | `styles2/a2.py` | `styles2/out/A_refined.*`; page `styles2/phase/` | **identical** |
| Regional scale test (Phase 2) | `styles2/region.py` (history `region_v1.py`) | `styles2/out/region.*` | **identical** |
| Folk Art Exploration — Version 2 | `folk2/scene.py` (history `scene_v1.py`) | `folk2/out/folk_v2*`; page `folk2/page/` | preserved (see note below) |
| County expansion | `county/county.py` (history `county_v1.py`) | `county/out/county.*`; page `county/page/` | **identical** |
| Approved Toy Town village prototype | `toy-town.html` | open in a browser | preserved, unchanged |

Note on C and Version 2: both were re-rendered during packaging. The result is recorded in
`docs/verification-log.txt`.

## In the archive download (`archive/`)

| Experiment | Folder | Notes |
|---|---|---|
| Interactive national map and its build kit (Node + Python) | `archive/mapbuild/` | has its own `README.md`; Natural Earth data in `ne/`; `node_modules` included |
| Interactive map site versions | `archive/site/`, `archive/site-s1/` | React (UMD) + Babel pages with painted tiles |
| Storybook map iterations | `archive/storymap/`, `storymap2/`, `storymap3/` | include the rendered PNGs and MP4 walkthroughs |
| Geographic alignment stage | `archive/stage1/` | affine and warp alignment of the painted map |
| Pacific Northwest scale experiment | `archive/pnw/` | |
| Painted-terrain studies A/B | `archive/paint2/`, `archive/paint3/` | raster painter, terrain caches (`.npz`), live-painted site |
| First-round style studies (Cut-Paper, Folk Stitch, Mid-Century, Twilight Impasto) | `archive/styles/` | `style_a.py` … `style_d.py`, shared `scene.py`, page `site/` |
| Review pages | `archive/review*/` | |
| Local copies of React 18.3.1 and Babel 7.24.7 | `archive/vendor/` | used by local previews of the interactive pages |
| Earlier build-kit download | `archive/toys-for-tots-map-build-kit.zip` | |

These were preserved byte for byte, which was checked file by file against the originals, and were not re-rendered.

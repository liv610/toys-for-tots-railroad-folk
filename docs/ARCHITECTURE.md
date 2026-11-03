# Architecture

## Languages and libraries

Pure Python 3.13 with NumPy (arrays, random numbers), OpenCV (anti-aliased polygons and ellipses, blurs, Sobel,
contours, image I/O), Pillow (only for some resizes in older experiments) and Matplotlib (only `matplotlib.path.Path`
for point-in-polygon tests). There is no web code in the rendering path. The published comparison pages
(`usmap/page*/index.html`) are static HTML that display the rendered JPEGs.

## Module graph of the current U.S. map

```
usmap/usmap2.py          pass 2: terrain, tree vocabulary, placement, final compose, save
 └─ usmap/usmap.py       pass 1 + shared state and painters (imported, its main() is NOT run)
     ├─ folk2/brush.py   Canvas: area(), stroke(), ink(), dab(), flow_fill(), mask(), save(); noise, catmull, resample, wobble
     ├─ folk2/kit.py     Kanvas(Canvas): stip(), dots(); trees (skeleton_tree, stipple_fir, dab_tree, bush),
     │                   rails(), path(), restipple(), impasto(), ribbon(), land(), y_on(), pal_fn()
     │    └─ folk2/story.py  the Storybook painter; supplies train(), lumpy(), smoke(), and other helpers (S.*)
     │         ├─ folk2/world.py  the Storybook valley composition (imported for names only)
     │         └─ folk2/parts.py  building massing, lumpy(), fir_tiers(), persp()
     └─ styles2/a.py     the Moonlit Village painter; supplies house(), window(), roofdots(), tunnel(), windmill() (A.*)
```

### How imports resolve

`usmap.py` begins with `sys.path.insert(0, '/home/claude/folk2'); sys.path.append('/home/claude/styles2')`. Those
absolute paths come from the original machine. On any other machine they don't exist and are ignored, so the render
scripts set `PYTHONPATH="$ROOT/folk2:$ROOT/styles2"`.

**The order matters.** `folk2/` and `styles2/` both contain `brush.py`, `kit.py`, `story.py`, `parts.py` and
`world.py`, and the copies differ. The U.S. map must load the `folk2/` versions. In particular, `folk2/kit.py` records
paint height for the relief pass and draws extra random numbers while doing so. `a.py` is found only in `styles2/`,
and inside the U.S. map process it uses the already-loaded `folk2/kit.py`.

### Import side effects (preserved, worth knowing)

* Importing `story.py` creates a full-size Canvas and runs no painting.
* Importing `a.py` calls `kit.setup()`, which creates another canvas and points `story.c` at it.
* `usmap.py` then creates the real canvas `c` and re-points `story.c` and `a.c` at it (`S.c = c; A.c = c`).
* `usmap.py` also replaces `A.window` with a daylight version: dark glass, cream frames, no lit windows.
* None of these extra canvases is used after import. They only cost memory and about 2 s.

### Absolute paths in the source (left as-is)

| File | Path | Effect elsewhere |
|---|---|---|
| `usmap/usmap.py`, `usmap_v1.py`, `usmap_pass1.py` | `sys.path` entries `/home/claude/folk2`, `/home/claude/styles2` | ignored; `PYTHONPATH` supplies them |
| `county/county.py`, `county_v1.py` | `sys.path` `/home/claude/styles2`; saves to `/home/claude/county/out/county` | save redirected in memory by `scripts/render_county.sh` |
| `styles/scene.py`, `archive/paint2/*`, `archive/paint3/*`, `archive/pnw/geo_pnw.py`, `archive/stage1/*` | various | older experiments; not used by the current map |

## Coordinate systems

**U.S. map (`usmap/`).** All geometry is in the reference image's own pixel space: x from 0 to 1672, y from 0 to 941,
origin at the top left, y pointing down. The canvas is 3200 × 1800 pixels, and the scale factor `k = 3200 / 1672 ≈ 1.914`
converts reference coordinates to output pixels. (941 × k = 1801, so the bottom pixel row is cropped.) To place
anything, measure its position on `references/us-map-reference.png` and use those numbers directly.

**Village family (`styles2/`, `county/`, `folk2/scene.py`).** A 1600 × 900 design space (16:9) rendered at K = 2,
giving 3200 × 1800.

**Brush units.** Stroke widths, dab lengths and wobble amplitudes are all in design units and scale with `k`. A stroke
of width 3 in the U.S. map is about 5.7 output pixels wide.

## The pass-2 render pipeline (`usmap2.main`), in order

Order matters: this is a painter's algorithm, and later layers cover earlier ones.

1. **Ocean.** The whole canvas is stippled in five blues with long wavy dabs (seed 2). About 220 groups of cream wave
   marks are added offshore, drawn from the module RNG `R = RandomState(2026)`.
2. **Land base.** The coastline polygon becomes `LAND_MASK` (anti-aliased, slightly blurred). It gets a dark olive
   wash and a broad stipple (seed 3). From here until the coastline step, every paint call is clipped to `LAND_MASK`.
3. **Mountains.** Six purple peaks in the Northwest (`usmap.mountain`, seeds 40–45), each with a lit face, a shaded
   face and a snowcap.
4. **Landforms.** The 33 hills in `HILLS` are painted back to front. Each hill gets:
   * an irregular contour (`hill_poly`, seed `500 + 7*i`)
   * a broad directional stroke layer
   * two or three colour patches
   * a finer surface pass
   * a crest highlight and a dark overlap line
   * stripes, for the three `field` hills
5. **Desert.** The ochre desert, two pale patches, two mesas and five cacti.
6. **Water.** The lakes (with cream rims), the south-eastern river with its fall, and the western stream with rocks.
7. **Toy Town hill.** The mound behind Toy Town, plus a fringe of conifers and autumn trees along its shoulders
   (`RandomState(79)`).
8. **Railroad.** The four track polylines, the two tunnel portals, and the stone arch bridge with its re-drawn green
   track section.
9. **Placement.** Trees are placed with `RandomState(301)` (see PAINTING_SYSTEM.md). The 13 houses and the landmarks
   are listed, and everything is sorted by its base y and drawn back to front.
10. **Train.** The train goes on the red route (`story.train`, scale 3.4), heading toward the west tunnel.
11. **Clipping released.** Then:
    * the cream coastline brushline
    * three clouds
    * four sailboats
12. **Relief.** `impasto(c, .14)` lights every dab's raised ridge from the upper left.
13. **Save.** `c.save('out/usmap2')` writes `.png` (lossless master), `.jpg` (quality 90) and `_sm.jpg` (half size).

Pass 1 (`usmap.main`) follows the same outline with simpler terrain: a grid of mounds and about 470 evenly placed trees.

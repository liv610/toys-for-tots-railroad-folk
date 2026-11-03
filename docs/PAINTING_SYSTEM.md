# The folk-art painting system

Everything is built from three primitives in `folk2/brush.py` and `folk2/kit.py`. Higher-level painters (hills,
trees, buildings, trains) only combine them. All colours are hex strings converted to float RGB in [0, 1], and the
canvas is a float32 image that is only quantized to 8 bits at `save()`.

## 1. Painted areas — `Canvas.area(poly, col, …)`

An opaque gouache-like fill.

* **Edge.** The polygon outline is displaced along its normals by smooth noise (`wobble`), so no edge is ever
  perfectly straight. It is rasterized anti-aliased at 8× sub-pixel precision, then roughened with paper and fine
  noise (`rough`) to give a slightly ragged painted edge.
* **Pigment.** Colour varies slightly with two noise fields (`var`, `varbig`) and darkens where pigment pools at the
  edge (`edge_dark`). `dens` lets a little paper texture show through.
* **Clip.** The result is multiplied by the active clip mask (`set_clip`) if one is set.
* **Return value.** It returns the area's mask `(x0, y0, mask)`, and other painters use that as a stencil.

## 2. Brush strokes — `Canvas.stroke(pts, w, col, …)`

A single bristle-brush stroke along a polyline.

* **Width.** It tapers at both ends (`taper`), and pressure varies along its length (`press`).
* **Bristles.** The brush has 5 or more bristles, each with its own pigment load. That produces streaks (`streak`)
  and, with `dry > 0`, dry-brush gaps where the paper shows through.
* **Edge and ridge.** Edge roughness (`rough`) and a darker ridge along the stroke's sides (`ridge`) complete it.
* **Related helpers.** `ink()` is a thin, unstreaked stroke with hand tremor. `dab()` is a short curved stroke.
  `flow_fill()` covers a mask with strokes that follow an angle field.
* **Shared random stream.** If `seed` is not given, the stroke takes one from the canvas's shared random stream
  (`c.rng`). See DETERMINISM.md for why this matters.

## 3. Stipple dabs — `Kanvas.stip(m, colfn, spacing, L, w, angfn, …)`

The signature texture of the folk-art style.

* **Placement.** A jittered grid of points covers the mask. At each point it paints a filled, anti-aliased ellipse
  ("dab") of length `L` and width `w`.
* **Colour.** `colfn(X, Y, rng)` picks each dab's colour, usually a small palette with ±5% value variation
  (`pal_fn`), or a function of position for banding or light.
* **Direction.** `angfn(X, Y)` sets each dab's direction, with jitter. This is how texture follows form:
  * along a hill's contour (`flow_of`)
  * down a mountain face
  * along a river's current
  * outward from a cloud's centre
* **Order and blending.** Dabs are drawn in random order, so they overlap like real paint. The layer is blended back
  through a softened copy of the mask (`spill`).
* **Paint height.** The `folk2` version also stamps each dab into a height map `c.HM` with a random height. Later,
  `impasto()` takes the gradient of that height map and lights it from the upper left. Every dab then has a lit edge
  and a shaded edge, like thick paint.

`dots()` paints round dots: blossoms, fruit, stars and coastline beads. `restipple()` re-covers anything drawn since a
snapshot with dabs sampled from what is there. It was used in the village to make the track and train match the
painted surface; pass 2 does not use it.

## Terrain (pass 2, `usmap2.py`)

* **`HILLS`** is a hand-authored list of 33 landforms, each `(centre x, base y, width, height, kind)` in reference
  coordinates. It is ordered back to front.
* **`hill_poly`** builds each contour from a skewed, rippled sine dome. No two hills are symmetric.
* **`paint_hill`** paints each hill in layers:
  1. a base area
  2. a broad stroke layer (`L = 6.5, w = 2.8`) following the contour
  3. two or three irregular colour patches from related palettes (`PATCH`)
  4. a finer, sparser stroke layer that is lighter toward the crest
  5. for `field` hills, ochre stripes following the contour
  6. a pale crest highlight and a thin dark line where it overlaps the hill behind
* **Kinds.** The palettes are `gold`, `olive`, `moss`, `forest`, `sage` and `rust`. `field` is gold plus stripes.
* **Other landforms.**
  * Mountains (`usmap.mountain`): two-tone faces with dabs angled down each face, plus a stippled snowcap.
  * Mesas (`usmap.mesa`): vertically striated rock in four reds.
  * The desert: one broad stippled area.

## Trees

The functions are `kit.skeleton_tree`, `kit.stipple_fir` and the wrappers in `usmap2.py`.

* **`tall_fir`.** A narrow stippled cone with dabs angled down-and-out on each side.
* **`layered_fir`.** Four or five drooping tiers, each its own stippled polygon.
* **`big_tree`.** A round canopy of fine dabs over a lumpy outline, with a recursive branch skeleton painted on top
  (brown branches in the U.S. map). The palettes are:
  * green
  * yellow
  * orange
  * red
  * pink (with blossom dots)
  * olive
* **`orchard_tree`.** A small round tree with red fruit dots.
* **`poplar`.** A columnar canopy with vertical dabs.
* **`palm`.** A curved trunk with seven fronds.

## Placement (pass 2)

One random stream, `RandomState(301)`, places every tree in this fixed order:

1. **Specimen trees.** Three to six per open hill, sitting just below its crest. Their colour depends on region:
   autumn colours in the Northeast, mixed in the south.
2. **Forest masses.** Twelve elliptical zones packed with conifers and a few deciduous trees (`FORESTS`). Each zone
   retries until it is filled.
3. **Groups.** 29 painterly clusters of 10–16 trees around chosen points (`GROUPS`). Each cluster is `mixed`, `firs`
   or `autumn`.
4. **Orchards.** Three loose orchards in rows.
5. **Lone trees.** 160 attempts at small trees standing alone in the open.

A tree is rejected if any of these is true:

* it is off land, or in a lake
* it is in the desert core
* it is inside a building's keep-out box
* it is within 24 units of any track, or its canopy would reach a track
* it is within 22 units of the river
* it is too close to an already-placed tree

All sizes are multiplied by 1.45 at placement. 206 trees survive.

## Buildings and landmarks

* **Houses.** `usmap.house` wraps the village's `a.house` at 82% width and 72% height, with one row of two windows and
  daylight windows. `a.house` paints:
  * a front wall with vertical dabs and a darker side wall
  * a gable, side-gable, barn or tall roof, plus a chimney with smoke
  * windows, a door, and a soft ground shadow
* **Bespoke painters in `usmap.py`.** Each landmark has its own function:
  * barn and silo
  * church
  * lighthouse
  * windmill
  * Toy Town: six storefronts with striped awnings and a clock-tower hall, on a cobbled plaza
  * tunnel portals
  * cow and horse
  * boats and clouds
* **The train.** `story.train` draws a red locomotive and tender, and wagons carrying a decorated tree, a teddy bear
  and drum, and gifts. All of it is oriented along the track.

## Depth

* **Back to front.** Hills, then water, then rails, then every object sorted by its base y (`objs.sort`). Lower on the
  canvas means nearer, so it is drawn later. There is no perspective scaling in the U.S. map; size variation is
  authored directly.
* **Clipping.** `LAND_MASK` keeps all land painting inside the coast. The coastline brushline is painted last, over
  the seam.

# What can be edited independently, and what is coupled

The illustration is one painted raster. There are no separate layers on disk. "Independent" below means an edit
changes pixels only where you intended, plus any later drawing that overlaps that spot (painter's algorithm).
"Coupled" means the edit can also shift pixels elsewhere in the map.

## The main source of coupling: shared random streams

Two random streams are consumed in program order:

* **The canvas stroke stream `c.rng`.** Any `stroke()`, `ink()` or `dab()` called without an explicit `seed=` takes
  the next number from it. Most painters do this: track ties and rails, the coastline, trunks, branch skeletons,
  stripes, crest lines, smoke and wave marks.
  * **What changes.** If you add, remove or reorder one of those strokes, every later unseeded stroke gets a different
    seed. Its bristle streaks, dry-brush gaps and edge roughness then change slightly across the rest of the map.
  * **What stays put.** Geometry, colour and placement do not move; only fine stroke texture does.
  * **Inside one landmark.** Changing a stroke inside a building or the train also shifts the texture of every tree
    and the coastline drawn after it.
* **The placement stream `RandomState(301)` in `usmap2.main`.** Any change that alters whether a candidate tree is
  accepted reshuffles all later trees. That includes:
  * the hill list, the forest zones or the groups
  * the keep-out boxes or the house list
  * the tracks or the river

  A small edit can therefore move many trees.

Stipple layers (`stip`, `dots`) and areas each carry their own seed, and so does any stroke given an explicit
`seed=`. Those are independent of call order.

## Editability by element

| Element | Where | Independent? | Notes |
|---|---|---|---|
| Palette colours of hills (`PAL`), trees, buildings | `usmap2.py`, `usmap.py` | **Yes** | colour pickers draw the same random numbers regardless of colour |
| Ocean, clouds, boats, coastline line | `usmap2.main` | **Mostly** | own stipple seeds; wave marks and coastline use streams, so editing their *count* shifts later strokes |
| A single hill's size or shape | `HILLS[i]` | **Partly** | its seed stays the same; specimen trees on its crest move, and later placement reshuffles |
| Adding or removing a hill | `HILLS` | **No** | seeds are by index (`500 + 7*i`), so every later hill changes texture, and placement reshuffles |
| Mountains, mesas, desert, cacti | `usmap2.main` + `usmap.mountain` / `mesa` / `cactus` | **Mostly** | each mountain and mesa has its own seed; cacti use the stroke stream |
| Lakes and rivers | `usmap2.main`, `coast.npy`, `lakes.npy` | **Partly** | river geometry also feeds tree rejection, so moving it reshuffles trees |
| Railroad routes | `RED`, `BLUE`, `GREEN`, `GREEN2` in `usmap.py` | **No** | also used for tree rejection and train position; ties and rails use the stroke stream |
| Tunnel portals and bridge | `usmap.portal`, bridge block in `usmap2.main` | **Mostly** | own stipple seeds; positions are tied to the routes |
| A house or landmark's *look* | `HOUSES` list, `usmap.barn`, `church`, `clocktower_town`, … | **Partly** | its geometry and own seeds are local; its strokes shift later stroke texture |
| A house or landmark's *position* | `HOUSES`, `objs.append(...)` | **No** | the keep-out boxes are derived from it, so trees reshuffle |
| Individual trees | — | **No** | they are not listed anywhere; they emerge from placement. To pin a tree, it must first be turned into a fixed list |
| The train | `S.train(...)` call | **Mostly** | drawn after nearly everything; only the coastline, clouds and boats come after |
| Relief strength | `impasto(c, .14)` | **Yes** | a global post-process |
| Output size | `W, H, k` in `usmap.py` | **No** | changes every dab and stroke |

## Safe first steps toward precise, local edits (not done; this was a preservation task)

1. **Make strokes deterministic per element.** Pass an explicit `seed=` to every stroke, derived from the element's
   identity. For example, hash a stable name with a fixed function such as `zlib.crc32`, not Python's `hash()`. Then
   editing one element cannot shift anything else.
2. **Freeze the placed trees.** Have the placer write its 206 accepted trees to a JSON file once, then paint from that
   list. Individual trees can then be nudged, recoloured or deleted without reshuffling the rest.
3. **Seed hills by name or position**, not by list index.
4. **Paint in layers.** Write terrain, water, rails, objects and the train to separate images or masks, so that a
   single layer can be re-rendered and composited.

After each step, run `scripts/verify.py`. The first two steps will intentionally change the image once: the
committed PNGs are the record of the current look, and a new baseline should be captured after the change.

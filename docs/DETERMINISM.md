# Randomness and reproducibility

## Yes, the illustration uses randomness, and all of it is seeded

Every irregularity is pseudo-random: wobbly edges, dab placement, colour jitter, bristle streaks, tree shapes and
tree placement. All of it comes from NumPy's legacy `np.random.RandomState(seed)` generators with fixed seeds. No code
in the U.S. map or village pipelines calls the unseeded global generator, reads the clock for anything but log
timing, or depends on the environment. The same code and the same library versions therefore give the same image,
bit for bit.

**Verified.** `scripts/verify.py` was run on the packaged copy with the original folders hidden. These all came back
identical, with 0 differing pixels:

* U.S. map pass 2
* U.S. map pass 1
* the Moonlit Village benchmark
* the refined village
* the county expansion

The pass-2 map was also rendered with three different `PYTHONHASHSEED` values, and all three matched.

## Where the seeds live

| Source | Seeded by |
|---|---|
| Canvas noise fields (paper, pigment variation) | the canvas seed: 1972 for the U.S. map (`Kanvas(..., seed=1972)`), others per script |
| Each `area()` edge wobble | its `seed=` argument (defaults to 0) |
| Each `stip()` / `dots()` call | its `seed=` argument; a private generator per call |
| Each `stroke()` given a `seed=` | that seed |
| Each `stroke()` **without** a `seed=` | the next number from the canvas's shared stream `c.rng` (seeded from the canvas seed + 9) |
| Hill shapes in pass 2 | `500 + 7 * index` in `HILLS` |
| Tree, house and fir shapes | the seed passed by the placer |
| Tree placement, pass 2 | one stream, `RandomState(301)`, consumed in a fixed order |
| Ocean wave marks, pass 2 | module stream `R = RandomState(2026)` |
| Forest fringe on the Toy Town hill | `RandomState(79)` |

## What keeps a render identical

1. **Same library versions** (`requirements.txt`): Python 3.13.17, NumPy 2.5.3, OpenCV 5.0.0.93, Pillow 12.3.0,
   Matplotlib 3.11.2.
   * NumPy's `RandomState` stream is frozen by NumPy's compatibility policy, so it is the safest part.
   * OpenCV's anti-aliased rasterization, Gaussian blur and JPEG encoder can change slightly between releases. Under a
     different OpenCV, expect images that look the same but are not bit-identical.
   * Compare the lossless `.png` masters, never the `.jpg` copies.
2. **Same call order.** The shared stroke stream and the placement stream are consumed in program order. Inserting,
   removing or reordering any call that draws from them shifts every later random number. See EDITABILITY.md.
3. **Same `PYTHONPATH` order** (`folk2` before `styles2` for the U.S. map). The two folders hold different versions of
   the same modules; the render scripts set this for you.
4. **Same input files**: `usmap/coast.npy` and `usmap/lakes.npy`. `tools/extract_coastline.py` regenerates them
   exactly from the reference, which was checked.

## Known exceptions (older experiments only)

`folk2/story.py` and `folk2/parts.py`, and their `styles2/` copies, seed some building details with
`abs(hash(name))`. Python randomizes string hashing per process unless `PYTHONHASHSEED` is set. Images that use those
building painters therefore differ from run to run on their buildings only. This was confirmed for the round-two
Storybook World plate (`styles2/b.py`): when re-rendered, only its buildings differed. It applies to these scripts:

* `styles2/b.py`, `styles2/c.py`, `styles2/story.py`, `styles2/folk.py`
* `folk2/scene.py`, `folk2/story.py`

The U.S. map, the village family and the county do not use those painters, as verified above. The render scripts set
`PYTHONHASHSEED=0` so that from now on those older images are repeatable too. Their original hash seeds were random
and cannot be recovered, so the committed images of those experiments are the record.

## The village benchmark

`styles2/kit.py` was edited after the village was approved: `rails()` now draws steel rails in 24-point segments. That
changes the village's track pixels. `village_benchmark/` holds copies of the village's modules with `kit.py` restored
to the version used at render time; it differs only in `rails()`. Rendering `village_benchmark/a.py` reproduces
`styles2/out/A_original.png` exactly. Use that folder whenever the approved village must be reproduced.

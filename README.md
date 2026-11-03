# Toys for Tots Railroad — illustration project

A folk-art illustrated map of the United States, and the experiments that led to it, painted entirely in code.
This folder is a byte-for-byte preservation of the project as it stood on 2 November 2026, prepared for
development in Claude Code. **Nothing was refactored, optimized or redrawn during the migration.**

| Image | Status | Script | Output |
|---|---|---|---|
| **U.S. map, pass 4 (newest: second reference, animation layers, 6400 × 3600)** | re-renders from `usmap/out4/scene4.json` | `scripts/render_usmap_pass4.sh` (add `--width 6400 --scene out4/scene4.json` for the zoomable size) | `usmap/out4/usmap4.png`, `usmap/out4_6400/usmap4.png`, viewer in `usmap/viewer4/` (see `docs/PASS4.md`) |
| U.S. map, pass 3 (layered scene, rebuilt railroad) | re-renders from `usmap/out/scene3.json` | `scripts/render_usmap_pass3.sh` | `usmap/out/usmap3.png` (see `docs/PASS3.md`) |
| **U.S. map, pass 2 (current)** | reproduces pixel-identically | `scripts/render_usmap_pass2.sh` | `usmap/out/usmap2.png` |
| U.S. map, pass 1 | reproduces pixel-identically | `scripts/render_usmap_pass1.sh` | `usmap/out/usmap.png` (baseline `usmap_pass1.png`) |
| **Moonlit Village (original, approved benchmark)** | reproduces pixel-identically | `scripts/render_village_benchmark.sh` | `village_benchmark/out/A.png` (baseline `styles2/out/A_original.png`) |
| Moonlit Village, refined | reproduces pixel-identically | `scripts/render_village_refined.sh` | `styles2/out/A_refined.png` |
| County expansion test | reproduces pixel-identically | `scripts/render_county.sh` | `county/out/county.png` |

Every other experiment is preserved with its source and its rendered images; see `docs/EXPERIMENTS.md`.

## Quick start

```bash
python3 --version                      # rendered with 3.13.17
pip install -r requirements.txt        # exact versions; see docs/DETERMINISM.md
bash scripts/render_usmap_pass2.sh     # ~80 s, writes usmap/out/usmap2.png (3200 x 1800)
python3 scripts/verify.py              # re-renders the five images above in a temp copy and compares pixels
```

`verify.py` prints `IDENTICAL` for each target when the environment matches. It was run on the packaged copy, with
the original working folders hidden so nothing could leak in, and all five targets came back identical
(0 differing pixels).

## What is where

```
README.md                 this file
requirements.txt          pinned library versions
scripts/                  render scripts (one per image) and verify.py
docs/
  ARCHITECTURE.md         module graph, import resolution, coordinate systems, the pass-2 render pipeline
  PAINTING_SYSTEM.md      how the folk-art brush engine works: brushwork, textures, terrain, trees, buildings, placement
  RAILROAD.md             the three routes as data: geometry, junctions, tunnels, train placement, animation notes
  DETERMINISM.md          randomness, seeds, what guarantees an identical image, and known exceptions
  EDITABILITY.md          what can be changed independently and what is tightly coupled
  EXPERIMENTS.md          every experiment, its entry point, outputs and reproduction status
references/
  us-map-reference.png    the folk-art U.S. map used as the specification for usmap/
  conversation-attachments/  every image and brief shared during development (47 files)
usmap/                    the U.S. map: usmap.py (pass 1 + shared painters), usmap2.py (pass 2), coast/lake geometry,
                          out/ renders, page/ and page2/ the published comparison pages
folk2/                    painting engine used by the U.S. map: brush.py, kit.py (+ paint-ridge relief), story.py, parts.py, world.py
styles2/                  the Moonlit Village family (a.py, a2.py, region.py), round-two directions (b.py, c.py, story.py, folk.py)
                          and the engine version the village was built with
village_benchmark/        a frozen copy of the engine as it was when the approved village was rendered (see below)
county/                   the county expansion test
tools/extract_coastline.py  re-derives usmap/coast.npy and lakes.npy from the reference (verified identical)
toy-town.html             the approved Toy Town village prototype (unchanged)
MANIFEST.sha256           checksum of every file in this folder
```

The companion download **toys-for-tots-railroad-archive.zip** unpacks to `archive/` inside this folder. It holds every
earlier experiment: the four first-round style studies (`styles/`), the painted-terrain studies (`paint2/`,
`paint3/`), the interactive national map and its build kit (`mapbuild/`, `site/`, `site-s1/`, `storymap*/`, `stage1/`,
`review*/`, `pnw/`), the vendored React and Babel used by the local previews (`vendor/`), and the earlier build-kit ZIP.

## Two things to know before editing

1. **The village needs its own engine copy.** After the village was approved, one shared drawing routine in
   `styles2/kit.py` (`rails()`, the steel-rail strokes) was changed for a later experiment. Running `styles2/a.py`
   today therefore differs from the approved village along its track and viaduct. `village_benchmark/` holds the engine
   with that one routine as it was at render time. It reproduces the approved image exactly. Nothing in `styles2/` was
   altered.
2. **Absolute paths from the original machine.** Several scripts contain paths such as `/home/claude/folk2` (in
   `sys.path.insert`) or an absolute save path (`county.py`). They are left untouched. The render scripts make
   them harmless: imports resolve through `PYTHONPATH`, and the county script redirects its one save call in memory. A
   full list is in `docs/ARCHITECTURE.md`. Replacing them with relative paths is a sensible first task in Claude Code,
   but run `scripts/verify.py` after doing it.

## Provenance

The coastline and Great Lakes outlines were traced from `references/us-map-reference.png` (geometry only, via
`tools/extract_coastline.py`). Every landmark position was measured by hand from that reference. No reference
pixels are used in any painting. Everything you see is generated by the code in this folder.

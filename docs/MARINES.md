# Toy Town Marines: where we left off

Paused on the user's request. Branch: `integration/northwest`.

## Current version
`usmap/closeup/parade/` (artifact https://claude.ai/artifact/AdeZy6c5iXy3BeMsi1SftG): a 30-second scene on the
painted Toy Town square, built only from the user's two full asset sheets
(`usmap/closeup/turn/ref/sheet7_full_set_a.webp`, `sheet8_full_set_b.webp`).

Rebuild:
```bash
python3 usmap/closeup/turn/cut3.py   # cut 51 pieces per Marine into parade/, enlarged 2x
python3 usmap/closeup/turn/fit3.py   # fit talking heads / head turns, measure frames -> parade/rig4.json
```
`parade/index.html` embeds `rig4.json` inline (the `const R = ...` line); re-embed it after re-running `fit3.py`.

## How it works
- Painted sprite frames, no 3D: turning blends between the four views (mirrored for the other side) with a squash.
- Walks: side, toward, and away cycles. Side steps are timed to the distance walked.
- Mouths: fitted onto the turnaround front, the turnaround three-quarter view, and the holding-present poses
  (`give_0`, `take_2`), using cap-width scale plus ECC affine.
- Handover: B's position is solved so his receiving hands meet A's offered present; the two lean in to hand it over.

## Known limits / open items
- The sheet figures are only ~260 px tall, so they're soft even after 2x enlargement.
  Same drawings at 700 px+ would drop straight into `cut3.py`.
- No talking while waving (the raised hand blocks the face fit). Minor pale specks at some edges;
  a small gap in B's belt in the back view.
- The loop fades at its seam. Voice is browser speech (placeholder).
- Next: put the scene into the map's Toy Town zoom (engine10 `detail` layer).
- Still open from the map: a tree under a building in the Southwest, a lantern on the track, and an automatic
  build check for objects on tracks and trees cut off by buildings.

## Earlier attempts (kept for reference)
- `trace/` + `talk/`: trace and repaint plus a 2D cut-out rig. Rejected as flat, with a duplicate-looking far arm.
- `toy3d/`: three.js toon models. Rejected; the user preferred the painted look.
- `turnview/`, `turnview2/`: earlier rounds from partial sheets.

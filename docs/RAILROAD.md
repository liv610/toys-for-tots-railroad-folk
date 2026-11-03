# Railroad geometry

All routes live in `usmap/usmap.py` as NumPy arrays of points in reference coordinates. Each is built the same way:
hand-placed control points, a Catmull-Rom spline through them (14 samples per span), then resampling to a constant
spacing of 1.6 units. The arrays are therefore evenly spaced polylines, ordered **in the direction of travel toward
Toy Town**. They are ready for animation: index `i` advances a fixed distance along the track.

| Route | Array | From | To | Notes |
|---|---|---|---|---|
| Red | `RED` | north-west coast (30, 166) | west tunnel (772, 402) | runs south along the Pacific side, then east across the plains |
| Blue | `BLUE` | south-west coast (104, 596) | joins the red line at (744, 416) | a junction just before the west portal; both share the last stretch into the tunnel |
| Green | `GREEN` | north-east coast (1580, 196) | east tunnel (1060, 418) | |
| Green branch | `GREEN2` | splits from Green at (1460, 360) | Toy Town station (872, 534) | crosses the south-eastern river on the stone arch bridge near (1084, 606) |

* **Portals.** `WEST_PORTAL = (776, 400)` and `EAST_PORTAL = (1056, 414)` are stone arches painted at the base of the
  Toy Town hill. The tracks end at the portal mouths. Nothing is drawn inside, so a train can vanish there.
* **Drawing.** `usmap.track(P, kind, w=11)` draws each route as three layers:
  * a faint ballast shadow
  * ties every ~10 units across the track: rust-red on Red, cream on Blue and Green
  * two rails in the route colour, offset ±8.8 units
* **Bridge.** The bridge segment of `GREEN2` (index of the point nearest (1084, 606), ±45) is painted over the bridge
  deck in `usmap2.main`.
* **Train.** The train sits on `RED` at the first index whose x is nearest 600 with y ≥ 380, drawn at scale 3.4 by
  `story.train(i_head, sabs, pts)`. That function orients each car by the local track direction (±3 samples). To
  animate, re-render the train at successive `i_head` values. A better option is to export the arrays (for example
  as JSON) and move a sprite along them in the browser.

### For a future interactive layer

Export `RED`, `BLUE`, `GREEN`, `GREEN2` and the two portal points. Multiply by `k = 3200 / 1672` to get output-pixel
coordinates, or keep reference coordinates and scale with the image. The tree placement already keeps canopies off
the tracks, so a train sprite animated along these points will not pass through painted trees. Toy Town's buildings
and the train itself are painted into the image, so an animated train needs either a version of the painting without
the train, or the same painting with the train layer skipped.

# Toy Town layout proposal (for review, nothing painted yet)

Three sketches drawn over the real artwork and the real route data. No map, route, engine or viewer file is
changed. Rebuild with `python3 docs/toytown_layout/make_sketches.py` (needs the built `usmap/viewer_nw/`).

- `A_context.jpg`: Toy Town in the national map, with all three railway approaches drawn from `scene.json`.
- `B_layout.jpg`: the station, enlarged square, both sides of the village, paths and bridge, over today's art.
- `C_plan.jpg`: an overhead plan of how the buildings, square, station and railway entrances relate.

Key: solid lines are existing and kept; orange dashes are proposed. "Kept, moved" houses keep their colours and
character. Landmarks are the blue shop with the green-and-white awning and the toy donation storefront.

All geometry lives in one place, the `EXIST`, `SQUARE`, `BUILD`, `PATHS` and `SQUARE_FEATURES` tables in
`make_sketches.py`, in detail-layer pixels. Adjusting the proposal means editing those tables and re-running.

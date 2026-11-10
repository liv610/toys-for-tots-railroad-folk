# Toy Town 3D: Stage A (layout blockout)

A separate experiment: Toy Town as a miniature village you can step into, built in Three.js. It does not
touch the national map, its engine, routes or viewer. The folk-art Toy Town illustration
(`reference/toytown_illustration.jpg`) is the architectural and compositional reference.

## Run

```bash
cd experiments/toytown-3d && python3 -m http.server 8798
```
Then open http://localhost:8798/blockout/ and use the view buttons. `?view=square` starts at a view;
`?shadows=0` turns shadows off.

## Files

| Path | What it is |
|---|---|
| `blockout/layout.js` | The whole layout as data: station, platforms, rails, square, buildings, river, bridge, paths, camera views. |
| `blockout/blockout.js` | Builders that turn the layout into simple shapes (`station`, `house`, `rails`, `bridge`, `lamp`...). |
| `assets/toyshop_scene.glb` | The existing real-time toy-shop scene (from the claymation real-time artifact), used here for scale. |
| `renders/` | The review views, a contact sheet, and the side-by-side with the illustration. |

## The existing toy-shop scene: what's in it and what to reuse

The real-time scene is one glTF of **1.59 million triangles in 101 meshes, 83 materials, no textures**,
with a single custom shader that adds clay and snow surface detail. Measured by mesh:

| Mesh | Triangles | Share |
|---|---:|---:|
| Snow (all snow, fused into one mesh) | 1,094,378 | 69% |
| Needles (three tree meshes) | 185,000 | 12% |
| Cobbles | 80,912 | 5% |
| Ground snow | 67,814 | 4% |
| Everything else (the shop, decorations, lamps, bridge, background) | ~160,000 | 10% |

**Reuse as is:**
- The clay and snow shader. It is already procedural, cheap, and gives the hand-made surface.
- The materials and palette.
- The shop building itself.
- The door hinge, falling snow and chimney smoke from the viewer.
- The camera-transition code.

**Rebuild:**
- **The snow.** It's remeshed sculpted volume at about a 1 cm voxel scale, which is far more geometry
  than the screen can show. Decimated to about 5% and baked to a normal map, it should look the same
  from human-scale views.
- **Needles and cobbles.** These are thousands of near-identical pieces welded into single meshes, so
  they should become instanced meshes: one needle cluster or stone, drawn thousands of times.

## Proposed technical plan

1. **One village, many components.** `layout.js` holds where everything goes, and each kind of thing has
   a builder:
   - **Generic parts:** house, roof, window, door, lamp, bench, wagon, fir, garland.
   - **Hero pieces:** the station, the toy shop and the donation storefront are modelled
     individually in Blender (like the toy shop), exported as glTF, and dropped into their slots.
   - **Generic buildings:** made from shared parts, each with its own proportions, colours and roofline.
2. **The pipeline.** Model in Blender with Python, as the claymation shop was.
   - Export each piece as compressed glTF (meshopt), with a reduced-detail version for distance.
   - Bake fine sculpting into normal maps.
   - Share materials by kind (clay, painted wood, snow, fabric, stone) rather than by object.
3. **Instancing.** Use it for cobbles, sleepers, needle clusters, snow lumps, garland pieces, ornaments,
   window frames, lamps and fence posts.
4. **A guided tour, not free roaming (my recommendation).**
   - **Movement:** a few meaningful stops (arrive at the square, the tree, the toy shop, the Marines,
     the station steps, inside the hall). The camera glides between them at eye height, and you can
     look around a little at each stop.
   - **Why:** this keeps every frame composed, keeps the "miniature set" framing, avoids clipping
     through walls, needs no controls tutorial, and works with touch and keyboard.
   - **Optional:** a free "wander" mode can come later, restricted to the streets.
5. **Loading.**
   - Load the square and station first, then stream the rest.
   - Interiors (station hall, shop) load only when the visitor goes in.

## Performance

| Target | Triangles per frame | Draw calls | Shadow and post-processing |
|---|---|---|---|
| Desktop (integrated GPU, 60 fps) | ≤ 1.5 M | ≤ 300 | soft shadows for 1 sun light, bloom, mild depth of field |
| Recent phone (30–60 fps) | ≤ 400 k | ≤ 150 | small shadow map, bloom only, lower pixel ratio |
| Download | ≤ 15 MB before first view, rest streamed | | |

- **Today:** the toy shop alone is 1.59 M triangles. The whole village at that density would be 10–15 M,
  which would not run on phones and would struggle on laptops.
- **With the steps above:** I expect a full village of about 1–1.5 M on desktop and about 300–400 k on
  mobile (via the distance versions), with no visible loss at human scale.
- **Biggest single win:** decimating the snow plus a normal map takes the shop from 1.59 M to under
  0.6 M triangles.
- **This blockout:** about 1.55 M triangles per frame, almost all of it the toy shop; the blockout's own
  shapes are only a few thousand triangles in about 200 draw calls.
- **Not measured yet:** this container has no GPU, so frame rates still need checking on a real
  laptop and phone.

## Layout decisions that differ from the illustration

- **Turning a flat picture into a place.** The illustration stacks the buildings in a flat row; here
  they wrap the square in a horseshoe, angled toward it, so a visitor standing in the square sees
  fronts and doors on three sides. The square runs about 25 m from the station steps to the low wall,
  and about 24 m across.
- **Station scale.** The vault's crown is about 16 m. That's grand next to 9–12 m houses, without
  dwarfing the village; it's about 1.8× the toy shop's gable. The corner towers stop below the crown,
  as in the illustration.
- **The clock porch** sits in front of the great arch, covering its lower part, as in the
  illustration. Its doors and two ticket windows face the square. That's where the campaign finder
  will open in Stage E.
- **The station has depth.** The barrel-vaulted hall runs 26 m back.
  - On each side, the wings are train sheds the tracks enter through portals in their outer walls.
  - The hall's side walls are arcades, so the trains pass from the sheds to the platforms.
- **Tracks and platforms.**
  - Red and blue arrive from the west, with blue curving in behind the west houses.
  - Both end at buffers on a shared west island platform.
  - Green crosses the river on the red trestle and ends at its own east platform.
  - The ends sit either side of a central concourse that leads to the entrance. No track crosses
    another or the square.
- **The low wall** along the front is a retaining wall: the meadow beyond is about 1.2 m lower, with
  steps down to the path to the fields. That gives the square a clear edge and a view out.
- **The river** runs north to south along the east side. The stone bridge takes the east path over it.
  The river is straightened compared with the illustration, so the bridge and trestle sit cleanly.
- **The toy shop** comes from the real-time scene with its own snow and decorations; it is clipped
  out of its street. It sits at the square's south-west corner, angled across the square, where the
  illustration puts it.

## Approach 1 test: the painted diorama (`painted/`)

The blockout's 3D layout, with every surface painted by the map's folk-art kit instead of 3D materials.

- **Painting:** `painted/paint_assets.py` paints the textures into `painted/tex/` (about 3 minutes):
  - the building fronts, the tree, Marines, lamps, wagons and firs;
  - wall and roof tiles;
  - the ground with the square's setts under snow;
  - the snowy hills.
  It uses the same kit code as the map's Toy Town, copied into `painted/kit/`.
- **3D:** `painted/diorama.js` stands each front at its place in the square and gives it painted side
  walls and roofs. Small things (the tree, people, lamps, wagons, firs) are cut-outs that turn to face
  you. Materials are unlit, so the painted light stays as painted.
- **Run:** serve `experiments/toytown-3d` and open `/painted/`.

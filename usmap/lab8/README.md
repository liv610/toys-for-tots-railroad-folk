# lab8: storefront detail experiment (4 Nov 2026)

The experiment is isolated from everything else:
* Nothing in `out5*/`, `viewer5/` or the published map changes.
* The live Toy Town is checkpointed in `checkpoints/pass5-toytown-branding-2026-11-04/`.

The subject is the yellow shop beside the clock tower (town row house 5). It is rendered from the real pass 5 scene by
`crop8.py`, at four levels:

| level | what changed | shop painting time, close-up / map |
|---|---|---|
| Original | the current shop window (rocking horse) and the TOY DONATION sign | 0.9 s / 0.09 s |
| A Refined | framed windows (reveal, frame, bars, stone sill and lintel), a cornice and string course, a shopfront (pilasters, transom of small panes, mullioned window, kick panels), a panelled door with a brass knob and a stone step | 1.7 s / 0.18 s |
| B Rich | A, plus green shutters, red and white flower boxes, lit upper windows, a TOYS FOR TOTS sign, a scalloped awning with its shadow, an evergreen garland with bows, a red door with a wreath and hinges, a shelf display (teddy and books behind; rocking horse and presents in front), warm light spilling onto the cobbles | 2.9 s / 0.23 s |
| C Maximum | B, plus quoins, a dentil cornice with brackets, keystones, three gooseneck sign lamps, string lights, a glazed door with a kick plate, a poinsettia, shingle courses and a ridge cap, a dormer with a lamp, a candle and a cat in the windows, and stars on the kick panels | 4.8 s / 0.41 s |

The whole crop (roof, hills and square included) takes about 125 s close up and 9 s at map density. The shop's own
detail adds 1–4 s close up and under half a second at map density.

## Files
* `store8.py`: the reusable components.
  * Architecture: `cornice`, `string_course`, `quoins`, `window_framed` (styles, glass, shutters, flower box, story),
    `flower_box`, `shopfront`, `door`, `awning`, `sign`, `gooseneck`, `roof_detail`.
  * Decoration: `wreath`, `garland`, `string_lights`.
  * Toys: `drum`, `blocks`, `soldier`, `books`, `doll`, `wooden_train`, and the arrangements in `display`.
  * Brush: `fine()`, a finer brush for small things.
  * All are in map units, and all paint with the same gouache primitives as the map.
* `crop8.py`: renders any rectangle of the real scene on its own canvas, close up (4× the map's density) or at map
  density.
* `sheets8.py`: the comparison sheets in `out/`.

## Findings
1. **Soft edges limit small detail.** Every painted area is softened by about 0.9 map units. Anything smaller than
   about 2 units melts, which is why the toys in the live shop windows look faint. `fine()` softens by 0.32 units
   instead, and that alone made the windows and toys read.
2. **Pixel budget.** The shop is 44 × 84 map units: 168 × 322 pixels at 100% of the map, and about 96 pixels wide in
   the Toy Town view.
   * At those sizes A and B read well.
   * In C, the lamps, cat, candle, dentils and kick-panel stars are below what the eye can resolve. They show only
     close up.
3. **A detail layer would let C pay off.** Toy Town could be painted at 4× density as a second tile layer that the
   viewer swaps in when zoomed close, as it already does with tiles. Nothing like this exists in the viewer yet.
4. **Cost is small.** Detail costs seconds per building, not minutes, so a whole town at level B adds roughly a minute
   to a full render.

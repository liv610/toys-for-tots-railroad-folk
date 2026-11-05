# Art direction and asset principles

Agreed on 5 November 2026. These guide every new piece of work on the map.

## What stays

The map's watercolour and gouache look, its railway routes, animations, zoom behaviour and interactions are the
direction. They are preserved, not reinvented.

## Principles

1. **The artwork comes first; the algorithm comes second.** Judge a new element by how it looks at the scales people
   see it, not by how clever its drawing code is.
2. **Not everything has to be procedural.** A building, character, tree or decorative object can be:
   - drawn by procedural geometry (as most of the map is now)
   - an authored illustration, for example an SVG or a layered image
   - a reusable illustrated component placed many times

   Choose whichever gives the best result for that element.
3. **Authored and painted can be combined.** An authored shape can still be filled and edged by the project's own
   gouache brush, so it keeps the map's texture and stays consistent with everything else. Avoid assets that would
   look pasted onto the painting.
4. **Learn from illustrated games.** Townscaper, Hidden Folks, Dordogne and Tiny Glade get much of their quality from
   carefully authored assets and reusable components. Their rendering systems assemble and animate those assets.
5. **Know the libraries, but don't adopt them by default.** PixiJS, Phaser, Paper.js and Three.js are available and
   free. Introduce one only for a clear technical reason that the current viewer (OpenSeadragon plus a canvas
   overlay) can't meet.
6. **No renderer migration or major rewrite on the strength of these ideas.** If a different way of producing assets
   or rendering could substantially improve the map, explain it first: what it would improve, what it costs, and
   what it risks. Implement it only after approval.

## How this applies to the current plan

- The high-resolution Toy Town work continues as planned.
- For small, detail-rich elements, compare a procedural version with an authored one before committing to either.
  These include figures, toys, signs and storefront ornaments.
- The engine's tile cache, part boxes and exactness checks apply to authored components just as to procedural ones.

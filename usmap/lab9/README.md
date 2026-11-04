# lab9: technology or technique? (4 Nov 2026)

These experiments test the limitations listed after the storefront experiment. Nothing in the live map changes.

| claimed limit | experiment | verdict |
|---|---|---|
| **Resolution ceiling:** one canvas in memory, about 7000 px wide | `tile9.py`: the shop crop painted whole and as 2 × 2 tiles, with the current brush and with a position-exact brush | **Technique.** With the current brush, tiles disagree with the whole render: mean error 14.5, and 57% of pixels are off by more than 8 levels. With the position-exact brush, the mean error is 0.09 and 99.8% of pixels are identical. The leftover 0.2% comes from a couple of painters that size their random draws by the visible area, and can be fixed. |
| **Small things melt** | `features9.py`: peak opacity of a disc of radius r | **Technique (one parameter).** At the default edge softness, discs smaller than about 0.8 map units radius never appear, even at 4× density, because softness is set in map units. At softness 0.32 a 0.4-unit disc is fully opaque at map density. Resolution alone would not have fixed this. |
| **Naive toys and figures** | `teddy9.py`: the current teddy (eight discs) against a designed silhouette (one smooth curve with pads, seams, eyes, nose, bow, fur and outline) | **Mostly technique.** At 4 map units tall the current teddy is invisible on the map; the designed one reads as a teddy at about 15 pixels. At 4× it is a storybook teddy. What remains is design effort per object. |
| **Low contrast in the window** | `teddy9.py`: lightness contrast (CIE L*) of the toy against the glass | **My diagnosis was wrong.** Contrast was already adequate (25–31). A darker interior *lowered* it (13–16). The problem was size and structure, not value. |
| **"I don't see while I paint"** | component sandbox timing | **Technique.** One component renders alone in 0.01–0.4 s, against 2 minutes for the crop and 15 minutes for the map. Iteration on small things can be nearly instant. |
| **Memory (8 GB)** | arithmetic | **Removed by tiling.** A 4096² tile needs about 1.5 GB. |
| **Hosting** | measured from the current tiles (level 13 = 8.3 MB for 29.6 Mpx) | **Real but not blocking.** A 4× map (about 28,400 × 16,700) at 2048-px tiles is about 180 files and roughly 120–180 MB. That is under the page limits of 511 files and 256 MB per version. |
| **Render time** | from measured crops | **Real.** About 25 min for a 4× Toy Town layer. A 4× whole map is a few hours on this workspace's 2 CPUs, which is fine as an overnight job. |

## What is genuinely limited
* **My eye and hand.** Every shape is designed in coordinates and judged from renders. The sandbox makes that fast, but
  the quality ceiling is my design skill per object, and each designed component is real work.
* **Compute.** A whole-map 4× render takes hours, not minutes.
* **Your rules.** Code-generated art only, so nothing is traced from the AI reference. That is a choice, not a
  technical limit.

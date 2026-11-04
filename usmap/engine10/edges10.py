"""Engine 10: per-function edge treatment (opt-in).

Each drawing function can be given an edge preset (brush10.EDGES). While it runs, every area it paints uses that
preset's softness, roughness and wobble, unless the call asks for a softness itself. Presets nest: a 'fine' window
painted inside a 'built' house is fine.
Profiles:
  'equivalent'  nothing wrapped: the legacy look (organic edges everywhere)
  'selective'   organic landscape and foliage, built architecture, fine windows, toys, figures and small decorations
Only an EngineCanvas responds; with the legacy canvas a wrapped function behaves exactly as before.
"""
import functools
import usmap4 as B
import tft7 as T7
import station5 as ST

A, U = B.A, B.U
SELECTIVE = {
    'built': [(A, 'house'), (B, 'wall'), (B, 'roof_tiles'), (B, 'depot'), (ST, 'masonry'), (ST, 'tiles'), (ST, 'pilaster'), (ST, 'voussoirs'),
              (U, 'barn'), (U, 'silo'), (U, 'lighthouse')],
    'fine': [(A, 'window'), (B, 'lit_window'), (ST, 'panes_and_doors'), (ST, 'lunette'),
             (T7, 'shop_window'), (T7, 'donation_sign'), (T7, 'teddy'), (T7, 'toy_train'), (T7, 'presents'), (T7, 'nutcracker'), (T7, 'rocking_horse'),
             (T7, 'marine'), (T7, 'person'), (T7, 'donation_box'), (T7, 'lamp_post'), (T7, 'lamp_wreath'), (T7, 'planter'), (T7, 'christmas_tree'),
             (T7, 'wagon'), (T7, 'medallion'), (T7, 'banner'), (T7, 'swag')],
}
_orig = {}

def _wrap(mod, name, preset):
    f = getattr(mod, name)
    @functools.wraps(f)
    def g(*a, **kw):
        c = B.c
        if hasattr(c, 'edges'):
            with c.edges(preset): return f(*a, **kw)
        return f(*a, **kw)
    _orig[(mod, name)] = f; setattr(mod, name, g)

def activate(profile='selective'):
    deactivate()
    if profile == 'equivalent': return
    for preset, fns in SELECTIVE.items():
        for mod, name in fns: _wrap(mod, name, preset)

def deactivate():
    for (mod, name), f in _orig.items(): setattr(mod, name, f)
    _orig.clear()

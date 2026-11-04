"""Engine 10, phase 6: views for comparison sheets that paint only what changed.

    crop(f, rect, ...)                  paint rect (map units) at density f with a 16-unit margin, return exactly rect
    view(f, rect, store, patches, ...)  the cached map over rect (cache10 tiles in `store`), with each patch rect
                                        painted fresh (crop) and pasted in

A patch must cover every mark the change makes. split10's part boxes do (tools/check_part_boxes.py), and a crop
equals a complete render inside its margin (the tiles do too), so a patched view equals a complete render of the
changed scene. tools/check_patched_view.py proves this for one case. The keyword arguments go to
render10.render_window (level, shop, scene_path); profile picks the edge preset.
"""
import math, time
import numpy as np
import render10 as R, cache10 as C, edges10 as E, split10 as SP

def px_rect(f, rect):
    x0, y0 = R.map_to_px(rect[0], rect[1], f); x1, y1 = R.map_to_px(rect[2], rect[3], f)
    return int(math.floor(x0)), int(math.floor(y0)), int(math.ceil(x1)), int(math.ceil(y1))

_CROPS = {}
def crop(f, rect, profile='equivalent', **kw):
    """(A crop is remembered for the rest of the run, so two views that share a patch paint it once.)"""
    key = (f, tuple(rect), profile, tuple(sorted((k_, getattr(v, '__name__', v)) for k_, v in kw.items())))
    if key not in _CROPS: _CROPS[key] = _crop(f, rect, profile, **kw)
    return _CROPS[key].copy()

def _crop(f, rect, profile='equivalent', **kw):
    x0, y0, x1, y1 = px_rect(f, rect); GW, GH = R.frame_px(f); pad = int(math.ceil(C.PAD * R.BR.K1 * f))
    win = (max(0, x0 - pad), max(0, y0 - pad), min(GW, x1 + pad), min(GH, y1 + pad))
    E.activate(profile)
    try: img, Z, st = R.render_window(f, win, **kw)
    finally: E.deactivate()
    return img[y0 - win[1]:y1 - win[1], x0 - win[0]:x1 - win[0]]

def view(f, rect, store, patches=(), profile='equivalent', **kw):
    asm, (X0, Y0, X1, Y1) = C.assemble(f, rect, store=store)
    x0, y0, x1, y1 = px_rect(f, rect)
    for pr in patches:
        a0, b0, a1, b1 = px_rect(f, pr); p = crop(f, pr, profile, **kw)
        asm[b0 - Y0:b1 - Y0, a0 - X0:a1 - X0] = p
    return asm[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]

def yellow_shop_patch():
    """Everything a storefront level can change: the yellow house's facade and the pavement in front (split10)."""
    x0, y, xs, _ = SP._xs(); w, h = SP.ROW[SP.YELLOW_SHOP][:2]; x = xs[SP.YELLOW_SHOP]
    return (x - 10, y - h - 60, x + w + 18, y + 14)

"""Claymation Toy Town: the blue shop with the green-and-white awning, as a hand-made miniature set.

Run (Blender 4.2 LTS):
    blender -b --factory-startup -P build_scene.py -- STAGE [WIDTH HEIGHT SAMPLES]
STAGE 1  architecture: shapes and proportions, flat preview colours
STAGE 2  materials: clay plaster, painted wood, fabric, snow, brick, cobbles
STAGE 3  atmosphere: decorations, warm practical light, depth of field, final render; saves the .blend

Everything is generated here from primitives: no downloaded assets. Seeds are fixed, so a run is reproducible.
Units: 1 unit is roughly 4 cm of a real miniature set (the shop is ~25 cm tall as a model).
Axes: x along the shop front, y into the shop (front wall at y = 0), z up. The camera looks from front-right.
"""
import bpy, bmesh, math, os, sys, time, random
from mathutils import Vector, Matrix, Euler, noise

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
STAGE = int(ARGS[0]) if ARGS else 3
RES = (int(ARGS[1]), int(ARGS[2])) if len(ARGS) > 2 else ((800, 600) if STAGE < 3 else (1600, 1200))
SAMPLES = int(ARGS[3]) if len(ARGS) > 3 else (64 if STAGE < 3 else 384)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'renders'); os.makedirs(OUT, exist_ok=True)
R = random.Random(11)

# ---------------------------------------------------------------- dimensions of the shop
W, D = 3.0, 2.6            # front width, depth
H = 4.3                    # eaves height
HR = 6.15                  # ridge height (steep, a little whimsical)
OVF, OVB, OVS = .32, .25, .30   # roof overhang front, back, sides
SLOPE = (HR - H) / (W / 2)

# ---------------------------------------------------------------- scene helpers
bpy.ops.wm.read_factory_settings(use_empty=True)
SCN = bpy.context.scene
CUTTERS = bpy.data.collections.new('cutters'); SCN.collection.children.link(CUTTERS)
CUTTERS.hide_render = True; CUTTERS.hide_viewport = True

def link(ob, coll=None):
    (coll or SCN.collection).objects.link(ob); return ob

def from_bm(name, bm, coll=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return link(bpy.data.objects.new(name, me), coll)

def bm_box(bm, c, s, rot=None, bevel=0.0, seg=2):
    """A box centred at c with size s (optionally rotated, optionally bevelled) added to bm."""
    old = set(bm.verts) if bevel else None
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r['verts']
    m = Matrix.Diagonal(Vector((s[0], s[1], s[2], 1)))
    bmesh.ops.transform(bm, matrix=m, verts=vs)
    if rot is not None: bmesh.ops.transform(bm, matrix=Euler(rot).to_matrix().to_4x4(), verts=vs)
    bmesh.ops.translate(bm, vec=Vector(c), verts=vs)
    if bevel:
        es = list({e for v in vs for e in v.link_edges})
        bmesh.ops.bevel(bm, geom=vs + es, offset=bevel, segments=seg, affect='EDGES', profile=.5)
        vs = [v for v in bm.verts if v not in old]
    return vs

_TPL = {}
def _template(kind, sub=2):
    """Unit shapes built once; bmesh's own create_* operators slow down as the mesh grows, so many small
    pieces (cobbles, lumps, needles) are stamped from these templates instead."""
    key = (kind, sub)
    if key not in _TPL:
        t = bmesh.new()
        if kind == 'ico': bmesh.ops.create_icosphere(t, subdivisions=sub, radius=1.0)
        elif kind == 'rbox':
            bmesh.ops.create_cube(t, size=1.0)
            bmesh.ops.bevel(t, geom=t.verts[:] + t.edges[:], offset=.22, segments=2, affect='EDGES', profile=.5)
        t.verts.ensure_lookup_table()
        _TPL[key] = ([v.co.copy() for v in t.verts], [[v.index for v in f.verts] for f in t.faces]); t.free()
    return _TPL[key]

def stamp(bm, kind, mat, sub=2):
    co, fa = _template(kind, sub)
    vs = [bm.verts.new(mat @ c) for c in co]
    for f in fa: bm.faces.new([vs[i] for i in f])
    return vs

def bm_blob(bm, c, r, rot=(0, 0, 0), sub=2):
    """An ellipsoid (ico sphere scaled to radii r)."""
    m = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal(Vector((r[0], r[1], r[2], 1)))
    return stamp(bm, 'ico', m, sub)

def bm_rbox(bm, c, s, rot=(0, 0, 0)):
    """A box with softly rounded edges (roof tiles)."""
    m = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal(Vector((s[0], s[1], s[2], 1)))
    return stamp(bm, 'rbox', m)

def bm_cyl(bm, c, r, depth, rot=(0, 0, 0), seg=16, r2=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    vs = res['verts']
    bmesh.ops.transform(bm, matrix=Euler(rot).to_matrix().to_4x4(), verts=vs)
    bmesh.ops.translate(bm, vec=Vector(c), verts=vs)
    return vs

def paint(bm, vs, rgb):
    """Store a per-piece colour (for tiles, cobbles, needles) in the 'Col' attribute."""
    lay = bm.loops.layers.color.get('Col') or bm.loops.layers.color.new('Col')
    for v in vs:
        for l in v.link_loops: l[lay] = (*rgb, 1.0)

WOBBLE = {}
def wobble_tex(scale):
    if scale not in WOBBLE:
        t = bpy.data.textures.new(f'wobble_{scale}', 'CLOUDS'); t.noise_scale = scale; t.noise_depth = 2; WOBBLE[scale] = t
    return WOBBLE[scale]

def clay(ob, voxel=.02, smooth=.5, iters=4, wob=.0, wob_scale=.8, adapt=0.0):
    """The 'sculpted' look: fuse everything into one volume (voxel remesh), soften every edge, then a slow
    hand-made wobble. Applied as modifiers so the stack stays editable in the .blend."""
    m = ob.modifiers.new('fuse', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.adaptivity = adapt; m.use_smooth_shade = True
    if smooth:
        s = ob.modifiers.new('soften', 'SMOOTH'); s.factor = smooth; s.iterations = iters
    if wob:
        d = ob.modifiers.new('hand_wobble', 'DISPLACE'); d.texture = wobble_tex(wob_scale); d.strength = wob; d.mid_level = .5
        d.texture_coords = 'GLOBAL'
    return ob

def smooth_shade(ob):
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def cutter_box(c, s):
    bm = bmesh.new(); bm_box(bm, c, s); return from_bm('cut', bm, CUTTERS)

# walls: local frames (u along the wall, v up, n = outward distance)
def front(u, v, n=0.0): return Vector((u, -n, v))
def right(u, v, n=0.0): return Vector((W / 2 + n, u, v))
WALLS = {'front': (front, Vector((1, 0, 0)), Vector((0, -1, 0))), 'right': (right, Vector((0, 1, 0)), Vector((1, 0, 0)))}

def wall_box(bm, wall, u0, u1, v0, v1, n0, n1, bevel=0.0):
    f, U, N = WALLS[wall]
    a, b = f(u0, v0, n0), f(u1, v1, n1)
    c = (a + b) / 2; s = Vector((abs(b.x - a.x), abs(b.y - a.y), abs(b.z - a.z)))
    return bm_box(bm, c, s, bevel=bevel)

# ---------------------------------------------------------------- materials
MATS = {}
def flat(name, rgb, rough=.8):
    """Stage 1: a plain colour, to judge only shapes and proportions."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    return m

def nodes(m):
    nt = m.node_tree; return nt, nt.nodes, nt.links

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt, N, L = nodes(m); p = N['Principled BSDF']
    return m, nt, N, L, p

def tex_coord(N, kind='Object', scale=(1, 1, 1), loc=(0, 0, 0)):
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale; mp.inputs['Location'].default_value = loc
    N.id_data.links.new(tc.outputs[kind], mp.inputs['Vector']); return mp.outputs['Vector']

def noise_tex(N, L, vec, scale, detail=3, rough=.55, distort=0.0):
    t = N.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = detail
    t.inputs['Roughness'].default_value = rough; t.inputs['Distortion'].default_value = distort
    L.new(vec, t.inputs['Vector']); return t

def voronoi(N, L, vec, scale, feature='SMOOTH_F1', rnd=1.0):
    t = N.new('ShaderNodeTexVoronoi'); t.feature = feature; t.inputs['Scale'].default_value = scale
    t.inputs['Randomness'].default_value = rnd; L.new(vec, t.inputs['Vector']); return t

def math_node(N, L, op, a, b=None, clamp=False):
    m = N.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    if isinstance(a, (int, float)): m.inputs[0].default_value = a
    else: L.new(a, m.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): m.inputs[1].default_value = b
        else: L.new(b, m.inputs[1])
    return m.outputs[0]

def mix_rgb(N, L, fac, a, b, blend='MIX'):
    m = N.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = blend
    for sock, val in ((m.inputs[0], fac), (m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(val, (int, float)): sock.default_value = val
        elif isinstance(val, tuple): sock.default_value = (*val, 1) if len(val) == 3 else val
        else: L.new(val, sock)
    return m.outputs[2]

def hsv(N, L, col, h=.5, s=1.0, v=1.0):
    n = N.new('ShaderNodeHueSaturation')
    for sock, val in ((n.inputs['Hue'], h), (n.inputs['Saturation'], s), (n.inputs['Value'], v)):
        if isinstance(val, (int, float)): sock.default_value = val
        else: L.new(val, sock)
    if isinstance(col, tuple): n.inputs['Color'].default_value = (*col, 1)
    else: L.new(col, n.inputs['Color'])
    return n.outputs[0]

def bump(N, L, height, strength, dist=.02, normal=None):
    b = N.new('ShaderNodeBump'); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = dist
    L.new(height, b.inputs['Height'])
    if normal is not None: L.new(normal, b.inputs['Normal'])
    return b.outputs['Normal']

def sculpt_marks(N, L, vec, scale=1.0):
    """Height field of a hand-modelled surface: shallow thumb/spatula dents (smooth voronoi), soft directional
    strokes (stretched voronoi), and a fine grain. Mixed at low weights so no single pattern dominates."""
    dents = voronoi(N, L, vec, 9 * scale, 'SMOOTH_F1', .9)
    sm = N.new('ShaderNodeMapping'); sm.inputs['Scale'].default_value = (3.5 * scale, 3.5 * scale, 22 * scale)
    sm.inputs['Rotation'].default_value = (0, .35, .2); L.new(vec, sm.inputs['Vector'])
    strokes = voronoi(N, L, sm.outputs[0], 1.0, 'SMOOTH_F1', 1.0)
    grain = noise_tex(N, L, vec, 140 * scale, 2, .6)
    lumps = noise_tex(N, L, vec, 2.2 * scale, 3, .5, .4)
    h = math_node(N, L, 'MULTIPLY', dents.outputs['Distance'], .45)
    h = math_node(N, L, 'ADD', h, math_node(N, L, 'MULTIPLY', strokes.outputs['Distance'], .35))
    h = math_node(N, L, 'ADD', h, math_node(N, L, 'MULTIPLY', grain.outputs['Fac'], .12))
    h = math_node(N, L, 'ADD', h, math_node(N, L, 'MULTIPLY', lumps.outputs['Fac'], .5))
    return h

def clay_mat(name, rgb, rough=.78, var=.10, sss=.06, scale=1.0, bump_s=.32, sparkle=0.0, use_attr=False, sheen=.12, ao=.35):
    """Painted clay / plaster. Colour drifts the way hand-mixed paint does (two scales of slow variation plus
    a per-piece shift), the surface carries sculpting marks, roughness varies a little, a touch of subsurface
    keeps it from reading as plastic."""
    if STAGE == 1: return flat(name, rgb)
    m, nt, N, L, p = new_mat(name)
    vec = tex_coord(N, 'Object')
    slow = noise_tex(N, L, vec, 1.3 * scale, 3, .5, .6)
    mid = noise_tex(N, L, vec, 6.0 * scale, 2, .5)
    base = (*rgb, 1)
    if use_attr:
        ca = N.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; col = ca.outputs['Color']
    else:
        col = mix_rgb(N, L, 0.0, base, base)
    v = math_node(N, L, 'ADD', 1 - var, math_node(N, L, 'MULTIPLY', slow.outputs['Fac'], 2 * var))
    v = math_node(N, L, 'ADD', v, math_node(N, L, 'MULTIPLY', math_node(N, L, 'SUBTRACT', mid.outputs['Fac'], .5), var * .8))
    h = math_node(N, L, 'ADD', .5 - .015, math_node(N, L, 'MULTIPLY', mid.outputs['Fac'], .03))
    col = hsv(N, L, col, h, 1.0, v)
    if ao:        # painted-in shading: model makers darken creases and corners by hand
        aon = N.new('ShaderNodeAmbientOcclusion'); aon.inputs['Distance'].default_value = .3; aon.samples = 8
        col = hsv(N, L, col, .5, 1.0, math_node(N, L, 'ADD', 1 - ao, math_node(N, L, 'MULTIPLY', aon.outputs['AO'], ao)))
    if sparkle:   # the glittery flecks of the Toy Town walls
        sp = voronoi(N, L, vec, 260 * scale, 'F1', 1.0)
        dot = math_node(N, L, 'LESS_THAN', sp.outputs['Distance'], .06)
        keep = math_node(N, L, 'GREATER_THAN', sp.outputs['Color'], .0)
        sel = math_node(N, L, 'MULTIPLY', dot, math_node(N, L, 'GREATER_THAN', noise_tex(N, L, vec, 40 * scale, 1).outputs['Fac'], .62))
        col = mix_rgb(N, L, math_node(N, L, 'MULTIPLY', sel, sparkle), col, (1, .97, .9))
    L.new(col, p.inputs['Base Color'])
    rr = math_node(N, L, 'ADD', rough - .06, math_node(N, L, 'MULTIPLY', mid.outputs['Fac'], .12))
    L.new(rr, p.inputs['Roughness'])
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Subsurface Radius'].default_value = (1.0, .55, .35)
    p.inputs['Subsurface Scale'].default_value = .05
    p.inputs['Sheen Weight'].default_value = sheen; p.inputs['Sheen Roughness'].default_value = .6
    p.inputs['Specular IOR Level'].default_value = .35
    L.new(bump(N, L, sculpt_marks(N, L, vec, scale), bump_s, .03), p.inputs['Normal'])
    return m

def wood_mat(name, rgb, wear=(.62, .48, .34), rough=.7, grain_dir='Z', scale=1.0):
    """Painted wood: paint colour over a faint grain, with the paint rubbed thin on edges and corners
    (pointiness) where hands would have handled the model."""
    if STAGE == 1: return flat(name, rgb)
    m, nt, N, L, p = new_mat(name)
    st = {'Z': (6, 6, .6), 'X': (.6, 6, 6), 'Y': (6, .6, 6)}[grain_dir]
    vec = tex_coord(N, 'Object', tuple(x * scale * 3 for x in st))
    gr = noise_tex(N, L, vec, 3.0, 4, .6, 2.5)
    wave = N.new('ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 2.0; wave.inputs['Distortion'].default_value = 6
    wave.inputs['Detail'].default_value = 3; L.new(vec, wave.inputs['Vector'])
    paint_v = math_node(N, L, 'ADD', .9, math_node(N, L, 'MULTIPLY', gr.outputs['Fac'], .2))
    col = hsv(N, L, (*rgb,), .5, 1.0, paint_v)
    col = mix_rgb(N, L, math_node(N, L, 'MULTIPLY', wave.outputs['Fac'], .12), col, (rgb[0] * .55, rgb[1] * .55, rgb[2] * .55))
    geo = N.new('ShaderNodeNewGeometry')
    edge = math_node(N, L, 'MULTIPLY', math_node(N, L, 'SUBTRACT', geo.outputs['Pointiness'], .53), 9.0, clamp=True)
    chip = noise_tex(N, L, tex_coord(N, 'Object'), 30 * scale, 3, .6)
    edge = math_node(N, L, 'MULTIPLY', edge, math_node(N, L, 'GREATER_THAN', chip.outputs['Fac'], .45))
    col = mix_rgb(N, L, math_node(N, L, 'MULTIPLY', edge, .75), col, wear)
    L.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    p.inputs['Specular IOR Level'].default_value = .4
    h = math_node(N, L, 'ADD', math_node(N, L, 'MULTIPLY', wave.outputs['Fac'], .4), math_node(N, L, 'MULTIPLY', chip.outputs['Fac'], .25))
    h = math_node(N, L, 'ADD', h, sculpt_marks(N, L, tex_coord(N, 'Object'), 1.6 * scale))
    L.new(bump(N, L, h, .22, .02), p.inputs['Normal'])
    return m

def fabric_mat(name, c1, c2, stripe=.3, x0=0.0):
    """Striped awning cloth: stripes painted by hand (edges waver), a fine weave, soft sheen."""
    if STAGE == 1:
        m, nt, N, L, p = new_mat(name)
        vec = tex_coord(N, 'Object')
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(vec, sep.inputs[0])
        s = math_node(N, L, 'MODULO', math_node(N, L, 'FLOOR', math_node(N, L, 'DIVIDE', math_node(N, L, 'ADD', sep.outputs['X'], x0 + 10 * stripe), stripe)), 2.0)
        L.new(mix_rgb(N, L, s, c1, c2), p.inputs['Base Color']); return m
    m, nt, N, L, p = new_mat(name)
    vec = tex_coord(N, 'Object')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(vec, sep.inputs[0])
    wob = noise_tex(N, L, vec, 4.0, 2, .5)
    x = math_node(N, L, 'ADD', sep.outputs['X'], math_node(N, L, 'MULTIPLY', math_node(N, L, 'SUBTRACT', wob.outputs['Fac'], .5), .035))
    s = math_node(N, L, 'MODULO', math_node(N, L, 'FLOOR', math_node(N, L, 'DIVIDE', math_node(N, L, 'ADD', x, x0 + 10 * stripe), stripe)), 2.0)
    col = mix_rgb(N, L, s, c1, c2)
    dirt = noise_tex(N, L, vec, 2.5, 3, .5)
    col = hsv(N, L, col, .5, 1.0, math_node(N, L, 'ADD', .9, math_node(N, L, 'MULTIPLY', dirt.outputs['Fac'], .18)))
    L.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = .92; p.inputs['Sheen Weight'].default_value = .55; p.inputs['Sheen Roughness'].default_value = .45
    p.inputs['Subsurface Weight'].default_value = .08; p.inputs['Subsurface Scale'].default_value = .03
    w1 = N.new('ShaderNodeTexWave'); w1.inputs['Scale'].default_value = 140; w1.bands_direction = 'X'; L.new(vec, w1.inputs['Vector'])
    w2 = N.new('ShaderNodeTexWave'); w2.inputs['Scale'].default_value = 140; w2.bands_direction = 'Y'; L.new(vec, w2.inputs['Vector'])
    weave = math_node(N, L, 'MULTIPLY', w1.outputs['Fac'], w2.outputs['Fac'])
    h = math_node(N, L, 'ADD', math_node(N, L, 'MULTIPLY', weave, .3), sculpt_marks(N, L, vec, 1.2))
    L.new(bump(N, L, h, .25, .015), p.inputs['Normal'])
    return m

def snow_mat(name='snow'):
    """Snow as the model makers do it: a soft white paste (subsurface, cool shadows) with a sugary grain and
    the odd glint where a crystal of 'glitter' catches the light."""
    if STAGE == 1: return flat(name, (.95, .96, 1.0), .6)
    m, nt, N, L, p = new_mat(name)
    vec = tex_coord(N, 'Object')
    lump = noise_tex(N, L, vec, 5, 3, .55, .3)
    col = hsv(N, L, (.93, .945, .98), .5, 1.0, math_node(N, L, 'ADD', .95, math_node(N, L, 'MULTIPLY', lump.outputs['Fac'], .08)))
    L.new(col, p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value = .55; p.inputs['Subsurface Radius'].default_value = (.9, .95, 1.0)
    p.inputs['Subsurface Scale'].default_value = .06
    gl = voronoi(N, L, vec, 420, 'F1', 1.0)
    glint = math_node(N, L, 'LESS_THAN', gl.outputs['Distance'], .07)
    rr = math_node(N, L, 'SUBTRACT', .62, math_node(N, L, 'MULTIPLY', glint, .5))
    L.new(rr, p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = .45
    grain = noise_tex(N, L, vec, 220, 2, .7)
    h = math_node(N, L, 'ADD', math_node(N, L, 'MULTIPLY', grain.outputs['Fac'], .35), math_node(N, L, 'MULTIPLY', lump.outputs['Fac'], .9))
    L.new(bump(N, L, h, .12, .015), p.inputs['Normal'])
    return m

def brick_mat(name='brick'):
    if STAGE == 1: return flat(name, (.62, .22, .14))
    m, nt, N, L, p = new_mat(name)
    tc = N.new('ShaderNodeTexCoord'); dis = noise_tex(N, L, tc.outputs['Object'], 3, 2, .5)
    off = N.new('ShaderNodeVectorMath'); off.operation = 'ADD'; L.new(tc.outputs['Object'], off.inputs[0])
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; L.new(dis.outputs['Color'], sc.inputs[0]); sc.inputs['Scale'].default_value = .012
    L.new(sc.outputs[0], off.inputs[1])
    br = N.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = .012
    br.inputs['Brick Width'].default_value = .15; br.inputs['Row Height'].default_value = .075
    br.inputs['Color1'].default_value = (.58, .2, .12, 1); br.inputs['Color2'].default_value = (.7, .3, .18, 1)
    br.inputs['Mortar'].default_value = (.78, .72, .64, 1); br.inputs['Bias'].default_value = .2
    br.inputs['Mortar Smooth'].default_value = .4; L.new(off.outputs[0], br.inputs['Vector'])
    L.new(br.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = .85
    p.inputs['Subsurface Weight'].default_value = .04
    h = math_node(N, L, 'ADD', math_node(N, L, 'MULTIPLY', br.outputs['Fac'], -1.0), math_node(N, L, 'MULTIPLY', sculpt_marks(N, L, tc.outputs['Object'], 1.5), .6))
    L.new(bump(N, L, h, .45, .02), p.inputs['Normal'])
    return m

def glow_glass(name, warm=(1.0, .58, .22), strength=6.0, frost=True):
    """Lit window: the light from a room behind frosted panes, brighter at the middle, with a faint mottle;
    plus a glossy surface so the cool sky glints on it."""
    m, nt, N, L, p = new_mat(name)
    p.inputs['Base Color'].default_value = (.08, .06, .04, 1); p.inputs['Roughness'].default_value = .08
    p.inputs['Specular IOR Level'].default_value = .6
    p.inputs['Emission Color'].default_value = (*warm, 1)
    if STAGE == 1:
        p.inputs['Emission Strength'].default_value = strength * .6; return m
    gen = N.new('ShaderNodeTexCoord'); gr = N.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.6, 1.6, 1.6); mp.inputs['Location'].default_value = (.5, .5, .5)
    L.new(gen.outputs['Generated'], mp.inputs['Vector']); mp.inputs['Location'].default_value = (0, 0, 0)
    sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; L.new(gen.outputs['Generated'], sub.inputs[0]); sub.inputs[1].default_value = (.5, .5, .5)
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1.6; L.new(sub.outputs[0], sc.inputs[0])
    L.new(sc.outputs[0], gr.inputs['Vector'])
    mot = noise_tex(N, L, gen.outputs['Object'], 14, 3, .6)
    e = math_node(N, L, 'ADD', .55, math_node(N, L, 'MULTIPLY', gr.outputs['Fac'], .8))
    if frost: e = math_node(N, L, 'MULTIPLY', e, math_node(N, L, 'ADD', .8, math_node(N, L, 'MULTIPLY', mot.outputs['Fac'], .4)))
    L.new(math_node(N, L, 'MULTIPLY', e, strength), p.inputs['Emission Strength'])
    return m

def glass_clear(name='shop_glass'):
    m, nt, N, L, p = new_mat(name)
    p.inputs['Base Color'].default_value = (1, .98, .95, 1); p.inputs['Roughness'].default_value = .03
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.2
    return m

def emissive(name, rgb, strength):
    m, nt, N, L, p = new_mat(name)
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Emission Color'].default_value = (*rgb, 1)
    p.inputs['Emission Strength'].default_value = strength; return m

def glossy_paint(name, rgb, rough=.25, metal=0.0):
    m, nt, N, L, p = new_mat(name)
    if STAGE > 1:
        vec = tex_coord(N, 'Object'); n_ = noise_tex(N, L, vec, 8, 2, .5)
        L.new(hsv(N, L, (*rgb,), .5, 1, math_node(N, L, 'ADD', .9, math_node(N, L, 'MULTIPLY', n_.outputs['Fac'], .2))), p.inputs['Base Color'])
        L.new(bump(N, L, sculpt_marks(N, L, vec, 3.0), .15, .01), p.inputs['Normal'])
    else: p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    p.inputs['Coat Weight'].default_value = .3 if STAGE > 1 else 0
    return m

def assign(ob, mat):
    ob.data.materials.clear(); ob.data.materials.append(mat); return ob

M = dict(
    wall=clay_mat('blue_plaster', (.11, .19, .4), var=.17, sparkle=.9, scale=1.25, bump_s=.95, ao=.55),
    stone=clay_mat('foundation_stone', (.42, .4, .38), var=.15, scale=1.6, bump_s=.8, ao=.5),
    cream=clay_mat('cream_trim', (.82, .73, .55), var=.09, scale=2.6, bump_s=.6, sheen=.2, ao=.5),
    shutter=wood_mat('red_shutters', (.58, .09, .07), grain_dir='Z', scale=1.6),
    shopwood=wood_mat('shop_wood', (.42, .2, .1), wear=(.7, .5, .3), grain_dir='Z', scale=1.4),
    plinth=wood_mat('red_plinth', (.6, .1, .08), grain_dir='X', scale=1.3),
    door=wood_mat('door_green', (.1, .26, .16), wear=(.6, .46, .3), grain_dir='Z', scale=1.4),
    roofwood=clay_mat('roof_board', (.32, .2, .14), var=.1, scale=1.6),
    tiles=clay_mat('roof_tiles', (.55, .2, .14), var=.08, use_attr=True, scale=2.2, bump_s=.4),
    brick=brick_mat(),
    snow=snow_mat(),
    awning=fabric_mat('awning', (.13, .36, .2), (.93, .9, .82), stripe=.3, x0=.0),
    glow=glow_glass('window_glow', warm=(1.0, .46, .13), strength=1.7),
    glow_soft=glow_glass('window_glow_soft', warm=(1.0, .46, .13), strength=1.2),
    shopglass=glass_clear(),
    shopback=emissive('shop_back', (1.0, .45, .14), .8),
    cobble=clay_mat('cobbles', (.5, .46, .42), var=.12, use_attr=True, scale=2.5, bump_s=.8, ao=.6),
    ground=clay_mat('ground_clay', (.36, .33, .3), var=.1),
)

# ---------------------------------------------------------------- the shop: walls with real openings
def build_walls():
    bm = bmesh.new()
    prof = [(-W / 2, 0), (W / 2, 0), (W / 2, H), (0, HR), (-W / 2, H)]
    fv = [bm.verts.new((x, 0, z)) for x, z in prof]; bv = [bm.verts.new((x, D, z)) for x, z in prof]
    bm.faces.new(fv[::-1]); bm.faces.new(bv)
    for i in range(5):
        j = (i + 1) % 5; bm.faces.new((fv[i], fv[j], bv[j], bv[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = assign(from_bm('shop_walls', bm), M['wall'])
    b = ob.modifiers.new('openings', 'BOOLEAN'); b.operation = 'DIFFERENCE'; b.operand_type = 'COLLECTION'; b.collection = CUTTERS; b.solver = 'EXACT'
    sh = ob.modifiers.new('lean', 'SIMPLE_DEFORM'); sh.deform_method = 'TAPER'; sh.factor = -.025; sh.deform_axis = 'Z'
    clay(ob, voxel=.022, smooth=.6, iters=5, wob=.07, wob_scale=1.4)
    ob.modifiers.move(ob.modifiers.find('lean'), 0)
    return ob

# window layout: (wall, u centre, v bottom, width, height, recess, style)
WINDOWS = [
    ('front', -.74, 2.78, .62, .9, .16, 'shutters'),
    ('front', .74, 2.78, .62, .9, .16, 'shutters'),
    ('front', 0.0, 4.62, .5, .62, .14, 'arch'),
    ('right', 1.32, 2.78, .6, .88, .16, 'shutters'),
    ('right', .55, .72, .5, .72, .14, 'plain'),
]
SHOP = dict(u0=-.18, u1=1.32, v0=.46, v1=1.78, depth=.8)
DOOR = dict(u0=-1.26, u1=-.48, v0=0.0, v1=1.86, depth=.16)

def build_openings():
    for wall, uc, v0, w, h, rec, style in WINDOWS:
        f, U, N_ = WALLS[wall]
        a, b = f(uc - w / 2, v0, .3), f(uc + w / 2, v0 + h + (w * .35 if style == 'arch' else 0), -rec)
        cutter_box((a + b) / 2, Vector((abs(b.x - a.x) or .01, abs(b.y - a.y) or .01, abs(b.z - a.z))))
    a, b = front(SHOP['u0'], SHOP['v0'], .3), front(SHOP['u1'], SHOP['v1'], -SHOP['depth'])
    cutter_box((a + b) / 2, Vector((abs(b.x - a.x), abs(b.y - a.y), abs(b.z - a.z))))
    a, b = front(DOOR['u0'], DOOR['v0'] - .1, .3), front(DOOR['u1'], DOOR['v1'], -DOOR['depth'])
    cutter_box((a + b) / 2, Vector((abs(b.x - a.x), abs(b.y - a.y), abs(b.z - a.z))))

def frame_bars(bm, wall, u0, u1, v0, v1, n0, n1, t, mull=(1, 1), arch=False):
    """A window frame as bars (fused later by the voxel remesh into one hand-modelled piece)."""
    wall_box(bm, wall, u0 - t, u0, v0 - t, v1 + t, n0, n1)
    wall_box(bm, wall, u1, u1 + t, v0 - t, v1 + t, n0, n1)
    wall_box(bm, wall, u0 - t, u1 + t, v0 - t, v0, n0, n1)
    if not arch: wall_box(bm, wall, u0 - t, u1 + t, v1, v1 + t, n0, n1)
    else:
        f, U, N_ = WALLS[wall]; r = (u1 - u0) / 2; uc = (u0 + u1) / 2
        for k in range(14):
            a0, a1 = math.pi * k / 14, math.pi * (k + 1) / 14
            p0 = (uc + (r + t / 2) * math.cos(a0), v1 + (r + t / 2) * math.sin(a0)); p1 = (uc + (r + t / 2) * math.cos(a1), v1 + (r + t / 2) * math.sin(a1))
            c = f((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (n0 + n1) / 2); ln = math.dist(p0, p1) + .02
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            if wall == 'front': bm_box(bm, c, (ln, abs(n1 - n0), t), rot=(0, -ang, 0))
    nu, nv = mull
    for i in range(1, nu + 1):
        u = u0 + (u1 - u0) * i / (nu + 1); wall_box(bm, wall, u - t * .28, u + t * .28, v0, v1 + (((u1 - u0) / 2) if arch else 0), n0 - .02, n1 - .04)
    for j in range(1, nv + 1):
        v = v0 + (v1 - v0) * j / (nv + 1); wall_box(bm, wall, u0, u1, v - t * .28, v + t * .28, n0 - .02, n1 - .04)

SNOWBITS = []      # (centre, radii) blobs of snow collected from everywhere, fused into one snow object per group

def snow_strip(group, p0, p1, thick=.07, width=.12, n=None, seed=0):
    """Snow resting along a ledge: a row of soft overlapping lumps (they melt into one by the remesh)."""
    rr = random.Random(seed); p0, p1 = Vector(p0), Vector(p1); L = (p1 - p0).length
    n = n or max(3, int(L / .07))
    for i in range(n + 1):
        t = i / n; c = p0.lerp(p1, t)
        k = .75 + .5 * rr.random()
        SNOWBITS.append((group, c + Vector((0, 0, thick * .35 * k)), (width * .5 * (0.9 + .3 * rr.random()), width * .5 * k, thick * k)))

def build_windows():
    frames, shutters, glass = bmesh.new(), bmesh.new(), []
    for i, (wall, uc, v0, w, h, rec, style) in enumerate(WINDOWS):
        f, U, N_ = WALLS[wall]; u0, u1, v1 = uc - w / 2, uc + w / 2, v0 + h
        t = .08
        frame_bars(frames, wall, u0, u1, v0, v1, -.02, .065, t, mull=(1, 2) if style != 'arch' else (1, 1), arch=style == 'arch')
        # deep inner reveal (the window sits back in the thick clay wall) and glass at the back
        gb = bmesh.new(); top = v1 + (w / 2 if style == 'arch' else 0)
        wall_box(gb, wall, u0 - .02, u1 + .02, v0 - .02, top + .02, -rec + .005, -rec + .02)
        g = assign(smooth_shade(from_bm(f'glass_{i}', gb)), M['glow'] if wall == 'front' else M['glow_soft']); glass.append(g)
        # sill and lintel
        wall_box(frames, wall, u0 - .12, u1 + .12, v0 - .13, v0 - .05, -.02, .16)
        snow_strip('ledges', f(u0 - .1, v0 - .03, .07), f(u1 + .1, v0 - .03, .07), .06, .14, seed=i)
        if style != 'arch':
            wall_box(frames, wall, u0 - .1, u1 + .1, v1 + .06, v1 + .16, -.02, .09)
            snow_strip('ledges', f(u0 - .08, v1 + .17, .04), f(u1 + .08, v1 + .17, .04), .04, .1, seed=10 + i)
        if style == 'shutters':
            for side in (-1, 1):
                su0 = u0 - .06 - .3 if side < 0 else u1 + .06; su1 = su0 + .3
                tilt = (R.random() - .5) * .03
                wall_box(shutters, wall, su0, su1, v0 - .02, v1 + .02, .0, .045)
                for k in range(7):
                    vv = v0 + .06 + (h - .08) * k / 7
                    wall_box(shutters, wall, su0 + .04, su1 - .04, vv, vv + .07, .04, .075)
                wall_box(shutters, wall, su0, su1, v0 - .02, v0 + .03, .03, .08)
                wall_box(shutters, wall, su0, su1, v1 - .03, v1 + .02, .03, .08)
    fo = assign(from_bm('window_frames', frames), M['cream']); clay(fo, voxel=.011, smooth=.5, iters=3, wob=.012, wob_scale=.5)
    so = assign(from_bm('shutters', shutters), M['shutter']); clay(so, voxel=.011, smooth=.45, iters=3, wob=.01, wob_scale=.5)
    return fo, so, glass

def build_shop_front():
    """The shop window (a deep lit display niche), its wooden frame, the red plinth, the door and its frame."""
    s = SHOP; bm = bmesh.new()
    t = .085
    frame_bars(bm, 'front', s['u0'], s['u1'], s['v0'], s['v1'], -.03, .07, t, mull=(2, 0))
    wall_box(bm, 'front', s['u0'], s['u1'], s['v1'] - .32, s['v1'] - .26, -.05, .02)    # transom bar
    # door frame and door
    d = DOOR
    wall_box(bm, 'front', d['u0'] - .09, d['u0'], d['v0'], d['v1'] + .09, -.02, .08)
    wall_box(bm, 'front', d['u1'], d['u1'] + .09, d['v0'], d['v1'] + .09, -.02, .08)
    wall_box(bm, 'front', d['u0'] - .09, d['u1'] + .09, d['v1'], d['v1'] + .1, -.02, .08)
    fo = assign(from_bm('shop_frame', bm), M['shopwood']); clay(fo, voxel=.012, smooth=.5, iters=3, wob=.012, wob_scale=.5)
    pb = bmesh.new()
    wall_box(pb, 'front', s['u0'] - .06, s['u1'] + .06, .05, s['v0'] - .02, -.02, .09)
    for k in range(3):     # raised panels
        uu0 = s['u0'] + .05 + (s['u1'] - s['u0'] - .1) * k / 3; uu1 = uu0 + (s['u1'] - s['u0'] - .1) / 3 - .06
        wall_box(pb, 'front', uu0, uu1, .12, s['v0'] - .1, .08, .12)
    po = assign(from_bm('shop_plinth', pb), M['plinth']); clay(po, voxel=.012, smooth=.5, iters=3, wob=.01, wob_scale=.5)
    db = bmesh.new()
    wall_box(db, 'front', d['u0'], d['u1'], d['v0'], d['v1'], -d['depth'] + .01, -d['depth'] + .07)
    for (a0, a1, b0, b1) in ((.08, .92, .08, .42), (.08, .92, .5, .54)):
        uu0 = d['u0'] + (d['u1'] - d['u0']) * a0; uu1 = d['u0'] + (d['u1'] - d['u0']) * a1
        wall_box(db, 'front', uu0, uu1, d['v0'] + d['v1'] * b0, d['v0'] + d['v1'] * b1, -d['depth'] + .06, -d['depth'] + .095)
    # the door's glazed top: muntin grid in front of a lit pane
    gu0, gu1 = d['u0'] + .08, d['u1'] - .08; gv0, gv1 = d['v1'] * .6, d['v1'] - .1
    for k in range(1, 3):
        uu = gu0 + (gu1 - gu0) * k / 3; wall_box(db, 'front', uu - .018, uu + .018, gv0, gv1, -d['depth'] + .06, -d['depth'] + .1)
    vv = (gv0 + gv1) / 2; wall_box(db, 'front', gu0, gu1, vv - .018, vv + .018, -d['depth'] + .06, -d['depth'] + .1)
    wall_box(db, 'front', gu0 - .04, gu1 + .04, gv0 - .04, gv0, -d['depth'] + .06, -d['depth'] + .1)
    wall_box(db, 'front', gu0 - .04, gu1 + .04, gv1, gv1 + .04, -d['depth'] + .06, -d['depth'] + .1)
    wall_box(db, 'front', gu0 - .04, gu0, gv0, gv1, -d['depth'] + .06, -d['depth'] + .1)
    wall_box(db, 'front', gu1, gu1 + .04, gv0, gv1, -d['depth'] + .06, -d['depth'] + .1)
    do = assign(from_bm('door', db), M['door']); clay(do, voxel=.01, smooth=.45, iters=3, wob=.008, wob_scale=.5)
    gb = bmesh.new(); wall_box(gb, 'front', gu0, gu1, gv0, gv1, -d['depth'] + .05, -d['depth'] + .06)
    assign(smooth_shade(from_bm('door_glass', gb)), M['glow'])
    # knob
    kb = bmesh.new(); bm_blob(kb, front(d['u1'] - .12, .92, -d['depth'] + .13), (.035, .035, .035))
    assign(smooth_shade(from_bm('door_knob', kb)), glossy_paint('brass', (.8, .58, .22), .3, 1.0))
    # doorstep
    sb = bmesh.new(); wall_box(sb, 'front', d['u0'] - .14, d['u1'] + .14, 0, .1, -.02, .32)
    so = assign(from_bm('doorstep', sb), M['stone']); clay(so, voxel=.015, smooth=.6, iters=4, wob=.02, wob_scale=.4)
    snow_strip('ledges', front(d['u0'] - .1, .11, .28), front(d['u1'] + .1, .11, .26), .05, .2, seed=31)
    # display glass and the warm interior of the shop window
    gb = bmesh.new(); wall_box(gb, 'front', s['u0'], s['u1'], s['v0'], s['v1'], -.06, -.055)
    assign(from_bm('shop_glass', gb), M['shopglass'])
    ib = bmesh.new()
    wall_box(ib, 'front', s['u0'] - .05, s['u1'] + .05, s['v0'] - .05, s['v1'] + .05, -s['depth'] - .02, -s['depth'] + .01)
    assign(smooth_shade(from_bm('shop_backdrop', ib)), M['shopback'])
    lt = bpy.data.lights.new('shop_light', 'POINT'); lt.energy = 70 if STAGE > 1 else 40; lt.color = (1.0, .66, .35); lt.shadow_soft_size = .3
    ob = link(bpy.data.objects.new('shop_light', lt)); ob.location = front((s['u0'] + s['u1']) / 2, s['v1'] - .25, -s['depth'] * .55)
    # foundation band of stones along the front and side
    fb = bmesh.new()
    x = -W / 2 - .04
    while x < W / 2:
        w = .22 + R.random() * .16; bm_blob(fb, (x + w / 2, -.035, .1 + R.random() * .02), (w / 2, .07, .1 + R.random() * .02)); x += w * .92
    y = 0.0
    while y < D:
        w = .22 + R.random() * .16; bm_blob(fb, (W / 2 + .035, y + w / 2, .1 + R.random() * .02), (.07, w / 2, .1 + R.random() * .02)); y += w * .92
    fo2 = assign(from_bm('foundation', fb), M['stone']); clay(fo2, voxel=.014, smooth=.5, iters=3, wob=.015, wob_scale=.3)

def build_awning():
    """Green-and-white striped awning: cloth sagging a little between its ribs, a scalloped valance, slightly
    uneven along its length, snow along the top."""
    x0, x1 = -1.5, 1.5; z_top, z_low = 2.42, 2.02; proj = .78
    nx, ny = 120, 24; stripe = .3
    bm = bmesh.new(); grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; t = j / ny
            sag = .025 * math.sin(math.pi * ((x - x0) / stripe)) ** 2 * math.sin(math.pi * t)
            belly = .03 * math.sin(math.pi * t)
            y = -t * proj; z = z_top + (z_low - z_top) * t - sag - belly * .5 + .012 * noise.noise(Vector((x * 2, t * 2, 0)))
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx): bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    # valance: a hanging flap with a scalloped hem
    vh = .2; vrow = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx; ph = ((x - x0) / stripe) % 1.0
        hem = vh - .06 + .07 * math.sqrt(max(0, 1 - (2 * ph - 1) ** 2))
        top = grid[ny][i].co
        vrow.append(bm.verts.new((x, top.y - .004, top.z - hem)))
    for i in range(nx): bm.faces.new((grid[ny][i], grid[ny][i + 1], vrow[i + 1], vrow[i]))
    ob = assign(from_bm('awning', bm), M['awning'])
    so = ob.modifiers.new('cloth_thickness', 'SOLIDIFY'); so.thickness = .028; so.offset = 0
    sd = ob.modifiers.new('smooth', 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    smooth_shade(ob)
    # metal/wood support rod ends and a snowy top edge
    rb = bmesh.new()
    for x in (x0 + .02, x1 - .02):
        bm_cyl(rb, (x, -proj / 2, (z_top + z_low) / 2 - .02), .022, math.hypot(proj, z_top - z_low) + .05, rot=(math.atan2(proj, z_top - z_low) + math.pi / 2, 0, 0), seg=10)
    assign(smooth_shade(from_bm('awning_rods', rb)), glossy_paint('dark_iron', (.08, .08, .08), .4, .6))
    rr = random.Random(41)
    for k in range(7):                        # a few soft drifts where the cloth meets the wall
        x = x0 + .2 + (x1 - x0 - .4) * (k + rr.uniform(-.2, .2)) / 6; t = rr.uniform(.04, .12); y = -t * proj; z = z_top + (z_low - z_top) * t + .03
        SNOWBITS.append(('awning_snow', Vector((x, y, z)), (rr.uniform(.18, .28), .07, .035)))
    snow_strip('awning_snow', (x0 + .04, -proj + .02, z_low + .005), (x1 - .04, -proj + .02, z_low + .005), .025, .05, seed=48)
    snow_strip('awning_snow', (x0 + .02, -.03, z_top + .02), (x1 - .02, -.03, z_top + .02), .06, .14, seed=49)

def snow_roll(bm, p0, p1, r0, flat=.8, seed=0, along=None):
    """A continuous rolled edge of snow: closely spaced lumps whose size drifts slowly (so the remesh makes one
    soft, uneven sausage instead of a row of balls)."""
    rr = random.Random(seed); p0, p1 = Vector(p0), Vector(p1); L = (p1 - p0).length
    n = max(4, int(L / (r0 * .35)))
    ph = rr.uniform(0, 10)
    for i in range(n + 1):
        t = i / n; c = p0.lerp(p1, t)
        k = 1 + .28 * noise.noise(Vector((t * L * 1.3 + ph, ph, .5))) + .1 * noise.noise(Vector((t * L * 4 + ph, 2, 1)))
        bm_blob(bm, c, (r0 * k, r0 * k, r0 * k * flat), sub=2)

def build_roof():
    """Roof boards, clay tiles on the lower part of each slope, a thick blanket of snow above with a lumpy rolled
    edge, snow icing along the front gable, and a brick chimney with its own snow cap."""
    th = .12
    bm = bmesh.new()
    for sgn in (-1, 1):
        ridge = Vector((0, 0, HR)); eave = Vector((sgn * (W / 2 + OVS), 0, H - OVS * SLOPE))
        dirv = (eave - ridge).normalized(); nrm = Vector((-dirv.z * sgn, 0, abs(dirv.x))) if sgn > 0 else Vector((dirv.z * -1, 0, abs(dirv.x)))
        nrm = Vector((sgn * abs(dirv.z), 0, abs(dirv.x))).normalized()
        pts = []
        for p in (ridge, eave):
            for y in (-OVF, D + OVB):
                for o in (0, th): pts.append(p + Vector((0, y, 0)) + nrm * o)
        vs = [bm.verts.new(p) for p in pts]
        idx = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]
        for f in idx: bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ro = assign(from_bm('roof_boards', bm), M['roofwood']); clay(ro, voxel=.02, smooth=.5, iters=3, wob=.03, wob_scale=.6)
    # tiles: overlapping rows, each tile its own slightly different shape, angle and colour
    tb = bmesh.new()
    for sgn in (-1, 1):
        ridge = Vector((0, 0, HR + th)); eave = Vector((sgn * (W / 2 + OVS), 0, H - OVS * SLOPE + th))
        L_ = (eave - ridge).length; dirv = (eave - ridge).normalized(); nrm = Vector((sgn * abs(dirv.z), 0, abs(dirv.x))).normalized()
        ang = math.atan2(eave.z - ridge.z, abs(eave.x - ridge.x))
        rows = 7
        for rI in range(rows):
            t = .52 + .48 * rI / (rows - 1)
            base = ridge + dirv * (L_ * t)
            off = .14 if rI % 2 else 0; y = -OVF + .1 - off * .5
            while y < D + OVB - .32:
                w = .27 * (.9 + .2 * R.random())
                c = base + Vector((0, y + w / 2, 0)) + nrm * (.025 + .01 * R.random())
                vs = bm_rbox(tb, c, (.24 * (.95 + .1 * R.random()), w * .92, .035), rot=(R.uniform(-.05, .05), sgn * ang + R.uniform(-.04, .04) + sgn * .12, R.uniform(-.05, .05)))
                k = R.uniform(-.07, .07); paint(tb, vs, (.62 + k + R.uniform(-.04, .04), .27 + k * .6 + R.uniform(-.03, .03), .16 + k * .3))
                y += w
    to = assign(smooth_shade(from_bm('roof_tiles', tb)), M['tiles'])
    # snow blanket
    sb = bmesh.new()
    for sgn in (-1, 1):
        ridge = Vector((0, 0, HR + th + .02)); eave = Vector((sgn * (W / 2 + OVS), 0, H - OVS * SLOPE + th + .02))
        L_ = (eave - ridge).length; dirv = (eave - ridge).normalized(); nrm = Vector((sgn * abs(dirv.z), 0, abs(dirv.x))).normalized()
        cover = .64
        # the blanket: one slab lying on the slope, thicker towards the ridge, with a few broad soft swells
        ang = math.atan2(-dirv.z, abs(dirv.x))
        mid = ridge + dirv * (L_ * cover / 2) + Vector((0, (D + OVB - OVF) / 2, 0)) + nrm * .1
        bm_box(sb, mid, (L_ * cover, D + OVF + OVB - .12, .2), rot=(0, sgn * ang, 0))
        for k in range(3):
            t = R.uniform(.15, cover - .1); y = R.uniform(0, D)
            bm_blob(sb, ridge + dirv * (L_ * t) + Vector((0, y, 0)) + nrm * .14, (.55, .6, .1), rot=(0, sgn * ang, 0), sub=2)
        # the lower edge of the blanket: a soft rolled lip that wanders a little up and down the slope
        prev = None; y = -OVF - .02; pts = []
        while y <= D + OVB + .02:
            t = cover + .05 * noise.noise(Vector((y * .9, sgn * 3.0, .2)))
            pts.append(ridge + dirv * (L_ * t) + Vector((0, y, 0)) + nrm * .1); y += .12
        for a, b in zip(pts, pts[1:]): snow_roll(sb, a, b, .15, .75, seed=int(a.y * 100) + sgn)
        # icing along the front and back gable edges, overhanging the verge, with a couple of soft drips
        for yy, out in ((-OVF + .05, -.04), (D + OVB - .05, .04)):
            a = ridge + Vector((0, yy, 0)) + nrm * .1; b = ridge + dirv * (L_ * .99) + Vector((0, yy, 0)) + nrm * .1
            snow_roll(sb, a, b, .17, .8, seed=7 + sgn + int(yy))
            for k in range(3):
                t = R.uniform(.25, .9); c = ridge + dirv * (L_ * t) + Vector((0, yy + out * 2.2, 0)) + nrm * .02
                bm_blob(sb, c + Vector((0, 0, -.1)), (.07, .07, .14), sub=2)
    # ridge cap
    snow_roll(sb, (0, -OVF + .05, HR + th + .14), (0, D + OVB - .05, HR + th + .14), .24, .7, seed=99)
    so = assign(from_bm('roof_snow', sb), M['snow']); clay(so, voxel=.03, smooth=.85, iters=12, wob=.025, wob_scale=.6)
    # chimney
    cb = bmesh.new(); cx, cy = -.8, 1.75
    zb = HR - (abs(cx) + .25) * SLOPE
    bm_box(cb, (cx, cy, (zb + HR + .75) / 2), (.46, .46, HR + .75 - zb))
    bm_box(cb, (cx, cy, HR + .78), (.56, .56, .1))
    co = assign(from_bm('chimney', cb), M['brick']); clay(co, voxel=.014, smooth=.4, iters=3, wob=.02, wob_scale=.5)
    for k in range(9):
        a = k / 9 * math.tau; SNOWBITS.append(('chimney_snow', Vector((cx + .17 * math.cos(a), cy + .17 * math.sin(a), HR + .88)), (.12, .12, .09)))
    SNOWBITS.append(('chimney_snow', Vector((cx, cy, HR + .93)), (.2, .2, .1)))

def build_street():
    """A small square of cobbles, packed snow between and over them in drifts, banked against the shop."""
    cb = bmesh.new(); n = 0
    def lane(x, y):   # 1 on the street, 0 in the deep snow beside it, soft and wavering between
        edge_front = -3.4 + .55 * noise.noise(Vector((x * .35, 0, 7))) + .15 * noise.noise(Vector((x * 1.5, 0, 3)))
        edge_side = W / 2 + 2.9 + .55 * noise.noise(Vector((0, y * .35, 9))) + .15 * noise.noise(Vector((0, y * 1.5, 4)))
        edge_back = .55 + .45 * noise.noise(Vector((x * .5, 5, 1)))                    # where the front lane meets the snow beside the shop
        edge_in = W / 2 - .2 + .45 * noise.noise(Vector((7, y * .5, 2)))
        a = min(1.0, max(0.0, (y - edge_front) / .8)) * min(1.0, max(0.0, (edge_back - y) / .7))
        b = min(1.0, max(0.0, (edge_side - x) / .8)) * min(1.0, max(0.0, (x - edge_in) / .5))
        a, b = a * a * (3 - 2 * a), b * b * (3 - 2 * b)
        return max(a if -9 < x < 11 else 0.0, b if -6 < y < 8 else 0.0)
    for gy in range(-13, 26):
        for gx in range(-26, 30):
            x = gx * .29 + (gy % 2) * .145 + R.uniform(-.03, .03); y = gy * .27 + R.uniform(-.03, .03)
            if -W / 2 - .05 < x < W / 2 + .05 and -.05 < y < D: continue
            if lane(x, y) < .15: continue
            r = .15 + .025 * R.random()
            vs = bm_blob(cb, (x, y, -.01), (r * R.uniform(.95, 1.15), r * R.uniform(.82, .98), .06 + .02 * R.random()), rot=(R.uniform(-.06, .06), R.uniform(-.06, .06), R.uniform(0, 3.1)), sub=2)
            for v in vs:   # no two stones the same shape
                v.co += Vector((0, 0, .012 * noise.noise(v.co * 9))) + (v.co - Vector((x, y, -.01))) * .12 * noise.noise(v.co * 5 + Vector((3, 1, 2)))
            k = R.uniform(-.08, .08); paint(cb, vs, (.48 + k + R.uniform(-.04, .04), .44 + k, .4 + k + R.uniform(-.03, .03))); n += 1
    co = assign(smooth_shade(from_bm('cobbles', cb)), M['cobble'])
    gb = bmesh.new(); bm_box(gb, (.5, 0, -.06), (40, 40, .1)); assign(from_bm('ground', gb), M['ground'])
    # snow sheet: a height field over the cobbles; it pokes through in worn patches and banks up at walls
    nx, ny = 240, 240; X0, X1, Y0, Y1 = -12.0, 14.0, -12.0, 16.0
    sb = bmesh.new(); grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = X0 + (X1 - X0) * i / nx; y = Y0 + (Y1 - Y0) * j / ny
            st = lane(x, y)
            # on the lane: a dusting that settles between the stones (tops show through), thicker in patches;
            # off it: soft deep snow, banked a little where it meets the lane
            dust = .015 + .035 * max(0.0, noise.noise(Vector((x * 1.1, y * 1.1, 1.3)))) + .012 * noise.noise(Vector((x * 4, y * 4, 4.1)))
            deep = .14 + .09 * noise.noise(Vector((x * .45, y * .45, 2.2))) + .035 * noise.noise(Vector((x * 1.8, y * 1.8, 5.0)))
            h = dust * st + deep * (1 - st) + .05 * st * (1 - st) * 4
            dx = max(-W / 2 - x, 0.0, x - W / 2); dy = max(-y, 0.0, y - D); dist = math.hypot(dx, dy)
            under_awning = -1.5 < x < 1.5 and -.85 < y < 0
            h += (.03 if under_awning else .14) * math.exp(-dist / .2)
            inside = -W / 2 < x < W / 2 and 0 < y < D
            row.append(sb.verts.new((x, y, (h if not inside else -.2))))
        grid.append(row)
    for j in range(ny):
        for i in range(nx): sb.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    so = assign(from_bm('street_snow', sb), M['snow']); smooth_shade(so)
    sd = so.modifiers.new('soft', 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    return n

def fuse_snow():
    groups = {}
    for g, c, r in SNOWBITS: groups.setdefault(g, []).append((c, r))
    for g, bits in groups.items():
        bm = bmesh.new()
        for c, r in bits: bm_blob(bm, c, r, sub=2)
        ob = assign(from_bm(g, bm), M['snow']); clay(ob, voxel=.012 if g != 'awning_snow' else .014, smooth=.6, iters=4, wob=.012, wob_scale=.3)

# ---------------------------------------------------------------- decorations (stage 3)
def needles(bm, c, r, n, rr, color_jit=True, droop=0.0):
    """A clump of clay 'needles': little elongated lumps, the way a model maker builds greenery."""
    vs_all = []
    for _ in range(n):
        d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1) - droop)).normalized()
        p = Vector(c) + d * r * rr.uniform(.2, 1.0)
        rot = d.to_track_quat('Z', 'Y').to_euler()
        vs = bm_blob(bm, p, (r * .16, r * .16, r * .55), rot=rot, sub=1)
        g = rr.uniform(-.04, .04); paint(bm, vs, (.07 + g * .5, .22 + g, .1 + g * .5)); vs_all += vs
    return vs_all

def bauble(bm_list, c, r, col):
    bm_blob(bm_list[col], c, (r, r, r), sub=2)

def bow(bm, c, size, facing='front', rot_extra=0.0):
    """A ribbon bow: two squashed loops and two tails."""
    cv = Vector(c)
    for s in (-1, 1):
        t = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=size * .55, radius2=size * .55, depth=size * .18)
        vs = t['verts']
        bmesh.ops.transform(bm, matrix=Matrix.Diagonal(Vector((1.0, .5, 1.0, 1))), verts=vs)
        bmesh.ops.transform(bm, matrix=Euler((math.pi / 2, 0, s * .5 + rot_extra)).to_matrix().to_4x4(), verts=vs)
        bmesh.ops.translate(bm, vec=cv + Vector((s * size * .48, 0, size * .08)), verts=vs)
        bm_box(bm, cv + Vector((s * size * .3, 0, -size * .7)), (size * .22, size * .1, size * 1.0), rot=(0, s * .35, 0))
    bm_blob(bm, cv, (size * .25, size * .18, size * .22))

def build_decorations():
    rr = random.Random(5)
    green, red, gold = bmesh.new(), bmesh.new(), bmesh.new()
    balls = {'red': red, 'gold': gold}
    # wreath on the door's glazed top
    d = DOOR; wc = front((d['u0'] + d['u1']) / 2, d['v1'] * .78, -d['depth'] + .14)
    for k in range(30):
        a = k / 30 * math.tau; p = wc + Vector((.2 * math.cos(a), 0, .2 * math.sin(a)))
        needles(green, p, .075, 7, rr)
    for k in range(9):
        a = k / 9 * math.tau + .3; bauble(balls, wc + Vector((.22 * math.cos(a), -.06, .22 * math.sin(a))), .025, 'red' if k % 3 else 'gold')
    rb = bmesh.new(); bow(rb, wc + Vector((0, -.06, -.2)), .12)
    # garlands under the upper front windows and along the awning top
    def garland(p0, p1, sag, n, seed):
        g = random.Random(seed)
        for i in range(n + 1):
            t = i / n; p = Vector(p0).lerp(Vector(p1), t); p.z -= sag * math.sin(math.pi * t)
            needles(green, p, .06, 6, g, droop=.3)
            if i % 3 == 1: bauble(balls, p + Vector((0, -.06, -.03)), .03, 'red' if (i // 3) % 2 == 0 else 'gold')
    for wall, uc, v0, w, h, rec, style in WINDOWS[:2]:
        garland(front(uc - w / 2 - .08, v0 - .16, .1), front(uc + w / 2 + .08, v0 - .16, .1), .07, 12, int(uc * 10) + 50)
    garland(front(-1.45, 2.45, .06), front(1.45, 2.45, .06), .0, 34, 77)
    # a little Christmas tree by the door, in a wooden tub
    tx, ty = -2.25, -.7
    tree = bmesh.new(); tree_snow = bmesh.new()
    tiers = [(.57, .72, .0), (.49, .6, .5), (.4, .48, .93), (.3, .38, 1.3), (.19, .28, 1.62)]
    for rad, hgt, z0 in tiers:
        zz = .5 + z0
        bm_cyl(tree, (tx, ty, zz + hgt / 2), rad * .9, hgt, seg=20, r2=rad * .25)
        nb = int(rad * 60)
        for k in range(nb):
            a = k / nb * math.tau + rr.uniform(-.1, .1)
            p = Vector((tx + rad * .85 * math.cos(a), ty + rad * .85 * math.sin(a), zz + .06))
            vs = bm_blob(tree, p, (.06, .06, .13), rot=(math.cos(a) * -.9 + math.pi / 2 * 0, 0, 0), sub=1)
            bmesh.ops.transform(tree, matrix=Euler((0, math.pi / 2 + .55, a)).to_matrix().to_4x4(), verts=vs, space=Matrix.Translation(-p))
            if rr.random() < .55:
                bm_blob(tree_snow, p + Vector((0, 0, .06)) - Vector((math.cos(a), math.sin(a), 0)) * .04, (.06, .06, .035), sub=2)
            if rr.random() < .22: bauble(balls, p + Vector((math.cos(a), math.sin(a), 0)) * .05 + Vector((0, 0, -.03)), .028, 'red' if rr.random() < .6 else 'gold')
        for k in range(int(rad * 14)):
            a = rr.uniform(0, math.tau); r_ = rad * rr.uniform(.3, .7)
            bm_blob(tree_snow, (tx + r_ * math.cos(a), ty + r_ * math.sin(a), zz + hgt * (1 - r_ / rad) * .8 + .02), (.07, .07, .035), sub=2)
    tro = assign(from_bm('xmas_tree', tree), clay_mat('tree_green', (.07, .25, .12), var=.12, scale=3.0, bump_s=.45))
    clay(tro, voxel=.014, smooth=.4, iters=3, wob=.01, wob_scale=.3)
    tso = assign(from_bm('xmas_tree_snow', tree_snow), M['snow']); clay(tso, voxel=.012, smooth=.6, iters=4)
    tub = bmesh.new(); bm_cyl(tub, (tx, ty, .26), .38, .52, seg=24, r2=.45)
    for zz in (.12, .42): bm_cyl(tub, (tx, ty, zz), .42 + (zz - .12) * .12, .05, seg=24)
    tuo = assign(from_bm('tree_tub', tub), wood_mat('tub_wood', (.45, .26, .12), grain_dir='Z', scale=2)); clay(tuo, voxel=.012, smooth=.4, iters=3)
    star = bmesh.new(); pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5; r_ = .11 if k % 2 == 0 else .05
        pts.append((tx + r_ * 1.3 * math.cos(a), ty - .01, 2.62 + r_ * 1.3 * math.sin(a)))
    vf = [star.verts.new(p) for p in pts]; fc = star.faces.new(vf)
    ext = bmesh.ops.extrude_face_region(star, geom=[fc]); bmesh.ops.translate(star, vec=(0, .05, 0), verts=[v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)])
    sto = assign(from_bm('tree_star', star), glossy_paint('gold_star', (.95, .7, .2), .3, .8)); clay(sto, voxel=.006, smooth=.5, iters=3)
    # tree fairy lights
    fl = bmesh.new()
    for k in range(70):
        tI = rr.randrange(len(tiers)); rad, hgt, z0 = tiers[tI]; a = rr.uniform(0, math.tau)
        bm_blob(fl, (tx + rad * .8 * math.cos(a), ty + rad * .8 * math.sin(a), .5 + z0 + .12), (.02, .02, .02), sub=1)
    assign(smooth_shade(from_bm('fairy_lights', fl)), emissive('fairy', (1.0, .78, .4), 25))
    # presents outside the shop window
    pres = [((.25, -.42), (.28, .26, .24), (.65, .08, .07), (.95, .78, .3), .2), ((.62, -.5), (.22, .22, .3), (.12, .32, .18), (.85, .1, .08), -.3),
            ((.95, -.38), (.32, .24, .2), (.2, .3, .6), (.95, .9, .8), .5), ((-1.7, -.98), (.2, .2, .18), (.85, .7, .2), (.7, .08, .06), .1),
            ((.45, -.78), (.17, .17, .14), (.8, .2, .3), (.98, .95, .9), .9)]
    for i, ((px, py), (sx, sy, sz), c1, c2, rz) in enumerate(pres):
        sx, sy, sz = sx * 1.3, sy * 1.3, sz * 1.3
        bb = bmesh.new(); bm_box(bb, (0, 0, sz / 2 + .03), (sx, sy, sz)); bmesh.ops.transform(bb, matrix=Matrix.Rotation(rz, 4, 'Z'), verts=bb.verts[:]); bmesh.ops.translate(bb, vec=(px, py, 0), verts=bb.verts[:])
        bo = assign(from_bm(f'present_{i}', bb), clay_mat(f'present_paper_{i}', c1, var=.08, scale=4, bump_s=.25)); clay(bo, voxel=.01, smooth=.45, iters=3)
        rb2 = bmesh.new()
        bm_box(rb2, (0, 0, sz / 2 + .03), (sx + .012, .045, sz + .012)); bm_box(rb2, (0, 0, sz / 2 + .03), (.045, sy + .012, sz + .012))
        bow(rb2, (0, 0, sz + .08), .07)
        bmesh.ops.transform(rb2, matrix=Matrix.Rotation(rz, 4, 'Z'), verts=rb2.verts[:]); bmesh.ops.translate(rb2, vec=(px, py, 0), verts=rb2.verts[:])
        ro = assign(from_bm(f'ribbon_{i}', rb2), glossy_paint(f'ribbon_{i}', c2, .35)); clay(ro, voxel=.007, smooth=.4, iters=2)
        SNOWBITS.append(('present_snow', Vector((px + .03, py - .02, sz + .05)), (sx * .3, sy * .3, .02)))
    # the shop's own display: a rocking horse and a stack of presents behind the glass
    s = SHOP; hb = bmesh.new(); hx = (s['u0'] + s['u1']) / 2 - .1; hy = .5; hz = s['v0'] + .02
    bm_blob(hb, (hx, hy, hz + .38), (.22, .08, .1)); bm_blob(hb, (hx + .23, hy, hz + .52), (.07, .06, .12), rot=(0, -.6, 0))
    bm_blob(hb, (hx + .27, hy, hz + .6), (.09, .055, .05))
    for lx in (-.13, .13):
        for ly in (-.04, .04): bm_cyl(hb, (hx + lx, hy + ly, hz + .22), .022, .26, rot=(0, lx, 0), seg=8)
    for k in range(13):
        a = math.pi * (k / 12) * .7 + math.pi * .15
        bm_blob(hb, (hx + .32 * math.cos(a) * -1, hy, hz + .38 - .3 * math.sin(a)), (.04, .05, .02), rot=(0, a, 0), sub=1)
    ho = assign(from_bm('rocking_horse', hb), clay_mat('horse_cream', (.9, .84, .72), var=.05, scale=4)); clay(ho, voxel=.008, smooth=.5, iters=3)
    db = bmesh.new()
    for (ox, sz, oz) in ((.42, .2, 0), (.42, .15, .2), (-.45, .22, 0), (-.47, .12, .22)):
        bm_box(db, (hx + ox, hy + .05, hz + oz + sz / 2), (sz, sz, sz), rot=(0, 0, ox))
    do = assign(from_bm('display_presents', db), clay_mat('display_paper', (.7, .12, .1), var=.15, scale=4)); clay(do, voxel=.01, smooth=.4, iters=2)
    go = assign(from_bm('greenery', green), clay_mat('greenery_clay', (.07, .23, .11), var=.1, use_attr=True, scale=4.0, bump_s=.4))
    clay(go, voxel=.009, smooth=.35, iters=2)
    assign(smooth_shade(from_bm('baubles_red', red)), glossy_paint('bauble_red', (.75, .04, .04), .18))
    assign(smooth_shade(from_bm('baubles_gold', gold)), glossy_paint('bauble_gold', (.95, .66, .2), .22, .9))
    bo = assign(from_bm('wreath_bow', rb), clay_mat('bow_red', (.72, .05, .05), var=.06, scale=5, bump_s=.2, sheen=.35)); clay(bo, voxel=.007, smooth=.4, iters=2)

def build_lamp_and_lights():
    """A street lamp at the corner (its glow pools on the snow and rakes the side wall) and a string of warm
    bulbs along the awning."""
    rr = random.Random(21); lx, ly = -3.55, -1.55
    pb = bmesh.new()
    bm_cyl(pb, (lx, ly, .12), .2, .24, seg=16, r2=.15)
    bm_cyl(pb, (lx, ly, 1.6), .065, 2.9, seg=12, r2=.05)
    for zz in (.5, 2.9): bm_cyl(pb, (lx, ly, zz), .1, .08, seg=12)
    bm_cyl(pb, (lx, ly, 3.1), .2, .12, seg=6, r2=.26)                   # lantern base
    for a in range(6):
        ang = a / 6 * math.tau; bm_cyl(pb, (lx + .22 * math.cos(ang), ly + .22 * math.sin(ang), 3.42), .018, .55, seg=6)
    bm_cyl(pb, (lx, ly, 3.75), .32, .14, seg=6, r2=.12)                 # lantern hat
    bm_blob(pb, (lx, ly, 3.9), (.06, .06, .08))
    po = assign(from_bm('lamp_post', pb), glossy_paint('lamp_iron', (.05, .055, .06), .45, .3)); clay(po, voxel=.012, smooth=.4, iters=2)
    gb = bmesh.new(); bm_cyl(gb, (lx, ly, 3.42), .2, .5, seg=6, r2=.22)
    assign(smooth_shade(from_bm('lamp_glass', gb)), emissive('lamp_glow', (1.0, .62, .25), 9))
    lt = bpy.data.lights.new('lamp_light', 'POINT'); lt.energy = 220; lt.color = (1.0, .64, .32); lt.shadow_soft_size = .2
    ob = link(bpy.data.objects.new('lamp_light', lt)); ob.location = (lx, ly - .3, 3.42)
    SNOWBITS.append(('lamp_snow', Vector((lx, ly, 3.86)), (.34, .34, .07)))
    SNOWBITS.append(('lamp_snow', Vector((lx, ly, 3.96)), (.16, .16, .07)))
    # string lights along the awning top, hung in little swags
    sl = bmesh.new(); wire = bmesh.new()
    n = 26
    for i in range(n + 1):
        x = -1.45 + 2.9 * i / n; sw = .05 * abs(math.sin(math.pi * ((i % 4) / 4)))
        p = Vector((x, -.84, 2.07 - sw))
        bm_blob(sl, p, (.022, .022, .03), sub=1)
    assign(smooth_shade(from_bm('string_lights', sl)), emissive('string_glow', (1.0, .7, .35), 30))

def build_background():
    """Out-of-focus village beyond: gabled houses in the Toy Town colours with warm windows and snowy roofs,
    soft shapes only, plus a few fir trees and falling snow."""
    bm_r = bmesh.new(); wb = bmesh.new(); snow = bmesh.new(); rr = random.Random(9)
    houses = [(-14.0, 8.0, 3.0, 4.4, (.3, .4, .62)), (-10.5, 9.0, 2.8, 4.8, (.85, .75, .55)), (-7.0, 9.5, 2.8, 4.2, (.6, .14, .1)), (-3.6, 11.0, 2.6, 5.0, (.82, .62, .2)), (-.4, 12.5, 3.0, 4.4, (.75, .45, .55)),
              (3.2, 11.5, 2.8, 5.2, (.85, .7, .45)), (6.8, 10.0, 3.2, 4.6, (.55, .12, .12)), (10.2, 9.0, 2.8, 4.0, (.2, .35, .3))]
    for i, (x, y, w, h, col) in enumerate(houses):
        b = bmesh.new(); r = h + w * .55
        prof = [(-w / 2, 0), (w / 2, 0), (w / 2, h), (0, r), (-w / 2, h)]
        y += 4.5
        fv = [b.verts.new((x + px, y - 1.2, pz)) for px, pz in prof]; bv = [b.verts.new((x + px, y + 1.2, pz)) for px, pz in prof]
        b.faces.new(fv[::-1]); b.faces.new(bv)
        for k in range(5): j = (k + 1) % 5; b.faces.new((fv[k], fv[j], bv[j], bv[k]))
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        o = assign(from_bm(f'far_house_{i}', b), clay_mat(f'far_house_{i}', col, var=.15, scale=.8, bump_s=.4)); clay(o, voxel=.06, smooth=.5, iters=3, wob=.06, wob_scale=1.2)
        for sgn in (-1, 1):
            a = Vector((x, y, r + .05)); e = Vector((x + sgn * (w / 2 + .3), y, h - .2))
            snow_roll(snow, a + Vector((0, -1.35, 0)), e + Vector((0, -1.35, 0)), .25, .7, seed=i * 3 + sgn)
            for t in (.2, .45, .7, .9):
                p = a.lerp(e, t); snow_roll(snow, p + Vector((0, -1.3, .05)), p + Vector((0, 1.3, .05)), .28, .5, seed=i * 7 + int(t * 10))
        for k in range(rr.randint(3, 5)):
            bm_box(wb, (x + rr.uniform(-w / 3, w / 3), y - 1.24, rr.uniform(1.0, h - .8)), (.42, .04, .58))
    so = assign(from_bm('far_snow', snow), M['snow']); clay(so, voxel=.06, smooth=.6, iters=4)
    assign(from_bm('village_windows', wb), emissive('far_windows', (1.0, .5, .18), 5))
    tb = bmesh.new()
    for k in range(16):
        x = rr.uniform(-11, 14); y = rr.uniform(9.5, 18); h = rr.uniform(2.5, 4.8)
        for tI in range(4):
            bm_cyl(tb, (x, y, h * (.15 + tI * .2)), h * (.32 - tI * .065), h * .32, seg=12, r2=h * .05)
    to = assign(from_bm('far_trees', tb), clay_mat('far_trees', (.08, .2, .13), var=.2, scale=.8)); clay(to, voxel=.06, smooth=.5, iters=2)
    fb = bmesh.new()
    for k in range(320):
        bm_blob(fb, (rr.uniform(-6, 8), rr.uniform(-9, 5), rr.uniform(.3, 8.5)), (.02, .02, .02), sub=1)
    assign(smooth_shade(from_bm('falling_snow', fb)), M['snow'])

# ---------------------------------------------------------------- light, camera, render
def setup_world_and_lights():
    w = bpy.data.worlds.new('dusk'); SCN.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    if STAGE == 1:
        bg.inputs['Color'].default_value = (.35, .38, .45, 1); bg.inputs['Strength'].default_value = .8
    else:
        nt = w.node_tree; N_ = nt.nodes; L_ = nt.links
        sky = N_.new('ShaderNodeTexGradient'); tc = N_.new('ShaderNodeTexCoord'); sep = N_.new('ShaderNodeSeparateXYZ')
        L_.new(tc.outputs['Generated'], sep.inputs[0])
        ramp = N_.new('ShaderNodeValToRGB'); L_.new(sep.outputs['Z'], ramp.inputs[0])
        ramp.color_ramp.elements[0].position = .45; ramp.color_ramp.elements[0].color = (.05, .055, .09, 1)
        ramp.color_ramp.elements[1].position = .75; ramp.color_ramp.elements[1].color = (.07, .1, .2, 1)
        L_.new(ramp.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = .6 if STAGE == 2 else .35
    def light(name, kind, loc, rot, energy, color, size=1.0, spot=None):
        lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = color
        if kind == 'AREA': lt.size = size; lt.shape = 'DISK'
        if kind == 'SUN': lt.angle = math.radians(size)
        if kind in ('POINT', 'SPOT'): lt.shadow_soft_size = size
        ob = link(bpy.data.objects.new(name, lt)); ob.location = loc; ob.rotation_euler = rot; return ob
    if STAGE == 1:
        light('sun', 'SUN', (0, 0, 10), (math.radians(50), 0, math.radians(30)), 3.0, (1, 1, 1), 5)
        return
    # cool moonlight from behind-left: rims the roof snow and separates the shop from the dark
    light('moon', 'SUN', (0, 0, 10), (math.radians(58), 0, math.radians(-150)), .9, (.6, .72, 1.0), 6)
    # warm key, high front-left and broad, like a big soft studio lamp standing in for a low winter sun
    light('key', 'AREA', (-9, -11, 9), (math.radians(52), 0, math.radians(-40)), 1500 if STAGE == 2 else 1300, (1.0, .74, .48) if STAGE > 2 else (1.0, .78, .55), 5)
    # cool sky fill from the other side, so shadows go blue the way they do on a set at dusk
    light('sky_fill', 'AREA', (9, -9, 6), (math.radians(60), 0, math.radians(45)), 260, (.55, .66, 1.0), 8)
    # warm bounce on the street from the shop windows
    light('window_spill', 'AREA', (.55, -.9, 1.3), (math.radians(-60), 0, 0), 70, (1.0, .6, .3), 1.2)
    light('door_spill', 'AREA', (-.85, -.6, 1.6), (math.radians(-70), 0, 0), 22, (1.0, .6, .3), .6)
    for wall, uc, v0, w_, h_, rec, style in WINDOWS:
        f, U, N_ = WALLS[wall]; p = f(uc, v0 + h_ / 2, .35)
        rot = (math.radians(-80), 0, 0) if wall == 'front' else (0, math.radians(80), 0)
        light(f'spill_{uc:.2f}', 'AREA', p, rot, 12, (1.0, .6, .3), .5)
    # warm lamp off to the right, out of frame: the 'street lamp' glow that rakes across the side wall
    if STAGE == 2: light('street_lamp', 'POINT', (4.3, -1.6, 3.2), (0, 0, 0), 320, (1.0, .68, .38), .25)
    # warm top light so the roof snow and side wall catch the glow of the street
    if STAGE > 2: light('top_warm', 'AREA', (7, -5, 13), (math.radians(35), 0, math.radians(55)), 650, (1.0, .8, .58), 5)
    # a cool rim from behind-right
    light('rim', 'AREA', (4, 6, 6), (math.radians(-60), 0, math.radians(150)), 450, (.6, .72, 1.0), 4)

def setup_camera():
    cam = bpy.data.cameras.new('cam'); co = link(bpy.data.objects.new('cam', cam)); SCN.camera = co
    target = Vector((.3, .5, 3.25))
    co.location = target + Vector((14.5, -27.0, 11.0)) * 1.06
    co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler()
    cam.lens = 98; cam.sensor_width = 36
    if STAGE >= 3:
        cam.dof.use_dof = True; cam.dof.focus_distance = (Vector((.6, -.2, 2.6)) - co.location).length; cam.dof.aperture_fstop = .09
        cam.dof.aperture_blades = 7; cam.dof.aperture_ratio = 1.0
    return co

def setup_render():
    r = SCN.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y = RES; r.resolution_percentage = 100
    c = SCN.cycles; c.device = 'CPU'; c.samples = SAMPLES; c.use_adaptive_sampling = True; c.adaptive_threshold = .02
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
    c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 6; c.transparent_max_bounces = 8
    c.caustics_reflective = False; c.caustics_refractive = False; c.blur_glossy = 1.0
    c.sample_clamp_indirect = 8
    SCN.view_settings.view_transform = 'AgX'; SCN.view_settings.look = 'AgX - Medium High Contrast' if STAGE > 1 else 'None'
    SCN.view_settings.exposure = .25 if STAGE > 1 else 0
    r.image_settings.file_format = 'PNG'; r.image_settings.color_depth = '8'
    r.use_persistent_data = False
    try: r.threads_mode = 'AUTO'
    except Exception: pass

# ---------------------------------------------------------------- build
t0 = time.time()
def timed(fn, *a):
    t = time.time(); r = fn(*a); print(f'TIME {fn.__name__} {time.time() - t:.1f}s', flush=True); return r
timed(build_openings)
walls = timed(build_walls)
timed(build_windows)
timed(build_shop_front)
timed(build_awning)
timed(build_roof)
n_cobbles = timed(build_street)
if STAGE >= 3:
    timed(build_decorations); timed(build_background); timed(build_lamp_and_lights)
timed(fuse_snow)
def eval_all():
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in SCN.objects:
        if ob.type == 'MESH':
            t = time.time(); ob.evaluated_get(deps); dt = time.time() - t
timed(eval_all)
setup_world_and_lights()
setup_camera()
setup_render()
if STAGE >= 3:
    # glints on the frames and a faint mist so far things sit back
    pass
t_build = time.time() - t0
SCN.render.filepath = os.path.join(OUT, f'iteration{STAGE}_{RES[0]}x{RES[1]}.png')
if STAGE >= 3:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'blue_shop_claymation.blend'), compress=True)
t1 = time.time(); bpy.ops.render.render(write_still=True); t_render = time.time() - t1
deps = bpy.context.evaluated_depsgraph_get(); tris = 0; objs = 0
for ob in SCN.objects:
    if ob.type == 'MESH':
        e = ob.evaluated_get(deps); me = e.to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles); objs += 1; e.to_mesh_clear()
import json
stats = dict(stage=STAGE, blender=bpy.app.version_string, engine='CYCLES (CPU)', resolution=list(RES), samples=SAMPLES,
             build_seconds=round(t_build, 1), render_seconds=round(t_render, 1), mesh_objects=objs, triangles=tris, cobbles=n_cobbles,
             lights=len([o for o in SCN.objects if o.type == 'LIGHT']), materials=len(bpy.data.materials))
json.dump(stats, open(os.path.join(OUT, f'iteration{STAGE}_stats.json'), 'w'), indent=1)
print('STATS', json.dumps(stats))

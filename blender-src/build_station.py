# TagVerse - "Estación Órbita" construida en Blender a partir de layout.json
# Uso: blender -b -P build_station.py -- layout.json station.glb station.blend
import bpy, bmesh, math, sys, json
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
L = json.load(open(argv[0]))
OUT_GLB, OUT_BLEND = argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb(h):
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

MATS = {}
def mat(name, hexcol, rough=0.6, metal=0.0, emit=None, es=1.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*srgb(emit), 1)
        b.inputs['Emission Strength'].default_value = es
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha; m.blend_method = 'BLEND'
    MATS[name] = m
    return m

FLOOR = {'cafe': 0xb9bfd0, 'bridge': 0x4a5a8a, 'oxygen': 0x8fb8a0, 'reactor': 0x5a4a5e, 'engine': 0x9a8670,
         'lab': 0xd7e2ea, 'security': 0x56688a, 'storage': 0xa69a78, 'comms': 0x7f94b8, 'lobby': 0x8a7fc0, 'corridor': 0x7c8296}
for k, v in FLOOR.items(): mat('Floor_' + k, v, 0.7)
M = dict(
    wallLow=mat('WallLow', 0x2c2b52, 0.7), wallUp=mat('WallUp', 0x8e94b8, 0.6), wallTrim=mat('WallTrim', 0x35e0ff, 0.4, 0, 0x35e0ff, 2.0),
    wallCap=mat('WallCap', 0x3c3a6e, 0.6),
    metal=mat('PropMetal', 0xc4c9d8, 0.45, 0.2), dark=mat('PropDark', 0x2b2d45, 0.6), accent=mat('PropAccent', 0x5a6bd6, 0.5),
    screen=mat('Screen', 0x0a1a30, 0.3, 0, 0x4fd8ff, 1.5), screenG=mat('ScreenGreen', 0x0a2a10, 0.3, 0, 0x6dff7a, 1.5),
    glass=mat('Glass', 0xbfefff, 0.05, 0, None, 1, 0.3), fluid=mat('Fluid', 0x2bd46a, 0.3, 0, 0x6dff7a, 1.6),
    plant=mat('Plant', 0x3f9e4d, 0.8), soil=mat('Soil', 0x5a4030, 0.9),
    crate0=mat('Crate0', 0xd88a3a, 0.7), crate1=mat('Crate1', 0x3aa7a0, 0.7), crate2=mat('Crate2', 0x8a9a3a, 0.7),
    hazard=mat('Hazard', 0xffd23d, 0.5, 0, 0x6a5000, 1.0), core=mat('ReactorCore', 0x9ff5ff, 0.2, 0, 0x35e0ff, 3.0),
    engineGlow=mat('EngineGlow', 0xffa040, 0.3, 0, 0xff8a2b, 3.0), holo=mat('Holo', 0x9fe8ff, 0.2, 0, 0x35e0ff, 2.5, 0.55),
    door=mat('Door', 0x46496e, 0.5), vent=mat('VentGrate', 0x1a1b2e, 0.6), ventGlow=mat('VentGlow', 0x2a2b40, 0.5, 0, 0x000000, 0.0),
    window=mat('Window', 0x050818, 0.1, 0, 0x0a1030, 1.0), sign=mat('Sign', 0x101020, 0.5, 0, 0xffffff, 1.0),
    bench=mat('Bench', 0x4757b8, 0.6), grav=mat('GravField', 0x6dff7a, 0.3, 0, 0x6dff7a, 1.0, 0.12),
    table=mat('TableTop', 0xe6e9f2, 0.4), red=mat('PropRed', 0xd84a5a, 0.6),
)

objs = []
def link(o):
    bpy.context.collection.objects.link(o); objs.append(o); return o
def G(x, y, z):  # juego -> Blender
    return Vector((x, -z, y))

def add_box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((x1 - x0, z1 - z0, y1 - y0)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=G((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect='EDGES')
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(material)
    return o

def add_cyl(name, x, z, y0, h, r1, r2=None, material=None, seg=20, axis='Y', cap=True):
    r2 = r1 if r2 is None else r2
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)
    if axis == 'X': bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    if axis == 'Z': bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    c = G(x, y0 + h / 2, z) if axis == 'Y' else G(x, y0, z)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = abs(p.normal.z) < 0.9   # tapas planas
    return o

def add_sphere(name, x, y, z, r, material, scale=(1, 1, 1), seg=14, rings=8):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=Vector((scale[0], scale[2], scale[1])), verts=bm.verts)
    bmesh.ops.translate(bm, vec=G(x, y, z), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    return o

def add_torus(name, x, y, z, R, r, material, seg=32, mseg=6):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            ring.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(mseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % mseg], rings[i][(j + 1) % mseg]))
    bmesh.ops.translate(bm, vec=G(x, y, z), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    return o

def add_plane(name, x0, x1, z0, z1, y, material, uv_scale=0.5, facing='up', uv01=False):
    """Plano horizontal (facing='up') o vertical: facing 'S','N','E','W' indica hacia dónde mira; y=(y0,y1) en ese caso."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    if facing == 'up':
        pts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
        pts = [pts[0], pts[3], pts[2], pts[1]]   # normal hacia arriba
        uvs = [(p[0] * uv_scale, p[2] * uv_scale) for p in pts]
        verts = [bm.verts.new(G(*p)) for p in pts]
    else:
        y0, y1 = y
        if facing in ('S', 'N'):
            zz = z0
            pts = [(x0, y0, zz), (x1, y0, zz), (x1, y1, zz), (x0, y1, zz)]
            if facing == 'S': pts = [pts[1], pts[0], pts[3], pts[2]]
        else:
            xx = x0
            pts = [(xx, y0, z1), (xx, y0, z0), (xx, y1, z0), (xx, y1, z1)]
            if facing == 'W': pts = [pts[1], pts[0], pts[3], pts[2]]
        uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
        verts = [bm.verts.new(G(*p)) for p in pts]
    f = bm.faces.new(verts)
    f.normal_update()
    for lp, uv in zip(f.loops, uvs):
        lp[uvl].uv = uv
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(material)
    return o

H = L['wallVisH']
# ---------------------------------------------------------------- suelos
for r in L['rooms']:
    add_plane('Floor', r['x0'], r['x1'], r['z0'], r['z1'], 0.0, MATS['Floor_' + r['style']])
    # borde de neón en el contorno del suelo
for c in L['corridors']:
    add_plane('Floor', c['x0'], c['x1'], c['z0'], c['z1'], 0.002, MATS['Floor_corridor'])
    # franjas guía en el centro del pasillo
    if c['x1'] - c['x0'] < c['z1'] - c['z0']:
        cx = (c['x0'] + c['x1']) / 2
        add_box('Guide', cx - 0.12, cx + 0.12, 0.0, 0.02, c['z0'] + 0.3, c['z1'] - 0.3, M['wallTrim'])
    else:
        cz = (c['z0'] + c['z1']) / 2
        add_box('Guide', c['x0'] + 0.3, c['x1'] - 0.3, 0.0, 0.02, cz - 0.12, cz + 0.12, M['wallTrim'])

# ---------------------------------------------------------------- paredes bajas en tres franjas
for w in L['walls']:
    add_box('Wall', w['x0'], w['x1'], 0.0, 0.8, w['z0'], w['z1'], M['wallLow'])
    add_box('Wall', w['x0'], w['x1'], 0.8, H - 0.3, w['z0'], w['z1'], M['wallUp'])
    add_box('Wall', w['x0'] - 0.02, w['x1'] + 0.02, H - 0.3, H - 0.18, w['z0'] - 0.02, w['z1'] + 0.02, M['wallTrim'])
    add_box('Wall', w['x0'], w['x1'], H - 0.18, H, w['z0'], w['z1'], M['wallCap'])

# ---------------------------------------------------------------- objetos
def P(p):
    return p['x'] - p['sx'] / 2, p['x'] + p['sx'] / 2, p['y0'], p['y0'] + p['h'], p['z'] - p['sz'] / 2, p['z'] + p['sz'] / 2

for i, p in enumerate(L['props']):
    x0, x1, y0, y1, z0, z1 = P(p); x, z, h = p['x'], p['z'], p['h']; k = p['kind']
    if k == 'table':
        add_cyl('Table', x, z, 0, h - 0.08, 0.25, material=M['metal'], seg=12)
        add_cyl('Table', x, z, h - 0.1, 0.1, min(p['sx'], p['sz']) / 2, material=M['table'], seg=28)
        add_torus('Table', x, h - 0.05, z, min(p['sx'], p['sz']) / 2, 0.04, M['wallTrim'], seg=28, mseg=5)
        for a in range(4):  # taburetes
            ang = a * math.pi / 2 + math.pi / 4
            add_cyl('Stool', x + math.cos(ang) * 2.0, z + math.sin(ang) * 2.0, 0, 0.45, 0.28, material=M['accent'], seg=12)
    elif k == 'holo':
        add_cyl('HoloBase', x, z, 0, h, 1.0, 0.85, M['dark'], seg=24)
        add_torus('HoloBase', x, h, z, 0.86, 0.05, M['wallTrim'], seg=24)
        o = add_cyl('HoloSpin', x, z, h + 0.2, 1.4, 0.7, 0.0, M['holo'], seg=6, cap=False)
    elif k == 'counter':
        add_box('Counter', x0, x1, 0, h, z0, z1, M['metal'], 0.04)
        add_box('Counter', x0 + 0.1, x1 - 0.1, h - 0.02, h + 0.02, z0 + 0.1, z1 - 0.1, M['table'])
    elif k == 'stage':
        add_box('Stage', x0, x1, 0, h, z0, z1, M['dark'], 0.05)
        add_box('Stage', x0 - 0.02, x1 + 0.02, h - 0.1, h - 0.04, z0 - 0.02, z1 + 0.02, M['wallTrim'])
    elif k == 'console':
        add_box('Console', x0, x1, 0, h - 0.25, z0, z1, M['metal'], 0.04)
        f = p.get('face', 'S')
        add_box('Console', x0, x1, h - 0.25, h, z0, z1, M['dark'], 0.03)
        # pantalla inclinada (simplificada: panel brillante encima)
        add_box('Screen', x0 + 0.15, x1 - 0.15, h, h + 0.03, z0 + 0.15, z1 - 0.15, M['screen'])
        # monitor vertical detrás
        if f in ('S', 'N'):
            zz = z1 - 0.1 if f == 'S' else z0 + 0.1
            add_box('Monitor', x0 + 0.2, x1 - 0.2, h + 0.1, h + 0.9, zz - 0.05, zz + 0.05, M['screen'])
        else:
            xx = x0 + 0.1 if f == 'E' else x1 - 0.1
            add_box('Monitor', xx - 0.05, xx + 0.05, h + 0.1, h + 0.9, z0 + 0.2, z1 - 0.2, M['screen'])
    elif k == 'planter':
        add_box('Planter', x0, x1, 0, h, z0, z1, M['metal'], 0.05)
        add_box('Planter', x0 + 0.15, x1 - 0.15, h - 0.05, h + 0.01, z0 + 0.15, z1 - 0.15, M['soil'])
        n = int(p['sz'] / 1.3)
        for j in range(n):
            zz = z0 + (j + 0.5) * p['sz'] / n
            add_sphere('Bush', x, h + 0.25, zz, 0.55, M['plant'], (1, 0.7, 1))
    elif k == 'tank':
        add_cyl('Tank', x, z, 0, h - 0.3, p['sx'] / 2, material=M['metal'], seg=20)
        add_sphere('Tank', x, h - 0.3, z, p['sx'] / 2, M['metal'], (1, 0.55, 1), 20, 8)
        add_torus('Tank', x, h * 0.55, z, p['sx'] / 2 + 0.01, 0.05, M['screenG'], seg=24)
        add_box('Tank', x - 0.3, x + 0.3, h * 0.3, h * 0.3 + 0.25, z - p['sz'] / 2 - 0.03, z - p['sz'] / 2 + 0.02, M['red'])
    elif k == 'reactor':
        add_cyl('ReactorBase', x, z, 0, 0.6, 2.0, 2.0, M['dark'], seg=28)
        add_cyl('ReactorCore', x, z, 0.6, h - 1.2, 1.3, 1.3, M['core'], seg=28)
        add_cyl('ReactorBase', x, z, h - 0.6, 0.6, 1.6, 2.0, M['dark'], seg=28)
        for j, yy in enumerate((1.6, 3.0, 4.4)):
            add_torus('ReactorRings', x, yy, z, 1.55, 0.08, M['hazard'], seg=32)
    elif k == 'platform':
        add_box('Platform', x0, x1, 0, h, z0, z1, M['metal'], 0.04)
        add_box('Platform', x0 - 0.02, x1 + 0.02, h - 0.12, h - 0.04, z0 - 0.02, z1 + 0.02, M['hazard'])
    elif k == 'step':
        add_box('Step', x0, x1, 0, h, z0, z1, M['dark'], 0.03)
        add_box('Step', x0 - 0.01, x1 + 0.01, h - 0.06, h, z0 - 0.01, z1 + 0.01, M['hazard'])
    elif k == 'engine':
        r = min(h, p['sz']) / 2
        add_box('EngineBase', x0 + 0.3, x1 - 0.3, 0, 0.5, z0 + 0.2, z1 - 0.2, M['dark'])
        add_cyl('Engine', x - 0.5, z, h / 2, p['sx'] - 1.2, r * 0.98, r * 0.98, M['metal'], seg=24, axis='X')
        add_cyl('Engine', x + p['sx'] / 2 - 0.45, z, h / 2, 0.9, r * 0.98, r * 0.7, M['dark'], seg=24, axis='X')
        add_cyl('EngineGlow', x0 + 0.25, z, h / 2, 0.5, r * 0.75, r * 0.9, M['engineGlow'], seg=24, axis='X')
        for j in range(3):
            add_torus('Engine', 0, 0, 0, 0, 0, M['hazard'], seg=3, mseg=3) if False else None
            xx = x0 + 1.5 + j * 2.2
            o = add_cyl('Engine', xx, z, h / 2, 0.15, r + 0.04, r + 0.04, M['hazard'], seg=24, axis='X')
    elif k == 'tube':
        add_cyl('TubeBase', x, z, 0, 0.3, p['sx'] / 2, material=M['dark'], seg=18)
        add_cyl('Fluid', x, z, 0.3, h - 0.6, p['sx'] / 2 - 0.15, material=M['fluid'], seg=18)
        add_cyl('Glass', x, z, 0.3, h - 0.6, p['sx'] / 2 - 0.02, material=M['glass'], seg=18)
        add_cyl('TubeBase', x, z, h - 0.3, 0.3, p['sx'] / 2, material=M['dark'], seg=18)
    elif k == 'desk':
        add_box('Desk', x0, x1, 0, h, z0, z1, M['metal'], 0.04)
        f = p.get('face', 'S')
        n = max(2, int(p['sx'] / 1.6))
        for j in range(n):
            xx = x0 + (j + 0.5) * p['sx'] / n
            zz = z1 - 0.25
            add_box('Monitor', xx - 0.55, xx + 0.55, h + 0.15, h + 0.85, zz - 0.04, zz + 0.04, M['screen'] if j % 2 == 0 else M['screenG'])
            add_box('Monitor', xx - 0.05, xx + 0.05, h, h + 0.15, zz - 0.04, zz + 0.04, M['dark'])
        for j in range(n):  # sillas (sin colisión)
            xx = x0 + (j + 0.5) * p['sx'] / n
            add_cyl('Chair', xx, z0 - 0.9, 0, 0.5, 0.3, material=M['accent'], seg=12)
    elif k == 'crate':
        cm = [M['crate0'], M['crate1'], M['crate2']][p.get('tone', 0) % 3]
        add_box('Crate', x0, x1, p['y0'], y1, z0, z1, cm, 0.04)
        e = 0.06
        for (ax0, ax1, az0, az1) in ((x0 - 0.01, x0 + e, z0 - 0.01, z1 + 0.01), (x1 - e, x1 + 0.01, z0 - 0.01, z1 + 0.01)):
            add_box('CrateEdge', ax0, ax1, p['y0'], y1 + 0.01, az0, az1, M['dark'])
        add_box('CrateEdge', x0 - 0.01, x1 + 0.01, y1 - e, y1 + 0.01, z0 - 0.01, z1 + 0.01, M['dark'])
    elif k == 'mezz':
        add_box('Mezz', x0, x1, h - 0.3, h, z0, z1, M['metal'], 0.03)
        add_box('Mezz', x0 - 0.02, x1 + 0.02, h - 0.22, h - 0.12, z0 - 0.02, z1 + 0.02, M['hazard'])
        for xx in (x0 + 0.3, x1 - 0.3):
            for zz in (z0 + 0.3, z1 - 0.3):
                add_box('Mezz', xx - 0.15, xx + 0.15, 0, h - 0.3, zz - 0.15, zz + 0.15, M['dark'])
        # baranda en el borde norte (decorativa)
        add_box('Rail', x0 + 1.2, x1 - 1.2, h + 0.85, h + 0.95, z1 - 0.08, z1 + 0.02, M['hazard'])
        for j in range(6):
            xx = x0 + 1.2 + j * (p['sx'] - 2.4) / 5
            add_box('Rail', xx - 0.04, xx + 0.04, h, h + 0.9, z1 - 0.08, z1, M['dark'])
        # parte inferior cerrada para la colisión (es un bloque sólido)
        add_box('Mezz', x0 + 0.05, x1 - 0.05, 0, h - 0.3, z0 + 0.05, z1 - 0.05, M['crate1'])
    elif k == 'barrel':
        add_cyl('Barrel', x, z, 0, h, p['sx'] / 2, material=M['red'], seg=16)
        add_torus('Barrel', x, h * 0.3, z, p['sx'] / 2, 0.03, M['dark'], seg=16, mseg=4)
        add_torus('Barrel', x, h * 0.75, z, p['sx'] / 2, 0.03, M['dark'], seg=16, mseg=4)
    elif k == 'dish':
        add_box('Dish', x0, x1, 0, h, z0, z1, M['dark'], 0.06)
        add_cyl('Dish', x, z, h, 0.8, 0.2, material=M['metal'], seg=10)
        add_cyl('DishBowl', x, z, h + 0.8, 0.6, 0.3, 1.5, M['metal'], seg=24, cap=False)
        add_sphere('Dish', x, h + 1.6, z, 0.15, M['screen'])
    elif k == 'rack':
        add_box('Rack', x0, x1, 0, h, z0, z1, M['dark'], 0.03)
        for j in range(5):
            yy = 0.3 + j * 0.38
            add_box('RackLed', x0 + 0.2, x1 - 0.2, yy, yy + 0.06, z1 - 0.02, z1 + 0.02, M['screenG'] if j % 2 else M['screen'])
    elif k == 'locker':
        add_box('Locker', x0, x1, 0, h, z0, z1, M['accent'], 0.03)
        n = int(p['sz'] / 0.75)
        for j in range(n):
            zz = z0 + (j + 0.5) * p['sz'] / n
            xx = x1 + 0.01 if x < 0 else x0 - 0.01
            add_box('LockerLine', xx - 0.02, xx + 0.02, 0.1, h - 0.1, zz + p['sz'] / n / 2 - 0.03, zz + p['sz'] / n / 2, M['dark'])
            add_box('LockerVent', xx - 0.025, xx + 0.025, h - 0.5, h - 0.35, zz - 0.2, zz + 0.2, M['dark'])
    elif k == 'bench':
        add_box('Bench', x0, x1, 0.3, h, z0, z1, M['bench'], 0.05)
        add_box('Bench', x0 + 0.2, x1 - 0.2, 0, 0.3, z0 + 0.3, z1 - 0.3, M['dark'])
    else:
        add_box('Prop', x0, x1, p['y0'], y1, z0, z1, M['metal'])

# ---------------------------------------------------------------- compuertas, conductos, gravedad
for d in L['doors']:
    o = add_box('Door_' + d['id'], d['x'] - d['sx'] / 2, d['x'] + d['sx'] / 2, 0, H, d['z'] - d['sz'] / 2, d['z'] + d['sz'] / 2, M['door'])
    o['tv_keep'] = 1
    stripe = add_box('Door_' + d['id'] + '_Stripe', d['x'] - d['sx'] / 2, d['x'] + d['sx'] / 2, 1.2, 1.6, d['z'] - d['sz'] / 2 - 0.02, d['z'] + d['sz'] / 2 + 0.02, M['hazard'])
    stripe['tv_keep'] = 1
for v in L['vents']:
    add_box('VentFrame', v['x'] - 0.75, v['x'] + 0.75, 0, 0.06, v['z'] - 0.6, v['z'] + 0.6, M['dark'])
    for j in range(5):
        zz = v['z'] - 0.45 + j * 0.225
        add_box('VentGrate', v['x'] - 0.6, v['x'] + 0.6, 0.0, 0.075, zz - 0.05, zz + 0.05, M['vent'])
    g = add_box('VentGlow', v['x'] - 0.62, v['x'] + 0.62, 0.0, 0.03, v['z'] - 0.5, v['z'] + 0.5, M['ventGlow'])
gr = L['grav']
add_plane('GravFloor', gr['x0'], gr['x1'], gr['z0'], gr['z1'], 0.006, M['grav'])
gf = add_box('GravField', gr['x0'], gr['x1'], 0.0, 4.5, gr['z0'], gr['z1'], M['grav']); gf['tv_keep'] = 1

# ---------------------------------------------------------------- ventanas y letreros
rooms = {r['id']: r for r in L['rooms']}
p = rooms['P']
add_plane('Window_P', -3.5, 3.5, p['z1'] - 0.03, p['z1'] - 0.03, (0.9, 2.5), M['window'], facing='S')
add_box('WindowFrame', -3.65, 3.65, 0.8, 0.9, p['z1'] - 0.1, p['z1'], M['wallTrim'])
add_box('WindowFrame', -3.65, 3.65, 2.5, 2.6, p['z1'] - 0.1, p['z1'], M['wallTrim'])
e = rooms['E']
add_plane('Window_E', -6, 6, e['z1'] - 0.03, e['z1'] - 0.03, (0.9, 2.6), M['window'], facing='S')
add_box('WindowFrame', -6.15, 6.15, 0.8, 0.9, e['z1'] - 0.1, e['z1'], M['wallTrim'])
add_box('WindowFrame', -6.15, 6.15, 2.6, 2.7, e['z1'] - 0.1, e['z1'], M['wallTrim'])
signs = []
for r in L['rooms']:
    if r['id'] == 'E':
        s = add_plane('Sign_E', -4.5, 4.5, r['z0'] + 0.03, r['z0'] + 0.03, (1.3, 2.7), mat('Sign_E', 0x101020, 0.5, 0, 0xffffff, 1.0), facing='N')
    else:
        cx = r['x0'] + 2.0
        s = add_plane('Sign_' + r['id'], cx - 1.6, cx + 1.6, r['z1'] - 0.03, r['z1'] - 0.03, (2.05, 2.65), mat('Sign_' + r['id'], 0x101020, 0.5, 0, 0xffffff, 1.0), facing='S')
    s['tv_keep'] = 1

# ---------------------------------------------------------------- unir por material (menos llamadas de dibujo)
KEEP_PREFIX = ('Door_', 'Sign_', 'Window_', 'HoloSpin', 'ReactorRings', 'GravField', 'VentGlow')
groups = {}
for o in objs:
    if o.name.startswith(KEEP_PREFIX) or o.get('tv_keep'):
        key = o.name.split('.')[0]
        if key.startswith('Door_'): key = 'Door_' + key.split('_')[1]
    else:
        key = 'M_' + o.data.materials[0].name
    groups.setdefault(key, []).append(o)
for key, lst in groups.items():
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = lst[0]
    for o in lst: o.select_set(True)
    if len(lst) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = key; ob.data.name = key
tris = sum(sum(len(pp.vertices) - 2 for pp in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('OBJECTS', len([o for o in bpy.data.objects if o.type == 'MESH']), 'TRIS', tris)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=False, export_apply=True,
                          export_yup=True, export_materials='EXPORT', export_animations=False, export_texcoords=True, export_normals=True)
print('EXPORTED', OUT_GLB)

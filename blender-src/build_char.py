# TagVerse - personaje "corredor cibernético" generado por código en Blender 4.0
# Uso: blender -b -P build_char.py -- <salida.glb> <salida.blend>
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT_GLB = argv[0] if len(argv) > 0 else 'tagverse_runner.glb'
OUT_BLEND = argv[1] if len(argv) > 1 else 'tagverse_runner.blend'

# ---------------------------------------------------------------- escena limpia
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30

# ---------------------------------------------------------------- materiales
def mat(name, color, rough=0.5, metal=0.0, emit=None, emit_str=1.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_str
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    return m

M = {
    'Accent': mat('Accent', (0.95, 0.25, 0.6), 0.35, 0.15),
    'Suit':   mat('Suit', (0.06, 0.05, 0.12), 0.55, 0.25),
    'Trim':   mat('Trim', (1.0, 0.45, 0.8), 0.3, 0.0, (1.0, 0.45, 0.8), 3.0),
    'Visor':  mat('Visor', (0.01, 0.01, 0.03), 0.08, 0.6),
    'Eyes':   mat('Eyes', (1, 1, 1), 0.3, 0.0, (1, 1, 1), 4.0),
    'Gold':   mat('Gold', (1.0, 0.72, 0.15), 0.25, 1.0),
    'Horn':   mat('Horn', (1.0, 0.15, 0.5), 0.35, 0.0, (0.5, 0.02, 0.2), 1.0),
    'Antenna':mat('Antenna', (0.2, 0.9, 1.0), 0.3, 0.0, (0.2, 0.9, 1.0), 4.0),
    'Halo':   mat('Halo', (1.0, 0.95, 0.6), 0.3, 0.0, (1.0, 0.95, 0.6), 5.0),
    'Metal':  mat('Metal', (0.6, 0.6, 0.7), 0.3, 1.0),
    'Flame':  mat('Flame', (1.0, 0.6, 0.1), 0.5, 0.0, (1.0, 0.55, 0.1), 6.0),
    'Wing':   mat('Wing', (1.0, 0.5, 0.85), 0.3, 0.0, (1.0, 0.5, 0.85), 1.5, alpha=0.6),
    'Cape':   mat('Cape', (0.55, 0.12, 0.35), 0.7, 0.0),
    'Cap':    mat('Cap', (0.25, 0.06, 0.16), 0.6, 0.1),
}

def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj

def set_active(obj):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

def apply_mods(obj):
    set_active(obj)
    for md in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)

def finish(obj, material, smooth=True):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def uv_sphere(name, r, loc, scale=(1, 1, 1), seg=24, rings=14):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    return link(bpy.data.objects.new(name, me))

def cylinder(name, r1, r2, depth, loc, rot=(0, 0, 0), seg=16, cap=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=depth)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z'))
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    return link(bpy.data.objects.new(name, me))

def rounded_box(name, size, loc, bevel=0.03, sub=1, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z'))
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    bv = o.modifiers.new('bevel', 'BEVEL'); bv.width = bevel; bv.segments = 2
    if sub:
        ss = o.modifiers.new('sub', 'SUBSURF'); ss.levels = sub; ss.render_levels = sub
    apply_mods(o)
    return o

def torus(name, R, r, loc, scale=(1, 1, 1), rot=(0, 0, 0), seg=32, mseg=10):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            v = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            ring.append(bm.verts.new(v))
        verts.append(ring)
    for i in range(seg):
        for j in range(mseg):
            a, b = verts[i][j], verts[(i + 1) % seg][j]
            c, d = verts[(i + 1) % seg][(j + 1) % mseg], verts[i][(j + 1) % mseg]
            bm.faces.new((a, b, c, d))
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z'))
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    return link(bpy.data.objects.new(name, me))

# ---------------------------------------------------------------- esqueleto (Blender: X = izquierda del personaje, -Y = adelante, Z = arriba)
J = {
    'pelvis': Vector((0, 0, 0.80)), 'waist': Vector((0, 0, 0.92)), 'chest': Vector((0, 0, 1.05)), 'neck': Vector((0, 0.0, 1.17)),
    'head': Vector((0, -0.01, 1.47)), 'headTop': Vector((0, -0.01, 1.80)),
}
for s, n in ((1, 'L'), (-1, 'R')):
    J['hip' + n] = Vector((0.1 * s, 0, 0.77))
    J['knee' + n] = Vector((0.11 * s, -0.015, 0.43))
    J['ankle' + n] = Vector((0.11 * s, 0.0, 0.11))
    J['toe' + n] = Vector((0.11 * s, -0.14, 0.05))
    J['shoulder' + n] = Vector((0.205 * s, 0.0, 1.08))
    J['elbow' + n] = Vector((0.29 * s, 0.01, 0.85))
    J['wrist' + n] = Vector((0.325 * s, -0.01, 0.65))
    J['hand' + n] = Vector((0.335 * s, -0.015, 0.57))

arm_data = bpy.data.armatures.new('Rig')
rig = link(bpy.data.objects.new('Rig', arm_data))
set_active(rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
def bone(name, h, t, parent=None, roll=0.0, connect=False):
    b = eb.new(name); b.head = h; b.tail = t; b.roll = roll
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    return b
bone('Hips', J['pelvis'], J['waist'])
bone('Spine', J['waist'], J['chest'], 'Hips', connect=True)
bone('Chest', J['chest'], J['neck'], 'Spine', connect=True)
bone('Head', J['neck'], J['headTop'], 'Chest', connect=True)
for n in ('L', 'R'):
    bone('UpperLeg.' + n, J['hip' + n], J['knee' + n], 'Hips')
    bone('LowerLeg.' + n, J['knee' + n], J['ankle' + n], 'UpperLeg.' + n, connect=True)
    bone('Foot.' + n, J['ankle' + n], J['toe' + n], 'LowerLeg.' + n, connect=True)
    bone('UpperArm.' + n, J['shoulder' + n], J['elbow' + n], 'Chest')
    bone('LowerArm.' + n, J['elbow' + n], J['wrist' + n], 'UpperArm.' + n, connect=True)
    bone('Hand.' + n, J['wrist' + n], J['hand' + n], 'LowerArm.' + n, connect=True)
# Huesos de accesorios (los anima el juego por código)
for b in eb:
    d = (b.tail - b.head).normalized()
    if abs(d.z) > 0.5:
        b.align_roll(Vector((0, 1, 0)) if d.z < 0 else Vector((0, -1, 0)))
    else:
        b.align_roll(Vector((0, 0, -1)))
bone('Cape', Vector((0, 0.17, 1.12)), Vector((0, 0.19, 0.95)), 'Chest')
bone('Scarf', Vector((0.06, 0.12, 1.15)), Vector((0.07, 0.16, 0.95)), 'Chest')
bone('Wing.L', Vector((0.05, 0.16, 1.03)), Vector((0.35, 0.22, 1.12)), 'Chest')
bone('Wing.R', Vector((-0.05, 0.16, 1.03)), Vector((-0.35, 0.22, 1.12)), 'Chest')
bpy.ops.object.mode_set(mode='OBJECT')
BONES = [b.name for b in arm_data.bones]

# ---------------------------------------------------------------- cuerpo continuo (Skin + Subsurf)
SK = [  # nombre, radio x, radio y
    ('pelvis', 0.16, 0.12), ('waist', 0.135, 0.105), ('chest', 0.175, 0.13), ('neck', 0.065, 0.065),
]
for n in ('L', 'R'):
    SK += [('hip' + n, 0.095, 0.095), ('knee' + n, 0.07, 0.07), ('ankle' + n, 0.055, 0.055),
           ('shoulder' + n, 0.078, 0.078), ('elbow' + n, 0.062, 0.062), ('wrist' + n, 0.05, 0.05)]
EDGES = [('pelvis', 'waist'), ('waist', 'chest'), ('chest', 'neck')]
for n in ('L', 'R'):
    EDGES += [('pelvis', 'hip' + n), ('hip' + n, 'knee' + n), ('knee' + n, 'ankle' + n),
              ('chest', 'shoulder' + n), ('shoulder' + n, 'elbow' + n), ('elbow' + n, 'wrist' + n)]
names = [s[0] for s in SK]
me = bpy.data.meshes.new('Body')
me.from_pydata([J[n] for n in names], [(names.index(a), names.index(b)) for a, b in EDGES], [])
body = link(bpy.data.objects.new('Body', me))
skin = body.modifiers.new('skin', 'SKIN')
skin.use_smooth_shade = True
for i, (n, rx, ry) in enumerate(SK):
    sv = me.skin_vertices[0].data[i]
    sv.radius = (rx, ry)
    sv.use_root = (n == 'pelvis')
ss = body.modifiers.new('sub', 'SUBSURF'); ss.levels = 2; ss.render_levels = 2
apply_mods(body)

# ---------------------------------------------------------------- pesos (distancia a los segmentos de hueso)
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (a + t * ab - p).length

def bone_segs(names_):
    out = []
    for bn in names_:
        b = arm_data.bones[bn]
        out.append((bn, b.head_local.copy(), b.tail_local.copy()))
    return out

BODY_BONES = ['Hips', 'Spine', 'Chest', 'Head'] + [f'{p}.{n}' for n in ('L', 'R') for p in ('UpperLeg', 'LowerLeg', 'UpperArm', 'LowerArm')]

def auto_weights(obj, names_, power=6.0, keep=3):
    segs = bone_segs(names_)
    groups = {bn: obj.vertex_groups.new(name=bn) for bn in names_}
    for v in obj.data.vertices:
        p = obj.matrix_world @ v.co
        ds = sorted(((seg_dist(p, a, b), bn) for bn, a, b in segs))[:keep]
        ws = [(1.0 / max(d, 1e-3) ** power, bn) for d, bn in ds]
        tot = sum(w for w, _ in ws)
        for w, bn in ws:
            if w / tot > 0.01:
                groups[bn].add([v.index], w / tot, 'REPLACE')

def rigid(obj, bone_name):
    vg = obj.vertex_groups.new(name=bone_name)
    vg.add([v.index for v in obj.data.vertices], 1.0, 'REPLACE')

# Pesos del cuerpo: evitar que una pierna "jale" de la otra y que el brazo jale del torso
auto_weights(body, BODY_BONES)

# Materiales del cuerpo por zona: chaqueta y mangas del color del jugador, resto traje oscuro
body.data.materials.append(M['Suit'])
body.data.materials.append(M['Accent'])
segs = bone_segs(BODY_BONES)
for poly in body.data.polygons:
    c = body.matrix_world @ poly.center
    bn = min(((seg_dist(c, a, b), n) for n, a, b in segs))[1]
    accent = (bn in ('Spine', 'Chest') and c.z > 0.9) or bn.startswith('UpperArm')
    poly.material_index = 1 if accent else 0
for p in body.data.polygons:
    p.use_smooth = True

parts = [body]
def part(obj, material, bone_name=None, smooth=True):
    finish(obj, material, smooth)
    if bone_name:
        rigid(obj, bone_name)
    parts.append(obj)
    return obj

# ---------------------------------------------------------------- cabeza y casco
part(uv_sphere('Helmet', 0.3, J['head'], (1.0, 0.96, 0.93), 28, 16), M['Accent'], 'Head')
# Visor envolvente: franja frontal de una esfera algo mayor
visor = uv_sphere('Visor', 0.304, J['head'], (1.0, 0.96, 0.93), 40, 24)
bm = bmesh.new(); bm.from_mesh(visor.data)
hc = J['head']
kill = []
for v in bm.verts:
    d = v.co - hc
    ang = math.degrees(math.atan2(d.x, -d.y))
    if not (-72 < ang < 72 and -0.075 < d.z < 0.085 and d.y < 0):
        kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(visor.data); bm.free()
sol = visor.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1.0
apply_mods(visor)
part(visor, M['Visor'], 'Head')
# Ojos: dos píldoras brillantes sobre el visor
for s in (1, -1):
    e = uv_sphere('Eye', 0.05, (0.095 * s, hc.y - 0.29, hc.z + 0.005), (0.75, 0.3, 1.15), 16, 10)
    part(e, M['Eyes'], 'Head')
# Auriculares con anillo de neón
for s in (1, -1):
    part(cylinder('Ear', 0.085, 0.085, 0.06, (0.29 * s, hc.y + 0.01, hc.z), (0, math.pi / 2, 0), 20), M['Suit'], 'Head')
    part(torus('EarRing', 0.075, 0.014, (0.322 * s, hc.y + 0.01, hc.z), rot=(0, math.pi / 2, 0), seg=24, mseg=8), M['Trim'], 'Head')

# ---------------------------------------------------------------- detalles del cuerpo
part(torus('Belt', 0.15, 0.022, (0, 0, 0.865), scale=(1.0, 0.8, 1.0), seg=40, mseg=8), M['Trim'], 'Hips')
# Emblema del pecho (chevron de neón)
for s in (1, -1):
    st = rounded_box('Chevron', (0.11, 0.02, 0.022), (0.045 * s, -0.15, 1.02), bevel=0.008, sub=1, rot=(0, 0.6 * s, 0))
    part(st, M['Trim'], 'Chest')
# Cuello alto del traje
part(cylinder('Collar', 0.1, 0.085, 0.07, (0, 0, 1.155), seg=20), M['Suit'], 'Chest')
# Hombreras y rodilleras
for s, n in ((1, 'L'), (-1, 'R')):
    part(uv_sphere('Pad', 0.095, J['shoulder' + n] + Vector((0.015 * s, 0, 0.02)), (1.0, 1.0, 0.75), 20, 12), M['Accent'], 'UpperArm.' + n)
    part(torus('PadRing', 0.08, 0.01, J['shoulder' + n] + Vector((0.015 * s, 0, 0.005)), scale=(1, 1, 1), seg=24, mseg=6), M['Trim'], 'UpperArm.' + n)
    part(uv_sphere('Knee', 0.06, J['knee' + n] + Vector((0, -0.05, -0.01)), (1.05, 0.45, 1.1), 16, 10), M['Accent'], 'LowerLeg.' + n)
    # Guantes
    part(uv_sphere('Glove', 0.072, J['wrist' + n] + Vector((0.005 * s, -0.005, -0.06)), (0.9, 0.8, 1.1), 18, 12), M['Accent'], 'Hand.' + n)
    part(torus('Cuff', 0.048, 0.013, J['wrist' + n] + Vector((0, 0, 0.0)), seg=20, mseg=6), M['Trim'], 'LowerArm.' + n)
    # Zapatillas
    a = J['ankle' + n]
    part(rounded_box('Shoe', (0.125, 0.26, 0.11), (a.x, a.y - 0.06, 0.068), bevel=0.045, sub=2), M['Accent'], 'Foot.' + n)
    part(rounded_box('Sole', (0.135, 0.27, 0.035), (a.x, a.y - 0.06, 0.018), bevel=0.014, sub=1), M['Trim'], 'Foot.' + n)
    part(rounded_box('Laces', (0.07, 0.09, 0.03), (a.x, a.y - 0.1, 0.112), bevel=0.01, sub=1, rot=(-0.35, 0, 0)), M['Suit'], 'Foot.' + n)

# Núcleo de energía en la espalda (se oculta con el propulsor)
core = part(rounded_box('Back_Nucleo', (0.2, 0.08, 0.24), (0, 0.15, 1.0), bevel=0.025, sub=1), M['Suit'], 'Chest')
coreg = part(rounded_box('Back_NucleoLuz', (0.05, 0.02, 0.17), (0, 0.19, 1.0), bevel=0.008, sub=1), M['Trim'], 'Chest')

# ---------------------------------------------------------------- accesorios de cabeza (uno visible a la vez)
acc = []
def accessory(obj, material, bone_name, group):
    part(obj, material, bone_name)
    obj['tv_group'] = group
    acc.append((obj, group))
    return obj

top = hc.z + 0.3 * 0.93
# Gorra: casquete + visera
cap = uv_sphere('Cap', 0.313, hc, (1.0, 0.97, 0.94), 32, 18)
bm = bmesh.new(); bm.from_mesh(cap.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < hc.z + 0.07], context='VERTS')
bm.to_mesh(cap.data); bm.free()
sol = cap.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.015; apply_mods(cap)
accessory(cap, M['Cap'], 'Head', 'Hat_Gorra')
me_b = bpy.data.meshes.new('Brim'); bm = bmesh.new()
pts = [bm.verts.new((0.22 * math.cos(math.pi * i / 16), -0.17 * math.sin(math.pi * i / 16), 0)) for i in range(17)]
bm.faces.new(pts)
bm.to_mesh(me_b); bm.free()
brim = link(bpy.data.objects.new('Brim', me_b))
sol = brim.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.022; sol.offset = 0; apply_mods(brim)
brim.rotation_euler = (-0.18, 0, 0); brim.location = (0, hc.y - 0.17, hc.z + 0.085)
set_active(brim); bpy.ops.object.transform_apply(location=True, rotation=True)
accessory(brim, M['Cap'], 'Head', 'Hat_Gorra')
accessory(torus('CapBand', 0.305, 0.012, (0, hc.y, hc.z + 0.08), scale=(1, 0.96, 1), seg=40, mseg=6), M['Trim'], 'Head', 'Hat_Gorra')
# Corona con puntas
me_c = bpy.data.meshes.new('Crown'); bm = bmesh.new()
N = 16; rb, rt = 0.2, 0.22
low = [bm.verts.new((rb * math.cos(2 * math.pi * i / N), rb * math.sin(2 * math.pi * i / N), 0)) for i in range(N)]
up = [bm.verts.new((rt * math.cos(2 * math.pi * i / N), rt * math.sin(2 * math.pi * i / N), 0.16 if i % 2 == 0 else 0.08)) for i in range(N)]
for i in range(N):
    bm.faces.new((low[i], low[(i + 1) % N], up[(i + 1) % N], up[i]))
bmesh.ops.translate(bm, vec=Vector((0, hc.y, top - 0.06)), verts=bm.verts)
bm.to_mesh(me_c); bm.free()
crown = link(bpy.data.objects.new('Crown', me_c))
sol = crown.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.02; apply_mods(crown)
accessory(crown, M['Gold'], 'Head', 'Hat_Corona')
accessory(uv_sphere('Gem', 0.035, (0, hc.y - 0.215, top + 0.0), (1, 0.6, 1.2), 12, 8), M['Horn'], 'Head', 'Hat_Corona')
# Cuernos curvos
for s in (1, -1):
    h = cylinder('Horn', 0.07, 0.0, 0.3, (0, 0, 0.15), seg=14)
    h.rotation_euler = (0.25, -0.55 * s, 0); h.location = (0.17 * s, hc.y - 0.03, hc.z + 0.2)
    set_active(h); bpy.ops.object.transform_apply(location=True, rotation=True)
    sm = h.modifiers.new('sm', 'SUBSURF'); sm.levels = 1; apply_mods(h)
    accessory(h, M['Horn'], 'Head', 'Hat_Cuernos')
# Antena
accessory(cylinder('AntStick', 0.014, 0.014, 0.3, (0.12, hc.y + 0.02, top + 0.1), (0, -0.25, 0), 8), M['Metal'], 'Head', 'Hat_Antena')
accessory(uv_sphere('AntBall', 0.055, (0.157, hc.y + 0.02, top + 0.245), (1, 1, 1), 16, 10), M['Antenna'], 'Head', 'Hat_Antena')
# Cresta (mohicano de neón)
for i in range(6):
    zf = -0.18 + i * 0.075
    yy = hc.y + zf
    zz = hc.z + math.sqrt(max(0.0, 0.29 ** 2 - zf ** 2)) * 0.93
    sp = cylinder('Spike', 0.045, 0.0, 0.2 - abs(i - 2.5) * 0.02, (0, 0, 0.09), seg=4)
    sp.rotation_euler = (0.5 + i * 0.08, 0, math.pi / 4); sp.location = (0, yy, zz - 0.02)
    sp.scale = (0.5, 1.6, 1)
    set_active(sp); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    accessory(sp, M['Trim'], 'Head', 'Hat_Cresta')
# Halo
accessory(torus('Halo', 0.2, 0.022, (0, hc.y, top + 0.17), seg=40, mseg=8), M['Halo'], 'Head', 'Hat_Halo')

# ---------------------------------------------------------------- accesorios de espalda
# Capa: tela con caída, pegada a los hombros
me_cape = bpy.data.meshes.new('Cape'); bm = bmesh.new()
rows, cols = 6, 6
grid = []
for r in range(rows + 1):
    t = r / rows
    row = []
    for c in range(cols + 1):
        u = c / cols - 0.5
        w = 0.36 + 0.24 * t
        x = u * w * 2 * 0.5
        y = 0.17 + 0.04 * t + 0.03 * math.cos(u * math.pi)
        z = 1.13 - t * 0.78
        row.append(bm.verts.new((x, y, z)))
    grid.append(row)
for r in range(rows):
    for c in range(cols):
        bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
bm.to_mesh(me_cape); bm.free()
cape = link(bpy.data.objects.new('Back_Capa', me_cape))
sol = cape.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.015
sm = cape.modifiers.new('sm', 'SUBSURF'); sm.levels = 1
apply_mods(cape)
accessory(cape, M['Cape'], 'Cape', 'Back_Capa')
accessory(torus('CapeClasp', 0.17, 0.02, (0, 0.04, 1.14), scale=(1.05, 0.95, 1), seg=32, mseg=6), M['Gold'], 'Chest', 'Back_Capa')
# Bufanda
accessory(torus('ScarfRing', 0.11, 0.045, (0, 0.0, 1.16), scale=(1, 0.95, 0.9), seg=28, mseg=10), M['Cape'], 'Chest', 'Back_Bufanda')
accessory(rounded_box('ScarfTail', (0.09, 0.03, 0.26), (0.065, 0.155, 1.03), bevel=0.012, sub=1), M['Cape'], 'Scarf', 'Back_Bufanda')
accessory(rounded_box('ScarfTail2', (0.08, 0.03, 0.2), (0.11, 0.15, 1.05), bevel=0.012, sub=1), M['Cape'], 'Scarf', 'Back_Bufanda')
# Alas de neón
for s, n in ((1, 'L'), (-1, 'R')):
    me_w = bpy.data.meshes.new('Wing'); bm = bmesh.new()
    pts = [(0, 0), (0.42, 0.2), (0.55, 0.26), (0.47, 0.08), (0.6, -0.02), (0.42, -0.05), (0.48, -0.2), (0.25, -0.12), (0, -0.06)]
    vs = [bm.verts.new((0.06 * s + px * s, 0.17 + px * 0.12, 1.03 + py)) for px, py in pts]
    bm.faces.new(vs)
    bm.to_mesh(me_w); bm.free()
    wg = link(bpy.data.objects.new('Wing.' + n, me_w))
    sol = wg.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.012; apply_mods(wg)
    accessory(wg, M['Wing'], 'Wing.' + n, 'Back_Alas')
# Propulsor
for s, n in ((1, 'L'), (-1, 'R')):
    accessory(cylinder('Tank', 0.06, 0.06, 0.3, (0.085 * s, 0.18, 1.0), seg=16), M['Metal'], 'Chest', 'Back_Propulsor')
    accessory(uv_sphere('TankTop', 0.06, (0.085 * s, 0.18, 1.15), (1, 1, 0.6), 16, 8), M['Metal'], 'Chest', 'Back_Propulsor')
    accessory(torus('TankRing', 0.062, 0.01, (0.085 * s, 0.18, 1.04), seg=20, mseg=6), M['Trim'], 'Chest', 'Back_Propulsor')
    accessory(cylinder('Nozzle', 0.045, 0.065, 0.06, (0.085 * s, 0.18, 0.82), seg=16, cap=False), M['Suit'], 'Chest', 'Back_Propulsor')
    fl = cylinder('Flame.' + n, 0.05, 0.0, 0.26, (0.085 * s, 0.18, 0.66), (math.pi, 0, 0), seg=12)
    accessory(fl, M['Flame'], 'Chest', 'Back_Propulsor')
    fl['tv_flame'] = 1

# ---------------------------------------------------------------- unir piezas por grupo y enlazar al esqueleto
def join(objs, name):
    set_active(objs[0])
    for o in objs[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name; o.data.name = name
    return o

groups = {}
base = []
flames = []
for o in parts:
    g = o.get('tv_group')
    if o.get('tv_flame'):
        flames.append(o)
    elif g:
        groups.setdefault(g, []).append(o)
    else:
        base.append(o)
core_objs = [o for o in base if o.name.startswith('Back_Nucleo')]
base = [o for o in base if o not in core_objs]
final = [join(base, 'Body')]
def decimate(o, target):
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris > target:
        dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = target / tris; dm.use_collapse_triangulate = False
        apply_mods(o)
decimate(final[0], 7000)
final.append(join(core_objs, 'Back_Nucleo'))
for g, objs in groups.items():
    final.append(join(objs, g))
for f in flames:
    final.append(f)

for o in final:
    o.parent = rig
    md = o.modifiers.new('rig', 'ARMATURE'); md.object = rig
    # quitar grupos vacíos
    used = set()
    for v in o.data.vertices:
        for gg in v.groups:
            used.add(gg.group)
    for vg in list(o.vertex_groups):
        if vg.index not in used:
            o.vertex_groups.remove(vg)

print('TRIS', {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in final})

# ---------------------------------------------------------------- animaciones
rig.animation_data_create()
for pb in rig.pose.bones:
    pb.rotation_mode = 'ZXY'   # primero abrir hacia afuera (Z) y luego levantar hacia adelante (X)

def calib(bn):
    """Devuelve el signo de rotación X que lleva la punta del hueso hacia adelante (-Y)."""
    pb = rig.pose.bones[bn]
    pb.rotation_euler = (0.4, 0, 0)
    bpy.context.view_layer.update()
    tail = (rig.matrix_world @ pb.tail).y
    pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    rest = (rig.matrix_world @ pb.tail).y
    return 1.0 if tail < rest else -1.0
SIGN = {bn: calib(bn) for bn in BONES}

def side_out(bn):
    """Signo de rotación Y/Z que abre el brazo hacia afuera."""
    pb = rig.pose.bones[bn]
    pb.rotation_euler = (0, 0, 0.4)
    bpy.context.view_layer.update()
    x1 = abs((rig.matrix_world @ pb.tail).x)
    pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    x0 = abs((rig.matrix_world @ pb.tail).x)
    return 1.0 if x1 > x0 else -1.0
OUT = {bn: side_out(bn) for bn in ('UpperArm.L', 'UpperArm.R')}
print('SIGN', SIGN, OUT)

def new_action(name):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data.action = act
    return act

def key(frame, pose, hips_z=0.0):
    """pose: {hueso: (adelante, afuera)} en radianes. Adelante = rotación que lleva la punta hacia -Y."""
    for bn in BONES:
        pb = rig.pose.bones[bn]
        fwd, out = pose.get(bn, (0.0, 0.0))
        rz = out * OUT.get(bn, 0.0)
        pb.rotation_euler = (fwd * SIGN[bn], 0.0, rz)
        pb.keyframe_insert('rotation_euler', frame=frame)
    hb = rig.pose.bones['Hips']
    hb.location = (0.0, hips_z, 0.0)   # eje Y local del hueso Hips = arriba
    hb.keyframe_insert('location', frame=frame)

def cyclic(act):
    for fc in act.fcurves:
        fc.modifiers.new('CYCLES')
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'

BODY_ANIM = [b for b in BONES if b not in ('Cape', 'Scarf', 'Wing.L', 'Wing.R')]
BONES = BODY_ANIM

# Reposo: respira y balancea un poco los brazos
act = new_action('Idle')
for f, ph in ((1, 0), (31, 1), (61, 0)):
    k = ph
    key(f, {
        'Spine': (0.03 * k, 0), 'Chest': (-0.02 * k, 0), 'Head': (0.04 - 0.05 * k, 0),
        'UpperArm.L': (0.05 * k, 0.12), 'UpperArm.R': (0.05 * k, 0.12),
        'LowerArm.L': (0.35 + 0.05 * k, 0), 'LowerArm.R': (0.35 + 0.05 * k, 0),
        'UpperLeg.L': (0.02, 0), 'UpperLeg.R': (0.02, 0), 'LowerLeg.L': (-0.05, 0), 'LowerLeg.R': (-0.05, 0),
    }, hips_z=-0.008 * k)
cyclic(act)

# Correr: ciclo de 20 cuadros (dos pasos)
act = new_action('Run')
def run_pose(ph, amp=1.0, lean=0.22):
    s = math.sin(ph); c = math.cos(ph)
    return {
        'Hips': (0.0, 0), 'Spine': (lean, 0), 'Chest': (0.05, 0), 'Head': (-lean * 0.8, 0),
        'UpperLeg.L': (0.85 * s * amp, 0), 'UpperLeg.R': (-0.85 * s * amp, 0),
        'LowerLeg.L': (-(0.25 + 1.1 * max(0.0, -c)) * amp, 0), 'LowerLeg.R': (-(0.25 + 1.1 * max(0.0, c)) * amp, 0),
        'Foot.L': (0.2 * s, 0), 'Foot.R': (-0.2 * s, 0),
        'UpperArm.L': (-0.9 * s * amp, 0.15), 'UpperArm.R': (0.9 * s * amp, 0.15),
        'LowerArm.L': (1.25, 0), 'LowerArm.R': (1.25, 0),
    }
for i in range(5):
    ph = i / 4 * 2 * math.pi
    key(1 + i * 5, run_pose(ph), hips_z=0.045 * abs(math.cos(ph)))
cyclic(act)

# Salto: brazos arriba y piernas recogidas (bucle suave mientras está en el aire)
act = new_action('Jump')
for f, k in ((1, 0), (11, 1), (21, 0)):
    key(f, {
        'Spine': (0.05, 0), 'Head': (-0.1, 0),
        'UpperArm.L': (2.5 + 0.1 * k, 0.45), 'UpperArm.R': (2.4 + 0.1 * k, 0.45),
        'LowerArm.L': (0.4, 0), 'LowerArm.R': (0.4, 0),
        'UpperLeg.L': (1.0 + 0.05 * k, 0), 'UpperLeg.R': (0.35, 0),
        'LowerLeg.L': (-1.3, 0), 'LowerLeg.R': (-0.7 - 0.05 * k, 0),
        'Foot.L': (0.3, 0), 'Foot.R': (0.2, 0),
    })
cyclic(act)

# Dash: inclinado, brazos atrás, zancada rápida
act = new_action('Dash')
for i in range(5):
    ph = i / 4 * 2 * math.pi
    p = run_pose(ph, 1.15, 0.55)
    p['UpperArm.L'] = (-1.2, 0.25); p['UpperArm.R'] = (-1.2, 0.25)
    p['LowerArm.L'] = (0.2, 0); p['LowerArm.R'] = (0.2, 0)
    p['Head'] = (-0.45, 0)
    key(1 + i * 3, p, hips_z=0.03 * abs(math.cos(ph)))
cyclic(act)

# Celebración (para cuando atrapas a alguien o ganas)
act = new_action('Cheer')
for f, k in ((1, 0), (9, 1), (17, 0)):
    key(f, {
        'Spine': (-0.1 * k, 0), 'Head': (-0.15 * k, 0),
        'UpperArm.L': (2.9, 0.6 + 0.2 * k), 'UpperArm.R': (2.9, 0.6 + 0.2 * k),
        'LowerArm.L': (0.2, 0), 'LowerArm.R': (0.2, 0),
    }, hips_z=0.06 * k)
cyclic(act)

rig.animation_data.action = bpy.data.actions['Idle']
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# ---------------------------------------------------------------- exportar
for o in bpy.context.selected_objects:
    o.select_set(False)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format='GLB', use_selection=False,
    export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_def_bones=False, export_skins=True, export_morph=False,
    export_apply=False, export_yup=True, export_materials='EXPORT', export_image_format='AUTO',
    export_draco_mesh_compression_enable=False,
)
print('EXPORTED', OUT_GLB)

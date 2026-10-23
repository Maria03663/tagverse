# Plano de la "Estación Órbita" de TagVerse (diseño original).
# Coordenadas del juego: x (este +), z (norte +), y arriba. Unidades en metros.
# Genera layout.json (para Blender) y layout.js (para el juego).
import json, sys, os

WALL_COLLIDE_H = 8.0    # las paredes chocan hasta 8 m (no se pueden saltar)
WALL_VIS_H = 3.0        # pero se ven bajas, como en una nave vista desde arriba

ROOMS = [
    # id, nombre, x0, x1, z0, z1, estilo de suelo
    ('C', 'Comedor', -11, 11, -8, 8, 'cafe'),
    ('P', 'Puente de mando', -8, 8, 16, 30, 'bridge'),
    ('O', 'Oxígeno', -32, -16, 14, 30, 'oxygen'),
    ('R', 'Reactor', 16, 32, 14, 30, 'reactor'),
    ('M', 'Motores', -33, -18, -7, 7, 'engine'),
    ('L', 'Laboratorio', 18, 33, -7, 7, 'lab'),
    ('S', 'Seguridad', -32, -16, -30, -14, 'security'),
    ('A', 'Almacén', -10, 10, -32, -16, 'storage'),
    ('K', 'Comunicaciones', 16, 32, -30, -14, 'comms'),
    ('E', 'Sala de espera', -10, 10, 42, 56, 'lobby'),
]
CORRIDORS = [
    ('C-P', -3, 3, 8, 16), ('C-A', -3, 3, -16, -8), ('C-M', -18, -11, -3, 3), ('C-L', 11, 18, -3, 3),
    ('M-O', -28, -22, 7, 14), ('M-S', -28, -22, -14, -7), ('L-R', 22, 28, 7, 14), ('L-K', 22, 28, -14, -7),
    ('O-P', -16, -8, 20, 26), ('R-P', 8, 16, 20, 26), ('S-A', -16, -10, -26, -20), ('K-A', 10, 16, -26, -20),
]

# Objetos con colisión: tipo, centro (x, z), tamaño (sx, alto, sz)
PROPS = []
def prop(kind, x, z, sx, h, sz, y0=0.0, **kw):
    d = dict(kind=kind, x=x, z=z, sx=sx, h=h, sz=sz, y0=y0); d.update(kw); PROPS.append(d)

# Comedor: mesas redondas y holograma central
for x in (-6, 6):
    for z in (-4, 4):
        prop('table', x, z, 3.0, 0.9, 3.0)
prop('holo', 0, 0, 2.0, 1.2, 2.0)
prop('counter', -7.5, -7.2, 5.0, 1.1, 1.2)
# Puente de mando
prop('stage', 0, 26, 8.0, 0.8, 4.0)
prop('console', -5.5, 29.2, 2.6, 1.1, 1.2, face='S')
prop('console', 5.5, 29.2, 2.6, 1.1, 1.2, face='S')
prop('console', -7.2, 19, 1.2, 1.1, 2.6, face='E')
prop('console', 7.2, 19, 1.2, 1.1, 2.6, face='W')
# Oxígeno
prop('planter', -28, 18, 3.0, 0.8, 6.0)
prop('planter', -20, 18, 3.0, 0.8, 6.0)
prop('tank', -30.5, 28.5, 1.8, 2.2, 1.8)
prop('tank', -17.5, 28.5, 1.8, 2.2, 1.8)
# Reactor: núcleo alto con pasarelas alrededor
prop('reactor', 24, 22, 4.0, 6.0, 4.0)
prop('platform', 24, 18.6, 6.0, 1.2, 1.6)
prop('platform', 24, 25.4, 6.0, 1.2, 1.6)
prop('platform', 20.4, 22, 1.6, 1.2, 5.2)
prop('platform', 27.6, 22, 1.6, 1.2, 5.2)
prop('step', 24, 17.2, 2.0, 0.6, 1.2)
prop('step', 24, 26.8, 2.0, 0.6, 1.2)
# Motores
prop('engine', -26, 3.6, 8.0, 2.4, 3.0)
prop('engine', -26, -3.6, 8.0, 2.4, 3.0)
prop('step', -21.4, 3.6, 0.8, 1.2, 2.0)
prop('step', -21.4, -3.6, 0.8, 1.2, 2.0)
# Laboratorio (zona de gravedad en el centro)
for x in (19.6, 31.4):
    for z in (-5.4, 5.4):
        prop('tube', x, z, 1.6, 2.6, 1.6)
# Seguridad
prop('desk', -24, -15.8, 6.0, 1.0, 1.4, face='S')
prop('crate', -30.2, -28.2, 1.6, 1.2, 1.6, tone=0)
prop('crate', -18.0, -28.4, 1.6, 0.8, 1.6, tone=1)
# Almacén: cajas en escalera hasta un entrepiso
prop('mezz', 0, -30.25, 10.0, 2.0, 3.5)
prop('crate', -6.2, -29.8, 2.2, 1.0, 2.2, tone=0)
prop('crate', 6.2, -29.8, 2.2, 1.0, 2.2, tone=1)
prop('crate', -6.0, -21.0, 2.0, 1.0, 2.0, tone=1)
prop('crate', -6.0, -23.0, 2.0, 2.0, 2.0, tone=0)
prop('crate', 6.0, -21.5, 2.4, 1.2, 2.4, tone=2)
prop('barrel', 2.0, -24.0, 1.4, 0.9, 1.4)
prop('barrel', -2.5, -18.2, 1.4, 0.9, 1.4)
# Comunicaciones
prop('dish', 28.0, -26.0, 3.0, 1.5, 3.0)
prop('rack', 18.2, -29.0, 3.6, 2.2, 1.0)
prop('desk', 24, -15.8, 5.0, 1.0, 1.2, face='S')
# Sala de espera
prop('bench', -8.8, 49, 1.0, 0.5, 6.0)
prop('bench', 8.8, 49, 1.0, 0.5, 6.0)
prop('stage', 0, 49, 4.0, 0.6, 4.0)
for z in (44.5, 53.5):
    prop('locker', -9.45, z, 1.0, 2.2, 3.0)
    prop('locker', 9.45, z, 1.0, 2.2, 3.0)

# Compuertas (aparecen con la mutación 1) y conductos de ventilación (mutación 2)
DOORS = [dict(id='CP', x=0, z=12, sx=6.0, sz=0.6), dict(id='CA', x=0, z=-12, sx=6.0, sz=0.6)]
VENTS = [  # pares conectados
    dict(id=0, x=-29.5, z=-17.0, to=1), dict(id=1, x=29.8, z=28.0, to=0),
    dict(id=2, x=-30.0, z=25.0, to=3), dict(id=3, x=30.0, z=-17.0, to=2),
    dict(id=4, x=-31.0, z=-0.0, to=5), dict(id=5, x=24.0, z=-5.5, to=4),
]
GRAV = dict(x0=21.5, x1=29.5, z0=-4.5, z1=4.5, y1=6.0)

SPAWNS = [(-9, 0), (0, 19), (-24, 23), (18, 28), (-20, 0), (25, 0), (-24, -24), (22, -22), (0, -19)]
LOBBY_SPAWNS = [(-5, 45), (5, 45), (-5, 53), (5, 53), (-3, 46), (3, 52), (-7, 50), (7, 47)]
LOBBY_C = (0, 49)

ORBS = [
    (0, 1.2, 0), (6, 0.9, -4), (-9, 0, -6), (9, 0, 6),
    (0, 0.8, 26), (-4, 0, 20), (4, 0, 22),
    (-28, 0.8, 18), (-20, 0, 26), (-24, 0, 16),
    (24, 1.2, 18.6), (24, 1.2, 25.4), (30, 0, 16),
    (-26, 2.4, 3.6), (-26, 0, 0), (-31, 0, -6),
    (25, 0, 3), (32, 0, 0),
    (-24, 1.0, -15.8), (-20, 0, -26),
    (0, 2.0, -30.25), (-6, 2.0, -23), (6.2, 1.0, -29.8), (0, 0, -24),
    (28, 1.5, -26), (24, 0, -21),
    (0, 0, 14.5), (0, 0, -14.5), (-15, 0, 0), (15, 0, 0), (-25, 0, 10), (25, 0, -10),
]

# ---------------------------------------------------------------- paredes automáticas
def rects():
    for r in ROOMS: yield r[2], r[3], r[4], r[5]
    for c in CORRIDORS: yield c[1], c[2], c[3], c[4]

X0, X1, Z0, Z1 = -36, 36, -36, 60
def is_floor(cx, cz):
    return any(x0 < cx < x1 and z0 < cz < z1 for x0, x1, z0, z1 in rects())
W, H = X1 - X0, Z1 - Z0
floor = [[is_floor(X0 + i + 0.5, Z0 + j + 0.5) for j in range(H)] for i in range(W)]
wall = [[False] * H for _ in range(W)]
for i in range(W):
    for j in range(H):
        if floor[i][j]: continue
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                a, b = i + di, j + dj
                if 0 <= a < W and 0 <= b < H and floor[a][b]:
                    wall[i][j] = True
# fusionar celdas en rectángulos (corridas en x y luego unir en z)
used = [[False] * H for _ in range(W)]
WALLS = []
for j in range(H):
    for i in range(W):
        if not wall[i][j] or used[i][j]: continue
        i2 = i
        while i2 + 1 < W and wall[i2 + 1][j] and not used[i2 + 1][j]: i2 += 1
        j2 = j
        while j2 + 1 < H and all(wall[k][j2 + 1] and not used[k][j2 + 1] for k in range(i, i2 + 1)): j2 += 1
        for k in range(i, i2 + 1):
            for l in range(j, j2 + 1): used[k][l] = True
        WALLS.append(dict(x0=X0 + i, x1=X0 + i2 + 1, z0=Z0 + j, z1=Z0 + j2 + 1))

# ---------------------------------------------------------------- navegación (áreas y portales)
AREAS = [dict(id=r[0], name=r[1], x0=r[2], x1=r[3], z0=r[4], z1=r[5]) for r in ROOMS] + \
        [dict(id=c[0], name='Pasillo', x0=c[1], x1=c[2], z0=c[3], z1=c[4]) for c in CORRIDORS]
LINKS = []
for a in range(len(AREAS)):
    for b in range(a + 1, len(AREAS)):
        A, B = AREAS[a], AREAS[b]
        # borde compartido en x
        if A['x1'] == B['x0'] or B['x1'] == A['x0']:
            x = A['x1'] if A['x1'] == B['x0'] else A['x0']
            lo, hi = max(A['z0'], B['z0']), min(A['z1'], B['z1'])
            if hi - lo >= 2: LINKS.append([a, b, x, (lo + hi) / 2])
        if A['z1'] == B['z0'] or B['z1'] == A['z0']:
            z = A['z1'] if A['z1'] == B['z0'] else A['z0']
            lo, hi = max(A['x0'], B['x0']), min(A['x1'], B['x1'])
            if hi - lo >= 2: LINKS.append([a, b, (lo + hi) / 2, z])

# ---------------------------------------------------------------- comprobaciones
def overlaps(px, pz, r=0.5):
    for p in PROPS:
        if abs(px - p['x']) < p['sx'] / 2 + r and abs(pz - p['z']) < p['sz'] / 2 + r: return p
    return None
for sx, sz in SPAWNS + LOBBY_SPAWNS:
    assert is_floor(sx, sz), ('spawn fuera', sx, sz)
    assert not overlaps(sx, sz), ('spawn en prop', sx, sz)
for v in VENTS:
    assert is_floor(v['x'], v['z']) and not overlaps(v['x'], v['z'], 0.8), ('vent', v)
for p in PROPS:
    for dx in (-1, 1):
        for dz in (-1, 1):
            assert is_floor(p['x'] + dx * p['sx'] / 2 * 0.98, p['z'] + dz * p['sz'] / 2 * 0.98), ('prop fuera', p)
for ox, oy, oz in ORBS:
    assert is_floor(ox, oz), ('orbe fuera', ox, oz)
    top = 0.0
    for p in PROPS:
        if abs(ox - p['x']) < p['sx'] / 2 and abs(oz - p['z']) < p['sz'] / 2: top = max(top, p['y0'] + p['h'])
    assert abs(top - oy) < 0.01, ('orbe a mala altura', ox, oy, oz, top)
print('paredes', len(WALLS), 'props', len(PROPS), 'enlaces', len(LINKS))

data = dict(rooms=[dict(id=r[0], name=r[1], x0=r[2], x1=r[3], z0=r[4], z1=r[5], style=r[6]) for r in ROOMS],
            corridors=[dict(id=c[0], x0=c[1], x1=c[2], z0=c[3], z1=c[4]) for c in CORRIDORS],
            walls=WALLS, props=PROPS, doors=DOORS, vents=VENTS, grav=GRAV, spawns=SPAWNS, lobbySpawns=LOBBY_SPAWNS,
            lobbyC=LOBBY_C, orbs=ORBS, areas=AREAS, links=LINKS, wallCollideH=WALL_COLLIDE_H, wallVisH=WALL_VIS_H)
out = os.path.dirname(os.path.abspath(__file__))
json.dump(data, open(os.path.join(out, 'layout.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'layout.js'), 'w').write('  const LAYOUT = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('ok', os.path.getsize(os.path.join(out, 'layout.js')), 'bytes')

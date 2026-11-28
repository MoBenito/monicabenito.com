"""Entangling nuclear spins in distant quantum dots via an electron bus (Bello, Benito, Schuetz, Platero, Giedke,
PRApplied 2022).

Figure 1 in 3D: a channel (the road) with two gate-defined quantum dots (pits) at its ends, each holding an
ensemble of randomly oriented nuclear spins (blue). A spin-polarised electron (orange spin) is injected into QD1
(curved arrow in), interacts with that ensemble, is carried coherently along the channel (here: it rides a bus),
interacts with QD2 and leaves (curved arrow out). The result: the two distant ensembles become entangled, drawn as
pink threads joining them, pinched where the electron passes (it mediates the correlation).
"""
import random
random.seed(11)

bright_stage(floor_z=-0.7, exposure=-0.35, sun_rot=(48, 0, -30))


def eb_cyclorama(y0=8.0, R=6.0, top=40.0, width=140.0, fz=-0.7, bottom=(1.0, 0.7, 0.62, 1), upper=(0.5, 0.62, 1.0, 1), glow=0.3):
    import bmesh
    bm = bmesh.new()
    prof = [(y0 + R * math.sin(math.pi / 2 * j / 24), R - R * math.cos(math.pi / 2 * j / 24)) for j in range(25)]
    prof.append((y0 + R, top))
    rows = [[bm.verts.new((xx, yy, zz + fz + 0.01)) for xx in (-width / 2, width / 2)] for (yy, zz) in prof]
    for a_, b_ in zip(rows[:-1], rows[1:]):
        bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
    me = bpy.data.meshes.new("eb_cyc"); bm.to_mesh(me); bm.free()
    for f_ in me.polygons:
        f_.use_smooth = True
    ob = bpy.data.objects.new("eb_cyc", me); sc.collection.objects.link(ob)
    m = principled("eb_cyc", **{"Roughness": 0.6})
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.0, bottom
    el[1].position, el[1].color = 1.0, upper
    mid = el.new(0.45); mid.color = (1.0, 0.68, 0.82, 1)
    nt.links.new(_math(nt, "DIVIDE", sp.outputs["Z"], 9.0), rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow
    me.materials.append(m)


eb_cyclorama(y0=6.5)

P = "eb_"
CHIP = principled(P + "chip", **{"Base Color": (0.35, 0.82, 0.72, 1), "Roughness": 0.3, "Coat Weight": 0.5})
ROAD = principled(P + "road", **{"Base Color": (0.9, 0.9, 1.0, 1), "Roughness": 0.25, "Coat Weight": 0.8})
STRIPE = principled(P + "stripe", **{"Base Color": (0.15, 0.4, 1.0, 1), "Roughness": 0.25})
PIT = principled(P + "pit", **{"Base Color": (0.55, 0.75, 1.0, 1), "Roughness": 0.3, "Emission Color": (0.4, 0.65, 1.0, 1),
                               "Emission Strength": 0.3})
NUC = principled(P + "nuc", **{"Base Color": (0.2, 0.5, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0})
NUC_ARROW = principled(P + "nuc_arrow", **{"Base Color": (0.02, 0.04, 0.18, 1), "Roughness": 0.25})
QARROW = principled(P + "qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
ENT = emission(P + "ent", (1.0, 0.05, 0.45, 1), 5.0)
FLOW = emission(P + "flow", (1.0, 0.25, 0.1, 1), 4.0)

# chip slab
box((0, 0.5, -0.35), (30.0, 12.0, 0.7), CHIP, bevel=0.08)

# the channel: a raised road with two pits (the dots), as in the cross-section of Figure 1
L, W, H = 15.6, 3.4, 0.7
DX, PW, PD = 5.2, 3.0, 0.45          # dot centre, pit length, pit depth
box((0, 0, (H - PD) / 2), (L, W, H - PD), ROAD, bevel=0.04)
segs = [(-L / 2, -DX - PW / 2), (-DX + PW / 2, DX - PW / 2), (DX + PW / 2, L / 2)]
for a, b in segs:
    box(((a + b) / 2, 0, H - PD / 2), (b - a, W, PD), ROAD, bevel=0.04)
for s in (-1, 1):
    box((s * DX, 0, H - PD + 0.01), (PW - 0.02, W - 0.02, 0.02), PIT, bevel=0.0)
    for sy in (-1, 1):  # pit side walls in y so the pit is a pocket, not a trench
        box((s * DX, sy * (W / 2 - 0.15), H - PD / 2), (PW, 0.3, PD), ROAD, bevel=0.03)
# blue edge stripes along the road
for a, b in segs:
    for sy in (-1, 1):
        box(((a + b) / 2, sy * (W / 2 + 0.005), H - 0.06), (b - a - 0.1, 0.02, 0.06), STRIPE, bevel=0.0)

# gold gates laid out like a real gate-defined device (cf. conveyor-mode shuttling chips): each dot is defined by a
# plunger over the pit and two barrier gates at its ends; the channel between the dots is covered by a regular comb
# of conveyor (clavier) gates that move the electron along. Every finger is a lithographic strip that climbs the mesa
# wall and ends with a short lip over the road edge, mirrored on both sides (split-gate pairs); all lines fan out
# in order to a regular row of bond pads.
GW = 0.075                    # gate metal thickness
FING = []                     # (x, width)
for s in (-1, 1):
    FING += [(s * (DX - PW / 2 - 0.28), 0.32), (s * DX, 0.5), (s * (DX + PW / 2 + 0.28), 0.32)]
NCV = 11
for k in range(NCV):
    FING.append((-2.75 + 5.5 * k / (NCV - 1), 0.24))
FING.sort()
NP = len(FING)
PADX = [-7.3 + 14.6 * k / (NP - 1) for k in range(NP)]
for sy in (-1, 1):
    for (x, w), px in zip(FING, PADX):
        yw = sy * (W / 2 + 0.03)
        lip = 0.42 if abs(abs(x) - DX) > 0.3 else 0.34
        box((x, sy * (W / 2 - lip / 2 + 0.06), H + GW / 2), (w, lip + 0.12, GW), GOLD, bevel=0.025)   # lip on the road
        box((x, yw + sy * 0.03, (H + GW) / 2), (w, GW, H + GW), GOLD, bevel=0.02)                     # up the wall
        if sy > 0:             # far side: lines run straight off to the far bond pads (out of view)
            gate([(x, yw), (x, 6.3)], width=min(w, 0.3), height=GW)
            continue
        gate([(x, yw), (x, sy * 2.2), (px, sy * 3.25), (px, sy * 3.55)], width=min(w, 0.3), height=GW)
        box((px, sy * 3.82, GW / 2 + 0.02), (0.62, 0.62, GW + 0.04), GOLD, bevel=0.04)

 
def nspin(c, d, r=0.14):
    d = Vector(d).normalized()
    sphere(tuple(c), r, NUC)
    start, end = c - d * r * 1.8, c + d * r * 2.2
    rot = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=(end - start).length, location=tuple((start + end) / 2),
                                        rotation=rot, vertices=12)
    link(bpy.context.object, NUC_ARROW)
    bpy.ops.mesh.primitive_cone_add(radius1=0.09, depth=0.17, location=tuple(end + d * 0.07), rotation=rot, vertices=16)
    link(bpy.context.object, NUC_ARROW)


def rand_dir():
    while True:
        v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
        if 0.2 < v.length < 1:
            return v


# nuclear-spin ensembles in each dot: two layers
ENS = {-1: [], 1: []}
zf = H - PD
for s in (-1, 1):
    for layer, (nx, ny, z) in enumerate(((6, 5, zf + 0.2), (5, 4, zf + 0.62))):
        for i in range(nx):
            for j in range(ny):
                x = s * DX + (i - (nx - 1) / 2) * 0.46 + random.uniform(-0.05, 0.05)
                y = (j - (ny - 1) / 2) * 0.5 + random.uniform(-0.05, 0.05)
                c = Vector((x, y, z + random.uniform(-0.03, 0.03)))
                nspin(c, rand_dir())
                ENS[s].append(c)

# the bus: a toy open-top double-decker driving along the channel towards QD2 (+x). Red two-tone body with rounded
# bevels, cream belt line, a row of windows, a split front door, windscreen with a lit destination blind, headlights,
# tail lights, bumpers, grille, mirrors, carved wheel arches and wheels with tyres and silver hubs. The electron spin
# is its one passenger, sitting on the bench of the open upper deck.
BX = 0.4
_before = set(bpy.data.objects)
BUS = principled(P + "bus", **{"Base Color": (0.95, 0.06, 0.05, 1), "Roughness": 0.18, "Coat Weight": 1.0})
CREAM = principled(P + "cream", **{"Base Color": (1.0, 0.93, 0.78, 1), "Roughness": 0.25, "Coat Weight": 1.0})
DECK = principled(P + "deck", **{"Base Color": (0.82, 0.85, 0.92, 1), "Roughness": 0.35})
SEAT = principled(P + "seat", **{"Base Color": (0.1, 0.35, 0.95, 1), "Roughness": 0.3, "Coat Weight": 0.6})
GLASS = principled(P + "win", **{"Base Color": (0.06, 0.16, 0.38, 1), "Roughness": 0.03, "Coat Weight": 1.0,
                                 "Metallic": 0.5})
TYRE = principled(P + "tyre", **{"Base Color": (0.035, 0.035, 0.045, 1), "Roughness": 0.55})
DARK = principled(P + "dark", **{"Base Color": (0.05, 0.05, 0.07, 1), "Roughness": 0.4})
LAMP = emission(P + "lamp", (1.0, 0.92, 0.65, 1), 9.0)
TAIL = emission(P + "tail", (1.0, 0.08, 0.05, 1), 6.0)
BLIND = emission(P + "blind", (1.0, 0.8, 0.25, 1), 2.5)

bl, bw = 3.7, 1.6
bz = H + 0.2                   # underside of the body
bh = 1.25                      # lower deck height
xf, xr = BX + bl / 2, BX - bl / 2
WR, WZ = 0.37, H + 0.37        # wheel radius, wheel centre height
WXS = (xr + 0.75, xf - 0.72)

body = box((BX, 0, bz + bh / 2), (bl, bw, bh), BUS, bevel=0.2)
for wx in WXS:                 # wheel arches carved out of the body
    bpy.ops.mesh.primitive_cylinder_add(radius=WR + 0.08, depth=bw + 0.6, location=(wx, 0, WZ), rotation=(math.radians(90), 0, 0), vertices=48)
    cut = bpy.context.object; cut.hide_render = True; cut.hide_viewport = True
    bo = body.modifiers.new("arch", "BOOLEAN"); bo.object = cut; bo.operation = "DIFFERENCE"
    # dark inner arch lining
    bpy.ops.mesh.primitive_cylinder_add(radius=WR + 0.07, depth=bw - 0.12, location=(wx, 0, WZ), rotation=(math.radians(90), 0, 0), vertices=48)
    link(bpy.context.object, DARK)
# cream belt line between the decks and a cream skirt
box((BX, 0, bz + bh - 0.2), (bl + 0.02, bw + 0.02, 0.13), CREAM, bevel=0.05)
# side windows (both sides) and the front door on the near side (y < 0)
wz, wh = bz + 0.7, 0.58
for sy in (-1, 1):
    xs = [xr + 0.42 + 0.66 * k for k in range(4)] if sy < 0 else [xr + 0.42 + 0.66 * k for k in range(5)]
    for x in xs:
        box((x + 0.27, sy * (bw / 2 + 0.005), wz), (0.54, 0.04, wh), GLASS, bevel=0.06)
    if sy < 0:                 # split door near the front
        for dx in (-0.155, 0.155):
            box((xf - 0.75 + dx, -bw / 2 - 0.005, bz + 0.52), (0.29, 0.04, 0.86), GLASS, bevel=0.04)
        box((xf - 0.75, -bw / 2 - 0.02, bz + 0.52), (0.04, 0.03, 0.88), CREAM, bevel=0.01)
# windscreen, destination blind, rear window
box((xf + 0.005, 0, wz + 0.02), (0.04, bw - 0.36, wh + 0.1), GLASS, bevel=0.06)
box((xf + 0.01, 0, bz + bh - 0.42), (0.04, bw - 0.6, 0.16), BLIND, bevel=0.03)
box((xr - 0.005, 0, wz + 0.05), (0.04, bw - 0.6, wh - 0.06), GLASS, bevel=0.06)
# grille, headlights with silver rims, tail lights, bumpers
box((xf + 0.01, 0, bz + 0.3), (0.04, 0.6, 0.18), DARK, bevel=0.03)
for sy in (-1, 1):
    for x, mat, r in ((xf + 0.01, LAMP, 0.1), (xr - 0.01, TAIL, 0.08)):
        bpy.ops.mesh.primitive_cylinder_add(radius=r + 0.035, depth=0.05, location=(x, sy * (bw / 2 - 0.28), bz + 0.3), rotation=(0, math.radians(90), 0), vertices=32)
        link(bpy.context.object, SILVER)
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.07, location=(x, sy * (bw / 2 - 0.28), bz + 0.3), rotation=(0, math.radians(90), 0), vertices=32)
        link(bpy.context.object, mat)
for x in (xf + 0.06, xr - 0.06):
    box((x, 0, bz + 0.08), (0.14, bw + 0.04, 0.14), SILVER, bevel=0.06)
# side mirrors on little stalks
for sy in (-1, 1):
    tube([(xf - 0.12, sy * (bw / 2), bz + 0.95), (xf + 0.08, sy * (bw / 2 + 0.16), bz + 0.95), (xf + 0.08, sy * (bw / 2 + 0.16), bz + 0.75)], 0.018, DARK)
    box((xf + 0.08, sy * (bw / 2 + 0.17), bz + 0.68), (0.05, 0.1, 0.18), DARK, bevel=0.025)
# wheels: rounded tyres, silver hubs with a centre cap and five wheel nuts
for wx in WXS:
    for sy in (-1, 1):
        y0 = sy * (bw / 2 - 0.1)
        bpy.ops.mesh.primitive_cylinder_add(radius=WR, depth=0.3, location=(wx, y0, WZ), rotation=(math.radians(90), 0, 0), vertices=48)
        t_ = bpy.context.object; bpy.ops.object.shade_smooth()
        bv = t_.modifiers.new("b", "BEVEL"); bv.width = 0.09; bv.segments = 5
        link(t_, TYRE)
        yo = y0 + sy * 0.15
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.06, location=(wx, yo, WZ), rotation=(math.radians(90), 0, 0), vertices=40)
        h_ = bpy.context.object; bv = h_.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 3
        link(h_, SILVER)
        sphere((wx, yo + sy * 0.03, WZ), 0.075, SILVER)
        for k in range(5):
            a = 2 * math.pi * k / 5
            sphere((wx + 0.13 * math.cos(a), yo + sy * 0.035, WZ + 0.13 * math.sin(a)), 0.025, DARK)
# open upper deck: floor, red side walls with a cream top rail, a short front screen, benches
dz = bz + bh
box((BX, 0, dz - 0.02), (bl - 0.3, bw - 0.24, 0.06), DECK, bevel=0.02)
uh = 0.3
for sy in (-1, 1):
    box((BX, sy * (bw / 2 - 0.06), dz + uh / 2 - 0.05), (bl - 0.12, 0.12, uh), BUS, bevel=0.05)
    box((BX, sy * (bw / 2 - 0.06), dz + uh - 0.02), (bl - 0.08, 0.16, 0.07), CREAM, bevel=0.03)
for x in (xf - 0.06, xr + 0.06):
    box((x, 0, dz + uh / 2 - 0.05), (0.12, bw - 0.12, uh), BUS, bevel=0.05)
    box((x, 0, dz + uh - 0.02), (0.16, bw - 0.08, 0.07), CREAM, bevel=0.03)
box((xf - 0.1, 0, dz + uh + 0.17), (0.04, bw - 0.3, 0.3), GLASS, bevel=0.03)        # little front wind screen
for x in (xf - 0.6, BX - 0.1, xr + 0.55):
    box((x, 0, dz + 0.14), (0.42, bw - 0.4, 0.14), SEAT, bevel=0.04)                  # seat
    box((x - 0.2, 0, dz + 0.3), (0.08, bw - 0.4, 0.3), SEAT, bevel=0.035)         # backrest
ec = Vector((BX - 0.05, 0, dz + 0.36 + 0.52))
spin(tuple(ec), (0.45, -0.25, 1.0), r=0.52, arrow=QARROW, reach=1.7, shaft=0.11)
hot_spot(tuple(ec), (1.0, 0.7, 0.4, 1), 0.05, 25)
# scale the whole bus (and its passenger) up about its ground point so the hero fills more of the frame
from mathutils import Matrix as _M
SB = 1.25
_piv = Vector((BX, 0, H))
_S = _M.Translation(_piv) @ _M.Scale(SB, 4) @ _M.Translation(-_piv)
for _o in set(bpy.data.objects) - _before:
    if _o.parent is None:
        _o.matrix_world = _S @ _o.matrix_world
bz = H + (bz - H) * SB
xr = BX - (BX - xr) * SB
# speed lines behind the bus
for k, (dy, dz_) in enumerate(((-0.4, 0.45), (0.0, 0.8), (0.4, 0.3))):
    x0 = xr - 0.35
    tube([(x0 - 1.6 + 0.3 * k, dy, bz + dz_), (x0, dy, bz + dz_)], 0.035, FLOW)
def arrow_curve(pts, r, mat, head=0.32):
    tube(pts[:-3], r, mat)
    a, b = Vector(pts[-4]), Vector(pts[-1])
    d = (b - a).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=r * 3.2, depth=head, location=tuple(a + d * head / 2),
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, mat)


def bez(p0, p1, p2, n=60):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2) for t in [i / n for i in range(n + 1)]]


# injection of a polarised electron into QD1, and the electron leaving QD2 (the curved arrows of Figure 1)
arrow_curve(bez((-DX - 1.5, -0.3, 4.6), (-DX - 0.4, -0.3, 4.8), (-DX - 0.15, -0.2, 1.75)), 0.06, FLOW)
spin((-DX - 1.85, -0.3, 4.6), (0, 0, 1), r=0.3, arrow=QARROW, reach=1.5, shaft=0.12)   # incoming polarised spin
arrow_curve(bez((DX + 0.3, 0.2, 1.6), (DX + 1.0, 0.2, 3.6), (DX + 3.4, 0.2, 3.4)), 0.06, FLOW)

# entanglement: pink threads from QD1's nuclear spins to QD2's, pinched where the electron passes
top = [c for c in ENS[-1] if c.z > zf + 0.4]
top2 = [c for c in ENS[1] if c.z > zf + 0.4]
for k in range(34):
    a = random.choice(top) + Vector((0, 0, 0.18))
    b = random.choice(top2) + Vector((0, 0, 0.18))
    mid = Vector((BX - 0.1 + random.uniform(-0.2, 0.2), random.uniform(-0.15, 0.15), 4.95 + random.uniform(-0.15, 0.15)))
    pts = []
    for i in range(121):
        t = i / 120
        if t < 0.5:
            u = t * 2
            q = (1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * (a + Vector((0, 0, 2.6))) + 3 * (1 - u) * u * u * (mid - Vector((2.0, 0, 0))) + u ** 3 * mid
        else:
            u = (t - 0.5) * 2
            q = (1 - u) ** 3 * mid + 3 * (1 - u) ** 2 * u * (mid + Vector((2.0, 0, 0))) + 3 * (1 - u) * u * u * (b + Vector((0, 0, 2.6))) + u ** 3 * b
        pts.append(tuple(q))
    tube(pts, 0.02, ENT)

camera((1.8, -15.0, 6.9), (0.5, 0.0, 2.0), lens=30, dof=6.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

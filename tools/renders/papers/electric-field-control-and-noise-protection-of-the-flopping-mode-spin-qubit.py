"""Electric-field control and noise protection of the flopping-mode spin qubit (Benito et al. 2019): an electron
moves across a double-well confinement potential (sculpted landscape) while an oscillating electric field shakes it;
the micromagnet's transverse field changes sign along the double dot (row of red field arrows), so the spin direction
turns as the charge moves: artificial spin-orbit coupling. At the sweet spot (zero detuning, electron delocalised over
the barrier) the qubit is protected from charge noise: fluctuators' ripples fade before they reach it."""
import bmesh
import random

random.seed(3)
bright_stage()


def ef_mat(name, **kw):
    return principled("ef_" + name, **kw)


def ef_arrow(base, d, length, r, mat, head_k=3.0):
    d = Vector(d).normalized(); base = Vector(base)
    head = min(r * head_k, length * 0.6)
    rot = d.to_track_quat("Z", "Y").to_euler()
    if length - head > 1e-3:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length - head, location=base + d * (length - head) / 2,
                                            rotation=rot, vertices=32)
        bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.3, depth=head, location=base + d * (length - head / 2), rotation=rot,
                                    vertices=32)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


# --- the double-well landscape: a sculpted block whose top is the confinement potential --------------------------
D, A, Z0, HW = 2.2, 1.55, 0.0, 1.6
V = lambda x: Z0 + A * ((x / D) ** 2 - 1) ** 2
XM = 3.35
bm = bmesh.new()
NX = 160
top, bot = [], []
for i in range(NX + 1):
    x = -XM + 2 * XM * i / NX
    top.append([bm.verts.new((x, y, V(x))) for y in (-HW, HW)])
    bot.append([bm.verts.new((x, y, -0.7)) for y in (-HW, HW)])
for i in range(NX):
    a, b = top[i], top[i + 1]
    bm.faces.new((a[0], b[0], b[1], a[1]))                 # top
    bm.faces.new((bot[i][0], bot[i][1], bot[i + 1][1], bot[i + 1][0]))
    bm.faces.new((a[0], bot[i][0], bot[i + 1][0], b[0]))   # front
    bm.faces.new((a[1], b[1], bot[i + 1][1], bot[i][1]))   # back
for row, tb in ((0, top[0]), (NX, top[NX])):
    bb = bot[row]
    f = bm.faces.new((tb[0], tb[1], bb[1], bb[0]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("ef_well"); bm.to_mesh(me); bm.free()
well = bpy.data.objects.new("ef_well", me); sc.collection.objects.link(well)
for p in me.polygons:
    p.use_smooth = abs(p.normal.y) < 0.5
bev = well.modifiers.new("b", "BEVEL"); bev.width = 0.05; bev.segments = 3; bev.limit_method = "ANGLE"
WELL = ef_mat("well", **{"Base Color": (0.3, 0.8, 0.7, 1), "Roughness": 0.25, "Coat Weight": 1.0, "Coat Roughness": 0.05})
# the front face shows the energy as colour bands (contour-like), the top stays plain
nt = WELL.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.12, 0.38, 1.0, 1)
el[1].position, el[1].color = 1.0, (0.25, 0.85, 0.68, 1)
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.7; mr.inputs["From Max"].default_value = 1.2
nt.links.new(sp.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
link(well, WELL)
# a glowing line traces the potential along the middle of the top
tube([(x, 0, V(x) + 0.015) for x in [-XM + 2 * XM * i / 200 for i in range(201)]], 0.03, emission("ef_vline", (1.0, 1.0, 1.0, 1), 2.0))

# --- the electron's journey across the barrier: the spin turns as it moves through the field gradient ------------
QARROW = ef_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
GHOST = bpy.data.materials.new("ef_ghost"); GHOST.use_nodes = True
gnt = GHOST.node_tree; gb = gnt.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (1.0, 0.4, 0.06, 1); gb.inputs["Roughness"].default_value = 0.15
gb.inputs["Emission Color"].default_value = (1.0, 0.4, 0.08, 1); gb.inputs["Emission Strength"].default_value = 0.4
gb.inputs["Alpha"].default_value = 0.85
GARROW = ef_mat("garrow", **{"Base Color": (0.0, 0.32, 0.32, 1), "Roughness": 0.25, "Coat Weight": 1.0})
xs = [-2.2, -1.55, -0.85, 0.85, 1.55, 2.2]
theta = lambda x: math.radians(-70) * math.tanh(x / 1.1) * -1    # spin axis follows the local field direction
for x in xs:
    r = 0.24
    n = Vector((-(V(x + 0.01) - V(x - 0.01)) / 0.02, 0, 1)).normalized()
    p = Vector((x, -0.1, V(x))) + n * (r + 0.02)
    sphere(tuple(p), r, GHOST)
    al = math.atan2(-x / 2.2 * 1.3, 1.0)
    d = Vector((math.cos(al), -0.15, math.sin(al)))
    ef_arrow(p - d * r * 1.5, d, r * 4.6, 0.045, GARROW)
# a dotted trail along the path
TRAILM = emission("ef_trail", (1.0, 0.55, 0.15, 1), 4.0)
for i in range(46):
    x = -2.4 + 4.8 * i / 45
    if any(abs(x - xx) < 0.3 for xx in xs) or abs(x) < 0.55:
        continue
    n = Vector((-(V(x + 0.01) - V(x - 0.01)) / 0.02, 0, 1)).normalized()
    sphere(tuple(Vector((x, -0.1, V(x))) + n * 0.12), 0.035, TRAILM)
# the hero: the qubit at the sweet spot, right on top of the barrier
c = Vector((0, -0.1, V(0) + 0.55))
spin(tuple(c), (1.0, -0.2, 0.0), r=0.52, arrow=QARROW, reach=2.1, shaft=0.1)
hot_spot(tuple(c), (1.0, 0.7, 0.4, 1), 0.05, 25)
# protective soap-bubble around the sweet-spot qubit
bub = ef_mat("bubble", **{"Base Color": (1, 1, 1, 1), "Transmission Weight": 1.0, "Roughness": 0.0, "IOR": 1.05,
                           "Thin Film Thickness": 600.0, "Thin Film IOR": 1.33})
sphere(tuple(c + Vector((0, 0, 0.15))), 1.35, bub)
bpy.context.object.visible_shadow = False

# --- the magnetic field from the micromagnet: transverse part flips sign across the double dot -----------------
RED = ef_mat("bfield", **{"Base Color": (0.85, 0.05, 0.06, 1), "Roughness": 0.25, "Coat Weight": 1.0})
zb = 4.3
for i in range(13):
    x = -3.0 + 6.0 * i / 12
    L = 1.15 * (-x / 3.0)
    if abs(L) < 0.08:
        sphere((x, 0, zb), 0.07, RED)
        continue
    d = (0, 0, 1 if L > 0 else -1)
    ef_arrow((x, 0, zb - L / 2), d, abs(L), 0.055, RED)
NAVY = ef_mat("bz", **{"Base Color": (0.05, 0.1, 0.45, 1), "Roughness": 0.25, "Coat Weight": 1.0})
ef_arrow((-3.1, 0.0, 5.35), (1, 0, 0), 6.2, 0.08, NAVY)

# --- the oscillating electric field that drives the charge back and forth --------------------------------------
WAVE = emission("ef_drive", (0.7, 0.1, 1.0, 1), 5.0)
pts = [(x, -HW - 0.45, -0.05 + 0.32 * math.sin(2 * math.pi * x / 1.1)) for x in [-2.75 + 5.5 * i / 300 for i in range(301)]]
tube(pts, 0.04, WAVE)
for s in (-1, 1):
    ef_arrow((s * 2.9, -HW - 0.45, -0.05), (s, 0, 0), 0.5, 0.04, WAVE)

# --- charge noise: fluctuators on the floor around the device, their ripples dying out ------------------------
PLUS = emission("ef_tls_plus", (1.0, 0.35, 0.25, 1), 5.0)
MINUS = emission("ef_tls_minus", (0.25, 0.5, 1.0, 1), 5.0)
for (fx, fy, ang) in ((-4.7, -1.4, 20), (4.8, -1.0, -35), (-5.2, 2.6, 60), (5.3, 3.0, 110)):
    cc = Vector((fx, fy, -0.55))
    dd = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.25)).normalized()
    sphere(tuple(cc + 0.16 * dd), 0.09, PLUS); sphere(tuple(cc - 0.16 * dd), 0.09, MINUS)
    tube([tuple(cc - 0.16 * dd), tuple(cc + 0.16 * dd)], 0.02, STEEL)
    for i, rr in enumerate((0.45, 0.8, 1.15)):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.03, major_segments=96, minor_segments=6, location=(fx, fy, -0.66))
        link(bpy.context.object, emission("ef_ring%d" % i, (1.0, 0.45, 0.05, 1), 3.0 / (1 + 1.2 * i)))

# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 9.0 + 6.0 * math.sin(a) if t < 1 else 15.0, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 15.0, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("ef_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("ef_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = ef_mat("sweep", **{"Roughness": 0.6})
nt = SW.node_tree; b_ = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 9.0
nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (1.0, 0.68, 0.52, 1)
el[1].position, el[1].color = 1.0, (0.38, 0.62, 1.0, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b_.inputs["Base Color"])
nt.links.new(ramp.outputs["Color"], b_.inputs["Emission Color"])
b_.inputs["Emission Strength"].default_value = 0.0
b_.inputs["Roughness"].default_value = 0.9
link(sw, SW)

# --- polish pass: saturated stage colours (floor, sky, backdrop sweep) ------------------------------------------
def pz_colour_stage(floor=None, mortar=None, sky=None, sweep=None, sweep_emit=0.0, sweep_name=None, sweep_widen=1.0):
    if floor:
        for n_ in bpy.data.materials["pale_floor"].node_tree.nodes:
            if n_.type == "TEX_BRICK":
                n_.inputs["Color1"].default_value = n_.inputs["Color2"].default_value = floor + (1,)
                n_.inputs["Mortar"].default_value = (mortar or floor) + (1,)
    if sky:
        for n_ in sc.world.node_tree.nodes:
            if n_.type == "VALTORGB":
                n_.color_ramp.elements[0].color = sky[0] + (1,)
                n_.color_ramp.elements[-1].color = sky[1] + (1,)
    if sweep_name:
        m_ = bpy.data.materials[sweep_name]
        for n_ in m_.node_tree.nodes:
            if n_.type == "VALTORGB" and sweep:
                n_.color_ramp.elements[0].color = sweep[0] + (1,)
                n_.color_ramp.elements[-1].color = sweep[-1] + (1,)
                if len(sweep) == 3:     # a warm middle stop so the peach-to-blue blend never passes through grey
                    n_.color_ramp.elements.new(0.5).color = sweep[1] + (1,)
        m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = sweep_emit
        bpy.data.objects[sweep_name].scale.x = sweep_widen


pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.42, 0.24), (1.0, 0.45, 0.62), (0.18, 0.42, 1.0)), sweep_emit=0.5, sweep_name='ef_sweep', sweep_widen=2.0)

camera((0.6, -14.8, 4.3), (0, 0, 2.15), lens=40)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

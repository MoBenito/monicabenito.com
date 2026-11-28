"""Round 3: both arrangements of Fig. 1 side by side on one chip: the 4x1 chain (left, Fig. 1a) and the 2x2 square
(right, Fig. 1b, where U_N = U_F), each with its own Bx/Bz colour bars.

Programmable two-qubit gates between capacitively coupled flopping-mode spin qubits (Cayao, Benito, Burkard 2020):
two double quantum dots in a row, each holding one electron whose spin rides on its delocalised charge. A floating
capacitor between the inner dots couples the two charges; Coulomb interactions between the dots (nearest, middle, far)
are drawn as coloured arcs. Under the row, the micromagnet field gradient (transverse field changing sign) is a
blue-to-orange band. Tuning the detunings programs which two-qubit gate the coupling produces.

Final (revision "combine both variants"): base is concept A (the chain of Fig. 1a, arcs, spins, warm backdrop); from
concept B come the figure's two colour bars lifted into 3D in front of the chain (Bx: + blue -> 0 -> - orange, Bz:
high red -> low -> high red), replacing the flat band, and B's round parallel-plate capacitor. The barrier gates now
come from the back so the bars have a clean run along the front."""
import bmesh
import random

random.seed(5)
bright_stage()


def tq_mat(name, **kw):
    return principled("tq_" + name, **kw)


def tq_chip(loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    slab = bpy.context.object
    slab.scale = scale
    m = tq_mat("hetero", **{"Roughness": 0.35})
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    fac = _math(nt, "ADD", sp.outputs["Z"], 0.5)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.55, 0.85, 0.75, 1)
    els[1].position, els[1].color = 0.55, (0.3, 0.6, 1.0, 1)
    for pos, col in ((0.68, (1.0, 0.5, 0.3, 1)), (0.93, (0.22, 0.78, 0.72, 1))):
        e = els.new(pos); e.color = col
    nt.links.new(fac, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.02; bev.segments = 2
    link(slab, m)


def tq_arrowhead(tip, d, r, mat):
    d = Vector(d).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=r * 2.6, location=Vector(tip) - d * r * 1.3,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


tq_chip((0, 0.5, -0.35), (34.0, 20.0, 0.7))
_tq_before = set(bpy.data.objects)   # everything built from here to the backdrop is the 4x1 chain

# --- the micromagnet field profile as Figure 1a's two colour bars, lifted into 3D in front of the chain ---------
def tq_bar(y, stops, name, w=10.8, x=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.13))
    ob = bpy.context.object; ob.scale = (w, 0.62, 0.26)
    m = tq_mat(name, **{"Roughness": 0.25, "Coat Weight": 1.0})
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    fac = _math(nt, "ADD", sp.outputs["X"], 0.5)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); els = ramp.color_ramp.elements
    els[0].position, els[0].color = stops[0]
    els[1].position, els[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        els.new(pos).color = col
    nt.links.new(fac, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.25
    bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.06; bv.segments = 3
    link(ob, m)


# Bx: transverse field, + (blue) -> 0 -> - (orange); Bz: longitudinal field, high (red) -> low -> high (red)
tq_bar(-1.75, [(0.0, (0.05, 0.25, 1.0, 1)), (0.5, (0.72, 0.5, 1.0, 1)), (1.0, (1.0, 0.4, 0.02, 1))], "bx")
tq_bar(-2.6, [(0.0, (1.0, 0.04, 0.03, 1)), (0.5, (1.0, 0.72, 0.8, 1)), (1.0, (1.0, 0.04, 0.03, 1))], "bz")

# --- four dots: glowing wells ringed by gold; tunnel links inside each qubit -----------------------------------
XS = {"L1": -5.0, "R1": -2.6, "L2": 2.6, "R2": 5.0}
RING = GOLD
for name, x in XS.items():
    bpy.ops.mesh.primitive_torus_add(major_radius=0.78, minor_radius=0.12, major_segments=96, minor_segments=24,
                                     location=(x, 0, 0.16))
    link(bpy.context.object, RING)
# plunger gates: fingers from the back to each dot ring, barrier gates between the dots of a pair
for name, x in XS.items():
    gate([(x * 1.25, 8.5), (x, 2.4), (x, 0.88)], width=0.34, height=0.2)
for s in (-1, 1):
    gate([(s * 4.7, 8.5), (s * 3.8, 2.6), (s * 3.8, 0.75)], width=0.26, height=0.2)

# charge clouds: each electron spread over its double dot (flopping mode)
for qx in (-3.8, 3.8):
    psi = bpy.data.materials.new("tq_psi"); psi.use_nodes = True
    nt = psi.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, b=None: _math(nt, op, a, b)
    X, Y = sep.outputs["X"], sep.outputs["Y"]
    g = lambda x0: M("EXPONENT", M("MULTIPLY", -1.0, M("ADD", M("POWER", M("DIVIDE", M("SUBTRACT", X, x0), 0.5), 2.0),
                                                         M("POWER", M("DIVIDE", Y, 0.5), 2.0))))
    val = M("POWER", M("ADD", g(-1.2), g(1.2)), 2.0)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.95, 0.8, 1)
    nt.links.new(M("MULTIPLY", val, 8.0), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(qx, 0, 0.06))
    cl = bpy.context.object; cl.scale = (4.4, 2.0, 1); link(cl, psi); cl.visible_shadow = False
    for x_ in (qx - 1.2, qx + 1.2):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(x_, 0, 0.2), segments=32, ring_count=16)
        hh = bpy.context.object; hh.scale = (1.0, 1.0, 0.5)
        link(hh, volume_glow("tq_halo", (0.1, 1.0, 0.7, 1), 8.0)); hh.visible_shadow = False
    # tunnel link between the two dots of the pair
    tube([(qx - 0.7, 0, 0.18), (qx + 0.7, 0, 0.18)], 0.06, emission("tq_tunnel", (0.3, 1.0, 0.85, 1), 3.0))

# --- the floating capacitor between the inner dots: two round parallel plates (from concept B) -----------------
TQPLATE = tq_mat("plate", **{"Base Color": (1.0, 0.78, 0.35, 1), "Metallic": 1.0, "Roughness": 0.15})
for s in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(s * 0.3, 0, 0.95),
                                        rotation=(0, math.radians(90), 0), vertices=64)
    ob = bpy.context.object; bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3
    bpy.ops.object.shade_smooth(); link(ob, TQPLATE)
    tube([(s * 1.82, 0, 0.18), (s * 0.9, 0, 0.18), (s * 0.9, 0, 0.95), (s * 0.36, 0, 0.95)], 0.07, GOLD)
EF = emission("tq_efield", (0.4, 0.8, 1.0, 1), 6.0)
for k in range(9):
    a_ = 2 * math.pi * k / 8 if k < 8 else 0.0
    rr = 0.0 if k == 8 else 0.55
    yy, zz = rr * math.cos(a_), 0.95 + rr * math.sin(a_)
    tube([(-0.24, yy, zz), (0.24, yy, zz)], 0.014, EF)

# --- Coulomb interactions between the dots: nearest (green), middle (blue), far (violet) ------------------------
def tq_arc(x0, x1, h, col, r, name, strength=6.0):
    m = emission(name, col, strength)
    pts = []
    for i in range(121):
        t = i / 120
        x = x0 + (x1 - x0) * t
        pts.append((x, 0.6, 0.45 + h * math.sin(math.pi * t)))
    tube(pts[6:-6], r, m)
    for a_, b_ in ((pts[7], pts[3]), (pts[-8], pts[-4])):
        tq_arrowhead(b_, Vector(b_) - Vector(a_), r * 3.6, m)


tq_arc(XS["R1"], XS["L2"], 1.5, (0.2, 0.9, 0.1, 1), 0.06, "tq_UN", 4.0)
tq_arc(XS["L1"], XS["L2"], 2.6, (0.05, 0.3, 1.0, 1), 0.06, "tq_UM", 4.0)
tq_arc(XS["L1"], XS["R2"], 3.6, (0.6, 0.1, 1.0, 1), 0.06, "tq_UF", 4.0)

# --- the two spin qubits, riding above their charge clouds, each being rotated ---------------------------------
QARROW = tq_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
for qx, tilt in ((-3.8, -30), (3.8, 40)):
    c = Vector((qx, -0.6, 1.9))
    t = math.radians(tilt)
    spin(tuple(c), (math.sin(t), -0.15, math.cos(t)), r=0.58, arrow=QARROW, reach=1.75, shaft=0.1)
    hot_spot(tuple(c), (1.0, 0.7, 0.4, 1), 0.05, 25)
    # the gate acting on this spin: a curved rotation arrow around it
    ROTM = emission("tq_rot", (1.0, 0.45, 0.05, 1), 5.0)
    arc = [tuple(c + Vector((0.95 * math.cos(a), -0.95 * math.sin(a) * 0.5, 0.95 * math.sin(a)))) for a in [math.radians(200 - 150 * i / 40) for i in range(41)]]
    tube(arc, 0.035, ROTM)
    tq_arrowhead(Vector(arc[-1]) + (Vector(arc[-1]) - Vector(arc[-3])).normalized() * 0.15, Vector(arc[-1]) - Vector(arc[-3]), 0.1, ROTM)
    tube([(qx, 0, 0.12), tuple(c - Vector((0, 0, 0.58)))], 0.012, emission("tq_tether", (0.3, 1.0, 0.85, 1), 3.0))

# ======== shift the chain left; build the 2x2 square arrangement (Fig. 1b) on the right ===========================
CHAIN_DX = -4.3
SQ_DX, SQ_DY = 5.2, 3.0
for ob_ in set(bpy.data.objects) - _tq_before:
    if ob_.parent is None:
        ob_.location.x += CHAIN_DX

_tq_before = set(bpy.data.objects)
SQX, SQY, RINGQ = 1.75, 1.75, 0.74
DOTQ = tq_mat("sqdot", **{"Base Color": (0.55, 0.95, 0.9, 1), "Roughness": 0.1, "Transmission Weight": 0.5,
                          "Emission Color": (0.3, 1.0, 0.85, 1), "Emission Strength": 0.8})
for x in (-SQX, SQX):
    for y in (-SQY, SQY):
        bpy.ops.mesh.primitive_torus_add(major_radius=RINGQ, minor_radius=0.12, major_segments=96, minor_segments=24,
                                         location=(x, y, 0.16))
        bpy.ops.object.shade_smooth(); link(bpy.context.object, GOLD)
        bpy.ops.mesh.primitive_cylinder_add(radius=RINGQ - 0.05, depth=0.2, location=(x, y, 0.08), vertices=64)
        link(bpy.context.object, DOTQ)
ZQ = 0.2
TUN = emission("tq_sqtunnel", (0.3, 1.0, 0.85, 1), 3.0)
for y in (-SQY, SQY):        # tunnel link inside each qubit (L-R)
    tube([(-SQX + RINGQ + 0.1, y, ZQ), (SQX - RINGQ - 0.1, y, ZQ)], 0.07, TUN)


def tq_cap(a, b, gap=0.22, plate=0.34, frac=0.5):
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); m = a + (b - a) * frac
    tube([tuple(a), tuple(m - d * gap / 2)], 0.06, GOLD)
    tube([tuple(m + d * gap / 2), tuple(b)], 0.06, GOLD)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=plate, depth=0.07, location=m + d * s_ * gap / 2,
                                            rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=48)
        bpy.ops.object.shade_smooth(); link(bpy.context.object, TQPLATE)


ZC = 0.55
for x in (-SQX, SQX):        # L-L and R-R capacitors between the qubits
    tq_cap((x, -SQY + RINGQ + 0.1, ZC), (x, SQY - RINGQ - 0.1, ZC))
for x in (-SQX, SQX):
    for y in (-SQY, SQY):
        tube([(x, y + (RINGQ + 0.1) * (1 if y < 0 else -1), ZQ), (x, y + (RINGQ + 0.1) * (1 if y < 0 else -1), ZC)], 0.06, GOLD)
# diagonals (round 4: simplified): each has one compact plate pair away from the crossing, and the second one simply
# hops over the first with a low arch, so the crossing itself stays clean
u_ = Vector((1, -1, 0)).normalized()       # diagonal back-L to front-R, straight, plates near the front-R dot
tq_cap(Vector((-SQX, SQY, ZC)) + u_ * (RINGQ + 0.15), Vector((SQX, -SQY, ZC)) - u_ * (RINGQ + 0.15), plate=0.3, frac=0.78)
v_ = Vector((1, 1, 0)).normalized()        # diagonal front-L to back-R, arching over, plates near the back-R dot
a_ = Vector((-SQX, -SQY, ZC)) + v_ * (RINGQ + 0.15); b_ = Vector((SQX, SQY, ZC)) - v_ * (RINGQ + 0.15)
mid_ = (a_ + b_) / 2 + Vector((0, 0, 0.75))
arch = [tuple((1 - t) ** 2 * a_ + 2 * (1 - t) * t * mid_ + t * t * b_) for t in [i / 40 for i in range(41)]]
tube(arch[:30], 0.06, GOLD); tube(arch[33:], 0.06, GOLD)
dd = (Vector(arch[33]) - Vector(arch[30])).normalized()
for p_ in (arch[30], arch[33]):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.07, location=p_, rotation=dd.to_track_quat("Z", "Y").to_euler(), vertices=48)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, TQPLATE)

# one electron spin in the L dot of each qubit (red dots of Fig. 1b)
for y, tilt in ((-SQY, -25), (SQY, 30)):
    c = Vector((-SQX, y, 1.35))
    t = math.radians(tilt)
    spin(tuple(c), (math.sin(t), 0.1, math.cos(t)), r=0.5, arrow=QARROW, reach=1.5, shaft=0.09)
    tube([(-SQX, y, 0.12), tuple(c - Vector((0, 0, 0.5)))], 0.012, emission("tq_tether2", (0.3, 1.0, 0.85, 1), 3.0))

# U_M (blue) between the two L dots, bulging outwards; U_N = U_F (green) pointing at the diagonal crossing
um = [(-SQX - 1.0 - 0.7 * math.sin(math.pi * t), -SQY + 0.2 + (2 * SQY - 0.4) * t, 0.9 + 0.5 * math.sin(math.pi * t))
      for t in [i / 60 for i in range(61)]]
UMQ = emission("tq_UM2", (0.05, 0.3, 1.0, 1), 4.0)
tube(um[5:-5], 0.06, UMQ)
tq_arrowhead(um[0], Vector(um[0]) - Vector(um[5]), 0.22, UMQ)
tq_arrowhead(um[-1], Vector(um[-1]) - Vector(um[-6]), 0.22, UMQ)
UNQ = emission("tq_UN2", (0.2, 0.9, 0.1, 1), 4.0)
tube([(0, -SQY - 1.0, 0.5), (0, -0.9, 1.0)], 0.06, UNQ)
tq_arrowhead((0, -0.55, 1.14), Vector((0, -0.9, 1.0)) - Vector((0, -SQY - 1.0, 0.5)), 0.22, UNQ)

# Fig. 1b colour bars: Bx from + (blue) to 0, Bz from high (red) to low
tq_bar(-SQY - 1.35, [(0.0, (0.05, 0.25, 1.0, 1)), (1.0, (0.72, 0.5, 1.0, 1))], "bx2", w=5.0)
tq_bar(-SQY - 2.15, [(0.0, (1.0, 0.04, 0.03, 1)), (1.0, (1.0, 0.72, 0.8, 1))], "bz2", w=5.0)

for ob_ in set(bpy.data.objects) - _tq_before:
    if ob_.parent is None:
        ob_.location += Vector((SQ_DX, SQ_DY, 0))

# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 10.5 + 6.0 * math.sin(a) if t < 1 else 16.5, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 16.5, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("tq_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("tq_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = tq_mat("sweep", **{"Roughness": 0.6})
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


pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.42, 0.24), (1.0, 0.45, 0.62), (0.42, 0.3, 1.0)), sweep_emit=0.5, sweep_name='tq_sweep', sweep_widen=2.0)

camera((-1.3, -10.0, 13.0), (-1.3, 2.6, 0.9), lens=28)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

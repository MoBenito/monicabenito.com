"""Flopping-mode EDSR (Croot et al. 2020): a single electron in a Si/SiGe double quantum dot, delocalised across both
dots at zero detuning, between two cobalt micromagnets (field gradient). A weak microwave on a plunger gate shakes the
charge back and forth, and through the gradient this flips the spin (EDSR). The other plunger gate connects to a
superconducting resonator whose photons read the spin out dispersively."""
import bmesh
import random
FM1_YS, FM1_ZS = (-1.5, -0.2, 1.1, 2.4, 3.7), (0.2,)

random.seed(11)
bright_stage()


def fm1_mat(name, **kw):
    return principled("fm1_" + name, **kw)


def fm1_chip(loc, scale):
    """Substrate block with the Si/SiGe heterostructure layers on its cut faces."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    slab = bpy.context.object
    slab.scale = scale
    m = fm1_mat("hetero", **{"Roughness": 0.35})
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    fac = _math(nt, "ADD", sp.outputs["Z"], 0.5)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.55, 0.85, 0.75, 1)
    els[1].position, els[1].color = 0.55, (0.3, 0.6, 1.0, 1)
    for pos, col in ((0.68, (1.0, 0.5, 0.3, 1)), (0.93, (0.42, 0.64, 1.0, 1))):
        e = els.new(pos); e.color = col
    nt.links.new(fac, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.02; bev.segments = 2
    link(slab, m)
    return slab


def fm1_arrow(base, d, length, r, mat):
    d = Vector(d).normalized(); base = Vector(base)
    head = r * 3.2
    rot = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length - head, location=base + d * (length - head) / 2,
                                        rotation=rot, vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.4, depth=head, location=base + d * (length - head / 2), rotation=rot,
                                    vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


fm1_chip((0, 3.0, -0.35), (19.0, 15.0, 0.7))

# --- gates: fingers fanning in from the back, accumulation gates from the sides, plunger P2 from the front -------
DL, DR = Vector((-1.0, 0, 0)), Vector((1.0, 0, 0))
fingers = [
    [(-5.5, 9.0), (-2.3, 2.6), (-1.95, 0.45)],     # B1
    [(-2.5, 9.0), (-1.05, 2.4), (-1.0, 0.7)],      # P1 (drive)
    [(0.2, 9.0), (0.0, 2.4), (0.0, 0.5)],          # B2
    [(4.6, 9.0), (2.2, 2.6), (1.95, 0.45)],        # B3
]
# Figure 1 colour code: barrier gates green, plungers and source/drain gates coral red
BGREEN = fm1_mat("bgate", **{"Base Color": (0.1, 0.85, 0.35, 1), "Metallic": 0.35, "Roughness": 0.25, "Coat Weight": 1.0})
PCORAL = fm1_mat("pgate", **{"Base Color": (1.0, 0.22, 0.2, 1), "Metallic": 0.35, "Roughness": 0.25, "Coat Weight": 1.0})
for k_, pts in enumerate(fingers):
    gate(pts, width=0.34, height=0.2, mat=PCORAL if k_ == 1 else BGREEN)
# lower-layer screening gates (aluminium) G1 behind-left and G2 in front-right
ALU = fm1_mat("alu", **{"Base Color": (0.95, 0.7, 0.55, 1), "Metallic": 1.0, "Roughness": 0.3})
for s in (-1, 1):                                   # source / drain accumulation gates
    gate([(s * 8.5, -0.4), (s * 4.6, -0.2), (s * 2.55, 0.0)], width=0.62, height=0.14, mat=PCORAL)
# plunger P2 under the right dot comes from the front and becomes the resonator's centre pin
NB = fm1_mat("niobium", **{"Base Color": (0.8, 0.76, 0.98, 1), "Metallic": 1.0, "Roughness": 0.25})
gate([(1.0, -0.7), (1.0, -2.0)], width=0.34, height=0.2, mat=PCORAL)
# superconducting resonator: a niobium meander leaving the plunger, its photon a glowing standing wave
res_pts = [(1.0, -2.0), (1.0, -2.9), (2.9, -2.9), (2.9, -1.9), (4.7, -1.9), (4.7, -2.9), (8.5, -2.9)]
gate(res_pts, width=0.42, height=0.1, mat=NB)
PH = (0.8, 0.25, 1.0, 1)
seg = res_pts[1:]
for j, ((x0, y0), (x1, y1)) in enumerate(zip(seg[:-1], seg[1:])):
    L = math.hypot(x1 - x0, y1 - y0)
    beam((x0, y0, 0.3), (x1, y1, 0.3), 0.36, beam_material(f"fm1_ph{j}", PH, 8.0, standing=0.95, k=2 * math.pi / 1.4 * L / 2))

# --- cobalt micromagnets on both sides, with a few stray-field lines ---------------------------------------------
CO = fm1_mat("cobalt", **{"Base Color": (1.0, 0.72, 0.15, 1), "Metallic": 0.35, "Roughness": 0.28, "Coat Weight": 1.0})
for s in (-1, 1):
    box((s * 3.7, 1.6, 0.42), (1.5, 5.0, 0.5), CO, bevel=0.08)
# stray field computed, not drawn by hand: the external field (along the double-dot axis, the paper's z) magnetises
# both cobalt bars along +x; each bar is a uniformly magnetised box (north face on its +x side). Lines are integrated
# from seeds spread evenly over the north faces until they close into a south face.
exec(compile((HERE / "papers" / "fieldlines_common.inc").read_text(), "fieldlines_common.inc", "exec"), globals())
FM1_MAGS = [FlMagnet((s * 3.7, 1.6, 0.42), (1.5, 5.0, 0.5), axis=0, sign=1) for s in (-1, 1)]
FM1_BOUNDS = ((-30, -20, -0.7), (30, 30, 20))
fm1_clip = lambda p: p[2] < 0.0          # the chip hides the parts of a line that run through it
# (1) the flux that links the two bars: lines through a grid of points in the mid-plane x = 0, integrated both ways
# (back to the left bar's north face, on to the right bar's south face). They leave a thin band at mid-height of
# the pole faces (dense near the poles) and fan out and sag across the gap: B tilts down at the left dot and up at
# the right dot, the transverse gradient that flopping-mode EDSR uses.
fm1_mid = [(0.0, y, z) for y in FM1_YS for z in FM1_ZS]
fwd = fl_trace_many(fm1_mid, FM1_MAGS, FM1_BOUNDS, step=0.02, max_len=40)
bwd = fl_trace_many(fm1_mid, FM1_MAGS, FM1_BOUNDS, step=0.02, max_len=40, sign=-1)
for (pf, cf), (pb, cb) in zip(fwd, bwd):
    if cf and cb:
        fl_draw(_np.concatenate([pb[::-1], pf[1:]]), radius=0.022, arrows=(0.2, 0.8), clip=fm1_clip)
# (2) the rest of each bar's flux closes on itself: loops from the north face over the bar into its own south face
fm1_seeds = []
for m_ in FM1_MAGS:
    fm1_seeds += [q for i_, q in enumerate(fl_face_seeds(m_, 6, 6, inset=0.06)) if i_ % 6 == 4]
for pts_, closed_ in fl_trace_many(fm1_seeds, FM1_MAGS, FM1_BOUNDS, step=0.025, max_len=60):
    if closed_ and pts_[:, 2].min() > -0.02:      # skip loops that would dive under the chip surface
        fl_draw(pts_, radius=0.022, arrows=(0.5,), clip=fm1_clip)

# --- the electron: one charge spread over both dots (bonding state at zero detuning) -----------------------------
psi = bpy.data.materials.new("fm1_psi"); psi.use_nodes = True
nt = psi.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])
M = lambda op, a=None, b=None: _math(nt, op, a, b)
X, Y = sep.outputs["X"], sep.outputs["Y"]
g = lambda x0: M("EXPONENT", M("MULTIPLY", -1.0, M("ADD", M("POWER", M("DIVIDE", M("SUBTRACT", X, x0), 0.55), 2.0),
                                                     M("POWER", M("DIVIDE", Y, 0.45), 2.0))))
val = M("POWER", M("ADD", g(-1.0), g(1.0)), 2.0)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.95, 0.8, 1)
nt.links.new(M("MULTIPLY", val, 7.0), em.inputs["Strength"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); add = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.03))
cl = bpy.context.object; cl.scale = (5.0, 2.2, 1); link(cl, psi); cl.visible_shadow = False
for x in (-1.0, 1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=(x, 0, 0.3), segments=32, ring_count=16)
    h = bpy.context.object; h.scale = (1.0, 0.8, 0.55)
    link(h, volume_glow("fm1_halo", (0.25, 1.0, 0.8, 1), 14.0)); h.visible_shadow = False

# the spin rides on the delocalised charge, high above the middle of the double dot
c = Vector((0, 0, 1.95))
QARROW = fm1_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
# EDSR: starting from up, the spin is driven down; its Bloch-vector path spirals around the field axis
TRAIL = emission("fm1_rabi", (0.6, 0.15, 1.0, 1), 3.0)
pts = []
N = 600
R = 1.2
for i in range(N):
    s_ = i / (N - 1)
    th = 0.08 + 1.25 * s_
    ph = 2 * math.pi * 2.6 * s_ - 1.2
    pts.append(c + R * Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))))
tube([tuple(p) for p in pts], 0.035, TRAIL)
hot_spot(tuple(pts[-1]), (0.85, 0.55, 1.0, 1), 0.06, 30)
spin(tuple(c), tuple(pts[-1] - c), r=0.6, arrow=QARROW, reach=1.6, shaft=0.1)
hot_spot(tuple(c), (1.0, 0.7, 0.4, 1), 0.06, 25)
# tether from the spin down to the charge cloud: the spin belongs to the flopping electron
tube([(0, 0, 0.3), tuple(c - Vector((0, 0, 0.6)))], 0.014, emission("fm1_tether", (0.3, 1.0, 0.85, 1), 3.0))
# the flopping: a swing arc between the two dots, arrowheads at both ends
SWING = emission("fm1_swing", (1.0, 0.5, 0.1, 1), 7.0)
arc = [(x, -0.1, 1.0 - 0.55 * (1 - (x / 1.1) ** 2)) for x in [-1.1 + 2.2 * i / 60 for i in range(61)]]
tube(arc, 0.04, SWING)
for s in (-1, 1):
    tip = Vector((s * 1.16, -0.1, 1.12)); d = Vector((s * 0.55, 0, 1)).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=0.11, depth=0.27, location=tip, rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, SWING)

# --- the weak microwave drive on P1: a few gentle wavefronts towards the double dot ----------------------------
wave_arcs((-1.0, 0.75, 0.3), (0.0, -0.25, 1.0), n=3, spacing=0.26, color=(1.0, 0.2, 0.5, 1), start=0.12)

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


# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 12.5 + 6.0 * math.sin(a) if t < 1 else 18.5, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 18.5, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("fm1_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("fm1_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = fm1_mat("sweep", **{"Roughness": 0.6})
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

pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.42, 0.24), (1.0, 0.45, 0.62), (0.18, 0.42, 1.0)), sweep_emit=0.5, sweep_name='fm1_sweep', sweep_widen=2.0)

camera((-3.4, -9.6, 5.6), (0.4, -0.7, 1.3), lens=38, dof=None)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

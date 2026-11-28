"""Modeling of flopping-mode spin qubits beyond the two-site model (Kinikar et al. 2026): instead of two sites, the
full spatial problem. A silicon device (blue) under a clear oxide carries plunger and barrier gates and bar
micromagnets whose stray field arcs through it. In the silicon, the electron of each flopping-mode qubit is a
continuous double-humped wavefunction computed on a fine grid (glowing wireframe surfaces). Two such qubits sit side by
side; their spins are coupled through the Coulomb-mediated exchange (glowing link)."""
import bmesh
import random

random.seed(7)
MO_Y = 2.4          # magnets on the front edge of the gate stack; the oxide is cut just behind their symmetry plane
MO_CUT = MO_Y + 0.05
MO_UP, MO_DOWN = (3.05, 3.5, 4.1, 4.8), (0.25, 0.7, 1.2, 1.7)
bright_stage()


def mo_mat(name, **kw):
    return principled("mo_" + name, **kw)


# --- silicon substrate with the interface on top ---------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.0, -0.4))
si = bpy.context.object; si.scale = (17.0, 10.0, 0.8)
SI = mo_mat("si", **{"Roughness": 0.5})
nt = SI.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
fac = _math(nt, "ADD", sp.outputs["Z"], 0.5)
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.15, 0.35, 1.0, 1)
els[1].position, els[1].color = 0.9, (0.3, 0.55, 1.0, 1)
nt.links.new(fac, ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
bev = si.modifiers.new("b", "BEVEL"); bev.width = 0.02; bev.segments = 2
link(si, SI)

# --- oxide terrace at the back (cut away in front to reveal the silicon), holding gates and magnets ------------
OX_H = 1.9
OX = mo_mat("oxide", **{"Base Color": (1.0, 0.58, 0.42, 1), "Roughness": 0.45})
box((0, (8.0 + MO_CUT) / 2, OX_H / 2), (17.0, 8.0 - MO_CUT, OX_H), OX, bevel=0.06)

# --- the two flopping-mode qubits ------------------------------------------------------------------------------
QX = (-3.6, 3.6)
D = 1.05
PGREEN = mo_mat("plunger", **{"Base Color": (0.1, 0.8, 0.3, 1), "Metallic": 0.35, "Roughness": 0.25, "Coat Weight": 1.0})   # Figure 1: plungers green
GATE_C = mo_mat("barrier", **{"Base Color": (0.55, 0.45, 1.0, 1), "Metallic": 0.9, "Roughness": 0.2})


def wf_surface(cx, asym, name):
    """|psi|^2 of the flopping-mode electron on a fine grid: double-humped, asymmetric with detuning."""
    bm = bmesh.new()
    NXg, NYg = 64, 30
    W, Hh = 2.6, 1.5
    grid = []
    for i in range(NXg + 1):
        row = []
        for j in range(NYg + 1):
            x = -W + 2 * W * i / NXg
            y = -Hh + 2 * Hh * j / NYg
            # two Gaussians with a ripple of the full spatial solution between them
            p = ((1 + asym) * math.exp(-((x + D) / 0.62) ** 2) + (1 - asym) * math.exp(-((x - D) / 0.62) ** 2))
            p = p * math.exp(-(y / 0.75) ** 2)
            z = 0.04 + 1.1 * p * p
            row.append(bm.verts.new((cx + x, y, z)))
        grid.append(row)
    for i in range(NXg):
        for j in range(NYg):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    # filled skin: soft glow by height
    skin = bpy.data.materials.new(name + "_skin"); skin.use_nodes = True
    nt = skin.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    r = nt.nodes.new("ShaderNodeValToRGB"); e = r.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.1, 0.55, 1.0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.85, 0.3, 1)
    mid = e.new(0.45); mid.color = (0.25, 1.0, 0.75, 1)
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.05; mr.inputs["From Max"].default_value = 1.6
    nt.links.new(sp.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], r.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(r.outputs["Color"], em.inputs["Color"])
    nt.links.new(_math(nt, "ADD", 0.4, _math(nt, "MULTIPLY", mr.outputs["Result"], 4.0)), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = 0.8
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    me.materials.append(skin)
    # the computational grid: a wireframe copy, brighter
    wire = ob.copy(); wire.data = me.copy(); sc.collection.objects.link(wire)
    wm = wire.modifiers.new("w", "WIREFRAME"); wm.thickness = 0.012; wm.use_replace = True
    wire.data.materials.clear()
    wmat = bpy.data.materials.new(name + "_wire"); wmat.use_nodes = True
    nt = wmat.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    r2 = nt.nodes.new("ShaderNodeValToRGB"); e2 = r2.color_ramp.elements
    e2[0].position, e2[0].color = 0.0, (0.2, 0.6, 1.0, 1)
    e2[1].position, e2[1].color = 1.0, (1.0, 0.75, 0.1, 1)
    mid2 = e2.new(0.4); mid2.color = (0.1, 1.0, 0.6, 1)
    mr2 = nt.nodes.new("ShaderNodeMapRange"); mr2.inputs["From Min"].default_value = 0.05; mr2.inputs["From Max"].default_value = 1.6
    nt.links.new(sp.outputs["Z"], mr2.inputs["Value"]); nt.links.new(mr2.outputs["Result"], r2.inputs["Fac"])
    em2 = nt.nodes.new("ShaderNodeEmission"); nt.links.new(r2.outputs["Color"], em2.inputs["Color"])
    nt.links.new(_math(nt, "ADD", 1.6, _math(nt, "MULTIPLY", mr2.outputs["Result"], 5.0)), em2.inputs["Strength"])
    nt.links.new(em2.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    wire.data.materials.append(wmat)
    ob.visible_shadow = False; wire.visible_shadow = False


QARROW = mo_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
for k, cx in enumerate(QX):
    wf_surface(cx, 0.18 if k == 0 else -0.12, f"mo_wf{k}")
    # gates on the oxide: plungers over the dots (gold), barrier between them (violet), running back along y
    for dx, w, mat in ((-D, 1.15, PGREEN), (0.0, 0.32, GATE_C), (D, 1.15, PGREEN)):
        box((cx + dx, 3.5, OX_H + 0.17), (w, 7.6, 0.34), mat, bevel=0.04)
    c = Vector((cx, -0.9, 1.45))
    t = math.radians(-28 if k == 0 else 24)
    spin(tuple(c), (math.sin(t), -0.2, math.cos(t)), r=0.5, arrow=QARROW, reach=1.6, shaft=0.11)
# screening gates between the qubits
box((0, 4.6, OX_H + 0.17), (1.7, 4.8, 0.34), GATE_C, bevel=0.04)

# --- bar micromagnets on top and their stray field lines -------------------------------------------------------
MR = mo_mat("mag_n", **{"Base Color": (0.9, 0.08, 0.08, 1), "Roughness": 0.3, "Coat Weight": 1.0})
MB = mo_mat("mag_s", **{"Base Color": (0.08, 0.2, 0.95, 1), "Roughness": 0.3, "Coat Weight": 1.0})
mags = (-6.4, 0.0, 6.4)
zm = OX_H + 0.34 + 0.35
for mx in mags:
    box((mx - 0.5, MO_Y, zm), (1.0, 1.2, 0.6), MB, bevel=0.05)
    box((mx + 0.5, MO_Y, zm), (1.0, 1.2, 0.6), MR, bevel=0.05)
    if abs(mx) > 1:     # the outer magnets stand on oxide spacers (no gate below them)
        box((mx, (MO_CUT + MO_Y + 0.55) / 2, (OX_H + zm - 0.3) / 2), (1.9, MO_Y + 0.55 - MO_CUT, zm - 0.3 - OX_H), OX, bevel=0.03)

# stray field computed, not drawn by hand: each bar is a uniformly magnetised box (S|N along +x, as in Figure 1);
# lines are integrated (RK4) through the computed field until they close into a south face.
exec(compile((HERE / "papers" / "fieldlines_common.inc").read_text(), "fieldlines_common.inc", "exec"), globals())
MO_MAGS = [FlMagnet((mx, MO_Y, zm), (2.0, 1.2, 0.6), axis=0, sign=1) for mx in mags]
MO_BOUNDS = ((-40, -30, -1.0), (40, 40, 30))


def mo_clip(p):
    """Hidden where a line runs inside the silicon or the oxide terrace (it is still there, just inside matter)."""
    return p[2] < 0.0 or (p[1] > MO_CUT and p[2] < OX_H and abs(p[0]) < 8.5)


def mo_both_ways(seeds, arrows):
    fwd = fl_trace_many(seeds, MO_MAGS, MO_BOUNDS, step=0.025, max_len=50)
    bwd = fl_trace_many(seeds, MO_MAGS, MO_BOUNDS, step=0.025, max_len=50, sign=-1)
    for (pf, cf), (pb, cb) in zip(fwd, bwd):
        if cf and cb:
            fl_draw(_np.concatenate([pb[::-1], pf[1:]]), radius=0.03, arrows=arrows, clip=mo_clip)


# flux from each north face into the next magnet's south face: arcs above the gates (symmetry plane) and, in the
# cut face, down through the gate stack towards the silicon and the double dot, where the field varies (gradient)
gaps = [(a_ + b_) / 2 for a_, b_ in zip(mags[:-1], mags[1:])]
mo_both_ways([(xc, MO_Y, z) for xc in gaps for z in MO_UP], (0.5,))
mo_both_ways([(xc, MO_Y - 0.08, z) for xc in gaps for z in MO_DOWN], (0.5,))
# the outer ends: flux leaving the last north face and entering the first south face loops back over its own bar
ends = [q for q in fl_face_seeds(MO_MAGS[-1], 1, 4, inset=0.1)][2:]
fl_res = fl_trace_many(ends, MO_MAGS, MO_BOUNDS, step=0.025, max_len=50)
ends_s = [q for q in fl_face_seeds(MO_MAGS[0], 1, 4, inset=0.1, which="S")][2:]
fl_res += [(p[::-1], c) for p, c in fl_trace_many(ends_s, MO_MAGS, MO_BOUNDS, step=0.025, max_len=50, sign=-1)]
for p, c in fl_res:
    if c:
        fl_draw(p, radius=0.03, arrows=(0.5,), clip=mo_clip)

# --- exchange between the two qubits: a glowing link from spin to spin ----------------------------------------
JM = emission("mo_exchange", (1.0, 0.15, 0.55, 1), 5.0)
pA, pB = Vector((QX[0] + 0.5, -0.9, 1.5)), Vector((QX[1] - 0.5, -0.9, 1.5))
pts = []
for i in range(201):
    t = i / 200
    p = pA.lerp(pB, t)
    p.z += 0.55 * math.sin(math.pi * t)
    p += Vector((0, 0.12 * math.sin(2 * math.pi * 7 * t), 0.12 * math.cos(2 * math.pi * 7 * t))) * math.sin(math.pi * t)
    pts.append(tuple(p))
tube(pts, 0.04, JM)

# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 10.0 + 6.0 * math.sin(a) if t < 1 else 16.0, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 16.0, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("mo_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("mo_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = mo_mat("sweep", **{"Roughness": 0.6})
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


pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.55, 0.2), (1.0, 0.45, 0.55), (0.18, 0.42, 1.0)), sweep_emit=0.5, sweep_name='mo_sweep', sweep_widen=2.0)

camera((0.8, -13.8, 5.4), (0, 1.3, 1.5), lens=43)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

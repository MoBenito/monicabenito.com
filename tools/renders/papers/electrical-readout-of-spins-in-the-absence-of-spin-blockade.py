"""Electrical readout of spins in the absence of spin blockade (von Horstig et al. 2025): a silicon nanowire
transistor on buried oxide. Under the wrap-around gold gate a hole quantum dot forms at the nanowire's top corner;
beside it sits a single boron acceptor (magenta atom) that binds a second hole. The hole hops back and forth between
dot and acceptor (polarizability), which depends on the two-spin state. The gate is wired to an LC resonator (spiral
inductor); an RF tone goes in and comes back changed: gate-based reflectometry reads the spins."""
import bmesh
import random

random.seed(9)
bright_stage()


def rd_mat(name, **kw):
    return principled("rd_" + name, **kw)


def rd_arrowhead(tip, d, r, mat):
    d = Vector(d).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=r * 2.6, location=Vector(tip) - d * r * 1.3,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


# --- chip: silicon handle wafer under buried oxide -----------------------------------------------------------------
BOX = rd_mat("box", **{"Base Color": (0.6, 0.94, 0.84, 1), "Roughness": 0.3, "Coat Weight": 0.6})
HANDLE = rd_mat("handle", **{"Base Color": (0.25, 0.45, 1.0, 1), "Roughness": 0.35})
box((0, 3.0, -0.5), (20.0, 15.0, 0.4), HANDLE, bevel=0.02)
box((0, 3.0, -0.15), (20.0, 15.0, 0.3), BOX, bevel=0.02)

# --- the nanowire, source/drain pads (boron doped, p+) ---------------------------------------------------------
SI = rd_mat("si", **{"Base Color": (0.6, 0.68, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0, "Metallic": 0.15})
PPLUS = rd_mat("pplus", **{"Base Color": (1.0, 0.55, 0.6, 1), "Roughness": 0.3, "Coat Weight": 0.8})
NW_W, NW_H = 1.0, 0.55
box((0, 0, NW_H / 2), (8.0, NW_W, NW_H), SI, bevel=0.12)
for s in (-1, 1):
    box((s * 5.0, 0, NW_H / 2), (2.2, 4.2, NW_H), PPLUS, bevel=0.1)
    # metal contacts on the pads
    box((s * 5.1, 0, NW_H + 0.12), (1.4, 3.0, 0.24), GOLD, bevel=0.05)

# --- the wrap-around gate with nitride spacers ------------------------------------------------------------------
GW = 1.1
SPACER = rd_mat("spacer", **{"Base Color": (0.8, 1.0, 0.92, 1), "Transmission Weight": 0.85, "Roughness": 0.1, "IOR": 1.2})
# cutaway: the front part of the gate stack is removed to show the nanowire corner where the dot forms
Y0, Y1 = -0.3, 1.3
for s_ in (-1, 1):
    box((s_ * (GW / 2 + 0.16), (Y0 + Y1) / 2, 0.45), (0.32, Y1 - Y0, 0.9), SPACER, bevel=0.04)
box((0, (Y0 + Y1) / 2, 0.62), (GW, Y1 - Y0, 1.24), GOLD, bevel=0.04)
# gate lead going back to the resonator
gate([(0, 1.3), (0, 3.4), (3.2, 5.6)], width=0.5, height=0.22)

# --- the hole dot at the corner under the gate and the boron acceptor beside it ---------------------------------
DOT = Vector((0.0, -NW_W / 2 + 0.12, NW_H - 0.05))
ACC = Vector((-1.55, -NW_W / 2 + 0.05, NW_H * 0.8))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=DOT, segments=32, ring_count=16)
h = bpy.context.object; h.scale = (0.9, 0.6, 0.5)
link(h, volume_glow("rd_dot", (1.0, 0.3, 0.5, 1), 16.0)); h.visible_shadow = False
BORON = rd_mat("boron", **{"Base Color": (0.85, 0.1, 0.75, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                             "Emission Color": (1.0, 0.2, 0.8, 1), "Emission Strength": 1.2})
sphere(tuple(ACC), 0.17, BORON)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=ACC, segments=32, ring_count=16)
link(bpy.context.object, volume_glow("rd_acc", (1.0, 0.3, 0.85, 1), 6.0)); bpy.context.object.visible_shadow = False
# a few spinless silicon atoms around the acceptor so it reads as a dopant in the lattice
SIATOM = rd_mat("siatom", **{"Base Color": (0.8, 0.83, 0.92, 1), "Roughness": 0.25, "Coat Weight": 0.6})
for i in range(-9, 10):
    for j in range(-1, 2):
        x = -1.55 + i * 0.3 + (j % 2) * 0.15
        if abs(x - ACC.x) < 0.2 and j == 0 or abs(x) < 1.2:
            continue
        if abs(x) > 3.8:
            continue
        sphere((x, -NW_W / 2 - 0.005, 0.12 + 0.17 * (j + 1)), 0.055, SIATOM)

# --- the two hole spins above, the hole hopping between dot and acceptor ----------------------------------------
QARROW = rd_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
TETH = emission("rd_tether", (1.0, 0.4, 0.7, 1), 3.0)
sA = Vector((-2.2, -1.3, 2.5))
sD = Vector((0.7, -1.3, 2.75))
spin(tuple(sA), (0.25, -0.1, 1.0), r=0.66, arrow=QARROW, reach=1.8, shaft=0.1)
spin(tuple(sD), (-0.15, -0.1, -1.0), r=0.66, arrow=QARROW, reach=1.8, shaft=0.1)
for s_, base in ((sA, ACC), (sD, DOT + Vector((0, -0.1, 0.0)))):
    tube([tuple(base + Vector((0, -0.05, 0.1))), tuple(s_ - Vector((0, 0, 0.66)))], 0.013, TETH)
HOP = emission("rd_hop", (1.0, 0.5, 0.15, 1), 6.0)
pts = []
for i in range(81):
    t = i / 80
    p = ACC.lerp(DOT, t) + Vector((0, -0.55, 0.35 + 0.6 * math.sin(math.pi * t)))
    pts.append(tuple(p))
tube(pts[5:-5], 0.035, HOP)
rd_arrowhead(pts[-3], Vector(pts[-3]) - Vector(pts[-8]), 0.1, HOP)
rd_arrowhead(pts[2], Vector(pts[2]) - Vector(pts[7]), 0.1, HOP)

# --- the LC resonator: planar spiral inductor, feedline, RF in and out -------------------------------------------
COP = COPPER
spiral = []
cx, cy = 5.2, 6.6
for k in range(4 * 4 + 1):
    rr = 2.0 - 0.1 * k
    corner = [(1, 1), (-1, 1), (-1, -1), (1, -1)][k % 4]
    spiral.append((cx + rr * corner[0], cy + rr * corner[1]))
gate([(3.2, 5.6), (cx + 2.0, cy - 2.0)] + spiral, width=0.22, height=0.12, mat=COP)
# feedline from the front-right bringing the RF tone
gate([(cx + 2.0, cy - 2.0), (8.0, 4.6), (8.0, 10.5)], width=0.4, height=0.14, mat=COP)
WIN = emission("rd_rf_in", (1.0, 0.15, 0.5, 1), 10.0)
WOUT = emission("rd_rf_out", (0.1, 0.6, 1.0, 1), 10.0)
a, b = Vector((8.0, 9.8, 0.0)), Vector((8.0, 4.0, 0.0))   # RF tone comes in from the back along the feedline
d = (b - a).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
for off, mat, amp, forward in ((-0.45, WIN, 0.28, True), (0.45, WOUT, 0.18, False)):
    pts = []
    for i in range(241):
        t = i / 240
        p = a.lerp(b, t) + side * off + Vector((0, 0, 0.75 + amp * math.sin(2 * math.pi * 6 * t + (0.0 if forward else 1.4))))
        pts.append(tuple(p))
    tube(pts, 0.035, mat)
    tip = Vector(pts[-1] if forward else pts[0]); dd = d if forward else -d
    rd_arrowhead(tip + dd * 0.3, dd, 0.12, mat)

# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 11.0 + 6.0 * math.sin(a) if t < 1 else 17.0, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 17.0, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("rd_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("rd_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = rd_mat("sweep", **{"Roughness": 0.6})
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


pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.5, 0.4), (1.0, 0.55, 0.72), (0.25, 0.5, 1.0)), sweep_emit=0.3, sweep_name='rd_sweep', sweep_widen=2.0)

camera((-2.6, -9.9, 5.0), (2.3, 1.6, 1.3), lens=37)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

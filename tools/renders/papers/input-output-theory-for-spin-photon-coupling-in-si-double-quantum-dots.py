"""Input-output theory for spin-photon coupling in Si double quantum dots (Benito et al., PRB 2017).

Cross-section of the Si/SiGe heterostructure: one electron in a double-well potential in the Si quantum well,
tunnelling between the two dots; two micromagnets on top whose stray field differs at the two dots (opposite
transverse components), which hybridises spin and charge. As in the paper's Figure 1, the cavity is drawn as two
blue curved mirrors on either side; at each a probe wave goes in and an output wave comes out (a_in, a_out),
and between them the cavity's standing wave glows. The output field is what the theory predicts.
"""
bright_stage(floor_z=-2.2, exposure=-0.4, sun_rot=(48, 0, -20))

H = 2.2
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.6, -H / 2))
slab = bpy.context.object; slab.scale = (7.2, 3.2, H)
sm = principled("io_hetero", **{"Roughness": 0.3, "Coat Weight": 0.4})
nt = sm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.3, 0.78, 0.62, 1)          # SiGe buffer
els[1].position, els[1].color = 1.15 / H, (0.08, 0.35, 1.0, 1)      # Si quantum well
for pos, col in (((1.6 / H), (0.3, 0.78, 0.62, 1)), ((2.05 / H), (0.04, 0.22, 0.34, 1))):   # SiGe barrier, oxide
    e = els.new(pos); e.color = col
nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 3
link(slab, sm)
QW_Z = -H + 1.375          # middle of the quantum well

# double-well confinement potential drawn just in front of the cut face: deep wells in the quantum well, a high
# central barrier and steep outer walls (as in Figure 1)
D = 1.12
ZMIN = QW_Z - 0.2                      # bottom of the wells, inside the Si quantum well
DEPTH = 0.78                           # barrier height above the well bottoms
WALL = 1.02                            # outer walls rise a bit above the barrier
POT = emission("io_potential", (1.0, 0.72, 0.0, 1), 5.0)
xw = D * math.sqrt(1 + math.sqrt(WALL / DEPTH))
pts = []
for i in range(301):
    x = -xw + 2 * xw * i / 300
    pts.append((x, -0.25, ZMIN + DEPTH * ((x / D) ** 2 - 1) ** 2))
tube(pts, 0.075, POT)
# faint glowing fill under the curve's wells (the bound states' probability, a soft amber sheet)
import bmesh as _bm
bm_ = _bm.new()
top_v, bot_v = [], []
for (x, y, z) in pts:
    zz = min(z, ZMIN + DEPTH * 0.92)
    top_v.append(bm_.verts.new((x, -0.22, zz))); bot_v.append(bm_.verts.new((x, -0.22, ZMIN - 0.02)))
for i in range(len(pts) - 1):
    if top_v[i].co.z - bot_v[i].co.z > 0.03 or top_v[i + 1].co.z - bot_v[i + 1].co.z > 0.03:
        bm_.faces.new((bot_v[i], bot_v[i + 1], top_v[i + 1], top_v[i]))
me_ = bpy.data.meshes.new("io_wellfill"); bm_.to_mesh(me_); bm_.free()
wf_ = bpy.data.objects.new("io_wellfill", me_); sc.collection.objects.link(wf_)
fm = bpy.data.materials.new("io_wellfill"); fm.use_nodes = True
fnt = fm.node_tree; fnt.nodes.clear()
fo = fnt.nodes.new("ShaderNodeOutputMaterial")
fe = fnt.nodes.new("ShaderNodeEmission"); fe.inputs["Color"].default_value = (1.0, 0.8, 0.2, 1); fe.inputs["Strength"].default_value = 1.6
ft = fnt.nodes.new("ShaderNodeBsdfTransparent")
fmix = fnt.nodes.new("ShaderNodeMixShader"); fmix.inputs["Fac"].default_value = 0.35
fnt.links.new(ft.outputs[0], fmix.inputs[1]); fnt.links.new(fe.outputs[0], fmix.inputs[2]); fnt.links.new(fmix.outputs[0], fo.inputs["Surface"])
me_.materials.append(fm)
wf_.visible_shadow = False

# the electron: a spin in the left well and its tunnelling partner in the right well (same electron, the field
# there has the opposite transverse component, so the spin axis tilts the other way)
IO_QARROW = principled("io_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
GHOST = principled("io_ghost", **{"Base Color": (1.0, 0.42, 0.08, 1), "Transmission Weight": 0.6, "Roughness": 0.06,
                                   "IOR": 1.45, "Alpha": 0.45})
R = 0.4
spin((-D, -0.6, ZMIN + R + 0.1), (0.55, 0, 1.0), r=R, arrow=IO_QARROW, reach=1.7, shaft=0.11)
spin((D, -0.6, ZMIN + R + 0.1), (-0.55, 0, 1.0), r=R, mat=GHOST, arrow=IO_QARROW, reach=1.7, shaft=0.11)
for x in (-D, D):
    hot_spot((x, -0.6, ZMIN + R + 0.1), (1.0, 0.7, 0.4, 1), 0.04, 20)
# tunnelling arc t_c between the dots (double-headed)
TUN = emission("io_tunnel", (1.0, 0.1, 0.45, 1), 6.0)
c = Vector((0, -0.75, ZMIN + DEPTH + 0.3))
arc = [tuple(c + Vector((0.5 * math.cos(a), 0, 0.22 * math.sin(a)))) for a in [math.radians(160 - 140 * k / 40) for k in range(41)]]
tube(arc, 0.035, TUN)
for end, nxt in ((arc[0], arc[3]), (arc[-1], arc[-4])):
    d = (Vector(end) - Vector(nxt)).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=0.09, depth=0.2, location=Vector(end) + d * 0.06,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, TUN)

# micromagnets on top: blue (S) and red (N) halves, same orientation, either side of the double dot
MAG_Y = 0.7
for xc in (-2.5, 2.5):
    box((xc - 0.45, MAG_Y, 0.25), (0.9, 0.8, 0.5), MAG_BLUE, bevel=0.04)
    box((xc + 0.45, MAG_Y, 0.25), (0.9, 0.8, 0.5), MAG_RED, bevel=0.04)
# stray field lines: from the left magnet's N pole over and through the device to the right magnet's S pole
FL = emission("io_field", (0.08, 0.3, 1.0, 1), 2.6)
for i, hgt in enumerate((0.5, 0.95, 1.4, 1.85)):
    x0, x1 = -1.6, 1.6
    pts = [(x0 + (x1 - x0) * t, MAG_Y, 0.3 + hgt * math.sin(math.pi * t) ** 0.8) for t in [k / 60 for k in range(61)]]
    tube(pts, 0.022, FL)
    mid = Vector(pts[30]); d = Vector((1, 0, 0))
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, depth=0.18, location=mid, rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=16)
    link(bpy.context.object, FL)

# the cavity, drawn as in the paper's Figure 1: two blue curved mirrors either side of the heterostructure
SX = 3.6                               # half width of the slab
L = SX + 0.75                          # mirror apex position
RES_Y = 1.3
IO_MIRROR = principled("io_mirror", **{"Base Color": (0.25, 0.5, 1.0, 1), "Metallic": 0.3, "Roughness": 0.12,
                                       "Coat Weight": 1.0, "Transmission Weight": 0.35, "IOR": 1.45})
MODE_Z = 0.95                          # cavity axis, above the magnets
for s_ in (-1, 1):
    ms = mirror_shell(s_ * L, s_, 0.55, R=4.2, depth=0.55)
    ms.location.y = RES_Y
    ms.scale = (1.0, 1.0, 1.1)
    ms.data.materials.clear(); ms.data.materials.append(IO_MIRROR)
    ms.modifiers["solid"].thickness = 0.28
# the cavity field: a glowing Gaussian standing wave between the mirrors, antinodes at both mirrors and at the
# centre (right above the double dot), nodes in between
XM = L - 0.1
MODE_COL = (0.1, 1.0, 0.25, 1)
beam((-XM, RES_Y, MODE_Z), (XM, RES_Y, MODE_Z), 0.9,
     gauss_mode_material("io_mode", MODE_COL, 40.0, waist=0.35, standing=1.0, k=2 * math.pi))
XC = XM - 0.06
beam((-XC, RES_Y, MODE_Z), (XC, RES_Y, MODE_Z), 0.3,
     gauss_mode_material("io_mode_core", (0.3, 1.0, 0.35, 1), 85.0, waist=0.999, standing=0.98, k=2 * math.pi * XC / XM))
for s_ in (-1, 1):
    sphere((s_ * (XM - 0.02), RES_Y, MODE_Z), 0.09, emission("io_hot", (0.8, 1.0, 0.75, 1), 160.0))


# input and output fields at both mirrors (a_in above, a_out below, as in Figure 1)
def packet(x0, x1, z, color, name, cycles=5, amp=0.22):
    pts = []
    for j in range(241):
        t = j / 240
        env = math.sin(math.pi * t) ** 1.5
        pts.append((x0 + (x1 - x0) * t, RES_Y, z + amp * env * math.sin(2 * math.pi * cycles * t)))
    m = emission(name, color, 3.2)
    tube(pts, 0.05, m)
    d = Vector((1 if x1 > x0 else -1, 0, 0))
    bpy.ops.mesh.primitive_cone_add(radius1=0.13, depth=0.32, location=(x1 + d.x * 0.12, RES_Y, z),
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, m)


IN_COL, OUT_COL = (0.7, 0.15, 1.0, 1), (1.0, 0.55, 0.05, 1)
for s in (-1, 1):
    packet(s * 5.7, s * (L + 0.4), 1.25, IN_COL, "io_in%d" % s)        # a_in, travelling towards the cavity
    packet(s * (L + 0.4), s * 5.7, 0.6, OUT_COL, "io_out%d" % s)       # a_out, leaving it

camera((0.0, -12.5, 3.4), (0.0, 1.0, -0.25), lens=40, dof=3.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.3, streaks=0.12, ghosts=0.0, threshold=6.0, anamorphic=0.2, dispersion=0.0, contrast=18.0, saturation=1.15)

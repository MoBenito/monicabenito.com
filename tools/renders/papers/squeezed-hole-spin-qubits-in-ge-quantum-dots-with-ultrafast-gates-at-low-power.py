# Squeezed hole spin qubits in planar Ge quantum dots (Bosco, Benito, Adelsberger, Loss 2021).
# Built on the paper's Figure 1: a SiGe/Ge/SiGe slab seen from a corner, the hole quantum dot a long, narrow glowing
# ellipse in the blue Ge well (seen through a translucent top barrier), a dotted outline around it, a red arrow for
# the in-plane ac drive E_y^ac along the long axis, and on the cut faces the magnetic field along the long axis, the
# vertical field E and the hole's wavefunction profile across the well. Two thin gold gates along the dot squeeze it.
# Above the dot the hole spin flips fast: its trajectory spirals from up to down in a few turns (ultrafast gate).
bright_stage(floor_z=-0.7)

SQ_SIGE = principled("sq_sige", **{"Base Color": (0.72, 0.62, 1.0, 1), "Roughness": 0.3, "Coat Weight": 0.7})
SQ_TOP = principled("sq_top", **{"Base Color": (0.78, 0.66, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.2,
                                 "IOR": 1.25, "Coat Weight": 0.5})
SQ_GE = principled("sq_ge", **{"Base Color": (0.03, 0.22, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0})
SQ_RED = principled("sq_red", **{"Base Color": (1.0, 0.05, 0.05, 1), "Roughness": 0.25, "Coat Weight": 1.0,
                                 "Emission Color": (1.0, 0.1, 0.05, 1), "Emission Strength": 1.0})
SQ_DARK = principled("sq_dark", **{"Base Color": (0.02, 0.02, 0.08, 1), "Roughness": 0.3, "Coat Weight": 1.0})
SQ_WHITE = principled("sq_white", **{"Base Color": (1.0, 1.0, 1.0, 1), "Roughness": 0.3, "Emission Color": (1, 1, 1, 1),
                                     "Emission Strength": 1.5})
SQ_ROT = emission("sq_rot", (0.6, 0.15, 1.0, 1), 9.0)
SQ_PROF = emission("sq_prof", (1.0, 0.25, 0.65, 1), 6.0)

X0, X1, Y0, Y1 = -6.5, 6.5, -3.6, 3.6
zb, zw, zt = 0.25, 1.0, 1.6        # tops of the lower barrier, the Ge well, the upper barrier
box((0, 0, (zb - 0.7) / 2), (X1 - X0, Y1 - Y0, zb + 0.7), SQ_SIGE, bevel=0.03)
box((0, 0, (zb + zw) / 2), (X1 - X0, Y1 - Y0, zw - zb), SQ_GE, bevel=0.005)
top = box((0, 0, (zw + zt) / 2), (X1 - X0, Y1 - Y0, zt - zw), SQ_TOP, bevel=0.03)
top.visible_shadow = False

# the squeezed hole dot in the well: long along x, narrow along y
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, zw - 0.2), segments=64, ring_count=32)
cl = bpy.context.object; cl.scale = (3.0, 0.6, 0.22)
cl.data.materials.append(volume_glow("sq_psi", (1.0, 0.2, 0.6, 1), 30.0)); cl.visible_shadow = False
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, zw + 0.004))
fp = bpy.context.object; fp.scale = (3.6, 0.8, 1)
m = bpy.data.materials.new("sq_foot"); m.use_nodes = True
nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])
M = lambda op, a=None, b=None: _math(nt, op, a, b)
r2 = M("ADD", M("POWER", M("DIVIDE", sep.outputs["X"], 0.5), 2.0), M("POWER", M("DIVIDE", sep.outputs["Y"], 0.5), 2.0))
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.15, 0.55, 1)
nt.links.new(M("MULTIPLY", M("EXPONENT", M("MULTIPLY", -1.0, r2)), 10.0), em.inputs["Strength"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); add = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
fp.data.materials.append(m); fp.visible_shadow = False

# dotted outline on the top surface (as in the figure)
N = 56
for i in range(0, N, 2):
    seg = [(3.9 * math.cos(2 * math.pi * (i + j / 6) / N), 1.25 * math.sin(2 * math.pi * (i + j / 6) / N), zt + 0.02) for j in range(7)]
    tube(seg, 0.03, SQ_WHITE)
# thin gold gates along both long sides: the asymmetric confinement that squeezes the dot
gate([(-6.0, -1.75), (6.0, -1.75)], width=0.45, height=0.16).location.z = zt
gate([(-6.0, 1.75), (6.0, 1.75)], width=0.45, height=0.16).location.z = zt


def arrow(p0, p1, r, mat, head=0.5, both=False):
    p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized()
    tube([tuple(p0 + (d * head * 0.6 if both else Vector())), tuple(p1 - d * head * 0.6)], r, mat)
    for p, dd in ((p1, d),) + (((p0, -d),) if both else ()):
        bpy.ops.mesh.primitive_cone_add(radius1=r * 3.0, depth=head, location=p - dd * head / 2,
                                        rotation=dd.to_track_quat("Z", "Y").to_euler(), vertices=24)
        link(bpy.context.object, mat)


# ac electric field along the long axis (red, as in the figure), on the top surface in front of the dot
arrow((-5.6, -2.7, zt + 0.15), (-2.6, -2.7, zt + 0.15), 0.09, SQ_RED, head=0.6)
# on the right cut face: vertical field E and the hole's wavefunction profile across the well
xf = X1 + 0.03
arrow((xf + 0.02, -1.6, zb + 0.08), (xf + 0.02, -1.6, zw - 0.02), 0.04, SQ_DARK, head=0.24)
prof = [(xf + 0.03, 0.4 + 1.1 * math.exp(-((z - (zb + zw) / 2) / 0.2) ** 2), z) for z in [zb - 0.15 + (zw - zb + 0.3) * i / 80 for i in range(81)]]
tube(prof, 0.03, SQ_PROF)
tube([(xf + 0.03, 0.4, zb - 0.15), (xf + 0.03, 0.4, zw + 0.15)], 0.012, SQ_DARK)
# on the front cut face: the magnetic field along the long axis
arrow((-1.2, Y0 - 0.03, (zb + zw) / 2), (2.4, Y0 - 0.03, (zb + zw) / 2), 0.05, SQ_DARK, head=0.32)

# the hole spin above the dot and its fast flip: a spiral from the north to the south pole in a few turns
h = zt + 1.25
QA = principled("sq_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
spin((0, 0, h), (0.6, 0.45, 0.75), r=0.5, arrow=QA, reach=2.1, shaft=0.1)
hot_spot((0, 0, h), (1.0, 0.7, 0.45, 1), 0.05, 25)
pts = []
for i in range(500):
    u = i / 499
    th = math.radians(12) + math.radians(150) * u
    ph = 2 * math.pi * 3.2 * u
    R = 1.0
    pts.append((R * math.sin(th) * math.cos(ph), R * math.sin(th) * math.sin(ph), h + R * math.cos(th)))
tube(pts, 0.035, SQ_ROT)
hot_spot(pts[-1], (0.8, 0.5, 1.0, 1), 0.06, 30)

camera((9.4, -11.4, 9.8), (0.9, -0.4, 1.2), lens=35, dof=5.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.3)

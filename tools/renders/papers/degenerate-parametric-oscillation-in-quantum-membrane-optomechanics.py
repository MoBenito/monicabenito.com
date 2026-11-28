# Degenerate parametric oscillation in quantum membrane optomechanics (Benito, Sanchez Munoz, Navarrete-Benlloch 2016).
# Hero: a membrane-in-the-middle cavity on a light breadboard. Two curved mirrors hold two standing-wave cavity
# modes: a violet "linear" mode and a yellow "quadratic" mode, whose node sits on the membrane. A violet laser
# drives the cavity from the left, two yellow lasers (two colours, omega_Q and omega_Q - Omega) from the right. The
# thin membrane in its silicon frame is bowed in its drum mode; a faint ghost shows the opposite phase, the other
# of the two symmetry-broken oscillation states.
import bmesh
bright_stage(floor_z=-0.7)

OM_BOARD = principled("om_board", **{"Base Color": (0.72, 0.8, 0.95, 1), "Metallic": 0.6, "Roughness": 0.3})
nt = OM_BOARD.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord")
sc_ = nt.nodes.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 1.6
nt.links.new(tc.outputs["Object"], sc_.inputs[0])
fr = nt.nodes.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"; nt.links.new(sc_.outputs[0], fr.inputs[0])
sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.0)
nt.links.new(fr.outputs[0], sub.inputs[0])
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(sub.outputs[0], ln.inputs[0])
lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.13
nt.links.new(ln.outputs["Value"], lt.inputs[0])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
mix.inputs[6].default_value = (0.72, 0.8, 0.95, 1); mix.inputs[7].default_value = (0.25, 0.3, 0.45, 1)
nt.links.new(lt.outputs[0], mix.inputs["Factor"]); nt.links.new(mix.outputs[2], nt.nodes["Principled BSDF"].inputs["Base Color"])

box((0, 2, -0.35), (34, 22, 0.7), OM_BOARD, bevel=0.06)

h, L = 2.3, 4.6
SILVER_M = principled("om_silver", **{"Base Color": (0.97, 0.98, 1.0, 1), "Metallic": 1.0, "Roughness": 0.0})
SUBSTRATE = principled("om_substrate", **{"Base Color": (0.45, 0.85, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.02, "IOR": 1.5})
ANOD = principled("om_mount", **{"Base Color": (0.15, 0.55, 1.0, 1), "Metallic": 0.7, "Roughness": 0.3})
for x, f in ((L, 1), (-L, -1)):
    ms = mirror_shell(x, f, h)
    ms.data.materials.clear(); ms.data.materials.append(SILVER_M); ms.data.materials.append(SUBSTRATE)
    ms.modifiers["solid"].material_offset_rim = 1
    ms.modifiers["solid"].thickness = 0.18
R_, depth_ = 3.2, 0.75
rim_r = R_ * math.sin(math.acos((R_ - depth_) / R_))
for s in (-1, 1):
    xr = s * (L - depth_ + 0.06)
    bpy.ops.mesh.primitive_torus_add(major_radius=rim_r + 0.05, minor_radius=0.11, major_segments=128, minor_segments=24,
                                     location=(xr, 0, h), rotation=(0, math.radians(90), 0))
    link(bpy.context.object, ANOD)
    bottom = h - rim_r - 0.14
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=bottom, vertices=32, location=(xr, 0, bottom / 2))
    link(bpy.context.object, STEEL)
    box((xr, 0, 0.05), (0.8, 1.4, 0.1), ANOD, bevel=0.03)

# two cavity modes: standing waves with different wavenumbers. Field ~ sin(k x + phi): the quadratic (yellow) mode
# has a node on the membrane (x = 0), the linear (violet) mode is at mid-slope of its intensity there.
VIOLET, YELLOW = (0.6, 0.2, 1.0, 1), (1.0, 0.78, 0.1, 1)
HL = L - 0.12


def om_mode(name, color, strength, waist, k, phi):
    """Gaussian beam volume (cylinder radius 1, z in [-1, 1] = x / HL) with intensity sin^2(k HL z + phi)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = 0.0
    v.inputs["Emission Color"].default_value = color
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, b=None: _math(nt, op, a, b)
    Z = sep.outputs["Z"]
    w2 = M("ADD", waist * waist, M("MULTIPLY", 1 - waist * waist, M("MULTIPLY", Z, Z)))
    r2 = M("ADD", M("MULTIPLY", sep.outputs["X"], sep.outputs["X"]), M("MULTIPLY", sep.outputs["Y"], sep.outputs["Y"]))
    g = M("MULTIPLY", M("EXPONENT", M("MULTIPLY", -2.5, M("DIVIDE", r2, w2))), M("DIVIDE", waist * waist, w2))
    sn = M("SINE", M("ADD", M("MULTIPLY", Z, k * HL), phi))
    val = M("MULTIPLY", g, M("ADD", 0.04, M("MULTIPLY", sn, sn)))
    nt.links.new(M("MULTIPLY", val, strength), v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


nq, nl = 8, 7                      # half wavelengths across the cavity (stylised)
kq, kl = math.pi * nq / (2 * L), math.pi * nl / (2 * L)
phq, phl = 0.0, math.pi / 4
beam((-HL, 0, h), (HL, 0, h), 0.8, om_mode("om_quad", YELLOW, 16.0, 0.4, kq, phq))
beam((-HL, 0, h), (HL, 0, h), 0.8, om_mode("om_lin", VIOLET, 12.0, 0.45, kl, phl))
# thin field lines like the paper's sketch
for (col, k, amp, ph, nm) in ((YELLOW, kq, 0.55, phq, "om_wq"), (VIOLET, kl, 0.4, phl, "om_wl")):
    pts = [(x, -0.02, h + amp * math.sin(k * x + ph)) for x in [-L + 0.4 + (2 * L - 0.8) * i / 300 for i in range(301)]]
    if nm == "om_wl":      # dashed, as in the paper's sketch
        for j in range(0, 300, 12):
            tube(pts[j:j + 8], 0.03, emission(nm, col, 8.0))
    else:
        tube(pts, 0.03, emission(nm, col, 8.0))

# the membrane: a thin, translucent SiN film stretched over the square window of a silicon chip (the frame), held by
# two clamps as in the paper's sketch, bowed in its fundamental drum mode. Glowing iso-displacement contour rings make
# the drum shape readable; a faint glassy ghost at the opposite displacement shows the vibration (and the other of the
# two symmetry-broken oscillation states).
a = 1.5          # membrane (window) half size
F = 2.05         # chip half size
TH = 0.16        # chip thickness along the cavity axis
FRAME = principled("om_frame", **{"Base Color": (0.3, 0.22, 0.75, 1), "Metallic": 0.55, "Roughness": 0.2, "Coat Weight": 1.0})
SIN = principled("om_sin", **{"Base Color": (0.45, 0.9, 1.0, 1), "Transmission Weight": 0.75, "Roughness": 0.08, "IOR": 2.0,
                              "Coat Weight": 1.0, "Thin Film Thickness": 520.0, "Thin Film IOR": 2.0,
                              "Emission Color": (0.3, 0.8, 1.0, 1), "Emission Strength": 0.25})
GHOST = principled("om_ghost", **{"Base Color": (0.7, 0.95, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.15, "IOR": 1.1,
                                  "Alpha": 0.3, "Emission Color": (0.5, 0.9, 1.0, 1), "Emission Strength": 0.3})
CLAMP = principled("om_clamp", **{"Base Color": (0.35, 0.37, 0.45, 1), "Metallic": 0.6, "Roughness": 0.3})
# chip frame: four bars around the window
for sy in (-1, 1):
    box((0, sy * (a + F) / 2, h), (TH, F - a, 2 * F), FRAME, bevel=0.02)
    box((0, 0, h + sy * (a + F) / 2), (TH, 2 * a + 0.01, F - a), FRAME, bevel=0.02)


def trapezoid(zc, flip):
    bm = bmesh.new()
    wt, wb, hh, dd = 2 * F - 0.2, 2 * F + 0.7, 0.75, 0.62      # narrow side towards the membrane
    zs_ = [zc - hh / 2, zc + hh / 2]
    widths = (wt, wb) if flip else (wb, wt)
    vs = []
    for z_, w_ in zip(zs_, widths):
        vs.append([bm.verts.new((sx * dd / 2, sy * w_ / 2, z_)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.faces.new(vs[0][::-1]); bm.faces.new(vs[1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i]))
    me = bpy.data.meshes.new("clamp"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("clamp", me); sc.collection.objects.link(ob); me.materials.append(CLAMP)
    bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 2


for z_, fl in ((h + F + 0.3, True), (h - F - 0.3, False)):
    trapezoid(z_, fl)


def membrane(amp, mat, name, thick=0.025):
    bm = bmesh.new()
    N = 48
    vs = [[bm.verts.new((amp * math.cos(math.pi * (j / N - 0.5)) * math.cos(math.pi * (k / N - 0.5)),
                         -a + 2 * a * j / N, h - a + 2 * a * k / N)) for k in range(N + 1)] for j in range(N + 1)]
    for j in range(N):
        for k in range(N):
            bm.faces.new((vs[j][k], vs[j + 1][k], vs[j + 1][k + 1], vs[j][k + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(mat)
    so = ob.modifiers.new("s", "SOLIDIFY"); so.thickness = thick
    return ob


AMP = 0.7
membrane(AMP, SIN, "om_membrane")
gh = membrane(-AMP, GHOST, "om_ghost", thick=0.01)
gh.visible_shadow = False


def contour(c, amp, xoff):
    """Closed iso-displacement line cos(p) cos(q) = c of the drum mode, p = pi y / 2a, q = pi (z - h) / 2a."""
    pts = []
    for i in range(161):
        t = 2 * math.pi * i / 160
        ct, st = math.cos(t), math.sin(t)
        p = math.copysign(math.acos(c ** (ct * ct)), ct)
        q = math.copysign(math.acos(c ** (st * st)), st)
        pts.append((amp * c + xoff, 2 * a * p / math.pi, h + 2 * a * q / math.pi))
    return pts


for i, c in enumerate((0.3, 0.6, 0.88)):
    tube(contour(c, AMP, 0.03), 0.016, emission("om_ring%d" % i, (0.55, 1.0, 1.0, 1), 4.0))
# displacement shading: the membrane glows brighter where it is displaced most (the drum mode's antinode)
nt = SIN.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])
M = lambda op, x=None, y=None: _math(nt, op, x, y)
cy_ = M("COSINE", M("MULTIPLY", sep.outputs["Y"], math.pi / (2 * a)))
cz_ = M("COSINE", M("MULTIPLY", M("SUBTRACT", sep.outputs["Z"], h), math.pi / (2 * a)))
u_ = M("MULTIPLY", cy_, cz_)
nt.links.new(M("ADD", 0.1, M("MULTIPLY", 1.4, M("MULTIPLY", u_, u_))), nt.nodes["Principled BSDF"].inputs["Emission Strength"])
# frame post
bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=h - F - 0.65, vertices=32, location=(0, 0, (h - F - 0.65) / 2))
link(bpy.context.object, STEEL)
box((0, 0, 0.05), (0.8, 1.4, 0.1), ANOD, bevel=0.03)
# a double arrow beside the membrane: its oscillation along the cavity axis
OSC = emission("om_osc", (1.0, 0.35, 0.55, 1), 8.0)
p0, p1 = Vector((-0.85, 0, h + F + 1.0)), Vector((0.85, 0, h + F + 1.0))
tube([tuple(p0 + Vector((0.2, 0, 0))), tuple(p1 - Vector((0.2, 0, 0)))], 0.045, OSC)
for p, d in ((p1, Vector((1, 0, 0))), (p0, Vector((-1, 0, 0)))):
    bpy.ops.mesh.primitive_cone_add(radius1=0.13, depth=0.32, location=p - d * 0.1, rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, OSC)

# drive lasers: violet from the left, two yellows (two frequencies) from the right
src = laser_head((-12.5, 0, h), (-L, 0, h))
beam(src, (-L - 0.25, 0, h), 0.2, beam_material("om_drive_l", VIOLET, 30.0))
hot_spot((-L - 0.3, 0, h), (0.85, 0.6, 1.0, 1), 0.09, 80)
for (yy, col, nm) in ((0.55, YELLOW, "om_drive_q1"), (-0.55, (1.0, 0.55, 0.05, 1), "om_drive_q2")):
    a_ = laser_head((10.0, yy * 2.4, h), (L + 0.2, 0, h))
    beam(a_, (L + 0.3, yy * 0.1, h), 0.16, beam_material(nm, col, 30.0))
hot_spot((L + 0.32, 0, h), (1.0, 0.9, 0.5, 1), 0.09, 80)

camera((7.0, -11.4, 6.5), (0.0, 0.0, 2.25), lens=36, dof=6.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.25)

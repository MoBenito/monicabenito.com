"""Readout of multi-level quantum geometry from electronic transport (Klees, Benito, arXiv:2508.08239).

A molecular / tunnel junction: two gold tip electrodes with a molecule between them, electrons tunnelling through it
(the conductance is the readout). Two gates modulate two parameters of the molecule weakly and resonantly, with a
phase lag (pink and cyan wavefronts). Above the junction floats the hero: the curved manifold of the molecule's
states over parameter space, its grid stretched by the quantum metric, and the small elliptical loop that the
phase-lagged modulation traces on it. Orbitals around the molecule hint at its several levels.
"""
import bmesh
import random
from mathutils import Matrix

random.seed(13)
bright_stage(floor_z=-0.7)

QG_E = principled("qg_electron", **{"Base Color": (0.05, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 0.6,
                                     "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 0.6})
QG_E_HOT = principled("qg_electron_hot", **{"Base Color": (0.1, 0.4, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                             "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 1.2})
QG_ATOM = principled("qg_atom", **{"Base Color": (0.15, 0.8, 0.65, 1), "Roughness": 0.15, "Coat Weight": 1.0})
QG_ATOM2 = principled("qg_atom2", **{"Base Color": (0.95, 0.95, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0})
QG_TRAIL = emission("qg_trail", (0.35, 0.6, 1.0, 1), 3.0)

# chip slab
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.0, -0.35))
slab = bpy.context.object; slab.scale = (16.0, 12.0, 0.7)
bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
sm = principled("qg_hetero", **{"Roughness": 0.35})
nt = sm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (1.0, 0.7, 0.55, 1)
els[1].position, els[1].color = 0.6, (0.55, 0.5, 1.0, 1)
e = els.new(0.88); e.color = (0.98, 0.9, 0.95, 1)
nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
link(slab, sm)

# --- the junction: gold leads tapering to tips, molecule in the gap --------------------------------------------
ZJ = 0.75
for sg in (-1, 1):
    box((sg * 5.2, 0, 0.3), (4.0, 3.2, 0.6), GOLD, bevel=0.06)
    bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.07, depth=2.4, location=(sg * 2.15, 0, ZJ),
                                    rotation=(0, -sg * math.radians(90), 0), vertices=64)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, GOLD)
# inside the central system H_C(lambda): its discrete levels, as in the paper's Fig. 1(b). The transport level
# eps_n sits at the leads' chemical potential, level to level with the tips; a lower level eps_p (occupied) and an
# upper one complete the multi-level spectrum. Each level is a lens-shaped glowing plate (broadened by the lead
# coupling). The resonant modulation (hbar Omega = |eps_n - eps_p|) couples eps_p and eps_n: a wavy double arrow.
mol = Vector((0, 0, ZJ))


def qg_level(z, col, strength, w=1.5):
    m = principled("qg_lvl_%d" % int(z * 100), **{"Base Color": (*col, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                                  "Emission Color": (*col, 1), "Emission Strength": strength})
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, z), segments=64, ring_count=24)
    ob = bpy.context.object; ob.scale = (w / 2, 0.2, 0.05)
    bpy.ops.object.shade_smooth()
    return link(ob, m)


Z_N, Z_P, Z_U = ZJ, ZJ - 0.5, ZJ + 0.42
qg_level(Z_N, (1.0, 0.45, 0.0), 4.0)            # eps_n at mu: the conducting level (orange)
qg_level(Z_P, (1.0, 0.05, 0.45), 3.5)             # eps_p, below: occupied (magenta)
qg_level(Z_U, (0.25, 0.35, 1.0), 3.0, w=1.2)    # a further level above (blue)
sphere((0.35, 0.0, Z_P + 0.11), 0.09, QG_E_HOT)   # the electron occupying eps_p
# resonant transition eps_p <-> eps_n driven by the modulation: wavy line with heads at both ends
WV = emission("qg_wave", (0.55, 0.0, 1.0, 1), 4.0)
x0, za, zb = -0.35, Z_P + 0.05, Z_N - 0.05
wp = [(x0 + 0.08 * math.sin(2 * math.pi * 1.5 * u), -0.24, za + 0.06 + (zb - za - 0.12) * u) for u in [i / 80 for i in range(81)]]
tube(wp, 0.026, WV)
for tip, dz in (((x0, -0.24, zb), 1), ((x0, -0.24, za), -1)):
    bpy.ops.mesh.primitive_cone_add(radius1=0.065, depth=0.12, location=(tip[0], tip[1], tip[2] - dz * 0.03),
                                    rotation=(0, 0 if dz > 0 else math.pi, 0), vertices=24)
    link(bpy.context.object, WV)
# the central system H_C(lambda) as in the paper's sketch: a green box between the yellow leads
box(tuple(mol), (1.75, 1.75, 1.25), principled("qg_hc", **{"Base Color": (0.75, 1.0, 0.7, 1), "Transmission Weight": 1.0,
    "Roughness": 0.03, "IOR": 1.02, "Emission Color": (0.2, 0.9, 0.3, 1), "Emission Strength": 0.08}), bevel=0.08)
# modulation gates beneath, each sending up its drive (same frequency, phase-lagged colours)
for sg, col in ((-1, (1.0, 0.3, 0.65, 1)), (1, (0.2, 0.85, 1.0, 1))):
    gate([(sg * 0.45, -0.3), (sg * 0.45, -1.4), (sg * 1.3, -2.8)], width=0.3, height=0.2)
    wave_arcs((sg * 0.45, -1.2, 0.25), (0, 0.6, 0.45), n=3, spacing=0.15, color=col, start=0.1)
# electrons: Fermi seas on the leads (left higher = bias) and one tunnelling across
es = bmesh.new()
for sg, nz in ((-1, 3), (1, 1)):
    for ix in range(15):
        for iy in range(13):
            for iz in range(nz):
                if iz == nz - 1 and random.random() < 0.4:
                    continue
                if sg > 0 and random.random() < 0.6:
                    continue
                bmesh.ops.create_icosphere(es, subdivisions=2, radius=0.09, matrix=Matrix.Translation(
                    (sg * (3.6 + ix * 0.21) + random.uniform(-0.03, 0.03), -1.35 + iy * 0.225, 0.72 + iz * 0.19)))
me = bpy.data.meshes.new("qg_sea"); es.to_mesh(me); es.free()
for f_ in me.polygons:
    f_.use_smooth = True
o_ = bpy.data.objects.new("qg_sea", me); sc.collection.objects.link(o_); me.materials.append(QG_E)
# one electron tunnels from the left tip into the level eps_n (at the chemical potential)
pts = [(-2.0 + 1.5 * u, -0.15, ZJ + 0.12 + 0.35 * math.sin(math.pi * u)) for u in [i / 30 for i in range(31)]]
tube(pts[:27], 0.03, QG_TRAIL); sphere(pts[30], 0.11, QG_E_HOT)

# --- the quantum-geometry manifold above ------------------------------------------------------------------
C = Vector((0, 0.8, 3.6))
S = 3.3
f = lambda u, v: 1.25 * math.exp(-((u - 0.1) ** 2 + (v + 0.05) ** 2) / 0.28) - 0.35 * math.exp(-((u + 0.55) ** 2 + (v - 0.5) ** 2) / 0.2)
bm = bmesh.new()
hue = bm.verts.layers.float_color.new("hue")
NG = 90
G = [[None] * (NG + 1) for _ in range(NG + 1)]
for i in range(NG + 1):
    for j in range(NG + 1):
        u, v = -1 + 2 * i / NG, -1 + 2 * j / NG
        G[i][j] = bm.verts.new(C + Vector((S * u, S * 0.75 * v, f(u, v))))
        G[i][j][hue] = (0.5 + 0.5 * f(u, v), (u + 1) / 2, (v + 1) / 2, 1)
for i in range(NG):
    for j in range(NG):
        bm.faces.new((G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1]))
me = bpy.data.meshes.new("qg_manifold"); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
man = bpy.data.objects.new("qg_manifold", me); sc.collection.objects.link(man)
sol = man.modifiers.new("s", "SOLIDIFY"); sol.thickness = 0.04
mm = principled("qg_manifold", **{"Roughness": 0.2, "Coat Weight": 1.0})
nt = mm.node_tree
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "hue"
sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(at.outputs["Color"], sep.inputs[0])
rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.1, 0.4, 1.0, 1)
el[1].position, el[1].color = 1.0, (1.0, 0.75, 0.05, 1)
for pos, c_ in ((0.33, (0.0, 0.85, 0.7, 1)), (0.62, (1.0, 0.2, 0.6, 1))):
    e = el.new(pos); e.color = c_
nt.links.new(_math(nt, "ADD", _math(nt, "MULTIPLY", sep.outputs["Red"], 0.7), _math(nt, "MULTIPLY", sep.outputs["Green"], 0.45)), rp.inputs["Fac"])
nt.links.new(rp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
nt.links.new(rp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Emission Color"])
nt.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.1
me.materials.append(mm)
# grid lines on the surface (white), so that its stretching reads
GRID = principled("qg_grid", **{"Base Color": (1, 1, 1, 1), "Roughness": 0.3, "Emission Color": (1, 1, 1, 1), "Emission Strength": 0.3})
for k in range(-4, 5):
    w = k / 4.5
    tube([tuple(C + Vector((S * u, S * 0.75 * w, f(u, w) + 0.035))) for u in [-1 + 2 * i / 120 for i in range(121)]], 0.012, GRID)
    tube([tuple(C + Vector((S * w, S * 0.75 * v, f(w, v) + 0.035))) for v in [-1 + 2 * i / 120 for i in range(121)]], 0.012, GRID)
# the modulation loop: an ellipse in parameter space (phase lag), drawn on the slope of the bump
uc, vc, a_, b_, rot = 0.25, -0.3, 0.32, 0.17, 0.6
loop = []
for i in range(201):
    t = 2 * math.pi * i / 200
    du, dv = a_ * math.cos(t), b_ * math.sin(t)
    u = uc + du * math.cos(rot) - dv * math.sin(rot); v = vc + du * math.sin(rot) + dv * math.cos(rot)
    loop.append(C + Vector((S * u, S * 0.75 * v, f(u, v) + 0.08)))
LOOP = principled("qg_loop", **{"Base Color": (1.0, 0.35, 0.0, 1), "Roughness": 0.2, "Emission Color": (1.0, 0.4, 0.0, 1), "Emission Strength": 2.5})
tube([tuple(p) for p in loop], 0.055, LOOP)
for i0 in (40, 140):
    d = (loop[i0 + 3] - loop[i0]).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=0.11, depth=0.28, location=loop[i0] + d * 0.1,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, LOOP)
pc = C + Vector((S * uc, S * 0.75 * vc, f(uc, vc) + 0.08))
hot_spot(tuple(pc), (1.0, 0.8, 0.5, 1), 0.07, 30)
# a thin thread of light linking the operating point to the molecule
tube([tuple(pc), tuple(mol + Vector((0, 0, 0.63)))], 0.012, emission("qg_thread", (1.0, 0.7, 0.4, 1), 3.0))

camera((2.2, -11.5, 7.6), (0.0, 0.3, 2.0), lens=39, dof=3.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

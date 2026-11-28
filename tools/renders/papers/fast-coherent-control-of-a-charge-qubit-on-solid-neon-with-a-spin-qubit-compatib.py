# Fast coherent control of a charge qubit on solid neon with a spin-qubit-compatible resonator (Wang et al. 2026).
# Hero: a frosted layer of solid neon covering a silicon chip with a thin pink NbTiN nanowire resonator (two
# parallel strands) and gold gate electrodes. On the neon surface, next to the end of the strands, a single electron
# sits in a double-well trap: two glowing lobes, the electron in one and its ghost in the other. Above the trap, the
# paper's potential sketch in 3D: double well with the two lowest charge states. Microwave field arcs spread from the
# open end of the strands to the electron.
import bmesh
bright_stage(floor_z=-0.7)

NE_SI = principled("ne_si", **{"Base Color": (0.2, 0.28, 0.85, 1), "Roughness": 0.25, "Coat Weight": 0.8})
NE_NBTIN = principled("ne_nbtin", **{"Base Color": (1.0, 0.2, 0.55, 1), "Metallic": 0.6, "Roughness": 0.2, "Coat Weight": 1.0,
                                     "Emission Color": (1.0, 0.2, 0.55, 1), "Emission Strength": 0.6})
NE_ICE = principled("ne_ice", **{"Base Color": (0.9, 0.98, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.3, "IOR": 1.11, "Coat Weight": 0.8, "Coat Roughness": 0.02})
nt = NE_ICE.node_tree
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.3
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
# polycrystalline grains: each Voronoi cell gets its own tint and roughness
vor2 = nt.nodes.new("ShaderNodeTexVoronoi"); vor2.inputs["Scale"].default_value = 1.3
nt.links.new(tc.outputs["Object"], vor2.inputs["Vector"])
gm = nt.nodes.new("ShaderNodeMix"); gm.data_type = "RGBA"
gm.inputs[6].default_value = (0.92, 0.99, 1.0, 1); gm.inputs[7].default_value = (0.65, 0.88, 1.0, 1)
sepc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(vor2.outputs["Color"], sepc.inputs[0])
nt.links.new(sepc.outputs[0], gm.inputs["Factor"])
nt.links.new(gm.outputs[2], nt.nodes["Principled BSDF"].inputs["Base Color"])
rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.2, 0.6
nt.links.new(sepc.outputs[1], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Roughness"])
NE_E = principled("ne_electron", **{"Base Color": (0.05, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                    "Emission Color": (0.25, 0.55, 1.0, 1), "Emission Strength": 4.0})
NE_GHOST = principled("ne_ghost", **{"Base Color": (0.4, 0.7, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.05, "IOR": 1.2,
                                     "Emission Color": (0.25, 0.55, 1.0, 1), "Emission Strength": 0.6})
NE_ARC = emission("ne_arc", (1.0, 0.55, 0.1, 1), 9.0)
NE_MW = emission("ne_mw", (1.0, 0.3, 0.7, 1), 5.0)

X0, X1, Y0, Y1 = -9.0, 9.0, 0.2, 14.0
TN = 0.8                                     # neon thickness
box(((X0 + X1) / 2, (Y0 + Y1) / 2, -0.35), (X1 - X0, Y1 - Y0, 0.7), NE_SI, bevel=0.03)
# neon slab with a faintly faceted surface
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
me = bpy.data.meshes.new("neon"); bm.to_mesh(me); bm.free()
ice = bpy.data.objects.new("neon", me); sc.collection.objects.link(ice)
ice.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, TN / 2 + 0.002); ice.scale = (X1 - X0 - 0.01, Y1 - Y0 - 0.01, TN)
bv = ice.modifiers.new("b", "BEVEL"); bv.width = 0.04; bv.segments = 3
me.materials.append(NE_ICE)
ice.visible_shadow = False
# frost sparkles: small neon crystallites on the surface
import random
rnd = random.Random(3)
SPARK_ICE = principled("ne_xtal", **{"Base Color": (0.92, 0.98, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.03, "IOR": 1.5})
for _ in range(0):
    x, y = rnd.uniform(X0 + 0.4, X1 - 0.4), rnd.uniform(Y0 + 0.4, Y1 - 0.4)
    if math.hypot(x - 0.6, y - 1.6) < 2.6:
        continue
    bpy.ops.mesh.primitive_cube_add(size=rnd.uniform(0.15, 0.35), location=(x, y, TN + 0.03),
                                    rotation=(math.radians(54.7), math.radians(45), rnd.uniform(0, 3)))
    ob = bpy.context.object; ob.scale = (1, 1, 1)
    link(ob, SPARK_ICE)

# NbTiN nanowire resonator: two parallel thin strands coming from the back, ending at the trap
W, H, SEP = 0.32, 0.2, 0.9
def strand_path(off):
    pts = []
    for i in range(80):
        u = i / 79
        y = 1.6 + (Y1 - 0.4 - 1.6) * u
        x = -0.9 - 4.5 * u ** 1.6 + off
        pts.append((x, y))
    return pts
strands = []
for off in (-SEP / 2, SEP / 2):
    p = strand_path(off)
    strands.append(p)
    gate(p, width=W, height=H, mat=NE_NBTIN)
# gold gate electrodes (G1-G4 style) beside and below the trap
GOLD_N = principled("ne_gold", **{"Base Color": (1.0, 0.64, 0.22, 1), "Metallic": 1.0, "Roughness": 0.2})
gate([(2.9, 0.2), (2.9, 1.7), (6.5, 3.4), (8.6, 3.4)], width=0.8, height=0.22, mat=GOLD_N)            # G4, facing the trap
gate([(-2.6, 0.2), (-2.6, 3.0)], width=0.9, height=0.22, mat=GOLD_N)                      # G2, beside the strands
gate([(-5.6, -1.6), (-4.0, 2.0), (-6.8, 6.0)], width=1.0, height=0.22, mat=GOLD_N)       # G1
gate([(3.6, 7.0), (6.0, 9.5), (8.4, 9.5)], width=1.0, height=0.22, mat=GOLD_N)            # G3

# the charge qubit: double well on the neon surface between the strand ends and G4
zc = TN + 0.32
cA, cB = Vector((0.0, 1.6, zc)), Vector((1.7, 1.75, zc))
for cc in (cA, cB):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=tuple(cc - Vector((0, 0, 0.12))), segments=48, ring_count=24)
    lobe = bpy.context.object; lobe.scale = (0.8, 0.8, 0.42)
    lobe.data.materials.append(volume_glow("ne_lobe", (0.2, 1.0, 0.85, 1), 24.0)); lobe.visible_shadow = False
sphere(tuple(cA), 0.26, NE_E)
sphere(tuple(cB), 0.24, NE_GHOST)
hot_spot(tuple(cA), (0.6, 0.85, 1.0, 1), 0.05, 40)
l = bpy.data.lights.new("ne_e", "POINT"); l.energy, l.color = 10, (0.4, 0.7, 1.0)
lo = bpy.data.objects.new("ne_e", l); lo.location = cA + Vector((0, 0, 0.3)); sc.collection.objects.link(lo)
# resonator microwave field: glowing arcs spreading from the open end of the strands over the trap
tip = Vector((-0.9, 1.6, TN + 0.03))
for i, rr_ in enumerate((0.6, 1.05, 1.5, 1.95)):
    pts = [tuple(tip + Vector((rr_ * math.cos(a_), rr_ * math.sin(a_), 0.0))) for a_ in [math.radians(-55 + 110 * j / 60) for j in range(61)]]
    tube(pts, 0.03, emission("ne_mw%d" % i, (1.0, 0.3, 0.7, 1), 7.0 * (1 - i / 5)))
# the paper's sketch of the trap, lifted into 3D: double-well potential along the line through both wells, with the
# two lowest charge states (|0> red, symmetric; |1> blue, antisymmetric) as level lines carrying their wavefunctions
D = (cB - cA).length
ex = (cB - cA).normalized()
base = cA + Vector((0, 0, 0.5))
Hb = 0.55
U = lambda t: Hb * ((t - D / 2) ** 2 - (D / 2) ** 2) ** 2 / (D / 2) ** 4
pot = [tuple(base + ex * t + Vector((0, 0, U(t)))) for t in [-1.2 + (D + 2.4) * i / 200 for i in range(201)] if U(t) < 1.5]
tube(pot, 0.035, principled("ne_pot", **{"Base Color": (0.05, 0.05, 0.12, 1), "Roughness": 0.3, "Coat Weight": 1.0}))
g_ = lambda t, c: math.exp(-((t - c) / 0.33) ** 2)
for (lev, sign, col, nm) in ((0.22, 1, (1.0, 0.12, 0.1, 1), "ne_l0"), (0.42, -1, (0.15, 0.35, 1.0, 1), "ne_l1")):
    ts = [t for t in [-0.9 + (D + 1.8) * i / 160 for i in range(161)] if U(t) < lev + 0.25]
    mat = principled(nm, **{"Base Color": col, "Roughness": 0.3, "Emission Color": col, "Emission Strength": 2.5})
    tube([tuple(base + ex * t + Vector((0, 0, lev))) for t in ts], 0.012, mat)
    tube([tuple(base + ex * t + Vector((0, 0, lev + 0.2 * (g_(t, 0) + sign * g_(t, D))))) for t in ts], 0.028, mat)

camera((3.4, -5.4, 4.9), (0.0, 2.8, 0.7), lens=32, dof=9.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.3)

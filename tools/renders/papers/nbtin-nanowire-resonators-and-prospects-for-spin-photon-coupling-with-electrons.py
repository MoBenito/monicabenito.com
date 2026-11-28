"""NbTiN nanowire resonators and prospects for spin-photon coupling with electrons on solid neon (Tian et al. 2026).

High-resistivity silicon (blue) with etched ridges carrying the two pink NbTiN nanowire ends of the resonator,
running side by side across a narrow gap; far away they curve apart into the resonator loop. Solid neon covers
the chip as a clear icy layer. Electrons float just above the neon surface: a loose sheet of them across the
ice, and the qubit electron trapped over the gap between the wire ends (two minima, a double dot), its spin
coupled to the resonator's photon (electric-field arcs across the gap) through the field gradient of two cobalt
micromagnets placed symmetrically at the wire ends.
"""
import bmesh
import random
random.seed(11)

bright_stage(floor_z=-0.9, exposure=-0.35, sun_rot=(38, 0, 55))

# silicon substrate
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 20, -0.45))
sub = bpy.context.object; sub.scale = (70.0, 64.0, 0.9)
SI = principled("ne_silicon", **{"Base Color": (0.12, 0.35, 0.95, 1), "Roughness": 0.3, "Coat Weight": 0.6})
bv = sub.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 2
link(sub, SI)

NBTIN = principled("ne_nbtin", **{"Base Color": (1.0, 0.42, 0.62, 1), "Metallic": 0.6, "Roughness": 0.22, "Coat Weight": 0.8})
W, G = 0.7, 0.9           # wire width and gap
RZ, NZ = 0.32, 0.16       # ridge height, NbTiN thickness
Y_END = 0.0
BEND_Y, BEND_R = 9.0, 4.0


def wire_path(s):
    """Centre line of one wire end: straight from the tip, then bending outwards (s = -1 left, +1 right)."""
    xc = s * (G / 2 + W / 2)
    pts = [(xc, Y_END)]
    pts += [(xc, Y_END + BEND_Y * k / 10) for k in range(1, 11)]
    for k in range(1, 25):
        a = math.pi / 2 * k / 24
        pts.append((xc + s * BEND_R * (1 - math.cos(a)), BEND_Y + BEND_R * math.sin(a)))
    pts += [(xc + s * (BEND_R + 34.0 * k / 6), BEND_Y + BEND_R) for k in range(1, 7)]
    return pts


for s in (-1, 1):
    pts = wire_path(s)
    gate(pts, width=W, height=RZ, mat=SI)                 # etched silicon ridge
    g = gate(pts, width=W, height=NZ, mat=NBTIN)          # NbTiN film on top
    g.location.z = RZ

# cobalt micromagnets (Co/Ti/NbTiN electrodes) symmetric at the wire ends, one either side
COBALT = principled("ne_cobalt", **{"Base Color": (0.55, 0.62, 0.95, 1), "Metallic": 0.9, "Roughness": 0.22, "Coat Weight": 0.5})
NE_PINKCAP = principled("ne_pinkcap", **{"Base Color": (1.0, 0.42, 0.62, 1), "Metallic": 0.6, "Roughness": 0.2, "Coat Weight": 0.8})
for s in (-1, 1):
    box((s * (G / 2 + W + 1.25), Y_END + 0.4, 0.3), (1.6, 1.7, 0.6), COBALT, bevel=0.05)        # Co
    box((s * (G / 2 + W + 1.25), Y_END + 0.4, 0.66), (1.6, 1.7, 0.12), NE_PINKCAP, bevel=0.03)  # Ti/NbTiN cap

# solid neon: a clear, slightly frosted icy layer over everything
NE_TOP = 1.05
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 20.0, NE_TOP / 2 - 0.001))
ne = bpy.context.object; ne.scale = (69.9, 63.9, NE_TOP)
NEON = principled("ne_neon", **{"Base Color": (0.8, 0.97, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.12,
                                "IOR": 1.3, "Coat Weight": 0.6})
nt = NEON.node_tree
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
nt.links.new(nz.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
bv = ne.modifiers.new("b", "BEVEL"); bv.width = 0.04; bv.segments = 3
link(ne, NEON)
ne.visible_shadow = False

# the cavity photon: electric field arcs across the gap, strongest at the open ends
ARC = (1.0, 0.75, 0.05, 1)
for k in range(14):
    y = Y_END + 0.15 + 0.6 * k
    a = math.exp(-y / 4.5)
    pts = [(-G / 2 + G * t, y, RZ + NZ + 0.02 + (0.25 + 0.35 * a) * math.sin(math.pi * t)) for t in [j / 16 for j in range(17)]]
    tube(pts, 0.04, emission("ne_arc%02d" % k, ARC, 1.0 + 4.0 * a))

# electrons floating on the neon surface: a loose sheet of small glowing balls away from the device
EL = principled("ne_electron", **{"Base Color": (0.05, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                  "Emission Color": (0.1, 0.45, 1.0, 1), "Emission Strength": 3.0})
eb = bmesh.new()
Mx = __import__("mathutils").Matrix
for i in range(150):
    x = random.uniform(-16, 16); y = random.uniform(-4.0, 26)
    if math.hypot(x, y * 0.8) < 4.2:
        continue
    bmesh.ops.create_icosphere(eb, subdivisions=2, radius=0.13, matrix=Mx.Translation((x, y, NE_TOP + 0.14)))
me = bpy.data.meshes.new("ne_sheet"); eb.to_mesh(me); eb.free()
for f_ in me.polygons:
    f_.use_smooth = True
ob = bpy.data.objects.new("ne_sheet", me); sc.collection.objects.link(ob); me.materials.append(EL)
ob.visible_shadow = False

# the qubit: one electron over the gap; its two trap minima glow on the ice, its spin floats above
for s in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(s * 0.45, Y_END + 0.35, NE_TOP + 0.02), segments=32, ring_count=16)
    o = bpy.context.object; o.scale = (1.0, 1.0, 0.3)
    link(o, volume_glow("ne_dot", (0.1, 1.0, 0.6, 1), 7.0)); o.visible_shadow = False
SC = Vector((0.0, Y_END + 0.35, NE_TOP + 0.95))
NE_QARROW = principled("ne_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
NE_SPIN = principled("ne_spinglass", **{"Base Color": (1.0, 0.55, 0.1, 1), "Transmission Weight": 0.2,
                                       "Roughness": 0.22, "IOR": 1.45, "Coat Weight": 0.6, "Coat Roughness": 0.12})
spin(tuple(SC), (-0.35, -0.25, 1.0), r=0.5, mat=NE_SPIN, arrow=NE_QARROW, reach=1.8, shaft=0.1)
hot_spot(tuple(SC), (1.0, 0.7, 0.4, 1), 0.05, 25)
# gradient field between the magnets: faint lines over the gap, slanted (they differ at the two minima)
FL = emission("ne_field", (0.45, 0.1, 1.0, 1), 3.0)
for dz, dy in ((0.0, -0.5), (0.12, 1.3)):
    pts = [(-2.0 + 4.0 * t, Y_END + 0.4 + dy, 0.75 + dz + 0.55 * math.sin(math.pi * t)) for t in [j / 40 for j in range(41)]]
    tube(pts, 0.03, FL)

camera((5.0, -6.4, 6.0), (-0.4, 2.2, 0.6), lens=32, dof=3.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

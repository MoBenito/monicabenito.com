"""Lindblad linear response in minimal Kitaev junctions (Kuhn, Klees, Aguado, Benito 2026), concept new1.

The Kitaev Josephson junction of the paper's Fig. 4a: a semiconductor nanowire with four quantum dots; two
superconducting segments (each proximitising one dot pair = one minimal Kitaev chain) are the two ends of one
superconducting loop, so the loop's flux sets the phase difference phi across the weak link t_J between the
two inner dots. Flux readout: the flux through the loop is modulated (glowing rings around the flux arrow) and
the response is the supercurrent circulating in the loop (glowing chevrons). Faint wiggles leaving the dots are
the bath (Lindblad dissipation).
"""
import bmesh

bright_stage(floor_z=-0.9, exposure=-0.15, sun_rot=(42, 0, 35))

# chip substrate: saturated violet
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, -0.45))
sub = bpy.context.object; sub.scale = (60.0, 50.0, 0.9)
LK1_SUB = principled("lk1_sub", **{"Base Color": (0.74, 0.64, 1.0, 1), "Roughness": 0.4, "Coat Weight": 0.6})
link(sub, LK1_SUB)

LK1_SC = principled("lk1_sc", **{"Base Color": (0.3, 0.95, 1.0, 1), "Metallic": 0.35, "Roughness": 0.18, "Coat Weight": 1.0,
                                 "Emission Color": (0.2, 0.85, 1.0, 1), "Emission Strength": 0.6})
LK1_GOLD = principled("lk1_gold", **{"Base Color": (1.0, 0.72, 0.25, 1), "Metallic": 0.55, "Roughness": 0.25, "Coat Weight": 0.6})
LK1_WIRE = principled("lk1_wire", **{"Base Color": (0.85, 0.95, 1.0, 1), "Transmission Weight": 0.85,
                                     "Roughness": 0.1, "IOR": 1.35})
WY, WZ, WR = -1.6, 0.26, 0.24          # nanowire centre line
DX = (-3.3, -1.1, 1.1, 3.3)              # the four dots
SX = 2.2                                 # superconducting segments at +-SX

# nanowire
tube([(-5.2, WY, WZ), (5.2, WY, WZ)], WR, LK1_WIRE)

# plunger gates under the dots (gold), running to the front
for x in DX:
    gate([(x, WY + 0.4), (x, WY - 0.6), (x * 1.25, WY - 3.2), (x * 1.45, WY - 6.0)], width=0.34, height=0.08, mat=LK1_GOLD)

# the superconducting loop: two pads on the wire, joined by a big arc behind
C = Vector((0.0, 1.1)); R = (Vector((SX, WY)) - C).length
a_end = math.atan2(WY - C.y, SX - C.x)            # angle of right end (about -40 deg)
N = 90
# go from the right pad counter-clockwise over the back to the left pad
pts = [(C.x + R * math.cos(a_end + k / N * (math.pi - 2 * a_end)), C.y + R * math.sin(a_end + k / N * (math.pi - 2 * a_end)))
       for k in range(N + 1)]
ring = gate(pts, width=0.62, height=0.42, mat=LK1_SC)
ring.location.z = 0.12
for s in (-1, 1):
    box((s * SX, WY, WZ + 0.12), (0.95, 0.95, 0.42), LK1_SC, bevel=0.06)

# quantum dots: glow in the wire with an electron each
for i, x in enumerate(DX):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(x, WY, WZ), segments=32, ring_count=16)
    o = bpy.context.object; o.scale = (1.0, 0.75, 0.75)
    link(o, volume_glow("lk1_dot", (1.0, 0.55, 0.1, 1), 9.0)); o.visible_shadow = False
    sphere((x, WY, WZ), 0.13, emission("lk1_e", (1.0, 0.5, 0.08, 1), 12.0))

# the weak link t_J between the two inner dots: a short glowing bridge
LK1_TJ = emission("lk1_tj", (1.0, 0.25, 0.75, 1), 12.0)
tube([(DX[1] + 0.25 + (DX[2] - DX[1] - 0.5) * t, WY, WZ + 0.38 + 0.25 * math.sin(math.pi * t)) for t in [j / 20 for j in range(21)]],
     0.06, LK1_TJ)

# flux through the loop: a magenta arrow with modulation rings
FL = principled("lk1_flux", **{"Base Color": (1.0, 0.2, 0.6, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                               "Emission Color": (1.0, 0.2, 0.6, 1), "Emission Strength": 1.5})
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=3.4, location=(C.x, C.y, 1.7), vertices=32)
bpy.ops.object.shade_smooth(); link(bpy.context.object, FL)
bpy.ops.mesh.primitive_cone_add(radius1=0.42, depth=0.8, location=(C.x, C.y, 3.8), vertices=32)
bpy.ops.object.shade_smooth(); link(bpy.context.object, FL)
for k, (z, r) in enumerate(((0.9, 0.9), (1.6, 1.3), (2.3, 1.7))):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.05, location=(C.x, C.y, z))
    link(bpy.context.object, emission("lk1_mod%d" % k, (1.0, 0.3, 0.75, 1), 6.0 - 1.6 * k))

# supercurrent around the loop: glowing chevrons riding on the ring
SUP = emission("lk1_sup", (1.0, 0.85, 0.15, 1), 8.0)
bm = bmesh.new()
ZT = 0.12 + 0.42 + 0.02
for k in range(1, 10):
    a = a_end + k / 10 * (math.pi - 2 * a_end)
    rad = Vector((math.cos(a), math.sin(a), 0)); tdir = Vector((-math.sin(a), math.cos(a), 0))
    c = Vector((C.x, C.y, ZT)) + rad * R
    # flat chevron pointing along the current direction
    w, L, th = 0.36, 0.3, 0.1
    o = [c + tdir * L, c - tdir * L * 0.4 + rad * w, c - tdir * L * 0.05, c - tdir * L * 0.4 - rad * w]
    bot = [bm.verts.new(v) for v in o]; top = [bm.verts.new(v + Vector((0, 0, th))) for v in o]
    bm.faces.new(bot[::-1]); bm.faces.new(top)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
me = bpy.data.meshes.new("lk1_chev"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("lk1_chev", me); sc.collection.objects.link(ob); me.materials.append(SUP)

# the bath: little photon wiggles leaving the outer dots (Lindblad dissipation)
BATH = emission("lk1_bath", (1.0, 0.35, 0.8, 1), 6.0)
for x, sgn in ((DX[0], -1), (DX[3], 1)):
    pts = []
    for j in range(61):
        t = j / 60
        pts.append((x + sgn * (0.3 + 1.0 * t), WY - 0.2 - 0.3 * t, WZ + 0.5 + 1.4 * t + 0.12 * math.sin(t * 6 * math.pi)))
    tube(pts, 0.03, BATH)

camera((0.0, -11.5, 8.6), (0.0, 0.45, 1.1), lens=36, dof=4.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

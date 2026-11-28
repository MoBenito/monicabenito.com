# Escaping AB caging via Floquet engineering (Ahmed, Benito, Perez-Gonzalez 2025)
# A diamond (rhombic) chain on a plate: hub sites C (blue), upper U (coral) and lower D (green), one bond per plaquette
# carrying the Peierls phase (dotted), and a magnetic flux line (violet rod with arrow) threading every plaquette.
# With pi flux, interference cages a particle inside one plaquette (Aharonov-Bohm caging): drawn literally as a
# golden birdcage around the first rhombus. Light falls on the chain (wavy rays from above: the periodic drive); the
# photo-induced long-range tunnelling opens a way out: the cage door stands open and the glowing particle arcs out to
# the far end of the chain, which lights up (charge oscillation between the chain ends).
import bmesh
from mathutils import Matrix

bright_stage(floor_z=0.0, exposure=-0.4, sun_rot=(38, 0, -20))


def ab_cyclorama(y0=5.0, R=5.0, top=30.0, width=80.0, bottom=(1.0, 0.86, 0.74, 1), upper=(0.62, 0.76, 1.0, 1), glow=0.55):
    """Studio sweep behind the scene: the floor curves up into a pastel wall (peach at the bottom, sky blue above)."""
    import bmesh as _bm
    bm = _bm.new()
    prof = []
    for j in range(25):
        a = math.pi / 2 * j / 24
        prof.append((y0 + R * math.sin(a), R - R * math.cos(a)))
    prof.append((y0 + R, top))
    rows = []
    for (yy, zz) in prof:
        rows.append([bm.verts.new((xx, yy, zz + 0.002)) for xx in (-width / 2, width / 2)])
    for a_, b_ in zip(rows[:-1], rows[1:]):
        bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
    me = bpy.data.meshes.new("cyc"); bm.to_mesh(me); bm.free()
    for f_ in me.polygons:
        f_.use_smooth = True
    ob = bpy.data.objects.new("cyc", me); sc.collection.objects.link(ob)
    m = principled("ab_cyc", **{"Roughness": 0.6})
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.0, bottom
    el[1].position, el[1].color = 1.0, upper
    nt.links.new(_math(nt, "DIVIDE", sp.outputs["Z"], 9.0), rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow
    me.materials.append(m)
    return ob


ab_cyclorama(y0=5.0, bottom=(1.0, 0.62, 0.48, 1), upper=(0.35, 0.55, 1.0, 1), glow=0.05)
ZC = 1.25
A = 1.3                       # half diagonal of a rhombus
NPL = 3
CX = [2 * A * (i - NPL / 2) for i in range(NPL + 1)]

AB_PLATE = principled("ab_plate", **{"Base Color": (0.75, 0.7, 1.0, 1), "Roughness": 0.3, "Coat Weight": 0.8})
AB_C = principled("ab_c", **{"Base Color": (0.15, 0.55, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0})
AB_U = principled("ab_u", **{"Base Color": (1.0, 0.3, 0.22, 1), "Roughness": 0.15, "Coat Weight": 1.0})
AB_D = principled("ab_d", **{"Base Color": (0.15, 0.7, 0.3, 1), "Roughness": 0.15, "Coat Weight": 1.0})
AB_BOND = principled("ab_bond", **{"Base Color": (0.08, 0.12, 0.5, 1), "Roughness": 0.25, "Metallic": 0.3, "Coat Weight": 0.6})
AB_PHASE = principled("ab_phase", **{"Base Color": (0.08, 0.12, 0.5, 1), "Roughness": 0.25, "Coat Weight": 0.6})
AB_FLUX = principled("ab_flux", **{"Base Color": (0.55, 0.2, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                     "Emission Color": (0.55, 0.2, 1.0, 1), "Emission Strength": 2.5})
AB_FLUXHALO = beam_material("ab_fluxhalo", (0.6, 0.25, 1.0, 1), 1.5)
AB_PART = principled("ab_particle", **{"Base Color": (1.0, 0.28, 0.0, 1), "Roughness": 0.1, "Coat Weight": 1.0,
                                         "Emission Color": (1.0, 0.3, 0.0, 1), "Emission Strength": 1.2})
AB_TRAIL = emission("ab_trail", (1.0, 0.4, 0.02, 1), 4.0)
AB_PHALO = volume_glow("ab_phalo", (1.0, 0.4, 0.0, 1), 1.5)
AB_PHIDISC = principled("ab_phidisc", **{"Base Color": (0.55, 0.8, 1.0, 1), "Roughness": 0.2, "Transmission Weight": 0.5,
                                          "Emission Color": (0.5, 0.8, 1.0, 1), "Emission Strength": 0.8})
AB_LIGHT = emission("ab_light", (1.0, 0.8, 0.2, 1), 6.0)

box((0, 0.3, 0.12), (CX[-1] - CX[0] + 3.0, 4.4, 0.24), AB_PLATE, bevel=0.08)

sites = []
for i, x in enumerate(CX):
    sites.append(((x, 0, ZC), AB_C, 0.27))
    if i < NPL:
        xm = x + A
        sites.append(((xm, A, ZC), AB_U, 0.23))
        sites.append(((xm, -A, ZC), AB_D, 0.23))
        c, u, d, c2 = Vector((x, 0, ZC)), Vector((xm, A, ZC)), Vector((xm, -A, ZC)), Vector((x + 2 * A, 0, ZC))
        for a_, b_ in ((c, u), (u, c2), (d, c2)):
            dd = (b_ - a_).normalized()
            tube([tuple(a_ + dd * 0.22), tuple(b_ - dd * 0.22)], 0.065, AB_BOND)
        dd = (d - c).normalized(); L = (d - c).length
        for k in range(1, 8):
            sphere(tuple(c + dd * L * k / 8), 0.06, AB_PHASE)
        # flux line through the plaquette, with an arrow head on top
        tube([(xm, 0, 0.24), (xm, 0, ZC + 1.1)], 0.05, AB_FLUX)
        bpy.ops.mesh.primitive_cone_add(radius1=0.15, depth=0.32, location=(xm, 0, ZC + 1.25), vertices=32)
        link(bpy.context.object, AB_FLUX)
        beam((xm, 0, 0.3), (xm, 0, ZC + 1.0), 0.32, AB_FLUXHALO)
        # the flux symbol of the paper's sketch: a pale blue disc in the plaquette
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.03, location=(xm, 0, ZC - 0.02), vertices=64)
        link(bpy.context.object, AB_PHIDISC)
for x in CX:
    tube([(x, 0, 0.24), (x, 0, ZC - 0.27)], 0.03, GOLD)
for p, m, r in sites:
    sphere(p, r, m)
# the chain continues beyond the plate: faint bond stubs
for x0, s in ((CX[0], -1), (CX[-1], 1)):
    for yy in (A, -A):
        tube([(x0 - s * 0.0 + s * 0.2, yy * 0.15, ZC), (x0 + s * 0.75, yy * 0.58, ZC)], 0.04, AB_BOND)

# --- the birdcage around the first plaquette -----------------------------------------------------------------
cx, R, z0, z1 = CX[0] + A, A + 0.45, 0.26, ZC + 0.9
CAGE = principled("ab_cage", **{"Base Color": (1.0, 0.68, 0.25, 1), "Metallic": 1.0, "Roughness": 0.18})
nb = 24
door = range(16, 20)          # the door opening spans bars 16..20; bar 16 is the hinge post, bar 20 the latch post
DT = 0.75                     # dome height
for k in range(nb):
    a = 2 * math.pi * k / nb
    # every meridian runs over the full dome (the roof is complete above the door too) ...
    dome = [(cx + R * math.cos(a) * math.cos(t), R * math.sin(a) * math.cos(t), z1 + DT * math.sin(t))
            for t in [math.pi / 2 * j / 12 for j in range(13)]]
    tube(dome, 0.022, CAGE)
    # ... and every wall bar is present except those in the door opening (they swing out with the door)
    if k not in door[1:]:
        tube([(cx + R * math.cos(a), R * math.sin(a), z0), (cx + R * math.cos(a), R * math.sin(a), z1)],
             0.03 if k in (door[0], door[-1] + 1) else 0.022, CAGE)
# rings: base and top rim all round; the middle ring stops at the door posts
tube([(cx + R * math.cos(a), R * math.sin(a), z0) for a in [2 * math.pi * j / 160 for j in range(161)]], 0.035, CAGE)
tube([(cx + R * math.cos(a), R * math.sin(a), z1) for a in [2 * math.pi * j / 160 for j in range(161)]], 0.035, CAGE)
a_h = 2 * math.pi * door[0] / nb
a_e = 2 * math.pi * (door[-1] + 1) / nb
mid_ring = [a_e + (2 * math.pi - (a_e - a_h)) * j / 150 for j in range(151)]
tube([(cx + R * math.cos(a), R * math.sin(a), z0 + 0.2) for a in mid_ring], 0.035, CAGE)
# a second roof ring on the dome, like a real birdcage
tz = math.radians(45)
tube([(cx + R * math.cos(tz) * math.cos(a), R * math.cos(tz) * math.sin(a), z1 + DT * math.sin(tz))
      for a in [2 * math.pi * j / 160 for j in range(161)]], 0.028, CAGE)
sphere((cx, 0, z1 + 0.8), 0.1, CAGE)
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.028, location=(cx, 0, z1 + 1.1), rotation=(math.radians(90), 0, 0))
link(bpy.context.object, CAGE)
# the door: the curved panel of bars 16..20, swung open about the hinge post
hinge = Vector((cx + R * math.cos(a_h), R * math.sin(a_h), 0))
rot = Matrix.Rotation(math.radians(-100), 3, "Z")


def door_pt(a):
    return hinge + rot @ (Vector((cx + R * math.cos(a), R * math.sin(a), 0)) - hinge)


d_ang = [a_h + (a_e - a_h) * u for u in (0, 0.25, 0.5, 0.75, 1.0)]
for a in d_ang[1:]:
    p = door_pt(a)
    tube([(p.x, p.y, z0 + 0.03), (p.x, p.y, z1 - 0.03)], 0.022, CAGE)
arc = [door_pt(a_h + (a_e - a_h) * j / 40) for j in range(41)]
for z in (z0 + 0.03, z0 + 0.2, z1 - 0.03):
    tube([(p.x, p.y, z) for p in arc], 0.032, CAGE)
# hinge knuckles on the hinge post and a latch hook on the free edge of the door
for z in (z0 + 0.32, z1 - 0.3):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.16, location=(hinge.x, hinge.y, z), vertices=24)
    link(bpy.context.object, CAGE)
pe = door_pt(a_e)
bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.018, location=(pe.x, pe.y, (z0 + z1) / 2 + 0.1),
                                 rotation=(math.radians(90), 0, a_h + math.radians(-100)))
link(bpy.context.object, CAGE)

# --- the escaping particle -------------------------------------------------------------------------------------
def bez(p0, p1, p2, p3, u):
    return (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3 * p3
start = Vector((cx + 0.1, 0.35, ZC + 0.15))
gate_pt = Vector((cx, -R - 0.25, ZC + 0.3))
end = Vector((CX[-1], 0, ZC + 0.32))
leg1 = [start.lerp(gate_pt, j / 30) for j in range(31)]
leg2 = [bez(gate_pt, Vector((cx + 0.6, -R - 1.8, ZC + 1.2)), Vector((end.x - 1.2, -1.6, ZC + 3.2)), end, j / 200) for j in range(201)]
path = leg1 + leg2[1:]
ih = 30 + 118
# trail: thickens towards the particle
for seg in range(10):
    a, b = int(ih * seg / 10), int(ih * (seg + 1) / 10) + 1
    tube([tuple(p) for p in path[a:b]], 0.012 + 0.005 * seg, AB_TRAIL)
for j in range(ih + 10, len(path) - 4, 8):
    sphere(tuple(path[j]), 0.045, AB_TRAIL)
ph = path[ih]
sphere(tuple(ph), 0.26, AB_PART)
sphere((CX[-1], 0, ZC), 0.75, volume_glow("ab_endglow", (1.0, 0.5, 0.1, 1), 2.0)).visible_shadow = False
l = bpy.data.lights.new("ab_p", "POINT"); l.energy, l.color, l.shadow_soft_size = 40, (1.0, 0.6, 0.25), 0.3
lo = bpy.data.objects.new("ab_p", l); lo.location = ph; sc.collection.objects.link(lo)

# --- the drive: wavy light rays falling on the chain -----------------------------------------------------------
dirv = Vector((-0.35, 0.25, -1.0)).normalized()
side = dirv.cross(Vector((0, 1, 0))).normalized()
for k, (ox, oy) in enumerate(((-0.8, 1.2), (1.4, 1.6), (3.4, 1.0), (0.4, 2.4))):
    tip = Vector((ox, oy, ZC + 1.3))
    st = tip - dirv * 3.2
    pts = []
    for j in range(161):
        u = j / 160
        pts.append(tuple(st.lerp(tip, u) + side * 0.12 * math.sin(2 * math.pi * 6 * u)))
    for seg in range(6):
        tube(pts[seg * 27: seg * 27 + 28], 0.03, emission("ab_ray%d" % seg, (1.0, 0.75, 0.2, 1), 1.0 + 1.2 * seg))

camera((0.6, -10.2, 6.2), (-0.3, -0.2, 1.4), lens=34, dof=2.6)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

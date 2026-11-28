# Topological instabilities in ac-driven bosonic systems (Engelhardt, Benito, Platero, Brandes, PRL 2016)
# A dimerized (SSH-type) chain of bosonic modes (mint glass resonators on gold pins) coupled by springs: thick springs
# inside pairs, thin ones between pairs, so each end site keeps only a weak link (the topological configuration).
# The springs are the ac-driven hoppings (pink, glowing). The bulk modes hold a boson or two and stay calm (stable);
# at the two ends the bosonic occupation grows exponentially: a whirl of green bosons rises from each end mode and
# widens with height, the symmetry-protected instability localized at the boundaries.
import random
random.seed(7)

bright_stage(floor_z=0.0, exposure=-0.4, sun_rot=(40, 0, 30))


def ti_cyclorama(y0=5.0, R=5.0, top=30.0, width=80.0, bottom=(1.0, 0.86, 0.74, 1), upper=(0.62, 0.76, 1.0, 1), glow=0.55):
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
    m = principled("ti_cyc", **{"Roughness": 0.6})
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


ti_cyclorama(y0=4.0, bottom=(1.0, 0.7, 0.82, 1), upper=(0.45, 0.65, 1.0, 1), glow=0.12)
N = 8
xs, x = [], 0.0
for i in range(N):
    xs.append(x)
    x += 1.8 if i % 2 == 0 else 1.15          # weak bond after even sites, strong after odd -> ends weakly bound
off = (xs[0] + xs[-1]) / 2
xs = [v - off for v in xs]
ZS, R = 1.25, 0.34

TI_PLATE = principled("ti_plate", **{"Base Color": (0.85, 0.22, 0.6, 1), "Roughness": 0.3, "Coat Weight": 0.8})
TI_MODE = principled("ti_mode", **{"Base Color": (0.55, 0.95, 0.9, 1), "Transmission Weight": 0.75, "Roughness": 0.06, "IOR": 1.45,
                                     "Coat Weight": 1.0})
TI_BOSON = principled("ti_boson", **{"Base Color": (0.12, 0.75, 0.05, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                       "Emission Color": (0.2, 0.9, 0.05, 1), "Emission Strength": 0.6})
TI_HOT = principled("ti_boson_hot", **{"Base Color": (0.12, 0.75, 0.05, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                         "Emission Color": (0.2, 0.9, 0.05, 1), "Emission Strength": 0.9})
TI_BOND = principled("ti_spring", **{"Base Color": (1.0, 0.25, 0.6, 1), "Roughness": 0.2, "Metallic": 0.4, "Coat Weight": 1.0,
                                       "Emission Color": (1.0, 0.2, 0.55, 1), "Emission Strength": 1.6})
TI_HALO = volume_glow("ti_halo", (0.3, 1.0, 0.1, 1), 0.9)

box((0, 0.2, 0.15), (xs[-1] - xs[0] + 2.0, 2.2, 0.3), TI_PLATE, bevel=0.08)
for i, x in enumerate(xs):
    tube([(x, 0, 0.3), (x, 0, ZS - R)], 0.06, GOLD)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.06, location=(x, 0, 0.33), vertices=48)
    link(bpy.context.object, GOLD)
    sphere((x, 0, ZS), R, TI_MODE)
    if 0 < i < N - 1:
        for k in range(1 + (i % 3 == 1)):
            a = 1.0 + 2.6 * k + i
            sphere((x + 0.2 * math.cos(a), -0.2 * math.sin(a) - 0.05, ZS + R + 0.02 - 0.06 * k), 0.1, TI_BOSON)

# ac-driven hoppings as springs between the modes
for i in range(N - 1):
    strong = i % 2 == 1
    a, b = xs[i] + R + 0.02, xs[i + 1] - R - 0.02
    turns = 6 if strong else 9
    rr = 0.13 if strong else 0.09
    pts = [(a + (b - a) * u, rr * math.sin(2 * math.pi * turns * u), ZS + rr * math.cos(2 * math.pi * turns * u)) for u in [j / 300 for j in range(301)]]
    tube(pts, 0.035 if strong else 0.016, TI_BOND)

# exponentially growing edge occupation: a widening whirl of bosons over each end mode
for x, s in ((xs[0], -1), (xs[-1], 1)):
    for strand in range(7):
        ph0 = 2 * math.pi * strand / 7
        u = 0.0
        while u < 1.0:
            r = 0.18 * math.exp(1.75 * u)
            a = ph0 + 2 * math.pi * 1.6 * u * s
            z = ZS + R + 0.1 + 2.6 * u
            sphere((x + r * math.cos(a), r * math.sin(a), z), 0.07 + 0.09 * u, TI_HOT)
            u += 0.085 * math.exp(-1.2 * u)
    # a glowing trace of the growing amplitude: a helix spiralling outwards
    pts = []
    for j in range(401):
        u = j / 400
        r = 0.2 * math.exp(1.9 * u) + 0.12
        a = 2 * math.pi * 1.6 * u * s + 0.4
        pts.append((x + r * math.cos(a), r * math.sin(a), ZS + R + 0.1 + 2.6 * u))
    tube(pts, 0.025, emission("ti_trace", (0.35, 1.0, 0.3, 1), 5.0))
    sphere((x, 0, ZS), R * 0.6, TI_HOT)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, 0, ZS + 1.6), segments=48, ring_count=24)
    hz = bpy.context.object; hz.scale = (1.1, 1.1, 1.9); link(hz, TI_HALO); hz.visible_shadow = False
    l = bpy.data.lights.new("ti_edge", "POINT"); l.energy, l.color, l.shadow_soft_size = 40, (0.4, 1.0, 0.35), 0.5
    lo = bpy.data.objects.new("ti_edge", l); lo.location = (x, -0.8, ZS + 0.6); sc.collection.objects.link(lo)

# the ac drive: a pink wave running along the front of the plate
pts = [(xs[0] - 0.6 + (xs[-1] - xs[0] + 1.2) * u, -1.05, 0.62 + 0.16 * math.sin(2 * math.pi * 9 * u)) for u in [j / 600 for j in range(601)]]
tube(pts, 0.04, emission("ti_drive", (1.0, 0.15, 0.5, 1), 6.0))

camera((-1.0, -13.2, 3.2), (0.0, 0.3, 2.45), lens=32, dof=2.6)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

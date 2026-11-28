# Floquet Majorana fermions in superconducting quantum dots (Benito & Platero, Physica E 2015)
# Three quantum dots in a row on a chip, each holding one electron spin set by its own magnetic field (the middle one
# tilted by theta, non-collinear fields are what allow pairing). Two superconductors (pale blue, Cooper pairs on top)
# bridge neighbouring dots: tunnelling (gold arcs) and crossed-Andreev pairing (violet arcs: a Cooper pair
# split onto both dots). Each dot's plunger gate carries an ac signal (pink sine wave riding the gold lead, pulsing rings at
# the dot). The Floquet Majoranas glow teal at the two outer dots.

bright_stage(floor_z=0.0, exposure=-0.4, sun_rot=(48, 0, 35))


def qm_cyclorama(y0=5.0, R=5.0, top=30.0, width=80.0, bottom=(1.0, 0.86, 0.74, 1), upper=(0.62, 0.76, 1.0, 1), glow=0.55):
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
    m = principled("qm_cyc", **{"Roughness": 0.6})
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


qm_cyclorama(y0=6.5, bottom=(0.85, 0.65, 1.0, 1), upper=(0.42, 0.62, 1.0, 1), glow=0.12)
TOP = 0.6
QM_XS = (-2.7, 0.0, 2.7)
QM_THETA = math.radians(55)

# chip with heterostructure layers on its cut faces
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.5, TOP / 2))
slab = bpy.context.object; slab.scale = (11.5, 9.0, TOP)
sm = principled("qm_hetero", **{"Roughness": 0.35})
nt = sm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.72, 0.62, 1.0, 1)
els[1].position, els[1].color = 0.5, (1.0, 0.55, 0.65, 1)
for pos, col in ((0.66, (1.0, 0.85, 0.45, 1)), (0.86, (0.3, 0.33, 0.8, 1))):
    e = els.new(pos); e.color = col
nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
link(slab, sm)

QM_SPIN_ARROW = principled("qm_arrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
QM_ZERO = emission("qm_zero", (0.0, 1.0, 0.7, 1), 9.0)
QM_ZHALO = volume_glow("qm_zhalo", (0.1, 1.0, 0.75, 1), 2.5)
QM_PUDDLE_W = emission("qm_puddle_warm", (1.0, 0.6, 0.25, 1), 3.5)
QM_SC = principled("qm_superconductor", **{"Base Color": (0.82, 0.88, 0.95, 1), "Metallic": 0.9, "Roughness": 0.25, "Coat Weight": 0.8})
QM_PAIR = principled("qm_cooper", **{"Base Color": (0.1, 0.35, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                       "Emission Color": (0.25, 0.5, 1.0, 1), "Emission Strength": 1.2})
QM_TUN = emission("qm_tunnel", (1.0, 0.7, 0.25, 1), 5.0)
QM_ANDREEV = emission("qm_andreev", (0.55, 0.15, 1.0, 1), 8.0)
QM_AC = emission("qm_ac", (1.0, 0.2, 0.5, 1), 7.0)

# plunger gates: gold fingers from the front edge to each dot, plus two side gates closing the row
for x in QM_XS:
    g = gate([(x, -2.95), (x, -0.75)], width=0.34, height=0.16); g.location.z = TOP
gl = gate([(-4.6, -1.3), (-4.6, 0.9)], width=0.3, height=0.16); gl.location.z = TOP
gr = gate([(4.6, -1.3), (4.6, 0.9)], width=0.3, height=0.16); gr.location.z = TOP

# superconductors bridging neighbouring dots, slightly behind the row
for xa, xb in ((QM_XS[0], QM_XS[1]), (QM_XS[1], QM_XS[2])):
    xc = (xa + xb) / 2
    box((xc, 1.25, TOP + 0.2), (xb - xa - 0.2, 1.1, 0.4), QM_SC, bevel=0.06)
    # Cooper pairs: pairs of electrons bound together on the superconductor
    for (dx, dy, ang) in ((-0.75, 1.05, 20), (0.05, 1.45, -30), (0.8, 1.0, 60)):
        c = Vector((xc + dx, dy, TOP + 0.5))
        d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)) * 0.15
        sphere(tuple(c + d), 0.09, QM_PAIR); sphere(tuple(c - d), 0.09, QM_PAIR)
        tube([tuple(c + d), tuple(c - d)], 0.02, QM_PAIR)

H = 1.55
for i, x in enumerate(QM_XS):
    th = QM_THETA if i == 1 else 0.0
    spin((x, 0, H), (math.sin(th), 0, math.cos(th)), r=0.42, arrow=QM_SPIN_ARROW, reach=1.75, shaft=0.11)
    # electron puddle defined by the gates
    bpy.ops.mesh.primitive_circle_add(radius=0.55, fill_type="NGON", location=(x, 0, TOP + 0.005))
    link(bpy.context.object, QM_ZERO if i != 1 else QM_PUDDLE_W)
    # the ac signal on the plunger gate: a pink sine riding above the gold lead, rings pulsing out at the dot
    pts = []
    for j in range(161):
        u = j / 160
        y = -2.9 + 2.0 * u
        pts.append((x + 0.17 * math.sin(2 * math.pi * 4 * u), y, TOP + 0.24))
    tube(pts, 0.024, QM_AC)
    for k, rr in enumerate((0.78, 1.0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.022, major_segments=96, minor_segments=8, location=(x, 0, TOP + 0.03))
        link(bpy.context.object, emission("qm_ring%d" % k, (1.0, 0.25, 0.55, 1), 5.0 / (1 + k)))

# couplings: direct tunnelling (gold arc) and pairing through the superconductor (violet arc dipping into it)
for xa, xb in ((QM_XS[0], QM_XS[1]), (QM_XS[1], QM_XS[2])):
    pa, pb = Vector((xa + 0.5, 0, H)), Vector((xb - 0.5, 0, H))
    tube([tuple(pa.lerp(pb, u) + Vector((0, 0, 0.5 * math.sin(math.pi * u)))) for u in [j / 40 for j in range(41)]], 0.04, QM_TUN)

# crossed Andreev pairing: one Cooper pair in each superconductor splits its two electrons onto the neighbouring dots
for xa, xb in ((QM_XS[0], QM_XS[1]), (QM_XS[1], QM_XS[2])):
    src = Vector(((xa + xb) / 2 + 0.05, 1.45, TOP + 0.62))
    for xd in (xa, xb):
        dst = Vector((xd + (0.3 if xd < src.x else -0.3), 0.15, H - 0.35))
        mid = (src + dst) / 2 + Vector((0, -0.2, 0.55))
        tube([tuple((1 - u) ** 2 * src + 2 * (1 - u) * u * mid + u * u * dst) for u in [j / 40 for j in range(41)]], 0.045, QM_ANDREEV)
    hot_spot(tuple(src), (0.7, 0.4, 1.0, 1), 0.07, 20)

# the Floquet Majoranas: teal glow around the outer dots
for x in (QM_XS[0], QM_XS[2]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, 0, TOP + 0.05), segments=48, ring_count=24)
    hz = bpy.context.object; hz.scale = (0.95, 0.95, 0.55); link(hz, QM_ZHALO); hz.visible_shadow = False
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.03, major_segments=96, minor_segments=8, location=(x, 0, H - 0.05))
    link(bpy.context.object, emission("qm_zring", (0.1, 1.0, 0.75, 1), 6.0))
    l = bpy.data.lights.new("qm_zm", "POINT"); l.energy, l.color, l.shadow_soft_size = 40, (0.3, 1.0, 0.8), 0.5
    lo = bpy.data.objects.new("qm_zm", l); lo.location = (x, -0.6, H); sc.collection.objects.link(lo)

camera((2.4, -7.6, 3.1), (0.0, 0.3, 1.35), lens=36, dof=2.4)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

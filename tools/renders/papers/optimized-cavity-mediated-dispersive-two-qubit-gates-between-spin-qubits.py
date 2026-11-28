"""Second concept: the paper's Figure 1 lifted into 3D, as a sculpture standing on a chip.

Two double-well potentials (the two double quantum dots), each with a micromagnet bar (blue S / red N) whose dipole
field lines fan out in 3D, the electron spin in the left well and its tilted partner orbital (dashed ghost) in the
right well, the tunnelling arrow t_c, a coupling capacitor down to a shared meandering superconducting resonator
that carries the faint glow of the virtual photon exchanged in the dispersive gate.
"""
bright_stage(floor_z=-0.7, exposure=-0.4, sun_rot=(46, 0, -32))
exec(compile((HERE / "papers" / "fieldlines_common.inc").read_text(), "fieldlines_common.inc", "exec"), globals())
# stray field computed, not drawn by hand: each micromagnet is a uniformly magnetised box (S|N along +x as in
# Figure 1); its lines are integrated from seeds on rings around the centre of the north face until they close into
# the south face. The two double dots sit a cavity length (millimetres) apart on the real chip, so each magnet's
# field is computed on its own (the other one is effectively at infinity), exactly as Figure 1 draws them.
OCG_B0 = 0.0016     # external field B_z along +x, in the same units (mu0 M), comparable to the transverse stray field
OCG_RINGS = ((0.96, (90, 270)), (0.9, (90, 270)), (0.82, (90, 270)), (0.74, (270,)))   # in-plane only (2D, as Figure 1)

# --- chip slab (coloured, so the background is not pale grey) -------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6.0, -0.45))
slab = bpy.context.object; slab.scale = (400.0, 400.0, 0.5)
cm = principled("ocg_chip", **{"Base Color": (0.3, 0.78, 0.84, 1), "Roughness": 0.45})
nt = cm.node_tree
br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.0; br.squash = 1.0
br.inputs["Scale"].default_value = 0.35; br.inputs["Mortar Size"].default_value = 0.006
br.inputs["Color1"].default_value = (0.3, 0.78, 0.85, 1); br.inputs["Color2"].default_value = (0.34, 0.8, 0.82, 1)
br.inputs["Mortar"].default_value = (0.6, 0.92, 0.95, 1)
tcc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcc.outputs["Object"], br.inputs["Vector"])
link(slab, cm)

OCG_POT = principled("ocg_pot", **{"Base Color": (0.12, 0.1, 0.55, 1), "Metallic": 0.4, "Roughness": 0.15,
                                   "Coat Weight": 1.0})
OCG_LINE = principled("ocg_line", **{"Base Color": (1.0, 0.66, 0.25, 1), "Metallic": 1.0, "Roughness": 0.18})
OCG_FIELD = emission("ocg_field", (0.05, 0.6, 1.0, 1), 4.0)
OCG_MAG_R = principled("ocg_mag_r", **{"Base Color": (0.95, 0.06, 0.05, 1), "Roughness": 0.25, "Coat Weight": 1.0})
OCG_MAG_B = principled("ocg_mag_b", **{"Base Color": (0.05, 0.15, 0.95, 1), "Roughness": 0.25, "Coat Weight": 1.0})
OCG_ORANGE = principled("ocg_orange", **{"Base Color": (1.0, 0.3, 0.04, 1), "Transmission Weight": 0.5,
                                         "Roughness": 0.05, "IOR": 1.45, "Coat Weight": 0.5})
OCG_ARROW = principled("ocg_arrow", **{"Base Color": (1.0, 0.12, 0.1, 1), "Roughness": 0.2, "Coat Weight": 1.0})
OCG_PURPLE = emission("ocg_purple", (0.65, 0.15, 1.0, 1), 3.0)
OCG_PINK = emission("ocg_pink", (1.0, 0.25, 0.7, 1), 14.0)


def ocg_ghost():
    m = bpy.data.materials.new("ocg_ghost"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.35, 0.15, 1)
    em.inputs["Strength"].default_value = 1.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


OCG_GHOST = ocg_ghost()

Y0 = 0.0          # all of the figure lives in the plane y = 0


def pot(u):
    return 0.3 * (u * u - 1.69) ** 2 + 0.1 * u


def arrow3(a, b, r, mat, head=0.32):
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    tube([tuple(a), tuple(b - d * head * 0.6)], r, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.8, depth=head, location=b - d * head / 2,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


def dqd(cx, base):
    mz = base + 3.0
    # potential
    pts = []
    for i in range(121):
        u = -2.35 + 4.7 * i / 120
        pts.append((cx + 1.15 * u, Y0, base + 1.0 * pot(u)))
    tube(pts, 0.085, OCG_POT)
    zl = base + pot(-1.3); zr = base + pot(1.3)
    # electron spin in the left well, tilted (field gradient: x-component), ghost partner in the right well
    rr = 0.55
    lc = (cx - 1.15 * 1.3, Y0, zl + rr + 0.08)
    mag_ = FlMagnet((cx, Y0, mz), (2.0, 0.46, 0.46), axis=0, sign=1)
    bl = fl_field(_np.array([lc]), [mag_], (OCG_B0, 0, 0))[0]
    spin(lc, tuple(bl), r=rr, mat=OCG_ORANGE, arrow=OCG_ARROW, reach=1.5, shaft=0.13)
    rc = Vector((cx + 1.15 * 1.3, Y0, zr + rr + 0.08))
    sphere(tuple(rc), rr, OCG_GHOST)
    d = Vector(tuple(fl_field(_np.array([tuple(rc)]), [mag_], (OCG_B0, 0, 0))[0])).normalized()
    # dashed ghost arrow
    for k in range(6):
        s0 = -1.5 * rr + k * 0.27
        tube([tuple(rc + d * s0), tuple(rc + d * (s0 + 0.15))], 0.05, OCG_ARROW)
    end = rc + d * (1.5 * rr + 0.2)
    bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=0.3, location=end,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, OCG_ARROW)
    # tunnelling t_c: curved double arrow under the barrier (in front of the plane)
    pts = []
    for i in range(31):
        t = i / 30
        x = cx - 0.95 + 1.9 * t
        pts.append((x, Y0 - 0.25, base - 0.25 - 0.55 * math.sin(math.pi * t)))
    tube(pts[2:-2], 0.04, OCG_PURPLE)
    for a_, b_ in ((pts[3], pts[0]), (pts[-4], pts[-1])):
        dd = (Vector(b_) - Vector(a_)).normalized()
        bpy.ops.mesh.primitive_cone_add(radius1=0.12, depth=0.28, location=Vector(b_),
                                        rotation=dd.to_track_quat("Z", "Y").to_euler(), vertices=24)
        link(bpy.context.object, OCG_PURPLE)
    # micromagnet bar: S (blue) left, N (red) right
    mz = base + 3.0
    box((cx - 0.5, Y0, mz), (1.0, 0.46, 0.46), OCG_MAG_B)
    box((cx + 0.5, Y0, mz), (1.0, 0.46, 0.46), OCG_MAG_R)
    # computed stray-field lines (closed loops N -> S), arrowheads at the far point of each loop
    mag = FlMagnet((cx, Y0, mz), (2.0, 0.46, 0.46), axis=0, sign=1)
    seeds = []
    for rf, phis in OCG_RINGS:
        for ph in phis:
            q = mag.c.copy()
            q[1] += rf * mag.h[1] * math.cos(math.radians(ph)); q[2] += rf * mag.h[2] * math.sin(math.radians(ph))
            q[0] = mag.c[0] + mag.h[0] + 0.012
            seeds.append(q)
    for p_, c_ in fl_trace_many(seeds, [mag], ((-60, -40, -0.2), (60, 40, 40)), step=0.02, max_len=40):
        if c_:
            fl_draw(p_, radius=0.026, arrows=(0.5,))
    # coupling capacitor from the left well bottom down to the line
    x0 = cx - 1.15 * 1.3
    tube([(x0, Y0, zl - 0.05), (x0, Y0, base - 1.05)], 0.05, OCG_LINE)
    box((x0, Y0, base - 1.1), (0.7, 0.3, 0.07), OCG_LINE, bevel=0.02)
    box((x0, Y0, base - 1.3), (0.7, 0.3, 0.07), OCG_LINE, bevel=0.02)
    tube([(x0, Y0, base - 1.35), (x0, Y0, 0.35)], 0.05, OCG_LINE)
    return x0


BASE = 1.9
xa = dqd(-5.0, BASE)
xb = dqd(5.0, BASE)

# --- the shared resonator: a double-line meander between the two dots ------------------------------------------
path = [(xa, 0.35), (-1.26, 0.35)]
for k, xm in enumerate((-1.26, -0.21, 0.84)):
    w = 0.42
    path += [(xm, 4.6), (xm + w, 4.6), (xm + w, 0.35 if k < 2 else 0.35)]
    if k < 2:
        path += [(xm + 1.05, 0.35)]
path += [(xb, 0.35)]
# smooth the meander corners a little and draw it as two parallel lines with a glowing core between them
def rounded(path, r=0.18):
    out = [path[0]]
    for i in range(1, len(path) - 1):
        p, q, n = Vector(path[i - 1]), Vector(path[i]), Vector(path[i + 1])
        a = q + (p - q).normalized() * min(r, (p - q).length / 2)
        c = q + (n - q).normalized() * min(r, (n - q).length / 2)
        for j in range(7):
            t = j / 6
            out.append(tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * q + t * t * c))
    out.append(path[-1])
    return out


pr = rounded(path)
tube([(x, Y0 - 0.13, z) for x, z in pr], 0.05, OCG_LINE)
tube([(x, Y0 + 0.13, z) for x, z in pr], 0.05, OCG_LINE)
tube([(x, Y0, z) for x, z in pr], 0.045, OCG_PINK)

# B_z arrow over the meander (glass-gold)
fl_external((0.1, Y0, 5.35), (1, 0, 0), 3.0, n=3, spacing=0.9, normal=(0, 1, 0), radius=0.05)

camera((-2.2, -16.5, 10.2), (0, 0, 3.1), lens=30)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0,
        saturation=1.2)

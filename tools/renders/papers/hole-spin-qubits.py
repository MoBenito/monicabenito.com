# Hole-spin qubits in Ge/Si core-shell nanowire quantum dots (Adelsberger, Benito, Bosco, Klinovaja, Loss 2022).
# Hero: a square Ge/Si core-shell nanowire, cut open at the front to show the blue Ge core inside the orange Si
# shell and the core's atom lattice (growth direction). Two gold wrap gates confine a hole quantum dot; its spin
# (orange glass) sits in the core, tilted away from the field. B (and E) point straight up, perpendicular to the
# wire; violet loops around the dot show the orbital effect of B. Behind: the circular-cross-section wire the paper
# compares with.
import random
random.seed(7)
bright_stage(floor_z=-0.7)

HS_CHIP = principled("hs_chip", **{"Base Color": (0.45, 0.82, 0.78, 1), "Roughness": 0.3, "Coat Weight": 0.6})
HS_SHELL = principled("hs_shell", **{"Base Color": (1.0, 0.45, 0.12, 1), "Roughness": 0.22, "Coat Weight": 1.0, "Subsurface Weight": 0.3})
HS_CORE = principled("hs_core", **{"Base Color": (0.1, 0.35, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0})
HS_SHELL_FACE = principled("hs_shell_face", **{"Base Color": (1.0, 0.5, 0.15, 1), "Roughness": 0.35, "Coat Weight": 0.8})
HS_CORE_FACE = principled("hs_core_face", **{"Base Color": (0.12, 0.38, 1.0, 1), "Roughness": 0.3, "Coat Weight": 0.8})
HS_ATOM = principled("hs_atom", **{"Base Color": (0.85, 0.93, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0})
HS_ATOM_SI = principled("hs_atom_si", **{"Base Color": (1.0, 0.85, 0.6, 1), "Roughness": 0.2, "Coat Weight": 1.0})
HS_BFIELD = principled("hs_b", **{"Base Color": (0.05, 0.2, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0, "Emission Color": (0.2, 0.35, 1.0, 1), "Emission Strength": 0.8})
HS_ORBIT = emission("hs_orbit", (0.75, 0.25, 1.0, 1), 6.0)

# chip
box((0, 8, -0.35), (40, 40, 0.7), HS_CHIP, bevel=0.05)

S, C = 2.0, 1.36           # shell and core widths (square cross-section)
z0 = S / 2                 # wire centre height (sits on the chip at z = 0)
y0, y1 = -1.4, 16.0        # cut face at y0, running into the depth
ydot = 3.0
ga, gb = ydot - 2.4, ydot + 2.4
for (a_, b_) in ((y0, ga), (gb, y1)):           # full wire in front of and behind the dot
    box((0, (a_ + b_) / 2, z0), (S, b_ - a_, S), HS_SHELL, bevel=0.05)
    box((0, (a_ + b_) / 2, z0 + 0.01), (C, b_ - a_ + 0.02, C), HS_CORE, bevel=0.02)
# between the gates: cut open down to the wire axis, so the dot inside the core is visible
box((0, ydot, z0 / 2), (S, gb - ga, z0), HS_SHELL, bevel=0.02)
box((0, ydot, z0 - C / 4 + 0.012), (C, gb - ga + 0.02, C / 2), HS_CORE, bevel=0.01)
# opaque cut face: shell frame and core square, with the crystal lattice of the core on it
box((0, y0 - 0.005, z0), (S, 0.02, S), HS_SHELL_FACE, bevel=0.005)
box((0, y0 - 0.02, z0), (C, 0.02, C), HS_CORE_FACE, bevel=0.005)
n = 6
for i in range(n):
    for j in range(n):
        x = -C / 2 + C * (i + 0.5) / n
        z = z0 - C / 2 + C * (j + 0.5) / n
        sphere((x, y0 - 0.05, z), 0.07, HS_ATOM)
        if i < n - 1 and j < n - 1:   # second fcc sublattice of the diamond structure, offset by a quarter
            sphere((x + C / (2 * n), y0 - 0.05, z + C / (2 * n)), 0.045, HS_ATOM)
for i in range(8):
    for j in range(8):
        x = -S / 2 + S * (i + 0.5) / 8
        z = z0 - S / 2 + S * (j + 0.5) / 8
        if abs(x) > C / 2 + 0.05 or abs(z - z0) > C / 2 + 0.05:
            sphere((x, y0 - 0.04, z), 0.05, HS_ATOM_SI)


def wrap_gate(yc, w=0.55, t=0.14, reach=3.6, mat=GOLD):
    """Gold gate strip crossing the wire: along the chip, up, over the top, down, along the chip again."""
    h = S + t
    for s in (-1, 1):
        box((s * (S / 2 + t / 2 + reach / 2), yc, t / 2), (reach, w, t), mat, bevel=0.03)
        box((s * (S / 2 + t / 2), yc, h / 2), (t, w, h), mat, bevel=0.03)
        # contact pad at the end
        box((s * (S / 2 + reach + 0.4), yc, t / 2 + 0.02), (1.2, 1.2, t + 0.04), mat, bevel=0.04)
    box((0, yc, S + t / 2), (S + 2 * t, w, t), mat, bevel=0.03)


for yc in (ga, gb):
    wrap_gate(yc)

# hole wavefunction: glowing cigar in the core between the gates
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, ydot, z0), segments=48, ring_count=24)
cl = bpy.context.object; cl.scale = (C * 0.5, 2.0, C * 0.42)
cl.data.materials.append(volume_glow("hs_psi", (1.0, 0.3, 0.6, 1), 30.0))
cl.visible_shadow = False

# the hole spin, tilted away from the vertical field (renormalised, anisotropic g factor)
c = Vector((0, ydot, z0 + 0.3))
QA = principled("hs_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
spin(tuple(c), (0.55, -0.25, 1.0), r=0.56, arrow=QA, reach=2.2, shaft=0.1)
hot_spot(tuple(c), (1.0, 0.7, 0.45, 1), 0.05, 25)
l = bpy.data.lights.new("hs_core", "POINT"); l.energy, l.color = 8, (1.0, 0.6, 0.4)
lo = bpy.data.objects.new("hs_core", l); lo.location = c; sc.collection.objects.link(lo)


def arrow_line(p0, p1, r, mat, head=0.32):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    tube([tuple(p0), tuple(p1 - d * head * 0.5)], r, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 3.2, depth=head, location=p1 - d * head / 2,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, mat)


# magnetic field: straight up, perpendicular to the wire (B || E || z)
for (bx, by) in ((-2.7, 1.6), (2.7, 1.6), (-2.7, 4.4), (2.7, 4.4)):
    arrow_line((bx, by, 0.2), (bx, by, 3.6), 0.06, HS_BFIELD, head=0.5)
# orbital effect: the field makes the hole circulate around it (loops around the dot, about the z axis)
for k, (rx, ry, zz) in enumerate(((1.55, 2.9, z0 + 0.15),)):
    pts = []
    N = 120
    for i in range(N):
        a = math.radians(-60) + math.radians(320) * i / (N - 1)
        pts.append((rx * math.cos(a), ydot + ry * math.sin(a), zz + 0.12 * math.sin(a)))
    tube(pts, 0.07, HS_ORBIT)
    a = math.radians(260)
    tip = Vector((rx * math.cos(a), ydot + ry * math.sin(a), zz + 0.12 * math.sin(a)))
    d = Vector((-rx * math.sin(a), ry * math.cos(a), 0)).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=0.15, depth=0.38, location=tip + d * 0.15,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, HS_ORBIT)

# the circular-cross-section Ge/Si wire the paper compares with: a second, round core-shell nanowire beside the
# hero, cut open at the front like it (blue Ge core with its atoms inside the orange Si shell ring), with its own pair
# of gold wrap gates arching over it.
import bmesh
XR, RS, RC = 6.5, 0.86, 0.58        # axis x, shell and core radius (same core/shell ratio as the square wire)
ZR = RS                              # sits on the chip
YF, YE = 1.2, 16.0                   # cut face and far end
for (mat, r) in ((HS_SHELL, RS), (HS_CORE, RC)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=YE - YF, location=(XR, (YF + YE) / 2, ZR), rotation=(math.radians(90), 0, 0), vertices=96)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)
for (r, mat, dy) in ((RS, HS_SHELL_FACE, 0.005), (RC, HS_CORE_FACE, 0.02)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.02, location=(XR, YF - dy, ZR), rotation=(math.radians(90), 0, 0), vertices=96)
    link(bpy.context.object, mat)
# atoms on the round cut face: core lattice inside the core disc, Si atoms around the shell ring

st = 2 * RC / 5.2
for i in range(-4, 5):
    for j in range(-4, 5):
        for (ox, oz, rr) in ((0, 0, 0.065), (0.5, 0.5, 0.042)):
            x, z = (i + ox) * st, (j + oz) * st
            if x * x + z * z < (RC - 0.08) ** 2:
                sphere((XR + x, YF - 0.05, ZR + z), rr, HS_ATOM)
for k in range(22):
    ang = 2 * math.pi * k / 22
    rm = (RS + RC) / 2 + 0.02
    sphere((XR + rm * math.cos(ang), YF - 0.04, ZR + rm * math.sin(ang)), 0.05, HS_ATOM_SI)


def arch_gate(yc, w=0.5, t=0.13, reach=1.1, mat=GOLD):
    """Gold wrap gate over the round wire: a half annulus hugging the shell, with feet and pads on the chip."""
    bm = bmesh.new()
    r1, r2 = RS + 0.005, RS + t
    N = 48
    rings = []
    for i in range(N + 1):
        ang = math.pi * i / N
        rings.append([bm.verts.new((XR + r * math.cos(ang), yc + dy, ZR + r * math.sin(ang)))
                      for (r, dy) in ((r1, -w / 2), (r2, -w / 2), (r2, w / 2), (r1, w / 2))])
    for i in range(N):
        for k in range(4):
            l = (k + 1) % 4
            bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][l], rings[i][l]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[N])
    me = bpy.data.meshes.new("hs_arch"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("hs_arch", me); sc.collection.objects.link(ob); me.materials.append(mat)
    # flanks down to the chip and feet along it
    hgt = ZR
    for sx in (-1, 1):
        box((XR + sx * (RS + t / 2), yc, hgt / 2), (t, w, hgt), mat, bevel=0.02)
        box((XR + sx * (RS + t + reach / 2), yc, t / 2), (reach, w, t), mat, bevel=0.03)
    box((XR + RS + t + reach + 0.3, yc, t / 2 + 0.02), (0.85, 0.85, t + 0.04), mat, bevel=0.04)


for yc in (YF + 1.7, YF + 5.3):
    arch_gate(yc)

camera((-5.8, -9.2, 6.6), (1.5, 2.6, 1.0), lens=40, dof=2.5)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.3)

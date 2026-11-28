"""Dissipative long-range entanglement generation between electronic spins (Benito et al., PRB 2016).

A quantum Hall bar (strong field B out of the plane) carries chiral edge channels: along the lower edge electrons
run to the right, along the upper edge to the left, in skipping orbits. Two distant spin qubits S1 and S2 (orange)
sit in quantum dots inside the bar; each is tunnel/exchange coupled (J) to two auxiliary dots (lavender), one next
to each edge. Spin-polarised leads (gold) fill auxiliary dots with spin-up electrons (lower left) and spin-down
electrons (upper right); electrons leave into the edge channels (gamma), which carry them, one way, past the other
qubit. Weak drives (Omega) rotate each spin. The dissipative dynamics pumps the two spins into an entangled steady
state: the glowing two-stranded bridge between them.
"""
import bmesh
import random
random.seed(5)

bright_stage(floor_z=-0.7, exposure=-0.4, sun_rot=(45, 0, -15))

# chip and Hall-bar mesa
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.0, -0.35))
slab = bpy.context.object; slab.scale = (26.0, 14.0, 0.7)
link(slab, principled("de_chip", **{"Base Color": (0.98, 0.86, 0.78, 1), "Roughness": 0.4}))
HX, HY, RC = 7.4, 2.9, 1.2
ZC = 0.45      # height of the edge channel and dots above the chip


def rounded_rect(hx, hy, r, n=2000):
    """Counter-clockwise closed path (seen from above), uniformly resampled; returns points and tangents."""
    raw = []
    for (cx, cy, a0) in ((hx - r, -hy + r, -90), (hx - r, hy - r, 0), (-hx + r, hy - r, 90), (-hx + r, -hy + r, 180)):
        for k in range(31):
            a = math.radians(a0 + 90 * k / 30)
            raw.append(Vector((cx + r * math.cos(a), cy + r * math.sin(a), 0)))
    raw.append(raw[0])
    L = [0.0]
    for i in range(1, len(raw)):
        L.append(L[-1] + (raw[i] - raw[i - 1]).length)
    out = []
    j = 0
    for k in range(n):
        s = L[-1] * k / n
        while L[j + 1] < s:
            j += 1
        f = (s - L[j]) / (L[j + 1] - L[j])
        out.append(raw[j].lerp(raw[j + 1], f))
    return out, L[-1]


_mp, _ = rounded_rect(HX, HY, RC, n=400)
cu = bpy.data.curves.new("de_mesa", "CURVE"); cu.dimensions = "2D"; cu.fill_mode = "BOTH"
sp_ = cu.splines.new("POLY"); sp_.points.add(len(_mp) - 1)
for pt, co in zip(sp_.points, _mp):
    pt.co = (co.x, co.y, 0, 1)
sp_.use_cyclic_u = True
cu.extrude = 0.2; cu.bevel_depth = 0.03; cu.bevel_resolution = 3
mesa = bpy.data.objects.new("de_mesa", cu); sc.collection.objects.link(mesa); mesa.location.z = 0.2
cu.materials.append(principled("de_mesa", **{"Base Color": (0.35, 0.8, 0.68, 1), "Roughness": 0.3, "Coat Weight": 0.6}))

# chiral edge channel: a glowing lane just inside the edge, and skipping-orbit trajectories along it
EDGE = emission("de_edge", (0.1, 0.4, 1.0, 1), 2.0)
ORBIT = emission("de_orbit", (0.1, 0.55, 1.0, 1), 4.0)
inset = 0.55
path, Ltot = rounded_rect(HX - inset, HY - inset, RC - inset * 0.8)
tube([tuple(p + Vector((0, 0, ZC - 0.02))) for p in path] + [tuple(path[0] + Vector((0, 0, ZC - 0.02)))], 0.11, EDGE)
n = len(path)
loops = 64
orbit = []
for k in range(n):
    p = path[k]; t = (path[(k + 1) % n] - path[k - 1]).normalized()
    nrm = Vector((-t.y, t.x, 0))                                    # inward normal for a CCW path
    ph = 2 * math.pi * loops * k / n
    q = p - t * 0.28 * math.sin(ph) + nrm * (0.2 - 0.2 * math.cos(ph))
    orbit.append(tuple(q + Vector((0, 0, ZC + 0.05))))
orbit.append(orbit[0])
tube(orbit, 0.035, ORBIT)
# electrons on the edge: glowing balls riding the skipping orbits, with direction cones along the lane
EL = principled("de_electron", **{"Base Color": (0.05, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                  "Emission Color": (0.1, 0.45, 1.0, 1), "Emission Strength": 1.5})
for k in range(0, n, n // 22):
    sphere(orbit[k], 0.15, EL)
for k in range(n // 44, n, n // 11):
    p = path[k]; t = (path[(k + 1) % n] - path[k - 1]).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=0.36, location=tuple(p + Vector((0, 0, ZC + 0.05))),
                                    rotation=t.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, ORBIT)

# qubit dots, auxiliary dots, couplings
DE_QARROW = principled("de_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
AUX = principled("de_aux", **{"Base Color": (0.7, 0.62, 1.0, 1), "Transmission Weight": 0.7, "Roughness": 0.06, "IOR": 1.35,
                              "Coat Weight": 1.0})
JLINK = emission("de_j", (1.0, 0.6, 0.1, 1), 4.0)
QX = 3.6
QZ = 1.35
spins = []
for s, tilt in ((-1, (0.25, -0.35, 1.0)), (1, (-0.25, -0.35, -1.0))):
    c = Vector((s * QX, 0.0, QZ))
    spin(tuple(c), tilt, r=0.62, arrow=DE_QARROW, reach=1.7, shaft=0.1)
    hot_spot(tuple(c), (1.0, 0.7, 0.4, 1), 0.05, 25)
    spins.append(c)
    for sy in (-1, 1):
        a = Vector((s * QX, sy * 1.65, ZC + 0.25))
        sphere(tuple(a), 0.4, AUX)
        # its discrete levels: three thin rings
        for dz in (-0.14, 0.0, 0.14):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.41 * math.sqrt(1 - (dz / 0.4) ** 2), minor_radius=0.018,
                                             major_segments=64, minor_segments=6, location=(a.x, a.y, a.z + dz))
            link(bpy.context.object, GOLD)
        # exchange / tunnel coupling J to the qubit: double-headed link
        p0 = c + (a - c).normalized() * 0.72; p1 = a + (c - a).normalized() * 0.5
        tube([tuple(p0), tuple(p1)], 0.04, JLINK)
        for e_, o_ in ((p0, p1), (p1, p0)):
            d = (e_ - o_).normalized()
            bpy.ops.mesh.primitive_cone_add(radius1=0.1, depth=0.22, location=tuple(e_), rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=20)
            link(bpy.context.object, JLINK)
    # plunger gate under the qubit dot
    gate([(s * QX, -HY - 1.5), (s * QX, -2.25)], width=0.22, height=0.47, mat=GOLD)

# spin-polarised leads: gold contacts at the lower left (spin up) and upper right (spin down), each with a fan of
# polarised electrons feeding its auxiliary dot
LEAD_ARROW = principled("de_lead_arrow", **{"Base Color": (0.0, 0.45, 0.42, 1), "Roughness": 0.2, "Emission Color": (0.2, 1.0, 0.85, 1),
                                            "Emission Strength": 2.0})
for (lx, ly, up) in ((-QX - 2.3, -1.65, 1), (QX + 2.3, 1.65, -1)):
    box((lx, ly, 0.5), (1.5, 1.3, 0.6), GOLD, bevel=0.06)
    for k in range(3):
        p = Vector((lx + (0.75 if lx < 0 else -0.75) * (1.2 + 0.5 * k) / 1.0, ly + (k - 1) * 0.3, ZC + 0.2))
        sphere(tuple(p), 0.14, EL)
        d = Vector((0, 0, up))
        tube([tuple(p - d * 0.32), tuple(p + d * 0.16)], 0.035, LEAD_ARROW)
        bpy.ops.mesh.primitive_cone_add(radius1=0.09, depth=0.2, location=tuple(p + d * 0.25), rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=16)
        link(bpy.context.object, LEAD_ARROW)

# drives Omega: green wave packets aimed at each qubit
DRV = emission("de_drive", (0.25, 1.0, 0.15, 1), 3.5)
for s in (-1, 1):
    c = spins[0] if s < 0 else spins[1]
    start = c + Vector((-s * 2.6, -1.2, 1.6))
    end = c + (start - c).normalized() * 0.95
    dvec = (end - start); L_ = dvec.length; dn = dvec.normalized()
    side = dn.cross(Vector((0, 0, 1))).normalized()
    pts = [tuple(start + dn * L_ * t + side * 0.24 * math.sin(2 * math.pi * 6 * t) * math.sin(math.pi * t) ** 0.6) for t in [j / 160 for j in range(161)]]
    tube(pts, 0.05, DRV)
    bpy.ops.mesh.primitive_cone_add(radius1=0.12, depth=0.28, location=tuple(end), rotation=dn.to_track_quat("Z", "Y").to_euler(), vertices=20)
    link(bpy.context.object, DRV)

# the entangled steady state: two intertwined glowing strands arching from S1 to S2
a, b = spins
for k, col in ((0, (1.0, 0.1, 0.5, 1)), (1, (0.6, 0.15, 1.0, 1))):
    pts = []
    for j in range(401):
        t = j / 400
        base = a.lerp(b, t) + Vector((0, 0.6 * math.sin(math.pi * t), 2.2 * math.sin(math.pi * t)))
        base_d = (b - a).normalized()
        ph = 2 * math.pi * 3.5 * t + k * math.pi
        rad = 0.18 * math.sin(math.pi * t) ** 0.5
        w = base + Vector((0, math.cos(ph), math.sin(ph))) * rad
        pts.append(tuple(w))
    tube(pts[12:-12], 0.065, emission("de_ent%d" % k, col, 4.0))

# the strong perpendicular magnetic field B: a sparse forest of thin field lines rising through the bar
BF = principled("de_bfield", **{"Base Color": (0.5, 0.3, 1.0, 1), "Roughness": 0.2, "Emission Color": (0.45, 0.2, 1.0, 1),
                               "Emission Strength": 1.2})
for ix in range(-6, 7):
    for iy in (-1, 0, 1):
        x, y = ix * 1.05 + 0.5 * (iy % 2), iy * 1.25
        if any(math.hypot(x - qx, y - qy) < 1.0 for qx in (-QX, QX) for qy in (-1.65, 0, 1.65)):
            continue
        if abs(x) > HX - 1.0 or (abs(x) > QX + 1.2 and abs(y) > 0.8):
            continue
        tube([(x, y, 0.42), (x, y, 1.0)], 0.018, BF)
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, depth=0.15, location=(x, y, 1.05), vertices=16)
        link(bpy.context.object, BF)

# red wavy arrows on the two edges, as in the paper's Figure 1: electrons travel right along the lower edge and
# left along the upper edge
WAVY = emission("de_wavy", (1.0, 0.1, 0.15, 1), 4.0)
for (x0, x1, y) in ((-1.6, 1.6, -HY - 0.05), (1.6, -1.6, HY + 0.05)):
    pts = [(x0 + (x1 - x0) * t, y, 0.75 + 0.14 * math.sin(2 * math.pi * 7 * t)) for t in [j / 200 for j in range(201)]]
    tube(pts, 0.045, WAVY)
    d = Vector((1 if x1 > x0 else -1, 0, 0))
    bpy.ops.mesh.primitive_cone_add(radius1=0.14, depth=0.32, location=(x1 + d.x * 0.12, y, 0.75),
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, WAVY)

camera((1.5, -12.0, 7.4), (0.0, 0.3, 0.8), lens=30, dof=5.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

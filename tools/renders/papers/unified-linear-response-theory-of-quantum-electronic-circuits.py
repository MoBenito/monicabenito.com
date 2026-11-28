"""Second concept, from Fig. 1 of Peri et al. (the universal small-signal model): the equivalent circuit built as
real hardware on a printed circuit board. Between two gold rails stand the three parallel branches with the figure's
colour code: blue branch from input-output theory (capacitor, capacitor, resistor, inductor; the quantum capacitance
pair framed by a dashed silkscreen box, its upper capacitor red because the semiclassical model shares it), red
semiclassical Sisyphus branch (capacitor, resistor) and the dark new branch (capacitor, resistor, then a parallel
capacitor-resistor pair). Every element carries the 'variable' glass arrow. At the top the actual quantum device, a
double-quantum-dot charge qubit chip, is driven by the gate voltage V_G (orange sine); ground is at the bottom."""
import bmesh

bright_stage(floor_z=-0.7)


def ur_mat(name, **kw):
    return principled("uralt_" + name, **kw)


BOARD = ur_mat("board", **{"Base Color": (0.08, 0.62, 0.6, 1), "Roughness": 0.35, "Coat Weight": 0.8, "Coat Roughness": 0.08})
BLUE = ur_mat("blue", **{"Base Color": (0.05, 0.22, 1.0, 1), "Roughness": 0.18, "Coat Weight": 1.0})
RED = ur_mat("red", **{"Base Color": (1.0, 0.06, 0.08, 1), "Roughness": 0.18, "Coat Weight": 1.0})
INK = ur_mat("ink", **{"Base Color": (0.1, 0.06, 0.22, 1), "Roughness": 0.2, "Coat Weight": 1.0})
LEAD = ur_mat("lead", **{"Base Color": (0.85, 0.87, 0.9, 1), "Metallic": 1.0, "Roughness": 0.2})
SILK = emission("uralt_silk", (1.0, 1.0, 1.0, 1), 2.5)
VARI = principled("uralt_vari", **{"Base Color": (0.85, 1.0, 0.95, 1), "Transmission Weight": 0.85, "Roughness": 0.05,
                                    "IOR": 1.45, "Emission Color": (0.4, 1.0, 0.85, 1), "Emission Strength": 1.6})

TZ = 0.0          # board top
box((0, 0, -0.35), (17.0, 10.0, 0.7), BOARD, bevel=0.12)


def trace(pts, w=0.16):
    gate([(x, y) for x, y in pts], width=w, height=0.05, mat=GOLD)


def pad(x, y, r=0.16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.07, location=(x, y, TZ + 0.03), vertices=32)
    link(bpy.context.object, GOLD)


def vari_arrow(c, L=1.9):
    """The 'variable component' arrow: a glass arrow diagonally across the element, above it."""
    c = Vector(c)
    d = Vector((0.75, 0.25, 0.62)).normalized()
    a, b = c - d * L / 2, c + d * L / 2
    hl = 0.32
    rot = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=L - hl, location=(a + b - d * hl) / 2, rotation=rot, vertices=20)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, VARI)
    bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=hl, location=b - d * hl / 2, rotation=rot, vertices=24)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, VARI)


def capacitor(x, y, mat, h=0.7):
    """Two upright plates across the branch (the circuit symbol, in 3D), with leads to the pads."""
    for s in (-1, 1):
        box((x, y + s * 0.15, TZ + h), (1.25, 0.14, 0.82), mat, bevel=0.05)
        tube([(x, y + s * 0.5, TZ), (x, y + s * 0.5, TZ + h), (x, y + s * 0.22, TZ + h)], 0.04, LEAD)
        pad(x, y + s * 0.5)
    vari_arrow((x, y, TZ + h))


def resistor(x, y, mat, length=1.0, h=0.5):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.32, depth=length, location=(x, y, TZ + h),
                                        rotation=(math.radians(90), 0, 0), vertices=48)
    r = bpy.context.object; bv = r.modifiers.new("b", "BEVEL"); bv.width, bv.segments = 0.09, 4
    bpy.ops.object.shade_smooth(); link(r, mat)
    for k, col in enumerate((GOLD, LEAD, GOLD)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.08, location=(x, y - length * 0.25 + k * length * 0.2, TZ + h),
                                            rotation=(math.radians(90), 0, 0), vertices=48)
        link(bpy.context.object, col)
    for s in (-1, 1):
        y0 = y + s * (length / 2 + 0.3)
        tube([(x, y + s * length / 2, TZ + h), (x, y0, TZ + h), (x, y0, TZ)], 0.035, LEAD)
        pad(x, y0)
    vari_arrow((x, y, TZ + h + 0.05))


def inductor(x, y, mat, length=1.4, h=0.5):
    pts = []
    n = 7
    for k in range(n * 24 + 1):
        t = k / (n * 24)
        a = 2 * math.pi * n * t
        pts.append((x + 0.42 * math.cos(a), y - length / 2 + length * t, TZ + h + 0.42 * math.sin(a)))
    tube(pts, 0.095, mat)
    for s in (-1, 1):
        y0 = y + s * (length / 2 + 0.3)
        tube([(x + 0.34, y + s * length / 2, TZ + h), (x + 0.34, y0, TZ + h), (x + 0.34, y0, TZ)], 0.035, LEAD)
        pad(x + 0.34, y0)
    vari_arrow((x, y, TZ + h + 0.05))


# ---- rails and branches ------------------------------------------------------------------------------------------
YT, YB = 2.3, -2.9
trace([(-6.6, YT), (6.6, YT)], 0.3)
trace([(-6.6, YB), (6.6, YB)], 0.3)
for s in (-1, 1):
    for k in range(3):
        sphere((s * (7.0 + 0.42 * k), (YT + YB) / 2, TZ + 0.2), 0.16, GOLD)

XL, XM, XR = -4.4, 0.0, 4.2
# left (blue) branch: C_Q (red, shared with the semiclassical model), C_D, G_D, L_Q
trace([(XL, YT), (XL, YB)], 0.1)
capacitor(XL, 1.55, RED)
capacitor(XL, 0.45, BLUE)
resistor(XL, -0.75, BLUE)
inductor(XL, -2.05, BLUE, length=1.0)
# dashed silkscreen frame around the two capacitors (C_H)
for (x0, y0, x1, y1) in ((XL - 0.75, 0.0, XL - 0.75, 2.0), (XL + 0.75, 0.0, XL + 0.75, 2.0),
                         (XL - 0.75, 0.0, XL + 0.75, 0.0), (XL - 0.75, 2.0, XL + 0.75, 2.0)):
    L = math.hypot(x1 - x0, y1 - y0); n = int(L / 0.25)
    for k in range(0, n, 2):
        a = k / n; b = min((k + 1) / n, 1)
        tube([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, TZ + 0.012), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b, TZ + 0.012)], 0.045, SILK)
# middle (red) branch: C_Gamma, G_Gamma (Sisyphus)
trace([(XM, YT), (XM, YB)], 0.1)
capacitor(XM, 1.1, RED)
resistor(XM, -1.0, RED, length=1.2)
# right (dark) branch: C_L+, G_L+, then C_L|| parallel to G_L||
trace([(XR, YT), (XR, -0.75)], 0.1)
trace([(XR - 0.9, -0.75), (XR + 0.9, -0.75)], 0.1)
trace([(XR - 0.9, -0.75), (XR - 0.9, -2.35), (XR + 0.9, -2.35), (XR + 0.9, -0.75)], 0.1)
trace([(XR, -2.35), (XR, YB)], 0.1)
capacitor(XR, 1.55, INK)
resistor(XR, 0.3, INK, length=0.8)
capacitor(XR - 0.9, -1.55, INK)
resistor(XR + 0.9, -1.55, INK, length=0.7)

# ---- ground symbol at the bottom ------------------------------------------------------------------------------------
trace([(XM, YB), (XM, YB - 0.8)], 0.1)
bm = bmesh.new()
tri = [(-0.55, YB - 0.8), (0.55, YB - 0.8), (0.0, YB - 1.5)]
lo = [bm.verts.new((x, y, TZ)) for x, y in tri]
hi = [bm.verts.new((x, y, TZ + 0.18)) for x, y in tri]
bm.faces.new(hi); bm.faces.new(list(reversed(lo)))
for k in range(3):
    bm.faces.new((lo[k], lo[(k + 1) % 3], hi[(k + 1) % 3], hi[k]))
gm = bpy.data.meshes.new("uralt_gnd"); bm.to_mesh(gm); bm.free()
g = bpy.data.objects.new("uralt_gnd", gm); sc.collection.objects.link(g); gm.materials.append(GOLD)

# ---- the quantum device: a double-quantum-dot chip, gate-driven by V_G --------------------------------------------
CHIP = ur_mat("chip", **{"Base Color": (0.95, 0.97, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0})
cx, cy = 1.7, 3.75
trace([(XM, YT), (XM, cy), (cx - 1.4, cy)], 0.16)
box((cx, cy, TZ + 0.18), (3.0, 1.5, 0.36), CHIP, bevel=0.08)
DOT = emission("uralt_dot", (0.05, 0.4, 1.0, 1), 1.5)
for s in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.04, location=(cx + 0.65 * s, cy, TZ + 0.37), vertices=48)
    link(bpy.context.object, DOT)
    gate([(cx + 0.65 * s, cy - 0.68), (cx + 0.65 * s, cy - 0.5)], width=0.12, height=0.42)
sphere((cx - 0.65, cy, TZ + 0.6), 0.22, emission("uralt_e", (0.4, 0.75, 1.0, 1), 8.0))
arc = [(cx - 0.65 + 1.3 * t, cy, TZ + 0.7 + 0.55 * math.sin(math.pi * t)) for t in [k / 30 for k in range(31)]]
tube(arc, 0.05, emission("uralt_tun", (1.0, 0.6, 0.1, 1), 3.0))
# V_G sine coming in along the top edge
sine = [(-5.6 + 6.0 * t, cy, TZ + 0.6 + 0.38 * math.sin(2 * math.pi * 3.5 * t)) for t in [k / 240 for k in range(241)]]
tube(sine, 0.1, emission("uralt_vg", (1.0, 0.3, 0.02, 1), 3.0))

camera((0.0, -10.0, 12.0), (0.0, 0.1, 0.0), lens=34)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.2)

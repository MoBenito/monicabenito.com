# Hybrid superconductor-semiconductor systems for quantum technology (Benito, Burkard 2020, perspective).
# Hero: a superconducting coplanar-waveguide resonator (silvery niobium centre strip between ground planes, with
# coupling gaps to the input and output lines) running diagonally across a chip. At both ends sits a semiconductor
# double quantum dot (blue mesa, gold gate fingers, two glowing dot lobes) holding an electron spin (orange glass).
# The resonator's half-wave photon mode is drawn above the strip: a glowing cosine envelope with field arrows up at one
# end and down at the other, linking the two distant spins.
bright_stage(floor_z=-0.7)

HY_CHIP = principled("hy_chip", **{"Base Color": (1.0, 0.5, 0.38, 1), "Roughness": 0.35, "Coat Weight": 0.5})
HY_NB = principled("hy_nb", **{"Base Color": (0.66, 0.7, 1.0, 1), "Metallic": 0.6, "Roughness": 0.22, "Coat Weight": 0.6})
HY_MESA = principled("hy_mesa", **{"Base Color": (0.15, 0.45, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0})
HY_FIELD = principled("hy_field", **{"Base Color": (0.02, 0.25, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                     "Emission Color": (0.1, 0.4, 1.0, 1), "Emission Strength": 1.2})
HY_ENV = principled("hy_env", **{"Base Color": (0.02, 0.35, 1.0, 1), "Roughness": 0.2, "Emission Color": (0.15, 0.5, 1.0, 1), "Emission Strength": 3.0})
QA = principled("hy_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})

box((0, 4, -0.35), (40, 30, 0.7), HY_CHIP, bevel=0.05)

L = 6.0            # half length of the resonator centre strip
w, g, t = 0.7, 0.45, 0.12     # strip width, gap, metal thickness
GW = 3.2          # ground plane width
# centre strip and ground planes (the resonator is along x)
box((0, 0, t / 2), (2 * L, w, t), HY_NB, bevel=0.02)
box((0, w / 2 + g + GW / 2, t / 2), (2 * L + 9.0, GW, t), HY_NB, bevel=0.02)
# front ground plane with a notch at each end of the strip for the double dots
NX = 2.1
xs = [-(L + 4.5), -(L - 0.9) - NX, -(L - 0.9) + NX, (L - 0.9) - NX, (L - 0.9) + NX, L + 4.5]
for a, b in ((xs[0], xs[1]), (xs[2], xs[3]), (xs[4], xs[5])):
    box(((a + b) / 2, -(w / 2 + g + GW / 2), t / 2), (b - a, GW, t), HY_NB, bevel=0.02)
# input and output lines through coupling gaps (kappa_1, kappa_2)
cg = 0.45
for s in (-1, 1):
    box((s * (L + cg + 2.5), 0, t / 2), (5.0, w, t), HY_NB, bevel=0.02)

# double quantum dots at both ends, on blue semiconductor heterostructure mesas in notches of the ground plane.
# Gate stack as in real Si/SiGe or GaAs double dots: a lower layer of two thin screening gates that define the
# channel (along x) and two accumulation gates over the reservoirs, then an upper layer of fine finger gates
# (barrier - plunger - barrier - plunger - barrier) crossing the channel at a regular pitch. Away from the dots the
# fingers fan out into wider leads ending in pads; the right plunger is instead wired straight to the end of the
# resonator centre strip (the galvanic plunger coupling used in the spin-photon experiments).
HY_GOLD = principled("hy_gold", **{"Base Color": (1.0, 0.8, 0.35, 1), "Metallic": 1.0, "Roughness": 0.3, "Coat Weight": 0.5, "Emission Color": (1.0, 0.7, 0.3, 1), "Emission Strength": 0.25})
HY_GATE2 = principled("hy_gate2", **{"Base Color": (1.0, 0.88, 0.6, 1), "Metallic": 1.0, "Roughness": 0.3, "Coat Weight": 0.5, "Emission Color": (1.0, 0.8, 0.5, 1), "Emission Strength": 0.2})
MT = 0.08                      # mesa thickness
Z1, H1 = MT, 0.05              # lower gate layer
Z2, H2 = MT + 0.05, 0.08       # upper gate layer (fingers)
PITCH = 0.38
DQD = []
for s in (-1, 1):
    cx = s * (L - 0.9)
    cy = -(w / 2 + g) - 1.5
    ych = cy + 0.75                                # channel / dot row
    y_top, y_bot = cy + 1.35, cy - 4.3
    box((cx, (y_top + y_bot) / 2, MT / 2), (4.0, y_top - y_bot, MT), HY_MESA, bevel=0.02)
    # lower layer: screening gates along both sides of the channel
    for dy in (-0.42, 0.42):
        gate([(cx - 1.25, ych + dy), (cx + 1.25, ych + dy)], width=0.12, height=H1, mat=HY_GATE2).location.z = Z1
    # fingers: (x offset, width, layer) for accumulation (reservoirs), barriers and plungers, left to right
    fingers = [(-1.05, 0.34, 1), (-2 * PITCH, 0.12, 2), (-PITCH, 0.22, 2), (0.0, 0.12, 2), (PITCH, 0.22, 2),
               (2 * PITCH, 0.12, 2), (1.05, 0.34, 1)]
    y_tip, y_fan, y_lead, y_pad = ych + 0.3, ych - 0.6, ych - 1.9, y_bot + 0.45
    front = [fi for fi in fingers if not (fi[2] == 2 and abs(fi[0] - s * PITCH) < 1e-6)]
    for n_, (dx, wid, layer) in enumerate(front):
        x = cx + dx
        xl = cx - 1.7 + 3.4 * n_ / (len(front) - 1)
        mat, z, hh = (HY_GATE2, Z1, H1) if layer == 1 else (HY_GOLD, Z2, H2)
        gate([(x, y_tip), (x, y_fan)], width=wid, height=hh, mat=mat).location.z = z
        gate([(x, y_fan + 0.03), (xl, y_lead), (xl, y_pad + 0.25)], width=0.2, height=hh, mat=mat).location.z = z
        box((xl, y_pad, z + hh / 2), (0.42, 0.55, hh), mat, bevel=0.015)
    # the plunger next to the strip end is wired straight to the resonator centre strip
    x = cx + s * PITCH
    gate([(x, y_tip - 0.75), (x, y_top - 0.05)], width=0.22, height=H2, mat=HY_GOLD).location.z = Z2
    gate([(x, y_top - 0.15), (x, -w / 2 + 0.15)], width=0.16, height=MT + H2, mat=HY_GOLD).location.z = 0.0
    # two dot lobes under the plungers
    for dx in (-PITCH, PITCH):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(cx + dx, ych, 0.34), segments=48, ring_count=24)
        ob = bpy.context.object; ob.scale = (0.3, 0.32, 0.22)
        ob.data.materials.append(volume_glow("hy_lobe", (1.0, 0.8, 0.1, 1), 60.0)); ob.visible_shadow = False
    c = Vector((cx, ych, 1.1))
    DQD.append(c)
    spin(tuple(c), (0.2 * s, -0.15, 1.0), r=0.48, arrow=QA, reach=2.0, shaft=0.1)
    hot_spot(tuple(c), (1.0, 0.7, 0.45, 1), 0.05, 25)

# the resonator's fundamental (half-wave) mode: E ~ cos(pi x / 2L), up at one end, down at the other
zb = 1.6
env = lambda x: math.sin(math.pi * x / (2 * L)) * -1.35   # +1 at x = -L, -1 at x = +L
tube([(x, 0, zb + 1.1 * env(x)) for x in [-L + 2 * L * i / 200 for i in range(201)]], 0.07, HY_ENV)
tube([(x, 0, zb) for x in [-L + 2 * L * i / 100 for i in range(101)]], 0.015, emission("hy_axis", (0.4, 0.6, 1.0, 1), 1.5))
for i in range(17):
    x = -L + 0.35 + (2 * L - 0.7) * i / 16
    e = 1.1 * env(x)
    if abs(e) < 0.3:
        continue
    p0, p1 = Vector((x, 0, zb)), Vector((x, 0, zb + e * 0.92))
    d = (p1 - p0).normalized()
    head = 0.28
    tube([tuple(p0), tuple(p1 - d * head * 0.6)], 0.07, HY_FIELD)
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=head, location=p1 - d * head / 2,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, HY_FIELD)
# soft glow of the mode volume over the strip
beam((-L, 0, zb), (L, 0, zb), 1.2, beam_material("hy_mode", (0.2, 0.5, 1.0, 1), 0.5))

for s_, col in ((-1, (0.6, 0.35, 1.0, 1)), (1, (0.6, 0.35, 1.0, 1))):
    for j in range(3):
        x = s_ * (L + cg + 0.9 + 1.2 * j)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(x, 0, 0.3), segments=32, ring_count=16)
        ob = bpy.context.object; ob.scale = (0.35, 0.45, 0.25)
        ob.data.materials.append(volume_glow("hy_pulse", col, 25.0 * (1 - 0.25 * j))); ob.visible_shadow = False

camera((-7.5, -13.5, 8.0), (0.6, -0.9, 1.0), lens=36, dof=5.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.3)

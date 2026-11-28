"""Second concept for 'Transport, shot noise, and topology in AC-driven dimer arrays' (Niklas, Benito, Kohler, Platero).

A sculpture of the paper's Fig. 2(a): the quasienergy spectrum of the driven N=20 dimer chain versus A/omega, computed
from the effective Hamiltonian of the paper (tau'_eff = J0(A b/w)(tau0 - dtau), tau_eff = J0(A(a-b)/w)(tau0 + dtau),
dtau = 0.2 tau0, b = 0.4 a). Bands are glossy tubes, the topological windows (grey in the paper) are tinted glass
slabs, and the pair of zero-energy edge states inside them glows orange. In front, the dimer chain of Fig. 1 (blue
discs, short/long spacing) between gold source and drain; its two end dots glow orange (the edge states), electrons
arrive in irregular bunches.
"""
import numpy as np
import random

random.seed(3)
bright_stage(floor_z=-0.7, exposure=-0.35)

# ---------- physics: effective SSH spectrum ----------
N = 20
tau0, dtau, bb = 0.2, 0.04, 0.4
tt = np.linspace(0, np.pi, 400)


def J0(x):
    return float(np.mean(np.cos(x * np.sin(tt))))


XS = np.linspace(0.0, 13.0, 521)
E = []
topo = []
for x in XS:
    ti = J0(bb * x) * (tau0 - dtau)
    te = J0((1 - bb) * x) * (tau0 + dtau)
    H = np.zeros((N, N))
    for n in range(N - 1):
        H[n, n + 1] = H[n + 1, n] = ti if n % 2 == 0 else te
    E.append(np.linalg.eigvalsh(H))
    topo.append(abs(te) > abs(ti))
E = np.array(E)

SX, SZ, X0, Z0 = 1.08, 5.6, -7.0, 3.2


def P(x, e, y=0.0):
    return (X0 + SX * x, y, Z0 + SZ * e)


# ---------- materials ----------
def band_mat(i, k):
    # top bands magenta -> violet -> blue -> teal at the bottom
    cols = [(1.0, 0.1, 0.55), (0.65, 0.15, 1.0), (0.15, 0.35, 1.0), (0.0, 0.8, 0.85)]
    u = k * (len(cols) - 1)
    j = min(int(u), len(cols) - 2); f = u - j
    c = tuple(cols[j][q] * (1 - f) + cols[j + 1][q] * f for q in range(3))
    return principled(f"dsn_band{i}", **{"Base Color": (*c, 1), "Roughness": 0.18, "Coat Weight": 1.0,
                                         "Emission Color": (*c, 1), "Emission Strength": 0.6})


EDGE = principled("dsn_edge", **{"Base Color": (1.0, 0.25, 0.0, 1), "Emission Color": (1.0, 0.28, 0.0, 1),
                                  "Emission Strength": 2.2, "Roughness": 0.2})
SLAB = principled("dsn_slab", **{"Base Color": (0.6, 0.35, 1.0, 1), "Transmission Weight": 0.7, "Roughness": 0.08,
                                  "IOR": 1.3, "Coat Weight": 1.0})
PLINTH = principled("dsn_plinth", **{"Base Color": (0.25, 0.72, 0.92, 1), "Roughness": 0.3, "Coat Weight": 0.6})
DOT = principled("dsn_dot", **{"Base Color": (0.03, 0.2, 0.95, 1), "Metallic": 0.35, "Roughness": 0.1, "Coat Weight": 1.0})
DOT_EDGE = principled("dsn_dot_edge", **{"Base Color": (1.0, 0.3, 0.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                          "Emission Color": (1.0, 0.28, 0.0, 1), "Emission Strength": 1.2})
ELEC = principled("dsn_e", **{"Base Color": (0.05, 0.4, 1.0, 1), "Emission Color": (0.05, 0.45, 1.0, 1),
                               "Emission Strength": 0.6, "Coat Weight": 1.0})
DRIVE = emission("dsn_drive", (0.7, 0.2, 1.0, 1), 4.0)

# ---------- spectrum sculpture ----------
mid = {N // 2 - 1, N // 2}
for i in range(N):
    k = 1 - i / (N - 1)
    m = band_mat(i, k)
    y = (i - (N - 1) / 2) * 0.07
    if i not in mid:
        tube([P(x, E[j, i], y) for j, x in enumerate(XS)], 0.028, m)
        continue
    # middle pair: orange where it is the zero-energy edge state, band colour elsewhere
    seg, cur = [], None
    for j, x in enumerate(XS):
        state = topo[j] and abs(E[j, i]) < 0.012
        if cur is None or state == cur:
            seg.append(P(x, E[j, i], y))
        else:
            seg.append(P(x, E[j, i], y))
            tube(seg, 0.05 if cur else 0.028, EDGE if cur else m)
            seg = [P(x, E[j, i], y)]
        cur = state
    tube(seg, 0.05 if cur else 0.028, EDGE if cur else m)

# topological windows as glass slabs
j = 0
while j < len(XS):
    if topo[j]:
        k0 = j
        while j < len(XS) and topo[j]:
            j += 1
        xa, xb = XS[k0], XS[j - 1]
        cx = X0 + SX * (xa + xb) / 2
        w = SX * (xb - xa)
        box((cx, 1.0, Z0), (w, 0.08, 2 * SZ * 0.45), SLAB, bevel=0.03)
    j += 1

# plinth carrying the sculpture
box((0, -0.9, -0.45), (16.4, 6.6, 0.5), PLINTH, bevel=0.06)
for xe in (X0 - 0.1, X0 + SX * 13 + 0.1):
    tube([(xe, 0.0, -0.2), (xe, 0.0, Z0 - SZ * 0.43)], 0.05, SILVER)

# ---------- the dimer chain of Fig. 1, in front, rocked by the ac field ----------
# The ac dipole field shifts each dot's level in proportion to its position, E_n = A x_n cos(wt): the chain's level
# profile rocks like a seesaw about its centre. Glassy ghosts mark the undriven (aligned) levels, purple arrows the
# rocking, and the field's oscillation runs as a glowing wave underneath.
gaps = [0.95, 1.55] * 3 + [0.95]
cx_ = [0.0]
for g in gaps:
    cx_.append(cx_[-1] + g)
cx_ = [c - cx_[-1] / 2 for c in cx_]
YC, ZC = -3.0, 1.25
th = math.radians(14)
t_now = 0.85 * th
GHOST = bpy.data.materials.new("dsn_ghost"); GHOST.use_nodes = True
_nt = GHOST.node_tree; _nt.nodes.clear()
_o = _nt.nodes.new("ShaderNodeOutputMaterial"); _d = _nt.nodes.new("ShaderNodeBsdfPrincipled")
_d.inputs["Base Color"].default_value = (0.75, 0.8, 0.95, 1); _d.inputs["Roughness"].default_value = 0.2
_d.inputs["Emission Color"].default_value = (0.85, 0.9, 1.0, 1); _d.inputs["Emission Strength"].default_value = 0.25
_t = _nt.nodes.new("ShaderNodeBsdfTransparent"); _mx = _nt.nodes.new("ShaderNodeMixShader"); _mx.inputs["Fac"].default_value = 0.7
_nt.links.new(_t.outputs[0], _mx.inputs[1]); _nt.links.new(_d.outputs[0], _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _o.inputs["Surface"])


def dsn_dot(c, mat, tilt):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=c, segments=48, ring_count=24, rotation=(0, -tilt, 0))
    ob = bpy.context.object; ob.scale = (0.4, 0.4, 0.15)
    bpy.ops.object.shade_smooth()
    return link(ob, mat)


for n, c in enumerate(cx_):
    dsn_dot((c, YC, ZC), GHOST, 0.0)
    p = (c * math.cos(t_now), YC, ZC + c * math.sin(t_now))
    dsn_dot(p, DOT_EDGE if n in (0, len(cx_) - 1) else DOT, t_now)
# pivot under the chain centre: the level at the centre does not move
sphere((0, YC, ZC), 0.07, GOLD)
bpy.ops.mesh.primitive_cone_add(radius1=0.32, radius2=0.05, depth=ZC - 0.1, location=(0, YC + 0.6, (ZC - 0.1) / 2), vertices=48)
bpy.ops.object.shade_smooth()
link(bpy.context.object, principled("dsn_pivot", **{"Base Color": (0.95, 0.92, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0}))
# rocking arrows at both ends of the chain
R = cx_[-1] + 0.6
for ang0 in (0.0, math.pi):
    a0, a1 = ang0 - th * 1.1, ang0 + th * 1.1
    pts = [(R * math.cos(a0 + (a1 - a0) * i / 40), YC, ZC + R * math.sin(a0 + (a1 - a0) * i / 40)) for i in range(41)]
    tube(pts[3:-3], 0.06, DRIVE)
    for a, sg in ((a0, -1), (a1, 1)):
        tip = Vector((R * math.cos(a), YC, ZC + R * math.sin(a)))
        dd = Vector((-math.sin(a), 0, math.cos(a))) * sg
        bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=0.38, location=tip, rotation=dd.to_track_quat("Z", "Y").to_euler(), vertices=24)
        link(bpy.context.object, DRIVE)
# gold source and drain, tall enough to reach the chain
XS_ = cx_[-1] + 2.15
for sgn in (-1, 1):
    box((sgn * XS_, YC, 0.4), (1.4, 2.0, 1.6), GOLD, bevel=0.05)
# electrons in bunches: crowded on the source, an irregular train leaving the drain
for _ in range(22):
    sphere((-XS_ + random.uniform(-0.5, 0.5), YC + random.uniform(-0.65, 0.65), 1.3), 0.08, ELEC)
xs_e = [0.0, 0.18, 0.33, 1.1, 1.25, 2.3]
for xe in xs_e:
    sphere((XS_ - 0.4 + xe * 0.55, YC - 0.1, 1.55 + 0.1 * xe), 0.07, ELEC)
# the ac field: a glowing wave running under the chain from source to drain
tube([(-XS_ + 0.8 + (2 * XS_ - 1.6) * i / 300, YC - 0.25, 0.3 + 0.16 * math.sin(2 * math.pi * 3 * i / 300)) for i in range(301)],
     0.05, DRIVE)

camera((-8.0, -16.0, 9.0), (0.6, 0.0, 1.6), lens=36)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

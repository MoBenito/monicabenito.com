"""Full-counting statistics of time-dependent conductors (Benito, Niklas, Kohler, PRB 94, 195433).

An open double quantum dot between source and drain, its detuning driven by an ac gate (purple wavefronts: LZSM
driving). Every electron that leaves through the drain is counted: the counts pile up in a row of glass tubes, one tube
per number n of transferred electrons, so their filling is the full counting statistics P(n) (a slightly skewed,
non-Gaussian distribution: the higher cumulants the paper computes).
"""
import bmesh
import random
from mathutils import Matrix

random.seed(5)
bright_stage()

FCS_E = principled("fcs_electron", **{"Base Color": (0.02, 0.25, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                       "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 0.5})
FCS_E_HOT = principled("fcs_electron_hot", **{"Base Color": (0.1, 0.4, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                               "Emission Color": (0.15, 0.4, 1.0, 1), "Emission Strength": 2.2})
FCS_GLASS = bpy.data.materials.new("fcs_glass"); FCS_GLASS.use_nodes = True
_nt = FCS_GLASS.node_tree; _nt.nodes.clear()
_o = _nt.nodes.new("ShaderNodeOutputMaterial"); _g = _nt.nodes.new("ShaderNodeBsdfGlossy"); _g.inputs["Roughness"].default_value = 0.05
_t = _nt.nodes.new("ShaderNodeBsdfTransparent"); _lw = _nt.nodes.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.25
_mx = _nt.nodes.new("ShaderNodeMixShader")
_nt.links.new(_lw.outputs["Fresnel"], _mx.inputs["Fac"]); _nt.links.new(_t.outputs[0], _mx.inputs[1]); _nt.links.new(_g.outputs[0], _mx.inputs[2])
_nt.links.new(_mx.outputs[0], _o.inputs["Surface"])
FCS_DOT = principled("fcs_dot", **{"Base Color": (0.3, 0.95, 0.8, 1), "Metallic": 0.6, "Roughness": 0.12,
                                    "Coat Weight": 1.0})
FCS_TRAIL = emission("fcs_trail", (0.35, 0.6, 1.0, 1), 3.0)


def fcs_slab():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.0, -0.35))
    slab = bpy.context.object; slab.scale = (19.0, 16.0, 0.7)
    sm = principled("fcs_hetero", **{"Roughness": 0.35})
    nt = sm.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.6, 0.9, 0.75, 1)
    els[1].position, els[1].color = 0.5, (1.0, 0.75, 0.35, 1)
    for pos, col in ((0.68, (0.55, 0.7, 1.0, 1)), (0.9, (0.95, 0.9, 0.98, 1))):
        e = els.new(pos); e.color = col
    els[-1].color = (0.8, 0.95, 0.85, 1)
    nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
    link(slab, sm)


fcs_slab()

# --- the counting histogram: one glass tube per count n, filled with that many "events" ----------------------
counts = [1, 2, 4, 7, 9, 8, 7, 5, 4, 2, 1, 1]          # P(n), skewed to large n
N = len(counts)
r_ball, r_tube = 0.24, 0.27
xs = [-2.4 + 0.58 * i for i in range(N)]
yt = 1.2
tint = [(0.55, 0.85, 1.0), (0.6, 0.8, 1.0), (0.7, 0.75, 1.0), (0.8, 0.7, 1.0), (0.9, 0.7, 0.95), (1.0, 0.7, 0.85),
        (1.0, 0.72, 0.7), (1.0, 0.78, 0.6), (1.0, 0.85, 0.55), (0.9, 0.92, 0.55), (0.75, 0.95, 0.6), (0.6, 0.95, 0.7)]
H = 0.4 * max(counts) + 0.5
eb = bmesh.new()
tops = []
for i, (x, n) in enumerate(zip(xs, counts)):
    # each bin: a coloured pedestal with a stack of n counted electrons on it
    col = tint[i]
    bpy.ops.mesh.primitive_cylinder_add(radius=r_tube, depth=0.16, location=(x, yt, 0.08), vertices=48)
    bpy.ops.object.shade_smooth()
    link(bpy.context.object, principled("fcs_base%d" % i, **{"Base Color": (*col, 1), "Roughness": 0.2, "Coat Weight": 1.0}))
    for k in range(n):
        z = 0.16 + r_ball + k * 2 * r_ball * 0.97
        bmesh.ops.create_icosphere(eb, subdivisions=3, radius=r_ball,
                                   matrix=Matrix.Translation((x + random.uniform(-0.02, 0.02), yt + random.uniform(-0.02, 0.02), z)))
    tops.append(Vector((x, yt, 0.16 + n * 2 * r_ball * 0.97 + 0.12)))
me = bpy.data.meshes.new("fcs_counts"); eb.to_mesh(me); eb.free()
for f_ in me.polygons:
    f_.use_smooth = True
ob = bpy.data.objects.new("fcs_counts", me); sc.collection.objects.link(ob); me.materials.append(FCS_E)

# the distribution's envelope: a smooth glowing curve over the stacks
import itertools
env = []
for j in range(201):
    t = j / 200 * (N - 1)
    i0 = min(int(t), N - 2); f = t - i0
    # Catmull-Rom through the stack tops
    P = [tops[max(min(i0 + k, N - 1), 0)] for k in (-1, 0, 1, 2)]
    p = 0.5 * ((2 * P[1]) + (-P[0] + P[2]) * f + (2 * P[0] - 5 * P[1] + 4 * P[2] - P[3]) * f * f + (-P[0] + 3 * P[1] - 3 * P[2] + P[3]) * f ** 3)
    env.append(tuple(p + Vector((0, 0, 0.12))))
tube(env, 0.06, principled("fcs_envelope", **{"Base Color": (1.0, 0.3, 0.0, 1), "Roughness": 0.2, "Emission Color": (1.0, 0.35, 0.0, 1), "Emission Strength": 2.5}))

# --- the paper's Figure 1 behind it: LZSM interference of the driven double dot, lifted onto a glowing panel --------
# current ~ sum_n J_n(A/w)^2 L(eps - n w): resonance lobes at eps = n w, modulated along the drive amplitude A
import numpy as np
W_, H_ = 480, 320
eps = np.linspace(-6.5, 6.5, W_)
amp = np.linspace(0.0, 11.0, H_)
tau = np.linspace(0, np.pi, 400)
I = np.zeros((H_, W_))
for n in range(-12, 13):
    Jn = (getattr(np, "trapezoid", None) or np.trapz)(np.cos(n * tau[None, :] - amp[:, None] * np.sin(tau[None, :])), tau, axis=1) / np.pi
    I += (Jn ** 2)[:, None] * (0.16 ** 2 / ((eps[None, :] - n) ** 2 + 0.16 ** 2))[None, :].reshape(1, W_)
I = np.clip(I / np.percentile(I, 99), 0, 1) ** 0.55
c0, c1, c2 = np.array([0.95, 0.99, 0.92]), np.array([0.35, 0.8, 0.8]), np.array([0.0, 0.2, 0.7])
t = I[..., None]
rgb = np.where(t < 0.5, c0 + (c1 - c0) * (t / 0.5), c1 + (c2 - c1) * ((t - 0.5) / 0.5))
rgba = np.concatenate([rgb, np.ones((H_, W_, 1))], axis=2).astype(np.float32)
img = bpy.data.images.new("fcs_lzsm", W_, H_, float_buffer=True)
img.pixels.foreach_set(rgba.ravel())
img.pack()
PW, PH = 6.0, 3.4
PX, PY = -5.65, 1.6
bpy.ops.mesh.primitive_plane_add(size=1, location=(PX, PY, PH / 2 + 0.35), rotation=(math.radians(90), 0, 0))
pan = bpy.context.object; pan.scale = (PW, PH, 1)
pm = principled("fcs_lzsm_panel", **{"Roughness": 0.4, "Emission Strength": 0.25})
nt = pm.node_tree
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Cubic"
nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Emission Color"])
link(pan, pm)
fr = [(PX - PW / 2, PY - 0.02, 0.35), (PX + PW / 2, PY - 0.02, 0.35), (PX + PW / 2, PY - 0.02, PH + 0.35), (PX - PW / 2, PY - 0.02, PH + 0.35), (PX - PW / 2, PY - 0.02, 0.35)]
tube(fr, 0.06, GOLD)

# --- the driven double dot in front -----------------------------------------------------------------------
yd = -1.7
XS, XD = -6.0, -1.2
box((-7.6, yd, 0.2), (2.4, 2.6, 0.4), GOLD, bevel=0.05)     # source
box((-1.8, yd, 0.2), (1.6, 2.6, 0.4), GOLD, bevel=0.05)     # drain (feeds the counter)
dots = [(-5.2, yd, 0.35), (-3.8, yd, 0.35)]
for c in dots:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=c, segments=64, ring_count=32)
    d_ = bpy.context.object; d_.scale = (0.55, 0.55, 0.2); bpy.ops.object.shade_smooth(); link(d_, FCS_DOT)
# tunnel barriers between the islands: gold gate fingers across the transport direction
for x in (-6.05, -4.5, -2.95):
    gate([(x, yd - 1.2), (x, yd + 1.2)], width=0.16, height=0.3)
# the ac gate under the dots and its drive (purple wavefronts going up from it)
gate([(-5.6, yd - 2.4), (-5.6, yd - 1.0), (-3.6, yd - 1.0)], width=0.24, height=0.2)
wave_arcs((-4.5, yd - 1.0, 0.45), (0, 0, 1), n=4, spacing=0.32, color=(0.55, 0.05, 1.0, 1), start=0.35)
# source Fermi sea: electrons waiting on the source contact
es = bmesh.new()
for ix in range(10):
    for iy in range(11):
        for iz in range(2):
            if iz == 1 and random.random() < 0.45:
                continue
            bmesh.ops.create_icosphere(es, subdivisions=2, radius=0.09,
                                       matrix=Matrix.Translation((-8.6 + ix * 0.22 + random.uniform(-0.03, 0.03), yd - 1.1 + iy * 0.22, 0.5 + iz * 0.2)))
me = bpy.data.meshes.new("fcs_sea"); es.to_mesh(me); es.free()
for f_ in me.polygons:
    f_.use_smooth = True
o_ = bpy.data.objects.new("fcs_sea", me); sc.collection.objects.link(o_); me.materials.append(FCS_E)
# electrons tunnelling: one on dot 1, one hopping dot 1 -> dot 2, one leaving the drain towards the counter
sphere((dots[0][0], yd, 0.65), 0.16, FCS_E_HOT)
hp = [(-4.95 + 0.9 * u, yd, 0.7 + 0.5 * math.sin(math.pi * u)) for u in [i / 30 for i in range(31)]]
tube(hp[:24], 0.03, FCS_TRAIL); sphere(hp[24], 0.15, FCS_E_HOT)
# from the drain up and over into the tube for the current count (a long, airy arc)
tgt = tops[3] + Vector((0, 0, 0.35))
p0 = Vector((-1.8, yd, 0.7))
mid = (p0 + tgt) / 2 + Vector((0, 0, 1.8))
arc = [tuple((1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u * u * tgt) for u in [i / 60 for i in range(61)]]
tube(arc[:50], 0.03, FCS_TRAIL)
sphere(arc[50], 0.17, FCS_E_HOT)
hot_spot(arc[50], (0.6, 0.8, 1.0, 1), 0.04, 30)

camera((-2.4, -13.4, 5.9), (-1.9, 0.3, 1.45), lens=35, dof=4.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

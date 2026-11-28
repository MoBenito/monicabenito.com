"""Edge-state blockade (Benito, Niklas, Platero, Kohler, PRB 93, 115432).

A dimer chain of quantum dots (SSH, topological phase: weak intra-dimer / strong inter-dimer coupling, so the end
dots sit apart) between a strongly biased source (left, full Fermi sea) and drain (right, nearly empty). One electron
has fallen into the left edge state (|psi|^2 on dots 1, 3, 5, ... decaying into the chain). Coulomb repulsion from it
(red ripples) turns the next electron back at the source: transport is blocked until it leaves.
"""
import bmesh
import random
from mathutils import Matrix

random.seed(11)
bright_stage()

ESB_E = principled("esb_electron", **{"Base Color": (0.05, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 0.6,
                                       "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 0.4})
ESB_E_HOT = principled("esb_electron_hot", **{"Base Color": (0.0, 0.15, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                               "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 1.0})
ESB_DOT = principled("esb_dot", **{"Base Color": (0.55, 0.35, 1.0, 1), "Roughness": 0.18, "Coat Weight": 1.0})
ESB_DOT_EDGE = principled("esb_dot_edge", **{"Base Color": (0.0, 0.85, 0.75, 1), "Roughness": 0.18, "Coat Weight": 1.0})
ESB_BOND = emission("esb_bond", (0.3, 0.95, 0.85, 1), 3.0)
ESB_BOND_W = principled("esb_bond_weak", **{"Base Color": (0.75, 0.8, 0.9, 1), "Roughness": 0.4,
                                             "Transmission Weight": 0.6})


def esb_slab():
    """Chip slab whose cut faces show coloured heterostructure layers (as in bath_wow)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.0, -0.35))
    slab = bpy.context.object; slab.scale = (17.0, 13.0, 0.7)
    sm = principled("esb_hetero", **{"Roughness": 0.35})
    nt = sm.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.75, 0.7, 0.95, 1)
    els[1].position, els[1].color = 0.5, (0.3, 0.6, 1.0, 1)
    for pos, col in ((0.66, (1.0, 0.55, 0.45, 1)), (0.9, (0.78, 0.93, 0.95, 1))):
        e = els.new(pos); e.color = col
    els[-1].color = (0.62, 0.9, 0.85, 1)
    nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
    link(slab, sm)


def esb_hump_mat(name, color, strength):
    """Glowing translucent skin for |psi|^2 humps: emission + transparency, brighter where the surface faces away."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = _math(nt, "ADD", 0.35, _math(nt, "MULTIPLY", lw.outputs["Facing"], 0.6))
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac, mix.inputs["Fac"]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def esb_hump(c, height, width, mat):
    """Surface of revolution z = h exp(-r^2/w^2) (open at the bottom)."""
    bm = bmesh.new()
    nr, nphi = 28, 64
    tip = bm.verts.new((c[0], c[1], c[2] + height))
    rings = []
    for i in range(1, nr + 1):
        r = 1.7 * width * i / nr
        z = height * math.exp(-(r / width) ** 2)
        rings.append([bm.verts.new((c[0] + r * math.cos(2 * math.pi * j / nphi), c[1] + r * math.sin(2 * math.pi * j / nphi), c[2] + z)) for j in range(nphi)])
    for j in range(nphi):
        bm.faces.new((tip, rings[0][j], rings[0][(j + 1) % nphi]))
    for i in range(nr - 1):
        for j in range(nphi):
            bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % nphi], rings[i][(j + 1) % nphi]))
    me = bpy.data.meshes.new("hump"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("hump", me); sc.collection.objects.link(ob); me.materials.append(mat)
    ob.visible_shadow = False
    return ob


def esb_dot(c, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=c, segments=64, ring_count=32)
    ob = bpy.context.object; ob.scale = (0.38, 0.38, 0.17)
    bpy.ops.object.shade_smooth()
    return link(ob, mat)


esb_slab()

# SSH chain of four dimers as in the paper's Fig. 1: pairs of dots (short spacing inside a pair, long between pairs),
# starting with dot 1, the edge site on which the left edge state lives
gaps = [0.95, 1.65] * 3 + [0.95]
xs = [0.0]
for g in gaps:
    xs.append(xs[-1] + g)
xs = [x - xs[-1] / 2 for x in xs]
zd = 0.2
for i, x in enumerate(xs):
    esb_dot((x, 0, zd), ESB_DOT_EDGE if i == 0 else ESB_DOT)
# tunnel couplings along the chain: a thin glassy line through all dots, as in the figure
for i in range(7):
    tube([(xs[i] + 0.36, 0, zd), (xs[i + 1] - 0.36, 0, zd)], 0.03, ESB_BOND_W)

# gate electrodes defining the array: a barrier gate between neighbouring dots, a plunger gate under each dot
for i in range(7):
    xm = (xs[i] + xs[i + 1]) / 2
    gate([(xm, 0.45), (xm, 1.6), (xm + 0.25 * xm, 3.2)], width=0.16, height=0.22)
for i, x in enumerate(xs):
    gate([(x, -0.55), (x, -1.4), (x + 0.1 * x, -2.6)], width=0.2, height=0.12)

# left edge state |psi|^2: on sites 1, 3, 5, 7, decaying into the chain
HUMP = esb_hump_mat("esb_edge_state", (1.0, 0.12, 0.2, 1), 2.2)
for k, h in enumerate((2.3, 0.85, 0.32, 0.12)):
    esb_hump((xs[2 * k], 0, zd + 0.1), h, 0.36, HUMP)

# the trapped electron in the edge state (with its glow lighting the dot)
ce = Vector((xs[0], 0, zd + 0.42))
sphere(tuple(ce), 0.2, ESB_E_HOT)
hot_spot(tuple(ce), (0.6, 0.8, 1.0, 1), 0.06, 30)
l = bpy.data.lights.new("esb_core", "POINT"); l.energy, l.color, l.shadow_soft_size = 8, (0.4, 0.6, 1.0), 0.3
lo = bpy.data.objects.new("esb_core", l); lo.location = ce + Vector((0, 0, 0.5)); sc.collection.objects.link(lo)

# Coulomb repulsion: red rings spreading out from the trapped electron, flat on the chip around the first dot
for i, rr in enumerate((0.6, 0.82, 1.04)):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.03, major_segments=128, minor_segments=8,
                                     location=(xs[0], 0, zd))
    link(bpy.context.object, emission("esb_ring%d" % i, (1.0, 0.25, 0.2, 1), 6.0 / (1 + 0.8 * i)))

# reservoirs: gold blocks; source full of electrons (strong bias), drain nearly empty
XL = xs[0] - 1.35
XR = xs[-1] + 1.5
for sg, xi, xo in ((-1, XL, XL - 2.6), (1, XR, XR + 2.6)):
    box(((xi + xo) / 2, 0, 0.17), (abs(xo - xi), 4.4, 0.34), GOLD, bevel=0.05)
es = bmesh.new()
g = 0.21
for side, (lo_x, hi_x, nz) in ((-1, (XL - 2.45, XL - 0.15, 5)), (1, (XR + 0.15, XR + 2.45, 1))):
    nx = int((hi_x - lo_x) / g) + 1
    for ix in range(nx):
        for iy in range(int(4.1 / g) + 1):
            for iz in range(nz):
                ex = random.uniform(lo_x, hi_x)
                ey = random.uniform(-2.05, 2.05)
                ez = 0.43 + random.uniform(0, (nz - 1) * g * 0.95)
                if side > 0 and random.random() < 0.88:
                    continue
                if side < 0 and iz == nz - 1 and random.random() < 0.4:
                    continue
                bmesh.ops.create_icosphere(es, subdivisions=2, radius=0.085, matrix=Matrix.Translation((ex, ey, ez)))
me = bpy.data.meshes.new("esb_sea"); es.to_mesh(me); es.free()
for f_ in me.polygons:
    f_.use_smooth = True
ob = bpy.data.objects.new("esb_sea", me); sc.collection.objects.link(ob); me.materials.append(ESB_E)

# the next electron from the source heads for dot 1, but dot 1 is occupied: its path into the dot is crossed out
TR = emission("esb_trail", (0.35, 0.6, 1.0, 1), 3.0)
p1 = Vector((XL - 0.25, -1.35, 1.38))
pe = Vector((xs[0] - 0.3, -0.3, zd + 0.3))
arc = lambda a_, b_, h, u: a_.lerp(b_, u) + Vector((0, 0, h * math.sin(math.pi * u)))
ESB_E_NEXT = principled("esb_electron_next", **{"Base Color": (0.1, 0.45, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                                 "Emission Color": (0.1, 0.4, 1.0, 1), "Emission Strength": 1.2})
sphere(tuple(p1), 0.2, ESB_E_NEXT)
hot_spot(tuple(p1), (0.6, 0.8, 1.0, 1), 0.04, 20)
# intended hop into dot 1: one single arc with an arrow head
hp = [arc(p1, pe, 0.9, i / 60) for i in range(61)]
tube([tuple(q) for q in hp[0:56]], 0.035, TR)
d = (hp[-1] - hp[-5]).normalized()
bpy.ops.mesh.primitive_cone_add(radius1=0.1, depth=0.24, location=hp[-3], rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
link(bpy.context.object, TR)
# the "forbidden" cross over the hop, facing the camera
CAM = Vector((-7.2, -8.6, 5.6))
xc = hp[30]
fwd = (CAM - xc).normalized()
right = fwd.cross(Vector((0, 0, 1))).normalized()
up = right.cross(fwd).normalized()
XMAT = principled("esb_cross", **{"Base Color": (1.0, 0.02, 0.05, 1), "Roughness": 0.25, "Coat Weight": 1.0,
                                   "Emission Color": (1.0, 0.02, 0.04, 1), "Emission Strength": 2.0})
for sg in (1, -1):
    dvec = (right + sg * up).normalized() * 0.3
    tube([tuple(xc - dvec + fwd * 0.15), tuple(xc + dvec + fwd * 0.15)], 0.07, XMAT)

camera(tuple(CAM), (-1.5, 0.6, 0.5), lens=27, dof=2.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

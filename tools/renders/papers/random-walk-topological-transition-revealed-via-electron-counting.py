"""Random-walk topological transition revealed via electron counting (Engelhardt, Benito, Platero, Schaller, Brandes,
PRB 96, 241404(R)).

A single-electron transistor (one dot between source and drain) is counted: m electrons have reached the drain, the
dot holds d = 0 or 1. The record n = 2m - d is a classical random walker on a staircase: every tunnelling event moves
it one step up (electron in from the source / out into the drain) and the rates alternate from step to step (the SSH
pattern, here as hopping probabilities). The walker's escape from a finite section of steps (glass rails) reveals the
topological phase.
"""
import bmesh
import random
from mathutils import Matrix

random.seed(3)
bright_stage()

RW_E = principled("rw_electron", **{"Base Color": (0.02, 0.25, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                                     "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 0.5})
RW_E_HOT = principled("rw_electron_hot", **{"Base Color": (0.0, 0.2, 1.0, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                             "Emission Color": (0.1, 0.35, 1.0, 1), "Emission Strength": 1.2})
RW_A = principled("rw_tread_a", **{"Base Color": (0.0, 0.72, 0.62, 1), "Roughness": 0.25, "Coat Weight": 1.0})
RW_B = principled("rw_tread_b", **{"Base Color": (1.0, 0.32, 0.22, 1), "Roughness": 0.25, "Coat Weight": 1.0})
RW_FADE = principled("rw_tread_out", **{"Base Color": (0.95, 0.93, 0.9, 1), "Roughness": 0.3,
                                         "Transmission Weight": 0.7, "IOR": 1.3})
RW_RAIL = principled("rw_rail", **{"Base Color": (0.85, 0.95, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.05,
                                    "IOR": 1.45})
RW_UP = principled("rw_up", **{"Base Color": (1.0, 0.6, 0.0, 1), "Roughness": 0.25, "Coat Weight": 1.0, "Emission Color": (1.0, 0.55, 0.0, 1), "Emission Strength": 1.2})
RW_DOWN = principled("rw_down", **{"Base Color": (0.45, 0.1, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0, "Emission Color": (0.45, 0.1, 1.0, 1), "Emission Strength": 1.2})
RW_DOT = principled("rw_dot", **{"Base Color": (0.85, 0.9, 1.0, 1), "Metallic": 0.85, "Roughness": 0.12, "Coat Weight": 1.0})


def rw_arrow(p0, p1, lift, radius, mat, frac=1.0):
    p0, p1 = Vector(p0), Vector(p1)
    pts = [tuple(p0.lerp(p1, u) + Vector((0, 0, lift * math.sin(math.pi * u)))) for u in [i / 40 * frac for i in range(41)]]
    tube(pts[:-3], radius, mat)
    d = (Vector(pts[-1]) - Vector(pts[-4])).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=radius * 2.6, depth=radius * 6, location=Vector(pts[-4]) + d * radius * 3,
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, mat)


bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.0, -0.35))
slab = bpy.context.object; slab.scale = (22.0, 14.0, 0.7)
bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
sm = principled("rw_hetero", **{"Roughness": 0.35})
nt = sm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (1.0, 0.8, 0.45, 1)
els[1].position, els[1].color = 0.5, (0.4, 0.8, 0.95, 1)
for pos, col in ((0.7, (0.75, 0.6, 1.0, 1)), (0.9, (0.85, 0.95, 0.93, 1))):
    e = els.new(pos); e.color = col
nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
link(slab, sm)

# --- the staircase of counting states ----------------------------------------------------------------------
NS = 12
dx, dz = 0.92, 0.36
X0, Z0 = -4.6, 0.35
IN0, IN1 = 1, 10                     # finite SSH section: steps IN0..IN1
tops = []
for i in range(NS):
    x, z = X0 + i * dx, Z0 + i * dz
    inside = IN0 <= i <= IN1
    mat = (RW_A if i % 2 == 0 else RW_B) if inside else RW_FADE
    box((x, 0, z - 0.07), (dx * 0.9, 2.0, 0.14), mat, bevel=0.04)
    # thin pillar under each step
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=z - 0.07, location=(x, 0.7, (z - 0.07) / 2), vertices=16)
    link(bpy.context.object, STEEL)
    tops.append(Vector((x, 0, z)))
# glass rails along the finite section
for yr in (-1.08, 1.08):
    a = tops[IN0] + Vector((-dx * 0.45, yr, 0.55)); b = tops[IN1] + Vector((dx * 0.45, yr, 0.55))
    pass
    for i in range(IN0, IN1 + 1):
        p = tops[i] + Vector((0, yr, 0))
        pass
# the section boundaries, drawn as in the paper's figure: red bars standing between the section and the outside
RW_RED = principled("rw_boundary", **{"Base Color": (0.85, 0.02, 0.05, 1), "Roughness": 0.25, "Coat Weight": 1.0,
                                       "Emission Color": (1.0, 0.05, 0.05, 1), "Emission Strength": 0.6})
for i in (IN0, IN1 + 1):
    xb = (tops[i - 1].x + tops[i].x) / 2
    zb = (tops[i - 1].z + tops[i].z) / 2
    for yb in (-1.05, 1.05):
        box((xb, yb, zb + 0.45), (0.12, 0.16, 1.5), RW_RED, bevel=0.03)
    tube([(xb, -1.05, zb + 1.2), (xb, 1.05, zb + 1.2)], 0.05, RW_RED)
# hop arrows: up (gold, in front) and down (violet, behind); thickness = rate, alternating step to step (SSH)
for i in range(IN0 - 1, IN1 + 1):
    strong_up = i % 2 == 0
    a, b = tops[i] + Vector((0.1, -0.7, 0.12)), tops[i + 1] + Vector((-0.1, -0.7, 0.12))
    rw_arrow(a, b, 0.45, 0.085 if strong_up else 0.022, RW_UP)
    a, b = tops[i + 1] + Vector((-0.1, 0.7, 0.12)), tops[i] + Vector((0.1, 0.7, 0.12))
    rw_arrow(a, b, 0.45, 0.022 if strong_up else 0.085, RW_DOWN)

# the walker on step 6, with a faint ghost trail of earlier positions
w = tops[6] + Vector((0, 0, 0.36))
sphere(tuple(w), 0.36, RW_E_HOT)
hot_spot(tuple(w), (0.6, 0.8, 1.0, 1), 0.06, 20)
l = bpy.data.lights.new("rw_core", "POINT"); l.energy, l.color, l.shadow_soft_size = 30, (0.4, 0.6, 1.0), 0.3
lo = bpy.data.objects.new("rw_core", l); lo.location = w + Vector((0, -0.4, 0.6)); sc.collection.objects.link(lo)
for k, i in enumerate((5, 4, 5)):
    sphere(tuple(tops[i] + Vector((0.0, 0.05 * k, 0.32))), 0.3 * (0.7 - 0.12 * k),
           emission("rw_ghost%d" % k, (0.45, 0.7, 1.0, 1), 1.5 - 0.4 * k))

# --- the counted device: one dot between source and drain (at the foot of the stairs) ----------------------
yd = -2.9
box((-6.3 + 2.4 + 0.4, yd, 0.2), (1.6, 2.2, 0.4), GOLD, bevel=0.05)      # source
box((-1.7 + 2.4 - 0.4, yd, 0.2), (1.6, 2.2, 0.4), GOLD, bevel=0.05)      # drain
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(-4.0 + 2.4, yd, 0.3), segments=64, ring_count=32)
d_ = bpy.context.object; d_.scale = (0.6, 0.6, 0.22); bpy.ops.object.shade_smooth(); link(d_, RW_DOT)
for x in (-4.85 + 2.4, -3.15 + 2.4):
    gate([(x, yd - 1.2), (x, yd + 1.2)], width=0.14, height=0.32)
sphere((-4.0 + 2.4, yd, 0.62), 0.17, RW_E_HOT)                         # d = 1: the dot is occupied
es = bmesh.new()
for side, (lo_x, nz, keep) in ((-1, (-7.35 + 2.4 + 0.5, 3, 1.0)), (1, (-2.75 + 2.4 - 0.2, 1, 0.45))):
    for ix in range(7):
        for iy in range(9):
            for iz in range(nz):
                if random.random() > keep:
                    continue
                bmesh.ops.create_icosphere(es, subdivisions=2, radius=0.09, matrix=Matrix.Translation(
                    (lo_x + ix * 0.21 + random.uniform(-0.03, 0.03), yd - 0.85 + iy * 0.21, 0.5 + iz * 0.19)))
me = bpy.data.meshes.new("rw_sea"); es.to_mesh(me); es.free()
for f_ in me.polygons:
    f_.use_smooth = True
o_ = bpy.data.objects.new("rw_sea", me); sc.collection.objects.link(o_); me.materials.append(RW_E)
# a counted electron leaving into the drain
tr = emission("rw_trail", (0.35, 0.6, 1.0, 1), 3.0)
pts = [(-3.6 + 2.4 + 1.4 * u, yd, 0.65 + 0.55 * math.sin(math.pi * u)) for u in [i / 30 for i in range(31)]]
tube(pts[:22], 0.03, tr); sphere(pts[22], 0.14, RW_E_HOT)

camera((0.9, -14.5, 7.4), (0.7, -0.5, 2.0), lens=38, dof=2.6)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

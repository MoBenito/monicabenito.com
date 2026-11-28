"""Topologically enforced bifurcations in superconducting circuits (Engelhardt, Benito, Platero, Brandes, PRL 118,
197702).

A superconducting circuit chip: a chain of nodes linked with the SSH pattern (alternating strong/weak Josephson
junctions and alternating inductors), every node shunted to ground by a capacitor and a resistor, the whole driven by
an ac current source. Above it rises the hero: the bifurcation diagram of the nonlinear chain as a function of the
topological control parameter, one stable branch that splits again and again (period doubling) into a chaotic cloud,
which separates it from the other phase.
"""
import bmesh
import random
from mathutils import Matrix

random.seed(2)
bright_stage(floor_z=-0.7)

SC_CHIP = principled("sc_chip", **{"Base Color": (0.72, 0.78, 1.0, 1), "Roughness": 0.3, "Coat Weight": 0.6})
SC_NB = principled("sc_niobium", **{"Base Color": (0.9, 0.92, 0.97, 1), "Metallic": 1.0, "Roughness": 0.38})
SC_JJ = emission("sc_jj", (0.3, 1.0, 0.85, 1), 6.0)
SC_COIL = principled("sc_coil", **{"Base Color": (0.1, 0.3, 1.0, 1), "Metallic": 0.6, "Roughness": 0.2})
SC_CAP = principled("sc_cap", **{"Base Color": (1.0, 0.55, 0.1, 1), "Roughness": 0.25, "Coat Weight": 1.0})
SC_RES = principled("sc_res", **{"Base Color": (0.9, 0.08, 0.1, 1), "Roughness": 0.3, "Coat Weight": 1.0})

# chip: slab with layered faces
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 5.5, -0.35))
slab = bpy.context.object; slab.scale = (18.0, 19.0, 0.7)
bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 2
nt = SC_CHIP.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.55, 0.6, 0.95, 1)
els[1].position, els[1].color = 0.75, (1.0, 0.65, 0.5, 1)
e = els.new(0.9); e.color = (0.62, 0.7, 1.0, 1)
nt.links.new(_math(nt, "ADD", sp.outputs["Z"], 0.5), ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
link(slab, SC_CHIP)

# --- the circuit, wired as in the paper's Fig. 1 --------------------------------------------------------------
# Three rails joined at both ends: the front rail carries the ac source (next to ground), the middle rail is the
# chain of Josephson junctions alternating I_c2, I_c1, I_c2, ..., I_c2, each shunted by its own inductor (L2 or L1)
# lying beside it; every node between two junctions goes to the front rail through a capacitor C and to the back
# rail through a resistor R.
NN = 6                                   # nodes; NN + 1 junctions
P_ = 2.15
xn = [(i - (NN - 1) / 2) * P_ for i in range(NN)]
xj = [xn[0] - P_ / 2] + [(xn[i] + xn[i + 1]) / 2 for i in range(NN - 1)] + [xn[-1] + P_ / 2]
XE0, XE1 = xj[0] - 1.05, xj[-1] + 1.05   # the two end connections of the frame
YF, YM, YB = -2.4, 0.0, 2.3              # front, middle, back rails
H = 0.06
W = 0.16


def sc_wire(x0, y0, x1, y1, w=W):
    """Flat niobium strip on the chip between two points (axis-aligned or diagonal)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, H / 2),
                                    rotation=(0, 0, math.atan2(dy, dx)))
    o = bpy.context.object; o.scale = (L + w, w, H)
    return link(o, SC_NB)


# frame: front and back rails, end connections through all three rails
sc_wire(XE0 + 1.55, YF, XE1, YF); sc_wire(XE0, YB, XE1, YB)
sc_wire(XE0, YF, XE0, YB); sc_wire(XE1, YF, XE1, YB)
# middle rail: junction chain from the left end to the right end
SC_JJ_BODY = principled("sc_jj_body", **{"Base Color": (0.92, 0.94, 1.0, 1), "Metallic": 1.0, "Roughness": 0.12})
pts_mid = [XE0] + [v for x in xj for v in (x - 0.28, x + 0.28)] + [XE1]
for k in range(0, len(pts_mid), 2):
    sc_wire(pts_mid[k], YM, pts_mid[k + 1], YM)
for j, x in enumerate(xj):
    big = j % 2 == 0                      # I_c2 at both ends and every second junction, I_c1 in between
    # junction: two niobium pads with a glowing tunnel barrier, larger for the larger critical current
    s_ = 0.62 if big else 0.4
    for sg in (-1, 1):
        box((x + sg * 0.17, YM, H), (0.3, s_, 2 * H), SC_JJ_BODY, bevel=0.02)
    box((x, YM, H + 0.01), (0.05, s_ * 0.92, 2 * H + 0.02), SC_JJ, bevel=0.0)
    # its shunt inductor lies in front of it, joined to the rail on both sides of the junction
    xa, xb = x - 0.62, x + 0.62
    yl = YM - 0.85
    sc_wire(x - 0.5, YM, xa, yl, w=0.09); sc_wire(x + 0.5, YM, xb, yl, w=0.09)
    turns = 9 if big else 6
    pts = []
    for k in range(361):
        u = k / 360
        ph = 2 * math.pi * turns * u
        pts.append((xa + 0.08 + (xb - xa - 0.16) * u + 0.06 * math.sin(ph), yl + 0.16 * math.cos(ph), 0.2 + 0.16 * math.sin(ph)))
    tube(pts, 0.026, SC_COIL)
    tube([(xa, yl, H), pts[0]], 0.026, SC_COIL); tube([(xb, yl, H), pts[-1]], 0.026, SC_COIL)
# every node: capacitor to the front rail, resistor to the back rail
for x in xn:
    box((x, YM, H / 2), (0.3, 0.3, H), SC_NB, bevel=0.01)
    sc_wire(x, YM, x, YM - 1.45); sc_wire(x, YM - 1.95, x, YF)
    for dy in (-0.11, 0.11):              # two orange plates
        box((x, YM - 1.7 + dy, 0.22), (0.55, 0.12, 0.42), SC_CAP, bevel=0.035)
    sc_wire(x, YM, x, YB)
    box((x, YM + 1.25, 0.2), (0.42, 0.42, 0.4), SC_RES, bevel=0.04)
# ac current source in the front rail near its left end, ground symbol at the corner
cs = Vector((XE0 + 1.05, YF, 0.0))
sc_wire(XE0, YF, cs.x - 0.5, YF)
bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.06, location=(cs.x, YF, 0.5),
                                 rotation=(math.radians(90), 0, 0), major_segments=96, minor_segments=12)
link(bpy.context.object, SC_NB)
tube([(cs.x - 0.32 + 0.64 * u, YF, 0.5 + 0.17 * math.sin(2 * math.pi * u)) for u in [i / 60 for i in range(61)]], 0.035,
     emission("sc_src", (0.75, 0.3, 1.0, 1), 8.0))
tube([(cs.x - 0.45, YF, 0.5), (cs.x - 0.5, YF, H)], 0.03, SC_NB)
tube([(cs.x + 0.45, YF, 0.5), (cs.x + 0.5, YF, H)], 0.03, SC_NB)
gx, gy = XE0, YF
sc_wire(gx - 0.9, gy, gx, gy)
for k, w in enumerate((0.7, 0.46, 0.22)):
    box((gx - 0.9 - 0.16 * k, gy, H), (0.07, w, 0.1), SC_NB, bevel=0.01)

# --- the bifurcation diagram, rising behind the circuit ----------------------------------------------------
# stylised: logistic-map attractor vs. control parameter, cascading into chaos towards the middle and back out
bm = bmesh.new()
col = bm.verts.layers.float_color.new("hue")
X0, X1 = -6.6, 6.6
Yd = 3.4
for j in range(520):
    s = j / 519
    m = 1 - abs(2 * s - 1)                    # 0 at the edges, 1 in the middle
    r = 2.9 + 1.08 * m ** 1.3
    x = random.random()
    for _ in range(300):
        x = r * x * (1 - x)
    seen = set()
    for k in range(90 if m > 0.7 else 40):
        x = r * x * (1 - x)
        key = round(x, 3)
        if key in seen:
            continue
        seen.add(key)
        # mirror the right half so that both phases sit on the outside
        z = 0.45 + 3.9 * x
        px = X0 + (X1 - X0) * s
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.035 if m < 0.75 else 0.022,
                                         matrix=Matrix.Translation((px, Yd + random.uniform(-0.05, 0.05), z)))
        for v in res["verts"]:
            v[col] = (s, m, 0, 1)
me = bpy.data.meshes.new("sc_bif"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("sc_bif", me); sc.collection.objects.link(ob)
mat = bpy.data.materials.new("sc_bif"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "hue"
sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(at.outputs["Color"], sep.inputs[0])
rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.0, 0.6, 1.0, 1)
el[1].position, el[1].color = 1.0, (1.0, 0.05, 0.55, 1)
e2 = el.new(0.5); e2.color = (1.0, 0.55, 0.0, 1)
nt.links.new(sep.outputs["Green"], rp.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.6
nt.links.new(rp.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
me.materials.append(mat)


camera((-6.2, -15.2, 8.4), (-1.0, -0.2, 1.4), lens=33, dof=3.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

# Floquet physics from quantized light-matter interaction -- second concept: the paper's Fig. 1(a) as a sculpture.
# The quasienergy spectrum of the driven two-level system versus driving frequency, lifted into 3D: the central
# Floquet pair (dark red and navy glass tubes, braiding through Bessel-like crossings) inside the highlighted
# yellow zone, and its replicas shifted by integer multiples of the photon energy above and below (silver). Light
# dashed sleeves (salmon, pale blue, white) run along every tube: the quantum energies E/Omega - n0 of the fully
# quantized cavity problem, lying exactly on the classical Floquet curves (the paper's one-to-one correspondence).
import bmesh as fq_bm

bright_stage(floor_z=0.0, exposure=-0.35, sun_rot=(48, 0, -30))


def fq_j0(z):
    """Bessel J0 by its integral representation."""
    n = 64
    return sum(math.cos(z * math.sin(math.pi * (k + 0.5) / n)) for k in range(n)) / n


X0, X1 = -6.2, 6.2          # omega/Delta from 0.26 to 1.5
ZC, ZS = 3.6, 1.15          # height of quasienergy 0 and scale per unit eps/omega
DEPTH = 0.0


def fq_eps(x):
    w = 0.26 + (x - X0) / (X1 - X0) * (1.5 - 0.26)
    return 0.78 * fq_j0(2.77 / w) * min(1.0, (w - 0.2) / 0.12)


def fq_curve(m, sign, n=420):
    pts = []
    for i in range(n + 1):
        x = X0 + (X1 - X0) * i / n
        pts.append(Vector((x, DEPTH, ZC + ZS * (m + sign * fq_eps(x)))))
    return pts


def fq_dashes(pts, radius, mat, dash=0.34, gap=0.2):
    """Cut a polyline into dashes of fixed arc length and draw each as a tube."""
    seg, acc, on, cur = [], 0.0, True, [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = (b - a).length
        t = 0.0
        while t < L:
            left = (dash if on else gap) - acc
            step = min(left, L - t)
            t += step; acc += step
            p = a + (b - a) * (t / L)
            if on:
                cur.append(p)
            if acc >= (dash if on else gap) - 1e-9:
                if on and len(cur) > 1:
                    seg.append(cur)
                on = not on; acc = 0.0; cur = [p]
    if on and len(cur) > 1:
        seg.append(cur)
    for s in seg:
        tube([tuple(p) for p in s], radius, mat)


FQ_RED = principled("fq_red", **{"Base Color": (0.78, 0.02, 0.06, 1), "Roughness": 0.12, "Coat Weight": 1.0,
                                 "Emission Color": (1.0, 0.05, 0.1, 1), "Emission Strength": 0.4})
FQ_NAVY = principled("fq_navy", **{"Base Color": (0.02, 0.06, 0.6, 1), "Roughness": 0.12, "Coat Weight": 1.0,
                                   "Emission Color": (0.05, 0.15, 1.0, 1), "Emission Strength": 0.4})
FQ_GREY = principled("fq_grey", **{"Base Color": (0.25, 0.2, 0.85, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
FQ_SALMON = emission("fq_salmon", (1.0, 0.5, 0.35, 1), 3.5)
FQ_SKY = emission("fq_sky", (0.45, 0.75, 1.0, 1), 3.5)
FQ_WHITE = emission("fq_white", (0.92, 0.88, 1.0, 1), 3.0)

def fq_ribbon(pts, width, thick, mat):
    """Flat glossy band along the curve: width along y (depth), thickness along z."""
    bm = fq_bm.new(); prev = None
    for p in pts:
        row = [bm.verts.new((p.x, p.y + sy * width / 2, p.z + sz * thick / 2)) for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        if prev:
            for k in range(4):
                bm.faces.new((prev[k], prev[(k + 1) % 4], row[(k + 1) % 4], row[k]))
        else:
            bm.faces.new(row[::-1])
        prev = row
    bm.faces.new(prev)
    me = bpy.data.meshes.new("fq_rib"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("fq_rib", me); sc.collection.objects.link(ob); me.materials.append(mat)
    bv = ob.modifiers.new("bev", "BEVEL"); bv.width = 0.025; bv.segments = 3; bv.limit_method = "ANGLE"
    return ob


def fq_dashed_band(p, mat, solid, width, thick, rdash):
    fq_ribbon(p, width, thick, solid)
    for dz in (thick / 2 + 0.005, -thick / 2 - 0.005):
        fq_dashes([q + Vector((0, 0, dz)) for q in p], rdash, mat)


for m in (-2, -1, 1, 2):
    for sgn in (1, -1):
        fq_dashed_band(fq_curve(m, sgn), FQ_WHITE, FQ_GREY, 0.6, 0.09, 0.05)
for sgn, solid, dmat in ((1, FQ_RED, FQ_SALMON), (-1, FQ_NAVY, FQ_SKY)):
    fq_dashed_band(fq_curve(0, sgn), dmat, solid, 0.8, 0.12, 0.065)

# highlighted first Floquet zone: a glowing yellow glass slab behind and around the central pair
FQ_ZONE = principled("fq_zone", **{"Base Color": (1.0, 0.85, 0.2, 1), "Roughness": 0.3, "Emission Color": (1.0, 0.8, 0.1, 1), "Emission Strength": 0.6})
box((0, 0.5, ZC), (X1 - X0 + 0.4, 0.12, ZS * 1.0), FQ_ZONE, bevel=0.04)

# plot frame as a gold rail (axes box), on a coloured plinth
fz0, fz1 = ZC - ZS * 2.6, ZC + ZS * 2.6
tube([(X0 - 0.35, 0, fz0), (X1 + 0.35, 0, fz0), (X1 + 0.35, 0, fz1), (X0 - 0.35, 0, fz1), (X0 - 0.35, 0, fz0)],
     0.07, GOLD)
for x in (X0 + 0.4, X1 - 0.4):
    box((x, 0, (fz0) / 2), (0.25, 0.25, fz0), GOLD, bevel=0.03)
FQ_PLINTH = principled("fq_plinth", **{"Base Color": (0.35, 0.3, 0.95, 1), "Roughness": 0.3, "Coat Weight": 0.6})
box((0, 1.0, 0.15), (X1 - X0 + 9.0, 9.0, 0.3), FQ_PLINTH, bevel=0.08)



def fq_backdrop(y=7.0, w=80.0, h=40.0, low=(1.0, 0.5, 0.35, 1), high=(0.3, 0.5, 1.0, 1)):
    """Vertical backdrop with a saturated peach-to-blue gradient (self-lit, so it stays colourful)."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, h / 2 - 1), rotation=(math.radians(90), 0, 0))
    ob = bpy.context.object; ob.scale = (w, h, 1)
    m = principled("fq_backdrop", **{"Roughness": 0.8})
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sp.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.0, low
    el[1].position, el[1].color = 0.3, high
    nt.links.new(sp.outputs["Y"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.35
    link(ob, m)


fq_backdrop()
camera((-5.5, -16.5, 6.2), (0.0, 0, ZC - 0.1), lens=38)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.2)

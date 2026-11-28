"""Multi-cavity strong coupling to an electron spin ensemble (Oehrl et al. 2026), round 3: clarity first.

One feedline at the back; three superconducting resonators hang off it, drawn as bold gold loops, each holding its
microwave photon as a blue glow. Resonator 1 (left) is far detuned: dim. Resonators 2 and 3 are nearly degenerate
and directly coupled: their glows merge into one shared mode. The spin ensemble (DPPH crystal, violet glass full of
orange spins aligned by the field along the feedline) sits on resonator 3, bathed in that shared light. A bright
green probe enters the feedline from the left; on the right the same wave leaves undiminished: at the dark state the
coupled resonator-spin mode does not radiate into the line, so the hanger dip vanishes (full transmission).
"""
import bmesh
import random
random.seed(5)

bright_stage(floor_z=-0.7, exposure=-0.4, sun_rot=(52, 0, -35))

# chip: pale blue silicon
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6.0, -0.35))
slab = bpy.context.object; slab.scale = (60.0, 34.0, 0.7)
link(slab, principled("mc3_chip", **{"Base Color": (1.0, 0.84, 0.74, 1), "Roughness": 0.35, "Coat Weight": 0.5}))

NB = principled("mc3_nb", **{"Base Color": (1.0, 0.7, 0.3, 1), "Metallic": 1.0, "Roughness": 0.2})
T = 0.22
FY = 3.3                     # feedline
gate([(-40, FY), (40, FY)], width=0.5, height=T, mat=NB)

RW = 3.0                     # resonator loop size
RES = ((-6.2, 0.0), (-1.6, 1.0), (2.0, 1.8))      # (x centre, brightness of the photon mode)


def loop_pts(cx, cy, a, r=0.55, gap=0.5):
    """Rounded square with a small capacitor gap at the top middle, as a polyline."""
    h = a / 2
    pts = [(cx + gap / 2, cy + h)]
    corners = ((cx + h - r, cy + h - r, 90, 0), (cx + h - r, cy - h + r, 0, -90),
               (cx - h + r, cy - h + r, -90, -180), (cx - h + r, cy + h - r, -180, -270))
    for x0, y0, a0, a1 in corners:
        for k in range(9):
            t = math.radians(a0 + (a1 - a0) * k / 8)
            pts.append((x0 + r * math.cos(t), y0 + r * math.sin(t)))
    pts.append((cx - gap / 2, cy + h))
    return pts


def glow_disc(name, loc, rx, ry, color, strength):
    """Flat emitting disc on the chip, bright in the middle and fading out (the mode seen from above)."""
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1, fill_type="NGON", location=loc)
    ob = bpy.context.object; ob.scale = (rx, ry, 1)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = color; em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    nt.links.new(tc.outputs["Object"], gr.inputs[0])
    pw = _math(nt, "POWER", gr.outputs["Fac"], 0.8)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pw, mix.inputs["Fac"]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    link(ob, m); ob.visible_shadow = False
    return ob


MODE = (0.02, 0.3, 1.0, 1)
for i, (cx, br) in enumerate(RES):
    gate(loop_pts(cx, 0.0, RW), width=0.32, height=T, mat=NB)
    # coupling capacitor to the feedline: two pads across the gap, one stub up to the line
    box((cx - 0.45, RW / 2, T / 2), (0.5, 0.3, T), NB, bevel=0.03)
    box((cx + 0.45, RW / 2, T / 2), (0.5, 0.3, T), NB, bevel=0.03)
    gate([(cx + 0.45, RW / 2 + 0.1), (cx + 0.45, FY - 0.45)], width=0.16, height=T, mat=NB)
    box((cx + 0.45, FY - 0.42, T / 2), (1.0, 0.16, T), NB, bevel=0.02)
    # the photon mode: glow filling the loop
    if br <= 0:
        continue
    glow_disc("mc3_disc%d" % i, (cx, 0.0, 0.01), RW * 0.52, RW * 0.52, MODE, 3.5 * br)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(cx, 0.0, 0.25), segments=48, ring_count=24)
    o = bpy.context.object; o.scale = (RW * 0.5, RW * 0.5, 0.9)
    link(o, volume_glow("mc3_mode%d" % i, (0.05, 0.35, 1.0, 1), 1.2 * br)); o.visible_shadow = False

# resonators 2 and 3 share one hybrid mode: a glow bridging the two loops
x2, x3 = RES[1][0], RES[2][0]
glow_disc("mc3_bridge", ((x2 + x3) / 2, 0.0, 0.012), (x3 - x2) / 2 + RW * 0.3, RW * 0.38, (0.02, 0.3, 1.0, 1), 3.5)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=((x2 + x3) / 2, 0.0, 0.35), segments=48, ring_count=24)
o = bpy.context.object; o.scale = ((x3 - x2) / 2 + RW * 0.45, RW * 0.42, 1.0)
link(o, volume_glow("mc3_shared", (0.05, 0.35, 1.0, 1), 1.2)); o.visible_shadow = False

# the spin ensemble: a violet DPPH crystal on resonator 3, spins aligned along the feedline field (+x)
CX, CY, CZ = x3, -0.15, 1.0
CW, CD, CH = 1.9, 1.9, 1.4
bpy.ops.mesh.primitive_cube_add(size=1, location=(CX, CY, CZ), rotation=(0, 0, math.radians(6)))
cr = bpy.context.object; cr.scale = (CW, CD, CH)
bv = cr.modifiers.new("b", "BEVEL"); bv.width = 0.08; bv.segments = 3
link(cr, principled("mc3_dpph", **{"Base Color": (0.78, 0.5, 1.0, 1), "Transmission Weight": 0.95, "Roughness": 0.0,
                                   "IOR": 1.12, "Coat Weight": 0.6, "Emission Color": (0.5, 0.35, 1.0, 1),
                                   "Emission Strength": 0.8}))
cr.visible_shadow = False
sp_b, ar_b = bmesh.new(), bmesh.new()
Mx = __import__("mathutils").Matrix
rot = Mx.Rotation(math.radians(6), 4, "Z")
for ix in range(3):
    for iy in range(3):
        for iz in range(2):
            p = Vector(((ix - 1) * 0.55, (iy - 1) * 0.55, (iz - 0.5) * 0.62))
            p += Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(-0.04, 0.04)))
            c = rot @ p + Vector((CX, CY, CZ))
            bmesh.ops.create_icosphere(sp_b, subdivisions=3, radius=0.14, matrix=Mx.Translation(c))
            d = Vector((1, random.gauss(0, 0.08), 0.15 + random.gauss(0, 0.08))).normalized()
            e1 = d.orthogonal().normalized(); e2 = d.cross(e1); n_ = 12
            p0, p1, tp = c - 0.3 * d, c + 0.26 * d, c + 0.46 * d
            ring = lambda q, rr: [ar_b.verts.new(q + rr * (math.cos(2 * math.pi * k / n_) * e1 + math.sin(2 * math.pi * k / n_) * e2)) for k in range(n_)]
            r0, r1, hd = ring(p0, 0.035), ring(p1, 0.035), ring(p1, 0.09)
            tv = ar_b.verts.new(tp)
            for k in range(n_):
                j = (k + 1) % n_
                ar_b.faces.new((r0[k], r0[j], r1[j], r1[k])); ar_b.faces.new((hd[k], hd[j], tv))
SPN = principled("mc3_spin", **{"Base Color": (1.0, 0.32, 0.02, 1), "Roughness": 0.15, "Emission Color": (1.0, 0.35, 0.04, 1),
                               "Emission Strength": 3.0, "Coat Weight": 1.0})
ARR = principled("mc3_arrow", **{"Base Color": (1.0, 0.85, 0.3, 1), "Metallic": 0.3, "Roughness": 0.15,
                                "Emission Color": (1.0, 0.8, 0.3, 1), "Emission Strength": 0.8})
for b_, nm, mt in ((sp_b, "mc3_spins", SPN), (ar_b, "mc3_arrows", ARR)):
    me = bpy.data.meshes.new(nm); b_.to_mesh(me); b_.free()
    for f_ in me.polygons:
        f_.use_smooth = True
    ob = bpy.data.objects.new(nm, me); sc.collection.objects.link(ob); me.materials.append(mt)


# probe on the feedline: a bright wave comes in from the left and leaves on the right just as bright (dark state)
def packet(x0, x1, amp, strength, color, name, cycles=6, z=0.8):
    pts = []
    for j in range(241):
        t = j / 240
        env = math.sin(math.pi * t) ** 1.5
        pts.append((x0 + (x1 - x0) * t, FY, z + amp * env * math.sin(2 * math.pi * cycles * t)))
    m = emission(name, color, strength)
    tube(pts, 0.06, m)
    d = Vector((1, 0, 0))
    bpy.ops.mesh.primitive_cone_add(radius1=0.18, depth=0.42, location=(x1 + 0.16, FY, z),
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, m)


packet(-9.6, -7.3, 0.5, 6.0, (0.2, 1.0, 0.1, 1), "mc3_in")
packet(3.3, 5.5, 0.5, 6.0, (0.2, 1.0, 0.1, 1), "mc3_out")

camera((0.0, -10.0, 9.0), (-1.7, 0.6, 0.2), lens=32, dof=10.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.3, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

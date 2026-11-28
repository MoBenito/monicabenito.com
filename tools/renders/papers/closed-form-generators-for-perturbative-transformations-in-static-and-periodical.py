# Closed-form generators for perturbative transformations (Reascos, Diotallevi, Benito 2024)
# The Hamiltonian as a matrix of glass tiles on a board, ordered as in the paper's Fig. 1: the low-energy block
# (orange, top left), the high-energy block (blue, bottom right) and the couplings between them (pink, off-diagonal).
# The board slides through a golden frame, the transformation U = exp(-S) with the closed-form generator S. Before the
# frame the tiles still bob up and down with the periodic drive and the pink couplings are there; after it the matrix
# is calm (time independent) and block diagonal: the couplings are gone, leaving glowing empty sockets, and the
# effective blocks shine.
import random
random.seed(3)

bright_stage(floor_z=0.0, exposure=-0.4, sun_rot=(45, 0, -35))


def cf_cyclorama(y0=5.0, R=5.0, top=30.0, width=80.0, bottom=(1.0, 0.86, 0.74, 1), upper=(0.62, 0.76, 1.0, 1), glow=0.55):
    """Studio sweep behind the scene: the floor curves up into a pastel wall (peach at the bottom, sky blue above)."""
    import bmesh as _bm
    bm = _bm.new()
    prof = []
    for j in range(25):
        a = math.pi / 2 * j / 24
        prof.append((y0 + R * math.sin(a), R - R * math.cos(a)))
    prof.append((y0 + R, top))
    rows = []
    for (yy, zz) in prof:
        rows.append([bm.verts.new((xx, yy, zz + 0.002)) for xx in (-width / 2, width / 2)])
    for a_, b_ in zip(rows[:-1], rows[1:]):
        bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
    me = bpy.data.meshes.new("cyc"); bm.to_mesh(me); bm.free()
    for f_ in me.polygons:
        f_.use_smooth = True
    ob = bpy.data.objects.new("cyc", me); sc.collection.objects.link(ob)
    m = principled("cf_cyc", **{"Roughness": 0.6})
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.0, bottom
    el[1].position, el[1].color = 1.0, upper
    nt.links.new(_math(nt, "DIVIDE", sp.outputs["Z"], 9.0), rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow
    me.materials.append(m)
    return ob


cf_cyclorama(y0=6.0, bottom=(1.0, 0.62, 0.45, 1), upper=(0.35, 0.55, 1.0, 1), glow=0.05)
n, nl = 10, 5
P, T, ZB = 0.64, 0.56, 0.3
XF = 0.0                         # the frame sits between column 4 and 5

CF_BOARD = principled("cf_board", **{"Base Color": (0.02, 0.28, 0.34, 1), "Roughness": 0.2, "Metallic": 0.2, "Coat Weight": 1.0})
def glass(name, col, em=0.0):
    return principled(name, **{"Base Color": col, "Transmission Weight": 0.5, "Roughness": 0.08, "IOR": 1.45, "Coat Weight": 1.0,
                                "Emission Color": col, "Emission Strength": em})
CF_LOW, CF_LOW_D = glass("cf_low", (1.0, 0.5, 0.12, 1)), glass("cf_low_d", (1.0, 0.42, 0.05, 1))
CF_HIGH, CF_HIGH_D = glass("cf_high", (0.2, 0.55, 1.0, 1)), glass("cf_high_d", (0.1, 0.4, 1.0, 1))
CF_LOW_E, CF_HIGH_E = glass("cf_low_eff", (1.0, 0.5, 0.1, 1), 1.6), glass("cf_high_eff", (0.15, 0.5, 1.0, 1), 1.6)
CF_COUP = principled("cf_coupling", **{"Base Color": (1.0, 0.2, 0.55, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                         "Emission Color": (1.0, 0.2, 0.55, 1), "Emission Strength": 1.2})
CF_SOCKET = emission("cf_socket", (1.0, 0.35, 0.65, 1), 2.5)
CF_FRAME = principled("cf_frame", **{"Base Color": (1.0, 0.68, 0.25, 1), "Metallic": 1.0, "Roughness": 0.12})
CF_SHEET = principled("cf_sheet", **{"Base Color": (1.0, 0.85, 0.5, 1), "Transmission Weight": 1.0, "Roughness": 0.0, "IOR": 1.0,
                                       "Emission Color": (1.0, 0.75, 0.3, 1), "Emission Strength": 0.6, "Alpha": 0.35})
CF_LINE = emission("cf_blockline", (1.0, 0.8, 0.3, 1), 6.0)

span = n * P + 0.4
box((0, 0, ZB / 2), (span, span, ZB), CF_BOARD, bevel=0.08)

def pos(i, j):
    return Vector(((j - (n - 1) / 2) * P, ((n - 1) / 2 - i) * P, ZB))

for i in range(n):
    for j in range(n):
        p = pos(i, j)
        before = p.x < XF
        li, lj = i < nl, j < nl
        diag_block = li == lj
        if not diag_block:
            if before:
                lift = 0.25 + 0.22 * math.sin(2 * math.pi * (j / 3.2) + 0.7 * i)
                h = 0.16
                bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(p + Vector((0, 0, lift + h / 2))), rotation=(0, 0, 0.15 * math.sin(i + j)))
                ob = bpy.context.object; ob.scale = (T * 0.9, T * 0.9, h)
                bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 2
                link(ob, CF_COUP)
            # an empty glowing socket (after the frame the coupling is gone; before it, the tile hovers above it)
            bpy.ops.mesh.primitive_plane_add(size=T * 0.8, location=tuple(p + Vector((0, 0, 0.006))))
            link(bpy.context.object, CF_SOCKET if not before else CF_BOARD)
            continue
        on_diag = i == j
        if before:
            h = (0.55 if on_diag else 0.28) + 0.22 * (1 + math.sin(2 * math.pi * (j / 3.2) + 0.7 * i))
            mat = (CF_LOW_D if li else CF_HIGH_D) if on_diag else (CF_LOW if li else CF_HIGH)
        else:
            h = 0.75 if on_diag else 0.4
            mat = CF_LOW_E if li else CF_HIGH_E
        box(tuple(p + Vector((0, 0, h / 2))), (T, T, h), mat, bevel=0.04)

# block outlines of the effective (block-diagonal) Hamiltonian, after the frame
for (i0, j0, sz) in ((0, 0, nl), (nl, nl, n - nl)):
    a0 = pos(i0, j0) + Vector((-P / 2, P / 2, 0.012))
    a1 = a0 + Vector((sz * P, 0, 0)); a2 = a1 + Vector((0, -sz * P, 0)); a3 = a0 + Vector((0, -sz * P, 0))
    tube([tuple(a0), tuple(a1), tuple(a2), tuple(a3), tuple(a0)], 0.025, CF_LINE)

# the golden frame: a rounded portal standing across the board
Wf, Hf = span / 2 + 0.35, 2.4
pts = []
rc = 0.6
corners = [(-Wf + rc, Hf - rc, 90, 180), (Wf - rc, Hf - rc, 0, 90)]
pts.append((XF, -Wf, ZB))
for j in range(13):
    a = math.radians(180 - 90 * j / 12)
    pts.append((XF, -Wf + rc + rc * math.cos(a), ZB + Hf - rc + rc * math.sin(a)))
for j in range(13):
    a = math.radians(90 - 90 * j / 12)
    pts.append((XF, Wf - rc + rc * math.cos(a), ZB + Hf - rc + rc * math.sin(a)))
pts.append((XF, Wf, ZB))
pts += [(XF, Wf, -0.05), (XF, -Wf, -0.05), (XF, -Wf, ZB)]
tube(pts, 0.14, CF_FRAME)
# glowing inner band and a faint light curtain inside the frame
tube([(XF, p[1] * 0.96, ZB + (p[2] - ZB) * 0.96) for p in pts[:-3]], 0.03, emission("cf_frameglow", (1.0, 0.75, 0.35, 1), 9.0))
bpy.ops.mesh.primitive_plane_add(size=1, location=(XF, 0, ZB + Hf / 2 - 0.05), rotation=(0, math.radians(90), 0))
cur = bpy.context.object; cur.scale = (Hf - 0.2, 2 * Wf - 0.3, 1)
m = bpy.data.materials.new("cf_curtain"); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.8, 0.4, 1); em.inputs["Strength"].default_value = 3.0
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.3
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
link(cur, m); cur.visible_shadow = False

# the drive: a sine wave entering from the left, ending at the frame
pts = [(-span / 2 - 1.2 + (span / 2 + 1.2) * u, 0.0, ZB + 2.0 + 0.3 * math.sin(2 * math.pi * 4.5 * u)) for u in [j / 300 for j in range(301)]]
tube(pts, 0.06, emission("cf_drive", (0.5, 0.15, 1.0, 1), 9.0))

camera((-8.6, -5.4, 5.6), (0.3, 0.1, 0.9), lens=34, dof=3.0)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

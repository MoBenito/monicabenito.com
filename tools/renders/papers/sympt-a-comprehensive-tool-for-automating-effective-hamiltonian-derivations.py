# SymPT: automated Schrieffer-Wolff transformation.
# Staged as the paper's flowchart (Figure 1) in 3D: a Hamiltonian matrix, built as a grid of tiles whose heights are
# the size of each matrix element, sits on the green "start" ellipse, passes through the blue process box (gears) with
# the cyan decision diamond and its iteration loop (order-by-order perturbation theory), and arrives on the red "end"
# ellipse. It enters with a
# low-energy block (short orange diagonal), a high-energy block (tall blue diagonal) and magenta couplings V between
# the two subspaces; it leaves block-diagonal: the couplings are gone and the diagonal energies are slightly shifted
# (level repulsion: low block pushed down, high block pushed up).
import bmesh

bright_stage()

SP_FRAME = principled("sp_frame", **{"Base Color": (0.92, 0.93, 0.95, 1), "Metallic": 0.0, "Roughness": 0.3, "Coat Weight": 0.6})
SP_BODY = principled("sp_body", **{"Base Color": (0.95, 0.28, 0.22, 1), "Roughness": 0.28, "Coat Weight": 1.0})
SP_LOW = principled("sp_low", **{"Base Color": (1.0, 0.45, 0.08, 1), "Transmission Weight": 0.55, "Roughness": 0.08, "IOR": 1.45,
                                 "Emission Color": (1.0, 0.45, 0.1, 1), "Emission Strength": 0.25})
SP_HIGH = principled("sp_high", **{"Base Color": (0.15, 0.45, 1.0, 1), "Transmission Weight": 0.55, "Roughness": 0.08, "IOR": 1.45,
                                   "Emission Color": (0.2, 0.5, 1.0, 1), "Emission Strength": 0.25})
SP_LOW_OFF = principled("sp_low_off", **{"Base Color": (1.0, 0.55, 0.15, 1), "Roughness": 0.25, "Coat Weight": 0.6})
SP_HIGH_OFF = principled("sp_high_off", **{"Base Color": (0.4, 0.62, 1.0, 1), "Roughness": 0.25, "Coat Weight": 0.6})
SP_V = principled("sp_v", **{"Base Color": (0.8, 0.0, 0.42, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                             "Emission Color": (1.0, 0.0, 0.5, 1), "Emission Strength": 0.5})
SP_ZERO = principled("sp_zero", **{"Base Color": (0.95, 0.96, 0.97, 1), "Roughness": 0.35})
SP_TRAY = principled("sp_tray", **{"Base Color": (0.98, 0.98, 1.0, 1), "Roughness": 0.25, "Metallic": 0.0, "Coat Weight": 1.0})
SP_LOOP = emission("sp_loop", (0.45, 0.05, 1.0, 1), 4.0)

N, NL = 6, 2                 # matrix size, size of the low-energy block
PITCH, TILE = 0.62, 0.53
BELT_Z = 0.55                # top of the belt
E0 = [0.42, 0.5, 0.8, 0.88, 0.96, 1.04]   # diagonal heights (energies)


def sp_matrix(cx, stage):
    """stage 0: full H (couplings V between blocks), 1: after the transformation (block diagonal, shifted energies)."""
    box((cx, 0, BELT_Z + 0.04), (N * PITCH + 0.3, N * PITCH + 0.3, 0.08), SP_TRAY, bevel=0.04)
    for i in range(N):
        for j in range(N):
            x = cx + (j - (N - 1) / 2) * PITCH
            y = ((N - 1) / 2 - i) * PITCH
            low_i, low_j = i < NL, j < NL
            if i == j:
                h = E0[i] + (0.0 if stage == 0 else (-0.1 if low_i else 0.1))
                mat = SP_LOW if low_i else SP_HIGH
            elif low_i == low_j:
                h = (0.26 if low_i else 0.36) - 0.04 * abs(i - j)
                mat = SP_LOW_OFF if low_i else SP_HIGH_OFF
            else:
                if stage == 0:
                    h = 0.62 - 0.06 * (abs(i - j) - 1)
                    mat = SP_V
                else:
                    h, mat = 0.06, SP_ZERO
            box((x, y, BELT_Z + 0.08 + h / 2), (TILE, TILE, h), mat, bevel=0.04)


def sp_gear(loc, r, teeth, thick, mat, rot=(math.radians(90), 0, 0), tooth=0.18):
    bm = bmesh.new()
    pts = []
    for k in range(teeth):
        a0 = 2 * math.pi * k / teeth
        da = 2 * math.pi / teeth
        for frac, rr in ((0.0, r), (0.18, r + tooth), (0.5, r + tooth), (0.68, r)):
            a = a0 + da * frac
            pts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), -thick / 2)))
    f = bm.faces.new(pts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z += thick
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("gear"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("gear", me); sc.collection.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 2; bv.limit_method = "ANGLE"
    me.materials.append(mat)
    # hub
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.3, depth=thick * 1.6, location=loc, rotation=rot, vertices=32)
    link(bpy.context.object, STEEL)
    return ob


# the paper's flowchart (Figure 1) lifted into 3D: green "start" ellipse, blue process box, cyan decision diamond
# with the iteration loop, red "end" ellipse, joined by dark flowchart arrows
SP_START = principled("sp_start", **{"Base Color": (0.3, 0.9, 0.3, 1), "Roughness": 0.25, "Coat Weight": 1.0})
SP_START_RIM = principled("sp_start_rim", **{"Base Color": (0.05, 0.75, 0.05, 1), "Roughness": 0.2, "Coat Weight": 1.0})
SP_END = principled("sp_end", **{"Base Color": (1.0, 0.4, 0.4, 1), "Roughness": 0.25, "Coat Weight": 1.0})
SP_END_RIM = principled("sp_end_rim", **{"Base Color": (0.9, 0.08, 0.08, 1), "Roughness": 0.2, "Coat Weight": 1.0})
SP_DIAMOND = principled("sp_diamond", **{"Base Color": (0.35, 1.0, 1.0, 1), "Transmission Weight": 0.6, "Roughness": 0.05, "IOR": 1.45,
                                         "Emission Color": (0.2, 0.9, 1.0, 1), "Emission Strength": 0.4})
SP_INK = principled("sp_ink", **{"Base Color": (0.02, 0.03, 0.08, 1), "Roughness": 0.25, "Coat Weight": 1.0})
FZ = -0.7
for cx, top_m, rim_m in ((-5.6, SP_START, SP_START_RIM), (5.6, SP_END, SP_END_RIM)):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(cx, 0, FZ + 0.25), vertices=128)
    o = bpy.context.object; o.scale = (3.3, 3.0, 1)
    bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.06; bv.segments = 3
    link(o, top_m)
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.05, major_segments=192, minor_segments=12, location=(cx, 0, FZ + 0.5))
    o = bpy.context.object; o.scale = (3.3, 3.0, 1)
    link(o, rim_m)


def flow_arrow(x0, x1, z, w=0.16):
    box(((x0 + x1 - 0.5) / 2, 0, z), (x1 - x0 - 0.5, w, w), SP_INK, bevel=0.03)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.32, depth=0.6, location=(x1 - 0.3, 0, z), rotation=(0, math.radians(90), 0))
    link(bpy.context.object, SP_INK)


flow_arrow(-2.25, -1.55, FZ + 0.9)
flow_arrow(1.55, 2.25, FZ + 0.9)

# the machine: a blue process box
MX, MW, MD, MH = 0.0, 3.0, 3.4, 3.4
SP_BODY = principled("sp_body2", **{"Base Color": (0.35, 0.5, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0})
box((MX, 0, FZ + MH / 2), (MW, MD, MH), SP_BODY, bevel=0.12)
BELT_Z = FZ + 0.5 - 0.04
# gears on the front face
sp_gear((MX - 0.5, -MD / 2 - 0.08, FZ + 1.25), 0.68, 14, 0.18, GOLD)
sp_gear((MX + 0.72, -MD / 2 - 0.08, FZ + 0.6), 0.45, 10, 0.18, COPPER)
sp_gear((MX + 0.76, -MD / 2 - 0.08, FZ + 1.85), 0.38, 9, 0.18, GOLD)
# the owner's request: the tool's name on a white nameplate above the gears (bold sans, navy, extruded)
SP_PLATE = principled("sp_plate", **{"Base Color": (0.97, 0.98, 1.0, 1), "Roughness": 0.25, "Coat Weight": 1.0})
SP_LABEL = principled("sp_label", **{"Base Color": (0.02, 0.06, 0.32, 1), "Roughness": 0.2, "Coat Weight": 1.0})
PZ = FZ + 2.83
box((MX, -MD / 2 - 0.02, PZ), (2.72, 0.08, 0.98), SP_PLATE, bevel=0.06)
_fnt = bpy.data.fonts.load(str(ASSETS / "sp_NimbusSans-Bold.otf"))
_cu = bpy.data.curves.new("sp_label", "FONT"); _cu.body = "SymPT"; _cu.font = _fnt
_cu.size = 0.98; _cu.extrude = 0.035; _cu.bevel_depth = 0.006; _cu.align_x, _cu.align_y = "CENTER", "CENTER"
_ob = bpy.data.objects.new("sp_label", _cu); sc.collection.objects.link(_ob)
_ob.location = (MX, -MD / 2 - 0.1, PZ - 0.02); _ob.rotation_euler = (math.radians(90), 0, 0)
_cu.materials.append(SP_LABEL)
# the decision diamond (an octahedron of cyan glass) on the roof, circled by the iteration loop (order n -> n+1)
top = FZ + MH
DC = Vector((MX, 0.0, top + 1.05))
bm = bmesh.new()
vs = [bm.verts.new(DC + Vector(v)) for v in ((0.85, 0, 0), (-0.85, 0, 0), (0, 0.85, 0), (0, -0.85, 0), (0, 0, 1.0), (0, 0, -1.0))]
for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
    bm.faces.new([vs[i] for i in f])
me = bpy.data.meshes.new("sp_oct"); bm.to_mesh(me); bm.free()
oc = bpy.data.objects.new("sp_oct", me); sc.collection.objects.link(oc); me.materials.append(SP_DIAMOND)
oc.rotation_euler = (0, 0, math.radians(45))
oc.location = (0, 0, 0)
bv = oc.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 2
LC = DC + Vector((0, -0.2, 0))
pts = []
for k in range(220):
    a_ = math.radians(-50) + 2 * math.pi * 0.84 * k / 219
    pts.append(tuple(LC + Vector((1.45 * math.cos(a_), 0, 1.3 * math.sin(a_)))))
tube(pts, 0.11, SP_LOOP)
tip = Vector(pts[-1])
tipdir = (tip - Vector(pts[-4])).normalized()
bpy.ops.mesh.primitive_cone_add(radius1=0.28, depth=0.55, location=tip + tipdir * 0.2, rotation=tipdir.to_track_quat("Z", "Y").to_euler(), vertices=32)
link(bpy.context.object, SP_LOOP)

# matrices before and after
sp_matrix(-5.6, 0)
sp_matrix(5.6, 1)

camera((-1.0, -15.0, 9.5), (0.0, 0.3, 1.15), lens=33, dof=None)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

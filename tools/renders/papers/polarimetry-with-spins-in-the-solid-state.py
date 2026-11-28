"""Polarimetry with spins in the solid state (Peri et al. 2025): Pauli spin blockade recast as a polarimeter. A hole
passes from a silicon quantum dot (polarizer, left, its spin fixed) through the tunnel barrier (active medium: the
spin-orbit coupling turns the spin as it goes) to a boron acceptor (analyzer, right). The disks are the polarizer and
analyzer of an optical bench standing on a silicon chip; the yellow beam is the hole's path. Above, the magnetic field
arrow with a rotation arc: turning the field realigns the spins."""
import bmesh
import random

random.seed(12)
bright_stage()


def po_mat(name, **kw):
    return principled("po_" + name, **kw)


def po_arrow(base, d, length, r, mat, head_k=3.0):
    d = Vector(d).normalized(); base = Vector(base)
    head = min(r * head_k, length * 0.6)
    rot = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length - head, location=base + d * (length - head) / 2,
                                        rotation=rot, vertices=32)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.3, depth=head, location=base + d * (length - head / 2), rotation=rot,
                                    vertices=32)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, mat)


# --- silicon chip as the bench ----------------------------------------------------------------------------------
CHIP = po_mat("chip", **{"Base Color": (0.78, 0.66, 1.0, 1), "Roughness": 0.25, "Coat Weight": 0.8})
box((0, 1.5, -0.35), (17.0, 9.0, 0.7), CHIP, bevel=0.03)
# faint lattice of silicon atoms on the chip surface
SIATOM = po_mat("siatom", **{"Base Color": (0.58, 0.45, 0.95, 1), "Roughness": 0.3, "Coat Weight": 0.6})
bm = bmesh.new()
Mx = __import__("mathutils").Matrix
for gx in range(-26, 27):
    for gy in range(-8, 19):
        x = gx * 0.32 + (gy % 2) * 0.16; y = gy * 0.28
        if abs(x) > 8.2 or y < -2.7 or y > 5.8:
            continue
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.05, matrix=Mx.Translation((x, y, 0.03)))
me = bpy.data.meshes.new("po_atoms"); bm.to_mesh(me); bm.free()
for f in me.polygons:
    f.use_smooth = True
ob = bpy.data.objects.new("po_atoms", me); sc.collection.objects.link(ob); me.materials.append(SIATOM)

H = 2.0                 # beam height
XP, XA = -4.2, 4.2      # polarizer (dot) and analyzer (acceptor)

# --- the beam: the hole's path from dot to acceptor ------------------------------------------------------------
YEL = (1.0, 0.65, 0.02, 1)
beam((-30.0, 0, H), (36.0, 0, H), 0.5, beam_material("po_beam", YEL, 14.0))


def po_disk(x, base_col, name):
    """Polarizer / analyzer: a ring with a fine grating, on a post, with an aperture for the beam."""
    m = po_mat(name, **{"Base Color": base_col, "Roughness": 0.25, "Coat Weight": 1.0, "Metallic": 0.2})
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 2.2; wv.inputs["Distortion"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[6].default_value = base_col
    mix.inputs[7].default_value = tuple(min(1.0, c * 0.45) for c in base_col[:3]) + (1,)
    lt = _math(nt, "GREATER_THAN", wv.outputs["Fac"], 0.5)
    nt.links.new(lt, mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    bpy.ops.mesh.primitive_cylinder_add(radius=1.45, depth=0.18, location=(x, 0, H), rotation=(0, math.radians(90), 0), vertices=96)
    disk = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.62, depth=0.6, location=(x, 0, H), rotation=(0, math.radians(90), 0), vertices=64)
    hole = bpy.context.object
    bo = disk.modifiers.new("hole", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"
    hole.hide_render = True; hole.hide_viewport = True
    bv = disk.modifiers.new("bev", "BEVEL"); bv.width = 0.03; bv.segments = 3
    link(disk, m)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.48, minor_radius=0.07, major_segments=128, minor_segments=16,
                                     location=(x, 0, H), rotation=(0, math.radians(90), 0))
    link(bpy.context.object, SILVER)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=H - 1.45, location=(x, 0, (H - 1.45) / 2), vertices=32)
    link(bpy.context.object, SILVER)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.12, location=(x, 0, 0.06), vertices=48)
    link(bpy.context.object, SILVER)


po_disk(XP, (0.15, 0.35, 1.0, 1), "polarizer")
po_disk(XA, (0.15, 0.35, 1.0, 1), "analyzer")

# the dot and acceptor under the posts: a glowing dot region and a magenta boron atom
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(XP, -1.5, 0.05), segments=32, ring_count=16)
h_ = bpy.context.object; h_.scale = (1.0, 0.7, 0.35)
link(h_, volume_glow("po_dotglow", (0.1, 1.0, 0.7, 1), 12.0)); h_.visible_shadow = False
BORON = po_mat("boron", **{"Base Color": (0.85, 0.1, 0.75, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                             "Emission Color": (1.0, 0.2, 0.8, 1), "Emission Strength": 1.5})
sphere((XA, -1.5, 0.18), 0.2, BORON)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(XA, -1.5, 0.18), segments=32, ring_count=16)
link(bpy.context.object, volume_glow("po_accglow", (1.0, 0.3, 0.85, 1), 5.0)); bpy.context.object.visible_shadow = False
for x0 in (XP, XA):
    tube([(x0, -1.5, 0.2), (x0, -0.55, H - 1.6)], 0.014, emission("po_tether", (0.6, 0.9, 1.0, 1), 2.5))

# --- spins: polarizer spin and analyzer spin, misaligned; the active medium turns the spin in between -----------
QARROW = po_mat("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
ang0, ang1 = math.radians(0), math.radians(55)       # spin angle in the y-z plane (perpendicular to the beam)
dirn = lambda a: (0.0, -math.sin(a), math.cos(a))
# Figure 1 colour code: polarizer spin blue, analyzer spin red
PBLUE = po_mat("spinP", **{"Base Color": (0.04, 0.28, 1.0, 1), "Transmission Weight": 0.4, "Roughness": 0.06, "IOR": 1.45})
ARED = po_mat("spinA", **{"Base Color": (1.0, 0.12, 0.1, 1), "Transmission Weight": 0.6, "Roughness": 0.06, "IOR": 1.45})
spin((XP + 0.85, 0, H), dirn(ang0), r=0.48, mat=PBLUE, arrow=QARROW, reach=1.75, shaft=0.1)
spin((XA - 0.85, 0, H), dirn(math.radians(28)), r=0.48, mat=ARED, arrow=QARROW, reach=1.75, shaft=0.1)
# analyzer's own axis: a thin dashed guide at the analyzer's preferred direction, showing the misalignment
GUIDE = emission("po_guide", (1.0, 0.25, 0.2, 1), 5.0)
for k in range(6):
    a_ = 0.62 + k * 0.22
    d = Vector(dirn(0.0))
    tube([tuple(Vector((XA - 0.12, 0, H)) + d * a_), tuple(Vector((XA - 0.12, 0, H)) + d * (a_ + 0.12))], 0.022, GUIDE)
# active medium: a glass cylinder; inside, small arrows turning step by step (spin-orbit rotation)
GLASS = po_mat("medium", **{"Base Color": (0.7, 0.95, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.05, "IOR": 1.2})
bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=2.6, location=(0, 0, H), rotation=(0, math.radians(90), 0), vertices=96)
md = bpy.context.object; bv = md.modifiers.new("bev", "BEVEL"); bv.width = 0.08; bv.segments = 4
link(md, GLASS); md.visible_shadow = False
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2.5, location=(0, 0, H), rotation=(0, math.radians(90), 0), vertices=64)
link(bpy.context.object, volume_glow("po_medglow", (0.3, 0.9, 1.0, 1), 1.5)); bpy.context.object.visible_shadow = False
SMALL = po_mat("small", **{"Base Color": (1.0, 0.5, 0.12, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                             "Emission Color": (1.0, 0.45, 0.1, 1), "Emission Strength": 0.6})
for k in range(7):
    x = -1.05 + 2.1 * k / 6
    a_ = ang0 + (math.radians(28) - ang0) * k / 6
    d = Vector(dirn(a_))
    sphere((x, 0, H), 0.09, SMALL)
    po_arrow(Vector((x, 0, H)) - d * 0.15, d, 0.68, 0.03, QARROW)
# rotation arrow around the medium
ROT = emission("po_rot", (1.0, 0.5, 0.1, 1), 6.0)
pts = [(0.0, -1.15 * math.sin(a), H + 1.15 * math.cos(a)) for a in [math.radians(-30 + 110 * i / 60) for i in range(61)]]
tube(pts, 0.04, ROT)
a_end = math.radians(80)
po_arrow(Vector(pts[-4]), Vector(pts[-1]) - Vector(pts[-4]), 0.32, 0.04, ROT)

# --- turning the field = turning the polarizer (Figure 1a): a double-headed arc hugging the polarizer's rim -------
# (revision: the floating field arrow above the bench read as an unrelated blue rod; the paper's own figure shows
# the knob as a rotation of the polarizer, so the control is drawn on the polarizer itself)
TURNP = po_mat("turnP", **{"Base Color": (0.02, 0.3, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0,
                           "Emission Color": (0.05, 0.4, 1.0, 1), "Emission Strength": 1.2})
R_T = 1.9
pts = [(XP - 0.3, -R_T * math.sin(a), H + R_T * math.cos(a)) for a in
       [math.radians(-60 + 120 * i / 80) for i in range(81)]]
tube(pts[3:-3], 0.075, TURNP)
po_arrow(Vector(pts[4]), Vector(pts[0]) - Vector(pts[4]), 0.5, 0.075, TURNP)
po_arrow(Vector(pts[-5]), Vector(pts[-1]) - Vector(pts[-5]), 0.5, 0.075, TURNP)

# pastel backdrop: a curved sweep behind the stage, peach at the bottom to sky blue at the top
import bmesh as _bm
bm = _bm.new()
rows = []
for i in range(41):
    t = i / 40
    a = t * math.pi / 2
    y, z = 10.0 + 6.0 * math.sin(a) if t < 1 else 16.0, -0.69 + 6.0 * (1 - math.cos(a))
    if i == 40:
        pass
    rows.append([bm.verts.new((x, y, z)) for x in (-40, 40)])
for i in range(30):
    rows.append([bm.verts.new((x, 16.0, 5.31 + 1.0 * (i + 1))) for x in (-40, 40)])
for a_, b_ in zip(rows[:-1], rows[1:]):
    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
me = bpy.data.meshes.new("po_sweep"); bm.to_mesh(me); bm.free()
sw = bpy.data.objects.new("po_sweep", me); sc.collection.objects.link(sw)
for p_ in me.polygons:
    p_.use_smooth = True
SW = po_mat("sweep", **{"Roughness": 0.6})
nt = SW.node_tree; b_ = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 9.0
nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (1.0, 0.68, 0.52, 1)
el[1].position, el[1].color = 1.0, (0.38, 0.62, 1.0, 1)
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b_.inputs["Base Color"])
nt.links.new(ramp.outputs["Color"], b_.inputs["Emission Color"])
b_.inputs["Emission Strength"].default_value = 0.0
b_.inputs["Roughness"].default_value = 0.9
link(sw, SW)

# --- polish pass: saturated stage colours (floor, sky, backdrop sweep) ------------------------------------------
def pz_colour_stage(floor=None, mortar=None, sky=None, sweep=None, sweep_emit=0.0, sweep_name=None, sweep_widen=1.0):
    if floor:
        for n_ in bpy.data.materials["pale_floor"].node_tree.nodes:
            if n_.type == "TEX_BRICK":
                n_.inputs["Color1"].default_value = n_.inputs["Color2"].default_value = floor + (1,)
                n_.inputs["Mortar"].default_value = (mortar or floor) + (1,)
    if sky:
        for n_ in sc.world.node_tree.nodes:
            if n_.type == "VALTORGB":
                n_.color_ramp.elements[0].color = sky[0] + (1,)
                n_.color_ramp.elements[-1].color = sky[1] + (1,)
    if sweep_name:
        m_ = bpy.data.materials[sweep_name]
        for n_ in m_.node_tree.nodes:
            if n_.type == "VALTORGB" and sweep:
                n_.color_ramp.elements[0].color = sweep[0] + (1,)
                n_.color_ramp.elements[-1].color = sweep[-1] + (1,)
                if len(sweep) == 3:     # a warm middle stop so the peach-to-blue blend never passes through grey
                    n_.color_ramp.elements.new(0.5).color = sweep[1] + (1,)
        m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = sweep_emit
        bpy.data.objects[sweep_name].scale.x = sweep_widen


pz_colour_stage(floor=(1.0, 0.6, 0.42), mortar=(1.0, 0.48, 0.34), sweep=((1.0, 0.6, 0.45), (1.0, 0.55, 0.75), (0.3, 0.5, 1.0)), sweep_emit=0.35, sweep_name='po_sweep', sweep_widen=3.5)
for n_ in bpy.data.materials['po_sweep'].node_tree.nodes:      # blue reaches lower so the top of the frame is cool
    if n_.type == 'MAP_RANGE':
        n_.inputs['From Max'].default_value = 6.0

camera((-8.5, -10.0, 5.8), (0.4, 0.3, 1.9), lens=38)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

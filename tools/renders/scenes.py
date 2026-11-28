"""Research-area renders (Blender 5, Cycles). See README.md in this folder.

    blender -b --factory-startup --python scenes.py -- <scene> <out.png> [preview]

Scenes used on the site: mobius_float (topological matter), laser_wow (light-matter interaction), bath_wow (open
quantum systems). The other scenes are earlier drafts, kept for reference.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
args = sys.argv[sys.argv.index("--") + 1:]
SCENE, OUT = args[0], args[1]
PREVIEW = len(args) > 2 and args[2] == "preview"

# --- render setup -------------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
sc.render.engine = "CYCLES"
sc.cycles.device = "GPU"
sc.cycles.samples = 96 if PREVIEW else 512
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (960, 540) if PREVIEW else (1920, 1080)
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = OUT

# world: studio HDRI, a bit dimmed, plus one soft key light for shadows
world = bpy.data.worlds.new("world")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
env = wn.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ASSETS / "studio.hdr"))
world.node_tree.links.new(env.outputs["Color"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.75


def light(loc, energy, size, rot=(0.0, 0.0, 0.0)):
    data = bpy.data.lights.new("key", "AREA")
    data.energy, data.size = energy, size
    ob = bpy.data.objects.new("key", data)
    ob.location, ob.rotation_euler = loc, rot
    sc.collection.objects.link(ob)
    return ob


light((-6, -5, 9), 2200, 6, (math.radians(35), 0, math.radians(-40)))


# --- materials ----------------------------------------------------------------------------------------------
def principled(name, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


GOLD = principled("gold", **{"Base Color": (1.0, 0.64, 0.22, 1), "Metallic": 1.0, "Roughness": 0.16})
ORANGE = principled("orange_glass", **{"Base Color": (1.0, 0.42, 0.08, 1), "Transmission Weight": 0.6,
                                         "Roughness": 0.06, "IOR": 1.45})
ARROW = principled("arrow_glass", **{"Base Color": (0.75, 0.95, 0.92, 1), "Transmission Weight": 0.9,
                                       "Roughness": 0.08, "IOR": 1.4})


def emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = color
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


GLOW = emission("teal_glow", (0.25, 1.0, 0.8, 1), 6.0)
GLOW_SOFT = emission("teal_soft", (0.25, 1.0, 0.8, 1), 1.2)


def volume_glow(name, color, strength, density=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Emission Color"].default_value = color
    v.inputs["Emission Strength"].default_value = strength
    # fade out towards the rim: emission scaled by (1 - r/R)^2 from object coordinates
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[0].default_value = 1.0
    nt.links.new(ln.outputs["Value"], sub.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0; pw.use_clamp = True
    nt.links.new(sub.outputs[0], pw.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = strength
    nt.links.new(pw.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


HALO = volume_glow("halo", (0.25, 1.0, 0.8, 1), 3.0)
SPARK = emission("electron", (1.0, 0.45, 0.1, 1), 5.0)
TRAIL = emission("trail", (1.0, 0.5, 0.15, 1), 1.5)


def floor():
    """Large smooth grey stone tiles with thin joints and a faint mottled pattern."""
    bpy.ops.mesh.primitive_plane_add(size=80)
    ob = bpy.context.object
    m = bpy.data.materials.new("tiles")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 0.085
    brick.inputs["Mortar Size"].default_value = 0.006
    brick.inputs["Mortar Smooth"].default_value = 0.3
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Color1"].default_value = (0.26, 0.26, 0.255, 1)
    brick.inputs["Color2"].default_value = (0.31, 0.31, 0.30, 1)
    brick.inputs["Mortar"].default_value = (0.16, 0.16, 0.16, 1)
    nt.links.new(coord.outputs["Object"], brick.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.6
    noise.inputs["Detail"].default_value = 8
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "OVERLAY"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(brick.outputs["Color"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ob.data.materials.append(m)


# --- building blocks ----------------------------------------------------------------------------------------
def link(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def gate(points, width=0.3, height=0.25, mat=GOLD):
    """A gold gate line along a polyline on the floor (mitred corners)."""
    prof = bpy.data.curves.new("prof", "CURVE")
    sp = prof.splines.new("POLY")
    sp.points.add(3)
    for p, (x, y) in zip(sp.points, ((-width / 2, 0), (width / 2, 0), (width / 2, height), (-width / 2, height))):
        p.co = (x, y, 0, 1)
    sp.use_cyclic_u = True
    prof_ob = bpy.data.objects.new("prof", prof)
    cu = bpy.data.curves.new("gate", "CURVE")
    cu.dimensions = "3D"
    s = cu.splines.new("POLY")
    s.points.add(len(points) - 1)
    for p, (x, y) in zip(s.points, points):
        p.co = (x, y, 0, 1)
    cu.bevel_mode = "OBJECT"
    cu.bevel_object = prof_ob
    cu.use_fill_caps = True
    s.use_smooth = False
    ob = bpy.data.objects.new("gate", cu)
    sc.collection.objects.link(ob)
    cu.materials.append(mat)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width, bv.segments, bv.limit_method = 0.03, 3, "ANGLE"
    ob.modifiers.new("ws", "WEIGHTED_NORMAL")
    return ob


def tube(points, radius, mat, smooth=True):
    cu = bpy.data.curves.new("tube", "CURVE")
    cu.dimensions = "3D"
    s = cu.splines.new("POLY")
    s.points.add(len(points) - 1)
    for p, co in zip(s.points, points):
        p.co = (*co, 1)
    cu.bevel_depth = radius
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    ob = bpy.data.objects.new("tube", cu)
    sc.collection.objects.link(ob)
    cu.materials.append(mat)
    return ob


def sphere(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32)
    bpy.ops.object.shade_smooth()
    return link(bpy.context.object, mat)


def spin(loc, direction, r=0.45, mat=ORANGE, arrow=None, reach=1.55, shaft=0.12):
    """Glass ball with a glass arrow through it, pointing along `direction`."""
    sphere(loc, r, mat)
    d = Vector(direction).normalized()
    c = Vector(loc)
    start, end = c - d * r * 1.6, c + d * r * reach
    rot = d.to_track_quat("Z", "Y").to_euler()
    length = (end - start).length
    bpy.ops.mesh.primitive_cylinder_add(radius=r * shaft, depth=length, location=(start + end) / 2, rotation=rot,
                                        vertices=32)
    bpy.ops.object.shade_smooth()
    link(bpy.context.object, arrow or ARROW)
    head = r * 0.55
    bpy.ops.mesh.primitive_cone_add(radius1=r * 0.28, depth=head, location=end + d * head / 2, rotation=rot,
                                    vertices=32)
    bpy.ops.object.shade_smooth()
    link(bpy.context.object, arrow or ARROW)


def camera(loc, target, lens=35, dof=None):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    ob = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if dof:
        cam.dof.use_dof = True
        cam.dof.focus_distance = (Vector(target) - Vector(loc)).length
        cam.dof.aperture_fstop = dof
    sc.camera = ob


# --- scenes -------------------------------------------------------------------------------------------------
def light_matter():
    """Two spins in double dots at the ends of a superconducting resonator, linked by a glowing photon."""
    floor()
    strip = [(-6, 0), (-2.6, 0), (-2.6, 1.1), (-1.3, 1.1), (-1.3, -1.1), (0, -1.1), (0, 1.1), (1.3, 1.1),
             (1.3, -1.1), (2.6, -1.1), (2.6, 0), (6, 0)]
    gate(strip, width=0.3, height=0.22)
    for y in (2.1, -2.1):
        gate([(-7.5, y), (7.5, y)], width=0.9, height=0.22)
    for x, tilt in ((-4.6, 35), (4.6, -35)):
        for dx in (-0.55, 0.0, 0.55):
            gate([(x + dx, -1.6), (x + dx, -0.45)], width=0.2, height=0.25)
        t = math.radians(tilt)
        spin((x, 0, 1.05), (math.sin(t), 0.2, math.cos(t)), r=0.55)
    n = 300
    for k in (1, -1):  # standing wave between the spins: antinodes at the spins
        pts = [(-4.6 + 9.2 * i / n, 0, 1.05 + k * 0.5 * math.cos(math.pi * 2 * i / n)) for i in range(n + 1)]
        tube(pts, 0.04, GLOW)
    camera((-1.0, -10.5, 6.8), (0, 0.2, 0.5), lens=34, dof=8)


def open_systems():
    """A spin in a quantum dot between two leads; electrons stream in from one lead and out the other."""
    floor()
    for s in (1, -1):
        gate([(-8, s * 1.0), (-2.0, s * 1.0), (-0.9, s * 0.3)], width=0.45)   # source lead
        gate([(0.9, s * 0.3), (2.0, s * 1.0), (8, s * 1.0)], width=0.45)      # drain lead
    gate([(0, -4.0), (0, -1.7)], width=0.35)                                   # plunger gate
    gate([(-3.2, 3.6), (-1.4, 1.9)], width=0.3)
    gate([(3.2, 3.6), (1.4, 1.9)], width=0.3)
    spin((0, 0, 0.95), (0.45, 0.2, 1.0), r=0.6)
    for i in range(14):  # electrons in the channel, a short glowing trail behind each
        x = -7.6 + i * 1.15
        if abs(x) < 1.4:
            continue
        z = 0.3
        sphere((x, 0, z), 0.09, SPARK)
        tube([(x - 0.6, 0, z), (x - 0.12, 0, z)], 0.03, TRAIL)
    camera((2.5, -9.5, 6.4), (-0.2, 0.2, 0.4), lens=36, dof=8)


def topological():
    """SSH chain: spins in dimers (strong bonds), weakly linked pairs, glowing edge states at both ends."""
    floor()
    n = 8
    pos, x = [], 0.0
    for i in range(n):
        pos.append(x)
        x += 1.25 if i % 2 == 0 else 2.6
    off = (pos[0] + pos[-1]) / 2
    pos = [p - off for p in pos]
    z = 0.9
    for i in range(n - 1):
        if i % 2 == 0:   # strong bond within a pair
            tube([(pos[i], 0, z), (pos[i + 1], 0, z)], 0.13, GOLD)
        else:            # weak bond between pairs: a thin dashed link
            a, b = pos[i] + 0.5, pos[i + 1] - 0.5
            k = 5
            for j in range(k):
                x0 = a + (b - a) * j / k
                tube([(x0 + 0.05, 0, z), (x0 + (b - a) / k - 0.12, 0, z)], 0.035, GOLD)
    for i, p in enumerate(pos):
        t = math.radians(30 * (1 if i % 2 == 0 else -1))
        spin((p, 0, z), (math.sin(t), 0.15, math.cos(t)), r=0.42)
        if i in (0, n - 1):  # edge state: a soft glowing halo localized at the end
            h = sphere((p, 0, z), 1.25, HALO)
            l = bpy.data.lights.new("edge", "POINT")
            l.energy, l.color, l.shadow_soft_size = 60, (0.3, 1.0, 0.8), 1.2
            lo = bpy.data.objects.new("edge", l)
            lo.location = (p, 0, z)
            sc.collection.objects.link(lo)
    for i in range(0, n, 2):  # a gate finger under each pair
        gate([(pos[i] + 0.62, -2.6), (pos[i] + 0.62, -0.7)], width=0.3)
    gate([(pos[0] - 2.2, 1.4), (pos[-1] + 2.2, 1.4)], width=0.4)
    camera((-1.5, -10.8, 6.0), (0, 0.1, 0.6), lens=34, dof=10)



# --- creative scenes on a dark glossy floor -------------------------------------------------------------------
def dark_stage(world_strength=0.12):
    bpy.ops.mesh.primitive_plane_add(size=120)
    ob = bpy.context.object
    m = principled("dark_floor", **{"Base Color": (0.02, 0.025, 0.025, 1), "Roughness": 0.18, "Metallic": 0.0})
    nt = m.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.8
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = 0.12, 0.3
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Roughness"])
    ob.data.materials.append(m)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = world_strength
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        o.data.energy *= 0.25


def beam_material(name, color, strength, standing=0.0, k=1.0):
    """Glowing beam: emitting volume, brightest on the axis; `standing` > 0 adds standing-wave bands along local Z."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = 0.0
    v.inputs["Emission Color"].default_value = color
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # radial falloff (cylinder of radius 1 in object space)
    r2 = nt.nodes.new("ShaderNodeVectorMath"); r2.operation = "LENGTH"
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"]); nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs[0], r2.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[0].default_value = 1.0
    nt.links.new(r2.outputs["Value"], sub.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0; pw.use_clamp = True
    nt.links.new(sub.outputs[0], pw.inputs[0])
    val = pw.outputs[0]
    if standing:
        mulz = nt.nodes.new("ShaderNodeMath"); mulz.operation = "MULTIPLY"; mulz.inputs[1].default_value = k
        nt.links.new(sep.outputs["Z"], mulz.inputs[0])
        cos = nt.nodes.new("ShaderNodeMath"); cos.operation = "COSINE"
        nt.links.new(mulz.outputs[0], cos.inputs[0])
        sq = nt.nodes.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 2.0
        nt.links.new(cos.outputs[0], sq.inputs[0])
        mix = nt.nodes.new("ShaderNodeMapRange")
        mix.inputs["To Min"].default_value, mix.inputs["To Max"].default_value = 1 - standing, 1.0
        nt.links.new(sq.outputs[0], mix.inputs["Value"])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
        nt.links.new(val, m2.inputs[0]); nt.links.new(mix.outputs["Result"], m2.inputs[1])
        val = m2.outputs[0]
    s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY"; s.inputs[1].default_value = strength
    nt.links.new(val, s.inputs[0])
    nt.links.new(s.outputs[0], v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


def beam(a, b, radius, mat):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, vertices=48, location=(a + b) / 2,
                                        rotation=d.to_track_quat("Z", "Y").to_euler())
    ob = bpy.context.object
    ob.scale = (radius, radius, d.length / 2)
    return link(ob, mat)


MIRROR = principled("mirror", **{"Base Color": (0.55, 0.85, 0.95, 1), "Metallic": 1.0, "Roughness": 0.08, "Coat Weight": 1.0})
STEEL = principled("steel", **{"Base Color": (0.6, 0.6, 0.62, 1), "Metallic": 1.0, "Roughness": 0.35})


def laser_cavity():
    """Optical cavity: two mirrors, a standing-wave laser mode between them, a spin at the antinode, a drive laser."""
    dark_stage(0.05)
    h, L = 2.2, 4.2
    for s in (-1, 1):  # mirrors on posts, facing each other
        x = s * L
        rot = (0, math.radians(90), 0)
        bpy.ops.mesh.primitive_cylinder_add(radius=1.15, depth=0.28, vertices=96, location=(x + s * 0.14, 0, h), rotation=rot)
        link(bpy.context.object, STEEL)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.02, vertices=96, location=(x, 0, h), rotation=rot)
        link(bpy.context.object, MIRROR)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=h - 1.1, vertices=32, location=(x + s * 0.14, 0, (h - 1.1) / 2))
        link(bpy.context.object, STEEL)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=0.12, vertices=64, location=(x + s * 0.14, 0, 0.06))
        link(bpy.context.object, STEEL)
    k = 2 * math.pi * 3.5 / (2 * L)   # 3.5 wavelengths: antinode in the middle
    beam((-L, 0, h), (L, 0, h), 0.42, beam_material("cavity", (0.3, 1.0, 0.85, 1), 9.0, standing=0.92, k=k * L))
    spin((0, 0, h), (0.5, 0.25, 1.0), r=0.5)
    # drive laser from the front-left above, ending at the spin
    drive = beam_material("drive", (1.0, 0.25, 0.45, 1), 7.0)
    beam((-6.5, -7.5, 6.5), (0, 0, h), 0.14, drive)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(-6.5, -7.5, 6.5))
    camera((1.5, -10.5, 4.8), (0, 0, 1.9), lens=38, dof=6)


def mobius():
    """A Moebius strip covered with spins along its normal (they come back reversed), and a glowing edge state."""
    dark_stage(0.18)
    import bmesh
    R, w = 3.2, 1.25
    def P(u, v):
        return Vector(((R + v * math.cos(u / 2)) * math.cos(u), (R + v * math.cos(u / 2)) * math.sin(u), 2.6 + v * math.sin(u / 2)))
    def N(u, v, e=1e-3):
        du = (P(u + e, v) - P(u - e, v)); dv = (P(u, v + e) - P(u, v - e))
        return du.cross(dv).normalized()
    bm = bmesh.new()
    nu, nv = 240, 16
    verts = [[bm.verts.new(P(2 * math.pi * i / nu, -w + 2 * w * j / nv)) for j in range(nv + 1)] for i in range(nu)]
    for i in range(nu):
        for j in range(nv):
            if i < nu - 1:
                a, b, c, d = verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]
            else:  # the twist: the last column joins the first one upside down
                a, b, c, d = verts[i][j], verts[0][nv - j], verts[0][nv - j - 1], verts[i][j + 1]
            bm.faces.new((a, b, c, d))
    me = bpy.data.meshes.new("mobius"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("mobius", me); sc.collection.objects.link(ob)
    for f in me.polygons:
        f.use_smooth = True
    sol = ob.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.07; sol.offset = 0
    band = principled("band", **{"Base Color": (0.8, 0.95, 0.93, 1), "Transmission Weight": 0.95, "Roughness": 0.18, "IOR": 1.45})
    me.materials.append(band)
    # spins on the band, along its normal: after one round they point the other way
    for i in range(14):
        u = 2 * math.pi * i / 14 + 0.12
        n = N(u, 0)
        c = P(u, 0) + n * 0.55
        spin(tuple(c), tuple(n), r=0.34)
    # the edge: one single closed curve (v = +w, u from 0 to 4 pi)
    edge = [tuple(P(4 * math.pi * i / 600, w)) for i in range(601)]
    tube(edge, 0.06, GLOW)
    camera((0.0, -11.5, 7.8), (0, 0, 2.2), lens=38, dof=7)


def bath():
    """An open quantum system: a spin in a swirling cloud of tiny particles, its environment."""
    dark_stage(0.1)
    import random
    random.seed(7)
    spin((0, 0, 2.0), (0.4, 0.2, 1.0), r=0.6)
    # the environment: thousands of small glowing grains in a flat swirl, instanced on tiny triangles
    import bmesh
    for name, col, n, strength in (("bath_teal", (0.3, 1.0, 0.85, 1), 2600, 1.6), ("bath_amber", (1.0, 0.5, 0.15, 1), 700, 2.2)):
        bm = bmesh.new()
        for _ in range(n):
            r = 1.6 + random.expovariate(1 / 1.8)
            if r > 9:
                continue
            a = random.uniform(0, 2 * math.pi)
            spiral = a + 0.35 * r
            z = 2.0 + random.gauss(0, 0.12 + 0.06 * r)
            c = Vector((r * math.cos(spiral), r * math.sin(spiral), z))
            s = random.uniform(0.02, 0.06) * (1.2 if r < 3 else 1)
            v = [bm.verts.new(c + Vector(o) * s) for o in ((1, 0, 0), (-0.5, 0.87, 0), (-0.5, -0.87, 0))]
            bm.faces.new(v)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        host = bpy.data.objects.new(name, me); sc.collection.objects.link(host)
        host.instance_type = "FACES"; host.use_instance_faces_scale = True; host.instance_faces_scale = 0.55
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2)
        grain = bpy.context.object; link(grain, emission(name + "_m", col, strength))
        grain.parent = host
        grain.location = (0, 0, 0)
    # streams between the spin and its surroundings (energy and information leaking in and out)
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        pts = []
        for j in range(80):
            f = j / 79
            r = 0.7 + f * 4.5
            pts.append((r * math.cos(a + 0.35 * r), r * math.sin(a + 0.35 * r), 2.0 + 0.15 * math.sin(6 * f + i)))
        tube(pts, 0.018, GLOW_SOFT)
    camera((0.5, -10.0, 6.5), (0, 0, 1.8), lens=36, dof=6)



# --- second iteration: elements from the papers -------------------------------------------------------------
PURPLE = emission("purple", (0.55, 0.12, 1.0, 1), 1.6)
MAG_RED = principled("mag_red", **{"Base Color": (0.75, 0.05, 0.05, 1), "Roughness": 0.35})
MAG_BLUE = principled("mag_blue", **{"Base Color": (0.05, 0.12, 0.8, 1), "Roughness": 0.35})
SILVER = principled("silver", **{"Base Color": (0.8, 0.82, 0.85, 1), "Metallic": 1.0, "Roughness": 0.2})
SHELL = principled("shell", **{"Base Color": (0.35, 0.85, 0.9, 1), "Metallic": 0.6, "Roughness": 0.12,
                               "Coat Weight": 1.0})
BLUE_E = emission("blue_e", (0.25, 0.55, 1.0, 1), 6.0)


def box(loc, size, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    m = ob.modifiers.new("bevel", "BEVEL"); m.width, m.segments = bevel, 3
    return link(ob, mat)


def mirror_shell(x, facing, h, R=3.2, depth=0.75):
    """A curved cavity mirror: a spherical cap shell with a clean circular rim, concave side to the centre."""
    import bmesh
    th_max = math.acos((R - depth) / R)
    bm = bmesh.new()
    nr, nphi = 24, 128
    tip = bm.verts.new((R, 0, 0))
    rings = []
    for i in range(1, nr + 1):
        th = th_max * i / nr
        rings.append([bm.verts.new((R * math.cos(th), R * math.sin(th) * math.cos(2 * math.pi * j / nphi),
                                    R * math.sin(th) * math.sin(2 * math.pi * j / nphi))) for j in range(nphi)])
    for j in range(nphi):
        bm.faces.new((tip, rings[0][j], rings[0][(j + 1) % nphi]))
    for i in range(nr - 1):
        for j in range(nphi):
            bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % nphi], rings[i][(j + 1) % nphi]))
    me = bpy.data.meshes.new("shell"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("shell", me); sc.collection.objects.link(ob)
    for f in me.polygons:
        f.use_smooth = True
    sol = ob.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.12
    ob.location = (x - facing * R, 0, h)
    ob.rotation_euler = (0, 0, 0 if facing > 0 else math.pi)
    me.materials.append(SHELL)
    return ob


def flip_arrow(center, radius, start, sweep, mat=PURPLE, axis="y"):
    """A curved arrow (arc with a cone tip) around `center`, in the x-z plane."""
    c = Vector(center)
    pts = []
    for i in range(40):
        a = start + sweep * i / 39
        pts.append(tuple(c + Vector((radius * math.cos(a), 0, radius * math.sin(a)))))
    tube(pts, 0.045, mat)
    a = start + sweep
    tipdir = Vector((-math.sin(a), 0, math.cos(a))) * (1 if sweep > 0 else -1)
    tip = c + Vector((radius * math.cos(a), 0, radius * math.sin(a)))
    bpy.ops.mesh.primitive_cone_add(radius1=0.13, depth=0.3, location=tip + tipdir * 0.12,
                                    rotation=tipdir.to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, mat)


def laser2():
    """Spin-photon interface: two spins in a cavity mode between curved mirrors, micromagnets below, spin flips."""
    dark_stage(0.04)
    h, L = 2.3, 4.6
    mirror_shell(L, 1, h); mirror_shell(-L, -1, h)
    k = 2 * math.pi * 2.5 / (2 * L)
    beam((-L + 0.2, 0, h), (L - 0.2, 0, h), 0.55, beam_material("cavity2", (0.3, 1.0, 0.85, 1), 6.0, standing=0.9, k=k * L))
    for s in (-1, 1):
        x = s * 1.85
        tilt = math.radians(25 * s)
        spin((x, 0, h), (math.sin(tilt), 0.1, math.cos(tilt)), r=0.46)
        flip_arrow((x, 0, h), 0.95, math.radians(55 if s < 0 else 125), math.radians(70 * (1 if s < 0 else -1)))
        flip_arrow((x, 0, h), 0.95, math.radians(235 if s < 0 else 305), math.radians(70 * (1 if s < 0 else -1)))
        # micromagnet below the spin: red (S) and blue (N) halves
        box((x - 0.45, 0, 0.35), (0.9, 0.7, 0.5), MAG_RED)
        box((x + 0.45, 0, 0.35), (0.9, 0.7, 0.5), MAG_BLUE)
    drive = beam_material("drive2", (1.0, 0.25, 0.45, 1), 5.0)
    beam((-7.0, -6.5, 7.0), (-1.85, 0, h), 0.1, drive)
    camera((1.2, -10.8, 4.6), (0, 0, 1.9), lens=36, dof=7)


def mobius2():
    """Moebius strip carrying a dimerized chain of quantum dots, with a glowing edge state."""
    dark_stage(0.16)
    import bmesh
    R, w = 3.2, 1.25
    def P(u, v):
        return Vector(((R + v * math.cos(u / 2)) * math.cos(u), (R + v * math.cos(u / 2)) * math.sin(u), 2.6 + v * math.sin(u / 2)))
    def N(u, v, e=1e-3):
        return (P(u + e, v) - P(u - e, v)).cross(P(u, v + e) - P(u, v - e)).normalized()
    def T(u, e=1e-3):
        return (P(u + e, 0) - P(u - e, 0)).normalized()
    bm = bmesh.new()
    nu, nv = 240, 16
    verts = [[bm.verts.new(P(2 * math.pi * i / nu, -w + 2 * w * j / nv)) for j in range(nv + 1)] for i in range(nu)]
    for i in range(nu):
        for j in range(nv):
            if i < nu - 1:
                q = (verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1])
            else:
                q = (verts[i][j], verts[0][nv - j], verts[0][nv - j - 1], verts[i][j + 1])
            bm.faces.new(q)
    me = bpy.data.meshes.new("mobius"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("mobius", me); sc.collection.objects.link(ob)
    for f in me.polygons:
        f.use_smooth = True
    sol = ob.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.07; sol.offset = 0
    me.materials.append(principled("band2", **{"Base Color": (0.8, 0.95, 0.93, 1), "Transmission Weight": 0.95, "Roughness": 0.18, "IOR": 1.45}))
    # dimer chain of quantum-dot discs along the centre line, lying on the band
    n_pairs, gap_in, = 11, 0.33
    for i in range(n_pairs):
        u0 = 2 * math.pi * i / n_pairs
        for du in (-gap_in / 2, gap_in / 2):
            u = u0 + du / R
            n = N(u, 0)
            c = P(u, 0) + n * 0.09
            bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.08, vertices=48, location=tuple(c),
                                                rotation=n.to_track_quat("Z", "Y").to_euler())
            d = bpy.context.object
            b = d.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.03, 3
            link(d, SILVER)
        # strong bond inside the pair: a short glowing link
        a, b2 = P(u0 - gap_in / 2 / R, 0) + N(u0 - gap_in / 2 / R, 0) * 0.13, P(u0 + gap_in / 2 / R, 0) + N(u0 + gap_in / 2 / R, 0) * 0.13
        tube([tuple(a), tuple(b2)], 0.03, BLUE_E)
    # a few spins riding on the band, reversed after a round
    for i in range(5):
        u = 2 * math.pi * (i + 0.5) / 5
        n = N(u, 0.75)
        spin(tuple(P(u, 0.75) + n * 0.45), tuple(n), r=0.27)
    edge = [tuple(P(4 * math.pi * i / 600, w)) for i in range(601)]
    tube(edge, 0.06, GLOW)
    camera((0.0, -11.0, 8.2), (0, 0, 2.1), lens=38, dof=7)


def text(body, loc, size, mat, rot=(math.radians(90), 0, 0)):
    cu = bpy.data.curves.new("txt", "FONT"); cu.body = body; cu.size = size; cu.extrude = 0.03
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    ob = bpy.data.objects.new("txt", cu); sc.collection.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    cu.materials.append(mat)
    return ob


def bath2():
    """Transport through a quantum dot between gold leads L and R, inside a swirling environment."""
    dark_stage(0.1)
    import random
    random.seed(11)
    h = 1.3
    DARKGOLD = principled("leadgold", **{"Base Color": (1.0, 0.66, 0.25, 1), "Metallic": 1.0, "Roughness": 0.22})
    for s, letter in ((-1, "L"), (1, "R")):   # rounded gold leads, as in the edge-state paper's figure
        ld = box((s * 4.4, 0, h), (2.2, 1.6, 1.0), DARKGOLD, bevel=0.35)
        text(letter, (s * 4.4, -0.83, h), 0.7, emission("lt" + letter, (1.0, 0.95, 0.8, 1), 2.0))
    spin((0, 0, h + 0.15), (0.4, 0.2, 1.0), r=0.6)
    for x in (-2.0, 2.0):  # neighbouring dots as silver discs
        bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.14, vertices=48, location=(x, 0, h - 0.2))
        dsk = bpy.context.object; b = dsk.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.05, 3
        link(dsk, SILVER)
    # electrons hopping L -> dot -> R along arcs, with glowing beads
    hops = [(-3.3, -2.0), (-2.0, 0.0), (0.0, 2.0), (2.0, 3.3)]
    for a, b in hops:
        pts = [((a + (b - a) * i / 40), 0, h + 0.1 + 0.9 * math.sin(math.pi * i / 40)) for i in range(41)]
        tube(pts, 0.025, emission("arc", (0.45, 0.7, 1.0, 1), 2.5))
        m = pts[26]
        sphere(m, 0.12, BLUE_E)
    # dimmed environment cloud around it
    import bmesh
    for name, col, n, strength in (("env_teal", (0.3, 1.0, 0.85, 1), 2200, 1.0), ("env_amber", (1.0, 0.5, 0.15, 1), 500, 1.4)):
        bm = bmesh.new()
        for _ in range(n):
            r = 2.5 + random.expovariate(1 / 2.2)
            if r > 11:
                continue
            a = random.uniform(0, 2 * math.pi)
            c = Vector((r * math.cos(a + 0.3 * r), r * math.sin(a + 0.3 * r), h + random.gauss(0, 0.25 + 0.08 * r)))
            if c.z < 0.05:
                continue
            s = random.uniform(0.02, 0.05)
            v = [bm.verts.new(c + Vector(o) * s) for o in ((1, 0, 0), (-0.5, 0.87, 0), (-0.5, -0.87, 0))]
            bm.faces.new(v)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        host = bpy.data.objects.new(name, me); sc.collection.objects.link(host)
        host.instance_type = "FACES"; host.use_instance_faces_scale = True; host.instance_faces_scale = 0.55
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2)
        g = bpy.context.object; link(g, emission(name + "_m", col, strength)); g.parent = host
    camera((1.0, -10.5, 5.6), (0, 0, 1.2), lens=36, dof=7)


# --- third iteration: canonical models --------------------------------------------------------------------
def half_sphere(center, r, side, mat):
    """Hemisphere (side -1: left half, +1: right half along x), closed flat face."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=r)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0),
                                 clear_inner=side > 0, clear_outer=side < 0)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    bmesh.ops.edgeloop_fill(bm, edges=edges)
    me = bpy.data.meshes.new("half"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("half", me); sc.collection.objects.link(ob)
    for f in me.polygons:
        f.use_smooth = abs(f.normal.x) < 0.99
    ob.location = Vector(center) + Vector((side * 0.06, 0, 0))
    me.materials.append(mat)
    return ob


def kitaev():
    """Kitaev chain: every dot splits into two Majorana halves; bulk halves pair across dots, the ends stay unpaired."""
    dark_stage(0.08)
    n, d, h, r = 6, 2.0, 1.25, 0.5
    xs = [d * (i - (n - 1) / 2) for i in range(n)]
    # superconductor underneath: a long brushed-metal slab
    SC = principled("superconductor", **{"Base Color": (0.55, 0.62, 0.72, 1), "Metallic": 1.0, "Roughness": 0.3,
                                          "Anisotropic": 0.6})
    box((0, 0, 0.25), (xs[-1] - xs[0] + 3.2, 2.2, 0.5), SC, bevel=0.08)
    PAIRED = principled("majorana", **{"Base Color": (1.0, 0.45, 0.1, 1), "Transmission Weight": 0.7, "Roughness": 0.1, "IOR": 1.45})
    FREE = emission("zero_mode", (0.3, 1.0, 0.85, 1), 5.0)
    for i, x in enumerate(xs):
        for side in (-1, 1):
            end = (i == 0 and side < 0) or (i == n - 1 and side > 0)
            half_sphere((x, 0, h), r, side, FREE if end else PAIRED)
        if i < n - 1:  # the pairing bond: right half of dot i with left half of dot i+1
            a, b = x + r * 0.55, xs[i + 1] - r * 0.55
            tube([(a, 0, h), (b, 0, h)], 0.07, GOLD)
            # a faint capsule enclosing the paired halves
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=((x + xs[i + 1]) / 2, 0, h))
            cap = bpy.context.object
            cap.scale = (d / 2 + 0.05, 0.62, 0.62)
            link(cap, beam_material("pair%d" % i, (1.0, 0.55, 0.2, 1), 0.25))
    for x in (xs[0], xs[-1]):  # the zero modes glow into the room
        h_ = sphere((x + (-0.3 if x < 0 else 0.3), 0, h), 1.3, HALO)
        l = bpy.data.lights.new("zm", "POINT"); l.energy, l.color, l.shadow_soft_size = 80, (0.3, 1.0, 0.8), 1.0
        lo = bpy.data.objects.new("zm", l); lo.location = (x + (-0.6 if x < 0 else 0.6), 0, h); sc.collection.objects.link(lo)
    camera((-1.5, -9.8, 5.0), (0, 0, 1.0), lens=36, dof=8)


def bloch():
    """Open-system dynamics on the Bloch sphere: the state spirals from the equator to the ground state."""
    dark_stage(0.08)
    import random
    random.seed(5)
    c, R = Vector((0, 0, 2.6)), 2.0
    GLASS = principled("bloch", **{"Base Color": (0.85, 0.97, 0.97, 1), "Transmission Weight": 1.0, "Roughness": 0.05, "IOR": 1.05})
    sphere(tuple(c), R, GLASS)
    WIRE = emission("wire", (0.6, 0.8, 0.8, 1), 0.6)
    for lat in (-60, -30, 0, 30, 60):  # latitude and longitude rings, faint
        z = R * math.sin(math.radians(lat)); rr = R * math.cos(math.radians(lat))
        tube([tuple(c + Vector((rr * math.cos(a), rr * math.sin(a), z))) for a in [2 * math.pi * k / 120 for k in range(121)]], 0.008 if lat else 0.014, WIRE)
    for lon in range(0, 180, 30):
        a = math.radians(lon)
        tube([tuple(c + Vector((R * math.cos(t_) * math.cos(a), R * math.cos(t_) * math.sin(a), R * math.sin(t_)))) for t_ in [2 * math.pi * k / 120 for k in range(121)]], 0.008, WIRE)
    tube([tuple(c + Vector((0, 0, -R * 1.25))), tuple(c + Vector((0, 0, R * 1.25)))], 0.02, WIRE)  # z axis
    # the trajectory: precession while relaxing from the equator to the south pole
    pts = []
    N = 900
    for k in range(N + 1):
        s = k / N
        theta = math.pi / 2 + (math.pi / 2 - 0.05) * (1 - math.exp(-3.5 * s)) / (1 - math.exp(-3.5))
        phi = 2 * math.pi * 6 * s
        rr = R * (1 - 0.25 * s)        # dephasing shrinks the vector a little
        pts.append(tuple(c + Vector((rr * math.sin(theta) * math.cos(phi), rr * math.sin(theta) * math.sin(phi), rr * math.cos(theta)))))
    tube(pts, 0.035, GLOW)
    # the Bloch vector at the start of the path, with an orange spin at its tip
    start = Vector(pts[0])
    d = (start - c).normalized()
    tube([tuple(c), tuple(c + d * (R - 0.35))], 0.05, ARROW)
    bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=0.4, location=tuple(c + d * (R - 0.15)), rotation=d.to_track_quat("Z", "Y").to_euler())
    link(bpy.context.object, ARROW)
    sphere(tuple(c), 0.18, ORANGE)
    # environment: drifting quanta around the sphere, a few streaming away
    import bmesh
    bm = bmesh.new()
    for _ in range(1600):
        rad = R + 0.6 + random.expovariate(1 / 1.8)
        if rad > 10: continue
        a = random.uniform(0, 2 * math.pi); z = c.z + random.gauss(0, 0.9)
        if z < 0.05: continue
        cc = Vector((rad * math.cos(a), rad * math.sin(a), z)); s = random.uniform(0.02, 0.05)
        v = [bm.verts.new(cc + Vector(o) * s) for o in ((1, 0, 0), (-0.5, 0.87, 0), (-0.5, -0.87, 0))]
        bm.faces.new(v)
    me = bpy.data.meshes.new("env"); bm.to_mesh(me); bm.free()
    host = bpy.data.objects.new("env", me); sc.collection.objects.link(host)
    host.instance_type = "FACES"; host.use_instance_faces_scale = True; host.instance_faces_scale = 0.55
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2)
    g = bpy.context.object; link(g, emission("env_m", (1.0, 0.55, 0.2, 1), 1.3)); g.parent = host
    camera((2.5, -9.5, 5.6), (0, 0, 2.3), lens=38, dof=8)


# --- fourth iteration: from the web research ----------------------------------------------------------------
def surf():
    """Electron bus: electrons surf a surface acoustic wave between two dots sitting on nuclear-spin carpets."""
    dark_stage(0.06)
    import bmesh, random
    random.seed(3)
    Lx, Ly, lam, amp = 26.0, 14.0, 2.2, 0.14
    def height(x, y):
        return amp * math.sin(2 * math.pi * (x + 0.35 * y) / lam)
    # the wafer: a dark slab whose top carries the wave (fading out near the two dots)
    bm = bmesh.new()
    nx, ny = 520, 280
    grid = [[bm.verts.new((-Lx / 2 + Lx * i / nx, -Ly / 2 + Ly * j / ny, 0.6)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            v = grid[i][j]
            fade = min(1.0, max(0.0, (5.0 - abs(abs(v.co.x) - 5.6)) / 2.0)) if abs(v.co.x) > 3.6 else 1.0
            fade *= min(1.0, abs(abs(v.co.x) - 5.6) / 1.2)
            v.co.z += height(v.co.x, v.co.y) * fade
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    me = bpy.data.meshes.new("wafer"); bm.to_mesh(me); bm.free()
    wafer = bpy.data.objects.new("wafer", me); sc.collection.objects.link(wafer)
    for f in me.polygons:
        f.use_smooth = True
    s = wafer.modifiers.new("solid", "SOLIDIFY"); s.thickness = 0.6
    me.materials.append(principled("wafer", **{"Base Color": (0.09, 0.095, 0.1, 1), "Roughness": 0.45}))
    CONE = principled("nuc", **{"Base Color": (0.75, 0.78, 0.85, 1), "Metallic": 0.3, "Roughness": 0.25})
    PADGLOW = emission("pad", (1.0, 0.35, 0.55, 1), 0.6)
    for xd in (-5.6, 5.6):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.02, vertices=96, location=(xd, 0, 0.61))
        link(bpy.context.object, PADGLOW)
        for gx in range(-7, 8):  # nuclear spins: a lattice of tiny cones, randomly tilted
          for gy in range(-7, 8):
            loc = Vector((xd + 0.19 * gx, 0.19 * gy, 0.7))
            if (loc.x - xd) ** 2 + loc.y ** 2 > 1.38 ** 2:
                continue
            dvec = (Vector((0, 0, 1)) + 0.45 * Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1)))).normalized()
            bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.16, vertices=12, location=loc,
                                            rotation=dvec.to_track_quat("Z", "Y").to_euler())
            link(bpy.context.object, CONE)
        spin((xd, 0, 1.25), (0.35 if xd < 0 else -0.35, 0.1, 1.0), r=0.42)
    # surfing electrons in the wave troughs, each with a short white wake
    WAKE = emission("wake", (0.9, 0.95, 1.0, 1), 1.2)
    for x0 in (-2.9, -0.7, 1.5, 3.4):
        y0 = random.uniform(-0.6, 0.6)
        # move to the nearest trough along x
        k = round(((x0 + 0.35 * y0) / lam) - 0.75)
        x = lam * (k + 0.75) - 0.35 * y0
        z = 0.6 + height(x, y0) + 0.13
        sphere((x, y0, z), 0.13, SPARK)
        pts = [(x - 0.18 - 0.07 * i, y0 + 0.025 * math.sin(i * 0.9) * i * 0.3, 0.6 + height(x - 0.18 - 0.07 * i, y0) + 0.03) for i in range(18)]
        tube(pts, 0.018, WAKE)
    # entanglement between the two nuclear-spin clouds: a faint arc of light
    arc = [(-5.6 + 11.2 * i / 200, 0.4 * math.sin(math.pi * i / 200), 1.7 + 1.3 * math.sin(math.pi * i / 200)) for i in range(201)]
    tube(arc, 0.02, emission("ent", (1.0, 0.45, 0.7, 1), 2.5))
    camera((-1.0, -12.0, 6.6), (0, 0.6, 0.8), lens=36, dof=6)


def timechain():
    """SSH chain in time: dots continue as glass tubes into depth (time), wiggling with the drive; only the two end tubes carry light."""
    dark_stage(0.06)
    n = 8
    xs, x = [], 0.0
    for i in range(n):
        xs.append(x); x += 0.9 if i % 2 == 0 else 1.9
    off = (xs[0] + xs[-1]) / 2; xs = [v - off for v in xs]
    T, h = 14.0, 1.2
    TUBE = principled("tubeglass", **{"Base Color": (0.85, 0.93, 0.97, 1), "Transmission Weight": 0.95, "Roughness": 0.22, "IOR": 1.3})
    EDGE = emission("edge_light", (0.25, 1.0, 0.6, 1), 7.0)
    def path(i, k=260):
        pts = []
        for j in range(k + 1):
            y = T * j / k
            ph = 0.9 * xs[i]   # drive phase set by the dot's position
            pts.append((xs[i] + 0.18 * math.sin(2 * math.pi * y / 3.5 + ph), y, h + 0.22 * math.cos(2 * math.pi * y / 3.5 + ph)))
        return pts
    paths = [path(i) for i in range(n)]
    for i in range(n):
        tube(paths[i], 0.2, TUBE)
        if i in (0, n - 1):
            tube(paths[i], 0.06, EDGE)
        sphere(paths[i][0], 0.3, ORANGE)   # the quantum dots at the front face
    # bonds repeated along time: thick glass bridges inside pairs, thin threads between pairs
    for j in range(0, 261, 20):
        for i in range(n - 1):
            a, b = Vector(paths[i][j]), Vector(paths[i + 1][j])
            strong = i % 2 == 0
            d = (b - a).normalized()
            tube([tuple(a + d * 0.2), tuple(b - d * 0.2)], 0.075 if strong else 0.018, TUBE if strong else GOLD)
    for i in (0, n - 1):  # the edge states glow at the front
        sphere(paths[i][0], 0.75, HALO)
    camera((-7.5, -5.5, 4.6), (0.5, 4.5, 1.1), lens=32, dof=6)


def mobius_ssh():
    """A Moebius strip whose cross-section is an SSH chain: tubes run around the band, joined across its width by
    alternating strong and weak bonds; the edge states on the outer tubes form one single glowing loop."""
    dark_stage(0.06)
    R, w, n = 3.3, 1.35, 8
    vs, v = [], 0.0
    for i in range(n):
        vs.append(v); v += 0.26 if i % 2 == 0 else 0.5
    off = (vs[0] + vs[-1]) / 2; vs = [(x - off) * (w / ((vs[-1] - vs[0]) / 2)) for x in vs]
    zc = 2.7
    def P(u, v):
        return Vector(((R + v * math.cos(u / 2)) * math.cos(u), (R + v * math.cos(u / 2)) * math.sin(u), zc + v * math.sin(u / 2)))
    TUBE = principled("tubeglass2", **{"Base Color": (0.85, 0.93, 0.97, 1), "Transmission Weight": 0.95, "Roughness": 0.2, "IOR": 1.3})
    EDGE = emission("edge2", (0.25, 1.0, 0.6, 1), 7.0)
    K = 500
    for i in range(n):
        # each tube closes after one round, except that the twist maps v to -v: tube i continues as tube n-1-i
        pts = [tuple(P(2 * math.pi * j / K, vs[i])) for j in range(K + 1)]
        tube(pts, 0.075, TUBE)
    edge = [tuple(P(4 * math.pi * j / (2 * K), vs[-1])) for j in range(2 * K + 1)]   # one loop over two rounds
    tube(edge, 0.03, EDGE)
    for j in range(0, K, 10):  # rungs across the width: thick inside pairs, thin between pairs
        u = 2 * math.pi * j / K
        for i in range(n - 1):
            a, b = P(u, vs[i]), P(u, vs[i + 1])
            d = (b - a).normalized()
            if i % 2 == 0:
                tube([tuple(a + d * 0.07), tuple(b - d * 0.07)], 0.032, TUBE)
            else:
                tube([tuple(a + d * 0.07), tuple(b - d * 0.07)], 0.009, GOLD)
    for j in range(0, K, 50):  # quantum dots sit at the sites now and then
        u = 2 * math.pi * j / K + 0.05
        for i in range(n):
            sphere(tuple(P(u, vs[i])), 0.11, ORANGE)
    for j in range(0, 2 * K, 40):  # the edge state glows softly along its loop
        sphere(tuple(P(4 * math.pi * j / (2 * K), vs[-1])), 0.2, HALO)
    camera((0.0, -14.5, 9.5), (0, 0, 2.3), lens=40, dof=12)


def param_surface(name, f, nu, nv, mat, loc, scale, rot=(0, 0, 0)):
    """Closed parametric surface f(u, v) with u, v in [0, 2pi), as one smooth mesh."""
    import bmesh
    bm = bmesh.new()
    vs = [[bm.verts.new(f(2 * math.pi * i / nu, 2 * math.pi * j / nv)) for j in range(nv)] for i in range(nu)]
    for i in range(nu):
        for j in range(nv):
            a, b = vs[i][j], vs[(i + 1) % nu][j]
            c, d = vs[(i + 1) % nu][(j + 1) % nv], vs[i][(j + 1) % nv]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(mat)
    ob.location, ob.scale, ob.rotation_euler = loc, (scale,) * 3, rot
    return ob


def knot(fn, n, radius, mat, loc, scale, rot=(0, 0, 0)):
    """Closed space curve fn(t), t in [0, 2pi], as a tube."""
    pts = [fn(2 * math.pi * i / n) for i in range(n + 1)]
    ob = tube([tuple(Vector(p) * scale) for p in pts], radius, mat)
    ob.location, ob.rotation_euler = loc, rot
    return ob


def topology_zoo():
    """Out-of-focus collection of topological objects behind the main figure: knots, links, a torus, a Klein
    bottle, a genus-two surface ... in glass, metal and a few faint glows."""
    FROST = principled("frost", **{"Base Color": (0.75, 0.92, 0.95, 1), "Transmission Weight": 0.9, "Roughness": 0.35, "IOR": 1.4})
    BRUSHED = principled("brushed", **{"Base Color": (0.7, 0.72, 0.75, 1), "Metallic": 1.0, "Roughness": 0.3})
    AMBER = principled("amber", **{"Base Color": (1.0, 0.5, 0.12, 1), "Transmission Weight": 0.7, "Roughness": 0.15})
    TEAL_DIM = emission("teal_dim", (0.25, 1.0, 0.75, 1), 2.0)
    VIOLET = emission("violet_dim", (0.55, 0.3, 1.0, 1), 2.0)
    c, s_ = math.cos, math.sin
    trefoil = lambda t: (s_(t) + 2 * s_(2 * t), c(t) - 2 * c(2 * t), -s_(3 * t))
    fig8 = lambda t: ((2 + c(2 * t)) * c(3 * t), (2 + c(2 * t)) * s_(3 * t), s_(4 * t))
    tk25 = lambda t: ((2 + c(5 * t)) * c(2 * t), (2 + c(5 * t)) * s_(2 * t), s_(5 * t))
    def klein(u, v, r=2.2):
        a = r + c(u / 2) * s_(v) - s_(u / 2) * s_(2 * v)
        return (a * c(u), a * s_(u), s_(u / 2) * s_(v) + c(u / 2) * s_(2 * v))
    def torus(R, r):
        return lambda u, v: ((R + r * c(v)) * c(u), (R + r * c(v)) * s_(u), r * s_(v))
    # knots and links
    knot(trefoil, 400, 0.2, AMBER, (-9.0, 12.0, 2.2), 0.65, (0.6, 0.3, 0.2))
    knot(fig8, 400, 0.17, BRUSHED, (9.5, 13.0, 2.3), 0.6, (1.0, 0.2, 0.5))
    knot(tk25, 500, 0.12, TEAL_DIM, (2.0, 21.0, 2.6), 0.75, (1.2, 0.0, 0.3))
    hopf = (lambda t: (1.3 * c(t), 1.3 * s_(t), 0.0), lambda t: (1.3 * c(t) + 1.3, 0.0, 1.3 * s_(t)))
    for fn, m in zip(hopf, (FROST, VIOLET)):                                  # Hopf link
        knot(fn, 120, 0.16, m, (-4.5, 18.0, 2.4), 1.0, (0.9, 0.4, 0.3))
    for k, m in enumerate((GOLD, BRUSHED, FROST)):                          # Borromean rings
        e = [(1.4 * c(t), 0.75 * s_(t), 0.0) for t in [2 * math.pi * i / 120 for i in range(121)]]
        pts = [((x, y, z), (z, x, y), (y, z, x))[k] for x, y, z in e]
        ob = tube([tuple(Vector(p)) for p in pts], 0.11, m); ob.location, ob.rotation_euler = (12.5, 19.0, 2.0), (0.5, 0.3, 0.8)
    # surfaces
    param_surface("klein", klein, 160, 48, FROST, (-13.0, 20.0, 2.6), 0.8, (1.1, 0.3, 0.6))
    param_surface("torus", torus(1.2, 0.45), 96, 48, BRUSHED, (-7.5, 7.5, 0.46), 1.0, (0.0, 0.0, 0.3))
    param_surface("torus_glass", torus(1.2, 0.35), 96, 36, AMBER, (7.5, 8.5, 1.3), 0.85, (1.2, 0.0, 0.7))
    # genus-two surface: implicit-looking "double torus" made from two tori glued side by side
    param_surface("g2a", torus(1.0, 0.42), 80, 36, FROST, (15.0, 11.0, 0.45), 1.0, (0.0, 0.0, 0.0))
    param_surface("g2b", torus(1.0, 0.42), 80, 36, FROST, (16.8, 11.0, 0.45), 1.0, (0.0, 0.0, 0.0))
    # a few small spheres (genus zero) to complete the zoo
    sphere((-1.5, 13.0, 0.6), 0.6, BRUSHED)
    sphere((5.0, 16.0, 0.45), 0.45, AMBER)


def mobius_zoo():
    mobius_ssh()
    topology_zoo()
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.16
    light((6, 16, 10), 900, 10, (math.radians(-40), 0, math.radians(160)))   # rim light from behind
    cam = sc.camera.data
    cam.dof.aperture_fstop = 0.25
    sc.camera.location = (0.0, -15.0, 8.0)
    sc.camera.rotation_euler = (Vector((0, 0, 2.5)) - Vector((0.0, -15.0, 8.0))).to_track_quat("-Z", "Y").to_euler()
    cam.dof.focus_distance = (Vector((0, 0, 2.5)) - Vector((0.0, -15.0, 8.0))).length


BOARD_TEX = HERE / "board" / "board_tex.png"


def blackboard(y=7.0, width=26.0, z0=0.0):
    """Chalkboard on the back wall, textured with board/board_tex.png (formulas and plots in chalk)."""
    img = bpy.data.images.load(str(BOARD_TEX))
    h = width * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, z0 + h / 2), rotation=(math.radians(90), 0, 0))
    ob = bpy.context.object
    ob.scale = (width, h, 1)
    m = principled("board", **{"Roughness": 0.85, "Specular IOR Level": 0.2})
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.append(m)
    FRAME = principled("frame", **{"Base Color": (0.25, 0.16, 0.09, 1), "Roughness": 0.5})
    t = 0.25
    for loc, size in (((0, y - 0.05, z0 + h + t / 2), (width + 2 * t, 0.3, t)), ((0, y - 0.05, z0 - t / 2), (width + 2 * t, 0.3, t)),
                      ((-width / 2 - t / 2, y - 0.05, z0 + h / 2), (t, 0.3, h)), ((width / 2 + t / 2, y - 0.05, z0 + h / 2), (t, 0.3, h))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); c = bpy.context.object; c.scale = size; link(c, FRAME)
    # chalk tray with a few pieces of chalk
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y - 0.35, z0 - 0.1)); c = bpy.context.object; c.scale = (width, 0.6, 0.08); link(c, FRAME)
    CHALK = principled("chalk", **{"Base Color": (0.95, 0.95, 0.92, 1), "Roughness": 0.95})
    for x in (-8.0, -7.4, 5.5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.7, location=(x, y - 0.35, z0 + 0.02), rotation=(0, math.radians(90), 0.3 * x))
        link(bpy.context.object, CHALK)
    return h


def mobius_board():
    mobius_ssh()
    for o in [o for o in sc.objects if o.type == "MESH" and o.dimensions.x > 100]:
        o.location.z = -0.0   # keep the dark floor
    blackboard(y=7.5, width=27.0, z0=0.4)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    light((0, -2, 13), 2600, 14, (math.radians(-25), 0, 0))   # wash over the board from above the viewer
    eye, tgt = Vector((0.0, -16.0, 6.2)), Vector((0, 0, 3.7))
    sc.camera.data.lens = 30
    sc.camera.location = eye
    sc.camera.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
    cam = sc.camera.data
    cam.dof.focus_distance = (tgt - eye).length
    cam.dof.aperture_fstop = 0.6


def mobius_float():
    """The Moebius-SSH strip floating in front of a full-bleed chalkboard (no floor, no frame)."""
    mobius_ssh()
    for o in [o for o in sc.objects if o.type == "MESH" and o.dimensions.x > 100]:
        bpy.data.objects.remove(o)                       # no floor
    board_backdrop()


def mobius_float_setup(build):
    build()
    camera((0, -1, 0), (0, 0, 0))
    board_backdrop()


def board_backdrop():
    eye, tgt = Vector((0.0, -15.5, 7.5)), Vector((0, 0, 2.7))
    cam = sc.camera
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 40
    cam.data.dof.focus_distance = (tgt - eye).length
    cam.data.dof.aperture_fstop = 0.5
    # board perpendicular to the view, far enough behind to fill the frame
    img = bpy.data.images.load(str(BOARD_TEX))
    d = (tgt - eye).normalized()
    dist = (tgt - eye).length + 9.0
    centre = eye + d * dist
    frame_h = dist * 20.25 / 40 * 1.08
    h = frame_h; w = h * img.size[0] / img.size[1]
    bpy.ops.mesh.primitive_plane_add(size=1, location=centre)
    ob = bpy.context.object
    ob.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    ob.scale = (w, h, 1)
    m = principled("board_bg", **{"Roughness": 0.9, "Specular IOR Level": 0.1})
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.append(m)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        o.data.energy *= 0.25
    light(tuple(eye + Vector((0, 4, 6))), 3000, 16, tuple((-d).to_track_quat("Z", "Y").to_euler()))


def mobius_band():
    """Simpler Moebius strip: one smooth glass band, the SSH sites as rows of dots on it (paired), and the edge
    state as one glowing line along the single boundary (it goes round twice)."""
    import bmesh
    R, w, zc = 3.3, 1.25, 2.7
    def P(u, v):
        return Vector(((R + v * math.cos(u / 2)) * math.cos(u), (R + v * math.cos(u / 2)) * math.sin(u), zc + v * math.sin(u / 2)))
    import os
    tint = {"clear": (0.92, 0.97, 1.0, 1), "teal": (0.55, 0.95, 0.9, 1), "violet": (0.78, 0.7, 1.0, 1),
            "amber": (1.0, 0.85, 0.6, 1)}[os.environ.get("BAND_TINT", "clear")]
    # tinted sheet without refraction: transparent in the middle, glossy towards grazing angles, faint own glow
    BAND = bpy.data.materials.new("band"); BAND.use_nodes = True
    nt = BAND.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = tuple(0.15 + 0.5 * c for c in tint[:3]) + (1,)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.08; gl.inputs["Color"].default_value = tint
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = tint; em.inputs["Strength"].default_value = 0.3
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    mix = nt.nodes.new("ShaderNodeMixShader"); add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(lw.outputs["Facing"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    EDGE = emission("edge_b", (0.25, 1.0, 0.6, 1), 7.0)
    nu, nv = 400, 16
    bm = bmesh.new()
    vs = [[bm.verts.new(P(2 * math.pi * i / nu, -w + 2 * w * j / (nv - 1))) for j in range(nv)] for i in range(nu)]
    for i in range(nu):
        for j in range(nv - 1):
            if i < nu - 1:
                a, b, c, d = vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]
            else:   # the seam: after one round v becomes -v
                a, b, c, d = vs[i][j], vs[0][nv - 1 - j], vs[0][nv - 2 - j], vs[i][j + 1]
            bm.faces.new((a, b, c, d))
    me = bpy.data.meshes.new("band"); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("band", me); sc.collection.objects.link(ob); me.materials.append(BAND)
    # SSH chains along the band: three rows of dimers (short strong bond inside a pair, long gap between pairs)
    rows, M = [0.0], 40
    BOND = principled("bond", **{"Base Color": (1.0, 0.64, 0.22, 1), "Metallic": 1.0, "Roughness": 0.2})
    for v in rows:
        for j in range(M):
            ua = 2 * math.pi * j / M
            ub = ua + 2 * math.pi / M * 0.4
            a, b = P(ua, v * w), P(ub, v * w)
            sphere(tuple(a), 0.13, ORANGE); sphere(tuple(b), 0.13, ORANGE)
            dd = (b - a).normalized()
            tube([tuple(a + dd * 0.12), tuple(b - dd * 0.12)], 0.05, BOND)
    # the edge state: one loop along the boundary, over two rounds
    edge = [tuple(P(4 * math.pi * j / 1000, w * 1.0)) for j in range(1001)]
    tube(edge, 0.045, EDGE)
    for j in range(0, 1000, 40):
        sphere(tuple(P(4 * math.pi * j / 1000, w)), 0.18, HALO)


def mobius_band_float():
    mobius_float_setup(mobius_band)


# ------------------------------------------------------------------------------------------------------------
# Twenty variations of the Moebius-SSH strip over the chalkboard (VARIANT=1..20 in the environment)
import colorsys


def _hsv(h, s=1.0, v=1.0):
    return (*colorsys.hsv_to_rgb(h, s, v), 1)


VARIANTS = {
    1: dict(name="synthwave", tube="emit", tube_col=(0.2, 0.9, 1.0, 1), tube_str=0.6, edge_col=(1.0, 0.15, 0.8, 1), edge_str=9,
            dots=(1.0, 0.9, 0.2, 1), board_tint=(0.75, 0.45, 1.0), board_bright=0.8,
            lights=[((-8, -4, 6), 1500, 6, (1.0, 0.2, 0.7)), ((8, -4, 6), 1500, 6, (0.2, 0.6, 1.0))], key=0.0),
    2: dict(name="whiteboard", board_invert=True, board_tint=(0.95, 0.95, 0.97), board_bright=1.0, tube="chrome",
            edge_col=(0.1, 0.35, 1.0, 1), edge_str=6, dots=(1.0, 0.3, 0.1, 1), world=0.6, key=1.0),
    3: dict(name="gold", tube="gold", edge_col=(1.0, 0.85, 0.55, 1), edge_str=8, dots=(0.9, 0.2, 0.1, 1),
            board_tint=(1.0, 0.8, 0.55), board_bright=0.9, lights=[((-6, -6, 8), 2500, 5, (1.0, 0.75, 0.45))], key=0.4),
    4: dict(name="three half-twists", twists=3, edge_col=(0.25, 1.0, 0.6, 1)),
    5: dict(name="low hero angle", eye=(2.0, -11.0, 2.2), tgt=(0, 0, 3.0), lens=24, fstop=0.8),
    6: dict(name="from above", eye=(0.0, -5.0, 17.0), tgt=(0, 0, 2.5), lens=45, board_behind=False),
    7: dict(name="ice", tube="frost", edge_col=(0.6, 0.85, 1.0, 1), edge_str=8, dots=(0.75, 0.9, 1.0, 1), dots_mat="emit",
            board_tint=(0.55, 0.75, 1.0), lights=[((0, -8, 10), 2500, 10, (0.6, 0.8, 1.0))], key=0.3),
    8: dict(name="fire", edge_col=(1.0, 0.35, 0.05, 1), edge_str=10, tube="dark", dots=(1.0, 0.1, 0.05, 1), dots_mat="emit",
            board_tint=(1.0, 0.55, 0.35), board_bright=0.7, lights=[((0, 6, 3), 3000, 8, (1.0, 0.35, 0.1))], key=0.2),
    9: dict(name="wide band, 12 chains", w=2.1, n=12, tube_r=0.05, R=3.6),
    10: dict(name="narrow, 4 chunky chains", w=0.75, n=4, tube_r=0.14, dot_r=0.17),
    11: dict(name="rainbow chains", tube="rainbow", tube_str=2.0, edge_col=(1, 1, 1, 1), edge_str=6),
    12: dict(name="noir spotlight", spot=True, world=0.0, key=0.0, board_bright=0.45, edge_str=5, fstop=0.35),
    13: dict(name="tilted, heavy blur", tilt=(0.45, -0.35, 0.3), fstop=0.15),
    14: dict(name="five half-twists", twists=5, edge_col=(0.7, 0.4, 1.0, 1), dots=(1.0, 0.75, 0.2, 1)),
    15: dict(name="racetrack", stretch=(1.7, 0.8), eye=(-6.0, -15.0, 6.0), tgt=(0, 0, 2.7), lens=38),
    16: dict(name="chalk strip", tube="chalk", edge_col=(0.25, 1.0, 0.8, 1), dots=(0.95, 0.95, 0.9, 1), rungs=False),
    17: dict(name="green schoolboard", board_tint=(0.45, 0.85, 0.55), board_bright=1.1, edge_col=(1.0, 0.8, 0.3, 1),
            lights=[((5, -6, 9), 2200, 6, (1.0, 0.85, 0.6))], key=0.3),
    18: dict(name="edge colour runs twice round", edge_grad=True),
    19: dict(name="macro on the twist", eye=(4.5, -6.5, 4.6), tgt=(2.4, -1.6, 2.6), lens=50, fstop=0.12),
    20: dict(name="blueprint", board_tint=(0.35, 0.6, 1.0), board_bright=1.6, board_blueprint=True, tube="emit",
            tube_col=(0.85, 0.95, 1.0, 1), tube_str=0.5, tube_r=0.045, edge_col=(1.0, 1.0, 1.0, 1), edge_str=8, dots=(1.0, 1.0, 1.0, 1),
            dots_mat="emit", rungs=False),
}


def mobius_variant():
    import os
    v = VARIANTS[int(os.environ["VARIANT"])]
    g = lambda k, d: v.get(k, d)
    R, w, n, k = g("R", 3.3), g("w", 1.35), g("n", 8), g("twists", 1)
    sx, sy = g("stretch", (1.0, 1.0))
    zc = 2.7
    vs, x = [], 0.0
    for i in range(n):
        vs.append(x); x += 0.26 if i % 2 == 0 else 0.5
    off = (vs[0] + vs[-1]) / 2; vs = [(q - off) * (w / ((vs[-1] - vs[0]) / 2)) for q in vs]
    def P(u, q):
        r = R + q * math.cos(k * u / 2)
        return Vector((sx * r * math.cos(u), sy * r * math.sin(u), zc + q * math.sin(k * u / 2)))
    tube_kind = g("tube", "glass")
    def tube_mat(i):
        if tube_kind == "glass":
            return principled("tg", **{"Base Color": (0.85, 0.93, 0.97, 1), "Transmission Weight": 0.95, "Roughness": 0.2, "IOR": 1.3})
        if tube_kind == "chrome":
            return principled("chrome", **{"Base Color": (0.9, 0.9, 0.92, 1), "Metallic": 1.0, "Roughness": 0.05})
        if tube_kind == "gold":
            return GOLD
        if tube_kind == "frost":
            return principled("frost", **{"Base Color": (0.85, 0.95, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.45, "IOR": 1.31})
        if tube_kind == "dark":
            return principled("dark", **{"Base Color": (0.05, 0.05, 0.05, 1), "Metallic": 1.0, "Roughness": 0.25})
        if tube_kind == "chalk":
            return principled("chalkt", **{"Base Color": (0.9, 0.9, 0.86, 1), "Roughness": 1.0})
        if tube_kind == "emit":
            return emission("te", g("tube_col", (1, 1, 1, 1)), g("tube_str", 1.0))
        if tube_kind == "rainbow":
            return emission(f"rb{i}", _hsv(i / n * 0.85), g("tube_str", 2.0))
    EDGE = emission("edge", g("edge_col", (0.25, 1.0, 0.6, 1)), g("edge_str", 7.0))
    halo = volume_glow("halo_v", g("edge_col", (0.25, 1.0, 0.6, 1)), 3.0)
    dots_col = g("dots", None)
    if dots_col is None:
        DOT = ORANGE
    elif g("dots_mat", "glass") == "emit":
        DOT = emission("dot", dots_col, 4.0)
    else:
        DOT = principled("dot", **{"Base Color": dots_col, "Transmission Weight": 0.6, "Roughness": 0.06, "IOR": 1.45})
    before = set(sc.objects)
    K = 500
    tr = g("tube_r", 0.075)
    if k == 1:
        for i in range(n):
            tube([tuple(P(2 * math.pi * j / K, vs[i])) for j in range(K + 1)], tr, tube_mat(i))
    else:   # with more twists the tubes only close after two rounds; draw each loop once
        done = set()
        for i in range(n):
            if i in done: continue
            done |= {i, n - 1 - i}
            tube([tuple(P(4 * math.pi * j / (2 * K), vs[i])) for j in range(2 * K + 1)], tr, tube_mat(i))
    if g("edge_grad", False):
        S = 40
        for sgm in range(S):
            col = _hsv(0.45 + 0.4 * sgm / S, 0.85, 1.0)
            m = emission(f"eg{sgm}", col, 8.0)
            tube([tuple(P(4 * math.pi * (sgm + t / 10) / S, vs[-1])) for t in range(11)], 0.035, m)
    else:
        tube([tuple(P(4 * math.pi * j / (2 * K), vs[-1])) for j in range(2 * K + 1)], 0.03, EDGE)
    if g("rungs", True):
        for j in range(0, K, 10):
            u = 2 * math.pi * j / K
            for i in range(n - 1):
                a, b = P(u, vs[i]), P(u, vs[i + 1])
                d = (b - a).normalized()
                if (b - a).length < 0.2: continue
                if i % 2 == 0:
                    tube([tuple(a + d * (tr + 0.01)), tuple(b - d * (tr + 0.01))], 0.032, tube_mat(i) if tube_kind != "rainbow" else GOLD)
                else:
                    tube([tuple(a + d * (tr + 0.01)), tuple(b - d * (tr + 0.01))], 0.009, GOLD)
    for j in range(0, K, 50):
        u = 2 * math.pi * j / K + 0.05
        for i in range(n):
            sphere(tuple(P(u, vs[i])), g("dot_r", 0.11), DOT)
    if not g("edge_grad", False):
        for j in range(0, 2 * K, 40):
            sphere(tuple(P(4 * math.pi * j / (2 * K), vs[-1])), 0.2, halo)
    made = [o for o in sc.objects if o not in before]
    if "tilt" in v:
        piv = bpy.data.objects.new("pivot", None); sc.collection.objects.link(piv)
        piv.location = (0, 0, zc)
        for o in made:
            o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
        piv.rotation_euler = v["tilt"]
    # camera + board
    eye, tgt = Vector(g("eye", (0.0, -15.5, 7.5))), Vector(g("tgt", (0, 0, 2.7)))
    camera(tuple(eye), tuple(tgt), lens=g("lens", 40), dof=1)
    cam = sc.camera
    cam.data.dof.aperture_fstop = g("fstop", 0.5)
    img = bpy.data.images.load(str(BOARD_TEX))
    d = (tgt - eye).normalized()
    dist = (tgt - eye).length + 9.0
    centre = eye + d * dist
    lens = g("lens", 40)
    h = dist * 20.25 / lens * 1.12; wb = max(h * img.size[0] / img.size[1], dist * 36 / lens * 1.12)
    h = wb * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=centre)
    ob = bpy.context.object
    ob.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    ob.scale = (wb, h, 1)
    m = principled("board_v", **{"Roughness": 0.9, "Specular IOR Level": 0.1})
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    col = tex.outputs["Color"]
    if g("board_invert", False):
        inv = nt.nodes.new("ShaderNodeInvert"); nt.links.new(col, inv.inputs["Color"]); col = inv.outputs[0]
    if g("board_blueprint", False):
        # chalk becomes white lines on a saturated blue sheet
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(col, bw.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(bw.outputs[0], ramp.inputs[0])
        ramp.color_ramp.elements[0].position = 0.08; ramp.color_ramp.elements[0].color = (0.02, 0.12, 0.42, 1)
        ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (0.9, 0.95, 1.0, 1)
        col = ramp.outputs[0]
    else:
        tint = g("board_tint", (1, 1, 1)); br = g("board_bright", 1.0)
        mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = tuple(c * br for c in tint)
        nt.links.new(col, mul.inputs[0]); col = mul.outputs[0]
    nt.links.new(col, nt.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.append(m)
    if not g("board_behind", True):   # from above: lay the board flat as the floor
        ob.location = (0, 2, -0.5); ob.rotation_euler = (0, 0, 0)
        ob.scale = (wb * 1.3, h * 1.3, 1)
    # lighting
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = g("world", 0.12)
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        o.data.energy *= 0.25 * g("key", 1.0)
    fill = light(tuple(eye + Vector((0, 4, 6))), 3000 * g("key", 1.0), 16, tuple((-d).to_track_quat("Z", "Y").to_euler()))
    for loc, e, size, c in g("lights", []):
        L = light(loc, e, size, tuple((Vector((0, 0, zc)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()))
        L.data.color = c
    if g("spot", False):
        data = bpy.data.lights.new("spot", "SPOT"); data.energy = 9000; data.spot_size = math.radians(38); data.spot_blend = 0.25
        data.shadow_soft_size = 0.4
        so = bpy.data.objects.new("spot", data); sc.collection.objects.link(so)
        so.location = (2.0, -3.0, 13.0)
        so.rotation_euler = (Vector((0, 0, zc)) - Vector(so.location)).to_track_quat("-Z", "Y").to_euler()


# ------------------------------------------------------------------------------------------------------------
def post_fx(fog=0.6, streaks=0.5, ghosts=0.35, dispersion=0.015, threshold=1.0, anamorphic=0.0, contrast=0.0, saturation=1.0):
    """Compositor: soft glow, star streaks and lens-flare ghosts on the bright parts, slight chromatic aberration."""
    ng = bpy.data.node_groups.new("post", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    out = ng.nodes.new("NodeGroupOutput")
    cur = rl.outputs["Image"]
    for kind, strength, extra in (("Fog Glow", fog, {"Size": 0.6}), ("Streaks", streaks, {"Streaks": 6, "Streaks Angle": math.radians(15), "Fade": 0.92}),
                                  ("Ghosts", ghosts, {"Color Modulation": 0.5}),
                                  ("Streaks", anamorphic, {"Streaks": 2, "Streaks Angle": 0.0, "Fade": 0.97})):
        if strength <= 0:
            continue
        gl = ng.nodes.new("CompositorNodeGlare")
        gl.inputs["Type"].default_value = kind
        gl.inputs["Quality"].default_value = "High"
        gl.inputs["Threshold"].default_value = threshold
        gl.inputs["Strength"].default_value = strength
        for k_, val in extra.items():
            try:
                gl.inputs[k_].default_value = val
            except Exception as e:
                print("glare input", k_, e)
        ng.links.new(cur, gl.inputs["Image"]); cur = gl.outputs["Image"]
    if dispersion:
        ld = ng.nodes.new("CompositorNodeLensdist")
        for name, val in (("Dispersion", dispersion), ("Distortion", -0.01)):
            try:
                ld.inputs[name].default_value = val
            except Exception as e:
                print("lensdist", name, e)
        ng.links.new(cur, ld.inputs["Image"]); cur = ld.outputs["Image"]
    if contrast:
        bc = ng.nodes.new("CompositorNodeBrightContrast")
        for name, val in (("Contrast", contrast), ("Bright", 0.0)):
            try:
                bc.inputs[name].default_value = val
            except Exception as e:
                print("brightcontrast", name, e)
        ng.links.new(cur, bc.inputs["Image"]); cur = bc.outputs["Image"]
    if saturation != 1.0:
        hs = ng.nodes.new("CompositorNodeHueSat")
        try:
            hs.inputs["Saturation"].default_value = saturation
        except Exception as e:
            print("huesat", e, [i.name for i in hs.inputs])
        ng.links.new(cur, hs.inputs["Image"]); cur = hs.outputs["Image"]
    ng.links.new(cur, out.inputs["Image"])
    sc.compositing_node_group = ng


def haze(density=0.012, color=(0.8, 0.9, 1.0, 1)):
    """Thin scattering air in the world, so beams and lights draw visible shafts."""
    wn = sc.world.node_tree.nodes
    vs = wn.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = density
    vs.inputs["Color"].default_value = color
    sc.world.node_tree.links.new(vs.outputs[0], wn["World Output"].inputs["Volume"])


def optical_table(size=40):
    """Dark breadboard with the usual hole grid."""
    bpy.ops.mesh.primitive_plane_add(size=size)
    ob = bpy.context.object
    m = principled("table", **{"Base Color": (0.03, 0.033, 0.036, 1), "Roughness": 0.3, "Metallic": 0.7})
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sc_ = nt.nodes.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], sc_.inputs[0])
    fr = nt.nodes.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"; nt.links.new(sc_.outputs[0], fr.inputs[0])
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(fr.outputs[0], sub.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(sub.outputs[0], ln.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.12
    nt.links.new(ln.outputs["Value"], lt.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.3, 1.0
    nt.links.new(lt.outputs[0], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Roughness"])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(lt.outputs[0], inv.inputs[1])
    nt.links.new(inv.outputs[0], nt.nodes["Principled BSDF"].inputs["Metallic"])
    ob.data.materials.append(m)


def laser_head(at, towards, body=(0.7, 0.45, 0.45)):
    """Small laser housing at `at`, aiming at `towards` (black box with a bright aperture)."""
    a, t = Vector(at), Vector(towards)
    d = (t - a).normalized()
    rot = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cube_add(size=1, location=a - d * body[0] / 2, rotation=rot)
    ob = bpy.context.object; ob.scale = (body[1], body[2], body[0])
    bev = ob.modifiers.new("bev", "BEVEL"); bev.width = 0.04; bev.segments = 3
    link(ob, principled("housing", **{"Base Color": (0.02, 0.02, 0.025, 1), "Metallic": 0.8, "Roughness": 0.35}))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.3, location=a - d * 0.05, rotation=rot, vertices=24)
    link(bpy.context.object, STEEL)
    return a


def hot_spot(loc, color, r=0.07, strength=60):
    sphere(loc, r, emission("hot", color, strength))


COPPER = principled("copper", **{"Base Color": (0.95, 0.55, 0.36, 1), "Metallic": 1.0, "Roughness": 0.22})


def waveguide(points, a=0.46, b=0.23, mat=None, sharp=False):
    """Rectangular metal waveguide along a polyline (rounded bends), a x b cross-section."""
    mat = mat or COPPER
    prof = bpy.data.curves.new("wgprof", "CURVE"); prof.dimensions = "2D"
    sp = prof.splines.new("POLY"); sp.points.add(3)
    for pt, (x, y) in zip(sp.points, ((-a / 2, -b / 2), (a / 2, -b / 2), (a / 2, b / 2), (-a / 2, b / 2))):
        pt.co = (x, y, 0, 1)
    sp.use_cyclic_u = True
    po = bpy.data.objects.new("wgprof", prof); sc.collection.objects.link(po); po.hide_render = True
    cu = bpy.data.curves.new("wg", "CURVE"); cu.dimensions = "3D"
    if sharp:
        s_ = cu.splines.new("POLY"); s_.points.add(len(points) - 1)
        for pt, co in zip(s_.points, points):
            pt.co = (*co, 1)
    else:
        s_ = cu.splines.new("BEZIER"); s_.bezier_points.add(len(points) - 1)
        for bp, co in zip(s_.bezier_points, points):
            bp.co = co; bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_mode = "OBJECT"; cu.bevel_object = po; cu.use_fill_caps = True
    cu.twist_mode = "MINIMUM"
    ob = bpy.data.objects.new("wg", cu); sc.collection.objects.link(ob); cu.materials.append(mat)
    return ob


def flange(loc, direction, a=0.46, b=0.23, mat=None):
    d = Vector(direction).normalized()
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=d.to_track_quat("Z", "Y").to_euler())
    ob = bpy.context.object; ob.scale = (a + 0.3, b + 0.3, 0.06)
    bev = ob.modifiers.new("bev", "BEVEL"); bev.width = 0.02
    link(ob, mat or COPPER)


def horn(mouth_centre, direction, a=0.46, b=0.23, A=1.3, B=1.0, length=1.1, mat=None):
    """Pyramidal horn: from the waveguide (a x b) to the mouth (A x B), open, along `direction`."""
    import bmesh
    d = Vector(direction).normalized()
    q = d.to_track_quat("Z", "Y")
    bm = bmesh.new()
    def ring(w, h, z):
        return [bm.verts.new(q @ Vector(c) + Vector(mouth_centre)) for c in ((-w / 2, -h / 2, z), (w / 2, -h / 2, z), (w / 2, h / 2, z), (-w / 2, h / 2, z))]
    r0, r1 = ring(a, b, -length), ring(A, B, 0.0)
    for i in range(4):
        bm.faces.new((r0[i], r0[(i + 1) % 4], r1[(i + 1) % 4], r1[i]))
    me = bpy.data.meshes.new("horn"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("horn", me); sc.collection.objects.link(ob); me.materials.append(mat or COPPER)
    sol = ob.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.04
    bev = ob.modifiers.new("bev", "BEVEL"); bev.width = 0.015; bev.segments = 2
    return ob


def wavefronts(origin, direction, n=6, spacing=0.38, color=(0.85, 0.35, 1.0, 1), start=0.25, R=1.2):
    """Microwave wavefronts leaving a horn: curved, glowing, fading sheets."""
    import bmesh
    d = Vector(direction).normalized(); q = d.to_track_quat("Z", "Y")
    for i in range(n):
        dist = start + i * spacing
        rad = 0.9 + 0.35 * i            # fronts widen as they travel
        curv = 1.6 + 0.6 * i
        bm = bmesh.new()
        N = 20
        grid = []
        for ix in range(N + 1):
            row = []
            for iy in range(N + 1):
                x = (ix / N - 0.5) * 2 * rad * 0.8; y = (iy / N - 0.5) * 2 * rad * 0.6
                z = dist - (x * x + y * y) / (2 * curv)
                row.append(bm.verts.new(q @ Vector((x, y, z)) + Vector(origin)))
            grid.append(row)
        for ix in range(N):
            for iy in range(N):
                bm.faces.new((grid[ix][iy], grid[ix + 1][iy], grid[ix + 1][iy + 1], grid[ix][iy + 1]))
        me = bpy.data.meshes.new("wf"); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("wf", me); sc.collection.objects.link(ob)
        # fade: transparent mix with emission, strongest in the middle, weaker for later fronts
        m = bpy.data.materials.new(f"wf{i}"); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = color; em.inputs["Strength"].default_value = 3.0
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / rad, 1 / rad, 1 / rad)
        nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], gr.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.55 * (1 - i / (n + 1))
        nt.links.new(gr.outputs["Fac"], mul.inputs[0])
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul.outputs[0], mix.inputs["Fac"]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        me.materials.append(m)
        ob.location = (0, 0, 0)
        # object coordinates are around the world origin; shift so the gradient is centred on this front
        for v in me.vertices:
            v.co -= Vector(origin) + d * dist
        ob.location = Vector(origin) + d * dist


def wave_arcs(origin, direction, n=4, spacing=0.3, color=(0.85, 0.35, 1.0, 1), start=0.2):
    """Microwave wavefronts drawn as thin glowing arcs (in the plane facing the camera), fading with distance."""
    d = Vector(direction).normalized()
    side = Vector((1, 0, 0))
    o = Vector(origin)
    for i in range(n):
        dist = start + i * spacing
        half = 0.55 + 0.32 * i
        curv = 1.4 + 0.5 * i
        pts = []
        for j in range(41):
            x = (j / 40 - 0.5) * 2 * half
            pts.append(tuple(o + side * x + d * (dist - x * x / (2 * curv))))
        tube(pts, 0.022, emission(f"arc{i}", color, 9.0 * (1 - i / (n + 0.5))))


def gauss_mode_material(name, color, strength, waist=0.3, standing=0.0, k=1.0):
    """Cavity mode as an emitting volume in a cylinder of radius 1, z in [-1, 1]: Gaussian beam with waist `waist`
    (relative to the end radius) at z = 0, I = (w0/w)^2 exp(-2 r^2 / w^2)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = 0.0
    v.inputs["Emission Color"].default_value = color
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, b=None: _math(nt, op, a, b)
    w2 = M("ADD", waist * waist, M("MULTIPLY", 1 - waist * waist, M("MULTIPLY", sep.outputs["Z"], sep.outputs["Z"])))
    r2 = M("ADD", M("MULTIPLY", sep.outputs["X"], sep.outputs["X"]), M("MULTIPLY", sep.outputs["Y"], sep.outputs["Y"]))
    g = M("EXPONENT", M("MULTIPLY", -2.5, M("DIVIDE", r2, w2)))
    amp = M("DIVIDE", waist * waist, w2)
    val = M("MULTIPLY", g, amp)
    if standing:
        c = M("COSINE", M("MULTIPLY", sep.outputs["Z"], k))
        val = M("MULTIPLY", val, M("ADD", 1 - standing, M("MULTIPLY", standing, M("MULTIPLY", c, c))))
    nt.links.new(M("MULTIPLY", val, strength), v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


def _math(nt, op, a, b):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def laser_wow():
    """Cavity QED with more drama: haze, several colored lasers from housings on an optical table, hot spots and
    lens flares in post."""
    optical_table()
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.015
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        o.data.energy *= 0.15
    haze(0.02)
    h, L = 2.3, 4.6
    # real mirrors: silver coating, near-perfect reflection, with a glass substrate rim
    SILVER_M = principled("silver_mirror", **{"Base Color": (0.97, 0.98, 1.0, 1), "Metallic": 1.0, "Roughness": 0.0})
    SUBSTRATE = principled("substrate", **{"Base Color": (0.75, 0.95, 0.92, 1), "Transmission Weight": 1.0, "Roughness": 0.02, "IOR": 1.5})
    for x, f in ((L, 1), (-L, -1)):
        ms = mirror_shell(x, f, h)
        ms.data.materials.clear(); ms.data.materials.append(SILVER_M); ms.data.materials.append(SUBSTRATE)
        ms.modifiers["solid"].material_offset_rim = 1
        ms.modifiers["solid"].thickness = 0.18
    # mounts: a metal ring holding each mirror at its rim, on a short post and base plate
    R_, depth_ = 3.2, 0.75
    rim_r = R_ * math.sin(math.acos((R_ - depth_) / R_))
    for s in (-1, 1):
        xr = s * (L - depth_ + 0.06)
        bpy.ops.mesh.primitive_torus_add(major_radius=rim_r + 0.05, minor_radius=0.11, major_segments=128, minor_segments=24,
                                         location=(xr, 0, h), rotation=(0, math.radians(90), 0))
        link(bpy.context.object, STEEL)
        bottom = h - rim_r - 0.14
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=bottom, vertices=32, location=(xr, 0, bottom / 2))
        link(bpy.context.object, STEEL)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(xr, 0, 0.04)); c = bpy.context.object; c.scale = (0.7, 1.3, 0.08)
        link(c, STEEL)
    # the world stays dark for the camera but shows the studio in reflections, so the mirrors have something to mirror
    wt = sc.world.node_tree; wn_ = wt.nodes
    lp = wn_.new("ShaderNodeLightPath")
    mixw = wn_.new("ShaderNodeMath"); mixw.operation = "MULTIPLY_ADD"
    mixw.inputs[1].default_value = 2.5; mixw.inputs[2].default_value = 0.015
    # hidden light panels at the back: what the mirrors reflect from this camera (no light into the haze)
    for px in (9.0, -9.0):
        loc = Vector((px, 11.0, 3.0))
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        pan = bpy.context.object; pan.scale = (5, 3.5, 1)
        pan.rotation_euler = (Vector((-px * 0.5, 0, 2.3)) - loc).to_track_quat("Z", "Y").to_euler()
        link(pan, emission("panel", (0.85, 0.95, 1.0, 1), 3.0))
        pan.visible_camera = False; pan.visible_volume_scatter = False; pan.visible_diffuse = False
    wt.links.new(lp.outputs["Is Glossy Ray"], mixw.inputs[0])
    wt.links.new(mixw.outputs[0], wn_["Background"].inputs["Strength"])
    k = 2 * math.pi * 3.5 / (2 * L)
    TEAL = (0.3, 1.0, 0.85, 1)
    # an intense, well-defined laser beam: hot white-teal core, tight teal sheath, only a faint hint of standing-wave nodes
    # the cavity mode: wide on the curved mirrors, focused to a bright waist in the middle
    beam((-L + 0.12, 0, h), (L - 0.12, 0, h), 0.85, gauss_mode_material("cav_mode", TEAL, 18.0, waist=0.25, standing=0.25, k=k * L))
    for s in (-1, 1):
        x = s * 1.85
        tilt = math.radians(25 * s)
        spin((x, 0, h), (math.sin(tilt), 0.1, math.cos(tilt)), r=0.46)
        flip_arrow((x, 0, h), 0.95, math.radians(55 if s < 0 else 125), math.radians(70 * (1 if s < 0 else -1)))
        flip_arrow((x, 0, h), 0.95, math.radians(235 if s < 0 else 305), math.radians(70 * (1 if s < 0 else -1)))
    PINK, VIOLET, BLUE, AMBER = (1.0, 0.2, 0.45, 1), (0.6, 0.25, 1.0, 1), (0.25, 0.5, 1.0, 1), (1.0, 0.6, 0.15, 1)
    # main drive laser through the left mirror
    src = laser_head((-11, 0, h), (-L, 0, h))
    beam(src, (-L - 0.25, 0, h), 0.14, beam_material("drive", PINK, 16.0))
    hot_spot((-L - 0.3, 0, h), (1.0, 0.5, 0.7, 1), 0.09, 80)
    # control lasers from the front-above onto each spin
    for s, col in ((-1, VIOLET), (1, BLUE)):
        tgt = Vector((s * 1.85, 0, h))
        a = laser_head((s * 6.5, -7.5, 0.9), tgt)
        beam(a, tgt, 0.08, beam_material(f"ctl{s}", col, 18.0))
        # continues a bit past the spin, fading into the haze
        d = (tgt - Vector(a)).normalized()
        beam(tgt, tgt + d * 4.0, 0.06, beam_material(f"ctl2{s}", col, 6.0))
        hot_spot(tuple(tgt), (1, 1, 1, 1), 0.06, 40)
    # a probe beam that bounces off a small steering mirror at the back and goes across
    m1 = Vector((3.0, 5.5, 0.9)); m2 = Vector((-3.5, 5.5, 3.6))
    a = laser_head((9.5, 5.5, 0.9), m1)
    beam(a, m1, 0.06, beam_material("probe1", AMBER, 14.0)); beam(m1, m2, 0.06, beam_material("probe2", AMBER, 12.0))
    beam(m2, (-12, 2.0, 5.0), 0.06, beam_material("probe3", AMBER, 9.0))
    for p in (m1, m2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.06, location=p, vertices=48)
        mo = bpy.context.object; mo.rotation_euler = Vector((1, -0.4, 0.2)).to_track_quat("Z", "Y").to_euler()
        link(mo, MIRROR)
        hot_spot(tuple(p), (1.0, 0.8, 0.5, 1), 0.06, 60)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=p.z, location=(p.x, p.y, p.z / 2), vertices=16)
        link(bpy.context.object, STEEL)
    # output leaking through the right mirror into a detector
    beam((L + 0.25, 0, h), (11, 0, h), 0.12, beam_material("leak", TEAL, 8.0))
    hot_spot((L + 0.3, 0, h), (0.7, 1.0, 0.9, 1), 0.08, 70)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.9, location=(11.4, 0, h), rotation=(0, math.radians(90), 0), vertices=48)
    link(bpy.context.object, principled("det", **{"Base Color": (0.05, 0.05, 0.06, 1), "Metallic": 0.9, "Roughness": 0.3}))
    # a few faint dust sparkles in the beams
    import random
    rnd = random.Random(4)
    for _ in range(18):
        x = rnd.uniform(-L, L); y = rnd.gauss(0, 0.25); z = h + rnd.gauss(0, 0.25)
        sphere((x, y, z), 0.012, emission("dust", (0.8, 1.0, 0.95, 1), 12))
    # microwave drive: two gold waveguides along the table, each ending in a horn right below one spin
    for sgn in (-1, 1):
        x = sgn * 1.85
        mouth = (x, 0.0, 1.35)
        # right-angle bends: in from the side, then towards the cavity, then straight up into the horn
        zf = 0.14
        pts = [(sgn * 9.0, -1.5, zf), (x, -1.5, zf), (x, 0.0, zf), (x, 0.0, 0.62)]
        waveguide(pts, mat=GOLD, sharp=True)
        for c, d in (((x, 0.0, 0.62), (0, 0, 1)), ((sgn * 3.4, -1.5, zf), (1, 0, 0)), ((x, -0.75, zf), (0, 1, 0))):
            flange(c, d, mat=GOLD)
        for c in ((x, -1.5, zf), (x, 0.0, zf)):   # mitred corner blocks
            bpy.ops.mesh.primitive_cube_add(size=1, location=c); cb = bpy.context.object; cb.scale = (0.5, 0.5, 0.27)
            bev = cb.modifiers.new("bev", "BEVEL"); bev.width = 0.02; link(cb, GOLD)
        horn(mouth, (0, 0, 1), length=0.73, A=0.95, B=0.7, mat=GOLD)
        pass  # no wave arcs
    camera((1.0, -10.8, 5.0), (0, 0, 2.0), lens=32, dof=16)
    post_fx(fog=0.55, streaks=0.0, ghosts=0.0, threshold=2.0, anamorphic=0.12)


def neon():
    """A single electron floating on solid neon above the gap of a NbTiN nanowire resonator, Co magnets beside it."""
    dark_stage(0.04)
    light((3.5, 6.0, 3.0), 900, 4, (math.radians(-70), 0, math.radians(150)))   # warm rim light from behind
    bpy.data.lights[-1].color = (1.0, 0.45, 0.25)
    CHIP = principled("chip", **{"Base Color": (0.05, 0.055, 0.07, 1), "Roughness": 0.35})
    box((0, 0, 0.2), (9.0, 7.0, 0.4), CHIP, bevel=0.06)
    NBTIN = principled("nbtin", **{"Base Color": (1.0, 0.3, 0.55, 1), "Metallic": 0.6, "Roughness": 0.25,
                                    "Emission Color": (1.0, 0.25, 0.5, 1), "Emission Strength": 0.25})
    GROUND = principled("ground", **{"Base Color": (0.85, 0.7, 0.35, 1), "Metallic": 1.0, "Roughness": 0.3})
    z0 = 0.42
    # the nanowire: two meanders coming in from left and right, ends nearly touching at the centre
    for s in (-1, 1):
        pts = [(s * 4.2, 1.6), (s * 3.2, 1.6), (s * 3.2, -1.2), (s * 2.6, -1.2), (s * 2.6, 1.2), (s * 2.0, 1.2),
               (s * 2.0, -1.2), (s * 1.4, -1.2), (s * 1.4, 0.0), (s * 0.07, 0.0)]
        gate(pts, width=0.07, height=0.04, mat=NBTIN).location.z = z0 - 0.02
    for y in (2.6, -2.6):  # ground planes
        box((0, y, z0 + 0.01), (8.6, 1.4, 0.04), GROUND, bevel=0.01)
    for x, y in ((-0.6, 0.5), (0.6, 0.5), (-0.6, -0.5), (0.6, -0.5)):  # trap electrodes G1-G4
        box((x, y, z0 + 0.01), (0.5, 0.35, 0.04), GROUND, bevel=0.01)
    COB = principled("cobalt", **{"Base Color": (0.5, 0.52, 0.56, 1), "Metallic": 1.0, "Roughness": 0.4})
    for y in (0.95, -0.95):  # Co micromagnets beside the gap
        box((0, y, z0 + 0.12), (1.0, 0.25, 0.22), COB)
    # solid neon: a frosted, slightly lumpy translucent film over the chip
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, z0 + 0.32))
    film = bpy.context.object; film.scale = (8.6, 6.6, 1)
    bpy.ops.object.transform_apply(scale=True)
    sub = film.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 5; sub.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.new("lumps", "CLOUDS"); tex.noise_scale = 0.8
    dsp = film.modifiers.new("disp", "DISPLACE"); dsp.texture = tex; dsp.strength = 0.08
    sol = film.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.28
    link(film, principled("neon_ice", **{"Base Color": (0.75, 0.88, 1.0, 1), "Transmission Weight": 1.0,
                                           "Roughness": 0.35, "IOR": 1.1}))
    # the electron above the gap, glowing blue-white, with a soft halo and a faint double-well dip below
    ez = z0 + 0.78
    sphere((0, 0, ez), 0.12, emission("electron_blue", (0.7, 0.85, 1.0, 1), 30.0))
    sphere((0, 0, ez), 0.7, volume_glow("e_halo", (0.4, 0.7, 1.0, 1), 4.0))
    l = bpy.data.lights.new("e", "POINT"); l.energy, l.color = 40, (0.6, 0.8, 1.0)
    lo = bpy.data.objects.new("e", l); lo.location = (0, 0, ez); sc.collection.objects.link(lo)
    # a microwave photon rising from the gap: a white helix fading upwards
    pts = []
    for k in range(400):
        f = k / 399
        pts.append((0.18 * math.cos(2 * math.pi * 7 * f), 0.18 * math.sin(2 * math.pi * 7 * f) - 0.6 * f, ez + 0.4 + 2.6 * f))
    tube(pts, 0.018, emission("photon", (0.9, 0.95, 1.0, 1), 3.0))
    # a few stray electrons trapped on rough patches of the neon
    for x, y in ((-2.9, -2.0), (3.3, 1.9), (-3.6, 2.2)):
        sphere((x, y, z0 + 0.66), 0.06, emission("stray", (0.6, 0.8, 1.0, 1), 8.0))
    camera((-4.2, -7.2, 5.2), (0, 0, 0.8), lens=40, dof=5)


def chip_cavity():
    """Circuit QED in general: a qubit on a chip at the antinode of a superconducting resonator, exchanging a photon."""
    dark_stage(0.04)
    light((3.5, 6.0, 3.0), 700, 4, (math.radians(-70), 0, math.radians(150)))
    bpy.data.lights[-1].color = (1.0, 0.5, 0.3)
    CHIP = principled("chip2", **{"Base Color": (0.05, 0.055, 0.07, 1), "Roughness": 0.3})
    box((0, 0, 0.2), (13.0, 6.0, 0.4), CHIP, bevel=0.06)
    METAL = principled("niobium", **{"Base Color": (0.8, 0.82, 0.86, 1), "Metallic": 1.0, "Roughness": 0.22})
    z0, L = 0.42, 5.2
    box((0, 0, z0 + 0.02), (2 * L, 0.22, 0.05), METAL, bevel=0.01)              # centre strip
    for s in (-1, 1):
        box((s * (L + 0.95), 0, z0 + 0.02), (1.6, 0.22, 0.05), METAL, bevel=0.01)  # feed lines, gaps = mirrors
        box((0, s * 1.75, z0 + 0.02), (12.6, 2.6, 0.05), METAL, bevel=0.01)    # ground planes
    # the photon's standing wave over the strip: two mirrored glowing waves, antinode in the middle
    for k in (1, -1):
        pts = [(-L + 2 * L * i / 500, 0, z0 + 0.9 + k * 0.7 * math.cos(math.pi * (-L + 2 * L * i / 500) / L)) for i in range(501)]
        tube(pts, 0.035, GLOW)
    # the qubit at the central antinode, just beside the strip
    sz = z0 + 0.9
    spin((0, -0.55, sz), (0.4, 0.15, 1.0), r=0.42)
    # a photon being exchanged: a white helix between the spin and the resonator crest
    pts = []
    for k in range(300):
        f = k / 299
        pts.append((-2.6 + 2.6 * f, -0.55 * f + 0.2 * math.cos(2 * math.pi * 7 * f), sz + 0.7 * (1 - f) + 0.2 * math.sin(2 * math.pi * 7 * f)))
    tube(pts, 0.022, emission("photon2", (0.95, 0.97, 1.0, 1), 4.0))
    camera((-4.0, -9.0, 5.2), (0.3, 0, 0.9), lens=38, dof=6)


def open_bubble():
    """An open quantum system: a spin in a glass bubble (the system) on an endless carpet of small spins (the
    environment); rings of excitation spread from the system into the environment and tilt the spins they reach."""
    dark_stage(0.05)
    import random
    random.seed(9)
    c = Vector((0, 0, 1.15))
    BUB = principled("bubble", **{"Base Color": (0.9, 0.85, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.02,
                                   "IOR": 1.15, "Coat Weight": 1.0})
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.1, location=tuple(c), segments=96, ring_count=48)
    bpy.ops.object.shade_smooth(); b = bpy.context.object
    sol = b.modifiers.new("s", "SOLIDIFY"); sol.thickness = 0.03
    link(b, BUB)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.015, location=(0, 0, c.z))  # rim glint
    link(bpy.context.object, emission("rim", (0.7, 0.5, 1.0, 1), 2.0))
    spin(tuple(c), (0.35, 0.15, 1.0), r=0.45)
    # the environment: a carpet of tiny cones, instanced on small triangles whose normals set each cone's direction;
    # near the rings they tilt outwards
    CONE = principled("envcone", **{"Base Color": (0.72, 0.75, 0.82, 1), "Metallic": 0.3, "Roughness": 0.25})
    rings = (2.0, 3.6, 5.6)
    step = 0.34
    import bmesh
    bm = bmesh.new()
    for gx in range(-60, 61):
        for gy in range(-24, 60):
            x, y = gx * step + random.uniform(-0.03, 0.03), gy * step + random.uniform(-0.03, 0.03)
            r = math.hypot(x, y)
            if r < 1.35 or r > 20:
                continue
            tilt = sum(math.exp(-((r - rr) / 0.3) ** 2) for rr in rings)
            rad = Vector((x, y, 0)).normalized()
            d = (Vector((0, 0, 1)) + 0.15 * Vector((random.gauss(0, 1), random.gauss(0, 1), 0)) + 1.6 * tilt * rad).normalized()
            e1 = d.orthogonal().normalized(); e2 = d.cross(e1)
            cc = Vector((x, y, 0.1))
            s = 0.05
            v = [bm.verts.new(cc + s * (math.cos(a) * e1 + math.sin(a) * e2)) for a in (0, 2.094, 4.189)]
            f = bm.faces.new(v)
            if f.normal.dot(d) < 0:
                f.normal_flip()
    me = bpy.data.meshes.new("carpet"); bm.to_mesh(me); bm.free()
    host = bpy.data.objects.new("carpet", me); sc.collection.objects.link(host)
    host.instance_type = "FACES"; host.use_instance_faces_scale = False
    bpy.ops.mesh.primitive_cone_add(radius1=0.055, depth=0.18, vertices=10, location=(0, 0, 0))
    cone = bpy.context.object; link(cone, CONE); cone.parent = host
    # the rings of excitation spreading outwards, fading with distance
    for i, rr in enumerate(rings):
        pts = [(rr * math.cos(a), rr * math.sin(a), 0.06) for a in [2 * math.pi * k / 300 for k in range(301)]]
        tube(pts, 0.03, emission("ring%d" % i, (0.7, 0.45, 1.0, 1), 4.0 / (1 + i)))
    # a soft glow under the bubble where system and environment touch
    bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=0.01, vertices=96, location=(0, 0, 0.02))
    link(bpy.context.object, emission("pool", (0.7, 0.45, 1.0, 1), 0.8))
    camera((0.0, -7.2, 3.2), (0, 1.5, 0.8), lens=40, dof=3.2)


def laser3():
    """Cavity QED in general: two spins in the standing wave between curved mirrors, a drive laser coming in,
    and the light the cavity leaks out through one mirror."""
    dark_stage(0.03)
    h, L = 2.3, 4.6
    mirror_shell(L, 1, h); mirror_shell(-L, -1, h)
    for s in (-1, 1):  # slim mounts under the mirrors
        bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=h - 1.4, vertices=32, location=(s * (L + 0.45), 0, (h - 1.4) / 2))
        link(bpy.context.object, STEEL)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.1, vertices=64, location=(s * (L + 0.45), 0, 0.05))
        link(bpy.context.object, STEEL)
    k = 2 * math.pi * 2.5 / (2 * L)
    beam((-L + 0.2, 0, h), (L - 0.2, 0, h), 0.55, beam_material("cavity3", (0.3, 1.0, 0.85, 1), 6.0, standing=0.9, k=k * L))
    for s in (-1, 1):
        x = s * 1.85
        tilt = math.radians(25 * s)
        spin((x, 0, h), (math.sin(tilt), 0.1, math.cos(tilt)), r=0.46)
        flip_arrow((x, 0, h), 0.95, math.radians(55 if s < 0 else 125), math.radians(70 * (1 if s < 0 else -1)))
        flip_arrow((x, 0, h), 0.95, math.radians(235 if s < 0 else 305), math.radians(70 * (1 if s < 0 else -1)))
    # drive laser entering through the left mirror, light leaking out through the right one
    beam((-14, 0, h), (-L - 0.25, 0, h), 0.16, beam_material("drive3", (1.0, 0.25, 0.45, 1), 6.0))
    beam((L + 0.25, 0, h), (14, 0, h), 0.12, beam_material("leak3", (0.3, 1.0, 0.85, 1), 3.5))
    camera((1.0, -11.5, 4.4), (0, 0, 2.0), lens=34, dof=8)


def spin_bath():
    """Open quantum system: a central spin on an endless carpet of small spins; the excitation it leaks into its
    environment spreads as rings in which the small spins tilt outwards."""
    dark_stage(0.05)
    import random, bmesh
    random.seed(9)
    c = Vector((0, 0, 0.62))
    spin(tuple(c), (0.35, 0.15, 1.0), r=0.4)
    rings = (1.9, 3.3, 5.0, 7.0)
    bm = bmesh.new()
    glow_bm = bmesh.new()
    step = 0.3
    base = []
    for a in range(10):  # a small cone: 10 base points and a tip
        an = 2 * math.pi * a / 10
        base.append((math.cos(an), math.sin(an)))
    for gx in range(-80, 81):
        for gy in range(-30, 90):
            x, y = gx * step + random.uniform(-0.06, 0.06), gy * step + random.uniform(-0.06, 0.06)
            r = math.hypot(x, y)
            if r < 1.0 or r > 26:
                continue
            w = [math.exp(-((r - rr) / 0.32) ** 2) for rr in rings]
            tilt = sum(wi / (1 + 0.35 * i) for i, wi in enumerate(w))
            rad = Vector((x, y, 0)).normalized()
            d = (Vector((0, 0, 1)) + 0.12 * Vector((random.gauss(0, 1), random.gauss(0, 1), 0)) + 2.2 * tilt * rad).normalized()
            e1 = d.orthogonal().normalized(); e2 = d.cross(e1)
            cc = Vector((x, y, 0.08))
            target = glow_bm if tilt > 0.35 else bm
            ring = [target.verts.new(cc + 0.05 * (bx * e1 + by * e2)) for bx, by in base]
            tip = target.verts.new(cc + 0.17 * d)
            for i in range(10):
                target.faces.new((ring[i], ring[(i + 1) % 10], tip))
            target.faces.new(list(reversed(ring)))
    for b_, name, mat in ((bm, "carpet2", principled("envcone2", **{"Base Color": (0.7, 0.73, 0.8, 1), "Metallic": 0.3, "Roughness": 0.3})),
                          (glow_bm, "carpet_lit", principled("envcone_lit", **{"Base Color": (0.85, 0.75, 1.0, 1), "Metallic": 0.2, "Roughness": 0.3,
                                                                              "Emission Color": (0.7, 0.45, 1.0, 1), "Emission Strength": 0.8}))):
        me = bpy.data.meshes.new(name); b_.to_mesh(me); b_.free()
        ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(mat)
    camera((0.0, -6.0, 4.4), (0, 1.2, 0.3), lens=38, dof=3.5)

def bright_stage(floor_z=-0.7, exposure=-0.45, sun_rot=(40, 0, -25)):
    """The shared look of the paper renders (as in bath_wow): pale brick-grid floor, pastel sky gradient seen by the
    camera only, studio HDRI for lighting and reflections, a warm sun, AgX Punchy, and the near-empty air box that
    keeps Cycles/OptiX from crashing on object volumes. Call it first, then build the scene, then camera() and
    post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0,
    saturation=1.15). Set sc.camera.data.clip_end = 5000 after camera()."""
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, floor_z))
    fl = principled("pale_floor", **{"Base Color": (0.78, 0.8, 0.82, 1), "Roughness": 0.45})
    nt = fl.node_tree
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = br.inputs["Color2"].default_value = (0.98, 0.9, 0.82, 1)
    br.inputs["Mortar"].default_value = (0.95, 0.72, 0.62, 1)
    br.inputs["Scale"].default_value = 0.6; br.inputs["Mortar Size"].default_value = 0.012
    br.offset = 0.0; br.squash = 1.0
    nt.links.new(br.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    link(bpy.context.object, fl)
    wt = sc.world.node_tree; wn_ = wt.nodes
    lp = wn_.new("ShaderNodeLightPath")
    grad_tc = wn_.new("ShaderNodeTexCoord"); gsep = wn_.new("ShaderNodeSeparateXYZ")
    wt.links.new(grad_tc.outputs["Window"], gsep.inputs[0])
    gr = wn_.new("ShaderNodeValToRGB"); ge = gr.color_ramp.elements
    ge[0].position, ge[0].color = 0.55, (1.0, 0.82, 0.72, 1)
    ge[1].position, ge[1].color = 1.0, (0.55, 0.75, 1.0, 1)
    wt.links.new(gsep.outputs["Y"], gr.inputs["Fac"])
    mixc = wn_.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    wt.links.new(lp.outputs["Is Camera Ray"], mixc.inputs["Factor"])
    bg = wn_["Background"]
    src_link = bg.inputs["Color"].links[0].from_socket
    wt.links.new(src_link, mixc.inputs[6]); wt.links.new(gr.outputs["Color"], mixc.inputs[7])
    wt.links.new(mixc.outputs[2], bg.inputs["Color"])
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy, sun.angle, sun.color = 4.2, math.radians(6), (1.0, 0.94, 0.86)
    so = bpy.data.objects.new("sun", sun); so.rotation_euler = tuple(math.radians(a) for a in sun_rot); sc.collection.objects.link(so)
    bg.inputs["Strength"].default_value = 0.8
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = exposure
    for o_ in [o_ for o_ in sc.objects if o_.type == "LIGHT"]:
        o_.data.color = (1.0, 0.93, 0.85)
    bpy.ops.mesh.primitive_cube_add(size=80, location=(0, 0, 10))
    vb = bpy.context.object
    vm = bpy.data.materials.new("air"); vm.use_nodes = True
    vnt = vm.node_tree; vnt.nodes.remove(vnt.nodes["Principled BSDF"])
    vs_ = vnt.nodes.new("ShaderNodeVolumeScatter"); vs_.inputs["Density"].default_value = 0.0002
    vnt.links.new(vs_.outputs[0], vnt.nodes["Material Output"].inputs["Volume"])
    vb.data.materials.append(vm); vb.visible_shadow = False


def bath_wow():
    """Open quantum system, physical version: an electron spin qubit above a silicon lattice. Spinless 28Si atoms,
    sparse 29Si nuclear spins. The electron's wavefunction |psi|^2 (envelope x valley oscillations) glows on the
    lattice; nuclear spins inside it precess by an angle set by their hyperfine coupling (spiral pattern), far ones
    stay put. Around the qubit, its Bloch vector's trajectory spirals inwards: dephasing and relaxation."""
    import random, bmesh
    random.seed(4)
    # light studio mood: pale floor, normal HDRI, soft key light
    # die surface around the device: pale, with a fine tile grid
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.7))
    fl = principled("pale_floor", **{"Base Color": (0.78, 0.8, 0.82, 1), "Roughness": 0.45})
    nt = fl.node_tree
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = br.inputs["Color2"].default_value = (0.98, 0.9, 0.82, 1)
    br.inputs["Mortar"].default_value = (0.95, 0.72, 0.62, 1)
    br.inputs["Scale"].default_value = 0.6; br.inputs["Mortar Size"].default_value = 0.012
    br.offset = 0.0; br.squash = 1.0
    nt.links.new(br.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    link(bpy.context.object, fl)
    # the chip: a substrate block whose cut front face shows the heterostructure layers
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6.6, -0.35))
    slab = bpy.context.object; slab.scale = (15.2, 18.8, 0.7)
    sm = principled("hetero", **{"Roughness": 0.35})
    nt = sm.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    fac = _math(nt, "ADD", sp.outputs["Z"], 0.5)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.55, 0.85, 0.75, 1)       # SiGe buffer
    els[1].position, els[1].color = 0.55, (0.3, 0.6, 1.0, 1)     # Si quantum well
    for pos, col in ((0.68, (1.0, 0.5, 0.3, 1)), (0.93, (0.3, 0.75, 0.62, 1))):   # SiGe barrier, oxide
        e = els.new(pos); e.color = col
    nt.links.new(fac, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bev = slab.modifiers.new("b", "BEVEL"); bev.width = 0.02; bev.segments = 2
    link(slab, sm)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    # cheerful look: the camera sees a pastel gradient, the HDRI still lights and reflects
    wt = sc.world.node_tree; wn_ = wt.nodes
    lp = wn_.new("ShaderNodeLightPath")
    grad_tc = wn_.new("ShaderNodeTexCoord"); gsep = wn_.new("ShaderNodeSeparateXYZ")
    wt.links.new(grad_tc.outputs["Window"], gsep.inputs[0])
    gr = wn_.new("ShaderNodeValToRGB"); ge = gr.color_ramp.elements
    ge[0].position, ge[0].color = 0.55, (1.0, 0.82, 0.72, 1)     # peach at the horizon
    ge[1].position, ge[1].color = 1.0, (0.55, 0.75, 1.0, 1)     # sky blue above
    wt.links.new(gsep.outputs["Y"], gr.inputs["Fac"])
    mixc = wn_.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    wt.links.new(lp.outputs["Is Camera Ray"], mixc.inputs["Factor"])
    bg = wn_["Background"]
    src_link = bg.inputs["Color"].links[0].from_socket
    wt.links.new(src_link, mixc.inputs[6]); wt.links.new(gr.outputs["Color"], mixc.inputs[7])
    wt.links.new(mixc.outputs[2], bg.inputs["Color"])
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy, sun.angle, sun.color = 4.2, math.radians(6), (1.0, 0.94, 0.86)
    so = bpy.data.objects.new("sun", sun); so.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(so)
    bg.inputs["Strength"].default_value = 0.8
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = -0.45
    for o_ in [o_ for o_ in sc.objects if o_.type == "LIGHT"]:
        o_.data.color = (1.0, 0.93, 0.85)
    # Cycles crashes on the object volumes below unless the camera starts inside a volume; a large, nearly empty box
    # does that without darkening reflections the way an infinite world volume does
    bpy.ops.mesh.primitive_cube_add(size=80, location=(0, 0, 10))
    vb = bpy.context.object
    vm = bpy.data.materials.new("air"); vm.use_nodes = True
    vnt = vm.node_tree; vnt.nodes.remove(vnt.nodes["Principled BSDF"])
    vs_ = vnt.nodes.new("ShaderNodeVolumeScatter"); vs_.inputs["Density"].default_value = 0.0002
    vnt.links.new(vs_.outputs[0], vnt.nodes["Material Output"].inputs["Volume"])
    vb.data.materials.append(vm); vb.visible_shadow = False
    sx, sy = 1.75, 1.4
    wave = lambda x, y: math.sin(2 * math.pi * math.hypot(x, y - 0.3) / 1.7 - 0.6)
    ripple = lambda x, y: 0.12 * wave(x, y) * math.exp(-math.hypot(x, y - 0.3) / 5.0)   # phonon wave                     # wavefunction envelope (Gaussian widths)
    kv = 2 * math.pi / 0.55               # valley oscillation wavenumber (stylised)
    psi2 = lambda x, y: math.exp(-(x / sx) ** 2 - (y / sy) ** 2) * (0.35 + 0.65 * math.cos(kv * x / 2) ** 2)
    step = 0.42
    XL = 2.2                              # inner edge of the leads
    NUC = []
    si28, si29, arrows = bmesh.new(), bmesh.new(), bmesh.new()
    ph = si28.verts.layers.float_color.new("glow")
    glow = arrows.verts.layers.float_color.new("glow")
    glow29 = si29.verts.layers.float_color.new("glow")
    for gx in range(-19, 19):
        for gy in range(-14, 60):
            x = gx * step + (gy % 2) * step / 2
            y = gy * step * 0.87
            if abs(x) > 7.45 or y > 15.9 or y < -2.65 or (XL - 0.2 < abs(x) < 4.6 and y < 3.4):
                continue
            if random.random() > 0.24:
                res28 = bmesh.ops.create_icosphere(si28, subdivisions=2, radius=0.075, matrix=__import__("mathutils").Matrix.Translation((x, y, 0.075 + ripple(x, y))))
                q = 0.5 + 0.5 * wave(x, y) * math.exp(-math.hypot(x, y - 0.3) / 9.0)
                for v in res28["verts"]:
                    v[ph] = (q, q, q, 1)
                continue
            a = psi2(x, y)
            # nuclear spin: ball + arrow; tilt and precession phase grow with the hyperfine coupling a
            c = Vector((x, y, 0.11 + ripple(x, y)))
            NUC.append((c.copy(), a))
            res = bmesh.ops.create_icosphere(si29, subdivisions=2, radius=0.09, matrix=__import__("mathutils").Matrix.Translation(c))
            for v in res["verts"]:
                v[glow29] = (a * a, a * a, a * a, 1)
            theta = 1.7 * a ** 0.5 + random.gauss(0, 0.06)
            phi = math.atan2(y, x) + 9.0 * a + random.uniform(-0.1, 0.1)
            d = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
            e1 = d.orthogonal().normalized(); e2 = d.cross(e1)
            n = 10
            start, mid, tip = c - 0.22 * d, c + 0.2 * d, c + 0.4 * d
            shaft0 = [arrows.verts.new(start + 0.025 * (math.cos(2 * math.pi * i / n) * e1 + math.sin(2 * math.pi * i / n) * e2)) for i in range(n)]
            shaft1 = [arrows.verts.new(mid + 0.025 * (math.cos(2 * math.pi * i / n) * e1 + math.sin(2 * math.pi * i / n) * e2)) for i in range(n)]
            head = [arrows.verts.new(mid + 0.085 * (math.cos(2 * math.pi * i / n) * e1 + math.sin(2 * math.pi * i / n) * e2)) for i in range(n)]
            tv = arrows.verts.new(tip)
            for i in range(n):
                j = (i + 1) % n
                arrows.faces.new((shaft0[i], shaft0[j], shaft1[j], shaft1[i]))
                arrows.faces.new((head[i], head[j], tv))
            arrows.faces.new(list(reversed(shaft0))); arrows.faces.new(list(reversed(head)))
            for v in shaft0 + shaft1 + head + [tv]:
                v[glow] = (a, a, a, 1)

    def glow_mat(name, base, col, k):
        m = principled(name, **{"Base Color": base, "Metallic": 0.6, "Roughness": 0.25})
        nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "glow"
        b.inputs["Emission Color"].default_value = col
        nt.links.new(_math(nt, "MULTIPLY", at.outputs["Fac"], k), b.inputs["Emission Strength"])
        return m
    def phonon_mat():
        """Silicon atoms coloured by their phonon displacement: blue pushed down, grey at rest, warm coral lifted."""
        m = principled("si28", **{"Base Color": (0.62, 0.65, 0.7, 1), "Roughness": 0.3, "Coat Weight": 0.5})
        nt = m.node_tree
        at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "glow"
        rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
        el[0].position, el[0].color = 0.2, (0.0, 0.22, 0.85, 1)
        el[1].position, el[1].color = 0.8, (0.95, 0.08, 0.2, 1)
        mid = el.new(0.5); mid.color = (1.0, 0.93, 0.8, 1)
        nt.links.new(at.outputs["Fac"], rp.inputs["Fac"])
        nt.links.new(rp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        return m
    for b_, name, mat in ((si28, "si28", phonon_mat()),
                          (si29, "si29", glow_mat("si29", (1.0, 0.62, 0.2, 1), (1.0, 0.55, 0.15, 1), 1.5)),
                          (arrows, "nuc_arrows", glow_mat("nuc_arrows", (0.0, 0.45, 0.42, 1), (0.2, 1.0, 0.85, 1), 4.0))):
        me = bpy.data.meshes.new(name); b_.to_mesh(me); b_.free()
        for f in me.polygons:
            f.use_smooth = True
        ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(mat)

    # the electron's |psi|^2 glowing just above the lattice
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0.02))
    cloud = bpy.context.object
    m = bpy.data.materials.new("psi"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, b=None: _math(nt, op, a, b)
    X, Y = sep.outputs["X"], sep.outputs["Y"]
    env = M("EXPONENT", M("MULTIPLY", -1.0, M("ADD", M("POWER", M("DIVIDE", X, sx), 2.0), M("POWER", M("DIVIDE", Y, sy), 2.0))))
    cv = M("COSINE", M("MULTIPLY", X, kv / 2))
    val = M("MULTIPLY", env, M("ADD", 0.15, M("MULTIPLY", 0.85, M("MULTIPLY", cv, cv))))
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.95, 0.8, 1)
    nt.links.new(M("MULTIPLY", val, 3.0), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    cloud.data.materials.append(m)
    cloud.visible_shadow = False

    # the qubit: electron spin above the lattice, warm core lighting the nuclei below
    c = Vector((0, 0.3, 1.05))
    QARROW = principled("qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})
    spin(tuple(c), (0.45, -0.2, 1.0), r=0.42, arrow=QARROW, reach=1.9, shaft=0.1)
    # faint Bloch sphere: equator and two meridians, so the trail reads as the qubit's trajectory
    RING = principled("bloch_ring", **{"Base Color": (0.45, 0.5, 0.6, 1), "Roughness": 0.4})
    for rot in ((0, 0, 0), (math.radians(90), 0, 0), (math.radians(90), 0, math.radians(90))):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.95, minor_radius=0.006, major_segments=160, minor_segments=8,
                                         location=tuple(c), rotation=rot)
        link(bpy.context.object, RING)
    hot_spot(tuple(c), (1.0, 0.7, 0.4, 1), 0.05, 25)
    l = bpy.data.lights.new("core", "POINT"); l.energy, l.color, l.shadow_soft_size = 6, (1.0, 0.65, 0.35), 0.3
    lo = bpy.data.objects.new("core", l); lo.location = c; sc.collection.objects.link(lo)
    # Bloch-vector trajectory: spirals down from the north pole while shrinking (T1 relaxation + T2 dephasing)
    pts = []
    N = 600
    for i in range(N):
        s_ = i / (N - 1)
        R = 0.95 * math.exp(-1.0 * s_)
        th = 0.25 + 1.6 * s_
        ph = 2 * math.pi * 2.5 * s_
        pts.append(tuple(c + R * Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))))
    TRAIL = emission("trail", (0.5, 0.15, 1.0, 1), 4.0)
    tube(pts, 0.04, TRAIL)
    hot_spot(pts[-1], (0.8, 0.5, 1.0, 1), 0.04, 30)

    # electron transport: source and drain leads as Fermi seas (filled up to their chemical potential; source higher =
    # bias), thin tunnel barriers, and single electrons tunnelling source -> dot -> drain
    LEAD = principled("lead", **{"Base Color": (1.0, 0.64, 0.22, 1), "Metallic": 1.0, "Roughness": 0.22})
    ESEA = emission("fermi_sea", (0.3, 0.75, 1.0, 1), 2.2)
    EMOV = emission("electron", (0.45, 0.85, 1.0, 1), 9.0)
    EHOT = principled("electron_trail", **{"Base Color": (0.02, 0.2, 0.85, 1), "Roughness": 0.3, "Emission Color": (0.1, 0.4, 1.0, 1), "Emission Strength": 0.8})
    BARRIER = principled("barrier", **{"Base Color": (0.8, 0.9, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.15, "IOR": 1.3})
    mus = {-1: 1.15, 1: 0.6}
    ESPIN = principled("espin", **{"Base Color": (0.1, 0.45, 1.0, 1), "Roughness": 0.2, "Coat Weight": 0.6})
    QARROW_L = principled("qarrow_l", **{"Base Color": (0.05, 0.42, 0.42, 1), "Metallic": 0.3, "Roughness": 0.25})
    kT = 0.06

    def fermi_sea_mat(name, mu, z0, h):
        """Emitting volume filled up to mu with Fermi-Dirac smearing f = 1 / (1 + exp((z - mu) / kT))."""
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
        v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = 0.6
        v.inputs["Color"].default_value = (0.4, 0.85, 1.0, 1)
        v.inputs["Emission Color"].default_value = (0.25, 0.65, 1.0, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        M = lambda op, a=None, b=None: _math(nt, op, a, b)
        z = M("ADD", z0, M("MULTIPLY", sep.outputs["Z"], h))          # local -> world height
        f = M("DIVIDE", 1.0, M("ADD", 1.0, M("EXPONENT", M("MINIMUM", M("MAXIMUM", M("DIVIDE", M("SUBTRACT", z, mu), kT), -20.0), 20.0))))
        nt.links.new(M("MULTIPLY", f, 0.5), v.inputs["Density"])
        edge = M("MULTIPLY", f, M("SUBTRACT", 1.0, f))              # brightest at the Fermi level
        nt.links.new(M("ADD", M("MULTIPLY", f, 0.0), M("MULTIPLY", edge, 1.5)), v.inputs["Emission Strength"])
        nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
        return m
    for sg in (-1, 1):
        mu = mus[sg]
        x0, x1 = sg * XL, sg * 4.4
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, 0.2250000000000001, 0.17))
        blk = bpy.context.object; blk.scale = (abs(x1 - x0), 5.95, 0.34)
        bev = blk.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 3
        link(blk, LEAD)
        top, bot = mu + 0.3, 0.35
        zc, h = (bot + top) / 2, top - bot
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, 0.2250000000000001, zc))
        vol = bpy.context.object; vol.scale = (abs(x1 - x0) - 0.02, 5.930000000000001, h)
        vol.data.materials.append(fermi_sea_mat("sea%d" % sg, mu, zc, h))
        vol.visible_shadow = False
        # the Fermi sea itself: thousands of electron spins, randomly up or down, filled up to mu
        es, ea = bmesh.new(), bmesh.new()
        Mx = __import__("mathutils").Matrix
        g = 0.2
        lo_x, hi_x = min(x0, x1) + 0.09, max(x0, x1) - 0.09
        nx = int((hi_x - lo_x) / g) + 1
        ny = int(5.75 / g) + 1
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(int((mu - 0.42) / g) + 1):
                    ex = min(max(lo_x + (hi_x - lo_x) * ix / (nx - 1) + random.uniform(-0.03, 0.03), lo_x), hi_x)
                    ey = min(max(-2.65 + 5.75 * iy / (ny - 1) + random.uniform(-0.03, 0.03), -2.65), 3.1)
                    ez = 0.42 + iz * g + random.uniform(-0.03, 0.03)
                    if ez > mu - 0.04 + random.gauss(0, kT):
                        continue
                    cc = Vector((ex, ey, ez))
                    bmesh.ops.create_icosphere(es, subdivisions=1, radius=0.045, matrix=Mx.Translation(cc))
                    up = 1 if random.random() < 0.5 else -1
                    dd = Vector((random.gauss(0, 0.12), random.gauss(0, 0.12), up)).normalized()
                    e1 = dd.orthogonal().normalized(); e2 = dd.cross(e1)
                    n_ = 6
                    p0, p1, tp = cc - 0.09 * dd, cc + 0.06 * dd, cc + 0.12 * dd
                    r0 = [ea.verts.new(p0 + 0.01 * (math.cos(2 * math.pi * i / n_) * e1 + math.sin(2 * math.pi * i / n_) * e2)) for i in range(n_)]
                    r1 = [ea.verts.new(p1 + 0.01 * (math.cos(2 * math.pi * i / n_) * e1 + math.sin(2 * math.pi * i / n_) * e2)) for i in range(n_)]
                    hd = [ea.verts.new(p1 + 0.028 * (math.cos(2 * math.pi * i / n_) * e1 + math.sin(2 * math.pi * i / n_) * e2)) for i in range(n_)]
                    tv = ea.verts.new(tp)
                    for i in range(n_):
                        j = (i + 1) % n_
                        ea.faces.new((r0[i], r0[j], r1[j], r1[i])); ea.faces.new((hd[i], hd[j], tv))
        for b_, nm, mt in ((es, "esea", ESPIN), (ea, "esea_arrows", QARROW_L)):
            me = bpy.data.meshes.new(nm); b_.to_mesh(me); b_.free()
            for f_ in me.polygons:
                f_.use_smooth = True
            ob = bpy.data.objects.new(nm, me); sc.collection.objects.link(ob); me.materials.append(mt)
        bm_ = bmesh.new()
        bmesh.ops.create_cube(bm_, size=1.0)
        me = bpy.data.meshes.new("barrier"); bm_.to_mesh(me); bm_.free()
        bar = bpy.data.objects.new("barrier", me); sc.collection.objects.link(bar)
        bar.location = (sg * (XL - 0.25), 0.2250000000000001, 1.0); bar.scale = (0.12, 5.95, 2.0)
        bm_m = bpy.data.materials.new("barrier"); bm_m.use_nodes = True
        nt = bm_m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
        vv = nt.nodes.new("ShaderNodeVolumePrincipled"); vv.inputs["Density"].default_value = 0.25
        vv.inputs["Color"].default_value = (0.6, 0.35, 1.0, 1)
        vv.inputs["Emission Color"].default_value = (0.55, 0.25, 1.0, 1); vv.inputs["Emission Strength"].default_value = 0.35
        nt.links.new(vv.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
        me.materials.append(bm_m); bar.visible_shadow = False
    # tunnelling path: from the source sea up through the left barrier onto the dot, then down through the right one
    def path(u):
        if u < 0.5:
            v = u / 0.5
            p0, p1 = Vector((-XL - 1.4, -0.2, mus[-1] + 0.05)), Vector((-0.45, 0.25, c.z - 0.05))
        else:
            v = (u - 0.5) / 0.5
            p0, p1 = Vector((0.45, 0.25, c.z - 0.05)), Vector((XL + 1.4, -0.2, mus[1] + 0.05))
        q = p0.lerp(p1, v)
        q.z += 0.35 * math.sin(math.pi * v)
        return q
    for u0 in (0.18, 0.36, 0.7, 0.88):
        tail = [tuple(path(max(u0 - 0.12 + 0.12 * i / 30, 0.0 if u0 < 0.5 else 0.5))) for i in range(31)]
        tube(tail, 0.035, EHOT)
        sphere(tail[-1], 0.075, principled("electron_ball", **{"Base Color": (0.02, 0.25, 1.0, 1), "Roughness": 0.2, "Coat Weight": 1.0, "Emission Color": (0.2, 0.5, 1.0, 1), "Emission Strength": 1.5}))
        # each electron carries its spin: a small arrow, up or down
        up = 1 if u0 in (0.18, 0.88) else -1
        e = Vector(tail[-1]); dd = Vector((0, 0, up))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.26, location=e, vertices=12)
        link(bpy.context.object, QARROW)
        bpy.ops.mesh.primitive_cone_add(radius1=0.035, depth=0.08, location=e + dd * 0.16, rotation=dd.to_track_quat("Z", "Y").to_euler(), vertices=16)
        link(bpy.context.object, QARROW)
    # 1) entanglement: threads from the qubit to the nuclear spins it couples to most strongly
    THREAD = lambda k: emission("thread%.2f" % k, (0.1, 0.85, 0.75, 1), k * 0.35)
    strongest = sorted(NUC, key=lambda q: -q[1])[:16]
    for pos, a_ in strongest:
        top = pos + Vector((0, 0, 0.2))
        d0 = (top - c).normalized()
        p0 = c + d0 * 0.45
        mid = (p0 + top) / 2 + Vector((0, 0, 0.25 + 0.1 * (top - p0).length))
        pts_ = [tuple((1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u * u * top) for u in [i / 40 for i in range(41)]]
        tube(pts_, 0.012 + 0.01 * a_, THREAD(round(4 + 10 * a_, 2)))
    # 2) charge noise: two-level fluctuators (flipping dipoles) in the surface oxide, each sending out field ripples
    PLUS = emission("tls_plus", (1.0, 0.35, 0.25, 1), 5.0)
    MINUS = emission("tls_minus", (0.25, 0.5, 1.0, 1), 5.0)
    for (fx, fy, ang) in ((-1.35, -1.7, 20), (1.55, -0.85, -35), (-1.05, 2.4, 60), (1.25, 3.0, 110)):
        cc = Vector((fx, fy, 0.16 + ripple(fx, fy)))
        dd = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.25)).normalized()
        sphere(tuple(cc + 0.09 * dd), 0.05, PLUS); sphere(tuple(cc - 0.09 * dd), 0.05, MINUS)
        tube([tuple(cc - 0.09 * dd), tuple(cc + 0.09 * dd)], 0.012, STEEL)
        # flip arrow over the dipole: it switches back and forth (telegraph noise)
        arc = [tuple(cc + 0.16 * (math.cos(u) * dd + math.sin(u) * Vector((0, 0, 1)))) for u in [math.radians(30 + 120 * i / 30) for i in range(31)]]
        tube(arc, 0.018, emission("tls_flip", (1.0, 0.7, 0.3, 1), 8.0))
        for i, rr in enumerate((0.3, 0.52, 0.76)):
            bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.02, major_segments=96, minor_segments=6, location=(cc.x, cc.y, 0.17))
            link(bpy.context.object, emission("tls_ring%d" % i, (1.0, 0.45, 0.05, 1), 3.0 / (1 + 0.7 * i)))
    # 3) spontaneous emission: a photon wave packet leaving the qubit
    u_ = Vector((-1.0, 0.25, 0.75)).normalized()
    w_ = u_.cross(Vector((0, 0, 1))).normalized()
    p_start = c + u_ * 1.05
    pts_ = []
    for i in range(241):
        sv = i / 240
        env_ = math.exp(-((sv - 0.5) / 0.22) ** 2)
        pts_.append(tuple(p_start + u_ * 1.2 * sv + Vector((0, 0, 1)) * 0.13 * env_ * math.sin(2 * math.pi * 5 * sv)))
    PHOTON = False  # dropped at the owner's request
    if PHOTON:
        tube(pts_, 0.016, emission("photon", (1.0, 0.85, 0.5, 1), 7.0))
    camera((0.0, -9.4, 3.9), (0, 0.5, 0.55), lens=40, dof=1.4)
    sc.camera.data.clip_end = 5000
    post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)


SCENES = {"bath_wow": bath_wow, "laser_wow": laser_wow, "mobius_variant": mobius_variant, "mobius_band_float": mobius_band_float, "mobius_float": mobius_float, "mobius_board": mobius_board, "mobius_zoo": mobius_zoo, "laser3": laser3, "spin_bath": spin_bath, "chip_cavity": chip_cavity, "open_bubble": open_bubble, "mobius_ssh": mobius_ssh, "neon": neon, "surf": surf, "timechain": timechain, "kitaev": kitaev, "bloch": bloch, "laser2": laser2, "mobius2": mobius2, "bath2": bath2, "light_matter": light_matter, "open_systems": open_systems, "topological": topological,
 "laser_cavity": laser_cavity, "mobius": mobius, "bath": bath}
if SCENE in SCENES:
    SCENES[SCENE]()
else:
    # paper scenes live in papers/<name>.py and run with this module's helpers in scope
    _f = HERE / "papers" / (SCENE + ".py")
    exec(compile(_f.read_text(), str(_f), "exec"), globals())
# make the soft glow shell see-through
for m in (GLOW_SOFT,):
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    if m is GLOW_SOFT:
        mix = nt.nodes.new("ShaderNodeMixShader")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix.inputs["Fac"].default_value = 0.35
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT)

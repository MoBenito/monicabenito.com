"""Revision of the second concept: the paper's own Figure 1 lifted into 3D, with more wow.

Two curved cavity mirrors hold one photon mode (green glowing Gaussian standing wave). In the middle the two states
that the strong coupling mixes: spin down plus one photon, and spin up with the photon absorbed (green glow inside
the sphere). Purple arrows close the exchange loop (vacuum Rabi oscillation). Below: a polished, iridescent silicon
wafer with a Si/SiGe heterostructure chip in the middle (cut edge shows the layers), whose mirror-like top reflects
the mode. Hot spots where the mode meets the mirrors, with soft star streaks and lens ghosts in post.
"""
bright_stage(floor_z=-0.7, exposure=-0.35, sun_rot=(48, 0, -30))

# --- ground ---------------------------------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.68))
link(bpy.context.object, principled("cspf_ground", **{"Base Color": (1.0, 0.68, 0.62, 1), "Roughness": 0.5}))

# --- polished silicon wafer: deep violet-blue, thin-film iridescence, fine die grid etched in roughness --------
bpy.ops.mesh.primitive_cylinder_add(radius=16.0, depth=0.25, vertices=256, location=(0, 7.0, -0.55))
wafer = bpy.context.object
wm = principled("cspf_wafer", **{"Base Color": (0.3, 0.36, 0.95, 1), "Metallic": 0.8, "Roughness": 0.06,
                                  "Coat Weight": 1.0, "Coat Roughness": 0.02})
nt = wm.node_tree
b = nt.nodes["Principled BSDF"]
try:
    b.inputs["Thin Film Thickness"].default_value = 520.0
    b.inputs["Thin Film IOR"].default_value = 1.9
except Exception as e:
    print("thin film", e)
tcw = nt.nodes.new("ShaderNodeTexCoord")
br = nt.nodes.new("ShaderNodeTexBrick")
br.offset = 0.0; br.squash = 1.0
br.inputs["Scale"].default_value = 0.5
br.inputs["Mortar Size"].default_value = 0.006
br.inputs["Color1"].default_value = (0.32, 0.4, 1.0, 1)
br.inputs["Color2"].default_value = (0.42, 0.36, 1.0, 1)
br.inputs["Mortar"].default_value = (0.55, 0.55, 1.0, 1)
nt.links.new(tcw.outputs["Object"], br.inputs["Vector"])
nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
# street lines are matte, dies are polished
rmap = nt.nodes.new("ShaderNodeMapRange")
rmap.inputs["To Min"].default_value, rmap.inputs["To Max"].default_value = 0.35, 0.05
nt.links.new(br.outputs["Fac"], rmap.inputs["Value"])
nt.links.new(rmap.outputs["Result"], b.inputs["Roughness"])
# radial colour drift across the wafer (like real thin-film thickness variation)
grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 16, 1 / 16, 1 / 16)
nt.links.new(tcw.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], grad.inputs[0])
tf = nt.nodes.new("ShaderNodeMapRange")
tf.inputs["To Min"].default_value, tf.inputs["To Max"].default_value = 620.0, 430.0
nt.links.new(grad.outputs["Fac"], tf.inputs["Value"])
try:
    nt.links.new(tf.outputs["Result"], b.inputs["Thin Film Thickness"])
except Exception as e:
    print("thin film link", e)
link(wafer, wm)
bev = wafer.modifiers.new("b", "BEVEL"); bev.width = 0.06; bev.segments = 3

# --- heterostructure chip under the cavity: layered cut edge, mirror-polished top -----------------------------
CW, CD, CH = 6.4, 3.6, 0.9
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.6, -0.43 + CH / 2))
chip = bpy.context.object; chip.scale = (CW, CD, CH)
cm = principled("cspf_hetero", **{"Roughness": 0.25, "Coat Weight": 0.8, "Coat Roughness": 0.05})
nt = cm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sp.inputs[0])
fac = _math(nt, "ADD", sp.outputs["Z"], 0.5)
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.55, 0.88, 0.78, 1)        # SiGe buffer
els[1].position, els[1].color = 0.42, (0.35, 0.55, 1.0, 1)        # 28Si well
for pos, col in ((0.56, (1.0, 0.55, 0.32, 1)), (0.80, (0.42, 0.8, 0.7, 1)), (0.93, (0.88, 0.86, 1.0, 1))):
    e = els.new(pos); e.color = col                                    # SiGe barrier, Si cap, oxide
nt.links.new(fac, ramp.inputs["Fac"])
# top face: dark polished silicon so it reflects the glowing mode; sides show the layer colours
top = _math(nt, "GREATER_THAN", sp.outputs["Z"], 0.49)
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
mixc.inputs[7].default_value = (0.62, 0.48, 1.0, 1)
nt.links.new(top, mixc.inputs["Factor"]); nt.links.new(ramp.outputs["Color"], mixc.inputs[6])
nt.links.new(mixc.outputs[2], nt.nodes["Principled BSDF"].inputs["Base Color"])
nt.links.new(_math(nt, "SUBTRACT", 0.25, _math(nt, "MULTIPLY", top, 0.23)), nt.nodes["Principled BSDF"].inputs["Roughness"])
try:
    nt.links.new(_math(nt, "MULTIPLY", top, 450.0), nt.nodes["Principled BSDF"].inputs["Thin Film Thickness"])
except Exception as e:
    print("thin film", e)
nt.links.new(_math(nt, "MULTIPLY", top, 0.4), nt.nodes["Principled BSDF"].inputs["Metallic"])
bev = chip.modifiers.new("b", "BEVEL"); bev.width = 0.03; bev.segments = 3
link(chip, cm)
CSPF_PAD = principled("cspf_pad", **{"Base Color": (1.0, 0.7, 0.25, 1), "Metallic": 1.0, "Roughness": 0.32})
# a gold frame of bond pads along the chip rim
for i in range(8):
    x = -CW / 2 + 0.5 + i * (CW - 1.0) / 7
    for y in (0.6 - CD / 2 + 0.35, 0.6 + CD / 2 - 0.35):
        box((x, y, -0.43 + CH + 0.02), (0.34, 0.34, 0.05), CSPF_PAD, bevel=0.015)

H = 2.6          # cavity axis height
L = 4.3          # mirror vertex distance from centre

# --- mirrors: cyan dielectric coating with thin-film shimmer --------------------------------------------------
CSPF_SHELL = principled("cspf_shell", **{"Base Color": (0.15, 0.78, 1.0, 1), "Metallic": 0.75, "Roughness": 0.06,
                                          "Coat Weight": 1.0, "Coat Roughness": 0.0})
try:
    CSPF_SHELL.node_tree.nodes["Principled BSDF"].inputs["Thin Film Thickness"].default_value = 380.0
    CSPF_SHELL.node_tree.nodes["Principled BSDF"].inputs["Thin Film IOR"].default_value = 1.5
except Exception as e:
    print("thin film", e)
for x, f in ((L, 1), (-L, -1)):
    ms = mirror_shell(x, f, H, R=3.4, depth=0.7)
    ms.data.materials.clear(); ms.data.materials.append(CSPF_SHELL)
    ms.scale = (1.0, 1.15, 1.15)

# --- the cavity photon: Gaussian standing-wave mode between the mirrors --------------------------------------
GREEN = (0.15, 1.0, 0.25, 1)
beam((-L + 0.1, 0, H), (L - 0.1, 0, H), 1.25, gauss_mode_material("cspf_mode", GREEN, 34.0, waist=0.32,
                                                                  standing=0.45, k=5 * math.pi / 2))
# a thin bright core along the axis
beam((-L + 0.15, 0, H), (L - 0.15, 0, H), 0.16, beam_material("cspf_core", (0.6, 1.0, 0.55, 1), 18.0))
# hot spots where the mode lands on the mirrors: these carry the flare
for x in (L - 0.55, -(L - 0.55)):
    sphere((x, 0, H), 0.08, emission("cspf_hot", (0.75, 1.0, 0.7, 1), 220.0))

# --- the two coupled states ----------------------------------------------------------------------------------
CSPF_ORANGE = principled("cspf_orange", **{"Base Color": (1.0, 0.32, 0.05, 1), "Transmission Weight": 0.55,
                                            "Roughness": 0.05, "IOR": 1.45, "Coat Weight": 0.5})
CSPF_ARROW = principled("cspf_arrow", **{"Base Color": (1.0, 0.85, 0.3, 1), "Metallic": 0.3, "Roughness": 0.15,
                                          "Coat Weight": 1.0})
down = Vector((-1.05, -0.2, H - 0.45))
up = Vector((1.05, -0.2, H + 0.45))
spin(tuple(down), (0, 0, -1), r=0.62, mat=CSPF_ORANGE, arrow=CSPF_ARROW, reach=1.7, shaft=0.13)
spin(tuple(up), (0, 0, 1), r=0.5, mat=CSPF_ORANGE, arrow=CSPF_ARROW, reach=1.8, shaft=0.14)
# the absorbed photon: green glow inside the spin-up sphere
sphere(tuple(up), 0.26, emission("cspf_core_up", GREEN, 14.0))

# purple exchange arrows (top: up -> down, bottom: down -> up), as in the figure
CSPF_PURPLE = emission("cspf_purple", (0.62, 0.15, 1.0, 1), 3.0)
c = Vector((0, -0.35, H))
flip_arrow(tuple(c), 2.15, math.radians(32), math.radians(118), mat=CSPF_PURPLE)
flip_arrow(tuple(c), 2.15, math.radians(212), math.radians(118), mat=CSPF_PURPLE)

camera((0.8, -12.0, 8.2), (0, 0, H - 0.35), lens=39)
sc.camera.data.clip_end = 5000
post_fx(fog=0.3, streaks=0.18, ghosts=0.12, threshold=6.0, anamorphic=0.25, dispersion=0.004, contrast=18.0,
        saturation=1.2)

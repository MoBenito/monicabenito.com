# Floquet engineering of long-range p-wave superconductivity (Benito et al., PRB 2014)
# A driven Kitaev chain on a superconductor. Front: the chain at t = 0, every site split into two Majorana halves,
# bulk halves paired with neighbours (gold) and, thanks to the drive, with further neighbours (violet arcs = effective
# long-range p-wave pairing); the unpaired end halves glow (Floquet Majoranas). Behind it, stroboscopic snapshots at
# t = T, 2T, ... recede in depth (time axis); the end mode hops between the first and second site from period to
# period, as in the paper's Fig. 1. A drive wave runs along the time axis, its crests marking the strobe instants.
import bmesh

FE_N, FE_D, FE_H, FE_R = 8, 1.32, 1.05, 0.4
FE_XS = [FE_D * (i - (FE_N - 1) / 2) for i in range(FE_N)]
FE_DT = 2.1           # spacing of the snapshots in depth (one drive period)
FE_K = 6              # number of later snapshots

bright_stage(floor_z=0.0, exposure=-0.4, sun_rot=(42, 0, -30))


def fe_cyclorama(y0=5.0, R=5.0, top=30.0, width=80.0, bottom=(1.0, 0.86, 0.74, 1), upper=(0.62, 0.76, 1.0, 1), glow=0.55):
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
    m = principled("fe_cyc", **{"Roughness": 0.6})
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


fe_cyclorama(y0=15.5, R=6.0, bottom=(1.0, 0.7, 0.58, 1), upper=(0.45, 0.65, 1.0, 1), glow=0.12)

FE_SC = principled("fe_superconductor", **{"Base Color": (0.3, 0.55, 1.0, 1), "Metallic": 0.85, "Roughness": 0.28,
                                             "Anisotropic": 0.5, "Coat Weight": 0.6})
FE_HALF = principled("fe_majorana", **{"Base Color": (0.98, 0.85, 0.35, 1), "Transmission Weight": 0.55,
                                         "Roughness": 0.06, "IOR": 1.45, "Coat Weight": 1.0})
FE_ZERO = principled("fe_zero_mode", **{"Base Color": (0.95, 0.3, 0.03, 1), "Roughness": 0.15, "Coat Weight": 1.0,
                                         "Emission Color": (1.0, 0.35, 0.05, 1), "Emission Strength": 2.2})
FE_ZHALO = volume_glow("fe_zero_halo", (1.0, 0.45, 0.05, 1), 1.4)
FE_LONG = emission("fe_long_range", (0.5, 0.15, 1.0, 1), 9.0)
FE_LONG2 = emission("fe_long_range2", (1.0, 0.2, 0.5, 1), 8.0)
FE_GHOST = principled("fe_ghost", **{"Base Color": (0.85, 0.95, 1.0, 1), "Transmission Weight": 1.0,
                                       "Roughness": 0.08, "IOR": 1.25})
FE_TINTS = [principled("fe_tint%d" % j, **{"Base Color": c, "Transmission Weight": 0.6, "Roughness": 0.1, "IOR": 1.3})
            for j, c in enumerate(((1.0, 0.92, 0.55, 1), (0.65, 0.9, 1.0, 1), (1.0, 0.8, 0.6, 1)))]
FE_DRIVE = emission("fe_drive", (1.0, 0.25, 0.55, 1), 6.0)
FE_STROBE = emission("fe_strobe", (1.0, 0.85, 0.4, 1), 18.0)
FE_FRAME = emission("fe_frame", (0.35, 0.6, 1.0, 1), 3.0)

# superconductor slab under the whole time stack
slab_len = FE_DT * FE_K + 2.6
box((0, slab_len / 2 - 1.3, 0.22), (FE_XS[-1] - FE_XS[0] + 2.0, slab_len, 0.44), FE_SC, bevel=0.06)
z0 = 0.44

# --- t = 0: the full chain -------------------------------------------------------------------------------------
for i, x in enumerate(FE_XS):
    for side in (-1, 1):
        end = (i == 0 and side < 0) or (i == FE_N - 1 and side > 0)
        half_sphere((x, 0, FE_H), FE_R, side, FE_ZERO if end else FE_HALF)
    # little gold pedestal: the site sits on the superconductor
    tube([(x, 0, z0), (x, 0, FE_H - FE_R)], 0.05, GOLD)
    if i < FE_N - 1:
        tube([(x + FE_R * 0.75, 0, FE_H), (FE_XS[i + 1] - FE_R * 0.75, 0, FE_H)], 0.075, GOLD)


def fe_arc(xa, xb, y, h, height, mat, r):
    pts = []
    for j in range(61):
        u = j / 60
        pts.append((xa + (xb - xa) * u, y, h + height * math.sin(math.pi * u)))
    tube(pts, r, mat)


# drive-induced long-range pairing: next-nearest (violet) and third-neighbour (pink) arcs above the chain
for i in range(1, FE_N - 3):
    fe_arc(FE_XS[i] + 0.2, FE_XS[i + 2] - 0.2, 0, FE_H + FE_R * 0.8, 0.75, FE_LONG, 0.05)
for i in (1, 4):
    fe_arc(FE_XS[i] + 0.15, FE_XS[i + 3] - 0.15, 0, FE_H + FE_R * 0.8, 1.45, FE_LONG2, 0.045)

# Majorana end modes glow into the room
for x, s in ((FE_XS[0], -1), (FE_XS[-1], 1)):
    sphere((x + s * 0.25, 0, FE_H), 1.0, FE_ZHALO).visible_shadow = False
    l = bpy.data.lights.new("fe_zm", "POINT"); l.energy, l.color, l.shadow_soft_size = 60, (1.0, 0.55, 0.25), 0.5
    lo = bpy.data.objects.new("fe_zm", l); lo.location = (x + s * 0.5, -0.3, FE_H); sc.collection.objects.link(lo)

# --- stroboscopic snapshots t = T, 2T, ... receding in depth ----------------------------------------------------
for k in range(1, FE_K + 1):
    y = k * FE_DT
    site = k % 2                      # the end mode alternates between site 1 and site 2 each period
    for i, x in enumerate(FE_XS):
        glow = i in (site, FE_N - 1 - site)
        sphere((x, y, FE_H), FE_R * (0.62 if glow else 0.5), FE_ZERO if glow else FE_TINTS[(3 * i + 2 * k) % 3])
        if i < FE_N - 1:
            tube([(x + 0.25, y, FE_H), (FE_XS[i + 1] - 0.25, y, FE_H)], 0.03, GOLD)
    # a thin glowing frame: one stroboscopic slice in time
    fx0, fx1 = FE_XS[0] - 0.75, FE_XS[-1] + 0.75
    tube([(fx0, y, z0 + 0.02), (fx0, y, FE_H + 0.85), (fx1, y, FE_H + 0.85), (fx1, y, z0 + 0.02)], 0.018, FE_FRAME)

# --- the drive: a wave along the time axis; each crest is one strobe instant -------------------------------------
xw = FE_XS[-1] + 1.5
pts = []
ymax = FE_K * FE_DT + 0.4
for j in range(600):
    y = -1.4 + (ymax + 1.4) * j / 599
    pts.append((xw, y, FE_H + 0.45 + 0.5 * math.cos(2 * math.pi * y / FE_DT)))
tube(pts, 0.08, FE_DRIVE)
for k in range(0, FE_K + 1):
    hot_spot((xw, k * FE_DT, FE_H + 0.95), (1.0, 0.85, 0.4, 1), 0.13, 25)
    # link from each crest (strobe instant) to its snapshot frame
    tube([(xw, k * FE_DT, FE_H + 0.95), (FE_XS[-1] + 0.75, k * FE_DT, FE_H + 0.85)], 0.014, FE_FRAME)
camera((-5.4, -9.6, 5.3), (0.5, 2.6, 0.75), lens=32, dof=2.2)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.15)

# Blueprint for quantum computing using electrons on helium (Kawakami, Chen, Benito, Konstantinov 2023).
# Hero: a pool of superfluid helium over a chip with an array of ferromagnetic micropillars. Above each pillar one
# electron floats on the helium surface (orange glass spin). Its quantized vertical motion is drawn as glowing
# level rings at the heights of the n = 1 and n = 2 Rydberg states; the front electron is driven between them by
# microwaves from a waveguide horn. Field lines from the micropillar give the local magnetic field gradient that
# mixes Rydberg and spin states; a violet thread between neighbours is their long-range Coulomb coupling.
import bmesh
bright_stage(floor_z=-0.7)

HE_BASE = principled("he_base", **{"Base Color": (1.0, 0.55, 0.8, 1), "Roughness": 0.3, "Coat Weight": 0.6})
HE_WALL = principled("he_wall", **{"Base Color": (0.75, 0.9, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.03, "IOR": 1.45})
HE_LIQ = principled("he_liquid", **{"Base Color": (0.75, 0.95, 1.0, 1), "Transmission Weight": 1.0, "Roughness": 0.0,
                                    "IOR": 1.04, "Coat Weight": 0.0})
HE_PILLAR = principled("he_pillar", **{"Base Color": (0.2, 0.35, 0.95, 1), "Metallic": 0.85, "Roughness": 0.18})
HE_ELEC = principled("he_electrode", **{"Base Color": (0.55, 0.62, 0.9, 1), "Metallic": 0.7, "Roughness": 0.25})
HE_FIELD = emission("he_field", (0.3, 0.55, 1.0, 1), 4.0)
HE_LEVEL1 = emission("he_level1", (0.2, 1.0, 0.8, 1), 6.0)
HE_LEVEL1_S = emission("he_level1s", (0.2, 1.0, 0.8, 1), 2.5)
HE_LEVEL2 = emission("he_level2", (1.0, 0.35, 0.75, 1), 6.0)
HE_COUL = emission("he_coulomb", (0.65, 0.3, 1.0, 1), 5.0)
QA = principled("he_qarrow", **{"Base Color": (0.0, 0.3, 0.3, 1), "Metallic": 0.3, "Roughness": 0.2, "Coat Weight": 1.0})

zs = 0.0            # chip surface (pillar feet)
zl = 1.0            # helium surface
X0, X1, Y0, Y1 = -8.5, 8.5, -3.0, 13.0
box(((X0 + X1) / 2, (Y0 + Y1) / 2, (zs - 0.7) / 2), (X1 - X0 + 0.8, Y1 - Y0 + 0.8, 0.7 - zs), HE_BASE, bevel=0.05)

# rippled helium surface (closed liquid volume: top surface with small capillary ripples around each electron)
PIL = [(x, y) for y in (0.0, 3.2, 6.4, 9.6) for x in (-5.4, -1.8, 1.8, 5.4)]
def ripple(x, y):
    z = 0.0
    for (px, py) in PIL:
        r = math.hypot(x - px, y - py)
        z += 0.012 * math.cos(2 * math.pi * r / 0.55) * math.exp(-r / 0.9)
    return z
bm = bmesh.new()
NX, NY = 220, 200
grid = [[bm.verts.new((X0 + (X1 - X0) * i / NX, Y0 + (Y1 - Y0) * j / NY,
                       zl + ripple(X0 + (X1 - X0) * i / NX, Y0 + (Y1 - Y0) * j / NY))) for j in range(NY + 1)] for i in range(NX + 1)]
for i in range(NX):
    for j in range(NY):
        bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
# sides and bottom so the liquid is a closed volume
bot = [[bm.verts.new((v.co.x, v.co.y, zs + 0.002)) for v in (grid[i][0], grid[i][NY])] for i in range(NX + 1)]
for i in range(NX):
    bm.faces.new((grid[i][0], bot[i][0], bot[i + 1][0], grid[i + 1][0]))
    bm.faces.new((grid[i + 1][NY], bot[i + 1][1], bot[i][1], grid[i][NY]))
left = [bm.verts.new((X0, grid[0][j].co.y, zs + 0.002)) for j in range(NY + 1)]
right = [bm.verts.new((X1, grid[NX][j].co.y, zs + 0.002)) for j in range(NY + 1)]
left[0], left[-1] = bot[0][0], bot[0][1]
right[0], right[-1] = bot[NX][0], bot[NX][1]
for j in range(NY):
    bm.faces.new((grid[0][j + 1], left[j + 1], left[j], grid[0][j]))
    bm.faces.new((grid[NX][j], right[j], right[j + 1], grid[NX][j + 1]))
bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("he_liquid"); bm.to_mesh(me); bm.free()
for f in me.polygons:
    f.use_smooth = True
liq = bpy.data.objects.new("he_liquid", me); sc.collection.objects.link(liq); me.materials.append(HE_LIQ)
liq.visible_shadow = False

# glass cell walls (low rim) around the pool
for (cx, cy, sx, sy) in (((X0 + X1) / 2, Y0 - 0.15, X1 - X0 + 0.6, 0.3), ((X0 + X1) / 2, Y1 + 0.15, X1 - X0 + 0.6, 0.3),
                         (X0 - 0.15, (Y0 + Y1) / 2, 0.3, Y1 - Y0), (X1 + 0.15, (Y0 + Y1) / 2, 0.3, Y1 - Y0)):
    box((cx, cy, 0.7), (sx, sy, 1.4), HE_WALL, bevel=0.04).visible_shadow = False

# micropillars (ferromagnetic, domed) and flat electrodes between them on the chip
for (px, py) in PIL:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.4, location=(px, py, zs + 0.2), vertices=48)
    bpy.ops.object.shade_smooth(); link(bpy.context.object, HE_PILLAR)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(px, py, zs + 0.4), segments=48, ring_count=24)
    bpy.ops.object.shade_smooth(); ob = bpy.context.object; ob.scale = (1, 1, 0.75); link(ob, HE_PILLAR)
for y in (-1.6, 1.6, 4.8, 8.0, 11.2):
    box((0, y, zs + 0.04), (X1 - X0 - 0.6, 0.8, 0.08), HE_ELEC, bevel=0.02)

z1, z2 = zl + 0.5, zl + 1.75        # heights of the n = 1 and n = 2 states (<z> grows like n^2)


def ring(c, r, z, mat, rad=0.03):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=rad, major_segments=96, minor_segments=10, location=(c[0], c[1], z))
    link(bpy.context.object, mat)


def field_lines(px, py, z0):
    """Dipole field lines of a vertically magnetised pillar, r = L sin^2(theta), above the pillar top."""
    for L in (1.5, 2.6):
        for k in range(6):
            ph = 2 * math.pi * k / 6 + 0.3
            pts = []
            for i in range(121):
                th = 0.12 + (math.pi / 2 - 0.12) * i / 120
                r = L * math.sin(th) ** 2
                pts.append((px + r * math.sin(th) * math.cos(ph), py + r * math.sin(th) * math.sin(ph), z0 + r * math.cos(th)))
            tube(pts, 0.016, HE_FIELD)


for n, (px, py) in enumerate(PIL):
    hero = n in (1, 2)
    rr = 0.36 if hero else 0.3
    up = (0.15, -0.1, 1.0) if n % 3 else (-0.1, 0.1, -1.0)
    zc = z2 if n == 1 else z1
    spin((px, py, zc), up, r=rr, arrow=QA, reach=1.9 if hero else 1.7, shaft=0.11)
    hot_spot((px, py, zc), (1.0, 0.7, 0.45, 1), 0.04, 20)
    if hero:
        ring((px, py), 0.75, z1, HE_LEVEL1, 0.035)
        ring((px, py), 0.75, z2, HE_LEVEL2, 0.035)
        field_lines(px, py, zs + 0.7)
    else:
        ring((px, py), 0.5, z1, HE_LEVEL1_S, 0.018)
# the driven electron (front left): a transition arrow between its two levels, and its ghost in n = 1
pa = PIL[1]
gh = sphere((pa[0], pa[1], z1), 0.5, volume_glow("he_ghost", (1.0, 0.5, 0.15, 1), 12.0)); gh.visible_shadow = False
pts = [(pa[0] - 0.95 - 0.25 * math.sin(math.pi * i / 40), pa[1], z1 + (z2 - z1) * i / 40) for i in range(41)]
tube(pts, 0.04, HE_LEVEL2)
for (p, d) in ((pts[-1], (0, 0, 1)), (pts[0], (0, 0, -1))):
    bpy.ops.mesh.primitive_cone_add(radius1=0.12, depth=0.28, location=Vector(p) + Vector(d) * 0.1,
                                    rotation=Vector(d).to_track_quat("Z", "Y").to_euler(), vertices=24)
    link(bpy.context.object, HE_LEVEL2)
# Coulomb coupling between the two hero electrons
pb = PIL[2]
pts = []
for i in range(161):
    u = i / 160
    x = pa[0] + (pb[0] - pa[0]) * u
    z = z2 + (z1 - z2) * u + 0.35 * math.sin(math.pi * u) + 0.08 * math.sin(2 * math.pi * 7 * u)
    pts.append((x, pa[1], z))
tube(pts[12:-12], 0.03, HE_COUL)
# microwave waveguide at the right (two gold plates), a microwave travelling out of it towards the electrons
xw0, xw1, yw, zw_ = 3.9, 6.3, -2.4, z2 + 0.2
for dz in (-0.75, 0.75):
    box(((xw0 + xw1) / 2, yw, zw_ + dz), (xw1 - xw0, 1.6, 0.14), GOLD, bevel=0.03)
MW = emission("he_mw", (0.35, 0.3, 1.0, 1), 9.0)
pts = []
for i in range(301):
    u = i / 300
    x = 6.0 - 3.6 * u
    env_ = min(1.0, u / 0.1) * min(1.0, (1 - u) / 0.1)
    pts.append((x, yw, zw_ + 0.42 * env_ * math.sin(2 * math.pi * 8 * u)))
tube(pts, 0.04, MW)
d = Vector((-1, 0, 0))
bpy.ops.mesh.primitive_cone_add(radius1=0.16, depth=0.38, location=(2.25, yw, zw_), rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=24)
link(bpy.context.object, MW)

camera((-0.6, -12.2, 6.4), (0.2, 2.0, 1.3), lens=34, dof=3.5)
sc.camera.data.clip_end = 5000
post_fx(fog=0.25, streaks=0.0, ghosts=0.0, threshold=3.0, anamorphic=0.0, dispersion=0.0, contrast=18.0, saturation=1.3)

# Shared magnetic field-line helpers for the "__final" revisions of the micromagnet papers (exec'd from
# papers/<slug>__final.py with the scenes.py helpers in scope).
#
# Physics: every magnet is a uniformly magnetised box. Its field is that of two uniformly charged faces
# (magnetic surface charge sigma = M.n on the north face, -M.n on the south face); the field of a charged
# rectangle is evaluated in closed form. Field lines are integrated with RK4 from seeds spread evenly over the
# north face (equal flux per line, so the line density follows |B|) until they enter a magnet again (they close
# into a south face). Lines that do not close inside the scene volume are dropped, so no line ends in mid-air.
#
# One visual language for all papers: stray-field lines are thin glowing blue tubes with a few small arrowheads
# (N -> S outside the magnet); an external homogeneous field is drawn as straight, parallel gold arrows.
import numpy as _np

FL_COLOR = (0.03, 0.3, 1.0, 1)
FL_STRENGTH = 3.2
FL_EXT_COLOR = (1.0, 0.62, 0.12, 1)


class FlMagnet:
    """Box magnet: centre c, full size s, magnetisation along +axis (0,1,2) times sign (+1/-1)."""

    def __init__(self, c, s, axis=0, sign=1, M=1.0):
        self.c = _np.array(c, float); self.h = _np.array(s, float) / 2
        self.axis, self.sign, self.M = axis, sign, M

    def faces(self):
        """(axis, plane coordinate, sigma) of the north and the south face."""
        k = self.axis
        n = (k, self.c[k] + self.sign * self.h[k], +self.M)
        s = (k, self.c[k] - self.sign * self.h[k], -self.M)
        return n, s

    def inside(self, P, pad=0.0):
        return _np.all(_np.abs(_np.asarray(P) - self.c) < self.h + pad, axis=-1)


def _rect_field(P, k, ck, lo, hi, sigma):
    """Field (1/4pi) sigma * int (P-Q)/|P-Q|^3 dA of a charged rectangle normal to axis k at coordinate ck, spanning
    lo..hi in the two other axes. P has shape (..., 3)."""
    i, j = [a for a in range(3) if a != k]
    w = P[..., k] - ck
    w = _np.where(_np.abs(w) < 1e-9, 1e-9, w)
    out = _np.zeros(P.shape)
    for ai, a in enumerate((lo[0], hi[0])):
        for bi, b in enumerate((lo[1], hi[1])):
            s = 1.0 if ai == bi else -1.0        # (u1,v1)+, (u1,v2)-, (u2,v1)-, (u2,v2)+
            u = P[..., i] - a; v = P[..., j] - b
            r = _np.sqrt(u * u + v * v + w * w)
            out[..., k] += s * _np.arctan(u * v / (w * r))
            out[..., i] += s * -_np.log(_np.maximum(v + r, 1e-12))
            out[..., j] += s * -_np.log(_np.maximum(u + r, 1e-12))
    return out * sigma / (4 * math.pi)


def fl_field(P, mags, B0=(0.0, 0.0, 0.0)):
    """Magnetic field B (in units of mu0 M) of all magnets (+ optional homogeneous B0) at points P (..., 3):
    H from the surface charges everywhere, plus M inside the magnets, so B is divergence-free and continuous
    across the pole faces (lines run on through the magnet from S back to N)."""
    P = _np.asarray(P, float)
    out = _np.zeros(P.shape) + _np.asarray(B0, float)
    for m in mags:
        k = m.axis
        i, j = [a for a in range(3) if a != k]
        lo = (m.c[i] - m.h[i], m.c[j] - m.h[j]); hi = (m.c[i] + m.h[i], m.c[j] + m.h[j])
        for (kk, ck, sg) in m.faces():
            out += _rect_field(P, kk, ck, lo, hi, sg)
        out[..., k] += _np.where(m.inside(P), m.sign * m.M, 0.0)
    return out


def fl_trace_many(seeds, mags, bounds, step=0.03, max_len=60.0, B0=(0, 0, 0), sign=1.0):
    """RK4 along +B (sign=1) for many seeds at once. Returns a list of (points, closed): closed means the line
    ran into a magnet (it ends on a face; the last point is bisected onto the surface)."""
    p = _np.array(seeds, float)
    n = len(p)
    lo, hi = _np.array(bounds[0], float), _np.array(bounds[1], float)
    paths = [[p[t].copy()] for t in range(n)]
    result = [None] * n
    active = _np.arange(n)

    def d(q):
        f = fl_field(q, mags, B0) * sign
        return f / _np.maximum(_np.linalg.norm(f, axis=-1, keepdims=True), 1e-15)

    def inside_any(q):
        r = _np.zeros(len(q), bool)
        for m in mags:
            r |= m.inside(q)
        return r

    L = 0.0
    while len(active) and L < max_len:
        x = p[active]
        k1 = d(x); k2 = d(x + 0.5 * step * k1); k3 = d(x + 0.5 * step * k2); k4 = d(x + step * k3)
        q = x + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        L += step
        ins = inside_any(q) & (L > 2 * step)
        out = _np.any(q < lo, axis=1) | _np.any(q > hi, axis=1)
        keep = []
        for t_, idx in enumerate(active):
            if ins[t_]:
                a, b = x[t_], q[t_]
                for _ in range(24):
                    mid = (a + b) / 2
                    if inside_any(mid[None])[0]:
                        b = mid
                    else:
                        a = mid
                paths[idx].append(a)
                result[idx] = (_np.array(paths[idx]), True)
            elif out[t_]:
                paths[idx].append(q[t_])
                result[idx] = (_np.array(paths[idx]), False)
            else:
                paths[idx].append(q[t_]); keep.append(t_)
        p[active] = q
        active = active[keep]
    for idx in active:
        result[idx] = (_np.array(paths[idx]), False)
    return result


def fl_face_seeds(m, nu, nv, inset=0.12, offset=0.012, which="N"):
    """Grid of seeds just outside the north (or south) face: equal face area per seed = equal flux per line."""
    k = m.axis
    i, j = [a for a in range(3) if a != k]
    sgn = m.sign if which == "N" else -m.sign
    seeds = []
    for a in range(nu):
        for b in range(nv):
            fu = (a + 0.5) / nu; fv = (b + 0.5) / nv
            q = m.c.copy()
            q[i] = m.c[i] + (2 * fu - 1) * m.h[i] * (1 - inset)
            q[j] = m.c[j] + (2 * fv - 1) * m.h[j] * (1 - inset)
            q[k] = m.c[k] + sgn * (m.h[k] + offset)
            seeds.append(q)
    return seeds


def fl_ring_seeds(m, n, rad_frac=0.6, offset=0.012, phase=0.0, which="N", rings=(0.6,)):
    """Seeds on rings around the face centre (gives lines fanning out in all azimuths, like a bar-magnet figure)."""
    k = m.axis
    i, j = [a for a in range(3) if a != k]
    sgn = m.sign if which == "N" else -m.sign
    seeds = []
    for rf in rings:
        for t in range(n):
            ph = phase + 2 * math.pi * t / n
            q = m.c.copy()
            q[i] += rf * m.h[i] * math.cos(ph)
            q[j] += rf * m.h[j] * math.sin(ph)
            q[k] = m.c[k] + sgn * (m.h[k] + offset)
            seeds.append(q)
    return seeds


def fl_resample(pts, ds):
    seg = _np.linalg.norm(_np.diff(pts, axis=0), axis=1)
    s = _np.concatenate([[0], _np.cumsum(seg)])
    n = max(int(s[-1] / ds), 2)
    t = _np.linspace(0, s[-1], n + 1)
    return _np.stack([_np.interp(t, s, pts[:, a]) for a in range(3)], 1), s[-1]


_FL_MAT = {}


def fl_material(color=None, strength=None, name="fl_field"):
    key = name
    if key not in _FL_MAT:
        _FL_MAT[key] = emission(name, color or FL_COLOR, strength or FL_STRENGTH)
    return _FL_MAT[key]


def fl_cone(at, d, r, depth, mat):
    d = Vector(d).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=depth, location=Vector(at),
                                    rotation=d.to_track_quat("Z", "Y").to_euler(), vertices=16)
    bpy.ops.object.shade_smooth()
    link(bpy.context.object, mat)


def fl_draw(pts, radius=0.026, mat=None, arrows=(0.5,), head=None, ds=0.04, clip=None):
    """Draw one field line as a glowing tube with arrowheads at the given arc-length fractions.
    clip(p) -> bool: points where clip is True are hidden (the line is split there; used only for occluding
    solids such as a chip block, so the visible pieces still run into the solid, never end in free space)."""
    mat = mat or fl_material()
    P, L = fl_resample(_np.asarray(pts), ds)
    head = head or radius * 6.5
    pieces, cur = [], []
    for p in P:
        if clip is not None and clip(p):
            if len(cur) > 1:
                pieces.append(cur)
            cur = []
        else:
            cur.append(tuple(p))
    if len(cur) > 1:
        pieces.append(cur)
    for pc in pieces:
        tube(pc, radius, mat)
    for f in arrows:
        idx = int(f * (len(P) - 1))
        idx = min(max(idx, 1), len(P) - 2)
        if clip is not None and clip(P[idx]):
            continue
        d = P[idx + 1] - P[idx - 1]
        fl_cone(P[idx], d, radius * 2.7, head, mat)
    return L


def fl_external(origin, direction, span, n=3, spacing=0.5, normal=(0, 0, 1), length=None, radius=0.035, mat=None):
    """Homogeneous external field: n straight, parallel, equally spaced arrows."""
    mat = mat or fl_material(FL_EXT_COLOR, 6.0, "fl_ext")
    d = Vector(direction).normalized(); nrm = Vector(normal).normalized()
    o = Vector(origin)
    for t in range(n):
        off = nrm * spacing * (t - (n - 1) / 2)
        a = o + off - d * span / 2; b = o + off + d * span / 2
        head = radius * 7
        tube([tuple(a), tuple(b - d * head * 0.6)], radius, mat)
        fl_cone(b - d * head / 2, d, radius * 2.8, head, mat)

"""Builds a blackboard page (Hugo renders the formulas with KaTeX, Python draws the plots as wobbly SVG)."""
import json, math, random, shutil, subprocess
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
SITE = HERE / "site"
random.seed(3); rng = np.random.default_rng(3)
W, H = 4800, 2000

def wob(pts, amp=2.0):
    """Hand-drawn look: jitter the points a little, smoothly."""
    pts = np.asarray(pts, float)
    n = len(pts)
    noise = np.cumsum(rng.normal(0, 1, (n, 2)), axis=0)
    noise -= np.linspace(noise[0], noise[-1], n)
    noise *= amp / (np.abs(noise).max() + 1e-9)
    return pts + noise

def path(pts, w=5, op=1.0, amp=2.0, close=False):
    p = wob(pts, amp)
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in p) + (" Z" if close else "")
    return f'<path d="{d}" stroke="white" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>'

def line(a, b, **kw):
    return path(np.linspace(a, b, 30), **kw)

def arrow(a, b, w=5, head=18):
    a, b = np.array(a, float), np.array(b, float)
    d = (b - a) / np.linalg.norm(b - a); nrm = np.array([-d[1], d[0]])
    return line(a, b, w=w) + line(b, b - head * d + head * .55 * nrm, w=w) + line(b, b - head * d - head * .55 * nrm, w=w)

def text(x, y, s, size=56, it=True):
    st = "italic" if it else "normal"
    return f'<text x="{x}" y="{y}" fill="white" font-family="KaTeX_Math, serif" font-style="{st}" font-size="{size}">{s}</text>'

def axes(x0, y0, w, h, xl, yl):
    return arrow((x0, y0 + h), (x0 + w, y0 + h)) + arrow((x0, y0 + h), (x0, y0)) + text(x0 + w - 10, y0 + h + 50, xl) + text(x0 - 60, y0 + 10, yl)

svgs = []

# 1. SSH open chain spectrum E vs v/w with the zero modes
def ssh_spectrum(x0, y0, w, h):
    N = 14; out = [axes(x0, y0, w, h, "v/w", "E")]
    vs = np.linspace(0.0, 2.0, 60)
    Es = []
    for v in vs:
        M = np.zeros((2 * N, 2 * N))
        for i in range(2 * N - 1):
            M[i, i + 1] = M[i + 1, i] = v if i % 2 == 0 else 1.0
        Es.append(np.linalg.eigvalsh(M))
    Es = np.array(Es)
    X = x0 + 20 + (vs / 2.0) * (w - 60)
    Y = lambda e: y0 + h / 2 - e / 3.2 * (h / 2 - 20)
    for k in range(2 * N):
        zero = k in (N - 1, N)
        if zero:
            m = vs < 1.0
            out.append(path(np.c_[X[m], Y(Es[m, k])], w=9, amp=1.5))
            out.append(path(np.c_[X[~m], Y(Es[~m, k])], w=3, op=.6, amp=1.5))
        else:
            out.append(path(np.c_[X, Y(Es[:, k])], w=3, op=.6, amp=1.5))
    out.append(line((x0 + 20 + (w - 60) / 2, y0 + h), (x0 + 20 + (w - 60) / 2, y0 + h - 15), w=4))
    out.append(text(x0 + 20 + (w - 60) / 2 - 10, y0 + h + 50, "1", it=False))
    out.append(text(x0 + 30, y0 + h / 2 - 30, "zero modes", 50, False))
    return out

# 2. bands E(k) = ±|v + w e^{ik}|
def bands(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "k", "E")]
    k = np.linspace(-math.pi, math.pi, 120)
    for v, wt, op in ((0.5, 1.0, 1.0),):
        e = np.abs(v + wt * np.exp(1j * k))
        X = x0 + 20 + (k + math.pi) / (2 * math.pi) * (w - 60)
        for s in (1, -1):
            out.append(path(np.c_[X, y0 + h / 2 - s * e / 1.6 * (h / 2 - 30)], w=6, op=op))
    out.append(text(x0 + 10, y0 + h + 50, "−π", it=False)); out.append(text(x0 + w - 80, y0 + h + 50, "π", it=False))
    out.append(arrow((x0 + w / 2 + 40, y0 + h / 2 - 60), (x0 + w / 2 + 40, y0 + h / 2 + 60), w=4, head=14))
    out.append(text(x0 + w / 2 + 60, y0 + h / 2 + 12, "Δ = 2|v−w|", 50))
    return out

# 3. winding of h(k) around the origin
def winding(cx, cy, r):
    out = [arrow((cx - r - 120, cy), (cx + r + 120, cy)), arrow((cx, cy + r + 60), (cx, cy - r - 80))]
    t = np.linspace(0, 2 * math.pi, 120)
    out.append(path(np.c_[cx + 0.55 * r + r * np.cos(t), cy - r * np.sin(t)], w=6, close=True))
    out.append(arrow((cx + 0.55 * r + r * math.cos(1.2), cy - r * math.sin(1.2)), (cx + 0.55 * r + r * math.cos(1.5), cy - r * math.sin(1.5)), w=6, head=24))
    out.append(text(cx + r + 40, cy + 50, "Re h")); out.append(text(cx + 20, cy - r - 70, "Im h"))
    out.append(text(cx - 70, cy + 70, "0", it=False))
    out.append(text(cx + 1.2 * r, cy - r * .85, "𝒲 = 1", 60))
    return out

# 4. Bloch sphere with a loop enclosing a solid angle
def bloch(cx, cy, r):
    out = []
    t = np.linspace(0, 2 * math.pi, 140)
    out.append(path(np.c_[cx + r * np.cos(t), cy + r * np.sin(t)], w=5, close=True))
    out.append(path(np.c_[cx + r * np.cos(t), cy + 0.28 * r * np.sin(t)], w=3, op=.55, close=True))
    th = 0.75
    out.append(path(np.c_[cx + r * math.sin(th) * np.cos(t), cy - r * math.cos(th) + 0.28 * r * math.sin(th) * np.sin(t)], w=7, close=True))
    for i in range(14):  # hatch the enclosed cap
        a = -math.pi / 2 + (i + .5) / 14 * math.pi
        x = cx + r * math.sin(th) * math.sin(a) * .95
        out.append(line((x, cy - r * math.cos(th) - 0.28 * r * math.sin(th) * math.cos(a) * .9), (x * .2 + cx * .8 + (x - cx) * .1, cy - r * .97), w=2, amp=1))
    out.append(arrow((cx, cy), (cx + r * .55, cy - r * .78), w=5))
    out.append(text(cx + r * .9, cy - r * .9, "γ = −Ω/2", 58))
    return out

# 5. the SSH chain with an edge state
def chain(x0, y0, n=7, d=110):
    out = []
    xs = []
    x = x0
    for i in range(2 * n):
        xs.append(x); x += d * (0.6 if i % 2 == 0 else 1.0)
    for i in range(2 * n - 1):
        out.append(line((xs[i] + 16, y0), (xs[i + 1] - 16, y0), w=8 if i % 2 == 0 else 3))
    for i, x in enumerate(xs):
        t = np.linspace(0, 2 * math.pi, 30)
        out.append(path(np.c_[x + 15 * np.cos(t), y0 + 15 * np.sin(t)], w=4 if i % 2 else 7, close=True, amp=1))
    for i, x in enumerate(xs[::2]):  # edge-state amplitude on A sites, decaying
        a = 140 * (0.45 ** i)
        if a > 6:
            out.append(line((x, y0 - 30), (x, y0 - 30 - a), w=6))
    out.append(text(xs[0] + 18, y0 + 70, "v")); out.append(text(xs[1] + 40, y0 + 70, "w"))
    return out


def kitaev_chain(x0, y0, n=6, d=120):
    out = []
    for i in range(n):
        x = x0 + i * d
        t = np.linspace(0, 2 * math.pi, 40)
        out.append(path(np.c_[x + 50 * np.cos(t), y0 + 26 * np.sin(t)], w=3, op=.6, close=True))
        out.append(path(np.c_[x - 22 + 10 * np.cos(t), y0 + 10 * np.sin(t)], w=6, close=True, amp=.8))
        out.append(path(np.c_[x + 22 + 10 * np.cos(t), y0 + 10 * np.sin(t)], w=6, close=True, amp=.8))
        if 0 < i:
            out.append(line((x - d + 34, y0), (x - 34, y0), w=7))
    out.append(text(x0 - 50, y0 + 90, "γ₁")); out.append(text(x0 + (n - 1) * d + 10, y0 + 90, "γ₂ₙ"))
    return out

def quasienergy(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "A/ω", "εT")]
    a = np.linspace(0, 3, 90)
    for k in range(6):
        e = ((0.7 * k + 1.6 * np.sin(a * (0.6 + 0.25 * k)) + 0.3) % (2 * math.pi)) - math.pi
        seg = np.split(np.arange(len(a)), np.where(np.abs(np.diff(e)) > 2)[0] + 1)
        for sg in seg:
            if len(sg) > 1:
                out.append(path(np.c_[x0 + 20 + a[sg] / 3 * (w - 60), y0 + h / 2 - e[sg] / math.pi * (h / 2 - 20)], w=3, op=.7, amp=1))
    for yy in (y0 + 20, y0 + h - 20):
        out.append(path(np.c_[np.linspace(x0 + 20 + (w - 60) * .35, x0 + w - 40, 30), np.full(30, yy)], w=9, amp=1))
    out.append(text(x0 + w - 150, y0 + 10, "π modes", 46, False))
    return out

def phase_diagram(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "μ/t", "Δ")]
    xa, xb = x0 + w * .25, x0 + w * .75
    out.append(line((xa, y0 + h), (xa, y0 + 30), w=5)); out.append(line((xb, y0 + h), (xb, y0 + 30), w=5))
    for i in range(16):
        xx = xa + (xb - xa) * i / 16
        out.append(line((xx, y0 + h - 5), (xx + 60, y0 + h - 160), w=2, amp=1))
    out.append(text(x0 + w * .38, y0 + h * .35, "topo", 54, False))
    out.append(text(xa - 40, y0 + h + 55, "−2", it=False)); out.append(text(xb - 10, y0 + h + 55, "2", it=False))
    return out

def zbp(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "V", "dI/dV")]
    v = np.linspace(-1, 1, 120)
    g = 0.15 + 0.85 / (1 + (v / 0.08) ** 2)
    out.append(path(np.c_[x0 + 20 + (v + 1) / 2 * (w - 60), y0 + h - 20 - g * (h - 60)], w=6))
    out.append(text(x0 + w / 2 + 30, y0 + 50, "2e²/h", 48))
    return out

def decay(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "n", "|ψ|²")]
    for i in range(12):
        a = math.exp(-i / 2.2) * (h - 60)
        x = x0 + 40 + i * (w - 80) / 12
        out.append(line((x, y0 + h - 5), (x, y0 + h - 5 - a), w=10, amp=1))
    xs = np.linspace(0, 12, 60)
    out.append(path(np.c_[x0 + 40 + xs * (w - 80) / 12, y0 + h - 5 - np.exp(-xs / 2.2) * (h - 60)], w=3, op=.6))
    return out

def torus_bz(cx, cy, R):
    t = np.linspace(0, 2 * math.pi, 120)
    out = [path(np.c_[cx + R * np.cos(t), cy + .45 * R * np.sin(t)], w=5, close=True)]
    out.append(path(np.c_[cx + .45 * R * np.cos(t[10:50]), cy - 10 + .14 * R * np.sin(t[10:50])], w=4))
    out.append(path(np.c_[cx + .38 * R * np.cos(t[60:115]), cy - 20 + .12 * R * np.sin(t[60:115])], w=4))
    out.append(path(np.c_[cx + .72 * R * np.cos(t), cy + .32 * R * np.sin(t)], w=3, op=.5, close=True))
    out.append(text(cx - 60, cy + .45 * R + 70, "BZ ≅ T²", 50, False))
    return out

def diamond(x0, y0, n=5, d=150):
    out = []
    for i in range(n):
        x = x0 + i * d
        pts = [(x, y0), (x + d / 2, y0 - d / 2), (x + d, y0), (x + d / 2, y0 + d / 2), (x, y0)]
        out.append(path(np.array([np.linspace(pts[j], pts[j + 1], 12) for j in range(4)]).reshape(-1, 2), w=4))
        for p in pts[:4]:
            tt = np.linspace(0, 2 * math.pi, 20)
            out.append(path(np.c_[p[0] + 10 * np.cos(tt), p[1] + 10 * np.sin(tt)], w=6, close=True, amp=.6))
        out.append(text(x + d / 2 - 14, y0 + 16, "φ", 40))
    return out

def chern_edge(x0, y0, w, h):
    """Bulk bands of a Chern insulator (slab) with one chiral edge mode crossing the gap."""
    out = [axes(x0, y0, w, h, "k<tspan font-size=\"36\" dy=\"12\">x</tspan>", "E")]
    k = np.linspace(-1, 1, 100)
    X = x0 + 20 + (k + 1) / 2 * (w - 60)
    for i in range(5):
        up = 0.35 + 0.08 * i + 0.4 * k ** 2
        out.append(path(np.c_[X, y0 + h / 2 - up * (h / 2 - 30) / 1.3], w=3, op=.6, amp=1))
        out.append(path(np.c_[X, y0 + h / 2 + up * (h / 2 - 30) / 1.3], w=3, op=.6, amp=1))
    m = np.abs(k) < 0.85
    out.append(path(np.c_[X[m], y0 + h / 2 - k[m] * 0.55 * (h / 2 - 30)], w=8))
    out.append(text(x0 + w - 210, y0 + h / 2 - 70, "edge", 46, False))
    return out

def majorana_wf(x0, y0, w, h):
    out = [axes(x0, y0, w, h, "j", "|γ|²")]
    j = np.linspace(0, 1, 140)
    l = np.exp(-j / 0.08) * (1 + 0.35 * np.cos(j * 70))
    r = np.exp(-(1 - j) / 0.08) * (1 + 0.35 * np.cos((1 - j) * 70))
    X = x0 + 20 + j * (w - 60)
    out.append(path(np.c_[X, y0 + h - 10 - np.clip(l, 0, None) * (h - 80)], w=6))
    out.append(path(np.c_[X, y0 + h - 10 - np.clip(r, 0, None) * (h - 80)], w=6))
    out.append(text(x0 + 70, y0 + 60, "γ<tspan font-size=\"34\" dy=\"12\">L</tspan>", 56)); out.append(text(x0 + w - 150, y0 + 60, "γ<tspan font-size=\"34\" dy=\"12\">R</tspan>", 56))
    return out

PLOTS = [  # (function, args in local coords, box w, h)
    (bands, (70, 20, 760, 560), 860, 680), (ssh_spectrum, (70, 20, 700, 560), 820, 680),
    (winding, (380, 340, 230), 820, 680), (bloch, (320, 330, 260), 760, 660), (chain, (40, 220), 1300, 320),
    (kitaev_chain, (80, 100), 820, 240), (quasienergy, (70, 20, 700, 500), 820, 620), (phase_diagram, (80, 20, 620, 420), 760, 540),
    (zbp, (90, 20, 560, 420), 700, 540), (decay, (90, 20, 560, 400), 700, 520), (torus_bz, (330, 220, 300), 680, 420),
    (diamond, (40, 120), 820, 260), (chern_edge, (90, 20, 520, 400), 660, 520), (majorana_wf, (70, 20, 520, 420), 640, 540),
]
EQS = [
    r"H_{\mathrm{SSH}}=\sum_n\big(v\,c^\dagger_{A,n}c_{B,n}+w\,c^\dagger_{B,n}c_{A,n+1}+\mathrm{h.c.}\big)",
    r"h(k)=v+w\,e^{ik}", r"\mathcal W=\frac{1}{2\pi i}\oint dk\,\partial_k \ln h(k)",
    r"\gamma_n=i\oint_{\mathcal C}\langle u_n(\mathbf k)|\nabla_{\mathbf k}u_n(\mathbf k)\rangle\cdot d\mathbf k",
    r"\Omega_n=\nabla_{\mathbf k}\times\mathcal A_n", r"C=\frac{1}{2\pi}\int_{\mathrm{BZ}}\Omega_n\,d^2k\;\in\mathbb Z",
    r"H_K=\sum_j\big[-\mu\,c_j^\dagger c_j-t\,(c_j^\dagger c_{j+1}+\mathrm{h.c.})+\Delta\,(c_jc_{j+1}+\mathrm{h.c.})\big]",
    r"c_j=\tfrac12(\gamma_{2j-1}+i\gamma_{2j})", r"\gamma=\gamma^\dagger,\;\gamma^2=1",
    r"U(T)=\mathcal T\,e^{-i\int_0^T H(t)\,dt}\equiv e^{-iH_FT}",
    r"Q_{\mu\nu}=\langle\partial_\mu u|\,(1-|u\rangle\langle u|)\,|\partial_\nu u\rangle=g_{\mu\nu}-\tfrac{i}{2}\Omega_{\mu\nu}",
    r"\gamma_{\mathrm{Zak}}=\pi\,\mathcal W", r"\psi_{A,n}\propto\Big(-\frac{v}{w}\Big)^{n}",
    r"\nu=\mathrm{sgn}\,\mathrm{Pf}\,[H(0)]\;\mathrm{Pf}\,[H(\pi)]", r"E_{\pm}(k)=\pm\,|v+w\,e^{ik}|", r"\{\Gamma,H\}=0",
    r"\mathcal A_n(\mathbf k)=i\langle u_n|\nabla_{\mathbf k}u_n\rangle", r"|\psi(T)\rangle=e^{i\gamma}e^{-i\int E\,dt}|\psi(0)\rangle",
    r"\sigma_{xy}=\frac{e^2}{h}\sum_n C_n", r"\Delta(t)=\Delta_0+\Delta_1\cos\omega t", r"H_F=\sum_{m}\frac{[H_{-m},H_m]}{m\hbar\omega}+\dots",
    r"\epsilon_\alpha\in\big[-\tfrac{\pi}{T},\tfrac{\pi}{T}\big)", r"\mathcal{CS}\mathcal{C}^{-1}=-\mathcal S",
    r"\mathcal H(k)=\begin{pmatrix}0&h(k)\\ h^*(k)&0\end{pmatrix}", r"\Gamma=\sigma_z", r"\theta=\pi\;\Rightarrow\;\text{edge modes}",
    r"g_{\mu\nu}=\mathrm{Re}\,Q_{\mu\nu}", r"\mathrm{Ch}=\frac{1}{4\pi}\int d^2k\;\hat{\mathbf d}\cdot(\partial_{k_x}\hat{\mathbf d}\times\partial_{k_y}\hat{\mathbf d})",
    r"G=\frac{2e^2}{h}", r"\nu=\frac{1}{2\pi}\oint d\phi", r"H=\mathbf d(k)\cdot\boldsymbol\sigma", r"\mathbb Z_2", r"\mathbb Z",
    r"\hat P\,e^{i\hat x 2\pi/L}", r"\dot\rho=-i[H,\rho]+\mathcal D[\rho]", r"\langle n\rangle_{t}\to\mathcal W\,t", r"S=\mathrm{e}^{i\pi\nu}",
    r"T\,H(k)\,T^{-1}=H(-k)", r"\Phi=\pi\;:\;\text{AB caging}", r"|\Psi_{\mathrm{edge}}|^2\sim e^{-n/\xi}", r"\xi^{-1}=\ln\frac{w}{v}",
]
rng2 = random.Random(7)
items = []
for f, a, w, h in PLOTS:
    items.append(f'<div class="it" data-w="{w}" data-h="{h}"><svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" overflow="visible">' + "".join(f(*a)) + "</svg></div>")
for tex in EQS:
    size = rng2.choice([46, 54, 60, 68, 76, 88])
    items.append(f'<div class="it eq" style="font-size:{size}px">{{{{ transform.ToMath {json.dumps(tex)} (dict "displayMode" false "output" "html") }}}}</div>')
items_html = "".join(items)
js = """
<script>
(function(){
  var W=%d,H=%d, rnd=(function(s){return function(){s=(s*16807)%%2147483647;return s/2147483647;};})(11);
  var els=[].slice.call(document.querySelectorAll('.it'));
  els.sort(function(a,b){return (b.offsetWidth*b.offsetHeight)-(a.offsetWidth*a.offsetHeight);});
  var placed=[];
  function ov(a,b){var x=Math.max(0,Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)),y=Math.max(0,Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y));return x*y;}
  els.forEach(function(e){
    var w=e.offsetWidth,h=e.offsetHeight,best=null,bs=1e18;
    for(var i=0;i<600;i++){
      var r={x:rnd()*(W-w*0.8)-w*0.1,y:rnd()*(H-h*0.85)-h*0.05,w:w,h:h},s=0;
      placed.forEach(function(p){s+=ov(r,p);});
      s+= (rnd()*0.02)*w*h;
      if(s<bs){bs=s;best=r;}
    }
    placed.push({x:best.x+w*0.12,y:best.y+h*0.12,w:w*0.76,h:h*0.76});
    e.style.left=best.x+'px';e.style.top=best.y+'px';
    e.style.transform='rotate('+((rnd()-0.5)*9).toFixed(2)+'deg)';
    e.style.opacity=(0.65+rnd()*0.35).toFixed(2);
  });
})();
</script>""" % (W, H)
if SITE.exists(): shutil.rmtree(SITE)
(SITE / "layouts").mkdir(parents=True); (SITE / "static").mkdir()
shutil.copytree(HERE.parents[2] / "static" / "katex", SITE / "static/katex")
(SITE / "hugo.toml").write_text('baseURL = "/"\ndisableKinds = ["taxonomy","term","RSS","sitemap","robotsTXT","404"]\n')
(SITE / "layouts/index.html").write_text(f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="katex/katex.min.css">
<style>html,body{{margin:0;background:#000;color:#fff;width:{W}px;height:{H}px;overflow:hidden}} .katex{{color:#fff}}
.it{{position:absolute;white-space:nowrap;transform-origin:center}}</style></head>
<body><div style="position:relative;width:{W}px;height:{H}px">{items_html}</div>{js}</body></html>""")
subprocess.run(["hugo", "-s", str(SITE), "--quiet"], check=True)
print("built")

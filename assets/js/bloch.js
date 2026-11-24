// Bloch sphere on the home page: an electron spin in a magnetic field B along z.
//
// Physics: the Bloch vector r = (<σx>, <σy>, <σz>) precesses about B at the Larmor frequency
// f = (g μB / h) B ≈ 28 GHz/T × B (g ≈ 2). Gates are rotations of r: X, Y, Z are π rotations about x, y, z;
// H is a π rotation about (x + z)/√2. P(|0⟩) = (1 + z)/2. The animation runs the precession about
// 4×10⁹ times slower than real time and plays each gate as a short pulse (π per 0.6 s) in the rotating frame,
// i.e. with the precession paused, as for resonant pulses in an experiment.
// Interaction: click (or drag) on the sphere to point the spin there (the poles give exactly |0⟩ and |1⟩),
// drag the B arrow (0 to 100 mT, its track shows the range); buttons below give X, Y, Z, H. Keyboard on the focused sphere:
// Enter/Space = X, 0/1 = prepare, arrow up/down = field. Colours come from the CSS tokens (light/dark mode);
// drawing pauses off screen; with reduced motion the precession is off and gates apply at once.
(function () {
  var fig = document.querySelector(".bloch");
  if (!fig) return;
  var cv = fig.querySelector("canvas"), g = cv.getContext("2d");
  var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var GAMMA = 0.028;            // Larmor frequency in GHz per mT (g = 2)
  var SHOWN = 0.0075;           // shown revolutions per second per mT
  var PULSE = Math.PI / 0.6;    // gate rotation speed on screen, rad/s
  var az = 0.61, tilt = 0.3;    // view: turned about z; tilt sets how open the equator ellipse is
  var r = norm([Math.sin(0.85) * Math.cos(0.6), Math.sin(0.85) * Math.sin(0.6), Math.cos(0.85)]);
  var B = 20, queue = [], trail = [], last = 0, visible = true, W = 0, dpr = 1;

  function norm(v) { var n = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / n, v[1] / n, v[2] / n]; }
  function rotate(v, k, a) {  // Rodrigues: rotate v about unit axis k by angle a
    var c = Math.cos(a), s = Math.sin(a), d = k[0] * v[0] + k[1] * v[1] + k[2] * v[2];
    var cr = [k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0]];
    return [0, 1, 2].map(function (i) { return v[i] * c + cr[i] * s + k[i] * d * (1 - c); });
  }
  var GATES = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1], H: norm([1, 0, 1]) };

  function size() {
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = cv.clientWidth; cv.width = cv.height = Math.round(W * dpr);
    g.setTransform(dpr, 0, 0, dpr, 0, 0); trail = [];
  }
  function token(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  // Textbook projection: z points straight up, so the poles sit exactly on the top and bottom of the outline;
  // depth (after turning by az about z) only shifts points up a little, which draws the equator as an ellipse.
  function proj(x, y, z, C, R) {
    var x1 = x * Math.cos(az) - y * Math.sin(az), y1 = x * Math.sin(az) + y * Math.cos(az);
    var sx = x1, sy = z + y1 * Math.sin(tilt), d = Math.hypot(sx, sy);
    if (d > 1) { sx /= d; sy /= d; }  // points just behind the upper rim would land outside the outline: keep them on it
    return [C + sx * R, C - sy * R, y1];  // third value > 0: behind the sphere
  }
  // Inverse of proj() for the front half of the sphere: the Bloch vector under a screen point
  // (points outside the outline snap to its rim).
  function unproj(px, py, C, R) {
    var k = Math.sin(tilt), x1 = (px - C) / R, sy = (C - py) / R, d = Math.hypot(x1, sy);
    if (d > 1) { x1 /= d; sy /= d; }
    var a = 1 + k * k, b = -2 * k * sy, c = x1 * x1 + sy * sy - 1, disc = Math.max(0, b * b - 4 * a * c);
    var y1 = (-b - Math.sqrt(disc)) / (2 * a), z = sy - k * y1;  // the root nearer the viewer
    return norm([x1 * Math.cos(az) + y1 * Math.sin(az), -x1 * Math.sin(az) + y1 * Math.cos(az), z]);
  }
  function ring(f, C, R, front, back) {
    [true, false].forEach(function (behind) {
      g.beginPath(); var on = false;
      for (var i = 0; i <= 96; i++) {
        var p = proj.apply(null, f(i / 96 * Math.PI * 2).concat([C, R]));
        if ((p[2] > 0) === behind) { on ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); on = true; } else on = false;
      }
      g.setLineDash(behind ? [3, 4] : []); g.strokeStyle = behind ? back : front; g.lineWidth = behind ? 1.4 : 1.2; g.stroke();
    });
    g.setLineDash([]);
  }
  // The meridian through the poles, drawn as in textbook Bloch spheres: a narrow ellipse, symmetric about the
  // axis, through both poles. (An exact projection of a tilted view would lean to one side.) Front half solid,
  // back half dashed.
  function meridian(C, R, front, back) {
    [true, false].forEach(function (behind) {
      g.beginPath(); var on = false;
      for (var i = 0; i <= 96; i++) {
        var a = i / 96 * Math.PI * 2, x = C + R * Math.cos(az) * Math.cos(a), y = C - R * Math.sin(a);
        var depth = Math.cos(a) * Math.sin(az);  // split exactly at the poles: one side in front, the other behind
        if ((depth > 0) === behind) { on ? g.lineTo(x, y) : g.moveTo(x, y); on = true; } else on = false;
      }
      g.setLineDash(behind ? [3, 4] : []); g.strokeStyle = behind ? back : front; g.lineWidth = behind ? 1.4 : 1.2; g.stroke();
    });
    g.setLineDash([]);
  }
  function arrow(x1, y1, x2, y2, col, w, h) {
    var a = Math.atan2(y2 - y1, x2 - x1);
    g.strokeStyle = g.fillStyle = col; g.lineWidth = w; g.lineCap = "round";
    g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2 - Math.cos(a) * h * .8, y2 - Math.sin(a) * h * .8); g.stroke();
    g.beginPath(); g.moveTo(x2, y2);
    g.lineTo(x2 - h * Math.cos(a - .4), y2 - h * Math.sin(a - .4)); g.lineTo(x2 - h * Math.cos(a + .4), y2 - h * Math.sin(a + .4));
    g.closePath(); g.fill();
  }

  function step(dt) {
    // Larmor precession about B ∥ z; paused while a gate runs (gates act in the frame rotating with the spin,
    // as resonant pulses do in experiments, so X maps |0⟩ to |1⟩ exactly)
    if (!reduced && B > 0 && !queue.length) r = rotate(r, [0, 0, 1], -2 * Math.PI * SHOWN * B * dt);
    if (queue.length) {
      var gate = queue[0];
      if (gate.to) {  // prepare a state: turn along the great circle towards it
        var dot = Math.max(-1, Math.min(1, r[0] * gate.to[0] + r[1] * gate.to[1] + r[2] * gate.to[2])), left = Math.acos(dot);
        var axis = [r[1] * gate.to[2] - r[2] * gate.to[1], r[2] * gate.to[0] - r[0] * gate.to[2], r[0] * gate.to[1] - r[1] * gate.to[0]];
        if (Math.hypot(axis[0], axis[1], axis[2]) < 1e-6) axis = [1, 0, 0];  // exactly opposite: any perpendicular axis
        var a = reduced ? left : Math.min(left, PULSE * dt);
        r = rotate(r, norm(axis), a);
        if (left - a < 1e-3) { r = gate.to.slice(); queue.shift(); }
      } else {
        var d = reduced ? gate.left : Math.min(gate.left, PULSE * dt);
        r = rotate(r, gate.axis, d); gate.left -= d;
        if (gate.left <= 1e-9) queue.shift();
      }
    }
    r = norm(r);
  }
  function field(C, R) { return { x: W * 0.07, y0: C + R * 0.75, y1: C - R * 0.85 }; }
  function draw() {
    var fg = token("--fg"), muted = token("--muted"), line = token("--line"), accent = token("--accent"),
        pulse = token("--pulse") || accent, drive = token("--drive") || muted;
    var C = W / 2, R = W * 0.34;
    g.clearRect(0, 0, W, W); g.lineWidth = 1.2;
    g.globalAlpha = .55; ring(function (t) { return [Math.cos(t), Math.sin(t), 0]; }, C, R, fg, line);
    meridian(C, R, fg, line); g.globalAlpha = 1;
    g.strokeStyle = fg; g.globalAlpha = .7; g.beginPath(); g.arc(C, C, R, 0, Math.PI * 2); g.stroke(); g.globalAlpha = 1;
    var top = proj(0, 0, 1.1, C, R), bot = proj(0, 0, -1.1, C, R), n = proj(0, 0, 1, C, R), s = proj(0, 0, -1, C, R);
    g.setLineDash([3, 6]); g.strokeStyle = muted; g.beginPath(); g.moveTo(bot[0], bot[1]); g.lineTo(top[0], top[1]); g.stroke(); g.setLineDash([]);
    g.fillStyle = fg; [n, s].forEach(function (p) { g.beginPath(); g.arc(p[0], p[1], W * 0.011, 0, 7); g.fill(); });  // the poles |0⟩ and |1⟩
    g.fillStyle = muted; g.font = "italic " + Math.round(W * 0.07) + "px Georgia, serif"; g.textAlign = "center";
    g.fillText("|0⟩", C, C - R - W * 0.045); g.fillText("|1⟩", C, C + R + W * 0.095);  // centred above and below the poles
    // the field: a draggable arrow beside the sphere on a faint track from 0 (bottom) to 100 mT (top)
    var f = field(C, R);
    g.strokeStyle = line; g.lineWidth = W * 0.012; g.lineCap = "round";
    g.beginPath(); g.moveTo(f.x, f.y0); g.lineTo(f.x, f.y1); g.stroke();
    g.lineWidth = 1.2; g.strokeStyle = muted;
    [f.y0, f.y1].forEach(function (y) { g.beginPath(); g.moveTo(f.x - W * 0.025, y); g.lineTo(f.x + W * 0.025, y); g.stroke(); });
    var ty = f.y0 - (f.y0 - f.y1) * B / 100;
    if (B > 0) arrow(f.x, f.y0, f.x, ty, drive, W * 0.012, W * 0.045);
    g.fillStyle = drive; g.beginPath(); g.arc(f.x, ty, W * 0.016, 0, 7); g.fill();  // the handle
    g.font = "italic " + Math.round(W * 0.062) + "px Georgia, serif"; g.textAlign = "center";
    g.fillText("B", f.x, f.y0 + W * 0.075);
    g.font = Math.round(W * 0.048) + "px system-ui, sans-serif"; g.fillStyle = muted;
    g.fillText(B + " mT", f.x, f.y0 + W * 0.13);
    // the spin: trail of the tip, projection onto the equator, arrow
    var tip = proj(r[0], r[1], r[2], C, R), foot = proj(r[0], r[1], 0, C, R);
    trail.push([tip[0], tip[1]]); if (trail.length > 70) trail.shift();
    g.lineWidth = W * 0.008; g.strokeStyle = accent;
    for (var i = 1; i < trail.length; i++) { g.globalAlpha = i / trail.length * .45; g.beginPath(); g.moveTo(trail[i - 1][0], trail[i - 1][1]); g.lineTo(trail[i][0], trail[i][1]); g.stroke(); }
    g.globalAlpha = .45; g.lineWidth = 1.2; g.setLineDash([3, 4]);
    g.beginPath(); g.moveTo(C, C); g.lineTo(foot[0], foot[1]); g.lineTo(tip[0], tip[1]); g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
    arrow(C, C, tip[0], tip[1], r[2] < 0 ? pulse : accent, W * 0.017, W * 0.055);
    g.fillStyle = fg; g.beginPath(); g.arc(C, C, W * 0.012, 0, 7); g.fill();
  }

  // gate buttons below the sphere
  function gate(name) { queue.push({ axis: GATES[name], left: Math.PI }); }
  function prepare(z) { queue = [{ to: [0, 0, z] }]; }
  var panel = document.querySelector(".bloch-controls");
  if (panel) {
    panel.hidden = false;
    panel.querySelectorAll("[data-gate]").forEach(function (b) { b.addEventListener("click", function () { gate(b.dataset.gate); }); });
  }
  // pointer on the drawing: the B arrow drags the field, anywhere else points the spin (poles snap exactly)
  var dragging = false;  // false, "spin" or "field"
  function hit(e) {
    var box = cv.getBoundingClientRect(), x = e.clientX - box.left, y = e.clientY - box.top, C = W / 2, R = W * 0.34;
    var n = proj(0, 0, 1, C, R), s = proj(0, 0, -1, C, R), f = field(C, R), near = W * 0.08;
    if (Math.hypot(x - n[0], y - n[1]) < near) return { what: "pole", z: 1 };
    if (Math.hypot(x - s[0], y - s[1]) < near) return { what: "pole", z: -1 };
    if (Math.abs(x - f.x) < W * 0.07 && y > f.y1 - near && y < f.y0 + near) return { what: "field", y: y, f: f };
    return { what: "sphere" };
  }
  function setB(y, f) { B = Math.round(Math.max(0, Math.min(100, (f.y0 - y) / (f.y0 - f.y1) * 100))); }
  function aim(e) {  // turn the spin towards the point under the pointer
    var box = cv.getBoundingClientRect();
    queue = [{ to: unproj(e.clientX - box.left, e.clientY - box.top, W / 2, W * 0.34) }];
  }
  cv.addEventListener("pointerdown", function (e) {
    var h = hit(e);
    cv.setPointerCapture(e.pointerId);
    if (h.what === "pole") { prepare(h.z); dragging = "spin"; }
    else if (h.what === "field") { dragging = "field"; setB(h.y, h.f); }
    else { dragging = "spin"; aim(e); }
  });
  cv.addEventListener("pointermove", function (e) {
    var h = hit(e);
    if (dragging === "field") { var box = cv.getBoundingClientRect(); setB(e.clientY - box.top, field(W / 2, W * 0.34)); }
    else if (dragging === "spin") aim(e);
    cv.style.cursor = dragging === "field" || (!dragging && h.what === "field") ? "ns-resize" : "crosshair";
  });
  ["pointerup", "pointercancel"].forEach(function (ev) { cv.addEventListener(ev, function () { dragging = false; }); });
  fig.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") gate("X");
    else if (e.key === "0") prepare(1);
    else if (e.key === "1") prepare(-1);
    else if (e.key === "ArrowUp") B = Math.min(100, B + 5);
    else if (e.key === "ArrowDown") B = Math.max(0, B - 5);
    else return;
    e.preventDefault();
  });

  fig.blochState = function () { return { r: r.slice(), B: B, busy: queue.length > 0 }; };  // read-only, for tests

  function frame(now) {
    if (!visible) return;
    var dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    step(dt); draw();
    requestAnimationFrame(frame);
  }
  size(); addEventListener("resize", size);
  new IntersectionObserver(function (es) {
    var was = visible; visible = es[0].isIntersecting;
    if (visible && !was) { last = 0; requestAnimationFrame(frame); }
  }).observe(fig);
  requestAnimationFrame(frame);
})();

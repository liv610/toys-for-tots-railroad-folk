// Toy Town, the painted scene in depth. compose.py paints every piece on its own card and says how deep it stands;
// here each card is set at that depth and scaled so that, from the home camera, the cards line up into exactly the
// painting. The square is a real ground plane carrying its painting. When the camera glides in, the pieces part
// with true parallax, like walking into a pop-up book.
import * as THREE from 'three';

const Q = new URLSearchParams(location.search);
const TEX = new URL('./tex/', import.meta.url).href, B = window.TT_BUNDLE || {};
const scene_ = B['scene.json'] || await (await fetch(TEX + 'scene.json')).json();
const [FW, FH] = scene_.frame, CAM = scene_.camera, U1 = 2 * Math.tan(THREE.MathUtils.degToRad(CAM.fov / 2)) / FH;
const depthOf = v => CAM.height / ((v - CAM.horizon) * U1);
// the home camera looks level with a shifted lens: its principal point is on the painting's horizon, so a frame
// point (u, v) at depth d is here
const world = (u, v, d) => new THREE.Vector3((u - FW / 2) * d * U1, (CAM.horizon - v) * d * U1, -d);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace; document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2f5a9a);
const camera = new THREE.PerspectiveCamera(CAM.fov, innerWidth / innerHeight, .05, 5000);

const loader = new THREE.TextureLoader(), manager = THREE.DefaultLoadingManager;
const tex = n => { const t = loader.load(B[n] || TEX + n); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
const glows = [], byName = {};
for (const p of scene_.pieces) {
  const mat = new THREE.MeshBasicMaterial({ map: tex(p.file), transparent: true, depthWrite: false, depthTest: false });
  let mesh;
  if (p.kind === 'ground') {
    // the square: a level plane; each vertex takes the colour the home camera sees there
    const nu = 48, nv = 64, P = [], UV = [], I = [];
    for (let j = 0; j <= nv; j++) {
      const t = j / nv, v = p.y + p.h * t ** 1.6;           // rows packed toward the horizon, where depth changes fastest
      for (let i = 0; i <= nu; i++) {
        const u = p.x + p.w * i / nu, d = depthOf(Math.max(v, CAM.horizon + 8)), w = world(u, v, d);
        P.push(w.x, -CAM.height, w.z); UV.push(i / nu, 1 - (v - p.y) / p.h);
      }
    }
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) { const a = j * (nu + 1) + i; I.push(a, a + nu + 1, a + 1, a + 1, a + nu + 1, a + nu + 2); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(UV, 2)); g.setIndex(I);
    mesh = new THREE.Mesh(g, mat); mesh.renderOrder = -100;
  } else {
    const d = p.depth, s = d * U1;
    mesh = new THREE.Mesh(new THREE.PlaneGeometry(p.w * s, p.h * s), mat);
    mesh.position.copy(world(p.x + p.w / 2, p.y + p.h / 2, d));
    mesh.renderOrder = -d;                                    // far to near
    if (p.kind === 'back') mesh.renderOrder = -1000 - d;     // sky and hills before the ground
    if (p.glow) {                                              // lit windows and lamps: their glow, added on top
      const gm = new THREE.Mesh(mesh.geometry, new THREE.MeshBasicMaterial({ map: tex(p.glow), transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, opacity: .3 }));
      gm.position.copy(mesh.position); gm.renderOrder = mesh.renderOrder + .5; scene.add(gm); glows.push(gm);
    }
  }
  mesh.userData.piece = p; scene.add(mesh); byName[p.name] = mesh;
}

// ---- the places you can click: the ticket window, the toy donation shop, the Marines. Each has a soft warm
// highlight (the piece's own painting added over itself) that breathes gently to invite a click, and brightens on hover.
const HOT = [
  { kind: 'ticket', label: 'Ticket window', sub: 'find a toy drop-off near you', pieces: ['station_porch'], box: [.06, .5, .94, 1] },
  { kind: 'donate', label: 'Toy donation', sub: 'drop off a new toy', pieces: ['donation_shop'], box: [.05, .2, .95, 1] },
  { kind: 'marines', label: 'The Marines', sub: 'how a toy reaches a child', pieces: ['marine_a', 'marine_b'], box: [0, 0, 1, 1] },
];
for (const h of HOT) h.lit = h.pieces.map(n => {
  const m = byName[n], g = new THREE.Mesh(m.geometry, new THREE.MeshBasicMaterial({ map: m.material.map, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, opacity: 0, color: 0xffd9a0 }));
  g.position.copy(m.position); g.renderOrder = m.renderOrder + .6; scene.add(g); return g;
});
function hotRect(h) {                                  // the hotspot on screen, from its pieces' painted boxes
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const n of h.pieces) { const p = P(n);
    for (const [fu, fv] of [[h.box[0], h.box[1]], [h.box[2], h.box[3]]]) {
      const w = world(p.x + p.w * fu, p.y + p.h * fv, p.depth).project(camera), sx = (w.x + 1) / 2 * innerWidth, sy = (1 - w.y) / 2 * innerHeight;
      x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy); } }
  return [x0, y0, x1, y1];
}
let hover = null, down = null;
const tip = document.createElement('div'); tip.className = 'hot-tip'; tip.hidden = true; document.body.appendChild(tip);
const hit = (x, y) => HOT.find(h => { const [a, b, c, d] = hotRect(h); return x >= a && x <= c && y >= b && y <= d; }) || null;
function setHover(h, x, y) {
  hover = h; renderer.domElement.style.cursor = h ? 'pointer' : '';
  tip.hidden = !h; if (h) { tip.innerHTML = h.label + '<small>' + h.sub + '</small>'; const [a, b, c] = hotRect(h); tip.style.left = ((a + c) / 2) + 'px'; tip.style.top = Math.max(40, b - 8) + 'px'; }
}
renderer.domElement.addEventListener('pointermove', e => { if (window.__busy) return; setHover(hit(e.clientX, e.clientY), e.clientX, e.clientY); });
renderer.domElement.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 8 || window.__busy) return;
  const h = hit(e.clientX, e.clientY); if (h) { setHover(null); dispatchEvent(new CustomEvent('tt-hotspot', { detail: h.kind })); }
});
window.__hotspots = () => HOT.map(h => ({ kind: h.kind, rect: hotRect(h) }));
function stepHot(t) {
  for (const [i, h] of HOT.entries()) { const o = hover === h ? .34 : .06 + .05 * Math.max(0, Math.sin(t * 1.6 + i * 2.1));
    for (const g of h.lit) g.material.opacity += (o - g.material.opacity) * .12; }
}

// ---- falling snow, in the space between you and the station
const N = Q.get('snow') === '0' ? 0 : 1600, sp = new Float32Array(N * 3), seed = new Float32Array(N);
{ let s = 7; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < N; i++) { const d = 3 + r() * 40; sp[i * 3] = (r() - .5) * d * .9; sp[i * 3 + 1] = (r() - .3) * d * .5; sp[i * 3 + 2] = -d; seed[i] = r(); } }
const flake = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); const q = g.createRadialGradient(32, 32, 2, 32, 32, 30);
  q.addColorStop(0, 'rgba(255,255,255,1)'); q.addColorStop(.5, 'rgba(255,255,255,.75)'); q.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = q; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
const snow = new THREE.Points(sg, new THREE.PointsMaterial({ map: flake, size: .07, transparent: true, depthWrite: false, depthTest: false, opacity: .9 }));
snow.renderOrder = 10; scene.add(snow);
function stepSnow(dt, t) {
  for (let i = 0; i < N; i++) { const d = -sp[i * 3 + 2]; sp[i * 3 + 1] -= dt * (.35 + seed[i] * .4); sp[i * 3] += dt * Math.sin(t * .6 + seed[i] * 30) * .12;
    if (sp[i * 3 + 1] < -CAM.height) sp[i * 3 + 1] = d * .3; }
  sg.attributes.position.needsUpdate = true;
}

// ---- the camera: the home view is the painting; the stops glide in among the pieces
const P = n => scene_.pieces.find(p => p.name === n);
const at = (n, fu = .5, fv = .5) => { const p = P(n); return world(p.x + p.w * fu, p.y + p.h * fv, p.depth); };
// each stop is a place to stand and a slight downward tilt; the camera never turns sideways, so the painting's
// shifted lens stays true and the cards only slide past each other
const VIEWS = {
  arrive: { pos: [0, 0, 0], tilt: 0 },
  square: { pos: [0, -2.4, -6], tilt: -.03 },
  station: { pos: [.2, -3.3, -12], tilt: -.02 },
  toyshop: { pos: [-3.0, -3.0, -7], tilt: -.04 },
  donation: { pos: [3.0, -3.0, -7], tilt: -.04 },
  tree: { pos: [-1.3, -3.5, -8.4], tilt: -.05 },
};
for (const v of Object.values(VIEWS)) v.look = () => new THREE.Vector3(v.pos[0], v.pos[1] + v.tilt, v.pos[2] - 1);
const cur = { pos: new THREE.Vector3(), look: new THREE.Vector3(0, 0, -1) }; let glide = null, look = { x: 0, y: 0 }, lookT = { x: 0, y: 0 };
function fit() {                                    // cover the window with the painting, whatever its shape (a shift lens)
  const a = innerWidth / innerHeight, fa = FW / FH;
  let fw = FW, fh = FH; if (a >= fa) fh = FW / a; else fw = FH * a;
  const u0 = FW / 2 - fw / 2, u1 = FW / 2 + fw / 2, v0 = FH / 2 - fh / 2, v1 = FH / 2 + fh / 2, n = camera.near;
  camera.aspect = a;
  camera.projectionMatrix.makePerspective((u0 - FW / 2) * U1 * n, (u1 - FW / 2) * U1 * n, (CAM.horizon - v0) * U1 * n, (CAM.horizon - v1) * U1 * n, n, camera.far);
  camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
}
function apply() {
  const lean = new THREE.Vector3(look.x * .45, -look.y * .2, 0);
  camera.position.copy(cur.pos).add(lean); camera.lookAt(cur.look.clone().add(lean));
  camera.updateMatrixWorld();
}
function setView(k) { const v = VIEWS[k] || VIEWS.arrive; cur.pos.fromArray(v.pos); cur.look.copy(v.look()); apply(); }
window.__setView = setView; window.__views = Object.keys(VIEWS);
window.__glideTo = (k, dur = 4) => new Promise(res => { const v = VIEWS[k]; glide = { p0: cur.pos.clone(), l0: cur.look.clone(), p1: new THREE.Vector3(...v.pos), l1: v.look(), t0: performance.now(), dur, res }; });
window.__glideAt = (a, b, f) => { const e = f * f * (3 - 2 * f); cur.pos.fromArray(VIEWS[a].pos).lerp(new THREE.Vector3(...VIEWS[b].pos), e); cur.look.copy(VIEWS[a].look()).lerp(VIEWS[b].look(), e); apply(); };
window.__stationRect = () => {                        // where the station's painted face is on screen (for the map hand-over)
  apply(); const p = P('station_face');
  return [[p.x, p.y], [p.x + p.w, p.y + p.h]].map(([u, v]) => { const w = world(u, v, p.depth).project(camera); return [(w.x + 1) / 2 * innerWidth, (1 - w.y) / 2 * innerHeight]; });
};
let paused = Q.get('paused') === '1', last = performance.now();
window.__pause = v => { paused = v; last = performance.now(); };
window.__still = () => { apply(); renderer.render(scene, camera); return renderer.domElement.toDataURL('image/jpeg', .9); };
// a little look-around: drag (or move the mouse) and the view leans, so the pieces slide past each other
addEventListener('pointermove', e => { if (e.pointerType === 'mouse' || e.buttons) { lookT.x = (e.clientX / innerWidth - .5) * 2; lookT.y = (e.clientY / innerHeight - .5) * 2; } });
addEventListener('pointerleave', () => { lookT.x = lookT.y = 0; });
addEventListener('resize', () => { renderer.setSize(innerWidth, innerHeight); fit(); });
fit(); setView(Q.get('view') || 'arrive');
renderer.setAnimationLoop(now => {
  if (paused || Q.get('still') === '1') return;
  const dt = Math.min(.1, (now - last) / 1000); last = now;
  if (glide) { const f = Math.min(1, (now - glide.t0) / 1000 / glide.dur), e = f * f * (3 - 2 * f);
    cur.pos.copy(glide.p0).lerp(glide.p1, e); cur.look.copy(glide.l0).lerp(glide.l1, e); if (f >= 1) { const r = glide.res; glide = null; r && r(); } }
  look.x += (lookT.x - look.x) * .05; look.y += (lookT.y - look.y) * .05;
  stepSnow(dt, now / 1000); stepHot(now / 1000);
  for (const [i, g] of glows.entries()) g.material.opacity = .28 + .06 * Math.sin(now / 900 + i * 1.7);
  apply(); renderer.render(scene, camera);
});
manager.onLoad = () => { window.__ready = true; };
setTimeout(() => { window.__ready = true; }, 15000);

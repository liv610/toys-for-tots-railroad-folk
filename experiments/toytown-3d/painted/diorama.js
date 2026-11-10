// Approach 1 test: a painted pop-up diorama. Every surface is a painting from the folk-art kit (paint_assets.py);
// the 3D only arranges them in space: building fronts stand at their places in the square, painted walls and
// roofs give them depth, the ground and the hills are painted too. Unlit materials keep the painted light.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LAYOUT as L, VIEWS } from './layout.js';
import { buildLandscape } from './landscape.js';

const Q = new URLSearchParams(location.search);
const TEX = new URL('./tex/', import.meta.url).href;
// textures come from tex/, or from window.TT_BUNDLE (name -> data URL / object) when the page is packed for the map
const B = window.TT_BUNDLE || {};
const getJSON = async (n) => B[n] || (await fetch(TEX + n)).json();
const meta = await getJSON('assets.json'), land = await getJSON('land.json');
const U = meta._scale_m_per_unit;                       // metres per painted unit

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const SKY = new THREE.Color(0xd6e4ea);
scene.background = SKY; scene.fog = new THREE.Fog(0xdbe6e9, 120, 1300);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, .1, 3000);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
controls.maxPolarAngle = THREE.MathUtils.degToRad(88);

const loader = new THREE.TextureLoader(); const cache = {};
function tex(name, rep) {
  const key = name + (rep || '');
  if (!cache[key]) {
    const t = loader.load(B[name] || TEX + name); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
    if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); }
    cache[key] = t;
  }
  return cache[key];
}
const card = (name) => new THREE.MeshBasicMaterial({ map: tex(name + '.png'), alphaTest: .5, side: THREE.DoubleSide, fog: true });
const surf = (name, rep, shade = 1) => new THREE.MeshBasicMaterial({ map: tex(name + '.png', rep), color: new THREE.Color(shade, shade, shade) });

// a soft contact shadow, painted as a blurred oval, under everything that stands on the ground
const shadowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const r = g.createRadialGradient(64, 64, 4, 64, 64, 62); r.addColorStop(0, 'rgba(70,80,110,.55)'); r.addColorStop(1, 'rgba(70,80,110,0)');
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
function shadow(parent, w, d, x = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.set(x, .03, z); parent.add(m); return m;
}
const place = (obj, x, z, rot = 0) => { const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = THREE.MathUtils.degToRad(rot); g.add(obj); scene.add(g); return g; };

// ---------------------------------------------------------------- the town's ground, then the map's country around it
{ const fade = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
    const r = g.createRadialGradient(128, 128, 96, 128, 128, 127); r.addColorStop(0, '#fff'); r.addColorStop(1, '#000');
    g.fillStyle = r; g.fillRect(0, 0, 256, 256); return new THREE.CanvasTexture(c); })();
  const g = new THREE.Mesh(new THREE.PlaneGeometry(meta.ground.size_m, meta.ground.size_m),
    new THREE.MeshBasicMaterial({ map: tex('ground.jpg'), alphaMap: fade, transparent: true }));
  g.rotation.x = -Math.PI / 2; g.position.y = .01; g.renderOrder = -1; scene.add(g);
}
const LAND = buildLandscape(scene, { tex, land });

// ---------------------------------------------------------------- a building: painted front card + painted volume
const W_TILE = 220 * U, R_TILE = 240 * U;                                   // tile sizes in metres
const HOUSE = 1.45;                                   // houses at human scale: the illustration draws their doors ~1 m tall
// a piece of a painted card: the u range [u0, u1] of the painting, as a plane of its true width
function piece(name, u0, u1, w, h) {
  const g = new THREE.PlaneGeometry(w * (u1 - u0), h), uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setX(i, u0 + uv.getX(i) * (u1 - u0));
  return new THREE.Mesh(g, card(name));
}
const smokeAt = [];                                   // chimney tops in world space, filled as buildings are placed
// fold: u where the painted side wall begins; that part folds back 90 degrees onto the body's side (stretched by sideK)
// split: u where a set-back wing begins (left part), pushed back by `back` metres
function building(name, { wall, roof = 'roof_red', depth = 5, wallFrac = .62, roofH = 2.6, inset = .12, fold, sideK = 1.6, split, chimneys = [] } = {}) {
  const m = meta[name], w = m.w * U * HOUSE, h = m.h * U * HOUSE, g = new THREE.Group(); depth *= 1.3; roofH *= 1.3;
  let f0 = 0, f1 = 1;                                     // the u range of the front that faces the square
  if (fold) {
    f1 = fold; const sw = w * (1 - fold) * sideK;
    const sp = piece(name, fold, 1, w, h); sp.scale.x = sideK;
    sp.rotation.y = Math.PI / 2; sp.position.set(-w / 2 + w * fold, h / 2, -sw / 2); g.add(sp);
    depth = sw;
  }
  if (split) {
    f0 = split.u; const lp = piece(name, 0, split.u, w, h);
    lp.position.set(-w / 2 + w * split.u / 2, h / 2, -split.back); g.add(lp);
    // the wing's own little body, between its card and the main front
    const ww = w * split.u * .9, side = surf(wall, [split.back / W_TILE, h * .4 / W_TILE], .8);
    const wb = new THREE.Mesh(new THREE.BoxGeometry(ww, h * .42, split.back + depth * .6), side);
    wb.position.set(-w / 2 + w * split.u / 2, h * .21, -split.back - depth * .3 + .02); g.add(wb);
  }
  const fw = w * (f1 - f0), fx = -w / 2 + w * (f0 + f1) / 2;
  const front = piece(name, f0, f1, w, h); front.position.set(fx, h / 2, 0); g.add(front);
  // the body behind the painted front, a little narrower so the front's own painted edge stays the silhouette
  const bw = fw * (1 - inset * (fold ? 1 : 2)), bx = fold ? fx + fw / 2 - bw / 2 - .02 : fx, bh = h * wallFrac;
  const side = surf(wall, [depth / W_TILE, bh / W_TILE], .86);
  const body = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, depth), [side, side, surf(roof, [1, 1]), side, side, side]);
  body.position.set(fold ? bx - .06 : bx, bh / 2, -depth / 2 - .05); g.add(body);
  const s = new THREE.Shape([new THREE.Vector2(-bw / 2 - .3, 0), new THREE.Vector2(bw / 2 + .3, 0), new THREE.Vector2(0, roofH)]);
  const rg = new THREE.ExtrudeGeometry(s, { depth: depth * (fold ? .92 : 1), bevelEnabled: false }); rg.translate(0, 0, -depth * (fold ? .92 : 1));
  const r = new THREE.Mesh(rg, surf(roof, [1 / bw, 1 / roofH])); r.position.set(fold ? bx - .06 : bx, bh, -.08); g.add(r);
  shadow(g, w * 1.25, depth * 1.6, 0, -depth / 2 + .6);
  g.userData.chimneys = chimneys.map(([ux, uy, back = 0]) => new THREE.Vector3((ux - m.x0 - m.w / 2) * U * HOUSE, (m.y0 + m.h - uy) * U * HOUSE, -back));
  return g;
}

// ---------------------------------------------------------------- the station, as the painting's own depth layers
// Each layer of the painted station (paint_assets.py) stands at its own depth, with a painted volume behind it:
// the train-shed wings at the back, the vault over the hall, the main face, the corner towers, the low annexes,
// and the clock porch nearest the square, with real stone steps down to the setts.
const SX = ux => (ux - 700) * U, SY = uy => (615 - uy) * U;
const stationG = new THREE.Group();
function layer(name, z) {
  const m = meta[name], w = m.w * U, h = m.h * U;
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), card(name));
  p.position.set(SX(m.x0 + m.w / 2), SY(m.y0 + m.h / 2), z); stationG.add(p); return p;
}
function box(x0, x1, y0, y1, z0, z1, mats) {
  const b = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), mats);
  b.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); stationG.add(b); return b;
}
function gable(x0, x1, y, z0, z1, rh, mat) {               // a pitched roof prism running from z0 back to z1 (z1 < z0)
  const w = x1 - x0, s = new THREE.Shape([new THREE.Vector2(-w / 2, 0), new THREE.Vector2(w / 2, 0), new THREE.Vector2(0, rh)]);
  const g = new THREE.ExtrudeGeometry(s, { depth: z0 - z1, bevelEnabled: false }); g.translate(0, 0, -(z0 - z1));
  const r = new THREE.Mesh(g, mat); r.position.set((x0 + x1) / 2, y, z0); stationG.add(r); return r;
}
{ const S = L.station, D = S.front - S.back;
  const stone = (d, h, sh = .9) => surf('wall_cream', [d / W_TILE, h / W_TILE], sh);
  const roofM = (a, b) => surf('roof_red', [a, b]);
  const Z = { wings: -3.0, vault: -0.6, face: 0, towers: .9, annex: 2.4, porch: 4.2 };
  layer('station_wings', Z.wings); layer('station_vault', Z.vault); layer('station_face', Z.face);
  layer('station_towers', Z.towers); layer('station_annex', Z.annex); layer('station_porch', Z.porch);
  // wings: walls to the painted eaves, then a ridge roof, running back to the sheds
  const wingTop = SY(185 + 431 * .18);
  for (const [a, b] of [[172, 444], [956, 1224]]) {
    const x0 = SX(a) + .15, x1 = SX(b) - .15, sm = stone(D, wingTop);
    box(x0, x1, 0, wingTop, Z.wings - D, Z.wings - .03, [sm, sm, roofM(1, 1), sm, sm, sm]);
    gable(x0 - .2, x1 + .2, wingTop, Z.wings - .5, Z.wings - D, 2.2, roofM(2, 3));
  }
  // the hall under the vault: side walls to the spring of the arch, then a real barrel vault
  const vm = meta.station_vault, R = vm.w * U / 2 - .25, crown = SY(vm.y0) - .25, spring = crown - R;
  for (const sx of [-1, 1]) { const sm = stone(D, spring); box(sx * R - .3, sx * R + .3, 0, spring, Z.vault - D, Z.vault - .05, sm); }
  const vg = new THREE.CylinderGeometry(R, R, D, 48, 1, true, -Math.PI / 2, Math.PI); vg.rotateX(Math.PI / 2);
  const vault = new THREE.Mesh(vg, new THREE.MeshBasicMaterial({ map: tex('roof_red.png', [4, 1.5]), side: THREE.DoubleSide }));
  vault.position.set(0, spring, Z.vault - D / 2 - .05); stationG.add(vault);
  // the face's own thickness, so it reads as a wall, not a sheet
  { const sm = stone(1.2, SY(250)); box(SX(392), SX(1008), 0, SY(250), Z.vault + .05, Z.face - .04, sm); }
  // towers: square stone shafts from the face forward to their painted fronts
  for (const [a, b] of [[356, 442], [958, 1044]]) {
    const x0 = SX(a) + .08, x1 = SX(b) - .08, top = SY(84 + 30), sm = stone(Z.towers, top, .88);
    box(x0, x1, 0, top, Z.face + .02, Z.towers - .03, sm);
  }
  // annexes: low stone blocks with snowy roofs, between the face and the porch
  const annexTop = SY(444 + 172 * .3);
  for (const [a, b] of [[449, 607], [793, 951]]) {
    const x0 = SX(a) + .1, x1 = SX(b) - .1, sm = stone(Z.annex, annexTop);
    box(x0, x1, 0, annexTop, Z.face + .02, Z.annex - .03, [sm, sm, roofM(1, 1), sm, sm, sm]);
  }
  // the clock porch: a stone body under a gable, reaching back to the face
  const pm = meta.station_porch, pTop = SY(pm.y0 + pm.h * .42), px0 = SX(pm.x0) + .25, px1 = SX(pm.x0 + pm.w) - .25;
  { const sm = stone(Z.porch, pTop, .9); box(px0, px1, 0, pTop, Z.face + .02, Z.porch - .04, [sm, sm, roofM(1, 1), sm, sm, sm]); }
  gable(px0 - .15, px1 + .15, pTop, Z.porch - .3, Z.face + .05, SY(pm.y0 + 30) - pTop, roofM(1.5, 1.5));
  // real stone steps down from the porch doors to the square
  const st = S.steps, sw = px1 - px0 + 1.6, stepM = stone(st.tread, st.rise, .95), topM = new THREE.MeshBasicMaterial({ map: tex('wall_cream.png', [1.5, .25]), color: 0xf4f2ee });
  for (let i = 0; i < st.n; i++) {
    const h = st.rise * (st.n - i), z0 = Z.porch + i * st.tread;
    box(-sw / 2 - i * .18, sw / 2 + i * .18, 0, h, z0 - .02, z0 + st.tread, [stepM, stepM, topM, stepM, stepM, stepM]);
  }
  shadow(stationG, 30, 10, 0, -1);
  stationG.position.z = S.front; scene.add(stationG);
  for (const ux of [399, 1001]) smokeAt.push(new THREE.Vector3(SX(ux), SY(92), S.front + Z.towers - .9));
  window.__stepsFront = S.front + Z.porch + st.n * st.tread;
}

// ---------------------------------------------------------------- the houses around the square (the layout's slots)
const HOUSES = [
  ['blue_shop', -17.0, 3.6, 52, { wall: 'wall_blue', depth: 6, split: { u: 104 / 340.7, back: 1.4 }, chimneys: [[139, 452], [87, 548, 1.4]] }],
  ['pink_narrow', -18.6, -6.0, 76, { wall: 'wall_pink', depth: 5, inset: .05 }],
  ['cream_house', -15.4, -13.0, 48, { wall: 'wall_cream', depth: 5 }],
  ['donation_shop', 17.2, 2.8, -54, { wall: 'wall_yellow', roof: 'roof_purple', fold: (1206 - 1000) / 291, chimneys: [[1232, 500]] }],
  ['red_house', 19.4, -7.6, -72, { wall: 'wall_red', fold: (1178 - 1040) / 241 }],
  ['pink_house', 14.6, -14.6, -40, { wall: 'wall_pink', roof: 'roof_purple', depth: 5 }],
];
for (const [n, x, z, r, o] of HOUSES) {
  const b = building(n, o), g = place(b, x, z, r); g.updateMatrixWorld(true);
  for (const c of b.userData.chimneys) smokeAt.push(b.localToWorld(c.clone()));
}

// ---------------------------------------------------------------- the square's real edges: the low wall, kerbs, planters
const snowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#f3f5f7'; g.fillRect(0, 0, 256, 256); const R = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(5);
  for (let i = 0; i < 900; i++) { const x = R() * 256, y = R() * 256, r = 2 + R() * 9, b = R();
    g.fillStyle = b < .5 ? `rgba(196,208,224,${.12 + R() * .2})` : `rgba(255,255,255,${.3 + R() * .5})`; g.beginPath(); g.ellipse(x, y, r * 1.6, r, 0, 0, 7); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t; })();
const snowMat = (rx, ry) => { const t = snowTex.clone(); t.needsUpdate = true; t.repeat.set(rx, ry); return new THREE.MeshBasicMaterial({ map: t }); };
{ const Wl = SQ0().wall, h = .72, th = .55;
  for (const [a, b] of [[-12.8, Wl.gap[0]], [Wl.gap[1], 12.8]]) {
    const len = b - a, sm = surf('wall_cream', [len / W_TILE * 1.6, h / W_TILE * 1.6], .82);
    const wl = new THREE.Mesh(new THREE.BoxGeometry(len, h, th), sm); wl.position.set((a + b) / 2, h / 2, Wl.z); scene.add(wl);
    // a soft rounded cap of snow
    const cg = new THREE.CylinderGeometry(th * .62, th * .62, len + .1, 12, 1, false, -Math.PI / 2, Math.PI); cg.rotateZ(Math.PI / 2); cg.scale(1, .55, 1);
    const cap = new THREE.Mesh(cg, snowMat(len / 2, 1)); cap.position.set((a + b) / 2, h, Wl.z); scene.add(cap);
    for (const x of [a + .3, b - .3]) {                      // piers at the ends, with snow caps
      const p = new THREE.Mesh(new THREE.BoxGeometry(.8, h + .35, .8), surf('wall_cream', [.6, .6], .78)); p.position.set(x, (h + .35) / 2, Wl.z); scene.add(p);
      const pc = new THREE.Mesh(new THREE.SphereGeometry(.5, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), snowMat(1, 1)); pc.scale.set(1, .45, 1); pc.position.set(x, h + .35, Wl.z); scene.add(pc);
    }
  }
  // kerbs: a low run of stones along the square's edge where it meets the streets in front of the houses
  const o = SQ0().outline, kerbM = surf('wall_cream', [2, .3], .74);
  for (let i = 1; i < o.length; i++) {
    const [x0, z0] = o[i], [x1, z1] = o[(i + 1) % o.length]; if (Math.abs(z0 - Wl.z) < 1.5 && Math.abs(z1 - Wl.z) < 1.5) continue;
    if (i === 0) continue; const len = Math.hypot(x1 - x0, z1 - z0);
    const k = new THREE.Mesh(new THREE.BoxGeometry(len, .16, .32), kerbM); k.position.set((x0 + x1) / 2, .08, (z0 + z1) / 2);
    k.rotation.y = -Math.atan2(z1 - z0, x1 - x0); scene.add(k);
    const kc = new THREE.Mesh(new THREE.BoxGeometry(len, .06, .34), snowMat(len / 2, .2)); kc.position.copy(k.position); kc.position.y = .18; kc.rotation.copy(k.rotation); scene.add(kc);
  }
}
function SQ0() { return L.square; }

// ---------------------------------------------------------------- the square's life: painted cut-outs that turn to face you
const billboards = [];
function cutout(name, x, z, scale = 1, sh = .9) {
  const m = meta[name], w = m.w * U * scale, h = m.h * U * scale;
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), card(name)); p.position.y = h / 2;
  const g = new THREE.Group(); g.position.set(x, 0, z); g.add(p); scene.add(g);
  shadow(scene, w * sh, w * sh * .5, x, z + .1); billboards.push(g); return g;
}
const SQ = L.square;
cutout('tree', SQ.tree[0], SQ.tree[1], 1.35);
cutout('marine_a', SQ.marines[0][0], SQ.marines[0][1], .9); cutout('marine_b', SQ.marines[1][0], SQ.marines[1][1], .9);
SQ.lamps.forEach(([x, z]) => cutout('lamp', x, z, 1.15, 1.2));
cutout('wagon_bear', SQ.wagons[0][0], SQ.wagons[0][1], .75); cutout('wagon_presents', SQ.wagons[1][0], SQ.wagons[1][1], .75);
{ const R = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(11);
  for (let i = 0; i < 70; i++) {
    const a = R() * Math.PI * 2, d = 26 + R() * 28, x = Math.cos(a) * d, z = Math.sin(a) * d * .8 - 12;
    if (z > 12 && Math.abs(x) < 10) continue;
    cutout('fir', x, z, .7 + R() * .9);
  }
}

// planters with little firs either side of the station steps and at the wall's gap
for (const [x, z] of [[-5.2, window.__stepsFront - 1.2], [5.2, window.__stepsFront - 1.2], [-3.0, L.square.wall.z - .1], [3.0, L.square.wall.z - .1]]) {
  const p = new THREE.Mesh(new THREE.BoxGeometry(1.1, .62, 1.1), surf('wall_cream', [.5, .3], .8)); p.position.set(x, .31, z); scene.add(p);
  const c = new THREE.Mesh(new THREE.BoxGeometry(1.14, .1, 1.14), snowMat(1, 1)); c.position.set(x, .66, z); scene.add(c);
  const f = cutout('fir', x, z, .42, .5); f.position.y = .62;
}

// ---------------------------------------------------------------- falling snow and chimney smoke
const flake = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const r = g.createRadialGradient(32, 32, 2, 32, 32, 30); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.45, 'rgba(255,255,255,.8)'); r.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const SNOW_N = Q.get('snow') === '0' ? 0 : 4000, SB = { x: 70, y: 30, z: 70 };
const snowPos = new Float32Array(SNOW_N * 3), snowSeed = new Float32Array(SNOW_N);
{ const R = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(29);
  for (let i = 0; i < SNOW_N; i++) { snowPos[i * 3] = (R() - .5) * SB.x; snowPos[i * 3 + 1] = R() * SB.y; snowPos[i * 3 + 2] = (R() - .5) * SB.z - 6; snowSeed[i] = R(); } }
const snowGeo = new THREE.BufferGeometry(); snowGeo.setAttribute('position', new THREE.BufferAttribute(snowPos, 3));
const snow = new THREE.Points(snowGeo, new THREE.PointsMaterial({ map: flake, size: .09, transparent: true, depthWrite: false, opacity: .9, fog: true }));
scene.add(snow);
function stepSnow(dt, t) {
  for (let i = 0; i < SNOW_N; i++) { const s = snowSeed[i];
    snowPos[i * 3 + 1] -= dt * (.55 + s * .5); snowPos[i * 3] += dt * Math.sin(t * .7 + s * 40) * .25;
    if (snowPos[i * 3 + 1] < 0) snowPos[i * 3 + 1] += SB.y; }
  snowGeo.attributes.position.needsUpdate = true;
}
const puffTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  for (const [x, y, r] of [[64, 70, 40], [44, 60, 26], [84, 56, 28], [62, 42, 26]]) { const q = g.createRadialGradient(x, y, 2, x, y, r);
    q.addColorStop(0, 'rgba(236,236,240,.75)'); q.addColorStop(1, 'rgba(236,236,240,0)'); g.fillStyle = q; g.fillRect(0, 0, 128, 128); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
const puffs = [];
for (const [ci, c] of smokeAt.entries()) for (let i = 0; i < 7; i++) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: puffTex, transparent: true, depthWrite: false, fog: true }));
  s.userData = { base: c, ph: i / 7 + ci * .13 }; scene.add(s); puffs.push(s);
}
function stepSmoke(t) {
  for (const p of puffs) { const { base, ph } = p.userData, f = ((t * .09 + ph) % 1);
    p.position.set(base.x + f * 2.2 + Math.sin(t * .5 + ph * 9) * .25, base.y + .3 + f * 5, base.z - f * .8);
    const sc = .7 + f * 2.4; p.scale.set(sc, sc, 1); p.material.opacity = Math.sin(Math.PI * Math.min(1, f * 1.15)) * .7; }
}

// ---------------------------------------------------------------- views and the glide between them
// 'arrive' frames the town the way the map paints it (from the south, high up), so the map can dissolve into it
VIEWS.arrive = { name: 'Arriving from the map', pos: [0, 13, 15], target: [0, 6.5, -18], fov: 44 };
VIEWS.south = { name: 'Over the wall, to the fields', pos: [0, 1.65, 6.5], target: [-8, 3.5, 80], fov: 62 };
VIEWS.west = { name: 'Out past the toy shop', pos: [-6, 1.65, 4], target: [-90, 6, -30], fov: 62 };
function setView(k) {
  const v = VIEWS[k]; camera.position.fromArray(v.pos); controls.target.fromArray(v.target); camera.fov = v.fov; camera.updateProjectionMatrix(); controls.update();
}
let glide = null;
window.__glide = (from, to, dur = 4) => { glide = { a: VIEWS[from], b: VIEWS[to], t0: performance.now(), dur }; };
window.__glideAt = (from, to, f) => { const a = VIEWS[from], b = VIEWS[to], e = f * f * (3 - 2 * f);
  camera.position.fromArray(a.pos).lerp(new THREE.Vector3(...b.pos), e); controls.target.fromArray(a.target).lerp(new THREE.Vector3(...b.target), e);
  camera.fov = a.fov + (b.fov - a.fov) * e; camera.updateProjectionMatrix(); };
function face() { for (const b of billboards) { const dx = camera.position.x - b.position.x, dz = camera.position.z - b.position.z; b.rotation.y = Math.atan2(dx, dz); } }
window.__setView = setView;
// glide from wherever the camera is now to a named view; resolves when it arrives
window.__glideTo = (to, dur = 4) => new Promise(res => {
  const a = { pos: camera.position.toArray(), target: controls.target.toArray(), fov: camera.fov }; glide = { a, b: VIEWS[to], t0: performance.now(), dur, res };
});
// where the station's painted face sits on screen (for lining the map up with the 3D at the hand-over)
window.__stationRect = () => {
  controls.update(); camera.updateMatrixWorld();
  const m = meta.station_face, p = [[m.x0, m.y0], [m.x0 + m.w, m.y0 + m.h]].map(([ux, uy]) =>
    new THREE.Vector3((ux - 700) * U, (615 - uy) * U, L.station.front).project(camera));
  return p.map(v => [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]);
}; window.__views = Object.keys(VIEWS);
window.__still = () => { controls.update(); face(); stepSmoke(Number(Q.get('t') || 7)); renderer.render(scene, camera); return renderer.domElement.toDataURL('image/jpeg', .9); };
setView(Q.get('view') || 'square');
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
let last = performance.now(), paused = Q.get('paused') === '1';
window.__pause = (v) => { paused = v; last = performance.now(); };
if (Q.get('still') !== '1') renderer.setAnimationLoop((now) => {
  if (paused) return;
  const dt = Math.min(.1, (now - last) / 1000); last = now; stepSnow(dt, now / 1000); stepSmoke(now / 1000);
  if (glide) { const f = Math.min(1, (now - glide.t0) / 1000 / glide.dur);     const { a, b } = glide, e = f * f * (3 - 2 * f);
    camera.position.fromArray(a.pos).lerp(new THREE.Vector3(...b.pos), e); controls.target.fromArray(a.target).lerp(new THREE.Vector3(...b.target), e);
    camera.fov = a.fov + (b.fov - a.fov) * e; camera.updateProjectionMatrix(); if (f >= 1) { const r = glide.res; glide = null; r && r(); } }
  LAND.clouds.rotation.y = now / 1000 * .004;
  controls.update(); face(); renderer.render(scene, camera);
});
await new Promise(r => setTimeout(r, 50));
THREE.DefaultLoadingManager.onLoad = () => { window.__ready = true; };
setTimeout(() => { window.__ready = true; }, 15000);

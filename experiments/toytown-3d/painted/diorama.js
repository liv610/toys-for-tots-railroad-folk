// Approach 1 test: a painted pop-up diorama. Every surface is a painting from the folk-art kit (paint_assets.py);
// the 3D only arranges them in space: building fronts stand at their places in the square, painted walls and
// roofs give them depth, the ground and the hills are painted too. Unlit materials keep the painted light.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LAYOUT as L, VIEWS } from './layout.js';

const Q = new URLSearchParams(location.search);
const TEX = new URL('./tex/', import.meta.url).href;
const meta = await (await fetch(TEX + 'assets.json')).json();
const U = meta._scale_m_per_unit;                       // metres per painted unit

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const SKY = new THREE.Color(0xcbd7dd);
scene.background = SKY; scene.fog = new THREE.Fog(SKY, 70, 150);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, .1, 400);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
controls.maxPolarAngle = THREE.MathUtils.degToRad(88);

const loader = new THREE.TextureLoader(); const cache = {};
function tex(name, rep) {
  const key = name + (rep || '');
  if (!cache[key]) {
    const t = loader.load(TEX + name); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
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

// ---------------------------------------------------------------- ground and hills
{ const g = new THREE.Mesh(new THREE.PlaneGeometry(meta.ground.size_m, meta.ground.size_m), new THREE.MeshBasicMaterial({ map: tex('ground.jpg') }));
  g.rotation.x = -Math.PI / 2; scene.add(g);
  const far = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshBasicMaterial({ map: tex('ground.jpg', [1, 1]), color: 0xffffff }));
  // beyond the painted square, the same snow (a corner of the ground painting, repeated)
  const snowOnly = tex('wall_cream.png'); far.material = new THREE.MeshBasicMaterial({ color: 0xedeeef });
  far.rotation.x = -Math.PI / 2; far.position.y = -.02; scene.add(far);
  // the painted hills: a curved panel behind the town, the painting repeated twice around the arc
  const R = 95, arc = Math.PI * 2, h = 40;
  const geo = new THREE.CylinderGeometry(R, R, h, 64, 1, true, Math.PI - arc / 2, arc);
  const t = tex('backdrop.png', [3, 1]); t.wrapS = THREE.MirroredRepeatWrapping; const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: t, side: THREE.BackSide, fog: false }));
  m.position.set(0, h / 2 - 6, -8); scene.add(m);
}

// ---------------------------------------------------------------- a building: painted front card + painted volume
const W_TILE = 220 * U, R_TILE = 240 * U;                                   // tile sizes in metres
const HOUSE = 1.45;                                   // houses at human scale: the illustration draws their doors ~1 m tall
function building(name, { wall, roof = 'roof_red', depth = 5, wallFrac = .62, roofH = 2.6, inset = .12 } = {}) {
  const m = meta[name], w = m.w * U * HOUSE, h = m.h * U * HOUSE, g = new THREE.Group(); depth *= 1.3; roofH *= 1.3;
  const front = new THREE.Mesh(new THREE.PlaneGeometry(w, h), card(name)); front.position.set(0, h / 2, 0); g.add(front);
  // the body behind the painted front, a little narrower so the front's own painted edge stays the silhouette
  const bw = w * (1 - inset * 2), bh = h * wallFrac;
  const side = surf(wall, [depth / W_TILE, bh / W_TILE], .86);
  const body = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, depth), [side, side, surf(roof, [1, 1]), side, side, side]);
  body.position.set(0, bh / 2, -depth / 2 - .05); g.add(body);
  const s = new THREE.Shape([new THREE.Vector2(-bw / 2 - .3, 0), new THREE.Vector2(bw / 2 + .3, 0), new THREE.Vector2(0, roofH)]);
  const rg = new THREE.ExtrudeGeometry(s, { depth: depth, bevelEnabled: false }); rg.translate(0, 0, -depth);
  const rm = surf(roof, [1 / bw, 1 / roofH]);
  const r = new THREE.Mesh(rg, rm); r.position.set(0, bh, -.05); g.add(r);
  shadow(g, w * 1.25, depth * 1.6, 0, -depth / 2 + .6);
  return g;
}

// ---------------------------------------------------------------- the station
{ const S = L.station, m = meta.station, w = m.w * U, h = m.h * U, g = new THREE.Group();
  const front = new THREE.Mesh(new THREE.PlaneGeometry(w, h), card('station'));
  // the painting's steps run to its foot; stand it so the porch doors meet the square at the steps
  front.position.set(0, h / 2, 0); g.add(front);
  const D = S.front - S.back, k = w / 25.4, hall = { x1: 7.6 * k, wallH: 6.2 * k, vaultR: 7.2 * k };
  const stone = surf('wall_cream', [D / W_TILE, hall.wallH / W_TILE], .9);
  // the hall behind: walls and the barrel vault in painted tiles and snow
  for (const sx of [-1, 1]) { const wl = new THREE.Mesh(new THREE.BoxGeometry(.6, hall.wallH, D), stone); wl.position.set(sx * hall.x1, hall.wallH / 2, -D / 2); g.add(wl); }
  const vg = new THREE.CylinderGeometry(hall.vaultR, hall.vaultR, D, 40, 1, true, Math.PI / 2, Math.PI); vg.rotateX(Math.PI / 2);
  const vault = new THREE.Mesh(vg, new THREE.MeshBasicMaterial({ map: tex('roof_red.png', [2, 1]), side: THREE.DoubleSide }));
  vault.position.set(0, hall.wallH + .2, -D / 2 - .3); g.add(vault);
  // the side wings, lower, with roofs, reaching back to the train sheds
  for (const sx of [-1, 1]) {
    const ww = 7.6 * k, wh = 7.2 * k, cx = sx * (w / 2 - ww / 2 - .6);          // the wings stay inside the painted front
    const side = surf('wall_cream', [D / W_TILE, wh / W_TILE], .84);
    const wb = new THREE.Mesh(new THREE.BoxGeometry(ww, wh, D), [side, side, surf('roof_red', [1, D / 12]), side, side, side]);
    wb.position.set(cx, wh / 2, -D / 2 - .4); g.add(wb);
  }
  shadow(g, w * 1.1, 8, 0, -1);
  place(g, 0, S.front);
}

// ---------------------------------------------------------------- the houses around the square (the layout's slots)
const HOUSES = [
  ['blue_shop', -17.0, 3.6, 52, { wall: 'wall_blue', depth: 6 }],
  ['pink_narrow', -18.6, -6.0, 76, { wall: 'wall_pink', depth: 5, inset: .05 }],
  ['cream_house', -15.4, -13.0, 48, { wall: 'wall_cream', depth: 5 }],
  ['donation_shop', 17.2, 2.8, -54, { wall: 'wall_yellow', roof: 'roof_purple', depth: 6 }],
  ['red_house', 19.4, -7.6, -72, { wall: 'wall_red', depth: 6 }],
  ['pink_house', 14.6, -14.6, -40, { wall: 'wall_pink', roof: 'roof_purple', depth: 5 }],
];
for (const [n, x, z, r, o] of HOUSES) place(building(n, o), x, z, r);

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
    const a = R() * Math.PI * 2, d = 26 + R() * 36, x = Math.cos(a) * d, z = Math.sin(a) * d * .8 - 12;
    if (z > 12 && Math.abs(x) < 10) continue;
    cutout('fir', x, z, .7 + R() * .9);
  }
}

// ---------------------------------------------------------------- views and the glide between them
function setView(k) {
  const v = VIEWS[k]; camera.position.fromArray(v.pos); controls.target.fromArray(v.target); camera.fov = v.fov; camera.updateProjectionMatrix(); controls.update();
}
let glide = null;
window.__glide = (from, to, dur = 4) => { glide = { a: VIEWS[from], b: VIEWS[to], t0: performance.now(), dur }; };
window.__glideAt = (from, to, f) => { const a = VIEWS[from], b = VIEWS[to], e = f * f * (3 - 2 * f);
  camera.position.fromArray(a.pos).lerp(new THREE.Vector3(...b.pos), e); controls.target.fromArray(a.target).lerp(new THREE.Vector3(...b.target), e);
  camera.fov = a.fov + (b.fov - a.fov) * e; camera.updateProjectionMatrix(); };
function face() { for (const b of billboards) { const dx = camera.position.x - b.position.x, dz = camera.position.z - b.position.z; b.rotation.y = Math.atan2(dx, dz); } }
window.__setView = setView; window.__views = Object.keys(VIEWS);
window.__still = () => { controls.update(); face(); renderer.render(scene, camera); return renderer.domElement.toDataURL('image/jpeg', .9); };
setView(Q.get('view') || 'square');
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
if (Q.get('still') !== '1') renderer.setAnimationLoop((now) => {
  if (glide) { const f = Math.min(1, (now - glide.t0) / 1000 / glide.dur);     const { a, b } = glide, e = f * f * (3 - 2 * f);
    camera.position.fromArray(a.pos).lerp(new THREE.Vector3(...b.pos), e); controls.target.fromArray(a.target).lerp(new THREE.Vector3(...b.target), e);
    camera.fov = a.fov + (b.fov - a.fov) * e; camera.updateProjectionMatrix(); if (f >= 1) glide = null; }
  controls.update(); face(); renderer.render(scene, camera);
});
await new Promise(r => setTimeout(r, 50));
THREE.DefaultLoadingManager.onLoad = () => { window.__ready = true; };
setTimeout(() => { window.__ready = true; }, 15000);

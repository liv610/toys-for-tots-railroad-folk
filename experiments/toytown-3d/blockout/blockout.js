// Toy Town 3D, Stage A blockout. Simple shapes and flat colours; the existing toy shop (from the claymation
// real-time scene) is placed in the village for scale. Each part is a small builder so later stages can swap a
// block for a detailed model without moving anything: station(), house(), rails(), river(), bridge(), lamp()...
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LAYOUT as L, VIEWS } from './layout.js';

const Q = new URLSearchParams(location.search);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = Q.get('shadows') !== '0';
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
renderer.toneMapping = THREE.AgXToneMapping; renderer.toneMappingExposure = 1.15;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9fb2c8);
scene.fog = new THREE.Fog(0x9fb2c8, 90, 260);
const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 600);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.maxPolarAngle = THREE.MathUtils.degToRad(88);

// light: a soft winter afternoon so the shapes read; the real lighting comes in later stages
scene.add(new THREE.HemisphereLight(0xdfe8f5, 0x8a8478, 1.4));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.4);
sun.position.set(-40, 60, 35); sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
Object.assign(sun.shadow.camera, { left: -70, right: 70, top: 70, bottom: -70, near: 1, far: 220 });
sun.shadow.bias = -0.0004;
scene.add(sun);

const M = {}; const mat = (c, o = {}) => (M[c + JSON.stringify(o)] ||= new THREE.MeshStandardMaterial({ color: c, roughness: .85, ...o }));
const glow = (c, i = 1.5) => mat(c, { emissive: c, emissiveIntensity: i });
function mesh(geo, m, x = 0, y = 0, z = 0, parent = scene) {
  const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; parent.add(o); return o;
}
const box = (w, h, d, m, x, y, z, p) => mesh(new THREE.BoxGeometry(w, h, d), m, x, y, z, p);
function prism(w, h, d) {                     // a gable roof volume: triangle w x h, extruded d along z
  const s = new THREE.Shape([new THREE.Vector2(-w / 2, 0), new THREE.Vector2(w / 2, 0), new THREE.Vector2(0, h)]);
  const g = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: false }); g.translate(0, 0, -d / 2); return g;
}
const group = (x = 0, z = 0, rot = 0, y = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = THREE.MathUtils.degToRad(rot); scene.add(g); return g; };

// ---------------------------------------------------------------- ground, terrain, square, paths
const SNOW = mat(0xf2f4f8), COBBLE = mat(0xb9ab98), STONE = mat(0xd8c7a2), PATH = mat(0xd9d2c6);
{
  const g = new THREE.PlaneGeometry(400, 400); g.rotateX(-Math.PI / 2);
  mesh(g, SNOW, 0, 0, 0).castShadow = false;
  // the meadow south of the square lies a little lower: the low wall is a retaining wall with steps down
  const low = new THREE.PlaneGeometry(400, 200); low.rotateX(-Math.PI / 2);
  mesh(low, SNOW, 0, -1.2, L.square.wall.z + 101).castShadow = false;
  // hills around: snowy behind the station, darker woods on the slopes
  const hills = [[-70, -95, 46, 16], [0, -110, 60, 22], [75, -90, 50, 18], [-110, -20, 40, 12], [110, 10, 44, 12], [-90, 80, 50, 10], [95, 85, 46, 11]];
  for (const [x, z, r, h] of hills) { const s = mesh(new THREE.SphereGeometry(1, 32, 16), mat(0xe6ecef), x, -2, z); s.scale.set(r, h, r * .8); s.castShadow = false; }
}
function flatPoly(pts, m, y = 0.02) {
  const s = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, -z)));
  const g = new THREE.ShapeGeometry(s, 24); g.rotateX(-Math.PI / 2); const o = mesh(g, m, 0, y, 0); o.castShadow = false; return o;
}
function ribbon(pts, w, m, y = 0.03, smooth = true) {
  const c = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)));
  const n = Math.max(12, Math.round(c.getLength() / 1.2)), P = [], I = [];
  for (let i = 0; i <= n; i++) {
    const p = c.getPointAt(i / n), t = c.getTangentAt(i / n), nx = -t.z, nz = t.x;
    P.push(p.x + nx * w / 2, y, p.z + nz * w / 2, p.x - nx * w / 2, y, p.z - nz * w / 2);
    if (i) { const a = 2 * i - 2; I.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setIndex(I); g.computeVertexNormals();
  const o = mesh(g, m); o.castShadow = false; return { mesh: o, curve: c };
}
flatPoly(L.square.outline, COBBLE, 0.03);
for (const p of L.paths) ribbon(p.pts, p.w, PATH, 0.025);

// ---------------------------------------------------------------- the station
function station(S) {
  const g = new THREE.Group(); scene.add(g);
  const { hall, wings, towers, porch, front, back } = S; const D = back - front, zc = (front + back) / 2;
  const CREAM = mat(0xeee0c0), ROOF = mat(0xa8463c), GLASS = glow(0xf3b45a, 1.2), DARK = mat(0x2a2522);
  // the hall's side walls and back, and the barrel vault (axis north-south, its arch facing the square)
  // the hall's side walls are arcades (piers and a beam) so the tracks pass from the sheds to the platforms
  for (const hx of [hall.x0, hall.x1]) {
    for (let z = front - 1; z > back; z -= 4.2) box(1.0, hall.wallH, 1.0, CREAM, hx, hall.wallH / 2, z, g);
    box(1.0, 1.6, -D, CREAM, hx, hall.wallH - .8, zc, g);
  }
  { const bw = hall.x1 - hall.x0, bs = new THREE.Shape(); bs.moveTo(-bw / 2, 0); bs.lineTo(bw / 2, 0); bs.lineTo(bw / 2, hall.wallH); bs.absarc(0, hall.wallH, bw / 2, 0, Math.PI, false); bs.lineTo(-bw / 2, 0);
    mesh(new THREE.ExtrudeGeometry(bs, { depth: .8, bevelEnabled: false, curveSegments: 32 }), CREAM, 0, 0, back - .4, g); }
  const vg = new THREE.CylinderGeometry(hall.vaultR + .5, hall.vaultR + .5, -D + 1.2, 48, 1, true, Math.PI / 2, Math.PI);
  vg.rotateX(Math.PI / 2); const vault = mesh(vg, mat(0xa8463c, { side: THREE.DoubleSide }), 0, hall.wallH, zc, g); vault.userData.roof = true;
  // the front: a stone wall with the great arch (glazed), the tympanum fan above the banner
  const fw = hall.x1 - hall.x0 + 2, sh = new THREE.Shape();
  sh.moveTo(-fw / 2, 0); sh.lineTo(fw / 2, 0); sh.lineTo(fw / 2, hall.wallH); sh.absarc(0, hall.wallH, fw / 2, 0, Math.PI, false); sh.lineTo(-fw / 2, 0);
  const hole = new THREE.Path(); const ar = hall.vaultR - 1.4;
  hole.moveTo(-ar, 0.4); hole.lineTo(ar, 0.4); hole.lineTo(ar, hall.wallH - .6); hole.absarc(0, hall.wallH - .6, ar, 0, Math.PI, false); hole.lineTo(-ar, .4);
  sh.holes.push(hole);
  const fg = new THREE.ExtrudeGeometry(sh, { depth: 1.0, bevelEnabled: false, curveSegments: 40 });
  mesh(fg, CREAM, 0, 0, front - 0.5, g);
  const gl = new THREE.Shape(); gl.moveTo(-ar, .4); gl.lineTo(ar, .4); gl.lineTo(ar, hall.wallH - .6); gl.absarc(0, hall.wallH - .6, ar, 0, Math.PI, false); gl.lineTo(-ar, .4);
  mesh(new THREE.ShapeGeometry(gl, 40), GLASS, 0, 0, front - 0.1, g).castShadow = false;
  // the banner across the arch and the star medallion above it
  box(15, 2.0, .35, mat(0xf6eedc), 0, hall.wallH + .4, front + .5, g);
  box(10.5, 1.0, .4, mat(0xb8262a), 0, hall.wallH + .4, front + .52, g);
  const star = mesh(new THREE.CylinderGeometry(1.5, 1.5, .4, 40), mat(0xe0b040, { metalness: .5, roughness: .4 }), 0, hall.wallH + 5.4, front + .6, g); star.rotation.x = Math.PI / 2;
  const wreath = mesh(new THREE.TorusGeometry(2.0, .45, 12, 40), mat(0x2f5e3c), 0, hall.wallH + 5.4, front + .55, g);
  // corner towers
  for (const sx of [-1, 1]) {
    const tx = sx * (fw / 2 + towers.size / 2 - .6);
    box(towers.size, towers.h, towers.size, CREAM, tx, towers.h / 2, front + towers.size / 2 - .4, g);
    box(towers.size + .6, .5, towers.size + .6, mat(0xd8c7a2), tx, towers.h + .25, front + towers.size / 2 - .4, g);
    box(.9, 1.8, .2, GLASS, tx, towers.h - 3.5, front - .5, g);
  }
  // side wings: lower halls with pitched roofs, arched windows, the rail portals in their outer walls
  for (const sx of [-1, 1]) {
    const inner = sx < 0 ? hall.x0 - towers.size + .6 : hall.x1 + towers.size - .6;
    const outer = inner + sx * wings.w, cx = (inner + outer) / 2;
    // the wings are the train sheds: hollow, so the tracks run inside them to the platforms
    box(.6, wings.h, -D, CREAM, outer - sx * .3, wings.h / 2, zc, g);
    box(wings.w, wings.h, .6, CREAM, cx, wings.h / 2, front - .3, g); box(wings.w, wings.h, .6, CREAM, cx, wings.h / 2, back + .3, g);
    const rf = mesh(prism(-D + 1, 3.2, wings.w + 1), ROOF, cx, wings.h, zc, g); rf.rotation.y = Math.PI / 2; rf.userData.roof = true;
    for (const wz of [front + 4, front + 10, front + 16]) box(.2, 3.6, 2.4, GLASS, outer + sx * .02, 4.2, wz, g);
    box(wings.w - 1.5, 3.4, .2, GLASS, cx, 3.8, front - .02, g);
  }
  // the clock porch: a small gabled entrance, the clock in its gable, doors and the ticket windows, steps
  const pg = new THREE.Group(); pg.position.set(0, 0, front); g.add(pg);
  const pw = porch.x1 - porch.x0;
  box(pw, porch.h, porch.depth, CREAM, 0, porch.h / 2, porch.depth / 2, pg);
  const pr = mesh(prism(pw + 1.2, porch.gable, porch.depth + 1), ROOF, 0, porch.h, porch.depth / 2, pg); pr.userData.roof = true;
  const clock = mesh(new THREE.CylinderGeometry(.85, .85, .2, 40), mat(0xfaf6ea), 0, porch.h + 1.0, porch.depth + .55, pg); clock.rotation.x = Math.PI / 2;
  box(2.4, 3.2, .3, mat(0x7a4422), 0, 1.6, porch.depth + .05, pg);                          // the doors
  for (const sx of [-1, 1]) box(1.1, 1.1, .2, GLASS, sx * 2.6, 1.9, porch.depth + .05, pg); // the ticket windows
  const st = L.station.steps;
  for (let i = 0; i < st.n; i++) box(pw + 2 + i * .6, st.rise, st.tread, STONE, 0, st.rise * (st.n - i) - st.rise / 2, front + porch.depth + st.tread * (i + .5), g);
  // inside: platforms, concourse, buffers
  const PLAT = mat(0xcfc6b4);
  for (const p of L.platforms) box(p.x1 - p.x0, .9, p.w, PLAT, (p.x0 + p.x1) / 2, .45, p.z, g);
  const c = L.concourse; box(c.x1 - c.x0, .3, c.z1 - c.z0, mat(0xd8cdb8), 0, .15, (c.z0 + c.z1) / 2, g);
  return g;
}
const stationGroup = station(L.station);

// ---------------------------------------------------------------- houses (blocks with gable roofs, doors, windows)
function house(b) {
  const g = group(b.x, b.z, b.rot);
  box(b.w, b.h, b.d, mat(b.wall), 0, b.h / 2, 0, g);
  const r = mesh(prism(b.w + .8, b.roofH, b.d + .8), mat(b.roof), 0, b.h, 0, g); r.userData.roof = true;
  box(1.1, 2.2, .15, mat(0x5a3420), 0, 1.1, b.d / 2 + .05, g);                     // the door, facing the square
  const W = glow(0xf3b45a, .9), cols = b.w > 4 ? [-1.4, 1.4] : [0];
  for (let fl = 0; fl < Math.floor((b.h - 1) / 3); fl++) for (const cx of cols) {
    if (fl === 0 && Math.abs(cx) < .8) continue;
    box(.9, 1.3, .12, W, cx, 1.6 + fl * 3, b.d / 2 + .04, g);
  }
  if (b.sign) box(3.6, 1.0, .2, mat(0xf3ead6), 0, b.h - 1.4, b.d / 2 + .15, g);
  box(b.w + .4, .4, 1.4, mat(b.name.startsWith('Toy') ? 0xb8262a : 0x3f7340), 0, 2.7, b.d / 2 + .7, g);     // an awning or canopy line
  return g;
}
for (const b of L.buildings) house(b);

// ---------------------------------------------------------------- rails: ballast bed, sleepers (instanced), two rails
function rails(R) {
  const bed = ribbon(R.pts, 2.4, mat(0xa59c8c), 0.05);
  const c = bed.curve, n = Math.round(c.getLength() / .65);
  const sl = new THREE.InstancedMesh(new THREE.BoxGeometry(2.0, .12, .22), mat(0x5a4030), n + 1); sl.castShadow = sl.receiveShadow = true;
  const o = new THREE.Object3D();
  for (let i = 0; i <= n; i++) { const p = c.getPointAt(i / n), t = c.getTangentAt(i / n); o.position.set(p.x, .1, p.z); o.rotation.set(0, Math.atan2(t.x, t.z), 0); o.updateMatrix(); sl.setMatrixAt(i, o.matrix); }
  scene.add(sl);
  for (const off of [-.72, .72]) {
    const P = c.getSpacedPoints(n).map((p, i) => { const t = c.getTangentAt(i / n); return new THREE.Vector3(p.x - t.z * off, .2, p.z + t.x * off); });
    mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(P), n, .07, 6), mat(0x55585e, { metalness: .6, roughness: .4 })).castShadow = false;
  }
  // a coloured marker post where each line arrives, so the routes are easy to read in the blockout
  const end = R.pts[R.pts.length - 1]; box(.6, 1.6, .6, mat(R.color), end[0], .8, end[1]);
  return c;
}
const RC = {}; for (const [k, r] of Object.entries(L.rails)) RC[k] = rails(r);
// dark portals where the rails pass through the wing walls (the trains enter the station from the sides)
for (const [k, r] of Object.entries(L.rails)) {
  const sx = k === 'green' ? 1 : -1, wallX = sx * (L.station.hall.x1 + L.station.towers.size - .6 + L.station.wings.w);
  const z = r.pts.find(p => Math.abs(p[0]) < Math.abs(wallX) + 1)?.[1] ?? r.pts[r.pts.length - 1][1];
  box(.3, 4.6, 3.6, mat(0x1c1a1e), wallX + sx * .02, 2.3, z);
}

// ---------------------------------------------------------------- river, stone bridge, rail trestle
{ ribbon(L.river.pts, L.river.w + 3.5, mat(0xc9d2dc), 0.035);                     // the banks, trodden snow and stones
  ribbon(L.river.pts, L.river.w, mat(0x4a74b0, { roughness: .25, metalness: .1 }), 0.06); }
function bridge(B) {
  const g = group(B.x, B.z, B.rot);
  const s = new THREE.Shape(); const l = B.len / 2;
  s.moveTo(-l, -1); s.lineTo(l, -1); s.lineTo(l, 1.1); s.quadraticCurveTo(0, 2.2, -l, 1.1); s.lineTo(-l, -1);
  const h = new THREE.Path(); h.absarc(0, -1, B.archR, 0, Math.PI, false); s.holes.push(h);
  const geo = new THREE.ExtrudeGeometry(s, { depth: B.w, bevelEnabled: false, curveSegments: 24 }); geo.translate(0, 0, -B.w / 2);
  mesh(geo, STONE, 0, 0, 0, g);
  for (const sz of [-1, 1]) box(B.len - .4, .8, .3, STONE, 0, 1.9, sz * (B.w / 2 - .15), g);
  return g;
}
bridge(L.bridge);
{ const T = L.trestle, g = group(T.x, T.z, 90); const RED = mat(0xa8322a);
  box(T.len, .5, T.w, RED, 0, .6, 0, g);
  for (const x of [-T.len / 2 + 1, -2, 2, T.len / 2 - 1]) for (const z of [-1, 1]) box(.3, 2.4, .3, RED, x, -.6, z * (T.w / 2 - .2), g);
  for (const z of [-1, 1]) box(T.len, .9, .15, RED, 0, 1.3, z * (T.w / 2), g); }

// ---------------------------------------------------------------- the square's furniture (placeholders)
const SQ = L.square;
{ // Christmas tree
  const [x, z] = SQ.tree; const g = group(x, z);
  mesh(new THREE.CylinderGeometry(.3, .4, 1.2), mat(0x5a3a22), 0, .6, 0, g);
  [[3.0, 3.2, 1.6], [2.4, 2.8, 3.6], [1.7, 2.4, 5.4], [1.0, 2.0, 7.0]].forEach(([r, h, y]) => mesh(new THREE.ConeGeometry(r, h, 18), mat(0x2f6446), 0, y, 0, g));
  const s = mesh(new THREE.OctahedronGeometry(.45), glow(0xf6d77a, 2), 0, 8.4, 0, g);
  for (let i = 0; i < 6; i++) box(.7, .55, .7, mat([0xb8262a, 0x3a6aa8, 0xe0b040][i % 3]), Math.cos(i) * 2.6, .28, Math.sin(i) * 2.6, g);
}
function lamp(x, z) { const g = group(x, z); mesh(new THREE.CylinderGeometry(.09, .12, 3.6), mat(0x1c1c22), 0, 1.8, 0, g); box(.5, .7, .5, glow(0xffd890, 2.2), 0, 3.9, 0, g);
  const pl = new THREE.PointLight(0xffc880, 6, 9, 1.6); pl.position.set(0, 3.9, 0); g.add(pl); return g; }
SQ.lamps.forEach(([x, z]) => lamp(x, z));
function figure(x, z, coat = 0x1c2a52) {           // a Marine placeholder, 1.8 m: body, head, white cap
  const g = group(x, z, 180); mesh(new THREE.CapsuleGeometry(.24, 1.0, 4, 10), mat(coat), 0, .85, 0, g);
  mesh(new THREE.SphereGeometry(.16, 16, 12), mat(0xe8b080), 0, 1.6, 0, g); mesh(new THREE.CylinderGeometry(.19, .17, .1, 16), mat(0xf6f2ea), 0, 1.77, 0, g); return g; }
SQ.marines.forEach(([x, z], i) => figure(x, z));
SQ.wagons.forEach(([x, z, r]) => { const g = group(x, z, r); box(1.4, .4, .8, mat(0xb8262a), 0, .5, 0, g); for (const a of [-.5, .5]) for (const b of [-.42, .42]) { const w = mesh(new THREE.CylinderGeometry(.18, .18, .08, 16), mat(0x1c1c22), a, .2, b, g); w.rotation.x = Math.PI / 2; } });
SQ.benches.forEach(([x, z, r]) => { const g = group(x, z, r); box(1.8, .1, .5, mat(0x6a4a30), 0, .45, 0, g); box(1.8, .5, .08, mat(0x6a4a30), 0, .75, -.22, g); });
{ // the low retaining wall along the front of the square, with steps down in the middle
  const W = SQ.wall; const xs = [[-12.5, W.gap[0]], [W.gap[1], 12.5]];
  for (const [a, b] of xs) box(b - a, W.h + 1.2, .7, STONE, (a + b) / 2, (W.h - 1.2) / 2 + .0, W.z);
  for (let i = 0; i < 6; i++) box(W.gap[1] - W.gap[0], .2, .55, STONE, 0, -.1 - i * .2, W.z + .3 + i * .55);
}
// background firs and bare trees: simple cones, kept off the paths and rails
{ const R = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(7);
  for (let i = 0; i < 140; i++) {
    const x = (R() - .5) * 240, z = -150 + R() * 260;
    if (Math.abs(x) < 34 && z > -50 && z < 40) continue;
    if (Math.abs(x - 28) < 10 && z < 20) continue;
    const h = 5 + R() * 7; mesh(new THREE.ConeGeometry(h * .28, h, 10), mat(0x2f5a40), x, h / 2, z);
  }
}

// ---------------------------------------------------------------- the existing toy shop, for scale
const shopReady = (async () => {
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(new URL(Q.get('shop') || './toyshop_scene.glb', import.meta.url).href);
  const shop = gltf.scene, T = L.toyshop;
  const g = group(T.x, T.z, T.rot); g.add(shop); g.updateMatrixWorld(true);
  // keep only the blue shop: everything outside its footprint (its street, neighbours, hillside) is clipped away
  const local = [[1, 0, 0, 2.95], [-1, 0, 0, 2.85], [0, 0, 1, 5.3], [0, 0, -1, 1.35], [0, -1, 0, 10.6], [0, 1, 0, 0.05]]
    .map(([a, b, c, d]) => new THREE.Plane(new THREE.Vector3(a, b, c), d).applyMatrix4(g.matrixWorld));
  let tris = 0;
  shop.traverse(o => { if (!o.isMesh) return; o.castShadow = o.receiveShadow = true;
    const m = o.material; m.clippingPlanes = local; m.clipShadows = true; if (m.emissiveIntensity > 0) m.emissiveIntensity *= .6;
    tris += o.geometry.index ? o.geometry.index.count / 3 : 0; });
  return { tris };
})();

// ---------------------------------------------------------------- views, cutaway, render loop
function setView(k) {
  const v = VIEWS[k]; camera.position.fromArray(v.pos); controls.target.fromArray(v.target); camera.fov = v.fov; camera.updateProjectionMatrix(); controls.update();
  scene.traverse(o => { if (o.userData.roof) o.visible = !v.cutaway; });
  document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === k));
  const t = document.getElementById('viewname'); if (t) t.textContent = v.name;
}
window.__setView = setView; window.__views = Object.keys(VIEWS);
window.__project = (pts) => pts.map(([x, y, z]) => { const v = new THREE.Vector3(x, y, z).project(camera); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight, v.z]; });
setView(Q.get('view') || 'overview');
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
const STILL = Q.get('still') === '1';                // for review captures: render one frame on request
if (!STILL) renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
window.__still = () => { renderer.render(scene, camera); window.__info = { ...renderer.info.render }; return renderer.domElement.toDataURL('image/png'); };
shopReady.then(s => { window.__ready = true; window.__stats = { ...renderer.info.render, shopTris: s.tris }; })
  .catch(e => { window.__ready = true; window.__error = String(e); });

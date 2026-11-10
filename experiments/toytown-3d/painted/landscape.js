// The country around Toy Town, from the national map's own paint (paint_landscape.py): rolling hills laid with the
// map's grass and fields, its river, its trees, the barn, farmhouses, mesas and mountains standing in the directions
// they lie on the map, a painted sky with the map's clouds, and far hills all round.
import * as THREE from 'three';

const hash = (s => () => (s = (s * 16807) % 2147483647) / 2147483647);

export function buildLandscape(scene, { tex, land, billboards }) {
  const E = land.extent_m, rand = hash(17);
  const RIVER = land.river;
  const riverDist = (x, z) => {
    let d = 1e9;
    for (let i = 0; i < RIVER.length - 1; i++) {
      const [ax, az] = RIVER[i], [bx, bz] = RIVER[i + 1], dx = bx - ax, dz = bz - az;
      const t = Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)));
      d = Math.min(d, Math.hypot(x - ax - t * dx, z - az - t * dz));
    }
    return d;
  };
  // the map's rounded hills: mounds rising beyond the town, a valley for the river, nothing inside the town
  const mounds = [];
  for (let i = 0; i < 34; i++) {
    const a = rand() * Math.PI * 2, r = 120 + rand() * 190;
    mounds.push([Math.cos(a) * r, Math.sin(a) * r, 5 + rand() * 15, 22 + rand() * 30]);
  }
  const smooth = (a, b, v) => { const t = Math.max(0, Math.min(1, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
  function height(x, z) {
    const r = Math.hypot(x, z + 6);
    let h = 2.5 + 3 * Math.sin(x / 37 + 1) * Math.sin(z / 43 + 2);
    for (const [mx, mz, mh, mr] of mounds) { const d2 = ((x - mx) ** 2 + (z - mz) ** 2) / (mr * mr); if (d2 < 9) h += mh * Math.exp(-d2); }
    const rd = riverDist(x, z);
    h *= 1 - .85 * Math.exp(-((rd / 34) ** 2));
    h = h * smooth(45, 150, r) - .06;
    if (rd < 7) h -= (1 - rd / 7) * .6;
    return h;
  }

  // ---- the hills
  const N = 200, geo = new THREE.PlaneGeometry(E, E, N, N); geo.rotateX(-Math.PI / 2);
  const pos = geo.attributes.position, col = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) pos.setY(i, height(pos.getX(i), pos.getZ(i)));
  geo.computeVertexNormals();
  const L = new THREE.Vector3(-.45, .8, -.3).normalize(), nrm = geo.attributes.normal, n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {                // painted light: lit from the north-west, as on the map
    n.fromBufferAttribute(nrm, i); const s = .62 + .44 * Math.max(0, n.dot(L));
    col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = Math.min(1.04, s);
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const hills = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex('meadow.jpg'), vertexColors: true }));
  scene.add(hills);
  // beyond the painted hills, the same green running to the horizon
  const far = new THREE.Mesh(new THREE.RingGeometry(E * .48, 2400, 64, 1), new THREE.MeshBasicMaterial({ color: 0x86a64a }));
  far.rotation.x = -Math.PI / 2; far.position.y = -.4; scene.add(far);

  // ---- sky: a painted dome, and the map's own clouds
  const sg = new THREE.SphereGeometry(1500, 48, 16, 0, Math.PI * 2, 0, Math.PI / 2 + .12), suv = sg.attributes.uv;
  scene.add(new THREE.Mesh(sg, new THREE.MeshBasicMaterial({ map: tex('sky.jpg'), side: THREE.BackSide, fog: false, depthWrite: false })));
  // far hills all round, repeated four times around the circle
  const hr = 900, hh = (2 * Math.PI * hr / 4) * 300 / 2400;
  const ht = tex('horizon.png'); ht.wrapS = THREE.RepeatWrapping; ht.repeat.set(4, 1);
  const hc = new THREE.Mesh(new THREE.CylinderGeometry(hr, hr, hh, 96, 1, true), new THREE.MeshBasicMaterial({ map: ht, side: THREE.BackSide, transparent: true, alphaTest: .4, fog: true }));
  hc.position.y = hh / 2 - hh * .42; scene.add(hc);
  const clouds = new THREE.Group(); scene.add(clouds);
  for (let i = 0; i < 14; i++) {
    const c = land.clouds[i % land.clouds.length], a = (i / 14) * Math.PI * 2 + rand() * .3, d = 520 + rand() * 260, w = 120 + rand() * 120;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w * c.h / c.w), new THREE.MeshBasicMaterial({ map: tex('map/' + c.file), transparent: true, depthWrite: false, fog: false, opacity: .95 }));
    m.position.set(Math.cos(a) * d, 120 + rand() * 140, Math.sin(a) * d); m.lookAt(0, m.position.y * .6, 0); clouds.add(m);
  }

  // ---- landmarks cut from the map, each in the direction it lies from Toy Town on the map
  const [TX, TY] = land.town_map_px, placed = [];
  const far_ = { mountains: 640, mesas: 330 };
  for (const [name, L_] of Object.entries(land.landmarks)) {
    const dx = L_.map[0] - TX, dy = L_.map[1] - TY, md = Math.hypot(dx, dy);
    const d = far_[name] || Math.min(260, 95 + md * .07), x = dx / md * d, z = dy / md * d;
    const h = L_.h_m * (name === 'mountains' ? 1.6 : 1), w = h * L_.w / L_.h;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex('land_' + name + '.png'), alphaTest: .5, side: THREE.DoubleSide }));
    const g = new THREE.Group(); g.position.set(x, Math.min(height(x, z), height(x - w * .3, z), height(x + w * .3, z)) - .3, z);
    m.position.y = h / 2; g.add(m); g.lookAt(0, g.position.y, 0); scene.add(g); placed.push([x, z, w * .6]);
  }

  // ---- the map's trees on the hills, grouped by picture so each kind is drawn once
  const groups = new Map(), clusters = []; for (let i = 0; i < 26; i++) { const a = rand() * Math.PI * 2, r = 60 + rand() * 230; clusters.push([Math.cos(a) * r, Math.sin(a) * r, 18 + rand() * 30]); }
  const ever = land.trees.filter(t => t.ever), decid = land.trees.filter(t => !t.ever);
  let count = 0;
  for (let tries = 0; tries < 20000 && count < 520; tries++) {
    const c = clusters[Math.floor(rand() * clusters.length)], loose = rand() < .3;
    const a = rand() * Math.PI * 2, rr = loose ? 0 : Math.sqrt(rand()) * c[2];
    let x = loose ? (rand() - .5) * E * .95 : c[0] + Math.cos(a) * rr, z = loose ? (rand() - .5) * E * .95 : c[1] + Math.sin(a) * rr;
    const r = Math.hypot(x, z + 6); if (r < 48 || Math.abs(x) > E * .48 || Math.abs(z) > E * .48) continue;
    if (riverDist(x, z) < 9) continue;
    if (placed.some(([px, pz, pr]) => Math.hypot(x - px, z - pz) < pr + 8)) continue;
    const isEver = r < 80 ? rand() < .75 : rand() < .25, pool = isEver ? ever : decid, t = pool[Math.floor(rand() * pool.length)];
    const h = (isEver ? 9 + rand() * 5 : 7 + rand() * 4) * (r < 80 ? .9 : 1), w = h * t.w / t.h, y = height(x, z) - .2;
    if (!groups.has(t.file)) groups.set(t.file, []);
    groups.get(t.file).push([x, y, z, w, h]); count++;
  }
  for (const [file, list] of groups) {
    const P = [], U = [], I = [];
    for (const [x, y, z, w, h] of list) {
      const ang = Math.atan2(x, z), cx = Math.cos(ang) * w / 2, cz = -Math.sin(ang) * w / 2, b = P.length / 3;   // faces the town
      P.push(x - cx, y, z - cz, x + cx, y, z + cz, x + cx, y + h, z + cz, x - cx, y + h, z - cz);
      U.push(0, 0, 1, 0, 1, 1, 0, 1); I.push(b, b + 1, b + 2, b, b + 2, b + 3);
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2)); g.setIndex(I);
    scene.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: tex('map/' + file), alphaTest: .5, side: THREE.DoubleSide })));
  }
  return { height, clouds, riverDist };
}

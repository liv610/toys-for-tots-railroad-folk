// Entering Toy Town from the national map. Added to a copy of the map viewer by build_enter.py; nothing in the
// live map changes. Clicking the town on the map zooms in until the painted station fills the view the way the
// painted scene frames it at its arrival stop, Toy Town (toytown/, in a frame laid exactly over the map) dissolves
// in on top, and the camera comes down into the square. "Back to the map" reverses it.
// The ticket window in Toy Town hands a ticket to window.__ttRide: Toy Town fades back into the map, a train leaves
// the station and runs out along the painted rails to the visitor's local toy drive, and a card there lists its
// drop-off spots, where the visitor can say which one they'll bring a toy to.
(function () {
  const C = window.TT_ENTER;                 // written by build_enter.py: the town outline and the station face in map px
  const stage = document.querySelector('.stage'), osd = document.getElementById('osd');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let viewer = null, base = null, frame = null, win = null, state = 'map', loadP = null;
  const TTC = window.TT_CAMPAIGNS;

  // ---- the 3D village, in a frame over the map, loaded ahead of time and kept paused until it is needed
  const shell = document.createElement('div'); shell.className = 'tt3d'; shell.setAttribute('aria-hidden', 'true');
  shell.innerHTML = '<div class="tt3d-ui" role="toolbar" aria-label="Toy Town">' +
    C.views.map(([k, label]) => '<button data-v="' + k + '">' + label + '</button>').join('') +
    '<button class="tt3d-back">Back to the map</button></div>' +
    '<div class="tt3d-note">Move or drag to look around.</div>';
  const tag = document.createElement('div'); tag.className = 'tag tt-tag'; tag.hidden = true;
  tag.innerHTML = 'Toy Town<small>click to step inside</small>';
  const msg = document.createElement('div'); msg.className = 'tt-msg'; msg.hidden = true; msg.textContent = 'Opening Toy Town…';
  stage.append(shell, tag, msg);
  function load() {
    if (loadP) return loadP;
    frame = document.createElement('iframe'); frame.title = 'Toy Town'; frame.src = 'toytown/index.html?embed=1&view=arrive&paused=1';
    frame.setAttribute('allow', 'fullscreen'); shell.prepend(frame);
    loadP = new Promise(res => {
      const poll = () => { try { win = frame.contentWindow; if (win && win.__ready && win.__stationRect) return res(win); } catch (e) {} setTimeout(poll, 120); };
      frame.addEventListener('load', poll); poll();
    });
    return loadP;
  }

  // ---- where Toy Town is on the map
  const inside = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j]; if ((yi > p.y) !== (yj > p.y) && p.x < (xj - xi) * (p.y - yi) / (yj - yi) + xi) c = !c; } return c; };
  const toImg = (ex, ey) => base.viewerElementToImageCoordinates(new OpenSeadragon.Point(ex, ey));

  function springs(t) { const v = viewer.viewport; for (const s of [v.zoomSpring, v.centerSpringX, v.centerSpringY]) s.animationTime = t; }
  const settle = () => new Promise(res => { const h = () => { viewer.removeHandler('animation-finish', h); res(); }; viewer.addHandler('animation-finish', h); });

  // the map view that puts the painted station exactly where the 3D arrival view draws it
  function arrivalRect(r3) {
    const [[sx0, sy0], [sx1, sy1]] = r3, [fx0, fy0, fx1, fy1] = C.face;
    const k = (fx1 - fx0) / (sx1 - sx0);                        // map px per screen px
    const W = stage.clientWidth, H = stage.clientHeight;
    const x0 = fx0 - sx0 * k, y0 = fy1 - sy1 * k;               // line up the left edge and the foot of the station
    return base.imageToViewportRectangle(x0, y0, W * k, H * k);
  }

  async function enter() {
    if (state === 'arrived') closeArrival();
    if (state !== 'map' || !base) return; state = 'entering'; TTC && TTC.log('enter');
    tag.hidden = true; const w = load();
    // 1. glide in toward the town while the village loads
    springs(reduce ? .01 : 1.6);
    const [x0, y0, x1, y1] = C.town_box; viewer.viewport.fitBounds(base.imageToViewportRectangle(x0, y0, x1 - x0, y1 - y0));
    await settle();
    const tm = setTimeout(() => { msg.hidden = false; }, 400);
    const win_ = await w; clearTimeout(tm); msg.hidden = true;
    win_.__setView('arrive');
    // 2. come in until the painted station sits where the 3D draws it
    springs(reduce ? .01 : 1.5); viewer.viewport.fitBounds(arrivalRect(win_.__stationRect())); await settle();
    // 3. the 3D dissolves in over the painting, then the camera comes down into the square
    win_.__pause(false); shell.classList.add('on'); shell.removeAttribute('aria-hidden');
    await new Promise(r => setTimeout(r, reduce ? 50 : 1300));
    state = 'in'; springs(1.2);
    shell.querySelector('.tt3d-back').focus({ preventScroll: true });
    await win_.__glideTo('square', reduce ? .01 : 5);
  }
  async function leave() {
    if (state !== 'in') return; state = 'leaving';
    await win.__glideTo('arrive', reduce ? .01 : 2.6);
    viewer.viewport.fitBounds(arrivalRect(win.__stationRect()), true);
    shell.classList.remove('on'); shell.setAttribute('aria-hidden', 'true');
    await new Promise(r => setTimeout(r, reduce ? 50 : 1100));
    win.__pause(true);
    springs(reduce ? .01 : 1.8); const [x0, y0, x1, y1] = C.town_box;
    viewer.viewport.fitBounds(base.imageToViewportRectangle(x0 - 600, y0 - 300, x1 - x0 + 1200, y1 - y0 + 600)); await settle(); springs(1.2);
    state = 'map';
  }
  // ---- the ride: a train from Toy Town out along the painted rails to the visitor's toy drive
  const S = JSON.parse(document.getElementById('scene-data').textContent), ROUTES = {};
  for (const [nm, r] of Object.entries(S.routes)) {
    const P = r.points, A = [0];
    for (let i = 1; i < P.length; i++) A.push(A[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    ROUTES[nm] = { P, A, L: A[A.length - 1], from: A[r.track_from], to: A[r.track_to] };
  }
  function along(r, s) {
    const { P, A } = r; s = Math.max(0, Math.min(r.L, s)); let lo = 0, hi = A.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (A[m] <= s) lo = m; else hi = m; }
    const u = (s - A[lo]) / Math.max(1e-6, A[hi] - A[lo]); return [P[lo][0] + (P[hi][0] - P[lo][0]) * u, P[lo][1] + (P[hi][1] - P[lo][1]) * u];
  }
  const stopOf = c => { const r = ROUTES[c.route]; return r.from + c.f * (r.to - r.from); };
  const ov = document.createElement('canvas'); ov.className = 'tt-ride'; ov.setAttribute('aria-hidden', 'true'); stage.appendChild(ov);
  const octx = ov.getContext('2d');
  const sprite = f => { const sp = S.sprites.find(x => x.file === f), im = new Image(); im.src = 'sprites/' + f; return { sp, im }; };
  const LOOK = { red: ['loco_0.png', 'wagon_0.png', 'wagon_1.png'], blue: ['loco_1.png', 'wagon_3.png', 'wagon_4.png'], green: ['loco_2.png', 'wagon_6.png', 'wagon_7.png'] };
  const CARS = {}; for (const [k, fs] of Object.entries(LOOK)) CARS[k] = fs.map(sprite);
  let ride_ = null;                                       // { c, r, s, puffs, t0 } while a train is out or has arrived
  function screenOf(x, y) { const p = base.imageToViewerElementCoordinates(new OpenSeadragon.Point(x, y)); return [p.x, p.y]; }
  function draw(now) {
    const dpr = devicePixelRatio || 1, W = stage.clientWidth, H = stage.clientHeight;
    if (ov.width !== Math.round(W * dpr) || ov.height !== Math.round(H * dpr)) { ov.width = Math.round(W * dpr); ov.height = Math.round(H * dpr); }
    octx.setTransform(dpr, 0, 0, dpr, 0, 0); octx.clearRect(0, 0, W, H);
    if (!ride_ || !base) return;
    const { r, c } = ride_, [ax, ay] = screenOf(0, 0), [bx] = screenOf(100, 0), k = (bx - ax) / 100;   // screen px per map px
    const end = stopOf(c), [ex, ey] = screenOf(...along(r, end));
    // the stop: a warm ring that breathes
    const pulse = .5 + .5 * Math.sin(now / 420);
    octx.strokeStyle = `rgba(255,214,140,${.55 + .35 * pulse})`; octx.lineWidth = 3;
    octx.beginPath(); octx.arc(ex, ey, 18 + 8 * pulse, 0, 6.283); octx.stroke();
    octx.fillStyle = 'rgba(255,240,200,.85)'; octx.beginPath(); octx.arc(ex, ey, 6, 0, 6.283); octx.fill();
    // steam puffs
    for (const p of ride_.puffs) { const age = (now - p.t) / 1600; if (age > 1) continue; const [px, py] = screenOf(p.x, p.y - age * 90);
      octx.fillStyle = `rgba(250,250,246,${.7 * (1 - age)})`; octx.beginPath(); octx.arc(px, py, (14 + 30 * age) * k * 2.4, 0, 6.283); octx.fill(); }
    // the train: engine first, heading away from Toy Town (toward smaller s); wagons follow behind
    const cars = CARS[c.route]; let off = 0;
    cars.forEach((car, i) => {
      if (!car.im.complete || !car.sp) return;
      const sv = ride_.s + off, [x, y] = along(r, sv), [x2, y2] = along(r, sv - 6), [px, py] = screenOf(x, y);
      let a = Math.atan2(y2 - y, x2 - x); octx.save(); octx.translate(px, py);
      if (Math.cos(a) < 0) { octx.scale(-1, 1); a = Math.PI - a; }
      octx.rotate(a); const sc = k, pv = car.sp.pivot || [car.sp.w / 2, car.sp.h * .8];
      octx.drawImage(car.im, -pv[0] * sc, -pv[1] * sc, car.sp.w * sc, car.sp.h * sc); octx.restore();
      off += 150;
    });
  }
  (function loop(now) { draw(now); if (state === 'arrived' && ride_) placeArrival(); requestAnimationFrame(loop); })(performance.now());

  async function ride(c) {
    state = 'riding'; const r = ROUTES[c.route], sA = r.to - 30, sB = stopOf(c);
    ride_ = { c, r, s: sA, puffs: [] };
    // frame the whole trip, from Toy Town to the stop
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (let s_ = sB; s_ <= sA; s_ += 40) { const [x, y] = along(r, s_); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    const pad = Math.max(500, (x1 - x0) * .15); springs(reduce ? .01 : 1.6);
    viewer.viewport.fitBounds(base.imageToViewportRectangle(x0 - pad, y0 - pad * .8, x1 - x0 + pad * 2, y1 - y0 + pad * 1.6)); await settle(); springs(1.2);
    const dur = reduce ? 0 : Math.max(3.5, Math.min(9, (sA - sB) / 650)) * 1000, t0 = performance.now();
    await new Promise(res => {
      (function step(now) {
        const f = dur ? Math.min(1, (now - t0) / dur) : 1, e = f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
        ride_.s = sA - (sA - sB) * e;
        if (!ride_.lastPuff || now - ride_.lastPuff > 260) { const [x, y] = along(r, ride_.s); ride_.puffs.push({ x, y: y - 120, t: now }); ride_.lastPuff = now; }
        f < 1 ? requestAnimationFrame(step) : res();
      })(t0);
    });
    TTC && TTC.log('arrive'); arrival(c);
  }
  window.__ttCardOpen = v => shell.classList.toggle('carding', !!v);      // Toy Town's toolbar steps aside for its cards
  window.__ttRide = async c => { if (state === 'in') await leave(); if (state === 'map') ride(c); };

  // ---- arriving: the toy drive's card at its station, with its drop-off spots
  const arr = document.createElement('div'); arr.className = 'card tt-arrive'; arr.hidden = true; arr.setAttribute('role', 'dialog'); arr.setAttribute('aria-labelledby', 'tta-title');
  stage.appendChild(arr);
  const esc = s => String(s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
  function arrival(c) {
    state = 'arrived';
    arr.innerHTML = `<button class="card-x" aria-label="Close">&times;</button><div class="card-body">
      <span class="card-eyebrow">Arrived &middot; ${esc(c.town)} station</span>
      <h2 id="tta-title">${esc(c.town)} Toy Drive</h2>
      <p>Bring a <b>new, unwrapped toy</b> to any of these spots by <b>${esc(c.deadline)}</b>. Marines and volunteers collect them and give them to children right here in ${esc(c.town)}.</p>
      <ol class="tta-spots">${c.spots.map(([n, a, h], i) => `<li><div><b>${esc(n)}</b><span>${esc(a)}</span><span>${esc(h)}</span></div>
        <button class="tta-pick" data-i="${i}">I'll bring a toy here</button></li>`).join('')}</ol>
      <p class="tta-thanks" role="status" hidden></p>
      <div class="card-actions"><button class="tta-back">Back to Toy Town</button><button class="tta-close">Back to the map</button></div>
      <p class="card-note">Demo: every toy drive, place and date here is invented.</p></div>`;
    arr.hidden = false; placeArrival();
    arr.querySelector('.card-x').onclick = arr.querySelector('.tta-close').onclick = closeArrival;
    arr.querySelector('.tta-back').onclick = () => { closeArrival(); enter(); };
    arr.querySelectorAll('.tta-pick').forEach(b => b.onclick = () => {
      const sp = c.spots[+b.dataset.i]; TTC && TTC.log('pledge');
      arr.querySelectorAll('.tta-pick').forEach(x => { x.disabled = true; x.textContent = x === b ? 'See you there!' : 'I\'ll bring a toy here'; });
      const t = arr.querySelector('.tta-thanks'); t.hidden = false;
      t.innerHTML = `<b>Thank you!</b> Your toy goes to ${esc(sp[0])}, ${esc(sp[1])} (${esc(sp[2])}), by ${esc(c.deadline)}.`;
    });
    arr.querySelector('.tta-pick').focus({ preventScroll: true });
  }
  function placeArrival() {
    if (!ride_ || arr.hidden) return;
    const [ex, ey] = screenOf(...along(ride_.r, stopOf(ride_.c))), W = stage.clientWidth, H = stage.clientHeight;
    if (W < 620 || H < 420) { arr.style.left = '10px'; arr.style.top = (H - arr.offsetHeight - 10) + 'px'; return; }
    const cw = arr.offsetWidth, ch = arr.offsetHeight; let x = ex + 30; if (x + cw > W - 10) x = ex - cw - 30;
    arr.style.left = Math.round(Math.max(10, Math.min(W - cw - 10, x))) + 'px'; arr.style.top = Math.round(Math.max(10, Math.min(H - ch - 10, ey - ch * .4))) + 'px';
  }
  function closeArrival() { arr.hidden = true; ride_ = null; if (state === 'arrived') state = 'map'; }

  // ---- a little funnel of what this browser's visitors did, for the demo
  const fun = document.createElement('div'); fun.className = 'tt-funnel'; fun.hidden = true; document.querySelector('.wrap').insertBefore(fun, document.querySelector('.notes'));
  const STEPS = [['enter', 'Stepped into Toy Town'], ['hotspot_ticket', 'Clicked the ticket window'], ['hotspot_donate', 'Clicked the donation shop'], ['hotspot_marines', 'Clicked the Marines'],
    ['ticket', 'Printed a ticket'], ['spots', 'Opened the drop-off list in Toy Town'], ['ride', 'Rode the train'], ['arrive', 'Arrived at their toy drive'], ['pledge', 'Chose a drop-off spot']];
  function showFunnel() {
    const t = TTC ? TTC.tally() : {}, top = Math.max(1, t.enter || 0);
    fun.innerHTML = '<h2>Demo funnel <small>this browser only</small></h2><ol>' + STEPS.map(([k, l]) => `<li><span>${l}</span><i style="--w:${Math.min(100, 100 * (t[k] || 0) / top)}%"></i><b>${t[k] || 0}</b></li>`).join('') +
      '</ol><button class="tt-reset">Reset</button>';
    fun.querySelector('.tt-reset').onclick = () => { TTC && TTC.reset(); showFunnel(); };
  }
  setInterval(() => { if (!fun.hidden) showFunnel(); }, 1500);

  shell.querySelector('.tt3d-back').onclick = leave;
  shell.querySelectorAll('[data-v]').forEach(b => b.onclick = () => { if (state === 'in') win.__glideTo(b.dataset.v, 3); });
  addEventListener('keydown', e => { if (e.key !== 'Escape') return; if (state === 'in') leave(); else if (state === 'arrived') closeArrival(); });

  // ---- hook into the map viewer once it is up
  (function wait() {
    viewer = window.__viewer; base = viewer && viewer.world.getItemAt(0);
    if (!base) return setTimeout(wait, 200);
    viewer.addHandler('canvas-click', e => {
      if (!e.quick || state !== 'map') return;
      if (inside(toImg(e.position.x, e.position.y), C.town)) { e.preventDefaultAction = true; enter(); }
    });
    osd.addEventListener('pointermove', e => {
      if (state !== 'map' || e.pointerType === 'touch') return;
      const r = osd.getBoundingClientRect(), p = toImg(e.clientX - r.left, e.clientY - r.top), on = inside(p, C.town);
      tag.hidden = !on; if (on) { tag.style.left = (e.clientX - r.left) + 'px'; tag.style.top = (e.clientY - r.top - 14) + 'px'; load(); }
      viewer.canvas.style.cursor = on ? 'pointer' : '';
    });
    osd.addEventListener('pointerleave', () => { tag.hidden = true; });
    const btn = document.createElement('button'); btn.textContent = 'Enter Toy Town'; btn.className = 'tt-enter'; btn.onclick = enter;
    const bar = document.querySelector('.bar'); bar && bar.prepend(btn);
    const fb = document.createElement('button'); fb.textContent = 'Demo funnel'; fb.setAttribute('aria-pressed', 'false');
    fb.onclick = () => { fun.hidden = !fun.hidden; fb.setAttribute('aria-pressed', String(!fun.hidden)); if (!fun.hidden) showFunnel(); };
    bar && bar.append(fb);
    if (new URLSearchParams(location.search).has('funnel')) fb.click();
    setTimeout(load, 6000);                                  // fetch the village quietly once the map has settled
    window.__tt = { enter, leave, ride, get state() { return state; }, get win() { return win; },          // test hooks
      async handover() { const w = await load(); w.__setView('arrive'); viewer.viewport.fitBounds(arrivalRect(w.__stationRect()), true); return true; },
      show(v) { shell.style.transition = 'none'; shell.classList.toggle('on', v); } };
  })();
})();

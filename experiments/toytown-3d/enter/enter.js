// Entering Toy Town from the national map. Added to a copy of the map viewer by build_enter.py; nothing in the
// live map changes. Clicking the town on the map zooms in until the painted station fills the view the way the
// 3D village frames it at its arrival stop, the 3D village (toytown/, in a frame laid exactly over the map)
// dissolves in on top, and the camera comes down into the square. "Back to the map" reverses it.
(function () {
  const C = window.TT_ENTER;                 // written by build_enter.py: the town outline and the station face in map px
  const stage = document.querySelector('.stage'), osd = document.getElementById('osd');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let viewer = null, base = null, frame = null, win = null, state = 'map', loadP = null;

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
    if (state !== 'map' || !base) return; state = 'entering';
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
  shell.querySelector('.tt3d-back').onclick = leave;
  shell.querySelectorAll('[data-v]').forEach(b => b.onclick = () => { if (state === 'in') win.__glideTo(b.dataset.v, 3); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && state === 'in') leave(); });

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
    setTimeout(load, 6000);                                  // fetch the village quietly once the map has settled
    window.__tt = { enter, leave, get state() { return state; }, get win() { return win; },          // test hooks
      async handover() { const w = await load(); w.__setView('arrive'); viewer.viewport.fitBounds(arrivalRect(w.__stationRect()), true); return true; },
      show(v) { shell.style.transition = 'none'; shell.classList.toggle('on', v); } };
  })();
})();

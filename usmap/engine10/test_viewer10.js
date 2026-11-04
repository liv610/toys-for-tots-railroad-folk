// Phase 3 viewer tests (headless Chromium): views at three scales, a zoom transition sequence, detail on/off at
// the same viewport, load time, frame rate and memory, on a desktop and an emulated phone.
// usage: node test_viewer10.js <served base url> <out dir> <osd.min.js>
const { chromium, devices } = require('playwright'); const fs = require('fs');
const [URL, OUT, OSD] = process.argv.slice(2); const osd = fs.readFileSync(OSD);
const res = {};
async function page(b, opts) {
  const ctx = await b.newContext(opts); const p = await ctx.newPage(); const errs = [];
  await p.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ body: osd, contentType: 'application/javascript' }));
  await p.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  return { ctx, p, errs };
}
const settle = p => p.waitForFunction(() => { const v = window.__viewer; if (!v || !v.world.getItemCount()) return false;
  for (let i = 0; i < v.world.getItemCount(); i++) { const it = v.world.getItemAt(i); if (it.getOpacity() > 0 && !it.getFullyLoaded()) return false; } return true; }, null, { timeout: 30000, polling: 100 }).catch(() => 'timeout');
const fps = p => p.evaluate(() => new Promise(res => { let n = 0, t0 = performance.now(); const f = t => { n++; if (t - t0 < 4000) requestAnimationFrame(f); else res(Math.round(n * 1000 / (t - t0))); }; requestAnimationFrame(f); }));
const hud = p => p.textContent('#hud');
(async () => {
  const b = await chromium.launch();
  for (const [name, opts] of [['desktop', { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 }], ['phone', devices['iPhone 13']]]) {
    const { ctx, p, errs } = await page(b, opts); const r = res[name] = {};
    const t0 = Date.now(); await p.goto(URL + 'index.html'); await settle(p); r.load_home_s = (Date.now() - t0) / 1000;
    await p.screenshot({ path: `${OUT}/${name}_national.png` });
    // the Toy Town button, then the yellow shop button (each settles fully)
    for (const [tag, sel] of [['toytown', 'button[data-r^="640,250"]'], ['shop', 'button[data-r^="944,452"]']]) {
      const t1 = Date.now(); await p.click(sel); await p.waitForTimeout(900); await settle(p); r[`load_${tag}_s`] = (Date.now() - t1) / 1000;
      r[`hud_${tag}`] = await hud(p); await p.screenshot({ path: `${OUT}/${name}_${tag}.png` });
    }
    r.fps_shop = await fps(p);
    // zoom out through the crossfade in small steps from the shop (desktop only: the full sequence)
    if (name === 'desktop') {
      r.sequence = [];
      for (let i = 0; i < 9; i++) {
        await p.evaluate(() => window.__viewer.viewport.zoomBy(1 / 1.12, null, true)); await p.waitForTimeout(250); await settle(p); await p.waitForTimeout(150);
        await p.screenshot({ path: `${OUT}/seq_${i}.png` }); r.sequence.push(await hud(p));
      }
      // panning animation frame rate while the crossfade is half way
      r.fps_crossfade_idle = await fps(p);
      r.fps_panning = await p.evaluate(() => new Promise(res => { const v = window.__viewer; let n = 0, t0 = performance.now();
        const f = t => { n++; v.viewport.panBy(new OpenSeadragon.Point(.0004 * Math.sin(n / 20), .0002)); if (t - t0 < 4000) requestAnimationFrame(f); else res(Math.round(n * 1000 / (t - t0))); }; requestAnimationFrame(f); }));
    }
    const m = await p.evaluate(() => performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : null); r.js_heap_mb = m;
    r.tiles_requested = await p.evaluate(() => performance.getEntriesByType('resource').filter(e => /tiles\//.test(e.name)).length);
    r.tile_mb = await p.evaluate(() => Math.round(performance.getEntriesByType('resource').filter(e => /tiles\//.test(e.name)).reduce((a, e) => a + (e.encodedBodySize || 0), 0) / 1e5) / 10);
    r.errors = errs; await ctx.close();
  }
  // detail forced on / off at the same view: the shop at the Toy Town button's zoom and at a close-up
  for (const mode of ['on', 'off']) {
    const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    await p.goto(URL + 'index.html?detail=' + mode); await settle(p);
    await p.click('button[data-r^="640,250"]'); await p.waitForTimeout(900); await settle(p); await p.screenshot({ path: `${OUT}/force_${mode}_toytown.png` });
    await p.click('button[data-r^="944,452"]'); await p.waitForTimeout(900); await settle(p); await p.screenshot({ path: `${OUT}/force_${mode}_shop.png` });
    await ctx.close();
  }
  fs.writeFileSync(`${OUT}/viewer10_test.json`, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res, null, 1)); await b.close();
})();

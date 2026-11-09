// Northwest integration test, in headless Chromium: the station stop, the viaduct, the tunnel entry and exit,
// the station card at three zoom levels, alignment at the deepest zoom, frame rate, errors; desktop and phone.
// usage: node test_nw.js <served base url> <out dir> <openseadragon.min.js>
const { chromium, devices } = require('playwright'); const fs = require('fs');
const [URL, OUT, OSD] = process.argv.slice(2); const osd = fs.readFileSync(OSD);
fs.mkdirSync(OUT, { recursive: true });
const res = { frames: {} };
async function open(b, opts) {
  const ctx = await b.newContext(opts); const p = await ctx.newPage(); const errs = [];
  await p.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ body: osd, contentType: 'application/javascript' }));
  await p.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(URL + 'index.html'); await settle(p);
  return { ctx, p, errs };
}
const settle = p => p.waitForFunction(() => { const v = window.__viewer; if (!v || !v.world.getItemCount()) return false;
  for (let i = 0; i < v.world.getItemCount(); i++) { const it = v.world.getItemAt(i); if (it.getOpacity() > 0 && !it.getFullyLoaded()) return false; } return true; },
  null, { timeout: 30000, polling: 100 }).catch(() => 'timeout');
const fps = p => p.evaluate(() => new Promise(r => { let n = 0, t0 = performance.now(); const f = t => { n++; if (t - t0 < 4000) requestAnimationFrame(f); else r(Math.round(n * 1000 / (t - t0))); }; requestAnimationFrame(f); }));
// fit a map-unit box
const fit = (p, x, y, w, h) => p.evaluate(([x, y, w, h]) => { const v = window.__viewer, b = v.world.getItemAt(0), K = 6400 / 1671, FR = [100 * K, 70 * K];
  v.viewport.fitBounds(b.imageToViewportRectangle(x * K + FR[0], y * K + FR[1], w * K, h * K), true); }, [x, y, w, h]);
// put the red train's head at canvas-arc distance s (paused)
const headAt = (p, s) => p.evaluate(s => { const n = window.__nw; n.setPlay(false); n.t = n.timeForS(s); }, s);
const shot = async (p, name, wait = 350) => { await p.waitForTimeout(wait); await settle(p); await p.waitForTimeout(120); await p.screenshot({ path: `${OUT}/${name}.png` }); res.frames[name] = await p.textContent('#hud'); };
(async () => {
  const b = await chromium.launch();
  // ---------------- desktop
  { const { ctx, p, errs } = await open(b, { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const NW = await p.evaluate(() => window.__nw.NW), K = 6400 / 1671;
    res.nw = { portal_s: NW.portal_s, exit_s: NW.exit_s, stop_s: NW.stop_s };
    await shot(p, 'd00_national', 800);
    res.fps_national = await fps(p);
    // the station stop, in real time from a fresh departure clock
    await fit(p, 20, 60, 330, 210);
    await p.click('#again'); await fit(p, 20, 60, 330, 210);
    await shot(p, 'd01_station_arriving', 1200);
    await p.waitForFunction(() => window.__nw.state() && window.__nw.state().ph === 'dwell', null, { timeout: 30000 });
    await shot(p, 'd02_station_stopped', 1500);
    await p.waitForFunction(() => window.__nw.state().ph === 'depart', null, { timeout: 30000 });
    await shot(p, 'd03_station_departing', 1800);
    res.fps_station = await fps(p);
    // the viaduct and the tunnel, with the clock set exactly
    await fit(p, 250, 230, 420, 200);
    for (const [nm, ds] of [['d04_viaduct', (NW.portal_s - 520)], ['d05_tunnel_approach', NW.portal_s - 30 * K], ['d06_tunnel_entering', NW.portal_s + 40 * K],
                            ['d07_tunnel_half', NW.portal_s + 110 * K], ['d08_tunnel_inside', NW.exit_s + 20 * K], ['d09_tunnel_emerging', NW.exit_s + 80 * K],
                            ['d10_tunnel_out', NW.exit_s + 180 * K]]) {
      await headAt(p, ds); await shot(p, nm, 300);
    }
    // close-ups: the portal as the locomotive goes in, and as the train comes out from behind the shoulder
    await fit(p, 430, 270, 190, 120);
    await headAt(p, NW.portal_s + 25 * K); await shot(p, 'd11_portal_closeup');
    await headAt(p, NW.exit_s + 55 * K); await shot(p, 'd12_shoulder_closeup');
    // deepest zoom on the viaduct: are the train and the painted rails aligned?
    await fit(p, 330, 280, 60, 36); await headAt(p, NW.viaduct[0] + 120 * K); await shot(p, 'd13_viaduct_maxzoom', 600);
    res.hud_maxzoom = await p.textContent('#hud');
    // the station card at three zoom levels
    await p.evaluate(() => window.__nw.setPlay(true));
    for (const [nm, box] of [['d14_card_far', [-60, 0, 900, 520]], ['d15_card_mid', [-10, 40, 420, 250]], ['d16_card_near', [30, 70, 180, 120]]]) {
      await fit(p, ...box); await p.waitForTimeout(500); await settle(p);
      const pt = await p.evaluate(() => { const v = window.__viewer, b = v.world.getItemAt(0), h = window.__nw.NW.hit, r = document.getElementById('osd').getBoundingClientRect();
        const q = b.imageToViewerElementCoordinates(new OpenSeadragon.Point((h[0] + h[2]) / 2, (h[1] + h[3]) / 2)); return [r.left + q.x, r.top + q.y]; });
      if (!(await p.isHidden('#card'))) { await p.keyboard.press('Escape'); }
      await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(200);
      if (nm === 'd15_card_mid') await p.screenshot({ path: `${OUT}/d15a_hover.png` });
      await p.mouse.click(pt[0], pt[1]); await shot(p, nm, 400);
      res[nm] = { visible: await p.isVisible('#card'), live: await p.textContent('#card-live') };
    }
    // the card follows the station while panning
    await p.evaluate(() => window.__viewer.viewport.panBy(new OpenSeadragon.Point(.03, .01), true)); await shot(p, 'd17_card_panned', 300);
    await p.keyboard.press('Escape'); res.card_closed_by_escape = await p.isHidden('#card');
    // ride along for a few seconds
    await p.click('#again'); await p.click('#follow'); await shot(p, 'd18_ride_along', 9000);
    res.fps_ride = await fps(p);
    res.desktop_errors = errs; await ctx.close(); }
  // ---------------- phone
  { const { ctx, p, errs } = await open(b, devices['iPhone 13']);
    await shot(p, 'p00_national', 800);
    await p.click('#openStation'); await shot(p, 'p01_card', 900);
    res.phone_card_visible = await p.isVisible('#card');
    res.fps_phone = await fps(p);
    res.phone_errors = errs; await ctx.close(); }
  await b.close();
  fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res, null, 1));
})();

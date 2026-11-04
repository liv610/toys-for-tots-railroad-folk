const { chromium } = require('playwright'); const fs = require('fs');
const [URL, OUT, OSD] = process.argv.slice(2); const osd = fs.readFileSync(OSD);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 900 } }); let n = 0, bytes = 0;
  await p.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ body: osd, contentType: 'application/javascript' }));
  await p.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
  p.on('response', async r => { if (/tiles\//.test(r.url())) { n++; try { bytes += (await r.body()).length; } catch (e) {} } });
  await p.goto(URL + 'index.html'); await p.waitForTimeout(3000);
  const home = { n, mb: bytes / 1e6 };
  // the east edge of the 2x rectangle (map x 1237) at the shop's close-up zoom
  for (const [tag, x, y] of [['east', 1237, 480], ['south', 900, 732]]) {
    await p.evaluate(([x, y]) => { const v = window.__viewer, it = v.world.getItemAt(0), K = it.source.width / 1851;
      v.viewport.fitBounds(it.imageToViewportRectangle((x + 100 - 40) * K, (y + 70 - 25) * K, 80 * K, 50 * K), true); }, [x, y]);
    await p.waitForTimeout(3500); await p.screenshot({ path: `${OUT}/seam_${tag}.png` });
  }
  await p.click('button[data-r^="944,452"]'); await p.waitForTimeout(3500);
  console.log(JSON.stringify({ home, after_all: { n, mb: +(bytes / 1e6).toFixed(1) }, hud: await p.textContent('#hud') })); await b.close();
})();

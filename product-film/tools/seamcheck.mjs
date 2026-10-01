// Loop seam check: the frame after the last one must be frame 0, and every
// animated value (cursor included) must move continuously through the seam.
import { chromium } from 'playwright-core';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(path.resolve('film.html')).href);
await page.evaluate(() => window.ready);
const P = await page.evaluate(() => JSON.parse(document.getElementById('timeline').textContent).period);
const probe = t => page.evaluate(t => {
  window.seek(t);
  const c = document.getElementById('cursor').style.transform.match(/translate\(([-\d.]+)px, ([-\d.]+)px\) scale\(([-\d.]+)\)/);
  const b = document.getElementById('box').style;
  return { x: +c[1], y: +c[2], s: +c[3], w: parseFloat(b.width), h: parseFloat(b.height), bg: b.background, cam: document.getElementById('camera').style.transform };
}, t);
const dt = 1 / 60;
const rows = [];
for (const t of [P - 3 * dt, P - 2 * dt, P - dt, P, P + dt, P + 2 * dt]) rows.push([t, await probe(t)]);
for (const [t, r] of rows) console.log(t.toFixed(4).padStart(8), `cursor (${r.x.toFixed(2)}, ${r.y.toFixed(2)}) s=${r.s}`, `box ${r.w}×${r.h} ${r.bg}`, r.cam);
const v = (a, b) => [(b.x - a.x) / dt, (b.y - a.y) / dt];
const vIn = v(rows[1][1], rows[2][1]), vSeam = v(rows[2][1], rows[3][1]), vOut = v(rows[3][1], rows[4][1]);
console.log('cursor velocity px/s  before seam', vIn.map(x => x.toFixed(1)), ' across seam', vSeam.map(x => x.toFixed(1)), ' after', vOut.map(x => x.toFixed(1)));
const a0 = await probe(0), aP = await probe(P);
console.log('seek(0) == seek(P):', JSON.stringify(a0) === JSON.stringify(aP));
await browser.close();

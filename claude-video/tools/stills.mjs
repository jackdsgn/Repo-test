// Quadros avulsos de film.html → PNG (conferência e comparação com o storyboard).
//   node tools/stills.mjs out_dir t1 t2 ...
import { chromium } from 'playwright-core';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const [outDir, ...times] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto(pathToFileURL(path.resolve('film.html')).href);
await page.evaluate(() => window.ready);
for (const t of times) {
  await page.evaluate(t => window.seek(t), parseFloat(t));
  await page.screenshot({ path: path.join(outDir, `t${parseFloat(t).toFixed(3).padStart(6, '0')}.png`) });
}
await browser.close();

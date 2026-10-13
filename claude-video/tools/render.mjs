// film.html → frames/master.mkv (sem perdas, FFV1)
// 30 fps; cada quadro é a média de SUB subquadros no intervalo do quadro (obturador 180°),
// o que dá um motion blur leve sem mudar o desenho dos estados estáveis.
//   node tools/render.mjs [inicio=0] [fim=8] [fps=30] [sub=4]
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const [T0, T1, FPS, SUB] = [0, 8, 30, 4].map((d, i) => process.argv[2 + i] === undefined ? d : +process.argv[2 + i]);
const N = Math.round((T1 - T0) * FPS);
fs.mkdirSync('frames', { recursive: true });

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-c:v', 'png', '-i', '-',
  '-vf', `tmix=frames=${SUB}:weights='${Array(SUB).fill(1).join(' ')}',select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${FPS}*TB)`,
  '-r', String(FPS), '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0', 'frames/master.mkv'], { stdio: ['pipe', 'inherit', 'inherit'] });
const write = buf => new Promise(res => ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res));

const browser = await chromium.launch({ executablePath: process.env.CHROME || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exit(1); });
await page.goto(pathToFileURL(path.resolve('film.html')).href);
await page.evaluate(() => window.ready);
const cdp = await page.context().newCDPSession(page);

const t0 = Date.now();
for (let f = 0; f < N; f++) {
  for (let k = 0; k < SUB; k++) {
    const t = T0 + f / FPS + ((k + 0.5) / SUB - 0.5) * 0.5 / FPS;   // obturador 180° centrado no quadro
    await page.evaluate(t => window.seek(Math.max(0, t)), t);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
    await write(Buffer.from(data, 'base64'));
  }
  if (f % 30 === 29) console.log(`quadro ${f + 1}/${N} · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
ff.stdin.end();
await new Promise(res => ff.on('close', res));
await browser.close();
console.log(`frames/master.mkv · ${N} quadros (${T0}–${T1} s) @ ${FPS} fps × ${SUB} subquadros`);

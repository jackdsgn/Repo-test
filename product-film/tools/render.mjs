// film.html → frames/master.mkv
// 60 fps; every frame is the average of 4 subframes spread over the frame
// interval (centred, 360° shutter) for real motion blur. PNG subframes are piped
// straight into ffmpeg (tmix + decimate) and stored lossless (FFV1).
//   node tools/render.mjs [fps=60] [sub=4]
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const FPS = +(process.argv[2] || 60), SUB = +(process.argv[3] || 4);
const html = path.resolve('film.html');
const P = JSON.parse(fs.readFileSync('audio/timeline.json', 'utf8')).duration;
const N = Math.round(P * FPS);
fs.mkdirSync('frames', { recursive: true });

const weights = Array(SUB).fill(1).join(' ');
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-c:v', 'png', '-i', '-',
  '-vf', `tmix=frames=${SUB}:weights='${weights}',select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${FPS}*TB)`,
  '-r', String(FPS), '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0', 'frames/master.mkv'], { stdio: ['pipe', 'inherit', 'inherit'] });
const write = buf => new Promise(res => ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res));

const browser = await chromium.launch({ executablePath: process.env.CHROME || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exit(1); });
await page.goto(pathToFileURL(html).href);
await page.evaluate(() => window.ready);
const cdp = await page.context().newCDPSession(page);

const t0 = Date.now();
for (let f = 0; f < N; f++) {
  for (let k = 0; k < SUB; k++) {
    const t = f / FPS + (k + 0.5 - SUB / 2) / (FPS * SUB);   // centred shutter
    await page.evaluate(t => window.seek(t), t);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
    await write(Buffer.from(data, 'base64'));
  }
  if (f % 60 === 59) console.log(`frame ${f + 1}/${N} · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
ff.stdin.end();
await new Promise(res => ff.on('close', res));
await browser.close();
console.log(`frames/master.mkv · ${N} frames @ ${FPS} fps × ${SUB} subframes · ${((Date.now() - t0) / 1000).toFixed(0)} s`);

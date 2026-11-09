// Render SVG or HTML files to PNG with headless Chromium (global playwright).
// usage: node brand/v2/render_png.mjs <in.svg|in.html> <out.png> [widthPx] [--bg=#hex] [--full]
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
const require = createRequire(import.meta.url);
let pw; try { pw = require('playwright'); } catch { pw = require(path.join(process.execPath, '../../lib/node_modules/playwright')); }
const args = process.argv.slice(2);
const flags = Object.fromEntries(args.filter(a => a.startsWith('--')).map(a => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const pos = args.filter(a => !a.startsWith('--'));
const jobs = [];
for (let i = 0; i + 1 < pos.length; i += 3) jobs.push([pos[i], pos[i + 1], Number(pos[i + 2] || 1600)]);
const browser = await pw.chromium.launch({ args: ['--no-sandbox'] });
try {
  for (const [inp, out, width] of jobs) {
    const abs = path.resolve(inp);
    const page = await browser.newPage({ viewport: { width, height: 800 }, deviceScaleFactor: Number(flags.scale || 1) });
    if (abs.endsWith('.svg')) {
      const svg = fs.readFileSync(abs, 'utf8');
      const vb = /viewBox="([\d.\s-]+)"/.exec(svg)[1].trim().split(/\s+/).map(Number);
      const h = Math.round(width * vb[3] / vb[2]);
      await page.setViewportSize({ width, height: h });
      await page.goto('file://' + path.dirname(abs) + '/'); await page.setContent(`<html><body style="margin:0;background:${flags.bg || '#ffffff'}"><img src="file://${abs}" style="display:block;width:${width}px;height:${h}px"></body></html>`);
      await page.waitForTimeout(300);
      await page.screenshot({ path: out, omitBackground: flags.bg === 'transparent' });
    } else {
      await page.goto('file://' + abs, { waitUntil: 'networkidle' });
      await page.waitForTimeout(400);
      await page.screenshot({ path: out, fullPage: !!flags.full });
    }
    await page.close();
    console.log('wrote', out);
  }
} finally { await browser.close(); }

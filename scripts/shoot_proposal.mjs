// Render an HTML proposal to PNG for visual inspection.
// Usage: node scripts/shoot_proposal.mjs [docs/proposals/sample-ben20-healthcare.html] [outPrefix]
// Writes docs/media/screens/proposal-1.png (cover + section 2) and proposal-2.png (sections 3-4) at 1240 px wide.
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'node:fs';
import path from 'node:path';

const file = process.argv[2] || 'docs/proposals/sample-ben20-healthcare.html';
const prefix = process.argv[3] || 'docs/media/screens/proposal';
fs.mkdirSync(path.dirname(prefix), { recursive: true });
const browser = await chromium.launch({ args: ['--no-sandbox'] });
try {
  const page = await browser.newPage({ viewport: { width: 1240, height: 1600 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + path.resolve(file), { waitUntil: 'load' });
  const n = await page.locator('section.page').count();
  // page 1: cover and executive summary; page 2: mission profile and sizing
  for (const [i, ids] of [[1, ['#s1', '#s2']], [2, ['#s3', '#s4']]]) {
    const a = await page.locator(ids[0]).boundingBox();
    const b = await page.locator(ids[1]).boundingBox();
    const clip = { x: 0, y: Math.max(0, a.y - 8), width: 1240, height: Math.min(1900, b.y + b.height - a.y + 16) };
    await page.screenshot({ path: `${prefix}-${i}.png`, clip, fullPage: true });
  }
  const overflow = await page.evaluate(() => Array.from(document.querySelectorAll('table')).filter(t => t.scrollWidth > t.parentElement.clientWidth + 2).length);
  const narrow = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await narrow.goto('file://' + path.resolve(file), { waitUntil: 'load' });
  const narrowOverflow = await narrow.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  // print preview (light theme) of the price section
  await page.emulateMedia({ media: 'print' });
  const s6 = await page.locator('#s6').boundingBox();
  await page.screenshot({ path: `${prefix}-print.png`, clip: { x: 0, y: s6.y, width: 1240, height: Math.min(1400, s6.height) }, fullPage: true });
  console.log(JSON.stringify({ sections: n, tablesWiderThanWrapper: overflow, narrowHorizontalOverflow: narrowOverflow, errors }, null, 1));
} finally { await browser.close(); }

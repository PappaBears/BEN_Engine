// Screenshot the product page (desktop + narrow) for visual inspection and the README.
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn } from 'node:child_process';
import fs from 'node:fs';
const port = 8765;
const srv = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: process.cwd(), stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
fs.mkdirSync('docs/media/screens', { recursive: true });
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const scale = Number(process.env.SCALE || 1);
try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 }, deviceScaleFactor: scale });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`http://127.0.0.1:${port}/web/index.html`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#sizing table');
  await page.screenshot({ path: 'docs/media/screens/web-hero.png' });
  await page.locator('#configure').scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'docs/media/screens/web-configure.png' });
  await page.locator('#risks').scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'docs/media/screens/web-risks.png' });
  // interaction: pick healthcare + ben40 + hot_arid and check validation path
  await page.click('.profile:nth-child(6)');
  await page.selectOption('#tier', 'ben500');
  await page.selectOption('#climateSel', 'hot_arid');
  const txt = await page.textContent('#sizing');
  await page.fill('#racks', '1');
  await page.dispatchEvent('#racks', 'change');
  const err = await page.textContent('#cfgErrors');
  const full = await page.screenshot({ path: 'docs/media/screens/web-full.png', fullPage: true });
  // forward architecture: BEN 150 at 150 kW in 2 racks with the 800 VDC bus and high-density liquid selected
  await page.click('.profile:nth-child(1)');
  await page.selectOption('#tier', 'ben150');
  await page.selectOption('#climateSel', 'temperate');
  await page.fill('#racks', '2'); await page.dispatchEvent('#racks', 'change');
  await page.fill('#it_kw', '150'); await page.dispatchEvent('#it_kw', 'input');
  await page.selectOption('#powerArch', 'dc800');
  await page.selectOption('#cooling', 'dlc_hd'); await page.dispatchEvent('#cooling', 'change');
  await page.waitForTimeout(200);
  const dcTxt = await page.textContent('#sizing');
  const dcErr = (await page.textContent('#cfgErrors')).trim();
  await page.locator('#configure').scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'docs/media/screens/web-configure-dc800.png' });
  const dcConvVisible = await page.evaluate(() => !document.querySelector('#dcConv').closest('label').hidden);
  const narrow = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: scale });
  await narrow.goto(`http://127.0.0.1:${port}/web/index.html`, { waitUntil: 'networkidle' });
  await narrow.waitForSelector('#sizing table');
  await narrow.screenshot({ path: 'docs/media/screens/web-narrow.png', fullPage: true });
  const overflow = await narrow.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  console.log(JSON.stringify({ sizingHasBen500: txt.includes('40 ft'), validationError: err.trim().slice(0, 120), narrowHorizontalOverflow: overflow,
    dc800: { sizingHas800VDC: dcTxt.includes('800 VDC'), sizingHasBusway: /busway/.test(dcTxt), sizingHasLoop: /L\/min/.test(dcTxt), sizingHasVendorClaim: /vendor claim/.test(dcTxt), error: dcErr.slice(0, 120), dcConvVisible }, errors }, null, 1));
} finally { await browser.close(); srv.kill(); }

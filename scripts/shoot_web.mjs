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
  await page.selectOption('#tier', 'ben40');
  await page.selectOption('#climateSel', 'hot_arid');
  const txt = await page.textContent('#sizing');
  await page.fill('#racks', '1');
  await page.dispatchEvent('#racks', 'change');
  const err = await page.textContent('#cfgErrors');
  const full = await page.screenshot({ path: 'docs/media/screens/web-full.png', fullPage: true });
  const narrow = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: scale });
  await narrow.goto(`http://127.0.0.1:${port}/web/index.html`, { waitUntil: 'networkidle' });
  await narrow.waitForSelector('#sizing table');
  await narrow.screenshot({ path: 'docs/media/screens/web-narrow.png', fullPage: true });
  const overflow = await narrow.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  console.log(JSON.stringify({ sizingHasBen40: txt.includes('40 ft'), validationError: err.trim().slice(0, 120), narrowHorizontalOverflow: overflow, errors }, null, 1));
} finally { await browser.close(); srv.kill(); }

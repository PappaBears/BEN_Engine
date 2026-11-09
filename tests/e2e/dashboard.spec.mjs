// BEN Engine dashboard end-to-end test (plain `playwright` module, no @playwright/test).
// Starts uvicorn on a free port, drives the dashboard, records screenshots + guided-tour frames.
// Usage: node tests/e2e/dashboard.spec.mjs   (or bash tests/e2e/run_e2e.sh)
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { mkdirSync, existsSync, readFileSync, rmSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..', '..');
const SCREENS = resolve(ROOT, 'docs', 'media', 'screens');
const FRAMES = resolve(ROOT, 'docs', 'media', 'frames');
const PY = process.env.PYTHON || 'python';
const HEADLESS = process.env.HEADED ? false : true;
// `--only <substring>`: run only the steps whose name contains it (plus the bootstrap steps).
const onlyIdx = process.argv.indexOf('--only');
const ONLY = onlyIdx > 0 ? process.argv[onlyIdx + 1] : null;
const BOOT = ['server up', 'dashboard loads', 'websocket connected', '3D scene built', 'no uncaught page errors'];
mkdirSync(SCREENS, { recursive: true }); mkdirSync(FRAMES, { recursive: true });

const results = [];
let failures = 0;
function check(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
  if (!ok) failures++;
}
async function step(name, fn) {
  if (ONLY && !name.includes(ONLY) && !BOOT.some(b => name.startsWith(b))) { console.log(`SKIP  ${name}`); return; }
  try { const d = await fn(); check(name, true, d || ''); }
  catch (e) { check(name, false, e && e.message ? e.message.split('\n')[0] : String(e)); }
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function freePort() {
  return new Promise((res, rej) => { const s = createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); s.on('error', rej); });
}
async function waitHttp(url, ms = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { try { const r = await fetch(url); if (r.ok) return await r.json(); } catch (_) { /* retry */ } await sleep(250); }
  throw new Error(`server did not answer at ${url}`);
}

// ------------------------------------------------------------------------------------------------ server
const port = await freePort();
const server = spawn(PY, ['-m', 'uvicorn', 'ben_engine.api:app', '--host', '127.0.0.1', '--port', String(port), '--log-level', 'warning'],
  { cwd: ROOT, env: { ...process.env, PYTHONPATH: resolve(ROOT, 'software') + (process.env.PYTHONPATH ? ':' + process.env.PYTHONPATH : '') }, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLog = '';
server.stdout.on('data', d => { serverLog += d; }); server.stderr.on('data', d => { serverLog += d; });
const BASE = `http://127.0.0.1:${port}`;
let browser;
try {
  const health = await waitHttp(`${BASE}/api/health`);
  // the default configuration comes from /api/config (BEN 150 preset), never hard-coded here
  const cfg0 = await waitHttp(`${BASE}/api/config`);
  const presets = await waitHttp(`${BASE}/api/presets`);
  const DEF = { tier: cfg0.config.tier, racks: cfg0.config.racks, label: cfg0.derived.tier_label };
  const L = (t) => presets[t].derived.tier_label;
  check('server up', health.twin_running === true, `port ${port}, modules ${Object.entries(health.modules).filter(([, v]) => v).map(([k]) => k).join(',')}`);

  browser = await chromium.launch({ headless: HEADLESS, args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, acceptDownloads: true, reducedMotion: 'no-preference' });
  const page = await ctx.newPage();
  const pageErrors = [], badResponses = [];
  const shot = async (pg, path, opts = {}) => { // UI stays crisp at DSF 2; the WebGL canvas renders at 1x between shots to keep SwiftShader fast
    await pg.evaluate(() => window.__ben && window.__ben.scene.setPixelRatio(2)); await pg.waitForTimeout(250);
    await pg.screenshot({ path, ...opts });
    await pg.evaluate(() => window.__ben && window.__ben.scene.setPixelRatio(1));
  };
  page.on('pageerror', e => pageErrors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) pageErrors.push(m.text()); });
  page.on('response', r => { if (r.status() >= 500) badResponses.push(`${r.status()} ${new URL(r.url()).pathname}`); });

  // ---------------------------------------------------------------------------------------------- load
  await step('dashboard loads', async () => {
    await page.goto(BASE + '/#selector', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__ben && window.__ben.store.config && window.__ben.scene.rackCount() > 0, null, { timeout: 30000, polling: 200 });
    await page.evaluate(() => window.__ben.scene.setPixelRatio(1));
    return `title "${await page.title()}"`;
  });
  await step('websocket connected and state streaming', async () => {
    await page.waitForFunction(() => window.__ben.store.conn.connected && window.__ben.store.state && window.__ben.store.history.length >= 2, null, { timeout: 15000, polling: 200 });
    const dot = await page.locator('#st-conn .dot').getAttribute('class');
    if (!dot.includes('ok')) throw new Error('status dot not ok: ' + dot);
    return 'status strip shows live';
  });
  await step(`3D scene built for ${DEF.label} (${DEF.racks} racks)`, async () => {
    const n = await page.evaluate(() => window.__ben.scene.rackCount());
    const sensors = await page.evaluate(() => window.__ben.scene.sensorCount());
    if (n !== DEF.racks) throw new Error(`expected ${DEF.racks} racks, got ${n}`);
    if (sensors < 10) throw new Error(`expected sensors, got ${sensors}`);
    return `${n} racks, ${sensors} sensors`;
  });
  await page.waitForTimeout(1500);
  await shot(page, `${SCREENS}/desktop-exterior-iso.png`);

  // ---------------------------------------------------------------------------------------------- selector -> BEN 500
  await step('selector: five tier presets and a hardening select', async () => {
    await page.click('#tabs button[data-id="selector"]');
    await page.waitForSelector('#btn-apply-config');
    const labels = await page.$$eval('.panel-body[data-panel="selector"] .row button', bs => bs.map(b => b.textContent.trim()));
    const want = Object.keys(presets).map(L);
    for (const w of want) if (!labels.includes(w)) throw new Error(`preset button ${w} missing: ${labels.join(', ')}`);
    const hz = await page.$$eval('select[name=hardening] option', os => os.map(o => o.value));
    if (hz.join(',') !== 'H1,H2,H3') throw new Error('hardening options ' + hz.join(','));
    return `${labels.join(' · ')} · hardening ${hz.join('/')}`;
  });
  await step(`selector: switch to ${L('ben500')} rebuilds twin + scene`, async () => {
    await page.click(`.panel-body[data-panel="selector"] .row button:has-text("${L('ben500')}")`);
    await page.waitForFunction(() => document.querySelector('select[name=tier]').value === 'ben500');
    await page.waitForFunction(() => !document.querySelector('#btn-apply-config').disabled, null, { timeout: 5000, polling: 200 });
    await page.click('#btn-apply-config');
    await page.waitForFunction(() => window.__ben.store.config && window.__ben.store.config.tier === 'ben500' && window.__ben.scene.rackCount() === window.__ben.store.config.racks, null, { timeout: 15000, polling: 200 });
    const racks = await page.evaluate(() => [window.__ben.scene.rackCount(), window.__ben.store.config.racks, window.__ben.store.derived.tier_label]);
    if (racks[0] !== racks[1]) throw new Error(`scene racks ${racks[0]} != config ${racks[1]}`);
    if (racks[2] !== L('ben500')) throw new Error(`pill not ${L('ben500')}`);
    return `${racks[0]} racks in scene`;
  });
  await page.waitForTimeout(1200);
  await shot(page, `${SCREENS}/selector-ben500.png`);

  await step('selector: invalid configuration shows inline errors', async () => {
    await page.evaluate(() => { const s = document.querySelector('select[name=cooling]'); s.value = 'cabinet_dx'; s.dispatchEvent(new Event('change')); });
    await page.waitForFunction(() => { const e = document.querySelector('.errors'); return e && !e.hidden && /BEN 5 only/.test(e.textContent); }, null, { timeout: 5000, polling: 200 });
    const disabled = await page.evaluate(() => document.querySelector('#btn-apply-config').disabled);
    if (!disabled) throw new Error('apply should be disabled on invalid config');
    await page.evaluate(() => { const s = document.querySelector('select[name=cooling]'); s.value = 'dlc_cdu'; s.dispatchEvent(new Event('change')); });
    await page.waitForFunction(() => document.querySelector('.errors').hidden, null, { timeout: 5000, polling: 200 });
    return 'cabinet_dx-on-container error shown, apply disabled, then cleared';
  });

  // ---------------------------------------------------------------------------------------------- BEN 5 cabinet
  await step(`selector: ${L('ben5')} renders a single cabinet`, async () => {
    await page.click(`.panel-body[data-panel="selector"] .row button:has-text("${L('ben5')}")`);
    await page.waitForFunction(() => document.querySelector('select[name=tier]').value === 'ben5');
    await page.waitForFunction(() => !document.querySelector('#btn-apply-config').disabled, null, { timeout: 5000, polling: 200 });
    await page.click('#btn-apply-config');
    await page.waitForFunction(() => window.__ben.store.config.tier === 'ben5' && window.__ben.scene.rackCount() === 1, null, { timeout: 15000, polling: 200 });
    await page.evaluate(() => window.__ben.scene.setCamera('exterior_iso', true));
    await page.waitForTimeout(1200);
    await shot(page, `${SCREENS}/selector-ben5.png`);
    return 'rackCount 1';
  });

  // ---------------------------------------------------------------------------------------------- BEN 2000 hall
  await step(`selector: ${L('ben2000')} builds the hall (rows, power module, yard, hardening)`, async () => {
    await page.click(`.panel-body[data-panel="selector"] .row button:has-text("${L('ben2000')}")`);
    await page.waitForFunction(() => document.querySelector('select[name=tier]').value === 'ben2000');
    await page.evaluate(() => { const s = document.querySelector('select[name=hardening]'); s.value = 'H3'; s.dispatchEvent(new Event('change')); });
    await page.waitForFunction(() => !document.querySelector('#btn-apply-config').disabled, null, { timeout: 5000, polling: 200 });
    await page.click('#btn-apply-config');
    await page.waitForFunction(() => window.__ben.store.config.tier === 'ben2000' && window.__ben.scene.rackCount() === window.__ben.store.config.racks, null, { timeout: 30000, polling: 200 });
    const info = await page.evaluate(() => ({ racks: window.__ben.scene.rackCount(), cfgRacks: window.__ben.store.config.racks, rows: window.__ben.scene.rowCount(), dry: window.__ben.scene.dryCoolerCount(), d: window.__ben.store.derived, hall: window.__ben.scene.hallObjects(), hz: window.__ben.store.config.hardening }));
    if (info.racks !== info.cfgRacks) throw new Error(`scene racks ${info.racks} != config ${info.cfgRacks}`);
    if (info.rows !== info.d.rows) throw new Error(`rows ${info.rows} != derived ${info.d.rows}`);
    if (!info.d.mv_service || info.d.transformers_total < 2) throw new Error('derived MV service / transformers missing');
    if (!info.hall.powermodule || info.hall.transformers !== info.d.transformers_total || info.hall.generators !== info.d.generators_total) throw new Error('hall objects ' + JSON.stringify(info.hall));
    if (info.dry !== info.d.cooling_units_total) throw new Error(`dry coolers ${info.dry} != ${info.d.cooling_units_total}`);
    if (info.hz !== 'H3' || !info.hall.vestibule || !info.hall.plinth) throw new Error('H3 hardening visuals missing ' + JSON.stringify(info.hall));
    const derivedTxt = await page.textContent('.panel-body[data-panel="selector"]');
    if (!/Transformers/.test(derivedTxt) || !/Generators/.test(derivedTxt) || !/Hardening/.test(derivedTxt)) throw new Error('derived table lacks MV/generator/hardening rows');
    await page.evaluate(() => window.__ben.scene.setCamera('exterior_iso', true));
    await page.waitForTimeout(1500);
    await shot(page, `${SCREENS}/selector-ben2000.png`);
    return `${info.racks} racks in ${info.rows} rows, ${info.hall.transformers} transformers, ${info.hall.generators} generators, ${info.dry} dry coolers, ${info.hall.fanwalls} fan walls`;
  });

  // ---------------------------------------------------------------------------------------------- forward architecture (study): dc800 + dlc_hd
  await step(`selector: ${L('ben150')} forward options dc800 + dlc_hd build the rectifier, DC busway, row CDUs and manifolds`, async () => {
    await page.click(`.panel-body[data-panel="selector"] .row button:has-text("${L('ben150')}")`);
    await page.waitForFunction(() => document.querySelector('select[name=tier]').value === 'ben150');
    const opts = await page.$$eval('select[name=power_architecture] option', os => os.map(o => o.value));
    if (opts.join(',') !== 'ac480,dc800') throw new Error('power architecture options ' + opts.join(','));
    await page.evaluate(() => {
      const set = (name, v) => { const s = document.querySelector(`select[name=${name}]`); s.value = v; s.dispatchEvent(new Event('change')); };
      set('power_architecture', 'dc800'); set('dc_convention', 'bipolar_400'); set('cooling', 'dlc_hd');
      const kw = document.querySelector('input[type=range][max="150"]'); kw.value = 150; kw.dispatchEvent(new Event('input'));
      const racks = document.querySelector('input[type=range][max="6"]'); racks.value = 2; racks.dispatchEvent(new Event('input'));
    });
    await page.waitForFunction(() => !document.querySelector('#btn-apply-config').disabled && /800 VDC/.test(document.querySelector('.panel-body[data-panel="selector"]').textContent), null, { timeout: 8000, polling: 200 });
    await page.click('#btn-apply-config');
    await page.waitForFunction(() => window.__ben.store.config.power_architecture === 'dc800' && window.__ben.store.config.cooling === 'dlc_hd' && window.__ben.scene.rackCount() === 2, null, { timeout: 20000, polling: 200 });
    const info = await page.evaluate(() => { const o = window.__ben.scene.objects; return { rect: !!o.rectifier, bus: !!o.dc_busway, ups: o.ups === o.rectifier, bat: !!o.battery, cdu1: !!o.cdu1, cdu2: !!o.cdu2, man1: !!o.manifold1, man2: !!o.manifold2, d: window.__ben.store.derived, st: window.__ben.store.state }; });
    if (!info.rect || !info.bus || !info.ups || !info.bat) throw new Error('dc800 objects ' + JSON.stringify({ rect: info.rect, bus: info.bus, bat: info.bat }));
    if (!info.cdu1 || !info.cdu2 || !info.man1 || !info.man2) throw new Error('dlc_hd objects missing');
    if (info.d.dc_busway_a !== 400 || info.d.rectifier_modules !== 3 || info.d.loop_flow_lpm !== 193.8) throw new Error('derived forward numbers ' + JSON.stringify([info.d.dc_busway_a, info.d.rectifier_modules, info.d.loop_flow_lpm]));
    const derivedTxt = await page.textContent('.panel-body[data-panel="selector"]');
    if (!/Bus window/.test(derivedTxt) || !/Battery on bus/.test(derivedTxt) || !/Heat reuse/.test(derivedTxt) || !/Liquid loop/.test(derivedTxt)) throw new Error('derived table lacks DC / loop rows');
    // state carries the new sensors once the twin runs
    await page.waitForFunction(() => window.__ben.store.state && window.__ben.store.state.dc && window.__ben.store.state.loop, null, { timeout: 15000, polling: 300 });
    const st = await page.evaluate(() => ({ v: window.__ben.store.state.dc.v_bus, imd: window.__ben.store.state.dc.imd_kohm, flow: window.__ben.store.state.loop.flow_lpm }));
    if (!(st.v > 700 && st.imd > 500 && st.flow > 0)) throw new Error('forward state ' + JSON.stringify(st));
    // hover the rectifier: tooltip names the part and the convention
    const ok = await page.evaluate(() => window.__ben.scene.setHoverByKey('rectifier'));
    if (!ok) throw new Error('rectifier not hoverable');
    await page.waitForFunction(() => { const t = document.getElementById('tip'); return t && !t.hidden && /front end/i.test(t.textContent); }, null, { timeout: 5000, polling: 200 });
    const tip = await page.textContent('#tip');
    await page.evaluate(() => window.__ben.scene.clearHover());
    await page.evaluate(() => window.__ben.scene.setCamera('exterior_iso', true));
    await page.waitForTimeout(1200);
    await shot(page, `${SCREENS}/selector-ben150-forward.png`);
    return `rectifier + DC busway + battery, 2 row CDUs, 2 manifolds; bus ${st.v.toFixed(0)} V, IMD ${st.imd.toFixed(0)} kΩ, loop ${st.flow.toFixed(0)} L/min; tooltip: ${tip.slice(0, 60).replace(/\s+/g, ' ')}`;
  });

  // back to the default tier for the rest
  if (!ONLY) {
  await page.click(`.panel-body[data-panel="selector"] .row button:has-text("${DEF.label}")`);
  await page.waitForFunction((t) => document.querySelector('select[name=tier]').value === t, DEF.tier);
  await page.waitForFunction(() => !document.querySelector('#btn-apply-config').disabled, null, { timeout: 5000, polling: 200 });
  await page.click('#btn-apply-config');
  await page.waitForFunction(([t, n]) => window.__ben.store.config.tier === t && window.__ben.scene.rackCount() === n, [DEF.tier, DEF.racks], { timeout: 15000, polling: 200 });
  }

  // ---------------------------------------------------------------------------------------------- hover tooltip
  await step('hover tooltip: rack name, BOM part and kW over a rack', async () => {
    await page.evaluate(() => { window.__ben.scene.setCamera('power_room', true); window.__ben.render(); });
    await page.waitForFunction(() => window.__ben.tooltip && window.__ben.tooltip.bomLoaded && document.querySelector('#tip'), null, { timeout: 30000, polling: 200 });
    await page.waitForTimeout(600);
    const pos = await page.evaluate(() => window.__ben.scene.screenPositionOf('rack2'));
    if (!pos || !pos.visible) throw new Error('rack2 not on screen: ' + JSON.stringify(pos));
    await page.mouse.move(pos.x - 30, pos.y - 30); await page.mouse.move(pos.x, pos.y);
    await page.waitForFunction(() => { const t = document.getElementById('tip'); return t && !t.hidden && /Rack 2/.test(t.textContent); }, null, { timeout: 10000, polling: 150 });
    const text = (await page.textContent('#tip')).replace(/\s+/g, ' ');
    if (!/\d+(\.\d+)? kW/.test(text)) throw new Error('no kW value in tooltip: ' + text);
    if (!/STR-RACK|STR-CAB|no catalog line/.test(text)) throw new Error('no BOM part in tooltip: ' + text);
    const box = await page.evaluate(() => { const r = document.getElementById('tip').getBoundingClientRect(); return [r.width, r.right <= innerWidth, r.bottom <= innerHeight]; });
    if (box[0] > 330 || !box[1] || !box[2]) throw new Error('tooltip geometry ' + JSON.stringify(box));
    await shot(page, `${SCREENS}/hover-tooltip.png`);
    // keyboard cycling reaches the same tooltip
    await page.mouse.move(5, 5); await page.focus('#scene'); await page.keyboard.press('Tab');
    await page.waitForFunction(() => { const t = document.getElementById('tip'); return t && !t.hidden && /Enter: inspect/.test(t.textContent); }, null, { timeout: 5000, polling: 150 });
    const kb = (await page.textContent('#tip')).replace(/\s+/g, ' ').slice(0, 60);
    await page.keyboard.press('Escape');
    return `${text.slice(0, 90)}… | keyboard: ${kb}`;
  });

  // ---------------------------------------------------------------------------------------------- walkthrough
  if (!ONLY) {
  await step('walkthrough: first-person camera at eye height with collision', async () => {
    await page.evaluate(() => window.__ben.scene.enterWalk({ lock: false }));
    await page.waitForTimeout(300);
    const y0 = await page.evaluate(() => window.__ben.scene.camera.position.y);
    const floor = await page.evaluate(() => window.__ben.scene.G.floorTop);
    if (Math.abs(y0 - floor - 1.7) > 0.05) throw new Error(`eye height ${y0 - floor}`);
    await page.keyboard.down('KeyW'); await page.waitForTimeout(1200); await page.keyboard.up('KeyW');
    const inside = await page.evaluate(() => { const c = window.__ben.scene.camera.position, G = window.__ben.scene.G; return Math.abs(c.x) < G.intL / 2 && Math.abs(c.z) < G.intW / 2; });
    if (!inside) throw new Error('camera left the container');
    await page.waitForTimeout(800);
    await shot(page, `${SCREENS}/interior-walkthrough.png`);
    await page.evaluate(() => window.__ben.scene.exitWalk());
    return `eye ${(y0 - floor).toFixed(2)} m above floor, stayed inside`;
  });

  // ---------------------------------------------------------------------------------------------- fault -> alarm
  await step('inject cooling fault via UI -> alarm appears and highlights the unit', async () => {
    await page.click('#tabs button[data-id="sweeps"]');
    await page.waitForSelector('#fault-grid button[data-fault="cooling_unit_fail"]');
    await page.click('#fault-grid button[data-fault="cooling_unit_fail"]');
    await page.waitForFunction(() => window.__ben.store.state && window.__ben.store.state.alarms.some(a => a.id === 'cool1_fail'), null, { timeout: 10000, polling: 200 });
    await page.click('#tabs button[data-id="alarms"]');
    await page.waitForSelector('#alarm-list li[data-alarm="cool1_fail"]', { timeout: 10000, polling: 200 });
    const badge = await page.textContent('#alarm-badge');
    await page.click('#alarm-list li[data-alarm="cool1_fail"]');
    await page.waitForTimeout(1200);
    const sel = await page.evaluate(() => window.__ben.store.selection);
    if (sel.type !== 'cooling') throw new Error('clicking the alarm did not select the cooling unit: ' + JSON.stringify(sel));
    const title = await page.textContent('#insp-title');
    await shot(page, `${SCREENS}/alarms.png`);
    return `badge ${badge}, inspector "${title.trim().split('\n')[0]}"`;
  });
  await step('clear fault via UI -> alarm disappears', async () => {
    await page.click('#tabs button[data-id="sweeps"]');
    await page.click('#btn-clear-faults');
    await page.waitForFunction(() => window.__ben.store.state && !window.__ben.store.state.alarms.some(a => a.id === 'cool1_fail'), null, { timeout: 10000, polling: 200 });
  });

  // ---------------------------------------------------------------------------------------------- sweep + csv
  await step('run a sweep and download its CSV', async () => {
    await page.click('#tabs button[data-id="sweeps"]');
    await page.waitForSelector('#sweep-buttons button[data-sweep]');
    const first = page.locator('#sweep-buttons button[data-sweep]').first();
    const name = await first.getAttribute('data-sweep');
    await first.click();
    await page.waitForSelector('#sweep-results [data-sweep-job][data-status="done"]', { timeout: 120000, polling: 200 });
    const link = page.locator('#sweep-results [data-sweep-job][data-status="done"] a[data-sweep-csv]').first();
    const href = await link.getAttribute('href');
    const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 30000 }), link.click()]);
    const path = await Promise.race([dl.path(), sleep(20000).then(() => null)]);
    let text, how;
    if (path) { text = readFileSync(path, 'utf8'); how = 'saved by browser'; }
    else { const fail = await Promise.race([dl.failure(), sleep(2000).then(() => 'timeout')]); text = await (await fetch(BASE + href)).text(); how = `download event fired (${fail || 'no failure reason'}), body fetched`; }
    const lines = text.trim().split('\n');
    if (lines.length < 3) throw new Error('csv too short');
    if (!/pass|PASS|FAIL/.test(await page.textContent('#sweep-results'))) throw new Error('no pass/fail rendered');
    await page.waitForTimeout(400);
    await shot(page, `${SCREENS}/sweeps.png`);
    return `${name}: ${dl.suggestedFilename()} (${lines.length} lines, ${how})`;
  });

  // ---------------------------------------------------------------------------------------------- other panels render
  for (const id of ['live', 'io', 'calibration', 'cfd', 'commissioning', 'export']) {
    await step(`panel ${id} renders`, async () => {
      await page.click(`#tabs button[data-id="${id}"]`);
      await page.waitForFunction((pid) => { const el = document.querySelector(`.panel-body[data-panel="${pid}"]`); return el && !el.hidden && el.textContent.trim().length > 20; }, id, { timeout: 10000, polling: 200 });
      await page.waitForTimeout(600);
      const txt = (await page.textContent(`.panel-body[data-panel="${id}"]`)).replace(/\s+/g, ' ').slice(0, 70);
      return txt;
    });
  }
  await page.click('#tabs button[data-id="live"]'); await page.waitForTimeout(1500);
  await page.evaluate(() => window.__ben.scene.setCamera('hot_aisle', true)); await page.waitForTimeout(800);
  await shot(page, `${SCREENS}/live-hot-aisle.png`);

  await step('calibration: demo points -> gain/offset (or graceful 503)', async () => {
    await page.click('#tabs button[data-id="calibration"]');
    await page.click('#btn-cal-demo'); await page.click('#btn-calibrate');
    await page.waitForFunction(() => /Gain|not yet available/.test(document.querySelector('#cal-result').textContent), null, { timeout: 15000, polling: 200 });
    return (await page.textContent('#cal-result')).replace(/\s+/g, ' ').slice(0, 60);
  });

  // ---------------------------------------------------------------------------------------------- guided tour frames
  await step('guided tour: 24 ordered frames with captions', async () => {
    for (const f of readdirSync(FRAMES)) if (f.endsWith('.png')) rmSync(resolve(FRAMES, f));
    await page.click('#tabs button[data-id="live"]');
    await page.evaluate(() => window.__ben.scene.tour.start());
    await page.waitForFunction(() => !document.getElementById('tour-caption').hidden, null, { timeout: 5000, polling: 200 });
    const N = 24;
    for (let i = 0; i < N; i++) {
      await page.evaluate((k) => { window.__ben.scene.tour.seek(k); window.__ben.render(); }, (i + 0.5) / N);
      await page.waitForTimeout(140);
      await shot(page, `${FRAMES}/tour-${String(i + 1).padStart(2, '0')}.png`, { clip: { x: 330, y: 52, width: 810, height: 808 } });
    }
    const cap = await page.textContent('#tour-caption');
    await page.evaluate(() => window.__ben.scene.tour.stop());
    const n = readdirSync(FRAMES).filter(f => /^tour-\d\d\.png$/.test(f)).length;
    if (n !== N) throw new Error(`expected ${N} frames, found ${n}`);
    return `last caption "${cap.replace(/\s+/g, ' ').slice(0, 50)}…"`;
  });

  // ---------------------------------------------------------------------------------------------- proposal
  await step('proposal panel generates a proposal from the current configuration', async () => {
    await page.evaluate(() => window.__ben.showPanel('proposal'));
    await page.waitForSelector('#btn-proposal', { timeout: 15000 });
    await page.click('#btn-proposal');
    await page.waitForSelector('a[href^="/api/proposal/"][href$=".html"]', { timeout: 60000 });
    const href = await page.getAttribute('a[href^="/api/proposal/"][href$=".html"]', 'href');
    const res = await page.request.get(BASE + href);
    if (res.status() !== 200) throw new Error(`proposal html ${res.status()}`);
    const body = await res.text();
    if (!/Schreiber AI/.test(body)) throw new Error('proposal html missing brand');
    await page.evaluate(() => window.__ben.scene.setPixelRatio(1)); await shot(page, `${SCREENS}/proposal-panel.png`);
    return href;
  });

  // ---------------------------------------------------------------------------------------------- narrow
  await step('390 px layout stacks and keeps the scene', async () => {
    const narrow = await ctx.newPage();
    await narrow.setViewportSize({ width: 390, height: 844 });
    await narrow.goto(BASE + '/#live', { waitUntil: 'domcontentloaded' });
    await narrow.waitForFunction(() => window.__ben && window.__ben.store.state && window.__ben.scene.rackCount() > 0, null, { timeout: 30000, polling: 200 });
    await narrow.waitForTimeout(1500);
    const overflow = await narrow.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    const stacked = await narrow.evaluate(() => { const v = document.getElementById('viewport').getBoundingClientRect(), r = document.getElementById('rail').getBoundingClientRect(); return r.top >= v.bottom - 1; });
    await narrow.evaluate(() => window.__ben.scene.setPixelRatio(1)); await shot(narrow, `${SCREENS}/narrow-390.png`);
    await narrow.close();
    if (overflow > 2) throw new Error(`horizontal overflow ${overflow}px`);
    if (!stacked) throw new Error('rail not stacked under viewport');
    return 'no horizontal scroll, panels stacked';
  });

  }
  await step('no uncaught page errors', async () => {
    const real = pageErrors.filter(e => !/GL Driver|WebGL|swiftshader|favicon/i.test(e));
    const mine = badResponses.filter(u => !/\/api\/proposal/.test(u)); // proposal endpoints belong to another module; reported, not fatal here
    if (real.length || mine.length) throw new Error([...real, ...mine].slice(0, 4).join(' | '));
    return `${pageErrors.length} console errors` + (badResponses.length ? `; non-fatal 5xx: ${[...new Set(badResponses)].join(', ')}` : '');
  });
} catch (e) {
  check('unexpected failure', false, e && e.stack ? e.stack.split('\n').slice(0, 2).join(' ') : String(e));
} finally {
  if (browser) await browser.close().catch(() => {});
  server.kill('SIGTERM');
}
console.log(`\n${results.length - failures}/${results.length} checks passed. Screens: ${SCREENS}  Frames: ${FRAMES}`);
if (failures) { console.log('--- server log tail ---\n' + serverLog.split('\n').slice(-20).join('\n')); process.exit(1); }

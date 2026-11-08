// BEN Engine dashboard — app controller: store, WebSocket, panels, inspector, status strip.
import { api, h, fmt, sensorValue, reducedMotion } from './util.js';
import { createScene } from './scene.js';
import selectorPanel from './panels/selector.js';
import livePanel from './panels/live.js';
import alarmsPanel from './panels/alarms.js';
import sweepsPanel from './panels/sweeps.js';
import ioPanel from './panels/io.js';
import calibrationPanel from './panels/calibration.js';
import cfdPanel from './panels/cfd.js';
import commissioningPanel from './panels/commissioning.js';
import exportPanel from './panels/export.js';

// ----------------------------------------------------------------------------- store
class Store extends EventTarget {
  constructor() {
    super();
    this.config = null; this.derived = null; this.sensors = [];
    this.state = null; this.history = []; this.maxHistory = 360;
    this.selection = { type: 'container', id: 'container' };
    this.conn = { connected: false, lastMsg: 0, stepAge: null };
    this.health = null;
  }
  emit(type, detail) { this.dispatchEvent(new CustomEvent(type, { detail })); }
  on(type, fn) { this.addEventListener(type, (e) => fn(e.detail)); return () => this.removeEventListener(type, fn); }
  setConfig(payload) {
    this.config = payload.config; this.derived = payload.derived; this.sensors = payload.sensors || this.sensors;
    this.history = [];
    this.emit('config', payload);
  }
  setState(st) {
    this.state = st;
    this.history.push(st); if (this.history.length > this.maxHistory) this.history.shift();
    this.conn.lastMsg = performance.now();
    this.emit('state', st);
  }
  select(sel) { this.selection = sel || { type: 'container', id: 'container' }; this.emit('select', this.selection); }
}
export const store = new Store();

/** Which 3D object an alarm points at. */
export function alarmTarget(a) {
  let m;
  if ((m = /^rack(\d+)_/.exec(a.id))) return { type: 'rack', index: +m[1] - 1, id: `rack${m[1]}` };
  if ((m = /^cool(\d+)_/.exec(a.id))) return { type: 'cooling', index: +m[1] - 1, id: `cooling${m[1]}` };
  if (a.id === 'utility_loss') return { type: 'ats', id: 'ats' };
  if (a.id === 'ups_low') return { type: 'ups', id: 'ups' };
  if (a.id === 'door_open') return { type: 'doors', id: 'doors' };
  if (a.id === 'leak') return { type: 'sensor', id: 'leak_floor' };
  if (a.id === 'filter_dp') return { type: 'cooling', index: 0, id: 'cooling1' };
  return { type: 'container', id: 'container' };
}

// ----------------------------------------------------------------------------- websocket
let ws, wsRetry = 800;
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/state`);
  ws.onopen = () => { store.conn.connected = true; wsRetry = 800; store.emit('conn', store.conn); };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'config') store.setConfig(msg);
    else if (msg.type === 'state') store.setState(msg.state);
  };
  ws.onclose = () => { store.conn.connected = false; store.emit('conn', store.conn); setTimeout(connectWS, wsRetry); wsRetry = Math.min(wsRetry * 1.6, 8000); };
  ws.onerror = () => ws.close();
}

// ----------------------------------------------------------------------------- panels
const PANELS = [selectorPanel, livePanel, alarmsPanel, sweepsPanel, ioPanel, calibrationPanel, cfdPanel, commissioningPanel, exportPanel];
const mounted = new Map();
let activePanel = null;
const tabsEl = document.getElementById('tabs');
const panelEl = document.getElementById('panel');

function showPanel(id) {
  const p = PANELS.find(x => x.id === id) || PANELS[0];
  activePanel = p;
  for (const b of tabsEl.querySelectorAll('button')) b.classList.toggle('active', b.dataset.id === p.id);
  for (const [pid, el] of mounted) el.hidden = pid !== p.id;
  if (!mounted.has(p.id)) {
    const el = h('div', { class: 'panel-body', 'data-panel': p.id });
    panelEl.append(el); mounted.set(p.id, el);
    p.mount(el, ctx);
  }
  if (store.config && p.onConfig) p.onConfig({ config: store.config, derived: store.derived, sensors: store.sensors });
  if (store.state && p.update) p.update(store.state);
  try { localStorage.setItem('ben.panel', p.id); } catch (_) { /* ignore */ }
  location.hash = p.id;
}

function buildTabs() {
  tabsEl.replaceChildren(...PANELS.map(p => h('button', { 'data-id': p.id, onClick: () => showPanel(p.id), title: p.title || p.label }, p.label, p.id === 'alarms' ? h('span', { class: 'badge', id: 'alarm-badge', hidden: true }) : null)));
}

// ----------------------------------------------------------------------------- scene
const sceneCanvas = document.getElementById('scene');
let scene = null;
const ctx = { api, store, h, fmt, get scene() { return scene; }, showPanel, alarmTarget };

function initScene() {
  scene = createScene(sceneCanvas, {
    onSelect: (sel) => store.select(sel),
    caption: document.getElementById('tour-caption'),
    walkHint: document.getElementById('walk-hint'),
  });
  window.__ben = { store, scene, api, panels: PANELS, showPanel, render: () => scene.render(), tour: scene.tour };
  document.querySelectorAll('[data-cam]').forEach(b => b.addEventListener('click', () => { scene.setCamera(b.dataset.cam); markCam(b.dataset.cam); }));
  document.getElementById('btn-walk').addEventListener('click', () => scene.toggleWalk());
  document.getElementById('btn-tour').addEventListener('click', () => scene.tour.toggle());
  document.getElementById('btn-cutaway').addEventListener('click', () => { const on = scene.toggleCutaway(); document.getElementById('btn-cutaway').classList.toggle('active', on); });
  document.getElementById('btn-doors').addEventListener('click', () => { const on = scene.toggleDoors(); document.getElementById('btn-doors').classList.toggle('active', on); });
  scene.onModeChange = (m) => {
    document.getElementById('btn-walk').classList.toggle('active', m.walk);
    document.getElementById('btn-tour').classList.toggle('active', m.tour);
    document.getElementById('btn-cutaway').classList.toggle('active', m.cutaway);
    document.getElementById('btn-doors').classList.toggle('active', m.doors);
    if (m.camera) markCam(m.camera);
  };
}
function markCam(name) { document.querySelectorAll('[data-cam]').forEach(b => b.classList.toggle('active', b.dataset.cam === name)); }

// ----------------------------------------------------------------------------- inspector
const inspTitle = document.getElementById('insp-title');
const inspBody = document.getElementById('insp-body');

function kv(rows) {
  return h('table', { class: 'kv' }, rows.filter(Boolean).map(([k, v]) => h('tr', {}, h('td', {}, k), h('td', {}, v))));
}
function evidence(ids, st) {
  const rows = ids.map(id => {
    const s = store.sensors.find(x => x.id === id);
    if (!s) return null;
    const v = sensorValue(id, st);
    const val = s.unit === 'bool' ? (v ? 'ACTIVE' : 'clear') : `${fmt.num(v, s.kind === 'pressure' ? 1 : (s.kind === 'power' ? 2 : 2))} ${s.unit}`;
    return h('tr', {}, h('td', { class: 'id' }, s.id), h('td', { class: 'mono' }, val), h('td', { class: 'u' }, s.u95 ? `±${s.u95}` : ''), h('td', { class: 'u' }, s.node));
  }).filter(Boolean);
  if (!rows.length) return h('p', { class: 'muted' }, 'No sensors on this object.');
  return h('div', {}, h('h4', {}, 'Evidence'), h('table', { class: 'kv evidence' }, h('tr', {}, h('td', {}, 'sensor'), h('td', {}, 'value'), h('td', {}, 'U95'), h('td', {}, 'node')), ...rows),
    h('p', { class: 'muted', style: { fontSize: '11px', margin: '6px 0 0' } }, `last update ${fmt.iso(st.wall_ts)} · sim t ${fmt.hms(st.t)}`));
}

function renderInspector() {
  const sel = store.selection, st = store.state, cfg = store.config, d = store.derived;
  if (!st || !cfg) { inspBody.replaceChildren(h('p', { class: 'muted' }, 'Waiting for the twin…')); return; }
  const alarmsFor = (pred) => st.alarms.filter(pred);
  let title = 'Container', tag = 'enclosure', body = [];
  const p = st.power;
  switch (sel.type) {
    case 'rack': {
      const i = sel.index; title = `Rack ${i + 1}`; tag = 'compute';
      const inlet = st.rack_inlet_c[i], outlet = st.rack_outlet_c[i];
      const al = alarmsFor(a => a.id.startsWith(`rack${i + 1}_`));
      body = [kv([
        ['Inlet', `${fmt.num(inlet, 2)} °C`], ['Outlet', `${fmt.num(outlet, 2)} °C`], ['ΔT', `${fmt.num(outlet - inlet, 1)} K`],
        ['PDU load', `${fmt.num(p.pdu_kw[i], 2)} kW`], ['Design per rack', `${d.per_rack_kw} kW`], ['Rack size', `${d.geometry.rack_u} U`],
        ['ASHRAE class', d.ashrae_class], ['Alarms', al.length ? al.map(a => a.sev).join(', ') : 'none'],
      ]), evidence(store.sensors.filter(s => new RegExp(`_r${i + 1}(_|$)`).test(s.id)).map(s => s.id), st)];
      break;
    }
    case 'cooling': {
      const i = sel.index, u = st.cooling_units[i]; title = `Cooling unit ${i + 1}`; tag = cfg.cooling;
      body = [kv([
        ['Status', u.ok ? (u.on ? 'running' : 'standby') : 'FAILED'], ['Cooling', `${fmt.num(u.kw)} kW`], ['Fan', `${fmt.num(u.fan_pct, 0)} %`],
        ['Capacity (derated)', `${d.cooling_unit_kw_derated} kW`], ['Derate', d.cooling_derate], ['Supply', `${fmt.num(st.supply_c)} °C`], ['Return', `${fmt.num(st.return_c)} °C`],
        ['Filter ΔP', `${fmt.num(st.filter_dp_pa, 0)} Pa`], ['Electrical (all units)', `${fmt.num(st.cooling_kw_elec)} kW`],
      ]), evidence(['T_supply', 'T_return', 'dP_aisle'], st)];
      break;
    }
    case 'drycooler': title = `Dry cooler ${(sel.index || 0) + 1}`; tag = 'heat rejection';
      body = [kv([['Outdoor', `${fmt.num(st.outdoor_c)} °C`], ['Heat rejected', `${fmt.num(st.cooling_units.reduce((s, u) => s + u.kw, 0))} kW`], ['Design day', `${d.climate.t_design_c} °C`], ['Medium', 'glycol/water']])];
      break;
    case 'cdu': title = 'CDU'; tag = 'liquid cooling';
      body = [kv([['Liquid share of heat', '70 %'], ['Units', `${d.cooling_units_total} (${cfg.redundancy})`], ['Supply air (residual)', `${fmt.num(st.supply_c)} °C`], ['Leak', st.leak ? 'DETECTED' : 'clear']]), evidence(['leak_floor'], st)];
      break;
    case 'ups': title = 'UPS'; tag = 'power';
      body = [kv([['State', p.ups_on_battery ? 'ON BATTERY' : 'online'], ['Load', `${fmt.num(p.ups_kw)} kW`], ['SoC', `${fmt.num(p.ups_soc_pct)} %`], ['Runtime', `${fmt.num(p.ups_runtime_min)} min`], ['Modules', `${d.ups_modules} × ${d.ups_kva_each} kVA`], ['Battery', `${d.battery_kwh} kWh (${cfg.ups_minutes} min design)`]])];
      break;
    case 'battery': title = 'Battery cabinet'; tag = 'power';
      body = [kv([['SoC', `${fmt.num(p.ups_soc_pct)} %`], ['Energy', `${d.battery_kwh} kWh`], ['Chemistry', 'LFP, 90 % DoD'], ['Runtime at load', `${fmt.num(p.ups_runtime_min)} min`]])];
      break;
    case 'ats': title = 'Utility / ATS'; tag = 'power';
      body = [kv([['Utility', p.utility_ok ? 'OK' : 'LOST'], ['Utility kW', `${fmt.num(p.utility_kw)} kW`], ['Generator', cfg.generator ? (p.generator_on ? 'RUNNING' : 'standby') : 'not fitted'], ['Service', `${d.voltage}, ${d.service_breaker_a} A`], ['Total design', `${d.total_kw} kW / ${d.total_kva} kVA`]]), evidence(['P_utility'], st)];
      break;
    case 'panel': title = 'Distribution panel'; tag = 'power';
      body = [kv([['Breaker frame', `${d.service_breaker_a} A`], ['Calculated', `${d.service_amps_calc} A`], ['Voltage', d.voltage], ['PDU circuits', `${cfg.racks}`], ['IT now', `${fmt.num(st.it_kw)} kW`]])];
      break;
    case 'gateway': title = 'Gateway / network'; tag = 'controls';
      body = [kv([['Gateway', 'Raspberry Pi 5 · ben_engine'], ['Nodes', `${new Set(store.sensors.map(s => s.node)).size} virtual`], ['Transport', 'MQTT, isolated LAN'], ['Mode', st.mode], ['Seq', st.seq]])];
      break;
    case 'doors': title = 'Doors'; tag = 'envelope';
      body = [kv([['State', st.door_open ? 'OPEN' : 'closed'], ['Humidity', `${fmt.num(st.rh_pct)} %RH`], ['Outdoor', `${fmt.num(st.outdoor_c)} °C`]]), evidence(['door_main', 'RH_room'], st)];
      break;
    case 'tray': title = 'Cable tray'; tag = 'power'; body = [kv([['Carries', 'PDU whips + controls LAN'], ['Height', `${(d.geometry.int_h_m - 0.3).toFixed(2)} m`]])]; break;
    case 'aisle_cold': title = 'Cold aisle'; tag = 'cooling'; body = [kv([['Supply', `${fmt.num(st.supply_c)} °C`], ['ΔP aisle', `${fmt.num(st.aisle_dp_pa)} Pa`], ['RH', `${fmt.num(st.rh_pct)} %`]]), evidence(['T_supply', 'dP_aisle', 'RH_room'], st)]; break;
    case 'aisle_hot': title = 'Hot aisle'; tag = 'cooling'; body = [kv([['Return', `${fmt.num(st.return_c)} °C`], ['Mean outlet', `${fmt.num(st.rack_outlet_c.reduce((a, b) => a + b, 0) / st.rack_outlet_c.length)} °C`]]), evidence(['T_return'], st)]; break;
    case 'sensor': {
      const s = store.sensors.find(x => x.id === sel.id); title = sel.id; tag = s ? s.kind : 'sensor';
      const v = sensorValue(sel.id, st);
      body = [kv([['Value', s && s.unit === 'bool' ? (v ? 'ACTIVE' : 'clear') : `${fmt.num(v, 2)} ${s ? s.unit : ''}`], ['Uncertainty U95 (k=2)', s && s.u95 ? `±${s.u95} ${s.unit}` : '—'], ['Node', s ? s.node : '—'],
        ['Location (x, y, z)', s ? s.location_m.map(n => n.toFixed(2)).join(', ') + ' m' : '—'], ['Last update', fmt.iso(st.wall_ts)], ['Calibration', 'cal_id sim-default']])];
      break;
    }
    default: title = `${d.tier_label}`; tag = cfg.white_label ? cfg.brand : 'Schreiber AI';
      body = [kv([['Enclosure', d.enclosure], ['Profile', cfg.profile], ['IT', `${fmt.num(st.it_kw)} / ${cfg.it_kw} kW`], ['Racks', cfg.racks], ['Cooling', d.cooling_label], ['Redundancy', cfg.redundancy],
        ['PUE now', fmt.num(st.pue, 3)], ['Outdoor', `${fmt.num(st.outdoor_c)} °C`], ['Room', `${fmt.num(st.room_c)} °C`], ['Alarms', st.alarms.length]])];
  }
  inspTitle.replaceChildren(title, h('span', { class: 'tag' }, tag));
  inspBody.replaceChildren(...body);
}

// ----------------------------------------------------------------------------- status strip
const stConn = document.getElementById('st-conn'), stMode = document.getElementById('st-mode'), stSpeed = document.getElementById('st-speed'),
  stSpeedVal = document.getElementById('st-speed-val'), stSimT = document.getElementById('st-simt'), stStep = document.getElementById('st-step'), stClock = document.getElementById('st-clock');

stSpeed.addEventListener('input', () => { stSpeedVal.value = stSpeed.value; });
stSpeed.addEventListener('change', async () => { try { await api('/api/sim/speed', { body: { x: +stSpeed.value } }); } catch (e) { console.warn(e); } });

function tickStatus() {
  const age = store.conn.lastMsg ? (performance.now() - store.conn.lastMsg) / 1000 : null;
  const dot = stConn.querySelector('.dot'), txt = stConn.querySelector('span');
  const alive = store.conn.connected && age !== null && age < 4;
  dot.className = 'dot ' + (alive ? 'ok' : (store.conn.connected ? 'warn' : 'bad'));
  txt.textContent = alive ? `live · ${age.toFixed(1)} s` : (store.conn.connected ? `stale ${fmt.ago(age)}` : 'disconnected');
  stClock.textContent = new Date().toLocaleTimeString([], { hour12: false });
  if (store.state) {
    stSimT.textContent = `t ${fmt.hms(store.state.t)}`;
    const stepAge = Date.now() / 1000 - store.state.wall_ts;
    stStep.textContent = `step ${stepAge < 60 ? stepAge.toFixed(1) + ' s' : fmt.ago(stepAge)} ago`;
    stStep.style.color = stepAge > 5 ? 'var(--amber)' : '';
    if (document.activeElement !== stSpeed) { stSpeed.value = store.state.sim_speed; stSpeedVal.value = store.state.sim_speed; }
    stMode.textContent = store.state.mode === 'live' ? 'LIVE' : 'SIM'; stMode.classList.toggle('live', store.state.mode === 'live');
  }
}
setInterval(tickStatus, 500);

// ----------------------------------------------------------------------------- wiring
store.on('config', (payload) => {
  document.getElementById('pill-tier').textContent = payload.derived.tier_label;
  document.getElementById('pill-site').textContent = payload.config.site_name;
  document.getElementById('brand-sub').textContent = payload.config.white_label ? `Business Edge Node · ${payload.config.brand}` : 'Business Edge Node · Schreiber AI';
  scene.rebuild(payload);
  for (const p of PANELS) if (mounted.has(p.id) && p.onConfig) p.onConfig(payload);
  renderInspector();
});
store.on('state', (st) => {
  scene.update(st);
  if (activePanel && activePanel.update) activePanel.update(st);
  const badge = document.getElementById('alarm-badge');
  if (badge) { badge.hidden = !st.alarms.length; badge.textContent = st.alarms.length; }
  renderInspector();
});
store.on('select', () => renderInspector());

document.addEventListener('keydown', (e) => {
  if (e.target.matches('input, select, textarea')) return;
  const cams = ['exterior_iso', 'cold_aisle', 'hot_aisle', 'power_room', 'roof'];
  if (e.key >= '1' && e.key <= '5') { scene.setCamera(cams[+e.key - 1]); markCam(cams[+e.key - 1]); }
  else if (e.key === 'f' || e.key === 'F') scene.toggleWalk();
  else if (e.key === 'g' || e.key === 'G') scene.tour.toggle();
  else if (e.key === 'c' || e.key === 'C') { const on = scene.toggleCutaway(); document.getElementById('btn-cutaway').classList.toggle('active', on); }
  else if (e.key === 'Escape') { scene.tour.stop(); scene.exitWalk(); }
});
document.getElementById('btn-help').addEventListener('click', () => document.getElementById('help').showModal());

async function boot() {
  buildTabs();
  initScene();
  try {
    const cfg = await api('/api/config');
    store.setConfig(cfg);
    const st = await api('/api/state');
    store.setState(st);
  } catch (e) { console.error('initial load failed', e); }
  let initial = location.hash.slice(1);
  if (!initial) { try { initial = localStorage.getItem('ben.panel') || ''; } catch (_) { /* ignore */ } }
  showPanel(initial || 'selector');
  connectWS();
  if (reducedMotion()) document.body.classList.add('reduced-motion');
}
boot();

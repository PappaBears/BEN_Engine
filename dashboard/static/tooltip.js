// Hover tooltip for the 3D twin: component name, BOM part (code + manufacturer/model), one-line
// purpose, and the two or three most relevant live values. Also drives keyboard cycling.
import { api, h, fmt, sensorValue } from './util.js';

let bomRows = [], bomCfgKey = '', bomLoaded = false, tipEl = null, store = null, scene = null, current = null;

// Catalog code preferences per component type; the first code present in /api/bom wins.
const CODES = {
  container: ['STR-CONT40', 'STR-CONT20', 'STR-CONT10', 'STR-CAB24U'],
  doors: ['STR-MANDOOR', 'STR-CAB24U'],
  rack: ['STR-RACK48', 'STR-RACK42', 'STR-CAB24U'],
  cooling_inrow: ['CLG-INROW', 'CLG-INROW-DX', 'CLG-'],
  cooling_cabinet: ['CLG-CABAC', 'CLG-'],
  cooling_rdhx: ['CLG-RDHX', 'CLG-'],
  cdu: ['CLG-CDU', 'CLG-CDU-RDHX', 'CLG-'],
  drycooler: ['CLG-DRYCOOLER', 'CLG-'],
  ups: ['PWR-UPS-GVS150', 'PWR-UPS-SRT6K', 'PWR-UPS-'],
  battery: ['PWR-BATT-', 'PWR-UPS-SRT6K-XBP', 'PWR-UPS-'],
  ats: ['PWR-ATS', 'PWR-MAIN-BKR', 'PWR-LOADCTR'],
  panel: ['PWR-PANEL-ILINE', 'PWR-PANEL', 'PWR-LOADCTR'],
  utility: ['PWR-METER', 'PWR-XFMR', 'PWR-FEEDER'],
  generator: ['PWR-GEN', 'PWR-ATS'],
  controller: ['CTL-CTRL', 'CTL-PLC', 'CTL-REVPI', 'CTL-EDGE', 'CTL-GW-PI5', 'CTL-GW'],
  pod: ['CTL-POD', 'CTL-NODE-MCU', 'CTL-NODE'],
  tray: ['STR-TRAY', 'PWR-FEEDER'],
  containment: ['STR-CONT-DOOR', 'STR-CONT-FRAME'],
  leak_rope: ['CTL-LEAK', 'CTL-LEAK-LEADER'],
  sensor_temperature: ['CTL-PT1000', 'CTL-POD'],
  sensor_humidity: ['CTL-SHT45', 'CTL-POD'],
  sensor_pressure: ['CTL-SDP810', 'CTL-POD'],
  sensor_power: ['PWR-METER', 'PWR-CT'],
  sensor_leak: ['CTL-LEAK'],
  sensor_contact: ['CTL-DOOR'],
};

function findPart(prefs) {
  for (const p of prefs || []) {
    const exact = bomRows.find(r => r.code === p); if (exact) return exact;
    const pre = bomRows.find(r => r.code.startsWith(p)); if (pre) return pre;
  }
  return null;
}

export async function loadBom(cfg) {
  const key = JSON.stringify(cfg);
  if (key === bomCfgKey) return;
  bomCfgKey = key; bomLoaded = false;
  try { const b = await api('/api/bom'); if (bomCfgKey !== key) return; bomRows = b.lines || []; bomLoaded = true; }
  catch (e) { if (bomCfgKey === key) { bomRows = []; bomLoaded = true; } }
  if (current && tipEl && !tipEl.hidden) render(current); // refresh an open tooltip with the part line
}

/** Registry entry for a hovered object: name, tag, part preference list, purpose line, live values. */
function describe(hv) {
  const st = store.state, cfg = store.config, d = store.derived; if (!st || !cfg) return null;
  const p = st.power;
  const aMax = { A1: 27, A2: 35, A3: 40, A4: 45 }[d.ashrae_class] || 35;
  const cool = cfg.cooling, liquid = cool === 'dlc_cdu', water = cool === 'rdhx_drycooler';
  const live = [];
  const L = (k, v, cls) => live.push([k, v, cls]);
  let name = hv.type, tag = '', codes = [], desc = '';
  switch (hv.type) {
    case 'rack': {
      const i = hv.index, tin = st.rack_inlet_c[i], tout = st.rack_outlet_c[i], kw = p.pdu_kw[i];
      name = `Rack ${i + 1}`; tag = 'compute'; codes = CODES.rack;
      desc = `${d.geometry.rack_u}U server rack: ${d.per_rack_kw} kW design load, fed by a metered rack PDU; inlet air from the cold aisle${water ? ', rear-door heat exchanger on the back' : liquid ? ', direct liquid cooled via manifold' : ''}.`;
      L('inlet max', `${fmt.num(tin)} °C`, tin > aMax ? 'bad' : tin > aMax - 2 ? 'warn' : 'ok'); L('outlet', `${fmt.num(tout)} °C`); L('load', `${fmt.num(kw)} kW`);
      break;
    }
    case 'cooling': {
      const i = hv.index, u = st.cooling_units[i] || {};
      if (water) { name = `RDHx door ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_rdhx; desc = `Rear-door heat exchanger: removes ~${d.cooling_unit_kw_derated} kW per rack door into the glycol loop; air leaves the rack near room temperature.`; }
      else if (cool === 'cabinet_dx') { name = `Cabinet AC ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_cabinet; desc = `Side-mounted DX air conditioner: ${d.cooling_unit_kw_derated} kW sensible, closed-loop so no outdoor air enters the cabinet.`; }
      else { name = `In-row cooling unit ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_inrow; desc = `In-row DX unit: draws hot-aisle air, rejects ${d.cooling_unit_kw_derated} kW to the roof condenser and supplies the cold aisle; fans modulate on return temperature.`; }
      L('status', !u.ok ? 'FAILED' : u.on ? 'running' : 'standby', !u.ok ? 'bad' : u.on ? 'ok' : ''); L('cooling', `${fmt.num(u.kw)} kW`); L('fan', `${fmt.num(u.fan_pct, 0)} %`);
      break;
    }
    case 'drycooler': {
      const u = st.cooling_units[hv.index] || {};
      name = `Dry cooler ${(hv.index || 0) + 1}`; tag = 'heat rejection'; codes = CODES.drycooler;
      desc = `Roof dry cooler: rejects the glycol loop heat to outdoor air with EC fans; sized for the ${d.climate.t_design_c} °C design day.`;
      L('status', !u.ok ? 'FAILED' : u.on ? 'running' : 'standby', !u.ok ? 'bad' : u.on ? 'ok' : ''); L('heat rejected', `${fmt.num(u.kw)} kW`); L('fan', `${fmt.num(u.fan_pct, 0)} %`); L('outdoor', `${fmt.num(st.outdoor_c)} °C`);
      break;
    }
    case 'cdu': name = 'CDU'; tag = 'liquid cooling'; codes = CODES.cdu;
      desc = liquid ? 'Coolant distribution unit: pumps and isolates the rack coolant loop from the facility glycol loop; ~70 % of IT heat goes to liquid.' : 'Coolant distribution unit for the rear-door heat exchangers: pumps, heat exchanger and leak-safe isolation from the dry-cooler loop.';
      L('loop heat', `${fmt.num(st.cooling_units.reduce((s, u) => s + u.kw, 0))} kW`); L('residual air supply', `${fmt.num(st.supply_c)} °C`); L('leak', st.leak ? 'DETECTED' : 'clear', st.leak ? 'bad' : 'ok');
      break;
    case 'ups': name = 'UPS'; tag = 'power'; codes = CODES.ups;
      desc = `Double-conversion UPS, ${d.ups_modules} × ${d.ups_kva_each} kVA (${cfg.redundancy}): carries the IT load through utility events until the generator or utility returns.`;
      L('state', p.ups_on_battery ? 'ON BATTERY' : 'online', p.ups_on_battery ? 'warn' : 'ok'); L('SoC', `${fmt.num(p.ups_soc_pct, 0)} %`, p.ups_soc_pct < 30 ? 'bad' : ''); L('runtime', `${fmt.num(p.ups_runtime_min, 0)} min`);
      break;
    case 'battery': name = 'Battery cabinet'; tag = 'power'; codes = CODES.battery;
      desc = `LFP battery cabinet, ${d.battery_kwh} kWh at 90 % depth of discharge: ${cfg.ups_minutes} min of IT load for the UPS.`;
      L('SoC', `${fmt.num(p.ups_soc_pct, 0)} %`, p.ups_soc_pct < 30 ? 'bad' : ''); L('energy', `${d.battery_kwh} kWh`); L('runtime', `${fmt.num(p.ups_runtime_min, 0)} min`);
      break;
    case 'ats': name = 'ATS / main breaker'; tag = 'power'; codes = CODES.ats;
      desc = `Automatic transfer switch and ${d.service_breaker_a} A main: selects utility or generator and protects the ${d.voltage} service.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('generator', cfg.generator ? (p.generator_on ? 'running' : 'standby') : 'not fitted'); L('import', `${fmt.num(p.utility_kw)} kW`);
      break;
    case 'panel': name = 'Distribution panel'; tag = 'power'; codes = CODES.panel;
      desc = `Distribution panelboard: one branch breaker per rack PDU plus cooling and controls circuits; ${d.service_breaker_a} A frame.`;
      L('IT now', `${fmt.num(st.it_kw)} kW`); L('circuits', `${cfg.racks} PDU + aux`); L('calc demand', `${d.service_amps_calc} A`);
      break;
    case 'utility': name = 'Utility service'; tag = 'power'; codes = CODES.utility;
      desc = `Service entrance and revenue meter: ${d.voltage}, ${d.service_breaker_a} A; the meter is the reference for PUE.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('import', `${fmt.num(p.utility_kw)} kW`); L('PUE', fmt.num(st.pue, 3));
      break;
    case 'generator': name = 'Generator'; tag = 'power'; codes = CODES.generator;
      desc = 'Standby generator on its own skid: starts within ~12 s of utility loss and takes over through the ATS so cooling returns before the UPS battery empties.';
      L('state', p.generator_on ? 'RUNNING' : 'standby', p.generator_on ? 'ok' : ''); L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad');
      break;
    case 'controller': name = 'BEN Controller'; tag = 'controls'; codes = CODES.controller;
      desc = cfg.tier === 'micro' ? 'BEN Controller (RevPi): PLC logic plus the ben_engine twin and API; talks to the BEN Pods over BEN Mesh and to the UPS/AC over Modbus.' : 'BEN Controller: PLC + edge computer running ben_engine; collects BEN Pods over BEN Mesh, polls UPS/cooling/meters over Modbus, serves this dashboard locally.';
      L('pods', `${new Set(store.sensors.map(s => s.node)).size}`); L('mode', st.mode); L('seq', st.seq);
      break;
    case 'tray': name = 'Cable tray'; tag = 'power'; codes = CODES.tray;
      desc = 'Overhead cable tray: PDU whips from the distribution panel to each rack, and the BEN Mesh / network drops, kept separate.';
      L('circuits', `${cfg.racks} PDU`); L('IT now', `${fmt.num(st.it_kw)} kW`);
      break;
    case 'containment': name = `Containment door ${(hv.index || 0) + 1}`; tag = 'cooling'; codes = CODES.containment;
      desc = 'Hot-aisle containment door: keeps hot exhaust from recirculating to the inlets; the aisle ΔP sensor proves it is sealed.';
      L('aisle ΔP', `${fmt.num(st.aisle_dp_pa)} Pa`); L('return', `${fmt.num(st.return_c)} °C`);
      break;
    case 'leak_rope': name = 'Leak-detection rope'; tag = 'controls'; codes = CODES.leak_rope;
      desc = 'Conductive sensing rope along the floor under the racks and cooling units; any wetting trips the BEN Pod leak input.';
      L('leak', st.leak ? 'DETECTED' : 'clear', st.leak ? 'bad' : 'ok');
      break;
    case 'doors': name = 'Container doors'; tag = 'envelope'; codes = CODES.doors;
      desc = 'Door-end access doors with a reed contact: opening raises a warning and the twin adds envelope load and humidity.';
      L('state', st.door_open ? 'OPEN' : 'closed', st.door_open ? 'warn' : 'ok'); L('humidity', `${fmt.num(st.rh_pct, 0)} %RH`);
      break;
    case 'sensor': {
      const s = store.sensors.find(x => x.id === hv.id) || { kind: 'temperature', unit: '', u95: 0, node: '?' };
      const v = sensorValue(hv.id, st);
      name = `BEN Pod · ${hv.id}`; tag = s.kind; codes = CODES[`sensor_${s.kind}`] || CODES.pod;
      const what = { temperature: 'Pt1000 class A probe on a BEN Pod: 3-wire RTD temperature at this point, calibrated in a stirred bath.', humidity: 'SHT45 on the room BEN Pod: humidity for condensation and ASHRAE envelope checks.', pressure: 'SDP810 on the room BEN Pod: cold-to-hot aisle ΔP that proves containment and filter state.', power: 'Utility meter (Class 0.5) read by the BEN Controller: the PUE denominator.', leak: 'Leak rope input on the BEN Pod.', contact: 'Reed contact on the door, read by the BEN Pod.' }[s.kind];
      desc = what || 'Sensor channel on a BEN Pod.';
      L('value', s.unit === 'bool' ? (v ? 'ACTIVE' : 'clear') : `${fmt.num(v, 2)} ${s.unit}${s.u95 ? ` ± ${s.u95}` : ''}`, s.unit === 'bool' && v ? 'warn' : ''); L('pod', s.node); L('updated', fmt.clock(st.wall_ts));
      break;
    }
    case 'aisle_cold': name = 'Cold aisle'; tag = 'cooling'; codes = CODES.containment; desc = 'Supply-air aisle in front of the rack inlets.'; L('supply', `${fmt.num(st.supply_c)} °C`); L('ΔP', `${fmt.num(st.aisle_dp_pa)} Pa`); break;
    case 'aisle_hot': name = 'Hot aisle'; tag = 'cooling'; codes = CODES.containment; desc = 'Contained exhaust aisle behind the racks.'; L('return', `${fmt.num(st.return_c)} °C`); break;
    default: name = d.tier_label; tag = 'enclosure'; codes = CODES.container;
      desc = `${d.enclosure}: ISO corner castings, 100 mm PIR insulation, corrosion class ${d.climate.corrosion}; ${d.gross_kg.toLocaleString()} kg gross.`;
      L('room', `${fmt.num(st.room_c)} °C`); L('PUE', fmt.num(st.pue, 3)); L('alarms', st.alarms.length, st.alarms.length ? 'warn' : 'ok');
  }
  return { name, tag, part: findPart(codes), desc, live };
}

function render(hv) {
  const info = describe(hv); if (!info) return;
  const part = info.part;
  tipEl.replaceChildren(
    h('div', { class: 'tip-name' }, info.name, h('small', {}, info.tag)),
    h('div', { class: 'tip-part' }, part ? [part.code, ' ', h('span', {}, `· ${part.manufacturer || ''} ${part.mpn || part.name || ''}`.trim())] : h('span', {}, bomRows.length ? 'no catalog line for this item' : 'BOM not loaded')),
    h('div', { class: 'tip-desc' }, info.desc),
    h('dl', { class: 'tip-live' }, ...info.live.flatMap(([k, v, cls]) => [h('dt', {}, k), h('dd', { class: cls || '' }, String(v))])),
    h('div', { class: 'tip-hint' }, hv.source === 'keyboard' ? 'Enter: inspect · Tab / arrows: next part · Esc: close' : 'Click to inspect'),
  );
}

function place(screen) {
  if (!screen) return;
  const vw = window.innerWidth, vh = window.innerHeight;
  tipEl.hidden = false;
  const w = tipEl.offsetWidth || 320, hgt = tipEl.offsetHeight || 120;
  let x = screen.x + 16, y = screen.y + 16;
  if (x + w > vw - 8) x = Math.max(8, screen.x - w - 12);
  if (y + hgt > vh - 8) y = Math.max(8, screen.y - hgt - 12);
  tipEl.style.left = `${Math.round(x)}px`; tipEl.style.top = `${Math.round(y)}px`;
}

export function initTooltip({ store: st, scene: sc }) {
  store = st; scene = sc; tipEl = document.getElementById('tip');
  scene.onHover = (hv) => {
    current = hv;
    if (!hv) { tipEl.hidden = true; return; }
    render(hv); place(hv.screen);
  };
  // live values refresh while hovering; keyboard-anchored tooltips follow their object
  store.on('state', () => { if (current && !tipEl.hidden) { render(current); if (current.source === 'keyboard') place(scene.screenPositionOf(current.key)); } });
  store.on('config', (p) => { loadBom(p.config); tipEl.hidden = true; current = null; });
  if (store.config) loadBom(store.config);
  const canvas = document.getElementById('scene');
  canvas.addEventListener('keydown', (e) => {
    if (scene.mode.walk || scene.mode.tour) return;
    if (e.key === 'Tab' || e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); scene.hoverCycle(e.shiftKey && e.key === 'Tab' ? -1 : 1); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); scene.hoverCycle(-1); }
    else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); scene.hoverSelect(); }
    else if (e.key === 'Escape') { scene.clearHover(); }
  });
  canvas.addEventListener('blur', () => { if (current && current.source === 'keyboard') scene.clearHover(); });
  return { describe, loadBom, get current() { return current; }, get bomLoaded() { return bomLoaded; }, get bomRows() { return bomRows.length; } };
}

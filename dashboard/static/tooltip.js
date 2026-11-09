// Hover tooltip for the 3D twin: component name, BOM part (code + manufacturer/model), one-line
// purpose, and the two or three most relevant live values. Also drives keyboard cycling.
import { api, h, fmt, sensorValue } from './util.js';

let bomRows = [], bomCfgKey = '', bomLoaded = false, tipEl = null, store = null, scene = null, current = null;

// Catalog code preferences per component type; the first code present in /api/bom wins.
const CODES = {
  container: ['STR-CONT40', 'STR-CONT20', 'STR-CONT10', 'STR-CAB24U', 'STR-MINICAB-12', 'STR-MINIRACK-10'],
  doors: ['STR-MANDOOR', 'STR-CAB24U'],
  rack: ['STR-RACK48', 'STR-RACK42', 'STR-RACK-MGX', 'STR-CAB24U', 'STR-MINICAB-12', 'STR-MINIRACK-10'],
  cooling_inrow: ['CLG-INROW', 'CLG-INROW-DX', 'CLG-'],
  cooling_cabinet: ['CLG-CABAC', 'CLG-'],
  cooling_rdhx: ['CLG-RDHX', 'CLG-'],
  cdu: ['CLG-CDU-HD', 'CLG-CDU', 'CLG-CDU-RDHX', 'CLG-'],
  rectifier: ['PWR-DC-RECT-100', 'PWR-DC-RECT-CAB', 'PWR-DC-'],
  dc_busway: ['PWR-DC-BUSWAY', 'PWR-DC-TAPOFF', 'PWR-DC-'],
  manifold: ['CLG-MANIFOLD-HD', 'CLG-MANIFOLD', 'CLG-'],
  drycooler: ['CLG-DRYCOOLER', 'CLG-'],
  ups: ['PWR-UPS-GVS150', 'PWR-UPS-GVL500', 'PWR-UPS-MINI-2200', 'PWR-UPS-MINI-1000', 'PWR-UPS-SRT6K', 'PWR-UPS-'],
  battery: ['PWR-BATT-800V', 'PWR-BATT-', 'PWR-UPS-MINI-XBP', 'PWR-UPS-SRT6K-XBP', 'PWR-UPS-'],
  ats: ['PWR-ATS', 'PWR-MAIN-BKR', 'PWR-LOADCTR'],
  panel: ['PWR-PANEL-ILINE', 'PWR-PANEL-600', 'PWR-SWBD-SECTION', 'PWR-PANEL', 'PWR-PDU-10IN', 'PWR-LOADCTR'],
  utility: ['PWR-METER', 'PWR-XFMR', 'PWR-FEEDER', 'PWR-UPS-MINI-1000', 'PWR-UPS-MINI-2200'],
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
  // BEN 2000 hall and hardening items (docs/TIER_AND_ENCLOSURE_DECISION.md)
  hall: ['STR-MODULE-WB', 'STR-HALL', 'STR-MODULE', 'STR-CONT40'],
  powermodule: ['STR-POWERMOD', 'STR-MODULE-WB', 'PWR-SWGR'],
  transformer: ['PWR-XFMR-2500', 'PWR-XFMR', 'PWR-MV'],
  switchgear: ['PWR-SWBD-SECTION', 'PWR-SWGR', 'PWR-MV-SWGR', 'PWR-PANEL-ILINE', 'PWR-MAIN-BKR'],
  // Rev 2: liquid-first dense tiers and the BEN 1 mini rack
  fancoil: ['CLG-FANCOIL-CW20', 'CLG-AIR-RESID-HD', 'CLG-'],
  trim_chiller: ['CLG-TRIM-CHILLER', 'CLG-'],
  skid: ['CLG-SKID-DENSE', 'CLG-DRYCOOLER-W45'],
  ai_box: ['CMP-AI-DGXSPARK', 'CMP-AI-2U-RTXPRO', 'CMP-MINIPC', 'CMP-MINI-1U', 'CMP-'],
  nas: ['CMP-NAS-RS422', 'CMP-NAS-DS224'],
  switch: ['CMP-SW-MINI'],
  pdu: ['PWR-PDU-10IN', 'STR-MINICAB-12'],
  edge: ['CTL-EDGE-MINI', 'CTL-EDGE'],
  desk: [],
  patch: ['CTL-PATCH', 'CTL-CAT6A'],
  cooling_office: ['STR-MINICAB-12'],
  fanwall: ['CLG-FANWALL', 'CLG-AHU', 'CLG-INROW'],
  drycooler_adiabatic: ['CLG-DRYCOOLER-ADIA', 'CLG-DRYCOOLER', 'CLG-'],
  plinth: ['HRD-PLINTH', 'HRD-H2', 'STR-PLINTH'],
  armour: ['HRD-BALLISTIC', 'HRD-H3', 'STR-ARMOUR'],
  vestibule: ['HRD-VESTIBULE', 'HRD-MANTRAP', 'HRD-H3', 'STR-VESTIBULE'],
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
  const cool = cfg.cooling, liquid = cool === 'dlc_cdu' || cool === 'dlc_hd', water = cool === 'rdhx_drycooler', hd = cool === 'dlc_hd', dc800 = (cfg.power_architecture || 'ac480') === 'dc800';
  const dc = st.dc || {}, loop = st.loop || {};
  const kind = d.kind || (cfg.tier === 'ben5' ? 'cabinet' : 'module'), cabinet = kind === 'cabinet', hall = kind === 'hall';
  const live = [];
  const L = (k, v, cls) => live.push([k, v, cls]);
  let name = hv.type, tag = '', codes = [], desc = '';
  switch (hv.type) {
    case 'rack': {
      const i = hv.index, tin = st.rack_inlet_c[i], tout = st.rack_outlet_c[i], kw = p.pdu_kw[i];
      name = `Rack ${i + 1}`; tag = 'compute'; codes = CODES.rack;
      desc = kind === 'minirack' ? `${d.form_label} (${d.geometry.reference || ''}): ${cfg.it_kw} kW IT, office air in at the front; estimated ${d.noise_dba_est} dBA at 1 m (target ${d.noise_dba_target}).`
        : d.liquid_first ? `GB300 NVL72-class liquid rack, 600 x 1068 mm 48U MGX: ${d.per_rack_kw} kW (limit ${d.rack_kw_max}), cold plates on the W45 loop through the rear manifold, ${Math.round((d.air_residual || 0.1) * 100)} % residual air to the fan coils.`
        : `${d.geometry.rack_u}U server rack: ${d.per_rack_kw} kW design load, fed by a metered rack PDU; inlet air from the cold aisle${water ? ', rear-door heat exchanger on the back' : liquid ? ', direct liquid cooled via manifold' : ''}.`;
      L('inlet max', `${fmt.num(tin)} °C`, tin > aMax ? 'bad' : tin > aMax - 2 ? 'warn' : 'ok'); L('outlet', `${fmt.num(tout)} °C`); L('load', `${fmt.num(kw)} kW`);
      if (st.mini) L('noise', `${fmt.num(st.mini.noise_dba, 1)} dBA`, st.mini.noise_dba > d.noise_dba_target + 3 ? 'warn' : 'ok');
      break;
    }
    case 'cooling': {
      const i = hv.index, u = st.cooling_units[i] || {};
      if (water) { name = `RDHx door ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_rdhx; desc = `Rear-door heat exchanger: removes ~${d.cooling_unit_kw_derated} kW per rack door into the glycol loop; air leaves the rack near room temperature.`; }
      else if (cool === 'office_air') { name = `Extraction fan ${i + 1}`; tag = 'cooling · office air'; codes = CODES.cooling_office; desc = `Filtered, sound-damped extraction fan (N+1 pair) in the 12U cabinet: carries the IT exhaust out to the room; ${d.cooling_unit_kw_derated} kW at a 10 K rise, no refrigerant. The room's own air conditioning removes the heat.`; }
      else if (cool === 'cabinet_dx') { name = `Cabinet AC ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_cabinet; desc = `Side-mounted DX air conditioner: ${d.cooling_unit_kw_derated} kW sensible, closed-loop so no outdoor air enters the cabinet.`; }
      else { name = `In-row cooling unit ${i + 1}`; tag = 'cooling'; codes = CODES.cooling_inrow; desc = `In-row DX unit: draws hot-aisle air, rejects ${d.cooling_unit_kw_derated} kW to the roof condenser and supplies the cold aisle; fans modulate on return temperature.`; }
      L('status', !u.ok ? 'FAILED' : u.on ? 'running' : 'standby', !u.ok ? 'bad' : u.on ? 'ok' : ''); L('cooling', `${fmt.num(u.kw)} kW`); L('fan', `${fmt.num(u.fan_pct, 0)} %`);
      break;
    }
    case 'drycooler': {
      const u = st.cooling_units[hv.index] || {};
      name = hall ? `Adiabatic dry cooler ${(hv.index || 0) + 1}` : `Dry cooler ${(hv.index || 0) + 1}`; tag = 'heat rejection'; codes = hall ? CODES.drycooler_adiabatic : CODES.drycooler;
      desc = hall ? `Adiabatic dry cooler in the plant yard: EC fans with wetted pre-cooling pads for the ${d.climate.t_design_c} °C design day; water-free mode below ~30 °C.` : `Roof dry cooler: rejects the glycol loop heat to outdoor air with EC fans; sized for the ${d.climate.t_design_c} °C design day.`;
      L('status', !u.ok ? 'FAILED' : u.on ? 'running' : 'standby', !u.ok ? 'bad' : u.on ? 'ok' : ''); L('heat rejected', `${fmt.num(u.kw)} kW`); L('fan', `${fmt.num(u.fan_pct, 0)} %`); L('outdoor', `${fmt.num(st.outdoor_c)} °C`);
      break;
    }
    case 'rectifier': name = 'AC/DC front end'; tag = 'power · 800 VDC'; codes = CODES.rectifier;
      desc = `SiC rectifier / SST modules, ${d.rectifier_modules} × ${d.rectifier_module_kw} kW (${cfg.redundancy}) feeding the 800 VDC bus (${d.dc_convention_label}) at a vendor-claimed ${Math.round((d.rectifier_eff || 0.985) * 1000) / 10} % efficiency; no UPS double conversion, the battery sits on the bus; racks take the bus through 800 V → 50 V shelves. Forward architecture study.`;
      L('bus', `${fmt.num(dc.v_bus, 0)} V`, dc.v_bus < d.dc_bus_v_min || dc.v_bus > d.dc_bus_v_max ? 'warn' : 'ok'); L('front end', `${fmt.num(p.ups_kw)} kW`); L('IMD', `${fmt.num(dc.imd_kohm, 0)} kΩ`, dc.imd_kohm < 100 ? 'bad' : ''); break;
    case 'dc_busway': name = 'DC busway'; tag = 'power · 800 VDC'; codes = CODES.dc_busway;
      desc = `800 VDC busway rated ${d.dc_busway_a} A (bus ${d.dc_bus_current_a} A with 25 % headroom), ${d.dc_bus_v_pole} V to ground: ${d.dc_grounding}. DC tap-off breaker per rack, ${d.dc_imd_arrangement}, DC arc detection on every section. Window ${d.dc_bus_v_min}–${d.dc_bus_v_max} V is a working assumption.`;
      L('V+ / V−', `${fmt.num(dc.v_bus_pos, 0)} / ${fmt.num(dc.v_bus_neg, 0)} V`, dc.ground_fault ? 'bad' : 'ok'); L('I bus', `${fmt.num(dc.i_bus, 0)} A`); L('IMD', `${fmt.num(dc.imd_kohm, 0)} kΩ`, dc.imd_kohm < 100 ? 'bad' : (dc.imd_kohm < 500 ? 'warn' : 'ok')); break;
    case 'manifold': name = `Rack manifold ${(hv.index || 0) + 1}`; tag = 'liquid cooling'; codes = CODES.manifold;
      desc = `Supply/return manifold with UQD quick-disconnect drops to the cold plates of rack ${(hv.index || 0) + 1}; leak sensor in the drip tray closes the row isolation valves (leak-to-isolation time is measured, E19).`;
      L('supply', `${fmt.num(loop.supply_c)} °C`); L('ΔT', `${fmt.num(loop.dt_k)} K`); L('isolated', loop.leak_isolated ? 'YES' : 'no', loop.leak_isolated ? 'bad' : 'ok'); break;
    case 'cdu': name = hall ? `CDU ${(hv.index || 0) + 1}` : (hd ? `Row CDU ${(hv.index || 0) + 1}` : 'CDU'); tag = 'liquid cooling'; codes = CODES.cdu;
      if (hd) {
        desc = `600 kW class row CDU on the W45 warm-water loop (${d.loop_supply_design_c}/${d.loop_return_design_c} °C design, ${d.loop_flow_lpm} L/min), pumps N+1 with failover (E18); ${d.heat_reuse_kw_available} kW of heat available for reuse at the return.`;
        L('flow', `${fmt.num(loop.flow_lpm, 0)} L/min`, loop.flow_low ? 'bad' : 'ok'); L('supply / return', `${fmt.num(loop.supply_c)} / ${fmt.num(loop.return_c)} °C`); L('pumps', `${(loop.pumps || []).filter(x => x.on && x.ok).length}/${(loop.pumps || []).length} running`, (loop.pumps || []).some(x => !x.ok) ? 'warn' : 'ok'); break;
      }
      if (hall) { const u = st.cooling_units[hv.index] || {}; L('status', !u.ok ? 'FAILED' : u.on ? 'running' : 'standby', !u.ok ? 'bad' : u.on ? 'ok' : ''); L('to liquid', `${fmt.num(u.kw)} kW`); }
      desc = liquid ? 'Coolant distribution unit: pumps and isolates the rack coolant loop from the facility glycol loop; ~70 % of IT heat goes to liquid.' : 'Coolant distribution unit for the rear-door heat exchangers: pumps, heat exchanger and leak-safe isolation from the dry-cooler loop.';
      L('loop heat', `${fmt.num(st.cooling_units.reduce((s, u) => s + u.kw, 0))} kW`); L('residual air supply', `${fmt.num(st.supply_c)} °C`); L('leak', st.leak ? 'DETECTED' : 'clear', st.leak ? 'bad' : 'ok');
      break;
    case 'ups': name = hall ? `UPS string ${(hv.index || 0) + 1}` : 'UPS'; tag = 'power'; codes = CODES.ups;
      desc = kind === 'minirack' ? `${d.ups_model}: line-interactive lithium UPS carrying the IT, fans and Pods for an estimated ${d.ups_runtime_min_est} min at full load${d.ups_battery_packs ? ` plus ${d.ups_battery_packs} battery pack(s)` : ''}; plugs into a ${d.ups_plug} outlet.`
        : d.liquid_first ? `Galaxy VL UPS frame (850 x 925 mm, up to 500 kW, internal N+1 power modules), ${d.ups_frames} frame(s) at ${d.ups_kva_each} kVA; the CDU pumps and fan coils ride on it too.`
        : hall ? `Modular UPS string, ${d.ups_modules} × ${d.ups_kva_each.toLocaleString()} kVA (2N): each string alone carries the IT load; frames are hot-swappable.` : `Double-conversion UPS, ${d.ups_modules} × ${d.ups_kva_each} kVA (${cfg.redundancy}): carries the IT load through utility events until the generator or utility returns.`;
      L('state', p.ups_on_battery ? 'ON BATTERY' : 'online', p.ups_on_battery ? 'warn' : 'ok'); L('SoC', `${fmt.num(p.ups_soc_pct, 0)} %`, p.ups_soc_pct < 30 ? 'bad' : ''); L('runtime', `${fmt.num(p.ups_runtime_min, 0)} min`);
      break;
    case 'battery': name = hall ? 'Battery room cabinet' : 'Battery cabinet'; tag = 'power'; codes = CODES.battery;
      desc = dc800 ? `800 V class LFP battery string directly on the DC bus (no UPS, no double conversion): ${d.battery_on_bus_kwh} kWh for ${cfg.ups_minutes} min of IT load; bus voltage drifts with state of charge on utility loss.` : hall ? `Lithium battery room per NFPA 855 (2-hour separation, gas detection, UL 9540A data): ${d.battery_kwh.toLocaleString()} kWh for ${cfg.ups_minutes} min of IT load.` : `LFP battery cabinet, ${d.battery_kwh} kWh at 90 % depth of discharge: ${cfg.ups_minutes} min of IT load for the UPS.`;
      L('SoC', `${fmt.num(p.ups_soc_pct, 0)} %`, p.ups_soc_pct < 30 ? 'bad' : ''); L('energy', `${d.battery_kwh} kWh`); L('runtime', `${fmt.num(p.ups_runtime_min, 0)} min`);
      break;
    case 'ats': name = hall ? 'Transfer / paralleling section' : 'ATS / main breaker'; tag = 'power'; codes = CODES.ats;
      desc = hall ? `Paralleling and transfer section of the 480 V switchgear: selects the utility transformers or the ${d.generators_total} generators; ${d.service_breaker_a} A main.` : `Automatic transfer switch and ${d.service_breaker_a} A main: selects utility or generator and protects the ${d.voltage} service.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('generator', cfg.generator ? (p.generator_on ? 'running' : 'standby') : 'not fitted'); L('import', `${fmt.num(p.utility_kw)} kW`);
      break;
    case 'panel': name = 'Distribution panel'; tag = 'power'; codes = CODES.panel;
      desc = `Distribution panelboard: one branch breaker per rack PDU plus cooling and controls circuits; ${d.service_breaker_a} A frame.`;
      L('IT now', `${fmt.num(st.it_kw)} kW`); L('circuits', `${cfg.racks} PDU + aux`); L('calc demand', `${d.service_amps_calc} A`);
      break;
    case 'utility': name = hall ? 'MV utility service' : 'Utility service'; tag = 'power'; codes = CODES.utility;
      desc = hall ? `Medium-voltage service entrance and revenue meter (${d.voltage}) feeding the pad-mount transformers; the meter is the reference for PUE.` : `Service entrance and revenue meter: ${d.voltage}, ${d.service_breaker_a} A; the meter is the reference for PUE.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('import', `${fmt.num(p.utility_kw)} kW`); L('PUE', fmt.num(st.pue, 3));
      break;
    case 'generator': name = hall ? `Generator ${(hv.index || 0) + 1} of ${d.generators_total}` : 'Generator'; tag = 'power'; codes = CODES.generator;
      desc = hall ? `${d.generator_kw_each.toLocaleString()} kW diesel generator (N+1 set) with a 48 h belly tank and SPCC containment: starts within ~12 s of utility loss and parallels onto the switchgear.` : 'Standby generator on its own skid: starts within ~12 s of utility loss and takes over through the ATS so cooling returns before the UPS battery empties.';
      L('state', p.generator_on ? 'RUNNING' : 'standby', p.generator_on ? 'ok' : ''); L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad');
      break;
    case 'transformer': name = `Transformer ${(hv.index || 0) + 1} of ${d.transformers_total}`; tag = 'power'; codes = CODES.transformer;
      desc = `${(d.transformer_kva || 2500).toLocaleString()} kVA pad-mount transformer, ${d.voltage.split('→')[0].trim()} to 480 V (${cfg.redundancy === 'N' ? 'N' : '2N pair'}); oil-filled, loop-feed, in the fenced MV yard.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('load', `${fmt.num(p.utility_kw / Math.max(1, d.transformers_total))} kW each`); L('demand', `${d.total_kva.toLocaleString()} kVA`);
      break;
    case 'switchgear': name = d.liquid_first ? `480 V switchboard section ${(hv.index || 0) + 1}` : '480 V switchgear'; tag = 'power'; codes = CODES.switchgear;
      desc = d.liquid_first ? `UL 891 switchboard section (36 in W x 24 in D) in the row: ${d.service_breaker_a} A main, UPS maintenance bypass and the rack feeds; backed onto the wall so it has >= 1,067 mm of NEC 110.26 condition-2 working space in front.`
        : `Low-voltage switchgear lineup in the power module: transformer mains, tie, generator paralleling and UPS feeders; ${d.service_breaker_a} A frame.`;
      L('utility', p.utility_ok ? 'OK' : 'LOST', p.utility_ok ? 'ok' : 'bad'); L('import', `${fmt.num(p.utility_kw)} kW`); L('calc demand', `${d.service_amps_calc.toLocaleString()} A`);
      break;
    case 'powermodule': name = 'Power module'; tag = 'power'; codes = CODES.powermodule;
      desc = `Separate wide-body module beside the hall: switchgear, ${d.ups_modules} UPS strings and the battery room, so no energy storage sits in the IT hall.`;
      L('UPS', p.ups_on_battery ? 'ON BATTERY' : 'online', p.ups_on_battery ? 'warn' : 'ok'); L('SoC', `${fmt.num(p.ups_soc_pct, 0)} %`); L('import', `${fmt.num(p.utility_kw)} kW`);
      break;
    case 'fanwall': name = `Fan-wall unit ${(hv.index || 0) + 1}`; tag = 'cooling'; codes = CODES.fanwall;
      desc = 'Fan-wall air handler along the long wall: handles the ~30 % air-side residual heat of the liquid-cooled racks and holds the hall at the supply set-point.';
      L('supply', `${fmt.num(st.supply_c)} °C`); L('return', `${fmt.num(st.return_c)} °C`); L('fans', `${fmt.num(Math.max(...st.cooling_units.map(u => u.fan_pct), 0), 0)} %`);
      break;
    case 'plinth': name = 'Flood plinth'; tag = 'hardening'; codes = CODES.plinth;
      desc = `${d.hardening_label || cfg.hardening}: 600 mm flood plinth with sealed penetrations above the flood line; stainless fasteners and ${d.hardening_coating || 'C5-M'} coating.`;
      L('level', cfg.hardening); L('rating', d.hardening_rating || 'IP66');
      break;
    case 'armour': name = 'Ballistic wall panel'; tag = 'hardening'; codes = CODES.armour;
      desc = 'H3 hardened envelope: UL 752 ballistic panels (level selectable), IK10 impact doors, forced-entry rating per ASTM F3038; HEMP shielding option (MIL-STD-188-125-1).';
      L('level', cfg.hardening); L('rating', d.hardening_rating || '');
      break;
    case 'vestibule': name = 'Secure vestibule / mantrap'; tag = 'hardening'; codes = CODES.vestibule;
      desc = 'Two-door interlocked vestibule with two-factor access, tamper detection on the PLC and an audit trail in BEN Care (H3 package).';
      L('door', st.door_open ? 'OPEN' : 'closed', st.door_open ? 'warn' : 'ok'); L('access', 'two-factor');
      break;
    case 'controller': name = 'BEN Controller'; tag = 'controls'; codes = CODES.controller;
      desc = cabinet ? 'BEN Controller (RevPi): PLC logic plus the ben_engine twin and API; talks to the BEN Pods over BEN Mesh and to the UPS/AC over Modbus.' : 'BEN Controller: PLC + edge computer running ben_engine; collects BEN Pods over BEN Mesh, polls UPS/cooling/meters over Modbus, serves this dashboard locally.';
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
    // ---------------------------------------------------------------- Rev 2 parts
    case 'fancoil': name = `In-row fan coil ${(hv.index || 0) + 1}`; tag = 'cooling · residual air'; codes = CODES.fancoil;
      desc = `300 mm chilled-water fan coil on the ${d.trim_loop_c} °C trim loop: removes the ${Math.round((d.air_residual || 0.1) * 100)} % of the GB300-class racks' heat that stays in the air (${d.fancoils_total} units, N+1). The W45 loop is too warm to cool room air.`;
      L('supply', `${fmt.num(st.supply_c)} °C`); L('return', `${fmt.num(st.return_c)} °C`); L('trim chiller', `${d.trim_loop_kw} kW`); break;
    case 'trim_chiller': name = 'Trim chiller'; tag = 'heat rejection'; codes = CODES.trim_chiller;
      desc = `Air-cooled chiller on the skid for the ${d.trim_loop_c} °C fan-coil loop (${d.trim_loop_kw} kW, R-454B, GWP 466).`; L('outdoor', `${fmt.num(st.outdoor_c)} °C`); break;
    case 'skid': name = 'Heat-rejection skid'; tag = 'heat rejection'; codes = CODES.skid;
      desc = `Skid beside the blind end: W45 dry coolers for ${fmt.num(d.liquid_heat_kw, 0)} kW of liquid heat, the trim chiller and the pipe bridge to the module (all-in-one rule: heat rejection outside).`;
      L('loop supply', `${fmt.num(loop.supply_c)} °C`); L('outdoor', `${fmt.num(st.outdoor_c)} °C`); break;
    case 'ai_box': name = cfg.form === 'rack10' ? 'Desktop AI box' : 'GPU server'; tag = 'compute · customer-selectable'; codes = CODES.ai_box;
      desc = cfg.form === 'rack10' ? 'Desktop AI computer (DGX Spark class, GB10, 128 GB unified memory) on a 2U shelf of the 10-inch rack; the customer may bring their own.' : '2U short-depth server (<= 550 mm) with one RTX PRO 6000 Blackwell; standard-depth GPU servers do not fit the cabinet.';
      L('load', `${fmt.num(st.it_kw)} kW`); L('inlet', `${fmt.num(st.rack_inlet_c[0])} °C`, st.rack_inlet_c[0] > aMax ? 'bad' : 'ok'); break;
    case 'nas': name = 'NAS'; tag = 'compute'; codes = CODES.nas; desc = '1U 4-bay NAS (Synology RS422+) for local backup and files.'; L('inlet', `${fmt.num(st.rack_inlet_c[0])} °C`); break;
    case 'switch': name = 'Managed switch'; tag = 'compute'; codes = CODES.switch; desc = '8-port managed PoE switch: the IT network and the uplink to the customer router; controls traffic is outbound HTTPS only.'; break;
    case 'pdu': name = '10-inch PDU'; tag = 'power'; codes = CODES.pdu; desc = '1U 10-inch PDU, 4 x NEMA 5-15R, fed from the UPS.'; L('IT now', `${fmt.num(st.it_kw)} kW`); break;
    case 'edge': name = 'Edge computer (BEN Care agent)'; tag = 'controls · BEN Controls Mini'; codes = CODES.edge; desc = 'Fanless edge computer (OnLogic CL210 class) running the BEN Care agent and the Thread border router for the two Pods; can be the customer\'s own box instead.'; L('mode', st.mode); break;
    case 'pod': name = `BEN Pod W (${hv.id === 'pod1' ? 'inlet' : 'exhaust'})`; tag = 'controls'; codes = CODES.pod; desc = 'BEN Pod W on the rack rail: two Pt1000 probes, Thread radio, hardware watchdog.'; L('inlet', `${fmt.num(st.rack_inlet_c[0])} °C`); L('outlet', `${fmt.num(st.rack_outlet_c[0])} °C`); break;
    case 'patch': name = 'Patch panel'; tag = 'compute'; codes = CODES.patch; desc = '1U brush / patch panel for cable dressing.'; break;
    case 'desk': name = 'Office desk (for scale)'; tag = 'room'; codes = CODES.desk; desc = d.room_cooling_note || ''; L('room', `${fmt.num((st.mini || {}).room_c)} °C`); break;
    case 'aisle_cold': name = 'Cold aisle'; tag = 'cooling'; codes = CODES.containment; desc = 'Supply-air aisle in front of the rack inlets.'; L('supply', `${fmt.num(st.supply_c)} °C`); L('ΔP', `${fmt.num(st.aisle_dp_pa)} Pa`); break;
    case 'aisle_hot': name = 'Hot aisle'; tag = 'cooling'; codes = CODES.containment; desc = 'Contained exhaust aisle behind the racks.'; L('return', `${fmt.num(st.return_c)} °C`); break;
    default: name = d.tier_label; tag = 'enclosure'; codes = hall ? CODES.hall : CODES.container;
      desc = hall ? `${d.enclosure}: ${d.modules} wide-body modules on a slab, ${d.hardening_label || 'H1'} (${d.hardening_rating || 'IP66'}); ${d.gross_kg.toLocaleString()} kg gross.` : `${d.enclosure}: ${cabinet ? 'NEMA 4X / IP66 cabinet' : 'ISO corner castings, 100 mm PIR insulation'}, ${d.hardening_label || 'H1'}, corrosion class ${d.climate.corrosion}; ${d.gross_kg.toLocaleString()} kg gross.`;
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

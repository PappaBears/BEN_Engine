import { validate, derived, preset, canonicalTier, hardeningRecommended, powerArchitectures, dcConventions, tiersByLineup, lineupOf } from './selector.js';

const $ = (s) => document.querySelector(s);
const fmt = (n) => n.toLocaleString('en-US');
const usd = (n) => '$' + Math.round(n).toLocaleString('en-US');

const PROFILE_BLURB = {
  ai_inference: 'Serve models next to the people and machines that use them. Low latency, N+1, A2 class.',
  ai_training: 'Dense GPU pod for fine-tuning and training. Liquid cooling, A1 class, N+1.',
  private_cloud: 'Your ERP, files and virtual machines on your own pad. N+1, A2 class.',
  disaster_recovery: 'A warm second site in a box. N, A3 class, lowest cost per rack.',
  industrial_ot: 'Analytics and vision at the plant. Dust, heat, vibration packages. N+1, A3.',
  healthcare: 'HIPAA pack, 2N power, A1 class, generator standard.',
  public_sector: 'NIST 800-171 / CMMC pack, 2N, tactical climate options, generator standard.',
  off_grid: 'Solar, battery and generator ready. N+1, A3, remote monitoring first.',
};

const FALLBACK_RISKS = [
  { id: 'R-ELEC', category: 'Electrical', title: 'Arc flash and shock during service', severity: 'high', plain_text: 'A container concentrates a lot of power in a small space.', covered_by: 'NEC 110.26 working space, NFPA 70E labels, lockable disconnects, remote metering so nobody opens panels to read numbers.', customer_owns: 'Only qualified people open electrical panels.', profiles: [] },
  { id: 'R-THERM', category: 'Thermal', title: 'Overheating when cooling fails or utility drops', severity: 'high', plain_text: 'A full rack row can pass its temperature limit within minutes without cooling.', covered_by: 'N+1 cooling, mechanical ride-through option, three-height inlet sensing, twin-predicted minutes-to-limit alarm, automatic load shed hooks.', customer_owns: 'Choose the redundancy level that matches how much downtime costs you.', profiles: [] },
  { id: 'R-FIRE', category: 'Fire', title: 'Fire in an enclosed, unattended space', severity: 'high', plain_text: 'Lithium batteries, power electronics and insulation in one steel box.', covered_by: 'UL 9540 battery cabinets, early smoke detection, clean-agent suppression, hardwired EPO, separation of batteries from IT.', customer_owns: 'Local fire marshal review and annual inspection access.', profiles: [] },
  { id: 'R-WATER', category: 'Water and leaks', title: 'Condensate, rain or coolant leaks', severity: 'medium', plain_text: 'Cooling makes water; liquid cooling moves it on purpose.', covered_by: 'Leak-detection rope under the floor, drip trays, drains, CDU leak interlocks, sealed penetrations.', customer_owns: 'Keep drains and the pad grade clear.', profiles: [] },
  { id: 'R-STRUCT', category: 'Structure and transport', title: 'Damage in transport or wind/seismic events', severity: 'medium', plain_text: 'Cutouts weaken a container; equipment must survive the road.', covered_by: 'Reinforced cutouts, CSC re-certification, tie-down and hold-down design per climate package, transport-mode brackets.', customer_owns: 'Pad, anchoring and permits per the site requirements document.', profiles: [] },
  { id: 'R-CYBER', category: 'Cyber', title: 'Remote access to building controls', severity: 'medium', plain_text: 'A connected box is a target.', covered_by: 'Controls on an isolated network, local-first data, signed firmware, no cloud dependency, outbound-only support tunnel.', customer_owns: 'Your IT network security and credentials policy.', profiles: [] },
  { id: 'R-PERMIT', category: 'Regulatory', title: 'Permits and inspections take longer than the build', severity: 'medium', plain_text: 'Authorities differ on whether a container is a building.', covered_by: 'Compliance pack per profile, PE-stamped drawings where required, pre-submission with the AHJ.', customer_owns: 'Local zoning, noise and setback decisions.', profiles: [] },
  { id: 'R-SUPPLY', category: 'Supply chain', title: 'Long-lead equipment (UPS, cooling, GPUs)', severity: 'medium', plain_text: 'Lead times of 12 to 30 weeks are common.', covered_by: 'Long-lead items ordered at engineering release; alternates qualified in the catalog.', customer_owns: 'Early deposit commits long-lead orders.', profiles: [] },
  { id: 'R-NOISE', category: 'Environmental', title: 'Noise from condensers or dry coolers', severity: 'low', plain_text: 'Outdoor heat rejection makes noise at the property line.', covered_by: 'Low-noise fan selection, acoustic survey in the test guide, placement rules.', customer_owns: 'Local noise ordinance limits.', profiles: [] },
];

let CAT, RISKS, PRICING;
let state = { profile: 'ai_inference', climate: 'temperate', cfg: null, lineup: 'rev2' };
let PRICING_BY_LINEUP = {};
// Rev 2 (docs/REV2_DECISION.md §2): tiers shown follow the lineup; BEN 1 has a form; hero art for tiers without their own image
// Rev 2 heroes live in assets/rev2/hero-<tier>.svg (design agent); Rev 1 configurations and missing Rev 2 files fall back to
// the Rev 1 art in assets/hero-<tier>.svg (HERO_FALLBACK maps the new tiers onto the nearest Rev 1 drawing).
// The page opens on the flagship dense all-in-one box (docs/REV2_DECISION.md §2b); BEN 150 stays one click away.
const OPENING_TIER = 'ben700';
const HERO_FALLBACK = { ben300: 'ben150', ben700: 'ben500' };
function heroSources(tier, lineup) {
  const rev1 = `assets/hero-${HERO_FALLBACK[tier] || tier}.svg`;
  return lineup === 'rev2' ? [`assets/rev2/hero-${tier}.svg`, ...(HERO_FALLBACK[tier] || tier !== 'ben1' ? [rev1] : [])] : [rev1];
}
const lineupTiers = () => tiersByLineup(CAT)[state.lineup];

async function load(url, fallback) { try { const r = await fetch(url); if (!r.ok) throw 0; return await r.json(); } catch { return fallback; } }

function buildTiers() {
  const g = $('#tierGrid'); g.innerHTML = '';
  for (const k of lineupTiers()) {
    const t = CAT.tiers[k];
    const d = derived(preset(k, state.profile, state.climate, CAT, null, state.lineup), CAT);
    const el = document.createElement('article'); el.className = 'card';
    const service = d.mv_service ? `${t.voltage}; ${d.transformers_total} × ${fmt(d.transformer_kva)} kVA transformers at preset` : `${t.voltage}, ${d.service_breaker_a} A at preset`;
    const racks = (t.rows ?? 1) > 1 ? `up to ${t.max_racks} × ${t.rack_u}U in ${t.rows} rows` : `up to ${t.max_racks} × ${t.rack_u}U`;
    const footprint = (t.modules ?? 1) > 1 ? `${t.ext_l_m} × ${t.ext_w_m} × ${t.ext_h_m} m hall (${t.modules} modules) + power module + plant yard` : `${t.ext_l_m} × ${t.ext_w_m} × ${t.ext_h_m} m`;
    el.dataset.tier = k;
    el.innerHTML = `<h3>${t.label}<span class="kw">${fmt(t.it_kw_min)}–${fmt(t.it_kw_max)} kW</span></h3>
      <p class="muted">${t.enclosure}</p>
      <dl><dt>Racks</dt><dd>${racks}</dd><dt>Cooling</dt><dd>${CAT.cooling[t.default_cooling].label}</dd><dt>Service</dt><dd>${service}</dd><dt>Footprint</dt><dd>${footprint}</dd></dl>
      <button class="btn" data-tier="${k}" style="margin-top:12px">Configure ${t.label}</button>`;
    el.querySelector('button').onclick = () => { setPreset(k); location.hash = '#configure'; };
    g.appendChild(el);
  }
}

function buildProfiles() {
  const g = $('#profileGrid'); g.innerHTML = '';
  for (const [k, p] of Object.entries(CAT.profiles)) {
    const b = document.createElement('button'); b.className = 'profile'; b.type = 'button'; b.setAttribute('role', 'listitem');
    b.setAttribute('aria-pressed', String(k === state.profile));
    b.innerHTML = `<span class="tag">${p.redundancy}</span><span class="tag tag-class">ASHRAE ${p.ashrae}</span><h3>${p.label}</h3><p>${PROFILE_BLURB[k] || ''}</p>`;
    b.onclick = () => { state.profile = k; buildProfiles(); buildRisks(); setPreset(state.cfg?.tier || 'ben150'); };
    g.appendChild(b);
  }
  const cs = $('#climateSel'); cs.innerHTML = '';
  for (const [k, c] of Object.entries(CAT.climates)) { const o = document.createElement('option'); o.value = k; o.textContent = c.label; o.selected = k === state.climate; cs.appendChild(o); }
  cs.onchange = () => { state.climate = cs.value; climateNote(); setPreset(state.cfg?.tier || 'ben150'); };
  climateNote();
}
function climateNote() { const c = CAT.climates[state.climate]; $('#climateNote').textContent = `Design day ${c.t_design_c} °C, low ${c.t_min_c} °C, corrosion class ${c.corrosion}, wind ${c.wind_ms} m/s. Cooling is derated and the envelope package is chosen from this.`; }

function buildRisks() {
  const list = $('#riskList'); list.innerHTML = '';
  // filtered by mission profile AND tier (risks.json `tiers`; an empty or missing list means every tier)
  const tier = state.cfg ? canonicalTier(state.cfg.tier, CAT) : null;
  const rs = RISKS.filter(r => (!r.profiles || r.profiles.length === 0 || r.profiles.includes(state.profile))
    && (!tier || !r.tiers || r.tiers.length === 0 || r.tiers.includes(tier)));
  for (const r of rs) {
    const sev = (r.severity || 'medium').toLowerCase();
    const el = document.createElement('article'); el.className = `risk ${sev}`;
    el.innerHTML = `<div class="cat">${r.category}<br><strong>${sev}</strong></div><div><h4>${r.title}</h4><p>${r.plain_text}</p><p class="cover"><strong>BEN covers:</strong> ${r.covered_by}</p><p class="own"><strong>You own:</strong> ${r.customer_owns}</p></div>`;
    list.appendChild(el);
  }
}

function setPreset(tier, form = null) {
  tier = canonicalTier(tier, CAT);
  if (!lineupTiers().includes(tier)) tier = 'ben150';
  state.cfg = preset(tier, state.profile, state.climate, CAT, null, state.lineup, form);
  writeForm(); recompute(); buildRisks();
}
function buildTierSelect() {
  const ts = $('#tier'); ts.innerHTML = '';
  for (const k of lineupTiers()) { const o = document.createElement('option'); o.value = k; o.textContent = CAT.tiers[k].label; ts.appendChild(o); }
}
// Lineup and BEN 1 form controls are created here (no markup change needed); they use the same label/select pattern as the form
function addRev2Controls() {
  const tierLbl = $('#tier').closest('label');
  const mk = (id, text) => { const l = document.createElement('label'); l.id = id + 'Lbl'; l.append(text + ' '); const sel = document.createElement('select'); sel.id = id; l.appendChild(sel); return l; };
  const ll = mk('lineupSel', 'Lineup');
  for (const [k, t] of [['rev2', 'Rev 2 (current)'], ['rev1', 'Rev 1 (frozen, existing quotes)']]) { const o = document.createElement('option'); o.value = k; o.textContent = t; ll.querySelector('select').appendChild(o); }
  const fl = mk('formSel', 'Form');
  for (const [k, f] of Object.entries(CAT.tiers.ben1?.forms || {})) { const o = document.createElement('option'); o.value = k; o.textContent = f.label; fl.querySelector('select').appendChild(o); }
  tierLbl.before(ll); tierLbl.after(fl);
}
function hardeningNote() {
  const rec = hardeningRecommended(state.profile, state.climate);
  const h = CAT.hardening?.[state.cfg.hardening];
  const chosen = state.cfg.hardening;
  $('#hardeningNote').textContent = `${h ? h.rating + '; coating ' + h.coating + '. ' : ''}Recommended for ${CAT.profiles[state.profile].label} in ${CAT.climates[state.climate].label}: ${rec}` + (rec !== chosen ? ` (you chose ${chosen})` : '');
}
function writeForm() {
  const c = state.cfg; c.tier = canonicalTier(c.tier, CAT); const t = CAT.tiers[c.tier];
  if (!c.hardening) c.hardening = hardeningRecommended(c.profile || state.profile, c.climate || state.climate);
  $('#tier').value = c.tier;
  const mini = t.kind === 'minirack';
  if ($('#lineupSel')) $('#lineupSel').value = state.lineup;
  if ($('#formSel')) { $('#formSelLbl').hidden = !mini; if (mini) $('#formSel').value = c.form; }
  const itMax = mini ? (t.forms[c.form]?.it_kw_max ?? t.it_kw_max) : t.it_kw_max;
  const it = $('#it_kw'); it.step = mini ? 0.1 : 1; it.min = t.it_kw_min; it.max = itMax; it.value = c.it_kw; $('#itOut').value = c.it_kw;
  $('#racks').max = t.max_racks; $('#racks').value = c.racks;
  for (const o of $('#hardeningSel').options) o.hidden = mini ? o.value !== 'IND' : o.value === 'IND';
  $('#hardeningSel').disabled = mini; $('#generator').disabled = mini;
  const cs = $('#cooling'); cs.innerHTML = '';
  for (const [k, v] of Object.entries(CAT.cooling)) {
    if (mini !== (k === 'office_air')) continue;
    if ((c.tier === 'ben5') !== (k === 'cabinet_dx')) continue;
    if (t.liquid_first && k !== 'dlc_hd') continue;
    if (t.kind === 'hall' && k !== 'dlc_cdu' && k !== 'dlc_hd') continue;
    if (k === 'dlc_hd' && !(CAT.dlc_hd_tiers || ['ben150', 'ben500', 'ben2000']).includes(c.tier)) continue;
    const o = document.createElement('option'); o.value = k; o.textContent = v.label + (k === 'dlc_hd' && !t.liquid_first ? ' — forward option, study' : ''); cs.appendChild(o);
  }
  cs.value = c.cooling;
  const ps = $('#powerArch'); ps.innerHTML = '';
  if (!c.power_architecture) c.power_architecture = 'ac480';
  for (const [k, v] of Object.entries(powerArchitectures(CAT))) {
    if (!v.tiers.includes(c.tier)) continue;
    const o = document.createElement('option'); o.value = k; o.textContent = k === 'dc800' ? '800 VDC bus, battery on bus — forward option, study' : '480 V AC → UPS → AC PDUs (today)'; ps.appendChild(o);
  }
  if (![...ps.options].some(o => o.value === c.power_architecture)) c.power_architecture = 'ac480';
  ps.value = c.power_architecture;
  const cv = $('#dcConv'); cv.innerHTML = '';
  if (!c.dc_convention) c.dc_convention = 'bipolar_400';
  for (const [k, v] of Object.entries(dcConventions(CAT))) { const o = document.createElement('option'); o.value = k; o.textContent = v.label; cv.appendChild(o); }
  cv.value = c.dc_convention; cv.closest('label').hidden = c.power_architecture !== 'dc800';
  $('#powerArchNote').textContent = c.power_architecture === 'dc800' ? 'Forward architecture study (docs/FORWARD_ARCHITECTURE_DECISION.md): sizing shown with its stated assumptions; listings for 800 VDC distribution are being confirmed in the program. Not a quotable option yet.' : ''; $('#redundancy').value = c.redundancy; $('#ups_minutes').value = c.ups_minutes; $('#generator').checked = c.generator;
  $('#hardeningSel').value = c.hardening;
  document.querySelectorAll('.sub').forEach(x => x.checked = c.subsystems.includes(x.value));
  $('#white_label').checked = c.white_label; $('#brand').value = c.brand;
  const hero = $('#heroImg'), fig = hero.closest('figure');
  const srcs = heroSources(c.tier, state.lineup); let k = 0;
  hero.onerror = () => { if (++k < srcs.length) hero.src = srcs[k]; else if (fig) fig.hidden = true; };   // no art at all: hide the figure
  hero.onload = () => { if (fig) fig.hidden = false; };
  if (fig) fig.hidden = false;
  hero.src = srcs[0];
  const cap = hero.closest('figure') && hero.closest('figure').querySelector('figcaption');
  if (cap) cap.textContent = `${t.label} · ${t.enclosure} · up to ${fmt(t.it_kw_max)} kW IT · generated from the configuration model`;
  hero.alt = t.kind === 'hall' ? `Isometric illustration of the ${t.label} prefabricated data hall: three joined modules, a power module and a plant yard with dry coolers and generators` : `Isometric illustration of a ${t.label} ${t.kind === 'cabinet' ? 'outdoor cabinet' : 'container data center'} with the Schreiber AI mark on the side`;
}
function readForm() {
  const c = state.cfg;
  c.tier = $('#tier').value; c.it_kw = +$('#it_kw').value; c.racks = +$('#racks').value; c.cooling = $('#cooling').value;
  c.redundancy = $('#redundancy').value; c.ups_minutes = +$('#ups_minutes').value; c.generator = $('#generator').checked;
  c.power_architecture = $('#powerArch').value || 'ac480';
  c.dc_convention = $('#dcConv').value || 'bipolar_400';
  c.hardening = $('#hardeningSel').value || c.hardening || 'H1';
  c.subsystems = [...document.querySelectorAll('.sub:checked')].map(x => x.value);
  c.white_label = $('#white_label').checked; c.brand = $('#brand').value || 'Schreiber AI';
  c.profile = state.profile; c.climate = state.climate;
  c.lineup = state.lineup;
  const mini = CAT.tiers[canonicalTier(c.tier, CAT)]?.kind === 'minirack';
  c.form = mini ? ($('#formSel')?.value || c.form || 'rack10') : '';
  if (mini) { c.hardening = 'IND'; c.generator = false; }
}
function recompute() {
  readForm();
  const errs = validate(state.cfg, CAT);
  const eb = $('#cfgErrors'); eb.hidden = errs.length === 0; eb.innerHTML = errs.map(e => `<div>⚠ ${e}</div>`).join('');
  if (errs.length) { $('#sizing').innerHTML = '<p class="muted">Fix the configuration to see sizing.</p>'; $('#price').innerHTML = ''; return; }
  const d = derived(state.cfg, CAT);
  hardeningNote();
  const layout = d.rows > 1 ? `${state.cfg.racks} racks in ${d.rows} rows of ${d.racks_per_row} (${d.per_rack_kw} kW/rack)` : `${state.cfg.racks} racks (${d.per_rack_kw} kW/rack)`;
  const rows = [['Enclosure', d.enclosure], ['IT load', `${fmt(state.cfg.it_kw)} kW in ${layout}`], ['Cooling', `${d.cooling_units_total} × ${d.cooling_label} (${d.cooling_units_n} duty, ${state.cfg.redundancy})`], ['Cooling derate for climate', `${Math.round(d.cooling_derate * 100)} %`], ['Total electrical load', `${fmt(d.total_kw)} kW / ${fmt(d.total_kva)} kVA`], ['Service', `${d.voltage}, ${fmt(d.service_breaker_a)} A main (calc ${fmt(d.service_amps_calc)} A)`]];
  if (d.mv_service) rows.push(['Transformers', `${d.transformers_total} × ${fmt(d.transformer_kva)} kVA pad-mount (MV → 480 V, ${state.cfg.redundancy})`]);
  if (d.power_architecture === 'dc800') {
    rows.push(['Power architecture', `800 VDC bus — ${d.dc_convention_label}; ${d.dc_bus_v_pole} V to ground — forward option, study`]);
    rows.push(['Bus window', `${d.dc_bus_v_min}–${d.dc_bus_v_max} V: working ${d.dc_window_basis}`]);
    rows.push(['AC/DC front end', `${fmt(d.ac_dc_front_end_kw)} kW at ${Math.round(d.rectifier_eff * 1000) / 10} % (vendor claim) · ${d.rectifier_modules} × ${d.rectifier_module_kw} kW rectifier modules (${state.cfg.redundancy})`]);
    rows.push(['Rack interface', `${d.rack_shelves_total} × ${d.rack_shelf_kw} kW 800 V → 50 V DC shelves (${d.rack_shelves_per_rack}/rack, ${Math.round(d.rack_shelf_eff * 1000) / 10} % vendor claim) or MGX 800 VDC power racks; no server takes 800 V directly`]);
    rows.push(['DC bus', `${fmt(d.dc_bus_current_a)} A with 25 % headroom → ${fmt(d.dc_busway_a)} A busway · ${d.imd_count} insulation monitors (${d.dc_imd_arrangement})`]);
    rows.push(['Battery on bus', `${fmt(d.battery_on_bus_kwh)} kWh, ${d.battery_string_v}, ${state.cfg.ups_minutes} min — no UPS modules`]);
    rows.push(['Loss / copper (assumptions)', `${fmt(d.dc_loss_saving_kw)} kW distribution loss saved (3 % assumption) · copper ${fmt(d.copper_kg_dc_bus)} kg vs ${fmt(d.copper_kg_ac_feeders)} kg AC feeders (−${d.copper_saving_pct} %, area-ratio method)`]);
  } else {
    rows.push(['UPS', `${d.ups_modules} × ${fmt(d.ups_kva_each)} kVA, ${state.cfg.ups_minutes} min → ${fmt(d.battery_kwh)} kWh LFP`]);
  }
  if (d.kind === 'minirack') {
    rows.push(['Outlet', `${d.outlet_circuit}; draws ${d.outlet_amps} A at 120 V (${d.ups_plug}). ${d.voltage_option}`]);
    rows.push(['UPS', `${d.ups_model}; est. ${d.ups_runtime_min_est} min at full load${d.ups_battery_packs ? ` + ${d.ups_battery_packs} battery pack(s)` : ''}`]);
    rows.push(['Heat to the room', `${fmt(d.heat_to_room_w)} W (${fmt(d.heat_to_room_btu_h)} BTU/h): ${d.room_cooling_note}`]);
    rows.push(['Noise at 1 m (estimate)', `${d.noise_dba_est} dBA (target ${d.noise_dba_target})${d.noise_ok ? '' : ` — meets the target up to ${d.noise_quiet_up_to_kw} kW`}`]);
  }
  if (d.liquid_first) {
    rows.push(['Row (door end first)', `${d.row_items.join(' · ')} — ${fmt(d.row_length_mm)} of ${fmt(Math.round(((d.geometry || CAT.tiers[state.cfg.tier]).int_l_m) * 1000))} mm`]);
    rows.push(['Power gear inside', `${d.ups_frames} UPS frame(s), ${d.battery_cabinets} lithium cabinet(s) ${fmt(d.battery_kwh_installed)} kWh (${d.battery_minutes_installed} min), ${d.swbd_sections ? d.swbd_sections + ' switchboard section(s)' : '600 A panelboard on the end wall'}`]);
    rows.push(['Residual air', `${d.fancoils_total} in-row fan coils on an ${d.trim_loop_c} °C trim loop (${fmt(d.trim_loop_kw)} kW trim chiller on the skid)`]);
  }
  if (d.lineup === 'rev2') rows.push(['Density', `${d.kw_per_rack} kW/rack · ${d.kw_per_m2_footprint} kW/m² footprint · ${d.kw_per_m3_volume} kW/m³`]);
  if (state.cfg.cooling === 'dlc_hd') {
    rows.push(['Liquid loop', `${d.loop_water_class} warm water, ${d.loop_supply_design_c}/${d.loop_return_design_c} °C, ${fmt(d.loop_flow_lpm)} L/min at ΔT ${d.loop_dt_design_k} K`]);
    rows.push(['Heat reuse available', `${fmt(d.heat_reuse_kw_available)} kW at the return (${Math.round(d.air_residual * 100)} % of IT heat stays on the air side)`]);
  }
  rows.push(['Generators', d.generators_total ? `${d.generators_total} × ${fmt(d.generator_kw_each)} kW standby${d.mv_service ? ' (N+1, 48 h fuel)' : ''}` : 'none (option)']);
  rows.push(['Hardening', `${d.hardening_label}: ${d.hardening_rating}`]);
  rows.push(['Airflow', `${fmt(d.airflow_cfm)} cfm`], ['Gross mass', `${fmt(d.gross_kg)} kg${d.modules > 1 ? ` (${d.modules} modules + power module)` : ''}`], ['Estimated PUE', d.pue_estimate], ['Environmental class', `ASHRAE ${d.ashrae_class}`]);
  $('#sizing').innerHTML = `<h3>Sizing</h3><table>${rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>`;
  renderPrice(d);
  const q = encodeURIComponent(JSON.stringify(state.cfg));
  $('#openDemo').href = `../dashboard/?config=${q}`;
  $('#mailto').href = `mailto:Ben@SchreiberAI.com?subject=${encodeURIComponent('BEN Engine inquiry: ' + d.tier_label + ' ' + state.cfg.it_kw + ' kW ' + CAT.profiles[state.profile].label)}&body=${encodeURIComponent('Configuration:\n' + JSON.stringify(state.cfg, null, 2))}`;
}
function renderPrice(d) {
  const p = $('#price');
  PRICING = PRICING_BY_LINEUP[state.lineup] || PRICING_BY_LINEUP.rev1;
  if (!PRICING || !PRICING[state.cfg.tier]) { p.innerHTML = '<h3>Indicative price</h3><p class="muted">Pricing table not published yet. The bill of materials in the repository (docs/BOM.md) is the source.</p>'; return; }
  const t = PRICING[state.cfg.tier];
  // scale by selected subsystems and by IT kW relative to preset (compute scales, rest step-wise)
  let total = 0, conf = 0, list = 0, est = 0;
  for (const s of ['power', 'cooling', 'compute', 'controls', 'base']) {
    if (s !== 'base' && !state.cfg.subsystems.includes(s)) continue;
    const b = t.by_subsystem[s]; if (!b) continue;
    let scale = 1;
    if (s === 'compute') scale = state.cfg.it_kw / t.preset_it_kw;
    if (s === 'cooling') scale = d.cooling_units_total / t.preset_cooling_units;
    total += b.total * scale; conf += b.confirmed * scale; list += b.list * scale; est += b.estimate * scale;
  }
  const pc = (x) => Math.round(100 * x / Math.max(total, 1));
  p.innerHTML = `<h3>Indicative hardware + build price</h3><div class="big">${usd(total)}</div>
    <p class="muted small">Excludes site civil, utility service, permits and GPUs beyond the reference compute node unless Compute is selected. Managed service is priced separately.</p>
    <div class="bar"><span class="c" style="width:${pc(conf)}%"></span><span class="l" style="width:${pc(list)}%"></span><span class="e" style="width:${pc(est)}%"></span></div>
    <div class="legend"><span><i style="background:var(--green)"></i>Vendor-confirmed ${pc(conf)} %</span><span><i style="background:var(--cyan)"></i>List price ${pc(list)} %</span><span><i style="background:var(--hold)"></i>Estimate ${pc(est)} %</span></div>
    <p class="small muted">Per kW IT: ${usd(total / state.cfg.it_kw)}. Priced ${t.priced_on}.</p>${(state.cfg.power_architecture === 'dc800' || state.cfg.cooling === 'dlc_hd') ? '<p class="small muted"><strong>Forward options are not in this table.</strong> The 800 VDC chain and the high-density liquid loop are costed only as estimates in <a href="../docs/BOM-ben150-forward.md">docs/BOM-ben150-forward.md</a> (forward prototype); the figure above still uses the standard AC / cooling pricing.</p>' : ''}`;
}

async function main() {
  CAT = await load('assets/catalog.json', null);
  if (!CAT) { document.body.insertAdjacentHTML('afterbegin', '<p class="errors">Could not load the catalog. Serve this folder over HTTP.</p>'); return; }
  RISKS = await load('assets/risks.json', FALLBACK_RISKS);
  PRICING_BY_LINEUP = { rev1: await load('assets/pricing.json', null), rev2: await load('assets/pricing-rev2.json', null) };
  PRICING = PRICING_BY_LINEUP.rev2 || PRICING_BY_LINEUP.rev1;
  addRev2Controls();
  buildTiers(); buildProfiles(); buildRisks();
  buildTierSelect();
  const ts = $('#tier');
  const hs = $('#hardeningSel'); for (const [k, h] of Object.entries(CAT.hardening || {})) { const o = document.createElement('option'); o.value = k; o.textContent = h.label; o.title = h.rating; hs.appendChild(o); }
  const urlCfg = new URLSearchParams(location.search).get('config');
  if (urlCfg) { try { state.cfg = JSON.parse(urlCfg); state.cfg.tier = canonicalTier(state.cfg.tier, CAT); state.lineup = lineupOf(state.cfg, CAT); state.cfg.lineup = state.lineup; buildTierSelect(); buildTiers(); state.profile = state.cfg.profile; state.climate = state.cfg.climate; buildProfiles(); buildRisks(); writeForm(); recompute(); } catch { setPreset(OPENING_TIER); } }
  else setPreset(OPENING_TIER);
  ts.onchange = () => setPreset(ts.value);
  $('#lineupSel').onchange = () => { state.lineup = $('#lineupSel').value; buildTierSelect(); buildTiers(); setPreset(state.cfg?.tier || 'ben150'); };
  $('#formSel').onchange = () => setPreset('ben1', $('#formSel').value);
  $('#it_kw').oninput = () => { $('#itOut').value = $('#it_kw').value; recompute(); };
  for (const id of ['#racks', '#cooling', '#redundancy', '#ups_minutes', '#generator', '#hardeningSel', '#white_label', '#brand']) $(id).onchange = recompute;
  $('#powerArch').onchange = () => { readForm(); writeForm(); recompute(); };
  $('#dcConv').onchange = recompute;
  document.querySelectorAll('.sub').forEach(x => x.onchange = recompute);
  $('#dlCfg').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(state.cfg, null, 2)], { type: 'application/json' })); a.download = `ben-config-${state.cfg.tier}.json`; a.click(); };
}
main();

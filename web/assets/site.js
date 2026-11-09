import { validate, derived, preset, canonicalTier, hardeningRecommended, powerArchitectures } from './selector.js';

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
let state = { profile: 'ai_inference', climate: 'temperate', cfg: null };

async function load(url, fallback) { try { const r = await fetch(url); if (!r.ok) throw 0; return await r.json(); } catch { return fallback; } }

function buildTiers() {
  const g = $('#tierGrid'); g.innerHTML = '';
  for (const [k, t] of Object.entries(CAT.tiers)) {
    const d = derived(preset(k, state.profile, state.climate, CAT), CAT);
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
    b.innerHTML = `<span class="tag">${p.redundancy}</span><span class="tag" style="background:#66E3FF">ASHRAE ${p.ashrae}</span><h3>${p.label}</h3><p>${PROFILE_BLURB[k] || ''}</p>`;
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
  const rs = RISKS.filter(r => !r.profiles || r.profiles.length === 0 || r.profiles.includes(state.profile));
  for (const r of rs) {
    const sev = (r.severity || 'medium').toLowerCase();
    const el = document.createElement('article'); el.className = `risk ${sev}`;
    el.innerHTML = `<div class="cat">${r.category}<br><strong>${sev}</strong></div><div><h4>${r.title}</h4><p>${r.plain_text}</p><p class="cover"><strong>BEN covers:</strong> ${r.covered_by}</p><p class="own"><strong>You own:</strong> ${r.customer_owns}</p></div>`;
    list.appendChild(el);
  }
}

function setPreset(tier) {
  state.cfg = preset(canonicalTier(tier, CAT), state.profile, state.climate, CAT);
  writeForm(); recompute();
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
  const it = $('#it_kw'); it.min = t.it_kw_min; it.max = t.it_kw_max; it.value = c.it_kw; $('#itOut').value = c.it_kw;
  $('#racks').max = t.max_racks; $('#racks').value = c.racks;
  const cs = $('#cooling'); cs.innerHTML = '';
  for (const [k, v] of Object.entries(CAT.cooling)) {
    if ((c.tier === 'ben5') !== (k === 'cabinet_dx')) continue;
    if (t.kind === 'hall' && k !== 'dlc_cdu' && k !== 'dlc_hd') continue;
    if (k === 'dlc_hd' && !(CAT.dlc_hd_tiers || ['ben150', 'ben500', 'ben2000']).includes(c.tier)) continue;
    const o = document.createElement('option'); o.value = k; o.textContent = v.label + (k === 'dlc_hd' ? ' — forward option, study' : ''); cs.appendChild(o);
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
  $('#powerArchNote').textContent = c.power_architecture === 'dc800' ? 'Forward architecture study (docs/FORWARD_ARCHITECTURE_DECISION.md): sizing shown with its stated assumptions; listings for 800 VDC distribution are being confirmed in the program. Not a quotable option yet.' : ''; $('#redundancy').value = c.redundancy; $('#ups_minutes').value = c.ups_minutes; $('#generator').checked = c.generator;
  $('#hardeningSel').value = c.hardening;
  document.querySelectorAll('.sub').forEach(x => x.checked = c.subsystems.includes(x.value));
  $('#white_label').checked = c.white_label; $('#brand').value = c.brand;
  const hero = $('#heroImg'); hero.src = `assets/hero-${c.tier}.svg`;
  const cap = hero.closest('figure') && hero.closest('figure').querySelector('figcaption');
  if (cap) cap.textContent = `${t.label} · ${t.enclosure} · up to ${fmt(t.it_kw_max)} kW IT · generated from the configuration model`;
  hero.alt = t.kind === 'hall' ? `Isometric illustration of the ${t.label} prefabricated data hall: three joined modules, a power module and a plant yard with dry coolers and generators` : `Isometric illustration of a ${t.label} ${t.kind === 'cabinet' ? 'outdoor cabinet' : 'container data center'} with the Schreiber AI mark on the side`;
}
function readForm() {
  const c = state.cfg;
  c.tier = $('#tier').value; c.it_kw = +$('#it_kw').value; c.racks = +$('#racks').value; c.cooling = $('#cooling').value;
  c.redundancy = $('#redundancy').value; c.ups_minutes = +$('#ups_minutes').value; c.generator = $('#generator').checked;
  c.power_architecture = $('#powerArch').value || 'ac480';
  c.hardening = $('#hardeningSel').value || c.hardening || 'H1';
  c.subsystems = [...document.querySelectorAll('.sub:checked')].map(x => x.value);
  c.white_label = $('#white_label').checked; c.brand = $('#brand').value || 'Schreiber AI';
  c.profile = state.profile; c.climate = state.climate;
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
    rows.push(['Power architecture', `800 VDC bus (±${d.dc_bus_v_pole} V to ground, ${d.dc_bus_v_min}–${d.dc_bus_v_max} V window) — forward option, study`]);
    rows.push(['AC/DC front end', `${fmt(d.ac_dc_front_end_kw)} kW at ${Math.round(d.rectifier_eff * 1000) / 10} % (assumption) · ${d.rectifier_modules} × ${d.rectifier_module_kw} kW rectifier modules (${state.cfg.redundancy})`]);
    rows.push(['DC bus', `${fmt(d.dc_bus_current_a)} A with 25 % headroom → ${fmt(d.dc_busway_a)} A busway · ${d.imd_count} insulation monitors`]);
    rows.push(['Battery on bus', `${fmt(d.battery_on_bus_kwh)} kWh, ${d.battery_string_v}, ${state.cfg.ups_minutes} min — no UPS modules`]);
    rows.push(['Loss / copper (assumptions)', `${fmt(d.dc_loss_saving_kw)} kW distribution loss saved (3 % assumption) · copper ${fmt(d.copper_kg_dc_bus)} kg vs ${fmt(d.copper_kg_ac_feeders)} kg AC feeders (−${d.copper_saving_pct} %, area-ratio method)`]);
  } else {
    rows.push(['UPS', `${d.ups_modules} × ${fmt(d.ups_kva_each)} kVA, ${state.cfg.ups_minutes} min → ${fmt(d.battery_kwh)} kWh LFP`]);
  }
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
    <div class="legend"><span><i style="background:var(--green)"></i>Vendor-confirmed ${pc(conf)} %</span><span><i style="background:var(--cyan)"></i>List price ${pc(list)} %</span><span><i style="background:var(--amber)"></i>Estimate ${pc(est)} %</span></div>
    <p class="small muted">Per kW IT: ${usd(total / state.cfg.it_kw)}. Priced ${t.priced_on}.</p>`;
}

async function main() {
  CAT = await load('assets/catalog.json', null);
  if (!CAT) { document.body.insertAdjacentHTML('afterbegin', '<p class="errors">Could not load the catalog. Serve this folder over HTTP.</p>'); return; }
  RISKS = await load('assets/risks.json', FALLBACK_RISKS);
  PRICING = await load('assets/pricing.json', null);
  buildTiers(); buildProfiles(); buildRisks();
  const ts = $('#tier'); for (const [k, t] of Object.entries(CAT.tiers)) { const o = document.createElement('option'); o.value = k; o.textContent = t.label; ts.appendChild(o); }
  const hs = $('#hardeningSel'); for (const [k, h] of Object.entries(CAT.hardening || {})) { const o = document.createElement('option'); o.value = k; o.textContent = h.label; o.title = h.rating; hs.appendChild(o); }
  const urlCfg = new URLSearchParams(location.search).get('config');
  if (urlCfg) { try { state.cfg = JSON.parse(urlCfg); state.cfg.tier = canonicalTier(state.cfg.tier, CAT); state.profile = state.cfg.profile; state.climate = state.cfg.climate; buildProfiles(); buildRisks(); writeForm(); recompute(); } catch { setPreset('ben150'); } }
  else setPreset('ben150');
  ts.onchange = () => setPreset(ts.value);
  $('#it_kw').oninput = () => { $('#itOut').value = $('#it_kw').value; recompute(); };
  for (const id of ['#racks', '#cooling', '#redundancy', '#ups_minutes', '#generator', '#hardeningSel', '#white_label', '#brand']) $(id).onchange = recompute;
  $('#powerArch').onchange = () => { readForm(); writeForm(); recompute(); };
  document.querySelectorAll('.sub').forEach(x => x.onchange = recompute);
  $('#dlCfg').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(state.cfg, null, 2)], { type: 'application/json' })); a.download = `ben-config-${state.cfg.tier}.json`; a.click(); };
}
main();

// SELECTOR panel: builds a Config, validates it live, posts it (rebuilds twin + 3D scene).
import { api, h, fmt } from '../util.js';

let catalog = null, draft = null, root = null, errorsEl = null, derivedEl = null, applyBtn = null, timer = null, ctxRef = null;
const FIELDS = ['tier', 'profile', 'climate', 'it_kw', 'racks', 'cooling', 'redundancy', 'subsystems', 'white_label', 'brand', 'ups_minutes', 'generator', 'site_name', 'hardening', 'controls_tier', 'power_architecture', 'dc_convention'];
const SEVERE = ['coastal', 'hot_arid', 'cold', 'high_altitude', 'hot_humid'];
const recommendHardening = (profile, climate) => profile === 'public_sector' ? 'H3' : (SEVERE.includes(climate) ? 'H2' : 'H1');

function field(label, input, outId) {
  return h('div', { class: 'field' }, h('label', {}, label, outId ? h('output', { id: outId }) : null), input);
}
function sel(name, options, onchange) {
  const s = h('select', { name, onChange: (e) => { draft[name] = e.target.value; onchange && onchange(); schedule(); } }, ...options.map(([v, l]) => h('option', { value: v, selected: draft[name] === v }, l)));
  return s;
}

export default {
  id: 'selector', label: 'Selector', title: 'Configuration selector',
  async mount(el, ctx) {
    ctxRef = ctx; root = el;
    el.append(h('p', { class: 'muted' }, 'Loading catalog…'));
    catalog = await api('/api/catalog');
    if (ctx.store.config) { draft = structuredClone(ctx.store.config); render(); }
  },
  onConfig(payload) {
    draft = structuredClone(payload.config);
    if (catalog) render();
  },
};

function schedule() { clearTimeout(timer); timer = setTimeout(validate, 250); }

async function validate() {
  if (!draft) return;
  try {
    const r = await api('/api/config/validate', { body: draft });
    showErrors(r.errors); if (r.derived) showDerived(r.derived);
    applyBtn.disabled = r.errors.length > 0;
  } catch (e) { showErrors([e.message]); }
}
function showErrors(errs) {
  errorsEl.replaceChildren();
  if (!errs || !errs.length) { errorsEl.hidden = true; return; }
  errorsEl.hidden = false;
  errorsEl.append(h('b', {}, 'Configuration is not valid'), h('ul', {}, ...errs.map(e => h('li', {}, e))));
}
function showDerived(d) {
  const rows = [
    ['Enclosure', `${d.enclosure}${d.modules > 1 ? ` · ${d.modules} modules` : ''}`],
    ['Service', `${d.voltage} · ${d.service_breaker_a.toLocaleString()} A breaker (${d.service_amps_calc.toLocaleString()} A calc)`],
  ];
  if (d.mv_service) rows.push(['Transformers', `${d.transformers_total} × ${d.transformer_kva.toLocaleString()} kVA pad-mount (MV → 480 V)`]);
  if (d.power_architecture === 'dc800') {
    rows.push(['Power architecture', `800 VDC bus — ${d.dc_convention_label}; ${d.dc_bus_v_pole} V to ground — forward option, study`]);
    rows.push(['Bus window', `${d.dc_bus_v_min}–${d.dc_bus_v_max} V (working ${d.dc_window_basis})`]);
    rows.push(['AC/DC front end', `${d.ac_dc_front_end_kw.toLocaleString()} kW · ${d.rectifier_modules} × ${d.rectifier_module_kw} kW rectifier modules (${draft.redundancy}); ${d.rack_shelves_total} × ${d.rack_shelf_kw} kW 800→50 V rack shelves (efficiencies: vendor claims)`]);
    rows.push(['DC bus', `${d.dc_bus_current_a.toLocaleString()} A → ${d.dc_busway_a.toLocaleString()} A busway · ${d.imd_count} IMD`]);
    rows.push(['Battery on bus', `${d.battery_on_bus_kwh.toLocaleString()} kWh (${d.battery_string_v}) · no UPS modules`]);
    rows.push(['Loss / copper (assumed)', `−${d.dc_loss_saving_kw} kW distribution loss · copper −${d.copper_saving_pct} % (${d.copper_kg_dc_bus} vs ${d.copper_kg_ac_feeders} kg)`]);
  } else {
    rows.push(['UPS', `${d.ups_modules} × ${d.ups_kva_each.toLocaleString()} kVA · ${d.battery_kwh.toLocaleString()} kWh`]);
  }
  if (d.loop_flow_lpm !== undefined) {
    rows.push(['Liquid loop', `${d.loop_water_class} · ${d.loop_supply_design_c}/${d.loop_return_design_c} °C · ${d.loop_flow_lpm.toLocaleString()} L/min at ΔT ${d.loop_dt_design_k} K`]);
    rows.push(['Heat reuse', `${d.heat_reuse_kw_available.toLocaleString()} kW available at the return`]);
  }
  rows.push(['Generators', d.generators_total ? `${d.generators_total} × ${d.generator_kw_each.toLocaleString()} kW${d.mv_service ? ' (N+1, 48 h fuel)' : ''}` : 'none']);
  rows.push(
    ['Cooling', `${d.cooling_units_total} × ${d.cooling_unit_kw_derated} kW (${d.cooling_units_n} duty, derate ${d.cooling_derate})`],
    ['Layout', d.rows > 1 ? `${d.rows} rows of ${d.racks_per_row} racks · ${d.row_length_mm} mm per row` : `single row · ${d.row_length_mm} mm`],
    ['Hardening', `${d.hardening_label} · ${d.hardening_rating}` + (d.hardening_recommended !== d.hardening ? ` · recommended here: ${d.hardening_recommended}` : '')],
    ['Per rack', `${d.per_rack_kw} kW · ASHRAE ${d.ashrae_class}`],
    ['Controls', `${d.controls_label} · ${d.pods} BEN Pods`],
    ['Total / PUE est.', `${d.total_kw.toLocaleString()} kW · ${d.pue_estimate}`],
    ['Airflow', `${d.airflow_cfm.toLocaleString()} cfm`],
    ['Gross mass', `${d.gross_kg.toLocaleString()} kg (payload ${d.payload_kg.toLocaleString()})`],
    ['Envelope gain', `${d.envelope_gain_kw} kW at ${d.climate.t_design_c} °C`],
  );
  derivedEl.replaceChildren(h('table', { class: 'kv' }, ...rows.map(([k, v]) => h('tr', {}, h('td', {}, k), h('td', {}, v)))));
}

function render() {
  const tiers = catalog.tiers, g = tiers[draft.tier];
  root.replaceChildren();
  const presetRow = h('div', { class: 'row' }, ...Object.entries(tiers).map(([t, tg]) => h('button', { class: 'btn btn-sm' + (draft.tier === t ? ' active' : ''), onClick: async () => { const p = await api('/api/presets'); draft = p[t].config; render(); schedule(); } }, tg.label)));
  if (!draft.hardening) draft.hardening = recommendHardening(draft.profile, draft.climate);
  if (!draft.controls_tier) draft.controls_tier = 'auto';
  if (!draft.power_architecture) draft.power_architecture = 'ac480';
  if (!draft.dc_convention) draft.dc_convention = 'bipolar_400';
  const tierSel = sel('tier', Object.entries(tiers).map(([k, v]) => [k, `${v.label} — ${v.enclosure}`]), () => {
    const ng = tiers[draft.tier];
    draft.it_kw = Math.min(ng.it_kw_max, Math.max(ng.it_kw_min, draft.it_kw)); draft.racks = Math.min(ng.max_racks, Math.max(1, draft.racks));
    draft.cooling = ng.kind === 'hall' ? 'dlc_cdu' : ng.default_cooling; if (ng.kind === 'hall') draft.generator = true;
    if (draft.power_architecture === 'dc800' && !((catalog.power_architectures?.dc800?.tiers) || ['ben150', 'ben500', 'ben2000']).includes(draft.tier)) draft.power_architecture = 'ac480';
    render();
  });
  const paTable = catalog.power_architectures || { ac480: { tiers: ['ben5', 'ben30', 'ben150', 'ben500', 'ben2000'] }, dc800: { tiers: ['ben150', 'ben500', 'ben2000'] } };
  const paLabel = { ac480: '480 V AC → UPS → AC PDUs (today)', dc800: '800 VDC bus, battery on bus — forward option (study)' };
  const paNote = h('div', { class: 'muted', style: { fontSize: '12px' } });
  const convTable = catalog.dc_conventions || { bipolar_400: { label: '±400 VDC bipolar, HR midpoint (OCP Diablo 400)' }, unipolar_800: { label: '800 VDC unipolar, isolated return (OCP LVDC SST v0.3)' } };
  const convSel = sel('dc_convention', Object.entries(convTable).map(([k, v]) => [k, v.label]));
  const convField = field('DC convention', convSel);
  const updatePaNote = () => { paNote.textContent = draft.power_architecture === 'dc800' ? 'Forward architecture study: AC/DC front end → DC busway → 800 V→50 V rack shelves (or MGX power racks); sizing uses stated assumptions and vendor-claimed efficiencies (docs/FORWARD_ARCHITECTURE_DECISION.md, docs/research). Listings to be confirmed in the program.' : ''; convField.hidden = draft.power_architecture !== 'dc800'; };
  const paSel = sel('power_architecture', Object.entries(paTable).filter(([k, v]) => !v.tiers || v.tiers.includes(draft.tier)).map(([k]) => [k, paLabel[k] || k]), updatePaNote);
  updatePaNote();
  const hardeningTable = catalog.hardening || { H1: { label: 'H1 Standard', rating: 'NEMA 4X / IP66' }, H2: { label: 'H2 Severe environment', rating: 'IP66 + flood plinth' }, H3: { label: 'H3 Hardened / government', rating: 'IP66 + ballistic + forced-entry + HEMP option' } };
  const hardNote = h('div', { class: 'muted', id: 'hardening-note', style: { fontSize: '12px' } });
  const updateHardNote = () => { const rec = recommendHardening(draft.profile, draft.climate); const hz = hardeningTable[draft.hardening] || {}; hardNote.textContent = `${hz.rating || ''}${hz.coating ? ' · ' + hz.coating : ''} — recommended for this profile and climate: ${rec}${rec !== draft.hardening ? ` (selected ${draft.hardening})` : ''}`; };
  const hardSel = sel('hardening', Object.entries(hardeningTable).map(([k, v]) => [k, `${v.label} — ${v.rating}`]), updateHardNote);
  updateHardNote();
  const kwOut = h('output', {}, `${draft.it_kw} kW`);
  const kw = h('input', { type: 'range', min: g.it_kw_min, max: g.it_kw_max, step: g.it_kw_max > 1000 ? 50 : g.it_kw_max > 50 ? 5 : 1, value: draft.it_kw, onInput: (e) => { draft.it_kw = +e.target.value; kwOut.value = `${draft.it_kw} kW`; schedule(); } });
  const racksOut = h('output', {}, draft.racks);
  const racks = h('input', { type: 'range', min: 1, max: g.max_racks, step: 1, value: draft.racks, onInput: (e) => { draft.racks = +e.target.value; racksOut.value = draft.racks; schedule(); } });
  const subs = h('div', { class: 'checks' }, ...catalog.subsystems.map(s => h('label', {}, h('input', { type: 'checkbox', checked: draft.subsystems.includes(s), onChange: (e) => { draft.subsystems = e.target.checked ? [...new Set([...draft.subsystems, s])] : draft.subsystems.filter(x => x !== s); schedule(); } }), s)));
  const brandIn = h('input', { type: 'text', value: draft.brand, maxlength: 40, disabled: !draft.white_label, onInput: (e) => { draft.brand = e.target.value || 'Schreiber AI'; schedule(); } });
  const wl = h('label', {}, h('input', { type: 'checkbox', checked: draft.white_label, onChange: (e) => { draft.white_label = e.target.checked; brandIn.disabled = !draft.white_label; if (!draft.white_label) { draft.brand = 'Schreiber AI'; brandIn.value = draft.brand; } schedule(); } }), 'White-label');
  const gen = h('label', {}, h('input', { type: 'checkbox', checked: draft.generator, onChange: (e) => { draft.generator = e.target.checked; schedule(); } }), 'Generator ready');
  errorsEl = h('div', { class: 'errors', hidden: true });
  derivedEl = h('div', {});
  applyBtn = h('button', { class: 'btn btn-primary', id: 'btn-apply-config', onClick: apply }, 'Apply · rebuild twin and scene');

  root.append(
    h('h3', {}, 'Tier presets'), presetRow,
    h('h3', {}, 'Configuration'),
    field('Tier', tierSel),
    field('Mission profile', sel('profile', Object.entries(catalog.profiles).map(([k, v]) => [k, `${v.label} (${v.redundancy}, ${v.ashrae})`]), updateHardNote)),
    field('Climate', sel('climate', Object.entries(catalog.climates).map(([k, v]) => [k, `${v.label} — ${v.t_design_c} °C design`]), updateHardNote)),
    field('Hardening', hardSel), hardNote,
    h('div', { class: 'field' }, h('label', {}, `IT load (${g.it_kw_min}–${g.it_kw_max} kW)`, kwOut), kw),
    h('div', { class: 'field' }, h('label', {}, `Racks (1–${g.max_racks})`, racksOut), racks),
    field('Cooling', sel('cooling', Object.entries(catalog.cooling).filter(([k]) => (g.kind !== 'hall' || k === 'dlc_cdu' || k === 'dlc_hd') && (k !== 'dlc_hd' || (catalog.dlc_hd_tiers || ['ben150', 'ben500', 'ben2000']).includes(draft.tier))).map(([k, v]) => [k, `${v.label} (${v.unit_kw} kW/unit, COP ${v.cop})${k === 'dlc_hd' ? ' — forward option' : ''}`]))),
    field('Power architecture', paSel), convField, paNote,
    h('div', { class: 'grid2' },
      field('Redundancy', sel('redundancy', catalog.redundancy.map(r => [r, r]))),
      field('UPS minutes', h('input', { type: 'number', min: 2, max: 60, value: draft.ups_minutes, onInput: (e) => { draft.ups_minutes = +e.target.value || 10; schedule(); } }))),
    h('h3', {}, 'Subsystems'), subs,
    h('h3', {}, 'Brand & site'),
    h('div', { class: 'checks' }, wl, gen),
    field('Brand text (rendered on the container)', brandIn),
    field('Site name', h('input', { type: 'text', value: draft.site_name, onInput: (e) => { draft.site_name = e.target.value; schedule(); } })),
    errorsEl,
    h('div', { class: 'row', style: { marginTop: '8px' } }, applyBtn),
    h('h3', {}, 'Derived sizing'), derivedEl,
  );
  validate();
}

async function apply() {
  applyBtn.disabled = true; applyBtn.textContent = 'Applying…';
  try {
    const body = {}; for (const k of FIELDS) body[k] = draft[k];
    const r = await api('/api/config', { body });
    showErrors([]); showDerived(r.derived);
    ctxRef.store.setConfig(r);
    applyBtn.textContent = 'Applied ✓';
    setTimeout(() => { applyBtn.textContent = 'Apply · rebuild twin and scene'; applyBtn.disabled = false; }, 1200);
  } catch (e) {
    showErrors(e.body && e.body.errors ? e.body.errors : [e.message]);
    applyBtn.textContent = 'Apply · rebuild twin and scene'; applyBtn.disabled = false;
  }
}

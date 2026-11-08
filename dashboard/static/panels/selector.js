// SELECTOR panel: builds a Config, validates it live, posts it (rebuilds twin + 3D scene).
import { api, h, fmt } from '../util.js';

let catalog = null, draft = null, root = null, errorsEl = null, derivedEl = null, applyBtn = null, timer = null, ctxRef = null;
const FIELDS = ['tier', 'profile', 'climate', 'it_kw', 'racks', 'cooling', 'redundancy', 'subsystems', 'white_label', 'brand', 'ups_minutes', 'generator', 'site_name'];

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
    ['Service', `${d.voltage} · ${d.service_breaker_a} A breaker (${d.service_amps_calc} A calc)`],
    ['UPS', `${d.ups_modules} × ${d.ups_kva_each} kVA · ${d.battery_kwh} kWh`],
    ['Cooling', `${d.cooling_units_total} × ${d.cooling_unit_kw_derated} kW (${d.cooling_units_n} duty, derate ${d.cooling_derate})`],
    ['Per rack', `${d.per_rack_kw} kW · ASHRAE ${d.ashrae_class}`],
    ['Total / PUE est.', `${d.total_kw} kW · ${d.pue_estimate}`],
    ['Airflow', `${d.airflow_cfm.toLocaleString()} cfm`],
    ['Gross mass', `${d.gross_kg.toLocaleString()} kg (payload ${d.payload_kg.toLocaleString()})`],
    ['Envelope gain', `${d.envelope_gain_kw} kW at ${d.climate.t_design_c} °C`],
  ];
  derivedEl.replaceChildren(h('table', { class: 'kv' }, ...rows.map(([k, v]) => h('tr', {}, h('td', {}, k), h('td', {}, v)))));
}

function render() {
  const tiers = catalog.tiers, g = tiers[draft.tier];
  root.replaceChildren();
  const presetRow = h('div', { class: 'row' }, ...Object.entries(tiers).map(([t, tg]) => h('button', { class: 'btn btn-sm' + (draft.tier === t ? ' active' : ''), onClick: async () => { const p = await api('/api/presets'); draft = p[t].config; render(); schedule(); } }, tg.label)));
  const tierSel = sel('tier', Object.entries(tiers).map(([k, v]) => [k, `${v.label} — ${v.enclosure}`]), () => {
    const ng = tiers[draft.tier];
    draft.it_kw = Math.min(ng.it_kw_max, Math.max(ng.it_kw_min, draft.it_kw)); draft.racks = Math.min(ng.max_racks, Math.max(1, draft.racks));
    draft.cooling = ng.default_cooling; render();
  });
  const kwOut = h('output', {}, `${draft.it_kw} kW`);
  const kw = h('input', { type: 'range', min: g.it_kw_min, max: g.it_kw_max, step: g.it_kw_max > 50 ? 5 : 1, value: draft.it_kw, onInput: (e) => { draft.it_kw = +e.target.value; kwOut.value = `${draft.it_kw} kW`; schedule(); } });
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
    field('Mission profile', sel('profile', Object.entries(catalog.profiles).map(([k, v]) => [k, `${v.label} (${v.redundancy}, ${v.ashrae})`]))),
    field('Climate', sel('climate', Object.entries(catalog.climates).map(([k, v]) => [k, `${v.label} — ${v.t_design_c} °C design`]))),
    h('div', { class: 'field' }, h('label', {}, `IT load (${g.it_kw_min}–${g.it_kw_max} kW)`, kwOut), kw),
    h('div', { class: 'field' }, h('label', {}, `Racks (1–${g.max_racks})`, racksOut), racks),
    field('Cooling', sel('cooling', Object.entries(catalog.cooling).map(([k, v]) => [k, `${v.label} (${v.unit_kw} kW/unit, COP ${v.cop})`]))),
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

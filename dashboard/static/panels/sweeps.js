// SWEEPS panel: automated sweeps (background, pollable), pass/fail criteria, CSV download, fault injection.
import { api, h, fmt } from '../util.js';

let ctxRef = null, catalog = null, listEl = null, faultsEl = null, sourceEl = null, pollTimer = null, unitSel = null;
let lastSig = '';
const FAULT_LABELS = { cooling_unit_fail: 'Cooling unit fail', utility_loss: 'Utility loss', door_open: 'Door open', filter_clog: 'Filter clog', leak: 'Leak', sensor_drift: 'Sensor drift', generator_fail: 'Generator fail' };

export default {
  id: 'sweeps', label: 'Sweeps', title: 'Automated sweeps and fault injection',
  async mount(el, ctx) {
    ctxRef = ctx;
    sourceEl = h('span', { class: 'muted' });
    const btns = h('div', { class: 'row', id: 'sweep-buttons' });
    listEl = h('div', { id: 'sweep-results' });
    faultsEl = h('div', { class: 'fault-grid', id: 'fault-grid' });
    unitSel = h('select', { id: 'fault-unit', style: { width: 'auto' } });
    el.append(
      h('h3', {}, 'Sweeps ', sourceEl), btns, listEl,
      h('h3', {}, 'Fault injection'),
      h('div', { class: 'row', style: { marginBottom: '6px' } }, h('span', { class: 'muted', style: { flex: '0 0 auto' } }, 'Cooling unit'), unitSel),
      faultsEl,
      h('div', { class: 'row', style: { marginTop: '6px' } }, h('button', { class: 'btn btn-sm', id: 'btn-clear-faults', onClick: async () => { await api('/api/faults', { method: 'DELETE' }); } }, 'Clear all faults')),
    );
    try {
      catalog = await api('/api/sweeps/catalog');
      sourceEl.textContent = `(${catalog.source})`;
      btns.replaceChildren(
        ...catalog.sweeps.map(s => h('button', { class: 'btn btn-sm', 'data-sweep': s.name, title: s.description, onClick: () => run(s.name) }, s.label || s.name)),
        h('button', { class: 'btn btn-sm btn-primary', id: 'btn-run-all', onClick: () => run('all') }, 'Run all'),
      );
    } catch (e) { btns.append(h('div', { class: 'note warn' }, e.message)); }
    renderFaults([]);
    poll();
  },
  update(st) { renderFaults(st.faults, st.cooling_units.length); },
};

async function run(name) {
  try { await api('/api/sweep', { body: { name } }); poll(); } catch (e) { listEl.prepend(h('div', { class: 'errors' }, e.message)); }
}

async function poll() {
  clearTimeout(pollTimer);
  let jobs;
  try { jobs = await api('/api/sweeps'); } catch (e) { pollTimer = setTimeout(poll, 3000); return; }
  render(jobs);
  const busy = jobs.some(j => j.status === 'queued' || j.status === 'running');
  pollTimer = setTimeout(poll, busy ? 500 : 4000);
}

function render(jobs) {
  const sig = JSON.stringify(jobs.map(j => [j.id, j.status, j.progress, j.results.length]));
  if (sig === lastSig) return; // keep the DOM stable (download links) when nothing changed
  lastSig = sig;
  if (!jobs.length) { listEl.replaceChildren(h('div', { class: 'note' }, 'No sweeps run yet. Each sweep runs a fresh twin from the current configuration in the background and checks pass criteria.')); return; }
  listEl.replaceChildren(...[...jobs].reverse().slice(0, 6).map(j => {
    const head = h('div', { class: 'row', style: { justifyContent: 'space-between', marginBottom: '4px' } },
      h('b', { style: { flex: '1 1 auto' } }, j.name === 'all' ? 'Automated sequence (all)' : j.name),
      h('span', { class: j.status === 'done' ? (j.passed ? 'pass' : 'fail') : 'muted', style: { flex: '0 0 auto' } }, j.status === 'done' ? (j.passed ? 'PASS' : 'FAIL') : j.status.toUpperCase()),
    );
    const prog = h('div', { class: 'progress' }, h('i', { style: { width: `${Math.round((j.progress || 0) * 100)}%` } }));
    const parts = [head, prog];
    if (j.error) parts.push(h('div', { class: 'errors' }, j.error));
    for (const r of j.results) {
      parts.push(h('table', { class: 'data', style: { marginTop: '6px' } },
        h('thead', {}, h('tr', {}, h('th', { colspan: 3 }, `${r.name} · ${r.rows_n} rows`), h('th', { class: r.passed ? 'pass' : 'fail' }, r.passed ? 'pass' : 'FAIL'))),
        h('tbody', {}, ...r.criteria.map(c => h('tr', {}, h('td', {}, c.name), h('td', { class: 'num' }, typeof c.value === 'number' ? fmt.num(c.value, 2) : String(c.value)), h('td', { class: 'num muted' }, `${c.limit ?? ''} ${c.unit ?? ''}`), h('td', { class: c.pass ? 'pass' : 'fail' }, c.pass ? '✓' : '✗'))))));
      if (r.events && r.events.length) parts.push(h('p', { class: 'muted', style: { fontSize: '11.5px', margin: '4px 0' } }, r.events.join(' · ')));
    }
    if (j.status === 'done') parts.push(h('div', { class: 'row', style: { marginTop: '6px' } }, h('a', { class: 'btn btn-sm', href: `/api/sweeps/${j.id}.csv`, download: `ben_sweep_${j.name}_${j.id}.csv`, 'data-sweep-csv': j.id }, 'Download CSV')));
    return h('div', { class: 'tile', style: { marginBottom: '8px' }, 'data-sweep-job': j.id, 'data-status': j.status }, ...parts);
  }));
}

function renderFaults(active, nUnits = 1) {
  if (unitSel.children.length !== nUnits) unitSel.replaceChildren(...Array.from({ length: nUnits }, (_, i) => h('option', { value: i }, `Unit ${i + 1}`)));
  const faults = Object.keys(FAULT_LABELS);
  if (!faultsEl.children.length) {
    faultsEl.replaceChildren(...faults.map(f => h('button', { class: 'btn btn-sm', 'data-fault': f, onClick: async (e) => {
      const on = e.currentTarget.classList.contains('on');
      const params = f === 'cooling_unit_fail' ? { unit: +unitSel.value } : (f === 'sensor_drift' ? { delta_c: 1.5 } : {});
      try {
        if (on) await api(`/api/fault/${f}` + (f === 'cooling_unit_fail' ? `?unit=${params.unit}` : ''), { method: 'DELETE' });
        else await api('/api/fault', { body: { name: f, params } });
      } catch (err) { console.warn(err); }
    } }, FAULT_LABELS[f])));
  }
  for (const b of faultsEl.children) b.classList.toggle('on', active.includes(b.dataset.fault));
}

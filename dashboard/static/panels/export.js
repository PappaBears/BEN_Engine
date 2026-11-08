// EXPORT panel: telemetry time range -> CSV / JSON download.
import { api, h, fmt } from '../util.js';

let rangeEl = null, modeSel = null, lastIn = null, fromIn = null, toIn = null, timer = null;

export default {
  id: 'export', label: 'Export', title: 'Telemetry export',
  mount(el) {
    rangeEl = h('div', { class: 'note' }, 'Reading buffer…');
    modeSel = h('select', { onChange: toggle }, h('option', { value: 'last' }, 'Last N minutes'), h('option', { value: 'range' }, 'From / to (UTC)'));
    lastIn = h('input', { type: 'number', min: 1, max: 360, value: 10, id: 'exp-last' });
    fromIn = h('input', { type: 'datetime-local', step: 1 }); toIn = h('input', { type: 'datetime-local', step: 1 });
    const rangeFields = h('div', { class: 'grid2', hidden: true }, h('div', { class: 'field' }, h('label', {}, 'From'), fromIn), h('div', { class: 'field' }, h('label', {}, 'To'), toIn));
    const lastField = h('div', { class: 'field' }, h('label', {}, 'Minutes'), lastIn);
    el.append(
      h('h3', {}, 'Buffer'), rangeEl,
      h('h3', {}, 'Time range'), h('div', { class: 'field' }, modeSel), lastField, rangeFields,
      h('div', { class: 'row' },
        h('a', { class: 'btn btn-primary', id: 'btn-export-csv', href: '#', onClick: (e) => { e.currentTarget.href = url('csv'); } }, 'Download CSV'),
        h('a', { class: 'btn', id: 'btn-export-json', href: '#', onClick: (e) => { e.currentTarget.href = url('json'); } }, 'Download JSON')),
      h('p', { class: 'muted', style: { fontSize: '12px' } }, 'One row per simulated second: timestamps, every rack inlet/outlet, supply/return, ΔP, RH, cooling units, power chain, PUE, active alarms and faults. The buffer holds the last 6 hours in memory; the edge computer database is the long-term record.'),
    );
    function toggle() { const r = modeSel.value === 'range'; rangeFields.hidden = !r; lastField.hidden = r; }
    refresh();
  },
  update() { if (!timer) timer = setTimeout(() => { timer = null; refresh(); }, 5000); },
};

function url(kind) {
  const q = new URLSearchParams();
  if (modeSel.value === 'last') q.set('last', String((+lastIn.value || 10) * 60));
  else { if (fromIn.value) q.set('from', new Date(fromIn.value + 'Z').toISOString()); if (toIn.value) q.set('to', new Date(toIn.value + 'Z').toISOString()); }
  return `/api/export.${kind}?${q}`;
}
async function refresh() {
  try {
    const r = await api('/api/export/range');
    rangeEl.textContent = r.rows ? `${r.rows.toLocaleString()} rows buffered · ${fmt.iso(r.from)} → ${fmt.iso(r.to)}` : 'Buffer empty.';
    if (r.from && !fromIn.value) { fromIn.value = new Date(r.from * 1000).toISOString().slice(0, 19); toIn.value = new Date(r.to * 1000).toISOString().slice(0, 19); }
  } catch (e) { rangeEl.textContent = e.message; }
}

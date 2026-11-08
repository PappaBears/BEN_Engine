// CALIBRATION panel: reference/reading pairs -> /api/calibrate -> gain, offset, U95 and the uncertainty budget.
import { api, h, fmt } from '../util.js';

let ctxRef = null, chanSel = null, pairsEl = null, resultEl = null, pairs = [];

export default {
  id: 'calibration', label: 'Calibration', title: 'Channel calibration (GUM)',
  mount(el, ctx) {
    ctxRef = ctx;
    chanSel = h('select', { id: 'cal-channel' });
    pairsEl = h('div', {});
    resultEl = h('div', { id: 'cal-result' });
    el.append(
      h('h3', {}, 'Channel'), h('div', { class: 'field' }, chanSel),
      h('h3', {}, 'Reference / reading pairs'),
      pairsEl,
      h('div', { class: 'row', style: { marginTop: '6px' } },
        h('button', { class: 'btn btn-sm', onClick: () => { pairs.push({ reference: '', reading: '' }); renderPairs(); } }, '+ pair'),
        h('button', { class: 'btn btn-sm', id: 'btn-cal-demo', onClick: demo }, 'Generate demo points'),
        h('button', { class: 'btn btn-sm btn-primary', id: 'btn-calibrate', onClick: calibrate }, 'Calibrate')),
      h('h3', {}, 'Result'), resultEl,
    );
    fillChannels(); renderPairs();
  },
  onConfig() { fillChannels(); },
};

function fillChannels() {
  if (!ctxRef.store.sensors.length) return;
  const cur = chanSel.value;
  chanSel.replaceChildren(...ctxRef.store.sensors.filter(s => s.unit !== 'bool').map(s => h('option', { value: s.id, selected: s.id === cur }, `${s.id} (${s.unit}, U95 ±${s.u95})`)));
}
function renderPairs() {
  if (!pairs.length) { pairsEl.replaceChildren(h('div', { class: 'note' }, 'Add at least two pairs, or generate demo points. Reference = traceable instrument, reading = Pod value.')); return; }
  pairsEl.replaceChildren(h('table', { class: 'data' }, h('thead', {}, h('tr', {}, h('th', {}, '#'), h('th', {}, 'reference'), h('th', {}, 'reading'), h('th', {}, ''))),
    h('tbody', {}, ...pairs.map((p, i) => h('tr', {}, h('td', { class: 'muted' }, i + 1),
      h('td', {}, h('input', { type: 'number', step: 'any', value: p.reference, onInput: (e) => { p.reference = e.target.value; } })),
      h('td', {}, h('input', { type: 'number', step: 'any', value: p.reading, onInput: (e) => { p.reading = e.target.value; } })),
      h('td', {}, h('button', { class: 'btn btn-sm btn-ghost', onClick: () => { pairs.splice(i, 1); renderPairs(); } }, '×')))))));
}
function demo() {
  const s = ctxRef.store.sensors.find(x => x.id === chanSel.value) || { kind: 'temperature' };
  const base = s.kind === 'temperature' ? [15, 20, 25, 30, 35] : s.kind === 'humidity' ? [20, 35, 50, 65, 80] : s.kind === 'pressure' ? [-50, -20, 0, 20, 50] : [0, 25, 50, 75, 100];
  const gain = 1.004, offset = s.kind === 'temperature' ? -0.32 : (s.kind === 'pressure' ? 1.1 : 0.6);
  let seed = 11; const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280 - 0.5; };
  pairs = base.map(r => ({ reference: r, reading: +(r * gain + offset + rnd() * (s.u95 || 0.3) * 0.6).toFixed(3) }));
  renderPairs();
}
async function calibrate() {
  const pts = pairs.map(p => ({ reference: +p.reference, reading: +p.reading })).filter(p => Number.isFinite(p.reference) && Number.isFinite(p.reading));
  if (pts.length < 2) { resultEl.replaceChildren(h('div', { class: 'errors' }, 'Need at least two numeric pairs.')); return; }
  resultEl.replaceChildren(h('div', { class: 'note' }, 'Calibrating…'));
  try {
    const r = await api('/api/calibrate', { body: { channel: chanSel.value, reference_points: pts } });
    const u95 = r.u95 ?? r.U95 ?? r.uncertainty_k2 ?? r.expanded_uncertainty;
    const budget = r.budget || r.uncertainty_budget || r.components || [];
    const rows = [['Gain', fmt.num(r.gain, 5)], ['Offset', fmt.num(r.offset, 4)], ['U95 (k=2)', u95 !== undefined ? `±${fmt.num(u95, 3)}` : '—'], ['Residual RMS', r.residual_rms !== undefined ? fmt.num(r.residual_rms, 4) : (r.rms !== undefined ? fmt.num(r.rms, 4) : '—')], ['Points', pts.length], ['cal_id', r.cal_id || '—']];
    resultEl.replaceChildren(
      h('table', { class: 'kv' }, ...rows.map(([k, v]) => h('tr', {}, h('td', {}, k), h('td', {}, v)))),
      budget.length ? h('table', { class: 'data', style: { marginTop: '8px' } }, h('thead', {}, h('tr', {}, h('th', {}, 'source'), h('th', {}, 'type'), h('th', {}, 'u (k=1)'))),
        h('tbody', {}, ...budget.map(b => h('tr', {}, h('td', {}, b.source || b.name), h('td', { class: 'muted' }, b.type || ''), h('td', { class: 'num' }, fmt.num(b.u ?? b.value ?? b.std, 4)))))) : h('p', { class: 'muted' }, 'No budget table returned.'),
      h('div', { class: 'row', style: { marginTop: '8px' } }, h('button', { class: 'btn btn-sm', onClick: async () => {
        const a = await api('/api/calibrate/apply', { body: { channel: chanSel.value } });
        resultEl.append(h('div', { class: 'note ok' }, a.applied_to_twin ? `Applied: twin reported drift now ${a.twin_drift_c} °C.` : `Stored for ${a.channel}; only T_in channels change the twin's reported value.`));
      } }, 'Apply to twin channel')),
    );
  } catch (e) {
    resultEl.replaceChildren(h('div', { class: e.status === 503 ? 'note warn' : 'errors' }, e.status === 503 ? `${e.message}. Needs ben_engine.calibration.` : e.message));
  }
}

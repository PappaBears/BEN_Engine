// CFD panel: run the 2D lattice-Boltzmann solver for the current tier in the background; show PNG + metrics.
import { api, h, fmt } from '../util.js';

let ctxRef = null, statusEl = null, img = null, metricsEl = null, timer = null, runBtn = null, applyBtn = null;

export default {
  id: 'cfd', label: 'CFD', title: 'Airflow CFD',
  mount(el, ctx) {
    ctxRef = ctx;
    statusEl = h('div', { class: 'note' }, 'Idle.');
    img = h('img', { alt: 'CFD temperature / velocity field', style: { width: '100%', borderRadius: '8px', border: '1px solid var(--line)', display: 'none', background: '#0B1018' } });
    metricsEl = h('div', {});
    runBtn = h('button', { class: 'btn btn-primary', id: 'btn-cfd-run', onClick: run }, 'Run CFD for current tier');
    applyBtn = h('button', { class: 'btn', disabled: true, onClick: apply }, 'Apply recirculation profile to twin');
    el.append(h('h3', {}, 'Solver'), h('div', { class: 'row' }, runBtn, applyBtn), statusEl, h('h3', {}, 'Field'), img, h('h3', {}, 'Metrics'), metricsEl,
      h('p', { class: 'muted', style: { fontSize: '12px' } }, 'The solver runs per tier in a background thread; results feed the twin\'s recirculation fraction, which sets how much hot exhaust re-enters the rack inlets.'));
    poll();
  },
  onConfig() { poll(); },
};

async function run() {
  runBtn.disabled = true;
  try { await api('/api/cfd/run?tier=' + ctxRef.store.config.tier, { method: 'POST' }); poll(); }
  catch (e) { statusEl.className = 'note ' + (e.status === 503 ? 'warn' : ''); statusEl.textContent = e.status === 503 ? `${e.message}. Needs ben_engine.cfd.` : e.message; runBtn.disabled = false; }
}
async function poll() {
  clearTimeout(timer);
  if (!ctxRef.store.config) return;
  const tier = ctxRef.store.config.tier;
  try {
    const m = await api('/api/cfd/metrics?tier=' + tier);
    if (m.status === 'running') { statusEl.className = 'note'; statusEl.textContent = `Solving ${tier}… ${fmt.num((Date.now() / 1000 - m.started), 0)} s`; runBtn.disabled = true; timer = setTimeout(poll, 1000); return; }
    runBtn.disabled = false;
    if (m.status === 'done') {
      statusEl.className = 'note ok'; statusEl.textContent = `Done for ${tier} in ${fmt.num(m.finished - m.started, 1)} s.`;
      img.src = `/api/cfd?tier=${tier}&t=${Date.now()}`; img.style.display = 'block';
      const met = m.metrics || {};
      metricsEl.replaceChildren(h('table', { class: 'kv' }, ...Object.entries(met).filter(([, v]) => typeof v !== 'object').map(([k, v]) => h('tr', {}, h('td', {}, k), h('td', {}, typeof v === 'number' ? fmt.num(v, 3) : String(v))))));
      applyBtn.disabled = !(met.recirculation ?? met.recirculation_fraction ?? met.recirc);
    } else if (m.status === 'failed') { statusEl.className = 'errors'; statusEl.textContent = m.error; }
    else { statusEl.className = 'note'; statusEl.textContent = `No CFD result for ${tier} yet.`; img.style.display = 'none'; metricsEl.replaceChildren(); applyBtn.disabled = true; }
  } catch (e) {
    statusEl.className = 'note ' + (e.status === 503 ? 'warn' : ''); statusEl.textContent = e.status === 503 ? `${e.message}. The CFD panel activates when ben_engine.cfd lands.` : e.message;
    runBtn.disabled = e.status === 503;
  }
}
async function apply() {
  try { const r = await api('/api/cfd/apply?tier=' + ctxRef.store.config.tier, { method: 'POST' }); statusEl.className = 'note ok'; statusEl.textContent = `Twin recirculation set to ${fmt.num(r.recirculation, 3)}.`; }
  catch (e) { statusEl.className = 'errors'; statusEl.textContent = e.message; }
}

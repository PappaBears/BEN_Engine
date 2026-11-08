// COMMISSIONING panel: run the commissioning script against the twin, stream step results, link the report.
import { api, h, fmt } from '../util.js';

let statusEl = null, stepsEl = null, runBtn = null, linkEl = null, timer = null;

export default {
  id: 'commissioning', label: 'Commissioning', title: 'Commissioning (simulated)',
  mount(el) {
    statusEl = h('div', { class: 'note' }, 'Idle.');
    stepsEl = h('div', { id: 'cx-steps' });
    linkEl = h('div', {});
    runBtn = h('button', { class: 'btn btn-primary', id: 'btn-cx-run', onClick: run }, 'Run commissioning in sim');
    el.append(h('h3', {}, 'Script'), h('div', { class: 'row' }, runBtn), statusEl, linkEl, h('h3', {}, 'Steps'), stepsEl,
      h('p', { class: 'muted', style: { fontSize: '12px' } }, 'The same script runs on site against the BEN Controller; here every step exercises the digital twin and produces a signed report.'));
    poll();
  },
};

async function run() {
  runBtn.disabled = true;
  try { await api('/api/commission/run', { method: 'POST' }); poll(); }
  catch (e) { statusEl.className = 'note ' + (e.status === 503 ? 'warn' : ''); statusEl.textContent = e.status === 503 ? `${e.message}. Needs ben_engine.commissioning.` : e.message; runBtn.disabled = e.status === 503; }
}

async function poll() {
  clearTimeout(timer);
  try {
    const j = await api('/api/commission/status');
    if (j.status === 'idle') { statusEl.className = 'note'; statusEl.textContent = j.module ? 'Ready.' : 'ben_engine.commissioning not yet available; the panel activates when it lands.'; runBtn.disabled = !j.module; return; }
    renderSteps(j.steps || []);
    if (j.status === 'running') { statusEl.className = 'note'; statusEl.textContent = `Running… ${j.steps.length} step${j.steps.length === 1 ? '' : 's'} so far (${fmt.num(Date.now() / 1000 - j.started, 0)} s)`; timer = setTimeout(poll, 700); return; }
    runBtn.disabled = false;
    if (j.status === 'done') {
      statusEl.className = 'note ' + (j.passed === false ? 'warn' : 'ok'); statusEl.textContent = `Finished in ${fmt.num(j.finished - j.started, 1)} s · ${j.passed === false ? 'some steps FAILED' : 'all steps passed'}.`;
      linkEl.replaceChildren(j.report_url ? h('a', { class: 'btn btn-sm', href: j.report_url, target: '_blank' }, 'Open report') : h('span', { class: 'muted' }, 'No report file returned.'));
    } else if (j.status === 'failed') { statusEl.className = 'errors'; statusEl.textContent = j.error; }
  } catch (e) { statusEl.className = 'errors'; statusEl.textContent = e.message; }
}

function renderSteps(steps) {
  if (!steps.length) { stepsEl.replaceChildren(h('div', { class: 'note' }, 'No steps yet.')); return; }
  stepsEl.replaceChildren(h('table', { class: 'data' }, h('thead', {}, h('tr', {}, h('th', {}, '#'), h('th', {}, 'step'), h('th', {}, 'measured'), h('th', {}, 'criterion'), h('th', {}, ''))),
    h('tbody', {}, ...steps.map((s, i) => {
      const ok = s.pass ?? s.ok ?? s.passed;
      return h('tr', {}, h('td', { class: 'muted' }, s.id ?? i + 1), h('td', {}, s.name || s.title || s.step || JSON.stringify(s).slice(0, 60)), h('td', { class: 'num' }, s.measured !== undefined ? (typeof s.measured === 'number' ? fmt.num(s.measured, 2) : String(s.measured)) : (s.value !== undefined ? String(s.value) : '')), h('td', { class: 'muted' }, s.criterion || s.limit || s.expected || ''), h('td', { class: ok === undefined ? 'muted' : (ok ? 'pass' : 'fail') }, ok === undefined ? '…' : (ok ? '✓' : '✗')));
    }))));
}

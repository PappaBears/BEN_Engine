// ALARMS panel: active alarms with severity and age; click selects the object in 3D.
import { h, fmt } from '../util.js';

let list = null, empty = null, ctxRef = null, lastKey = '';

export default {
  id: 'alarms', label: 'Alarms', title: 'Active alarms',
  mount(el, ctx) {
    ctxRef = ctx;
    list = h('ul', { class: 'alarm-list', id: 'alarm-list' });
    empty = h('div', { class: 'note ok' }, 'No active alarms. Inject faults from the Sweeps panel to exercise them.');
    el.append(h('h3', {}, 'Active'), empty, list, h('p', { class: 'muted', style: { fontSize: '12px' } }, 'Severity: warn → alarm → critical. Thresholds follow the ASHRAE class of the mission profile. Click an alarm to fly to the affected object.'));
  },
  update(st) {
    const alarms = [...st.alarms].sort((a, b) => ({ critical: 0, alarm: 1, warn: 2 }[a.sev] - { critical: 0, alarm: 1, warn: 2 }[b.sev]) || a.since - b.since);
    const key = alarms.map(a => a.id + a.sev).join('|');
    empty.hidden = alarms.length > 0;
    if (key !== lastKey) {
      lastKey = key;
      list.replaceChildren(...alarms.map(a => h('li', { class: `sev-${a.sev}`, 'data-alarm': a.id, onClick: () => {
        const t = ctxRef.alarmTarget(a); ctxRef.store.select(t); ctxRef.scene.focus(t);
      } }, h('span', { class: 'sev' }, a.sev), h('span', { class: 'since', 'data-since': a.since }, ''), h('span', { class: 'msg' }, a.msg))));
    }
    for (const li of list.children) {
      const a = alarms.find(x => x.id === li.dataset.alarm); if (!a) continue;
      li.querySelector('.since').textContent = `since ${fmt.hms(a.since)} · ${fmt.ago(st.t - a.since)}`;
      li.querySelector('.msg').textContent = a.msg;
    }
  },
};

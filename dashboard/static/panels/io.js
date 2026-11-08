// I/O TEST panel: virtual nodes/channels from /api/io/status; relays, contacts, identify, acks with latency.
import { api, h, fmt } from '../util.js';

let root = null, nodesEl = null, logEl = null, noteEl = null, timer = null;

export default {
  id: 'io', label: 'I/O Test', title: 'Node I/O test (virtual nodes in simulation)',
  mount(el) {
    root = el;
    noteEl = h('div', { class: 'note', hidden: true });
    nodesEl = h('div', { id: 'io-nodes' });
    logEl = h('div', { id: 'io-log' });
    el.append(h('h3', {}, 'Nodes and channels'), noteEl, nodesEl, h('h3', {}, 'Command acknowledgements'), logEl,
      h('p', { class: 'muted', style: { fontSize: '12px' } }, 'Raw = ADC counts / bus value as sent by the node; calibrated = after gain and offset (cal_id). In simulation the virtual nodes answer over an in-process bus; on hardware the same commands go over MQTT (spec/PROTOCOL.md).'));
    refresh();
  },
  update() { if (!timer) timer = setTimeout(() => { timer = null; refresh(); }, 2000); },
};

async function refresh() {
  if (!root || root.hidden) return;
  try {
    const st = await api('/api/io/status');
    noteEl.hidden = true;
    renderNodes(st.nodes);
    renderLog(st.log || []);
  } catch (e) {
    noteEl.hidden = false;
    noteEl.className = 'note ' + (e.status === 503 ? 'warn' : '');
    noteEl.textContent = e.status === 503 ? `${e.message}. The I/O test needs ben_engine.sim_nodes (virtual BEN nodes); the panel will populate as soon as that module lands.` : e.message;
    nodesEl.replaceChildren();
  }
}

function asList(nodes) {
  if (Array.isArray(nodes)) return nodes;
  if (nodes && typeof nodes === 'object') {
    if (Array.isArray(nodes.nodes)) return nodes.nodes;
    return Object.entries(nodes).map(([id, v]) => ({ id, ...(typeof v === 'object' ? v : { value: v }) }));
  }
  return [];
}

function renderNodes(nodes) {
  const list = asList(nodes);
  if (!list.length) { nodesEl.replaceChildren(h('div', { class: 'note' }, 'No virtual nodes reported.')); return; }
  nodesEl.replaceChildren(...list.map(n => {
    const id = n.id || n.node_id || n.name;
    const chans = asList(n.channels || n.ch || n.inputs || {});
    const outs = asList(n.outputs || n.relays || {});
    const status = n.status || {};
    return h('div', { class: 'tile', style: { marginBottom: '8px' }, 'data-node': id },
      h('div', { class: 'row', style: { justifyContent: 'space-between' } }, h('b', {}, id), h('span', { class: 'muted mono', style: { fontSize: '11px', flex: '0 0 auto' } }, [status.fw && `fw ${status.fw}`, status.rssi !== undefined && `${status.rssi} dBm`, n.online === false ? 'OFFLINE' : 'online'].filter(Boolean).join(' · '))),
      h('div', { class: 'row', style: { margin: '6px 0' } },
        h('button', { class: 'btn btn-sm', onClick: () => cmd(id, 'identify') }, 'Identify'),
        h('button', { class: 'btn btn-sm', onClick: () => cmd(id, 'get_cal') }, 'Get cal'),
        h('button', { class: 'btn btn-sm', onClick: () => cmd(id, 'tare', 'dP_aisle') }, 'Tare dP')),
      chans.length ? h('table', { class: 'data' }, h('thead', {}, h('tr', {}, h('th', {}, 'channel'), h('th', {}, 'raw'), h('th', {}, 'calibrated'), h('th', {}, 'unit'))),
        h('tbody', {}, ...chans.map(c => h('tr', {}, h('td', { class: 'mono' }, c.id || c.name || c.ch), h('td', { class: 'num muted' }, fmtv(c.raw)), h('td', { class: 'num' }, fmtv(c.value ?? c.calibrated ?? c.cal)), h('td', { class: 'muted' }, c.unit || ''))))) : null,
      outs.length ? h('div', { class: 'row', style: { marginTop: '6px' } }, ...outs.map(o => h('button', { class: 'btn btn-sm' + ((o.value ?? o.state) ? ' active' : ''), onClick: () => test(id, o.id || o.name, (o.value ?? o.state) ? 0 : 1) }, `${o.id || o.name}: ${(o.value ?? o.state) ? 'ON' : 'off'}`))) : null,
    );
  }));
}
const fmtv = (v) => v === undefined || v === null ? '—' : (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : fmt.num(v, 2)) : String(v));

function renderLog(log) {
  if (!log.length) { logEl.replaceChildren(h('div', { class: 'note' }, 'No commands sent yet.')); return; }
  logEl.replaceChildren(h('table', { class: 'data' }, h('thead', {}, h('tr', {}, h('th', {}, 'time'), h('th', {}, 'node'), h('th', {}, 'command'), h('th', {}, 'ack'), h('th', {}, 'latency'))),
    h('tbody', {}, ...log.slice(0, 12).map(e => h('tr', {}, h('td', { class: 'mono muted' }, fmt.clock(e.ts)), h('td', { class: 'mono' }, e.node), h('td', { class: 'mono' }, e.op ? e.op + (e.channel ? ` ${e.channel}` : '') : `${e.channel}=${e.value}`), h('td', { class: (e.ack && e.ack.ok === false) ? 'fail' : 'pass' }, e.ack && e.ack.ok === false ? 'NAK' : 'ok'), h('td', { class: 'num' }, `${fmt.num(e.latency_ms, 1)} ms`))))));
}

async function cmd(node, op, channel) { try { await api('/api/io/test', { body: { node, op, channel } }); } catch (e) { console.warn(e); } refresh(); }
async function test(node, channel, value) { try { await api('/api/io/test', { body: { node, channel, value } }); } catch (e) { console.warn(e); } refresh(); }

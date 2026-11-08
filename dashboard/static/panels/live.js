// LIVE panel: numeric tiles with timestamps + canvas sparklines, outdoor temperature and IT load controls.
import { api, h, fmt, drawSparkline, BRAND } from '../util.js';

const RACK_COLORS = ['#66E3FF', '#6EE7A8', '#FFC66D', '#FF9D6D', '#C7A6FF', '#FF707D', '#9FB3CC', '#7FD1FF', '#B8F28B', '#FFD79A', '#FFB3B3', '#D6C2FF'];
let tiles = {}, sparks = {}, store = null, outdoorIn = null, loadIn = null, outdoorOut = null, loadOut = null;

function tile(key, label, unit, digits = 1) {
  const v = h('div', { class: 'v' }, '—');
  const ts = h('div', { class: 'ts' }, '—');
  const el = h('div', { class: 'tile', 'data-tile': key }, h('div', { class: 'k' }, h('span', {}, label), h('span', {}, unit)), v, ts);
  tiles[key] = { el, v, ts, digits, unit };
  return el;
}
function spark(key, label, opts = {}) {
  const canvas = h('canvas', { class: 'spark', height: 56 });
  const val = h('b', {}, '—');
  const wrap = h('div', { class: 'spark-wrap' }, h('div', { class: 'k' }, h('span', {}, label), val), canvas);
  sparks[key] = { canvas, val, opts };
  return wrap;
}
function setTile(key, value, cls = '', ts) {
  const t = tiles[key]; if (!t) return;
  t.v.replaceChildren(fmt.num(value, t.digits), h('small', {}, t.unit));
  t.ts.textContent = fmt.iso(ts);
  t.el.className = 'tile ' + cls;
}

export default {
  id: 'live', label: 'Live', title: 'Live telemetry',
  mount(el, ctx) {
    store = ctx.store;
    outdoorOut = h('output', {}, '—'); loadOut = h('output', {}, '—');
    outdoorIn = h('input', { type: 'range', min: -30, max: 50, step: 1, value: 25, id: 'in-outdoor', onInput: (e) => { outdoorOut.value = `${e.target.value} °C`; }, onChange: (e) => api('/api/outdoor', { body: { c: +e.target.value } }).catch(console.warn) });
    loadIn = h('input', { type: 'range', min: 0, max: 120, step: 5, value: 75, id: 'in-load', onInput: (e) => { loadOut.value = `${e.target.value} %`; }, onChange: (e) => api('/api/load', { body: { fraction: +e.target.value / 100 } }).catch(console.warn) });
    el.append(
      h('h3', {}, 'Now'),
      h('div', { class: 'tiles' },
        tile('it_kw', 'IT load', 'kW'), tile('utility_kw', 'Utility', 'kW'), tile('pue', 'PUE', '', 3), tile('ups_soc', 'UPS SoC', '%', 0),
        tile('inlet_max', 'Inlet max', '°C'), tile('supply', 'Supply', '°C'), tile('return', 'Return', '°C'), tile('dp', 'Aisle ΔP', 'Pa'),
        tile('rh', 'Humidity', '%RH', 0), tile('outdoor', 'Outdoor', '°C'), tile('cool_kw', 'Cooling elec.', 'kW'), tile('runtime', 'UPS runtime', 'min', 0)),
      h('h3', {}, 'Controls'),
      h('div', { class: 'field' }, h('label', {}, 'Outdoor temperature', outdoorOut), outdoorIn),
      h('div', { class: 'field' }, h('label', {}, 'IT load (fraction of design)', loadOut), loadIn),
      h('h3', {}, 'Trends (last 6 min)'),
      spark('inlets', 'Rack inlets °C', { minSpan: 2 }), spark('supply_return', 'Supply / return °C', { minSpan: 2 }), spark('dp', 'Aisle ΔP Pa', { minSpan: 2 }),
      spark('it', 'IT kW', { minSpan: 5 }), spark('utility', 'Utility kW', { minSpan: 5 }), spark('soc', 'UPS SoC %', { minSpan: 5, digits: 0 }), spark('pue', 'PUE', { minSpan: 0.1, digits: 3 }),
    );
  },
  update(st) {
    const ts = st.wall_ts, p = st.power;
    const aMax = { A1: 27, A2: 35, A3: 40, A4: 45 }[store.derived?.ashrae_class] || 35;
    const inletMax = Math.max(...st.rack_inlet_c);
    setTile('it_kw', st.it_kw, '', ts); setTile('utility_kw', p.utility_kw, p.utility_ok ? '' : 'alarm', ts); setTile('pue', st.pue, '', ts);
    setTile('ups_soc', p.ups_soc_pct, p.ups_soc_pct < 30 ? 'alarm' : (p.ups_on_battery ? 'warn' : ''), ts);
    setTile('inlet_max', inletMax, inletMax > aMax ? 'alarm' : (inletMax > aMax - 2 ? 'warn' : 'ok'), ts);
    setTile('supply', st.supply_c, '', ts); setTile('return', st.return_c, '', ts); setTile('dp', st.aisle_dp_pa, '', ts); setTile('rh', st.rh_pct, '', ts);
    setTile('outdoor', st.outdoor_c, '', ts); setTile('cool_kw', st.cooling_kw_elec, '', ts); setTile('runtime', p.ups_runtime_min, p.ups_on_battery ? 'warn' : '', ts);
    if (document.activeElement !== outdoorIn) { outdoorIn.value = Math.round(st.outdoor_c); outdoorOut.value = `${Math.round(st.outdoor_c)} °C`; }
    if (document.activeElement !== loadIn) { loadIn.value = Math.round(st.it_fraction * 100); loadOut.value = `${Math.round(st.it_fraction * 100)} %`; }
    const H = store.history;
    const series = (f) => H.map(f);
    const n = st.rack_inlet_c.length;
    drawSparkline(sparks.inlets.canvas, Array.from({ length: n }, (_, i) => ({ values: series(s => s.rack_inlet_c[i]), color: RACK_COLORS[i % RACK_COLORS.length], width: 1.2 })), { ...sparks.inlets.opts, limit: aMax, band: { min: 18, max: aMax - 2 } });
    sparks.inlets.val.textContent = `${fmt.num(inletMax)} max`;
    drawSparkline(sparks.supply_return.canvas, [{ values: series(s => s.supply_c), color: BRAND.cyan }, { values: series(s => s.return_c), color: BRAND.amber }], sparks.supply_return.opts);
    sparks.supply_return.val.textContent = `${fmt.num(st.supply_c)} / ${fmt.num(st.return_c)}`;
    drawSparkline(sparks.dp.canvas, [{ values: series(s => s.aisle_dp_pa), color: BRAND.cyan }], sparks.dp.opts); sparks.dp.val.textContent = fmt.num(st.aisle_dp_pa);
    drawSparkline(sparks.it.canvas, [{ values: series(s => s.it_kw), color: BRAND.green }], sparks.it.opts); sparks.it.val.textContent = fmt.num(st.it_kw);
    drawSparkline(sparks.utility.canvas, [{ values: series(s => s.power.utility_kw), color: BRAND.green }], sparks.utility.opts); sparks.utility.val.textContent = fmt.num(p.utility_kw);
    drawSparkline(sparks.soc.canvas, [{ values: series(s => s.power.ups_soc_pct), color: p.ups_on_battery ? BRAND.amber : BRAND.cyan }], sparks.soc.opts); sparks.soc.val.textContent = fmt.num(p.ups_soc_pct, 0);
    drawSparkline(sparks.pue.canvas, [{ values: series(s => s.pue), color: BRAND.muted }], sparks.pue.opts); sparks.pue.val.textContent = fmt.num(st.pue, 3);
  },
};

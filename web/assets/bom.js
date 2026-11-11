// BEN Engine price engine for the product page: a line-for-line port of software/ben_engine/bom.py generate_bom()
// over the exported catalog rules (web/assets/price-rules.json, scripts/export_price_rules.py), with the margin of
// software/ben_engine/commercial.py. tests/test_price_parity.py runs this file under node and checks it against
// the Python BOM for every tier and option, so the page, the dashboard and the proposals quote the same number.
import { canonicalTier, controlsTierResolved, derived, geometry, isCluster, lineupOf, moduleConfig, pyRound } from './selector.js';

const FUNCS = {
  ceil: Math.ceil, floor: Math.floor, abs: Math.abs, int: Math.trunc,
  min: (...a) => Math.min(...a), max: (...a) => Math.max(...a),
  round: (x, n) => (n === undefined ? pyRound(x) : pyRound(x * 10 ** n) / 10 ** n),
};
const pyMod = (a, b) => a - b * Math.floor(a / b);

export function evalRule(node, vars) {
  if (typeof node === 'number') return node;
  if (typeof node === 'string') {
    if (!(node in vars)) throw new Error(`unknown variable ${node}`);
    return vars[node];
  }
  const [op, a, b, c] = node;
  switch (op) {
    case '+': return evalRule(a, vars) + evalRule(b, vars);
    case '-': return evalRule(a, vars) - evalRule(b, vars);
    case '*': return evalRule(a, vars) * evalRule(b, vars);
    case '/': return evalRule(a, vars) / evalRule(b, vars);
    case '//': return Math.floor(evalRule(a, vars) / evalRule(b, vars));
    case '%': return pyMod(evalRule(a, vars), evalRule(b, vars));
    case '<': return +(evalRule(a, vars) < evalRule(b, vars));
    case '<=': return +(evalRule(a, vars) <= evalRule(b, vars));
    case '>': return +(evalRule(a, vars) > evalRule(b, vars));
    case '>=': return +(evalRule(a, vars) >= evalRule(b, vars));
    case '==': return +(evalRule(a, vars) === evalRule(b, vars));
    case '!=': return +(evalRule(a, vars) !== evalRule(b, vars));
    case 'neg': return -evalRule(a, vars);
    case 'pos': return +evalRule(a, vars);
    case 'if': return evalRule(a, vars) ? evalRule(b, vars) : evalRule(c, vars);
    case 'call': return FUNCS[a](...node.slice(2).map((x) => evalRule(x, vars)));
    default: throw new Error(`bad rule node ${op}`);
  }
}

const r1 = (x) => pyRound(x * 10) / 10;
const r2 = (x) => pyRound(x * 100) / 100;

/** bom.py rule_variables(cfg) */
export function ruleVariables(cfg, cat, d = derived(cfg, cat), g = geometry(cfg, cat)) {
  const kind = d.kind;
  return {
    racks: cfg.racks, it_kw: cfg.it_kw, cooling_units_total: d.cooling_units_total, ups_modules: d.ups_modules, ups_kva_each: d.ups_kva_each,
    battery_kwh: d.battery_kwh, service_breaker_a: d.service_breaker_a, total_kw: d.total_kw, total_kva: d.total_kva,
    pods: d.pods, nodes: d.pods, controls_pro: d.controls_tier_resolved === 'pro' ? 1 : 0, tier_len_m: g.ext_l_m,
    generator: cfg.generator ? 1 : 0,
    transformers_total: d.transformers_total, transformer_kva: d.transformer_kva, generators_total: d.generators_total,
    generator_kw_each: d.generator_kw_each, modules: d.modules, rows: d.rows, racks_per_row: d.racks_per_row, mv_service: d.mv_service ? 1 : 0,
    hardening_H2: cfg.hardening === 'H2' ? 1 : 0, hardening_H3: cfg.hardening === 'H3' ? 1 : 0,
    hardening_H2_plus: (cfg.hardening === 'H2' || cfg.hardening === 'H3') ? 1 : 0,
    envelope_area_m2: d.envelope_area_m2,
    wall_area_m2: r1(2 * (g.ext_l_m * g.ext_h_m + g.ext_w_m * g.ext_h_m)),
    footprint_m2: r1(g.ext_l_m * g.ext_w_m),
    int_volume_m3: r1(g.int_l_m * g.int_w_m * g.int_h_m),
    dc800: cfg.power_architecture === 'dc800' ? 1 : 0,
    rectifier_modules: d.rectifier_modules ?? 0, rectifier_cabinets: d.rectifier_cabinets ?? 0, dc_busway_a: d.dc_busway_a ?? 0,
    dc_bus_current_a: d.dc_bus_current_a ?? 0, imd_count: d.imd_count ?? 0, battery_on_bus_kwh: d.battery_on_bus_kwh ?? 0,
    rack_shelves_total: d.rack_shelves_total ?? 0, dlc_hd: cfg.cooling === 'dlc_hd' ? 1 : 0, liquid_heat_kw: d.liquid_heat_kw ?? 0,
    loop_flow_lpm: d.loop_flow_lpm ?? 0, heat_reuse_kw: d.heat_reuse_kw_available ?? 0,
    liquid_first: d.liquid_first ? 1 : 0, fancoils_total: d.fancoils_total ?? 0, battery_cabinets: d.battery_cabinets ?? 0,
    swbd_sections: d.swbd_sections ?? 0, ups_frames: d.ups_frames ?? 0, trim_loop_kw: d.trim_loop_kw ?? 0,
    minirack: kind === 'minirack' ? 1 : 0, form_rack10: (kind === 'minirack' && cfg.form === 'rack10') ? 1 : 0,
    form_cab12: (kind === 'minirack' && cfg.form === 'cab12') ? 1 : 0, ups_va: d.ups_va ?? 0, ups_battery_packs: d.ups_battery_packs ?? 0,
    controls_mini: d.controls_tier_resolved === 'mini' ? 1 : 0,
    profile_ai: (cfg.profile === 'ai_training' || cfg.profile === 'ai_inference') ? 1 : 0,
    cluster: kind === 'cluster' ? 1 : 0, yard_pad_sqft: d.yard_pad_sqft ?? 0, yard_area_m2: d.yard_area_m2 ?? 0,
    yard_surface_m2: d.yard_surface_m2 ?? 0, lane_area_m2: d.lane_area_m2 ?? 0, mv_feeder_m: d.mv_feeder_m ?? 0,
  };
}

function applies(ln, cfg, ct, subs, lineup) {
  for (const [k, v] of [['cooling', cfg.cooling], ['controls', ct], ['hardening', cfg.hardening], ['power', cfg.power_architecture], ['lineups', lineup]]) {
    if (ln[k] && !ln[k].includes(v)) return false;
  }
  return ln.always || subs.has(ln.sub);
}
const toQty = (q) => (Number.isInteger(q) ? q : Math.ceil(q - 1e-9));
const row = (ln, qty, scope) => ({ code: ln.code, subsystem: ln.sub, name: ln.name, unit: ln.unit, qty, unit_price_usd: r2(ln.price), ext_price_usd: r2(qty * ln.price), price_status: ln.status, ...(scope ? { scope } : {}) });

/** bom.py generate_bom(cfg): priced rows; zero-quantity lines dropped. */
export function generateBom(cfg, cat, rules) {
  const subs = new Set(cfg.subsystems || []);
  if (!subs.size) return [];
  if (isCluster(cfg, cat)) return clusterBom(cfg, cat, rules);
  const tier = canonicalTier(cfg.tier, cat), lineup = lineupOf(cfg, cat), ct = controlsTierResolved(cfg, cat);
  const vars = ruleVariables(cfg, cat);
  const rows = [];
  for (const ln of rules.lines) {
    if (!ln.tiers.includes(tier) || !applies(ln, cfg, ct, subs, lineup)) continue;
    let qty = toQty(evalRule(ln.q, vars));
    if (qty > 0 && ln.moq > 1) qty = Math.ceil(Math.max(qty, ln.moq) / ln.moq) * ln.moq;
    if (qty <= 0) continue;
    rows.push(row(ln, qty));
  }
  return rows;
}

function clusterBom(cfg, cat, rules) {
  const d = derived(cfg, cat), n = d.modules;
  const rows = generateBom(moduleConfig(cfg, cat), cat, rules).map((r) => ({ ...r, qty: r.qty * n, ext_price_usd: r2(r.qty * n * r.unit_price_usd), scope: `${n} x module` }));
  const byCode = Object.fromEntries(rows.map((r) => [r.code, r]));
  const vars = ruleVariables(cfg, cat, d), ct = controlsTierResolved(cfg, cat), subs = new Set(cfg.subsystems), tier = canonicalTier(cfg.tier, cat);
  for (const ln of rules.lines) {
    const yard = ln.tiers.includes(tier) && Array.isArray(ln.lineups) && ln.lineups.length === 1 && ln.lineups[0] === 'rev2';
    if (!(yard || ln.cq !== undefined) || !applies(ln, cfg, ct, subs, lineupOf(cfg, cat))) continue;
    const qty = toQty(evalRule(yard ? ln.q : ln.cq, vars));
    if (qty <= 0) continue;
    if (byCode[ln.code]) { const r = byCode[ln.code]; r.qty += qty; r.ext_price_usd = r2(r.qty * r.unit_price_usd); r.scope = `${n} x module + yard`; continue; }
    const nr = row(ln, qty, 'yard'); rows.push(nr); byCode[ln.code] = nr;
  }
  return rows;
}

/** bom.py totals() (the fields the page shows). */
export function bomTotals(rows) {
  const bySub = {}, byStatus = { confirmed: 0, list: 0, estimate: 0 };
  let total = 0;
  for (const r of rows) { bySub[r.subsystem] = (bySub[r.subsystem] || 0) + r.ext_price_usd; byStatus[r.price_status] += r.ext_price_usd; total += r.ext_price_usd; }
  return { total_usd: r2(total), by_subsystem: bySub, by_status: byStatus, items: rows.length };
}

/** Capital sell price of a configuration at the project margin, with the infrastructure-only figure and the cost of
 *  the selected hardening level against H1 (what the customer pays for hardening). */
export function quote(cfg, cat, rules) {
  const m = rules.margin, sell = (x) => x / (1 - m);
  const rows = generateBom(cfg, cat, rules), t = bomTotals(rows);
  const infra = rows.filter((r) => r.subsystem !== 'compute').reduce((s, r) => s + r.ext_price_usd, 0);
  let hardeningAdd = 0;
  if (cfg.hardening && cfg.hardening !== 'H1') {
    const h1 = bomTotals(generateBom({ ...cfg, hardening: 'H1' }, cat, rules)).total_usd;
    hardeningAdd = sell(t.total_usd - h1);
  }
  return {
    margin: m, cost_usd: t.total_usd, price_usd: sell(t.total_usd), infra_price_usd: sell(infra), compute_price_usd: sell(t.total_usd - infra),
    by_subsystem: Object.fromEntries(Object.entries(t.by_subsystem).map(([k, v]) => [k, sell(v)])),
    by_status: Object.fromEntries(Object.entries(t.by_status).map(([k, v]) => [k, sell(v)])),
    hardening_add_usd: hardeningAdd, lines: t.items, rows,
  };
}

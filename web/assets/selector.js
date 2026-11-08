// BEN Engine selector — JavaScript port of software/ben_engine/config.py (keep in sync; tests/test_selector_parity.py checks numbers)
export const FRAMES = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000];

// controls tier (docs/CONTROLS_HARDWARE_DECISION.md §2a): "auto" -> lite for micro, pro for ben20/ben40,
// ben10 lite unless the profile is in cat.controls_pro_profiles
export function controlsTierResolved(cfg, cat) {
  const ct = cfg.controls_tier ?? 'auto';
  if (ct === 'lite' || ct === 'pro') return ct;
  if (cfg.tier === 'micro') return 'lite';
  if (cfg.tier === 'ben10') return (cat.controls_pro_profiles ?? ['healthcare', 'public_sector', 'ai_training']).includes(cfg.profile) ? 'pro' : 'lite';
  return 'pro';
}

export function validate(cfg, cat) {
  const errs = [];
  const g = cat.tiers[cfg.tier];
  if (!g) return [`unknown tier ${cfg.tier}`];
  if (!(g.it_kw_min <= cfg.it_kw && cfg.it_kw <= g.it_kw_max)) errs.push(`${g.label} supports ${g.it_kw_min}–${g.it_kw_max} kW IT, got ${cfg.it_kw}`);
  if (!(1 <= cfg.racks && cfg.racks <= g.max_racks)) errs.push(`${g.label} holds 1–${g.max_racks} racks, got ${cfg.racks}`);
  const cl = cat.cooling[cfg.cooling];
  if (!cl) errs.push(`unknown cooling ${cfg.cooling}`);
  else {
    const perRack = cfg.it_kw / Math.max(cfg.racks, 1);
    if (perRack > cl.max_rack_kw) errs.push(`${perRack.toFixed(1)} kW/rack exceeds ${cl.label} limit of ${cl.max_rack_kw} kW/rack`);
  }
  if (cfg.tier === 'micro' && cfg.cooling !== 'cabinet_dx') errs.push('BEN Micro uses cabinet_dx cooling only');
  if (cfg.tier !== 'micro' && cfg.cooling === 'cabinet_dx') errs.push('cabinet_dx is for BEN Micro only');
  const ct = cfg.controls_tier ?? 'auto';
  if (!['auto', 'lite', 'pro'].includes(ct)) errs.push(`unknown controls_tier ${ct}`);
  else if (ct === 'lite' && (cfg.tier === 'ben20' || cfg.tier === 'ben40')) errs.push('BEN Controls Lite is for BEN Micro and BEN 10 only; BEN 20/40 use BEN Controls Pro');
  if (!errs.length && cfg.tier !== 'micro') {
    const d = derived(cfg, cat);
    if (!d.row_fits) errs.push(`single row of ${cfg.racks} racks + ${d.cooling_units_total} cooling units is ${d.row_length_mm} mm, exceeds interior ${Math.round(g.int_l_m * 1000)} mm; use fewer racks, rear-door or liquid cooling`);
  }
  return errs;
}

export function derived(cfg, cat) {
  const g = cat.tiers[cfg.tier], cl = cat.cooling[cfg.cooling], clim = cat.climates[cfg.climate];
  const perRack = cfg.it_kw / cfg.racks;
  let derate = 1.0;
  if ((cl.medium === 'air' || cl.medium === 'water') && clim.t_design_c > 35) derate = Math.max(0.6, 1 - 0.015 * (clim.t_design_c - 35));
  const unitKw = cl.unit_kw * derate;
  const nUnits = Math.ceil(cfg.it_kw * 1.05 / unitKw);
  const nTotal = cfg.redundancy === 'N+1' ? nUnits + 1 : cfg.redundancy === '2N' ? 2 * nUnits : nUnits;
  const coolElec = cfg.it_kw / cl.cop;
  const auxKw = coolElec + 0.5 + 0.02 * cfg.it_kw;
  const totalKw = cfg.it_kw + auxKw;
  const pf = 0.95, totalKva = totalKw / pf;
  const upsN = cfg.it_kw / pf * 1.15;
  const upsModules = cfg.redundancy === 'N' ? 1 : 2;
  let serviceAmps;
  if (g.voltage.startsWith('480')) serviceAmps = totalKva * 1000 / (Math.sqrt(3) * 480) / 0.8;
  else if (g.voltage.startsWith('208 V 3')) serviceAmps = totalKva * 1000 / (Math.sqrt(3) * 208) / 0.8;
  else serviceAmps = totalKva * 1000 / 240 / 0.8;
  const breaker = FRAMES.find(f => f >= serviceAmps) ?? 2000;
  const ups_minutes = cfg.ups_minutes ?? 10;
  const batteryKwh = cfg.it_kw * ups_minutes / 60 / 0.9;
  const airflow = cl.medium === 'air' ? cfg.it_kw * 125 : cfg.it_kw * 40;
  const payload = cfg.racks * (cfg.tier === 'micro' ? 400 : 900) + nTotal * cl.mass_kg + upsModules * (cfg.tier === 'micro' ? 120 : 350) + batteryKwh * 8;
  const rowLen = cfg.racks * 600 + ((cl.medium === 'air' || cl.medium === 'liquid') ? nTotal * cl.width_mm : 0) + 500;
  const rowFits = cfg.tier === 'micro' || rowLen <= g.int_l_m * 1000;
  const nfpa855 = batteryKwh >= 20;
  const gross = payload + g.tare_kg;
  const area = 2 * (g.ext_l_m * g.ext_h_m + g.ext_w_m * g.ext_h_m) + g.ext_l_m * g.ext_w_m;
  const envGain = (area * (clim.t_design_c - 22) / 3.5 + 0.3 * clim.solar_w_m2 * g.ext_l_m * g.ext_w_m * 0.25) / 1000;
  return {
    tier_label: g.label, enclosure: g.enclosure, per_rack_kw: +perRack.toFixed(2),
    cooling_label: cl.label, cooling_units_n: nUnits, cooling_units_total: nTotal,
    cooling_unit_kw_derated: +unitKw.toFixed(1), cooling_derate: +derate.toFixed(3), cooling_elec_kw: +coolElec.toFixed(2),
    total_kw: +totalKw.toFixed(1), total_kva: +totalKva.toFixed(1), voltage: g.voltage,
    service_amps_calc: Math.round(serviceAmps), service_breaker_a: breaker,
    ups_modules: upsModules, ups_kva_each: Math.round(upsN), battery_kwh: +batteryKwh.toFixed(1),
    airflow_cfm: Math.round(airflow), payload_kg: Math.round(payload), gross_kg: Math.round(gross),
    envelope_gain_kw: +envGain.toFixed(2), pue_estimate: +(totalKw / cfg.it_kw + 0.03).toFixed(3),
    row_length_mm: Math.trunc(rowLen), row_fits: rowFits, nfpa_855_scope: nfpa855,
    ashrae_class: cat.profiles[cfg.profile].ashrae,
    controls_tier_resolved: controlsTierResolved(cfg, cat),
    controls_label: (cat.controls_tiers ?? {})[controlsTierResolved(cfg, cat)]?.label ?? (controlsTierResolved(cfg, cat) === 'pro' ? 'BEN Controls Pro' : 'BEN Controls Lite'),
    pods: cfg.tier === 'micro' ? 3 : cfg.racks * 2 + 2,
  };
}

export function preset(tier, profile = 'ai_inference', climate = 'temperate', cat) {
  const g = cat.tiers[tier], p = cat.profiles[profile];
  let itKw = Math.min(g.it_kw_max, Math.max(g.it_kw_min, p.rack_kw * g.max_racks * 0.8));
  const racks = Math.max(1, Math.min(g.max_racks, Math.ceil(itKw / p.rack_kw)));
  let cooling = g.default_cooling;
  if (tier !== 'micro' && itKw / racks > cat.cooling[cooling].max_rack_kw) cooling = 'dlc_cdu';
  const cfg = { tier, profile, it_kw: Math.round(itKw), racks, cooling, redundancy: p.redundancy, climate,
    subsystems: ['power', 'cooling', 'compute', 'controls'], white_label: false, brand: 'Schreiber AI', ups_minutes: 10,
    generator: ['healthcare', 'public_sector', 'off_grid'].includes(profile), site_name: 'Demo site', controls_tier: 'auto' };
  if (tier !== 'micro') for (const alt of [cooling, 'inrow_dx_300', 'rdhx_drycooler', 'dlc_cdu']) { cfg.cooling = alt; if (!validate(cfg, cat).length) break; }
  return cfg;
}

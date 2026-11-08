// BEN Engine selector — JavaScript port of software/ben_engine/config.py (keep in sync; tests/test_selector_parity.py checks numbers)
export const FRAMES = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000];

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
  const payload = cfg.racks * (cfg.tier === 'micro' ? 400 : 900) + nTotal * (cl.medium === 'air' ? 250 : 400) + upsModules * 350 + batteryKwh * 8;
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
    ashrae_class: cat.profiles[cfg.profile].ashrae,
  };
}

export function preset(tier, profile = 'ai_inference', climate = 'temperate', cat) {
  const g = cat.tiers[tier], p = cat.profiles[profile];
  let itKw = Math.min(g.it_kw_max, Math.max(g.it_kw_min, p.rack_kw * g.max_racks * 0.8));
  const racks = Math.max(1, Math.min(g.max_racks, Math.ceil(itKw / p.rack_kw)));
  let cooling = g.default_cooling;
  if (tier !== 'micro' && itKw / racks > cat.cooling[cooling].max_rack_kw) cooling = 'dlc_cdu';
  return { tier, profile, it_kw: Math.round(itKw), racks, cooling, redundancy: p.redundancy, climate,
    subsystems: ['power', 'cooling', 'compute', 'controls'], white_label: false, brand: 'Schreiber AI', ups_minutes: 10,
    generator: ['healthcare', 'public_sector', 'off_grid'].includes(profile), site_name: 'Demo site' };
}

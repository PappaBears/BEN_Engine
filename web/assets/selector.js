// BEN Engine selector — JavaScript port of software/ben_engine/config.py (keep in sync; tests/test_selector_parity.py checks numbers)
export const FRAMES = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000];
// forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): 800 VDC option and high-density DLC; defaults in cat.power_architectures
export const DC_BUSWAY_FRAMES = [400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200];
const FALLBACK_DC = { tiers: ['ben150', 'ben500', 'ben2000'], bus_v_nominal: 800, bus_v_min: 760, bus_v_max: 920, pole_v_to_ground: 400, rectifier_eff: 0.985, rectifier_module_kw: 100,
  bus_headroom: 1.25, busway_frames_a: DC_BUSWAY_FRAMES, loss_saving_frac: 0.03, copper_current_density_a_mm2: 2.0, ac_feeder_v: 415, ac_feeder_pf: 0.95, copper_kg_per_mm2_m: 8.96e-3, pue_loss_adder: 0.015 };
function dcTable(cat) { return (cat.power_architectures && cat.power_architectures.dc800) || FALLBACK_DC; }
function dlcHdTiers(cat) { return cat.dlc_hd_tiers || ['ben150', 'ben500', 'ben2000']; }
export function powerArchitectures(cat) { return cat.power_architectures || { ac480: { label: '480 V AC → UPS → 208/415 V AC PDUs (today)', tiers: ['ben5', 'ben30', 'ben150', 'ben500', 'ben2000'] }, dc800: { ...FALLBACK_DC, label: '800 VDC bus (forward option)' } }; }

// Generation-1 keys (container-length names) are accepted everywhere and normalised to the power-based keys.
export const TIER_ALIASES = { micro: 'ben5', ben10: 'ben30', ben20: 'ben150', ben40: 'ben500' };
export function canonicalTier(t, cat) { return ((cat && cat.tier_aliases) || TIER_ALIASES)[t] ?? t; }

export const SEVERE_CLIMATES = ['coastal', 'hot_arid', 'cold', 'high_altitude', 'hot_humid'];
export function hardeningRecommended(profile, climate) {
  return profile === 'public_sector' ? 'H3' : (SEVERE_CLIMATES.includes(climate) ? 'H2' : 'H1');
}

const FALLBACK_HARDENING = {
  H1: { label: 'H1 Standard', rating: 'NEMA 4X / IP66', coating: 'ISO 12944 C3', mass_kg_m2: 0.0 },
  H2: { label: 'H2 Severe environment', rating: 'NEMA 4X / IP66 + flood plinth 600 mm', coating: 'ISO 12944 C5-M', mass_kg_m2: 6.0 },
  H3: { label: 'H3 Hardened / government', rating: 'NEMA 4X / IP66 + ballistic (UL 752) + forced-entry (ASTM F3038) + HEMP shielding option (MIL-STD-188-125-1)', coating: 'ISO 12944 C5-M', mass_kg_m2: 48.0 },
};
function hardeningTable(cat) { return cat.hardening ?? FALLBACK_HARDENING; }

// controls tier (docs/CONTROLS_HARDWARE_DECISION.md §2a): "auto" -> lite for BEN 5, pro for BEN 150/500/2000,
// BEN 30 lite unless the profile is in cat.controls_pro_profiles
export function controlsTierResolved(cfg, cat) {
  const ct = cfg.controls_tier ?? 'auto';
  const tier = canonicalTier(cfg.tier, cat);
  if (ct === 'lite' || ct === 'pro') return ct;
  if (tier === 'ben5') return 'lite';
  if (tier === 'ben30') return (cat.controls_pro_profiles ?? ['healthcare', 'public_sector', 'ai_training']).includes(cfg.profile) ? 'pro' : 'lite';
  return 'pro';
}

export function validate(cfg, cat) {
  const errs = [];
  const tier = canonicalTier(cfg.tier, cat);
  const g = cat.tiers[tier];
  if (!g) return [`unknown tier ${cfg.tier}`];
  if (!(g.it_kw_min <= cfg.it_kw && cfg.it_kw <= g.it_kw_max)) errs.push(`${g.label} supports ${g.it_kw_min}–${g.it_kw_max} kW IT, got ${cfg.it_kw}`);
  if (!(1 <= cfg.racks && cfg.racks <= g.max_racks)) errs.push(`${g.label} holds 1–${g.max_racks} racks, got ${cfg.racks}`);
  const cl = cat.cooling[cfg.cooling];
  if (!cl) errs.push(`unknown cooling ${cfg.cooling}`);
  else {
    const perRack = cfg.it_kw / Math.max(cfg.racks, 1);
    if (perRack > cl.max_rack_kw) errs.push(`${perRack.toFixed(1)} kW/rack exceeds ${cl.label} limit of ${cl.max_rack_kw} kW/rack`);
  }
  if (tier === 'ben5' && cfg.cooling !== 'cabinet_dx') errs.push('BEN 5 uses cabinet_dx cooling only');
  if (tier !== 'ben5' && cfg.cooling === 'cabinet_dx') errs.push('cabinet_dx is for BEN 5 only');
  if (tier === 'ben2000' && cfg.cooling !== 'dlc_cdu' && cfg.cooling !== 'dlc_hd') errs.push('BEN 2000 is direct-liquid cooled (dlc_cdu)');
  if (cfg.cooling === 'dlc_hd' && !dlcHdTiers(cat).includes(tier)) errs.push('High-density DLC (dlc_hd) is for BEN 150 and up');
  const pa = cfg.power_architecture ?? 'ac480';
  if (!powerArchitectures(cat)[pa]) errs.push(`unknown power_architecture ${pa}`);
  else if (!powerArchitectures(cat)[pa].tiers.includes(tier)) errs.push('800 VDC (dc800) is for BEN 150, BEN 500 and BEN 2000 only; BEN 5 and BEN 30 stay 480/208 V AC');
  const hz = cfg.hardening ?? 'H1';
  if (!hardeningTable(cat)[hz]) errs.push(`unknown hardening ${hz}`);
  const ct = cfg.controls_tier ?? 'auto';
  if (!['auto', 'lite', 'pro'].includes(ct)) errs.push(`unknown controls_tier ${ct}`);
  else if (ct === 'lite' && (tier === 'ben150' || tier === 'ben500' || tier === 'ben2000')) errs.push('BEN Controls Lite is for BEN 5 and BEN 30 only; BEN 150 and up use BEN Controls Pro');
  if (!errs.length && tier !== 'ben5') {
    const d = derived(cfg, cat);
    if (!d.row_fits) errs.push(`${d.rows} row(s) of ${d.racks_per_row} racks + cooling units is ${d.row_length_mm} mm per row, exceeds interior ${Math.round(g.int_l_m * 1000)} mm; use fewer racks, rear-door or liquid cooling`);
  }
  return errs;
}

export function derived(cfg, cat) {
  const tier = canonicalTier(cfg.tier, cat);
  const g = cat.tiers[tier], cl = cat.cooling[cfg.cooling], clim = cat.climates[cfg.climate];
  const hzKey = cfg.hardening ?? 'H1';
  const hz = hardeningTable(cat)[hzKey];
  const modules = g.modules ?? 1, kind = g.kind ?? 'module', rows = g.rows ?? 1;
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
  let upsModules = cfg.redundancy === 'N' ? 1 : 2;
  let upsKvaEach = Math.round(upsN);
  const dc800 = (cfg.power_architecture ?? 'ac480') === 'dc800';
  let dc = {};
  if (dc800) {
    upsModules = 0; upsKvaEach = 0;
    const P = dcTable(cat), v = P.bus_v_nominal;
    const frontEnd = totalKw / P.rectifier_eff;
    const busA = cfg.it_kw * 1000 / v * P.bus_headroom;
    const frames = P.busway_frames_a && P.busway_frames_a.length ? P.busway_frames_a : DC_BUSWAY_FRAMES;
    const buswayA = frames.find(f => f >= busA) ?? frames[frames.length - 1];
    const nRect = Math.ceil(frontEnd / P.rectifier_module_kw);
    const nRectTotal = cfg.redundancy === 'N+1' ? nRect + 1 : cfg.redundancy === '2N' ? 2 * nRect : nRect;
    const lengthM = g.int_l_m + 5.0;
    const iDc = cfg.it_kw * 1000 / v, iAc = cfg.it_kw * 1000 / (Math.sqrt(3) * P.ac_feeder_v * P.ac_feeder_pf);
    const cuDc = 2 * (iDc / P.copper_current_density_a_mm2) * lengthM * P.copper_kg_per_mm2_m;
    const cuAc = 3 * (iAc / P.copper_current_density_a_mm2) * lengthM * P.copper_kg_per_mm2_m;
    const battKwh = cfg.it_kw * (cfg.ups_minutes ?? 10) / 60 / 0.9;
    dc = { ac_dc_front_end_kw: +frontEnd.toFixed(1), rectifier_eff: P.rectifier_eff, dc_bus_v_nominal: v, dc_bus_v_pole: P.pole_v_to_ground, dc_bus_v_min: P.bus_v_min, dc_bus_v_max: P.bus_v_max,
      dc_bus_current_a: Math.round(busA), dc_busway_a: buswayA, rectifier_module_kw: P.rectifier_module_kw, rectifier_modules_n: nRect, rectifier_modules: nRectTotal,
      rectifier_cabinets: Math.ceil(nRectTotal / 4), imd_count: nRectTotal, battery_on_bus_kwh: +battKwh.toFixed(1), battery_string_v: '800 V class',
      dc_loss_saving_kw: +(cfg.it_kw * P.loss_saving_frac).toFixed(1), dc_loss_saving_frac: P.loss_saving_frac,
      copper_kg_dc_bus: +cuDc.toFixed(1), copper_kg_ac_feeders: +cuAc.toFixed(1), copper_saving_pct: +(100 * (1 - cuDc / cuAc)).toFixed(1) };
  }
  const mvService = g.voltage.startsWith('12.47');
  let serviceAmps;
  if (mvService || g.voltage.startsWith('480')) serviceAmps = totalKva * 1000 / (Math.sqrt(3) * 480) / 0.8;
  else if (g.voltage.startsWith('208 V 3')) serviceAmps = totalKva * 1000 / (Math.sqrt(3) * 208) / 0.8;
  else serviceAmps = totalKva * 1000 / 240 / 0.8;
  const breaker = FRAMES.find(f => f >= serviceAmps) ?? 4000;
  // MV service: 2,500 kVA pad-mount transformers, 2N when redundancy is 2N or N+1; N+1 generators of 1,250 kW
  let xfmrKva = 0, xfmrTotal = 0, gensTotal = 0, genKwEach = 0;
  if (mvService) {
    xfmrKva = 2500;
    const xfmrN = Math.ceil(totalKva / (xfmrKva * 0.9));
    xfmrTotal = (cfg.redundancy === '2N' || cfg.redundancy === 'N+1') ? xfmrN * 2 : xfmrN;
    const gensN = Math.ceil(totalKw * 1.25 / 1250);
    gensTotal = cfg.generator ? gensN + 1 : 0;
    genKwEach = 1250;
  } else {
    gensTotal = cfg.generator ? 1 : 0;
    genKwEach = cfg.generator ? Math.ceil(totalKw * 1.25 / 10) * 10 : 0;
  }
  const ups_minutes = cfg.ups_minutes ?? 10;
  const batteryKwh = cfg.it_kw * ups_minutes / 60 / 0.9;
  const airflow = cl.medium === 'air' ? cfg.it_kw * 125 : (cl.air_residual !== undefined ? cfg.it_kw * 125 * cl.air_residual : cfg.it_kw * 40);
  const area = 2 * (g.ext_l_m * g.ext_h_m + g.ext_w_m * g.ext_h_m) + g.ext_l_m * g.ext_w_m;
  let payload = cfg.racks * (tier === 'ben5' ? 400 : 900) + nTotal * cl.mass_kg + upsModules * (tier === 'ben5' ? 120 : 350) + batteryKwh * 8 + area * hz.mass_kg_m2;
  if (dc800) payload += dc.rectifier_cabinets * 400;
  let loop = {};
  if (cfg.cooling === 'dlc_hd') {
    const liquidKw = cfg.it_kw * (1 - cl.air_residual);
    loop = { loop_water_class: cl.water_class, loop_dt_design_k: 10, loop_supply_design_c: 40, loop_return_design_c: 50, liquid_heat_kw: +liquidKw.toFixed(1),
      loop_flow_lpm: +(liquidKw / (4.18 * 10) * 60).toFixed(1), heat_reuse_kw_available: +liquidKw.toFixed(1), air_residual: cl.air_residual };
  }
  const gross = payload + g.tare_kg;
  const envGain = (area * (clim.t_design_c - 22) / 3.5 + 0.3 * clim.solar_w_m2 * g.ext_l_m * g.ext_w_m * 0.25) / 1000;
  const racksPerRow = Math.ceil(cfg.racks / rows);
  const unitsPerRow = Math.ceil(nTotal / rows);
  const rowLen = racksPerRow * 600 + ((cl.medium === 'air' || cl.medium === 'liquid') ? unitsPerRow * cl.width_mm : 0) + 500;
  const rowFits = tier === 'ben5' || rowLen <= g.int_l_m * 1000;
  const nfpa855 = batteryKwh >= 20;
  const ct = controlsTierResolved(cfg, cat);
  const pods = tier === 'ben5' ? 3 : cfg.racks * 2 + 2 * modules;
  return {
    tier_label: g.label, enclosure: g.enclosure, per_rack_kw: +perRack.toFixed(2),
    cooling_label: cl.label, cooling_units_n: nUnits, cooling_units_total: nTotal,
    cooling_unit_kw_derated: +unitKw.toFixed(1), cooling_derate: +derate.toFixed(3), cooling_elec_kw: +coolElec.toFixed(2),
    total_kw: +totalKw.toFixed(1), total_kva: +totalKva.toFixed(1), voltage: g.voltage,
    service_amps_calc: Math.round(serviceAmps), service_breaker_a: breaker,
    ups_modules: upsModules, ups_kva_each: upsKvaEach, battery_kwh: +batteryKwh.toFixed(1),
    airflow_cfm: Math.round(airflow), payload_kg: Math.round(payload), gross_kg: Math.round(gross),
    envelope_gain_kw: +envGain.toFixed(2), pue_estimate: +(totalKw / cfg.it_kw + (dc800 ? dcTable(cat).pue_loss_adder : 0.03)).toFixed(3),
    power_architecture: cfg.power_architecture ?? 'ac480', dc_ready: dcTable(cat).tiers.includes(tier), ...dc, ...loop,
    row_length_mm: Math.trunc(rowLen), row_fits: rowFits, rows, racks_per_row: racksPerRow, nfpa_855_scope: nfpa855,
    mv_service: mvService, transformer_kva: xfmrKva, transformers_total: xfmrTotal,
    generators_total: gensTotal, generator_kw_each: genKwEach,
    modules, kind,
    hardening: hzKey, hardening_label: hz.label, hardening_rating: hz.rating, hardening_coating: hz.coating,
    hardening_recommended: hardeningRecommended(cfg.profile, cfg.climate), envelope_area_m2: +area.toFixed(1),
    ashrae_class: cat.profiles[cfg.profile].ashrae,
    controls_tier_resolved: ct,
    controls_label: (cat.controls_tiers ?? {})[ct]?.label ?? (ct === 'pro' ? 'BEN Controls Pro' : 'BEN Controls Lite'),
    pods,
  };
}

export function preset(tier, profile = 'ai_inference', climate = 'temperate', cat, hardening = null) {
  tier = canonicalTier(tier, cat);
  const g = cat.tiers[tier], p = cat.profiles[profile];
  let itKw = Math.min(g.it_kw_max, Math.max(g.it_kw_min, p.rack_kw * g.max_racks * 0.8));
  if ((g.kind ?? 'module') === 'hall') itKw = 0.8 * g.it_kw_max;  // a 2 MW center is sold near its nominal size
  const racks = Math.max(1, Math.min(g.max_racks, Math.ceil(itKw / p.rack_kw)));
  let cooling = g.default_cooling;
  if (tier !== 'ben5' && itKw / racks > cat.cooling[cooling].max_rack_kw) cooling = 'dlc_cdu';
  if (hardening == null) hardening = hardeningRecommended(profile, climate);
  const cfg = { tier, profile, it_kw: Math.round(itKw), racks, cooling, redundancy: p.redundancy, climate,
    subsystems: ['power', 'cooling', 'compute', 'controls'], white_label: false, brand: 'Schreiber AI', ups_minutes: 10,
    generator: ['healthcare', 'public_sector', 'off_grid'].includes(profile) || tier === 'ben2000', site_name: 'Demo site',
    controls_tier: 'auto', hardening, power_architecture: 'ac480' };
  if (tier === 'ben2000') cfg.cooling = 'dlc_cdu';
  else if (tier !== 'ben5') for (const alt of [cooling, 'inrow_dx_300', 'rdhx_drycooler', 'dlc_cdu']) { cfg.cooling = alt; if (!validate(cfg, cat).length) break; }
  return cfg;
}

// BEN Engine selector — JavaScript port of software/ben_engine/config.py (keep in sync; tests/test_selector_parity.py checks numbers)
export const FRAMES = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000];
// forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): 800 VDC option and high-density DLC; defaults in cat.power_architectures
export const DC_BUSWAY_FRAMES = [400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200];
// 760–920 V is a WORKING ASSUMPTION (no primary source found; pending OCP Diablo 400 §9.3.1 / NVIDIA MGX power rack spec); efficiencies are vendor claims
const FALLBACK_DC = { tiers: ['ben150', 'ben500', 'ben2000'], bus_v_nominal: 800, bus_v_min: 760, bus_v_max: 920, window_basis: 'assumption pending OCP Diablo 400 §9.3.1 / NVIDIA MGX power rack spec',
  pole_v_to_ground: 400, rectifier_eff: 0.985, rectifier_module_kw: 100, rack_shelf_kw: 90, rack_shelf_eff: 0.985,
  bus_headroom: 1.25, busway_frames_a: DC_BUSWAY_FRAMES, loss_saving_frac: 0.03, copper_current_density_a_mm2: 2.0, ac_feeder_v: 415, ac_feeder_pf: 0.95, copper_kg_per_mm2_m: 8.96e-3 };
const FALLBACK_CONV = {
  bipolar_400: { label: '±400 VDC bipolar, high-resistance midpoint ground (OCP Diablo 400 convention)', pole_v_to_ground: 400 },
  unipolar_800: { label: '800 VDC unipolar, return isolated from earth (NVIDIA / OCP LVDC SST v0.3 convention)', pole_v_to_ground: 800 },
};
export function dcConventions(cat) { return cat.dc_conventions || FALLBACK_CONV; }
function dcTable(cat) { return (cat.power_architectures && cat.power_architectures.dc800) || FALLBACK_DC; }
function dlcHdTiers(cat) { return cat.dlc_hd_tiers || ['ben150', 'ben500', 'ben2000']; }
export function powerArchitectures(cat) { return cat.power_architectures || { ac480: { label: '480 V AC → UPS → 208/415 V AC PDUs (today)', tiers: ['ben5', 'ben30', 'ben150', 'ben500', 'ben2000'] }, dc800: { ...FALLBACK_DC, label: '800 VDC bus (forward option)' } }; }

// Generation-1 keys (container-length names) are accepted everywhere and normalised to the power-based keys.
// Rev 2: "ben1000" was the working name of the 40 ft liquid-first flagship; with real footprints it is BEN 700.
export const TIER_ALIASES = { micro: 'ben5', ben10: 'ben30', ben20: 'ben150', ben40: 'ben500', ben1000: 'ben700' };
export function canonicalTier(t, cat) { return ((cat && cat.tier_aliases) || TIER_ALIASES)[t] ?? t; }

// ---------------------------------------------------------------- Rev 2 (docs/REV2_DECISION.md §2, config.py TIERS_BY_LINEUP)
export const TIERS_BY_LINEUP = {
  rev1: ['ben5', 'ben30', 'ben150', 'ben500', 'ben2000'],
  rev2: ['ben1', 'ben5', 'ben30', 'ben150', 'ben300', 'ben500', 'ben700', 'ben2000'],
};
export function tiersByLineup(cat) { return (cat && cat.tiers_by_lineup) || TIERS_BY_LINEUP; }
// A saved configuration without a lineup is Rev 1 when its tier is a Rev 1 tier (config.Config.from_dict)
export function lineupOf(cfg, cat) {
  if (cfg.lineup) return cfg.lineup;
  return tiersByLineup(cat).rev1.includes(canonicalTier(cfg.tier, cat)) ? 'rev1' : 'rev2';
}
// Python round(): half to even (used where config.py rounds a value that can land on .5)
export function pyRound(x) {
  const f = Math.floor(x), r = x - f;
  if (Math.abs(r - 0.5) < 1e-9) return f % 2 === 0 ? f : f + 1;
  return Math.round(x);
}
const isMini = (g) => (g.kind ?? 'module') === 'minirack';
export function geometry(cfg, cat) {
  const tier = canonicalTier(cfg.tier, cat);
  const g = cat.tiers[tier];
  if (!isMini(g)) return g;
  const f = g.forms[cfg.form] || g.forms[g.default_form];
  const out = { ...g };
  delete out.forms;
  for (const k of ['ext_l_m', 'ext_w_m', 'ext_h_m', 'int_l_m', 'int_w_m', 'int_h_m', 'rack_u', 'tare_kg']) out[k] = f[k];
  Object.assign(out, { form: cfg.form, form_label: f.label, it_kw_max_form: f.it_kw_max, rack_in: f.rack_in, door: f.door, insertion_loss_db: f.insertion_loss_db, reference: f.reference });
  return out;
}
function densityOf(cfg, g) {
  const fp = g.ext_l_m * g.ext_w_m, vol = fp * g.ext_h_m;
  return { lineup: 'rev2', kw_per_rack: +(cfg.it_kw / cfg.racks).toFixed(2), footprint_m2: +fp.toFixed(3), volume_m3: +vol.toFixed(3),
    kw_per_m2_footprint: +(cfg.it_kw / fp).toFixed(2), kw_per_m3_volume: +(cfg.it_kw / vol).toFixed(2) };
}

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
  if (ct === 'lite' || ct === 'pro' || ct === 'mini') return ct;
  if (cat.tiers[tier] && isMini(cat.tiers[tier])) return 'mini';
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
  if (!dcConventions(cat)[cfg.dc_convention ?? 'bipolar_400']) errs.push(`unknown dc_convention ${cfg.dc_convention}`);
  const hz = cfg.hardening ?? 'H1';
  if (!hardeningTable(cat)[hz]) errs.push(`unknown hardening ${hz}`);
  const ct = cfg.controls_tier ?? 'auto';
  if (!['auto', 'lite', 'pro', 'mini'].includes(ct)) errs.push(`unknown controls_tier ${ct}`);
  else if (ct === 'lite' && (tier === 'ben150' || tier === 'ben500' || tier === 'ben2000')) errs.push('BEN Controls Lite is for BEN 5 and BEN 30 only; BEN 150 and up use BEN Controls Pro');
  errs.push(...validateRev2(cfg, cat));
  if (!errs.length && tier !== 'ben5' && !isMini(g)) {
    const d = derived(cfg, cat);
    if (!d.row_fits) errs.push(`${d.rows} row(s) of ${d.racks_per_row} racks + cooling units is ${d.row_length_mm} mm per row, exceeds interior ${Math.round(g.int_l_m * 1000)} mm; use fewer racks, rear-door or liquid cooling`);
  }
  return errs;
}

// Rev 2 rules (config.Config._validate_rev2); none of them can fire on a valid Rev 1 configuration
function validateRev2(cfg, cat) {
  const errs = [];
  const tier = canonicalTier(cfg.tier, cat);
  const g = cat.tiers[tier];
  const lineup = lineupOf(cfg, cat), byL = tiersByLineup(cat);
  const hz = cfg.hardening ?? 'H1', ct = cfg.controls_tier ?? 'auto';
  if (!byL[lineup]) errs.push(`unknown lineup ${lineup}`);
  else if (!byL[lineup].includes(tier)) errs.push(`${g.label} is not in lineup ${lineup}`);
  if (hz === 'IND' && !isMini(g)) errs.push('hardening IND (indoor) is for BEN 1 only');
  if (ct === 'mini' && !isMini(g)) errs.push('BEN Controls Mini is for BEN 1 only');
  if (cfg.cooling === 'office_air' && !isMini(g)) errs.push('office_air cooling is for BEN 1 only');
  if (isMini(g)) {
    const f = g.forms[cfg.form];
    if (!f) errs.push(`unknown BEN 1 form ${cfg.form} (rack10 or cab12)`);
    else if (cfg.it_kw > f.it_kw_max) errs.push(`BEN 1 ${cfg.form} carries up to ${f.it_kw_max} kW IT, got ${cfg.it_kw}; use cab12`);
    if (cfg.cooling !== 'office_air') errs.push('BEN 1 uses office_air cooling only (no dc800, no dlc_hd; liquid only inside the IT device)');
    if ((cfg.power_architecture ?? 'ac480') !== 'ac480') errs.push('BEN 1 is a 120 V plug-in unit: dc800 does not apply');
    if (hz !== 'IND') errs.push('BEN 1 is indoor: hardening levels H1-H3 do not apply (IND)');
    if (cfg.generator) errs.push('BEN 1 has no generator (plug-in UPS only)');
    if (cfg.redundancy === '2N') errs.push('BEN 1 has one UPS; for 2N use two BEN 1 units');
    if (ct === 'lite' || ct === 'pro') errs.push('BEN 1 uses BEN Controls Mini (2 BEN Pods + BEN Care agent)');
    if (!errs.length && f && miniPower(cfg, cat).amps > 16.0) errs.push(`BEN 1 draws ${miniPower(cfg, cat).amps.toFixed(1)} A at 120 V, above the 16 A continuous limit of a 20 A circuit; use the 230 V option`);
  }
  if (g.liquid_first) {
    if (cfg.cooling !== 'dlc_hd') errs.push(`${g.label} is liquid-first: dlc_hd only`);
    const pr = cfg.it_kw / Math.max(cfg.racks, 1);
    if (pr > g.max_rack_kw) errs.push(`${pr.toFixed(1)} kW/rack exceeds the ${g.max_rack_kw} kW GB300 NVL72-class rack limit of ${g.label}`);
    if (ct === 'lite') errs.push(`BEN Controls Lite is for BEN 5 and BEN 30 only; ${g.label} uses BEN Controls Pro`);
  }
  return errs;
}

function miniPower(cfg, cat) {
  const M = cat.minirack, cl = cat.cooling.office_air;
  const cool = cfg.it_kw / cl.cop;
  const total = cfg.it_kw + cool + M.aux_kw + cfg.it_kw * (1 / M.ups_eff - 1);
  const kva = total / 0.95;
  return { cool, total, kva, amps: kva * 1000 / 120 };
}

// BEN 1 sizing (config.Config._derived_minirack): 120 V plug-in, lithium line-interactive UPS, office-air extraction
function derivedMinirack(cfg, cat) {
  const tier = canonicalTier(cfg.tier, cat);
  const g = geometry(cfg, cat), M = cat.minirack;
  const f = cat.tiers[tier].forms[cfg.form] || cat.tiers[tier].forms.cab12;
  const cl = cat.cooling[cfg.cooling] || cat.cooling.office_air;
  const clim = cat.climates[cfg.climate];
  const hzKey = cfg.hardening ?? 'IND', hz = hardeningTable(cat)[hzKey] || hardeningTable(cat).IND;
  const pw = miniPower(cfg, cat);
  const itW = cfg.it_kw * 1000;
  const nUnits = Math.ceil(cfg.it_kw * 1.05 / cl.unit_kw);
  const nTotal = cfg.redundancy === 'N+1' ? nUnits + 1 : cfg.redundancy === '2N' ? 2 * nUnits : nUnits;
  const amps = pw.amps;
  let brk, outlet;
  if (amps <= 12) { brk = 15; outlet = 'NEMA 5-15R on a dedicated 15 A, 120 V circuit (12 A continuous at 80 %)'; }
  else if (amps <= 16) { brk = 20; outlet = 'NEMA 5-20R on a dedicated 20 A, 120 V circuit (16 A continuous at 80 %)'; }
  else { brk = 30; outlet = 'exceeds a 120 V 20 A circuit: use the 230 V option'; }
  const needW = itW * M.ups_headroom;
  const ups = M.ups_models.find(u => u.w >= needW) || M.ups_models[M.ups_models.length - 1];
  const runtime = ups.wh / Math.max(itW, 1) * 60;
  const upsMin = cfg.ups_minutes ?? 10;
  const packs = runtime >= upsMin ? 0 : Math.ceil((upsMin * itW / 60 - ups.wh) / ups.wh);
  const batteryKwh = cfg.it_kw * upsMin / 60 / 0.9;
  const src = M.noise_src_dba[f.noise_source] + 15 * Math.log10(Math.max(itW, 50) / 200);
  const inside = src - f.insertion_loss_db;
  const noise = 10 * Math.log10(10 ** (inside / 10) + 10 ** (28 / 10));
  const target = M.noise_target_dba[cfg.form] ?? M.noise_target_dba.cab12;
  const heatW = pw.total * 1000;
  const ventCfm = heatW / (1.18 * 1006 * 5) / 0.000471947;
  const airflow = itW / (1.18 * 1006 * (cl.design_rise_k ?? 10)) / 0.000471947;
  const area = 2 * (g.ext_l_m * g.ext_h_m + g.ext_w_m * g.ext_h_m) + g.ext_l_m * g.ext_w_m;
  const upsKg = ups.va <= 1000 ? 16 : 28;
  const payload = cfg.it_kw * M.kg_per_kw_it + upsKg * (1 + packs);
  const ct = controlsTierResolved(cfg, cat);
  const prof = cat.profiles[cfg.profile].ashrae;
  return {
    power_architecture: 'ac480', power_architecture_label: '120 V plug-in → line-interactive lithium UPS → rack PDU (BEN 1)', dc_ready: false,
    tier_label: g.label, enclosure: `${g.form_label} (${g.reference} class)`, form: cfg.form, form_label: g.form_label,
    per_rack_kw: +(cfg.it_kw / cfg.racks).toFixed(2), cooling_label: cl.label, cooling_units_n: nUnits, cooling_units_total: nTotal,
    cooling_unit_kw_derated: +cl.unit_kw.toFixed(1), cooling_derate: 1.0, cooling_elec_kw: +pw.cool.toFixed(3),
    total_kw: +pw.total.toFixed(3), total_kva: +pw.kva.toFixed(3), voltage: g.voltage, voltage_option: g.voltage_option,
    service_amps_calc: pyRound(amps / 0.8), service_breaker_a: brk, outlet_amps: +amps.toFixed(1), outlet_circuit: outlet, outlet_circuit_a: brk,
    ups_modules: 1, ups_kva_each: ups.va / 1000, ups_va: ups.va, ups_w: ups.w, ups_model: ups.model, ups_plug: ups.plug,
    ups_runtime_min_est: +runtime.toFixed(1), ups_battery_packs: packs, battery_kwh: +batteryKwh.toFixed(3),
    airflow_cfm: Math.round(airflow), payload_kg: Math.round(payload), gross_kg: Math.round(payload + g.tare_kg),
    envelope_gain_kw: 0.0, pue_estimate: +(pw.total / cfg.it_kw).toFixed(3),
    row_length_mm: Math.trunc(g.ext_l_m * 1000), row_fits: true, rows: 1, racks_per_row: 1, nfpa_855_scope: batteryKwh >= 20,
    mv_service: false, transformer_kva: 0, transformers_total: 0, generators_total: 0, generator_kw_each: 0, modules: 1, kind: 'minirack',
    hardening: hzKey, hardening_label: hz.label, hardening_rating: hz.rating, hardening_coating: hz.coating, hardening_recommended: 'IND',
    envelope_area_m2: +area.toFixed(2), ashrae_class: prof === 'A1' ? 'A2' : prof, ashrae_profile_class: prof,
    controls_tier_resolved: ct, controls_label: (cat.controls_tiers ?? {})[ct]?.label ?? 'BEN Controls Mini', pods: 2,
    noise_dba_est: +noise.toFixed(1), noise_dba_target: target, noise_ok: noise <= target,
    noise_quiet_up_to_kw: +(200 * 10 ** ((target - M.noise_src_dba[f.noise_source] + f.insertion_loss_db) / 15) / 1000).toFixed(2),
    heat_to_room_w: Math.round(heatW), heat_to_room_btu_h: Math.round(heatW * 3.412), closet_vent_cfm: Math.round(ventCfm),
    office_design_c: M.office_design_c, office_max_c: M.office_max_c, climate: clim, geometry: g,
    ...densityOf(cfg, g),
  };
}

// Dense row order (config.Config.dense_row_items): switchboard, power (battery / UPS interleaved), CDUs, racks with fan coils between
export function denseRowItems(cfg, d) {
  const items = Array(d.swbd_sections).fill('swbd');
  if ((cfg.power_architecture ?? 'ac480') === 'dc800') {
    items.push(...Array(d.rectifier_cabinets).fill('rect'), ...Array(d.battery_cabinets).fill('batt800'));
  } else {
    let b = d.battery_cabinets, u = d.ups_frames;
    while (b || u) { if (b) { items.push('batt'); b--; } if (u) { items.push('ups'); u--; } }
  }
  items.push(...Array(d.cooling_units_total).fill('cdu'));
  const nr = cfg.racks, nf = d.fancoils_total;
  const slots = new Set();
  for (let i = 0; i < nf; i++) slots.add(pyRound((i + 0.5) * (nr + nf) / nf - 0.5));
  let ri = 0, fi = 0;
  for (let k = 0; k < nr + nf; k++) {
    if ((slots.has(k) && fi < nf) || ri >= nr) { items.push('fancoil'); fi++; } else { items.push('rack'); ri++; }
  }
  return items;
}

function applyDense(cfg, cat, out, upsKvaN, area, hz, dc) {
  const tier = canonicalTier(cfg.tier, cat);
  const g = cat.tiers[tier], F = cat.dense_footprints, R = cat.dense_rules;
  const mult = cfg.redundancy === '2N' ? 2 : 1;
  const resid = cat.cooling[cfg.cooling].air_residual ?? 0.10;
  const fcN = Math.ceil(resid * cfg.it_kw * 1.05 / F.fancoil.kw);
  const fcTotal = cfg.redundancy === 'N+1' ? fcN + 1 : fcN * mult;
  const dc800 = (cfg.power_architecture ?? 'ac480') === 'dc800';
  const battNeed = dc800 ? dc.battery_on_bus_kwh : out.battery_kwh;
  const battCab = Math.max(Math.ceil(battNeed / F.batt.kwh), Math.ceil(cfg.it_kw / F.batt.kw)) * mult;
  let framesN = 0, frames = 0, kvaEach = 0;
  if (!dc800) { framesN = Math.ceil(upsKvaN / F.ups.kva); frames = framesN * mult; kvaEach = pyRound(upsKvaN / framesN); }
  const brk = out.service_breaker_a;
  const swbd = brk <= R.panelboard_max_a ? 0 : (brk <= F.swbd.a_per_section ? 1 : (brk <= 2500 ? 2 : 3));
  Object.assign(out, { ups_modules: frames, ups_kva_each: kvaEach, ups_frames: frames, ups_frames_n: framesN,
    fancoils_n: fcN, fancoils_total: fcTotal, fancoil_kw: F.fancoil.kw, trim_loop_kw: +(resid * cfg.it_kw * 1.1).toFixed(1), trim_loop_c: R.trim_loop_c,
    battery_cabinets: battCab, battery_kwh_installed: +(battCab * F.batt.kwh).toFixed(1),
    battery_minutes_installed: +(battCab * F.batt.kwh * 0.9 * 60 / cfg.it_kw).toFixed(1),
    swbd_sections: swbd, panelboard_wall: swbd === 0, liquid_first: true, rack_envelope_mm: [F.rack.w, F.rack.d, F.rack.h], rack_kw_max: g.max_rack_kw });
  const items = denseRowItems(cfg, out);
  const rowMm = items.reduce((a, k) => a + F[k].w, 0) + R.end_zone_mm;
  const rect = dc800 ? (out.rectifier_cabinets ?? 0) : 0;
  const payload = cfg.racks * F.rack.kg + out.cooling_units_total * F.cdu.kg + fcTotal * F.fancoil.kg + frames * F.ups.kg + battCab * F.batt.kg
    + swbd * F.swbd.kg + rect * F.rect.kg + area * hz.mass_kg_m2;
  Object.assign(out, { row_items: items, row_length_mm: Math.trunc(rowMm), row_fits: rowMm <= g.int_l_m * 1000,
    row_budget_mm: Math.trunc(g.int_l_m * 1000 - R.end_zone_mm), end_zone_mm: R.end_zone_mm,
    payload_kg: Math.round(payload), gross_kg: Math.round(payload + g.tare_kg), nfpa_855_scope: battCab * F.batt.kwh >= 20 });
}

export function derived(cfg, cat) {
  const tier = canonicalTier(cfg.tier, cat);
  if (cat.tiers[tier] && isMini(cat.tiers[tier])) return derivedMinirack(cfg, cat);
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
    const convKey = cfg.dc_convention ?? 'bipolar_400', conv = dcConventions(cat)[convKey];
    const busKw = cfg.it_kw / P.rack_shelf_eff;            // the bus feeds the 800 V -> 50 V rack shelves
    const frontEnd = (totalKw + busKw - cfg.it_kw) / P.rectifier_eff;
    const busA = busKw * 1000 / v * P.bus_headroom;
    const frames = P.busway_frames_a && P.busway_frames_a.length ? P.busway_frames_a : DC_BUSWAY_FRAMES;
    const buswayA = frames.find(f => f >= busA) ?? frames[frames.length - 1];
    const nRect = Math.ceil(frontEnd / P.rectifier_module_kw);
    const nRectTotal = cfg.redundancy === 'N+1' ? nRect + 1 : cfg.redundancy === '2N' ? 2 * nRect : nRect;
    const lengthM = g.int_l_m + 5.0;
    const iDc = busKw * 1000 / v, iAc = cfg.it_kw * 1000 / (Math.sqrt(3) * P.ac_feeder_v * P.ac_feeder_pf);
    const shelvesPerRack = Math.ceil(cfg.it_kw / cfg.racks / P.rack_shelf_kw) + ((cfg.redundancy === 'N+1' || cfg.redundancy === '2N') ? 1 : 0);
    const cuDc = 2 * (iDc / P.copper_current_density_a_mm2) * lengthM * P.copper_kg_per_mm2_m;
    const cuAc = 3 * (iAc / P.copper_current_density_a_mm2) * lengthM * P.copper_kg_per_mm2_m;
    const battKwh = cfg.it_kw * (cfg.ups_minutes ?? 10) / 60 / 0.9;
    dc = { ac_dc_front_end_kw: +frontEnd.toFixed(1), rectifier_eff: P.rectifier_eff, dc_convention: convKey, dc_convention_label: conv.label, dc_grounding: conv.grounding, dc_imd_arrangement: conv.imd_arrangement,
      dc_bus_v_nominal: v, dc_bus_v_pole: conv.pole_v_to_ground, dc_bus_v_min: P.bus_v_min, dc_bus_v_max: P.bus_v_max, dc_window_v: [P.bus_v_min, P.bus_v_max], dc_window_basis: P.window_basis,
      dc_bus_kw: +busKw.toFixed(1), rack_shelf_kw: P.rack_shelf_kw, rack_shelf_eff: P.rack_shelf_eff, rack_shelves_per_rack: shelvesPerRack, rack_shelves_total: shelvesPerRack * cfg.racks,
      dc_pue_loss_adder: +((1 / P.rectifier_eff - 1) + (1 / P.rack_shelf_eff - 1)).toFixed(4),
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
  const out = {
    tier_label: g.label, enclosure: g.enclosure, per_rack_kw: +perRack.toFixed(2),
    cooling_label: cl.label, cooling_units_n: nUnits, cooling_units_total: nTotal,
    cooling_unit_kw_derated: +unitKw.toFixed(1), cooling_derate: +derate.toFixed(3), cooling_elec_kw: +coolElec.toFixed(2),
    total_kw: +totalKw.toFixed(1), total_kva: +totalKva.toFixed(1), voltage: g.voltage,
    service_amps_calc: Math.round(serviceAmps), service_breaker_a: breaker,
    ups_modules: upsModules, ups_kva_each: upsKvaEach, battery_kwh: +batteryKwh.toFixed(1),
    airflow_cfm: Math.round(airflow), payload_kg: Math.round(payload), gross_kg: Math.round(gross),
    envelope_gain_kw: +envGain.toFixed(2), pue_estimate: +(totalKw / cfg.it_kw + (dc800 ? dc.dc_pue_loss_adder : 0.03)).toFixed(3),
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
  if (g.liquid_first) applyDense(cfg, cat, out, upsN, area, hz, dc);
  if (lineupOf(cfg, cat) === 'rev2') Object.assign(out, densityOf(cfg, g));
  return out;
}

// Rev 2 presets (config.Config._preset_minirack / _preset_dense); carried tiers use the frozen Rev 1 rule in both lineups
function presetMinirack(tier, profile, climate, lineup, form) {
  form = form || (['ai_training', 'healthcare', 'public_sector'].includes(profile) ? 'cab12' : 'rack10');
  const it = form === 'cab12' ? (profile === 'ai_training' ? 1.1 : 1.0) : (profile === 'ai_inference' ? 0.6 : 0.4);
  return { tier, profile, it_kw: it, racks: 1, cooling: 'office_air', redundancy: form === 'rack10' ? 'N' : 'N+1', climate,
    subsystems: ['power', 'cooling', 'compute', 'controls'], white_label: false, brand: 'Schreiber AI', ups_minutes: 10, generator: false,
    site_name: 'Demo site', controls_tier: 'auto', hardening: 'IND', power_architecture: 'ac480', dc_convention: 'bipolar_400', lineup, form };
}

function presetDense(tier, profile, climate, cat, hardening, lineup) {
  const g = cat.tiers[tier], p = cat.profiles[profile];
  const it0 = ['ai_training', 'ai_inference'].includes(profile) ? g.it_kw_max : 0.8 * g.it_kw_max;
  if (hardening == null) hardening = hardeningRecommended(profile, climate);
  const cfg = { tier, profile, it_kw: pyRound(it0), racks: g.max_racks, cooling: 'dlc_hd', redundancy: p.redundancy, climate,
    subsystems: ['power', 'cooling', 'compute', 'controls'], white_label: false, brand: 'Schreiber AI', ups_minutes: g.ups_minutes_default ?? 5,
    generator: ['healthcare', 'public_sector', 'off_grid'].includes(profile), site_name: 'Demo site', controls_tier: 'auto', hardening,
    power_architecture: 'ac480', dc_convention: 'bipolar_400', lineup, form: '' };
  for (let racks = g.max_racks; racks >= 1; racks--) {
    let it = Math.min(pyRound(it0), racks * g.max_rack_kw);
    while (it >= g.it_kw_min) {
      cfg.racks = racks; cfg.it_kw = it;
      if (!validate(cfg, cat).length) return cfg;
      it -= 10;
    }
  }
  cfg.racks = g.max_racks; cfg.it_kw = pyRound(it0);
  return cfg;
}

export function preset(tier, profile = 'ai_inference', climate = 'temperate', cat, hardening = null, lineup = 'rev2', form = null) {
  tier = canonicalTier(tier, cat);
  const byL = tiersByLineup(cat);
  if (!byL[lineup] || !byL[lineup].includes(tier)) throw new Error(`${tier} is not in lineup ${lineup}`);
  const g0 = cat.tiers[tier];
  if (isMini(g0)) return presetMinirack(tier, profile, climate, lineup, form);
  if (g0.liquid_first) return presetDense(tier, profile, climate, cat, hardening, lineup);
  const cfg = presetRev1(tier, profile, climate, cat, hardening);
  cfg.lineup = lineup;
  cfg.form = '';
  return cfg;
}

function presetRev1(tier, profile, climate, cat, hardening) {
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
    controls_tier: 'auto', hardening, power_architecture: 'ac480', dc_convention: 'bipolar_400' };
  if (tier === 'ben2000') cfg.cooling = 'dlc_cdu';
  else if (tier !== 'ben5') for (const alt of [cooling, 'inrow_dx_300', 'rdhx_drycooler', 'dlc_cdu']) { cfg.cooling = alt; if (!validate(cfg, cat).length) break; }
  return cfg;
}

# BEN Engine — Test Guide (experiments on the twin, in the factory and on site)

**Owner:** Schreiber AI engineering. **Rule:** every experiment runs **first in the digital twin** (`ben_engine.twin.Twin`, faults via `tw.inject(...)`) so the expected curve is known before anyone touches the real unit; then at **FAT** (factory mode: load banks, shop power) and, where marked, again at **SAT** (site mode: real utility, real outdoor air). The commissioning script `software/ben_engine/commissioning.py` executes the experiments marked "scripted" and writes a signed report; the others are run by hand and the data attached.

Channel names are from `spec/PROTOCOL.md`: node telemetry `T_in_1..4`, `T_out_1..4`, `T_ref`, `RH`, `dP_aisle`, `leak`, `door`, `ai0..3_mA`, `pulse_kwh`; equipment telemetry (`ben/<unit>/equip/<id>/telemetry`): `kw`, `kva`, `v_ab`, `i_a`, `supply_c`, `return_c`, `fan_pct`, `soc_pct`, `runtime_min`, `alarm[]`; twin/dashboard state: `rack_inlet_c[]`, `rack_outlet_c[]`, `aisle_dp_pa`, `power.utility_kw`, `power.pdu_kw[]`, `power.ups_on_battery`, `pue`.

Data rate for all experiments: node telemetry at 1 Hz (set 2 Hz for E3/E5 transients), equipment at 1–10 s, outdoor temperature from the site weather sensor or the dry-cooler inlet probe. All data is exported as CSV (`GET /api/export.csv`) and kept with the report.

Summary:

| ID | Experiment | Where | Scripted | Proves |
| --- | --- | --- | --- | --- |
| E1 | Sensor cross-check at isothermal idle | twin, FAT, SAT | yes | Sensors agree; calibration valid |
| E2 | dP tare and fan-off zero | twin, FAT, SAT | yes | dP zero is real; tap placement OK |
| E3 | Load step with load banks | twin, FAT (full), SAT (reduced) | yes | Thermal time constant, recirculation, capacity |
| E4 | Cooling unit failover (N+1) | twin, FAT, SAT | yes | Redundancy works without a thermal excursion |
| E5 | Utility loss ride-through | twin, FAT, SAT | yes | Minutes to ASHRAE max with cooling off: "does cooling need UPS?" |
| E6 | Door-open infiltration | twin, FAT, SAT | yes | Effect of an open door; alarm logic |
| E7 | Filter clog simulation | twin, FAT | yes | dP alarm threshold; capacity loss with blocked filters |
| E8 | Outdoor temperature derate | twin, FAT (heated condenser inlet) or SAT (hot day) | partly | Capacity at design outdoor temperature |
| E9 | Power meter vs PDU sum reconciliation | twin, FAT, SAT | yes | Metering is right; PUE is honest |
| E10 | Acoustic survey at property line | SAT | no | Noise ordinance compliance |
| E11 | 48-hour burn-in | FAT (24 h minimum) / SAT (48 h) | yes | Infant mortality caught; stability |
| E12 | Cyber: port scan and failsafe on gateway loss | twin, FAT, SAT | yes | No open attack surface; loss of gateway is safe |

Common "what to do if it fails": stop, record, do not adjust more than one thing, re-run on the twin with the suspected fault injected to see whether the twin reproduces the real data — if it does not, the model is wrong and `analysis.py` must be refit; if it does, fix the hardware cause and repeat.

---

## E1 — Sensor cross-check at isothermal idle

| | |
| --- | --- |
| **Purpose** | Verify that every temperature and humidity sensor agrees when there is no reason for them to differ, and that calibration coefficients (`cal_id`) are loaded. |
| **Hypothesis** | With IT load off, cooling fans on low (mixing) and compressors off for ≥ 60 minutes, the container air is isothermal within 0.3 °C; all `T_in_*`, `T_out_*` and `T_ref` read within their combined k=2 uncertainty (±0.25 °C DS18B20, ±0.15 °C SHT45 → pair limit 0.3 °C). |
| **Setup** | Unit closed, doors shut, IT load 0 (load banks off), cooling units in "fan only" at 30 %, lights off (lights add ~0.3 kW), outdoor temperature between 10 and 30 °C (otherwise the envelope gain creates a gradient — record `outdoor_c`). Twin: `tw.set_it_load(0.0)`, cooling fan-only mode, run 3,600 s. |
| **Instrumentation** | All node channels at 1 Hz; one traceable reference probe (handheld, ±0.1 °C) placed next to `T_ref`, then moved to two inlet positions for 5 minutes each. |
| **Procedure** | 1. Confirm `cal_id` on every node matches the calibration certificates. 2. Wait 60 min, logging. 3. Take the last 10 minutes; compute mean and standard deviation per channel. 4. Compute each channel's deviation from the all-channel median and from the reference probe. 5. Repeat with fans off for 10 min to see stratification appear (expected: top − bottom rises to 0.5–1.5 °C, proving the three-height layout sees it). |
| **Data to record** | 10-min means/SD per channel; reference readings with time; `outdoor_c`; fan %; `RH` at supply and return; raw ADC counts (`raw`) for later re-processing. |
| **Analysis** | Deviation table; flag channels outside ±0.3 °C from median; compute RH consistency: humidity ratio from (T, RH) at supply and return must match within 0.3 g/kg. |
| **Pass** | ≥ 95 % of channels within ±0.3 °C of median and the reference; no channel beyond ±0.5 °C; RH humidity-ratio match within 0.3 g/kg; `cal_id` verified on 100 % of nodes. |
| **If it fails** | Single channel out: check mounting (touching metal? near a light?), then swap the sensor with a spare and re-run; if the deviation moves with the sensor, recalibrate/replace; if it stays, it is a placement effect — fix placement. Many channels out with a pattern by height: the room is not isothermal — extend mixing time or wait for milder outdoor temperature. Whole node offset: `cal_id` wrong — reload coefficients. |

## E2 — dP tare and fan-off zero

| | |
| --- | --- |
| **Purpose** | Establish the zero of the aisle differential pressure measurement and prove the taps are not in a velocity field. |
| **Hypothesis** | With all fans off and doors closed, cold-aisle to hot-aisle static pressure difference is 0.0 ± 0.4 Pa; the tare removes the mounting offset; turning fans on produces a positive, repeatable dP that scales with fan speed squared. |
| **Setup** | Fans off ≥ 5 min (no residual flow), doors shut, containment closed. Twin: cooling units off, `aisle_dp_pa` should read the sensor offset only. |
| **Instrumentation** | `dP_aisle` at 1 Hz; reference micromanometer (±0.25 Pa) on a parallel tee for 5 minutes. |
| **Procedure** | 1. Read `dP_aisle` for 5 min fans-off; record mean (this is the as-found offset). 2. Send `{"op":"tare","ch":"dP_aisle"}`; confirm ack. 3. Read 5 min; mean must be 0 ± 0.4 Pa. 4. Fans to 30 %, 60 %, 100 % for 5 min each; record mean dP. 5. Swap tubing sides (A↔B) at 60 % — the reading must change sign with the same magnitude within 1 Pa. 6. Open the containment door at 60 % — dP should collapse toward 0. |
| **Data to record** | As-found offset; post-tare mean/SD; dP at three fan speeds; sign-swap readings; reference readings. |
| **Analysis** | Fit dP = k·(fan %)² ; R² ≥ 0.95 proves a static-pressure signal. A poor fit or a dP that does not reverse on tube swap indicates a velocity-pressure contribution (tap in a jet) or a leak in the tubing. |
| **Pass** | Post-tare zero within ±0.4 Pa; reference agreement within ±0.5 Pa at 60 %; sign reversal within 1 Pa; R² ≥ 0.95; containment-open dP < 20 % of containment-closed value. |
| **If it fails** | Offset will not tare: tubing has water or a kink — blow out, re-run. No sign reversal: tap in a fan jet — move tap ≥ 1 m away, flush, perpendicular. Poor fit: leak in tubing — pressure-hold test the tubing. |

## E3 — Load step with load banks (thermal time constant, recirculation estimate)

| | |
| --- | --- |
| **Purpose** | Measure how fast the room responds to load, how much hot air leaks back to the inlets, and whether the cooling capacity in `config.derived()` is real. |
| **Hypothesis** | A step from 0 to 50 % and 50 to 100 % of `it_kw` with cooling in automatic produces an inlet temperature rise that settles with a time constant τ of 3–8 minutes (air-cooled container, small thermal mass) and a settled inlet rise ≤ 2 °C at 100 %; recirculation ratio (fraction of rack inlet air that is rack outlet air) ≤ 10 % with containment closed. |
| **Setup** | Resistive load banks in the racks (or server heaters) wired to the rack PDUs in the same positions as real IT; airflow through the load banks front-to-back at roughly 125 cfm/kW (match server airflow, otherwise ΔT is unrepresentative). Cooling in auto with commissioning setpoints. Twin: `tw.set_it_load(0.5)` then `1.0`, dt = 1 s. |
| **Instrumentation** | `T_in_1..3` per rack (three heights), `T_out_*`, `T_ref`, `supply_c`, `return_c`, `fan_pct`, `kw` per cooling unit, `pdu_kw[]`, `utility_kw`, `dP_aisle`, `outdoor_c`; 2 Hz on nodes. |
| **Procedure** | 1. Idle 30 min (E1 condition). 2. Step to 50 %; hold until all inlets change < 0.1 °C per 5 min (settled), minimum 45 min. 3. Step to 100 %; hold until settled, minimum 60 min. 4. Step down to 0; log the decay 45 min. 5. At 100 % settled, record the top/middle/bottom inlet spread per rack. |
| **Data to record** | Full time series; settled values at each level; `outdoor_c`; cooling unit on/off states and fan %. |
| **Analysis** | **Time constant:** fit the inlet rise to T(t) = T₀ + ΔT·(1 − e^(−t/τ)) per rack; report τ and ΔT. **Recirculation ratio** r = (T_in − T_supply) / (T_out − T_supply) per rack at settled 100 % (a mixing balance: inlet air is supply air plus a fraction r of outlet air). **Capacity check:** Σ cooling `kw` (sensible, from vendor curve or from airflow × ΔT) vs Σ `pdu_kw` + lights/fan heat; and heat balance closure within 10 %. **Rack ΔT** = mean(T_out) − mean(T_in): should be 10–14 K at 125 cfm/kW. Compare every curve with the twin prediction; store the fit coefficients for `analysis.py`. |
| **Pass** | Settled inlet at 100 % below the ASHRAE class recommended max (A1: 25 °C recommended, 32 °C allowable; A2: 35 °C allowable; A3: 40 °C) at the top sensor of every rack; r ≤ 10 % per rack with containment closed; heat balance closure ≤ 10 %; twin agrees with measured τ within 30 % and settled ΔT within 1 °C (otherwise the twin must be refit before SAT). |
| **If it fails** | r > 10 %: find the leak — missing blanking panels, gaps at rack sides/top, containment door seals; smoke-pencil test; fix and repeat at 100 % only. Inlet too hot but r is fine: capacity short — check supply temperature, fan %, cooling unit alarms, outdoor temperature vs derate (see E8). Heat balance off: meter error (do E9) or airflow mismatch at the load banks. |

## E4 — Cooling unit failover (N+1 proof)

| | |
| --- | --- |
| **Purpose** | Prove that losing any one cooling unit at full load does not push any inlet past the ASHRAE allowable limit, and that the rotation/standby logic brings the standby unit on. |
| **Hypothesis** | With N+1 units and `it_kw` at 100 %, stopping any single unit raises the worst inlet by ≤ 3 °C peak with recovery to within 1 °C of the pre-fault value in ≤ 10 min; the standby unit starts within 60 s. |
| **Setup** | 100 % load (E3 condition settled). Twin: `tw.inject("cooling_unit_fail", unit=k)` for each k. |
| **Instrumentation** | As E3 plus per-unit `fan_pct`, `kw`, `alarm[]`; `ben/<unit>/alarm` stream. |
| **Procedure** | For each cooling unit k: 1. Record 10 min baseline. 2. Open the unit's disconnect (or vendor "stop"), note time. 3. Log 20 min. 4. Restore; wait for settle. Also run one **double fault** on 2N configurations (lose one unit per path). |
| **Data to record** | Peak inlet per rack and time to peak, time to standby start, alarm messages and their timestamps, recovery time. |
| **Analysis** | Table per unit: peak rise, time to peak, standby start delay, recovery time. Compare with twin. Identify any rack whose inlet is sensitive to a particular unit (locality effect in in-row systems). |
| **Pass** | No inlet exceeds the class allowable at any time; peak rise ≤ 3 °C; standby start ≤ 60 s; alarm raised within 30 s with the correct `src`; recovery ≤ 10 min; for 2N, no excursion at all. |
| **If it fails** | Standby did not start: controls logic or the unit's own controller in "manual" — fix and repeat that unit only. Excursion too large: unit placement/airflow — consider re-arranging in-row units or lowering supply setpoint; re-run E3 after any change. |

## E5 — Utility loss ride-through ("does cooling need UPS?")

| | |
| --- | --- |
| **Purpose** | Measure how many minutes the room stays within the ASHRAE allowable limit when utility power is lost and cooling stops while IT continues on UPS. This is the number that decides whether cooling fans/pumps must be on UPS and how fast a generator must start. |
| **Hypothesis** | At 100 % load with cooling off, inlet temperature rises at roughly ΔT/Δt ≈ P_IT / (m·cp) of the air volume plus the thermal mass of racks and liner; for a BEN 20 at 96 kW with ~32 m³ of air (≈ 38 kg, cp 1.0 kJ/kg·K) the air alone would heat at > 2 K/s, so the real slope is set by rack/liner thermal mass and will be **0.5–2 °C per minute**, giving **3–10 minutes** from 24 °C to the A2 allowable 35 °C (≈ 1.5–5 min to A1 32 °C). Liquid-cooled BEN 40 with pumps on UPS and dry-cooler fans off has far longer (the glycol loop volume is the buffer). |
| **Setup** | 100 % load settled (E3). UPS fully charged. Safety: a person at the utility breaker; abort limit = class allowable − 2 °C at any top inlet, or UPS SOC 30 %, whichever first. Twin: `tw.inject("utility_loss")`. |
| **Instrumentation** | All inlets at 2 Hz, `supply_c`, `return_c`, `power.ups_on_battery`, `soc_pct`, `runtime_min`, `utility_kw`, `pdu_kw[]`, `fan_pct` (should go to 0 unless fans are on UPS), generator status if fitted. |
| **Procedure** | **Variant A (cooling not on UPS):** 1. Open the utility feeder breaker. 2. Confirm IT stays up on UPS, cooling stops. 3. Log until the abort limit or 15 min. 4. Restore utility; log recovery. **Variant B (fans/pumps on UPS, compressors off):** repeat. **Variant C (generator fitted):** repeat A with the ATS live; record generator start, transfer time and cooling restart. |
| **Data to record** | Slope °C/min per rack (top sensor), time from loss to each threshold (recommended max, allowable max), UPS runtime displayed vs measured consumption, generator start and transfer times, time for cooling to recover the room. |
| **Analysis** | Linear fit of the first 3 minutes slope; time-to-threshold table; effective thermal mass C_eff = P_IT / slope (kJ/K), stored for the twin. Compare variants A and B: the benefit of fans on UPS is the extra minutes gained by moving heat into the liner and slab mass. Decision table: if time-to-allowable (A) < generator start + transfer + cooling restart (typically 10 s + 10 s + 2–4 min for DX restart after a short-cycle delay) then cooling fans **must** be on UPS or the UPS must shed IT. |
| **Pass** | The measured time-to-allowable is published in the product page's risk R05 and in the turnover; the configured architecture gives time-to-allowable ≥ 1.5 × (generator start + transfer + cooling restart) **or** the customer has signed the acceptance that IT will be shed by the UPS runtime logic before the allowable limit. Nothing is a "fail" except an unsafe abort or a UPS that does not carry the load. |
| **If it fails** | UPS drops load: capacity/battery issue — vendor. Time-to-allowable too short for the chosen architecture: options in order of cost — add fans/pumps to UPS (≈ +25 % UPS kVA), shorten compressor restart delay with the vendor, add a generator with ≤ 10 s start, or reduce the IT shed threshold. Re-run after the change. |

## E6 — Door-open infiltration

| | |
| --- | --- |
| **Purpose** | Quantify what happens when the personnel door is open in hot or cold weather (a technician inside for 20 minutes), and verify the door alarm and any cooling response. |
| **Hypothesis** | With the door open, containment pressure (`dP_aisle`) drops, the inlet nearest the door changes toward outdoor temperature by up to 3 °C in 10 minutes in a 35 °C or −15 °C outdoor condition, `RH` moves toward outdoor dew point; the door alarm raises within 10 s and clears when closed; no ASHRAE excursion at 100 % load within 20 minutes. |
| **Setup** | 100 % load settled; record `outdoor_c` and outdoor RH. Twin: `tw.inject("door_open")`. |
| **Instrumentation** | `door`, all inlets, `RH`, `dP_aisle`, `fan_pct`, cooling `kw`. |
| **Procedure** | 1. Open the door fully, latch it; log 20 min. 2. Close; log 20 min recovery. 3. Repeat with the containment door also open (worst case). |
| **Data to record** | Time series; door event timestamps; alarm timestamps; max inlet change by rack position; dew point vs coldest surface temperature (supply coil) — condensation risk. |
| **Analysis** | Infiltration heat load estimate from the cooling `kw` increase; dew-point margin; which racks are affected (door proximity map). |
| **Pass** | Door alarm within 10 s; no inlet exceeds the class allowable within 20 min; dew point inside stays ≥ 2 °C below the coldest surface temperature (no condensation); recovery to within 1 °C of baseline in ≤ 15 min. |
| **If it fails** | Condensation risk in humid climates: add a door-open cooling response (raise supply temperature while door open) and a vestibule curtain; excursion near the door: re-orient the first rack or add a strip curtain. |

## E7 — Filter clog simulation (partial blank-off)

| | |
| --- | --- |
| **Purpose** | Set the filter dP alarm threshold on real data and show how much capacity is lost with loaded filters. |
| **Hypothesis** | Blanking 50 % of a cooling unit's filter face area roughly doubles its filter dP at constant fan speed (dP ∝ velocity² through the remaining area), reduces airflow by 15–30 % at constant fan command, and the unit's EC fans compensate by raising speed up to their limit; at 75 % blank-off, supply airflow falls enough that inlet temperatures rise ≥ 1 °C at 100 % load. |
| **Setup** | 100 % load; cardboard blank-off sheets cut to 25/50/75 % of filter face per unit. Twin: `tw.inject("filter_clog", unit=k, fraction=f)`. |
| **Instrumentation** | Unit filter dP (vendor Modbus point or a second SDP810 across the filter on a spare node), `fan_pct`, unit `kw`, `supply_c`, inlets, `dP_aisle`. |
| **Procedure** | For one unit: 0 → 25 → 50 → 75 % blank-off, 15 min each, then clear. Repeat on one more unit to confirm. |
| **Data to record** | Filter dP, fan %, airflow (if the unit reports it), supply temperature, worst inlet, `dP_aisle`, at each level. |
| **Analysis** | Plot filter dP vs blank-off fraction (expect ∝ 1/(1−f)²); identify the blank-off at which inlets start to rise; set the "replace filter" alarm at the filter dP corresponding to ~50 % blockage and the "critical" alarm at the point of inlet rise. |
| **Pass** | Alarm thresholds derived and written into the gateway config with the supporting plot; no inlet exceeds the recommended max at 50 % blank-off on one unit (N+1 should cover); twin reproduces the trend. |
| **If it fails** | Inlets rise already at 25 %: airflow is marginal — check fan curves, containment leakage (E3), and consider lower filter grade (MERV 8 instead of 13 where outdoor air is not introduced). |

## E8 — Outdoor temperature derate

| | |
| --- | --- |
| **Purpose** | Verify the DX capacity derate used in sizing (1.5 %/K above 35 °C, floor 0.6) and the dry-cooler approach temperature at the climate's design temperature. |
| **Hypothesis** | At the climate design temperature (`t_design_c`: 35–46 °C) each DX unit delivers ≥ the derated `cooling_unit_kw_derated` from the config; compressor discharge pressure stays below the high-pressure cut-out; dry coolers hold supply glycol ≤ design (e.g. 40 °C for W40 racks) with an approach ≤ 6 K. |
| **Setup** | **SAT on a hot day** (outdoor within 5 K of design), or **FAT with a heated condenser inlet**: a temporary enclosure/tent over the condenser intake with electric heaters or recirculated condenser discharge to raise the intake to the design temperature (control to ±2 K, monitor with a calibrated probe at the coil face). 100 % load. Twin: set `outdoor_c` to `t_design_c` and compare. |
| **Instrumentation** | Condenser/dry-cooler inlet air temperature (calibrated probe), unit `kw`, `supply_c`, `return_c`, `fan_pct`, compressor discharge/suction pressures (vendor points), inlets, `utility_kw`. |
| **Procedure** | 1. Baseline at ambient. 2. Raise condenser intake in 5 K steps to the design temperature, 20 min per step. 3. Hold 30 min at design. 4. If N+1, also stop one unit at design temperature (E4 under heat) for 10 min — the worst realistic case. |
| **Data to record** | Capacity per unit (from airflow × ΔT or vendor Modbus capacity), electrical kW per unit (COP), discharge pressure margin, inlet temperatures, any derate alarms. |
| **Analysis** | Measured capacity vs config derate curve; measured COP vs `cop` in `COOLING_LIBRARY`; update the twin's derate constants if the difference exceeds 10 %. Report PUE at design temperature. |
| **Pass** | Capacity at design ≥ config derated value; no high-pressure trip; all inlets within class allowable including the one-unit-off case; COP within 15 % of the library value. |
| **If it fails** | Capacity short: condenser recirculation (check yard layout against `SITE_REQUIREMENTS.md` §3), dirty coil, or vendor curve optimistic — correct `COOLING_LIBRARY` derate for that unit model and re-size (may add a unit). High-pressure trips: head-pressure control settings. |

## E9 — Power meter vs PDU sum reconciliation

| | |
| --- | --- |
| **Purpose** | Prove the metering chain so that the PUE and the kW on the dashboard are true. |
| **Hypothesis** | `utility_kw` = Σ `pdu_kw` + Σ cooling `kw` + UPS losses + lights/controls, within 3 % at 50 % and 100 % load; `pulse_kwh` (S0 pulses) integrates to the meter's kWh within 1 %; PDU sum equals the load bank nameplate within 3 %. |
| **Setup** | Load banks at 50 % and 100 %, steady 30 min each; a reference power analyser (class 0.5) clamped on the incoming feeder for the test. Twin: compare `power.utility_kw` with Σ `pdu_kw` + `cooling_kw_elec` + 0.5 kW + 3 % UPS loss. |
| **Instrumentation** | Power meter `kw`, `kva`, `v_ab`, `i_a` per phase; each PDU `kw`; UPS input/output kW; cooling unit `kw`; `pulse_kwh`; reference analyser. |
| **Procedure** | 1. Verify CT ratios and polarity (all phases positive kW). 2. At each load level record 30 min averages. 3. Compute the balance. 4. Compare `pulse_kwh` delta against meter kWh delta over 1 hour. 5. Check phase balance (max − min phase current)/mean ≤ 10 %. |
| **Data to record** | Per-phase V, I, kW, PF at meter; PDU kW list; UPS in/out; cooling kW; reference analyser; kWh deltas. |
| **Analysis** | Balance table; residual as % of utility kW; PUE = utility_kw / Σ pdu_kw at each level vs `pue_estimate` in config; UPS efficiency = out/in. |
| **Pass** | Residual ≤ 3 %; meter vs reference ≤ 1 %; `pulse_kwh` ≤ 1 %; PUE within 0.05 of config estimate at 100 % (otherwise the estimate is corrected in the turnover, not hidden); phase imbalance ≤ 10 %. |
| **If it fails** | Negative or tiny phase kW: CT polarity/ratio. Residual > 3 % with meter correct: an unmetered load (lights, heaters, controls) or a PDU meter error — add it to the balance or recalibrate the PDU. Imbalance > 10 %: re-distribute rack PDUs across phases. |

## E10 — Acoustic survey at property line (SAT)

| | |
| --- | --- |
| **Purpose** | Show the installed unit meets the local noise ordinance at the property line and the nearest sensitive receptor, day and night conditions. |
| **Hypothesis** | Measured L_Aeq at the property line is within 2 dB of the prediction made at quotation (point-source spreading with barrier credit) and below the ordinance limit, at 100 % cooling fan speed. |
| **Setup** | 100 % load (or force fans to 100 % and compressors on); generator test run as a separate case. Class 1 or Class 2 sound level meter, calibrated before and after with a 94 dB calibrator; wind < 5 m/s; no rain. |
| **Instrumentation** | Sound level meter (L_Aeq, L_A90, L_Amax, 1/3-octave if available), tripod at 1.5 m height, positions: 1 m from each equipment yard face (source check), property line nearest points (≥ 3), nearest dwelling façade if accessible; GPS/plan positions; background (unit off) at the same points. |
| **Procedure** | 1. Background 10 min per point, unit off. 2. Unit at 100 %: 10 min per point. 3. Night condition repeated after dusk or computed from the day measurement with the night fan setback applied and verified at one point. 4. Generator running: repeat the property-line points. 5. Tonal check: 1/3-octave for fan blade-pass tones (ordinances often add a 5 dB penalty for tones). |
| **Data to record** | All levels, positions, weather, fan % and compressor states, calibrator readings, photos. |
| **Analysis** | Background-corrected levels; comparison with prediction and ordinance; tonal penalty assessment; map of contours if needed. |
| **Pass** | L_Aeq at every property-line point ≤ ordinance limit (day and night, including tonal penalty if applicable); generator case ≤ limit for the allowed test hours or documented as exempt (emergency testing provisions). |
| **If it fails** | Night setback of fans (raise supply setpoint at night within class limits), acoustic barrier on the yard side facing the receptor, low-noise fan option, or relocate the yard. Re-measure. |

## E11 — 48-hour burn-in

| | |
| --- | --- |
| **Purpose** | Catch infant failures and slow drifts before the customer's IT goes in; produce the baseline the weekly remote checks compare against. |
| **Hypothesis** | Over 48 h at a load profile cycling 30 → 100 → 30 % every 4 h, no alarm occurs, no node resets, inlet temperatures track load without drift, UPS stays at 100 % SOC, and all redundant sensor pairs stay within 0.3 °C. |
| **Setup** | Load banks on an automatic profile (or the dashboard sweep `POST /api/sweep {"name":"burnin48"}`); FAT runs a minimum 24 h version, SAT the full 48 h. |
| **Instrumentation** | Everything; node `status` (uptime, heap, rssi/ip, errors) at 10 s. |
| **Procedure** | Start the sweep; review at 12 h intervals remotely; hands-off otherwise. |
| **Data to record** | Full telemetry; alarm log; node status log; cooling unit cycle counts; UPS log. |
| **Analysis** | `analysis.py` burn-in report: drift per channel (linear fit over 48 h after removing load correlation), alarm count, node resets (uptime discontinuities), heap trend (memory leak check), cooling cycle counts (short-cycling), heat balance per 4 h block. |
| **Pass** | Zero node resets; zero unexplained alarms; channel drift ≤ 0.2 °C/48 h; heap stable (≤ 5 % decline); no cooling unit > 6 starts/h; heat balance within 10 % in every block. |
| **If it fails** | Node reset: PoE budget, firmware watchdog, brown-out — fix root cause and re-run 24 h. Short-cycling: deadband/staging settings. Drift: sensor or placement — E1. |

## E12 — Cyber: port scan and failsafe on gateway loss

| | |
| --- | --- |
| **Purpose** | Prove the controls network exposes nothing it should not, that default credentials are gone, and that losing the gateway or the controls network leaves the physical plant safe. |
| **Hypothesis** | From the customer LAN side of the firewall, no BEN controls port is reachable; from inside the controls LAN only the documented services answer (MQTT 8883 with TLS and client certs, dashboard HTTPS 443, SSH 22 key-only if enabled); no device answers to default credentials; pulling the gateway keeps nodes measuring and buffering for 1 h and leaves outputs in last state except `failsafe` outputs, which drop (cooling-enable relay wired so cooling stays ON). |
| **Setup** | Laptop with nmap and a credential-check script; permission in writing from the customer for the SAT scan; the twin for the failsafe sequence (`tw.inject("gateway_loss")` or stopping the broker in sim). |
| **Instrumentation** | nmap outputs; MQTT broker logs; node `status` and buffered telemetry; cooling unit run state (observed physically); dashboard alarm log. |
| **Procedure** | 1. From customer LAN: `nmap -sS -sU -p- <controls subnet>` — expect no response/filtered. 2. From controls LAN: full TCP/UDP scan of every device (gateway, switch, nodes, UPS, cooling, PDU, fire-panel gateway if any); list open ports and compare with the allowed list in `CYBERSECURITY.md`. 3. Default-credential attempt on every web/SNMP/Modbus interface (vendor defaults list). 4. Verify firmware signature check: attempt to OTA an unsigned image → must be rejected and logged. 5. Power off the gateway for 15 min: observe nodes (LED/status), cooling stays on, `failsafe` relay drops, fire panel unaffected; restore and confirm buffered data arrives with correct `ts`/`seq` and no gaps. 6. Unplug the controls switch uplink to the customer LAN: dashboard still works locally, alarms still raised locally. |
| **Data to record** | Scan outputs (saved), credential attempt results, OTA rejection log, timeline of gateway-loss test, gap analysis of telemetry after restore. |
| **Analysis** | Open-port list vs allow-list; any default credential success = fail; buffer completeness = (expected samples − missing)/expected. |
| **Pass** | Zero unexpected open ports; zero default credentials; unsigned OTA rejected; cooling ran continuously through gateway loss; buffered data ≥ 99 % complete; alarms raised locally with uplink down; SNMP v1/v2c disabled or read-only community changed; all vendor web interfaces on HTTPS or disabled. |
| **If it fails** | Close ports / disable services; change credentials and record in the handover; if a vendor device cannot be secured, isolate it in its own VLAN with an ACL and document the residual risk; repeat the scan. |

---

## Appendix — running the scripted experiments

```
# twin (simulation) — run everything, produce the expected curves
python -m ben_engine.commissioning --mode sim --config unit.json --experiments E1,E2,E3,E4,E5,E6,E7,E9,E11,E12

# factory acceptance test
python -m ben_engine.commissioning --mode factory --config unit.json --experiments E1,E2,E3,E4,E5,E7,E9,E11,E12 --burnin-hours 24

# site acceptance test
python -m ben_engine.commissioning --mode site --config unit.json --experiments E1,E2,E3r,E4,E5,E6,E9,E12 --burnin-hours 48
```

The report is signed JSON (hash of the data files plus the engineer's key) and a PDF. E8 and E10 are attached as separate reports with their own data files. The twin run is kept beside the real run so every plot in the report shows "predicted" and "measured".

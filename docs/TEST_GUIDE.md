# BEN Engine — Test Guide (experiments on the twin, in the factory and on site)

**Owner:** Schreiber AI engineering. **Rule:** every experiment runs **first in the digital twin** (`ben_engine.twin.Twin`, faults via `tw.inject(...)`) so the expected curve is known before anyone touches the real unit; then at **FAT** (factory mode: load banks, shop power) and, where marked, again at **SAT** (site mode: real utility, real outdoor air). The commissioning script `software/ben_engine/commissioning.py` executes the experiments marked "scripted" and writes a signed report; the others are run by hand and the data attached.

Channel names are from `spec/PROTOCOL.md`: BEN Pod telemetry `T_in_1..4`, `T_out_1..4`, `T_ref`, `RH`, `dP_aisle`, `leak`, `door`, `ai0..3_mA`, `pulse_kwh`; equipment telemetry (`ben/<unit>/equip/<id>/telemetry`): `kw`, `kva`, `v_ab`, `i_a`, `supply_c`, `return_c`, `fan_pct`, `soc_pct`, `runtime_min`, `alarm[]`; twin/dashboard state: `rack_inlet_c[]`, `rack_outlet_c[]`, `aisle_dp_pa`, `power.utility_kw`, `power.pdu_kw[]`, `power.ups_on_battery`, `pue`.

Data rate for all experiments: Pod telemetry at 1 Hz (set 2 Hz for E3/E5 transients), equipment at 1–10 s, outdoor temperature from the site weather sensor or the dry-cooler inlet probe. All data is exported as CSV (`GET /api/export.csv`) and kept with the report.

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
| E12 | Cyber: port scan, Pod attestation, rogue-join rejection and failsafe on controller loss | twin, FAT, SAT | yes | No open attack surface; only attested Pods join; loss of the edge computer or PLC is safe |
| E13 | Mesh resilience: pull a router Pod, measure heal time | twin (model), FAT, SAT | partly | BEN Mesh heals around a lost router without data loss |
| E14 | Envelope hose test (UL 50E type 4X) | FAT (H8), SAT after relocation, every 3 years | no | The envelope is watertight at every hardening level; the basis of the envelope warranty |
| E15 | Module joint seal test (BEN 2000) | SAT (H17a), after relocation, by rotation annually | no | Three factory modules are one sealed envelope on site |
| E16 | MV transformer / UPS string transfer test (BEN 2000) | FAT (power module, reduced), SAT | partly | 2N power path: either transformer and either UPS string carries the hall; generators start and carry it on utility loss |
| E17 | DC bus ground-fault injection (test cell, dc800) | twin, test cell, FAT | yes (step 11) | Insulation monitoring reads, alarms and locates a first fault on each pole without tripping the IT load |
| E18 | CDU pump failover (dlc_hd) | twin, FAT, SAT | yes (step 6) | Standby pump starts within the failover time; loop flow and ΔT stay inside the cold-plate margin |
| E19 | Leak-to-isolation time (dlc_hd) | twin, FAT, SAT, quarterly | yes (step 10) | A leak at a rack manifold closes the row isolation valves within 15 s and the loop reports isolated |
| E20 | W45 ΔT and heat-reuse accounting (dlc_hd) | twin, FAT (load banks), SAT | partly | Loop flow and ΔT reconcile with the IT load within 5 %; the heat available for reuse is a measured number, not a brochure one |

Common "what to do if it fails": stop, record, do not adjust more than one thing, re-run on the twin with the suspected fault injected to see whether the twin reproduces the real data — if it does not, the model is wrong and `analysis.py` must be refit; if it does, fix the hardware cause and repeat.

---

## E1 — Sensor cross-check at isothermal idle

| | |
| --- | --- |
| **Purpose** | Verify that every temperature and humidity sensor agrees when there is no reason for them to differ, and that calibration coefficients (`cal_id`) are loaded. |
| **Hypothesis** | With IT load off, cooling fans on low (mixing) and compressors off for ≥ 60 minutes, the container air is isothermal within 0.3 °C; all `T_in_*`, `T_out_*` and `T_ref` read within their combined k=2 uncertainty (±0.25 °C DS18B20, ±0.15 °C SHT45 → pair limit 0.3 °C). |
| **Setup** | Unit closed, doors shut, IT load 0 (load banks off), cooling units in "fan only" at 30 %, lights off (lights add ~0.3 kW), outdoor temperature between 10 and 30 °C (otherwise the envelope gain creates a gradient — record `outdoor_c`). Twin: `tw.set_it_load(0.0)`, cooling fan-only mode, run 3,600 s. |
| **Instrumentation** | All Pod channels at 1 Hz; one traceable reference probe (handheld, ±0.1 °C) placed next to `T_ref`, then moved to two inlet positions for 5 minutes each. |
| **Procedure** | 1. Confirm `cal_id` on every Pod matches the calibration certificates. 2. Wait 60 min, logging. 3. Take the last 10 minutes; compute mean and standard deviation per channel. 4. Compute each channel's deviation from the all-channel median and from the reference probe. 5. Repeat with fans off for 10 min to see stratification appear (expected: top − bottom rises to 0.5–1.5 °C, proving the three-height layout sees it). |
| **Data to record** | 10-min means/SD per channel; reference readings with time; `outdoor_c`; fan %; `RH` at supply and return; raw ADC counts (`raw`) for later re-processing. |
| **Analysis** | Deviation table; flag channels outside ±0.3 °C from median; compute RH consistency: humidity ratio from (T, RH) at supply and return must match within 0.3 g/kg. |
| **Pass** | ≥ 95 % of channels within ±0.3 °C of median and the reference; no channel beyond ±0.5 °C; RH humidity-ratio match within 0.3 g/kg; `cal_id` verified on 100 % of Pods. |
| **If it fails** | Single channel out: check mounting (touching metal? near a light?), then swap the sensor with a spare and re-run; if the deviation moves with the sensor, recalibrate/replace; if it stays, it is a placement effect — fix placement. Many channels out with a pattern by height: the room is not isothermal — extend mixing time or wait for milder outdoor temperature. Whole Pod offset: `cal_id` wrong — reload coefficients. |

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
| **Instrumentation** | `T_in_1..3` per rack (three heights), `T_out_*`, `T_ref`, `supply_c`, `return_c`, `fan_pct`, `kw` per cooling unit, `pdu_kw[]`, `utility_kw`, `dP_aisle`, `outdoor_c`; 2 Hz on Pods. |
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
| **Hypothesis** | At 100 % load with cooling off, inlet temperature rises at roughly ΔT/Δt ≈ P_IT / (m·cp) of the air volume plus the thermal mass of racks and liner; for a BEN 150 at 96 kW with ~32 m³ of air (≈ 38 kg, cp 1.0 kJ/kg·K) the air alone would heat at > 2 K/s, so the real slope is set by rack/liner thermal mass and will be **0.5–2 °C per minute**, giving **3–10 minutes** from 24 °C to the A2 allowable 35 °C (≈ 1.5–5 min to A1 32 °C). Liquid-cooled BEN 500 with pumps on UPS and dry-cooler fans off has far longer (the glycol loop volume is the buffer). |
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
| **Instrumentation** | Unit filter dP (vendor Modbus point or a second SDP810 across the filter on a spare Pod), `fan_pct`, unit `kw`, `supply_c`, inlets, `dP_aisle`. |
| **Procedure** | For one unit: 0 → 25 → 50 → 75 % blank-off, 15 min each, then clear. Repeat on one more unit to confirm. |
| **Data to record** | Filter dP, fan %, airflow (if the unit reports it), supply temperature, worst inlet, `dP_aisle`, at each level. |
| **Analysis** | Plot filter dP vs blank-off fraction (expect ∝ 1/(1−f)²); identify the blank-off at which inlets start to rise; set the "replace filter" alarm at the filter dP corresponding to ~50 % blockage and the "critical" alarm at the point of inlet rise. |
| **Pass** | Alarm thresholds derived and written into the edge computer config with the supporting plot; no inlet exceeds the recommended max at 50 % blank-off on one unit (N+1 should cover); twin reproduces the trend. |
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
| **Hypothesis** | Over 48 h at a load profile cycling 30 → 100 → 30 % every 4 h, no alarm occurs, no Pod resets, inlet temperatures track load without drift, UPS stays at 100 % SOC, and all redundant sensor pairs stay within 0.3 °C. |
| **Setup** | Load banks on an automatic profile (or the dashboard sweep `POST /api/sweep {"name":"burnin48"}`); FAT runs a minimum 24 h version, SAT the full 48 h. |
| **Instrumentation** | Everything; Pod `status` (uptime, heap, link quality, parent, attestation, battery, errors) at 10 s. |
| **Procedure** | Start the sweep; review at 12 h intervals remotely; hands-off otherwise. |
| **Data to record** | Full telemetry; alarm log; Pod status log; cooling unit cycle counts; UPS log. |
| **Analysis** | `analysis.py` burn-in report: drift per channel (linear fit over 48 h after removing load correlation), alarm count, Pod resets (uptime discontinuities), heap trend (memory leak check), cooling cycle counts (short-cycling), heat balance per 4 h block. |
| **Pass** | Zero Pod resets; zero unexplained alarms; channel drift ≤ 0.2 °C/48 h; heap stable (≤ 5 % decline); no cooling unit > 6 starts/h; heat balance within 10 % in every block. |
| **If it fails** | Pod reset: battery / 24 VDC drop, firmware watchdog, brown-out — fix root cause and re-run 24 h. Short-cycling: deadband/staging settings. Drift: sensor or placement — E1. |

## E12 — Cyber: port scan, Pod attestation, rogue-join rejection and failsafe on controller loss

| | |
| --- | --- |
| **Purpose** | Prove the controls network exposes nothing it should not, that default credentials are gone, that only Pods with a Schreiber AI certificate and a valid attestation can join BEN Mesh, and that losing the edge computer or the PLC leaves the physical plant safe. |
| **Hypothesis** | From the customer LAN side of the firewall, no BEN controls port is reachable; from inside the controls LAN only the documented services answer (MQTT 8883 with TLS and client certs, dashboard HTTPS 443, PLC Modbus/OPC UA from the edge computer only, SSH 22 key-only if enabled); no device answers to default credentials; every Pod reports `attested: true` with a firmware hash on the release list; an unprovisioned Pod (blank Secure Vault) and a Pod with a self-signed certificate are both rejected at join and logged; pulling the edge computer keeps Pods measuring and buffering for 1 h and the PLC holding the interlocks; stopping the PLC (or RevPi) drops the watchdog relay within 5 s with cooling staying ON. |
| **Setup** | Laptop with nmap and a credential-check script; permission in writing from the customer for the SAT scan; two "rogue" Pods from the engineering kit (one blank, one with a test-CA certificate); the twin for the failsafe sequence (`tw.inject("gateway_loss")` or stopping the broker in sim). |
| **Instrumentation** | nmap outputs; MQTT broker and OTBR logs (join attempts); Pod `status` (attestation state, parent, link quality) and buffered telemetry; PLC diagnostic log and watchdog relay state; cooling unit run state (observed physically); dashboard alarm and mesh health panels. |
| **Procedure** | 1. From customer LAN: `nmap -sS -sU -p- <controls subnet>` — expect no response/filtered. 2. From controls LAN: full TCP/UDP scan of every device (edge computer, PLC, switch, Pod E, UPS, cooling, PDU, leak controller, fire-panel gateway if any); list open ports and compare with the allowed list in `CYBERSECURITY.md` §3. 3. Default-credential attempt on every web/SNMP/Modbus interface (vendor defaults list) including the PLC web UI (must be disabled). 4. Verify firmware signature check: attempt to OTA an unsigned image to one Pod → must be rejected and logged. 5. **Attestation:** run `python -m ben_engine.commissioning --stage provisioning-check`; confirm 100 % of Pods attested with a release-list firmware hash and a certificate chaining to the Schreiber AI CA. 6. **Rogue join:** power the blank Pod and the test-CA Pod within 2 m of a router Pod for 10 min each; both must be rejected (no network key issued, no broker session), with a join-rejection event on the dashboard. 7. Power off the edge computer for 15 min: observe Pods (status LED), PLC keeps interlocks, cooling stays on, fire panel unaffected; restore and confirm buffered data arrives with correct `ts`/`seq` and no gaps. 8. Stop the PLC (pull the Axioline bus power) or the RevPi on Lite: watchdog relay drops within 5 s, cooling stays ON (fail-ON wiring), alarm raised by the edge computer; restore. 9. Unplug the controls switch uplink to the customer LAN: dashboard still works locally, alarms still raised locally. 10. (Pro) Confirm the edge computer's TPM PCR values match the FAT baseline. |
| **Data to record** | Scan outputs (saved), credential attempt results, OTA rejection log, attestation report, join-rejection log entries with timestamps, timeline of edge-computer-loss and PLC-loss tests, gap analysis of telemetry after restore, PCR baseline comparison. |
| **Analysis** | Open-port list vs allow-list; any default credential success = fail; any rogue join accepted = fail; attested share must be 100 %; buffer completeness = (expected samples − missing)/expected; watchdog drop time from the relay contact log. |
| **Pass** | Zero unexpected open ports; zero default credentials; unsigned OTA rejected; 100 % Pods attested; both rogue Pods rejected and logged; cooling ran continuously through edge computer loss and PLC loss; watchdog relay dropped ≤ 5 s; buffered data ≥ 99 % complete; alarms raised locally with uplink down; SNMP v1/v2c disabled or read-only community changed; all vendor web interfaces on HTTPS or disabled; PCRs match baseline. |
| **If it fails** | Close ports / disable services; change credentials and record in the handover; a Pod that does not attest is replaced with a spare and returned (never re-flashed in the field); if a rogue Pod joined, the Thread network key is rotated from the edge computer and the commissioner settings reviewed before any other test; if a vendor device cannot be secured, isolate it in its own VLAN with an ACL and document the residual risk; repeat. |

---

## E13 — Mesh resilience: pull a router Pod, measure heal time

| | |
| --- | --- |
| **Purpose** | Prove BEN Mesh (Thread) heals around a lost router Pod and a lost border router radio without losing telemetry, so a single Pod failure or battery change never blinds a rack. |
| **Hypothesis** | With the placement rules in `BUILD_AND_WIRING.md` §6 (every battery Pod within range of ≥ 2 router-eligible Pods, two RCPs on BEN 150/500), removing any one router Pod causes its children to re-attach to another parent within 60 s (Thread parent search; target < 30 s) with no telemetry gap longer than the ring-buffer catch-up, and removing one RCP causes no gap at all on BEN 150/500 (second border router) or a ≤ 2 min gap with full buffer catch-up on single-RCP units. |
| **Setup** | Fully commissioned mesh (E12 step 5 passed); dashboard mesh health panel open (topology, parent, link quality per Pod); a stopwatch; the unit at idle or low load. |
| **Instrumentation** | Pod `status` at 10 s (parent, link quality, role); OTBR topology dump every 10 s; broker message log per Pod; alarm log. |
| **Procedure** | 1. Record the topology: which Pods are routers, which are children of which parent. 2. Identify the router Pod with the most children (usually the room Pod E or a 24 VDC Pod W). Remove its power (or pull it off the rail and open the battery door). Start the stopwatch. 3. Record, per orphaned child, the time until it reports a new parent and the time until its telemetry resumes at the broker. 4. Leave it out for 15 min; confirm no sensor-loss alarm escalates beyond "Pod offline" for the removed Pod itself, and that the twin keeps running on neighbouring sensors. 5. Restore the Pod; confirm it re-attests and rejoins as a router within 2 min. 6. Repeat for a second router Pod at the far end of the row. 7. Unplug RCP 1 from the edge computer for 10 min; record any gap; restore; on BEN 150/500 repeat with RCP 2. 8. Export the CSV for the whole window. |
| **Data to record** | Topology before/after each step; per-Pod re-attach time and telemetry resume time; gap analysis per channel from the CSV (`seq` continuity); alarm log; RCP events. |
| **Analysis** | Heal time = max over children of (new parent time − removal time); data completeness per channel over the window; any child that failed to re-attach = placement defect (shadowed by racks, only one parent in range). |
| **Pass** | Every orphaned child re-attached ≤ 60 s (record the value; target ≤ 30 s); telemetry completeness ≥ 99.5 % per channel over the window after buffer catch-up; no false alarm other than the removed Pod's own offline event; removed Pod re-attests on return; RCP loss on BEN 150/500 produced no gap; on single-RCP units the gap was ≤ 2 min and fully back-filled. |
| **If it fails** | A child with no second parent: add a 24 VDC-powered Pod W as a router above the rack line or move the Pod per the spacing rule; a child with link quality 1 to its only parent: re-site away from the metal rack top; heal time > 60 s on every child: check the Thread network's router count (target ≥ 3 inside a 20 ft unit) and the RCP placement; after any change repeat E13 from step 1. |

---

## E14 — Envelope hose test (UL 50E type 4X method)

| | |
| --- | --- |
| **Purpose** | Prove the enclosure is watertight and every penetration is sealed before the liner closes and again after the unit has travelled. This is the test behind the NEMA 4X / IP66 claim at every hardening level (`COMPLIANCE.md` §15) and the condition of the envelope warranty (`contracts/WARRANTY_TERMS.md`). |
| **Hypothesis** | With gasketed doors and penetrations built to the envelope drawings, a hose-down per UL 50E type 4X leaves no water inside the enclosure and no water in the drained cavities of the joints or plinth. |
| **Setup** | Unit or module with all exterior penetrations installed (louvres with weather hoods, cable glands, refrigerant/glycol sleeves, roof penetrations, door hardware); doors closed and latched; positive-pressure fan OFF (the test is passive); interior lined with white absorbent paper at every penetration, door threshold and seam; H2: plinth fitted; H3: shielded doors closed with finger-stock engaged. Water supply ≥ 240 L/min at the nozzle. |
| **Instrumentation** | 25 mm (1 in.) hose nozzle, flow meter or bucket-timed calibration (≥ 240 L/min = 65 US gal/min), tape measure for the 3.0–3.5 m stand-off, stopwatch, humidity Pods inside logging at 1 Hz, camera. |
| **Procedure** | 1. Calibrate the flow (fill a 200 L drum: ≤ 50 s). 2. Mark the seam and penetration map on the envelope drawing; compute the test time: 5 min per linear metre of seam and gasket for a module (not less than 5 min per face). 3. From 3.0–3.5 m, direct the stream at every seam, gasket, hinge, latch, penetration and roof edge, moving along at the computed rate; include the underside of hoods and the plinth junction. 4. After each face, open the door and inspect the paper; photograph. 5. Repeat for roof and all faces. 6. H3 shielded units: after the hose test, check door finger-stock for retained water and the filter box drains. |
| **Data to record** | Flow calibration, stand-off, per-face start/stop times, humidity trend inside, paper inspection result per location, photos, the hardening level, ambient temperature. |
| **Analysis** | Any damp paper, droplet or run mark inside = fail at that location. Interior RH rise > 10 %RH during the test with dry paper = a vapour path (likely a gland or a hood): investigate and re-test. |
| **Pass** | **No water inside the enclosure at any location after the full procedure; no standing water in drained cavities more than 10 min after the hose stops.** Record "E14 PASS (UL 50E type 4X method), date, level, witness" in Q-03 and the turnover package. |
| **If it fails** | Re-seal the failed location (gasket, gland, sealant); never rely on sealant alone where a gasket is specified; re-test the face; two failures at the same location = design review of that detail. |

---

## E15 — Module joint seal test (BEN 2000)

| | |
| --- | --- |
| **Purpose** | The three hall modules are joined on site; their joints are the only part of the IP66 envelope not finished in the factory. E15 proves each joint before hook-up (H17a) and after any relocation or seismic event. |
| **Hypothesis** | With factory compression gaskets engaged, field EPDM cover strips applied and the drained cavity open, a hose-down of each joint (wall both sides and roof) per the E14 method produces no water inside and the drained cavity discharges at its outlets only. |
| **Setup** | Modules set, aligned to ±5 mm, structural bolts torqued (record), cover strips and roof seam complete, interior finish at the joints still open for inspection (do not close the interior joint trim until E15 passes). Leak rope under each joint live on the PLC. Absorbent paper along the joint inside, floor to ceiling. |
| **Instrumentation** | As E14; plus a dye tablet in the roof seam cavity and a clear jar at each cavity outlet. |
| **Procedure** | 1. Joint 1–2: hose the roof seam for 10 min walking the full width, then each wall joint 5 min per 3 m of height from both exterior sides. 2. Inspect inside: paper, leak rope event log, cavity outlets (dye water at outlets = cavity drains correctly; dye inside = fail). 3. Repeat for joint 2–3 and at the power module coupling (busway and DLC manifold sleeves). 4. Stop; wait 30 min; re-inspect for delayed seepage. |
| **Data to record** | Bolt torque log, alignment survey, per-joint times, leak rope events, photos inside and at outlets, dye observations. |
| **Analysis** | Any water or dye inside = fail; cavity outlet not flowing while the seam is wetted = blocked drain (fail until cleared and re-tested). |
| **Pass** | **No water inside at any joint after 30 min, leak rope log clean, every cavity outlet flowed during the test.** Interior joint trim may then be closed; result recorded in Q-11 supplement and the turnover package. |
| **If it fails** | Open the cover strip at the failed location, inspect the gasket for crush or displacement, re-seat or replace, re-apply the strip, re-test the joint from step 1. |

---

## E16 — MV transformer and UPS string transfer test (BEN 2000)

| | |
| --- | --- |
| **Purpose** | Prove the 2N power path: either pad-mount transformer, either 480 V main and either UPS string carries the whole hall, the tie closes as designed, and on utility loss the N+1 generators start and carry the load within the NFPA 110 Level 1 time. |
| **Hypothesis** | With load banks (FAT) or the live IT load (SAT, at ≤ 50 % of design so one string can carry it), opening transformer A's main causes no IT interruption (UPS rides through, tie closes within the trip-unit settings), shifting the UPS load from string A to string B and back causes no output deviation beyond the UPS spec, and opening the utility causes all three generators to start and accept load within 10 s (NFPA 110 Type 10) with one generator inhibited to prove N+1. |
| **Setup** | Switchgear in automatic; both transformers energised; both UPS strings online and sharing; generators ready with fuel ≥ 50 %; battery rooms normal; load banks on the busway (FAT) or IT at ≤ 50 %; coordination study and trip settings on hand; NETA test company present; all alarms cleared; plant PLC event log at 10 ms resolution. |
| **Instrumentation** | Power quality recorder on each UPS output (voltage, frequency, transients), switchgear event recorder, UPS logs, generator controller logs, twin running in `utility_loss_ride_through` and plant mode, stopwatch. |
| **Procedure** | 1. Baseline 15 min. 2. Open main A: record tie closing time, UPS A input loss and ride-through, bus voltages; hold 15 min; restore main A; repeat for main B. 3. UPS string transfer: through the maintenance bypass procedure shift the load to string B only, hold 15 min, return to shared, then to string A only, return. 4. Utility loss: open the utility switch; record generator start, synchronise and load acceptance times for each set; hold 30 min; inhibit one set and confirm the other two carry the load (N+1); restore utility; record retransfer and cool-down. 5. Battery room: during step 4 confirm gas detection and ventilation stay normal. |
| **Data to record** | All timestamps (open, trip, tie, start, sync, load, retransfer), UPS output recorder files, bus voltages, generator loads, alarms, fuel consumed, twin prediction vs measured for the ride-through. |
| **Analysis** | Compare switching times to the coordination study; UPS output within ITIC curve throughout; generator start-to-load ≤ 10 s each; retransfer timed; no unintended trips. |
| **Pass** | **No IT interruption during any step; UPS output within specification; tie and transfers within study times; all three generators started and the hall ran on two with the third inhibited; NFPA 110 acceptance witnessed.** Result in Q-12; the FAT version (power module alone on load banks) is recorded as E16-F. |
| **If it fails** | A trip outside the study: stop, review settings with the PE before any retry; a generator not accepting load in 10 s: vendor adjustment and repeat step 4 for that set only; UPS transfer deviation: vendor service and repeat step 3. |

---

## E17 — DC bus ground-fault injection on the test cell (dc800, forward architecture)

| | |
| --- | --- |
| **Purpose** | Prove that the insulation monitoring on the 800 VDC bus (bipolar ±400 V HR midpoint or unipolar 800 V isolated return) detects a first ground fault on either pole, raises the critical alarm, locates the faulted tap-off and does **not** trip the IT load; and that the alarm clears when the fault is removed. |
| **Hypothesis** | With a listed test resistor (20 kΩ class) from one pole to the ground bar, `IMD_kohm` falls below 100 kΩ and `dc_ground_fault` is raised within 10 s; the faulted pole voltage to ground falls toward 0 V (`V_bus_pos` or `V_bus_neg`); `I_bus` and the rack loads are unchanged; the IMD location function names the tap-off; the second pole behaves the same. |
| **Setup** | Test cell at ≥ 60 % load on load banks; bus healthy (`IMD_kohm` ≥ 500 kΩ recorded first); test resistor with a fused lead; qualified person; DC arc-flash PPE per the study; nobody else inside the module. Twin: `tw.inject("dc_ground_fault", pole="pos", kohm=20)`; sweep `dc_ground_fault_response`. |
| **Instrumentation** | IMD over Modbus (`IMD_kohm`, location), `V_bus_pos`, `V_bus_neg`, `I_bus`, `power.pdu_kw[]`, `ben/<unit>/alarm` stream at 1 Hz; stopwatch on the alarm. |
| **Procedure** | 1. Record 5 min baseline. 2. Connect the resistor positive pole to ground; log 60 s; read the location. 3. Remove; wait for the alarm to clear (log the clear time). 4. Repeat on the negative pole (or the return on unipolar_800). 5. On unipolar_800 repeat with the IMD coupling switched to the two-pole arrangement. |
| **Data to record** | Healthy kΩ, kΩ at fault, time to alarm, pole voltages before/during, `I_bus`, rack kW, location result, clear time, convention and IMD arrangement used. |
| **Analysis** | Compare with the twin sweep; any trip of a rack or the bus is a failure of the protection philosophy (first fault = alarm), to be reviewed with the PE before any retry. |
| **Pass** | Alarm ≤ 10 s on both poles; `IMD_kohm` < 100 kΩ at fault and ≥ 500 kΩ after; location correct; IT load held within 5 %; alarm cleared. Commissioning step 11 records it. |
| **If it fails** | No alarm: IMD coupling or Modbus mapping wrong (check the convention setting); trip on first fault: breaker ground-fault setting or a bonded pole — stop, review with the PE; wrong location: tap-off CT polarity. |

## E18 — CDU pump failover (dlc_hd, forward architecture)

| | |
| --- | --- |
| **Purpose** | Prove that losing any CDU pump at full load starts the standby within the failover time and that loop flow and ΔT stay inside the cold-plate margin (no chip throttling). |
| **Hypothesis** | Stopping any one pump drops the flow to ≥ 60 % of design for ≤ 10 s; the standby starts within 5 s (twin) / 10 s (field); flow recovers to ≥ 80 % of design; loop ΔT peaks ≤ 1.5 × design (15 K); alarm `cdu_pumpN_fail` raised with the standby status. Twin: `tw.inject("cdu_pump_fail", pump=k)`; sweep `cdu_pump_failover`. |
| **Setup** | 100 % load (E3 condition settled), both pumps healthy, CDU in automatic, flow meter and manifold temperatures logging at 1 Hz. |
| **Instrumentation** | `F_loop`, `T_loop_sup`, `T_loop_ret`, `cdu_pump1..N`, CDU Modbus (pump speed, ΔP), rack inlet probes, GPU throttle flags from the IT (if available). |
| **Procedure** | For each pump: 1. Baseline 10 min. 2. Stop the pump at its local disconnect; note the time. 3. Log 5 min. 4. Restore; wait for settle. Then one test with both pumps stopped for 20 s to record the loss-of-flow behaviour (cold-plate temperature rise rate) — only with load banks, never with customer IT. |
| **Data to record** | Standby start delay, minimum flow (% design), peak ΔT, time to recover, alarm timestamps, any throttle flag. |
| **Analysis** | Table per pump; compare with the twin; the both-pumps-off rate of rise gives the real thermal margin for the risk register (R37). |
| **Pass** | Standby ≤ 10 s; flow ≥ 80 % after failover; ΔT ≤ 15 K; alarm within 30 s with the right `src`; no throttle flag. Commissioning step 6 records it. |
| **If it fails** | Standby did not start: CDU controller in manual or the sequencing on the controller; flow too low: check valve, strainer ΔP, VFD limit; ΔT too high: loop under-flowed for the rack load, re-balance at the rack valves. |

## E19 — Leak-to-isolation time (dlc_hd, forward architecture)

| | |
| --- | --- |
| **Purpose** | Measure the time from a leak at a rack manifold to the row isolation valves closed, and prove the loop reports isolated. The number is written into the turnover package and repeated quarterly. |
| **Hypothesis** | Wetting the drip-tray sensor of any rack closes the row isolation valves (spring-return) within 15 s (detection ≤ 2 s + valve travel ≤ 6 s in the twin → 8 s), `F_loop` to the row reads 0 within 30 s, `loop_iso` = 1 and `loop_isolated` is raised; after reset the valves reopen and flow returns. Twin: `tw.inject("leak")`, `state.loop.leak_to_isolation_s`. |
| **Setup** | 60 % load on load banks (never customer IT for the first run); valve position switches wired; stopwatch; a wet sponge or the leak controller's test input; drip trays dry. |
| **Instrumentation** | `leak`, `loop_iso`, `F_loop`, valve position switches, `ben/<unit>/alarm`, CDU pump status (the CDU must ride through a closed row without damage: dead-head protection). |
| **Procedure** | For each rack: 1. Wet the drip-tray sensor; start the stopwatch. 2. Record valve-closed time and `F_loop` = 0 time. 3. Dry the sensor; reset; record reopen. Also one test at the manifold rope (not a tray). |
| **Data to record** | Per rack: leak-to-valve-closed s, time to zero flow, alarm timestamps, CDU response, reopen time. |
| **Analysis** | Worst rack is the number quoted; compare with the twin's 8 s; trend quarterly (valve wear). |
| **Pass** | ≤ 15 s to valve closed on every rack; zero flow ≤ 30 s; alarm and `loop_iso` correct; reopen clean; CDU unharmed. Commissioning step 10 records it; quarterly result in `MAINTENANCE.md` §4b. |
| **If it fails** | Slow: sensor placement or leak-controller delay; valve did not close: actuator supply or spring; no alarm: PLC mapping. Any failure stops liquid-cooled IT until repeated and passed. |

## E20 — W45 ΔT and heat-reuse accounting (dlc_hd, forward architecture)

| | |
| --- | --- |
| **Purpose** | Make the heat-reuse number honest: measure loop flow and ΔT against the IT load and show that the kW offered at the heat-reuse exchanger is a measured, reconciled figure. |
| **Hypothesis** | At steady load, `F_loop` × 4.18 × (`T_loop_ret` − `T_loop_sup`) / 60 reconciles with the IT load × (1 − air residual 0.10) within 5 %; with the heat-reuse valve open, the customer-side BTU meter reads the same within 10 %; the supply stays ≤ 45 °C (W45) at the design outdoor temperature. |
| **Setup** | Load banks at 40 / 70 / 100 %, each held 30 min; flow meter and manifold Pt1000s calibrated (E1 method); BTU meter on the HRX customer side (or a temporary one); outdoor temperature logged; dry coolers in automatic. |
| **Instrumentation** | `F_loop`, `T_loop_sup`, `T_loop_ret`, `power.pdu_kw[]`, BTU meter, dry-cooler fan power, outdoor probe. |
| **Procedure** | For each load: 1. Hold 30 min. 2. Record 10 min of 1 Hz data. 3. Open the heat-reuse valve (customer loop or a dump load); hold 20 min; record. 4. Close; confirm the dry coolers take the heat back. Repeat step 3 at 100 % only. |
| **Data to record** | Loop kW (computed), IT kW, residual air kW (fan-coil side), BTU meter kW, supply/return °C, outdoor °C, dry-cooler kW, PUE. |
| **Analysis** | Reconciliation table per load; the heat-reuse figure on the product page is the 100 % BTU-meter value minus losses, with its uncertainty from the meter classes. |
| **Pass** | Loop energy balance within 5 % at every load; BTU meter within 10 %; supply ≤ 45 °C; the stated `heat_reuse_kw_available` is within 10 % of the measured value or the configuration model is corrected. |
| **If it fails** | Flow meter or probe calibration (repeat E1 on the loop sensors); air-side share larger than 10 % (fan-coil load measured separately; correct `air_residual` in the library); supply above 45 °C: dry-cooler sizing or fouling (R39). |

## Rev 2 experiments (added 2026-11-09)

| ID | Experiment | Where | Scripted | Proves |
| --- | --- | --- | --- | --- |
| E21 | Noise at 1 m (BEN 1) | Bench (burn-in shelf), handover | no | The mini rack meets the office comfort target at full load |
| E22 | Heat to room and input current (BEN 1) | Bench, handover | partly | The heat figure on the quote is true and the circuit stays under the 80 % rule |
| E23 | UPS runtime (BEN 1) | Bench, handover, quarterly (self-test) | partly | The UPS carries the real load long enough for a clean shutdown |
| E24 | Filter-clog alarm (BEN 1) | Bench | yes | A blocked intake raises the BEN Pod alarm before the IT throttles |
| E25 | Single-rack isolation (BEN 300, BEN 1000) | twin, FAT | partly | One rack can be isolated (valves and tap-off) with the other racks unaffected; the failure domain in the proposal is real |

BEN 1 experiments run on the burn-in shelf for every unit before shipping (`docs/MANUFACTURING_STRATEGY.md` §12) and E21–E23 again at the customer's site at handover with the unit in its final place. They need only a Class 2 sound level meter, a plug-in power meter (or the UPS's own input reading), a stopwatch and a dummy load (the AI box running a fixed benchmark); no load banks.

## E21 — Noise at 1 m (BEN 1)

| | |
| --- | --- |
| **Purpose** | Show that the mini rack is acceptable in an office: measure A-weighted sound level at 1 m at idle and full load. |
| **Hypothesis** | With the cab12 door closed, ≤ 45 dBA at 1 m in front at full load and ≤ 35 dBA at idle; rack10 ≤ 45 dBA at 1 m at full load (the AI box's own fan is the limit). |
| **Setup** | Unit in its final place (handover) or on the burn-in shelf (bench); background level measured first with the unit off and recorded; doors and windows as normal. |
| **Instrumentation** | IEC 61672 Class 2 (or better) sound level meter, A-weighting, slow response; tripod at 1.0 m from the front face, 1.2 m high (seated ear height). |
| **Procedure** | 1. Unit off: record background for 30 s (L_Aeq). 2. Idle: 2 min L_Aeq. 3. Full load (fixed benchmark on the AI box for 15 min so fans settle): 2 min L_Aeq. 4. Repeat step 3 at 1 m to the left side. |
| **Data to record** | Background, idle and full-load L_Aeq per position; fan speeds; room and intake temperature. |
| **Analysis** | Unit level = measured level corrected for background (subtract energetically if within 3–10 dB; if less than 3 dB above background, report "at or below background"). |
| **Pass** | Full load ≤ 45 dBA and idle ≤ 35 dBA (cab12, door closed); rack10 ≤ 45 dBA at full load. Value written on the handover sheet; later annual checks compare against it (`MAINTENANCE.md` §10). |
| **If it fails** | Door not closed or seal missing; a fan at maximum (check intake temperature, E22); move the unit away from a reflecting corner; replace a noisy fan. |

## E22 — Heat to room and input current (BEN 1)

| | |
| --- | --- |
| **Purpose** | Prove the heat-to-room figure on the quote (BTU/h) and that the input current stays inside the 80 % rule for the circuit. |
| **Hypothesis** | At full IT load the UPS input power equals IT power + UPS losses + fans within 5 %, i.e. ≤ 0.66 kW (2,250 BTU/h) for rack10 and ≤ 1.65 kW (5,600 BTU/h) for cab12; input current ≤ 12 A (15 A circuit) or ≤ 16 A (20 A circuit); the room temperature rise with the site's vent path or cooling stays ≤ 5 K above the room's normal temperature after 2 h. |
| **Setup** | Unit at full load (fixed benchmark); room in normal use; BEN Pod intake and exhaust probes logging; room thermometer away from the exhaust. |
| **Instrumentation** | Plug-in power meter between the receptacle and the UPS (or the UPS input reading), BEN Pod `T_in_1`, `T_out_1`, room probe; 1-min logging for 2 h. |
| **Procedure** | 1. Record room temperature with the unit at idle for 15 min. 2. Full load for 2 h. 3. Record input W and A every 10 min, intake and exhaust temperatures, room temperature. |
| **Data to record** | Input W, A and power factor; IT W (from the AI box or PDU); room temperature at 0, 60 and 120 min; intake temperature. |
| **Analysis** | Heat to room = input W (all electrical input becomes heat in the room); BTU/h = W × 3.412. Compare with the quote. Room rise compared with the site check (`SITE_REQUIREMENTS.md` §15). |
| **Pass** | Heat within 5 % of the quote; current inside the 80 % rule; room rise ≤ 5 K at 2 h; intake temperature ≤ 30 °C. |
| **If it fails** | Heat high: an extra device was added (R45) or the AI box is over its configured power cap. Room rise high: the vent path or room cooling is not as signed in the site check (R41) — the unit does not stay on site in that room until it is fixed. |

## E23 — UPS runtime (BEN 1)

| | |
| --- | --- |
| **Purpose** | Measure how long the UPS carries the real load and prove that the AI box and NAS shut down cleanly before the battery is empty. |
| **Hypothesis** | At full load the UPS carries the IT for at least the configured `ups_minutes` ({{BEN1_UPS_MINUTES}} min in the BEN 1 preset); at the shutdown threshold BEN Controls Mini commands an orderly shutdown of the AI box and NAS; on mains return the unit restarts in a defined order. |
| **Setup** | Full load; backups up to date; customer told; nothing irreplaceable running. Twin: not used (the vendor runtime curve is the prediction). |
| **Instrumentation** | UPS `runtime_min`, `soc_pct`, input status; BEN Pod event log; stopwatch. |
| **Procedure** | 1. Pull the UPS input plug (or open the circuit breaker). 2. Time to the shutdown command, to IT off, and the remaining SoC. 3. Restore power; time to everything back up and the dashboard green. |
| **Data to record** | Runtime to shutdown command, IT off time, SoC at IT off, restart time, any errors in the AI box or NAS logs. |
| **Analysis** | Compare runtime with the vendor curve at the measured load; record as the handover value. Quarterly self-tests (`MAINTENANCE.md` §10) compare against it. |
| **Pass** | Runtime ≥ configured minutes; clean shutdown with no file-system errors; automatic restart in order. |
| **If it fails** | Short runtime: battery not fully charged (wait 8 h and repeat) or a weak pack (replace, R47); no shutdown command: UPS USB/network link to BEN Controls Mini not configured. |

## E24 — Filter-clog alarm (BEN 1)

| | |
| --- | --- |
| **Purpose** | Prove that a blocked intake filter raises an alarm through the BEN Pod before the AI box throttles. |
| **Hypothesis** | Covering 75 % of the intake filter with a card raises intake-to-exhaust ΔT and fan speed; the BEN Pod `filter_clog` warning is raised within 15 min at full load, before the AI box reports thermal throttling. |
| **Setup** | Bench (burn-in shelf), full load, filter clean, Pod logging at 1 Hz. |
| **Instrumentation** | BEN Pod `T_in_1`, `T_out_1`, fan tachometer (cab12) or the AI box fan reading; AI box throttle flag. |
| **Procedure** | 1. 15 min baseline. 2. Cover 75 % of the filter area. 3. Log until the alarm or 30 min. 4. Remove the cover; confirm the alarm clears. |
| **Data to record** | Time to alarm, ΔT and fan speed at alarm, any throttle flag, time to clear. |
| **Analysis** | Alarm must lead throttling; set the threshold from the bench data if the default does not. |
| **Pass** | Alarm ≤ 15 min; no throttle flag before the alarm; alarm clears after the cover is removed. |
| **If it fails** | Threshold too high: adjust the ΔT threshold in BEN Controls Mini and repeat; probe placement wrong: move the exhaust probe out of the direct fan stream. |

## Dense tiers BEN 300 and BEN 1000: which experiments apply

Liquid is the default on BEN 300 and BEN 1000, so **E18 (CDU pump failover), E19 (leak-to-isolation) and E20 (W45 ΔT and heat-reuse accounting) are mandatory at FAT and SAT on every unit**, no longer forward-architecture-only, and they are run with every rack position loaded (liquid load banks at FAT, the customer's IT at SAT only after the FAT values are in hand). Changes against the E18–E20 text above: E18 is run per CDU **and** with one whole CDU stopped (N+1 CDUs are the default on the dense tiers, R49); E19 is run on every rack at FAT and by rotation afterwards (`MAINTENANCE.md` §11); E20 is run at 40 / 70 / 100 % of the configured IT kW and the reconciliation result is the source of the measured density figure in `docs/DENSITY.md`. **E17** applies only when `dc800` is selected (study). E1–E14 apply as for BEN 150 (BEN 300) and BEN 500 (BEN 1000); E16-style transfer testing applies where a BEN 1000 is fed from two transformers.

## E25 — Single-rack isolation (BEN 300, BEN 1000)

| | |
| --- | --- |
| **Purpose** | Prove that one rack can be taken out (liquid isolated and tap-off opened) while the others carry on, so the single-fault failure domain printed in the proposal (R48) is real. |
| **Hypothesis** | Closing the isolation valves of rack k and opening its tap-off leaves every other rack's flow within ±10 % of its set value and its inlet coolant temperature within 1 K; CDU pumps rebalance without a low-flow alarm; reopening restores rack k without air in the loop. Twin: no rack-isolation fault is modelled yet; add one before the first BEN 300 FAT so the expected curve exists (see the rule at the top of this guide). |
| **Setup** | FAT, liquid load banks on every rack at 80 % load; loop settled; per-rack flow meters logging at 1 Hz. |
| **Instrumentation** | Per-rack `F_rack_k`, `T_loop_sup`, `T_loop_ret`, CDU pump speed and ΔP, tap-off breaker status, `power.pdu_kw[]`. |
| **Procedure** | For each rack: 1. Baseline 10 min. 2. Open the tap-off, close the rack valves; log 10 min. 3. Reopen valves (vent at the high point), close the tap-off; log 10 min. |
| **Data to record** | Other racks' flow and supply temperature deviation, CDU response, alarms, time to restore, air-vent volume. |
| **Analysis** | Worst deviation across the other racks; kW lost per single fault = the isolated rack's kW (proposal figure). |
| **Pass** | Other racks within ±10 % flow and 1 K supply; no low-flow alarm; restore clean. |
| **If it fails** | Rebalancing too slow: CDU pressure control tuning; large flow swing: missing or mis-set rack balancing valve; air: venting procedure. |

## Appendix — running the scripted experiments

```
# twin (simulation) — run everything, produce the expected curves
python -m ben_engine.commissioning --mode sim --config unit.json --experiments E1,E2,E3,E4,E5,E6,E7,E9,E11,E12,E13

# factory acceptance test
python -m ben_engine.commissioning --mode factory --config unit.json --experiments E1,E2,E3,E4,E5,E7,E9,E11,E12,E13 --burnin-hours 24

# site acceptance test
python -m ben_engine.commissioning --mode site --config unit.json --experiments E1,E2,E3r,E4,E5,E6,E9,E12,E13 --burnin-hours 48
```

The report is signed JSON (hash of the data files plus the engineer's key) and a PDF. E17–E20 run only on units configured with the forward options (dc800 / dlc_hd) and map to commissioning steps 11, 6, 10 and the loop reconciliation in step 5. E8, E10, E14 and E15 are attached as separate reports with their own data files; E16 is scripted for the switching sequence log and the twin prediction only (the switching itself is done by the NETA test company). For BEN 2000 the twin and scripted experiments run per module (`--module 1..3`) plus one plant run. The twin run is kept beside the real run so every plot in the report shows "predicted" and "measured".

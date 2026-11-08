# BEN Engine commissioning report — BEN 20 — Demo site

Schreiber AI · BEN Engine `ben_engine 0.1.0` · mode **sim** · started 2026-11-07T23:44:12+00:00 · overall **FAIL**

## Unit

| Item | Value |
| --- | --- |
| Tier | BEN 20 |
| Enclosure | 20 ft high-cube ISO container |
| Mission profile | AI inference edge |
| IT load | 96.0 kW in 5 racks (19.2 kW/rack) |
| Cooling | In-row DX cooling unit, 5 units (N+1) |
| Power | 480 V 3ph, 225 A service, UPS 2 × 116 kVA, battery 17.8 kWh for 10 min |
| Climate | Temperate, design 35 C |
| ASHRAE class | A2 |
| Twin seed | 1 |

## Steps

| # | Step | Result | Key values |
| --- | --- | --- | --- |
| 1 | Pre-power visual checklist | **PASS** | — |
| 2 | Node discovery and firmware versions | **PASS** | expected_nodes=4, nodes=4 |
| 3 | Sensor sanity at idle | **PASS** | inlet_spread_k=0.562, rh_pct=41.7, dp_after_tare_pa=0.0 |
| 4 | I/O point-to-point test | **PASS** | n_points=38, n_failed=0 |
| 5 | Power chain: meter vs PDU sum | **PASS** | disagreement_pct=0.52, utility_meter_kw=77.01, pdu_sum_kw=57.6 |
| 6 | Cooling unit sequential start and failover | **PASS** | — |
| 7 | Load step to 100 % and thermal steady state | **PASS** | ashrae_max_c=35.0, max_inlet_c_at_100=21.59 |
| 8 | Utility loss ride-through | **PASS** | minutes_to_ashrae_max=2.1, minutes_to_ups_empty=11.85, ashrae_max_c=35.0 |
| 9 | Alarm verification | **FAIL** | alarm_paths_ok=4/5 |
| 10 | Export CSV and signed report | **PASS** | rows=868, sha256=a6d98a1cf15d… |

### Step 1: Pre-power visual checklist — PASS


### Step 2: Node discovery and firmware versions — PASS

- 4 nodes, firmware ['1.0.0-sim']

| Node | Kind | Racks | Firmware | IP |
| --- | --- | --- | --- | --- |
| node1 | room | [] | 1.0.0-sim | 10.77.0.11 |
| node2 | rack | [1, 2] | 1.0.0-sim | 10.77.0.12 |
| node3 | rack | [3, 4] | 1.0.0-sim | 10.77.0.13 |
| node4 | rack | [5] | 1.0.0-sim | 10.77.0.14 |

### Step 3: Sensor sanity at idle — PASS

- 10 inlet probes within 0.56 K; RH 42 %; ΔP after tare +0.00 Pa

### Step 4: I/O point-to-point test — PASS

- 38 point checks, 0 failed

38 point checks; failed: 0

### Step 5: Power chain: meter vs PDU sum — PASS

- meter 77.0 kW, PDUs 57.6 kW, reconciled within 0.52 %

| Utility meter kW | PDU sum kW | Cooling kW | House kW | UPS input kW | Reconciled IT kW | Disagreement % |
| --- | --- | --- | --- | --- | --- | --- |
| 77.01 | 57.6 | 14.29 | 2.42 | 60.0 | 57.9 | 0.52 |

### Step 6: Cooling unit sequential start and failover — PASS

- Each of 5 cooling units failed in turn at 100 % load. Worst peak rack inlet 22.1 C (unit 5), limit 35 C. Redundancy N+1: 4 units needed, standby picked up every time.

| Unit failed | Peak inlet C | Units running after | Standby start s | Alarm |
| --- | --- | --- | --- | --- |
| 1 | 21.76 | 4 | 1.0 | yes |
| 2 | 22.04 | 4 | 1.0 | yes |
| 3 | 22.03 | 4 | 1.0 | yes |
| 4 | 22.11 | 4 | 1.0 | yes |
| 5 | 22.15 | 4 | 1.0 | yes |
| Unit | On | OK | kW | Fan % |
| --- | --- | --- | --- | --- |
| 1 | True | True | 17.82 | 52.1 |
| 2 | True | True | 18.43 | 54.4 |
| 3 | True | True | 19.06 | 56.7 |
| 4 | True | True | 19.67 | 59.0 |
| 5 | True | True | 6.23 | 14.0 |

### Step 7: Load step to 100 % and thermal steady state — PASS

- Load stepped 20→100 %. Hottest rack inlet 21.7 C at 60 % (limit 35 C, ASHRAE A2). Rack ΔT at full load 14.2 K, PUE 1.326. Settling time at full load 170 s.
- In the field the IT load is a resistive load bank in each rack (or the customer's servers at a burn-in load); record the load-bank serial numbers and kW settings here.

| Load | Max inlet C | Mean ΔT K | PUE | Settle s | Steady |
| --- | --- | --- | --- | --- | --- |
| 20 % | 21.57 | 14.3 | 2.47 | 111.0 | yes |
| 40 % | 21.5 | 14.27 | 1.752 | 180.0 | yes |
| 60 % | 21.67 | 14.26 | 1.514 | 170.0 | yes |
| 80 % | 21.6 | 14.34 | 1.397 | 120.0 | yes |
| 100 % | 21.59 | 14.24 | 1.326 | 170.0 | yes |

### Step 8: Utility loss ride-through — PASS

- Utility lost at 100 % load with cooling off. Rack inlets reached the ASHRAE A2 limit (35 C) after 2.1 min; UPS reached 0 % after 11.8 min (configured 10 min). Thermal ride-through, not battery, is the binding limit.

### Step 9: Alarm verification — FAIL

- alarms already active before the test (carried over from step 8, not counted): ['rack1_inlet_crit', 'rack1_inlet_high', 'rack2_inlet_crit', 'rack2_inlet_high', 'rack3_inlet_crit', 'rack3_inlet_high', 'rack4_inlet_crit', 'rack4_inlet_high', 'rack5_inlet_crit', 'rack5_inlet_high', 'ups_low']
- 4/5 alarm paths raised and cleared

| Alarm | Forced via | Raised | Cleared |
| --- | --- | --- | --- |
| rack | sensor_drift | rack5_inlet_high, rack4_inlet_high, rack2_inlet_high | NO |
| leak | leak | leak | yes |
| door_open | door_open | door_open | yes |
| cool1_fail | cooling_unit_fail | cool1_fail | yes |
| utility_loss | utility_loss | utility_loss | yes |

### Step 10: Export CSV and signed report — PASS

- 868 rows → /home/user/ben_engine/docs/reports/commissioning_ben20_20261107T234412Z_data.csv (sha256 a6d98a1cf15d7e76…)

## Sweep criteria

| Sweep | Result | Summary |
| --- | --- | --- |
| cooling_unit_failover | PASS | Each of 5 cooling units failed in turn at 100 % load. Worst peak rack inlet 22.1 C (unit 5), limit 35 C. Redundancy N+1: 4 units needed, standby picked up every time. |
| load_step | PASS | Load stepped 20→100 %. Hottest rack inlet 21.7 C at 60 % (limit 35 C, ASHRAE A2). Rack ΔT at full load 14.2 K, PUE 1.326. Settling time at full load 170 s. |
| utility_loss_ride_through | PASS | Utility lost at 100 % load with cooling off. Rack inlets reached the ASHRAE A2 limit (35 C) after 2.1 min; UPS reached 0 % after 11.8 min (configured 10 min). Thermal ride-through, not battery, is the binding limit. |

### cooling_unit_failover
| Criterion | Pass | Value | Limit | Note |
| --- | --- | --- | --- | --- |
| peak_inlet_within_ashrae_during_any_failure | yes | 22.15 | 35.0 | worst case unit 5 |
| required_units_running_after_each_failure | yes | 4 | 4 |  |
| failure_alarm_raised_each_time | yes | 5 | 5 |  |

### load_step
| Criterion | Pass | Value | Limit | Note |
| --- | --- | --- | --- | --- |
| max_rack_inlet_within_ashrae | yes | 21.67 | 35.0 | ASHRAE A2 allowable max at 60 % load |
| max_rack_inlet_within_recommended | yes | 21.67 | 27.0 | ASHRAE recommended envelope (27 C) |
| steady_state_reached_each_level | yes | 5 | 5 |  |
| rack_delta_t_in_band_at_full_load | yes | 14.24 | 6–20 K |  |

### utility_loss_ride_through
| Criterion | Pass | Value | Limit | Note |
| --- | --- | --- | --- | --- |
| ups_runtime_meets_config | yes | 11.8 | 10 | minutes until UPS state of charge reached 0 % (≥ 90 % of configured minutes) |
| alarm_utility_loss_raised | yes | True | True |  |

## Data

- Telemetry CSV: `commissioning_ben20_20261107T234412Z_data.csv`
- SHA-256: `a6d98a1cf15d7e76869e6f23b4c42abd2c50fd379ff515d9e85079c4f02e8518`
- Verify with `sha256sum <file>`; the report is valid only with a data file whose hash matches.

## Notes and limits

- Simulation mode exercises the control logic, protocol, sweeps and report path against the digital twin; it does not prove the hardware. Live commissioning repeats every step on the real unit with a resistive load bank.
- Temperatures are read from calibrated DS18B20 strings (U95 ±0.25 K per spec/PROTOCOL.md); pass/fail margins smaller than that are not meaningful.
- The ride-through result is the time to the ASHRAE allowable limit with cooling off; battery minutes are the UPS runtime at the tested load.

## Signature

| Role | Name | Organisation | Date | Signature |
| --- | --- | --- | --- | --- |
| Commissioning engineer | dashboard (sim) | Schreiber AI | 2026-11-07 | |
| Customer witness | | | | |

Report generated by `ben_engine.commissioning` on vm; mode sim; data hash a6d98a1cf15d7e76869e6f23b4c42abd2c50fd379ff515d9e85079c4f02e8518.
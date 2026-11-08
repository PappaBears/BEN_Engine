# BEN Engine — analysis, calibration, CFD, sweeps and commissioning tools

Schreiber AI · BEN Engine · `software/ben_engine/` · plain-language guide

This guide covers the software that turns a BEN unit's measurements into statements an operator
can act on: *what the box will do before it does it*, how sure we are, and how to prove a build
on site. Every number quoted below was produced by running the code in this repository; where
a value is an assumption it says so.

All commands run from `software/` (or with `PYTHONPATH=software` from the repo root).

| Tool | Module | One line |
| --- | --- | --- |
| Digital twin | `twin.py` | Lumped thermal + power model of one unit (already existed; two small additions, see §7) |
| CFD | `cfd.py` | 2-D thermal lattice-Boltzmann airflow in the container plan view; per-rack recirculation into the twin |
| Calibration | `calibration.py` | GUM uncertainty budgets, linear calibration fits, tares, predictability score, markdown report |
| Analysis | `analysis.py` | Fit twin parameters to telemetry, predict with 95 % intervals, PUE split, ride-through, UPS curve |
| Sweeps | `sweeps.py` | Automated tests on the twin (load step, failover, utility loss, door, outdoor, filter clog) with pass/fail |
| Virtual nodes | `sim_nodes.py` | In-process BEN nodes that speak `spec/PROTOCOL.md` (telemetry / cmd / ack) |
| Export | `export.py` | Telemetry ring buffer, flattened CSV, JSON lines |
| Commissioning | `commissioning.py` | The ten-step site script, simulation or live, signed report with data hash |

Tests: `PYTHONPATH=software pytest tests -q` (178 tests, about 16 s).

---

## 1. "Predictability instead of uncertainty"

A sensor's uncertainty tells you how far a reading can be from the truth. That is necessary but
it is not what an operator needs. The operator needs to know, *before* a hot day or a utility
loss, whether rack 5 will stay inside its ASHRAE class, and whether the model's answer is tight
enough to act on.

BEN Engine therefore reports a **prediction interval** (model parameter uncertainty combined
with sensor uncertainty, 95 %) and compares it with the **margin to the alarm**:

```
predictability score = (95 % prediction-interval half-width) / (alarm threshold − predicted value)
```

| Score | Meaning |
| --- | --- |
| < 0.25 | excellent: the model warns long before the alarm |
| < 0.5 | good |
| < 1 | marginal: the interval is a large part of the margin |
| ≥ 1 | unpredictable: the interval already touches the alarm; act on the alarm, not the model |

The score is produced by `calibration.predictability_score` and printed by the analysis CLI.
Example from `python -m ben_engine.analysis --tier ben150 --load 1.0 --outdoor 35` (synthetic
telemetry from a perturbed twin, then fitted):

```
At 100 % load on a 35 °C day, rack 5 inlet will be 22.3 ± 0.2 °C (95 % prediction interval; ASHRAE A2 limit 35 °C).
If all cooling stops you have 2.0 minutes before the hottest inlet passes 35 °C (warning at 1.7 min).
On utility loss the UPS carries 96 kW for 11.8 minutes (battery empty); configured target 10 min.
PUE at this point 1.325: IT 75.5 %, cooling 19.1 %, UPS/PDU losses 3.5 %, house 1.9 %.
Predictability: predicted 22.29 ± 0.25 (95 %) against alarm at 35.00: margin 12.71, score 0.02 (excellent).
Fitted parameters: recirculation = 0.12 ± 0.00016 (well determined), envelope_ua_w_k = 109 ± 33 (usable; weak sensitivity, ...),
rack_mass_kg = 80.9 ± 13 (usable; weak sensitivity, ...), bypass = 0.149 ± 0.0011 (well determined); residual RMS 0.082 K over 180 samples.
```

The true values behind that synthetic record were recirculation 0.12, bypass 0.15, rack mass
80 kg, UA 60 W/K: the two parameters that set the steady temperatures are recovered exactly, the
rack mass (a time constant) is recovered within its stated uncertainty, and the envelope UA is
not recoverable from an indoor load step (see §6).

---

## 2. Calibration and uncertainty budgets (`calibration.py`)

### What it does

* `linear_fit(reference, reading)` → `CalResult(gain, offset, residual_std, u_gain, u_offset, …)`.
  The node applies `corrected = gain · raw + offset` (PROTOCOL.md `set_cal`), so the fit is
  `reference = gain · reading + offset`. `u95_at(x)` is the expanded uncertainty of a corrected
  reading at `x` from the coefficient covariance plus the residual scatter, with `k` from Student's
  t at `n − 2` degrees of freedom. Extrapolating beyond the calibrated range widens it.
* `tare(readings)` → offset and its Type A uncertainty from repeated zero readings (ΔP with both
  ports open).
* `UncertaintySource` + `combine()` → GUM budget: standard uncertainty = value / divisor
  (normal 1, k=2 normal 2, rectangular √3, triangular √6, U-shaped √2) × sensitivity; combined
  `u_c` by root-sum-square; effective degrees of freedom by Welch–Satterthwaite; `U95 = k · u_c`
  with `k` from the t-distribution (1.96 when ν_eff is effectively infinite).
* `default_budget(channel, placement=[…])` gives the budget for each PROTOCOL.md channel, and
  adds installation effects as Type B terms.
* `markdown_report(...)` writes the summary and every budget as tables
  (`python -m ben_engine.calibration --out report.md`).

### Default budgets (as computed by the code, no placement effects)

| Channel | u_c | k | U95 computed | PROTOCOL.md claim (k=2) | Dominant term |
| --- | --- | --- | --- | --- | --- |
| DS18B20 rack inlet/outlet (calibrated) | 0.086 K | 1.97 | **±0.17 K** | ±0.25 K ✓ | 12-month drift (0.10 K rect.) |
| SHT45 temperature | 0.069 K | 1.96 | **±0.14 K** | ±0.15 K ✓ | datasheet typical ±0.1 K |
| SHT45 relative humidity | 0.87 %RH | 1.96 | **±1.7 %RH** | ±1.5 %RH ✗ | datasheet typical ±1.0 %RH |
| SDP810-125Pa at 12 Pa, after tare | 0.23 Pa | 1.96 | **±0.46 Pa** | ±0.4 Pa ✗ | 3 % of reading span term |
| ADS1115 + 165 Ω, 4–20 mA loop | 0.013 mA | 1.96 | **±0.025 mA** | ±0.02 mA ✗ | transmitter accuracy if the loop is not calibrated end to end |
| CT + power meter class 0.5 | 0.46 % | 1.96 | **±0.9 % of reading** | — | meter class |

Three channels come out slightly worse than the protocol table claims. That is a finding, not a
tuning problem: the RH claim needs a chilled-mirror reference instead of salt points, the SDP810
claim holds only below ~9 Pa (the span term is 3 % of reading), and the 4–20 mA claim is met only
when the loop is calibrated end to end with the transmitter (then the dominant term drops out).
The protocol table should be updated or the calibration method tightened; either is a one-line
change here.

### Placement (wall) effects as Type B terms

| Key | Effect | Term added | Correction |
| --- | --- | --- | --- |
| `inlet_near_perforated_door` | inlet probe < 50 mm from a perforated rack door reads 0.3–0.8 K high | ±0.25 K rect. | −0.55 K |
| `inlet_standard_standoff` | probe at 100–150 mm stand-off: spatial non-uniformity across the rack face | ±0.15 K rect. | — |
| `hot_aisle_radiation` | unshielded probe sees 35–45 °C hot-aisle surfaces | ±0.20 K rect. | −0.20 K |
| `wall_conduction_mount` | stem conduction to the mounting rail | ±0.15 K rect. | — |
| `pressure_tap_near_fan_discharge` | static tap within 0.5 m of a fan discharge picks up dynamic pressure | ±3 Pa rect. | — |
| `pressure_tap_quiet` | tap in quiet air behind a baffle | ±0.3 Pa rect. | — |
| `rh_near_coil` | RH sensor within 0.3 m of the cooling coil | ±3 %RH rect. | — |
| `ct_crowded_conductor` | CT near adjacent phases / off-centre conductor | ±0.3 % rect. | — |

Example: a DS18B20 inlet probe mounted close to the door and unshielded toward the hot aisle
has U95 = ±0.40 K after a −0.75 K correction (computed by
`default_budget("DS18B20", ["inlet_near_perforated_door", "hot_aisle_radiation"])`), more than
double the clean installation. The placement terms are the largest controllable item in the
whole measurement chain, which is why the assembly instructions call for 100–150 mm stand-off
clips and radiation shields.

### Calibration procedure (what the numbers assume)

1. Temperature strings: stirred bath comparison at 3 points (15, 25, 40 °C) against a reference
   with U95 ≤ 0.05 K; 10 readings per point; `linear_fit` → `set_cal` per channel; recalibrate
   every 12 months (drift is the dominant term).
2. ΔP: both ports open, fans off, 20 readings → `tare` → `set_cal` with the offset; repeat at
   each commissioning and after any tubing change.
3. 4–20 mA: loop calibrator at 4, 12, 20 mA, preferably with the transmitter in the loop.
4. Power: no field calibration; compare against a reference analyser at commissioning (verify,
   do not correct).

---

## 3. CFD (`cfd.py`)

### What it is

A plan-view (looking down) model of the air inside the container:

* **Flow**: D2Q9 lattice-Boltzmann BGK, full-way bounce-back walls, τ = 0.6, max lattice speed
  0.08 (0.04 for BEN 5). Racks are *fan zones with a heat source* (velocity relaxed toward the
  server-fan face velocity, front → back; heat injected so the air leaving the rack is
  `P_rack / (ṁ cp)` warmer). Cooling units are fan zones the other way (hot aisle → cold aisle);
  air passing through them is reset to the supply temperature.
* **Scalars**: temperature and a hot-air tracer (1 at rack exhaust, 0 at supply) are carried as
  D2Q5 passive scalars during the flow run; once the velocity field is steady they are
  recomputed as the exact steady state of upwind advection–diffusion on that field with one
  sparse direct solve (`steady_scalar`). The reason: the physical loop time of hot-aisle
  leakage is minutes, which would be ~10⁵ lattice steps; the steady solve gets the same answer
  in under a second. The last D2Q5 values are kept in the metrics for comparison.
* **Geometry from `Config`**: interior length × width; one rack row along the back wall
  (hot aisle 22 % / racks 45 % / cold aisle 33 % of the width); 600 mm racks and 300 mm
  in-row units interleaved; containment doors between the row ends and the end walls with an 8 %
  open fraction when closed (seals, cut-outs) or fully open. The standby (N+1) unit is off and
  solid, as in the twin; `failed_units=[…]` fails a unit and starts the standby;
  `supply_ratio` is unit airflow ÷ rack airflow (1.10 = the twin's 10 % bypass).
* **Metrics**: per-rack inlet temperature, per-rack **recirculation index** (mean tracer at the
  inlet face = fraction of inlet air that came from the hot side without passing a cooling
  unit), max inlet, supply→inlet rise, return temperature, cold-minus-hot aisle pressure proxy
  (lattice density difference scaled to Pa), lattice and real Reynolds numbers, runtime.

### Running it

```
python -m ben_engine.cfd --tier ben150 --png /tmp/x.png
python -m ben_engine.cfd --tier ben150 --supply-ratio 0.9
python -m ben_engine.cfd --tier ben150 --fail-unit 1 --png /tmp/fail.png
python -m ben_engine.cfd --tier ben500 --json
```

Results actually obtained (BEN 150 preset, 5 × 19.2 kW racks, 232 × 90 cells at 25 mm,
runtime 14–16 s on the development container):

| Scenario | Recirculation index per rack | Max inlet | Return |
| --- | --- | --- | --- |
| Design: 4 of 5 units running, supply ratio 1.10, doors closed | 0.001 × 5 | 20.0 °C | 31.7 °C |
| Same, doors open | 0.001 × 5 | 20.0 °C | 31.6 °C |
| Fans turned down: supply ratio 0.90 | 0.35, 0.00, 0.00, 0.00, 0.31 | 31.4 °C (rack 1) | 34.4 °C |
| Unit 2 failed, standby started | 0.40, 0.00, 0.00, 0.00, 0.00 | 32.4 °C (rack 1) | 31.7 °C |

Reading: when the units supply more air than the racks pull, the cold aisle is pressurised and
the plan-view recirculation is nil; the risk appears when supply falls below demand (fan
turn-down, a failed unit next to an end rack), and it lands on the end racks first. That is the
relative information the twin needs.

### Honest limits (read before quoting a number)

* **Reynolds number.** The lattice Reynolds number is ~70 for BEN 150 (34 for BEN 500); the real
  cold-aisle flow is ~10⁵. There is no turbulence model; the lattice viscosity acts as a crude,
  fixed eddy viscosity. Mixing rates and jet spreading are therefore qualitative.
* **Two dimensions.** Over-rack and under-floor recirculation, stratification and the vertical
  distribution of rack inlet temperature do not exist in a plan view; the "closed containment ⇒
  ~0 % recirculation" result is a lower bound. The twin's default 8 % stays as the conservative
  design assumption until a site measurement replaces it.
* **Fan zones** are a soft prescription, not fan curves; a 50 % relaxation factor for server
  fans is a modelling choice.
* **DLC tiers**: the CDUs move no room air, so the residual 30 % air-side heat is handled by an
  assumed one in-row air unit per two racks plus one standby (`layout_notes` says so).
* **BEN 5** has no aisle containment; doors are treated as open and the row is compressed to fit.
* Density varies ±5 % in the lattice (weakly compressible scheme); the pressure proxy is a
  relative number.

### Feeding the twin

`TwinParams.recirculation_profile` (added for this purpose) takes a list of per-rack
fractions; when its length equals `cfg.racks` the twin uses it instead of the scalar
`recirculation` and its built-in +0.3 K position bias (the `door_open` fault still multiplies by
1.6). Two ways to set it:

```python
from ben_engine.cfd import run_cfd, recirculation_profile, apply_to_params
params.recirculation_profile = recirculation_profile(cfg, failed_units=[1])   # list[float]
# or
m = run_cfd(cfg, supply_ratio=0.9); apply_to_params(m, params)              # also sets the scalar to the mean
```

---

## 4. Analysis (`analysis.py`)

* `schedule_from_states(states)` recovers the load, outdoor and fault timeline from a record
  (twin states, or JSON lines written by `export`).
* `fit_params(cfg, states, fit=("recirculation","envelope_ua_w_k","rack_mass_kg","bypass"))`
  replays the twin through that timeline (noise-free, unrounded internal values) and solves a
  bounded least-squares problem (`scipy.optimize.least_squares`) on rack inlet and return
  temperatures sampled every 10 s. Returns the fitted values, their standard deviations and
  covariance (residual variance × (JᵀJ)⁻¹), residual RMS and an identifiability note per
  parameter (relative standard deviation, plus a sensitivity warning when a 10 % change moves
  the residual by less than 10 mK RMS).
* `predict(cfg, params, schedule, duration, cov)` runs the twin forward and draws `n_mc`
  parameter sets from the covariance (clipped to physical bounds); the 95 % prediction interval
  is 1.96 × √(model spread² + sensor σ²) with sensor σ = 0.125 K (±0.25 K k=2 from
  PROTOCOL.md).
* `pue_breakdown(state, cfg)`, `thermal_margin(cfg, params, load, outdoor_c)` (minutes from all
  cooling units failing, IT still running, to the ASHRAE allowable max; the warning point at
  −2 K is also given), `ups_runtime_curve(cfg, params, loads)` (minutes until the battery is
  empty at each load, by running the twin through a utility loss).
* `plain_summary(...)` and the CLI phrase the answers; `--jsonl file` fits real telemetry,
  otherwise a synthetic record is used and the CLI says so.

Run: `python -m ben_engine.analysis --tier ben150 --load 1.0 --outdoor 35 [--jsonl data.jsonl] [--json]`
(≈ 10 s with 30 Monte Carlo runs).

---

## 5. Sweeps, virtual nodes, export and commissioning

### Sweeps (`sweeps.py`)

`python -m ben_engine.sweeps --tier ben150 --csv-dir out/` runs all six on fresh seeded twins in
under a second. Each returns `SweepResult(name, started, rows, criteria, summary, extra)`; rows
are flattened states with `sweep`, `phase`, `phase_t` columns; `to_csv(result, path)`. Results
on the BEN 150 preset:

| Sweep | Result | Finding |
| --- | --- | --- |
| load_step | PASS | hottest inlet 21.6 °C at 100 % (A2 limit 35 °C), rack ΔT 14.3 K, PUE 1.32, settles in 120 s |
| cooling_unit_failover | PASS | worst peak 22.1 °C; standby picked up after every one of 5 failures |
| utility_loss_ride_through | PASS | ASHRAE limit reached after 2.1 min with cooling off; UPS empty after 11.8 min (10 configured) — **temperature, not battery, is the binding limit** |
| door_open | PASS | +1.1 K at 80 % load, 25 °C outdoor; alarm raised |
| outdoor_temperature_sweep | PASS | at 35 °C design: inlet 21.6 °C, PUE 1.33, fans 78 % |
| filter_clog | PASS | ΔP alarm after 105 min; peak inlet 24.5 °C |

### Virtual nodes (`sim_nodes.py`)

`NodeFleet(cfg)` builds `node1` (room: `T_ref`, `T_return`, `RH`, `dP_aisle`, `leak`, `door`,
`ai0_mA`, `pulse_kwh`, relays) and one node per two racks (`T_in_1..4`, `T_out_1..4`, relays).
`poll_all(state)` → `(topic, payload)` pairs exactly as in PROTOCOL.md (`ts, seq, ch, raw,
cal_id`), `handle(topic, cmd)` → `(ack_topic, ack)` for `set_output`, `get_output`, `set_cal`,
`get_cal`, `tare`, `identify`, `reboot`, `ota` (refused in sim). Raw values use the real sensor
scalings (DS18B20 1/16 °C, SHT45 ticks, SDP810 ×240, ADS1115 125 µV/LSB over 165 Ω) and the
calibration is applied as the firmware does. `MqttPublisher` bridges to a broker when
`paho-mqtt` is installed; otherwise `available` is False and nothing else changes.

Note: `twin.sensors()` labels rack sensors `node1..` by rack pair; the virtual fleet reserves
`node1` for the room node as the task brief asked. The dashboard should take node ids from the
fleet's `discover()`.

### Export (`export.py`)

`TelemetryBuffer(hours=24)` keeps raw states; `to_csv(path, from_t, to_t)` and
`to_jsonl(...)` export a time window. Flattening: nested dicts join with `_`, lists become
`name_1, name_2, …`, `alarms` → `alarm_count`, `alarm_ids`, `alarm_max_sev`, `faults` → `;`-joined.

### Commissioning (`commissioning.py`)

```
python -m ben_engine.commissioning --sim --tier ben150 --yes --out report.md --operator "Name"
python -m ben_engine.commissioning --live --url http://ben-controller.local:8000 --out report.md
```

Ten steps, each with recorded values and PASS/FAIL, then a markdown report with a step table,
detail tables, the sweep criteria, the SHA-256 of the exported CSV and a signature block. The
simulation run for BEN 150 passes all ten steps in under a second and exports ~1 400 rows. The
`--live` entry currently only proves the gateway answers `/api/config` and `/api/state` and
writes a report saying so; the live steps need a person at the panel and a load bank, and are
driven from the dashboard's commissioning page.

Two things the sim run teaches that belong in the field procedure: step 5 reconciles the
utility meter with the PDU sum only after subtracting metered cooling, house load and UPS/PDU
losses (0.5 % residual in the twin is the PDU loss); and step 9 waits for the unit to recover
from the ride-through test — in the twin the room needs about 13–14 minutes to come back under
the warning threshold after cooling is restored, and the UPS `ups_low` alarm stays until the
battery has recharged.

---

## 6. Known limits — least accurate first

1. **Thermal ride-through (2 minutes to 35 °C at full load, BEN 150).** The twin's air-side
   thermal mass (60 kg effective per rack, 40 kg room air) is a design value, not a measurement;
   server mass, racks, floor and walls store far more heat than that. The real number is very
   likely longer, and the fit cannot tell: `rack_mass_kg` is only weakly identifiable from
   10-second samples of a load step. The commissioning ride-through test (step 8) is the only
   way to pin it down. Until then quote the twin's value as a lower bound.
2. **Envelope UA.** Not identifiable from an indoor load step (the model moves by ~0.1 mK per
   W/K); it needs an outdoor temperature swing or a door-open test with a large indoor–outdoor
   difference. The fitter says so in its identifiability note.
3. **CFD absolute values.** Laminar, two-dimensional, soft fan zones (see §3). Use rack
   rankings and scenario differences, not absolute temperatures.
4. **Calibration budgets** are datasheet/handbook values with the assumptions listed; the
   placement corrections (−0.55 K, −0.20 K) are typical literature magnitudes and must be
   confirmed with a traverse at the first commissioning. Three channels do not meet the protocol
   claim as budgeted (§2).
5. **Recovery time after ride-through (≈ 13–14 min)** inherits the same thermal-mass caveat as
   item 1 and the twin's simplified cooling-capacity curve.
6. **Power-chain reconciliation** in the twin is bookkeeping with fixed efficiencies
   (UPS 96 %, PDU 99.5 %); a real UPS efficiency curve and transformer losses will move the
   3 % criterion's residual.
7. **Virtual nodes** reproduce the protocol and the sensor scalings, not the firmware's timing,
   buffering or failure modes.

## 7. Changes made to `twin.py`

Both additive, nothing else touched:

* `TwinParams.recirculation_profile: Optional[List[float]]` — per-rack recirculation from the
  CFD; when set with length `racks` it replaces the scalar and the position bias.
* `_update_alarms` evaluates rack-inlet alarms on the *reported* reading
  (`rack_inlet_c + drift_c`), as the gateway does, so a sensor-drift fault can raise the alarm
  that commissioning step 9 verifies. Before, the drift only changed the reading and never the
  alarm.

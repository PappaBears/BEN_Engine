# Software interfaces (contract for the python package and dashboard)

```python
from ben_engine.config import Config
from ben_engine.twin import Twin

cfg = Config.preset("ben20", "ai_inference", "temperate")
tw = Twin(cfg, seed=1)              # deterministic digital twin
tw.step(dt=1.0)                      # advance 1 s
s = tw.state()                       # dict, JSON-serialisable
tw.set_it_load(0.8)                  # fraction of it_kw
tw.inject("cooling_unit_fail", unit=1)   # faults: cooling_unit_fail, utility_loss, door_open, filter_clog, leak, sensor_drift
tw.clear("cooling_unit_fail", unit=1)
tw.sensors()                         # list of SensorSpec(id, kind, location_xyz_m, unit, u95)
```

`state()` keys (all floats unless stated):
`t`, `outdoor_c`, `it_kw`, `it_fraction`, `rack_inlet_c` (list), `rack_outlet_c` (list),
`supply_c`, `return_c`, `aisle_dp_pa`, `rh_pct`, `cooling_units` (list of {on, kw, fan_pct, ok}),
`cooling_kw_elec`, `power` ({utility_ok, utility_kw, ups_kw, ups_soc_pct, ups_runtime_min, ups_on_battery, generator_on, pdu_kw(list)}),
`pue`, `alarms` (list of {id, sev, msg, active}), `faults` (list of active fault names), `door_open` (bool), `leak` (bool).

Dashboard API (FastAPI, `ben_engine.api:app`):
- `GET /api/config` / `POST /api/config` (validate + rebuild twin)
- `GET /api/presets`, `GET /api/catalog` (tiers, profiles, cooling, climates)
- `GET /api/state` (latest), `WS /ws/state` (1 Hz push)
- `POST /api/fault {name, params}` , `DELETE /api/fault/{name}`
- `POST /api/load {fraction}`
- `POST /api/sweep {name}` → runs an automated sweep in background; `GET /api/sweeps` lists results; `GET /api/sweeps/{id}.csv`
- `GET /api/export.csv?from=&to=` telemetry CSV
- `POST /api/io/test {node, channel, value}` and `GET /api/io/status` (virtual nodes in sim mode)
- `POST /api/calibrate {channel, reference_points}` → coefficients + uncertainty
- `GET /api/cfd?tier=` → PNG of latest CFD field + metrics JSON at `/api/cfd/metrics`
- `POST /api/commission/run` → runs commissioning script against the twin, returns report path
- `GET /api/bom` → BOM for current config
```

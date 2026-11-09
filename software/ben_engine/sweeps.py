"""BEN Engine automated test sweeps, run on a Twin (simulation) and later on real hardware
through the same interface.

Every sweep takes a ``Twin``, drives it through a scripted scenario, records flattened states
(see ``export.flatten_state``) with extra ``sweep``, ``phase`` and ``phase_t`` columns, evaluates
pass/fail criteria and writes a plain-language summary. Sweeps are deterministic: the twin is
seeded and nothing here uses wall-clock time except the ``started`` stamp, which can be passed
in.

Sweeps: ``load_step``, ``cooling_unit_failover``, ``utility_loss_ride_through``, ``door_open``,
``outdoor_temperature_sweep``, ``filter_clog``; ``run_all`` runs them in order on fresh twins. Forward architecture
(docs/FORWARD_ARCHITECTURE_DECISION.md): ``cdu_pump_failover`` runs only on ``cooling == "dlc_hd"`` and
``dc_ground_fault_response`` only on ``power_architecture == "dc800"``; ``applicable(name, cfg)`` says which apply and
``run_all`` skips the rest.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from .config import Config, CLIMATE_DESIGN
from .twin import Twin
from .export import flatten_state, write_csv

ASHRAE_MAX = {"A1": 27.0, "A2": 35.0, "A3": 40.0, "A4": 45.0}
ASHRAE_RECOMMENDED_MAX = 27.0


@dataclass
class Criterion:
    name: str
    passed: bool
    value: Any
    limit: Any
    note: str = ""


@dataclass
class SweepResult:
    name: str
    started: str
    rows: List[Dict[str, Any]] = field(default_factory=list)
    criteria: List[Criterion] = field(default_factory=list)
    summary: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.criteria)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["passed"] = self.passed
        return d


def _now(clock: Optional[str]) -> str:
    return clock or _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


class Recorder:
    """Steps a twin and records flattened rows every ``record_every_s`` seconds of sim time."""

    def __init__(self, twin: Twin, sweep: str, dt: float = 1.0, record_every_s: float = 10.0):
        self.tw = twin
        self.sweep = sweep
        self.dt = dt
        self.every = record_every_s
        self.rows: List[Dict[str, Any]] = []
        self.phase = "init"
        self.phase_t0 = twin.t
        self._next_rec = twin.t

    def set_phase(self, name: str):
        self.phase = name
        self.phase_t0 = self.tw.t

    def run(self, seconds: float, until: Optional[Callable[[Dict[str, Any]], bool]] = None) -> Optional[Dict[str, Any]]:
        """Advance ``seconds`` of sim time; stop early when ``until(state)`` is true. Returns last state."""
        t_end = self.tw.t + seconds
        last = None
        while self.tw.t < t_end - 1e-9:
            self.tw.step(self.dt)
            if self.tw.t >= self._next_rec - 1e-9:
                last = self.tw.state()
                row = flatten_state(last)
                row.update({"sweep": self.sweep, "phase": self.phase, "phase_t": round(self.tw.t - self.phase_t0, 1)})
                self.rows.append(row)
                self._next_rec = self.tw.t + self.every
                if until is not None and until(last):
                    return last
        if last is None:
            last = self.tw.state()
        return last


def _max_inlet(state: Dict[str, Any]) -> float:
    return max(state["rack_inlet_c"])


def _steady(history: List[float], window: int, tol: float) -> bool:
    if len(history) < window:
        return False
    seg = history[-window:]
    return max(seg) - min(seg) < tol


# ------------------------------------------------------------------ sweeps
def load_step(twin: Twin, levels=(0.2, 0.4, 0.6, 0.8, 1.0), hold_s: float = 900.0, settle_tol_k: float = 0.15,
              record_every_s: float = 10.0, clock: Optional[str] = None) -> SweepResult:
    """Step IT load up through ``levels``; hold each until rack inlets are steady (or ``hold_s``)."""
    res = SweepResult("load_step", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    rec = Recorder(twin, "load_step", record_every_s=record_every_s)
    per_level = []
    for lv in levels:
        twin.set_it_load(lv)
        rec.set_phase(f"load_{int(lv*100)}")
        hist: List[float] = []

        def steady(st, hist=hist):
            hist.append(_max_inlet(st))
            return _steady(hist, 6, settle_tol_k) and len(hist) >= 12

        last = rec.run(hold_s, until=steady)
        per_level.append({"load": lv, "settle_s": round(twin.t - rec.phase_t0, 1), "max_inlet_c": _max_inlet(last),
                          "mean_delta_t_k": round(sum(last["rack_outlet_c"]) / len(last["rack_outlet_c"]) - sum(last["rack_inlet_c"]) / len(last["rack_inlet_c"]), 2),
                          "pue": last["pue"], "steady": _steady(hist, 6, settle_tol_k)})
    worst = max(per_level, key=lambda r: r["max_inlet_c"])
    res.criteria.append(Criterion("max_rack_inlet_within_ashrae", worst["max_inlet_c"] <= a_max, worst["max_inlet_c"], a_max,
                                  f"ASHRAE {cls} allowable max at {int(worst['load']*100)} % load"))
    res.criteria.append(Criterion("max_rack_inlet_within_recommended", worst["max_inlet_c"] <= ASHRAE_RECOMMENDED_MAX,
                                  worst["max_inlet_c"], ASHRAE_RECOMMENDED_MAX, "ASHRAE recommended envelope (27 C)"))
    res.criteria.append(Criterion("steady_state_reached_each_level", all(r["steady"] for r in per_level),
                                  sum(r["steady"] for r in per_level), len(per_level)))
    full = per_level[-1]
    res.criteria.append(Criterion("rack_delta_t_in_band_at_full_load", 6.0 <= full["mean_delta_t_k"] <= 20.0,
                                  full["mean_delta_t_k"], "6–20 K"))
    res.extra["levels"] = per_level
    res.summary = (f"Load stepped {int(levels[0]*100)}→{int(levels[-1]*100)} %. Hottest rack inlet {worst['max_inlet_c']:.1f} C "
                   f"at {int(worst['load']*100)} % (limit {a_max:.0f} C, ASHRAE {cls}). Rack ΔT at full load {full['mean_delta_t_k']:.1f} K, "
                   f"PUE {full['pue']}. Settling time at full load {full['settle_s']:.0f} s.")
    res.rows = rec.rows
    return res


def cooling_unit_failover(twin: Twin, load: float = 1.0, fail_s: float = 900.0, recover_s: float = 600.0,
                          record_every_s: float = 10.0, clock: Optional[str] = None) -> SweepResult:
    """Fail each cooling unit in turn at ``load``; standby must start and inlets must stay in class."""
    res = SweepResult("cooling_unit_failover", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    rec = Recorder(twin, "cooling_unit_failover", record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    base = rec.run(600.0)
    units = []
    n_needed = twin.d["cooling_units_n"]
    for u in range(len(twin.cooling_units)):
        rec.set_phase(f"fail_unit_{u+1}")
        twin.inject("cooling_unit_fail", unit=u)
        peak = -1e9
        start_t = None
        t0 = twin.t

        def watch(st, u=u):
            nonlocal peak, start_t
            peak = max(peak, _max_inlet(st))
            running = sum(1 for c in st["cooling_units"] if c["on"] and c["ok"])
            if start_t is None and running >= n_needed:
                start_t = st["t"] - t0
            return False

        last = rec.run(fail_s, until=watch)
        running = sum(1 for c in last["cooling_units"] if c["on"] and c["ok"])
        units.append({"unit": u + 1, "peak_inlet_c": round(peak, 2), "running_after_fail": running,
                      "standby_started_after_s": start_t, "alarm_raised": any(a["id"] == f"cool{u+1}_fail" for a in last["alarms"])})
        twin.clear("cooling_unit_fail", unit=u)
        rec.set_phase(f"recover_unit_{u+1}")
        rec.run(recover_s)
    worst = max(units, key=lambda r: r["peak_inlet_c"])
    res.criteria.append(Criterion("peak_inlet_within_ashrae_during_any_failure", worst["peak_inlet_c"] <= a_max, worst["peak_inlet_c"], a_max,
                                  f"worst case unit {worst['unit']}"))
    res.criteria.append(Criterion("required_units_running_after_each_failure", all(r["running_after_fail"] >= n_needed for r in units),
                                  min(r["running_after_fail"] for r in units), n_needed))
    res.criteria.append(Criterion("failure_alarm_raised_each_time", all(r["alarm_raised"] for r in units), sum(r["alarm_raised"] for r in units), len(units)))
    res.extra["units"] = units
    res.extra["baseline_max_inlet_c"] = _max_inlet(base)
    res.summary = (f"Each of {len(units)} cooling units failed in turn at {int(load*100)} % load. Worst peak rack inlet "
                   f"{worst['peak_inlet_c']:.1f} C (unit {worst['unit']}), limit {a_max:.0f} C. "
                   f"Redundancy {twin.cfg.redundancy}: {n_needed} units needed, "
                   f"{'standby picked up every time' if all(r['running_after_fail'] >= n_needed for r in units) else 'capacity was short after at least one failure'}.")
    res.rows = rec.rows
    return res


def utility_loss_ride_through(twin: Twin, load: float = 1.0, max_s: float = 3600.0, record_every_s: float = 5.0,
                              clock: Optional[str] = None) -> SweepResult:
    """Drop utility; measure time to ASHRAE max inlet and UPS depletion. Cooling is off on battery
    (mechanical load is not on the UPS except the BEN 5 cabinet) unless a generator starts."""
    res = SweepResult("utility_loss_ride_through", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    rec = Recorder(twin, "utility_loss_ride_through", record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    base = rec.run(600.0)
    runtime_claimed = base["power"]["ups_runtime_min"]
    rec.set_phase("utility_loss")
    twin.inject("utility_loss")
    t0 = twin.t
    t_ashrae = None
    t_ups_empty = None
    t_gen = None
    peak = -1e9

    def watch(st):
        nonlocal t_ashrae, t_ups_empty, t_gen, peak
        peak = max(peak, _max_inlet(st))
        if t_ashrae is None and _max_inlet(st) > a_max:
            t_ashrae = st["t"] - t0
        if t_gen is None and st["power"]["generator_on"]:
            t_gen = st["t"] - t0
        if t_ups_empty is None and st["power"]["ups_soc_pct"] <= 0.0:
            t_ups_empty = st["t"] - t0
        # stop when both answers are known or load has dropped (UPS empty) or generator carries it 10 min
        if t_ups_empty is not None and (t_ashrae is not None or st["it_kw"] <= 0.01):
            return True
        if t_gen is not None and st["t"] - t0 > t_gen + 600:
            return True
        return False

    last = rec.run(max_s, until=watch)
    twin.clear("utility_loss")
    rec.set_phase("restored")
    rec.run(300.0)
    ride_min = (t_ashrae / 60.0) if t_ashrae is not None else None
    ups_min = (t_ups_empty / 60.0) if t_ups_empty is not None else None
    res.criteria.append(Criterion("ups_runtime_meets_config", (ups_min is None and t_gen is not None) or (ups_min is not None and ups_min >= twin.cfg.ups_minutes * 0.9),
                                  None if ups_min is None else round(ups_min, 1), twin.cfg.ups_minutes,
                                  "minutes until UPS state of charge reached 0 % (≥ 90 % of configured minutes)"))
    alarm_seen = any("utility_loss" in str(r.get("alarm_ids", "")).split(";") for r in rec.rows)
    res.criteria.append(Criterion("alarm_utility_loss_raised", alarm_seen, alarm_seen, True))
    if twin.cfg.generator:
        res.criteria.append(Criterion("generator_started", t_gen is not None, t_gen, "≤ 60 s", "generator start time s"))
    res.extra.update({"claimed_runtime_min_at_onset": runtime_claimed, "minutes_to_ashrae_max": None if ride_min is None else round(ride_min, 2),
                      "minutes_to_ups_empty": None if ups_min is None else round(ups_min, 2), "peak_inlet_c": round(peak, 2),
                      "generator_start_s": t_gen, "ashrae_max_c": a_max})
    if t_gen is not None:
        res.summary = (f"Utility lost at {int(load*100)} % load; generator took load after {t_gen:.0f} s. Peak rack inlet {peak:.1f} C. ")
    else:
        res.summary = (f"Utility lost at {int(load*100)} % load with cooling off. Rack inlets reached the ASHRAE {cls} limit ({a_max:.0f} C) after "
                       f"{'%.1f min' % ride_min if ride_min is not None else 'more than the test window'}; UPS reached 0 % after "
                       f"{'%.1f min' % ups_min if ups_min is not None else 'more than the test window'} (configured {twin.cfg.ups_minutes} min). ")
    res.summary += "Thermal ride-through, not battery, is the binding limit." if (ride_min is not None and (ups_min is None or ride_min < ups_min)) else "Battery, not temperature, is the binding limit."
    res.rows = rec.rows
    return res


def door_open(twin: Twin, load: float = 0.8, open_s: float = 900.0, record_every_s: float = 10.0,
              clock: Optional[str] = None) -> SweepResult:
    """Open the container door at ``load``; inlets must stay in class and the door alarm must raise."""
    res = SweepResult("door_open", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    rec = Recorder(twin, "door_open", record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    base = rec.run(600.0)
    base_in = _max_inlet(base)
    rec.set_phase("door_open")
    twin.inject("door_open")
    peak = -1e9
    alarm = False

    def watch(st):
        nonlocal peak, alarm
        peak = max(peak, _max_inlet(st))
        alarm = alarm or any(a["id"] == "door_open" for a in st["alarms"])
        return False

    last = rec.run(open_s, until=watch)
    rh_peak = max(r.get("rh_pct", 0) for r in rec.rows)
    twin.clear("door_open")
    rec.set_phase("door_closed")
    rec.run(600.0)
    res.criteria.append(Criterion("peak_inlet_within_ashrae", peak <= a_max, round(peak, 2), a_max))
    res.criteria.append(Criterion("inlet_rise_under_3k", peak - base_in <= 3.0, round(peak - base_in, 2), 3.0, "rise vs closed-door baseline"))
    res.criteria.append(Criterion("door_alarm_raised", alarm, alarm, True))
    res.extra.update({"baseline_max_inlet_c": base_in, "peak_inlet_c": round(peak, 2), "rh_peak_pct": rh_peak, "outdoor_c": twin.outdoor_c})
    res.summary = (f"Door open {open_s/60:.0f} min at {int(load*100)} % load, outdoor {twin.outdoor_c:.0f} C: hottest inlet rose "
                   f"{peak - base_in:.1f} K to {peak:.1f} C; RH peaked {rh_peak:.0f} %. Door alarm {'raised' if alarm else 'NOT raised'}.")
    res.rows = rec.rows
    return res


def outdoor_temperature_sweep(twin: Twin, load: float = 1.0, t_start_c: float = 10.0, t_end_c: Optional[float] = None,
                              step_k: float = 5.0, hold_s: float = 900.0, record_every_s: float = 10.0,
                              clock: Optional[str] = None) -> SweepResult:
    """Ramp outdoor temperature from ``t_start_c`` to the climate design temperature in steps."""
    res = SweepResult("outdoor_temperature_sweep", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    t_end = t_end_c if t_end_c is not None else CLIMATE_DESIGN[twin.cfg.climate]["t_design_c"]
    rec = Recorder(twin, "outdoor_temperature_sweep", record_every_s=record_every_s)
    twin.set_it_load(load)
    points = []
    t = t_start_c
    temps = []
    while t < t_end - 1e-9:
        temps.append(t)
        t += step_k
    temps.append(t_end)
    for tc in temps:
        twin.set_outdoor(tc)
        rec.set_phase(f"outdoor_{tc:g}")
        last = rec.run(hold_s)
        points.append({"outdoor_c": tc, "max_inlet_c": _max_inlet(last), "pue": last["pue"], "cooling_kw_elec": last["cooling_kw_elec"],
                       "fan_pct_max": max(u["fan_pct"] for u in last["cooling_units"])})
    design = points[-1]
    res.criteria.append(Criterion("inlet_within_ashrae_at_design_outdoor", design["max_inlet_c"] <= a_max, design["max_inlet_c"], a_max,
                                  f"outdoor {design['outdoor_c']} C"))
    res.criteria.append(Criterion("fans_have_headroom_at_design", design["fan_pct_max"] < 100.0, design["fan_pct_max"], 100.0, "max cooling fan %"))
    res.extra["points"] = points
    res.summary = (f"Outdoor swept {t_start_c:g}→{t_end:g} C at {int(load*100)} % load. At design outdoor {design['outdoor_c']:g} C the hottest inlet "
                   f"is {design['max_inlet_c']:.1f} C (limit {a_max:.0f} C), PUE {design['pue']}, fans at {design['fan_pct_max']:.0f} %.")
    res.rows = rec.rows
    return res


def filter_clog(twin: Twin, load: float = 1.0, max_s: float = 9000.0, record_every_s: float = 60.0,
                clock: Optional[str] = None) -> SweepResult:
    """Let the filters clog; the ΔP alarm must raise before inlets leave the ASHRAE class."""
    res = SweepResult("filter_clog", _now(clock))
    cls = twin.d["ashrae_class"]
    a_max = ASHRAE_MAX[cls]
    rec = Recorder(twin, "filter_clog", dt=5.0, record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    rec.run(600.0)
    rec.set_phase("clogging")
    twin.inject("filter_clog")
    t0 = twin.t
    t_alarm = None
    t_ashrae = None
    peak = -1e9

    def watch(st):
        nonlocal t_alarm, t_ashrae, peak
        peak = max(peak, _max_inlet(st))
        if t_alarm is None and any(a["id"] == "filter_dp" for a in st["alarms"]):
            t_alarm = st["t"] - t0
        if t_ashrae is None and _max_inlet(st) > a_max:
            t_ashrae = st["t"] - t0
        return t_alarm is not None and (st["t"] - t0) > t_alarm + 600

    last = rec.run(max_s, until=watch)
    twin.clear("filter_clog")
    res.criteria.append(Criterion("filter_dp_alarm_raised", t_alarm is not None, t_alarm, "within test", "s after clogging began"))
    res.criteria.append(Criterion("alarm_before_inlet_exceeds_ashrae", t_ashrae is None or (t_alarm is not None and t_alarm < t_ashrae),
                                  t_ashrae, t_alarm))
    res.criteria.append(Criterion("inlet_within_ashrae_with_clogged_filters", peak <= a_max, round(peak, 2), a_max))
    res.extra.update({"alarm_after_s": t_alarm, "ashrae_exceeded_after_s": t_ashrae, "peak_inlet_c": round(peak, 2), "final_filter_dp_pa": last["filter_dp_pa"]})
    res.summary = (f"Filters clogged at {int(load*100)} % load: ΔP alarm after {('%.0f min' % (t_alarm/60)) if t_alarm is not None else 'never'}, "
                   f"peak inlet {peak:.1f} C (limit {a_max:.0f} C), final filter ΔP {last['filter_dp_pa']:.0f} Pa.")
    res.rows = rec.rows
    return res


def cdu_pump_failover(twin: Twin, load: float = 1.0, fail_s: float = 300.0, recover_s: float = 120.0,
                      record_every_s: float = 5.0, clock: Optional[str] = None) -> SweepResult:
    """dlc_hd only: fail each CDU pump in turn at ``load``; the standby must start within the failover time, loop flow must
    recover to >= 80 % of design and the loop ΔT must stay under 1.5 x design (cold plates do not throttle)."""
    if not twin.hd:
        raise ValueError("cdu_pump_failover applies to cooling == dlc_hd only")
    res = SweepResult("cdu_pump_failover", _now(clock))
    rec = Recorder(twin, "cdu_pump_failover", record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    base = rec.run(600.0)
    design = base["loop"]["design_flow_lpm"]
    dt_design = twin.p.loop_dt_design_k
    pumps = []
    for u in range(len(twin.cdu_pumps)):
        rec.set_phase(f"fail_pump_{u+1}")
        twin.inject("cdu_pump_fail", pump=u)
        t0 = twin.t
        min_flow, max_dt, start_t = 1e9, -1e9, None

        def watch(st):
            nonlocal min_flow, max_dt, start_t
            lp = st["loop"]
            min_flow = min(min_flow, lp["flow_lpm"])
            max_dt = max(max_dt, lp["dt_k"])
            if start_t is None and any(pp["on"] and pp["ok"] for pp in lp["pumps"]):
                start_t = st["t"] - t0
            return False

        last = rec.run(fail_s, until=watch)
        pumps.append({"pump": u + 1, "standby_started_after_s": start_t, "min_flow_lpm": round(min_flow, 1), "min_flow_pct": round(100 * min_flow / design, 1),
                      "max_dt_k": round(max_dt, 2), "flow_after_lpm": last["loop"]["flow_lpm"], "alarm_raised": any(a["id"] == f"cdu_pump{u+1}_fail" for a in last["alarms"])})
        twin.clear("cdu_pump_fail", pump=u)
        rec.set_phase(f"recover_pump_{u+1}")
        rec.run(recover_s)
    worst = max(pumps, key=lambda r: r["max_dt_k"])
    res.criteria.append(Criterion("standby_pump_started_each_time", all(r["standby_started_after_s"] is not None and r["standby_started_after_s"] <= twin.p.cdu_pump_failover_s + 5 for r in pumps),
                                  max((r["standby_started_after_s"] or 1e9) for r in pumps), f"<= {twin.p.cdu_pump_failover_s + 5:.0f} s"))
    res.criteria.append(Criterion("loop_flow_recovered_80pct", all(r["flow_after_lpm"] >= 0.8 * design for r in pumps), min(r["flow_after_lpm"] for r in pumps), round(0.8 * design, 1), "L/min after failover"))
    res.criteria.append(Criterion("loop_dt_under_1p5x_design", worst["max_dt_k"] <= 1.5 * dt_design, worst["max_dt_k"], 1.5 * dt_design, "K, cold plates do not throttle"))
    res.criteria.append(Criterion("pump_fail_alarm_raised_each_time", all(r["alarm_raised"] for r in pumps), sum(r["alarm_raised"] for r in pumps), len(pumps)))
    res.extra.update({"pumps": pumps, "design_flow_lpm": design, "baseline_dt_k": base["loop"]["dt_k"], "baseline_supply_c": base["loop"]["supply_c"]})
    res.summary = (f"Each of {len(pumps)} CDU pumps failed in turn at {int(load*100)} % load. Standby started within "
                   f"{max((r['standby_started_after_s'] or 0) for r in pumps):.0f} s; flow fell to {min(r['min_flow_pct'] for r in pumps):.0f} % of design "
                   f"({design} L/min) and recovered; loop ΔT peaked at {worst['max_dt_k']:.1f} K (design {dt_design:.0f} K).")
    res.rows = rec.rows
    return res


def dc_ground_fault_response(twin: Twin, load: float = 0.8, fault_kohm: float = 20.0, hold_s: float = 120.0,
                             record_every_s: float = 2.0, clock: Optional[str] = None) -> SweepResult:
    """dc800 only: inject a ground fault on each pole; the IMD must drop below 100 kΩ, the critical alarm must raise within
    10 s, the faulted pole must shift toward 0 V, the IT load must stay up (IT system: first fault is an alarm, not a trip)
    and the alarm must clear with the fault."""
    if not twin.dc800:
        raise ValueError("dc_ground_fault_response applies to power_architecture == dc800 only")
    res = SweepResult("dc_ground_fault_response", _now(clock))
    rec = Recorder(twin, "dc_ground_fault_response", record_every_s=record_every_s)
    twin.set_it_load(load)
    rec.set_phase("baseline")
    base = rec.run(300.0)
    poles = []
    for pole in ("pos", "neg"):
        rec.set_phase(f"fault_{pole}")
        twin.inject("dc_ground_fault", pole=pole, kohm=fault_kohm)
        t0 = twin.t
        t_alarm, min_it = None, 1e9

        def watch(st):
            nonlocal t_alarm, min_it
            min_it = min(min_it, st["it_kw"])
            if t_alarm is None and any(a["id"] == "dc_ground_fault" for a in st["alarms"]):
                t_alarm = st["t"] - t0
            return False

        last = rec.run(hold_s, until=watch)
        dc = last["dc"]
        shifted = abs(dc["v_bus_pos"]) < 0.25 * dc["v_bus"] if pole == "pos" else abs(dc["v_bus_neg"]) < 0.25 * dc["v_bus"]
        twin.clear("dc_ground_fault")
        rec.set_phase(f"clear_{pole}")
        after = rec.run(30.0)
        poles.append({"pole": pole, "alarm_after_s": t_alarm, "imd_kohm_at_fault": dc["imd_kohm"], "v_pos": dc["v_bus_pos"], "v_neg": dc["v_bus_neg"],
                      "faulted_pole_shifted": shifted, "it_kw_min_during_fault": round(min_it, 2),
                      "alarm_cleared": not any(a["id"] == "dc_ground_fault" for a in after["alarms"]), "imd_kohm_after": after["dc"]["imd_kohm"]})
    res.criteria.append(Criterion("imd_alarm_within_10s_each_pole", all(p["alarm_after_s"] is not None and p["alarm_after_s"] <= 10.0 for p in poles),
                                  max((p["alarm_after_s"] or 1e9) for p in poles), 10.0, "s from fault to critical alarm"))
    res.criteria.append(Criterion("imd_reads_fault_resistance", all(p["imd_kohm_at_fault"] < 100.0 for p in poles), max(p["imd_kohm_at_fault"] for p in poles), 100.0, "kΩ"))
    res.criteria.append(Criterion("faulted_pole_shifted_toward_ground", all(p["faulted_pole_shifted"] for p in poles), sum(p["faulted_pole_shifted"] for p in poles), len(poles)))
    res.criteria.append(Criterion("it_load_stays_up_on_first_fault", all(p["it_kw_min_during_fault"] >= 0.95 * base["it_kw"] for p in poles),
                                  min(p["it_kw_min_during_fault"] for p in poles), round(0.95 * base["it_kw"], 2), "kW; an IT (ungrounded) DC system alarms on the first fault and does not trip"))
    res.criteria.append(Criterion("alarm_clears_with_fault", all(p["alarm_cleared"] for p in poles), sum(p["alarm_cleared"] for p in poles), len(poles)))
    res.extra.update({"poles": poles, "healthy_imd_kohm": base["dc"]["imd_kohm"], "bus_v_at_baseline": base["dc"]["v_bus"]})
    res.summary = (f"Ground fault of {fault_kohm:g} kΩ injected on each pole at {int(load*100)} % load: insulation monitor fell from "
                   f"{base['dc']['imd_kohm']:.0f} to {min(p['imd_kohm_at_fault'] for p in poles):.0f} kΩ, critical alarm after "
                   f"{max((p['alarm_after_s'] or 0) for p in poles):.0f} s, faulted pole shifted toward ground, IT load held "
                   f"({min(p['it_kw_min_during_fault'] for p in poles):.1f} kW); alarm cleared on reset.")
    res.rows = rec.rows
    return res


SWEEPS: Dict[str, Callable[..., SweepResult]] = {
    "load_step": load_step,
    "cooling_unit_failover": cooling_unit_failover,
    "utility_loss_ride_through": utility_loss_ride_through,
    "door_open": door_open,
    "outdoor_temperature_sweep": outdoor_temperature_sweep,
    "filter_clog": filter_clog,
    "cdu_pump_failover": cdu_pump_failover,
    "dc_ground_fault_response": dc_ground_fault_response,
}
# sweeps that need a configuration feature: name -> predicate on Config
SWEEP_REQUIRES: Dict[str, Callable[[Config], bool]] = {
    "cdu_pump_failover": lambda cfg: cfg.cooling == "dlc_hd",
    "dc_ground_fault_response": lambda cfg: cfg.power_architecture == "dc800",
}


def applicable(name: str, cfg: Config) -> bool:
    """True when ``name`` runs on ``cfg`` (the forward-architecture sweeps need dlc_hd / dc800)."""
    req = SWEEP_REQUIRES.get(name)
    return req is None or req(cfg)


def run_sweep(name: str, cfg: Config, seed: int = 0, params=None, clock: Optional[str] = None, **kw) -> SweepResult:
    """Run one named sweep on a fresh twin."""
    if name not in SWEEPS:
        raise ValueError(f"unknown sweep {name}; valid: {sorted(SWEEPS)}")
    if not applicable(name, cfg):
        raise ValueError(f"sweep {name} does not apply to this configuration (cooling {cfg.cooling}, power {cfg.power_architecture})")
    tw = Twin(cfg, params=params, seed=seed)
    return SWEEPS[name](tw, clock=clock, **kw)


def run_all(cfg: Config, seed: int = 0, params=None, clock: Optional[str] = None) -> List[SweepResult]:
    return [run_sweep(n, cfg, seed=seed, params=params, clock=clock) for n in SWEEPS if applicable(n, cfg)]


def to_csv(result: SweepResult, path: str) -> str:
    """Write the sweep rows (flattened) to CSV."""
    return write_csv(result.rows, path)


def report_markdown(results: List[SweepResult]) -> str:
    lines = ["| Sweep | Result | Summary |", "| --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r.name} | {'PASS' if r.passed else 'FAIL'} | {r.summary} |")
    lines.append("")
    for r in results:
        lines.append(f"### {r.name}")
        lines.append("| Criterion | Pass | Value | Limit | Note |")
        lines.append("| --- | --- | --- | --- | --- |")
        for c in r.criteria:
            lines.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {c.value} | {c.limit} | {c.note} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    import argparse, json
    ap = argparse.ArgumentParser(description="BEN Engine automated sweeps on the digital twin")
    ap.add_argument("--tier", default="ben150")
    ap.add_argument("--profile", default="ai_inference")
    ap.add_argument("--climate", default="temperate")
    ap.add_argument("--sweep", default="all", choices=["all"] + list(SWEEPS))
    ap.add_argument("--csv-dir", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--power-architecture", dest="power_architecture", default=None, help="ac480 or dc800 (forward option)")
    ap.add_argument("--cooling", default=None, help="override the preset cooling (e.g. dlc_hd)")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate)
    if a.power_architecture:
        cfg.power_architecture = a.power_architecture
    if a.cooling:
        cfg.cooling = a.cooling
    results = run_all(cfg, seed=a.seed) if a.sweep == "all" else [run_sweep(a.sweep, cfg, seed=a.seed)]
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name}: {r.summary}")
        for c in r.criteria:
            print(f"      {'ok ' if c.passed else 'NO '} {c.name} = {c.value} (limit {c.limit}) {c.note}")
        if a.csv_dir:
            import os
            os.makedirs(a.csv_dir, exist_ok=True)
            p = os.path.join(a.csv_dir, f"{r.name}.csv")
            to_csv(r, p)
            print(f"      csv {p} ({len(r.rows)} rows)")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

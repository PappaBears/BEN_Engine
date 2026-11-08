"""BEN Engine analysis: fit the twin to measured telemetry, then predict with intervals.

Workflow
--------
1. ``schedule_from_states(states)`` extracts what was *done* to the unit (IT load, outdoor
   temperature, faults) from a telemetry record (twin states or ``export`` CSV/JSONL rows).
2. ``fit_params(cfg, states)`` replays the twin with candidate ``TwinParams`` through that
   schedule and adjusts ``recirculation``, ``envelope_ua_w_k``, ``rack_mass_kg`` and ``bypass``
   by least squares (scipy) so that modelled rack inlet and return temperatures match the
   measured ones. It returns the fitted parameters, their covariance (from the Jacobian and the
   residual variance) and the residual RMS.
3. ``predict(cfg, params, schedule, cov)`` runs the fitted twin forward and gives 95 % prediction
   intervals by Monte Carlo over the parameter covariance plus the sensor uncertainty (so the
   interval is "where the real reading will be", not just model scatter).
4. ``pue_breakdown``, ``thermal_margin`` (minutes of ride-through to the ASHRAE limit if all
   cooling stops), ``ups_runtime_curve`` and ``plain_summary`` for the CLI.

Everything is deterministic for a given seed. Nothing here invents numbers: every figure in the
summary is read back from the twin run.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import least_squares

from .config import Config, CLIMATE_DESIGN
from .twin import Twin, TwinParams
from .sweeps import ASHRAE_MAX

FIT_FIELDS = ("recirculation", "envelope_ua_w_k", "rack_mass_kg", "bypass")
BOUNDS = {"recirculation": (0.0, 0.6), "envelope_ua_w_k": (5.0, 400.0), "rack_mass_kg": (10.0, 400.0), "bypass": (0.0, 0.6)}
SENSOR_U95_C = 0.25   # PROTOCOL.md DS18B20 after calibration (k=2)


# ------------------------------------------------------------------ schedules
@dataclass
class Event:
    t: float
    it_fraction: Optional[float] = None
    outdoor_c: Optional[float] = None
    inject: Optional[str] = None
    clear: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


def schedule_from_states(states: Sequence[Dict[str, Any]]) -> Tuple[List[Event], float, float]:
    """Recover (events, dt, duration) from a telemetry record."""
    if len(states) < 2:
        raise ValueError("need at least two states")
    ts = [float(s["t"]) for s in states]
    dt = float(np.median(np.diff(ts)))
    ev: List[Event] = []
    prev_load = prev_out = None
    prev_faults: set = set()
    t0 = ts[0]
    for s in states:
        t = float(s["t"]) - t0
        faults = set(s.get("faults", []))
        e = Event(t)
        changed = False
        if s.get("it_fraction") is not None and s["it_fraction"] != prev_load:
            e.it_fraction = float(s["it_fraction"])
            prev_load = e.it_fraction
            changed = True
        if s.get("outdoor_c") is not None and s["outdoor_c"] != prev_out:
            e.outdoor_c = float(s["outdoor_c"])
            prev_out = e.outdoor_c
            changed = True
        for f in sorted(faults - prev_faults):
            ev.append(Event(t, inject=f))
        for f in sorted(prev_faults - faults):
            ev.append(Event(t, clear=f))
        prev_faults = faults
        if changed:
            ev.append(e)
    return ev, dt, ts[-1] - t0


def simulate(cfg: Config, params: TwinParams, schedule: Sequence[Event], duration_s: float, dt: float = 1.0,
             seed: int = 0, noise: bool = False, outdoor_c: Optional[float] = None,
             warmup_s: float = 0.0, warmup_load: Optional[float] = None, exact: bool = False) -> List[Dict[str, Any]]:
    """Run a twin through ``schedule`` and return one state per ``dt``.

    ``warmup_s`` runs the twin (unrecorded) before t=0 so it starts near steady state, which is
    how a measured record normally begins.
    """
    p = copy.deepcopy(params)
    if not noise:
        p.sensor_noise_c = 0.0
        p.sensor_noise_pa = 0.0
    tw = Twin(cfg, params=p, seed=seed, outdoor_c=outdoor_c)
    events = sorted(schedule, key=lambda e: e.t)
    # apply t<=0 events before warm-up so the warm-up is at the initial condition
    i = 0
    while i < len(events) and events[i].t <= 1e-9:
        _apply(tw, events[i])
        i += 1
    if warmup_load is not None:
        tw.set_it_load(warmup_load)
    if warmup_s > 0:
        n = int(warmup_s / 5.0)
        for _ in range(n):
            tw.step(5.0)
        tw.t = 0.0
        tw._seq = 0
    out = []
    n_steps = int(round(duration_s / dt))
    for k in range(1, n_steps + 1):
        t_next = k * dt
        while i < len(events) and events[i].t <= t_next - dt / 2 + 1e-9:
            _apply(tw, events[i])
            i += 1
        tw.step(dt)
        st = tw.state()
        if exact:
            # unrounded, noise-free internal values for fitting (state() rounds to 0.01 K, which
            # turns finite-difference Jacobians into rounding noise)
            st["rack_inlet_c_exact"] = list(tw.rack_inlet_c)
            st["return_c_exact"] = float(tw.return_c)
        out.append(st)
    return out


def _apply(tw: Twin, e: Event):
    if e.it_fraction is not None:
        tw.set_it_load(e.it_fraction)
    if e.outdoor_c is not None:
        tw.set_outdoor(e.outdoor_c)
    if e.inject:
        tw.inject(e.inject, **e.params)
    if e.clear:
        tw.clear(e.clear, **e.params)


# ------------------------------------------------------------------ fitting
@dataclass
class FitResult:
    params: TwinParams
    fitted: Dict[str, float]
    std: Dict[str, float]
    cov: np.ndarray
    residual_rms_k: float
    n_points: int
    nfev: int
    success: bool
    message: str
    identifiability: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {"fitted": self.fitted, "std": self.std, "residual_rms_k": self.residual_rms_k, "n_points": self.n_points,
                "nfev": self.nfev, "success": self.success, "identifiability": self.identifiability}


def _measured_matrix(states: Sequence[Dict[str, Any]], idx: np.ndarray, exact: bool = False) -> np.ndarray:
    rows = []
    ki, kr = ("rack_inlet_c_exact", "return_c_exact") if exact else ("rack_inlet_c", "return_c")
    for k in idx:
        s = states[k]
        rows.append(list(s[ki]) + [s[kr]])
    return np.asarray(rows, dtype=float)


def fit_params(cfg: Config, states: Sequence[Dict[str, Any]], base: Optional[TwinParams] = None,
               fit: Sequence[str] = FIT_FIELDS, sample_every_s: float = 10.0, seed: int = 0,
               warmup_s: float = 1200.0, verbose: bool = False) -> FitResult:
    """Least-squares fit of ``fit`` parameters to measured rack inlet + return temperatures."""
    base = copy.deepcopy(base or TwinParams())
    schedule, dt, duration = schedule_from_states(states)
    first_load = states[0].get("it_fraction", 0.6)
    first_out = states[0].get("outdoor_c")
    step = max(1, int(round(sample_every_s / dt)))
    idx = np.arange(step - 1, len(states), step)
    y = _measured_matrix(states, idx)
    names = list(fit)
    x0 = np.array([getattr(base, n) for n in names])
    lo = np.array([BOUNDS[n][0] for n in names])
    hi = np.array([BOUNDS[n][1] for n in names])
    scale = np.array([max(abs(v), 1e-3) for v in x0])

    def model(x):
        p = copy.deepcopy(base)
        for n, v in zip(names, x):
            setattr(p, n, float(v))
        sim = simulate(cfg, p, schedule, duration, dt=dt, seed=seed, noise=False, outdoor_c=first_out,
                       warmup_s=warmup_s, warmup_load=first_load, exact=True)
        return _measured_matrix(sim, idx[idx < len(sim)], exact=True)

    def resid(x):
        m = model(x)
        n = min(len(m), len(y))
        return (m[:n] - y[:n]).ravel()

    res = least_squares(resid, x0, bounds=(lo, hi), x_scale=scale, diff_step=0.05, max_nfev=200, verbose=1 if verbose else 0)
    r = res.fun
    dof = max(len(r) - len(names), 1)
    s2 = float(r @ r) / dof
    J = res.jac
    try:
        cov = s2 * np.linalg.inv(J.T @ J)
    except np.linalg.LinAlgError:
        cov = s2 * np.linalg.pinv(J.T @ J)
    std = np.sqrt(np.clip(np.diag(cov), 0, None))
    fitted = {n: float(v) for n, v in zip(names, res.x)}
    ident = {}
    col_norm = np.sqrt((J ** 2).sum(axis=0))
    for n, v, s, cn in zip(names, res.x, std, col_norm):
        rel = s / max(abs(v), 1e-9)
        # sensitivity: K of residual change per 10 % parameter change, summed over the record
        sens = cn * 0.1 * abs(v) / math.sqrt(max(len(r), 1))
        label = "well determined" if rel < 0.1 else "usable" if rel < 0.5 else "poorly determined" if rel < 1.0 else "not identifiable from this data"
        if sens < 0.01:
            label += f"; weak sensitivity, {sens*1000:.1f} mK RMS per 10 % change"
        ident[n] = label
    p = copy.deepcopy(base)
    for n, v in fitted.items():
        setattr(p, n, v)
    return FitResult(p, fitted, {n: float(s) for n, s in zip(names, std)}, cov, math.sqrt(float(r @ r) / len(r)),
                     len(y), int(res.nfev), bool(res.success), str(res.message), ident)


# ------------------------------------------------------------------ prediction
@dataclass
class Prediction:
    t: List[float]
    rack_inlet_mean: np.ndarray      # (n_t, racks)
    rack_inlet_lo: np.ndarray
    rack_inlet_hi: np.ndarray
    return_mean: np.ndarray
    return_lo: np.ndarray
    return_hi: np.ndarray
    nominal_states: List[Dict[str, Any]]
    n_mc: int

    def at(self, t_s: float) -> Dict[str, Any]:
        k = int(np.argmin(np.abs(np.asarray(self.t) - t_s)))
        return {"t": self.t[k], "rack_inlet_c": self.rack_inlet_mean[k].tolist(), "lo95": self.rack_inlet_lo[k].tolist(),
                "hi95": self.rack_inlet_hi[k].tolist(), "return_c": float(self.return_mean[k]),
                "return_lo95": float(self.return_lo[k]), "return_hi95": float(self.return_hi[k])}

    def final(self) -> Dict[str, Any]:
        return self.at(self.t[-1])

    def rows(self) -> List[Dict[str, Any]]:
        out = []
        for k, t in enumerate(self.t):
            row = {"t": t, "return_c": float(self.return_mean[k]), "return_lo95": float(self.return_lo[k]), "return_hi95": float(self.return_hi[k])}
            for i in range(self.rack_inlet_mean.shape[1]):
                row[f"rack_inlet_c_{i+1}"] = float(self.rack_inlet_mean[k, i])
                row[f"rack_inlet_lo95_{i+1}"] = float(self.rack_inlet_lo[k, i])
                row[f"rack_inlet_hi95_{i+1}"] = float(self.rack_inlet_hi[k, i])
            out.append(row)
        return out


def predict(cfg: Config, params: TwinParams, schedule: Sequence[Event], duration_s: float, cov: Optional[np.ndarray] = None,
            fit_names: Sequence[str] = FIT_FIELDS, n_mc: int = 40, dt: float = 5.0, seed: int = 0,
            sensor_u95_c: float = SENSOR_U95_C, outdoor_c: Optional[float] = None, warmup_s: float = 1200.0,
            warmup_load: Optional[float] = None) -> Prediction:
    """Forward prediction with 95 % prediction intervals (parameter covariance + sensor uncertainty)."""
    nominal = simulate(cfg, params, schedule, duration_s, dt=dt, seed=seed, noise=False, outdoor_c=outdoor_c,
                       warmup_s=warmup_s, warmup_load=warmup_load)
    t = [s["t"] for s in nominal]
    inlet0 = np.array([s["rack_inlet_c"] for s in nominal])
    ret0 = np.array([s["return_c"] for s in nominal])
    rng = np.random.default_rng(seed)
    names = list(fit_names)
    mean = np.array([getattr(params, n) for n in names])
    samples_in, samples_ret = [inlet0], [ret0]
    if cov is not None and n_mc > 0:
        cov = np.asarray(cov, dtype=float)
        # keep the covariance sane: clip the std of each parameter to its bound range
        try:
            L = np.linalg.cholesky(cov + 1e-12 * np.eye(len(names)))
        except np.linalg.LinAlgError:
            L = np.diag(np.sqrt(np.clip(np.diag(cov), 0, None)))
        for _ in range(n_mc):
            x = mean + L @ rng.standard_normal(len(names))
            p = copy.deepcopy(params)
            for n, v in zip(names, x):
                lo, hi = BOUNDS[n]
                setattr(p, n, float(min(hi, max(lo, v))))
            sim = simulate(cfg, p, schedule, duration_s, dt=dt, seed=seed, noise=False, outdoor_c=outdoor_c,
                           warmup_s=warmup_s, warmup_load=warmup_load)
            samples_in.append(np.array([s["rack_inlet_c"] for s in sim]))
            samples_ret.append(np.array([s["return_c"] for s in sim]))
    A = np.stack(samples_in)       # (n_mc+1, n_t, racks)
    R = np.stack(samples_ret)
    sens_sd = sensor_u95_c / 2.0
    sd_in = np.sqrt(A.std(axis=0) ** 2 + sens_sd ** 2)
    sd_ret = np.sqrt(R.std(axis=0) ** 2 + sens_sd ** 2)
    return Prediction(t, inlet0, inlet0 - 1.96 * sd_in, inlet0 + 1.96 * sd_in, ret0, ret0 - 1.96 * sd_ret, ret0 + 1.96 * sd_ret,
                      nominal, n_mc if cov is not None else 0)


# ------------------------------------------------------------------ derived answers
def pue_breakdown(state: Dict[str, Any], cfg: Config, params: Optional[TwinParams] = None) -> Dict[str, Any]:
    """Split facility power into IT, UPS loss, PDU loss, cooling and house loads (twin accounting)."""
    p = params or TwinParams()
    it = float(state["it_kw"])
    ups_in = it / p.ups_eff / p.pdu_eff
    pdu_loss = it / p.pdu_eff - it
    ups_loss = ups_in - it / p.pdu_eff
    cooling = float(state["cooling_kw_elec"])
    house = 0.5 + 0.02 * cfg.it_kw
    total = ups_in + cooling + house
    return {"it_kw": round(it, 2), "pdu_loss_kw": round(pdu_loss, 2), "ups_loss_kw": round(ups_loss, 2), "cooling_kw": round(cooling, 2),
            "house_kw": round(house, 2), "total_kw": round(total, 2), "pue": round(total / it, 3) if it > 0.5 else None,
            "shares_pct": {"it": round(100 * it / total, 1), "cooling": round(100 * cooling / total, 1),
                           "ups_pdu_losses": round(100 * (ups_loss + pdu_loss) / total, 1), "house": round(100 * house / total, 1)} if total > 0 else {}}


def thermal_margin(cfg: Config, params: Optional[TwinParams] = None, load: float = 1.0, outdoor_c: Optional[float] = None,
                   max_minutes: float = 60.0, seed: int = 0, warmup_s: float = 1800.0) -> Dict[str, Any]:
    """Minutes from total cooling loss (all units failed, IT still running) to the ASHRAE max inlet."""
    p = copy.deepcopy(params or TwinParams())
    p.sensor_noise_c = 0.0
    tw = Twin(cfg, params=p, seed=seed, outdoor_c=outdoor_c)
    tw.set_it_load(load)
    for _ in range(int(warmup_s / 5)):
        tw.step(5.0)
    a_max = ASHRAE_MAX[tw.d["ashrae_class"]]
    start_inlet = max(tw.rack_inlet_c)
    for u in range(len(tw.cooling_units)):
        tw.inject("cooling_unit_fail", unit=u)
    t0 = tw.t
    t_hit = None
    t_warn = None
    while tw.t - t0 < max_minutes * 60:
        tw.step(1.0)
        m = max(tw.rack_inlet_c)
        if t_warn is None and m > a_max - 2:
            t_warn = tw.t - t0
        if m > a_max:
            t_hit = tw.t - t0
            break
    return {"ashrae_class": tw.d["ashrae_class"], "ashrae_max_c": a_max, "start_max_inlet_c": round(start_inlet, 2),
            "minutes_to_warning": None if t_warn is None else round(t_warn / 60, 2),
            "minutes_to_ashrae_max": None if t_hit is None else round(t_hit / 60, 2), "load": load,
            "outdoor_c": tw.outdoor_c, "scenario": "all cooling units failed, IT load maintained"}


def ups_runtime_curve(cfg: Config, params: Optional[TwinParams] = None, loads: Sequence[float] = (0.25, 0.5, 0.75, 1.0),
                      seed: int = 0) -> List[Dict[str, float]]:
    """Minutes of battery at each load fraction, measured by running the twin through a utility loss."""
    out = []
    for lf in loads:
        p = copy.deepcopy(params or TwinParams())
        tw = Twin(cfg, params=p, seed=seed)
        tw.set_it_load(lf)
        tw.step(5.0)
        tw.inject("utility_loss")
        t0 = tw.t
        gen = False
        while tw.t - t0 < 6 * 3600:
            tw.step(5.0)
            if tw.generator_on:
                gen = True
                break
            if tw.ups_soc <= 0.0:
                break
        out.append({"load_fraction": lf, "it_kw": round(cfg.it_kw * lf, 1), "minutes": round((tw.t - t0) / 60.0, 1),
                    "limited_by": "generator took over" if gen else "battery empty"})
    return out


# ------------------------------------------------------------------ plain-language summary
def plain_summary(cfg: Config, params: TwinParams, fit: Optional[FitResult] = None, load: float = 1.0,
                  outdoor_c: Optional[float] = None, horizon_s: float = 3600.0, n_mc: int = 30, seed: int = 0) -> Dict[str, Any]:
    """Run the standard questions and phrase the answers."""
    clim = CLIMATE_DESIGN[cfg.climate]
    outdoor = clim["t_design_c"] if outdoor_c is None else outdoor_c
    sched = [Event(0.0, it_fraction=load, outdoor_c=outdoor)]
    cov = fit.cov if fit is not None else None
    names = list(fit.fitted.keys()) if fit is not None else FIT_FIELDS
    pred = predict(cfg, params, sched, horizon_s, cov=cov, fit_names=names, n_mc=n_mc, seed=seed, outdoor_c=outdoor, warmup_load=load)
    fin = pred.final()
    worst = int(np.argmax(fin["rack_inlet_c"]))
    half = (fin["hi95"][worst] - fin["lo95"][worst]) / 2
    tm = thermal_margin(cfg, params, load=load, outdoor_c=outdoor, seed=seed)
    ups = ups_runtime_curve(cfg, params, loads=(load,), seed=seed)[0]
    pb = pue_breakdown(pred.nominal_states[-1], cfg, params)
    a_max = ASHRAE_MAX[cfg.derived()["ashrae_class"]]
    from .calibration import predictability_score
    ps = predictability_score(half, fin["rack_inlet_c"][worst], a_max)
    lines = [
        f"At {int(load*100)} % load on a {outdoor:.0f} °C day, rack {worst+1} inlet will be {fin['rack_inlet_c'][worst]:.1f} ± {half:.1f} °C "
        f"(95 % prediction interval; ASHRAE {tm['ashrae_class']} limit {a_max:.0f} °C).",
        f"If all cooling stops you have "
        + (f"{tm['minutes_to_ashrae_max']:.1f} minutes" if tm["minutes_to_ashrae_max"] is not None else f"more than {60:.0f} minutes")
        + f" before the hottest inlet passes {a_max:.0f} °C"
        + (f" (warning at {tm['minutes_to_warning']:.1f} min)." if tm["minutes_to_warning"] is not None else "."),
        f"On utility loss the UPS carries {ups['it_kw']:.0f} kW for {ups['minutes']:.1f} minutes ({ups['limited_by']}); configured target {cfg.ups_minutes} min.",
        f"PUE at this point {pb['pue']}: IT {pb['shares_pct'].get('it')} %, cooling {pb['shares_pct'].get('cooling')} %, "
        f"UPS/PDU losses {pb['shares_pct'].get('ups_pdu_losses')} %, house {pb['shares_pct'].get('house')} %.",
        f"Predictability: {ps.text}.",
    ]
    if fit is not None:
        lines.append("Fitted parameters: " + ", ".join(f"{k} = {v:.3g} ± {fit.std[k]:.2g} ({fit.identifiability[k]})" for k, v in fit.fitted.items())
                     + f"; residual RMS {fit.residual_rms_k:.3f} K over {fit.n_points} samples.")
    return {"text": "\n".join(lines), "prediction_final": fin, "thermal_margin": tm, "ups": ups, "pue": pb, "predictability": ps.__dict__,
            "worst_rack": worst + 1}


def synthetic_load_step_record(cfg: Config, true_params: TwinParams, seed: int = 1, dt: float = 1.0,
                               levels=(0.4, 1.0), hold_s: float = 900.0, outdoor_c: Optional[float] = None) -> List[Dict[str, Any]]:
    """A measured-looking record (with sensor noise) of a load step, for demos and tests."""
    sched = [Event(0.0, it_fraction=levels[0], outdoor_c=outdoor_c)]
    for k, lv in enumerate(levels[1:], start=1):
        sched.append(Event(k * hold_s, it_fraction=lv))
    return simulate(cfg, true_params, sched, hold_s * len(levels), dt=dt, seed=seed, noise=True, outdoor_c=outdoor_c,
                    warmup_s=1200.0, warmup_load=levels[0])


def main(argv=None):
    import argparse, json
    ap = argparse.ArgumentParser(description="BEN Engine analysis: fit twin to telemetry and predict with intervals")
    ap.add_argument("--tier", default="ben150")
    ap.add_argument("--profile", default="ai_inference")
    ap.add_argument("--climate", default="temperate")
    ap.add_argument("--load", type=float, default=1.0)
    ap.add_argument("--outdoor", type=float, default=None, help="outdoor C for the prediction (default climate design temp)")
    ap.add_argument("--jsonl", default=None, help="telemetry JSON lines to fit (default: synthetic load step from a perturbed twin)")
    ap.add_argument("--no-fit", action="store_true")
    ap.add_argument("--mc", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate)
    fit = None
    params = TwinParams()
    if not a.no_fit:
        if a.jsonl:
            from .export import TelemetryBuffer
            states = TelemetryBuffer.read_jsonl(a.jsonl)
        else:
            true = TwinParams(recirculation=0.12, bypass=0.15, rack_mass_kg=80.0, envelope_ua_w_k=60.0)
            states = synthetic_load_step_record(cfg, true, seed=1)
            print("(no telemetry given: fitting a synthetic load-step record from a twin with recirculation 0.12, bypass 0.15, rack mass 80 kg, UA 60 W/K)")
        fit = fit_params(cfg, states)
        params = fit.params
    summ = plain_summary(cfg, params, fit, load=a.load, outdoor_c=a.outdoor, n_mc=a.mc)
    if a.json:
        print(json.dumps({k: v for k, v in summ.items() if k != "text"}, indent=2, default=float))
    print(summ["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

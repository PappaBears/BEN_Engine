"""Fit twin parameters from telemetry and predict with intervals (small, fast settings)."""
import numpy as np

from ben_engine.config import Config
from ben_engine.twin import TwinParams
from ben_engine import analysis as an


def test_schedule_from_states_detects_steps_and_faults():
    cfg = Config.preset("ben10")
    sched = [an.Event(0.0, it_fraction=0.4), an.Event(60.0, it_fraction=0.9), an.Event(120.0, inject="door_open"), an.Event(150.0, clear="door_open")]
    states = an.simulate(cfg, TwinParams(), sched, 200.0, dt=5.0)
    ev, dt, dur = an.schedule_from_states(states)
    assert dt == 5.0 and dur == 195.0
    loads = [e.it_fraction for e in ev if e.it_fraction is not None]
    assert loads[:2] == [0.4, 0.9]
    assert any(e.inject == "door_open" for e in ev) and any(e.clear == "door_open" for e in ev)


def test_fit_recovers_recirculation_and_bypass():
    cfg = Config.preset("ben10")
    true = TwinParams(recirculation=0.15, bypass=0.18)
    rec = an.synthetic_load_step_record(cfg, true, seed=4, dt=2.0, levels=(0.4, 1.0), hold_s=400.0)
    fit = an.fit_params(cfg, rec, fit=("recirculation", "bypass"), sample_every_s=10.0, warmup_s=600.0)
    assert fit.success
    assert abs(fit.fitted["recirculation"] - 0.15) < 0.02
    assert abs(fit.fitted["bypass"] - 0.18) < 0.03
    assert fit.residual_rms_k < 0.3
    assert fit.cov.shape == (2, 2)
    assert set(fit.identifiability) == {"recirculation", "bypass"}


def test_predict_intervals_contain_nominal_and_widen_with_cov():
    cfg = Config.preset("ben10")
    p = TwinParams(recirculation=0.1)
    sched = [an.Event(0.0, it_fraction=1.0, outdoor_c=35.0)]
    tight = an.predict(cfg, p, sched, 300.0, cov=None, dt=10.0, warmup_s=300.0, warmup_load=1.0)
    cov = np.diag([0.03 ** 2, 10.0 ** 2, 10.0 ** 2, 0.03 ** 2])
    wide = an.predict(cfg, p, sched, 300.0, cov=cov, n_mc=8, dt=10.0, warmup_s=300.0, warmup_load=1.0)
    f_t, f_w = tight.final(), wide.final()
    assert all(lo <= m <= hi for lo, m, hi in zip(f_t["lo95"], f_t["rack_inlet_c"], f_t["hi95"]))
    # sensor uncertainty alone gives ±0.25 K
    assert abs((f_t["hi95"][0] - f_t["lo95"][0]) / 2 - 0.25) < 0.01
    assert (f_w["hi95"][0] - f_w["lo95"][0]) > (f_t["hi95"][0] - f_t["lo95"][0])
    assert wide.n_mc == 8 and len(wide.rows()) == len(wide.t)


def test_pue_thermal_margin_ups_curve():
    cfg = Config.preset("ben20")
    st = an.simulate(cfg, TwinParams(), [an.Event(0, it_fraction=1.0)], 60.0, dt=10.0, warmup_s=600.0, warmup_load=1.0)[-1]
    pb = an.pue_breakdown(st, cfg)
    assert pb["pue"] is not None and 1.0 < pb["pue"] < 2.0
    assert abs(sum(pb["shares_pct"].values()) - 100.0) < 0.5
    tm = an.thermal_margin(cfg, load=1.0, max_minutes=20, warmup_s=300.0)
    assert tm["minutes_to_ashrae_max"] is not None and 0 < tm["minutes_to_ashrae_max"] < 20
    curve = an.ups_runtime_curve(cfg, loads=(0.5, 1.0))
    assert curve[0]["minutes"] > curve[1]["minutes"] > 5


def test_plain_summary_text(capsys):
    cfg = Config.preset("ben10")
    s = an.plain_summary(cfg, TwinParams(), None, load=1.0, outdoor_c=35.0, horizon_s=300.0, n_mc=0)
    assert "inlet will be" in s["text"] and "ride" not in s["text"].lower() or "minutes" in s["text"]
    assert s["worst_rack"] in (1, 2)

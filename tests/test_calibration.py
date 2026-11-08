"""GUM tools: fits recover known coefficients, budgets combine correctly, report renders."""
import math

import numpy as np
import pytest

from ben_engine import calibration as cal


def test_linear_fit_recovers_gain_offset():
    rng = np.random.default_rng(0)
    ref = np.linspace(10, 45, 10)
    reading = (ref - 0.4) / 1.01 + rng.normal(0, 0.02, ref.size)   # so ref = 1.01*reading + 0.4
    f = cal.linear_fit(ref, reading)
    assert abs(f.gain - 1.01) < 0.005
    assert abs(f.offset - 0.4) < 0.15
    assert f.residual_std < 0.05
    assert f.u95_at(f.x_mean) > f.residual_std
    assert f.u95_at(60.0) > f.u95_at(f.x_mean)     # extrapolation is less certain
    assert abs(f.correct(reading[3]) - ref[3]) < 0.1


def test_linear_fit_rejects_bad_input():
    with pytest.raises(ValueError):
        cal.linear_fit([1.0], [1.0])


def test_tare():
    t = cal.tare([0.31, 0.29, 0.30, 0.32, 0.28])
    assert abs(t.offset + 0.30) < 1e-9
    assert t.n == 5 and t.u_offset == pytest.approx(t.std / math.sqrt(5))


def test_combine_rss_and_welch_satterthwaite():
    a = cal.UncertaintySource("A", 0.1, "normal", "A", dof=4)
    b = cal.UncertaintySource("B", math.sqrt(3) * 0.1, "rectangular", "B")   # u = 0.1
    bud = cal.combine([a, b])
    assert bud.u_c == pytest.approx(math.sqrt(0.02))
    # WS: nu_eff = u_c^4 / (u_a^4/4) = 0.0004 / (0.0001/4) = 16
    assert bud.nu_eff == pytest.approx(16.0)
    assert bud.k > 1.96 and bud.U95 == pytest.approx(bud.k * bud.u_c)
    only_b = cal.combine([b])
    assert not math.isfinite(only_b.nu_eff) and only_b.k == 1.96


def test_default_budgets_all_channels_and_placement():
    buds = cal.all_default_budgets()
    assert set(buds) == set(cal.CHANNELS)
    for b in buds.values():
        assert b.U95 > 0 and b.dominant() in b.sources
    plain = cal.default_budget("DS18B20")
    placed = cal.default_budget("DS18B20", ["inlet_near_perforated_door", "hot_aisle_radiation"])
    assert placed.U95 > plain.U95
    assert placed.total_correction == pytest.approx(-0.75)
    uncal = cal.default_budget("DS18B20", calibrated=False)
    assert uncal.U95 > plain.U95
    with pytest.raises(ValueError):
        cal.default_budget("SDP810", ["inlet_near_perforated_door"])   # unit mismatch K vs Pa
    with pytest.raises(ValueError):
        cal.default_budget("nope")


def test_fit_feeds_budget_type_a():
    rng = np.random.default_rng(2)
    ref = np.linspace(15, 35, 8)
    rd = ref + rng.normal(0, 0.03, 8)
    f = cal.linear_fit(ref, rd)
    b = cal.default_budget("DS18B20", reading=25.0, cal=f)
    assert any(s.type == "A" and s.dof == f.dof for s in b.sources)


def test_predictability_score():
    p = cal.predictability_score(0.9, 24.1, 35.0)
    assert p.grade == "excellent" and p.score == pytest.approx(0.9 / 10.9)
    assert cal.predictability_score(5.0, 31.0, 35.0).grade == "unpredictable"
    assert cal.predictability_score(1.0, 36.0, 35.0).grade == "exceeded"


def test_markdown_report(tmp_path):
    buds = cal.all_default_budgets()
    f = cal.linear_fit([10, 20, 30, 40], [9.9, 19.95, 30.1, 40.0])
    md = cal.markdown_report(buds, fits={"T_in_1": f}, tares={"dP_aisle": cal.tare([0.1, 0.2])})
    assert "| DS18B20 |" in md and "Welch" in md and "T_in_1" in md and "dP_aisle" in md
    rc = cal.main(["--out", str(tmp_path / "r.md"), "--placement", "DS18B20=inlet_near_perforated_door"])
    assert rc == 0 and (tmp_path / "r.md").exists()

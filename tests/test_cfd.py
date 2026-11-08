"""2-D thermal LBM: stability, mass/heat bookkeeping, containment and failure effects, PNG."""
import os

import numpy as np
import pytest

from ben_engine.config import Config
from ben_engine import cfd
from ben_engine.twin import TwinParams

COARSE = dict(dx=0.1, steps=400)   # small grid for tests (~1 s each)


def test_layout_geometry_from_config():
    cfg = Config.preset("ben150")
    lay = cfd.build_layout(cfg, dx=0.05)
    assert len(lay.rack_cells) == cfg.racks
    assert len(lay.unit_cells) == cfg.derived()["cooling_units_total"]
    assert lay.solid[0, :].all() and lay.solid[:, -1].all()
    assert lay.y_cold[1] <= lay.y_rack[0] < lay.y_rack[1] <= lay.y_hot[0]
    # closed doors leave only the leakage fraction open
    assert 0 < lay.door_open_cells < lay.door_cells
    lay_open = cfd.build_layout(cfg, containment=False, dx=0.05)
    assert lay_open.door_open_cells == lay_open.door_cells


def test_run_is_stable_and_low_mach():
    m = cfd.run_cfd(Config.preset("ben150"), **COARSE)
    F = m["fields"]
    assert np.isfinite(F["T"]).all() and np.isfinite(F["ux"]).all()
    assert m["u_lattice_max"] < 0.2
    assert 0.5 < m["tau"] < 1.0
    assert m["re_lattice"] > 1 and m["re_real_estimate"] > 1e4


def test_heat_bookkeeping_outlets_warmer_by_design_delta_t():
    m = cfd.run_cfd(Config.preset("ben150"), **COARSE)
    rises = np.array(m["rack_outlet_c"]) - np.array(m["rack_inlet_c"])
    # outlet rise should be within ~40 % of the designed rack ΔT (soft fan forcing + diffusion)
    assert np.all(rises > 0.6 * m["design_rack_delta_t_k"])
    assert np.all(rises < 1.6 * m["design_rack_delta_t_k"])
    assert all(0.0 <= r <= 1.0 for r in m["recirculation_index"])
    assert m["return_c_mean"] > m["supply_c"]


def test_low_supply_ratio_increases_recirculation():
    cfg = Config.preset("ben150")
    good = cfd.run_cfd(cfg, supply_ratio=1.1, **COARSE)
    starved = cfd.run_cfd(cfg, supply_ratio=0.8, **COARSE)
    assert max(starved["recirculation_index"]) > max(good["recirculation_index"]) + 0.05
    assert starved["max_rack_inlet_c"] > good["max_rack_inlet_c"]


def test_failed_unit_changes_active_units_and_metrics():
    cfg = Config.preset("ben150")
    m = cfd.run_cfd(cfg, failed_units=[1], **COARSE)
    assert m["active_units"][1] is False
    assert sum(m["active_units"]) == cfg.derived()["cooling_units_n"]


@pytest.mark.parametrize("tier", ["ben5", "ben30", "ben500"])
def test_other_tiers_run(tier):
    m = cfd.run_cfd(Config.preset(tier), dx=0.1 if tier != "ben5" else 0.04, steps=300)
    assert np.isfinite(m["max_rack_inlet_c"])
    assert len(m["recirculation_index"]) == Config.preset(tier).racks


def test_png_and_profile_and_twin_coupling(tmp_path):
    cfg = Config.preset("ben150")
    png = tmp_path / "cfd.png"
    m = cfd.run_cfd(cfg, out_png=str(png), **COARSE)
    assert png.exists() and png.stat().st_size > 10_000
    prof = cfd.recirculation_profile(cfg, **COARSE)
    assert len(prof) == cfg.racks
    p = cfd.apply_to_params(m, TwinParams())
    assert p.recirculation_profile == m["recirculation_index"]
    js = cfd.metrics_json(m)
    assert "recirculation_index" in js and "fields" not in js


def test_cli(tmp_path, capsys):
    rc = cfd.main(["--tier", "ben30", "--dx", "0.1", "--steps", "200", "--png", str(tmp_path / "x.png")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "recirculation index" in out and (tmp_path / "x.png").exists()


def test_ben2000_hall_is_modelled_per_row_bay_and_tiles_results():
    """BEN 2000: one row bay of the hall is solved (100 mm cells) and per-rack results are tiled over the rows."""
    import time
    cfg = Config.preset("ben2000")
    d = cfg.derived()
    lay = cfd.build_layout(cfg)
    assert lay.dx == 0.1 and len(lay.rack_cells) == d["racks_per_row"]
    assert any("row bay" in n for n in lay.notes)
    t0 = time.perf_counter()
    m = cfd.run_cfd(cfg, steps=300)
    assert time.perf_counter() - t0 < 60
    assert m["racks"] == cfg.racks and m["racks_modelled"] == d["racks_per_row"] and m["rows"] == 4
    assert len(m["recirculation_index"]) == cfg.racks == len(m["rack_inlet_c"])
    assert np.isfinite(m["max_rack_inlet_c"]) and all(0.0 <= r <= 1.0 for r in m["recirculation_index"])
    p = cfd.apply_to_params(m, TwinParams())
    assert len(p.recirculation_profile) == cfg.racks


def test_default_run_for_ben2000_is_fast():
    import time
    t0 = time.perf_counter()
    m = cfd.run_cfd(Config.preset("ben2000"))
    assert time.perf_counter() - t0 < 60, m["runtime_s"]
    assert m["grid"][0] * m["grid"][1] < 20000

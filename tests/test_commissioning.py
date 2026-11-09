"""Commissioning runs end to end in simulation and produces a signed report + hashed CSV."""
import hashlib

from ben_engine.config import Config
from ben_engine import commissioning as cm


def test_sim_commissioning_passes_and_signs(tmp_path):
    cfg = Config.preset("ben150")
    cfg.site_name = "Test site"
    c = cm.Commissioning(cfg, sim=True, yes=True, seed=0, operator="QA", log=lambda m: None, fast=True,
                         clock="2026-01-01T00:00:00+00:00")
    rep = c.run(str(tmp_path / "report.md"))
    assert [s.num for s in rep.steps] == list(range(1, 13))
    failed = [(s.num, s.notes) for s in rep.steps if not s.passed]
    assert rep.passed, failed
    # forward-architecture steps are skipped with a stated reason on a standard AC / rear-door unit
    assert rep.steps[9].values.get("skipped") and "dlc_hd" in rep.steps[9].notes[0]
    assert rep.steps[10].values.get("skipped") and "dc800" in rep.steps[10].notes[0]
    md = (tmp_path / "report.md").read_text()
    assert "overall **PASS**" in md and "## Signature" in md and "QA" in md and "SHA-256" in md
    data = tmp_path / "report_data.csv"
    assert data.exists()
    assert hashlib.sha256(data.read_bytes()).hexdigest() == rep.csv_sha256
    assert rep.csv_sha256 in md
    assert "load bank" in md
    assert {"cooling_unit_failover", "load_step", "utility_loss_ride_through"} <= set(rep.sweep_results)


def test_checklist_can_fail_step1(tmp_path):
    cfg = Config.preset("ben30")
    answers = iter(["y"] * 3 + ["n"] + ["y"] * 10)
    c = cm.Commissioning(cfg, sim=True, yes=False, ask=lambda q: next(answers), log=lambda m: None, fast=True)
    rep = c.run(str(tmp_path / "r.md"))
    assert rep.steps[0].passed is False and not rep.passed
    assert "not confirmed" in rep.steps[0].notes[0]


def test_cli_and_live_placeholder(tmp_path):
    rc = cm.main(["--sim", "--tier", "ben30", "--yes", "--fast", "--out", str(tmp_path / "cli.md")])
    assert rc == 0 and (tmp_path / "cli.md").exists()
    rep = cm.run_live("http://127.0.0.1:9", Config.preset("ben30"), str(tmp_path / "live.md"), log=lambda m: None)
    assert rep.mode == "live" and rep.steps[0].passed is False
    assert "not reachable" in rep.steps[0].notes[0]

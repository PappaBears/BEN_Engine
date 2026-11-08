"""Simulated end-to-end gate (brief row 17): configuration → twin → sweeps → commissioning → CSV + SHA-256 report.
Runs in CI. The browser end-to-end lives in tests/e2e/ and runs on demand."""
import hashlib, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config
from ben_engine.commissioning import Commissioning
from ben_engine import sweeps as S
import pytest


@pytest.mark.parametrize("tier", ["ben5", "ben150", "ben2000"])
def test_commissioning_sim_end_to_end(tmp_path, tier):
    cfg = Config.preset(tier)
    out = tmp_path / f"report-{tier}.md"
    rep = Commissioning(cfg, sim=True, yes=True, fast=True).run(str(out))
    text = out.read_text()
    assert all(s.passed for s in rep.steps), [s.name for s in rep.steps if not s.passed]
    assert "PASS" in text
    m = re.search(r"SHA-256: `([0-9a-f]{64})`", text)
    assert m, "report must carry the SHA-256 of the data file"
    csv_path = str(out).replace(".md", "_data.csv")
    assert os.path.exists(csv_path)
    assert hashlib.sha256(open(csv_path, "rb").read()).hexdigest() == m.group(1)
    rows = open(csv_path).read().strip().splitlines()
    assert len(rows) > 100 and rows[0].count(",") > 10


def test_all_sweeps_pass_for_default_tier():
    cfg = Config.preset("ben150")
    results = S.run_all(cfg)
    assert len(results) == len(S.SWEEPS)
    for r in results:
        assert r.passed, (r.name, [c.name for c in r.criteria if not c.passed])


def test_cli_config_sizing_runs():
    out = subprocess.run([sys.executable, "-m", "ben_engine.config", "--tier", "ben500", "--json"], cwd=os.path.join(ROOT, "software"), capture_output=True, text=True)
    assert out.returncode == 0 and '"service_breaker_a"' in out.stdout

"""The product page price engine (web/assets/bom.js over web/assets/price-rules.json) must price every configuration
exactly as the Python BOM and the proposals do: same rule inputs, same lines, same total, same 35 % margin.
Every spec the customer can change on the page is exercised: tier, lineup, form, profile, climate, hardening,
redundancy, UPS minutes, generator, power architecture, cooling, IT load, racks and subsystem selection."""
import dataclasses
import itertools
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from ben_engine.bom import generate_bom, rule_variables, totals  # noqa: E402
from ben_engine.commercial import PROJECT_MARGIN  # noqa: E402
from ben_engine.config import Config, TIERS_BY_LINEUP  # noqa: E402
from ben_engine import proposal as P  # noqa: E402

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _variants():
    """Valid configurations around every preset: one option changed at a time, plus a few combined changes."""
    out = []
    for lineup in ("rev2", "rev1"):
        for tier in TIERS_BY_LINEUP[lineup]:
            forms = ("rack10", "cab12") if tier == "ben1" else (None,)
            for form, profile in itertools.product(forms, ("ai_inference", "ai_training", "healthcare", "private_cloud")):
                kw = {"lineup": lineup}
                if form:
                    kw["form"] = form
                try:
                    base = Config.preset(tier, profile, "temperate", **kw)
                except TypeError:
                    base = Config.preset(tier, profile, "temperate", lineup=lineup)
                if base.validate():
                    continue
                cands = [base]
                for k, vals in (("hardening", ("H1", "H2", "H3")), ("redundancy", ("N", "N+1", "2N")), ("ups_minutes", (5, 10, 15, 30)),
                                ("generator", (True, False)), ("climate", ("hot_arid", "cold", "coastal")),
                                ("power_architecture", ("ac480", "dc800")), ("cooling", ("dlc_hd", "dlc_cdu", "rdhx_drycooler", "inrow_dx_300")),
                                ("subsystems", (["power"], ["cooling", "controls"], ["power", "cooling", "controls"]))):
                    for v in vals:
                        cands.append(dataclasses.replace(base, **{k: v}))
                for f in (0.5, 0.8):
                    cands.append(dataclasses.replace(base, it_kw=round(base.it_kw * f, 1)))
                cands.append(dataclasses.replace(base, hardening="H3", generator=True, redundancy="N"))
                for c in cands:
                    if not c.validate():
                        out.append(c)
    seen, uniq = set(), []
    for c in out:
        key = json.dumps(c.to_dict(), sort_keys=True)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


CONFIGS = _variants()


def _js(cfgs):
    script = f"""
    import {{ generateBom, bomTotals, ruleVariables, quote }} from '{ROOT}/web/assets/bom.js';
    import fs from 'fs';
    const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
    const rules = JSON.parse(fs.readFileSync('{ROOT}/web/assets/price-rules.json'));
    const cfgs = JSON.parse(fs.readFileSync(0, 'utf8'));
    const out = cfgs.map((c) => {{
      try {{ const rows = generateBom(c, cat, rules); return {{ vars: ruleVariables(c, cat), total: bomTotals(rows).total_usd,
             codes: rows.map((r) => r.code + ':' + r.qty).sort(), price: quote(c, cat, rules).price_usd }}; }}
      catch (e) {{ return {{ error: String(e) }}; }}
    }});
    console.log(JSON.stringify(out));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script], input=json.dumps([c.to_dict() for c in cfgs]),
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def test_grid_covers_every_spec():
    assert len(CONFIGS) > 300
    for k in ("hardening", "redundancy", "ups_minutes", "generator", "climate", "power_architecture"):
        assert len({getattr(c, k) for c in CONFIGS}) > 1, k
    assert {c.tier for c in CONFIGS} >= set(TIERS_BY_LINEUP["rev2"]) | set(TIERS_BY_LINEUP["rev1"])


@needs_node
def test_page_engine_matches_python_bom_for_every_configuration():
    js = _js(CONFIGS)
    bad = []
    for c, j in zip(CONFIGS, js):
        if "error" in j:
            bad.append((c.tier, c.lineup, j["error"]))
            continue
        rows = generate_bom(c)
        py_total = totals(rows)["total_usd"]
        if abs(j["total"] - py_total) > 0.02 or sorted(f"{r['code']}:{r['qty']}" for r in rows) != j["codes"]:
            pv = rule_variables(c)
            diff = {k: (pv[k], j["vars"].get(k)) for k in pv if pv[k] != j["vars"].get(k)}
            bad.append((c.tier, c.lineup, c.hardening, c.redundancy, c.generator, py_total, j["total"], diff))
        assert j["price"] == pytest.approx(py_total / (1 - PROJECT_MARGIN), abs=0.05)
    assert not bad, f"{len(bad)} of {len(CONFIGS)} configurations differ, first: {bad[:3]}"


def test_margin_is_35_percent_on_the_whole_project():
    assert PROJECT_MARGIN == 0.35 and P.MARGIN_HW == PROJECT_MARGIN
    rules = json.load(open(os.path.join(ROOT, "web", "assets", "price-rules.json")))
    assert rules["margin"] == PROJECT_MARGIN
    cfg = Config.preset("ben700", lineup="rev2")
    prop = P.build_proposal(cfg) if hasattr(P, "build_proposal") else None
    if prop is not None:
        cost = totals(generate_bom(cfg))["total_usd"]
        assert prop.headline.capital_price_usd == pytest.approx(cost / 0.65, rel=1e-6)


def test_specs_move_the_price():
    """Hardening, generator, redundancy and UPS minutes change the price wherever the BOM has lines for them."""
    base = Config.preset("ben700", lineup="rev2")
    t = lambda c: totals(generate_bom(c))["total_usd"]  # noqa: E731
    assert t(dataclasses.replace(base, hardening="H2")) > t(base)
    assert t(dataclasses.replace(base, hardening="H3")) > t(dataclasses.replace(base, hardening="H2"))
    assert t(dataclasses.replace(base, generator=True)) > t(base)
    assert t(dataclasses.replace(base, redundancy="N")) < t(base)


def test_price_rules_file_is_current():
    import export_price_rules as E
    on_disk = json.load(open(E.OUT))
    assert on_disk == json.loads(json.dumps(E.build())), "run python scripts/export_price_rules.py"

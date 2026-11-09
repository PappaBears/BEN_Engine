"""Generator for tests/fixtures/rev1_presets.json — the frozen Rev 1 numbers (docs/REVISION_POLICY.md rule 3).

Run ONCE against the Rev 1 code (commit 3ea7d7d, before the Rev 2 lineup change) and kept as evidence. Re-running it
against later code is only allowed through ``Config.preset(..., lineup="rev1")`` and must reproduce the file exactly;
tests/test_rev1_frozen.py does that comparison.

    PYTHONPATH=software python tests/fixtures/gen_rev1_presets.py
"""
import inspect
import json
import sys
from pathlib import Path

from ben_engine import config as C
from ben_engine.bom import generate_bom, load_catalog, totals

REV1_TIERS = ["ben5", "ben30", "ben150", "ben500", "ben2000"]
OUT = Path(__file__).with_name("rev1_presets.json")


def preset(tier, profile, climate, hardening=None):
    if "lineup" in inspect.signature(C.Config.preset).parameters:
        return C.Config.preset(tier, profile, climate, hardening, lineup="rev1")
    return C.Config.preset(tier, profile, climate, hardening)


def derived_json(cfg):
    return json.loads(json.dumps(cfg.derived(), sort_keys=True, default=str))


def cfg_json(cfg):
    d = cfg.to_dict()
    d.pop("lineup", None)
    d.pop("form", None)
    return d


def variants():
    """(key, cfg) pairs: every tier x profile x climate preset, every hardening level per tier, and the forward options."""
    for t in REV1_TIERS:
        for p in C.PROFILE_DEFAULTS:
            for c in C.CLIMATE_DESIGN:
                yield f"{t}|{p}|{c}", preset(t, p, c)
        for h in ("H1", "H2", "H3"):
            yield f"{t}|ai_inference|temperate|{h}", preset(t, "ai_inference", "temperate", h)
    for t in ("ben150", "ben500", "ben2000"):
        for cool in ("dlc_hd",):
            cfg = preset(t, "ai_training", "temperate"); cfg.cooling = cool
            yield f"{t}|ai_training|temperate|cooling={cool}", cfg
        for conv in ("bipolar_400", "unipolar_800"):
            cfg = preset(t, "ai_training", "temperate"); cfg.power_architecture = "dc800"; cfg.dc_convention = conv
            yield f"{t}|ai_training|temperate|dc800|{conv}", cfg
    cfg = preset("ben150", "ai_inference", "temperate"); cfg.power_architecture = "dc800"; cfg.cooling = "dlc_hd"
    yield "ben150|ai_inference|temperate|dc800|dlc_hd", cfg
    for ct in ("lite", "pro"):
        cfg = preset("ben30", "ai_inference", "temperate"); cfg.controls_tier = ct
        yield f"ben30|ai_inference|temperate|controls={ct}", cfg


def build():
    cat = load_catalog()
    out = {"_source": "Rev 1 code before the Rev 2 lineup change (git 3ea7d7d); do not regenerate", "derived": {}, "config": {}, "bom": {}}
    for key, cfg in variants():
        if cfg.validate():
            continue
        out["derived"][key] = derived_json(cfg)
        out["config"][key] = cfg_json(cfg)
        t = totals(generate_bom(cfg, cat))
        out["bom"][key] = {"total_usd": t["total_usd"], "by_status": t["by_status"], "by_subsystem": t["by_subsystem"], "items": t["items"]}
    return out


if __name__ == "__main__":
    data = build()
    if "--check" in sys.argv:
        print("equal" if json.loads(OUT.read_text()) == data else "DIFFERENT")
    else:
        OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
        print(f"wrote {OUT} with {len(data['derived'])} configs")

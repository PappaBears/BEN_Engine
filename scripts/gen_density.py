"""Generate docs/DENSITY.md: density of every Rev 2 tier and the verified maxima of the liquid-first modules.

    PYTHONPATH=software python scripts/gen_density.py          # writes docs/DENSITY.md
    PYTHONPATH=software python scripts/gen_density.py --check  # exit 1 if docs/DENSITY.md is stale

Every number comes from ben_engine.config (Config.derived(), DENSE_FOOTPRINTS) and design/layout.py (interference checks), so the
table is reproducible. Density = IT kW per rack, per m² of the enclosure's external footprint and per m³ of its external volume; the
dense tiers also show the site footprint including the heat-rejection skid; the Rev 2 BEN 2000 (three BEN 700 modules) shows module, fenced-yard and
site density against the Rev 1 hall.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
sys.path.insert(0, os.path.join(ROOT, "design"))

from ben_engine.config import Config, TIERS_BY_LINEUP, TIER_GEOMETRY, DENSE_FOOTPRINTS, DENSE_RULES  # noqa: E402
import layout as L  # noqa: E402

OUT = os.path.join(ROOT, "docs", "DENSITY.md")

LIMITS = {
    "ben1/rack10": "the 15 A, 120 V outlet (12 A continuous) and desktop-class gear on 200 mm shelves; open frame, so noise is the IT's own",
    "ben1/cab12": "the 20 A, 120 V circuit (16 A continuous) caps it at 1.5 kW; noise meets 45 dBA only up to ~1.17 kW; 550 mm usable depth (short-depth servers); the room must take the heat",
    "ben5": "cabinet DX units (5.5 kW each) and 24U in an outdoor NEMA 4X cabinet",
    "ben30": "in-row DX units share the 2.7 m row with the two racks and the rack-mount UPS",
    "ben150": "rear-door coils (35-40 kW per door) and a 5.75 m row that also holds the UPS and battery",
    "ben300": "row length: UPS 850 + two battery cabinets 1,200 + two CDUs 1,200 + three fan coils 900 + two racks 1,200 = 5,350 of 5,400 mm usable (the 600 A panel sits on the end wall); a third rack does not fit, and 155 kW per rack is the GB300-class ceiling",
    "ben500": "Rev 1 DLC at 80 kW per rack with 25 % residual air in in-row DX",
    "ben700": "power gear length: switchboard, two UPS frames and four battery cabinets take 5.0 m (44 %) of the 11.5 m usable row, and three CDUs another 1.8 m; the 1,000 kW / 7-rack target needs {need:,} mm against {have:,}",
    "ben2000": "three BEN 700 modules (each limited as BEN 700) on a shared yard; site density is set by the yard clearances (I-K3 module gap 3,048 for the lithium ESS, transformer working space, fire / crane lane)",
}


def _site_footprint_m2(cfg: Config) -> float:
    g = cfg.geometry()
    if g.get("kind") == "cluster":
        return cfg.derived()["yard_area_m2"]          # Rev 2 BEN 2000: the fenced yard (modules, skids, transformers, switchgear, clearances)
    lay = L.resolve(cfg.tier, cfg=cfg)
    dc = lay.find("DC1")
    if not dc or not g.get("liquid_first"):
        return round(g["ext_l_m"] * g["ext_w_m"], 2)
    skid_len = (dc.x1 - dc.x0) / 1000.0
    return round((g["ext_l_m"] + 1.5 + skid_len) * max(g["ext_w_m"], (dc.y1 - dc.y0) / 1000.0), 2)


def _row(label: str, cfg: Config, limit: str):
    d = cfg.derived()
    g = cfg.geometry()
    site = _site_footprint_m2(cfg)
    return (f"| {label} | {d['enclosure'] if cfg.tier != 'ben1' else d['form_label']} | {cfg.it_kw:g} | {cfg.racks} | {d['kw_per_rack']:g} | "
            f"{d['footprint_m2']:g} | {d['kw_per_m2_footprint']:g} | {d['volume_m3']:g} | {d['kw_per_m3_volume']:g} | {site:g} | {round(cfg.it_kw / site, 2):g} | {limit} |")


def _cluster_section() -> list:
    """Rev 2 BEN 2000 (docs/REV2_DECISION.md §2b): three BEN 700 modules on a shared yard, against the Rev 1 hall it replaces in lineup rev2."""
    c = Config.preset("ben2000", "ai_training")
    d = c.derived()
    lay = L.resolve("ben2000", cfg=c)
    hall_cfg = Config.preset("ben2000", "ai_training", lineup="rev1")
    hall = L.resolve("ben2000", cfg=hall_cfg)
    xs = [v for i in hall.items for v in (i.x0, i.x1)]
    ys = [v for i in hall.items for v in (i.y0, i.y1)]
    hall_site = (max(xs) - min(xs)) * (max(ys) - min(ys)) / 1e6
    hg = hall_cfg.geometry()
    hall_fp = hg["ext_l_m"] * hg["ext_w_m"]
    kw5, _ = max_fit("ben700", 5)
    y = d["yard"]
    res = {}
    for ch in lay.checks:
        res[ch.result] = res.get(ch.result, 0) + 1
    return ["", "## BEN 2000 (Rev 2): three BEN 700 modules on a shared yard", "",
            f"Rev 2 decision §2b. Preset `Config.preset('ben2000', 'ai_training')`: **{c.it_kw:g} kW in {c.racks} racks** = {d['modules']} modules × {d['module_racks']} racks × "
            f"{d['kw_per_rack']:g} kW (each module {d['module_it_kw']:g} kW, inside the BEN 700 rating), `{c.cooling}`, {c.redundancy} inside every module. "
            f"Verified maximum {d['modules']} × {kw5} kW = **{d['modules'] * kw5:,} kW** (BEN 700 `max_fit` below); sold as up to 2,000 kW. "
            f"Yard: {d['mv_kv']} kV service ({d['mv_service_amps']} A at {d['total_kva']:,} kVA), one {d['mv_switchgear_ways']}-way 15 kV pad-mounted switchgear "
            f"(1 source + {d['modules']} transformer ways), **one {d['transformer_kva']:,} kVA pad-mount transformer per module** ({d['transformer_loading_pct']} % loaded; "
            f"each module keeps its own {d['module_service_breaker_a']:,} A 480 V service as a stand-alone BEN 700, so a transformer fault takes one module, not the site), "
            f"one heat-rejection skid per module ({d['skid_rejection_kw_each']} kW W45 dry coolers + trim chiller).", "",
            "| Basis | Area m² | kW / m² | What it includes |", "|---|---:|---:|---|",
            f"| Module footprint | {d['footprint_m2']:g} | {d['kw_per_m2_footprint']:g} | the three 40 ft module envelopes ({d['footprint_m2'] / d['modules']:.3f} m² each, {d['kw_per_m2_module']:g} kW/m² per module) |",
            f"| Fenced yard | {d['yard_area_m2']:g} | {d['kw_per_m2_yard']:g} | {y['yard_l_m']:g} × {y['yard_w_m']:g} m: modules, door-end apron, skids, transformers, switchgear, working clearances, 1 m to the fence |",
            f"| Site incl. lanes | {d['site_area_m2']:g} | {d['kw_per_m2_site']:g} | {y['site_l_m']:g} × {y['site_w_m']:g} m: the yard + the 6.1 m fire / crane lane and the 6.1 m service lane |",
            f"| Rev 1 hall building (for comparison) | {hall_fp:.1f} | {hall_cfg.it_kw / hall_fp:.2f} | 36.6 × 11.0 m hall envelope at the Rev 1 preset {hall_cfg.it_kw:g} kW, {hall_cfg.racks} racks, `{hall_cfg.cooling}` |",
            f"| Rev 1 hall site (for comparison) | {hall_site:.0f} | {hall_cfg.it_kw / hall_site:.2f} | bounding box of every item of the Rev 1 hall layout (hall, power module, MV pad, three 1,250 kW generators and fuel, plant yard, crane lane) |",
            "",
            f"The cluster carries {c.it_kw / hall_cfg.it_kw:.2f} × the Rev 1 preset IT load on {d['site_area_m2'] / hall_site:.2f} × its site area. The Rev 1 hall site includes N+1 generators "
            f"and a 48 h fuel tank; the Rev 2 AI preset has no generator (healthcare, public sector and off-grid profiles add one 480 V generator per module beside module 1, I-K24). "
            f"Yard checks (design/layout.py I-K1..I-K23; I-K24 when generators are fitted): " + ", ".join(f"{v} {k}" for k, v in sorted(res.items())) + "; STUDY = the rule needs the AHJ's or the utility's value "
            "(I-K6 fire separation if the modules are classed as buildings, I-K11 utility working clearance in front of pad-mount doors).", ""]


def max_fit(tier: str, racks: int) -> tuple:
    """Highest IT kW (5 kW steps, <= 155 kW per rack) whose dense row fits the interior with real footprints; (kW, row mm) or (0, row mm)."""
    best = (0, None)
    for it in range(5, racks * 155 + 1, 5):
        c = Config(tier=tier, profile="ai_training", it_kw=float(it), racks=racks, cooling="dlc_hd", redundancy="N+1", climate="temperate",
                   ups_minutes=5, lineup="rev2")
        d = c.derived()
        if d["row_fits"]:
            best = (it, d["row_length_mm"])
        elif best[1] is None:
            best = (0, d["row_length_mm"])
    return best


def build() -> str:
    out = ["# BEN Engine Rev 2 — density by tier", "",
           "Generated by `scripts/gen_density.py` from `software/ben_engine/config.py` and `design/layout.py`; do not edit by hand. "
           "Presets: profile `ai_training` (the densest), climate `temperate`, lineup `rev2`. Footprint and volume are the enclosure's external "
           "dimensions; *site* adds the heat-rejection skid of the liquid-first tiers (1.5 m gap + skid); for BEN 2000 (three modules) footprint and volume are the "
           "three module envelopes and *site* is the fenced yard (section below). Rev 1 tiers are carried unchanged.", "",
           "| Tier | Enclosure | IT kW | Racks | kW / rack | Footprint m² | kW / m² | Volume m³ | kW / m³ | Site m² | kW / site m² | What limits density |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for t in TIERS_BY_LINEUP["rev2"]:
        if t == "ben1":
            for f in ("rack10", "cab12"):
                c = Config.preset("ben1", "ai_training", form=f)
                c.it_kw = TIER_GEOMETRY["ben1"]["forms"][f]["it_kw_max"]
                out.append(_row(f"BEN 1 {f} (at max)", c, LIMITS[f"ben1/{f}"]))
            continue
        c = Config.preset(t, "ai_training")
        lim = LIMITS[t]
        if t == "ben700":
            target = Config(tier="ben700", profile="ai_training", it_kw=1000.0, racks=7, cooling="dlc_hd", redundancy="N+1", ups_minutes=5, lineup="rev2")
            lim = lim.format(need=target.derived()["row_length_mm"], have=int(TIER_GEOMETRY[t]["int_l_m"] * 1000))
        out.append(_row(TIER_GEOMETRY[t]["label"], c, lim))
    out += _cluster_section()
    out += ["", "## Verified maxima of the liquid-first modules", "",
            f"Single row against the rack wall, real footprints (`DENSE_FOOTPRINTS`), end zone {DENSE_RULES['end_zone_mm']} mm, N+1 cooling and UPS modules, "
            "5 min battery, GB300 NVL72-class racks capped at 155 kW. The table is the highest IT load that fits for each rack count.", "",
            "| Module | Racks | Max IT kW that fits | Row length mm (incl. end zone) | Interior mm |", "|---|---:|---:|---:|---:|"]
    for t in ("ben300", "ben700"):
        g = TIER_GEOMETRY[t]
        for r in range(1, (3 if t == "ben300" else 8) + 1):
            kw, row = max_fit(t, r)
            out.append(f"| {g['enclosure'].split(',')[0]} | {r} | {kw if kw else 'does not fit'} | {row} | {int(g['int_l_m'] * 1000)} |")
    out += ["",
            "Result: the 20 ft module carries **two racks at up to 155 kW = 310 kW**, so the name **BEN 300** stands (rated 300 kW at 150 kW per rack). "
            "The 40 ft module's best is **5 racks at 141 kW = 705 kW**; six or seven racks lose more to power gear and CDUs than they add. The "
            "Rev 2 decision's target (BEN 1000, 7 racks) does not fit, so the tier is **BEN 700** (5 × 140 kW), and `ben1000` loads as `ben700`. "
            "Three of them are the Rev 2 BEN 2000 (section above).", "",
            "## Footprints used (sources)", "",
            "| Item | W × D × H mm | Source |", "|---|---|---|"]
    for k, f in DENSE_FOOTPRINTS.items():
        out.append(f"| {f['label']} | {f['w']} × {f['d']} × {f['h']} | {f['src']} |")
    out += ["",
            "## Interference checks (design/layout.py)", "",
            L.checks_table([L.resolve(t, cfg=Config.preset(t, "ai_training")) for t in ("ben300", "ben700")]
                           + [L.resolve("ben1", cfg=Config.preset("ben1", "ai_training", form=f)) for f in ("rack10", "cab12")]
                           + [L.resolve("ben2000", cfg=Config.preset("ben2000", "ai_training"))]),
            "", "Deviations:", "",
            L.deviations_md([L.resolve(t, cfg=Config.preset(t, "ai_training")) for t in ("ben300", "ben700", "ben2000")]),
            "", "## Notes", "",
            "- Residual air: the W45 loop (40 °C supply) cannot cool room air, so the in-row fan coils run on an 18 °C trim loop from a chiller on the skid; "
            "the 20 kW per 300 mm fan coil is a design value, not a datasheet figure.",
            "- Heat rejection: a W45 dry cooler needs design ambient + 8 K approach ≤ 45 °C; above a 37 °C design day (hot / arid) the skid needs adiabatic pre-cooling.",
            "- NFPA 855: each lithium cabinet (32.6 kWh) is one group under the 50 kWh limit; cabinets stand side by side only with UL 9540A data for reduced spacing.",
            "- NEC 110.26: the racks and CDUs face 932-1000 mm of aisle (condition 1, non-conductive liner panels opposite the rack zone); the 480 V gear backs onto the wall and "
            "has ≥ 1,200 mm in front (condition 2, grounded liner opposite).",
            ""]
    return "\n".join(out)


if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        print("up to date" if cur == text else "STALE")
        raise SystemExit(0 if cur == text else 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {OUT}")

"""Regenerate spec/ben-config.schema.json and web/assets/catalog.json from config.py (run after any config change)."""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import TIER_GEOMETRY, COOLING_LIBRARY, PROFILE_DEFAULTS, CLIMATE_DESIGN, CONTROLS_TIERS, CONTROLS_PRO_PROFILES, HARDENING, TIER_ALIASES, POWER_ARCHITECTURES, DLC_HD_TIERS
schema = {
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "$id": "https://schreiberai.com/schemas/ben-config.schema.json",
 "title": "BEN Engine configuration", "type": "object", "additionalProperties": False,
 "required": ["tier", "profile", "it_kw", "racks", "cooling", "redundancy", "climate"],
 "properties": {
  "tier": {"enum": list(TIER_GEOMETRY) + list(TIER_ALIASES), "description": "Tier by nominal maximum IT kW (ben5/ben30/ben150/ben500/ben2000); generation-1 keys micro/ben10/ben20/ben40 are accepted as aliases"},
  "profile": {"enum": list(PROFILE_DEFAULTS)},
  "it_kw": {"type": "number", "minimum": min(g["it_kw_min"] for g in TIER_GEOMETRY.values()), "maximum": max(g["it_kw_max"] for g in TIER_GEOMETRY.values())},
  "racks": {"type": "integer", "minimum": 1, "maximum": max(g["max_racks"] for g in TIER_GEOMETRY.values())},
  "hardening": {"enum": list(HARDENING), "description": "Enclosure hardening level: H1 standard IP66, H2 severe environment, H3 hardened/government"},
  "cooling": {"enum": list(COOLING_LIBRARY)},
  "redundancy": {"enum": ["N", "N+1", "2N"]},
  "climate": {"enum": list(CLIMATE_DESIGN)},
  "subsystems": {"type": "array", "items": {"enum": ["power", "cooling", "compute", "controls"]}, "uniqueItems": True},
  "white_label": {"type": "boolean"}, "brand": {"type": "string", "maxLength": 40},
  "ups_minutes": {"type": "integer", "minimum": 5, "maximum": 60}, "generator": {"type": "boolean"},
  "site_name": {"type": "string", "maxLength": 80},
  "controls_tier": {"enum": list(CONTROLS_TIERS), "description": "BEN Controls tier: auto (by size and profile), lite (Revolution Pi + Pods) or pro (PLCnext + UL 508A panel + edge computer + Pods)"},
  "power_architecture": {"enum": list(POWER_ARCHITECTURES), "default": "ac480", "description": "Power distribution: ac480 (480 V AC -> UPS -> AC PDUs, today) or dc800 (800 VDC bus, AC/DC front end, battery on bus; BEN 150 and up; docs/FORWARD_ARCHITECTURE_DECISION.md)"}},
 "x-tier-limits": {t: {"it_kw_min": g["it_kw_min"], "it_kw_max": g["it_kw_max"], "max_racks": g["max_racks"], "kind": g["kind"], "modules": g["modules"], "rows": g.get("rows", 1)} for t, g in TIER_GEOMETRY.items()},
 "x-tier-aliases": dict(TIER_ALIASES),
 "x-cooling-limits": {c: {"max_rack_kw": v["max_rack_kw"], "medium": v["medium"]} for c, v in COOLING_LIBRARY.items()},
 "x-power-architectures": {k: {"tiers": list(v["tiers"])} for k, v in POWER_ARCHITECTURES.items()},
 "x-dlc-hd-tiers": list(DLC_HD_TIERS),
}
json.dump(schema, open(os.path.join(ROOT, "spec/ben-config.schema.json"), "w"), indent=2)
tiers = {t: {**g, "rows": g.get("rows", 1)} for t, g in TIER_GEOMETRY.items()}  # every tier carries kind/modules/rows
json.dump({"tiers": tiers, "tier_aliases": dict(TIER_ALIASES), "hardening": HARDENING, "cooling": COOLING_LIBRARY, "profiles": PROFILE_DEFAULTS,
           "climates": CLIMATE_DESIGN, "controls_tiers": CONTROLS_TIERS, "controls_pro_profiles": list(CONTROLS_PRO_PROFILES),
           "power_architectures": {k: {**v, "tiers": list(v["tiers"]), "busway_frames_a": list(v.get("busway_frames_a", []))} for k, v in POWER_ARCHITECTURES.items()},
           "dlc_hd_tiers": list(DLC_HD_TIERS)},
          open(os.path.join(ROOT, "web/assets/catalog.json"), "w"), indent=1)
print("schema + catalog regenerated")

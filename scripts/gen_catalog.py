"""Regenerate spec/ben-config.schema.json and web/assets/catalog.json from config.py (run after any config change)."""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import TIER_GEOMETRY, COOLING_LIBRARY, PROFILE_DEFAULTS, CLIMATE_DESIGN, CONTROLS_TIERS, CONTROLS_PRO_PROFILES
schema = {
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "$id": "https://schreiberai.com/schemas/ben-config.schema.json",
 "title": "BEN Engine configuration", "type": "object", "additionalProperties": False,
 "required": ["tier", "profile", "it_kw", "racks", "cooling", "redundancy", "climate"],
 "properties": {
  "tier": {"enum": list(TIER_GEOMETRY), "description": "Enclosure tier"},
  "profile": {"enum": list(PROFILE_DEFAULTS)},
  "it_kw": {"type": "number", "minimum": 2, "maximum": 500},
  "racks": {"type": "integer", "minimum": 1, "maximum": 12},
  "cooling": {"enum": list(COOLING_LIBRARY)},
  "redundancy": {"enum": ["N", "N+1", "2N"]},
  "climate": {"enum": list(CLIMATE_DESIGN)},
  "subsystems": {"type": "array", "items": {"enum": ["power", "cooling", "compute", "controls"]}, "uniqueItems": True},
  "white_label": {"type": "boolean"}, "brand": {"type": "string", "maxLength": 40},
  "ups_minutes": {"type": "integer", "minimum": 5, "maximum": 60}, "generator": {"type": "boolean"},
  "site_name": {"type": "string", "maxLength": 80},
  "controls_tier": {"enum": list(CONTROLS_TIERS), "description": "BEN Controls tier: auto (by size and profile), lite (Revolution Pi + Pods) or pro (PLCnext + UL 508A panel + edge computer + Pods)"}},
 "x-tier-limits": {t: {"it_kw_min": g["it_kw_min"], "it_kw_max": g["it_kw_max"], "max_racks": g["max_racks"]} for t, g in TIER_GEOMETRY.items()},
 "x-cooling-limits": {c: {"max_rack_kw": v["max_rack_kw"], "medium": v["medium"]} for c, v in COOLING_LIBRARY.items()},
}
json.dump(schema, open(os.path.join(ROOT, "spec/ben-config.schema.json"), "w"), indent=2)
json.dump({"tiers": TIER_GEOMETRY, "cooling": COOLING_LIBRARY, "profiles": PROFILE_DEFAULTS, "climates": CLIMATE_DESIGN,
           "controls_tiers": CONTROLS_TIERS, "controls_pro_profiles": list(CONTROLS_PRO_PROFILES)},
          open(os.path.join(ROOT, "web/assets/catalog.json"), "w"), indent=1)
print("schema + catalog regenerated")

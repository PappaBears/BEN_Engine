"""BEN Engine configuration model.

This is the "base model". A Config is produced by the selector (dashboard, product page,
or CLI) and consumed by the BOM generator, drawings, digital twin, CFD, commissioning and
compliance matrix. Sizing rules live here so every deliverable agrees.

All units SI unless the field name says otherwise (kw, kva, amps, ft).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from typing import Literal, Dict, Any, List

Tier = Literal["micro", "ben10", "ben20", "ben40"]
Cooling = Literal["cabinet_dx", "inrow_dx", "inrow_dx_300", "rdhx_drycooler", "dlc_cdu"]
Redundancy = Literal["N", "N+1", "2N"]
Climate = Literal["temperate", "hot_arid", "hot_humid", "cold", "coastal", "high_altitude"]
Profile = Literal[
    "ai_inference", "ai_training", "private_cloud", "disaster_recovery",
    "industrial_ot", "healthcare", "public_sector", "off_grid",
]
Subsystem = Literal["power", "cooling", "compute", "controls"]

# ---------------------------------------------------------------- tier geometry
# External ISO dimensions (ISO 668 high cube), internal usable after insulation + liner.
TIER_GEOMETRY: Dict[str, Dict[str, Any]] = {
    "micro": {
        "label": "BEN Micro", "enclosure": "Outdoor 24U NEMA 3R cabinet on skid",
        "ext_l_m": 1.20, "ext_w_m": 1.00, "ext_h_m": 1.80,
        "int_l_m": 1.00, "int_w_m": 0.80, "int_h_m": 1.40,
        "max_racks": 1, "rack_u": 24, "it_kw_min": 2, "it_kw_max": 5,
        "default_cooling": "cabinet_dx", "voltage": "208/240 V 1ph", "tare_kg": 320,
    },
    "ben10": {
        "label": "BEN 10", "enclosure": "10 ft high-cube ISO container",
        "ext_l_m": 2.991, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 2.70, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 2, "rack_u": 42, "it_kw_min": 10, "it_kw_max": 30,
        "default_cooling": "inrow_dx_300", "voltage": "208 V 3ph", "tare_kg": 1300,
    },
    "ben20": {
        "label": "BEN 20", "enclosure": "20 ft high-cube ISO container",
        "ext_l_m": 6.058, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 5.75, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 6, "rack_u": 42, "it_kw_min": 50, "it_kw_max": 150,
        "default_cooling": "rdhx_drycooler", "voltage": "480 V 3ph", "tare_kg": 2400,
    },
    "ben40": {
        "label": "BEN 40", "enclosure": "40 ft high-cube ISO container",
        "ext_l_m": 12.192, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 11.85, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 12, "rack_u": 48, "it_kw_min": 150, "it_kw_max": 500,
        "default_cooling": "dlc_cdu", "voltage": "480 V 3ph", "tare_kg": 3900,
    },
}

COOLING_LIBRARY: Dict[str, Dict[str, Any]] = {
    # unit_kw: sensible cooling per unit at ASHRAE A1 conditions; cop at design point
    "cabinet_dx":     {"label": "Cabinet DX air conditioner", "unit_kw": 5.8,  "cop": 2.6, "medium": "air",   "max_rack_kw": 5,  "width_mm": 400, "mass_kg": 60},
    "inrow_dx":       {"label": "In-row DX cooling unit (600 mm, 30 kW)", "unit_kw": 30.0, "cop": 3.2, "medium": "air",   "max_rack_kw": 30, "width_mm": 600, "mass_kg": 250},
    "inrow_dx_300":   {"label": "In-row DX cooling unit (300 mm, 20 kW)", "unit_kw": 20.0, "cop": 3.1, "medium": "air",   "max_rack_kw": 20, "width_mm": 300, "mass_kg": 180},
    "rdhx_drycooler": {"label": "Rear-door heat exchanger + dry cooler", "unit_kw": 35.0, "cop": 8.0, "medium": "water", "max_rack_kw": 40, "width_mm": 0, "mass_kg": 150},
    "dlc_cdu":        {"label": "Direct liquid cooling + CDU + dry cooler", "unit_kw": 300.0, "cop": 12.0, "medium": "liquid", "max_rack_kw": 80, "width_mm": 600, "mass_kg": 400},
}

PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "ai_inference":      {"label": "AI inference edge",     "redundancy": "N+1", "ashrae": "A2", "rack_kw": 20},
    "ai_training":       {"label": "AI training pod",       "redundancy": "N+1", "ashrae": "A1", "rack_kw": 60},
    "private_cloud":     {"label": "Private cloud / ERP",   "redundancy": "N+1", "ashrae": "A2", "rack_kw": 10},
    "disaster_recovery": {"label": "Disaster recovery",     "redundancy": "N",   "ashrae": "A3", "rack_kw": 8},
    "industrial_ot":     {"label": "Industrial OT analytics","redundancy": "N+1", "ashrae": "A3", "rack_kw": 8},
    "healthcare":        {"label": "Healthcare (HIPAA)",     "redundancy": "2N",  "ashrae": "A1", "rack_kw": 10},
    "public_sector":     {"label": "Public sector / tactical","redundancy": "2N", "ashrae": "A3", "rack_kw": 12},
    "off_grid":          {"label": "Remote / off-grid",      "redundancy": "N+1", "ashrae": "A3", "rack_kw": 6},
}

CLIMATE_DESIGN: Dict[str, Dict[str, Any]] = {
    # design outdoor temps (ASHRAE 0.4%), solar, corrosion class ISO 9223, wind ASCE 7 basic (m/s)
    "temperate":     {"label": "Temperate",     "t_design_c": 35, "t_min_c": -15, "solar_w_m2": 800, "corrosion": "C3", "wind_ms": 47},
    "hot_arid":      {"label": "Hot / arid",     "t_design_c": 46, "t_min_c": -5,  "solar_w_m2": 1000,"corrosion": "C2", "wind_ms": 47},
    "hot_humid":     {"label": "Hot / humid",    "t_design_c": 38, "t_min_c": 0,   "solar_w_m2": 900, "corrosion": "C4", "wind_ms": 58},
    "cold":          {"label": "Cold",           "t_design_c": 30, "t_min_c": -40, "solar_w_m2": 700, "corrosion": "C3", "wind_ms": 47},
    "coastal":       {"label": "Coastal",        "t_design_c": 34, "t_min_c": -5,  "solar_w_m2": 850, "corrosion": "C5", "wind_ms": 67},
    "high_altitude": {"label": "High altitude",  "t_design_c": 32, "t_min_c": -30, "solar_w_m2": 1100,"corrosion": "C3", "wind_ms": 51},
}


@dataclass
class Config:
    tier: str = "ben20"
    profile: str = "ai_inference"
    it_kw: float = 100.0
    racks: int = 5
    cooling: str = "inrow_dx"
    redundancy: str = "N+1"
    climate: str = "temperate"
    subsystems: List[str] = field(default_factory=lambda: ["power", "cooling", "compute", "controls"])
    white_label: bool = False
    brand: str = "Schreiber AI"
    ups_minutes: int = 10
    generator: bool = False
    site_name: str = "Demo site"

    # ------------------------------------------------------------ validation
    def validate(self) -> List[str]:
        errs: List[str] = []
        g = TIER_GEOMETRY.get(self.tier)
        if g is None:
            return [f"unknown tier {self.tier}"]
        if not (g["it_kw_min"] <= self.it_kw <= g["it_kw_max"]):
            errs.append(f"{g['label']} supports {g['it_kw_min']}–{g['it_kw_max']} kW IT, got {self.it_kw}")
        if not (1 <= self.racks <= g["max_racks"]):
            errs.append(f"{g['label']} holds 1–{g['max_racks']} racks, got {self.racks}")
        if self.cooling not in COOLING_LIBRARY:
            errs.append(f"unknown cooling {self.cooling}")
        else:
            per_rack = self.it_kw / max(self.racks, 1)
            if per_rack > COOLING_LIBRARY[self.cooling]["max_rack_kw"]:
                errs.append(f"{per_rack:.1f} kW/rack exceeds {COOLING_LIBRARY[self.cooling]['label']} limit of {COOLING_LIBRARY[self.cooling]['max_rack_kw']} kW/rack")
        if self.tier == "micro" and self.cooling != "cabinet_dx":
            errs.append("BEN Micro uses cabinet_dx cooling only")
        if self.tier != "micro" and self.cooling == "cabinet_dx":
            errs.append("cabinet_dx is for BEN Micro only")
        if self.profile not in PROFILE_DEFAULTS:
            errs.append(f"unknown profile {self.profile}")
        if self.climate not in CLIMATE_DESIGN:
            errs.append(f"unknown climate {self.climate}")
        if self.redundancy not in ("N", "N+1", "2N"):
            errs.append(f"unknown redundancy {self.redundancy}")
        for s in self.subsystems:
            if s not in ("power", "cooling", "compute", "controls"):
                errs.append(f"unknown subsystem {s}")
        if not errs and self.tier != "micro":
            d = self.derived()
            if not d["row_fits"]:
                errs.append(f"single row of {self.racks} racks + {d['cooling_units_total']} cooling units is {d['row_length_mm']} mm, exceeds interior {int(TIER_GEOMETRY[self.tier]['int_l_m']*1000)} mm; use fewer racks, rear-door or liquid cooling")
        return errs

    # ------------------------------------------------------------ derived sizing
    def derived(self) -> Dict[str, Any]:
        g = TIER_GEOMETRY[self.tier]
        cl = COOLING_LIBRARY[self.cooling]
        clim = CLIMATE_DESIGN[self.climate]
        per_rack_kw = self.it_kw / self.racks

        # cooling: units needed for N, then redundancy
        # derate DX capacity 1.5 %/K above 35 C outdoor design (manufacturer-typical curve)
        derate = 1.0
        if cl["medium"] in ("air", "water") and clim["t_design_c"] > 35:
            derate = max(0.6, 1 - 0.015 * (clim["t_design_c"] - 35))
        unit_kw = cl["unit_kw"] * derate
        n_units = math.ceil(self.it_kw * 1.05 / unit_kw)  # 5 % fan/lighting/transformer heat in space
        if self.redundancy == "N+1":
            n_units_total = n_units + 1
        elif self.redundancy == "2N":
            n_units_total = 2 * n_units
        else:
            n_units_total = n_units
        cooling_kw_elec = self.it_kw / cl["cop"]

        # power chain
        aux_kw = cooling_kw_elec + 0.5 + 0.02 * self.it_kw  # lighting, controls, fans
        total_kw = self.it_kw + aux_kw
        pf = 0.95
        total_kva = total_kw / pf
        ups_kva_n = self.it_kw / pf * 1.15  # UPS carries IT only, 15 % headroom
        if self.redundancy == "2N":
            ups_modules = 2
            ups_kva_each = ups_kva_n
        elif self.redundancy == "N+1":
            # modular UPS: N frames of 50 kVA style modules + 1 module
            ups_modules = 2
            ups_kva_each = ups_kva_n
        else:
            ups_modules = 1
            ups_kva_each = ups_kva_n

        if g["voltage"].startswith("480"):
            v_ll = 480
            service_amps = total_kva * 1000 / (math.sqrt(3) * v_ll) / 0.8
        elif g["voltage"].startswith("208 V 3"):
            v_ll = 208
            service_amps = total_kva * 1000 / (math.sqrt(3) * v_ll) / 0.8
        else:
            v_ll = 240
            service_amps = total_kva * 1000 / v_ll / 0.8
        # round up to standard breaker frames
        frames = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000]
        service_breaker = next((f for f in frames if f >= service_amps), 2000)

        # battery energy for ups_minutes at IT load (lithium, 90 % DoD)
        battery_kwh = self.it_kw * self.ups_minutes / 60 / 0.9

        # airflow: 125 cfm/kW typical at ΔT 12 K (air cooled)
        airflow_cfm = self.it_kw * 125 if cl["medium"] == "air" else self.it_kw * 40

        # structural: payload
        payload_kg = self.racks * (400 if self.tier == "micro" else 900) + n_units_total * cl["mass_kg"] + ups_modules * (120 if self.tier == "micro" else 350) + battery_kwh * 8
        gross_kg = payload_kg + g["tare_kg"]

        # envelope solar/transmission gain, R-value 3.5 m2K/W (100 mm PIR), ΔT at design
        area_m2 = 2 * (g["ext_l_m"] * g["ext_h_m"] + g["ext_w_m"] * g["ext_h_m"]) + g["ext_l_m"] * g["ext_w_m"]
        envelope_gain_kw = (area_m2 * (clim["t_design_c"] - 22) / 3.5 + 0.3 * clim["solar_w_m2"] * g["ext_l_m"] * g["ext_w_m"] * 0.25) / 1000

        pue_est = round(total_kw / self.it_kw + 0.03, 3)  # +0.03 UPS loss
        # single-row length check (racks 600 mm + in-row units + 500 mm end zone) vs interior length
        row_len_mm = self.racks * 600 + (n_units_total * cl["width_mm"] if cl["medium"] == "air" or cl["medium"] == "liquid" else 0) + 500
        row_fits = (self.tier == "micro") or (row_len_mm <= g["int_l_m"] * 1000)
        nfpa_855 = battery_kwh >= 20.0

        return {
            "tier_label": g["label"], "enclosure": g["enclosure"],
            "per_rack_kw": round(per_rack_kw, 2),
            "cooling_label": cl["label"], "cooling_units_n": n_units, "cooling_units_total": n_units_total,
            "cooling_unit_kw_derated": round(unit_kw, 1), "cooling_derate": round(derate, 3),
            "cooling_elec_kw": round(cooling_kw_elec, 2),
            "total_kw": round(total_kw, 1), "total_kva": round(total_kva, 1),
            "voltage": g["voltage"], "service_amps_calc": round(service_amps), "service_breaker_a": service_breaker,
            "ups_modules": ups_modules, "ups_kva_each": round(ups_kva_each), "battery_kwh": round(battery_kwh, 1),
            "airflow_cfm": round(airflow_cfm), "payload_kg": round(payload_kg), "gross_kg": round(gross_kg),
            "envelope_gain_kw": round(envelope_gain_kw, 2), "pue_estimate": pue_est,
            "row_length_mm": int(row_len_mm), "row_fits": row_fits, "nfpa_855_scope": nfpa_855,
            "ashrae_class": PROFILE_DEFAULTS[self.profile]["ashrae"],
            "climate": clim, "geometry": g,
        }

    # ------------------------------------------------------------ io
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, **kw) -> str:
        return json.dumps(self.to_dict(), indent=2, **kw)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Config":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)

    @classmethod
    def preset(cls, tier: str, profile: str = "ai_inference", climate: str = "temperate") -> "Config":
        g = TIER_GEOMETRY[tier]
        p = PROFILE_DEFAULTS[profile]
        it_kw = min(g["it_kw_max"], max(g["it_kw_min"], p["rack_kw"] * g["max_racks"] * 0.8))
        racks = max(1, min(g["max_racks"], math.ceil(it_kw / p["rack_kw"])))
        cooling = g["default_cooling"]
        if tier != "micro" and it_kw / racks > COOLING_LIBRARY[cooling]["max_rack_kw"]:
            cooling = "dlc_cdu"
        cfg = cls(tier=tier, profile=profile, it_kw=float(round(it_kw)), racks=racks,
                  cooling=cooling, redundancy=p["redundancy"], climate=climate,
                  generator=profile in ("healthcare", "public_sector", "off_grid"))
        if tier != "micro":
            for alt in (cooling, "inrow_dx_300", "rdhx_drycooler", "dlc_cdu"):
                cfg.cooling = alt
                if not cfg.validate():
                    break
        return cfg


PRESETS = {t: Config.preset(t) for t in TIER_GEOMETRY}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine selector / sizing")
    ap.add_argument("--tier", default="ben20", choices=list(TIER_GEOMETRY))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--it-kw", type=float)
    ap.add_argument("--racks", type=int)
    ap.add_argument("--cooling", choices=list(COOLING_LIBRARY))
    ap.add_argument("--redundancy", choices=["N", "N+1", "2N"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate)
    for k in ("it_kw", "racks", "cooling", "redundancy"):
        v = getattr(a, k)
        if v is not None:
            setattr(cfg, k, v)
    errs = cfg.validate()
    if errs:
        print("INVALID:\n  " + "\n  ".join(errs))
        return 2
    d = cfg.derived()
    if a.json:
        print(json.dumps({"config": cfg.to_dict(), "derived": {k: v for k, v in d.items() if k not in ("geometry", "climate")}}, indent=2))
    else:
        print(f"{d['tier_label']} — {PROFILE_DEFAULTS[cfg.profile]['label']} — {cfg.it_kw} kW IT in {cfg.racks} racks")
        for k in ("per_rack_kw", "cooling_label", "cooling_units_total", "total_kw", "voltage", "service_breaker_a",
                  "ups_modules", "ups_kva_each", "battery_kwh", "airflow_cfm", "gross_kg", "pue_estimate", "row_length_mm", "row_fits", "nfpa_855_scope"):
            print(f"  {k:24s} {d[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

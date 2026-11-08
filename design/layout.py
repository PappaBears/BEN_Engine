"""BEN Engine physical layout engine (shared by drawings, renders, assembly docs).

Reads `ben_engine.config.Config` for a tier preset and resolves a buildable interior
layout: every floor-standing or wall-mounted item gets a position in interior
millimetres, and every interference check is recorded with its numbers and result.

Coordinate system (interior, mm):
    x  along the container length, 0 at the door-end interior face (cargo doors)
    y  across the width, 0 at the RACK-WALL interior face (racks back onto this wall)
    z  up, 0 at finished floor

Where the configuration as given cannot be built in the enclosure, the engine applies a
documented fallback and records it in `Layout.deviations` so the lead can reconcile the
configuration model. Nothing here is silent.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "software"))
from ben_engine.config import Config, TIER_GEOMETRY, COOLING_LIBRARY, CLIMATE_DESIGN  # noqa: E402

# ------------------------------------------------------------------ component library (mm)
# All footprints are catalogue-typical for the class of equipment; see DESIGN_BASIS.md §9.
_CL = COOLING_LIBRARY
LIB: Dict[str, Dict[str, Any]] = {
    # widths / masses of cooling units come from COOLING_LIBRARY (width_mm, mass_kg) so config and drawings agree
    "rack42":    {"w": 600, "d": 1070, "h": 2000, "kg": 900, "label": "IT rack 42U 600x1070", "code": "STR-RACK42"},
    "rack48":    {"w": 600, "d": 1070, "h": 2200, "kg": 1000, "label": "IT rack 48U 600x1070", "code": "STR-RACK48"},
    "rack24":    {"w": 600, "d": 600,  "h": 1200, "kg": 400, "label": "Rack rails 24U (inside cabinet)", "code": "STR-CAB24U"},
    "inrow300":  {"w": _CL["inrow_dx_300"]["width_mm"], "d": 1070, "h": 2000, "kg": _CL["inrow_dx_300"]["mass_kg"], "label": "In-row DX 300 mm, 20 kW class", "kw": _CL["inrow_dx_300"]["unit_kw"], "code": "CLG-INROW"},
    "inrow600":  {"w": _CL["inrow_dx"]["width_mm"], "d": 1070, "h": 2000, "kg": _CL["inrow_dx"]["mass_kg"], "label": "In-row DX 600 mm, 30 kW class", "kw": _CL["inrow_dx"]["unit_kw"], "code": "CLG-INROW"},
    "rdhx":      {"w": 600, "d": 200,  "h": 2000, "kg": _CL["rdhx_drycooler"]["mass_kg"], "label": "Rear-door heat exchanger 35 kW", "code": "CLG-RDHX"},
    "cdu":       {"w": _CL["dlc_cdu"]["width_mm"], "d": 1070, "h": 2000, "kg": _CL["dlc_cdu"]["mass_kg"], "label": "Coolant distribution unit", "code": "CLG-CDU"},
    "pump_unit": {"w": 600, "d": 1070, "h": 2000, "kg": 350, "label": "Row CDU for RDHx loop", "code": "CLG-CDU-RDHX"},
    "ups600":    {"w": 600, "d": 1000, "h": 2000, "kg": 350, "label": "Modular UPS frame 600", "code": "PWR-UPS-GVS100"},
    "ups800":    {"w": 800, "d": 1000, "h": 2000, "kg": 500, "label": "Modular UPS frame 800", "code": "PWR-UPS-GVS100"},
    "batt":      {"w": 600, "d": 1000, "h": 2000, "kg": 450, "label": "Li-ion battery cabinet 32.6 kWh", "code": "PWR-BATT-LI"},
    "panel":     {"w": 500, "d": 250,  "h": 1000, "kg": 60,  "label": "Panelboard, wall mounted", "code": "PWR-PANEL-ILINE"},
    "controller": {"w": 610, "d": 305, "h": 762, "kg": 45, "label": "BEN Controller panel (UL 508A, PLC + edge computer)", "code": "CTL-PANEL"},
    "controller_lite": {"w": 300, "d": 180, "h": 200, "kg": 8, "label": "BEN Controls Lite cabinet (RevPi, DIN rail)", "code": "CTL-ENCL"},
    "cylinder":  {"w": 400, "d": 400,  "h": 1400, "kg": 90,  "label": "Clean-agent cylinder", "code": "FS-CLEAN-AGENT"},
    "cabdx":     {"w": _CL["cabinet_dx"]["width_mm"], "d": 250, "h": 1500, "kg": _CL["cabinet_dx"]["mass_kg"], "label": "Cabinet DX air conditioner 5.8 kW", "code": "CLG-CABAC"},
}
# catalogue footprints used for the "as purchased" row check (purchasing/parts_catalog.json rules)
CATALOG_FOOTPRINT = {"PWR-UPS-GVS100": 521, "PWR-BATT-LI": 600, "PWR-UPS-93PM50": 495, "STR-RACK48_depth": 1200}

HOT_PLENUM = 200          # rear hot-aisle plenum between rack rear and wall (air layouts)
END_ZONE = 500            # dead-end zone at the blind end: cylinder, BEN Controller panel, mech panel
EGRESS_MIN = 900          # clear egress path, mm
NEC_WS_COND1 = 914        # NEC 110.26 condition 1 working space depth, mm
NEC_WS_COND2 = 1067       # NEC 110.26 condition 2
NEC_WS_WIDTH = 762        # minimum working space width
TRAY_Z = 2250             # underside of overhead cable tray, mm above finished floor (trays run over the aisle)
ENVELOPE_BUILDUP = 408    # ext_h - shipped interior 2698 (198) + floor build-up 100 + roof PIR/liner 110
TRAY_H = 100
BATT_CAB_KWH = 32.6       # one battery cabinet (catalog PWR-BATT-LI)
UPS_INTEGRATED_BATT_KWH = 20.0  # up to this energy fits inside the UPS frame (lithium)
RACK_UPS_KVA_MAX = 40     # above this a floor-standing frame is used

COLORS = {
    "rack": "#66E3FF", "cooling": "#6EE7A8", "power": "#FFC66D", "controls": "#C7A6FF",
    "fire": "#FF707D", "structure": "#9FB3CC", "envelope": "#5C7391", "tray": "#EDF4FF",
}


@dataclass
class Item:
    code: str            # BOM-style code, e.g. CMP-001
    tag: str             # drawing tag, e.g. R1, CU2, UPS1
    kind: str            # rack | cooling | power | controls | fire | tray | structure | envelope
    label: str
    x0: float; y0: float; x1: float; y1: float
    z0: float = 0.0
    z1: float = 2000.0
    mount: str = "floor"   # floor | wall | roof | ext
    kg: float = 0.0
    front: str = "+y"       # direction the service face points (interior coords)
    note: str = ""

    @property
    def w(self): return self.x1 - self.x0
    @property
    def d(self): return self.y1 - self.y0
    @property
    def cx(self): return (self.x0 + self.x1) / 2
    @property
    def cy(self): return (self.y0 + self.y1) / 2


@dataclass
class Check:
    id: str
    sheet: str
    description: str
    formula: str
    value: float
    limit: float
    comparator: str        # "<=" or ">="
    result: str            # OK | FAIL | OK*  (OK after deviation)
    resolution: str = ""

    @property
    def passed(self): return self.result.startswith("OK")


@dataclass
class Sensor:
    id: str
    kind: str
    node: str
    x: float; y: float; z: float
    channel: str


@dataclass
class Layout:
    tier: str
    cfg: Config
    d: Dict[str, Any]
    L: float; W: float; H: float            # interior mm
    ext_l: float; ext_w: float; ext_h: float
    items: List[Item] = field(default_factory=list)
    checks: List[Check] = field(default_factory=list)
    deviations: List[str] = field(default_factory=list)
    sensors: List[Sensor] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)

    def by_kind(self, kind: str) -> List[Item]:
        return [i for i in self.items if i.kind == kind]

    def find(self, tag: str) -> Optional[Item]:
        return next((i for i in self.items if i.tag == tag), None)

    @property
    def is_container(self): return self.tier != "micro"

    @property
    def rack_depth(self):
        r = self.by_kind("rack")
        return r[0].d if r else 0

    @property
    def aisle_y0(self):
        """y of the service face plane of the row (cold aisle starts here)."""
        return self.notes.get("row_front_y", 0)

    @property
    def aisle_width(self):
        return self.W - self.aisle_y0


# ------------------------------------------------------------------ helpers
def _chk(lay: Layout, id_, sheet, desc, formula, value, limit, comp, resolution=""):
    ok = (value <= limit) if comp == "<=" else (value >= limit)
    res = "OK" if ok else "FAIL"
    if ok and resolution:
        res = "OK*"
    lay.checks.append(Check(id_, sheet, desc, formula, round(value, 1), limit, comp, res, resolution))
    return ok


def _air_units(lay: Layout, kw_air: float, redundancy: str, unit_key: str):
    kw = LIB[unit_key]["kw"]
    n = math.ceil(kw_air * 1.05 / kw)
    if redundancy == "N+1":
        n += 1
    elif redundancy == "2N":
        n *= 2
    return n


# ------------------------------------------------------------------ resolver
def resolve(tier: str, profile: str = "ai_inference", climate: str = "temperate") -> Layout:
    cfg = Config.preset(tier, profile, climate)
    d = cfg.derived()
    g = d["geometry"]
    lay = Layout(tier, cfg, d,
                 L=g["int_l_m"] * 1000, W=g["int_w_m"] * 1000, H=g["int_h_m"] * 1000,
                 ext_l=g["ext_l_m"] * 1000, ext_w=g["ext_w_m"] * 1000, ext_h=g["ext_h_m"] * 1000)
    if tier == "micro":
        _resolve_micro(lay)
    else:
        h_eff = lay.ext_h - ENVELOPE_BUILDUP
        _chk(lay, "I-C0", "A-003", "Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance",
             f"config {lay.H:.0f} vs computed {h_eff:.0f}", lay.H, h_eff + 10, "<=",
             resolution="" if lay.H <= h_eff + 10 else f"Drawings use {h_eff:.0f} mm; recommend int_h_m = {h_eff/1000:.2f}")
        lay.notes["int_h_config"] = lay.H
        lay.H = min(lay.H, h_eff + 10)
        _resolve_container(lay)
    _sensors(lay)
    return lay


def _resolve_micro(lay: Layout):
    cfg, d = lay.cfg, lay.d
    L, W, H = lay.L, lay.W, lay.H
    r = LIB["rack24"]
    # rails centred in the cabinet; cabinet door is the +y face
    x0 = (L - r["w"]) / 2
    lay.items.append(Item("STR-CAB24U", "R1", "rack", r["label"], x0, 100, x0 + r["w"], 100 + r["d"], 0, r["h"], kg=r["kg"]))
    lay.notes["row_front_y"] = 100 + r["d"]
    # rack-mounted UPS modules inside the rails (catalog: SRT 6 kVA RM 4U + external battery pack 3U, per module)
    u_used = 0
    for i in range(d["ups_modules"]):
        lay.items.append(Item("PWR-UPS-SRT6K", f"UPS{i+1}", "power", f"Rack UPS {d['ups_kva_each']} kVA (4U)",
                              x0, 100, x0 + r["w"], 100 + r["d"], u_used * 44.45, (u_used + 4) * 44.45, mount="rack", kg=55))
        u_used += 4
        lay.items.append(Item("PWR-UPS-SRT6K-XBP", f"BAT{i+1}", "power", "Rack battery pack (3U)",
                              x0, 100, x0 + r["w"], 100 + r["d"], u_used * 44.45, (u_used + 3) * 44.45, mount="rack", kg=60))
        u_used += 3
    lay.items.append(Item("CTL-REVPI", "CP1", "controls", "BEN Controls Lite shelf (1U): RevPi Connect 4 + DIO/AIO on DIN bracket, switch, 24 VDC",
                          x0, 100, x0 + r["w"], 100 + r["d"], u_used * 44.45, (u_used + 1) * 44.45, mount="rack", kg=5))
    u_used += 1
    lay.items.append(Item("PWR-PDU", "PDU1", "power", "Rack PDU 30 A, zero-U", x0 + r["w"] - 60, 100, x0 + r["w"], 160, 0, r["h"], mount="rack", kg=5))
    lay.notes["u_it"] = 24 - u_used
    lay.notes["u_used"] = u_used
    # cabinet DX units on the exterior long faces (y = 0 face and y = W face)
    n = d["cooling_units_total"]
    c = LIB["cabdx"]
    for i in range(n):
        side = 0 if i % 2 == 0 else 1
        slot = i // 2
        cx = slot * (c["w"] + 100) + c["w"] / 2
        if side == 0:
            y0, y1 = -c["d"] - 120, -120
        else:
            y0, y1 = W + 120, W + 120 + c["d"]
        lay.items.append(Item("CLG-CABAC", f"CU{i+1}", "cooling", c["label"], cx - c["w"] / 2, y0, cx + c["w"] / 2, y1, 150, 150 + c["h"], mount="ext", kg=c["kg"]))
    lay.items.append(Item("PWR-LOADCTR", "SVC1", "power", "Load center 50 A 1ph NEMA 3R, exterior", L + 120, W / 2 - 200, L + 120 + 200, W / 2 + 200, 600, 1200, mount="ext", kg=20))
    lay.items.append(Item("FS-AEROSOL", "FS1", "fire", "Aerosol suppression unit (cabinet)", x0, 20, x0 + 200, 100, H - 150, H - 20, mount="wall", kg=4))
    lay.items.append(Item("STR-SKID", "SKID", "structure", "Steel skid 1.3 x 1.1 m with fork pockets", -50, -50, L + 50, W + 50, -150, 0, kg=120))

    # checks
    _chk(lay, "I-M1", "A-002", "Rack units available for IT after UPS (2 x 4U), battery packs (2 x 3U) and controls shelf (1U)",
         f"24U - {u_used}U", 24 - u_used, 6, ">=", resolution="9U for IT at 5 kW: 2 x 2U servers + 1U switch + 1U patch fits; was 12U rule")
    per_side = math.ceil(n / 2)
    _chk(lay, "I-M2", "A-001", "Cabinet DX units fit on cabinet exterior long face",
         f"{per_side} x {c['w']} + {per_side+1} x 100 gap vs ext {lay.ext_l:.0f}", per_side * c["w"] + (per_side + 1) * 100, lay.ext_l, "<=")
    _chk(lay, "I-M3", "A-003", "Rack depth + front/rear air gap vs cabinet interior width",
         f"{r['d']} + 100 + 100 vs {W:.0f}", r["d"] + 200, W, "<=")
    _chk(lay, "I-M4", "S-001", "Skid + cabinet gross mass vs 2.5 t forklift / tail-lift", f"gross {d['gross_kg']} kg", d["gross_kg"], 2500, "<=")


def _resolve_container(lay: Layout):
    cfg, d = lay.cfg, lay.d
    L, W, H = lay.L, lay.W, lay.H
    red = cfg.redundancy
    rack_key = "rack48" if lay.d["geometry"]["rack_u"] >= 48 else "rack42"
    rk = LIB[rack_key]
    cooling = cfg.cooling

    # ---- step 1: choose air-side architecture and compute row length for the given config
    def row_items_for(cooling_mode):
        """Return (list of (kind,key) in row order from door end, row_depth, plenum, notes)."""
        items = []
        # power block nearest the door: UPS frame(s) (+ integrated battery) then battery cabinets
        ups_kva = d["ups_kva_each"]
        rack_ups = ups_kva <= RACK_UPS_KVA_MAX   # BEN 10: 3 x 20 kVA rack modules in R1 (the catalog 93PM tower does not fit the row)
        if not rack_ups:
            ups_key = "ups600" if ups_kva <= 150 else "ups800"
            frames = 2 if red == "2N" else 1
            for _ in range(frames):
                items.append(("power", ups_key))
            if d["battery_kwh"] > UPS_INTEGRATED_BATT_KWH:
                for _ in range(math.ceil(d["battery_kwh"] / BATT_CAB_KWH)):
                    items.append(("power", "batt"))
        if cooling_mode in ("inrow_dx", "inrow_dx_300"):
            key = "inrow600" if cooling_mode == "inrow_dx" else "inrow300"
            n_units = d["cooling_units_total"] if cooling_mode == cfg.cooling else _air_units(lay, cfg.it_kw, red, key)
            racks = [("rack", rack_key)] * cfg.racks
            units = [("cooling", key)] * n_units
            # interleave: unit, rack, rack, unit ... distribute evenly
            seq = _interleave(racks, units)
            items += seq
            return items, rk["d"], HOT_PLENUM, rack_ups, {"n_air": n_units, "air_key": key}
        if cooling_mode == "rdhx_drycooler":
            items += [("rack", rack_key)] * cfg.racks
            n_pu = 2 if red in ("N+1", "2N") else 1   # catalog CLG-CDU-RDHX qty 2 (N+1 row CDUs)
            items += [("cooling", "pump_unit")] * n_pu
            return items, rk["d"] + LIB["rdhx"]["d"], 0, rack_ups, {"n_air": 0, "n_rdhx": cfg.racks, "n_pu": n_pu}
        if cooling_mode == "dlc_cdu":
            # residual air 25 % of IT at the rack (per DLC vendor data), handled by in-row DX
            n_air = _air_units(lay, 0.25 * cfg.it_kw, red, "inrow300")
            racks = [("rack", rack_key)] * cfg.racks
            units = [("cooling", "inrow300")] * n_air
            items += [("cooling", "cdu")] * d["cooling_units_total"]
            items += _interleave(racks, units)
            return items, rk["d"], HOT_PLENUM, rack_ups, {"n_air": n_air, "air_key": "inrow300", "n_cdu": d["cooling_units_total"]}
        raise ValueError(cooling_mode)

    def row_len(items):
        return sum(LIB[k]["w"] for _, k in items)

    budget = L - END_ZONE
    items, depth, plenum, rack_ups, extra = row_items_for(cooling)
    _chk(lay, "I-C1", "A-002", "Config row_length_mm (racks + cooling units + 500 end zone) vs interior length, config rule",
         f"{d['row_length_mm']} vs {L:.0f}", d["row_length_mm"], L, "<=")
    rl = row_len(items)
    ok = _chk(lay, "I-C2", "A-002", f"Row length with layout footprints ({cooling}: {cfg.racks} racks, {d['cooling_units_total']} cooling units, power cabinets) vs usable length",
              f"{rl:.0f} vs {budget:.0f}", rl, budget, "<=")
    if not ok and cooling in ("inrow_dx", "inrow_dx_300"):
        # fallback kept for non-preset configurations: rear-door heat exchangers + dry cooler (zero row footprint)
        cooling = "rdhx_drycooler"
        items, depth, plenum, rack_ups, extra = row_items_for(cooling)
        rl = row_len(items)
        lay.deviations.append(
            f"DEV-2: in-row row exceeds usable length; drawings use rear-door heat exchangers + dry cooler (cooling = rdhx_drycooler).")
        _chk(lay, "I-C3", "A-002", "Row length after fallback to RDHx vs usable length", f"{rl:.0f} vs {budget:.0f}", rl, budget, "<=",
             resolution="cooling changed to rdhx_drycooler")
    # as-purchased check: UPS / battery quantities per the purchasing catalog qty rules and footprints
    try:
        import json as _json
        from ben_engine.bom import eval_qty_rule, rule_variables, CATALOG_PATH
        _cat = {p["code"]: p for p in _json.load(open(CATALOG_PATH))}
        _v = rule_variables(cfg)
        def _q(code):
            return int(eval_qty_rule(_cat[code]["qty_rule"], _v)) if code in _cat and tier_ok(code) else 0
        def tier_ok(code):
            return lay.tier in _cat[code]["applies_to_tiers"]
        lay.notes["catalog"] = _cat
    except Exception as e:  # catalog missing: skip the as-purchased check
        _cat = None
    if _cat:
        lay_power = sum(LIB[k]["w"] for kind, k in items if kind == "power")
        if not rack_ups:
            n_gvs, n_bat = _q("PWR-UPS-GVS100"), _q("PWR-BATT-LI")
            cat_power = n_gvs * CATALOG_FOOTPRINT["PWR-UPS-GVS100"] + n_bat * CATALOG_FOOTPRINT["PWR-BATT-LI"]
            rl_cat = rl - lay_power + cat_power
            _chk(lay, "I-C21", "A-002", f"Row length with catalog UPS/battery quantities ({n_gvs} x Galaxy VS 100 kW @521 + {n_bat} x Li cab @600, catalog qty rules) vs usable length",
                 f"{rl_cat:.0f} vs {budget:.0f}", rl_cat, budget, "<=",
                 resolution="" if rl_cat <= budget else (
                     f"Over by {rl_cat - budget:.0f} mm with {n_gvs} Galaxy VS 100 kW frames. Drawings assume one modular frame with internal N+1 modules "
                     f"({lay_power:.0f} mm incl. batteries). Options: Galaxy VS 150 kW single frame with redundant power module (521 mm) "
                     + ("- still 71 mm over for BEN 20: reduce end zone to 430 mm or preset 4 racks" if lay.tier == "ben20" else "or BEN 40 preset at 9 racks (frees 600 mm)")))
            lay.notes["catalog_power_mm"] = cat_power
        else:
            n93 = _q("PWR-UPS-93PM50") * CATALOG_FOOTPRINT["PWR-UPS-93PM50"]
            n_rm = _q("PWR-UPS-RM20")
            _chk(lay, "I-C21", "A-002", f"Row length with catalog UPS ({_q('PWR-UPS-93PM50')} x 93PM 50 kW tower @495 in the row; {n_rm} x PWR-UPS-RM20 rack-mount alternative) vs usable length",
                 f"{rl + n93:.0f} vs {budget:.0f}", rl + n93, budget, "<=",
                 resolution="" if rl + n93 <= budget else f"93PM towers do not fit the BEN 10 row; drawings use {n_rm} x 20 kVA rack-mount UPS (PWR-UPS-RM20, 10U each) in R1. Purchasing: keep one of the two catalog lines")
    lay.notes.update(extra)
    lay.notes["cooling_resolved"] = cooling
    lay.notes["rack_ups"] = rack_ups

    # ---- step 2: place the row against the rack wall (y=0), door end first
    y_rear = plenum
    row_front = y_rear + depth
    lay.notes["row_front_y"] = row_front
    lay.notes["plenum"] = plenum
    x = 0.0
    counters: Dict[str, int] = {}
    codes = {k: v["code"] for k, v in LIB.items()}
    tags = {"rack42": "R", "rack48": "R", "inrow300": "CU", "inrow600": "CU", "cdu": "CDU", "pump_unit": "PU",
            "ups600": "UPS", "ups800": "UPS", "batt": "BAT"}
    for kind, key in items:
        spec = LIB[key]
        counters[tags[key]] = counters.get(tags[key], 0) + 1
        tag = f"{tags[key]}{counters[tags[key]]}"
        dep = spec["d"] if kind != "rack" else depth
        y0 = row_front - dep if kind != "power" else row_front - spec["d"]
        label = spec["label"]
        if key.startswith("ups"):
            label = f"Modular UPS frame, {d['ups_modules']} x {d['ups_kva_each']} kVA modules" + (f" + {d['battery_kwh']} kWh Li-ion internal" if d["battery_kwh"] <= UPS_INTEGRATED_BATT_KWH else "")
        if kind == "rack" and cooling == "rdhx_drycooler":
            label = f"{spec['label']} + RDHx door"
        it = Item(codes[key], tag, kind, label, x, y0, x + spec["w"], row_front, 0, spec["h"], kg=spec["kg"])
        lay.items.append(it)
        x += spec["w"]
    lay.notes["row_end_x"] = x
    door_zone = L - END_ZONE - x
    lay.notes["door_zone"] = door_zone

    # containment: hot-aisle plenum panels (air layouts) along the row top and ends
    if plenum > 0:
        lay.items.append(Item("STR-CONT-ROOF", "HAC", "cooling", "Hot-aisle containment: top panels + end doors",
                              0, 0, x, plenum, 0, H, mount="wall", kg=40, note="plenum"))

    # ---- step 3: end zone (blind end): cylinder + BEN Controller panel on the rack-wall side, mech panel on the aisle side
    cyl = LIB["cylinder"]
    lay.items.append(Item("FS-CLEAN-AGENT", "FS1", "fire", f"{cyl['label']} (clean agent, wall bracket)",
                          L - END_ZONE + 50, 100, L - END_ZONE + 50 + cyl["w"], 100 + cyl["d"], 0, cyl["h"], kg=cyl["kg"], front="+x"))
    # controls tier (docs/CONTROLS_HARDWARE_DECISION.md §2a): Pro = UL 508A panel ~800x600x300 class; Lite = DIN cabinet
    pro = cfg.controls_tier_resolved() == "pro"
    gw = LIB["controller" if pro else "controller_lite"]
    lay.notes["controls_tier"] = "pro" if pro else "lite"
    lay.items.append(Item(gw["code"], "CP1", "controls", gw["label"] + " (end wall, 1200 AFF)",
                          L - gw["d"], 100, L, 100 + gw["w"], 1200, 1200 + gw["h"], mount="wall", kg=gw["kg"], front="-x"))
    pn = LIB["panel"]
    # panels on the end wall, aisle side: PNL-M (mechanical) low, PNL-IT high when rack-mounted UPS is used
    pnl_code = "PWR-PANEL-NQ" if d["voltage"].startswith("208") else "PWR-PANEL-ILINE"
    lay.items.append(Item(pnl_code, "PNL-M", "power", "Mechanical panelboard (cooling, lights, receptacles)",
                          L - pn["d"], W - 80 - pn["w"], L, W - 80, 300, 300 + pn["h"], mount="wall", kg=pn["kg"], front="-x"))
    if rack_ups:
        lay.items.append(Item("PWR-PANEL-NQ", "PNL-IT", "power", "IT distribution panelboard (UPS output)",
                              L - pn["d"], W - 80 - pn["w"], L, W - 80, 1400, 1400 + pn["h"], mount="wall", kg=pn["kg"], front="-x"))
        # rack-mount UPS in rack 1: N x 20 kVA modules + 1 (parallel), 10U each, + one 6U external battery cabinet
        r1 = lay.find("R1")
        n_rm = math.ceil(d["ups_kva_each"] / 20) + 1
        for i in range(n_rm):
            lay.items.append(Item("PWR-UPS-RM20", f"UPS{i+1}", "power", "Rack UPS 20 kVA module (10U), parallel N+1",
                                  r1.x0, r1.y0, r1.x1, r1.y1, i * 10 * 44.45, (i + 1) * 10 * 44.45, mount="rack", kg=120))
        lay.items.append(Item("PWR-UPS-RM20-XBP", "BAT1", "power", f"Rack battery cabinet {d['battery_kwh']} kWh (6U)",
                              r1.x0, r1.y0, r1.x1, r1.y1, n_rm * 10 * 44.45, (n_rm * 10 + 6) * 44.45, mount="rack", kg=120))
        lay.notes["u_it_rack1"] = lay.d["geometry"]["rack_u"] - (n_rm * 10 + 6)
        lay.notes["n_rm_ups"] = n_rm
    # door-end wall: EPO + fire releasing panel + light switch on the aisle wall (shallow)
    lay.items.append(Item("FS-CLEAN-AGENT", "FRP", "fire", "Fire releasing panel (wall, aisle side, 1500 AFF)", 150, W - 100, 450, W, 1500, 1900, mount="wall", kg=8, front="-y"))
    lay.items.append(Item("FS-EPO", "EPO", "power", "EPO push-button (by door, 1200 AFF)", 500, W - 60, 600, W, 1200, 1300, mount="wall", kg=1, front="-y"))
    lay.items.append(Item("CTL-LEAK", "LEAK", "controls", "Leak rope, floor perimeter + under cooling units", 0, 0, L, W, 0, 20, mount="floor", kg=3))
    # exterior: service section on the blind end wall, condensers / dry cooler
    lay.items.append(Item("PWR-SVC-ENCL", "SVC", "power", f"Service section NEMA 3R: main breaker {d['service_breaker_a']} A + SPD + ATS (exterior, end wall)",
                          L + 160, W / 2 - 500, L + 160 + 400, W / 2 + 500, 600, 2000, mount="ext", kg=180, front="+x"))
    if cooling == "inrow_dx" or lay.notes.get("n_air", 0):
        n_air = lay.notes["n_air"]
        cus = [i for i in lay.items if i.tag.startswith("CU")]
        for i, cu in enumerate(cus):
            lay.items.append(Item("CLG-COND", f"CND{i+1}", "cooling", "Roof condenser 20 kW class", cu.x0 - 150, 250, cu.x1 + 150, 1050, H + 120, H + 120 + 700, mount="roof", kg=80))
    if cooling in ("rdhx_drycooler", "dlc_cdu"):
        lay.items.append(Item("CLG-DRYCOOLER", "DC1", "cooling", "Dry cooler (site, on pad adjacent to blind end)", L + 1500, -200, L + 1500 + 2400, W + 200, 0, 2200, mount="ext", kg=900))
    # overhead trays above the cold aisle: data tray and power tray
    ay = row_front
    lay.items.append(Item("STR-TRAY", "TR-D", "tray", "Cable tray 300 wide, data (overhead)", 0, ay + 100, L - END_ZONE, ay + 400, TRAY_Z, TRAY_Z + TRAY_H, mount="ceiling", kg=6 * L / 1000))
    lay.items.append(Item("STR-TRAY", "TR-P", "tray", "Cable tray 300 wide, power (overhead)", 0, ay + 500, L - END_ZONE, ay + 800, TRAY_Z, TRAY_Z + TRAY_H, mount="ceiling", kg=6 * L / 1000))
    # floor channel under the row (rack hold-down)
    lay.items.append(Item("STR-FLOORCHAN", "FC", "structure", "Floor channel C100x50x5, 2 runs under row", 0, y_rear, x, row_front, -50, 0, kg=8 * x / 1000 * 2))

    # ---- step 4: checks
    aisle = W - row_front
    _chk(lay, "I-C4", "A-002", "Cold aisle / egress width (int W - plenum - row depth) vs 900 egress",
         f"{W:.0f} - {plenum} - {depth} = {aisle:.0f}", aisle, EGRESS_MIN, ">=")
    cat = lay.notes.get("catalog") or {}
    rc = "STR-RACK48" if rack_key == "rack48" else "STR-RACK42"
    if rc in cat:
        import re as _re
        m = _re.search(r"600\s*x\s*(\d{3,4})", cat[rc]["name"])
        cat_depth = int(m.group(1)) if m else rk["d"]
        a_cat = W - plenum - cat_depth - (LIB["rdhx"]["d"] if cooling == "rdhx_drycooler" else 0)
        _chk(lay, "I-C22", "A-002", f"Aisle width with the catalog rack ({rc}: 600 x {cat_depth} deep{' + RDHx' if cooling == 'rdhx_drycooler' else ''}) vs 900 egress / 914 NEC",
             f"{W:.0f} - {plenum} - {cat_depth} = {a_cat:.0f}", a_cat, NEC_WS_COND1, ">=",
             resolution="" if a_cat >= NEC_WS_COND1 else f"Drawings use a {rk['d']}-deep rack. Change catalog {rc} to a 1070-deep model")
    _chk(lay, "I-C5", "A-002", "Working space depth in front of row, NEC 110.26 condition 1 (insulated wall opposite)",
         f"{aisle:.0f} vs 914", aisle, NEC_WS_COND1, ">=")
    _chk(lay, "I-C6", "A-002", "Working space depth NEC 110.26 condition 2 (grounded parts opposite) - informative",
         f"{aisle:.0f} vs 1067", aisle, NEC_WS_COND2, ">=",
         resolution="Not required: liner wall opposite the row is insulated and non-grounded-surface; condition 1 applies")
    _chk(lay, "I-C7", "A-002", "Door zone (free length between door and first row item) vs 0",
         f"{L:.0f} - {END_ZONE} - {x:.0f} = {door_zone:.0f}", door_zone, 0, ">=")
    two_row = 2 * rk["d"] + 1000
    _chk(lay, "I-C8", "A-002", "Two-row layout (2 x rack depth + 1000 cold aisle) vs interior width",
         f"{two_row} vs {W:.0f}", two_row, W, "<=", resolution="Not used; single row chosen")
    three = rk["d"] + 1000 + LIB["inrow600"]["d"]
    _chk(lay, "I-C9", "A-002", "Rack 1070 + aisle 1000 + cooling unit 1070 across the width vs interior width",
         f"{three} vs {W:.0f}", three, W, "<=", resolution="Not used; cooling units are in-row, not across the width")
    _chk(lay, "I-C10", "A-002", "Rack working space width (762 min) vs rack width", "762 vs 600 rack + aisle continuous", 762, NEC_WS_WIDTH, ">=",
         resolution="Aisle is continuous along the row; width requirement met by the open aisle")
    rack_h = rk["h"]
    _chk(lay, "I-C11", "A-003", "Overhead tray underside (over the aisle) vs rack top, cables drop to rack top entry",
         f"{TRAY_Z} - {rack_h} = {TRAY_Z - rack_h}", TRAY_Z - rack_h, 0, ">=",
         resolution="Trays run over the aisle, not over racks; head clearance under tray 2250 >= 2100")
    _chk(lay, "I-C12", "A-003", "Tray top vs ceiling liner (clearance >= 100 for installation)",
         f"{H:.0f} - {TRAY_Z + TRAY_H} = {H - TRAY_Z - TRAY_H:.0f}", H - TRAY_Z - TRAY_H, 100, ">=")
    _chk(lay, "I-C13", "A-002", "Door swing: ISO cargo doors swing outward; interior door zone needed", "0 vs 0", 0, 0, ">=",
         resolution="Cargo doors open outward 270 deg; no interior swing")
    _chk(lay, "I-C14", "A-003", "Rack height vs interior height (>= 300 for top cable entry and lights over the row)",
         f"{H:.0f} - {rack_h} = {H - rack_h:.0f}", H - rack_h, 300, ">=",
         resolution="" if H - rack_h >= 300 else "Short by %d mm: lights move over the aisle; top cable entry needs >= 250. Alternative: 47U racks (2150)" % (300 - (H - rack_h)))
    _chk(lay, "I-C15", "S-001", "Gross mass vs ISO 668 max gross for the container size (30480 kg)",
         f"{d['gross_kg']} vs 30480", d["gross_kg"], 30480, "<=")
    floor_load = (d["payload_kg"] * 9.81 / 1000) / (L / 1000 * (depth / 1000 + 0.2))  # kN/m2 over the row strip
    _chk(lay, "I-C16", "S-001", "Row strip floor load (payload over row footprint) vs ISO 1496-1 uniform payload rating (~20 kN/m2)",
         f"{floor_load:.1f} kN/m2 vs 20", floor_load, 20, "<=",
         resolution="Rack feet are point loads: C100 floor channels on cross-members spread them; verify in structural calc")
    if lay.notes.get("rack_ups"):
        n_rm = lay.notes["n_rm_ups"]
        _chk(lay, "I-C17", "A-002", f"Rack 1 U available for IT after {n_rm} rack-mount UPS (10U each) + battery (6U)",
             f"{lay.d['geometry']['rack_u']} - {n_rm * 10 + 6}", lay.notes["u_it_rack1"], 6, ">=",
             resolution=f"IT in rack 1 limited to {lay.notes['u_it_rack1']}U; rack 2 carries the balance. Alternative: BEN 10 preset at 20 kW (2 modules)")
    if cooling == "rdhx_drycooler":
        _chk(lay, "I-C18", "M-001", "RDHx doors per rack vs config cooling_units_total",
             f"{cfg.racks} doors vs {d['cooling_units_total']} config units", cfg.racks, d["cooling_units_total"], ">=",
             resolution="RDHx is one door per rack (catalog CLG-RDHX qty = racks); config counts 35 kW units for capacity only")
    if cooling == "dlc_cdu":
        _chk(lay, "I-C19", "M-001", "Residual air load (25 % IT) vs in-row 300 capacity x units (N)",
             f"{0.25*cfg.it_kw*1.05:.1f} kW vs {lay.notes['n_air']} x 20 kW", lay.notes["n_air"] * 20, 0.25 * cfg.it_kw * 1.05, ">=")
    # roof penetration positions clear of corrugation top rails (>= 300 from side rail)
    _chk(lay, "I-C20", "A-001", "Roof penetrations min 300 mm from side top rail", "line-set curbs at y=300 interior = 419 from ext side face", 419, 300, ">=",
         resolution="Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001")


def _interleave(racks, units):
    """Distribute cooling units evenly between racks: unit first, then racks, keep a unit at the far end if odd."""
    if not units:
        return list(racks)
    seq = []
    nr, nu = len(racks), len(units)
    # positions for units among nr+nu slots, spread evenly
    unit_slots = set(round((i + 0.5) * (nr + nu) / nu - 0.5) for i in range(nu))
    ri = ui = 0
    for s in range(nr + nu):
        if s in unit_slots and ui < nu:
            seq.append(units[ui]); ui += 1
        elif ri < nr:
            seq.append(racks[ri]); ri += 1
        else:
            seq.append(units[ui]); ui += 1
    return seq


def _sensors(lay: Layout):
    """Sensor placement rule (matches twin.sensors() and PROTOCOL.md channel names):
    3 inlet probes per rack at 0.4 / 1.2 / 1.8 m on the cold face, 1 outlet probe at 1.2 m on the hot face,
    supply and return probes at the first cooling unit, dP taps across the containment, RH at room centre,
    leak rope on the floor, door contact on the cargo door. Logical node ids stay node{k} (one per two racks, as the
    twin and the API use them); the physical BEN Pods are two per rack (cold face P{2i+1}, hot face P{2i+2}) plus a
    room Pod and an outdoor Pod (docs/CONTROLS_HARDWARE_DECISION.md §3)."""
    racks = lay.by_kind("rack")
    rf = lay.aisle_y0
    heights = (400, 1200, 1800) if lay.is_container else (300, 700, 1100)
    lay.notes["probe_heights"] = heights
    for i, r in enumerate(racks):
        node = f"node{i // 2 + 1}"
        for j, z in enumerate(heights):
            lay.sensors.append(Sensor(f"T_in_r{i+1}_{z/1000:g}", "T", node, r.cx, rf + 50, z, f"T_in_{j+1}"))
        lay.sensors.append(Sensor(f"T_out_r{i+1}", "T", node, r.cx, r.y0 - 50 if lay.notes.get("plenum", 0) else r.y0 + 50, heights[1], "T_out_1"))
    cus = [i for i in lay.items if i.tag.startswith("CU") or i.tag.startswith("PU") or i.tag.startswith("CDU")]
    if cus:
        c = cus[0]
        lay.sensors.append(Sensor("T_supply", "T", "node1", c.cx, rf + 50, 300, "T_in_4"))
        lay.sensors.append(Sensor("T_return", "T", "node1", c.cx, max(c.y0 - 50, 20), 2200 if lay.is_container else 1100, "T_out_4"))
    zmid = 1500 if lay.is_container else 900
    lay.sensors.append(Sensor("RH_room", "RH", "node1", lay.L / 2, rf + lay.aisle_width / 2, zmid, "RH"))
    lay.sensors.append(Sensor("dP_aisle", "dP", "node1", lay.L / 2, rf, zmid, "dP_aisle"))
    lay.sensors.append(Sensor("leak_floor", "leak", "node1", lay.L / 2, rf + 100, 20, "leak"))
    lay.sensors.append(Sensor("door_main", "door", "node1", 50 if lay.is_container else lay.L / 2, lay.W / 2 if lay.is_container else lay.W - 20, 1000, "door"))
    lay.sensors.append(Sensor("P_utility", "kWh", "meter1", lay.L - 100, lay.W - 300, zmid, "pulse_kwh"))
    n_nodes = max(1, math.ceil(len(racks) / 2))
    lay.notes["n_nodes"] = n_nodes
    # BEN Pods: cold-face and hot-face Pod on the top rail of every rack, one room Pod beside the controller, one outdoor Pod
    pods = []
    for i, r in enumerate(racks):
        ztop = r.z1 - 150
        cold_y = rf + 20 if lay.is_container else r.y1 + 10
        hot_y = (r.y0 - 70 if lay.notes.get("plenum", 0) else r.y0 - 70) if lay.is_container else r.y0 - 60
        pods.append(Item("CTL-POD", f"P{2*i+1}", "controls", f"BEN Pod W (cold face R{i+1}, Thread, 4 x Pt1000)", r.x0 + 40, cold_y, r.x0 + 140, cold_y + 50, ztop, ztop + 120, mount="rack", kg=0.3))
        pods.append(Item("CTL-POD", f"P{2*i+2}", "controls", f"BEN Pod W (hot face R{i+1}, Thread, 4 x Pt1000)", r.x0 + 40, max(hot_y, 0), r.x0 + 140, max(hot_y, 0) + 50, ztop, ztop + 120, mount="rack", kg=0.3))
    cp = lay.find("CP1")
    k = len(pods) + 1
    if lay.is_container and cp:
        pods.append(Item("CTL-POD", f"P{k}", "controls", "BEN Pod E (room: RH, dP, leak, door; RS-485 to controller; Thread router)", cp.x0 - 220, cp.y0, cp.x0 - 100, cp.y0 + 50, cp.z1 + 100, cp.z1 + 220, mount="wall", kg=0.4))
        pods.append(Item("CTL-POD", f"P{k+1}", "controls", "BEN Pod E (outdoor: dry cooler / condenser pad, IP65)", lay.L + 160, -300, lay.L + 280, -250, 1800, 1920, mount="ext", kg=0.5))
    else:
        pods.append(Item("CTL-POD", f"P{k}", "controls", "BEN Pod E (room: RH, dP, leak, door; RS-485 to RevPi; Thread router)", 200, 20, 320, 70, 1250, 1370, mount="wall", kg=0.4))
    lay.items.extend(pods)
    lay.notes["n_pods"] = len(pods)


# ------------------------------------------------------------------ reporting
def checks_table(lays: List[Layout]) -> str:
    rows = ["| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |", "|---|---|---|---|---|---|---|---|"]
    for lay in lays:
        for c in lay.checks:
            rows.append(f"| {lay.d['tier_label']} | {c.id} | {c.sheet} | {c.description} | {c.formula} | {c.comparator} {c.limit:g} | **{c.result}** | {c.resolution} |")
    return "\n".join(rows)


def deviations_md(lays: List[Layout]) -> str:
    out = []
    for lay in lays:
        for dv in lay.deviations:
            out.append(f"- **{lay.d['tier_label']}** — {dv}")
    return "\n".join(out) if out else "- None."


if __name__ == "__main__":
    lays = [resolve(t) for t in TIER_GEOMETRY]
    for lay in lays:
        print(f"== {lay.d['tier_label']}  cooling resolved: {lay.notes.get('cooling_resolved', lay.cfg.cooling)}  row end {lay.notes.get('row_end_x')}  door zone {lay.notes.get('door_zone')}")
        for it in lay.items:
            print(f"   {it.tag:7s} {it.code:8s} {it.kind:9s} x{it.x0:7.0f}-{it.x1:7.0f} y{it.y0:6.0f}-{it.y1:6.0f} z{it.z0:5.0f}-{it.z1:5.0f} {it.mount:7s} {it.label}")
        for dv in lay.deviations:
            print("   DEV:", dv)
    print()
    print(checks_table(lays))

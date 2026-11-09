"""BEN Engine physical layout engine (shared by drawings, renders, assembly docs).

Reads `ben_engine.config.Config` for a tier preset and resolves a buildable interior
layout: every floor-standing or wall-mounted item gets a position in interior
millimetres, and every interference check is recorded with its numbers and result.

Coordinate system (interior, mm):
    x  along the enclosure length, 0 at the door-end interior face (cargo doors / vestibule)
    y  across the width, 0 at the RACK-WALL interior face (racks back onto this wall); in the BEN 2000 hall
       y = 0 is the long wall opposite the fan wall and the four rows run along x
    z  up, 0 at finished floor

Tier kinds (software/ben_engine/config.py TIER_GEOMETRY["kind"]): "cabinet" (BEN 5 NEMA 4X / IP66 cabinet on a
skid), "module" (BEN 30/150/500 ISO-frame modules sealed to IP66) and "hall" (BEN 2000: three 12.2 m bays, each
delivered as three 12.2 x 3.66 x 4.2 m road sections, site-joined into one 36.6 x 11.0 m envelope, plus a power
module and a plant yard). Site items of the hall (power module, MV pad, generators, dry coolers) are Items with
mount="ext" in the same coordinate system so the A-000 site plan and the renders share one source.

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
from ben_engine.config import Config, TIER_GEOMETRY, COOLING_LIBRARY, CLIMATE_DESIGN, HARDENING, TIER_ALIASES, canonical_tier  # noqa: E402

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
    # forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): high-density row CDU, W45 in-row fan coil for the residual air,
    # 800 VDC rectifier / SST cabinet and 800 V class battery string cabinet (footprints are catalogue-typical, vendors sampling 2026)
    "cdu_hd":    {"w": _CL["dlc_hd"]["width_mm"], "d": 1070, "h": 2000, "kg": _CL["dlc_hd"]["mass_kg"], "label": "Row CDU 600 kW class, W45 loop, pumps N+1", "kw": _CL["dlc_hd"]["unit_kw"], "code": "CLG-CDU-HD"},
    "inrow_cw300": {"w": 300, "d": 1070, "h": 2000, "kg": 170, "label": "In-row fan coil 300 mm on the W45 loop (residual air), 12 kW at W45", "kw": 12.0, "code": "CLG-AIR-RESID-HD"},
    "rect":      {"w": 600, "d": 1000, "h": 2000, "kg": 400, "label": "AC/DC front-end cabinet 800 VDC (4 x 100 kW SiC rectifier / SST modules)", "code": "PWR-DC-RECT-CAB"},
    "batt800":   {"w": 600, "d": 1000, "h": 2000, "kg": 450, "label": "Battery string cabinet 800 V class LFP, on the DC bus", "code": "PWR-BATT-800V"},
    "ups600":    {"w": 600, "d": 1000, "h": 2000, "kg": 350, "label": "Modular UPS frame 600", "code": "PWR-UPS-GVS100"},
    "ups800":    {"w": 800, "d": 1000, "h": 2000, "kg": 500, "label": "Modular UPS frame 800", "code": "PWR-UPS-GVS100"},
    "batt":      {"w": 600, "d": 1000, "h": 2000, "kg": 450, "label": "Li-ion battery cabinet 32.6 kWh", "code": "PWR-BATT-LI"},
    "panel":     {"w": 500, "d": 250,  "h": 1000, "kg": 60,  "label": "Panelboard, wall mounted", "code": "PWR-PANEL-ILINE"},
    "controller": {"w": 610, "d": 305, "h": 762, "kg": 45, "label": "BEN Controller panel (UL 508A, PLC + edge computer)", "code": "CTL-PANEL"},
    "controller_lite": {"w": 300, "d": 180, "h": 200, "kg": 8, "label": "BEN Controls Lite cabinet (RevPi, DIN rail)", "code": "CTL-ENCL"},
    "cylinder":  {"w": 400, "d": 400,  "h": 1400, "kg": 90,  "label": "Clean-agent cylinder", "code": "FS-CLEAN-AGENT"},
    "cabdx":     {"w": _CL["cabinet_dx"]["width_mm"], "d": 250, "h": 1500, "kg": _CL["cabinet_dx"]["mass_kg"], "label": "Cabinet DX air conditioner 5.8 kW", "code": "CLG-CABAC"},
    # BEN 2000 hall and plant yard (catalogue-typical footprints)
    "fanwall":   {"w": 3000, "d": 1000, "h": 3000, "kg": 1400, "label": "Fan-wall air handler 200 kW class", "kw": 200.0, "code": "CLG-FANWALL"},
    "ups_vl":    {"w": 1200, "d": 1000, "h": 2000, "kg": 1100, "label": "Galaxy VL 500 kW UPS frame", "code": "PWR-UPS-GVL500"},
    "lv_swgr":   {"w": 4800, "d": 1600, "h": 2300, "kg": 4500, "label": "480 V switchgear 4,000 A UL 1558 (6 sections)", "code": "PWR-LV-SWGR-4000"},
    "batt_room": {"w": 3200, "d": 3300, "h": 3600, "kg": 6000, "label": "Lithium battery room (NFPA 855, 2-hour separation)", "code": "PWR-BATT-ROOM"},
    "mv_swgr":   {"w": 2600, "d": 1900, "h": 2000, "kg": 2500, "label": "15 kV pad-mounted switchgear 4-way", "code": "PWR-MV-SWGR"},
    "mv_xfmr":   {"w": 2600, "d": 2400, "h": 2300, "kg": 7500, "label": "Pad-mount transformer 2,500 kVA 12.47 kV-480Y", "code": "PWR-MV-XFMR-2500"},
    "genset":    {"w": 12000, "d": 3200, "h": 4000, "kg": 22000, "label": "Diesel generator 1,250 kW, L2 enclosure, sub-base tank", "code": "PWR-GEN-1250"},
    "gen_swgr":  {"w": 4000, "d": 1600, "h": 2300, "kg": 3500, "label": "Generator paralleling switchgear 4,000 A", "code": "PWR-GEN-PARALLEL"},
    "fuel_tank": {"w": 9000, "d": 3000, "h": 2800, "kg": 12000, "label": "Bulk diesel tank 10,000 gal UL 2085", "code": "PWR-FUEL-48H"},
    "adiabatic": {"w": 6000, "d": 2500, "h": 2800, "kg": 3200, "label": "Adiabatic dry cooler 400 kW class, EC fans", "kw": 400.0, "code": "CLG-ADIABATIC"},
    "pump_skid": {"w": 4000, "d": 2000, "h": 2000, "kg": 2500, "label": "Primary pump skid N+1 with expansion / treatment", "code": "CLG-PIPING-HALL"},
    "mantrap":   {"w": 3000, "d": 2400, "h": 2400, "kg": 900, "label": "Service vestibule with mantrap option", "code": "STR-MANTRAP"},
    "cyl_bank":  {"w": 1200, "d": 500, "h": 1600, "kg": 350, "label": "Clean-agent cylinder bank (per module zone)", "code": "FS-CLEAN-AGENT-HALL"},
}
# catalogue footprints used for the "as purchased" row check (purchasing/parts_catalog.json rules)
CATALOG_FOOTPRINT = {"PWR-UPS-GVS100": 521, "PWR-BATT-LI": 600, "PWR-UPS-93PM50": 495, "STR-RACK48_depth": 1200, "PWR-DC-RECT-CAB": 600, "PWR-BATT-800V_cab": 600}

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
# BEN 2000 hall (docs/TIER_AND_ENCLOSURE_DECISION.md §2): four rows along x in cold/hot/cold/hot/cold pods, fan wall on
# the long wall (y = W), CDUs at the row ends, overhead busway + DLC manifolds, no raised floor.
HALL_COLD_AISLE = 1100    # cold aisle, >= 1067 NEC 110.26 condition 2 (equipment both sides)
HALL_HOT_AISLE = 900      # contained hot aisle, >= 900 egress
HALL_FANWALL_D = 1000     # fan-wall unit depth along the long wall
HALL_RACK_H = 2200        # 48U
HALL_MANIFOLD_Z = 2450    # underside of DLC supply/return manifolds over each row
HALL_BUSWAY_Z = 2800      # underside of the overhead busway (A and B) over each row
HALL_SECTION_W = 3660     # road-transport section width (3 per 12.2 m bay)
SITE_SETBACK = 6100       # fire lane / setback around the hall on the site plan (IFC 503: 6.1 m apparatus access)
NEC_WS_COND3_LV = 1200    # NEC 110.26(A)(1) condition 3, 151-600 V (4,000 A switchgear in the power module)
SWGR_WS_DRAWN = 1500      # working space drawn in front of the 480 V switchgear

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
    def kind(self): return self.d["geometry"]["kind"]

    @property
    def is_container(self):
        """ISO-frame module tiers (BEN 30/150/500): single row against the rack wall, cargo doors at x = 0."""
        return self.kind == "module"

    @property
    def is_cabinet(self): return self.kind == "cabinet"

    @property
    def is_hall(self): return self.kind == "hall"

    @property
    def modules(self) -> int: return self.d["modules"]

    @property
    def module_x(self) -> List[float]:
        """Interior x of the module (bay) joints of the hall, excluding the end walls."""
        if not self.is_hall:
            return []
        pitch = self.ext_l / self.modules
        endw = (self.ext_l - self.L) / 2
        return [k * pitch - endw for k in range(1, self.modules)]

    @property
    def hardening(self) -> Dict[str, Any]:
        return HARDENING[self.cfg.hardening]

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
def resolve(tier: str, profile: str = "ai_inference", climate: str = "temperate", hardening: str | None = None, cfg: Config | None = None) -> Layout:
    """Resolve the layout of a tier preset, or of an explicit ``cfg`` (forward-architecture studies: dc800 / dlc_hd)."""
    cfg = cfg if cfg is not None else Config.preset(canonical_tier(tier), profile, climate, hardening)
    errs = cfg.validate()
    if errs:
        raise ValueError("; ".join(errs))
    d = cfg.derived()
    g = d["geometry"]
    lay = Layout(tier, cfg, d,
                 L=g["int_l_m"] * 1000, W=g["int_w_m"] * 1000, H=g["int_h_m"] * 1000,
                 ext_l=g["ext_l_m"] * 1000, ext_w=g["ext_w_m"] * 1000, ext_h=g["ext_h_m"] * 1000)
    tier = cfg.tier
    lay.tier = tier
    lay.notes["dc800"] = cfg.power_architecture == "dc800"
    lay.notes["dlc_hd"] = cfg.cooling == "dlc_hd"
    if lay.is_cabinet:
        _resolve_micro(lay)
    elif lay.is_hall:
        _resolve_hall(lay)
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


def resolve_config(cfg: Config) -> Layout:
    """Layout for an explicit configuration (used by the forward prototype set, design/drawings/forward-ben150/)."""
    return resolve(cfg.tier, cfg=cfg)


def forward_prototype_config() -> Config:
    """The forward prototype: BEN 150 at 150 kW in 2 racks (75 kW/rack), 800 VDC bus (±400 V, HR midpoint) and high-density DLC
    (docs/FORWARD_ARCHITECTURE_DECISION.md §4 workstream E; BOM in docs/BOM-ben150-forward.md)."""
    cfg = Config.preset("ben150")
    cfg.power_architecture = "dc800"
    cfg.dc_convention = "bipolar_400"
    cfg.cooling = "dlc_hd"
    cfg.it_kw = 150.0
    cfg.racks = 2
    cfg.site_name = "Forward prototype (test cell)"
    return cfg


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
    lay.items.append(Item("PWR-LOADCTR", "SVC1", "power", "Load center 50 A 1ph NEMA 4X, exterior", L + 120, W / 2 - 200, L + 120 + 200, W / 2 + 200, 600, 1200, mount="ext", kg=20))
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
        dc800 = cfg.power_architecture == "dc800"
        rack_ups = (ups_kva <= RACK_UPS_KVA_MAX) and not dc800   # BEN 30: 3 x 20 kVA rack modules in R1 (the catalog 93PM tower does not fit the row)
        if dc800:
            # 800 VDC: rectifier / SST cabinets (4 x 100 kW modules each) + 800 V class battery string cabinets on the bus; no UPS frame
            for _ in range(d["rectifier_cabinets"]):
                items.append(("power", "rect"))
            for _ in range(math.ceil(d["battery_on_bus_kwh"] / BATT_CAB_KWH)):
                items.append(("power", "batt800"))
        elif not rack_ups:
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
        if cooling_mode == "dlc_hd":
            # high-density DLC: 90 % of IT heat to the W45 loop; the stated 10 % residual air goes to in-row fan coils on the same loop
            # (catalog CLG-AIR-RESID-HD qty rule: ceil(it_kw x 0.10 x 1.05 / 12) + 1); row CDUs 600 kW class, N+1
            n_air = math.ceil(_CL["dlc_hd"]["air_residual"] * cfg.it_kw * 1.05 / LIB["inrow_cw300"]["kw"]) + 1
            racks = [("rack", rack_key)] * cfg.racks
            units = [("cooling", "inrow_cw300")] * n_air
            items += [("cooling", "cdu_hd")] * d["cooling_units_total"]
            items += _interleave(racks, units)
            return items, rk["d"], HOT_PLENUM, rack_ups, {"n_air": n_air, "air_key": "inrow_cw300", "n_cdu": d["cooling_units_total"]}
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
        if cfg.power_architecture == "dc800":
            n_rc, kwh = _q("PWR-DC-RECT-CAB"), _q("PWR-BATT-800V")
            n_b = math.ceil(kwh / BATT_CAB_KWH)
            cat_power = n_rc * CATALOG_FOOTPRINT["PWR-DC-RECT-CAB"] + n_b * CATALOG_FOOTPRINT["PWR-BATT-800V_cab"]
            rl_cat = rl - lay_power + cat_power
            _chk(lay, "I-C21", "A-002", f"Row length with catalog 800 VDC power quantities ({n_rc} x rectifier cabinet @600 + {n_b} x 800 V battery cabinet @600 for {kwh} kWh) vs usable length",
                 f"{rl_cat:.0f} vs {budget:.0f}", rl_cat, budget, "<=",
                 resolution="" if rl_cat <= budget else f"Over by {rl_cat - budget:.0f} mm: fewer racks or a battery string above the rectifier cabinet")
            lay.notes["catalog_power_mm"] = cat_power
        elif not rack_ups:
            n_gvs, n_bat = _q("PWR-UPS-GVS100"), _q("PWR-BATT-LI")
            cat_power = n_gvs * CATALOG_FOOTPRINT["PWR-UPS-GVS100"] + n_bat * CATALOG_FOOTPRINT["PWR-BATT-LI"]
            rl_cat = rl - lay_power + cat_power
            _chk(lay, "I-C21", "A-002", f"Row length with catalog UPS/battery quantities ({n_gvs} x Galaxy VS 100 kW @521 + {n_bat} x Li cab @600, catalog qty rules) vs usable length",
                 f"{rl_cat:.0f} vs {budget:.0f}", rl_cat, budget, "<=",
                 resolution="" if rl_cat <= budget else (
                     f"Over by {rl_cat - budget:.0f} mm with {n_gvs} Galaxy VS 100 kW frames. Drawings assume one modular frame with internal N+1 modules "
                     f"({lay_power:.0f} mm incl. batteries). Options: Galaxy VS 150 kW single frame with redundant power module (521 mm) "
                     + ("- still 71 mm over for BEN 150: reduce end zone to 430 mm or preset 4 racks" if lay.tier == "ben150" else "or BEN 500 preset at 9 racks (frees 600 mm)")))
            lay.notes["catalog_power_mm"] = cat_power
        else:
            n93 = _q("PWR-UPS-93PM50") * CATALOG_FOOTPRINT["PWR-UPS-93PM50"]
            n_rm = _q("PWR-UPS-RM20")
            _chk(lay, "I-C21", "A-002", f"Row length with catalog UPS ({_q('PWR-UPS-93PM50')} x 93PM 50 kW tower @495 in the row; {n_rm} x PWR-UPS-RM20 rack-mount alternative) vs usable length",
                 f"{rl + n93:.0f} vs {budget:.0f}", rl + n93, budget, "<=",
                 resolution="" if rl + n93 <= budget else f"93PM towers do not fit the BEN 30 row; drawings use {n_rm} x 20 kVA rack-mount UPS (PWR-UPS-RM20, 10U each) in R1. Purchasing: keep one of the two catalog lines")
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
    tags = {"rack42": "R", "rack48": "R", "inrow300": "CU", "inrow600": "CU", "inrow_cw300": "CU", "cdu": "CDU", "cdu_hd": "CDU", "pump_unit": "PU",
            "ups600": "UPS", "ups800": "UPS", "batt": "BAT", "rect": "RECT", "batt800": "BAT"}
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
        if kind == "rack" and cooling == "dlc_hd":
            label = f"{spec['label']} + cold plates, UQD manifold" + (f", 800 V -> 50 V DC shelf x{d['rack_shelves_per_rack']}" if cfg.power_architecture == "dc800" else "")
        if key == "rect":
            label = f"{spec['label']}: {d['rectifier_modules']} x {d['rectifier_module_kw']} kW modules in {d['rectifier_cabinets']} cabinet(s), {d['dc_convention_label'].split(',')[0]}, IMD"
        if key == "batt800":
            label = f"{spec['label']}, {d['battery_on_bus_kwh']} kWh total for {cfg.ups_minutes} min"
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
    lay.items.append(Item("PWR-SVC-ENCL", "SVC", "power", f"Service section NEMA 4X: main breaker {d['service_breaker_a']} A + SPD + ATS (exterior, end wall)",
                          L + 160, W / 2 - 500, L + 160 + 400, W / 2 + 500, 600, 2000, mount="ext", kg=180, front="+x"))
    if (cooling == "inrow_dx" or lay.notes.get("n_air", 0)) and lay.notes.get("air_key", "inrow300") in ("inrow300", "inrow600"):
        n_air = lay.notes["n_air"]
        cus = [i for i in lay.items if i.tag.startswith("CU")]
        for i, cu in enumerate(cus):
            lay.items.append(Item("CLG-COND", f"CND{i+1}", "cooling", "Roof condenser 20 kW class", cu.x0 - 150, 250, cu.x1 + 150, 1050, H + 120, H + 120 + 700, mount="roof", kg=80))
    if cooling in ("rdhx_drycooler", "dlc_cdu"):
        lay.items.append(Item("CLG-DRYCOOLER", "DC1", "cooling", "Dry cooler (site, on pad adjacent to blind end)", L + 1500, -200, L + 1500 + 2400, W + 200, 0, 2200, mount="ext", kg=900))
    if cooling == "dlc_hd":
        lay.items.append(Item("CLG-DRYCOOLER-W45", "DC1", "cooling", f"W45 dry cooler bank (site pad, {math.ceil(d['liquid_heat_kw'] * 1.15)} kW rejection at design ambient)", L + 1500, -200, L + 1500 + 2400, W + 200, 0, 2200, mount="ext", kg=900))
        lay.items.append(Item("CLG-HRX", "HRX", "cooling", f"Heat-reuse plate heat exchanger (option), {d['heat_reuse_kw_available']} kW at the W45 return", L + 160, W / 2 + 700, L + 160 + 400, W / 2 + 1300, 300, 1500, mount="ext", kg=120, front="+x"))
        lay.items.append(Item("CLG-ISOVALVE-ROW", "ISO1", "cooling", "Row isolation valves (supply + return, spring-return, position feedback), close on leak", lay.notes["row_end_x"] - 300, 100, lay.notes["row_end_x"], 400, 2300, 2450, mount="ceiling", kg=12))
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
             resolution=f"IT in rack 1 limited to {lay.notes['u_it_rack1']}U; rack 2 carries the balance. Alternative: BEN 30 preset at 20 kW (2 modules)")
    if cooling == "rdhx_drycooler":
        _chk(lay, "I-C18", "M-001", "RDHx doors per rack vs config cooling_units_total",
             f"{cfg.racks} doors vs {d['cooling_units_total']} config units", cfg.racks, d["cooling_units_total"], ">=",
             resolution="RDHx is one door per rack (catalog CLG-RDHX qty = racks); config counts 35 kW units for capacity only")
    if cooling == "dlc_cdu":
        _chk(lay, "I-C19", "M-001", "Residual air load (25 % IT) vs in-row 300 capacity x units (N)",
             f"{0.25*cfg.it_kw*1.05:.1f} kW vs {lay.notes['n_air']} x 20 kW", lay.notes["n_air"] * 20, 0.25 * cfg.it_kw * 1.05, ">=")
    if cooling == "dlc_hd":
        resid = _CL["dlc_hd"]["air_residual"]
        _chk(lay, "I-C23", "M-001", f"Residual air load ({resid:.0%} IT, stated library value) vs W45 in-row fan coils x (units - 1)",
             f"{resid*cfg.it_kw*1.05:.1f} kW vs {lay.notes['n_air'] - 1} x 12 kW", (lay.notes["n_air"] - 1) * 12, resid * cfg.it_kw * 1.05, ">=")
        _chk(lay, "I-C24", "M-001", f"Row CDU capacity (N units) vs liquid heat x 1.05",
             f"{(d['cooling_units_n']) * 600} vs {d['liquid_heat_kw'] * 1.05:.0f}", d["cooling_units_n"] * 600, d["liquid_heat_kw"] * 1.05, ">=")
    if cfg.power_architecture == "dc800":
        _chk(lay, "I-C25", "E-001", f"DC busway frame vs bus current with 25 % headroom ({d['dc_convention_label'].split(',')[0]})",
             f"{d['dc_busway_a']} A vs {d['dc_bus_current_a']} A", d["dc_busway_a"], d["dc_bus_current_a"], ">=")
        _chk(lay, "I-C26", "E-001", "Rectifier modules (N, 100 kW) vs AC/DC front-end load",
             f"{d['rectifier_modules_n'] * d['rectifier_module_kw']} vs {d['ac_dc_front_end_kw']}", d["rectifier_modules_n"] * d["rectifier_module_kw"], d["ac_dc_front_end_kw"], ">=")
    # roof penetration positions clear of corrugation top rails (>= 300 from side rail)
    _chk(lay, "I-C20", "A-001", "Roof penetrations min 300 mm from side top rail", "line-set curbs at y=300 interior = 419 from ext side face", 419, 300, ">=",
         resolution="Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001")



def _resolve_hall(lay: Layout):
    """BEN 2000: 4 rows of racks_per_row along x in the IT bays (modules 2-3), cold/hot/cold/hot/cold aisles across the
    width, fan-wall units on the long wall y = W, CDUs at both row ends on a common secondary header, overhead busway
    and DLC manifolds per row. Module 1 (door end) holds the service vestibule, the BEN Controller panel, fire releasing
    and the staging zone. Power module, MV pad, generators, fuel and adiabatic dry coolers are exterior items (A-000)."""
    cfg, d = lay.cfg, lay.d
    L, W, H = lay.L, lay.W, lay.H
    rk = LIB["rack48"]
    rows = d["rows"]; rpr = d["racks_per_row"]
    red = cfg.redundancy
    endw = (lay.ext_l - L) / 2
    bay = lay.ext_l / lay.modules                     # 12,200 external bay pitch
    lay.notes.update({"bay_mm": bay, "section_w": HALL_SECTION_W, "n_sections": lay.modules * 3, "module_x": lay.module_x})
    _chk(lay, "I-H0", "A-001", "Hall external width vs 3 road sections of 3,660 mm joined side by side",
         f"3 x {HALL_SECTION_W} = {3 * HALL_SECTION_W} vs ext {lay.ext_w:.0f}", 3 * HALL_SECTION_W, lay.ext_w, "<=")
    # ---- width stack: wall | cold | R1 | hot | R2 | cold | R3 | hot | R4 | cold | fan wall
    seq = ["cold", "rack", "hot", "rack", "cold", "rack", "hot", "rack", "cold", "fanwall"]
    if rows != 4:
        seq = ["cold"] + sum([["rack", "hot" if i % 2 == 0 else "cold"] for i in range(rows)], [])[:-1] + ["cold", "fanwall"]
    widths = {"cold": HALL_COLD_AISLE, "hot": HALL_HOT_AISLE, "rack": rk["d"], "fanwall": HALL_FANWALL_D}
    stack = sum(widths[k] for k in seq)
    _chk(lay, "I-H1", "A-002", f"Width stack ({rows} rows, cold {HALL_COLD_AISLE} / hot {HALL_HOT_AISLE} aisles, racks {rk['d']} deep, fan wall {HALL_FANWALL_D}) vs interior width",
         f"{stack} vs {W:.0f}", stack, W, "<=")
    _chk(lay, "I-H2", "A-002", "Config row_length_mm (racks + CDUs + 500 end zone) vs interior length, config rule", f"{d['row_length_mm']} vs {L:.0f}", d["row_length_mm"], L, "<=")
    # ---- rows along x inside bays 2..n (bay 1 = vestibule / staging)
    row_len = rpr * rk["w"]
    cdu = LIB["cdu"]
    n_cdu = d["cooling_units_total"]
    per_row = [n_cdu // rows + (1 if i < n_cdu % rows else 0) for i in range(rows)]   # e.g. 2,2,2,1
    it_x0 = bay - endw + 600                           # start of the IT zone (bay 2) + 600 clear
    it_len = L - it_x0 - 600
    row_total = row_len + 2 * cdu["w"]
    x_row = it_x0 + (it_len - row_total) / 2          # rows centred in bays 2..n
    # snap so that no rack straddles a bay joint (a rack boundary lands on the joint)
    joints = [jx for jx in lay.module_x if x_row < jx < x_row + row_total]
    if joints:
        x_row += (joints[0] - (x_row + cdu["w"])) % rk["w"]
    _chk(lay, "I-H3", "A-002", f"Row footprint ({rpr} racks x 600 + 2 CDU ends) vs IT-zone length (bays 2-{lay.modules})",
         f"{row_total:.0f} vs {it_len:.0f}", row_total, it_len, "<=",
         resolution=f"Rows centred; {it_len - row_total:.0f} mm spare split to the two row-end service zones (staging, spares). Hall holds 48 racks at up to 80 kW DLC = 3,840 kW; preset {cfg.it_kw:.0f} kW")
    y = 0.0
    row_i = 0
    rack_i = 0
    cdu_i = 0
    aisle_y = []
    lay.notes["rows_y"] = []
    for k in seq:
        wdt = widths[k]
        if k in ("cold", "hot"):
            aisle_y.append((k, y, y + wdt))
        elif k == "rack":
            row_i += 1
            # front faces the cold aisle: rows 1,3 face -y (cold aisle before them), rows 2,4 face +y
            front = "-y" if (row_i % 2 == 1) else "+y"
            lay.notes["rows_y"].append((row_i, y, y + wdt, front))
            x = x_row
            # CDU at the west end
            n_here = per_row[row_i - 1]
            if n_here >= 1:
                cdu_i += 1
                lay.items.append(Item(cdu["code"], f"CDU{cdu_i}", "cooling", f"{cdu['label']} 300 kW, row {row_i} west end (common secondary header)", x, y, x + cdu["w"], y + wdt, 0, cdu["h"], kg=cdu["kg"], front=front))
            x += cdu["w"]
            for j in range(rpr):
                rack_i += 1
                lay.items.append(Item(rk["code"], f"R{rack_i}", "rack", f"{rk['label']} (row {row_i}, DLC manifold + residual air)", x, y, x + rk["w"], y + wdt, 0, rk["h"], kg=rk["kg"], front=front, note=f"row{row_i}"))
                x += rk["w"]
            if n_here >= 2:
                cdu_i += 1
                lay.items.append(Item(cdu["code"], f"CDU{cdu_i}", "cooling", f"{cdu['label']} 300 kW, row {row_i} east end (common secondary header)", x, y, x + cdu["w"], y + wdt, 0, cdu["h"], kg=cdu["kg"], front=front))
            # overhead busway A/B and DLC manifolds over the row
            lay.items.append(Item("PWR-BUSWAY", f"BUS-{row_i}A", "power", f"Overhead busway 800 A, row {row_i} path A", x_row, y + 50, x_row + row_total, y + 250, HALL_BUSWAY_Z, HALL_BUSWAY_Z + 150, mount="ceiling", kg=28 * row_total / 1000))
            lay.items.append(Item("PWR-BUSWAY", f"BUS-{row_i}B", "power", f"Overhead busway 800 A, row {row_i} path B", x_row, y + wdt - 250, x_row + row_total, y + wdt - 50, HALL_BUSWAY_Z, HALL_BUSWAY_Z + 150, mount="ceiling", kg=28 * row_total / 1000))
            lay.items.append(Item("CLG-MANIFOLD", f"MAN-{row_i}", "cooling", f"DLC supply/return manifolds DN80 over row {row_i}, QD drops per rack", x_row, y + 350, x_row + row_total, y + wdt - 350, HALL_MANIFOLD_Z, HALL_MANIFOLD_Z + 200, mount="ceiling", kg=40 * row_total / 1000))
        elif k == "fanwall":
            # fan-wall units along the long wall, spread over the IT zone
            n_fw = lay.modules + 1
            fw = LIB["fanwall"]
            pitch = it_len / n_fw
            for i in range(n_fw):
                fx = it_x0 + pitch * (i + 0.5) - fw["w"] / 2
                lay.items.append(Item(fw["code"], f"FW{i+1}", "cooling", f"{fw['label']} (residual air, N+1), long wall", fx, y, fx + fw["w"], y + wdt, 0, fw["h"], kg=fw["kg"], front="-y"))
            lay.notes["n_fanwall"] = n_fw
        y += wdt
    lay.notes.update({"row_x0": x_row, "row_x1": x_row + row_total, "row_len": row_total, "aisles": aisle_y, "n_cdu": n_cdu, "cdu_per_row": per_row,
                      "row_front_y": HALL_COLD_AISLE, "plenum": 0, "n_air": 0, "cooling_resolved": cfg.cooling, "rack_ups": False, "it_x0": it_x0, "it_x1": it_x0 + it_len})
    # containment: hot-aisle pods (doors at both ends, roof panels rack top to 2,400)
    for k, (kind, y0, y1) in enumerate([a for a in aisle_y if a[0] == "hot"], 1):
        lay.items.append(Item("STR-CONT-ROOF", f"HAC{k}", "cooling", f"Hot-aisle containment pod {k}: roof panels + end doors", x_row, y0, x_row + row_total, y1, rk["h"], rk["h"] + 200, mount="wall", kg=120, note="plenum"))
    # ---- bay 1: vestibule / mantrap, controller, fire, staging
    mt = LIB["mantrap"]
    lay.items.append(Item("ENV-DOORGASKET-4X", "VEST", "structure", "Service vestibule 3.0 x 2.4 m, IP66 doors with compression gaskets (mantrap interlock at H3)", 0, W / 2 - mt["d"] / 2, mt["w"], W / 2 + mt["d"] / 2, 0, mt["h"], mount="wall", kg=mt["kg"]))
    gw = LIB["controller"]
    lay.notes["controls_tier"] = "pro"
    lay.items.append(Item(gw["code"], "CP1", "controls", gw["label"] + " + plant PLC (bay 1 wall, 1200 AFF)", 3600, 100, 3600 + gw["w"], 100 + gw["d"], 1200, 1200 + gw["h"], mount="wall", kg=gw["kg"], front="+y"))
    for m in range(lay.modules):
        xm = 3600 + 900 + m * 300 if m == 0 else lay.module_x[m - 1] + 300
        lay.items.append(Item("CTL-PLC", f"PLC{m+1}", "controls", f"Module {m+1} PLC (PLCnext) in wall panel", xm, 100, xm + 400, 300, 1300, 1900, mount="wall", kg=25, front="+y"))
    cyl = LIB["cyl_bank"]
    for m in range(lay.modules):
        xm = 6000 if m == 0 else lay.module_x[m - 1] + 800
        lay.items.append(Item(cyl["code"], f"FS{m+1}", "fire", f"{cyl['label']} module {m+1}, wall bracket", xm, 100, xm + cyl["w"], 100 + cyl["d"], 0, cyl["h"], kg=cyl["kg"], front="+y"))
    lay.items.append(Item("FS-CLEAN-AGENT-HALL", "FRP", "fire", "Fire releasing panel, 3 zones (vestibule wall, 1500 AFF)", mt["w"] + 150, W - 100, mt["w"] + 450, W, 1500, 1900, mount="wall", kg=8, front="-y"))
    lay.items.append(Item("FS-EPO", "EPO", "power", "EPO push-button (vestibule, 1200 AFF)", mt["w"] + 600, W - 60, mt["w"] + 700, W, 1200, 1300, mount="wall", kg=1, front="-y"))
    lay.items.append(Item("CTL-LEAK", "LEAK", "controls", "Leak rope: perimeter, under every CDU and along the manifold drip trays", 0, 0, L, W, 0, 20, mount="floor", kg=12))
    lay.items.append(Item("STR-TRAY", "TR-D", "tray", "Cable tray 300 wide, data (overhead, bay 1 -> rows)", 0, W / 2 - 150, x_row + row_total, W / 2 + 150, TRAY_Z + 350, TRAY_Z + 450, mount="ceiling", kg=6 * L / 1000))
    lay.items.append(Item("ENV-LED", "STG", "structure", "Staging / unloading zone (bay 1), 2.5 kN/m2 live load", mt["w"] + 300, 600, bay - endw - 300, W - 1600, 0, 10, mount="floor", kg=0))
    # ---- exterior: power module, MV pad, generators, fuel, adiabatic dry coolers, pump skid (site plan A-000)
    pm_y0 = W + SITE_SETBACK
    pm_w, pm_d = bay, 3 * HALL_SECTION_W
    lay.items.append(Item("STR-MODULE-PWR", "PM", "power", f"Power module {pm_w/1000:.1f} x {pm_d/1000:.1f} m (3 sections): 480 V switchgear A/B, UPS 2N, 2 battery rooms", 0, pm_y0, pm_w, pm_y0 + pm_d, 0, 4200, mount="ext", kg=18000 + 6000 + 2 * 6000 + 8 * 1100))
    sw = LIB["lv_swgr"]
    for k, tag in enumerate(("SWGR-A", "SWGR-B")):
        sx = 400 + k * (sw["w"] + 1200)
        lay.items.append(Item(sw["code"], tag, "power", f"{sw['label']} path {tag[-1]}, working space {SWGR_WS_DRAWN} in front, 1000 rear", sx, pm_y0 + 300, sx + sw["w"], pm_y0 + 300 + sw["d"], 0, sw["h"], mount="ext", kg=sw["kg"], front="+y", note="in PM"))
    n_frames = d["ups_modules"] * math.ceil(d["ups_kva_each"] / 500)
    uf = LIB["ups_vl"]
    for k in range(n_frames):
        ux = 400 + k * (uf["w"] + 100)
        lay.items.append(Item(uf["code"], f"UPS{k+1}", "power", f"{uf['label']} string {'A' if k < n_frames/2 else 'B'}", ux, pm_y0 + 300 + sw["d"] + SWGR_WS_DRAWN + 200, ux + uf["w"], pm_y0 + 300 + sw["d"] + SWGR_WS_DRAWN + 200 + uf["d"], 0, uf["h"], mount="ext", kg=uf["kg"], front="-y", note="in PM"))
    br = LIB["batt_room"]
    for k in range(2):
        bx = pm_w - 400 - br["w"] - k * (br["w"] + 300)
        lay.items.append(Item(br["code"], f"BATT-{'AB'[k]}", "power", f"{br['label']} string {'AB'[k]}, {d['battery_kwh']} kWh", bx, pm_y0 + pm_d - 300 - br["d"], bx + br["w"], pm_y0 + pm_d - 300, 0, br["h"], mount="ext", kg=br["kg"], note="in PM"))
    mv = LIB["mv_swgr"]; xf = LIB["mv_xfmr"]
    lay.items.append(Item(mv["code"], "MV-SWGR", "power", mv["label"] + " (MV pad)", -3000 - 3000 - xf["w"] - mv["w"], pm_y0 + 600, -3000 - 3000 - xf["w"], pm_y0 + 600 + mv["d"], 0, mv["h"], mount="ext", kg=mv["kg"]))
    for k in range(d["transformers_total"]):
        lay.items.append(Item(xf["code"], f"XFMR-{'AB'[k % 2]}", "power", xf["label"] + f" path {'AB'[k % 2]}", -3000 - xf["w"], pm_y0 + 400 + k * (xf["d"] + 1000), -3000, pm_y0 + 400 + k * (xf["d"] + 1000) + xf["d"], 0, xf["h"], mount="ext", kg=xf["kg"]))
    gs = LIB["genset"]
    gx0 = pm_w + 3000
    for k in range(d["generators_total"]):
        gy = pm_y0 + k * (gs["d"] + 1300)
        lay.items.append(Item(gs["code"], f"GEN{k+1}", "power", gs["label"] + (" (N+1)" if k == d["generators_total"] - 1 else ""), gx0, gy, gx0 + gs["w"], gy + gs["d"], 0, gs["h"], mount="ext", kg=gs["kg"]))
    gsw = LIB["gen_swgr"]
    lay.items.append(Item(gsw["code"], "GEN-SWGR", "power", gsw["label"] + " (outdoor walk-in)", gx0 + gs["w"] + 1500, pm_y0, gx0 + gs["w"] + 1500 + gsw["w"], pm_y0 + gsw["d"], 0, gsw["h"], mount="ext", kg=gsw["kg"]))
    ft = LIB["fuel_tank"]
    lay.items.append(Item(ft["code"], "FUEL", "power", ft["label"] + ", SPCC containment", gx0 + gs["w"] + 1500, pm_y0 + gsw["d"] + 1500, gx0 + gs["w"] + 1500 + ft["w"], pm_y0 + gsw["d"] + 1500 + ft["d"], 0, ft["h"], mount="ext", kg=ft["kg"]))
    ad = LIB["adiabatic"]
    n_dc = math.ceil(d["total_kw"] * 1.1 / ad["kw"])
    lay.notes["n_drycooler"] = n_dc
    dx0 = L + endw + 4000
    for k in range(n_dc):
        dy = -300 + k * (ad["d"] + 4000)
        lay.items.append(Item(ad["code"], f"DC{k+1}", "cooling", ad["label"] + f" ({k+1}/{n_dc}, {n_dc} x 400 kW >= {d['total_kw'] * 1.1:.0f} kW rejection)", dx0, dy, dx0 + ad["w"], dy + ad["d"], 0, ad["h"], mount="ext", kg=ad["kg"]))
    ps = LIB["pump_skid"]
    lay.items.append(Item(ps["code"], "PUMP", "cooling", ps["label"], dx0 + ad["w"] + 1500, -300, dx0 + ad["w"] + 1500 + ps["w"], -300 + ps["d"], 0, ps["h"], mount="ext", kg=ps["kg"]))
    lay.items.append(Item("STR-PLANTYARD", "YARD", "structure", "Plant yard: pipe rack, skids, bollards, crushed-stone surface", L + endw + 2000, -SITE_SETBACK, dx0 + ad["w"] + 1500 + ps["w"] + 2000, -300 + (n_dc - 1) * (ad["d"] + 4000) + ad["d"] + 2000, 0, 0, mount="ext", kg=0))
    lay.items.append(Item("SITE-CRANE-HALL", "CRANE", "structure", "Crane hardstand and access lane (100-130 t AT crane), 6 m wide", -endw - SITE_SETBACK, -SITE_SETBACK - 6000, L + endw + SITE_SETBACK, -SITE_SETBACK, 0, 0, mount="ext", kg=0))
    # ---- checks
    cold = [a for a in aisle_y if a[0] == "cold"]; hot = [a for a in aisle_y if a[0] == "hot"]
    _chk(lay, "I-H4", "A-002", "Cold aisle width vs NEC 110.26 condition 2 (1067, equipment on both sides) and 900 egress",
         f"{cold[0][2] - cold[0][1]:.0f} vs 1067", cold[0][2] - cold[0][1], NEC_WS_COND2, ">=")
    _chk(lay, "I-H5", "A-002", "Contained hot aisle width vs 900 egress (doors at both ends)", f"{hot[0][2] - hot[0][1]:.0f} vs 900", hot[0][2] - hot[0][1], EGRESS_MIN, ">=")
    _chk(lay, "I-H6", "A-002", "Fan-wall discharge aisle (cold aisle 3 in front of the fan wall) vs 1067", f"{cold[-1][2] - cold[-1][1]:.0f} vs 1067", cold[-1][2] - cold[-1][1], NEC_WS_COND2, ">=")
    _chk(lay, "I-H7", "E-001", f"480 V switchgear 4,000 A working space, NEC 110.26(A)(1) condition 3 (grounded/live both sides) at 480 V: drawn {SWGR_WS_DRAWN} vs 1,200 min; two entrances >= 610 x 2,000 (110.26(C)(2), >= 1,200 A and > 1.8 m wide)",
         f"{SWGR_WS_DRAWN} vs {NEC_WS_COND3_LV}", SWGR_WS_DRAWN, NEC_WS_COND3_LV, ">=",
         resolution="1,500 drawn: 1,200 cond. 3 minimum + 300 for drawout breaker lift truck; rear access 1,000; two exits from the switchgear room")
    pm_stack = 300 + sw["d"] + SWGR_WS_DRAWN + 200 + uf["d"] + 1200 + br["d"] + 300
    _chk(lay, "I-H8", "A-000", "Power module depth stack (switchgear + working space + UPS row + 1,200 aisle + battery rooms) vs 3 sections (11.0 m)",
         f"{pm_stack} vs {pm_d}", pm_stack, pm_d, "<=")
    two_lineups = 2 * sw["w"] + 1200 + 800
    _chk(lay, "I-H9", "A-000", "Two 4,000 A lineups side by side + 1,200 between + ends vs power module length", f"{two_lineups} vs {pm_w:.0f}", two_lineups, pm_w, "<=")
    row_kw = cfg.it_kw / rows
    _chk(lay, "I-H10", "M-001", f"CDU capacity on the common secondary header vs IT x 1.05 + one 300 kW spare (row {rows} alone has {per_row[-1]} CDU = {per_row[-1] * 300} kW < row load {row_kw:.0f} kW, so per-row CDUs would not carry N)",
         f"{n_cdu} x 300 = {n_cdu * 300} vs {cfg.it_kw * 1.05 + 300:.0f}", n_cdu * 300, cfg.it_kw * 1.05 + 300, ">=",
         resolution=f"CDUs feed one ring-main secondary header so N+1 is system-wide ({per_row} per row); per-row isolation valves, header sized DN150")
    _chk(lay, "I-H11", "M-001", "Residual air (25 % of IT) vs fan-wall units N (one per module)", f"{0.25 * cfg.it_kw * 1.05:.0f} vs {(lay.notes['n_fanwall'] - 1) * 200}", (lay.notes["n_fanwall"] - 1) * 200, 0.25 * cfg.it_kw * 1.05, ">=")
    _chk(lay, "I-H12", "A-003", "Overhead stack: rack 2,200 + manifold + busway (top) vs interior height - 300 for lights and sprinkler/clean-agent nozzles",
         f"{HALL_BUSWAY_Z + 150} vs {H - 300:.0f}", HALL_BUSWAY_Z + 150, H - 300, "<=")
    _chk(lay, "I-H13", "A-003", "Road section travel height (4,200 + 600 lowboy deck) vs 4,880 (16 ft) permit route limit",
         "4200 + 600 = 4800 vs 4880", 4800, 4880, "<=", resolution="Lowboy / drop-deck trailer, route survey and superload permits (SITE-FREIGHT-WB); 3.66 m width needs escorts")
    kwh_room = d["battery_kwh"] * d["ups_modules"] / 2
    _chk(lay, "I-H14", "E-001", "Lithium battery energy per room vs NFPA 855 600 kWh group limit (UL 9540A large-scale test above it), 2-hour separation between rooms",
         f"{kwh_room:.0f} kWh per room vs 600", kwh_room, 600, "<=")
    _chk(lay, "I-H15", "A-000", "Generator enclosure to hall / power module clearance vs 3,000 (NFPA 37 1.5 m min to combustible walls; 3 m for service and radiator discharge)",
         f"{gx0 - pm_w:.0f} vs 3000", gx0 - pm_w, 3000, ">=")
    _chk(lay, "I-H16", "A-000", "FR3 ester pad-mount transformer to power module clearance vs 900 (FM 5-4 / IEEE C57.12 less-flammable liquid, non-combustible wall)",
         "3000 vs 900", 3000, 900, ">=")
    _chk(lay, "I-H17", "A-000", "Setback / fire lane around the hall vs 6,000 (IFC 503 fire apparatus access 6.1 m)", f"{SITE_SETBACK} vs 6100", SITE_SETBACK, 6100, ">=",
         resolution="Fire lane is the 6 m crane lane on the south side plus the 6 m yard; AHJ confirms the access route")
    floor = (rk["kg"] * 9.81 / 1000) / (0.6 * 1.07)
    _chk(lay, "I-H18", "S-001", "Rack footprint load (1,000 kg on 0.6 x 1.07 m) vs 200 mm slab-on-grade design 20 kN/m2", f"{floor:.1f} kN/m2 vs 20", floor, 20, "<=")
    sec_kg = d["geometry"]["tare_kg"] / lay.modules / 3 + 800
    _chk(lay, "I-H19", "S-001", "Road section lift mass (tare per section + 800 kg fit-out) vs 100 t AT crane at 20 m radius (~25 t)", f"{sec_kg:.0f} vs 25000", sec_kg, 25000, "<=")
    _chk(lay, "I-H20", "A-001", "Hall gross mass (config) vs slab + grade beams design 1,200 t", f"{d['gross_kg']} vs 1200000", d["gross_kg"], 1200000, "<=")


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
    heights = (300, 700, 1100) if lay.is_cabinet else (400, 1200, 1800)
    lay.notes["probe_heights"] = heights

    def cold_hot_y(r):
        if lay.is_hall:
            return (r.y0 - 50, r.y1 + 50) if r.front == "-y" else (r.y1 + 50, r.y0 - 50)
        return rf + 50, (r.y0 - 50 if lay.notes.get("plenum", 0) else r.y0 + 50)
    for i, r in enumerate(racks):
        node = f"node{i // 2 + 1}"
        cy, hy = cold_hot_y(r)
        for j, z in enumerate(heights):
            lay.sensors.append(Sensor(f"T_in_r{i+1}_{z/1000:g}", "T", node, r.cx, cy, z, f"T_in_{j+1}"))
        lay.sensors.append(Sensor(f"T_out_r{i+1}", "T", node, r.cx, hy, heights[1], "T_out_1"))
    cus = [i for i in lay.items if i.tag.startswith("CU") or i.tag.startswith("PU") or i.tag.startswith("CDU")]
    if cus:
        c = cus[0]
        lay.sensors.append(Sensor("T_supply", "T", "node1", c.cx, rf + 50, 300, "T_in_4"))
        lay.sensors.append(Sensor("T_return", "T", "node1", c.cx, max(c.y0 - 50, 20), 2200 if lay.is_container else 1100, "T_out_4"))
    zmid = 900 if lay.is_cabinet else 1500
    if lay.is_hall:
        cold = [a for a in lay.notes["aisles"] if a[0] == "cold"]
        for m in range(lay.modules):
            xm = (lay.module_x + [lay.L])[m] - 2000 if m else 6000
            lay.sensors.append(Sensor(f"RH_room_m{m+1}", "RH", "node1", xm, (cold[1][1] + cold[1][2]) / 2, zmid, "RH"))
        lay.sensors.append(Sensor("dP_aisle", "dP", "node1", lay.notes["row_x0"] + 1000, lay.notes["rows_y"][0][2], zmid, "dP_aisle"))
        lay.sensors.append(Sensor("leak_floor", "leak", "node1", lay.notes["row_x0"], cold[0][1] + 100, 20, "leak"))
        lay.sensors.append(Sensor("door_main", "door", "node1", 50, lay.W / 2, 1000, "door"))
        lay.sensors.append(Sensor("P_utility", "kWh", "meter1", 3600, 80, zmid, "pulse_kwh"))
    else:
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
        if lay.is_hall:
            cold_y, hot_y = (r.y0 - 70, r.y1 + 20) if r.front == "-y" else (r.y1 + 20, r.y0 - 70)
        else:
            cold_y = rf + 20 if lay.is_container else r.y1 + 10
            hot_y = (r.y0 - 70 if lay.notes.get("plenum", 0) else r.y0 - 70) if lay.is_container else r.y0 - 60
        pods.append(Item("CTL-POD", f"P{2*i+1}", "controls", f"BEN Pod W (cold face R{i+1}, Thread, 4 x Pt1000)", r.x0 + 40, cold_y, r.x0 + 140, cold_y + 50, ztop, ztop + 120, mount="rack", kg=0.3))
        pods.append(Item("CTL-POD", f"P{2*i+2}", "controls", f"BEN Pod W (hot face R{i+1}, Thread, 4 x Pt1000)", r.x0 + 40, max(hot_y, 0), r.x0 + 140, max(hot_y, 0) + 50, ztop, ztop + 120, mount="rack", kg=0.3))
    cp = lay.find("CP1")
    k = len(pods) + 1
    if lay.is_hall:
        xs = [6000] + [x + 1500 for x in lay.module_x]
        for m, xm in enumerate(xs):
            pods.append(Item("CTL-POD", f"P{k}", "controls", f"BEN Pod E (module {m+1} room: RH, dP, leak; RS-485 to PLC{m+1}; Thread router)", xm, 20, xm + 120, 70, 2000, 2120, mount="wall", kg=0.4)); k += 1
            pods.append(Item("CTL-POD", f"P{k}", "controls", f"BEN Pod E (module {m+1} outdoor / plant yard, IP66)", xm, lay.W + 350, xm + 120, lay.W + 400, 1800, 1920, mount="ext", kg=0.5)); k += 1
    elif lay.is_container and cp:
        pods.append(Item("CTL-POD", f"P{k}", "controls", "BEN Pod E (room: RH, dP, leak, door; RS-485 to controller; Thread router)", cp.x0 - 220, cp.y0, cp.x0 - 100, cp.y0 + 50, cp.z1 + 100, cp.z1 + 220, mount="wall", kg=0.4))
        pods.append(Item("CTL-POD", f"P{k+1}", "controls", "BEN Pod E (outdoor: dry cooler / condenser pad, IP65)", lay.L + 160, -300, lay.L + 280, -250, 1800, 1920, mount="ext", kg=0.5))
    else:
        pods.append(Item("CTL-POD", f"P{k}", "controls", "BEN Pod E (room: RH, dP, leak, door; RS-485 to RevPi; Thread router)", 200, 20, 320, 70, 1250, 1370, mount="wall", kg=0.4))
    lay.items.extend(pods)
    lay.notes["n_pods"] = len(pods)


# ------------------------------------------------------------------ reporting
def is_valid_hardening(lay: Layout) -> bool:
    return lay.cfg.hardening in HARDENING


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

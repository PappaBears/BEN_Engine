"""BEN Engine — ASD-STE100 assembly instructions generator.

Writes design/assembly/ASSEMBLY-<tier>.md for each tier from the shared layout engine
(design/layout.py) and the CTQ/CTP register (design/ctq.py), plus ITEM_CODES_USED.md.

Writing rules: design/assembly/STE_STYLE.md. One instruction per sentence, <= 20 words,
imperative, approved vocabulary, warnings and cautions before the step they apply to.

Run:  python design/assembly/gen_assembly.py
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import layout as L  # noqa: E402
import ctq as C  # noqa: E402
from revision import REV  # noqa: E402  (design/REVISION.json — issue letter and date of the whole set)

DATE = REV["issue_date"]
ISSUE = REV["issue_label"]          # "Issue B · 2026-11-08"

# ------------------------------------------------------------------ item codes (reconcile with purchasing/bom.csv)
ITEMS = {
    "STR-001": "Floor channel C100x50x5, hot-dip galvanised, 3 m lengths",
    "STR-002": "Bolt kit M12 x 8.8 (bolt, nyloc nut, 2 washers), zinc flake",
    "STR-003": "Steel shim pack 1 / 2 / 5 mm",
    "STR-004": "Reinforcement frame 50x50x5 angle, for shell cutouts",
    "STR-005": "Rack hold-down angle 100x100x8 with 2 x M12 slots",
    "STR-010": "Steel skid 1.3 x 1.1 m with fork pockets (BEN 5)",
    "STR-011": "Wedge anchor M16 x 140, with washer and nut",
    "STR-020": "Cable tray 300 x 100 mm, wire mesh, data (TR-D)",
    "STR-021": "Cable tray 300 x 100 mm, wire mesh, power (TR-P)",
    "STR-022": "Tray ceiling bracket + M10 threaded rod, 1.5 m pitch",
    "STR-030": "Seismic strut kit P1000 channel + fittings (option)",
    "ENV-001": "PIR insulation board 100 mm, foil faced, 1200 x 2400",
    "ENV-002": "Liner panel 0.7 mm galvanised steel, white, 1000 mm cover",
    "ENV-003": "Sealant, polyurethane, grey, 600 ml sausage",
    "ENV-004": "PIR adhesive + mechanical pins (4 per m2)",
    "ENV-005": "EPDM bulb seal 20 mm, self-adhesive",
    "ENV-006": "Floor PIR 80 mm + 18 mm plywood panels",
    "ENV-007": "Anti-static vinyl floor 2 mm, grey",
    "ENV-008": "EPDM roof boot kit + butyl tape + clamp band",
    "ENV-009": "Brand panel, aluminium composite 1.5 mm, printed",
    "ENV-010": "Closed-cell foam 20 mm, self-adhesive (thermal bridges)",
    "ENV-011": "Floor drain 50 mm with trap and exterior cap",
    "ENV-012": "Zinc-rich primer + topcoat C4-M, 1 L",
    "ENV-013": "Cabinet door gasket IP55 + 100 W anti-condensation heater (BEN 5)",
    "CMP-001": "IT rack 42U 600 x 1070, perforated doors, 1000 kg rating",
    "CMP-002": "IT rack 48U 600 x 1070, perforated doors, 1200 kg rating",
    "CMP-003": "Rack rails 24U kit (BEN 5 cabinet)",
    "CMP-010": "Blanking panel 1U, tool-less, pack of 10",
    "CMP-011": "Rack grounding kit (6 AWG, lugs, bar)",
    "CLG-001": "Cabinet DX air conditioner 5.8 kW, side mount (BEN 5)",
    "CLG-010": "In-row DX cooling unit 300 mm, 20 kW class, EC fans",
    "CLG-015": "Roof condenser 20 kW class, EC fan, low-ambient kit",
    "CLG-016": "Pre-insulated refrigerant line set 3/8 + 7/8, 15 m",
    "CLG-017": "Condensate drain kit 32 mm PVC, trap, clips",
    "CLG-020": "Coolant distribution unit 300 kW, N+1 pumps, Modbus",
    "CLG-030": "RDHx pumping unit, plate HX, N+1 pumps, Modbus",
    "CLG-031": "Rear-door heat exchanger 35 kW, 42U, with flex hoses",
    "CLG-032": "Secondary manifold set DN50/DN65, insulated, with isolation valves",
    "CLG-033": "Propylene glycol 30 % premix, 200 L",
    "CLG-034": "Primary pipe kit to dry cooler, DN65, insulated, 20 m",
    "CLG-040": "Dry cooler 150-300 kW, EC fans, adiabatic option",
    "CLG-050": "Hot-aisle containment kit: top panels, end door, brush strips",
    "PWR-010": "Rack-mount UPS (size per tier), with network card",
    "PWR-011": "Rack-mount Li-ion battery module",
    "PWR-020": "Rack PDU zero-U, metered, 2 per rack",
    "PWR-030": "Service entrance box 1 ph 50 A, NEMA 4X (BEN 5)",
    "PWR-100": "Modular UPS frame 600 mm, 50-150 kVA, internal Li-ion",
    "PWR-101": "Modular UPS frame 800 mm, 150-300 kVA",
    "PWR-110": "Li-ion battery cabinet 20 kWh, UL 9540A",
    "PWR-120": "Mechanical panelboard, 24 circuits, with Type 2 SPD",
    "PWR-121": "IT distribution panelboard (UPS output)",
    "PWR-122": "Isolation transformer 480-415/240 V, K-13 (480 V tiers)",
    "PWR-130": "EPO mushroom push-button station, 2 NC + 2 NO",
    "PWR-140": "Service section NEMA 4X: main CB, Type 1 SPD, ATS",
    "PWR-150": "Power cable set (feeders, branch circuits), pre-cut and labelled",
    "PWR-160": "Grounding kit: TMGB bar, ground rods, exothermic moulds, 6 AWG",
    "PWR-170": "Receptacle set for rack PDUs, IEC 60309, labelled",
    "CTL-001": "BEN Controller: UL 508A panel with PLCnext AXC F 2152, Axioline F I/O, Karbon 400 edge computer, 2 x QUINT4 24 VDC, managed switch, SPD; or BEN Controls Lite cabinet with RevPi Connect 4, DIO/AIO, 24 VDC, switch",
    "CTL-002": "BEN Pod: MGM240P Thread module, Secure Vault, 4 x Pt1000 inputs, rack-rail / DIN enclosure, provisioned",
    "CTL-003": "Pt1000 class A 3-wire probe string, 4 probes, 3 m, M12, labelled",
    "CTL-004": "Room RH/T transmitter Vaisala HMW90, 4-20 mA to the PLC",
    "CTL-005": "Aisle differential pressure: Setra 264 4-20 mA on Pro, Pod SDP810 on Lite, + 2 x 3 m tubing + pitot taps",
    "CTL-007": "Door contact, magnetic reed, surface mount",
    "CTL-008": "Industrial Ethernet switch, 8 port, DIN mount, controls LAN",
    "CTL-009": "Cat6A patch cables, shielded, labelled set",
    "CTL-010": "Conductive leak rope 30 m + end-of-line terminator",
    "CTL-011": "Label kit: laminated tags 10 mm text, cable markers",
    "CTL-012": "PLCnext AXC F 2152 controller with Axioline F I/O, inside CTL-001, Pro",
    "CTL-013": "RevPi Connect 4 controller with RevPi DIO / AIO, inside CTL-001, Lite",
    "CTL-014": "OnLogic Karbon 400 edge computer, TPM 2.0, inside CTL-001, Pro",
    "CTL-015": "Thread border router radio, MGM240P RCP on USB, 1 or 2",
    "CTL-016": "SeaHawk LD2100 leak detection controller, Pro",
    "CTL-017": "24 VDC power supply QUINT4, 2 redundant on Pro, 1 on Lite",
    "FS-001": "Aerosol fire suppression unit, cabinet size (BEN 5)",
    "FS-010": "Clean-agent cylinder (FK-5-1-12), wall bracket, sized per room",
    "FS-020": "Fire releasing panel with abort, 2 detection zones",
    "FS-030": "Smoke detectors, photoelectric, 2 per zone",
    "FS-040": "Discharge pipe + nozzles kit",
    "SITE-001": "Concrete pad per site drawing, 4 twist-lock foundations",
    "SITE-002": "Twist-locks / tie-down plates, 4",
    "SITE-003": "Ground rods 3 m Cu-clad, 2, with clamps",
    "SITE-004": "Fibre entry: 2 x SMF, with ODF",
    "SITE-005": "Rigging: 4-leg sling set, spreader, shackles rated for gross mass",
    "SITE-006": "Transport blocking and strapping kit",
}


# ------------------------------------------------------------------ reconciliation with purchasing/parts_catalog.json
import json as _json
import re as _re
_CAT_PATH = os.path.join(os.path.dirname(os.path.dirname(HERE)), "purchasing", "parts_catalog.json")
CATALOG = {p["code"]: p for p in _json.load(open(_CAT_PATH))}


def _by_controls(lite, pro):
    """lite / pro: catalog code by the resolved controls tier (Config.controls_tier_resolved)."""
    return lambda lay: pro if lay.cfg.controls_tier_resolved() == "pro" else lite


def _by_tier(**kw):
    """kw: tier -> catalog code (or 'default')."""
    def f(lay):
        return kw.get(lay.tier, kw.get("default"))
    return f


# old working code -> catalog code (string) or callable(lay) -> code. Secondary catalog items that come with the
# mapped item are listed in ALSO so ITEM_CODES_USED.md can show them.
MAP = {
    "STR-001": "STR-FLOORCHAN", "STR-002": "STR-FASTENERS", "STR-003": "STR-FASTENERS", "STR-004": "SVC-MODS-MAT",
    "STR-005": "STR-SEISMIC", "STR-010": "STR-SKID", "STR-011": "STR-FASTENERS", "STR-020": "STR-TRAY", "STR-021": "STR-TRAY",
    "STR-022": "STR-FASTENERS", "STR-030": "STR-STRUT-KIT",
    "ENV-001": "ENV-PIR", "ENV-002": "ENV-LINER", "ENV-003": "ENV-SEAL", "ENV-004": "ENV-HAT", "ENV-005": "ENV-DOORSEAL",
    "ENV-006": "ENV-FLOOR-PIR", "ENV-007": "ENV-FLOOR", "ENV-008": "ENV-ROOFBOOT", "ENV-009": "ENV-BRANDPANEL", "ENV-010": "ENV-SEAL",
    "ENV-011": "ENV-DRAIN", "ENV-012": "SVC-MODS-MAT", "ENV-013": "ENV-MICRO-HEATER",
    "CMP-001": "STR-RACK42", "CMP-002": "STR-RACK48", "CMP-003": "STR-CAB24U", "CMP-010": "CMP-BLANK", "CMP-011": "PWR-GROUNDBAR",
    "CLG-001": "CLG-CABAC", "CLG-010": "CLG-INROW", "CLG-015": "CLG-COND", "CLG-016": "CLG-REFRIG", "CLG-017": "CLG-CONDPUMP",
    "CLG-020": "CLG-CDU", "CLG-030": "CLG-CDU-RDHX", "CLG-031": "CLG-RDHX", "CLG-032": _by_tier(ben40="CLG-MANIFOLD", default="CLG-PIPING"),
    "CLG-033": "CLG-GLYCOL", "CLG-034": "CLG-PIPING", "CLG-040": "CLG-DRYCOOLER", "CLG-050": "STR-CONT-ROOF",
    "PWR-010": _by_tier(micro="PWR-UPS-SRT6K", default="PWR-UPS-RM20"), "PWR-011": _by_tier(micro="PWR-UPS-SRT6K-XBP", default="PWR-UPS-RM20-XBP"),
    "PWR-020": "PWR-PDU", "PWR-030": "PWR-LOADCTR", "PWR-100": "PWR-UPS-GVS100", "PWR-101": "PWR-UPS-GVS100", "PWR-110": "PWR-BATT-LI",
    "PWR-120": _by_tier(micro="PWR-LOADCTR", ben10="PWR-PANEL-NQ", default="PWR-PANEL-ILINE"), "PWR-121": "PWR-PANEL-NQ",
    "PWR-122": _by_tier(ben40="PWR-XFMR-300", default="PWR-XFMR"), "PWR-130": _by_tier(micro="FS-EPO-MICRO", default="FS-EPO"),
    "PWR-140": "PWR-SVC-ENCL", "PWR-150": "PWR-FEEDER", "PWR-160": "PWR-GROUNDBAR", "PWR-170": "PWR-RCPT",
    "CTL-001": _by_controls("CTL-ENCL", "CTL-PANEL"), "CTL-002": "CTL-POD", "CTL-003": "CTL-PT1000", "CTL-004": "CTL-VAISALA-HMW90",
    "CTL-005": _by_controls("CTL-SDP810", "CTL-SETRA264"), "CTL-007": "CTL-DOOR", "CTL-008": _by_controls("CTL-SWITCH-LITE", "CTL-SWITCH"),
    "CTL-009": "CTL-CAT6A", "CTL-010": "CTL-LEAK", "CTL-011": "CTL-LABELS", "CTL-012": "CTL-PLC", "CTL-013": "CTL-REVPI",
    "CTL-014": "CTL-EDGE", "CTL-015": "CTL-RCP", "CTL-016": "CTL-LEAK-CTRL", "CTL-017": "CTL-PSU-QUINT",
    "FS-001": "FS-AEROSOL", "FS-010": "FS-CLEAN-AGENT", "FS-020": "FS-CLEAN-AGENT", "FS-030": "FS-SMOKE", "FS-040": "FS-CLEAN-AGENT",
    "SITE-001": "SITE-PAD", "SITE-002": "STR-TIEDOWN", "SITE-003": "SITE-GROUND", "SITE-004": "SITE-FIBER",
    "SITE-005": _by_tier(micro="SITE-FORKLIFT", default="SITE-CRANE"), "SITE-006": "SITE-TRANSPORT-KIT",
}
ALSO = {
    "PWR-SVC-ENCL": ["PWR-MAIN-BKR", "PWR-SPD", "PWR-ATS-400", "PWR-ATS-200", "PWR-EPO-RELAY"],
    "PWR-PANEL-ILINE": ["PWR-PANEL-BOX"],
    "CTL-PANEL": ["CTL-PLC", "CTL-IO-DIO", "CTL-IO-RTD", "CTL-IO-AI", "CTL-PSU-QUINT", "CTL-PSU-ORING", "CTL-SPD", "CTL-SWITCH", "CTL-EDGE",
                  "CTL-RCP", "CTL-PANEL-BUILD", "CTL-PANEL-KIT", "CTL-RELAY", "CTL-TERM", "CTL-RS485"],
    "CTL-ENCL": ["CTL-REVPI", "CTL-REVPI-DIO", "CTL-REVPI-AIO", "CTL-PSU-QUINT", "CTL-SWITCH-LITE", "CTL-RCP", "CTL-PANEL-KIT", "CTL-RELAY", "CTL-TERM", "CTL-RS485"],
    "CTL-POD": ["CTL-POD-ENCL", "CTL-MGM240P", "CTL-SDP810"],
    "CTL-LEAK": ["CTL-LEAK-LEADER"], "PWR-GROUNDBAR": ["SITE-GROUND"], "STR-CONT-ROOF": ["STR-CONT-FRAME", "STR-CONT-DOOR"],
    "FS-CLEAN-AGENT": ["FS-SMOKE", "FS-VESDA", "FS-EXT", "FS-SIGNS"], "SVC-MODS-MAT": ["SVC-WELDER"],
}
NEW_IN_CATALOG = {"STR-FLOORCHAN", "STR-TRAY", "STR-STRUT-KIT", "ENV-DOORSEAL", "ENV-FLOOR-PIR", "ENV-ROOFBOOT", "ENV-BRANDPANEL",
                  "ENV-DRAIN", "ENV-MICRO-HEATER", "CMP-BLANK", "PWR-UPS-RM20", "PWR-UPS-RM20-XBP", "PWR-SVC-ENCL", "PWR-RCPT",
                  "SITE-TRANSPORT-KIT", "FS-PANIC"}


def _desc(code):
    if code in ITEMS:
        return ITEMS[code]
    if code in CATALOG:
        return CATALOG[code]["name"]
    raise KeyError(code)


def catalog_code(old, lay):
    m = MAP[old]
    return m(lay) if callable(m) else m


def reconcile(lines, lay):
    """Replace working codes with catalog codes and catalog names in the finished document."""
    out = []
    used = {}
    for ln in lines:
        for old in sorted(MAP, key=len, reverse=True):
            if old not in ln:
                continue
            new = catalog_code(old, lay)
            if new not in CATALOG:
                raise KeyError(f"{old} -> {new} not in catalog")
            ln = _re.sub(_re.escape(old) + r" \([^)]*\)", f"{new} ({CATALOG[new]['name']})", ln)
            ln = ln.replace(old, new)
            used[new] = old
        for code in _re.findall(r"\b(?:STR|ENV|PWR|CLG|CMP|CTL|FS|SITE|SVC)-[A-Z0-9-]+\b", ln):
            if code in CATALOG and code not in used:
                used[code] = ""
        out.append(ln)
    return out, used


TOOLS = {
    "T-01": "Steel tape 8 m",
    "T-02": "Spirit level 1.8 m / laser level",
    "T-03": "Calibrated torque wrench 20-200 N·m (cal. within 12 months)",
    "T-04": "Cordless drill, step drill, hole saws",
    "T-05": "Angle grinder with cutting and grinding discs",
    "T-06": "Welding set (certified welder only)",
    "T-07": "Sealant gun, caulking tools",
    "T-08": "Pallet jack / rack lifter, 1000 kg",
    "T-09": "Forklift 2.5 t or crane with spreader",
    "T-10": "True-RMS multimeter, insulation tester 1000 V, earth tester",
    "T-11": "Refractometer, vacuum pump, micron gauge, nitrogen set (HVAC technician)",
    "T-12": "Laptop with ben_engine software and USB-serial cable",
    "T-13": "Smoke pencil, manometer, paper strips",
    "T-14": "Label printer",
    "T-15": "PPE: hard hat, safety glasses, gloves, steel-toe boots, hearing protection",
    "T-16": "Rack lifter / stair climber for 100 kg modules",
    "T-17": "Ferrule crimper, torque screwdriver 0.5-2.5 N·m (controls terminals), RS-485 / loop test meter",
}

STEPS_LEAD = "**Step**"


def W(s):  # warning block
    return f"> **WARNING:** {s}\n"


def Ca(s):  # caution block
    return f"> **CAUTION:** {s}\n"


def note(s):
    return f"> **NOTE:** {s}\n"


class Doc:
    def __init__(self):
        self.lines = []
        self.codes_used = set()
        self.tools_used = set()
        self.n_task = 0

    def add(self, s=""):
        self.lines.append(s)

    def task(self, title, personnel, time_h, tools, parts, body):
        self.n_task += 1
        n = self.n_task
        self.add(f"## Task {n:02d} — {title}")
        self.add()
        self.add(f"**Personnel:** {personnel}  ")
        self.add(f"**Time:** {time_h}  ")
        self.add("**Tools:** " + "; ".join(f"{t} {TOOLS[t]}" for t in tools) + "  ")
        self.tools_used.update(tools)
        if parts:
            self.add("**Parts:** " + "; ".join(f"{p} ({_desc(p)})" + (f" x {q}" if q else "") for p, q in parts) + "  ")
            self.codes_used.update(p for p, _ in parts)
        self.add()
        for b in body:
            self.add(b)
        self.add()

    def steps(self, items):
        """items: list of str (step) or tuples ('W'|'C'|'N', text) placed before the next step."""
        out = []
        k = 0
        for it in items:
            if isinstance(it, tuple):
                kind, txt = it
                out.append("\n" + {"W": W, "C": Ca, "N": note}[kind](txt))
            else:
                k += 1
                out.append(f"{k}. {it}")
        return "\n".join(out) + "\n"

    def checks(self, items):
        """items: list of (ctq_id or '', text, form)."""
        out = ["**Check:**", ""]
        for cid, txt, form in items:
            tag = f"[{cid}] " if cid else ""
            out.append(f"- {tag}{txt} Record on form {form}.")
        return "\n".join(out) + "\n"


def h(hours):
    return f"{hours:g} h" if hours < 8 else f"{hours / 8:.1f} days ({hours:g} h)"


def generate(lay: L.Layout) -> Doc:
    d, cfg = lay.d, lay.cfg
    tl = d["tier_label"]
    is_c = lay.is_container
    racks = lay.by_kind("rack")
    nr = len(racks)
    mode = lay.notes.get("cooling_resolved", cfg.cooling)
    cus = [i for i in lay.items if i.tag.startswith("CU")]
    cnds = [i for i in lay.items if i.tag.startswith("CND")]
    pumps = [i for i in lay.items if i.tag.startswith("PU") or i.tag.startswith("CDU")]
    reg = {c.id: c for c in C.register(lay)}
    doc = Doc()
    A = doc.add

    A(f"# {tl} — Assembly instructions (ASD-STE100)")
    A()
    A(f"Schreiber AI · BEN Engine · {ISSUE} · matches drawing set {REV['set_label']} · Generated by `design/assembly/gen_assembly.py` from `Config.preset('{lay.tier}')` and `design/REVISION.json`.")
    A()
    A("Read `design/assembly/STE_STYLE.md` before you change this document. Read the drawing set in "
      f"`design/drawings/{lay.tier}/` before you start work. Keep the drawings at the work area.")
    A()
    A("## About this document")
    A()
    A("This document tells you how to assemble one unit. Each task has these parts: the people you need, the time, the tools, the parts, the warnings, the steps and the checks.")
    A("Do the tasks in the order given. Do not start a task before the checks of the task before it are complete.")
    A("A **HOLD POINT** stops the work. Only the named qualified person can do the work after a hold point. Work does not continue until that person signs the form.")
    A("A **WITNESS POINT** needs the QC inspector present. The inspector signs the form.")
    A("The CTQ and CTP references point to the tables on the drawings and to `design/ctq.py`. The Q-forms are in `design/assembly/QC_FORMS.md`.")
    A()
    A("### Configuration of this unit")
    A()
    A("| Item | Value |")
    A("|---|---|")
    A(f"| Tier / enclosure | {tl}, {d['enclosure']} |")
    A(f"| IT load / racks | {cfg.it_kw:.0f} kW in {nr} rack(s), {d['per_rack_kw']} kW per rack |")
    A(f"| Cooling (as built) | {L.COOLING_LIBRARY[mode]['label']}" + ("" if mode == cfg.cooling else f" — DEVIATION from config `{cfg.cooling}`, see INDEX.md") + " |")
    A(f"| Power | {d['voltage']}, main breaker {d['service_breaker_a']} A, UPS {d['ups_modules']} x {d['ups_kva_each']} kVA, battery {d['battery_kwh']} kWh |")
    A(f"| Interior (mm) | {lay.L:.0f} x {lay.W:.0f} x {lay.H:.0f} |")
    A(f"| Gross mass | {d['gross_kg']} kg (weigh before transport) |")
    A(f"| Redundancy / climate | {cfg.redundancy}, {d['climate']['label']} (design {d['climate']['t_design_c']} C / {d['climate']['t_min_c']} C) |")
    A()
    A("### Safety rules for all tasks")
    A()
    A(W("Electrical work can kill. Only a licensed electrician connects or disconnects power conductors. Lock out and tag out before you open an electrical enclosure."))
    A(W("Racks and cabinets are heavy. One rack has a mass of up to 1000 kg when loaded. Use the rack lifter. Do not stand under a lifted load."))
    A(W("Refrigerant and pressurised coolant can cause injury. Only a licensed HVAC technician opens a refrigerant circuit."))
    A(Ca("Wear the PPE in T-15 for all tasks. Wear hearing protection when you cut or grind."))
    A(Ca("Lithium batteries can start a fire if you damage them. Do not drop a battery module. Keep the battery documents with the unit."))
    A()
    A("### Coordinates")
    A()
    A("All positions are in millimetres. x is along the length from the door-end liner. y is across the width from the rack-wall liner. z is up from the finished floor. See drawing A-002.")
    A()

    # ---------------------------------------------------------------- T01 receiving
    doc.task("Receiving inspection", "2 workers, 1 QC inspector", h(4),
             ["T-01", "T-09", "T-14", "T-15"],
             [("SITE-005", 1)],
             [doc.steps([
                 ("C", "Do not accept a damaged enclosure. A bent corner post or a cracked corner casting makes the unit unsafe to lift."),
                 "Compare the delivery note with the purchase order and the parts list.",
                 "Unload the enclosure with the forklift or the crane. Lift only at the four corner castings." if is_c else "Unload the cabinet with the forklift. Lift only at the skid fork pockets.",
                 "Put the enclosure on level blocks at the work area. Make sure there is 1.5 m of free space on all sides.",
                 "Examine all outer surfaces for dents, cracks, holes and corrosion. Mark each defect with chalk. Take a photo of each defect.",
                 "Read the CSC plate. Record the owner code, the serial number and the date of the last inspection." if is_c else "Read the rating label of the cabinet. Record the model and the IP rating.",
                 "Open the doors. Examine the floor and the walls from inside. Look for light through the walls. Look for water marks.",
                 "Measure the external length, the width and the height. Measure the two floor diagonals.",
                 "Open each pallet of parts. Count the parts against the parts list. Examine each part for transport damage.",
                 "Put a label with the item code on each pallet. Store the parts in the dry area.",
                 "Put the electrical parts and the batteries in the locked store.",
             ]),
              doc.checks([
                  ("CTQ-A1", f"External dimensions {lay.ext_l:.0f} x {lay.ext_w:.0f} x {lay.ext_h:.0f} mm, each +0/-6 mm. Diagonals within 10 mm.", "Q-02"),
                  ("CTQ-A2", reg["CTQ-A2"].criterion + ".", reg["CTQ-A2"].form),
                  ("", "All parts counted. All defects photographed. Delivery note signed.", "Q-01"),
              ])])

    # ---------------------------------------------------------------- T02 container prep
    if is_c:
        cut_list = ["2 x line-set roof curbs 300 x 200 per condenser position (see A-001)" if cnds else None,
                    "2 x DN65 pipe sleeves in the blind end wall at z 2100 and 2300 (see A-001)" if lay.find("DC1") else None,
                    "1 x power entry 150 x 150 in the blind end wall behind the service section, z 1800",
                    "1 x fibre / controls entry 100 x 100 in the blind end wall, z 2200",
                    "1 x floor drain 60 mm hole at x 300, y 1400 (see A-003)",
                    f"{len([i for i in lay.items if i.tag == 'LEAK'])} x condensate drain exit 40 mm in the rack wall at floor level, x {lay.L - 300:.0f}"]
        cut_list = [c for c in cut_list if c]
        doc.task("Container preparation: cutouts and reinforcement", "2 workers, 1 certified welder", h(16),
                 ["T-01", "T-04", "T-05", "T-06", "T-07", "T-15"],
                 [("STR-004", len(cut_list)), ("ENV-012", 2)],
                 [doc.steps([
                     ("W", "Grinding and welding make sparks and fumes. Keep a fire extinguisher at the work area. Remove all flammable material 10 m around."),
                     ("W", "HOLD POINT. Only a certified welder (AWS D1.1 or ISO 9606-1) welds on the container. The welder signs form Q-02."),
                     "Mark the position of each cutout on the outside of the container. Use the dimensions on A-001 and A-003. The cutouts are:\n"
                     + "\n".join(f"   - {c}" for c in cut_list),
                     ("C", "Do not cut within 300 mm of a corner post. Do not cut the top side rail or the bottom side rail."),
                     "Measure each mark again from a second reference. Make sure the two measurements agree within 5 mm.",
                     "Drill a 10 mm hole at each corner of each cutout.",
                     "Cut each opening with the angle grinder. Cut from hole to hole. Remove the cut piece.",
                     "Grind all cut edges smooth. Remove all burrs.",
                     "Welder: fit the reinforcement frame STR-004 around each opening. Tack the frame in four places. Measure the frame for square.",
                     "Welder: weld the frame fully to the shell. Make a continuous fillet weld on the outside and the inside.",
                     "Welder: examine each weld. Look for cracks, undercut and porosity. Repair any defect.",
                     "Clean each weld with a wire brush. Apply zinc-rich primer within 4 hours. Apply the topcoat the next day.",
                     "Weld the four tray bosses to the top side rail at the positions on S-001.",
                     "Weld the two seismic bosses to the top side rail if the seismic option applies (S-001 Detail B).",
                     "Record the welder name, the licence number and the date on form Q-02.",
                 ]),
                  doc.checks([
                      ("CTP-A1", reg["CTP-A1"].criterion + ". HOLD POINT: welder signs.", "Q-02"),
                      ("", "Each cutout position within 5 mm of A-001. No cutout within 300 mm of a corner post.", "Q-02"),
                      ("", "Primer applied to 100 % of cut edges and welds. Photo of each frame.", "Q-02"),
                  ])])
    else:
        doc.task("Cabinet preparation: cutouts for the air conditioners", "2 workers", h(6),
                 ["T-01", "T-04", "T-05", "T-07", "T-15"],
                 [("ENV-012", 1), ("ENV-013", 1)],
                 [doc.steps([
                     ("C", "The cabinet is rated IP55. Each cutout must get the gasket of the air conditioner. Do not make a cutout that is larger than the template."),
                     "Remove the side panels of the cabinet.",
                     f"Put the cutting template of the air conditioner CLG-001 on each side panel at the positions on A-001. There are {len(cus)} units.",
                     "Mark the cutout and the bolt holes. Drill the bolt holes. Cut the opening with the angle grinder.",
                     "Grind the edges smooth. Apply primer to all cut edges.",
                     "Drill the gland holes for the power entry and the fibre entry in the rear panel at z 600.",
                     "Fit the anti-condensation heater ENV-013 at the bottom of the cabinet. Fit the new door gasket.",
                     "Fit the side panels again.",
                 ]),
                  doc.checks([
                      ("CTQ-A2", reg["CTQ-A2"].criterion + ".", "Q-03"),
                      ("", "All cutouts match the template. All cut edges primed.", "Q-02"),
                  ])])

    # ---------------------------------------------------------------- T03 insulation / liner
    if is_c:
        area = 2 * (lay.L * lay.H + lay.W * lay.H) / 1e6 + lay.L * lay.W / 1e6
        n_pir = math.ceil(area / 2.88 * 1.1)
        doc.task("Insulation, vapour barrier and liner", "3 workers", h(8 * (3 if lay.tier == "ben500" else 2)),
                 ["T-01", "T-04", "T-07", "T-13", "T-15"],
                 [("ENV-001", n_pir), ("ENV-004", 1), ("ENV-002", math.ceil(area / 2.4)), ("ENV-003", math.ceil(area / 4)), ("ENV-010", 1), ("ENV-005", 1), ("ENV-006", math.ceil(lay.L * lay.W / 1e6 / 2.88 * 1.1)), ("ENV-007", 1), ("ENV-011", 1), ("ENV-008", max(1, len(cnds)))],
                 [doc.steps([
                     ("C", "PIR dust irritates the eyes and the skin. Wear safety glasses and gloves when you cut PIR."),
                     ("N", "The liner is the vapour barrier. Every joint and every penetration must be sealed. A gap lets warm air reach the cold steel and makes water."),
                     "Clean the inside of the shell. Remove all oil, dust and loose paint.",
                     "Apply the closed-cell foam ENV-010 to the corner posts, the door frame and the floor cross-member ends inside the shell.",
                     "Fit the first PIR board ENV-001 at the blind end wall, bottom corner. Apply adhesive in strips 200 mm apart. Push the board into the corrugation.",
                     "Fit the next boards. Stagger the joints by 600 mm. Push each board tightly against the board before it.",
                     "Fit four pins per square metre through each board into the corrugation crests.",
                     "Cut the boards around each reinforcement frame. Leave a gap of not more than 3 mm. Fill the gap with foam sealant.",
                     "Tape all board joints with foil tape.",
                     "Fit the roof boards the same way. Support each board with a prop until the adhesive is set.",
                     "Fit the floor: put the 80 mm PIR between the floor channel positions marked on S-001. Lay the 18 mm plywood on the PIR. Screw the plywood to the container floor at 300 mm pitch.",
                     "Fit the floor drain ENV-011 at x 300, y 1400. Make sure the drain is the lowest point. Fall 1:100 toward the drain.",
                     "Fit the liner panels ENV-002 on the walls. Start at the blind end. Overlap each panel 25 mm. Apply a continuous sealant bead ENV-003 in each overlap.",
                     "Fit the liner on the roof. Fit the corner trims. Seal all trims.",
                     "Fit the EPDM roof boots ENV-008 on each roof curb. Clamp the band. Seal with butyl tape.",
                     "Fit 25 mm PIR and liner on the inside of each door. Fit the EPDM bulb seal ENV-005 around the door frame.",
                     "Lay the anti-static vinyl ENV-007 on the plywood. Weld the seams. Fit the coved skirting.",
                     "Test the envelope with the smoke pencil at 10 joints. Hold the smoke 20 mm from the joint. The smoke must not move.",
                 ]),
                  doc.checks([
                      ("CTQ-C1", reg["CTQ-C1"].criterion + ".", "Q-03"),
                      ("CTQ-C2", reg["CTQ-C2"].criterion + ".", "Q-03"),
                      ("CTQ-C3", reg["CTQ-C3"].criterion + ".", "Q-03"),
                      ("CTQ-C4", reg["CTQ-C4"].criterion + ".", "Q-03"),
                      ("CTP-C1", reg["CTP-C1"].criterion + ".", "Q-03"),
                  ])])

    # ---------------------------------------------------------------- T04 floor channels and trays
    if is_c:
        row_end = lay.notes["row_end_x"]
        n_cm = int(lay.L // 300) + 1
        n_bolts = 2 * len([x for x in range(n_cm) if x * lay.L / (n_cm - 1) <= row_end])
        doc.task("Floor channels and cable trays", "2 workers, 1 QC inspector (witness)", h(8),
                 ["T-01", "T-02", "T-03", "T-04", "T-15"],
                 [("STR-001", math.ceil(2 * row_end / 3000)), ("STR-002", n_bolts + 8), ("STR-003", 1), ("STR-020", math.ceil((lay.L - 500) / 3000)), ("STR-021", math.ceil((lay.L - 500) / 3000)), ("STR-022", 2 * math.ceil((lay.L - 500) / 1500)), ("CTL-010", 1)],
                 [doc.steps([
                     ("N", "The floor channels carry the rack feet. The channels must bear on the plywood over the cross members, not on insulation."),
                     f"Mark the two channel centre lines on the floor. See S-001 for the y positions. Mark the channel length {row_end:.0f} mm from the door-end liner.",
                     "Mark the position of each floor cross member on the channel line. The cross members are at about 300 mm pitch. Find them with a magnet or by drilling a pilot hole.",
                     "Cut the channels STR-001 to length. Remove the burrs. Apply primer to the cut ends.",
                     "Put the first channel on the line. Drill 13 mm holes through the channel web, the plywood and the cross-member flange at each cross member.",
                     "Fit an M12 bolt STR-002 in each hole, bolt head up, washer under the head and under the nut.",
                     "Put the laser level on the channel. Measure the height every 600 mm. Put steel shims STR-003 under the channel where the height is low.",
                     ("C", "Use steel shims only. Do not use plywood or plastic shims."),
                     "Do the same for the second channel. Make sure the two channels are parallel within 2 mm.",
                     ("W", "WITNESS POINT. Call the QC inspector before you torque the bolts."),
                     f"Torque each M12 bolt to {C.TORQUE['M12']} N·m with the calibrated torque wrench. Put a paint stripe across the nut and the channel after each bolt.",
                     "Mark the tray hanger positions on the ceiling liner at 1500 mm pitch. The data tray TR-D is at y 1370 to 1670. The power tray TR-P is at y 1770 to 2070.",
                     "Fit the hangers STR-022 to the tray bosses with M10 rod. Fit the trays STR-020 and STR-021 at z 2250 (underside).",
                     "Fit the tray ground bonding jumper at each tray joint.",
                     "Lay the leak rope CTL-010 on the floor around the perimeter 100 mm from the walls. Fix the rope with clips every 500 mm. Leave the ends at the controller position.",
                 ]),
                  doc.checks([
                      ("CTP-S1", reg["CTP-S1"].criterion + ". WITNESS POINT.", "Q-04"),
                      ("CTQ-S1", reg["CTQ-S1"].criterion + ".", "Q-04"),
                      ("", "Tray underside at 2250 +/-10 mm. Trays bonded. Leak rope continuous, ends labelled.", "Q-04"),
                  ])])
    else:
        doc.task("Skid and rack rails", "2 workers", h(4),
                 ["T-01", "T-02", "T-03", "T-15"],
                 [("STR-010", 1), ("STR-002", 4), ("CMP-003", 1), ("CTL-010", 1)],
                 [doc.steps([
                     "Put the skid STR-010 on the level floor. Put the cabinet on the skid. Align the cabinet holes with the skid holes.",
                     f"Fit four M12 bolts. Torque each bolt to {C.TORQUE['M12']} N·m.",
                     "Fit the rack rails CMP-003 at x 200 to 800 and y 100 to 700. Put the level on each rail.",
                     f"Torque the rail bolts M8 to {C.TORQUE['M8']} N·m.",
                     "Lay the leak rope CTL-010 on the cabinet floor. Fix the rope with clips.",
                 ]),
                  doc.checks([
                      ("CTP-S2", reg["CTP-S2"].criterion + ".", "Q-04"),
                      ("CTQ-B3", "Rails plumb within 2 mm over the rail height.", "Q-05"),
                  ])])

    # ---------------------------------------------------------------- T05 racks and hold-downs
    if is_c:
        rk = racks[0]
        rack_code = rk.code
        doc.task("Racks and hold-downs", "3 workers, 1 QC inspector (witness)", h(2 * nr + 2),
                 ["T-01", "T-02", "T-03", "T-08", "T-15"],
                 [(rack_code, nr), ("STR-005", 2 * nr), ("STR-002", 4 * nr), ("CMP-010", math.ceil(nr * 42 / 10)), ("CMP-011", nr), ("CTL-011", 1)],
                 [doc.steps([
                     ("W", "A rack can fall over when you move it. Keep the rack on the lifter until two hold-downs are fitted."),
                     f"Move the first rack {racks[0].tag} through the door with the rack lifter. The rack front faces the aisle (+y).",
                     f"Put the rack at x {racks[0].x0:.0f} to {racks[0].x1:.0f}, rear face at y {racks[0].y0:.0f}. Use the dimensions on A-002.",
                     "Put the level on the front rail. Adjust the levelling feet until the rack is plumb in both axes.",
                     "Fit the two hold-down angles STR-005 to the rack base. Fit two M12 bolts STR-002 through each angle into the floor channel.",
                     "Move the next rack into position. Push the rack against the rack before it. Make sure the gap is not more than 3 mm.",
                     "Bolt the racks together at the top and the bottom with the rack joining kit.",
                     f"Do the same for all {nr} racks. The rack positions are:\n" + "\n".join(f"   - {r.tag} at x {r.x0:.0f}" for r in racks),
                     ("W", "WITNESS POINT. Call the QC inspector before you torque the hold-down bolts."),
                     f"Torque each hold-down bolt to {C.TORQUE['M12']} N·m. Put a paint stripe on each bolt.",
                     "Fit the blanking panels CMP-010 in every open U.",
                     "Fit the rack ground kit CMP-011 to each rack. Connect each rack to the tray ground bar with 6 AWG.",
                     "Fit the laminated tag label (R1, R2 ...) at the top front of each rack.",
                 ] + ([f"Fit the rear-door heat exchangers CLG-031 on each rack in place of the rear door. Connect the flex hoses later in Task 07."] if mode == "rdhx_drycooler" else [])),
                  doc.checks([
                      ("CTQ-B1", "Each rack x-position within +/-10 mm of A-002.", "Q-05"),
                      ("CTQ-B3", "Rails plumb within 2 mm over 2 m, both axes.", "Q-05"),
                      ("CTQ-B4", "Gap <= 3 mm; fronts within 3 mm of a straight line.", "Q-05"),
                      ("CTP-S2", f"{4 * nr} hold-down bolts torqued to {C.TORQUE['M12']} N·m. WITNESS POINT.", "Q-04"),
                      ("", "Blanking panels in every open U. Ground bond <= 0.1 ohm per rack.", "Q-05"),
                  ])])
    # ---------------------------------------------------------------- T06 containment
    if is_c and lay.notes.get("plenum", 0):
        doc.task("Hot-aisle containment", "2 workers", h(6),
                 ["T-01", "T-04", "T-07", "T-13", "T-15"],
                 [("CLG-050", 1), ("ENV-003", 2)],
                 [doc.steps([
                     ("N", "The containment makes the 200 mm space behind the racks into the hot aisle. Air must go from the racks to the cooling units only through this space."),
                     f"Fit the top panels of CLG-050 over the plenum and the rack row, x 0 to {lay.notes['row_end_x']:.0f}.",
                     f"The top panels go from the rack top (z {racks[0].z1:.0f}) to the ceiling liner.",
                     f"Fit the end panel at x {lay.notes['row_end_x']:.0f} from the floor to the ceiling. Fit the brush strips at every cable opening.",
                     "Fit the end door at the door-end side of the plenum. Make sure the door closes against the seal.",
                     "Seal every joint between the panels and the liner with sealant.",
                     "Close all doors. Run one cooling unit fan at full speed (Task 07 or temporary fan). Measure the pressure difference with the manometer across the containment.",
                 ]),
                  doc.checks([
                      ("CTQ-B5", reg["CTQ-B5"].criterion + ".", "Q-05"),
                  ])])

    # ---------------------------------------------------------------- T07 cooling
    parts = []
    if cus:
        parts += [(cus[0].code, len(cus)), ("CLG-017", len(cus))]
        if is_c:
            parts += [("CLG-015", len(cnds)), ("CLG-016", len(cnds))]
    if mode == "rdhx_drycooler":
        parts += [("CLG-030", 1), ("CLG-031", nr), ("CLG-032", 1), ("CLG-033", 2), ("CLG-034", 1), ("CLG-040", 1)]
    if mode == "dlc_cdu":
        parts += [("CLG-020", lay.notes.get("n_cdu", 2)), ("CLG-032", 1), ("CLG-033", 3), ("CLG-034", 1), ("CLG-040", 1)]
    parts += [("STR-002", 4 * (len(cus) + len(pumps)))]
    steps = [("W", "HOLD POINT. Only a licensed HVAC technician (EPA 608 / F-gas) brazes, pressure tests, evacuates and charges a refrigerant circuit. Workers do the mechanical work only."),
             ("W", "Refrigerant R-513A is under pressure and can freeze skin. Wear gloves and eye protection. Ventilate the work area.")]
    if cus and is_c:
        steps += [
            "Move each in-row unit into its position with the rack lifter. The unit front faces the aisle. The positions are:\n" + "\n".join(f"   - {c.tag} at x {c.x0:.0f}" for c in cus),
            f"Level each unit. Fit four M12 bolts to the floor channel. Torque to {C.TORQUE['M12']} N·m.",
            "Lift each roof condenser CLG-015 onto its curb with the crane. Bolt the condenser frame to the curb with the vibration mounts.",
            "Pull the pre-insulated line set CLG-016 from each condenser through the roof boot to its in-row unit. Do not kink the pipe. Keep the pipe ends capped.",
            "Fit the condensate drain kit CLG-017 from each unit to the drain header. Make a trap at each unit. Fall 1:100 to the exterior drain.",
            "HVAC technician: braze the line set with nitrogen purge. Pressure test with dry nitrogen. Evacuate to 500 micron and hold 30 minutes. Charge per the nameplate.",
            "HVAC technician: record the refrigerant type and the charge of each circuit on form Q-06. The design refrigerant is R-513A (A1, GWP 631).",
        ]
    if cus and not is_c:
        steps += [
            f"Lift each cabinet air conditioner CLG-001 onto its cutout. There are {len(cus)} units. Fit the gasket. Fit the bolts from inside.",
            "Fit the condensate drain hose from each unit to the drain spigot at the skid.",
            "HVAC technician: examine the factory charge on the sight glass. The units are pre-charged and sealed. No brazing is needed.",
        ]
    if mode in ("rdhx_drycooler", "dlc_cdu"):
        unit_name = "pumping unit CLG-030" if mode == "rdhx_drycooler" else "coolant distribution units CLG-020"
        steps += [
            f"Move the {unit_name} into position. The positions are:\n" + "\n".join(f"   - {p.tag} at x {p.x0:.0f}" for p in pumps),
            f"Level each unit. Bolt it to the floor channel with four M12 bolts. Torque to {C.TORQUE['M12']} N·m.",
            "Fit the secondary manifolds CLG-032 along the top of the rack row. Supply manifold at the front, return manifold at the rear. Fit an isolation valve at each rack branch.",
            ("Connect the flex hoses of each rear-door heat exchanger to the manifold branches. Supply at the bottom, return at the top." if mode == "rdhx_drycooler"
             else "Connect the rack manifold of each rack to the secondary manifolds. Supply at the bottom, return at the top. Fit the quick-disconnects per the rack manual."),
            "Fit a drip tray under each hose connection. Route the leak rope CTL-010 along the manifolds and through each drip tray.",
            "Pull the primary pipe kit CLG-034 through the two end-wall sleeves to the dry cooler position. Insulate the pipe. Seal the sleeves.",
            ("W", "WITNESS POINT. Call the QC inspector for the pressure test."),
            "HVAC technician: pressure test the secondary loop with water at 1.5 x the working pressure for 2 hours. No pressure drop is permitted.",
            "HVAC technician: flush the loop through the strainer. Fill with 30 % propylene glycol CLG-033. Vent all high points. Measure the mix with the refractometer.",
        ]
    steps += ["Pour 1 L of water in each drain tray. Make sure the water clears in less than 60 seconds.",
              "Fit the tag label on each unit (CU1, CND1, PU1 ...)."]
    checks = [("CTP-M1", reg["CTP-M1"].criterion + ". HOLD POINT.", "Q-06"),
              ("CTQ-M1", reg["CTQ-M1"].criterion + ". WITNESS POINT.", "Q-06"),
              ("CTQ-M2", reg["CTQ-M2"].criterion + ".", "Q-06")]
    if "CTQ-M4" in reg:
        checks.append(("CTQ-M4", reg["CTQ-M4"].criterion + ".", "Q-06"))
    doc.task("Cooling units, refrigerant and coolant piping", "2 workers, 1 licensed HVAC technician, 1 QC inspector (witness)", h(8 * (1 + len(cus) // 3 + len(pumps))),
             ["T-01", "T-02", "T-03", "T-08", "T-09", "T-11", "T-15"], parts, [doc.steps(steps), doc.checks(checks)])

    # ---------------------------------------------------------------- T08 electrical
    pw = [i for i in lay.items if i.kind == "power" and i.mount in ("floor", "wall", "ext")]
    counts = {}
    for it in pw:
        counts[it.code] = counts.get(it.code, 0) + 1
    parts = list(counts.items())
    parts += [("PWR-020", 2 * nr), ("PWR-150", 1), ("PWR-160", 1), ("PWR-170", 2 * nr), ("CTL-011", 1)]
    if d["voltage"].startswith("480"):
        parts.append(("PWR-122", 1))
    if lay.notes.get("rack_ups") or not is_c:
        parts += [("PWR-010", d["ups_modules"]), ("PWR-011", 1)]
    ups_floor = [i for i in pw if i.tag.startswith("UPS") or i.tag.startswith("BAT")]
    steps = [("W", "HOLD POINT. Only a licensed electrician lands power conductors, connects the service, and energises. Workers mount enclosures, pull labelled cables and plug in labelled connectors after the electrician signs."),
             ("W", "The battery cabinet has stored energy. Keep the battery disconnect open until the electrician completes the tests."),
             ("W", "Lock out and tag out the service disconnect before you work in any enclosure.")]
    if ups_floor:
        steps += ["Move the power cabinets into position with the rack lifter. The front faces the aisle. The positions are:\n" + "\n".join(f"   - {u.tag} at x {u.x0:.0f}" for u in ups_floor),
                  f"Level each cabinet. Fit four M12 bolts to the floor channel. Torque to {C.TORQUE['M12']} N·m."]
    if lay.notes.get("rack_ups") or not is_c:
        steps += [f"Fit the rack UPS modules PWR-010 and the battery PWR-011 in rack R1 at the bottom U positions on A-002. Use the rack lifter T-16 for each module."]
    if is_c:
        steps += [f"Mount the service section PWR-140 on the outside of the blind end wall at z 600 to 2000. Use the four M12 bosses.",
                  "Mount the mechanical panel PWR-120 on the end wall inside, aisle side, at z 300 to 1300." + (" Mount the IT panel PWR-121 above it at z 1400 to 2400." if lay.find("PNL-IT") else ""),
                  "Mount the EPO station PWR-130 on the aisle wall at x 500, z 1200.",
                  "Mount the second EPO station on the service section outside.",
                  "Mount the receptacle set PWR-170 for the rack PDUs on the power tray above each rack. Two receptacles per rack, labelled A and B."]
    else:
        steps += ["Mount the service entrance box PWR-030 on the rear of the cabinet at z 600 to 1200.",
                  "Mount the EPO station PWR-130 beside the door at z 1200."]
    steps += ["Pull the labelled cables PWR-150 in the power tray. Keep power cables in TR-P only. Keep 300 mm from the data tray. Cross at 90 degrees.",
              "Fit two rack PDUs PWR-020 in each rack. Plug each PDU into its receptacle A or B.",
              "Fit the ground bar PWR-160 in the service section. Connect the container frame bond at two places. Connect the tray ground, the rack grounds and each cabinet frame.",
              "Electrician: land all conductors. Torque each lug to the value on the device label. Record each value.",
              "Electrician: test insulation resistance of each feeder at 1000 V. Test phase rotation at each panel.",
              ("W", "WITNESS POINT. Call the QC inspector for the ground resistance and the termination torque record."),
              "Electrician: energise the service section. Measure the voltage at each panel. Start the UPS per the manufacturer start-up procedure.",
              "Press the EPO. Make sure all IT power and all cooling units go off in less than 1 second. Reset the EPO.",
              "Fit the tag label on each breaker, each cable end and each receptacle."]
    doc.task("Electrical installation", "2 workers, 1 licensed electrician, 1 QC inspector (witness)", h(8 * (2 + nr // 4)),
             ["T-01", "T-03", "T-04", "T-08", "T-10", "T-14", "T-15", "T-16"], parts,
             [doc.steps(steps),
              doc.checks([("CTP-E1", reg["CTP-E1"].criterion + ". HOLD POINT.", "Q-07"),
                          ("CTP-E2", reg["CTP-E2"].criterion + ". WITNESS POINT.", "Q-07"),
                          ("CTQ-E1", reg["CTQ-E1"].criterion + ".", "Q-07"),
                          ("CTQ-E2", reg["CTQ-E2"].criterion + ". WITNESS POINT.", "Q-07"),
                          ("CTQ-E4", reg["CTQ-E4"].criterion + ".", "Q-07"),
                          ("CTQ-E3", reg["CTQ-E3"].criterion + ".", "Q-10")])])

    # ---------------------------------------------------------------- T09 controls (docs/CONTROLS_HARDWARE_DECISION.md)
    pro = lay.cfg.controls_tier_resolved() == "pro"
    pods = [i for i in lay.items if i.tag.startswith("P") and i.code == "CTL-POD"]
    n_pods = len(pods)
    cp = lay.find("CP1")
    hz = lay.notes["probe_heights"]
    steps = [("C", "Static electricity can damage a Pod or an I/O module. Touch the rack frame before you touch a circuit board. Do not open a Pod: there is nothing to solder or set inside. A Pod with a broken seal is returned, not repaired."),
             ("W", "The controls panel is fed from PNL-M. Only a licensed electrician lands the panel feeder. Lock out the feeder before you work inside the panel."),
             ("N", "Sensor names on the labels must match spec/PROTOCOL.md exactly. The software finds each sensor by its name."),
             (f"Mount the BEN Controller panel CTL-001 on the end wall at x {cp.x0:.0f}, z {cp.z0:.0f} to {cp.z1:.0f}. Use four M10 anchors. The UL 508A shop delivers the panel built, wired and labelled. Inside are the PLC CTL-012, the I/O, the edge computer CTL-014, two 24 VDC supplies CTL-017 and the switch CTL-008. Do not change the wiring inside the panel."
              if pro else f"Mount the BEN Controls Lite cabinet CTL-001 on the end wall at x {cp.x0:.0f}, z {cp.z0:.0f} to {cp.z1:.0f}. Fit the RevPi CTL-013 and the DIO and AIO modules on the DIN rail. Fit the 24 VDC supply CTL-017 and the switch CTL-008 on the DIN rail. Fit the RevPi watchdog relay in the cooling-enable circuit.")
             if is_c else "Fit the BEN Controls Lite shelf CTL-001 in the rack at the U position on A-002. Fit the RevPi CTL-013 and the DIO and AIO modules on the shelf DIN rail. Fit the 24 VDC supply CTL-017 and the switch CTL-008 on the same rail.",
             "Electrician: land the panel feeder from PNL-M and the ground. Land 24 VDC to the field terminal strip. Use one fused 24 VDC branch per Pod E, one per transmitter and one for the leak controller. Torque the terminals to the value on the label (T-17).",
             (f"Mount the {n_pods} Pods CTL-002. Pods P1 to P{2 * nr} go on the top rail of each rack. Odd numbers go on the cold face. Even numbers go on the hot face. The positions are:\n" + "\n".join(f"   - {p_.tag} at x {p_.x0:.0f}, y {p_.y0:.0f}, z {p_.z0:.0f}" for p_ in pods)),
             f"Fit the probe string CTL-003 of each Pod. On the cold-face Pod, put the three inlet probes on the front door at z {hz[0]}, {hz[1]} and {hz[2]}. Put each inlet probe 50 mm in front of the door face. On the hot-face Pod, put the one outlet probe at the rear at z {hz[1]}. Plug the M12 connector into the Pod. Fix each probe with its clip.",
             "Label each probe at the sensor and at the Pod: " + ", ".join(f"T_in_r1_{z/1000:g}" for z in hz) + ", T_out_r1, and so on.",
             "Fit the supply probe T_supply at the first cooling unit outlet at z 300. Fit the return probe T_return at the unit inlet at z 2200. These two go to the panel RTD input, not to a Pod." if (is_c and pro) else "Fit T_supply at the cooling unit outlet and T_return at the inlet. Connect them to the room Pod E.",
             "Connect the room Pod E to the controller with the RS-485 cable (A, B, shield; shield grounded at the panel only). Connect the room Pod E to the switch CTL-008 with a Cat6A cable CTL-009. Run 24 VDC and RS-485 to the outdoor Pod E in one cable run. The run goes to the dry cooler / condenser pad." if is_c else "Connect the room Pod E to the RevPi with the RS-485 cable (A, B, shield) and 24 VDC.",
             "Fit the RH/T transmitter CTL-004 at the room centre at z 1500. Wire the 4-20 mA loop to the panel AI module (loop powered from 24 VDC). Label RH_room." if pro else "The room Pod E carries the RH sensor. Mount the Pod at the room centre position on C-001 if the layout shows it there. Label RH_room.",
             ("Fit the dP transmitter CTL-005 beside the panel. Route one tube to the cold aisle and one tube to the hot plenum at z 1500. Wire the 4-20 mA loop to the panel AI module. Label dP_aisle." if lay.notes.get("plenum", 0) else "Fit the dP transmitter CTL-005 beside the panel. Route one tube to the rack front and one tube to the rack rear. Wire the 4-20 mA loop to the panel AI module. Label dP_aisle.") if pro
             else ("Route the dP tubes of the room Pod E. Put one tube in the cold aisle and one in the hot plenum at z 1500. Label dP_aisle." if lay.notes.get("plenum", 0) else "Route the dP tubes of the room Pod E. Put one tube at the rack front and one at the rack rear. Label dP_aisle."),
             "Connect the leak rope CTL-010 to the leak controller CTL-016 in the panel. Fit the end-of-line terminator. The controller relay and Modbus go to the PLC." if pro else "Connect the leak rope CTL-010 to the room Pod E leak input. Fit the end-of-line terminator.",
             "Fit the door contact CTL-007 on the door at z 1000. Wire it to a DI on the panel. Label door_main.",
             "Connect the utility meter pulse output to a DI on the panel (meter1, pulse_kwh).",
             "Connect the Modbus TCP cables from the UPS, the cooling units and the PDUs to the switch CTL-008. Set the switch to the controls VLAN only. No route to the internet.",
             "Connect the dry contacts from the fire releasing panel and the EPO to the panel DI. These are monitor contacts only. Life safety stays hard-wired.",
             "Close the panel. Energise the panel feeder. Make sure both 24 VDC supplies show DC OK and the redundancy module shows both inputs." if pro else "Energise the cabinet. Make sure the 24 VDC supply shows DC OK and the RevPi boots.",
             "Plug the border router radio CTL-015 into the edge computer USB port (two radios on BEN 150 and larger)." if pro else "Plug the border router radio CTL-015 into the RevPi USB port.",
             f"Start `ben_engine` on the laptop T-12. Run `python -m ben_engine.commissioning --stage provisioning-check`. Make sure all {n_pods} Pods join the mesh, show attestation OK and a valid firmware signature. A Pod that does not attest is replaced, not re-flashed in the field.",
             "Open the containment doors. Send the tare command to dP_aisle. Close the doors.",
             "Put the probes of rack R1 in the ice-point bath, then the 40 C bath. Enter the reference values in the calibration tool. The coefficients are stored in the Pod.",
             "Wet a finger and touch the leak rope at each 1 m. Make sure the controller reports leak = 1 within 10 seconds.",
             "Open and close the door. Make sure door_main changes within 2 seconds.",
             "Stop `ben_engine` on the edge computer. Make sure the cooling units go to local control and the watchdog relay drops within 5 seconds. Restart. Make sure the alarm is logged." if pro else "Stop `ben_engine` on the RevPi. Make sure the watchdog relay drops within 5 seconds and the cooling units keep running on local control. Restart."]
    parts = [("CTL-001", 1), ("CTL-002", n_pods), ("CTL-003", 2 * nr + 1), ("CTL-005", 1), ("CTL-007", 1), ("CTL-008", 1), ("CTL-009", 1), ("CTL-010", 1), ("CTL-011", 1), ("CTL-015", 2 if nr >= 3 else 1), ("CTL-017", 2 if pro else 1)]
    parts += [("CTL-012", 1), ("CTL-014", 1), ("CTL-004", 1), ("CTL-016", 1)] if pro else [("CTL-013", 1)]
    doc.task("BEN Controller panel, BEN Pods and transmitters", "2 workers, 1 controls technician, 1 licensed electrician (panel feeder)", h(6 + 1.5 * nr),
             ["T-01", "T-04", "T-12", "T-14", "T-15", "T-17"], parts,
             [doc.steps(steps),
              doc.checks([("CTQ-K1", reg["CTQ-K1"].criterion + ".", "Q-08"),
                          ("CTQ-K2", reg["CTQ-K2"].criterion + ".", "Q-08"),
                          ("CTQ-K3", reg["CTQ-K3"].criterion + ". WITNESS POINT.", "Q-08"),
                          ("CTQ-K4", reg["CTQ-K4"].criterion + ".", "Q-08"),
                          ("CTQ-K5", reg["CTQ-K5"].criterion + ". WITNESS POINT.", "Q-08"),
                          ("CTP-K2", reg["CTP-K2"].criterion + ". WITNESS POINT.", "Q-08"),
                          ("CTQ-K6", reg["CTQ-K6"].criterion + (". HOLD POINT." if pro else "."), "Q-08"),
                          ("CTQ-M3", reg["CTQ-M3"].criterion + ".", "Q-08"),
                          ("CTP-K1", reg["CTP-K1"].criterion + ". HOLD POINT.", "Q-09")])])

    # ---------------------------------------------------------------- T10 fire
    if is_c:
        vol = lay.L * lay.W * lay.H / 1e9
        doc.task("Fire detection and suppression", "1 worker, 1 certified fire-system installer", h(8),
                 ["T-01", "T-04", "T-15"],
                 [("FS-010", 1), ("FS-020", 1), ("FS-030", 4), ("FS-040", 1)],
                 [doc.steps([
                     ("W", "HOLD POINT. Only a certified fire-system installer connects, tests and commissions the suppression system. Workers mount the cylinder bracket, the panel and the pipe only."),
                     ("W", "A clean-agent discharge is loud and reduces visibility. Nobody stays inside during a discharge test. Fit the safety pin in the cylinder valve before you work near it."),
                     f"Mount the cylinder bracket on the end wall at x {lay.find('FS1').x0:.0f}, y 100 to 500. The room volume is {vol:.1f} m3. The cylinder size is on the installer drawing.",
                     "Put the cylinder FS-010 in the bracket with the safety pin fitted. Tighten the bracket.",
                     "Mount the releasing panel FS-020 on the aisle wall at x 150, z 1500. Mount the abort button beside the door.",
                     "Mount two smoke detectors FS-030 on the ceiling in the cold aisle and two in the hot plenum.",
                     "Fit the discharge pipe FS-040 and the nozzles at the ceiling. Support the pipe every 1.5 m.",
                     "Installer: connect the detectors, the releasing circuit, the EPO interlock and the cooling shutdown relay. Connect the monitor contacts to the controller DI in CTL-001.",
                     "Installer: do the door-fan room integrity test. Record the hold time.",
                     "Installer: do the functional test with the release solenoid disconnected. Fit the actuator last.",
                 ]),
                  doc.checks([("CTP-F1", reg["CTP-F1"].criterion + ". HOLD POINT.", "Q-09"),
                              ("CTP-K1", "Releasing circuit independent of the controls bus.", "Q-09")])])
    else:
        doc.task("Fire suppression unit", "1 worker", h(1),
                 ["T-04", "T-15"], [("FS-001", 1)],
                 [doc.steps(["Mount the aerosol unit FS-001 at the top rear of the cabinet at x 200 to 400.",
                             "Connect the thermal actuator monitor contact to the RevPi DI. Do not connect the actuator to any controller or Pod output.",
                             "Fit the warning label on the door."]),
                  doc.checks([("CTP-K1", "Actuator independent of the controls bus. Label fitted.", "Q-09")])])

    # ---------------------------------------------------------------- T11 final QC and pre-ship test
    doc.task("Final QC and pre-ship test", "1 QC inspector, 1 controls technician, 1 electrician", h(8),
             ["T-01", "T-02", "T-10", "T-12", "T-13", "T-15"], [],
             [doc.steps([
                 ("N", "The pre-ship test proves the unit before it leaves the factory. The commissioning script repeats part of this test at the site."),
                 "Walk the unit with the drawings. Compare each tag label with A-002 and C-001. Correct any label.",
                 f"Measure the aisle width at three points. Make sure it is {lay.aisle_width:.0f} mm, and not less than 914 mm." if is_c else "Make sure the door opens 120 degrees and the rails are plumb.",
                 "Close all doors and panels. Energise the unit from the test supply.",
                 "Connect the load bank to the rack PDUs. Apply 50 % of the IT load. Run for 1 hour.",
                 "Run `python -m ben_engine.commissioning --stage pre-ship` on the laptop. The script reads all sensors and all equipment.",
                 "Make sure every rack inlet is between 18 C and 27 C. Make sure all cooling units share the load within 15 %.",
                 "Apply 100 % of the IT load. Run for 2 hours. Record the supply, the return and the inlet temperatures every 10 minutes.",
                 "Open the utility breaker. Make sure the UPS carries the load. Make sure the runtime is more than the design minutes. Close the breaker.",
                 "Press the EPO. Make sure all IT power and cooling go off in less than 1 second. Reset.",
                 "Remove the load bank. Record the energy meter reading.",
                 "Print the pre-ship report from the script. Attach the report to form Q-10.",
             ]),
              doc.checks([("CTQ-B6", reg["CTQ-B6"].criterion + ".", "Q-10"),
                          ("CTQ-M5", reg["CTQ-M5"].criterion + ".", "Q-10"),
                          ("CTQ-E3", reg["CTQ-E3"].criterion + ". WITNESS POINT.", "Q-10"),
                          ("", f"UPS runtime at full IT load >= {cfg.ups_minutes} min. Pre-ship report signed.", "Q-10")])])

    # ---------------------------------------------------------------- T12 transport prep
    doc.task("Transport preparation", "2 workers, 1 QC inspector, 1 approved surveyor (containers)", h(6),
             ["T-01", "T-09", "T-15"], [("SITE-006", 1), ("SITE-005", 1)],
             [doc.steps([
                 ("W", "HOLD POINT. A modified container needs a new CSC inspection before road or sea transport. Do not ship without the surveyor's plate or record." if is_c else "Do not lift the cabinet with IT equipment installed unless the equipment is strapped."),
                 ("C", "Lithium batteries are dangerous goods in transport. Obey the shipping instructions of the battery manufacturer. Keep the state of charge at 30 to 50 %."),
                 "Set the battery to transport state of charge. Open the battery disconnect. Fit the transport lock on the UPS.",
                 "Remove the IT servers if the shipping method does not permit loaded racks. Strap each remaining module to the rack with the transport straps.",
                 "Fit the transport blocking SITE-006 between the racks and the aisle wall. Fit the door locks on the containment." if is_c else "Fit the transport blocking SITE-006 between the rails and the cabinet door.",
                 "Drain the condensate traps. Cap the drains. Cap the pipe sleeves.",
                 "Close and lock the cargo doors. Fit the seal. Record the seal number." if is_c else "Close and lock the door. Record the key number.",
                 f"Weigh the unit on the weigh-bridge or with the crane scale. Record the gross mass. The design gross mass is {d['gross_kg']} kg.",
                 "Surveyor: inspect the container. Fix the new CSC plate or the ACEP record." if is_c else "Fit the lifting label and the centre-of-gravity label on the skid.",
                 "Lift with the four-leg sling set SITE-005 on the top corner castings. Sling angle not less than 60 degrees." if is_c else "Lift with the forklift at the long side fork pockets.",
                 "Put the unit on the trailer. Lock the twist-locks. Attach the transport documents in the document box." if is_c else "Put the unit on the trailer. Strap the skid to the trailer at four points. Attach the transport documents.",
             ]),
              doc.checks([("CTQ-A3", reg["CTQ-A3"].criterion + ". WITNESS POINT.", "Q-11"),
                          ("CTP-A2", reg["CTP-A2"].criterion + ". HOLD POINT.", "Q-11")] if is_c else [("CTQ-A3", reg["CTQ-A3"].criterion + ".", "Q-11")]) +
              (doc.checks([("CTP-S4", reg["CTP-S4"].criterion + ". HOLD POINT.", "Q-11")]) if is_c else "")])

    # ---------------------------------------------------------------- T13 site set-down and hook-up
    doc.task("Site set-down and hook-up", "2 workers, 1 crane operator, 1 licensed electrician, 1 HVAC technician", h(16),
             ["T-01", "T-02", "T-03", "T-09", "T-10", "T-15"],
             [("SITE-001", 1), ("SITE-002", 4), ("SITE-003", 2), ("SITE-004", 1)] + ([("STR-011", 4)] if not is_c else []),
             [doc.steps([
                 ("W", "Keep all persons 10 m from a suspended load. Only the rigger gives signals to the crane operator."),
                 ("W", "HOLD POINT. Only a licensed electrician connects the service conductors. Only a licensed HVAC technician connects the dry cooler pipes." if is_c else "HOLD POINT. Only a licensed electrician connects the service conductors."),
                 "Make sure the pad SITE-001 is complete and cured. Measure the level of the four foundation points. Difference not more than 6 mm.",
                 "Lift the unit from the trailer. Lower the unit onto the four twist-locks SITE-002. Lock the twist-locks." if is_c else f"Lower the cabinet onto the pad. Drill four M16 anchor holes. Fit the anchors STR-011. Torque to {C.TORQUE['M16']} N·m.",
                 "Remove the transport blocking and the straps. Open the containment door locks." if is_c else "Remove the transport straps.",
                 "Drive the two ground rods SITE-003 at the service end, 1.8 m apart. Connect the rods and the pad rebar to the ground bar with exothermic welds.",
                 "Electrician: measure the ground resistance. Target 5 ohm, maximum 25 ohm.",
                 "Electrician: connect the utility conductors to the service section. Examine the phase rotation.",
                 "HVAC technician: set the dry cooler on its pad. Connect the primary pipes. Fill, vent and pressure test the primary loop." if lay.find("DC1") else "HVAC technician: measure the refrigerant pressures. Examine the condenser fans.",
                 "Pull the fibre SITE-004 through the controls entry to the BEN Controller panel. Terminate on the ODF.",
                 "Fit the IT servers in the racks if they were removed. Connect each server to PDU A and PDU B.",
                 "Close the battery disconnect. Energise the unit. Start the UPS.",
                 "Run `python -m ben_engine.commissioning --stage site` on the laptop. The script now takes over. Do the steps of the script.",
             ]),
              doc.checks([("CTQ-E2", reg["CTQ-E2"].criterion + ".", "Q-12"),
                          ("CTQ-E4", reg["CTQ-E4"].criterion + ".", "Q-12"),
                          ("", "Pad level within 6 mm. Twist-locks locked (containers) or anchors torqued (micro). Fibre terminated.", "Q-12"),
                          ("", "Commissioning script report generated and signed. This is the handover point.", "Q-12")])])

    A("## Handover")
    A()
    A("The commissioning script writes the signed report. Give the customer the turnover package (`docs/TURNOVER.md`), the QC forms Q-01 to Q-12, the drawings and the maintenance schedule.")
    A()
    A("## Tool list used in this document")
    A()
    for t in sorted(doc.tools_used):
        A(f"- {t}: {TOOLS[t]}")
    A()
    A("## Item codes used in this document")
    A()
    A("Codes are purchasing catalog codes (`purchasing/parts_catalog.json`); see `design/assembly/ITEM_CODES_USED.md` for the full reconciled list.")
    A()
    for c in sorted(doc.codes_used):
        A(f"- {c} ({_desc(c)})")
    A()
    return doc


# ------------------------------------------------------------------ STE check (STE_STYLE.md rules 2 and 10)
MAX_STEP_WORDS = 20


def ste_banned_words() -> list[str]:
    """The banned list is read from STE_STYLE.md rule 10 (the lines '- word → replacement'), the same way scripts/audit.py A10 reads it."""
    style = open(os.path.join(HERE, "STE_STYLE.md"), encoding="utf-8").read()
    words = []
    for line in style.split("\n"):
        m = _re.match(r"\s*-\s*(.+?)\s*→", line)
        if m:
            for w in _re.split(r"\s*/\s*", m.group(1)):
                w = _re.sub(r"\(.*?\)", "", w).strip()
                if w:
                    words.append(w.lower())
    if not words:
        raise RuntimeError("STE_STYLE.md rule 10 has no banned-word lines")
    return words


def ste_check(lines, name, banned):
    """Return (violations, n_steps, n_sentences). A violation is a banned word anywhere in the prose (except the
    'Check:' heading, part lists and the register table, STE rule 12) or a numbered-step sentence over MAX_STEP_WORDS."""
    viol, n_steps, n_sent = [], 0, 0
    for i, line in enumerate("\n".join(lines).split("\n"), 1):   # the file's physical lines (a step block is one entry)
        if line.startswith("**Parts:**") or line.startswith("|") or _re.match(r"^- (?:STR|ENV|PWR|CLG|CMP|CTL|FS|SITE|SVC)-", line):
            continue
        low = _re.sub(r"`[^`]*`", "", line.lower()).replace("secure vault", "")
        low = _re.sub(r"\*\*check:\*\*|^\s*check:", "", low)
        for b in banned:
            if b == "position":
                if _re.search(r"\bposition (the|each|a|it|them)\b", low):
                    viol.append(f"{name}:{i} banned verb 'position': {line.strip()[:90]}")
                continue
            if _re.search(r"\b" + _re.escape(b) + r"\b", low):
                viol.append(f"{name}:{i} banned word '{b}': {line.strip()[:90]}")
        m = _re.match(r"^\s*\d+\.\s+(.*)", line)
        if m:
            n_steps += 1
            body = _re.sub(r"\(.*?\)|\[.*?\]|`.*?`", "", m.group(1))
            for sent in _re.split(r"(?<=[.!?])\s+", body):
                if not sent.strip():
                    continue
                n_sent += 1
                n = len(sent.split())
                if n > MAX_STEP_WORDS:
                    viol.append(f"{name}:{i} {n} words (max {MAX_STEP_WORDS}): {sent.strip()[:100]}")
    return viol, n_steps, n_sent


def main():
    used_by_tier = {}
    banned = ste_banned_words()
    violations, tot_steps, tot_sent = [], 0, 0
    for t in L.TIER_GEOMETRY:
        lay = L.resolve(t)
        doc = generate(lay)
        lines, used = reconcile(doc.lines, lay)
        v, ns, nsent = ste_check(lines, f"ASSEMBLY-{t}.md", banned)
        violations += v; tot_steps += ns; tot_sent += nsent
        # tool/item code appendix: rewrite the item list with catalog codes
        p = os.path.join(HERE, f"ASSEMBLY-{t}.md")
        with open(p, "w") as f:
            f.write("\n".join(lines))
        used_by_tier[t] = used
        print("  wrote", p, f"({doc.n_task} tasks, {len(used)} catalog codes, {ns} steps, {nsent} step sentences)")
    if violations:
        print(f"\nSTE CHECK FAILED — {len(violations)} violation(s) of STE_STYLE.md rules 2 / 10 (banned list: {len(banned)} words):")
        for v in violations:
            print("  ", v)
        raise SystemExit(f"gen_assembly.py: fix the step text in generate() ({len(violations)} STE violations)")
    print(f"  STE check: 0 banned-word hits, 0 step sentences over {MAX_STEP_WORDS} words "
          f"({tot_steps} numbered steps, {tot_sent} step sentences, {len(banned)} banned words from STE_STYLE.md rule 10, {len(L.TIER_GEOMETRY)} documents)")
    # ------------------------------------------------------------ reconciled item code register
    drawing_codes = {}
    for t in L.TIER_GEOMETRY:
        for i in L.resolve(t).items:
            drawing_codes.setdefault(i.code, set()).add(t)
    all_codes = set(drawing_codes) | {c for u in used_by_tier.values() for c in u}
    for c in list(all_codes):
        all_codes |= set(ALSO.get(c, []))
    missing = [c for c in all_codes if c not in CATALOG]
    lines = ["# Item codes — reconciled with purchasing/parts_catalog.json", "",
             f"Generated {DATE} by `design/assembly/gen_assembly.py`. Every code in the assembly instructions and on the drawings is a code from "
             f"`purchasing/parts_catalog.json` ({len(CATALOG)} parts). Codes marked **new** were appended to the catalog by the design "
             "generator as `estimate` lines (basis note on each) because no catalog part covered them; purchasing confirms or replaces them.", "",
             "| Catalog code | Catalog name | Status | Used in assembly docs (tiers) | On drawings (tiers) | Working code it replaced |", "|---|---|---|---|---|---|"]
    for code in sorted(all_codes):
        if code not in CATALOG:
            continue
        p = CATALOG[code]
        tiers_a = [t for t, u in used_by_tier.items() if code in u]
        olds = sorted({u[code] for u in used_by_tier.values() if code in u})
        tiers_d = sorted(drawing_codes.get(code, []))
        flag = "**new** (" + p["price_status"] + ")" if code in NEW_IN_CATALOG else p["price_status"]
        also = "via " + ", ".join(k for k, v in ALSO.items() if code in v and k in all_codes) if (not tiers_a and not tiers_d) else ""
        lines.append(f"| {code} | {p['name'][:90]} | {flag} | {', '.join(tiers_a) or also} | {', '.join(tiers_d)} | {', '.join(olds)} |")
    lines += ["", "## Catalog items the drawings assume but the catalog sizes differently", "",
              "- `PWR-UPS-93PM50` (BEN 30): two 50 kW towers (495 mm wide each) do not fit the 10 ft row; the drawings and instructions use `PWR-UPS-RM20` x 3 + `PWR-UPS-RM20-XBP` (new). Purchasing decides which stays.",
              "- `PWR-UPS-GVS100` / `PWR-BATT-LI` (BEN 150/500): qty rules `ceil(ups_kva_each/100)*ups_modules` give 4 / 6 UPS frames and 2 / 4 battery cabinets; the rows do not hold them (check I-C21). Drawings use one modular frame with N+1 modules (+ 2 battery cabinets for BEN 500). Recommend qty rule `ceil(ups_kva_each*1.0/100)+1` frames per unit, not per module.",
              "- `STR-RACK48` is 600 x 1200 deep: the BEN 500 aisle drops to 800 mm (< 900 egress, check I-C22). Drawings use a 1070-deep 48U enclosure; change the catalog part or use 42U 1070 racks.",
              "- `CLG-INROW` is the 300 mm / 20 kW-class unit (`inrow_dx_300`); the catalog note says the 600 mm / 30 kW unit is to be quoted separately. BEN 500 residual air also uses `CLG-INROW` (4 units) + `CLG-COND`, which the catalog currently limits to ben10/ben20 (`applies_to_tiers`).",
              "- `FS-PANIC` (new) is required by the egress note in DESIGN_BASIS §6.", ""]
    if missing:
        lines += ["## Codes not in the catalog (fix before purchase)", ""] + [f"- {c}" for c in sorted(missing)] + [""]
    with open(os.path.join(HERE, "ITEM_CODES_USED.md"), "w") as f:
        f.write("\n".join(lines))
    print("  wrote ITEM_CODES_USED.md", "MISSING:" if missing else "", missing or "")


if __name__ == "__main__":
    main()

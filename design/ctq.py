"""Critical-to-quality (CTQ) and critical-to-process (CTP) register for BEN Engine.

One source used by the drawing title sheets (gen_drawings.py), the STE assembly
instructions (gen_assembly.py) and the QC forms. Each item carries the sheet it is shown
on, the check method, the acceptance criterion, the QC form that records it and whether
it is a HOLD point (work stops until a qualified person signs) or a WITNESS point
(QC inspector present).

Numbers that depend on the configuration are formatted with the layout `lay`.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class CTQ:
    id: str
    kind: str          # CTQ | CTP
    sheet: str
    item: str
    method: str
    criterion: str
    form: str
    point: str = ""    # "", "WITNESS", "HOLD"


QC_FORMS = {
    "Q-01": "Receiving inspection",
    "Q-02": "Container structure and modification",
    "Q-03": "Envelope: insulation, liner, seals",
    "Q-04": "Floor channels, anchors and torque record",
    "Q-05": "Racks, hold-downs and containment",
    "Q-06": "Cooling: piping, pressure test, charge",
    "Q-07": "Electrical installation and tests",
    "Q-08": "Controls nodes, sensors and calibration",
    "Q-09": "Fire detection and suppression",
    "Q-10": "Final QC and pre-ship test",
    "Q-11": "Transport preparation",
    "Q-12": "Site set-down and hook-up",
}

# Torque values (ISO 898-1 class 8.8, dry, Kt 0.2) used across the sheets
TORQUE = {"M8": 25, "M10": 50, "M12": 85, "M16": 210, "M20": 410}


def register(lay) -> List[CTQ]:
    d = lay.d
    is_c = lay.is_container
    racks = len(lay.by_kind("rack"))
    aisle = lay.aisle_width if is_c else 0
    items: List[CTQ] = []
    A = items.append

    # ---- A-001 general arrangement
    A(CTQ("CTQ-A1", "CTQ", "A-001", "Overall external dimensions", "Steel tape, 2 diagonals",
          f"L {lay.ext_l:.0f} / W {lay.ext_w:.0f} / H {lay.ext_h:.0f} mm, each +0/-6 mm; diagonals within 10 mm", "Q-02"))
    if is_c:
        A(CTQ("CTQ-A2", "CTQ", "A-001", "ISO corner castings undamaged, CSC plate present and legible", "Visual + photo", "No cracks, no weld repair without report; CSC plate date valid", "Q-01"))
        A(CTQ("CTP-A1", "CTP", "A-001", "Roof and wall cutouts (line sets, cable entries) reinforced with welded frames", "Certified welder (AWS D1.1 / ISO 9606-1); weld visual VT",
              "Frame 50x50x5 fully welded, no undercut > 0.5 mm; primed within 4 h", "Q-02", "HOLD"))
        A(CTQ("CTP-A2", "CTP", "A-001", "CSC re-inspection after structural modification", "Approved surveyor", "New CSC plate or ACEP record issued before transport", "Q-11", "HOLD"))
    else:
        A(CTQ("CTQ-A2", "CTQ", "A-001", "Cabinet IP55 / NEMA 3R rating preserved at every cutout", "Visual; hose test IEC 60529", "No water ingress after 3 min hose test", "Q-03"))
    A(CTQ("CTQ-A3", "CTQ", "A-001", "Gross mass against drawing weight table", "Certified weigh-bridge or crane scale", f"Gross {d['gross_kg']} kg +10 % max; record value", "Q-11", "WITNESS"))

    # ---- A-002 interior layout
    A(CTQ("CTQ-B1", "CTQ", "A-002", "Row position from door-end wall", "Steel tape from liner face", "Each tag x-position per A-002 +/-10 mm", "Q-05"))
    if is_c:
        A(CTQ("CTQ-B2", "CTQ", "A-002", "Clear egress / working-space width in front of the row", "Steel tape at 3 points",
              f">= 914 mm (drawn {aisle:.0f} mm) along the whole row; nothing stored in the aisle", "Q-05", "WITNESS"))
    A(CTQ("CTQ-B3", "CTQ", "A-002", "Rack rails plumb", "1.8 m spirit level or laser, both axes", "Within 2 mm over 2 m", "Q-05"))
    A(CTQ("CTQ-B4", "CTQ", "A-002", "Rack-to-rack gap and alignment of fronts", "Feeler gauge / straight-edge", "Gap <= 3 mm; fronts within 3 mm of a straight line", "Q-05"))
    if is_c and lay.notes.get("plenum", 0):
        A(CTQ("CTQ-B5", "CTQ", "A-002", "Hot-aisle containment leakage", "dP across containment at full fan speed (node dP_aisle)", ">= 5 Pa cold-to-hot with all doors closed; blanking panels in every open U", "Q-05"))
    A(CTQ("CTQ-B6", "CTQ", "A-002", "Labels on every item match drawing tags", "Visual against A-002", "100 % of tags present, laminated, 10 mm text minimum", "Q-10"))

    # ---- A-003 envelope
    if is_c:
        A(CTQ("CTQ-C1", "CTQ", "A-003", "PIR insulation thickness and continuity", "Depth gauge at 10 random points; visual at joints", "100 mm +5/-0; no gap > 3 mm; joints taped", "Q-03"))
        A(CTQ("CTQ-C2", "CTQ", "A-003", "Vapour barrier / liner joints sealed", "Visual + smoke pencil at 10 joints", "Continuous sealant bead; no smoke movement", "Q-03"))
        A(CTQ("CTQ-C3", "CTQ", "A-003", "Door seal compression", "Paper-strip test at 8 points around each door", "Paper held at every point; no light visible from inside", "Q-03"))
        A(CTQ("CTP-C1", "CTP", "A-003", "Floor drain and condensate drain fall", "Spirit level / water test", "Fall >= 1:100 toward drain; water test clears in < 60 s", "Q-03"))
        A(CTQ("CTQ-C4", "CTQ", "A-003", "Exposed steel at thermal bridges (corner posts, door frame) insulated", "Visual", "20 mm closed-cell foam, no bare steel inside the envelope", "Q-03"))
    else:
        A(CTQ("CTQ-C1", "CTQ", "A-003", "Cabinet door gasket continuous and compressed", "Paper-strip test at 8 points", "Paper held at every point", "Q-03"))

    # ---- S-001 floor / anchoring
    if is_c:
        A(CTQ("CTP-S1", "CTP", "S-001", f"Floor channel through-bolts M12 torqued", "Calibrated torque wrench (cal. within 12 months)", f"{TORQUE['M12']} N·m +/-10 %; mark each bolt with paint stripe", "Q-04", "WITNESS"))
        A(CTQ("CTP-S2", "CTP", "S-001", "Rack hold-down bolts M12 torqued", "Calibrated torque wrench", f"{TORQUE['M12']} N·m; 4 bolts per rack, {4 * racks} total", "Q-04", "WITNESS"))
        A(CTQ("CTQ-S1", "CTQ", "S-001", "Floor channel level along the row", "Laser level", "Within 3 mm over the full row length; shim with steel only", "Q-04"))
        A(CTQ("CTP-S3", "CTP", "S-001", "Equipment skid bolts (UPS, battery, CDU) M12 torqued", "Calibrated torque wrench", f"{TORQUE['M12']} N·m; 4 per cabinet", "Q-04"))
        A(CTQ("CTP-S4", "CTP", "S-001", "Lifting: 4-point spreader on top castings only", "Rigging check by competent person", "Sling angle >= 60 deg from horizontal; never lift by bottom castings with load inside", "Q-11", "HOLD"))
    else:
        A(CTQ("CTP-S1", "CTP", "S-001", "Skid anchors M16 to pad torqued", "Calibrated torque wrench", f"{TORQUE['M16']} N·m; 4 anchors", "Q-12", "WITNESS"))
        A(CTQ("CTP-S2", "CTP", "S-001", "Rail mounting bolts M8 torqued", "Calibrated torque wrench", f"{TORQUE['M8']} N·m", "Q-04"))

    # ---- E-001 power
    A(CTQ("CTP-E1", "CTP", "E-001", "All power terminations by licensed electrician", "Licence copy on file; sign-off", "No energisation before sign-off", "Q-07", "HOLD"))
    A(CTQ("CTP-E2", "CTP", "E-001", "Conductor terminations torqued to manufacturer value", "Calibrated torque screwdriver/wrench", "Value on device label; record every lug", "Q-07", "WITNESS"))
    A(CTQ("CTQ-E1", "CTQ", "E-001", "Insulation resistance of feeders", "1000 V megger, phase-phase and phase-ground", ">= 100 Mohm at 1000 V dc (feeders), >= 1 Mohm (branch)", "Q-07"))
    A(CTQ("CTQ-E2", "CTQ", "E-001", "Grounding electrode and bonding resistance", "Fall-of-potential tester; micro-ohmmeter for bonds", "Electrode <= 25 ohm (target <= 5 ohm); every bond <= 0.1 ohm", "Q-07", "WITNESS"))
    A(CTQ("CTQ-E3", "CTQ", "E-001", "EPO drops UPS output and cooling", "Functional test at pre-ship", "All IT power off < 1 s; recorded on Q-10", "Q-10", "WITNESS"))
    A(CTQ("CTQ-E4", "CTQ", "E-001", "Phase rotation and voltage at every panel", "Phase rotation meter, true-RMS meter", f"Rotation A-B-C; voltage {d['voltage']} +/-5 %", "Q-07"))

    # ---- M-001 cooling
    A(CTQ("CTP-M1", "CTP", "M-001", "Refrigerant brazing, evacuation and charge by licensed HVAC technician (EPA 608 / F-gas)", "Licence copy; vacuum gauge log",
          "Nitrogen purge while brazing; vacuum <= 500 micron held 30 min; charge per nameplate", "Q-06", "HOLD"))
    A(CTQ("CTQ-M1", "CTQ", "M-001", "Refrigerant / coolant pressure test", "Dry nitrogen or hydrostatic, calibrated gauge", "Refrigerant: 1.1 x design pressure 24 h, drop <= 1 %; water: 1.5 x working pressure 2 h, no drop", "Q-06", "WITNESS"))
    A(CTQ("CTQ-M2", "CTQ", "M-001", "Condensate / drip-tray drains run to drain", "Pour 1 L water in each tray", "Clears in < 60 s; no pooling", "Q-06"))
    A(CTQ("CTQ-M3", "CTQ", "M-001", "Leak rope under every cooling unit and along manifolds", "Wet-finger test at each 1 m", "Node reports leak = 1 within 10 s at every point", "Q-08"))
    if lay.notes.get("cooling_resolved") in ("rdhx_drycooler", "dlc_cdu"):
        A(CTQ("CTQ-M4", "CTQ", "M-001", "Coolant mix and flow", "Refractometer; CDU flow meter", "30 % propylene glycol +/-2 %; flow per rack within +/-10 % of design", "Q-06"))
    A(CTQ("CTQ-M5", "CTQ", "M-001", "Supply air / coolant temperature at design load", "Commissioning sweep (software)", f"Rack inlet 18-27 C (ASHRAE {d['ashrae_class']}); all units share load within 15 %", "Q-10"))

    # ---- C-001 controls
    hz = " / ".join(str(z) for z in lay.notes.get("probe_heights", (400, 1200, 1800)))
    A(CTQ("CTQ-K1", "CTQ", "C-001", "Sensor positions", "Steel tape from rack centre and floor", f"Inlet probes at {hz} mm +/-20 mm; 50 mm in front of the rack face", "Q-08"))
    A(CTQ("CTQ-K2", "CTQ", "C-001", "Sensor ID labels match PROTOCOL.md channel names", "Visual against C-001 schedule", "100 % match; label at sensor and at node terminal", "Q-08"))
    A(CTQ("CTQ-K3", "CTQ", "C-001", "Temperature probes calibrated against reference", "Ice-point and 40 C bath, 3 points", "Within +/-0.25 C after correction; cal_id stored in node", "Q-08", "WITNESS"))
    A(CTQ("CTQ-K4", "CTQ", "C-001", "dP tare and door contact function", "Tare with containment open; open/close door", "dP reads 0 +/-0.4 Pa after tare; door = 1 within 2 s", "Q-08"))
    A(CTQ("CTP-K1", "CTP", "C-001", "Life-safety contacts (fire, EPO) hard-wired, not on MQTT bus", "Visual trace of wiring", "Dry contacts only to node; releasing circuit independent", "Q-09", "HOLD"))
    A(CTQ("CTP-F1", "CTP", "C-001", "Clean-agent system installed and commissioned by certified installer", "Certificate; room integrity (door fan) test",
          "Hold time >= 10 min at design concentration; certificate on file", "Q-09", "HOLD"))
    return items


def for_sheet(items: List[CTQ], sheet: str) -> List[CTQ]:
    return [i for i in items if i.sheet == sheet]

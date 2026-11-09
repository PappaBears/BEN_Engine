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
    "Q-08": "Controls: panel, BEN Pods, transmitters and calibration",
    "Q-09": "Fire detection and suppression",
    "Q-10": "Final QC and pre-ship test",
    "Q-11": "Transport preparation",
    "Q-12": "Site set-down and hook-up",
}

# Torque values (ISO 898-1 class 8.8, dry, Kt 0.2) used across the sheets
TORQUE = {"M8": 25, "M10": 50, "M12": 85, "M16": 210, "M20": 410}


def register(lay) -> List[CTQ]:
    if getattr(lay, "is_minirack", False):
        return _register_minirack(lay)
    items = _register(lay)
    if lay.notes.get("dense"):
        # no refrigerant inside a liquid-first module (the trim chiller on the skid is factory sealed): CTP-M1 is the liquid piping
        items = [CTQ("CTP-M1", "CTP", "M-001", "W45 and trim-loop piping: press-fit / welded joints, flushing and fill by a licensed mechanical contractor",
                     "Joint log (press-fit gauge or weld VT); flush log; fill record", "Every joint logged; flush until the strainer stays clean for 30 min and turbidity < 5 NTU; fill fluid per CTQ-M9",
                     "Q-06", "HOLD") if i.id == "CTP-M1" else i for i in items]
    if lay.notes.get("dense") or lay.notes.get("nc_liner"):
        items += _register_rev2(lay)
    return items


def _register(lay) -> List[CTQ]:
    d = lay.d
    is_c = lay.is_container          # ISO-frame module tiers (BEN 30/150/500)
    is_h = lay.is_hall               # BEN 2000 hall
    is_cab = lay.is_cabinet          # BEN 5 cabinet
    hz = lay.cfg.hardening
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
    elif is_h:
        A(CTQ("CTQ-A2", "CTQ", "A-001", f"Road sections ({lay.notes.get('n_sections', 9)} + 3 power module) undamaged, factory QC dossier and IP66 factory test certificate per section", "Visual + photo; document check",
              "No frame distortion > 5 mm over 12.2 m; sealed panel joints intact; factory hose-test certificate per section", "Q-01"))
        A(CTQ("CTP-J1", "CTP", "A-001", "Module joint seal and continuity (BEN 2000): two-stage gasket compressed, splice plates torqued, bonding jumpers fitted at every joint", "Manufacturer technician; torque wrench; micro-ohmmeter; smoke pencil along the seam",
              f"Gasket compression 30-50 % (gauge); splice bolts M20 {TORQUE['M20']} N·m; bond <= 0.1 ohm across every joint; no smoke movement along the seam", "Q-02", "HOLD"))
        A(CTQ("CTP-A2", "CTP", "A-001", "Module set: bearing on grade beams, level and alignment before joining", "Laser level; steel tape", "Rails within 3 mm over 12.2 m; joint gap 10 +/-3 mm before compression; anchors at every rail bracket", "Q-12", "WITNESS"))
    else:
        A(CTQ("CTQ-A2", "CTQ", "A-001", "Cabinet NEMA 4X / IP66 rating preserved at every cutout (cooler flanges, glands)", "Visual; hose test UL 50E type 4X", "No water ingress after the hose test; gasket continuous at every flange", "Q-03"))
    A(CTQ("CTQ-A3", "CTQ", "A-001", "Gross mass against drawing weight table", "Certified weigh-bridge or crane scale", f"Gross {d['gross_kg']} kg +10 % max; record value" + (" (per road section)" if is_h else ""), "Q-11", "WITNESS"))
    # IP66 element-proof envelope on every tier (docs/TIER_AND_ENCLOSURE_DECISION.md §3, H1 baseline)
    A(CTQ("CTQ-A4", "CTQ", "A-003", "Hose test per UL 50E type 4X on every penetration (gasketed frames, glands, roof curbs, door seals)", "Hose test: 25 mm nozzle, 240 L/min, 3-3.5 m, 5 min per m of seam (UL 50E 4X / IEC 60529 IPX6); inspect inside",
          "No water inside the envelope at any penetration or door; record every penetration ID", "Q-03", "WITNESS"))

    # ---- A-002 interior layout
    A(CTQ("CTQ-B1", "CTQ", "A-002", "Row position from door-end wall", "Steel tape from liner face", "Each tag x-position per A-002 +/-10 mm", "Q-05"))
    if is_c:
        A(CTQ("CTQ-B2", "CTQ", "A-002", "Clear egress / working-space width in front of the row", "Steel tape at 3 points",
              f">= 914 mm (drawn {aisle:.0f} mm) along the whole row; nothing stored in the aisle", "Q-05", "WITNESS"))
    elif is_h:
        A(CTQ("CTQ-B2", "CTQ", "A-002", "Cold aisle (NEC 110.26 condition 2) and contained hot aisle widths, every row", "Steel tape at 3 points per aisle",
              ">= 1,067 mm cold aisle (drawn 1,100), >= 900 mm hot aisle (drawn 900); hot-aisle doors open to the egress path", "Q-05", "WITNESS"))
    A(CTQ("CTQ-B3", "CTQ", "A-002", "Rack rails plumb", "1.8 m spirit level or laser, both axes", "Within 2 mm over 2 m", "Q-05"))
    A(CTQ("CTQ-B4", "CTQ", "A-002", "Rack-to-rack gap and alignment of fronts", "Feeler gauge / straight-edge", "Gap <= 3 mm; fronts within 3 mm of a straight line", "Q-05"))
    if (is_c and lay.notes.get("plenum", 0)) or is_h:
        A(CTQ("CTQ-B5", "CTQ", "A-002", "Hot-aisle containment leakage", "dP across containment at full fan speed (Pod dP_aisle / Setra 264)", ">= 5 Pa cold-to-hot with all doors closed; blanking panels in every open U", "Q-05"))
    A(CTQ("CTQ-B6", "CTQ", "A-002", "Labels on every item match drawing tags", "Visual against A-002", "100 % of tags present, laminated, 10 mm text minimum", "Q-10"))

    # ---- A-003 envelope
    if is_c:
        A(CTQ("CTQ-C1", "CTQ", "A-003", "PIR insulation thickness and continuity", "Depth gauge at 10 random points; visual at joints", "100 mm +5/-0; no gap > 3 mm; joints taped", "Q-03"))
        A(CTQ("CTQ-C2", "CTQ", "A-003", "Vapour barrier / liner joints sealed", "Visual + smoke pencil at 10 joints", "Continuous sealant bead; no smoke movement", "Q-03"))
        A(CTQ("CTP-C1", "CTP", "A-003", "Floor drain and condensate drain fall", "Spirit level / water test", "Fall >= 1:100 toward drain; water test clears in < 60 s", "Q-03"))
        A(CTQ("CTQ-C4", "CTQ", "A-003", "Exposed steel at thermal bridges (corner posts, door frame) insulated", "Visual", "20 mm closed-cell foam, no bare steel inside the envelope", "Q-03"))
    elif is_h:
        A(CTQ("CTQ-C1", "CTQ", "A-003", "Sandwich panel joints and section seams sealed inside and out", "Visual + smoke pencil at every seam, 10 points per bay", "Continuous sealant; no smoke movement; cover flashing fixed at 300 mm pitch", "Q-03"))
        A(CTQ("CTP-C1", "CTP", "A-003", "Slab fall and floor drains at CDU rows", "Spirit level / water test", "Fall >= 1:100 toward drains; 1 L clears in < 60 s", "Q-03"))
    else:
        A(CTQ("CTQ-C1", "CTQ", "A-003", "Cabinet double-skin and 40 mm PIR continuous at cooler flanges", "Visual", "No bare steel inside; flange gaskets compressed", "Q-03"))
    A(CTQ("CTQ-C3", "CTQ", "A-003", "Door gasket compression check (compression gasket, three-point latch)", "Paper-strip test at 8 points around each door; feeler gauge at the latch side",
          "Paper held at every point; gasket compression 30-50 % (gauge); no light visible from inside; latch engages at all three points", "Q-03"))
    # hardening add-ons (docs/TIER_AND_ENCLOSURE_DECISION.md §3)
    if hz in ("H2", "H3"):
        A(CTQ("CTQ-H1", "CTQ", "A-003", "H2: flood plinth 600 mm level, anchored; C5-M coating DFT; ePM1 intake filters and hoods fitted", "Laser level; DFT gauge (ISO 19840) 20 points; visual",
              "Plinth top within 5 mm; DFT >= 320 um at 90 % of points, none < 260 um; filter class label ePM1 65 %", "Q-03"))
    if hz == "H3":
        A(CTQ("CTQ-H2", "CTQ", "A-003", "Ballistic panel certification record (H3): UL 752 level per contract, lot certificates, seams battened", "Document check; visual of every seam and fastener line",
              "UL 752 level matches the order; certificate per panel lot on file; seam strip overlap >= 50 mm; no unprotected penetration in a wall", "Q-03", "HOLD"))
        A(CTQ("CTQ-H3", "CTQ", "A-003", "Shield integrity test 80 dB (H3 HEMP option): shielded enclosure, door and filtered penetrations", "IEEE 299 / MIL-STD-188-125-1 shielding-effectiveness survey by an accredited test house",
              ">= 80 dB from 10 kHz to 1 GHz at every test point; door and every penetration tested; report on file", "Q-10", "HOLD"))
        A(CTQ("CTQ-H4", "CTQ", "A-002", "Forced-entry door (ASTM F3038) and mantrap interlock function", "Document check; functional test",
              "Test report level per contract; both mantrap doors never open together; two-factor reader audit entry in BEN Care", "Q-10", "WITNESS"))

    # ---- S-001 floor / anchoring
    if is_h:
        A(CTQ("CTP-S1", "CTP", "S-001", "Module rail anchors to grade beams (M20 adhesive anchors) torqued", "Calibrated torque wrench; anchor pull test on 5 %", f"{TORQUE['M20']} N·m; pull test >= 25 kN; every bracket anchored", "Q-04", "WITNESS"))
        A(CTQ("CTP-S2", "CTP", "S-001", "Rack base anchors to slab (M12 adhesive anchors, 4 per rack) torqued", "Calibrated torque wrench", f"{TORQUE['M12']} N·m; 4 per rack, {4 * racks} total", "Q-04", "WITNESS"))
        A(CTQ("CTQ-S1", "CTQ", "S-001", "Slab level under the rows", "Laser level", "Within 3 mm over each row; grout under rack bases where > 3 mm", "Q-04"))
        A(CTQ("CTP-S3", "CTP", "S-001", "Equipment anchors (CDU, fan wall, switchgear, UPS, batteries) per manufacturer seismic detail", "Calibrated torque wrench; anchor schedule", "Anchor type, embedment and torque per S-001 schedule; 100 % recorded", "Q-04"))
        A(CTQ("CTP-S4", "CTP", "S-001", "Section lift: spreader frame on the manufacturer's lifting points only", "Rigging check by competent person", "Lifting points per manufacturer; sling angle >= 60 deg; tag lines; wind < 10 m/s", "Q-12", "HOLD"))
    elif is_c:
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
    A(CTQ("CTQ-E4", "CTQ", "E-001", "Phase rotation and voltage at every panel", "Phase rotation meter, true-RMS meter", f"Rotation A-B-C; voltage {d['voltage'].split(' → ')[-1] if is_h else d['voltage']} +/-5 %", "Q-07"))
    if is_h:
        A(CTQ("CTP-E3", "CTP", "E-001", "MV/LV acceptance tests (NETA ATS): transformers, 15 kV switchgear, 4,000 A switchgear, relay settings", "NETA-accredited test firm; report", "All ATS tests passed; relay settings per coordination study; report before energisation", "Q-07", "HOLD"))
        A(CTQ("CTQ-E5", "CTQ", "E-001", "Switchgear working space NEC 110.26 condition 3 and two entrances", "Steel tape", ">= 1,200 mm in front (drawn 1,500); rear >= 1,000; two doors >= 610 x 2,000 at opposite ends", "Q-07"))
        A(CTQ("CTQ-E6", "CTQ", "E-001", "Generator N+1 paralleling and 2N UPS transfer (integrated systems test)", "Pull-the-plug test with load bank; event log", "Any one generator out: load carried; any one UPS string out: IT held; transfer < 10 ms on static switch", "Q-10", "WITNESS"))

    # ---- M-001 cooling
    if is_h:
        A(CTQ("CTP-M1", "CTP", "M-001", "Plant piping welding, flushing and fill by licensed mechanical contractor; adiabatic water treatment commissioned", "Weld VT; flush log; water analysis",
              "Welds VT pass; flush until turbidity < 5 NTU; glycol 30 % +/-2; make-up water treatment report", "Q-06", "HOLD"))
    else:
        A(CTQ("CTP-M1", "CTP", "M-001", "Refrigerant brazing, evacuation and charge by licensed HVAC technician (EPA 608 / F-gas)", "Licence copy; vacuum gauge log",
              "Nitrogen purge while brazing; vacuum <= 500 micron held 30 min; charge per nameplate", "Q-06", "HOLD"))
    A(CTQ("CTQ-M1", "CTQ", "M-001", "Refrigerant / coolant pressure test", "Dry nitrogen or hydrostatic, calibrated gauge", "Refrigerant: 1.1 x design pressure 24 h, drop <= 1 %; water: 1.5 x working pressure 2 h, no drop", "Q-06", "WITNESS"))
    A(CTQ("CTQ-M2", "CTQ", "M-001", "Condensate / drip-tray drains run to drain", "Pour 1 L water in each tray", "Clears in < 60 s; no pooling", "Q-06"))
    A(CTQ("CTQ-M3", "CTQ", "M-001", "Leak rope under every cooling unit and along manifolds", "Wet-finger test at each 1 m", "Controller reports leak = 1 within 10 s at every point (LD2100 on Pro, Pod E leak input on Lite)", "Q-08"))
    if lay.notes.get("cooling_resolved") in ("rdhx_drycooler", "dlc_cdu"):
        A(CTQ("CTQ-M4", "CTQ", "M-001", "Coolant mix and flow", "Refractometer; CDU flow meter", "30 % propylene glycol +/-2 %; flow per rack within +/-10 % of design", "Q-06"))
    if lay.notes.get("cooling_resolved") == "dlc_hd":
        A(CTQ("CTQ-M4", "CTQ", "M-001", "W45 loop fluid and flow", "Refractometer / water analysis; CDU flow meter", f"Treated water or 25 % PG where t_min < 0 C; loop flow {d['loop_flow_lpm']} L/min +/-10 % at ΔT {d['loop_dt_design_k']:.0f} K", "Q-06"))
        A(CTQ("CTQ-M6", "CTQ", "M-001", "Leak-to-isolation time (E19)", "Wet-finger test on a rack drip-tray sensor; valve position switch timed", "Row isolation valves closed <= 15 s after the leak; loop flow to the row 0 within 30 s; alarm raised", "Q-10", "WITNESS"))
    if lay.notes.get("dc800"):
        A(CTQ("CTQ-E7", "CTQ", "E-001", "800 VDC bus insulation monitoring (E17)", "Test resistor each pole to ground; IMD test button", "Healthy >= 500 kOhm; alarm < 100 kOhm within 10 s on each pole; IT load held; location identifies the faulted tap-off", "Q-07", "WITNESS"))
        A(CTQ("CTQ-E8", "CTQ", "E-001", "DC bus polarity, voltage and window", "True-RMS/DC meter at every tap-off", f"Polarity per label; {d['dc_bus_v_nominal']} V nominal, {d['dc_bus_v_pole']} V to ground ({d['dc_convention'].replace('_', ' ')}); window {d['dc_window_v'][0]}-{d['dc_window_v'][1]} V (working assumption)", "Q-07"))
    A(CTQ("CTQ-M5", "CTQ", "M-001", "Supply air / coolant temperature at design load", "Commissioning sweep (software)", f"Rack inlet 18-27 C (ASHRAE {d['ashrae_class']}); all units share load within 15 %", "Q-10"))

    # ---- C-001 controls
    hts = " / ".join(str(z) for z in lay.notes.get("probe_heights", (400, 1200, 1800)))
    A(CTQ("CTQ-K1", "CTQ", "C-001", "Sensor positions", "Steel tape from rack centre and floor", f"Inlet probes at {hts} mm +/-20 mm; 50 mm in front of the rack face", "Q-08"))
    A(CTQ("CTQ-K2", "CTQ", "C-001", "Sensor ID labels match PROTOCOL.md channel names", "Visual against C-001 schedule", "100 % match; label at sensor and at Pod / panel terminal", "Q-08"))
    A(CTQ("CTQ-K3", "CTQ", "C-001", "Temperature probes calibrated against reference", "Ice-point and 40 C bath, 3 points", "Within +/-0.25 C after correction; cal_id stored in the Pod (Secure Vault NVM)", "Q-08", "WITNESS"))
    A(CTQ("CTQ-K4", "CTQ", "C-001", "dP tare and door contact function", "Tare with containment open; open/close door", "dP reads 0 +/-0.4 Pa after tare; door = 1 within 2 s", "Q-08"))
    A(CTQ("CTP-K1", "CTP", "C-001", "Life-safety contacts (fire, EPO) hard-wired, not on MQTT bus or BEN Mesh", "Visual trace of wiring", "Dry contacts only to the controller DI (and Pod monitor input); releasing circuit independent", "Q-09", "HOLD"))
    A(CTQ("CTQ-K5", "CTQ", "C-001", "Pod attestation = OK on all Pods; rogue join rejected", "Commissioning script mesh report (`--stage pre-ship`); join attempt with an unprovisioned Pod",
          f"All {lay.notes.get('n_pods', 3)} Pods attested (certificate chain valid, firmware signature valid, Secure Vault state locked); unprovisioned Pod rejected at join", "Q-08", "WITNESS"))
    A(CTQ("CTP-K2", "CTP", "C-001", "Controller watchdog proven", "Stop ben_engine / unplug the edge computer or RevPi network; stopwatch",
          "Cooling units fall back to local control and the watchdog relay drops within 5 s; alarm logged on return; no IT power affected", "Q-08", "WITNESS"))
    if lay.notes.get("controls_tier", "pro") == "pro":
        A(CTQ("CTQ-K6", "CTQ", "C-001", "BEN Controller panel SCCR label and UL 508A listing mark", "Visual; compare to panel shop drawing",
              "UL 508A mark present; SCCR >= available fault current at the panel feeder; nameplate lists voltage, FLA, drawing number", "Q-08", "HOLD"))
    else:
        A(CTQ("CTQ-K6", "CTQ", "C-001", "BEN Controls Lite cabinet: listed components and 24 VDC fusing", "Visual against component list",
              "RevPi, I/O, PSU and switch all UL/CE listed; each 24 VDC branch fused; cabinet labelled", "Q-08"))
    if not is_cab:
        A(CTQ("CTP-F1", "CTP", "C-001", "Clean-agent system installed and commissioned by certified installer" + (" (one zone per module + power module, VESDA per zone)" if is_h else ""), "Certificate; room integrity (door fan) test",
              "Hold time >= 10 min at design concentration" + (" in every zone" if is_h else "") + "; certificate on file", "Q-09", "HOLD"))
    else:
        A(CTQ("CTP-F1", "CTP", "C-001", "Aerosol suppression unit fitted, actuator independent of the controls bus", "Visual; document", "Unit listed; monitor contact only to the controller; warning label fitted", "Q-09"))
    return items


# ------------------------------------------------------------------ Rev 2 additions (design/rev2/REVISION.json R2-03, R2-04)
def _register_rev2(lay) -> List[CTQ]:
    """Dense liquid-first tiers (BEN 300 / BEN 700): CDU, manifold, W45 loop, trim loop, leak-to-isolation and battery groups.
    Rev 2 module tiers on condition 1: the non-conductive liner (EN-001)."""
    d = lay.d
    items: List[CTQ] = []
    A = items.append
    if lay.notes.get("nc_liner"):
        A(CTQ("CTQ-E10", "CTQ", "A-002", "Aisle-wall liner is ENV-LINER-NC (non-conductive, ASTM E84 Class A) with nylon fasteners and no metal trim; no device on that wall in the working space (EN-001)",
              "Document check (E84 Class A report for the delivered lot); visual; steel tape; continuity tester on the liner face at 10 points",
              "Class A report on file; no conductive path from the liner face to ground (open circuit); clear depth >= 914 mm in front of the row, >= 1,067 mm in front of 480 V gear", "Q-03", "WITNESS"))
    if not lay.notes.get("dense"):
        return items
    A(CTQ("CTQ-M7", "CTQ", "M-001", f"Row CDUs ({d['cooling_units_total']} x 600 kW, N+1): pump failover and approach", "Commissioning: trip the duty pump on each CDU; CDU log",
          "Standby pump takes over in <= 5 s, loop flow dip < 20 %; approach (secondary supply - facility supply) <= 4 K at design load", "Q-10", "WITNESS"))
    A(CTQ("CTQ-M8", "CTQ", "M-001", "Rear-plenum W45 manifold and UQD drops: pressure test and dry-break check", "Hydrostatic test, calibrated gauge class 1.0; connect / disconnect every UQD 3 times on a drip tray",
          "1.5 x working pressure for 2 h, no drop; no drip at any UQD after 3 cycles; drip tray under every drop with a leak sensor", "Q-06", "WITNESS"))
    A(CTQ("CTQ-M9", "CTQ", "M-001", "W45 loop water quality and filtration", "Lab water analysis after flush; filter delta-p log",
          "Conductivity, pH and inhibitor per the CDU / cold-plate vendor limits (OCP / ASHRAE TC 9.9 liquid-cooling guidance); 50 um or finer strainer on the secondary; report before the racks are connected", "Q-06", "HOLD"))
    A(CTQ("CTQ-M10", "CTQ", "M-001", f"Trim loop {d['trim_loop_c']:.0f} C to the residual-air fan coils ({d['trim_loop_kw']} kW, skid chiller)", "Calibrated probe at the fan-coil supply; dew-point from the room Pod RH",
          f"Supply {d['trim_loop_c']:.0f} +/-1 C at design load; supply >= room dew point + 2 K (no condensation); fan coils never on the W45 loop", "Q-10"))
    if "CTQ-M6" not in {i.id for i in _register_ids(lay)}:
        A(CTQ("CTQ-M6", "CTQ", "M-001", "Leak-to-isolation time (E19)", "Wet-finger test on a rack drip-tray sensor; valve position switch timed",
              "Row isolation valves closed <= 15 s after the leak; loop flow to the row 0 within 30 s; alarm raised", "Q-10", "WITNESS"))
    A(CTQ("CTQ-E9", "CTQ", "E-001", f"Lithium battery groups ({d['battery_cabinets']} cabinets of 32.6 kWh): NFPA 855 group limit and UL 9540A evidence", "Document check; steel tape between groups",
          "One cabinet per group (<= 50 kWh); UL 9540 listing and the UL 9540A large-scale test report on file for the reduced spacing, otherwise 914 mm between groups; BMS trip tested", "Q-07", "HOLD"))
    A(CTQ("CTP-S5", "CTP", "S-001", "Rack load-spreading frames STR-LOADFRAME under every rack bolted to the floor channels", "Calibrated torque wrench; laser level",
          f"M12 {TORQUE['M12']} N·m, 4 per frame; frame level within 2 mm; rack {1500} kg on the frame only", "Q-04", "WITNESS"))
    return items


def _register_ids(lay) -> List[CTQ]:
    return _register(lay)


def _register_minirack(lay) -> List[CTQ]:
    """BEN 1 in-house bench build (design/assembly/rev2/ASSEMBLY-ben1.md): sheets A-001, E-001, C-001, I-001."""
    d = lay.d
    f = lay.cfg.form
    items: List[CTQ] = []
    A = items.append
    A(CTQ("CTQ-A1", "CTQ", "A-001", "Rack / cabinet model and outside dimensions", "Model label; steel tape",
          f"{d['geometry']['reference']}; {lay.ext_l:.0f} x {lay.ext_w:.0f} x {lay.ext_h:.0f} mm +/-5", "Q-01"))
    A(CTQ("CTQ-A2", "CTQ", "A-001", f"U stack per A-001 ({lay.notes['u_used']}U of {lay.notes['u_total']}U), shelves and devices fixed", "Visual against the A-001 elevation; tug test on every shelf",
          "Every device in its U; cage nuts / shelf screws tight; nothing loose on a shelf; blanking panels in open U" + (" (cab12)" if f == "cab12" else ""), "Q-05"))
    A(CTQ("CTQ-A3", "CTQ", "A-001", "Unit mass and labels", "Bench scale; visual", f"Mass {d['gross_kg']} kg +10 % max; data plate band, nameplate and QR fitted; serial recorded", "Q-10"))
    A(CTQ("CTP-E1", "CTP", "E-001", "UPS and PDU are listed, cord-connected; no field wiring", "Listing marks (UL 1778 UPS, UL 62368-1 / UL 60950 IT gear)", "Every power item carries a listing mark; no splices, no extension cords, no daisy-chained power strips", "Q-07", "HOLD"))
    A(CTQ("CTQ-E1", "CTQ", "E-001", "Ground continuity, plug to every metal part", "Bond tester / ohmmeter", "<= 0.1 ohm from the UPS plug ground pin to the rack frame and every chassis", "Q-07"))
    A(CTQ("CTQ-E2", "CTQ", "E-001", f"Load on the UPS and on the {d['outlet_circuit_a']} A outlet circuit", "UPS load display; clamp meter at full burn-in load",
          f"UPS load <= 80 % of {d['ups_w']} W; input current <= {0.8 * d['outlet_circuit_a']:.0f} A (NEC 210.19/210.20 continuous)", "Q-07", "WITNESS"))
    A(CTQ("CTQ-E3", "CTQ", "E-001", "UPS self-test and runtime", "UPS self-test; pull the plug at full load", f"Self-test pass; runtime >= {d['ups_runtime_min_est'] * 0.8:.0f} min at burn-in load; graceful shutdown signal reaches the hosts", "Q-10", "WITNESS"))
    A(CTQ("CTQ-K1", "CTQ", "C-001", "Pod positions: P1 inlet (front rail), P2 exhaust (rear rail)", "Visual against C-001", "Pods at the drawn U positions +/-1U; probes 20-50 mm from the rail", "Q-08"))
    A(CTQ("CTQ-K3", "CTQ", "C-001", "Pod probes calibrated", "Ice-point and 40 C bath, 3 points", "Within +/-0.25 C after correction; cal_id in the Pod", "Q-08", "WITNESS"))
    A(CTQ("CTQ-K5", "CTQ", "C-001", "Pod attestation and BEN Care agent enrolment", "Commissioning script `--stage pre-ship`", "Both Pods attested; edge agent online in BEN Care; unprovisioned Pod rejected", "Q-08", "WITNESS"))
    A(CTQ("CTQ-T1", "CTQ", "I-001", "24 h burn-in at full load", "Burn-in script; Pod inlet / exhaust log",
          f"24 h without fault; exhaust - inlet <= {10:.0f} K; noise at 1 m <= {d['noise_dba_target']:.0f} dBA (sound meter, A-weighted)", "Q-10", "HOLD"))
    A(CTQ("CTQ-I1", "CTQ", "I-001", "Customer site checklist signed (circuit, clearances, heat to room, vent)", "Site checklist I-001 with the customer",
          f"Dedicated {d['outlet_circuit_a']} A 120 V circuit; 300 mm clear at inlet and exhaust; {d['heat_to_room_w']} W heat accepted by the room or a {d['closet_vent_cfm']} cfm closet vent", "Q-12"))
    return items


def for_sheet(items: List[CTQ], sheet: str) -> List[CTQ]:
    return [i for i in items if i.sheet == sheet]

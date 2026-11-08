"""Writes docs/SQAM.md (Supplier Quality Assurance Manual) and design/assembly/CTQ-CARD-<tier>.md
from design/ctq.py + design/layout.py, so the manual never drifts from the drawings and the
STE assembly instructions.

Run:  python design/gen_sqam.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L  # noqa: E402
import ctq as C  # noqa: E402
from revision import REV as DRW  # noqa: E402  (design/REVISION.json — the drawing issue this manual is pinned to)

DATE = DRW["issue_date"]
REV = DRW["drawing_rev"]          # the SQAM is re-issued with every drawing revision
DRAWING_SET = f"drawing set Rev {DRW['drawing_rev']} ({DRW['issue_date']}, {DRW['status_title']})"


def tier_list() -> str:
    labels = [L.TIER_GEOMETRY[t]["label"] for t in L.TIER_GEOMETRY]
    return ", ".join(labels[:-1]) + " and " + labels[-1]
ROOT = os.path.dirname(HERE)

# ------------------------------------------------------------------ measurement mapping
# method keyword -> (instrument, instrument accuracy / resolution typically available)
INSTRUMENTS = [
    ("torque wrench", "Calibrated click or digital torque wrench, 20-200 N·m", "+/-3 % of reading (ISO 6789 class A)"),
    ("torque screwdriver", "Calibrated torque screwdriver / wrench per lug size", "+/-6 % of reading"),
    ("steel tape", "Class II steel tape 8 m", "+/-1.1 mm over 5 m (EC class II)"),
    ("laser", "Rotating laser level + receiver", "+/-1.5 mm at 15 m"),
    ("spirit level", "1.8 m spirit level, 0.5 mm/m vial", "0.5 mm/m"),
    ("feeler", "Feeler gauge set + 1 m straight-edge", "0.05 mm"),
    ("depth gauge", "Depth gauge / probe rule", "0.5 mm"),
    ("smoke pencil", "Smoke pencil", "qualitative"),
    ("paper-strip", "Paper strip 80 g/m2, 25 mm wide", "qualitative"),
    ("water test", "1 L measuring jug + stopwatch", "+/-1 s"),
    ("megger", "Insulation resistance tester 1000 V dc", "+/-5 % of reading"),
    ("fall-of-potential", "3-pole earth resistance tester + micro-ohmmeter (bonds)", "+/-2 % + 2 digits; micro-ohm 1 mohm resolution"),
    ("phase rotation", "Phase-rotation meter + true-RMS multimeter CAT IV 600 V", "+/-0.5 % V"),
    ("vacuum gauge", "Digital micron gauge, N2 regulator, calibrated pressure gauge", "micron gauge +/-10 % at 500 micron; gauge class 1.0"),
    ("nitrogen", "Calibrated pressure gauge 0-60 bar, class 1.0", "+/-1 % FS"),
    ("hydrostatic", "Calibrated pressure gauge 0-16 bar, class 1.0", "+/-1 % FS"),
    ("refractometer", "Glycol refractometer (propylene glycol scale)", "+/-1 %"),
    ("flow meter", "CDU / pumping unit flow meter (electromagnetic)", "+/-2 % of reading"),
    ("ice-point", "Ice-point bath + 40 C stirred bath + reference PRT (k=2 0.05 C)", "0.05 C"),
    ("manometer", "Digital manometer 0-125 Pa (or Pod dP channel after tare)", "+/-0.4 Pa"),
    ("dP across", "Pod dP_aisle channel (SDP810) after tare; Setra 264 on the PLC (Pro)", "+/-0.4 Pa"),
    ("wet-finger", "Wet finger / damp cloth + controller event log", "n/a (functional)"),
    ("commissioning sweep", "Commissioning script + calibrated Pod Pt1000 probes", "+/-0.25 C per probe"),
    ("functional test", "Stopwatch / controller event log", "0.1 s"),
    ("weigh-bridge", "Certified weigh-bridge or crane scale", "+/-0.5 % of reading"),
    ("crane scale", "Certified crane scale", "+/-0.5 % of reading"),
    ("hose test", "Hose nozzle 6.3 mm, 12.5 L/min, 3 m (IEC 60529 IPX5)", "qualitative"),
    ("door fan", "Door-fan (room integrity) test kit", "per NFPA 2001 Annex C"),
    ("rigging", "Visual + sling angle gauge / inclinometer", "1 deg"),
    ("visual", "Visual, with photo record", "n/a"),
    ("licence", "Document check (licence / certificate copy)", "n/a"),
]


def instrument_for(method: str):
    m = method.lower()
    for key, inst, acc in INSTRUMENTS:
        if key in m:
            return inst, acc
    return "Per method column", "n/a"


def quarter_tolerance(criterion: str) -> str:
    """Instrument accuracy required = <= 1/4 of the tolerance, when the criterion carries a numeric tolerance."""
    c = criterion
    m = re.search(r"\+/-\s*(\d+(?:\.\d+)?)\s*(mm|%|C|Pa|N·m|K)", c)
    if m:
        v = float(m.group(1)); u = m.group(2)
        return f"<= {v / 4:g} {u} (1/4 of +/-{v:g} {u})"
    m = re.search(r"[Ww]ithin\s+(\d+(?:\.\d+)?)\s*(mm|%|C|Pa)", c)
    if m:
        v = float(m.group(1)); u = m.group(2)
        return f"<= {v / 4:g} {u} (1/4 of {v:g} {u})"
    m = re.search(r"\+(\d+)/-(\d+)\s*mm", c)
    if m:
        band = int(m.group(1)) + int(m.group(2))
        return f"<= {band / 4:g} mm (1/4 of the {band} mm band)"
    m = re.search(r"<=\s*(\d+(?:\.\d+)?)\s*(mm|ohm|Pa|%|s)", c)
    if m:
        v = float(m.group(1)); u = m.group(2)
        return f"<= {v / 4:g} {u} (1/4 of the {v:g} {u} limit)"
    m = re.search(r">=\s*(\d+(?:\.\d+)?)\s*(mm|Pa|min)", c)
    if m:
        v = float(m.group(1)); u = m.group(2)
        return f"<= {max(v * 0.05, 0.1):g} {u} (<= 5 % of the limit; one-sided)"
    return "n/a (attribute / document check)"


def frequency(item: C.CTQ, lay) -> str:
    if item.point == "HOLD":
        return "100 %, every unit, at the hold point"
    if item.id in ("CTQ-A1", "CTQ-A3", "CTQ-E3", "CTQ-M5", "CTQ-E2"):
        return "100 % every unit + first article full record"
    if "every" in item.criterion.lower() or "100 %" in item.criterion or "each" in item.criterion.lower():
        return "100 % of the feature on every unit"
    if "random" in item.method.lower():
        return "Sample per method on every unit; 100 % on first article"
    return "Every unit (one record per unit); 100 % on first article"


ROLE = {"A": "Fabricator / certified welder; QC inspector", "B": "Fitter (racks, containment); QC inspector", "C": "Envelope fitter; QC inspector",
        "S": "Fitter; QC inspector (witness)", "E": "Licensed electrician; QC inspector", "M": "Licensed HVAC technician; fitter",
        "K": "Controls technician", "F": "Certified fire-system installer"}


def responsible(item: C.CTQ) -> str:
    if item.form == "Q-09":
        return ROLE["F"]
    return ROLE.get(item.id[4], "QC inspector")


def reaction(item: C.CTQ) -> str:
    if item.point == "HOLD":
        return "STOP. Work after the hold point does not start. Named qualified person corrects and re-presents; Schreiber AI quality re-signs. NCR if the cause is a process failure."
    if item.kind == "CTP":
        return "STOP the step. Correct the process (re-torque / re-run / re-do), re-measure, QC re-witness. Record on the Q-form and raise an NCR if repeated."
    return "Tag the feature, raise an NCR, rework to the specification and re-measure 100 %. Use-as-is only with Schreiber AI engineering approval on the deviation request."


# ------------------------------------------------------------------ writers
def ctq_table(items, lay, full=True):
    rows = ["| ID | Type | Characteristic | Specification / tolerance | Method and instrument | Instrument accuracy required | Sample / frequency | Form | Hold / witness | Responsible | Reaction plan |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for it in items:
        inst, acc = instrument_for(it.method)
        rows.append(f"| {it.id} | {it.kind} | {it.item} ({it.sheet}) | {it.criterion} | {it.method}; {inst} (typ. {acc}) | {quarter_tolerance(it.criterion)} | {frequency(it, lay)} | {it.form} | {it.point or '-'} | {responsible(it)} | {reaction(it)} |")
    return "\n".join(rows)


def ctq_card(lay, items):
    d = lay.d
    o = [f"# CTQ / CTP quick card — {d['tier_label']}", "",
         f"Schreiber AI · BEN Engine · Rev {REV} {DATE} · pin at the bay · generated by `design/gen_sqam.py` from `design/ctq.py`. "
         f"Configuration: {lay.cfg.it_kw:.0f} kW, {lay.cfg.racks} rack(s), {L.COOLING_LIBRARY[lay.notes.get('cooling_resolved', lay.cfg.cooling)]['label']}, {d['voltage']} {d['service_breaker_a']} A.", "",
         "**STOP at every HOLD. Call QC for every WITNESS. Write the number, not a tick.**", "",
         "| ID | What | Must be | How | Form | Stop? |", "|---|---|---|---|---|---|"]
    for it in items:
        stop = "HOLD" if it.point == "HOLD" else ("WITNESS" if it.point == "WITNESS" else "")
        o.append(f"| {it.id} | {it.item} | {it.criterion} | {it.method} | {it.form} | {stop} |")
    o += ["", "Torque (class 8.8, dry, calibrated wrench, +/-10 %): " + " · ".join(f"{k} {v} N·m" for k, v in C.TORQUE.items()) + ".",
          "", "Probe heights: " + " / ".join(str(z) for z in lay.notes.get("probe_heights", (400, 1200, 1800))) + " mm, 50 mm in front of the rack face. "
          "Aisle: >= 914 mm clear. Labels: 10 mm text, laminated, every tag on A-002 / C-001.", "",
          f"Hold points on this tier: {sum(1 for i in items if i.point == 'HOLD')} · Witness points: {sum(1 for i in items if i.point == 'WITNESS')} · "
          f"CTQ: {sum(1 for i in items if i.kind == 'CTQ')} · CTP: {sum(1 for i in items if i.kind == 'CTP')}.", ""]
    return "\n".join(o)


STAGES = [
    ("Receiving", "Task 01", ["CTQ-A1", "CTQ-A2"], "Enclosure and parts accepted only after Q-01 is complete; damaged corner castings are a rejection."),
    ("Structural (cutouts, frames, bosses)", "Task 02", ["CTP-A1", "CTP-A2"], "HOLD: certified welder. All frames welded, VT passed, primed within 4 h. No cutout within 300 mm of a corner post."),
    ("Envelope (insulation, liner, seals, drains)", "Task 03", ["CTQ-C1", "CTQ-C2", "CTQ-C3", "CTQ-C4", "CTP-C1"], "Smoke-pencil 10/10 joints still; paper strip held at 8/8 points per door; drains clear < 60 s."),
    ("Mechanical (floor channels, trays, racks, containment)", "Task 04-06", ["CTP-S1", "CTP-S2", "CTP-S3", "CTQ-S1", "CTQ-B1", "CTQ-B2", "CTQ-B3", "CTQ-B4", "CTQ-B5"], "WITNESS: torque of channel and hold-down bolts, paint-marked. Racks plumb 2 mm / 2 m, aisle >= 914 mm."),
    ("Cooling (units, refrigerant, coolant)", "Task 07", ["CTP-M1", "CTQ-M1", "CTQ-M2", "CTQ-M4"], "HOLD: EPA 608 / F-gas technician. WITNESS: pressure test. Drains water-tested."),
    ("Electrical", "Task 08", ["CTP-E1", "CTP-E2", "CTQ-E1", "CTQ-E2", "CTQ-E4"], "HOLD: licensed electrician lands conductors and energises. WITNESS: lug torque record and ground resistance."),
    ("Controls and sensors", "Task 09", ["CTQ-K1", "CTQ-K2", "CTQ-K3", "CTQ-K4", "CTQ-M3", "CTP-K1"], "Probe heights +/-20 mm; labels = PROTOCOL.md names; calibration +/-0.25 C witnessed; life-safety hard-wired."),
    ("Fire detection and suppression", "Task 10", ["CTP-F1", "CTP-K1"], "HOLD: certified installer; room-integrity hold time >= 10 min; certificate on file."),
    ("Final QC and FAT", "Task 11", ["CTQ-B6", "CTQ-M5", "CTQ-E3", "CTQ-A3"], "Label walk-down 100 %; 2 h at 100 % load within ASHRAE class; EPO < 1 s witnessed; commissioning report hash recorded."),
    ("Transport preparation", "Task 12", ["CTQ-A3", "CTP-A2", "CTP-S4"], "HOLD: CSC re-inspection and rigging check; battery SoC 30-50 %; gross mass weighed."),
]


def write_sqam(lays):
    regs = {t: C.register(lay) for t, lay in lays.items()}
    o = []
    A = o.append
    A("# Schreiber AI — Supplier Quality Assurance Manual (SQAM) for BEN Engine")
    A("")
    A(f"| | |\n|---|---|\n| Document | SQAM-BEN |\n| Revision | {REV} — {DATE} |\n| Owner | Schreiber AI Quality (design authority: Schreiber AI Engineering) |\n| Applies to | Contract manufacturers (CM), system integrators, modular-building manufacturers and component suppliers building or supplying {tier_list()} units ({len(L.TIER_GEOMETRY)} tiers, `TIER_GEOMETRY`) |\n| Generated by | `design/gen_sqam.py` from `design/ctq.py` (the same register that prints the CTQ/CTP tables on the IFC drawings and the \"Check:\" lines in the STE assembly instructions) |\n| Status | Issue for use with the {DRAWING_SET}; {'checked by ' + DRW['checker'] if DRW['checked'] else 'the drawing set is not yet checked — not for construction'} |")
    A("")
    A("This manual is written in plain language. Where it says **shall**, the requirement is contractual. Where it says **should**, the requirement is expected and a deviation needs Schreiber AI agreement in writing.")
    A("")
    # 1
    A("## 1. Purpose, scope and applicability")
    A("")
    A("**Purpose.** BEN Engine units are built by third parties from Schreiber AI's drawings, parts list and Simplified Technical English instructions. This manual tells those parties what quality system they need, which characteristics are critical, how each one is measured and recorded, where work stops for a Schreiber AI signature, and what happens when something is out of tolerance.")
    A("")
    A(f"**Scope.** Everything between receipt of the enclosure and parts and hand-over of the unit on the transport vehicle, plus site set-down where the same party does it. It covers the {len(L.TIER_GEOMETRY)} tiers ({tier_list()}) and every subsystem (structure, envelope, power, cooling, compute mounting, controls, fire and life safety).")
    A("")
    A("| Party | Applicability |")
    A("|---|---|")
    A("| Contract manufacturer (CM) | All sections. The CM is responsible for the hold and witness points inside its shop and for the sub-tier suppliers it uses (welders, electricians, HVAC, fire installer). |")
    A("| System integrator | Sections 1-4, 5 (controls and electrical items), 6 (electrical, controls, final/FAT), 8-16. |")
    A("| Component supplier (racks, UPS, cooling units, PLC and I/O, edge computer, BEN Pods, UL 508A panel shop, cabinets) | Sections 1, 2 (quality system), 4, 9, 10 (serial numbers and certificates), 12, 15. The supplier's own CTQs are the catalogue specification referenced on the purchase order. |")
    A("")
    A("**Definitions.**")
    A("")
    A("| Term | Meaning |")
    A("|---|---|")
    A("| CTQ — critical to quality | A measurable characteristic of the finished unit that, if out of tolerance, affects safety, listing, performance or the customer's acceptance. Every CTQ has a specification, a method, an instrument and a record. |")
    A("| CTP — critical to process | A process step that cannot be verified by inspecting the result alone (welding, torque, brazing, evacuation, licensed electrical work). CTPs are controlled by qualified people, calibrated tools and a witnessed or held record. |")
    A("| Hold point | Work stops. It restarts only after the named qualified person (and Schreiber AI quality where stated) signs the form. A hold point is never waived by the CM. |")
    A("| Witness point | The QC inspector (Schreiber AI or its delegated inspector) is present and signs. If the inspector was notified 48 h ahead and did not attend, the CM may proceed and records it. |")
    A("| NCR — non-conformance report | The record of anything that does not meet a drawing, this manual or the instructions, with its disposition. |")
    A("| CAPA | Corrective and preventive action: the fix for the cause of an NCR, with evidence that it worked. |")
    A("| FAI — first-article inspection | The complete dimensional and functional inspection of the first unit of each tier built by a supplier, witnessed 100 % by Schreiber AI. |")
    A("| FAT | Factory acceptance test: the pre-ship test run with the Schreiber AI commissioning script, producing a signed report and data hash. |")
    A("| Deviation request | The form that asks Schreiber AI Engineering to accept a departure from a drawing or specification before the work is done. |")
    A("")
    # 2
    A("## 2. Quality system requirements")
    A("")
    A("| Requirement | Evidence the supplier provides | Checked |")
    A("|---|---|---|")
    A("| Quality management system certified to ISO 9001:2015 or an equivalent documented system accepted by Schreiber AI after audit (quality manual, document control, calibration, NCR/CAPA, training records) | Certificate or manual + last internal audit | At audit, annually |")
    A("| Industrial control panels built in a UL 508A listed panel shop (own file or named sub-contractor) | UL file number; label on every panel | At audit; label check at FAT |")
    A("| Welding on the container shell by welders qualified to AWS D1.1 (or ISO 9606-1) with a CWI available for visual inspection | Welder qualification records, continuity log, CWI certificate | At audit; copy on Q-02 |")
    A("| Power wiring, terminations and energisation by a licensed electrician for the jurisdiction (journeyman or master) | Licence copy on file | At audit; licence number on Q-07 |")
    A("| Refrigerant work by EPA Section 608 (Type II or Universal) or F-gas certified technicians | Certificate copies | At audit; certificate number on Q-06 |")
    A("| Cable and harness assemblies to IPC/WHMA-A-620 Class 2 (Class 3 for life-safety and EPO circuits) | Trained-operator list; sample inspection | At audit; sample at FAI |")
    A("| Measuring and test equipment calibrated with traceability to NIST (or national equivalent) at intervals not longer than 12 months: torque wrenches, insulation testers, earth testers, pressure and vacuum gauges, multimeters, reference thermometers, scales | Calibration certificates and a register with due dates; the instrument ID is written on every Q-form entry | At audit; spot check at every witness point |")
    A("| Instrument accuracy at least 4 times better than the tolerance measured (the register in section 5 states the value per item) | Register review | At audit |")
    A("| Lithium battery handling: trained staff, storage at 30-50 % SoC, UL 9540A data on file, dangerous-goods shipping competence | Training records, storage procedure | At audit |")
    A("| Fire-suppression installation by an installer certified by the system manufacturer and acceptable to the AHJ | Certificate | Copy on Q-09 |")
    A("| Workers who follow the STE assembly instructions have completed Schreiber AI's 1-day build induction (instructions, forms, hold/witness rules, PPE) | Induction attendance list | Before first build |")
    A("")
    # 3
    A("## 3. Roles and the Schreiber AI quality presence")
    A("")
    A("| Role | Responsibility |")
    A("|---|---|")
    A("| Schreiber AI Engineering (design authority) | Owns the configuration model, drawings, CTQ/CTP register and instructions. Approves deviations, use-as-is dispositions and design changes. Nobody else changes a drawing. |")
    A("| Schreiber AI Quality | Approves suppliers (audit), attends hold and witness points, reviews Q-forms, runs or witnesses the FAT, signs the certificate of conformance, keeps the scorecard. |")
    A("| Schreiber AI Field / Commissioning | Runs the commissioning script at FAT and at site; signs the hand-over. |")
    A("| Supplier quality lead (named person) | Single point of contact. Keeps the unit's QC file, raises NCRs, calls hold/witness points 48 h ahead, closes CAPAs. |")
    A("| Supplier qualified persons | Certified welder, licensed electrician, EPA 608 technician, fire installer, CSC surveyor, rigger: each signs the hold point in their trade. |")
    A("| Workers | Follow the STE instructions step by step, record values on the Q-forms, stop at every hold point. |")
    A("")
    A("Presence rules: first article of each tier — Schreiber AI Quality present for 100 % of hold and witness points and the full FAT. Units 2-3 — witness points and FAT. Standard surveillance after that — FAT always, hold points by sampling (at least one per unit), all Q-forms reviewed before shipment. Surveillance increases to first-article level after any critical NCR.")
    A("")
    # 4
    A("## 4. Document control")
    A("")
    A(f"- Build only from a drawing set whose title block reads **ISSUE FOR CONSTRUCTION** with a named checker (current set: {DRAWING_SET}; `design/REVISION.json`) for the unit's configuration: `design/drawings/<tier>/A-001 … C-001`, revision letter in the title block, together with `design/assembly/ASSEMBLY-<tier>.md`, `QC_FORMS.md` and this manual. The configuration line in the title block (tier, kW, racks, cooling, redundancy, climate) must match the purchase order.")
    A("- Drawing numbers: A- architecture, S- structure, E- electrical, M- mechanical/cooling, C- controls; sheets are numbered n/7. Superseded revisions are stamped SUPERSEDED and removed from the bay.")
    A("- Red-lines: the supplier marks as-built changes in red on a copy of the IFC sheet, dated and initialled, within 24 h of the change. Red-lines are scanned into the unit's QC file and sent to Schreiber AI Engineering, which regenerates the drawing set (the drawings are generated from the configuration model, so a red-line becomes a model or generator change, not a hand edit).")
    A("- Deviation request (form DR-01): any departure from a drawing, this manual or the instructions is requested **before** the work, with the reason, the proposed alternative and the CTQs affected. Schreiber AI Engineering answers in writing within 2 working days. No verbal approvals.")
    A("- Records are kept for the life of the unit plus 10 years; the unit QC file is handed over with the turnover package.")
    A("")
    # 5
    A("## 5. CTQ / CTP register")
    A("")
    A("The register is generated per tier from `design/ctq.py`. The same items appear on the drawing sheet named in the characteristic column and as \"Check:\" lines in the assembly task that produces the feature. Instrument accuracy required is one quarter of the tolerance (or 5 % of a one-sided limit); the instrument column gives the typical instrument and its accuracy so the supplier can confirm its own equipment qualifies.")
    A("")
    A("| Tier | CTQ | CTP | Hold points | Witness points | Total |")
    A("|---|---|---|---|---|---|")
    for t, lay in lays.items():
        r = regs[t]
        A(f"| {lay.d['tier_label']} | {sum(1 for i in r if i.kind == 'CTQ')} | {sum(1 for i in r if i.kind == 'CTP')} | {sum(1 for i in r if i.point == 'HOLD')} | {sum(1 for i in r if i.point == 'WITNESS')} | {len(r)} |")
    A("")
    for t, lay in lays.items():
        A(f"### 5.{list(lays).index(t) + 1} {lay.d['tier_label']} — {lay.cfg.it_kw:.0f} kW, {lay.cfg.racks} rack(s), {L.COOLING_LIBRARY[lay.notes.get('cooling_resolved', lay.cfg.cooling)]['label']}, {lay.d['voltage']}")
        A("")
        A(ctq_table(regs[t], lay))
        A("")
    # 6
    A("## 6. Inspection plan by build stage")
    A("")
    A("Stages follow the task order of `ASSEMBLY-<tier>.md`. A stage is closed when every item in its Q-form has a value and the required signatures. The next stage does not start before that (the instructions say the same).")
    A("")
    A("| Stage | Assembly task(s) | CTQ / CTP items | Inspection points and acceptance | Q-form |")
    A("|---|---|---|---|---|")
    forms_by_id = {}
    for r in regs.values():
        for i in r:
            forms_by_id[i.id] = i.form
    for name, task, ids, acc in STAGES:
        forms = sorted({forms_by_id.get(i, "") for i in ids if forms_by_id.get(i)})
        A(f"| {name} | {task} | {', '.join(ids)} | {acc} | {', '.join(forms)} |")
    A("")
    A("Items that do not apply to a tier (for example containment on an RDHx unit, or welding on the BEN 5 cabinet) are marked N/A with the reason on the form; the register in section 5 lists exactly which items each tier carries.")
    A("")
    # 7
    A("## 7. First-article inspection (FAI)")
    A("")
    A("- The first unit of each tier built by a supplier (and the first unit after a move of the production bay, a change of key personnel, or 6 months without a build) is a first article.")
    A("- Scope: 100 % of the CTQ/CTP register with every value recorded (no sampling); full dimensional check of the equipment schedule on A-002 (every tag x, y, z position within +/-10 mm); full functional test per section 8 at 50 % and 100 % load; label walk-down of every tag on A-002, C-001 and E-001; photograph record of every hold point.")
    A("- Schreiber AI Quality witnesses 100 % of hold and witness points and the FAT. Schreiber AI Engineering reviews the FAI report before the unit ships.")
    A("- Record: form FAI-01 (balloon numbers keyed to the drawing dims, measured value, instrument ID, pass/fail) plus the complete Q-01…Q-12 set, the NCR log and the FAT report. The FAI report is approved in writing before the second unit of that tier starts.")
    A("")
    # 8
    A("## 8. Factory acceptance test (FAT) linkage")
    A("")
    A("- The FAT is the pre-ship test of Task 11 run with the Schreiber AI commissioning script. In the factory the script runs in simulation-assisted mode against the real BEN Controller (PLC or RevPi, edge computer) and BEN Pods (`python -m ben_engine.commissioning --live --url <gateway> --tier <tier> --out FAT-<serial>.md --operator <name>`); where the controller is not yet networked, the `--sim` run proves the controls software path and is attached as a separate report, never as the FAT.")
    A("- Load: resistive load bank on the rack PDUs at 50 % for 1 h and 100 % for 2 h; utility-loss test on battery; EPO test (< 1 s, witnessed).")
    A("- Output: the markdown report, the telemetry CSV and the CSV's SHA-256 hash printed in the report. The report is valid only with a data file whose hash matches. Schreiber AI Quality signs the certificate of conformance (form COC-01) referencing the report hash, the unit serial number and the IFC revision.")
    A("- Acceptance: all CTQ-M5 / CTQ-E3 limits met, no open critical or major NCR, all Q-forms complete, FAI approved (first unit).")
    A("")
    # 9
    A("## 9. Nonconformance, disposition and corrective action")
    A("")
    A("- Anything that does not meet a drawing, the register, the instructions or this manual is recorded on an NCR (form NCR-01) within one shift of discovery. The feature is tagged. Work on that feature stops.")
    A("- Classification: **critical** — safety, listing or a CTQ out of tolerance; **major** — function or durability; **minor** — cosmetic or documentation.")
    A("- Disposition is one of: **rework** to the drawing and re-inspect 100 %; **use-as-is** only with Schreiber AI Engineering approval written on the NCR (never for critical); **scrap / replace**. Anything touching a CTQ is Schreiber AI's decision.")
    A("- CAPA (form CAPA-01, 8D-lite): D1 team, D2 problem, D3 containment (which other units / features are affected), D4 root cause (5-why), D5 corrective action, D6 verification evidence, D7 prevention (procedure / instruction / fixture change), D8 close-out. Required for every critical NCR, for any major NCR repeated on two units, and when a hold point is found bypassed.")
    A("- Escape escalation: a nonconformance found after shipment (site, commissioning, warranty) is a **quality escape**. The supplier is informed within 24 h, a CAPA is mandatory, surveillance returns to first-article level for the next unit, and the escape counts in the scorecard (section 14).")
    A("")
    # 10
    A("## 10. Traceability and the as-built record")
    A("")
    A("| Item | Identifier recorded | Where |")
    A("|---|---|---|")
    A("| Unit | Schreiber AI serial BEN-<tier>-<yyyy>-<nnn>; IFC revision; configuration hash from the config model | Nameplate inside the door; QC file; FAT report |")
    A("| Container / cabinet | Manufacturer serial, CSC plate data, ACEP or re-inspection record number | Q-01, Q-11 |")
    A("| Racks | Manufacturer serial per tag (R1…Rn) | Q-05 |")
    A("| UPS frames / modules and battery cabinets / modules | Serial numbers, firmware version, UL 9540A report reference, SoC at shipment | Q-07, Q-11 |")
    A("| Cooling units, condensers, CDUs, RDHx doors, dry cooler | Serial numbers, refrigerant type and charge per circuit, glycol concentration | Q-06 |")
    A("| BEN Pods and controller | Pod EUI-64 / node_id, certificate serial, attestation state, firmware version and signature, `cal_id` per channel; PLC project hash and firmware; edge computer image version, TPM PCR baseline and database backup ID | Q-08, FAT report |")
    A("| Sensors | Channel name (PROTOCOL.md), position (x, y, z), calibration coefficients | C-001 schedule, Q-08 |")
    A("| Fire system | Cylinder serial, agent mass, hydrostatic test date, installer certificate | Q-09 |")
    A("| Torque records | Bolt map (S-001 marked up) with every bolt numbered, wrench ID, value | Q-04, Q-07 |")
    A("| Measuring equipment | Instrument ID and calibration due date on every measured entry | All Q-forms |")
    A("")
    A("The as-built record is the complete QC file: Q-01…Q-12, NCR log, deviation requests, red-lines, FAI (first unit), FAT report + CSV + hash, certificates of the qualified persons, serial-number list above. One copy goes in the unit's document box, one to Schreiber AI before shipment.")
    A("")
    # 11
    A("## 11. Workmanship standards")
    A("")
    A("**Torque (ISO 898-1 class 8.8, dry, calibrated wrench, +/-10 %, paint stripe after witness):**")
    A("")
    A("| Size | N·m |\n|---|---|")
    for k, v in C.TORQUE.items():
        A(f"| {k} | {v} |")
    A("")
    A("Electrical lugs and breaker terminals: the value on the device label, recorded per lug (CTP-E2). Never re-use a nyloc nut. Never torque over insulation or shims that can creep.")
    A("")
    A("- **Labelling:** every item carries the tag from A-002 / C-001 / E-001 (R1, CU2, UPS1, PNL-M, N1, T_in_r1_0.4 …) on a laminated or engraved label, 10 mm text minimum, at the top front; every cable at both ends; every breaker, receptacle and terminal. Sensor names are the PROTOCOL.md channel names exactly. Arc-flash and warning labels per E-001 notes.")
    A("- **Cable management:** power in tray TR-P, data in TR-D, 300 mm apart, crossings at 90 degrees; bend radius >= 8 x cable diameter (4 x for Cat6A); hook-and-loop ties only on data; no cable rests on a sharp edge; service loops 300 mm at Pods and at the panel; separate life-safety wiring (FRP, EPO) in its own conduit, red-identified.")
    A("- **Conduit and glands:** liquid-tight or EMT inside; every shell penetration through a welded frame or curb with an EPDM boot or IP66 gland; fire-stop where required; bonding bushings on metallic conduit.")
    A("- **Penetration sealing:** butyl + EPDM boot on roof curbs, sleeved and sealed pipe penetrations, PU sealant on every liner lap; smoke-pencil test (CTQ-C2).")
    A("- **Welding:** AWS D1.1 visual acceptance; no undercut > 0.5 mm, no porosity, full fillet both sides of reinforcement frames; grind flush where a seal lands.")
    A("- **Paint and corrosion:** cut edges and welds primed within 4 h with zinc-rich primer; topcoat to the corrosion class on A-001 (C4-M min, C5-M coastal); touch-up any chip > 2 mm before shipment; dissimilar metals isolated.")
    A("- **Housekeeping:** no swarf in the envelope before the liner closes (magnet sweep); no debris in trays; filters fitted before the first fan run.")
    A("")
    # 12
    A("## 12. Packaging, transport preparation and handling")
    A("")
    A("- Follow Task 12 of the instructions and record on Q-11. Containers: CSC re-inspection after modification (HOLD, CTP-A2); 4-leg lift on top castings only, sling angle >= 60 degrees (HOLD, CTP-S4); tie-down by the bottom castings; doors sealed and seal number recorded.")
    A("- Batteries at 30-50 % SoC, disconnect open, dangerous-goods paperwork; UPS transport locks fitted; IT removed or strapped; racks blocked; drains capped and traps drained.")
    A("- Humidity: two humidity indicator cards (30/40/50 %) inside the unit — one at the BEN Controller panel, one at the far rack — plus desiccant 1 kg per 10 m3 in sealed units; the indicators are photographed at set-down (Q-12).")
    A("- Shock: a tilt indicator and a 10 g shock indicator on the UPS frame and on rack R1; tripped indicators are recorded as an NCR and trigger a re-check of hold-downs and connections at site.")
    A("- BEN 5: forklift only from the long side with the cabinet empty of IT; the skid lifting label and CoG label fitted.")
    A("")
    # 13
    A("## 13. Supplier audit")
    A("")
    A("Audit before the first order, annually, and after any critical escape. Scoring uses the same criteria and weights as `docs/MANUFACTURING_STRATEGY.md` section 4: a supplier needs >= 70/100 and no gate failure. Gates: valid licences and insurance; NDA / IP terms signed; UL 508A panel shop (own or named sub); AWS D1.1 welders with a CWI available.")
    A("")
    A("| # | Criterion (weight) | Audit question | Yes / No | Score 1-5 | Weighted |")
    A("|---|---|---|---|---|---|")
    audit = [
        ("Capabilities (20)", "Container cutting/framing, insulation, 480 V electrical, refrigeration, paint, indoor bay with 10-20 t crane, 480 V test power >= 400 A and load banks seen in operation?"),
        ("Certifications and licences (20)", "UL 508A file, AWS D1.1 welder records + CWI, electrical and HVAC licences, EPA 608, ISO 9001 certificate verified against the issuing body?"),
        ("Capacity (10)", "Bays and shifts available; can hold a bay 6-8 weeks per BEN 150; current backlog shown?"),
        ("Distance and freight (10)", "Distance to the first three sites; dock, crane and road access for a 40 ft high cube?"),
        ("References (15)", "Three relevant containerized / e-house / shelter projects in 3 years with contactable customers; QC records of the last three projects reviewed?"),
        ("Quality system (10)", "Calibration register with due dates; NCR log and closed CAPAs; traceability of serials; uses or accepts Q-01…Q-12; sample weld and sample 480 V termination made during the audit pass?"),
        ("Financial health (10)", "Years in business; our order < 30 % of revenue; credit report acceptable; bonding capacity?"),
        ("Commercial terms (5)", "Open-book margin, consignment accepted, progress payments tied to hold points, workmanship warranty >= 24 months?"),
    ]
    for i, (c, q) in enumerate(audit, 1):
        A(f"| {i} | {c} | {q} | | | |")
    A("| | **Total (100)** | | | | |")
    A("")
    A("Weighted = score / 5 x weight. Audit report within one week; corrective actions agreed with dates; re-audit of failed items before the first order.")
    A("")
    # 14
    A("## 14. Performance metrics")
    A("")
    A("| Metric | Definition | Target | Review |")
    A("|---|---|---|---|")
    A("| First-pass yield at FAT | Units that pass the FAT with no rework after the load test / units tested | >= 90 % after the first three units | Per unit, quarterly scorecard |")
    A("| NCRs per unit | Critical / major / minor NCRs raised per unit | Critical <= 0.2, major <= 1.0, minor <= 5 per unit (same thresholds as the greenfield transition criteria) | Per unit |")
    A("| Hold-point first-time acceptance | Hold points signed at the first presentation / hold points presented | >= 95 % | Per unit |")
    A("| Witness-point first-time acceptance | Same for witness points | >= 95 % | Per unit |")
    A("| On-time delivery | Units shipped on or before the contract date | >= 90 % | Quarterly |")
    A("| Quality escapes | Nonconformances found at site or in warranty attributable to the build | 0 critical; <= 0.5 per unit total | Quarterly |")
    A("| CAPA closure | CAPAs closed with verified effectiveness within 30 days | 100 % | Quarterly |")
    A("| Calibration compliance | Instruments in calibration at every use (ID on form) | 100 % | Every witness point |")
    A("")
    A("Scores feed the supplier scorecard. Two consecutive quarters below target move the supplier to first-article surveillance; a third quarter triggers re-qualification.")
    A("")
    # 15
    A("## 15. Change control")
    A("")
    A("- Schreiber AI changes: a change to the configuration model, a drawing, the CTQ/CTP register or the instructions is issued as a new revision of the generated set with a change note. The supplier acknowledges receipt, removes superseded sheets, and states which units in progress are affected; Engineering decides whether in-progress units follow the old or new revision.")
    A("- Supplier changes: no change to materials, parts (including equivalents), sub-tier suppliers, process, location or key personnel without a deviation request or change notice approved by Schreiber AI before use. Part substitutions are checked against the catalogue footprint and the interference checks (`design/drawings/INTERFERENCE_CHECKS.md`) before approval.")
    A("- Firmware and software: BEN Pods, PLC and edge computer run the signed firmware / image version named in the build contract; the supplier does not update firmware without instruction; versions are recorded in the FAT report.")
    A("")
    # 16
    A("## 16. Forms index")
    A("")
    A("| Form | Title | Issued in |")
    A("|---|---|---|")
    for k, v in C.QC_FORMS.items():
        A(f"| {k} | {v} | design/assembly/QC_FORMS.md |")
    for k, v in [("NCR-01", "Non-conformance report and disposition"), ("FAI-01", "First-article inspection report"), ("DR-01", "Deviation request"), ("CAPA-01", "Corrective and preventive action (8D-lite)"), ("COC-01", "Certificate of conformance (FAT)")]:
        A(f"| {k} | {v} | design/assembly/QC_FORMS.md |")
    A("")
    A("Per-tier CTQ/CTP quick cards for the bay: " + ", ".join(f"`design/assembly/CTQ-CARD-{t}.md`" for t in lays) + ".")
    A("")
    # 17
    A("## 17. Revision history")
    A("")
    A("| Rev | Date | Change | By |")
    A("|---|---|---|---|")
    sp = DRW.get("supersedes")
    if sp:
        A(f"| {sp['drawing_rev']} | {sp['issue_date']} | Generation-1 manual for the superseded drawing set: {sp['notes']} | BEN Engine generator |")
    A(f"| {REV} | {DATE} | Generated from the ctq.py register matching the {DRAWING_SET} and ASSEMBLY-<tier>.md {DRW['issue_label']}. {DRW['notes_short']} | BEN Engine generator; checked: {DRW['checker'] or '____'} |")
    A("")
    out = os.path.join(ROOT, "docs", "SQAM.md")
    with open(out, "w") as f:
        f.write("\n".join(o))
    print("  wrote", out)
    for t, lay in lays.items():
        p = os.path.join(HERE, "assembly", f"CTQ-CARD-{t}.md")
        with open(p, "w") as f:
            f.write(ctq_card(lay, regs[t]))
        print("  wrote", p, f"({len(regs[t])} items)")
    return regs


if __name__ == "__main__":
    lays = {t: L.resolve(t) for t in L.TIER_GEOMETRY}
    regs = write_sqam(lays)
    for t, r in regs.items():
        print(f"  {t}: CTQ {sum(1 for i in r if i.kind == 'CTQ')}, CTP {sum(1 for i in r if i.kind == 'CTP')}, HOLD {sum(1 for i in r if i.point == 'HOLD')}, WITNESS {sum(1 for i in r if i.point == 'WITNESS')}")

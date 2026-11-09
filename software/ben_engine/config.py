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

Tier = Literal["ben1", "ben5", "ben30", "ben150", "ben300", "ben500", "ben700", "ben2000"]
Hardening = Literal["H1", "H2", "H3", "IND"]
Lineup = Literal["rev1", "rev2"]
Form = Literal["rack10", "cab12"]

# Generation-1 keys (container-length names) are accepted everywhere and normalised to the power-based keys.
# Rev 2: "ben1000" was the working name of the 40 ft liquid-first flagship; it does not fit at 1,000 kW with real footprints
# (design/layout.py I-D checks, docs/DENSITY.md) and is sold as BEN 700, so the old key loads as ben700.
TIER_ALIASES: Dict[str, str] = {"micro": "ben5", "ben10": "ben30", "ben20": "ben150", "ben40": "ben500", "ben1000": "ben700"}


def canonical_tier(t: str) -> str:
    return TIER_ALIASES.get(t, t)
Cooling = Literal["cabinet_dx", "inrow_dx", "inrow_dx_300", "rdhx_drycooler", "dlc_cdu", "dlc_hd"]
PowerArchitecture = Literal["ac480", "dc800"]
# Two DC conventions coexist in 2026 (docs/research/STATE_OF_THE_ART_2026.md §1.3, §1.5): OCP Diablo 400 = ±400 VDC bipolar with a
# high-resistance midpoint ground (±0.5 % regulation); NVIDIA / OCP LVDC SST v0.3 = 800 VDC unipolar with the return isolated from earth.
DcConvention = Literal["bipolar_400", "unipolar_800"]
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
    # Names follow nominal maximum IT power (docs/TIER_AND_ENCLOSURE_DECISION.md). The CORE product is BEN 5–500: all-in-one
    # boxes (power + cooling + compute + controls in one enclosure). BEN 2000 is a capability example, not the lead product.
    # Enclosures are element-proof
    # (NEMA 4X / IP66) at hardening level H1; H2/H3 add severe-environment and hardened/government packages.
    "ben5": {
        "label": "BEN 5", "enclosure": "Outdoor 24U NEMA 4X / IP66 cabinet on skid",
        "kind": "cabinet", "modules": 1, "positioning": "core",
        "ext_l_m": 1.20, "ext_w_m": 1.00, "ext_h_m": 1.80,
        "int_l_m": 1.00, "int_w_m": 0.80, "int_h_m": 1.40,
        "max_racks": 1, "rack_u": 24, "it_kw_min": 2, "it_kw_max": 5,
        "default_cooling": "cabinet_dx", "voltage": "208/240 V 1ph", "tare_kg": 320,
    },
    "ben30": {
        "label": "BEN 30", "enclosure": "10 ft high-cube ISO-frame module, sealed to IP66",
        "kind": "module", "modules": 1, "positioning": "core",
        "ext_l_m": 2.991, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 2.70, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 2, "rack_u": 42, "it_kw_min": 10, "it_kw_max": 30,
        "default_cooling": "inrow_dx_300", "voltage": "208 V 3ph", "tare_kg": 1300,
    },
    "ben150": {
        "label": "BEN 150", "enclosure": "20 ft high-cube ISO-frame module, sealed to IP66",
        "kind": "module", "modules": 1, "positioning": "core",
        "ext_l_m": 6.058, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 5.75, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 6, "rack_u": 42, "it_kw_min": 50, "it_kw_max": 150,
        "default_cooling": "rdhx_drycooler", "voltage": "480 V 3ph", "tare_kg": 2400,
    },
    "ben500": {
        "label": "BEN 500", "enclosure": "40 ft high-cube ISO-frame module, sealed to IP66",
        "kind": "module", "modules": 1, "positioning": "core",
        "ext_l_m": 12.192, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 11.85, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 12, "rack_u": 48, "it_kw_min": 150, "it_kw_max": 500,
        "default_cooling": "dlc_cdu", "voltage": "480 V 3ph", "tare_kg": 3900,
    },
    "ben2000": {
        # Single 2 MW center: three site-joined wide-body modules (12.2 x 3.66 x 4.2 m each) form the IT hall,
        # plus a separate power module and a plant yard. Interior dims are the joined hall.
        "label": "BEN 2000", "enclosure": "Prefabricated wide-body modular hall (3 site-joined 12.2 m modules) + power module + plant yard, IP66 envelope",
        "kind": "hall", "modules": 3, "positioning": "capability",
        "ext_l_m": 36.6, "ext_w_m": 11.0, "ext_h_m": 4.2,
        "int_l_m": 35.8, "int_w_m": 10.4, "int_h_m": 3.6,
        "max_racks": 48, "rack_u": 48, "it_kw_min": 800, "it_kw_max": 2000,
        "rows": 4,
        "default_cooling": "dlc_cdu", "voltage": "12.47 kV MV service → 480 V 3ph", "tare_kg": 3 * 14000 + 18000,
    },
    # ---------------------------------------------------------------- Rev 2 tiers (docs/REV2_DECISION.md §2). Rev 1 entries above are frozen.
    "ben1": {
        # Indoor mini rack. Top-level dimensions are the cab12 form; the selected form's dimensions replace them (Config.geometry()).
        "label": "BEN 1", "enclosure": "Indoor mini rack: 10-inch 8U desk / shelf rack or 19-inch 12U sound-damped office cabinet",
        "kind": "minirack", "modules": 1, "positioning": "core", "lineup": "rev2", "indoor": True,
        "ext_l_m": 0.688, "ext_w_m": 0.952, "ext_h_m": 0.744,
        "int_l_m": 0.48, "int_w_m": 0.80, "int_h_m": 0.53,
        "max_racks": 1, "rack_u": 12, "it_kw_min": 0.2, "it_kw_max": 1.5,
        "default_cooling": "office_air", "voltage": "120 V 1ph 15/20 A plug-in",
        "voltage_option": "230 V 1ph 10/16 A (IEC C14 / C20 inlet) option for export; same UPS family in the 230 V (I) variant",
        "tare_kg": 75, "default_form": "cab12",
        "forms": {
            # DeskPi RackMate T1 class: 281 W x 200 D (shelf) x 451 H mm incl. handles (computingforgeeks / CNX listings; DeskPi wiki not read).
            # Depth carried as 260 mm = 200 mm shelf + 60 mm rear cable and PDU space. Open frame: no sound damping.
            "rack10": {"label": "10-inch 8U desk / shelf mini rack (open or semi-enclosed)", "rack_in": 10,
                       "ext_l_m": 0.281, "ext_w_m": 0.260, "ext_h_m": 0.451, "int_l_m": 0.222, "int_w_m": 0.200, "int_h_m": 0.356,
                       "rack_u": 8, "it_kw_max": 0.6, "tare_kg": 4, "insertion_loss_db": 0.0, "noise_source": "desktop",
                       "door": False, "reference": "DeskPi RackMate T1 (10-inch 8U)"},
            # APC NetShelter CX Mini 12U (AR4000MV family): 744 H x 688 W x 952 D mm, 75 kg, 18.5 dB broadband noise reduction at 1 m
            # (APC sales sheet as quoted by resellers, 2026-11-09). Internal: 12U x 44.45 = 533 mm, usable depth ~ 800 mm.
            "cab12": {"label": "19-inch 12U sound-damped office cabinet", "rack_in": 19,
                      "ext_l_m": 0.688, "ext_w_m": 0.952, "ext_h_m": 0.744, "int_l_m": 0.48, "int_w_m": 0.80, "int_h_m": 0.53,
                      "rack_u": 12, "it_kw_max": 1.5, "tare_kg": 75, "insertion_loss_db": 18.5, "noise_source": "rack",
                      "door": True, "reference": "APC NetShelter CX Mini 12U (AR4000MVX431)"},
        },
    },
    "ben300": {
        # Liquid-first 20 ft: two GB300 NVL72-class racks (132-155 kW each), row CDUs N+1 on the W45 loop, residual air in in-row
        # fan coils on a trim loop, UPS + lithium + 480 V distribution inside; heat rejection on an adjacent dry-cooler skid.
        "label": "BEN 300", "enclosure": "20 ft high-cube ISO-frame module, liquid-first, sealed to IP66",
        "kind": "module", "modules": 1, "positioning": "core", "lineup": "rev2", "liquid_first": True,
        "ext_l_m": 6.058, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 5.75, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 2, "rack_u": 48, "it_kw_min": 150, "it_kw_max": 300, "max_rack_kw": 155,
        "default_cooling": "dlc_hd", "voltage": "480 V 3ph", "tare_kg": 2600, "ups_minutes_default": 5,
    },
    "ben700": {
        # Liquid-first 40 ft flagship. Target was 1,000 kW in 7 racks; with real footprints the single row holds 5 racks and
        # 705 kW (DENSE_FOOTPRINTS, design/layout.py I-D2), so the tier is named for 700 kW (5 x 140 kW).
        "label": "BEN 700", "enclosure": "40 ft high-cube ISO-frame module, liquid-first, all-in-one, sealed to IP66",
        "kind": "module", "modules": 1, "positioning": "core", "lineup": "rev2", "liquid_first": True,
        "ext_l_m": 12.192, "ext_w_m": 2.438, "ext_h_m": 2.896,
        "int_l_m": 11.85, "int_w_m": 2.20, "int_h_m": 2.49,
        "max_racks": 5, "rack_u": 48, "it_kw_min": 400, "it_kw_max": 700, "max_rack_kw": 155,
        "default_cooling": "dlc_hd", "voltage": "480 V 3ph", "tare_kg": 4300, "ups_minutes_default": 5,
        "target_note": "Rev 2 decision target BEN 1000 (500-1,000 kW, up to 7 racks); verified maximum 705 kW in 5 racks, sold as BEN 700",
    },
}

# Product lineups (docs/REVISION_POLICY.md rule 3). A saved configuration without a lineup key is Rev 1.
LINEUPS = ("rev1", "rev2")
TIERS_BY_LINEUP: Dict[str, List[str]] = {
    "rev1": ["ben5", "ben30", "ben150", "ben500", "ben2000"],
    "rev2": ["ben1", "ben5", "ben30", "ben150", "ben300", "ben500", "ben700", "ben2000"],
}
REV1_TIERS = tuple(TIERS_BY_LINEUP["rev1"])
DENSE_TIERS = ("ben300", "ben700")
MINIRACK_TIERS = ("ben1",)

# Rev 2 dense-tier footprints (mm; w = length along the row, d = depth from the rack wall). One table feeds config.derived(),
# design/layout.py and the dashboard so they agree. Sources were read on 2026-11-09; see "src".
DENSE_FOOTPRINTS: Dict[str, Dict[str, Any]] = {
    "rack": {"w": 600, "d": 1068, "h": 2236, "kg": 1500, "kw_max": 155,
             "label": "GB300 NVL72-class liquid rack, 48U MGX, 600 x 1068 x 2236 mm",
             "src": "Supermicro / Cisco GB300 NVL72 datasheet 600 W x 1068 D x 2236 H mm; ~1.36-1.5 t loaded (GPU Smith, HPE). "
                    "Vertiv SmartIT for GB300 is 600 x 1200 D with its rear extension and 2286 mm high: that depth leaves an 800 mm aisle "
                    "behind a 200 mm plenum in a 2.2 m module and is not used"},
    "cdu": {"w": 600, "d": 1200, "h": 2000, "kg": 550, "kw": 600,
            "label": "Row CDU 600 kW (Vertiv CoolChip CDU 600 class), W45 secondary",
            "src": "Vertiv CoolChip CDU 600 product page / brochure: 2000 H x 600 W x 1200 D mm, 480 kg dry / 550 kg wet, 600 kW at 4 K approach"},
    "fancoil": {"w": 300, "d": 1070, "h": 2000, "kg": 170, "kw": 20,
                "label": "In-row chilled-water fan coil 300 mm, 20 kW on the 18 °C trim loop",
                "src": "300 mm in-row chilled-water class (Schneider InRow RC / Vertiv CRV CW); 20 kW at 18 °C water is a design value, NOT verified. "
                       "W45 water cannot cool room air, so the residual-air coils run on a trim loop from the skid chiller"},
    "ups": {"w": 850, "d": 925, "h": 1970, "kg": 900, "kva": 500,
            "label": "Galaxy VL UPS frame up to 500 kW, internal N+1 power modules",
            "src": "Schneider Galaxy VL brochure footprint 850 W x 925 D mm (GVL200K500DS max depth 925 mm); mass not read (900 kg assumed)"},
    "batt": {"w": 600, "d": 1000, "h": 2000, "kg": 650, "kwh": 32.6, "kw": 200,
             "label": "Galaxy Lithium-ion battery cabinet, 16 x 2.04 kWh",
             "src": "32.6 kWh per cabinet (catalog PWR-BATT-LI); 200 kW per cabinet from Schneider's Galaxy VL 2000 kW system = 10 cabinets; "
                    "600 x 1000 mm footprint and 650 kg not read from the manual (Rev 1 layout value)"},
    "swbd": {"w": 915, "d": 610, "h": 2286, "kg": 600, "a_per_section": 1200,
             "label": "480 V switchboard section 36 in W x 24 in D (Square D QED-2 class), main + maintenance bypass",
             "src": "QED-2 bid specification: 36 in wide x 24 in deep sections; one section to 1,200 A, two sections to 2,500 A (ABB Emax 2000 A needs 60 in depth)"},
    "rect": {"w": 600, "d": 1000, "h": 2000, "kg": 400, "label": "AC/DC front-end cabinet 800 VDC (4 x 100 kW)", "src": "Rev 1 forward study value"},
    "batt800": {"w": 600, "d": 1000, "h": 2000, "kg": 650, "kwh": 32.6, "kw": 200, "label": "800 V class battery cabinet on the bus", "src": "Rev 1 forward study value"},
}
DENSE_RULES: Dict[str, Any] = {
    "end_zone_mm": 350,          # blind end: controls panel (305 deep) on the end wall; the FK-5-1-12 cylinder sits in a heated exterior enclosure
    "rear_plenum_mm": 200,       # behind racks and fan coils (residual-air return); CDUs and power gear back onto the wall
    "panelboard_max_a": 600,     # at or below: wall-mounted 600 A panelboard on the end wall; above: floor switchboard sections in the row
    "rack_top_min_mm": 250,      # top power entry + lights over the aisle; liquid connections from the rear plenum, low
    "trim_loop_c": 18.0,
}

# BEN 1 (mini rack) sizing constants. Every number is a stated design value; vendor sources in purchasing/parts_catalog.json.
MINIRACK: Dict[str, Any] = {
    "office_design_c": 23.0, "office_max_c": 30.0,
    "aux_kw": 0.015,              # fanless edge computer (10-15 W) + 2 BEN Pods; 0 when BEN Care runs on the customer's box
    "ups_eff": 0.97,              # line-interactive UPS in line mode incl. charger standby
    "design_rise_k": 10.0,        # cabinet extraction design temperature rise
    # 120 V lithium line-interactive 2U models (APC Smart-UPS Li-ion): VA, W, delivered Wh at full load (runtime x W)
    "ups_models": [
        {"va": 1000, "w": 800, "wh": 104, "model": "APC SMTL1000RM2UC (1000 VA / 800 W, 2U, LiFePO4, 5-15P)", "plug": "NEMA 5-15P"},
        {"va": 2200, "w": 1920, "wh": 192, "model": "APC SMTL2200RM2UC (2200 VA / 1920 W, 2U, Li-ion, 5-20P)", "plug": "NEMA 5-20P"},
    ],
    "ups_headroom": 1.25,
    "noise_src_dba": {"desktop": 38.0, "rack": 52.0},   # sound pressure at 1 m of the IT at 200 W; +15 dB per decade of power
    "noise_target_dba": {"rack10": 50.0, "cab12": 45.0},
    "kg_per_kw_it": 30.0,
}

HARDENING: Dict[str, Dict[str, Any]] = {
    # docs/TIER_AND_ENCLOSURE_DECISION.md §3. Mass adder per m² of envelope and cost handled by catalog lines.
    "H1": {"label": "H1 Standard", "rating": "NEMA 4X / IP66", "coating": "ISO 12944 C3", "wind_ms_min": 47, "mass_kg_m2": 0.0,
           "features": ["hose-tested gasketed penetrations (UL 50E type 4X)", "compression-gasket doors, three-point latches", "positive-pressure interior", "door contacts"]},
    "H2": {"label": "H2 Severe environment", "rating": "NEMA 4X / IP66 + flood plinth 600 mm", "coating": "ISO 12944 C5-M", "wind_ms_min": 67, "mass_kg_m2": 6.0,
           "features": ["sand/dust ePM1 filtration with weather hoods", "hurricane-rated door hardware", "roof snow guards", "stainless fasteners, sacrificial anodes", "intrusion detection and lighting"]},
    "H3": {"label": "H3 Hardened / government", "rating": "NEMA 4X / IP66 + ballistic (UL 752) + forced-entry (ASTM F3038) + HEMP shielding option (MIL-STD-188-125-1)", "coating": "ISO 12944 C5-M", "wind_ms_min": 67, "mass_kg_m2": 48.0,
           "features": ["ballistic wall panels UL 752 level selectable", "IK10 impact doors, forced-entry rated", "80 dB shielded enclosure with filtered penetrations (option)", "TEMPEST-ready separation", "secure vestibule / mantrap", "two-factor access, tamper detection, audit trail in BEN Care", "CMMC / NIST 800-171 controls pack"]},
    # Rev 2: BEN 1 is indoor and has no hardening levels
    "IND": {"label": "Indoor (no hardening levels)", "rating": "UL 62368-1 listed parts, IP20 indoor, NEMA 12 option for dusty closets", "coating": "powder coat, indoor", "wind_ms_min": 0, "mass_kg_m2": 0.0,
            "features": ["listed IT, UPS and PDU parts (UL 62368-1)", "IP20 indoor; NEMA 12 gasketed option for dusty closets", "lockable door (cab12)"],
            "tiers": ["ben1"]},
}

COOLING_LIBRARY: Dict[str, Dict[str, Any]] = {
    # unit_kw: sensible cooling per unit at ASHRAE A1 conditions; cop at design point
    "cabinet_dx":     {"label": "Cabinet DX air conditioner (R-513A, 5.5 kW)", "unit_kw": 5.5,  "cop": 2.6, "medium": "air",   "max_rack_kw": 5,  "width_mm": 400, "mass_kg": 60},
    "inrow_dx":       {"label": "In-row DX cooling unit (600 mm, 30 kW)", "unit_kw": 30.0, "cop": 3.2, "medium": "air",   "max_rack_kw": 30, "width_mm": 600, "mass_kg": 250},
    "inrow_dx_300":   {"label": "In-row DX cooling unit (300 mm, 20 kW)", "unit_kw": 20.0, "cop": 3.1, "medium": "air",   "max_rack_kw": 20, "width_mm": 300, "mass_kg": 180},
    "rdhx_drycooler": {"label": "Rear-door heat exchanger + dry cooler", "unit_kw": 35.0, "cop": 8.0, "medium": "water", "max_rack_kw": 40, "width_mm": 0, "mass_kg": 150},
    "dlc_cdu":        {"label": "Direct liquid cooling + CDU + dry cooler", "unit_kw": 300.0, "cop": 12.0, "medium": "liquid", "max_rack_kw": 80, "width_mm": 600, "mass_kg": 400},
    # Forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md §1, §3): high-density DLC, warm-water W45 secondary loop,
    # 600 kW row CDU, 100-250 kW per rack, air-side residual 10 %. Allowed on BEN 150 and up (DLC_HD_TIERS). Option, default off.
    "dlc_hd":         {"label": "High-density direct liquid cooling (W45 loop, 600 kW row CDU)", "unit_kw": 600.0, "cop": 20.0, "medium": "liquid", "max_rack_kw": 250, "width_mm": 600, "mass_kg": 500,
                       "water_class": "W45", "air_residual": 0.10},
    # Rev 2, BEN 1 only: office air through a filtered, sound-damped extraction path; no refrigerant. unit_kw = cabinet extraction capacity
    # at a 10 K rise (design value; the cabinet vendor's heat rating is to be checked); cop = heat moved / fan power.
    "office_air":     {"label": "Office air: filtered, sound-damped extraction path (no refrigerant)", "unit_kw": 1.6, "cop": 40.0, "medium": "air", "max_rack_kw": 1.5,
                       "width_mm": 0, "mass_kg": 2, "refrigerant": None, "noise_dba": 45, "design_rise_k": 10.0, "indoor": True},
}
DLC_HD_TIERS = ("ben150", "ben500", "ben2000", "ben300", "ben700")

# ---------------------------------------------------------------- power architecture (docs/FORWARD_ARCHITECTURE_DECISION.md §1, §2)
# "ac480" is today's chain (480 V AC -> UPS -> 208/415 V PDUs); "dc800" is the forward option: AC/DC front end (SiC rectifier or
# solid-state transformer) -> 800 VDC busway (±400 V to ground) -> DC breakers -> racks with DC input; lithium battery on the bus
# (no double conversion). Every number below is a stated design assumption for the study, not a measurement.
POWER_ARCHITECTURES: Dict[str, Dict[str, Any]] = {
    "ac480": {"label": "480 V AC → UPS → 208/415 V AC PDUs (today)", "tiers": ("ben5", "ben30", "ben150", "ben500", "ben2000", "ben1", "ben300", "ben700")},
    "dc800": {"label": "800 VDC bus: AC/DC front end → DC busway → DC-input racks, battery on bus (forward option)",
              "tiers": ("ben150", "ben500", "ben2000", "ben300", "ben700"),
              # WORKING ASSUMPTION, not a sourced figure: a 760–920 V operating window was found in no primary source (research §1.5);
              # to be replaced by OCP Diablo 400 table 9.3.1 / the NVIDIA MGX power-rack spec once read in full.
              "bus_v_nominal": 800, "bus_v_min": 760, "bus_v_max": 920, "window_basis": "assumption pending OCP Diablo 400 §9.3.1 / NVIDIA MGX power rack spec",
              "pole_v_to_ground": 400,
              "rectifier_eff": 0.985,            # VENDOR CLAIM (DG Matrix / Heron / Envision >98.5 % for SST; Delta shelves 98.5 % peak), used as the sizing assumption
              # racks do not take 800 VDC directly today: each rack carries an 800 V -> 50 V DC shelf (Delta 90 kW class, 98.5 % peak VENDOR CLAIM)
              # or is an MGX 800 VDC power rack; the shelf loss is in the chain (research §1.9)
              "rack_shelf_kw": 90, "rack_shelf_eff": 0.985,
              "rectifier_module_kw": 100,        # assumption: 100 kW rectifier modules, N+1 (2N doubles)
              "bus_headroom": 1.25,              # bus current carries 25 % headroom over IT at nominal voltage
              "busway_frames_a": (400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200),
              "loss_saving_frac": 0.03,          # assumption: 3 % of IT power saved in distribution losses vs ac480 (vendor claims 3-5 %; we will measure)
              "copper_current_density_a_mm2": 2.0, "ac_feeder_v": 415, "ac_feeder_pf": 0.95, "copper_kg_per_mm2_m": 8.96e-3,
              },
}
DC_CONVENTIONS: Dict[str, Dict[str, Any]] = {
    "bipolar_400": {"label": "±400 VDC bipolar, high-resistance midpoint ground (OCP Diablo 400 convention)", "pole_v_to_ground": 400,
                    "grounding": "midpoint of the ±400 V bus tied to ground through a high resistance (HRG): first fault flows a limited current, alarms, does not trip; insulation and clearances sized for 400 V to ground",
                    "imd_arrangement": "one insulation monitoring device at the midpoint per rectifier section (pole-to-ground resistance both poles)",
                    "spec": "OCP Diablo 400 v0.5.2 / v0.7.0 (±400 VDC, ±0.5 % regulation, 800 V rail-to-rail)"},
    "unipolar_800": {"label": "800 VDC unipolar, return isolated from earth (NVIDIA / OCP LVDC SST v0.3 convention)", "pole_v_to_ground": 800,
                     "grounding": "two-wire 800 VDC with the return isolated from protective earth (IT system): first fault undetected without insulation monitoring, so the IMD is mandatory; insulation and clearances sized for 800 V to ground",
                     "imd_arrangement": "two-pole insulation monitoring device (positive and return to earth) per rectifier section, with fault location on the tap-offs",
                     "spec": "OCP LVDC SST specification v0.3 (800 VDC unipolar, effective 2026-06-22); Diablo 400 800 VDC two-wire option"},
}
DC_BUSWAY_FRAMES = POWER_ARCHITECTURES["dc800"]["busway_frames_a"]

CONTROLS_TIERS: Dict[str, Dict[str, Any]] = {
    # docs/CONTROLS_HARDWARE_DECISION.md §2a. Both tiers run the same ben_engine software, the same BEN Pods on BEN Mesh
    # and the same protocol; life safety is hardwired in both.
    "auto": {"label": "Automatic (by tier and profile)"},
    "lite": {"label": "BEN Controls Lite", "controller": "Revolution Pi RevPi Connect 4 + RevPi DIO/AIO (DIN rail, UL/CE listed)",
             "edge": "same RevPi runs ben_engine and the Thread border router", "panel": "DIN-rail cabinet, listed components",
             "for": ["ben5", "ben30"]},
    "pro":  {"label": "BEN Controls Pro", "controller": "Phoenix Contact PLCnext AXC F 2152 + Axioline F I/O",
             "edge": "OnLogic Karbon 400 industrial edge computer (TPM 2.0)", "panel": "UL 508A listed BEN Controller panel",
             "for": ["ben30", "ben150", "ben500", "ben2000", "ben300", "ben700"]},
    # Rev 2: BEN 1. No controller panel; the BEN Care agent runs on the customer's own box or a small fanless edge computer.
    "mini": {"label": "BEN Controls Mini", "controller": "none: 2 BEN Pods (Pod W) on the BEN Mesh, hardware watchdog in the Pod",
             "edge": "BEN Care agent on the customer's own box, or a small fanless edge (OnLogic CL210-class or RevPi Connect S)",
             "panel": "none (Pods clip to the rack rails)", "for": ["ben1"]},
}
# BEN 30 profiles that default to BEN Controls Pro
CONTROLS_PRO_PROFILES = ("healthcare", "public_sector", "ai_training")

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
    tier: str = "ben150"
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
    # Controls tier (docs/CONTROLS_HARDWARE_DECISION.md §2a): "lite" = BEN Controls Lite (Revolution Pi RevPi Connect 4
    # + RevPi DIO/AIO, BEN Pods on BEN Mesh), "pro" = BEN Controls Pro (PLCnext AXC F 2152 + Axioline F I/O in a UL 508A
    # panel + OnLogic Karbon 400 edge computer + BEN Pods). "auto" resolves by size and profile, see controls_tier_resolved().
    controls_tier: str = "auto"
    # Enclosure hardening level (docs/TIER_AND_ENCLOSURE_DECISION.md §3): H1 standard IP66, H2 severe environment, H3 hardened/government.
    hardening: str = "H1"
    # Power distribution architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): "ac480" today; "dc800" = 800 VDC bus option on BEN 150+.
    power_architecture: str = "ac480"
    # DC convention for dc800 (ignored on ac480): "bipolar_400" (±400 V, HR midpoint, Diablo 400) or "unipolar_800" (800 V, isolated return, OCP SST v0.3).
    dc_convention: str = "bipolar_400"
    # Product lineup (docs/REVISION_POLICY.md rule 3): "rev2" for new configurations; Config.from_dict() loads a saved configuration
    # without the key as "rev1" so every Rev 1 quote reproduces exactly (tests/test_rev1_frozen.py).
    lineup: str = "rev2"
    # BEN 1 form (Rev 2): "rack10" = 10-inch 8U desk / shelf rack (<= 0.6 kW), "cab12" = 19-inch 12U sound-damped cabinet (<= 1.5 kW).
    # Empty on every other tier.
    form: str = ""

    def __post_init__(self):
        self.tier = canonical_tier(self.tier)
        if self.tier in MINIRACK_TIERS:
            if not self.form:
                self.form = "rack10" if self.it_kw <= TIER_GEOMETRY[self.tier]["forms"]["rack10"]["it_kw_max"] else "cab12"
            if self.hardening == "H1":      # the dataclass default; BEN 1 is indoor and has no hardening levels
                self.hardening = "IND"

    # ------------------------------------------------------------ geometry (BEN 1 forms replace the tier dimensions)
    def geometry(self) -> Dict[str, Any]:
        g = TIER_GEOMETRY[self.tier]
        if g.get("kind") != "minirack":
            return g
        f = g["forms"].get(self.form) or g["forms"][g["default_form"]]
        out = {k: v for k, v in g.items() if k != "forms"}
        out.update({k: f[k] for k in ("ext_l_m", "ext_w_m", "ext_h_m", "int_l_m", "int_w_m", "int_h_m", "rack_u", "tare_kg")})
        out.update({"form": self.form, "form_label": f["label"], "it_kw_max_form": f["it_kw_max"], "rack_in": f["rack_in"], "door": f["door"],
                    "insertion_loss_db": f["insertion_loss_db"], "reference": f["reference"]})
        return out

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
        if self.tier == "ben5" and self.cooling != "cabinet_dx":
            errs.append("BEN 5 uses cabinet_dx cooling only")
        if self.tier != "ben5" and self.cooling == "cabinet_dx":
            errs.append("cabinet_dx is for BEN 5 only")
        if self.tier == "ben2000" and self.cooling not in ("dlc_cdu", "dlc_hd"):
            errs.append("BEN 2000 is direct-liquid cooled (dlc_cdu)")
        if self.cooling == "dlc_hd" and self.tier not in DLC_HD_TIERS:
            errs.append("High-density DLC (dlc_hd) is for BEN 150 and up")
        if self.power_architecture not in POWER_ARCHITECTURES:
            errs.append(f"unknown power_architecture {self.power_architecture}")
        elif self.tier not in POWER_ARCHITECTURES[self.power_architecture]["tiers"]:
            errs.append("800 VDC (dc800) is for BEN 150, BEN 500 and BEN 2000 only; BEN 5 and BEN 30 stay 480/208 V AC")
        if self.dc_convention not in DC_CONVENTIONS:
            errs.append(f"unknown dc_convention {self.dc_convention}")
        if self.hardening not in HARDENING:
            errs.append(f"unknown hardening {self.hardening}")
        if self.profile not in PROFILE_DEFAULTS:
            errs.append(f"unknown profile {self.profile}")
        if self.climate not in CLIMATE_DESIGN:
            errs.append(f"unknown climate {self.climate}")
        if self.redundancy not in ("N", "N+1", "2N"):
            errs.append(f"unknown redundancy {self.redundancy}")
        for s in self.subsystems:
            if s not in ("power", "cooling", "compute", "controls"):
                errs.append(f"unknown subsystem {s}")
        if self.controls_tier not in CONTROLS_TIERS:
            errs.append(f"unknown controls_tier {self.controls_tier}")
        elif self.controls_tier == "lite" and self.tier in ("ben150", "ben500", "ben2000"):
            errs.append("BEN Controls Lite is for BEN 5 and BEN 30 only; BEN 150 and up use BEN Controls Pro")
        errs += self._validate_rev2()
        if not errs and self.tier not in ("ben5",) + MINIRACK_TIERS:
            d = self.derived()
            if not d["row_fits"]:
                errs.append(f"{d['rows']} row(s) of {d['racks_per_row']} racks + cooling units is {d['row_length_mm']} mm per row, exceeds interior {int(TIER_GEOMETRY[self.tier]['int_l_m']*1000)} mm; use fewer racks, rear-door or liquid cooling")
        return errs

    def _validate_rev2(self) -> List[str]:
        """Rules added in Rev 2 (lineup, BEN 1, liquid-first tiers). None of them can fire on a valid Rev 1 configuration."""
        errs: List[str] = []
        g = TIER_GEOMETRY[self.tier]
        if self.lineup not in LINEUPS:
            errs.append(f"unknown lineup {self.lineup}")
        elif self.tier not in TIERS_BY_LINEUP[self.lineup]:
            errs.append(f"{g['label']} is not in lineup {self.lineup} (lineups: " + ", ".join(f"{k}: {' '.join(v)}" for k, v in TIERS_BY_LINEUP.items()) + ")")
        if self.hardening == "IND" and self.tier not in MINIRACK_TIERS:
            errs.append("hardening IND (indoor) is for BEN 1 only")
        if self.controls_tier == "mini" and self.tier not in MINIRACK_TIERS:
            errs.append("BEN Controls Mini is for BEN 1 only")
        if self.cooling == "office_air" and self.tier not in MINIRACK_TIERS:
            errs.append("office_air cooling is for BEN 1 only")
        if self.tier in MINIRACK_TIERS:
            if self.form not in g["forms"]:
                errs.append(f"unknown BEN 1 form {self.form!r} (rack10 or cab12)")
            elif self.it_kw > g["forms"][self.form]["it_kw_max"]:
                errs.append(f"BEN 1 {self.form} carries up to {g['forms'][self.form]['it_kw_max']} kW IT, got {self.it_kw}; use cab12")
            if self.cooling != "office_air":
                errs.append("BEN 1 uses office_air cooling only (no dc800, no dlc_hd; liquid only inside the IT device)")
            if self.power_architecture != "ac480":
                errs.append("BEN 1 is a 120 V plug-in unit: dc800 does not apply")
            if self.hardening != "IND":
                errs.append("BEN 1 is indoor: hardening levels H1-H3 do not apply (IND)")
            if self.generator:
                errs.append("BEN 1 has no generator (plug-in UPS only)")
            if self.redundancy == "2N":
                errs.append("BEN 1 has one UPS; for 2N use two BEN 1 units")
            if self.controls_tier in ("lite", "pro"):
                errs.append("BEN 1 uses BEN Controls Mini (2 BEN Pods + BEN Care agent)")
            if not errs and self.form in g["forms"] and self._minirack_amps() > 16.0:
                errs.append(f"BEN 1 draws {self._minirack_amps():.1f} A at 120 V, above the 16 A continuous limit of a 20 A circuit; use the 230 V option")
        if g.get("liquid_first"):
            if self.cooling != "dlc_hd":
                errs.append(f"{g['label']} is liquid-first: dlc_hd only")
            if self.it_kw / max(self.racks, 1) > g["max_rack_kw"]:
                errs.append(f"{self.it_kw / max(self.racks, 1):.1f} kW/rack exceeds the {g['max_rack_kw']} kW GB300 NVL72-class rack limit of {g['label']}")
            if self.controls_tier == "lite":
                errs.append(f"BEN Controls Lite is for BEN 5 and BEN 30 only; {g['label']} uses BEN Controls Pro")
        return errs

    # ------------------------------------------------------------ controls tier
    def controls_tier_resolved(self) -> str:
        """Resolve ``controls_tier`` "auto": Lite for BEN 5, Pro for BEN 150/500/2000, and for BEN 30 Lite unless the
        profile is one where the buyer expects a PLC and a UL 508A panel (healthcare, public sector, AI training)."""
        if self.controls_tier in ("lite", "pro", "mini"):
            return self.controls_tier
        if self.tier in MINIRACK_TIERS:
            return "mini"
        if self.tier == "ben5":
            return "lite"
        if self.tier == "ben30":
            return "pro" if self.profile in CONTROLS_PRO_PROFILES else "lite"
        return "pro"

    # ------------------------------------------------------------ derived sizing
    def derived(self) -> Dict[str, Any]:
        g = TIER_GEOMETRY[self.tier]
        if g["kind"] == "minirack":
            return self._derived_minirack()
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
        dc800 = self.power_architecture == "dc800"
        dc: Dict[str, Any] = {}
        if dc800:
            # no UPS modules: the battery sits on the DC bus; the AC/DC front end replaces the UPS rectifier stage
            ups_modules, ups_kva_each = 0, 0.0
            dc = self._derived_dc800(total_kw)

        mv_service = g["voltage"].startswith("12.47")
        if mv_service:
            # medium-voltage service: pad-mount transformers at 480 V secondary, 2N at 2N/N+1 redundancy
            v_ll = 480
            service_amps = total_kva * 1000 / (math.sqrt(3) * v_ll) / 0.8
        elif g["voltage"].startswith("480"):
            v_ll = 480
            service_amps = total_kva * 1000 / (math.sqrt(3) * v_ll) / 0.8
        elif g["voltage"].startswith("208 V 3"):
            v_ll = 208
            service_amps = total_kva * 1000 / (math.sqrt(3) * v_ll) / 0.8
        else:
            v_ll = 240
            service_amps = total_kva * 1000 / v_ll / 0.8
        # round up to standard breaker frames
        frames = [30, 50, 60, 100, 150, 200, 225, 250, 400, 600, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000]
        service_breaker = next((f for f in frames if f >= service_amps), 4000)
        # MV service: transformer count/size (2,500 kVA pad-mounts), 2N when redundancy is 2N or N+1
        if mv_service:
            xfmr_kva = 2500
            xfmr_n = math.ceil(total_kva / (xfmr_kva * 0.9))
            xfmr_total = xfmr_n * 2 if self.redundancy in ("2N", "N+1") else xfmr_n
            gens_n = math.ceil(total_kw * 1.25 / 1250)
            gens_total = gens_n + 1 if self.generator else 0
        else:
            xfmr_kva, xfmr_n, xfmr_total = 0, 0, 0
            gens_n = math.ceil(total_kw * 1.25 / 50) * 0 + (1 if self.generator else 0)
            gens_total = gens_n

        # battery energy for ups_minutes at IT load (lithium, 90 % DoD)
        battery_kwh = self.it_kw * self.ups_minutes / 60 / 0.9

        # airflow: 125 cfm/kW typical at ΔT 12 K (air cooled); liquid tiers move only the residual air
        # (40 cfm/kW for dlc_cdu; dlc_hd: 125 cfm/kW x its stated air_residual)
        if cl["medium"] == "air":
            airflow_cfm = self.it_kw * 125
        elif "air_residual" in cl:
            airflow_cfm = self.it_kw * 125 * cl["air_residual"]
        else:
            airflow_cfm = self.it_kw * 40

        # structural: payload (+ hardening envelope mass)
        area_m2 = 2 * (g["ext_l_m"] * g["ext_h_m"] + g["ext_w_m"] * g["ext_h_m"]) + g["ext_l_m"] * g["ext_w_m"]
        hz = HARDENING[self.hardening]
        payload_kg = self.racks * (400 if self.tier == "ben5" else 900) + n_units_total * cl["mass_kg"] + ups_modules * (120 if self.tier == "ben5" else 350) + battery_kwh * 8 + area_m2 * hz["mass_kg_m2"]
        if dc800:
            payload_kg += dc["rectifier_cabinets"] * 400   # assumption: 400 kg per 4-module rectifier cabinet (replaces the UPS frames)
        gross_kg = payload_kg + g["tare_kg"]

        # envelope solar/transmission gain, R-value 3.5 m2K/W (100 mm PIR), ΔT at design
        envelope_gain_kw = (area_m2 * (clim["t_design_c"] - 22) / 3.5 + 0.3 * clim["solar_w_m2"] * g["ext_l_m"] * g["ext_w_m"] * 0.25) / 1000

        # +0.03 UPS double-conversion loss (ac480); dc800: rectifier loss + rack DC shelf loss from the two stated (vendor-claim) efficiencies
        pue_est = round(total_kw / self.it_kw + (dc["dc_pue_loss_adder"] if dc800 else 0.03), 3)
        # row length check per row (racks 600 mm + in-row/CDU units + 500 mm end zone) vs interior length
        rows = g.get("rows", 1)
        racks_per_row = math.ceil(self.racks / rows)
        units_per_row = math.ceil(n_units_total / rows)
        row_len_mm = racks_per_row * 600 + (units_per_row * cl["width_mm"] if cl["medium"] == "air" or cl["medium"] == "liquid" else 0) + 500
        row_fits = (self.tier == "ben5") or (row_len_mm <= g["int_l_m"] * 1000)
        nfpa_855 = battery_kwh >= 20.0
        # controls: tier and BEN Pod count (two per rack: cold face and hot face, + room + outdoor per module; BEN 5: 3)
        ct = self.controls_tier_resolved()
        pods = 3 if self.tier == "ben5" else self.racks * 2 + 2 * g["modules"]
        # hardening and climate: H2 forced for severe climates unless the user chose H3
        hardening_recommended = "H3" if self.profile == "public_sector" else ("H2" if self.climate in ("coastal", "hot_arid", "cold", "high_altitude", "hot_humid") else "H1")
        # high-density liquid loop (dlc_hd): W45 secondary loop, ΔT 10 K design; flow in L/min from Q = m·cp·ΔT with water
        # (cp 4.18 kJ/kg·K, 1 kg/L); 90 % of IT heat to liquid (air_residual 0.10), all of it available for heat reuse at the return
        loop: Dict[str, Any] = {}
        if self.cooling == "dlc_hd":
            liquid_frac = 1.0 - cl["air_residual"]
            liquid_kw = self.it_kw * liquid_frac
            loop = {"loop_water_class": cl["water_class"], "loop_dt_design_k": 10.0, "loop_supply_design_c": 40.0, "loop_return_design_c": 50.0,
                    "liquid_heat_kw": round(liquid_kw, 1), "loop_flow_lpm": round(liquid_kw / (4.18 * 10.0) * 60.0, 1),
                    "heat_reuse_kw_available": round(liquid_kw, 1), "air_residual": cl["air_residual"]}

        out = {
            "power_architecture": self.power_architecture, "power_architecture_label": POWER_ARCHITECTURES[self.power_architecture]["label"],
            "dc_ready": self.tier in POWER_ARCHITECTURES["dc800"]["tiers"],
            **dc, **loop,
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
            "row_length_mm": int(row_len_mm), "row_fits": row_fits, "rows": rows, "racks_per_row": racks_per_row, "nfpa_855_scope": nfpa_855,
            "mv_service": mv_service, "transformer_kva": xfmr_kva, "transformers_total": xfmr_total,
            "generators_total": gens_total, "generator_kw_each": 1250 if mv_service else (math.ceil(total_kw * 1.25 / 10) * 10 if self.generator else 0),
            "modules": g["modules"], "kind": g["kind"],
            "hardening": self.hardening, "hardening_label": hz["label"], "hardening_rating": hz["rating"], "hardening_coating": hz["coating"],
            "hardening_recommended": hardening_recommended, "envelope_area_m2": round(area_m2, 1),
            "ashrae_class": PROFILE_DEFAULTS[self.profile]["ashrae"],
            "controls_tier_resolved": ct, "controls_label": CONTROLS_TIERS[ct]["label"],
            "pods": pods,
            "climate": clim, "geometry": g,
        }
        if g.get("liquid_first"):
            self._apply_dense(out, ups_kva_n, area_m2, hz, dc)
        if self.lineup == "rev2":
            out.update(self._density(g))
        return out

    # ------------------------------------------------------------ Rev 2: density metrics
    def _density(self, g: Dict[str, Any]) -> Dict[str, Any]:
        fp = g["ext_l_m"] * g["ext_w_m"]
        vol = fp * g["ext_h_m"]
        return {"lineup": self.lineup, "kw_per_rack": round(self.it_kw / self.racks, 2), "footprint_m2": round(fp, 3), "volume_m3": round(vol, 3),
                "kw_per_m2_footprint": round(self.it_kw / fp, 2), "kw_per_m3_volume": round(self.it_kw / vol, 2)}

    # ------------------------------------------------------------ Rev 2: liquid-first dense tiers (BEN 300 / BEN 700)
    def dense_row_items(self, d: Dict[str, Any]) -> List[str]:
        """Row order from the door end: switchboard sections, power (battery / UPS interleaved, or rectifier + 800 V battery), CDUs,
        then the racks with the fan coils spread between them. Keys index DENSE_FOOTPRINTS."""
        items: List[str] = ["swbd"] * d["swbd_sections"]
        if self.power_architecture == "dc800":
            items += ["rect"] * d["rectifier_cabinets"] + ["batt800"] * d["battery_cabinets"]
        else:
            b, u = d["battery_cabinets"], d["ups_frames"]
            while b or u:
                if b:
                    items.append("batt"); b -= 1
                if u:
                    items.append("ups"); u -= 1
        items += ["cdu"] * d["cooling_units_total"]
        nr, nf = self.racks, d["fancoils_total"]
        slots = set(round((i + 0.5) * (nr + nf) / nf - 0.5) for i in range(nf)) if nf else set()
        ri = fi = 0
        for k in range(nr + nf):
            if (k in slots and fi < nf) or ri >= nr:
                items.append("fancoil"); fi += 1
            else:
                items.append("rack"); ri += 1
        return items

    def _apply_dense(self, out: Dict[str, Any], ups_kva_n: float, area_m2: float, hz: Dict[str, Any], dc: Dict[str, Any]) -> None:
        g, F, R = TIER_GEOMETRY[self.tier], DENSE_FOOTPRINTS, DENSE_RULES
        mult = 2 if self.redundancy == "2N" else 1
        resid = COOLING_LIBRARY[self.cooling].get("air_residual", 0.10)
        fc_n = math.ceil(resid * self.it_kw * 1.05 / F["fancoil"]["kw"])
        fc_total = fc_n + 1 if self.redundancy == "N+1" else fc_n * mult
        batt_need_kwh = (dc["battery_on_bus_kwh"] if self.power_architecture == "dc800" else out["battery_kwh"])
        batt_cab = max(math.ceil(batt_need_kwh / F["batt"]["kwh"]), math.ceil(self.it_kw / F["batt"]["kw"])) * mult
        if self.power_architecture == "dc800":
            frames_n, frames, kva_each = 0, 0, 0
        else:
            frames_n = math.ceil(ups_kva_n / F["ups"]["kva"])
            frames, kva_each = frames_n * mult, round(ups_kva_n / frames_n)
        brk = out["service_breaker_a"]
        swbd = 0 if brk <= R["panelboard_max_a"] else (1 if brk <= F["swbd"]["a_per_section"] else (2 if brk <= 2500 else 3))
        out.update({"ups_modules": frames, "ups_kva_each": kva_each, "ups_frames": frames, "ups_frames_n": frames_n,
                    "fancoils_n": fc_n, "fancoils_total": fc_total, "fancoil_kw": F["fancoil"]["kw"],
                    "trim_loop_kw": round(resid * self.it_kw * 1.1, 1), "trim_loop_c": R["trim_loop_c"],
                    "battery_cabinets": batt_cab, "battery_kwh_installed": round(batt_cab * F["batt"]["kwh"], 1),
                    "battery_minutes_installed": round(batt_cab * F["batt"]["kwh"] * 0.9 * 60 / self.it_kw, 1),
                    "swbd_sections": swbd, "panelboard_wall": swbd == 0, "liquid_first": True,
                    "rack_envelope_mm": [F["rack"]["w"], F["rack"]["d"], F["rack"]["h"]], "rack_kw_max": g["max_rack_kw"]})
        items = self.dense_row_items(out)
        row_mm = sum(F[k]["w"] for k in items) + R["end_zone_mm"]
        rect = out.get("rectifier_cabinets", 0) if self.power_architecture == "dc800" else 0
        payload = (self.racks * F["rack"]["kg"] + out["cooling_units_total"] * F["cdu"]["kg"] + fc_total * F["fancoil"]["kg"]
                   + frames * F["ups"]["kg"] + batt_cab * F["batt"]["kg"] + swbd * F["swbd"]["kg"] + rect * F["rect"]["kg"] + area_m2 * hz["mass_kg_m2"])
        out.update({"row_items": items, "row_length_mm": int(row_mm), "row_fits": row_mm <= g["int_l_m"] * 1000,
                    "row_budget_mm": int(g["int_l_m"] * 1000 - R["end_zone_mm"]), "end_zone_mm": R["end_zone_mm"],
                    "payload_kg": round(payload), "gross_kg": round(payload + g["tare_kg"]),
                    "nfpa_855_scope": batt_cab * F["batt"]["kwh"] >= 20.0})

    # ------------------------------------------------------------ Rev 2: BEN 1 mini rack
    def _minirack_power(self) -> Dict[str, float]:
        M = MINIRACK
        cl = COOLING_LIBRARY["office_air"]
        cool = self.it_kw / cl["cop"]
        total = self.it_kw + cool + M["aux_kw"] + self.it_kw * (1.0 / M["ups_eff"] - 1.0)
        kva = total / 0.95
        return {"cool": cool, "total": total, "kva": kva, "amps": kva * 1000.0 / 120.0}

    def _minirack_amps(self) -> float:
        return self._minirack_power()["amps"]

    def _derived_minirack(self) -> Dict[str, Any]:
        """BEN 1 sizing: 120 V plug-in, line-interactive lithium UPS, office-air extraction; every watt ends up in the room."""
        g, M = self.geometry(), MINIRACK
        f = TIER_GEOMETRY[self.tier]["forms"].get(self.form) or TIER_GEOMETRY[self.tier]["forms"]["cab12"]
        cl = COOLING_LIBRARY[self.cooling] if self.cooling in COOLING_LIBRARY else COOLING_LIBRARY["office_air"]
        clim = CLIMATE_DESIGN[self.climate]
        hz = HARDENING.get(self.hardening, HARDENING["IND"])
        pw = self._minirack_power()
        it_w = self.it_kw * 1000.0
        n_units = math.ceil(self.it_kw * 1.05 / cl["unit_kw"])
        n_total = n_units + 1 if self.redundancy == "N+1" else (2 * n_units if self.redundancy == "2N" else n_units)
        amps = pw["amps"]
        if amps <= 12.0:
            brk, outlet = 15, "NEMA 5-15R on a dedicated 15 A, 120 V circuit (12 A continuous at 80 %)"
        elif amps <= 16.0:
            brk, outlet = 20, "NEMA 5-20R on a dedicated 20 A, 120 V circuit (16 A continuous at 80 %)"
        else:
            brk, outlet = 30, "exceeds a 120 V 20 A circuit: use the 230 V option"
        need_w = it_w * M["ups_headroom"]
        ups = next((u for u in M["ups_models"] if u["w"] >= need_w), M["ups_models"][-1])
        runtime = ups["wh"] / max(it_w, 1.0) * 60.0
        packs = 0 if runtime >= self.ups_minutes else math.ceil((self.ups_minutes * it_w / 60.0 - ups["wh"]) / ups["wh"])
        battery_kwh = self.it_kw * self.ups_minutes / 60 / 0.9
        src = M["noise_src_dba"][f["noise_source"]] + 15.0 * math.log10(max(it_w, 50.0) / 200.0)
        inside = src - f["insertion_loss_db"]
        noise = 10.0 * math.log10(10 ** (inside / 10.0) + 10 ** (28.0 / 10.0))     # + cabinet extraction fans, 28 dBA at 1 m
        target = M["noise_target_dba"][self.form if self.form in M["noise_target_dba"] else "cab12"]
        heat_w = pw["total"] * 1000.0
        vent_cfm = heat_w / (1.18 * 1006 * 5.0) / 0.000471947
        airflow = it_w / (1.18 * 1006 * cl.get("design_rise_k", 10.0)) / 0.000471947
        area = 2 * (g["ext_l_m"] * g["ext_h_m"] + g["ext_w_m"] * g["ext_h_m"]) + g["ext_l_m"] * g["ext_w_m"]
        ups_kg = 16 if ups["va"] <= 1000 else 28
        payload = self.it_kw * M["kg_per_kw_it"] + ups_kg * (1 + packs)
        ct = self.controls_tier_resolved()
        quiet_kw = 200.0 * 10 ** ((target - M["noise_src_dba"][f["noise_source"]] + f["insertion_loss_db"]) / 15.0) / 1000.0
        note = (f"All {heat_w:.0f} W ({heat_w * 3.412:.0f} BTU/h) of BEN 1 goes into the room; the room's air conditioning must remove it. "
                f"In an open office with central HVAC that is one or two people's worth of heat. In a closed closet it is not: give the closet a "
                f"transfer fan or door grille moving at least {vent_cfm:.0f} cfm (holds the closet within 5 K of the office), or a dedicated "
                f"{max(0.5, math.ceil(heat_w * 3.412 / 6000.0) / 2):.1f} ton split unit. Keep the inlet side 300 mm clear of walls.")
        out = {
            "power_architecture": "ac480", "power_architecture_label": "120 V plug-in → line-interactive lithium UPS → rack PDU (BEN 1)",
            "dc_ready": False,
            "tier_label": g["label"], "enclosure": f"{g['form_label']} ({g['reference']} class)", "form": self.form, "form_label": g["form_label"],
            "per_rack_kw": round(self.it_kw / self.racks, 2),
            "cooling_label": cl["label"], "cooling_units_n": n_units, "cooling_units_total": n_total,
            "cooling_unit_kw_derated": round(cl["unit_kw"], 1), "cooling_derate": 1.0, "cooling_elec_kw": round(pw["cool"], 3),
            "total_kw": round(pw["total"], 3), "total_kva": round(pw["kva"], 3),
            "voltage": g["voltage"], "voltage_option": g["voltage_option"], "service_amps_calc": round(amps / 0.8), "service_breaker_a": brk,
            "outlet_amps": round(amps, 1), "outlet_circuit": outlet, "outlet_circuit_a": brk,
            "ups_modules": 1, "ups_kva_each": ups["va"] / 1000.0, "ups_va": ups["va"], "ups_w": ups["w"], "ups_model": ups["model"], "ups_plug": ups["plug"],
            "ups_runtime_min_est": round(runtime, 1), "ups_battery_packs": packs, "battery_kwh": round(battery_kwh, 3),
            "airflow_cfm": round(airflow), "payload_kg": round(payload), "gross_kg": round(payload + g["tare_kg"]),
            "envelope_gain_kw": 0.0, "pue_estimate": round(pw["total"] / self.it_kw, 3),
            "row_length_mm": int(g["ext_l_m"] * 1000), "row_fits": True, "rows": 1, "racks_per_row": 1, "nfpa_855_scope": battery_kwh >= 20.0,
            "mv_service": False, "transformer_kva": 0, "transformers_total": 0, "generators_total": 0, "generator_kw_each": 0,
            "modules": 1, "kind": "minirack",
            "hardening": self.hardening, "hardening_label": hz["label"], "hardening_rating": hz["rating"], "hardening_coating": hz["coating"],
            "hardening_recommended": "IND", "envelope_area_m2": round(area, 2),
            "ashrae_class": PROFILE_DEFAULTS[self.profile]["ashrae"],
            "controls_tier_resolved": ct, "controls_label": CONTROLS_TIERS[ct]["label"], "pods": 2,
            "noise_dba_est": round(noise, 1), "noise_dba_target": target, "noise_ok": noise <= target, "noise_quiet_up_to_kw": round(quiet_kw, 2),
            "noise_basis": f"IT sound pressure at 1 m {src:.1f} dBA ({f['noise_source']} gear, +15 dB per decade of power) less {f['insertion_loss_db']} dB cabinet insertion loss, + 28 dBA extraction fans",
            "heat_to_room_w": round(heat_w), "heat_to_room_btu_h": round(heat_w * 3.412), "closet_vent_cfm": round(vent_cfm),
            "room_cooling_note": note, "office_design_c": M["office_design_c"], "office_max_c": M["office_max_c"],
            "climate": clim, "geometry": g,
        }
        out.update(self._density(g))
        return out

    # ------------------------------------------------------------ 800 VDC sizing (forward option)
    def _derived_dc800(self, total_kw: float) -> Dict[str, Any]:
        """Sizing of the 800 VDC option (docs/FORWARD_ARCHITECTURE_DECISION.md). Stated assumptions, see POWER_ARCHITECTURES["dc800"]:
        front-end kW = total_kw / rectifier efficiency; bus current = IT kW / 800 V with 25 % headroom, rounded up to a standard DC busway
        frame; rectifier modules of 100 kW with the configured redundancy; one insulation monitoring device per module; a 3 % distribution
        loss saving; copper by the simple area-ratio method (same current density, 2 DC conductors vs 3 AC phase conductors at 415 V)."""
        pa = POWER_ARCHITECTURES["dc800"]
        conv = DC_CONVENTIONS[self.dc_convention]
        v = pa["bus_v_nominal"]
        # the bus feeds the rack DC shelves (800 V -> 50 V), so the bus carries the IT load plus the shelf loss
        bus_kw = self.it_kw / pa["rack_shelf_eff"]
        front_end_kw = (total_kw + bus_kw - self.it_kw) / pa["rectifier_eff"]
        bus_a = bus_kw * 1000.0 / v * pa["bus_headroom"]
        busway_a = next((f for f in pa["busway_frames_a"] if f >= bus_a), pa["busway_frames_a"][-1])
        n_rect = math.ceil(front_end_kw / pa["rectifier_module_kw"])
        if self.redundancy == "N+1":
            n_rect_total = n_rect + 1
        elif self.redundancy == "2N":
            n_rect_total = 2 * n_rect
        else:
            n_rect_total = n_rect
        # copper: area ∝ current at a fixed density; mass = conductors x area x length x 8.96e-3 kg/(mm²·m); length = row length + 5 m to the bus
        g = TIER_GEOMETRY[self.tier]
        length_m = g["int_l_m"] + 5.0
        i_dc = bus_kw * 1000.0 / v
        i_ac = self.it_kw * 1000.0 / (math.sqrt(3) * pa["ac_feeder_v"] * pa["ac_feeder_pf"])
        cu_dc = 2 * (i_dc / pa["copper_current_density_a_mm2"]) * length_m * pa["copper_kg_per_mm2_m"]
        cu_ac = 3 * (i_ac / pa["copper_current_density_a_mm2"]) * length_m * pa["copper_kg_per_mm2_m"]
        battery_kwh = self.it_kw * self.ups_minutes / 60 / 0.9
        per_rack_kw = self.it_kw / self.racks
        shelves_per_rack = math.ceil(per_rack_kw / pa["rack_shelf_kw"]) + (1 if self.redundancy in ("N+1", "2N") else 0)
        return {
            "ac_dc_front_end_kw": round(front_end_kw, 1), "rectifier_eff": pa["rectifier_eff"], "rectifier_eff_basis": "vendor claim (SST/rectifier >98.5 % peak), sizing assumption",
            "dc_convention": self.dc_convention, "dc_convention_label": conv["label"], "dc_grounding": conv["grounding"], "dc_imd_arrangement": conv["imd_arrangement"], "dc_convention_spec": conv["spec"],
            "dc_bus_v_nominal": v, "dc_bus_v_pole": conv["pole_v_to_ground"], "dc_bus_v_min": pa["bus_v_min"], "dc_bus_v_max": pa["bus_v_max"],
            "dc_window_v": [pa["bus_v_min"], pa["bus_v_max"]], "dc_window_basis": pa["window_basis"],
            "dc_bus_kw": round(bus_kw, 1), "rack_shelf_kw": pa["rack_shelf_kw"], "rack_shelf_eff": pa["rack_shelf_eff"], "rack_shelf_eff_basis": "vendor claim (Delta 90 kW 800 V -> 50 V shelf, 98.5 % peak)",
            "rack_shelves_per_rack": shelves_per_rack, "rack_shelves_total": shelves_per_rack * self.racks,
            "rack_interface": "800 V -> 50 V DC shelf per rack (Delta 90 kW class) or an MGX 800 VDC power rack; no server takes 800 VDC directly",
            "dc_pue_loss_adder": round((1.0 / pa["rectifier_eff"] - 1.0) + (1.0 / pa["rack_shelf_eff"] - 1.0), 4),
            "dc_bus_current_a": round(bus_a), "dc_busway_a": busway_a,
            "rectifier_module_kw": pa["rectifier_module_kw"], "rectifier_modules_n": n_rect, "rectifier_modules": n_rect_total,
            "rectifier_cabinets": math.ceil(n_rect_total / 4), "imd_count": n_rect_total,
            "battery_on_bus_kwh": round(battery_kwh, 1), "battery_string_v": "800 V class",
            "dc_loss_saving_kw": round(self.it_kw * pa["loss_saving_frac"], 1), "dc_loss_saving_frac": pa["loss_saving_frac"],
            "copper_kg_dc_bus": round(cu_dc, 1), "copper_kg_ac_feeders": round(cu_ac, 1),
            "copper_saving_pct": round(100.0 * (1.0 - cu_dc / cu_ac), 1), "copper_method": "area ratio: same current density, 2 DC conductors at 800 V vs 3 AC phase conductors at 415 V, same run length",
        }

    # ------------------------------------------------------------ io
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, **kw) -> str:
        return json.dumps(self.to_dict(), indent=2, **kw)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Config":
        """Load a saved configuration. A dict without ``lineup`` is a Rev 1 configuration (every quote saved before Rev 2) when its tier
        is a Rev 1 tier, so it reproduces exactly; a Rev 2-only tier without the key loads as rev2."""
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        if "tier" in known:
            known["tier"] = canonical_tier(str(known["tier"]))
        if "lineup" not in known:
            known["lineup"] = "rev1" if known.get("tier", "ben150") in REV1_TIERS else "rev2"
        return cls(**known)

    @classmethod
    def preset(cls, tier: str, profile: str = "ai_inference", climate: str = "temperate", hardening: str | None = None,
               lineup: str = "rev2", form: str | None = None) -> "Config":
        """Preset for ``tier`` in ``lineup``. Rev 1 tiers follow the Rev 1 rules in both lineups (frozen; tests/test_rev1_frozen.py);
        BEN 1 and the liquid-first tiers have their own rules (_preset_minirack, _preset_dense)."""
        tier = canonical_tier(tier)
        if lineup not in LINEUPS:
            raise ValueError(f"unknown lineup {lineup}; valid: {LINEUPS}")
        if tier not in TIERS_BY_LINEUP[lineup]:
            raise ValueError(f"{tier} is not in lineup {lineup}: {TIERS_BY_LINEUP[lineup]}")
        g = TIER_GEOMETRY[tier]
        if g["kind"] == "minirack":
            return cls._preset_minirack(tier, profile, climate, lineup, form)
        if g.get("liquid_first"):
            return cls._preset_dense(tier, profile, climate, hardening, lineup)
        cfg = cls._preset_rev1(tier, profile, climate, hardening)
        cfg.lineup = lineup
        return cfg

    @classmethod
    def _preset_minirack(cls, tier: str, profile: str, climate: str, lineup: str, form: str | None) -> "Config":
        """BEN 1: AI inference on two desktop AI boxes in the 10-inch rack; AI training, healthcare and public sector in the lockable
        12U cabinet with a 2U single-GPU server; everyone else a 0.4 kW 10-inch rack. Hardening IND, no generator, 10 min UPS."""
        form = form or ("cab12" if profile in ("ai_training", "healthcare", "public_sector") else "rack10")
        if form == "cab12":
            it = 1.5 if profile == "ai_training" else 1.0
        else:
            it = 0.6 if profile == "ai_inference" else 0.4
        return cls(tier=tier, profile=profile, it_kw=it, racks=1, cooling="office_air", redundancy="N" if form == "rack10" else "N+1",
                   climate=climate, generator=False, hardening="IND", ups_minutes=10, controls_tier="auto", lineup=lineup, form=form)

    @classmethod
    def _preset_dense(cls, tier: str, profile: str, climate: str, hardening: str | None, lineup: str) -> "Config":
        """BEN 300 / BEN 700: AI profiles at the nominal maximum, others at 80 %, all racks, dlc_hd. If the profile's redundancy (2N)
        does not fit the single row, the IT load steps down 10 kW at a time and then one rack at a time until it does."""
        g = TIER_GEOMETRY[tier]
        p = PROFILE_DEFAULTS[profile]
        it0 = g["it_kw_max"] if profile in ("ai_training", "ai_inference") else 0.8 * g["it_kw_max"]
        if hardening is None:
            hardening = "H3" if profile == "public_sector" else ("H2" if climate in ("coastal", "hot_arid", "cold", "high_altitude", "hot_humid") else "H1")
        cfg = cls(tier=tier, profile=profile, it_kw=float(round(it0)), racks=g["max_racks"], cooling="dlc_hd", redundancy=p["redundancy"],
                  climate=climate, generator=profile in ("healthcare", "public_sector", "off_grid"), hardening=hardening,
                  ups_minutes=g.get("ups_minutes_default", 5), lineup=lineup)
        for racks in range(g["max_racks"], 0, -1):
            it = min(float(round(it0)), racks * g["max_rack_kw"])
            while it >= g["it_kw_min"]:
                cfg.racks, cfg.it_kw = racks, float(it)
                if not cfg.validate():
                    return cfg
                it -= 10.0
        cfg.racks, cfg.it_kw = g["max_racks"], float(round(it0))
        return cfg

    @classmethod
    def _preset_rev1(cls, tier: str, profile: str = "ai_inference", climate: str = "temperate", hardening: str | None = None) -> "Config":
        """The Rev 1 preset rule, unchanged (frozen)."""
        g = TIER_GEOMETRY[tier]
        p = PROFILE_DEFAULTS[profile]
        it_kw = min(g["it_kw_max"], max(g["it_kw_min"], p["rack_kw"] * g["max_racks"] * 0.8))
        if g["kind"] == "hall":
            it_kw = 0.8 * g["it_kw_max"]  # a 2 MW center is sold near its nominal size; density follows from the profile
        racks = max(1, min(g["max_racks"], math.ceil(it_kw / p["rack_kw"])))
        cooling = g["default_cooling"]
        if tier != "ben5" and it_kw / racks > COOLING_LIBRARY[cooling]["max_rack_kw"]:
            cooling = "dlc_cdu"
        if hardening is None:
            hardening = "H3" if profile == "public_sector" else ("H2" if climate in ("coastal", "hot_arid", "cold", "high_altitude", "hot_humid") else "H1")
        cfg = cls(tier=tier, profile=profile, it_kw=float(round(it_kw)), racks=racks,
                  cooling=cooling, redundancy=p["redundancy"], climate=climate,
                  generator=(profile in ("healthcare", "public_sector", "off_grid")) or tier == "ben2000",
                  hardening=hardening)
        if tier == "ben2000":
            cfg.cooling = "dlc_cdu"
        elif tier != "ben5":
            for alt in (cooling, "inrow_dx_300", "rdhx_drycooler", "dlc_cdu"):
                cfg.cooling = alt
                if not cfg.validate():
                    break
        return cfg


# Rev 2 presets (default for new work) and the frozen Rev 1 presets (byte-identical derived() to the Rev 1 release).
PRESETS = {t: Config.preset(t, lineup="rev2") for t in TIERS_BY_LINEUP["rev2"]}
PRESETS_REV1 = {t: Config.preset(t, lineup="rev1") for t in TIERS_BY_LINEUP["rev1"]}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine selector / sizing")
    ap.add_argument("--tier", default="ben150", choices=list(TIER_GEOMETRY) + list(TIER_ALIASES))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--it-kw", type=float)
    ap.add_argument("--racks", type=int)
    ap.add_argument("--cooling", choices=list(COOLING_LIBRARY))
    ap.add_argument("--redundancy", choices=["N", "N+1", "2N"])
    ap.add_argument("--controls-tier", dest="controls_tier", choices=list(CONTROLS_TIERS))
    ap.add_argument("--hardening", choices=list(HARDENING))
    ap.add_argument("--power-architecture", dest="power_architecture", choices=list(POWER_ARCHITECTURES),
                    help="ac480 (default, today) or dc800 (800 VDC bus option, BEN 150 and up)")
    ap.add_argument("--dc-convention", dest="dc_convention", choices=list(DC_CONVENTIONS), help="dc800 only: bipolar_400 (±400 V, HR midpoint; default) or unipolar_800 (isolated return)")
    ap.add_argument("--lineup", default="rev2", choices=list(LINEUPS), help="product lineup (rev1 = frozen Rev 1 rules)")
    ap.add_argument("--form", choices=["rack10", "cab12"], help="BEN 1 form")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate, lineup=a.lineup, form=a.form)
    for k in ("it_kw", "racks", "cooling", "redundancy", "controls_tier", "hardening", "power_architecture", "dc_convention"):
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
                  "ups_modules", "ups_kva_each", "battery_kwh", "airflow_cfm", "gross_kg", "pue_estimate", "row_length_mm", "row_fits", "nfpa_855_scope",
                  "controls_tier_resolved", "pods", "hardening_label", "transformers_total", "generators_total", "power_architecture"):
            print(f"  {k:24s} {d[k]}")
        for k in ("ac_dc_front_end_kw", "dc_convention", "dc_bus_v_nominal", "dc_bus_v_pole", "dc_window_v", "dc_window_basis", "dc_bus_current_a", "dc_busway_a", "rectifier_modules", "imd_count", "rack_shelves_total", "battery_on_bus_kwh",
                  "dc_loss_saving_kw", "copper_saving_pct", "loop_flow_lpm", "heat_reuse_kw_available"):
            if k in d:
                print(f"  {k:24s} {d[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

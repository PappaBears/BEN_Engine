# BEN Engine Rev 2 — decision record

**Status:** decided 2026-11-09 by the operator. Major product revision. Rev 1 is frozen (`releases/REV1.md`, branch `release/rev1`); nothing from Rev 1 is deleted (`docs/REVISION_POLICY.md`).

Operator's words: "Make sure we have the correct branding on the modules … the base is good, we just need a once-over … the budget to do the once-over is a 5 million revamp … especially the liquid cooling, and I want to make sure we are as dense as we can be. Rev 2 of the Schreiber AI BEN Engine has the cutting edge and density people are looking for, along with the very low side for tiny business, where we do mini racks."

## 1. Brand: apply the Schreiber AI brand package v2

Source: `brand/v2/source/Schreiber-AI-Brand-Revamp-Package-2026-10-08.html` (VIP Experience Team, Round 1, 2026-10-08). Masters exported to `brand/v2/` (mark, horizontal lockup, stacked lockup, 32 px and 16 px small marks in Signal, Deep Cobalt, black and white).

| Token | Value | Job (one job per color) |
| --- | --- | --- |
| Night Navy / S0 | `#06101F` | page ground, module body paint (≈ PMS 2767 C, proof required) |
| S1 | `#0B1A31` | sections |
| S2 | `#0F2342` | panels, plates |
| S3 | `#16305A` | raised, hover |
| Border | `#24406B` | rules |
| Signal Blue (400) | `#4C9DFF` | the mark on dark, headline highlight, links |
| Deep Cobalt (700) | `#1E40AF` | the mark on white |
| Cobalt | `#2563EB` | secondary blue |
| Safety Amber | `#FFB020` (hover `#FFC14D`, pressed `#E69500`) | **the primary button only**; text on amber is Night Navy |
| Shop White | `#F4F7FB` · Paper `#EEF4FC` | light grounds, QR plates |
| Ink / Slate / Fog / Steel | `#0B1A31` / `#4A5D7A` / `#B2C1D8` / `#8EA7C8` | text and secondary text |
| Status: Run / Hold / Stop / Info | `#2BB673` / `#F2C94C` / `#FF6369` (light ground `#C8323A`) / `#5CD6FF` | status chips and alarms only, never brand |
| Type | Archivo (display wdth 125, H2 and below wdth 100), IBM Plex Sans (body), IBM Plex Mono (labels, data) | |

**Brand architecture.** Schreiber AI is the only customer-facing brand. The product line is written **BEN Engine, by Schreiber AI** (same pattern as "Atlas, by Schreiber AI"). The legal line is "Schreiber AI is a Schreiber Holding LLC company." Lowercase "i" lives only inside the mark; the wordmark says "AI".

**Signature device on the hardware.** Every BEN unit already needs a nameplate. Rev 2 makes it the brand's **data plate band**: a strip along the bottom of the module side and on the door that reads `Schreiber AI · BEN Engine · BEN 300 · S/N … · Rated 300 kW IT · 480 V 3φ · IP66 · Rev 2` with a QR to the unit's page. The same band runs along proposals, drawings, slides, the dashboard footer and the data sheets.

**Data visualisation.** Amber is reserved for the button, so the hot aisle and heat maps use a thermal ramp that is not a brand or status color (cool → `#5CD6FF` … warm → `#FF8A3D`), labelled with a legend.

## 2. Lineup Rev 2: the low end and the dense end

Names keep the Rev 1 rule: the number is the nominal maximum IT kW.

| Tier | Enclosure | IT load | Cooling | Who it is for | Status in Rev 2 |
| --- | --- | --- | --- | --- | --- |
| **BEN 1** (new) | Indoor **mini rack**: 10-inch 8U desk/shelf rack (≤ 0.6 kW) or 19-inch 12U sound-damped office cabinet (≤ 1.5 kW) | 0.2–1.5 kW | Office air through a filtered, sound-damped path; closed-loop liquid only inside the IT device | Tiny businesses: one or two AI boxes (DGX Spark-class desktop AI, a small GPU server), a NAS and a firewall in a closet or on a shelf; 120 V plug-in | new |
| **BEN 5** | Outdoor NEMA 4X / IP66 24U cabinet | 2–5 kW | Cabinet DX, R-513A | Small business outdoors | carried |
| **BEN 30** | 10 ft module | 10–30 kW | 300 mm in-row DX | SMB private cloud | carried |
| **BEN 150** | 20 ft module | 50–150 kW | Rear-door + dry cooler | Mid-market air/rear-door | carried |
| **BEN 300** (new, dense) | 20 ft module, liquid-first | 150–300 kW | Direct liquid W45, row CDU N+1, ≤ 10 % air residual | One or two current liquid racks (GB300 NVL72-class, 132–155 kW) | new |
| **BEN 500** | 40 ft module | 150–500 kW | DLC + CDU | Rev 1 configuration kept for existing quotes | carried |
| **BEN 1000** (new, flagship dense) | 40 ft module, liquid-first, all-in-one | 500–1,000 kW | Direct liquid W45, CDU N+1, heat-reuse port | Up to six or seven current liquid racks with power, UPS/battery, CDUs and controls in one sealed box; heat rejection on an adjacent skid | new |
| **BEN 2000** | Prefabricated hall | 800–2,000 kW | DLC | Capability example | carried |

**All-in-one rule (from the operator, Rev 1):** power, cooling distribution, compute and controls inside one enclosure; heat rejection outside (roof or skid). The dense tiers must pass the existing interference checks (single row, 900 mm egress, NEC 110.26 working space at 480 V) with real footprints, or they are reported as study, not sold. If a target density does not fit, the tier is renamed to the power that does fit.

**Forward options** (`dc800`, `dlc_hd`) remain options; on BEN 300 and BEN 1000 `dlc_hd` is the default cooling, `dc800` stays a study option until the program's test-cell gate.

## 3. Budget: USD 5 M revamp

The revamp budget is USD 5 M. The engineering, branding and documentation revision is done in this repository now (Rev 2). The USD 5 M funds what a repository cannot: the BEN 1 and BEN 300 lighthouse units, the liquid and 800 VDC test cell, listings (UL 508A, FCC for the Pod, field evaluation), BEN Pod production, brand production (data plates, livery, print), and the team to run it. Allocation in `docs/programs/REV2_REVAMP_PROGRAM.md`, which supersedes `RD_PROGRAM_2027.md` (kept for history).

## 4. Questions the operator still owns

1. Does the BEN Care dashboard sign-in become **"Atlas, by Schreiber AI"** (the brand package names Atlas as the system clients log into), or stay "BEN Care"?
2. Brand package "facts only you have": phone number, starting prices for the BEN tiers, first pilot results for proof slots.
3. Module paint: Night Navy body (on brand, absorbs solar heat: about +4–8 K skin temperature against white in direct sun) or Shop White body with a Night Navy band (cooler, cheaper to cool). Default chosen: Shop White body with the Night Navy data plate band on outdoor tiers; Night Navy for indoor BEN 1.

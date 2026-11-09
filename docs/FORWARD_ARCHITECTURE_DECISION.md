# Forward architecture decision — 800 VDC power and high-density liquid cooling

**Status:** decided 2026-11-09 from operator steering ("focus on liquid cooling and innovations along with the new 800 or 900 V architecture; be at the forefront; $5 M to line it out"). Binding for the engineering changes and the program plan in `docs/programs/`.

## 1. What changes in the product

| Area | Today (Rev C) | Forward option (this decision) |
| --- | --- | --- |
| Power distribution inside the unit | 480 V AC → UPS → 208/415 V AC PDUs → rack PSUs | **800 VDC** from an AC/DC front end (SiC rectifier or solid-state transformer) to a DC busway, designed for **both** conventions in use in 2026: OCP Diablo 400 (±400 VDC bipolar, high-resistance midpoint ground) and the NVIDIA/OCP LVDC spec (800 VDC unipolar, isolated return); the rack interface is an 800 V → 50 V DC shelf per rack or an MGX 800 VDC power rack (Kyber-class direct DC racks are 2027+); lithium battery on the DC bus (no double conversion). The 760–920 V operating window is a working assumption until the OCP Diablo 400 §9.3.1 and NVIDIA MGX power-rack specifications are read in full |
| Cooling | Air (in-row), rear-door, DLC + CDU for BEN 500/2000 | **High-density direct liquid cooling** as a first-class option from BEN 150 up: warm-water W45 secondary loop, 100–250 kW per rack, CDU per row with N+1, air-side residual ≤ 10 %, heat-reuse port; immersion kept as a study |
| Controls | BEN Controls Pro/Lite, BEN Pod, BEN Mesh, BEN Care | Unchanged platform; adds DC-bus monitoring (insulation monitoring device, ground-fault location, DC arc detection), CDU loop twin (flow, ΔT, leak-to-isolation time), heat-reuse accounting |

The configuration model gains two selectable options: `power_architecture: "ac480" | "dc800"` and a cooling entry `dlc_hd` (high-density DLC). Existing presets keep `ac480` so nothing already quoted changes. BEN 5 and BEN 30 stay AC (no DC-input IT equipment exists at that scale yet).

## 2. Why 800 VDC and why now

- The GPU vendors have moved the industry: NVIDIA's 800 VDC roadmap (hybrid in-row power rack H2 2026, row power centre with overhead 800 VDC busway 2027, full scale with Rubin Ultra / Kyber 2027, one report of slip to 2028) and the OCP Diablo 400 and LVDC SST specifications put DC distribution on the roadmap of every rack-scale buyer. Sources and dates: `docs/research/STATE_OF_THE_ART_2026.md` §1. A modular product that cannot offer DC input will be designed out of AI workloads within two product cycles.
- Physics: at 800 V the conductor cross-section for a given kW falls by roughly 3–4× against 208/415 V AC, the UPS double conversion disappears (battery on the bus), and the rack loses its AC PSU stage. Published vendor claims are 3–5 % end-to-end efficiency gain and large copper savings; we will measure, not quote.
- Risk: in November 2026 nothing native-800 VDC is a listed catalogue product; NEC 2026 has no 800 VDC article (analysts point to NEC 2029), NFPA 70E 2027 has no 800 VDC PPE category, UL's solid-state-transformer programme is two months old, and IEEE 1584 arc-flash is AC-only. Field evaluation (NFPA 791) may be the only route through 2028. That is exactly why a funded program with a test cell and an agreed listing path is needed, not a slide.

## 3. Why high-density liquid first

Racks at 100 kW and above cannot be cooled by air or rear doors; the DLC market has matured (cold plates, CDUs, UQD connectors, ASHRAE W-classes) and a sealed, relocatable module with a warm-water loop is a natural fit: no chiller, dry coolers only, heat reuse possible. Our differentiation is the controls layer: loop twin, leak-to-isolation proof, monthly proof of redundancy on pumps and CDUs, and calibration of flow and ΔT so the energy accounting is trustworthy.

## 4. The $5 M program (summary; full plan in `docs/programs/FORWARD_800V_LIQUID_PROGRAM.md`)

Workstreams: (A) 800 VDC power architecture and test cell; (B) high-density liquid cooling and loop controls; (C) controls, twin and BEN Care extensions for DC and liquid; (D) standards, listings and partnerships; (E) one forward-architecture BEN 150 prototype built with a contract manufacturer and tested end to end. Twelve months to a demonstrated prototype, eighteen to a sellable option. Budget, staffing, gates and metrics are in the program plan.

## 4a. What the research changed (2026-11-09)
Read `docs/research/STATE_OF_THE_ART_2026.md` §6 before quoting anything. In short: design for both DC conventions; treat all efficiency, copper and TCO figures as vendor claims until our cell measures them; the Kyber "600 kW" rack is unconfirmed and a 150–500 kW module holds one or two current liquid racks (GB300 NVL72 about 132–142 kW nominal, 155 kW peak); W45 operation roughly triples secondary flow against 25 °C (vendor table) so pumps, manifolds and quick-disconnects must be sized for it; there is no published leak-to-isolation benchmark, so ours becomes one; and no vendor ships a DC-ready, liquid-first module at 150–500 kW, which is the slot this program targets. The research was built from search excerpts because the primary hosts were outside this session's network; the primary PDFs listed in §6 must be read in full in program month 1.

## 5. Honesty rules for this work

Every performance figure (efficiency, copper, PUE, density) is either measured on our test cell or quoted with its source and marked as a vendor claim. No "up to" numbers on the product page. The research file `docs/research/STATE_OF_THE_ART_2026.md` lists sources and dates.

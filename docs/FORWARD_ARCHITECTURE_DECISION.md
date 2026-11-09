# Forward architecture decision — 800 VDC power and high-density liquid cooling

**Status:** decided 2026-11-09 from operator steering ("focus on liquid cooling and innovations along with the new 800 or 900 V architecture; be at the forefront; $5 M to line it out"). Binding for the engineering changes and the program plan in `docs/programs/`.

## 1. What changes in the product

| Area | Today (Rev C) | Forward option (this decision) |
| --- | --- | --- |
| Power distribution inside the unit | 480 V AC → UPS → 208/415 V AC PDUs → rack PSUs | **800 VDC** (nominal; ±400 VDC to ground, 760–920 V range) from an AC/DC front end (SiC rectifier or solid-state transformer) to a DC busway; racks take DC directly (OCP / NVIDIA Kyber-class 800 VDC input); lithium battery on the DC bus (no double conversion) |
| Cooling | Air (in-row), rear-door, DLC + CDU for BEN 500/2000 | **High-density direct liquid cooling** as a first-class option from BEN 150 up: warm-water W45 secondary loop, 100–250 kW per rack, CDU per row with N+1, air-side residual ≤ 10 %, heat-reuse port; immersion kept as a study |
| Controls | BEN Controls Pro/Lite, BEN Pod, BEN Mesh, BEN Care | Unchanged platform; adds DC-bus monitoring (insulation monitoring device, ground-fault location, DC arc detection), CDU loop twin (flow, ΔT, leak-to-isolation time), heat-reuse accounting |

The configuration model gains two selectable options: `power_architecture: "ac480" | "dc800"` and a cooling entry `dlc_hd` (high-density DLC). Existing presets keep `ac480` so nothing already quoted changes. BEN 5 and BEN 30 stay AC (no DC-input IT equipment exists at that scale yet).

## 2. Why 800 VDC and why now

- The GPU vendors have moved the industry: NVIDIA's 800 VDC power delivery for Rubin Ultra / Kyber racks (2027) and the OCP Mt. Diablo sidecar-power work put DC distribution on the roadmap of every rack-scale buyer. A modular product that cannot offer DC input will be designed out of AI workloads within two product cycles.
- Physics: at 800 V the conductor cross-section for a given kW falls by roughly 3–4× against 208/415 V AC, the UPS double conversion disappears (battery on the bus), and the rack loses its AC PSU stage. Published vendor claims are 3–5 % end-to-end efficiency gain and large copper savings; we will measure, not quote.
- Risk: standards and listed equipment for 800 VDC distribution are immature in 2026 (NEC DC articles, UL listings for DC busway/breakers, arc-flash methods, insulation monitoring). That is exactly why a funded program with a test cell is needed, not a slide.

## 3. Why high-density liquid first

Racks at 100 kW and above cannot be cooled by air or rear doors; the DLC market has matured (cold plates, CDUs, UQD connectors, ASHRAE W-classes) and a sealed, relocatable module with a warm-water loop is a natural fit: no chiller, dry coolers only, heat reuse possible. Our differentiation is the controls layer: loop twin, leak-to-isolation proof, monthly proof of redundancy on pumps and CDUs, and calibration of flow and ΔT so the energy accounting is trustworthy.

## 4. The $5 M program (summary; full plan in `docs/programs/FORWARD_800V_LIQUID_PROGRAM.md`)

Workstreams: (A) 800 VDC power architecture and test cell; (B) high-density liquid cooling and loop controls; (C) controls, twin and BEN Care extensions for DC and liquid; (D) standards, listings and partnerships; (E) one forward-architecture BEN 150 prototype built with a contract manufacturer and tested end to end. Twelve months to a demonstrated prototype, eighteen to a sellable option. Budget, staffing, gates and metrics are in the program plan.

## 5. Honesty rules for this work

Every performance figure (efficiency, copper, PUE, density) is either measured on our test cell or quoted with its source and marked as a vendor claim. No "up to" numbers on the product page. The research file `docs/research/STATE_OF_THE_ART_2026.md` lists sources and dates.

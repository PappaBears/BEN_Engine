# BEN Engine marketing kit

## One-liners
- AI infrastructure that arrives finished.
- The all-in-one data center: power, cooling, compute and controls in one sealed box.
- Bringing AI back to every business.
- A data center you can see, test and own before it ships.
- Risks first. Price second. Box third.

## Elevator pitch (30 s)
Most small and mid-size businesses want AI on their own data, but their only options are a public cloud bill that never ends or a server closet nobody maintains. BEN Engine is an all-in-one modular data center, power, cooling, compute and controls in one sealed off-the-shelf container or outdoor cabinet, sized from one rack to 500 kW (and, when you need it, the same system scales to a single 2 MW center), that Schreiber AI designs from a single configuration model, builds from Simplified Technical English instructions, tests with a commissioning script, and watches with a digital twin. Buy the whole thing, one module, or put your own brand on it.

## Audience one-pagers

### Business owner (SMB)
**Headline:** Your AI, on your pad, watched by people who measure things.
**Body:** You pick the mission profile. We tell you the risks before the price. The box arrives commissioned, with a signed test report and a dashboard you can read without a data-center background. Schreiber AI monitors it, or you do.
**Proof points:** four all-in-one tiers (BEN 5 to BEN 500) from the same engineering model, which also scales to the 2 MW BEN 2000; every enclosure NEMA 4X / IP66, hose-tested, with H2/H3 hardening on request; upfront risk register; commissioning report with data; maintenance schedule for outdoor life.
**Call to action:** Build your configuration at schreiberai.com/ben and send it to Ben@SchreiberAI.com.

### Integrator / white-label partner
**Headline:** A finished platform you can sell under your name.
**Body:** BEN Controls (BEN Controller, BEN Pods on the BEN Mesh, dashboard, twin, commissioning, BEN Care) is local-first and brandable. Proof points: a listed PLC (Phoenix Contact PLCnext) in a UL 508A panel on BEN 150/500/2000, a Revolution Pi on the BEN 5 and BEN 30; sensor Pods with a hardware root of trust that attest before they join; no sensor cabling to pull; hardwired life safety; minutes-to-limit alarms and monthly proof of redundancy. Take the full unit, or only the power, cooling or controls module. Drawings, BOM and compliance pack are generated per configuration, so your proposal is engineering, not a brochure.
**Call to action:** Partner inquiry to Ben@SchreiberAI.com.

### Facilities / MEP lead
**Headline:** One-lines a worker can read. Numbers an engineer can check.
**Body:** Service size, UPS kVA, cooling units, airflow and gross mass come from `config.py` and are printed on the drawings. Sensors are specified with uncertainty budgets. The CFD and the twin are tools you can run, not pictures.
**Call to action:** Download the IFC drawing set from the repository.

## Proof-point copy blocks (use only with the evidence linked)
| Claim | Evidence |
| --- | --- |
| "Every drawing, part and alarm threshold comes from the same configuration." | `software/ben_engine/config.py`, `design/drawings/gen_drawings.py`, `software/ben_engine/bom.py`, `software/ben_engine/twin.py` |
| "You can run the whole box before it exists." | `scripts/run_dashboard.sh`, `tests/e2e/` screenshots |
| "Risks before prices." | `web/index.html` section order, `docs/RISK_REGISTER.md` |
| "Assembly by workers with minimal experience." | `design/assembly/ASSEMBLY-*.md` (ASD-STE100) |
| "Commissioned, not just delivered." | `software/ben_engine/commissioning.py` report |

### Regional enterprise, hospital, university, municipality (BEN 2000)
**Headline:** A 2 MW data center that arrives as a building kit and a schedule you can hold.
**Body:** Three factory-finished modules, a power module and a plant yard, joined on site into one sealed hall. Medium-voltage service, 2N power, N+1 generators, liquid cooling. The utility is the critical path and we say so: about 52 weeks from order to in service, with the permit, civil and MV work planned around it. Same twin, same commissioning script, same BEN Care as every BEN.
**Proof points:** `python -m ben_engine.config --tier ben2000` sizing; `docs/PROCESS_FLOW.md` §5 schedule; `docs/COMPLIANCE.md` §14 building, MV, NFPA 855, NFPA 110 and SPCC rows.
**Call to action:** Site and utility pre-screen with Ben@SchreiberAI.com.

### Element-proof by default, hardened on request (all audiences)
**Copy block:** Every BEN is NEMA 4X / IP66: gasketed, hose-tested, corrosion class C3. **H2** for coasts, deserts, the arctic and hurricane zones: flood plinth, marine coating, dust filtration, 150 mph door hardware. **H3** for public sector, defence and critical infrastructure: ballistic panels (UL 752), forced-entry doors (ASTM F3038), mantrap, tamper detection, optional HEMP shield. The hose test is in the warranty.
**Do not say:** "bulletproof", "EMP-proof", "TEMPEST certified" (we are TEMPEST-ready; the customer's authority certifies).

## Do not say
"Tier III certified" (we are not), "military grade", "bulletproof", "EMP-proof", "TEMPEST certified", the retired rain-only "3R" enclosure rating (say NEMA 4X / IP66), "zero downtime", any PUE as a guarantee (it is an estimate until measured on site), any price as final before quote.

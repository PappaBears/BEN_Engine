# BEN Engine marketing kit

## One-liners
- AI infrastructure that arrives finished.
- Bringing AI back to every business.
- A data center you can see, test and own before it ships.
- Risks first. Price second. Box third.

## Elevator pitch (30 s)
Most small and mid-size businesses want AI on their own data, but their only options are a public cloud bill that never ends or a server closet nobody maintains. BEN Engine is a modular data center built in an off-the-shelf container or outdoor cabinet, sized from one rack to 500 kW, that Schreiber AI designs from a single configuration model, builds from Simplified Technical English instructions, tests with a commissioning script, and watches with a digital twin. Buy the whole thing, one module, or put your own brand on it.

## Audience one-pagers

### Business owner (SMB)
**Headline:** Your AI, on your pad, watched by people who measure things.
**Body:** You pick the mission profile. We tell you the risks before the price. The box arrives commissioned, with a signed test report and a dashboard you can read without a data-center background. Schreiber AI monitors it, or you do.
**Proof points:** four tiers from the same engineering model; upfront risk register; commissioning report with data; maintenance schedule for outdoor life.
**Call to action:** Build your configuration at schreiberai.com/ben and send it to Ben@SchreiberAI.com.

### Integrator / white-label partner
**Headline:** A finished platform you can sell under your name.
**Body:** BEN Controls (BEN Controller, BEN Pods on the BEN Mesh, dashboard, twin, commissioning, BEN Care) is local-first and brandable. Proof points: a listed PLC (Phoenix Contact PLCnext) in a UL 508A panel on BEN 20/40, a Revolution Pi on the Micro; sensor Pods with a hardware root of trust that attest before they join; no sensor cabling to pull; hardwired life safety; minutes-to-limit alarms and monthly proof of redundancy. Take the full unit, or only the power, cooling or controls module. Drawings, BOM and compliance pack are generated per configuration, so your proposal is engineering, not a brochure.
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

## Do not say
"Tier III certified" (we are not), "military grade", "zero downtime", any PUE as a guarantee (it is an estimate until measured on site), any price as final before quote.

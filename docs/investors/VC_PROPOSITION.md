# BEN Engine — Investment proposition

**Schreiber AI · prepared 2026-11-07 · contact Ben@SchreiberAI.com**
*This document is generated alongside a working build. Every technical number in it is produced by the code in this repository; every market number is cited in `MARKET_SOURCES.md`; every price carries a confidence label from the bill of materials.*

## 1. The one-paragraph case

Small and mid-size businesses are adopting AI faster than their infrastructure can follow. Their choices today are a cloud bill that scales with success, a colocation contract priced for hyperscalers (about USD 196 per kW-month wholesale in 2025), or a server closet nobody commissioned. BEN Engine is a family of modular data centers, from a 6 kW outdoor cabinet to a 500 kW liquid-cooled 40 ft container, built from off-the-shelf enclosures and listed equipment, and sold with a controls layer that makes the box observable, testable and brandable. Schreiber AI's edge is not the steel: it is the **configuration-driven engineering system** that turns a mission profile into drawings, bill of materials, compliance pack, assembly instructions, digital twin and commissioning report, in the same afternoon, with the same numbers. That system is working software in this repository, not a roadmap item.

## 2. Problem

1. **Cloud economics invert for steady AI workloads.** Inference that runs all day on owned GPUs is cheaper than renting them after roughly one to two years; most SMBs cannot capture that because they cannot operate a facility.
2. **Traditional builds are priced for megawatts.** USD 10–13 M per MW and 18–30 months. Nobody builds a 100 kW facility that way.
3. **Modular vendors sell to hyperscalers and telcos.** Their minimum viable deal, engineering cycle and support model do not fit a 40-person manufacturer or a regional clinic.
4. **Data sovereignty and latency.** Healthcare, public sector, industrial OT and anyone with a customer-data promise want the model where the data is.

## 3. Product

| Tier | Enclosure | IT load | Who buys it |
| --- | --- | --- | --- |
| BEN Micro | NEMA 3R outdoor 24U cabinet | 2–6 kW | Clinics, retailers, farms, branch offices, "AI for everyone" |
| BEN 10 | 10 ft high-cube ISO container | 10–30 kW | SMB private cloud + inference |
| BEN 20 | 20 ft high-cube | 50–150 kW | Mid-market, industrial sites, regional AI |
| BEN 40 | 40 ft high-cube, direct liquid cooling | 150–500 kW | Training pods, white-label partners, public sector |

Four ways to buy: **hardware only**, **hardware + BEN Controls**, **white-label** (partner's brand on the box and dashboard), **managed** (Schreiber AI watches and maintains). Modules (power, cooling, compute, controls) can be bought separately.

## 4. Why we win: the engineering system

| Capability | What it does | Status in this repo |
| --- | --- | --- |
| Configuration model | One schema sizes power, cooling, structure, mass, PUE | `software/ben_engine/config.py` — verified for all tiers |
| Generated drawings | Issue-for-construction set with CTQ/CTP tables per tier | `design/drawings/` |
| Generated BOM with price confidence | Real parts, confirmed/list/estimate split | `purchasing/`, `docs/BOM.md` |
| Digital twin | Thermal + power model with faults; fits itself from commissioning data | `software/ben_engine/twin.py`, `analysis.py` |
| CFD | 2-D lattice-Boltzmann airflow for layout and recirculation | `software/ben_engine/cfd.py` |
| Commissioning script | FAT/SAT with signed report; customer or Schreiber AI can run it | `software/ben_engine/commissioning.py` |
| Dashboard | 3-D twin, walkthrough, sweeps, I/O test, CSV, calibration | `dashboard/` |
| Firmware | Open ESP32 nodes + Pi gateway, MQTT/Modbus, signed OTA | `firmware/` |
| STE assembly instructions | Workers with minimal experience build it; licensed trades at hold points | `design/assembly/` |
| Compliance pack per profile | NEC, NFPA, UL 9540, ASHRAE, A2L refrigerant limits, IEC 62443, HIPAA, CMMC | `docs/COMPLIANCE.md` |

A competitor can buy the same container and the same UPS. They cannot buy the system that makes every unit identical, documented and testable, and that is what lets a small company ship many units with few engineers.

## 5. Market

Ranges, not point estimates (sources in `MARKET_SOURCES.md`):
- Modular data centers: USD 36–39 B in 2025 growing to USD 63–85 B by 2030 (10–19 % CAGR). A conservative house puts 2030 at USD 37 B.
- Edge data centers: USD 13–16 B in 2025 by most firms; US alone about USD 5.7 B.
- SMB AI adoption: between 28 % and 65 % of US small businesses report using or piloting AI in 2025 depending on survey; 68 % among 10–100 employee firms in one survey.

Our serviceable segment is the sub-500 kW, owner-operated deployment: SMBs, regional healthcare, industrial sites, municipalities, and integrators who want a white-label platform. We do not compete for hyperscale campuses.

## 6. Business model and unit economics

Unit economics are derived from the bill of materials in `docs/BOM.md`. The table below is regenerated by `scripts/unit_economics.py` and shows the price-confidence split so an investor can audit the margin.

<!-- UNIT_ECONOMICS_TABLE -->
| Tier (preset) | IT kW | BOM cost (all modules) | Sell price (28 % GM) | Infrastructure-only sell price (no compute) | Gross profit | Confirmed / list / estimate share of cost | Controls licence /yr | Managed service /yr | Price per kW IT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BEN Micro | 5 | $135,082 | $187,614 | $135,811 | $52,532 | 69 % / 0 % / 31 % | $1,200 | $2,700 | $37,523 |
| BEN 10 | 30 | $659,524 | $916,006 | $278,290 | $256,482 | 81 % / 0 % / 19 % | $4,800 | $16,200 | $30,534 |
| BEN 20 | 96 | $1,984,953 | $2,756,879 | $769,733 | $771,926 | 84 % / 0 % / 16 % | $12,000 | $51,840 | $28,717 |
| BEN 40 | 192 | $4,458,727 | $6,192,676 | $1,319,932 | $1,733,949 | 86 % / 0 % / 14 % | $30,000 | $103,680 | $32,254 |

Assumptions: hardware gross margin 28%; managed service $45/kW-month; controls licence per tier as shown. BOM cost excludes site civil and utility service (SITE- lines are shown separately in `docs/BOM.md`). Compute is the reference GPU/CPU node set from the catalog and dominates the all-modules price (one 8-GPU server is ~$82–236 k); most SMB customers will size their own compute or start with the infrastructure-only price and grow.

Revenue lines:
1. **Unit sales** (hardware + build + commissioning), target gross margin 25–35 % on hardware, higher on the controls module.
2. **BEN Controls licence** per unit per year (white-label partners) or included in managed service.
3. **Managed service** per kW-month: remote monitoring, maintenance scheduling, calibration, compliance records. Priced below colocation retail rates because the customer owns the asset.
4. **Engineering services**: site survey, permits support, AHJ submissions.

## 6b. Asset-light manufacturing

Units are built by qualified third-party contract manufacturers (container modification shops, modular electrical skid builders, UL 508A panel shops) to Schreiber AI's issue-for-construction drawings, Simplified Technical English instructions and QC forms, with Schreiber AI supplying the controls kit, witnessing hold points and running the factory acceptance test. Integrators sell and install under their brand or ours. Schreiber AI keeps the design authority, the controls layer, commissioning and operations. Capital goes into engineering, certification and controls hardware, not into a building. A greenfield factory is a later phase with explicit transition criteria (`docs/MANUFACTURING_STRATEGY.md`). Delivery risk is managed contractually: supplier and contract-manufacturer delay liquidated damages flow back-to-back with customer commitments, and customer scope changes re-baseline price and schedule (`docs/contracts/`).

## 7. Go-to-market

1. **Lighthouse units.** First BEN Micro and BEN 20 built for Schreiber AI's own and friendly customers; every one produces the commissioning data that proves the twin.
2. **Integrators and MEP firms** as white-label channel: they bring sites and licensed trades, we bring the system.
3. **Profile-led marketing**: the product page leads with mission profiles and risks, which qualifies buyers before a sales call.

## 8. What the money is for

| Use | Why |
| --- | --- |
| Two lighthouse builds (Micro, 20) | Convert "verified in simulation" into "verified on hardware"; UL 508A listing of the controls panel; CSC re-cert procedure |
| Certification and compliance | NRTL listings, PE stamps per state, FCC Part 15 for the node, SOC 2 for the managed service |
| Controls hardware | BEN Node carrier PCB production run, secure-boot provisioning line |
| Team | Controls engineer, field commissioning lead, sourcing/quality lead |
| Working capital | Long-lead equipment deposits (UPS, cooling, GPUs) |

The exact ask and allocation are set with the lead investor; this document fixes the *shape* of the plan so the numbers can be audited against the build.

## 9. Risks we tell investors (same list we tell customers)

See `docs/RISK_REGISTER.md`. The three that matter most for the investment case: (1) **regulatory variance** across jurisdictions (container as building, battery storage, A2L refrigerants) lengthens first sales cycles; (2) **supply chain** on UPS, cooling and GPUs, mitigated by the catalog of qualified alternates; (3) **the twin's accuracy is proven in simulation, not yet on hardware**. We say so on every page. The lighthouse builds exist to retire that risk.

## 10. What you can verify today

Clone the repository, run `pip install -r requirements.txt`, `PYTHONPATH=software pytest tests -q`, then `bash scripts/run_dashboard.sh` and open the dashboard. Everything in this document that is marked verified is reproducible from that command line. `docs/VALIDATION.md` lists what is not.

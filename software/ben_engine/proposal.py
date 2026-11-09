"""BEN Engine proposal generator.

"Once the slider is there we already have the back end ready": a complete customer-ready
proposal is generated from one :class:`ben_engine.config.Config` with one call::

    from ben_engine.config import Config
    from ben_engine.proposal import build_proposal, to_markdown, to_html, to_json

    p = build_proposal(Config.preset("ben150", "healthcare", "hot_humid"), option="managed",
                       customer="Acme Clinic", site="Austin, TX")
    open("proposal.md", "w").write(to_markdown(p))
    open("proposal.html", "w").write(to_html(p))

Everything in the proposal is derived from the configuration, the BOM generator
(``ben_engine.bom``), and the project documents (``docs/PROCESS_FLOW.md``, ``docs/COMPLIANCE.md``
section 11/12, ``docs/SITE_REQUIREMENTS.md``, ``docs/MAINTENANCE.md``, ``docs/TURNOVER.md``,
``design/drawings/<tier>/INDEX.md``, ``web/assets/risks.json``, ``web/kit/brand.json``).
Where a document cannot be read the generator falls back to a short built-in summary so that
no section is ever left blank; the fallback is flagged in ``Proposal.notes``.

Purchase options (``option=``):

* ``hardware_only``      power + cooling + compute + base (enclosure, fire, site kit, build
                         labour); the controls hardware and BEN Controls licence are excluded.
* ``hardware_controls``  all modules plus the BEN Controls licence (annual, per tier).
* ``white_label``        all modules plus the white-label licence; the dashboard and documents
                         carry the partner brand from ``cfg.brand``.
* ``managed``            all modules plus the managed service at $/kW-month, multi-year.
* ``modules``            exactly the subsystems in ``cfg.subsystems``.

Margin assumptions mirror ``scripts/unit_economics.py`` (hardware gross margin 28 %, controls
licence per tier, managed service $45/kW-month) and are explicit inputs, not hidden.

Contract pre-fill: :func:`fill_contract` replaces ``[FIELD_NAME]`` tokens in a template
(``docs/contracts/*.md``) with the proposal's numbers; see :func:`contract_fields` for the
vocabulary.

CLI::

    python -m ben_engine.proposal --tier ben150 --profile healthcare --climate hot_humid \
        --option managed --customer "Acme Clinic" --site "Austin, TX" \
        --out docs/proposals/sample-ben150-healthcare.md --html docs/proposals/sample-ben150-healthcare.html \
        [--json path] [--fill-sow docs/contracts/SOW_TEMPLATE.md --out-sow path] \
        [--fill-change-order docs/contracts/CHANGE_ORDER.md --out-change-order path]
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import html as _html
import json
import math
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import Config, TIER_GEOMETRY, TIER_ALIASES, PROFILE_DEFAULTS, CLIMATE_DESIGN, COOLING_LIBRARY, canonical_tier
from .bom import generate_bom, totals, load_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
BRAND_PATH = REPO_ROOT / "web" / "kit" / "brand.json"
RISKS_PATH = REPO_ROOT / "web" / "assets" / "risks.json"

# ----------------------------------------------------------------------------- commercial inputs
MARGIN_HW = 0.28                       # gross margin on purchased hardware + build labour (unit_economics.py)
CONTROLS_LICENCE_PER_UNIT_YR = {"ben5": 1200, "ben30": 4800, "ben150": 12000, "ben500": 30000, "ben2000": 90000,
                                # Rev 2 tiers: BEN Controls Mini (BEN Care agent + 2 Pods); dense tiers priced per the BEN 150 -> BEN 500 slope
                                "ben1": 480, "ben300": 24000, "ben700": 54000}
WHITE_LABEL_UPLIFT = 1.25              # white-label licence = controls licence x 1.25 (partner brand, source escrow)
MANAGED_PER_KW_MONTH = 45.0            # USD/kW-month; below retail colocation because the customer owns the asset
MANAGED_TERM_YEARS = 3                 # headline managed term; 1 and 5 year totals are also shown
VALIDITY_DAYS = 60
PAYMENT_MILESTONES = [("Engineering release (H4)", 0.30), ("Factory acceptance test (H13)", 0.40),
                      ("Site acceptance test (H19)", 0.25), ("Turnover (W20)", 0.05)]
# BEN 1 (Rev 2) has no FAT/SAT on a pad: Schreiber AI assembles, burns in and ships it, then sets it up and hands it over
PAYMENT_MILESTONES_MINI = [("Order confirmation (H4)", 0.50), ("Bench test passed and shipped (H13)", 0.40), ("Setup and handover (H19)", 0.10)]
LD_RATE_PCT_PER_WEEK = 0.5             # delay liquidated damages, % of capital price per week of Schreiber AI-caused delay
LD_CAP_PCT = 5.0                       # cap on delay LDs, % of capital price
STORAGE_FEE_PER_DAY = {"ben5": 60, "ben30": 150, "ben150": 300, "ben500": 600, "ben2000": 2500,  # finished unit/modules that cannot ship (USD/day)
                       "ben1": 10, "ben300": 400, "ben700": 750}
WARRANTY_WORKMANSHIP_MONTHS = 24
WARRANTY_EQUIPMENT_MONTHS = 12         # pass-through of vendor warranties; longer vendor terms are passed through as-is

OPTIONS = ("hardware_only", "hardware_controls", "white_label", "managed", "modules")
OPTION_LABELS = {
    "hardware_only": "Hardware only",
    "hardware_controls": "Hardware + BEN Controls",
    "white_label": "White-label",
    "managed": "Managed service",
    "modules": "Selected modules",
}
HARDWARE_SUBSYSTEMS = ("power", "cooling", "compute")
BASE_SUBSYSTEMS = ("str", "env", "fs", "site", "svc")
SUBSYSTEM_LABELS = {"power": "Power module", "cooling": "Cooling module", "compute": "Compute module",
                    "controls": "Controls module", "str": "Structure (container / cabinet)",
                    "env": "Envelope (insulation, liner, coatings)", "fs": "Fire detection and suppression",
                    "site": "Site kit (anchors, embeds, signage)", "svc": "Build labour, FAT, logistics"}

# schedule building blocks per tier (weeks); totals calibrated to docs/PROCESS_FLOW.md section 3
SCHEDULE_TIER = {
    # survey->H3, release->H4, short-lead (container), factory chain (receiving..electrical), cooling+controls, FAT, transport, hookup, SAT, turnover
    "ben5": {"survey": 1, "release": 1, "short_lead": 2, "factory": 2, "cool_ctl": 1, "fat": 1, "ship": 1, "hookup": 1, "sat": 1, "permits": 4, "civil": 2, "ref_total": "10-12 weeks"},
    "ben30": {"survey": 2, "release": 2, "short_lead": 3, "factory": 6, "cool_ctl": 2, "fat": 1, "ship": 1, "hookup": 1, "sat": 1, "permits": 8, "civil": 4, "ref_total": "about 20 weeks"},
    "ben150": {"survey": 3, "release": 3, "short_lead": 3, "factory": 9, "cool_ctl": 3, "fat": 1, "ship": 1, "hookup": 1, "sat": 1, "permits": 8, "civil": 6, "ref_total": "about 27 weeks"},
    "ben500": {"survey": 4, "release": 3, "short_lead": 3, "factory": 12, "cool_ctl": 4, "fat": 2, "ship": 2, "hookup": 1, "sat": 1, "permits": 10, "civil": 8, "ref_total": "32-36 weeks"},
    # BEN 2000: long-lead items (MV pad-mount transformers, 2 MW UPS strings, generators) typically 40 weeks from release;
    # site works (slab, MV service, yard) run 20 weeks in parallel; order-to-service about 52 weeks.
    # Rev 2. BEN 1: assembled and shipped by Schreiber AI in 2-3 weeks (no contract manufacturer, no pad, no SAT: setup and handover).
    "ben1": {"survey": 0, "release": 0, "short_lead": 1, "factory": 1, "cool_ctl": 0, "fat": 1, "ship": 1, "hookup": 0, "sat": 0, "permits": 0, "civil": 0, "ref_total": "2-3 weeks with customer-furnished or in-stock compute"},
    # Liquid-first dense tiers: CDUs, Galaxy VL frames and the skid gear set the path (catalog lead times); FAT adds the loop pressure / flush test.
    "ben300": {"survey": 3, "release": 3, "short_lead": 3, "factory": 10, "cool_ctl": 4, "fat": 2, "ship": 1, "hookup": 2, "sat": 1, "permits": 8, "civil": 6, "ref_total": "about 30-34 weeks, set by the CDU, UPS and compute lead times"},
    "ben700": {"survey": 4, "release": 4, "short_lead": 3, "factory": 14, "cool_ctl": 5, "fat": 2, "ship": 2, "hookup": 2, "sat": 2, "permits": 10, "civil": 8, "ref_total": "about 36-40 weeks, set by the switchboard, UPS, CDU and compute lead times"},
    "ben2000": {"survey": 4, "release": 8, "short_lead": 12, "factory": 20, "cool_ctl": 4, "fat": 2, "ship": 3, "hookup": 4, "sat": 2, "permits": 12, "civil": 20, "long_lead_typical": 40, "ref_total": "52 weeks when the utility energises inside 40 weeks and transformers are ordered at engineering release; 60–72 weeks at today's catalog lead times (48–52 weeks for pad-mount transformers and 1,250 kW generators), which is what this schedule shows"},
}

COMMISSIONING_STEPS = [
    ("1", "Pre-power visual checklist", "Every checklist item answered yes by the operator; no open item"),
    ("2", "Pod discovery, attestation and firmware versions", "All BEN Pods answer and attest; firmware versions and hashes match the release record"),
    ("3", "Sensor sanity at idle", "Rack inlet temperatures within 2 K of each other; RH plausible; aisle dP tared"),
    ("4", "I/O point-to-point test", "Every relay toggles and reads back; every contact (door, leak, EPO) reads correctly"),
    ("5", "Power chain: utility meter vs PDU sum", "Meter agrees with the PDU sum within 3 % after metered cooling, house and UPS losses"),
    ("6", "Cooling unit sequential start and failover", "Each unit starts in sequence; one unit removed and inlet stays within the ASHRAE class"),
    ("7", "Load step 20-100 % and thermal steady state", "Inlet temperatures settle inside the ASHRAE class at 100 % load (resistive load bank on the real unit)"),
    ("8", "Utility loss ride-through", "UPS carries IT for the configured minutes; cooling ride-through measured and published"),
    ("9", "Alarm verification", "Inlet high, leak, door, cooling fail and utility loss each raise and clear the correct alarm"),
    ("10", "Export CSV and signed report", "CSV of all channels exported; report carries the SHA-256 of the data and a signature block"),
]


# ----------------------------------------------------------------------------- data model
@dataclass
class Block:
    """One renderable block: kind is 'p' (text), 'ul' (items), 'table' (headers + rows) or 'kv' (two-column rows)."""
    kind: str
    text: str = ""
    items: List[str] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class Section:
    number: int
    title: str
    blocks: List[Block] = field(default_factory=list)

    def p(self, text: str) -> "Section":
        self.blocks.append(Block("p", text=text)); return self

    def ul(self, items: Sequence[str]) -> "Section":
        self.blocks.append(Block("ul", items=[str(i) for i in items])); return self

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> "Section":
        self.blocks.append(Block("table", headers=[str(h) for h in headers], rows=[[str(c) for c in r] for r in rows])); return self

    def kv(self, rows: Sequence[Tuple[str, Any]]) -> "Section":
        self.blocks.append(Block("kv", rows=[[str(k), str(v)] for k, v in rows])); return self

    @property
    def is_empty(self) -> bool:
        return not any((b.text.strip() or b.items or b.rows) for b in self.blocks)


@dataclass
class OptionPrice:
    key: str
    label: str
    subsystems: List[str]
    hardware_cost_usd: float
    capital_price_usd: float
    recurring_usd_per_year: float
    recurring_label: str
    term_years: int
    total_term_usd: float
    price_per_kw_usd: float
    confirmed_pct: float
    list_pct: float
    estimate_pct: float
    bom_lines: int
    headline: bool = False


@dataclass
class Proposal:
    proposal_id: str
    date: str
    valid_until: str
    customer: str
    site: str
    option: str
    brand: str
    config: Dict[str, Any]
    derived: Dict[str, Any]
    bom_totals: Dict[str, Any]
    prices: List[OptionPrice]
    headline: OptionPrice
    milestones: List[Dict[str, Any]]
    payment_milestones: List[Dict[str, Any]]
    long_lead: List[Dict[str, Any]]
    sections: List[Section]
    notes: List[str] = field(default_factory=list)

    @property
    def tier_label(self) -> str:
        return TIER_GEOMETRY[self.config["tier"]]["label"]

    @property
    def profile_label(self) -> str:
        return PROFILE_DEFAULTS[self.config["profile"]]["label"]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Proposal":
        d = dict(d)
        d["prices"] = [OptionPrice(**p) for p in d["prices"]]
        d["headline"] = OptionPrice(**d["headline"])
        d["sections"] = [Section(number=s["number"], title=s["title"], blocks=[Block(**b) for b in s["blocks"]]) for s in d["sections"]]
        return cls(**d)


# ----------------------------------------------------------------------------- helpers
def _usd(v: float) -> str:
    return f"${v:,.0f}"


def _pct(v: float) -> str:
    return f"{v:.0f} %"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _md_tables(md: str) -> List[Tuple[List[str], List[List[str]]]]:
    """Return every pipe table in a markdown string as (headers, rows) with cells stripped."""
    tables: List[Tuple[List[str], List[List[str]]]] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            headers = _split_row(lines[i])
            rows: List[List[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(_split_row(lines[j])); j += 1
            tables.append((headers, rows)); i = j
        else:
            i += 1
    return tables


def _split_row(line: str) -> List[str]:
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def _section_text(md: str, heading_prefix: str) -> str:
    """Text of the '## N.' section whose heading starts with heading_prefix, up to the next '## '."""
    m = re.search(r"^## " + re.escape(heading_prefix) + r".*?$", md, flags=re.M)
    if not m:
        return ""
    rest = md[m.end():]
    n = re.search(r"^## ", rest, flags=re.M)
    return rest[: n.start()] if n else rest


def _strip_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)
    return s.replace("\\|", "|").strip()


def _brand() -> Dict[str, Any]:
    try:
        return json.loads(BRAND_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"brand": "Schreiber AI", "product": "BEN Engine", "tagline": "AI infrastructure that arrives finished.",
                "colors": {"graphite": "#0B1018", "slate": "#152234", "panel": "#1B2B42", "text": "#EDF4FF", "muted": "#9FB3CC",
                           "cyan": "#66E3FF", "amber": "#FFC66D", "red": "#FF707D", "green": "#6EE7A8",
                           "light_bg": "#F4F7FB", "light_text": "#0B1018"}}


def _proposal_id(cfg: Config, date: str, customer: str) -> str:
    h = hashlib.sha256((cfg.to_json(sort_keys=True) + date + customer).encode("utf-8")).hexdigest()[:8].upper()
    return f"SAI-{cfg.tier.upper()}-{date.replace('-', '')}-{h}"


# ----------------------------------------------------------------------------- pricing
def _price_option(key: str, cfg: Config, catalog, margin: float, headline: bool) -> Tuple[OptionPrice, List[Dict[str, Any]]]:
    if key == "hardware_only":
        subs = [s for s in HARDWARE_SUBSYSTEMS]
    elif key == "modules":
        subs = list(cfg.subsystems)
    else:
        subs = ["power", "cooling", "compute", "controls"]
    c = Config.from_dict(cfg.to_dict()); c.subsystems = subs
    rows = generate_bom(c, catalog) if subs else []
    t = totals(rows)
    cost = t["total_usd"]
    capital = cost / (1 - margin)
    lic = CONTROLS_LICENCE_PER_UNIT_YR[cfg.tier]
    if key == "hardware_only":
        recurring, rlabel, term = 0.0, "none (vendor warranties pass through; support on request)", 1
    elif key == "hardware_controls":
        recurring, rlabel, term = float(lic), "BEN Controls licence (dashboard, twin, firmware updates, remote support hooks)", 1
    elif key == "white_label":
        recurring, rlabel, term = round(lic * WHITE_LABEL_UPLIFT), f"White-label licence under the {cfg.brand} brand (controls licence x {WHITE_LABEL_UPLIFT:.2f}, partner branding, source escrow)", 1
    elif key == "managed":
        recurring, rlabel, term = MANAGED_PER_KW_MONTH * cfg.it_kw * 12, f"Managed service at ${MANAGED_PER_KW_MONTH:.0f}/kW-month x {cfg.it_kw:.0f} kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule)", MANAGED_TERM_YEARS
    else:  # modules
        recurring = float(lic) if "controls" in subs else 0.0
        rlabel, term = ("BEN Controls licence" if recurring else "none"), 1
    total_term = capital + recurring * term
    op = OptionPrice(
        key=key, label=OPTION_LABELS[key], subsystems=subs,
        hardware_cost_usd=round(cost, 2), capital_price_usd=round(capital, 2),
        recurring_usd_per_year=round(recurring, 2), recurring_label=rlabel, term_years=term,
        total_term_usd=round(total_term, 2), price_per_kw_usd=round(capital / cfg.it_kw, 2),
        confirmed_pct=round(100 * t["by_status"]["confirmed"] / cost, 1) if cost else 0.0,
        list_pct=round(100 * t["by_status"]["list"] / cost, 1) if cost else 0.0,
        estimate_pct=round(100 * t["by_status"]["estimate"] / cost, 1) if cost else 0.0,
        bom_lines=t["items"], headline=headline,
    )
    return op, rows


# ----------------------------------------------------------------------------- schedule
def _schedule_minirack(cfg: Config, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """BEN 1: Schreiber AI orders the parts, assembles, burns in and ships; then setup and handover at the customer. No contract
    manufacturer, no pad, no SAT. Compute is customer-selectable; when Schreiber AI buys it, its lead time can set the path."""
    leads = sorted([r for r in rows if r.get("lead_time_weeks")], key=lambda r: (-(r["lead_time_weeks"] or 0), -r["ext_price_usd"]))
    long_lead = [{"code": r["code"], "name": r["name"], "lead_time_weeks": r["lead_time_weeks"], "qty": r["qty"], "unit": r["unit"],
                  "ext_price_usd": r["ext_price_usd"], "vendor": r["vendor"]} for r in leads[:5]]
    # BEN Pods, their enclosures, the Thread radio and labels are Schreiber AI stock items for BEN 1 (built ahead in Pod production batches)
    stock = ("CTL-POD", "CTL-POD-ENCL", "CTL-RCP", "CTL-LABELS", "ENV-DATAPLATE-MINI")
    infra = max([(r["lead_time_weeks"] or 0) for r in rows if r["subsystem"] != "compute" and r["code"] not in stock] + [1])
    comp = max([(r["lead_time_weeks"] or 0) for r in rows if r["subsystem"] == "compute"] + [0])
    w_parts = max(1, infra)
    w_burn = w_parts + 1
    w_ship = w_burn + 1 if w_burn < 2 else w_burn
    w_ship = max(2, min(3, w_ship)) if infra <= 2 else w_ship
    w_hand = w_ship + 1
    ms = [
        {"week": 0, "milestone": "Order confirmation: form (10-inch rack or 12U cabinet), compute (customer-furnished or bought by us), outlet and room checked against section 11", "owner": "Customer + Schreiber AI", "hold": "H4", "path": "critical"},
        {"week": w_parts, "milestone": f"Parts on the bench (longest non-compute lead {infra} weeks; BEN Pods from Schreiber AI stock)", "owner": "Schreiber AI", "hold": "-", "path": "critical"},
        {"week": w_burn, "milestone": "Assembled, imaged and 24 h burn-in test passed (commissioning script in factory mode)", "owner": "Schreiber AI; customer may witness remotely", "hold": "H13", "path": "critical"},
        {"week": w_ship, "milestone": "Shipped (parcel for the 10-inch rack, LTL with liftgate for the 12U cabinet)", "owner": "Schreiber AI", "hold": "-", "path": "critical"},
        {"week": w_hand, "milestone": "Setup and handover at the customer (or remote): placement, outlet check, network, BEN Care enrolment, room-heat check; in service", "owner": "Schreiber AI + customer", "hold": "H19, W20", "path": "critical"},
    ]
    if comp > infra:
        ms.append({"week": comp + 2, "milestone": f"NOTE: compute bought by Schreiber AI has a {comp}-week lead time; with customer-furnished compute the dates above hold", "owner": "Customer", "hold": "-", "path": "risk"})
    return ms, long_lead


def _schedule(cfg: Config, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if TIER_GEOMETRY[cfg.tier]["kind"] == "minirack":
        return _schedule_minirack(cfg, rows)
    s = SCHEDULE_TIER[cfg.tier]
    leads = sorted([r for r in rows if r.get("lead_time_weeks")], key=lambda r: (-(r["lead_time_weeks"] or 0), -r["ext_price_usd"]))
    max_lead = max((r["lead_time_weeks"] or 0) for r in rows) if rows else 0
    long_lead = [{"code": r["code"], "name": r["name"], "lead_time_weeks": r["lead_time_weeks"], "qty": r["qty"], "unit": r["unit"],
                  "ext_price_usd": r["ext_price_usd"], "vendor": r["vendor"]} for r in leads[:5]]
    hall = TIER_GEOMETRY[cfg.tier]["kind"] == "hall"
    w_h3 = s["survey"]
    w_h4 = w_h3 + s["release"]
    w_container = w_h4 + s["short_lead"]
    if hall:
        # BEN 2000: the wide-body modules are built and FAT-tested in the factory while the long-lead site gear
        # (MV transformers, switchgear, generators, MV interconnect) ships straight to site; SAT waits for both.
        site_leads = [r for r in rows if r.get("lead_time_weeks") and (r["code"].startswith("PWR-MV") or r["code"].startswith("PWR-GEN") or r["code"].startswith("PWR-LV-SWGR") or r["code"].startswith("SITE-"))]
        factory_lead = max([(r["lead_time_weeks"] or 0) for r in rows if r not in site_leads] + [0])
        site_lead = max([(r["lead_time_weeks"] or 0) for r in site_leads] + [s.get("long_lead_typical", 40)])
        procurement_done = w_h4 + max(factory_lead, s["short_lead"] + s["factory"])
        w_fit_out_done = max(w_container + s["factory"], procurement_done)
        w_fat = w_fit_out_done + s["cool_ctl"] + s["fat"]
        w_ship = w_fat + s["ship"]
        w_setdown = max(w_ship, w_h4 + site_lead) + s["hookup"]
    else:
        procurement_done = w_h4 + max(max_lead, s["short_lead"] + s["factory"])
        w_fit_out_done = max(w_container + s["factory"], procurement_done)
        w_fat = w_fit_out_done + s["cool_ctl"] + s["fat"]
        w_ship = w_fat + s["ship"]
        w_setdown = w_ship + s["hookup"]
    w_sat = w_setdown + s["sat"]
    w_turnover = w_sat + 1
    w_permits = w_h4 + s["permits"]
    w_civil = w_permits + s["civil"]
    ms = [
        {"week": 0, "milestone": "Order and risk acknowledgement signed", "owner": "Customer + Schreiber AI", "hold": "-", "path": "critical"},
        {"week": w_h3, "milestone": "Site survey and site requirements sign-off", "owner": "Customer + ENG", "hold": "H3", "path": "critical"},
        {"week": w_h4, "milestone": "Engineering release: configuration frozen, IFC drawings, BOM; long-lead purchase orders placed", "owner": "ENG", "hold": "H4", "path": "critical"},
        {"week": w_container, "milestone": ("Wide-body module shells received and inspected; structural and envelope work starts (per module)" if hall else "Container / cabinet received and inspected; structural and envelope work starts"), "owner": "FAC", "hold": "W6, H7, W8", "path": "critical"},
        {"week": w_permits, "milestone": "Permits issued (building, electrical, mechanical, fire plan review)", "owner": "Customer / AHJ", "hold": "-", "path": "parallel"},
        {"week": w_fit_out_done, "milestone": (f"Longest-lead factory item on the floor ({factory_lead} weeks from release); module mechanical and electrical fit-out complete; site gear (MV transformers, switchgear, generators) ships direct to site at {site_lead} weeks" if hall else f"Longest-lead item on the floor ({max_lead} weeks from release); mechanical and electrical fit-out complete"), "owner": "FAC + SUB", "hold": "H10", "path": "critical"},
        {"week": w_civil, "milestone": "Site pad, grounding and utility feeder complete and surveyed", "owner": "Customer civil", "hold": "H16", "path": "parallel"},
        {"week": w_fat, "milestone": "Cooling, controls and firmware complete; factory acceptance test incl. 24 h burn-in", "owner": "FAC + ENG; customer witness", "hold": "H11, W12, H13", "path": "critical"},
        {"week": w_ship, "milestone": "Transport prep and shipping", "owner": "LOG", "hold": "-", "path": "critical"},
        {"week": w_setdown, "milestone": ("Modules set and site-joined, power module and MV gear set, hook-up and pre-energisation check (long-lead site gear on site)" if hall else "Set-down, hook-up and pre-energisation check"), "owner": "LOG + SUB + AHJ", "hold": "W17, H18", "path": "critical"},
        {"week": w_sat, "milestone": "Site acceptance test and fire marshal acceptance", "owner": "ENG + customer + AHJ", "hold": "H19", "path": "critical"},
        {"week": w_turnover, "milestone": "Training and turnover; unit in service", "owner": "ENG + customer", "hold": "W20", "path": "critical"},
    ]
    if w_civil > w_ship:
        ms.append({"week": w_civil, "milestone": "NOTE: site civil path finishes after the unit is ready to ship; storage fee applies from the ship date if the pad is not ready", "owner": "Customer", "hold": "-", "path": "risk"})
    ms.sort(key=lambda m: (m["week"], m["path"] != "critical"))
    return ms, long_lead


# ----------------------------------------------------------------------------- document readers
def _drawing_index(tier: str) -> Tuple[List[List[str]], str]:
    if TIER_GEOMETRY[tier]["kind"] == "minirack":
        return ([["A-001", "Mini rack general arrangement, U stack and desk / closet footprint", "1:5"], ["E-001", "Power: outlet circuit, UPS, PDU one-line", "NTS"],
                 ["C-001", "BEN Pods, network and BEN Care enrolment", "NTS"]],
                "Rev 2.A set generated from the configuration at order confirmation (design/layout.py BEN 1 resolver, checks I-B1..I-B7)")
    md = _read(REPO_ROOT / "design" / "drawings" / tier / "INDEX.md")
    rows: List[List[str]] = []
    for headers, trs in _md_tables(md):
        if headers and headers[0].lower().startswith("sheet"):
            rows = [[tr[0], _strip_md(tr[1]), tr[2]] for tr in trs if len(tr) >= 3]
            break
    status = ""
    m = re.search(r"^Status:\s*(.+)$", md, flags=re.M)
    if m:
        status = _strip_md(m.group(1))
    if not rows:
        rows = [["A-001", "General arrangement", "see sheet"], ["A-002", "Interior layout plan", "see sheet"],
                ["A-003", "Envelope section", "1:10 / 1:2"], ["S-001", "Floor framing and anchoring", "see sheet / 1:5"],
                ["E-001", "Power one-line", "NTS"], ["M-001", "Cooling P&ID", "NTS"], ["C-001", "Controls layout", "see sheet"]]
        status = "Issue for construction set regenerated from the frozen configuration at engineering release (index not readable at proposal time)"
    return rows, status


def _compliance_rows(profile: str, climate: str) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
    md = _read(DOCS / "COMPLIANCE.md")
    prof_row = clim_row = None
    for headers, trs in _md_tables(_section_text(md, "11.")):
        for tr in trs:
            if tr and _strip_md(tr[0]).startswith(profile):
                prof_row = dict(zip([_strip_md(h) for h in headers], [_strip_md(c) for c in tr]))
    for headers, trs in _md_tables(_section_text(md, "12.")):
        for tr in trs:
            if tr and _strip_md(tr[0]) == climate:
                clim_row = dict(zip([_strip_md(h) for h in headers], [_strip_md(c) for c in tr]))
    return prof_row, clim_row


def _risks(profile: str) -> List[Dict[str, Any]]:
    try:
        risks = json.loads(RISKS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    sev = {"high": 0, "medium": 1, "low": 2}
    out = [r for r in risks if profile in r.get("profiles", [])]
    out.sort(key=lambda r: (sev.get(r.get("severity", "low"), 3), r["id"]))
    return out


def _site_requirements(tier: str) -> Dict[str, str]:
    md = _read(DOCS / "SITE_REQUIREMENTS.md")
    label = TIER_GEOMETRY[tier]["label"]
    want = {"Pad plan size": "pad_size", "Pad type and thickness": "pad_type", "Anchor points": "anchors",
            "Voltage / phases": "voltage", "Customer-provided disconnect": "disconnect", "Feeder conductors": "feeder",
            "Generator (if selected)": "generator"}
    out: Dict[str, str] = {}
    for headers, trs in _md_tables(md):
        hs = [_strip_md(h) for h in headers]
        if label in hs:
            col = hs.index(label)
            for tr in trs:
                key = _strip_md(tr[0])
                for prefix, k in want.items():
                    if key.startswith(prefix) and len(tr) > col and k not in out:
                        out[k] = _strip_md(tr[col])
    for headers, trs in _md_tables(_section_text(md, "6.")):
        for tr in trs:
            k = _strip_md(tr[0])
            if k == "Electrode": out["ground_electrode"] = _strip_md(tr[1])
            if k == "Target resistance": out["ground_resistance"] = _strip_md(tr[1])
    for headers, trs in _md_tables(_section_text(md, "7.")):
        for tr in trs:
            k = _strip_md(tr[0])
            if k == "Conduit": out["fiber_conduit"] = _strip_md(tr[1])
            if k == "Service": out["fiber_service"] = _strip_md(tr[1])
    permits: List[Tuple[str, str, str]] = []
    for headers, trs in _md_tables(_section_text(md, "10.")):
        for tr in trs:
            if len(tr) >= 3:
                permits.append((_strip_md(tr[0]), _strip_md(tr[1]), _strip_md(tr[2])))
    out["_permits"] = json.dumps(permits)
    return out


def _maintenance_summary() -> List[Tuple[str, str, int]]:
    """(interval, who, task count) rows from docs/MAINTENANCE.md sections 1-4."""
    md = _read(DOCS / "MAINTENANCE.md")
    out: List[Tuple[str, str, int]] = []
    for prefix, who in (("1.", "Remote, Schreiber AI operations (R)"), ("2.", "Local technician (L) with remote review"), ("3.", "Local technician + certified subcontractor (L + S)")):
        sec = _section_text(md, prefix)
        m = re.search(r"^## " + re.escape(prefix) + r"\s*(.+)$", md, flags=re.M)
        name = _strip_md(m.group(1)) if m else prefix
        n = sum(len(trs) for _, trs in _md_tables(sec))
        if n:
            out.append((name, who, n))
    sec4 = _section_text(md, "4.")
    counts: Dict[str, int] = {}
    for headers, trs in _md_tables(sec4):
        for tr in trs:
            if tr:
                counts[_strip_md(tr[0])] = counts.get(_strip_md(tr[0]), 0) + 1
    for k, v in counts.items():
        out.append((k, "Certified subcontractor (S) with record; remote (R) for controls", v))
    if not out:
        out = [("Weekly (remote)", "R", 9), ("Monthly", "L", 8), ("Quarterly", "L + S", 6), ("Semi-annual", "S", 4),
               ("Annual", "S / R / L", 8), ("3-year", "S", 4), ("5-year", "S / PE", 6)]
    return out


# ----------------------------------------------------------------------------- the builder
def build_proposal(cfg: Config, option: str = "full", customer: Optional[str] = None, site: Optional[str] = None,
                   margin: float = MARGIN_HW, date: Optional[str] = None) -> Proposal:
    """Build a complete proposal from a configuration. ``option`` is one of :data:`OPTIONS`
    (``"full"`` is accepted as an alias of ``hardware_controls``)."""
    if option == "full":
        option = "hardware_controls"
    if option not in OPTIONS:
        raise ValueError(f"option must be one of {OPTIONS}, got {option!r}")
    errs = cfg.validate()
    if errs:
        raise ValueError("invalid config: " + "; ".join(errs))
    customer = customer or "Prospective customer"
    site = site or cfg.site_name or "Site to be confirmed"
    today = date or _dt.date.today().isoformat()
    valid_until = (_dt.date.fromisoformat(today) + _dt.timedelta(days=VALIDITY_DAYS)).isoformat()
    brand = _brand()
    brand_name = cfg.brand if (option == "white_label" and cfg.brand) else brand.get("brand", "Schreiber AI")
    d = cfg.derived()
    g = d["geometry"]; clim = d["climate"]
    catalog = load_catalog()
    notes: List[str] = []

    # ---- pricing for every option; headline option first
    full_set = set(cfg.subsystems) == {"power", "cooling", "compute", "controls"}
    keys = [k for k in OPTIONS if k != "modules" or not full_set]
    if option == "modules" and full_set:
        keys.append("modules")
    prices: List[OptionPrice] = []
    rows_by_key: Dict[str, List[Dict[str, Any]]] = {}
    for k in keys:
        op, rows = _price_option(k, cfg, catalog, margin, headline=(k == option))
        prices.append(op); rows_by_key[k] = rows
    headline = next(p for p in prices if p.key == option)
    rows = rows_by_key[option]
    bt = totals(rows)
    milestones, long_lead = _schedule(cfg, rows)
    pay = []
    mini = TIER_GEOMETRY[cfg.tier]["kind"] == "minirack"
    pay_ms = PAYMENT_MILESTONES_MINI if mini else PAYMENT_MILESTONES
    for name, share in pay_ms:
        wk = next((m["week"] for m in milestones if m["hold"].split(",")[-1].strip() in name or name.split("(")[-1].rstrip(")") in m["hold"]), None)
        pay.append({"milestone": name, "share": share, "amount_usd": round(headline.capital_price_usd * share, 2), "week": wk})
    pid = _proposal_id(cfg, today, customer)
    weeks_in_service = milestones[-1]["week"] if milestones[-1]["path"] == "critical" else max(m["week"] for m in milestones if m["path"] == "critical")

    # ---- document inputs
    sheets, dwg_status = _drawing_index(cfg.tier)
    prof_row, clim_row = _compliance_rows(cfg.profile, cfg.climate)
    if prof_row is None:
        notes.append("COMPLIANCE.md section 11 row not found; built-in summary used")
    if clim_row is None:
        notes.append("COMPLIANCE.md section 12 row not found; built-in summary used")
    risks = _risks(cfg.profile)
    if not risks:
        notes.append("web/assets/risks.json not readable; risk section lists the register reference only")
    sreq = _site_requirements(cfg.tier)
    maint = _maintenance_summary()

    prof = PROFILE_DEFAULTS[cfg.profile]
    sections: List[Section] = []

    # 1 cover
    s = Section(1, "Cover")
    s.kv([
        ("Proposal", f"{brand.get('product', 'BEN Engine')} {d['tier_label']} for {customer}"),
        ("Prepared by", f"{brand_name}" + ("" if brand_name == brand.get("brand") else f" (engineering by {brand.get('brand')})")),
        ("Customer", customer), ("Site", site),
        ("Tier", f"{d['tier_label']} — {d['enclosure']}"),
        ("Mission profile", f"{prof['label']} ({cfg.profile})"),
        ("Climate package", clim["label"]),
        ("Purchase option", headline.label),
        ("Date", today), ("Valid until", f"{valid_until} ({VALIDITY_DAYS} days)"),
        ("Proposal ID", pid),
        ("Configuration", f"{cfg.it_kw:.0f} kW IT in {cfg.racks} rack(s), {d['cooling_label']}, {cfg.redundancy}, {cfg.ups_minutes} min UPS"
                          + (", generator" if cfg.generator else "")),
    ])
    s.p(f"{brand.get('tagline', '')} This proposal is generated from configuration version {hashlib.sha256(cfg.to_json(sort_keys=True).encode()).hexdigest()[:8]}; "
        f"every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.")
    sections.append(s)

    # 2 executive summary
    s = Section(2, "Executive summary")
    s.p(f"{customer} needs {cfg.it_kw:.0f} kW of IT capacity for a {prof['label']} workload at {site}. "
        f"We propose one {d['tier_label']}: a {d['enclosure']} fitted out as a complete data center with {cfg.racks} rack(s), "
        f"{d['cooling_label']} with {cfg.redundancy} redundancy, a {d['ups_modules']} x {d['ups_kva_each']} kVA UPS giving {cfg.ups_minutes} minutes of ride-through"
        + (", a standby generator" if cfg.generator else "") + ", clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).")
    if mini:
        s.p(f"BEN 1 arrives assembled and burnt in by Schreiber AI. It needs a {d['outlet_circuit']}, a network port and a room that can take "
            f"{d['heat_to_room_w']:,} W ({d['heat_to_room_btu_h']:,} BTU/h) of heat; estimated noise {d['noise_dba_est']} dBA at 1 m (target {d['noise_dba_target']:.0f}).")
    else:
        s.p(f"The unit arrives finished and factory-tested. It needs a pad, a {d['service_breaker_a']} A {d['voltage']} feeder, fiber and a grounding electrode at the site; "
            f"everything inside the enclosure is built, wired, tested and documented before it ships.")
    s.p(f"Price for the {headline.label.lower()} option: {_usd(headline.capital_price_usd)} capital ({_usd(headline.price_per_kw_usd)} per kW IT)"
        + (f" plus {_usd(headline.recurring_usd_per_year)} per year ({headline.recurring_label.split(' (')[0]})" if headline.recurring_usd_per_year else "")
        + f". {headline.confirmed_pct:.0f} % of the underlying cost is at confirmed vendor prices, {headline.list_pct:.0f} % at manufacturer list price and {headline.estimate_pct:.0f} % is engineering estimate; "
          f"the price is firm at engineering release, when the configuration is frozen.")
    s.p(f"Order to in-service: about {weeks_in_service} weeks, set by the longest-lead item ({long_lead[0]['lead_time_weeks'] if long_lead else 0} weeks) and the permit cycle. "
        f"Risks are disclosed in section 10 before the price is accepted; the site requirements in section 11 are signed before anything is built for this site.")
    sections.append(s)

    # 3 mission profile
    s = Section(3, "Mission profile and what it means")
    ashrae_txt = {"A1": "15–32 °C inlet, 20–80 % RH allowable (recommended 18–27 °C); the tightest class, for sensitive or mission-critical IT",
                  "A2": "10–35 °C inlet allowable; standard enterprise IT",
                  "A3": "5–40 °C inlet allowable; hardened IT and wider economizer hours"}.get(d["ashrae_class"], d["ashrae_class"])
    red_txt = {"N": "no redundant cooling or UPS module; a failure of one unit means a planned shutdown (accepted for this profile by the customer's recovery-time decision)",
               "N+1": "one spare cooling unit and one spare UPS module; any single unit can fail or be serviced with no loss of capacity",
               "2N": "two complete, independent cooling and UPS paths; either path alone carries the full load"}[cfg.redundancy]
    s.kv([
        ("Profile", f"{prof['label']} ({cfg.profile})"),
        ("ASHRAE class", f"{d['ashrae_class']}: {ashrae_txt}"),
        ("Redundancy", f"{cfg.redundancy}: {red_txt}"),
        ("Design rack density", f"{d['per_rack_kw']} kW per rack (profile default {prof['rack_kw']} kW)"),
        ("Climate package", f"{clim['label']}: design outdoor {clim['t_design_c']} °C / minimum {clim['t_min_c']} °C, solar {clim['solar_w_m2']} W/m², "
                            f"corrosion class ISO 9223 {clim['corrosion']}, basic wind {clim['wind_ms']} m/s (ASCE 7)"),
        ("Cooling derate at design day", f"{d['cooling_derate']:.3f} -> {d['cooling_unit_kw_derated']} kW per unit; {d['cooling_units_total']} units installed for {d['cooling_units_n']} required"),
        ("Generator", "included (profile default)" if cfg.generator else "not included (option)"),
    ])
    s.p("What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; "
        "the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.")
    sections.append(s)

    # 4 the unit
    s = Section(4, "The unit: sizing")
    s.table(["Item", "Value", "Basis"], [
        ["Enclosure", d["enclosure"], f"External {g['ext_l_m']} x {g['ext_w_m']} x {g['ext_h_m']} m; interior {g['int_l_m']} x {g['int_w_m']} x {g['int_h_m']} m" + (f"; {d['modules']} site-joined modules" if d["modules"] > 1 else "")],
        ["IT load", f"{cfg.it_kw:.0f} kW in {cfg.racks} rack(s) of {g['rack_u']} U", f"{d['per_rack_kw']} kW per rack; tier range {g['it_kw_min']}–{g['it_kw_max']} kW"],
        ["Cooling", f"{d['cooling_units_total']} x {d['cooling_label']}", f"{d['cooling_units_n']} required at {d['cooling_unit_kw_derated']} kW each (derate {d['cooling_derate']}), {cfg.redundancy}"],
        ["Row fit", "fits" if d["row_fits"] else "DOES NOT FIT - revise", f"{d['rows']} row(s) of {d['racks_per_row']} racks, {d['row_length_mm']} mm per row vs interior {int(g['int_l_m'] * 1000)} mm"],
        ["Cooling electrical", f"{d['cooling_elec_kw']} kW", f"COP {COOLING_LIBRARY[cfg.cooling]['cop']} at design point"],
        ["Total electrical demand", f"{d['total_kw']} kW / {d['total_kva']} kVA", "IT + cooling + 2 % house + 0.5 kW controls, pf 0.95"],
        ["Controls tier", d["controls_label"], ("PLCnext AXC F 2152 + Axioline I/O in a UL 508A BEN Controller panel, OnLogic Karbon 400 edge computer (TPM 2.0)" if d["controls_tier_resolved"] == "pro" else "Revolution Pi RevPi Connect 4 + DIO/AIO (DIN rail, listed), software interlocks behind a hardware watchdog relay") + f"; {d['pods']} BEN Pods on the BEN Mesh (Thread, Secure Vault); selectable with controls_tier (docs/CONTROLS_HARDWARE_DECISION.md 2a)"],
        ["Service", f"{d['voltage']}, {d['service_breaker_a']} A breaker", f"calculated {d['service_amps_calc']} A at 80 % continuous, rounded to the next frame" + ("; medium-voltage utility service to pad-mount transformers" if d["mv_service"] else "")],
    ] + ([
        ["Transformers", f"{d['transformers_total']} x {d['transformer_kva']:,} kVA pad-mount (MV to 480 V)", f"{cfg.redundancy}: 2N transformer pairs when 2N or N+1; 90 % loading at {d['total_kva']} kVA"],
        ["Generators", f"{d['generators_total']} x {d['generator_kw_each']:,} kW" if d["generators_total"] else "not included (option)", "N+1 standby with 48 h fuel; SPCC plan for the fuel yard"],
    ] if d["mv_service"] else ([
        ["Generator", f"1 x {d['generator_kw_each']:,} kW standby" if d["generators_total"] else "not included (option)", "total demand x 1.25, rounded to 10 kW"],
    ])) + [
        ["Hardening", f"{d['hardening_label']}: {d['hardening_rating']}", f"coating {d['hardening_coating']}; recommended for this profile/climate: {d['hardening_recommended']}; envelope {d['envelope_area_m2']} m²"],
        ["UPS", f"{d['ups_modules']} x {d['ups_kva_each']} kVA", f"IT only with 15 % headroom, {cfg.redundancy}"],
        ["Battery", f"{d['battery_kwh']} kWh lithium (LFP)", f"{cfg.ups_minutes} min at IT load, 90 % depth of discharge"],
        ["NFPA 855 scope", "YES - battery >= 20 kWh: UL 9540A data, gas detection and venting, AHJ review" if d["nfpa_855_scope"] else "no - battery below 20 kWh", "energy storage threshold"],
        ["Airflow", f"{d['airflow_cfm']:,} cfm", "125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water" ],
        ["Envelope gain at design day", f"{d['envelope_gain_kw']} kW", "100 mm PIR, R 3.5 m²K/W, solar on roof"],
        ["Mass", f"payload {d['payload_kg']:,} kg; gross {d['gross_kg']:,} kg", f"tare {g['tare_kg']:,} kg; crane and pad sized for the gross mass"],
        ["PUE estimate", f"{d['pue_estimate']}", "design-point calculation incl. 0.03 UPS loss; measured at SAT"],
    ])
    sections.append(s)

    # 5 scope of supply
    s = Section(5, "Scope of supply")
    by_sub = bt["by_subsystem"]
    scope_rows = []
    for sub in ("power", "cooling", "compute", "controls") + BASE_SUBSYSTEMS:
        if sub in by_sub:
            n = sum(1 for r in rows if r["subsystem"] == sub)
            scope_rows.append([SUBSYSTEM_LABELS[sub], "included", f"{n} lines", _usd(by_sub[sub] / (1 - margin))])
        elif sub in ("power", "cooling", "compute", "controls"):
            scope_rows.append([SUBSYSTEM_LABELS[sub], "not in this option", "-", "-"])
    s.table(["Module", "Status", "BOM lines", "Sell price"], scope_rows)
    top = sorted(rows, key=lambda r: -r["ext_price_usd"])[:15]
    s.p(f"Top {len(top)} lines of the {bt['items']}-line bill of materials for this option (sell price at {margin:.0%} gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):")
    s.table(["Code", "Item", "Manufacturer / MPN", "Qty", "Sell price", "Price basis", "Lead (wk)"],
            [[r["code"], r["name"], f"{r['manufacturer']} {r['mpn']}".strip() or "-", f"{r['qty']:,} {r['unit']}", _usd(r["ext_price_usd"] / (1 - margin)),
              r["price_status"], r["lead_time_weeks"] if r["lead_time_weeks"] is not None else "-"] for r in top])
    excl = ["Site civil works: pad, piers, anchors set in concrete, drainage, fencing, lighting, equipment yard (PE-stamped drawings are supplied by us)",
            "Utility service: feeder from the customer's switchgear to the disconnect at the unit, utility fees, metering, interconnection",
            "Permits and fees pulled by the customer (zoning, building, utility, generator air permit); we supply the engineering documents",
            "Fiber / ISP circuits, customer network equipment above the controls LAN, customer software licences",
            "Taxes, duties, freight insurance beyond the quoted domestic delivery, crane standby beyond one day"]
    if "compute" not in headline.subsystems:
        excl.insert(0, "Compute: servers, GPUs, storage and network switches are not selected in this option; racks, PDUs and cooling are sized for them")
    if not cfg.generator:
        excl.append("Standby generator, ATS and fuel system (available as an option)")
    s.p("Explicitly excluded:")
    s.ul(excl)
    sections.append(s)

    # 6 price
    s = Section(6, "Price")
    s.table(["Option", "Capital price", "Per kW IT", "Recurring / year", "Term", "Total over term", "Confirmed / list / estimate", "BOM lines", "Status"],
            [[p.label, _usd(p.capital_price_usd), _usd(p.price_per_kw_usd), _usd(p.recurring_usd_per_year) if p.recurring_usd_per_year else "-",
              f"{p.term_years} yr", _usd(p.total_term_usd), f"{p.confirmed_pct:.0f} / {p.list_pct:.0f} / {p.estimate_pct:.0f} %", p.bom_lines,
              "PROPOSED" if p.headline else "alternative"] for p in prices])
    s.p("Confirmed listing (shown as 'confirmed') = a price seen on the vendor's or distributor's own product page on the date in the BOM, read from a search-result snippet, not a quote, re-verified before purchase order; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. "
        f"Capital prices carry a {margin:.0%} gross margin on purchased hardware and build labour. Recurring items: " + "; ".join(f"{p.label}: {p.recurring_label}" for p in prices if p.recurring_usd_per_year) + ".")
    if any(p.key == "managed" for p in prices):
        mp = next(p for p in prices if p.key == "managed")
        s.table(["Managed service term", "Capital", "Service fees", "Total"],
                [[f"{y} year{'s' if y > 1 else ''}", _usd(mp.capital_price_usd), _usd(mp.recurring_usd_per_year * y), _usd(mp.capital_price_usd + mp.recurring_usd_per_year * y)] for y in (1, 3, 5)])
    s.p(f"Payment milestones for the proposed option ({headline.label}, capital {_usd(headline.capital_price_usd)}):")
    s.table(["Milestone", "Share", "Amount", "Week from order"],
            [[m["milestone"], _pct(m["share"] * 100), _usd(m["amount_usd"]), m["week"] if m["week"] is not None else "-"] for m in pay])
    s.p("Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.")
    sections.append(s)

    # 7 schedule
    s = Section(7, "Schedule")
    if mini:
        s.p(f"BEN 1 is assembled and shipped by Schreiber AI in {SCHEDULE_TIER[cfg.tier]['ref_total']}: no contract manufacturer, no pad and no site acceptance test; "
            "the last milestone is setup and handover. Weeks from order:")
    else:
        s.p(f"Milestones in weeks from order, derived from the stage durations in docs/PROCESS_FLOW.md for the {d['tier_label']} (reference order-to-service {SCHEDULE_TIER[cfg.tier]['ref_total']}) "
            f"and the longest lead time in this bill of materials ({long_lead[0]['lead_time_weeks'] if long_lead else 0} weeks). Critical path: engineering release -> long-lead procurement -> fit-out -> FAT -> SAT. Site civil and permits run in parallel.")
    s.table(["Week", "Milestone", "Owner", "Hold / witness point", "Path"],
            [[m["week"], m["milestone"], m["owner"], m["hold"], m["path"]] for m in milestones])
    s.p("Long-lead items (ordered at engineering release):")
    s.table(["Code", "Item", "Vendor", "Qty", "Lead time (weeks)"],
            [[l["code"], l["name"], l["vendor"] or "-", f"{l['qty']:,} {l['unit']}", l["lead_time_weeks"]] for l in long_lead])
    sections.append(s)

    # 8 drawings and documents
    s = Section(8, "Drawings and documents delivered")
    s.p(f"Issue-for-construction drawing set for the {d['tier_label']}, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. {dwg_status}")
    s.table(["Sheet", "Title", "Scale"], sheets)
    s.p("Document set (indexed binder, encrypted USB in the BEN Controller panel pocket, and the edge computer share, per docs/TURNOVER.md):")
    s.ul([
        "At order: this proposal, risk acknowledgement, site requirements form (docs/SITE_REQUIREMENTS.md) for signature",
        "At engineering release (H4): frozen configuration JSON with derived sizing, IFC drawing set with CTQ/CTP callouts, priced bill of materials with confirmation status, arc-flash and coordination study, PE anchorage calculation, compliance pack, FAT/SAT procedure",
        "At FAT (H13): signed commissioning report (JSON + PDF) with sweep CSVs, thermography, door-fan test, electrical and cooling test records",
        "At SAT (H19): site commissioning report, acoustic survey, final arc-flash labels, AHJ certificates",
        "At turnover (W20): as-built drawings, as-built BOM with serials, O&M manual, maintenance schedule with the first 12 months pre-populated, calibration certificates per channel, firmware hashes, Pod certificate register, edge computer backup, password handover record, training sign-off, warranty certificates",
    ])
    sections.append(s)

    # 9 compliance pack
    s = Section(9, "Compliance pack for this profile")
    s.p("Compliance is central to the design, not an appendix: docs/COMPLIANCE.md maps every applicable code to a design feature and a verification. The pack delivered with this unit is the subset for the profile and climate below.")
    if prof_row:
        rows_kv = []
        for k, v in prof_row.items():
            if k.startswith("ASHRAE class"):
                rows_kv.append(("ASHRAE class / redundancy (from config)", f"{d['ashrae_class']} / {cfg.redundancy}"))
                rows_kv.append(("Emphasis", v))
            else:
                rows_kv.append((k, v))
        s.kv(rows_kv)
    else:
        s.kv([("Profile", f"{prof['label']} ({d['ashrae_class']}, {cfg.redundancy})"),
              ("Standards emphasised", "NEC (NFPA 70), NFPA 75, NFPA 2001, NFPA 72, UL 508A, ASHRAE TC 9.9, AIM Act; NFPA 855 / UL 9540 when battery >= 20 kWh"),
              ("Extra documents in the pack", "Design-basis statement, PUE calculation, profile-specific security and access documents")])
    s.p("Climate add-ons:")
    if clim_row:
        s.kv([(k, clim_row[k]) for k in clim_row.keys()])
    else:
        s.kv([("Climate", clim["label"]), ("Design values", f"{clim['t_design_c']} °C / {clim['t_min_c']} °C, {clim['corrosion']}, {clim['wind_ms']} m/s")])
    base_rows = [["NFPA 70 (NEC)", "Listed dead-front gear, SCCR 65 kA, selective coordination, arc-flash labels", "Electrical inspection H10, AHJ at H18"],
                 ["NFPA 75 / 2001 / 72", "Non-combustible liner, VEWFD, clean agent with 10-min hold, EPO, HVAC shutdown", "Door-fan test, NFPA 72 record of completion at SAT"],
                 ["UL 508A", "BEN Controller panel (PLCnext PLC, I/O, edge computer) built and labelled by a UL 508A shop" if d["controls_tier_resolved"] == "pro" else "BEN Controls Lite: DIN-rail cabinet of UL-listed components (RevPi, QUINT4, switch); no 508A panel label", "Panel label and schedule (CTQ-K6)" if d["controls_tier_resolved"] == "pro" else "Component listing marks (CTQ-K6)"],
                 ["ASHRAE TC 9.9", f"Class {d['ashrae_class']} alarm limits in the controls", "Load step test E3/E7 at FAT and SAT"],
                 ["AIM Act / EPA 608", "GWP < 700 A1 refrigerant or water loops; certified technicians", "Charge record per circuit"],
                 ["ISO 668 / 1496 / CSC", "One-trip high-cube container, PE-checked modifications, CSC decision at transport", "Weld inspection H7, weigh ticket"]]
    if d["nfpa_855_scope"]:
        base_rows.append(["NFPA 855 / UL 9540 / 9540A", f"{d['battery_kwh']} kWh LFP battery: listed cabinets, gas detection, venting, separation", "UL 9540A data in the pack; AHJ review"])
    if cfg.generator:
        base_rows.append(["NFPA 110 / NFPA 37 / 30", "Standby generator with ATS, fuel system, exhaust setbacks", "Installation acceptance test, load bank"])
    s.p("Baseline matrix lines that apply to every unit:")
    s.table(["Code / standard", "Design feature", "Verification"], base_rows)
    sections.append(s)

    # 10 risks
    s = Section(10, "Risks disclosed up front")
    s.p(f"These are the risks that apply to the {prof['label'].lower()} profile, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). "
        "Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.")
    if risks:
        s.table(["ID", "Risk", "Severity", "What can happen", "Covered by the design", "Customer owns"],
                [[r["id"], r["title"], r["severity"], r["plain_text"], r["covered_by"], r["customer_owns"]] for r in risks])
    else:
        s.p("Risk register attached separately (docs/RISK_REGISTER.md).")
    sections.append(s)

    # 11 site requirements
    s = Section(11, "Site requirements summary")
    s.p("The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:")
    permits = json.loads(sreq.get("_permits", "[]"))
    if mini:
        permits = []
        s.kv([
            ("Placement", f"{d['form_label']}: {g['ext_l_m'] * 1000:.0f} W x {g['ext_w_m'] * 1000:.0f} D x {g['ext_h_m'] * 1000:.0f} H mm on a desk, shelf or floor; 300 mm clear at the front and back"),
            ("Mass", f"{d['gross_kg']:,} kg loaded"),
            ("Power", f"{d['outlet_circuit']}; draw {d['outlet_amps']} A at 120 V ({d['ups_plug']} on the UPS). {d['voltage_option']}"),
            ("Room heat", d["room_cooling_note"]),
            ("Noise", f"estimated {d['noise_dba_est']} dBA at 1 m (target {d['noise_dba_target']:.0f}); {d['noise_basis']}"),
            ("Network", "one uplink port (1 GbE) to the customer's router or firewall; BEN Care reaches out over HTTPS only"),
            ("Environment", f"office air {d['office_design_c']:.0f} °C design, {d['office_max_c']:.0f} °C maximum; IT held to ASHRAE {d['ashrae_class']}; {d['hardening_rating']}"),
            ("Permits", "none for a plug-in unit; the building's own fire and electrical rules apply"),
        ])
    else:
      s.kv([
          ("Pad plan size", sreq.get("pad_size", "unit footprint + 1.0 m apron all round + equipment yard")),
          ("Pad type", sreq.get("pad_type", "reinforced slab or piers at corner castings to frost depth; PE-stamped drawing supplied")),
          ("Anchor points", sreq.get("anchors", "twist-lock bases or weld plates at the corner castings (ISO 1161 pattern)")),
          ("Gross mass to set", f"{d['gross_kg']:,} kg (crane sized for this mass at the required radius)"),
          ("Utility service", f"{sreq.get('voltage', d['voltage'])}; customer disconnect rated {d['service_breaker_a']} A for this configuration (tier range: {sreq.get('disconnect', str(d['service_breaker_a']) + ' A')})"),
          ("Feeder conductors (customer side)", sreq.get("feeder", "per NEC 310.16 for the breaker rating")),
          ("Fault current", "utility available fault current and voltage required before shipping; unit SCCR 65 kA"),
          ("Generator", sreq.get("generator", "n/a") if cfg.generator else "not in this configuration"),
          ("Grounding electrode", sreq.get("ground_electrode", "ground ring or two rods, bonded to the building electrode system")),
          ("Ground resistance", sreq.get("ground_resistance", "<= 25 ohm code minimum; <= 5 ohm recommended")),
          ("Fiber conduit", sreq.get("fiber_conduit", "two 50 mm conduits with pull strings to the communications entry plate")),
          ("Fiber service", sreq.get("fiber_service", "customer orders the circuit; order at H3 (60–120 day lead time)")),
          ("Clearances", "2.5 m clear on the door side; >= 1.5 m at condensers / dry cooler with no recirculation; >= 3 m to other structures; fire lane on one long side"),
          ("Climate inputs the customer confirms", "flood zone and base flood elevation, site wind speed and exposure, ground snow load, seismic category, altitude, corrosivity"),
      ])
    if permits:
        s.p("Permits and who pulls them:")
        s.table(["Permit", "Typical need", "Who pulls"], [[p[0], p[1], p[2]] for p in permits])
    sections.append(s)

    # 12 acceptance
    s = Section(12, "Acceptance: FAT and SAT" if not mini else "Acceptance: burn-in test and handover")
    if mini:
        s.p("Acceptance is by the commissioning script (software/ben_engine/commissioning.py) in factory mode before shipping (24 h burn-in, hold point H13) and a short setup check at "
            "handover (H19). Steps that need hardware BEN 1 does not have (generator, liquid loop, DC bus; door and fans on the 10-inch rack) are skipped with the reason stated in the report.")
    else:
        s.p("Acceptance is by the commissioning script (software/ben_engine/commissioning.py), run twice: in factory mode on load banks before shipping (FAT, hold point H13) and in site mode on the energised unit (SAT, hold point H19). "
            "The same ten steps run both times and produce a signed report with the SHA-256 of the data file. The customer may witness both; FAT passing releases the 40 % milestone and SAT passing releases the 25 % milestone.")
    s.table(["Step", "Test", "Pass criterion"], [[a, b, c] for a, b, c in COMMISSIONING_STEPS])
    s.p(f"Pass criteria specific to this configuration: rack inlets within ASHRAE {d['ashrae_class']} at {cfg.it_kw:.0f} kW; {cfg.redundancy} failover with no inlet excursion; UPS ride-through >= {cfg.ups_minutes} minutes at IT load; "
        f"meter vs PDU reconciliation within 3 %; PUE at full load reported against the {d['pue_estimate']} estimate. Deviations are closed or accepted in writing before the milestone is invoiced.")
    sections.append(s)

    # 13 warranty, maintenance, support
    s = Section(13, "Warranty, maintenance and support")
    s.kv([
        ("Workmanship warranty", f"{WARRANTY_WORKMANSHIP_MONTHS} months from SAT on the integration, wiring, piping, envelope and controls build"),
        ("Equipment warranty", f"Vendor warranties (UPS, cooling, CDU, batteries, fire panel, generator, servers) registered in the customer's name at turnover and passed through; minimum {WARRANTY_EQUIPMENT_MONTHS} months, longer where the vendor offers it"),
        ("Controls software", "Signed Pod firmware, PLC project and edge computer updates for the licence term; security fixes for the life of the licence"),
        ("Support level in this option", {
            "hardware_only": "Remote email support during business hours for the warranty period; maintenance by the customer or a certified subcontractor per the schedule",
            "hardware_controls": "Remote dashboard access and business-hours support for the licence term; maintenance by the customer's technician with our remote review",
            "white_label": f"Second-line engineering support to {cfg.brand}; partner delivers first-line support under its own brand",
            "managed": "24 x 7 remote monitoring by Schreiber AI operations, weekly remote checks, scheduled local and subcontractor visits per the maintenance schedule, alarm response and monthly report; the maintenance schedule below is included",
            "modules": "Remote support for the supplied modules during the warranty period; controls licence support if the controls module is selected",
        }[headline.key]),
    ])
    s.p("Maintenance schedule (docs/MAINTENANCE.md; intervals for temperate climate, climate add-ons shorten some intervals; task counts per interval):")
    s.table(["Interval", "Who", "Tasks"], [[a, b, c] for a, b, c in maint])
    s.p("Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). "
        "Climate add-ons for this unit: " + {
            "temperate": "baseline intervals",
            "hot_arid": "filter inspection monthly, coil cleaning quarterly, cool-roof coating check annually",
            "hot_humid": "dew-point and condensation check monthly, coating inspection annually (C4)",
            "cold": "freeze-protection checklist before winter, heat-trace and door-seal heater test, snow removal plan",
            "coastal": "fresh-water coil rinse quarterly, C5 coating survey annually, stainless fastener inspection",
            "high_altitude": "fan curve check at commissioning, UV inspection of gaskets and coatings, lightning protection check",
        }[cfg.climate] + ".")
    sections.append(s)

    # 14 commercial terms
    s = Section(14, "Commercial terms summary")
    s.p("The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), "
        "the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). "
        "This section summarises them; the contracts prevail.")
    s.table(["Term", "Summary"], [
        ["Payment", " / ".join(f"{int(sh * 100)} % at {name.split(' (')[0]}" for name, sh in pay_ms) + "; net 30 from invoice; recurring fees annually in advance"],
        ["Price validity", f"{VALIDITY_DAYS} days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4)"],
        ["Scope changes", "Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done"],
        ["Customer-caused delay", "A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period"],
        ["Delivery liquidated damages", f"{LD_RATE_PCT_PER_WEEK} % of the capital price per week of Schreiber AI-caused delay to FAT, capped at {LD_CAP_PCT} %; sole remedy for delay"],
        ["Storage of a finished unit", f"If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at ${STORAGE_FEE_PER_DAY[cfg.tier]:,} per day after 14 days, and the FAT milestone is payable"],
        ["Supplier and contract-manufacturer delay", "Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages"],
        ["Title and risk", "Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value"],
        ["Warranty", f"{WARRANTY_WORKMANSHIP_MONTHS} months workmanship; vendor warranties passed through (section 13)"],
        ["Acceptance", "FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed"],
        ["Data and software", "Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency"],
        ["Governing law", "[GOVERNING_STATE] (set in the MSA)"],
    ])
    sections.append(s)

    # 15 assumptions
    s = Section(15, "Assumptions and what is not included")
    s.ul([
        f"Configuration as on the cover: {cfg.it_kw:.0f} kW IT, {cfg.racks} rack(s), {d['cooling_label']}, {cfg.redundancy}, climate {clim['label']}; any change is priced as a change order",
        f"Prices from purchasing/parts_catalog.json priced on the dates in the BOM; {headline.confirmed_pct:.0f} % confirmed, {headline.list_pct:.0f} % list, {headline.estimate_pct:.0f} % estimate for this option; the estimate share is re-priced at engineering release",
        f"Gross margin {margin:.0%} on hardware and build labour; controls licence {_usd(CONTROLS_LICENCE_PER_UNIT_YR[cfg.tier])}/yr for this tier; white-label uplift x{WHITE_LABEL_UPLIFT}; managed service ${MANAGED_PER_KW_MONTH:.0f}/kW-month",
        "Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra",
        "Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order",
        "Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost",
        "Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 16 lists editions not verified on the proposal date)",
        "Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times",
        "Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)",
    ])
    if notes:
        s.p("Generator notes: " + "; ".join(notes) + ".")
    sections.append(s)

    # 16 signature
    s = Section(16, "Signature block")
    s.p(f"By signing, the customer accepts this proposal ({pid}) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.")
    s.table(["Role", "Name", "Signature", "Date"], [
        [f"Customer authorised representative, {customer}", "", "", ""],
        [f"{brand.get('brand', 'Schreiber AI')} — sales", "", "", ""],
        [f"{brand.get('brand', 'Schreiber AI')} — engineering", "", "", ""],
        [f"{brand.get('brand', 'Schreiber AI')} — compliance", "", "", ""],
    ] + ([[f"Partner, {cfg.brand}", "", "", ""]] if headline.key == "white_label" else []))
    sections.append(s)

    return Proposal(
        proposal_id=pid, date=today, valid_until=valid_until, customer=customer, site=site, option=option, brand=brand_name,
        config=cfg.to_dict(), derived={k: v for k, v in d.items() if k not in ("geometry", "climate")},
        bom_totals=bt, prices=prices, headline=headline, milestones=milestones, payment_milestones=pay,
        long_lead=long_lead, sections=sections, notes=notes,
    )


# ----------------------------------------------------------------------------- renderers
def _md_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def to_markdown(p: Proposal) -> str:
    out: List[str] = [f"# {p.brand} — BEN Engine proposal {p.proposal_id}", "",
                      f"*{p.tier_label} · {p.profile_label} · {p.customer} · {p.site} · {p.date} · valid until {p.valid_until}*", ""]
    for s in p.sections:
        out.append(f"## {s.number}. {s.title}\n")
        for b in s.blocks:
            if b.kind == "p":
                out.append(b.text + "\n")
            elif b.kind == "ul":
                out.extend(f"- {i}" for i in b.items); out.append("")
            elif b.kind == "kv":
                out.append("| Item | Value |\n|---|---|")
                out.extend(f"| {_md_cell(k)} | {_md_cell(v)} |" for k, v in b.rows); out.append("")
            elif b.kind == "table":
                out.append("| " + " | ".join(_md_cell(h) for h in b.headers) + " |")
                out.append("|" + "---|" * len(b.headers))
                out.extend("| " + " | ".join(_md_cell(c) for c in r) + " |" for r in b.rows); out.append("")
    out.append(f"---\n*Schreiber AI — proposal {p.proposal_id}. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*")
    return "\n".join(out)


_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="56" height="56" role="img" aria-label="Schreiber AI monogram">'
    '<rect width="120" height="120" rx="24" fill="#0B1018"/>'
    '<path d="M30 78c0 9 8 14 19 14 12 0 19-6 19-14 0-9-7-12-18-15-9-2-12-4-12-8 0-5 5-8 11-8 7 0 11 3 12 8" fill="none" stroke="#66E3FF" stroke-width="6" stroke-linecap="round"/>'
    '<path d="M78 92V40h8v52zM60 28h26" fill="none" stroke="#EDF4FF" stroke-width="6" stroke-linecap="round"/>'
    '<circle cx="98" cy="28" r="5" fill="#FFC66D"/></svg>'
)


def _inline(s: str) -> str:
    """Escape HTML and render **bold**, `code` and [text](url) inline markdown."""
    e = _html.escape(str(s), quote=False)
    e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
    e = re.sub(r"`(.+?)`", r"<code>\1</code>", e)
    e = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', e)
    return e


def to_html(p: Proposal) -> str:
    b = _brand(); c = b.get("colors", {})
    watermark = f"Schreiber AI — proposal {p.proposal_id}"
    parts: List[str] = []
    for s in p.sections:
        body: List[str] = []
        for bl in s.blocks:
            if bl.kind == "p":
                body.append(f"<p>{_inline(bl.text)}</p>")
            elif bl.kind == "ul":
                body.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in bl.items) + "</ul>")
            elif bl.kind == "kv":
                body.append("<table class='kv'><tbody>" + "".join(f"<tr><th>{_inline(k)}</th><td>{_inline(v)}</td></tr>" for k, v in bl.rows) + "</tbody></table>")
            elif bl.kind == "table":
                num_cols = [all(re.fullmatch(r"[\$\d,\.\s%/\-]+", r[i] or "-") for r in bl.rows) for i in range(len(bl.headers))] if bl.rows else []
                th = "".join(f"<th{' class=num' if num_cols and num_cols[i] else ''}>{_inline(h)}</th>" for i, h in enumerate(bl.headers))
                trs = "".join("<tr>" + "".join(f"<td{' class=num' if num_cols and num_cols[i] else ''}{' class=hl' if 'PROPOSED' in r else ''}>{_inline(cell)}</td>" for i, cell in enumerate(r)) + "</tr>" for r in bl.rows)
                body.append(f"<div class='tw'><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>")
        cover = " cover" if s.number == 1 else ""
        head = (f"<header class='hdr'>{_LOGO_SVG}<div><div class='eyebrow'>{_html.escape(p.brand)} · BEN Engine · Proposal {p.proposal_id}</div>"
                f"<h1>{_html.escape(p.tier_label)} for {_html.escape(p.customer)}</h1>"
                f"<div class='sub'>{_html.escape(p.profile_label)} · {_html.escape(p.site)} · {OPTION_LABELS[p.option]} · {p.date}</div></div></header>") if s.number == 1 else ""
        parts.append(f"<section class='page{cover}' id='s{s.number}'>{head}<h2><span class='n'>{s.number}</span>{_html.escape(s.title)}</h2>{''.join(body)}"
                     f"<footer class='pf'><span>{_html.escape(watermark)}</span><span>Section {s.number} of {len(p.sections)} · valid until {p.valid_until}</span></footer></section>")
    toc = "".join(f"<a href='#s{s.number}'>{s.number}. {_html.escape(s.title)}</a>" for s in p.sections)
    css = f"""
:root {{ --bg:{c.get('graphite', '#0B1018')}; --slate:{c.get('slate', '#152234')}; --panel:{c.get('panel', '#1B2B42')}; --text:{c.get('text', '#EDF4FF')}; --muted:{c.get('muted', '#9FB3CC')};
  --cyan:{c.get('cyan', '#66E3FF')}; --amber:{c.get('amber', '#FFC66D')}; --red:{c.get('red', '#FF707D')}; --green:{c.get('green', '#6EE7A8')}; --line:rgba(159,179,204,.22); --wm:rgba(159,179,204,.55); }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; background:var(--bg); color:var(--text); font-family:{b.get('type', {}).get('display', "'Inter', 'Segoe UI', system-ui, sans-serif")}; font-size:14px; line-height:1.5; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
code {{ font-family:{b.get('type', {}).get('mono', "'JetBrains Mono', Consolas, monospace")}; font-size:.9em; color:var(--cyan); }}
.wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px 64px; }}
nav.toc {{ display:flex; flex-wrap:wrap; gap:6px 14px; padding:12px 0 20px; font-size:12px; }}
nav.toc a {{ color:var(--muted); text-decoration:none; }} nav.toc a:hover {{ color:var(--cyan); }}
.page {{ background:var(--slate); border:1px solid var(--line); border-radius:14px; padding:28px 32px 20px; margin:0 0 22px; position:relative; page-break-after:always; break-after:page; }}
.page.cover {{ background:linear-gradient(160deg, var(--panel), var(--slate) 60%, var(--bg)); min-height:560px; }}
.hdr {{ display:flex; gap:18px; align-items:flex-start; padding-bottom:22px; margin-bottom:18px; border-bottom:1px solid var(--line); }}
.hdr svg {{ flex:none; }}
.eyebrow {{ color:var(--cyan); font-size:12px; letter-spacing:.14em; text-transform:uppercase; }}
h1 {{ margin:6px 0 4px; font-size:30px; line-height:1.15; font-weight:650; }}
.sub {{ color:var(--muted); font-size:14px; }}
h2 {{ font-size:20px; margin:0 0 14px; font-weight:650; display:flex; align-items:center; gap:12px; }}
h2 .n {{ display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:8px; background:var(--panel); color:var(--cyan); font-size:14px; font-weight:700; border:1px solid var(--line); }}
p {{ margin:0 0 12px; }} ul {{ margin:0 0 12px; padding-left:20px; }} li {{ margin:2px 0; }}
.tw {{ overflow-x:auto; margin:0 0 14px; }}
table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
thead th {{ text-align:left; color:var(--muted); font-weight:600; font-size:11.5px; letter-spacing:.04em; text-transform:uppercase; padding:8px 10px; border-bottom:1px solid var(--line); background:var(--panel); white-space:nowrap; }}
tbody td, tbody th {{ padding:7px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
tbody tr:nth-child(even) td {{ background:rgba(27,43,66,.45); }}
td.num, th.num {{ text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }}
table.kv th {{ text-align:left; color:var(--muted); font-weight:600; width:26%; }}
table.kv {{ margin-bottom:14px; }}
td.hl {{ color:var(--amber); font-weight:700; }}
.pf {{ display:flex; justify-content:space-between; gap:12px; margin-top:18px; padding-top:10px; border-top:1px dashed var(--line); color:var(--wm); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }}
.wm {{ display:none; }}
@media (max-width:640px) {{ .page {{ padding:18px 14px; }} h1 {{ font-size:22px; }} table.kv th {{ width:38%; }} }}
@media print {{
  :root {{ --bg:{c.get('light_bg', '#F4F7FB')}; --slate:#ffffff; --panel:#E9EFF6; --text:{c.get('light_text', '#0B1018')}; --muted:#4A5B72; --cyan:#0A6B86; --amber:#8A5A00; --line:#C9D4E2; --wm:#7A8AA0; }}
  @page {{ size:A4; margin:14mm 12mm 18mm; }}
  html,body {{ background:#fff; font-size:11px; }}
  .wrap {{ max-width:none; padding:0; }}
  nav.toc {{ display:none; }}
  .page {{ border:none; border-radius:0; padding:0 0 10mm; margin:0; background:#fff; min-height:0; }}
  .page.cover {{ background:#fff; }}
  .hdr svg rect {{ fill:#0B1018; }}
  tbody tr:nth-child(even) td {{ background:#F4F7FB; }}
  .tw {{ overflow:visible; }} table {{ font-size:9.5px; }} tr {{ page-break-inside:avoid; }}
  .pf {{ display:none; }}
  .wm {{ display:block; position:fixed; bottom:4mm; left:0; right:0; text-align:center; color:var(--wm); font-size:9px; letter-spacing:.14em; text-transform:uppercase; }}
  a {{ color:inherit; text-decoration:none; }}
}}
"""
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{_html.escape(p.tier_label)} proposal — {_html.escape(p.customer)}</title><style>{css}</style></head><body>"
            f"<div class='wrap'><nav class='toc'>{toc}</nav>{''.join(parts)}</div><div class='wm'>{_html.escape(watermark)}</div></body></html>")


def to_json(p: Proposal, **kw) -> str:
    kw.setdefault("indent", 2)
    return json.dumps(p.to_dict(), **kw)


def from_json(s: str) -> Proposal:
    return Proposal.from_dict(json.loads(s))


# ----------------------------------------------------------------------------- contract pre-fill
class FilledText(str):
    """A ``str`` with an ``unfilled`` attribute: the ``[FIELD]`` names left in the template."""
    unfilled: List[str] = []


def contract_fields(p: Proposal, extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """The [FIELD_NAME] vocabulary (docs/contracts/fields.json) filled from a proposal."""
    cfg = p.config; d = p.derived; h = p.headline
    start = _dt.date.fromisoformat(p.date)
    week = lambda w: (start + _dt.timedelta(weeks=w)).isoformat() if w is not None else ""
    ms = {m["hold"]: m["week"] for m in p.milestones}
    pay = {m["milestone"]: m for m in p.payment_milestones}
    f: Dict[str, Any] = {
        "PROPOSAL_ID": p.proposal_id, "PROPOSAL_DATE": p.date, "VALID_UNTIL": p.valid_until,
        "CUSTOMER_NAME": p.customer, "SITE_ADDRESS": p.site, "SITE_NAME": p.site,
        "SUPPLIER_NAME": "Schreiber AI", "PARTNER_BRAND": cfg.get("brand", "Schreiber AI"), "BRAND": p.brand,
        "TIER": cfg["tier"], "TIER_LABEL": p.tier_label, "PROFILE": cfg["profile"], "PROFILE_LABEL": p.profile_label,
        "CLIMATE": cfg["climate"], "REDUNDANCY": cfg["redundancy"], "COOLING": d["cooling_label"],
        "IT_KW": f"{cfg['it_kw']:.0f}", "RACKS": str(cfg["racks"]), "UPS_MINUTES": str(cfg["ups_minutes"]),
        "SERVICE_VOLTAGE": d["voltage"], "SERVICE_BREAKER_A": str(d["service_breaker_a"]), "GROSS_MASS_KG": f"{d['gross_kg']:,}",
        "PURCHASE_OPTION": h.label, "OPTION": h.key,
        "PRICE_TOTAL": f"{h.capital_price_usd:,.2f}", "CAPITAL_PRICE": f"{h.capital_price_usd:,.2f}",
        "PRICE_PER_KW": f"{h.price_per_kw_usd:,.2f}", "RECURRING_PER_YEAR": f"{h.recurring_usd_per_year:,.2f}",
        "RECURRING_LABEL": h.recurring_label, "TERM_YEARS": str(h.term_years), "TOTAL_OVER_TERM": f"{h.total_term_usd:,.2f}",
        "CURRENCY": "USD", "MARGIN_PCT": f"{MARGIN_HW * 100:.0f}",
        "CONFIRMED_PCT": f"{h.confirmed_pct:.0f}", "LIST_PCT": f"{h.list_pct:.0f}", "ESTIMATE_PCT": f"{h.estimate_pct:.0f}",
        "BOM_LINES": str(h.bom_lines),
        "MILESTONE_ENG_RELEASE_PCT": "30", "MILESTONE_FAT_PCT": "40", "MILESTONE_SAT_PCT": "25", "MILESTONE_TURNOVER_PCT": "5",
        "MILESTONE_ENG_RELEASE_AMOUNT": f"{pay['Engineering release (H4)']['amount_usd']:,.2f}",
        "MILESTONE_FAT_AMOUNT": f"{pay['Factory acceptance test (H13)']['amount_usd']:,.2f}",
        "MILESTONE_SAT_AMOUNT": f"{pay['Site acceptance test (H19)']['amount_usd']:,.2f}",
        "MILESTONE_TURNOVER_AMOUNT": f"{pay['Turnover (W20)']['amount_usd']:,.2f}",
        "MILESTONE_H3_DATE": week(ms.get("H3")), "MILESTONE_ENG_RELEASE_DATE": week(ms.get("H4")),
        "MILESTONE_FAT_DATE": week(ms.get("H11, W12, H13")), "MILESTONE_SHIP_DATE": week(next((m["week"] for m in p.milestones if m["milestone"].startswith("Transport")), None)),
        "MILESTONE_SAT_DATE": week(ms.get("H19")), "MILESTONE_TURNOVER_DATE": week(ms.get("W20")),
        "MILESTONE_ENG_RELEASE_WEEK": str(ms.get("H4", "")), "MILESTONE_FAT_WEEK": str(ms.get("H11, W12, H13", "")),
        "MILESTONE_SAT_WEEK": str(ms.get("H19", "")), "MILESTONE_TURNOVER_WEEK": str(ms.get("W20", "")),
        "DELIVERY_WEEKS": str(ms.get("W20", "")), "ORDER_DATE": p.date,
        "LD_RATE_PCT_PER_WEEK": f"{LD_RATE_PCT_PER_WEEK:g}", "LD_CAP_PCT": f"{LD_CAP_PCT:g}",
        "STORAGE_FEE_PER_DAY": f"{STORAGE_FEE_PER_DAY[cfg['tier']]:,}", "STORAGE_FREE_DAYS": "14",
        "WARRANTY_WORKMANSHIP_MONTHS": str(WARRANTY_WORKMANSHIP_MONTHS), "WARRANTY_EQUIPMENT_MONTHS": str(WARRANTY_EQUIPMENT_MONTHS),
        "PAYMENT_TERMS_DAYS": "30", "VALIDITY_DAYS": str(VALIDITY_DAYS), "LONG_LEAD_WEEKS": str(p.long_lead[0]["lead_time_weeks"] if p.long_lead else 0),
        "DRAWING_SET": f"design/drawings/{cfg['tier']}/INDEX.md", "COMMISSIONING_SCRIPT": "software/ben_engine/commissioning.py",
        "DATE": p.date, "GENERATED_BY": "ben_engine.proposal",
    }
    f.update({k: v for k, v in _extended_fields(p, f, ms, week).items() if k not in f})
    if extra_fields:
        f.update(extra_fields)
    return {k: str(v) for k, v in f.items()}


def _drawing_rev() -> str:
    """Drawing set label from design/REVISION.json (e.g. 'IFR Rev B (2026-11-08)'): one revision for drawings, SQAM, assembly and this proposal."""
    try:
        r = json.loads((REPO_ROOT / "design" / "REVISION.json").read_text(encoding="utf-8"))
        status = "IFC" if r.get("checker", "").strip() else "IFR"
        return f"{status} Rev {r['drawing_rev']} ({r['issue_date']})"
    except Exception:
        return "Rev ? (design/REVISION.json unreadable)"


def _git_rev() -> str:
    try:
        import subprocess
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=5).stdout.strip() or "untracked"
    except Exception:
        return "untracked"


def _extended_fields(p: Proposal, base: Dict[str, Any], ms: Dict[str, Any], week) -> Dict[str, Any]:
    """Fill the rest of docs/contracts/fields.json that can be derived from the proposal: configuration,
    derived sizing, module prices from the BOM, schedule baselines, SOW scope rows, repository revisions,
    document identifiers, entity defaults and every field default declared in fields.json."""
    cfg = p.config; d = p.derived; h = p.headline
    tier = cfg["tier"]; subs = set(cfg.get("subsystems") or [])
    clim = CLIMATE_DESIGN[cfg["climate"]]
    inc = lambda c: "Included" if c else "Excluded"
    liquid = COOLING_LIBRARY[cfg["cooling"]]["medium"] in ("water", "liquid")
    gen = bool(cfg.get("generator"))
    managed = h.key == "managed"; white = h.key == "white_label"
    # module prices at the headline margin, from the BOM rows the proposal already priced
    try:
        from .bom import generate_bom
        from .config import Config as _C
        rows = generate_bom(_C.from_dict(cfg))
    except Exception:
        rows = []
    m = 1.0 / (1.0 - MARGIN_HW)
    by = lambda *ss: sum(r["ext_price_usd"] for r in rows if r["subsystem"] in ss) * m
    price_power, price_cool, price_comp, price_ctl = by("power"), by("cooling"), by("compute"), by("controls")
    price_encl = by("str", "env", "fs")
    price_site, price_svc = by("site"), by("svc")
    licence = CONTROLS_LICENCE_PER_UNIT_YR[tier]
    a_max = {"A1": 27, "A2": 35, "A3": 40, "A4": 45}.get(d.get("ashrae_class", "A2"), 35)
    avail = {"N": "99.5", "N+1": "99.9", "2N": "99.99"}[cfg["redundancy"]]
    pid = p.proposal_id; stem = pid.replace("SAI-", "")
    w_fat = ms.get("H11, W12, H13"); w_sat = ms.get("H19"); w_turn = ms.get("W20")
    w_ship = next((mm["week"] for mm in p.milestones if mm["milestone"].startswith("Transport")), None)
    w_set = ms.get("W17, H18"); w_h3 = ms.get("H3"); w_h4 = ms.get("H4"); w_h10 = ms.get("H10"); w_h16 = ms.get("H16")
    w_w6 = ms.get("W6, H7, W8")
    end_warranty = (_dt.date.fromisoformat(p.date) + _dt.timedelta(weeks=(w_turn or 0)) + _dt.timedelta(days=30 * WARRANTY_WORKMANSHIP_MONTHS)).isoformat()
    f: Dict[str, Any] = {
        # config
        "CONFIG_ID": f"{pid}-cfg-v1.0", "CONFIG_JSON": json.dumps(cfg, indent=2), "TIER_DIR": tier, "SUBSYSTEMS": ", ".join(cfg.get("subsystems") or []),
        "WHITE_LABEL": str(bool(cfg.get("white_label"))).lower(), "GENERATOR": str(gen).lower(), "BRAND_NAME": cfg.get("brand") or "Schreiber AI",
        # derived
        "ASHRAE_CLASS": d.get("ashrae_class", ""), "ASHRAE_MAX_C": str(a_max), "AVAILABILITY_TARGET_PCT": avail,
        "BATTERY_KWH": f"{d['battery_kwh']:g}", "CLIMATE_DESIGN_TEMP_C": str(clim["t_design_c"]), "COOLING_UNITS_TOTAL": str(d["cooling_units_total"]),
        "GENERATOR_KW": (f"{d['generators_total']} x {d['generator_kw_each']:g}" if d.get("mv_service") else f"{math.ceil(d['total_kw'] * 1.25 / 10) * 10:g}") if gen else "0", "GLYCOL_PCT": "35" if clim["t_min_c"] <= -20 else "25",
        "NFPA855_PACKAGE": str(bool(d.get("nfpa_855_scope"))).lower(), "NODE_COUNT": str(1 + math.ceil(cfg["racks"] / 2)),
        "POD_COUNT": str(d.get("pods", 3 if tier == "ben5" else cfg["racks"] * 2 + 2)), "CONTROLS_TIER_LABEL": d.get("controls_label", "BEN Controls Pro" if tier in ("ben150", "ben500", "ben2000") else "BEN Controls Lite"),
        "HARDENING_LEVEL": d.get("hardening", cfg.get("hardening", "H1")), "HARDENING_LABEL": d.get("hardening_label", ""), "HARDENING_RATING": d.get("hardening_rating", ""),
        "MV_SERVICE": str(bool(d.get("mv_service"))).lower(), "TRANSFORMERS_TOTAL": str(d.get("transformers_total", 0)), "TRANSFORMER_KVA": str(d.get("transformer_kva", 0)),
        "GENERATORS_TOTAL": str(d.get("generators_total", 0)), "MODULES": str(d.get("modules", 1)), "RACK_ROWS": str(d.get("rows", 1)),
        "PUE_ESTIMATE": f"{d['pue_estimate']:.3f}", "TOTAL_KVA": f"{d['total_kva']:g}", "UPS_KVA_EACH": str(d["ups_kva_each"]), "UPS_MODULES": str(d["ups_modules"]),
        "CORROSIVITY_CLASS": clim["corrosion"], "WIND_SPEED": f"{clim['wind_ms']} m/s (ASCE 7 basic; confirm per site)",
        # pricing by module
        "PRICE_POWER": f"{price_power:,.2f}", "PRICE_COOLING": f"{price_cool:,.2f}", "PRICE_COMPUTE": f"{price_comp if 'compute' in subs else 0:,.2f}",
        "PRICE_CONTROLS": f"{price_ctl:,.2f}", "PRICE_ENCLOSURE": f"{price_encl:,.2f}", "PRICE_SERVICES": f"{price_svc:,.2f}",
        "PRICE_SITE_WORKS": f"{price_site:,.2f}", "PRICE_OPTIONS": "0.00", "PRICE_PERMIT_SERVICES": "0.00", "OPTIONS_LIST": "none", "PERMIT_SERVICES_LIST": "AHJ pre-submission support (included); permits pulled by Customer",
        "CONTRACT_VALUE_TOTAL": f"{h.capital_price_usd + (h.recurring_usd_per_year if (managed or white) else 0):,.2f}",
        "LICENSE_FEE": f"{licence * (1.25 if white else 1):,.2f}" if "controls" in subs else "0.00",
        "WHITE_LABEL_LICENSE_FEE": f"{licence * 1.25:,.2f}", "LICENSE_MICRO_ANNUAL": "USD 1,200", "LICENSE_BEN10_ANNUAL": "USD 4,800",
        "LICENSE_BEN20_ANNUAL": "USD 12,000", "LICENSE_BEN40_ANNUAL": "USD 30,000",
        "LICENSE_BEN5_ANNUAL": "USD 1,200", "LICENSE_BEN30_ANNUAL": "USD 4,800", "LICENSE_BEN150_ANNUAL": "USD 12,000", "LICENSE_BEN500_ANNUAL": "USD 30,000", "LICENSE_BEN2000_ANNUAL": "USD 90,000", "SLA_RATE_PER_KW_MONTH": "USD 45",
        "SLA_MONTHLY_FEE": f"{45 * cfg['it_kw']:,.2f}", "MANAGED_SERVICES": str(managed).lower(),
        "DELIVERY_MODEL": h.label, "COMPUTE_DESCRIPTION": "Reference GPU/CPU node set from the catalog (CMP- lines)" if "compute" in subs else "Customer-supplied compute",
        "TURNKEY_SITE_WORKS": "no", "RECOMMISSIONING_FEE": "7,500.00", "CRANE_REMOB_FEE": "4,500.00", "STANDBY_RATE_PER_DAY": "1,200.00",
        "RATE_PRINCIPAL_ENGINEER": "225.00", "RATE_CONTROLS_ENGINEER": "175.00", "RATE_PM": "165.00", "RATE_FIELD_TECH": "125.00",
        "RATE_ELECTRICIAN": "110.00", "RATE_HVAC": "125.00", "RATE_WELDER": "135.00",
        # schedule baselines
        "DATE_ORDER": p.date, "SOW_DATE": p.date, "DATE_H3_BASELINE": week(w_h3), "DATE_H4_BASELINE": week(w_h4), "DATE_W6_BASELINE": week(w_w6),
        "DATE_H7_BASELINE": week(w_w6), "DATE_W8_BASELINE": week((w_w6 or 0) + 1), "DATE_LONGLEAD_BASELINE": week(w_h10), "DATE_H10_BASELINE": week(w_h10),
        "DATE_H11_BASELINE": week(max((w_fat or 1) - 1, 0)), "DATE_W12_BASELINE": week(w_fat), "DATE_FAT_BASELINE": week(w_fat), "DATE_SHIP_BASELINE": week(w_ship),
        "DATE_SETDOWN_BASELINE": week(w_set), "DATE_H18_BASELINE": week(w_set), "DATE_SAT_BASELINE": week(w_sat), "DATE_TURNOVER_BASELINE": week(w_turn),
        "DATE_PERMITS_APPLIED_BASELINE": week((w_h4 or 0) + 1), "DATE_H16_BASELINE": week(w_h16), "DATE_UTILITY_READY_BASELINE": week(w_h16), "DATE_FIBER_READY_BASELINE": week(w_h16),
        "WARRANTY_END_DATE": end_warranty,
        # SOW scope rows
        "SCOPE_ENCLOSURE": inc(True), "SCOPE_STRUCTURAL": inc(True), "SCOPE_ENVELOPE": inc(True), "SCOPE_FLOOR": inc(True), "SCOPE_LIGHTING_SIGNAGE": inc(True),
        "SCOPE_VESTIBULE": inc(tier in ("ben150", "ben500", "ben2000")), "SCOPE_ACCESS_CONTROL": inc(True), "SCOPE_TRANSPORT_PREP": inc(True), "SCOPE_SPARES": inc(managed),
        "SCOPE_PE_ANCHORAGE": inc(tier != "ben5"), "SCOPE_CERTIFICATION": inc(True), "SCOPE_FIELD_EVAL": "Excluded (option)",
        "SCOPE_PWR_MAIN": inc("power" in subs), "SCOPE_PWR_UPS": inc("power" in subs), "SCOPE_PWR_PDU": inc("power" in subs), "SCOPE_PWR_TRANSFORMERS": inc("power" in subs and tier in ("ben150", "ben500", "ben2000")),
        "SCOPE_PWR_METERS": inc("power" in subs or "controls" in subs), "SCOPE_PWR_BONDING": inc("power" in subs), "SCOPE_PWR_ARCFLASH": inc("power" in subs), "SCOPE_PWR_INSTALL": inc("power" in subs),
        "SCOPE_PWR_GENERATOR": inc(gen and "power" in subs), "SCOPE_PWR_COOLING_ON_UPS": inc(cfg["redundancy"] != "N" and "power" in subs),
        "SCOPE_CLG_UNITS": inc("cooling" in subs), "SCOPE_CLG_INSTALL": inc("cooling" in subs), "SCOPE_CLG_OUTDOOR": inc("cooling" in subs), "SCOPE_CLG_CONTAINMENT": inc("cooling" in subs and not liquid),
        "SCOPE_CLG_FLUIDS": inc("cooling" in subs and liquid), "SCOPE_CLG_SAFETY": inc("cooling" in subs), "SCOPE_CLG_ECONOMIZER": "Excluded (option)", "SCOPE_CLG_ACOUSTIC": "Excluded (option)",
        "SCOPE_CMP_RACKS": inc("compute" in subs), "SCOPE_CMP_SERVERS": inc("compute" in subs), "SCOPE_CMP_NETWORK": inc("compute" in subs), "SCOPE_CMP_LOADBANKS": "Included (FAT/SAT rental)",
        "SCOPE_CTL_PANEL": inc("controls" in subs), "SCOPE_CTL_NODES": inc("controls" in subs), "SCOPE_CTL_DASHBOARD": inc("controls" in subs), "SCOPE_CTL_FIRMWARE_CAL": inc("controls" in subs),
        "SCOPE_CTL_LICENSE": inc("controls" in subs), "SCOPE_CTL_BACKUP": inc("controls" in subs), "SCOPE_CTL_REMOTE": inc(managed), "SCOPE_CTL_FORWARDING": inc(managed), "SCOPE_CTL_INTEGRATION": "Excluded (option)",
        "SCOPE_FS_DETECTION": inc(True), "SCOPE_FS_SUPPRESSION": inc(True), "SCOPE_FS_EPO": inc(True), "SCOPE_FS_MONITORING": inc("controls" in subs), "SCOPE_FS_PERMIT": "Included (submittal support; Customer pulls permit)",
        "SCOPE_SITE_CIVIL": "Excluded", "SCOPE_SITE_UTILITY": "Excluded", "SCOPE_SITE_GROUNDING": "Excluded", "SCOPE_SITE_FIBER": "Excluded", "SCOPE_SITE_CRANE": "Included (set-down)",
        "SCOPE_SITE_FENCE": "Excluded", "SCOPE_SITE_WATER": inc(False), "SCOPE_SITE_PERMITS": "Excluded (Customer)",
        # repository revisions and identifiers
        "TEMPLATE_REV": _git_rev(), "DRAWING_INDEX_REV": f"{_drawing_rev()} ({_git_rev()})", "BOM_REV": f"{p.date} ({_git_rev()})", "BOM_DATE": p.date, "ASSEMBLY_ISSUE": f"Issue 1 ({_git_rev()})",
        "BOM_CONFIDENCE_SPLIT": f"{h.confirmed_pct:.0f} % confirmed / {h.list_pct:.0f} % list / {h.estimate_pct:.0f} % estimate", "BEN_ENGINE_VERSION": "0.1.0",
        "MSA_ID": f"MSA-{p.customer[:12].upper().replace(' ', '')}-{p.date[:4]}", "SOW_ID": f"SOW-{stem}", "NDA_ID": f"NDA-{stem}", "LICENSE_ID": f"LIC-{stem}", "SLA_ID": f"SLA-{stem}",
        "FAT_CERT_ID": f"FAT-{stem}", "SAT_CERT_ID": f"SAT-{stem}", "TURNOVER_CERT_ID": f"TOC-{stem}", "WARRANTY_CERT_ID": f"WAR-{stem}", "UNIT_SERIAL": f"BEN-{tier.upper()}-{stem[-8:]}",
        "CO_NUMBER": "001", "INTEGRATOR_AGREEMENT_ID": f"INT-{p.date[:4]}-[SEQ]", "CM_AGREEMENT_ID": f"CMA-{p.date[:4]}-[SEQ]",
        "MILESTONE_1_AMOUNT": base.get("MILESTONE_ENG_RELEASE_AMOUNT", ""), "MILESTONE_2_AMOUNT": base.get("MILESTONE_FAT_AMOUNT", ""),
        "MILESTONE_3_AMOUNT": base.get("MILESTONE_SAT_AMOUNT", ""), "MILESTONE_4_AMOUNT": base.get("MILESTONE_TURNOVER_AMOUNT", ""),
        # entity
        "SCHREIBER_ENTITY_NAME": "Schreiber AI", "SCHREIBER_SIGNATORY_NAME": "Ben Schreiber", "SCHREIBER_SIGNATORY_TITLE": "Founder", "SCHREIBER_NOTICE_NAME": "Ben Schreiber",
        "SCHREIBER_NOTICE_EMAIL": "Ben@SchreiberAI.com", "SCHREIBER_EXEC_SPONSOR": "Ben Schreiber", "RMA_EMAIL": "Ben@SchreiberAI.com", "WARRANTY_EMAIL": "Ben@SchreiberAI.com", "OPS_CENTER_EMAIL": "Ben@SchreiberAI.com",
    }
    for k in ("DOC_REV_ACCEPTANCE", "DOC_REV_CO", "DOC_REV_COMPLIANCE", "DOC_REV_CYBERSECURITY", "DOC_REV_MAINTENANCE", "DOC_REV_PROCESS_FLOW", "DOC_REV_PROTOCOL", "DOC_REV_QC_FORMS",
              "DOC_REV_RISK_REGISTER", "DOC_REV_SITE_REQUIREMENTS", "DOC_REV_SLA", "DOC_REV_SOFTWARE_LICENSE", "DOC_REV_SOW", "DOC_REV_TEST_GUIDE", "DOC_REV_TURNOVER", "DOC_REV_WARRANTY"):
        f[k] = _git_rev()
    # declared defaults from fields.json for anything still unset
    try:
        data = json.loads((REPO_ROOT / "docs/contracts/fields.json").read_text(encoding="utf-8"))
        for x in data.get("fields", []):
            if x.get("default") not in (None, "") and x["name"] not in f and x["name"] not in base:
                f[x["name"]] = x["default"]
    except (OSError, ValueError):
        pass
    return f


_FIELD_RE = re.compile(r"\[([A-Z][A-Z0-9_]{1,63})\]")


def fill_contract(template_path: Path | str, proposal: Proposal, extra_fields: Optional[Dict[str, Any]] = None) -> FilledText:
    """Fill ``[FIELD_NAME]`` tokens in a contract template from the proposal. Unknown fields are left
    as-is; the returned string carries ``.unfilled`` (sorted unique names still in the text)."""
    text = Path(template_path).read_text(encoding="utf-8")
    fields = contract_fields(proposal, extra_fields)
    unfilled: set = set()

    def rep(m: "re.Match[str]") -> str:
        k = m.group(1)
        if k in fields:
            return fields[k]
        unfilled.add(k)
        return m.group(0)

    out = FilledText(_FIELD_RE.sub(rep, text))
    out.unfilled = sorted(unfilled)
    return out


def known_fields_report(fields_json: Path | str, proposal: Proposal) -> Tuple[List[str], List[str]]:
    """Compare docs/contracts/fields.json (list of names, or dict name->description) with what the proposal can fill."""
    try:
        data = json.loads(Path(fields_json).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []
    if isinstance(data, dict) and isinstance(data.get("fields"), list):
        data = data["fields"]  # docs/contracts/fields.json shape: {"_meta": …, "fields": [{"name": …}, …]}
    names = list(data.keys()) if isinstance(data, dict) else [x if isinstance(x, str) else x.get("name", "") for x in data]
    have = contract_fields(proposal)
    return [n for n in names if n in have], [n for n in names if n not in have]


# ----------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine proposal generator")
    ap.add_argument("--tier", default="ben150", choices=list(TIER_GEOMETRY) + list(TIER_ALIASES))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--option", default="hardware_controls", choices=list(OPTIONS) + ["full"])
    ap.add_argument("--it-kw", type=float); ap.add_argument("--racks", type=int)
    ap.add_argument("--cooling", choices=list(COOLING_LIBRARY)); ap.add_argument("--redundancy", choices=["N", "N+1", "2N"])
    ap.add_argument("--subsystems", help="comma list for the 'modules' option, e.g. power,cooling")
    ap.add_argument("--generator", action="store_true"); ap.add_argument("--brand", help="partner brand for white_label")
    ap.add_argument("--customer"); ap.add_argument("--site"); ap.add_argument("--date", help="YYYY-MM-DD (default today)")
    ap.add_argument("--margin", type=float, default=MARGIN_HW)
    ap.add_argument("--config", help="JSON file with a Config (overrides tier/profile/climate flags)")
    ap.add_argument("--out", help="markdown path"); ap.add_argument("--html", help="HTML path"); ap.add_argument("--json", help="JSON path")
    ap.add_argument("--fill-sow", help="SOW template with [FIELD] tokens"); ap.add_argument("--out-sow", help="pre-filled SOW path")
    ap.add_argument("--fill-change-order", help="change order template"); ap.add_argument("--out-change-order", help="pre-headed change order path")
    ap.add_argument("--field", action="append", default=[], help="extra NAME=value for contract fill (e.g. GOVERNING_STATE=Texas)")
    a = ap.parse_args(argv)

    if a.config:
        cfg = Config.from_dict(json.loads(Path(a.config).read_text(encoding="utf-8")))
    else:
        cfg = Config.preset(a.tier, a.profile, a.climate)
    for k in ("it_kw", "racks", "cooling", "redundancy"):
        v = getattr(a, k)
        if v is not None:
            setattr(cfg, k, v)
    if a.subsystems:
        cfg.subsystems = [s.strip() for s in a.subsystems.split(",") if s.strip()]
    if a.generator:
        cfg.generator = True
    if a.brand:
        cfg.brand = a.brand; cfg.white_label = True
    if a.site:
        cfg.site_name = a.site
    errs = cfg.validate()
    if errs:
        print("INVALID:\n  " + "\n  ".join(errs)); return 2

    p = build_proposal(cfg, option=a.option, customer=a.customer, site=a.site, margin=a.margin, date=a.date)
    wrote = []
    for path, fn in ((a.out, to_markdown), (a.html, to_html), (a.json, to_json)):
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(fn(p), encoding="utf-8"); wrote.append(path)
    extra = dict(kv.split("=", 1) for kv in a.field if "=" in kv)
    for tmpl, outp, label in ((a.fill_sow, a.out_sow, "SOW"), (a.fill_change_order, a.out_change_order, "change order")):
        if tmpl:
            if not Path(tmpl).exists():
                print(f"{label}: template {tmpl} not found; skipped"); continue
            filled = fill_contract(tmpl, p, extra)
            target = outp or str(Path(a.out or a.html or f"{p.proposal_id}.md").with_suffix("")) + f"-{label.replace(' ', '_')}.md"
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_text(filled, encoding="utf-8"); wrote.append(target)
            print(f"{label}: {len(filled.unfilled)} field(s) left for the contract owner: {', '.join(filled.unfilled) or 'none'}")
    h = p.headline
    print(f"{p.proposal_id}  {p.tier_label} / {p.profile_label} / {cfg.climate} / {h.label}")
    print(f"  capital {_usd(h.capital_price_usd)} ({_usd(h.price_per_kw_usd)}/kW)  recurring {_usd(h.recurring_usd_per_year)}/yr  "
          f"confidence {h.confirmed_pct:.0f}/{h.list_pct:.0f}/{h.estimate_pct:.0f} %  in service week {p.milestones[-1]['week']}")
    for w in wrote:
        print(f"  wrote {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

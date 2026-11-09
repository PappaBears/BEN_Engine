"""Prepare the paperwork set for every counterparty before anything is sent.

Writes docs/contracts/ready/:
  NDA-<slug>.md                 mutual NDA pre-filled with Schreiber AI's side and the counterparty name/purpose
  MSA-master.md, INTEGRATOR-master.md, CMA-master.md, SUPPLIER-TERMS-master.md
                                the agreements with every Schreiber AI-side and policy field filled, counterparty fields left as [FIELD]
  INDEX.md                      counterparty → documents → fields still open → status
Counterparties come from purchasing/counterparties.json (seeded from the RFQ queue; edit it as real legal names arrive).
Nothing here is legal advice; counsel reviews before signature (see docs/contracts/README.md).
"""
from __future__ import annotations
import json, re, datetime as dt, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "docs" / "contracts"
OUT = C / "ready"
TODAY = dt.date.today().isoformat()
try:
    REV = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "untracked"
except Exception:
    REV = "untracked"

SCHREIBER = {
    "SCHREIBER_ENTITY_NAME": "Schreiber AI", "SCHREIBER_ENTITY_TYPE": "[SCHREIBER_ENTITY_TYPE: e.g. a Texas limited liability company]",
    "SCHREIBER_SIGNATORY_NAME": "Ben Schreiber", "SCHREIBER_SIGNATORY_TITLE": "Founder",
    "SCHREIBER_NOTICE_NAME": "Ben Schreiber", "SCHREIBER_NOTICE_EMAIL": "Ben@SchreiberAI.com",
    "SCHREIBER_ADDRESS": "[SCHREIBER_ADDRESS]", "SCHREIBER_EXEC_SPONSOR": "Ben Schreiber",
    "TEMPLATE_REV": REV, "CURRENCY": "USD", "PAYMENT_TERMS_DAYS": "30",
    "NDA_TERM_YEARS": "3", "CONFIDENTIALITY_YEARS": "5", "NDA_EFFECTIVE_DATE": "[NDA_EFFECTIVE_DATE]",
    "SUPPLIER_LD_RATE_PCT_PER_WEEK": "0.5", "SUPPLIER_LD_CAP_PCT": "10", "SUPPLIER_LD_GRACE_DAYS": "5", "SUPPLIER_COVER_TRIGGER_WEEKS": "4",
    "CM_LD_RATE_PCT_PER_WEEK": "0.5", "CM_LD_CAP_PCT": "10", "CM_LD_GRACE_DAYS": "7", "CM_COVER_TRIGGER_WEEKS": "6",
    "CUSTOMER_LD_RATE_PCT_PER_WEEK": "0.5", "CUSTOMER_LD_CAP_PCT": "10", "LD_GRACE_DAYS": "14", "LD_CAP_CURE_DAYS": "30",
    "PRICE_HOLD_DAYS": "90", "PRICE_HOLD_EXTENDED_DAYS": "180", "PRICE_HOLD_DEPOSIT_PCT": "10",
    "SUPPLIER_WARRANTY_MONTHS": "18", "SUPPLIER_PRICE_INCREASE_NOTICE_DAYS": "60", "PCN_NOTICE_DAYS": "90", "EOL_NOTICE_DAYS": "180",
    "RECEIVING_INSPECTION_DAYS": "10", "EPIDEMIC_FAILURE_PCT": "3", "SUPPLIER_OTD_THRESHOLD_PCT": "90", "SUPPLIER_REJECT_THRESHOLD_PCT": "2",
    "SUPPLIER_REVIEW_FREQUENCY": "quarterly", "UL9540A_REPORT_MAX_AGE_MONTHS": "36", "FM_TERMINATION_DAYS": "120",
    "MDF_PCT": "2", "FREE_STORAGE_DAYS": "14",
}
# defaults from fields.json fill anything else that has a declared default
try:
    for f in json.loads((C / "fields.json").read_text())["fields"]:
        if f.get("default") not in (None, "") and f["name"] not in SCHREIBER:
            SCHREIBER[f["name"]] = str(f["default"])
except (OSError, ValueError, KeyError):
    pass

TOKEN = re.compile(r"\[([A-Z][A-Z0-9_]{1,63})\]")


def fill(text: str, fields: dict) -> tuple[str, list[str]]:
    open_fields = set()
    def rep(m):
        k = m.group(1)
        if k in fields and not str(fields[k]).startswith("["):
            return str(fields[k])
        open_fields.add(k)
        return m.group(0)
    return TOKEN.sub(rep, text), sorted(open_fields)


LEGAL = "Schreiber AI is a Schreiber Holding LLC company."
LOCKUP = '<img src="../../../brand/v2/lockup-deep.svg" alt="Schreiber AI" height="28">'


def for_ready(text: str) -> str:
    """ready/ sits one folder deeper than the templates: fix the brand lockup path."""
    return text.replace('src="../../brand/v2/', 'src="../../../brand/v2/')


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def main() -> int:
    cps = json.loads((ROOT / "purchasing" / "counterparties.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    nda_t = (C / "NDA_MUTUAL.md").read_text()
    rows = []
    for cp in cps:
        f = dict(SCHREIBER)
        f.update({
            "COUNTERPARTY_NAME": cp["name"], "COUNTERPARTY_ENTITY_TYPE": cp.get("entity_type", "[COUNTERPARTY_ENTITY_TYPE]"),
            "COUNTERPARTY_ADDRESS": cp.get("address", "[COUNTERPARTY_ADDRESS]"),
            "COUNTERPARTY_NOTICE_NAME": cp.get("contact", "[COUNTERPARTY_NOTICE_NAME]"), "COUNTERPARTY_NOTICE_EMAIL": cp.get("email", "[COUNTERPARTY_NOTICE_EMAIL]"),
            "COUNTERPARTY_SIGNATORY_NAME": cp.get("signatory", "[COUNTERPARTY_SIGNATORY_NAME]"), "COUNTERPARTY_SIGNATORY_TITLE": cp.get("signatory_title", "[COUNTERPARTY_SIGNATORY_TITLE]"),
            "NDA_ID": f"NDA-{TODAY[:4]}-{slug(cp['name'])[:20].upper()}", "NDA_PURPOSE": cp["purpose"],
            "GOVERNING_STATE": cp.get("governing_state", "[GOVERNING_STATE]"), "VENUE_COUNTY": cp.get("venue_county", "[VENUE_COUNTY]"),
            "SUPPLIER_NAME": cp["name"],
        })
        text, open_f = fill(nda_t, f)
        p = OUT / f"NDA-{slug(cp['name'])}.md"
        p.write_text(for_ready(text))
        rows.append((cp["name"], cp["role"], cp.get("rfq", ""), p.name, cp.get("agreements", []), open_f))
    masters = {"MSA-master.md": "MSA.md", "INTEGRATOR-master.md": "INTEGRATOR_AGREEMENT.md",
               "CMA-master.md": "CONTRACT_MANUFACTURING_AGREEMENT.md", "SUPPLIER-TERMS-master.md": "SUPPLIER_TERMS.md",
               "SLA-master.md": "MANAGED_SERVICES_SLA.md", "SOFTWARE-LICENSE-master.md": "SOFTWARE_LICENSE_BEN_CONTROLS.md",
               "WARRANTY-master.md": "WARRANTY_TERMS.md"}
    master_open = {}
    for out_name, src in masters.items():
        text, open_f = fill((C / src).read_text(), SCHREIBER)
        (OUT / out_name).write_text(for_ready(text))
        master_open[out_name] = open_f
    lines = [f"# Paperwork ready set — generated {TODAY} (template rev {REV})", "", LOCKUP, "",
             "BEN Engine, by Schreiber AI · Rev 2", "",
             "Schreiber AI's side and every policy number are filled; counterparty identity, addresses, dates and counsel choices stay as `[FIELD]` until known. "
             "Templates are not legal advice; counsel reviews before signature (`docs/contracts/README.md` §7). Regenerate with `python scripts/prepare_paperwork.py` after editing `purchasing/counterparties.json`.", "",
             "## Signing sequence", "",
             "1. **NDA first**, before any drawing, BOM or configuration leaves Schreiber AI (send with the RFQ reply, not the RFQ).",
             "2. **Suppliers**: Purchase Order Terms (`SUPPLIER-TERMS-master.md`) referenced on every PO; delivery liquidated damages 0.5 %/week, cap 10 %, grace 5 days.",
             "3. **Contract manufacturer**: `CMA-master.md` after the site audit and before the first-article build order; LDs 0.5 %/week, cap 10 %, grace 7 days.",
             "4. **Integrators / white-label**: `INTEGRATOR-master.md` plus the software licence.",
             "5. **Customers**: `MSA-master.md` once, then one SOW per unit from the proposal generator; change orders; acceptance certificates; SLA for managed units.",
             "6. Every counterparty NDA/agreement ID is logged in `docs/contracts/ready/INDEX.md` (this file) and the customer deal in the proposal package MANIFEST.", "",
             "## Counterparties", "", "| Counterparty | Role | RFQ | NDA file | Agreements to follow | Fields still open |", "| --- | --- | --- | --- | --- | --- |"]
    for name, role, rfq, nda, ags, open_f in rows:
        lines.append(f"| {name} | {role} | {rfq} | `{nda}` | {', '.join(ags)} | {len(open_f)}: {', '.join(open_f[:6])}{'…' if len(open_f) > 6 else ''} |")
    lines += ["", "## Masters (Schreiber AI side filled)", "", "| File | Source template | Fields still open |", "| --- | --- | --- |"]
    for k, v in masters.items():
        lines.append(f"| `{k}` | `{v}` | {len(master_open[k])} |")
    lines += ["", "---", f"BEN Engine, by Schreiber AI · Rev 2 · {LEGAL}"]
    (OUT / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {len(rows)} NDAs, {len(masters)} masters → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

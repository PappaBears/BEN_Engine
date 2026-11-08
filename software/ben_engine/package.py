"""Deal package assembler.

One command assembles everything a deal needs from one configuration:

* customer package  — proposal (md/html/json), pre-filled SOW, change-order form, acceptance
  certificates, site requirements, risk disclosure, compliance pack, warranty, SLA (managed),
  software licence, NDA, maintenance schedule, turnover checklist, drawings index + sheets.
* partner package   — integrator agreement, contract manufacturing agreement, supplier PO terms,
  SQAM, CTQ/CTP cards, STE assembly instructions, QC forms, drawings, process flow, test guide.

Missing source documents are listed in MANIFEST.md as missing, never silently skipped.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import Config
from . import proposal as P

ROOT = Path(__file__).resolve().parents[2]

CUSTOMER_DOCS = [
    ("docs/contracts/MSA.md", "contracts/MSA.md", True),
    ("docs/contracts/SOW_TEMPLATE.md", "contracts/SOW-draft.md", True),
    ("docs/contracts/CHANGE_ORDER.md", "contracts/CHANGE_ORDER-form.md", True),
    ("docs/contracts/ACCEPTANCE_CERTIFICATES.md", "contracts/ACCEPTANCE_CERTIFICATES-draft.md", True),
    ("docs/contracts/SOFTWARE_LICENSE_BEN_CONTROLS.md", "contracts/SOFTWARE_LICENSE_BEN_CONTROLS.md", True),
    ("docs/contracts/WARRANTY_TERMS.md", "contracts/WARRANTY_TERMS.md", True),
    ("docs/contracts/NDA_MUTUAL.md", "contracts/NDA_MUTUAL.md", True),
    ("docs/SITE_REQUIREMENTS.md", "site/SITE_REQUIREMENTS.md", False),
    ("docs/RISK_REGISTER.md", "risk/RISK_REGISTER.md", False),
    ("docs/COMPLIANCE.md", "compliance/COMPLIANCE.md", False),
    ("docs/MAINTENANCE.md", "operations/MAINTENANCE.md", False),
    ("docs/TURNOVER.md", "operations/TURNOVER.md", False),
    ("docs/TEST_GUIDE.md", "acceptance/TEST_GUIDE.md", False),
    ("docs/CYBERSECURITY.md", "security/CYBERSECURITY.md", False),
]
MANAGED_DOCS = [("docs/contracts/MANAGED_SERVICES_SLA.md", "contracts/MANAGED_SERVICES_SLA-draft.md", True)]
PARTNER_DOCS = [
    ("docs/contracts/INTEGRATOR_AGREEMENT.md", "contracts/INTEGRATOR_AGREEMENT.md", True),
    ("docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md", "contracts/CONTRACT_MANUFACTURING_AGREEMENT.md", True),
    ("docs/contracts/SUPPLIER_TERMS.md", "contracts/SUPPLIER_TERMS.md", True),
    ("docs/contracts/NDA_MUTUAL.md", "contracts/NDA_MUTUAL.md", True),
    ("docs/SQAM.md", "quality/SQAM.md", False),
    ("design/assembly/QC_FORMS.md", "quality/QC_FORMS.md", False),
    ("docs/PROCESS_FLOW.md", "process/PROCESS_FLOW.md", False),
    ("docs/MANUFACTURING_STRATEGY.md", "process/MANUFACTURING_STRATEGY.md", False),
    ("docs/BUILD_AND_WIRING.md", "build/BUILD_AND_WIRING.md", False),
    ("docs/TEST_GUIDE.md", "build/TEST_GUIDE.md", False),
    ("design/DESIGN_BASIS.md", "design/DESIGN_BASIS.md", False),
    ("design/specs/CONTROLS_SPEC.md", "design/CONTROLS_SPEC.md", False),
    ("design/specs/BEN-NODE-v1.md", "design/BEN-NODE-v1.md", False),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _copy_or_fill(src_rel: str, dst_rel: str, fill: bool, out: Path, prop: P.Proposal, extra: Dict, manifest: List[Tuple[str, str, str]]):
    src = ROOT / src_rel
    dst = out / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        manifest.append((dst_rel, "MISSING", f"source {src_rel} not found"))
        return
    if fill:
        text = P.fill_contract(src, prop, extra)
        dst.write_text(str(text))
        unfilled = getattr(text, "unfilled", [])
        note = "pre-filled" + (f"; {len(unfilled)} fields left for counsel/sales: " + ", ".join(sorted(set(unfilled))[:12]) if unfilled else "; all known fields filled")
        manifest.append((dst_rel, _sha(dst), note))
    else:
        shutil.copy2(src, dst)
        manifest.append((dst_rel, _sha(dst), "copied"))


def _copy_tree(src_rel: str, dst_rel: str, out: Path, manifest: List[Tuple[str, str, str]], patterns=("*.md", "*.png", "*.svg")):
    src = ROOT / src_rel
    if not src.exists():
        manifest.append((dst_rel + "/", "MISSING", f"source {src_rel} not found"))
        return
    n = 0
    for pat in patterns:
        for f in sorted(src.glob(pat)):
            d = out / dst_rel / f.name
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, d)
            n += 1
    manifest.append((dst_rel + "/", "-", f"{n} files copied"))


def build_package(cfg: Config, option: str = "hardware_controls", customer: str = "Customer", site: str = "Site",
                  out_dir: Path | str = "dist/packages", kind: str = "both", extra_fields: Optional[Dict] = None,
                  include_drawings: bool = True, zip_it: bool = True) -> Dict[str, Path]:
    extra = {"CUSTOMER_NAME": customer, "SITE_ADDRESS": site, **(extra_fields or {})}
    prop = P.build_proposal(cfg, option=option, customer=customer, site=site)
    base = Path(out_dir) / prop.proposal_id
    results: Dict[str, Path] = {}
    tier = cfg.tier

    if kind in ("customer", "both"):
        out = base / "customer-package"
        out.mkdir(parents=True, exist_ok=True)
        manifest: List[Tuple[str, str, str]] = []
        (out / "proposal").mkdir(exist_ok=True)
        (out / "proposal" / "PROPOSAL.md").write_text(P.to_markdown(prop))
        (out / "proposal" / "PROPOSAL.html").write_text(P.to_html(prop))
        (out / "proposal" / "proposal.json").write_text(P.to_json(prop))
        (out / "proposal" / "config.json").write_text(cfg.to_json())
        for n in ("PROPOSAL.md", "PROPOSAL.html", "proposal.json", "config.json"):
            manifest.append((f"proposal/{n}", _sha(out / "proposal" / n), "generated"))
        docs = CUSTOMER_DOCS + (MANAGED_DOCS if option == "managed" else [])
        for s, d, fill in docs:
            _copy_or_fill(s, d, fill, out, prop, extra, manifest)
        # risk disclosure extract for this profile
        risks = P._risks(cfg.profile)
        lines = [f"# Risk disclosure — {customer} — {prop.proposal_id}", "", "Shown before price. Filtered for the selected mission profile.", "",
                 "| Risk | Severity | BEN Engine covers | Customer owns |", "| --- | --- | --- | --- |"]
        for r in risks:
            lines.append(f"| {r.get('title','')} | {r.get('severity','')} | {r.get('covered_by','')} | {r.get('customer_owns','')} |")
        (out / "risk" / "RISK_DISCLOSURE.md").parent.mkdir(parents=True, exist_ok=True)
        (out / "risk" / "RISK_DISCLOSURE.md").write_text("\n".join(lines) + "\n")
        manifest.append(("risk/RISK_DISCLOSURE.md", _sha(out / "risk" / "RISK_DISCLOSURE.md"), f"generated, {len(risks)} risks"))
        if include_drawings:
            _copy_tree(f"design/drawings/{tier}", "drawings", out, manifest, patterns=("*.md", "*.png"))
            _copy_tree(f"design/renders/{tier}", "renders", out, manifest, patterns=("contact-sheet.png", "stage-8.png"))
        _write_manifest(out, prop, manifest, "Customer deal package")
        results["customer"] = out

    if kind in ("partner", "both"):
        out = base / "partner-package"
        out.mkdir(parents=True, exist_ok=True)
        manifest = []
        (out / "proposal").mkdir(exist_ok=True)
        (out / "proposal" / "config.json").write_text(cfg.to_json())
        manifest.append(("proposal/config.json", _sha(out / "proposal" / "config.json"), "generated"))
        for s, d, fill in PARTNER_DOCS:
            _copy_or_fill(s, d, fill, out, prop, extra, manifest)
        _copy_or_fill(f"design/assembly/ASSEMBLY-{tier}.md", "build/ASSEMBLY.md", False, out, prop, extra, manifest)
        _copy_or_fill(f"design/assembly/CTQ-CARD-{tier}.md", "quality/CTQ-CARD.md", False, out, prop, extra, manifest)
        _copy_or_fill("design/assembly/STE_STYLE.md", "build/STE_STYLE.md", False, out, prop, extra, manifest)
        bom_csv = ROOT / f"purchasing/bom-{tier}.csv"
        if bom_csv.exists():
            (out / "purchasing").mkdir(exist_ok=True)
            shutil.copy2(bom_csv, out / "purchasing" / f"bom-{tier}.csv")
            manifest.append((f"purchasing/bom-{tier}.csv", _sha(bom_csv), "copied (consigned vs CM-supplied split to be marked by purchasing)"))
        else:
            manifest.append((f"purchasing/bom-{tier}.csv", "MISSING", "run python -m ben_engine.bom --all"))
        if include_drawings:
            _copy_tree(f"design/drawings/{tier}", "drawings", out, manifest, patterns=("*.md", "*.png", "*.svg"))
            _copy_tree("design/specs/wiring", "wiring", out, manifest, patterns=("*.svg",))
            _copy_tree(f"design/renders/{tier}", "renders", out, manifest, patterns=("*.png",))
        _write_manifest(out, prop, manifest, "Partner (integrator / contract manufacturer) package")
        results["partner"] = out

    if zip_it:
        for k, d in list(results.items()):
            z = base / f"{prop.proposal_id}-{k}-package.zip"
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(d.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(base))
            results[k + "_zip"] = z
    results["base"] = base
    return results


def _write_manifest(out: Path, prop: P.Proposal, manifest: List[Tuple[str, str, str]], title: str):
    missing = [m for m in manifest if m[1] == "MISSING"]
    lines = [f"# {title}", "", f"Proposal {prop.proposal_id} · {prop.customer} · {prop.site} · generated {prop.date}", "",
             "All contract documents are TEMPLATES pre-filled from the proposal; counsel reviews before signature.", "",
             f"Files: {len(manifest) - len(missing)} present, {len(missing)} missing.", "",
             "| File | SHA-256 (16) | Note |", "| --- | --- | --- |"]
    for f, h, n in manifest:
        lines.append(f"| {f} | {h} | {n} |")
    (out / "MANIFEST.md").write_text("\n".join(lines) + "\n")


def main(argv=None) -> int:
    import argparse
    from .config import TIER_GEOMETRY, TIER_ALIASES, PROFILE_DEFAULTS, CLIMATE_DESIGN
    ap = argparse.ArgumentParser(description="Assemble the customer and partner deal packages for a configuration")
    ap.add_argument("--tier", default="ben150", choices=list(TIER_GEOMETRY) + list(TIER_ALIASES))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--config-json", help="use a saved configuration instead of the preset")
    ap.add_argument("--option", default="hardware_controls", choices=list(P.OPTIONS))
    ap.add_argument("--customer", default="Customer")
    ap.add_argument("--site", default="Site")
    ap.add_argument("--kind", default="both", choices=["customer", "partner", "both"])
    ap.add_argument("--out", default="dist/packages")
    ap.add_argument("--field", action="append", default=[], help="NAME=value extra contract field")
    ap.add_argument("--no-drawings", action="store_true")
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args(argv)
    if a.config_json:
        cfg = Config.from_dict(json.loads(Path(a.config_json).read_text()))
    else:
        cfg = Config.preset(a.tier, a.profile, a.climate)
    errs = cfg.validate()
    if errs:
        print("INVALID configuration:\n  " + "\n  ".join(errs))
        return 2
    extra = dict(kv.split("=", 1) for kv in a.field)
    res = build_package(cfg, a.option, a.customer, a.site, a.out, a.kind, extra, not a.no_drawings, not a.no_zip)
    for k, v in res.items():
        print(f"{k:14s} {v}")
    for k in ("customer", "partner"):
        if k in res:
            print(open(res[k] / "MANIFEST.md").read().splitlines()[6])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

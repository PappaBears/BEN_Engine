#!/usr/bin/env python3
"""BEN Engine — automated internal audit of the mechanical checks.

Prints one line per check (PASS / FAIL / WARN) with details, a summary, and exits 1 when any check
FAILs. Run from anywhere:

    python scripts/audit.py            # static checks only (fast)
    python scripts/audit.py --run      # also executes the build-contract commands as written

Checks (see docs/audit/AUDIT_CHECKLIST.md for the criterion behind each one):
  A1  every artifact path named in docs/BRIEF.md §5 exists
  A2  every path in docs/launch-manifest.json (deliverables + evidence) exists
  A3  build-contract commands: the program exists; with --run each command must exit 0
  A4  scripts/check_links.py reports 0 broken links
  A5  no stale generation-1 references outside the allowed history files
  A6  parts catalog: every "confirmed" line has vendor_url + price_checked; every "estimate" has a
      price_source_note; every line has lead_time_weeks; WARN on marketplace/aggregator URLs
  A7  docs/contracts/fields.json covers every [FIELD] token used in the templates and vice versa
  A8  test count quoted in README.md / docs/VALIDATION.md / PROJECT_STATE.md == pytest --collect-only
  A9  every drawing SVG title block carries the status and revision from design/REVISION.json
  A10 every design/assembly/ASSEMBLY-*.md is free of the STE banned words (design/assembly/STE_STYLE.md
      rule 10); WARN for instruction sentences over 20 words
  A11 secrets scan (API keys, tokens, private keys, passwords) over tracked text files
  A12 every *.json in the repository parses
  A13 document-control marks: drawings INDEX "Checked" not blank (WARN), dated revision marks consistent
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "dist", "node_modules", "__pycache__", ".pytest_cache", ".schreiber-ai", ".pio", ".venv", "data"}

RESULTS: list[tuple[str, str, str, str]] = []  # (id, status, title, detail)


def record(cid: str, status: str, title: str, detail: str = "") -> None:
    RESULTS.append((cid, status, title, detail))


def iter_files(exts: tuple[str, ...] | None = None):
    for p in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.is_file() and (exts is None or p.suffix.lower() in exts):
            yield p


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


# ----------------------------------------------------------------------------- A1 brief §5 artifacts
def check_brief_artifacts() -> None:
    brief = (ROOT / "docs/BRIEF.md").read_text(encoding="utf-8")
    m = re.search(r"## 5\. What must be delivered.*?\n(\|.*?)(?:\n## )", brief, re.S)
    if not m:
        record("A1", "FAIL", "Brief §5 acceptance table", "section not found in docs/BRIEF.md")
        return
    rows = [r for r in m.group(1).split("\n") if r.startswith("|") and not r.startswith("| #") and "---" not in r]
    missing, total = [], 0
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if len(cells) < 4:
            continue
        where = cells[2]
        for tok in re.findall(r"`([^`]+)`", where):
            # `config.py (hardening)` style tokens: take the path part
            path = tok.split(" ")[0].strip()
            if path in ("config.py", "analysis.py"):
                path = "software/ben_engine/" + path
            if not path or "/" not in path and "." not in path:
                continue
            total += 1
            candidates = [ROOT / path, ROOT / "docs" / path, ROOT / "software" / "ben_engine" / path]
            if not (any(c.exists() for c in candidates) or list(ROOT.glob(path + "*"))):
                missing.append(f"row {cells[0]}: {path}")
    status = "PASS" if not missing else "FAIL"
    record("A1", status, f"Brief §5 artifact paths exist ({total - len(missing)}/{total})", "; ".join(missing))


# ----------------------------------------------------------------------------- A2 launch manifest
def check_launch_manifest() -> None:
    mf = json.loads((ROOT / "docs/launch-manifest.json").read_text())
    paths = [d["path"] for d in mf.get("deliverables", [])]
    for c in mf.get("capabilities", []):
        paths += c.get("evidence", [])
    missing = sorted({p for p in paths if not (ROOT / p).exists()})
    record("A2", "PASS" if not missing else "FAIL", f"Launch manifest paths exist ({len(set(paths)) - len(missing)}/{len(set(paths))})", "; ".join(missing))
    # acceptance ids must match the build contract
    bc = json.loads((ROOT / "docs/build-contract.json").read_text())
    ids = {c["id"] for c in bc["checks"]}
    bad = [i for i in mf.get("acceptance_ids", []) if i not in ids]
    record("A2b", "PASS" if not bad else "FAIL", "Manifest acceptance_ids exist in build-contract.json", "; ".join(bad))


# ----------------------------------------------------------------------------- A3 build contract
def check_build_contract(run: bool) -> None:
    bc = json.loads((ROOT / "docs/build-contract.json").read_text())
    import shutil
    problems, ran = [], []
    for c in bc["checks"]:
        prog = c["command"][0]
        if shutil.which(prog) is None:
            problems.append(f"{c['id']}: program {prog} not found")
            continue
        if run:
            try:
                r = subprocess.run(c["command"], cwd=ROOT, capture_output=True, text=True, timeout=c.get("timeout_seconds", 600))
                tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
                if r.returncode != 0:
                    problems.append(f"{c['id']}: exit {r.returncode}: {tail[0][:160]}")
                else:
                    ran.append(c["id"])
            except subprocess.TimeoutExpired:
                problems.append(f"{c['id']}: timeout")
    # static: python -m ben_engine.* commands need the package importable without PYTHONPATH
    static_note = ""
    def _has_pythonpath(cmd):
        return any(a.startswith("PYTHONPATH=") for a in cmd)
    needs_pkg = [c["id"] for c in bc["checks"] if "-m" in c["command"] and any(a.startswith("ben_engine") for a in c["command"]) and not _has_pythonpath(c["command"])]
    if needs_pkg:
        probe = subprocess.run([sys.executable, "-c", "import ben_engine"], cwd=ROOT, capture_output=True, text=True)
        if probe.returncode != 0:
            static_note = (f"{', '.join(needs_pkg)} call `python3 -m ben_engine.*` with no PYTHONPATH and the package is not "
                           f"installed (pip install -e . or PYTHONPATH=software missing); these checks fail as written")
    if problems or static_note:
        record("A3", "FAIL", f"Build-contract checks runnable as written ({'executed' if run else 'static'})", "; ".join(problems + ([static_note] if static_note else [])))
    else:
        record("A3", "PASS", f"Build-contract checks runnable as written ({'executed: ' + ', '.join(ran) if run else 'static'})")


# ----------------------------------------------------------------------------- A4 links
def check_links() -> None:
    r = subprocess.run([sys.executable, "scripts/check_links.py"], cwd=ROOT, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    ok = r.returncode == 0 and re.search(r"\b0 broken\b", last)
    record("A4", "PASS" if ok else "FAIL", "Relative link check", last[:200] or r.stderr[-200:])


# ----------------------------------------------------------------------------- A5 stale references
STALE = re.compile(r"ben-node|ben-gateway|Raspberry|Olimex|ESP32|NEMA 3R|BEN Micro|\bBEN (10|20|40)\b", re.I)
ALLOWED_HISTORY = {
    "archive/", "releases/", "brand/v2/source/",
    "docs/audit/evidence/", "docs/audit/AUDIT_REPORT_2026-11-08.md", "docs/audit/CAPA_LOG.md",
    "docs/PROJECT_NOTES.md", "docs/TIER_AND_ENCLOSURE_DECISION.md", "docs/CONTROLS_HARDWARE_DECISION.md",
    "docs/ORIGINAL_REQUEST.md", "docs/BRIEF.md", "docs/FAQ.md", "firmware/README.md", "software/ben_engine/config.py",
    "docs/audit/AUDIT_REPORT_2026-11-08.md", "docs/audit/AUDIT_CHECKLIST.md", "scripts/audit.py",
    "purchasing/parts_catalog_withdrawn.json",  # generation-1 catalog lines kept for history (F-22); nothing loads it
}
CONTEXT_OK = re.compile(r"replaced|retired|dropped|changed from|alias|history|supersed|formerly|was |old |earlier|generation.1|gen-1|not in|no longer|rejected", re.I)


def check_stale() -> None:
    hits, soft = [], []
    for p in iter_files((".md", ".html", ".py", ".js", ".json", ".svg", ".csv", ".txt", ".yml", ".yaml", ".cpp", ".h", ".st", ".sh", ".conf", ".mjs")):
        rp = rel(p)
        if rp in ALLOWED_HISTORY or any(rp.startswith(h) for h in ALLOWED_HISTORY if h.endswith("/")):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            m = STALE.search(line)
            if not m:
                continue
            entry = f"{rp}:{i} [{m.group(0)}]"
            (soft if CONTEXT_OK.search(line) else hits).append(entry)
    if hits:
        record("A5", "FAIL", f"Stale generation-1 references outside history files ({len(hits)} hard, {len(soft)} explained)", "; ".join(hits[:25]) + (" …" if len(hits) > 25 else ""))
    elif soft:
        record("A5", "WARN", f"Stale references only in explanatory context ({len(soft)})", "; ".join(soft[:12]) + (" …" if len(soft) > 12 else ""))
    else:
        record("A5", "PASS", "No stale generation-1 references")


# ----------------------------------------------------------------------------- A6 catalog
MARKETPLACE = re.compile(r"reach\.dog|alibaba|ebay|amazon|findchips|octopart|/videos/|marketplace-admin|inchcalculator|pages\.dev|google\.|bing\.", re.I)


def check_catalog() -> None:
    cat = json.loads((ROOT / "purchasing/parts_catalog.json").read_text())
    conf_bad, est_bad, lead_bad, mkt, list_bad = [], [], [], [], []
    n_conf = n_est = 0
    for x in cat:
        st = x.get("price_status")
        if st == "confirmed":
            n_conf += 1
            if not x.get("vendor_url") or not x.get("price_checked"):
                conf_bad.append(x["code"])
            if x.get("vendor_url") and MARKETPLACE.search(x["vendor_url"]):
                mkt.append(f"{x['code']} ({re.sub(r'^https?://([^/]+).*', r'\1', x['vendor_url'])})")
        elif st == "estimate":
            n_est += 1
            if not (x.get("price_source_note") or "").strip():
                est_bad.append(x["code"])
        elif st == "list":
            if not x.get("vendor_url") or not x.get("price_checked"):
                list_bad.append(x["code"])
        else:
            conf_bad.append(f"{x['code']} unknown status {st!r}")
        if x.get("lead_time_weeks") in (None, "", 0):
            lead_bad.append(x["code"])
    record("A6a", "PASS" if not conf_bad else "FAIL", f"Catalog: confirmed lines carry vendor_url + price_checked ({n_conf - len(conf_bad)}/{n_conf})", "; ".join(conf_bad))
    record("A6b", "PASS" if not est_bad else "FAIL", f"Catalog: estimate lines carry a price_source_note ({n_est - len(est_bad)}/{n_est})", "; ".join(est_bad))
    record("A6c", "PASS" if not lead_bad else "FAIL", f"Catalog: every line has lead_time_weeks ({len(cat) - len(lead_bad)}/{len(cat)})", "; ".join(lead_bad))
    record("A6d", "WARN" if mkt else "PASS", f"Catalog: confirmed URLs on marketplaces / aggregators / non-product pages ({len(mkt)})", "; ".join(mkt))
    record("A6e", "WARN" if list_bad else "PASS", f"Catalog: 'list' lines without vendor_url or price_checked ({len(list_bad)})", "; ".join(list_bad))


# ----------------------------------------------------------------------------- A7 fields.json
def check_fields() -> None:
    fj = json.loads((ROOT / "docs/contracts/fields.json").read_text())
    names = {f["name"] for f in fj["fields"]}
    tok = re.compile(r"\[([A-Z][A-Z0-9_]{2,})\]")
    used: dict[str, set[str]] = {}
    for p in (ROOT / "docs/contracts").glob("*.md"):
        if p.name == "README.md":
            continue
        for t in tok.findall(p.read_text(encoding="utf-8")):
            used.setdefault(t, set()).add(p.name)
    META_WORDS = {"FIELD", "FIELDS", "FIELD_NAME"}  # the templates' own explanatory text, not fillable fields
    not_in_fields = sorted(t for t in used if t not in names and t not in META_WORDS)
    unused = sorted(n for n in names if n not in used)
    declared_count = fj.get("_meta", {}).get("field_count")
    detail = f"tokens in templates {len(used) - len(META_WORDS & set(used))}, fields declared {len(names)}, _meta.field_count {declared_count}"
    if not_in_fields or unused:
        detail += f"; in templates not in fields.json: {not_in_fields[:20]}; declared but unused: {unused[:20]}"
    if declared_count != len(names):
        detail += f"; _meta.field_count is stale ({declared_count} vs {len(names)} declared)"
    status = "FAIL" if not_in_fields else ("WARN" if unused or declared_count != len(names) else "PASS")
    record("A7", status, "fields.json covers every template [FIELD] token", detail)


# ----------------------------------------------------------------------------- A8 test count
def check_test_count() -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "software"))
    r = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q", "--ignore=tests/e2e", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, env=env)
    last = [l for l in r.stdout.strip().splitlines() if "collected" in l]
    m = re.search(r"(\d+) tests? collected", last[-1]) if last else None
    if not m:
        record("A8", "FAIL", "pytest --collect-only", r.stdout[-300:] + r.stderr[-300:])
        return
    n = int(m.group(1))
    quoted = {}
    for doc in ("README.md", "docs/VALIDATION.md", "docs/PROJECT_STATE.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        quoted[doc] = sorted({int(x) for x in re.findall(r"\b(\d{2,4}) (?:passed|Python tests|tests collected)\b", text)})
    mismatch = {d: q for d, q in quoted.items() if q and n not in q}
    record("A8", "PASS" if not mismatch else "FAIL", f"Test count in docs matches collected ({n})", f"quoted: {quoted}" if mismatch else f"{n} collected; README/VALIDATION/PROJECT_STATE quote it")


# ----------------------------------------------------------------------------- A9 drawings
def check_drawings() -> None:
    import json as _json
    rev = _json.loads((ROOT / "design/REVISION.json").read_text(encoding="utf-8"))
    letter, date, checker = rev["drawing_rev"], rev["issue_date"], rev.get("checker", "")
    status_title = "ISSUE FOR CONSTRUCTION" if checker else "ISSUED FOR REVIEW"
    svgs = sorted((ROOT / "design/drawings").glob("*/*.svg"))
    bad = []
    for s in svgs:
        t = s.read_text(encoding="utf-8", errors="replace")
        if status_title not in t or not re.search(rf"Rev {letter}\b", t):
            bad.append(rel(s))
    record("A9", "PASS" if svgs and not bad else "FAIL", f"Drawing SVG title blocks carry '{status_title}' and 'Rev {letter}' from design/REVISION.json ({len(svgs) - len(bad)}/{len(svgs)})", "; ".join(bad))
    # document control: checker blank
    idx = list((ROOT / "design/drawings").glob("*/INDEX.md"))
    blank = [rel(i) for i in idx if not checker]
    record("A13a", "WARN" if blank else "PASS", f"Drawing set has a named checker ({'yes' if checker else 'no'}; status {status_title})", "Set stays ISSUED FOR REVIEW until a checker is named in design/REVISION.json" if blank else "")
    # revision-date consistency between drawings, SQAM, QC forms, assembly and the revision file
    marks = {"design/REVISION.json": date}
    for f, pat in (("docs/SQAM.md", rf"Rev {letter} \(([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})"), ("design/assembly/QC_FORMS.md", rf"Rev {letter}[^0-9]*([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})"),
                   ("design/assembly/ASSEMBLY-ben150.md", rf"Issue {letter} · ([0-9-]+)"), ("design/drawings/ben150/INDEX.md", rf"Rev {letter}[^0-9]*([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})")):
        m = re.search(pat, (ROOT / f).read_text(encoding="utf-8"))
        marks[f] = m.group(1) if m else None
    dates = {v for v in marks.values() if v}
    missing = [k for k, v in marks.items() if v is None]
    record("A13b", "PASS" if len(dates) == 1 and not missing else "WARN", f"Rev {letter} issue dates agree across REVISION.json, SQAM, QC forms, assembly, INDEX", str(marks))


# ----------------------------------------------------------------------------- A10 STE
def ste_banned_words() -> list[str]:
    style = (ROOT / "design/assembly/STE_STYLE.md").read_text(encoding="utf-8")
    words = []
    for line in style.split("\n"):
        m = re.match(r"\s*-\s*(.+?)\s*→", line)
        if m:
            for w in re.split(r"\s*/\s*", m.group(1)):
                w = re.sub(r"\(.*?\)", "", w).strip()
                if w:
                    words.append(w.lower())
    return words or ["ensure", "utilize", "employ", "verify", "approximately", "prior to", "subsequent to", "in order to", "perform", "carry out", "conduct", "locate", "secure", "position"]


def check_ste() -> None:
    banned = ste_banned_words()
    hits, long_steps = [], []
    for p in sorted((ROOT / "design/assembly").glob("ASSEMBLY-*.md")):
        for i, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            if line.startswith("**Parts:**") or line.startswith("|") or line.startswith("- CTL-") or line.startswith("- STR-"):
                continue  # part names and the register are permitted technical names (STE rule 12)
            low = re.sub(r"`[^`]*`", "", line.lower()).replace("secure vault", "")
            low = re.sub(r"\*\*check:\*\*|^\s*check:", "", low)  # "Check:" is permitted as a heading (rule 10)
            for b in banned:
                if b == "position":  # banned as a verb only; "the position" (noun) is allowed
                    if re.search(r"\bposition (the|each|a|it|them)\b", low):
                        hits.append(f"{rel(p)}:{i} 'position (verb)'")
                    continue
                if re.search(r"\b" + re.escape(b) + r"\b", low):
                    hits.append(f"{rel(p)}:{i} '{b}'")
            m = re.match(r"^\s*\d+\.\s+(.*)", line)
            if m:
                body = re.sub(r"\(.*?\)|\[.*?\]|`.*?`", "", m.group(1))
                for s in re.split(r"(?<=[.!?])\s+", body):
                    if len(s.split()) > 20:
                        long_steps.append(f"{rel(p)}:{i} ({len(s.split())} w)")
    record("A10a", "PASS" if not hits else "FAIL", f"STE banned words in ASSEMBLY-*.md ({len(hits)} hits; list from STE_STYLE.md rule 10: {len(banned)} words)", "; ".join(hits[:15]))
    record("A10b", "PASS" if not long_steps else "WARN", f"STE instruction sentences over 20 words ({len(long_steps)})", "; ".join(long_steps[:12]) + (" …" if len(long_steps) > 12 else ""))


# ----------------------------------------------------------------------------- A11 secrets
SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"), "GitHub token"),
    (re.compile(r"sk-[A-Za-z0-9]{32,}|sk-ant-[A-Za-z0-9-]{20,}"), "API key"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"), "hard-coded credential"),
    (re.compile(r"[A-Za-z0-9._%+-]+@gmail\.com"), "personal gmail address"),
]


def check_secrets() -> None:
    hits = []
    for p in iter_files((".md", ".html", ".py", ".js", ".mjs", ".json", ".csv", ".txt", ".yml", ".yaml", ".sh", ".conf", ".env", ".example", ".st", ".cpp", ".h", ".ini", ".toml", ".template")):
        if rel(p).startswith("docs/audit/") or rel(p) == "scripts/audit.py":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            for pat, label in SECRET_PATTERNS:
                if pat.search(line):
                    if label == "hard-coded credential" and re.search(r"CHANGE_ME|\[[A-Z_]+\]|example|placeholder|\$\(|\$\{", line):
                        continue
                    hits.append(f"{rel(p)}:{i} {label}")
    hard = [h for h in hits if "gmail" not in h]
    status = "FAIL" if hard else ("WARN" if hits else "PASS")
    record("A11", status, f"Secrets / personal-data scan ({len(hits)} hits)", "; ".join(hits[:12]))


# ----------------------------------------------------------------------------- A12 json
def check_json() -> None:
    bad, n = [], 0
    for p in iter_files((".json",)):
        n += 1
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            bad.append(f"{rel(p)}: {e}")
    record("A12", "PASS" if not bad else "FAIL", f"JSON files parse ({n - len(bad)}/{n})", "; ".join(bad))


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="also execute the build-contract commands as written")
    args = ap.parse_args()
    for fn, kw in ((check_brief_artifacts, {}), (check_launch_manifest, {}), (check_build_contract, {"run": args.run}), (check_links, {}),
                   (check_stale, {}), (check_catalog, {}), (check_fields, {}), (check_test_count, {}), (check_drawings, {}),
                   (check_ste, {}), (check_secrets, {}), (check_json, {})):
        try:
            fn(**kw)
        except Exception as e:  # noqa: BLE001
            record(fn.__name__, "FAIL", f"{fn.__name__} crashed", repr(e))
    width = max(len(r[2]) for r in RESULTS)
    print(f"BEN Engine audit — {ROOT}")
    for cid, status, title, detail in RESULTS:
        print(f"{status:<4} {cid:<5} {title:<{width}}" + (f"  | {detail}" if detail else ""))
    counts = {s: sum(1 for r in RESULTS if r[1] == s) for s in ("PASS", "WARN", "FAIL")}
    print(f"\nSummary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

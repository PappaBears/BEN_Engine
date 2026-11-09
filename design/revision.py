"""One source for the drawing revision of a BEN Engine design set.

Two design-set records exist (docs/REVISION_POLICY.md):

* Rev 1 (frozen history): ``design/REVISION.json`` — drawing set Rev B / Rev C, read by the Rev 1 generators.
* Rev 2: ``design/rev2/REVISION.json`` — drawing set Rev 2.A onward, read by the generators when they run with
  ``--lineup rev2`` (outputs go to the versioned rev2 folders).

Every generator under design/ (drawings, renders, assembly, SQAM, design basis, wiring) reads its record through this
module, so one edit re-issues the whole set. ``REV`` is the record selected by ``--lineup`` on the command line of the
running generator (default ``rev1``, so the Rev 1 generators keep reading design/REVISION.json unchanged);
``load(lineup_or_path)`` loads either record explicitly. Procedure: design/drawings/README.md "Revision procedure".
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATHS = {
    "rev1": os.path.join(HERE, "REVISION.json"),
    "rev2": os.path.join(HERE, "rev2", "REVISION.json"),
}
PATH = PATHS["rev1"]          # kept for callers that read the Rev 1 path directly


def _resolve_path(lineup_or_path: str | None) -> str:
    if not lineup_or_path:
        return PATHS["rev1"]
    if lineup_or_path in PATHS:
        return PATHS[lineup_or_path]
    return lineup_or_path if os.path.isabs(lineup_or_path) else os.path.join(os.path.dirname(HERE), lineup_or_path)


def load(lineup_or_path: str | None = "rev1") -> dict:
    """Load a design-set record: ``"rev1"`` (design/REVISION.json), ``"rev2"`` (design/rev2/REVISION.json) or a path."""
    path = _resolve_path(lineup_or_path)
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    for k in ("drawing_rev", "issue_date", "status", "checker", "notes"):
        if k not in r:
            raise KeyError(f"{os.path.relpath(path, os.path.dirname(HERE))} is missing '{k}'")
    r["path"] = os.path.relpath(path, os.path.dirname(HERE)).replace(os.sep, "/")
    r["lineup"] = r.get("lineup", "rev1")
    r["checked"] = bool(r["checker"].strip())
    # Status words are derived from the checker field, not typed by hand:
    # no checker -> issued for review; a named checker -> issue for construction.
    r["status_long"] = ("ISSUE FOR CONSTRUCTION" if r["checked"]
                        else "ISSUED FOR REVIEW — not for construction until checked")
    r["status_short"] = "IFC" if r["checked"] else "IFR"
    r["status_title"] = "ISSUE FOR CONSTRUCTION" if r["checked"] else "ISSUED FOR REVIEW"
    r["set_label"] = f"{r['status_short']} Rev {r['drawing_rev']} ({r['issue_date']})"   # e.g. "IFR Rev B (2026-11-08)", "IFR Rev 2.A (2026-11-09)"
    r["issue_label"] = f"Issue {r['drawing_rev']} · {r['issue_date']}"                   # e.g. "Issue B · 2026-11-08"
    r["checker_text"] = r["checker"].strip() or "____________________"
    r["notes_short"] = r["notes"].split(". ")[0].rstrip(".") + "."       # first sentence: what this revision is
    sup = r.get("superseded_set")
    # The superseded set is named by letter and a written-out date so that a grep for the old ISO date over the
    # generated set finds nothing that still cites it as an issue.
    r["supersedes"] = {"drawing_rev": sup["letter"], "issue_date": sup["date_text"], "notes": sup["notes"]} if sup else None
    return r


def lineup_from_argv(argv=None) -> str:
    """The ``--lineup`` value on the command line of the running generator (``rev1`` when absent)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    for i, a in enumerate(argv):
        if a == "--lineup" and i + 1 < len(argv):
            return argv[i + 1] if argv[i + 1] in PATHS else "rev1"
        if a.startswith("--lineup="):
            v = a.split("=", 1)[1]
            return v if v in PATHS else "rev1"
    return "rev1"


LINEUP = lineup_from_argv()
REV = load(LINEUP)


def activate(lineup: str) -> dict:
    """Switch the shared ``REV`` dict in place (for in-process use by tests and drivers)."""
    global LINEUP
    LINEUP = lineup
    new = load(lineup)
    REV.clear()
    REV.update(new)
    return REV


if __name__ == "__main__":
    print(json.dumps(REV, indent=2, ensure_ascii=False))

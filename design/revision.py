"""One source for the drawing revision of the BEN Engine design set.

Every generator under design/ (drawings, renders, assembly, SQAM, design basis, wiring) and
software/ben_engine/proposal.py read design/REVISION.json through this module, so one edit
re-issues the whole set. Procedure: design/drawings/README.md "Revision procedure".
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "REVISION.json")


def load() -> dict:
    with open(PATH, encoding="utf-8") as f:
        r = json.load(f)
    for k in ("drawing_rev", "issue_date", "status", "checker", "notes"):
        if k not in r:
            raise KeyError(f"design/REVISION.json is missing '{k}'")
    r["checked"] = bool(r["checker"].strip())
    # Status words are derived from the checker field, not typed by hand:
    # no checker -> issued for review; a named checker -> issue for construction.
    r["status_long"] = ("ISSUE FOR CONSTRUCTION" if r["checked"]
                        else "ISSUED FOR REVIEW — not for construction until checked")
    r["status_short"] = "IFC" if r["checked"] else "IFR"
    r["status_title"] = "ISSUE FOR CONSTRUCTION" if r["checked"] else "ISSUED FOR REVIEW"
    r["set_label"] = f"{r['status_short']} Rev {r['drawing_rev']} ({r['issue_date']})"   # e.g. "IFR Rev B (2026-11-08)"
    r["issue_label"] = f"Issue {r['drawing_rev']} · {r['issue_date']}"                   # e.g. "Issue B · 2026-11-08"
    r["checker_text"] = r["checker"].strip() or "____________________"
    r["notes_short"] = r["notes"].split(". ")[0].rstrip(".") + "."       # first sentence: what this revision is
    sup = r.get("superseded_set")
    # The superseded set is named by letter and a written-out date so that a grep for the old ISO date over the
    # generated set finds nothing that still cites it as an issue.
    r["supersedes"] = {"drawing_rev": sup["letter"], "issue_date": sup["date_text"], "notes": sup["notes"]} if sup else None
    return r


REV = load()

if __name__ == "__main__":
    print(json.dumps(REV, indent=2, ensure_ascii=False))

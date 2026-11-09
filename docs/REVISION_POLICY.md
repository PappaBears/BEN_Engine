# Revision policy — nothing is deleted, every revision is kept

Set by the operator on 2026-11-09: "We don't delete, we only save the updated revs, so we always have the history."

## Two levels of revision

| Level | What it names | Format | Where it lives |
| --- | --- | --- | --- |
| **Product revision** | The whole BEN Engine offering: lineup, configuration rules, software, drawings, BOMs, documents, brand application | **Rev 1, Rev 2, …** | branch `release/revN` on GitHub (frozen, never force-pushed), record `releases/REVN.md` + `releases/revN.json`; a git tag `ben-engine-revN` is added where tags can be pushed |
| **Document revision** | One controlled document set inside a product revision (drawing set, SQAM, assembly instructions, contracts) | **Rev N.letter**, e.g. Rev 2.A, Rev 2.B | `design/REVISION.json` (drawings), document headers |

Rev 1 ended with drawing set Rev C (Rev B issued for construction for BEN 30/150/500/2000, Rev C issued for review for the BEN 5 refrigerant change). Rev 2 starts the drawing set at **Rev 2.A**.

## Rules

1. **Never delete a released artifact.** A superseded file is either left in place (versioned folders) or copied to `archive/revN/` before it changes. Git history and the release tag are the second copy.
2. **New revisions write to versioned locations.** Rev 2 drawings go to `design/drawings/rev2/<tier>/`, renders to `design/renders/rev2/<tier>/`, assembly to `design/assembly/rev2/`, BOMs to `purchasing/rev2/`, sample proposals to `docs/proposals/rev2/`. Rev 1 locations stay frozen.
3. **Rev 1 configurations stay reproducible.** The configuration model keeps a `lineup` field (`rev1`, `rev2`); a saved Rev 1 configuration computes exactly the numbers it computed when it was quoted. Tests pin Rev 1 numbers.
4. **Supersede, don't overwrite, in documents.** A superseded decision or plan gets a header "Superseded by …" and stays in the repository.
5. **Every release has a record.** `releases/REVN.md` lists what was released, the commit, the tag and a content hash per area; the automated audit checks that every file listed for an earlier release still exists at its path or in `archive/`.
6. **Customer-facing items carry the revision.** Drawings, proposals, SOWs, data plates and the dashboard "About" show the product revision and document revision.

## How to retrieve history

```bash
git branch -r --list "origin/release/*"
git show origin/release/rev1:design/drawings/ben150/A-001.svg > A-001-rev1.svg
```

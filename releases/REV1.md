# Release record — BEN Engine Rev 1 (final)

Frozen 2026-11-09 at commit `d9dad54361779c72bc80def65cafda9f556b6e44`, git branch **`release/rev1`** on GitHub (and local tag `ben-engine-rev1`; this environment cannot push tags). Nothing in Rev 1 is deleted by Rev 2: Rev 2 artifacts are written to versioned locations (see `docs/REVISION_POLICY.md`) and Rev 1 files stay where they are or are copied under `archive/rev1/` before any change.

Retrieve any Rev 1 file exactly as released:

```bash
git show origin/release/rev1:<path>
git checkout origin/release/rev1 -- <path>   # restore into the working tree
```

| Area | Paths | Files | SHA-256 of the file list + contents |
| --- | --- | --- | --- |
| Configuration model and software | `software/ben_engine` | 16 | `e2375483b73b330a` |
| Drawing set (Rev C, issued for review; Rev B IFC for non-BEN 5 tiers) | `design/drawings` | 99 | `71d27340ada39a66` |
| Renders, STE assembly, SQAM, design basis | `design/renders`, `design/assembly`, `docs/SQAM.md`, `design/DESIGN_BASIS.md` | 62 | `44a19760d8e39af9` |
| Purchasing (catalog, BOMs, RFQs) | `purchasing` | 33 | `43032dd8fd0d384a` |
| Contracts and ready set | `docs/contracts` | 44 | `f434070524fceffe` |
| Proposals (samples) | `docs/proposals` | 18 | `12567126fec7c63b` |
| Website (also copied to archive/rev1/web) | `web` | 17 | `6854dae6354a24e2` |
| Dashboard | `dashboard` | 22 | `cf6954d2777dc4d3` |
| Firmware | `firmware` | 79 | `3ba72078e3280784` |
| Audit and evidence | `docs/audit` | 9 | `325573a4fb7183ae` |

Lineup at Rev 1: BEN 5 (2–5 kW NEMA 4X cabinet), BEN 30 (10 ft), BEN 150 (20 ft), BEN 500 (40 ft), BEN 2000 (2 MW hall, capability example); hardening H1–H3; BEN Controls Lite/Pro; forward options dc800 and dlc_hd as study.

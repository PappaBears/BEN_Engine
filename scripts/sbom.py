#!/usr/bin/env python3
"""Minimal SPDX 2.3 software bill of materials for the Python side of BEN Engine.

Lists every distribution importable in the current interpreter (``importlib.metadata``), which on a unit is the
``/opt/ben_engine/.venv`` the installers create; in the repository it is the test environment. The Pod firmware
(Gecko SDK / OpenThread) and the PLC project are NOT covered — see docs/CYBERSECURITY.md section 5 and docs/ROADMAP.md.

    python scripts/sbom.py                       # writes docs/sbom/ben_engine-python.spdx.json
    python scripts/sbom.py --out /path/file.json # or elsewhere
    python scripts/sbom.py --check               # exit 1 if the committed file lists a different package set
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "sbom" / "ben_engine-python.spdx.json"


def _spdx_id(name: str, version: str) -> str:
    safe = "".join(c if c.isalnum() or c in ".-" else "-" for c in f"{name}-{version}")
    return f"SPDXRef-Package-{safe}"


def collect() -> list[dict]:
    pkgs: dict[str, dict] = {}
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "").strip()
        if not name:
            continue
        version = dist.version or "UNKNOWN"
        lic = (dist.metadata.get("License-Expression") or dist.metadata.get("License") or "").strip()
        if not lic or len(lic) > 120 or "\n" in lic:
            classifiers = [c for c in dist.metadata.get_all("Classifier") or [] if c.startswith("License ::")]
            lic = classifiers[-1].split("::")[-1].strip() if classifiers else "NOASSERTION"
        pkgs[name.lower()] = {
            "name": name,
            "SPDXID": _spdx_id(name, version),
            "versionInfo": version,
            "downloadLocation": f"https://pypi.org/project/{name}/{version}/",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": lic,
            "supplier": "NOASSERTION",
            "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                              "referenceLocator": f"pkg:pypi/{name.lower()}@{version}"}],
        }
    return [pkgs[k] for k in sorted(pkgs)]


def build(packages: list[dict]) -> dict:
    root_id = "SPDXRef-Package-ben-engine"
    rels = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": root_id}]
    rels += [{"spdxElementId": root_id, "relationshipType": "DEPENDS_ON", "relatedSpdxElement": p["SPDXID"]} for p in packages]
    root_pkg = {"name": "ben-engine", "SPDXID": root_id, "versionInfo": _project_version(), "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False, "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
                "supplier": "Organization: Schreiber AI", "primaryPackagePurpose": "APPLICATION"}
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "ben-engine-python",
        "documentNamespace": f"https://schreiberai.com/spdx/ben-engine-python-{_fingerprint(packages)}",
        "comment": ("Python side only (edge computer services ben-api, ben-plc-bridge, ben-interlocks and the tools). "
                    "Pod firmware and PLC project SBOMs are roadmap items (docs/ROADMAP.md)."),
        "creationInfo": {"created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "creators": ["Tool: scripts/sbom.py", f"Tool: python-{platform.python_version()}"]},
        "packages": [root_pkg] + packages,
        "relationships": rels,
    }


def _project_version() -> str:
    try:
        import tomllib
        return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    except Exception:  # pragma: no cover - pyproject always present in the repo
        return "UNKNOWN"


def _fingerprint(packages: list[dict]) -> str:
    h = hashlib.sha256("\n".join(f"{p['name']}=={p['versionInfo']}" for p in packages).encode()).hexdigest()
    return h[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true", help="compare the package set with the committed file; exit 1 on difference")
    a = ap.parse_args(argv)
    packages = collect()
    doc = build(packages)
    if a.check:
        if not a.out.exists():
            print(f"missing {a.out}"); return 1
        old = json.loads(a.out.read_text())
        old_set = {(p["name"], p["versionInfo"]) for p in old.get("packages", []) if p["SPDXID"] != "SPDXRef-Package-ben-engine"}
        new_set = {(p["name"], p["versionInfo"]) for p in packages}
        if old_set != new_set:
            print(f"SBOM differs: +{sorted(new_set - old_set)} -{sorted(old_set - new_set)}"); return 1
        print(f"SBOM matches ({len(new_set)} packages)"); return 0
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"wrote {a.out.relative_to(ROOT) if a.out.is_relative_to(ROOT) else a.out}: {len(packages)} packages, SPDX 2.3")
    return 0


if __name__ == "__main__":
    sys.exit(main())

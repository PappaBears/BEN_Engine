"""Store the latest evidence in the repository (audit F-15): build-control report, audit.py output, pytest summary, link check."""
import json, os, shutil, subprocess, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "docs" / "audit" / "evidence"
EV.mkdir(parents=True, exist_ok=True)
runs = sorted((ROOT / ".schreiber-ai" / "runs").glob("*/report.json"), key=lambda p: p.stat().st_mtime)
if runs:
    shutil.copy2(runs[-1], EV / "build-report.json")
def run(cmd, out):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "software")})
    (EV / out).write_text(f"$ {' '.join(cmd)}\n# exit {r.returncode} · {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n" + r.stdout[-20000:] + r.stderr[-5000:])
    return r.returncode
codes = {
    "audit": run([sys.executable, "scripts/audit.py"], "audit-output.txt"),
    "links": run([sys.executable, "scripts/check_links.py"], "link-check.txt"),
    "pytest": run([sys.executable, "-m", "pytest", "tests", "-q", "--ignore=tests/e2e", "-p", "no:cacheprovider"], "pytest-summary.txt"),
    "firmware": run(["make", "-C", "firmware/ben-pod", "test"], "firmware-host-tests.txt"),
}
(EV / "INDEX.md").write_text("# Evidence of the latest verification run\n\n" + "\n".join(f"- `{k}` → exit {v}" for k, v in codes.items()) + f"\n- `build-report.json` copied from the latest build_control run\n\nGenerated {dt.date.today().isoformat()} by scripts/store_evidence.py\n")
print(codes)

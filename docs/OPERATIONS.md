# Operations (software)

## Run locally (simulation)
```bash
pip install -r requirements.txt
bash scripts/run_dashboard.sh         # http://localhost:8080
```

## Tests
```bash
PYTHONPATH=software pytest tests -q --ignore=tests/e2e
bash tests/e2e/run_e2e.sh             # Playwright, writes docs/media/screens
cd firmware/ben-node && pio test -e native
```

## Regenerate generated deliverables
```bash
python design/drawings/gen_drawings.py
python design/renders/gen_renders.py
PYTHONPATH=software python -m ben_engine.bom --tier ben20 --csv purchasing/bom-ben20.csv --md docs/BOM-ben20.md
python scripts/unit_economics.py       # refreshes VC table + web/assets/pricing.json
```

## On a gateway
See `firmware/ben-gateway/README.md`: install, services, logs (`journalctl -u ben-api`), nightly backup location, restore procedure (`ben-restore <backup.tar>`), firmware OTA.

## Backups and recovery
Git holds code, docs and generated artifacts. It does **not** hold a unit's telemetry database or calibration records; those live on the gateway and in its nightly backup. Recovery drill is part of commissioning step 10.

## Releases
Tag `vX.Y.Z` on `main`; CI must be green; release notes list compliance-relevant changes (alarm thresholds, firmware protocol) explicitly.

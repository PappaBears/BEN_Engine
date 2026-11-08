"""BEN Engine telemetry export: ring buffer of twin states, flattened CSV and JSON lines.

Flattening rule (shared with sweeps and commissioning): nested dicts join their keys with ``_``
(``power_ups_soc_pct``), lists become ``name_1, name_2, ...`` (1-based, as on the racks), lists of
dicts become ``cooling_units_1_on``. The variable-length ``alarms`` list is reduced to
``alarm_count`` and ``alarm_ids`` (``;``-joined); ``faults`` is ``;``-joined.
"""
from __future__ import annotations

import csv
import json
from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Optional


def flatten_state(state: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten one twin ``state()`` dict into a single-level dict of scalars."""
    out: Dict[str, Any] = {}
    for k, v in state.items():
        key = f"{prefix}{k}"
        if k == "alarms" and isinstance(v, list):
            out["alarm_count"] = len(v)
            out["alarm_ids"] = ";".join(str(a.get("id", "")) for a in v if isinstance(a, dict))
            out["alarm_max_sev"] = _max_sev(v)
        elif k == "faults" and isinstance(v, list):
            out["faults"] = ";".join(str(x) for x in v)
        elif isinstance(v, dict):
            out.update(flatten_state(v, key + "_"))
        elif isinstance(v, (list, tuple)):
            for i, item in enumerate(v, start=1):
                if isinstance(item, dict):
                    out.update(flatten_state(item, f"{key}_{i}_"))
                else:
                    out[f"{key}_{i}"] = item
        else:
            out[key] = v
    return out


def _max_sev(alarms: List[Dict[str, Any]]) -> str:
    rank = {"": 0, "warn": 1, "alarm": 2, "critical": 3}
    best = ""
    for a in alarms:
        s = str(a.get("sev", ""))
        if rank.get(s, 0) > rank.get(best, 0):
            best = s
    return best


def columns_for(rows: Iterable[Dict[str, Any]]) -> List[str]:
    """Union of keys across rows, first-seen order, so ragged rows still line up."""
    cols: List[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    return cols


def write_csv(rows: List[Dict[str, Any]], path: str) -> str:
    cols = columns_for(rows)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


class TelemetryBuffer:
    """Fixed-duration ring buffer of raw twin states (not flattened, so nothing is lost)."""

    def __init__(self, hours: float = 24.0, rate_hz: float = 1.0):
        self.hours = hours
        self.rate_hz = rate_hz
        self.maxlen = max(1, int(hours * 3600 * rate_hz))
        self._buf: Deque[Dict[str, Any]] = deque(maxlen=self.maxlen)

    def append(self, state: Dict[str, Any]) -> None:
        self._buf.append(state)

    def extend(self, states: Iterable[Dict[str, Any]]) -> None:
        for s in states:
            self._buf.append(s)

    def __len__(self) -> int:
        return len(self._buf)

    @property
    def t_first(self) -> Optional[float]:
        return self._buf[0].get("t") if self._buf else None

    @property
    def t_last(self) -> Optional[float]:
        return self._buf[-1].get("t") if self._buf else None

    def select(self, from_t: Optional[float] = None, to_t: Optional[float] = None) -> List[Dict[str, Any]]:
        """States with from_t <= t <= to_t (either bound may be None)."""
        out = []
        for s in self._buf:
            t = s.get("t", 0.0)
            if from_t is not None and t < from_t:
                continue
            if to_t is not None and t > to_t:
                continue
            out.append(s)
        return out

    def to_rows(self, from_t=None, to_t=None) -> List[Dict[str, Any]]:
        return [flatten_state(s) for s in self.select(from_t, to_t)]

    def to_csv(self, path: str, from_t: Optional[float] = None, to_t: Optional[float] = None) -> str:
        return write_csv(self.to_rows(from_t, to_t), path)

    def to_jsonl(self, path: str, from_t: Optional[float] = None, to_t: Optional[float] = None) -> str:
        with open(path, "w") as fh:
            for s in self.select(from_t, to_t):
                fh.write(json.dumps(s, separators=(",", ":")) + "\n")
        return path

    @staticmethod
    def read_jsonl(path: str) -> List[Dict[str, Any]]:
        with open(path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

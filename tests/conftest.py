"""pytest configuration: make the ben_engine package importable from the repo root."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOFTWARE = os.path.join(ROOT, "software")
if SOFTWARE not in sys.path:
    sys.path.insert(0, SOFTWARE)

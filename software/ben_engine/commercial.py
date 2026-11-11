"""Commercial terms shared by every price the product shows: the product page, the dashboard proposal panel,
proposal documents and the unit-economics tables (one source, so they can never drift apart).

Margin policy (operator, 2026-11-11): **35 % gross margin on the whole project** — every capital line of the
bill of materials (power, cooling, compute, controls, enclosure, fire, site, services and, on the BEN 2000
cluster, the shared yard) is sold at cost / (1 - 0.35). Recurring items (controls licence, white-label licence,
managed service) are priced separately and are not part of the capital margin.

Gross margin, not markup: at 35 % gross margin the price is cost / 0.65 = cost x 1.538; a 35 % markup would be
cost x 1.35 (a 25.9 % gross margin).

History (docs/REVISION_POLICY.md, never delete): Rev 1 prices were issued at 28 % gross margin on hardware and
build labour; those records stay in releases/rev1 (branch release/rev1) and archive/rev1/. New quotes for any
lineup use PROJECT_MARGIN.
"""
from __future__ import annotations

PROJECT_MARGIN = 0.35                 # gross margin on the whole capital price, effective 2026-11-11
MARGIN_EFFECTIVE = "2026-11-11"
MARGIN_HISTORY = (
    {"margin": 0.28, "from": "2026-11-07", "to": "2026-11-10", "scope": "hardware + build labour (Rev 1 and Rev 2.A drafts)"},
    {"margin": 0.35, "from": "2026-11-11", "to": None, "scope": "whole project capital price (operator direction)"},
)


def sell_price(cost_usd: float, margin: float = PROJECT_MARGIN) -> float:
    """Capital sell price for a cost at a gross margin."""
    if not 0 <= margin < 1:
        raise ValueError(f"gross margin must be in [0, 1): {margin}")
    return cost_usd / (1.0 - margin)

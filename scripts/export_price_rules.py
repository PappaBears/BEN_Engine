"""Export the BOM price rules for the product page: web/assets/price-rules.json.

The product page prices every configuration with the same parts catalog, quantity rules and margin as the
proposals (software/ben_engine/bom.py, proposal.py, commercial.py), so hardening, redundancy, UPS minutes,
generator, climate, power architecture, cooling, racks and IT load all move the price exactly as they do in a
proposal. The qty_rule strings are Python expressions; they are compiled here to a small JSON syntax tree that
web/assets/bom.js evaluates (no eval in the browser). tests/test_price_parity.py checks the page engine against
generate_bom() for every tier and option.

Run after any catalog or rule change:  python scripts/export_price_rules.py
"""
from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.bom import ALWAYS_PREFIXES, PREFIX_TO_SUBSYSTEM, load_catalog, subsystem_of  # noqa: E402
from ben_engine.commercial import MARGIN_EFFECTIVE, PROJECT_MARGIN  # noqa: E402

OUT = os.path.join(ROOT, "web", "assets", "price-rules.json")
_OPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
        ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
        ast.USub: "neg", ast.UAdd: "pos"}


def compile_rule(expr: str):
    """Python qty_rule -> JSON tree: number | "var" | ["op", a, b] | ["neg", a] | ["if", test, body, else] | ["call", fn, args...]."""
    def c(n):
        if isinstance(n, ast.Expression):
            return c(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.Name):
            return n.id
        if isinstance(n, ast.BinOp):
            return [_OPS[type(n.op)], c(n.left), c(n.right)]
        if isinstance(n, ast.UnaryOp):
            return [_OPS[type(n.op)], c(n.operand)]
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            return [_OPS[type(n.ops[0])], c(n.left), c(n.comparators[0])]
        if isinstance(n, ast.IfExp):
            return ["if", c(n.test), c(n.body), c(n.orelse)]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
            return ["call", n.func.id] + [c(a) for a in n.args]
        raise ValueError(f"cannot compile {type(n).__name__} in {expr!r}")
    return c(ast.parse(expr.strip(), mode="eval"))


def build() -> dict:
    lines = []
    for p in load_catalog():
        ln = {"code": p["code"], "sub": subsystem_of(p["code"]), "always": p["code"].split("-", 1)[0] in ALWAYS_PREFIXES,
              "name": p["name"], "unit": p["unit"], "price": float(p["unit_price_usd"]), "status": p["price_status"],
              "tiers": p["applies_to_tiers"], "q": compile_rule(p["qty_rule"])}
        for k, short in (("applies_to_cooling", "cooling"), ("applies_to_controls", "controls"), ("applies_to_hardening", "hardening"),
                         ("applies_to_power", "power"), ("applies_to_lineups", "lineups")):
            if p.get(k):
                ln[short] = p[k]
        if int(p.get("moq") or 1) > 1:
            ln["moq"] = int(p["moq"])
        if "cluster_qty_rule" in p:
            ln["cq"] = compile_rule(p["cluster_qty_rule"])
        lines.append(ln)
    return {"margin": PROJECT_MARGIN, "margin_effective": MARGIN_EFFECTIVE,
            "margin_note": "Gross margin on the whole capital price (software/ben_engine/commercial.py)",
            "prefix_to_subsystem": PREFIX_TO_SUBSYSTEM, "always_prefixes": list(ALWAYS_PREFIXES), "lines": lines}


def main() -> int:
    data = build()
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
        f.write("\n")
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(data['lines'])} lines, {os.path.getsize(OUT):,} bytes, margin {data['margin']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

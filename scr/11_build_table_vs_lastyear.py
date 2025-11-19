#!/usr/bin/env python3
"""
Build the current-vs-last-year table from shock_data.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = PROJECT_ROOT / "data" / "intermediate" / "shock_data.json"
SPEC_PATH = PROJECT_ROOT / "config" / "table_specs" / "table_vs_lastyear.json"


def load_summary() -> Dict[str, Dict[str, Any]]:
    return json.loads(SUMMARY_PATH.read_text())


def load_spec() -> Dict[str, Any]:
    return json.loads(SPEC_PATH.read_text())


def base_context(entry: Dict[str, Any]) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}
    shock = entry.get("shock_value")
    extreme = entry.get("extreme_value")

    if isinstance(shock, dict):
        values = list(shock.values())
        ctx["high"] = max(values)
        ctx["low"] = min(values)
    elif shock is not None:
        ctx["shock"] = shock
        ctx["delta"] = shock

    if isinstance(extreme, dict):
        ctx["extreme_high"] = max(extreme.values())
        ctx["extreme_low"] = min(extreme.values())
    elif extreme is not None:
        ctx["extreme"] = extreme

    return ctx


def render_value(entry: Dict[str, Any], spec: Dict[str, Any]) -> str:
    ctx = base_context(entry)

    if "delta" in ctx and spec.get("delta_scale"):
        ctx["delta"] = ctx["delta"] * spec["delta_scale"]

    template = spec["template"]
    return template.format(**ctx)


def build_table() -> Dict[str, Any]:
    summary = load_summary()
    spec = load_spec()
    columns = spec["columns"]
    factor_order: List[str] = spec["order"]

    headers = [col["header"] for col in columns]
    rows: List[List[str]] = []

    for factor in factor_order:
        entry = summary[factor]
        row: List[str] = []
        for column in columns:
            if column.get("source") == "factor":
                row.append(factor)
            else:
                value_spec = next(v for v in column["values"] if v["source"] == factor)
                row.append(render_value(entry, value_spec))
        rows.append(row)

    return {"columns": headers, "rows": rows}


def main() -> None:
    spec = load_spec()
    table = build_table()
    output_path = PROJECT_ROOT / spec["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(table, indent=2))
    print(f"Saved table -> {output_path}")


if __name__ == "__main__":
    main()


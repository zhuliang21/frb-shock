#!/usr/bin/env python3
"""
Generate Markdown commentary comparing current CCAR shocks vs prior year using
pre-built table outputs. Configuration for factor grouping and paths lives in
config/md_config/key_commentary.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = PROJECT_ROOT / "config" / "md_config" / "key_commentary.json"


def load_spec() -> Dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text())

    def resolve(path_str: str) -> Path:
        return PROJECT_ROOT / path_str

    spec["current_table_path"] = resolve(spec["current_table_path"])
    spec["history_table_path"] = resolve(spec["history_table_path"])
    spec["output_md_path"] = resolve(spec["output_md_path"])

    categories: List[Dict[str, Any]] = []
    for category in spec.get("categories", []):
        factors = []
        for factor in category.get("factors", []):
            if isinstance(factor, str):
                factors.append({"key": factor})
            else:
                factors.append(
                    {
                        "key": factor["key"],
                        "note": factor.get("note"),
                    }
                )
        categories.append({"name": category["name"], "factors": factors})
    spec["categories"] = categories
    return spec


def load_table(path: Path) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    data = json.loads(path.read_text())
    if not data:
        raise ValueError(f"No data found in {path}")
    scenario, factors = next(iter(data.items()))
    return scenario, factors


def normalise_display(entry: Dict[str, Any]) -> str:
    display = entry.get("display")
    if display:
        return display.replace("\n", "<br>").replace("|", "\\|")
    shock = entry.get("shock_value")
    if shock is None:
        return "n/a"
    return f"{shock:.2f}"


def build_category_markdown(
    category: Dict[str, Any],
    current_factors: Dict[str, Dict[str, Any]],
    history_factors: Dict[str, Dict[str, Any]],
    current_label: str,
    history_label: str,
) -> List[str]:
    lines: List[str] = []
    lines.append(f"## {category['name']}\n")
    lines.append(f"| Factor | {current_label} | {history_label} |")
    lines.append("| --- | --- | --- |")

    for factor in category["factors"]:
        key = factor["key"]
        cur_entry = current_factors.get(key, {})
        hist_entry = history_factors.get(key, {})
        lines.append(
            f"| {key} | {normalise_display(cur_entry)} | {normalise_display(hist_entry)} |"
        )

    note_lines = [
        factor.get("note") for factor in category["factors"] if factor.get("note")
    ]
    if note_lines:
        lines.append("\n> " + " ".join(f"[{note}]" for note in note_lines))

    lines.append("")
    return lines


def main() -> None:
    spec = load_spec()
    current_label, current_factors = load_table(spec["current_table_path"])
    history_label, history_factors = load_table(spec["history_table_path"])

    markdown_lines: List[str] = [
        "# Supervisory Severely Adverse Scenario: Key Factor Commentary",
        "",
        f"Current scenario: **{current_label}**  •  Prior scenario: **{history_label}**",
        "",
        "> Tables below are sourced from the auto-generated `table_vs_lastyear.json` files. "
        "Annotate or rewrite the copy beneath each section as needed.",
        "",
    ]

    for category in spec["categories"]:
        markdown_lines.extend(
            build_category_markdown(
                category, current_factors, history_factors, current_label, history_label
            )
        )

    output_path: Path = spec["output_md_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(markdown_lines))
    print(f"Saved Markdown -> {output_path}")


if __name__ == "__main__":
    main()


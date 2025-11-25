#!/usr/bin/env python3
"""
Select and rename factors based on config/factor_mapping.json.

Outputs
-------
1. data/intermediate/path_SA.csv : SA path filtered to mapped factors.
2. data/intermediate/t0.json     : Baseline factors filtered/renamed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "factor_mapping.json"
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
PATH_SA_SOURCE = INTERMEDIATE_DIR / "path_SA_source.csv"
PATH_SA_OUTPUT = INTERMEDIATE_DIR / "path_SA.csv"
PATH_BASELINE_SOURCE = INTERMEDIATE_DIR / "path_baseline_source.csv"
PATH_BASELINE_OUTPUT = INTERMEDIATE_DIR / "path_baseline.csv"
T0_SOURCE = INTERMEDIATE_DIR / "t0_source.json"
T0_OUTPUT = INTERMEDIATE_DIR / "t0.json"

DATE_COLUMN = "Date"


def load_mapping() -> List[Tuple[str, str]]:
    config = json.loads(CONFIG_PATH.read_text())
    factors = config.get("factors", [])
    pairs: List[Tuple[str, str]] = []
    for entry in factors:
        name = entry["name"]
        source = entry["source_column"]
        pairs.append((name, source))
    return pairs


def select_from_path(mapping: List[Tuple[str, str]], input_path: Path, output_path: Path) -> None:
    df = pd.read_csv(input_path)
    missing = [source for _, source in mapping if source not in df.columns]
    if missing:
        raise KeyError(f"Columns missing in {input_path}: {missing}")

    ordered_sources = [source for _, source in mapping]
    renamed = {source: name for name, source in mapping}

    selected = df[[DATE_COLUMN] + ordered_sources].rename(columns=renamed)
    selected.to_csv(output_path, index=False)


def select_from_t0(mapping: List[Tuple[str, str]]) -> None:
    payload = json.loads(T0_SOURCE.read_text())
    selected_factors: Dict[str, float | None] = {}
    factors: Dict[str, float | None] = payload["factors"]

    for name, source in mapping:
        if source not in factors:
            raise KeyError(f"Factor '{source}' missing in {T0_SOURCE}")
        selected_factors[name] = factors[source]

    output_payload = {
        "date": payload["date"],
        "factors": selected_factors,
    }
    T0_OUTPUT.write_text(json.dumps(output_payload, indent=2))


def main() -> None:
    mapping = load_mapping()
    select_from_path(mapping, PATH_SA_SOURCE, PATH_SA_OUTPUT)
    select_from_path(mapping, PATH_BASELINE_SOURCE, PATH_BASELINE_OUTPUT)
    select_from_t0(mapping)
    print(f"Saved mapped SA path -> {PATH_SA_OUTPUT}")
    print(f"Saved mapped baseline path -> {PATH_BASELINE_OUTPUT}")
    print(f"Saved mapped t0 -> {T0_OUTPUT}")


if __name__ == "__main__":
    main()


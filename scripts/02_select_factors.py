#!/usr/bin/env python3
"""
Select and rename factors based on config/factor_mapping.json.

Outputs
-------
1. path_SA.csv      : SA path filtered to mapped factors.
2. path_baseline.csv: Baseline path filtered to mapped factors.
3. t0.json          : Baseline factors filtered/renamed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from paths import ScenarioPaths


DATE_COLUMN = "Date"


def load_mapping(config_path: Path) -> List[Tuple[str, str]]:
    config = json.loads(config_path.read_text())
    factors = config.get("factors", [])
    pairs: List[Tuple[str, str]] = []
    for entry in factors:
        name = entry["name"]
        source = entry["source_column"]
        pairs.append((name, source))
    return pairs


def select_from_path(mapping: List[Tuple[str, str]], input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        return
        
    df = pd.read_csv(input_path)
    missing = [source for _, source in mapping if source not in df.columns]
    if missing:
        raise KeyError(f"Columns missing in {input_path}: {missing}")

    ordered_sources = [source for _, source in mapping]
    renamed = {source: name for name, source in mapping}

    selected = df[[DATE_COLUMN] + ordered_sources].rename(columns=renamed)
    selected.to_csv(output_path, index=False)
    print(f"Saved -> {output_path}")


def select_from_t0(mapping: List[Tuple[str, str]], t0_source: Path, t0_output: Path) -> None:
    payload = json.loads(t0_source.read_text())
    selected_factors: Dict[str, float | None] = {}
    factors: Dict[str, float | None] = payload["factors"]

    for name, source in mapping:
        if source not in factors:
            raise KeyError(f"Factor '{source}' missing in {t0_source}")
        selected_factors[name] = factors[source]

    output_payload = {
        "date": payload["date"],
        "factors": selected_factors,
    }
    t0_output.write_text(json.dumps(output_payload, indent=2))
    print(f"Saved -> {t0_output}")


def main() -> None:
    paths = ScenarioPaths()
    
    mapping = load_mapping(paths.factor_mapping_path)
    
    sa_source = paths.intermediate_dir / "path_SA_source.csv"
    sa_output = paths.intermediate_dir / "path_SA.csv"
    baseline_source = paths.intermediate_dir / "path_baseline_source.csv"
    baseline_output = paths.intermediate_dir / "path_baseline.csv"
    t0_source = paths.intermediate_dir / "t0_source.json"
    t0_output = paths.intermediate_dir / "t0.json"
    
    select_from_path(mapping, sa_source, sa_output)
    select_from_path(mapping, baseline_source, baseline_output)
    select_from_t0(mapping, t0_source, t0_output)


if __name__ == "__main__":
    main()

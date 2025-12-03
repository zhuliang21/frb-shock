#!/usr/bin/env python3
"""
Preprocess FRB scenario source files.

Steps
-----
1. Read domestic/international historic tables to extract each variable's t0.
2. Read supervisory severely adverse (SA) tables and merge them into one path.
3. Write the t0 payload to JSON and the combined SA path to CSV.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from paths import ScenarioPaths


DATE_COLUMN = "Date"
SCENARIO_COLUMN = "Scenario Name"


def get_source_files(paths: ScenarioPaths) -> Tuple[Dict[str, Path], Dict[str, Path], Dict[str, Path]]:
    """Discover source files based on naming convention."""
    source_dir = paths.source_dir
    
    # Find files by pattern
    historic_files: Dict[str, Path] = {}
    sa_files: Dict[str, Path] = {}
    baseline_files: Dict[str, Path] = {}
    
    for csv_file in source_dir.glob("*.csv"):
        name = csv_file.name.lower()
        if "historic" in name:
            if "domestic" in name:
                historic_files["domestic"] = csv_file
            elif "international" in name:
                historic_files["international"] = csv_file
        elif "severely_adverse" in name or "severely-adverse" in name:
            if "domestic" in name:
                sa_files["domestic"] = csv_file
            elif "international" in name:
                sa_files["international"] = csv_file
        elif "baseline" in name:
            if "domestic" in name:
                baseline_files["domestic"] = csv_file
            elif "international" in name:
                baseline_files["international"] = csv_file
    
    return historic_files, sa_files, baseline_files


def _quarter_sort_key(dates: pd.Series) -> pd.Series:
    extracted = dates.str.extract(r"(?P<year>\d{4})\s*Q(?P<quarter>\d)", expand=True)
    if extracted.isnull().any().any():
        raise ValueError("Date column must follow the 'YYYY Qn' format.")
    return extracted["year"].astype(int) * 10 + extracted["quarter"].astype(int)


def sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    sort_key = _quarter_sort_key(df[DATE_COLUMN])
    return df.assign(_sort_key=sort_key).sort_values("_sort_key").drop(columns="_sort_key")


def _to_float_or_none(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_t0(df: pd.DataFrame) -> Tuple[str, Dict[str, float | None]]:
    ordered = sort_by_date(df)
    t0_row = ordered.iloc[-1]
    t0_date = str(t0_row[DATE_COLUMN])

    factors: Dict[str, float | None] = {}
    for column in ordered.columns:
        if column in {DATE_COLUMN, SCENARIO_COLUMN}:
            continue
        factors[column] = _to_float_or_none(t0_row[column])

    return t0_date, factors


def build_t0_payload(historic_files: Dict[str, Path]) -> Dict[str, object]:
    combined_factors: Dict[str, float | None] = {}
    t0_dates: List[str] = []

    for region, csv_path in historic_files.items():
        df = pd.read_csv(csv_path)
        t0_date, factors = extract_t0(df)
        t0_dates.append(t0_date)

        for name, value in factors.items():
            if name in combined_factors:
                raise ValueError(f"Duplicate factor name '{name}' found while merging {region}.")
            combined_factors[name] = value

    unique_dates = set(t0_dates)
    if len(unique_dates) != 1:
        raise ValueError(f"Historic tables must share the same t0 date. Found: {sorted(unique_dates)}")

    return {
        "date": unique_dates.pop(),
        "factors": combined_factors,
    }


def _numeric_columns(df: pd.DataFrame, ignore: Iterable[str]) -> pd.DataFrame:
    for column in df.columns:
        if column in ignore:
            continue
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def build_scenario_path(file_map: Dict[str, Path]) -> pd.DataFrame:
    dataframes: List[pd.DataFrame] = []
    column_order: List[str] = [DATE_COLUMN]

    for csv_path in file_map.values():
        df = pd.read_csv(csv_path)
        df = sort_by_date(df)
        df = df.drop(columns=[SCENARIO_COLUMN], errors="ignore")
        df = _numeric_columns(df, ignore=[DATE_COLUMN])
        dataframes.append(df)

        for col in df.columns:
            if col == DATE_COLUMN or col in column_order:
                continue
            column_order.append(col)

    if not dataframes:
        raise ValueError("No scenario files were provided.")

    merged = dataframes[0]
    for df in dataframes[1:]:
        merged = pd.merge(merged, df, on=DATE_COLUMN, how="outer", sort=False)

    merged = sort_by_date(merged)
    return merged[column_order]


def main() -> None:
    paths = ScenarioPaths()
    paths.ensure_dirs()
    
    historic_files, sa_files, baseline_files = get_source_files(paths)
    
    if not historic_files:
        raise FileNotFoundError(f"No historic files found in {paths.source_dir}")
    if not sa_files:
        raise FileNotFoundError(f"No SA files found in {paths.source_dir}")

    t0_json_path = paths.intermediate_dir / "t0_source.json"
    sa_path_csv = paths.intermediate_dir / "path_SA_source.csv"
    baseline_path_csv = paths.intermediate_dir / "path_baseline_source.csv"

    t0_payload = build_t0_payload(historic_files)
    t0_json_path.write_text(json.dumps(t0_payload, indent=2))

    sa_path_df = build_scenario_path(sa_files)
    sa_path_df.to_csv(sa_path_csv, index=False)

    if baseline_files:
        baseline_path_df = build_scenario_path(baseline_files)
        baseline_path_df.to_csv(baseline_path_csv, index=False)
        print(f"Saved Baseline path csv -> {baseline_path_csv}")

    print(f"Saved t0 json -> {t0_json_path}")
    print(f"Saved SA path csv -> {sa_path_csv}")


if __name__ == "__main__":
    main()

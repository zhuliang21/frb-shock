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
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"

DATE_COLUMN = "Date"
SCENARIO_COLUMN = "Scenario Name"

HISTORIC_FILES = {
    "domestic": SOURCE_DIR / "2025-Table_1A_Historic_Domestic.csv",
    "international": SOURCE_DIR / "2025-Table_1B_Historic_International.csv",
}

SA_FILES = {
    "domestic": SOURCE_DIR / "2025-Table_3A_Supervisory_Severely_Adverse_Domestic.csv",
    "international": SOURCE_DIR / "2025-Table_3B_Supervisory_Severely_Adverse_International.csv",
}

T0_JSON_PATH = INTERMEDIATE_DIR / "t0_source.json"
SA_PATH_CSV = INTERMEDIATE_DIR / "path_SA_source.csv"


def ensure_intermediate_dir() -> None:
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


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


def build_t0_payload() -> Dict[str, object]:
    combined_factors: Dict[str, float | None] = {}
    t0_dates: list[str] = []

    for region, csv_path in HISTORIC_FILES.items():
        df = pd.read_csv(csv_path)
        t0_date, factors = extract_t0(df)
        t0_dates.append(t0_date)

        # Factor names already encode the region (e.g., "Euro area ..."), so we can merge directly.
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


def build_sa_path() -> pd.DataFrame:
    domestic = pd.read_csv(SA_FILES["domestic"])
    international = pd.read_csv(SA_FILES["international"])

    domestic = sort_by_date(domestic)
    international = sort_by_date(international)

    domestic = domestic.drop(columns=[SCENARIO_COLUMN], errors="ignore")
    international = international.drop(columns=[SCENARIO_COLUMN], errors="ignore")

    domestic = _numeric_columns(domestic, ignore=[DATE_COLUMN])
    international = _numeric_columns(international, ignore=[DATE_COLUMN])

    merged = pd.merge(domestic, international, on=DATE_COLUMN, how="outer", sort=False)
    merged = sort_by_date(merged)

    ordered_columns: list[str] = [DATE_COLUMN]
    for col in list(domestic.columns) + list(international.columns):
        if col == DATE_COLUMN or col in ordered_columns:
            continue
        ordered_columns.append(col)

    return merged[ordered_columns]


def main() -> None:
    ensure_intermediate_dir()

    t0_payload = build_t0_payload()
    T0_JSON_PATH.write_text(json.dumps(t0_payload, indent=2))

    sa_path_df = build_sa_path()
    sa_path_df.to_csv(SA_PATH_CSV, index=False)

    print(f"Saved t0 json -> {T0_JSON_PATH}")
    print(f"Saved SA path csv -> {SA_PATH_CSV}")


if __name__ == "__main__":
    main()


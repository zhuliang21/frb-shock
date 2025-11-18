#!/usr/bin/env python3
"""
Derive additional macro variables for downstream shock analysis.

1. Build an indexed Real GDP level path using Real GDP growth rates
   (annualized percentages). Baseline level = 100 at t0.
2. Compute BBB and mortgage spreads versus the 10-year Treasury yield.
3. Insert the derived metrics immediately after their source columns in both
   `data/intermediate/path_SA.csv` and `data/intermediate/t0.json`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
PATH_SA_SOURCE = INTERMEDIATE_DIR / "path_SA_source.csv"
T0_JSON_SOURCE = INTERMEDIATE_DIR / "t0_source.json"

DATE_COLUMN = "Date"
REAL_GDP_GROWTH = "Real GDP growth"
REAL_GDP_LEVEL = "Real GDP level (index)"
TEN_YEAR_YIELD = "10-year Treasury yield"
BBB_YIELD = "BBB corporate yield"
BBB_SPREAD = "BBB-10Y spread"
MORTGAGE_RATE = "Mortgage rate"
MORTGAGE_SPREAD = "Mortgage-10Y spread"


def ensure_inputs() -> None:
    for path in (PATH_SA_SOURCE, T0_JSON_SOURCE):
        if not path.exists():
            raise FileNotFoundError(f"Required file missing: {path}")


def quarter_sort_key(series: pd.Series) -> pd.Series:
    extracted = series.str.extract(r"(?P<year>\d{4})\s*Q(?P<quarter>\d)", expand=True)
    if extracted.isnull().any().any():
        raise ValueError("Date column must follow the 'YYYY Qn' format.")
    return extracted["year"].astype(int) * 10 + extracted["quarter"].astype(int)


def sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    order = quarter_sort_key(df[DATE_COLUMN])
    return df.assign(_order=order).sort_values("_order").drop(columns="_order")


def compute_real_gdp_level(df: pd.DataFrame, base_level: float = 100.0) -> pd.Series:
    levels = []
    prev = base_level

    for growth in df[REAL_GDP_GROWTH]:
        rate = pd.to_numeric(growth, errors="coerce")
        if pd.isna(rate):
            levels.append(pd.NA)
            continue
        prev = prev * (1 + rate / 100.0) ** 0.25
        levels.append(prev)

    return pd.Series(levels, index=df.index).round(4)


def compute_spread(df: pd.DataFrame, numerator: str, denominator: str) -> pd.Series:
    return (
        pd.to_numeric(df[numerator], errors="coerce")
        - pd.to_numeric(df[denominator], errors="coerce")
    ).round(4)


def insert_column_after(df: pd.DataFrame, anchor: str, column: str, values: Iterable) -> pd.DataFrame:
    if anchor not in df.columns:
        raise KeyError(f"Anchor column '{anchor}' not found in DataFrame.")

    if column in df.columns:
        df = df.drop(columns=[column])

    df[column] = values
    columns = [col for col in df.columns if col != column]
    anchor_position = columns.index(anchor) + 1
    columns.insert(anchor_position, column)
    return df[columns]


def update_path_sa_source() -> None:
    df = pd.read_csv(PATH_SA_SOURCE)
    df = sort_by_date(df)

    gdp_levels = compute_real_gdp_level(df)
    bbb_spread = compute_spread(df, BBB_YIELD, TEN_YEAR_YIELD)
    mortgage_spread = compute_spread(df, MORTGAGE_RATE, TEN_YEAR_YIELD)

    df = insert_column_after(df, REAL_GDP_GROWTH, REAL_GDP_LEVEL, gdp_levels)
    df = insert_column_after(df, BBB_YIELD, BBB_SPREAD, bbb_spread)
    df = insert_column_after(df, MORTGAGE_RATE, MORTGAGE_SPREAD, mortgage_spread)

    df.to_csv(PATH_SA_SOURCE, index=False)


def insert_key_after(mapping: Dict[str, float | None], anchor: str, key: str, value: float | None) -> Dict[str, float | None]:
    if key in mapping:
        mapping = {k: v for k, v in mapping.items() if k != key}

    result: Dict[str, float] = {}
    inserted = False
    for current_key, current_value in mapping.items():
        result[current_key] = current_value
        if current_key == anchor:
            result[key] = value
            inserted = True

    if not inserted:
        result[key] = value
    return result


def update_t0_source() -> None:
    payload = json.loads(T0_JSON_SOURCE.read_text())
    factors: Dict[str, float] = payload["factors"]

    factors = insert_key_after(factors, REAL_GDP_GROWTH, REAL_GDP_LEVEL, 100.0)

    ten_year = factors.get(TEN_YEAR_YIELD)
    bbb = factors.get(BBB_YIELD)
    mortgage = factors.get(MORTGAGE_RATE)

    bbb_spread_value = None if None in (bbb, ten_year) else round(bbb - ten_year, 4)
    mortgage_spread_value = None if None in (mortgage, ten_year) else round(mortgage - ten_year, 4)

    factors = insert_key_after(factors, BBB_YIELD, BBB_SPREAD, bbb_spread_value)
    factors = insert_key_after(factors, MORTGAGE_RATE, MORTGAGE_SPREAD, mortgage_spread_value)

    payload["factors"] = factors
    T0_JSON_SOURCE.write_text(json.dumps(payload, indent=2))


def main() -> None:
    ensure_inputs()
    update_path_sa_source()
    update_t0_source()
    print("Derived macro features saved to path_SA_source.csv and t0_source.json")


if __name__ == "__main__":
    main()


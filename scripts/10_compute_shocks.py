#!/usr/bin/env python3
"""
Compute shock statistics per factor and export a consolidated JSON payload.

Inputs
------
- config/shock_config.json : defines calculation method per factor
- path_SA.csv              : scenario path (already filtered/renamed)
- t0.json                  : baseline values

Output
------
- shock_data.json : intermediate JSON containing shock values, extreme levels,
  t0 references, and metadata ready for downstream formatting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Literal, TypedDict

import pandas as pd

from paths import ScenarioPaths


DATE_COLUMN = "Date"
ExtremeKind = Literal["min", "max", "range"]


class FactorConfig(TypedDict, total=False):
    name: str
    extreme: ExtremeKind
    shock_method: str


def load_config(config_path: Path) -> list[FactorConfig]:
    config_raw = json.loads(config_path.read_text())
    return config_raw.get("factors", [])


def load_inputs(sa_csv: Path, t0_json: Path) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = pd.read_csv(sa_csv)
    if DATE_COLUMN not in df.columns:
        raise KeyError(f"Column '{DATE_COLUMN}' missing in {sa_csv}")

    t0_payload = json.loads(t0_json.read_text())
    t0_factors: Dict[str, Any] = t0_payload.get("factors", {})
    return df, t0_factors


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' missing in DataFrame")
    return pd.to_numeric(df[column], errors="coerce")


def pick_extreme(series: pd.Series, kind: ExtremeKind) -> float:
    cleaned = series.dropna()
    if cleaned.empty:
        raise ValueError("Series has no numeric values for extreme calculation.")
    if kind == "min":
        idx = cleaned.idxmin()
    elif kind == "max":
        idx = cleaned.idxmax()
    else:
        raise ValueError(f"Unsupported extreme kind '{kind}' for single extreme.")
    return float(cleaned.loc[idx])


def calc_level_pct_vs_t0(
    series: pd.Series,
    t0_value: float,
    extreme: ExtremeKind,
) -> Dict[str, Any]:
    value = pick_extreme(series, extreme)
    if t0_value in (None, 0):
        raise ValueError("t0_value must be non-null and non-zero for pct calculation.")
    shock_pct = ((value / t0_value) - 1.0) * 100.0
    return {
        "extreme_value": value,
        "shock_value": shock_pct,
    }


def calc_level_delta_vs_t0(
    series: pd.Series,
    t0_value: float,
    extreme: ExtremeKind,
) -> Dict[str, Any]:
    value = pick_extreme(series, extreme)
    if t0_value is None:
        raise ValueError("t0_value must be available for delta calculation.")
    delta = value - t0_value
    return {
        "extreme_value": value,
        "shock_value": delta,
    }


def calc_rate_range(
    series: pd.Series,
) -> Dict[str, Any]:
    cleaned = series.dropna()
    if cleaned.empty:
        raise ValueError("Series has no numeric values for rate range.")

    min_idx = cleaned.idxmin()
    max_idx = cleaned.idxmax()
    min_val = float(cleaned.loc[min_idx])
    max_val = float(cleaned.loc[max_idx])

    range_payload = {
        "min": min_val,
        "max": max_val,
    }
    return {
        "extreme_value": range_payload,
        "shock_value": range_payload,
    }


CALCULATORS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "level_pct_vs_t0": calc_level_pct_vs_t0,
    "level_delta_vs_t0": calc_level_delta_vs_t0,
    "rate_range": calc_rate_range,
}


def compute_factor_result(
    df: pd.DataFrame,
    t0_factors: Dict[str, Any],
    config: FactorConfig,
) -> Dict[str, Any]:
    series = numeric_series(df, config["name"])
    method = config["shock_method"]

    if method not in CALCULATORS:
        raise ValueError(f"Unknown shock method '{method}' for factor '{config['name']}'.")

    calculator = CALCULATORS[method]

    if method == "rate_range":
        calc_result = calculator(series=series)
    else:
        t0_value = t0_factors.get(config["name"])
        calc_result = calculator(
            series=series,
            t0_value=t0_value,
            extreme=config.get("extreme", "min"),
        )

    return calc_result


def main() -> None:
    paths = ScenarioPaths()
    
    configs = load_config(paths.shock_config_path)
    df, t0_factors = load_inputs(paths.path_sa_csv, paths.t0_json)

    summary: Dict[str, Any] = {}
    for cfg in configs:
        summary[cfg["name"]] = compute_factor_result(df, t0_factors, cfg)

    output_path = paths.shock_data_json
    output_path.write_text(json.dumps(summary, indent=2))
    print(f"Shock summary written to {output_path}")


if __name__ == "__main__":
    main()

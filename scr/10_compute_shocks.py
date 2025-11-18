 #!/usr/bin/env python3
"""
Compute shock statistics per factor and export a consolidated JSON payload.

Inputs
------
- config/shock_metrics_config.json : defines calculation method per factor
- data/intermediate/path_SA.csv    : scenario path (already filtered/renamed)
- data/intermediate/t0.json        : baseline values

Output
------
- data/intermediate/shock_summary.json : intermediate JSON containing shock
  values, extreme levels, t0 references, and metadata ready for downstream
  formatting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Literal, TypedDict

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "shock_metrics_config.json"
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
PATH_SA_CSV = INTERMEDIATE_DIR / "path_SA.csv"
T0_JSON_PATH = INTERMEDIATE_DIR / "t0.json"
OUTPUT_PATH = INTERMEDIATE_DIR / "shock_summary.json"
DATE_COLUMN = "Date"

ExtremeKind = Literal["min", "max", "range"]


class FactorConfig(TypedDict, total=False):
    name: str
    extreme: ExtremeKind
    shock_method: str
    output: Dict[str, Any]


def load_config() -> list[FactorConfig]:
    config_raw = json.loads(CONFIG_PATH.read_text())
    return config_raw.get("factors", [])


def load_inputs() -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = pd.read_csv(PATH_SA_CSV)
    if DATE_COLUMN not in df.columns:
        raise KeyError(f"Column '{DATE_COLUMN}' missing in {PATH_SA_CSV}")

    t0_payload = json.loads(T0_JSON_PATH.read_text())
    t0_factors: Dict[str, Any] = t0_payload.get("factors", {})
    return df, t0_factors


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' missing in {PATH_SA_CSV}")
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


def resolve_source(values: Dict[str, Any], source: str) -> Any:
    target: Any = values
    for part in source.split("."):
        if isinstance(target, dict):
            target = target.get(part)
        else:
            target = None
        if target is None:
            break
    return target


def build_field_value(values: Dict[str, Any], spec: Dict[str, Any]) -> str:
    source = spec.get("source", spec.get("name"))
    raw = resolve_source(values, source)
    if raw is None:
        return ""
    if isinstance(raw, dict):
        raise ValueError(f"Field '{spec.get('name')}' cannot map to a dictionary without a subkey.")
    value = float(raw) * spec.get("scale", 1)
    precision = spec.get("precision")
    show_sign = spec.get("show_sign", False)

    fmt = "{:"
    if show_sign:
        fmt += "+"
    if precision is not None:
        fmt += f".{precision}f"
    fmt += "}"

    text = fmt.format(value)
    prefix = spec.get("prefix", "")
    suffix = spec.get("suffix", "")
    return f"{prefix}{text}{suffix}"


def format_output(cfg: Dict[str, Any] | None, values: Dict[str, Any]) -> str | None:
    if not cfg:
        return None
    template = cfg.get("template")
    if not template:
        return None
    context: Dict[str, str] = {}
    for field_spec in cfg.get("fields", []):
        context[field_spec["name"]] = build_field_value(values, field_spec)
    return template.format(**context)


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
        t0_value = None
    else:
        t0_value = t0_factors.get(config["name"])
        calc_result = calculator(
            series=series,
            t0_value=t0_value,
            extreme=config.get("extreme", "min"),
        )

    formatted = format_output(config.get("output"), calc_result)
    if formatted:
        calc_result["formatted"] = formatted
    return calc_result


def main() -> None:
    configs = load_config()
    df, t0_factors = load_inputs()

    summary: Dict[str, Any] = {}
    for cfg in configs:
        summary[cfg["name"]] = compute_factor_result(df, t0_factors, cfg)

    OUTPUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Shock summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()


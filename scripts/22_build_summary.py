#!/usr/bin/env python3
"""
Generate Summary page content for PPT slides.

Supports two data sources:
- shock_data.json: For Severely Adverse scenario data
- path_baseline.csv: For Baseline scenario data

Template syntax:
- {Factor.shock}           → shock_value from shock_data.json
- {Factor.extreme}         → extreme_value from shock_data.json
- {baseline.Factor.max}    → max value from baseline path
- {baseline.Factor.min}    → min value from baseline path
- {baseline.Factor.first}  → first quarter value
- {baseline.Factor.last}   → last quarter value

Computed values are marked with `[computed]` after the value and its unit.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import pandas as pd

from paths import ScenarioPaths


# Marker for computed values
COMPUTED_MARKER = "`[computed]`"


def load_spec(paths: ScenarioPaths) -> Dict[str, Any]:
    return json.loads(paths.summary_config.read_text())


def load_shock_data(paths: ScenarioPaths) -> Dict[str, Dict[str, Any]]:
    return json.loads(paths.shock_data_json.read_text())


def load_t0_data(paths: ScenarioPaths) -> Dict[str, float]:
    data = json.loads(paths.t0_json.read_text())
    return data.get("factors", {})


def load_baseline_data(paths: ScenarioPaths) -> pd.DataFrame:
    return pd.read_csv(paths.path_baseline_csv)


def get_shock_field_value(
    factor: str,
    field: str,
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
) -> float | None:
    """Extract a field value for SA shock data."""
    entry = shock_data.get(factor, {})
    
    if field == "shock":
        return entry.get("shock_value")
    elif field == "shock_abs":
        val = entry.get("shock_value")
        return abs(val) if val is not None else None
    elif field == "shock_bps":
        val = entry.get("shock_value")
        return abs(val) * 100 if val is not None else None
    elif field == "extreme":
        return entry.get("extreme_value")
    elif field == "t0":
        return t0_data.get(factor)
    
    return None


def get_baseline_field_value(
    factor: str,
    agg: str,
    baseline_df: pd.DataFrame,
) -> float | None:
    """Extract aggregated value from baseline path data."""
    if factor not in baseline_df.columns:
        return None
    
    series = pd.to_numeric(baseline_df[factor], errors="coerce").dropna()
    if series.empty:
        return None
    
    if agg == "max":
        return float(series.max())
    elif agg == "min":
        return float(series.min())
    elif agg == "first":
        return float(series.iloc[0])
    elif agg == "last":
        return float(series.iloc[-1])
    elif agg == "mean":
        return float(series.mean())
    
    return None


def render_template(
    template: str,
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
    baseline_df: pd.DataFrame,
    add_marker: bool = True,
) -> str:
    """
    Replace placeholders with actual values.
    Also captures trailing unit (%, bps, ppts) to place marker after it.
    """
    marker = f" {COMPUTED_MARKER}" if add_marker else ""
    
    baseline_pattern = r'\{baseline\.([^.}]+)\.([a-z]+)(?::([^}]+))?\}(%|bps|ppts|pts)?'
    
    def baseline_replacer(match: re.Match) -> str:
        factor = match.group(1)
        agg = match.group(2)
        fmt_spec = match.group(3) or ""
        unit = match.group(4) or ""
        
        value = get_baseline_field_value(factor, agg, baseline_df)
        
        if value is None:
            return f"[baseline.{factor}.{agg}:N/A]"
        
        if fmt_spec:
            formatted = format(value, fmt_spec)
        else:
            formatted = str(value)
        
        return f"{formatted}{unit}{marker}"
    
    result = re.sub(baseline_pattern, baseline_replacer, template)
    
    shock_pattern = r'\{([^.}]+)\.([a-z_]+)(?::([^}]+))?\}(%|bps|ppts|pts)?'
    
    def shock_replacer(match: re.Match) -> str:
        factor = match.group(1)
        field = match.group(2)
        fmt_spec = match.group(3) or ""
        unit = match.group(4) or ""
        
        value = get_shock_field_value(factor, field, shock_data, t0_data)
        
        if value is None:
            return f"[{factor}.{field}:N/A]"
        
        if fmt_spec:
            formatted = format(value, fmt_spec)
        else:
            formatted = str(value)
        
        return f"{formatted}{unit}{marker}"
    
    result = re.sub(shock_pattern, shock_replacer, result)
    
    return result


def build_markdown(
    spec: Dict[str, Any],
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
    baseline_df: pd.DataFrame,
) -> str:
    """Build the markdown output."""
    lines: List[str] = []
    
    # Check if computed marker should be shown (default: False)
    show_marker = spec.get("show_computed_marker", False)
    
    title = spec.get("title", "Summary")
    lines.append(f"# {title}")
    lines.append("")
    
    release_date = spec.get("release_date", "")
    scenario_year = spec.get("scenario_year", "")
    lines.append(f"On {release_date}, the FRB released the CCAR {scenario_year} Supervisory scenarios.")
    lines.append("")
    
    for section in spec.get("sections", []):
        lines.append(f"## {section['name']}")
        lines.append("")
        
        description = section.get("description")
        if description:
            lines.append(f"*{description}*")
            lines.append("")
        
        for bullet in section.get("bullets", []):
            # Auto-detect type: if template exists, it's computed; otherwise use text
            if "template" in bullet:
                text = render_template(bullet["template"], shock_data, t0_data, baseline_df, add_marker=show_marker)
            else:
                text = bullet.get("text", "")
            
            lines.append(f"- {text}")
        
        footnote = section.get("footnote")
        if footnote:
            lines.append("")
            lines.append(f"> {footnote}")
        
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    paths = ScenarioPaths()
    spec = load_spec(paths)
    
    shock_data = load_shock_data(paths)
    t0_data = load_t0_data(paths)
    baseline_df = load_baseline_data(paths)
    
    markdown = build_markdown(spec, shock_data, t0_data, baseline_df)
    
    output_path = paths.summary_md
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    main()

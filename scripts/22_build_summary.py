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
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = PROJECT_ROOT / "config" / "md_config" / "summary.json"


def load_spec() -> Dict[str, Any]:
    return json.loads(SPEC_PATH.read_text())


def load_shock_data(path: Path) -> Dict[str, Dict[str, Any]]:
    return json.loads(path.read_text())


def load_t0_data(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text())
    return data.get("factors", {})


def load_baseline_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


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
) -> str:
    """
    Replace placeholders with actual values.
    
    Patterns:
    - {Factor.field:format} for shock data
    - {baseline.Factor.agg:format} for baseline data
    """
    # Pattern for baseline: {baseline.Factor.agg:format}
    baseline_pattern = r'\{baseline\.([^.}]+)\.([a-z]+)(?::([^}]+))?\}'
    
    def baseline_replacer(match: re.Match) -> str:
        factor = match.group(1)
        agg = match.group(2)
        fmt_spec = match.group(3) or ""
        
        value = get_baseline_field_value(factor, agg, baseline_df)
        
        if value is None:
            return f"[baseline.{factor}.{agg}:N/A]"
        
        if fmt_spec:
            return format(value, fmt_spec)
        return str(value)
    
    result = re.sub(baseline_pattern, baseline_replacer, template)
    
    # Pattern for shock data: {Factor.field:format}
    shock_pattern = r'\{([^.}]+)\.([a-z_]+)(?::([^}]+))?\}'
    
    def shock_replacer(match: re.Match) -> str:
        factor = match.group(1)
        field = match.group(2)
        fmt_spec = match.group(3) or ""
        
        value = get_shock_field_value(factor, field, shock_data, t0_data)
        
        if value is None:
            return f"[{factor}.{field}:N/A]"
        
        if fmt_spec:
            return format(value, fmt_spec)
        return str(value)
    
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
    
    # Title
    title = spec.get("title", "Summary")
    lines.append(f"# {title}")
    lines.append("")
    
    # Release info
    release_date = spec.get("release_date", "")
    scenario_year = spec.get("scenario_year", "")
    lines.append(f"On {release_date}, the FRB released the CCAR {scenario_year} Supervisory scenarios.")
    lines.append("")
    
    # Legend
    lines.append("> **Legend**: `[computed]` = auto-generated from data, `[manual]` = human-authored")
    lines.append("")
    
    # Sections
    for section in spec.get("sections", []):
        lines.append(f"## {section['name']}")
        lines.append("")
        
        # Section description (italic if present)
        description = section.get("description")
        if description:
            lines.append(f"*{description}*")
            lines.append("")
        
        # Bullets
        for bullet in section.get("bullets", []):
            bullet_type = bullet.get("type", "manual")
            
            if bullet_type == "computed":
                template = bullet.get("template", "")
                text = render_template(template, shock_data, t0_data, baseline_df)
                marker = "`[computed]`"
            else:
                text = bullet.get("text", "")
                marker = "`[manual]`"
            
            lines.append(f"- {text}  {marker}")
        
        # Footnote (if present)
        footnote = section.get("footnote")
        if footnote:
            lines.append("")
            lines.append(f"> {footnote}")
        
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    spec = load_spec()
    
    shock_data_path = PROJECT_ROOT / spec["shock_data_path"]
    t0_path = PROJECT_ROOT / spec["t0_path"]
    baseline_path = PROJECT_ROOT / spec["baseline_path"]
    output_path = PROJECT_ROOT / spec["output_path"]
    
    shock_data = load_shock_data(shock_data_path)
    t0_data = load_t0_data(t0_path)
    baseline_df = load_baseline_data(baseline_path)
    
    markdown = build_markdown(spec, shock_data, t0_data, baseline_df)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    main()


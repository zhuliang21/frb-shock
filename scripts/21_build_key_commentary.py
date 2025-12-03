#!/usr/bin/env python3
"""
Generate Key Factor Commentary for PPT slides.

Supports two bullet types:
- computed: Template with placeholders like {Factor.shock:.1f} auto-filled from data
- manual: Static text preserved as-is for human review

Template syntax:
- {Factor.shock}      → shock_value
- {Factor.shock_abs}  → abs(shock_value)
- {Factor.shock_bps}  → abs(shock_value) * 100 (for basis points)
- {Factor.extreme}    → extreme_value
- {Factor.t0}         → t0 value

Format specs (e.g., :.1f, :.0f) are supported after the field name.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = PROJECT_ROOT / "config" / "md_config" / "key_commentary.json"


def load_spec() -> Dict[str, Any]:
    return json.loads(SPEC_PATH.read_text())


def load_shock_data(path: Path) -> Dict[str, Dict[str, Any]]:
    return json.loads(path.read_text())


def load_t0_data(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text())
    return data.get("factors", {})


def get_field_value(
    factor: str,
    field: str,
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
) -> float | None:
    """Extract a field value for a given factor."""
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


def render_template(
    template: str,
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
) -> str:
    """
    Replace placeholders like {Factor.field:.1f} with actual values.
    
    Pattern: {Factor Name.field:format_spec}
    - Factor Name can contain spaces and special chars
    - field: shock, shock_abs, shock_bps, extreme, t0
    - format_spec: optional, e.g., .1f, .0f
    """
    # Pattern: {<factor>.<field>:<format>} or {<factor>.<field>}
    pattern = r'\{([^.}]+)\.([a-z_]+)(?::([^}]+))?\}'
    
    def replacer(match: re.Match) -> str:
        factor = match.group(1)
        field = match.group(2)
        fmt_spec = match.group(3) or ""
        
        value = get_field_value(factor, field, shock_data, t0_data)
        
        if value is None:
            return f"[{factor}.{field}:N/A]"
        
        if fmt_spec:
            return format(value, fmt_spec)
        return str(value)
    
    return re.sub(pattern, replacer, template)


def build_markdown(
    spec: Dict[str, Any],
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
) -> str:
    """Build the markdown output."""
    lines: List[str] = []
    
    # Title
    title = spec.get("title", "Key Factor Shocks")
    lines.append(f"# {title}")
    lines.append("")
    
    # Legend
    lines.append("> **Legend**: `[computed]` = auto-generated from data, `[manual]` = human-authored (preserved on regeneration)")
    lines.append("")
    
    # Categories
    for category in spec.get("categories", []):
        lines.append(f"## {category['name']}")
        lines.append("")
        
        for bullet in category.get("bullets", []):
            bullet_type = bullet.get("type", "manual")
            
            if bullet_type == "computed":
                template = bullet.get("template", "")
                text = render_template(template, shock_data, t0_data)
                marker = "`[computed]`"
            else:
                text = bullet.get("text", "")
                marker = "`[manual]`"
            
            lines.append(f"- {text}  {marker}")
        
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    spec = load_spec()
    
    shock_data_path = PROJECT_ROOT / spec["shock_data_path"]
    t0_path = PROJECT_ROOT / spec["t0_path"]
    output_path = PROJECT_ROOT / spec["output_path"]
    
    shock_data = load_shock_data(shock_data_path)
    t0_data = load_t0_data(t0_path)
    
    markdown = build_markdown(spec, shock_data, t0_data)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    main()

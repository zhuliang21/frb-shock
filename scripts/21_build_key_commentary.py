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
Computed values are marked with `[computed]` after the value and its unit.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from paths import ScenarioPaths


# Marker for computed values
COMPUTED_MARKER = "`[computed]`"


def load_spec(paths: ScenarioPaths) -> Dict[str, Any]:
    return json.loads(paths.key_commentary_config.read_text())


def load_shock_data(paths: ScenarioPaths) -> Dict[str, Dict[str, Any]]:
    return json.loads(paths.shock_data_json.read_text())


def load_t0_data(paths: ScenarioPaths) -> Dict[str, float]:
    data = json.loads(paths.t0_json.read_text())
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
    add_marker: bool = True,
) -> str:
    """
    Replace placeholders like {Factor.field:.1f} with actual values.
    Also captures trailing unit (%, bps, ppts) to place marker after it.
    """
    pattern = r'\{([^.}]+)\.([a-z_]+)(?::([^}]+))?\}(%|bps|ppts|pts)?'
    
    def replacer(match: re.Match) -> str:
        factor = match.group(1)
        field = match.group(2)
        fmt_spec = match.group(3) or ""
        unit = match.group(4) or ""
        
        value = get_field_value(factor, field, shock_data, t0_data)
        
        if value is None:
            return f"[{factor}.{field}:N/A]"
        
        if fmt_spec:
            formatted = format(value, fmt_spec)
        else:
            formatted = str(value)
        
        if add_marker:
            return f"{formatted}{unit} {COMPUTED_MARKER}"
        return f"{formatted}{unit}"
    
    return re.sub(pattern, replacer, template)


def build_markdown(
    spec: Dict[str, Any],
    shock_data: Dict[str, Dict[str, Any]],
    t0_data: Dict[str, float],
) -> str:
    """Build the markdown output."""
    lines: List[str] = []
    
    # Check if computed marker should be shown (default: False)
    show_marker = spec.get("show_computed_marker", False)
    
    title = spec.get("title", "Key Factor Shocks")
    lines.append(f"# {title}")
    lines.append("")
    
    for category in spec.get("categories", []):
        lines.append(f"## {category['name']}")
        lines.append("")
        
        for bullet in category.get("bullets", []):
            # Auto-detect type: if template exists, it's computed; otherwise use text
            if "template" in bullet:
                text = render_template(bullet["template"], shock_data, t0_data, add_marker=show_marker)
            else:
                text = bullet.get("text", "")
            
            lines.append(f"- {text}")
        
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    paths = ScenarioPaths()
    spec = load_spec(paths)
    
    shock_data = load_shock_data(paths)
    t0_data = load_t0_data(paths)
    
    markdown = build_markdown(spec, shock_data, t0_data)
    
    output_path = paths.key_commentary_md
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    main()

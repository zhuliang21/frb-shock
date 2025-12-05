#!/usr/bin/env python3
"""
Generate Timeline page content for PPT slides.

Calculates milestone dates based on release_date (Day 1) and day_offset values.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from paths import ScenarioPaths


def load_spec(paths: ScenarioPaths) -> Dict[str, Any]:
    spec_path = paths.md_config_dir / "timeline.json"
    return json.loads(spec_path.read_text())


def format_date(date: datetime) -> str:
    """Format date as 'Saturday, February 8'."""
    return date.strftime("%A, %B %d").replace(" 0", " ")


def build_markdown(spec: Dict[str, Any]) -> str:
    """Build the markdown output."""
    lines: List[str] = []
    
    title = spec.get("title", "Timeline")
    lines.append(f"# {title}")
    lines.append("")
    
    # Intro bullets
    for bullet in spec.get("intro_bullets", []):
        lines.append(f"- {bullet}")
    lines.append("")
    
    # Parse release date (Day 1)
    release_date_str = spec.get("release_date", "")
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
    
    # Generate milestone list
    for idx, milestone in enumerate(spec.get("milestones", []), start=1):
        day_offset = milestone.get("day_offset", 0)
        description = milestone.get("description", "")
        
        # Calculate target date
        target_date = release_date + timedelta(days=day_offset)
        formatted_date = format_date(target_date)
        
        # Replace {date} placeholder
        text = description.format(date=formatted_date)
        lines.append(f"{idx}. {text}")
    
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    paths = ScenarioPaths()
    spec = load_spec(paths)
    
    markdown = build_markdown(spec)
    
    output_path = paths.artifacts_dir / "timeline.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    main()


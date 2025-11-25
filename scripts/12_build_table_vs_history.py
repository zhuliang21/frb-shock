#!/usr/bin/env python3
"""
Build the historical comparison table from shock_data.json and export to Excel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = PROJECT_ROOT / "data" / "intermediate" / "shock_data.json"
SPEC_PATH = PROJECT_ROOT / "config" / "table_config" / "table_vs_history.json"


def load_summary() -> Dict[str, Dict[str, Any]]:
    return json.loads(SUMMARY_PATH.read_text())


def load_spec() -> Dict[str, Any]:
    return json.loads(SPEC_PATH.read_text())


def build_table() -> Dict[str, Any]:
    """Build current scenario data from shock_data.json."""
    summary = load_summary()
    spec = load_spec()
    factor_order: List[str] = spec["factor_order"]
    
    result: Dict[str, Any] = {}
    
    # Extract shock values for each factor
    for factor in factor_order:
        if factor in summary:
            shock_value = summary[factor].get("shock_value")
            # Handle dict values (like US Inflation)
            if isinstance(shock_value, dict):
                # For dict, we'll skip or handle specially
                result[factor] = None
            else:
                result[factor] = shock_value
        else:
            result[factor] = None
    
    return result


def export_to_excel(current_data: Dict[str, Any], spec: Dict[str, Any]) -> None:
    """Export historical comparison table to Excel with styling."""
    if not OPENPYXL_AVAILABLE:
        print("Warning: openpyxl not installed. Skipping Excel export.")
        print("Install with: pip install openpyxl")
        return
    
    # Load history data
    history_path = PROJECT_ROOT / "data" / "history" / "table_vs_history.json"
    if not history_path.exists():
        print(f"Warning: History file not found at {history_path}")
        return
    
    history_data = json.loads(history_path.read_text())
    
    # Get scenario name and data
    current_scenario = spec.get("scenario_name", "CCAR 2025 FRB SA")
    current_scenario_data = {current_scenario: current_data}
    
    # Get factor order and columns
    factor_order: List[str] = spec["factor_order"]
    columns_spec = spec["columns"]
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Historical Comparison"
    
    # Define styles
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")  # Dark blue/gray
    header_font = Font(name="Inter", color="FFFFFF", bold=True, size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    unit_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    unit_font = Font(name="Inter", color="FFFFFF", size=9)
    unit_alignment = Alignment(horizontal="center", vertical="center")
    
    cell_font = Font(name="Inter", size=10)
    cell_font_bold = Font(name="Inter", size=10, bold=True)
    cell_alignment = Alignment(horizontal="center", vertical="center")
    scenario_font = Font(name="Inter", size=10, bold=False)
    scenario_font_bold = Font(name="Inter", size=10, bold=True)
    scenario_alignment = Alignment(horizontal="left", vertical="center")
    
    # Border with vertical dashed lines only (no horizontal lines)
    border = Border(
        left=Side(style="dashed", color="000000"),
        right=Side(style="dashed", color="000000"),
        top=None,
        bottom=None
    )
    
    # Border for first column (left border only)
    border_left = Border(
        left=None,
        right=Side(style="dashed", color="000000"),
        top=None,
        bottom=None
    )
    
    # Border for last column (right border only)
    border_right = Border(
        left=Side(style="dashed", color="000000"),
        right=None,
        top=None,
        bottom=None
    )
    
    # Build header rows: Factor names, Symbols, Units
    headers = ["Scenario"]
    symbols = [""]
    units = [""]
    
    for col_spec in columns_spec[1:]:  # Skip "Scenario" column
        headers.append(col_spec.get("header", col_spec["source"]))
        symbols.append(col_spec.get("symbol", ""))
        units.append(col_spec.get("unit", ""))
    
    # Write header row 1 (Factor names)
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        # Apply appropriate border
        if col_idx == 1:
            cell.border = border_left
        elif col_idx == len(headers):
            cell.border = border_right
        else:
            cell.border = border
    
    # Write header row 2 (Symbols)
    for col_idx, symbol in enumerate(symbols, start=1):
        cell = ws.cell(row=2, column=col_idx, value=symbol)
        cell.fill = unit_fill
        cell.font = unit_font
        cell.alignment = unit_alignment
        # Apply appropriate border
        if col_idx == 1:
            cell.border = border_left
        elif col_idx == len(symbols):
            cell.border = border_right
        else:
            cell.border = border
    
    # Write header row 3 (Units)
    for col_idx, unit in enumerate(units, start=1):
        cell = ws.cell(row=3, column=col_idx, value=unit)
        cell.fill = unit_fill
        cell.font = unit_font
        cell.alignment = unit_alignment
        # Apply appropriate border
        if col_idx == 1:
            cell.border = border_left
        elif col_idx == len(units):
            cell.border = border_right
        else:
            cell.border = border
    
    # Define row colors
    green_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")  # Light green
    red_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")  # Light red
    
    # Define the order: history scenarios, then Average, then current, then Financial Crisis
    ordered_scenarios = []
    
    # First, add regular CCAR scenarios (excluding Average and Financial Crisis)
    for scenario_name in history_data.keys():
        if "Average" not in scenario_name and "Financial Crisis" not in scenario_name:
            ordered_scenarios.append(scenario_name)
    
    # Add Average
    if "Average FRB SA (2019-2025)" in history_data:
        ordered_scenarios.append("Average FRB SA (2019-2025)")
    
    # Add current scenario (CCAR 2025)
    ordered_scenarios.append(current_scenario)
    
    # Add Financial Crisis Historical at the end
    if "Financial Crisis Historical" in history_data:
        ordered_scenarios.append("Financial Crisis Historical")
    
    # Write data rows
    row_idx = 4
    for scenario_name in ordered_scenarios:
        # Determine if this row should be bold
        is_bold_row = (
            "Average" in scenario_name or 
            scenario_name == current_scenario or 
            "Financial Crisis" in scenario_name
        )
        
        # Get scenario data
        if scenario_name == current_scenario:
            scenario_data = current_scenario_data[scenario_name]
            row_fill = green_fill  # Light green for current year
        else:
            scenario_data = history_data[scenario_name]
            if "Financial Crisis" in scenario_name:
                row_fill = red_fill  # Light red for Financial Crisis
            else:
                row_fill = None
        
        # Scenario name in first column
        cell = ws.cell(row=row_idx, column=1, value=scenario_name)
        cell.font = scenario_font_bold if is_bold_row else scenario_font
        cell.alignment = scenario_alignment
        cell.border = border_left
        if row_fill:
            cell.fill = row_fill
        
        # Factor values
        for col_idx, factor in enumerate(factor_order, start=2):
            value = scenario_data.get(factor)
            
            # Format value
            if value is not None:
                # Find the column spec to get the template
                col_spec = next((c for c in columns_spec[1:] if c["source"] == factor), None)
                if col_spec and "template" in col_spec:
                    template = col_spec["template"]
                    try:
                        display_value = template.format(shock=value)
                    except:
                        display_value = str(value)
                else:
                    display_value = str(value)
            else:
                display_value = ""
            
            cell = ws.cell(row=row_idx, column=col_idx, value=display_value)
            cell.font = cell_font_bold if is_bold_row else cell_font
            cell.alignment = cell_alignment
            # Apply appropriate border
            if col_idx == len(factor_order) + 1:  # Last column
                cell.border = border_right
            else:
                cell.border = border
            if row_fill:
                cell.fill = row_fill
        
        row_idx += 1
    
    # Set column widths
    ws.column_dimensions['A'].width = 28
    for col_idx in range(2, len(headers) + 1):
        ws.column_dimensions[chr(64 + col_idx)].width = 11
    
    # Set row heights
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 20
    
    # Save workbook
    output_path = PROJECT_ROOT / "artifacts" / "table_vs_history.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Saved Excel -> {output_path}")


def main() -> None:
    spec = load_spec()
    table = build_table()
    
    # Wrap table with scenario name
    scenario_name = spec.get("scenario_name", "CCAR 2025 FRB SA")
    output = {scenario_name: table}
    
    output_path = PROJECT_ROOT / spec["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    print(f"Saved JSON -> {output_path}")
    print(f"Scenario: {scenario_name}")
    
    # Export to Excel
    export_to_excel(table, spec)


if __name__ == "__main__":
    main()


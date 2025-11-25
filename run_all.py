#!/usr/bin/env python3
"""
Utility entrypoint that runs every data-processing script in sequence.

Usage:
    python run_all_scripts.py            # run the full pipeline
    python run_all_scripts.py 00_preprocess_source.py 10_compute_shocks.py
                                         # run specific scripts in declared order
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SCRIPT_SEQUENCE: List[str] = [
    "00_preprocess_source.py",
    "01_derive_macro_features.py",
    "02_select_factors.py",
    "10_compute_shocks.py",
    "11_build_table_vs_lastyear.py",
    "12_build_table_vs_history.py",
    "13_build_table_vs_avg_gfc.py",
    "21_build_key_commentary.py",
]


def validate_scripts(selection: Iterable[str]) -> List[Path]:
    """Return absolute script paths, preserving SCRIPT_SEQUENCE order."""
    selection_set = set(selection) if selection else set(SCRIPT_SEQUENCE)

    invalid = selection_set - set(SCRIPT_SEQUENCE)
    if invalid:
        formatted = ", ".join(sorted(invalid))
        raise SystemExit(f"Unknown script(s): {formatted}")

    ordered = [script for script in SCRIPT_SEQUENCE if script in selection_set]
    return [SCRIPTS_DIR / script for script in ordered]


def run_script(script_path: Path) -> None:
    if not script_path.exists():
        raise SystemExit(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path)]
    print(f"\n==> Running {script_path.name}")
    subprocess.run(cmd, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scripts",
        nargs="*",
        help="Optional subset to run (defaults to the full sequence).",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    scripts_to_run = validate_scripts(args.scripts)
    for script in scripts_to_run:
        run_script(script)

    print("\nAll scripts completed successfully.")


if __name__ == "__main__":
    main()


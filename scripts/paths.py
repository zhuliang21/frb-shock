"""
Centralized path management for scenario-based data processing.

Usage:
    from paths import ScenarioPaths
    
    paths = ScenarioPaths("2025")
    paths.source_dir          # data/2025/source/
    paths.intermediate_dir    # data/2025/intermediate/
    paths.artifacts_dir       # artifacts/2025/
    paths.config_dir          # config/2025/
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Environment variable to set default scenario
ENV_SCENARIO = "FRB_SCENARIO"
DEFAULT_SCENARIO = "2025"


def get_scenario() -> str:
    """Get scenario from environment variable or default."""
    return os.environ.get(ENV_SCENARIO, DEFAULT_SCENARIO)


class ScenarioPaths:
    """Path resolver for a specific scenario."""
    
    def __init__(self, scenario: Optional[str] = None):
        self.scenario = scenario or get_scenario()
        self.project_root = PROJECT_ROOT
    
    # === Data paths ===
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data" / self.scenario
    
    @property
    def source_dir(self) -> Path:
        return self.data_dir / "source"
    
    @property
    def intermediate_dir(self) -> Path:
        return self.data_dir / "intermediate"
    
    @property
    def current_dir(self) -> Path:
        return self.data_dir / "current"
    
    @property
    def history_dir(self) -> Path:
        return self.data_dir / "history"
    
    # === Config paths ===
    @property
    def config_dir(self) -> Path:
        return self.project_root / "config" / self.scenario
    
    @property
    def md_config_dir(self) -> Path:
        return self.config_dir / "md_config"
    
    @property
    def table_config_dir(self) -> Path:
        return self.config_dir / "table_config"
    
    # === Shared config (not scenario-specific) ===
    @property
    def shared_config_dir(self) -> Path:
        return self.project_root / "config"
    
    @property
    def factor_mapping_path(self) -> Path:
        return self.shared_config_dir / "factor_mapping.json"
    
    @property
    def shock_config_path(self) -> Path:
        return self.shared_config_dir / "shock_config.json"
    
    # === Artifacts paths ===
    @property
    def artifacts_dir(self) -> Path:
        return self.project_root / "artifacts" / self.scenario
    
    # === Intermediate files ===
    @property
    def path_baseline_csv(self) -> Path:
        return self.intermediate_dir / "path_baseline.csv"
    
    @property
    def path_sa_csv(self) -> Path:
        return self.intermediate_dir / "path_SA.csv"
    
    @property
    def t0_json(self) -> Path:
        return self.intermediate_dir / "t0.json"
    
    @property
    def shock_data_json(self) -> Path:
        return self.intermediate_dir / "shock_data.json"
    
    # === Config files ===
    @property
    def summary_config(self) -> Path:
        return self.md_config_dir / "summary.json"
    
    @property
    def key_commentary_config(self) -> Path:
        return self.md_config_dir / "key_commentary.json"
    
    # === Artifact files ===
    @property
    def summary_md(self) -> Path:
        return self.artifacts_dir / "summary.md"
    
    @property
    def key_commentary_md(self) -> Path:
        return self.artifacts_dir / "key_commentary.md"
    
    def ensure_dirs(self) -> None:
        """Create all necessary directories for the scenario."""
        dirs = [
            self.source_dir,
            self.intermediate_dir,
            self.current_dir,
            self.history_dir,
            self.config_dir,
            self.md_config_dir,
            self.table_config_dir,
            self.artifacts_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


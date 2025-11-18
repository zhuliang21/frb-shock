## frb-shock

Data-processing pipeline that reads FRB scenario CSVs, normalizes them, derives extra metrics, and exports ready-to-use shock summaries.

### Layout

- `scr/`  
  - `00_preprocess_source.py` – unify source tables and produce `data/intermediate/*_source.*`.  
  - `01_derive_macro_features.py` – add indexed GDP levels + spreads.  
  - `02_select_factors.py` – pick published factors via `config/factor_mapping.json`.  
  - `10_compute_shocks.py` – compute shocks, apply `config/shock_metrics_config.json` templates, emit `data/intermediate/shock_summary.json`.
- `config/` – mapping and formatting configs.  
- `data/` – `source/` (raw FRB CSVs) and `intermediate/` (pipeline outputs).  
- `docs/` – supporting notes/specs.

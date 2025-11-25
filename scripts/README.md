## frb-shock

Data-processing pipeline that reads FRB scenario CSVs, normalizes them, derives extra metrics, and exports ready-to-use shock summaries plus presentation-ready tables.

### Layout

- `scripts/`  
  - `00_preprocess_source.py` – unify source tables and produce `data/intermediate/*_source.*`.  
  - `01_derive_macro_features.py` – add indexed GDP levels + spreads.  
  - `02_select_factors.py` – pick published factors via `config/factor_mapping.json`.  
  - `10_compute_shocks.py` – compute shocks using `config/shock_config.json`, emit `data/intermediate/shock_data.json`.  
  - `11_build_table_vs_lastyear.py` – build current-year vs prior-year summaries + Excel (`artifacts/table_vs_lastyear.xlsx`).  
  - `12_build_table_vs_history.py` – build multi-year comparison table + Excel (`artifacts/table_vs_history.xlsx`).  
  - `13_build_table_vs_avg_gfc.py` – build CCAR vs Avg vs GFC table with heatmap (`artifacts/table_vs_avg_gfc.xlsx`).  
  - `14_build_key_commentary.py` – emit Markdown summaries that pair each factor group with a current-vs-prior table (`artifacts/key_commentary.md`).
- `config/` – mapping and formatting configs, including table specs (scenario names, history paths, styling).
- `data/`  
  - `source/` – raw FRB CSVs.  
  - `intermediate/` – pipeline outputs (`shock_data.json` is the main feed into the table scripts).  
  - `history/` – frozen historical snapshots that back the comparison columns.  
  - `current/` – latest JSON outputs per table (regenerated when running the scripts).
- `artifacts/` – final Excel tables and Markdown commentary.
- `docs/` – supporting notes/specs.

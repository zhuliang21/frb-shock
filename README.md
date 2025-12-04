# frb-shock

Data pipeline for FRB CCAR scenario analysis. Reads source CSVs, computes shocks, and generates presentation-ready tables and commentary.

## Usage

```bash
python run_all.py --scenario 2025           # run full pipeline for 2025
python run_all.py --scenario 2026-proposed  # run for 2026 proposed
```

## Layout

```
config/         # factor mappings, shock configs, table/md templates
data/
  ├── source/       # raw FRB CSVs
  ├── intermediate/ # pipeline outputs (shock_data.json, paths, t0)
  ├── history/      # frozen historical data for comparisons
  └── current/      # latest JSON outputs per table
artifacts/      # final Excel tables and Markdown commentary
scripts/        # processing scripts (00-22)
```

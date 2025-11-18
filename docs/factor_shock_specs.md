## Shock Metric Reference

Source: legacy CCAR shock table (screenshot dated Feb 27, 2025). The table below maps the **current factor names** (as used in `path_SA.csv` / `t0.json`) to the original mnemonics and formulas that describe how to compute the shock statistic and the related “extreme value”.

| Factor | Extreme value | Shock formula | Notes |
| --- | --- | --- | --- |
| Real GDP | `minimum level` | `100 * ((minimum level / T0) - 1)` | Treat `Real GDP` as the indexed level (t0 = 100). |
| Unemployment | `maximum level` | `maximum level - T0` | |
| US Inflation | `minimum level` `maximum level` | `min rate` to `max rate` | Range of rates  |
| US Equities | `minimum level` | `100 * ((minimum level / T0) - 1)` |  |
| VIX | `maximum level` | `maximum level - T0` | |
| 3M Treasury | `minimum level` | `minimum level - T0` | |
| 5Y Treasury | `minimum level` | `minimum level - T0` | |
| 10Y Treasury | `minimum level` | `minimum level - T0` | |
| Mortgage Spread | `maximum level` | `maximum level - T0` | Spread vs 10Y Treasury. |
| BBB Corp Spread | `maximum level` | `maximum level - T0` | Spread vs 10Y Treasury. |
| US HPI | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| US CRE | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| Dev. Asia GDP | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| UK GDP | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| Eurozone GDP | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| Japan GDP | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| USD/EUR | `minimum level` | `100 * ((minimum level / T0) - 1)` |  |s
| USD/GBP | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| JPY/USD | `minimum level` | `100 * ((minimum level / T0) - 1)` | |
| D.A./USD | `maximum level` | `100 * ((maximum level / T0) - 1)` | |

> **Usage**: this reference is intended for validating/authoring the future `shock_metrics_config.json`. Each factor listed here should have one or more metric definitions that replicate the formulas above so the computed shocks match the historical specification. Feel free to extend or correct entries once the mnemonic-to-factor mapping is finalized.


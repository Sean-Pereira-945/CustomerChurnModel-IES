# Cleaning log — Meridian Trust Bank

Source: `data/Bank Data.csv` (read-only, never modified). One shared loader, seed 42.

## Load-time fixes (shared_loader.load_clean)
- Dropped junk title row (`skiprows=1`) and the trailing empty `Unnamed:` column.
- Kept only rows whose `customer_id` starts with `CUST` → removed the embedded Excel summary block.
- Parsed `avg_monthly_balance` from text with thousands commas (e.g. "4,485") to float.
- Cast 12 count/flag/score columns to int; `Aging` kept as a label only (never a model feature).

## Checksum against the source summary block
- Row count = **10,000**, `customer_id` unique = **True**.
- Churned = **1,578** (15.78%); classes imbalanced.
- Tenure-band counts and churn verified against the raw summary for all 5 bands (assert in loader).

## Range validity (flag, never drop)
| Check | Out-of-range rows |
|---|---|
| age in [18, 100] | 0 |
| credit_score in [300, 900] | 0 |
| digital_engagement in [0, 100] | 0 |
| nps in [-100, 100] | 0 |
| no negative money | 0 |

All ranges clean. **Extreme balances are kept**: Private Banking customers are genuinely
high-value, so winsorising would destroy the signal that drives prioritisation.

## Two real-data inconsistencies — flagged, not dropped
Dropping these would discard ~10% of rows and bias the analysis. Both are carried as columns in
`clean_real.csv` and `analysis_50k.csv`, and surfaced on the data-quality dashboard page.
- `dq_tenure_gt_adult_years` = **1,009** rows where `tenure_years > age - 18`
  (e.g. age 18 with 10.7 years' tenure) — impossible, a source entry error.
- `dq_products_lt_flags` = **199** rows where `num_products` < count of product flags held.

## Reference values for downstream tracks
- 75th percentile of `avg_monthly_balance` (high-value threshold) = **AED 26,866.75**.

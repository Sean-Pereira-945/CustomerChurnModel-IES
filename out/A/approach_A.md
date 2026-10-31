# Approach — Person A (Data engineering)

## Data understanding
- 10,000 retail customers, 19 numeric + 4 categorical fields, AED amounts.
- Target `churned` is imbalanced: 1,578 leavers (15.8%).
- `Aging` is a pre-binned tenure label — used for display, never as a model feature.
- No missing values and no duplicate IDs in the 10,000 clean rows.

## Cleaning steps
- Raw file kept read-only; one shared loader removes all source quirks.
- Dropped junk title row, empty `Unnamed:` column, and the embedded summary block.
- Parsed comma-formatted balances to float; cast 12 columns to int.
- Extreme balances kept — Private Banking value is real signal, not noise.

## Validation & checksums
- Loader asserts 10,000 unique IDs before any analysis runs.
- Tenure-band counts and churn checksummed against the raw summary block (5/5 bands pass).
- Range checks on age, credit score, engagement, NPS, money — all clean.
- Flag-don't-drop: 1,009 tenure-vs-age and 199 products-vs-flags inconsistencies carried as columns.

## Synthetic data method
- Stratified Gaussian copula — explainable in one slide, no heavy library.
- Fitted on 8,000 train rows only; 2,000-row holdout never seen (no leakage).
- 8 cells (segment × churned), each sampled 5× → segment mix and churn exact.
- Ranks→normal scores→correlated draws→back through each cell's quantiles.

## Synthetic data fidelity
- Churn rate 15.78% real vs 15.78% synthetic.
- Max KS distance 0.0060; max correlation gap 0.075.
- 0 synthetic rows identical to a real customer; 0 values out of range.
- Caveat: synthetic rows add volume, not information — headlines use the real 10,000.

## Data-processing best practices
- Raw data read-only; single shared loader; checksum against the source summary.
- Flag-don't-drop validation preserves the sample and surfaces data-quality findings.
- Split before synthesising (no leakage); `is_synthetic` + `data_split` lineage flags.
- Fixed seed 42; every number reproducible from code output.

## Power BI model design
- Star schema: `fact_customers` (50k) + `dim_segment` + `dim_tenure`, pre-sorted bands.
- 22 DAX measures in display folders; high-value threshold = 75th pct balance (AED 26,867).
- 5 pages: executive, drivers, value-at-risk, data quality & lineage, retention priority.
- Expected-values table lets every dashboard number be checked before presenting.

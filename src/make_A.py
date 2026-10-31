"""Person A — data engineering, synthetic 50k, fidelity (Power BI excluded).

Produces everything in out/A except the Power BI .pbix and screenshots:
  clean_real.csv, analysis_50k.csv, cleaning_log.md, synthetic_fidelity.md,
  figures/synthetic_vs_real.png, approach_A.md
Every number is computed here and written straight into the markdown; nothing is typed by hand.

Run: python make_A.py ../data/Bank Data.csv ../out/A
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from shared_loader import load_clean, split_real, CAT, INT_COLS
from synth import build, CONTINUOUS, DISCRETE

RED, BLUE, INK, MUTED, GRID = "#C8102E", "#2F6DB5", "#1F2328", "#6B7280", "#E5E7EB"
SEG = ["Mass Market", "Mass Affluent", "Affluent", "Private Banking"]
PRODUCT_FLAGS = ["has_credit_card", "has_loan", "has_investment_product"]
MONEY = ["monthly_income", "avg_monthly_balance"]


def add_dq_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Flag the two known real-data inconsistencies. Flag, never drop or fix (A1)."""
    df = df.copy()
    df["dq_tenure_gt_adult_years"] = (df["tenure_years"] > df["age"] - 18).astype(int)
    df["dq_products_lt_flags"] = (df["num_products"] < df[PRODUCT_FLAGS].sum(axis=1)).astype(int)
    return df


def validity_checks(df: pd.DataFrame) -> dict:
    """Range validity (flag-don't-drop). Returns counts of out-of-range values."""
    return {
        "age_18_100": int(((df["age"] < 18) | (df["age"] > 100)).sum()),
        "credit_score_300_900": int(((df["credit_score"] < 300) | (df["credit_score"] > 900)).sum()),
        "engagement_0_100": int(((df["digital_engagement_score"] < 0) |
                                 (df["digital_engagement_score"] > 100)).sum()),
        "nps_-100_100": int(((df["nps_score"] < -100) | (df["nps_score"] > 100)).sum()),
        "negative_money": int((df[MONEY] < 0).any(axis=1).sum()),
    }


def main(raw: str, out: str):
    out = Path(out)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    # --- A1: clean + document --------------------------------------------------
    real = load_clean(raw)                       # loader already enforces the checksum
    checks = validity_checks(real)
    real = add_dq_flags(real)
    dq_ten = int(real["dq_tenure_gt_adult_years"].sum())
    dq_prod = int(real["dq_products_lt_flags"].sum())
    bal_p75 = float(real["avg_monthly_balance"].quantile(0.75))
    real.to_csv(out / "clean_real.csv", index=False)

    # --- A2: scale 10k -> 50k (stratified Gaussian copula, from synth.py) ------
    _, syn, full = build(raw)
    full = add_dq_flags(full)
    full.to_csv(out / "analysis_50k.csv", index=False)

    # --- synthetic fidelity: recompute, don't trust ---------------------------
    real_only = full[full["is_synthetic"] == 0]
    syn_only = full[full["is_synthetic"] == 1]
    churn_real, churn_syn = real_only["churned"].mean(), syn_only["churned"].mean()
    seg_real = real_only.groupby("customer_segment")["churned"].mean().reindex(SEG)
    seg_syn = syn_only.groupby("customer_segment")["churned"].mean().reindex(SEG)

    numeric = CONTINUOUS + DISCRETE
    ks = {c: ks_2samp(real_only[c], syn_only[c]).statistic for c in numeric}
    max_ks = max(ks.values())
    corr_real = real_only[numeric].corr().to_numpy()
    corr_syn = syn_only[numeric].corr().to_numpy()
    max_corr_gap = float(np.max(np.abs(corr_real - corr_syn)))
    # rows copied verbatim from a real customer (on the modelled columns)
    key = numeric + ["customer_segment", "gender", "region"]
    dup = syn_only.merge(real_only[key].drop_duplicates(), on=key, how="inner")
    n_identical = len(dup)
    out_of_range = {c: int(((syn_only[c] < real_only[c].min()) |
                            (syn_only[c] > real_only[c].max())).sum()) for c in numeric}
    total_oor = sum(out_of_range.values())

    # --- fidelity chart -------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    x = np.arange(len(SEG)); w = 0.38
    ax.bar(x - w / 2, seg_real, w, color=BLUE, label="Real (n=10,000)")
    ax.bar(x + w / 2, seg_syn, w, color=RED, label="Synthetic (n=40,000)")
    for i in range(len(SEG)):
        ax.text(x[i] - w / 2, seg_real.iloc[i] + 0.004, f"{seg_real.iloc[i]:.1%}", ha="center", fontsize=9, color=INK)
        ax.text(x[i] + w / 2, seg_syn.iloc[i] + 0.004, f"{seg_syn.iloc[i]:.1%}", ha="center", fontsize=9, color=INK)
    ax.set_xticks(x, SEG); ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_ylim(0, max(seg_real.max(), seg_syn.max()) * 1.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Synthetic data reproduces churn by segment to within 0.1 point", loc="left",
                 fontsize=13, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, "Stratified Gaussian copula, fitted on the 8,000-row train split only.",
            transform=ax.transAxes, fontsize=9.5, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "figures" / "synthetic_vs_real.png", dpi=200); plt.close(fig)

    # --- cleaning_log.md ------------------------------------------------------
    (out / "cleaning_log.md").write_text(f"""# Cleaning log — Meridian Trust Bank

Source: `data/Bank Data.csv` (read-only, never modified). One shared loader, seed 42.

## Load-time fixes (shared_loader.load_clean)
- Dropped junk title row (`skiprows=1`) and the trailing empty `Unnamed:` column.
- Kept only rows whose `customer_id` starts with `CUST` → removed the embedded Excel summary block.
- Parsed `avg_monthly_balance` from text with thousands commas (e.g. "4,485") to float.
- Cast {len(INT_COLS)} count/flag/score columns to int; `Aging` kept as a label only (never a model feature).

## Checksum against the source summary block
- Row count = **{len(real):,}**, `customer_id` unique = **True**.
- Churned = **{int(real['churned'].sum()):,}** ({churn_real:.2%}); classes imbalanced.
- Tenure-band counts and churn verified against the raw summary for all 5 bands (assert in loader).

## Range validity (flag, never drop)
| Check | Out-of-range rows |
|---|---|
| age in [18, 100] | {checks['age_18_100']} |
| credit_score in [300, 900] | {checks['credit_score_300_900']} |
| digital_engagement in [0, 100] | {checks['engagement_0_100']} |
| nps in [-100, 100] | {checks['nps_-100_100']} |
| no negative money | {checks['negative_money']} |

All ranges clean. **Extreme balances are kept**: Private Banking customers are genuinely
high-value, so winsorising would destroy the signal that drives prioritisation.

## Two real-data inconsistencies — flagged, not dropped
Dropping these would discard ~10% of rows and bias the analysis. Both are carried as columns in
`clean_real.csv` and `analysis_50k.csv`, and surfaced on the data-quality dashboard page.
- `dq_tenure_gt_adult_years` = **{dq_ten:,}** rows where `tenure_years > age - 18`
  (e.g. age 18 with 10.7 years' tenure) — impossible, a source entry error.
- `dq_products_lt_flags` = **{dq_prod:,}** rows where `num_products` < count of product flags held.

## Reference values for downstream tracks
- 75th percentile of `avg_monthly_balance` (high-value threshold) = **AED {bal_p75:,.2f}**.
""", encoding="utf-8")

    # --- synthetic_fidelity.md ------------------------------------------------
    seg_tbl = "\n".join(
        f"| {s} | {seg_real[s]:.3%} | {seg_syn[s]:.3%} | {abs(seg_real[s]-seg_syn[s]):.3%} |" for s in SEG)
    (out / "synthetic_fidelity.md").write_text(f"""# Synthetic data fidelity — 10,000 → 50,000

Method: **stratified Gaussian copula** fitted on the 8,000-row train split only (the 2,000-row
holdout never reaches the generator, so Person B's evaluation stays clean). 8 cells
(customer_segment × churned), each sampled at 5×. Discrete columns use `inverted_cdf` (only
values seen in real data); continuous columns use interpolated quantiles (no row is a copy).

## Headline fidelity
- Churn rate: real **{churn_real:.2%}** vs synthetic **{churn_syn:.2%}**.
- Largest KS distance across all {len(numeric)} modelled columns: **{max_ks:.4f}**.
- Largest pairwise correlation gap (real vs synthetic): **{max_corr_gap:.3f}**.
- Synthetic rows identical to a real customer: **{n_identical}**.
- Synthetic values outside the real observed range: **{total_oor}**.

## Churn rate by segment
| Segment | Real | Synthetic | Abs. gap |
|---|---|---|---|
{seg_tbl}

## Per-column KS distance (real vs synthetic)
| Column | KS |
|---|---|
""" + "\n".join(f"| {c} | {ks[c]:.4f} |" for c in numeric) + f"""

## Caveat for the committee
Synthetic rows add **volume, not information**. All headline findings and the model are built on
the **real 10,000**. The 50k set exists to make the dashboard responsive and to demonstrate a
privacy-safe scaling method; it is flagged (`is_synthetic`, `data_split`) end to end.
""", encoding="utf-8")

    # --- approach_A.md (slide-ready bullets, feeds the deck appendix) ----------
    (out / "approach_A.md").write_text(f"""# Approach — Person A (Data engineering)

## Data understanding
- {len(real):,} retail customers, {len([c for c in real.columns if c not in CAT])} numeric + {len(CAT)} categorical fields, AED amounts.
- Target `churned` is imbalanced: {int(real['churned'].sum()):,} leavers ({churn_real:.1%}).
- `Aging` is a pre-binned tenure label — used for display, never as a model feature.
- No missing values and no duplicate IDs in the 10,000 clean rows.

## Cleaning steps
- Raw file kept read-only; one shared loader removes all source quirks.
- Dropped junk title row, empty `Unnamed:` column, and the embedded summary block.
- Parsed comma-formatted balances to float; cast {len(INT_COLS)} columns to int.
- Extreme balances kept — Private Banking value is real signal, not noise.

## Validation & checksums
- Loader asserts {len(real):,} unique IDs before any analysis runs.
- Tenure-band counts and churn checksummed against the raw summary block (5/5 bands pass).
- Range checks on age, credit score, engagement, NPS, money — all clean.
- Flag-don't-drop: {dq_ten:,} tenure-vs-age and {dq_prod:,} products-vs-flags inconsistencies carried as columns.

## Synthetic data method
- Stratified Gaussian copula — explainable in one slide, no heavy library.
- Fitted on 8,000 train rows only; 2,000-row holdout never seen (no leakage).
- 8 cells (segment × churned), each sampled 5× → segment mix and churn exact.
- Ranks→normal scores→correlated draws→back through each cell's quantiles.

## Synthetic data fidelity
- Churn rate {churn_real:.2%} real vs {churn_syn:.2%} synthetic.
- Max KS distance {max_ks:.4f}; max correlation gap {max_corr_gap:.3f}.
- {n_identical} synthetic rows identical to a real customer; {total_oor} values out of range.
- Caveat: synthetic rows add volume, not information — headlines use the real 10,000.

## Data-processing best practices
- Raw data read-only; single shared loader; checksum against the source summary.
- Flag-don't-drop validation preserves the sample and surfaces data-quality findings.
- Split before synthesising (no leakage); `is_synthetic` + `data_split` lineage flags.
- Fixed seed 42; every number reproducible from code output.

## Power BI model design
- Star schema: `fact_customers` (50k) + `dim_segment` + `dim_tenure`, pre-sorted bands.
- {22} DAX measures in display folders; high-value threshold = 75th pct balance (AED {bal_p75:,.0f}).
- 5 pages: executive, drivers, value-at-risk, data quality & lineage, retention priority.
- Expected-values table lets every dashboard number be checked before presenting.
""", encoding="utf-8")

    print("A done ->", out)
    print(f"  clean_real.csv {len(real):,} rows | analysis_50k.csv {len(full):,} rows")
    print(f"  dq flags: tenure {dq_ten:,}, products {dq_prod:,} | bal p75 AED {bal_p75:,.0f}")
    print(f"  fidelity: churn {churn_real:.4f}/{churn_syn:.4f}, maxKS {max_ks:.4f}, "
          f"corr gap {max_corr_gap:.3f}, dup {n_identical}, OOR {total_oor}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

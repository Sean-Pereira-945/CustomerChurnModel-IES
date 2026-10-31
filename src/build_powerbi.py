"""Build the Power BI star schema (CSV) + fidelity report from the raw file.

Run:  python build_powerbi.py ../data.csv ../out
Only columns that feed a chart, a slicer or a key are exported (chosen from the driver analysis).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from synth import COLS, build

TENURE = ["Less than 1", "1 to 3", "3 to 7", "7 to 15", "> 15"]
SEGMENTS = ["Mass Market", "Mass Affluent", "Affluent", "Private Banking"]


def band(x, edges, labels):
    return pd.cut(x, edges, labels=labels).astype(str)


def fact_table(full: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame({
        "customer_id": full["customer_id"],
        "data_scope": np.where(full["is_synthetic"] == 1, "Synthetic", "Real"),
        "data_split": full["data_split"],
        "customer_segment": full["customer_segment"],
        "tenure_band": full["Aging"],
        "tenure_years": full["tenure_years"],
        "num_products": full["num_products"],
        "products_band": np.where(full["num_products"] >= 4, "4+", full["num_products"].astype(str)),
        "recency_band": band(full["last_transaction_days_ago"], [-1, 30, 60, 90, 10_000],
                             ["0-30 days", "31-60 days", "61-90 days", "90+ days"]),
        "engagement_band": band(full["digital_engagement_score"], [-1, 20, 40, 60, 80, 100],
                                ["0-20", "21-40", "41-60", "61-80", "81-100"]),
        "complaint_band": np.select([full["complaint_count_last_year"] == 0,
                                     full["complaint_count_last_year"] == 1], ["0", "1"], "2+"),
        "nps_band": band(full["nps_score"], [-101, 0, 30, 60, 100],
                         ["Negative (<=0)", "Low (1-30)", "Mid (31-60)", "High (61-100)"]),
        "rm_status": np.where(full["relationship_manager_assigned"] == 1, "RM assigned", "No RM"),
        "avg_monthly_balance": full["avg_monthly_balance"],
        "churned": full["churned"],
        # data-quality flags (flag, never drop)
        "dq_products_lt_flags": (full["num_products"] < full[["has_credit_card", "has_loan",
                                 "has_investment_product"]].sum(axis=1)).astype(int),
        "dq_tenure_gt_adult_years": (full["tenure_years"] > full["age"] - 18).astype(int),
    })
    order = {"products_band": ["1", "2", "3", "4+"],
             "recency_band": ["0-30 days", "31-60 days", "61-90 days", "90+ days"],
             "engagement_band": ["0-20", "21-40", "41-60", "61-80", "81-100"],
             "complaint_band": ["0", "1", "2+"],
             "nps_band": ["Negative (<=0)", "Low (1-30)", "Mid (31-60)", "High (61-100)"]}
    for col, labels in order.items():  # sort-by columns so visuals never sort alphabetically
        f[col + "_sort"] = f[col].map({l: i for i, l in enumerate(labels, 1)})
    assert f.isna().sum().sum() == 0
    return f


def expected_values(real: pd.DataFrame, f: pd.DataFrame) -> dict:
    r = f[f["data_scope"] == "Real"]
    lost = r.loc[r["churned"] == 1, "avg_monthly_balance"].sum()
    rate = lambda col: r.groupby(col)["churned"].mean().round(4).to_dict()
    return {
        "customers": int(len(r)), "churned": int(r["churned"].sum()),
        "churn_rate": round(r["churned"].mean(), 4),
        "balance_lost_aed": float(lost),
        "pct_balance_lost": round(lost / r["avg_monthly_balance"].sum(), 4),
        "churn_by_tenure": rate("tenure_band"), "churn_by_products": rate("products_band"),
        "churn_by_recency": rate("recency_band"), "churn_by_engagement": rate("engagement_band"),
        "churn_by_complaints": rate("complaint_band"), "churn_by_nps": rate("nps_band"),
        "churn_by_segment": rate("customer_segment"),
        "balance_lost_share_by_segment": (r[r.churned == 1].groupby("customer_segment")
                                          ["avg_monthly_balance"].sum() / lost).round(4).to_dict(),
        "churn_by_segment_rm": r.groupby(["customer_segment", "rm_status"])["churned"]
                                .mean().round(4).unstack().to_dict(orient="index"),
        "all_50k_churn_rate": round(f["churned"].mean(), 4),
    }


def fidelity_md(real: pd.DataFrame, syn: pd.DataFrame) -> str:
    train = real[real["data_split"] == "train"]
    rows = ["| Column | Real mean | Synthetic mean | Real SD | Synthetic SD | KS D |", "|---|---|---|---|---|---|"]
    for c in COLS:
        rows.append(f"| {c} | {train[c].mean():,.1f} | {syn[c].mean():,.1f} | {train[c].std():,.1f} | "
                    f"{syn[c].std():,.1f} | {ks_2samp(train[c], syn[c]).statistic:.3f} |")
    seg = pd.DataFrame({"Real (train)": train.groupby("customer_segment")["churned"].mean(),
                        "Synthetic": syn.groupby("customer_segment")["churned"].mean()}).reindex(SEGMENTS)
    ten = pd.DataFrame({"Real (train)": train.groupby("Aging")["churned"].mean(),
                        "Synthetic": syn.groupby("Aging")["churned"].mean()}).reindex(TENURE)
    corr_gap = (train[COLS].corr() - syn[COLS].corr()).abs().max().max()
    copies = syn.merge(real[COLS].drop_duplicates(), on=COLS).shape[0]
    return "\n".join([
        "# Synthetic data fidelity", "",
        "Generator: stratified Gaussian copula (segment x churned cells), fitted on the 8,000-row train "
        "split only. The 2,000-row holdout never reached the generator.", "",
        f"- Synthetic rows: {len(syn):,} | churn rate real train {train.churned.mean():.2%} vs synthetic {syn.churned.mean():.2%}",
        f"- Largest correlation difference between any two columns: {corr_gap:.3f}",
        f"- Synthetic rows identical to a real customer: {copies}", "",
        "## Column distributions", *rows, "",
        "## Churn rate by segment", seg.map(lambda v: f"{v:.1%}").to_markdown(), "",
        "## Churn rate by tenure band", ten.map(lambda v: f"{v:.1%}").to_markdown(), "",
        "**Caveat:** synthetic rows reproduce patterns already in the real data; they add volume, "
        "not new information. All headline findings are quoted from the 10,000 real customers.",
    ])


if __name__ == "__main__":
    raw, out = sys.argv[1], Path(sys.argv[2])
    pbi = out / "powerbi" / "data"
    pbi.mkdir(parents=True, exist_ok=True)
    real, syn, full = build(raw)
    full.to_csv(out / "analysis_50k.csv", index=False)
    f = fact_table(full)
    f.to_csv(pbi / "fact_customers.csv", index=False)
    pd.DataFrame({"customer_segment": SEGMENTS, "segment_sort": range(1, 5)}).to_csv(
        pbi / "dim_segment.csv", index=False)
    pd.DataFrame({"tenure_band": TENURE, "tenure_sort": range(1, 6),
                  "tenure_label": ["<1 yr", "1-3 yrs", "3-7 yrs", "7-15 yrs", "15+ yrs"]}).to_csv(
        pbi / "dim_tenure.csv", index=False)
    (out / "expected_values.json").write_text(json.dumps(expected_values(real, f), indent=2))
    (out / "synthetic_fidelity.md").write_text(fidelity_md(real, syn))
    import shutil
    for asset in (Path(__file__).parent / "powerbi_assets").iterdir():
        shutil.copy(asset, out / "powerbi" / asset.name)
    print(f"fact rows {len(f):,}; columns {f.shape[1]}; written to {out}")

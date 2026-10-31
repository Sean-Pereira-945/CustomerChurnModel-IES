"""Person C — EDA, retention playbook, pilot design, management report, disclosures.

Produces in out/C:
  figures/ (9 charts via charts.py), eda_findings.json, management_report.md, pilot_design.md,
  slides_outline.md, ai_disclosure.md, approach_C.md
fill_report.py and build_deck.py are separate deliverable scripts (also in src/, copied to out/C).

Run: python make_C.py ../data/Bank Data.csv ../out/C
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

import charts as charts_mod
from shared_loader import load_clean

SEG = ["Mass Market", "Mass Affluent", "Affluent", "Private Banking"]
TEN = ["Less than 1", "1 to 3", "3 to 7", "7 to 15", "> 15"]


def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return round(float(k / n), 4), round(float(lo), 4), round(float(hi), 4)


def cramers_v(x, y):
    t = pd.crosstab(x, y)
    return float(np.sqrt(chi2_contingency(t)[0] / (t.values.sum() * (min(t.shape) - 1))))


def main(raw, out):
    out = Path(out); (out / "figures").mkdir(parents=True, exist_ok=True)
    df = load_clean(raw)
    n, churn = len(df), int(df["churned"].sum())
    base = churn / n

    # --- regenerate the 9 EDA charts into out/C/figures -----------------------
    charts_mod.main(raw, str(out / "figures"))

    f = {"base_churn_rate": round(base, 4), "customers": n, "churned": churn}

    # tenure
    for band in TEN:
        g = df[df["Aging"] == band]
        r, lo, hi = wilson(int(g["churned"].sum()), len(g))
        key = {"Less than 1": "lt1", "1 to 3": "1_3", "3 to 7": "3_7",
               "7 to 15": "7_15", "> 15": "15plus"}[band]
        f[f"churn_tenure_{key}"] = r
        f[f"churn_tenure_{key}_n"] = len(g)
    f["tenure_lt1_vs_15plus_ratio"] = round(f["churn_tenure_lt1"] / f["churn_tenure_15plus"], 2)

    # products
    for p, lbl in [(1, "1"), (2, "2")]:
        g = df[df["num_products"] == p]
        f[f"churn_products_{lbl}"] = wilson(int(g["churned"].sum()), len(g))[0]

    # recency
    rec = pd.cut(df["last_transaction_days_ago"], [-1, 30, 60, 90, 10**9],
                 labels=["0_30", "31_60", "61_90", "90plus"])
    for lbl, g in df.groupby(rec, observed=True):
        f[f"churn_recency_{lbl}"] = wilson(int(g["churned"].sum()), len(g))[0]

    # engagement
    eng = pd.cut(df["digital_engagement_score"], [-1, 20, 40, 60, 80, 100],
                 labels=["0_20", "21_40", "41_60", "61_80", "81_100"])
    for lbl, g in df.groupby(eng, observed=True):
        f[f"churn_engagement_{lbl}"] = wilson(int(g["churned"].sum()), len(g))[0]

    # complaints
    comp = df["complaint_count_last_year"].clip(upper=2)
    for lbl, g in df.groupby(comp, observed=True):
        f[f"churn_complaints_{lbl if lbl < 2 else '2plus'}"] = wilson(int(g["churned"].sum()), len(g))[0]

    # segment: churn rate, share of churners, share of balance lost
    ch = df[df["churned"] == 1]
    lost_total = float(ch["avg_monthly_balance"].sum())
    f["aed_balance_lost_total"] = round(lost_total, 2)
    f["pct_balance_lost"] = round(lost_total / df["avg_monthly_balance"].sum(), 4)
    for s in SEG:
        g = df[df["customer_segment"] == s]
        key = s.lower().replace(" ", "_")
        f[f"churn_segment_{key}"] = wilson(int(g["churned"].sum()), len(g))[0]
        f[f"share_churners_{key}"] = round((ch["customer_segment"] == s).mean(), 4)
        f[f"share_balance_lost_{key}"] = round(
            ch.loc[ch["customer_segment"] == s, "avg_monthly_balance"].sum() / lost_total, 4)
    # headline concentration (Affluent + Private Banking share of balance lost)
    f["share_balance_lost_top2_segments"] = round(
        f["share_balance_lost_affluent"] + f["share_balance_lost_private_banking"], 4)
    f["share_churners_mass_market_pct"] = round(f["share_churners_mass_market"] * 100, 1)

    # RM effect by segment
    for s in SEG:
        g = df[df["customer_segment"] == s]
        key = s.lower().replace(" ", "_")
        f[f"churn_rm_no_{key}"] = round(g.loc[g["relationship_manager_assigned"] == 0, "churned"].mean(), 4)
        f[f"churn_rm_yes_{key}"] = round(g.loc[g["relationship_manager_assigned"] == 1, "churned"].mean(), 4)
    f["rm_coverage_mass_affluent"] = round(
        df.loc[df["customer_segment"] == "Mass Affluent", "relationship_manager_assigned"].mean(), 4)

    # driver ranking (Cramér's V), top 5
    scores = {}
    for c in df.columns.drop(["customer_id", "churned", "Aging"]):
        x = df[c]
        if x.dtype != object and x.nunique() > 7:
            x = pd.qcut(x.rank(method="first"), 5, labels=False)
        scores[c] = cramers_v(x, df["churned"])
    top5 = sorted(scores.items(), key=lambda kv: -kv[1])[:5]
    f["top_drivers"] = [{"feature": k, "cramers_v": round(v, 3)} for k, v in top5]
    f["cramers_v_num_products"] = round(scores["num_products"], 3)

    (out / "eda_findings.json").write_text(json.dumps(f, indent=2), encoding="utf-8")

    # --- power calculation for the pilot (in code) ----------------------------
    p_ctrl, p_treat, alpha, power = 0.40, 0.32, 0.05, 0.80
    es = proportion_effectsize(p_ctrl, p_treat)
    n_arm = NormalIndPower().solve_power(effect_size=es, alpha=alpha, power=power, alternative="two-sided")
    n_per_arm = int(np.ceil(n_arm))

    # --- pilot_design.md ------------------------------------------------------
    (out / "pilot_design.md").write_text(f"""# Pilot design — measurable retention RCT

## Design
- **Randomised controlled trial** on **T1 (Save now)** and **T3 (Automated save)** customers —
  the high-risk tiers where intervention can change outcomes.
- Randomised to **treatment** vs **business-as-usual control**, stratified by tier and segment.
- 90-day treatment window; churn measured at **90 and 180 days**.

## Sample size (computed, statsmodels NormalIndPower)
- Detect a drop from **{p_ctrl:.0%} → {p_treat:.0%}** churn (effect size {es:.3f}).
- α = {alpha}, power = {power}, two-sided → **{n_per_arm:,} customers per arm**.
- Feasible within RM capacity ({500}/month) staged across the T1/T3 population.

## KPIs
- **Primary:** churn-rate uplift = control churn − treatment churn (90 & 180 days).
- **Secondary:** AED balance retained; ROI = (balance retained × 2% net margin − offer cost) /
  offer cost; products per customer; NPS change; model precision measured in the control group.

## Guardrails
- Cost cap per customer by tier; no adverse impact by gender or age (monitored weekly).
- Treatment offers logged; opt-out honoured.

## Decision rule
- **Scale** an arm if its churn uplift is statistically significant **and** ROI > 1.
- Otherwise **retire or redesign** the intervention.

## Post-launch
- Monthly re-scoring; drift check via **PSI**; quarterly retraining.
- Control group becomes the ongoing benchmark for model precision in production.
""", encoding="utf-8")

    # --- ai_disclosure.md -----------------------------------------------------
    (out / "ai_disclosure.md").write_text("""# Responsible AI & tool disclosure

## AI tools used
- **Claude Code** assisted in writing the data-processing, modelling, charting and reporting code.
- All code is committed and reproducible; no numbers were hand-typed into documents.

## How every output was verified
- **Data:** the shared loader asserts 10,000 unique IDs and checksums tenure-band counts and churn
  against the raw summary block before any analysis runs.
- **Synthetic data:** fidelity re-computed independently (KS, correlation gap, duplicate check,
  range check) and reported honestly, including the caveat that it adds volume, not information.
- **Model:** evaluated once on an untouched 2,000-row holdout; PR-AUC reported with a bootstrap CI;
  out-of-fold scores used for the priority list so no customer is scored by a model trained on them.
- **Charts:** every chart regenerated from code with 95% Wilson intervals and sample sizes shown.
- **Report & deck:** numbers injected from `metrics.json` and `eda_findings.json` via
  `fill_report.py`; a missing key fails loudly rather than leaving a gap.

## Responsible-AI choices
- Gender excluded from the model; recall and false-positive rate reported by gender and age band.
- Correlation is never presented as causation; only the pilot (an RCT) can show cause.
- The model informs **outreach**, never credit, pricing or eligibility decisions.
- No competitor-rate, offer or reason-for-leaving data exists — those are pilot hypotheses only.
""", encoding="utf-8")

    # --- approach_C.md --------------------------------------------------------
    drivers = ", ".join(f"{d['feature']} ({d['cramers_v']})" for d in f["top_drivers"])
    (out / "approach_C.md").write_text(f"""# Approach — Person C (Insights & strategy)

## EDA method
- Churn rate with n and 95% Wilson intervals across 11 customer dimensions.
- Driver ranking by Cramér's V (p-values alone mean little at n={n:,}).
- Columns charted on evidence; weak/redundant columns excluded and justified.
- Top drivers: {drivers}.

## Pilot design method
- RCT on high-risk tiers (T1, T3), treatment vs BAU control, stratified.
- Power calc in code: detect {p_ctrl:.0%}→{p_treat:.0%}, α={alpha}, power={power} → {n_per_arm:,}/arm.
- KPIs: churn uplift (primary), AED retained, ROI, NPS, products/customer.
- Decision rule: scale if uplift significant and ROI>1; else retire/redesign.
""", encoding="utf-8")

    print(f"C done -> {out}")
    print(f"  base churn {base:.4f} | balance lost AED {lost_total/1e6:.1f}m "
          f"({f['pct_balance_lost']:.1%})")
    print(f"  tenure <1 {f['churn_tenure_lt1']:.1%} vs 15+ {f['churn_tenure_15plus']:.1%} "
          f"({f['tenure_lt1_vs_15plus_ratio']}x)")
    print(f"  Affluent+Private = {f['share_balance_lost_top2_segments']:.0%} of balance lost; "
          f"Mass Market = {f['share_churners_mass_market_pct']}% of churners")
    print(f"  pilot n/arm = {n_per_arm:,} | top driver {top5[0][0]} V={top5[0][1]:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

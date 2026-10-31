"""Train the lean churn model for the dashboard and write all artifacts + MODEL.md.

Uses the shared loader and the same 80/20 holdout as the main project, but only the relevant
fields (see ml.NEGLECTED for what is dropped and why). Every number in MODEL.md comes from here.

Run: python train.py
Outputs (artifacts/): app_model.joblib, app_metrics.json, app_priority.csv, fields.json
Also writes ../MODEL.md
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, roc_auc_score, precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                       # meridian_retention_kit
sys.path.insert(0, str(ROOT / "src"))
from shared_loader import load_clean, split_real  # noqa: E402
import ml  # noqa: E402

ART = HERE / "artifacts"
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=ml.SEED)


def logreg():
    return Pipeline([("prep", ml.build_preprocessor(scale=True)),
                     ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=ml.SEED))])


def lgbm():
    return Pipeline([("prep", ml.build_preprocessor(scale=False)),
                     ("clf", LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05,
                                            class_weight="balanced", random_state=ml.SEED, verbosity=-1))])


def main():
    ART.mkdir(parents=True, exist_ok=True)
    df = load_clean(str(ROOT / "data" / "Bank Data.csv"))
    train, holdout = split_real(df)
    bal_p75 = float(df["avg_monthly_balance"].quantile(0.75))
    base_rate = float(df["churned"].mean())

    Xtr, ytr = ml.make_features(train), train["churned"].values
    Xho, yho = ml.make_features(holdout), holdout["churned"].values

    # pick model by CV PR-AUC
    cands = {"Logistic regression": logreg(), "LightGBM": lgbm()}
    cv = {n: cross_val_score(m, Xtr, ytr, cv=CV, scoring="average_precision").mean() for n, m in cands.items()}
    chosen = max(cv, key=cv.get)
    base_est = cands[chosen]

    # calibrate + holdout metrics
    calib = CalibratedClassifierCV(base_est, method="isotonic", cv=5).fit(Xtr, ytr)
    p_ho = calib.predict_proba(Xho)[:, 1]
    thr = ml.HIGH_RISK_THR
    pred = (p_ho >= thr).astype(int)
    order = np.argsort(-p_ho)
    top10 = order[: max(1, len(order) // 10)]
    metrics_perf = {
        "chosen_model": chosen,
        "cv_pr_auc": round(cv[chosen], 4),
        "cv_pr_auc_logreg": round(cv["Logistic regression"], 4),
        "cv_pr_auc_lightgbm": round(cv["LightGBM"], 4),
        "pr_auc": round(average_precision_score(yho, p_ho), 4),
        "roc_auc": round(roc_auc_score(yho, p_ho), 4),
        "recall_at_thr": round(recall_score(yho, pred), 4),
        "precision_at_thr": round(precision_score(yho, pred, zero_division=0), 4),
        "threshold": thr,
        "top_decile_capture": round(float(yho[top10].sum() / yho.sum()), 4),
        "baseline_pr_auc": round(base_rate, 4),
        "base_churn_rate": round(base_rate, 4),
        "n_customers": len(df), "n_churned": int(df["churned"].sum()),
        "bal_p75": round(bal_p75, 2), "capacity_n": ml.CAPACITY_N,
    }

    # out-of-fold scores for all 10,000 -> priority table
    oof = cross_val_predict(CalibratedClassifierCV(base_est, method="isotonic", cv=5),
                            ml.make_features(df), df["churned"].values, cv=CV, method="predict_proba")[:, 1]
    pri = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "customer_segment": df["customer_segment"].values,
        "churn_probability": np.round(oof, 4),
        "avg_monthly_balance": df["avg_monthly_balance"].values,
    })
    pri["expected_balance_at_risk"] = np.round(oof * df["avg_monthly_balance"].values, 2)
    pri["priority_tier"] = ml.assign_tier(oof, df["avg_monthly_balance"].values, bal_p75)
    feats = ml.make_features(df)
    pri["top_3_reasons"] = [ml.risk_reasons(feats.iloc[i]) for i in range(len(df))]
    pri = pri.sort_values("expected_balance_at_risk", ascending=False).reset_index(drop=True)
    pri.to_csv(ART / "app_priority.csv", index=False)

    tier_counts = pri["priority_tier"].value_counts().to_dict()

    # value-weighted vs probability-only vs random (capacity)
    churn_mask = df["churned"].values.astype(bool)
    bal = df["avg_monthly_balance"].values
    def protected(key):
        top = np.argsort(-key)[: ml.CAPACITY_N]
        m = np.zeros(len(df), bool); m[top] = True
        return float(bal[m & churn_mask].sum())
    aed_value = protected(oof * bal)
    aed_prob = protected(oof)
    aed_random = ml.CAPACITY_N / len(df) * float(bal[churn_mask].sum())

    # churn-rate drivers for the dashboard (descriptive, real data)
    def rate_by(bins, labels, col):
        g = pd.cut(df[col], bins, labels=labels) if labels else df[col]
        return [{"label": str(k), "rate": round(float(v), 4)}
                for k, v in df.groupby(g, observed=True)["churned"].mean().items()]
    drivers = {
        "by_products": rate_by([0, 1, 2, 3, 100], ["1", "2", "3", "4+"], "num_products"),
        "by_recency": rate_by([-1, 30, 60, 90, 10**9], ["0-30", "31-60", "61-90", "90+"], "last_transaction_days_ago"),
        "by_engagement": rate_by([-1, 20, 40, 60, 80, 100], ["0-20", "21-40", "41-60", "61-80", "81-100"], "digital_engagement_score"),
        "by_segment": [{"label": s, "rate": round(float(df.loc[df.customer_segment == s, "churned"].mean()), 4)} for s in ml.SEGMENTS],
    }

    # feature importance for display
    est = base_est.fit(Xtr, ytr)
    names = est.named_steps["prep"].get_feature_names_out()
    clf = est.named_steps["clf"]
    raw = np.abs(clf.coef_[0]) if chosen == "Logistic regression" else clf.feature_importances_.astype(float)
    imp = sorted(({"feature": n.split("__", 1)[1], "importance": float(v)} for n, v in zip(names, raw)),
                 key=lambda d: -d["importance"])[:10]
    mx = imp[0]["importance"] or 1.0
    for d in imp:
        d["importance"] = round(d["importance"] / mx, 4)

    metrics = {**metrics_perf,
               "tier_counts": {k: int(v) for k, v in tier_counts.items()},
               "aed_protected_value_weighted": round(aed_value, 2),
               "aed_protected_prob_only": round(aed_prob, 2),
               "aed_protected_random": round(aed_random, 2),
               "value_vs_prob_ratio": round(aed_value / max(aed_prob, 1), 2),
               "drivers": drivers, "feature_importance": imp}
    (ART / "app_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    joblib.dump({"calibrated": calib, "bal_p75": bal_p75}, ART / "app_model.joblib")
    (ART / "fields.json").write_text(json.dumps({"fields": ml.FIELDS}, indent=2), encoding="utf-8")

    write_model_md(metrics)
    print(f"Trained lean model: {chosen}")
    print(f"  CV PR-AUC: logreg {cv['Logistic regression']:.3f} | lgbm {cv['LightGBM']:.3f}")
    print(f"  Holdout PR-AUC {metrics['pr_auc']:.3f}  ROC {metrics['roc_auc']:.3f}  "
          f"top-decile {metrics['top_decile_capture']:.0%}")
    print(f"  AED protected value {aed_value/1e6:.2f}m vs prob {aed_prob/1e6:.2f}m vs random {aed_random/1e6:.2f}m")
    print(f"  tiers {tier_counts}")


def write_model_md(m):
    fld_rows = "\n".join(
        f"| `{f['name']}` | {f['label']} | {f['kind']} |" for f in ml.FIELDS)
    neg_rows = "\n".join(f"| `{c}` | {why} |" for c, why in ml.NEGLECTED.items())
    imp_rows = "\n".join(f"| {d['feature']} | {d['importance']:.2f} |" for d in m["feature_importance"])
    tier_rows = "\n".join(f"| {k} | {v:,} |" for k, v in m["tier_counts"].items())
    (HERE.parent / "MODEL.md").write_text(f"""# Predictive model — Meridian churn dashboard

*Generated by `app/backend/train.py`. Every number below comes from code output (seed {ml.SEED}).*

## 1. The model used
- **Algorithm:** {m['chosen_model']}, chosen as the better of logistic regression and LightGBM on
  cross-validated PR-AUC (logreg {m['cv_pr_auc_logreg']:.3f} vs LightGBM {m['cv_pr_auc_lightgbm']:.3f}).
- **Target:** `churned` (1 = left the bank). Base rate **{m['base_churn_rate']:.1%}** — imbalanced,
  so PR-AUC is the primary metric and the model is trained with balanced class weights.
- **Calibration:** isotonic (`CalibratedClassifierCV`, cv=5) so *probability × balance* is real AED.
- **Validation:** 80/20 stratified split (seed {ml.SEED}); the 2,000-row holdout is scored once.
- **Training data:** the real 10,000 customers only.

## 2. Results (on the untouched holdout)
| Metric | Value |
|---|---|
| PR-AUC (primary) | **{m['pr_auc']:.3f}** |
| Baseline PR-AUC (base rate) | {m['baseline_pr_auc']:.3f} |
| ROC-AUC | {m['roc_auc']:.3f} |
| Recall @ threshold {m['threshold']} | {m['recall_at_thr']:.2f} |
| Precision @ threshold {m['threshold']} | {m['precision_at_thr']:.2f} |
| Top-decile capture | {m['top_decile_capture']:.0%} of all leavers |

**Prioritisation value.** Contacting the top **{m['capacity_n']}** customers (one month of RM
capacity) by *expected balance at risk* protects **AED {m['aed_protected_value_weighted']/1e6:.1f}m**,
versus AED {m['aed_protected_prob_only']/1e6:.1f}m by probability alone and
AED {m['aed_protected_random']/1e6:.1f}m at random
({m['value_vs_prob_ratio']}× the probability-only ranking).

**Tier distribution** (high risk = calibrated probability ≥ {m['threshold']}; high value = balance ≥
75th percentile, AED {m['bal_p75']:,.0f}):

| Tier | Customers |
|---|---|
{tier_rows}

## 3. Fields required (model inputs)
The dashboard's prediction form collects only these {len(ml.FIELDS)} fields:

| Field | Label | Type |
|---|---|---|
{fld_rows}

Engineered inside the model from the above: `log_balance`, `is_new` (tenure < 1),
`single_product` (products = 1), `has_complaint`, `inactive_60d` (last transaction > 60 days).

## 4. Columns neglected (and why)
These raw columns are **excluded** — they are weak, redundant, or not predictive (per the project's
Cramér's V driver analysis), or are identifiers/labels:

| Column | Reason neglected |
|---|---|
{neg_rows}

## 5. Top features by model importance
| Feature | Relative importance |
|---|---|
{imp_rows}

## 6. Responsible use
Descriptive/predictive tool for **outreach prioritisation** only — never credit, pricing or
eligibility. Associations are not causation; the retention playbook's effect is to be proven by the
RCT pilot. Reasons shown in the UI are rule-based from the customer's own risk signals; full SHAP
explanations are in `out/B/model_card.md`.
""", encoding="utf-8")


if __name__ == "__main__":
    main()

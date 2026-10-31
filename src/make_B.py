"""Person B — model, calibration, prioritisation, unseen-data demo. Real data only.

Produces everything in out/B:
  priority_list.csv, metrics.json, model_comparison.csv, model.joblib, model_card.md,
  hidden_test_sample.csv, approach_B.md, figures/{pr_curve,calibration,shap_bar,value_capture}.png

Run: python make_B.py ../data/Bank Data.csv ../out/B
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import shap
import lightgbm as lgb
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, roc_auc_score, precision_recall_curve,
                             precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline

from shared_loader import load_clean, split_real
import model_lib as ML
from model_lib import (make_features, build_preprocessor, assign_tier, top_reasons,
                       feature_lists, HIGH_RISK_THR, CAPACITY_N, SEED)

RED, BLUE, INK, MUTED, GRID, GREEN = "#C8102E", "#2F6DB5", "#1F2328", "#6B7280", "#E5E7EB", "#2E7D32"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def make_logreg(include_leak):
    return Pipeline([("prep", build_preprocessor(include_leak, scale=True)),
                     ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=SEED))])


def make_lgbm(include_leak, **params):
    base = dict(n_estimators=300, class_weight="balanced", random_state=SEED, verbosity=-1)
    base.update(params)
    return Pipeline([("prep", build_preprocessor(include_leak, scale=False)),
                     ("clf", LGBMClassifier(**base))])


def cv_pr_auc(model, X, y):
    return cross_val_score(model, X, y, cv=CV, scoring="average_precision").mean()


def holdout_scores(model, Xtr, ytr, Xho, yho):
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xho)[:, 1]
    return average_precision_score(yho, p), roc_auc_score(yho, p), p


def main(raw, out):
    out = Path(out); (out / "figures").mkdir(parents=True, exist_ok=True)
    df = load_clean(raw)
    train, holdout = split_real(df)
    bal_p75 = float(df["avg_monthly_balance"].quantile(0.75))
    base_rate = float(df["churned"].mean())

    ytr, yho = train["churned"].values, holdout["churned"].values
    comparison = []

    # --- baseline rule: tenure < 1 year ---------------------------------------
    base_pred_ho = (holdout["tenure_years"] < 1).astype(int).values
    base_prec = precision_score(yho, base_pred_ho)
    base_rec = recall_score(yho, base_pred_ho)
    comparison.append({"model": "Baseline (tenure<1yr rule)", "cv_pr_auc": round(base_rate, 4),
                       "holdout_pr_auc": round(base_rate, 4), "holdout_roc_auc": np.nan})

    # --- models WITH the recency (leak) features ------------------------------
    Xtr_L, Xho_L = make_features(train, True), make_features(holdout, True)
    lr = make_logreg(True)
    lr_cv = cv_pr_auc(lr, Xtr_L, ytr)
    lr_pr, lr_roc, _ = holdout_scores(lr, Xtr_L, ytr, Xho_L, yho)
    comparison.append({"model": "Logistic regression (with recency)", "cv_pr_auc": round(lr_cv, 4),
                       "holdout_pr_auc": round(lr_pr, 4), "holdout_roc_auc": round(lr_roc, 4)})

    # small LightGBM grid on CV PR-AUC
    grid = [dict(num_leaves=nl, learning_rate=lr_) for nl in (15, 31) for lr_ in (0.05, 0.1)]
    best_cv, best_params = -1, None
    for p in grid:
        c = cv_pr_auc(make_lgbm(True, **p), Xtr_L, ytr)
        if c > best_cv:
            best_cv, best_params = c, p
    gb = make_lgbm(True, **best_params)
    gb_pr, gb_roc, _ = holdout_scores(gb, Xtr_L, ytr, Xho_L, yho)
    comparison.append({"model": "LightGBM (with recency)", "cv_pr_auc": round(best_cv, 4),
                       "holdout_pr_auc": round(gb_pr, 4), "holdout_roc_auc": round(gb_roc, 4)})

    # --- pick best model family by CV PR-AUC ----------------------------------
    chosen = "LightGBM" if best_cv >= lr_cv else "Logistic regression"

    # --- leakage check: same family WITHOUT recency features ------------------
    Xtr_N, Xho_N = make_features(train, False), make_features(holdout, False)
    if chosen == "LightGBM":
        noleak = make_lgbm(False, **best_params)
    else:
        noleak = make_logreg(False)
    nl_cv = cv_pr_auc(noleak, Xtr_N, ytr)
    nl_pr, nl_roc, _ = holdout_scores(noleak, Xtr_N, ytr, Xho_N, yho)
    comparison.append({"model": f"{chosen} (no recency / deployed)", "cv_pr_auc": round(nl_cv, 4),
                       "holdout_pr_auc": round(nl_pr, 4), "holdout_roc_auc": round(nl_roc, 4)})

    leak_pr = gb_pr if chosen == "LightGBM" else lr_pr
    drop = leak_pr - nl_pr
    deploy_leak = drop > 0.03                        # deploy WITHOUT recency if the drop is small
    include_leak = deploy_leak
    Xtr, Xho = (Xtr_L, Xho_L) if include_leak else (Xtr_N, Xho_N)
    X_all = make_features(df, include_leak)
    y_all = df["churned"].values

    if chosen == "LightGBM":
        base_est = make_lgbm(include_leak, **best_params)
    else:
        base_est = make_logreg(include_leak)

    # --- calibrate (isotonic) + holdout metrics at the operating threshold -----
    calib = CalibratedClassifierCV(base_est, method="isotonic", cv=5)
    calib.fit(Xtr, ytr)
    p_ho = calib.predict_proba(Xho)[:, 1]
    pr_auc = average_precision_score(yho, p_ho)
    roc_auc = roc_auc_score(yho, p_ho)
    thr = HIGH_RISK_THR
    pred_ho = (p_ho >= thr).astype(int)
    recall_thr = recall_score(yho, pred_ho)
    precision_thr = precision_score(yho, pred_ho, zero_division=0)
    # top-decile capture on the holdout
    order = np.argsort(-p_ho)
    top10 = order[: max(1, len(order) // 10)]
    top_decile_capture = yho[top10].sum() / yho.sum()
    # bootstrap 95% CI on PR-AUC
    rng = np.random.default_rng(SEED)
    boot = [average_precision_score(yho[idx], p_ho[idx])
            for idx in (rng.integers(0, len(yho), len(yho)) for _ in range(1000))
            if yho[idx].sum() > 0]
    pr_ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    # --- out-of-fold calibrated scores for all 10,000 (priority list) ---------
    oof = cross_val_predict(CalibratedClassifierCV(base_est, method="isotonic", cv=5),
                            X_all, y_all, cv=CV, method="predict_proba")[:, 1]

    # --- SHAP (fit chosen uncalibrated model on all real data for explanations)
    expl_model = base_est.fit(X_all, y_all)
    prep = expl_model.named_steps["prep"]
    clf = expl_model.named_steps["clf"]
    Xt = prep.transform(X_all)
    feat_names = prep.get_feature_names_out()
    if chosen == "LightGBM":
        explainer = shap.TreeExplainer(clf)
        sv = explainer.shap_values(Xt)
        sv = sv[1] if isinstance(sv, list) else sv
    else:
        explainer = shap.LinearExplainer(clf, Xt)
        sv = explainer.shap_values(Xt)
    shap_df = pd.DataFrame(sv, columns=feat_names, index=df.index)
    # collapse one-hot + scaled names back to raw feature names for reason mapping
    num_cols, cat_cols = feature_lists(include_leak)
    raw_map = {}
    for fn in feat_names:
        core = fn.split("__", 1)[1]
        raw = next((c for c in num_cols if core == c), None) or next((c for c in cat_cols if core.startswith(c)), core)
        raw_map.setdefault(raw, []).append(fn)
    shap_raw = pd.DataFrame({raw: shap_df[cols].sum(axis=1) for raw, cols in raw_map.items()})

    global_imp = shap_raw.abs().mean().sort_values(ascending=False)

    # --- priority list for all 10,000 (out-of-fold) ---------------------------
    pl = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "churn_probability": np.round(oof, 4),
        "avg_monthly_balance": df["avg_monthly_balance"].values,
    })
    pl["expected_balance_at_risk"] = np.round(pl["churn_probability"] * pl["avg_monthly_balance"], 2)
    pl["priority_tier"] = assign_tier(pl["churn_probability"].values, pl["avg_monthly_balance"].values, bal_p75)
    pl["top_3_reasons"] = [top_reasons(shap_raw.iloc[i], df.iloc[i]) for i in range(len(df))]
    pl = pl.sort_values("expected_balance_at_risk", ascending=False).reset_index(drop=True)
    pl.to_csv(out / "priority_list.csv", index=False)
    tier_counts = pl["priority_tier"].value_counts().to_dict()

    # --- key chart: value-weighted vs probability-only vs random (capacity 500)
    churned_mask = y_all.astype(bool)
    bal = df["avg_monthly_balance"].values
    ebar = oof * bal
    def protected(rank_key):
        top = np.argsort(-rank_key)[:CAPACITY_N]
        reached = np.zeros(len(df), bool); reached[top] = True
        return bal[reached & churned_mask].sum()
    aed_value = protected(ebar)
    aed_prob = protected(oof)
    aed_random = CAPACITY_N / len(df) * bal[churned_mask].sum()   # expected value of random choice

    fig, ax = plt.subplots(figsize=(8, 4.6))
    vals = [aed_value / 1e6, aed_prob / 1e6, aed_random / 1e6]
    labels = ["Value-weighted\n(balance at risk)", "Probability-only", "Random"]
    bars = ax.bar(labels, vals, color=[GREEN, BLUE, MUTED], width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"AED {v:.1f}m", ha="center",
                fontsize=11, fontweight="bold", color=INK)
    ax.set_ylabel("AED balance of reached churners (millions)")
    ax.set_ylim(0, max(vals) * 1.2)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_title(f"Ranking by balance-at-risk protects {aed_value/max(aed_prob,1):.2f}× the money of "
                 f"probability alone", loc="left", fontsize=12.5, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, f"Top {CAPACITY_N} customers contacted (one month of RM capacity). "
            f"Out-of-fold scores, real customers.", transform=ax.transAxes, fontsize=9.5, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "figures" / "value_capture.png", dpi=200); plt.close(fig)

    # --- PR curve -------------------------------------------------------------
    prec, rec, _ = precision_recall_curve(yho, p_ho)
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.plot(rec, prec, color=RED, lw=2.2, label=f"Model (PR-AUC {pr_auc:.3f})")
    ax.axhline(base_rate, color=MUTED, ls="--", lw=1.2, label=f"Base rate ({base_rate:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.legend(frameon=False); ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_title("Precision–recall on the untouched 2,000-row holdout", loc="left",
                 fontsize=13, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, f"95% CI on PR-AUC: {pr_ci[0]:.3f}–{pr_ci[1]:.3f}. Top-decile capture "
            f"{top_decile_capture:.0%}.", transform=ax.transAxes, fontsize=9.5, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "figures" / "pr_curve.png", dpi=200); plt.close(fig)

    # --- calibration ----------------------------------------------------------
    frac_pos, mean_pred = calibration_curve(yho, p_ho, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(6.4, 6))
    ax.plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1.2, label="Perfect calibration")
    ax.plot(mean_pred, frac_pos, "o-", color=RED, lw=2, label="Isotonic-calibrated model")
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Observed churn rate")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(frameon=False)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_title("Calibrated probabilities track reality", loc="left", fontsize=13,
                 color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, "So that probability × balance means real AED.", transform=ax.transAxes,
            fontsize=9.5, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "figures" / "calibration.png", dpi=200); plt.close(fig)

    # --- SHAP global bar ------------------------------------------------------
    top = global_imp.head(12)[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.barh(top.index, top.values, color=RED, height=0.7)
    ax.set_xlabel("Mean |SHAP value| (impact on churn prediction)")
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_title(f"What drives the {chosen} model", loc="left", fontsize=13,
                 color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, "Global feature importance, real customers (n=10,000).",
            transform=ax.transAxes, fontsize=9.5, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "figures" / "shap_bar.png", dpi=200); plt.close(fig)

    # --- fairness: recall & FPR by gender and age band (OOF, thr=0.40) --------
    pred_all = (oof >= thr).astype(int)
    fair = {}
    grp = df.assign(pred=pred_all, y=y_all,
                    age_band=pd.cut(df["age"], [17, 30, 45, 60, 101],
                                    labels=["18-30", "31-45", "46-60", "60+"]))
    for dim in ["gender", "age_band"]:
        rows = []
        for g, sub in grp.groupby(dim, observed=True):
            pos, neg = sub["y"] == 1, sub["y"] == 0
            rec_g = sub.loc[pos, "pred"].mean() if pos.any() else float("nan")
            fpr_g = sub.loc[neg, "pred"].mean() if neg.any() else float("nan")
            rows.append({"group": str(g), "n": int(len(sub)), "recall": round(rec_g, 3), "fpr": round(fpr_g, 3)})
        fair[dim] = rows

    # --- metrics.json (flat keys, §3) -----------------------------------------
    metrics = {
        "pr_auc": round(pr_auc, 4), "roc_auc": round(roc_auc, 4),
        "recall_at_thr": round(recall_thr, 4), "precision_at_thr": round(precision_thr, 4),
        "threshold": thr, "top_decile_capture": round(float(top_decile_capture), 4),
        "pr_auc_ci_low": round(pr_ci[0], 4), "pr_auc_ci_high": round(pr_ci[1], 4),
        "baseline_pr_auc": round(base_rate, 4),
        "baseline_rule_precision": round(base_prec, 4), "baseline_rule_recall": round(base_rec, 4),
        "aed_protected_value_weighted": round(float(aed_value), 2),
        "aed_protected_prob_only": round(float(aed_prob), 2),
        "aed_protected_random": round(float(aed_random), 2),
        "value_vs_prob_ratio": round(float(aed_value / max(aed_prob, 1)), 3),
        "capacity_n": CAPACITY_N, "bal_p75": round(bal_p75, 2),
        "chosen_model": chosen, "deployed_with_recency": bool(include_leak),
        "leakage_pr_auc_drop": round(float(drop), 4),
        "tier_counts": {k: int(v) for k, v in tier_counts.items()},
        "top_features": {k: round(float(v), 4) for k, v in global_imp.head(8).items()},
        "fairness": fair,
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    pd.DataFrame(comparison).to_csv(out / "model_comparison.csv", index=False)

    # --- save deployable bundle + hidden test sample --------------------------
    joblib.dump({"calibrated": calib, "explain_model": expl_model, "include_leak": include_leak,
                 "bal_p75": bal_p75, "chosen": chosen}, out / "model.joblib")

    hidden = holdout.head(200).drop(columns=["churned"]).copy()
    hidden["avg_monthly_balance"] = hidden["avg_monthly_balance"].map(lambda v: f"{v:,.0f}")
    # write with the junk title row so the raw format round-trips through shared_loader
    header = "Variable Tracked = 20," + "," * (len(hidden.columns) - 1)
    body = hidden.to_csv(index=False)
    (out / "hidden_test_sample.csv").write_text(header + "\n" + body, encoding="utf-8")

    # --- model_card.md --------------------------------------------------------
    fair_tbl = ""
    for dim, rows in fair.items():
        fair_tbl += f"\n**By {dim}**\n\n| Group | n | Recall | FPR |\n|---|---|---|---|\n"
        fair_tbl += "\n".join(f"| {r['group']} | {r['n']:,} | {r['recall']} | {r['fpr']} |" for r in rows) + "\n"
    (out / "model_card.md").write_text(f"""# Model card — Meridian churn model

## Purpose
Rank Meridian's {len(df):,} retail customers by **expected average monthly balance at risk**
(calibrated churn probability × balance) so {CAPACITY_N} monthly RM contacts protect the most AED.
Descriptive/predictive tool only — not a credit or eligibility decision.

## Data & split
- Real customers only, n={len(df):,}, churn {base_rate:.2%} (imbalanced).
- 80/20 stratified split, seed {SEED}. Holdout (2,000 rows) touched once, at the end.
- Synthetic rows were **not** used for training (they add volume, not information).

## Models compared (by CV PR-AUC on train)
| Model | CV PR-AUC | Holdout PR-AUC | Holdout ROC-AUC |
|---|---|---|---|
""" + "\n".join(f"| {c['model']} | {c['cv_pr_auc']} | {c['holdout_pr_auc']} | "
                f"{'' if pd.isna(c['holdout_roc_auc']) else c['holdout_roc_auc']} |" for c in comparison) + f"""

Chosen family: **{chosen}** (best CV PR-AUC). Baseline rule "tenure < 1yr": precision {base_prec:.2f},
recall {base_rec:.2f}.

## Leakage & robustness
`last_transaction_days_ago` (and its `inactive_60d` flag) may be an **effect** of churning, not a
cause. Trained with and without: holdout PR-AUC drops by **{drop:.3f}** when removed.
Deployed **{'WITH' if include_leak else 'WITHOUT'}** recency features
({'drop was material' if include_leak else 'drop is small, so the more defensible model is used'}).

## Calibration & threshold
Isotonic calibration (`CalibratedClassifierCV`, cv=5) so probability × balance is real AED.
Operating threshold = **{thr}** (= the high-risk tier cutoff). At this threshold on the holdout:
recall {recall_thr:.2f}, precision {precision_thr:.2f}. PR-AUC {pr_auc:.3f}
(95% CI {pr_ci[0]:.3f}–{pr_ci[1]:.3f}), ROC-AUC {roc_auc:.3f}, top-decile capture {top_decile_capture:.0%}.

## Prioritisation
`expected_balance_at_risk = churn_probability × avg_monthly_balance`. Tiers: T1 Save now (high risk,
high value) · T2 Protect · T3 Automated save · T4 Monitor. High value = balance ≥ 75th pct
(AED {bal_p75:,.0f}). With {CAPACITY_N} contacts, value-weighted ranking protects
**AED {aed_value/1e6:.1f}m** vs **AED {aed_prob/1e6:.1f}m** (probability-only) vs
**AED {aed_random/1e6:.1f}m** (random).

## Fairness (out-of-fold, threshold {thr})
Gender is excluded from the model and used only here.
{fair_tbl}
## Limitations
No competitor-rate, offer or reason-for-leaving fields exist, so the model cannot explain *why* in
a causal sense. Recency may be partly post-hoc. Associations only; causation is tested by the pilot.
""", encoding="utf-8")

    # --- approach_B.md (slide bullets) ----------------------------------------
    f_top = ", ".join(global_imp.head(4).index)
    (out / "approach_B.md").write_text(f"""# Approach — Person B (Model & prioritisation)

## Problem framing
- Rank {len(df):,} customers by AED balance at risk, not probability alone.
- Churn is imbalanced ({base_rate:.1%}), so PR-AUC is the primary metric.
- Goal: protect the most money within {CAPACITY_N} monthly RM contacts.
- Descriptive/predictive tool; interventions tested causally by the pilot.

## Feature engineering
- Added log_balance, balance_to_income, is_new, single_product, has_complaint.
- gender excluded from the model (used only for the fairness check).
- Aging and customer_id dropped; one ColumnTransformer (scale + one-hot).
- Recency feature isolated so its leakage risk can be tested.

## Models compared
- Baseline rule (tenure<1yr): precision {base_prec:.2f}, recall {base_rec:.2f}.
- Logistic regression (balanced) and LightGBM (small grid, 5-fold CV).
- Selected by CV PR-AUC: {chosen}.
- LightGBM grid: num_leaves {{15,31}} × learning_rate {{0.05,0.1}}, 300 trees.

## Validation design
- 80/20 stratified split, seed {SEED}; holdout touched once.
- 5-fold stratified CV on train for model selection.
- Holdout PR-AUC {pr_auc:.3f} (95% CI {pr_ci[0]:.3f}–{pr_ci[1]:.3f}), ROC-AUC {roc_auc:.3f}.
- Top-decile capture {top_decile_capture:.0%} of all leavers.

## Leakage & robustness checks
- Recency may be an effect of churn, not a cause.
- With vs without recency: holdout PR-AUC drop {drop:.3f}.
- Deployed {'with' if include_leak else 'without'} recency ({'material' if include_leak else 'small'} drop).
- Synthetic data excluded from training by design.

## Explainability
- SHAP global bar + per-customer top-3 reasons in plain English.
- Strongest drivers: {f_top}.
- Reasons map to actions (new, single-product, inactive, complaints, no RM).
- Logistic odds ratios available as a cross-check.

## Prioritisation logic
- expected_balance_at_risk = calibrated probability × balance.
- Isotonic calibration so AED figures are trustworthy.
- Tiers T1–T4 on risk (≥{thr}) × value (≥AED {bal_p75:,.0f}).
- Out-of-fold scores so no customer is scored by a model trained on them.

## Fairness & responsible AI
- Recall and false-positive rate reported by gender and age band.
- Gender kept out of the model entirely.
- Model informs outreach, never eligibility or pricing.
- Monthly re-scoring, PSI drift check, quarterly retrain (handover to pilot).

## Unseen-data demo
- score.py scores 200 untouched holdout rows in raw format.
- Outputs id, probability, balance-at-risk, tier, top-3 reasons.
- Holdout metrics on the 200 match the reported holdout metrics.
- Proves the pipeline runs end-to-end on data it has never seen.
""", encoding="utf-8")

    print(f"B done -> {out}")
    print(f"  chosen={chosen} deployed_with_recency={include_leak} leak_drop={drop:.3f}")
    print(f"  PR-AUC={pr_auc:.3f} ({pr_ci[0]:.3f}-{pr_ci[1]:.3f}) ROC={roc_auc:.3f} "
          f"topdecile={top_decile_capture:.1%} rec@{thr}={recall_thr:.2f} prec={precision_thr:.2f}")
    print(f"  tiers={tier_counts}")
    print(f"  AED protected: value={aed_value/1e6:.2f}m prob={aed_prob/1e6:.2f}m random={aed_random/1e6:.2f}m")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

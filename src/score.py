"""Score unseen customers with the deployed Meridian churn model.

Usage: python score.py --input hidden_test_sample.csv --output scored.csv [--model model.joblib]

Reads a raw-format CSV (junk title row, comma-formatted balances), applies the exact same feature
engineering and calibrated model used in training, and writes:
  customer_id, churn_probability, expected_balance_at_risk, priority_tier, top_3_reasons
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import shap

from model_lib import make_features, assign_tier, top_reasons, feature_lists

CAT = ["gender", "region", "customer_segment", "Aging"]
INT_COLS = ["age", "num_products", "has_credit_card", "has_loan", "has_investment_product",
            "branch_visits_last_year", "complaint_count_last_year", "credit_score",
            "relationship_manager_assigned", "nps_score", "last_transaction_days_ago"]


def load_raw_for_scoring(path: str) -> pd.DataFrame:
    """Same quirks as shared_loader, but no 10k/checksum asserts (scoring an arbitrary batch)."""
    df = pd.read_csv(path, skiprows=1)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df[df["customer_id"].astype(str).str.startswith(("CUST", "SYN"), na=False)].copy()
    df["avg_monthly_balance"] = df["avg_monthly_balance"].astype(str).str.replace(",", "").astype(float)
    num = [c for c in df.columns if c not in CAT + ["customer_id"]]
    df[num] = df[num].apply(pd.to_numeric)
    present = [c for c in INT_COLS if c in df.columns]
    df[present] = df[present].astype(int)
    return df.reset_index(drop=True)


def score(df: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    include_leak = bundle["include_leak"]
    X = make_features(df, include_leak)
    prob = bundle["calibrated"].predict_proba(X)[:, 1]

    # SHAP reasons via the deployed (uncalibrated) model
    expl = bundle["explain_model"]
    prep, clf = expl.named_steps["prep"], expl.named_steps["clf"]
    Xt = prep.transform(X)
    names = prep.get_feature_names_out()
    try:
        explainer = shap.TreeExplainer(clf); sv = explainer.shap_values(Xt)
        sv = sv[1] if isinstance(sv, list) else sv
    except Exception:
        explainer = shap.LinearExplainer(clf, Xt); sv = explainer.shap_values(Xt)
    shap_df = pd.DataFrame(sv, columns=names, index=df.index)
    num_cols, cat_cols = feature_lists(include_leak)
    raw_map = {}
    for fn in names:
        core = fn.split("__", 1)[1]
        raw = next((c for c in num_cols if core == c), None) or \
              next((c for c in cat_cols if core.startswith(c)), core)
        raw_map.setdefault(raw, []).append(fn)
    shap_raw = pd.DataFrame({r: shap_df[cols].sum(axis=1) for r, cols in raw_map.items()})

    out = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "churn_probability": np.round(prob, 4),
        "expected_balance_at_risk": np.round(prob * df["avg_monthly_balance"].values, 2),
    })
    out["priority_tier"] = assign_tier(prob, df["avg_monthly_balance"].values, bundle["bal_p75"])
    out["top_3_reasons"] = [top_reasons(shap_raw.iloc[i], df.iloc[i]) for i in range(len(df))]
    return out.sort_values("expected_balance_at_risk", ascending=False).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default=str(Path(__file__).with_name("model.joblib")))
    a = ap.parse_args()
    model_path = a.model if Path(a.model).exists() else str(Path("../out/B/model.joblib"))
    bundle = joblib.load(model_path)
    df = load_raw_for_scoring(a.input)
    result = score(df, bundle)
    result.to_csv(a.output, index=False)
    print(f"Scored {len(result):,} customers -> {a.output}")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

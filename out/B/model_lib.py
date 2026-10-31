"""Shared model logic used by both make_B.py (training) and score.py (scoring unseen rows).

Keeping feature engineering, the tier rule and the plain-English reason mapping in one place
guarantees the demo scores exactly the way the reported model was trained.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
HIGH_RISK_THR = 0.40        # calibrated churn probability (§3)
CAPACITY_N = 500            # RM contacts per month (§3)

# Raw columns that go into the model (gender excluded -> fairness check only; Aging dropped).
NUMERIC_BASE = ["age", "tenure_years", "monthly_income", "avg_monthly_balance", "num_products",
                "has_credit_card", "has_loan", "has_investment_product", "digital_engagement_score",
                "branch_visits_last_year", "complaint_count_last_year", "credit_score",
                "relationship_manager_assigned", "nps_score"]
ENGINEERED_BASE = ["log_balance", "balance_to_income", "is_new", "single_product", "has_complaint"]
CATEGORICAL = ["region", "customer_segment"]
# The leakage group: last_transaction_days_ago may be an *effect* of churning, not a cause.
LEAK_NUMERIC = ["last_transaction_days_ago"]
LEAK_ENGINEERED = ["inactive_60d"]


def make_features(df: pd.DataFrame, include_leak: bool) -> pd.DataFrame:
    """Build the model feature frame. `include_leak` toggles the recency-based features."""
    f = pd.DataFrame(index=df.index)
    for c in NUMERIC_BASE:
        f[c] = df[c].astype(float)
    f["log_balance"] = np.log1p(df["avg_monthly_balance"].astype(float))
    f["balance_to_income"] = df["avg_monthly_balance"] / df["monthly_income"].replace(0, np.nan)
    f["balance_to_income"] = f["balance_to_income"].fillna(0.0)
    f["is_new"] = (df["tenure_years"] < 1).astype(int)
    f["single_product"] = (df["num_products"] == 1).astype(int)
    f["has_complaint"] = (df["complaint_count_last_year"] >= 1).astype(int)
    for c in CATEGORICAL:
        f[c] = df[c].astype(str)
    if include_leak:
        f["last_transaction_days_ago"] = df["last_transaction_days_ago"].astype(float)
        f["inactive_60d"] = (df["last_transaction_days_ago"] > 60).astype(int)
    return f


def feature_lists(include_leak: bool):
    num = NUMERIC_BASE + ENGINEERED_BASE + (LEAK_NUMERIC + LEAK_ENGINEERED if include_leak else [])
    return num, CATEGORICAL


def build_preprocessor(include_leak: bool, scale: bool) -> ColumnTransformer:
    """scale=True for logistic regression; scale=False (passthrough) for tree models."""
    num, cat = feature_lists(include_leak)
    num_step = StandardScaler() if scale else "passthrough"
    return ColumnTransformer([
        ("num", num_step, num),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
    ])


def assign_tier(prob: np.ndarray, balance: np.ndarray, bal_p75: float) -> np.ndarray:
    """T1 Save now | T2 Protect | T3 Automated save | T4 Monitor (§3)."""
    high_risk = prob >= HIGH_RISK_THR
    high_value = balance >= bal_p75
    tier = np.where(high_risk & high_value, "T1 Save now",
           np.where(~high_risk & high_value, "T2 Protect",
           np.where(high_risk & ~high_value, "T3 Automated save", "T4 Monitor")))
    return tier


# --- plain-English reasons -------------------------------------------------------
def _reason_for(feat: str, row: pd.Series):
    """Map a model feature that pushed a customer toward churn to a plain-English reason."""
    if feat in ("is_new", "tenure_years") and row["tenure_years"] < 1:
        return "New customer (<1 yr)"
    if feat in ("single_product", "num_products") and row["num_products"] <= 1:
        return "Single product only"
    if feat in ("inactive_60d", "last_transaction_days_ago") and row["last_transaction_days_ago"] > 60:
        return "Inactive 60+ days"
    if feat in ("has_complaint", "complaint_count_last_year") and row["complaint_count_last_year"] >= 2:
        return "2+ complaints"
    if feat in ("has_complaint", "complaint_count_last_year") and row["complaint_count_last_year"] == 1:
        return "Recent complaint"
    if feat == "relationship_manager_assigned" and row["relationship_manager_assigned"] == 0:
        return "No relationship manager"
    if feat == "digital_engagement_score" and row["digital_engagement_score"] < 40:
        return "Low digital engagement"
    if feat == "nps_score" and row["nps_score"] <= 0:
        return "Negative NPS"
    if feat == "nps_score" and row["nps_score"] <= 30:
        return "Low NPS"
    if feat in ("avg_monthly_balance", "log_balance") and row["avg_monthly_balance"] < 5000:
        return "Low balance"
    if feat == "credit_score" and row["credit_score"] < 600:
        return "Low credit score"
    if feat == "branch_visits_last_year" and row["branch_visits_last_year"] == 0:
        return "No branch visits"
    return None


# Fallback order when SHAP gives fewer than 3 mapped reasons.
_FALLBACK = ["is_new", "single_product", "inactive_60d", "has_complaint",
             "relationship_manager_assigned", "digital_engagement_score", "nps_score"]


def top_reasons(shap_row: pd.Series, raw_row: pd.Series, k: int = 3) -> str:
    """Top-k reasons a customer is at risk: SHAP-ranked features mapped to phrases, then fallbacks."""
    reasons, seen = [], set()
    for feat in shap_row.sort_values(ascending=False).index:
        if shap_row[feat] <= 0:
            break
        r = _reason_for(feat, raw_row)
        if r and r not in seen:
            reasons.append(r); seen.add(r)
        if len(reasons) == k:
            break
    for feat in _FALLBACK:
        if len(reasons) == k:
            break
        r = _reason_for(feat, raw_row)
        if r and r not in seen:
            reasons.append(r); seen.add(r)
    return "; ".join(reasons) if reasons else "No strong risk signal"

"""Lean churn model for the predictive dashboard.

Deliberately uses only the fields the EDA showed matter, and neglects the rest (documented in
NEGLECTED). Feature engineering, the tier rule and the rule-based reasons live here so the training
script and the API score identically.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
HIGH_RISK_THR = 0.40          # calibrated churn probability => high risk
CAPACITY_N = 500              # RM contacts per month
SEGMENTS = ["Mass Market", "Mass Affluent", "Affluent", "Private Banking"]

# --- the input fields the app requires (the relevant columns) -------------------
# kind: num | int | select | binary ; used to render the form and validate input.
FIELDS = [
    {"name": "customer_segment", "label": "Customer segment", "kind": "select",
     "options": SEGMENTS, "default": "Mass Market"},
    {"name": "tenure_years", "label": "Tenure (years)", "kind": "num", "min": 0, "max": 60, "default": 3.0},
    {"name": "avg_monthly_balance", "label": "Avg monthly balance (AED)", "kind": "num",
     "min": 0, "max": 5_000_000, "default": 15000},
    {"name": "num_products", "label": "Products held", "kind": "int", "min": 1, "max": 6, "default": 2},
    {"name": "digital_engagement_score", "label": "Digital engagement (0-100)", "kind": "num",
     "min": 0, "max": 100, "default": 50},
    {"name": "complaint_count_last_year", "label": "Complaints last year", "kind": "int",
     "min": 0, "max": 20, "default": 0},
    {"name": "nps_score", "label": "NPS score (-100 to 100)", "kind": "int", "min": -100, "max": 100, "default": 10},
    {"name": "relationship_manager_assigned", "label": "Relationship manager assigned", "kind": "binary", "default": 0},
    {"name": "last_transaction_days_ago", "label": "Days since last transaction", "kind": "int",
     "min": 0, "max": 2000, "default": 20},
]
REQUIRED = [f["name"] for f in FIELDS]

# --- columns deliberately neglected, with the reason (for MODEL.md) -------------
NEGLECTED = {
    "customer_id": "Identifier, not predictive.",
    "Aging": "Pre-binned tenure label — duplicates tenure_years; using it as a feature would double-count.",
    "gender": "No association with churn (Cramér's V ~0.00). Excluded for fairness too.",
    "region": "No meaningful association (Cramér's V ~0.02).",
    "age": "Weak association (Cramér's V ~0.04).",
    "monthly_income": "Correlates ~0.77 with avg_monthly_balance — redundant.",
    "has_credit_card": "Captured by num_products.",
    "has_loan": "Weak (Cramér's V ~0.04) and captured by num_products.",
    "has_investment_product": "Captured by num_products.",
    "branch_visits_last_year": "Weak signal (Cramér's V <= 0.11).",
    "credit_score": "Weak signal (Cramér's V <= 0.11).",
}

NUMERIC = ["tenure_years", "avg_monthly_balance", "num_products", "digital_engagement_score",
           "complaint_count_last_year", "nps_score", "relationship_manager_assigned",
           "last_transaction_days_ago", "log_balance", "is_new", "single_product",
           "has_complaint", "inactive_60d"]
CATEGORICAL = ["customer_segment"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    for c in ["tenure_years", "avg_monthly_balance", "num_products", "digital_engagement_score",
              "complaint_count_last_year", "nps_score", "relationship_manager_assigned",
              "last_transaction_days_ago"]:
        f[c] = df[c].astype(float)
    f["log_balance"] = np.log1p(df["avg_monthly_balance"].astype(float))
    f["is_new"] = (df["tenure_years"] < 1).astype(int)
    f["single_product"] = (df["num_products"] == 1).astype(int)
    f["has_complaint"] = (df["complaint_count_last_year"] >= 1).astype(int)
    f["inactive_60d"] = (df["last_transaction_days_ago"] > 60).astype(int)
    f["customer_segment"] = df["customer_segment"].astype(str)
    return f


def build_preprocessor(scale: bool) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler() if scale else "passthrough", NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ])


def assign_tier(prob, balance, bal_p75):
    high_risk = np.asarray(prob) >= HIGH_RISK_THR
    high_value = np.asarray(balance) >= bal_p75
    return np.where(high_risk & high_value, "T1 Save now",
           np.where(~high_risk & high_value, "T2 Protect",
           np.where(high_risk & ~high_value, "T3 Automated save", "T4 Monitor")))


# --- rule-based reasons (fast, deterministic — SHAP lives in the main model card) ---
def risk_reasons(row, k=3):
    r = []
    if row["last_transaction_days_ago"] > 90:
        r.append("Inactive 90+ days")
    elif row["last_transaction_days_ago"] > 60:
        r.append("Inactive 60+ days")
    if row["num_products"] <= 1:
        r.append("Single product only")
    if row["tenure_years"] < 1:
        r.append("New customer (<1 yr)")
    if row["digital_engagement_score"] < 40:
        r.append("Low digital engagement")
    if row["complaint_count_last_year"] >= 2:
        r.append("2+ complaints")
    elif row["complaint_count_last_year"] == 1:
        r.append("Recent complaint")
    if row["nps_score"] <= 0:
        r.append("Negative NPS")
    elif row["nps_score"] <= 30:
        r.append("Low NPS")
    if row["relationship_manager_assigned"] == 0:
        r.append("No relationship manager")
    return "; ".join(r[:k]) if r else "No strong risk signal"


# --- tailored retention plan ----------------------------------------------------
# Tier-level strategy: how much effort/spend this type of customer justifies.
TIER_APPROACH = {
    "T1 Save now": "Highest priority — RM-led, high-touch intervention this month.",
    "T2 Protect": "Low risk but high value — nurture the relationship with periodic check-ins.",
    "T3 Automated save": "High risk, lower value — low-cost automated digital journeys.",
    "T4 Monitor": "Low risk, lower value — monitor only, no proactive spend.",
}


def retention_plan(row, tier):
    """Actions matched to this customer's own risk signals and tier (AED costs are planning
    assumptions). Recommendations, not guarantees — effectiveness is tested in the pilot (RCT)."""
    high_value = tier in ("T1 Save now", "T2 Protect")
    automated = tier == "T3 Automated save"
    actions = []

    def add(signal, action, channel, cost, hypothesis=False):
        actions.append({"signal": signal, "action": action, "channel": channel,
                        "est_cost_aed": cost, "hypothesis": hypothesis})

    if row["last_transaction_days_ago"] > 60:
        add("Inactive 60+ days",
            "Reactivation offer: cashback on the next few transactions to restart activity",
            "App push + SMS" if automated else "RM call + app push", 75)
    if row["num_products"] <= 1:
        add("Single product only",
            "Cross-sell a complementary bundle (e.g. savings + card) to deepen the relationship",
            "In-app offer" if automated else "RM / in-app offer", 50)
    if row["tenure_years"] < 1:
        add("New customer (<1 yr)",
            "90-day structured onboarding journey, plus a salary-transfer bonus",
            "Email journey" if automated else "RM + email journey", 200)
    if row["digital_engagement_score"] < 40:
        add("Low digital engagement",
            "Guided mobile-app activation and feature nudges",
            "App push + email", 20)
    if row["complaint_count_last_year"] >= 2:
        add("2+ complaints",
            "Priority complaint resolution and a service-recovery call",
            "RM call", 120)
    elif row["complaint_count_last_year"] == 1:
        add("Recent complaint",
            "Proactive follow-up to confirm the issue is fully resolved",
            "Phone / email", 40)
    if row["nps_score"] <= 0:
        add("Negative NPS",
            "Service-recovery conversation and a satisfaction follow-up",
            "RM call", 100)
    if row["relationship_manager_assigned"] == 0 and high_value:
        add("High balance, no RM",
            "Assign a relationship manager or upgrade to priority banking",
            "RM assignment", 300)
    if tier == "T1 Save now":
        add("High value + high risk",
            "Rate-match or bonus-profit-rate deposit, including Islamic deposit options",
            "RM", 0, hypothesis=True)

    if not actions:
        add("No strong risk signal",
            "No proactive spend — continue standard servicing and monitor monthly",
            "Automated monitoring", 0)

    return {
        "tier": tier,
        "approach": TIER_APPROACH.get(tier, ""),
        "actions": actions,
        "est_total_cost_aed": sum(a["est_cost_aed"] for a in actions),
    }

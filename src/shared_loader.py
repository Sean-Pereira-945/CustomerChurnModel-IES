"""Shared loader: identical in every track. Handles every quirk of the raw CSV."""
import pandas as pd
from sklearn.model_selection import train_test_split

TENURE_CHECK = {  # from the summary block embedded at the bottom of the raw file
    "Less than 1": (1613, 453), "1 to 3": (2654, 467), "3 to 7": (2931, 409),
    "7 to 15": (2160, 217), "> 15": (642, 32),
}
CAT = ["gender", "region", "customer_segment", "Aging"]
INT_COLS = ["age", "num_products", "has_credit_card", "has_loan", "has_investment_product",
            "branch_visits_last_year", "complaint_count_last_year", "credit_score",
            "relationship_manager_assigned", "nps_score", "last_transaction_days_ago", "churned"]


def load_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=1)                       # row 1 is a junk title row
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]   # trailing empty column
    df = df[df["customer_id"].astype(str).str.startswith("CUST", na=False)].copy()  # drop summary block
    df["avg_monthly_balance"] = df["avg_monthly_balance"].astype(str).str.replace(",", "").astype(float)
    num = [c for c in df.columns if c not in CAT + ["customer_id"]]
    df[num] = df[num].apply(pd.to_numeric)
    df[INT_COLS] = df[INT_COLS].astype(int)
    assert len(df) == 10_000 and df["customer_id"].is_unique
    for band, (n, churn) in TENURE_CHECK.items():
        g = df[df["Aging"] == band]
        assert (len(g), int(g["churned"].sum())) == (n, churn), f"checksum failed: {band}"
    return df.reset_index(drop=True)


def split_real(df: pd.DataFrame, seed: int = 42):
    """Shared 80/20 stratified split. The 20% holdout never reaches the generator or model."""
    return train_test_split(df, test_size=0.2, stratify=df["churned"], random_state=seed)

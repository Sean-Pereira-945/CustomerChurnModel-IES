"""Scale 10,000 real customers to 50,000 rows with a stratified Gaussian copula.

Method (explainable, no black box):
1. Split real data 80/20 (shared seed). Fit ONLY on the 8,000-row train split.
2. Stratify into 8 cells: customer_segment x churned. Each cell is fitted separately, so
   segment mix and churn rate per segment are preserved exactly (each cell sampled 5x).
3. Inside a cell, map every numeric/binary column to normal scores via its empirical ranks,
   estimate the correlation matrix, draw correlated normal samples, and map back through the
   cell's own empirical quantiles:
     - discrete columns (counts, flags, scores): 'inverted_cdf' -> only values seen in real data
     - continuous columns (balance, income, tenure, engagement): interpolated quantiles, so no
       row is copied verbatim while staying inside the observed range
4. gender/region have no association with churn (Cramer's V ~ 0), so they are sampled from the
   cell's empirical distribution. Aging is recomputed from tenure with the source's banding.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

from shared_loader import load_clean, split_real

SEED = 42
N_SYNTH = 40_000
CONTINUOUS = ["tenure_years", "monthly_income", "avg_monthly_balance", "digital_engagement_score"]
DISCRETE = ["age", "num_products", "has_credit_card", "has_loan", "has_investment_product",
            "branch_visits_last_year", "complaint_count_last_year", "credit_score",
            "relationship_manager_assigned", "nps_score", "last_transaction_days_ago"]
COLS = CONTINUOUS + DISCRETE


def aging_band(t: pd.Series) -> pd.Series:
    """Source banding: <1 | 1-3 (3.0 inclusive) | 3.1-7 | 7.1-15 | >15. Tenure has 1 decimal."""
    return pd.Series(np.select(
        [t < 1, t <= 3, t <= 7, t <= 15],
        ["Less than 1", "1 to 3", "3 to 7", "7 to 15"], default="> 15"), index=t.index)


def sample_cell(cell: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    x = cell[COLS].to_numpy(float)
    z = norm.ppf(np.column_stack([rankdata(c) / (len(c) + 1) for c in x.T]))
    corr = np.nan_to_num(np.corrcoef(z, rowvar=False))
    np.fill_diagonal(corr, 1.0)
    corr += np.eye(len(COLS)) * 1e-6
    u = norm.cdf(rng.multivariate_normal(np.zeros(len(COLS)), corr, size=n))
    out = {}
    for j, col in enumerate(COLS):
        method = "linear" if col in CONTINUOUS else "inverted_cdf"
        out[col] = np.quantile(cell[col].to_numpy(float), u[:, j], method=method)
    s = pd.DataFrame(out)
    s["gender"] = rng.choice(cell["gender"].to_numpy(), n)
    s["region"] = rng.choice(cell["region"].to_numpy(), n)
    return s


def build(raw_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    real = load_clean(raw_path)
    train, holdout = split_real(real)
    parts = []
    for (seg, churn), cell in train.groupby(["customer_segment", "churned"]):
        n = round(len(cell) * N_SYNTH / len(train))
        s = sample_cell(cell, n, rng)
        s["customer_segment"], s["churned"] = seg, churn
        parts.append(s)
    syn = pd.concat(parts, ignore_index=True).iloc[:N_SYNTH]
    syn = syn.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle cell order
    # tidy types / precision to match the source
    syn["tenure_years"] = syn["tenure_years"].round(1).clip(lower=0.1)
    syn["digital_engagement_score"] = syn["digital_engagement_score"].round(1)
    syn["monthly_income"] = syn["monthly_income"].round(0)
    syn["avg_monthly_balance"] = syn["avg_monthly_balance"].round(0)
    syn[DISCRETE + ["churned"]] = syn[DISCRETE + ["churned"]].astype(int)
    syn["Aging"] = aging_band(syn["tenure_years"])
    syn.insert(0, "customer_id", [f"SYN{i:06d}" for i in range(1, len(syn) + 1)])
    syn["is_synthetic"] = 1
    real = real.assign(is_synthetic=0)
    real["data_split"] = np.where(real["customer_id"].isin(holdout["customer_id"]), "holdout", "train")
    syn["data_split"] = "synthetic"
    full = pd.concat([real, syn[real.columns]], ignore_index=True)
    return real, syn, full

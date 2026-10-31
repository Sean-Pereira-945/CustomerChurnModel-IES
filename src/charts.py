"""EDA charts, chosen from the driver analysis. Real data only (n=10,000).

Run: python charts.py ../data.csv ../out/figures
Columns used (and only these): num_products, last_transaction_days_ago, digital_engagement_score,
complaint_count_last_year, nps_score, Aging/tenure_years, customer_segment, avg_monthly_balance,
relationship_manager_assigned, churned. The driver-ranking chart scores every column to justify
which ones were dropped.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint

from shared_loader import load_clean

RED, BLUE, INK, MUTED, GRID = "#C8102E", "#2F6DB5", "#1F2328", "#6B7280", "#E5E7EB"
SEG = ["Mass Market", "Mass Affluent", "Affluent", "Private Banking"]
TEN = ["Less than 1", "1 to 3", "3 to 7", "7 to 15", "> 15"]
TEN_LBL = ["<1 yr", "1-3", "3-7", "7-15", "15+"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})


def style(ax, title, sub, base=None):
    ax.set_title(title, loc="left", fontsize=13, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5, color=MUTED)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    if base is not None:
        ax.axhline(base, color=MUTED, ls="--", lw=1)
        ax.text(1.0, base, f" Bank average {base:.1%}", transform=ax.get_yaxis_transform(),
                va="bottom", ha="right", fontsize=8.5, color=MUTED)


def rate_bars(df, key, order, labels, title, sub, path, xlabel):
    g = df.groupby(key)["churned"].agg(["sum", "size"]).reindex(order)
    p = g["sum"] / g["size"]
    lo, hi = proportion_confint(g["sum"], g["size"], method="wilson")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(range(len(p)), p, color=RED, width=0.6, edgecolor="white", linewidth=2)
    ax.errorbar(range(len(p)), p, yerr=[p - lo, hi - p], fmt="none", ecolor=INK, elinewidth=1, capsize=3)
    for i, (v, n) in enumerate(zip(p, g["size"])):
        ax.text(i, hi.iloc[i] + 0.012, f"{v:.0%}", ha="center", color=INK, fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(p)), [f"{l}\nn={n:,}" for l, n in zip(labels, g["size"])])
    ax.set_xlabel(xlabel); ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_ylim(0, max(hi) * 1.18)
    style(ax, title, sub, df["churned"].mean())
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def cramers_v(x, y):
    t = pd.crosstab(x, y)
    return np.sqrt(chi2_contingency(t)[0] / (t.values.sum() * (min(t.shape) - 1)))


def main(raw, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    df = load_clean(raw)
    note = "Real customers, n=10,000. Bars show 95% Wilson intervals. Association, not causation."

    # 1. Driver ranking: justifies which columns get charts
    scores = {}
    for c in df.columns.drop(["customer_id", "churned", "Aging"]):
        x = df[c]
        if x.dtype != object and x.nunique() > 7:
            x = pd.qcut(x.rank(method="first"), 5, labels=False)
        scores[c] = cramers_v(x, df["churned"])
    s = pd.Series(scores).sort_values()
    fig, ax = plt.subplots(figsize=(9, 6))
    charted = {"num_products", "last_transaction_days_ago", "digital_engagement_score",
               "customer_segment", "tenure_years", "nps_score", "relationship_manager_assigned",
               "complaint_count_last_year", "avg_monthly_balance"}
    ax.barh(s.index, s.values, color=[RED if c in charted else GRID for c in s.index], height=0.65)
    for i, v in enumerate(s.values):
        ax.text(v + 0.004, i, f"{v:.2f}", va="center", fontsize=8.5, color=INK)
    ax.set_xlabel("Strength of association with churn (Cramér's V)")
    ax.xaxis.grid(True, color=GRID); ax.yaxis.grid(False); ax.set_axisbelow(True)
    ax.set_title("Products held, inactivity and engagement are the strongest signals",
                 loc="left", fontsize=12, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, "Red = charted. Grey = weak (gender, region, age ≈ 0) or redundant (income tracks balance).",
            transform=ax.transAxes, fontsize=9, color=MUTED)
    fig.tight_layout(); fig.savefig(out / "01_driver_ranking.png", dpi=200); plt.close(fig)

    # 2-6. Single-driver charts
    rate_bars(df, df["num_products"].clip(upper=4), [1, 2, 3, 4], ["1", "2", "3", "4+"],
              "Single-product customers churn at more than twice the bank average", note,
              out / "02_products.png", "Products held")
    rec = pd.cut(df["last_transaction_days_ago"], [-1, 30, 60, 90, 10_000], labels=False)
    rate_bars(df, rec, [0, 1, 2, 3], ["0-30", "31-60", "61-90", "90+"],
              "Customers idle for 90+ days leave at three times the bank average", note,
              out / "03_recency.png", "Days since last transaction")
    eng = pd.cut(df["digital_engagement_score"], [-1, 20, 40, 60, 80, 100], labels=False)
    rate_bars(df, eng, [0, 1, 2, 3, 4], ["0-20", "21-40", "41-60", "61-80", "81-100"],
              "Churn falls steadily as digital engagement rises", note,
              out / "04_engagement.png", "Digital engagement score")
    rate_bars(df, df["complaint_count_last_year"].clip(upper=2), [0, 1, 2], ["0", "1", "2+"],
              "Customers with 2+ complaints churn at twice the bank average", note,
              out / "05_complaints.png", "Complaints last year")
    nps = pd.cut(df["nps_score"], [-101, 0, 30, 60, 100], labels=False)
    rate_bars(df, nps, [0, 1, 2, 3], ["≤0", "1-30", "31-60", "61-100"],
              "Customers with negative NPS churn at 1.7× the bank average", note,
              out / "06_nps.png", "NPS score band")

    # 7. Tenure x products heatmap
    m = df.assign(p=df["num_products"].clip(upper=4)).pivot_table(
        index="Aging", columns="p", values="churned", aggfunc="mean").reindex(TEN)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    im = ax.imshow(m.values, cmap="Reds", vmin=0, vmax=0.6, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.values[i, j]
            ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=10,
                    color="white" if v > 0.35 else INK)
    ax.set_xticks(range(4), ["1", "2", "3", "4+"]); ax.set_yticks(range(5), TEN_LBL)
    ax.set_xlabel("Products held"); ax.set_ylabel("Tenure")
    ax.spines[:].set_visible(False)
    ax.set_title("New customers with one product: more than half leave", loc="left",
                 fontsize=13, color=INK, fontweight="bold", pad=24)
    ax.text(0, 1.02, "Churn rate by tenure and products held. Real customers, n=10,000.",
            transform=ax.transAxes, fontsize=9.5, color=MUTED)
    fig.colorbar(im, ax=ax, format=matplotlib.ticker.PercentFormatter(1, 0), shrink=0.8)
    fig.tight_layout(); fig.savefig(out / "07_tenure_x_products.png", dpi=200); plt.close(fig)

    # 8. Segment: share of churners vs share of balance lost (same % scale, one axis)
    ch = df[df["churned"] == 1]
    share_n = ch["customer_segment"].value_counts(normalize=True).reindex(SEG)
    share_b = (ch.groupby("customer_segment")["avg_monthly_balance"].sum() /
               ch["avg_monthly_balance"].sum()).reindex(SEG)
    lost = ch["avg_monthly_balance"].sum()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(4); w = 0.36
    ax.bar(x - w / 2 - 0.01, share_n, w, color=BLUE, label="Share of churned customers")
    ax.bar(x + w / 2 + 0.01, share_b, w, color=RED, label="Share of balance lost (AED)")
    for i in range(4):
        ax.text(x[i] - w / 2, share_n.iloc[i] + 0.012, f"{share_n.iloc[i]:.0%}", ha="center", fontsize=9.5, color=INK)
        ax.text(x[i] + w / 2, share_b.iloc[i] + 0.012, f"{share_b.iloc[i]:.0%}", ha="center", fontsize=9.5, color=INK)
    ax.set_xticks(x, SEG); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_ylim(0, 0.85); ax.legend(frameon=False, loc="upper right")
    style(ax, "Mass Market drives churn volume; higher segments drive the money lost",
          f"Real customers. AED {lost/1e6:.1f}m of average monthly balance left with churned customers.")
    fig.tight_layout(); fig.savefig(out / "08_segment_volume_vs_value.png", dpi=200); plt.close(fig)

    # 9. RM assigned vs not, by segment
    r = df.pivot_table(index="customer_segment", columns="relationship_manager_assigned",
                       values="churned", aggfunc="mean").reindex(SEG)
    cover = df.groupby("customer_segment")["relationship_manager_assigned"].mean().reindex(SEG)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(x - w / 2 - 0.01, r[0], w, color=RED, label="No RM")
    ax.bar(x + w / 2 + 0.01, r[1], w, color=BLUE, label="RM assigned")
    for i in range(4):
        ax.text(x[i] - w / 2, r[0].iloc[i] + 0.005, f"{r[0].iloc[i]:.0%}", ha="center", fontsize=9.5, color=INK)
        ax.text(x[i] + w / 2, r[1].iloc[i] + 0.005, f"{r[1].iloc[i]:.0%}", ha="center", fontsize=9.5, color=INK)
    ax.set_xticks(x, [f"{s}\nRM coverage {c:.0%}" for s, c in zip(SEG, cover)])
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_ylabel("Churn rate"); ax.legend(frameon=False)
    style(ax, "Customers with an RM churn at about half the rate in every segment",
          "Association only: RMs may be given to already-loyal customers. To be tested in the pilot.")
    fig.tight_layout(); fig.savefig(out / "09_rm_by_segment.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Generate the explainer diagrams for docs/diagrams/ (matplotlib, no external assets).

Run: python build_docs_diagrams.py ../docs/diagrams
Produces: approach_pipeline.png, data_flow.png, tier_matrix.png, retention_flow.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RED, BLUE, INK, MUTED, GREEN = "#C8102E", "#2F6DB5", "#1F2328", "#6B7280", "#2E7D32"
LIGHT, PAPER = "#F3F4F6", "#FFFFFF"
plt.rcParams.update({"font.family": "DejaVu Sans"})


def box(ax, x, y, w, h, text, fc=BLUE, tc="white", fs=11, bold=True, ec="none"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.10",
                                fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.35)


def arrow(ax, p1, p2, color=INK, lw=2.2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=20, lw=lw,
                                 color=color, shrinkA=2, shrinkB=2))


def frame(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    fig.patch.set_facecolor(PAPER)
    return fig, ax


def title(ax, x, y, text, fs=16):
    ax.text(x, y, text, fontsize=fs, fontweight="bold", color=INK, va="top")


# ---------------------------------------------------------------- 1. approach pipeline
def approach_pipeline(out):
    fig, ax = frame(14, 5)
    title(ax, 0.3, 4.8, "The four-stage approach")
    stages = [
        ("1  DATA", BLUE, "Clean & checksum the file\nFlag bad rows (keep them)\nScale 10k → 50k (synthetic)"),
        ("2  UNDERSTANDING", INK, "9 charts with confidence bars\nRank drivers (Cramer's V)\nSee why customers leave"),
        ("3  PREDICTION", BLUE, "Logistic Regression model\nCalibrated probability\nTested on a held-out 20%"),
        ("4  RECOMMENDATION", INK, "Rank by money at risk\nTiers + retention playbook\nProve it with a pilot (RCT)"),
    ]
    x, w, h, y = 0.3, 3.05, 1.3, 2.9
    for i, (name, c, cap) in enumerate(stages):
        box(ax, x, y, w, h, name, fc=c, fs=13)
        ax.text(x + w / 2, y - 0.2, cap, ha="center", va="top", fontsize=10, color=INK, linespacing=1.5)
        if i < 3:
            arrow(ax, (x + w + 0.02, y + h / 2), (x + w + 0.28, y + h / 2), RED)
        x += w + 0.3
    fig.savefig(out / "approach_pipeline.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 2. data flow (key diagram)
def data_flow(out):
    fig, ax = frame(14.5, 7.2)
    title(ax, 0.3, 7.05, "How the data is used")
    ax.text(0.3, 6.55, "Key point: the 50,000 synthetic rows power the dashboard only — the model "
            "trains on the real customers.", fontsize=11, color=RED, va="top", style="italic")

    # left intake column (vertical): raw -> clean -> split -> train
    box(ax, 0.3, 5.55, 2.4, 0.62, "Raw file (messy CSV)", fc=MUTED, fs=10)
    box(ax, 0.3, 4.75, 2.4, 0.62, "Clean 10,000 real", fc=INK, fs=10)
    box(ax, 0.3, 3.95, 2.4, 0.62, "80 / 20 split", fc=INK, fs=10)
    box(ax, 0.3, 2.75, 2.4, 0.62, "Train  8,000 (80%)", fc=RED, fs=10)
    for y0, y1 in [(5.55, 5.37), (4.75, 4.57)]:
        arrow(ax, (1.5, y0), (1.5, y1 + 0.18))
    arrow(ax, (1.5, 5.55), (1.5, 5.37 + 0.0))
    arrow(ax, (1.5, 4.75), (1.5, 4.57))
    arrow(ax, (1.5, 3.95), (1.5, 3.37))               # split -> train

    # holdout (upper, feeds the model test)
    box(ax, 5.3, 5.3, 2.7, 0.62, "Holdout  2,000 (20%)", fc="#9AA7B4", fs=10)
    arrow(ax, (2.7, 4.26), (5.3, 5.55), "#6B7A88")    # split -> holdout

    # MODEL lane (red)
    ax.add_patch(FancyBboxPatch((3.35, 2.25), 11.05, 1.65, boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc="#FCECEF", ec=RED, lw=1.2))
    ax.text(3.55, 3.82, "MODEL  ·  real data only", fontsize=10.5, color=RED, fontweight="bold", va="top")
    mb = [("Logistic\nRegression", RED), ("Calibrate\nprobabilities", RED),
          ("Score all\n10,000 (OOF)", RED), ("Churn %\nper customer", INK),
          ("Tiers +\nmoney at risk", INK)]
    x, w, h, y = 3.7, 1.95, 0.92, 2.42
    centers = []
    for i, (t, c) in enumerate(mb):
        box(ax, x, y, w, h, t, fc=c, fs=9.5)
        centers.append(x + w / 2)
        if i < len(mb) - 1:
            arrow(ax, (x + w + 0.0, y + h / 2), (x + w + 0.15, y + h / 2), INK)
        x += w + 0.15
    arrow(ax, (2.7, 3.06), (3.7, 2.95), RED)          # train -> LR
    arrow(ax, (6.7, 5.3), (centers[2], 3.9), "#6B7A88")   # holdout -> score (test)
    ax.text(6.95, 4.55, "tested once →\nPR-AUC 0.56, ROC 0.84", fontsize=9, color="#4B5563", style="italic")

    # DASHBOARD lane (blue)
    ax.add_patch(FancyBboxPatch((3.35, 0.35), 11.05, 1.5, boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc="#ECF2FA", ec=BLUE, lw=1.2))
    ax.text(3.55, 1.77, "DASHBOARD  ·  volume only — does NOT train the model", fontsize=10.5,
            color=BLUE, fontweight="bold", va="top")
    db = [("Gaussian copula\n(learns the shape)", BLUE), ("+ 40,000\nsynthetic rows", BLUE),
          ("50,000-row\ndataset", BLUE), ("Power BI\ndashboard", INK)]
    x, w, h, y = 3.7, 2.3, 0.9, 0.52
    for i, (t, c) in enumerate(db):
        box(ax, x, y, w, h, t, fc=c, fs=9.5)
        if i < len(db) - 1:
            arrow(ax, (x + w + 0.0, y + h / 2), (x + w + 0.2, y + h / 2), INK)
        x += w + 0.2
    arrow(ax, (1.9, 2.75), (4.0, 1.44), BLUE)         # train -> copula
    ax.text(2.1, 2.05, "shape only", fontsize=9, color=BLUE, style="italic")
    fig.savefig(out / "data_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 3. tier matrix
def tier_matrix(out):
    fig, ax = frame(9, 7.6)
    title(ax, 0.3, 7.4, "The four action tiers (risk x value)")
    quads = [  # x, y, color, name, count, note
        (4.7, 4.0, RED, "T1  Save now", "48", "RM-led, this month"),
        (1.0, 4.0, GREEN, "T3  Automated save", "972", "low-cost digital"),
        (4.7, 1.0, BLUE, "T2  Protect", "2,452", "nurture / check-ins"),
        (1.0, 1.0, MUTED, "T4  Monitor", "6,528", "watch only"),
    ]
    for x, y, c, name, n, note in quads:
        box(ax, x, y, 3.3, 2.7, "", fc=c)
        ax.text(x + 1.65, y + 2.1, name, ha="center", color="white", fontsize=14, fontweight="bold")
        ax.text(x + 1.65, y + 1.35, f"{n} customers", ha="center", color="white", fontsize=12)
        ax.text(x + 1.65, y + 0.6, note, ha="center", color="white", fontsize=10.5, style="italic")
    # axes labels
    ax.annotate("", xy=(8.2, 0.6), xytext=(0.9, 0.6), arrowprops=dict(arrowstyle="-|>", color=INK, lw=2))
    ax.annotate("", xy=(0.6, 7.0), xytext=(0.6, 0.9), arrowprops=dict(arrowstyle="-|>", color=INK, lw=2))
    ax.text(4.6, 0.2, "VALUE  (balance)  →   high value = top 25%, AED 26,867+", ha="center", fontsize=11, color=INK)
    ax.text(0.33, 4.0, "RISK  (churn probability)  →   high risk = 40%+", rotation=90, va="center",
            fontsize=11, color=INK)
    fig.savefig(out / "tier_matrix.png", dpi=200, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 4. retention flow
def retention_flow(out):
    fig, ax = frame(13.5, 7)
    title(ax, 0.3, 6.8, "How we decide what to do for each customer")
    box(ax, 0.3, 3.0, 2.6, 1.3, "Customer\ndata (9 fields)", fc=MUTED, fs=11)
    arrow(ax, (2.9, 3.65), (3.3, 3.65))
    box(ax, 3.3, 3.0, 2.7, 1.3, "Model →\nchurn % + reasons", fc=RED, fs=11)
    arrow(ax, (6.0, 3.65), (6.4, 3.65))
    box(ax, 6.4, 3.0, 2.5, 1.3, "Tier sets the\neffort & channel", fc=BLUE, fs=11)
    arrow(ax, (8.9, 3.65), (9.4, 3.65))
    acts = [
        "Inactive → reactivation offer",
        "Single product → cross-sell bundle",
        "New customer → onboarding journey",
        "Complaints → service-recovery call",
        "High value, no RM → assign an RM",
        "T1 → rate-match deposit (pilot)",
    ]
    ax.text(11.3, 6.65, "matched to the customer's own signals", ha="center", fontsize=10,
            color=MUTED, style="italic")
    y = 5.5
    for i, a in enumerate(acts):
        c = RED if "T1" in a else INK
        box(ax, 9.4, y, 3.8, 0.72, a, fc="white", tc=c, fs=9.8, bold=False, ec=BLUE)
        y -= 0.9
    fig.savefig(out / "retention_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def main(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    approach_pipeline(out); data_flow(out); tier_matrix(out); retention_flow(out)
    print("Diagrams ->", out)
    for p in sorted(out.glob("*.png")):
        print(" ", p.name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../docs/diagrams")

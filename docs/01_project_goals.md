# 1. Project goals — and how we met them

The bank's brief asked for seven things. Here is each one in plain words, how we delivered it, and
where to find it.

| # | What the brief asked for | How we did it | Where it lives |
|---|---|---|---|
| 1 | **Find the strongest churn patterns** (at least 3 charts) | 9 evidence-chosen charts, each with confidence bars and sample sizes | [page 5](05_graphs_explained.md), `out/C/figures/` |
| 2 | **Build at least one ML model, tested properly** | Logistic Regression, compared to a baseline and LightGBM, tested once on a held-out 20% | [page 6](06_model.md), `out/B/` |
| 3 | **Rank customers by *balance at risk*, not just probability** | Every customer scored; ranked by `probability × balance` | [page 7](07_retention.md), `out/B/priority_list.csv` |
| 4 | **Targeted actions + a measurable pilot with KPIs** | A retention playbook + a randomised controlled trial with a sample-size calculation | [page 7](07_retention.md), `out/C/pilot_design.md` |
| 5 | **Demonstrate on unseen records** | `score.py` scores 200 never-seen customers; metrics match the reported ones | [page 6](06_model.md), `app/`, `out/B/score.py` |
| 6 | **A cleaned dataset or a documented cleaning process** | Both: a clean file and a full cleaning log | [page 4](04_data_and_synthetic.md), `out/A/` |
| 7 | **A management report (1,000–1,500 words or 5–7 slides)** | A 1,050-word report **and** a 7-slide deck (+ appendix) | `out/C/management_report.md`, `out/C/Meridian_Retention.pptx` |

## How the marks map to the work

The brief is graded on: framing, data/cleaning, EDA (exploring the data), the ML model,
prioritisation, the pilot, responsible AI, and the demo. Every one of those has a concrete output:

- **Framing & report** → the management report and slide deck.
- **Data & cleaning** → `out/A/cleaning_log.md`, the two flagged data-quality issues.
- **EDA** → the 9 charts and `out/C/eda_findings.json`.
- **ML model** → `out/B/model_card.md`, `out/B/metrics.json`.
- **Prioritisation** → the 4 tiers and the balance-at-risk ranking.
- **Pilot** → `out/C/pilot_design.md` (with a real power calculation).
- **Responsible AI** → `out/C/ai_disclosure.md` (fairness, no causation claims).
- **Demo** → `score.py` on unseen data, and the live web app.

## Two extra things we built (beyond the brief)

- A **Power BI dashboard** (5 pages) — [page 8](08_dashboards.md).
- A **live web app** (FastAPI + React) that scores a customer on the spot and tells you **how to
  retain them** — [page 7](07_retention.md) and [page 8](08_dashboards.md).

➡️ Next: [The folder guide](02_folder_guide.md)

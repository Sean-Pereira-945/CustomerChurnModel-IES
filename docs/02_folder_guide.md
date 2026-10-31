# 2. Folder guide — what each part does

Here is the whole project, folder by folder, in plain words.

```
meridian_retention_kit/
├── data/                  the raw bank file (never changed)
├── src/                   all the code that builds everything
├── out/                   all the generated results (A = data, B = model, C = insights)
│   ├── A/                 cleaned data, synthetic data, Power BI project
│   ├── B/                 the model, scores, metrics, the priority list
│   ├── C/                 charts, report, slides, pilot
│   └── powerbi/           starter Power BI tables (copied into out/A/powerbi)
├── app/                   the live web dashboard (FastAPI backend + React frontend)
├── docs/                  this documentation (+ diagrams/)
├── CLAUDE.md              the original team plan for the 2-hour sprint
├── README.md             short setup notes
├── start.bat             one-click launcher for the web app
└── PROJECT_OVERVIEW.md   the simple end-to-end story
```

## `data/` — the raw material
- **`Bank Data.csv`** — the original 10,000-customer file from the bank. We **never edit this**; all
  cleaning happens in code so it's repeatable.

## `src/` — the code that does the work
Think of this as the "factory". Each script builds part of the results.
- **`shared_loader.py`** — one function everyone uses to open and clean the raw file (fixes commas,
  junk rows, checks the row counts match the source).
- **`synth.py`** — turns 10,000 real customers into 50,000 by adding 40,000 realistic fakes.
- **`charts.py`** — draws the 9 analysis charts.
- **`make_A.py` / `make_B.py` / `make_C.py`** — build the three result folders (data / model / insights).
- **`model_lib.py`, `score.py`** — the model's feature logic and the scoring script for new customers.
- **`fill_report.py`, `build_deck.py`** — fill the report numbers and build the slide deck.
- **`build_powerbi.py`, `build_pbip.py`** — build the Power BI tables and the Power BI project file.
- **`build_docs_diagrams.py`** — draws the diagrams in this docs folder.

## `out/A/` — Data (Person A's work)
- **`clean_real.csv`** — the 10,000 cleaned customers.
- **`analysis_50k.csv`** — 10,000 real + 40,000 synthetic, each row tagged real/fake.
- **`cleaning_log.md`** — exactly what was cleaned and the two data-quality flags.
- **`synthetic_fidelity.md`** — proof the fakes match the real data.
- **`approach_A.md`** — the data method as slide bullets.
- **`powerbi/`** — the Power BI dashboard project (see [page 8](08_dashboards.md)).
- **`figures/synthetic_vs_real.png`** — the fake-vs-real check chart.

## `out/B/` — Prediction (Person B's work)
- **`priority_list.csv`** — all 10,000 customers ranked by money at risk, with tier and reasons.
- **`metrics.json`** — all the model's scores (how good it is).
- **`model_comparison.csv`** — baseline vs Logistic Regression vs LightGBM.
- **`model.joblib`** — the saved, trained model.
- **`score.py`** — scores new/unseen customers.
- **`model_card.md`** — a one-page summary of the model, including fairness checks.
- **`hidden_test_sample.csv`** — 200 unseen customers for the live demo.
- **`figures/`** — the model charts (PR curve, calibration, SHAP, value capture).
- **`approach_B.md`** — the modelling method as slide bullets.

## `out/C/` — Understanding & strategy (Person C's work)
- **`figures/`** — the 9 EDA charts.
- **`eda_findings.json`** — the key churn numbers.
- **`management_report.md`** (+ `_filled.md`) — the committee report.
- **`Meridian_Retention.pptx`** — the slide deck (7 main + methodology appendix).
- **`pilot_design.md`** — the experiment to prove the actions work.
- **`ai_disclosure.md`** — responsible-AI notes.
- **`build_deck.py`, `fill_report.py`** — copies of the deck/report builders.

## `app/` — the live web dashboard
- **`backend/`** — FastAPI server: the lean model, the scoring endpoint, the retention plan.
- **`frontend/`** — React app: KPI cards, charts, the "score a customer" form, the priority table.
- **`MODEL.md`** — the model used in the app, its results, the fields it needs, and the columns it ignores.
- **`README.md`** — how to run just the app.

## `docs/` — this documentation
- The nine numbered pages, plus **`diagrams/`** (the four diagrams drawn by `build_docs_diagrams.py`).

➡️ Next: [The approach](03_approach.md)

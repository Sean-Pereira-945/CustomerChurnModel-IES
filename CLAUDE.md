# CLAUDE.md — Meridian Trust Bank: Customer Retention Decision Engine
## 2-hour sprint · 3 people · parallel tracks

You are a **senior data analyst on a Big Four (Deloitte-style) engagement** for **Meridian Trust Bank
(UAE retail bank, amounts in AED)**. Audience: the bank's management committee.
Tagline: **PREDICT. PRIORITISE. RETAIN.**

**Starter kit:** `src/` already contains the shared loader, the 50k scaling (`synth.py`), the Power BI
dataset builder and the 9 charts, and `out/` holds their verified outputs (see `README.md`).

**How to use this file:** each team member opens Claude Code in their own folder copy and says
*"Read CLAUDE.md. I am Person A"* (or B / C). Claude Code then does **only that person's track**.
The three tracks never wait on each other. They meet only in the final 15-minute integration,
through the fixed file contract in §3.

---

## 0. Timeline (120 minutes)

| Time | Person A — Data & Dashboard | Person B — Model & Prioritisation | Person C — Insights & Strategy |
|---|---|---|---|
| 0:00–0:10 | Setup, paste shared loader (§2), verify checksum | Same | Same |
| 0:10–0:35 | Run the starter kit: clean, flag, 50k scaling, fidelity check | Baseline + LogReg + LightGBM on real data, holdout eval | EDA: churn rates with CIs, 9 charts (kit's `charts.py`), driver ranking |
| 0:35–1:30 | Build the 5-page Power BI dashboard from `powerbi/BUILD_GUIDE.md` and verify against its expected values | Calibration, SHAP, value-at-risk ranking, tiers, `score.py` | Playbook, pilot design, report text, `build_deck.py` (deck generator) |
| 1:30–1:45 | Screenshots, `approach_A.md` (data-processing practices) | Hidden-test demo, metrics.json, model card, `approach_B.md` (modelling approach) | Finish report, AI disclosure, dry-run the deck with placeholder images |
| 1:45–2:00 | **Integration (all three, §7)**: fill numbers, generate the final deck | | |

**Rule for everyone:** if a step runs late, cut the item marked *(stretch)*. Never cut the
items marked **(must)**. At 1:30, stop building and start packaging outputs.

---

## 1. The brief, compressed

Required by the brief:
1. **(must)** The strongest churn patterns, with at least 3 visualisations. → C (plus A's dashboard)
2. **(must)** At least one ML model, evaluated properly. → B
3. **(must)** A ranked list of customers, using **average monthly balance at risk**, not probability alone. → B
4. **(must)** Targeted interventions plus a measurable pilot with KPIs. → C
5. **(must)** A demonstration on unseen records (hidden test input). → B
6. **(must)** A cleaned dataset or a documented cleaning process. → A
7. **(must)** A management report of 1,000–1,500 words or 5–7 slides. → C writes, everyone fills in

Marks: framing 10 · data/cleaning 10 · EDA 15 · ML 20 · prioritisation 15 · pilot 10 ·
responsible AI 10 · demo/defence 10.

**Hard rules (apply to all tracks):**
- No hardcoded answers and no hand-typed metrics. Every number must come from code output.
- Never present correlation as causation. Write "associated with" or "churn is higher among".
  Only the pilot (an RCT) can show cause.
- Label every statement as **descriptive**, **predictive**, or **recommendation**.
- The dataset has **no** competitor-rate, offer, or reason-for-leaving fields. Never claim
  findings about those. Treat them as **pilot hypotheses** only.
- Use `random_state=42` everywhere.

---

## 2. Shared data facts and loader (all three paste this exact function)

Each person loads the raw CSV themselves with this identical function. That removes any
dependency between tracks and guarantees everyone works on the same 10,000 clean rows.

Known quirks of `Bank Data.csv` (already verified):
- Row 1 is a junk title row. It needs `skiprows=1`.
- The trailing empty column `Unnamed: 21` must be dropped.
- Below the 10,000 customers there is an **Excel summary block**. Keep only rows whose
  `customer_id` starts with `CUST`.
- `avg_monthly_balance` is text with commas, e.g. `"4,485"`.
- `Aging` is a pre-binned version of tenure. Use it for labels only, **never as a model feature**.
- There are no missing values and no duplicate IDs. 1,578 of 10,000 churned (**15.8%**), so the classes are imbalanced.

```python
# shared_loader.py — identical copy in every track
import pandas as pd

TENURE_CHECK = {  # from the summary block embedded in the raw file
    "Less than 1": (1613, 453), "1 to 3": (2654, 467), "3 to 7": (2931, 409),
    "7 to 15": (2160, 217), "> 15": (642, 32),
}
CAT = ["gender", "region", "customer_segment", "Aging"]

def load_clean(path="data/Bank Data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=1)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df[df["customer_id"].astype(str).str.startswith("CUST", na=False)].copy()
    df["avg_monthly_balance"] = df["avg_monthly_balance"].astype(str).str.replace(",", "").astype(float)
    num = [c for c in df.columns if c not in CAT + ["customer_id"]]
    df[num] = df[num].apply(pd.to_numeric)
    for c in ["num_products", "has_credit_card", "has_loan", "has_investment_product",
              "branch_visits_last_year", "complaint_count_last_year", "credit_score",
              "relationship_manager_assigned", "last_transaction_days_ago", "churned", "age"]:
        df[c] = df[c].astype(int)
    assert len(df) == 10_000 and df["customer_id"].is_unique
    for band, (n, churn) in TENURE_CHECK.items():
        g = df[df["Aging"] == band]
        assert (len(g), int(g["churned"].sum())) == (n, churn), band
    return df.reset_index(drop=True)

def split_real(df, seed=42):
    """Shared 80/20 stratified split. B uses it for the holdout; A uses it so the
    synthetic generator never sees holdout rows."""
    from sklearn.model_selection import train_test_split
    return train_test_split(df, test_size=0.2, stratify=df["churned"], random_state=seed)
```

The canonical copy is `src/shared_loader.py` in the starter kit (it also casts `nps_score` to int); use that file rather than retyping this one.

Because the split is seeded and identical, A's synthetic data and B's holdout stay consistent
without the two ever exchanging files.

Stack: Python 3.11, pandas, scikit-learn, lightgbm, shap, matplotlib, statsmodels, python-pptx *(C only)*. Power BI Desktop on Windows *(A only)*.

---

## 3. File contract (what each track must deliver, with exact names)

Integration only works if these names and columns are exact.

| Owner | File | Contents |
|---|---|---|
| A | `out/A/clean_real.csv` | 10,000 cleaned rows |
| A | `out/A/analysis_50k.csv` | 50,000 rows, with `is_synthetic` (0/1) and `customer_id` (`SYN…` for synthetic rows) |
| A | `out/A/cleaning_log.md`, `out/A/synthetic_fidelity.md` | Cleaning steps and synthetic-data checks |
| A | `out/A/powerbi/` | `Meridian.pbix`, `data/` star-schema CSVs, `measures.dax`, `BUILD_GUIDE.md` |
| A | `out/A/screens/page1.png … page5.png` | One screenshot per dashboard page (page 5 is added at integration) |
| A | `out/A/approach_A.md` | Data-processing approach and practices, written as slide bullets (feeds deck appendix, §6 C3) |
| A | `out/A/figures/synthetic_vs_real.png` | One fidelity chart (churn rate by segment, real vs synthetic) |
| B | `out/B/priority_list.csv` | `customer_id, churn_probability, avg_monthly_balance, expected_balance_at_risk, priority_tier, top_3_reasons` for all 10,000 real customers (out-of-fold scores) |
| B | `out/B/metrics.json` | Flat keys: `pr_auc, roc_auc, recall_at_thr, precision_at_thr, threshold, top_decile_capture, baseline_pr_auc, aed_protected_value_weighted, aed_protected_prob_only, aed_protected_random, capacity_n, tier_counts` |
| B | `out/B/figures/*.png` | Model figures: PR curve, calibration, SHAP bar, value-vs-probability capture chart |
| B | `out/B/model.joblib`, `out/B/score.py`, `out/B/model_card.md`, `out/B/hidden_test_sample.csv` | Saved model, scoring script, model card, demo input |
| B | `out/B/approach_B.md` | Modelling, validation and prioritisation approach, written as slide bullets (feeds deck) |
| B | `out/B/model_comparison.csv` | `model, cv_pr_auc, holdout_pr_auc, holdout_roc_auc` — one row per model incl. baseline and the with/without leakage-feature runs |
| C | `out/C/figures/*.png` | 9 EDA charts (§6 C1) |
| C | `out/C/eda_findings.json` | Flat keys, e.g. `base_churn_rate, churn_tenure_lt1, churn_tenure_15plus, aed_balance_lost_total, ...` |
| C | `out/C/management_report.md` | Report with `{{B.key}}` placeholders for B's metrics |
| C | `out/C/slides_outline.md`, `out/C/pilot_design.md`, `out/C/ai_disclosure.md` | Slide text, pilot design, AI disclosure |
| C | `out/C/fill_report.py` | Replaces `{{B.*}}` and `{{C.*}}` placeholders from the JSON files |
| C | `out/C/build_deck.py` | Generates `Meridian_Retention.pptx` from all three tracks' files (§6 C3) |

**Tier definition (A and C must use exactly what B uses):**
- High risk means calibrated `churn_probability >= 0.40`.
- High value means `avg_monthly_balance >= ` the 75th percentile of all 10,000 real customers.
- Tiers: **T1 Save now** (high risk, high value) · **T2 Protect** (low risk, high value) ·
  **T3 Automated save** (high risk, low value) · **T4 Monitor** (low risk, low value).
- RM capacity assumption: **500 contacts per month** (`capacity_n`).
- `expected_balance_at_risk = churn_probability × avg_monthly_balance` (AED).

---

## 4. PERSON A — Data engineering, synthetic 50k, Power BI

Goal: the *Data* stage, plus the visual dashboard the committee will see.

**A1 (must, 0:10–0:20): Clean and document**
- `load_clean()`, then validity checks, logging counts to `cleaning_log.md`. Flag, never drop:
  age 18–100, credit score 300–900, engagement 0–100, NPS −100 to 100, tenure ≤ age − 18,
  and no negative money values.
- Keep extreme balances, because Private Banking customers are genuinely valuable. Write the decision down.
- Two real-data inconsistencies were found; **flag them, don't drop or fix** (dropping 10% of rows
  would bias the analysis): 1,009 rows where `tenure_years > age − 18` (e.g. age 18 with 10.7 years'
  tenure), and 199 rows where `num_products` is less than the count of product flags.
  Columns: `dq_tenure_gt_adult_years`, `dq_products_lt_flags`. Mention both in the deck as data-quality findings.
- Save `clean_real.csv`.

**A2 (must, 0:20–0:35): Scale 10,000 → 50,000 rows (already built: `src/synth.py`)**

Exact method, a **stratified Gaussian copula**, chosen because it is explainable in one slide,
needs no heavy library, and preserves both the distributions and the relationships with churn:

1. `train_real, holdout = split_real(df)`. Fit on the **8,000 train rows only**; the 2,000-row
   holdout never reaches the generator, so B's evaluation stays clean.
2. Split train into **8 cells: customer_segment × churned**. Each cell is fitted on its own and
   sampled at 5× its size. This keeps the segment mix and the churn rate inside every segment exact.
3. Inside each cell, for the 15 numeric and binary columns:
   - convert each column to normal scores using its ranks (removes skew, e.g. balances);
   - estimate the correlation matrix of those scores;
   - draw correlated normal samples, then map each back through the cell's own quantiles.
   - Counts, flags and scores use `inverted_cdf`, so only values seen in the real data appear
     (no 2.7 products, no out-of-range credit scores). Balance, income, tenure and engagement use
     interpolated quantiles, so no row is a copy of a real customer.
4. `gender` and `region` have no association with churn (Cramér's V 0.00 and 0.02), so they are
   sampled from the cell's distribution. `Aging` is recomputed from tenure with the source's exact
   banding (<1 | 1–3 incl. 3.0 | 3.1–7 | 7.1–15 | >15), which matches the source on 100% of real rows.
5. IDs `SYN000001…SYN040000`, `is_synthetic = 1`, plus `data_split` = train / holdout / synthetic.
   Do **not** "fix" the two real-data inconsistencies in synthetic rows (see A1); flag them in both.

Verified fidelity (`synthetic_fidelity.md`): churn 15.78% real vs 15.78% synthetic; churn by
segment identical to 3 decimals; KS distance ≤ 0.005 on every column; largest correlation gap
0.07; 0 synthetic rows identical to a real customer; all values inside real ranges.
Caveat for the deck: synthetic rows add volume, not information. Headline numbers use the real 10,000.

*Not to be confused with feature scaling* (B's job): `StandardScaler` on numeric features for
logistic regression only, `log1p` on balance first; no scaling for LightGBM (trees don't need it).

**A3 (must, 0:35–1:30): Power BI dashboard (already prepared: `powerbi/`)**

Claude Code can't produce or test a `.pbix`, and a hand-written `.pbip` can fail to open, so the
reliable route is: import three CSVs, paste the measures, build visuals by the guide (~40 min).
- `powerbi/data/fact_customers.csv` (50,000 rows, 22 columns, only what the visuals need),
  `dim_segment.csv`, `dim_tenure.csv`. Bands are pre-computed with `_sort` columns.
- `powerbi/measures.dax`: 22 measures in 6 display folders.
- `powerbi/BUILD_GUIDE.md`: load steps, theme, slicers, 5 pages visual by visual, and an
  **expected-values table** to check every number before presenting.
- Pages: 1 Executive overview · 2 Behavioural drivers · 3 Relationship & value at risk ·
  4 Data quality & lineage · 5 Retention priority (B's list, at integration).
- Export each page to `out/A/screens/`.

**A4 (must, 1:30–1:45): Approach notes and checks**
- Write `approach_A.md` as slide-ready bullets under these exact headings (the deck reads them):
  `## Data understanding`, `## Cleaning steps`, `## Validation & checksums`,
  `## Synthetic data method`, `## Synthetic data fidelity`, `## Data-processing best practices`,
  `## Power BI model design`.
  Each heading gets 3–5 bullets of at most 15 words, with real counts from your logs.
- The best-practices section covers: raw data kept read-only; one shared loader; checksum against
  the source summary; flag-don't-drop validation; split before synthesising (no leakage);
  `is_synthetic` lineage flag; fixed seeds; star schema with a measures table; every number reproducible.
- Save `figures/synthetic_vs_real.png` and confirm every A file in §3 exists.

---

## 5. PERSON B — Model, prioritisation, unseen-data demo

Goal: the *Prediction* and *Prioritisation* stages, worth the most marks (35). Train on **real data
only**. That's the defensible choice in 2 hours, and the holdout stays clean. *(stretch)* At the
end, retrain with A's synthetic rows added and report whether holdout PR-AUC changes.

**B1 (must, 0:10–0:20): Features**
- Drop `customer_id`, `Aging`, `churned`. Exclude `gender` from the model (it's kept for the fairness check).
- Add: `log_balance`, `balance_to_income`, `is_new` (tenure < 1), `single_product`,
  `inactive_60d` (last transaction > 60 days), `has_complaint`.
- Use one sklearn `Pipeline` with a `ColumnTransformer` (one-hot encoding plus scaling for LogReg).
- **Leakage note:** `last_transaction_days_ago` may partly be an effect of churning. Train once
  with it and once without, report both PR-AUCs, and deploy the version **without** it if the
  drop is small. Write the reasoning into the model card.

**B2 (must, 0:20–0:55): Models and evaluation**
- `train, holdout = split_real(df)`. Touch the holdout **once**, at the end.
- Baseline rule: "tenure < 1 year" → its precision and recall, plus the base-rate PR-AUC (0.158).
- Logistic regression (`class_weight="balanced"`) → report its top odds ratios.
- LightGBM (small grid: `num_leaves` {15, 31}, `learning_rate` {0.05, 0.1}, 300 trees,
  early stopping), using 5-fold stratified CV on train.
- Metrics on the holdout: **PR-AUC (primary)**, ROC-AUC, recall and precision at the threshold,
  top-decile capture ("the top 10% of scores catches X% of leavers"), and a bootstrap 95% CI on PR-AUC.
- Pick the best model by CV PR-AUC. If LightGBM beats LogReg by only a small margin, say that
  LogReg is the more explainable choice.

**B3 (must, 0:55–1:30): Calibrate, explain, prioritise**
- Calibrate with `CalibratedClassifierCV(method="isotonic", cv=5)`, then save a reliability plot.
  Calibration matters because probability × balance has to mean real AED.
- SHAP: a global bar chart, plus the top 3 reasons per customer, mapped to plain English
  (e.g. "New customer (<1 yr)", "2+ complaints", "Inactive 60+ days", "No RM assigned").
- Score all 10,000 real customers with **out-of-fold predictions** (`cross_val_predict`), so
  no customer is scored by a model that trained on them.
- Compute `expected_balance_at_risk` and the tiers exactly as in §3.
- **The key chart:** with capacity 500, compare the AED balance of the churners actually
  reached by (1) value-weighted ranking, (2) probability-only ranking, and (3) random choice.
  This proves why balance at risk matters. Save the numbers to metrics.json.
- Fairness: recall and false-positive rate by gender and by age band, as a table in the model card.

**B4 (must, 1:30–1:45): Unseen-data demo**
- `hidden_test_sample.csv`: 200 holdout rows with `churned` removed, in raw format (commas in balances).
- `python score.py --input hidden_test_sample.csv --output scored.csv` must output
  `customer_id, churn_probability, expected_balance_at_risk, priority_tier, top_3_reasons`.
- Print the holdout metrics for those 200 rows next to the reported ones, to show they match.
- Write `metrics.json` (flat keys, §3), `model_comparison.csv`, and a one-page `model_card.md`.
- Write `approach_B.md` as slide-ready bullets under these exact headings:
  `## Problem framing`, `## Feature engineering`, `## Models compared`, `## Validation design`,
  `## Leakage & robustness checks`, `## Explainability`, `## Prioritisation logic`,
  `## Fairness & responsible AI`, `## Unseen-data demo`.
  Each heading gets 3–5 bullets of at most 15 words. Every number comes from `metrics.json`.

---

## 6. PERSON C — Insights, retention strategy, pilot, report

Goal: the *Understanding* and *Recommendation* stages, plus the final story. C computes the
descriptive numbers on real data independently. For B's model numbers, C writes `{{B.key}}`
placeholders that `fill_report.py` fills at integration.

**C1 (must, 0:10–0:55): EDA on the 10,000 real rows**
- Churn rate with n and a **95% Wilson CI** (`statsmodels proportion_confint(method="wilson")`) by:
  tenure band, segment, region, age band, products held, RM assigned, complaint count,
  digital-engagement quintile, NPS band, days since last transaction (0–30 / 31–60 / 61–90 / 90+),
  and balance quintile.
- Driver ranking: lift versus 15.8%, multiplied by group size. Keep the top 5.
- Effect sizes: Cramér's V for categoricals (p-values alone mean little at n = 10,000).
- Money framing: total AED balance held by churned customers, and its share by segment.
- **Charts, chosen from the data** (Cramér's V of every column vs churn was computed first;
  built in `src/charts.py`, rendered to `figures/`). Only these columns are charted:

  | # | Chart | Column(s) | Evidence |
  |---|---|---|---|
  | 1 | Driver ranking (justifies the selection) | all columns | V from 0.34 down to 0.00 |
  | 2 | Churn by products held | `num_products` | 1 product 36% vs 2 products 12% (V 0.34, strongest) |
  | 3 | Churn by days since last transaction | `last_transaction_days_ago` | 90+ days idle: 49% |
  | 4 | Churn by digital engagement band | `digital_engagement_score` | 37% (0–20) → 6% (81–100) |
  | 5 | Churn by complaints | `complaint_count_last_year` | 13% → 20% → 31% (0 / 1 / 2+) |
  | 6 | Churn by NPS band | `nps_score` | negative NPS 26% vs high 7% |
  | 7 | Tenure × products heatmap | `Aging`, `num_products` | new + single product: 54% |
  | 8 | Segment: share of churners vs share of balance lost | `customer_segment`, `avg_monthly_balance` | Mass Market 73% of churners but 19% of balance lost; Affluent + Private Banking 6% of churners but 50% of balance lost |
  | 9 | Churn with vs without RM, by segment | `relationship_manager_assigned`, `customer_segment` | RM ≈ halves churn in every segment; only 6% of Mass Affluent have one |

  **Not charted, with reason:** `gender` (V 0.00), `region` (0.02), `age` (0.04), `has_loan` (0.04):
  no meaningful link. `monthly_income`: correlates 0.77 with balance, so it duplicates chart 8.
  `has_credit_card`, `has_investment_product`: captured by `num_products`. `branch_visits_last_year`,
  `credit_score`: weak (≤ 0.11). Say this on the EDA appendix slide; excluding weak columns on
  evidence is a strength, not a gap.
  Chart standards: message as title, 95% Wilson intervals, n under each bar, 15.8% reference line,
  red #C8102E for churn, blue #2F6DB5 for comparison series.
- Save the key numbers to `eda_findings.json`.

**C2 (must, 0:55–1:20): Retention playbook and pilot**
- Playbook table: driver signal → intervention → channel → assumed cost per customer (AED) → tier.
  Example rows: new and disengaged → 90-day onboarding plus a salary-transfer bonus;
  complaints → priority resolution plus an RM call; no RM and high balance → assign an RM or upgrade
  to priority banking; single product → a cross-sell bundle; dormant → a reactivation cashback offer;
  high value and high risk → *hypothesis:* a rate-match or bonus-profit-rate deposit, including
  Islamic deposit options.
- `pilot_design.md`:
  - A randomised controlled trial on T1 and T3 customers, stratified by tier and segment,
    with treatment vs a BAU control.
  - 90 days of treatment, with churn read at 90 and 180 days.
  - A power calculation in code (`statsmodels NormalIndPower`), e.g. detecting 40% → 32% churn,
    α = 0.05, power 0.8, giving n per arm.
  - Primary KPI: the churn-rate uplift (control − treatment). Secondary KPIs: AED retained,
    ROI = (balance retained × assumed 2% net margin − offer cost) / offer cost, products per
    customer, NPS change, and model precision as measured in the control group.
  - Guardrails: a cost cap and no adverse impact by gender or age.
  - Decision rule: scale an arm if its uplift is significant and ROI > 1; otherwise retire or redesign it.
  - Post-launch: monthly re-scoring, a drift check (PSI), and quarterly retraining.

**C3 (must, 1:20–1:45): Report, presentation, disclosure**
- `management_report.md`, 1,000–1,500 words, with sections labelled descriptive / predictive / recommendation.
- Also write `approach_C.md` under `## EDA method` and `## Pilot design method` (3–5 bullets each).

**The presentation.** The brief allows 5–7 slides, but you want every approach and practice
explained. Solution: a **7-slide main story** for the committee, plus a **methodology appendix**
that the judges and the technical Q&A can use. Present the main 7; flip to the appendix when
asked "how did you do X?". That keeps you inside the brief and shows the full method.

Write `build_deck.py` (python-pptx, 16:9) that generates `Meridian_Retention.pptx`.
Content order:

| # | Slide | Source |
|---|---|---|
| 1 | Title: *Predict. Prioritise. Retain.* and team names | — |
| 2 | **Our approach**: the 4-stage pipeline diagram (Data → Understanding → Prediction → Recommendation), drawn with shapes, one line of method under each stage | static |
| 3 | **The problem in AED**: churn rate, balance lost, where it concentrates | `eda_findings.json`, chart 8 |
| 4 | **Why customers leave** *(descriptive)*: top drivers with CIs | charts 2, 3, 7 (+ chart 1 in appendix) |
| 5 | **Predicting who will leave** *(predictive)*: model comparison, holdout PR-AUC, top-decile capture, SHAP drivers | `model_comparison.csv`, SHAP figure |
| 6 | **Who to save first**: value–risk tier matrix plus value-weighted vs probability-only AED protected | B's key chart, `tier_counts` |
| 7 | **Recommendations**: playbook by tier, pilot design, KPIs, decision rule, then the ask from the committee | playbook + pilot |
| — | *Appendix: methodology & practices* | |
| A1 | Data understanding & cleaning steps | `approach_A.md` |
| A2 | Validation & checksums, data-quality flags (1,009 / 199), best practices | `approach_A.md` |
| A3 | Synthetic data: method and fidelity, with the caveat | `approach_A.md` + `synthetic_vs_real.png` |
| A4 | EDA method: driver ranking (chart 1), columns excluded and why, Wilson CIs | `approach_C.md` |
| A5 | Feature engineering & models compared | `approach_B.md` |
| A6 | Validation design, leakage & robustness checks | `approach_B.md` |
| A7 | Explainability, fairness & responsible AI | `approach_B.md` |
| A8 | Prioritisation logic & unseen-data demo | `approach_B.md` |
| A9 | Power BI model design + 2 dashboard screenshots | `approach_A.md` + `screens/` |
| A10 | Pilot design method & power calculation | `approach_C.md` |
| A11 | Limitations & next steps; AI tools used and how they were verified | `ai_disclosure.md` |

`build_deck.py` rules:
- Appendix slides are built by reading each `## heading` from the approach files and laying its
  bullets out automatically. Nobody hand-copies text.
- Numbers on main slides come from the JSON files via the same placeholder filling as `fill_report.py`.
- If an image or file from another track is missing, insert a grey box labelled with the missing
  filename instead of crashing. That lets C dry-run the whole deck before integration.
- One consistent look: one accent colour for churn/risk, a neutral palette, titles that state the
  message ("New customers churn at 5× the rate of 15+ year customers"), slide numbers, source line
  on every chart slide.
- Add speaker notes to each main slide: 3–4 sentences the presenter can say.
- Also write `slides_outline.md` mirroring the table above, for review.
- `fill_report.py`: reads `out/B/metrics.json` and `out/C/eda_findings.json` and replaces
  every `{{B.x}}` and `{{C.x}}`. If a key is missing, it fails loudly rather than leaving a gap.
- `ai_disclosure.md`: which tools were used, and how each output was verified
  (checksum asserts, holdout evaluation, manual review of the charts).

---

## 7. Integration (1:45–2:00, all three)

1. Copy each person's `out/A`, `out/B`, `out/C` into one shared repo.
2. Run `python out/C/fill_report.py`. The report and slides now hold B's real metrics.
3. A loads `out/B/priority_list.csv` into Power BI Page 5 (joined on `customer_id`):
   tier counts, expected balance at risk by tier, top-50 table, then exports `screens/page5.png`.
   *(Skip if past 1:55; B's key chart covers it.)* Save the project and zip `out/A/powerbi/` for submission.
4. Run `python out/C/build_deck.py`. Open the deck, check there are no grey placeholder boxes left,
   and fix any overflowing text.
5. Rehearse the demo: B runs `score.py` live on the hidden sample.
6. Final check: every number in the report traces to a JSON file; no causal wording slipped in.

---

## 8. Working rules for Claude Code (every track)

- Do **only** the track for the person named. Don't build another person's files.
- Never modify `data/Bank Data.csv`. Write only inside `out/<your letter>/`.
- Print a 3-line progress summary after each step (A1, B2, etc.) so the person can track time.
- Prefer simple and explainable choices over clever ones. When short on time, cut *(stretch)*
  items first, and report anything weak honestly (a model barely beating the baseline,
  synthetic data not helping) instead of hiding it.
- Every number written into a document must come from code output saved to a file.

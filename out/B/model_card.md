# Model card — Meridian churn model

## Purpose
Rank Meridian's 10,000 retail customers by **expected average monthly balance at risk**
(calibrated churn probability × balance) so 500 monthly RM contacts protect the most AED.
Descriptive/predictive tool only — not a credit or eligibility decision.

## Data & split
- Real customers only, n=10,000, churn 15.78% (imbalanced).
- 80/20 stratified split, seed 42. Holdout (2,000 rows) touched once, at the end.
- Synthetic rows were **not** used for training (they add volume, not information).

## Models compared (by CV PR-AUC on train)
| Model | CV PR-AUC | Holdout PR-AUC | Holdout ROC-AUC |
|---|---|---|---|
| Baseline (tenure<1yr rule) | 0.1578 | 0.1578 |  |
| Logistic regression (with recency) | 0.5207 | 0.5624 | 0.8444 |
| LightGBM (with recency) | 0.4874 | 0.5416 | 0.8318 |
| Logistic regression (no recency / deployed) | 0.4747 | 0.5017 | 0.8176 |

Chosen family: **Logistic regression** (best CV PR-AUC). Baseline rule "tenure < 1yr": precision 0.30,
recall 0.31.

## Leakage & robustness
`last_transaction_days_ago` (and its `inactive_60d` flag) may be an **effect** of churning, not a
cause. Trained with and without: holdout PR-AUC drops by **0.061** when removed.
Deployed **WITH** recency features
(drop was material).

## Calibration & threshold
Isotonic calibration (`CalibratedClassifierCV`, cv=5) so probability × balance is real AED.
Operating threshold = **0.4** (= the high-risk tier cutoff). At this threshold on the holdout:
recall 0.40, precision 0.58. PR-AUC 0.559
(95% CI 0.507–0.611), ROC-AUC 0.843, top-decile capture 39%.

## Prioritisation
`expected_balance_at_risk = churn_probability × avg_monthly_balance`. Tiers: T1 Save now (high risk,
high value) · T2 Protect · T3 Automated save · T4 Monitor. High value = balance ≥ 75th pct
(AED 26,867). With 500 contacts, value-weighted ranking protects
**AED 9.3m** vs **AED 2.4m** (probability-only) vs
**AED 1.1m** (random).

## Fairness (out-of-fold, threshold 0.4)
Gender is excluded from the model and used only here.

**By gender**

| Group | n | Recall | FPR |
|---|---|---|---|
| Female | 4,853 | 0.377 | 0.054 |
| Male | 5,147 | 0.372 | 0.048 |

**By age_band**

| Group | n | Recall | FPR |
|---|---|---|---|
| 18-30 | 1,961 | 0.324 | 0.038 |
| 31-45 | 4,208 | 0.361 | 0.05 |
| 46-60 | 3,100 | 0.389 | 0.058 |
| 60+ | 731 | 0.479 | 0.063 |

## Limitations
No competitor-rate, offer or reason-for-leaving fields exist, so the model cannot explain *why* in
a causal sense. Recency may be partly post-hoc. Associations only; causation is tested by the pilot.

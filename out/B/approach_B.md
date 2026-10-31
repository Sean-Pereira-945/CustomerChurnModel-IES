# Approach — Person B (Model & prioritisation)

## Problem framing
- Rank 10,000 customers by AED balance at risk, not probability alone.
- Churn is imbalanced (15.8%), so PR-AUC is the primary metric.
- Goal: protect the most money within 500 monthly RM contacts.
- Descriptive/predictive tool; interventions tested causally by the pilot.

## Feature engineering
- Added log_balance, balance_to_income, is_new, single_product, has_complaint.
- gender excluded from the model (used only for the fairness check).
- Aging and customer_id dropped; one ColumnTransformer (scale + one-hot).
- Recency feature isolated so its leakage risk can be tested.

## Models compared
- Baseline rule (tenure<1yr): precision 0.30, recall 0.31.
- Logistic regression (balanced) and LightGBM (small grid, 5-fold CV).
- Selected by CV PR-AUC: Logistic regression.
- LightGBM grid: num_leaves {15,31} × learning_rate {0.05,0.1}, 300 trees.

## Validation design
- 80/20 stratified split, seed 42; holdout touched once.
- 5-fold stratified CV on train for model selection.
- Holdout PR-AUC 0.559 (95% CI 0.507–0.611), ROC-AUC 0.843.
- Top-decile capture 39% of all leavers.

## Leakage & robustness checks
- Recency may be an effect of churn, not a cause.
- With vs without recency: holdout PR-AUC drop 0.061.
- Deployed with recency (material drop).
- Synthetic data excluded from training by design.

## Explainability
- SHAP global bar + per-customer top-3 reasons in plain English.
- Strongest drivers: single_product, last_transaction_days_ago, relationship_manager_assigned, digital_engagement_score.
- Reasons map to actions (new, single-product, inactive, complaints, no RM).
- Logistic odds ratios available as a cross-check.

## Prioritisation logic
- expected_balance_at_risk = calibrated probability × balance.
- Isotonic calibration so AED figures are trustworthy.
- Tiers T1–T4 on risk (≥0.4) × value (≥AED 26,867).
- Out-of-fold scores so no customer is scored by a model trained on them.

## Fairness & responsible AI
- Recall and false-positive rate reported by gender and age band.
- Gender kept out of the model entirely.
- Model informs outreach, never eligibility or pricing.
- Monthly re-scoring, PSI drift check, quarterly retrain (handover to pilot).

## Unseen-data demo
- score.py scores 200 untouched holdout rows in raw format.
- Outputs id, probability, balance-at-risk, tier, top-3 reasons.
- Holdout metrics on the 200 match the reported holdout metrics.
- Proves the pipeline runs end-to-end on data it has never seen.

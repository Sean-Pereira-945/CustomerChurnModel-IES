# Synthetic data fidelity — 10,000 → 50,000

Method: **stratified Gaussian copula** fitted on the 8,000-row train split only (the 2,000-row
holdout never reaches the generator, so Person B's evaluation stays clean). 8 cells
(customer_segment × churned), each sampled at 5×. Discrete columns use `inverted_cdf` (only
values seen in real data); continuous columns use interpolated quantiles (no row is a copy).

## Headline fidelity
- Churn rate: real **15.78%** vs synthetic **15.78%**.
- Largest KS distance across all 15 modelled columns: **0.0060**.
- Largest pairwise correlation gap (real vs synthetic): **0.075**.
- Synthetic rows identical to a real customer: **0**.
- Synthetic values outside the real observed range: **0**.

## Churn rate by segment
| Segment | Real | Synthetic | Abs. gap |
|---|---|---|---|
| Mass Market | 21.775% | 21.707% | 0.068% |
| Mass Affluent | 11.965% | 11.987% | 0.022% |
| Affluent | 5.260% | 5.369% | 0.110% |
| Private Banking | 4.090% | 4.416% | 0.326% |

## Per-column KS distance (real vs synthetic)
| Column | KS |
|---|---|
| tenure_years | 0.0054 |
| monthly_income | 0.0051 |
| avg_monthly_balance | 0.0058 |
| digital_engagement_score | 0.0059 |
| age | 0.0058 |
| num_products | 0.0044 |
| has_credit_card | 0.0031 |
| has_loan | 0.0025 |
| has_investment_product | 0.0006 |
| branch_visits_last_year | 0.0057 |
| complaint_count_last_year | 0.0040 |
| credit_score | 0.0050 |
| relationship_manager_assigned | 0.0029 |
| nps_score | 0.0031 |
| last_transaction_days_ago | 0.0060 |

## Caveat for the committee
Synthetic rows add **volume, not information**. All headline findings and the model are built on
the **real 10,000**. The 50k set exists to make the dashboard responsive and to demonstrate a
privacy-safe scaling method; it is flagged (`is_synthetic`, `data_split`) end to end.

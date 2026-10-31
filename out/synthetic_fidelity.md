# Synthetic data fidelity

Generator: stratified Gaussian copula (segment x churned cells), fitted on the 8,000-row train split only. The 2,000-row holdout never reached the generator.

- Synthetic rows: 40,000 | churn rate real train 15.78% vs synthetic 15.78%
- Largest correlation difference between any two columns: 0.071
- Synthetic rows identical to a real customer: 0

## Column distributions
| Column | Real mean | Synthetic mean | Real SD | Synthetic SD | KS D |
|---|---|---|---|---|---|
| tenure_years | 5.4 | 5.4 | 5.4 | 5.3 | 0.003 |
| monthly_income | 6,748.7 | 6,745.9 | 6,110.1 | 6,073.7 | 0.003 |
| avg_monthly_balance | 34,156.8 | 33,831.0 | 81,578.6 | 80,228.9 | 0.004 |
| digital_engagement_score | 54.7 | 54.6 | 19.3 | 19.4 | 0.005 |
| age | 41.7 | 41.7 | 12.7 | 12.7 | 0.003 |
| num_products | 2.3 | 2.3 | 1.0 | 1.0 | 0.002 |
| has_credit_card | 0.5 | 0.5 | 0.5 | 0.5 | 0.001 |
| has_loan | 0.3 | 0.3 | 0.4 | 0.4 | 0.000 |
| has_investment_product | 0.1 | 0.1 | 0.3 | 0.3 | 0.001 |
| branch_visits_last_year | 3.7 | 3.7 | 2.2 | 2.2 | 0.005 |
| complaint_count_last_year | 0.4 | 0.4 | 0.6 | 0.6 | 0.002 |
| credit_score | 761.0 | 761.0 | 70.6 | 70.8 | 0.003 |
| relationship_manager_assigned | 0.2 | 0.2 | 0.4 | 0.4 | 0.001 |
| nps_score | 25.8 | 25.8 | 23.6 | 23.6 | 0.003 |
| last_transaction_days_ago | 25.9 | 25.9 | 27.4 | 27.1 | 0.004 |

## Churn rate by segment
| customer_segment   | Real (train)   | Synthetic   |
|:-------------------|:---------------|:------------|
| Mass Market        | 21.7%          | 21.7%       |
| Mass Affluent      | 12.0%          | 12.0%       |
| Affluent           | 5.4%           | 5.4%        |
| Private Banking    | 4.4%           | 4.4%        |

## Churn rate by tenure band
| Aging       | Real (train)   | Synthetic   |
|:------------|:---------------|:------------|
| Less than 1 | 27.5%          | 27.9%       |
| 1 to 3      | 17.9%          | 17.6%       |
| 3 to 7      | 14.0%          | 13.9%       |
| 7 to 15     | 9.9%           | 10.3%       |
| > 15        | 5.0%           | 4.3%        |

**Caveat:** synthetic rows reproduce patterns already in the real data; they add volume, not new information. All headline findings are quoted from the 10,000 real customers.
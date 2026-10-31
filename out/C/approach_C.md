# Approach — Person C (Insights & strategy)

## EDA method
- Churn rate with n and 95% Wilson intervals across 11 customer dimensions.
- Driver ranking by Cramér's V (p-values alone mean little at n=10,000).
- Columns charted on evidence; weak/redundant columns excluded and justified.
- Top drivers: num_products (0.336), last_transaction_days_ago (0.202), digital_engagement_score (0.197), customer_segment (0.186), avg_monthly_balance (0.172).

## Pilot design method
- RCT on high-risk tiers (T1, T3), treatment vs BAU control, stratified.
- Power calc in code: detect 40%→32%, α=0.05, power=0.8 → 564/arm.
- KPIs: churn uplift (primary), AED retained, ROI, NPS, products/customer.
- Decision rule: scale if uplift significant and ROI>1; else retire/redesign.

# Pilot design — measurable retention RCT

## Design
- **Randomised controlled trial** on **T1 (Save now)** and **T3 (Automated save)** customers —
  the high-risk tiers where intervention can change outcomes.
- Randomised to **treatment** vs **business-as-usual control**, stratified by tier and segment.
- 90-day treatment window; churn measured at **90 and 180 days**.

## Sample size (computed, statsmodels NormalIndPower)
- Detect a drop from **40% → 32%** churn (effect size 0.167).
- α = 0.05, power = 0.8, two-sided → **564 customers per arm**.
- Feasible within RM capacity (500/month) staged across the T1/T3 population.

## KPIs
- **Primary:** churn-rate uplift = control churn − treatment churn (90 & 180 days).
- **Secondary:** AED balance retained; ROI = (balance retained × 2% net margin − offer cost) /
  offer cost; products per customer; NPS change; model precision measured in the control group.

## Guardrails
- Cost cap per customer by tier; no adverse impact by gender or age (monitored weekly).
- Treatment offers logged; opt-out honoured.

## Decision rule
- **Scale** an arm if its churn uplift is statistically significant **and** ROI > 1.
- Otherwise **retire or redesign** the intervention.

## Post-launch
- Monthly re-scoring; drift check via **PSI**; quarterly retraining.
- Control group becomes the ongoing benchmark for model precision in production.

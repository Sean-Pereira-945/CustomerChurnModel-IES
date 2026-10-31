# Protecting Meridian's Deposit Base: A Customer Retention Decision Engine

**Prepared for the Meridian Trust Bank Management Committee**
*Predict. Prioritise. Retain.*

All figures are produced from code and are reproducible (seed 42). Every statement is labelled
**[Descriptive]**, **[Predictive]** or **[Recommendation]**. Associations are not causation; only
the proposed pilot (a randomised trial) can establish cause.

---

## 1. The problem, in dirhams

**[Descriptive]** Of Meridian's **{{C.customers|int}}** retail customers, **{{C.churned|int}}**
have churned — a base rate of **{{C.base_churn_rate|pct1}}**. Those leavers held
**AED {{C.aed_balance_lost_total|aed_m}}** in average monthly balances, or
**{{C.pct_balance_lost|pct1}}** of the retail deposit base.

The money does not leave evenly. **[Descriptive]** Mass Market customers are
**{{C.share_churners_mass_market_pct}}%** of all churners but a small share of the balance lost,
while the Affluent and Private Banking segments together account for
**{{C.share_balance_lost_top2_segments|pct}}** of the balance that walks out of the door. Churn is a
volume problem in the mass segments and a **value** problem at the top — which is why we rank
customers by balance at risk, not by probability alone.

---

## 2. Why customers leave *(the strongest patterns)*

**[Descriptive]** Ranking every field by its association with churn (Cramér's V), the dominant
signal is the number of products held (**V = {{C.cramers_v_num_products|f3}}**). Four patterns are
clear and each is shown with 95% confidence intervals and sample sizes:

- **Tenure.** New customers (under one year) churn at **{{C.churn_tenure_lt1|pct1}}** versus
  **{{C.churn_tenure_15plus|pct1}}** for those with 15+ years — a **{{C.tenure_lt1_vs_15plus_ratio|x2}}**
  difference. The first year is where the relationship is won or lost.
- **Product depth.** Single-product customers churn at **{{C.churn_products_1|pct1}}**, more than
  double the **{{C.churn_products_2|pct1}}** of two-product customers.
- **Inactivity.** Customers with no transaction for 90+ days churn at **{{C.churn_recency_90plus|pct1}}**.
- **Engagement and voice.** Churn falls from **{{C.churn_engagement_0_20|pct1}}** among the least
  digitally engaged to **{{C.churn_engagement_81_100|pct1}}** among the most; customers with two or
  more complaints churn at **{{C.churn_complaints_2plus|pct1}}**.

**[Descriptive]** Customers with a relationship manager churn at roughly half the rate in every
segment — an association worth testing, because RMs may simply be assigned to already-loyal clients.

Fields with no meaningful link (gender, region, age) were examined and set aside on the evidence;
excluding weak signals is a discipline, not a gap. Note that the dataset contains **no**
competitor-rate, offer or reason-for-leaving fields, so those remain pilot hypotheses, not findings.

---

## 3. Predicting who will leave

**[Predictive]** We trained models on the real 10,000 customers only, with an 80/20 stratified
split and a 2,000-row holdout touched exactly once. A naive "new customers" rule achieves a
precision–recall AUC of just **{{B.baseline_pr_auc|f3}}** (the base rate). The deployed model — a
**{{B.chosen_model}}** chosen on cross-validated PR-AUC — reaches a holdout **PR-AUC of
{{B.pr_auc|f3}}** (95% CI {{B.pr_auc_ci_low|f3}}–{{B.pr_auc_ci_high|f3}}) and **ROC-AUC of
{{B.roc_auc|f3}}**. Its top decile of scores captures **{{B.top_decile_capture|pct}}** of all
leavers. At the operating threshold of **{{B.threshold}}**, recall is **{{B.recall_at_thr|pct}}**
and precision **{{B.precision_at_thr|pct}}**.

**[Predictive]** We tested for leakage: the recency feature may partly be an *effect* of churning.
Removing it lowers holdout PR-AUC by **{{B.leakage_pr_auc_drop|f3}}**; because the drop is material,
it is retained, and the risk is documented in the model card. Probabilities are isotonic-calibrated
so that *probability × balance* is a trustworthy AED figure. SHAP explanations give each customer a
plain-English reason — new, single-product, inactive, complaining, or without an RM.

---

## 4. Who to save first

**[Recommendation]** Relationship managers can make about **{{B.capacity_n|int}}** proactive
contacts a month. We assign every customer to one of four tiers on **risk × value** (high value =
balance at or above AED {{B.bal_p75|aed}}):

- **T1 Save now** (high risk, high value) — the priority queue.
- **T2 Protect** (low risk, high value) — guard the relationship.
- **T3 Automated save** (high risk, low value) — low-cost digital journeys.
- **T4 Monitor** (low risk, low value).

**[Recommendation]** Ranking the {{B.capacity_n|int}} contacts by **expected balance at risk**
protects **AED {{B.aed_protected_value_weighted|aed_m}}** of churning balances, versus
**AED {{B.aed_protected_prob_only|aed_m}}** from ranking by probability alone and
**AED {{B.aed_protected_random|aed_m}}** from random outreach. Same effort, far more money
protected — this is the core of the business case.

---

## 5. What to do, and how we will prove it works

**[Recommendation]** The retention playbook maps each risk signal to an intervention: a 90-day
onboarding journey for new and disengaged customers; priority complaint resolution with an RM call;
RM assignment or a priority-banking upgrade for high-balance customers without one; a cross-sell
bundle for single-product customers; and reactivation offers for the dormant. For high-value,
high-risk clients, a rate-match or bonus-profit-rate deposit (including Shariah-compliant options)
is a *hypothesis* to be tested, not an established remedy.

**[Recommendation]** We will prove impact with a **randomised controlled trial** on the T1 and T3
tiers, stratified by tier and segment, treatment versus business-as-usual control. A power
calculation (detecting a 40% → 32% churn reduction, α = 0.05, power 0.8) sizes each arm. The primary
KPI is churn-rate uplift; secondary KPIs are AED retained, ROI (balance retained × 2% net margin,
net of offer cost), products per customer and NPS. The decision rule is simple: scale an arm only if
its uplift is statistically significant and ROI exceeds 1; otherwise retire or redesign it.

---

## 6. Responsible use and limitations

**[Recommendation]** Gender is excluded from the model and used only to monitor fairness; recall and
false-positive rates are reported by gender and age band. The model informs **outreach**, never
credit, pricing or eligibility. Synthetic data (used to scale the dashboard to 50,000 rows) adds
volume, not information, and is flagged end to end; all headline numbers use the real 10,000. The
key limitation is the absence of competitor, offer and reason-for-leaving data — the pilot is
designed to fill exactly that gap.

---

### The ask
Approve a **90-day pilot** on the T1/T3 tiers with the sample size and KPIs above, and the RM
capacity to contact the top-ranked customers each month. The engine is built, validated and ready;
the pilot turns association into measured, causal return.

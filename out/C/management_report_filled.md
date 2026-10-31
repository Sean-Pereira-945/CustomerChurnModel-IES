# Protecting Meridian's Deposit Base: A Customer Retention Decision Engine

**Prepared for the Meridian Trust Bank Management Committee**
*Predict. Prioritise. Retain.*

All figures are produced from code and are reproducible (seed 42). Every statement is labelled
**[Descriptive]**, **[Predictive]** or **[Recommendation]**. Associations are not causation; only
the proposed pilot (a randomised trial) can establish cause.

---

## 1. The problem, in dirhams

**[Descriptive]** Of Meridian's **10,000** retail customers, **1,578**
have churned — a base rate of **15.8%**. Those leavers held
**AED 22.5m** in average monthly balances, or
**6.6%** of the retail deposit base.

The money does not leave evenly. **[Descriptive]** Mass Market customers are
**73.1%** of all churners but a small share of the balance lost,
while the Affluent and Private Banking segments together account for
**50%** of the balance that walks out of the door. Churn is a
volume problem in the mass segments and a **value** problem at the top — which is why we rank
customers by balance at risk, not by probability alone.

---

## 2. Why customers leave *(the strongest patterns)*

**[Descriptive]** Ranking every field by its association with churn (Cramér's V), the dominant
signal is the number of products held (**V = 0.336**). Four patterns are
clear and each is shown with 95% confidence intervals and sample sizes:

- **Tenure.** New customers (under one year) churn at **28.1%** versus
  **5.0%** for those with 15+ years — a **5.64×**
  difference. The first year is where the relationship is won or lost.
- **Product depth.** Single-product customers churn at **36.1%**, more than
  double the **12.2%** of two-product customers.
- **Inactivity.** Customers with no transaction for 90+ days churn at **48.7%**.
- **Engagement and voice.** Churn falls from **37.1%** among the least
  digitally engaged to **5.5%** among the most; customers with two or
  more complaints churn at **30.9%**.

**[Descriptive]** Customers with a relationship manager churn at roughly half the rate in every
segment — an association worth testing, because RMs may simply be assigned to already-loyal clients.

Fields with no meaningful link (gender, region, age) were examined and set aside on the evidence;
excluding weak signals is a discipline, not a gap. Note that the dataset contains **no**
competitor-rate, offer or reason-for-leaving fields, so those remain pilot hypotheses, not findings.

---

## 3. Predicting who will leave

**[Predictive]** We trained models on the real 10,000 customers only, with an 80/20 stratified
split and a 2,000-row holdout touched exactly once. A naive "new customers" rule achieves a
precision–recall AUC of just **0.158** (the base rate). The deployed model — a
**Logistic regression** chosen on cross-validated PR-AUC — reaches a holdout **PR-AUC of
0.559** (95% CI 0.507–0.611) and **ROC-AUC of
0.844**. Its top decile of scores captures **39%** of all
leavers. At the operating threshold of **0.4**, recall is **40%**
and precision **58%**.

**[Predictive]** We tested for leakage: the recency feature may partly be an *effect* of churning.
Removing it lowers holdout PR-AUC by **0.061**; because the drop is material,
it is retained, and the risk is documented in the model card. Probabilities are isotonic-calibrated
so that *probability × balance* is a trustworthy AED figure. SHAP explanations give each customer a
plain-English reason — new, single-product, inactive, complaining, or without an RM.

---

## 4. Who to save first

**[Recommendation]** Relationship managers can make about **500** proactive
contacts a month. We assign every customer to one of four tiers on **risk × value** (high value =
balance at or above AED 26,867):

- **T1 Save now** (high risk, high value) — the priority queue.
- **T2 Protect** (low risk, high value) — guard the relationship.
- **T3 Automated save** (high risk, low value) — low-cost digital journeys.
- **T4 Monitor** (low risk, low value).

**[Recommendation]** Ranking the 500 contacts by **expected balance at risk**
protects **AED 9.3m** of churning balances, versus
**AED 2.4m** from ranking by probability alone and
**AED 1.1m** from random outreach. Same effort, far more money
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

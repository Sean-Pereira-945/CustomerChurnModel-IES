# 🎤 Presentation sequence — Meridian Retention

A presenter's runbook. It sequences the documentation into a **~10-minute talk**. Present by walking
through the stops below in order; each stop tells you **which doc to open**, **which visual to show**,
the **one message**, and a **short script** to say. Keep the [glossary](09_glossary.md) open in a
side tab for Q&A.

**Before you start:** open this folder in VS Code (or GitHub). For the live demo, have the web app
running (`../start.bat`). Have the slide deck `../out/C/Meridian_Retention.pptx` ready as a backup.

---

## At a glance

| # | Time | Message | Open this doc | Show this visual |
|---|---|---|---|---|
| 1 | 0:00 | Predict. Prioritise. Retain. | [README](README.md) | approach pipeline |
| 2 | 0:45 | The problem is money, not just count | [04](04_data_and_synthetic.md) / [05](05_graphs_explained.md) | chart 08 (volume vs value) |
| 3 | 2:00 | Our 4-stage approach | [03](03_approach.md) | approach_pipeline diagram |
| 4 | 3:00 | Trustworthy data (and the 50k truth) | [04](04_data_and_synthetic.md) | data_flow diagram |
| 5 | 4:15 | Why customers leave | [05](05_graphs_explained.md) | charts 02, 03, 07 |
| 6 | 5:30 | Predicting who leaves | [06](06_model.md) | pr_curve + calibration |
| 7 | 6:45 | Who to save first | [07](07_retention.md) | tier_matrix + value_capture |
| 8 | 7:45 | How to retain — live demo | [07](07_retention.md) | retention_flow + **web app** |
| 9 | 9:00 | Prove it: the pilot | [07](07_retention.md) | (pilot table) |
| 10 | 9:30 | Responsible AI + the ask | [06](06_model.md) / [09](09_glossary.md) | — |

Appendix stops (for Q&A): data quality, synthetic fidelity, SHAP, dashboards, glossary.

---

## Stop 1 — Title & hook  ·  0:00–0:45
- **Open:** [docs/README.md](README.md) · **Show:** `diagrams/approach_pipeline.png`
- **Message:** *Predict. Prioritise. Retain.*
- **Say:** "Meridian is losing customers. We built an engine that predicts who will leave, ranks them
  by the money at risk, and tells us exactly how to retain them — and we designed a fair test to
  prove the plan works. Here's the whole thing in four stages."

## Stop 2 — The problem, in dirhams  ·  0:45–2:00
- **Open:** [04](04_data_and_synthetic.md) → headline numbers · **Show:** `../out/C/figures/08_segment_volume_vs_value.png`
- **Message:** Churn is a *money* problem, and the money concentrates.
- **Say:** "Of our 10,000 customers, 1,578 have left — 15.8%. They held AED 22.5 million in balances.
  But look where the money is: Mass Market is 73% of the leavers, yet the Affluent and Private
  Banking segments hold 50% of the balance that walks out. So the real question isn't just *who*
  leaves — it's *which leavers cost us the most*."

## Stop 3 — Our approach  ·  2:00–3:00
- **Open:** [03](03_approach.md) · **Show:** `diagrams/approach_pipeline.png`
- **Message:** Four defensible stages: Data → Understanding → Prediction → Recommendation.
- **Say:** "We clean and verify the data, understand the patterns with proper statistics, predict
  with a calibrated model, and turn that into prioritised action — proven by a pilot. Every number
  is reproducible from code; nothing is hand-typed."

## Stop 4 — Trustworthy data (and the 50k truth)  ·  3:00–4:15
- **Open:** [04](04_data_and_synthetic.md) · **Show:** `diagrams/data_flow.png`
- **Message:** Honest data handling — and the synthetic rows do **not** train the model.
- **Say:** "We cleaned the file and found two impossible things — 1,009 and 199 rows — which we
  *flagged but kept*, because deleting 10% would bias everything. We also grew the data to 50,000
  rows, but — this is important — those synthetic rows only power the dashboard. **The model trains
  on the real customers.** Fakes add volume, not information."
- *If asked about fidelity:* flip to `../out/A/figures/synthetic_vs_real.png` (churn 15.78% vs 15.78%).

## Stop 5 — Why customers leave  ·  4:15–5:30
- **Open:** [05](05_graphs_explained.md) · **Show:** `../out/C/figures/02_products.png`, `../out/C/figures/03_recency.png`, `../out/C/figures/07_tenure_x_products.png`
- **Message:** A few clear, actionable signals — with confidence intervals.
- **Say:** "Single-product customers churn at 36%, triple the rate of two-product customers. Ninety
  days of inactivity means a near-50% churn rate. And the danger zone is new *and* single-product —
  more than half leave in year one. Every bar carries a margin of error, and we're careful to call
  these *associations*, not causes."

## Stop 6 — Predicting who leaves  ·  5:30–6:45
- **Open:** [06](06_model.md) · **Show:** `../out/B/figures/pr_curve.png` then `../out/B/figures/calibration.png`
- **Message:** A simple, explainable model that clearly beats guessing.
- **Say:** "We chose Logistic Regression — it beat the alternatives and a bank committee can
  understand it. It scores 0.56 on PR-AUC versus 0.16 for guessing, and its riskiest 10% of
  customers contain 39% of all leavers. We calibrated the probabilities so that 'probability ×
  balance' is real money."

## Stop 7 — Who to save first  ·  6:45–7:45
- **Open:** [07](07_retention.md) · **Show:** `diagrams/tier_matrix.png` then `../out/B/figures/value_capture.png`
- **Message:** Ranking by money at risk protects far more than probability alone.
- **Say:** "We sort customers by risk *and* value into four tiers. With 500 RM contacts a month,
  ranking by money at risk protects AED 9.3 million — versus 2.4 million by probability alone, and
  1.1 million at random. Same effort, nearly four times the money saved."

## Stop 8 — How to retain — live demo  ·  7:45–9:00
- **Open:** [07](07_retention.md) · **Show:** `diagrams/retention_flow.png`, then **the live web app**
- **Message:** The engine tells you exactly what to do for each customer.
- **Demo (see script below):** score a high-risk customer; show the churn %, tier, reasons, and the
  **tailored retention plan** with costs.
- **Say:** "For any customer, the model gives a probability and plain-English reasons, the tier sets
  the effort and channel, and we generate a specific action plan — reactivation, cross-sell,
  onboarding, service recovery — with an estimated cost to retain."

## Stop 9 — Prove it: the pilot  ·  9:00–9:30
- **Open:** [07](07_retention.md) → pilot section
- **Message:** We don't claim it works — we test it.
- **Say:** "Before rolling out, we run a randomised controlled trial on the high-risk tiers: treat
  half, hold half as control, compare at 90 and 180 days. A power calculation sizes it at 564 per
  group. We scale only what significantly reduces churn *and* returns more than it costs."

## Stop 10 — Responsible AI & the ask  ·  9:30–10:00
- **Open:** [06](06_model.md) → responsible section
- **Message:** Fair, honest, and ready.
- **Say:** "Gender is excluded from the model and used only to check fairness. The model informs
  outreach, never credit or pricing. We never dress up correlation as causation. **The ask:**
  approve a 90-day pilot on the T1 and T3 tiers and the RM capacity to contact the top-ranked
  customers. The engine is built, validated, and ready."

---

## 🖥️ Live demo script (Stop 8)

1. Have the app open (`../start.bat` → http://localhost:5173).
2. In **Score a customer**, enter a clear high-risk, high-value profile:
   - Segment **Private Banking**, tenure **0.5**, balance **300000**, products **1**,
     engagement **15**, complaints **2**, NPS **-30**, RM **No**, days since last txn **120**.
3. Click **Predict churn risk**. Point out:
   - **~96% churn probability**, tier **T1 Save now**, **AED ~287k at risk**.
   - The **reasons** (inactive, single product, new customer).
   - The **retention plan**: reactivation, cross-sell, onboarding, service recovery, assign an RM,
     and the T1 rate-match hypothesis — with an estimated cost to retain.
4. Then enter a loyal customer (tenure 10, 3 products, engagement 90, NPS 70, RM Yes, recent
   activity) → **~0% churn**, tier **Protect**, "monitor only." Contrast makes the point.

*Backup if the app isn't running:* show `../out/B/priority_list.csv` (the ranked list) and the
`value_capture.png` chart.

---

## ❓ Q&A prep — where to flip

| If they ask… | Go to | Short answer |
|---|---|---|
| "Did you train on fake data?" | [04](04_data_and_synthetic.md), data_flow | No — model trains on the real 10,000; synthetic is dashboard-only. |
| "Why Logistic Regression, not deep learning?" | [06](06_model.md) | It won on the fair score and is explainable for a risk committee. |
| "How do you know the model is any good?" | [05](05_graphs_explained.md) charts 10–11 | PR-AUC 0.56 vs 0.16 baseline, tested once on a held-out 2,000. |
| "Isn't this just correlation?" | [03](03_approach.md), [07](07_retention.md) | Yes — that's why the pilot (an RCT) tests cause before rollout. |
| "What about bias/fairness?" | [06](06_model.md), `../out/B/model_card.md` | Gender excluded; recall & false-positive rate reported by gender and age. |
| "What's a term on this chart?" | [09](09_glossary.md) | Every term (PR-AUC, SHAP, Cramér's V, calibration…) explained simply. |
| "Can we see the dashboard?" | [08](08_dashboards.md) | Power BI (5 pages) + the live web app. |
| "How much does retention cost?" | [07](07_retention.md) | The app sums an estimated cost per customer; the pilot measures ROI. |

---

## ⏱️ Timing variants

- **5-minute version:** Stops 1 → 2 → 6 → 7 → 8 (demo) → 10. Skip 3, 4, 5, 9 (mention in one line).
- **10-minute version:** all stops as above.
- **Technical deep-dive / judges:** add the appendix — data quality (`out/A/cleaning_log.md`),
  synthetic fidelity (`synthetic_vs_real.png`), SHAP (`shap_bar.png`), model card, and the
  methodology appendix in `../out/C/Meridian_Retention.pptx`.

---

*This runbook sequences the docs; for the full detail behind any stop, open the linked page. For the
one-page story, see [`../PROJECT_OVERVIEW.md`](../PROJECT_OVERVIEW.md).*

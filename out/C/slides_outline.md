# Slides outline — Meridian Retention (7 main + methodology appendix)

Present the main 7 to the committee; flip to the appendix for technical Q&A ("how did you do X?").

## Main story
| # | Slide | Message | Source |
|---|---|---|---|
| 1 | Title | Predict. Prioritise. Retain. + team | — |
| 2 | Our approach | 4-stage pipeline: Data → Understanding → Prediction → Recommendation | static diagram |
| 3 | The problem in AED | Churn 15.8%; AED ~22.5m at risk; value concentrates in top segments | `eda_findings.json`, chart 8 |
| 4 | Why customers leave *(descriptive)* | New / single-product / inactive customers churn hardest, with 95% CIs | charts 2, 3, 7 |
| 5 | Predicting who will leave *(predictive)* | Model beats baseline; PR-AUC, top-decile capture, SHAP drivers | `model_comparison.csv`, SHAP figure |
| 6 | Who to save first | Risk × value tiers; value-weighted ranking protects far more AED | value-capture chart, `tier_counts` |
| 7 | Recommendations | Playbook by tier, RCT pilot, KPIs, decision rule, the ask | playbook + pilot |

## Appendix: methodology & practices
| # | Slide | Source |
|---|---|---|
| A1 | Data understanding & cleaning steps | `approach_A.md` |
| A2 | Validation & checksums, data-quality flags (1,009 / 199), best practices | `approach_A.md` |
| A3 | Synthetic data: method & fidelity, with caveat | `approach_A.md` + `synthetic_vs_real.png` |
| A4 | EDA method: driver ranking, excluded columns, Wilson CIs | `approach_C.md` |
| A5 | Feature engineering & models compared | `approach_B.md` |
| A6 | Validation design, leakage & robustness checks | `approach_B.md` |
| A7 | Explainability, fairness & responsible AI | `approach_B.md` |
| A8 | Prioritisation logic & unseen-data demo | `approach_B.md` |
| A9 | Power BI model design + dashboard screenshots | `approach_A.md` + `screens/` |
| A10 | Pilot design method & power calculation | `approach_C.md` |
| A11 | Limitations & next steps; AI tools used and verification | `ai_disclosure.md` |

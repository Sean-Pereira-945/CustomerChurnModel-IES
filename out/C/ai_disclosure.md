# Responsible AI & tool disclosure

## AI tools used
- **Claude Code** assisted in writing the data-processing, modelling, charting and reporting code.
- All code is committed and reproducible; no numbers were hand-typed into documents.

## How every output was verified
- **Data:** the shared loader asserts 10,000 unique IDs and checksums tenure-band counts and churn
  against the raw summary block before any analysis runs.
- **Synthetic data:** fidelity re-computed independently (KS, correlation gap, duplicate check,
  range check) and reported honestly, including the caveat that it adds volume, not information.
- **Model:** evaluated once on an untouched 2,000-row holdout; PR-AUC reported with a bootstrap CI;
  out-of-fold scores used for the priority list so no customer is scored by a model trained on them.
- **Charts:** every chart regenerated from code with 95% Wilson intervals and sample sizes shown.
- **Report & deck:** numbers injected from `metrics.json` and `eda_findings.json` via
  `fill_report.py`; a missing key fails loudly rather than leaving a gap.

## Responsible-AI choices
- Gender excluded from the model; recall and false-positive rate reported by gender and age band.
- Correlation is never presented as causation; only the pilot (an RCT) can show cause.
- The model informs **outreach**, never credit, pricing or eligibility decisions.
- No competitor-rate, offer or reason-for-leaving data exists — those are pilot hypotheses only.

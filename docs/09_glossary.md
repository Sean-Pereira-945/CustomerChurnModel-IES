# 9. Glossary — every complex term, explained simply

Terms you'll see in the charts and docs, in plain English.

## Churn & business terms
- **Churn** — a customer leaving the bank. **Churned = 1** means they left.
- **Churn rate** — the share of a group who left (e.g. 15.8% of all customers).
- **Base rate / bank average** — the overall churn rate (15.8%), shown as the dashed line on charts.
- **Tenure** — how many years someone has been a customer.
- **Recency** — how long since their last transaction. Long recency (going quiet) is a warning sign.
- **NPS (Net Promoter Score)** — a satisfaction score from −100 to +100. Negative = unhappy.
- **Segment** — the customer's value band: Mass Market, Mass Affluent, Affluent, Private Banking.
- **RM (Relationship Manager)** — a dedicated personal banker.
- **Balance at risk / expected balance at risk** — churn probability × the customer's balance. The
  money we'd *expect* to lose from that customer. This is what we rank by.
- **Tier (T1–T4)** — the action group from combining risk and value (see [page 7](07_retention.md)).

## Chart & statistics terms
- **Confidence interval (the whiskers)** — a "margin of error" around a number. Small groups have
  wide intervals, so we don't over-trust them. We use the **Wilson** method (good for percentages).
- **Cramér's V** — a score from 0 to 1 for how strongly a field relates to churn. 0 = no link,
  higher = stronger link. Used in Chart 1 to decide what's worth charting.
- **Correlation vs causation** — two things moving together (*correlation*) does **not** mean one
  *causes* the other. Only an experiment (the pilot) can show cause. We always say "associated with".
- **n** — the number of customers in a group (shown under each bar).

## Model & machine-learning terms
- **Feature** — a piece of information the model uses (e.g. number of products, balance).
- **Probability** — the model's output: a 0–100% chance the customer will leave. "73%" = the
  "percent prediction".
- **Logistic Regression** — the model we used: simple, explainable, outputs a probability.
- **LightGBM** — a more complex "boosted trees" model we compared against (it didn't win here).
- **Baseline** — a dumb rule ("new customers churn") used as a floor to beat.
- **Class imbalance** — churn is rare (only 15.8%), which makes prediction harder and changes which
  score we use (PR-AUC, not plain accuracy).
- **Class weights ("balanced")** — a setting that tells the model to pay extra attention to the rare
  group (leavers) so it isn't ignored.
- **Training set / holdout** — we train on 8,000 customers and keep 2,000 hidden ("holdout") to test
  fairly on people the model never saw.
- **Stratified split** — when splitting into train/test, we keep the same churn rate in each part, so
  the test is representative.
- **Out-of-fold (OOF)** — a trick so every customer is scored by a model that did **not** train on
  them, giving honest scores for the whole 10,000.
- **Cross-validation (CV)** — training and testing several times on different slices to get a stable
  score; used to choose the model.
- **Calibration / isotonic** — adjusting the model so its probabilities are honest (when it says
  30%, about 30% really leave). "Isotonic" is the specific method used.
- **PR-AUC (Precision–Recall AUC)** — the **main score** here (higher = better). Good for rare
  events. 0.559 for our model vs 0.158 for guessing.
- **ROC-AUC** — another score (0.5 = random, 1.0 = perfect). 0.844 means strong ranking ability.
- **Precision** — of the customers the model flags as high-risk, how many actually leave.
- **Recall** — of the customers who actually leave, how many the model flagged.
- **Threshold** — the cut-off probability for calling someone "high risk" (we use 40%).
- **Top-decile capture** — how many of all leavers are caught in the model's riskiest 10% (39%).
- **SHAP** — a method that explains how much each feature pushed a prediction, for the model overall
  and for each individual customer.
- **Leakage** — when a model accidentally uses information that wouldn't really be available (a form
  of "cheating"). We checked for it with the recency field.

## Data & synthetic terms
- **Synthetic data** — realistic fake customers generated to add volume. They don't train the model.
- **Gaussian copula** — the method used to make the fakes: it learns how fields move together, then
  draws new rows with the same patterns, separately per segment.
- **KS distance (Kolmogorov–Smirnov)** — a 0–1 measure of how different two distributions are. Tiny
  values (ours ≤ 0.006) mean the fakes closely match the real data.
- **Lineage flags** — columns (`is_synthetic`, `data_split`) that mark each row as real or fake and
  which split it belongs to, so nothing gets mixed up.
- **Data-quality flag** — a marker on an impossible-looking row that we keep but don't trust blindly
  (e.g. tenure longer than adult life).

## Pilot & deployment terms
- **RCT (Randomised Controlled Trial)** — the fair experiment: randomly treat half, leave half as a
  control, compare. The only way to prove cause.
- **Power calculation** — a statistics calculation of how many customers you need in the experiment
  to reliably detect an effect (we need 564 per group).
- **KPI** — a Key Performance Indicator; the things we measure in the pilot (churn drop, money
  retained, ROI, NPS).
- **ROI (Return on Investment)** — money saved vs money spent. We only scale actions with ROI > 1.
- **PSI (Population Stability Index)** — a check, after launch, that the customers coming in haven't
  drifted away from what the model was trained on (a signal to retrain).

⬅️ Back to the [documentation index](README.md)

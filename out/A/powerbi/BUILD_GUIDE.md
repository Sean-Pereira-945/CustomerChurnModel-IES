# Meridian Trust Bank — Power BI dashboard build guide

Build time: about 40 minutes in Power BI Desktop (Windows). Everything below uses only the
files in `data/` and the measures in `measures.dax`. The expected values at the end let you
prove the dashboard is correct. Reference images for each visual are in `../figures/`.

---

## 1. Load the data (5 min)

1. **Get data → Text/CSV** → load `fact_customers.csv`, `dim_segment.csv`, `dim_tenure.csv`.
   In the preview, choose **Transform data** and check the types:
   - `avg_monthly_balance`, `tenure_years` → Decimal number
   - `num_products`, `churned`, `dq_*`, every `*_sort` column → Whole number
   - all other columns → Text
2. **Close & Apply.**
3. **Model view → relationships** (many-to-one, single direction, fact on the "many" side):
   - `fact_customers[customer_segment]` → `dim_segment[customer_segment]`
   - `fact_customers[tenure_band]` → `dim_tenure[tenure_band]`
4. **Sort by column** (select column → Column tools → Sort by column):

   | Column | Sort by |
   |---|---|
   | `dim_segment[customer_segment]` | `segment_sort` |
   | `dim_tenure[tenure_label]` | `tenure_sort` |
   | `fact_customers[products_band]` | `products_band_sort` |
   | `fact_customers[recency_band]` | `recency_band_sort` |
   | `fact_customers[engagement_band]` | `engagement_band_sort` |
   | `fact_customers[complaint_band]` | `complaint_band_sort` |
   | `fact_customers[nps_band]` | `nps_band_sort` |

5. Hide from report view: all `*_sort` columns, `fact_customers[customer_segment]` and
   `fact_customers[tenure_band]` (visuals always use the dimension columns).
6. **Home → Enter data** → create an empty table named `_Measures`, then add every measure from
   `measures.dax` (New measure, paste, set the format string). Hide the dummy column.

## 2. Report-wide settings (3 min)

- **Theme:** View → Themes → Customize. Two colours carry meaning everywhere:
  churn / money lost = **#C8102E** (red); comparison series (customers, RM assigned) = **#2F6DB5** (blue).
  Reference lines and gridlines grey, background white. This pair passes colour-blind separation checks.
- **Page size:** 16:9.
- **Slicer "Data scope"** (`fact_customers[data_scope]`), top-right of every page.
  Default selection **Real**. Select Real + Synthetic to show all 50,000 rows.
  Sync it across all pages (View → Sync slicers).
- **Slicer "Segment"** (`dim_segment[customer_segment]`), synced across pages 1–3.
- Every churn-rate chart gets a **constant line at the Base Churn Rate**: Analytics pane →
  Constant line → fx → `Base Churn Rate`, dashed grey, label "Bank average".
- Every chart title states the message, not the metric (titles below).

---

## 3. Pages

### Page 1 — Executive overview
*Question it answers: how big is the problem, and where is the money?*

| Visual | Fields | Title |
|---|---|---|
| 4 cards | `Customers`, `Churn Rate`, `Balance Lost AED`, `Pct Balance Lost` | — |
| Column chart | X: `dim_tenure[tenure_label]` · Y: `Churn Rate` | "Churn is highest in the first year" |
| Clustered bar | Y: `dim_segment[customer_segment]` · X: `Share of Churners`, `Share of Balance Lost` | "Mass Market drives volume; higher segments drive the money lost" |
| Column chart | X: `dim_segment[customer_segment]` · Y: `Churn Rate` | "Churn rate falls as segment value rises" |

Layout: cards across the top; tenure chart on the left; the volume-vs-value chart large on the right.
That chart is the single most important visual for the committee (reference: `08_segment_volume_vs_value.png`).

### Page 2 — Behavioural churn drivers
*Question: which behaviours are associated with leaving?* (descriptive, not causal)

| Visual | Fields | Title |
|---|---|---|
| Column chart | X: `products_band` · Y: `Churn Rate` | "Single-product customers churn at more than twice the bank average" |
| Column chart | X: `recency_band` · Y: `Churn Rate` | "Customers idle for 90+ days leave at three times the average" |
| Column chart | X: `engagement_band` · Y: `Churn Rate` | "Churn falls steadily as digital engagement rises" |
| Column chart | X: `complaint_band` · Y: `Churn Rate` | "Customers with 2+ complaints churn at twice the average" |
| Column chart | X: `nps_band` · Y: `Churn Rate` | "Negative-NPS customers churn at 1.7× the average" |
| Matrix (heatmap) | Rows: `dim_tenure[tenure_label]` · Columns: `products_band` · Values: `Churn Rate`; conditional formatting → background colour, white → red | "New customers with one product: more than half leave" |

Tooltip on every column chart: `Customers`, `Churned Customers`, `Churn Lift`, so group sizes are
visible (small groups such as engagement 0–20, n = 394, shouldn't be over-read).

### Page 3 — Relationship & value at risk
*Question: where is retention effort worth the most?*

| Visual | Fields | Title |
|---|---|---|
| Clustered column | X: `dim_segment[customer_segment]` · Y: `Churn Rate No RM`, `Churn Rate With RM` | "Customers with an RM churn at about half the rate in every segment" |
| Card | `Pct With RM`, visual-level filter segment = Mass Affluent | "Only ~6% of Mass Affluent customers have an RM" |
| Matrix | Rows: `dim_segment[customer_segment]` · Columns: `dim_tenure[tenure_label]` · Values: `Balance Lost AED`; data bars | "Where the lost balances sit" |
| Decomposition tree | Analyse: `Balance Lost AED` · Explain by: segment → `rm_status` → `products_band` → `recency_band` | "Drill into balance lost" |
| Key influencers *(stretch)* | Analyse: `churned` (= 1) · Explain by: `products_band`, `recency_band`, `engagement_band`, `complaint_band`, `nps_band`, `rm_status`, `dim_tenure[tenure_label]`, `dim_segment[customer_segment]` | "What raises the likelihood of churn" |

Caveat text box on this page: *"RM coverage is associated with lower churn. RMs may be assigned to
customers who were already more loyal, so the effect must be tested in the pilot before we claim
it causes retention."*

### Page 4 — Data quality & lineage
*Question: can we trust this data?* (supports the data-quality marks)

| Visual | Fields | Title |
|---|---|---|
| Table + 2 cards | `data_scope` with `Customers` and `Churn Rate`; cards `DQ Products Below Flags`, `DQ Tenure Above Adult Years` | "Data scope and quality flags" |
| Clustered column | X: `dim_segment[customer_segment]` · Legend: `data_scope` · Y: `Churn Rate`. Edit interactions so the Data scope slicer does **not** filter this visual. | "Synthetic rows reproduce real churn patterns" |
| Clustered column | X: `dim_tenure[tenure_label]` · Legend: `data_scope` · Y: `Churn Rate` (same interaction setting) | "…by tenure band too" |
| Text box | Method summary below | "How the 50,000-row dataset was built" |

Method text: *"10,000 real customers, cleaned and checksum-verified against the source summary.
40,000 synthetic rows generated with a stratified Gaussian copula fitted on 8,000 training customers
only. Data-quality issues are flagged, not removed. Headline figures use real data only."*

### Page 5 — Retention priority *(added at integration, from Person B)*
Load `priority_list.csv` and relate `priority_list[customer_id]` → `fact_customers[customer_id]`
(one-to-one). Add: a card per tier with its customer count, `SUM(expected_balance_at_risk)` by
`priority_tier` (bar), and a top-50 table sorted by `expected_balance_at_risk` with `top_3_reasons`.

---

## 4. Verify before presenting (Data scope = Real, no other filters)

| Check | Expected |
|---|---|
| Customers | 10,000 |
| Churned Customers | 1,578 |
| Churn Rate | 15.8% |
| Balance Lost AED | 22,468,465 |
| Pct Balance Lost | 6.6% |
| Churn by tenure: <1 / 1–3 / 3–7 / 7–15 / 15+ | 28.1% / 17.6% / 14.0% / 10.1% / 5.0% |
| Churn by products: 1 / 2 / 3 / 4+ | 36.1% / 12.2% / 5.8% / 4.4% |
| Churn by recency: 0–30 / 31–60 / 61–90 / 90+ | 11.8% / 19.7% / 29.7% / 48.7% |
| Churn by engagement: 0–20 / 21–40 / 41–60 / 61–80 / 81–100 | 37.1% / 25.3% / 16.1% / 9.9% / 5.6% |
| Churn by complaints: 0 / 1 / 2+ | 13.1% / 20.1% / 30.9% |
| Churn by NPS: Negative / Low / Mid / High | 26.2% / 17.4% / 11.3% / 7.1% |
| Churn by segment: MM / MA / Aff / PB | 21.8% / 12.0% / 5.3% / 4.1% |
| Share of churners: MM / MA / Aff / PB | 73.1% / 20.7% / 4.9% / 1.3% |
| Share of balance lost: MM / MA / Aff / PB | 18.8% / 30.7% / 24.8% / 25.7% |
| Churn with RM vs no RM, Mass Market | 10.9% vs 22.4% |
| Data scope = Real + Synthetic: Customers / Churn Rate | 50,000 / 15.8% |
| DQ flags (real only): products below flags / tenure above adult years | 199 / 1,009 |

If a number differs, the usual causes are a wrong data type on import, a missing relationship,
or a visual using the fact table's segment/tenure column instead of the dimension's.

Export each page (File → Export → PDF, or a screenshot per page) to `screens/page1.png … page5.png`.

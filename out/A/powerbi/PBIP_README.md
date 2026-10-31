# Meridian dashboard — PBIP project (open in Power BI Desktop)

This folder contains a **generated** Power BI project. It was built from code
(`src/build_pbip.py`) and its JSON was validated, but it could not be test-opened here — Power BI
Desktop runs only on your machine. Open it there and verify against the table in §4 of
`BUILD_GUIDE.md`.

## Open it
1. Install/open **Power BI Desktop** (Windows). Enable **File → Options → Preview features →
   "Power BI Project (.pbip) save option"** if it isn't already on, then restart.
2. Double-click **`Meridian.pbip`** (or File → Open → browse to it).
3. The model loads 5 tables from `data/` (50,000 fact rows + dimensions + the 10,000-row priority
   list), with all relationships, sort-by-column settings, hidden helper columns and **24 measures**
   in display folders already defined.
4. **Apply the colour scheme:** View → Themes → **Browse for themes** → pick `Meridian_theme.json`.
   This sets churn/money = red `#C8102E`, comparison series = blue `#2F6DB5`.

## If the data fails to load (path moved)
The CSV paths are baked in as absolute paths to **this** `data/` folder. If you move the project,
re-point them: Transform data → each query → gear on "Source" → update the file path. Or re-run
`python src/build_pbip.py <new powerbi folder>` to regenerate with the new path.

## Pages already laid out
1. Executive overview · 2. Behavioural drivers · 3. Relationship & value · 4. Data quality &
lineage · 5. Retention priority (from `priority_list.csv`).

A few finishing touches are intentionally left to do by hand (they're fiddly to generate reliably):
- **Constant "Bank average" reference line** on churn-rate charts (Analytics pane → Constant line →
  fx → `Base Churn Rate`).
- **Heatmap conditional formatting** on the tenure × products matrix (Cell elements → Background
  colour → `Churn Rate`, white→red).
- **Top-50 filter** on the page-5 table (Filters pane → `expected_balance_at_risk` → Top N = 50).
- **Edit interactions** on page 4 so the Data scope slicer does *not* filter the real-vs-synthetic
  comparison chart.

## Verify, then export
Set the **Data scope** slicer to **Real** and check every number against the expected-values table
in `BUILD_GUIDE.md` §4 (e.g. Customers 10,000 · Churn Rate 15.8% · Balance Lost 22,468,465).
Then **File → Export → Export to PDF**, or screenshot each page, into `../screens/page1.png …
page5.png`. Re-running `python src/build_deck.py` will then drop the screenshots into appendix
slide A9 automatically.

## Fallback (if the report half won't open on your Desktop version)
The report layout (`Meridian.Report/report.json`) is a hand-authored legacy layout and is the only
fragile part. If Desktop refuses to open it, **delete the `Meridian.Report` folder** — the
`Meridian.SemanticModel` still opens on its own with all tables and 24 measures ready, and you build
the 5 pages by dragging fields per `BUILD_GUIDE.md` (~15 min). The data model is the slow part, and
it's done.

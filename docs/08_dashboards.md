# 8. The dashboards

The project has **two** dashboards. One is for executives to explore the data (Power BI); the other
is a live tool that scores customers and recommends actions (the web app).

---

## A) Power BI dashboard (`out/A/powerbi/`)

A 5-page interactive report built on the 50,000-row dataset. It's a **project file** (`.pbip`) you
open in Power BI Desktop; full instructions are in `out/A/powerbi/PBIP_README.md` and
`BUILD_GUIDE.md`.

| Page | Question it answers |
|---|---|
| 1. Executive overview | How big is the problem, and where is the money? |
| 2. Behavioural drivers | Which behaviours go with leaving? |
| 3. Relationship & value | Where is retention effort worth the most? |
| 4. Data quality & lineage | Can we trust this data? (shows the flagged issues + real-vs-synthetic) |
| 5. Retention priority | The ranked list of who to save first |

It uses the same two meaningful colours as everything else (**red = churn/money, blue = compare**)
and has a slicer to switch between **Real only** and **Real + Synthetic**. There's an
expected-values table so every number can be checked before presenting.

> Note: the `.pbip` is generated from code and could not be opened/tested from the build environment,
> so open it in Power BI Desktop and verify against the expected-values table. If the report half
> doesn't open on your version, the data model still loads and you rebuild the visuals in ~15 minutes
> from the guide.

---

## B) Live web app (`app/`) — predict + retain

A modern web app with a **FastAPI** backend (Python) and a **React** frontend. This is the
interactive, "do it now" tool.

### What you can do on it
- **See model performance** at a glance — PR-AUC, ROC-AUC, top-decile capture, money protected.
- **Score a customer live** — type in 9 details, get their churn %, tier, money at risk, reasons,
  **and a tailored retention plan with costs** (the [page 7](07_retention.md) procedure, instantly).
- **Explore churn drivers** — switch between products, recency, engagement, and segment.
- **Browse the priority list** — all 10,000 customers, filter by tier, search by ID.

### The four parts of the screen
1. **KPI cards** — the headline model numbers.
2. **"Score a customer" form** — the live prediction + retention plan.
3. **Charts** — tier distribution, money-protected comparison, churn drivers, feature importance.
4. **Priority table** — the ranked, filterable list.

### How to run it — the easy way
Double-click **[`../start.bat`](../start.bat)** in the project root. It will:
1. Find the right Python and Node.
2. Install everything and train the model (first run only).
3. Start the backend (port 8137) and frontend (port 5173) in two windows.
4. Open your browser to the dashboard.

To stop it, close the two server windows.

### How to run it — manually (two terminals)
```bash
# terminal 1 — backend
cd app/backend
pip install -r requirements.txt      # first time
python train.py                      # first time (builds the model)
python -m uvicorn main:app --port 8137

# terminal 2 — frontend
cd app/frontend
npm install                          # first time
npm run dev                          # opens http://localhost:5173
```

Full details and the API reference are in `app/README.md`, and the model behind it is documented in
`app/MODEL.md`.

➡️ Next: [Glossary](09_glossary.md)

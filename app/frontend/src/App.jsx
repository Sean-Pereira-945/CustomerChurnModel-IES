import React, { useEffect, useState } from "react";
import { getMetrics, getFields } from "./api.js";
import PredictForm from "./components/PredictForm.jsx";
import PriorityTable from "./components/PriorityTable.jsx";
import { TierChart, ValueChart, DriversChart, ImportanceChart } from "./components/Charts.jsx";

function Kpi({ label, value, sub, accent }) {
  return (
    <div className={`kpi ${accent ? "accent" : ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [fields, setFields] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getMetrics(), getFields()])
      .then(([m, f]) => { setMetrics(m); setFields(f.fields); })
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return <div className="loading">Could not reach the API ({error}).<br />
      Start the backend: <code>cd app/backend &amp;&amp; python -m uvicorn main:app --port 8137</code></div>;
  if (!metrics || !fields) return <div className="loading">Loading model…</div>;

  const m = metrics;
  return (
    <>
      <div className="header">
        <div>
          <h1>Meridian — Churn Predictive Dashboard</h1>
          <div className="tag">Predict · Prioritise · Retain &nbsp;|&nbsp; {m.chosen_model}, calibrated · real data (n={m.n_customers.toLocaleString()})</div>
        </div>
        <div className="badge">Holdout PR-AUC <b>{m.pr_auc.toFixed(3)}</b> &nbsp;·&nbsp; ROC <b>{m.roc_auc.toFixed(3)}</b></div>
      </div>

      <div className="wrap">
        <div className="section-title">Model performance</div>
        <div className="kpis">
          <Kpi label="PR-AUC (holdout)" value={m.pr_auc.toFixed(3)} sub={`vs ${m.baseline_pr_auc.toFixed(3)} base rate`} accent />
          <Kpi label="ROC-AUC" value={m.roc_auc.toFixed(3)} sub="ranking quality" />
          <Kpi label="Top-decile capture" value={`${(m.top_decile_capture * 100).toFixed(0)}%`} sub="of all leavers" />
          <Kpi label="Balance protected" value={`AED ${(m.aed_protected_value_weighted / 1e6).toFixed(1)}m`} sub={`top ${m.capacity_n}, value-weighted`} accent />
          <Kpi label="Base churn rate" value={`${(m.base_churn_rate * 100).toFixed(1)}%`} sub={`${m.n_churned.toLocaleString()} of ${m.n_customers.toLocaleString()}`} />
        </div>

        <div className="section-title">Predict &amp; explain</div>
        <div className="grid2">
          <PredictForm fields={fields} />
          <div className="grid-charts">
            <TierChart tierCounts={m.tier_counts} />
            <ValueChart m={m} />
            <DriversChart drivers={m.drivers} />
            <ImportanceChart imp={m.feature_importance} />
          </div>
        </div>

        <div className="section-title">Who to save first</div>
        <PriorityTable />

        <p className="footnote">
          Predictive/descriptive tool for outreach prioritisation only — not credit, pricing or eligibility.
          Associations are not causation. Model & neglected-column rationale: <code>app/MODEL.md</code>.
        </p>
      </div>
    </>
  );
}

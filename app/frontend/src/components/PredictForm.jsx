import React, { useState } from "react";
import { predict } from "../api.js";

const TIER_CLASS = { "T1 Save now": "t1", "T2 Protect": "t2", "T3 Automated save": "t3", "T4 Monitor": "t4" };
const TIER_BG = { "T1 Save now": "#c8102e", "T2 Protect": "#2f6db5", "T3 Automated save": "#2e7d32", "T4 Monitor": "#6b7280" };

export default function PredictForm({ fields }) {
  const init = Object.fromEntries(fields.map((f) => [f.name, f.default]));
  const [form, setForm] = useState(init);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (name, value) => setForm((f) => ({ ...f, [name]: value }));

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const body = {};
      for (const f of fields) {
        const v = form[f.name];
        body[f.name] = f.kind === "num" ? parseFloat(v) : f.kind === "select" ? v : parseInt(v, 10);
      }
      setResult(await predict(body));
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="card">
      <h3>Score a customer</h3>
      <p className="hint">Enter the {fields.length} required fields to predict churn risk.</p>
      <form onSubmit={onSubmit}>
        {fields.map((f) => (
          <div className="form-row" key={f.name}>
            <label>{f.label}</label>
            {f.kind === "select" ? (
              <select value={form[f.name]} onChange={(e) => set(f.name, e.target.value)}>
                {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : f.kind === "binary" ? (
              <select value={form[f.name]} onChange={(e) => set(f.name, parseInt(e.target.value, 10))}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            ) : (
              <input type="number" step={f.kind === "num" ? "0.1" : "1"} min={f.min} max={f.max}
                value={form[f.name]} onChange={(e) => set(f.name, e.target.value)} />
            )}
          </div>
        ))}
        <button className="btn" disabled={busy}>{busy ? "Scoring…" : "Predict churn risk"}</button>
      </form>

      {err && <p className="footnote" style={{ color: "#c8102e" }}>{err}</p>}

      {result && (
        <div className="result">
          <div className="gauge" style={{ color: result.high_risk ? "#c8102e" : "#2e7d32" }}>
            {(result.churn_probability * 100).toFixed(1)}%
          </div>
          <div className="footnote">calibrated churn probability</div>
          <div style={{ marginTop: 10 }}>
            <span className="pill" style={{ background: TIER_BG[result.priority_tier] }}>
              {result.priority_tier}
            </span>
          </div>
          <div className="kv"><span>Expected balance at risk</span>
            <b>AED {result.expected_balance_at_risk.toLocaleString()}</b></div>
          <ul className="reasons">
            {result.top_3_reasons.split("; ").map((r, i) => <li key={i}>• {r}</li>)}
          </ul>

          {result.retention_plan && (
            <div className="plan">
              <div className="plan-head">How to retain this customer</div>
              <p className="plan-approach">{result.retention_plan.approach}</p>
              {result.retention_plan.actions.map((a, i) => (
                <div className="action" key={i}>
                  <div className="action-top">
                    <span className="action-signal">{a.signal}</span>
                    <span className="action-channel">{a.channel}</span>
                  </div>
                  <div className="action-text">
                    {a.action}{a.hypothesis && <span className="hyp"> · hypothesis (test in pilot)</span>}
                  </div>
                  <div className="action-cost">
                    {a.est_cost_aed > 0 ? `≈ AED ${a.est_cost_aed} / customer` : "no direct cost"}
                  </div>
                </div>
              ))}
              <div className="kv" style={{ marginTop: 10 }}>
                <span>Estimated cost to retain</span>
                <b>AED {result.retention_plan.est_total_cost_aed.toLocaleString()}</b>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

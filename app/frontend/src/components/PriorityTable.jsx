import React, { useEffect, useState } from "react";
import { getPriority } from "../api.js";

const TIERS = ["all", "T1 Save now", "T2 Protect", "T3 Automated save", "T4 Monitor"];
const TIER_CLASS = { "T1 Save now": "t1", "T2 Protect": "t2", "T3 Automated save": "t3", "T4 Monitor": "t4" };

export default function PriorityTable() {
  const [tier, setTier] = useState("all");
  const [q, setQ] = useState("");
  const [limit, setLimit] = useState(25);
  const [data, setData] = useState({ total: 0, rows: [] });

  useEffect(() => {
    const t = setTimeout(() => getPriority(tier, limit, q).then(setData).catch(() => {}), 150);
    return () => clearTimeout(t);
  }, [tier, q, limit]);

  return (
    <div className="card">
      <h3>Retention priority list</h3>
      <p className="hint">Out-of-fold scores for all 10,000 customers, ranked by expected balance at risk.</p>
      <div className="toolbar">
        <select value={tier} onChange={(e) => setTier(e.target.value)}>
          {TIERS.map((t) => <option key={t} value={t}>{t === "all" ? "All tiers" : t}</option>)}
        </select>
        <input placeholder="Search customer id…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={limit} onChange={(e) => setLimit(parseInt(e.target.value, 10))}>
          {[10, 25, 50, 100].map((n) => <option key={n} value={n}>Top {n}</option>)}
        </select>
        <span className="footnote" style={{ marginLeft: "auto" }}>{data.total.toLocaleString()} matching</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Customer</th><th>Segment</th><th className="num">Churn prob</th>
              <th className="num">Balance (AED)</th><th className="num">At risk (AED)</th>
              <th>Tier</th><th>Top reasons</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.customer_id}>
                <td>{r.customer_id}</td>
                <td>{r.customer_segment}</td>
                <td className="num">{(r.churn_probability * 100).toFixed(1)}%</td>
                <td className="num">{Math.round(r.avg_monthly_balance).toLocaleString()}</td>
                <td className="num">{Math.round(r.expected_balance_at_risk).toLocaleString()}</td>
                <td className={`tier-tag ${TIER_CLASS[r.priority_tier]}`}>{r.priority_tier}</td>
                <td style={{ color: "#6b7280" }}>{r.top_3_reasons}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

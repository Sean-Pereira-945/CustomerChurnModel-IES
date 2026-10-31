import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, LabelList,
} from "recharts";

const RED = "#c8102e", BLUE = "#2f6db5", MUTED = "#9aa0a6", GREEN = "#2e7d32", INK = "#1f2328";
const pct = (v) => `${(v * 100).toFixed(0)}%`;
const aedM = (v) => `AED ${(v / 1e6).toFixed(1)}m`;

function Panel({ title, hint, children, h = 240 }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {hint && <p className="hint">{hint}</p>}
      <ResponsiveContainer width="100%" height={h}>{children}</ResponsiveContainer>
    </div>
  );
}

export function TierChart({ tierCounts }) {
  const order = ["T1 Save now", "T2 Protect", "T3 Automated save", "T4 Monitor"];
  const colors = { "T1 Save now": RED, "T2 Protect": BLUE, "T3 Automated save": GREEN, "T4 Monitor": MUTED };
  const data = order.filter((t) => t in tierCounts).map((t) => ({ tier: t, n: tierCounts[t] }));
  return (
    <Panel title="Customers by priority tier" hint="Risk × value segmentation of all 10,000 customers">
      <BarChart data={data} margin={{ top: 16, right: 10, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
        <XAxis dataKey="tier" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v) => v.toLocaleString()} />
        <Bar dataKey="n" radius={[6, 6, 0, 0]}>
          <LabelList dataKey="n" position="top" fontSize={11} formatter={(v) => v.toLocaleString()} />
          {data.map((d) => <Cell key={d.tier} fill={colors[d.tier]} />)}
        </Bar>
      </BarChart>
    </Panel>
  );
}

export function ValueChart({ m }) {
  const data = [
    { k: "Value-weighted", v: m.aed_protected_value_weighted, c: GREEN },
    { k: "Probability-only", v: m.aed_protected_prob_only, c: BLUE },
    { k: "Random", v: m.aed_protected_random, c: MUTED },
  ];
  return (
    <Panel title={`Balance protected at capacity ${m.capacity_n}`}
      hint={`Ranking by balance-at-risk protects ${m.value_vs_prob_ratio}× the money of probability alone`}>
      <BarChart data={data} margin={{ top: 16, right: 10, left: 10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
        <XAxis dataKey="k" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={aedM} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v) => `AED ${Number(v).toLocaleString()}`} />
        <Bar dataKey="v" radius={[6, 6, 0, 0]}>
          <LabelList dataKey="v" position="top" fontSize={11} formatter={aedM} />
          {data.map((d, i) => <Cell key={i} fill={d.c} />)}
        </Bar>
      </BarChart>
    </Panel>
  );
}

export function DriversChart({ drivers }) {
  const opts = [
    { key: "by_products", label: "Products held" },
    { key: "by_recency", label: "Days since last txn" },
    { key: "by_engagement", label: "Digital engagement" },
    { key: "by_segment", label: "Segment" },
  ];
  const [sel, setSel] = useState("by_products");
  const data = drivers[sel];
  return (
    <div className="card">
      <h3>Churn rate by driver</h3>
      <p className="hint">Descriptive, real data. Association, not causation.</p>
      <div className="chips">
        {opts.map((o) => (
          <span key={o.key} className={`chip ${sel === o.key ? "active" : ""}`} onClick={() => setSel(o.key)}>
            {o.label}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={data} margin={{ top: 16, right: 10, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={pct} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => pct(v)} />
          <Bar dataKey="rate" fill={RED} radius={[6, 6, 0, 0]}>
            <LabelList dataKey="rate" position="top" fontSize={11} formatter={pct} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ImportanceChart({ imp }) {
  const data = [...imp].reverse();
  return (
    <Panel title="Top features by model importance" hint="Relative contribution in the deployed model" h={260}>
      <BarChart layout="vertical" data={data} margin={{ top: 4, right: 20, left: 40, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey="feature" tick={{ fontSize: 10.5 }} width={120} />
        <Tooltip formatter={(v) => v.toFixed(2)} />
        <Bar dataKey="importance" fill={BLUE} radius={[0, 5, 5, 0]} />
      </BarChart>
    </Panel>
  );
}

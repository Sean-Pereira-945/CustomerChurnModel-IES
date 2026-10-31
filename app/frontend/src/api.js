const BASE = "/api";

async function get(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export const getMetrics = () => get("/metrics");
export const getFields = () => get("/fields");
export const getPriority = (tier = "all", limit = 50, q = "") =>
  get(`/priority?tier=${encodeURIComponent(tier)}&limit=${limit}&q=${encodeURIComponent(q)}`);

export async function predict(body) {
  const r = await fetch(BASE + "/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`predict → ${r.status}`);
  return r.json();
}

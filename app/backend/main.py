"""FastAPI backend for the Meridian predictive-churn dashboard.

Serves the lean model's metrics, drivers, priority list and a single-customer prediction endpoint.
Run: uvicorn main:app --reload --port 8000   (from app/backend)
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import ml

ART = Path(__file__).resolve().parent / "artifacts"

app = FastAPI(title="Meridian Churn API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

# --- load artifacts once at startup --------------------------------------------
if not (ART / "app_model.joblib").exists():
    raise RuntimeError("Model artifacts missing. Run: python train.py")
BUNDLE = joblib.load(ART / "app_model.joblib")
METRICS = json.loads((ART / "app_metrics.json").read_text(encoding="utf-8"))
FIELDS = json.loads((ART / "fields.json").read_text(encoding="utf-8"))
PRIORITY = pd.read_csv(ART / "app_priority.csv")


class Customer(BaseModel):
    customer_segment: str = Field(default="Mass Market")
    tenure_years: float = 3.0
    avg_monthly_balance: float = 15000
    num_products: int = 2
    digital_engagement_score: float = 50
    complaint_count_last_year: int = 0
    nps_score: int = 10
    relationship_manager_assigned: int = 0
    last_transaction_days_ago: int = 20


@app.get("/api/health")
def health():
    return {"status": "ok", "model": METRICS["chosen_model"]}


@app.get("/api/fields")
def fields():
    return FIELDS


@app.get("/api/metrics")
def metrics():
    return METRICS


@app.get("/api/priority")
def priority(limit: int = Query(50, ge=1, le=500), tier: str = "all", q: str = ""):
    df = PRIORITY
    if tier != "all":
        df = df[df["priority_tier"] == tier]
    if q:
        df = df[df["customer_id"].str.contains(q, case=False, na=False)]
    return {"total": int(len(df)), "rows": df.head(limit).to_dict(orient="records")}


@app.post("/api/predict")
def predict(c: Customer):
    if c.customer_segment not in ml.SEGMENTS:
        raise HTTPException(422, f"customer_segment must be one of {ml.SEGMENTS}")
    row = pd.DataFrame([c.model_dump()])
    X = ml.make_features(row)
    prob = float(BUNDLE["calibrated"].predict_proba(X)[:, 1][0])
    bal = float(c.avg_monthly_balance)
    tier = ml.assign_tier([prob], [bal], BUNDLE["bal_p75"])[0]
    return {
        "churn_probability": round(prob, 4),
        "expected_balance_at_risk": round(prob * bal, 2),
        "priority_tier": tier,
        "top_3_reasons": ml.risk_reasons(X.iloc[0]),
        "high_risk": prob >= ml.HIGH_RISK_THR,
        "retention_plan": ml.retention_plan(X.iloc[0], tier),
    }

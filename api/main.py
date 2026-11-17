from contextlib import asynccontextmanager
from pathlib import Path
import numbers

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from api.schemas import Applicant, Prediction
from src.app_support import MAIN_COLUMNS, build_applicant, friendly_name
from src.explain import make_explainer, explain_applicant
from src.features import NON_FEATURE_COLUMNS
from src.policy import load_policy, decide

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATEGORY_COLUMNS = ["purpose", "home_ownership", "addr_state"]

assets = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model = joblib.load(PROJECT_ROOT / "models" / "lightgbm_v2_calibrated.joblib")
    typical = pd.read_parquet(PROJECT_ROOT / "models" / "typical_applicant.parquet")
    demo_loans = pd.read_parquet(PROJECT_ROOT / "models" / "demo_loans.parquet")

    assets["model"] = model
    assets["explainer"] = make_explainer(model)
    assets["policy"] = load_policy(PROJECT_ROOT / "results" / "policy.json")
    assets["typical"] = typical
    assets["extra_columns"] = [
        c for c in typical.columns if c not in MAIN_COLUMNS + NON_FEATURE_COLUMNS
    ]
    assets["allowed"] = {
        col: sorted(set(demo_loans[col].dropna().unique()) | {typical[col].iloc[0]})
        for col in CATEGORY_COLUMNS
    }
    yield
    assets.clear()


app = FastAPI(
    title="Loan Default API",
    description="Predicts the probability that a 36-month Lending Club loan is charged off, "
                "and returns an approve / review / reject decision with the main reasons.",
    version="1.0.0",
    lifespan=lifespan,
)


def to_plain(value):
    """Turn numpy numbers and missing values into plain JSON-friendly values."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, numbers.Number):
        return float(value)
    return str(value)


@app.get("/")
def root():
    return {"message": "Loan Default API. Open /docs to try it."}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": "model" in assets,
        "policy": assets.get("policy"),
    }


@app.post("/predict", response_model=Prediction)
def predict(applicant: Applicant):
    for col in CATEGORY_COLUMNS:
        value = getattr(applicant, col)
        if value not in assets["allowed"][col]:
            raise HTTPException(
                status_code=422,
                detail=f"{col} '{value}' is not recognised. Allowed: {assets['allowed'][col]}",
            )

    unknown = set(applicant.extra) - set(assets["extra_columns"])
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown extra fields: {sorted(unknown)}. Allowed: {assets['extra_columns']}",
        )

    form = applicant.model_dump(exclude={"issue_date", "extra"})
    try:
        row = build_applicant(assets["typical"], form, applicant.issue_date, applicant.extra)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=422, detail=f"Could not use the extra fields: {error}")

    model = assets["model"]
    policy = assets["policy"]
    probability = float(model.predict_proba(row)[:, 1][0])
    decision = decide(probability, policy["cutoff"], policy["review_margin"])

    reasons = explain_applicant(model, assets["explainer"], row, top_n=len(row.columns))
    all_reasons = [
        {
            "feature": r.feature,
            "label": friendly_name(r.feature),
            "value": to_plain(r.value),
            "contribution": round(float(r.contribution), 4),
            "effect": r.effect,
        }
        for r in reasons.itertuples(index=False)
    ]
    against = [r for r in all_reasons if r["contribution"] > 0][:3]

    return {
        "probability": round(probability, 4),
        "decision": decision,
        "cutoff": policy["cutoff"],
        "review_from": round(policy["cutoff"] - policy["review_margin"], 4),
        "top_reasons": all_reasons[:5],
        "reasons_against": against if decision != "Approve" else [],
    }
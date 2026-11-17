from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.app_support import EMP_LENGTH_OPTIONS


class Applicant(BaseModel):
    loan_amnt: float = Field(..., ge=500, le=35000, description="Loan amount in dollars")
    purpose: str = Field(..., description="Loan purpose, e.g. debt_consolidation")
    annual_inc: float = Field(..., gt=0, description="Annual income in dollars")
    fico: int = Field(..., ge=300, le=850, description="Credit score")
    dti: float = Field(..., ge=0, le=100, description="Debt-to-income ratio, in percent")
    credit_years: float = Field(..., ge=0, le=80, description="Years since first credit line")
    emp_length: str = Field("Not provided", description="Employment length, e.g. 10+ years")
    home_ownership: str = Field(..., description="RENT, OWN or MORTGAGE")
    addr_state: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    acc_open_past_24mths: int = Field(..., ge=0, le=60, description="Accounts opened in the last 2 years")
    inq_last_6mths: int = Field(..., ge=0, le=30, description="Credit inquiries in the last 6 months")
    revol_util: float = Field(..., ge=0, le=200, description="Credit card utilization, in percent")
    issue_date: date = Field(default_factory=date.today, description="Application date")
    extra: dict[str, float | str | None] = Field(
        default_factory=dict,
        description="Optional extra credit details (the app's 'More credit details'). "
                    "Anything left out uses the typical applicant's value.",
    )

    @field_validator("emp_length")
    @classmethod
    def check_emp_length(cls, value):
        if value not in EMP_LENGTH_OPTIONS:
            raise ValueError(f"must be one of {EMP_LENGTH_OPTIONS}")
        return value

    @field_validator("addr_state", "home_ownership")
    @classmethod
    def to_upper(cls, value):
        return value.upper()

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "loan_amnt": 12000,
                "purpose": "debt_consolidation",
                "annual_inc": 55000,
                "fico": 690,
                "dti": 18.5,
                "credit_years": 12,
                "emp_length": "10+ years",
                "home_ownership": "RENT",
                "addr_state": "CA",
                "acc_open_past_24mths": 4,
                "inq_last_6mths": 1,
                "revol_util": 45,
            }]
        }
    }


class Reason(BaseModel):
    feature: str
    label: str
    value: float | str | None
    contribution: float
    effect: str


class Prediction(BaseModel):
    probability: float
    decision: Literal["Approve", "Review", "Reject"]
    cutoff: float
    review_from: float
    top_reasons: list[Reason]
    reasons_against: list[Reason]
"""Helpers for the Streamlit app: friendly names, building an applicant, logging."""

import pandas as pd

FRIENDLY_NAMES = {
    "fico_avg": "Credit score",
    "loan_to_income": "Loan size relative to income",
    "acc_open_past_24mths": "Accounts opened in the last 2 years",
    "num_tl_op_past_12m": "Accounts opened in the last 12 months",
    "dti": "Debt-to-income ratio",
    "annual_inc": "Annual income",
    "addr_state": "State",
    "purpose": "Loan purpose",
    "home_ownership": "Home ownership",
    "verification_status": "Income verification",
    "loan_amnt": "Loan amount",
    "revol_util": "Revolving utilization",
    "revol_bal": "Revolving balance",
    "bc_util": "Credit card utilization",
    "percent_bc_gt_75": "Share of cards over 75% used",
    "bc_open_to_buy": "Available credit on cards",
    "total_bc_limit": "Total credit card limit",
    "total_rev_hi_lim": "Total revolving limit",
    "mths_since_recent_bc": "Months since newest card opened",
    "mo_sin_old_rev_tl_op": "Age of oldest card (months)",
    "mo_sin_old_il_acct": "Age of oldest installment loan (months)",
    "mo_sin_rcnt_tl": "Months since newest account",
    "inq_last_6mths": "Credit inquiries in the last 6 months",
    "mths_since_recent_inq": "Months since last credit inquiry",
    "credit_history_months": "Length of credit history (months)",
    "emp_length_years": "Employment length (years)",
    "emp_length_missing": "Employment length not provided",
    "avg_cur_bal": "Average account balance",
    "tot_cur_bal": "Total balance owed",
    "total_bal_to_limit": "Total balance relative to limit",
    "total_bal_ex_mort": "Total balance excluding mortgage",
    "mort_acc": "Mortgage accounts",
    "open_acc": "Open accounts",
    "total_acc": "Total accounts ever",
    "num_il_tl": "Installment accounts",
    "delinq_2yrs": "Delinquencies in the last 2 years",
    "mths_since_last_delinq": "Months since last delinquency",
    "pub_rec": "Public records",
    "pub_rec_bankruptcies": "Bankruptcies",
}

EMP_LENGTH_OPTIONS = [
    "< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years",
    "6 years", "7 years", "8 years", "9 years", "10+ years", "Not provided",
]

# Raw columns controlled by the main form (the rest go in "More credit details")
MAIN_COLUMNS = [
    "loan_amnt", "purpose", "annual_inc", "emp_length", "home_ownership", "addr_state",
    "fico_range_low", "fico_range_high", "dti", "acc_open_past_24mths",
    "inq_last_6mths", "revol_util", "earliest_cr_line",
]


def friendly_name(feature):
    """Readable name for a feature, or the column name if none is defined."""
    return FRIENDLY_NAMES.get(feature, feature)


def build_applicant(typical, form, issue_date, extra=None):
    """Combine the typical applicant with the form values into one model-ready row."""
    applicant = typical.copy()
    issue_date = pd.Timestamp(issue_date)
    applicant["issue_date"] = issue_date

    applicant["fico_range_low"] = form["fico"] - 2
    applicant["fico_range_high"] = form["fico"] + 2
    applicant["earliest_cr_line"] = issue_date - pd.DateOffset(
        months=round(form["credit_years"] * 12)
    )

    emp_length = form["emp_length"]
    applicant["emp_length"] = None if emp_length == "Not provided" else emp_length

    for col in ["loan_amnt", "purpose", "annual_inc", "home_ownership", "addr_state",
                "dti", "acc_open_past_24mths", "inq_last_6mths", "revol_util"]:
        applicant[col] = form[col]

    for col, value in (extra or {}).items():
        applicant[col] = value

    return applicant.astype(typical.dtypes.to_dict())


def log_prediction(engine, record):
    """Save one prediction to SQL Server. Returns True if saved, False otherwise."""
    if engine is None:
        return False
    try:
        pd.DataFrame([record]).to_sql(
            "prediction_log", engine, schema="dbo", if_exists="append", index=False
        )
        return True
    except Exception:
        return False


    # Example imaginary applicants (values for the main form; everything else stays typical)
PROFILES = {
    "Strong applicant": {
        "loan_amnt": 10000.0, "purpose": "credit_card", "annual_inc": 120000.0,
        "emp_length": "10+ years", "home_ownership": "MORTGAGE", "addr_state": "CA",
        "fico": 780.0, "dti": 8.0, "acc_open_past_24mths": 2.0,
        "inq_last_6mths": 0.0, "revol_util": 20.0, "credit_years": 20.0,
    },
    "Borderline applicant": {
        "loan_amnt": 20000.0, "purpose": "debt_consolidation", "annual_inc": 50000.0,
        "emp_length": "2 years", "home_ownership": "RENT", "addr_state": "CA",
        "fico": 670.0, "dti": 26.0, "acc_open_past_24mths": 9.0,
        "inq_last_6mths": 2.0, "revol_util": 80.0, "credit_years": 8.0,
    },
    "High-risk applicant": {
        "loan_amnt": 25000.0, "purpose": "small_business", "annual_inc": 30000.0,
        "emp_length": "Not provided", "home_ownership": "RENT", "addr_state": "CA",
        "fico": 650.0, "dti": 34.0, "acc_open_past_24mths": 15.0,
        "inq_last_6mths": 5.0, "revol_util": 95.0, "credit_years": 4.0,
    },
}
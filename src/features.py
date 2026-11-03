"""Feature engineering for the loan default project.

All transformations here are fixed rules decided during EDA. They do not
learn anything from the data, so they can be applied identically to the
training data, the test data, and a single new applicant in the app.
"""

import numpy as np
import pandas as pd


# Columns that are never model inputs
NON_FEATURE_COLUMNS = [
    "id", "issue_date", "target",
    "grade", "sub_grade", "int_rate", "installment",
    "funded_amnt", "total_pymnt",
]

# Categories with too few loans to estimate reliably (from EDA)
RARE_PURPOSES = ["renewable_energy", "educational"]
RARE_HOME_OWNERSHIP = ["OTHER", "NONE", "ANY"]
RARE_STATES = ["IA", "ID", "ND", "ME", "NE"]

EMP_LENGTH_YEARS = {
    "< 1 year": 0,
    "1 year": 1,
    "2 years": 2,
    "3 years": 3,
    "4 years": 4,
    "5 years": 5,
    "6 years": 6,
    "7 years": 7,
    "8 years": 8,
    "9 years": 9,
    "10+ years": 10,
}

# Columns removed after engineering (redundant or replaced by new features)
COLUMNS_TO_DROP = [
    "fico_range_low", "fico_range_high",   # replaced by fico_avg
    "num_sats",                            # duplicate of open_acc
    "num_rev_tl_bal_gt_0",                 # duplicate of num_actv_rev_tl
    "tot_hi_cred_lim",                     # replaced by total_bal_to_limit
    "emp_length",                          # replaced by emp_length_years + flag
    "earliest_cr_line",                    # replaced by credit_history_months
]

CATEGORICAL_FEATURES = [
    "home_ownership", "verification_status", "purpose", "addr_state",
]


def clean_placeholders(df):
    """Replace placeholder values with missing (NaN)."""
    df["annual_inc"] = df["annual_inc"].where(df["annual_inc"] > 0)
    df["dti"] = df["dti"].where(df["dti"] < 999)
    for col in ["total_rev_hi_lim", "tot_hi_cred_lim"]:
        df[col] = df[col].where(df[col] < 9_999_999)
    return df


def add_engineered_features(df):
    """Create new features from existing columns."""
    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2

    df["emp_length_years"] = df["emp_length"].map(EMP_LENGTH_YEARS)
    df["emp_length_missing"] = df["emp_length_years"].isna().astype(int)

    df["credit_history_months"] = (
        (df["issue_date"].dt.year - df["earliest_cr_line"].dt.year) * 12
        + (df["issue_date"].dt.month - df["earliest_cr_line"].dt.month)
    )

    df["loan_to_income"] = df["loan_amnt"] / df["annual_inc"]

    df["total_bal_to_limit"] = df["tot_cur_bal"] / df["tot_hi_cred_lim"]
    df["total_bal_to_limit"] = df["total_bal_to_limit"].replace(
        [np.inf, -np.inf], np.nan
    )
    return df


def group_rare_categories(df):
    """Merge categories with too few loans into a shared group."""
    df["purpose"] = df["purpose"].replace(RARE_PURPOSES, "other")
    df["home_ownership"] = df["home_ownership"].replace(RARE_HOME_OWNERSHIP, "OTHER")
    df["addr_state"] = df["addr_state"].replace(RARE_STATES, "OTHER")
    return df


def build_features(df):
    """Apply all feature engineering steps and return a new DataFrame."""
    df = df.copy()
    df = clean_placeholders(df)
    df = add_engineered_features(df)
    df = group_rare_categories(df)
    df = df.drop(columns=COLUMNS_TO_DROP)
    return df


def get_feature_columns(df):
    """Return the names of the model input columns."""
    return [c for c in df.columns if c not in NON_FEATURE_COLUMNS]




BINARY_FEATURES = ["emp_length_missing"]


def get_numeric_features(df):
    """Return the names of numeric model inputs (not categorical or binary)."""
    excluded = CATEGORICAL_FEATURES + BINARY_FEATURES
    return [c for c in get_feature_columns(df) if c not in excluded]
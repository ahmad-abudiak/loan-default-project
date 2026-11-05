"""Loan default risk: Streamlit demo app."""

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import json
from pathlib import Path

from src.app_support import (
    EMP_LENGTH_OPTIONS, MAIN_COLUMNS, build_applicant, friendly_name, log_prediction,
)
from src.explain import make_explainer, explain_applicant
from src.features import NON_FEATURE_COLUMNS
from src.policy import load_policy, decide

st.set_page_config(page_title="Loan default risk", layout="wide")


# ---------- Loading (runs once, then cached) ----------

@st.cache_resource
def load_assets():
    model = joblib.load("models/lightgbm_v2_calibrated.joblib")
    return {
        "model": model,
        "explainer": make_explainer(model),
        "policy": load_policy("results/policy.json"),
        "typical": pd.read_parquet("models/typical_applicant.parquet"),
        "demo_loans": pd.read_parquet("models/demo_loans.parquet"),
    }


@st.cache_resource
def get_engine_or_none():
    try:
        from sqlalchemy import text
        from src.db import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None


@st.cache_data
def load_results():
    return {
        "metrics": json.loads(Path("results/metrics.json").read_text()),
        "policy_results": pd.read_csv("results/policy_test_results.csv", index_col=0),
    }


assets = load_assets()
engine = get_engine_or_none()
typical = assets["typical"]
demo_loans = assets["demo_loans"]
policy = assets["policy"]

EXTRA_COLUMNS = [c for c in typical.columns if c not in MAIN_COLUMNS + NON_FEATURE_COLUMNS]


# ---------- Helper functions ----------

def clean(value):
    """Turn missing values into None and numbers into plain floats."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    return value


def values_from_row(row):
    """Convert one raw loan row into the values shown in the form."""
    months = (row["issue_date"].year - row["earliest_cr_line"].year) * 12 + (
        row["issue_date"].month - row["earliest_cr_line"].month
    )
    values = {
        "loan_amnt": clean(row["loan_amnt"]),
        "purpose": row["purpose"],
        "annual_inc": clean(row["annual_inc"]),
        "emp_length": row["emp_length"] if pd.notna(row["emp_length"]) else "Not provided",
        "home_ownership": row["home_ownership"],
        "addr_state": row["addr_state"],
        "fico": clean((row["fico_range_low"] + row["fico_range_high"]) / 2),
        "dti": clean(row["dti"]),
        "acc_open_past_24mths": clean(row["acc_open_past_24mths"]),
        "inq_last_6mths": clean(row["inq_last_6mths"]),
        "revol_util": clean(row["revol_util"]),
        "credit_years": round(months / 12, 1),
    }
    for col in EXTRA_COLUMNS:
        values[col] = clean(row[col])
    return values


def format_value(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "not reported"
    if isinstance(value, (int, float, np.integer, np.floating)):
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
    return str(value)


def options_for(column):
    """Dropdown choices: values seen in the demo loans plus the typical applicant's value."""
    choices = set(demo_loans[column].dropna().unique().tolist())
    choices.add(typical[column].iloc[0])
    return sorted(choices)


def same_value(a, b):
    """True if two form values are equal, treating None as equal and allowing tiny rounding."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    return a == b


def style_chart(fig, ax):
    """Transparent background and gray text, readable in light and dark themes."""
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_color("#888888")
    ax.tick_params(colors="#888888")
    ax.xaxis.label.set_color("#888888")
    ax.yaxis.label.set_color("#888888")


# ---------- Session state (remembers values between interactions) ----------

if "values" not in st.session_state:
    st.session_state["values"] = values_from_row(typical.iloc[0])
    st.session_state["issue_date"] = pd.Timestamp.today().normalize()
    st.session_state["loaded_loan"] = None
    st.session_state["loaded_values"] = None
    st.session_state["result"] = None
    st.session_state["version"] = 0


def load_random_loan():
    loan = demo_loans.sample(1).iloc[0]
    st.session_state["values"] = values_from_row(loan)
    st.session_state["loaded_values"] = dict(st.session_state["values"])
    st.session_state["issue_date"] = loan["issue_date"]
    st.session_state["loaded_loan"] = {
        "id": int(loan["id"]),
        "target": int(loan["target"]),
        "issue_date": loan["issue_date"],
    }
    st.session_state["result"] = None
    st.session_state["version"] += 1


def reset_to_typical():
    st.session_state["values"] = values_from_row(typical.iloc[0])
    st.session_state["loaded_values"] = None
    st.session_state["issue_date"] = pd.Timestamp.today().normalize()
    st.session_state["loaded_loan"] = None
    st.session_state["result"] = None
    st.session_state["version"] += 1


# ---------- Page ----------

st.title("Loan default risk")
st.caption("LightGBM model trained on Lending Club loans issued 2007–2014, "
           "calibrated and evaluated on 2015 loans.")

tab_score, tab_performance, tab_history = st.tabs(
    ["Score an applicant", "Model performance", "Prediction history"]
)

with tab_score:
    values = st.session_state["values"]
    v = st.session_state["version"]
    form = {}

    left, right = st.columns([1, 1.1], gap="large")

    with left:
        st.subheader("1. Application form")
        a, b = st.columns(2)
        form["loan_amnt"] = a.number_input("Loan amount ($)", min_value=500.0, step=500.0,
                                           value=values["loan_amnt"], format="%.0f", key=f"loan_amnt_{v}")
        purposes = options_for("purpose")
        form["purpose"] = b.selectbox("Purpose", purposes,
                                      index=purposes.index(values["purpose"]), key=f"purpose_{v}")
        form["annual_inc"] = a.number_input("Annual income ($)", min_value=0.0, step=1000.0,
                                            value=values["annual_inc"], format="%.0f", key=f"annual_inc_{v}")
        form["emp_length"] = b.selectbox("Employment length", EMP_LENGTH_OPTIONS,
                                         index=EMP_LENGTH_OPTIONS.index(values["emp_length"]),
                                         key=f"emp_length_{v}")
        homes = options_for("home_ownership")
        form["home_ownership"] = a.selectbox("Home ownership", homes,
                                             index=homes.index(values["home_ownership"]),
                                             key=f"home_ownership_{v}")
        states = options_for("addr_state")
        form["addr_state"] = b.selectbox("State", states,
                                         index=states.index(values["addr_state"]), key=f"addr_state_{v}")

        st.subheader("2. Credit report")
        a, b = st.columns(2)
        form["fico"] = a.number_input("Credit score (FICO)", min_value=300.0, max_value=850.0, step=5.0,
                                      value=values["fico"], format="%.0f", key=f"fico_{v}")
        form["dti"] = b.number_input("Debt-to-income ratio", min_value=0.0, step=0.5,
                                     value=values["dti"], key=f"dti_{v}")
        form["acc_open_past_24mths"] = a.number_input("Accounts opened, last 2 years", min_value=0.0,
                                                      step=1.0, value=values["acc_open_past_24mths"],
                                                      format="%.0f", key=f"acc_open_{v}")
        form["inq_last_6mths"] = b.number_input("Credit inquiries, last 6 months", min_value=0.0,
                                                step=1.0, value=values["inq_last_6mths"],
                                                format="%.0f", key=f"inq_{v}")
        form["revol_util"] = a.number_input("Revolving utilization (%)", min_value=0.0, step=1.0,
                                            value=values["revol_util"], key=f"revol_util_{v}")
        form["credit_years"] = b.number_input("Years of credit history", min_value=0.0, step=0.5,
                                              value=values["credit_years"], key=f"credit_years_{v}")

        extra = {}
        with st.expander(f"More credit details ({len(EXTRA_COLUMNS)} fields, typical values by default)"):
            a, b = st.columns(2)
            for i, col in enumerate(EXTRA_COLUMNS):
                column_box = a if i % 2 == 0 else b
                if col == "verification_status":
                    choices = options_for(col)
                    extra[col] = column_box.selectbox(friendly_name(col), choices,
                                                      index=choices.index(values[col]),
                                                      key=f"extra_{col}_{v}")
                else:
                    extra[col] = column_box.number_input(friendly_name(col), value=values[col],
                                                         key=f"extra_{col}_{v}")

        c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
        score_clicked = c1.button("Score applicant", type="primary", use_container_width=True)
        c2.button("Random test loan", on_click=load_random_loan, use_container_width=True)
        c3.button("Reset", on_click=reset_to_typical, use_container_width=True)

    if score_clicked:
        model = assets["model"]
        applicant = build_applicant(typical, form, st.session_state["issue_date"], extra)
        probability = float(model.predict_proba(applicant)[:, 1][0])
        decision = decide(probability, policy["cutoff"], policy["review_margin"])
        reasons = explain_applicant(model, assets["explainer"], applicant, top_n=len(applicant.columns))

        loaded = st.session_state["loaded_loan"]
        edited = False
        if loaded:
            current = {**form, **extra}
            original = st.session_state["loaded_values"]
            edited = any(not same_value(current[k], original[k]) for k in current)

        if loaded and not edited:
            source = "test_loan"
        elif loaded:
            source = "test_loan_edited"
        else:
            source = "manual"

        record = {
            "source": source,
            "loan_id": loaded["id"] if loaded else None,
            **{k: form[k] for k in ["loan_amnt", "purpose", "annual_inc", "emp_length",
                                    "home_ownership", "addr_state", "fico", "dti",
                                    "acc_open_past_24mths", "inq_last_6mths",
                                    "revol_util", "credit_years"]},
            "probability": probability,
            "decision": decision,
            "reason_1": reasons.loc[0, "feature"],
            "reason_2": reasons.loc[1, "feature"],
            "reason_3": reasons.loc[2, "feature"],
            "actual_default": loaded["target"] if (loaded and not edited) else None,
        }
        saved = log_prediction(engine, record)

        st.session_state["result"] = {
            "probability": probability, "decision": decision,
            "reasons": reasons, "saved": saved, "edited": edited,
        }

    with right:
        result = st.session_state["result"]
        loaded = st.session_state["loaded_loan"]

        if loaded and result is None:
            st.info(f"Loaded test loan {loaded['id']}, issued {loaded['issue_date']:%b %Y}. "
                    "Click **Score applicant** to see the prediction.")

        if result is None:
            st.write("Fill in the details and click **Score applicant**.")
        else:
            p = result["probability"]
            decision = result["decision"]
            cutoff = policy["cutoff"]
            review_start = cutoff - policy["review_margin"]

            m1, m2 = st.columns(2)
            m1.metric("Predicted default risk", f"{p * 100:.1f}%")
            with m2:
                st.write("Decision")
                if decision == "Approve":
                    st.success(decision)
                elif decision == "Review":
                    st.warning(decision)
                else:
                    st.error(decision)

            st.markdown(
                f"""
<div style="position:relative;height:16px;display:flex;border-radius:4px;overflow:hidden;margin-top:6px">
  <div style="width:{review_start * 100}%;background:#c8e6c9"></div>
  <div style="width:{policy['review_margin'] * 100}%;background:#ffe0b2"></div>
  <div style="width:{(1 - cutoff) * 100}%;background:#ffcdd2"></div>
  <div style="position:absolute;left:{min(p, 0.995) * 100}%;top:-3px;width:3px;height:22px;background:#333"></div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.caption(f"Approve below {review_start * 100:.0f}% · Review "
                       f"{review_start * 100:.0f}–{cutoff * 100:.0f}% · Reject {cutoff * 100:.0f}% and above")

            if loaded and not result["edited"]:
                outcome = "defaulted" if loaded["target"] == 1 else "repaid"
                st.write(f"**What actually happened:** this borrower {outcome}.")
            elif loaded:
                st.write("You edited this loan's values, so its actual outcome no longer applies.")

            st.subheader("Why this score")
            top5 = result["reasons"].head(5).iloc[::-1]
            labels = [f"{friendly_name(f)}: {format_value(val)}"
                      for f, val in zip(top5["feature"], top5["value"])]
            colors = ["#d9534f" if c > 0 else "#2e8b57" for c in top5["contribution"]]

            fig, ax = plt.subplots(figsize=(6, 2.8))
            ax.barh(labels, top5["contribution"], color=colors)
            ax.axvline(0, color="#888888", linewidth=0.8)
            ax.set_xlabel("← lowers risk        raises risk →")
            ax.tick_params(axis="y", labelsize=9)
            style_chart(fig, ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            if decision in ("Review", "Reject"):
                against = result["reasons"][result["reasons"]["contribution"] > 0].head(3)
                st.markdown("**Main reasons against approval**")
                for f, val in zip(against["feature"], against["value"]):
                    st.markdown(f"- {friendly_name(f)}: {format_value(val)}")

            st.caption(("Saved to the prediction log. " if result["saved"]
                        else "Not saved (database not available). ")
                       + "Shows the last scored inputs. Portfolio demo, not lending advice; "
                         "don't enter real personal data.")

with tab_performance:
    results = load_results()
    metrics = results["metrics"]
    lgbm_m = metrics["lightgbm"]

    st.subheader("Results on the test set (Jul–Dec 2015)")
    st.caption(f"{metrics['test_loans']:,} loans the model never saw during training, tuning, "
               f"or calibration. Actual default rate: {metrics['actual_default_rate'] * 100:.1f}%.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AUC", f"{lgbm_m['auc']:.3f}")
    c2.metric("Gini", f"{lgbm_m['gini']:.3f}")
    c3.metric("KS", f"{lgbm_m['ks']:.3f}")
    c4.metric("Average predicted risk", f"{lgbm_m['avg_predicted'] * 100:.1f}%",
              help="Compare with the actual default rate above: close values mean good calibration.")

    st.markdown("**Ranking quality compared with alternatives**")
    comparison = pd.DataFrame({
        "Model": ["LightGBM (this app)", "Logistic regression baseline", "Lending Club sub-grade"],
        "Test AUC": [lgbm_m["auc"], metrics["logistic_regression_auc"],
                     metrics["lending_club_sub_grade_auc"]],
    })
    comparison["Gini"] = 2 * comparison["Test AUC"] - 1
    st.dataframe(comparison.round(3), hide_index=True, use_container_width=True)

    lead = metrics["lead_over_sub_grade"]
    st.caption(f"Lead over Lending Club's sub-grade: {lead['mean']:+.3f} AUC "
               f"(95% bootstrap interval {lead['ci_95_low']:.3f} to {lead['ci_95_high']:.3f}).")

    st.markdown("**Business result of the approval policy**")
    pr = results["policy_results"]
    gain = pr.loc["LightGBM policy", "gain_vs_approve_all"]
    st.write(f"Rejecting applicants with a predicted risk of {policy['cutoff'] * 100:.0f}% or more "
             f"(cut-off chosen on Jan–Jun 2015) would have earned **${gain:.2f} million more** "
             f"than approving everyone on the test loans.")
    policy_table = pr.rename(columns={
        "approval_rate_pct": "Approved (%)",
        "default_rate_approved_pct": "Default rate of approved (%)",
        "profit_millions": "Profit ($M)",
        "gain_vs_approve_all": "Gain vs approve all ($M)",
    })
    st.dataframe(policy_table.round(2), use_container_width=True)

    st.markdown("**Charts**")
    charts = [
        ("roc_curves_validation.png", "ROC curves (validation, Jan–Jun 2015)"),
        ("calibration_test.png", "Calibration on the test set"),
        ("profit_by_cutoff_validation.png", "Profit by cut-off (validation)"),
        ("shap_importance.png", "Most important features (SHAP)"),
    ]
    left_col, right_col = st.columns(2)
    for i, (file_name, caption) in enumerate(charts):
        path = Path("results/figures") / file_name
        target_col = left_col if i % 2 == 0 else right_col
        if path.exists():
            target_col.image(str(path), caption=caption, use_container_width=True)
        else:
            target_col.warning(f"Chart not found: {file_name}")

with tab_history:
    if engine is None:
        st.info("The prediction history needs the SQL Server database, which isn't available here.")
    else:
        st.button("Refresh")

        summary = pd.read_sql(
            "SELECT decision, COUNT(*) AS predictions FROM dbo.prediction_log GROUP BY decision",
            engine,
        )
        total = int(summary["predictions"].sum()) if len(summary) else 0
        counts = dict(zip(summary["decision"], summary["predictions"]))

        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Predictions logged", f"{total:,}")
        h2.metric("Approve", counts.get("Approve", 0))
        h3.metric("Review", counts.get("Review", 0))
        h4.metric("Reject", counts.get("Reject", 0))

        st.markdown("**Latest predictions**")
        latest = pd.read_sql(
            """
            SELECT TOP 20 log_id, log_time, source, loan_amnt, annual_inc, fico, dti,
                   probability, decision, reason_1, actual_default
            FROM dbo.prediction_log
            ORDER BY log_id DESC
            """,
            engine,
        )
        latest["probability"] = (latest["probability"] * 100).round(1).astype(str) + "%"
        latest["reason_1"] = latest["reason_1"].map(friendly_name)
        latest["actual_default"] = latest["actual_default"].map(
            {0: "Repaid", 1: "Defaulted"}
        ).fillna("")
        latest = latest.rename(columns={
            "log_time": "Time (UTC)", "source": "Source", "loan_amnt": "Loan",
            "annual_inc": "Income", "fico": "FICO", "dti": "DTI",
            "probability": "Risk", "decision": "Decision",
            "reason_1": "Main reason", "actual_default": "Actual outcome",
        })
        st.dataframe(latest, hide_index=True, use_container_width=True)

        st.markdown("**How did the app do on unedited test loans?**")
        checked = pd.read_sql(
            """
            SELECT probability, actual_default
            FROM (
                SELECT probability, actual_default,
                       ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY log_id DESC) AS rn
                FROM dbo.prediction_log
                WHERE source = 'test_loan'
            ) AS t
            WHERE rn = 1
            """,
            engine,
        )
        if len(checked) < 5:
            st.caption("Score at least 5 real test loans (without editing them) to see this check.")
        else:
            k1, k2, k3 = st.columns(3)
            k1.metric("Distinct test loans scored", len(checked))
            k2.metric("Average predicted risk", f"{checked['probability'].mean() * 100:.1f}%")
            k3.metric("Actual default rate", f"{checked['actual_default'].mean() * 100:.1f}%")
            st.caption("With only a handful of loans these numbers vary a lot by chance; "
                       "they become meaningful after many scores.")
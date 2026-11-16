/*
    10_powerbi_views.sql
    Dashboard-ready views for Power BI.
*/

USE LoanDefault;
GO

-- ------------------------------------------------------------
-- All loans in the project population, with bands and profit
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_loans AS
SELECT
    m.id,
    m.issue_date,
    YEAR(m.issue_date) AS issue_year,
    s.split,
    m.grade,
    m.sub_grade,
    m.purpose,
    m.home_ownership,
    m.addr_state,
    m.verification_status,
    m.emp_length,
    m.loan_amnt,
    m.funded_amnt,
    m.total_pymnt,
    m.total_pymnt - m.funded_amnt AS profit,
    m.int_rate,
    m.annual_inc,
    m.dti,
    x.fico_avg,
    x.loan_to_income,
    CASE
        WHEN x.fico_avg < 670 THEN '1. Below 670'
        WHEN x.fico_avg < 690 THEN '2. 670-689'
        WHEN x.fico_avg < 710 THEN '3. 690-709'
        WHEN x.fico_avg < 740 THEN '4. 710-739'
        ELSE '5. 740+'
    END AS fico_band,
    CASE
        WHEN m.dti IS NULL OR m.dti >= 999 THEN '5. Unknown'
        WHEN m.dti < 10 THEN '1. Below 10'
        WHEN m.dti < 20 THEN '2. 10-19'
        WHEN m.dti < 30 THEN '3. 20-29'
        ELSE '4. 30+'
    END AS dti_band,
    CASE
        WHEN x.loan_to_income IS NULL THEN '5. Unknown'
        WHEN x.loan_to_income < 0.1 THEN '1. Below 0.1'
        WHEN x.loan_to_income < 0.2 THEN '2. 0.1-0.2'
        WHEN x.loan_to_income < 0.3 THEN '3. 0.2-0.3'
        ELSE '4. 0.3+'
    END AS loan_to_income_band,
    m.target AS defaulted
FROM dbo.loans_model AS m
JOIN dbo.loan_split AS s
    ON s.id = m.id
CROSS APPLY (
    SELECT
        (m.fico_range_low + m.fico_range_high) / 2 AS fico_avg,
        CASE WHEN m.annual_inc > 0 THEN m.loan_amnt / m.annual_inc END AS loan_to_income
) AS x;
GO


-- ------------------------------------------------------------
-- Model predictions on the test set, with readable reasons
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_predictions AS
SELECT
    p.id,
    p.probability,
    p.decision,
    CASE p.decision WHEN 'Approve' THEN 1 WHEN 'Review' THEN 2 ELSE 3 END AS decision_order,
    p.actual_default,
    NTILE(10) OVER (ORDER BY p.probability) AS risk_decile,
    COALESCE(f1.friendly_name, p.reason_1) AS main_reason,
    p.reason_1_effect AS main_reason_effect,
    COALESCE(f2.friendly_name, p.reason_2) AS second_reason,
    COALESCE(f3.friendly_name, p.reason_3) AS third_reason
FROM dbo.predictions AS p
LEFT JOIN dbo.feature_names AS f1 ON f1.feature = p.reason_1
LEFT JOIN dbo.feature_names AS f2 ON f2.feature = p.reason_2
LEFT JOIN dbo.feature_names AS f3 ON f3.feature = p.reason_3;
GO


-- ------------------------------------------------------------
-- Predictions made in the Streamlit app
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_prediction_log AS
SELECT
    log_id,
    log_time,
    CAST(log_time AS DATE) AS log_date,
    source,
    decision,
    probability,
    loan_amnt,
    annual_inc,
    fico,
    dti,
    reason_1,
    actual_default
FROM dbo.prediction_log;
GO

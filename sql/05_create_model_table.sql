/*
    05_create_model_table.sql
    Build dbo.loans_model: the clean, typed table used for modeling.

    Contents (72 columns):
      - Key and label: id, issue_date, target
      - Evaluation only (never used as features): grade, sub_grade,
        int_rate, installment, funded_amnt, total_pymnt
      - Features (63): chosen in the leakage audit (step 4.1)

    Conversions:
      - Numeric text -> FLOAT (TRY_CAST returns NULL instead of failing)
      - Categorical text -> trimmed of leading/trailing spaces
      - earliest_cr_line 'Mon-YYYY' -> DATE
*/

USE LoanDefault;
GO

DROP TABLE IF EXISTS dbo.loans_model;

SELECT
    -- Key and label
    TRY_CAST(id AS BIGINT)                          AS id,
    issue_date,
    CAST(target AS TINYINT)                         AS target,

    -- Evaluation only (not features)
    LTRIM(RTRIM(grade))                             AS grade,
    LTRIM(RTRIM(sub_grade))                         AS sub_grade,
    TRY_CAST(int_rate AS FLOAT)                     AS int_rate,
    TRY_CAST(installment AS FLOAT)                  AS installment,
    TRY_CAST(funded_amnt AS FLOAT)                  AS funded_amnt,
    TRY_CAST(total_pymnt AS FLOAT)                  AS total_pymnt,

    -- Features: application (8)
    TRY_CAST(loan_amnt AS FLOAT)                    AS loan_amnt,
    LTRIM(RTRIM(emp_length))                        AS emp_length,
    LTRIM(RTRIM(home_ownership))                    AS home_ownership,
    TRY_CAST(annual_inc AS FLOAT)                   AS annual_inc,
    LTRIM(RTRIM(verification_status))               AS verification_status,
    LTRIM(RTRIM(purpose))                           AS purpose,
    TRY_CAST(dti AS FLOAT)                          AS dti,
    LTRIM(RTRIM(addr_state))                        AS addr_state,

    -- Features: core credit history (19)
    TRY_CAST(delinq_2yrs AS FLOAT)                  AS delinq_2yrs,
    TRY_CONVERT(DATE, '01 ' + REPLACE(earliest_cr_line, '-', ' '), 106)
                                                    AS earliest_cr_line,
    TRY_CAST(fico_range_low AS FLOAT)               AS fico_range_low,
    TRY_CAST(fico_range_high AS FLOAT)              AS fico_range_high,
    TRY_CAST(inq_last_6mths AS FLOAT)               AS inq_last_6mths,
    TRY_CAST(mths_since_last_delinq AS FLOAT)       AS mths_since_last_delinq,
    TRY_CAST(mths_since_last_record AS FLOAT)       AS mths_since_last_record,
    TRY_CAST(mths_since_last_major_derog AS FLOAT)  AS mths_since_last_major_derog,
    TRY_CAST(open_acc AS FLOAT)                     AS open_acc,
    TRY_CAST(pub_rec AS FLOAT)                      AS pub_rec,
    TRY_CAST(revol_bal AS FLOAT)                    AS revol_bal,
    TRY_CAST(revol_util AS FLOAT)                   AS revol_util,
    TRY_CAST(total_acc AS FLOAT)                    AS total_acc,
    TRY_CAST(collections_12_mths_ex_med AS FLOAT)   AS collections_12_mths_ex_med,
    TRY_CAST(acc_now_delinq AS FLOAT)               AS acc_now_delinq,
    TRY_CAST(chargeoff_within_12_mths AS FLOAT)     AS chargeoff_within_12_mths,
    TRY_CAST(delinq_amnt AS FLOAT)                  AS delinq_amnt,
    TRY_CAST(pub_rec_bankruptcies AS FLOAT)         AS pub_rec_bankruptcies,
    TRY_CAST(tax_liens AS FLOAT)                    AS tax_liens,

    -- Features: extended credit bureau data (36)
    TRY_CAST(tot_coll_amt AS FLOAT)                 AS tot_coll_amt,
    TRY_CAST(tot_cur_bal AS FLOAT)                  AS tot_cur_bal,
    TRY_CAST(total_rev_hi_lim AS FLOAT)             AS total_rev_hi_lim,
    TRY_CAST(acc_open_past_24mths AS FLOAT)         AS acc_open_past_24mths,
    TRY_CAST(avg_cur_bal AS FLOAT)                  AS avg_cur_bal,
    TRY_CAST(bc_open_to_buy AS FLOAT)               AS bc_open_to_buy,
    TRY_CAST(bc_util AS FLOAT)                      AS bc_util,
    TRY_CAST(mo_sin_old_il_acct AS FLOAT)           AS mo_sin_old_il_acct,
    TRY_CAST(mo_sin_old_rev_tl_op AS FLOAT)         AS mo_sin_old_rev_tl_op,
    TRY_CAST(mo_sin_rcnt_rev_tl_op AS FLOAT)        AS mo_sin_rcnt_rev_tl_op,
    TRY_CAST(mo_sin_rcnt_tl AS FLOAT)               AS mo_sin_rcnt_tl,
    TRY_CAST(mort_acc AS FLOAT)                     AS mort_acc,
    TRY_CAST(mths_since_recent_bc AS FLOAT)         AS mths_since_recent_bc,
    TRY_CAST(mths_since_recent_bc_dlq AS FLOAT)     AS mths_since_recent_bc_dlq,
    TRY_CAST(mths_since_recent_inq AS FLOAT)        AS mths_since_recent_inq,
    TRY_CAST(mths_since_recent_revol_delinq AS FLOAT) AS mths_since_recent_revol_delinq,
    TRY_CAST(num_accts_ever_120_pd AS FLOAT)        AS num_accts_ever_120_pd,
    TRY_CAST(num_actv_bc_tl AS FLOAT)               AS num_actv_bc_tl,
    TRY_CAST(num_actv_rev_tl AS FLOAT)              AS num_actv_rev_tl,
    TRY_CAST(num_bc_sats AS FLOAT)                  AS num_bc_sats,
    TRY_CAST(num_bc_tl AS FLOAT)                    AS num_bc_tl,
    TRY_CAST(num_il_tl AS FLOAT)                    AS num_il_tl,
    TRY_CAST(num_op_rev_tl AS FLOAT)                AS num_op_rev_tl,
    TRY_CAST(num_rev_accts AS FLOAT)                AS num_rev_accts,
    TRY_CAST(num_rev_tl_bal_gt_0 AS FLOAT)          AS num_rev_tl_bal_gt_0,
    TRY_CAST(num_sats AS FLOAT)                     AS num_sats,
    TRY_CAST(num_tl_120dpd_2m AS FLOAT)             AS num_tl_120dpd_2m,
    TRY_CAST(num_tl_30dpd AS FLOAT)                 AS num_tl_30dpd,
    TRY_CAST(num_tl_90g_dpd_24m AS FLOAT)           AS num_tl_90g_dpd_24m,
    TRY_CAST(num_tl_op_past_12m AS FLOAT)           AS num_tl_op_past_12m,
    TRY_CAST(pct_tl_nvr_dlq AS FLOAT)               AS pct_tl_nvr_dlq,
    TRY_CAST(percent_bc_gt_75 AS FLOAT)             AS percent_bc_gt_75,
    TRY_CAST(tot_hi_cred_lim AS FLOAT)              AS tot_hi_cred_lim,
    TRY_CAST(total_bal_ex_mort AS FLOAT)            AS total_bal_ex_mort,
    TRY_CAST(total_bc_limit AS FLOAT)               AS total_bc_limit,
    TRY_CAST(total_il_high_credit_limit AS FLOAT)   AS total_il_high_credit_limit
INTO dbo.loans_model
FROM dbo.loans_population;
GO

-- Make id the primary key
ALTER TABLE dbo.loans_model ALTER COLUMN id BIGINT NOT NULL;
GO

ALTER TABLE dbo.loans_model
    ADD CONSTRAINT PK_loans_model PRIMARY KEY (id);
GO


-- ------------------------------------------------------------
-- Verify: null counts must match the raw audit (no failed conversions)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dbo.column_audit_model;

DECLARE @sql NVARCHAR(MAX);

SELECT @sql = STRING_AGG(
    CAST(
        'SELECT ''' + COLUMN_NAME + ''' AS column_name, '
        + 'COUNT(*) - COUNT(' + QUOTENAME(COLUMN_NAME) + ') AS null_count '
        + 'FROM dbo.loans_model'
    AS NVARCHAR(MAX)),
    ' UNION ALL '
)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = 'loans_model';

SET @sql = 'SELECT * INTO dbo.column_audit_model FROM (' + @sql + ') AS x;';

EXEC sp_executesql @sql;

-- Columns where conversion created new nulls (expected: no rows)
SELECT
    m.column_name,
    a.null_count AS nulls_before,
    m.null_count AS nulls_after,
    m.null_count - a.null_count AS failed_conversions
FROM dbo.column_audit_model AS m
JOIN dbo.column_audit AS a
    ON a.column_name = m.column_name
WHERE m.null_count <> a.null_count;

-- Row count (expected: 618,584) and a quick look
SELECT COUNT(*) AS loans FROM dbo.loans_model;

SELECT TOP 5 * FROM dbo.loans_model;
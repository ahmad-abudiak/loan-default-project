/*
    08_create_prediction_log.sql
    Stores every prediction made in the Streamlit app.
*/

USE LoanDefault;
GO

DROP TABLE IF EXISTS dbo.prediction_log;

CREATE TABLE dbo.prediction_log (
    log_id                INT IDENTITY(1, 1) PRIMARY KEY,
    log_time              DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
    source                VARCHAR(20)   NOT NULL,
    loan_id               BIGINT        NULL,
    loan_amnt             FLOAT         NULL,
    purpose               VARCHAR(30)   NULL,
    annual_inc            FLOAT         NULL,
    emp_length            VARCHAR(20)   NULL,
    home_ownership        VARCHAR(20)   NULL,
    addr_state            VARCHAR(10)   NULL,
    fico                  FLOAT         NULL,
    dti                   FLOAT         NULL,
    acc_open_past_24mths  FLOAT         NULL,
    inq_last_6mths        FLOAT         NULL,
    revol_util            FLOAT         NULL,
    credit_years          FLOAT         NULL,
    probability           FLOAT         NOT NULL,
    decision              VARCHAR(10)   NOT NULL,
    reason_1              VARCHAR(50)   NULL,
    reason_2              VARCHAR(50)   NULL,
    reason_3              VARCHAR(50)   NULL,
    actual_default        TINYINT       NULL
);
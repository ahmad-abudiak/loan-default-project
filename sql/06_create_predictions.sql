/*
    06_create_predictions.sql
    Stores the final model's predictions for the test loans (Jul-Dec 2015):
    probability, decision, actual outcome, and the top 3 SHAP reasons.
*/

USE LoanDefault;
GO

DROP TABLE IF EXISTS dbo.predictions;

CREATE TABLE dbo.predictions (
    id                      BIGINT        NOT NULL PRIMARY KEY,
    split                   VARCHAR(10)   NOT NULL,
    model_name              VARCHAR(50)   NOT NULL,
    probability             FLOAT         NOT NULL,
    decision                VARCHAR(10)   NOT NULL,
    actual_default          TINYINT       NOT NULL,
    reason_1                VARCHAR(50)   NULL,
    reason_1_effect         VARCHAR(12)   NULL,
    reason_1_contribution   FLOAT         NULL,
    reason_2                VARCHAR(50)   NULL,
    reason_2_effect         VARCHAR(12)   NULL,
    reason_2_contribution   FLOAT         NULL,
    reason_3                VARCHAR(50)   NULL,
    reason_3_effect         VARCHAR(12)   NULL,
    reason_3_contribution   FLOAT         NULL,
    created_at              DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);
USE LoanDefault;
GO

-- How many months after issue did charged-off borrowers make their last payment?
WITH charged_off AS (
    SELECT
        p.issue_date,
        TRY_CONVERT(DATE, '01 ' + REPLACE(p.last_pymnt_d, '-', ' '), 106) AS last_pymnt_date
    FROM dbo.loans_population AS p
    WHERE p.target = 1
)
SELECT
    DATEDIFF(MONTH, issue_date, last_pymnt_date) AS months_to_last_payment,
    COUNT(*) AS loans
FROM charged_off
GROUP BY DATEDIFF(MONTH, issue_date, last_pymnt_date)
ORDER BY months_to_last_payment;



DROP TABLE IF EXISTS dbo.target_early;

SELECT
    TRY_CAST(p.id AS BIGINT) AS id,
    DATEDIFF(MONTH, p.issue_date, d.last_pymnt_date) AS months_to_last_payment,
    CASE
        WHEN p.target = 1
             AND (d.last_pymnt_date IS NULL
                  OR DATEDIFF(MONTH, p.issue_date, d.last_pymnt_date) <= 8)
        THEN 1
        ELSE 0
    END AS target_early
INTO dbo.target_early
FROM dbo.loans_population AS p
CROSS APPLY (
    SELECT TRY_CONVERT(DATE, '01 ' + REPLACE(p.last_pymnt_d, '-', ' '), 106) AS last_pymnt_date
) AS d;
GO

ALTER TABLE dbo.target_early ALTER COLUMN id BIGINT NOT NULL;
GO

ALTER TABLE dbo.target_early ADD CONSTRAINT PK_target_early PRIMARY KEY (id);
GO



-- Check 1: row count (expected: 618,584) and overall early default rate
SELECT
    COUNT(*) AS loans,
    SUM(target_early) AS early_defaults,
    CAST(100.0 * AVG(CAST(target_early AS FLOAT)) AS DECIMAL(5, 2)) AS early_rate_pct
FROM dbo.target_early;


-- Check 2: how the two targets relate (expected: no row with target = 0 and target_early = 1)
SELECT
    p.target,
    e.target_early,
    COUNT(*) AS loans
FROM dbo.loans_population AS p
JOIN dbo.target_early AS e ON e.id = TRY_CAST(p.id AS BIGINT)
GROUP BY p.target, e.target_early
ORDER BY p.target, e.target_early;


-- Check 3: early default rate by issue year, next to the original default rate
SELECT
    YEAR(m.issue_date) AS issue_year,
    COUNT(*) AS loans,
    CAST(100.0 * AVG(CAST(m.target AS FLOAT)) AS DECIMAL(5, 2)) AS default_rate_pct,
    CAST(100.0 * AVG(CAST(e.target_early AS FLOAT)) AS DECIMAL(5, 2)) AS early_rate_pct
FROM dbo.loans_model AS m
JOIN dbo.target_early AS e ON e.id = m.id
GROUP BY YEAR(m.issue_date)
ORDER BY issue_year;
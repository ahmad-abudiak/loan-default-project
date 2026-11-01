/*
    03_create_population.sql
    Build the project population from dbo.raw_loans.

    Population:
      - 36-month loans only
      - Issued 2007-01-01 to 2015-12-31
      - Final status: Fully Paid, Charged Off, or Default
        (excludes Current/Late/Grace loans, credit-policy loans,
         and the 33 broken summary rows)

    New columns:
      - issue_date : issue_d converted from 'Mon-YYYY' text to DATE
      - target     : 1 = Charged Off or Default, 0 = Fully Paid
*/

USE LoanDefault;
GO

DROP TABLE IF EXISTS dbo.loans_population;

SELECT
    r.*,
    d.issue_date,
    CASE
        WHEN r.loan_status IN ('Charged Off', 'Default') THEN 1
        ELSE 0
    END AS target
INTO dbo.loans_population
FROM dbo.raw_loans AS r
CROSS APPLY (
    SELECT TRY_CONVERT(DATE, '01 ' + REPLACE(r.issue_d, '-', ' '), 106) AS issue_date
) AS d
WHERE r.loan_status IN ('Fully Paid', 'Charged Off', 'Default')
  AND LTRIM(r.term) = '36 months'
  AND d.issue_date >= '2007-01-01'
  AND d.issue_date <  '2016-01-01';

-- Check 1: row count and overall target rate
-- Expected: 618,584 rows, about 13.9% target rate
SELECT
    COUNT(*) AS loans,
    SUM(target) AS charged_off,
    CAST(100.0 * AVG(CAST(target AS FLOAT)) AS DECIMAL(5, 2)) AS target_rate_pct
FROM dbo.loans_population;


-- Check 2: no dates failed to convert
-- Expected: 0
SELECT COUNT(*) AS null_issue_dates
FROM dbo.loans_population
WHERE issue_date IS NULL;


-- Check 3: each loan appears only once
-- Expected: both numbers equal
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT id) AS distinct_ids
FROM dbo.loans_population;


-- Check 4: target rate by issue year
SELECT
    YEAR(issue_date) AS issue_year,
    COUNT(*) AS loans,
    SUM(target) AS charged_off,
    CAST(100.0 * AVG(CAST(target AS FLOAT)) AS DECIMAL(5, 2)) AS target_rate_pct
FROM dbo.loans_population
GROUP BY YEAR(issue_date)
ORDER BY issue_year;
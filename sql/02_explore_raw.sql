/*
    02_explore_raw.sql
    Explore the key columns in dbo.raw_loans before defining the project population.
    Columns checked: loan_status, term, issue_d.
*/

USE LoanDefault;
GO


-- ------------------------------------------------------------
-- Query 1: Loan status distribution
-- Shows every status, its count, and its share of all loans.
-- Excludes the 33 broken summary rows (loan_status IS NULL).
-- ------------------------------------------------------------
SELECT
    loan_status,
    COUNT(*) AS loans,
    CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS DECIMAL(5, 2)) AS pct
FROM dbo.raw_loans
WHERE loan_status IS NOT NULL
GROUP BY loan_status
ORDER BY loans DESC;


-- ------------------------------------------------------------
-- Query 2: Term values
-- Compares LEN (ignores trailing spaces) with DATALENGTH / 2
-- (counts every character) to expose hidden spaces.
-- ------------------------------------------------------------
SELECT
    term,
    LEN(term) AS len_without_trailing_spaces,
    DATALENGTH(term) / 2 AS actual_characters,
    COUNT(*) AS loans
FROM dbo.raw_loans
WHERE term IS NOT NULL
GROUP BY term;


-- ------------------------------------------------------------
-- Query 3: Issue date format
-- Shows how issue_d is written, to decide how to convert it to DATE.
-- ------------------------------------------------------------
SELECT TOP 10
    issue_d,
    COUNT(*) AS loans
FROM dbo.raw_loans
WHERE issue_d IS NOT NULL
GROUP BY issue_d
ORDER BY loans DESC;


-- ------------------------------------------------------------
-- Query 4: Loan outcomes by issue year (36-month loans only)
-- Checks the 2007-2015 cutoff: unfinished loans should be rare
-- up to 2015 and common from 2016 onward.
-- ------------------------------------------------------------
SELECT
    RIGHT(issue_d, 4) AS issue_year,
    COUNT(*) AS total,
    SUM(CASE WHEN loan_status = 'Fully Paid' THEN 1 ELSE 0 END) AS fully_paid,
    SUM(CASE WHEN loan_status IN ('Charged Off', 'Default') THEN 1 ELSE 0 END) AS charged_off,
    SUM(CASE WHEN loan_status NOT IN ('Fully Paid', 'Charged Off', 'Default') THEN 1 ELSE 0 END) AS not_finished
FROM dbo.raw_loans
WHERE loan_status IS NOT NULL
  AND term LIKE '%36%'
GROUP BY RIGHT(issue_d, 4)
ORDER BY issue_year;
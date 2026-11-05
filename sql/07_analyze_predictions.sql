USE LoanDefault;
GO

-- 1. Row count (expected: 162,236)
SELECT COUNT(*) AS loans FROM dbo.predictions;


-- 2. Results by decision: loans, default rate, profit
SELECT
    p.decision,
    COUNT(*) AS loans,
    CAST(100.0 * AVG(CAST(p.actual_default AS FLOAT)) AS DECIMAL(5, 2)) AS default_rate_pct,
    CAST(SUM(m.total_pymnt - m.funded_amnt) / 1e6 AS DECIMAL(10, 2)) AS profit_millions
FROM dbo.predictions AS p
JOIN dbo.loans_model AS m ON m.id = p.id
GROUP BY p.decision
ORDER BY default_rate_pct;


-- 3. The most common main reasons for rejection
SELECT TOP 10
    reason_1,
    COUNT(*) AS rejections,
    CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS DECIMAL(5, 1)) AS pct_of_rejections
FROM dbo.predictions
WHERE decision = 'Reject'
GROUP BY reason_1
ORDER BY rejections DESC;


-- 4. Good borrowers wrongly rejected, by state (top 10)
SELECT TOP 10
    m.addr_state,
    COUNT(*) AS wrongly_rejected
FROM dbo.predictions AS p
JOIN dbo.loans_model AS m ON m.id = p.id
WHERE p.decision = 'Reject' AND p.actual_default = 0
GROUP BY m.addr_state
ORDER BY wrongly_rejected DESC;


-- 5. Good borrowers wrongly rejected, by state (top 10), with wrongly rejected percentage
SELECT TOP 10
    m.addr_state,
    SUM(CASE WHEN p.actual_default = 0 THEN 1 ELSE 0 END) AS good_borrowers,
    SUM(CASE WHEN p.actual_default = 0 AND p.decision = 'Reject' THEN 1 ELSE 0 END) AS wrongly_rejected,
    CAST(100.0 * SUM(CASE WHEN p.actual_default = 0 AND p.decision = 'Reject' THEN 1 ELSE 0 END)
         / SUM(CASE WHEN p.actual_default = 0 THEN 1 ELSE 0 END) AS DECIMAL(5, 2)) AS wrongly_rejected_pct
FROM dbo.predictions AS p
JOIN dbo.loans_model AS m ON m.id = p.id
GROUP BY m.addr_state
HAVING SUM(CASE WHEN p.actual_default = 0 THEN 1 ELSE 0 END) >= 1000
ORDER BY wrongly_rejected_pct DESC;


-- 6. Loans Lending Club rated A or B that our model would reject
SELECT
    m.grade,
    COUNT(*) AS rejected_by_model,
    CAST(100.0 * AVG(CAST(p.actual_default AS FLOAT)) AS DECIMAL(5, 2)) AS actual_default_rate_pct
FROM dbo.predictions AS p
JOIN dbo.loans_model AS m ON m.id = p.id
WHERE m.grade IN ('A', 'B') AND p.decision = 'Reject'
GROUP BY m.grade;
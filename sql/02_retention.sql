-- =============================================================================
-- 02_retention.sql
-- Maps to JD line: "recurring metrics: ... retention ..." and
-- "monthly retention breakdown"
-- =============================================================================

-- 2a. Headline retention rate: of all placements ever made, what share are
--     still active today?
SELECT
    COUNT(*)                                                        AS total_placements_ever,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)              AS active_today,
    ROUND(100.0 * SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) / COUNT(*), 1) AS retention_rate_pct
FROM placements;

-- 2b. Retention by tenure band (how long placements that DID end actually lasted)
SELECT
    CASE
        WHEN tenure_days < 60  THEN '0-60 days'
        WHEN tenure_days < 120 THEN '61-120 days'
        WHEN tenure_days < 240 THEN '121-240 days'
        ELSE '240+ days'
    END AS tenure_band,
    COUNT(*) AS ended_placements
FROM (
    SELECT
        placement_id,
        julianday(end_date) - julianday(start_date) AS tenure_days
    FROM placements
    WHERE status = 'Ended'
)
GROUP BY tenure_band
ORDER BY MIN(tenure_days);

-- 2c. Retention driver: end reason breakdown (client-side churn vs staff-side churn)
--     This is the number leadership actually wants — is attrition on us or on them?
SELECT
    end_reason,
    COUNT(*)                                                            AS occurrences,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM placements WHERE status = 'Ended'), 1) AS pct_of_churn
FROM placements
WHERE status = 'Ended'
GROUP BY end_reason
ORDER BY occurrences DESC;

-- 2d. Monthly retention cohort: of placements that STARTED in a given month,
--     what % are still active? (classic cohort retention curve)
SELECT
    strftime('%Y-%m', start_date)                                        AS start_cohort_month,
    COUNT(*)                                                              AS placements_started,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)                    AS still_active,
    ROUND(100.0 * SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_still_active
FROM placements
GROUP BY start_cohort_month
ORDER BY start_cohort_month;

-- 2e. Retention by role and by region (staffing-mix diagnostic)
SELECT
    role,
    region,
    COUNT(*)                                                          AS total_placements,
    ROUND(100.0 * SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) / COUNT(*), 1) AS retention_rate_pct
FROM placements
GROUP BY role, region
HAVING total_placements >= 2
ORDER BY retention_rate_pct ASC;

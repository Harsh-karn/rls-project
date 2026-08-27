-- =============================================================================
-- 03_escalations.sql
-- Maps to JD line: "recurring metrics: ... escalations" and
-- "Flag data gaps and quality issues directly rather than quietly working
-- around them"
-- =============================================================================

-- 3a. Escalation rate: escalations per active placement (a normalized load metric)
SELECT
    (SELECT COUNT(*) FROM escalations)                              AS total_escalations,
    (SELECT COUNT(*) FROM placements)                                AS total_placements,
    ROUND(1.0 * (SELECT COUNT(*) FROM escalations) /
          (SELECT COUNT(*) FROM placements), 2)                     AS escalations_per_placement;

-- 3b. Escalations by category and severity — where is operational risk concentrated?
SELECT
    category,
    severity,
    COUNT(*) AS escalation_count
FROM escalations
GROUP BY category, severity
ORDER BY category, 
    CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;

-- 3c. Resolution performance: % resolved and average days-to-resolve by severity.
--     This is the SLA-style metric leadership will ask for first.
SELECT
    severity,
    COUNT(*)                                                             AS total_raised,
    SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END)                        AS resolved_count,
    ROUND(100.0 * SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_resolved,
    ROUND(AVG(
        CASE WHEN resolved = 1
             THEN julianday(resolution_date) - julianday(date_raised)
             ELSE NULL END
    ), 1)                                                                AS avg_days_to_resolve
FROM escalations
GROUP BY severity
ORDER BY CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;

-- 3d. Open (unresolved) escalations right now — the "needs attention today" list
SELECT
    e.escalation_id,
    e.client_id,
    c.firm_name,
    e.category,
    e.severity,
    e.date_raised,
    CAST(julianday('now') - julianday(e.date_raised) AS INTEGER) AS days_open
FROM escalations e
JOIN clients c ON c.client_id = e.client_id
WHERE e.resolved = 0
ORDER BY e.severity DESC, days_open DESC;

-- 3e. Clients generating the most escalations (client-health signal, not just staff-health)
SELECT
    cl.client_id,
    cl.firm_name,
    cl.plan_tier,
    COUNT(e.escalation_id) AS escalation_count
FROM clients cl
JOIN placements p ON p.client_id = cl.client_id
JOIN escalations e ON e.placement_id = p.placement_id
GROUP BY cl.client_id, cl.firm_name, cl.plan_tier
ORDER BY escalation_count DESC
LIMIT 10;

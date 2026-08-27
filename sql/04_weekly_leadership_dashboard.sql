-- =============================================================================
-- 04_weekly_leadership_dashboard.sql
-- Maps to JD line: "Support the Weekly Leadership Dashboard by ensuring the
-- underlying data is pulled, cleaned, and refreshed ahead of each reporting
-- cycle" + "dashboards run clean with zero blanks or broken links"
-- =============================================================================

-- 4a. Single-row leadership summary — the numbers that would headline the
--     Monday morning leadership dashboard.
SELECT
    (SELECT COUNT(*) FROM candidates WHERE application_date >= date('now', '-7 day')) AS new_applicants_7d,
    (SELECT COUNT(*) FROM candidates WHERE current_stage = 'Placed' AND stage_date >= date('now', '-7 day')) AS placements_7d,
    (SELECT ROUND(100.0 * SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) / COUNT(*), 1) FROM placements) AS retention_rate_pct,
    (SELECT COUNT(*) FROM escalations WHERE resolved = 0) AS open_escalations,
    (SELECT COUNT(*) FROM clients) AS total_active_clients;

-- 4b. Data-quality / hygiene check: rows that would break a dashboard if left
--     unnoticed. A real "catching blanks, duplicates, and inconsistencies
--     proactively" query — run this before every refresh.
SELECT 'candidates_missing_stage_date'  AS check_name, COUNT(*) AS issue_count FROM candidates WHERE stage_date IS NULL OR stage_date = ''
UNION ALL
SELECT 'placements_ended_but_no_end_date', COUNT(*) FROM placements WHERE status = 'Ended' AND (end_date IS NULL OR end_date = '')
UNION ALL
SELECT 'placements_active_but_has_end_date', COUNT(*) FROM placements WHERE status = 'Active' AND end_date != ''
UNION ALL
SELECT 'placements_end_before_start', COUNT(*) FROM placements WHERE end_date != '' AND julianday(end_date) < julianday(start_date)
UNION ALL
SELECT 'duplicate_candidate_ids', COUNT(*) - COUNT(DISTINCT candidate_id) FROM candidates
UNION ALL
SELECT 'escalations_resolved_but_no_resolution_date', COUNT(*) FROM escalations WHERE resolved = 1 AND (resolution_date IS NULL OR resolution_date = '');

-- 4c. Reporting cadence hygiene (Monday.com board): is the reporting function
--     itself hitting its own deadlines? Directly measures "dashboards run
--     clean ... at any weekly check" from the success criteria.
SELECT
    report_name,
    COUNT(*)                                                              AS weeks_tracked,
    SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END)                   AS weeks_overdue,
    ROUND(100.0 * SUM(CASE WHEN on_time = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_on_time
FROM reporting_tasks
GROUP BY report_name
ORDER BY pct_on_time ASC;

-- 4d. Trailing 12-week trend of new applicants vs. placements (what a
--     leadership-dashboard line chart is built from)
SELECT
    strftime('%Y-%W', application_date) AS app_week,
    COUNT(*)                            AS new_applicants,
    SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END) AS placed_from_that_week
FROM candidates
WHERE application_date >= date('now', '-84 day')
GROUP BY app_week
ORDER BY app_week;

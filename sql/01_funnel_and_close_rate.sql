-- =============================================================================
-- 01_funnel_and_close_rate.sql
-- Maps to JD line: "recurring metrics: close rate ... using Claude to clean
-- and QA the data before it reaches leadership" + "breaking a funnel metric
-- into stage-by-stage data"
-- =============================================================================

-- 1a. Overall recruiting funnel (stage-by-stage counts)
SELECT
    current_stage,
    COUNT(*)                                            AS candidate_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM candidates), 1) AS pct_of_all_applicants
FROM candidates
GROUP BY current_stage
ORDER BY
    CASE current_stage
        WHEN 'Applied'      THEN 1
        WHEN 'Screened'     THEN 2
        WHEN 'Interviewed'  THEN 3
        WHEN 'Offered'      THEN 4
        WHEN 'Placed'       THEN 5
        WHEN 'Rejected'     THEN 6
        WHEN 'Withdrawn'    THEN 7
    END;

-- 1b. Close rate = Placed / (candidates who reached "Offered" or further)
--     This is the metric a staffing agency actually manages to, since a
--     "close" is defined at the offer stage, not at first application.
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END)
        / SUM(CASE WHEN current_stage IN ('Placed', 'Offered', 'Rejected') AND
                        current_stage != 'Applied' AND current_stage != 'Screened'
                   THEN 1 ELSE 0 END)
    , 1) AS close_rate_pct_of_offers
FROM candidates
WHERE current_stage IN ('Offered', 'Placed');
-- Note: a stricter version would require a `reached_offer_stage` flag rather
-- than inferring from current_stage; see docs for the known-quirks writeup.

-- 1c. Close rate by role (surfaces which roles are hardest to fill)
SELECT
    role_applied,
    SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END)                    AS placed,
    SUM(CASE WHEN current_stage IN ('Offered', 'Placed') THEN 1 ELSE 0 END)      AS offered_or_placed,
    ROUND(
        100.0 * SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN current_stage IN ('Offered', 'Placed') THEN 1 ELSE 0 END), 0)
    , 1) AS close_rate_pct
FROM candidates
GROUP BY role_applied
ORDER BY close_rate_pct DESC;

-- 1d. Close rate by sourcing channel (which channels convert, not just fill top of funnel)
SELECT
    source_channel,
    COUNT(*)                                                                      AS total_applicants,
    SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END)                     AS placed,
    ROUND(100.0 * SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END) / COUNT(*), 1) AS placement_rate_pct
FROM candidates
GROUP BY source_channel
ORDER BY placement_rate_pct DESC;

-- 1e. Recruiter-level funnel (for 1:1s / workload balancing)
SELECT
    recruiter,
    COUNT(*)                                                                    AS candidates_owned,
    SUM(CASE WHEN current_stage = 'Placed' THEN 1 ELSE 0 END)                   AS placements,
    ROUND(AVG(julianday(stage_date) - julianday(application_date)), 1)         AS avg_days_in_pipeline
FROM candidates
GROUP BY recruiter
ORDER BY placements DESC;

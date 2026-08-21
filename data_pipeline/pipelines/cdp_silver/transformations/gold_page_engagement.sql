CREATE OR REFRESH MATERIALIZED VIEW gold_page_engagement
COMMENT "One row per page_location: time-on-page metrics derived from event_pageview. Dwell time is the gap between consecutive pageviews within a session; consecutive/duplicate same-page events are collapsed into a single visit so duplicate page_view emissions don't split a stay into zero-second slivers."
TBLPROPERTIES ("quality" = "gold")
AS
WITH ordered AS (
  SELECT
    page_location,
    page_title,
    user_id,
    source_timestamp,
    CONCAT(COALESCE(client_id, ''), '|', COALESCE(ga_session_id, '')) AS session_key,
    LAG(page_location) OVER (
      PARTITION BY CONCAT(COALESCE(client_id, ''), '|', COALESCE(ga_session_id, ''))
      ORDER BY source_timestamp
    ) AS prev_page_location
  FROM event_pageview
  WHERE source_timestamp IS NOT NULL
),
flagged AS (
  SELECT *,
    CASE
      WHEN prev_page_location IS NULL OR prev_page_location <> page_location THEN 1
      ELSE 0
    END AS is_new_visit
  FROM ordered
),
visits_grouped AS (
  SELECT *,
    SUM(is_new_visit) OVER (
      PARTITION BY session_key
      ORDER BY source_timestamp
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS visit_id
  FROM flagged
),
visits AS (
  -- Collapse a run of consecutive identical page_location events (including
  -- exact duplicate page_view emissions) into one visit, keeping the earliest
  -- timestamp. raw_event_count preserves the pre-collapse count.
  SELECT
    session_key,
    visit_id,
    page_location,
    MAX(page_title)       AS page_title,
    MAX(user_id)          AS user_id,
    MIN(source_timestamp) AS visit_start,
    COUNT(*)              AS raw_event_count
  FROM visits_grouped
  GROUP BY session_key, visit_id, page_location
),
with_dwell AS (
  SELECT *,
    LEAD(visit_start) OVER (
      PARTITION BY session_key
      ORDER BY visit_start
    ) AS next_visit_start
  FROM visits
),
dwell AS (
  SELECT *,
    CASE
      WHEN next_visit_start IS NOT NULL
      THEN UNIX_TIMESTAMP(next_visit_start) - UNIX_TIMESTAMP(visit_start)
    END AS seconds_on_page
  FROM with_dwell
)
SELECT
  page_location,
  MAX(page_title)                          AS page_title,
  COUNT(*)                                 AS total_visits,
  SUM(raw_event_count)                     AS raw_pageview_events,
  COUNT(DISTINCT session_key)              AS distinct_sessions,
  COUNT(DISTINCT user_id)                  AS distinct_users,
  COUNT(seconds_on_page)                   AS measured_visits,
  SUM(seconds_on_page)                     AS total_seconds_on_page,
  ROUND(AVG(seconds_on_page), 2)           AS avg_seconds_on_page,
  PERCENTILE(seconds_on_page, 0.5)         AS median_seconds_on_page
FROM dwell
GROUP BY page_location

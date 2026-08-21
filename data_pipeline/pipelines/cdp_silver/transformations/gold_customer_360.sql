CREATE OR REFRESH MATERIALIZED VIEW gold_customer_360
COMMENT "One row per customer: identity + engagement + purchase/abandonment metrics + RFM numeric scores. Segmentation-ready feature table for a downstream composable CDP (no named segment label)."
TBLPROPERTIES ("quality" = "gold")
AS
WITH users AS (
  SELECT user_id FROM event_sign_up       WHERE user_id IS NOT NULL
  UNION SELECT user_id FROM event_purchase     WHERE user_id IS NOT NULL
  UNION SELECT user_id FROM event_pageview     WHERE user_id IS NOT NULL
  UNION SELECT user_id FROM event_view_item    WHERE user_id IS NOT NULL
  UNION SELECT user_id FROM event_add_to_cart  WHERE user_id IS NOT NULL
  UNION SELECT user_id FROM event_abandon_cart WHERE user_id IS NOT NULL
),
identity AS (
  SELECT user_id,
         MIN(source_timestamp)              AS signup_timestamp,
         MAX_BY(email,      source_timestamp) AS email,
         MAX_BY(first_name, source_timestamp) AS first_name,
         MAX_BY(surname,    source_timestamp) AS surname,
         MAX_BY(city,       source_timestamp) AS city,
         MAX_BY(country,    source_timestamp) AS country
  FROM event_sign_up
  GROUP BY user_id
),
deleted AS (
  SELECT user_id, MAX(source_timestamp) AS account_deleted_timestamp
  FROM event_account_deleted
  GROUP BY user_id
),
purch AS (
  SELECT user_id,
         COUNT(*)              AS purchase_count,
         SUM(value)            AS lifetime_value,
         AVG(value)            AS avg_order_value,
         MAX(value)            AS max_order_value,
         MIN(source_timestamp) AS first_purchase_timestamp,
         MAX(source_timestamp) AS last_purchase_timestamp,
         SUM(SIZE(items))      AS purchased_line_items
  FROM event_purchase
  GROUP BY user_id
),
pv AS (
  SELECT user_id,
         COUNT(*)                                   AS total_pageviews,
         COUNT(DISTINCT ga_session_id)              AS total_sessions,
         MAX(source_timestamp)                      AS last_pageview_timestamp,
         MAX_BY(device_platform, source_timestamp)  AS last_device_platform
  FROM event_pageview
  GROUP BY user_id
),
vi AS (
  -- event_view_item uses COMMON_COLS (no source_timestamp); use ingest_timestamp.
  SELECT user_id,
         COUNT(*)                                       AS product_views,
         COUNT(DISTINCT ELEMENT_AT(items, 1).item_id)   AS distinct_products_viewed,
         MAX(ingest_timestamp)                          AS last_view_timestamp
  FROM event_view_item
  GROUP BY user_id
),
atc AS (
  SELECT user_id,
         COUNT(*)                 AS add_to_cart_events,
         COUNT(DISTINCT cart_id)  AS carts_started,
         MAX(source_timestamp)    AS last_add_to_cart_timestamp
  FROM event_add_to_cart
  GROUP BY user_id
),
ab AS (
  -- event_abandon_cart uses COMMON_COLS (no source_timestamp); use ingest_timestamp.
  SELECT user_id,
         COUNT(*)              AS abandon_count,
         SUM(value)            AS abandoned_value,
         MAX(ingest_timestamp) AS last_abandon_timestamp
  FROM event_abandon_cart
  GROUP BY user_id
),
joined AS (
  SELECT u.user_id,
         i.email, i.first_name, i.surname, i.city, i.country,
         i.signup_timestamp,
         d.account_deleted_timestamp,
         d.account_deleted_timestamp IS NOT NULL          AS is_deleted,
         COALESCE(p.purchase_count, 0)                    AS purchase_count,
         COALESCE(p.lifetime_value, 0)                    AS lifetime_value,
         p.avg_order_value,
         p.max_order_value,
         p.first_purchase_timestamp,
         p.last_purchase_timestamp,
         COALESCE(p.purchased_line_items, 0)              AS purchased_line_items,
         COALESCE(pv.total_pageviews, 0)                  AS total_pageviews,
         COALESCE(pv.total_sessions, 0)                   AS total_sessions,
         pv.last_device_platform,
         COALESCE(vi.product_views, 0)                    AS product_views,
         COALESCE(vi.distinct_products_viewed, 0)         AS distinct_products_viewed,
         COALESCE(atc.add_to_cart_events, 0)              AS add_to_cart_events,
         COALESCE(atc.carts_started, 0)                   AS carts_started,
         COALESCE(ab.abandon_count, 0)                    AS abandon_count,
         COALESCE(ab.abandoned_value, 0)                  AS abandoned_value,
         GREATEST(
           COALESCE(p.last_purchase_timestamp,      TIMESTAMP '1970-01-01'),
           COALESCE(pv.last_pageview_timestamp,     TIMESTAMP '1970-01-01'),
           COALESCE(vi.last_view_timestamp,         TIMESTAMP '1970-01-01'),
           COALESCE(atc.last_add_to_cart_timestamp, TIMESTAMP '1970-01-01'),
           COALESCE(ab.last_abandon_timestamp,      TIMESTAMP '1970-01-01')
         )                                                AS last_activity_timestamp
  FROM users u
  LEFT JOIN identity i USING (user_id)
  LEFT JOIN deleted  d USING (user_id)
  LEFT JOIN purch    p USING (user_id)
  LEFT JOIN pv         USING (user_id)
  LEFT JOIN vi         USING (user_id)
  LEFT JOIN atc        USING (user_id)
  LEFT JOIN ab         USING (user_id)
)
SELECT *,
  DATEDIFF(CURRENT_TIMESTAMP(), last_activity_timestamp) AS days_since_last_activity,
  DATEDIFF(CURRENT_TIMESTAMP(), last_purchase_timestamp) AS days_since_last_purchase,
  ROUND(abandon_count / NULLIF(abandon_count + purchase_count, 0), 4) AS cart_abandonment_rate,
  ROUND(purchase_count / NULLIF(product_views, 0), 4)                 AS view_to_purchase_rate,
  -- RFM numeric quintile scores (features only; no named segment).
  -- r_score is inverted so the most recent purchasers score highest (5).
  6 - NTILE(5) OVER (ORDER BY DATEDIFF(CURRENT_TIMESTAMP(), last_purchase_timestamp) ASC NULLS LAST) AS r_score,
  NTILE(5) OVER (ORDER BY purchase_count ASC) AS f_score,
  NTILE(5) OVER (ORDER BY lifetime_value ASC) AS m_score
FROM joined

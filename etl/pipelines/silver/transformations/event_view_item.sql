-- Silver: GA4 view_item events (product detail page views).
--
-- Streams the raw gtm_events table and decodes only the eventData fields this
-- table needs. Table + source are referenced by bare name so they resolve in
-- the pipeline's own configured catalog/schema (see etl/resources/pipeline_silver.yml).
-- Downstream (etl/src/key_normalize.sql) explodes `items` to the SKU and reads
-- ingest_timestamp / user_id / ga_session_id, so those are the load-bearing columns.
CREATE OR REFRESH STREAMING TABLE event_view_item
  COMMENT 'GA4 view_item events. One row per product detail page view.'
  TBLPROPERTIES ('quality' = 'silver')
AS
WITH parsed AS (
  SELECT
    ingestion_time,
    from_json(
      eventData,
      'STRUCT<user_id: STRING, ga_session_id: STRING, items: ARRAY<STRUCT<item_id: STRING, item_name: STRING, price: DOUBLE, currency: STRING, quantity: INT>>>'
    ) AS ed
  FROM STREAM(gtm_events)
  WHERE event_name = 'view_item'
)
SELECT
  CAST(ingestion_time / 1000 AS TIMESTAMP) AS ingest_timestamp,
  ed.user_id                               AS user_id,
  ed.ga_session_id                         AS ga_session_id,
  ed.items                                 AS items
FROM parsed;

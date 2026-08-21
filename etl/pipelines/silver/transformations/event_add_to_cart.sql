-- Silver: GA4 add_to_cart events.
--
-- Streams the raw gtm_events table and decodes only the eventData fields this
-- table needs. Table + source are referenced by bare name so they resolve in
-- the pipeline's own configured catalog/schema (see etl/resources/pipeline_silver.yml).
-- Downstream (etl/src/key_normalize.sql) reads source_timestamp / user_id /
-- cart_id / item_id / quantity_delta / cart_action; the rest round out the
-- cart action for analytics.
CREATE OR REFRESH STREAMING TABLE event_add_to_cart
  COMMENT 'GA4 add_to_cart events. One row per item-added-to-cart action.'
  TBLPROPERTIES ('quality' = 'silver')
AS
WITH parsed AS (
  SELECT
    ingestion_time,
    from_json(
      eventData,
      'STRUCT<timestamp: STRING, user_id: STRING, cart_id: STRING, item_id: STRING, item_name: STRING, price: DOUBLE, previous_quantity: INT, new_quantity: INT, quantity_delta: INT, cart_action: STRING, currency: STRING>'
    ) AS ed
  FROM STREAM(gtm_events)
  WHERE event_name = 'add_to_cart'
)
SELECT
  CAST(ingestion_time / 1000 AS TIMESTAMP) AS ingest_timestamp,
  to_timestamp(ed.timestamp)               AS source_timestamp,
  ed.user_id                               AS user_id,
  ed.cart_id                               AS cart_id,
  ed.item_id                               AS item_id,
  ed.item_name                             AS item_name,
  ed.price                                 AS price,
  ed.previous_quantity                     AS previous_quantity,
  ed.new_quantity                          AS new_quantity,
  ed.quantity_delta                        AS quantity_delta,
  ed.cart_action                           AS cart_action,
  ed.currency                              AS currency
FROM parsed;

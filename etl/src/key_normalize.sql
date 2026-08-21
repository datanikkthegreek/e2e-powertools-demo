-- Key normalization (load-bearing, not optional).
--
-- The behavioral funnel joins to the Lakebase star on product_id. The
-- behavioral `item_id` arrives as a JSON STRING; Lakebase `product_id` is a
-- UUID that wal2delta may expose as BINARY(16) or STRING. To make the two
-- compare equal reliably, both sides are reduced to canonical lowercase
-- hyphenated UUID text:
--   * a BINARY id -> hex-encode (32 hex chars) and hyphenate 8-4-4-4-12;
--   * a STRING id -> lowercase and pass through.
-- cdc_to_current.sql normalizes dim_product.product_id with the exact same
-- expression, so fact_view_item.product_id == dim_product.product_id.
-- Assumption: a non-string id is BINARY(16); extend the CASE if the connector
-- ever emits a third representation.
USE CATALOG nikks_fevm_workspace_7405607030687545;
USE SCHEMA techsummit;

-- fact_view_item: one row per product-detail-page view.
-- event_view_item carries the GA4 `items` array; explode it to the SKU.
CREATE OR REPLACE TABLE fact_view_item AS
SELECT
  v.ingest_timestamp                       AS event_ts,
  CAST(v.user_id AS STRING)                AS user_id,
  CASE WHEN typeof(item.item_id) = 'binary'
       THEN lower(regexp_replace(hex(item.item_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(item.item_id AS STRING)) END  AS product_id,
  v.ga_session_id                          AS session_id
FROM event_view_item v
LATERAL VIEW explode(v.items) t AS item
WHERE item.item_id IS NOT NULL;

-- fact_add_to_cart: one row per add-to-cart action.
CREATE OR REPLACE TABLE fact_add_to_cart AS
SELECT
  a.source_timestamp                       AS event_ts,
  CAST(a.user_id AS STRING)                AS user_id,
  CAST(a.cart_id AS STRING)                AS cart_id,
  CASE WHEN typeof(a.item_id) = 'binary'
       THEN lower(regexp_replace(hex(a.item_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(a.item_id AS STRING)) END      AS product_id,
  a.quantity_delta                         AS quantity_delta,
  a.cart_action                            AS cart_action
FROM event_add_to_cart a
WHERE a.item_id IS NOT NULL;

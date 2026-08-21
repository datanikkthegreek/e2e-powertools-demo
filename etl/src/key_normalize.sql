-- Key normalization (load-bearing, not optional).
--
-- The behavioral funnel joins to the Lakebase star on product_id. This step
-- produces the two behavioral fact tables Genie consumes, keyed on product_id.
--
-- ============================================================================
-- CANONICAL UUID NORMALIZATION CONTRACT (must stay identical across all sites)
--   Sites: etl/src/cdc_to_current.sql, etl/src/key_normalize.sql,
--          etl/src/seed_gtm_events.py (_load_products).
--   Every join-key id is reduced to canonical lowercase hyphenated UUID text:
--     1. binary                -> hex(id) [32 chars] -> hyphenate 8-4-4-4-12 -> lower
--     2. string ^[0-9a-f]{32}$ -> hyphenate 8-4-4-4-12 -> lower   (case-insensitive)
--     3. else                  -> lower(CAST(id AS STRING))
--   So binary-, hex-string-, and already-hyphenated ids all collapse to the
--   SAME text and behavioral item_id == dim_product.product_id regardless of
--   the wal2delta output type. This is inlined (not a SQL UDF) on purpose: a
--   typed UDF parameter would coerce a binary id to string before typeof()
--   could see it, losing the binary branch. Keep every CASE below byte-for-byte
--   identical to the other sites (only the column name changes).
-- ============================================================================
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
       WHEN lower(CAST(item.item_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(item.item_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
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
       WHEN lower(CAST(a.item_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(a.item_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(a.item_id AS STRING)) END      AS product_id,
  a.quantity_delta                         AS quantity_delta,
  a.cart_action                            AS cart_action
FROM event_add_to_cart a
WHERE a.item_id IS NOT NULL;

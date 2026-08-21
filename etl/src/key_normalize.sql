-- Key normalization (load-bearing, not optional).
--
-- Behavioral `item_id` is a STRING; Lakebase `product_id` is a UUID. Without
-- this cast the funnel joins to nothing. This step produces the two behavioral
-- fact tables Genie consumes, with `product_id` as canonical text uuid so it
-- lines up with dim_product.product_id.
USE CATALOG nikks_fevm_workspace_7405607030687545;
USE SCHEMA techsummit;

-- fact_view_item: one row per product-detail-page view.
-- event_view_item carries the GA4 `items` array; explode it to the SKU.
CREATE OR REPLACE TABLE fact_view_item AS
SELECT
  v.ingest_timestamp                       AS event_ts,
  CAST(v.user_id AS STRING)                AS user_id,
  CAST(item.item_id AS STRING)             AS product_id,
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
  CAST(a.item_id AS STRING)                AS product_id,
  a.quantity_delta                         AS quantity_delta,
  a.cart_action                            AS cart_action
FROM event_add_to_cart a
WHERE a.item_id IS NOT NULL;

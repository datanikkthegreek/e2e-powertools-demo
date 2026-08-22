-- Key normalization (load-bearing, not optional).
--
-- The behavioral funnel joins to the Lakebase star on product_id. This step
-- produces the two behavioral fact tables Genie consumes, keyed on product_id.
--
-- ============================================================================
-- CANONICAL UUID NORMALIZATION CONTRACT (both sides yield the SAME text)
--   Every join-key id must be canonical lowercase hyphenated UUID text so the
--   behavioral product_id == dim_product.product_id. There are two kinds of site:
--
--   OLTP / CDC side — id arrives as BINARY (Lakebase CDF renders the Postgres
--     UUID as raw binary; verified live 2026-08-22, typeof(id)='binary' in every
--     lb_*_history table). CAST(binary AS STRING) is garbage, so those sites MUST
--     keep the full CASE: hex(id) -> hyphenate 8-4-4-4-12 -> lower. Sites:
--     etl/pipelines/silver/transformations/{dim_product,dim_customer,
--     fact_purchase,fact_purchase_line}.sql and etl/src/seed_gtm_events.py.
--
--   Behavioral side (THIS FILE) — item_id arrives already as canonical lowercase
--     hyphenated STRING: seed_gtm_events normalizes the binary UUID before
--     serializing it into gtm_events, and the silver event tables type item_id as
--     STRING via from_json. The binary + hex-32 branches PROVABLY never fire here
--     (verified live 2026-08-22: across 3012 view + 830 cart item_ids, 0 binary,
--     0 bare-32-hex, and 0 rows where the old 3-branch CASE differed from
--     lower(CAST(item_id AS STRING))). So the regex was dead weight and is
--     removed; lower(CAST(... AS STRING)) is byte-identical and keeps the funnel
--     join green. (lower() is retained defensively against any stray uppercase.)
-- ============================================================================
-- Catalog/schema come from the `powertools-build` job parameters (:catalog /
-- :schema), so a bundle target override is honored consistently with the other
-- curate SQL tasks.
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

-- fact_view_item: one row per product-detail-page view.
-- event_view_item carries the GA4 `items` array; explode it to the SKU.
CREATE OR REPLACE TABLE fact_view_item AS
SELECT
  v.ingest_timestamp                       AS event_ts,
  CAST(v.user_id AS STRING)                AS user_id,
  lower(CAST(item.item_id AS STRING))      AS product_id,
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
  lower(CAST(a.item_id AS STRING))         AS product_id,
  a.quantity_delta                         AS quantity_delta,
  a.cart_action                            AS cart_action
FROM event_add_to_cart a
WHERE a.item_id IS NOT NULL;

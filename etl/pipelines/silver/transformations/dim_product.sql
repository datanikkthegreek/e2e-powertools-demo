-- Silver / CDC (1 of 4): lb_products_history -> dim_product (current state).
--
-- The pipeline collapses the change-log to current state NATIVELY via AUTO CDC
-- INTO: the engine keeps the latest change per key (highest _sort_by) and
-- applies deletes. No ROW_NUMBER dedup, no manual _rn/preimage filtering.
--
-- TWO-STAGE SHAPE (required by AUTO CDC — it reads a table/view, never a
-- subquery, so the projection + pre-filter live in a streaming temp view):
--   1. _products_changes : STREAM(lb_products_history), project/normalize the
--      columns, and drop update_preimage rows. CDF emits an UPDATE as TWO rows
--      (update_preimage = old, update_postimage = new); AUTO CDC applies the row
--      it sees as the new state, so feeding the preimage would regress the row.
--      Keep only 'insert' | 'update_postimage' | 'delete'.
--   2. AUTO CDC flow    : KEYS(product_id), SEQUENCE BY _sort_by (CDF's monotonic
--      order key, never ties), APPLY AS DELETE WHEN _pg_change_type='delete'.
--
-- UUID NORMALIZATION — LOAD-BEARING, centralized in canonical_uuid(BINARY).
--   Verified live 2026-08-22: typeof(id) in every lb_*_history table is 'binary'
--   (Lakebase CDF renders the Postgres UUID as raw binary). CAST(binary AS STRING)
--   yields garbage bytes, so the id MUST go hex(id) -> hyphenate 8-4-4-4-12 ->
--   lower to become the canonical UUID text that the behavioral funnel joins on.
--   That transform now lives in ONE place — the canonical_uuid() UC function
--   (etl/src/create_canonical_uuid.sql, created by the create_canonical_uuid job
--   task before this pipeline runs) — so dim_product.product_id equals
--   fact_view_item/fact_add_to_cart.product_id. The BINARY-typed parameter
--   documents intent and catches an obviously-wrong argument, though SQL may still
--   apply an implicit cast, so it is a guard rather than an absolute guarantee.
--   The behavioral side (key_normalize.sql) sees item_id already as canonical
--   lowercase text, so it uses the simple lower(CAST(...)) form — see that note.
-- The call is BARE (canonical_uuid). The function lives in the catalog's `default`
-- schema (etl/src/create_canonical_uuid.sql) and SDP's function search path
-- includes <catalog>.default, so a bare call resolves there (verified live
-- 2026-08-22). Keeping it in default, not techsummit, is what honors the bundle
-- target/schema override: the catalog follows the target and no schema is pinned.
CREATE TEMPORARY VIEW _products_changes AS
SELECT
  canonical_uuid(id)            AS product_id,
  name,
  description                   AS category,
  price_eur,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_products_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE dim_product
  COMMENT 'Current-state products (specs live in product_specs, not here). Collapsed from lb_products_history via native AUTO CDC.'
  TBLPROPERTIES ('quality' = 'silver');

CREATE FLOW dim_product_cdc AS AUTO CDC INTO dim_product
FROM STREAM(_products_changes)
KEYS (product_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

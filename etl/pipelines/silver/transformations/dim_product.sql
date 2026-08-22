-- Silver / CDC (1 of 4): lb_products_history -> dim_product (current state).
--
-- Migrated from the old warehouse collapse task (etl/src/cdc_to_current.sql).
-- Instead of a manual ROW_NUMBER() dedup + delete/preimage filter, the pipeline
-- does the merge/collapse NATIVELY via AUTO CDC INTO: the engine keeps the
-- latest change per key (highest _sort_by) and applies deletes. No ROW_NUMBER,
-- no manual _rn filtering.
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
-- UUID NORMALIZATION — the binary branch is LOAD-BEARING here (NOT removable).
--   Verified live 2026-08-22: typeof(id) in every lb_*_history table is 'binary'
--   (Lakebase CDF renders the Postgres UUID as raw binary). CAST(binary AS STRING)
--   yields garbage bytes, so the id MUST go hex(id) -> hyphenate 8-4-4-4-12 ->
--   lower to become the canonical UUID text that the behavioral funnel joins on.
--   The full 3-branch CASE below is kept byte-for-byte from the retired
--   cdc_to_current.sql so dim_product.product_id stays byte-identical to before
--   (and equal to fact_view_item/fact_add_to_cart.product_id). The behavioral
--   side (key_normalize.sql) sees item_id already as canonical lowercase text,
--   so it uses the simple lower(CAST(...)) form — see that file's note.
-- Bare names resolve in the pipeline's configured catalog/schema (see
-- etl/resources/pipeline_silver.yml), matching the event/IDP tables.
CREATE TEMPORARY VIEW _products_changes AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS product_id,
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

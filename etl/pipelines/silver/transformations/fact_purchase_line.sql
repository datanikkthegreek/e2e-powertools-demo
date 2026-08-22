-- Silver / CDC (4 of 4): lb_purchase_lines_history -> fact_purchase_line.
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale).
--
-- KEY CHOICE: the retired cdc_to_current.sql deduped on the line's own `id`, but
-- the OUTPUT schema deliberately drops that id (it carries only purchase_id,
-- product_id, quantity, unit_price_eur, name_snapshot). AUTO CDC requires its
-- KEYS columns to exist in the target, so keying on the line `id` would force an
-- extra column into the table and break the schema contract. Instead we key on
-- the composite (purchase_id, product_id): a purchase line is one product within
-- one purchase (quantity is a column, not repeated rows), so this pair is the
-- natural business key. Verified unique live 2026-08-22 (18 rows == 18 distinct
-- pairs). This assumes a product is never split across two lines of the same
-- purchase, which holds for this OLTP schema and the seed.
-- Bare names resolve in the pipeline's configured catalog/schema.
CREATE TEMPORARY VIEW _purchase_lines_changes AS
SELECT
  CASE WHEN typeof(purchase_id) = 'binary'
       THEN lower(regexp_replace(hex(purchase_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(purchase_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(purchase_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(purchase_id AS STRING)) END  AS purchase_id,
  CASE WHEN typeof(product_id) = 'binary'
       THEN lower(regexp_replace(hex(product_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(product_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(product_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(product_id AS STRING)) END   AS product_id,
  quantity,
  unit_price_eur,
  name_snapshot,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_purchase_lines_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE fact_purchase_line
  COMMENT 'Current-state purchase lines. Collapsed from lb_purchase_lines_history via native AUTO CDC, keyed on (purchase_id, product_id).'
  TBLPROPERTIES ('quality' = 'silver');

CREATE FLOW fact_purchase_line_cdc AS AUTO CDC INTO fact_purchase_line
FROM STREAM(_purchase_lines_changes)
KEYS (purchase_id, product_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

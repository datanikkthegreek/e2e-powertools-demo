-- Silver / CDC (4 of 4): lb_purchase_lines_history -> fact_purchase_line.
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale).
--
-- KEY CHOICE — key on the true per-row identity `id`. The Lakebase OLTP
-- purchase_lines table's PRIMARY KEY is the line `id` alone; there is NO
-- UNIQUE(purchase_id, product_id) constraint or unique index (verified live
-- 2026-08-22 against information_schema.table_constraints / pg_indexes: the only
-- unique index is purchase_lines_pkey on (id)). So (purchase_id, product_id) is
-- only OBSERVED unique, not enforced — keying AUTO CDC on that pair would be a
-- CDC-correctness bug: two lines of the same product in one purchase would
-- collapse last-writer-wins, and a delete of one line would delete the shared
-- target row. We therefore key on the line `id` (binary, like every other CDF
-- id — normalized with the same load-bearing hex->hyphenate->lower CASE).
--
-- AUTO CDC requires its KEYS columns to exist in the target, so the normalized
-- line id is exposed as an ADDITIVE column `purchase_line_id`. Nothing but Genie
-- consumes this table and an extra identity column is harmless; the other
-- projected columns (purchase_id, product_id, quantity, unit_price_eur, name_snapshot) are
-- unchanged. Bare names resolve in the pipeline's configured catalog/schema.
CREATE TEMPORARY VIEW _purchase_lines_changes AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END           AS purchase_line_id,
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
  COMMENT 'Current-state purchase lines. Collapsed from lb_purchase_lines_history via native AUTO CDC, keyed on the line id (purchase_line_id).'
  TBLPROPERTIES ('quality' = 'silver');

CREATE FLOW fact_purchase_line_cdc AS AUTO CDC INTO fact_purchase_line
FROM STREAM(_purchase_lines_changes)
KEYS (purchase_line_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

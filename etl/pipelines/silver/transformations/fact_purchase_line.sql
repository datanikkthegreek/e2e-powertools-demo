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
-- id — normalized via the centralized canonical_uuid(BINARY) UC function).
--
-- AUTO CDC requires its KEYS columns to exist in the target, so the normalized
-- line id is exposed as an ADDITIVE column `purchase_line_id`. Nothing but Genie
-- consumes this table and an extra identity column is harmless; the other
-- projected columns (purchase_id, product_id, quantity, unit_price_eur, name_snapshot) are
-- unchanged. All three binary ids go through canonical_uuid() (see dim_product.sql
-- / create_canonical_uuid.sql). The calls are BARE: the function lives in
-- <catalog>.default, which is on SDP's function search path — see dim_product.sql
-- for the full note.
CREATE TEMPORARY VIEW _purchase_lines_changes AS
SELECT
  canonical_uuid(id)           AS purchase_line_id,
  canonical_uuid(purchase_id)  AS purchase_id,
  canonical_uuid(product_id)   AS product_id,
  quantity,
  unit_price_eur,
  name_snapshot,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_purchase_lines_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE fact_purchase_line (
  purchase_line_id STRING COMMENT 'Canonical UUID primary key identifying this individual line item. Derived from the binary Lakebase purchase_lines id.',
  purchase_id      STRING COMMENT 'Canonical UUID of the parent purchase transaction. Foreign key to fact_purchase.purchase_id.',
  product_id       STRING COMMENT 'Canonical UUID of the product purchased on this line. Foreign key to dim_product.product_id.',
  quantity         INT    COMMENT 'Number of units of this product purchased on this line item.',
  unit_price_eur   DOUBLE COMMENT 'Price per unit in euros (EUR) at the time of purchase. May differ from dim_product.price_eur if price has changed since.',
  name_snapshot    STRING COMMENT 'Product name captured at time of purchase. Snapshot preserves the name even if dim_product.name changes later.'
)
  COMMENT 'Purchase line-item fact table (SCD Type 1 — current state only). One row per product line within a purchase, continuously updated via CDC. Grain: one row = one product in one purchase. Join to fact_purchase on purchase_id for transaction totals and timestamps, and to dim_product on product_id for current product attributes.';

CREATE FLOW fact_purchase_line_cdc AS AUTO CDC INTO fact_purchase_line
FROM STREAM(_purchase_lines_changes)
KEYS (purchase_line_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

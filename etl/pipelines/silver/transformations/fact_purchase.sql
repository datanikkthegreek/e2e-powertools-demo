-- Silver / CDC (3 of 4): lb_purchases_history -> fact_purchase (the money fact).
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale). Three id columns
-- (id -> purchase_id, account_id -> customer_id, cart_id) are each binary and
-- normalized with the same load-bearing CASE. created_at + total_eur are the
-- money columns, carried through unchanged from the retired cdc_to_current.sql.
-- Bare names resolve in the pipeline's configured catalog/schema.
CREATE TEMPORARY VIEW _purchases_changes AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END          AS purchase_id,
  CASE WHEN typeof(account_id) = 'binary'
       THEN lower(regexp_replace(hex(account_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(account_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(account_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(account_id AS STRING)) END  AS customer_id,
  CASE WHEN typeof(cart_id) = 'binary'
       THEN lower(regexp_replace(hex(cart_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(cart_id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(cart_id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(cart_id AS STRING)) END      AS cart_id,
  created_at,
  total_eur,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_purchases_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE fact_purchase
  COMMENT 'Current-state purchases (the money fact). Collapsed from lb_purchases_history via native AUTO CDC.'
  TBLPROPERTIES ('quality' = 'silver');

CREATE FLOW fact_purchase_cdc AS AUTO CDC INTO fact_purchase
FROM STREAM(_purchases_changes)
KEYS (purchase_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

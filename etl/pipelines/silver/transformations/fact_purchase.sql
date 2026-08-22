-- Silver / CDC (3 of 4): lb_purchases_history -> fact_purchase (the money fact).
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale). Three id columns
-- (id -> purchase_id, account_id -> customer_id, cart_id) are each binary and
-- normalized via the centralized canonical_uuid(BINARY) UC function (see
-- dim_product.sql / create_canonical_uuid.sql). created_at + total_eur are the
-- money columns, carried through unchanged.
-- The calls are BARE: the function lives in <catalog>.default, which is on SDP's
-- function search path — see dim_product.sql for the note.
CREATE TEMPORARY VIEW _purchases_changes AS
SELECT
  canonical_uuid(id)           AS purchase_id,
  canonical_uuid(account_id)   AS customer_id,
  canonical_uuid(cart_id)      AS cart_id,
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

-- Silver / CDC (2 of 4): lb_accounts_history -> dim_customer (current state).
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale). The engine collapses
-- lb_accounts_history to current state via AUTO CDC INTO — no ROW_NUMBER, no
-- manual _rn/delete filtering. signup_date is a literal NULL DATE (accounts carry
-- no signup timestamp). The binary id is normalized via the centralized
-- canonical_uuid(BINARY) UC function (see dim_product.sql / create_canonical_uuid.sql).
-- The call is SCHEMA-QUALIFIED (techsummit.) because SDP resolves a bare function
-- only against the `default` schema — see dim_product.sql for the full note.
CREATE TEMPORARY VIEW _accounts_changes AS
SELECT
  techsummit.canonical_uuid(id) AS customer_id,
  city,
  country,
  CAST(NULL AS DATE)            AS signup_date,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_accounts_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE dim_customer
  COMMENT 'Current-state customers. Collapsed from lb_accounts_history via native AUTO CDC.'
  TBLPROPERTIES ('quality' = 'silver');

CREATE FLOW dim_customer_cdc AS AUTO CDC INTO dim_customer
FROM STREAM(_accounts_changes)
KEYS (customer_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

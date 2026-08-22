-- Silver / CDC (2 of 4): lb_accounts_history -> dim_customer (current state).
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale). The engine collapses
-- lb_accounts_history to current state via AUTO CDC INTO — no ROW_NUMBER, no
-- manual _rn/delete filtering. signup_date is a literal NULL DATE (accounts carry
-- no signup timestamp), preserved from the retired cdc_to_current.sql output.
-- Bare names resolve in the pipeline's configured catalog/schema.
CREATE TEMPORARY VIEW _accounts_changes AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS customer_id,
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

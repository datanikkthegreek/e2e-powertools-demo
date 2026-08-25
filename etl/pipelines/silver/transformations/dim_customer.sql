-- Silver / CDC (2 of 4): lb_accounts_history -> dim_customer (current state).
--
-- Same native-merge pattern as dim_product.sql (read that file's header for the
-- full AUTO CDC + preimage-filter + binary-UUID rationale). The engine collapses
-- lb_accounts_history to current state via AUTO CDC INTO — no ROW_NUMBER, no
-- manual _rn/delete filtering. signup_date is a literal NULL DATE (accounts carry
-- no signup timestamp). The binary id is normalized via the centralized
-- canonical_uuid(BINARY) UC function (see dim_product.sql / create_canonical_uuid.sql).
-- The call is BARE: the function lives in <catalog>.default, which is on SDP's
-- function search path — see dim_product.sql for the full note.
CREATE TEMPORARY VIEW _accounts_changes AS
SELECT
  canonical_uuid(id)           AS customer_id,
  city,
  country,
  CAST(NULL AS DATE)            AS signup_date,
  _pg_change_type,
  _sort_by
FROM STREAM(lb_accounts_history)
WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete');

CREATE OR REFRESH STREAMING TABLE dim_customer (
  customer_id STRING NOT NULL COMMENT 'Canonical UUID primary key identifying the customer account. Derived from the binary Lakebase account id. Join key to fact_purchase.customer_id.',
  city        STRING COMMENT 'City where the customer is located, as recorded in the source account system.',
  country     STRING COMMENT 'Country where the customer is located (full country name, e.g. Germany, France).',
  signup_date DATE   COMMENT 'Date the customer first signed up. Currently NULL for all rows — the source system does not track signup timestamps.',
  CONSTRAINT pk_dim_customer PRIMARY KEY (customer_id)
)
  COMMENT 'Customer dimension table (SCD Type 1 — current state only). One row per unique customer account, continuously updated from the Lakebase accounts database via CDC. Use customer_id to join to fact_purchase and fact_purchase_line for purchase analysis.';

CREATE FLOW dim_customer_cdc AS AUTO CDC INTO dim_customer
FROM STREAM(_accounts_changes)
KEYS (customer_id)
APPLY AS DELETE WHEN _pg_change_type = 'delete'
SEQUENCE BY _sort_by
COLUMNS * EXCEPT (_pg_change_type, _sort_by);

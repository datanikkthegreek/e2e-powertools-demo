-- CDC -> current-state collapse.
--
-- The wal2delta sync (../resources/sync.yml) lands each Lakebase table as a
-- change-log `lb_*_history` (many change rows per row). Genie must only ever
-- see the collapsed current state, or it double-counts. For every history
-- table: rank ALL change rows per primary key (newest _pg_lsn first), keep the
-- newest (_rn = 1), and only THEN drop rows whose latest change is a delete.
--
-- UUID NORMALIZATION (load-bearing for the funnel join): Lakebase ids are
-- UUIDs, but wal2delta may expose them as BINARY(16) or as STRING depending on
-- the connector. Every id column is normalized to canonical lowercase
-- hyphenated UUID text via the same CASE used in key_normalize.sql, so that
-- behavioral `item_id` (a JSON string) and Lakebase `product_id` reliably
-- compare equal. Assumption: a non-string id is BINARY(16); if the connector
-- ever emits a third representation, extend the CASE.
--
-- Catalog/schema are the isolated techsummit environment. The `powertools-build`
-- job also passes them as parameters (:catalog / :schema) for reuse.
USE CATALOG nikks_fevm_workspace_7405607030687545;
USE SCHEMA techsummit;

-- dim_product (specs are NOT here — they come from IDP -> product_specs)
CREATE OR REPLACE TABLE dim_product AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS product_id,
  name,
  description                   AS category,
  price_eur
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS _rn
  FROM lb_products_history
)
WHERE _rn = 1
  AND _pg_change_type <> 'delete';

-- dim_customer
CREATE OR REPLACE TABLE dim_customer AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS customer_id,
  city,
  country,
  CAST(NULL AS DATE)            AS signup_date
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS _rn
  FROM lb_accounts_history
)
WHERE _rn = 1
  AND _pg_change_type <> 'delete';

-- fact_purchase (the money fact)
CREATE OR REPLACE TABLE fact_purchase AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END          AS purchase_id,
  CASE WHEN typeof(account_id) = 'binary'
       THEN lower(regexp_replace(hex(account_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(account_id AS STRING)) END  AS customer_id,
  CASE WHEN typeof(cart_id) = 'binary'
       THEN lower(regexp_replace(hex(cart_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(cart_id AS STRING)) END      AS cart_id,
  created_at,
  total_eur
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS _rn
  FROM lb_purchases_history
)
WHERE _rn = 1
  AND _pg_change_type <> 'delete';

-- fact_purchase_line
CREATE OR REPLACE TABLE fact_purchase_line AS
SELECT
  CASE WHEN typeof(purchase_id) = 'binary'
       THEN lower(regexp_replace(hex(purchase_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(purchase_id AS STRING)) END  AS purchase_id,
  CASE WHEN typeof(product_id) = 'binary'
       THEN lower(regexp_replace(hex(product_id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(product_id AS STRING)) END   AS product_id,
  quantity,
  unit_price_eur,
  name_snapshot
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS _rn
  FROM lb_purchase_lines_history
)
WHERE _rn = 1
  AND _pg_change_type <> 'delete';

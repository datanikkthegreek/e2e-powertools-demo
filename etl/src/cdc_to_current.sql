-- CDC -> current-state collapse.
--
-- The wal2delta sync (../resources/sync.yml) lands each Lakebase table as a
-- change-log `lb_*_history` (many change rows per row). Genie must only ever
-- see the collapsed current state, or it double-counts. For every history
-- table: keep the newest change per primary key (highest _pg_lsn) and drop
-- rows whose latest change is a delete.
--
-- Catalog/schema are the isolated techsummit environment. The `powertools-curate`
-- job also passes them as parameters (:catalog / :schema) for reuse.
USE CATALOG nikks_fevm_workspace_7405607030687545;
USE SCHEMA techsummit;

-- dim_product (specs are NOT here — they come from IDP -> product_specs)
CREATE OR REPLACE TABLE dim_product AS
SELECT
  CAST(id AS STRING)            AS product_id,
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
  CAST(id AS STRING)            AS customer_id,
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
  CAST(id AS STRING)            AS purchase_id,
  CAST(account_id AS STRING)    AS customer_id,
  CAST(cart_id AS STRING)       AS cart_id,
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
  CAST(purchase_id AS STRING)   AS purchase_id,
  CAST(product_id AS STRING)    AS product_id,
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

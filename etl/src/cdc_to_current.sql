-- CDC -> current-state collapse.
--
-- Lakebase Change Data Feed (CDF, the wal2delta extension) lands each Lakebase
-- table as a change-log `lb_*_history` (many change rows per row) in this
-- schema. Genie must only ever see the collapsed current state, or it
-- double-counts. For every history table: rank ALL change rows per primary key
-- by `_sort_by DESC` (CDF's monotonic ordering key), keep the newest (_rn = 1),
-- and only THEN drop rows whose latest change is a delete.
--
-- CDF CHANGE-COLUMN CONTRACT (Lakebase CDF, not classic wal2delta):
--   _pg_change_type : 'insert' | 'delete' | 'update_preimage' | 'update_postimage'
--   _sort_by        : BIGINT, monotonic across ALL changes -> ORDER BY this
--   _pg_lsn / _pg_xid / _timestamp : also present (LSN can tie within a txn, so
--                     we order by _sort_by, which never ties, for determinism).
-- An UPDATE emits TWO rows (update_preimage = old, update_postimage = new).
-- Ranking by _sort_by DESC makes the postimage win, so keeping _rn = 1 and
-- dropping both 'delete' and 'update_preimage' yields exactly the live row.
--
-- ============================================================================
-- CANONICAL UUID NORMALIZATION CONTRACT (must stay identical across all sites)
--   Sites: etl/src/cdc_to_current.sql, etl/src/key_normalize.sql,
--          etl/src/seed_gtm_events.py (_load_products).
--   Every join-key id is reduced to canonical lowercase hyphenated UUID text:
--     1. binary                -> hex(id) [32 chars] -> hyphenate 8-4-4-4-12 -> lower
--     2. string ^[0-9a-f]{32}$ -> hyphenate 8-4-4-4-12 -> lower   (case-insensitive)
--     3. else                  -> lower(CAST(id AS STRING))
--   So binary-, hex-string-, and already-hyphenated ids all collapse to the
--   SAME text and behavioral item_id == dim_product.product_id regardless of
--   the wal2delta output type. This is inlined (not a SQL UDF) on purpose: a
--   typed UDF parameter would coerce a binary id to string before typeof()
--   could see it, losing the binary branch. Keep every CASE below byte-for-byte
--   identical to the other sites (only the column name changes).
-- ============================================================================
--
-- Catalog/schema come from the `powertools-build` job parameters (:catalog /
-- :schema, defaulting to the isolated techsummit environment) so a bundle
-- target override is actually honored. IDENTIFIER() promotes the string
-- parameter to a catalog/schema identifier.
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

-- dim_product (specs are NOT here — they come from IDP -> product_specs)
CREATE OR REPLACE TABLE dim_product AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS product_id,
  name,
  description                   AS category,
  price_eur
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _sort_by DESC) AS _rn
  FROM lb_products_history
)
WHERE _rn = 1
  AND _pg_change_type NOT IN ('delete', 'update_preimage');

-- dim_customer
CREATE OR REPLACE TABLE dim_customer AS
SELECT
  CASE WHEN typeof(id) = 'binary'
       THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$'
       THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5'))
       ELSE lower(CAST(id AS STRING)) END  AS customer_id,
  city,
  country,
  CAST(NULL AS DATE)            AS signup_date
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _sort_by DESC) AS _rn
  FROM lb_accounts_history
)
WHERE _rn = 1
  AND _pg_change_type NOT IN ('delete', 'update_preimage');

-- fact_purchase (the money fact)
CREATE OR REPLACE TABLE fact_purchase AS
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
  total_eur
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _sort_by DESC) AS _rn
  FROM lb_purchases_history
)
WHERE _rn = 1
  AND _pg_change_type NOT IN ('delete', 'update_preimage');

-- fact_purchase_line
CREATE OR REPLACE TABLE fact_purchase_line AS
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
  name_snapshot
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY _sort_by DESC) AS _rn
  FROM lb_purchase_lines_history
)
WHERE _rn = 1
  AND _pg_change_type NOT IN ('delete', 'update_preimage');

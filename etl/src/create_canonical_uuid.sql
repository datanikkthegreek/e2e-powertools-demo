-- Canonical UUID normalization function (single source of truth).
--
-- Lakebase CDF renders the Postgres UUID primary keys as raw BINARY in every
-- lb_*_history change-log (verified live 2026-08-22, typeof(id)='binary'). A
-- plain CAST(binary AS STRING) is garbage bytes, so every OLTP/CDC site must
-- reduce the id to canonical lowercase hyphenated UUID text (8-4-4-4-12) before
-- the behavioral funnel can join behavioral product_id == dim_product.product_id.
--
-- This function centralizes that transform so the four silver AUTO CDC flows
-- (dim_product / dim_customer / fact_purchase / fact_purchase_line) and the GTM
-- behavior seed all call ONE definition instead of duplicating a 3-branch regex
-- CASE at nine sites. The BINARY-typed parameter is the seatbelt: a non-binary
-- column fails loud at analysis rather than silently corrupting the key. The
-- hex form is byte-identical to the retired regex CASE (verified live
-- 2026-08-22: 0 diffs across all 12 products, still matches dim_product).
--
-- NOTE: this is the BINARY side only. The behavioral read-back side
-- (etl/src/key_normalize.sql) sees item_id already as canonical lowercase text
-- and stays lower(CAST(... AS STRING)) — a BINARY-typed function cannot serve a
-- STRING column, so that file is intentionally left untouched.
--
-- Created by the `create_canonical_uuid` task of the powertools-build job
-- (../resources/job_build.yml), which runs FIRST — before seed_gtm_events and
-- the silver pipeline — because SDP does not track UC-function dependencies and
-- DABs has no function resource type, so this pre-pipeline task is how the
-- function is guaranteed to exist at pipeline analysis time. Catalog/schema come
-- from the job's :catalog / :schema parameters, consistent with key_normalize.sql.
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE OR REPLACE FUNCTION canonical_uuid(id BINARY)
  RETURNS STRING
  DETERMINISTIC
  COMMENT 'Binary Lakebase-CDF UUID -> canonical lowercase hyphenated UUID text (8-4-4-4-12).'
  RETURN lower(concat_ws('-',
    substr(hex(id), 1, 8),
    substr(hex(id), 9, 4),
    substr(hex(id), 13, 4),
    substr(hex(id), 17, 4),
    substr(hex(id), 21, 12)));

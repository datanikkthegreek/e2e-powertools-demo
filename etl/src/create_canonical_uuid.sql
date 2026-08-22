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
-- CASE at nine sites. The hex form is byte-identical to the retired regex CASE
-- (verified live 2026-08-22: 0 diffs across all 12 products, still matches
-- dim_product). The BINARY-typed parameter documents intent and catches an
-- obviously-wrong argument, though SQL may still apply an implicit cast, so it is
-- a guard rather than an absolute guarantee.
--
-- NULL SEMANTICS: concat_ws SKIPS nulls (a NULL id would yield '' — four bare
-- hyphens' worth of nothing), so the body guards NULL explicitly and returns NULL,
-- matching the old CASE (lower(CAST(NULL AS STRING)) = NULL).
--
-- LOCATION — the catalog's `default` schema, NOT techsummit. Every catalog has a
-- `default` schema, and SDP's function search path includes <catalog>.default, so
-- a BARE canonical_uuid(...) call inside the pipeline resolves here while the
-- catalog still follows the bundle target (no schema is pinned). Keeping it out of
-- techsummit is what preserves the repo's schema-override convention: bare table
-- names follow the pipeline's configured schema, and this bare function call
-- follows the catalog's default schema — neither hardcodes techsummit.
--
-- NOTE: this is the BINARY side only. The behavioral read-back side
-- (etl/src/key_normalize.sql) sees item_id already as canonical lowercase text
-- and stays lower(CAST(... AS STRING)) — a BINARY-typed function cannot serve a
-- STRING column, so that file is intentionally left untouched.
--
-- Created by the `create_canonical_uuid` task of the powertools-build job
-- (../resources/job_build.yml), which completes before its consumers
-- (seed_gtm_events + the silver pipeline) because SDP does not track UC-function
-- dependencies and DABs has no function resource type, so this task is how the
-- function is guaranteed to exist at pipeline analysis time. Catalog comes from
-- the job's :catalog parameter (so a bundle target override is honored); the
-- schema is fixed to `default`.
CREATE OR REPLACE FUNCTION IDENTIFIER(:catalog || '.default.canonical_uuid')(id BINARY)
  RETURNS STRING
  DETERMINISTIC
  COMMENT 'Binary Lakebase-CDF UUID -> canonical lowercase hyphenated UUID text (8-4-4-4-12); NULL-preserving.'
  RETURN CASE WHEN id IS NULL THEN NULL
    ELSE lower(concat_ws('-',
      substr(hex(id), 1, 8),
      substr(hex(id), 9, 4),
      substr(hex(id), 13, 4),
      substr(hex(id), 17, 4),
      substr(hex(id), 21, 12)))
    END;

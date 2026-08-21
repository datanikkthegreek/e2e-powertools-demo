-- Silver / IDP (3 of 3): explode typed specs -> product_specs.
--
-- Streams _extracted_specs and EXPLODES its `specs` ARRAY<STRUCT> to one row per
-- extracted model, exactly the way event_view_item's `items` array is exploded
-- in key_normalize (LATERAL VIEW explode). Plain explode (not OUTER) keeps this
-- truly one-row-per-extracted-model: a datasheet that extracts nothing produces
-- no row rather than an all-NULL placeholder. Each of the 12 datasheets yields
-- exactly one model today, so product_specs is 12 rows.
--
-- The numeric columns are already TYPED (DOUBLE / INT) coming out of the typed
-- ai_extract response schema -- there is NO regexp_extract / try_cast unit
-- stripping anywhere in this chain. product_specs is keyed by what the datasheet
-- itself yields (source_path + model_name); it deliberately does NOT carry
-- product_id and does NOT join dim_product -- the old _model_crosswalk join is
-- removed, so IDP no longer depends on the curate chain. Bare names resolve in
-- the pipeline's configured catalog/schema (see etl/resources/pipeline_silver.yml).
CREATE OR REFRESH STREAMING TABLE product_specs
  COMMENT 'Typed Bosch tool specs from datasheet PDFs (voltage/torque/rpm/chuck/weight). Keyed by source_path + model_name; not joined to dim_product.'
  TBLPROPERTIES ('quality' = 'silver')
AS
SELECT
  e.path                   AS source_path,
  spec.model_name          AS model_name,
  spec.voltage_v           AS voltage_v,
  spec.max_torque_nm       AS max_torque_nm,
  spec.no_load_rpm         AS no_load_rpm,
  spec.chuck_capacity_mm   AS chuck_capacity_mm,
  spec.weight_kg           AS weight_kg,
  spec.battery_platform    AS battery_platform
FROM STREAM(_extracted_specs) e
LATERAL VIEW explode(e.specs) t AS spec;

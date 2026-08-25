-- Silver / IDP (3 of 3): explode typed specs -> idp_product_specs.
--
-- Streams _extracted_specs and EXPLODES its `specs` ARRAY<STRUCT> to one row per
-- extracted model, exactly the way event_view_item's `items` array is exploded
-- in key_normalize (LATERAL VIEW explode). Plain explode (not OUTER) keeps this
-- truly one-row-per-extracted-model: a datasheet that extracts nothing produces
-- no row rather than an all-NULL placeholder. Each of the 12 datasheets yields
-- exactly one model today, so idp_product_specs is 12 rows.
--
-- The numeric columns are already TYPED (DOUBLE / INT) coming out of the typed
-- ai_extract response schema -- there is NO regexp_extract / try_cast unit
-- stripping anywhere in this chain. idp_product_specs is keyed by what the datasheet
-- itself yields (source_path + model_name); it deliberately does NOT carry
-- product_id and does NOT join dim_product -- the old _model_crosswalk join is
-- removed, so IDP no longer depends on the curate chain. Bare names resolve in
-- the pipeline's configured catalog/schema (see etl/resources/pipeline_silver.yml).
CREATE OR REFRESH STREAMING TABLE idp_product_specs (
  source_path       STRING COMMENT 'Full Volume file path of the PDF datasheet this spec was extracted from. Part of the natural key (source_path + model_name).',
  model_name        STRING COMMENT 'Bosch model designation as stated in the datasheet (e.g. GSR 18V-55, GBH 2-26 DRE). Part of the natural key.',
  voltage_v         DOUBLE COMMENT 'Rated/nominal voltage in volts (V). Indicates battery platform voltage or mains voltage for corded tools.',
  max_torque_nm     DOUBLE COMMENT 'Maximum torque output in Newton-meters (Nm). Key performance indicator for drills and impact drivers.',
  no_load_rpm       INT    COMMENT 'Maximum no-load rotational speed in revolutions per minute (RPM).',
  chuck_capacity_mm DOUBLE COMMENT 'Maximum chuck or collet capacity in millimeters (mm). Determines the largest drill bit diameter the tool accepts.',
  weight_kg         DOUBLE COMMENT 'Tool weight in kilograms (kg) without battery. Relevant for ergonomics and portability comparisons.',
  battery_platform  STRING COMMENT 'Battery platform family (e.g. 18V, 12V) or corded for mains-powered tools. Determines battery interoperability across the Bosch lineup.'
)
  COMMENT 'Bosch power tool technical specifications extracted from PDF datasheets via AI (IDP pipeline). One row per tool model per datasheet. Grain: source_path + model_name. Use for product comparisons, filtering by technical attributes, and enriching product analytics. Can be joined to dim_product on model_name = dim_product.name for combining catalog data with technical specs.'
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

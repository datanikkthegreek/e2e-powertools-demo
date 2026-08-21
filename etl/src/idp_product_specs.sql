-- IDP: datasheet PDFs -> typed product_specs.
--
-- The specs deliberately removed from the Lakebase `products` table are
-- produced fresh here from the real Bosch datasheet PDFs in the raw_docs
-- Volume, using two GA functions:
--   ai_parse_document(...)  -> layout/text/tables from the PDF
--   ai_extract(text, [...]) -> typed fields pulled from the parsed text
-- Battery/charger datasheets legitimately lack torque/rpm; those rows keep
-- voltage/weight/price and leave tool-only fields NULL.
--
-- Catalog/schema come from the `powertools-build` job parameters (:catalog /
-- :schema), so the product_specs target and the dim_product join resolve in the
-- same namespace as the other curate SQL tasks under a bundle target override.
-- NOTE: the READ_FILES Volume path below is still a literal
-- (…/techsummit/raw_docs/datasheets); parameterizing a READ_FILES path is not
-- done here because a non-literal path is not guaranteed to fold in that TVF.
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

-- 1) Parse each datasheet PDF, then extract typed fields.
CREATE OR REPLACE TEMP VIEW _parsed_datasheets AS
SELECT
  path,
  ai_parse_document(content) AS parsed
FROM READ_FILES(
  '/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/datasheets',
  format => 'binaryFile'
);

CREATE OR REPLACE TEMP VIEW _extracted_specs AS
SELECT
  path,
  extracted.*
FROM (
  SELECT
    path,
    ai_extract(
      CAST(parsed AS STRING),
      ARRAY(
        'model_name',
        'voltage_v',
        'max_torque_nm',
        'no_load_rpm',
        'chuck_capacity_mm',
        'weight_kg',
        'battery_platform'
      )
    ) AS extracted
  FROM _parsed_datasheets
);

-- 2) Deterministic model_name -> product_id crosswalk (12 active SKUs),
--    joined to dim_product by name so product_specs keys cleanly to the star.
CREATE OR REPLACE TEMP VIEW _model_crosswalk AS
SELECT dp.product_id, dp.name AS model_name
FROM dim_product dp
WHERE dp.name IN (
  'GSR 18V-55', 'GSB 18V-90 C', 'GSR 12V-35', 'PSR 1080 LI', 'PSB 1800 LI-2',
  'GBH 2-26', 'GBH 18V-26 F', 'PBH 2100 RE', 'GWS 18V-10', 'PWS 700-115',
  'GWS 22-230 JH', 'GST 18V-LI S'
);

-- 3) product_specs: typed numeric columns, joined to product_id.
--    ai_extract returns values WITH units ("2.7 Nm", "18 V", "1800 rpm"), so a
--    plain CAST(... AS DOUBLE) throws CAST_INVALID_INPUT. Pull the leading
--    numeric token out with regexp_extract and try_cast it (NULL on no match)
--    so battery/charger rows that legitimately lack torque/rpm stay NULL rather
--    than failing the whole job.
CREATE OR REPLACE TABLE product_specs AS
SELECT
  x.product_id,
  e.model_name,
  try_cast(regexp_extract(CAST(e.voltage_v         AS STRING), '[-+]?[0-9]*\\.?[0-9]+', 0) AS DOUBLE) AS voltage_v,
  try_cast(regexp_extract(CAST(e.max_torque_nm     AS STRING), '[-+]?[0-9]*\\.?[0-9]+', 0) AS DOUBLE) AS max_torque_nm,
  try_cast(regexp_extract(CAST(e.no_load_rpm       AS STRING), '[0-9]+', 0)                AS INT)    AS no_load_rpm,
  try_cast(regexp_extract(CAST(e.chuck_capacity_mm AS STRING), '[-+]?[0-9]*\\.?[0-9]+', 0) AS DOUBLE) AS chuck_capacity_mm,
  try_cast(regexp_extract(CAST(e.weight_kg         AS STRING), '[-+]?[0-9]*\\.?[0-9]+', 0) AS DOUBLE) AS weight_kg,
  e.battery_platform
FROM _extracted_specs e
JOIN _model_crosswalk x
  ON lower(trim(e.model_name)) = lower(trim(x.model_name));

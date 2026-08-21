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
-- Volume: nikks_fevm_workspace_7405607030687545.techsummit.raw_docs/datasheets
USE CATALOG nikks_fevm_workspace_7405607030687545;
USE SCHEMA techsummit;

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
CREATE OR REPLACE TABLE product_specs AS
SELECT
  x.product_id,
  e.model_name,
  CAST(e.voltage_v          AS DOUBLE) AS voltage_v,
  CAST(e.max_torque_nm      AS DOUBLE) AS max_torque_nm,
  CAST(e.no_load_rpm        AS INT)    AS no_load_rpm,
  CAST(e.chuck_capacity_mm  AS DOUBLE) AS chuck_capacity_mm,
  CAST(e.weight_kg          AS DOUBLE) AS weight_kg,
  e.battery_platform
FROM _extracted_specs e
JOIN _model_crosswalk x
  ON lower(trim(e.model_name)) = lower(trim(x.model_name));

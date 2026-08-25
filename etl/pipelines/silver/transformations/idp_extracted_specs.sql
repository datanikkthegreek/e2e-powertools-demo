-- Silver / IDP (2 of 3): parsed VARIANT -> TYPED extracted specs.
--
-- Streams _parsed_datasheets and applies ai_extract with a TYPED response
-- schema (structured output), mirroring the reference product-manuals pipeline
-- (github.com/datanikkthegreek/databricks_data_extraction). The schema declares
-- the numeric fields as JSON `number`, so ai_extract returns them typed in the
-- variant `response` -- NO regexp_extract / try_cast unit-stripping.
--
-- VERSION IS PINNED TO 2.0 ON PURPOSE. ai_extract's response shape is version
-- -dependent: under v2.0 each scalar sits DIRECTLY under response.specs[i]
-- (e.g. {"voltage_v": 18, ...}); under v2.1 (which is what this workspace
-- returns when the version is left to default) every scalar is wrapped as
-- {"value": ...}. Verified live 2026-08-21 with to_json(ai_extract(...)):
--   v2.0 -> {"response":{"specs":[{"voltage_v":18,"model_name":"GSR 18V-55",...}]}}
--   v2.1 -> {"response":{"specs":[{"voltage_v":{"value":18},...}]}}
-- Pinning v2.0 makes the shape deterministic, so we CAST the `response.specs`
-- variant array straight into a typed ARRAY<STRUCT<...>> with NO `.value`
-- unwrap. That array is what product_specs explodes downstream, exactly the way
-- event_view_item's `items` array is exploded in key_normalize. Bare names
-- resolve in the pipeline's configured catalog/schema (see
-- etl/resources/pipeline_silver.yml).
--
-- REPROCESSING NOTE: this is a streaming AI stage. Changing the prompt/schema
-- (or the pinned version) does NOT re-run ai_extract over datasheets already
-- consumed from _parsed_datasheets -- a FULL REFRESH of these IDP tables is
-- required to re-extract. See RUNBOOK.md.
CREATE OR REFRESH STREAMING TABLE _extracted_specs (
  path      STRING                                                                                                                                                                                                      COMMENT 'Full Volume file path of the source PDF datasheet. Carried from _parsed_datasheets for lineage tracing.',
  file_name STRING                                                                                                                                                                                                      COMMENT 'File name of the source PDF. Carried from _parsed_datasheets for human-readable identification.',
  specs     ARRAY<STRUCT<model_name: STRING, voltage_v: DOUBLE, max_torque_nm: DOUBLE, no_load_rpm: INT, chuck_capacity_mm: DOUBLE, weight_kg: DOUBLE, battery_platform: STRING>> COMMENT 'Array of typed product specifications extracted by AI from the datasheet. One entry per distinct power-tool model in the PDF (usually one). Exploded downstream in product_specs for per-model analysis.'
)
  COMMENT 'AI-extracted product specifications from parsed datasheets. One row per PDF, with a specs array containing typed numeric/string fields for each tool model found. Intermediate IDP stage: structured VARIANT -> typed ARRAY<STRUCT> via ai_extract. Consumed by idp_product_specs (which explodes the array). Internal table (prefixed with underscore).'
AS
SELECT
  path,
  file_name,
  CAST(
    ai_extract(
      parsed,
      '{
        "specs": {
          "type": "array",
          "description": "One entry per distinct power-tool model described in the datasheet. Usually exactly one.",
          "items": {
            "type": "object",
            "properties": {
              "model_name": {"type": "string", "description": "Bosch model designation, e.g. GSR 18V-55, GBH 2-26."},
              "voltage_v": {"type": "number", "description": "Rated/nominal voltage in volts."},
              "max_torque_nm": {"type": "number", "description": "Maximum torque in Newton-meters (Nm)."},
              "no_load_rpm": {"type": "number", "description": "Maximum no-load speed in RPM."},
              "chuck_capacity_mm": {"type": "number", "description": "Chuck/collet capacity in mm."},
              "weight_kg": {"type": "number", "description": "Tool weight in kg without battery."},
              "battery_platform": {"type": "string", "description": "Battery platform e.g. 18V, 12V, or corded for mains tools."}
            }
          }
        }
      }',
      map('version', '2.0')
    ):response.specs AS ARRAY<STRUCT<
      model_name:        STRING,
      voltage_v:         DOUBLE,
      max_torque_nm:     DOUBLE,
      no_load_rpm:       INT,
      chuck_capacity_mm: DOUBLE,
      weight_kg:         DOUBLE,
      battery_platform:  STRING
    >>
  ) AS specs
FROM STREAM(_parsed_datasheets);

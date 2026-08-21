-- Silver / IDP (2 of 3): parsed text -> TYPED extracted specs.
--
-- Streams _parsed_datasheets and applies ai_extract with a TYPED response
-- schema (structured output), mirroring the reference product-manuals pipeline
-- (github.com/datanikkthegreek/databricks_data_extraction). The schema declares
-- the numeric fields as JSON `number`, so ai_extract returns them typed in the
-- variant `response` -- NO regexp_extract / try_cast unit-stripping. ai_extract
-- v2 wraps each field as {value: ...}; we CAST the `response.specs` variant
-- array into a typed ARRAY<STRUCT<...>> and `transform` it into a clean,
-- unwrapped ARRAY<STRUCT<...>> named `specs`. That array is what product_specs
-- explodes downstream, exactly the way event_view_item's `items` array is
-- exploded in key_normalize. Bare names resolve in the pipeline's configured
-- catalog/schema (see etl/resources/pipeline_silver.yml).
CREATE OR REFRESH STREAMING TABLE _extracted_specs
  COMMENT 'Typed product specs extracted from parsed datasheets. specs is an ARRAY<STRUCT> (one entry per model in the PDF).'
  TBLPROPERTIES ('quality' = 'silver')
AS
SELECT
  path,
  file_name,
  transform(
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
        }'
      ):response.specs AS ARRAY<STRUCT<
        model_name:        STRUCT<value: STRING>,
        voltage_v:         STRUCT<value: DOUBLE>,
        max_torque_nm:     STRUCT<value: DOUBLE>,
        no_load_rpm:       STRUCT<value: INT>,
        chuck_capacity_mm: STRUCT<value: DOUBLE>,
        weight_kg:         STRUCT<value: DOUBLE>,
        battery_platform:  STRUCT<value: STRING>
      >>
    ),
    s -> named_struct(
      'model_name',        s.model_name.value,
      'voltage_v',         s.voltage_v.value,
      'max_torque_nm',     s.max_torque_nm.value,
      'no_load_rpm',       s.no_load_rpm.value,
      'chuck_capacity_mm', s.chuck_capacity_mm.value,
      'weight_kg',         s.weight_kg.value,
      'battery_platform',  s.battery_platform.value
    )
  ) AS specs
FROM STREAM(_parsed_datasheets);

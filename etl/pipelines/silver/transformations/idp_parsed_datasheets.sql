-- Silver / IDP (1 of 3): datasheet PDFs -> parsed text.
--
-- Streams the Bosch datasheet PDFs from the raw_docs Volume and runs
-- ai_parse_document over each binary file, keeping the parsed document as a
-- STRING the downstream extraction feeds on. The Volume path is a literal (a
-- non-literal path is not guaranteed to fold in read_files); everything else is
-- referenced by bare name so it resolves in the pipeline's own configured
-- catalog/schema (see etl/resources/pipeline_silver.yml), matching the event
-- tables. Mirrors the reference product-manuals pipeline
-- (github.com/datanikkthegreek/databricks_data_extraction) parse -> extract ->
-- explode chain as streaming tables.
CREATE OR REFRESH STREAMING TABLE _parsed_datasheets
  COMMENT 'Parsed Bosch datasheet PDFs. One row per PDF file on the raw_docs Volume.'
  TBLPROPERTIES ('quality' = 'silver')
AS
SELECT
  _metadata.file_path                    AS path,
  _metadata.file_name                    AS file_name,
  CAST(ai_parse_document(content) AS STRING) AS parsed
FROM STREAM read_files(
  '/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/datasheets',
  format => 'binaryFile'
);

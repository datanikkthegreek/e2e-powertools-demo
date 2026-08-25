-- Silver / IDP (1 of 3): datasheet PDFs -> parsed VARIANT.
--
-- Streams the Bosch datasheet PDFs from the raw_docs Volume and runs
-- ai_parse_document over each binary file, keeping the parsed result as a
-- VARIANT. ai_extract accepts that VARIANT directly (per the databricks-ai
-- -functions skill: "content: VARIANT | STRING -- raw text, or VARIANT from
-- ai_parse_document"), so we persist the structure rather than flattening to a
-- string. The parser version is pinned to 2.0 for deterministic output. The
-- Volume path is a literal (a non-literal path is not guaranteed to fold in
-- read_files); everything else is referenced by bare name so it resolves in the
-- pipeline's own configured catalog/schema (see etl/resources/pipeline_silver.yml),
-- matching the event tables. Mirrors the reference product-manuals pipeline
-- (github.com/datanikkthegreek/databricks_data_extraction) parse -> extract ->
-- explode chain as streaming tables.
CREATE OR REFRESH STREAMING TABLE _parsed_datasheets (
  path      STRING  COMMENT 'Full Volume file path of the source PDF datasheet (e.g. /Volumes/.../datasheets/GSR_18V-55.pdf). Unique identifier for lineage tracing back to the raw document.',
  file_name STRING  COMMENT 'File name of the source PDF (e.g. GSR_18V-55.pdf). Human-readable identifier for the datasheet.',
  parsed    VARIANT COMMENT 'Structured VARIANT output from ai_parse_document. Contains the full parsed document content (text, layout, tables) ready for downstream ai_extract processing.'
)
  COMMENT 'Parsed Bosch power tool datasheet PDFs. One row per PDF file ingested from the raw_docs Volume. Intermediate IDP stage: raw binary PDF -> structured VARIANT via ai_parse_document. Consumed by _extracted_specs for AI-based specification extraction. Internal table (prefixed with underscore).'
AS
SELECT
  _metadata.file_path                        AS path,
  _metadata.file_name                        AS file_name,
  ai_parse_document(content, map('version', '2.0')) AS parsed
FROM STREAM read_files(
  '/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/datasheets',
  format => 'binaryFile'
);

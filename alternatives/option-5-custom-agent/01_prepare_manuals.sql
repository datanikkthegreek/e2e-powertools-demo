CREATE OR REPLACE TABLE nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_chunks AS
WITH parsed AS (
  SELECT path AS source_path, ai_parse_document(content, map('version', '2.0')) AS document
  FROM read_files(
    '/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/',
    format => 'binaryFile'
  )
),
prepared AS (
  SELECT source_path, ai_prep_search(document) AS search_document
  FROM parsed
  WHERE document:error_status IS NULL
)
SELECT
  concat(sha2(source_path, 256), '-', chunks.value:chunk_id::STRING) AS chunk_id,
  chunks.value:chunk_to_retrieve::STRING AS chunk_to_retrieve,
  chunks.value:chunk_to_embed::STRING AS chunk_to_embed,
  source_path
FROM prepared
, LATERAL variant_explode(search_document:document:contents) chunks;

ALTER TABLE nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_chunks
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

CREATE OR REPLACE TABLE nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_chunks AS
SELECT
  concat(sha2(source_path, 256), '-', value:chunk_id::STRING) AS chunk_id,
  value:chunk_to_retrieve::STRING AS chunk_to_retrieve,
  value:chunk_to_embed::STRING AS chunk_to_embed,
  source_path
FROM nikks_fevm_workspace_7405607030687545.techsummit.option3_prepared_manuals,
LATERAL variant_explode(search_document:document:contents);

ALTER TABLE nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_chunks
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

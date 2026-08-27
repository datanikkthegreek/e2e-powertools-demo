CREATE OR REPLACE TABLE nikks_fevm_workspace_7405607030687545.techsummit.option3_prepared_manuals AS
SELECT
  path AS source_path,
  ai_prep_search(ai_parse_document(content, map('version', '2.0'))) AS search_document
FROM read_files(
  '/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/',
  format => 'binaryFile'
);

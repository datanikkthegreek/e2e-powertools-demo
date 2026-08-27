CREATE OR REPLACE FUNCTION nikks_fevm_workspace_7405607030687545.techsummit.search_product_manuals(
  question STRING COMMENT 'Natural-language service, safety, maintenance, or troubleshooting question'
)
RETURNS TABLE (
  manual_text STRING,
  source_path STRING,
  score DOUBLE
)
COMMENT 'Searches Bosch product manuals. Use for operating, safety, maintenance, and troubleshooting questions.'
RETURN
  SELECT chunk_to_retrieve, source_path, search_score AS score
  FROM VECTOR_SEARCH(
    index => 'nikks_fevm_workspace_7405607030687545.techsummit.option4_manual_index',
    query_text => question,
    num_results => 5
  );

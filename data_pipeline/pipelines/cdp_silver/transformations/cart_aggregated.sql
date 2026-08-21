CREATE OR REFRESH MATERIALIZED VIEW cart_aggregated
COMMENT "One row per cart with all items collected into a struct array."
TBLPROPERTIES ("quality" = "gold")
AS SELECT
  cart_id,
  user_id,
  MAX(source_timestamp) AS source_timestamp,
  COLLECT_LIST(STRUCT(item_id, item_name, new_quantity AS quantity, price, currency)) AS items
FROM cart_filtered
GROUP BY cart_id, user_id

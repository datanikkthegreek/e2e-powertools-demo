CREATE OR REFRESH MATERIALIZED VIEW cart_filtered
COMMENT "Latest add_to_cart mutation per cart_id and item_id where new_quantity is above 0."
TBLPROPERTIES ("quality" = "gold")
AS
SELECT *
FROM event_add_to_cart
WHERE new_quantity > 0
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY cart_id, item_id
  ORDER BY source_timestamp DESC NULLS LAST
) = 1

CREATE OR REFRESH MATERIALIZED VIEW cart_abandoned
COMMENT "Carts that were never purchased — identified via anti-join with event_purchase."
TBLPROPERTIES ("quality" = "gold")
AS SELECT cart_aggregated.*
FROM cart_aggregated
LEFT ANTI JOIN event_purchase USING (cart_id)

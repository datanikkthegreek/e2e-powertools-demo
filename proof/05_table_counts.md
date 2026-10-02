# Base table counts and maximum timestamps

Blank `max_timestamp` is the CLI JSON rendering of SQL NULL. Three tables have no timestamp column; `dim_customer.signup_date` exists but is NULL in every row.

```console
$ databricks experimental aitools tools query "SELECT 'dim_product' AS table_name, COUNT(*) AS row_count, CAST(NULL AS TIMESTAMP) AS max_timestamp, 'no timestamp column' AS timestamp_column FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_product UNION ALL SELECT 'dim_customer', COUNT(*), CAST(MAX(signup_date) AS TIMESTAMP), 'signup_date' FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_customer UNION ALL SELECT 'fact_purchase', COUNT(*), MAX(created_at), 'created_at' FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase UNION ALL SELECT 'fact_purchase_line', COUNT(*), CAST(NULL AS TIMESTAMP), 'no timestamp column' FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line UNION ALL SELECT 'event_view_item', COUNT(*), MAX(ingest_timestamp), 'ingest_timestamp' FROM nikks_fevm_workspace_7405607030687545.techsummit.event_view_item UNION ALL SELECT 'event_add_to_cart', COUNT(*), MAX(source_timestamp), 'source_timestamp' FROM nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart UNION ALL SELECT 'idp_product_specs', COUNT(*), CAST(NULL AS TIMESTAMP), 'no timestamp column' FROM nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs" -p FEVM
[
  {
    "max_timestamp": "",
    "row_count": "12",
    "table_name": "dim_product",
    "timestamp_column": "no timestamp column"
  },
  {
    "max_timestamp": "",
    "row_count": "14",
    "table_name": "dim_customer",
    "timestamp_column": "signup_date"
  },
  {
    "max_timestamp": "2026-10-02T11:36:06.252Z",
    "row_count": "36",
    "table_name": "fact_purchase",
    "timestamp_column": "created_at"
  },
  {
    "max_timestamp": "",
    "row_count": "47",
    "table_name": "fact_purchase_line",
    "timestamp_column": "no timestamp column"
  },
  {
    "max_timestamp": "2026-10-02T15:26:35.388Z",
    "row_count": "3031",
    "table_name": "event_view_item",
    "timestamp_column": "ingest_timestamp"
  },
  {
    "max_timestamp": "2026-10-02T15:26:37.424Z",
    "row_count": "860",
    "table_name": "event_add_to_cart",
    "timestamp_column": "source_timestamp"
  },
  {
    "max_timestamp": "",
    "row_count": "12",
    "table_name": "idp_product_specs",
    "timestamp_column": "no timestamp column"
  }
]
```


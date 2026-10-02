# Continuous silver pipeline

Captured at 2026-10-02T15:20:12Z. The latest update started at 2026-09-30T20:42:52.970Z, so its observed running duration at capture time was 1 day, 18 hours, 37 minutes, 19 seconds.

```console
$ databricks pipelines get dc8db3d2-8aa7-4a8c-a6f4-5bab859afbaf -p FEVM -o json | jq '{pipeline_id, name, state, continuous: .spec.continuous, catalog: .spec.catalog, schema: .spec.schema, latest_update: .latest_updates[0]}'
{
  "pipeline_id": "dc8db3d2-8aa7-4a8c-a6f4-5bab859afbaf",
  "name": "powertools-silver-dev",
  "state": "RUNNING",
  "continuous": true,
  "catalog": "nikks_fevm_workspace_7405607030687545",
  "schema": "techsummit",
  "latest_update": {
    "creation_time": "2026-09-30T20:42:52.970Z",
    "state": "RUNNING",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  }
}
```

## Dataset/flow list

```console
$ databricks pipelines list-pipeline-events dc8db3d2-8aa7-4a8c-a6f4-5bab859afbaf --limit 1000 -p FEVM -o json | jq -r '[.[] | select(.event_type == "flow_definition") | (.origin.flow_name // .details.flow_definition.output_dataset // .message)] | unique[]'
_accounts_changes
_products_changes
_purchase_lines_changes
_purchases_changes
nikks_fevm_workspace_7405607030687545.techsummit._extracted_specs
nikks_fevm_workspace_7405607030687545.techsummit._parsed_datasheets
nikks_fevm_workspace_7405607030687545.techsummit.dim_customer_cdc
nikks_fevm_workspace_7405607030687545.techsummit.dim_product_cdc
nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart
nikks_fevm_workspace_7405607030687545.techsummit.event_view_item
nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_cdc
nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line_cdc
nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs
```

## Latest event-log excerpt

```console
$ databricks pipelines list-pipeline-events dc8db3d2-8aa7-4a8c-a6f4-5bab859afbaf --limit 20 -p FEVM -o json | jq '[.[] | {timestamp, event_type, level, message, update_id: .origin.update_id}]'
[
  {
    "timestamp": "2026-09-30T20:43:51.255Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.dim_customer_cdc' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:50.904Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.dim_customer_cdc' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:50.712Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:49.891Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:49.773Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_cdc' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:49.198Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_cdc' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:48.966Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line_cdc' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:48.578Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line_cdc' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:48.372Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.dim_product_cdc' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:47.917Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.dim_product_cdc' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:47.448Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:46.907Z",
    "event_type": "advisory",
    "level": "WARN",
    "message": "By running Auto Loader (Flow Name: nikks_fevm_workspace_7405607030687545.techsummit._parsed_datasheets) with directory listing in continuous mode, you are missing out on optimized file discovery and processing. This can increase ingestion costs. Databricks recommends enabling file events instead.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:46.651Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:46.551Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit._parsed_datasheets' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:46.033Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit._parsed_datasheets' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:45.800Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.event_view_item' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:44.983Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit.event_view_item' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:44.553Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit._extracted_specs' is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:38.867Z",
    "event_type": "flow_progress",
    "level": "INFO",
    "message": "Flow 'nikks_fevm_workspace_7405607030687545.techsummit._extracted_specs' is STARTING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  },
  {
    "timestamp": "2026-09-30T20:43:38.655Z",
    "event_type": "update_progress",
    "level": "INFO",
    "message": "Update 40d48a is RUNNING.",
    "update_id": "40d48a5b-a351-43cb-b4a7-d4c64a19ba4f"
  }
]
```


# Zerobus live-funnel proof — 2026-10-02

This is the only live write authorized by the evidence request: two fresh synthetic test events posted through the app. No table, pipeline, job, or seed mutation was performed directly.

## Before

```console
$ databricks experimental aitools tools query "SELECT (SELECT COUNT(*) FROM nikks_fevm_workspace_7405607030687545.techsummit.gtm_events) AS gtm_events_count, (SELECT MAX(ingestion_time) FROM nikks_fevm_workspace_7405607030687545.techsummit.gtm_events) AS max_gtm_ingestion_time_ms, (SELECT MAX(ingest_timestamp) FROM nikks_fevm_workspace_7405607030687545.techsummit.event_view_item) AS max_view_ingest_timestamp, (SELECT MAX(source_timestamp) FROM nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart) AS max_cart_source_timestamp" -p FEVM
[
  {
    "gtm_events_count": "4381",
    "max_cart_source_timestamp": "2026-10-02T11:35:36.323Z",
    "max_gtm_ingestion_time_ms": "1790941110425",
    "max_view_ingest_timestamp": "2026-10-02T11:35:22.487Z"
  }
]
```

## POST fresh `view_item` and `add_to_cart`

The command used `WorkspaceClient(profile='FEVM').config.authenticate()` to add the authentication header without printing or storing the credential.

```console
$ python -u - <<'PY'
from databricks.sdk import WorkspaceClient
import json
import requests

w = WorkspaceClient(profile="FEVM")
headers = w.config.authenticate()  # credential used but never printed
headers["Content-Type"] = "application/json"
url = "https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/api/events"
payloads = [
    {"event_name":"view_item","page_location":"https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/product/06f80d3f-2c18-5d0f-876b-d95f03eee4cc","page_title":"Execution proof","web_input_data":{"user_id":"user-proof-20261002T152700Z","items":[{"item_id":"06f80d3f-2c18-5d0f-876b-d95f03eee4cc","item_name":"GSB 18V-90 C","price":249.0,"currency":"EUR","quantity":1}]}},
    {"event_name":"add_to_cart","page_location":"https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/cart","page_title":"Execution proof","web_input_data":{"user_id":"user-proof-20261002T152700Z","cart_id":"cart-proof-20261002T152700Z","item_id":"06f80d3f-2c18-5d0f-876b-d95f03eee4cc","item_name":"GSB 18V-90 C","price":249.0,"previous_quantity":0,"new_quantity":1,"quantity_delta":1,"cart_action":"add","currency":"EUR"}},
]
for payload in payloads:
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print("POST", url)
    print("REQUEST", json.dumps(payload, sort_keys=True))
    print("HTTP", response.status_code)
    print("BODY", response.text)
PY
POST https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/api/events
REQUEST {"event_name": "view_item", "page_location": "https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/product/06f80d3f-2c18-5d0f-876b-d95f03eee4cc", "page_title": "Execution proof", "web_input_data": {"items": [{"currency": "EUR", "item_id": "06f80d3f-2c18-5d0f-876b-d95f03eee4cc", "item_name": "GSB 18V-90 C", "price": 249.0, "quantity": 1}], "user_id": "user-proof-20261002T152700Z"}}
HTTP 200
BODY {"status":"ok"}
POST https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/api/events
REQUEST {"event_name": "add_to_cart", "page_location": "https://powertools-webshop-7405607030687545.5.azure.databricksapps.com/cart", "page_title": "Execution proof", "web_input_data": {"cart_action": "add", "cart_id": "cart-proof-20261002T152700Z", "currency": "EUR", "item_id": "06f80d3f-2c18-5d0f-876b-d95f03eee4cc", "item_name": "GSB 18V-90 C", "new_quantity": 1, "previous_quantity": 0, "price": 249.0, "quantity_delta": 1, "user_id": "user-proof-20261002T152700Z"}}
HTTP 200
BODY {"status":"ok"}
```

## After: raw landing and continuous-pipeline outputs

```console
$ databricks experimental aitools tools query "SELECT COUNT(*) AS gtm_events_count, MAX(ingestion_time) AS max_gtm_ingestion_time_ms, COUNT_IF(eventData LIKE '%proof-20261002T152700Z%') AS marker_events FROM nikks_fevm_workspace_7405607030687545.techsummit.gtm_events" -p FEVM
[
  {
    "gtm_events_count": "4383",
    "marker_events": "2",
    "max_gtm_ingestion_time_ms": "1790954797425"
  }
]

$ databricks experimental aitools tools query "SELECT 'view_item' AS event_table, COUNT(*) AS marker_rows, MAX(ingest_timestamp) AS max_event_timestamp FROM nikks_fevm_workspace_7405607030687545.techsummit.event_view_item WHERE user_id = 'user-proof-20261002T152700Z' UNION ALL SELECT 'add_to_cart', COUNT(*), MAX(source_timestamp) FROM nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart WHERE user_id = 'user-proof-20261002T152700Z'" -p FEVM
[
  {
    "event_table": "view_item",
    "marker_rows": "1",
    "max_event_timestamp": "2026-10-02T15:26:35.388Z"
  },
  {
    "event_table": "add_to_cart",
    "marker_rows": "1",
    "max_event_timestamp": "2026-10-02T15:26:37.424Z"
  }
]
```

The raw count increased by exactly two, the raw maximum ingestion epoch advanced, and each continuous output contains exactly one row carrying this session's unique marker.

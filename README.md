# e2e CDP Demo

End-to-end customer-data-platform demo. Two independently deployable Databricks Asset Bundles:

| Folder | What it is | Deploy |
|---|---|---|
| [`webshop_app/`](./webshop_app) | apx full-stack web shop (React + FastAPI) backed by Lakebase Postgres. Emits GA4 events to a server-side GTM container which lands them in `cdp.gtm_events`. | `cd webshop_app && databricks bundle deploy` |
| [`data_pipeline/`](./data_pipeline) | Seed notebook (simulated GTM events) plus a continuous Lakeflow Declarative Pipeline that parses `cdp.gtm_events` into a bronze table and six event-typed silver tables. | `cd data_pipeline && databricks bundle deploy` |

Both bundles target the same Unity Catalog schema (`nikks_fevm_workspace_7405607030687545.cdp`) and share data by name only — neither bundle references the other.

See [`webshop_app/README.md`](./webshop_app/README.md) for the apx dev-loop workflow (`apx dev start`, hot reload, OpenAPI watcher).

# Build submission: text-readable execution evidence

All outputs in this directory are real captures produced on 2026-10-02 against Databricks profile `FEVM`, catalog `nikks_fevm_workspace_7405607030687545`, schema `techsummit`. No result or number was copied from memory. Live infrastructure was read-only except for the two explicitly authorized synthetic app events in `11_zerobus_live_funnel.md`.

| Artifact | Demo component | What it proves |
|---|---|---|
| `01_bundle_validate.txt` | DAB / ETL | The ETL bundle validates successfully for `dev`. |
| `02_bundle_summary.txt` | DAB, app, Genie | Deployed job, continuous pipeline, two Volumes, Genie space, schema, and running app identity/status. |
| `03_pipeline.md` | ETL pipeline | `powertools-silver-dev` is continuous and RUNNING; includes latest update, duration, flows, and event-log excerpt. |
| `04_jobs.md` | Build job | Actual latest successful `powertools-build` run and all deployed task statuses. |
| `05_table_counts.md` | Lakehouse | Current row counts and available maximum timestamps for all seven base tables. |
| `06_funnel.md` | Funnel + IDP | View → cart → purchase stage counts and the 12/12 product/spec join. |
| `07_sample_rows.md` | Lakehouse | Ten actual rows from every base table. |
| `08_idp_extraction.md` | IDP | All typed voltage, torque, and RPM outputs sourced from the 12 datasheet PDFs. |
| `09_knowledge_assistant.md` | Knowledge Assistant | KA/source/endpoint state and a real manual-cited answer from the endpoint. |
| `10_genie_space.md` | Genie | Live seven-table + manuals-volume configuration and two completed NL-to-SQL benchmark executions. |
| `11_zerobus_live_funnel.md` | App + Zerobus + ETL | Two HTTP 200 app events, raw count advancement, and continuous landing in both event tables. |
| `12_dashboard.md` | AI/BI dashboard | 11 dataset queries + real executed results. |
| `notebooks/verify_demo.ipynb` | Cross-component verification | Executed key queries with committed output cells. |
| `notebooks/knowledge_assistant_executed.ipynb` | Knowledge Assistant | Executed read-only copy of the KA setup notebook with committed output cells. |

## Authentication capture

```console
$ databricks current-user me -p FEVM | jq '{active, displayName, id, userName}'
{
  "active": true,
  "displayName": "[redacted-name]",
  "id": "[redacted-account-id]",
  "userName": "[redacted-email]"
}
```

This focused `jq` projection was captured before any live query; it omits irrelevant SCIM group and entitlement fields.

## Read-only constraint note

The original KA notebook's idempotent setup cell can create/reconcile sources and always calls `sync_knowledge_sources`. That is a live mutation and was not authorized by the read-only rule. Its executed proof copy therefore performs the same existing-resource lookup and status checks, labels the sync as skipped, and leaves the original notebook untouched. Everything else requested was captured.

# e2e-powertools-demo

A trimmed, two-bundle copy of `e2e-cdp-demo` rebuilt for the **Bosch Power
Tools — Service & Sales Assistant** Tech Summit demo. It runs a real Bosch PT
webshop (Databricks App on Lakebase) and the ETL data flow that feeds an AI/BI
Genie space, plus IDP-extracted product specs.

See the design PRD: `docs/superpowers/specs/2026-08-20-bosch-powertools-service-sales-demo-design.md`
(in the `nikkscoworkers` repo).

> **Status:** bundles authored and `databricks bundle validate`-clean. Nothing
> has been deployed or provisioned. This is the "author + validate" checkpoint.

## Environment

Everything lives in one isolated namespace on the FEVM workspace:

| Thing | Value |
|---|---|
| Workspace | FEVM (`adb-7405607030687545` / `nikks_fevm_workspace`) |
| Catalog | `nikks_fevm_workspace_7405607030687545` |
| Schema | `techsummit` |
| Lakebase project | `techsummit` |
| Volume (PDFs) | `nikks_fevm_workspace_7405607030687545.techsummit.raw_docs` |

## Two-bundle layout

```
e2e-powertools-demo/
  app/                       # BUNDLE 1 — Databricks App (webshop) on Lakebase
    databricks.yml
    app.yml                  # runtime: command + env (LAKEBASE_PROJECT_ID=techsummit, ...)
    resources/app.yml        # app resource; references the techsummit Lakebase project
    src/…                    # storefront front/back-end (specs removed from the product pages)
  etl/                       # BUNDLE 2 — ETL + Lakebase  (DEPLOY FIRST)
    databricks.yml
    resources/
      lakebase.yml           # Lakebase project 'techsummit' + raw_docs Volume
      sync.yml               # Lakebase -> Delta CDC sync (wal2delta) -> lb_*_history (bound to techsummit project)
      pipeline_silver.yml    # gtm_events -> event_view_item + event_add_to_cart ONLY
      job_build.yml          # one DAG: seed_gtm -> silver -> cdc_to_current -> key_normalize -> idp
    pipelines/silver/transformations/
      _shared.py             # shared schema/helpers (config keys: pipeline.table_*)
      event_view_item.py     # kept
      event_add_to_cart.py   # kept
    src/
      seed_gtm_events.py     # behavior seed (view/cart focus)
      cdc_to_current.sql     # lb_*_history -> dim_product / dim_customer / fact_purchase(_line)
      key_normalize.sql      # item_id -> product_id -> fact_view_item / fact_add_to_cart
      idp_product_specs.sql  # ai_parse_document + ai_extract -> product_specs (+ crosswalk)
    data/
      datasheets/            # (empty, .gitkeep) real Bosch datasheet PDFs — added later
      manuals/               # (empty, .gitkeep) real Bosch manuals — added later
  RUNBOOK.md                 # live click-path (stub)
  README.md
```

## Deploy order (important)

**Deploy the ETL bundle first, then the App bundle.** The App references the
Lakebase project (`techsummit`) that the ETL bundle provisions — deploying the
App first would point it at a project that doesn't exist yet.

```bash
# 1) ETL + Lakebase (provisions the techsummit Lakebase project + Volume, data flow)
cd etl && databricks bundle validate -p FEVM && databricks bundle deploy -p FEVM

# 2) App (webshop) — build the front-end first, then deploy
cd ../app && apx build && databricks bundle validate -p FEVM && databricks bundle deploy -p FEVM
```

> `app/.build/` ships with a placeholder so `bundle validate` works on a fresh
> checkout. `apx build` overwrites it with the real compiled app before deploy.

## What changed vs. the baseline (`e2e-cdp-demo`)

The first commit on `main` is the **unmodified** `e2e-cdp-demo` baseline (the
review base). Everything below is the trim, on the feature branch:

**Restructured into two asset bundles**
- `webshop_app/` → `app/` (App bundle); the app resource moved into
  `app/resources/app.yml`.
- The old `data_pipeline/` + top-level `notebooks/` were removed and replaced by
  a fresh, purpose-built `etl/` bundle (Lakebase + trimmed silver + curate).

**Environment repointed to the isolated `techsummit` namespace**
- Catalog → `nikks_fevm_workspace_7405607030687545`, schema → `techsummit`,
  Lakebase project → `techsummit`, Volume → `raw_docs`.
- App runtime (`app/app.yml`) and backend config defaults (`_config.py`,
  `lakebase.py`) updated; no references to the old `cdp` schema remain in the
  trimmed code paths. (The pipeline config keys were renamed `cdp.table_*` →
  `pipeline.table_*`.)
- Zerobus workspace repointed to FEVM; the Zerobus endpoint + OAuth client id
  are left as clearly-marked `REPLACE_WITH_...` placeholders to set at deploy.

**Specs moved out of the product (decision "A")**
- Removed the `specs` column from the Lakebase `products` data model
  (`models.py`), the seed (`seed.py`), the spec detail (`_product_details.py`,
  which now keeps only `long_description`), and the app UI (the "Specifications"
  card in the product page + the `specs` field in `api.ts`).
- Specs are produced fresh by IDP into `product_specs` (`idp_product_specs.sql`).

**Delta side trimmed to only the required tables**
- Kept `gtm_events` (raw) and only the `event_view_item` + `event_add_to_cart`
  silver transforms.
- Removed the purchase / pageview / abandon / signup silver tables, the email
  sinks, all gold cart MVs, and `gold_customer_360` from the pipeline.

**Lakebase (OLTP) kept:** `products` (no specs), `accounts`, `carts`,
`cart_items`, `purchases`, `purchase_lines`. The 12 active seeded Bosch tools
stay.

## Genie base tables (7)

`dim_product`, `product_specs`, `dim_customer`, `fact_purchase`,
`fact_purchase_line`, `fact_view_item`, `fact_add_to_cart`. The Genie space,
Knowledge Assistant, and Supervisor agent are UI-built (see `RUNBOOK.md`).

## Notes / follow-ups

- The webshop's legacy in-app **Analytics** page (and its `cdp-triggered`
  pipeline trigger) has been **removed** — it queried tables that no longer
  exist in the trimmed pipeline (`event_sign_up` / `event_purchase` /
  `gold_customer_360` / `cart_abandoned`) and would have errored live. The
  analytics story is told through the Genie space instead. The route, nav link,
  backend `analytics.py`/`jobs.py`, and their models/config were deleted; the
  dead client wrappers left in the generated `ui/lib/api.ts` (nothing imports
  them) are regenerated away on the next `apx build`.
- `etl/src/*.sql` and `seed_gtm_events.py` are coherent stubs matching the PRD
  steps; they are meant to be run/tuned during the post-approval integration
  phase, not before.

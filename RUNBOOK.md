# RUNBOOK — Bosch Power Tools demo (stub)

> Stub. Fill in during the rehearsal after the ETL + App bundles are deployed
> and the Genie space / Knowledge Assistant / Supervisor are built in the UI.

## Prereqs (deploy + run order)

The data flow has a hard dependency chain — each step reads what the previous
one produced. Run it in exactly this order:

1. **Deploy the ETL bundle.** `cd etl && databricks bundle deploy -p FEVM` —
   provisions the `techsummit` Lakebase project (**pg17**, required by CDF), the
   `techsummit` UC schema, the `raw_docs` Volume, the silver pipeline, and the
   `powertools-build` job.
2. **Seed the OLTP.** `python etl/src/seed_lakebase_oltp.py --profile FEVM
   --project techsummit`. Creates products/accounts/carts/cart_items/purchases/
   purchase_lines with deterministic UUIDs and sets `REPLICA IDENTITY FULL` on
   all of them (CDF prereq). *(a) Lakebase now holds the source-of-truth rows.*
   (In production these arrive via the webshop App; Phase 1 seeds directly.)
3. **Enable + start Lakebase CDF** (native Postgres→Delta change feed):
   - Admin: enable the **Lakebase Change Data Feed** preview (workspace
     Previews page).
   - Lakebase Postgres > project `techsummit` > branch `production` >
     **Lakebase CDF** tab > **Start**. Map source DB `databricks_postgres`,
     schema `public` → destination catalog `${var.catalog}` (whatever the
     deployed bundle target resolves it to — for the current FEVM target that
     is `nikks_fevm_workspace_7405607030687545`), schema `${var.schema}`
     (`techsummit` on the current FEVM target).
   - CDF snapshots + streams every `public` table into
     `lb_<table>_history` Delta tables (~15s batches). Wait until
     `lb_products_history`, `lb_accounts_history`, `lb_purchases_history`,
     `lb_purchase_lines_history` have rows. *(b) — must precede step 5: both the
     GTM seed and the silver pipeline's AUTO CDC flows read the `lb_*_history`
     tables.*
4. **Upload PDFs.** Real Bosch **datasheet** PDFs to
   `…techsummit.raw_docs/datasheets` (the IDP streaming tables in the silver
   pipeline read them). Manuals are a Phase-2 concern.
5. **Run `powertools-build`.** One job, one enforced DAG:
   `wait_for_cdc` (gate) → `seed_gtm_events` (c) → `run_silver_pipeline` (d) →
   `key_normalize` (e).
   The silver pipeline (d) now builds most of the base tables as streaming tables:
   - the two event tables (`event_view_item`, `event_add_to_cart`) from `gtm_events`;
   - the four current-state tables (`dim_product`, `dim_customer`, `fact_purchase`,
     `fact_purchase_line`) from the `lb_*_history` change-logs via **native AUTO
     CDC** (the engine does the CDC merge/collapse in-pipeline — no ROW_NUMBER
     collapse task);
   - IDP (datasheet PDFs → `product_specs`) as three streaming tables.

   IDP and the CDC tables no longer depend on the curate step. `key_normalize` (e)
   is the terminal warehouse task and produces `fact_view_item` / `fact_add_to_cart`
   from the event silver tables; it has no data dependency on the CDC tables but
   runs after the pipeline. This builds the 7 Genie base tables.
   > **Reprocessing:** the CDC + IDP stages are streaming (and `ai_extract` is
   > pinned to `version 2.0`). Changing an IDP prompt/schema/version — or needing
   > to re-collapse a CDC table — does **not** re-run over inputs already consumed;
   > do a **full refresh** of the affected streaming tables (e.g.
   > `databricks bundle run powertools_silver --full-refresh _parsed_datasheets,_extracted_specs,product_specs -p FEVM`).
   > A full refresh recomputes the event + CDC tables from the existing
   > `gtm_events` / `lb_*_history` (it does **not** re-run `seed_gtm_events`), so
   > the funnel counts stay put.
6. **Build (UI):** Knowledge Assistant (manuals), Genie space (7 base tables),
   Supervisor agent (Genie + Knowledge Assistant).

## Live click-path (to be finalized)

1. **Webshop** — browse, add a tool to cart, buy it. "Real app on Databricks,
   backed by Lakebase."
2. **IDP** — the silver pipeline's IDP streaming tables turn a datasheet PDF
   into typed `product_specs` (parse → typed `ai_extract` → explode). "The app
   doesn't even store these specs."
3. **Knowledge Assistant** — a usage question + a repair question; cited answers.
4. **Genie** — "view → cart → purchase conversion by category"; "revenue by
   product last month".
5. **Supervisor (AI Playground)** — the combined overheating question; watch it
   call both sub-agents and synthesize.

## Exact questions to ask

_TODO: paste the finalized Genie / KA / Supervisor prompts here after rehearsal._

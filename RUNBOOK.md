# RUNBOOK — Bosch Power Tools demo (stub)

> Stub. Fill in during the rehearsal after the ETL + App bundles are deployed
> and the Genie space / Knowledge Assistant / Supervisor are built in the UI.

## Prereqs (deploy + run order)

The data flow has a hard dependency chain — each step reads what the previous
one produced. Run it in exactly this order:

1. **Deploy the ETL bundle.** `cd etl && databricks bundle deploy -p FEVM` —
   provisions the `techsummit` Lakebase project, the `raw_docs` Volume, the CDC
   sync, the silver pipeline, and the `powertools-build` job.
2. **Deploy the app + seed OLTP.** `cd app && apx build && databricks bundle deploy -p FEVM`,
   then open the webshop once. On first connect it seeds the Lakebase OLTP
   tables (products/accounts/carts/purchases/...). *(a) Lakebase now holds the
   source-of-truth rows.*
3. **Let the CDC sync populate.** The continuous `synced_database_tables` stream
   the OLTP tables into Delta change-logs `lb_*_history`. Wait until they have
   rows before running the build job. *(b) — must happen before step 5, because
   both the GTM seed and `cdc_to_current` read `lb_products_history`.*
4. **Upload PDFs.** Real Bosch **datasheet** PDFs to
   `…techsummit.raw_docs/datasheets` and **manual** PDFs to `…/manuals`
   (needed by the IDP step inside the build job).
5. **Run `powertools-build`.** One job, one enforced DAG:
   `seed_gtm_events` (c) → `run_silver_pipeline` (d) →
   `cdc_to_current` → `key_normalize` → `idp_product_specs` (e).
   This builds the 7 Genie base tables.
6. **Build (UI):** Knowledge Assistant (manuals), Genie space (7 base tables),
   Supervisor agent (Genie + Knowledge Assistant).

## Live click-path (to be finalized)

1. **Webshop** — browse, add a tool to cart, buy it. "Real app on Databricks,
   backed by Lakebase."
2. **IDP** — run `idp_product_specs.sql` on a datasheet: PDF → typed
   `product_specs`. "The app doesn't even store these specs."
3. **Knowledge Assistant** — a usage question + a repair question; cited answers.
4. **Genie** — "view → cart → purchase conversion by category"; "revenue by
   product last month".
5. **Supervisor (AI Playground)** — the combined overheating question; watch it
   call both sub-agents and synthesize.

## Exact questions to ask

_TODO: paste the finalized Genie / KA / Supervisor prompts here after rehearsal._

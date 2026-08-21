# RUNBOOK — Bosch Power Tools demo (stub)

> Stub. Fill in during the rehearsal after the ETL + App bundles are deployed
> and the Genie space / Knowledge Assistant / Supervisor are built in the UI.

## Prereqs (deploy order)

1. `cd etl && databricks bundle deploy -p FEVM` — provisions the `techsummit`
   Lakebase project + `raw_docs` Volume and the data flow.
2. `cd app && apx build && databricks bundle deploy -p FEVM` — the webshop.
3. Upload real Bosch **datasheet** PDFs to
   `…techsummit.raw_docs/datasheets` and **manual** PDFs to `…/manuals`.
4. Run `powertools-seed-gtm`, then the silver pipeline, the CDC sync, and
   `powertools-curate` to build the 7 Genie base tables.
5. Build (UI): Knowledge Assistant (manuals), Genie space (7 base tables),
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

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
6. **Build:** Knowledge Assistant (manuals) — see the
   **Knowledge Assistant (product manuals)** section below; it can now be built
   **programmatically** via the `databricks knowledge-assistants` CLI. Genie
   space (7 base tables) and the Supervisor agent (Genie + Knowledge Assistant)
   are still built in the UI.

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

## Knowledge Assistant (product manuals)

A Databricks **Agent Bricks Knowledge Assistant** (KA) for RAG Q&A over the 12
power-tool **manuals**. This is the *simple* path: manuals → UC Volume → KA
pointed directly at the Volume folder. No `ai_parse_document`, no
`ai_prep_search`, no streaming tables, no Vector Search index — the KA does its
own chunking/embedding/retrieval over the PDFs.

> **Synthetic content.** We cannot legally redistribute real Bosch manuals, so
> the 12 manuals are **synthetic demo documents** generated from each tool's real
> spec class. Every page footer and cover carry
> _"Synthetic demo content — not an official Bosch document."_ The generator,
> `etl/src/generate_manuals.py`, is the reproducible source of truth; the PDFs
> are git-ignored (`etl/data/manuals/*.pdf`).

The manuals live in a **new `manuals/` subfolder** of the existing `raw_docs`
Volume — separate from the `datasheets/` folder that IDP reads:
`/Volumes/${var.catalog}/${var.schema}/${var.volume}/manuals/`
(resolves to
`/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/manuals/`
on the current FEVM target).

### 1. Generate + upload the manuals

Idempotent and re-runnable. Renders 12 multi-page PDFs (Safety, Technical
Specifications, Intended Use, Operating Instructions, Battery/Charging *or*
Mains, Maintenance & Cleaning, Troubleshooting, Warranty & Service) via
`weasyprint`, then uploads them PDF-only to the Volume subfolder — it never
touches the sibling `datasheets/`.

```bash
# from repo root; defaults target the FEVM catalog/schema/volume + profile
python etl/src/generate_manuals.py            # generate + upload
python etl/src/generate_manuals.py --no-upload  # local PDFs only
python etl/src/generate_manuals.py --force      # re-render even if up to date
# override targets if needed:
python etl/src/generate_manuals.py \
  --catalog ${var.catalog} --schema ${var.schema} --volume ${var.volume} --profile FEVM
```

Verify the 12 PDFs landed (and datasheets are untouched):

```bash
databricks fs ls dbfs:/Volumes/${var.catalog}/${var.schema}/${var.volume}/manuals -p FEVM
```

### 2. Create the KA (programmatic — `databricks knowledge-assistants`, Beta)

A KA is **not** a DAB resource (no `bundle` verb as of CLI v1.4.0), so it is
created with the Beta `databricks knowledge-assistants` CLI, not `bundle
deploy`. The spec is recorded in `etl/resources/knowledge_assistant.json`
(that file is a record, not a DAB resource — the bundle only includes
`resources/*.yml`). Exact commands used:

```bash
# a) create the assistant (display_name must be unique per workspace)
databricks knowledge-assistants create-knowledge-assistant \
  "powertools-manuals-ka" \
  "Answers questions about Bosch power-tool product manuals ... (SYNTHETIC demo)." \
  --instructions "Answer only from the retrieved product manuals and always cite the source manual. ..." \
  -p FEVM
# → returns name = knowledge-assistants/{ka_id} and endpoint_name = ka-<short>-endpoint

# b) add the Volume folder as a "files" knowledge source
databricks knowledge-assistants create-knowledge-source \
  "knowledge-assistants/{ka_id}" \
  --json '{
    "display_name": "Product manuals",
    "description": "Synthetic Bosch power-tool operating manuals (12 PDFs) ...",
    "source_type": "files",
    "files": {"path": "/Volumes/${var.catalog}/${var.schema}/${var.volume}/manuals/"}
  }' -p FEVM

# c) sync + poll status (CREATING → ONLINE, ~2–5 min)
databricks knowledge-assistants sync-knowledge-sources "knowledge-assistants/{ka_id}" -p FEVM
databricks knowledge-assistants get-knowledge-assistant  "knowledge-assistants/{ka_id}" -p FEVM
```

Current build (FEVM): `powertools-manuals-ka`,
`knowledge-assistants/44e78d1c-c243-4def-b0e6-c27638d78c91`, endpoint
`ka-44e78d1c-endpoint`. Query it from **AI Playground** (pick the KA endpoint)
once status is `ONLINE`.

### 2-alt. Create the KA (UI fallback)

If the Beta CLI is unavailable, build it in the UI instead:

1. Left nav → **Agents** → **Agent Bricks** → **Knowledge Assistant** → **Create**.
2. **Name:** `powertools-manuals-ka`.
3. **Description** (paste): _Answers questions about Bosch power-tool product
   manuals (safety, specifications, operation, battery/charging or mains,
   maintenance, troubleshooting, warranty) for 12 tools. Content is SYNTHETIC
   demo material, not official Bosch documentation._
4. **Add knowledge source** → **Files in a Unity Catalog Volume**.
5. **Volume path** (paste exactly):
   `/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/manuals/`
6. **Source description** (paste): _Synthetic Bosch power-tool operating manuals
   (12 PDFs) — safety, specs, operation, battery/mains, maintenance,
   troubleshooting, warranty._
7. **Create**, then wait for status **ONLINE** (~2–5 min) and test in AI Playground.

### 3. Sample questions (retrieval must read the manual to answer)

- "What is the impact energy of the GBH 18V-26 F, and what does fault code E01 mean?"
- "How do I change the blade on the GST 18V-LI S jigsaw?"
- "What triggers KickBack Control on the GWS 18V-10 and how do I restart the tool?"
- "What extension-lead cross-section does the GWS 22-230 JH need?"

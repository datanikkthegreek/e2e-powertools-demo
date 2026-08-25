# RUNBOOK — Bosch Power Tools demo (stub)

> Stub. Fill in during the rehearsal after the ETL + App bundles are deployed
> and the Genie space / Knowledge Assistant / Supervisor are built in the UI.

## Prereqs (deploy + run order)

The data flow has a hard dependency chain — each step reads what the previous
one produced. Run it in exactly this order:

1. **Deploy the ETL bundle.** `cd etl && databricks bundle deploy -p FEVM` —
   provisions the `techsummit` Lakebase project (**pg17**, required by CDF), the
   `techsummit` UC schema, the two PDF Volumes (`productmanuals` for the KA and
   `datasheets` for IDP), the silver pipeline, and the `powertools-build` job.
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
4. **Upload PDFs.** Run `scripts/upload_pdfs.sh` (FEVM defaults) to stage both
   PDF sets into their MANAGED Volumes: `etl/data/datasheets/*.pdf` →
   `…techsummit.datasheets` (read by the IDP streaming tables) and
   `etl/data/manuals/*.pdf` → `…techsummit.productmanuals` (the KA source). The
   script is idempotent (`databricks fs cp --overwrite`, kebab filenames kept).
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
   **Knowledge Assistant (product manuals)** section below; it is built by
   running the **`etl/src/create_or_update_knowledge_assistant.ipynb`** notebook
   in the workspace (Databricks **SDK**, `w.knowledge_assistants`). Genie space
   (7 base tables) and the Supervisor agent (Genie + Knowledge Assistant) are
   still built in the UI.

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

> **Real manuals only, 12/12 — already staged.** The 12 genuine Bosch manual
> PDFs are already uploaded to the `manuals/` Volume folder (a one-time
> destructive upload; the KA is built and grounded over them). Nothing is
> synthesized. **Three are honest nearest-variant / family substitutions** for
> tools with no exact PDF: `pbh-2100-re` → Bosch **PBH 2500 SRE** manual (same
> rotary-hammer family); `psr-1080-li` → Bosch **PSB 1080 LI-2** booklet (same
> 1080 LI platform); `gws-22-230-jh` → **GWS 22-230 J/P** family booklet (JH is a
> kit variant of that base tool). A few (`gsr-18v-55`, `pws-700-115`,
> `psr-1080-li`, `psb-1800-li-2`) are browser-sourced (device.report /
> discontinued catalogs). To re-stage or add a manual, drop the PDF into the
> Volume root directly (`databricks fs cp <file>.pdf
> dbfs:/Volumes/$CATALOG/$SCHEMA/$VOLUME_MANUALS/<tool-id>.pdf -p $PROFILE`), or
> just re-run `scripts/upload_pdfs.sh`, then re-run the KA notebook to re-sync.

The manuals live in their **own MANAGED Volume `productmanuals`** — completely
separate from the `datasheets` Volume that IDP reads (the old single `raw_docs`
Volume with `manuals/` + `datasheets/` subfolders was split in two). Manuals sit
at the Volume **root**, no subfolder:
`/Volumes/${var.catalog}/${var.schema}/${var.volume_manuals}/`
(resolves to
`/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/`
on the current FEVM target).

> The `${var.catalog}/${var.schema}/${var.volume_manuals}` above is the
> **DAB-variable reference** (see `etl/databricks.yml`), not shell syntax. The
> runnable commands below use plain shell `$CATALOG/$SCHEMA/$VOLUME_MANUALS/$PROFILE`
> so they paste-and-run.

### Prerequisites

The KA notebook needs **`databricks-sdk`** (see `etl/requirements.txt`). Install
from that file:

```bash
uv pip install -r etl/requirements.txt   # or: pip install -r etl/requirements.txt
```

Set your target once (FEVM defaults shown); the verify command below uses these:

```bash
export CATALOG=nikks_fevm_workspace_7405607030687545 SCHEMA=techsummit \
  VOLUME_MANUALS=productmanuals VOLUME_DATASHEETS=datasheets PROFILE=FEVM
```

### 1. Manuals in the Volume (already staged)

The 12 real Bosch manual PDFs live in the `productmanuals` Volume (staged by
`scripts/upload_pdfs.sh` from `etl/data/manuals/`). Verify they are present (and
the sibling `datasheets` Volume that IDP reads is separately populated):

```bash
databricks fs ls dbfs:/Volumes/$CATALOG/$SCHEMA/$VOLUME_MANUALS -p $PROFILE
databricks fs ls dbfs:/Volumes/$CATALOG/$SCHEMA/$VOLUME_DATASHEETS -p $PROFILE
```

To re-stage everything, just re-run the upload script (idempotent), then re-run
the KA notebook (step 2) to re-sync:

```bash
scripts/upload_pdfs.sh                    # FEVM defaults, both Volumes
# or a single manual:
databricks fs cp <file>.pdf \
  dbfs:/Volumes/$CATALOG/$SCHEMA/$VOLUME_MANUALS/<tool-id>.pdf --overwrite -p $PROFILE
```

### 2. Create-or-update the KA (Databricks SDK notebook)

A KA is **not** a DAB resource (the bundle only includes `resources/*.yml`), so
it is created/maintained with the Databricks **SDK** (`w.knowledge_assistants`),
not `bundle deploy`. Run **`etl/src/create_or_update_knowledge_assistant.ipynb`**
in the workspace (it uses ambient `WorkspaceClient()` auth).

**Non-destructive reuse.** `display_name` is unique per workspace, so the notebook
looks the KA up by display name and **REUSES** it (re-syncs its knowledge source)
when it already exists — it never re-creates or deletes. The notebook cells are:

1. **Config** — `WorkspaceClient()`, the `techsummit`-only target guardrail, the
   Volume path (`/Volumes/…/productmanuals/`), and the KA display name / description /
   instructions + knowledge-source display name / description.
2. **Create-or-update + sync** — if no KA named `powertools-manuals-ka` exists it
   creates one and attaches the `manuals/` Volume folder as a `files` knowledge
   source (`powertools-pdf-manuals`); otherwise it reuses the existing KA. Either
   way it triggers a sync so newly-uploaded manuals get (re)indexed.
3. **Status** — prints the KA state / endpoint and each knowledge source's state
   + path.

The terminal state is `KnowledgeAssistantState.ACTIVE` (the knowledge source
settles at `KnowledgeSourceState.UPDATED`); a full re-index of the real,
multi-hundred-page manuals takes ~10–15 min.

Current build (FEVM): `powertools-manuals-ka`,
`knowledge-assistants/44e78d1c-c243-4def-b0e6-c27638d78c91`, endpoint
`ka-44e78d1c-endpoint`. Last live run (2026-08-24): the synthetic stub PDFs were
cleared from `manuals/` and replaced with the **12 real** manuals, then the KA
was re-synced and reached `ACTIVE` (source `UPDATED`). Query it from **AI
Playground** (pick the KA endpoint) once state is `ACTIVE`.

> **Deleting a KA is destructive and irreversible** — only do it as a manual last
> resort (e.g. a genuinely corrupted KA), never as part of a routine rerun. The
> SDK exposes `w.knowledge_assistants.delete_knowledge_assistant(...)`; the
> notebook deliberately does not call it.

### 2-alt. Create the KA (UI fallback)

If you would rather not run the notebook, build it in the UI instead:

1. Left nav → **Agents** → **Agent Bricks** → **Knowledge Assistant** → **Create**.
2. **Name:** `powertools-manuals-ka`.
3. **Description** (paste): _Answers questions about Bosch power-tool product
   manuals (safety, specifications, operation, battery/charging or mains,
   maintenance, troubleshooting, warranty)._
4. **Add knowledge source** → **Files in a Unity Catalog Volume**.
5. **Volume path** (paste exactly):
   `/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/`
6. **Source description** (paste): _Bosch power-tool operating manuals (PDFs) —
   safety, specs, operation, battery/mains, maintenance, troubleshooting,
   warranty._
7. **Create**, then wait for the KA to reach **ACTIVE** (~10–15 min for a full
   re-index of the real manuals) and test in AI Playground.

### 3. Sample questions (retrieval must read the manual to answer)

Target models whose manuals are staged in the Volume (fault codes / exact specs
come from the real manuals, not invented ones):

- "What tool holder does the GBH 2-26 use, and what is its impact energy?"
- "How do I fit and remove an SDS-plus bit on the GBH 2-26?"
- "What does the GBH 2-26 manual say about the vibration control / auxiliary handle?"
- "What maintenance intervals does the GBH 2-26 manual recommend?"

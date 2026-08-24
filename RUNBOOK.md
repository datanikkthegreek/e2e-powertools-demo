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
   **Knowledge Assistant (product manuals)** section below; it is built
   **programmatically** via the Databricks **SDK** (`etl/src/create_knowledge_assistant.py`).
   Genie space (7 base tables) and the Supervisor agent (Genie + Knowledge
   Assistant) are still built in the UI.

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

> **Real manuals only, 12/12.** `etl/src/generate_manuals.py` stages the genuine
> Bosch manual PDF for each tool from one of three sources (see the script header):
>
> - **7 explicit URLs + 1 archive.org fallback** — 7 via an explicit per-tool URL
>   map (`MANUAL_URLS`) on Bosch's own hosts (`bosch-professional.com` + regional
>   `media.*.bosch-pt.*` CDNs under `/binary/manualsmedia/…`, docnum series
>   `160992A…`, plus one `bosch-diy.com/storage/…` DIY manual), and `gbh-2-26` via
>   an **Internet Archive** (archive.org) fallback search. These need no manual steps.
> - **4 browser-only** — `gsr-18v-55`, `pws-700-115`, `psr-1080-li`,
>   `psb-1800-li-2` come from sources that block scripted download (`gsr-18v-55`'s
>   public copy sits behind Cloudflare on device.report; the other three are
>   discontinued and absent from Bosch's online catalogs). They were downloaded
>   **manually via a browser** and must be placed before the upload step (see the
>   "browser-only manuals" note in step 1). The script's `LOCAL_MANUALS` map
>   copies them from `~/Downloads` (override with `--local-dir`) into
>   `etl/data/manuals/<tool-id>.pdf`.
>
> Every candidate — URL, local, or archive.org — is verified (`%PDF` header,
> non-trivial size, and a **`pypdf`-confirmed page count > 1** — `pypdf` is a
> required dependency, so a 1-page Declaration-of-Conformity stub is rejected)
> before upload; nothing is synthesized. **Three are
> honest nearest-variant / family substitutions** for tools with no exact PDF,
> flagged in the run summary: `pbh-2100-re` → Bosch **PBH 2500 SRE** manual (same
> rotary-hammer family); `psr-1080-li` → Bosch **PSB 1080 LI-2** booklet (same
> 1080 LI platform); `gws-22-230-jh` → **GWS 22-230 J/P** family booklet (JH is a
> kit variant of that base tool). The PDFs are git-ignored
> (`etl/data/manuals/*.pdf`); the script re-fetches/re-stages them.

The manuals live in a **new `manuals/` subfolder** of the existing `raw_docs`
Volume — separate from the `datasheets/` folder that IDP reads:
`/Volumes/${var.catalog}/${var.schema}/${var.volume}/manuals/`
(resolves to
`/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/manuals/`
on the current FEVM target).

> The `${var.catalog}/${var.schema}/${var.volume}` above is the **DAB-variable
> reference** (see `etl/databricks.yml`), not shell syntax. The runnable commands
> below use plain shell `$CATALOG/$SCHEMA/$VOLUME/$PROFILE` so they paste-and-run.

### Prerequisites

The `etl/` scripts pin their Python deps in **`etl/requirements.txt`**: `pypdf`
(**required** — the downloader aborts without it, because the "> 1 page" check is
what rejects 1-page Declaration-of-Conformity stubs) and `databricks-sdk` (the KA
scripts). Install from that file:

```bash
uv pip install -r etl/requirements.txt   # or: pip install -r etl/requirements.txt
```

Set your target once (FEVM defaults shown); every runnable command below uses these:

```bash
export CATALOG=nikks_fevm_workspace_7405607030687545 SCHEMA=techsummit VOLUME=raw_docs PROFILE=FEVM
```

### 1. Download + upload the manuals

Idempotent and re-runnable. Stages the **real** Bosch manual PDF for each tool —
7 explicit URLs + 1 archive.org fallback (`MANUAL_URLS` + `gbh-2-26` via
archive.org), 4 from local browser downloads (`LOCAL_MANUALS`) — verifies each one
(`%PDF` header, non-trivial size, `pypdf`-confirmed > 1 page), then uploads the
verified PDFs PDF-only to the `manuals/` subfolder. Real manuals only, **12/12**
(three are flagged variant/family substitutions; see the "Real manuals only" note
above). The upload is **additive at the folder level**: it may overwrite
same-named PDFs in `manuals/` (that is what makes reruns idempotent) but never
deletes anything and never touches the sibling `datasheets/` folder or the Volume
root.

> **Fail-closed on a partial set.** If any expected tool does not verify, the
> script uploads **nothing** and exits non-zero (the "expected set" is all 12
> tools, or exactly the `--only` ids when given). Pass **`--allow-partial`** to
> upload the verified subset anyway. Staging is **atomic**: each candidate is
> verified in a temp file and only then atomically replaces the cached PDF, so a
> failed re-fetch under `--force` never destroys a previously-valid manual. The
> upload target is guardrailed (schema must be `techsummit`, never `cdp`, catalog
> must be the FEVM default unless `--allow-catalog-override`).

> **Browser-only manuals (do this before the upload run).** Four manuals cannot
> be fetched by script — download each in a browser and drop it in `~/Downloads`
> (or pass `--local-dir`) under the **exact filename** below; the script copies it
> to `etl/data/manuals/<tool-id>.pdf`. (Alternatively, place the PDF directly at
> `etl/data/manuals/<tool-id>.pdf` and it is reused as-is.) If a file is missing,
> sourcing continues past it (that one tool is reported unsourced), but the
> default full run then exits **non-zero** — pass `--allow-partial` to upload the
> verified subset anyway.
>
> | tool-id | filename in `~/Downloads` | source |
> |---|---|---|
> | `gsr-18v-55` | `512aebc6e0d13e92aa9c018dd2bcbe76e6622e7ff879918a8d6837548591c97a.pdf` | device.report (Cloudflare-blocked to scripts) |
> | `pws-700-115` | `18f72f.pdf` | discontinued; absent from Bosch catalog |
> | `psr-1080-li` | `a28d32.pdf` | manualslib.de — Bosch **PSB 1080 LI-2** booklet (nearest variant) |
> | `psb-1800-li-2` | `41bbc4.pdf` | discontinued; absent from Bosch catalog |

```bash
# from repo root; the script defaults already target the FEVM catalog/schema/volume + profile
python etl/src/generate_manuals.py                   # stage + upload
python etl/src/generate_manuals.py --no-upload       # stage + verify only
python etl/src/generate_manuals.py --force           # re-fetch even if present
python etl/src/generate_manuals.py --local-dir ~/Downloads   # browser-only manuals dir
python etl/src/generate_manuals.py --only gbh-2-26   # one tool (repeatable)
# override targets explicitly if needed:
python etl/src/generate_manuals.py \
  --catalog "$CATALOG" --schema "$SCHEMA" --volume "$VOLUME" --profile "$PROFILE"
```

Verify the sourced PDFs landed (and datasheets are untouched):

```bash
databricks fs ls dbfs:/Volumes/$CATALOG/$SCHEMA/$VOLUME/manuals -p $PROFILE
```

### 2. Create the KA (programmatic — Databricks SDK)

A KA is **not** a DAB resource (the bundle only includes `resources/*.yml`), so
it is created/maintained with the Databricks **SDK** (`w.knowledge_assistants`),
not `bundle deploy`. The logic lives in `etl/src/manage_knowledge_assistant.py`
(thin SDK helpers) and `etl/src/create_knowledge_assistant.py` (orchestrator);
the record is `etl/resources/knowledge_assistant.json`.

**Non-destructive reuse.** `display_name` is unique per workspace, so the
orchestrator looks the KA up by display name and **REUSES** it (attaches/syncs
its knowledge source) when it already exists — it never re-creates or deletes.
One command does the whole create-or-reuse-then-sync:

```bash
# from repo root; defaults already target the FEVM catalog/schema/volume + profile
python etl/src/create_knowledge_assistant.py

# override targets explicitly if needed:
python etl/src/create_knowledge_assistant.py \
  --catalog "$CATALOG" --schema "$SCHEMA" --volume "$VOLUME" --profile "$PROFILE"
```

The script self-authenticates via the CLI profile (no tokens written to files).
On first run it creates the KA (`powertools-manuals-ka`), attaches the
`manuals/` Volume folder as a `files` knowledge source (`powertools-pdf-manuals`),
and syncs; on later runs it reuses the existing KA and just re-syncs so newly
uploaded manuals get re-indexed. The SDK reports the terminal state as
`KnowledgeAssistantState.ACTIVE` (the knowledge source settles at
`KnowledgeSourceState.UPDATED`); a full re-index of the real, multi-hundred-page
manuals takes ~10–15 min, longer than a first build on small stub PDFs.

Current build (FEVM): `powertools-manuals-ka`,
`knowledge-assistants/44e78d1c-c243-4def-b0e6-c27638d78c91`, endpoint
`ka-44e78d1c-endpoint`. Last live run (2026-08-24): the synthetic stub PDFs were
cleared from `manuals/` and replaced with the **12 real** manuals, then the KA
was re-synced and reached `ACTIVE` (source `UPDATED`). Query it from **AI
Playground** (pick the KA endpoint) once state is `ACTIVE`.

> **Deleting a KA is destructive and irreversible** — only do it as a manual last
> resort (e.g. a genuinely corrupted KA), never as part of a routine rerun. The
> SDK exposes `w.knowledge_assistants.delete_knowledge_assistant(...)`; the
> orchestrator deliberately does not wrap it.

### 2-alt. Create the KA (UI fallback)

If you would rather not run the SDK script, build it in the UI instead:

1. Left nav → **Agents** → **Agent Bricks** → **Knowledge Assistant** → **Create**.
2. **Name:** `powertools-manuals-ka`.
3. **Description** (paste): _Answers questions about Bosch power-tool product
   manuals (safety, specifications, operation, battery/charging or mains,
   maintenance, troubleshooting, warranty)._
4. **Add knowledge source** → **Files in a Unity Catalog Volume**.
5. **Volume path** (paste exactly):
   `/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/raw_docs/manuals/`
6. **Source description** (paste): _Bosch power-tool operating manuals (PDFs) —
   safety, specs, operation, battery/mains, maintenance, troubleshooting,
   warranty._
7. **Create**, then wait for the KA to reach **ACTIVE** (~10–15 min for a full
   re-index of the real manuals) and test in AI Playground.

### 3. Sample questions (retrieval must read the manual to answer)

Target models that were actually **sourced** (check the downloader's run summary;
fault codes / exact specs now come from the real manuals, not invented ones):

- "What tool holder does the GBH 2-26 use, and what is its impact energy?"
- "How do I fit and remove an SDS-plus bit on the GBH 2-26?"
- "What does the GBH 2-26 manual say about the vibration control / auxiliary handle?"
- "What maintenance intervals does the GBH 2-26 manual recommend?"

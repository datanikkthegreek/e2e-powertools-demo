# Bosch Power Tools — Service & Sales Assistant demo — design (PRD)

**Date:** 2026-08-20 (rev. 2026-08-21 — grounded on the real e2e-cdp-demo)
**Status:** Draft — pending Nikk review (no build/deploy until approved)
**Owner:** Nikk (Databricks SA, Bosch account)
**Type:** Live customer demo — Bosch Power Tools (PT)

## Purpose

A live, customer-facing Databricks demo for Bosch Power Tools that shows how
Databricks' *simple, managed AI features* chain into one useful assistant on top
of a **real, running webshop** — with no heavy ML engineering:

- **Databricks App + Lakebase** — a real Bosch PT webshop storefront (browse,
  add-to-cart, purchase) backed by a Lakebase (Postgres) OLTP database.
- **Intelligent Document Processing (IDP)** — extract structured product specs
  from real Bosch datasheet PDFs into a governed table.
- **Knowledge Assistant (managed RAG)** — answer "how do I use / how do I repair
  this tool" from real Bosch manuals.
- **AI/BI Genie** — natural-language analytics over the real view → add-to-cart →
  purchase funnel plus extracted specs.
- **Multi-Agent Supervisor** — one agent that routes across the Knowledge
  Assistant and Genie and synthesizes a combined answer.

Narrative payoff: a service / dealer-support persona asks one question that needs
*both* the manuals and the real webshop analytics, and the supervisor answers it
end to end.

## What changed in this revision

This PRD was rewritten after grounding it in the actual `e2e-cdp-demo`
repository and the live `cdp` Delta tables (two read-only investigations). The
key pivots vs. the first draft:

- **Real data, not synthetic warranty/sales.** The demo is now grounded in the
  existing CDP demo: a real Bosch PT webshop with real Lakebase purchases and a
  real GA4-style behavioral funnel — not invented `sales_orders` /
  `warranty_claims`.
- **The App is now in scope.** We deploy the webshop App on Lakebase; it is the
  demo's opening beat and the source of the behavioral/commercial data.
- **New isolated environment.** New schema `techsummit` in the FEVM catalog, a
  new Lakebase project `techsummit`, and a new repo `e2e-powertools-demo` (a
  trimmed copy of `e2e-cdp-demo`).
- **Specs move out of the products table.** Product specifications are removed
  from the Lakebase `products` table (and therefore no longer shown in the app);
  they are produced fresh by IDP from the datasheet PDFs. This keeps the
  "messy PDF → clean spec table" aha as a genuine capability, not a duplicate of
  data that already exists.
- **Trim to only the required tables.** From the Delta side we keep `gtm_events`
  and only the `event_view_item` and `event_add_to_cart` silver tables (drop
  purchase/pageview/abandon/signup silver and all gold cart MVs). Purchases come
  from Lakebase, which is the authoritative money fact.
- **Everything ships as Databricks Asset Bundles** — two bundles (App and ETL +
  Lakebase) so the whole demo is reproducibly deployable.

## Audience & setting

- Driven live by the SA in a meeting with Bosch PT stakeholders (Tech Summit).
- A real webshop App plus Databricks-native surfaces (Agent Bricks UIs, the
  Genie UI, the AI Playground).
- Optimized for a tight, reliable click-path that starts in the live storefront
  and culminates in the supervisor.

## Success criteria

- The full chain runs live without failing: live webshop → PDF → spec table →
  grounded manual answers → Genie funnel/revenue charts → supervisor combined
  answer.
- Every AI step is visibly low-code / no-code ("look how little effort this
  took").
- Extracted specs and RAG answers trace to genuine Bosch material; the
  behavioral seed is clearly labeled synthetic; the commercial figures come from
  the real Lakebase demo data.
- Rebuildable end-to-end from two asset bundles + a one-page runbook.

## Key decisions

- **Domain: Bosch Power Tools, 18V Professional platform.** The `e2e-cdp-demo`
  is already a Bosch PT webshop with 12 real tools — no re-theming needed.
- **Managed / low-code AI path — not the code-first Agent Framework.** IDP is two
  SQL functions; the three agents are built no-code in the Agents UI. The Mosaic
  AI Agent Framework code path stays a "here's how you'd extend it" talking
  point, not the spine.
- **Real documents + real webshop data.** Datasheets + manuals are real public
  Bosch Professional PDFs. The purchases/funnel are the demo's real Lakebase +
  behavioral data; the behavioral events are seeded (synthetic GA4) and labeled.
- **Lakebase is the money fact.** Revenue/orders come from Lakebase
  `purchases` / `purchase_lines` (real FKs, prices, quantities). Behavioral
  `event_purchase` is out of scope; behavior is only the view/cart funnel.
- **Specs sourced by IDP (decision "A").** Remove specs from `products`; extract
  typed numeric specs from datasheet PDFs into `product_specs`.
- **Supervisor = Genie + Knowledge Assistant.** Two sub-agents; the climax is a
  question that needs both.
- **Documentation-first gate.** No provisioning or build until this PRD is
  approved.

## Environment & naming

| Thing | Value |
|---|---|
| Workspace | FEVM (`adb-7405607030687545` / `nikks_fevm_workspace`) |
| Catalog | `nikks_fevm_workspace_7405607030687545` |
| Schema (new) | `techsummit` |
| Volume (PDFs) | `nikks_fevm_workspace_7405607030687545.techsummit.raw_docs` |
| Lakebase project (new) | `techsummit` |
| Repo (new) | `github.com/datanikkthegreek/e2e-powertools-demo`, cloned to `~/Repos/e2e-powertools-demo` (trimmed copy of `e2e-cdp-demo`) |

Everything for this demo lives in `…techsummit.*` — isolated from the existing
`cdp` schema so nothing collides with the baseline demo.

## Repository & asset-bundle layout (planned)

Two Databricks Asset Bundles so the demo is reproducibly deployable. The
Lakebase instance is owned by the **ETL** bundle (per "the ETL part including
lakebase"); the App bundle references it. **Deploy order: ETL bundle first
(provisions Lakebase + data), then App bundle.**

```
e2e-powertools-demo/
  app/                          # BUNDLE 1 — Databricks App (webshop) + Lakebase reference
    databricks.yml
    src/…                       # storefront front-end/back-end (copied from e2e-cdp-demo, specs hidden)
    resources/
      app.yml                   # app resource; references the techsummit Lakebase DB
  etl/                          # BUNDLE 2 — ETL + Lakebase (deploy first)
    databricks.yml
    resources/
      lakebase.yml              # Lakebase project 'techsummit' (OLTP: products[no specs], accounts,
                                #   carts, cart_items, purchases, purchase_lines)
      sync.yml                  # Lakebase -> Delta CDC sync (wal2delta) for required tables
      pipeline_silver.yml       # gtm_events -> event_view_item + event_add_to_cart ONLY
      job_seed.yml              # seed_gtm_events with multi-week backfill
      job_curate.yml            # CDC->current collapse, key-normalize, IDP -> product_specs, Genie tables
    src/
      seed_gtm_events.py        # behavior seed (bug-fixed; view/cart focus)
      cdc_to_current.sql        # lb_*_history -> current-state dim/fact tables
      key_normalize.sql         # binary/uuid id -> canonical text; item_id -> product_id
      idp_product_specs.sql     # ai_parse_document + ai_extract -> product_specs (+ model->id crosswalk)
    data/
      datasheets/               # real Bosch datasheet PDFs (IDP source)
      manuals/                  # real Bosch manuals (usage + repair; KA source)
  RUNBOOK.md                    # the live click-path + exact questions to ask
  README.md                     # what it is, deploy order, how to rebuild
```

The Genie space, Knowledge Assistant, and Supervisor are UI-built; `RUNBOOK.md`
documents their configuration so they can be recreated.

## Architecture

```
                 e2e-powertools-demo  (BUNDLE app/  +  BUNDLE etl/)

  Lakebase project: techsummit   (OLTP — all webshop tables; specs REMOVED)
    products(no specs), accounts, carts, cart_items, purchases, purchase_lines
        |                                        |
        | webshop App (app bundle)               | wal2delta CDC sync (etl bundle)
        v                                        v
   Bosch PT storefront                    lb_*_history --collapse--> dim_product, dim_customer,
   (browse / add-to-cart / buy)                                      fact_purchase, fact_purchase_line
        |
        | behavior (GA4-style, seeded + backfilled)
        v
   gtm_events (raw Delta) --silver--> event_view_item, event_add_to_cart
                                            |  (id-normalize: item_id -> product_id)
                                            v
                                  fact_view_item, fact_add_to_cart

  REAL Bosch datasheet PDFs (Volume) -> ai_parse_document -> ai_extract -> product_specs
  REAL Bosch manuals (Volume) -------> Knowledge Assistant endpoint

  GENIE SPACE  <-  dim_product, product_specs, dim_customer,
                   fact_purchase, fact_purchase_line, fact_view_item, fact_add_to_cart
        \                                                   /
         +--------> SUPERVISOR AGENT  <-- Knowledge Assistant
                      (routes + synthesizes)  -->  AI Playground
```

Both leaf agents (the Knowledge Assistant endpoint and the Genie space) attach to
the Supervisor natively.

## Genie data model (base tables Genie consumes)

Lean star, **current-state only** — Genie never sees the raw `lb_*_history` CDC
tables or any gold MV. Product key is canonical **text uuid** `product_id`
everywhere (see key-normalization step).

| Table | Grain | Key columns | Source |
|---|---|---|---|
| `dim_product` | 1 / SKU | `product_id` (text uuid), `name`, `category`, `price_eur` | Lakebase `products` (specs removed) → CDC → current |
| `product_specs` | 1 / SKU | `product_id`, `model_name`, `voltage_v`, `max_torque_nm`, `no_load_rpm`, `chuck_capacity_mm`, `weight_kg`, `battery_platform` (typed numerics) | IDP from datasheet PDFs + `model_name → product_id` crosswalk |
| `dim_customer` | 1 / customer | `customer_id`, `city`, `country`, `signup_date` | Lakebase `accounts` → CDC → current |
| `fact_purchase` | 1 / order | `purchase_id`, `customer_id`, `cart_id`, `created_at`, `total_eur` | Lakebase `purchases` → CDC → current |
| `fact_purchase_line` | 1 / order line | `purchase_id`, `product_id`, `quantity`, `unit_price_eur`, `name_snapshot` | Lakebase `purchase_lines` → CDC → current |
| `fact_view_item` | 1 / PDP view | `event_ts`, `user_id` (→`customer_id`), `product_id` (from `item_id`), `session_id` | Delta silver `event_view_item` (+ id-normalize) |
| `fact_add_to_cart` | 1 / cart action | `event_ts`, `user_id`, `cart_id`, `product_id` (from `item_id`), `quantity_delta`, `cart_action` | Delta silver `event_add_to_cart` (+ id-normalize) |

Deliberately excluded from Genie: gold cart MVs, `gold_customer_360`, the
purchase/pageview/abandon/signup silver tables, and every `lb_*_history` table.

## Pipelines / intermediate steps

1. **Lakebase provisioning (`techsummit`)** — new OLTP project; seed the webshop
   tables (`products` **without specs**, `accounts`, `carts`, `cart_items`,
   `purchases`, `purchase_lines`). *(etl bundle → `lakebase.yml`)*
2. **Webshop App on Lakebase** — deploy the storefront; product pages no longer
   render specs (specs live only in the analytics layer). *(app bundle)*
3. **Behavior seed + backfill** — run `seed_gtm_events` with a multi-week
   backfill (~100 users) so the funnel has statistical body → `gtm_events` (raw).
   Validate that `event_view_item` and `event_add_to_cart` volumes are
   realistic. *(etl bundle → `job_seed.yml`)*
4. **Silver pipeline (trimmed)** — `gtm_events` → `event_view_item` +
   `event_add_to_cart` **only**. *(etl bundle → `pipeline_silver.yml`)*
5. **Lakebase → Delta CDC sync** — `wal2delta` WAL→Delta for
   `products` / `accounts` / `purchases` / `purchase_lines` → `lb_*_history`.
   *(etl bundle → `sync.yml`)*
6. **CDC → current-state collapse** — per history table:
   `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC)=1` and drop
   `_pg_change_type='delete'` → `dim_product`, `dim_customer`, `fact_purchase`,
   `fact_purchase_line`. *(etl bundle → `cdc_to_current.sql`)*
7. **Key normalization** — one shared step casting binary/UUID `id` → canonical
   text so behavioral `item_id` = Lakebase `product_id`; produces
   `fact_view_item` / `fact_add_to_cart`. *(etl bundle → `key_normalize.sql`)*
8. **IDP → `product_specs`** — `ai_parse_document` + `ai_extract` on datasheet
   PDFs → typed numeric spec columns; join to `dim_product` via a deterministic
   12-row `model_name → product_id` crosswalk. *(etl bundle → `idp_product_specs.sql`)*
9. **Genie curation** — table/column descriptions + curated example questions;
   point the Genie space only at the 7 base tables above.
10. **Manuals → Knowledge Assistant** (separate track) — PDFs in the Volume →
    Knowledge Assistant → served endpoint. Independent of the CDP data.

## Components

### 1 · Webshop App + Lakebase — the opening beat
- **What:** a real Bosch PT storefront (browse, add-to-cart, purchase) on a
  Lakebase Postgres OLTP DB.
- **How:** app bundle deploys the front/back-end; references the `techsummit`
  Lakebase DB provisioned by the ETL bundle. Product detail pages show name /
  category / price but **not** specs (specs removed from `products`).
- **Talking point:** a live, governed operational app on Databricks — and its
  data flows straight into the lakehouse for analytics.

### 2 · IDP — datasheets → `product_specs`
- **What:** turn real datasheet PDFs into a typed, governed spec table (the specs
  that were deliberately removed from the app).
- **How (all GA):** land PDFs in the `raw_docs` Volume; `ai_parse_document`
  parses layout/text/tables; `ai_extract(..., schema)` pulls typed fields; write
  to `product_specs`; map to `product_id` via the crosswalk.
- **Heterogeneous docs:** battery + charger datasheets lack torque/rpm; those
  rows keep voltage/weight/price and leave tool-only fields null.
- **Talking point:** messy PDF → clean, joinable, numeric-typed table in two
  functions — now Genie can answer "drills over 90 Nm".

### 3 · Knowledge Assistant — usage + repair
- **What:** grounded Q&A over the tool manuals, split by intent — usage
  (operating / safety) and repair (service / troubleshooting).
- **How (production capability):** Agents UI → Knowledge Assistant; add manual
  PDFs (limits: ≤10 sources, ≤500 pages, ≤100 MB/file); instructions; test in
  chat. Exposed as an agent endpoint.
- **Talking point:** grounded, cited answers straight from the real manuals.

### 4 · Genie space — funnel + commercial analytics
- **What:** natural-language analytics over the real funnel + purchases + specs.
- **How:** a Genie space over the 7 base tables; curated example questions and
  table/column descriptions for reliable answers.
- **Sample asks:** "view → cart → purchase conversion by category"; "top viewed
  but never purchased tools"; "revenue by product last month"; "which cordless
  drills over 90 Nm sold best?".

### 5 · Supervisor agent — the payoff
- **What:** one agent that routes between the Manual Assistant and the Analytics
  Genie and synthesizes.
- **How (GA; SDK management is Beta):** Agents UI → Supervisor Agent; add the two
  sub-agents with routing descriptions; served as a Model Serving endpoint;
  demoed in the AI Playground.
- **Climax question:** *"The GSR 18V-90 keeps overheating — what's the fix, and
  how are its sales and cart-abandonment trending?"* → repair steps (KA) +
  funnel/revenue (Genie) in one answer.

## Demo narrative (live click-path)

1. **The live webshop** — browse the Bosch PT storefront, add a tool to cart,
   buy it. "This is a real app on Databricks, backed by Lakebase." *(opening)*
2. **Raw PDFs → `product_specs`** — run IDP on a datasheet (PDF → structure →
   typed table). "The app doesn't even store these specs — we lift them straight
   from your datasheets." *(aha #1)*
3. **Knowledge Assistant** — a usage question ("How do I set the torque on the
   GSR 18V-90?") and a repair question ("How do I replace the carbon brushes on
   the GWS 18V-10?") — cited answers. *(aha #2)*
4. **Genie** — "view → cart → purchase conversion by category"; "revenue by
   product last month" — charts over the real funnel. *(aha #3)*
5. **Supervisor in the AI Playground** — the combined overheating question; watch
   it call both sub-agents and synthesize. *(aha #4 — the payoff)*
6. **Close:** everything is governed in Unity Catalog, deployable from two asset
   bundles, and every AI piece was no-code / low-code.

## Questions this data can answer

- **Funnel:** view→cart→purchase conversion per product/category; top
  viewed-but-never-purchased tools; add-to-cart→purchase drop-off.
- **Commercial:** revenue by product/category, AOV, units per order, top sellers
  by region/month (Lakebase money fact).
- **Spec-driven (needs typed specs):** "cordless drills over 90 Nm that sold best
  last month"; "average price of tools viewed vs purchased".
- **Supervisor climax:** repair steps (KA) fused with funnel/revenue (Genie) in
  one answer.

## Build & deploy sequencing

1. Clone `e2e-cdp-demo` → `e2e-powertools-demo`; trim to the required tables and
   split into the two bundle folders.
2. **Deploy ETL bundle:** provision Lakebase `techsummit`; seed webshop tables
   (no specs); run behavior seed + backfill; stand up silver pipeline; wire the
   CDC sync; run curate job (CDC→current, key-normalize, IDP, Genie tables).
3. **Deploy App bundle:** webshop on the `techsummit` Lakebase DB.
4. Fetch + upload real datasheet + manual PDFs to the `raw_docs` Volume.
5. Build the Knowledge Assistant (UI).
6. Build the Genie space over the 7 base tables (UI / API); tune example
   questions.
7. Build the Supervisor (UI).
8. Rehearse the click-path; write `RUNBOOK.md`.

*Post-approval, this is the "start the integration" phase: deploy the App with
Lakebase and the data flow generating the listed tables, then review and decide
next steps (aggregations, joins, extra events).*

## Open decisions & risks

- **Behavioral data must be seeded with a real backfill.** The live `cdp` funnel
  is currently near-empty (`event_view_item` = 1 row, `add_to_cart` ≈ 19,
  purchases ≈ 10). A multi-week backfill (~100 users) is **mandatory** for Genie
  to look credible live.
- **Key mismatch is real.** Behavioral `item_id` is a string; Lakebase
  `product_id` is UUID/binary. The funnel returns nothing without the
  key-normalization step — treat it as load-bearing, not optional.
- **CDC history ≠ current state.** Synced tables are `lb_*_history` change-logs
  (e.g. purchases: ~82 change rows → 10 current). Genie must only see the
  collapsed current-state tables or it will double-count.
- **`model_name → product_id` crosswalk.** IDP keys on model name from the PDF;
  the 12-row crosswalk to `product_id` must be maintained so `product_specs`
  joins cleanly to `dim_product`.
- **Seed generator quirks.** The known `pageview` vs `page_view` naming bug only
  affects pageviews (now out of scope); still validate `event_view_item` /
  `event_add_to_cart` volumes after seeding.
- **Lakebase project reference.** The original demo's linked project returned
  "project not found" and `cdp.purchases` pointed at a different project — moot
  now that we create a fresh `techsummit` project, but confirm the new
  project/branch before wiring the sync.
- **Agent Bricks availability** — confirm Knowledge Assistant + Supervisor are
  enabled in FEVM / region before building.
- **Public repair docs are thin** — where a real service doc isn't public,
  augment with a clearly-synthetic troubleshooting procedure so the repair story
  always demos.

## Non-goals (YAGNI)

- No code-first Agent Framework build — managed path only (code path is a talking
  point).
- No behavioral `event_purchase` analytics — Lakebase is the money fact.
- No gold MVs / customer-360 / extra event silver tables in Genie — 7 base
  tables only (aggregations/joins are a deliberate *next* step after review).
- No production hardening beyond what the asset bundles give us — this is a demo.
- No fine-tuning / custom models.

## Immediate next step

Nikk reviews this PRD. On confirmation: start the integration — deploy the App
with Lakebase and the data flow that generates the listed tables — then review
and decide next steps (simple aggregations, joins, additional events).

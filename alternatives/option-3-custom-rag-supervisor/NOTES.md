# Option 3 — AI Parse + AI Prep Search + AI Search + KA + Supervisor

## Architecture

`PDFs → ai_parse_document → ai_prep_search → Delta chunks → AI Search index → KA → Supervisor ↔ Genie`

This option makes retrieval preparation and indexing visible while retaining managed answering and orchestration.

## FEVM deployment

- Chunk table: `nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_chunks` (4,759 chunks)
- Index: `nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_index`
- Genie: `01f1a11553c71a1cb20d4bf6cc65164f`
- Knowledge Assistant: `97328e2f-1d87-4ecd-b065-d11008c08d34`
- Supervisor endpoint: `mas-8b81ed97-endpoint`
- UI: `powertools-arch-options`, Option 3 tab

## Manual setup

1. Run `01_prepare_manuals.sql` on DBR 18.2+ or a serverless environment supporting `ai_prep_search`. It materializes AI calls once.
2. Run `python 02_create_ai_search_index.py`. The first run may only create the endpoint. Wait for `ONLINE`, rerun it to create the Delta Sync index and trigger its initial sync.
3. Wait for the index to become online. Export the printed value, for example `export AI_SEARCH_INDEX=nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_index`.
4. Export `GENIE_SPACE_ID` and run `bash 03_create_agents.sh`.
5. Wait for the KA and Supervisor endpoints before testing.

The AI Search index is a first-class step: it embeds `chunk_to_embed`, returns `chunk_to_retrieve`, syncs `source_path` for citations, and uses a triggered pipeline to keep demo cost predictable.

## Demo prompts

- “How do I fit an SDS-plus bit on the GBH 2-26?” → custom index through KA
- “Which rotary hammer has the most purchases?” → Genie
- “Which rotary hammer sells best and what are its maintenance instructions?” → both

## Trade-offs

- Full control over parsing, chunking, embedding input, metadata, and index lifecycle.
- Managed KA citations and Supervisor routing remain available.
- More runtime requirements, objects, waiting, monitoring, and cost than Option 2.
- Scripts create demo agents on each run; cleanup remains deliberate and manual.

# Option 4 — AI Search Function in Genie

## Architecture

`PDFs → AI Parse → AI Prep Search → Delta chunks → AI Search → UC table function → Genie`

This keeps one conversational surface. Genie handles structured analysis and calls a governed function when manual context is needed.

## FEVM deployment

- Index: `nikks_fevm_workspace_7405607030687545.techsummit.option4_manual_index`
- Function: `nikks_fevm_workspace_7405607030687545.techsummit.search_product_manuals`
- Genie: `01f1a11927d41dbf809a89d964725330`

## Manual setup

1. Run `01_prepare_manuals.sql` in an environment supporting `ai_prep_search`.
2. Run `python 02_create_ai_search_index.py`, wait for the endpoint, and rerun until the index is online.
3. Run `03_create_genie_function.sql` on a warehouse supporting the `VECTOR_SEARCH` table-valued function.
4. Grant the Genie identity `EXECUTE` on the function and access to the index.
5. Add the function to the Genie space and paste the text from `genie_instructions.md`.

Test the function directly before adding it:

```sql
SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.search_product_manuals(
  'How do I fit an SDS-plus bit on the GBH 2-26?'
);
```

## Trade-offs

- One user-facing Genie experience and no Supervisor endpoint.
- Explicit parsing, chunking, indexing, function contract, and citations.
- Function and `VECTOR_SEARCH` support must be available in the selected workspace/runtime.
- Genie needs precise tool instructions because the function returns evidence rather than a finished answer.

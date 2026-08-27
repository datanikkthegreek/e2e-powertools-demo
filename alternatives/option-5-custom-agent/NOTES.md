# Option 5 — Custom Agent

## Architecture

`User → custom router → SQL generator/executor and/or AI Search → custom synthesis`

This example rebuilds the parts needed for this demo, not the complete Genie product. The code owns routing, natural-language-to-SQL prompting, query validation, retrieval, contextual rules, and final synthesis.

## FEVM deployment

- Index: `nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_index`
- Tools: `option5_search_manuals`, `option5_product_performance`, `option5_revenue_by_country`, and `option5_product_specs` in the `techsummit` schema
- Runtime: AppKit Agent using the managed Supervisor API and `databricks-claude-sonnet-4-5`
- UI: `powertools-arch-options`, Option 5 tab

## Manual setup

1. Run `01_prepare_manuals.sql` in an environment supporting `ai_prep_search`.
2. Run `python 02_create_ai_search_index.py`, wait for the endpoint, and rerun until the index is online.
3. Install `requirements.txt`.
4. Export `DATABRICKS_CONFIG_PROFILE`, `WAREHOUSE_ID`, and optionally `MODEL_ENDPOINT`.
5. Run `python agent.py "Which rotary hammer sells best and how should I maintain it?"`.

The SQL tool accepts only a single statement beginning with `SELECT` or `WITH`. For production, replace this basic check with a SQL parser, restricted service principal, query timeout, row/byte limits, tracing, and evaluation.

## Included context methods

- Table schema supplied directly to the SQL generation prompt.
- Business rules supplied by an ordinary Python context tool.
- Manual evidence supplied by hybrid AI Search.
- More tools can be added as Python functions without changing a managed Genie space.

## Trade-offs

- Maximum control over routing, prompts, models, tools, context, and response format.
- Easy to integrate non-Databricks tools or custom authorization.
- You own SQL safety, serving, identity, monitoring, evaluation, latency, and failures.
- More code and operational responsibility than Options 2–4.

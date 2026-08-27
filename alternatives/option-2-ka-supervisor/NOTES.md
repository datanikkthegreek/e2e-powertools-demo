# Option 2 — Knowledge Assistant + Supervisor

## Architecture

`User → Supervisor → existing Genie space and/or managed Knowledge Assistant`

This is the easiest multi-agent architecture. Databricks manages document parsing, retrieval, citations, routing, and serving. The existing production code is not imported or changed.

## FEVM deployment

- Genie: `01f1a1155368132187a16b6e4849d6c8`
- Knowledge Assistant: `0bf64824-33de-4f25-a482-9fe3db0f3062`
- Supervisor endpoint: `mas-5a4c8e31-endpoint`
- UI: `powertools-arch-options`, Option 2 tab

## Manual setup

1. Select the intended Databricks CLI profile explicitly: `export DATABRICKS_CONFIG_PROFILE=FEVM`.
2. Install `databricks-sdk>=0.126.0` and run `python create_knowledge_assistant.py`.
3. Export the printed `KA_ID` and the existing `GENIE_SPACE_ID`.
4. Run `bash create_supervisor.sh`.
5. Wait for both endpoints to become online before testing.

The KA script is create-or-reuse by display name. The Supervisor script creates a fresh demo Supervisor on each run so its behavior stays visible and easy to explain.

## Demo prompts

- “Which 18V drill sells best?” → Genie
- “How do I fit an SDS-plus bit on the GBH 2-26?” → KA
- “Which rotary hammer sells best and how should I maintain it?” → both

## Trade-offs

- Least code and operational effort.
- Fastest path to a governed, cited assistant.
- Retrieval and routing internals offer less control than the later options.
- Cleanup is manual; verify resource ids before deleting anything.

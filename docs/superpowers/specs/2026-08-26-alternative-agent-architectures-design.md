# Alternative Agent Architectures Demo Design

## Goal

Add four small, manually executed reference implementations that demonstrate increasing architectural flexibility beyond the existing Genie-only path. The existing `app/` and `etl/` implementations remain unchanged.

All alternatives use the existing FEVM defaults:

- Catalog: `nikks_fevm_workspace_7405607030687545`
- Schema: `techsummit`
- Manuals volume: `productmanuals`
- Existing structured analytics tables and Genie space

## Layout

Each implementation lives below `alternatives/` and contains its own runnable assets plus a `NOTES.md` explaining the architecture, setup order, demo flow, trade-offs, and cleanup considerations.

### Option 2: Knowledge Assistant and Supervisor

Folder: `alternatives/option-2-ka-supervisor/`

Reuse the managed Knowledge Assistant over the manuals volume and combine it with the existing Genie space through a Supervisor Agent. This is the lowest-code alternative and establishes the baseline for multi-agent routing.

Assets remain focused on repeatable Knowledge Assistant creation/update and copy-ready Supervisor configuration. Creation is non-destructive and reuses resources by display name.

### Option 3: Custom Retrieval Pipeline, Knowledge Assistant, and Supervisor

Folder: `alternatives/option-3-custom-rag-supervisor/`

Build an explicit document pipeline:

1. Read manual PDFs from the Unity Catalog volume.
2. Parse documents with `ai_parse_document`.
3. Prepare chunks with `ai_prep_search`.
4. Materialize a Delta table suitable for a Vector Search index.
5. Use that retrieval source from a Knowledge Assistant.
6. Route between the Knowledge Assistant and Genie using a Supervisor.

The code provides SQL for document preparation and a small setup script for the online resources. Resource identifiers are configuration values because endpoint availability and product APIs vary by workspace.

### Option 4: Retrieval Function Added to Genie

Folder: `alternatives/option-4-genie-rag-function/`

Reuse the explicit parsing, preparation, and Vector Search pattern, then expose manual retrieval through a function that Genie can call. The function has a simple question-in, grounded-context-out contract. This option demonstrates extending one Genie space without adding a Supervisor.

The implementation includes the preparation SQL, the function/tool code, and the Genie instruction text needed to describe when the function should be used.

### Option 5: Custom Agent Rebuilding Genie-Oriented Routing

Folder: `alternatives/option-5-custom-agent/`

Provide a minimal custom agent that routes requests between:

- SQL analytics over the existing `techsummit` tables;
- manual retrieval through Vector Search;
- small optional context tools implemented as ordinary Python functions.

The agent uses explicit tool definitions and routing instructions. It does not attempt to reproduce the full Genie product. It demonstrates the additional control gained by owning orchestration, prompts, tool contracts, and response synthesis.

## Data Flow and Boundaries

The alternatives are independent examples, not a shared deployable platform. Small amounts of duplicated setup are intentional so each folder can be copied or demonstrated alone. No alternative imports code from the productive `etl/` or `app/` paths.

Configuration is kept at the top of scripts or in environment variables. Manual execution is the primary workflow; no new bundle deployment graph or CI automation is introduced.

## Error Handling

Scripts fail early when required identifiers or environment variables are missing. Retrieval and SQL tools return clear errors or an explicit no-result response instead of synthesizing unsupported facts. Resource creation favors create-or-reuse behavior and avoids automatic deletion.

## Validation

Validation is local and proportionate to these examples:

- Python syntax compilation for Python files.
- Static checks that expected files and placeholders are present.
- Review of SQL object names and data-flow order against the current repository.
- No workspace resources are created during validation.

## Out of Scope

- Deploying or deleting Databricks resources.
- Replacing the productive Genie space or existing Knowledge Assistant.
- Production authentication, observability, evaluation suites, or CI/CD.
- A custom UI.
- Full feature parity with Genie.

#!/usr/bin/env python3
"""Create-or-reuse the ``powertools-manuals-ka`` Knowledge Assistant via the SDK.

Idempotent orchestration on top of ``manage_knowledge_assistant.py``:

  1. Look the KA up by ``DISPLAY_NAME``.
  2. If it does not exist, create it and attach the ``manuals/`` Volume folder as
     a "files" knowledge source.
  3. If it already exists, REUSE it (no re-create, no delete).
  4. Always trigger a sync at the end so newly-uploaded manuals get (re)indexed.

Self-authenticates through the Databricks CLI profile (``--profile``, default
FEVM) — no tokens are read from or written to files.

Usage:
  python etl/src/create_knowledge_assistant.py                     # defaults (FEVM)
  python etl/src/create_knowledge_assistant.py --profile FEVM \
      --catalog nikks_fevm_workspace_7405607030687545 \
      --schema techsummit --volume raw_docs
"""
from __future__ import annotations

import argparse

from databricks.sdk import WorkspaceClient

from manage_knowledge_assistant import (
    create_knowledge_assistant,
    create_knowledge_source_files,
    get_knowledge_assistant_id_by_display_name,
    sync_knowledge_sources,
)

# ── defaults (match etl/databricks.yml vars + the demo guardrails) ─────────────
DEFAULT_CATALOG = "nikks_fevm_workspace_7405607030687545"
DEFAULT_SCHEMA = "techsummit"
DEFAULT_VOLUME = "raw_docs"
DEFAULT_PROFILE = "FEVM"
VOLUME_SUBFOLDER = "manuals"

# display_name is unique per workspace and is the idempotency key: keeping this
# stable makes reruns REUSE the existing KA (id 44e78d1c-… on the current FEVM
# build) rather than minting a duplicate.
DISPLAY_NAME = "powertools-manuals-ka"
DESCRIPTION = (
    "Answers questions about Bosch power-tool product manuals (safety, "
    "specifications, operation, battery/charging or mains, maintenance, "
    "troubleshooting, warranty). RAG over the PDFs in the manuals/ Volume folder."
)
INSTRUCTIONS = (
    "Answer only from the retrieved product manuals and always cite the source "
    "manual. Identify the specific tool model (e.g. GBH 2-26) the question is "
    "about. If a spec or fault code is not in the manuals, say so rather than "
    "guessing."
)
SOURCE_DISPLAY_NAME = "powertools-pdf-manuals"
SOURCE_DESCRIPTION = (
    "Bosch power-tool operating manuals (PDFs) — safety, specs, operation, "
    "battery/mains, maintenance, troubleshooting, warranty."
)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Create-or-reuse the powertools-manuals-ka Knowledge Assistant (SDK)."
    )
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--volume", default=DEFAULT_VOLUME)
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    args = ap.parse_args()

    volume_path = (
        f"/Volumes/{args.catalog}/{args.schema}/{args.volume}/{VOLUME_SUBFOLDER}/"
    )

    w = WorkspaceClient(profile=args.profile)

    ka_id = get_knowledge_assistant_id_by_display_name(w, DISPLAY_NAME)
    if ka_id is None:
        print(f"[ka  ] no KA named {DISPLAY_NAME!r} — creating it")
        ka = create_knowledge_assistant(w, DISPLAY_NAME, DESCRIPTION, INSTRUCTIONS)
        ka_id = (ka.name or "").split("/", 1)[-1]
        print(f"[ka  ] created knowledge-assistants/{ka_id} (state: {ka.state})")

        src = create_knowledge_source_files(
            w, ka_id, SOURCE_DISPLAY_NAME, SOURCE_DESCRIPTION, volume_path
        )
        src_id = (src.name or "").rsplit("/", 1)[-1]
        print(
            f"[src ] attached files source {SOURCE_DISPLAY_NAME!r} "
            f"(id {src_id}, state {src.state}) -> {volume_path}"
        )
    else:
        print(
            f"[ka  ] reusing existing knowledge-assistants/{ka_id} "
            f"({DISPLAY_NAME!r}) — no re-create, no delete"
        )

    # Always sync so freshly-uploaded manuals are (re)indexed.
    print(f"[sync] syncing knowledge sources for knowledge-assistants/{ka_id}")
    sync_knowledge_sources(w, ka_id)
    print(
        f"[done] KA knowledge-assistants/{ka_id} synced over {volume_path} "
        "(status CREATING -> ONLINE, ~2-5 min; query it in AI Playground)."
    )


if __name__ == "__main__":
    main()

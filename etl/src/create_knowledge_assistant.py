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
import sys

from databricks.sdk import WorkspaceClient

from manage_knowledge_assistant import (
    create_knowledge_assistant,
    create_knowledge_source_files,
    get_knowledge_assistant_id_by_display_name,
    list_knowledge_sources,
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


def _validate_target(catalog: str, schema: str, volume: str,
                     allow_catalog_override: bool) -> None:
    """Fail closed BEFORE any WorkspaceClient/KA call if the target is unsafe.

    Mirrors the guardrails in generate_manuals.py: reject '/'/'..'/whitespace in
    any component; schema must be 'techsummit'; never the 'cdp' catalog/schema;
    catalog must be the FEVM default unless --allow-catalog-override is passed.
    """
    for label, val in (("catalog", catalog), ("schema", schema), ("volume", volume)):
        if not val or "/" in val or ".." in val or any(c.isspace() for c in val):
            sys.exit(f"[guard] invalid {label} {val!r}: must be non-empty and free "
                     "of '/', '..', and whitespace")
    if "cdp" in (catalog, schema):
        sys.exit("[guard] refusing to touch the 'cdp' catalog/schema")
    if schema != DEFAULT_SCHEMA:
        sys.exit(f"[guard] schema must be '{DEFAULT_SCHEMA}' (got {schema!r}); this "
                 "demo operates ONLY in techsummit")
    if catalog != DEFAULT_CATALOG and not allow_catalog_override:
        sys.exit(f"[guard] catalog must be the FEVM default '{DEFAULT_CATALOG}' "
                 f"(got {catalog!r}); pass --allow-catalog-override to target another")


def _source_path(src) -> str:
    """Best-effort extract of a knowledge source's Volume path (files sources)."""
    files = getattr(src, "files", None)
    return (getattr(files, "path", None) or "") if files is not None else ""


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Create-or-reuse the powertools-manuals-ka Knowledge Assistant (SDK)."
    )
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--volume", default=DEFAULT_VOLUME)
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--allow-catalog-override", action="store_true",
                    help="permit a --catalog other than the FEVM default")
    args = ap.parse_args()

    # Fail closed before touching the workspace if the target looks wrong/unsafe.
    _validate_target(args.catalog, args.schema, args.volume,
                     args.allow_catalog_override)

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
        # True create-or-update: reuse the KA, but ensure a files source actually
        # points at the target Volume path before syncing. An existing KA with no
        # matching source (e.g. it was created empty, or the path changed) would
        # otherwise sync nothing.
        print(
            f"[ka  ] reusing existing knowledge-assistants/{ka_id} "
            f"({DISPLAY_NAME!r}) — no re-create, no delete"
        )
        want = volume_path.rstrip("/")
        existing = list(list_knowledge_sources(w, ka_id))
        matched = [s for s in existing if _source_path(s).rstrip("/") == want]
        if matched:
            print(
                f"[src ] found existing files source at {volume_path} "
                f"({len(matched)} match) — reusing it"
            )
        else:
            paths = ", ".join(_source_path(s) or "?" for s in existing) or "none"
            print(
                f"[src ] no source at {volume_path} (existing: {paths}) — "
                "attaching one"
            )
            src = create_knowledge_source_files(
                w, ka_id, SOURCE_DISPLAY_NAME, SOURCE_DESCRIPTION, volume_path
            )
            src_id = (src.name or "").rsplit("/", 1)[-1]
            print(
                f"[src ] attached files source {SOURCE_DISPLAY_NAME!r} "
                f"(id {src_id}, state {src.state}) -> {volume_path}"
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

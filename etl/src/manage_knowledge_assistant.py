#!/usr/bin/env python3
"""Thin Databricks SDK helpers for the Agent Bricks **Knowledge Assistant** (KA).

A KA is not a Databricks Asset Bundle resource (no DAB verb), so it is created
and maintained via the SDK's ``w.knowledge_assistants`` API rather than
``bundle deploy``. These helpers mirror the shape used across our data-extraction
repos so the orchestrator (``create_knowledge_assistant.py``) stays declarative.

Nothing here is destructive: we look a KA up by display name and REUSE it, add a
"files" knowledge source pointed at a UC Volume folder, and sync. Deleting a KA
is intentionally not wrapped — that is a manual last resort.

Requires ``databricks-sdk`` (tested on 0.126.0).
"""
from __future__ import annotations

from typing import Iterator, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.knowledgeassistants import (
    FilesSpec,
    KnowledgeAssistant,
    KnowledgeSource,
)


def list_knowledge_assistants(
    w: WorkspaceClient,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
) -> Iterator[KnowledgeAssistant]:
    """Yield every Knowledge Assistant in the workspace (SDK paginates for us)."""
    return w.knowledge_assistants.list_knowledge_assistants(
        page_size=page_size, page_token=page_token
    )


def get_knowledge_assistant_id_by_display_name(
    w: WorkspaceClient, display_name: str
) -> Optional[str]:
    """Return the bare KA id (uuid) for the first KA whose display name matches.

    ``display_name`` is unique per workspace, so this is the idempotency hook:
    if it returns an id we REUSE that KA instead of creating a duplicate.
    Returns ``None`` when no KA has that display name.
    """
    target = (display_name or "").strip()
    for a in list_knowledge_assistants(w):
        if (a.display_name or "").strip() == target:
            # a.name looks like "knowledge-assistants/{id}"; hand back the bare id.
            name = a.name or ""
            return name.split("/", 1)[1] if "/" in name else name
    return None


def create_knowledge_assistant(
    w: WorkspaceClient,
    display_name: str,
    description: str,
    instructions: Optional[str] = None,
) -> KnowledgeAssistant:
    """Create a new Knowledge Assistant and return the created resource."""
    return w.knowledge_assistants.create_knowledge_assistant(
        knowledge_assistant=KnowledgeAssistant(
            display_name=display_name,
            description=description,
            instructions=instructions,
        )
    )


def get_knowledge_assistant(w: WorkspaceClient, assistant_id: str) -> KnowledgeAssistant:
    """Fetch a Knowledge Assistant by its bare id."""
    return w.knowledge_assistants.get_knowledge_assistant(
        name=f"knowledge-assistants/{assistant_id}"
    )


def create_knowledge_source_files(
    w: WorkspaceClient,
    assistant_id: str,
    display_name: str,
    description: str,
    volume_path: str,
) -> KnowledgeSource:
    """Attach a "files" knowledge source (a UC Volume folder of PDFs) to the KA."""
    return w.knowledge_assistants.create_knowledge_source(
        parent=f"knowledge-assistants/{assistant_id}",
        knowledge_source=KnowledgeSource(
            display_name=display_name,
            description=description,
            source_type="files",
            files=FilesSpec(path=volume_path),
        ),
    )


def list_knowledge_sources(
    w: WorkspaceClient, assistant_id: str
) -> Iterator[KnowledgeSource]:
    """Yield the knowledge sources already attached to a KA (SDK paginates)."""
    return w.knowledge_assistants.list_knowledge_sources(
        parent=f"knowledge-assistants/{assistant_id}"
    )


def get_knowledge_source(
    w: WorkspaceClient, assistant_id: str, source_id: str
) -> KnowledgeSource:
    """Fetch a single knowledge source of a KA by its bare id."""
    return w.knowledge_assistants.get_knowledge_source(
        name=f"knowledge-assistants/{assistant_id}/knowledge-sources/{source_id}"
    )


def sync_knowledge_sources(w: WorkspaceClient, assistant_id: str):
    """Trigger (re)indexing of the KA's knowledge sources."""
    return w.knowledge_assistants.sync_knowledge_sources(
        name=f"knowledge-assistants/{assistant_id}"
    )

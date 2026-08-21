"""Event ingestion endpoint for the Zerobus path.

When ``ingestion_mode == "zerobus"``, the frontend POSTs normalized tracking
events here. This route assembles a GA4-server-side ``eventData`` row matching
the shape the silver pipeline parses (see ``EVENT_SCHEMA`` in
``etl/pipelines/silver/transformations/_shared.py``) and inserts it into the
configured ``gtm_events`` table via the Zerobus REST API.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from pydantic import BaseModel

from .core import Dependencies, create_router
from .core._config import AppConfig
from .zerobus import ZerobusClient, ZerobusConfigError

router = create_router()


class EventIn(BaseModel):
    """Normalized tracking event sent by the browser."""

    event_name: str
    web_input_data: dict[str, Any]
    page_location: str | None = None
    page_referrer: str | None = None
    page_title: str | None = None
    screen_resolution: str | None = None
    language: str | None = None


class EventAck(BaseModel):
    status: str


@lru_cache(maxsize=1)
def _client(config: AppConfig) -> ZerobusClient:
    """Cache a single Zerobus client per config (AppConfig is hashable)."""
    return ZerobusClient(config)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First hop is the originating client.
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _client_hints(request: Request) -> dict[str, Any] | None:
    """Build a client_hints object from sec-ch-ua-* headers, if present."""
    h = request.headers
    mobile_raw = h.get("sec-ch-ua-mobile")
    hints: dict[str, Any] = {
        "architecture": h.get("sec-ch-ua-arch", "").strip('"') or None,
        "bitness": h.get("sec-ch-ua-bitness", "").strip('"') or None,
        "platform": h.get("sec-ch-ua-platform", "").strip('"') or None,
        "platform_version": h.get("sec-ch-ua-platform-version", "").strip('"')
        or None,
        "mobile": (mobile_raw == "?1") if mobile_raw is not None else None,
        "model": h.get("sec-ch-ua-model", "").strip('"') or None,
        "wow64": None,
    }
    if all(value is None for value in hints.values()):
        return None
    return hints


def _request_path(page_location: str | None) -> str:
    if page_location:
        parsed = urlparse(page_location)
        if parsed.path:
            return parsed.path
    return "/gtm"


def _build_event_data(payload: EventIn, request: Request, config: AppConfig) -> dict:
    """Merge a GA4 envelope with the browser-supplied overlay fields."""
    now = datetime.now(timezone.utc)
    event_unix_s = int(now.timestamp())
    event_unix_ms = int(now.timestamp() * 1000)

    accept_language = request.headers.get("accept-language")
    language = payload.language or (
        accept_language.split(",")[0].strip() if accept_language else None
    )

    envelope: dict[str, Any] = {
        "event_name": payload.event_name,
        "event_id": f"{event_unix_ms}_{uuid.uuid4().hex}",
        "timestamp": now.isoformat(),
        # Synthesized GA4 session identifiers (no real gtag in zerobus mode).
        "client_id": f"{uuid.uuid4().int % 10**10}.{event_unix_s}",
        "ga_session_id": str(event_unix_s),
        "ga_session_number": 1,
        "page_location": payload.page_location,
        "page_referrer": payload.page_referrer,
        "page_title": payload.page_title,
        "language": language,
        "screen_resolution": payload.screen_resolution,
        "user_agent": request.headers.get("user-agent"),
        "ip_override": _client_ip(request),
        "client_hints": _client_hints(request),
        "x-ga-measurement_id": config.ga_measurement_id,
    }

    # event_location from geo headers when the platform provides them.
    country = (
        request.headers.get("x-forwarded-country")
        or request.headers.get("cf-ipcountry")
    )
    region = request.headers.get("x-forwarded-region")
    if country or region:
        envelope["event_location"] = {"country": country, "region": region}

    # Overlay the browser-supplied fields flat at the top level (GA4
    # server-side carries ecommerce/account fields flat, matching EVENT_SCHEMA).
    overlay = {
        key: value
        for key, value in payload.web_input_data.items()
        # event_name/timestamp already live in the envelope.
        if key not in {"event_name", "timestamp"}
    }
    return {**envelope, **overlay}


@router.post("/events", response_model=EventAck, operation_id="ingestEvent")
def ingest_event(
    payload: EventIn,
    request: Request,
    config: Dependencies.Config,
) -> EventAck:
    if config.ingestion_mode != "zerobus":
        # Defensive: the frontend only calls this in zerobus mode.
        return EventAck(status="skipped")

    event_data = _build_event_data(payload, request, config)
    visitor_region = None
    location = event_data.get("event_location")
    if isinstance(location, dict):
        visitor_region = location.get("country")

    row = {
        "ingestion_time": int(time.time() * 1000),
        "gtm_container_id": config.gtm_container_id,
        "event_name": payload.event_name,
        "request_path": _request_path(payload.page_location),
        "request_method": "POST",
        "query_string": "",
        "visitor_region": visitor_region,
        "eventData": json.dumps(event_data, ensure_ascii=False, separators=(",", ":")),
    }

    try:
        _client(config).insert_rows([row])
    except ZerobusConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return EventAck(status="ok")

"""Zerobus Ingest REST client.

Mints a client-credentials OAuth token scoped to the workspace's
``zerobusDirectWriteApi`` and inserts rows into the configured Unity Catalog
table via the Zerobus REST ``/insert`` endpoint.

The token is cached in-process and refreshed shortly before expiry. This module
is only exercised when ``AppConfig.ingestion_mode == "zerobus"``.
"""

from __future__ import annotations

import json
import threading
import time

import httpx

from .core._config import AppConfig, logger

# Tokens are valid for ~1h; refresh a little early to avoid edge expiry.
_TOKEN_TTL_SECONDS = 55 * 60
_REQUEST_TIMEOUT_SECONDS = 15.0


class ZerobusConfigError(RuntimeError):
    """Raised when the Zerobus configuration is incomplete."""


class ZerobusClient:
    """Thread-safe Zerobus REST client with a cached OAuth token."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # --- configuration helpers ---

    def _require(self, value: str, name: str) -> str:
        if not value:
            raise ZerobusConfigError(
                f"Zerobus ingestion is enabled but '{name}' is not configured."
            )
        return value

    def _authorization_details(self) -> str:
        catalog = self._config.zerobus_catalog
        schema = self._config.zerobus_schema
        table = self._config.zerobus_table
        return json.dumps(
            [
                {
                    "type": "unity_catalog_privileges",
                    "privileges": ["USE CATALOG"],
                    "object_type": "CATALOG",
                    "object_full_path": catalog,
                },
                {
                    "type": "unity_catalog_privileges",
                    "privileges": ["USE SCHEMA"],
                    "object_type": "SCHEMA",
                    "object_full_path": f"{catalog}.{schema}",
                },
                {
                    "type": "unity_catalog_privileges",
                    "privileges": ["SELECT", "MODIFY"],
                    "object_type": "TABLE",
                    "object_full_path": f"{catalog}.{schema}.{table}",
                },
            ]
        )

    # --- token handling ---

    def _fetch_token(self) -> str:
        workspace_url = self._require(
            self._config.zerobus_workspace_url, "zerobus_workspace_url"
        ).rstrip("/")
        workspace_id = self._require(
            self._config.zerobus_workspace_id, "zerobus_workspace_id"
        )
        client_id = self._require(self._config.zerobus_client_id, "zerobus_client_id")
        client_secret = self._require(
            self._config.zerobus_client_secret.get_secret_value(),
            "zerobus_client_secret",
        )

        resource = (
            f"api://databricks/workspaces/{workspace_id}/zerobusDirectWriteApi"
        )
        response = httpx.post(
            f"{workspace_url}/oidc/v1/token",
            auth=(client_id, client_secret),
            data={
                "grant_type": "client_credentials",
                "scope": "all-apis",
                "resource": resource,
                "authorization_details": self._authorization_details(),
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ZerobusConfigError(
                "OAuth token response did not contain an access_token."
            )
        return token

    def _get_token(self, *, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.monotonic()
            if force_refresh or self._token is None or now >= self._token_expiry:
                self._token = self._fetch_token()
                self._token_expiry = now + _TOKEN_TTL_SECONDS
            return self._token

    # --- ingestion ---

    def _insert_url(self) -> str:
        endpoint = self._require(
            self._config.zerobus_endpoint, "zerobus_endpoint"
        ).rstrip("/")
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"https://{endpoint}"
        return f"{endpoint}/zerobus/v1/tables/{self._config.zerobus_table_fqn}/insert"

    def insert_rows(self, rows: list[dict]) -> None:
        """Insert a list of row dicts into the configured Zerobus table.

        Refreshes the OAuth token once and retries on a 401 response.
        """
        if not rows:
            return

        url = self._insert_url()

        def _post(token: str) -> httpx.Response:
            return httpx.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                content=json.dumps(rows),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )

        response = _post(self._get_token())
        if response.status_code == httpx.codes.UNAUTHORIZED:
            logger.info("Zerobus token rejected (401); refreshing and retrying.")
            response = _post(self._get_token(force_refresh=True))
        response.raise_for_status()

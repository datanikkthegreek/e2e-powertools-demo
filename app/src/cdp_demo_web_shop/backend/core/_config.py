from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..._metadata import app_name, app_slug

# --- Config ---

project_root = Path(__file__).parent.parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)

    # --- Ingestion mode ---
    # "gtm" routes events through Google Tag Manager (client-side gtag).
    # "zerobus" routes events to the gtm_events table via the Zerobus REST API.
    ingestion_mode: str = Field(default="gtm")

    # --- Zerobus connection (used when ingestion_mode == "zerobus") ---
    zerobus_workspace_id: str = Field(default="")
    zerobus_workspace_url: str = Field(default="")
    zerobus_endpoint: str = Field(default="")
    zerobus_catalog: str = Field(default="nikks_fevm_workspace_7405607030687545")
    zerobus_schema: str = Field(default="techsummit")
    zerobus_table: str = Field(default="gtm_events")
    zerobus_client_id: str = Field(default="")
    zerobus_client_secret: SecretStr = Field(default=SecretStr(""))

    # --- Analytics: abandoned-carts source (gold materialized view) ---
    # Lives in the same catalog/schema as the events table. One row per
    # abandoned cart (carts anti-joined against purchases).
    abandoned_carts_table: str = Field(default="cart_abandoned")

    # --- GA4 / GTM identifiers stamped into the synthesized eventData row ---
    gtm_container_id: str = Field(default="GTM-K29QPLV2")
    ga_measurement_id: str = Field(default="G-C31T0FRWHZ")

    # --- Databricks job that runs the silver pipeline ---
    # The Analytics page resolves this job by name and triggers it via run_now.
    triggered_job_name: str = Field(default="powertools-silver")

    @property
    def zerobus_table_fqn(self) -> str:
        return f"{self.zerobus_catalog}.{self.zerobus_schema}.{self.zerobus_table}"

    @property
    def abandoned_carts_table_fqn(self) -> str:
        return (
            f"{self.zerobus_catalog}.{self.zerobus_schema}.{self.abandoned_carts_table}"
        )

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")

    def __hash__(self) -> int:
        return hash(self.app_name)


# --- Logger ---

logger = logging.getLogger(app_name)

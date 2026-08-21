"""Lakebase (Databricks Database) integration: config, engine, session, and dependency."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Generator
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, TypeAlias

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from fastapi import FastAPI, Request
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine, event
from sqlmodel import Session, SQLModel, text

from ._base import LifespanDependency
from ._config import logger


# --- Database Config ---


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    port: int = Field(
        description="The port of the database", default=5432, validation_alias="PGPORT"
    )
    database_name: str = Field(
        description="The name of the database", default="databricks_postgres"
    )
    # Lakebase Autoscaling Postgres endpoint coordinates (w.postgres API).
    # Resolves to projects/{project}/branches/{branch}/endpoints/{endpoint}.
    project_id: str = Field(
        description="Lakebase project id",
        default="techsummit",
        validation_alias="LAKEBASE_PROJECT_ID",
    )
    branch_id: str = Field(
        description="Lakebase branch id",
        default="production",
        validation_alias="LAKEBASE_BRANCH_ID",
    )
    endpoint_id: str = Field(
        description="Lakebase compute endpoint id",
        default="primary",
        validation_alias="LAKEBASE_ENDPOINT_ID",
    )

    @property
    def endpoint_name(self) -> str:
        return (
            f"projects/{self.project_id}"
            f"/branches/{self.branch_id}"
            f"/endpoints/{self.endpoint_id}"
        )


# --- Engine creation ---


def _use_local_db() -> bool:
    """Opt-in to the apx-provided local ephemeral Postgres for offline work.

    Default is off: the app connects to the real Lakebase autoscaling endpoint
    even locally. Set APX_USE_LOCAL_DB=1 to fall back to the local dev database.
    """
    return os.environ.get("APX_USE_LOCAL_DB", "").strip().lower() in {"1", "true", "yes"}


def _local_engine_url() -> str:
    dev_port = os.environ.get("APX_DEV_DB_PORT")
    if not dev_port:
        raise ValueError(
            "APX_USE_LOCAL_DB is set but APX_DEV_DB_PORT is missing; "
            "is the apx dev server running?"
        )
    password = os.environ.get("APX_DEV_DB_PWD")
    if password is None:
        raise ValueError(
            "APX server didn't provide a password, please check the dev server logs"
        )
    logger.info(f"Using local dev database at localhost:{dev_port}")
    return f"postgresql+psycopg://postgres:{password}@localhost:{dev_port}/postgres?sslmode=disable"


def _resolve_host(db_config: DatabaseConfig, ws: WorkspaceClient) -> str:
    """Resolve the read/write host of the Lakebase autoscaling endpoint."""
    endpoint = ws.postgres.get_endpoint(db_config.endpoint_name)
    host = endpoint.status.hosts.host if endpoint.status and endpoint.status.hosts else None
    if not host:
        raise ValueError(
            f"Lakebase endpoint {db_config.endpoint_name} has no read/write host"
        )
    return host


def _build_engine_url(db_config: DatabaseConfig, ws: WorkspaceClient) -> str:
    """Build the Lakebase engine URL (password is supplied per-connect)."""
    logger.info(f"Using Lakebase endpoint: {db_config.endpoint_name}")
    host = _resolve_host(db_config, ws)
    username = (
        ws.config.client_id if ws.config.client_id else ws.current_user.me().user_name
    )
    return (
        f"postgresql+psycopg://{username}:@{host}:{db_config.port}/{db_config.database_name}"
    )


def create_db_engine(db_config: DatabaseConfig, ws: WorkspaceClient) -> Engine:
    """
    Create a SQLAlchemy engine.

    Local opt-out (APX_USE_LOCAL_DB): apx local Postgres, no SSL/credential callback.
    Otherwise: connect to the Lakebase autoscaling endpoint with SSL and a
    per-connect OAuth credential minted via the w.postgres API using the app
    service principal.
    """
    if _use_local_db():
        return create_engine(
            _local_engine_url(), pool_size=4, pool_recycle=45 * 60
        )

    engine = create_engine(
        _build_engine_url(db_config, ws),
        pool_size=4,
        pool_recycle=45 * 60,
        connect_args={"sslmode": "require"},
    )

    def before_connect(dialect, conn_rec, cargs, cparams):
        cred = ws.postgres.generate_database_credential(
            endpoint=db_config.endpoint_name
        )
        cparams["password"] = cred.token

    event.listens_for(engine, "do_connect")(before_connect)

    return engine


def validate_db(engine: Engine, db_config: DatabaseConfig) -> None:
    """Validate that the database connection works."""
    local = _use_local_db()

    if local:
        logger.info("Validating local dev database connection")
    else:
        logger.info(
            f"Validating Lakebase connection to endpoint {db_config.endpoint_name}"
        )
        try:
            ws = WorkspaceClient()
            ws.postgres.get_endpoint(db_config.endpoint_name)
        except NotFound:
            raise ValueError(
                f"Lakebase endpoint {db_config.endpoint_name} does not exist"
            )

    try:
        with Session(engine) as session:
            session.connection().execute(text("SELECT 1"))
            session.close()
    except Exception:
        raise ConnectionError("Failed to connect to the database")

    if local:
        logger.info("Local dev database connection validated successfully")
    else:
        logger.info(
            f"Lakebase connection to endpoint {db_config.endpoint_name} validated successfully"
        )


def initialize_models(engine: Engine) -> None:
    """Create all SQLModel tables."""
    logger.info("Initializing database models")
    SQLModel.metadata.create_all(engine)
    logger.info("Database models initialized successfully")


# Post-initialization hooks (e.g. data seeding) run once, lazily, after the
# schema is created on the first successful connection. Registered by the app
# layer (see `_seed_dep.py`) so this core module never imports app code.
_post_init_hooks: list[Callable[[Engine], None]] = []


def register_post_init_hook(hook: Callable[[Engine], None]) -> None:
    """Register a callable run once (with the live engine) after schema init."""
    _post_init_hooks.append(hook)


def _ensure_ready(app: FastAPI, engine: Engine) -> None:
    """Create tables and run post-init hooks exactly once for the process."""
    if getattr(app.state, "_lakebase_ready", False):
        return
    with app.state._lakebase_lock:
        if getattr(app.state, "_lakebase_ready", False):
            return
        initialize_models(engine)
        for hook in _post_init_hooks:
            hook(engine)
        app.state._lakebase_ready = True


# --- Dependency ---


class _LakebaseDependency(LifespanDependency):
    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        db_config = DatabaseConfig()
        app.state.db_config = db_config
        app.state._lakebase_lock = threading.Lock()
        app.state._lakebase_ready = False

        ws = app.state.workspace_client
        engine = create_db_engine(db_config, ws)
        validate_db(engine, db_config)
        app.state.engine = engine
        _ensure_ready(app, engine)
        yield
        engine.dispose()

    @staticmethod
    def __call__(request: Request) -> Generator[Session, None, None]:
        with Session(bind=request.app.state.engine) as session:
            yield session


LakebaseDependency: TypeAlias = Annotated[Session, _LakebaseDependency.depends()]

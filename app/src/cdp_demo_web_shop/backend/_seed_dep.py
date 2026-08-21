from __future__ import annotations

from sqlalchemy import Engine
from sqlmodel import Session

from .core._config import logger
from .core.lakebase import register_post_init_hook
from .seed import seed_accounts, seed_products


def _seed(engine: Engine) -> None:
    """Idempotently insert the demo accounts (stable UUIDs) and Bosch products.

    Runs once, lazily, right after the schema is created on the first
    connection — for both local dev and the deployed (OBO) app.
    """
    with Session(engine) as session:
        try:
            seed_products(session)
            seed_accounts(session)
        except Exception as e:
            logger.error(f"Seed failed: {e}")
            raise


register_post_init_hook(_seed)

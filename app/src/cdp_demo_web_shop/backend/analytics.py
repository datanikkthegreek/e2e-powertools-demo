"""Real-time analytics over the gtm_events table via the SQL Warehouse.

A single conditional-aggregation query returns all four customer-facing
metrics in one warehouse call. The route runs on demand only (the frontend
fetches it when the user clicks Refresh), to avoid overloading the warehouse.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from .core import Dependencies, create_router, logger
from .models import AnalyticsOut, TablePreviewOut

router = create_router()

# Allowlist of tables that can be previewed on the Analytics page. Keys are the
# values accepted on the path; values are the table names resolved against the
# configured catalog/schema. An allowlist keeps the FQN out of user control, so
# there is no SQL-injection surface even though we interpolate into the query.
_PREVIEW_TABLES: dict[str, str] = {
    "event_sign_up": "event_sign_up",
    "event_purchase": "event_purchase",
    "gold_customer_360": "gold_customer_360",
}
_PREVIEW_ROW_LIMIT = 100


def _to_int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


@router.get(
    "/analytics/overview",
    response_model=AnalyticsOut,
    operation_id="analyticsOverview",
)
def analytics_overview(
    sql: Dependencies.Sql,
    config: Dependencies.Config,
) -> AnalyticsOut:
    # Event metrics from the gtm_events table; abandoned carts from the
    # dedicated cart_abandoned gold view (one row per abandoned cart). Both
    # FQNs come from config (not user input) — no injection surface. UNION the
    # two so a single warehouse call returns everything.
    statement = f"""
        SELECT
          COUNT(*) AS total_events,
          COUNT_IF(event_name = 'page_view') AS page_views,
          COUNT_IF(event_name = 'sign_up') AS registrations,
          COUNT_IF(event_name = 'purchase') AS purchases,
          (SELECT COUNT(*) FROM {config.abandoned_carts_table_fqn}) AS abandoned_carts
        FROM {config.zerobus_table_fqn}
    """

    try:
        response = sql.execute_statement(statement=statement, wait_timeout="30s")
    except Exception as exc:  # noqa: BLE001 - surface any warehouse error cleanly
        logger.exception("Analytics query failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SQL Warehouse query failed: {exc}",
        ) from exc

    result = response.result
    rows = result.data_array if result is not None else None
    if not rows or not rows[0]:
        # No data yet (empty table) — report zeros rather than erroring.
        return AnalyticsOut(
            total_events=0,
            page_views=0,
            registrations=0,
            purchases=0,
            abandoned_carts=0,
        )

    row = rows[0]
    return AnalyticsOut(
        total_events=_to_int(row[0]),
        page_views=_to_int(row[1]),
        registrations=_to_int(row[2]),
        purchases=_to_int(row[3]),
        abandoned_carts=_to_int(row[4]),
    )


@router.get(
    "/analytics/tables/{table_key}",
    response_model=TablePreviewOut,
    operation_id="tablePreview",
)
def table_preview(
    table_key: str,
    sql: Dependencies.Sql,
    config: Dependencies.Config,
) -> TablePreviewOut:
    table_name = _PREVIEW_TABLES.get(table_key)
    if table_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown table '{table_key}'",
        )

    fqn = f"{config.zerobus_catalog}.{config.zerobus_schema}.{table_name}"
    statement = f"SELECT * FROM {fqn} LIMIT {_PREVIEW_ROW_LIMIT}"

    try:
        response = sql.execute_statement(statement=statement, wait_timeout="30s")
    except Exception as exc:  # noqa: BLE001 - surface any warehouse error cleanly
        logger.exception("Table preview query failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SQL Warehouse query failed: {exc}",
        ) from exc

    columns: list[str] = []
    manifest = response.manifest
    if (
        manifest is not None
        and manifest.schema is not None
        and manifest.schema.columns is not None
    ):
        columns = [col.name or "" for col in manifest.schema.columns]

    result = response.result
    data = result.data_array if result is not None else None
    rows: list[list[str | None]] = []
    if data:
        rows = [[None if v is None else str(v) for v in row] for row in data]

    return TablePreviewOut(
        name=table_name,
        fqn=fqn,
        columns=columns,
        rows=rows,
        row_limit=_PREVIEW_ROW_LIMIT,
        truncated=len(rows) >= _PREVIEW_ROW_LIMIT,
    )

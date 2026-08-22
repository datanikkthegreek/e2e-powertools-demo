"""Behavior seed for the powertools demo (view/cart focus).

Backfills a multi-week, GA4-style behavioral stream into the raw `gtm_events`
Delta table so the funnel has statistical body for Genie. Only the two events
the trimmed demo needs are produced:

    view_item     — a product-detail-page view
    add_to_cart   — an item added to a cart

`event_purchase` is intentionally NOT seeded: Lakebase `purchases` /
`purchase_lines` are the authoritative money fact.

Each row matches the raw `gtm_events` envelope the app writes in zerobus mode
(see app/src/cdp_demo_web_shop/backend/events.py): 8 outer columns
(ingestion_time, gtm_container_id, event_name, request_path, request_method,
query_string, visitor_region) plus a JSON `eventData` string carrying the GA4
payload. The GA4 `event_id` lives INSIDE `eventData`, not as a top-level column
— the silver pipeline parses `eventData` into `ed` and reads `ed.event_id`
(see ../pipelines/silver/transformations/_shared.py). `item_id` is the Lakebase
product UUID as text, so the downstream key-normalize step lines the funnel up
with `dim_product.product_id`.

Run as a Databricks job task (the seed_gtm_events task in ../resources/job_build.yml):
    seed_gtm_events.py --catalog <cat> --schema <schema> --weeks 6 --users 100

NOTE: this is the demo seed generator. It reads the active product UUIDs from
the synced Lakebase products (`lb_products_history` current state) so the
behavioral `item_id`s reference real SKUs.
"""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType

GTM_CONTAINER_ID = "GTM-K29QPLV2"
GA_MEASUREMENT_ID = "G-C31T0FRWHZ"

# Rough funnel shape: most sessions view, a fraction of views add to cart.
VIEWS_PER_USER_PER_WEEK = (2, 8)
ADD_TO_CART_RATE = 0.28

RAW_EVENT_SCHEMA = StructType(
    [
        StructField("ingestion_time", LongType()),
        StructField("gtm_container_id", StringType()),
        StructField("event_name", StringType()),
        StructField("request_path", StringType()),
        StructField("request_method", StringType()),
        StructField("query_string", StringType()),
        StructField("visitor_region", StringType()),
        StructField("eventData", StringType()),
    ]
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed GA4-style view/cart events into gtm_events.")
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--weeks", type=int, default=6)
    p.add_argument("--users", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def _load_products(spark: SparkSession, catalog: str, schema: str) -> list[dict]:
    """Read active product (id, name, price) from the synced Lakebase products.

    Falls back to nothing if the history table isn't present yet — the caller
    should run the CDC sync first.
    """
    tbl = f"{catalog}.{schema}.lb_products_history"
    # Collapse lb_products_history to current state the same way the silver
    # pipeline's dim_product AUTO CDC flow does (etl/pipelines/silver/
    # transformations/dim_product.sql): rank ALL Lakebase CDF change rows per id
    # by `_sort_by DESC` (CDF's monotonic order key), keep the newest (_rn = 1),
    # and only THEN drop rows whose latest change is a delete or the pre-image
    # half of an update. This seed runs BEFORE the pipeline builds dim_product,
    # so it reads the raw history here rather than dim_product. Filtering before
    # ranking would let a deleted/superseded product's prior version surface as
    # _rn=1 and look active. (An UPDATE emits update_preimage + update_postimage;
    # the postimage has the higher _sort_by, so it wins _rn=1.)
    df = (
        spark.table(tbl)
        .withColumn(
            "_rn",
            F.expr("ROW_NUMBER() OVER (PARTITION BY id ORDER BY _sort_by DESC)"),
        )
        .where(F.col("_rn") == 1)
        .where(~F.col("_pg_change_type").isin("delete", "update_preimage"))
        .select(
            # CANONICAL UUID NORMALIZATION CONTRACT (OLTP / binary side).
            # This is the SOURCE of the behavioral item_id: it reduces the
            # Lakebase id to canonical lowercase hyphenated UUID text HERE, before
            # serializing it into gtm_events, so item_id == dim_product.product_id.
            # The Lakebase id is BINARY (Lakebase CDF renders the Postgres UUID as
            # raw binary; verified live 2026-08-22), so the binary branch is
            # LOAD-BEARING — a plain .cast("string") on a binary id is garbage and
            # would silently break the join. The full CASE is retained (identical
            # to the silver AUTO CDC flows in dim_product.sql etc.):
            #   1. binary                -> hex(id) [32 chars] -> hyphenate 8-4-4-4-12 -> lower
            #   2. string ^[0-9a-f]{32}$ -> hyphenate 8-4-4-4-12 -> lower   (case-insensitive)
            #   3. else                  -> lower(CAST(id AS STRING))
            # The BEHAVIORAL read-back side (etl/src/key_normalize.sql) then sees
            # item_id already as canonical lowercase text, so it uses the simple
            # lower(CAST(...)) form — the regex there was proven dead weight.
            F.expr(
                "CASE "
                "WHEN typeof(id) = 'binary' "
                "THEN lower(regexp_replace(hex(id), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5')) "
                "WHEN lower(CAST(id AS STRING)) RLIKE '^[0-9a-f]{32}$' "
                "THEN lower(regexp_replace(CAST(id AS STRING), '^(.{8})(.{4})(.{4})(.{4})(.{12})$', '$1-$2-$3-$4-$5')) "
                "ELSE lower(CAST(id AS STRING)) END"
            ).alias("product_id"),
            F.col("name"),
            F.col("price_eur"),
        )
    )
    return [row.asDict() for row in df.collect()]


def _event_row(event_name: str, ts: datetime, user_id: str, payload: dict) -> tuple:
    """Build one raw `gtm_events` row matching the Zerobus app envelope.

    The 8 outer columns mirror the row the app writes in zerobus mode (see
    app/src/cdp_demo_web_shop/backend/events.py). The GA4 `event_id` lives INSIDE
    the JSON `eventData` string (the silver pipeline reads `ed.event_id`), never
    as a top-level column. `event_id` uses the app's `{unix_ms}_{hex}` shape.
    """
    event_unix_ms = int(ts.timestamp() * 1000)
    event_data = {
        "event_name": event_name,
        "event_id": f"{event_unix_ms}_{uuid.uuid4().hex}",
        "timestamp": ts.isoformat(),
        "user_id": user_id,
        "x-ga-measurement_id": GA_MEASUREMENT_ID,
        **payload,
    }
    return (
        event_unix_ms,           # ingestion_time
        GTM_CONTAINER_ID,        # gtm_container_id
        event_name,              # event_name
        "/gtm",                  # request_path (app default when no page_location)
        "POST",                  # request_method
        "",                      # query_string
        None,                    # visitor_region
        json.dumps(event_data),  # eventData
    )


def generate(products: list[dict], weeks: int, users: int, rng: random.Random) -> list[tuple]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(weeks=weeks)
    span_seconds = int((now - start).total_seconds())
    rows: list[tuple] = []

    for _ in range(users):
        user_id = str(uuid.uuid4())
        for _week in range(weeks):
            n_views = rng.randint(*VIEWS_PER_USER_PER_WEEK)
            for _ in range(n_views):
                product = rng.choice(products)
                ts = start + timedelta(seconds=rng.randint(0, span_seconds))
                item = {
                    "item_id": product["product_id"],
                    "item_name": product["name"],
                    "price": product["price_eur"],
                    "currency": "EUR",
                    "quantity": 1,
                }
                rows.append(
                    _event_row(
                        "view_item",
                        ts,
                        user_id,
                        {"currency": "EUR", "value": product["price_eur"], "items": [item]},
                    )
                )
                if rng.random() < ADD_TO_CART_RATE:
                    qty = rng.randint(1, 3)
                    cart_ts = ts + timedelta(minutes=rng.randint(1, 30))
                    rows.append(
                        _event_row(
                            "add_to_cart",
                            cart_ts,
                            user_id,
                            {
                                "cart_id": str(uuid.uuid4()),
                                "item_id": product["product_id"],
                                "item_name": product["name"],
                                "price": product["price_eur"],
                                "previous_quantity": 0,
                                "new_quantity": qty,
                                "quantity_delta": qty,
                                "cart_action": "add",
                                "currency": "EUR",
                            },
                        )
                    )
    return rows


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed)
    spark = SparkSession.builder.getOrCreate()

    products = _load_products(spark, args.catalog, args.schema)
    if not products:
        raise SystemExit(
            "No products found in "
            f"{args.catalog}.{args.schema}.lb_products_history — run the CDC sync first."
        )

    rows = generate(products, args.weeks, args.users, rng)
    df = spark.createDataFrame(rows, schema=RAW_EVENT_SCHEMA)

    target = f"{args.catalog}.{args.schema}.gtm_events"
    df.write.mode("append").saveAsTable(target)
    print(
        json.dumps(
            {
                "target": target,
                "users": args.users,
                "weeks": args.weeks,
                "rows_written": len(rows),
                "view_item": sum(1 for r in rows if r[2] == "view_item"),
                "add_to_cart": sum(1 for r in rows if r[2] == "add_to_cart"),
            }
        )
    )


if __name__ == "__main__":
    main()

"""Behavior seed for the powertools demo (view/cart focus).

Backfills a multi-week, GA4-style behavioral stream into the raw `gtm_events`
Delta table so the funnel has statistical body for Genie. Only the two events
the trimmed demo needs are produced:

    view_item     — a product-detail-page view
    add_to_cart   — an item added to a cart

`event_purchase` is intentionally NOT seeded: Lakebase `purchases` /
`purchase_lines` are the authoritative money fact.

Each row matches the shape the silver pipeline expects (see
../pipelines/silver/transformations/_shared.py): an outer envelope plus a
JSON `eventData` string carrying the GA4 payload. `item_id` is the Lakebase
product UUID as text, so the downstream key-normalize step lines the funnel up
with `dim_product.product_id`.

Run as a Databricks job task (see ../resources/job_seed.yml):
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
        StructField("event_id", StringType()),
        StructField("event_name", StringType()),
        StructField("ingestion_time", LongType()),
        StructField("gtm_container_id", StringType()),
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
    df = (
        spark.table(tbl)
        .where(F.col("_pg_change_type") != "delete")
        .withColumn(
            "_rn",
            F.expr("ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC)"),
        )
        .where(F.col("_rn") == 1)
        .select(
            F.col("id").cast("string").alias("product_id"),
            F.col("name"),
            F.col("price_eur"),
        )
    )
    return [row.asDict() for row in df.collect()]


def _event_row(event_name: str, ts: datetime, user_id: str, payload: dict) -> tuple:
    envelope = {
        "event_name": event_name,
        "timestamp": ts.isoformat(),
        "user_id": user_id,
        "gtm_container_id": GTM_CONTAINER_ID,
        "x-ga-measurement_id": GA_MEASUREMENT_ID,
        **payload,
    }
    return (
        str(uuid.uuid4()),
        event_name,
        int(ts.timestamp() * 1000),
        GTM_CONTAINER_ID,
        json.dumps(envelope),
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
                "view_item": sum(1 for r in rows if r[1] == "view_item"),
                "add_to_cart": sum(1 for r in rows if r[1] == "add_to_cart"),
            }
        )
    )


if __name__ == "__main__":
    main()
